"""Focused Unix-protocol checks for protected runtime identity delivery."""

from __future__ import annotations

import os
import socket
import tempfile
import unittest
from pathlib import Path

from maestro.agents.runtime_identity import (
    ConfirmedRuntimeIdentity,
    PlanningIdentityConsumer,
    RuntimeIdentityCore,
    RuntimeIdentityProtocolError,
    RuntimeIdentityServer,
    SupervisorIdentityReporter,
)


class RuntimeIdentityProtocolTest(unittest.TestCase):
    def setUp(self) -> None:
        self.identity = ConfirmedRuntimeIdentity(
            "project-1:activity-1:assignment-1:run-1", "openai", "openai/model-1", "1",
            "a" * 64, 42, "boot", "start", "invocation",
        )

    def test_core_rejects_hostile_planning_write_and_single_consumes(self) -> None:
        core = RuntimeIdentityCore(supervisor_uid=1001, planning_uid=1002)
        with self.assertRaisesRegex(RuntimeIdentityProtocolError, "only the supervisor"):
            core.publish(1002, self.identity)
        core.publish(1001, self.identity)
        with self.assertRaisesRegex(RuntimeIdentityProtocolError, "already exists"):
            core.publish(1001, self.identity)
        with self.assertRaisesRegex(RuntimeIdentityProtocolError, "only planning"):
            core.consume(1001, self.identity.operation_key)
        self.assertEqual(self.identity, core.consume(1002, self.identity.operation_key))
        with self.assertRaisesRegex(RuntimeIdentityProtocolError, "unavailable"):
            core.consume(1002, self.identity.operation_key)

    def test_unix_protocol_uses_kernel_peer_identity_not_client_role_text(self) -> None:
        uid = os.getuid()
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "core" / "runtime.sock"
            # This test endpoint maps the real test process to the supervisor.
            # A production core requires distinct configured OS identities.
            core = RuntimeIdentityCore(supervisor_uid=uid, planning_uid=uid + 1)
            server = RuntimeIdentityServer(path, core)
            server.start()
            try:
                SupervisorIdentityReporter(path).publish(self.identity)
                raw = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                with raw:
                    raw.connect(os.fspath(path))
                    raw.sendall(b'{"action":"consume","operation_key":"project-1:activity-1:assignment-1:run-1","role":"planning"}\n')
                    response = raw.recv(4096)
                self.assertIn(b'"code":"invalid_request"', response)
                with self.assertRaises(RuntimeIdentityProtocolError) as rejected:
                    PlanningIdentityConsumer(path).consume(self.identity.operation_key)
                self.assertEqual("consumer_unauthorized", rejected.exception.code)
            finally:
                server.close()

    def test_distinct_runtime_identities_are_required(self) -> None:
        with self.assertRaisesRegex(ValueError, "must be separate"):
            RuntimeIdentityCore(supervisor_uid=1001, planning_uid=1001)
