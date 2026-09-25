"""Execution milestone gaps and correction supplements, with a real local Git remote and scripted agents.
Real agents and the installed path are proven in var/qa/architecture-gaps-live."""
from __future__ import annotations

import hashlib
import json
import unittest
from types import SimpleNamespace

from maestro.service.registry import OperationResult

from test_execution_determination import DeterminationBase, determination

FINDING = {"milestone_key": "m1", "source": "outcome_review", "subject": "Refunds are never applied", "explanation": "The milestone promises refunds but no path applies one.",
           "impact": "Billing totals are wrong", "requested_correction": "Add refund handling to billing", "evidence": ["app/billing has no refund function"], "review_limit_exhausted": False}


def supplement(**over):
    body = {"scope_explanation": "refunds are inside the confirmed billing scope", "packets": [
        {"key": "fix-refunds", "subject": "Apply refunds", "purpose": "Add the missing refund handling", "permitted_paths": ["app/billing"], "dependencies": [],
         "completion_criteria": ["a refund lowers the invoice total"], "essential_failure_checks": ["a refund above the total is refused"]}]}
    body.update(over)
    return body


class GapBase(DeterminationBase):
    def record(self, **over):
        payload = {**FINDING, **over}
        request = SimpleNamespace(request_id=f"req-{abs(hash(json.dumps(payload, sort_keys=True))) % 10**8}", project_id="proj", activity_id="exec-1", question_id=None, expected_version=None, payload=payload)
        prepared = self.service.prepare_record_finding(request)
        with self.database.transaction() as tx:
            return prepared.apply(tx, 2)

    def gap(self, n=1):
        return self.service._architect("exec-1", f"gap-finding-{n}")

    def answer_gap(self, body):
        self.runs.finish(self.runs.last("milestone_gap_architect"), body)
        self.tick()


class FindingTests(GapBase):
    def test_a_finding_starts_one_read_only_assignment_and_a_repeat_returns_the_saved_finding(self) -> None:
        first = self.record()
        self.assertEqual((first.data["finding_id"], first.data["duplicate"]), ("finding-1", False))
        again = self.record()
        self.assertEqual((again.data["finding_id"], again.data["duplicate"]), ("finding-1", True))
        self.assertEqual(len(self.service._architects("exec-1", "milestone_gap")), 1)
        self.tick()
        build = self.runs.runs[self.runs.last("milestone_gap_architect")]["build"]
        self.assertEqual((build.assignment.role, build.assignment.permitted_actions), ("milestone_gap_architect", ("read_source",)))
        self.assertIn("finding.json", build.inputs)
        self.assertEqual(json.loads(build.inputs["finding.json"])["subject"], "Refunds are never applied")
        self.assertEqual(self.gap()["state"], "determining")

    def test_a_finding_for_an_unknown_milestone_or_with_missing_evidence_is_refused(self) -> None:
        with self.assertRaises(Exception) as caught:
            self.record(milestone_key="nope")
        self.assertIn("no such milestone", str(caught.exception))
        with self.assertRaises(ValueError):
            self.record(evidence=[])
        with self.assertRaises(ValueError):
            self.record(source="a friend")


