"""Pause, resume, graceful stop and manual retry, with a real local Git remote and scripted agents.
Real agents, GitHub, restarts and the installed path are proven in var/qa/lifecycle-live."""
from __future__ import annotations

import json
import unittest
from types import SimpleNamespace

from maestro.service.registry import OperationResult
from maestro.service.requests import RequestRejection

from test_execution_integration import IntegrationBase
from test_execution_milestones import MilestoneDestination


class LifecycleBase(IntegrationBase):
    def setUp(self) -> None:
        super().setUp()
        self.dest = MilestoneDestination(self.bare)
        self.service._destination = lambda profile: self.dest
        self.n = 0

    def version(self) -> int:
        return int(self.service._read("SELECT version FROM entity_versions WHERE entity_id = 'exec-1'")["version"])

    def act(self, operation, payload=None, version=None):
        self.n += 1
        request = SimpleNamespace(request_id=f"r{self.n}", operation=operation, project_id="proj", activity_id="exec-1", expected_version=version if version is not None else self.version(), question_id=None, payload=payload or {})
        handler = next(h for h in self.service.operation_handlers if h.operation == operation)
        prepared = handler.validate(request)
        with self.database.transaction() as tx:
            return prepared.apply(tx, request.expected_version + 1)

    def state(self) -> str:
        return self.row()["state"]

    def settlement(self):
        return json.loads(self.row()["pending_json"] or "{}").get("settlement")

    def set_state(self, key, state):
        with self.database.transaction() as tx:
            tx.execute("UPDATE service_execution_packets SET state = ? WHERE packet_key = ?", (state, key))


