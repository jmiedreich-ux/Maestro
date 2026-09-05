"""Closed schema-5 operational records and service-owned persistence.

This module contains record creation, canonical value handling, idempotent
append, read foundations, guarded run-lifecycle and packet-eligibility
transitions, and the atomic assignment-claim primitive. Acceptance/merge
guards and recovery orchestration remain outside this boundary.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping, Sequence

from . import review_readiness
from .config import RuntimeConfig
from .storage import SQLiteFoundation


MAX_TEXT_BYTES = 512
MAX_JSON_BYTES = 1024 * 1024
_SHA40 = re.compile(r"[0-9a-f]{40}")
_SHA64 = re.compile(r"[0-9a-f]{64}")
_PROVIDER = re.compile(r"[a-z][a-z0-9-]{1,63}")
_REFERENCE_NAME = re.compile(r"[A-Z][A-Z0-9_]{2,127}")
_UTC = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}Z")
_CURRENCY = re.compile(r"[A-Z]{3}")
_ISO_DURATION = re.compile(r"P(?=\d|T\d)(?:\d+D)?(?:T(?:\d+H)?(?:\d+M)?(?:\d+(?:\.\d+)?S)?)?")
_BANNED_KEYS = {
    "prompt", "raw_prompt", "trace", "raw_trace", "secret", "secret_value",
    "password", "private_key", "credential_value", "authorization_header", "cookie_value",
}
_ENTITY_STATES = {
    "ProjectBinding": {"Candidate", "Active", "Superseded", "Blocked"},
    "SecretReferenceObservation": {"Active", "Stale", "Revoked", "Unavailable"},
    "GraphProjection": {"Active", "Stale", "NeedsReplan", "Superseded"},
    "WorkItem": {"Active", "NeedsReplan", "Superseded"},
    "Run": {"Planned", "Running", "Blocked", "AwaitingArchitect", "AwaitingOwner", "Complete", "Cancelled"},
    "Packet": {"Planned", "Waiting", "Blocked", "Ready", "Dispatchable", "Leased", "Running", "AwaitingIntegration", "AwaitingReview", "MergeReady", "AwaitingArchitect", "AwaitingOwner", "Merged", "Complete", "NeedsReplan", "Cancelled"},
    "Lease": {"Active", "Released", "Expired", "Cancelled"},
    "Attempt": {"Planned", "Running", "Succeeded", "Failed", "Cancelled", "TimedOut", "Stale"},
    "ResourceLock": {"Active", "Released", "Expired"},
    "Wait": {"Open", "Resolved", "Expired", "Cancelled"},
    "Notification": {"Pending", "Delivered", "Failed", "Acknowledged"},
}
_RUN_TRANSITIONS = {
    "Planned": {"Running", "Blocked", "Cancelled"},
    "Running": {"Blocked", "AwaitingArchitect", "AwaitingOwner", "Complete", "Cancelled"},
    "Blocked": {"Running", "AwaitingArchitect", "AwaitingOwner", "Cancelled"},
    "AwaitingArchitect": {"Running", "Blocked", "AwaitingOwner", "Cancelled"},
    "AwaitingOwner": {"Running", "Blocked", "Complete", "Cancelled"},
    "Complete": set(),
    "Cancelled": set(),
}
_PACKET_ELIGIBILITY_TRANSITIONS = {
    "Planned": {"Waiting", "Blocked", "Cancelled"},
    "Waiting": {"Ready", "Blocked", "Cancelled"},
    "Blocked": {"Waiting", "Ready", "Cancelled"},
    "Ready": {"Waiting", "Blocked", "Dispatchable", "Cancelled"},
    "Dispatchable": {"Ready", "Waiting", "Blocked", "Cancelled"},
}
_REVIEW_FINDING_REASON_CODES = {
    "CorrectNow", "AcceptKnownLimitation", "RejectFinding", "ReturnSlice",
}
_REVIEW_ROUTES = {
    ("AwaitingIntegration", "Integration", "ValidateOnly"): "AwaitingReview",
    ("AwaitingIntegration", "Integration", "NeedsReplan"): "NeedsReplan",
    ("AwaitingReview", "IndependentImplementation", "Approve"): "MergeReady",
    ("AwaitingReview", "IndependentImplementation", "RequestChanges"): "AwaitingArchitect",
}
_REVIEW_REVIEWER_ROLES = {
    "Integration": "IntegrationAgent",
    "IndependentImplementation": "IndependentImplementationReviewer",
}


class OperationalStateError(Exception):
    """Base class for closed operational-state failures."""


class InvalidRecord(OperationalStateError):
    pass


class InvalidTransition(OperationalStateError):
    pass


class StaleState(OperationalStateError):
    pass


class IdempotencyConflict(OperationalStateError):
    pass


class ResourceConflict(OperationalStateError):
    pass


class ResourceBusy(OperationalStateError):
    pass


class SensitiveMaterialRejected(InvalidRecord):
    pass


class RecoveryConflict(OperationalStateError):
    pass


@dataclass(frozen=True)
class Actor:
    actor_type: str
    actor_id: str
    correlation_id: str
    causation_event_id: int | None = None


def canonical_json(value: Any, *, root_type: type | tuple[type, ...] | None = None) -> str:
    """Return bounded canonical UTF-8 JSON after structural safety checks."""
    if root_type is not None and (not isinstance(value, root_type) or isinstance(value, bool)):
        raise InvalidRecord("JSON root has the wrong type")
    _reject_unsafe_json(value)
    try:
        encoded = json.dumps(
            value, sort_keys=True, separators=(",", ":"), allow_nan=False, ensure_ascii=False
        )
        encoded_bytes = encoded.encode("utf-8")
    except (TypeError, ValueError, UnicodeEncodeError) as error:
        raise InvalidRecord("value is not canonical JSON") from error
    if len(encoded_bytes) > MAX_JSON_BYTES:
        raise InvalidRecord("canonical JSON exceeds the one MiB row limit")
    return encoded


def canonical_digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def context_policy_digest(policy: Mapping[str, Any]) -> str:
    normalized = validate_context_policy(policy)
    return canonical_digest(normalized)


def validate_context_policy(
    policy: Mapping[str, Any],
    *,
    configured_context_limit: int | None = None,
    starting_input_tokens: int | None = None,
) -> dict[str, int]:
    fields = {
        "minimum_context_tokens", "output_reserve_tokens", "warning_remaining_tokens",
        "checkpoint_remaining_tokens", "stop_remaining_tokens",
    }
    normalized = _closed_mapping(policy, fields, "context policy")
    for field in fields:
        normalized[field] = _positive_int(normalized[field], field)
    warning = normalized["warning_remaining_tokens"]
    checkpoint = normalized["checkpoint_remaining_tokens"]
    stop = normalized["stop_remaining_tokens"]
    reserve = normalized["output_reserve_tokens"]
    if not warning > checkpoint > stop >= reserve:
        raise InvalidRecord("context policy thresholds are not strictly ordered")
    if configured_context_limit is not None:
        configured_context_limit = _positive_int(configured_context_limit, "configured context limit")
        required = normalized["minimum_context_tokens"] + reserve
        if configured_context_limit < required or configured_context_limit <= warning:
            raise InvalidRecord("configured context limit does not satisfy the materialized policy")
        if starting_input_tokens is not None:
            starting_input_tokens = _nonnegative_int(starting_input_tokens, "starting input")
            if starting_input_tokens + reserve > configured_context_limit:
                raise InvalidRecord("starting input plus output reserve does not fit")
    elif starting_input_tokens is not None:
        raise InvalidRecord("starting-input fit requires a configured context limit")
    return {key: int(normalized[key]) for key in sorted(fields)}


def validate_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, Mapping):
        raise InvalidRecord("payload must be an object")
    kind = payload.get("kind")
    shapes: dict[str, set[str]] = {
        "state": {"kind", "entity_type", "entity_id", "state", "version"},
        "claim": {"kind", "packet_id", "lease_id", "lock_ids"},
        "reference": {"kind", "provider", "reference_name"},
        "evidence-reference": {"kind", "evidence_id", "digest", "source_reference"},
        "measurement-reference": {"kind", "record_id", "measurement_kind"},
        "redacted-text": {"kind", "text", "redaction_status", "redaction_receipt_reference"},
        "notification": {
            "kind", "event_id", "audience", "severity", "subject_reference",
            "evidence_references", "next_action_reference",
        },
        "reason": {"kind", "reason_code", "detail_reference"},
        "review-finding": {
            "kind", "finding_id", "criterion_reference", "evidence", "disposition",
        },
    }
    if kind not in shapes:
        raise InvalidRecord("payload kind is not a closed production variant")
    value = _closed_mapping(payload, shapes[str(kind)], f"{kind} payload")
    if kind == "state":
        for name in ("entity_type", "entity_id", "state"):
            value[name] = _text(value[name], name)
        if value["entity_type"] not in _ENTITY_STATES or value["state"] not in _ENTITY_STATES[value["entity_type"]]:
            raise InvalidRecord("state payload does not name a declared entity state")
        value["version"] = _positive_int(value["version"], "version")
    elif kind == "claim":
        value["packet_id"] = _text(value["packet_id"], "packet_id")
        value["lease_id"] = _text(value["lease_id"], "lease_id")
        value["lock_ids"] = _sorted_unique_text(value["lock_ids"], "lock_ids")
    elif kind == "reference":
        value["provider"] = _provider(value["provider"])
        value["reference_name"] = _reference_name(value["reference_name"])
    elif kind == "evidence-reference":
        value["evidence_id"] = _text(value["evidence_id"], "evidence_id")
        value["digest"] = _digest(value["digest"], "digest")
        value["source_reference"] = _optional_text(value["source_reference"], "source_reference")
    elif kind == "measurement-reference":
        value["record_id"] = _text(value["record_id"], "record_id")
        value["measurement_kind"] = _text(value["measurement_kind"], "measurement_kind")
    elif kind == "redacted-text":
        if value["redaction_status"] != "Redacted":
            raise InvalidRecord("redacted text requires Redacted status")
        if not isinstance(value["text"], str):
            raise InvalidRecord("redacted text must be text")
        value["redaction_receipt_reference"] = _text(
            value["redaction_receipt_reference"], "redaction_receipt_reference"
        )
    elif kind == "notification":
        value["event_id"] = _positive_int(value["event_id"], "event_id")
        for name in ("audience", "subject_reference", "next_action_reference"):
            value[name] = _text(value[name], name)
        if value["severity"] not in {
            "Informational", "ActionNeeded", "CompletionReady", "CompletionSummary"
        }:
            raise InvalidRecord("notification payload severity is invalid")
        value["evidence_references"] = _sorted_unique_text(
            value["evidence_references"], "evidence_references"
        )
    elif kind == "review-finding":
        value["finding_id"] = _text(value["finding_id"], "finding_id")
        value["criterion_reference"] = _text(value["criterion_reference"], "criterion_reference")
        evidence = validate_payload(value["evidence"])
        if evidence["kind"] != "evidence-reference":
            raise InvalidRecord("review finding evidence must be an evidence-reference payload")
        value["evidence"] = evidence
        disposition = validate_payload(value["disposition"])
        if disposition["kind"] != "reason":
            raise InvalidRecord("review finding disposition must be a reason payload")
        if disposition["reason_code"] not in _REVIEW_FINDING_REASON_CODES:
            raise InvalidRecord("review finding disposition reason_code is invalid")
        if (
            disposition["reason_code"] == "AcceptKnownLimitation"
            and disposition["detail_reference"] is None
        ):
            raise InvalidRecord(
                "AcceptKnownLimitation disposition requires a detail_reference"
            )
        value["disposition"] = disposition
    else:
        value["reason_code"] = _text(value["reason_code"], "reason_code")
        value["detail_reference"] = _optional_text(value["detail_reference"], "detail_reference")
    canonical_json(value, root_type=dict)
    return value


def validate_measurement(value: Mapping[str, Any]) -> dict[str, Any]:
    result = _closed_mapping(
        value, {"value", "quality", "confidence", "source_reference", "observed_at"}, "measurement"
    )
    qualities = {"RuntimeReported", "TokenizerCounted", "Estimated", "Unavailable"}
    confidences = {"Exact", "High", "Medium", "Low", "Unavailable"}
    if result["quality"] not in qualities or result["confidence"] not in confidences:
        raise InvalidRecord("measurement quality or confidence is invalid")
    result["observed_at"] = _timestamp(result["observed_at"], "measurement observed_at")
    if result["quality"] == "Unavailable":
        if result["value"] is not None or result["source_reference"] is not None or result["confidence"] != "Unavailable":
            raise InvalidRecord("unavailable measurement must retain null value/source")
    else:
        result["value"] = _nonnegative_int(result["value"], "measurement value")
        result["source_reference"] = _text(result["source_reference"], "measurement source")
        if result["confidence"] == "Unavailable":
            raise InvalidRecord("available measurement cannot have unavailable confidence")
        if result["quality"] in {"RuntimeReported", "TokenizerCounted"} and result["confidence"] not in {"Exact", "High"}:
            raise InvalidRecord("reported/tokenizer measurement requires exact or high confidence")
        if result["quality"] == "Estimated" and result["confidence"] not in {"High", "Medium", "Low"}:
            raise InvalidRecord("estimated measurement confidence is invalid")
    return result


def validate_cost_measurement(value: Mapping[str, Any]) -> dict[str, Any]:
    result = _closed_mapping(
        value,
        {"status", "amount", "currency", "quality", "confidence", "source_reference", "observed_at"},
        "cost measurement",
    )
    result["observed_at"] = _timestamp(result["observed_at"], "cost observed_at")
    status = result["status"]
    if status in {"Billed", "Estimated"}:
        result["amount"] = _decimal_text(result["amount"], "cost amount")
        if not isinstance(result["currency"], str) or _CURRENCY.fullmatch(result["currency"]) is None:
            raise InvalidRecord("cost currency must be three uppercase letters")
        result["source_reference"] = _text(result["source_reference"], "cost source")
        if status == "Billed":
            if result["quality"] not in {"RuntimeReported", "ProviderReported"} or result["confidence"] not in {"Exact", "High"}:
                raise InvalidRecord("billed cost quality/confidence is invalid")
        elif result["quality"] != "Estimated" or result["confidence"] not in {"High", "Medium", "Low"}:
            raise InvalidRecord("estimated cost quality/confidence is invalid")
    elif status == "NotBilled":
        if result["amount"] is not None or result["currency"] is not None:
            raise InvalidRecord("not-billed cost has no amount or currency")
        result["source_reference"] = _text(result["source_reference"], "cost source")
        if result["quality"] not in {"RuntimeReported", "ProviderReported"} or result["confidence"] not in {"Exact", "High"}:
            raise InvalidRecord("not-billed cost quality/confidence is invalid")
    elif status == "Unknown":
        if any(result[name] is not None for name in ("amount", "currency", "source_reference")):
            raise InvalidRecord("unknown cost retains no amount, currency, or source")
        if result["quality"] != "Unavailable" or result["confidence"] != "Unavailable":
            raise InvalidRecord("unknown cost must be unavailable")
    else:
        raise InvalidRecord("cost status is invalid")
    return result


def preferred_measurement(existing: Mapping[str, Any], proposed: Mapping[str, Any]) -> dict[str, Any]:
    """Enforce runtime-reported precedence for the same measurement period."""
    current = validate_measurement(existing)
    candidate = validate_measurement(proposed)
    if current["observed_at"] == candidate["observed_at"]:
        rank = {"Unavailable": 0, "Estimated": 1, "TokenizerCounted": 2, "RuntimeReported": 3}
        if rank[candidate["quality"]] < rank[current["quality"]]:
            raise InvalidRecord("lower-quality measurement cannot replace the retained value")
    return candidate


class OperationalStateStore:
    """The sole schema-4 writer/read foundation behind a validated runtime."""

    def __init__(self, config: RuntimeConfig) -> None:
        if not isinstance(config, RuntimeConfig):
            raise TypeError("OperationalStateStore requires RuntimeConfig")
        self.config = RuntimeConfig(config.runtime_dir)
        self._foundation = SQLiteFoundation(self.config)

    def health(self):
        try:
            return self._foundation.health()
        except sqlite3.OperationalError as error:
            self._raise_sqlite(error)

    def record_binding(self, binding, idempotency_key, actor, now):
        row = self._binding(binding, now)
        return self._append_one("project_bindings", "binding_id", row, "ProjectBinding", "ProjectBindingRecorded", idempotency_key, actor, now)

    def record_secret_reference(self, observation, idempotency_key, actor, now):
        row = self._secret_reference(observation)
        return self._append_one("secret_reference_observations", "secret_reference_observation_id", row, "SecretReferenceObservation", "SecretReferenceObserved", idempotency_key, actor, now)

    def record_graph_projection(self, graph, work_items, idempotency_key, actor, now):
        timestamp = _timestamp(now, "now")
        graph_row = self._graph(graph, timestamp)
        if not isinstance(work_items, Sequence) or isinstance(work_items, (str, bytes, bytearray)):
            raise InvalidRecord("work_items must be an array")
        item_rows = [self._work_item(item, graph_row["graph_projection_id"], timestamp) for item in work_items]
        ids = [row["work_item_id"] for row in item_rows]
        if ids != sorted(set(ids)):
            raise InvalidRecord("work_items must be sorted and unique by work_item_id")
        payload = {"graph": graph_row, "work_items": item_rows}

        def write(connection: sqlite3.Connection) -> None:
            self._insert(connection, "graph_projections", graph_row)
            for item_row in item_rows:
                self._insert(connection, "work_items", item_row)

        return self._append(
            "record_graph_projection", payload, "GraphProjection",
            graph_row["graph_projection_id"], "GraphProjectionRecorded",
            idempotency_key, actor, timestamp, write,
        )

    def create_run(self, run, idempotency_key, actor, now):
        row = self._run(run, now)
        return self._append_one("runs", "run_id", row, "Run", "RunCreated", idempotency_key, actor, now)

    def transition_run(
        self, run_id, expected_version, target_state, reason_payload,
        idempotency_key, actor, now,
    ):
        run_id = _text(run_id, "run_id")
        expected_version = _positive_int(expected_version, "expected_version")
        target_state = _text(target_state, "target_state")
        if target_state not in _ENTITY_STATES["Run"]:
            raise InvalidTransition("target run state is not declared")
        reason = validate_payload(reason_payload)
        if reason["kind"] != "reason":
            raise InvalidRecord("run transition reason must be a reason payload")
        key = _text(idempotency_key, "idempotency_key")
        actor_value = _actor(actor)
        timestamp = _timestamp(now, "now")
        facts = {
            "run_id": run_id,
            "expected_version": expected_version,
            "target_state": target_state,
            "reason": reason,
        }
        fingerprint = _fingerprint("transition_run", facts, actor_value)

        try:
            with self._foundation._connection() as connection:
                connection.execute("BEGIN IMMEDIATE")
                replay = self._replay(connection, key, fingerprint)
                if replay is not None:
                    connection.commit()
                    return replay
                current = connection.execute(
                    "SELECT state,version FROM runs WHERE run_id=?", (run_id,)
                ).fetchone()
                if current is None:
                    raise InvalidRecord("unknown run")
                source_state, current_version = str(current[0]), int(current[1])
                if current_version != expected_version:
                    raise StaleState("run version is stale")
                if target_state not in _RUN_TRANSITIONS[source_state]:
                    raise InvalidTransition("run transition is not permitted")
                before = _state_payload("Run", run_id, source_state, current_version)
                after = _state_payload(
                    "Run", run_id, target_state, expected_version + 1
                )
                updated = connection.execute(
                    "UPDATE runs SET state=?,updated_at=?,version=? "
                    "WHERE run_id=? AND version=?",
                    (target_state, timestamp, expected_version + 1, run_id, expected_version),
                )
                if updated.rowcount != 1:
                    raise StaleState("run version is stale")
                self._insert_run_state_event(
                    connection, key, fingerprint, actor_value, timestamp,
                    run_id, before, after, reason,
                )
                connection.commit()
                return after
        except sqlite3.IntegrityError as error:
            raise InvalidRecord("run transition violates a durable constraint") from error
        except sqlite3.OperationalError as error:
            self._raise_sqlite(error)

    def materialize_packet(self, packet, idempotency_key, actor, now):
        row = self._packet(packet, now)
        return self._append_one("packets", "packet_id", row, "Packet", "PacketMaterialized", idempotency_key, actor, now)

    def transition_packet_eligibility(
        self, packet_id, expected_version, target_state, reason_payload,
        idempotency_key, actor, now,
    ):
        packet_id = _text(packet_id, "packet_id")
        expected_version = _positive_int(expected_version, "expected_version")
        target_state = _text(target_state, "target_state")
        if target_state not in _ENTITY_STATES["Packet"]:
            raise InvalidTransition("target packet state is not declared")
        reason = validate_payload(reason_payload)
        if reason["kind"] != "reason":
            raise InvalidRecord("packet eligibility reason must be a reason payload")
        key = _text(idempotency_key, "idempotency_key")
        actor_value = _actor(actor)
        timestamp = _timestamp(now, "now")
        facts = {
            "packet_id": packet_id,
            "expected_version": expected_version,
            "target_state": target_state,
            "reason": reason,
        }
        fingerprint = _fingerprint(
            "transition_packet_eligibility", facts, actor_value
        )

        try:
            with self._foundation._connection() as connection:
                connection.execute("BEGIN IMMEDIATE")
                replay = self._replay(connection, key, fingerprint)
                if replay is not None:
                    connection.commit()
                    return replay
                current = connection.execute(
                    "SELECT state,version FROM packets WHERE packet_id=?", (packet_id,)
                ).fetchone()
                if current is None:
                    raise InvalidRecord("unknown packet")
                source_state, current_version = str(current[0]), int(current[1])
                if current_version != expected_version:
                    raise StaleState("packet version is stale")
                if target_state not in _PACKET_ELIGIBILITY_TRANSITIONS.get(
                    source_state, set()
                ):
                    raise InvalidTransition("packet eligibility transition is not permitted")
                before = _state_payload("Packet", packet_id, source_state, current_version)
                after = _state_payload(
                    "Packet", packet_id, target_state, expected_version + 1
                )
                updated = connection.execute(
                    "UPDATE packets SET state=?,updated_at=?,version=? "
                    "WHERE packet_id=? AND version=?",
                    (target_state, timestamp, expected_version + 1, packet_id, expected_version),
                )
                if updated.rowcount != 1:
                    raise StaleState("packet version is stale")
                self._insert_packet_state_event(
                    connection, key, fingerprint, actor_value, timestamp,
                    packet_id, before, after, reason,
                )
                connection.commit()
                return after
        except sqlite3.IntegrityError as error:
            raise InvalidRecord("packet eligibility transition violates a durable constraint") from error
        except sqlite3.OperationalError as error:
            self._raise_sqlite(error)

    def claim_packet_assignment(
        self, packet_id, expected_version, lease_request, lock_requests,
        attempt_request, reason_payload, idempotency_key, actor, now,
    ):
        packet_id = _text(packet_id, "packet_id")
        expected_version = _positive_int(expected_version, "expected_version")
        lease = _assignment_lease_request(lease_request)
        locks = _assignment_lock_requests(lock_requests)
        attempt = _assignment_attempt_request(attempt_request)
        reason = validate_payload(reason_payload)
        if reason["kind"] != "reason":
            raise InvalidRecord("assignment claim reason must be a reason payload")
        key = _text(idempotency_key, "idempotency_key")
        actor_value = _actor(actor)
        timestamp = _timestamp(now, "now")
        facts = {
            "attempt": attempt,
            "expected_version": expected_version,
            "lease": lease,
            "locks": locks,
            "packet_id": packet_id,
            "reason": reason,
        }
        fingerprint = _fingerprint("claim_packet_assignment", facts, actor_value)

        try:
            with self._foundation._connection() as connection:
                connection.execute("BEGIN IMMEDIATE")
                replay = self._replay(connection, key, fingerprint)
                if replay is not None:
                    connection.commit()
                    return replay

                if lease["expires_at"] <= timestamp:
                    raise InvalidRecord("assignment lease expiry must follow observation time")

                packet = connection.execute(
                    "SELECT state,version,run_id,base_commit,executor_class,resource_claims_json "
                    "FROM packets WHERE packet_id=?",
                    (packet_id,),
                ).fetchone()
                if packet is None:
                    raise InvalidRecord("unknown packet")
                source_state, current_version = str(packet[0]), int(packet[1])
                if current_version != expected_version:
                    raise StaleState("packet version is stale")
                if source_state != "Dispatchable":
                    raise InvalidTransition("assignment claim requires a Dispatchable packet")

                run_id = str(packet[2])
                run = connection.execute(
                    "SELECT state,run_fingerprint FROM runs WHERE run_id=?", (run_id,)
                ).fetchone()
                if run is None:
                    raise InvalidRecord("packet run is missing")
                if str(run[0]) != "Running":
                    raise InvalidTransition("assignment claim requires a Running run")

                declared_resources = json.loads(str(packet[5]))
                requested_resources = [item["resource_key"] for item in locks]
                if requested_resources != declared_resources:
                    raise InvalidRecord("assignment locks must exactly cover declared resources")

                if connection.execute(
                    "SELECT 1 FROM leases WHERE lease_id=?", (lease["lease_id"],)
                ).fetchone() is not None:
                    raise InvalidRecord("assignment lease_id already exists")
                if connection.execute(
                    "SELECT 1 FROM leases WHERE claim_key=?", (key,)
                ).fetchone() is not None:
                    raise InvalidRecord("assignment claim_key already exists without replay")
                for lock_id in sorted(item["lock_id"] for item in locks):
                    if connection.execute(
                        "SELECT 1 FROM resource_locks WHERE lock_id=?", (lock_id,)
                    ).fetchone() is not None:
                        raise InvalidRecord("assignment lock_id already exists")
                if connection.execute(
                    "SELECT 1 FROM attempts WHERE attempt_id=?", (attempt["attempt_id"],)
                ).fetchone() is not None:
                    raise InvalidRecord("assignment attempt_id already exists")
                if connection.execute(
                    "SELECT 1 FROM attempts WHERE packet_id=? AND attempt_number=1", (packet_id,)
                ).fetchone() is not None:
                    raise InvalidRecord("packet already has an Initial attempt")

                if connection.execute(
                    "SELECT 1 FROM leases WHERE packet_id=? AND state='Active'", (packet_id,)
                ).fetchone() is not None:
                    raise ResourceConflict("packet already has an Active lease")
                if connection.execute(
                    "SELECT 1 FROM leases WHERE worktree_path=? AND state='Active'",
                    (lease["worktree_path"],),
                ).fetchone() is not None:
                    raise ResourceConflict("worktree already has an Active lease")
                if requested_resources:
                    requested_resource_set = set(requested_resources)
                    active_resources = connection.execute(
                        "SELECT resource_key FROM resource_locks WHERE state='Active' "
                        "ORDER BY resource_key"
                    ).fetchall()
                    conflicting_resources = [
                        str(row[0]) for row in active_resources
                        if str(row[0]) in requested_resource_set
                    ]
                    if conflicting_resources:
                        raise ResourceConflict(
                            f"resource already has an Active lock: {conflicting_resources[0]}"
                        )

                packet_before = _state_payload(
                    "Packet", packet_id, source_state, current_version
                )
                packet_after = _state_payload(
                    "Packet", packet_id, "Leased", expected_version + 1
                )
                lease_row = {
                    "lease_id": lease["lease_id"],
                    "packet_id": packet_id,
                    "run_id": run_id,
                    "claim_key": key,
                    "run_fingerprint": str(run[1]),
                    "base_commit": str(packet[3]),
                    "worktree_path": lease["worktree_path"],
                    "executor_route": lease["executor_route"],
                    "holder_id": lease["holder_id"],
                    "state": "Active",
                    "acquired_at": timestamp,
                    "expires_at": lease["expires_at"],
                    "heartbeat_at": timestamp,
                    "released_at": None,
                    "version": 1,
                }
                lock_rows = [
                    {
                        "lock_id": item["lock_id"],
                        "resource_key": item["resource_key"],
                        "lock_kind": item["lock_kind"],
                        "packet_id": packet_id,
                        "lease_id": lease["lease_id"],
                        "state": "Active",
                        "acquired_at": timestamp,
                        "expires_at": lease["expires_at"],
                        "released_at": None,
                        "version": 1,
                    }
                    for item in locks
                ]
                attempt_row = self._attempt(
                    {
                        "attempt_id": attempt["attempt_id"],
                        "packet_id": packet_id,
                        "lease_id": lease["lease_id"],
                        "attempt_number": 1,
                        "attempt_kind": "Initial",
                        "executor_class": str(packet[4]),
                        "model_identity": attempt["model_identity"],
                        "runtime_identity": attempt["runtime_identity"],
                        "state": "Planned",
                        "result_commit": None,
                        "correction_for_review_id": None,
                        "started_at": None,
                        "finished_at": None,
                    },
                    timestamp,
                )
                lock_ids = sorted(item["lock_id"] for item in locks)
                result = {
                    "attempt": _state_payload(
                        "Attempt", attempt["attempt_id"], "Planned", 1
                    ),
                    "claim": validate_payload(
                        {
                            "kind": "claim",
                            "lease_id": lease["lease_id"],
                            "lock_ids": lock_ids,
                            "packet_id": packet_id,
                        }
                    ),
                    "lease": _state_payload(
                        "Lease", lease["lease_id"], "Active", 1
                    ),
                    "locks": [
                        _state_payload("ResourceLock", lock_id, "Active", 1)
                        for lock_id in lock_ids
                    ],
                    "packet": packet_after,
                }
                canonical_json(result, root_type=dict)

                updated = connection.execute(
                    "UPDATE packets SET state='Leased',updated_at=?,version=? "
                    "WHERE packet_id=? AND version=? AND state='Dispatchable'",
                    (timestamp, expected_version + 1, packet_id, expected_version),
                )
                if updated.rowcount != 1:
                    raise StaleState("packet version is stale")
                self._insert(connection, "leases", lease_row)
                for lock_row in lock_rows:
                    self._insert(connection, "resource_locks", lock_row)
                self._insert(connection, "attempts", attempt_row)
                self._insert_packet_claim_event(
                    connection, key, fingerprint, actor_value, timestamp,
                    packet_id, packet_before, result, reason,
                )
                connection.commit()
                return result
        except sqlite3.IntegrityError as error:
            raise InvalidRecord("assignment claim violates a durable constraint") from error
        except sqlite3.OperationalError as error:
            self._raise_sqlite(error)

    def start_attempt_execution(
        self, attempt_id, expected_attempt_version, expected_packet_version,
        execution_handle, expected_result, reason_payload,
        idempotency_key, actor, now,
    ):
        attempt_id = _text(attempt_id, "attempt_id")
        expected_attempt_version = _positive_int(
            expected_attempt_version, "expected_attempt_version"
        )
        expected_packet_version = _positive_int(
            expected_packet_version, "expected_packet_version"
        )
        execution_handle = _text(execution_handle, "execution_handle")
        expected_result = _text(expected_result, "expected_result")
        reason = validate_payload(reason_payload)
        if reason["kind"] != "reason":
            raise InvalidRecord("execution start reason must be a reason payload")
        key = _text(idempotency_key, "idempotency_key")
        actor_value = _actor(actor)
        timestamp = _timestamp(now, "now")
        facts = {
            "attempt_id": attempt_id,
            "execution_handle": execution_handle,
            "expected_attempt_version": expected_attempt_version,
            "expected_packet_version": expected_packet_version,
            "expected_result": expected_result,
            "reason": reason,
        }
        fingerprint = _fingerprint("start_attempt_execution", facts, actor_value)

        try:
            with self._foundation._connection() as connection:
                connection.execute("BEGIN IMMEDIATE")
                replay = self._replay(connection, key, fingerprint)
                if replay is not None:
                    connection.commit()
                    return replay

                attempt = connection.execute(
                    "SELECT state,version,packet_id,lease_id FROM attempts WHERE attempt_id=?",
                    (attempt_id,),
                ).fetchone()
                if attempt is None:
                    raise InvalidRecord("unknown attempt")
                attempt_state, attempt_version = str(attempt[0]), int(attempt[1])
                if attempt_version != expected_attempt_version:
                    raise StaleState("attempt version is stale")
                if attempt_state != "Planned":
                    raise InvalidTransition("execution start requires a Planned attempt")

                packet_id = str(attempt[2])
                packet = connection.execute(
                    "SELECT state,version,run_id FROM packets WHERE packet_id=?", (packet_id,)
                ).fetchone()
                if packet is None:
                    raise InvalidRecord("attempt packet is missing")
                packet_state, packet_version = str(packet[0]), int(packet[1])
                if packet_version != expected_packet_version:
                    raise StaleState("packet version is stale")
                if packet_state != "Leased":
                    raise InvalidTransition("execution start requires a Leased packet")

                lease_id = str(attempt[3])
                lease = connection.execute(
                    "SELECT packet_id,run_id,state,version,expires_at FROM leases WHERE lease_id=?",
                    (lease_id,),
                ).fetchone()
                if lease is None:
                    raise InvalidRecord("attempt lease is missing")
                run_id = str(packet[2])
                if str(lease[0]) != packet_id or str(lease[1]) != run_id:
                    raise InvalidRecord("attempt, packet, and lease relationship is invalid")
                if str(lease[2]) != "Active":
                    raise InvalidTransition("execution start requires an Active lease")

                run = connection.execute(
                    "SELECT state FROM runs WHERE run_id=?", (run_id,)
                ).fetchone()
                if run is None:
                    raise InvalidRecord("packet parent run is missing")
                if str(run[0]) != "Running":
                    raise InvalidTransition("execution start requires a Running parent run")
                if str(lease[4]) <= timestamp:
                    raise InvalidTransition("execution start requires an unexpired lease")

                handle_owner = connection.execute(
                    "SELECT attempt_id FROM attempts WHERE execution_handle=?",
                    (execution_handle,),
                ).fetchone()
                if handle_owner is not None:
                    raise ResourceConflict("execution handle is already bound to another attempt")

                attempt_before = _state_payload(
                    "Attempt", attempt_id, attempt_state, attempt_version
                )
                packet_before = _state_payload(
                    "Packet", packet_id, packet_state, packet_version
                )
                attempt_after = _state_payload(
                    "Attempt", attempt_id, "Running", expected_attempt_version + 1
                )
                packet_after = _state_payload(
                    "Packet", packet_id, "Running", expected_packet_version + 1
                )
                result = {
                    "attempt": attempt_after,
                    "execution": {
                        "attempt_id": attempt_id,
                        "execution_handle": execution_handle,
                        "expected_result": expected_result,
                        "heartbeat_at": timestamp,
                        "started_at": timestamp,
                    },
                    "lease": _state_payload(
                        "Lease", lease_id, "Active", int(lease[3])
                    ),
                    "packet": packet_after,
                }
                before = {"attempt": attempt_before, "packet": packet_before}
                canonical_json(before, root_type=dict)
                canonical_json(result, root_type=dict)

                updated_attempt = connection.execute(
                    "UPDATE attempts SET state='Running',execution_handle=?,expected_result=?,"
                    "started_at=?,heartbeat_at=?,updated_at=?,version=? "
                    "WHERE attempt_id=? AND version=? AND state='Planned'",
                    (
                        execution_handle, expected_result, timestamp, timestamp, timestamp,
                        expected_attempt_version + 1, attempt_id, expected_attempt_version,
                    ),
                )
                if updated_attempt.rowcount != 1:
                    raise StaleState("attempt version is stale")
                updated_packet = connection.execute(
                    "UPDATE packets SET state='Running',updated_at=?,version=? "
                    "WHERE packet_id=? AND version=? AND state='Leased'",
                    (
                        timestamp, expected_packet_version + 1,
                        packet_id, expected_packet_version,
                    ),
                )
                if updated_packet.rowcount != 1:
                    raise StaleState("packet version is stale")
                self._insert_attempt_state_event(
                    connection, key, fingerprint, actor_value, timestamp,
                    attempt_id, before, result, reason,
                )
                connection.commit()
                return result
        except sqlite3.IntegrityError as error:
            if "attempts.execution_handle" in str(error):
                raise ResourceConflict(
                    "execution handle is already bound to another attempt"
                ) from error
            raise InvalidRecord("execution start violates a durable constraint") from error
        except sqlite3.OperationalError as error:
            self._raise_sqlite(error)

    def heartbeat_attempt_execution(
        self, attempt_id, expected_attempt_version, expected_lease_version,
        execution_handle, new_expires_at, reason_payload,
        idempotency_key, actor, now,
    ):
        attempt_id = _text(attempt_id, "attempt_id")
        expected_attempt_version = _positive_int(
            expected_attempt_version, "expected_attempt_version"
        )
        expected_lease_version = _positive_int(
            expected_lease_version, "expected_lease_version"
        )
        execution_handle = _text(execution_handle, "execution_handle")
        new_expiry = _timestamp(new_expires_at, "new_expires_at")
        reason = validate_payload(reason_payload)
        if reason["kind"] != "reason":
            raise InvalidRecord("execution heartbeat reason must be a reason payload")
        key = _text(idempotency_key, "idempotency_key")
        actor_value = _actor(actor)
        timestamp = _timestamp(now, "now")
        facts = {
            "attempt_id": attempt_id,
            "execution_handle": execution_handle,
            "expected_attempt_version": expected_attempt_version,
            "expected_lease_version": expected_lease_version,
            "new_expires_at": new_expiry,
            "reason": reason,
        }
        fingerprint = _fingerprint(
            "heartbeat_attempt_execution", facts, actor_value
        )

        try:
            with self._foundation._connection() as connection:
                connection.execute("BEGIN IMMEDIATE")
                replay = self._replay(connection, key, fingerprint)
                if replay is not None:
                    connection.commit()
                    return replay

                attempt = connection.execute(
                    "SELECT state,version,packet_id,lease_id,execution_handle,heartbeat_at "
                    "FROM attempts WHERE attempt_id=?",
                    (attempt_id,),
                ).fetchone()
                if attempt is None:
                    raise InvalidRecord("unknown attempt")
                attempt_state, attempt_version = str(attempt[0]), int(attempt[1])
                if attempt_version != expected_attempt_version:
                    raise StaleState("attempt version is stale")
                if attempt_state != "Running":
                    raise InvalidTransition("execution heartbeat requires a Running attempt")
                if str(attempt[4]) != execution_handle:
                    raise StaleState("execution handle does not match the Running attempt")

                packet_id = str(attempt[2])
                packet = connection.execute(
                    "SELECT state,run_id FROM packets WHERE packet_id=?", (packet_id,)
                ).fetchone()
                if packet is None:
                    raise InvalidRecord("attempt packet is missing")
                if str(packet[0]) != "Running":
                    raise InvalidTransition("execution heartbeat requires a Running packet")

                lease_id = str(attempt[3])
                lease = connection.execute(
                    "SELECT packet_id,run_id,state,version,expires_at,heartbeat_at "
                    "FROM leases WHERE lease_id=?",
                    (lease_id,),
                ).fetchone()
                if lease is None:
                    raise InvalidRecord("attempt lease is missing")
                run_id = str(packet[1])
                if str(lease[0]) != packet_id or str(lease[1]) != run_id:
                    raise InvalidRecord("attempt, packet, and lease relationship is invalid")
                lease_version = int(lease[3])
                if lease_version != expected_lease_version:
                    raise StaleState("lease version is stale")
                if str(lease[2]) != "Active":
                    raise InvalidTransition("execution heartbeat requires an Active lease")

                run = connection.execute(
                    "SELECT state FROM runs WHERE run_id=?", (run_id,)
                ).fetchone()
                if run is None:
                    raise InvalidRecord("packet parent run is missing")
                if str(run[0]) != "Running":
                    raise InvalidTransition("execution heartbeat requires a Running parent run")

                old_attempt_heartbeat = str(attempt[5])
                old_expiry, old_lease_heartbeat = str(lease[4]), str(lease[5])
                if timestamp <= old_attempt_heartbeat or timestamp <= old_lease_heartbeat:
                    raise InvalidTransition("execution heartbeat time must advance both heartbeats")
                if new_expiry <= timestamp:
                    raise InvalidTransition("heartbeat expiry must be strictly later than now")
                if new_expiry <= old_expiry:
                    raise InvalidTransition("execution heartbeat expiry must advance the lease")

                before = {
                    "attempt": _state_payload(
                        "Attempt", attempt_id, "Running", attempt_version
                    ),
                    "execution": {
                        "attempt_id": attempt_id,
                        "execution_handle": execution_handle,
                        "heartbeat_at": old_attempt_heartbeat,
                    },
                    "lease": _state_payload(
                        "Lease", lease_id, "Active", lease_version
                    ),
                    "renewal": {
                        "expires_at": old_expiry,
                        "heartbeat_at": old_lease_heartbeat,
                        "lease_id": lease_id,
                    },
                }
                result = {
                    "attempt": _state_payload(
                        "Attempt", attempt_id, "Running", expected_attempt_version + 1
                    ),
                    "execution": {
                        "attempt_id": attempt_id,
                        "execution_handle": execution_handle,
                        "heartbeat_at": timestamp,
                    },
                    "lease": _state_payload(
                        "Lease", lease_id, "Active", expected_lease_version + 1
                    ),
                    "renewal": {
                        "expires_at": new_expiry,
                        "heartbeat_at": timestamp,
                        "lease_id": lease_id,
                    },
                }
                canonical_json(before, root_type=dict)
                canonical_json(result, root_type=dict)

                updated_attempt = connection.execute(
                    "UPDATE attempts SET heartbeat_at=?,updated_at=?,version=? "
                    "WHERE attempt_id=? AND version=? AND state='Running' "
                    "AND execution_handle=?",
                    (
                        timestamp, timestamp, expected_attempt_version + 1,
                        attempt_id, expected_attempt_version, execution_handle,
                    ),
                )
                if updated_attempt.rowcount != 1:
                    raise StaleState("attempt version is stale")
                updated_lease = connection.execute(
                    "UPDATE leases SET expires_at=?,heartbeat_at=?,version=? "
                    "WHERE lease_id=? AND version=? AND state='Active'",
                    (
                        new_expiry, timestamp, expected_lease_version + 1,
                        lease_id, expected_lease_version,
                    ),
                )
                if updated_lease.rowcount != 1:
                    raise StaleState("lease version is stale")
                self._insert_lease_heartbeat_event(
                    connection, key, fingerprint, actor_value, timestamp,
                    lease_id, before, result, reason,
                )
                connection.commit()
                return result
        except sqlite3.IntegrityError as error:
            raise InvalidRecord(
                "execution heartbeat violates a durable constraint"
            ) from error
        except sqlite3.OperationalError as error:
            self._raise_sqlite(error)

    def finish_attempt_execution(
        self, attempt_id, expected_attempt_version, expected_packet_version,
        expected_lease_version, execution_handle, outcome, result_commit,
        completion_evidence_reference, reason_payload,
        idempotency_key, actor, now,
    ):
        attempt_id = _text(attempt_id, "attempt_id")
        expected_attempt_version = _positive_int(
            expected_attempt_version, "expected_attempt_version"
        )
        expected_packet_version = _positive_int(
            expected_packet_version, "expected_packet_version"
        )
        expected_lease_version = _positive_int(
            expected_lease_version, "expected_lease_version"
        )
        execution_handle = _text(execution_handle, "execution_handle")
        outcome = _text(outcome, "outcome")
        outcome_mapping = {
            "Succeeded": ("AwaitingIntegration", "Released", "Released"),
            "Failed": ("NeedsReplan", "Released", "Released"),
            "Cancelled": ("Cancelled", "Cancelled", "Released"),
            "TimedOut": ("NeedsReplan", "Expired", "Expired"),
            "Stale": ("NeedsReplan", "Released", "Released"),
        }
        if outcome not in outcome_mapping:
            raise InvalidRecord("execution outcome is invalid")
        if result_commit is not None:
            result_commit = _commit(result_commit, "result_commit")
        if outcome == "Succeeded" and result_commit is None:
            raise InvalidRecord("Succeeded execution requires a result commit")
        if outcome != "Succeeded" and result_commit is not None:
            raise InvalidRecord("non-success execution prohibits a result commit")
        completion_reference = _text(
            completion_evidence_reference, "completion_evidence_reference"
        )
        reason = validate_payload(reason_payload)
        if reason["kind"] != "reason":
            raise InvalidRecord("execution finish reason must be a reason payload")
        key = _text(idempotency_key, "idempotency_key")
        actor_value = _actor(actor)
        timestamp = _timestamp(now, "now")
        facts = {
            "attempt_id": attempt_id,
            "completion_evidence_reference": completion_reference,
            "execution_handle": execution_handle,
            "expected_attempt_version": expected_attempt_version,
            "expected_lease_version": expected_lease_version,
            "expected_packet_version": expected_packet_version,
            "outcome": outcome,
            "reason": reason,
            "result_commit": result_commit,
        }
        fingerprint = _fingerprint("finish_attempt_execution", facts, actor_value)

        try:
            with self._foundation._connection() as connection:
                connection.execute("BEGIN IMMEDIATE")
                replay = self._replay(connection, key, fingerprint)
                if replay is not None:
                    connection.commit()
                    return replay

                attempt = connection.execute(
                    "SELECT state,version,packet_id,lease_id,execution_handle,"
                    "expected_result,heartbeat_at FROM attempts WHERE attempt_id=?",
                    (attempt_id,),
                ).fetchone()
                if attempt is None:
                    raise InvalidRecord("unknown attempt")
                attempt_state, attempt_version = str(attempt[0]), int(attempt[1])
                if attempt_version != expected_attempt_version:
                    raise StaleState("attempt version is stale")
                if attempt_state != "Running":
                    raise InvalidTransition("execution finish requires a Running attempt")
                if str(attempt[4]) != execution_handle:
                    raise StaleState("execution handle does not match the Running attempt")

                packet_id = str(attempt[2])
                packet = connection.execute(
                    "SELECT state,version,run_id FROM packets WHERE packet_id=?", (packet_id,)
                ).fetchone()
                if packet is None:
                    raise InvalidRecord("attempt packet is missing")
                packet_state, packet_version = str(packet[0]), int(packet[1])
                if packet_version != expected_packet_version:
                    raise StaleState("packet version is stale")
                if packet_state != "Running":
                    raise InvalidTransition("execution finish requires a Running packet")

                lease_id = str(attempt[3])
                lease = connection.execute(
                    "SELECT packet_id,run_id,state,version,expires_at FROM leases WHERE lease_id=?",
                    (lease_id,),
                ).fetchone()
                if lease is None:
                    raise InvalidRecord("attempt lease is missing")
                run_id = str(packet[2])
                if str(lease[0]) != packet_id or str(lease[1]) != run_id:
                    raise InvalidRecord("attempt, packet, and lease relationship is invalid")
                lease_version = int(lease[3])
                if lease_version != expected_lease_version:
                    raise StaleState("lease version is stale")
                if str(lease[2]) != "Active":
                    raise InvalidTransition("execution finish requires an Active lease")

                run = connection.execute(
                    "SELECT state FROM runs WHERE run_id=?", (run_id,)
                ).fetchone()
                if run is None:
                    raise InvalidRecord("packet parent run is missing")
                if str(run[0]) != "Running":
                    raise InvalidTransition("execution finish requires a Running parent run")

                lease_expiry = str(lease[4])
                if outcome == "TimedOut":
                    if timestamp <= lease_expiry:
                        raise InvalidTransition("TimedOut execution requires an expired lease")
                elif timestamp > lease_expiry:
                    raise InvalidTransition("execution finish requires a current lease")

                lock_rows = connection.execute(
                    "SELECT lock_id,state,version FROM resource_locks "
                    "WHERE lease_id=? AND state='Active' ORDER BY lock_id",
                    (lease_id,),
                ).fetchall()
                packet_target, lease_target, lock_target = outcome_mapping[outcome]
                attempt_before = _state_payload(
                    "Attempt", attempt_id, "Running", attempt_version
                )
                packet_before = _state_payload(
                    "Packet", packet_id, "Running", packet_version
                )
                lease_before = _state_payload(
                    "Lease", lease_id, "Active", lease_version
                )
                locks_before = [
                    _state_payload("ResourceLock", str(row[0]), str(row[1]), int(row[2]))
                    for row in lock_rows
                ]
                result = {
                    "attempt": _state_payload(
                        "Attempt", attempt_id, outcome, expected_attempt_version + 1
                    ),
                    "completion": {
                        "attempt_id": attempt_id,
                        "completion_evidence_reference": completion_reference,
                        "execution_handle": execution_handle,
                        "finished_at": timestamp,
                        "result_commit": result_commit,
                    },
                    "lease": _state_payload(
                        "Lease", lease_id, lease_target, expected_lease_version + 1
                    ),
                    "locks": [
                        _state_payload(
                            "ResourceLock", str(row[0]), lock_target, int(row[2]) + 1
                        )
                        for row in lock_rows
                    ],
                    "packet": _state_payload(
                        "Packet", packet_id, packet_target, expected_packet_version + 1
                    ),
                }
                before = {
                    "attempt": attempt_before,
                    "execution": {
                        "attempt_id": attempt_id,
                        "execution_handle": execution_handle,
                        "expected_result": str(attempt[5]),
                        "heartbeat_at": str(attempt[6]),
                    },
                    "lease": lease_before,
                    "locks": locks_before,
                    "packet": packet_before,
                }
                canonical_json(before, root_type=dict)
                canonical_json(result, root_type=dict)

                updated_attempt = connection.execute(
                    "UPDATE attempts SET state=?,result_commit=?,finished_at=?,"
                    "completion_evidence_reference=?,updated_at=?,version=? "
                    "WHERE attempt_id=? AND version=? AND state='Running' "
                    "AND execution_handle=?",
                    (
                        outcome, result_commit, timestamp, completion_reference, timestamp,
                        expected_attempt_version + 1, attempt_id,
                        expected_attempt_version, execution_handle,
                    ),
                )
                if updated_attempt.rowcount != 1:
                    raise StaleState("attempt version is stale")
                updated_packet = connection.execute(
                    "UPDATE packets SET state=?,updated_at=?,version=? "
                    "WHERE packet_id=? AND version=? AND state='Running'",
                    (
                        packet_target, timestamp, expected_packet_version + 1,
                        packet_id, expected_packet_version,
                    ),
                )
                if updated_packet.rowcount != 1:
                    raise StaleState("packet version is stale")
                updated_lease = connection.execute(
                    "UPDATE leases SET state=?,released_at=?,version=? "
                    "WHERE lease_id=? AND version=? AND state='Active'",
                    (
                        lease_target, timestamp, expected_lease_version + 1,
                        lease_id, expected_lease_version,
                    ),
                )
                if updated_lease.rowcount != 1:
                    raise StaleState("lease version is stale")
                for lock_id, _, lock_version in lock_rows:
                    updated_lock = connection.execute(
                        "UPDATE resource_locks SET state=?,released_at=?,version=? "
                        "WHERE lock_id=? AND version=? AND state='Active'",
                        (
                            lock_target, timestamp, int(lock_version) + 1,
                            str(lock_id), int(lock_version),
                        ),
                    )
                    if updated_lock.rowcount != 1:
                        raise StaleState("resource lock version is stale")
                self._insert_attempt_state_event(
                    connection, key, fingerprint, actor_value, timestamp,
                    attempt_id, before, result, reason,
                )
                connection.commit()
                return result
        except sqlite3.IntegrityError as error:
            raise InvalidRecord(
                "execution finish violates a durable constraint"
            ) from error
        except sqlite3.OperationalError as error:
            self._raise_sqlite(error)

    def record_attempt(self, attempt, idempotency_key, actor, now):
        row = self._attempt(attempt, now)
        return self._append_one("attempts", "attempt_id", row, "Attempt", "AttemptRecorded", idempotency_key, actor, now)

    def append_evidence(self, evidence, actor):
        row = self._evidence(evidence)
        return self._append_one(
            "evidence", "evidence_id", row, "Evidence", "EvidenceAppended",
            row["idempotency_key"], actor, row["created_at"],
        )

    def open_wait(self, wait, idempotency_key, actor, now):
        row = self._wait(wait, now)
        return self._append_one("waits", "wait_id", row, "Wait", "WaitOpened", idempotency_key, actor, now)

    def record_review(self, review, idempotency_key, actor, now):
        row = self._review(review)
        _timestamp(now, "now")
        return self._append_one("reviews", "review_id", row, "Review", "ReviewRecorded", idempotency_key, actor, now)

    def record_and_route_review(
        self, packet_id, expected_packet_version, review, reason_payload,
        idempotency_key, actor, now,
    ):
        packet_id = _text(packet_id, "packet_id")
        expected_packet_version = _positive_int(
            expected_packet_version, "expected_packet_version"
        )
        reason = validate_payload(reason_payload)
        if reason["kind"] != "reason":
            raise InvalidRecord("review routing reason must be a reason payload")
        key = _text(idempotency_key, "idempotency_key")
        actor_value = _actor(actor)
        timestamp = _timestamp(now, "now")

        if not isinstance(review, Mapping):
            raise InvalidRecord("review has an invalid closed shape")
        review_row = self._review({**review, "packet_id": packet_id, "created_at": timestamp})
        if review_row["correction_number"] != 0:
            raise InvalidRecord("review routing requires correction_number zero")
        review_kind = review_row["review_kind"]

        facts = {
            "expected_packet_version": expected_packet_version,
            "packet_id": packet_id,
            "reason": reason,
            "review": review_row,
        }
        fingerprint = _fingerprint("record_and_route_review", facts, actor_value)

        try:
            with self._foundation._connection() as connection:
                connection.execute("BEGIN IMMEDIATE")
                replay = self._replay(connection, key, fingerprint)
                if replay is not None:
                    connection.commit()
                    return replay

                packet = connection.execute(
                    "SELECT state,version,base_commit,owned_paths_json,correction_count "
                    "FROM packets WHERE packet_id=?",
                    (packet_id,),
                ).fetchone()
                if packet is None:
                    raise InvalidRecord("unknown packet")
                source_state, current_version = str(packet[0]), int(packet[1])
                if current_version != expected_packet_version:
                    raise StaleState("packet version is stale")

                target_state = _REVIEW_ROUTES.get(
                    (source_state, review_kind, review_row["result"])
                )
                if target_state is None:
                    raise InvalidTransition(
                        "review routing is not permitted for this packet state, "
                        "review kind, and result"
                    )

                attempt = connection.execute(
                    "SELECT attempt_id,model_identity,runtime_identity,lease_id,result_commit "
                    "FROM attempts WHERE packet_id=? AND attempt_kind='Initial' "
                    "AND attempt_number=1 AND state='Succeeded' AND result_commit IS NOT NULL",
                    (packet_id,),
                ).fetchone()
                if attempt is None:
                    raise InvalidRecord(
                        "packet has no Succeeded Initial attempt with a result commit"
                    )
                model_identity, runtime_identity, lease_id, result_commit = (
                    str(attempt[1]), str(attempt[2]), str(attempt[3]), str(attempt[4]),
                )

                base_commit = str(packet[2])
                if review_row["base_commit"] != base_commit:
                    raise InvalidRecord("review base_commit does not match the packet base_commit")
                if review_row["head_commit"] != result_commit:
                    raise InvalidRecord(
                        "review head_commit does not match the attempt result_commit"
                    )
                if review_row["head_commit"] == review_row["base_commit"]:
                    raise InvalidRecord("review head_commit must differ from base_commit")

                if target_state == "MergeReady" and int(packet[4]) not in (0, 1):
                    raise InvalidRecord(
                        "packet correction_count must be zero or one for an approval route"
                    )

                self._validate_review_coverage(review_row, json.loads(str(packet[3])))

                required_role = _REVIEW_REVIEWER_ROLES[review_kind]
                if review_row["reviewer_role"] != required_role:
                    raise InvalidRecord(
                        "review reviewer_role does not match the review kind"
                    )
                lease = connection.execute(
                    "SELECT holder_id FROM leases WHERE lease_id=?", (lease_id,)
                ).fetchone()
                if lease is None:
                    raise InvalidRecord("attempt lease is missing")
                holder_id = str(lease[0])
                reviewer_instance = review_row["reviewer_instance"]
                if reviewer_instance in {model_identity, runtime_identity, holder_id}:
                    raise InvalidRecord(
                        "reviewer_instance is not independent of the attempt or lease"
                    )

                if review_kind == "IndependentImplementation":
                    prior_integration = connection.execute(
                        "SELECT reviewer_instance FROM reviews WHERE packet_id=? "
                        "AND review_kind='Integration' AND result='ValidateOnly' "
                        "AND head_commit=?",
                        (packet_id, review_row["head_commit"]),
                    ).fetchall()
                    if len(prior_integration) != 1:
                        raise InvalidRecord(
                            "independent implementation review requires exactly one prior "
                            "Integration ValidateOnly review on the same packet and head"
                        )
                    if reviewer_instance == str(prior_integration[0][0]):
                        raise InvalidRecord(
                            "reviewer_instance is not independent of the prior "
                            "Integration review"
                        )

                packet_before = _state_payload("Packet", packet_id, source_state, current_version)
                packet_after = _state_payload(
                    "Packet", packet_id, target_state, expected_packet_version + 1
                )
                before = {"packet": packet_before}
                result = {"packet": packet_after, "review": review_row}
                canonical_json(before, root_type=dict)
                canonical_json(result, root_type=dict)

                self._insert(connection, "reviews", review_row)
                updated = connection.execute(
                    "UPDATE packets SET state=?,updated_at=?,version=? "
                    "WHERE packet_id=? AND version=?",
                    (
                        target_state, timestamp, expected_packet_version + 1,
                        packet_id, expected_packet_version,
                    ),
                )
                if updated.rowcount != 1:
                    raise StaleState("packet version is stale")
                self._insert_review_route_event(
                    connection, key, fingerprint, actor_value, timestamp,
                    packet_id, before, result, reason,
                )
                connection.commit()
                return result
        except sqlite3.IntegrityError as error:
            raise InvalidRecord("review routing violates a durable constraint") from error
        except sqlite3.OperationalError as error:
            self._raise_sqlite(error)

    @staticmethod
    def _validate_review_coverage(review_row, owned_paths):
        coverage = review_row["coverage_json"]
        if set(coverage) != {"kind", "result"} or coverage.get("kind") != "review-readiness-coverage":
            raise InvalidRecord("review coverage_json has an invalid closed shape")
        coverage_result = coverage["result"]
        try:
            review_readiness.validate_result(coverage_result)
        except review_readiness.ResultError as error:
            raise InvalidRecord(f"review coverage result is invalid: {error}") from error
        if coverage_result["ready"] is not True:
            raise InvalidRecord("review coverage result is not ready")
        if coverage_result["blockers"] != []:
            raise InvalidRecord("review coverage result has blockers")
        if any(check["outcome"] != "Passed" for check in coverage_result["checks"]):
            raise InvalidRecord("review coverage result has a non-passed check")
        request = coverage_result["request"]
        if request is None or request["review_kind"] != "IndependentImplementation":
            raise InvalidRecord(
                "review coverage request review_kind must be IndependentImplementation"
            )
        if coverage_result["resolved_base"] != review_row["base_commit"]:
            raise InvalidRecord("review coverage resolved_base does not match")
        if coverage_result["resolved_head"] != review_row["head_commit"]:
            raise InvalidRecord("review coverage resolved_head does not match")
        if coverage_result["checked_out_head_before"] != review_row["head_commit"]:
            raise InvalidRecord("review coverage checked_out_head_before does not match")
        if coverage_result["checked_out_head_after"] != review_row["head_commit"]:
            raise InvalidRecord("review coverage checked_out_head_after does not match")
        if coverage_result["clean_before"] is not True or coverage_result["clean_after"] is not True:
            raise InvalidRecord("review coverage result is not clean")
        changed_paths = coverage_result["changed_paths"]
        if not changed_paths or changed_paths != sorted(changed_paths):
            raise InvalidRecord("review coverage changed_paths must be nonempty and sorted")
        sorted_owned = sorted(owned_paths, key=lambda item: item.encode("utf-8"))
        if request["allowed_paths"] != sorted_owned:
            raise InvalidRecord(
                "review coverage allowed_paths does not match the packet owned paths"
            )

    def record_notification(self, notification, idempotency_key, actor, now):
        row = self._notification(notification, now)
        return self._append_one("notifications", "notification_id", row, "Notification", "NotificationRecorded", idempotency_key, actor, now)

    def record_worker_progress(self, observation, idempotency_key, actor, now):
        row = self._worker_progress(observation)
        _timestamp(now, "now")
        return self._append_one("worker_progress_observations", "progress_id", row, "WorkerProgress", "WorkerProgressRecorded", idempotency_key, actor, now)

    def record_context_usage(self, record, idempotency_key, actor, now):
        row = self._context_usage(record, now)
        actor_value = _actor(actor)
        timestamp = _timestamp(now, "now")
        key = _text(idempotency_key, "idempotency_key")
        fingerprint = _fingerprint("record_context_usage", row, actor_value)
        try:
            with self._foundation._connection() as connection:
                connection.execute("BEGIN IMMEDIATE")
                replay = self._replay(connection, key, fingerprint)
                if replay is not None:
                    connection.commit()
                    return replay
                policy_row = connection.execute(
                    "SELECT p.context_policy_json FROM attempts a JOIN packets p ON p.packet_id=a.packet_id WHERE a.attempt_id=?",
                    (row["attempt_id"],),
                ).fetchone()
                if policy_row is None:
                    raise InvalidRecord("context usage attempt has no materialized packet policy")
                policy = json.loads(str(policy_row[0]))
                if row["context_policy_digest"] != context_policy_digest(policy):
                    raise InvalidRecord("context policy digest does not match the attempt packet")
                start = row["starting_input_measurement_json"]
                configured = row["configured_context_limit"]
                starting_value = start["value"] if start["quality"] != "Unavailable" else None
                validate_context_policy(
                    policy, configured_context_limit=configured, starting_input_tokens=starting_value
                ) if configured is not None else validate_context_policy(policy)
                self._insert(connection, "attempt_context_usage", row)
                self._insert_event(connection, key, fingerprint, actor_value, timestamp, "AttemptContextUsage", row["context_usage_id"], "AttemptContextUsageRecorded", row)
                connection.commit()
                return row
        except sqlite3.OperationalError as error:
            self._raise_sqlite(error)
        except sqlite3.IntegrityError as error:
            raise InvalidRecord("context usage violates a durable constraint") from error

    def update_context_usage(self, attempt_id, expected_version, measurements, idempotency_key, actor, now):
        attempt_id = _text(attempt_id, "attempt_id")
        expected_version = _positive_int(expected_version, "expected_version")
        changes = _closed_mapping(
            measurements, {"token_measurements", "cost_measurement", "availability_state", "observed_at"},
            "context usage update",
        )
        tokens = _token_measurements(changes["token_measurements"])
        cost = validate_cost_measurement(changes["cost_measurement"])
        availability = changes["availability_state"]
        if availability not in {"Available", "Partial", "Unavailable"}:
            raise InvalidRecord("context availability is invalid")
        changes["observed_at"] = _timestamp(changes["observed_at"], "context update observed_at")
        actor_value = _actor(actor)
        timestamp = _timestamp(now, "now")
        key = _text(idempotency_key, "idempotency_key")
        facts = {"attempt_id": attempt_id, "expected_version": expected_version, **changes, "token_measurements": tokens, "cost_measurement": cost}
        fingerprint = _fingerprint("update_context_usage", facts, actor_value)
        try:
            with self._foundation._connection() as connection:
                connection.execute("BEGIN IMMEDIATE")
                replay = self._replay(connection, key, fingerprint)
                if replay is not None:
                    connection.commit()
                    return replay
                current = connection.execute("SELECT * FROM attempt_context_usage WHERE attempt_id=?", (attempt_id,)).fetchone()
                if current is None:
                    raise InvalidRecord("unknown context usage attempt")
                columns = [str(info[1]) for info in connection.execute("PRAGMA table_info(attempt_context_usage)")]
                durable = _decode_row(dict(zip(columns, current)))
                if int(durable["version"]) != expected_version:
                    raise StaleState("context usage version is stale")
                old_tokens = durable["token_measurements_json"]
                for category in tokens:
                    preferred_measurement(old_tokens[category], tokens[category])
                old_cost = durable["cost_measurement_json"]
                if old_cost["observed_at"] == cost["observed_at"]:
                    rank = {"Unavailable": 0, "Estimated": 1, "ProviderReported": 2, "RuntimeReported": 3}
                    if rank[cost["quality"]] < rank[old_cost["quality"]]:
                        raise InvalidRecord("lower-quality cost cannot replace the retained value")
                version = expected_version + 1
                connection.execute(
                    "UPDATE attempt_context_usage SET token_measurements_json=?, cost_measurement_json=?, availability_state=?, observed_at=?, updated_at=?, version=? WHERE attempt_id=? AND version=?",
                    (canonical_json(tokens), canonical_json(cost), availability, changes["observed_at"], timestamp, version, attempt_id, expected_version),
                )
                durable.update({
                    "token_measurements_json": tokens, "cost_measurement_json": cost,
                    "availability_state": availability, "observed_at": changes["observed_at"],
                    "updated_at": timestamp, "version": version,
                })
                self._insert_event(connection, key, fingerprint, actor_value, timestamp, "AttemptContextUsage", str(durable["context_usage_id"]), "AttemptContextUsageRecorded", durable)
                connection.commit()
                return durable
        except sqlite3.OperationalError as error:
            self._raise_sqlite(error)
        except sqlite3.IntegrityError as error:
            raise InvalidRecord("context usage update violates a durable constraint") from error

    def record_allowance_window(self, observation, idempotency_key, actor, now):
        row = self._allowance(observation)
        _timestamp(now, "now")
        return self._append_one("provider_allowance_windows", "allowance_observation_id", row, "AllowanceWindow", "AllowanceWindowObserved", idempotency_key, actor, now)

    def record_usage_reconciliation(self, record, idempotency_key, actor, now):
        row = self._reconciliation(record)
        actor_value = _actor(actor)
        timestamp = _timestamp(now, "now")
        key = _text(idempotency_key, "idempotency_key")
        fingerprint = _fingerprint("record_usage_reconciliation", row, actor_value)
        try:
            with self._foundation._connection() as connection:
                connection.execute("BEGIN IMMEDIATE")
                replay = self._replay(connection, key, fingerprint)
                if replay is not None:
                    connection.commit()
                    return replay
                allowance = connection.execute(
                    "SELECT native_unit FROM provider_allowance_windows WHERE allowance_observation_id=?",
                    (row["allowance_observation_id"],),
                ).fetchone()
                if allowance is None or allowance[0] is None or str(allowance[0]) != row["native_unit"]:
                    raise InvalidRecord("reconciliation must retain the allowance native unit")
                self._insert(connection, "usage_reconciliations", row)
                self._insert_event(connection, key, fingerprint, actor_value, timestamp, "UsageReconciliation", row["usage_reconciliation_id"], "UsageReconciliationRecorded", row)
                connection.commit()
                return row
        except sqlite3.OperationalError as error:
            self._raise_sqlite(error)
        except sqlite3.IntegrityError as error:
            raise InvalidRecord("usage reconciliation violates a durable constraint") from error

    def record_acceptance(self, record, idempotency_key, actor, now):
        row = self._acceptance(record)
        _timestamp(now, "now")
        return self._append_one("acceptance_records", "acceptance_id", row, "Acceptance", "AcceptanceRecorded", idempotency_key, actor, now)

    def record_merge_observation(self, observation, idempotency_key, actor, now):
        row = self._merge_observation(observation)
        _timestamp(now, "now")
        return self._append_one("merge_observations", "merge_observation_id", row, "MergeObservation", "MergeObserved", idempotency_key, actor, now)

    def snapshot(self, entity_type: str, entity_id: str) -> dict[str, Any] | None:
        entity_type = _text(entity_type, "entity_type")
        entity_id = _text(entity_id, "entity_id")
        if entity_type not in _ENTITY_TABLES:
            raise InvalidRecord("entity_type is not snapshot-readable")
        table, key = _ENTITY_TABLES[entity_type]
        try:
            with self._foundation._connection() as connection:
                return self._row(connection, table, key, entity_id)
        except sqlite3.OperationalError as error:
            self._raise_sqlite(error)

    def events_after(self, event_id: int, limit: int) -> list[dict[str, Any]]:
        event_id = _nonnegative_int(event_id, "event_id")
        if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= 1000:
            raise InvalidRecord("event limit must be between 1 and 1000")
        try:
            with self._foundation._connection() as connection:
                cursor = connection.execute(
                    "SELECT * FROM events WHERE event_id>? ORDER BY event_id LIMIT ?", (event_id, limit)
                )
                columns = [item[0] for item in cursor.description]
                return [_decode_row(dict(zip(columns, row))) for row in cursor.fetchall()]
        except sqlite3.OperationalError as error:
            self._raise_sqlite(error)

    def _append_one(self, table, primary_key, row, entity_type, event_type, idempotency_key, actor, now):
        return self._append(
            f"record_{table}", row, entity_type, str(row[primary_key]), event_type,
            idempotency_key, actor, now, lambda connection: self._insert(connection, table, row),
        )

    def _append(self, operation, payload, entity_type, entity_id, event_type, idempotency_key, actor, now, writer):
        timestamp = _timestamp(now, "now")
        key = _text(idempotency_key, "idempotency_key")
        actor_value = _actor(actor)
        canonical_json(payload, root_type=dict)
        fingerprint = _fingerprint(operation, payload, actor_value)
        try:
            with self._foundation._connection() as connection:
                connection.execute("BEGIN IMMEDIATE")
                replay = self._replay(connection, key, fingerprint)
                if replay is not None:
                    connection.commit()
                    return replay
                writer(connection)
                self._insert_event(connection, key, fingerprint, actor_value, timestamp, entity_type, entity_id, event_type, payload)
                connection.commit()
                return payload
        except sqlite3.IntegrityError as error:
            raise InvalidRecord("record violates a durable schema constraint") from error
        except sqlite3.OperationalError as error:
            self._raise_sqlite(error)

    @staticmethod
    def _replay(connection: sqlite3.Connection, key: str, fingerprint: str):
        row = connection.execute(
            "SELECT command_fingerprint,after_json FROM events WHERE idempotency_key=?", (key,)
        ).fetchone()
        if row is None:
            return None
        if row[0] != fingerprint:
            raise IdempotencyConflict("idempotency key was already used for different command facts")
        return json.loads(str(row[1]))

    @staticmethod
    def _insert_event(connection, key, fingerprint, actor, now, entity_type, entity_id, event_type, payload):
        connection.execute(
            """
            INSERT INTO events(
                idempotency_key,entity_type,entity_id,event_type,before_json,after_json,reason,
                correlation_id,causation_event_id,actor_type,actor_id,command_fingerprint,observed_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                key, entity_type, entity_id, event_type, "{}", canonical_json(payload),
                canonical_json({"kind": "reason", "reason_code": "RECORDED", "detail_reference": None}),
                actor["correlation_id"], actor["causation_event_id"], actor["actor_type"],
                actor["actor_id"], fingerprint, now,
            ),
        )

    @staticmethod
    def _insert_run_state_event(
        connection, key, fingerprint, actor, now, run_id, before, after, reason,
    ):
        connection.execute(
            """
            INSERT INTO events(
                idempotency_key,entity_type,entity_id,event_type,before_json,after_json,reason,
                correlation_id,causation_event_id,actor_type,actor_id,command_fingerprint,observed_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                key, "Run", run_id, "RunStateChanged", canonical_json(before),
                canonical_json(after), canonical_json(reason), actor["correlation_id"],
                actor["causation_event_id"], actor["actor_type"], actor["actor_id"],
                fingerprint, now,
            ),
        )

    @staticmethod
    def _insert_packet_state_event(
        connection, key, fingerprint, actor, now, packet_id, before, after, reason,
    ):
        connection.execute(
            """
            INSERT INTO events(
                idempotency_key,entity_type,entity_id,event_type,before_json,after_json,reason,
                correlation_id,causation_event_id,actor_type,actor_id,command_fingerprint,observed_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                key, "Packet", packet_id, "PacketStateChanged", canonical_json(before),
                canonical_json(after), canonical_json(reason), actor["correlation_id"],
                actor["causation_event_id"], actor["actor_type"], actor["actor_id"],
                fingerprint, now,
            ),
        )

    @staticmethod
    def _insert_packet_claim_event(
        connection, key, fingerprint, actor, now, packet_id, before, after, reason,
    ):
        connection.execute(
            """
            INSERT INTO events(
                idempotency_key,entity_type,entity_id,event_type,before_json,after_json,reason,
                correlation_id,causation_event_id,actor_type,actor_id,command_fingerprint,observed_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                key, "Packet", packet_id, "PacketClaimed", canonical_json(before),
                canonical_json(after), canonical_json(reason), actor["correlation_id"],
                actor["causation_event_id"], actor["actor_type"], actor["actor_id"],
                fingerprint, now,
            ),
        )

    @staticmethod
    def _insert_attempt_state_event(
        connection, key, fingerprint, actor, now, attempt_id, before, after, reason,
    ):
        connection.execute(
            """
            INSERT INTO events(
                idempotency_key,entity_type,entity_id,event_type,before_json,after_json,reason,
                correlation_id,causation_event_id,actor_type,actor_id,command_fingerprint,observed_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                key, "Attempt", attempt_id, "AttemptStateChanged",
                canonical_json(before), canonical_json(after), canonical_json(reason),
                actor["correlation_id"], actor["causation_event_id"], actor["actor_type"],
                actor["actor_id"], fingerprint, now,
            ),
        )

    @staticmethod
    def _insert_lease_heartbeat_event(
        connection, key, fingerprint, actor, now, lease_id, before, after, reason,
    ):
        connection.execute(
            """
            INSERT INTO events(
                idempotency_key,entity_type,entity_id,event_type,before_json,after_json,reason,
                correlation_id,causation_event_id,actor_type,actor_id,command_fingerprint,observed_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                key, "Lease", lease_id, "LeaseHeartbeatRecorded",
                canonical_json(before), canonical_json(after), canonical_json(reason),
                actor["correlation_id"], actor["causation_event_id"], actor["actor_type"],
                actor["actor_id"], fingerprint, now,
            ),
        )

    @staticmethod
    def _insert_review_route_event(
        connection, key, fingerprint, actor, now, packet_id, before, after, reason,
    ):
        connection.execute(
            """
            INSERT INTO events(
                idempotency_key,entity_type,entity_id,event_type,before_json,after_json,reason,
                correlation_id,causation_event_id,actor_type,actor_id,command_fingerprint,observed_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                key, "Packet", packet_id, "ReviewRecorded", canonical_json(before),
                canonical_json(after), canonical_json(reason), actor["correlation_id"],
                actor["causation_event_id"], actor["actor_type"], actor["actor_id"],
                fingerprint, now,
            ),
        )

    @staticmethod
    def _insert(connection: sqlite3.Connection, table: str, row: Mapping[str, Any]) -> None:
        columns = tuple(row)
        placeholders = ",".join("?" for _ in columns)
        values = [canonical_json(row[name]) if name.endswith("_json") and row[name] is not None else row[name] for name in columns]
        connection.execute(
            f"INSERT INTO {table} ({','.join(columns)}) VALUES ({placeholders})", values
        )

    @staticmethod
    def _row(connection: sqlite3.Connection, table: str, key: str, value: str):
        cursor = connection.execute(f"SELECT * FROM {table} WHERE {key}=?", (value,))
        row = cursor.fetchone()
        if row is None:
            return None
        return _decode_row(dict(zip((item[0] for item in cursor.description), row)))

    @staticmethod
    def _raise_sqlite(error: sqlite3.OperationalError):
        if "locked" in str(error).lower() or "busy" in str(error).lower():
            raise ResourceBusy("SQLite busy timeout exhausted") from error
        raise error

    @staticmethod
    def _binding(value, now):
        fields = {
            "binding_id", "project_id", "binding_revision", "source_commit", "manifest_digest",
            "adapter_version", "process_version", "authority_reference", "merge_policy",
            "acceptance_authority", "merge_execution_authority", "merge_delegation_reference",
            "binding_json", "state", "activated_at", "superseded_at",
        }
        row = _closed_mapping(value, fields, "project binding")
        for field in fields - {"merge_delegation_reference", "binding_json", "activated_at", "superseded_at", "source_commit", "manifest_digest"}:
            row[field] = _text(row[field], field)
        row["source_commit"] = _commit(row["source_commit"], "source_commit")
        row["manifest_digest"] = _digest(row["manifest_digest"], "manifest_digest")
        row["merge_delegation_reference"] = _optional_text(row["merge_delegation_reference"], "merge_delegation_reference")
        row["binding_json"] = _json_object(row["binding_json"], "binding_json")
        for field in ("activated_at", "superseded_at"):
            row[field] = _optional_timestamp(row[field], field)
        if row["state"] not in {"Candidate", "Blocked"}:
            raise InvalidRecord("record_binding accepts Candidate or Blocked only")
        if row["acceptance_authority"] not in {"ProjectArchitect", "Owner"}:
            raise InvalidRecord("binding acceptance authority is invalid")
        if row["merge_execution_authority"] == "OwnerPerformed":
            if row["merge_delegation_reference"] is not None:
                raise InvalidRecord("owner-performed merge cannot carry delegation")
        elif row["merge_execution_authority"] == "PolicyDelegated":
            if row["merge_delegation_reference"] is None:
                raise InvalidRecord("delegated merge requires its reviewed policy reference")
        else:
            raise InvalidRecord("merge execution authority is invalid")
        if row["activated_at"] is not None or row["superseded_at"] is not None:
            raise InvalidRecord("candidate/blocked binding has no activation/supersession time")
        row["created_at"] = _timestamp(now, "now")
        return row

    @staticmethod
    def _secret_reference(value):
        fields = {
            "secret_reference_observation_id", "project_id", "binding_id", "provider",
            "reference_name", "owner_reference", "rotation_at", "expires_at", "status", "observed_at",
        }
        row = _closed_mapping(value, fields, "secret reference observation")
        for field in {"secret_reference_observation_id", "project_id", "binding_id", "owner_reference"}:
            row[field] = _text(row[field], field)
        row["provider"] = _provider(row["provider"])
        row["reference_name"] = _reference_name(row["reference_name"])
        row["rotation_at"] = _optional_timestamp(row["rotation_at"], "rotation_at")
        row["expires_at"] = _optional_timestamp(row["expires_at"], "expires_at")
        row["observed_at"] = _timestamp(row["observed_at"], "observed_at")
        if row["status"] not in {"Active", "Stale", "Revoked", "Unavailable"}:
            raise InvalidRecord("secret reference status is invalid")
        return row

    @staticmethod
    def _graph(value, now):
        fields = {"graph_projection_id", "project_id", "binding_id", "graph_revision", "authority_reference", "source_base_sha", "source_hash", "state", "observed_at"}
        row = _closed_mapping(value, fields, "graph projection")
        for field in fields - {"source_base_sha", "source_hash", "observed_at"}:
            row[field] = _text(row[field], field)
        row["source_base_sha"] = _commit(row["source_base_sha"], "source_base_sha")
        row["source_hash"] = _digest(row["source_hash"], "source_hash")
        row["observed_at"] = _timestamp(row["observed_at"], "observed_at")
        if row["state"] != "Active":
            raise InvalidRecord("record_graph_projection creates Active projections only")
        row.update(updated_at=now, version=1)
        return row

    @staticmethod
    def _work_item(value, graph_id, now):
        fields = {
            "work_item_id", "graph_projection_id", "architecture_node_id", "task_reference",
            "workstream_ref", "milestone_ref", "title", "priority", "planned_rank", "specialist_role",
            "execution_classes_json", "dependencies_json", "change_domains_json",
            "input_contract_json", "output_contract_json", "planning_state",
        }
        row = _closed_mapping(value, fields, "work item")
        if row["graph_projection_id"] != graph_id:
            raise InvalidRecord("work item belongs to a different graph projection")
        for field in fields - {"planned_rank", "execution_classes_json", "dependencies_json", "change_domains_json", "input_contract_json", "output_contract_json"}:
            row[field] = _text(row[field], field)
        row["planned_rank"] = _nonnegative_int(row["planned_rank"], "planned_rank")
        for field in ("execution_classes_json", "dependencies_json", "change_domains_json"):
            row[field] = _sorted_unique_text(row[field], field)
        row["input_contract_json"] = _json_object(row["input_contract_json"], "input_contract_json")
        row["output_contract_json"] = _json_object(row["output_contract_json"], "output_contract_json")
        if row["planning_state"] not in {"Active", "NeedsReplan", "Superseded"}:
            raise InvalidRecord("work-item planning state is invalid")
        row.update(created_at=now, updated_at=now, version=1)
        return row

    @staticmethod
    def _run(value, now):
        fields = {
            "run_id", "run_fingerprint", "project_id", "binding_id", "graph_projection_id",
            "milestone_ref", "approved_authority_reference", "branch_name", "pull_request_reference",
            "current_head", "current_head_source_reference", "candidate_head",
            "candidate_head_source_reference", "state", "acceptance_boundary",
        }
        row = _closed_mapping(value, fields, "run")
        for field in {"run_id", "project_id", "binding_id", "graph_projection_id", "milestone_ref", "approved_authority_reference", "state", "acceptance_boundary"}:
            row[field] = _text(row[field], field)
        row["run_fingerprint"] = _digest(row["run_fingerprint"], "run_fingerprint")
        for field in {"branch_name", "pull_request_reference", "current_head_source_reference", "candidate_head_source_reference"}:
            row[field] = _optional_text(row[field], field)
        for field in {"current_head", "candidate_head"}:
            row[field] = None if row[field] is None else _commit(row[field], field)
        if row["state"] != "Planned":
            raise InvalidRecord("create_run creates Planned runs only")
        if row["acceptance_boundary"] not in {"ProjectArchitect", "Owner"}:
            raise InvalidRecord("run acceptance boundary is invalid")
        if any(row[field] is not None for field in ("current_head", "current_head_source_reference", "candidate_head", "candidate_head_source_reference")):
            raise InvalidRecord("planned run cannot begin with observed/candidate head")
        timestamp = _timestamp(now, "now")
        row.update(created_at=timestamp, updated_at=timestamp, version=1)
        return row

    @staticmethod
    def _packet(value, now):
        fields = {
            "packet_id", "run_id", "work_item_id", "packet_revision", "authority_reference",
            "base_commit", "current_head", "expected_branch", "role_contract_reference", "sop_reference",
            "executor_class", "integration_route", "reviewer_route", "owned_paths_json",
            "forbidden_paths_json", "checks_json", "resource_claims_json", "context_policy_json",
            "state", "correction_count",
        }
        row = _closed_mapping(value, fields, "packet")
        for field in fields - {"base_commit", "current_head", "owned_paths_json", "forbidden_paths_json", "checks_json", "resource_claims_json", "context_policy_json", "correction_count"}:
            row[field] = _text(row[field], field)
        row["base_commit"] = _commit(row["base_commit"], "base_commit")
        row["current_head"] = None if row["current_head"] is None else _commit(row["current_head"], "current_head")
        for field in ("owned_paths_json", "forbidden_paths_json", "resource_claims_json"):
            row[field] = _sorted_unique_text(row[field], field)
        if not isinstance(row["checks_json"], list):
            raise InvalidRecord("checks_json must be an array")
        canonical_json(row["checks_json"], root_type=list)
        row["context_policy_json"] = validate_context_policy(row["context_policy_json"])
        row["correction_count"] = _nonnegative_int(row["correction_count"], "correction_count")
        if row["state"] != "Planned" or row["correction_count"] != 0:
            raise InvalidRecord("materialized packet starts Planned with correction count zero")
        if row["current_head"] is not None:
            raise InvalidRecord("materialized packet has no current head")
        timestamp = _timestamp(now, "now")
        row.update(created_at=timestamp, updated_at=timestamp, version=1)
        return row

    @staticmethod
    def _attempt(value, now):
        fields = {
            "attempt_id", "packet_id", "lease_id", "attempt_number", "attempt_kind", "executor_class",
            "model_identity", "runtime_identity", "state", "result_commit", "correction_for_review_id",
            "started_at", "finished_at",
        }
        row = _closed_mapping(value, fields, "attempt")
        for field in {"attempt_id", "packet_id", "lease_id", "executor_class", "model_identity", "runtime_identity"}:
            row[field] = _text(row[field], field)
        row["attempt_number"] = _positive_int(row["attempt_number"], "attempt_number")
        if row["attempt_number"] not in {1, 2}:
            raise InvalidRecord("attempt number is invalid")
        row["correction_for_review_id"] = _optional_text(row["correction_for_review_id"], "correction_for_review_id")
        row["result_commit"] = None if row["result_commit"] is None else _commit(row["result_commit"], "result_commit")
        row["started_at"] = _optional_timestamp(row["started_at"], "started_at")
        row["finished_at"] = _optional_timestamp(row["finished_at"], "finished_at")
        expected_kind = "Initial" if row["attempt_number"] == 1 else "TargetedCorrection"
        if row["attempt_kind"] != expected_kind or row["state"] != "Planned":
            raise InvalidRecord("attempt creation facts are invalid")
        if row["attempt_number"] == 1 and row["correction_for_review_id"] is not None:
            raise InvalidRecord("initial attempt cannot reference a correction review")
        if row["attempt_number"] == 2 and row["correction_for_review_id"] is None:
            raise InvalidRecord("targeted correction requires a review reference")
        if any(row[field] is not None for field in ("result_commit", "started_at", "finished_at")):
            raise InvalidRecord("planned attempt has no result/start/finish facts")
        timestamp = _timestamp(now, "now")
        row.update(
            created_at=timestamp,
            updated_at=timestamp,
            version=1,
            execution_handle=None,
            expected_result=None,
            heartbeat_at=None,
            completion_evidence_reference=None,
        )
        return row

    @staticmethod
    def _evidence(value):
        fields = {"evidence_id", "idempotency_key", "run_id", "packet_id", "attempt_id", "evidence_kind", "payload_json", "content_digest", "source_reference", "redaction_state", "created_at"}
        row = _closed_mapping(value, fields, "evidence")
        for field in {"evidence_id", "idempotency_key", "run_id", "packet_id", "evidence_kind"}:
            row[field] = _text(row[field], field)
        row["attempt_id"] = _optional_text(row["attempt_id"], "attempt_id")
        row["source_reference"] = _optional_text(row["source_reference"], "source_reference")
        row["payload_json"] = validate_payload(row["payload_json"])
        row["content_digest"] = _digest(row["content_digest"], "content_digest")
        if row["content_digest"] != canonical_digest(row["payload_json"]):
            raise InvalidRecord("evidence digest does not cover its canonical payload")
        if row["redaction_state"] not in {"Redacted", "NotRequired"}:
            raise InvalidRecord("evidence redaction state is invalid")
        if row["payload_json"]["kind"] == "redacted-text" and row["redaction_state"] != "Redacted":
            raise InvalidRecord("redacted prose evidence must be marked Redacted")
        row["created_at"] = _timestamp(row["created_at"], "created_at")
        return row

    @staticmethod
    def _wait(value, now):
        fields = {"wait_id", "run_id", "packet_id", "gate_type", "awaited_role", "awaited_reference", "expected_result", "timeout_at", "next_permitted_action", "state", "resolution_reason_payload_json"}
        row = _closed_mapping(value, fields, "wait")
        for field in fields - {"packet_id", "timeout_at", "resolution_reason_payload_json"}:
            row[field] = _text(row[field], field)
        row["packet_id"] = _optional_text(row["packet_id"], "packet_id")
        row["timeout_at"] = _optional_timestamp(row["timeout_at"], "timeout_at")
        if row["state"] != "Open" or row["resolution_reason_payload_json"] is not None:
            raise InvalidRecord("open_wait creates unresolved Open waits only")
        timestamp = _timestamp(now, "now")
        row.update(created_at=timestamp, updated_at=timestamp, version=1)
        return row

    @staticmethod
    def _review(value):
        fields = {"review_id", "packet_id", "attempt_id", "review_kind", "reviewer_role", "reviewer_instance", "base_commit", "head_commit", "result", "findings_json", "coverage_json", "correction_number", "created_at"}
        row = _closed_mapping(value, fields, "review")
        for field in {"review_id", "packet_id", "reviewer_role", "reviewer_instance"}:
            row[field] = _text(row[field], field)
        row["attempt_id"] = _optional_text(row["attempt_id"], "attempt_id")
        row["base_commit"] = _commit(row["base_commit"], "base_commit")
        row["head_commit"] = _commit(row["head_commit"], "head_commit")
        if row["review_kind"] not in {"Integration", "IndependentImplementation"}:
            raise InvalidRecord("review kind is invalid")
        if row["result"] not in {"ValidateOnly", "Assemble", "NeedsReplan", "Approve", "RequestChanges", "Comment"}:
            raise InvalidRecord("review result is invalid")
        if not isinstance(row["findings_json"], list):
            raise InvalidRecord("review findings must be an array")
        findings = []
        for item in row["findings_json"]:
            finding = validate_payload(item)
            if finding["kind"] != "review-finding":
                raise InvalidRecord("review finding must be a review-finding payload")
            findings.append(finding)
        row["findings_json"] = findings
        canonical_json(row["findings_json"], root_type=list)
        if row["result"] in {"Approve", "ValidateOnly"}:
            if row["findings_json"] != []:
                raise InvalidRecord("Approve and ValidateOnly reviews must carry no findings")
        elif row["result"] in {"RequestChanges", "NeedsReplan"}:
            if not row["findings_json"]:
                raise InvalidRecord(
                    "RequestChanges and NeedsReplan reviews require at least one finding"
                )
        row["coverage_json"] = _json_object(row["coverage_json"], "coverage_json")
        row["correction_number"] = _nonnegative_int(row["correction_number"], "correction_number")
        if row["correction_number"] not in {0, 1}:
            raise InvalidRecord("review correction number is invalid")
        row["created_at"] = _timestamp(row["created_at"], "created_at")
        return row

    @staticmethod
    def _notification(value, now):
        fields = {"notification_id", "event_id", "run_id", "packet_id", "channel", "destination_reference", "audience", "severity", "message_type", "grouping_key", "escalation_at", "payload_json", "state", "attempt_count", "last_error_payload_json", "next_attempt_at"}
        row = _closed_mapping(value, fields, "notification")
        for field in {"notification_id", "run_id", "destination_reference", "audience", "message_type", "grouping_key"}:
            row[field] = _text(row[field], field)
        row["event_id"] = _positive_int(row["event_id"], "event_id")
        row["packet_id"] = _optional_text(row["packet_id"], "packet_id")
        if row["channel"] not in {"LocalDurable", "Slack"} or row["severity"] not in {"Informational", "ActionNeeded", "CompletionReady", "CompletionSummary"}:
            raise InvalidRecord("notification channel or severity is invalid")
        row["escalation_at"] = _optional_timestamp(row["escalation_at"], "escalation_at")
        row["payload_json"] = validate_payload(row["payload_json"])
        if row["payload_json"]["kind"] != "notification" or row["payload_json"]["event_id"] != row["event_id"]:
            raise InvalidRecord("notification payload must reference its source event")
        if row["state"] != "Pending" or row["attempt_count"] != 0 or row["last_error_payload_json"] is not None or row["next_attempt_at"] is not None:
            raise InvalidRecord("record_notification stores a pending unsent record")
        timestamp = _timestamp(now, "now")
        row.update(created_at=timestamp, updated_at=timestamp, version=1)
        return row

    @staticmethod
    def _worker_progress(value):
        fields = {"progress_id", "attempt_id", "plan_payload_json", "current_step_payload_json", "blocker_payload_json", "eta_text", "confidence", "status_request_state", "next_permitted_action", "observed_at", "received_at"}
        row = _closed_mapping(value, fields, "worker progress")
        for field in {"progress_id", "attempt_id", "next_permitted_action"}:
            row[field] = _text(row[field], field)
        for field in ("plan_payload_json", "current_step_payload_json", "blocker_payload_json"):
            row[field] = validate_payload(row[field])
            if row[field]["kind"] != "redacted-text":
                raise InvalidRecord("worker progress prose must be pre-redacted with a receipt")
        if not isinstance(row["eta_text"], str) or not (
            row["eta_text"] == "unknown" or _is_timestamp(row["eta_text"]) or _ISO_DURATION.fullmatch(row["eta_text"])
        ):
            raise InvalidRecord("worker ETA must be unknown, UTC time, or ISO-8601 duration")
        if row["confidence"] not in {"Reported", "Unknown"} or row["status_request_state"] not in {"NotRequested", "Requested", "Answered", "Unavailable"}:
            raise InvalidRecord("worker progress confidence/status request state is invalid")
        row["observed_at"] = _timestamp(row["observed_at"], "observed_at")
        row["received_at"] = _timestamp(row["received_at"], "received_at")
        return row

    @staticmethod
    def _context_usage(value, now):
        fields = {"context_usage_id", "attempt_id", "model_identity", "runtime_identity", "quantization", "configured_context_limit", "context_policy_digest", "counting_method", "starting_input_measurement_json", "future_growth_estimate_json", "token_measurements_json", "cost_measurement_json", "availability_state", "observed_at"}
        row = _closed_mapping(value, fields, "attempt context usage")
        for field in {"context_usage_id", "attempt_id", "model_identity", "runtime_identity"}:
            row[field] = _text(row[field], field)
        row["quantization"] = _optional_text(row["quantization"], "quantization")
        if row["configured_context_limit"] is not None:
            row["configured_context_limit"] = _positive_int(row["configured_context_limit"], "configured_context_limit")
        row["context_policy_digest"] = _digest(row["context_policy_digest"], "context_policy_digest")
        if row["counting_method"] not in {"Runtime", "Tokenizer", "Estimate", "Unavailable"}:
            raise InvalidRecord("context counting method is invalid")
        row["starting_input_measurement_json"] = validate_measurement(row["starting_input_measurement_json"])
        growth = _closed_mapping(row["future_growth_estimate_json"], {"lower_bound", "upper_bound"}, "future growth estimate")
        growth = {name: validate_measurement(growth[name]) for name in ("lower_bound", "upper_bound")}
        for bound in growth.values():
            if bound["quality"] != "Estimated":
                raise InvalidRecord("future growth bounds must be explicit estimates")
        if growth["lower_bound"]["source_reference"] != growth["upper_bound"]["source_reference"] or growth["lower_bound"]["observed_at"] != growth["upper_bound"]["observed_at"]:
            raise InvalidRecord("future growth bounds must share source and time")
        if growth["lower_bound"]["value"] > growth["upper_bound"]["value"]:
            raise InvalidRecord("future growth lower bound exceeds upper bound")
        row["future_growth_estimate_json"] = growth
        row["token_measurements_json"] = _token_measurements(row["token_measurements_json"])
        row["cost_measurement_json"] = validate_cost_measurement(row["cost_measurement_json"])
        if row["availability_state"] not in {"Available", "Partial", "Unavailable"}:
            raise InvalidRecord("context availability is invalid")
        row["observed_at"] = _timestamp(row["observed_at"], "observed_at")
        timestamp = _timestamp(now, "now")
        row.update(updated_at=timestamp, version=1)
        return row

    @staticmethod
    def _allowance(value):
        fields = {"allowance_observation_id", "provider", "account_reference", "native_window_type", "used_value", "remaining_value", "native_unit", "reset_at", "precision", "measurement_quality", "freshness", "observed_at"}
        row = _closed_mapping(value, fields, "allowance observation")
        row["allowance_observation_id"] = _text(row["allowance_observation_id"], "allowance_observation_id")
        row["provider"] = _provider(row["provider"])
        row["account_reference"] = _text(row["account_reference"], "account_reference")
        row["native_window_type"] = _text(row["native_window_type"], "native_window_type")
        row["reset_at"] = _optional_timestamp(row["reset_at"], "reset_at")
        row["observed_at"] = _timestamp(row["observed_at"], "observed_at")
        if row["precision"] not in {"Exact", "Coarse", "Unavailable"} or row["measurement_quality"] not in {"RuntimeReported", "ProviderReported", "Estimated", "Unavailable"} or row["freshness"] not in {"Fresh", "Stale", "Unavailable"}:
            raise InvalidRecord("allowance quality state is invalid")
        if row["precision"] == "Unavailable" or row["measurement_quality"] == "Unavailable" or row["freshness"] == "Unavailable":
            if any(row[name] is not None for name in ("used_value", "remaining_value", "native_unit", "reset_at")):
                raise InvalidRecord("unavailable allowance values must remain null")
            if (row["precision"], row["measurement_quality"], row["freshness"]) != ("Unavailable", "Unavailable", "Unavailable"):
                raise InvalidRecord("unavailable allowance labels must agree")
        else:
            row["used_value"] = _decimal_text(row["used_value"], "used_value") if row["used_value"] is not None else None
            row["remaining_value"] = _decimal_text(row["remaining_value"], "remaining_value") if row["remaining_value"] is not None else None
            row["native_unit"] = _text(row["native_unit"], "native_unit")
            if row["used_value"] is None and row["remaining_value"] is None:
                raise InvalidRecord("available allowance needs a used or remaining value")
        return row

    @staticmethod
    def _reconciliation(value):
        fields = {"usage_reconciliation_id", "allowance_observation_id", "window_change_value", "tracked_controlled_value", "registered_coarse_value", "unattributed_value", "native_unit", "measurement_quality", "observed_at"}
        row = _closed_mapping(value, fields, "usage reconciliation")
        for field in {"usage_reconciliation_id", "allowance_observation_id", "native_unit"}:
            row[field] = _text(row[field], field)
        for field in {"window_change_value", "tracked_controlled_value", "registered_coarse_value", "unattributed_value"}:
            row[field] = _decimal_text(row[field], field)
        if row["measurement_quality"] not in {"Exact", "Coarse", "Estimated"}:
            raise InvalidRecord("reconciliation quality is invalid")
        if Decimal(row["tracked_controlled_value"]) + Decimal(row["registered_coarse_value"]) + Decimal(row["unattributed_value"]) != Decimal(row["window_change_value"]):
            raise InvalidRecord("usage reconciliation does not balance exactly")
        row["observed_at"] = _timestamp(row["observed_at"], "observed_at")
        return row

    @staticmethod
    def _acceptance(value):
        fields = {"acceptance_id", "subject_type", "subject_id", "packet_id", "run_id", "sequence_number", "supersedes_acceptance_id", "required_authority", "decision", "authority_reference", "exact_head", "review_coverage_json", "reason_payload_json", "created_at"}
        row = _closed_mapping(value, fields, "acceptance record")
        for field in {"acceptance_id", "subject_id", "authority_reference"}:
            row[field] = _text(row[field], field)
        for field in {"packet_id", "run_id", "supersedes_acceptance_id"}:
            row[field] = _optional_text(row[field], field)
        row["sequence_number"] = _positive_int(row["sequence_number"], "sequence_number")
        if row["subject_type"] not in {"Packet", "Run"} or row["sequence_number"] not in {1, 2} or row["required_authority"] not in {"ProjectArchitect", "Owner"} or row["decision"] not in {"Accepted", "Returned", "ReservedChoice"}:
            raise InvalidRecord("acceptance closed enum is invalid")
        if row["subject_type"] == "Packet":
            if row["packet_id"] != row["subject_id"] or row["run_id"] is not None:
                raise InvalidRecord("packet acceptance relation is invalid")
        elif row["run_id"] != row["subject_id"] or row["packet_id"] is not None:
            raise InvalidRecord("run acceptance relation is invalid")
        row["exact_head"] = _commit(row["exact_head"], "exact_head")
        row["review_coverage_json"] = _json_object(row["review_coverage_json"], "review_coverage_json")
        row["reason_payload_json"] = validate_payload(row["reason_payload_json"])
        if row["reason_payload_json"]["kind"] != "reason":
            raise InvalidRecord("acceptance reason must be a reason payload")
        row["created_at"] = _timestamp(row["created_at"], "created_at")
        return row

    @staticmethod
    def _merge_observation(value):
        fields = {"merge_observation_id", "run_id", "packet_id", "acceptance_id", "repository_reference", "default_branch", "accepted_head", "merge_commit", "source_kind", "source_reference", "performed_by_authority", "performed_by_reference", "delegation_reference", "review_coverage_json", "observed_at"}
        row = _closed_mapping(value, fields, "merge observation")
        for field in {"merge_observation_id", "run_id", "packet_id", "repository_reference", "default_branch", "source_reference", "performed_by_reference"}:
            row[field] = _text(row[field], field)
        row["acceptance_id"] = _optional_text(row["acceptance_id"], "acceptance_id")
        row["delegation_reference"] = _optional_text(row["delegation_reference"], "delegation_reference")
        row["accepted_head"] = _commit(row["accepted_head"], "accepted_head")
        row["merge_commit"] = _commit(row["merge_commit"], "merge_commit")
        if row["source_kind"] not in {"Git", "GitHub"}:
            raise InvalidRecord("merge source kind is invalid")
        if row["performed_by_authority"] == "Owner":
            if row["delegation_reference"] is not None:
                raise InvalidRecord("owner observation cannot carry delegation")
        elif row["performed_by_authority"] == "DelegatedIdentity":
            if row["delegation_reference"] is None:
                raise InvalidRecord("delegated observation requires delegation reference")
        else:
            raise InvalidRecord("merge performer authority is invalid")
        row["review_coverage_json"] = None if row["review_coverage_json"] is None else _json_object(row["review_coverage_json"], "review_coverage_json")
        row["observed_at"] = _timestamp(row["observed_at"], "observed_at")
        return row


