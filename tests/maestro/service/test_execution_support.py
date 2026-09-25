"""Execution architectural support: a missing specialist reaches its own bounded assignment, a new role is independently
reviewed, the exact files are published and read back, and only then is the role bound and the manager told.

The remote is a real local bare Git repository reached through the same handler calls the service makes on GitHub; agents
are scripted. Real agents, GitHub and the installed path are proven in var/qa/architecture-gaps-live.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import unittest

from maestro.service import execution_config
from maestro.service.agent_runs import AgentRunError
from maestro.service.registration_github import DestinationError

from test_execution import config_table
from test_execution_integration import ENV, IntegrationBase, LocalDestination, sh

SUPPORT = {
    "architect": {"primary": {"tool": "claude_code", "model": "arch-1"}, "backup": {"tool": "codex", "model": "arch-2"}, "run_timeout_seconds": 60},
    "fidelity_reviewer": {"primary": {"tool": "claude_code", "model": "arch-1"}, "backup": {"tool": "codex", "model": "rev-2"}, "run_timeout_seconds": 60},
    "maximum_fidelity_reviews": 2,
}
ROLE = "# Billing specialist\n\n## Responsibility\nOwns billing.\n\n## Authority\nBilling only.\n\n## Source area\napp/billing\n\n## Inputs and outputs\nReads invoices.\n"
CONTEXT = "# Billing context\n\n## Verified facts\n- app/billing/a.py exists.\n\n## Source references\napp/billing\n\n## Knowledge gaps\nNone.\n"


class PublishingDestination(LocalDestination):
    def head(self, repository, branch):
        return self.branch_head(repository, branch)

    def read_file(self, repository, commit, path):
        done = subprocess.run(["git", "-c", "safe.directory=*", "-C", str(self.bare), "show", f"{commit}:{path}"], capture_output=True, env=ENV)
        return done.stdout if done.returncode == 0 else None

    def publish(self, repository, branch, files, message, replaceable=frozenset()):
        head = self.branch_head(repository, branch)
        conflicts = [p for p, d in files.items() if self.read_file(repository, head, p) not in (None, d)]
        if conflicts:
            raise DestinationError("publication_conflict", "a target path already holds different content", paths=conflicts)
        if all(self.read_file(repository, head, p) == d for p, d in files.items()):
            return head
        clone = self.bare.parent / f"pub-{abs(hash(message)) % 10**8}"
        subprocess.run(["git", "clone", "-q", str(self.bare), str(clone)], check=True, env=ENV)
        for path, data in files.items():
            (clone / path).parent.mkdir(parents=True, exist_ok=True)
            (clone / path).write_bytes(data)
        sh(clone, "add", "-A")
        sh(clone, "commit", "-q", "-m", message)
        commit = sh(clone, "rev-parse", "HEAD")
        sh(clone, "push", "-q", str(self.bare), f"{commit}:refs/heads/{branch}")
        return commit

    def verify_files(self, repository, commit, files):
        for path, data in files.items():
            if self.read_file(repository, commit, path) != data:
                raise DestinationError("verification_failed", f"{path} does not match")


class SupportBase(IntegrationBase):
    def setUp(self) -> None:
        super().setUp()
        self.dest = PublishingDestination(self.bare)
        self.service._destination = lambda p: self.dest
        self.service._publication_branch = lambda row: "main"
        self.service._advance_integration = lambda row: None
        self.runs.route_resolver = lambda role, tool, model: None
        self.configure(SUPPORT)
        self.add_packet("pb", "m1", self.base, state="pending", paths=("app/billing",))

    def configure(self, support) -> None:
        config = execution_config.validate(config_table(**({"architectural_support": support} if support else {})))
        with self.database.transaction() as tx:
            tx.execute("UPDATE service_executions SET config_json = ? WHERE activity_id = 'exec-1'", (json.dumps(config),))

    def request(self, key="pb", reason="no role covers billing"):
        with self.database.transaction() as tx:
            problem = self.service._request_support(tx, self.row(), self.packet(key), reason)
        self.assertIsNone(problem)

    def support(self, n=1):
        return self.service._architect("exec-1", f"support-{n}")

    def architect_answers(self, **over):
        run_id = self.runs.last("support_architect")
        body = {"result": "completed", "summary": "s", "questions": [], "disposition": "create_role", "rationale": "billing has no role",
                "existing_role_path": None, "source_area": "app/billing", "role_title": "Billing specialist", "role_markdown": ROLE, "context_markdown": CONTEXT, "packet_keys": ["pb"]}
        body.update(over)
        self.runs.finish(run_id, body)
        self.tick()

    def reviewer_answers(self, outcome="APPROVE", blocking=0, range_override=None):
        if "reviewer_run" not in json.loads(self.support()["pending_json"]):
            self.tick()  # the reviewer starts on the step after the draft is accepted
        run_id = self.runs.last("support_reviewer")
        arch = self.support()
        span = range_override or self.service._reviewed_range(arch, json.loads(arch["result_json"]))
        findings = [{"local_key": f"f{i}", "subject": f"S{i}", "severity": "blocking", "explanation": "e", "impact": "i", "requested_correction": "c", "locations": []} for i in range(blocking)]
        self.runs.finish(run_id, {"result": "completed", "review_outcome": outcome, "reviewed_range": span, "summary": "reviewed", "independence": "did not author", "findings": findings, "questions": []})
        self.tick()


class SupportFlowTests(SupportBase):
    def test_a_missing_role_is_drafted_reviewed_published_bound_and_the_manager_is_told(self) -> None:
        self.request()
        self.assertEqual(self.support()["state"], "requested")
        self.assertIn("pb", self.service._held_packets("exec-1"), "the packet does not start while support is unresolved")
        self.tick()
        self.assertEqual(self.support()["state"], "drafting")
        architect = self.runs.runs[self.runs.last("support_architect")]["build"].assignment
        self.assertEqual(architect.role, "support_architect")
        self.assertEqual(self.runs.assignments[architect.assignment_id]["tool"], "claude_code")
        self.architect_answers()
        self.assertEqual(self.support()["state"], "reviewing")
        self.tick()
        reviewer = self.runs.assignments[self.runs.runs[self.runs.last("support_reviewer")]["build"].assignment.assignment_id]
        self.assertNotEqual((reviewer["tool"], reviewer["model"]), ("claude_code", "arch-1"), "the reviewer cannot be the author's tool and model")
        self.assertEqual((reviewer["tool"], reviewer["model"]), ("codex", "rev-2"))
        self.reviewer_answers()
        self.assertEqual(self.support()["state"], "publishing")
        self.tick()
        self.assertEqual(self.support()["state"], "active")
        binding = self.service._support_binding("exec-1", "pb")
        role_bytes = self.dest.read_file("o/r", binding["commit_sha"], "app/billing/.maestro/role-billing-specialist.md")
        self.assertEqual(role_bytes, ROLE.encode())
        self.assertEqual(hashlib.sha256(role_bytes).hexdigest(), binding["role_sha256"])
        base = ".maestro/execution/exec-1/architectural-support/support-1/versions/1"
        for name in ("support.json", "review.json", "activation.json"):
            self.assertIsNotNone(self.dest.read_file("o/r", binding["commit_sha"], f"{base}/{name}"), name)
        activation = json.loads(self.dest.read_file("o/r", binding["commit_sha"], f"{base}/activation.json"))
        self.assertEqual(activation["bindings"][0]["packet_key"], "pb")
        self.assertEqual(json.loads(self.dest.read_file("o/r", binding["commit_sha"], f"{base}/review.json"))["outcome"], "APPROVE")
        self.assertNotIn("pb", self.service._held_packets("exec-1"))
        events = self.service._rows("SELECT kind, handled FROM service_execution_events WHERE kind = 'support_ready'")
        self.assertEqual([(e["kind"], e["handled"]) for e in events], [("support_ready", 0)], "the manager is notified through a saved event")
        journal = self.service._rows("SELECT kind, state FROM service_execution_journal WHERE kind = 'support_publish'")
        self.assertEqual([(j["kind"], j["state"]) for j in journal], [("support_publish", "verified")])
        # the coder and reviewer inputs carry the exact activated role and the binding, next to the unchanged confirmed reference
        inputs = self.service._role_inputs(self.row(), self.packet("pb"))
        self.assertEqual(inputs["specialist-role.md"], ROLE.encode())
        self.assertEqual(inputs["specialist-context.md"], CONTEXT.encode())
        self.assertIn("support-binding.json", inputs)
        self.assertEqual(self.packet("pb")["record_sha256"], "h", "the confirmed packet record is untouched")

    def test_an_existing_role_needs_validation_only_and_no_review(self) -> None:
        sh(self.work, "checkout", "-q", "-b", "roles")
        (self.work / "app" / "billing" / ".maestro").mkdir(parents=True)
        (self.work / "app" / "billing" / ".maestro" / "role-ledger.md").write_text(ROLE)
        (self.work / "app" / "billing" / ".maestro" / "context.md").write_text(CONTEXT)
        sh(self.work, "add", "-A")
        sh(self.work, "commit", "-q", "-m", "roles")
        commit = sh(self.work, "rev-parse", "HEAD")
        sh(self.work, "push", "-q", str(self.bare), f"{commit}:refs/heads/roles")
        path = "app/billing/.maestro/role-ledger.md"
        record = {"id": "other", "subject": "other", "permitted_paths": ["app/billing"], "starting_context": {"specialist_role_ref": {"path": path, "commit": commit, "sha256": hashlib.sha256(ROLE.encode()).hexdigest()}}}
        with self.database.transaction() as tx:
            tx.execute("INSERT INTO service_execution_packets(activity_id, packet_key, subject, record_json, record_sha256, milestone_key, dependency_keys_json, state, round_limit, updated_at) VALUES ('exec-1', 'other', 'other', ?, 'h', 'm1', '[]', 'pending', 2, 't')", (json.dumps(record),))
        self.request()
        self.tick()
        self.architect_answers(disposition="use_existing", existing_role_path=path, source_area=None, role_title=None, role_markdown=None, context_markdown=None)
        self.assertEqual(self.support()["state"], "publishing", "an unchanged role is validated, not reviewed")
        self.assertEqual(self.runs.run_count("exec-1-support-1-review-1"), 0)
        self.tick()
        self.assertEqual(self.support()["state"], "active")
        binding = self.service._support_binding("exec-1", "pb")
        self.assertEqual((binding["role_path"], binding["role_sha256"]), (path, hashlib.sha256(ROLE.encode()).hexdigest()))
        activation = json.loads(self.dest.read_file("o/r", binding["commit_sha"], ".maestro/execution/exec-1/architectural-support/support-1/versions/1/activation.json"))
        self.assertTrue(activation["validation"]["existing_role_unchanged"])
        self.assertIsNone(self.dest.read_file("o/r", binding["commit_sha"], ".maestro/execution/exec-1/architectural-support/support-1/versions/1/review.json"))

    def test_a_draft_that_leaves_the_packet_area_or_names_an_unknown_role_is_sent_back(self) -> None:
        self.request()
        self.tick()
        self.architect_answers(source_area="app/other")
        self.assertIn("permitted paths", self.runs.rejected[-1])
        self.assertEqual(self.support()["state"], "drafting")
        self.tick()  # the recovery run starts
        self.architect_answers(disposition="use_existing", existing_role_path="app/none/.maestro/role-x.md")
        self.assertIn("existing-roles", self.runs.rejected[-1])
        self.tick()
        self.architect_answers(role_markdown="no heading\n")
        self.assertIn("first heading", self.runs.rejected[-1])

    def test_a_repeated_failure_recovers_until_the_configured_allowance_is_used(self) -> None:
        self.request()
        self.tick()
        assignment = self.runs.runs[self.runs.last("support_architect")]["assignment"]
        for expected_runs in (2, 3):
            self.runs.runs[self.runs.last("support_architect")]["state"] = "failed"
            self.runs.assignments[assignment]["state"] = "needs_recovery"
            self.tick()
            self.assertEqual(self.runs.run_count(assignment), expected_runs)
            self.assertNotEqual(self.support()["state"], "blocked_route")
        self.runs.runs[self.runs.last("support_architect")]["state"] = "failed"
        self.runs.assignments[assignment]["state"] = "needs_recovery"
        self.tick()
        self.assertEqual(self.support()["state"], "blocked_route")
        self.assertIn("automatic recovery", self.support()["note"])

    def test_a_scope_change_is_reported_as_replanning_and_the_packet_stays_blocked(self) -> None:
        self.request()
        self.tick()
        self.architect_answers(disposition="replanning_required", rationale="covering billing changes the confirmed responsibilities", source_area=None, role_title=None, role_markdown=None, context_markdown=None)
        self.assertEqual(self.support()["state"], "replanning_required")
        self.assertIn("pb", self.service._held_packets("exec-1"))
        self.assertIsNone(self.service._support_binding("exec-1", "pb"))
        self.assertEqual(self.runs.run_count("exec-1-support-1-review-1"), 0)

    def test_a_published_path_holding_different_content_pauses_without_overwrite(self) -> None:
        self.request()
        self.tick()
        self.architect_answers()
        self.reviewer_answers()
        clone = self.root / "squat"
        subprocess.run(["git", "clone", "-q", str(self.bare), str(clone)], check=True, env=ENV)
        (clone / "app" / "billing" / ".maestro").mkdir(parents=True)
        (clone / "app" / "billing" / ".maestro" / "context.md").write_text("someone else's context\n")
        sh(clone, "add", "-A")
        sh(clone, "commit", "-q", "-m", "squat")
        sh(clone, "push", "-q", str(self.bare), "HEAD:refs/heads/main")
        self.tick()
        self.assertEqual(self.support()["state"], "blocked_route")
        self.assertIsNone(self.service._support_binding("exec-1", "pb"))
        self.assertEqual(self.dest.read_file("o/r", "main", "app/billing/.maestro/context.md"), b"someone else's context\n")
        self.assertEqual([j["state"] for j in self.service._rows("SELECT state FROM service_execution_journal WHERE kind = 'support_publish'")], ["failed"])


class SupportLimitTests(SupportBase):
    def draft_and_review(self, outcome, blocking):
        self.request() if not self.service._architects("exec-1", "support") else None
        self.tick()
        self.architect_answers()
        self.reviewer_answers(outcome, blocking)

    def test_review_rounds_correct_then_reach_a_limit_with_a_saved_recommendation_and_one_owner_grant(self) -> None:
        self.draft_and_review("REQUEST_CHANGES", 1)
        self.assertEqual((self.support()["state"], self.support()["version"]), ("correcting", 2))
        self.tick()
        self.architect_answers(role_markdown=ROLE + "\nAmended.\n")
        self.reviewer_answers("REQUEST_CHANGES", 1)
        self.assertEqual(self.support()["state"], "recommending")
        self.assertEqual(self.support()["reviews_used"], 2)
        # a decision cannot be made before the recommendation is saved
        self.tick()
        run_id = self.runs.last("support_limit_architect")
        self.runs.finish(run_id, {"result": "completed", "support_id": "support-1", "support_version": 2, "completed_reviews": 2, "recommendation": "grant_one", "rationale": "one fix left", "summary": "s", "questions": []})
        self.tick()
        self.assertEqual(self.support()["state"], "limit_paused")
        view = self.service.view("exec-1")
        decision = view["owner_decisions"][0]
        self.assertEqual((decision["target"], decision["recommendation"], decision["assignment_id"]), ("execution_support_fidelity_review", "grant_one", "support-1"))
        self.assertIn("pb", self.service._held_packets("exec-1"))
        self.assertEqual(view["support"][0]["reviews"], {"completed": 2, "limit": 2})
        self.grant("grant_one")
        self.assertEqual((self.support()["state"], self.support()["version"]), ("correcting", 3))
        self.assertEqual(self.service.support_view("exec-1")[0]["reviews"]["limit"], 3, "the grant adds one allowance to this support only; the base limit stays 2")
        with self.assertRaises(Exception):
            self.grant("grant_one")  # replay by a new request cannot grant twice
        self.tick()
        self.architect_answers(role_markdown=ROLE + "\nAmended twice.\n")
        self.reviewer_answers("APPROVE")
        self.tick()
        self.assertEqual(self.support()["state"], "active")

    def grant(self, choice, request_id=None):
        from types import SimpleNamespace

        request = SimpleNamespace(request_id=request_id or f"req-{choice}-{self.support()['version']}", project_id="proj", activity_id="exec-1", expected_version=int(self.service._read("SELECT version FROM entity_versions WHERE entity_id = 'exec-1'")["version"]), payload={"target": "execution_support_fidelity_review", "choice": choice, "assignment_id": "support-1"}, question_id=None)
        prepared = self.service.prepare_owner_decision(request)
        with self.database.transaction() as tx:
            return prepared.apply(tx, int(self.service._read("SELECT version FROM entity_versions WHERE entity_id = 'exec-1'")["version"]) + 1)

    def test_remain_paused_keeps_the_blocker_and_changes_no_count(self) -> None:
        self.draft_and_review("REQUEST_CHANGES", 1)
        self.tick()
        self.architect_answers()
        self.reviewer_answers("REQUEST_CHANGES", 1)
        self.tick()
        self.runs.finish(self.runs.last("support_limit_architect"), {"result": "completed", "support_id": "support-1", "support_version": 2, "completed_reviews": 2, "recommendation": "remain_paused", "rationale": "not achievable", "summary": "s", "questions": []})
        self.tick()
        self.grant("remain_paused")
        self.assertEqual((self.support()["state"], self.support()["reviews_used"]), ("limit_paused", 2))

    def test_a_stale_recommendation_is_rejected_and_a_missing_one_blocks_the_decision(self) -> None:
        self.draft_and_review("REQUEST_CHANGES", 1)
        self.tick()
        self.architect_answers()
        self.reviewer_answers("REQUEST_CHANGES", 1)
        self.tick()
        self.runs.finish(self.runs.last("support_limit_architect"), {"result": "completed", "support_id": "support-1", "support_version": 1, "completed_reviews": 2, "recommendation": "grant_one", "rationale": "r", "summary": "s", "questions": []})
        self.tick()
        self.assertTrue(any("exactly" in r for r in self.runs.rejected), "a recommendation naming another version is refused")
        self.assertEqual(self.support()["state"], "recommending")
        with self.assertRaises(Exception):
            self.grant("grant_one")


class SupportRouteTests(SupportBase):
    def test_an_unavailable_primary_uses_the_configured_backup_and_records_why(self) -> None:
        def resolver(role, tool, model):
            if (tool, model) == ("claude_code", "arch-1"):
                raise RuntimeError("rate limited")
        self.runs.route_resolver = resolver
        self.request()
        self.tick()
        assignment = self.runs.assignments[self.runs.runs[self.runs.last("support_architect")]["build"].assignment.assignment_id]
        self.assertEqual((assignment["tool"], assignment["model"]), ("codex", "arch-2"))
        history = json.loads(self.support()["pending_json"])["route_history"]
        self.assertIn("rate limited", history[0]["reason"])
        self.assertEqual(history[0]["switched_to"], "codex arch-2")

    def test_no_usable_route_pauses_the_affected_packet_and_unrelated_work_is_unaffected(self) -> None:
        self.runs.route_resolver = lambda role, tool, model: (_ for _ in ()).throw(RuntimeError("down"))
        self.add_packet("other", "m1", self.base, state="pending", paths=("app/other",))
        self.request()
        self.tick()
        self.assertEqual(self.support()["state"], "blocked_route")
        self.assertIn("neither the primary nor the backup", self.support()["note"])
        held = self.service._held_packets("exec-1")
        self.assertIn("pb", held)
        self.assertNotIn("other", held)

    def test_without_configuration_the_request_is_saved_blocked_with_a_plain_reason(self) -> None:
        self.configure(None)
        self.request()
        self.assertEqual(self.support()["state"], "blocked_route")
        self.assertIn("not configured", self.support()["note"])

    def test_the_configuration_comes_from_the_start_snapshot_not_later_edits(self) -> None:
        self.request()
        self.assertEqual(json.loads(self.support()["config_json"])["architect"]["primary"]["model"], "arch-1")
        self.configure({**SUPPORT, "architect": {**SUPPORT["architect"], "primary": {"tool": "codex", "model": "later"}}})
        self.assertEqual(json.loads(self.support()["config_json"])["architect"]["primary"]["model"], "arch-1")

    def test_a_reviewer_whose_only_routes_match_the_author_cannot_review(self) -> None:
        self.configure({**SUPPORT, "fidelity_reviewer": {"primary": {"tool": "claude_code", "model": "arch-1"}, "backup": {"tool": "claude_code", "model": "arch-1x"}, "run_timeout_seconds": 60}})
        self.runs.route_resolver = lambda role, tool, model: (_ for _ in ()).throw(RuntimeError("x")) if (tool, model) == ("claude_code", "arch-1x") else None
        self.request()
        self.tick()
        self.architect_answers()
        self.tick()
        self.assertEqual(self.support()["state"], "blocked_route")
        self.assertIn("cannot review", self.support()["note"])


class ConfigTests(unittest.TestCase):
    def test_support_configuration_needs_distinct_primary_and_backup_and_positive_values(self) -> None:
        good = execution_config.validate(config_table(architectural_support=SUPPORT))
        self.assertEqual(good["architectural_support"]["maximum_fidelity_reviews"], 2)
        same = {**SUPPORT, "architect": {**SUPPORT["architect"], "backup": SUPPORT["architect"]["primary"]}}
        with self.assertRaises(execution_config.ExecutionConfigError):
            execution_config.validate(config_table(architectural_support=same))
        with self.assertRaises(execution_config.ExecutionConfigError):
            execution_config.validate(config_table(architectural_support={**SUPPORT, "maximum_fidelity_reviews": 0}))
        self.assertNotIn("architectural_support", execution_config.validate(config_table()))


if __name__ == "__main__":
    unittest.main()
