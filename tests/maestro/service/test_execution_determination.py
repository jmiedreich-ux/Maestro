"""Execution architectural determinations and the Owner's work disposition, with a real local Git remote and scripted agents.
Real agents and the installed path are proven in var/qa/architecture-gaps-live."""
from __future__ import annotations

import json
import unittest
from types import SimpleNamespace

from maestro.service import execution_config

from test_execution import config_table
from test_execution_support import SUPPORT, SupportBase


def determination(kind="within_confirmed_design", **over):
    body = {"result": "completed", "summary": "s", "questions": [], "determination": kind, "rationale": "because the confirmed design says so", "interpretation": "use the confirmed contract" if kind == "within_confirmed_design" else None,
            "minimum_correction": "fix the check" if kind == "implementation_defect" else None, "affected_work": ["pb"], "owner_recommendation": None,
            "disposition_recommendation": "finish_safe_work" if kind == "reregistration_required" else None, "supplement": None}
    body.update(over)
    return body


class DeterminationBase(SupportBase):
    def setUp(self) -> None:
        super().setUp()
        self.runs.stop_calls = []
        self.runs.stop = lambda run_id, reason="cancelled": (self.runs.stop_calls.append(run_id), self.runs.runs[run_id].update(state="cancelled"))[0]
        self.add_packet("dep", "m1", self.base, state="pending", deps=("pb",), paths=("app/dep",))
        self.add_packet("free", "m1", self.base, state="pending", paths=("app/free",))

    def det(self, key):
        return self.service._architect("exec-1", key)

    def ask(self, question="which storage contract applies?"):
        with self.database.transaction() as tx:
            self.assertIsNone(self.service._request_manager_question(tx, self.row(), self.packet("pb"), question))

    def answer(self, body):
        self.runs.finish(self.runs.last("determination_architect"), body)
        self.tick()

    def decide(self, target, choice, assignment_id):
        version = int(self.service._read("SELECT version FROM entity_versions WHERE entity_id = 'exec-1'")["version"])
        request = SimpleNamespace(request_id=f"r-{target}-{choice}-{assignment_id}", project_id="proj", activity_id="exec-1", expected_version=version, question_id=None,
                                  payload={"target": target, "choice": choice, "assignment_id": assignment_id})
        prepared = self.service.prepare_owner_decision(request)
        with self.database.transaction() as tx:
            return prepared.apply(tx, version + 1)


class QuestionTests(DeterminationBase):
    def test_a_saved_architectural_question_reaches_its_own_read_only_assignment_and_the_answer_returns_to_the_manager(self) -> None:
        self.ask()
        self.ask()  # the same question replays to the saved assignment
        self.assertEqual(len(self.service._architects("exec-1", "determination")), 1)
        self.assertIn("pb", self.service._held_packets("exec-1"))
        self.tick()
        assignment = self.runs.runs[self.runs.last("determination_architect")]["build"].assignment
        self.assertEqual(assignment.role, "determination_architect")
        self.assertEqual(assignment.permitted_actions, ("read_source",))
        self.assertEqual(self.runs.assignments[assignment.assignment_id]["tool"], "claude_code")
        self.answer(determination("within_confirmed_design"))
        self.assertEqual(self.det("det-q1")["state"], "decided")
        self.assertNotIn("pb", self.service._held_packets("exec-1"))
        events = self.service._rows("SELECT kind, detail, handled FROM service_execution_events WHERE kind = 'determination_ready'")
        self.assertEqual(len(events), 1)
        self.assertIn("within_confirmed_design", events[0]["detail"])
        self.assertEqual(self.packet("pb")["record_sha256"], "h", "no confirmed record changed")

    def test_a_supplement_or_an_unlisted_packet_or_a_stray_recommendation_is_sent_back(self) -> None:
        self.ask()
        self.tick()
        self.answer(determination("within_confirmed_design", owner_recommendation="grant_one"))
        self.assertIn("must be null", self.runs.rejected[-1])
        self.tick()
        self.answer(determination("within_confirmed_design", affected_work=["nope"]))
        self.assertIn("not in this Execution", self.runs.rejected[-1])

    def test_the_gap_route_falls_back_to_the_support_architect_and_a_missing_configuration_blocks_with_a_reason(self) -> None:
        self.ask()
        self.tick()
        self.assertIn("architectural_support", json.loads(self.det("det-q1")["config_json"]) and "architectural_support")
        self.assertIn("is not configured", self.det("det-q1")["note"])
        config = execution_config.validate(config_table())
        with self.database.transaction() as tx:
            tx.execute("UPDATE service_executions SET config_json = ? WHERE activity_id = 'exec-1'", (json.dumps(config),))
        self.ask("another question?")
        self.assertEqual(self.det("det-q2")["state"], "blocked_route")
        self.assertIn("no architect route", self.det("det-q2")["note"])
        self.assertIn("pb", self.service._held_packets("exec-1"))


