"""Focused real-process checks for durable agent supervision."""

from __future__ import annotations

import tempfile
import time
import unittest
from dataclasses import replace
from pathlib import Path

from maestro.agents.recovery import RecoveryReconciler
from maestro.agents.supervisor import (
    AgentSupervisor,
    FileSupervisorJournal,
    LaunchRequest,
    LocalProcessUnits,
    OperationIdentity,
    SupervisionError,
)


class DurableSupervisionTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.journal = FileSupervisorJournal(self.root / "service-owned" / "runs.json")
        self.units = LocalProcessUnits()
        self.supervisor = AgentSupervisor(self.journal, self.units)
        self.identity = OperationIdentity("project-one", "activity-one", "assignment-one", "run-one")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def request(self, script: str, *, timeout: float = 5, stall: float = 1) -> LaunchRequest:
        return LaunchRequest(self.identity, ("/bin/sh", "-c", script), str(self.root), timeout, stall)

    def test_journals_confirmed_identity_output_and_terminal_result(self) -> None:
        running = self.supervisor.launch(self.request("printf ready; sleep 0.05"))
        self.assertEqual("running", running.state)
        self.assertGreater(running.pid or 0, 0)
        self.assertTrue(running.boot_id)
        self.assertTrue(running.start_identity)
        for _ in range(30):
            record = self.supervisor.poll(self.identity)
            if record.state == "completed":
                break
            time.sleep(0.02)
        self.assertEqual("completed", record.state)
        self.assertEqual("exit_0", record.terminal_reason)
        stdout = next(event for event in record.events if event["kind"] == "stdout")
        self.assertIn("ready", str(stdout["data"]))
        self.assertEqual("terminal", record.events[-1]["kind"])
        self.assertEqual(tuple(range(1, len(record.events) + 1)), tuple(event["sequence"] for event in record.events))
        restarted = AgentSupervisor(self.journal, self.units)
        decision = RecoveryReconciler(self.journal, self.units).reconcile(self.identity)
        self.assertEqual("terminal", decision.status)
        self.assertIsNotNone(restarted)

    def test_interruption_before_or_after_ack_never_relaunches_or_changes_allowance(self) -> None:
        intent = self.request("sleep 5")
        # A failure before acknowledgement leaves intent for identity-based recovery.
        class BrokenUnits(LocalProcessUnits):
            def launch(self, request):
                raise OSError("interrupted")
        broken = AgentSupervisor(self.journal, BrokenUnits())
        with self.assertRaisesRegex(SupervisionError, "acknowledged"):
            broken.launch(intent)
        saved = self.journal.get(self.identity.key)
        assert saved is not None
        self.assertEqual("launch_uncertain", saved.state)
        first = RecoveryReconciler(self.journal, self.units).reconcile(self.identity)
        self.assertEqual("recovery_required", first.status)
        self.assertFalse(first.replacement_permitted)
        self.assertEqual(0, first.allowance_change)
        with self.assertRaisesRegex(SupervisionError, "already has a launch record"):
            self.supervisor.launch(intent)

        acknowledged_id = OperationIdentity("project-one", "activity-one", "assignment-two", "run-two")
        acknowledged = LaunchRequest(acknowledged_id, ("/bin/sh", "-c", "sleep 5"), str(self.root), 5, 1)
        self.supervisor.launch(acknowledged)
        after_ack = RecoveryReconciler(self.journal, self.units).reconcile(acknowledged_id)
        self.assertEqual("running", after_ack.status)
        self.assertEqual(0, after_ack.allowance_change)
        with self.assertRaisesRegex(SupervisionError, "already has a launch record"):
            self.supervisor.launch(acknowledged)
        self.units.stop(acknowledged_id.unit_name)

    def test_cancel_and_deadline_stop_confirmed_process_group_before_recovery(self) -> None:
        running = self.supervisor.launch(self.request("trap '' TERM; sleep 5"))
        cancelled = self.supervisor.stop(self.identity, "cancelled")
        self.assertEqual("cancelled", cancelled.state)
        self.assertEqual("cancelled", cancelled.terminal_reason)
        observed = self.units.inspect(running.unit_name)
        assert observed is not None
        self.assertTrue(observed.cgroup_empty)
        decision = RecoveryReconciler(self.journal, self.units).reconcile(self.identity)
        self.assertEqual("terminal", decision.status)

        identity = OperationIdentity("project-one", "activity-one", "assignment-two", "run-two")
        deadline = AgentSupervisor(self.journal, self.units)
        timed = deadline.launch(LaunchRequest(identity, ("/bin/sh", "-c", "sleep 5"), str(self.root), 0.01, 1))
        time.sleep(0.03)
        self.assertEqual("timed_out", deadline.poll(identity).state)
        self.assertEqual("timed_out", self.journal.get(identity.key).terminal_reason)
        self.assertNotEqual(timed.identity.key, running.identity.key)

    def test_stall_and_identity_mismatch_block_replacement(self) -> None:
        self.supervisor.launch(self.request("sleep 5", timeout=5, stall=0.01))
        time.sleep(0.03)
        self.assertEqual("stalled", self.supervisor.poll(self.identity).state)
        observed = self.units.inspect(self.identity.unit_name)
        assert observed is not None
        self.assertTrue(observed.cgroup_empty)

        identity = OperationIdentity("project-one", "activity-one", "assignment-two", "run-two")
        self.supervisor.launch(LaunchRequest(identity, ("/bin/sh", "-c", "sleep 5"), str(self.root), 5, 1))
        saved = self.journal.get(identity.key)
        assert saved is not None
        self.journal.save(replace(saved, pid=(saved.pid or 0) + 1))
        decision = RecoveryReconciler(self.journal, self.units).reconcile(identity)
        self.assertEqual("blocked", decision.status)
        self.assertFalse(decision.replacement_permitted)
        self.assertEqual(0, decision.allowance_change)
        self.units.stop(identity.unit_name)

    def test_heartbeat_is_durable_and_prevents_stall_until_its_own_deadline(self) -> None:
        self.supervisor.launch(self.request("sleep 5", timeout=5, stall=0.08))
        time.sleep(0.04)
        heartbeat = self.supervisor.heartbeat(self.identity, "agent progress")
        self.assertEqual("heartbeat", heartbeat.events[-1]["kind"])
        time.sleep(0.04)
        self.assertEqual("running", self.supervisor.poll(self.identity).state)
        time.sleep(0.05)
        self.assertEqual("stalled", self.supervisor.poll(self.identity).state)
        saved = self.journal.get(self.identity.key)
        assert saved is not None
        self.assertEqual("terminal", saved.events[-1]["kind"])


if __name__ == "__main__":
    unittest.main()
