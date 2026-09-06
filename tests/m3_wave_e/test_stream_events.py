from __future__ import annotations

import http.client
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "m2_wave_a"))

from test_events_snapshot import _RuntimeFixture, _insert_modern_event  # noqa: E402

from maestro import read_api  # noqa: E402


def _open_stream(port: int, path: str, *, last_event_id: str | None = None) -> http.client.HTTPResponse:
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    headers = {}
    if last_event_id is not None:
        headers["Last-Event-ID"] = last_event_id
    connection.request("GET", path, headers=headers)
    return connection.getresponse()


def _read_frames(response: http.client.HTTPResponse, count: int, *, max_bytes: int = 65536) -> list[str]:
    """Read raw bytes until `count` complete SSE frames (ending in \\n\\n) are seen."""
    buffer = b""
    frames: list[str] = []
    while len(frames) < count and len(buffer) < max_bytes:
        chunk = response.fp.read1(4096) if hasattr(response.fp, "read1") else response.fp.read(4096)
        if not chunk:
            break
        buffer += chunk
        while b"\n\n" in buffer:
            raw, buffer = buffer.split(b"\n\n", 1)
            frames.append(raw.decode("utf-8"))
    return frames


class StreamEventsTests(unittest.TestCase):
    def setUp(self):
        self.fixture = _RuntimeFixture()
        self.server = read_api.ReadApiServer(
            read_api.ReadApiConfig(port=0, runtime_dir=self.fixture.runtime_dir)
        )
        self.server.start()

    def tearDown(self):
        self.server.stop()
        self.fixture.close()

    def test_a_fresh_connection_with_no_after_only_sees_new_events_not_history(self):
        self.fixture.insert_modern_events(3, prefix="before")

        response = _open_stream(self.server.bound_port, "/stream/events")
        self.assertEqual(response.status, 200)
        self.assertEqual(response.getheader("Content-Type"), "text/event-stream")

        self.fixture.insert_modern_events(1, prefix="after")
        frames = _read_frames(response, 1)
        self.assertEqual(len(frames), 1)
        self.assertIn('"entity_id":"after-entity-000"', frames[0])
        response.close()

    def test_reconnecting_with_a_real_after_id_replays_the_real_gap(self):
        ids = self.fixture.insert_modern_events(2, prefix="seed")

        response = _open_stream(self.server.bound_port, f"/stream/events?after={ids[0]}")
        self.assertEqual(response.status, 200)
        frames = _read_frames(response, 1)
        self.assertEqual(len(frames), 1)
        self.assertIn('"entity_id":"seed-entity-001"', frames[0])
        self.assertIn(f"id: {ids[1]}", frames[0])
        response.close()

    def test_last_event_id_header_is_honored_the_same_as_the_query_param(self):
        ids = self.fixture.insert_modern_events(2, prefix="header")

        response = _open_stream(self.server.bound_port, "/stream/events", last_event_id=str(ids[0]))
        self.assertEqual(response.status, 200)
        frames = _read_frames(response, 1)
        self.assertEqual(len(frames), 1)
        self.assertIn('"entity_id":"header-entity-001"', frames[0])
        response.close()

    def test_a_last_seen_id_that_no_longer_resolves_gets_a_real_resync_signal(self):
        response = _open_stream(self.server.bound_port, "/stream/events?after=999999")
        self.assertEqual(response.status, 200)
        frames = _read_frames(response, 1)
        self.assertEqual(len(frames), 1)
        self.assertIn("event: resync", frames[0])
        self.assertIn('"resync_required":true', frames[0])
        response.close()

    def test_after_zero_replays_every_real_event_from_the_start(self):
        self.fixture.insert_modern_events(2, prefix="fromzero")

        response = _open_stream(self.server.bound_port, "/stream/events?after=0")
        self.assertEqual(response.status, 200)
        frames = _read_frames(response, 2)
        self.assertEqual(len(frames), 2)
        self.assertIn('"entity_id":"fromzero-entity-000"', frames[0])
        self.assertIn('"entity_id":"fromzero-entity-001"', frames[1])
        response.close()

    def test_multiple_after_params_are_rejected(self):
        status, _content_type, body = _get_error(self.server.bound_port, "/stream/events?after=1&after=2")
        self.assertEqual(status, 400)
        self.assertIn(b"invalid_query", body)

    def test_a_non_numeric_after_is_rejected(self):
        status, _content_type, body = _get_error(self.server.bound_port, "/stream/events?after=abc")
        self.assertEqual(status, 400)
        self.assertIn(b"invalid_query", body)

    def test_an_unknown_query_key_is_rejected(self):
        status, _content_type, body = _get_error(self.server.bound_port, "/stream/events?since=1")
        self.assertEqual(status, 400)
        self.assertIn(b"invalid_query", body)


def _get_error(port: int, path: str) -> tuple[int, str | None, bytes]:
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    try:
        connection.request("GET", path)
        response = connection.getresponse()
        body = response.read()
        return response.status, response.getheader("Content-Type"), body
    finally:
        connection.close()


if __name__ == "__main__":
    unittest.main()
