from __future__ import annotations

import tempfile
import threading
import unittest
from pathlib import Path

from maestro.agents.measurements import ContextPolicy, ContextReading, UsageMeasurement
from maestro.agents.sessions import Checkpoint, FileSessionStore, SessionError, SessionManager
from maestro.agents.supervisor import OperationIdentity


class SessionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(); self.root = Path(self.temporary.name)
        self.manager = SessionManager(FileSessionStore(self.root / "service" / "sessions.json"))
        self.manager.create("session-one", OperationIdentity("project-one", "activity-one", "assignment-one", "run-one"), "codex", "provider-one")
    def tearDown(self) -> None: self.temporary.cleanup()
    def test_serialized_actions_and_durable_usage(self) -> None:
        self.manager.begin_action("session-one")
        with self.assertRaises(SessionError): self.manager.begin_action("session-one")
        done = self.manager.finish_action("session-one", UsageMeasurement("session-one", "event-one", 12, 10, 5, "reported", "tool"))
        self.assertEqual(("idle", 1, 12), (done.state, done.action_count, done.active_seconds))
        reloaded = SessionManager(FileSessionStore(self.root / "service" / "sessions.json")).store.load("session-one")
        self.assertEqual(12, reloaded.active_seconds)
    def test_warning_handoff_and_continuation_preserve_counts(self) -> None:
        self.manager.begin_action("session-one"); self.manager.finish_action("session-one", UsageMeasurement("session-one", "event", 8, None, None, "unavailable", "tool"))
        warning = ContextReading("initial", 100, 80, "reported", 100, "tool")
        self.assertEqual("warning", self.manager.observe_context("session-one", warning, now=101))
        handoff = ContextReading("initial", 100, 90, "reported", 102, "tool")
        self.assertEqual("handoff", self.manager.observe_context("session-one", handoff, now=103))
        self.manager.checkpoint("session-one", Checkpoint("output/checkpoint.json", "initial", 103, "tool"))
        continued = self.manager.continue_capacity("session-one", "provider-two")
        self.assertEqual((8, 1, "initial-next", "provider-two"), (continued.active_seconds, continued.action_count, continued.segment_id, continued.provider_session_id))
    def test_unknown_stale_and_wrong_segment_measurements_stay_labeled(self) -> None:
        unknown = ContextReading("initial", None, None, "unavailable", 10, "not supported")
        self.assertEqual("unknown", self.manager.observe_context("session-one", unknown, now=11))
        stale = ContextReading("initial", 100, 1, "reported", 1, "tool")
        self.assertEqual("unknown", self.manager.observe_context("session-one", stale, now=40))
        handoff = ContextReading("initial", 100, 90, "reported", 41, "tool")
        self.assertEqual("handoff", self.manager.observe_context("session-one", handoff, now=41))
        self.manager.checkpoint("session-one", Checkpoint("checkpoint", "initial"))
        self.manager.continue_capacity("session-one", "provider-two")
        with self.assertRaises(SessionError) as caught: self.manager.observe_context("session-one", stale, now=2)
        self.assertEqual("stale_measurement", caught.exception.code)
    def test_invalid_policy_is_rejected(self) -> None:
        with self.assertRaises(Exception): ContextPolicy(warning_percent=80, handoff_percent=70)

    def test_usage_provenance_is_durable_and_deduplicated(self) -> None:
        usage = UsageMeasurement("session-one", "event-one", 12, 10, 5, "reported", "tool")
        self.manager.begin_action("session-one")
        self.manager.finish_action("session-one", usage)
        retried = self.manager.finish_action("session-one", usage)
        self.assertEqual((1, 12, (usage,)), (retried.action_count, retried.active_seconds, retried.usage_provenance))
        with self.assertRaises(SessionError) as caught:
            self.manager.finish_action("session-one", UsageMeasurement("session-one", "event-one", 13, 10, 5, "reported", "tool"))
        self.assertEqual("provenance_conflict", caught.exception.code)

    def test_managers_sharing_a_store_serialize_action_start(self) -> None:
        other = SessionManager(FileSessionStore(self.root / "service" / "sessions.json"))
        start = threading.Barrier(2)
        outcomes: list[str] = []

        def begin(manager: SessionManager) -> None:
            start.wait()
            try:
                manager.begin_action("session-one")
                outcomes.append("started")
            except SessionError as error:
                outcomes.append(error.code)

        first = threading.Thread(target=begin, args=(self.manager,))
        second = threading.Thread(target=begin, args=(other,))
        first.start(); second.start(); first.join(); second.join()
        self.assertEqual(["session_busy", "started"], sorted(outcomes))

    def test_lost_replacement_requires_loss_and_verified_checkpoint(self) -> None:
        checkpoint = Checkpoint("checkpoint", "initial", 1, "tool")
        self.manager.checkpoint("session-one", checkpoint)
        with self.assertRaises(SessionError):
            self.manager.replace_lost("session-one", "provider-two")
        self.manager.mark_lost("session-one")
        replaced = self.manager.replace_lost("session-one", "provider-two")
        self.assertEqual(("idle", "initial-next", "provider-two", None), (replaced.state, replaced.segment_id, replaced.provider_session_id, replaced.checkpoint))


if __name__ == "__main__": unittest.main()
