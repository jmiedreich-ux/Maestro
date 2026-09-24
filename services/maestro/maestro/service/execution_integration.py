"""Execution integration: milestone branches, the project's first-in first-out integration queue and dependency delivery.

Approved packet revisions and dependency imports enter one durable queue. One persistent Integration Manager
works the head entry: the service creates the integration branch, merges the exact approved commit into the
current milestone head and pushes it; the manager resolves conflicts and makes only necessary in-scope
integration fixes; an independent reviewer checks any new integration code; the service then merges the
integration branch into the milestone branch without fast-forward and records success only after reading the
remote branch back. Nothing is forced, rebased or squashed; a changed target sends the entry back for a fresh
attempt and review.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Mapping

from maestro.agents.execution_contract import CODER_SCHEMA, REVIEWER_SCHEMA
from maestro.agents.transport import AgentAssignment
from maestro.foundation import DomainMigration, canonical_json

from . import execution_git
from .agent_runs import AgentRunError, RunBuild
from .registration_github import DestinationError

INTEGRATION_MIGRATION = DomainMigration(
    domain="service_execution",
    version=2,
    identity="service-execution-v2-integration",
    statements=(
        "ALTER TABLE service_execution_sessions ADD COLUMN role TEXT NOT NULL DEFAULT 'development_manager'",
        """
        CREATE TABLE service_execution_milestones(
            activity_id TEXT NOT NULL REFERENCES service_executions(activity_id),
            milestone_key TEXT NOT NULL,
            subject TEXT NOT NULL,
            record_json TEXT NOT NULL,
            record_sha256 TEXT NOT NULL,
            dependencies_json TEXT NOT NULL,
            branch TEXT,
            base_commit TEXT,
            head_commit TEXT,
            updated_at TEXT NOT NULL,
            PRIMARY KEY(activity_id, milestone_key)
        )
        """,
        """
        CREATE TABLE service_execution_queue(
            activity_id TEXT NOT NULL REFERENCES service_executions(activity_id),
            entry_id INTEGER NOT NULL,
            kind TEXT NOT NULL CHECK(kind IN ('packet', 'dependency_import')),
            packet_key TEXT,
            delivery_id TEXT,
            milestone_key TEXT NOT NULL,
            source_commit TEXT NOT NULL,
            attempt INTEGER NOT NULL DEFAULT 1,
            branch TEXT,
            state TEXT NOT NULL,
            target_before TEXT,
            merge_commit TEXT,
            head_commit TEXT,
            merged_commit TEXT,
            result_json TEXT,
            rounds_used INTEGER NOT NULL DEFAULT 0,
            round_limit INTEGER NOT NULL,
            pending_json TEXT NOT NULL DEFAULT '{}',
            note TEXT,
            enqueued_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            PRIMARY KEY(activity_id, entry_id)
        )
        """,
        """
        CREATE TABLE service_execution_integration_reviews(
            activity_id TEXT NOT NULL REFERENCES service_executions(activity_id),
            entry_id INTEGER NOT NULL,
            attempt INTEGER NOT NULL,
            review_round INTEGER NOT NULL,
            assignment_id TEXT NOT NULL,
            run_id TEXT NOT NULL,
            reviewer_tool TEXT NOT NULL,
            reviewer_model TEXT NOT NULL,
            author_tool TEXT NOT NULL,
            author_model TEXT NOT NULL,
            reviewed_base TEXT NOT NULL,
            reviewed_head TEXT NOT NULL,
            outcome TEXT NOT NULL CHECK(outcome IN ('APPROVE', 'REQUEST_CHANGES')),
            summary TEXT NOT NULL,
            findings_json TEXT NOT NULL,
            independence TEXT NOT NULL,
            created_at TEXT NOT NULL,
            PRIMARY KEY(activity_id, entry_id, attempt, review_round)
        )
        """,
        """
        CREATE TABLE service_execution_deliveries(
            activity_id TEXT NOT NULL REFERENCES service_executions(activity_id),
            delivery_id TEXT NOT NULL,
            provider_milestone TEXT NOT NULL,
            consumer_milestone TEXT NOT NULL,
            trigger_packet TEXT NOT NULL,
            source_commit TEXT NOT NULL,
            packet_set_json TEXT NOT NULL,
            closure_json TEXT NOT NULL,
            state TEXT NOT NULL,
            queue_entry INTEGER,
            import_commit TEXT,
            note TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            PRIMARY KEY(activity_id, delivery_id)
        )
        """,
    ),
)

_INTEGRATOR_TOOLS = ["Read", "Write", "Edit", "Bash", "Glob", "Grep"]
_ENTRY_FINISHED = ("merged", "withdrawn", "invalidated")
_PACKET_STARTED = ("reserved", "coding", "correcting", "publishing", "review_ready", "reviewing", "approved", "limit_paused")

_INTEGRATION_TASK = """You are the Maestro Integration Manager for one project's Execution. You assemble independently approved work into a milestone branch. You are not the packet's implementer: you do not add features the packet omitted, change scope or change the architecture. Work only from this assignment, the files under input/ and the working clone at output/work/. source/ is a read-only copy of the current milestone head; never modify source/ or input/.

1. Read input/entry.json (what is being integrated, the milestone, the exact target and source commits, and any conflicts), input/milestone.json (the milestone's outcome and integration points), input/packet.json or input/provider-packets.json (the exact packets whose code is being assembled, with their completion criteria and permitted paths), input/approvals.json (the independent approvals already earned) and input/source.diff (what the source commit adds to the target).
2. output/work is a git clone on branch {branch}. {merge_state} Current milestone head is {target}; the approved source commit is {source}. Never change branches, rewrite history, reset, rebase or squash.
3. Check that the assembled result is compatible: shared interfaces, dependencies, the connections the packets declare and the milestone's integration points. Run the real checks that prove it (the packets' own checks and any entry point they touch) from output/work, with PYTHONDONTWRITEBYTECODE=1, and read their results. An unavailable check is untested, never passed.
4. Change files only where an integration problem requires it: resolve conflicts, and make the smallest in-scope fix that a cross-packet incompatibility needs. Stay inside these paths: {paths}. If the assembled result needs a change of scope or architecture instead, stop and report it as a blocker. When nothing needs changing, change nothing.
5. Leave your work in output/work. You may commit; the service commits anything left over. Do not push.
6. Response: base_revision is {target}; changed_paths lists every file you changed yourself in output/work (empty when you changed nothing); checks lists each real command you ran with outcome passed, failed or untested and a short detail; evidence states what you observed about compatibility and connections; limitations, blockers and unfinished list anything not done (empty when none). result is completed when the branch is ready for independent review or needs none; use clarification_required with questions only if a missing prerequisite blocks it.
{correction}
Copy contract_version (1), assignment_id, run_id, session_id, project_id, activity_id, role, source_commit and decision_version exactly from assignment.json. Return only the structured response."""

_INTEGRATION_CORRECTION = """
This is a targeted correction. An independent reviewer requested changes to your integration changes (already on the branch; output/work starts from it). input/review-findings.json lists the blocking findings with their minimum corrections. Fix exactly those and what they affect."""

_INTEGRATION_REVIEW_TASK = """You are an independent reviewer of integration changes. You did not write this integration and you cannot change it. The packets being assembled were already independently approved; do not re-review their own code. Decide whether the integration itself, meaning the conflict resolutions and any new integration code, is correct and connects the assembled result. Work only from this assignment, the files under input/ and source/, a read-only checkout of the exact reviewed commit {head}. Never modify source/ or input/.

