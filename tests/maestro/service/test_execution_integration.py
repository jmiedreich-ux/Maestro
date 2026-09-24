"""Execution integration: milestone branches, the FIFO queue, integration review, target changes, dependency delivery and invalidation.

The remote is a real local bare Git repository reached through the same handler calls the service makes on GitHub;
the agents are scripted (they edit the real working clone the service prepared, then answer). Real agents,
GitHub and the installed path are proven in var/qa/execution-live.
"""
from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from maestro.foundation import Database, StorageSettings
from maestro.service import execution_config, execution_git
from maestro.service.activities import ActivityRecord, ActivityRepository, ProjectRecord
from maestro.service.agent_runs import AgentRunError
from maestro.service.execution import ExecutionService
from maestro.service.execution_integration import is_delivered, milestone_closure
from maestro.service.questions import QuestionService
from maestro.service.registration_github import DestinationError
from maestro.service.reservations import ProjectReservations

from test_execution import config_table

ENV = execution_git._environment()


def sh(cwd: Path, *args: str) -> str:
    done = subprocess.run(["git", "-c", "safe.directory=*", "-C", str(cwd), *args], capture_output=True, text=True, env=ENV, check=True)
    return done.stdout.strip()


class LocalDestination:
    """The GitHub destination's code-branch calls, served by a local bare repository."""

    def __init__(self, bare: Path) -> None:
        self.bare = bare

    def _run(self, *args: str, check: bool = True) -> subprocess.CompletedProcess:
        return subprocess.run(["git", "-c", "safe.directory=*", "-C", str(self.bare), *args], capture_output=True, text=True, env=ENV, check=check)

    def branch_head(self, repository, branch):
        done = self._run("rev-parse", "--verify", "-q", f"refs/heads/{branch}", check=False)
        return done.stdout.strip() or None

    def fetch_source(self, repository, commit, mirror: Path) -> None:
        mirror.parent.mkdir(parents=True, exist_ok=True)
        if not (mirror / ".git" / "HEAD").exists():
            subprocess.run(["git", "init", "-q", str(mirror)], check=True, env=ENV)
        have = subprocess.run(["git", "-C", str(mirror), "cat-file", "-e", f"{commit}^{{commit}}"], capture_output=True, env=ENV)
        if have.returncode != 0:
            subprocess.run(["git", "-C", str(mirror), "fetch", "-q", "--no-tags", str(self.bare), commit], check=True, env=ENV, capture_output=True)

    def push_branch(self, repository, workdir, branch, commit, expected_before=None):
        remote = self.branch_head(repository, branch)
        if remote == commit:
            return commit
        if expected_before is not None and remote != expected_before:
            raise DestinationError("target_changed", f"the branch {branch} moved", remote=remote)
        done = subprocess.run(["git", "-c", "safe.directory=*", "-C", str(workdir), "push", "-q", str(self.bare), f"{commit}:refs/heads/{branch}"], capture_output=True, text=True, env=ENV)
        if done.returncode != 0:
            raise DestinationError("push_failed", done.stderr[-200:])
        return self.branch_head(repository, branch)

    def contains(self, repository, ancestor, descendant):
        return self._run("merge-base", "--is-ancestor", ancestor, descendant, check=False).returncode == 0


