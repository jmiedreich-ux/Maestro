"""Architecture review, amendment and confirmation stage against scripted destination and runs.

The scripted destination and runs stand in for network and agent tools only so the step machine's own
decisions can be exercised quickly and repeatably; real agents, real GitHub and the installed service are
proven separately (var/qa/architecture-live).
"""
from __future__ import annotations

import json
import unittest
from types import SimpleNamespace

from maestro.service.architecture import shared_owner_decision
from maestro.service.requests import RequestRejection

from tests.maestro.service import test_architecture as base
from tests.maestro.service import test_architecture_breakdown as bdt
from tests.maestro.service.test_registration import COMMIT

BASE = ".maestro/architecture/versions"


def review_finding(key, severity, packet="packet-1"):
    return {"local_key": key, "subject": f"Finding {key}", "severity": severity, "explanation": "Because", "impact": "It matters", "requested_correction": "Fix it",
            "source_refs": [{"path": f"{BASE}/2/work-packets/{packet}.json", "commit": COMMIT, "locator": "purpose"}], "missing_information": None,
            "affected_items": [{"id": packet, "subject": "Packet a", "version": 1, "path": f"work-packets/{packet}.json"}]}


def review(outcome, findings=(), **over):
    def build(a):
        value = {"contract_version": 1, "assignment_id": a.assignment_id, "run_id": a.run_id, "session_id": a.instructions["session_id"], "project_id": a.project_id,
                 "activity_id": a.activity_id, "role": "fidelity_reviewer", "source_commit": a.source_commit, "decision_version": a.decision_version, "input_manifest": None,
                 "result": "completed", "summary": "Reviewed.", "findings": list(findings), "questions": [], "outputs": [], "reviewed_set": None, "review_outcome": outcome,
                 "failure": None, "allocations": []}
        value.update(over)
        return value
    return {"kind": "completed", "response": build, "output_files": {}}


class ReviewRuns(base.ArchitectureRuns):
    def response(self, run_id):
        value = super().response(run_id)
        spec = self.state[run_id]["spec"]
        if value.get("role") == "fidelity_reviewer" and "reviewed_set" in value and value["reviewed_set"] is None:
            ref = json.loads(spec.inputs["reviewed-set.json"])
            value["reviewed_set"] = {"manifest_sha256": ref["manifest_sha256"], "reviewed_content_hash": ref["reviewed_content_hash"]}
        return value