1. Read input/entry.json, input/milestone.json, input/packet.json or input/provider-packets.json, input/integration-result.json (the Integration Manager's report), input/range.json (the exact base, the milestone head before integration, and head you review), input/diff.patch (base..head) and input/integration-changes.diff (only what the Integration Manager added beyond the clean merge, or the conflict resolution){later}.
2. Check: conflict resolutions keep both sides' intent; new integration code is inside the permitted paths ({paths}) and needed; the packets' connections and the milestone's integration points still hold; the manager's checks are real. Independently run the relevant checks against source/ where you can (PYTHONDONTWRITEBYTECODE=1; work on a copy under scratch/ if a check writes).
3. A blocking finding names a concrete unmet requirement, the affected code, the impact and the minimum correction. Preferences are non_blocking. Give each finding a unique local_key and its locations.
4. Return review_outcome APPROVE only when there is no blocking finding; otherwise REQUEST_CHANGES with at least one. Copy reviewed_range exactly from input/range.json. independence states in one sentence that you did not author the integration. result is completed.
Copy contract_version (1), assignment_id, run_id, session_id, project_id, activity_id, role, source_commit and decision_version exactly from assignment.json. Return only the structured response."""


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _dump(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _json(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def milestone_closure(milestones: Mapping[str, Mapping[str, Any]], key: str) -> set[str]:
    """Every milestone the given one declares as a dependency, directly or through others."""
    seen: set[str] = set()
    stack = list(json.loads(milestones[key]["dependencies_json"])) if key in milestones else []
    while stack:
        current = stack.pop()
        if current in seen or current not in milestones:
            continue
        seen.add(current)
        stack.extend(json.loads(milestones[current]["dependencies_json"]))
    return seen


def is_delivered(packets: Mapping[str, Mapping[str, Any]], deliveries: list[Mapping[str, Any]], packet: Mapping[str, Any], dependency: str) -> bool:
    """A dependency is delivered when its provider is integrated and, across milestones, imported into the consumer's branch."""
    provider = packets.get(dependency)
    if provider is None or provider["state"] != "integrated":
        return False
    if provider.get("milestone_key") == packet.get("milestone_key"):
        return True
    return any(
        d["state"] == "delivered" and d["consumer_milestone"] == packet.get("milestone_key") and dependency in json.loads(d["packet_set_json"]) for d in deliveries
    )


class IntegrationMixin:
    """Integration behavior of ``ExecutionService``; uses its records, runs and destination helpers."""

    # ------------------------------------------------------------- milestones

    @staticmethod
    def _read_milestones(destination: Any, confirmed: Mapping[str, Any], repository: str) -> list[dict[str, Any]]:
        found: list[dict[str, Any]] = []
        for entry in confirmed["listing"]:
            if entry["kind"] != "development_milestone":
                continue
            data = destination.read_file(repository, entry["commit"], entry["path"])
            if data is None or hashlib.sha256(data).hexdigest() != entry["sha256"]:
                raise ValueError(f"the published milestone {entry['id']} does not match the confirmed hash")
            record = json.loads(data)
            found.append({"key": entry["id"], "record": record, "sha256": entry["sha256"], "dependencies": [str(d["id"]) for d in record.get("dependencies", [])]})
        return found

    def _milestones(self, activity_id: str) -> dict[str, dict[str, Any]]:
        return {m["milestone_key"]: m for m in self._rows("SELECT * FROM service_execution_milestones WHERE activity_id = ? ORDER BY milestone_key", (activity_id,))}

    def _load_milestones(self, row: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
        """The confirmed milestone records, read and hash-checked once (an Execution begun earlier reads them on first use)."""
        known = self._milestones(row["activity_id"])
        if known:
            return known
        destination = self._destination(self.profiles[json.loads(row["profile_json"])["profile"]])
        found = self._read_milestones(destination, json.loads(row["confirmed_ref_json"]), row["repository"])
        with self.database.transaction() as tx:
            for m in found:
                tx.execute(
                    "INSERT OR IGNORE INTO service_execution_milestones(activity_id, milestone_key, subject, record_json, record_sha256, dependencies_json, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (row["activity_id"], m["key"], str(m["record"].get("subject", m["key"])), canonical_json(m["record"]), m["sha256"], _dump(m["dependencies"]), _now()),
                )
        return self._milestones(row["activity_id"])

    def _ensure_branch(self, row: Mapping[str, Any], key: str) -> dict[str, Any]:
        """The milestone's integration branch, created lazily from the recorded code baseline and verified on the remote."""
        milestones = self._load_milestones(row)
        milestone = milestones.get(key)
        if milestone is None:
            raise AgentRunError("unknown_milestone", f"the confirmed breakdown has no milestone {key}")
        if milestone["head_commit"]:
            return milestone
        activity_id = row["activity_id"]
        branch = f"maestro/{activity_id}/milestone/{key}"
        destination = self._destination(self.profiles[json.loads(row["profile_json"])["profile"]])
        mirror = self._mirror(row["project_id"])
        destination.fetch_source(row["repository"], row["source_commit"], mirror)
        operation_id = f"{activity_id}-milestone-{key}-create"
        self._journal_begin(row, operation_id, key, "milestone_create", branch, row["source_commit"], destination.branch_head(row["repository"], branch))
        try:
            remote = destination.push_branch(row["repository"], mirror, branch, row["source_commit"])
        except DestinationError as error:
            self._journal_end(operation_id, "failed", None, f"{error.code}: {error}")
            raise
        with self.database.transaction() as tx:
            tx.execute("UPDATE service_execution_journal SET state = 'verified', remote_after = ? WHERE operation_id = ?", (remote, operation_id))
            tx.execute("UPDATE service_execution_milestones SET branch = ?, base_commit = ?, head_commit = ?, updated_at = ? WHERE activity_id = ? AND milestone_key = ?",
                       (branch, row["source_commit"], remote, _now(), activity_id, key))
            self._say(tx, row["project_id"], activity_id, f"Milestone branch {branch} created from the recorded code baseline {row['source_commit'][:12]} and verified on the remote.")
        return self._milestones(activity_id)[key]

    def _journal_begin(self, row: Mapping[str, Any], operation_id: str, ref: str, kind: str, branch: str, intended: str, before: str | None) -> None:
        with self.database.transaction() as tx:
            tx.execute(
                "INSERT OR IGNORE INTO service_execution_journal(operation_id, activity_id, packet_key, kind, repository, branch, profile_json, intended_head, remote_before, state, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'prepared', ?)",
                (operation_id, row["activity_id"], ref, kind, row["repository"], branch, row["profile_json"], intended, before, _now()),
            )

    def _journal_end(self, operation_id: str, state: str, after: str | None, detail: str | None) -> None:
        with self.database.transaction() as tx:
            tx.execute("UPDATE service_execution_journal SET state = ?, remote_after = ?, detail = ? WHERE operation_id = ?", (state, after, detail, operation_id))

    def _current_milestone_head(self, row: Mapping[str, Any], key: str) -> str:
        """The milestone's recorded head, after checking the remote still agrees (reconciling an ordinary advance is not needed: only the service writes it)."""
        milestone = self._ensure_branch(row, key)
        destination = self._destination(self.profiles[json.loads(row["profile_json"])["profile"]])
        remote = destination.branch_head(row["repository"], milestone["branch"])
        if remote != milestone["head_commit"]:
            raise DestinationError("target_changed", f"milestone branch {milestone['branch']} is at {(remote or 'nothing')[:12]}, not the recorded {milestone['head_commit'][:12]}", remote=remote)
        return str(milestone["head_commit"])

    # ------------------------------------------------------------ deliveries

    def _deliveries(self, activity_id: str) -> list[dict[str, Any]]:
        return self._rows("SELECT * FROM service_execution_deliveries WHERE activity_id = ? ORDER BY created_at, delivery_id", (activity_id,))

    def _plan_deliveries(self, row: Mapping[str, Any]) -> None:
        """Queue an import for every pending packet whose integrated dependency lives in another milestone.

        A code dependency may arrive early, before its milestone is promoted, only when the providing milestone is
        one the consuming milestone declares (directly or transitively) and everything accumulated on the providing
        branch lies inside that closure. Otherwise the dependency is held until the source milestone completes.
        """
        activity_id = row["activity_id"]
        packets = {p["packet_key"]: p for p in self._packets(activity_id)}
        needed: dict[tuple[str, str], list[str]] = {}
        for packet in packets.values():
            if packet["state"] not in {"pending", "reserved"}:
                continue
            for dep in json.loads(packet["dependency_keys_json"]):
                provider = packets.get(dep)
                if provider is None or provider["state"] != "integrated" or provider["milestone_key"] == packet["milestone_key"]:
                    continue
                needed.setdefault((provider["milestone_key"], packet["milestone_key"]), []).append(dep)
        if not needed:
            return
        milestones = self._load_milestones(row)
        deliveries = self._deliveries(activity_id)
        for (source, consumer), deps in sorted(needed.items()):
            live = [d for d in deliveries if d["provider_milestone"] == source and d["consumer_milestone"] == consumer and d["state"] in {"queued", "delivered", "held"}]
            if not [d for d in deps if not any(d in json.loads(c["packet_set_json"]) for c in live)]:
                continue
            provider_head = self._ensure_branch(row, source)["head_commit"]
            accumulated = sorted(p["packet_key"] for p in packets.values() if p["state"] == "integrated" and p["milestone_key"] == source)
            imported = sorted({k for d in deliveries if d["consumer_milestone"] == source and d["state"] == "delivered" for k in json.loads(d["packet_set_json"])})
            accumulated = sorted(set(accumulated) | set(imported))
            closure = milestone_closure(milestones, consumer)
            allowed = closure | {consumer}
            outside = sorted(k for k in accumulated if packets[k]["milestone_key"] not in allowed)
            eligible = source in closure and not outside
            delivery_id = f"dep-{len(deliveries) + 1}"
            reason = None if eligible else (
                f"milestone {source} is not a declared dependency of {consumer}" if source not in closure else "the providing branch holds packets outside the declared dependency closure: " + ", ".join(outside)
            ) + "; it waits for the source milestone to complete"
            with self.database.transaction() as tx:
                entry_id = None
                if eligible:
                    entry_id = self._enqueue(tx, row, "dependency_import", None, delivery_id, consumer, provider_head)
                tx.execute(
                    "INSERT INTO service_execution_deliveries(activity_id, delivery_id, provider_milestone, consumer_milestone, trigger_packet, source_commit, packet_set_json, closure_json, state, queue_entry, note, created_at, updated_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (activity_id, delivery_id, source, consumer, deps[0], provider_head, _dump(accumulated), _dump(sorted(closure)), "queued" if eligible else "held", entry_id, reason, _now(), _now()),
                )
                if eligible:
                    self._say(tx, row["project_id"], activity_id, f"Dependency delivery {delivery_id} recorded: {', '.join(accumulated)} from milestone {source} (commit {provider_head[:12]}) into milestone {consumer}; it entered the integration queue as entry {entry_id}.")
                else:
                    self._event(tx, activity_id, "dependency_held", deps[0], f"{deps[0]} cannot be delivered early to milestone {consumer}: {reason}")
                    self._say(tx, row["project_id"], activity_id, f"Dependency {deps[0]} is held: {reason}.")
            deliveries = self._deliveries(activity_id)

    # ----------------------------------------------------------------- queue

    def _queue(self, activity_id: str) -> list[dict[str, Any]]:
        return self._rows("SELECT * FROM service_execution_queue WHERE activity_id = ? ORDER BY entry_id", (activity_id,))

    def _enqueue(self, tx: Any, row: Mapping[str, Any], kind: str, packet_key: str | None, delivery_id: str | None, milestone: str, source: str) -> int:
        config = json.loads(row["config_json"])
        limit = int(config.get("reviews", {}).get("integration", {}).get("maximum_completed_rounds", 2))
        entry_id = int(tx.execute("SELECT COALESCE(MAX(entry_id), 0) + 1 FROM service_execution_queue WHERE activity_id = ?", (row["activity_id"],)).fetchone()[0])
        tx.execute(
            "INSERT INTO service_execution_queue(activity_id, entry_id, kind, packet_key, delivery_id, milestone_key, source_commit, state, round_limit, enqueued_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, 'queued', ?, ?, ?)",
            (row["activity_id"], entry_id, kind, packet_key, delivery_id, milestone, source, limit, _now(), _now()),
        )
        return entry_id

    def _enqueue_approved(self, row: Mapping[str, Any]) -> None:
        """Every independently approved packet revision joins the queue once, in the order the service saw its approval."""
        activity_id = row["activity_id"]
        queued = {e["packet_key"] for e in self._queue(activity_id) if e["kind"] == "packet" and e["state"] not in {"withdrawn", "invalidated"}}
        approved = [p for p in self._packets(activity_id) if p["state"] == "approved" and p["packet_key"] not in queued and not self._packet_pending(p).get("quarantined")]
        if not approved:
            return
        order = {r["packet_key"]: r["created_at"] for r in self._rows("SELECT packet_key, created_at FROM service_execution_reviews WHERE activity_id = ? AND outcome = 'APPROVE'", (activity_id,))}
        for packet in sorted(approved, key=lambda p: (order.get(p["packet_key"], ""), p["packet_key"])):
            with self.database.transaction() as tx:
                entry_id = self._enqueue(tx, row, "packet", packet["packet_key"], None, packet["milestone_key"], packet["head_commit"])
                self._say(tx, row["project_id"], activity_id, f"{packet['packet_key']} (approved revision {packet['head_commit'][:12]}) entered the integration queue as entry {entry_id}, for milestone {packet['milestone_key']}.")

    def _entry(self, activity_id: str, entry_id: int) -> dict[str, Any]:
        found = self._read("SELECT * FROM service_execution_queue WHERE activity_id = ? AND entry_id = ?", (activity_id, entry_id))
        assert found is not None
        return found

    def _save_entry(self, activity_id: str, entry_id: int, pending: Mapping[str, Any], **columns: object) -> None:
        sets = "".join(f", {name} = ?" for name in columns)
        with self.database.transaction() as tx:
            tx.execute(f"UPDATE service_execution_queue SET pending_json = ?, updated_at = ?{sets} WHERE activity_id = ? AND entry_id = ?", (canonical_json(pending), _now(), *columns.values(), activity_id, entry_id))

    def _advance_integration(self, row: Mapping[str, Any]) -> None:
        """Work the head of the queue; a blocked head stays first and nothing behind it is started."""
        assert self.runs is not None
        entries = [e for e in self._queue(row["activity_id"]) if e["state"] not in _ENTRY_FINISHED]
        if not entries:
            return
        head = entries[0]
        state = head["state"]
        try:
            if state == "queued":
                self._integration_start(row, head)
            elif state == "integrating":
                self._advance_integrator(row, head)
            elif state == "publishing":
                self._integration_publish(row, head)
            elif state == "reviewing":
                self._advance_integration_review(row, head)
            elif state == "merging":
                self._integration_merge(row, head)
        except DestinationError as error:
            if error.code == "target_changed":
                self._target_changed(row, head, str(error))
            elif error.code in {"github_unreachable"} or (isinstance(error.fields.get("status"), int) and error.fields["status"] >= 500):
                raise
            else:
                self._block_entry(row, head, f"{error.code}: {error}")
        except (execution_git.GitError, AgentRunError, ValueError) as error:
            self._block_entry(row, head, f"{getattr(error, 'code', type(error).__name__)}: {error}")

    def _block_entry(self, row: Mapping[str, Any], entry: Mapping[str, Any], reason: str) -> None:
        with self.database.transaction() as tx:
            current = self._row(tx, "SELECT state FROM service_execution_queue WHERE activity_id = ? AND entry_id = ?", (row["activity_id"], entry["entry_id"]))
            if current is None or current["state"] in {*_ENTRY_FINISHED, "blocked", "limit_paused"}:
                return
            tx.execute("UPDATE service_execution_queue SET state = 'blocked', note = ?, updated_at = ? WHERE activity_id = ? AND entry_id = ?", (reason[:500], _now(), row["activity_id"], entry["entry_id"]))
            self._event(tx, row["activity_id"], "integration_blocked", entry["packet_key"], f"queue entry {entry['entry_id']} is blocked: {reason[:300]}")
            self._say(tx, row["project_id"], row["activity_id"], f"Queue entry {entry['entry_id']} is blocked: {reason[:400]}. It stays first in the queue; nothing behind it is skipped.")

    def _entry_subject(self, entry: Mapping[str, Any]) -> str:
        return entry["packet_key"] if entry["kind"] == "packet" else f"dependency delivery {entry['delivery_id']}"

    # ------------------------------------------------------------ integrator

    def _integrator_route(self, row: Mapping[str, Any]) -> dict[str, Any]:
        config = json.loads(row["config_json"])
        configured = config.get("integration_manager")
        if configured:
            return dict(configured)
        return {"tool": row["manager_tool"], "model": row["manager_model"], "run_timeout_seconds": config["development_manager"]["run_timeout_seconds"]}

    def _integration_session(self, row: Mapping[str, Any], route: Mapping[str, Any]) -> None:
        if self._read("SELECT 1 AS n FROM service_execution_sessions WHERE activity_id = ? AND role = 'integration_manager' AND state = 'active'", (row["activity_id"],)) is None:
            with self.database.transaction() as tx:
                tx.execute(
                    "INSERT INTO service_execution_sessions(session_id, activity_id, tool, model, assigned_provider_id, state, created_at, role) VALUES (?, ?, ?, ?, ?, 'active', ?, 'integration_manager')",
                    (f"{row['activity_id']}-isession-1", row["activity_id"], route["tool"], route["model"], str(uuid.uuid4()) if route["tool"] == "claude_code" else None, _now()),
                )

    def _entry_inputs(self, row: Mapping[str, Any], entry: Mapping[str, Any], target: str) -> dict[str, bytes]:
        milestone = self._milestones(row["activity_id"])[entry["milestone_key"]]
        packets = {p["packet_key"]: p for p in self._packets(row["activity_id"])}
        inputs: dict[str, bytes] = {"milestone.json": milestone["record_json"].encode("utf-8")}
        detail: dict[str, Any] = {"entry_id": entry["entry_id"], "kind": entry["kind"], "milestone": entry["milestone_key"], "target_branch": milestone["branch"], "target_commit": target,
                                  "source_commit": entry["source_commit"], "attempt": entry["attempt"], "integration_branch": entry["branch"]}
        if entry["kind"] == "packet":
            packet = packets[entry["packet_key"]]
            inputs["packet.json"] = packet["record_json"].encode("utf-8")
            reviews = self._rows("SELECT review_round, reviewer_tool, reviewer_model, reviewed_head, outcome, summary FROM service_execution_reviews WHERE activity_id = ? AND packet_key = ? ORDER BY review_round", (row["activity_id"], packet["packet_key"]))
            inputs["approvals.json"] = _json({"packet": packet["packet_key"], "approved_revision": packet["head_commit"], "reviews": reviews})
            detail["packet"] = packet["packet_key"]
        else:
            delivery = self._read("SELECT * FROM service_execution_deliveries WHERE activity_id = ? AND delivery_id = ?", (row["activity_id"], entry["delivery_id"]))
            assert delivery is not None
            keys = json.loads(delivery["packet_set_json"])
            inputs["provider-packets.json"] = _json({"packets": [json.loads(packets[k]["record_json"]) for k in keys if k in packets]})
            inputs["approvals.json"] = _json({"delivery": delivery["delivery_id"], "provider_milestone": delivery["provider_milestone"], "integrated_packets": keys, "note": "each packet was independently approved and integrated into the provider milestone branch"})
            detail.update({"delivery": delivery["delivery_id"], "provider_milestone": delivery["provider_milestone"], "packets": keys, "declared_closure": json.loads(delivery["closure_json"])})
        pending = json.loads(entry["pending_json"] or "{}")
        detail["conflicts"] = pending.get("conflicts", [])
        inputs["entry.json"] = _json(detail)
        return inputs

    def _allowed_paths(self, row: Mapping[str, Any], entry: Mapping[str, Any]) -> list[str]:
        """In-scope integration changes stay inside the permitted paths of the packets being assembled or already in the milestone."""
        paths: list[str] = []
        for packet in self._packets(row["activity_id"]):
            if packet["milestone_key"] == entry["milestone_key"] or packet["packet_key"] == entry["packet_key"]:
                paths.extend(json.loads(packet["record_json"]).get("permitted_paths", []))
            elif entry["kind"] == "dependency_import" and packet["state"] == "integrated":
                paths.extend(json.loads(packet["record_json"]).get("permitted_paths", []))
        return sorted(set(paths))

    def _integration_start(self, row: Mapping[str, Any], entry: Mapping[str, Any], recovery_note: str | None = None) -> None:
        assert self.runs is not None
        activity_id, entry_id = row["activity_id"], int(entry["entry_id"])
        pending = json.loads(entry["pending_json"] or "{}")
        route = self._integrator_route(row)
        milestone = self._ensure_branch(row, entry["milestone_key"])
        destination = self._destination(self.profiles[json.loads(row["profile_json"])["profile"]])
        correction = pending.get("correction")
        suffix = f"r{entry['attempt']}" if int(entry["attempt"]) > 1 else ""
        branch = entry["branch"] or (f"maestro/{activity_id}/integration/q{entry_id}{suffix}" if entry["kind"] == "packet" else f"maestro/{activity_id}/dependency/{entry['delivery_id']}{suffix}")
        target = str(entry["target_before"]) if correction else self._current_milestone_head(row, entry["milestone_key"])
        mirror = self._mirror(row["project_id"])
        for commit in (target, entry["source_commit"], *( [entry["head_commit"]] if correction else [])):
            destination.fetch_source(row["repository"], commit, mirror)
        staging = self.state_dir / "execution" / activity_id / f"integration-q{entry_id}-a{entry['attempt']}"
        shutil.rmtree(staging, ignore_errors=True)
        staging.parent.mkdir(parents=True, exist_ok=True)
        subject = self._entry_subject(entry)
        if correction:
            execution_git.prepare_clone(mirror, str(entry["head_commit"]), staging, branch)
            conflicts: list[str] = pending.get("conflicts", [])
            merge_state = "It starts from your earlier integration commit, which an independent reviewer questioned."
        else:
            conflicts = execution_git.prepare_merge(mirror, target, entry["source_commit"], staging, branch, f"Integrate {subject} into milestone {entry['milestone_key']}")
            pending.update({"conflicts": conflicts, "merge_commit": None if conflicts else execution_git.git(staging, "rev-parse", "HEAD").strip()})
            merge_state = (
                f"The service merged the approved source into the milestone head without fast-forward and the merge is committed (no conflicts); verify it." if not conflicts
                else "The service started the merge and it has conflicts in: " + ", ".join(conflicts) + ". The merge is in progress in the clone: resolve every conflict, keep both sides' intent, stage the files and commit (git commit --no-edit)."
            )
        pending.update({"target_before": target, "run_base": target, "staging": str(staging)})
        attempt = int(pending.get("integrator_attempt", 0)) + (1 if recovery_note is None else 0)
        assignment_id = f"{activity_id}-q{entry_id}a{entry['attempt']}-integrate-{attempt}"
        inputs = self._entry_inputs(row, {**entry, "pending_json": canonical_json(pending), "branch": branch}, target)
        source_diff = execution_git.git(staging, "diff", "--no-color", "--no-renames", f"{target}...{entry['source_commit']}", check=False)
        inputs["source.diff"] = source_diff.encode("utf-8")
        if correction:
            inputs["review-findings.json"] = _json({"findings": correction["findings"]})
        allowed = self._allowed_paths(row, entry)
        note = "" if not recovery_note else f"\nThe previous run's output was rejected: {recovery_note}. Fix exactly that."
        task = _INTEGRATION_TASK.format(branch=branch, merge_state=merge_state, target=target, source=entry["source_commit"], paths=", ".join(allowed) or "none", correction=(_INTEGRATION_CORRECTION if correction else "") + note)
        self._integration_session(row, route)
        session, replacement_note = self._session_use(row, "integration_manager")
        if replacement_note:
            task += "\n" + replacement_note
        elif session.provider_session_id is not None:
            task += "\nThis session continues: your earlier integrations' conversation is restored; the saved records in input/ are authoritative."

        def prepare(workspace) -> None:
            shutil.copytree(staging, workspace.paths.output / "work", symlinks=True)
            execution_git.make_writable(workspace.paths.output / "work")
            execution_git.prepare_agent_home(workspace.paths.scratch / "home")

        def build(run_id: str) -> RunBuild:
            assignment = AgentAssignment(
                project_id=row["project_id"], activity_id=activity_id, assignment_id=assignment_id, run_id=run_id, parent_assignment_id=None, role="integration_manager",
                role_responsibilities=("Assemble independently approved work into the milestone branch: resolve conflicts and make only necessary in-scope integration fixes; never change scope or architecture.",),
                task=task, source_commit=target, decision_version=f"i{attempt}",
                instructions={"session_id": session.session_id, "claude_tools": _INTEGRATOR_TOOLS, "task_kind": "integrate", "entry": entry_id, "branch": branch},
                permitted_actions=("read_source", "write_output"), writable_locations=("output", "scratch"), limits={"run_timeout_seconds": route["run_timeout_seconds"]},
                clarification_conditions=("A missing prerequisite blocks the integration.",), response_schema=CODER_SCHEMA, contract="execution",
            )
            return RunBuild(assignment, mirror, inputs, session, prepare)

        pending.pop("integrator_run", None)
        self._launch(row, pending, "integrator_run", assignment_id, route["tool"], route["model"], route["run_timeout_seconds"], recovery_note is not None, build, "integration_manager",
                     save=lambda _a, p: self._save_entry(activity_id, entry_id, p))
        pending["integrator_attempt"] = attempt
        pending["integrator"] = {"tool": route["tool"], "model": route["model"]}
        with self.database.transaction() as tx:
            tx.execute("UPDATE service_execution_queue SET state = 'integrating', branch = ?, target_before = ?, merge_commit = COALESCE(?, merge_commit), pending_json = ?, updated_at = ? WHERE activity_id = ? AND entry_id = ?",
                       (branch, target, pending.get("merge_commit"), canonical_json(pending), _now(), activity_id, entry_id))
            self._say(tx, row["project_id"], activity_id,
                      f"Integration Manager started for queue entry {entry_id} ({subject}): {route['tool']} {route['model']}, assignment {assignment_id}, milestone {entry['milestone_key']} head {target[:12]}, source {entry['source_commit'][:12]}, branch {branch}"
                      + (f"; conflicts in {', '.join(conflicts)}" if conflicts else "; the merge is clean") + (" (correction)" if correction else "") + ".")
            self._activity(tx, activity_id, "running", f"Integrating {subject} into milestone {entry['milestone_key']}")

    def _advance_integrator(self, row: Mapping[str, Any], entry: Mapping[str, Any]) -> None:
        assert self.runs is not None
        activity_id, entry_id = row["activity_id"], int(entry["entry_id"])
        pending = json.loads(entry["pending_json"] or "{}")
        current = pending.get("integrator_run")
        if current is None:
            self._integration_start(row, entry)
            return
        view = self.runs.poll(current["run_id"])
        if view.state in {"reserved", "running", "stopping"}:
            return
        self._remember_conversation(activity_id, current["run_id"], "integration_manager")
        assignment = self.runs.assignment_state(current["assignment_id"])
        if view.state == "completed":
            if assignment["state"] == "waiting_for_answers":
                self._block_entry(row, entry, "the Integration Manager needs information it does not have: " + str((self.runs.response(current["run_id"]) or {}).get("summary", ""))[:300])
                return
            self._finish_integrator(row, entry, pending, current)
            return
        if assignment["state"] == "needs_recovery":
            detail = view.terminal_reason or view.failure_code or "technical_failure"
            if pending.get("last_recovery_detail") == detail:
                self._block_entry(row, entry, f"the same integration error came back after a correction: {detail}")
                return
            pending["last_recovery_detail"] = detail
            pending.pop("integrator_run", None)
            self._save_entry(activity_id, entry_id, pending)
            self._integration_start(row, {**entry, "pending_json": canonical_json(pending)}, recovery_note=detail)
            return
        if view.state == "cancelled":
            return
        self._block_entry(row, entry, f"integration run {view.state}" + (f" ({view.failure_code})" if view.failure_code else "") + (f": {view.terminal_reason}" if view.terminal_reason else ""))

    def _finish_integrator(self, row: Mapping[str, Any], entry: Mapping[str, Any], pending: dict[str, Any], current: Mapping[str, str]) -> None:
        assert self.runs is not None
        activity_id, entry_id = row["activity_id"], int(entry["entry_id"])
        response = self.runs.response(current["run_id"]) or {}
        target = str(pending["target_before"])
        output = self._run_workspace(current["run_id"])
        try:
            if output is None or not (output / "work").is_dir():
                raise execution_git.GitError("work_missing", "the Integration Manager's working clone is missing")
            if response.get("base_revision") != pending["run_base"]:
                raise execution_git.GitError("wrong_base", f"the manager reported base {response.get('base_revision')}, not {pending['run_base']}")
            if response.get("blockers") or response.get("unfinished"):
                self._block_entry(row, entry, "the Integration Manager reports blockers or unfinished work: " + "; ".join(map(str, [*response.get("blockers", []), *response.get("unfinished", [])]))[:400])
                return
            work = output / "work"
            sealed = execution_git.seal_integration(work, entry["branch"], target, entry["source_commit"], f"Integration fixes for {self._entry_subject(entry)}")
            conflicts = pending.get("conflicts", [])
            merge_commit = pending.get("merge_commit")
            head = str(sealed["head"])
            if merge_commit:
                extra = sorted(p for p in execution_git.git(work, "diff", "--name-only", "--no-renames", merge_commit, head).split("\n") if p)
                changed = head != merge_commit
                integration_diff = execution_git.git(work, "diff", "--no-color", "--no-renames", merge_commit, head)
            else:
                source_paths = {p for p in execution_git.git(work, "diff", "--name-only", "--no-renames", f"{target}...{entry['source_commit']}").split("\n") if p}
                extra = sorted(set(sealed["changed_paths"]) - source_paths)
                changed = True
                integration_diff = execution_git.git(work, "diff-tree", "--cc", "--no-color", "-p", head)
            outside = execution_git.outside_scope(extra, self._allowed_paths(row, entry))
            if outside:
                raise execution_git.GitError("out_of_scope", "the integration changed paths outside the permitted paths of the assembled packets: " + ", ".join(outside[:8]))
            diff = execution_git.git(work, "diff", "--no-color", "--no-renames", target, head)
        except execution_git.GitError as error:
            self._reject_integrator_result(row, entry, pending, current, f"{error.code}: {error}")
            return
        directory = self.state_dir / "execution" / activity_id / f"integration-q{entry_id}-a{entry['attempt']}"
        directory.mkdir(parents=True, exist_ok=True)
        round_number = int(entry["rounds_used"]) + 1
        (directory / f"round-{round_number}.diff").write_text(diff, encoding="utf-8")
        (directory / f"round-{round_number}.integration.diff").write_text(integration_diff, encoding="utf-8")
        keep = directory / f"clone-{int(pending.get('integrator_attempt', 1))}"
        shutil.rmtree(keep, ignore_errors=True)
        shutil.copytree(work, keep, symlinks=True)
        result = {"response": response, "head": head, "target": target, "source": entry["source_commit"], "changed_paths": extra, "conflicts": conflicts, "changed": changed,
                  "merge_commit": merge_commit, "run_evidence": self.runs.run_evidence(current["run_id"]), "diff_file": str(directory / f"round-{round_number}.diff"),
                  "integration_diff_file": str(directory / f"round-{round_number}.integration.diff")}
        pending.update({"pushing": {"head": head, "clone": str(keep)}})
        for name in ("integrator_run", "correction", "last_recovery_detail"):
            pending.pop(name, None)
        with self.database.transaction() as tx:
            tx.execute("UPDATE service_execution_queue SET state = 'publishing', head_commit = ?, result_json = ?, pending_json = ?, updated_at = ? WHERE activity_id = ? AND entry_id = ?",
                       (head, canonical_json(result), canonical_json(pending), _now(), activity_id, entry_id))
            self._say(tx, row["project_id"], activity_id,
                      f"Integration result for queue entry {entry_id} accepted for publication: "
                      + ("no integration code change beyond the clean merge" if not changed else f"integration changes in {', '.join(extra) or 'the conflict resolution'}")
                      + f"; local integration head {head[:12]}. The service verifies it on the remote next.")

    def _reject_integrator_result(self, row: Mapping[str, Any], entry: Mapping[str, Any], pending: dict[str, Any], current: Mapping[str, str], reason: str) -> None:
        assert self.runs is not None
        self.runs.reject_result(current["run_id"], "malformed_response", reason)
        assignment = self.runs.assignment_state(current["assignment_id"])
        if assignment["state"] != "needs_recovery" or pending.get("last_recovery_detail") == reason:
            self._block_entry(row, entry, f"the Integration Manager's result was rejected: {reason}")
            return
        pending["last_recovery_detail"] = reason
        pending.pop("integrator_run", None)
        self._save_entry(row["activity_id"], int(entry["entry_id"]), pending)
        self._integration_start(row, {**entry, "pending_json": canonical_json(pending)}, recovery_note=reason)

    def _integration_publish(self, row: Mapping[str, Any], entry: Mapping[str, Any]) -> None:
        activity_id, entry_id = row["activity_id"], int(entry["entry_id"])
        pending = json.loads(entry["pending_json"])
        push = pending["pushing"]
        destination = self._destination(self.profiles[json.loads(row["profile_json"])["profile"]])
        operation_id = f"{activity_id}-q{entry_id}a{entry['attempt']}-push-{push['head'][:12]}"
        if self._read("SELECT 1 AS n FROM service_execution_journal WHERE operation_id = ?", (operation_id,)) is None:
            self._journal_begin(row, operation_id, f"entry-{entry_id}", "integration_push", entry["branch"], push["head"], destination.branch_head(row["repository"], entry["branch"]))
        try:
            remote = destination.push_branch(row["repository"], Path(push["clone"]), entry["branch"], push["head"])
        except DestinationError as error:
            if error.code in {"github_unreachable", "push_failed"}:
                raise
            self._journal_end(operation_id, "failed", None, f"{error.code}: {error}"[:300])
            raise
        destination.fetch_source(row["repository"], remote, self._mirror(row["project_id"]))
        result = json.loads(entry["result_json"])
        pending.pop("pushing", None)
        shutil.rmtree(push["clone"], ignore_errors=True)
        changed = bool(result["changed"])
        with self.database.transaction() as tx:
            tx.execute("UPDATE service_execution_journal SET state = 'verified', remote_after = ? WHERE operation_id = ?", (remote, operation_id))
            tx.execute("UPDATE service_execution_queue SET state = ?, head_commit = ?, merge_commit = ?, pending_json = ?, updated_at = ? WHERE activity_id = ? AND entry_id = ?",
                       ("reviewing" if changed else "merging", remote, result["merge_commit"], canonical_json(pending), _now(), activity_id, entry_id))
            self._say(tx, row["project_id"], activity_id,
                      f"Integration branch {entry['branch']} verified on the remote at {remote[:12]}. "
                      + ("Independent integration review is next." if changed else "The Integration Manager changed no code beyond the clean merge, so no repeat review of the approved packet is started; the integration evidence is recorded."))
            self._emit(tx, row["project_id"], activity_id, "execution.integration_published", {"entry": entry_id, "branch": entry["branch"], "commit": remote})

    # -------------------------------------------------------------- reviewer

    def _integration_reviewer_route(self, config: Mapping[str, Any], author: Mapping[str, Any]) -> dict[str, Any]:
        pair = config.get("integration_reviewers") or config["reviewers"]["packet"]
        for name in ("primary", "backup"):
            candidate = pair.get(name)
            if candidate and (candidate["tool"], candidate["model"]) != (author["tool"], author["model"]):
                return candidate
        raise AgentRunError("no_independent_reviewer", "no configured integration reviewer differs from the Integration Manager's tool and model")

    def _integration_review_start(self, row: Mapping[str, Any], entry: Mapping[str, Any], recovery_note: str | None = None) -> None:
        assert self.runs is not None
        activity_id, entry_id = row["activity_id"], int(entry["entry_id"])
        config = json.loads(row["config_json"])
        pending = json.loads(entry["pending_json"] or "{}")
        author = pending["integrator"]
        reviewer = self._integration_reviewer_route(config, author)
        round_number = int(entry["rounds_used"]) + 1
        assignment_id = f"{activity_id}-q{entry_id}a{entry['attempt']}-ireview-{round_number}"
        result = json.loads(entry["result_json"])
        head, base = entry["head_commit"], result["target"]
        mirror = self._mirror(row["project_id"])
        destination = self._destination(self.profiles[json.loads(row["profile_json"])["profile"]])
        destination.fetch_source(row["repository"], head, mirror)
        inputs = self._entry_inputs(row, entry, base)
        inputs.update({
            "range.json": _json({"base": base, "head": head, "branch": entry["branch"]}),
            "integration-result.json": _json({k: v for k, v in result.items() if k in {"response", "conflicts", "changed", "changed_paths", "merge_commit"}}),
            "diff.patch": Path(result["diff_file"]).read_bytes(), "integration-changes.diff": Path(result["integration_diff_file"]).read_bytes(),
        })
        prior = self._rows("SELECT findings_json FROM service_execution_integration_reviews WHERE activity_id = ? AND entry_id = ? AND attempt = ? ORDER BY review_round", (activity_id, entry_id, entry["attempt"]))
        if prior:
            inputs["prior-findings.json"] = _json({"findings": json.loads(prior[-1]["findings_json"])})
        later = ", input/prior-findings.json (your earlier findings; recheck them and what the correction changed)" if prior else ""
        note = "" if not recovery_note else f"\nThe previous run's output was rejected: {recovery_note}. Fix exactly that."
        task = _INTEGRATION_REVIEW_TASK.format(head=head, later=later, paths=", ".join(self._allowed_paths(row, entry)) or "none") + note

        def build(run_id: str) -> RunBuild:
            assignment = AgentAssignment(
                project_id=row["project_id"], activity_id=activity_id, assignment_id=assignment_id, run_id=run_id, parent_assignment_id=None, role="integration_reviewer",
                role_responsibilities=("Decide whether the exact integration revision is correct; never edit code or authorize a merge.",),
                task=task, source_commit=head, decision_version=f"ir{round_number}",
                instructions={"session_id": run_id, "claude_tools": ["Read", "Bash", "Glob", "Grep"], "task_kind": "review_integration", "entry": entry_id},
                permitted_actions=("read_source",), writable_locations=("output", "scratch"), limits={"run_timeout_seconds": reviewer["run_timeout_seconds"]},
                clarification_conditions=("The range cannot be verified.",), response_schema=REVIEWER_SCHEMA, contract="execution",
            )
            return RunBuild(assignment, mirror, inputs, None)

        self._launch(row, pending, "reviewer_run", assignment_id, reviewer["tool"], reviewer["model"], reviewer["run_timeout_seconds"], recovery_note is not None, build, "integration_reviewer",
                     save=lambda _a, p: self._save_entry(activity_id, entry_id, p))
        pending["reviewer"] = {"tool": reviewer["tool"], "model": reviewer["model"]}
        limit = int(entry["round_limit"]) + len(pending.get("grants", []))
        with self.database.transaction() as tx:
            tx.execute("UPDATE service_execution_queue SET state = 'reviewing', pending_json = ?, updated_at = ? WHERE activity_id = ? AND entry_id = ?", (canonical_json(pending), _now(), activity_id, entry_id))
            self._say(tx, row["project_id"], activity_id,
                      f"Independent integration review round {round_number} of {limit} for queue entry {entry_id} started: reviewer {reviewer['tool']} {reviewer['model']} (integrator {author['tool']} {author['model']}), exact revision {head[:12]}.")
            self._activity(tx, activity_id, "running", f"Reviewing the integration of {self._entry_subject(entry)} (round {round_number})")

    def _advance_integration_review(self, row: Mapping[str, Any], entry: Mapping[str, Any]) -> None:
        assert self.runs is not None
        activity_id, entry_id = row["activity_id"], int(entry["entry_id"])
        pending = json.loads(entry["pending_json"] or "{}")
        current = pending.get("reviewer_run")
        if current is None:
            self._integration_review_start(row, entry)
            return
        view = self.runs.poll(current["run_id"])
        if view.state in {"reserved", "running", "stopping"}:
            return
        assignment = self.runs.assignment_state(current["assignment_id"])
        if view.state == "completed":
            self._accept_integration_review(row, entry, pending, current)
            return
        if assignment["state"] == "needs_recovery":
            detail = view.terminal_reason or view.failure_code or "technical_failure"
            if pending.get("last_recovery_detail") == detail:
                self._block_entry(row, entry, f"the same integration reviewer error came back after a correction: {detail}")
                return
            pending["last_recovery_detail"] = detail
            pending.pop("reviewer_run", None)
            self._save_entry(activity_id, entry_id, pending)
            self._integration_review_start(row, {**entry, "pending_json": canonical_json(pending)}, recovery_note=detail)
            return
        if view.state == "cancelled":
            return
        self._block_entry(row, entry, f"integration reviewer run {view.state}" + (f" ({view.failure_code})" if view.failure_code else "") + (f": {view.terminal_reason}" if view.terminal_reason else ""))

    def _accept_integration_review(self, row: Mapping[str, Any], entry: Mapping[str, Any], pending: dict[str, Any], current: Mapping[str, str]) -> None:
        assert self.runs is not None
        activity_id, entry_id = row["activity_id"], int(entry["entry_id"])
        response = self.runs.response(current["run_id"]) or {}
        result = json.loads(entry["result_json"])
        expected = {"base": result["target"], "head": entry["head_commit"]}
        if response.get("result") != "completed" or response.get("reviewed_range") != expected:
            self.runs.reject_result(current["run_id"], "conflicting_response", "the review does not state the exact range it was given")
            pending.pop("reviewer_run", None)
            if self.runs.assignment_state(current["assignment_id"])["state"] != "needs_recovery":
                self._block_entry(row, entry, "the integration review did not state the exact revision it reviewed")
                return
            self._save_entry(activity_id, entry_id, pending)
            self._integration_review_start(row, {**entry, "pending_json": canonical_json(pending)}, recovery_note="the review must copy reviewed_range exactly from input/range.json")
            return
        round_number = int(entry["rounds_used"]) + 1
        findings = [{**f, "finding_id": f"{activity_id}-q{entry_id}a{entry['attempt']}-r{round_number}-{f['local_key']}"} for f in response.get("findings", [])]
        reviewer, integrator = pending["reviewer"], pending["integrator"]
        outcome = response["review_outcome"]
        blocking = [f for f in findings if f["severity"] == "blocking"]
        limit = int(entry["round_limit"]) + len(pending.get("grants", []))
        with self.database.transaction() as tx:
            tx.execute(
                "INSERT INTO service_execution_integration_reviews(activity_id, entry_id, attempt, review_round, assignment_id, run_id, reviewer_tool, reviewer_model, author_tool, author_model, reviewed_base, reviewed_head, outcome, summary, findings_json, independence, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (activity_id, entry_id, entry["attempt"], round_number, current["assignment_id"], current["run_id"], reviewer["tool"], reviewer["model"], integrator["tool"], integrator["model"],
                 expected["base"], expected["head"], outcome, str(response["summary"])[:2000], _dump(findings), str(response.get("independence", ""))[:500], _now()),
            )
            pending.pop("reviewer_run", None)
            pending.pop("last_recovery_detail", None)
            subject = self._entry_subject(entry)
            if outcome == "APPROVE":
                tx.execute("UPDATE service_execution_queue SET state = 'merging', rounds_used = ?, pending_json = ?, updated_at = ? WHERE activity_id = ? AND entry_id = ?", (round_number, canonical_json(pending), _now(), activity_id, entry_id))
                self._say(tx, row["project_id"], activity_id, f"Integration review round {round_number} of {limit} for queue entry {entry_id} ({subject}): APPROVED at {expected['head'][:12]} by {reviewer['tool']} {reviewer['model']}. {str(response['summary'])[:300]}")
            elif round_number < limit:
                pending["correction"] = {"findings": blocking, "round": round_number}
                tx.execute("UPDATE service_execution_queue SET state = 'queued', rounds_used = ?, pending_json = ?, note = ?, updated_at = ? WHERE activity_id = ? AND entry_id = ?",
                           (round_number, canonical_json(pending), f"correcting {len(blocking)} blocking finding(s)", _now(), activity_id, entry_id))
                self._say(tx, row["project_id"], activity_id, f"Integration review round {round_number} of {limit} for queue entry {entry_id}: changes requested ({len(blocking)} blocking): " + "; ".join(f['subject'] for f in blocking)[:400] + ". The Integration Manager gets one targeted correction.")
            else:
                pending["limit"] = {"assignment_id": current["assignment_id"], "round": round_number}
                tx.execute("UPDATE service_execution_queue SET state = 'limit_paused', rounds_used = ?, pending_json = ?, note = ?, updated_at = ? WHERE activity_id = ? AND entry_id = ?",
                           (round_number, canonical_json(pending), f"integration review limit reached with {len(blocking)} blocking finding(s)", _now(), activity_id, entry_id))
                self._event(tx, activity_id, "limit_reached", entry["packet_key"], f"queue entry {entry_id} reached its integration review limit with blocking findings; the Owner decides")
                self._say(tx, row["project_id"], activity_id, f"Integration review round {round_number} of {limit} for queue entry {entry_id}: blocking findings remain at the limit, so nothing merges and the entry stays first in the queue. Grant one extra attempt or keep it paused.")

    # ----------------------------------------------------------------- merge

    def _integration_merge(self, row: Mapping[str, Any], entry: Mapping[str, Any]) -> None:
        """Merge the reviewed integration branch into the milestone branch without fast-forward and record it only after the remote read-back."""
        activity_id, entry_id = row["activity_id"], int(entry["entry_id"])
        pending = json.loads(entry["pending_json"] or "{}")
        milestone = self._ensure_branch(row, entry["milestone_key"])
        destination = self._destination(self.profiles[json.loads(row["profile_json"])["profile"]])
        target = str(entry["target_before"])
        merging = pending.get("merging")
        operation_id = f"{activity_id}-q{entry_id}a{entry['attempt']}-merge"
        if merging is None:
            remote = destination.branch_head(row["repository"], milestone["branch"])
            if remote != milestone["head_commit"] or remote != target:
                raise DestinationError("target_changed", f"milestone branch {milestone['branch']} is at {(remote or 'nothing')[:12]}; the integration was reviewed against {target[:12]}", remote=remote)
            mirror = self._mirror(row["project_id"])
            destination.fetch_source(row["repository"], entry["head_commit"], mirror)
            staging = self.state_dir / "execution" / activity_id / f"merge-q{entry_id}-a{entry['attempt']}"
            shutil.rmtree(staging, ignore_errors=True)
            merge_commit = execution_git.merge_into(mirror, target, entry["head_commit"], staging, f"maestro-merge-q{entry_id}", f"Merge {self._entry_subject(entry)} into milestone {entry['milestone_key']} (queue entry {entry_id})")
            merging = {"commit": merge_commit, "clone": str(staging)}
            pending["merging"] = merging
            self._save_entry(activity_id, entry_id, pending)
            self._journal_begin(row, operation_id, f"entry-{entry_id}", "milestone_merge", milestone["branch"], merge_commit, remote)
        try:
            remote_after = destination.push_branch(row["repository"], Path(merging["clone"]), milestone["branch"], merging["commit"], expected_before=target)
        except DestinationError as error:
            if error.code in {"github_unreachable", "push_failed"}:
                raise
            if error.code != "target_changed":
                self._journal_end(operation_id, "failed", None, f"{error.code}: {error}"[:300])
            raise
        shutil.rmtree(merging["clone"], ignore_errors=True)
        pending.pop("merging", None)
        with self.database.transaction() as tx:
            tx.execute("UPDATE service_execution_journal SET state = 'verified', remote_after = ? WHERE operation_id = ?", (remote_after, operation_id))
            tx.execute("UPDATE service_execution_milestones SET head_commit = ?, updated_at = ? WHERE activity_id = ? AND milestone_key = ?", (remote_after, _now(), activity_id, entry["milestone_key"]))
            tx.execute("UPDATE service_execution_queue SET state = 'merged', merged_commit = ?, pending_json = ?, note = NULL, updated_at = ? WHERE activity_id = ? AND entry_id = ?", (remote_after, canonical_json(pending), _now(), activity_id, entry_id))
            if entry["kind"] == "packet":
                tx.execute("UPDATE service_execution_packets SET state = 'integrated', note = NULL, updated_at = ? WHERE activity_id = ? AND packet_key = ? AND state = 'approved'", (_now(), activity_id, entry["packet_key"]))
                self._event(tx, activity_id, "packet_integrated", entry["packet_key"], f"{entry['packet_key']} integrated into milestone {entry['milestone_key']} at {remote_after[:12]}")
                subject = f"{entry['packet_key']} is integrated into milestone {entry['milestone_key']}"
            else:
                tx.execute("UPDATE service_execution_deliveries SET state = 'delivered', import_commit = ?, updated_at = ? WHERE activity_id = ? AND delivery_id = ? AND state = 'queued'", (remote_after, _now(), activity_id, entry["delivery_id"]))
                self._event(tx, activity_id, "dependency_delivered", None, f"{entry['delivery_id']} delivered into milestone {entry['milestone_key']} at {remote_after[:12]}")
                subject = f"dependency delivery {entry['delivery_id']} is imported into milestone {entry['milestone_key']}"
            self._say(tx, row["project_id"], activity_id, f"Verified on the remote: {subject}. Milestone branch {milestone['branch']} moved from {target[:12]} to {remote_after[:12]} by a non-fast-forward merge of {entry['head_commit'][:12]} (queue entry {entry_id}).")
            self._emit(tx, row["project_id"], activity_id, "execution.integrated", {"entry": entry_id, "milestone": entry["milestone_key"], "commit": remote_after})

    def _target_changed(self, row: Mapping[str, Any], entry: Mapping[str, Any], reason: str) -> None:
        """The milestone branch moved after the integration was prepared: reconcile with a fresh attempt and review; earlier records stay."""
        activity_id, entry_id = row["activity_id"], int(entry["entry_id"])
        milestone = self._milestones(activity_id)[entry["milestone_key"]]
        destination = self._destination(self.profiles[json.loads(row["profile_json"])["profile"]])
        remote = destination.branch_head(row["repository"], milestone["branch"])
        pending = json.loads(entry["pending_json"] or "{}")
        adopt = remote is not None and remote != milestone["head_commit"] and destination.contains(row["repository"], milestone["head_commit"], remote)
        if remote is not None and remote != milestone["head_commit"] and not adopt:
            self._block_entry(row, entry, f"the milestone branch no longer contains the recorded head {milestone['head_commit'][:12]}: {reason}")
            return
        if pending.get("merging"):
            shutil.rmtree(pending["merging"]["clone"], ignore_errors=True)
        fresh = {"grants": pending.get("grants", [])}
        with self.database.transaction() as tx:
            if adopt:
                tx.execute("UPDATE service_execution_milestones SET head_commit = ?, updated_at = ? WHERE activity_id = ? AND milestone_key = ?", (remote, _now(), activity_id, entry["milestone_key"]))
            tx.execute(
                "UPDATE service_execution_queue SET state = 'queued', attempt = attempt + 1, branch = NULL, target_before = NULL, merge_commit = NULL, head_commit = NULL, result_json = NULL, rounds_used = 0, pending_json = ?, note = ?, updated_at = ? "
                "WHERE activity_id = ? AND entry_id = ?",
                (canonical_json(fresh), "the target changed after preparation; a new integration attempt with a fresh review", _now(), activity_id, entry_id),
            )
            self._event(tx, activity_id, "integration_reconciled", entry["packet_key"], f"queue entry {entry_id}: {reason[:200]}; it is integrated again from the current head")
            self._say(tx, row["project_id"], activity_id, f"The target changed under queue entry {entry_id}: {reason}. The earlier integration and its review stay on record; the entry keeps its place and is integrated again from the current milestone head, with a new review of any changed code.")

    # ------------------------------------------------------------ invalidation

    def _verify_deliveries(self, row: Mapping[str, Any]) -> None:
        """Delivered source evidence that no longer exists on the provider's branch invalidates the delivery and everything built on it."""
        activity_id = row["activity_id"]
        pending = json.loads(row["pending_json"] or "{}")
        now = _now()
        if pending.get("delivery_check_at", "") > now:
            return
        deliveries = [d for d in self._deliveries(activity_id) if d["state"] in {"delivered", "queued"}]
        if not deliveries:
            return
        destination = self._destination(self.profiles[json.loads(row["profile_json"])["profile"]])
        milestones = self._milestones(activity_id)
        for delivery in deliveries:
            provider = milestones.get(delivery["provider_milestone"])
            if provider is None or not provider["branch"]:
                continue
            try:
                head = destination.branch_head(row["repository"], provider["branch"])
                ok = head is not None and destination.contains(row["repository"], delivery["source_commit"], head)
            except DestinationError:
                continue  # an unreadable remote is not evidence that the source changed
            if not ok:
                self.invalidate_delivery(row, delivery, f"the providing branch {provider['branch']} no longer contains the delivered source {delivery['source_commit'][:12]}")
        fresh = self._read("SELECT pending_json FROM service_executions WHERE activity_id = ?", (activity_id,))
        pending = json.loads(fresh["pending_json"] or "{}") if fresh else {}
        pending["delivery_check_at"] = _future(60)
        self._save_pending(activity_id, pending)

    def invalidate_delivery(self, row: Mapping[str, Any], delivery: Mapping[str, Any], reason: str) -> None:
        """Atomically invalidate a delivery and its consumers: start nothing new on it, quarantine running results, keep every old record."""
        activity_id = row["activity_id"]
        provided = set(json.loads(delivery["packet_set_json"]))
        downstream = [d for d in self._deliveries(activity_id)
                      if d["state"] in {"queued", "delivered", "held"} and d["delivery_id"] != delivery["delivery_id"]
                      and d["provider_milestone"] == delivery["consumer_milestone"] and provided & set(json.loads(d["packet_set_json"]))]
        with self.database.transaction() as tx:
            tx.execute("UPDATE service_execution_deliveries SET state = 'invalidated', note = ?, updated_at = ? WHERE activity_id = ? AND delivery_id = ?", (reason[:500], _now(), activity_id, delivery["delivery_id"]))
            if delivery["queue_entry"]:
                tx.execute("UPDATE service_execution_queue SET state = 'invalidated', note = ?, updated_at = ? WHERE activity_id = ? AND entry_id = ? AND state NOT IN ('merged', 'withdrawn', 'invalidated')", (reason[:300], _now(), activity_id, delivery["queue_entry"]))
            affected: list[str] = []
            for packet in self._row_list(tx, "SELECT * FROM service_execution_packets WHERE activity_id = ? AND milestone_key = ?", (activity_id, delivery["consumer_milestone"])):
                if not provided & set(json.loads(packet["dependency_keys_json"])):
                    continue
                affected.append(packet["packet_key"])
                pending = json.loads(packet["pending_json"] or "{}")
                if packet["state"] == "pending":
                    tx.execute("UPDATE service_execution_packets SET note = ?, updated_at = ? WHERE activity_id = ? AND packet_key = ?", (f"waiting for a replacement delivery: {reason[:200]}", _now(), activity_id, packet["packet_key"]))
                elif packet["state"] != "integrated":
                    pending["quarantined"] = reason[:300]
                    tx.execute("UPDATE service_execution_packets SET pending_json = ?, note = ?, updated_at = ? WHERE activity_id = ? AND packet_key = ?", (canonical_json(pending), f"quarantined until reconciled: {reason[:200]}", _now(), activity_id, packet["packet_key"]))
                    tx.execute("UPDATE service_execution_queue SET state = 'invalidated', note = ?, updated_at = ? WHERE activity_id = ? AND packet_key = ? AND state NOT IN ('merged', 'withdrawn', 'invalidated')", (reason[:300], _now(), activity_id, packet["packet_key"]))
            self._event(tx, activity_id, "dependency_invalidated", None, f"{delivery['delivery_id']} invalidated: {reason[:200]}; affected packets: {', '.join(affected) or 'none'}")
            self._say(tx, row["project_id"], activity_id, f"Dependency delivery {delivery['delivery_id']} is invalidated: {reason}. New starts and merges on it stop; affected packets: {', '.join(affected) or 'none'}. Old records are kept; a replacement delivery is queued when its provider is integrated again.")
        for later in downstream:
            self.invalidate_delivery(row, later, f"it was built on invalidated delivery {delivery['delivery_id']}: {reason[:150]}")

    def _integration_decision(self, tx: Any, request: Any, row: Mapping[str, Any], payload: Mapping[str, Any], next_version: int) -> Any:
        """The Owner's typed choice at an integration review limit: one extra correction attempt or stay paused; approval is never forced."""
        from .registry import OperationResult
        from .requests import RequestRejection

        activity_id = row["activity_id"]
        found = None
        for candidate in self._row_list(tx, "SELECT * FROM service_execution_queue WHERE activity_id = ? AND state = 'limit_paused'", (activity_id,)):
            if json.loads(candidate["pending_json"]).get("limit", {}).get("assignment_id") == payload["assignment_id"]:
                found = candidate
        if found is None:
            raise RequestRejection(409, "no_decision_pending", "no integration review-limit decision is pending for that review assignment")
        pending = json.loads(found["pending_json"])
        grants = list(pending.get("grants", []))
        entry_id = int(found["entry_id"])
        subject = self._entry_subject(found)
        if payload["choice"] == "remain_paused":
            text = f"Owner chose to keep queue entry {entry_id} ({subject}) paused at {found['rounds_used']} of {int(found['round_limit']) + len(grants)} integration review rounds. Nothing was approved and no count changed."
        else:
            grants.append({"request_id": request.request_id, "assignment_id": payload["assignment_id"], "granted_at": _now()})
            pending["grants"] = grants
            findings = json.loads(self._row(tx, "SELECT findings_json FROM service_execution_integration_reviews WHERE activity_id = ? AND entry_id = ? AND attempt = ? AND review_round = ?", (activity_id, entry_id, found["attempt"], found["rounds_used"]))["findings_json"])
            pending["correction"] = {"findings": [f for f in findings if f["severity"] == "blocking"], "round": int(found["rounds_used"])}
            pending.pop("limit", None)
            tx.execute("UPDATE service_execution_queue SET state = 'queued', pending_json = ?, note = 'one extra integration review attempt granted', updated_at = ? WHERE activity_id = ? AND entry_id = ?", (canonical_json(pending), _now(), activity_id, entry_id))
            text = f"Owner granted one extra integration review attempt for queue entry {entry_id} ({subject}) (limit now {int(found['round_limit']) + len(grants)}); the base limit is unchanged and approval is not forced."
        self._activity(tx, activity_id, "running", text, version=next_version)
        self._say(tx, row["project_id"], activity_id, text)
        return OperationResult(data={"activity_id": activity_id, "decision": payload["choice"], "packet": subject, "message": text}, status="accepted", project_id=row["project_id"], activity_id=activity_id)

    # ----------------------------------------------------------------- views

    def integration_view(self, activity_id: str) -> dict[str, Any]:
        milestones = self._milestones(activity_id)
        entries = []
        for e in self._queue(activity_id):
            pending = json.loads(e["pending_json"] or "{}")
            reviews = self._rows("SELECT attempt, review_round, outcome, reviewer_tool, reviewer_model, reviewed_head, summary, findings_json FROM service_execution_integration_reviews WHERE activity_id = ? AND entry_id = ? ORDER BY attempt, review_round", (activity_id, e["entry_id"]))
            result = json.loads(e["result_json"]) if e["result_json"] else None
            entries.append({
                "entry_id": e["entry_id"], "kind": e["kind"], "packet_key": e["packet_key"], "delivery_id": e["delivery_id"], "milestone": e["milestone_key"], "state": e["state"], "attempt": e["attempt"],
                "source_commit": e["source_commit"], "target_before": e["target_before"], "branch": e["branch"], "integration_head": e["head_commit"], "merged_commit": e["merged_commit"],
                "conflicts": pending.get("conflicts", []), "code_changed": None if result is None else result["changed"], "integration_changes": [] if result is None else result["changed_paths"],
                "manager": pending.get("integrator"), "review": {"completed": e["rounds_used"], "limit": int(e["round_limit"]) + len(pending.get("grants", []))}, "note": e["note"],
                "reviews": [{"attempt": r["attempt"], "round": r["review_round"], "outcome": r["outcome"], "reviewer": f"{r['reviewer_tool']} {r['reviewer_model']}", "head": r["reviewed_head"], "summary": r["summary"],
                             "blocking": sum(1 for f in json.loads(r["findings_json"]) if f["severity"] == "blocking")} for r in reviews],
            })
        deliveries = [{"delivery_id": d["delivery_id"], "provider": d["provider_milestone"], "consumer": d["consumer_milestone"], "state": d["state"], "source_commit": d["source_commit"], "packets": json.loads(d["packet_set_json"]),
                      "queue_entry": d["queue_entry"], "import_commit": d["import_commit"], "note": d["note"]} for d in self._deliveries(activity_id)]
        return {"milestones": [{"key": k, "subject": m["subject"], "dependencies": json.loads(m["dependencies_json"]), "branch": m["branch"], "base_commit": m["base_commit"], "head_commit": m["head_commit"]} for k, m in milestones.items()],
                "queue": entries, "deliveries": deliveries}


def _future(seconds: int) -> str:
    return (datetime.now(timezone.utc) + timedelta(seconds=seconds)).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