class FakeRuns:
    """The run service's surface the integration steps use; a run's workspace is a real directory the test's 'agent' edits."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.assignments: dict[str, dict] = {}
        self.runs: dict[str, dict] = {}
        self.rejected: list[str] = []

    def create_assignment(self, assignment_id, project_id, activity_id, role, tool, model, duration_seconds, automatic_limit):
        self.assignments[assignment_id] = {"state": "running", "role": role, "tool": tool, "model": model}

    def assignment_state(self, assignment_id):
        if assignment_id not in self.assignments:
            raise AgentRunError("unknown_assignment", "no such assignment")
        return self.assignments[assignment_id]

    def run_count(self, assignment_id):
        return sum(1 for r in self.runs.values() if r["assignment"] == assignment_id)

    def start_run(self, assignment_id, run_id, kind, build, intervention=""):
        run_build = build(run_id)
        output = self.root / run_id / "output"
        scratch = self.root / run_id / "scratch"
        output.mkdir(parents=True)
        scratch.mkdir(parents=True)
        if run_build.prepare:
            run_build.prepare(SimpleNamespace(paths=SimpleNamespace(output=output, scratch=scratch)))
        self.runs[run_id] = {"assignment": assignment_id, "build": run_build, "output": output, "state": "running", "response": None}

    def poll(self, run_id):
        return SimpleNamespace(state=self.runs[run_id]["state"], failure_code=None, terminal_reason=None)

    def response(self, run_id):
        return self.runs[run_id]["response"]

    def run_evidence(self, run_id):
        return {}

    def reject_result(self, run_id, code, reason):
        self.rejected.append(reason)
        self.assignments[self.runs[run_id]["assignment"]]["state"] = "needs_recovery"

    def finish(self, run_id, response):
        self.runs[run_id]["state"] = "completed"
        self.runs[run_id]["response"] = response

    def last(self, role):
        for run_id in reversed(list(self.runs)):
            if self.runs[run_id]["build"].assignment.role == role:
                return run_id
        raise AssertionError(f"no {role} run")


class IntegrationBase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        # a real remote with a baseline commit
        self.bare = self.root / "remote.git"
        subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(self.bare)], check=True, env=ENV)
        self.work = self.root / "seed"
        subprocess.run(["git", "init", "-q", "-b", "main", str(self.work)], check=True, env=ENV)
        (self.work / "app").mkdir()
        (self.work / "app" / "a.py").write_text("one = 1\ntwo = 2\nthree = 3\n")
        (self.work / "app" / "b.py").write_text("b = 0\n")
        sh(self.work, "add", "-A")
        sh(self.work, "commit", "-q", "-m", "baseline")
        self.base = sh(self.work, "rev-parse", "HEAD")
        sh(self.work, "push", "-q", str(self.bare), "main")
        self.dest = LocalDestination(self.bare)
        self.database = Database(StorageSettings(path=self.root / "m.sqlite3"))
        from maestro.service.agent_runs import AGENT_RUN_MIGRATION, AGENT_RUN_SESSIONS_MIGRATION
        self.database.registry.register(AGENT_RUN_MIGRATION)
        self.database.registry.register(AGENT_RUN_SESSIONS_MIGRATION)
        records = ActivityRepository(self.database)
        self.runs = FakeRuns(self.root / "runs")
        self.service = ExecutionService(
            self.database, records=records, questions=QuestionService(self.database), reservations=ProjectReservations(self.database), runs=self.runs,
            profiles={"prof": None}, destination=lambda p: self.dest, state_dir=self.root / "state", owner_id="owner", config_source=lambda: config_table(),
        )
        self.service._run_workspace = lambda run_id: self.runs.runs[run_id]["output"]
        self.service._advance_manager = lambda row: None  # planning is the Development Manager's, proven elsewhere
        self.service._advance_packet = lambda row, packet: None  # coding and packet review are proven elsewhere
        config = execution_config.validate(config_table())
        with self.database.transaction() as tx:
            records.create_project(tx, ProjectRecord("proj", "Proj", "registered", 1))
            records.create_activity(tx, ActivityRecord("exec-1", "proj", "execution", "Execution", "running", 1, None, "2026-01-01T00:00:00Z", None, ()))
            tx.execute("INSERT INTO entity_versions(entity_id, version) VALUES ('exec-1', 1)")
            tx.execute(
                "INSERT INTO service_executions(activity_id, project_id, registration_activity_id, architecture_activity_id, registration_json, confirmed_ref_json, repository, profile_json, "
                "source_commit, master_branch, master_commit, observed_at, config_json, config_sha256, bundle_json, manager_route_id, manager_tool, manager_model, state, created_at) "
                "VALUES ('exec-1', 'proj', 'r', 'a', '{}', ?, 'o/r', '{\"profile\": \"prof\"}', ?, 'main', ?, 't', ?, 'h', '{}', 'm', 'claude_code', 'claude-x', 'running', 't')",
                (json.dumps({"version": 1, "commit": "c", "manifest_path": "m", "listing": []}), self.base, self.base, json.dumps(config)))
            for key, deps in (("m1", []), ("m2", ["m1"]), ("m3", [])):
                tx.execute("INSERT INTO service_execution_milestones(activity_id, milestone_key, subject, record_json, record_sha256, dependencies_json, updated_at) VALUES ('exec-1', ?, ?, ?, 'h', ?, 't')",
                           (key, f"Milestone {key}", json.dumps({"id": key, "outcome": f"outcome of {key}"}), json.dumps(deps)))

    def tearDown(self) -> None:
        self.tmp.cleanup()

    # -- helpers

    def packet_branch(self, key: str, files: dict[str, str], base: str | None = None) -> str:
        """A real packet branch on the remote holding one commit on top of ``base``."""
        clone = self.root / f"clone-{key}"
        subprocess.run(["git", "clone", "-q", str(self.bare), str(clone)], check=True, env=ENV)
        sh(clone, "checkout", "-q", "-b", key, base or self.base)
        for path, text in files.items():
            (clone / path).parent.mkdir(parents=True, exist_ok=True)
            (clone / path).write_text(text)
        sh(clone, "add", "-A")
        sh(clone, "commit", "-q", "-m", key)
        head = sh(clone, "rev-parse", "HEAD")
        sh(clone, "push", "-q", str(self.bare), f"{head}:refs/heads/packet/{key}")
        return head

    def add_packet(self, key, milestone, head, state="approved", deps=(), paths=("app",), tool="qwen", model="q"):
        record = {"id": key, "subject": key, "permitted_paths": list(paths), "parallel_opportunities": []}
        with self.database.transaction() as tx:
            tx.execute(
                "INSERT INTO service_execution_packets(activity_id, packet_key, subject, record_json, record_sha256, milestone_key, dependency_keys_json, state, tool, model, round_limit, updated_at, head_commit, base_commit, branch) "
                "VALUES ('exec-1', ?, ?, ?, 'h', ?, ?, ?, ?, ?, 2, 't', ?, ?, ?)",
                (key, key, json.dumps(record), milestone, json.dumps(list(deps)), state, tool, model, head, self.base, f"packet/{key}"))
            if state == "approved":
                tx.execute(
                    "INSERT INTO service_execution_reviews(activity_id, packet_key, review_round, assignment_id, run_id, reviewer_tool, reviewer_model, author_tool, author_model, reviewed_base, reviewed_head, outcome, summary, findings_json, independence, created_at) "
                    "VALUES ('exec-1', ?, 1, 'x', 'x', 'claude_code', 'r', ?, ?, ?, ?, 'APPROVE', 's', '[]', 'i', ?)", (key, tool, model, self.base, head, f"2026-01-01T00:00:0{len(key) % 10}Z"))

    def row(self):
        return self.service._read("SELECT * FROM service_executions WHERE activity_id = 'exec-1'")

    def tick(self):
        self.service.advance("exec-1")

    def entry(self, entry_id=1):
        return self.service._entry("exec-1", entry_id)

    def packet(self, key):
        return self.service._read("SELECT * FROM service_execution_packets WHERE packet_key = ?", (key,))

    def integrator_finishes(self, edit=None, blockers=(), changed=()):
        run_id = self.runs.last("integration_manager")
        run = self.runs.runs[run_id]
        work = run["output"] / "work"
        if edit:
            edit(work)
        pending = json.loads(self.active_entry()["pending_json"])
        self.runs.finish(run_id, {"result": "completed", "base_revision": pending["run_base"], "changed_paths": list(changed), "checks": [{"command": "python -c 'pass'", "outcome": "passed", "detail": "ok"}],
                                  "evidence": ["assembled"], "limitations": [], "blockers": list(blockers), "unfinished": [], "summary": "s", "questions": []})
        self.tick()  # the result is checked and sealed
        if self.active_entry()["state"] == "publishing":
            self.tick()  # the integration branch is pushed and read back

    def active_entry(self):
        return next(e for e in self.service._queue("exec-1") if e["state"] not in ("merged", "withdrawn", "invalidated"))

    def entry_pending(self, entry_id=1):
        return self.entry(entry_id)["pending_json"]

    def reviewer_answers(self, outcome, blocking=0):
        run_id = self.runs.last("integration_reviewer")
        entry = next(e for e in self.service._queue("exec-1") if e["state"] == "reviewing")
        result = json.loads(entry["result_json"])
        findings = [{"local_key": f"f{i}", "subject": f"S{i}", "severity": "blocking", "explanation": "e", "impact": "i", "requested_correction": "c", "locations": []} for i in range(blocking)]
        self.runs.finish(run_id, {"result": "completed", "review_outcome": outcome, "reviewed_range": {"base": result["target"], "head": entry["head_commit"]}, "summary": "s", "independence": "did not author",
                                  "findings": findings, "questions": []})


class MilestoneAndQueueTests(IntegrationBase):
    def test_a_milestone_branch_is_created_once_from_the_baseline_and_verified(self) -> None:
        milestone = self.service._ensure_branch(self.row(), "m1")
        self.assertEqual(milestone["branch"], "maestro/exec-1/milestone/m1")
        self.assertEqual((milestone["base_commit"], milestone["head_commit"]), (self.base, self.base))
        self.assertEqual(self.dest.branch_head("o/r", milestone["branch"]), self.base)
        self.assertEqual(self.service._ensure_branch(self.row(), "m1")["head_commit"], self.base)
        journal = self.service._rows("SELECT kind, state FROM service_execution_journal")
        self.assertEqual([(j["kind"], j["state"]) for j in journal], [("milestone_create", "verified")])

    def test_a_clean_integration_needs_no_review_and_merges_without_fast_forward_in_queue_order(self) -> None:
        h1 = self.packet_branch("p1", {"app/a.py": "one = 10\ntwo = 2\nthree = 3\n"})
        h2 = self.packet_branch("p2", {"app/b.py": "b = 5\n"})
        self.add_packet("p1", "m1", h1)
        self.add_packet("p2", "m1", h2)
        self.tick()
        self.assertEqual([(e["entry_id"], e["packet_key"], e["state"]) for e in self.service._queue("exec-1")], [(1, "p1", "integrating"), (2, "p2", "queued")])
        self.assertEqual(self.runs.run_count("exec-1-q1a1-integrate-1"), 1)
        self.assertEqual(self.entry()["state"], "integrating")
        self.integrator_finishes()
        self.assertEqual(self.entry()["state"], "merging")
        self.assertFalse(json.loads(self.entry()["result_json"])["changed"])
        self.assertEqual(self.dest.branch_head("o/r", "maestro/exec-1/integration/q1"), self.entry()["head_commit"])
        self.tick()
        entry, packet = self.entry(), self.packet("p1")
        self.assertEqual((entry["state"], packet["state"]), ("merged", "integrated"))
        milestone_head = self.dest.branch_head("o/r", "maestro/exec-1/milestone/m1")
        self.assertEqual(milestone_head, entry["merged_commit"])
        parents = sh(self.bare, "rev-list", "--parents", "-n", "1", milestone_head).split()
        self.assertEqual(len(parents), 3, "the milestone merge has two parents")
        self.assertEqual(parents[1], self.base)
        self.assertEqual(sh(self.bare, "show", f"{milestone_head}:app/a.py"), "one = 10\ntwo = 2\nthree = 3")
        # the next entry starts only now, from the moved milestone head
        self.tick()
        self.assertEqual((self.entry(2)["state"], self.entry(2)["target_before"]), ("integrating", milestone_head))
        kinds = [j["kind"] for j in self.service._rows("SELECT kind FROM service_execution_journal ORDER BY created_at, rowid")]
        self.assertEqual(kinds, ["milestone_create", "integration_push", "milestone_merge"])

    def test_a_blocked_head_keeps_its_place_and_nothing_behind_it_starts(self) -> None:
        h1 = self.packet_branch("p1", {"app/a.py": "one = 10\ntwo = 2\nthree = 3\n"})
        h2 = self.packet_branch("p2", {"app/b.py": "b = 5\n"})
        self.add_packet("p1", "m1", h1)
        self.add_packet("p2", "m1", h2)
        self.tick()
        self.integrator_finishes(blockers=["the packet needs a scope change"])
        self.tick()
        self.assertEqual(self.entry()["state"], "blocked")
        for _ in range(3):
            self.tick()
        self.assertEqual((self.entry(1)["state"], self.entry(2)["state"]), ("blocked", "queued"))
        self.assertEqual(self.runs.run_count("exec-1-q2a1-integrate-1"), 0)

    def test_conflicts_are_resolved_by_the_manager_reviewed_by_another_agent_and_merged_after_approval(self) -> None:
        h1 = self.packet_branch("p1", {"app/a.py": "one = 10\ntwo = 2\nthree = 3\n"})
        h2 = self.packet_branch("p2", {"app/a.py": "one = 11\ntwo = 2\nthree = 3\n"})
        self.add_packet("p1", "m1", h1)
        self.add_packet("p2", "m1", h2)
        self.tick()
        self.integrator_finishes()
        self.tick()
        self.tick()  # p1 merged
        self.tick()  # p2 starts: conflicts with p1
        pending = json.loads(self.entry_pending(2))
        self.assertEqual(pending["conflicts"], ["app/a.py"])
        self.assertEqual(self.entry(2)["state"], "integrating")
        unresolved = self.integrator_finishes  # the manager leaves the conflict unresolved first
        run_id = self.runs.last("integration_manager")
        self.runs.finish(run_id, {"result": "completed", "base_revision": pending["run_base"], "changed_paths": [], "checks": [{"command": "x", "outcome": "passed", "detail": "d"}], "evidence": [], "limitations": [], "blockers": [], "unfinished": [], "summary": "s", "questions": []})
        self.tick()
        self.assertTrue(self.runs.rejected and "conflict markers" in self.runs.rejected[-1], "an unresolved merge is refused")
        del unresolved
        # a recovery run resolves it properly
        self.tick()
        self.integrator_finishes(edit=lambda work: (work / "app" / "a.py").write_text("one = 11\ntwo = 2\nthree = 3\n"), changed=["app/a.py"])
        self.tick()
        entry = self.entry(2)
        self.assertEqual(entry["state"], "reviewing", entry["note"])
        # independence: the reviewer differs from the integrator (claude_code claude-x is the manager route)
        review = self.runs.runs[self.runs.last("integration_reviewer")]["build"].assignment
        self.assertEqual(review.role, "integration_reviewer")
        assignment = self.runs.assignments[review.assignment_id]
        self.assertNotEqual((assignment["tool"], assignment["model"]), ("claude_code", "claude-x"))
        self.reviewer_answers("APPROVE")
        self.tick()
        self.assertEqual(self.entry(2)["state"], "merging")
        self.tick()
        self.assertEqual((self.entry(2)["state"], self.packet("p2")["state"]), ("merged", "integrated"))
        head = self.dest.branch_head("o/r", "maestro/exec-1/milestone/m1")
        self.assertEqual(sh(self.bare, "show", f"{head}:app/a.py"), "one = 11\ntwo = 2\nthree = 3")
        self.assertEqual(len(sh(self.bare, "rev-list", "--parents", "-n", "1", head).split()), 3)

    def test_changes_requested_return_one_correction_and_the_limit_needs_the_owner(self) -> None:
        h1 = self.packet_branch("p1", {"app/a.py": "one = 10\ntwo = 2\nthree = 3\n"})
        self.add_packet("p1", "m1", h1)
        self.tick()
        self.integrator_finishes(edit=lambda work: (work / "app" / "b.py").write_text("b = 1\n"), changed=["app/b.py"])
        self.tick()
        self.assertEqual(self.entry()["state"], "reviewing")
        self.assertTrue(json.loads(self.entry()["result_json"])["changed"])
        self.reviewer_answers("REQUEST_CHANGES", 1)
        self.tick()
        self.assertEqual((self.entry()["state"], self.entry()["rounds_used"]), ("queued", 1))
        self.tick()  # the correction run starts from the reviewed integration head
        self.assertEqual(self.entry()["state"], "integrating")
        first_head = self.entry()["head_commit"]
        self.integrator_finishes(edit=lambda work: (work / "app" / "b.py").write_text("b = 2\n"), changed=["app/b.py"])
        self.tick()
        self.assertNotEqual(self.entry()["head_commit"], first_head)
        self.assertTrue(sh(self.bare, "merge-base", "--is-ancestor", first_head, self.entry()["head_commit"]) == "")
        self.reviewer_answers("REQUEST_CHANGES", 1)
        self.tick()
        self.assertEqual((self.entry()["state"], self.entry()["rounds_used"]), ("limit_paused", 2))
        self.assertEqual(self.packet("p1")["state"], "approved")
        view = self.service.view("exec-1")
        self.assertEqual(view["owner_decisions"][0]["target"], "integration_review")
        request = SimpleNamespace(request_id="r1", operation="owner.decision", project_id="proj", activity_id="exec-1", question_id=None,
                                  expected_version=self.service._read("SELECT version FROM entity_versions WHERE entity_id = 'exec-1'")["version"],
                                  payload={"target": "integration_review", "choice": "grant_one", "assignment_id": view["owner_decisions"][0]["assignment_id"]})
        prepared = self.service.prepare_owner_decision(request)
        with self.assertRaises(Exception) as caught, self.database.transaction() as tx:
            prepared.apply(tx, request.expected_version + 1)  # the grant waits for the architect's saved recommendation
        self.assertIn("recommendation", str(caught.exception))
        from test_execution import save_recommendation
        save_recommendation(self.database, view["owner_decisions"][0]["assignment_id"], "grant_one")
        prepared = self.service.prepare_owner_decision(request)
        with self.database.transaction() as tx:
            prepared.apply(tx, request.expected_version + 1)
        self.assertEqual(self.entry()["state"], "queued")
        self.assertEqual(self.service.view("exec-1")["integration"]["queue"][0]["review"], {"completed": 2, "limit": 3})

    def test_a_target_that_changed_is_reconciled_with_a_new_attempt_and_review_not_overwritten(self) -> None:
        h1 = self.packet_branch("p1", {"app/a.py": "one = 10\ntwo = 2\nthree = 3\n"})
        self.add_packet("p1", "m1", h1)
        self.tick()
        self.integrator_finishes()
        self.assertEqual(self.entry()["state"], "merging")
        # someone else adds a commit to the milestone branch after the integration was prepared
        outside = self.packet_branch("outside", {"app/c.py": "c = 1\n"})
        milestone = "maestro/exec-1/milestone/m1"
        sh(self.bare, "update-ref", f"refs/heads/{milestone}", outside)
        self.assertFalse(self.dest.contains("o/r", outside, self.base) and False)
        self.tick()
        entry = self.entry()
        self.assertEqual((entry["state"], entry["attempt"]), ("queued", 2), entry["note"])
        self.assertEqual(self.dest.branch_head("o/r", milestone), outside, "the remote branch was not overwritten")
        self.tick()
        self.assertEqual(self.entry()["target_before"], outside)
        self.assertEqual(self.entry()["branch"], "maestro/exec-1/integration/q1r2")


class DependencyDeliveryTests(IntegrationBase):
    def integrated_provider(self):
        h1 = self.packet_branch("p1", {"app/a.py": "one = 10\ntwo = 2\nthree = 3\n"})
        self.add_packet("p1", "m1", h1)
        self.tick()
        self.integrator_finishes()
        self.tick()
        self.tick()
        self.assertEqual(self.packet("p1")["state"], "integrated")

    def test_an_integrated_packet_is_delivered_to_a_dependent_milestone_through_the_queue(self) -> None:
        self.integrated_provider()
        self.add_packet("p3", "m2", None, state="pending", deps=("p1",))
        self.tick()
        deliveries = self.service._deliveries("exec-1")
        self.assertEqual([(d["delivery_id"], d["state"], d["provider_milestone"], d["consumer_milestone"]) for d in deliveries], [("dep-1", "queued", "m1", "m2")])
        provider_head = self.dest.branch_head("o/r", "maestro/exec-1/milestone/m1")
        self.assertEqual(deliveries[0]["source_commit"], provider_head)
        self.assertEqual(json.loads(deliveries[0]["packet_set_json"]), ["p1"])
        packets = {p["packet_key"]: p for p in self.service._packets("exec-1")}
        self.assertFalse(is_delivered(packets, deliveries, packets["p3"], "p1"), "an integrated provider is not yet delivered to another milestone")
        entry = next(e for e in self.service._queue("exec-1") if e["kind"] == "dependency_import")
        self.assertEqual(entry["milestone_key"], "m2")
        self.tick()
        self.integrator_finishes()
        self.tick()
        self.tick()
        deliveries = self.service._deliveries("exec-1")
        self.assertEqual(deliveries[0]["state"], "delivered")
        consumer = self.dest.branch_head("o/r", "maestro/exec-1/milestone/m2")
        self.assertEqual(deliveries[0]["import_commit"], consumer)
        self.assertEqual(sh(self.bare, "show", f"{consumer}:app/a.py"), "one = 10\ntwo = 2\nthree = 3")
        self.assertTrue(sh(self.bare, "merge-base", "--is-ancestor", provider_head, consumer) == "")
        self.assertEqual(len(sh(self.bare, "rev-list", "--parents", "-n", "1", consumer).split()), 3)
        packets = {p["packet_key"]: p for p in self.service._packets("exec-1")}
        self.assertTrue(is_delivered(packets, deliveries, packets["p3"], "p1"))
        self.assertEqual(self.dest.branch_head("o/r", "maestro/exec-1/dependency/dep-1"), self.entry(2)["head_commit"])

    def test_a_dependency_on_an_undeclared_milestone_is_held_for_source_completion_and_imports_nothing(self) -> None:
        self.integrated_provider()
        self.add_packet("p9", "m3", None, state="pending", deps=("p1",))  # m3 does not declare m1
        self.tick()
        deliveries = self.service._deliveries("exec-1")
        self.assertEqual([(d["state"], d["consumer_milestone"]) for d in deliveries], [("held", "m3")])
        self.assertIn("not a declared dependency", deliveries[0]["note"])
        self.assertEqual([e for e in self.service._queue("exec-1") if e["kind"] == "dependency_import"], [])
        self.assertIsNone(self.dest.branch_head("o/r", "maestro/exec-1/milestone/m3"))
        packets = {p["packet_key"]: p for p in self.service._packets("exec-1")}
        self.assertFalse(is_delivered(packets, deliveries, packets["p9"], "p1"))
        self.tick()
        self.assertEqual(len(self.service._deliveries("exec-1")), 1, "the hold is recorded once")

    def test_changed_source_evidence_invalidates_the_delivery_and_its_consumers_and_keeps_old_records(self) -> None:
        self.integrated_provider()
        self.add_packet("p3", "m2", None, state="pending", deps=("p1",))
        self.add_packet("p4", "m2", "HEADX", state="coding", deps=("p1",))
        self.tick()
        self.integrator_finishes()
        self.tick()
        self.assertEqual(self.service._deliveries("exec-1")[0]["state"], "delivered")
        # the providing branch is rewritten to history without the delivered source
        provider = "maestro/exec-1/milestone/m1"
        sh(self.bare, "update-ref", f"refs/heads/{provider}", self.base)
        with self.database.transaction() as tx:
            tx.execute("UPDATE service_executions SET pending_json = '{}' WHERE activity_id = 'exec-1'")
        self.service._verify_deliveries(self.row())
        delivery = self.service._deliveries("exec-1")[0]
        self.assertEqual(delivery["state"], "invalidated")
        self.assertEqual(delivery["import_commit"], self.dest.branch_head("o/r", "maestro/exec-1/milestone/m2"), "the old record is retained")
        self.assertIn("replacement delivery", self.packet("p3")["note"])
        self.assertIn("quarantined", json.loads(self.packet("p4")["pending_json"]))
        events = [e["kind"] for e in self.service._rows("SELECT kind FROM service_execution_events WHERE activity_id = 'exec-1'")]
        self.assertIn("dependency_invalidated", events)
        packets = {p["packet_key"]: p for p in self.service._packets("exec-1")}
        self.assertFalse(is_delivered(packets, self.service._deliveries("exec-1"), packets["p3"], "p1"))


class PureRuleTests(unittest.TestCase):
    def test_the_dependency_closure_is_transitive(self) -> None:
        milestones = {"a": {"dependencies_json": "[]"}, "b": {"dependencies_json": '["a"]'}, "c": {"dependencies_json": '["b"]'}, "d": {"dependencies_json": "[]"}}
        self.assertEqual(milestone_closure(milestones, "c"), {"a", "b"})
        self.assertEqual(milestone_closure(milestones, "d"), set())

    def test_a_dependency_in_the_same_milestone_needs_only_integration(self) -> None:
        packets = {"p1": {"state": "integrated", "milestone_key": "m1"}, "p2": {"state": "pending", "milestone_key": "m1"}, "p0": {"state": "approved", "milestone_key": "m1"}}
        self.assertTrue(is_delivered(packets, [], packets["p2"], "p1"))
        self.assertFalse(is_delivered(packets, [], packets["p2"], "p0"), "review approval alone is not delivery")


if __name__ == "__main__":
    unittest.main()
