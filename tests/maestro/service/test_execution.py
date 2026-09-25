"""Execution's own decisions: configuration, launch checks, Git safety, and the review/correction/limit state machine.

Agents and GitHub are stood in for by small scripted objects so the service's decisions run quickly and
repeatably; real agents, a real repository and the installed path are proven in var/qa/execution-live.
"""
from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from maestro.agents.execution_contract import ExecutionResponseValidator
from maestro.agents.transport import TransportError
from maestro.foundation import Database, StorageSettings
from maestro.service import execution_config, execution_git
from maestro.service.activities import ActivityRecord, ActivityRepository, ProjectRecord
from maestro.service.execution import ExecutionService
from maestro.service.questions import QuestionService
from maestro.service.registry import OperationRegistry
from maestro.service.reservations import ProjectReservations


def config_table(**over):
    table = {
        "saved_outputs": {"schema": "execution@1"},
        "development_manager": {"run_timeout_seconds": 60, "routes": {"m": {"tool": "codex", "model": "gm"}}},
        "coder_default_route_id": "local",
        "coder_routes": {
            "local": {"adapter": "local_qwen_qwen_cli", "model": "q", "location": "local_ai_box", "capabilities": ["code_edit", "local_command", "repository_search"],
                      "context_limit_tokens": 20000, "maximum_concurrent_runs": 1, "run_timeout_seconds": 60},
            "cloud": {"adapter": "codex_cli", "model": "c", "location": "cloud", "capabilities": ["code_edit", "local_command", "repository_search", "approved_network"],
                      "context_limit_tokens": 200000, "maximum_concurrent_runs": 2, "run_timeout_seconds": 60},
        },
        "reviewers": {"packet": {"primary": {"tool": "claude_code", "model": "r1", "run_timeout_seconds": 60}, "backup": {"tool": "codex", "model": "r2", "run_timeout_seconds": 60}}},
    }
    table.update(over)
    return table


def save_recommendation(database, assignment_id, recommendation, determination="implementation_defect"):
    """The architect's saved recommendation for a review limit, as the determination assignment leaves it."""
    result = {"determination": determination, "rationale": "r", "interpretation": None, "minimum_correction": "fix", "affected_work": [], "owner_recommendation": recommendation, "disposition_recommendation": None}
    with database.transaction() as tx:
        tx.execute("INSERT INTO service_execution_architect(activity_id, assignment_key, kind, packet_key, subject, trigger_json, state, version, config_json, pending_json, result_json, review_limit, created_at, updated_at) "
                   "VALUES ('exec-1', ?, 'determination', NULL, 's', '{}', 'decided', 1, '{}', '{}', ?, 0, 't', 't')", (f"det-{assignment_id}", json.dumps(result)))


class ConfigTests(unittest.TestCase):
    def test_defaults_are_applied_and_the_snapshot_is_stable(self) -> None:
        config = execution_config.validate(config_table())
        self.assertEqual(config["reviews"]["packet"]["maximum_completed_rounds"], 2)
        self.assertEqual(config["recovery"]["automatic_recovery_attempts"], 2)
        self.assertEqual(execution_config.digest(config), execution_config.digest(execution_config.validate(config_table())))

    def test_missing_or_invalid_settings_are_named(self) -> None:
        for change, text in (
            ({"coder_default_route_id": "nope"}, "coder_default_route_id"),
            ({"saved_outputs": {"schema": "execution@2"}}, "saved_outputs"),
            ({"reviewers": {"packet": {"primary": {"tool": "codex", "model": "x", "run_timeout_seconds": 0}}}}, "run_timeout_seconds"),
            ({"reviewers": {"packet": {"primary": {"tool": "codex", "model": "x", "run_timeout_seconds": 5}, "backup": {"tool": "codex", "model": "x", "run_timeout_seconds": 5}}}}, "differ"),
        ):
            with self.assertRaises(execution_config.ExecutionConfigError, msg=text) as caught:
                execution_config.validate(config_table(**change))
            self.assertIn(text, str(caught.exception))


class GitTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.mirror = root / "mirror"
        env = execution_git._environment()
        subprocess.run(["git", "init", "-q", str(self.mirror)], check=True, env=env)
        (self.mirror / "pkg").mkdir()
        (self.mirror / "pkg" / "a.py").write_text("x = 1\n")
        (self.mirror / "other.py").write_text("y = 1\n")
        execution_git.git(self.mirror, "add", "-A")
        execution_git.git(self.mirror, "commit", "-q", "-m", "base")
        self.base = execution_git.git(self.mirror, "rev-parse", "HEAD").strip()
        self.work = root / "work"
        execution_git.prepare_clone(self.mirror, self.base, self.work, "branch-x")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_leftover_changes_are_committed_and_described_against_the_base(self) -> None:
        (self.work / "pkg" / "a.py").write_text("x = 2\n")
        sealed = execution_git.seal(self.work, self.base, "branch-x", "message")
        self.assertNotEqual(sealed["head"], self.base)
        self.assertEqual(sealed["changed_paths"], ["pkg/a.py"])
        self.assertEqual(execution_git.outside_scope(sealed["changed_paths"], ["pkg"]), [])

    def test_paths_outside_the_permitted_scope_are_found(self) -> None:
        (self.work / "other.py").write_text("y = 2\n")
        sealed = execution_git.seal(self.work, self.base, "branch-x", "message")
        self.assertEqual(execution_git.outside_scope(sealed["changed_paths"], ["pkg", "pkg/a.py"]), ["other.py"])
        self.assertEqual(execution_git.outside_scope(["pkgx/a.py"], ["pkg"]), ["pkgx/a.py"])

    def test_bytecode_caches_from_running_tests_are_not_part_of_the_change(self) -> None:
        (self.work / "pkg").mkdir(exist_ok=True)
        (self.work / "pkg" / "__pycache__").mkdir()
        (self.work / "pkg" / "__pycache__" / "a.cpython-312.pyc").write_bytes(b"x")
        (self.work / "pkg" / "a.py").write_text("changed\n")
        sealed = execution_git.seal(self.work, self.base, "branch-x", "message")
        self.assertEqual(sealed["changed_paths"], ["pkg/a.py"])

    def test_tracked_bytecode_rewritten_by_test_runs_is_restored(self) -> None:
        (self.work / "pkg").mkdir(exist_ok=True)
        (self.work / "pkg" / "__pycache__").mkdir()
        pyc = self.work / "pkg" / "__pycache__" / "a.cpython-312.pyc"
        pyc.write_bytes(b"x")
        execution_git.git(self.work, "add", "-f", "-A")
        execution_git.git(self.work, "commit", "--quiet", "-m", "track bytecode")
        base = execution_git.git(self.work, "rev-parse", "HEAD").strip()
        pyc.write_bytes(b"rewritten")
        (self.work / "pkg" / "a.py").write_text("changed again\n")
        sealed = execution_git.seal(self.work, base, "branch-x", "message")
        self.assertEqual(sealed["changed_paths"], ["pkg/a.py"])

    def test_a_wrong_branch_and_no_change_are_visible(self) -> None:
        with self.assertRaises(execution_git.GitError):
            execution_git.seal(self.work, self.base, "another", "message")
        self.assertEqual(execution_git.seal(self.work, self.base, "branch-x", "message")["head"], self.base)

    def test_a_result_with_a_merge_commit_is_refused(self) -> None:
        execution_git.git(self.work, "checkout", "-q", "-b", "side")
        (self.work / "s.py").write_text("s\n"); execution_git.git(self.work, "add", "-A"); execution_git.git(self.work, "commit", "-q", "-m", "s")
        execution_git.git(self.work, "checkout", "-q", "branch-x")
        (self.work / "t.py").write_text("t\n"); execution_git.git(self.work, "add", "-A"); execution_git.git(self.work, "commit", "-q", "-m", "t")
        execution_git.git(self.work, "merge", "-q", "--no-ff", "-m", "m", "side")
        with self.assertRaises(execution_git.GitError):
            execution_git.seal(self.work, self.base, "branch-x", "message")