class SupplementTests(GapBase):
    def gap_to_publishing(self, **over):
        self.record()
        self.tick()
        self.answer_gap(determination("in_scope_supplement", affected_work=["m1"], supplement=supplement(**over)))

    def test_a_valid_supplement_is_published_with_verified_bytes_and_activated_into_pending_packets(self) -> None:
        self.gap_to_publishing()
        self.assertEqual(self.gap()["state"], "publishing")
        self.assertEqual(self.service._packets("exec-1").__len__(), 3, "nothing is released before publication is verified")
        self.tick()
        self.assertEqual(self.gap()["state"], "active")
        stored = self.service._read("SELECT * FROM service_execution_supplements WHERE supplement_id = 'supplement-1'")
        self.assertEqual((stored["version"], stored["state"]), (1, "active"))
        data = self.dest.read_file("o/r", stored["commit_sha"], stored["path"])
        self.assertEqual(stored["path"], ".maestro/execution/exec-1/supplements/supplement-1/versions/1/supplement.json")
        self.assertEqual(hashlib.sha256(data).hexdigest(), stored["record_sha256"], "the hash is stored outside the file and matches the remote bytes")
        record = json.loads(data)
        self.assertEqual((record["schema_version"], record["finding"]["finding_id"], record["milestone_key"]), (1, "finding-1", "m1"))
        self.assertNotIn("record_sha256", record)
        packet = self.packet("fix-refunds")
        self.assertEqual((packet["state"], packet["milestone_key"]), ("pending", "m1"))
        self.assertEqual(json.loads(packet["record_json"])["supplement_ref"]["sha256"], stored["record_sha256"])
        self.assertEqual(self.service._read("SELECT state FROM service_execution_findings WHERE finding_id = 'finding-1'")["state"], "supplement_active")
        self.assertEqual([e["kind"] for e in self.service._rows("SELECT kind FROM service_execution_events WHERE kind = 'supplement_active'")], ["supplement_active"])
        self.assertEqual([j["state"] for j in self.service._rows("SELECT state FROM service_execution_journal WHERE kind = 'supplement_publish'")], ["verified"])
        # a repeat step neither duplicates the packets nor rewrites the record
        self.tick()
        self.assertEqual(len(self.service._packets("exec-1")), 4)
        self.assertEqual(self.packet("pb")["record_sha256"], "h", "confirmed packets are untouched")
        view = self.service.view("exec-1")
        self.assertEqual(view["gaps"][0]["supplements"][0]["packets"], ["fix-refunds"])
        self.assertNotIn("fix-refunds", self.service._held_packets("exec-1"))

    def test_invalid_supplements_are_sent_back_with_the_exact_problem(self) -> None:
        cases = (
            (dict(packets=[{**supplement()["packets"][0], "permitted_paths": ["app/other"]}]), "outside the paths"),
            (dict(packets=[{**supplement()["packets"][0], "permitted_paths": ["/etc"]}]), "bounded"),
            (dict(packets=[{**supplement()["packets"][0], "permitted_paths": ["app/billing/../x"]}]), "bounded"),
            (dict(packets=[{**supplement()["packets"][0], "key": "pb"}]), "collides"),
            (dict(packets=[{**supplement()["packets"][0], "dependencies": ["ghost"]}]), "neither an existing packet"),
            (dict(packets=[{**supplement()["packets"][0], "key": "a", "dependencies": ["b"]}, {**supplement()["packets"][0], "key": "b", "dependencies": ["a"]}]), "cycle"),
            (dict(packets=[supplement()["packets"][0], supplement()["packets"][0]]), "repeated"),
            (dict(scope_explanation=" "), "scope_explanation"),
        )
        self.record()
        self.tick()
        for change, text in cases:
            self.answer_gap(determination("in_scope_supplement", affected_work=["m1"], supplement=supplement(**change)))
            self.assertIn(text, self.runs.rejected[-1])
            self.assertEqual(self.gap()["state"], "determining")
            self.assertEqual(len(self.service._packets("exec-1")), 3)
            self.tick()  # the recovery run starts
            self.service._save_architect("exec-1", "gap-finding-1", {**json.loads(self.gap()["pending_json"]), "last_recovery_detail": None})

    def test_conflicting_remote_content_pauses_without_overwrite_and_creates_no_packets(self) -> None:
        self.gap_to_publishing()
        path = ".maestro/execution/exec-1/supplements/supplement-1/versions/1/supplement.json"
        self.dest.publish("o/r", "main", {path: b"someone else's bytes\n"}, "squat")
        self.tick()
        self.assertEqual(self.gap()["state"], "blocked_route")
        self.assertEqual(self.dest.read_file("o/r", "main", path), b"someone else's bytes\n")
        self.assertIsNone(self.packet("fix-refunds"))
        self.assertEqual([j["state"] for j in self.service._rows("SELECT state FROM service_execution_journal WHERE kind = 'supplement_publish'")], ["failed"])

    def test_a_stale_finding_pauses_activation(self) -> None:
        self.gap_to_publishing()
        with self.database.transaction() as tx:
            tx.execute("UPDATE service_execution_findings SET state = 'closed' WHERE finding_id = 'finding-1'")
        self.tick()
        self.assertEqual(self.gap()["state"], "blocked_route")
        self.assertIn("stale", self.gap()["note"])
        self.assertIsNone(self.packet("fix-refunds"))


class RoutingTests(GapBase):
    def test_an_implementation_defect_is_saved_and_routed_to_integration_without_a_supplement(self) -> None:
        self.record()
        self.tick()
        self.answer_gap(determination("implementation_defect", affected_work=["m1"]))
        self.assertEqual(self.gap()["state"], "decided")
        self.assertEqual(self.service._read("SELECT state FROM service_execution_findings WHERE finding_id = 'finding-1'")["state"], "defect_routed")
        self.assertEqual([e["kind"] for e in self.service._rows("SELECT kind FROM service_execution_events WHERE kind = 'gap_defect'")], ["gap_defect"])
        self.assertEqual(len(self.service._rows("SELECT 1 FROM service_execution_supplements")), 0)

    def test_a_scope_change_goes_to_the_owner_disposition_and_starts_nothing(self) -> None:
        self.record()
        self.tick()
        self.answer_gap(determination("reregistration_required", affected_work=["pb"]))
        self.assertEqual(self.gap()["state"], "awaiting_disposition")
        self.assertIn("pb", self.service._held_packets("exec-1"))
        view = self.service.view("exec-1")
        decision = next(d for d in view["owner_decisions"] if d["target"] == "execution_work_disposition")
        self.assertEqual(decision["assignment_id"], "gap-finding-1")
        self.decide("execution_work_disposition", "continue_unaffected", "gap-finding-1")
        self.assertEqual(sorted(self.service._held_packets("exec-1")), ["dep", "pb"])
        self.assertIn(self.row()["state"], ("running", "blocked"), "choosing a disposition does not end the Execution")

    def test_an_exhausted_milestone_allowance_needs_the_recommendation_and_a_supplement_needs_none_otherwise(self) -> None:
        self.record(review_limit_exhausted=True)
        self.tick()
        self.answer_gap(determination("implementation_defect", affected_work=["m1"]))
        self.assertIn("exhausted", self.runs.rejected[-1])
        self.tick()
        self.answer_gap(determination("implementation_defect", affected_work=["m1"], owner_recommendation="remain_paused"))
        self.assertEqual(self.service.view("exec-1")["gaps"][0]["recommendation"], "remain_paused")


if __name__ == "__main__":
    unittest.main()
