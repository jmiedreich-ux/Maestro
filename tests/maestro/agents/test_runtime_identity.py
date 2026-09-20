"""Focused checks for protected runtime identity delivery."""

from __future__ import annotations

import unittest

from maestro.agents.runtime_identity import (
    ConfirmedRuntimeIdentity,
    RuntimeIdentityProtocolError,
    compose_runtime_identity_endpoints,
)


class RuntimeIdentityProtocolTest(unittest.TestCase):
    def setUp(self) -> None:
        self.identity = ConfirmedRuntimeIdentity(
            "project-1:activity-1:assignment-1:run-1", "openai", "openai/model-1", "1",
            "a" * 64, 42, "boot", "start", "invocation",
        )

    def test_separate_service_capabilities_publish_and_single_consume(self) -> None:
        reporter, consumer = compose_runtime_identity_endpoints()
        self.assertFalse(hasattr(reporter, "consume"))
        self.assertFalse(hasattr(consumer, "publish"))

        reporter.publish(self.identity)
        with self.assertRaisesRegex(RuntimeIdentityProtocolError, "already exists"):
            reporter.publish(self.identity)
        self.assertEqual(self.identity, consumer.consume(self.identity.operation_key))
        with self.assertRaisesRegex(RuntimeIdentityProtocolError, "unavailable"):
            consumer.consume(self.identity.operation_key)
        with self.assertRaisesRegex(RuntimeIdentityProtocolError, "already exists"):
            reporter.publish(self.identity)

    def test_separately_composed_authorities_cannot_cross_consume(self) -> None:
        reporter, _consumer = compose_runtime_identity_endpoints()
        _other_reporter, other_consumer = compose_runtime_identity_endpoints()
        reporter.publish(self.identity)
        with self.assertRaisesRegex(RuntimeIdentityProtocolError, "unavailable"):
            other_consumer.consume(self.identity.operation_key)


if __name__ == "__main__":
    unittest.main()
