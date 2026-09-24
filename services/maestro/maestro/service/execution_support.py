"""Execution architectural support: a missing specialist role reaches its own bounded Project Architect assignment.

The Development Manager records that no role adequately covers a packet. The service starts a support assignment
from the parent Execution's configuration snapshot; the architect either names an existing role, drafts a new
role and starting context inside the confirmed scope, or says the gap needs re-registration. A new role gets an
independent fidelity review. The service publishes the exact files and support records to the project's
publication branch, reads the bytes back and only then binds the role to the affected packets and tells the
Development Manager. Nothing here edits the confirmed breakdown or dispatches code.
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Callable, Mapping

from maestro.agents.execution_contract import REVIEWER_SCHEMA, SUPPORT_ARCHITECT_SCHEMA, SUPPORT_LIMIT_SCHEMA
from maestro.agents.transport import AgentAssignment
from maestro.foundation import DomainMigration, canonical_json

from .agent_runs import AgentRunError, RunBuild
from .architecture_records import CONTEXT_HEADINGS, ROLE_HEADINGS, _headings, encode, kebab
from .registration_github import DestinationError

SUPPORT_MIGRATION = DomainMigration(
    domain="service_execution",
    version=3,
    identity="service-execution-v3-architectural-support",
    statements=(
        """
        CREATE TABLE service_execution_architect(
            activity_id TEXT NOT NULL REFERENCES service_executions(activity_id),
            assignment_key TEXT NOT NULL,
            kind TEXT NOT NULL CHECK(kind IN ('support', 'determination', 'milestone_gap')),
            packet_key TEXT,
            subject TEXT NOT NULL,
            trigger_json TEXT NOT NULL,
            state TEXT NOT NULL,
            version INTEGER NOT NULL DEFAULT 1,
            config_json TEXT NOT NULL,
            pending_json TEXT NOT NULL DEFAULT '{}',
            result_json TEXT,
            reviews_used INTEGER NOT NULL DEFAULT 0,
            review_limit INTEGER NOT NULL DEFAULT 0,
            note TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            PRIMARY KEY(activity_id, assignment_key)
        )
        """,
        """
        CREATE TABLE service_execution_support_reviews(
            activity_id TEXT NOT NULL REFERENCES service_executions(activity_id),
            support_id TEXT NOT NULL,
            support_version INTEGER NOT NULL,
            review_round INTEGER NOT NULL,
            assignment_id TEXT NOT NULL,
            run_id TEXT NOT NULL,
            reviewer_tool TEXT NOT NULL,
            reviewer_model TEXT NOT NULL,
            author_tool TEXT NOT NULL,
            author_model TEXT NOT NULL,
            inventory_sha256 TEXT NOT NULL,
            outcome TEXT NOT NULL CHECK(outcome IN ('APPROVE', 'REQUEST_CHANGES')),
            summary TEXT NOT NULL,
            findings_json TEXT NOT NULL,
            independence TEXT NOT NULL,
            created_at TEXT NOT NULL,
            PRIMARY KEY(activity_id, support_id, review_round)
        )
        """,
        """
        CREATE TABLE service_execution_support_bindings(
            activity_id TEXT NOT NULL REFERENCES service_executions(activity_id),
            support_id TEXT NOT NULL,
            support_version INTEGER NOT NULL,
            packet_key TEXT NOT NULL,
            role_path TEXT NOT NULL,
            role_sha256 TEXT NOT NULL,
            context_path TEXT,
            context_sha256 TEXT,
            commit_sha TEXT NOT NULL,
            state TEXT NOT NULL CHECK(state IN ('active', 'invalidated')),
            activation_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            PRIMARY KEY(activity_id, support_id, packet_key)
        )
        """,
    ),
)

_ARCHITECT_TOOLS = ["Read", "Glob", "Grep"]
_SUPPORT_OPEN = ("requested", "drafting", "reviewing", "correcting", "publishing", "recommending")
_SUPPORT_FINISHED = ("active", "superseded")
_AREA = re.compile(r"(?!/)(?!.*(?:^|/)\.\.?(?:/|$))[A-Za-z0-9._/-]+\Z")


def _now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _dump(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _json(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


_SUPPORT_TASK = """You are the Maestro architectural-support Project Architect for one project's Execution. A work packet has no adequate specialist role. You decide, within the confirmed scope and architecture, whether an existing role already covers it or a new role is needed. You are not the architecture loop: you do not change scope, responsibilities, the confirmed breakdown or the packet, and you cannot dispatch code. Work only from this assignment, the files under input/ and the read-only source/ clone.

