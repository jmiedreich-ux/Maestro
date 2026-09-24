"""Architecture confirmation and review-limit actions submit exactly the Owner's explicit requests."""
from __future__ import annotations

import unittest
from types import SimpleNamespace

from maestro.terminal.architecture import ArchitectureError, ArchitectureExtension
from maestro.terminal.connection import ConnectionUnavailable, ServiceError
from maestro.terminal.extensions import ExtensionContext

REF = {"version": 2, "commit": "c" * 40, "manifest_path": ".maestro/architecture/versions/2/manifest.json", "manifest_sha256": "d" * 64, "reviewed_content_hash": "e" * 64}
LIMITATION = {"id": "finding-9", "subject": "Slow search", "version": 1, "container": {"id": "review-1", "subject": "Independent review 1", "version": 1, "path": "p", "sha256": "f" * 64, "commit": "c" * 40},
              "explanation": "Search scans every note"}
VIEW = {"state": "waiting_for_confirmation", "activity_version": 7, "repository": "o/r", "publication_branch": "maestro", "working_ref": REF, "review_count": 1, "review_limit": 2,
        "review_coverage_valid": True, "limitations": [LIMITATION], "coverage": {"o1": ["milestone-1"]}, "owner_decisions": [], "reviews": [], "records": [],
        "breakdown": {"milestones": [{"id": "milestone-1"}], "packets": [{"id": "packet-1", "depends_on": [], "parallel_with": []}, {"id": "packet-2", "depends_on": ["packet-1"], "parallel_with": []}]}}


class Client:
    def __init__(self) -> None:
        self.sent, self.fail, self.view = [], None, dict(VIEW)

    def submit(self, envelope):
        self.sent.append(envelope)
        if self.fail:
            raise self.fail
        return {"receipt": {"status": "accepted", "project_id": "p", "activity_id": "a", "result": {}}}

    def get_json(self, path, *, timeout=15):
        return {"data": self.view}


class ArchitectureTerminalTests(unittest.TestCase):
    def setUp(self) -> None:
        self.extension = ArchitectureExtension(lambda: "req-fixed")
        self.client = Client()
        self.state = SimpleNamespace(selected_project_id="p", selected_activity_id="a", error=None, activities=(), activity_detail={"available_actions": []})
        self.context = ExtensionContext(self.client, self.state)

    def test_confirming_shows_the_exact_version_first_and_sends_only_that_version(self) -> None:
        self.extension.action(self.context, "a-confirm")
        self.assertEqual([], self.client.sent)
        self.assertIn("version 2", self.state.error)
        self.assertIn("Slow search", self.state.error)
        self.assertIn("does not start Execution", self.state.error)
        self.assertEqual(["Confirm exactly version 2", "Go back"], [a["label"] for a in self.state.activity_detail["available_actions"]])
        self.extension.action(self.context, "a-confirm-yes")
        envelope, = self.client.sent
        self.assertEqual(("architecture.confirm", 7, REF), (envelope["operation"], envelope["expected_version"], envelope["payload"]["expected_working_ref"]))
        self.assertEqual([{k: LIMITATION[k] for k in ("id", "subject", "version", "container")}], envelope["payload"]["accepted_limitations"])

    def test_a_lost_acknowledgment_is_retried_under_the_same_request(self) -> None:
        self.client.fail = ConnectionUnavailable("connection lost")
        with self.assertRaises(ArchitectureError) as caught:
            self.extension.action(self.context, "a-confirm-yes")
        self.assertIn("Outcome not confirmed", str(caught.exception))
        self.client.fail = None
        self.extension.action(self.context, "a-confirm-yes")
        self.assertEqual(self.client.sent[0]["request_id"], self.client.sent[1]["request_id"])

    def test_a_changed_version_is_refused_and_explained(self) -> None:
        self.client.fail = ServiceError(409, "working_ref_changed", "the working version changed since it was displayed; review the current version")
        with self.assertRaises(ArchitectureError) as caught:
            self.extension.action(self.context, "a-confirm-yes")
        self.assertIn("changed", str(caught.exception))

    def test_nothing_is_confirmable_before_review(self) -> None:
        self.client.view = {**VIEW, "state": "running"}
        for action in ("a-confirm", "a-confirm-yes"):
            with self.assertRaises(ArchitectureError):
                self.extension.action(self.context, action)
        self.assertEqual([], self.client.sent)

    def test_the_review_limit_decision_is_explicit(self) -> None:
        self.client.view = {**VIEW, "state": "paused", "owner_decisions": [{"target": "fidelity_review", "assignment_id": "a-revi-3"}]}
        self.extension.action(self.context, "a-grant")
        self.extension.action(self.context, "a-remain")
        first, second = self.client.sent
        self.assertEqual(("owner.decision", {"target": "fidelity_review", "choice": "grant_one", "assignment_id": "a-revi-3"}), (first["operation"], first["payload"]))
        self.assertEqual("remain_paused", second["payload"]["choice"])


if __name__ == "__main__":
    unittest.main()
