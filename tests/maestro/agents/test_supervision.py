"""Focused real-process checks for durable agent supervision."""

from __future__ import annotations

import os
import tempfile
import time
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from maestro.agents.recovery import RecoveryReconciler
from maestro.agents.supervisor import (
    AgentSupervisor,
    FileSupervisorJournal,
    LaunchRequest,
    LocalProcessUnits,
    OperationIdentity,
    SupervisionError,
    SystemdUserUnits,
    UnitIdentity,
)
from maestro.agents import ResolvedAgentRoute, RunningToolIdentity
import maestro.agents.supervisor as supervisor_module


class DurableSupervisionTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.journal = FileSupervisorJournal(self.root / "service-owned" / "runs.json")
        self.units = LocalProcessUnits()
        self.published = []

        class Publisher:
            def __init__(self, published):
                self.published = published

            def publish(self, identity):
                self.published.append(identity)

        self.supervisor = AgentSupervisor(self.journal, self.units, runtime_identity_reporter=Publisher(self.published))
        self.identity = OperationIdentity("project-one", "activity-one", "assignment-one", "run-one")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def request(self, script: str, *, timeout: float = 5, stall: float = 1) -> LaunchRequest:
        return LaunchRequest(self.identity, ("/bin/sh", "-c", script), str(self.root), timeout, stall)

    @staticmethod
    def route() -> ResolvedAgentRoute:
        return ResolvedAgentRoute(
            role="architect",
            tool="codex",
            requested_model_id="openai/gpt-5.6-codex-2026-09-01",
            provider="openai",
            tool_version="1.2.3",
            executable="/usr/bin/codex",
            credential_profile="credential-codex",
            settings_profile="settings-codex",
            location="cloud",
            capabilities=("code_edit",),
            context_limit_tokens=131072,
            permitted_destinations=(),
            configuration_hash="a" * 64,
        )

    def test_journals_confirmed_identity_output_and_terminal_result(self) -> None:
        running = self.supervisor.launch(self.request("printf ready; sleep 0.05"))
        self.assertEqual("running", running.state)
        self.assertGreater(running.pid or 0, 0)
        self.assertTrue(running.boot_id)
        self.assertTrue(running.start_identity)
        self.assertTrue(running.invocation_id)
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
        self.assertEqual("blocked", first.status)
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

    def test_unacknowledged_started_unit_is_reconciled_and_stopped_by_exact_identity(self) -> None:
        class StartedWithoutAcknowledgement(LocalProcessUnits):
            visible = False

            def launch(self, request):
                self.managed = super().launch(request)
                raise OSError("acknowledgement interrupted")

            def inspect(self, unit_name):
                if not self.visible:
                    return None
                return super().inspect(unit_name)

        units = StartedWithoutAcknowledgement()
        supervisor = AgentSupervisor(self.journal, units)
        with self.assertRaisesRegex(SupervisionError, "acknowledged"):
            supervisor.launch(self.request("sleep 5"))

        self.assertEqual("launch_uncertain", supervisor.poll(self.identity).state)
        self.assertEqual(
            "stop_unconfirmed", supervisor.stop(self.identity, "cancelled").state
        )
        units.visible = True
        reconciled = supervisor.poll(self.identity)
        self.assertEqual("running", reconciled.state)
        self.assertTrue(reconciled.invocation_id)
        stopped = supervisor.stop(self.identity, "cancelled")
        self.assertEqual("cancelled", stopped.state)
        self.assertTrue(units.inspect(self.identity.unit_name).cgroup_empty)

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

    def test_verified_inactive_invocation_completes_but_unknown_or_mismatched_identity_blocks(self) -> None:
        self.supervisor.launch(self.request("exit 0"))
        for _ in range(20):
            if self.supervisor.poll(self.identity).state == "completed":
                break
            time.sleep(0.02)
        completed = RecoveryReconciler(self.journal, self.units).reconcile(self.identity)
        self.assertEqual("terminal", completed.status)
        self.assertEqual("exit_0", completed.reason)
        self.assertEqual("completed", self.journal.get(self.identity.key).state)

        unknown_identity = OperationIdentity("project-one", "activity-one", "assignment-two", "run-two")
        self.supervisor.launch(LaunchRequest(unknown_identity, ("/bin/sh", "-c", "sleep 5"), str(self.root), 5, 1))
        saved = self.journal.get(unknown_identity.key)
        assert saved is not None

        class MismatchedUnits(LocalProcessUnits):
            def inspect(self, unit_name):
                observed = super().inspect(unit_name)
                return None if observed is None else replace(observed, invocation_id="different-invocation")

        mismatched = MismatchedUnits()
        mismatched._units = self.units._units
        mismatched._identities = self.units._identities
        decision = RecoveryReconciler(self.journal, mismatched).reconcile(unknown_identity)
        self.assertEqual("blocked", decision.status)
        self.assertEqual("identity_mismatch", decision.reason)
        self.units.stop(unknown_identity.unit_name)

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

    def test_runtime_identity_publishes_only_its_reserved_confirmed_identity(self) -> None:
        self.supervisor.reserve_runtime_identity(self.identity, self.route())
        self.supervisor.launch(self.request("sleep 5"))
        identity = RunningToolIdentity(
            "tool_metadata", "openai", "openai/gpt-5.6-codex-2026-09-01", "1.2.3", "a" * 64
        )
        self.supervisor.report_runtime_identity(self.identity, identity)
        self.assertEqual(1, len(self.published))
        self.assertEqual(self.identity.key, self.published[0].operation_key)
        self.assertEqual(identity.provider, self.published[0].provider)
        saved = self.journal.get(self.identity.key)
        assert saved is not None
        self.assertEqual("runtime_identity_confirmed", saved.events[-1]["kind"])
        with self.assertRaisesRegex(SupervisionError, "already published"):
            self.supervisor.report_runtime_identity(self.identity, identity)

        unmatched = OperationIdentity("project-one", "activity-one", "assignment-two", "run-two")
        self.supervisor.launch(LaunchRequest(unmatched, ("/bin/sh", "-c", "sleep 5"), str(self.root), 5, 1))
        with self.assertRaisesRegex(SupervisionError, "reservation is not available"):
            self.supervisor.report_runtime_identity(unmatched, identity)
        self.units.stop(unmatched.unit_name)

    def test_runtime_identity_requires_protected_authority_and_cannot_be_replayed(self) -> None:
        self.assertFalse(hasattr(supervisor_module, "_issue_verified_runtime_identity"))
        self.assertFalse(hasattr(supervisor_module, "_VerifiedRuntimeIdentityDelivery"))
        self.assertFalse(hasattr(self.supervisor, "runtime_identity_callback"))
        self.assertFalse(hasattr(self.supervisor, "consume_verified_runtime_identity"))
        self.supervisor.reserve_runtime_identity(self.identity, self.route())
        self.supervisor.launch(self.request("sleep 5"))
        tool_identity = RunningToolIdentity(
            "tool_metadata", "openai", "openai/gpt-5.6-codex-2026-09-01", "1.2.3", "a" * 64
        )
        self.supervisor.report_runtime_identity(self.identity, tool_identity)
        self.assertEqual(1, len(self.published))
        with self.assertRaisesRegex(SupervisionError, "already published"):
            self.supervisor.report_runtime_identity(self.identity, tool_identity)

    def test_runtime_identity_rejects_agent_text_and_unconfirmed_unit(self) -> None:
        self.supervisor.reserve_runtime_identity(self.identity, self.route())
        self.supervisor.launch(self.request("sleep 5"))
        with self.assertRaisesRegex(SupervisionError, "trusted tool metadata"):
            self.supervisor.report_runtime_identity(self.identity, RunningToolIdentity("agent_text", "openai", "model", "1", "a" * 64))
        with self.assertRaisesRegex(SupervisionError, "differs from the reserved route"):
            self.supervisor.report_runtime_identity(self.identity, RunningToolIdentity("tool_metadata", "openai", "different-model", "1.2.3", "a" * 64))
        self.units.stop(self.identity.unit_name)
        with self.assertRaisesRegex(SupervisionError, "cannot confirm"):
            self.supervisor.report_runtime_identity(self.identity,
                RunningToolIdentity(
                    "tool_metadata",
                    "openai",
                    "openai/gpt-5.6-codex-2026-09-01",
                    "1.2.3",
                    "a" * 64,
                ))
        self.assertEqual([], self.published)


