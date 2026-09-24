"""Architecture loop, foundations stage: start, persistent architect session, investigation and saved foundations.

One architecture attempt is one activity with a durable row, like registration, so the step machine
(``tick``) can be repeated safely. The architect keeps one persistent session across runs: its saved
conversation is restored into each run's isolated home, and answers reach it only in the next
assignment. Findings, decisions, structure and specialist guidance are validated, saved in SQL and
published to the registered repository; the session's memory is never the record.
"""

from __future__ import annotations

import json
import logging
import subprocess
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping

from maestro.agents.architecture_contract import RESPONSE_SCHEMA
from maestro.agents.session_state import SessionUse
from maestro.agents.transport import AgentAssignment, _findings, _questions
from maestro.foundation import Database, DomainMigration, Transaction, canonical_json

from . import architecture_records as records_module
from .activities import ActivityAction, ActivityRecord, ActivityRepository, ConversationRecord, FindingRecord, QuestionRecord
from .agent_runs import AgentRunError, AgentRunService, RunBuild
from .architecture_records import FoundationError
from .process_definitions import ProcessDefinitions
from .processes import ProcessPolicyError
from .questions import AnswerChoice, DeliveredAnswer, QuestionService, RecipientDeliveryInterrupted
from .registration_github import DestinationError, GitHubDestination, RepositoryProfile
from .registry import OperationHandler, OperationResult, PreparedOperation, RequestLike
from .requests import RequestRejection
from .reservations import ProjectReservations, ReservationError

log = logging.getLogger("maestro.architecture")

ARCHITECTURE_MIGRATION = DomainMigration(
    domain="service_architecture",
    version=1,
    identity="service-architecture-v1",
    statements=(
        """
        CREATE TABLE service_architectures(
            activity_id TEXT PRIMARY KEY REFERENCES service_activities(activity_id) ON DELETE RESTRICT,
            project_id TEXT NOT NULL REFERENCES service_projects(project_id) ON DELETE RESTRICT,
            registration_activity_id TEXT NOT NULL,
            registration_json TEXT NOT NULL,
            scope_json TEXT NOT NULL,
            repository TEXT NOT NULL,
            overview_path TEXT NOT NULL,
            publication_branch TEXT NOT NULL,
            source_ref TEXT NOT NULL,
            source_commit TEXT NOT NULL,
            profile_json TEXT NOT NULL,
            architect_tool TEXT NOT NULL, architect_model TEXT NOT NULL,
            reviewer_tool TEXT NOT NULL, reviewer_model TEXT NOT NULL,
            outcome_refs_json TEXT NOT NULL,
            state TEXT NOT NULL,
            pending_json TEXT NOT NULL DEFAULT '{}',
            architecture_version INTEGER NOT NULL,
            decision_version INTEGER NOT NULL DEFAULT 1,
            pass_number INTEGER NOT NULL DEFAULT 0,
            question_seq INTEGER NOT NULL DEFAULT 0,
            finding_seq INTEGER NOT NULL DEFAULT 0,
            foundation_json TEXT,
            foundations_ref_json TEXT,
            cancel_requested INTEGER NOT NULL DEFAULT 0,
            note TEXT,
            created_at TEXT NOT NULL
        )
        """,
        """
        CREATE TABLE service_architecture_sessions(
            session_id TEXT PRIMARY KEY,
            activity_id TEXT NOT NULL REFERENCES service_architectures(activity_id),
            role TEXT NOT NULL,
            tool TEXT NOT NULL,
            model TEXT NOT NULL,
            provider_session_id TEXT,
            assigned_provider_id TEXT,
            prior_session_id TEXT,
            state TEXT NOT NULL CHECK(state IN ('active', 'lost')),
            note TEXT,
            created_at TEXT NOT NULL
        )
        """,
        """
        CREATE TABLE service_architecture_decisions(
            decision_id TEXT PRIMARY KEY,
            activity_id TEXT NOT NULL REFERENCES service_architectures(activity_id),
            subject TEXT NOT NULL,
            question_id TEXT NOT NULL,
            question_text TEXT NOT NULL,
            answer_text TEXT NOT NULL,
            choice_id TEXT,
            rationale TEXT NOT NULL,
            decision_version INTEGER NOT NULL,
            created_at TEXT NOT NULL
        )
        """,
        """
        CREATE TABLE service_architecture_findings(
            activity_id TEXT NOT NULL REFERENCES service_architectures(activity_id),
            local_key TEXT NOT NULL,
            finding_id TEXT NOT NULL,
            version INTEGER NOT NULL,
            content_sha256 TEXT NOT NULL,
            PRIMARY KEY(activity_id, local_key)
        )
        """,
        """
        CREATE TABLE service_architecture_outputs(
            activity_id TEXT NOT NULL REFERENCES service_architectures(activity_id),
            pass_number INTEGER NOT NULL,
            path TEXT NOT NULL,
            sha256 TEXT NOT NULL,
            content BLOB NOT NULL,
            PRIMARY KEY(activity_id, pass_number, path)
        )
        """,
        """
        CREATE TABLE service_architecture_publications(
            operation_id TEXT PRIMARY KEY,
            activity_id TEXT NOT NULL REFERENCES service_architectures(activity_id),
            kind TEXT NOT NULL CHECK(kind IN ('specialists', 'foundations', 'index')),
            repository TEXT NOT NULL,
            branch TEXT NOT NULL,
            files_json TEXT NOT NULL,
            state TEXT NOT NULL CHECK(state IN ('prepared', 'writing', 'verified', 'applied', 'paused')),
            commit_sha TEXT,
            detail TEXT,
            profile_json TEXT NOT NULL
        )
        """,
    ),
)

_OPEN_STATES = ("architect", "architect_waiting", "publishing", "saved", "paused", "cancelling")
_WORKING_STATES = ("architect", "publishing", "cancelling")
_SELECTION = ("tool", "model_id")
_LOST_SESSION_CODES = frozenset({"identity_unverified"})

_TASK = """You are the Maestro Project Architect. This is the first stage of the architecture loop: understand the existing code for the confirmed project outcomes and save lasting foundations. Work only from this assignment, the files under input/, and the product source under source/ (fixed at the assigned commit). Never modify source/ or input/; write only under output/.

1. Read input/registration-summary.json and input/outcomes.json, then the confirmed milestone and requirement records under input/registration/ (the outcomes you must serve). input/decisions.json holds Owner answers already recorded.
2. Investigate the existing source that bears on those outcomes: responsibilities, interfaces, dependencies, setup and how the parts actually connect. Read code and run only read-only commands. Reading code shows what it supports; it does not prove it works, so never claim operation. Stay proportionate: cover what the confirmed outcomes touch. For every outcome say whether existing code supports it (reuse), needs changes (update), is better replaced or retired, or is missing (missing). Choose the strongest path for the outcome; reuse is not presumed. Consider effects across the whole product.
3. Report findings in the response `findings`: each cites real source (the path relative to the repository root, so `docs/x.md` and never `source/docs/x.md`; the assigned commit; and a locator such as a symbol or line), or, if nothing exists to cite, states missing_information. Blocking means the missing or contradictory information prevents reliable architecture; observations and risks are non_blocking. Give each finding a unique local_key.
4. Write output/investigation.json exactly as {{"schema":"architecture_investigation_v1","summary":"<plain summary>","decisions":[{{"local_key":"<unique key>","subject":"<plain subject>","disposition":"reuse|update|replace|retire|missing","rationale":"<why>","code_paths":["<existing path under source/>"],"evidence":[{{"path":"<existing path>","commit":"{commit}","locator":"<symbol or line>"}}],"outcome_ids":["<record id from input/outcomes.json>"],"finding_keys":["<local_key of a finding above>"]}}]}}. Every listed path is relative to the repository root without a source/ prefix and must exist in source/. Together the decisions must cover every milestone outcome id: {milestones}. Use code_paths [] only with disposition missing.
5. Write output/project-structure.json exactly as {{"schema":"architecture_structure_v1","summary":"<plain summary>","locations":[{{"current_path":"<existing path or null>","intended_path":"<path>","responsibility":"<what lives there>","owner":"<specialist local_key or shared>","shared_boundaries":["<boundary>"],"planned_move":false}}],"specialists":[{{"local_key":"<unique key>","subject":"<plain subject>","source_area":"<existing directory under source/>","role_title":"<Role Title>","owner":"<Role Title>"}}]}}. The structure is AI-friendly: it makes feature locations, shared code, responsibilities and boundaries clear, distinguishing current locations from intended changes (a proposed layout is not code already moved; planned_move is false only when current_path equals intended_path). Name 2 to 4 specialists, one per code area that needs expertise, each with a distinct source_area.
6. For each specialist write, under output/specialists/<source_area>/.maestro/ (where <source_area> is a real subdirectory of the repository holding the code the specialist covers, never the repository root and never .git): role-<role-title-lowercase-hyphenated>.md (first line "# <Role Title>", then headings Responsibility, Authority, Source area, Inputs and outputs) and context.md (headings Verified facts, Source references, Knowledge gaps; distinguish established facts from gaps; cite source paths). Optionally memory.md (heading Entries). Keep each file under 40 lines. Creating a specialist does not start any worker and gives it no knowledge it has not acquired.
7. Ask the Owner only when missing information affects intended outcomes, scope or an Owner-reserved decision, or requirements conflict: return result clarification_required with specific questions (each with a plain question, the reason, options where alternatives exist) and no output files. Retiring or replacing working code that no confirmed outcome requires is not yours to decide: ask the Owner before choosing retire or replace for it, and offer keeping it as an option. Other routine technical choices are yours: record them as decisions. Never fill a gap with an unsupported assumption.
8. When the files are written compute the SHA-256 of each with sha256sum and list every file you wrote in `outputs` as {{"path":"output/<file>","sha256":"<digest>","version":1}}, including the specialist files; write nothing else. result is completed; failure is null; input_manifest, reviewed_set and review_outcome are null; allocations is [].
{continuation} Copy contract_version (1), assignment_id, run_id, session_id, project_id, activity_id, role, source_commit and decision_version exactly from assignment.json. Return only the structured response."""