class ContractTests(unittest.TestCase):
    check = staticmethod(ExecutionResponseValidator._check_role)

    def test_a_review_must_state_range_and_be_consistent(self) -> None:
        finding = {"local_key": "a", "severity": "blocking"}
        base = {"review_outcome": "APPROVE", "reviewed_range": {"base": "b", "head": "h"}, "findings": []}
        self.check("packet_reviewer", base)
        for bad in ({**base, "findings": [finding]}, {**base, "review_outcome": "REQUEST_CHANGES"}, {**base, "reviewed_range": None}, {**base, "review_outcome": None}):
            with self.assertRaises(TransportError):
                self.check("packet_reviewer", bad)

    def test_a_manager_may_not_request_a_packet_twice_or_nothing(self) -> None:
        launch = {"packet_key": "p", "route_id": "r", "model": "m", "reason": "why"}
        self.check("development_manager", {"launches": [launch], "blockers": [], "priorities": []})
        with self.assertRaises(TransportError):
            self.check("development_manager", {"launches": [launch, launch], "blockers": [], "priorities": []})
        with self.assertRaises(TransportError):
            self.check("development_manager", {"launches": [], "blockers": [], "priorities": []})


def packet_row(key, state="pending", deps=(), paths=("a",), capabilities=("code_edit",), locations=("local_ai_box", "cloud"), route=None, parallel=(), role=True):
    record = {"subject": key, "starting_context": {"specialist_role_ref": {"path": "r.md"}} if role else {}, "permitted_paths": list(paths), "parallel_opportunities": [{"id": p} for p in parallel],
              "execution_requirements": {"required_capabilities": list(capabilities), "allowed_locations": list(locations), "minimum_context_tokens": 8000}}
    return {"packet_key": key, "state": state, "record_json": json.dumps(record), "dependency_keys_json": json.dumps(list(deps)), "route_id": route}


class LaunchChecks(unittest.TestCase):
    def setUp(self) -> None:
        self.config = execution_config.validate(config_table())

    def problem(self, packets, launch, accepted=()):
        table = {p["packet_key"]: p for p in packets}
        return ExecutionService._launch_problem(self.config, table, launch, list(accepted))

    def launch(self, key="p1", route="local", model=None):
        return {"packet_key": key, "route_id": route, "model": model or self.config["coder_routes"].get(route, {"model": "x"})["model"], "reason": "r"}

    def test_a_valid_request_is_accepted(self) -> None:
        self.assertIsNone(self.problem([packet_row("p1")], self.launch()))

    def test_rejections_name_their_reason(self) -> None:
        cases = [
            ([packet_row("p1", "coding")], self.launch(), "not pending"),
            ([packet_row("p1", deps=["p0"]), packet_row("p0", "approved")], self.launch(), "not delivered"),
            ([packet_row("p1")], self.launch(route="none"), "not a configured"),
            ([packet_row("p1")], self.launch(model="other"), "exact model"),
            ([packet_row("p1", capabilities=("approved_network",))], self.launch(), "lacks capabilities"),
            ([packet_row("p1", locations=("cloud",))], self.launch(), "location"),
            ([packet_row("p1"), packet_row("p2", "coding", route="local", paths=("z",))], self.launch(), "capacity"),
            ([packet_row("p1"), packet_row("p2", "coding", route="cloud")], self.launch(route="cloud"), "shares permitted paths"),
        ]
        for packets, launch, text in cases:
            found = self.problem(packets, launch)
            self.assertIsNotNone(found, text)
            self.assertIn(text, found)

    def test_a_packet_without_a_confirmed_role_needs_an_active_support_binding(self) -> None:
        table = {"p1": packet_row("p1", role=False)}
        self.assertIn("no confirmed specialist role", ExecutionService._launch_problem(self.config, table, self.launch(), []))
        self.assertIsNone(ExecutionService._launch_problem(self.config, table, self.launch(), [], (), {"p1"}))

    def test_a_declared_parallel_packet_may_share_paths_and_a_delivered_dependency_unblocks(self) -> None:
        self.assertIsNone(self.problem([packet_row("p1", parallel=("p2",)), packet_row("p2", "coding", route="cloud")], self.launch(route="cloud")))
        self.assertIsNone(self.problem([packet_row("p1", deps=["p0"]), packet_row("p0", "integrated")], self.launch()))

    def test_the_same_batch_cannot_exceed_capacity(self) -> None:
        packets = [packet_row("p1", paths=("a",)), packet_row("p2", paths=("b",))]
        self.assertIsNone(self.problem(packets, self.launch("p1")))
        self.assertIn("capacity", self.problem(packets, self.launch("p2"), [self.launch("p1")]))

    def test_a_nested_permitted_path_counts_as_shared(self) -> None:
        packets = [packet_row("p1", paths=("pkg/file.py",)), packet_row("p2", "coding", paths=("pkg",), route="cloud")]
        self.assertIn("shares permitted paths", self.problem(packets, self.launch("p1")))