class LimitTests(DeterminationBase):
    def exhaust_packet_review(self):
        limit = {"assignment_id": "a-run-2", "round": 2}
        with self.database.transaction() as tx:
            tx.execute("UPDATE service_execution_packets SET state = 'limit_paused', rounds_used = 2, pending_json = ? WHERE packet_key = 'pb'", (json.dumps({"limit": limit}),))
            for i in (1, 2):
                tx.execute("INSERT INTO service_execution_reviews(activity_id, packet_key, review_round, assignment_id, run_id, reviewer_tool, reviewer_model, author_tool, author_model, reviewed_base, reviewed_head, outcome, summary, findings_json, independence, created_at) "
                           "VALUES ('exec-1', 'pb', ?, 'x', 'x', 'claude_code', 'r', 'qwen', 'q', 'b', 'h', 'REQUEST_CHANGES', 's', ?, 'i', 't')", (i, json.dumps([{"local_key": "f", "subject": "S", "severity": "blocking", "explanation": "e", "impact": "i", "requested_correction": "c", "locations": []}])))

    def test_an_exhausted_review_limit_needs_the_saved_recommendation_before_the_owner_can_grant(self) -> None:
        self.exhaust_packet_review()
        self.tick()
        self.tick()  # a repeated step reuses the one saved assignment
        self.assertEqual([a["assignment_key"] for a in self.service._architects("exec-1", "determination")], ["det-a-run-2"])
        inputs = self.runs.runs[self.runs.last("determination_architect")]["build"].inputs if hasattr(self.runs.runs[self.runs.last("determination_architect")]["build"], "inputs") else None
        with self.assertRaises(Exception) as caught:
            self.decide("packet_review", "grant_one", "a-run-2")
        self.assertIn("recommendation", str(caught.exception))
        self.answer(determination("implementation_defect", owner_recommendation=None))
        self.assertIn("exhausted review limit", self.runs.rejected[-1])
        self.tick()
        self.answer(determination("implementation_defect", owner_recommendation="grant_one"))
        self.assertEqual(self.det("det-a-run-2")["state"], "decided")
        decision = self.service.view("exec-1")["owner_decisions"][0]
        self.assertEqual((decision["target"], decision["recommendation"], decision["determination"]), ("packet_review", "grant_one", "implementation_defect"))
        self.decide("packet_review", "grant_one", "a-run-2")
        self.assertEqual(self.packet("pb")["state"], "reserved")
        self.assertEqual(self.packet("pb")["rounds_used"], 2, "the grant changes no count; the base limit stays")
        del inputs


class DispositionTests(DeterminationBase):
    def to_disposition(self):
        self.ask()
        self.tick()
        self.answer(determination("reregistration_required", affected_work=["pb"]))
        self.assertEqual(self.det("det-q1")["state"], "awaiting_disposition")

    def test_reregistration_holds_the_affected_work_and_the_owner_chooses_the_disposition(self) -> None:
        self.to_disposition()
        held = self.service._held_packets("exec-1")
        self.assertIn("pb", held)
        self.assertNotIn("free", held)
        view = self.service.view("exec-1")
        decision = next(d for d in view["owner_decisions"] if d["target"] == "execution_work_disposition")
        self.assertEqual((decision["recommendation"], decision["assignment_id"]), ("finish_safe_work", "det-q1"))
        self.assertIn("respond_to_owner_decision", view["actions"])
        # free text is not a choice
        with self.assertRaises(ValueError):
            self.decide("execution_work_disposition", "please just carry on", "det-q1")
        self.decide("execution_work_disposition", "continue_unaffected", "det-q1")
        held = self.service._held_packets("exec-1")
        self.assertEqual(sorted(held), ["dep", "pb"], "the affected packet and its dependant stay blocked; unrelated work continues")
        self.assertEqual(self.service.view("exec-1")["disposition"]["choice"], "continue_unaffected")
        self.assertEqual(self.row()["state"], "running", "choosing a disposition does not end the Execution or start re-registration")
        with self.assertRaises(Exception):
            self.decide("execution_work_disposition", "continue_unaffected", "det-q1")  # a replay by a new request finds nothing pending

    def test_finishing_current_work_stops_all_new_starts_and_ends_only_when_everything_has_settled(self) -> None:
        with self.database.transaction() as tx:
            tx.execute("UPDATE service_execution_packets SET state = 'coding' WHERE packet_key = 'free'")
        self.to_disposition()
        self.decide("execution_work_disposition", "finish_current_for_replanning", "det-q1")
        held = self.service._held_packets("exec-1")
        self.assertEqual(sorted(held), ["dep", "pb"], "every pending packet is held; the running one is not touched")
        self.tick()
        self.assertEqual(self.row()["state"], "running", "a packet is still running, so the Execution has not settled")
        with self.database.transaction() as tx:
            tx.execute("UPDATE service_execution_packets SET state = 'integrated' WHERE packet_key = 'free'")
        self.tick()
        row = self.row()
        self.assertEqual(row["state"], "ended_for_replanning")
        self.assertEqual(self.service._read("SELECT state FROM service_activities WHERE activity_id = 'exec-1'")["state"], "completed")
        self.assertIsNone(self.service.reservations.held("proj"), "the project reservation is released for re-registration")
        self.assertEqual(self.packet("pb")["state"], "pending", "unstarted work stays unfinished, never marked complete")
        self.assertIn("ready for re-registration", self.service._read("SELECT waiting_reason FROM service_activities WHERE activity_id = 'exec-1'")["waiting_reason"])

    def test_stopping_affected_running_work_stops_its_runs_then_the_execution_settles(self) -> None:
        self.runs.runs["r-coder"] = {"assignment": "a", "build": None, "output": None, "state": "running", "response": None}
        with self.database.transaction() as tx:
            tx.execute("UPDATE service_execution_packets SET state = 'coding', pending_json = ? WHERE packet_key = 'pb'", (json.dumps({"coder_run": {"assignment_id": "a", "run_id": "r-coder"}}),))
        self.to_disposition()
        self.decide("execution_work_disposition", "stop_affected_or_all", "det-q1")
        self.tick()
        self.assertEqual(self.runs.stop_calls, ["r-coder"])
        self.tick()
        self.assertEqual(self.packet("pb")["state"], "failed")
        self.assertIn("work disposition", self.packet("pb")["note"])
        self.tick()
        self.assertEqual(self.row()["state"], "ended_for_replanning")


if __name__ == "__main__":
    unittest.main()
