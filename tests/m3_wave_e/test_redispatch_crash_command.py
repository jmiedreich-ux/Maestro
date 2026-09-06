from __future__ import annotations

import http.client
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "m2_wave_d"))

from test_resolve_crash_command import ACTOR, REASON, _PacketDatabase  # noqa: E402

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


class RedispatchCrashCommandTests(unittest.TestCase):
    def setUp(self):
        self.db = _PacketDatabase()
        self.server = read_api.ReadApiServer(read_api.ReadApiConfig(port=0, runtime_dir=self.db.path))
        self.server.start()

    def tearDown(self):
        self.server.stop()
        self.db._temporary.cleanup()

    def _envelope(self, **overrides) -> dict:
        base = {
            "idempotency_key": "atlas-redispatch-1",
            "actor": ACTOR,
            "packet_id": "packet-1",
            "expected_version": 1,
            "reason_payload": REASON,
        }
        base.update(overrides)
        return base

    def test_a_real_redispatch_closes_the_old_packet_and_materializes_a_real_new_one(self):
        status, body = _post(self.server.bound_port, "/command/redispatch-crash", self._envelope())
        self.assertEqual(status, 200)
        self.assertEqual(body["closed_packet"]["state"], "Cancelled")
        self.assertEqual(body["redispatched_packet"]["state"], "Planned")
        self.assertEqual(body["redispatched_packet"]["packet_id"], "packet-1-redispatch-atlas-redispatch-1")

    def test_the_new_packet_is_real_and_durably_recorded(self):
        _status, body = _post(self.server.bound_port, "/command/redispatch-crash", self._envelope())
        new_packet_id = body["redispatched_packet"]["packet_id"]

        import sqlite3

        with sqlite3.connect(self.db.path / "maestro.sqlite3") as connection:
            row = connection.execute(
                "SELECT state, correction_count, work_item_id, run_id FROM packets WHERE packet_id = ?",
                (new_packet_id,),
            ).fetchone()
        self.assertEqual(row[0], "Planned")
        self.assertEqual(row[1], 0)
        self.assertEqual(row[2], "work-1")
        self.assertEqual(row[3], "run-1")

    def test_the_old_packet_is_really_cancelled(self):
        _status, _body = _post(self.server.bound_port, "/command/redispatch-crash", self._envelope())

        import sqlite3

        with sqlite3.connect(self.db.path / "maestro.sqlite3") as connection:
            row = connection.execute(
                "SELECT state FROM packets WHERE packet_id = 'packet-1'"
            ).fetchone()
        self.assertEqual(row[0], "Cancelled")

    def test_a_stale_expected_version_is_rejected_and_creates_no_new_packet(self):
        status, body = _post(
            self.server.bound_port, "/command/redispatch-crash", self._envelope(expected_version=99)
        )
        self.assertEqual(status, 409)
        self.assertEqual(body["error"], "stale_state")

        import sqlite3

        with sqlite3.connect(self.db.path / "maestro.sqlite3") as connection:
            count = connection.execute(
                "SELECT COUNT(*) FROM packets WHERE packet_id != 'packet-1'"
            ).fetchone()[0]
        self.assertEqual(count, 0)

    def test_an_unknown_packet_id_is_rejected(self):
        status, body = _post(
            self.server.bound_port,
            "/command/redispatch-crash",
            self._envelope(packet_id="does-not-exist"),
        )
        self.assertEqual(status, 400)
        self.assertEqual(body["error"], "invalid_command")

    def test_repeating_the_same_idempotency_key_replays_the_same_real_result(self):
        status1, body1 = _post(self.server.bound_port, "/command/redispatch-crash", self._envelope())
        status2, body2 = _post(self.server.bound_port, "/command/redispatch-crash", self._envelope())
        self.assertEqual(status1, 200)
        self.assertEqual(status2, 200)
        self.assertEqual(body1, body2)


if __name__ == "__main__":
    unittest.main()
