"""Pause, resume, graceful stop and manual retry of an Execution.

Accepting a pause or a stop saves, in one transaction, the exact set of work already in progress: the packets being
coded, reviewed or published, the integration queue entries in flight, the architectural operations running, and the
milestones whose remaining packets are all in that set. Nothing outside the set can start while the restriction
applies: pending packets are refused, a queue entry outside the set holds its place and blocks everything behind it
(first in, first out), and other milestones are not verified. Members keep running only the stages that settle their
own work. Once nothing in the set is running or uncertain, a pause enters `paused` (a resume continues from the saved
state) and a stop publishes a verified stopped-closure record before entering `stopped`. A saved manual-retry grant
lets the Owner run one more attempt of one failed assignment without resetting any allowance. Everything lives in the
activity's saved records, so a service restart reloads the set, the restriction and every grant unchanged.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Mapping

from maestro.foundation import Transaction, canonical_json

from .agent_runs import AgentRunError
from .architecture_records import encode
from .registration_github import DestinationError
from .registry import OperationHandler, OperationResult, PreparedOperation, RequestLike
from .requests import RequestRejection

_RUNNING_PACKET = ("reserved", "coding", "correcting", "reviewing", "publishing", "review_ready")
_ENTRY_IN_FLIGHT = ("integrating", "publishing", "reviewing", "merging")
_ARCHITECT_ACTIVE = ("requested", "drafting", "reviewing", "correcting", "publishing", "recommending", "determining")
_VERIFYING = ("qa_running", "reviewing", "promoting", "publishing")
_STOP_KIND = "execution_stop_publish"


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class LifecycleMixin:
    """Lifecycle behavior of ``ExecutionService``."""

    @property
    def lifecycle_handlers(self) -> tuple[OperationHandler, ...]:
        return (OperationHandler("execution.pause", lambda r: self._prepare_lifecycle(r, "pause")), OperationHandler("execution.resume", lambda r: self._prepare_lifecycle(r, "resume")),
                OperationHandler("execution.stop", lambda r: self._prepare_lifecycle(r, "stop")), OperationHandler("execution.retry", self.prepare_retry))

    # ---------------------------------------------------------------- the set

    @staticmethod
    def _settlement_of(row: Mapping[str, Any]) -> dict[str, Any] | None:
        return json.loads(row["pending_json"] or "{}").get("settlement")

    def _outside_set(self, row: Mapping[str, Any], group: str, key: object) -> bool:
        """True while a pause or stop applies and ``key`` was not in the saved in-progress set."""
        settlement = self._settlement_of(row)
        return settlement is not None and key not in settlement["members"][group]

    def _architect_outside_set(self, row: Mapping[str, Any], arch: Mapping[str, Any]) -> bool:
        """An architectural operation may run under a pause or stop only for work already in the saved set."""
        settlement = self._settlement_of(row)
        if settlement is None:
            return False
        members = settlement["members"]
        milestone = json.loads(arch["trigger_json"] or "{}").get("milestone_key")
        return not (arch["assignment_key"] in members["architects"] or arch["packet_key"] in members["packets"] or (milestone is not None and milestone in members["milestones"]))

    def _in_progress_set(self, tx: Transaction, activity_id: str) -> dict[str, list[Any]]:
        packets = self._row_list(tx, "SELECT * FROM service_execution_packets WHERE activity_id = ? ORDER BY packet_key", (activity_id,))
        queue = self._row_list(tx, "SELECT * FROM service_execution_queue WHERE activity_id = ? ORDER BY entry_id", (activity_id,))
        members = {p["packet_key"] for p in packets if p["state"] in _RUNNING_PACKET}
        entries = {e["packet_key"] for e in queue if e["kind"] == "packet" and e["state"] not in ("merged", "withdrawn", "invalidated")}
        members |= {p["packet_key"] for p in packets if p["state"] == "approved" and p["packet_key"] not in entries}
        in_queue = [e["entry_id"] for e in queue if e["state"] in _ENTRY_IN_FLIGHT or (e["state"] == "queued" and e["kind"] == "packet" and e["packet_key"] in members)]
        by_milestone: dict[str, list[dict[str, Any]]] = {}
        for p in packets:
            by_milestone.setdefault(p["milestone_key"], []).append(p)
        done = {v["milestone_key"] for v in self._row_list(tx, "SELECT milestone_key FROM service_execution_verifications WHERE activity_id = ? AND state = 'complete'", (activity_id,))}
        milestones = sorted(k for k, mine in by_milestone.items() if k not in done and all(p["state"] == "integrated" or p["packet_key"] in members for p in mine))
        architects = [a["assignment_key"] for a in self._row_list(tx, "SELECT assignment_key, state FROM service_execution_architect WHERE activity_id = ?", (activity_id,)) if a["state"] in _ARCHITECT_ACTIVE]
        return {"packets": sorted(members), "queue": in_queue, "milestones": milestones, "architects": architects}

    def _restricts_queue(self, row: Mapping[str, Any], head: Mapping[str, Any]) -> bool:
        """The head of the queue is not in the saved set, so the queue holds still: nothing behind it is skipped to."""
        settlement = self._settlement_of(row)
        if settlement is None:
            return False
        members = settlement["members"]
        return not (head["entry_id"] in members["queue"] or (head["kind"] == "packet" and head["packet_key"] in members["packets"]))

    # ------------------------------------------------------------- operations

    def _prepare_lifecycle(self, request: RequestLike, action: str) -> PreparedOperation:
        if request.project_id is None or request.activity_id is None or request.expected_version is None or request.question_id is not None:
            raise ValueError(f"execution.{action} needs a project, the Execution activity and the displayed activity version")
        if dict(request.payload):
            raise ValueError(f"execution.{action} takes no payload")
        activity_id = request.activity_id

        def apply(tx: Transaction, next_version: int) -> OperationResult:
            row = self._row(tx, "SELECT * FROM service_executions WHERE activity_id = ? AND project_id = ?", (activity_id, request.project_id))
            if row is None:
                raise RequestRejection(404, "execution_not_found", "the Execution activity was not found", fields={"activity_id": activity_id})
            current = self._row(tx, "SELECT version FROM entity_versions WHERE entity_id = ?", (activity_id,))
            if current is not None and int(current["version"]) != request.expected_version:
                raise RequestRejection(409, "stale_version", "the activity changed since it was displayed", fields={"activity_version": int(current["version"]), "state": row["state"]})
            pending = json.loads(row["pending_json"] or "{}")
            settlement = pending.get("settlement")
            state = row["state"]
            if action == "resume":
                text = self._resume(tx, row, pending, settlement)
            elif action == "pause":
                if state not in ("running", "blocked") or settlement is not None:
                    raise RequestRejection(409, "not_allowed", f"the Execution is {state}" + (f" and already {'stopping' if settlement['kind'] == 'stop' else 'pausing'}" if settlement else "") + "; it can only be paused while it is running", fields={"state": state})
                members = self._in_progress_set(tx, activity_id)
                pending["settlement"] = {"kind": "pause", "requested_at": _now(), "request_id": request.request_id, "members": members}
                text = f"Pausing: {len(members['packets'])} packet(s), {len(members['queue'])} queue entr{'y' if len(members['queue']) == 1 else 'ies'} and {len(members['architects'])} architectural operation(s) settle first; no other work starts."
            else:
                if state not in ("running", "blocked", "paused") or (settlement is not None and settlement["kind"] == "stop"):
                    raise RequestRejection(409, "not_allowed", f"the Execution is {state}" + (" and already stopping" if settlement else "") + "; it can be stopped while it is running or paused", fields={"state": state})
                members = settlement["members"] if settlement else self._in_progress_set(tx, activity_id)
                pending["settlement"] = {"kind": "stop", "requested_at": _now(), "request_id": request.request_id, "members": members}
                text = f"Stopping: {len(members['packets'])} packet(s), {len(members['queue'])} queue entr{'y' if len(members['queue']) == 1 else 'ies'} and {len(members['architects'])} architectural operation(s) settle first; unstarted work stays unfinished. A stopped-closure record is published when they have."
                tx.execute("UPDATE service_executions SET state = 'finishing' WHERE activity_id = ?", (activity_id,))
            tx.execute("UPDATE service_executions SET pending_json = ? WHERE activity_id = ?", (canonical_json(pending), activity_id))
            self._event(tx, activity_id, action, None, text[:400])
            self._say(tx, row["project_id"], activity_id, f"The Owner asked to {action} Execution. {text}")
            self._activity(tx, activity_id, "finishing" if action == "stop" else ("running" if action == "resume" else None), text, None, version=next_version)
            self._emit(tx, row["project_id"], activity_id, f"execution.{action}", {"activity_id": activity_id})
            return OperationResult(data={"activity_id": activity_id, "action": action, "state": "finishing" if action == "stop" else ("running" if action == "resume" else state), "message": text},
                                   status="accepted", project_id=row["project_id"], activity_id=activity_id)

        return PreparedOperation(activity_id, f"execution.{action}_accepted", {"activity_id": activity_id}, apply)

    def _resume(self, tx: Transaction, row: Mapping[str, Any], pending: dict[str, Any], settlement: Mapping[str, Any] | None) -> str:
        if row["state"] != "paused":
            raise RequestRejection(409, "not_allowed", f"the Execution is {row['state']}; only a paused Execution can be resumed", fields={"state": row["state"]})
        disposition = pending.get("disposition")
        if disposition and disposition["choice"] in ("finish_safe_work", "stop_affected_or_all", "finish_current_for_replanning"):
            raise RequestRejection(409, "restriction_remains", f"the Owner's work disposition {disposition['choice']} still restricts new work, so resuming would not start anything", fields={"disposition": disposition["choice"]})
        pending.pop("settlement", None)
        tx.execute("UPDATE service_executions SET state = 'running', note = NULL WHERE activity_id = ?", (row["activity_id"],))
        return "Resumed: the saved packets, queue, review counts and allowances continue exactly where they were, and new packets can be reserved again."

    # ---------------------------------------------------------------- settle

    def _unsettled(self, row: Mapping[str, Any], settlement: Mapping[str, Any]) -> list[str]:
        """Plain reasons the saved set still has running or uncertain work; empty when it has settled."""
        activity_id = row["activity_id"]
        members = settlement["members"]
        pending = json.loads(row["pending_json"] or "{}")
        reasons: list[str] = []
        queue = [e for e in self._queue(activity_id) if e["state"] not in ("merged", "withdrawn", "invalidated")]
        for p in self._packets(activity_id):
            if p["state"] in _RUNNING_PACKET:
                reasons.append(f"packet {p['packet_key']} is {p['state']}")
            elif p["state"] == "approved" and not any(e["packet_key"] == p["packet_key"] for e in queue):
                reasons.append(f"packet {p['packet_key']} is approved and about to be queued")
        held = False
        for e in queue:
            member = e["entry_id"] in members["queue"] or (e["kind"] == "packet" and e["packet_key"] in members["packets"])
            if e["state"] in ("blocked", "limit_paused") or (e["state"] == "queued" and not member):
                held = True
            elif e["state"] in _ENTRY_IN_FLIGHT or (e["state"] == "queued" and not held):
                reasons.append(f"queue entry {e['entry_id']} is {e['state']}")
        for a in self._architects(activity_id):
            if a["state"] in _ARCHITECT_ACTIVE and not self._architect_outside_set(row, a):
                reasons.append(f"architectural operation {a['assignment_key']} is {a['state']}")
        for key, v in self._verifications(activity_id).items():
            if v["state"] in _VERIFYING or (v["state"] == "qa" and key in members["milestones"]):
                reasons.append(f"milestone {key} verification is {v['state']}")
        if pending.get("manager_run") is not None:
            reasons.append("the Development Manager's planning run is active")
        if self._read("SELECT 1 AS n FROM service_execution_journal WHERE activity_id = ? AND state = 'prepared' AND kind != ?", (activity_id, _STOP_KIND)) is not None:
            reasons.append("a repository operation is unconfirmed")
        return reasons

    def _settlement_step(self, row: Mapping[str, Any]) -> bool:
        """Advance a saved pause or stop once its set has settled; True when nothing else should be evaluated this pass."""
        settlement = self._settlement_of(row)
        if settlement is None or settlement.get("settled"):
            return False
        if self._unsettled(row, settlement):
            return False
        if settlement["kind"] == "pause":
            with self.database.transaction() as tx:
                current = self._row(tx, "SELECT pending_json, state FROM service_executions WHERE activity_id = ?", (row["activity_id"],))
                if current is None or current["state"] not in ("running", "blocked"):
                    return True
                pending = json.loads(current["pending_json"] or "{}")
                if pending.get("settlement") is None or pending["settlement"]["kind"] != "pause":
                    return True
                pending["settlement"]["settled"] = _now()
                text = "Paused: every packet, review, integration and operation in the saved set has settled and nothing is uncertain. Resume continues from the saved state; held work keeps its place."
                tx.execute("UPDATE service_executions SET state = 'paused', pending_json = ?, note = 'paused by the Owner' WHERE activity_id = ?", (canonical_json(pending), row["activity_id"]))
                self._activity(tx, row["activity_id"], "paused", text)
                self._event(tx, row["activity_id"], "paused", None, text[:400])
                self._say(tx, row["project_id"], row["activity_id"], text)
                self._emit(tx, row["project_id"], row["activity_id"], "execution.paused", {"activity_id": row["activity_id"]})
            return True
        try:
            self._publish_stop(row, settlement)
        except DestinationError as error:
            transient = error.code == "github_unreachable" or (isinstance(error.fields.get("status"), int) and error.fields["status"] >= 500)
            if not transient:
                with self.database.transaction() as tx:
                    self._activity(tx, row["activity_id"], "finishing", f"Stopped closure is blocked: {error.code}: {str(error)[:300]}. It is retried; nothing is marked stopped until the record is verified.")
        return True

    # --------------------------------------------------------- stopped closure

    def _stop_record(self, row: Mapping[str, Any], settlement: Mapping[str, Any]) -> dict[str, Any]:
        activity_id = row["activity_id"]
        confirmed = json.loads(row["confirmed_ref_json"])
        verifications = self._verifications(activity_id)
        milestones = self._milestones(activity_id)
        completed = sorted((v for v in verifications.values() if v["state"] == "complete"), key=lambda v: v["master_seq"] or 0)
        packets = self._packets(activity_id)
        unfinished_milestones = [{"id": k, "subject": m["subject"], "verification": verifications[k]["state"] if k in verifications else "not started", "reason": (verifications[k]["note"] if k in verifications and verifications[k]["note"] else "not every packet is integrated and verified")}
                                 for k, m in sorted(milestones.items()) if verifications.get(k, {}).get("state") != "complete"]
        unfinished_packets = [{"key": p["packet_key"], "milestone": p["milestone_key"], "state": p["state"], "reason": p["note"] or ("not started" if p["state"] == "pending" else "not integrated")} for p in packets if p["state"] != "integrated"]
        queue = [{"entry": e["entry_id"], "kind": e["kind"], "packet": e["packet_key"], "delivery": e["delivery_id"], "state": e["state"], "reason": e["note"] or "not merged"} for e in self._queue(activity_id) if e["state"] not in ("merged", "withdrawn", "invalidated")]
        deliveries = [{"id": d["delivery_id"], "provider": d["provider_milestone"], "consumer": d["consumer_milestone"], "state": d["state"]} for d in self._deliveries(activity_id) if d["state"] not in ("delivered", "invalidated")]
        supplements = [{"supplement_id": s["supplement_id"], "version": s["version"], "milestone": s["milestone_key"], "state": s["state"]} for s in self._rows("SELECT * FROM service_execution_supplements WHERE activity_id = ?", (activity_id,)) if s["state"] != "active"]
        observations = sorted({f["subject"] for v in verifications.values() for r in self._rows("SELECT findings_json FROM service_execution_milestone_reviews WHERE activity_id = ? AND milestone_key = ?", (activity_id, v["milestone_key"]))
                               for f in json.loads(r["findings_json"]) if f["severity"] != "blocking"})
        operations = [{"operation": j["operation_id"], "kind": j["kind"], "branch": j["branch"], "state": j["state"], "remote_after": j["remote_after"]} for j in self._rows("SELECT * FROM service_execution_journal WHERE activity_id = ? ORDER BY created_at", (activity_id,)) if j["kind"] != _STOP_KIND]
        return {
            "schema_version": 1, "kind": "stopped", "record": "execution-stop@1", "project_id": row["project_id"], "activity_id": activity_id, "registration_activity_id": row["registration_activity_id"],
            "breakdown": {k: confirmed[k] for k in ("version", "commit", "manifest_path")}, "configuration": {"sha256": row["config_sha256"], "bundle": json.loads(row["bundle_json"])},
            "completed_milestones": [{"id": v["milestone_key"], "completion_path": v["completion_path"], "completion_sha256": v["completion_sha256"], "completion_commit": v["completion_commit"], "merge_commit": v["promoted_commit"]} for v in completed],
            "product_master": {"branch": row["master_branch"], "start_commit": row["master_commit"], "final_commit": self._master_head(row)},
            "unfinished": {"milestones": unfinished_milestones, "packets": unfinished_packets, "queue_entries": queue, "dependency_deliveries": deliveries, "supplements": supplements},
            "final_restrictions": {"requested_at": settlement["requested_at"], "in_progress_set": settlement["members"], "new_packet_reservations": "refused"},
            "delivery": "not delivered: this record closes a stopped Execution and is never a completion",
            "non_blocking_observations": observations, "repository_operations": operations, "started_at": row["created_at"], "stopped_at": _now(),
        }

    def _publish_stop(self, row: Mapping[str, Any], settlement: Mapping[str, Any]) -> None:
        activity_id = row["activity_id"]
        destination = self._dest(row)
        stored = self._read("SELECT * FROM service_execution_completion WHERE activity_id = ?", (activity_id,))
        if stored is None:
            record = self._stop_record(row, settlement)
            data = encode(record)
            path = f".maestro/execution/{activity_id}/stop/versions/1/stop.json"
            with self.database.transaction() as tx:
                tx.execute("INSERT INTO service_execution_completion(activity_id, state, path, sha256, record_json, final_master, created_at, updated_at) VALUES (?, 'prepared', ?, ?, ?, ?, ?, ?)",
                           (activity_id, path, _sha(data), canonical_json(record), record["product_master"]["final_commit"], _now(), _now()))
            stored = self._read("SELECT * FROM service_execution_completion WHERE activity_id = ?", (activity_id,))
        data = encode(json.loads(stored["record_json"]))
        if _sha(data) != stored["sha256"]:
            raise DestinationError("verification_failed", "the saved stopped-closure record changed before publication")
        operation_id = f"{activity_id}-execution-stop-v1"
        if self._read("SELECT 1 AS n FROM service_execution_journal WHERE operation_id = ?", (operation_id,)) is None:
            self._journal_begin(row, operation_id, "execution", _STOP_KIND, row["master_branch"], stored["sha256"], destination.branch_head(row["repository"], row["master_branch"]))
        destination.check_code_branch(row["repository"], row["master_branch"])
        remote_head = destination.branch_head(row["repository"], row["master_branch"])
        if remote_head != stored["final_master"] and stored["commit_sha"] is None:
            raise DestinationError("target_changed", f"the product's {row['master_branch']} branch moved from {stored['final_master'][:12]} to {(remote_head or 'nothing')[:12]}; the stopped closure waits until it is reconciled", remote=remote_head)
        commit = destination.publish(row["repository"], row["master_branch"], {stored["path"]: data}, f"Execution {activity_id}: stopped-closure record version 1")
        destination.verify_files(row["repository"], commit, {stored["path"]: data})
        for v in self._verifications(activity_id).values():
            if v["state"] == "complete" and not destination.contains(row["repository"], v["promoted_commit"], commit):
                raise DestinationError("verification_failed", f"the product branch does not contain the verified merge of milestone {v['milestone_key']}")
        with self.database.transaction() as tx:
            current = self._row(tx, "SELECT state, pending_json FROM service_executions WHERE activity_id = ?", (activity_id,))
            if current is None or current["state"] != "finishing":
                return
            pending = json.loads(current["pending_json"] or "{}")
            pending["settlement"]["settled"] = _now()
            tx.execute("UPDATE service_execution_journal SET state = 'verified', remote_after = ? WHERE operation_id = ?", (commit, operation_id))
            tx.execute("UPDATE service_execution_completion SET state = 'published', commit_sha = ?, updated_at = ? WHERE activity_id = ?", (commit, _now(), activity_id))
            tx.execute("UPDATE service_executions SET state = 'stopped', pending_json = ?, note = 'stopped by the Owner; not a completion' WHERE activity_id = ?", (canonical_json(pending), activity_id))
            self.reservations.release(tx, row["project_id"], activity_id)
            record = json.loads(stored["record_json"])
            text = (f"Execution stopped, not completed. {len(record['completed_milestones'])} milestone(s) were completed and promoted before the stop; "
                    f"{len(record['unfinished']['milestones'])} milestone(s) and {len(record['unfinished']['packets'])} packet(s) are unfinished. The stopped-closure record {stored['path']} "
                    f"(SHA-256 {stored['sha256'][:12]}) is published in {commit[:12]} and verified. The project is idle and can be registered again.")
            self._activity(tx, activity_id, "stopped", text, (), ended=True)
            self._event(tx, activity_id, "execution_stopped", None, text[:400])
            self._say(tx, row["project_id"], activity_id, text)
            self._emit(tx, row["project_id"], activity_id, "execution.stopped", {"commit": commit, "path": stored["path"]})

    # ------------------------------------------------------------ manual retry

    def _retry_decision(self, tx: Transaction, request: RequestLike, row: Mapping[str, Any], payload: Mapping[str, Any], next_version: int) -> OperationResult:
        """The Owner's typed choice for one failed assignment: a single unconsumed retry grant, or leaving it as it is."""
        activity_id, key = row["activity_id"], payload["assignment_id"]
        packet = self._row(tx, "SELECT * FROM service_execution_packets WHERE activity_id = ? AND packet_key = ?", (activity_id, key))
        if packet is None or packet["state"] != "failed":
            raise RequestRejection(409, "no_decision_pending", "that packet has no failed assignment waiting for a manual-retry decision")
        pending = json.loads(packet["pending_json"] or "{}")
        grants = list(pending.get("manual_grants", []))
        maximum = int(json.loads(row["config_json"])["recovery"]["manual_retry_attempts"])
        duration = payload.get("duration_seconds")
        if duration is not None and (not isinstance(duration, int) or isinstance(duration, bool) or duration <= 0):
            raise ValueError("duration_seconds must be a positive whole number of seconds")
        if payload["choice"] == "remain_paused":
            text = f"Owner chose to leave {key} stopped; no retry was granted and nothing changed."
        else:
            if any(g["state"] in ("unconsumed", "reserved") for g in grants):
                raise RequestRejection(409, "grant_open", f"{key} already has an unused manual-retry grant")
            if len(grants) >= maximum:
                raise RequestRejection(409, "manual_retry_limit", f"{key} has used its {maximum} configured manual retr{'y' if maximum == 1 else 'ies'}; no further grant can be made")
            grant = {"grant_id": f"{activity_id}-{key}-manual-{len(grants) + 1}", "state": "unconsumed", "request_id": request.request_id, "granted_at": _now(), "duration_seconds": duration}
            grants.append(grant)
            pending["manual_grants"] = grants
            tx.execute("UPDATE service_execution_packets SET pending_json = ?, updated_at = ? WHERE activity_id = ? AND packet_key = ?", (canonical_json(pending), _now(), activity_id, key))
            text = f"Owner granted one manual retry for {key} ({grant['grant_id']}), grant {len(grants)} of {maximum}" + (f", with {duration}s for the next run only" if duration else "") + ". Run it with execution.retry once you have recorded what changed; other counts are unchanged."
        self._event(tx, activity_id, "manual_retry_decision", key, text[:400])
        self._say(tx, row["project_id"], activity_id, text)
        self._activity(tx, activity_id, None, None, version=next_version)
        return OperationResult(data={"activity_id": activity_id, "decision": payload["choice"], "packet": key, "message": text, "grant_id": grants[-1]["grant_id"] if payload["choice"] == "grant_one" else None},
                               status="accepted", project_id=row["project_id"], activity_id=activity_id)

    def prepare_retry(self, request: RequestLike) -> PreparedOperation:
        if request.project_id is None or request.activity_id is None or request.expected_version is None or request.question_id is not None:
            raise ValueError("execution.retry needs a project, the Execution activity and the displayed activity version")
        payload = dict(request.payload)
        if set(payload) != {"packet_key", "grant_id", "intervention"} or not all(isinstance(payload[k], str) and payload[k].strip() for k in payload):
            raise ValueError("execution.retry payload must be packet_key, grant_id and intervention (what changed), all non-empty")
        activity_id = request.activity_id

        def apply(tx: Transaction, next_version: int) -> OperationResult:
            row = self._row(tx, "SELECT * FROM service_executions WHERE activity_id = ? AND project_id = ?", (activity_id, request.project_id))
            if row is None:
                raise RequestRejection(404, "execution_not_found", "the Execution activity was not found", fields={"activity_id": activity_id})
            current = self._row(tx, "SELECT version FROM entity_versions WHERE entity_id = ?", (activity_id,))
            if current is not None and int(current["version"]) != request.expected_version:
                raise RequestRejection(409, "stale_version", "the activity changed since it was displayed", fields={"activity_version": int(current["version"])})
            if row["state"] not in ("running", "blocked", "finishing"):
                raise RequestRejection(409, "not_allowed", f"the Execution is {row['state']}; a manual retry needs it to be running", fields={"state": row["state"]})
            key = payload["packet_key"]
            if self._outside_set(row, "packets", key):
                raise RequestRejection(409, "held_by_restriction", f"{key} was not in the work in progress when the pause or stop was accepted, so it cannot start")
            packet = self._row(tx, "SELECT * FROM service_execution_packets WHERE activity_id = ? AND packet_key = ?", (activity_id, key))
            if packet is None or packet["state"] != "failed":
                raise RequestRejection(409, "not_retryable", f"{key} is not a failed assignment", fields={"state": None if packet is None else packet["state"]})
            pending = json.loads(packet["pending_json"] or "{}")
            grants = list(pending.get("manual_grants", []))
            grant = next((g for g in grants if g["grant_id"] == payload["grant_id"]), None)
            if grant is None or grant["state"] != "unconsumed":
                raise RequestRejection(409, "grant_not_available", "that manual-retry grant does not exist or was already reserved or used", fields={"state": None if grant is None else grant["state"]})
            stage = self._retry_stage(pending)
            if stage is None:
                raise RequestRejection(409, "not_retryable", f"{key}'s last agent run is not one a manual retry can continue (it has no paused or recoverable assignment)")
            grant.update(state="reserved", reserved_by=request.request_id, reserved_at=_now())
            pending["manual_grants"] = grants
            pending["manual_retry"] = {"grant_id": grant["grant_id"], "intervention": payload["intervention"].strip()[:1000], "stage": stage, "duration_seconds": grant.get("duration_seconds")}
            tx.execute("UPDATE service_execution_packets SET state = ?, pending_json = ?, note = 'manual retry granted', updated_at = ? WHERE activity_id = ? AND packet_key = ?",
                       ("review_ready" if stage == "reviewer" else "reserved", canonical_json(pending), _now(), activity_id, key))
            text = f"Manual retry reserved for {key} ({grant['grant_id']}): the same assignment runs again with a new run; review rounds, attempts and the recorded grant count are unchanged. What changed: {payload['intervention'].strip()[:200]}"
            self._event(tx, activity_id, "manual_retry", key, text[:400])
            self._say(tx, row["project_id"], activity_id, text)
            self._activity(tx, activity_id, "finishing" if row["state"] == "finishing" else "running", text, None, version=next_version)
            if row["state"] == "blocked":
                tx.execute("UPDATE service_executions SET state = 'running' WHERE activity_id = ?", (activity_id,))
            return OperationResult(data={"activity_id": activity_id, "packet": key, "grant_id": grant["grant_id"], "stage": stage, "message": text}, status="accepted", project_id=row["project_id"], activity_id=activity_id)

        return PreparedOperation(activity_id, "execution.retry_accepted", {"activity_id": activity_id}, apply)

    def _retry_stage(self, pending: Mapping[str, Any]) -> str | None:
        """Which run the failed packet's retry continues: the coder's when its assignment is retryable, else the reviewer's."""
        assert self.runs is not None
        for stage, slot in (("coder", "coder_run"), ("reviewer", "reviewer_run")):
            current = pending.get(slot)
            if current is None:
                continue
            try:
                state = self.runs.assignment_state(current["assignment_id"])["state"]
            except AgentRunError:
                continue
            if state in ("paused", "needs_recovery"):
                return stage
        return None

    def _manual_launch(self, row: Mapping[str, Any], packet: Mapping[str, Any], pending: dict[str, Any], slot: str, assignment_id: str, launch: Any) -> str:
        """Run ``launch(intervention)`` for a reserved manual retry: consume the grant when a run was created, release it when none was."""
        assert self.runs is not None
        manual = pending["manual_retry"]
        before = self.runs.run_count(assignment_id)
        if manual.get("duration_seconds"):
            self.runs.set_next_run_duration(assignment_id, int(manual["duration_seconds"]))
        try:
            run_id = launch(manual["intervention"])
        except Exception:
            self._set_grant(row["activity_id"], packet["packet_key"], manual["grant_id"], "consumed" if self.runs.run_count(assignment_id) > before else "unconsumed", None)
            raise
        for grant in pending.get("manual_grants", []):
            if grant["grant_id"] == manual["grant_id"]:
                grant.update(state="consumed", run_id=run_id, consumed_at=_now())
                grant.pop("reserved_by", None)
        pending.pop("manual_retry", None)
        return run_id

    def _set_grant(self, activity_id: str, key: str, grant_id: str, state: str, run_id: str | None) -> None:
        with self.database.transaction() as tx:
            found = self._row(tx, "SELECT pending_json FROM service_execution_packets WHERE activity_id = ? AND packet_key = ?", (activity_id, key))
            if found is None:
                return
            pending = json.loads(found["pending_json"] or "{}")
            for grant in pending.get("manual_grants", []):
                if grant["grant_id"] == grant_id:
                    grant["state"] = state
                    grant["run_id"] = run_id or grant.get("run_id")
                    if state == "consumed":
                        grant["consumed_at"] = _now()
                    else:
                        grant.pop("reserved_by", None)
            if state in ("consumed", "unconsumed"):
                pending.pop("manual_retry", None)
            tx.execute("UPDATE service_execution_packets SET pending_json = ?, updated_at = ? WHERE activity_id = ? AND packet_key = ?", (canonical_json(pending), _now(), activity_id, key))

    # ------------------------------------------------------------------ view

    def lifecycle_view(self, row: Mapping[str, Any]) -> dict[str, Any] | None:
        settlement = self._settlement_of(row)
        activity_id = row["activity_id"]
        retryable = []
        for p in self._packets(activity_id):
            pending = self._packet_pending(p)
            if p["state"] == "failed":
                grants = pending.get("manual_grants", [])
                retryable.append({"packet_key": p["packet_key"], "reason": p["note"], "grants": [{k: g.get(k) for k in ("grant_id", "state", "run_id", "duration_seconds")} for g in grants],
                                  "maximum": int(json.loads(row["config_json"])["recovery"]["manual_retry_attempts"])})
            elif pending.get("manual_grants"):
                retryable.append({"packet_key": p["packet_key"], "reason": None, "grants": [{k: g.get(k) for k in ("grant_id", "state", "run_id", "duration_seconds")} for g in pending["manual_grants"]],
                                  "maximum": int(json.loads(row["config_json"])["recovery"]["manual_retry_attempts"])})
        stopped = self._read("SELECT state, path, sha256, commit_sha, final_master, record_json FROM service_execution_completion WHERE activity_id = ?", (activity_id,))
        closure = None
        if stopped is not None and json.loads(stopped["record_json"]).get("kind") == "stopped":
            record = json.loads(stopped["record_json"])
            closure = {"state": stopped["state"], "path": stopped["path"], "sha256": stopped["sha256"], "commit": stopped["commit_sha"], "completed_milestones": [m["id"] for m in record["completed_milestones"]],
                       "unfinished_milestones": [m["id"] for m in record["unfinished"]["milestones"]], "unfinished_packets": [p["key"] for p in record["unfinished"]["packets"]], "delivery": record["delivery"]}
        return {"settlement": None if settlement is None else {"kind": settlement["kind"], "requested_at": settlement["requested_at"], "settled": settlement.get("settled"), "members": settlement["members"],
                                                                   "waiting_on": [] if settlement.get("settled") else self._unsettled(row, settlement)},
                "manual_retries": retryable, "stopped_closure": closure}