def _actor(value: Actor | Mapping[str, Any]) -> dict[str, Any]:
    if isinstance(value, Actor):
        raw = asdict(value)
    else:
        if not isinstance(value, Mapping) or set(value) not in (
            {"actor_type", "actor_id", "correlation_id"},
            {"actor_type", "actor_id", "correlation_id", "causation_event_id"},
        ):
            raise InvalidRecord("actor has an invalid closed shape")
        raw = dict(value)
        raw.setdefault("causation_event_id", None)
    for field in ("actor_type", "actor_id", "correlation_id"):
        raw[field] = _text(raw[field], field)
    if raw["causation_event_id"] is not None:
        raw["causation_event_id"] = _positive_int(raw["causation_event_id"], "causation_event_id")
    return raw


def _assignment_lease_request(value: Any) -> dict[str, str]:
    row = _closed_mapping(
        value,
        {"executor_route", "expires_at", "holder_id", "lease_id", "worktree_path"},
        "assignment lease request",
    )
    row["executor_route"] = _text(row["executor_route"], "executor_route")
    row["expires_at"] = _timestamp(row["expires_at"], "expires_at")
    row["holder_id"] = _text(row["holder_id"], "holder_id")
    row["lease_id"] = _text(row["lease_id"], "lease_id")
    row["worktree_path"] = _text(row["worktree_path"], "worktree_path")
    return row


