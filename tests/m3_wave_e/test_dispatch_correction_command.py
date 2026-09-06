from __future__ import annotations

import http.client
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "m1_02"))

from test_correction_dispatch import CorrectionDispatchDatabase  # noqa: E402

from maestro import read_api  # noqa: E402


def _post(port: int, path: str, body: dict) -> tuple[int, dict]:
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    try:
        payload = json.dumps(body).encode("utf-8")
        connection.request(
            "POST", path, body=payload, headers={"Content-Type": "application/json"}
        )
        response = connection.getresponse()
        raw = response.read()
        return response.status, json.loads(raw) if raw else {}
    finally:
        connection.close()


class DispatchCorrectionCommandTests(unittest.TestCase):
    def setUp(self):
        self.db = CorrectionDispatchDatabase()
        self.server = read_api.ReadApiServer(read_api.ReadApiConfig(port=0, runtime_dir=self.db.path))
        self.server.start()

    def tearDown(self):
        self.server.stop()
        self.db.close()

    def _envelope(self, **overrides) -> dict:
        base = {
            "idempotency_key": "atlas-dispatch-correction-1",
            "actor": {"actor_type": "Owner", "actor_id": "owner-1", "correlation_id": "correlation-1"},
            "packet_id": "packet-1",
            "expected_version": 9,
            "review_id": self.db.review_id,
            "reason_payload": {"kind": "reason", "reason_code": "OWNER_AMENDED_CONTRACT", "detail_reference": None},
        }
        base.update(overrides)
        return base

    def test_a_real_amend_dispatch_succeeds_and_generates_real_lease_lock_attempt(self):
        status, body = _post(self.server.bound_port, "/command/dispatch-correction", self._envelope())
        self.assertEqual(status, 200)
        self.assertEqual(body["packet"]["state"], "Leased")
        self.assertTrue(body["claim"]["lease_id"].startswith("correction-lease-"))
        self.assertTrue(body["attempt"]["entity_id"].startswith("correction-attempt-"))
        self.assertEqual(body["lease"]["state"], "Active")
        # Real locks generated from the packet's own real resource_claims_json
        # ("finite:gpu", "path:services/maestro", "shared:operational-state").
        self.assertEqual(len(body["locks"]), 3)
        self.assertEqual(len(body["claim"]["lock_ids"]), 3)

    def test_a_stale_expected_version_is_rejected(self):
        status, body = _post(
            self.server.bound_port, "/command/dispatch-correction", self._envelope(expected_version=1)
        )
        self.assertEqual(status, 409)
        self.assertEqual(body["error"], "stale_state")

    def test_an_unknown_packet_id_is_rejected(self):
        status, body = _post(
            self.server.bound_port,
            "/command/dispatch-correction",
            self._envelope(packet_id="does-not-exist"),
        )
        self.assertEqual(status, 400)
        self.assertEqual(body["error"], "invalid_command")

    def test_a_missing_review_id_is_rejected_before_any_write(self):
        envelope = self._envelope()
        del envelope["review_id"]
        status, body = _post(self.server.bound_port, "/command/dispatch-correction", envelope)
        self.assertEqual(status, 400)
        self.assertEqual(body["error"], "invalid_command")

    def test_repeating_the_same_idempotency_key_replays_the_same_real_result(self):
        status1, body1 = _post(self.server.bound_port, "/command/dispatch-correction", self._envelope())
        status2, body2 = _post(self.server.bound_port, "/command/dispatch-correction", self._envelope())
        self.assertEqual(status1, 200)
        self.assertEqual(status2, 200)
        self.assertEqual(body1, body2)


if __name__ == "__main__":
    unittest.main()