class SystemdUserUnitsTest(unittest.TestCase):
    def test_uses_derived_user_bus_and_retains_completed_unit(self) -> None:
        controller = SystemdUserUnits(systemd_run="systemd-run-test", systemctl="systemctl-test")
        identity = OperationIdentity("project-one", "activity-one", "assignment-one", "run-one")
        request = LaunchRequest(identity, ("/bin/true",), "/tmp", 5, 1)
        observed = UnitIdentity(identity.unit_name, 123, "boot", "start", "invocation", True, False)
        with patch("maestro.agents.supervisor.subprocess.Popen") as popen, patch.object(controller, "inspect", return_value=observed):
            process = popen.return_value
            process.poll.return_value = None
            controller.launch(request)
        arguments = popen.call_args.args[0]
        environment = popen.call_args.kwargs["env"]
        self.assertNotIn("--collect", arguments)
        self.assertIn("--property=RemainAfterExit=yes", arguments)
        self.assertEqual(f"/run/user/{os.getuid()}", environment["XDG_RUNTIME_DIR"])
        self.assertEqual(f"unix:path=/run/user/{os.getuid()}/bus", environment["DBUS_SESSION_BUS_ADDRESS"])

    def test_inspection_persists_systemd_invocation_id_and_uses_derived_bus(self) -> None:
        controller = SystemdUserUnits(systemctl="systemctl-test")
        output = "MainPID=123\nActiveState=active\nControlGroup=/user.slice/test\nInvocationID=invocation\n"
        with patch("maestro.agents.supervisor.subprocess.run") as run, patch("maestro.agents.supervisor._boot_id", return_value="boot"), patch("maestro.agents.supervisor._proc_start_identity", return_value="start"):
            run.return_value.returncode = 0
            run.return_value.stdout = output
            observed = controller.inspect("maestro-agent-run-one.service")
        assert observed is not None
        self.assertEqual("invocation", observed.invocation_id)
        self.assertEqual(f"/run/user/{os.getuid()}", run.call_args.kwargs["env"]["XDG_RUNTIME_DIR"])


if __name__ == "__main__":
    unittest.main()
