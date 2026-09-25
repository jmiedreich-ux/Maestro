"""Execution architectural determinations and the Owner's work disposition.

A saved architectural question from the Development Manager, or blocking findings at a packet or integration review
limit, start one read-only Project Architect assignment. It answers within the confirmed design, points to an
implementation defect, or says the work needs re-registration; at a limit it also gives the Owner a recommendation
that grants nothing. The Owner's typed choice is applied only after that recommendation is saved. A re-registration
determination leads to the Owner's work disposition, which the service saves with the activity and enforces on new
starts. Nothing here dispatches code, approves work, grants an allowance or starts re-registration.
"""

from __future__ import annotations

import json
from typing import Any, Mapping

from maestro.agents.execution_contract import DETERMINATION_SCHEMA, DISPOSITION_CHOICES
from maestro.agents.transport import AgentAssignment
from maestro.foundation import canonical_json

from .agent_runs import AgentRunError, RunBuild

_DET_OPEN = ("requested", "determining")
_DISPOSITION_ENDS = ("finish_safe_work", "stop_affected_or_all", "finish_current_for_replanning")
_PACKET_RUNNING = ("reserved", "coding", "correcting", "reviewing", "publishing", "review_ready")


def _now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _dump(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _json(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


_DETERMINATION_TASK = """You are the Maestro Project Architect making one bounded architectural determination for a project's Execution. You are not the architecture loop and you do not restart it. You cannot publish a supplement, dispatch code, approve work, grant an allowance, change scope or start re-registration. Work only from this assignment, the files under input/ and the read-only source/ clone.

1. Read input/request.json (what triggered this: {trigger}), input/packets.json (the affected packets), input/review-evidence.json (earlier review rounds and their blocking findings, when any), input/limits.json (the base limit, completed rounds, grants and remaining allowances), input/integration.json (queue and dependency state) and input/execution.json. Read source/ where you need to verify facts.
2. Choose exactly one determination. within_confirmed_design: the confirmed architecture already answers it; put your interpretation in `interpretation` (it cannot change a confirmed outcome, packet, responsibility or dependency). implementation_defect: the design is right and the code is wrong; put the smallest correction for the original author in `minimum_correction`. reregistration_required: satisfying it would change scope, established responsibilities, dependencies or the confirmed breakdown; list the affected packet keys in `affected_work` and recommend a work disposition in `disposition_recommendation` (continue_unaffected, finish_safe_work, stop_affected_or_all or finish_current_for_replanning).
3. {owner_line}
4. Always give a plain rationale and the affected packet keys in `affected_work`. `supplement` must be null. result is completed.
Copy contract_version (1), assignment_id, run_id, session_id, project_id, activity_id, role, source_commit and decision_version exactly from assignment.json. Return only the structured response."""

_OWNER_LIMIT = "A review allowance is exhausted. Set owner_recommendation to grant_one (one more attempt is likely to resolve the blocking findings) or remain_paused (another attempt is unlikely to help, or the findings need a different path). Your recommendation grants nothing."
_OWNER_NONE = "No allowance is exhausted, so owner_recommendation must be null."


class DeterminationMixin:
    """Architectural determinations and work disposition of ``ExecutionService``."""

    # ------------------------------------------------------------- triggers

    def _gap_config(self, row: Mapping[str, Any]) -> tuple[dict[str, Any] | None, str | None]:
        """The determination assignment's route snapshot: execution.milestone_gap_architect, else the support architect's route (recorded)."""
        config = json.loads(row["config_json"])
        if config.get("milestone_gap_architect"):
            return {"architect": config["milestone_gap_architect"]}, None
        support = config.get("architectural_support")
        if support:
            return {"architect": support["architect"]}, "execution.milestone_gap_architect is not configured; the architectural_support architect route is used"
        return None, "neither execution.milestone_gap_architect nor execution.architectural_support is configured, so no architect route exists"

    def _request_determination(self, tx: Any, row: Mapping[str, Any], key: str, packet_key: str | None, subject: str, trigger: Mapping[str, Any]) -> str | None:
        """Save one determination assignment (the same trigger replays to the saved one); return a rejection reason when it cannot be created."""
        activity_id = row["activity_id"]
        if self._row(tx, "SELECT 1 AS n FROM service_execution_architect WHERE activity_id = ? AND assignment_key = ?", (activity_id, key)) is not None:
            return None
        config, note = self._gap_config(row)
        state = "requested" if config else "blocked_route"
        now = _now()
        tx.execute(
            "INSERT INTO service_execution_architect(activity_id, assignment_key, kind, packet_key, subject, trigger_json, state, version, config_json, pending_json, review_limit, note, created_at, updated_at) "
            "VALUES (?, ?, 'determination', ?, ?, ?, ?, 1, ?, '{}', 0, ?, ?, ?)",
            (activity_id, key, packet_key, subject[:200], canonical_json(trigger), state, canonical_json(config or {}), note, now, now),
        )
        self._say(tx, row["project_id"], activity_id, f"Architectural determination {key} recorded for {packet_key or 'the Execution'}: {subject[:300]}." + ("" if config else f" {note}."))
        return None

    def _detect_limits(self, row: Mapping[str, Any]) -> None:
        """An exhausted packet or integration review limit needs its architect recommendation before the Owner can decide."""
        activity_id = row["activity_id"]
        with self.database.transaction() as tx:
            for packet in self._row_list(tx, "SELECT * FROM service_execution_packets WHERE activity_id = ? AND state = 'limit_paused'", (activity_id,)):
                limit = json.loads(packet["pending_json"] or "{}").get("limit")
                if limit:
                    self._request_determination(tx, row, f"det-{limit['assignment_id']}", packet["packet_key"], f"packet review limit reached for {packet['packet_key']}",
                                                {"source": "packet_review_limit", "packet_key": packet["packet_key"], "assignment_id": limit["assignment_id"], "round": limit["round"], "exhausted": True})
            for entry in self._row_list(tx, "SELECT * FROM service_execution_queue WHERE activity_id = ? AND state = 'limit_paused'", (activity_id,)):
                limit = json.loads(entry["pending_json"] or "{}").get("limit")
                if limit:
                    self._request_determination(tx, row, f"det-{limit['assignment_id']}", entry["packet_key"], f"integration review limit reached for queue entry {entry['entry_id']}",
                                                {"source": "integration_review_limit", "entry_id": entry["entry_id"], "packet_key": entry["packet_key"], "assignment_id": limit["assignment_id"], "round": limit["round"], "exhausted": True})

    def _determination_numbers(self, tx: Any, activity_id: str) -> int:
        return 1 + int(self._row(tx, "SELECT COUNT(*) AS n FROM service_execution_architect WHERE activity_id = ? AND kind = 'determination'", (activity_id,))["n"])

    def _request_manager_question(self, tx: Any, row: Mapping[str, Any], packet: Mapping[str, Any] | None, question: str) -> str | None:
        if packet is None:
            return "no such packet in this Execution"
        activity_id = row["activity_id"]
        for existing in self._row_list(tx, "SELECT * FROM service_execution_architect WHERE activity_id = ? AND kind = 'determination' AND packet_key = ?", (activity_id, packet["packet_key"])):
            if json.loads(existing["trigger_json"]).get("question") == question[:2000] and existing["state"] not in ("blocked_route",):
                return None
        key = f"det-q{self._determination_numbers(tx, activity_id)}"
        return self._request_determination(tx, row, key, packet["packet_key"], f"architectural question on {packet['packet_key']}",
                                           {"source": "manager_question", "packet_key": packet["packet_key"], "question": question[:2000], "exhausted": False})

    def _held_by_determination(self, activity_id: str) -> dict[str, str]:
        held: dict[str, str] = {}
        for arch in self._architects(activity_id):
            if arch["kind"] == "support":
                continue
            trigger = json.loads(arch["trigger_json"])
            if trigger.get("source") == "manager_question" and arch["state"] in (*_DET_OPEN, "blocked_route") and arch["packet_key"]:
                held[str(arch["packet_key"])] = f"architectural determination {arch['assignment_key']} is {arch['state']}: {arch['note'] or 'the packet waits for the architect'}"
            elif arch["state"] == "awaiting_disposition":
                for key in json.loads(arch["result_json"] or "{}").get("affected_work", []):
                    held[str(key)] = f"work disposition for {arch['assignment_key']} is awaiting the Owner: re-registration is required for this work"
        return held

    def _held_by_disposition(self, row: Mapping[str, Any]) -> dict[str, str]:
        disposition = json.loads(row["pending_json"] or "{}").get("disposition")
        if not disposition:
            return {}
        packets = self._packets(row["activity_id"])
        held: dict[str, str] = {}
        if disposition["choice"] == "continue_unaffected":
            affected = set(disposition["affected"])
            grew = True
            while grew:
                grew = False
                for p in packets:
                    if p["packet_key"] not in affected and any(d in affected for d in json.loads(p["dependency_keys_json"])):
                        affected.add(p["packet_key"])
                        grew = True
            reason = "the Owner chose to continue unaffected work; this packet is affected by the architectural issue or depends on affected work"
            return {k: reason for k in affected}
        reason = "the Owner chose to stop new starts before re-registration"
        return {p["packet_key"]: reason for p in packets if p["state"] == "pending"}

    # ------------------------------------------------------------- advancing

    def _advance_determinations(self, row: Mapping[str, Any]) -> None:
        self._detect_limits(row)
        for arch in self._architects(row["activity_id"], "determination"):
            if arch["state"] in _DET_OPEN:
                try:
                    self._support_step(row, arch, "determination_run", self._determination_start, self._determination_accept)
                except AgentRunError as error:
                    self._support_block(row, arch, f"{error.code}: {error}")
        self._advance_disposition(row)

    def _determination_inputs(self, row: Mapping[str, Any], arch: Mapping[str, Any]) -> dict[str, bytes]:
        activity_id = row["activity_id"]
        trigger = json.loads(arch["trigger_json"])
        packet_key = trigger.get("packet_key")
        packets = [p for p in self._packets(activity_id) if p["packet_key"] == packet_key]
        listing = [{"key": p["packet_key"], "subject": p["subject"], "milestone": p["milestone_key"], "state": p["state"], "dependencies": json.loads(p["dependency_keys_json"]),
                    **{k: v for k, v in json.loads(p["record_json"]).items() if k in {"purpose", "permitted_paths", "completion_criteria", "essential_failure_checks", "required_outputs", "shared_code_constraints"}}} for p in packets]
        evidence: list[dict[str, Any]] = []
        limits: dict[str, Any] = {"exhausted": bool(trigger.get("exhausted"))}
        if trigger["source"] == "packet_review_limit" and packets:
            evidence = [{"round": r["review_round"], "outcome": r["outcome"], "summary": r["summary"], "findings": json.loads(r["findings_json"])} for r in
                        self._rows("SELECT * FROM service_execution_reviews WHERE activity_id = ? AND packet_key = ? ORDER BY review_round", (activity_id, packet_key))]
            pending = json.loads(packets[0]["pending_json"] or "{}")
            limits.update({"base_limit": packets[0]["round_limit"], "completed_rounds": packets[0]["rounds_used"], "grants": pending.get("grants", [])})
        elif trigger["source"] == "integration_review_limit":
            entry = self._entry(activity_id, int(trigger["entry_id"]))
            evidence = [{"attempt": r["attempt"], "round": r["review_round"], "outcome": r["outcome"], "summary": r["summary"], "findings": json.loads(r["findings_json"])} for r in
                        self._rows("SELECT * FROM service_execution_integration_reviews WHERE activity_id = ? AND entry_id = ? ORDER BY attempt, review_round", (activity_id, trigger["entry_id"]))]
            limits.update({"base_limit": entry["round_limit"], "completed_rounds": entry["rounds_used"], "grants": json.loads(entry["pending_json"] or "{}").get("grants", [])})
        limits["remaining_allowances"] = 0 if trigger.get("exhausted") else None
        return {
            "request.json": _json({"determination_id": arch["assignment_key"], **trigger}), "packets.json": _json(listing), "review-evidence.json": _json(evidence),
            "limits.json": _json(limits), "integration.json": _json(self._manager_integration(activity_id)),
            "execution.json": _json({"activity_id": activity_id, "source_commit": row["source_commit"], "repository": row["repository"], "confirmed_breakdown": {k: json.loads(row["confirmed_ref_json"])[k] for k in ("version", "commit", "manifest_path")}}),
        }

    def _determination_start(self, row: Mapping[str, Any], arch: dict[str, Any], recovery_note: str | None) -> None:
        assert self.runs is not None
        activity_id, key = row["activity_id"], arch["assignment_key"]
        route = self._support_route(arch, "architect")
        pending = json.loads(self._architect(activity_id, key)["pending_json"])
        trigger = json.loads(arch["trigger_json"])
        description = {"manager_question": "a saved architectural question from the Development Manager", "packet_review_limit": "blocking findings at a packet review limit",
                       "integration_review_limit": "blocking findings at an integration review limit"}[trigger["source"]]
        assignment_id = f"{activity_id}-{key}-architect"
        note = "" if not recovery_note else f"\nThe previous run's output was rejected: {recovery_note}. Fix exactly that."
        task = _DETERMINATION_TASK.format(trigger=description, owner_line=_OWNER_LIMIT if trigger.get("exhausted") else _OWNER_NONE) + note
        inputs = self._determination_inputs(row, arch)
        mirror = self._mirror(row["project_id"])

        def build(run_id: str) -> RunBuild:
            assignment = AgentAssignment(
                project_id=row["project_id"], activity_id=activity_id, assignment_id=assignment_id, run_id=run_id, parent_assignment_id=None, role="determination_architect",
                role_responsibilities=("Answer within the confirmed design, name an implementation defect or require re-registration; never publish, dispatch, approve or grant.",),
                task=task, source_commit=row["source_commit"], decision_version=f"{key}",
                instructions={"session_id": run_id, "claude_tools": ["Read", "Glob", "Grep"], "task_kind": "architectural_determination", "determination": key},
                permitted_actions=("read_source",), writable_locations=("output", "scratch"), limits={"run_timeout_seconds": route["run_timeout_seconds"]},
                clarification_conditions=("Missing information changes the determination.",), response_schema=DETERMINATION_SCHEMA, contract="execution",
            )
            return RunBuild(assignment, mirror, inputs, None)

        self._launch(row, pending, "determination_run", assignment_id, route["tool"], route["model"], route["run_timeout_seconds"], recovery_note is not None, build, "determination_architect",
                     save=lambda _a, p: self._save_architect(activity_id, key, p))
        pending["architect"] = {"tool": route["tool"], "model": route["model"]}
        with self.database.transaction() as tx:
            tx.execute("UPDATE service_execution_architect SET state = 'determining', pending_json = ?, updated_at = ? WHERE activity_id = ? AND assignment_key = ?", (canonical_json(pending), _now(), activity_id, key))
            self._say(tx, row["project_id"], activity_id, f"Architectural determination {key}: architect {route['tool']} {route['model']} ({route['slot']} route) started.")

    def _determination_accept(self, row: Mapping[str, Any], arch: dict[str, Any], pending: dict[str, Any], current: Mapping[str, str]) -> None:
        assert self.runs is not None
        activity_id, key = row["activity_id"], arch["assignment_key"]
        response = self.runs.response(current["run_id"]) or {}
        trigger = json.loads(arch["trigger_json"])
        if response.get("result") != "completed":
            self._support_block(row, arch, "the architect asked a question; a determination needs more information than this assignment can ask for")
            return
        known = {p["packet_key"] for p in self._packets(activity_id)}
        problem = None
        if response["determination"] == "in_scope_supplement":
            problem = "in_scope_supplement belongs to milestone-gap results; choose within_confirmed_design, implementation_defect or reregistration_required"
        elif trigger.get("exhausted") and response["owner_recommendation"] not in ("grant_one", "remain_paused"):
            problem = "an exhausted review limit needs owner_recommendation grant_one or remain_paused"
        elif not trigger.get("exhausted") and response["owner_recommendation"] is not None:
            problem = "no allowance is exhausted, so owner_recommendation must be null"
        elif any(k not in known for k in response["affected_work"]):
            problem = "affected_work names a packet that is not in this Execution"
        elif response["determination"] == "reregistration_required" and not response["affected_work"]:
            problem = "a re-registration result lists the affected packets"
        if problem:
            self._reject_support_result(row, arch, pending, current, "determination_run", problem, self._determination_start)
            return
        pending.pop("determination_run", None)
        pending.pop("last_recovery_detail", None)
        result = {k: response[k] for k in ("determination", "rationale", "interpretation", "minimum_correction", "affected_work", "owner_recommendation", "disposition_recommendation")}
        result["run_id"] = current["run_id"]
        kind = result["determination"]
        state = "awaiting_disposition" if kind == "reregistration_required" else "decided"
        with self.database.transaction() as tx:
            tx.execute("UPDATE service_execution_architect SET state = ?, result_json = ?, pending_json = ?, note = NULL, updated_at = ? WHERE activity_id = ? AND assignment_key = ?",
                       (state, canonical_json(result), canonical_json(pending), _now(), activity_id, key))
            summary = (f"interpretation: {result['interpretation']}" if kind == "within_confirmed_design" else f"implementation defect, minimum correction: {result['minimum_correction']}" if kind == "implementation_defect"
                       else f"re-registration is required for {', '.join(result['affected_work'])}; recommended disposition {result['disposition_recommendation']}")
            self._say(tx, row["project_id"], activity_id, f"Architectural determination {key} ({kind}): {str(result['rationale'])[:300]}. {summary[:400]}"
                      + (f" Architect recommendation to the Owner: {result['owner_recommendation']}." if result["owner_recommendation"] else ""))
            if trigger["source"] == "manager_question":
                self._event(tx, activity_id, "determination_ready", trigger.get("packet_key"), f"{key} ({kind}): {summary[:300]}")

    # --------------------------------------------------------- Owner choices

    def _limit_determination(self, tx: Any, activity_id: str, assignment_id: str) -> dict[str, Any]:
        """The saved architect recommendation for a review limit; the Owner's grant or hold waits for it."""
        from .requests import RequestRejection

        arch = self._row(tx, "SELECT * FROM service_execution_architect WHERE activity_id = ? AND assignment_key = ?", (activity_id, f"det-{assignment_id}"))
        result = json.loads(arch["result_json"]) if arch is not None and arch["result_json"] else None
        if result is None or result.get("owner_recommendation") not in ("grant_one", "remain_paused"):
            raise RequestRejection(409, "recommendation_pending", "the architect's recommendation for this review limit is not saved yet; the work stays blocked until it is")
        return result

    def _disposition_decision(self, tx: Any, request: Any, row: Mapping[str, Any], payload: Mapping[str, Any], next_version: int) -> Any:
        from .registry import OperationResult
        from .requests import RequestRejection

        activity_id = row["activity_id"]
        if payload["choice"] not in DISPOSITION_CHOICES:
            raise ValueError("the work disposition choice must be one of " + ", ".join(DISPOSITION_CHOICES))
        arch = self._row(tx, "SELECT * FROM service_execution_architect WHERE activity_id = ? AND assignment_key = ? AND state = 'awaiting_disposition'", (activity_id, payload["assignment_id"]))
        if arch is None:
            raise RequestRejection(409, "no_decision_pending", "no work disposition is pending for that determination")
        result = json.loads(arch["result_json"])
        affected = list(result["affected_work"])
        fresh = self._row(tx, "SELECT pending_json FROM service_executions WHERE activity_id = ?", (activity_id,))
        pending = json.loads(fresh["pending_json"] or "{}")
        pending["disposition"] = {"choice": payload["choice"], "determination": arch["assignment_key"], "affected": affected, "request_id": request.request_id, "recommended": result["disposition_recommendation"], "decided_at": _now()}
        tx.execute("UPDATE service_executions SET pending_json = ? WHERE activity_id = ?", (canonical_json(pending), activity_id))
        tx.execute("UPDATE service_execution_architect SET state = 'disposition_recorded', note = ?, updated_at = ? WHERE activity_id = ? AND assignment_key = ?",
                   (f"the Owner chose {payload['choice']}", _now(), activity_id, arch["assignment_key"]))
        labels = {"continue_unaffected": "block the affected packets and their dependants; unrelated work continues", "finish_safe_work": "stop new starts and finish safe running work",
                  "stop_affected_or_all": "stop new starts and stop the affected running work", "finish_current_for_replanning": "stop all new starts, finish current work and prioritize replanning"}
        text = (f"Owner chose {payload['choice']} for {arch['assignment_key']} (architect recommended {result['disposition_recommendation']}): {labels[payload['choice']]}. "
                f"Affected packets: {', '.join(affected)}. This does not start re-registration or replanning.")
        self._event(tx, activity_id, "disposition", None, text[:400])
        self._activity(tx, activity_id, "running", text, version=next_version)
        self._say(tx, row["project_id"], activity_id, text)
        return OperationResult(data={"activity_id": activity_id, "decision": payload["choice"], "determination": arch["assignment_key"], "affected": affected, "message": text},
                               status="accepted", project_id=row["project_id"], activity_id=activity_id)

    def _advance_disposition(self, row: Mapping[str, Any]) -> None:
        """Enforce a saved stop choice on running work, and end the Execution once the permitted work has settled."""
        assert self.runs is not None
        fresh = self._read("SELECT * FROM service_executions WHERE activity_id = ?", (row["activity_id"],))
        if fresh is None or fresh["state"] not in ("running", "blocked"):
            return
        disposition = json.loads(fresh["pending_json"] or "{}").get("disposition")
        if not disposition or disposition["choice"] not in _DISPOSITION_ENDS:
            return
        activity_id = fresh["activity_id"]
        if disposition["choice"] == "stop_affected_or_all":
            wanted = set(disposition["affected"]) or {p["packet_key"] for p in self._packets(activity_id)}
            for packet in self._packets(activity_id):
                if packet["packet_key"] not in wanted or packet["state"] not in ("reserved", "coding", "correcting", "reviewing"):
                    continue
                pending = json.loads(packet["pending_json"] or "{}")
                live = False
                for slot in ("coder_run", "reviewer_run"):
                    current = pending.get(slot)
                    if current and self.runs.poll(current["run_id"]).state in {"reserved", "running", "stopping"}:
                        self.runs.stop(current["run_id"], "stopped by the Owner's work disposition")
                        live = True
                if not live:
                    self._fail_packet(fresh, packet, "stopped by the Owner's work disposition")

    def _settled_for_replanning(self, row: Mapping[str, Any]) -> bool:
        activity_id = row["activity_id"]
        pending = json.loads(row["pending_json"] or "{}")
        disposition = pending.get("disposition")
        if not disposition or disposition["choice"] not in _DISPOSITION_ENDS or pending.get("manager_run") is not None:
            return False
        if any(p["state"] in (*_PACKET_RUNNING, "reserved") for p in self._packets(activity_id)):
            return False
        if any(e["state"] in ("queued", "integrating", "publishing", "reviewing", "merging") for e in self._queue(activity_id)):
            return False
        if any(a["state"] in ("requested", "drafting", "reviewing", "correcting", "publishing", "recommending", "determining", "requested") for a in self._architects(activity_id)):
            return False
        return self._read("SELECT 1 AS n FROM service_execution_journal WHERE activity_id = ? AND state = 'prepared'", (activity_id,)) is None

    def _end_for_replanning(self, row: Mapping[str, Any]) -> None:
        activity_id = row["activity_id"]
        unfinished = [p["packet_key"] for p in self._packets(activity_id) if p["state"] in ("pending",)]
        with self.database.transaction() as tx:
            current = self._row(tx, "SELECT state FROM service_executions WHERE activity_id = ?", (activity_id,))
            if current is None or current["state"] not in ("running", "blocked"):
                return
            tx.execute("UPDATE service_executions SET state = 'ended_for_replanning', note = 'ready for re-registration' WHERE activity_id = ?", (activity_id,))
            self.reservations.release(tx, row["project_id"], activity_id)
            text = (f"Execution ended for replanning: every permitted run, review and operation has settled and nothing was marked complete to reach this point. "
                    f"{len(unfinished)} packet(s) stay unfinished for replanning ({', '.join(unfinished) or 'none'}). The project is ready for re-registration.")
            self._activity(tx, activity_id, "completed", text)
            self._event(tx, activity_id, "ended_for_replanning", None, text[:400])
            self._say(tx, row["project_id"], activity_id, text)
            self._emit(tx, row["project_id"], activity_id, "execution.ended_for_replanning", {"unfinished": unfinished})

    # ------------------------------------------------------------------ view

    def determination_view(self, activity_id: str) -> list[dict[str, Any]]:
        views = []
        for arch in self._architects(activity_id, "determination"):
            pending = json.loads(arch["pending_json"] or "{}")
            result = json.loads(arch["result_json"]) if arch["result_json"] else None
            trigger = json.loads(arch["trigger_json"])
            views.append({"determination_id": arch["assignment_key"], "source": trigger.get("source"), "packet_key": arch["packet_key"], "state": arch["state"], "note": arch["note"], "subject": arch["subject"],
                          "question": trigger.get("question"), "architect": pending.get("architect"), "result": result})
        return views

    def _gap_result(self, activity_id: str, gap_id: str) -> dict[str, Any] | None:
        arch = self._read("SELECT result_json FROM service_execution_architect WHERE activity_id = ? AND assignment_key = ?", (activity_id, gap_id))
        return None if arch is None or not arch["result_json"] else json.loads(arch["result_json"])

    def disposition_view(self, row: Mapping[str, Any]) -> dict[str, Any] | None:
        return json.loads(row["pending_json"] or "{}").get("disposition")