class PauseAndStopTests(LifecycleBase):
    def test_pause_saves_the_exact_set_refuses_new_starts_and_pauses_only_after_the_set_settles(self) -> None:
        self.add_packet("run", "m1", None, state="coding")
        self.add_packet("wait", "m2", None, state="pending")
        result = self.act("execution.pause")
        self.assertIsInstance(result, OperationResult)
        settlement = self.settlement()
        self.assertEqual((settlement["kind"], settlement["members"]["packets"]), ("pause", ["run"]))
        self.assertEqual(self.state(), "running", "not paused while a member is still running")
        self.assertIn("wait", self.service._held_packets("exec-1"))
        self.assertFalse(self.service._needs_planning(self.row(), json.loads(self.row()["pending_json"])), "no planning pass can reserve work")
        self.tick()
        self.assertEqual(self.state(), "running")
        self.assertIn("run", self.service.view("exec-1")["lifecycle"]["settlement"]["waiting_on"][0])
        with self.assertRaises(RequestRejection) as caught:
            self.act("execution.pause")
        self.assertEqual(caught.exception.code, "not_allowed")
        self.set_state("run", "failed")  # a known failure is an explicit unfinished result, not an uncertain one
        self.tick()
        self.assertEqual(self.state(), "paused")
        self.assertEqual(self.service.view("exec-1")["state"], "paused")
        self.assertEqual(self.packet("wait")["state"], "pending", "unstarted work is kept, not started")

    def test_a_stale_or_wrong_state_action_changes_nothing_and_resume_restores_normal_starts(self) -> None:
        self.add_packet("run", "m1", None, state="failed")
        with self.assertRaises(RequestRejection) as caught:
            self.act("execution.resume")
        self.assertEqual(caught.exception.code, "not_allowed")
        stale = self.version()
        self.act("execution.pause")
        self.tick()
        self.assertEqual(self.state(), "paused")
        with self.assertRaises(RequestRejection) as caught:
            self.act("execution.stop", version=stale)
        self.assertEqual(caught.exception.code, "stale_version")
        self.assertEqual(self.state(), "paused")
        self.act("execution.resume")
        self.assertEqual((self.state(), self.settlement()), ("running", None))
        self.add_packet("later", "m2", None, state="pending")
        self.assertNotIn("later", self.service._held_packets("exec-1"))

    def test_a_queue_entry_outside_the_set_holds_its_place_and_nothing_behind_it_is_skipped(self) -> None:
        h1 = self.packet_branch("p1", {"app/a.py": "one = 10\ntwo = 2\nthree = 3\n"})
        self.add_packet("p1", "m1", h1)  # approved, queued first, but not running when the pause is accepted
        with self.database.transaction() as tx:
            self.service._enqueue(tx, self.row(), "packet", "p1", None, "m1", h1)
        self.add_packet("p2", "m1", None, state="coding")
        self.act("execution.pause")
        self.assertEqual(self.settlement()["members"]["packets"], ["p2"])
        h2 = self.packet_branch("p2", {"app/b.py": "b = 5\n"})
        with self.database.transaction() as tx:
            tx.execute("UPDATE service_execution_packets SET state = 'approved', head_commit = ? WHERE packet_key = 'p2'", (h2,))
            tx.execute("INSERT INTO service_execution_reviews(activity_id, packet_key, review_round, assignment_id, run_id, reviewer_tool, reviewer_model, author_tool, author_model, reviewed_base, reviewed_head, outcome, summary, findings_json, independence, created_at) "
                       "VALUES ('exec-1', 'p2', 1, 'x', 'x', 'claude_code', 'r', 'qwen', 'q', ?, ?, 'APPROVE', 's', '[]', 'i', 't')", (self.base, h2))
        self.tick()
        self.tick()
        self.assertEqual([(e["packet_key"], e["state"]) for e in self.service._queue("exec-1")], [("p1", "queued"), ("p2", "queued")], "the head is held, so the later member is blocked rather than skipped to")
        self.assertEqual(self.runs.runs, {}, "no integration run started for either entry")
        self.assertEqual(self.state(), "paused", "the held entries are settled, unfinished work")
        self.act("execution.resume")
        self.tick()
        self.assertEqual(self.service._queue("exec-1")[0]["state"], "integrating", "after resume the first entry proceeds in order")

    def test_stop_settles_then_publishes_a_verified_stopped_record_and_frees_the_project(self) -> None:
        self.add_packet("run", "m1", None, state="coding")
        self.add_packet("wait", "m2", None, state="pending")
        self.act("execution.stop")
        self.assertEqual(self.state(), "finishing")
        self.tick()
        self.assertEqual(self.state(), "finishing", "a running member keeps the stop open")
        with self.assertRaises(RequestRejection):
            self.act("execution.stop")
        before = self.dest.branch_head("o/r", "main")
        self.set_state("run", "failed")
        self.tick()
        self.assertEqual(self.state(), "stopped")
        stored = self.service._read("SELECT * FROM service_execution_completion WHERE activity_id = 'exec-1'")
        record = json.loads(stored["record_json"])
        self.assertEqual((record["kind"], record["record"]), ("stopped", "execution-stop@1"))
        self.assertEqual({p["key"] for p in record["unfinished"]["packets"]}, {"run", "wait"})
        self.assertEqual({m["id"] for m in record["unfinished"]["milestones"]}, {"m1", "m2", "m3"})
        self.assertEqual(record["completed_milestones"], [])
        on_remote = self.dest.read_file("o/r", self.dest.branch_head("o/r", "main"), stored["path"])
        self.assertEqual(json.loads(on_remote)["kind"], "stopped")
        self.assertNotEqual(before, self.dest.branch_head("o/r", "main"))
        self.assertTrue(stored["path"].endswith("/stop/versions/1/stop.json"))
        view = self.service.view("exec-1")
        self.assertEqual(view["lifecycle"]["stopped_closure"]["delivery"], record["delivery"])
        self.assertIn("not delivered", view["lifecycle"]["stopped_closure"]["delivery"])
        activity = self.service._read("SELECT state, waiting_reason FROM service_activities WHERE activity_id = 'exec-1'")
        self.assertEqual(activity["state"], "stopped")
        self.assertIn("stopped, not completed", activity["waiting_reason"])
        self.assertIsNone(self.service._open_activity("proj"))
        self.tick()  # a repeated pass publishes nothing more
        self.assertEqual(len(self.service._rows("SELECT * FROM service_execution_journal WHERE kind = 'execution_stop_publish'")), 1)

    def test_a_stopped_paused_execution_needs_no_settling_and_a_moved_product_branch_waits(self) -> None:
        self.add_packet("wait", "m1", None, state="pending")
        self.act("execution.pause")
        self.tick()
        self.assertEqual(self.state(), "paused")
        self.act("execution.stop")
        self.assertEqual(self.state(), "finishing")
        self.tick()
        self.assertEqual(self.state(), "stopped")


