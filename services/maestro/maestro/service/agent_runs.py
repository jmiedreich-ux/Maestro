"""Service-owned agent runs: SQL records around the supervised tool process.

An assignment names one role, tool and exact model. Each launch is a run under
it. A run is reserved in one transaction before its supervisor unit exists, so
simultaneous dispatchers cannot start the same assignment twice. Supervisor
events are copied to SQL by sequence number before anything displays them, a
result counts only after registration-contract validation against the
assignment's *current* run, and a run whose stop or identity is unknown blocks
replacement.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import threading
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Mapping

from maestro.agents.claude_transport import ClaudeTransport
from maestro.agents.codex_transport import CodexTransport
from maestro.agents.preflight import ResolvedAgentRoute
from maestro.agents.recovery import RecoveryReconciler
from maestro.agents.supervisor import (
    AgentSupervisor,
    LaunchRequest,
    OperationIdentity,
    SupervisionError,
)
from maestro.agents.transport import (
    AgentAssignment,
    ArtifactReference,
    DecodedToolResult,
    RegistrationResponseValidator,
    TransportError,
)
from maestro.agents.workspaces import PreparedWorkspace, ServiceProfileBinding, WorkspacePaths, WorkspaceManager
from maestro.foundation import Database, DomainMigration, Transaction, canonical_identifier, canonical_json


AGENT_RUN_MIGRATION = DomainMigration(
    domain="service_agent_runs",
    version=1,
    identity="service-agent-runs-v1",
    statements=(
        """
        CREATE TABLE service_agent_assignments(
            assignment_id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            activity_id TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('architect', 'fidelity_reviewer')),
            tool TEXT NOT NULL,
            model_id TEXT NOT NULL,
            duration_seconds INTEGER NOT NULL CHECK(duration_seconds > 0),
            automatic_limit INTEGER NOT NULL CHECK(automatic_limit >= 0),
            automatic_used INTEGER NOT NULL DEFAULT 0,
            manual_used INTEGER NOT NULL DEFAULT 0,
            state TEXT NOT NULL,
            pause_reason TEXT,
            current_run_id TEXT,
            next_duration_seconds INTEGER
        )
        """,
        """
        CREATE TABLE service_agent_runs(
            run_id TEXT PRIMARY KEY,
            assignment_id TEXT NOT NULL
                REFERENCES service_agent_assignments(assignment_id) ON DELETE RESTRICT,
            kind TEXT NOT NULL CHECK(kind IN ('initial', 'recovery', 'manual')),
            state TEXT NOT NULL,
            duration_seconds INTEGER NOT NULL,
            reserved_at TEXT NOT NULL,
            ended_at TEXT,
            unit_name TEXT,
            invocation_id TEXT,
            tool_version TEXT,
            model_id TEXT,
            configuration_hash TEXT,
            session_id TEXT,
            failure_code TEXT,
            terminal_reason TEXT,
            active_seconds REAL,
            response_sha256 TEXT,
            response_json TEXT,
            assignment_sha256 TEXT,
            source_commit TEXT,
            decision_version TEXT,
            assignment_json TEXT,
            workspace_json TEXT,
            inputs_json TEXT
        )
        """,
        """
        CREATE TABLE service_agent_run_events(
            run_id TEXT NOT NULL REFERENCES service_agent_runs(run_id) ON DELETE RESTRICT,
            sequence INTEGER NOT NULL,
            kind TEXT NOT NULL,
            detail TEXT NOT NULL,
            PRIMARY KEY(run_id, sequence)
        )
        """,
        """
        CREATE TABLE service_agent_artifacts(
            run_id TEXT NOT NULL REFERENCES service_agent_runs(run_id) ON DELETE RESTRICT,
            field TEXT NOT NULL,
            path TEXT NOT NULL,
            sha256 TEXT NOT NULL,
            stored_path TEXT NOT NULL,
            PRIMARY KEY(run_id, field)
        )
        """,
    ),
)

_OPEN_RUN_STATES = ("reserved", "running", "stopping", "blocked")
_KINDS = frozenset({"initial", "recovery", "manual"})
# Failures that a fresh run can plausibly fix. Anything else needs intervention.
_RETRYABLE = frozenset(
    {
        "malformed_response", "malformed_output", "missing_output", "tool_failure",
        "conflicting_response", "artifact_mismatch", "artifact_missing", "protocol_error",
        "stalled", "interrupted", "process_exited", "technical_failure",
    }
)
_POST_RESULT_GRACE_SECONDS = 30.0
_DETAIL_LIMIT = 2000


class AgentRunError(ValueError):
    def __init__(self, code: str, message: str, **fields: object) -> None:
        super().__init__(message)
        self.code = code
        self.fields = dict(fields)


@dataclass(frozen=True)
class RunBuild:
    """What the process supplies for one run: its assignment, source and immutable inputs."""

    assignment: AgentAssignment
    source_repository: Path
    inputs: Mapping[str, bytes]


@dataclass(frozen=True)
class RunView:
    run_id: str
    assignment_id: str
    kind: str
    state: str
    failure_code: str | None
    terminal_reason: str | None
    duration_seconds: int
    response_sha256: str | None


Builder = Callable[[str], RunBuild]


class AgentRunService:
    def __init__(
        self,
        database: Database,
        supervisor: AgentSupervisor,
        workspaces: WorkspaceManager,
        *,
        route_resolver: Callable[[str, str, str], ResolvedAgentRoute],
        profile_resolver: Callable[[ResolvedAgentRoute], ServiceProfileBinding],
        artifact_root: Path,
        clock: Callable[[], float],
    ) -> None:
        self.database = database
        self.supervisor = supervisor
        self.workspaces = workspaces
        self.route_resolver = route_resolver
        self.profile_resolver = profile_resolver
        self.artifact_root = artifact_root
        self.clock = clock
        self.reconciler = RecoveryReconciler(supervisor.journal, supervisor.units)
        self.validator = RegistrationResponseValidator()
        # In-memory only: an open tool conversation cannot survive a service restart.
        self._live: dict[str, _Live] = {}
        self._lock = threading.RLock()
        database.registry.register(AGENT_RUN_MIGRATION)
        database.initialize()

    # -- assignments ---------------------------------------------------------

    def create_assignment(
        self,
        assignment_id: str,
        project_id: str,
        activity_id: str,
        role: str,
        tool: str,
        model_id: str,
        *,
        duration_seconds: int = 1800,
        automatic_limit: int = 2,
    ) -> None:
        for value, name in ((assignment_id, "assignment_id"), (project_id, "project_id"), (activity_id, "activity_id")):
            canonical_identifier(value, name)
        with self.database.transaction() as tx:
            tx.execute(
                """
                INSERT INTO service_agent_assignments(
                    assignment_id, project_id, activity_id, role, tool, model_id,
                    duration_seconds, automatic_limit, state)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'ready')
                """,
                (assignment_id, project_id, activity_id, role, tool, model_id, duration_seconds, automatic_limit),
            )

    def set_next_run_duration(self, assignment_id: str, seconds: int) -> None:
        """An accepted duration exception: applies to the next eligible run only, once."""
        if isinstance(seconds, bool) or not isinstance(seconds, int) or seconds <= 0:
            raise AgentRunError("invalid_duration", "duration must be a positive number of seconds")
        with self.database.transaction() as tx:
            tx.execute(
                "UPDATE service_agent_assignments SET next_duration_seconds = ? WHERE assignment_id = ?",
                (seconds, assignment_id),
            )

    # -- launching -----------------------------------------------------------

    def start_run(self, assignment_id: str, run_id: str, kind: str, build: Builder, *, intervention: str = "") -> RunView:
        canonical_identifier(run_id, "run_id")
        if kind not in _KINDS:
            raise AgentRunError("invalid_kind", "run kind is invalid")
        with self.database.transaction() as tx:
            row = self._assignment(tx, assignment_id)
            project_id, activity_id, role, tool, model_id = row["project_id"], row["activity_id"], row["role"], row["tool"], row["model_id"]
            duration = self._reserve(tx, row, run_id, kind, intervention)
        identity = OperationIdentity(project_id, activity_id, assignment_id, run_id)
        try:
            route = self.route_resolver(role, tool, model_id)
            spec = build(run_id)
            if spec.assignment.run_id != run_id or spec.assignment.assignment_id != assignment_id:
                raise AgentRunError("assignment_mismatch", "assignment does not match the reserved run")
            self._check_baseline(assignment_id, spec.assignment)
            profile = self.profile_resolver(route)
            workspace = self.workspaces.prepare(
                project_id=project_id,
                activity_id=activity_id,
                run_id=run_id,
                source_repository=spec.source_repository,
                source_commit=spec.assignment.source_commit,
                assignment_bytes=spec.assignment.to_bytes(),
                inputs=spec.inputs,
            )
            live = _Live(route, spec.assignment, workspace)
            self._save_snapshot(run_id, spec)
            if tool == "codex":
                live.conversation = CodexTransport().open(route, spec.assignment, workspace, profile)
                launch = live.conversation.launch
            elif tool == "claude_code":
                launch = ClaudeTransport().launch(route, spec.assignment, workspace, profile)
            else:
                raise AgentRunError("unsupported_tool", "no adapter is installed for this tool")
        except Exception as error:
            code = getattr(error, "code", "launch_setup_failed")
            self._finish(run_id, "failed", failure_code=code, reason=str(error)[:_DETAIL_LIMIT])
            self._settle_failure(assignment_id, run_id, code)
            raise
        request = LaunchRequest(identity, tuple(launch.isolated_arguments), launch.cwd, float(duration), float(duration))
        try:
            record = self.supervisor.launch(request)
        except SupervisionError as error:
            # An unconfirmed launch may have started a unit: block replacement.
            self._finish(run_id, "blocked", failure_code=error.code, reason="launch outcome unknown")
            self._pause(assignment_id, error.code, run_id)
            raise
        self._live[run_id] = live
        with self.database.transaction() as tx:
            tx.execute("UPDATE service_agent_runs SET workspace_json = ? WHERE run_id = ?", (_workspace_json(workspace), run_id))
            tx.execute(
                """
                UPDATE service_agent_runs SET state = 'running', unit_name = ?, invocation_id = ?,
                    tool_version = ?, model_id = ?, configuration_hash = ?
                WHERE run_id = ?
                """,
                (record.unit_name, record.invocation_id, route.tool_version, route.requested_model_id, route.configuration_hash, run_id),
            )
            self._emit(tx, project_id, activity_id, "agent_run.started", {"run_id": run_id, "assignment_id": assignment_id, "role": role, "tool": tool, "model": model_id, "kind": kind, "duration_seconds": duration})
        if live.conversation is not None:
            for outgoing in live.conversation.launch.initial_stdin:
                self.supervisor.send(identity, outgoing)
        return self.view(run_id)

    def _reserve(self, tx: Transaction, row: Mapping[str, object], run_id: str, kind: str, intervention: str) -> int:
        assignment_id = str(row["assignment_id"])
        open_run = tx.execute(
            f"SELECT run_id, state FROM service_agent_runs WHERE assignment_id = ? AND state IN ({','.join('?' for _ in _OPEN_RUN_STATES)})",
            (assignment_id, *_OPEN_RUN_STATES),
        ).fetchone()
        if open_run is not None:
            raise AgentRunError("run_not_ended", "an earlier run is not confirmed ended", run_id=open_run[0], state=open_run[1])
        previous = tx.execute("SELECT COUNT(*) FROM service_agent_runs WHERE assignment_id = ?", (assignment_id,)).fetchone()[0]
        automatic_used, manual_used = int(row["automatic_used"]), int(row["manual_used"])
        if kind == "initial":
            if previous:
                raise AgentRunError("not_initial", "the assignment already has a run")
        elif previous == 0:
            raise AgentRunError("no_failed_run", "there is no earlier run to recover")
        if kind == "recovery":
            if row["state"] != "needs_recovery":
                raise AgentRunError("recovery_not_permitted", "the last run's cause does not permit automatic recovery")
            if automatic_used >= int(row["automatic_limit"]):
                raise AgentRunError("automatic_limit", "the automatic recovery limit is used")
            automatic_used += 1
        if kind == "manual":
            if row["state"] not in {"paused", "needs_recovery"}:
                raise AgentRunError("manual_not_permitted", "the assignment is not paused")
            if not intervention.strip():
                raise AgentRunError("intervention_required", "a manual retry records what changed")
            manual_used += 1
        duration = int(row["next_duration_seconds"]) if row["next_duration_seconds"] is not None and kind != "initial" else int(row["duration_seconds"])
        if row["next_duration_seconds"] is not None and kind != "initial":
            # The exception is consumed once by the launch that applies it.
            tx.execute("UPDATE service_agent_assignments SET next_duration_seconds = NULL WHERE assignment_id = ?", (assignment_id,))
        tx.execute(
            "INSERT INTO service_agent_runs(run_id, assignment_id, kind, state, duration_seconds, reserved_at) VALUES (?, ?, ?, 'reserved', ?, ?)",
            (run_id, assignment_id, kind, duration, _now()),
        )
        tx.execute(
            """
            UPDATE service_agent_assignments SET current_run_id = ?, state = 'running', pause_reason = NULL,
                automatic_used = ?, manual_used = ? WHERE assignment_id = ?
            """,
            (run_id, automatic_used, manual_used, assignment_id),
        )
        return duration

    def _check_baseline(self, assignment_id: str, assignment: AgentAssignment) -> None:
        """A later run may change task and inputs, never the assigned source or decision version."""
        with self.database.read_connection() as connection:
            first = connection.execute(
                "SELECT source_commit, decision_version FROM service_agent_runs WHERE assignment_id = ? AND source_commit IS NOT NULL ORDER BY rowid LIMIT 1",
                (assignment_id,),
            ).fetchone()
        if first is not None and tuple(first) != (assignment.source_commit, assignment.decision_version):
            raise AgentRunError("assignment_changed", "a later run cannot change the assigned source or decision version")

    def _save_snapshot(self, run_id: str, spec: RunBuild) -> None:
        assignment_bytes = spec.assignment.to_bytes()
        inputs = {name: hashlib.sha256(data).hexdigest() for name, data in sorted(spec.inputs.items())}
        with self.database.transaction() as tx:
            tx.execute(
                "UPDATE service_agent_runs SET assignment_sha256 = ?, source_commit = ?, decision_version = ?, assignment_json = ?, inputs_json = ? WHERE run_id = ?",
                (hashlib.sha256(assignment_bytes).hexdigest(), spec.assignment.source_commit, spec.assignment.decision_version,
                 assignment_bytes.decode("utf-8"), canonical_json(inputs), run_id),
            )

    # -- progress and completion --------------------------------------------

    def poll(self, run_id: str) -> RunView:
        with self._lock:
            return self._poll(run_id)

    def _poll(self, run_id: str) -> RunView:
        run = self._run(run_id)
        if run["state"] not in _OPEN_RUN_STATES:
            return self.view(run_id)
        assignment = self._assignment_for_run(run_id)
        identity = OperationIdentity(assignment["project_id"], assignment["activity_id"], assignment["assignment_id"], run_id)
        record = self.supervisor.poll(identity)
        self._mirror(identity, record, assignment)
        live = self._live.get(run_id)
        if live is not None and live.conversation is not None and live.result_at is not None and record.state == "running":
            if self.clock() - live.result_at > _POST_RESULT_GRACE_SECONDS:
                record = self.supervisor.stop(identity, "post_result_cleanup")
        if record.state == "running":
            return self.view(run_id)
        return self._finalize(identity, record, assignment)

    def _mirror(self, identity: OperationIdentity, record, assignment: Mapping[str, object]) -> None:
        run_id = identity.run_id
        live = self._live.get(run_id)
        with self.database.transaction() as tx:
            known = tx.execute("SELECT COALESCE(MAX(sequence), 0) FROM service_agent_run_events WHERE run_id = ?", (run_id,)).fetchone()[0]
            for event in record.events:
                sequence = int(event["sequence"])
                if sequence <= known:
                    continue  # replayed events are ignored
                kind = str(event["kind"])
                detail = _detail(event)
                tx.execute(
                    "INSERT INTO service_agent_run_events(run_id, sequence, kind, detail) VALUES (?, ?, ?, ?)",
                    (run_id, sequence, kind, detail),
                )
                progress = _progress(str(assignment["tool"]), event) if kind == "stdout" else None
                if kind != "stdout" or progress:
                    self._emit(tx, str(assignment["project_id"]), str(assignment["activity_id"]), "agent_run.progress",
                               {"run_id": run_id, "sequence": sequence, "kind": kind, "text": progress or kind})
        if live is None or live.conversation is None:
            return
        for event in record.events:
            sequence = int(event["sequence"])
            if sequence <= live.fed or event["kind"] != "stdout":
                continue
            live.fed = sequence
            try:
                for outgoing in live.conversation.receive(str(event["data"]).encode("utf-8")):
                    self.supervisor.send(identity, outgoing)
            except (TransportError, SupervisionError) as error:
                live.failure = getattr(error, "code", "protocol_error")
                self.supervisor.stop(identity, "conversation_failed")
                return
            if live.conversation.state == "completed" and live.result_at is None:
                live.result_at = self.clock()
                self.supervisor.send(identity, b"", close=True)

    def _finalize(self, identity: OperationIdentity, record, assignment: Mapping[str, object]) -> RunView:
        run_id = identity.run_id
        if self._run(run_id)["state"] not in _OPEN_RUN_STATES:
            return self.view(run_id)  # already settled: never overwrite accepted work
        live = self._live.pop(run_id, None)
        seconds = max(0.0, self.clock() - record.launched_monotonic)
        state = record.state
        if state in {"stop_unconfirmed", "recovery_required", "launch_uncertain"}:
            self._finish(run_id, "blocked", failure_code="stop_unconfirmed", reason=record.terminal_reason or state, seconds=seconds)
            self._pause(identity.assignment_id, "the run's stop or identity is unknown", run_id)
            return self.view(run_id)
        if state == "timed_out":
            self._finish(run_id, "timed_out", failure_code="timed_out", reason="run duration reached", seconds=seconds)
            self._pause(identity.assignment_id, "the run reached its duration limit", run_id)
            return self.view(run_id)
        if state == "cancelled":
            self._finish(run_id, "cancelled", reason=record.terminal_reason, seconds=seconds)
            self._settle(identity.assignment_id, run_id, "cancelled")
            return self.view(run_id)
        try:
            if live is None:
                live = self._rebuild(identity, assignment, record)
            if live.failure is not None:
                raise TransportError(live.failure, "the tool conversation failed")
            try:
                decoded = self._decode(assignment, live, record)
            except TransportError:
                if state in {"stopped", "stalled"}:
                    # Stopped before a complete result was saved.
                    code = "stalled" if state == "stalled" else "interrupted"
                    self._finish(run_id, "failed", failure_code=code, reason=record.terminal_reason, seconds=seconds)
                    self._settle_failure(identity.assignment_id, run_id, code)
                    return self.view(run_id)
                raise
            with self.database.transaction() as tx:
                current = tx.execute("SELECT current_run_id FROM service_agent_assignments WHERE assignment_id = ?", (identity.assignment_id,)).fetchone()[0]
            response = self.validator.validate(
                decoded,
                route=live.route,
                assignment=live.assignment,
                workspace=live.workspace,
                current_assignment_id=identity.assignment_id,
                current_run_id=current,
            )
        except TransportError as error:
            code = error.code
            if code == "stale_assignment":
                with self.database.transaction() as tx:
                    tx.execute(
                        "INSERT INTO service_agent_run_events(run_id, sequence, kind, detail) VALUES (?, (SELECT COALESCE(MAX(sequence), 0) + 1 FROM service_agent_run_events WHERE run_id = ?), 'stale_result', ?)",
                        (run_id, run_id, "result from a run that is no longer current was kept as evidence only"),
                    )
                self._finish(run_id, "stale", failure_code=code, reason="not the current run", seconds=seconds)
                return self.view(run_id)
            self._finish(run_id, "failed", failure_code=code, reason=str(error)[:_DETAIL_LIMIT], seconds=seconds)
            self._settle_failure(identity.assignment_id, run_id, code)
            return self.view(run_id)
        stored = self._store_artifacts(run_id, live, response)
        session = decoded.session_id or decoded.thread_id
        if response.result == "technical_failure":
            # A valid report of failure is still a failure: it enters technical recovery.
            self._finish(run_id, "failed", failure_code="technical_failure", reason=str((response.failure or {}).get("message", ""))[:_DETAIL_LIMIT],
                         seconds=seconds, response=response, raw=decoded.response, session=session, stored=stored)
            self._settle_failure(identity.assignment_id, run_id, "technical_failure")
            return self.view(run_id)
        self._finish(run_id, "completed", reason=record.terminal_reason, seconds=seconds, response=response, raw=decoded.response, session=session, stored=stored)
        self._settle(identity.assignment_id, run_id, "waiting_for_answers" if response.result == "clarification_required" else "completed")
        return self.view(run_id)

    def _decode(self, assignment: Mapping[str, object], live: "_Live", record) -> DecodedToolResult:
        if live.conversation is not None:
            return live.conversation.result()
        raw = "\n".join(str(e["data"]).rstrip("\n") for e in record.events if e["kind"] == "stdout")
        return ClaudeTransport().decode(raw, live.route)

    def _rebuild(self, identity: OperationIdentity, assignment: Mapping[str, object], record) -> "_Live":
        """After a restart, rebuild the run from its saved snapshot and replay its saved output."""
        run = self._run(identity.run_id)
        if not run["assignment_json"] or not run["workspace_json"]:
            raise TransportError("interrupted", "the run has no saved assignment snapshot")
        saved = json.loads(str(run["assignment_json"]))
        route = self.route_resolver(str(assignment["role"]), str(assignment["tool"]), str(assignment["model_id"]))
        if route.configuration_hash != run["configuration_hash"]:
            raise TransportError("configuration_changed", "the route configuration changed since the run started")
        prepared = _workspace_from_json(str(run["workspace_json"]), self.workspaces)
        parsed = _assignment_from_json(saved)
        live = _Live(route, parsed, prepared)
        if assignment["tool"] == "codex":
            live.conversation = CodexTransport().open(route, parsed, prepared, self.profile_resolver(route))
            for event in record.events:
                if event["kind"] == "stdout":
                    live.conversation.receive(str(event["data"]).encode("utf-8"))
        return live

    def _store_artifacts(self, run_id: str, live: "_Live", response) -> dict[str, tuple[str, str, str]]:
        stored: dict[str, tuple[str, str, str]] = {}
        target = self.artifact_root / run_id
        for field, reference in (("candidate", response.candidate), ("assessment", response.assessment), ("reviewed_assessment", response.reviewed_assessment)):
            if reference is None:
                continue
            source = live.workspace.resolve_artifact(reference.path, allow_input=field == "reviewed_assessment" or (field == "candidate" and live.assignment.role == "fidelity_reviewer"))
            target.mkdir(parents=True, exist_ok=True)
            destination = target / f"{field}-{reference.sha256[:12]}"
            shutil.copyfile(source, destination)
            destination.chmod(0o440)
            if hashlib.sha256(destination.read_bytes()).hexdigest() != reference.sha256:
                raise TransportError("artifact_mismatch", f"{field} changed while it was stored")
            stored[field] = (reference.path, reference.sha256, str(destination))
        return stored

    # -- stop, recovery ------------------------------------------------------

    def stop(self, run_id: str, reason: str = "cancelled") -> RunView:
        with self._lock:
            return self._stop(run_id, reason)

    def _stop(self, run_id: str, reason: str) -> RunView:
        if self._run(run_id)["state"] not in _OPEN_RUN_STATES:
            return self.view(run_id)
        assignment = self._assignment_for_run(run_id)
        identity = OperationIdentity(assignment["project_id"], assignment["activity_id"], assignment["assignment_id"], run_id)
        with self.database.transaction() as tx:
            tx.execute("UPDATE service_agent_runs SET state = 'stopping' WHERE run_id = ? AND state = 'running'", (run_id,))
        record = self.supervisor.stop(identity, reason)
        self._mirror(identity, record, assignment)
        return self._finalize(identity, record, assignment)

    def recover(self) -> list[RunView]:
        with self._lock:
            return self._recover()

    def _recover(self) -> list[RunView]:
        """After a service restart: reconcile every open run against its saved supervisor record.

        Never launches anything. A run that is still alive but whose tool conversation this
        instance cannot resume is stopped and confirmed ended first; only then may a recovery run follow.
        """
        views = []
        with self.database.read_connection() as connection:
            open_runs = [row[0] for row in connection.execute(
                f"SELECT run_id FROM service_agent_runs WHERE state IN ({','.join('?' for _ in _OPEN_RUN_STATES)})", _OPEN_RUN_STATES)]
        for run_id in open_runs:
            assignment = self._assignment_for_run(run_id)
            identity = OperationIdentity(assignment["project_id"], assignment["activity_id"], assignment["assignment_id"], run_id)
            decision = self.reconciler.reconcile(identity)
            record = self.supervisor.journal.get(identity.key)
            if record is None:
                self._finish(run_id, "failed", failure_code="interrupted", reason="the launch was never recorded by the supervisor")
                self._settle_failure(identity.assignment_id, run_id, "interrupted")
                views.append(self.view(run_id))
                continue
            if decision.status == "running":
                record = self.supervisor.stop(identity, "service_restarted")
            self._mirror(identity, record, assignment)
            views.append(self._finalize(identity, record, assignment))
        return views

    # -- outcomes ------------------------------------------------------------

    def _settle(self, assignment_id: str, run_id: str, outcome: str) -> None:
        with self.database.transaction() as tx:
            tx.execute("UPDATE service_agent_assignments SET state = ? WHERE assignment_id = ? AND current_run_id = ?", (outcome, assignment_id, run_id))
            row = self._assignment(tx, assignment_id)
            self._emit(tx, row["project_id"], row["activity_id"], "agent_run.ended", {"run_id": run_id, "assignment_id": assignment_id, "outcome": outcome})

    def _settle_failure(self, assignment_id: str, run_id: str, code: str) -> None:
        if code in _RETRYABLE:
            with self.database.transaction() as tx:
                row = self._assignment(tx, assignment_id)
                if int(row["automatic_used"]) < int(row["automatic_limit"]):
                    tx.execute("UPDATE service_agent_assignments SET state = 'needs_recovery', pause_reason = ? WHERE assignment_id = ? AND current_run_id = ?", (code, assignment_id, run_id))
                    self._emit(tx, row["project_id"], row["activity_id"], "agent_run.ended", {"run_id": run_id, "assignment_id": assignment_id, "outcome": "needs_recovery", "cause": code})
                    return
            self._pause(assignment_id, "the automatic recovery limit is used", run_id)
            return
        self._pause(assignment_id, f"intervention needed: {code}", run_id)

    def _pause(self, assignment_id: str, reason: str, run_id: str) -> None:
        with self.database.transaction() as tx:
            tx.execute("UPDATE service_agent_assignments SET state = 'paused', pause_reason = ? WHERE assignment_id = ? AND current_run_id = ?", (reason, assignment_id, run_id))
            row = self._assignment(tx, assignment_id)
            self._emit(tx, row["project_id"], row["activity_id"], "agent_run.paused", {"run_id": run_id, "assignment_id": assignment_id, "reason": reason})

    def _finish(self, run_id: str, state: str, *, failure_code: str | None = None, reason: str | None = None,
                seconds: float | None = None, response=None, raw=None, session: str | None = None, stored=None) -> None:
        with self.database.transaction() as tx:
            tx.execute(
                """
                UPDATE service_agent_runs SET state = ?, failure_code = ?, terminal_reason = ?, ended_at = ?,
                    active_seconds = ?, session_id = ?, response_sha256 = ?, response_json = ?
                WHERE run_id = ?
                """,
                (
                    state, failure_code, reason, _now(), seconds, session,
                    None if response is None else response.response_sha256,
                    None if raw is None else canonical_json(raw),
                    run_id,
                ),
            )
            for field, (path, digest, stored_path) in (stored or {}).items():
                tx.execute("INSERT INTO service_agent_artifacts(run_id, field, path, sha256, stored_path) VALUES (?, ?, ?, ?, ?)", (run_id, field, path, digest, stored_path))

    # -- reads ---------------------------------------------------------------

    def view(self, run_id: str) -> RunView:
        run = self._run(run_id)
        return RunView(run["run_id"], run["assignment_id"], run["kind"], run["state"], run["failure_code"], run["terminal_reason"], run["duration_seconds"], run["response_sha256"])

    def assignment_state(self, assignment_id: str) -> dict[str, object]:
        with self.database.read_connection() as connection:
            connection.row_factory = _row
            row = connection.execute("SELECT * FROM service_agent_assignments WHERE assignment_id = ?", (assignment_id,)).fetchone()
        if row is None:
            raise AgentRunError("assignment_not_found", "the assignment does not exist")
        return dict(row)

    def events(self, run_id: str) -> list[tuple[int, str, str]]:
        with self.database.read_connection() as connection:
            return [tuple(r) for r in connection.execute("SELECT sequence, kind, detail FROM service_agent_run_events WHERE run_id = ? ORDER BY sequence", (run_id,))]

    def _run(self, run_id: str) -> dict[str, object]:
        with self.database.read_connection() as connection:
            connection.row_factory = _row
            row = connection.execute("SELECT * FROM service_agent_runs WHERE run_id = ?", (run_id,)).fetchone()
        if row is None:
            raise AgentRunError("run_not_found", "the run does not exist")
        return dict(row)

    def _assignment(self, tx: Transaction, assignment_id: str) -> dict[str, object]:
        cursor = tx.execute("SELECT * FROM service_agent_assignments WHERE assignment_id = ?", (assignment_id,))
        row = cursor.fetchone()
        if row is None:
            raise AgentRunError("assignment_not_found", "the assignment does not exist")
        return {column[0]: value for column, value in zip(cursor.description, row)}

    def _assignment_for_run(self, run_id: str) -> dict[str, object]:
        run = self._run(run_id)
        with self.database.read_connection() as connection:
            connection.row_factory = _row
            return dict(connection.execute("SELECT * FROM service_agent_assignments WHERE assignment_id = ?", (run["assignment_id"],)).fetchone())

    @staticmethod
    def _emit(tx: Transaction, project_id: str, activity_id: str, event_type: str, data: Mapping[str, object]) -> None:
        tx.execute(
            """
            INSERT INTO outbox_events(schema_version, event_id, occurred_at, project_id, activity_id, type, data_json)
            VALUES (1, ?, ?, ?, ?, ?, ?)
            """,
            (f"agent-{uuid.uuid4().hex}", _now(), project_id, activity_id, event_type, canonical_json(data)),
        )


@dataclass
class _Live:
    route: ResolvedAgentRoute
    assignment: AgentAssignment
    workspace: PreparedWorkspace
    conversation: object | None = None
    fed: int = 0
    result_at: float | None = None
    failure: str | None = None


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _row(cursor, values):  # sqlite3 row factory
    return {column[0]: value for column, value in zip(cursor.description, values)}


def _detail(event: Mapping[str, object]) -> str:
    data = {key: value for key, value in event.items() if key not in {"sequence", "kind", "at_monotonic"}}
    text = json.dumps(data, sort_keys=True, default=str)
    return text[:_DETAIL_LIMIT]


def _progress(tool: str, event: Mapping[str, object]) -> str | None:
    """A short human-readable line from the tool's own message; never treated as completion."""
    try:
        message = json.loads(str(event.get("data", "")))
    except ValueError:
        return None
    if not isinstance(message, dict):
        return None
    if tool == "codex":
        item = (message.get("params") or {}).get("item") if message.get("method") == "item/completed" else None
        if isinstance(item, dict) and item.get("type") == "agentMessage" and isinstance(item.get("text"), str):
            return item["text"][:300]
        if message.get("method") in {"turn/started", "turn/completed"}:
            return str(message["method"])
        return None
    if message.get("type") == "assistant":
        for block in (message.get("message") or {}).get("content", []):
            if isinstance(block, dict) and block.get("type") == "text":
                return str(block.get("text", ""))[:300]
            if isinstance(block, dict) and block.get("type") == "tool_use":
                return f"using {block.get('name')}"
    return None


