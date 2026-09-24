"""Registration commands and actions submit exactly the Owner's explicit requests."""
from __future__ import annotations

import unittest
from types import SimpleNamespace

from maestro.terminal.connection import ConnectionUnavailable, ServiceError
from maestro.terminal.extensions import ExtensionContext, ExtensionRegistry
from maestro.terminal.registration import RegistrationError, RegistrationExtension

PACKAGE = {"repository": "o/r", "commit": "a" * 40, "registration_version": 1, "candidate_id": "cand-1", "manifest_path": "m.json", "manifest_sha256": "b" * 64}


class Client:
    def __init__(self) -> None:
        self.sent, self.fail = [], None

    def submit(self, envelope):
        self.sent.append(envelope)
        if self.fail:
            raise self.fail
        return {"receipt": {"status": "accepted", "project_id": "p", "activity_id": "a", "result": {}}}

    def get_json(self, path, *, timeout=15):
        return {"data": {"package_ref": PACKAGE, "activity_version": 4, "repository": "o/r", "registration_version": 1, "state": "ready"}}


def context(client):
    state = SimpleNamespace(
        selected_project_id="p", selected_activity_id="a", error=None, activities=(),
        activity_detail={"available_actions": [
            {"action_id": "a-confirm", "label": "Confirm", "kind": "decision"},
            {"action_id": "a-cancel", "label": "Cancel registration", "kind": "action"}]},
    )
    return ExtensionContext(client, state)


class RegistrationExtensionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.extension = RegistrationExtension(lambda: "req-fixed")
        self.registry = ExtensionRegistry()
        self.extension.install(self.registry)
        self.client = Client()
        self.context = context(self.client)

    def test_register_sends_the_intake_selections(self) -> None:
        self.registry.invoke_command("register", self.context, "o/r docs/overview.md --ref refs/heads/x --branch qa/p --scope PM1,PM2 --architect codex:m --reviewer claude_code:n")
        envelope, = self.client.sent
        self.assertEqual("registration.start", envelope["operation"])
        self.assertEqual({"repository": "o/r", "overview_path": "docs/overview.md", "source_ref": "refs/heads/x", "publication_branch": "qa/p",
                          "scope": {"kind": "milestones", "milestones": ["PM1", "PM2"]}, "architect": {"tool": "codex", "model": "m"},
                          "reviewer": {"tool": "claude_code", "model": "n"}}, envelope["payload"])

    def test_bad_usage_and_rejected_intake_are_plain(self) -> None:
        for arguments in ("", "o/r", "o/r p --nope x", "o/r p --architect codex"):
            with self.assertRaises(RegistrationError):
                self.registry.invoke_command("register", self.context, arguments)
        self.assertEqual([], self.client.sent)
        self.client.fail = ServiceError(400, "invalid_request", "binding_missing: no repository binding is configured for o/r")
        with self.assertRaises(RegistrationError) as caught:
            self.registry.invoke_command("register", self.context, "o/r p")
        self.assertIn("binding_missing", str(caught.exception))

    def test_confirm_names_the_displayed_candidate_and_is_never_repeated_under_a_new_identity(self) -> None:
        self.client.fail = ConnectionUnavailable("connection lost")
        with self.assertRaises(RegistrationError) as caught:
            self.registry.invoke_action("decision", self.context, "a-confirm")
        self.assertIn("Outcome not confirmed", str(caught.exception))
        self.client.fail = None
        self.registry.invoke_action("decision", self.context, "a-confirm")
        first, second = self.client.sent
        self.assertEqual(first["request_id"], second["request_id"])
        self.assertEqual(("registration.confirm", 4, {"package_ref": PACKAGE}), (second["operation"], second["expected_version"], second["payload"]))

    def test_cancel_needs_a_second_deliberate_action(self) -> None:
        self.registry.invoke_action("action", self.context, "a-cancel")
        self.assertEqual([], self.client.sent)
        labels = [a["label"] for a in self.context.state.activity_detail["available_actions"]]
        self.assertEqual(["Cancel registration", "Go back"], labels)
        self.registry.invoke_action("action", self.context, "a-cancel-yes")
        self.assertEqual("registration.cancel", self.client.sent[0]["operation"])


if __name__ == "__main__":
    unittest.main()