def _assignment_lock_requests(value: Any) -> list[dict[str, str]]:
    if not isinstance(value, list):
        raise InvalidRecord("assignment lock_requests must be an array")
    result = []
    for item in value:
        row = _closed_mapping(
            item, {"lock_id", "lock_kind", "resource_key"}, "assignment lock request"
        )
        row["lock_id"] = _text(row["lock_id"], "lock_id")
        row["lock_kind"] = _text(row["lock_kind"], "lock_kind")
        if row["lock_kind"] not in {"Path", "SharedBoundary", "FiniteResource"}:
            raise InvalidRecord("assignment lock_kind is invalid")
        row["resource_key"] = _text(row["resource_key"], "resource_key")
        result.append(row)
    resource_keys = [item["resource_key"] for item in result]
    if resource_keys != sorted(set(resource_keys)):
        raise InvalidRecord("assignment lock resources must be sorted and unique")
    lock_ids = [item["lock_id"] for item in result]
    if len(lock_ids) != len(set(lock_ids)):
        raise InvalidRecord("assignment lock IDs must be unique")
    canonical_json(result, root_type=list)
    return result


def _assignment_attempt_request(value: Any) -> dict[str, str]:
    row = _closed_mapping(
        value,
        {"attempt_id", "model_identity", "runtime_identity"},
        "assignment attempt request",
    )
    row["attempt_id"] = _text(row["attempt_id"], "attempt_id")
    row["model_identity"] = _text(row["model_identity"], "model_identity")
    row["runtime_identity"] = _text(row["runtime_identity"], "runtime_identity")
    return row


