from __future__ import annotations

import hashlib
import json
import sqlite3
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from unittest import mock

from maestro.operational_state import (
    Actor,
    IdempotencyConflict,
    InvalidRecord,
    InvalidTransition,
    OperationalStateStore,
    StaleState,
)
from test_packet_eligibility import ACTOR, NOW, LATER, PacketDatabase, REASON, STATES, state_payload


class NeedsReplanClosureTests(unittest.TestCase):
    def setUp(self) -> None:
        self.runtime = PacketDatabase()
        self.runtime.force_source("NeedsReplan")

    def tearDown(self) -> None:
        self.runtime.close()

    def replace_runtime(self) -> None:
        self.runtime.close()
        self.runtime = PacketDatabase()
        self.runtime.force_source("NeedsReplan")

    def close(
        self,
        *,
        version: int = 1,
        key: str = "close-1",
        reason=REASON,
        actor=ACTOR,
        now: str = NOW,
        packet_id: str = "packet-1",
    ):
        return self.runtime.store.record_and_close_needs_replan(
            packet_id, version, reason, key, actor, now
        )

    def test_01_needsreplan_transitions_to_cancelled(self) -> None:
        result = self.close()
        self.assertEqual(result, state_payload("Cancelled", 2))
        packet = self.runtime.store.snapshot("Packet", "packet-1")
        self.assertEqual(
            (packet["state"], packet["version"], packet["updated_at"]),
            ("Cancelled", 2, NOW),
        )
        events = self.runtime.state_events()
        self.assertEqual(len(events), 1)
        event = events[0]
        self.assertEqual(event["entity_type"], "Packet")
        self.assertEqual(event["entity_id"], "packet-1")
        self.assertEqual(event["event_type"], "PacketStateChanged")
        self.assertEqual(event["before_json"], state_payload("NeedsReplan", 1))
        self.assertEqual(event["after_json"], result)
        self.assertEqual(json.loads(event["reason"]), REASON)
        self.assertEqual(event["actor_type"], "MaestroDeveloper")
        self.assertEqual(event["actor_id"], "developer-1")
        self.assertEqual(event["correlation_id"], "correlation-1")
        self.assertEqual(event["observed_at"], NOW)

    def test_02_every_other_source_state_raises_invalid_transition(self) -> None:
        for state in STATES:
            if state == "NeedsReplan":
                continue
            with self.subTest(state=state):
                self.runtime.force_source(state)
                before_events = len(self.runtime.state_events())
                with self.assertRaises(InvalidTransition):
                    self.close(key=f"other-{state}")
                packet = self.runtime.store.snapshot("Packet", "packet-1")
                self.assertEqual((packet["state"], packet["version"]), (state, 1))
                self.assertEqual(len(self.runtime.state_events()), before_events)

    def test_03_version_mismatch_raises_stale_state(self) -> None:
        before = self.runtime.store.snapshot("Packet", "packet-1")
        with self.assertRaises(StaleState):
            self.close(version=2)
        self.assertEqual(self.runtime.store.snapshot("Packet", "packet-1"), before)
        self.assertEqual(self.runtime.state_events(), [])

        with self.assertRaises(StaleState):
            self.close(version=999, key="also-stale")
        self.assertEqual(self.runtime.store.snapshot("Packet", "packet-1"), before)
        self.assertEqual(self.runtime.state_events(), [])

    def test_04_malformed_reason_payload_rejects(self) -> None:
        cases = (
            state_payload("Planned", 1),
            {
                "kind": "claim",
                "packet_id": "packet-1",
                "lease_id": "lease-1",
                "lock_ids": [],
            },
            {"kind": "reason", "reason_code": "MISSING_DETAIL_KEY"},
            {"kind": "not-a-real-kind"},
            "not-a-mapping",
        )
        for index, reason in enumerate(cases):
            with self.subTest(reason=reason):
                with self.assertRaises(InvalidRecord):
                    self.close(reason=reason, key=f"malformed-{index}")
        packet = self.runtime.store.snapshot("Packet", "packet-1")
        self.assertEqual((packet["state"], packet["version"]), ("NeedsReplan", 1))
        self.assertEqual(self.runtime.state_events(), [])

    def test_05_fingerprint_replay_is_exact_and_changed_facts_conflict(self) -> None:
        actor = Actor("MaestroDeveloper", "developer-1", "correlation-1", 1)
        first = self.close(key="replay-1", actor=actor, now=NOW)
        replay = self.close(key="replay-1", actor=actor, now=LATER)
        self.assertEqual(replay, first)
        packet = self.runtime.store.snapshot("Packet", "packet-1")
        self.assertEqual((packet["state"], packet["version"], packet["updated_at"]), ("Cancelled", 2, NOW))
        events = self.runtime.state_events()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["observed_at"], NOW)

        documented = {
            "actor": {
                "actor_id": "developer-1",
                "actor_type": "MaestroDeveloper",
                "causation_event_id": 1,
                "correlation_id": "correlation-1",
            },
            "operation": "record_and_close_needs_replan",
            "payload": {
                "expected_version": 1,
                "packet_id": "packet-1",
                "reason": REASON,
            },
        }
        encoded = json.dumps(
            documented,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
        self.assertEqual(
            events[0]["command_fingerprint"], hashlib.sha256(encoded).hexdigest()
        )

        changed = (
            lambda: self.close(key="replay-1", actor=actor, reason={**REASON, "reason_code": "OTHER"}),
            lambda: self.close(key="replay-1", actor=Actor("Other", "developer-1", "correlation-1", 1)),
            lambda: self.close(key="replay-1", actor=Actor("MaestroDeveloper", "other", "correlation-1", 1)),
            lambda: self.close(key="replay-1", actor=Actor("MaestroDeveloper", "developer-1", "other", 1)),
        )
        for command in changed:
            with self.assertRaises(IdempotencyConflict):
                command()
        self.assertEqual(len(self.runtime.state_events()), 1)
        self.assertEqual(self.runtime.store.snapshot("Packet", "packet-1")["version"], 2)

    def test_06_event_rollback_concurrency_and_restart_reconstruct_exactly(self) -> None:
        before_snapshot = self.runtime.store.snapshot("Packet", "packet-1")
        before_events = self.runtime.store.events_after(0, 1000)

        with mock.patch.object(
            self.runtime.store,
            "_insert_packet_state_event",
            side_effect=RuntimeError("event insert failure"),
        ):
            with self.assertRaisesRegex(RuntimeError, "event insert failure"):
                self.close(key="fail-event-insert")
        self.assertEqual(self.runtime.store.snapshot("Packet", "packet-1"), before_snapshot)
        self.assertEqual(self.runtime.store.events_after(0, 1000), before_events)

        class _FailingConnection(sqlite3.Connection):
            def execute(self, sql, *args, **kwargs):
                if (
                    isinstance(sql, str)
                    and "UPDATE packets SET state=?,updated_at=?,version=?" in sql
                ):
                    raise RuntimeError("packet update failure")
                return super().execute(sql, *args, **kwargs)

        original_connect = sqlite3.connect

        def connect_with_failing_factory(*args, **kwargs):
            kwargs.setdefault("factory", _FailingConnection)
            return original_connect(*args, **kwargs)

        with mock.patch.object(sqlite3, "connect", connect_with_failing_factory):
            with self.assertRaisesRegex(RuntimeError, "packet update failure"):
                self.close(key="fail-packet-update")
        self.assertEqual(self.runtime.store.snapshot("Packet", "packet-1"), before_snapshot)
        self.assertEqual(self.runtime.store.events_after(0, 1000), before_events)

        barrier = threading.Barrier(2)

        def attempt(number: int):
            store = OperationalStateStore(self.runtime.config)
            barrier.wait()
            try:
                return store.record_and_close_needs_replan(
                    "packet-1", 1, REASON, f"concurrent-{number}", ACTOR, NOW
                )
            except Exception as error:
                return error

        with ThreadPoolExecutor(max_workers=2) as executor:
            outcomes = list(executor.map(attempt, (1, 2)))
        winners = [outcome for outcome in outcomes if isinstance(outcome, dict)]
        stale = [outcome for outcome in outcomes if isinstance(outcome, StaleState)]
        self.assertEqual(len(winners), 1)
        self.assertEqual(len(stale), 1)
        row = self.runtime.store.snapshot("Packet", "packet-1")
        self.assertEqual((row["state"], row["version"]), ("Cancelled", 2))
        self.assertEqual(len(self.runtime.state_events()), 1)

        self.replace_runtime()
        actor = Actor("MaestroDeveloper", "developer-1", "correlation-1", 1)
        first = self.runtime.store.record_and_close_needs_replan(
            "packet-1", 1, REASON, "restart-close", actor, NOW
        )
        original_events = self.runtime.state_events()

        reopened = OperationalStateStore(self.runtime.config)
        row = reopened.snapshot("Packet", "packet-1")
        self.assertEqual((row["state"], row["version"]), ("Cancelled", 2))
        replay = reopened.record_and_close_needs_replan(
            "packet-1", 1, REASON, "restart-close", actor, LATER
        )
        self.assertEqual(replay, first)
        self.assertEqual(
            [event for event in reopened.events_after(0, 1000) if event["event_type"] == "PacketStateChanged"],
            original_events,
        )


if __name__ == "__main__":
    unittest.main()