_CONTINUATION = "This session continues your earlier work: your conversation history is restored. Use your earlier investigation; do not repeat it from scratch. input/answers.json holds any Owner answers recorded since. Then produce the files."
_REPLACEMENT = "Your earlier conversation was unavailable, so this is a replacement session. The verified records in input/ (decisions, answers) are authoritative; nothing of your earlier work is assumed."


class ArchitectureRejection(RequestRejection):
    pass


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


class ArchitectureService:
    """Owns architecture-loop state; the worker thread calls ``tick`` repeatedly."""

    def __init__(
        self,
        database: Database,
        *,
        records: ActivityRepository,
        questions: QuestionService,
        reservations: ProjectReservations,
        definitions: ProcessDefinitions,
        runs: AgentRunService | None,
        profiles: Mapping[str, RepositoryProfile],
        destination: Callable[[RepositoryProfile], GitHubDestination],
        state_dir: Path,
        owner_id: str,
        schema: Mapping[str, Any] | None = None,
    ) -> None:
        self.database = database
        self.records = records
        self.questions = questions
        self.reservations = reservations
        self.definitions = definitions
        self.runs = runs
        self.profiles = profiles
        self._destination = destination
        self.state_dir = state_dir
        self.owner_id = owner_id
        self.schema = schema
        self._locks: dict[str, threading.Lock] = {}
        self._guard = threading.Lock()
        self._trees: dict[tuple[str, str], tuple[set[str], set[str]]] = {}
        database.registry.register(ARCHITECTURE_MIGRATION)
        database.initialize()

    @property
    def operation_handlers(self) -> tuple[OperationHandler, ...]:
        return (
            OperationHandler("architecture.start", self.prepare_start),
            OperationHandler("architecture.cancel", self.prepare_cancel),
            OperationHandler("architecture.retry", self.prepare_retry),
        )

    def owns(self, activity_id: str) -> bool:
        return self._read("SELECT 1 AS n FROM service_architectures WHERE activity_id = ?", (activity_id,)) is not None

    # ------------------------------------------------------------------ start

    def prepare_start(self, request: RequestLike) -> PreparedOperation:
        payload = dict(request.payload)
        if request.project_id is None or request.activity_id is not None or request.question_id is not None:
            raise ValueError("architecture.start needs a project and no activity or question")
        if request.expected_version is not None:
            raise ValueError("architecture.start expected_version must be null")
        if set(payload) != {"registration_ref", "architect", "reviewer"}:
            raise ValueError("architecture.start payload must be registration_ref, architect and reviewer")
        selections = {}
        for role in ("architect", "reviewer"):
            value = payload[role]
            if not isinstance(value, Mapping) or set(value) != set(_SELECTION) or not all(isinstance(value[k], str) and value[k] for k in _SELECTION):
                raise ValueError(f"{role} must be an object with tool and model_id")
            selections[role] = (value["tool"], value["model_id"])
            self._check_route(role, *selections[role])
        project_id = request.project_id
        project = self._read("SELECT * FROM service_projects WHERE project_id = ?", (project_id,))
        if project is None:
            raise RequestRejection(404, "project_not_found", "the project does not exist", fields={"project_id": project_id})
        entity_id = f"architecture-request-{request.request_id}"
        existing = self._open_activity(project_id)
        if existing is not None:
            return self._duplicate(entity_id, project_id, existing)
        active = self._read(
            "SELECT a.package_json, r.* FROM service_registration_active a JOIN service_registrations r ON r.activity_id = a.activity_id WHERE a.project_id = ?",
            (project_id,),
        )
        if active is None or project["registration_status"] != "registered":
            raise RequestRejection(409, "registration_not_confirmed", "this project has no confirmed registration; confirm one before starting the architecture loop")
        package = json.loads(active["package_json"])
        given = payload["registration_ref"]
        if not isinstance(given, Mapping) or {k: given.get(k) for k in package} != package or set(given) != set(package):
            raise RequestRejection(409, "registration_ref_stale", "the registration reference is not the project's active confirmed registration", fields={"active": package})
        try:
            self.definitions.evaluate("architecture_loop")
        except ProcessPolicyError as error:
            raise ValueError(f"the architecture loop is not configured: {error}") from error
        try:
            profile = self.profiles[json.loads(active["profile_json"])["profile"]]
            destination = self._destination(profile)

            def read(path: str) -> bytes | None:
                return destination.read_file(package["repository"], package["commit"], path)

            outcomes, _ = records_module.map_outcomes(package, read)
        except (DestinationError, FoundationError, KeyError, ValueError) as error:
            raise ValueError(f"the confirmed registration cannot supply architecture inputs: {getattr(error, 'code', '')} {error}".replace("  ", " ")) from error
        activity_id = f"architecture-{uuid.uuid4().hex[:12]}"
        details = {"active": active, "package": package, "outcomes": outcomes, "selections": selections, "project": project}

        def apply(transaction: Transaction, next_version: int) -> OperationResult:
            found = self._open_activity(project_id, transaction)
            if found is not None:
                return OperationResult(data={"activity_id": found, "duplicate": True, "message": "an architecture activity is already unfinished for this project"}, project_id=project_id, activity_id=found)
            try:
                self.reservations.reserve(transaction, project_id, "start", activity_id, check_unresolved=True)
            except ReservationError as error:
                raise RequestRejection(409, error.code, str(error), fields=error.fields) from error
            now = _now()

            def creator(tx: Transaction, snapshot) -> None:
                version = int(tx.execute("SELECT COALESCE(MAX(architecture_version), 0) + 1 FROM service_architectures WHERE project_id = ? AND foundations_ref_json IS NOT NULL", (project_id,)).fetchone()[0])
                self.records.create_activity(tx, ActivityRecord(
                    activity_id, project_id, "architecture", f"Architecture foundations for {details['project']['name']}", "investigating", 1,
                    "Preparing the persistent architect session", now, None, (ActivityAction(f"{activity_id}-cancel", "Cancel architecture", "action"),),
                ))
                tx.execute("INSERT INTO entity_versions(entity_id, version) VALUES (?, 1) ON CONFLICT(entity_id) DO UPDATE SET version = 1", (activity_id,))
                chosen = details["selections"]
                registration = details["active"]
                tx.execute(
                    """
                    INSERT INTO service_architectures(
                        activity_id, project_id, registration_activity_id, registration_json, scope_json, repository, overview_path,
                        publication_branch, source_ref, source_commit, profile_json, architect_tool, architect_model, reviewer_tool, reviewer_model,
                        outcome_refs_json, state, architecture_version, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'architect', ?, ?)
                    """,
                    (activity_id, project_id, registration["activity_id"], canonical_json(details["package"]), registration["scope_json"], registration["repository"],
                     registration["overview_path"], registration["publication_branch"], registration["source_ref"], registration["source_commit"], registration["profile_json"],
                     *chosen["architect"], *chosen["reviewer"], canonical_json({"outcomes": details["outcomes"]}), version, now),
                )
                tool = chosen["architect"][0]
                tx.execute(
                    "INSERT INTO service_architecture_sessions(session_id, activity_id, role, tool, model, assigned_provider_id, state, created_at) VALUES (?, ?, 'architect', ?, ?, ?, 'active', ?)",
                    (f"{activity_id}-session-1", activity_id, tool, chosen["architect"][1], str(uuid.uuid4()) if tool == "claude_code" else None, now),
                )
                self._say(tx, project_id, activity_id, f"Architecture started from registration version {details['package']['registration_version']} (candidate {details['package']['candidate_id']}): "
                          f"architect {tool} {chosen['architect'][1]}, reviewer {chosen['reviewer'][0]} {chosen['reviewer'][1]}, source {registration['repository']} at {registration['source_commit'][:12]}. "
                          f"{len(details['outcomes'])} confirmed outcome records were mapped as inputs.")

            self.definitions.start_activity(transaction, "architecture_loop", activity_id, creator)
            return OperationResult(
                data={"activity_id": activity_id, "project_id": project_id, "duplicate": False, "source_commit": details["active"]["source_commit"]},
                status="accepted", project_id=project_id, activity_id=activity_id,
            )

        return PreparedOperation(entity_id, "architecture.started", {"project_id": project_id}, apply)

    def _duplicate(self, entity_id: str, project_id: str, activity_id: str) -> PreparedOperation:
        def apply(transaction: Transaction, next_version: int) -> OperationResult:
            return OperationResult(data={"activity_id": activity_id, "duplicate": True, "message": "an architecture activity is already unfinished for this project"}, project_id=project_id, activity_id=activity_id)
        return PreparedOperation(entity_id, "architecture.duplicate", {"activity_id": activity_id}, apply)

    def _check_route(self, role: str, tool: str, model: str) -> None:
        if self.runs is None:
            raise ValueError("no agent tools are configured for the architecture loop")
        try:
            self.runs.route_resolver("architect" if role == "architect" else "fidelity_reviewer", tool, model)
        except Exception as error:  # noqa: BLE001 - any refusal to resolve the route means it cannot be launched
            raise ValueError(f"{role} selection {tool}/{model} cannot be used: {error}") from error

    def _open_activity(self, project_id: str, tx: Transaction | None = None) -> str | None:
        sql = "SELECT activity_id FROM service_architectures WHERE project_id = ? AND state != 'cancelled' ORDER BY created_at DESC LIMIT 1"
        row = self._row(tx, sql, (project_id,)) if tx is not None else self._read(sql, (project_id,))
        return None if row is None else str(row["activity_id"])

    # --------------------------------------------------------- answers, cancel, retry

    @property
    def recipients(self) -> dict[str, Callable[[DeliveredAnswer], None]]:
        return {"owner": self.receive_answer, "project_architect": self.receive_answer}

    def receive_answer(self, answer: DeliveredAnswer) -> None:
        with self.database.transaction() as tx:
            row = self._row(tx, "SELECT * FROM service_architectures WHERE activity_id = ?", (answer.activity_id,))
            if row is None:
                return
            pending = json.loads(row["pending_json"] or "{}")
            info = pending.get("questions", {}).get(answer.question_id)
            if info is None or info.get("answered"):
                return  # a replayed delivery: already applied
            info["answered"] = answer.answer_id
            question = self._row(tx, "SELECT subject, prompt FROM service_questions WHERE question_id = ?", (answer.question_id,))
            if row["state"] in {"cancelling", "cancelled"}:
                tx.execute("UPDATE service_architectures SET pending_json = ? WHERE activity_id = ?", (canonical_json(pending), answer.activity_id))
                self._resolve_question(tx, answer.question_id)
                return
            version = int(row["decision_version"]) + 1
            number = int(tx.execute("SELECT COUNT(*) FROM service_architecture_decisions WHERE activity_id = ?", (answer.activity_id,)).fetchone()[0]) + 1
            tx.execute(
                "INSERT INTO service_architecture_decisions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (f"{answer.activity_id}-d{number}", answer.activity_id, str(question["subject"]), answer.question_id, str(question["prompt"]), answer.text, answer.choice_id,
                 f"Owner answered: {answer.text}", version, _now()),
            )
            remaining = [q for q, i in pending.get("questions", {}).items() if not i.get("answered")]
            if remaining:
                tx.execute("UPDATE service_architectures SET pending_json = ?, decision_version = ? WHERE activity_id = ?", (canonical_json(pending), version, answer.activity_id))
            else:
                tx.execute("UPDATE service_architectures SET state = 'architect', pending_json = ?, decision_version = ? WHERE activity_id = ?", (canonical_json({**pending, "resume_after_answers": True}), version, answer.activity_id))
                self._activity(tx, answer.activity_id, "investigating", "Answers recorded; the architect resumes its session")
            self._resolve_question(tx, answer.question_id)

    def prepare_cancel(self, request: RequestLike) -> PreparedOperation:
        if request.project_id is None or request.activity_id is None or request.expected_version is None:
            raise ValueError("architecture.cancel needs project, activity and the displayed activity version")
        reason = dict(request.payload).get("reason")
        if set(request.payload) != {"reason"} or not isinstance(reason, str) or not reason.strip():
            raise ValueError("architecture.cancel needs a plain reason")
        activity_id = request.activity_id

        def apply(transaction: Transaction, next_version: int) -> OperationResult:
            row = self._row(transaction, "SELECT * FROM service_architectures WHERE activity_id = ? AND project_id = ?", (activity_id, request.project_id))
            if row is None:
                raise RequestRejection(404, "architecture_not_found", "the architecture activity was not found", fields={"activity_id": activity_id})
            current = self._row(transaction, "SELECT version FROM entity_versions WHERE entity_id = ?", (activity_id,))
            if current is not None and int(current["version"]) != request.expected_version:
                raise RequestRejection(409, "stale_version", "the activity changed since it was displayed", fields={"activity_version": int(current["version"])})
            if row["state"] in {"cancelling", "cancelled"}:
                raise RequestRejection(409, "architecture_ended", "the architecture activity has ended or is already being cancelled", fields={"state": row["state"]})
            pending = json.loads(row["pending_json"] or "{}")
            pending["cancel_request_id"] = request.request_id
            pending["cancel_reason"] = reason.strip()[:300]
            transaction.execute("UPDATE service_architectures SET state = 'cancelling', cancel_requested = 1, pending_json = ? WHERE activity_id = ?", (canonical_json(pending), activity_id))
            self._activity(transaction, activity_id, "cancelling", "Stopping: waiting for the agent run and any external write to be resolved", (), version=next_version)
            self._say(transaction, row["project_id"], activity_id, f"Cancellation requested ({reason.strip()[:200]}). Stopping any running agent before the activity ends; saved work is kept.")
            return OperationResult(data={"activity_id": activity_id, "message": "cancellation accepted; the activity ends once its work is confirmed stopped"}, status="accepted", project_id=row["project_id"], activity_id=activity_id)

        return PreparedOperation(activity_id, "architecture.cancel_requested", {"activity_id": activity_id}, apply)

    def prepare_retry(self, request: RequestLike) -> PreparedOperation:
        if request.project_id is None or request.activity_id is None or request.expected_version is None:
            raise ValueError("architecture.retry needs project, activity and the displayed activity version")
        payload = dict(request.payload)
        if set(payload) != {"target", "operation_id", "assignment_id", "intervention"}:
            raise ValueError("architecture.retry payload must be target, operation_id, assignment_id and intervention")
        intervention = payload["intervention"]
        if not isinstance(intervention, str) or not intervention.strip():
            raise ValueError("architecture.retry needs a nonempty intervention describing what changed")
        if payload["target"] not in {"agent", "publication"} or (payload["target"] == "agent") != (payload["operation_id"] is None) or (payload["target"] == "publication") != (payload["assignment_id"] is None):
            raise ValueError("architecture.retry targets an agent with assignment_id or a publication with operation_id, the other null")
        activity_id = request.activity_id

        def apply(transaction: Transaction, next_version: int) -> OperationResult:
            row = self._row(transaction, "SELECT * FROM service_architectures WHERE activity_id = ? AND project_id = ?", (activity_id, request.project_id))
            if row is None:
                raise RequestRejection(404, "architecture_not_found", "the architecture activity was not found", fields={"activity_id": activity_id})
            pending = json.loads(row["pending_json"] or "{}")
            paused = pending.get("paused")
            if row["state"] != "paused" or not isinstance(paused, dict):
                raise RequestRejection(409, "not_technically_paused", "the architecture activity is not paused by a technical failure", fields={"state": row["state"]})
            if payload["target"] == "agent":
                if paused["kind"] != "agent" or payload["assignment_id"] != paused["assignment_id"]:
                    raise RequestRejection(409, "stale_retry", "the assignment named is not the current failed assignment", fields={"paused": paused})
                if self.runs is None or self.runs.view(paused["failed_run_id"]).state in {"reserved", "running", "stopping", "blocked"}:
                    raise RequestRejection(409, "run_not_ended", "the earlier run is not confirmed ended, so it cannot be replaced", fields={"run_id": paused["failed_run_id"]})
                pending["retry"] = {"kind": "agent", "request_id": request.request_id, "intervention": intervention.strip()[:500]}
                label = "the agent run"
            else:
                if paused["kind"] != "publication" or payload["operation_id"] != paused["operation_id"]:
                    raise RequestRejection(409, "stale_retry", "the operation named is not the current paused publication", fields={"paused": paused})
                transaction.execute("UPDATE service_architecture_publications SET state = 'prepared' WHERE operation_id = ? AND state IN ('paused', 'writing', 'prepared')", (paused["operation_id"],))
                pending["retry"] = {"kind": "publication", "request_id": request.request_id, "intervention": intervention.strip()[:500]}
                label = "the publication"
            pending.pop("paused", None)
            transaction.execute("UPDATE service_architectures SET state = ?, pending_json = ?, note = NULL WHERE activity_id = ?", (paused["from"], canonical_json(pending), activity_id))
            self._activity(transaction, activity_id, "investigating" if paused["from"] == "architect" else "publishing", f"Retry accepted; {label} is being resumed (intervention: {intervention.strip()[:200]})", (), version=next_version)
            self._say(transaction, row["project_id"], activity_id, f"Retry accepted for {label}. Intervention recorded: {intervention.strip()[:300]}. The automatic recovery budget is unchanged.")
            return OperationResult(data={"activity_id": activity_id, "message": f"retry accepted; {label} resumes from its last verified step"}, status="accepted", project_id=row["project_id"], activity_id=activity_id)

        return PreparedOperation(activity_id, "architecture.retry_requested", {"activity_id": activity_id}, apply)

    # ----------------------------------------------------------------- worker

    def tick(self) -> None:
        """Deliver saved answers, then advance every architecture activity that can move."""
        try:
            self.questions.deliver_pending()
        except RecipientDeliveryInterrupted:
            log.warning("an answer delivery was interrupted and will be retried", exc_info=True)
        with self.database.read_connection() as connection:
            ids = [str(r[0]) for r in connection.execute(
                f"SELECT activity_id FROM service_architectures WHERE state IN ({','.join('?' for _ in _WORKING_STATES)}) ORDER BY created_at", _WORKING_STATES)]
        for activity_id in ids:
            lock = self._lock(activity_id)
            if not lock.acquire(blocking=False):
                continue
            try:
                self.advance(activity_id)
            except Exception as error:  # noqa: BLE001 - one activity's failure must not stop the others
                log.exception("architecture step failed for %s", activity_id)
                self._pause_on_error(activity_id, error)
            finally:
                lock.release()

    def _lock(self, activity_id: str) -> threading.Lock:
        with self._guard:
            return self._locks.setdefault(activity_id, threading.Lock())

    def advance(self, activity_id: str) -> None:
        row = self._read("SELECT * FROM service_architectures WHERE activity_id = ?", (activity_id,))
        if row is None:
            return
        if row["state"] == "cancelling":
            self._advance_cancel(row)
        elif row["state"] == "architect":
            self._advance_agent(row)
        elif row["state"] == "publishing":
            self._advance_publish(row)

    def _pause_on_error(self, activity_id: str, error: Exception) -> None:
        transient = isinstance(error, DestinationError) and (
            error.code == "github_unreachable" or (isinstance(error.fields.get("status"), int) and error.fields["status"] >= 500)
        )
        if transient:
            return
        reason = f"{getattr(error, 'code', type(error).__name__)}: {error}"
        with self.database.transaction() as tx:
            row = self._row(tx, "SELECT state FROM service_architectures WHERE activity_id = ?", (activity_id,))
            if row is None or row["state"] in {"cancelled", "cancelling", "paused", "saved"}:
                return
            self._pause_in(tx, activity_id, reason)

    # -- the architect and its session

    def _profile_of(self, row: Mapping[str, Any]) -> RepositoryProfile:
        return self.profiles[json.loads(row["profile_json"])["profile"]]

    def _session(self, activity_id: str) -> dict[str, Any]:
        session = self._read("SELECT * FROM service_architecture_sessions WHERE activity_id = ? AND state = 'active' ORDER BY created_at DESC, rowid DESC LIMIT 1", (activity_id,))
        assert session is not None
        return session

    def _advance_agent(self, row: Mapping[str, Any]) -> None:
        if self.runs is None:
            raise AgentRunError("agents_unavailable", "no agent tools are configured")
        activity_id = row["activity_id"]
        pending = json.loads(row["pending_json"] or "{}")
        current = pending.get("architect_run")
        retry = pending.get("retry")
        if retry and retry.get("kind") == "agent" and current is not None:
            kept = {k: v for k, v in pending.items() if k not in {"retry", "paused"}}
            self._start_agent(row, {**kept, "architect_run": None}, recovery_note="", kind="manual", intervention=retry["intervention"])
            return
        if current is None:
            self._start_agent(row, pending)
            return
        view = self.runs.poll(current["run_id"])
        if view.state in {"reserved", "running", "stopping"}:
            return
        self._remember_conversation(activity_id, current["run_id"])
        assignment = self.runs.assignment_state(current["assignment_id"])
        if view.state == "completed":
            if assignment["state"] == "waiting_for_answers":
                self._architect_questions(row, current)
            else:
                self._accept_architect(row, current)
            return
        if assignment["state"] == "needs_recovery":
            self._recover_agent(row, current, pending, view.failure_code or "technical_failure")
            return
        if view.state == "cancelled":
            return
        reason = f"architect run {view.state}" + (f" ({view.failure_code})" if view.failure_code else "") + (f": {view.terminal_reason}" if view.terminal_reason else "")
        self._pause(row, reason)

    def _remember_conversation(self, activity_id: str, run_id: str) -> None:
        """Record the tool's own conversation id so the next run resumes exactly that conversation."""
        assert self.runs is not None
        session = self._session(activity_id)
        provider = self.runs.run_evidence(run_id).get("session_id")
        if not provider and session["assigned_provider_id"]:
            # A run that ended before reporting still started the conversation the service named if its history was saved.
            history = self.state_dir / "sessions" / session["session_id"] / "history"
            if history.is_dir() and any(history.rglob(f"{session['assigned_provider_id']}.jsonl")):
                provider = session["assigned_provider_id"]
        if not provider:
            return
        with self.database.transaction() as tx:
            tx.execute("UPDATE service_architecture_sessions SET provider_session_id = ? WHERE session_id = ? AND provider_session_id IS NULL", (provider, session["session_id"]))

    def _session_use(self, row: Mapping[str, Any]) -> tuple[SessionUse, dict[str, Any], str | None]:
        """The session for the next run, replacing an unavailable conversation with a linked one."""
        session = self._session(row["activity_id"])
        state_dir = self.state_dir / "sessions" / session["session_id"]
        note = None
        if session["provider_session_id"] is not None and not (state_dir / "history").is_dir():
            session = self._replace_session(row, session, "the saved conversation is unavailable")
            state_dir = self.state_dir / "sessions" / session["session_id"]
            note = _REPLACEMENT
        provider = session["provider_session_id"]
        use = SessionUse(session["session_id"], state_dir, provider, session["assigned_provider_id"] if provider is None else None)
        return use, session, note

    def _replace_session(self, row: Mapping[str, Any], session: Mapping[str, Any], reason: str) -> dict[str, Any]:
        number = int(session["session_id"].rsplit("-", 1)[1]) + 1
        new_id = f"{row['activity_id']}-session-{number}"
        with self.database.transaction() as tx:
            tx.execute("UPDATE service_architecture_sessions SET state = 'lost', note = ? WHERE session_id = ?", (reason, session["session_id"]))
            tx.execute(
                "INSERT INTO service_architecture_sessions(session_id, activity_id, role, tool, model, assigned_provider_id, prior_session_id, state, created_at) VALUES (?, ?, 'architect', ?, ?, ?, ?, 'active', ?)",
                (new_id, row["activity_id"], session["tool"], session["model"], str(uuid.uuid4()) if session["tool"] == "claude_code" else None, session["session_id"], _now()),
            )
            self._say(tx, row["project_id"], row["activity_id"], f"The architect's conversation was unavailable ({reason}); a replacement session {new_id} with the same role and model continues from the saved records.")
        return self._session(row["activity_id"])

    def _start_agent(self, row: Mapping[str, Any], pending: dict[str, Any], recovery_note: str | None = None, kind: str | None = None, intervention: str = "") -> None:
        assert self.runs is not None
        activity_id, project_id = row["activity_id"], row["project_id"]
        terms = self.definitions.assignment_terms(activity_id, "architect")
        new_pass = recovery_note is None
        pass_number = int(row["pass_number"]) + (1 if new_pass else 0)
        assignment_id = f"{activity_id}-arch-{pass_number}"
        tool, model = row["architect_tool"], row["architect_model"]
        destination = self._destination(self._profile_of(row))
        mirror = self.state_dir / "sources" / f"{project_id}.git"
        destination.fetch_source(row["repository"], row["source_commit"], mirror)
        session, session_row, replacement_note = self._session_use(row)
        outcomes = json.loads(row["outcome_refs_json"])["outcomes"]
        inputs = self._inputs(row, outcomes, destination, pending)
        decision_version = f"d{row['decision_version']}"
        limits = {"run_timeout_seconds": terms.duration_seconds}
        note = "" if not recovery_note else f" The previous run's output was rejected: {recovery_note}. Fix exactly that."
        resuming = session.provider_session_id is not None and (pending.get("resume_after_answers") or bool(recovery_note) or kind == "manual")
        continuation = replacement_note or (_CONTINUATION if resuming else "")
        milestones = records_module.milestone_ids(outcomes)
        task = _TASK.format(commit=row["source_commit"], milestones=", ".join(milestones), continuation=continuation) + note

        def build(run_id: str) -> RunBuild:
            assignment = AgentAssignment(
                project_id=project_id, activity_id=activity_id, assignment_id=assignment_id, run_id=run_id,
                parent_assignment_id=None, role="project_architect",
                role_responsibilities=("Investigate the existing code for the confirmed outcomes and save project structure and specialist guidance; never invent requirements.",),
                task=task, source_commit=row["source_commit"], decision_version=decision_version,
                instructions={
                    "task_kind": "investigate", "session_id": session.session_id, "document_paths": [row["overview_path"]],
                    "outcome_ids": [o["id"] for o in outcomes], "recorded_decisions": ["input/decisions.json"], "answers": ["input/answers.json"],
                    "output_rules": records_module.OUTPUT_RULES, "replacement_session": replacement_note is not None,
                },
                permitted_actions=("read_source", "write_output"), writable_locations=("output", "scratch"), limits=limits,
                clarification_conditions=("Information affecting intended outcomes, scope or Owner-reserved decisions is missing or conflicting.",),
                response_schema=RESPONSE_SCHEMA, contract="architecture",
            )
            return RunBuild(assignment, mirror, inputs, session)

        if not self._assignment_exists(assignment_id):
            self.runs.create_assignment_from_terms(terms, assignment_id, project_id, activity_id, tool, model)
        run_id = f"{assignment_id}-run{self.runs.run_count(assignment_id) + 1}"
        kind = kind or ("initial" if recovery_note is None else "recovery")
        before = self.runs.run_count(assignment_id)
        try:
            self.runs.start_run(assignment_id, run_id, kind, build, intervention=intervention)
        except Exception:
            if self.runs.run_count(assignment_id) > before:
                with self.database.transaction() as tx:
                    pending["architect_run"] = {"assignment_id": assignment_id, "run_id": run_id}
                    tx.execute("UPDATE service_architectures SET pending_json = ? WHERE activity_id = ?", (canonical_json(pending), activity_id))
            raise
        pending["architect_run"] = {"assignment_id": assignment_id, "run_id": run_id}
        pending.pop("resume_after_answers", None)
        with self.database.transaction() as tx:
            tx.execute("UPDATE service_architectures SET pass_number = ?, pending_json = ? WHERE activity_id = ?", (pass_number, canonical_json(pending), activity_id))
            self._activity(tx, activity_id, "investigating", f"Project architect ({tool} {model}) is working in session {session.session_id}" + (" (resumed)" if session.provider_session_id else ""))
            self._say(tx, project_id, activity_id, f"Project architect started: {tool} {model}, assignment {assignment_id}, run {run_id}, session {session.session_id}"
                      + (f", resuming conversation {session.provider_session_id}" if session.provider_session_id else ", new conversation") + ".")

    def _assignment_exists(self, assignment_id: str) -> bool:
        assert self.runs is not None
        try:
            self.runs.assignment_state(assignment_id)
            return True
        except AgentRunError:
            return False

    def _inputs(self, row: Mapping[str, Any], outcomes: list[dict[str, Any]], destination: GitHubDestination, pending: Mapping[str, Any]) -> dict[str, bytes]:
        package = json.loads(row["registration_json"])
        summary = {
            "project_id": row["project_id"], "activity_id": row["activity_id"], "registration_ref": package,
            "scope": json.loads(row["scope_json"]),
            "source": {"repository": row["repository"], "ref": row["source_ref"], "commit": row["source_commit"], "overview_path": row["overview_path"]},
            "note": "The code baseline is the source commit; the registration is the confirmed statement of outcomes.",
        }
        decisions = self._decisions(row["activity_id"])
        inputs: dict[str, bytes] = {
            "registration-summary.json": records_module.encode(summary),
            "outcomes.json": records_module.encode({"outcomes": outcomes}),
            "decisions.json": records_module.encode({"decisions": decisions}),
            "answers.json": records_module.encode({"answers": [{"question_id": d["question_id"], "subject": d["subject"], "question": d["question_text"], "answer": d["answer_text"]} for d in decisions]}),
        }
        for outcome in outcomes:
            data = destination.read_file(package["repository"], package["commit"], outcome["path"])
            if data is None or records_module.sha256(data) != outcome["sha256"]:
                raise FoundationError(f"the confirmed record {outcome['path']} no longer matches its recorded hash")
            relative = outcome["path"].split("/candidates/", 1)[1].split("/", 1)[1]
            inputs[f"registration/{relative}"] = data
        return inputs

    def _recover_agent(self, row: Mapping[str, Any], current: Mapping[str, str], pending: dict[str, Any], code: str) -> None:
        assert self.runs is not None
        detail = self.runs.view(current["run_id"]).terminal_reason or code
        pending.pop("architect_run", None)
        self._start_agent(row, {**pending, "architect_run": None}, recovery_note=detail)

    def _architect_questions(self, row: Mapping[str, Any], current: Mapping[str, str]) -> None:
        assert self.runs is not None
        response = self.runs.response(current["run_id"]) or {}
        requests = _questions(_question_shape(response.get("questions", [])))
        findings = _findings(_finding_shape(response.get("findings", [])))
        assignment = AgentAssignment(
            project_id=row["project_id"], activity_id=row["activity_id"], assignment_id=current["assignment_id"], run_id=current["run_id"], parent_assignment_id=None,
            role="project_architect", role_responsibilities=("x",), task="x", source_commit=row["source_commit"], decision_version=f"d{row['decision_version']}",
            instructions={}, permitted_actions=("read_source",), writable_locations=("output", "scratch"), limits={}, clarification_conditions=("x",), response_schema={},
        )
        with self.database.transaction() as tx:
            fresh = self._row(tx, "SELECT * FROM service_architectures WHERE activity_id = ?", (row["activity_id"],))
            pending = json.loads(fresh["pending_json"] or "{}")
            pending.pop("architect_run", None)
            self._save_findings(tx, fresh, response.get("findings", []), f"{row['activity_id']}-arch-{fresh['pass_number']}")
            for request in requests:
                seq = int(fresh["question_seq"]) + 1
                fresh = {**fresh, "question_seq": seq}
                tx.execute("UPDATE service_architectures SET question_seq = ? WHERE activity_id = ?", (seq, row["activity_id"]))
                question_id = f"{row['activity_id']}-q{seq}"
                self.questions.publish(tx, request.to_linked_question(question_id=question_id, assignment=assignment, requester="project_architect"))
                pending.setdefault("questions", {})[question_id] = {"kind": "architect_question"}
            tx.execute("UPDATE service_architectures SET state = 'architect_waiting', pending_json = ? WHERE activity_id = ?", (canonical_json(pending), row["activity_id"]))
            self._activity(tx, row["activity_id"], "waiting", f"Waiting for your answer: the architect asked {len(requests)} question(s)")
            self._say(tx, row["project_id"], row["activity_id"], f"The architect needs {len(requests)} answer(s) before continuing; its session is kept.")

    def _accept_architect(self, row: Mapping[str, Any], current: Mapping[str, str]) -> None:
        assert self.runs is not None
        response = self.runs.response(current["run_id"]) or {}
        artifacts = self.runs.artifacts(current["run_id"])
        try:
            files = {path[len("output/"):]: Path(stored).read_bytes() for field, (path, _, stored) in artifacts.items() if field.startswith("output:")}
            checked = self._validate_outputs(row, response, files)
        except (KeyError, OSError, ValueError, FoundationError) as error:
            self.runs.reject_result(current["run_id"], "malformed_output", f"architecture output invalid: {error}")
            return
        pass_number = int(row["pass_number"])
        with self.database.transaction() as tx:
            fresh = self._row(tx, "SELECT * FROM service_architectures WHERE activity_id = ?", (row["activity_id"],))
            pending = json.loads(fresh["pending_json"] or "{}")
            pending.pop("architect_run", None)
            identities = self._save_findings(tx, fresh, response.get("findings", []), f"{row['activity_id']}-arch-{pass_number}")
            checked["finding_identities"] = {k: list(v) for k, v in identities.items()}
            for path, data in files.items():
                tx.execute("INSERT OR REPLACE INTO service_architecture_outputs VALUES (?, ?, ?, ?, ?)", (row["activity_id"], pass_number, path, records_module.sha256(data), data))
            pending["accepted_pass"] = pass_number
            tx.execute("UPDATE service_architectures SET state = 'publishing', foundation_json = ?, pending_json = ? WHERE activity_id = ?", (canonical_json(checked), canonical_json(pending), row["activity_id"]))
            self._activity(tx, row["activity_id"], "publishing", "Investigation validated; publishing structure, specialist guidance and records to GitHub")
            self._say(tx, row["project_id"], row["activity_id"], f"Architect investigation complete: {response.get('summary', '')} ({len(response.get('findings', []))} finding(s)). Validated; publishing next.")

    def _source_paths(self, row: Mapping[str, Any]) -> tuple[set[str], set[str]]:
        key = (row["project_id"], row["source_commit"])
        if key not in self._trees:
            mirror = self.state_dir / "sources" / f"{row['project_id']}.git"
            listing = subprocess.run(["git", "-C", str(mirror), "ls-tree", "-r", "--name-only", row["source_commit"]], capture_output=True, text=True, check=True).stdout.splitlines()
            files = set(listing)
            directories = {""}
            for path in files:
                parts = path.split("/")[:-1]
                directories.update("/".join(parts[:i]) for i in range(1, len(parts) + 1))
            self._trees[key] = (files, directories)
        return self._trees[key]

    def _validate_outputs(self, row: Mapping[str, Any], response: Mapping[str, Any], files: Mapping[str, bytes]) -> dict[str, Any]:
        source_files, source_dirs = self._source_paths(row)
        commit = row["source_commit"]
        outcomes = json.loads(row["outcome_refs_json"])["outcomes"]
        findings = list(_findings(_finding_shape(response.get("findings", []))))
        raw_findings = response.get("findings", [])
        records_module.validate_findings(raw_findings, commit, lambda p: p in source_files or p in source_dirs)
        try:
            investigation = records_module.validate_investigation(
                json.loads(files["investigation.json"]), {str(f["local_key"]) for f in findings}, {o["id"] for o in outcomes},
                set(records_module.milestone_ids(outcomes)), commit, lambda p: p in source_files or p in source_dirs,
            )
            structure = records_module.validate_structure(json.loads(files["project-structure.json"]), commit, lambda p: p.strip("/") in source_dirs)
        except KeyError as error:
            raise FoundationError(f"{error.args[0]} is missing") from error
        except json.JSONDecodeError as error:
            raise FoundationError(f"an output file is not valid JSON: {error}") from error
        specialists = records_module.validate_specialist_files(structure, files)
        return {"investigation": investigation, "structure": structure, "specialists": specialists, "findings": raw_findings}

    def _save_findings(self, tx: Transaction, row: Mapping[str, Any], findings: list[Mapping[str, Any]], marker: str) -> dict[str, tuple[str, int]]:
        """Bind each response-local key to one stable identity; a repeat keeps it and raises the version only when content changes."""
        identities: dict[str, tuple[str, int]] = {}
        seq = int(row["finding_seq"])
        for finding in findings:
            digest = records_module.sha256(canonical_json(finding).encode())
            known = self._row(tx, "SELECT * FROM service_architecture_findings WHERE activity_id = ? AND local_key = ?", (row["activity_id"], finding["local_key"]))
            detail = (f"{finding['explanation']} Impact: {finding['impact']} Requested correction: {finding['requested_correction']} "
                      + " ".join(f"[{s['path']}:{s['locator']}]" for s in finding["source_refs"]) + (f" Missing information: {finding['missing_information']}" if finding.get("missing_information") else ""))
            if known is None:
                seq += 1
                finding_id, version = f"finding-{seq}", 1
                tx.execute("INSERT INTO service_architecture_findings VALUES (?, ?, ?, ?, ?)", (row["activity_id"], finding["local_key"], finding_id, version, digest))
                self.records.create_finding(tx, FindingRecord(f"{row['activity_id']}-{finding_id}", row["project_id"], row["activity_id"], f"Architect: {finding['subject']}", detail, finding["severity"], 1))
            else:
                finding_id, version = known["finding_id"], int(known["version"])
                if known["content_sha256"] != digest:
                    version += 1
                    tx.execute("UPDATE service_architecture_findings SET version = ?, content_sha256 = ? WHERE activity_id = ? AND local_key = ?", (version, digest, row["activity_id"], finding["local_key"]))
                    current = self._row(tx, "SELECT version FROM service_findings WHERE finding_id = ?", (f"{row['activity_id']}-{finding_id}",))
                    if current is not None:
                        self.records.update_finding(tx, FindingRecord(f"{row['activity_id']}-{finding_id}", row["project_id"], row["activity_id"], f"Architect: {finding['subject']}", detail, finding["severity"], int(current["version"]) + 1), expected_record_version=int(current["version"]))
            identities[finding["local_key"]] = (finding_id, version)
        tx.execute("UPDATE service_architectures SET finding_seq = ? WHERE activity_id = ?", (seq, row["activity_id"]))
        return identities

    # -- publication

    def _advance_publish(self, row: Mapping[str, Any]) -> None:
        activity_id = row["activity_id"]
        destination = self._destination(self._profile_of(row))
        pending = json.loads(row["pending_json"] or "{}")
        retry = pending.get("retry")
        if retry and retry.get("kind") == "publication":
            with self.database.transaction() as tx:
                fresh = self._row(tx, "SELECT pending_json FROM service_architectures WHERE activity_id = ?", (activity_id,))
                kept = json.loads(fresh["pending_json"] or "{}")
                kept.pop("retry", None)
                tx.execute("UPDATE service_architectures SET pending_json = ? WHERE activity_id = ?", (canonical_json(kept), activity_id))
        checked = json.loads(row["foundation_json"])
        pass_number = int(pending["accepted_pass"])
        outputs = {r["path"]: bytes(r["content"]) for r in self._rows("SELECT path, content FROM service_architecture_outputs WHERE activity_id = ? AND pass_number = ?", (activity_id, pass_number))}
        specialist_files = {p: d for p, d in outputs.items() if p.startswith("specialists/")}
        version = int(row["architecture_version"])
        specialists_commit = self._publish_stage(
            row, destination, f"{activity_id}-specialists-{pass_number}", "specialists",
            {records_module.repo_path(p): d for p, d in specialist_files.items()}, f"Publish architect specialist guidance (architecture version {version})",
        )
        package = json.loads(row["registration_json"])
        outcomes = json.loads(row["outcome_refs_json"])["outcomes"]
        identities = {k: (v[0], v[1]) for k, v in checked["finding_identities"].items()}
        owner_decisions = [{"subject": d["subject"], "question_id": d["question_id"], "answer": d["answer_text"], "rationale": d["rationale"]} for d in self._decisions(activity_id)]
        files, manifest, manifest_path = records_module.build_foundation_set(
            project_id=row["project_id"], activity_id=activity_id, version=version, registration_ref=package, source_commit=row["source_commit"],
            decision_version=int(row["decision_version"]), outcomes=outcomes, findings=[_normalize_finding(f) for f in checked["findings"]], finding_identities=identities,
            investigation=checked["investigation"], structure=checked["structure"], specialists=checked["specialists"], specialist_files=specialist_files,
            specialist_commit=specialists_commit, owner_decisions=owner_decisions, owner_id=self.owner_id,
        )
        self._check_schema(files, manifest_path)
        foundations_commit = self._publish_stage(row, destination, f"{activity_id}-foundations-{pass_number}", "foundations", files, f"Publish architecture foundations (version {version})")
        manifest_bytes = files[manifest_path]
        reference = records_module.set_ref(foundations_commit, manifest, manifest_path, manifest_bytes)
        index_path = f"{records_module.ROOT}/index.json"
        previous_raw = destination.read_file(row["repository"], foundations_commit, index_path)
        previous = json.loads(previous_raw) if previous_raw else None
        index = records_module.discovery_index(row["project_id"], previous, version, foundations_commit, manifest_path, reference["manifest_sha256"], manifest["reviewed_content_hash"])
        index_commit = self._publish_stage(row, destination, f"{activity_id}-index-{pass_number}", "index", {index_path: records_module.encode(index)}, f"Update the architecture discovery index (version {version})", frozenset({index_path}))
        final = {**reference, "index_commit": index_commit, "specialists_commit": specialists_commit, "repository": row["repository"], "branch": row["publication_branch"]}
        with self.database.transaction() as tx:
            tx.execute("UPDATE service_architectures SET state = 'saved', foundations_ref_json = ?, note = NULL WHERE activity_id = ?", (canonical_json(final), activity_id))
            self._activity(tx, activity_id, "foundations_saved",
                           f"Foundations saved: architecture version {version} at {foundations_commit[:12]} ({len(checked['findings'])} findings, {len(checked['specialists'])} specialists). The work breakdown is the next stage.",
                           (ActivityAction(f"{activity_id}-cancel", "Cancel architecture", "action"),))
            self._say(tx, row["project_id"], activity_id, f"Foundations saved and published to {row['repository']} branch {row['publication_branch']}: manifest {manifest_path} at {foundations_commit[:12]}, "
                      f"specialist guidance at {specialists_commit[:12]}, discovery index at {index_commit[:12]}. No specialist was launched and no source was changed.")
            self._emit(tx, row["project_id"], activity_id, "architecture.foundations_saved", {"activity_id": activity_id, "working_ref": reference})

    def _check_schema(self, files: Mapping[str, bytes], manifest_path: str) -> None:
        if self.schema is None:
            return
        import jsonschema

        base = manifest_path.rsplit("/", 1)[0]
        for name, definition in (("investigation.json", "investigation"), ("decisions.json", "decisions"), ("project-structure.json", "projectStructure"), ("manifest.json", "manifest")):
            document = json.loads(files[f"{base}/{name}"])
            schema = {"$ref": f"#/$defs/{definition}", "$defs": self.schema["$defs"]}
            try:
                jsonschema.Draft202012Validator(schema).validate(document)
            except jsonschema.ValidationError as error:
                raise FoundationError(f"the saved {name} does not satisfy the architecture-loop schema: {error.message[:200]} at {'/'.join(str(p) for p in error.absolute_path)}") from error

    def _publish_stage(self, row: Mapping[str, Any], destination: GitHubDestination, operation_id: str, kind: str, files: Mapping[str, bytes], message: str, replaceable: frozenset[str] = frozenset()) -> str:
        """Write one journaled commit; return the commit that holds exactly these bytes (an earlier attempt's, if it landed)."""
        op = self._read("SELECT * FROM service_architecture_publications WHERE operation_id = ?", (operation_id,))
        if op is None:
            with self.database.transaction() as tx:
                tx.execute(
                    "INSERT INTO service_architecture_publications(operation_id, activity_id, kind, repository, branch, files_json, state, profile_json) VALUES (?, ?, ?, ?, ?, ?, 'prepared', ?)",
                    (operation_id, row["activity_id"], kind, row["repository"], row["publication_branch"],
                     canonical_json({"files": {p: records_module.sha256(d) for p, d in files.items()}}), row["profile_json"]),
                )
            self._frozen(operation_id, files)
            op = self._read("SELECT * FROM service_architecture_publications WHERE operation_id = ?", (operation_id,))
        assert op is not None
        if op["state"] in {"verified", "applied"}:
            return str(op["commit_sha"])
        frozen = self._frozen(operation_id)
        destination.check_publication_branch(row["repository"], row["publication_branch"])
        with self.database.transaction() as tx:
            tx.execute("UPDATE service_architecture_publications SET state = 'writing' WHERE operation_id = ?", (operation_id,))
        commit = destination.publish(row["repository"], row["publication_branch"], frozen, message, replaceable)
        destination.verify_files(row["repository"], commit, frozen)
        with self.database.transaction() as tx:
            tx.execute("UPDATE service_architecture_publications SET state = 'applied', commit_sha = ? WHERE operation_id = ?", (commit, operation_id))
        return commit

    def _frozen(self, operation_id: str, files: Mapping[str, bytes] | None = None) -> dict[str, bytes]:
        directory = self.state_dir / "frozen" / operation_id
        if files is not None:
            directory.mkdir(parents=True, exist_ok=True)
            for path, data in files.items():
                target = directory / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
            return dict(files)
        return {str(p.relative_to(directory)): p.read_bytes() for p in sorted(directory.rglob("*")) if p.is_file()}

    # -- cancellation

    def _advance_cancel(self, row: Mapping[str, Any]) -> None:
        activity_id = row["activity_id"]
        pending = json.loads(row["pending_json"] or "{}")
        current = pending.get("architect_run")
        if self.runs is not None and current is not None:
            view = self.runs.view(current["run_id"])
            if view.state in {"reserved", "running", "stopping"}:
                view = self.runs.stop(current["run_id"], "architecture_cancelled")
            if view.state in {"reserved", "running", "stopping", "blocked"}:
                with self.database.transaction() as tx:
                    self._activity(tx, activity_id, "cancelling", "Stop unconfirmed: the agent run has not been confirmed stopped; the activity stays open")
                return
        inflight = self._read("SELECT COUNT(*) AS n FROM service_architecture_publications WHERE activity_id = ? AND state IN ('prepared', 'writing')", (activity_id,))
        if inflight and inflight["n"]:
            self._settle_publications(row)
            return
        with self.database.transaction() as tx:
            tx.execute("UPDATE service_architectures SET state = 'cancelled' WHERE activity_id = ?", (activity_id,))
            for question_id in pending.get("questions", {}):
                q = self._row(tx, "SELECT * FROM service_questions WHERE question_id = ?", (question_id,))
                if q is not None and q["status"] in {"awaiting_answer", "clarification_required"}:
                    self.records.update_question(tx, QuestionRecord(question_id, q["project_id"], q["activity_id"], q["subject"], q["prompt"], q["requester"], "cancelled", int(q["version"]) + 1), expected_record_version=int(q["version"]))
                    tx.execute("INSERT INTO entity_versions(entity_id, version) VALUES (?, ?) ON CONFLICT(entity_id) DO UPDATE SET version = excluded.version", (question_id, int(q["version"]) + 1))
            self._activity(tx, activity_id, "cancelled", "Architecture cancelled; saved findings, decisions and any published foundations are retained", (), ended=True)
            self.reservations.release(tx, row["project_id"], activity_id)
            if pending.get("cancel_request_id"):
                tx.execute("UPDATE service_request_results SET status = 'completed' WHERE request_id = ?", (pending["cancel_request_id"],))
            self._say(tx, row["project_id"], activity_id, "Architecture cancelled. Saved work is retained; nothing was started or changed in the source.")
            self._emit(tx, row["project_id"], activity_id, "architecture.cancelled", {"activity_id": activity_id})

    def _settle_publications(self, row: Mapping[str, Any]) -> None:
        """A write that may have landed is reconciled by re-running its byte-exact publication before the activity ends."""
        destination = self._destination(self._profile_of(row))
        for op in self._rows("SELECT * FROM service_architecture_publications WHERE activity_id = ? AND state IN ('prepared', 'writing')", (row["activity_id"],)):
            frozen = self._frozen(op["operation_id"])
            commit = destination.publish(op["repository"], op["branch"], frozen, "Reconcile an interrupted architecture publication", frozenset({f"{records_module.ROOT}/index.json"}))
            destination.verify_files(op["repository"], commit, frozen)
            with self.database.transaction() as tx:
                tx.execute("UPDATE service_architecture_publications SET state = 'applied', commit_sha = ? WHERE operation_id = ?", (commit, op["operation_id"]))

    # -- pause

    def _pause(self, row: Mapping[str, Any], reason: str) -> None:
        with self.database.transaction() as tx:
            self._pause_in(tx, row["activity_id"], reason)

    def _pause_in(self, tx: Transaction, activity_id: str, reason: str) -> None:
        fresh = self._row(tx, "SELECT * FROM service_architectures WHERE activity_id = ?", (activity_id,))
        pending = json.loads(fresh["pending_json"] or "{}")
        pending.pop("retry", None)
        paused = None
        if fresh["state"] == "architect" and pending.get("architect_run") is not None:
            paused = {"kind": "agent", "from": "architect", "assignment_id": pending["architect_run"]["assignment_id"], "failed_run_id": pending["architect_run"]["run_id"]}
        elif fresh["state"] == "publishing":
            op = self._row(tx, "SELECT operation_id FROM service_architecture_publications WHERE activity_id = ? AND state != 'applied' ORDER BY rowid DESC LIMIT 1", (activity_id,))
            if op is not None:
                paused = {"kind": "publication", "from": "publishing", "operation_id": op["operation_id"]}
        if paused is None:
            pending.pop("paused", None)
        else:
            pending["paused"] = paused
        tx.execute("UPDATE service_architectures SET state = 'paused', note = ?, pending_json = ? WHERE activity_id = ?", (reason[:500], canonical_json(pending), activity_id))
        cancel = ActivityAction(f"{activity_id}-cancel", "Cancel architecture", "action")
        actions = (cancel,) if paused is None else (ActivityAction(f"{activity_id}-retry", "Retry publication" if paused["kind"] == "publication" else "Retry activity", "action"), cancel)
        self._activity(tx, activity_id, "paused", f"Paused: {reason[:300]}", actions)
        self._say(tx, fresh["project_id"], activity_id, f"Architecture paused: {reason[:400]}")

    # ----------------------------------------------------------------- records

    def _say(self, tx: Transaction, project_id: str, activity_id: str, text: str) -> None:
        self.records.append_conversation(tx, ConversationRecord(f"architecture-{uuid.uuid4().hex}", project_id, "maestro", "status", text, _now(), activity_id))
        self._emit(tx, project_id, activity_id, "architecture.updated", {"activity_id": activity_id})

    def _activity(self, tx: Transaction, activity_id: str, state: str | None, waiting: str | None, actions: tuple[ActivityAction, ...] | None = None, *, ended: bool = False, version: int | None = None) -> None:
        current = self._row(tx, "SELECT * FROM service_activities WHERE activity_id = ?", (activity_id,))
        assert current is not None
        existing = tuple(ActivityAction(r[0], r[1], r[2]) for r in tx.execute("SELECT action_id, label, kind FROM service_activity_actions WHERE activity_id = ? ORDER BY sequence", (activity_id,)).fetchall())
        record_version = int(current["version"])
        next_version = record_version + 1
        self.records.update_activity(
            tx,
            ActivityRecord(activity_id, current["project_id"], current["kind"], current["subject"], state or current["state"], next_version, waiting,
                           current["started_at"], _now() if ended else current["ended_at"], existing if actions is None else actions),
            expected_record_version=record_version,
        )
        tx.execute("INSERT INTO entity_versions(entity_id, version) VALUES (?, ?) ON CONFLICT(entity_id) DO UPDATE SET version = excluded.version", (activity_id, next_version))

    def _resolve_question(self, tx: Transaction, question_id: str) -> None:
        q = self._row(tx, "SELECT * FROM service_questions WHERE question_id = ?", (question_id,))
        if q is not None and q["status"] == "answer_received":
            self.records.update_question(tx, QuestionRecord(question_id, q["project_id"], q["activity_id"], q["subject"], q["prompt"], q["requester"], "resolved", int(q["version"]) + 1), expected_record_version=int(q["version"]))
            tx.execute("INSERT INTO entity_versions(entity_id, version) VALUES (?, ?) ON CONFLICT(entity_id) DO UPDATE SET version = excluded.version", (question_id, int(q["version"]) + 1))

    @staticmethod
    def _emit(tx: Transaction, project_id: str, activity_id: str, event_type: str, data: Mapping[str, object]) -> None:
        tx.execute(
            "INSERT INTO outbox_events(schema_version, event_id, occurred_at, project_id, activity_id, type, data_json) VALUES (1, ?, ?, ?, ?, ?, ?)",
            (f"architecture-{uuid.uuid4().hex}", _now(), project_id, activity_id, event_type, canonical_json(data)),
        )

    def _decisions(self, activity_id: str) -> list[dict[str, Any]]:
        return self._rows("SELECT * FROM service_architecture_decisions WHERE activity_id = ? ORDER BY rowid", (activity_id,))

    # ------------------------------------------------------------------ reads

    def project_view(self, project_id: str) -> dict[str, Any] | None:
        """The project's current (not cancelled) architecture activity as the CLI shows it; None when it has none. Reading starts nothing."""
        row = self._read("SELECT activity_id FROM service_architectures WHERE project_id = ? AND state != 'cancelled' ORDER BY created_at DESC, rowid DESC LIMIT 1", (project_id,))
        return None if row is None else self.view(str(row["activity_id"]))

    def view(self, activity_id: str) -> dict[str, Any] | None:
        row = self._read("SELECT * FROM service_architectures WHERE activity_id = ?", (activity_id,))
        if row is None:
            return None
        pending = json.loads(row["pending_json"] or "{}")
        version = self._read("SELECT version FROM entity_versions WHERE entity_id = ?", (activity_id,))
        foundations = None if row["foundations_ref_json"] is None else json.loads(row["foundations_ref_json"])
        state = {"architect": "running", "architect_waiting": "waiting_for_answers", "publishing": "publishing", "saved": "running",
                 "paused": "paused", "cancelling": "cancelling", "cancelled": "cancelled"}[row["state"]]
        actions: list[str] = []
        blocking: list[str] = []
        if row["state"] in {"architect", "architect_waiting", "publishing", "saved", "paused"}:
            actions.append("cancel")
        paused = pending.get("paused")
        if row["state"] == "paused" and isinstance(paused, dict):
            actions.append("retry_publication" if paused["kind"] == "publication" else "retry_agent")
        if row["state"] == "saved":
            blocking.append("Foundations are saved; producing the work breakdown is the next stage and has not been built yet.")
        if row["state"] == "paused" and row["note"]:
            blocking.append(str(row["note"]))
        session = self._read("SELECT * FROM service_architecture_sessions WHERE activity_id = ? AND state = 'active' ORDER BY created_at DESC, rowid DESC LIMIT 1", (activity_id,))
        sessions = self._rows("SELECT session_id, tool, model, provider_session_id, prior_session_id, state, note FROM service_architecture_sessions WHERE activity_id = ? ORDER BY rowid", (activity_id,))
        return {
            "project_id": row["project_id"], "activity_id": activity_id, "activity_version": None if version is None else int(version["version"]),
            "state": state, "stage": {"architect": "investigating", "architect_waiting": "waiting_for_answers", "publishing": "publishing", "saved": "foundations_saved",
                                      "paused": "paused", "cancelling": "cancelling", "cancelled": "cancelled"}[row["state"]],
            "registration_ref": json.loads(row["registration_json"]),
            "working_ref": None if foundations is None else {k: foundations[k] for k in ("version", "commit", "manifest_path", "manifest_sha256", "reviewed_content_hash")},
            "confirmed_ref": None, "review_coverage_valid": False, "review_count": 0, "review_limit": self._review_limit(activity_id),
            "available_actions": actions, "blocking_reasons": blocking, "allowances": [], "owner_decisions": [],
            "repository": row["repository"], "source": {"ref": row["source_ref"], "commit": row["source_commit"]}, "publication_branch": row["publication_branch"],
            "roles": {"architect": {"tool": row["architect_tool"], "model_id": row["architect_model"]}, "reviewer": {"tool": row["reviewer_tool"], "model_id": row["reviewer_model"]}},
            "session": None if session is None else {k: session[k] for k in ("session_id", "tool", "model", "provider_session_id", "prior_session_id")},
            "sessions": sessions, "foundations": foundations, "paused": paused, "note": row["note"],
            "outcomes": [{"id": o["id"], "subject": o["subject"]} for o in json.loads(row["outcome_refs_json"])["outcomes"] if o["path"].split("/")[-2] == "milestones"],
            "recovery": self._recovery_view(pending),
        }

    def _review_limit(self, activity_id: str) -> int:
        try:
            return int(self.definitions.policy.resume(activity_id).snapshot.definition["maximum_fidelity_reviews"])
        except Exception:  # noqa: BLE001 - the view must not fail because a definition cannot be read
            return 1

    def _recovery_view(self, pending: Mapping[str, Any]) -> dict[str, Any] | None:
        current = (pending.get("paused") or {}).get("assignment_id") or (pending.get("architect_run") or {}).get("assignment_id")
        if current is None or self.runs is None:
            return None
        try:
            state = self.runs.assignment_state(current)
        except AgentRunError:
            return None
        return {"assignment_id": current, **{k: state.get(k) for k in ("state", "automatic_used", "automatic_limit", "manual_used", "pause_reason", "duration_seconds")}}

    @staticmethod
    def _row(tx: Transaction, sql: str, params: tuple[object, ...] = ()) -> dict[str, Any] | None:
        cursor = tx.execute(sql, params)
        found = cursor.fetchone()
        return None if found is None else {column[0]: value for column, value in zip(cursor.description, found)}

    def _read(self, sql: str, params: tuple[object, ...] = ()) -> dict[str, Any] | None:
        with self.database.read_connection() as connection:
            cursor = connection.execute(sql, params)
            found = cursor.fetchone()
            return None if found is None else {column[0]: value for column, value in zip(cursor.description, found)}

    def _rows(self, sql: str, params: tuple[object, ...] = ()) -> list[dict[str, Any]]:
        with self.database.read_connection() as connection:
            cursor = connection.execute(sql, params)
            names = [c[0] for c in cursor.description]
            return [dict(zip(names, r)) for r in cursor.fetchall()]


def _finding_shape(findings: object) -> object:
    from maestro.agents.architecture_contract import _finding_view
    return _finding_view(findings)


def _question_shape(questions: object) -> object:
    from maestro.agents.architecture_contract import _question_view
    return _question_view(questions)


def _normalize_finding(finding: Mapping[str, Any]) -> dict[str, Any]:
    return {**finding, "missing_information": finding.get("missing_information"), "source_refs": list(finding["source_refs"]), "affected_items": list(finding["affected_items"])}