class ManualRetryTests(LifecycleBase):
    def failed_packet(self):
        self.add_packet("pf", "m1", None, state="failed")
        pending = {"coder_run": {"assignment_id": "a-code-1", "run_id": "a-code-1-run1"}}
        with self.database.transaction() as tx:
            tx.execute("UPDATE service_execution_packets SET pending_json = ? WHERE packet_key = 'pf'", (json.dumps(pending),))
        self.runs.assignments["a-code-1"] = {"state": "paused", "automatic_limit": 2, "automatic_used": 2}

    def _decide(self, choice, **extra):
        self.n += 1
        request = SimpleNamespace(request_id=f"d{self.n}", operation="owner.decision", project_id="proj", activity_id="exec-1", expected_version=self.version(), question_id=None,
                                  payload={"target": "execution_manual_retry", "choice": choice, "assignment_id": "pf", **extra})
        prepared = self.service.prepare_owner_decision(request)
        with self.database.transaction() as tx:
            return prepared.apply(tx, request.expected_version + 1)

    def grants(self):
        return json.loads(self.packet("pf")["pending_json"]).get("manual_grants", [])

    def test_a_grant_is_typed_limited_to_the_configured_maximum_and_reserved_once(self) -> None:
        self.failed_packet()
        with self.assertRaises(RequestRejection):
            self.act("execution.retry", {"packet_key": "pf", "grant_id": "nope", "intervention": "fixed the route"})
        result = self._decide("grant_one", duration_seconds=900)
        grant_id = result.data["grant_id"]
        self.assertEqual([(g["state"], g["duration_seconds"]) for g in self.grants()], [("unconsumed", 900)])
        with self.assertRaises(RequestRejection) as caught:
            self._decide("grant_one")
        self.assertEqual(caught.exception.code, "grant_open")
        with self.assertRaises(ValueError):
            self.act("execution.retry", {"packet_key": "pf", "grant_id": grant_id, "intervention": " "})
        result = self.act("execution.retry", {"packet_key": "pf", "grant_id": grant_id, "intervention": "raised the timeout"})
        self.assertEqual((result.data["stage"], self.packet("pf")["state"]), ("coder", "reserved"))
        self.assertEqual(self.grants()[0]["state"], "reserved")
        with self.assertRaises(RequestRejection):
            self.act("execution.retry", {"packet_key": "pf", "grant_id": grant_id, "intervention": "again"})

    def test_a_launch_consumes_the_grant_and_a_failed_preflight_releases_it_and_the_maximum_still_holds(self) -> None:
        self.failed_packet()
        grant_id = self._decide("grant_one").data["grant_id"]
        self.act("execution.retry", {"packet_key": "pf", "grant_id": grant_id, "intervention": "raised the timeout"})
        self.runs.set_next_run_duration = lambda assignment_id, seconds: None
        row, packet = self.row(), self.packet("pf")
        pending = json.loads(packet["pending_json"])

        def refuse(note):
            raise AgentRunError("route_unavailable", "no route")

        from maestro.service.agent_runs import AgentRunError
        with self.assertRaises(AgentRunError):
            self.service._manual_launch(row, packet, pending, "coder_run", "a-code-1", refuse)
        self.assertEqual(self.grants()[0]["state"], "unconsumed", "no run was created, so the grant is released")
        self.assertIsNone(json.loads(self.packet("pf")["pending_json"]).get("manual_retry"))
        self.set_state("pf", "failed")
        self.act("execution.retry", {"packet_key": "pf", "grant_id": grant_id, "intervention": "second try"})
        pending = json.loads(self.packet("pf")["pending_json"])
        self.service._manual_launch(row, self.packet("pf"), pending, "coder_run", "a-code-1", lambda note: "a-code-1-run2")
        self.assertEqual((pending["manual_grants"][0]["state"], pending["manual_grants"][0]["run_id"]), ("consumed", "a-code-1-run2"))
        self.service._save_packet("exec-1", "pf", pending)  # the launch step saves the packet's pending record with its next state
        self.set_state("pf", "failed")
        with self.assertRaises(RequestRejection) as caught:
            self._decide("grant_one")
        self.assertEqual(caught.exception.code, "manual_retry_limit")

    def test_remain_paused_records_the_choice_and_creates_no_grant(self) -> None:
        self.failed_packet()
        result = self._decide("remain_paused")
        self.assertIsNone(result.data["grant_id"])
        self.assertEqual(self.grants(), [])

    def test_a_packet_that_is_not_failed_has_no_retry_decision(self) -> None:
        self.add_packet("ok", "m1", None, state="pending")
        with self.assertRaises(RequestRejection):
            self.n += 1
            request = SimpleNamespace(request_id="x", project_id="proj", activity_id="exec-1", expected_version=self.version(), question_id=None,
                                      payload={"target": "execution_manual_retry", "choice": "grant_one", "assignment_id": "ok"})
            with self.database.transaction() as tx:
                self.service.prepare_owner_decision(request).apply(tx, 2)


if __name__ == "__main__":
    unittest.main()