1. Read input/request.json (why the Development Manager says no role covers the packet), input/packets.json (the affected packets: scope, permitted paths, completion criteria), input/existing-roles.json (every role the confirmed breakdown already provides, with its path, hash and text) and input/execution.json. Read source/ where you need to verify facts.
2. Decide the disposition. use_existing: an existing role in existing-roles.json already covers the packet; give its exact path in existing_role_path. create_role: no existing role covers it and a new role fits the confirmed scope; supply source_area (a repository-relative directory that contains the packet's permitted paths, no leading slash), role_title, role_markdown and context_markdown. replanning_required: covering it would change scope, established responsibilities or the confirmed breakdown.
3. role_markdown must begin with a first heading naming the role title and contain the headings {role_headings}. context_markdown must contain the headings {context_headings} and hold only facts you verified in source/ (each with its source path) plus honest knowledge gaps. Never invent facts. Never restate or replace an existing role's authority.
4. packet_keys lists every affected packet the result covers (at least the requested ones). rationale states in plain words why.
5. result is completed. Ask a question (clarification_required) only when missing information changes the answer.
{correction}
Copy contract_version (1), assignment_id, run_id, session_id, project_id, activity_id, role, source_commit and decision_version exactly from assignment.json. Return only the structured response."""

_SUPPORT_CORRECTION = """
This is a correction. An independent fidelity reviewer found blocking problems in your earlier draft (input/prior-draft.json, input/review-findings.json). Amend the role and starting context to fix exactly those findings and what they affect; do not change what was not questioned. Return the whole amended draft."""

_SUPPORT_REVIEW_TASK = """You are an independent fidelity reviewer of a newly drafted specialist role and its starting context. You did not write them and you cannot change them. Decide whether they faithfully fit the confirmed architecture and the affected packets. Work only from this assignment, the files under input/ and the read-only source/ clone.

1. Read input/draft.json (the source area, role title and why), input/role.md, input/context.md, input/packets.json (the affected packets), input/existing-roles.json (roles that already exist and must not be contradicted) and input/inventory.json (the exact files and hashes you review){later}.
2. Check: the role fits the confirmed scope and does not change responsibilities or replace an existing role; the role covers what the affected packets need; every fact in the starting context is true in source/ (verify at least the ones the packets depend on); the required headings are present. This is not a search for improvements. A blocking finding names a concrete unmet requirement, the affected text, the impact and the minimum correction; preferences are non_blocking. Give each finding a unique local_key.
3. Return review_outcome APPROVE only when there is no blocking finding; otherwise REQUEST_CHANGES with at least one. Copy reviewed_range exactly from input/reviewed-range.json. independence states in one sentence that you did not author the draft. result is completed.
Copy contract_version (1), assignment_id, run_id, session_id, project_id, activity_id, role, source_commit and decision_version exactly from assignment.json. Return only the structured response."""

_SUPPORT_LIMIT_TASK = """You are the Maestro architectural-support Project Architect. Independent fidelity review of a new role reached its configured limit with blocking findings still open. Give the Owner your recommendation. Work only from this assignment and the files under input/.

1. Read input/support.json (the exact reviewed support version, review count and prior grants), input/review-findings.json (the open blocking findings) and input/draft.json.
2. Recommend grant_one (one more completed review is likely to resolve the material findings) or remain_paused (the findings show the role is not achievable inside the confirmed scope or another round is unlikely to help), with a plain rationale. Your recommendation grants nothing.
3. Copy support_id, support_version and completed_reviews exactly from input/support.json. result is completed.
Copy contract_version (1), assignment_id, run_id, session_id, project_id, activity_id, role, source_commit and decision_version exactly from assignment.json. Return only the structured response."""


class SupportMixin:
    """Architectural-support behavior of ``ExecutionService``."""

    # ------------------------------------------------------------ records

    def _architects(self, activity_id: str, kind: str | None = None) -> list[dict[str, Any]]:
        if kind is None:
            return self._rows("SELECT * FROM service_execution_architect WHERE activity_id = ? ORDER BY created_at, rowid", (activity_id,))
        return self._rows("SELECT * FROM service_execution_architect WHERE activity_id = ? AND kind = ? ORDER BY created_at, rowid", (activity_id, kind))

    def _architect(self, activity_id: str, key: str) -> dict[str, Any]:
        found = self._read("SELECT * FROM service_execution_architect WHERE activity_id = ? AND assignment_key = ?", (activity_id, key))
        assert found is not None
        return found

    def _save_architect(self, activity_id: str, key: str, pending: Mapping[str, Any], **columns: object) -> None:
        sets = "".join(f", {name} = ?" for name in columns)
        with self.database.transaction() as tx:
            tx.execute(f"UPDATE service_execution_architect SET pending_json = ?, updated_at = ?{sets} WHERE activity_id = ? AND assignment_key = ?",
                       (canonical_json(pending), _now(), *columns.values(), activity_id, key))

    def _held_by_support(self, activity_id: str) -> dict[str, str]:
        """Packets that must not start while their support assignment is unresolved."""
        held: dict[str, str] = {}
        for arch in self._architects(activity_id, "support"):
            if arch["state"] not in _SUPPORT_FINISHED:
                held[str(arch["packet_key"])] = f"architectural support {arch['assignment_key']} is {arch['state']}: {arch['note'] or 'the packet waits for the specialist role'}"
        return held

    def _support_binding(self, activity_id: str, packet_key: str) -> dict[str, Any] | None:
        return self._read("SELECT * FROM service_execution_support_bindings WHERE activity_id = ? AND packet_key = ? AND state = 'active' ORDER BY support_version DESC LIMIT 1", (activity_id, packet_key))

    # ------------------------------------------------------- the request

    def _request_support(self, tx: Any, row: Mapping[str, Any], packet: Mapping[str, Any], reason: str) -> str | None:
        """Save one support assignment for a packet (the same request replays to the saved one); return a rejection reason instead when it cannot start."""
        activity_id, key = row["activity_id"], packet["packet_key"]
        if packet["state"] != "pending":
            return f"the packet is {packet['state']}; support is requested for a packet that has not started"
        existing = self._row(tx, "SELECT * FROM service_execution_architect WHERE activity_id = ? AND kind = 'support' AND packet_key = ? ORDER BY created_at DESC, rowid DESC LIMIT 1", (activity_id, key))
        if existing is not None and existing["state"] not in ("blocked_route", "superseded", "declined"):
            return None if existing["state"] != "active" else "a specialist role is already active for this packet; start it"
        config = json.loads(row["config_json"]).get("architectural_support")
        number = 1 + int(self._row(tx, "SELECT COUNT(*) AS n FROM service_execution_architect WHERE activity_id = ? AND kind = 'support'", (activity_id,))["n"])
        support_id = f"support-{number}"
        now = _now()
        state, note = ("requested", reason[:300]) if config else ("blocked_route", "execution.architectural_support is not configured for this Execution, so no architect or reviewer route exists")
        tx.execute(
            "INSERT INTO service_execution_architect(activity_id, assignment_key, kind, packet_key, subject, trigger_json, state, version, config_json, pending_json, review_limit, note, created_at, updated_at) "
            "VALUES (?, ?, 'support', ?, ?, ?, ?, 1, ?, '{}', ?, ?, ?, ?)",
            (activity_id, support_id, key, f"Specialist support for {key}", canonical_json({"packet_key": key, "reason": reason[:1000]}), state,
             canonical_json(config or {}), int((config or {}).get("maximum_fidelity_reviews", 0)), note, now, now),
        )
        self._say(tx, row["project_id"], activity_id,
                  f"Architectural support {support_id} recorded for {key}: {reason[:300]}." + ("" if config else f" {note}. Unrelated work continues."))
        if not config:
            self._event(tx, activity_id, "support_blocked", key, f"{support_id}: {note}")
        return None

    # ---------------------------------------------------------- advancing

    def _advance_support(self, row: Mapping[str, Any]) -> None:
        for arch in self._architects(row["activity_id"], "support"):
            state = arch["state"]
            try:
                if state in ("requested", "drafting", "correcting"):
                    self._support_step(row, arch, "architect_run", self._support_start_architect, self._support_accept_architect)
                elif state == "reviewing":
                    self._support_step(row, arch, "reviewer_run", self._support_start_reviewer, self._support_accept_review)
                elif state == "recommending":
                    self._support_step(row, arch, "limit_run", self._support_start_limit, self._support_accept_limit)
                elif state == "publishing":
                    self._support_publish(row, arch)
            except (AgentRunError, DestinationError) as error:
                if isinstance(error, DestinationError) and (error.code == "github_unreachable" or (isinstance(error.fields.get("status"), int) and error.fields["status"] >= 500)):
                    continue
                self._support_block(row, arch, f"{getattr(error, 'code', type(error).__name__)}: {error}")

    def _support_block(self, row: Mapping[str, Any], arch: Mapping[str, Any], reason: str) -> None:
        with self.database.transaction() as tx:
            tx.execute("UPDATE service_execution_architect SET state = 'blocked_route', note = ?, updated_at = ? WHERE activity_id = ? AND assignment_key = ? AND state NOT IN ('active', 'blocked_route')",
                       (reason[:400], _now(), row["activity_id"], arch["assignment_key"]))
            self._event(tx, row["activity_id"], "support_blocked", arch["packet_key"], f"{arch['assignment_key']} stopped: {reason[:300]}")
            self._say(tx, row["project_id"], row["activity_id"], f"Architectural support {arch['assignment_key']} for {arch['packet_key']} is blocked: {reason[:400]}. The packet stays unstarted and unrelated work continues.")

    def _support_step(self, row: Mapping[str, Any], arch: dict[str, Any], slot: str, start: Callable[..., None], accept: Callable[..., None]) -> None:
        """Start the assignment's next run, or read the current one: complete, recover once per new cause, or block."""
        assert self.runs is not None
        pending = json.loads(arch["pending_json"] or "{}")
        current = pending.get(slot)
        if current is None:
            start(row, arch, None)
            return
        view = self.runs.poll(current["run_id"])
        if view.state in {"reserved", "running", "stopping"}:
            return
        assignment = self.runs.assignment_state(current["assignment_id"])
        if view.state == "completed":
            accept(row, arch, pending, current)
            return
        if assignment["state"] == "needs_recovery":
            detail = view.terminal_reason or view.failure_code or "technical_failure"
            if pending.get("last_recovery_detail") == detail:
                self._support_block(row, arch, f"the same error came back after a correction: {detail}")
                return
            pending["last_recovery_detail"] = detail
            pending.pop(slot, None)
            self._save_architect(row["activity_id"], arch["assignment_key"], pending)
            start(row, {**arch, "pending_json": canonical_json(pending)}, detail)
            return
        if view.state == "cancelled":
            return
        self._support_block(row, arch, f"the run {view.state}" + (f" ({view.failure_code})" if view.failure_code else "") + (f": {view.terminal_reason}" if view.terminal_reason else ""))

    def _reject_support_result(self, row: Mapping[str, Any], arch: Mapping[str, Any], pending: dict[str, Any], current: Mapping[str, str], slot: str, reason: str, start: Callable[..., None]) -> None:
        assert self.runs is not None
        self.runs.reject_result(current["run_id"], "conflicting_response", reason)
        pending.pop(slot, None)
        if self.runs.assignment_state(current["assignment_id"])["state"] != "needs_recovery":
            self._support_block(row, arch, reason)
            return
        pending["last_recovery_detail"] = reason
        self._save_architect(row["activity_id"], arch["assignment_key"], pending)
        start(row, {**arch, "pending_json": canonical_json(pending)}, reason)

    # -------------------------------------------------------------- routes

    def _support_route(self, arch: Mapping[str, Any], role: str, exclude: tuple[str, str] | None = None) -> dict[str, Any]:
        """The configured primary route, or the configured backup when the primary cannot be used before launch (recorded, never silent)."""
        config = json.loads(arch["config_json"])[role]
        pending = json.loads(arch["pending_json"] or "{}")
        history = pending.setdefault("route_history", [])
        problems: list[str] = []
        for slot in ("primary", "backup"):
            route = config[slot]
            if exclude is not None and (route["tool"], route["model"]) == exclude:
                problems.append(f"{slot} {route['tool']} {route['model']} authored the reviewed draft and cannot review it")
                continue
            resolver = getattr(self.runs, "route_resolver", None)
            if resolver is not None:
                try:
                    resolver("architect" if role == "architect" else "fidelity_reviewer", route["tool"], route["model"])
                except Exception as error:  # noqa: BLE001 - an unusable route is a fallback cause, not a crash
                    problems.append(f"{slot} {route['tool']} {route['model']} is unavailable: {error}"[:300])
                    continue
            if slot == "backup":
                history.append({"role": role, "switched_to": f"{route['tool']} {route['model']}", "reason": "; ".join(problems)})
                self._save_architect(arch["activity_id"], arch["assignment_key"], {**pending, "route_history": history})
            return {**route, "run_timeout_seconds": config["run_timeout_seconds"], "slot": slot}
        raise AgentRunError("no_usable_route", f"neither the primary nor the backup {role.replace('_', ' ')} route can be used: " + "; ".join(problems))

    # ----------------------------------------------------------- inputs

    def _support_packets(self, row: Mapping[str, Any], arch: Mapping[str, Any]) -> list[dict[str, Any]]:
        keys = json.loads(arch["trigger_json"])["packet_key"]
        pending = json.loads(arch["pending_json"] or "{}")
        keys = [keys, *[k for k in pending.get("extra_packets", []) if k != keys]]
        found = self._rows(f"SELECT * FROM service_execution_packets WHERE activity_id = ? AND packet_key IN ({','.join('?' for _ in keys)})", (row["activity_id"], *keys))
        return [{"key": p["packet_key"], "subject": p["subject"], "milestone": p["milestone_key"], **{k: v for k, v in json.loads(p["record_json"]).items() if k in {
            "purpose", "permitted_paths", "completion_criteria", "essential_failure_checks", "required_outputs", "shared_code_constraints", "execution_requirements"}}} for p in found]

    def _existing_roles(self, row: Mapping[str, Any]) -> list[dict[str, Any]]:
        destination = self._destination(self.profiles[json.loads(row["profile_json"])["profile"]])
        seen: dict[str, dict[str, Any]] = {}
        for packet in self._packets(row["activity_id"]):
            ref = (json.loads(packet["record_json"]).get("starting_context") or {}).get("specialist_role_ref")
            if isinstance(ref, Mapping) and ref["path"] not in seen:
                data = destination.read_file(row["repository"], ref["commit"], ref["path"])
                if data is not None and _sha(data) == ref["sha256"]:
                    seen[ref["path"]] = {"path": ref["path"], "sha256": ref["sha256"], "commit": ref["commit"], "text": data.decode("utf-8", "replace")[:6000]}
        for binding in self._rows("SELECT * FROM service_execution_support_bindings WHERE activity_id = ? AND state = 'active'", (row["activity_id"],)):
            if binding["role_path"] not in seen:
                data = destination.read_file(row["repository"], binding["commit_sha"], binding["role_path"])
                if data is not None and _sha(data) == binding["role_sha256"]:
                    seen[binding["role_path"]] = {"path": binding["role_path"], "sha256": binding["role_sha256"], "commit": binding["commit_sha"], "text": data.decode("utf-8", "replace")[:6000]}
        return sorted(seen.values(), key=lambda r: r["path"])

    def _support_common_inputs(self, row: Mapping[str, Any], arch: Mapping[str, Any]) -> dict[str, bytes]:
        milestones = self._load_milestones(row)
        return {
            "request.json": _json({"support_id": arch["assignment_key"], **json.loads(arch["trigger_json"])}),
            "packets.json": _json(self._support_packets(row, arch)),
            "existing-roles.json": _json(self._existing_roles(row)),
            "execution.json": _json({"activity_id": row["activity_id"], "source_commit": row["source_commit"], "repository": row["repository"],
                                     "milestones": {k: {"subject": m["subject"]} for k, m in milestones.items()}}),
        }

    # ---------------------------------------------------------- architect

    def _support_ident(self, arch: Mapping[str, Any], suffix: str) -> str:
        return f"{arch['activity_id']}-{arch['assignment_key']}-{suffix}"

    def _support_start_architect(self, row: Mapping[str, Any], arch: dict[str, Any], recovery_note: str | None) -> None:
        assert self.runs is not None
        activity_id, support_id = row["activity_id"], arch["assignment_key"]
        pending = json.loads(arch["pending_json"] or "{}")
        route = self._support_route(arch, "architect")
        pending = json.loads(self._architect(activity_id, support_id)["pending_json"])
        version = int(arch["version"])
        assignment_id = self._support_ident(arch, f"architect-v{version}")
        inputs = self._support_common_inputs(row, arch)
        correction = ""
        if arch["state"] == "correcting":
            draft = json.loads(arch["result_json"])
            inputs["prior-draft.json"] = _json(draft)
            findings = pending.get("findings", [])
            inputs["review-findings.json"] = _json({"findings": findings})
            correction = _SUPPORT_CORRECTION
        note = "" if not recovery_note else f"\nThe previous run's output was rejected: {recovery_note}. Fix exactly that."
        task = _SUPPORT_TASK.format(role_headings=", ".join(ROLE_HEADINGS), context_headings=", ".join(CONTEXT_HEADINGS), correction=correction) + note
        mirror = self._mirror(row["project_id"])

        def build(run_id: str) -> RunBuild:
            assignment = AgentAssignment(
                project_id=row["project_id"], activity_id=activity_id, assignment_id=assignment_id, run_id=run_id, parent_assignment_id=None, role="support_architect",
                role_responsibilities=("Decide whether an existing role covers the packet or draft one in-scope role; never change scope or dispatch code.",),
                task=task, source_commit=row["source_commit"], decision_version=f"s{support_id}v{version}",
                instructions={"session_id": run_id, "claude_tools": _ARCHITECT_TOOLS, "task_kind": "architectural_support", "support": support_id},
                permitted_actions=("read_source",), writable_locations=("output", "scratch"), limits={"run_timeout_seconds": route["run_timeout_seconds"]},
                clarification_conditions=("Missing information changes whether an existing role covers the packet.",), response_schema=SUPPORT_ARCHITECT_SCHEMA, contract="execution",
            )
            return RunBuild(assignment, mirror, inputs, None)

        self._launch(row, pending, "architect_run", assignment_id, route["tool"], route["model"], route["run_timeout_seconds"], recovery_note is not None, build, "support_architect",
                     save=lambda _a, p: self._save_architect(activity_id, support_id, p))
        pending["architect"] = {"tool": route["tool"], "model": route["model"]}
        with self.database.transaction() as tx:
            tx.execute("UPDATE service_execution_architect SET state = ?, pending_json = ?, updated_at = ? WHERE activity_id = ? AND assignment_key = ?",
                       ("correcting" if arch["state"] == "correcting" else "drafting", canonical_json(pending), _now(), activity_id, support_id))
            self._say(tx, row["project_id"], activity_id,
                      f"Architectural support {support_id} for {arch['packet_key']}: architect {route['tool']} {route['model']} ({route['slot']} route) started on draft version {version}.")

    def _support_accept_architect(self, row: Mapping[str, Any], arch: dict[str, Any], pending: dict[str, Any], current: Mapping[str, str]) -> None:
        assert self.runs is not None
        activity_id, support_id = row["activity_id"], arch["assignment_key"]
        response = self.runs.response(current["run_id"]) or {}
        if response.get("result") != "completed":
            self._support_block(row, arch, "the support architect asked a question; the Development Manager's request needs more information than this assignment can ask for")
            return
        try:
            draft = self._validate_support_draft(row, arch, response)
        except ValueError as error:
            self._reject_support_result(row, arch, pending, current, "architect_run", str(error), self._support_start_architect)
            return
        pending.pop("architect_run", None)
        pending.pop("last_recovery_detail", None)
        disposition = draft["disposition"]
        if disposition == "replanning_required":
            with self.database.transaction() as tx:
                tx.execute("UPDATE service_execution_architect SET state = 'replanning_required', result_json = ?, pending_json = ?, note = ?, updated_at = ? WHERE activity_id = ? AND assignment_key = ?",
                           (canonical_json(draft), canonical_json(pending), draft["rationale"][:400], _now(), activity_id, support_id))
                self._event(tx, activity_id, "support_replanning", arch["packet_key"], f"{support_id}: {draft['rationale'][:300]}")
                self._say(tx, row["project_id"], activity_id,
                          f"Architectural support {support_id}: covering {arch['packet_key']} would change scope or the confirmed breakdown ({draft['rationale'][:300]}). The packet stays blocked; the Owner chooses the work disposition before re-registration.")
            return
        # a use_existing result needs applicability validation only; a new role needs the independent fidelity review
        next_state = "publishing" if disposition == "use_existing" else "reviewing"
        with self.database.transaction() as tx:
            tx.execute("UPDATE service_execution_architect SET state = ?, result_json = ?, pending_json = ?, note = NULL, updated_at = ? WHERE activity_id = ? AND assignment_key = ?",
                       (next_state, canonical_json(draft), canonical_json(pending), _now(), activity_id, support_id))
            self._say(tx, row["project_id"], activity_id,
                      f"Architectural support {support_id} draft version {arch['version']}: " + (
                          f"existing role {draft['existing_role_path']} covers {', '.join(draft['packet_keys'])}; its applicability is validated and the binding is published next."
                          if disposition == "use_existing" else f"new role '{draft['role_title']}' for {draft['source_area']}; independent fidelity review is next."))

    def _validate_support_draft(self, row: Mapping[str, Any], arch: Mapping[str, Any], response: Mapping[str, Any]) -> dict[str, Any]:
        """Deterministic checks on the architect's draft; a message names exactly what to fix."""
        packets = {p["key"]: p for p in self._support_packets(row, arch)}
        requested = json.loads(arch["trigger_json"])["packet_key"]
        keys = list(response["packet_keys"])
        known = {p["packet_key"]: p for p in self._packets(row["activity_id"])}
        if requested not in keys:
            raise ValueError(f"packet_keys must include the requested packet {requested}")
        for key in keys:
            if key not in known:
                raise ValueError(f"packet_keys names {key}, which is not a packet of this Execution")
            if known[key]["state"] != "pending":
                raise ValueError(f"packet {key} is {known[key]['state']}; a role cannot be bound to work that already started")
        draft: dict[str, Any] = {"disposition": response["disposition"], "rationale": str(response["rationale"]).strip()[:2000], "packet_keys": sorted(set(keys))}
        if response["disposition"] == "replanning_required":
            return {**draft, "existing_role_path": None, "source_area": None, "role_title": None}
        destination = self._destination(self.profiles[json.loads(row["profile_json"])["profile"]])
        if response["disposition"] == "use_existing":
            roles = {r["path"]: r for r in self._existing_roles(row)}
            path = response["existing_role_path"]
            if path not in roles:
                raise ValueError(f"existing_role_path {path} is not a role the confirmed breakdown provides; choose one from input/existing-roles.json")
            role = roles[path]
            context_path = path.rsplit("/", 1)[0] + "/context.md"
            context = destination.read_file(row["repository"], role["commit"], context_path)
            paths_by_packet = {k: packets[k]["permitted_paths"] for k in keys if k in packets}
            area = path.rsplit("/.maestro/", 1)[0]
            for key, permitted in paths_by_packet.items():
                if not any(p == area or p.startswith(area.rstrip("/") + "/") or area == "." for p in permitted):
                    raise ValueError(f"the role {path} belongs to {area}, which does not contain packet {key}'s permitted paths")
            return {**draft, "existing_role_path": path, "existing_role_sha256": role["sha256"], "existing_role_commit": role["commit"],
                    "existing_context_path": context_path if context is not None else None, "existing_context_sha256": None if context is None else _sha(context),
                    "source_area": None, "role_title": None}
        area = str(response["source_area"]).strip().strip("/")
        title = str(response["role_title"]).strip()
        if not _AREA.match(area) or not kebab(title):
            raise ValueError("source_area must be a repository-relative directory and role_title a plain title")
        for key in keys:
            permitted = known[key]["record_json"] and json.loads(known[key]["record_json"]).get("permitted_paths", [])
            if not any(p.strip("/") == area or p.strip("/").startswith(area + "/") for p in permitted):
                raise ValueError(f"source_area {area} does not contain packet {key}'s permitted paths ({', '.join(permitted)}); the role must stay inside the packet's source area")
        role_text, context_text = str(response["role_markdown"]), str(response["context_markdown"])
        first = role_text.lstrip().splitlines()[0] if role_text.strip() else ""
        if not first.startswith("#") or title.lower() not in first.lower():
            raise ValueError(f"role_markdown must begin with the role title '{title}' as its first heading")
        for name, text, needed in (("role_markdown", role_text, ROLE_HEADINGS), ("context_markdown", context_text, CONTEXT_HEADINGS)):
            present = [h.lower() for h in _headings(text)]
            missing = [h for h in needed if h.lower() not in present]
            if missing:
                raise ValueError(f"{name} lacks the required heading(s): {', '.join(missing)}")
        role_path = f"{area}/.maestro/role-{kebab(title)}.md"
        context_path = f"{area}/.maestro/context.md"
        head = destination.head(row["repository"], self._publication_branch(row))
        for path, text in ((role_path, role_text), (context_path, context_text)):
            found = destination.read_file(row["repository"], head, path)
            if found is not None and found != text.encode("utf-8"):
                raise ValueError(f"{path} already exists with different content; a support role cannot replace or move existing role authority: choose another source_area or use the existing role")
        others = [r for r in self._existing_roles(row) if r["path"].startswith(f"{area}/.maestro/role-") and r["path"] != role_path]
        if others:
            raise ValueError(f"the area {area} already has the role {others[0]['path']}; use it or choose another area")
        return {**draft, "existing_role_path": None, "source_area": area, "role_title": title, "role_markdown": role_text, "context_markdown": context_text,
                "role_path": role_path, "context_path": context_path}

    def _publication_branch(self, row: Mapping[str, Any]) -> str:
        found = self._read("SELECT publication_branch FROM service_registrations WHERE activity_id = ?", (row["registration_activity_id"],))
        assert found is not None
        return str(found["publication_branch"])

    # ------------------------------------------------------------ review

    def _inventory(self, draft: Mapping[str, Any]) -> dict[str, Any]:
        return {"role": {"path": draft["role_path"], "sha256": _sha(draft["role_markdown"].encode("utf-8"))},
                "context": {"path": draft["context_path"], "sha256": _sha(draft["context_markdown"].encode("utf-8"))}}

    def _reviewed_range(self, arch: Mapping[str, Any], draft: Mapping[str, Any]) -> dict[str, str]:
        return {"base": f"{arch['assignment_key']}@v{arch['version']}", "head": _sha(_dump(self._inventory(draft)).encode())}

    def _support_start_reviewer(self, row: Mapping[str, Any], arch: dict[str, Any], recovery_note: str | None) -> None:
        assert self.runs is not None
        activity_id, support_id = row["activity_id"], arch["assignment_key"]
        pending = json.loads(arch["pending_json"] or "{}")
        author = pending["architect"]
        reviewer = self._support_route(arch, "fidelity_reviewer", exclude=(author["tool"], author["model"]))
        pending = json.loads(self._architect(activity_id, support_id)["pending_json"])
        draft = json.loads(arch["result_json"])
        round_number = int(arch["reviews_used"]) + 1
        assignment_id = self._support_ident(arch, f"review-{round_number}")
        span = self._reviewed_range(arch, draft)
        inputs = self._support_common_inputs(row, arch)
        inputs.update({
            "draft.json": _json({k: draft[k] for k in ("disposition", "rationale", "source_area", "role_title", "packet_keys", "role_path", "context_path")}),
            "role.md": draft["role_markdown"].encode("utf-8"), "context.md": draft["context_markdown"].encode("utf-8"),
            "inventory.json": _json(self._inventory(draft)), "reviewed-range.json": _json(span),
        })
        prior = self._rows("SELECT findings_json FROM service_execution_support_reviews WHERE activity_id = ? AND support_id = ? ORDER BY review_round", (activity_id, support_id))
        if prior:
            inputs["prior-findings.json"] = _json({"findings": json.loads(prior[-1]["findings_json"])})
        later = ", input/prior-findings.json (your earlier findings; recheck them and what the amendment changed; do not reopen unchanged content over preference)" if prior else ""
        note = "" if not recovery_note else f"\nThe previous run's output was rejected: {recovery_note}. Fix exactly that."
        task = _SUPPORT_REVIEW_TASK.format(later=later) + note
        mirror = self._mirror(row["project_id"])

        def build(run_id: str) -> RunBuild:
            assignment = AgentAssignment(
                project_id=row["project_id"], activity_id=activity_id, assignment_id=assignment_id, run_id=run_id, parent_assignment_id=None, role="support_reviewer",
                role_responsibilities=("Decide whether the drafted role and starting context are faithful and fit the packets; never edit or approve activation.",),
                task=task, source_commit=row["source_commit"], decision_version=f"s{support_id}r{round_number}",
                instructions={"session_id": run_id, "claude_tools": ["Read", "Glob", "Grep"], "task_kind": "review_support", "support": support_id},
                permitted_actions=("read_source",), writable_locations=("output", "scratch"), limits={"run_timeout_seconds": reviewer["run_timeout_seconds"]},
                clarification_conditions=("The draft cannot be verified.",), response_schema=REVIEWER_SCHEMA, contract="execution",
            )
            return RunBuild(assignment, mirror, inputs, None)

        self._launch(row, pending, "reviewer_run", assignment_id, reviewer["tool"], reviewer["model"], reviewer["run_timeout_seconds"], recovery_note is not None, build, "support_reviewer",
                     save=lambda _a, p: self._save_architect(activity_id, support_id, p))
        pending["reviewer"] = {"tool": reviewer["tool"], "model": reviewer["model"]}
        self._save_architect(activity_id, support_id, pending)
        with self.database.transaction() as tx:
            self._say(tx, row["project_id"], activity_id,
                      f"Support fidelity review round {round_number} of {int(arch['review_limit']) + len(pending.get('grants', []))} for {support_id}: reviewer {reviewer['tool']} {reviewer['model']} "
                      f"(architect {author['tool']} {author['model']}), draft version {arch['version']}.")

    def _support_accept_review(self, row: Mapping[str, Any], arch: dict[str, Any], pending: dict[str, Any], current: Mapping[str, str]) -> None:
        assert self.runs is not None
        activity_id, support_id = row["activity_id"], arch["assignment_key"]
        response = self.runs.response(current["run_id"]) or {}
        draft = json.loads(arch["result_json"])
        expected = self._reviewed_range(arch, draft)
        if response.get("result") != "completed" or response.get("reviewed_range") != expected:
            self._reject_support_result(row, arch, pending, current, "reviewer_run", "the review must copy reviewed_range exactly from input/reviewed-range.json", self._support_start_reviewer)
            return
        round_number = int(arch["reviews_used"]) + 1
        findings = [{**f, "finding_id": f"{activity_id}-{support_id}-r{round_number}-{f['local_key']}"} for f in response.get("findings", [])]
        blocking = [f for f in findings if f["severity"] == "blocking"]
        reviewer, author = pending["reviewer"], pending["architect"]
        limit = int(arch["review_limit"]) + len(pending.get("grants", []))
        outcome = response["review_outcome"]
        with self.database.transaction() as tx:
            tx.execute(
                "INSERT INTO service_execution_support_reviews(activity_id, support_id, support_version, review_round, assignment_id, run_id, reviewer_tool, reviewer_model, author_tool, author_model, inventory_sha256, outcome, summary, findings_json, independence, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (activity_id, support_id, arch["version"], round_number, current["assignment_id"], current["run_id"], reviewer["tool"], reviewer["model"], author["tool"], author["model"],
                 expected["head"], outcome, str(response["summary"])[:2000], _dump(findings), str(response.get("independence", ""))[:500], _now()),
            )
            pending.pop("reviewer_run", None)
            pending.pop("last_recovery_detail", None)
            if outcome == "APPROVE":
                tx.execute("UPDATE service_execution_architect SET state = 'publishing', reviews_used = ?, pending_json = ?, note = NULL, updated_at = ? WHERE activity_id = ? AND assignment_key = ?",
                           (round_number, canonical_json(pending), _now(), activity_id, support_id))
                self._say(tx, row["project_id"], activity_id, f"Support fidelity review round {round_number} of {limit} for {support_id}: APPROVED by {reviewer['tool']} {reviewer['model']}. {str(response['summary'])[:300]} Publication and binding are next.")
            elif round_number < limit:
                pending["findings"] = blocking
                tx.execute("UPDATE service_execution_architect SET state = 'correcting', version = version + 1, reviews_used = ?, pending_json = ?, updated_at = ? WHERE activity_id = ? AND assignment_key = ?",
                           (round_number, canonical_json(pending), _now(), activity_id, support_id))
                self._say(tx, row["project_id"], activity_id, f"Support fidelity review round {round_number} of {limit} for {support_id}: changes requested ({len(blocking)} blocking): " + "; ".join(f['subject'] for f in blocking)[:400] + ". The architect amends the draft.")
            else:
                pending["findings"] = blocking
                tx.execute("UPDATE service_execution_architect SET state = 'recommending', reviews_used = ?, pending_json = ?, note = ?, updated_at = ? WHERE activity_id = ? AND assignment_key = ?",
                           (round_number, canonical_json(pending), f"fidelity review limit reached with {len(blocking)} blocking finding(s)", _now(), activity_id, support_id))
                self._say(tx, row["project_id"], activity_id, f"Support fidelity review round {round_number} of {limit} for {support_id}: blocking findings remain at the limit. The architect gives the Owner a recommendation; the packet stays blocked and unrelated work continues.")

    # ------------------------------------------------------ limit and owner

    def _support_start_limit(self, row: Mapping[str, Any], arch: dict[str, Any], recovery_note: str | None) -> None:
        assert self.runs is not None
        activity_id, support_id = row["activity_id"], arch["assignment_key"]
        route = self._support_route(arch, "architect")
        pending = json.loads(self._architect(activity_id, support_id)["pending_json"])
        draft = json.loads(arch["result_json"])
        assignment_id = self._support_ident(arch, f"limit-{int(arch['reviews_used'])}")
        snapshot = {"support_id": support_id, "support_version": int(arch["version"]), "completed_reviews": int(arch["reviews_used"]),
                    "review_limit": int(arch["review_limit"]), "grants": pending.get("grants", []), "inventory": self._inventory(draft)}
        inputs = {"support.json": _json(snapshot), "review-findings.json": _json({"findings": pending.get("findings", [])}),
                  "draft.json": _json({k: draft[k] for k in ("disposition", "rationale", "source_area", "role_title", "packet_keys", "role_path", "context_path")})}
        note = "" if not recovery_note else f"\nThe previous run's output was rejected: {recovery_note}. Fix exactly that."
        mirror = self._mirror(row["project_id"])

        def build(run_id: str) -> RunBuild:
            assignment = AgentAssignment(
                project_id=row["project_id"], activity_id=activity_id, assignment_id=assignment_id, run_id=run_id, parent_assignment_id=None, role="support_limit_architect",
                role_responsibilities=("Recommend grant_one or remain_paused for the Owner; grant nothing.",),
                task=_SUPPORT_LIMIT_TASK + note, source_commit=row["source_commit"], decision_version=f"s{support_id}l{int(arch['reviews_used'])}",
                instructions={"session_id": run_id, "claude_tools": ["Read"], "task_kind": "support_limit_recommendation", "support": support_id},
                permitted_actions=("read_source",), writable_locations=("output", "scratch"), limits={"run_timeout_seconds": route["run_timeout_seconds"]},
                clarification_conditions=("The findings cannot be understood.",), response_schema=SUPPORT_LIMIT_SCHEMA, contract="execution",
            )
            return RunBuild(assignment, mirror, inputs, None)

        self._launch(row, pending, "limit_run", assignment_id, route["tool"], route["model"], route["run_timeout_seconds"], recovery_note is not None, build, "support_limit_architect",
                     save=lambda _a, p: self._save_architect(activity_id, support_id, p))
        self._save_architect(activity_id, support_id, pending)

    def _support_accept_limit(self, row: Mapping[str, Any], arch: dict[str, Any], pending: dict[str, Any], current: Mapping[str, str]) -> None:
        assert self.runs is not None
        activity_id, support_id = row["activity_id"], arch["assignment_key"]
        response = self.runs.response(current["run_id"]) or {}
        expected = {"support_id": support_id, "support_version": int(arch["version"]), "completed_reviews": int(arch["reviews_used"])}
        if response.get("result") != "completed" or {k: response.get(k) for k in expected} != expected:
            self._reject_support_result(row, arch, pending, current, "limit_run", "support_id, support_version and completed_reviews must be copied exactly from input/support.json", self._support_start_limit)
            return
        pending.pop("limit_run", None)
        pending.pop("last_recovery_detail", None)
        pending["limit"] = {"assignment_id": support_id, "version": int(arch["version"]), "round": int(arch["reviews_used"]),
                            "recommendation": response["recommendation"], "rationale": str(response["rationale"])[:1000], "run_id": current["run_id"]}
        with self.database.transaction() as tx:
            tx.execute("UPDATE service_execution_architect SET state = 'limit_paused', pending_json = ?, note = ?, updated_at = ? WHERE activity_id = ? AND assignment_key = ?",
                       (canonical_json(pending), f"waiting for the Owner: architect recommends {response['recommendation']}", _now(), activity_id, support_id))
            self._event(tx, activity_id, "limit_reached", arch["packet_key"], f"{support_id} reached its support review limit; the architect recommends {response['recommendation']}")
            self._say(tx, row["project_id"], activity_id,
                      f"Support {support_id} for {arch['packet_key']} is at its fidelity review limit with blocking findings. Architect recommendation: {response['recommendation']} - {str(response['rationale'])[:400]}. Grant one more review or keep it paused.")

    def _support_decision(self, tx: Any, request: Any, row: Mapping[str, Any], payload: Mapping[str, Any], next_version: int) -> Any:
        from .registry import OperationResult
        from .requests import RequestRejection

        activity_id = row["activity_id"]
        arch = self._row(tx, "SELECT * FROM service_execution_architect WHERE activity_id = ? AND assignment_key = ? AND kind = 'support' AND state = 'limit_paused'", (activity_id, payload["assignment_id"]))
        if arch is None:
            raise RequestRejection(409, "no_decision_pending", "no support review-limit decision is pending for that support assignment")
        pending = json.loads(arch["pending_json"])
        limit = pending.get("limit")
        if not limit or limit.get("recommendation") not in ("grant_one", "remain_paused"):
            raise RequestRejection(409, "recommendation_pending", "the architect's recommendation is not saved yet")
        if any(g.get("version") == arch["version"] and g.get("round") == arch["reviews_used"] for g in pending.get("grants", [])) and payload["choice"] == "grant_one":
            raise RequestRejection(409, "already_granted", "this review allowance was already granted")
        grants = list(pending.get("grants", []))
        if payload["choice"] == "remain_paused":
            text = f"Owner chose to keep support {arch['assignment_key']} paused at {arch['reviews_used']} of {int(arch['review_limit']) + len(grants)} fidelity reviews. Nothing was activated and no count changed."
        else:
            grants.append({"request_id": request.request_id, "version": arch["version"], "round": arch["reviews_used"], "granted_at": _now()})
            pending["grants"] = grants
            pending.pop("limit", None)
            tx.execute("UPDATE service_execution_architect SET state = 'correcting', version = version + 1, pending_json = ?, note = 'one extra fidelity review granted', updated_at = ? WHERE activity_id = ? AND assignment_key = ?",
                       (canonical_json(pending), _now(), activity_id, arch["assignment_key"]))
            text = (f"Owner granted one extra fidelity review for support {arch['assignment_key']} (limit now {int(arch['review_limit']) + len(grants)}); the base limit of {arch['review_limit']} is unchanged, "
                    "and the grant activates nothing and approves no content.")
        self._activity(tx, activity_id, "running", text, version=next_version)
        self._say(tx, row["project_id"], activity_id, text)
        return OperationResult(data={"activity_id": activity_id, "decision": payload["choice"], "support": arch["assignment_key"], "message": text}, status="accepted", project_id=row["project_id"], activity_id=activity_id)

    # ---------------------------------------------------------- publication

    def _support_files(self, row: Mapping[str, Any], arch: Mapping[str, Any], draft: Mapping[str, Any]) -> tuple[dict[str, bytes], dict[str, Any]]:
        activity_id, support_id, version = row["activity_id"], arch["assignment_key"], int(arch["version"])
        base = f".maestro/execution/{activity_id}/architectural-support/{support_id}/versions/{version}"
        common = {"schema_version": 1, "project_id": row["project_id"], "activity_id": activity_id, "support_id": support_id, "version": version}
        confirmed = json.loads(row["confirmed_ref_json"])
        confirmed_ref = {k: confirmed[k] for k in ("version", "commit", "manifest_path", "manifest_sha256") if k in confirmed}
        pending = json.loads(arch["pending_json"] or "{}")
        files: dict[str, bytes] = {}
        support = {**common, "confirmed_breakdown": confirmed_ref, "affected_packets": draft["packet_keys"], "source_commit": row["source_commit"],
                   "assignment": self._support_ident(arch, f"architect-v{version}"), "configuration_sha256": _sha(arch["config_json"].encode()),
                   "routes": {"architect": pending.get("architect"), "reviewer": pending.get("reviewer"), "switches": pending.get("route_history", [])},
                   "disposition": draft["disposition"], "rationale": draft["rationale"]}
        binding_role: dict[str, Any]
        if draft["disposition"] == "create_role":
            role_bytes, context_bytes = draft["role_markdown"].encode("utf-8"), draft["context_markdown"].encode("utf-8")
            files[draft["role_path"]] = role_bytes
            files[draft["context_path"]] = context_bytes
            support["inventory"] = {"role": {"path": draft["role_path"], "sha256": _sha(role_bytes)}, "context": {"path": draft["context_path"], "sha256": _sha(context_bytes)}}
            binding_role = {"role_path": draft["role_path"], "role_sha256": _sha(role_bytes), "context_path": draft["context_path"], "context_sha256": _sha(context_bytes)}
            review = self._read("SELECT * FROM service_execution_support_reviews WHERE activity_id = ? AND support_id = ? AND outcome = 'APPROVE' ORDER BY review_round DESC LIMIT 1", (activity_id, support_id))
            assert review is not None
            files[f"{base}/review.json"] = encode({**common, "reviewed_inventory": support["inventory"], "reviewed_range": self._reviewed_range(arch, draft), "reviewer_assignment": review["assignment_id"], "reviewer_run": review["run_id"],
                                                   "reviewer": {"tool": review["reviewer_tool"], "model": review["reviewer_model"]}, "independence": review["independence"], "outcome": "APPROVE",
                                                   "findings": json.loads(review["findings_json"]), "completed_reviews": int(arch["reviews_used"]), "review_limit": int(arch["review_limit"]) + len(pending.get("grants", []))})
            evidence: dict[str, Any] = {"review": {"path": f"{base}/review.json", "round": review["review_round"]}}
        else:
            binding_role = {"role_path": draft["existing_role_path"], "role_sha256": draft["existing_role_sha256"], "context_path": draft.get("existing_context_path"), "context_sha256": draft.get("existing_context_sha256")}
            support["inventory"] = {"role": {"path": binding_role["role_path"], "sha256": binding_role["role_sha256"]}}
            evidence = {"validation": {"existing_role_unchanged": True, "commit": draft["existing_role_commit"], "applicable_to": draft["packet_keys"]}}
        files[f"{base}/support.json"] = encode(support)
        files[f"{base}/activation.json"] = encode({**common, "support_record": {"path": f"{base}/support.json", "sha256": _sha(files[f"{base}/support.json"])}, "confirmed_breakdown": confirmed_ref,
                                                   "bindings": [{"packet_key": k, **binding_role} for k in draft["packet_keys"]], **evidence,
                                                   "operation_id": f"{activity_id}-{support_id}-v{version}-publish"})
        return files, {"role": binding_role, "base": base}

    def _support_publish(self, row: Mapping[str, Any], arch: dict[str, Any]) -> None:
        activity_id, support_id = row["activity_id"], arch["assignment_key"]
        draft = json.loads(arch["result_json"])
        files, meta = self._support_files(row, arch, draft)
        destination = self._destination(self.profiles[json.loads(row["profile_json"])["profile"]])
        branch = self._publication_branch(row)
        operation_id = f"{activity_id}-{support_id}-v{arch['version']}-publish"
        digest = _sha(_dump({p: _sha(d) for p, d in sorted(files.items())}).encode())
        if self._read("SELECT 1 AS n FROM service_execution_journal WHERE operation_id = ?", (operation_id,)) is None:
            self._journal_begin(row, operation_id, support_id, "support_publish", branch, digest, destination.head(row["repository"], branch))
        try:
            commit = destination.publish(row["repository"], branch, files, f"Execution {activity_id}: architectural support {support_id} version {arch['version']}")
        except DestinationError as error:
            if error.code in {"github_unreachable", "publication_failed", "branch_unverifiable"}:
                raise
            self._journal_end(operation_id, "failed", None, f"{error.code}: {error}"[:300])
            raise
        destination.verify_files(row["repository"], commit, files)
        role = meta["role"]
        activation = json.loads(files[f"{meta['base']}/activation.json"])
        with self.database.transaction() as tx:
            tx.execute("UPDATE service_execution_journal SET state = 'verified', remote_after = ? WHERE operation_id = ?", (commit, operation_id))
            for key in draft["packet_keys"]:
                tx.execute(
                    "INSERT OR IGNORE INTO service_execution_support_bindings(activity_id, support_id, support_version, packet_key, role_path, role_sha256, context_path, context_sha256, commit_sha, state, activation_json, created_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?)",
                    (activity_id, support_id, arch["version"], key, role["role_path"], role["role_sha256"], role["context_path"], role["context_sha256"], commit, canonical_json(activation), _now()),
                )
            tx.execute("UPDATE service_execution_architect SET state = 'active', note = NULL, updated_at = ? WHERE activity_id = ? AND assignment_key = ? AND state = 'publishing'", (_now(), activity_id, support_id))
            self._event(tx, activity_id, "support_ready", arch["packet_key"], f"{support_id}: role {role['role_path']} is active for {', '.join(draft['packet_keys'])}; reconsider the packet")
            self._say(tx, row["project_id"], activity_id,
                      f"Architectural support {support_id} is active: {role['role_path']} ({role['role_sha256'][:12]}) published in {commit[:12]} with the exact bytes verified on the remote. "
                      f"It is bound to {', '.join(draft['packet_keys'])} and the Development Manager is told to reconsider them; the confirmed breakdown is unchanged.")
            self._emit(tx, row["project_id"], activity_id, "execution.support_active", {"support": support_id, "packets": draft["packet_keys"], "commit": commit})

    # --------------------------------------------------------------- view

    def support_view(self, activity_id: str) -> list[dict[str, Any]]:
        views = []
        for arch in self._architects(activity_id, "support"):
            pending = json.loads(arch["pending_json"] or "{}")
            result = json.loads(arch["result_json"]) if arch["result_json"] else None
            reviews = self._rows("SELECT support_version, review_round, outcome, reviewer_tool, reviewer_model, summary, findings_json FROM service_execution_support_reviews WHERE activity_id = ? AND support_id = ? ORDER BY review_round", (activity_id, arch["assignment_key"]))
            views.append({
                "support_id": arch["assignment_key"], "packet_key": arch["packet_key"], "state": arch["state"], "version": arch["version"], "note": arch["note"],
                "reason": json.loads(arch["trigger_json"]).get("reason"),
                "disposition": None if result is None else result.get("disposition"), "role_path": None if result is None else result.get("role_path") or result.get("existing_role_path"),
                "reviews": {"completed": arch["reviews_used"], "limit": int(arch["review_limit"]) + len(pending.get("grants", []))},
                "review_results": [{"round": r["review_round"], "version": r["support_version"], "outcome": r["outcome"], "reviewer": f"{r['reviewer_tool']} {r['reviewer_model']}", "summary": r["summary"],
                                    "blocking": sum(1 for f in json.loads(r["findings_json"]) if f["severity"] == "blocking")} for r in reviews],
                "recommendation": (pending.get("limit") or {}).get("recommendation"), "recommendation_rationale": (pending.get("limit") or {}).get("rationale"),
                "routes": {"architect": pending.get("architect"), "reviewer": pending.get("reviewer"), "switches": pending.get("route_history", [])},
            })
        return views