def _closed_mapping(value: Any, fields: set[str], name: str) -> dict[str, Any]:
    if not isinstance(value, Mapping) or set(value) != fields:
        raise InvalidRecord(f"{name} has an invalid closed shape")
    return dict(value)


def _text(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value:
        raise InvalidRecord(f"{name} must be non-empty UTF-8 text up to 512 bytes")
    try:
        byte_length = len(value.encode("utf-8"))
    except UnicodeEncodeError as error:
        raise InvalidRecord(f"{name} must be valid UTF-8 text") from error
    if byte_length > MAX_TEXT_BYTES:
        raise InvalidRecord(f"{name} must be non-empty UTF-8 text up to 512 bytes")
    if any(ord(character) < 32 or 127 <= ord(character) <= 159 for character in value):
        raise InvalidRecord(f"{name} contains a control character")
    return value


def _optional_text(value: Any, name: str) -> str | None:
    return None if value is None else _text(value, name)


def _commit(value: Any, name: str) -> str:
    if not isinstance(value, str) or _SHA40.fullmatch(value) is None:
        raise InvalidRecord(f"{name} must be a lowercase full Git commit")
    return value


def _digest(value: Any, name: str) -> str:
    if not isinstance(value, str) or _SHA64.fullmatch(value) is None:
        raise InvalidRecord(f"{name} must be a lowercase SHA-256 digest")
    return value


def _provider(value: Any) -> str:
    if not isinstance(value, str) or _PROVIDER.fullmatch(value) is None:
        raise SensitiveMaterialRejected("provider must match the closed non-secret grammar")
    return value


def _reference_name(value: Any) -> str:
    if not isinstance(value, str) or _REFERENCE_NAME.fullmatch(value) is None:
        raise SensitiveMaterialRejected("reference_name must match the closed non-secret grammar")
    return value


def _timestamp(value: Any, name: str) -> str:
    if not isinstance(value, str) or _UTC.fullmatch(value) is None:
        raise InvalidRecord(f"{name} must be a canonical UTC timestamp")
    try:
        datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%fZ")
    except ValueError as error:
        raise InvalidRecord(f"{name} must be a valid UTC timestamp") from error
    return value


def _is_timestamp(value: str) -> bool:
    try:
        _timestamp(value, "timestamp")
        return True
    except InvalidRecord:
        return False


def _optional_timestamp(value: Any, name: str) -> str | None:
    return None if value is None else _timestamp(value, name)


def _positive_int(value: Any, name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise InvalidRecord(f"{name} must be a positive integer")
    return value


def _nonnegative_int(value: Any, name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise InvalidRecord(f"{name} must be a non-negative integer")
    return value


def _sorted_unique_text(value: Any, name: str) -> list[str]:
    if not isinstance(value, list):
        raise InvalidRecord(f"{name} must be an array")
    result = [_text(item, f"{name} item") for item in value]
    if result != sorted(set(result)):
        raise InvalidRecord(f"{name} must be sorted and unique")
    canonical_json(result, root_type=list)
    return result


def _json_object(value: Any, name: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise InvalidRecord(f"{name} must be an object")
    result = dict(value)
    canonical_json(result, root_type=dict)
    return result


def _reject_unsafe_json(value: Any) -> None:
    if value is None or isinstance(value, (str, int, bool)):
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            raise InvalidRecord("NaN and infinity are not canonical operational facts")
        return
    if isinstance(value, list):
        for item in value:
            _reject_unsafe_json(item)
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if not isinstance(key, str):
                raise InvalidRecord("JSON object keys must be strings")
            if key in _BANNED_KEYS:
                raise SensitiveMaterialRejected("structured sensitive/raw field is rejected")
            _reject_unsafe_json(item)
        return
    raise InvalidRecord("unsupported JSON value type")


def _decimal_text(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value or "e" in value.lower() or value.startswith("+"):
        raise InvalidRecord(f"{name} must be normalized non-negative decimal text")
    try:
        number = Decimal(value)
    except InvalidOperation as error:
        raise InvalidRecord(f"{name} is not a decimal") from error
    if not number.is_finite() or number < 0:
        raise InvalidRecord(f"{name} must be finite and non-negative")
    canonical = format(number, "f")
    if "." in canonical:
        canonical = canonical.rstrip("0").rstrip(".")
    if canonical in {"", "-0"}:
        canonical = "0"
    if value != canonical:
        raise InvalidRecord(f"{name} is not normalized")
    return value


def _token_measurements(value: Any) -> dict[str, dict[str, Any]]:
    categories = {"input", "output", "cached_input", "reasoning", "total"}
    result = _closed_mapping(value, categories, "token measurements")
    return {name: validate_measurement(result[name]) for name in sorted(categories)}


def _fingerprint(operation: str, payload: Mapping[str, Any], actor: Mapping[str, Any]) -> str:
    managed_time_operations = {
        "record_project_bindings", "record_graph_projection", "record_runs", "record_packets",
        "record_attempts", "record_waits", "record_notifications", "record_context_usage",
        "update_context_usage",
    }

    def command_facts(value: Any) -> Any:
        if isinstance(value, Mapping):
            return {
                key: command_facts(item)
                for key, item in value.items()
                if operation not in managed_time_operations or key not in {"created_at", "updated_at", "version"}
            }
        if isinstance(value, list):
            return [command_facts(item) for item in value]
        return value

    return canonical_digest({"operation": operation, "payload": command_facts(payload), "actor": actor})


def _state_payload(
    entity_type: str, entity_id: str, state: str, version: int
) -> dict[str, Any]:
    return {
        "entity_id": entity_id,
        "entity_type": entity_type,
        "kind": "state",
        "state": state,
        "version": version,
    }


def _decode_row(row: dict[str, Any]) -> dict[str, Any]:
    for key, value in tuple(row.items()):
        if key.endswith("_json") and value is not None:
            row[key] = json.loads(str(value))
    return row


_ENTITY_TABLES = {
    "ProjectBinding": ("project_bindings", "binding_id"),
    "SecretReferenceObservation": ("secret_reference_observations", "secret_reference_observation_id"),
    "GraphProjection": ("graph_projections", "graph_projection_id"),
    "WorkItem": ("work_items", "work_item_id"),
    "Run": ("runs", "run_id"),
    "Packet": ("packets", "packet_id"),
    "Lease": ("leases", "lease_id"),
    "Attempt": ("attempts", "attempt_id"),
    "ResourceLock": ("resource_locks", "lock_id"),
    "Evidence": ("evidence", "evidence_id"),
    "Wait": ("waits", "wait_id"),
    "Review": ("reviews", "review_id"),
    "Notification": ("notifications", "notification_id"),
    "Acceptance": ("acceptance_records", "acceptance_id"),
    "MergeObservation": ("merge_observations", "merge_observation_id"),
    "WorkerProgress": ("worker_progress_observations", "progress_id"),
    "AttemptContextUsage": ("attempt_context_usage", "context_usage_id"),
    "AllowanceWindow": ("provider_allowance_windows", "allowance_observation_id"),
    "UsageReconciliation": ("usage_reconciliations", "usage_reconciliation_id"),
}