class ReviewTests(unittest.TestCase):
    """A saved breakdown is reviewed by a separate reviewer, amended in the same session, and confirmed at its exact version."""

    def setUp(self) -> None:
        bdt.StageTests.setUp(self)
        self.runs.__class__ = ReviewRuns
        self.requests = self._requests()

    def _requests(self):
        from maestro.service.authentication import OwnerAuthenticationSettings, OwnerAuthenticator, token_digest
        from maestro.service.registry import OperationRegistry
        from maestro.service.requests import RequestService
        from tests.maestro.service import test_registration as reg
        authenticator = OwnerAuthenticator(OwnerAuthenticationSettings("owner", token_digest(reg.TOKEN)))
        handlers = [h for h in self.service.operation_handlers if h.operation != "owner.decision"]
        return RequestService(self.database, authenticator, OperationRegistry(
            self.questions.operation_handlers + tuple(handlers) + self.architecture.operation_handlers + (shared_owner_decision(self.service, self.architecture),)))

    tearDown = base.ArchitectureTests.tearDown
    submit = base.ArchitectureTests.submit
    start = base.ArchitectureTests.start
    open_questions = base.ArchitectureTests.open_questions
    row = base.ArchitectureTests.row
    answer = base.ArchitectureTests.answer
    run_until = base.ArchitectureTests.run_until
    drive_to_ready = base.ArchitectureTests.drive_to_ready
    version = base.ArchitectureTests.version
    registered = base.ArchitectureTests.registered
    milestone_ids = base.ArchitectureTests.milestone_ids
    start_architecture = base.ArchitectureTests.start_architecture
    row_a = base.ArchitectureTests.row_a
    save_history = base.ArchitectureTests.save_history

    def reviewer_runs(self, activity):
        return [s for s in self.runs.started if s[3].assignment.role == "fidelity_reviewer" and s[3].assignment.activity_id == activity]

    def drive(self, activity, state, limit=40):
        for _ in range(limit):
            self.architecture.tick()
            self.save_history(activity)
            if self.row_a(activity)["state"] == state:
                return
        self.fail(f"architecture stayed {self.row_a(activity)['state']} ({self.row_a(activity)['note']}), wanted {state}")

    def breakdown_response(self, milestones, **change):
        document = bdt.breakdown(milestones)
        document["packets"][1]["permitted_paths"] = ["src/b", *change.get("extra_paths", [])]
        return base.architect_response({"breakdown.json": json.dumps(document)}, findings=[])

    def reach(self, review_script):
        """Foundations and a first breakdown are saved; the scripted reviewer outcomes follow."""
        project_id, package = self.registered()
        self.package = package
        outcomes, milestones = self.milestone_ids(package)
        self.milestones = milestones
        self.runs.script = [base.architect_response(base.files_for(milestones)), self.breakdown_response(milestones), *review_script]
        activity = self.start_architecture(project_id, package).activity_id
        return project_id, activity

    def working(self, project_id):
        return self.architecture.project_view(project_id)["working_ref"]

    def confirm(self, project_id, activity, expected=None, limitations=(), request_id=None):
        view = self.architecture.project_view(project_id)
        return self.submit("architecture.confirm", project_id, activity, None, view["activity_version"],
                           {"expected_working_ref": expected or view["working_ref"], "accepted_limitations": list(limitations)})

    def test_a_passing_review_is_published_and_the_exact_version_is_confirmed(self) -> None:
        note = review_finding("n1", "non_blocking")
        project_id, activity = self.reach([review("APPROVE", [note])])
        self.drive(activity, "ready")
        view = self.architecture.project_view(project_id)
        self.assertEqual("waiting_for_confirmation", view["state"])
        self.assertEqual(["confirm", "cancel"], view["available_actions"])
        self.assertTrue(view["review_coverage_valid"])
        self.assertEqual((1, 2), (view["review_count"], view["review_limit"]))
        # a separate reviewer role received the exact published set, the confirmed outcomes and nothing to write
        stage = self.reviewer_runs(activity)
        self.assertEqual(1, len(stage))
        spec = stage[0][3]
        self.assertEqual("architecture", spec.assignment.contract)
        self.assertNotEqual(self.runs.state[stage[0][0]]["tool"], self.row_a(activity)["architect_tool"])
        listed = json.loads(spec.inputs["reviewed/index.json"])["records"]
        self.assertIn("packet-1", {r["id"] for r in listed})
        self.assertIn("investigation", {r["id"] for r in listed})
        self.assertIn("outcomes.json", spec.inputs)
        # the review record and the manifest are added to the published version; content is unchanged
        published = self.destination.published[-2]
        record = json.loads(published[f"{BASE}/2/reviews/review-1.json"])
        manifest = json.loads(published[f"{BASE}/2/manifest.json"])
        self.assertEqual(("APPROVE", "reviewed"), (record["outcome"], manifest["stage"]))
        self.assertEqual(view["working_ref"]["reviewed_content_hash"], record["reviewed_set"]["reviewed_content_hash"])
        self.assertIn("review-1", {e["id"] for e in manifest["inventory"]})
        self.assertEqual(1, len(record["findings"]))
        # the working reference moved to the review commit; a confirmation that names the older reference is refused and shows the current one
        stale = {**view["working_ref"], "manifest_sha256": "0" * 64}
        with self.assertRaises(RequestRejection) as caught:
            self.confirm(project_id, activity, expected=stale)
        self.assertEqual("working_ref_changed", caught.exception.code)
        self.assertEqual(view["working_ref"], caught.exception.fields["working_ref"])
        with self.assertRaises(RequestRejection) as caught:
            self.confirm(project_id, activity, limitations=[{"id": "finding-99", "subject": "x", "version": 1, "container": record}])
        self.assertEqual("unknown_limitation", caught.exception.code)
        receipt = self.confirm(project_id, activity, limitations=view["limitations"] and [{k: v for k, v in view["limitations"][0].items() if k != "explanation"}])
        self.assertEqual("accepted", receipt.status)
        self.assertEqual("confirming", self.row_a(activity)["state"])
        with self.assertRaises(RequestRejection) as caught:
            self.submit("architecture.cancel", project_id, activity, None, self.architecture.project_view(project_id)["activity_version"], {"reason": "changed my mind"})
        self.assertEqual("confirmation_pending", caught.exception.code)
        self.drive(activity, "completed")
        done = self.architecture.project_view(project_id)
        self.assertEqual(done["working_ref"], done["confirmed_ref"])
        self.assertEqual(2, done["confirmed_ref"]["version"])
        receipt_files = self.destination.published[-2]
        confirmation = json.loads(receipt_files[f"{BASE}/2/confirmation.json"])
        self.assertEqual(view["working_ref"], confirmation["expected_working_ref"])
        self.assertEqual("owner", confirmation["owner_id"])
        self.assertEqual(["review-1"], [r["id"] for r in confirmation["review_refs"]])
        self.assertEqual("confirmed", json.loads(receipt_files[f"{BASE}/2/manifest.json"])["stage"])
        index = json.loads(self.destination.published[-1][".maestro/architecture/index.json"])
        self.assertEqual(done["confirmed_ref"], {k: index["confirmed_ref"][k] for k in done["confirmed_ref"]})
        # completion starts nothing and releases the project
        self.assertEqual(1, len(self.reviewer_runs(activity)))
        self.assertIsNone(self.architecture._read("SELECT 1 AS n FROM service_project_reservations WHERE project_id = ?", (project_id,)))
        with self.assertRaises(RequestRejection):
            self.confirm(project_id, activity)
        # the completed breakdown answers another start for the same registration, but does not block a start after a later registration
        again = self.start_architecture(project_id, self.package)
        self.assertEqual((activity, True), (again.activity_id, again.result["duplicate"]))
        with self.database.transaction() as tx:
            tx.execute("UPDATE service_architectures SET registration_activity_id = 'an-earlier-registration' WHERE activity_id = ?", (activity,))
        fresh = self.start_architecture(project_id, self.package)
        self.assertNotEqual(activity, fresh.activity_id)
        self.assertFalse(fresh.result["duplicate"])

    def test_requested_changes_are_amended_in_the_same_session_and_reviewed_again(self) -> None:
        blocking = review_finding("b1", "blocking", "packet-2")
        project_id, activity = self.reach([review("REQUEST_CHANGES", [blocking])])
        # the amendment changes only packet b
        self.runs.script.extend([self.breakdown_response(self.milestones, extra_paths=["src/b/extra"]), review("APPROVE")])
        self.drive(activity, "ready")
        view = self.architecture.project_view(project_id)
        self.assertEqual((2, True), (view["review_count"], view["review_coverage_valid"]))
        self.assertEqual(["REQUEST_CHANGES", "APPROVE"], [r["outcome"] for r in view["reviews"]])
        architect_runs = [s for s in self.runs.started if s[3].assignment.instructions.get("task_kind") == "break_down"]
        self.assertEqual(2, len(architect_runs))
        self.assertEqual(architect_runs[0][3].assignment.instructions["session_id"], architect_runs[1][3].assignment.instructions["session_id"])
        self.assertIn("amendment pass", architect_runs[1][3].assignment.task)
        findings = json.loads(architect_runs[1][3].inputs["review-findings.json"])["findings"]
        self.assertEqual("Finding b1", findings[0]["subject"])
        self.assertIn("current-breakdown.json", architect_runs[1][3].inputs)
        # only the changed packet, its milestone and plan are rewritten; the untouched packet is carried forward
        second = [p for p in self.destination.published if f"{BASE}/3/manifest.json" in p][0]
        manifest = json.loads(second[f"{BASE}/3/manifest.json"])
        self.assertIn("investigation", {c["record_ref"]["id"] for c in manifest["carried_forward"]})
        self.assertEqual(2, {e["id"]: e["version"] for e in manifest["inventory"]}["packet-2"])
        # the follow-up review is told what changed and what it found before
        follow = self.reviewer_runs(activity)[1][3]
        self.assertIn("prior-findings.json", follow.inputs)
        self.assertIn("packet-2", {r["id"] for r in json.loads(follow.inputs["amendment.json"])["rewritten"]})
        # both reviews stay in the published history; coverage belongs to the amended version
        self.assertEqual(3, view["working_ref"]["version"])
        first = json.loads([p for p in self.destination.published if f"{BASE}/2/reviews/review-1.json" in p][0][f"{BASE}/2/reviews/review-1.json"])
        self.assertEqual("REQUEST_CHANGES", first["outcome"])

    def test_the_review_limit_goes_to_the_owner_and_one_extra_attempt_cannot_force_approval(self) -> None:
        project_id, activity = self.reach([review("REQUEST_CHANGES", [review_finding("b1", "blocking")])])
        self.runs.script.extend([self.breakdown_response(self.milestones, extra_paths=["src/b/x"]), review("REQUEST_CHANGES", [review_finding("b1", "blocking")])])
        self.drive(activity, "limit_paused")
        view = self.architecture.project_view(project_id)
        self.assertEqual((2, 2), (view["review_count"], view["review_limit"]))
        self.assertEqual(["respond_to_owner_decision", "cancel"], view["available_actions"])
        self.assertFalse(view["review_coverage_valid"])
        decision = view["owner_decisions"][0]
        self.assertEqual("fidelity_review", decision["target"])
        payload = {"target": "fidelity_review", "choice": "grant_one", "assignment_id": decision["assignment_id"]}
        with self.assertRaises(RequestRejection) as caught:
            self.submit("owner.decision", project_id, activity, None, view["activity_version"], {**payload, "assignment_id": "someone-else"})
        self.assertEqual("stale_decision", caught.exception.code)
        with self.assertRaises(RequestRejection):
            self.confirm(project_id, activity)
        self.submit("owner.decision", project_id, activity, None, view["activity_version"], {**payload, "choice": "remain_paused"})
        again = self.architecture.project_view(project_id)
        self.assertEqual("limit_paused", self.row_a(activity)["state"])
        self.assertEqual(2, again["review_count"])
        self.submit("owner.decision", project_id, activity, None, again["activity_version"], payload)
        granted = self.architecture.project_view(project_id)
        self.assertEqual((3, 2, 1), (granted["review_limit"], granted["allowances"][0]["base_limit"], granted["allowances"][0]["granted"]))
        with self.assertRaises(RequestRejection):
            self.submit("owner.decision", project_id, activity, None, granted["activity_version"], payload)
        self.runs.script.extend([self.breakdown_response(self.milestones, extra_paths=["src/b/y"]), review("REQUEST_CHANGES", [review_finding("b1", "blocking")])])
        self.drive(activity, "limit_paused")
        final = self.architecture.project_view(project_id)
        self.assertEqual((3, 3), (final["review_count"], final["review_limit"]))
        self.assertEqual(3, len(self.reviewer_runs(activity)))

    def test_a_review_that_names_a_different_set_is_rejected_and_not_counted(self) -> None:
        wrong = review("APPROVE", reviewed_set={"manifest_sha256": "1" * 64, "reviewed_content_hash": "2" * 64})
        project_id, activity = self.reach([wrong, review("APPROVE")])
        self.drive(activity, "ready")
        view = self.architecture.project_view(project_id)
        self.assertEqual((1, True), (view["review_count"], view["review_coverage_valid"]))
        runs = self.reviewer_runs(activity)
        self.assertEqual(["initial", "recovery"], [s[2] for s in runs])
        self.assertEqual(runs[0][0], runs[1][0])

    def test_confirmation_needs_a_review_of_the_exact_version(self) -> None:
        project_id, activity = self.reach([review("REQUEST_CHANGES", [review_finding("b1", "blocking")])])
        for _ in range(12):
            self.architecture.tick()
            self.save_history(activity)
            if json.loads(self.row_a(activity)["pending_json"]).get("amend"):
                break
        with self.assertRaises(RequestRejection) as caught:
            self.confirm(project_id, activity)
        self.assertEqual("not_ready_for_confirmation", caught.exception.code)
        self.assertEqual("running", self.architecture.project_view(project_id)["state"])


if __name__ == "__main__":
    unittest.main()