def _workspace_json(workspace: PreparedWorkspace) -> str:
    return json.dumps({
        "project_id": workspace.project_id, "activity_id": workspace.activity_id, "run_id": workspace.run_id,
        "source_commit": workspace.source_commit, "paths": {k: str(v) for k, v in vars(workspace.paths).items()},
        "assignment_sha256": workspace.assignment_sha256, "immutable_hashes": [list(pair) for pair in workspace.immutable_hashes],
        "isolation_executable": str(workspace.isolation_executable), "workspace_root": str(workspace.workspace_root),
    })


def _workspace_from_json(text: str, manager: WorkspaceManager) -> PreparedWorkspace:
    value = json.loads(text)
    return PreparedWorkspace(
        value["project_id"], value["activity_id"], value["run_id"], value["source_commit"],
        WorkspacePaths(**{k: Path(v) for k, v in value["paths"].items()}), value["assignment_sha256"],
        tuple((a, b) for a, b in value["immutable_hashes"]), Path(value["isolation_executable"]), Path(value["workspace_root"]),
    )


def _assignment_from_json(value: Mapping[str, object]) -> AgentAssignment:
    return AgentAssignment(
        project_id=value["project_id"], activity_id=value["activity_id"], assignment_id=value["assignment_id"], run_id=value["run_id"],
        parent_assignment_id=value["parent_assignment_id"], role=value["role"], role_responsibilities=tuple(value["role_responsibilities"]),
        task=value["task"], source_commit=value["source_commit"], decision_version=value["decision_version"],
        instructions=value["instructions"], permitted_actions=tuple(value["permitted_actions"]),
        writable_locations=tuple(value["writable_locations"]), limits=value["limits"],
        clarification_conditions=tuple(value["clarification_conditions"]), response_schema=value["required_response"]["schema"],
        assigned_artifacts={k: ArtifactReference.from_mapping(v, k) for k, v in value["assigned_artifacts"].items()},
    )