class ScriptedRuns:
    def __init__(self):
        self.responses: dict[str, dict] = {}
        self.assignments: dict[str, dict] = {}
        self.rejected = []

    def response(self, run_id):
        return self.responses[run_id]

    def assignment_state(self, assignment_id):
        return self.assignments.get(assignment_id, {"state": "completed"})

    def reject_result(self, run_id, code, reason):
        self.rejected.append((run_id, reason))


class ReviewStateTests(unittest.TestCase):
    """The review outcome decides between approval, one targeted correction, and the Owner's limit decision."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.database = Database(StorageSettings(path=root / "m.sqlite3"))
        from maestro.service.agent_runs import AGENT_RUN_MIGRATION, AGENT_RUN_SESSIONS_MIGRATION
        self.database.registry.register(AGENT_RUN_MIGRATION)
        self.database.registry.register(AGENT_RUN_SESSIONS_MIGRATION)
        records = ActivityRepository(self.database)
        self.runs = ScriptedRuns()
        self.service = ExecutionService(
            self.database, records=records, questions=QuestionService(self.database), reservations=ProjectReservations(self.database), runs=self.runs,
            profiles={}, destination=lambda p: None, state_dir=root / "x", owner_id="owner", config_source=lambda: config_table(),
        )
        config = execution_config.validate(config_table())
        with self.database.transaction() as tx:
            records.create_project(tx, ProjectRecord("proj", "Proj", "registered", 1))
            records.create_activity(tx, ActivityRecord("exec-1", "proj", "execution", "Execution", "running", 1, None, "2026-01-01T00:00:00Z", None, ()))
            tx.execute("INSERT INTO entity_versions(entity_id, version) VALUES ('exec-1', 1)")
            tx.execute(
                "INSERT INTO service_executions(activity_id, project_id, registration_activity_id, architecture_activity_id, registration_json, confirmed_ref_json, repository, profile_json, "
                "source_commit, master_branch, master_commit, observed_at, config_json, config_sha256, bundle_json, manager_route_id, manager_tool, manager_model, state, created_at) "
                "VALUES ('exec-1', 'proj', 'r', 'a', '{}', ?, 'o/r', '{}', 'c', 'main', 'm', 't', ?, 'h', '{}', 'm', 'codex', 'gm', 'running', 't')",
                (json.dumps({"version": 1, "commit": "c", "manifest_path": "m"}), json.dumps(config)))
            tx.execute("INSERT INTO service_execution_packets(activity_id, packet_key, subject, record_json, record_sha256, milestone_key, dependency_keys_json, state, tool, model, round_limit, updated_at, head_commit, result_json, pending_json) "
                       "VALUES ('exec-1', 'p1', 'P1', '{}', 'h', 'm1', '[]', 'reviewing', 'qwen', 'q', 2, 't', 'HEAD1', ?, ?)",
                       (json.dumps({"base": "BASE", "changed_paths": ["a.py"]}), json.dumps({"reviewer": {"tool": "claude_code", "model": "r1"}, "reviewer_run": {"assignment_id": "a-review-1", "run_id": "run-r1"}})))

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def verdict(self, outcome, blocking=0, head="HEAD1"):
        findings = [{"local_key": f"f{i}", "subject": f"S{i}", "severity": "blocking", "explanation": "e", "impact": "i", "requested_correction": "c", "locations": []} for i in range(blocking)]
        return {"result": "completed", "review_outcome": outcome, "reviewed_range": {"base": "BASE", "head": head}, "summary": "s", "independence": "did not author", "findings": findings}

    def run_review(self, run_id, response):
        self.runs.responses[run_id] = response
        row = self.service._read("SELECT * FROM service_executions WHERE activity_id = 'exec-1'")
        packet = self.service._read("SELECT * FROM service_execution_packets WHERE packet_key = 'p1'")
        pending = json.loads(packet["pending_json"])
        pending["reviewer_run"] = {"assignment_id": f"a-{run_id}", "run_id": run_id}
        self.service._accept_review(row, packet, pending, pending["reviewer_run"])
        return self.service._read("SELECT * FROM service_execution_packets WHERE packet_key = 'p1'")

    def test_approval_makes_only_that_revision_eligible(self) -> None:
        packet = self.run_review("run-1", self.verdict("APPROVE"))
        self.assertEqual((packet["state"], packet["rounds_used"]), ("approved", 1))
        events = self.service._rows("SELECT kind FROM service_execution_events WHERE activity_id = 'exec-1'")
        self.assertEqual([e["kind"] for e in events], ["packet_approved"])

    def test_changes_requested_return_one_targeted_correction_then_the_limit_pauses_it(self) -> None:
        packet = self.run_review("run-1", self.verdict("REQUEST_CHANGES", 2))
        self.assertEqual((packet["state"], packet["rounds_used"]), ("reserved", 1))
        pending = json.loads(packet["pending_json"])
        self.assertEqual(len(pending["correction"]["findings"]), 2)
        self.service.database  # a second review of the corrected revision
        with self.database.transaction() as tx:
            tx.execute("UPDATE service_execution_packets SET state = 'reviewing' WHERE packet_key = 'p1'")
        packet = self.run_review("run-2", self.verdict("REQUEST_CHANGES", 1))
        self.assertEqual((packet["state"], packet["rounds_used"]), ("limit_paused", 2))
        self.assertNotEqual(packet["state"], "approved")
        view = self.service.view("exec-1")
        self.assertEqual(view["owner_decisions"][0]["packet_key"], "p1")

    def test_a_review_of_another_revision_is_rejected_and_not_counted(self) -> None:
        packet = self.run_review("run-1", self.verdict("APPROVE", head="OTHER"))
        self.assertEqual(packet["rounds_used"], 0)
        self.assertNotEqual(packet["state"], "approved")
        self.assertTrue(self.runs.rejected)

    def test_the_owner_grant_adds_one_round_and_cannot_force_approval(self) -> None:
        self.run_review("run-1", self.verdict("REQUEST_CHANGES", 1))
        with self.database.transaction() as tx:
            tx.execute("UPDATE service_execution_packets SET state = 'reviewing' WHERE packet_key = 'p1'")
        self.run_review("run-2", self.verdict("REQUEST_CHANGES", 1))
        registry = OperationRegistry(self.service.operation_handlers)
        request = SimpleNamespace(request_id="r1", operation="owner.decision", project_id="proj", activity_id="exec-1", question_id=None, expected_version=None,
                                  payload={"target": "packet_review", "choice": "grant_one", "assignment_id": "a-run-2"})
        version = self.service._read("SELECT version FROM entity_versions WHERE entity_id = 'exec-1'")["version"]
        request.expected_version = version
        prepared = self.service.prepare_owner_decision(request)
        with self.assertRaises(Exception) as caught, self.database.transaction() as tx:
            prepared.apply(tx, version + 1)  # the grant waits for the architect's saved recommendation
        self.assertIn("recommendation", str(caught.exception))
        save_recommendation(self.database, "a-run-2", "grant_one")
        prepared = self.service.prepare_owner_decision(request)
        with self.database.transaction() as tx:
            prepared.apply(tx, version + 1)
        packet = self.service._read("SELECT * FROM service_execution_packets WHERE packet_key = 'p1'")
        self.assertEqual((packet["state"], packet["rounds_used"]), ("reserved", 2))
        view = self.service.view("exec-1")
        self.assertEqual(view["packets"][0]["review"], {"completed": 2, "limit": 3})
        with self.database.transaction() as tx:
            tx.execute("UPDATE service_execution_packets SET state = 'reviewing' WHERE packet_key = 'p1'")
        packet = self.run_review("run-3", self.verdict("REQUEST_CHANGES", 1))
        self.assertEqual((packet["state"], packet["rounds_used"]), ("limit_paused", 3))


if __name__ == "__main__":
    unittest.main()
