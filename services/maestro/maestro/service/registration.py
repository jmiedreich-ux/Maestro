"""Project registration: intake, assessment, review, publication, confirmation and cancellation.

One registration attempt is one activity. Its durable row records every choice
and step, so the step machine (``tick``) can be repeated safely: each state does
one bounded unit of work, saves the result, and moves on. The shared process
definition saved with the activity supplies the review limit, run durations and
recovery limit. Agent runs, questions, findings and GitHub writes all go
through the existing service layers.
"""

from __future__ import annotations

import json
import logging
import re
import threading
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping

from maestro.agents.routes import AgentRouteError
from maestro.agents.transport import AgentAssignment, ArtifactReference, TransportError, _findings, _questions
from maestro.foundation import Database, DomainMigration, Transaction, canonical_json

from .activities import (
    ActivityAction,
    ActivityRecord,
    ActivityRepository,
    ConversationRecord,
    FindingRecord,
    ProjectRecord,
    QuestionRecord,
)
from .agent_runs import AgentRunError, AgentRunService, RunBuild
from .process_definitions import ProcessDefinitions
from .processes import ProcessPolicyError
from .questions import AnswerChoice, DeliveredAnswer, LinkedQuestion, QuestionService, RecipientDeliveryInterrupted
from .registration_github import DestinationError, GitHubDestination, RepositoryProfile, bind_repository
from .registration_package import (
    CandidateError,
    ROOT,
    build_package,
    encode,
    package_reference,
    receipt_and_index,
    sha256,
    validate_assessment,
    validate_candidate,
    validate_package,
)
from .registration_source import SourceError, SourceModel, interpret_scope, validate_sources
from .registry import OperationHandler, OperationResult, PreparedOperation, RequestLike
from .requests import RequestRejection
from .reservations import ProjectReservations, ReservationError

log = logging.getLogger("maestro.registration")

REGISTRATION_MIGRATION = DomainMigration(
    domain="service_registration",
    version=1,
    identity="service-registration-v1",
    statements=(
        """
        CREATE TABLE service_registrations(
            activity_id TEXT PRIMARY KEY REFERENCES service_activities(activity_id) ON DELETE RESTRICT,
            project_id TEXT NOT NULL REFERENCES service_projects(project_id) ON DELETE RESTRICT,
            repository TEXT NOT NULL,
            binding TEXT NOT NULL,
            overview_path TEXT NOT NULL,
            scope_json TEXT NOT NULL,
            source_ref TEXT,
            source_commit TEXT NOT NULL,
            source_provenance TEXT NOT NULL,
            publication_branch TEXT,
            branch_provenance TEXT,
            default_branch TEXT,
            profile_json TEXT NOT NULL,
            architect_tool TEXT, architect_model TEXT,
            reviewer_tool TEXT, reviewer_model TEXT,
            state TEXT NOT NULL,
            pending_json TEXT NOT NULL DEFAULT '{}',
            review_limit INTEGER NOT NULL,
            reviews_used INTEGER NOT NULL DEFAULT 0,
            registration_version INTEGER NOT NULL,
            decision_version INTEGER NOT NULL DEFAULT 1,
            pass_number INTEGER NOT NULL DEFAULT 0,
            question_seq INTEGER NOT NULL DEFAULT 0,
            candidate_id TEXT,
            package_json TEXT,
            confirmation_json TEXT,
            cancel_requested INTEGER NOT NULL DEFAULT 0,
            note TEXT,
            created_at TEXT NOT NULL,
            selected_at TEXT NOT NULL
        )
        """,
        """
        CREATE TABLE service_registration_decisions(
            decision_id TEXT PRIMARY KEY,
            activity_id TEXT NOT NULL REFERENCES service_registrations(activity_id),
            kind TEXT NOT NULL,
            subject TEXT NOT NULL,
            question_id TEXT,
            question_text TEXT,
            answer_text TEXT NOT NULL,
            choice_id TEXT,
            resolution TEXT NOT NULL,
            authority TEXT NOT NULL,
            decision_version INTEGER NOT NULL,
            created_at TEXT NOT NULL
        )
        """,
        """
        CREATE TABLE service_registration_reviews(
            activity_id TEXT NOT NULL REFERENCES service_registrations(activity_id),
            review_round INTEGER NOT NULL,
            assignment_id TEXT NOT NULL,
            run_id TEXT NOT NULL UNIQUE,
            reviewer_identity TEXT NOT NULL,
            outcome TEXT NOT NULL,
            findings_json TEXT NOT NULL,
            candidate_sha256 TEXT NOT NULL,
            assessment_sha256 TEXT NOT NULL,
            review_limit INTEGER NOT NULL,
            PRIMARY KEY(activity_id, review_round)
        )
        """,
        """
        CREATE TABLE service_registration_passes(
            activity_id TEXT NOT NULL REFERENCES service_registrations(activity_id),
            pass_number INTEGER NOT NULL,
            assignment_id TEXT NOT NULL,
            run_id TEXT NOT NULL,
            candidate_json TEXT NOT NULL,
            assessment_json TEXT NOT NULL,
            candidate_sha256 TEXT NOT NULL,
            assessment_sha256 TEXT NOT NULL,
            findings_json TEXT NOT NULL,
            PRIMARY KEY(activity_id, pass_number)
        )
        """,
        """
        CREATE TABLE service_registration_publications(
            operation_id TEXT PRIMARY KEY,
            activity_id TEXT NOT NULL REFERENCES service_registrations(activity_id),
            kind TEXT NOT NULL CHECK(kind IN ('candidate', 'confirmation')),
            repository TEXT NOT NULL,
            branch TEXT NOT NULL,
            files_json TEXT NOT NULL,
            request_id TEXT,
            state TEXT NOT NULL CHECK(state IN ('prepared', 'writing', 'verified', 'applied', 'paused')),
            commit_sha TEXT,
            detail TEXT,
            profile_json TEXT NOT NULL
        )
        """,
        """
        CREATE TABLE service_registration_active(
            project_id TEXT PRIMARY KEY REFERENCES service_projects(project_id),
            activity_id TEXT NOT NULL,
            package_json TEXT NOT NULL,
            confirmation_json TEXT NOT NULL,
            activated_at TEXT NOT NULL
        )
        """,
    ),
)

_OPEN_STATES = ("intake", "scope", "architect", "architect_waiting", "reviewer", "publishing", "ready", "source_changed", "confirming", "cancelling", "paused", "limit_paused", "blocked")
_WORKING_STATES = ("architect", "reviewer", "publishing", "confirming", "cancelling", "ready")
_STR = {"type": "string"}
_ART = {
    "type": ["object", "null"],
    "properties": {"path": _STR, "sha256": _STR, "version": _STR},
    "required": ["path", "sha256", "version"],
    "additionalProperties": False,
}
RESPONSE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "contract_version": {"type": "integer"}, "assignment_id": _STR, "run_id": _STR, "project_id": _STR, "activity_id": _STR,
        "role": _STR, "source_commit": _STR, "decision_version": _STR,
        "result": {"type": "string", "enum": ["completed", "clarification_required", "technical_failure"]},
        "summary": _STR,
        "findings": {"type": "array", "items": {"type": "object", "properties": {
            "local_key": _STR, "subject": _STR, "severity": {"type": "string", "enum": ["blocking", "non_blocking"]},
            "explanation": _STR, "impact": _STR, "requested_correction": _STR,
            "source_refs": {"type": "array", "items": {"type": "object", "properties": {"path": _STR, "commit": _STR, "line": {"type": "integer"}}, "required": ["path", "commit", "line"], "additionalProperties": False}},
            "affected_items": {"type": "array", "items": {"type": "object", "properties": {"id": _STR, "subject": _STR, "version": _STR}, "required": ["id", "subject", "version"], "additionalProperties": False}},
        }, "required": ["local_key", "subject", "severity", "explanation", "impact", "requested_correction", "source_refs", "affected_items"], "additionalProperties": False}},
        "questions": {"type": "array", "items": {"type": "object", "properties": {
            "local_key": _STR, "subject": _STR, "question": _STR, "reason": _STR,
            "recipient": {"type": "string", "enum": ["project_architect", "owner"]},
            "finding_keys": {"type": "array", "items": _STR},
            "options": {"type": "array", "items": {"type": "object", "properties": {"local_key": _STR, "label": _STR, "tradeoff": _STR, "recommendation_reason": {"type": ["string", "null"]}}, "required": ["local_key", "label", "tradeoff", "recommendation_reason"], "additionalProperties": False}},
        }, "required": ["local_key", "subject", "question", "reason", "recipient", "finding_keys", "options"], "additionalProperties": False}},
        "candidate": _ART, "assessment": _ART, "reviewed_assessment": _ART,
        "review_outcome": {"type": ["string", "null"], "enum": ["APPROVE", "REQUEST_CHANGES", None]},
        "failure": {"type": ["object", "null"], "properties": {"code": _STR, "message": _STR}, "required": ["code", "message"], "additionalProperties": False},
    },
    "required": ["contract_version", "assignment_id", "run_id", "project_id", "activity_id", "role", "source_commit", "decision_version", "result", "summary", "findings", "questions", "candidate", "assessment", "reviewed_assessment", "review_outcome", "failure"],
    "additionalProperties": False,
}
_COMMON = (
    "Copy contract_version (1), assignment_id, run_id, project_id, activity_id, role, source_commit and decision_version exactly from assignment.json. "
    "failure must be null unless you cannot do the work. Every finding must cite at least one source line (path, the assigned commit, a line number). "
    "Return only the structured response."
)
_ARCHITECT_TASK = """You are the Maestro Project Architect assessing project sources for registration. Work only from this assignment, the sources under source/ (fixed at the assigned commit) and the files under input/. Never modify source/ or input/.

1. Read input/source-summary.json, then every document it lists (overview, architecture, milestone declarations) under source/.
2. Assess only the selected scope. For each included milestone check that its outcome, acceptance criteria and dependencies are clear enough to organize work without inventing requirements. Walk through how a person starts using the capability, what it depends on, how the parts connect and how the result is observed. Classify each dependency as existing, included (part of the selected scope) or missing, with an evidence level: reported, source_inspection, verified_in_operation, or not_applicable for unbuilt work. Do not require unbuilt functionality to exist, and do not audit code beyond targeted checks.
3. Write output/assessment.json exactly as {"schema":"registration_assessment_v1","summary":"<plain summary>","evidence":[{"claim":"<text>","level":"reported|source_inspection|verified_in_operation|not_applicable","source":"<path#heading>"}]}.
4. Write output/candidate.json exactly as {"schema":"registration_candidate_v1","summary":{"purpose":"<text>","priorities":["<text>"],"assessment_outcome":"ready|clarification_required|blocked"},"milestones":[{"reference":"<reference>","dependencies":[{"subject":"<text>","required_outcome":"<text>","state":"existing|included|missing","evidence_level":"reported|source_inspection|verified_in_operation|not_applicable","evidence":"<text>"}],"usage_walkthrough":"<text>"}]} with exactly one milestones entry for each of: {milestones}. Use an empty dependencies list only when the milestone truly has none.
5. Report every finding in the response. A blocking finding is missing or contradictory information that prevents reliable interpretation; wording preferences and optional improvements are non_blocking. If no blocking finding exists, assessment_outcome is ready.
6. If you cannot proceed without an answer from the Owner, return result clarification_required with specific questions (each with a plain question, the reason, and options where there are clear alternatives) and no completed files.
7. Compute the SHA-256 of both files with sha256sum and return them: assessment = {"path":"output/assessment.json","sha256":"<digest>","version":"1"} and candidate = {"path":"output/candidate.json","sha256":"<digest>","version":"1"}. reviewed_assessment and review_outcome must be null; result is completed when both files are written.
{amendment}""" + " " + _COMMON
_AMENDMENT = """
This is an amendment pass. Read input/previous-candidate.json, input/previous-assessment.json, input/review-findings.json (the independent reviewer's findings) and input/answers.json (the Owner's recorded answers). Address each finding by amending the files, or explain in the assessment why a finding does not apply. Do not add requirements the sources and answers do not support."""
_REVIEWER_TASK = """You are the independent Fidelity Reviewer for a project registration. Check the architect's work against the same source the architect used. Work only from this assignment, the sources under source/ (fixed at the assigned commit) and the files under input/. Never modify source/ or input/.

1. Read input/source-summary.json, input/decisions.json, input/candidate.json and input/assessment.json, then the source documents they rely on under source/.
2. Check fidelity: the candidate covers exactly the selected scope; purpose, scope, dependencies and acceptance requirements are faithful to the sources and recorded decisions; the assessment's findings and evidence are justified; nothing is invented and no new requirements are introduced. Minor wording and optional improvements are non_blocking and never prevent approval.
3. Return review_outcome APPROVE only when there is no blocking finding and no unanswered question; return REQUEST_CHANGES with at least one blocking finding (each citing source lines) otherwise.
4. candidate and reviewed_assessment must be copied exactly from assigned_artifacts in assignment.json; assessment must be null; result is completed.
{later}""" + " " + _COMMON
_REVIEWER_LATER = "\nThis is a follow-up review. Recheck only the findings in input/prior-findings.json and anything the amendment changed; do not introduce new requirements."


class RegistrationRejection(RequestRejection):
    pass


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def project_identity(repository: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", repository.replace("/", "-")).strip("-")[:100]


class RegistrationService:
    """Owns registration state; the worker thread calls ``tick`` repeatedly."""

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
        bindings: Mapping[str, tuple[str, str]],
        destination: Callable[[RepositoryProfile], GitHubDestination],
        role_choices: tuple[tuple[str, str], ...],
        state_dir: Path,
        owner_id: str,
    ) -> None:
        self.database = database
        self.records = records
        self.questions = questions
        self.reservations = reservations
        self.definitions = definitions
        self.runs = runs
        self.profiles = profiles
        self.bindings = bindings
        self._destination = destination
        self.role_choices = role_choices
        self.state_dir = state_dir
        self.owner_id = owner_id
        self._locks: dict[str, threading.Lock] = {}
        self._guard = threading.Lock()
        database.registry.register(REGISTRATION_MIGRATION)
        database.initialize()

    @property
    def operation_handlers(self) -> tuple[OperationHandler, ...]:
        return (
            OperationHandler("registration.start", self.prepare_start),
            OperationHandler("registration.confirm", self.prepare_confirm),
            OperationHandler("registration.cancel", self.prepare_cancel),
        )

    @property
    def recipients(self) -> dict[str, Callable[[DeliveredAnswer], None]]:
        return {"owner": self.receive_answer, "project_architect": self.receive_answer}

    # ------------------------------------------------------------------ intake

    def prepare_start(self, request: RequestLike) -> PreparedOperation:
        allowed = {"repository", "overview_path", "source_ref", "publication_branch", "scope", "architect", "reviewer"}
        payload = dict(request.payload)
        if request.project_id is not None or request.activity_id is not None:
            raise ValueError("registration.start requires empty project and activity context")
        unknown = set(payload) - allowed
        if unknown:
            raise ValueError(f"registration.start does not accept: {', '.join(sorted(unknown))}")
        if not isinstance(payload.get("repository"), str) or not payload["repository"].strip():
            raise ValueError("registration.start needs repository")
        if request.expected_version not in (None, 0):
            raise ValueError("registration.start expected_version must be zero")
        repository = payload["repository"].strip()
        project_id = project_identity(repository)
        previous = self._active_selection(project_id)
        for name in ("overview_path",):
            if payload.get(name) is None and previous is not None:
                payload[name] = previous["overview_path"]
            if not isinstance(payload.get(name), str) or not payload[name].strip():
                raise ValueError(f"registration.start needs {name}")
        overview_path = payload["overview_path"].strip()
        try:
            binding_name, profile = bind_repository(repository, self.profiles, self.bindings)
        except DestinationError as error:
            raise ValueError(f"{error.code}: {error}") from error
        entity_id = f"registration-request-{request.request_id}"
        existing = self._open_registration(project_id)
        if existing is not None:
            return self._duplicate(entity_id, project_id, existing)
        try:
            self.definitions.evaluate("registration")
        except ProcessPolicyError as error:
            raise ValueError(f"registration is not configured: {error}") from error
        selections = {}
        for role in ("architect", "reviewer"):
            value = payload.get(role)
            if value is None and previous is not None and previous[f"{role}_tool"] is not None:
                value = {"tool": previous[f"{role}_tool"], "model": previous[f"{role}_model"]}
            if value is None:
                continue
            if not isinstance(value, Mapping) or set(value) != {"tool", "model"} or not all(isinstance(value[k], str) and value[k] for k in ("tool", "model")):
                raise ValueError(f"{role} must be an object with tool and model")
            selections[role] = (value["tool"], value["model"])
            self._check_route(role, *selections[role])
        destination = self._destination(profile)
        try:
            branch = payload.get("publication_branch")
            inherited_branch = branch is None and previous is not None and previous["publication_branch"] is not None
            if inherited_branch:
                branch = previous["publication_branch"]
            if branch is not None:
                destination.check_publication_branch(repository, branch)
            default_branch = destination.default_branch(repository)
            requested_ref = payload.get("source_ref")
            if requested_ref is None and previous is not None and str(previous["source_ref"]).startswith("refs/"):
                requested_ref = previous["source_ref"]
            source_ref, commit, provenance = destination.resolve_source(repository, requested_ref)
            model = validate_sources(overview_path, lambda path: destination.read_file(repository, commit, path))
            scope = interpret_scope(model, payload.get("scope"))
        except DestinationError as error:
            raise ValueError(f"{error.code}: {error}") from error
        except SourceError as error:
            raise ValueError("the project sources cannot be registered: " + "; ".join(f"{p['document']}: {p['problem']}" for p in error.problems)) from error
        project = self._project_row(project_id)
        re_registration = previous is not None
        if project is not None and project["registration_status"] not in {"not_registered", "unregistered", "registered"}:
            raise ValueError("this project's registration cannot be started from its current state")
        if re_registration and project["registration_status"] != "registered":
            raise ValueError("this project's active registration is not in a state that can be updated")
        activity_id = f"registration-{uuid.uuid4().hex[:12]}"
        details = {
            "repository": repository, "binding": binding_name, "overview_path": overview_path, "scope": scope,
            "source_ref": source_ref, "source_commit": commit, "source_provenance": provenance,
            "branch": branch, "branch_provenance": "inherited" if inherited_branch else ("supplied" if branch is not None else None),
            "default_branch": default_branch, "selections": selections,
            "profile": profile.snapshot(binding_name), "project_name": model.project_name,
        }

        def apply(transaction: Transaction, next_version: int) -> OperationResult:
            found = self._open_registration(project_id, transaction)
            if found is not None:
                return OperationResult(
                    data={"activity_id": found, "duplicate": True, "message": "registration is already in progress for this project"},
                    project_id=project_id, activity_id=found,
                )
            now = _now()
            if project is None:
                self.records.create_project(transaction, ProjectRecord(project_id, model.project_name, "registering", 1))
            else:
                shown = "updating_registration" if re_registration else "registering"
                name = project["name"] if re_registration else model.project_name
                self.records.update_project(transaction, ProjectRecord(project_id, name, shown, int(project["version"]) + 1), expected_record_version=int(project["version"]))
            try:
                self.reservations.reserve(transaction, project_id, "re_registration" if re_registration else "start", activity_id)
            except ReservationError as error:
                raise RequestRejection(409, error.code, str(error), fields=error.fields) from error

            def creator(tx: Transaction, snapshot) -> None:
                definition = snapshot.definition
                version = int(tx.execute("SELECT COALESCE(MAX(registration_version), 0) + 1 FROM service_registrations WHERE project_id = ?", (project_id,)).fetchone()[0])
                self.records.create_activity(tx, ActivityRecord(
                    activity_id, project_id, "registration", f"{'Update registration of' if re_registration else 'Register'} {model.project_name}", "registering", 1,
                    "Intake", now, None, (ActivityAction(f"{activity_id}-cancel", "Cancel registration", "action"),),
                ))
                tx.execute("INSERT INTO entity_versions(entity_id, version) VALUES (?, 1) ON CONFLICT(entity_id) DO UPDATE SET version = 1", (activity_id,))
                chosen = details["selections"]
                tx.execute(
                    """
                    INSERT INTO service_registrations(
                        activity_id, project_id, repository, binding, overview_path, scope_json, source_ref, source_commit,
                        source_provenance, publication_branch, branch_provenance, default_branch, profile_json,
                        architect_tool, architect_model, reviewer_tool, reviewer_model, state, review_limit,
                        registration_version, created_at, selected_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'intake', ?, ?, ?, ?)
                    """,
                    (
                        activity_id, project_id, repository, binding_name, overview_path, canonical_json(scope), source_ref, commit,
                        provenance, branch, details["branch_provenance"], default_branch, canonical_json(details["profile"]),
                        *(chosen.get("architect", (None, None))), *(chosen.get("reviewer", (None, None))),
                        int(definition["maximum_fidelity_reviews"]), version, now, now,
                    ),
                )
                self._say(tx, project_id, activity_id, f"{'Registration update' if re_registration else 'Registration'} started for {model.project_name}: source {source_ref} at {commit[:12]}, overview {overview_path}.")
                self._next_intake_step(tx, activity_id)

            self.definitions.start_activity(transaction, "registration", activity_id, creator)
            return OperationResult(
                data={"activity_id": activity_id, "project_id": project_id, "duplicate": False, "source_commit": commit},
                status="accepted", project_id=project_id, activity_id=activity_id,
            )

        return PreparedOperation(entity_id, "registration.started", {"project_id": project_id}, apply)

    def _duplicate(self, entity_id: str, project_id: str, activity_id: str) -> PreparedOperation:
        def apply(transaction: Transaction, next_version: int) -> OperationResult:
            return OperationResult(
                data={"activity_id": activity_id, "duplicate": True, "message": "registration is already in progress for this project"},
                project_id=project_id, activity_id=activity_id,
            )
        return PreparedOperation(entity_id, "registration.duplicate", {"activity_id": activity_id}, apply)

    def _check_route(self, role: str, tool: str, model: str) -> None:
        if self.runs is None:
            raise ValueError("no agent tools are configured for registration")
        try:
            self.runs.route_resolver("architect" if role == "architect" else "fidelity_reviewer", tool, model)
        except Exception as error:  # noqa: BLE001 - any refusal to resolve the route means it cannot be launched
            raise ValueError(f"{role} selection {tool}/{model} cannot be used: {error}") from error

    def _next_intake_step(self, tx: Transaction, activity_id: str) -> None:
        """Publish the question for the first missing intake choice, or move to scope confirmation."""
        row = self._row(tx, "SELECT * FROM service_registrations WHERE activity_id = ?", (activity_id,))
        project_id = row["project_id"]
        if row["publication_branch"] is None:
            default = row["default_branch"]
            self._ask(tx, row, "publication_branch", "Choose the publication branch",
                      f"Which existing branch of {row['repository']} may Maestro publish registration records to? "
                      f"The repository's default branch is {default}; it is suggested here but is not authorization. Maestro creates no branch.",
                      (AnswerChoice("default-branch", f"Publish to {default}", "Uses the repository's default branch.", None),))
            return
        for role, label in (("architect", "architect"), ("reviewer", "independent reviewer")):
            if row[f"{role}_tool"] is None:
                choices = tuple(AnswerChoice(f"{tool}:{model}", f"{tool} · {model}", "Installed route with verified model.", None) for tool, model in self.role_choices)
                self._ask(tx, row, role, f"Choose the {label} tool and model",
                          f"Which installed tool and model should act as the {label} for this registration? The architect and the reviewer are selected separately before the architect starts.", choices)
                return
        scope = json.loads(row["scope_json"])
        lines = [f"Registration scope: {scope['description']}.", "Included: " + "; ".join(f"{i['reference']} — {i['subject']}" for i in scope["included"]) + "."]
        lines.append("Excluded: " + ("; ".join(f"{i['reference']} — {i['subject']}" for i in scope["excluded"]) or "none") + ".")
        if scope["outside_dependencies"]:
            lines.append("Outside dependencies: " + "; ".join(f"{d['milestone']} needs {d['reference']} ({d['state']})" for d in scope["outside_dependencies"]) + ".")
        else:
            lines.append("Outside dependencies: none.")
        lines.append(f"Source: {row['repository']} {row['source_ref']} at {row['source_commit']}; publication branch {row['publication_branch']}.")
        self._ask(tx, row, "scope", "Confirm the registration scope", " ".join(lines) + " Confirming scope starts the assessment; it does not confirm registration.",
                  (AnswerChoice("confirm-scope", "Confirm this scope", "Starts the architect assessment of exactly this scope.", None),))

    def _ask(self, tx: Transaction, row: Mapping[str, Any], kind: str, subject: str, prompt: str, choices: tuple[AnswerChoice, ...],
             *, original: str | None = None, previous_answer: str | None = None, recipient: str = "owner", requester: str = "registration") -> str:
        seq = int(row["question_seq"]) + 1
        tx.execute("UPDATE service_registrations SET question_seq = ? WHERE activity_id = ?", (seq, row["activity_id"]))
        question_id = f"{row['activity_id']}-q{seq}"
        self.questions.publish(tx, LinkedQuestion(
            question_id, row["project_id"], row["activity_id"], subject, prompt, requester, recipient,
            choices=choices, allow_free_text=True, original_question_id=original, previous_answer_id=previous_answer,
        ))
        pending = json.loads(row["pending_json"] or "{}")
        pending.setdefault("questions", {})[question_id] = {"kind": kind}
        state = "intake" if kind in {"publication_branch", "architect", "reviewer"} else row["state"]
        if kind == "scope":
            state = "scope"
        tx.execute("UPDATE service_registrations SET pending_json = ?, state = ? WHERE activity_id = ?", (canonical_json(pending), state, row["activity_id"]))
        self._activity(tx, row["activity_id"], "registering" if state in {"intake", "scope"} else None, f"Waiting for your answer: {subject}")
        return question_id

    # ----------------------------------------------------------------- answers

    def receive_answer(self, answer: DeliveredAnswer) -> None:
        with self.database.transaction() as tx:
            row = self._row(tx, "SELECT * FROM service_registrations WHERE activity_id = ?", (answer.activity_id,))
            if row is None:
                return
            pending = json.loads(row["pending_json"] or "{}")
            info = pending.get("questions", {}).get(answer.question_id)
            if info is None or info.get("answered"):
                return  # a replayed delivery: already applied
            info["answered"] = answer.answer_id
            tx.execute("UPDATE service_registrations SET pending_json = ? WHERE activity_id = ?", (canonical_json(pending), answer.activity_id))
            question = self._row(tx, "SELECT subject, prompt, requester FROM service_questions WHERE question_id = ?", (answer.question_id,))
            if row["state"] in {"cancelling", "cancelled"}:
                self._resolve_question(tx, answer.question_id)
                return
            handler = getattr(self, f"_answer_{info['kind']}", self._answer_architect_question)
            handler(tx, row, pending, info, answer, question)
            self._resolve_question(tx, answer.question_id)

    def _decision(self, tx: Transaction, row: Mapping[str, Any], kind: str, subject: str, answer: DeliveredAnswer | None, question: Mapping[str, Any] | None, resolution: str) -> None:
        version = int(row["decision_version"]) + 1
        tx.execute("UPDATE service_registrations SET decision_version = ? WHERE activity_id = ?", (version, row["activity_id"]))
        number = int(tx.execute("SELECT COUNT(*) FROM service_registration_decisions WHERE activity_id = ?", (row["activity_id"],)).fetchone()[0]) + 1
        tx.execute(
            "INSERT INTO service_registration_decisions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (f"{row['activity_id']}-d{number}", row["activity_id"], kind, subject, None if answer is None else answer.question_id,
             None if question is None else str(question["prompt"]), "" if answer is None else answer.text, None if answer is None else answer.choice_id,
             resolution, f"Owner {self.owner_id}", version, _now()),
        )

    def _followup(self, tx: Transaction, row: Mapping[str, Any], kind: str, answer: DeliveredAnswer, question: Mapping[str, Any], text: str, choices: tuple[AnswerChoice, ...] = ()) -> None:
        fresh = self._row(tx, "SELECT * FROM service_registrations WHERE activity_id = ?", (row["activity_id"],))
        self._ask(tx, fresh, kind, str(question["subject"]), text, choices, original=answer.original_question_id or answer.question_id, previous_answer=answer.answer_id)

    def _answer_publication_branch(self, tx, row, pending, info, answer, question) -> None:
        branch = row["default_branch"] if answer.choice_id == "default-branch" else answer.text.strip()
        profile = self._profile_of(row)
        try:
            self._destination(profile).check_publication_branch(row["repository"], branch)
        except DestinationError as error:
            self._followup(tx, row, "publication_branch", answer, question, f"Branch {branch!r} cannot be used: {error}. Name another existing branch that allows direct writes.", ())
            return
        tx.execute("UPDATE service_registrations SET publication_branch = ?, branch_provenance = ? WHERE activity_id = ?",
                   (branch, "owner_choice" if answer.choice_id != "default-branch" else "owner_chose_default", row["activity_id"]))
        self._decision(tx, row, "publication_branch", "Publication branch", answer, question, f"Owner authorized direct publication to branch {branch}.")
        self._next_intake_step(tx, row["activity_id"])

    def _answer_role(self, role: str, tx, row, answer, question) -> None:
        text = (answer.choice_id or answer.text).strip()
        tool, _, model = text.partition(":")
        if not tool or not model:
            tool, _, model = text.partition("/")
        try:
            self._check_route(role, tool, model)
        except ValueError as error:
            choices = tuple(AnswerChoice(f"{t}:{m}", f"{t} · {m}", "Installed route with verified model.", None) for t, m in self.role_choices)
            self._followup(tx, row, role, answer, question, f"{error}. Choose an installed tool and model.", choices)
            return
        tx.execute(f"UPDATE service_registrations SET {role}_tool = ?, {role}_model = ? WHERE activity_id = ?", (tool, model, row["activity_id"]))
        self._decision(tx, row, role, f"{role.title()} tool and model", answer, question, f"Owner selected {tool} {model} as the {role}.")
        self._next_intake_step(tx, row["activity_id"])

    def _answer_architect(self, tx, row, pending, info, answer, question) -> None:
        self._answer_role("architect", tx, row, answer, question)

    def _answer_reviewer(self, tx, row, pending, info, answer, question) -> None:
        self._answer_role("reviewer", tx, row, answer, question)

    def _answer_scope(self, tx, row, pending, info, answer, question) -> None:
        if answer.choice_id != "confirm-scope":
            self._followup(tx, row, "scope", answer, question,
                           "A written reply cannot change the scope. Select Confirm this scope to assess exactly the scope shown, or cancel this registration and start it again with a narrower selection.",
                           (AnswerChoice("confirm-scope", "Confirm this scope", "Starts the architect assessment of exactly this scope.", None),))
            return
        self._decision(tx, row, "scope", "Registration scope confirmed", answer, question, "Owner confirmed the interpreted scope, exclusions and outside dependencies.")
        tx.execute("UPDATE service_registrations SET state = 'architect', pending_json = ? WHERE activity_id = ?", (canonical_json({"questions": pending["questions"]}), row["activity_id"]))
        self._activity(tx, row["activity_id"], "assessing", "Architect assessment is about to start")
        self._say(tx, row["project_id"], row["activity_id"], "Scope confirmed. The architect assessment starts next.")

    def _answer_architect_question(self, tx, row, pending, info, answer, question) -> None:
        self._decision(tx, row, "clarification", str(question["subject"]), answer, question, f"Owner answered: {answer.text}")
        remaining = [q for q, i in pending.get("questions", {}).items() if i.get("kind") == "architect_question" and not i.get("answered")]
        if remaining:
            return
        tx.execute("UPDATE service_registrations SET state = 'architect' WHERE activity_id = ?", (row["activity_id"],))
        pending = {"questions": pending["questions"], "amend": pending.get("amend", {})}
        tx.execute("UPDATE service_registrations SET pending_json = ? WHERE activity_id = ?", (canonical_json(pending), row["activity_id"]))
        self._activity(tx, row["activity_id"], "assessing", "Answers recorded; the architect resumes")

    def _answer_source_change(self, tx, row, pending, info, answer, question) -> None:
        if answer.choice_id == "retain-source":
            self._decision(tx, row, "source", "Retain the reviewed source", answer, question, "Owner chose to keep the reviewed source; newer changes are excluded from the package.")
            pending = {"questions": pending["questions"], "source_choice": "retained", "source_checked": {"commit": pending["latest"]["commit"]}}
            tx.execute("UPDATE service_registrations SET state = 'ready', pending_json = ? WHERE activity_id = ?", (canonical_json(pending), row["activity_id"]))
            self._activity(tx, row["activity_id"], "ready", "Awaiting your confirmation of the reviewed candidate", self._ready_actions(row["activity_id"], json.loads(row["package_json"])))
        elif answer.choice_id == "include-update":
            latest = pending["latest"]
            self._decision(tx, row, "source", "Include updated source", answer, question, f"Owner chose to assess the updated source at {latest['commit']}.")
            tx.execute(
                "UPDATE service_registrations SET source_commit = ?, source_provenance = 'owner_updated', state = 'architect', pending_json = ?, candidate_id = NULL, package_json = NULL WHERE activity_id = ?",
                (latest["commit"], canonical_json({"questions": pending["questions"], "amend": pending.get("amend", {}), "restart": True}), row["activity_id"]),
            )
            self._activity(tx, row["activity_id"], "assessing", "Updated source chosen; the candidate is being reassessed within the same review budget")
        else:
            self._followup(tx, row, "source_change", answer, question, "Choose Retain the reviewed source or Include the updated source.", self._source_choices())

    @staticmethod
    def _source_choices() -> tuple[AnswerChoice, ...]:
        return (
            AnswerChoice("retain-source", "Retain the reviewed source", "The package covers the reviewed requirements and excludes newer changes.", None),
            AnswerChoice("include-update", "Include the updated source", "The candidate is reassessed; affected findings are rechecked within the existing review budget.", None),
        )

    # ------------------------------------------------------------ confirm/cancel

    def prepare_confirm(self, request: RequestLike) -> PreparedOperation:
        if request.project_id is None or request.activity_id is None or request.expected_version is None:
            raise ValueError("registration.confirm needs project, activity and the displayed activity version")
        if set(request.payload) != {"package_ref"}:
            raise ValueError("registration.confirm payload must contain package_ref")
        shown = request.payload["package_ref"]
        activity_id = request.activity_id

        def apply(transaction: Transaction, next_version: int) -> OperationResult:
            row = self._row(transaction, "SELECT * FROM service_registrations WHERE activity_id = ? AND project_id = ?", (activity_id, request.project_id))
            if row is None:
                raise RequestRejection(404, "registration_not_found", "the registration was not found", fields={"activity_id": activity_id})
            if row["state"] == "confirming":
                raise RequestRejection(409, "confirmation_pending", "a confirmation is already pending; its outcome is being established")
            if row["state"] != "ready" or row["package_json"] is None:
                raise RequestRejection(409, "candidate_not_ready", "the candidate is not ready for confirmation; open the current candidate and review it first", fields={"state": row["state"]})
            package = json.loads(row["package_json"])
            if shown != package:
                raise RequestRejection(409, "candidate_changed", "the candidate shown is not the current candidate; inspect it again before confirming", fields={"current": package})
            operation_id = f"{activity_id}-confirm"
            confirmation_id = f"confirmation-{uuid.uuid4().hex[:12]}"
            pending = json.loads(row["pending_json"] or "{}")
            pending["confirmation"] = {"confirmation_id": confirmation_id, "request_id": request.request_id, "confirmed_at": _now()}
            transaction.execute("UPDATE service_registrations SET state = 'confirming', pending_json = ? WHERE activity_id = ?", (canonical_json(pending), activity_id))
            transaction.execute(
                "INSERT INTO service_registration_publications(operation_id, activity_id, kind, repository, branch, files_json, request_id, state, profile_json) VALUES (?, ?, 'confirmation', ?, ?, '{}', ?, 'prepared', ?)",
                (operation_id, activity_id, row["repository"], row["publication_branch"], request.request_id, row["profile_json"]),
            )
            self._activity(transaction, activity_id, "confirming", "Confirmation accepted; publishing the receipt to GitHub before activation", (), version=next_version)
            self._say(transaction, row["project_id"], activity_id, f"Confirmation accepted for candidate {package['candidate_id']} (version {package['registration_version']}). The receipt is being published.")
            return OperationResult(
                data={"activity_id": activity_id, "confirmation_id": confirmation_id, "package_ref": package, "message": "confirmation accepted; registration is active after the receipt is verified on GitHub"},
                status="accepted", project_id=row["project_id"], activity_id=activity_id,
            )

        return PreparedOperation(activity_id, "registration.confirmation_requested", {"activity_id": activity_id}, apply)

    def prepare_cancel(self, request: RequestLike) -> PreparedOperation:
        if request.project_id is None or request.activity_id is None or request.expected_version is None:
            raise ValueError("registration.cancel needs project, activity and the displayed activity version")
        if request.payload:
            raise ValueError("registration.cancel takes no payload")
        activity_id = request.activity_id

        def apply(transaction: Transaction, next_version: int) -> OperationResult:
            row = self._row(transaction, "SELECT * FROM service_registrations WHERE activity_id = ? AND project_id = ?", (activity_id, request.project_id))
            if row is None:
                raise RequestRejection(404, "registration_not_found", "the registration was not found", fields={"activity_id": activity_id})
            if row["state"] == "confirming":
                raise RequestRejection(409, "confirmation_pending", "a confirmation is pending; it cannot be cancelled while its outcome is established")
            if row["state"] in {"cancelling", "cancelled", "confirmed"}:
                raise RequestRejection(409, "registration_ended", "the registration attempt has ended or is already being cancelled", fields={"state": row["state"]})
            pending = json.loads(row["pending_json"] or "{}")
            pending["cancel_request_id"] = request.request_id
            transaction.execute("UPDATE service_registrations SET state = 'cancelling', cancel_requested = 1, pending_json = ? WHERE activity_id = ?", (canonical_json(pending), activity_id))
            self._activity(transaction, activity_id, "cancelling", "Stopping: waiting for the agent run and any external write to be resolved", (), version=next_version)
            self._say(transaction, row["project_id"], activity_id, "Cancellation requested. Stopping any running agent before the attempt ends.")
            return OperationResult(data={"activity_id": activity_id, "message": "cancellation accepted; the attempt ends once its work is confirmed stopped"}, status="accepted", project_id=row["project_id"], activity_id=activity_id)

        return PreparedOperation(activity_id, "registration.cancel_requested", {"activity_id": activity_id}, apply)

    # ----------------------------------------------------------------- worker

    def tick(self) -> None:
        """Deliver saved answers, then advance every registration that can move."""
        try:
            self.questions.deliver_pending()
        except RecipientDeliveryInterrupted:
            log.warning("an answer delivery was interrupted and will be retried", exc_info=True)
        with self.database.read_connection() as connection:
            ids = [str(r[0]) for r in connection.execute(
                f"SELECT activity_id FROM service_registrations WHERE state IN ({','.join('?' for _ in _WORKING_STATES)}) ORDER BY created_at", _WORKING_STATES)]
        for activity_id in ids:
            lock = self._lock(activity_id)
            if not lock.acquire(blocking=False):
                continue
            try:
                self.advance(activity_id)
            except Exception as error:  # noqa: BLE001 - one registration's failure must not stop the others
                log.exception("registration step failed for %s", activity_id)
                self._pause_on_error(activity_id, error)
            finally:
                lock.release()

    def _lock(self, activity_id: str) -> threading.Lock:
        with self._guard:
            return self._locks.setdefault(activity_id, threading.Lock())

    def advance(self, activity_id: str) -> None:
        row = self._read("SELECT * FROM service_registrations WHERE activity_id = ?", (activity_id,))
        if row is None:
            return
        state = row["state"]
        if state == "cancelling":
            self._advance_cancel(row)
        elif state == "architect":
            self._advance_agent(row, "architect")
        elif state == "reviewer":
            self._advance_agent(row, "reviewer")
        elif state == "publishing":
            self._advance_publish(row)
        elif state == "confirming":
            self._advance_confirm(row)
        elif state == "ready":
            self._check_source(row)

    def _pause_on_error(self, activity_id: str, error: Exception) -> None:
        transient = isinstance(error, DestinationError) and (
            error.code == "github_unreachable" or (isinstance(error.fields.get("status"), int) and error.fields["status"] >= 500)
        )
        if transient:
            return
        reason = f"{getattr(error, 'code', type(error).__name__)}: {error}"
        with self.database.transaction() as tx:
            row = self._row(tx, "SELECT state FROM service_registrations WHERE activity_id = ?", (activity_id,))
            if row is not None and row["state"] == "confirming" and getattr(error, "code", None) == "publication_conflict":
                # Definite refusal: no receipt was written, so the confirmation did not take effect and the Owner may cancel.
                tx.execute("UPDATE service_registration_publications SET state = 'paused' WHERE operation_id = ?", (f"{activity_id}-confirm",))
                tx.execute("UPDATE service_registrations SET state = 'paused', note = ? WHERE activity_id = ?", (reason[:500], activity_id))
                self._activity(tx, activity_id, "paused", f"Confirmation refused, nothing was written: {reason[:300]}", (ActivityAction(f"{activity_id}-cancel", "Cancel registration", "action"),))
                self._say(tx, self._project_of(tx, activity_id), activity_id, f"Confirmation refused; nothing was written to GitHub: {reason[:400]}")
                return
            if row is None or row["state"] in {"cancelled", "confirmed", "cancelling", "confirming"}:
                return
            tx.execute("UPDATE service_registrations SET state = 'paused', note = ? WHERE activity_id = ?", (reason[:500], activity_id))
            self._activity(tx, activity_id, "paused", f"Paused: {reason[:300]}", (ActivityAction(f"{activity_id}-cancel", "Cancel registration", "action"),))
            self._say(tx, self._project_of(tx, activity_id), activity_id, f"Registration paused: {reason[:400]}")

    # -- agents

    def _profile_of(self, row: Mapping[str, Any]) -> RepositoryProfile:
        return self.profiles[json.loads(row["profile_json"])["profile"]]

    def _agent_pass(self, row: Mapping[str, Any], role: str) -> tuple[str, int]:
        pending = json.loads(row["pending_json"] or "{}")
        return pending.get(f"{role}_assignment"), int(row["pass_number"])

    def _advance_agent(self, row: Mapping[str, Any], role: str) -> None:
        if self.runs is None:
            raise AgentRunError("agents_unavailable", "no agent tools are configured")
        activity_id = row["activity_id"]
        pending = json.loads(row["pending_json"] or "{}")
        current = pending.get(f"{role}_run")
        if current is None:
            if role == "reviewer" and int(row["reviews_used"]) >= int(row["review_limit"]):
                self._limit_pause(row)
                return
            self._start_agent(row, role, pending)
            return
        view = self.runs.poll(current["run_id"])
        if view.state in {"reserved", "running", "stopping"}:
            return
        assignment = self.runs.assignment_state(current["assignment_id"])
        if view.state == "completed":
            if assignment["state"] == "waiting_for_answers":
                self._architect_questions(row, current)
            else:
                (self._accept_architect if role == "architect" else self._accept_review)(row, current)
            return
        if assignment["state"] == "needs_recovery":
            self._recover_agent(row, role, current, pending, view.failure_code or "technical_failure")
            return
        if view.state == "cancelled":
            return
        reason = f"{role} run {view.state}" + (f" ({view.failure_code})" if view.failure_code else "") + (f": {view.terminal_reason}" if view.terminal_reason else "")
        self._pause(row, reason)

    def _start_agent(self, row: Mapping[str, Any], role: str, pending: dict[str, Any], recovery_note: str | None = None) -> None:
        assert self.runs is not None
        activity_id, project_id = row["activity_id"], row["project_id"]
        run_role = "architect" if role == "architect" else "fidelity_reviewer"
        terms = self.definitions.assignment_terms(activity_id, run_role)
        pass_number = int(row["pass_number"]) + (1 if role == "architect" and recovery_note is None else 0)
        rounds = int(row["reviews_used"]) + 1
        assignment_id = f"{activity_id}-{role[:4]}-{pass_number if role == 'architect' else rounds}"
        tool, model = row[f"{role}_tool"], row[f"{role}_model"]
        destination = self._destination(self._profile_of(row))
        mirror = self.state_dir / "sources" / f"{project_id}.git"
        destination.fetch_source(row["repository"], row["source_commit"], mirror)
        inputs, artifacts = self._inputs(row, role, pending)
        decision_version = f"d{row['decision_version']}"
        limits = {"run_timeout_seconds": terms.duration_seconds}
        scope = json.loads(row["scope_json"])
        summary = {"milestones": [i["reference"] for i in scope["included"]]}
        note = "" if recovery_note is None else f" The previous run's output was rejected: {recovery_note}. Fix exactly that."
        if role == "architect":
            task = _ARCHITECT_TASK.replace("{milestones}", ", ".join(summary["milestones"])).replace("{amendment}", _AMENDMENT if "previous-candidate.json" in inputs else "") + note
            responsibilities = ("Assess the supplied sources and prepare the candidate registration; never invent requirements.",)
            actions = ("read_source", "write_output")
        else:
            task = _REVIEWER_TASK.replace("{later}", _REVIEWER_LATER if "prior-findings.json" in inputs else "") + note
            responsibilities = ("Independently check fidelity of the candidate and assessment against the same source.",)
            actions = ("read_source", "write_output")

        def build(run_id: str) -> RunBuild:
            assignment = AgentAssignment(
                project_id=project_id, activity_id=activity_id, assignment_id=assignment_id, run_id=run_id,
                parent_assignment_id=None, role="project_architect" if role == "architect" else "fidelity_reviewer",
                role_responsibilities=responsibilities, task=task, source_commit=row["source_commit"], decision_version=decision_version,
                instructions={
                    "document_paths": [row["overview_path"]], "selected_scope": summary["milestones"],
                    "recorded_decisions": ["input/decisions.json"], "relevant_answers": [], "outstanding_questions": [],
                    "prior_findings": [], "candidate_refs": [],
                },
                permitted_actions=actions, writable_locations=("output", "scratch"), limits=limits,
                clarification_conditions=("Required source information is absent or contradictory.",), response_schema=RESPONSE_SCHEMA,
                assigned_artifacts=artifacts,
            )
            return RunBuild(assignment, mirror, inputs)

        existing = self._assignment_exists(assignment_id)
        if not existing:
            self.runs.create_assignment_from_terms(terms, assignment_id, project_id, activity_id, tool, model)
        run_id = f"{assignment_id}-run{self.runs.run_count(assignment_id) + 1}"
        kind = "initial" if recovery_note is None else "recovery"
        self.runs.start_run(assignment_id, run_id, kind, build)
        pending[f"{role}_run"] = {"assignment_id": assignment_id, "run_id": run_id}
        with self.database.transaction() as tx:
            updates = "pass_number = ?, " if role == "architect" else ""
            params: list[Any] = [pass_number] if role == "architect" else []
            tx.execute(f"UPDATE service_registrations SET {updates}pending_json = ? WHERE activity_id = ?", (*params, canonical_json(pending), activity_id))
            label = "Project architect" if role == "architect" else "Independent fidelity reviewer"
            self._activity(tx, activity_id, "assessing" if role == "architect" else "reviewing",
                           f"{label} ({tool} {model}) is working · review round {int(row['reviews_used']) + (0 if role == 'architect' else 1)} of {row['review_limit']}")
            self._say(tx, project_id, activity_id, f"{label} started: {tool} {model}, assignment {assignment_id}, run {run_id}.")

    def _assignment_exists(self, assignment_id: str) -> bool:
        assert self.runs is not None
        try:
            self.runs.assignment_state(assignment_id)
            return True
        except AgentRunError:
            return False

    def _inputs(self, row: Mapping[str, Any], role: str, pending: Mapping[str, Any]) -> tuple[dict[str, bytes], dict[str, ArtifactReference]]:
        activity_id = row["activity_id"]
        scope = json.loads(row["scope_json"])
        destination = self._destination(self._profile_of(row))
        model = self._model(row, destination)
        inputs: dict[str, bytes] = {
            "source-summary.json": encode({"selected_scope": scope, "source": model.as_summary(), "source_commit": row["source_commit"], "documents": list(model.documents)}),
            "decisions.json": encode({"decisions": self._decisions(activity_id)}),
        }
        artifacts: dict[str, ArtifactReference] = {}
        latest = self._latest_pass(activity_id)
        if role == "architect":
            reviews = self._reviews(activity_id)
            inputs["answers.json"] = encode({"answers": [d for d in self._decisions(activity_id) if d["kind"] == "clarification"]})
            if latest is not None:
                inputs["previous-candidate.json"] = latest["candidate_json"].encode()
                inputs["previous-assessment.json"] = latest["assessment_json"].encode()
                last = reviews[-1] if reviews else None
                inputs["review-findings.json"] = encode({"findings": json.loads(last["findings_json"]) if last else [], "outcome": last["outcome"] if last else None})
        else:
            assert latest is not None
            inputs["candidate.json"] = latest["candidate_json"].encode()
            inputs["assessment.json"] = latest["assessment_json"].encode()
            artifacts["candidate"] = ArtifactReference("input/candidate.json", latest["candidate_sha256"], "1")
            artifacts["reviewed_assessment"] = ArtifactReference("input/assessment.json", latest["assessment_sha256"], "1")
            reviews = self._reviews(activity_id)
            if reviews:
                inputs["prior-findings.json"] = encode({"findings": json.loads(reviews[-1]["findings_json"])})
        return inputs, artifacts

    def _model(self, row: Mapping[str, Any], destination: GitHubDestination) -> SourceModel:
        return validate_sources(row["overview_path"], lambda path: destination.read_file(row["repository"], row["source_commit"], path))

    def _recover_agent(self, row, role, current, pending, code: str) -> None:
        assert self.runs is not None
        detail = self.runs.view(current["run_id"]).terminal_reason or code
        pending.pop(f"{role}_run", None)
        self._start_agent(row, role, {**pending, f"{role}_run": None}, recovery_note=detail)

    def _architect_questions(self, row: Mapping[str, Any], current: Mapping[str, str]) -> None:
        assert self.runs is not None
        response = self.runs.response(current["run_id"]) or {}
        requests = _questions(response.get("questions", []))
        findings = _findings(response.get("findings", []))
        assignment = AgentAssignment(
            project_id=row["project_id"], activity_id=row["activity_id"], assignment_id=current["assignment_id"], run_id=current["run_id"], parent_assignment_id=None,
            role="project_architect", role_responsibilities=("x",), task="x", source_commit=row["source_commit"], decision_version=f"d{row['decision_version']}",
            instructions={}, permitted_actions=("read_source",), writable_locations=("output", "scratch"), limits={}, clarification_conditions=("x",), response_schema={},
        )
        with self.database.transaction() as tx:
            fresh = self._row(tx, "SELECT * FROM service_registrations WHERE activity_id = ?", (row["activity_id"],))
            pending = json.loads(fresh["pending_json"] or "{}")
            pending.pop("architect_run", None)
            self._save_findings(tx, fresh, findings, "architect")
            for request in requests:
                seq = int(fresh["question_seq"]) + 1
                fresh = {**fresh, "question_seq": seq}
                tx.execute("UPDATE service_registrations SET question_seq = ? WHERE activity_id = ?", (seq, row["activity_id"]))
                question_id = f"{row['activity_id']}-q{seq}"
                self.questions.publish(tx, request.to_linked_question(question_id=question_id, assignment=assignment, requester="project_architect"))
                pending.setdefault("questions", {})[question_id] = {"kind": "architect_question"}
            tx.execute("UPDATE service_registrations SET state = 'architect_waiting', pending_json = ? WHERE activity_id = ?", (canonical_json(pending), row["activity_id"]))
            self._activity(tx, row["activity_id"], "waiting", f"Waiting for your answer: the architect asked {len(requests)} question(s)")
            self._say(tx, row["project_id"], row["activity_id"], f"The architect needs {len(requests)} answer(s) before continuing.")

    def _accept_architect(self, row: Mapping[str, Any], current: Mapping[str, str]) -> None:
        assert self.runs is not None
        response = self.runs.response(current["run_id"]) or {}
        artifacts = self.runs.artifacts(current["run_id"])
        scope = json.loads(row["scope_json"])
        try:
            candidate_text = Path(artifacts["candidate"][2]).read_text(encoding="utf-8")
            assessment_text = Path(artifacts["assessment"][2]).read_text(encoding="utf-8")
            candidate = validate_candidate(json.loads(candidate_text), scope)
            assessment = validate_assessment(json.loads(assessment_text))
            if candidate["summary"]["assessment_outcome"] == "ready" and any(f["severity"] == "blocking" for f in response.get("findings", [])):
                raise CandidateError("assessment_outcome is ready but the response reports a blocking finding")
        except (KeyError, OSError, ValueError, CandidateError) as error:
            self.runs.reject_result(current["run_id"], "malformed_output", f"registration output invalid: {error}")
            return
        findings = _findings(response.get("findings", []))
        with self.database.transaction() as tx:
            fresh = self._row(tx, "SELECT * FROM service_registrations WHERE activity_id = ?", (row["activity_id"],))
            pending = json.loads(fresh["pending_json"] or "{}")
            pending.pop("architect_run", None)
            tx.execute(
                "INSERT INTO service_registration_passes VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (row["activity_id"], int(fresh["pass_number"]), current["assignment_id"], current["run_id"], candidate_text, assessment_text,
                 artifacts["candidate"][1], artifacts["assessment"][1], canonical_json({"findings": list(findings)})),
            )
            self._save_findings(tx, fresh, findings, "architect")
            tx.execute("UPDATE service_registrations SET state = 'reviewer', pending_json = ? WHERE activity_id = ?", (canonical_json(pending), row["activity_id"]))
            self._activity(tx, row["activity_id"], "reviewing", f"Architect finished; independent review round {int(fresh['reviews_used']) + 1} of {fresh['review_limit']} is next")
            self._say(tx, row["project_id"], row["activity_id"], f"Architect assessment complete: {response.get('summary', '')} ({len(findings)} finding(s)).")

    def _accept_review(self, row: Mapping[str, Any], current: Mapping[str, str]) -> None:
        assert self.runs is not None
        response = self.runs.response(current["run_id"]) or {}
        outcome = response.get("review_outcome")
        findings = _findings(response.get("findings", []))
        run_row = self.runs.run_evidence(current["run_id"])
        assignment = self.runs.assignment_state(current["assignment_id"])
        # The shared counter is the review accounting record; one completed review consumes one round, however often it is delivered.
        already = self._read("SELECT 1 AS n FROM service_registration_reviews WHERE run_id = ?", (current["run_id"],))
        counters = self.definitions.policy.status(row["activity_id"]).counters
        consumed = int(counters.get(("fidelity_reviews", "activity"), 0))
        if already is None and consumed <= int(row["reviews_used"]):
            consumed = self.definitions.policy.consume(row["activity_id"], "fidelity_reviews")
        with self.database.transaction() as tx:
            fresh = self._row(tx, "SELECT * FROM service_registrations WHERE activity_id = ?", (row["activity_id"],))
            latest = self._row(tx, "SELECT * FROM service_registration_passes WHERE activity_id = ? ORDER BY pass_number DESC LIMIT 1", (row["activity_id"],))
            counted = tx.execute("SELECT 1 FROM service_registration_reviews WHERE run_id = ?", (current["run_id"],)).fetchone()
            pending = json.loads(fresh["pending_json"] or "{}")
            pending.pop("reviewer_run", None)
            if counted is None:
                rounds = consumed
                tx.execute(
                    "INSERT INTO service_registration_reviews VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (row["activity_id"], rounds, current["assignment_id"], current["run_id"],
                     f"{assignment['tool']}:{run_row.get('model_id') or assignment['model_id']} (tool {run_row.get('tool_version')})",
                     outcome, canonical_json({"findings": list(findings)}), latest["candidate_sha256"], latest["assessment_sha256"], int(fresh["review_limit"])),
                )
                tx.execute("UPDATE service_registrations SET reviews_used = ? WHERE activity_id = ?", (rounds, row["activity_id"]))
                fresh = self._row(tx, "SELECT * FROM service_registrations WHERE activity_id = ?", (row["activity_id"],))
            self._save_findings(tx, fresh, findings, "reviewer")
            latest_candidate = json.loads(latest["candidate_json"])
            latest_findings = json.loads(latest["findings_json"])["findings"]
            architect_blockers = [f for f in latest_findings if f["severity"] == "blocking"]
            if outcome == "APPROVE" and (latest_candidate["summary"]["assessment_outcome"] != "ready" or architect_blockers):
                tx.execute("UPDATE service_registrations SET state = 'blocked', pending_json = ? WHERE activity_id = ?", (canonical_json(pending), row["activity_id"]))
                text = (f"The review agrees with the assessment, and the assessment finds the sources not ready to register ({len(architect_blockers)} blocking finding(s)). "
                        "Blocking findings are returned to the project architect: correct the sources, cancel this attempt and register again. Nothing was published.")
                self._activity(tx, row["activity_id"], "paused", text, (ActivityAction(f"{row['activity_id']}-cancel", "Cancel registration", "action"),))
                self._say(tx, row["project_id"], row["activity_id"], text)
            elif outcome == "APPROVE":
                tx.execute("UPDATE service_registrations SET state = 'publishing', pending_json = ? WHERE activity_id = ?", (canonical_json(pending), row["activity_id"]))
                self._activity(tx, row["activity_id"], "publishing", "Review passed; publishing the candidate package to GitHub")
                self._say(tx, row["project_id"], row["activity_id"], f"Independent review round {fresh['reviews_used']} of {fresh['review_limit']}: approved with {len(findings)} non-blocking finding(s).")
            elif int(fresh["reviews_used"]) < int(fresh["review_limit"]):
                tx.execute("UPDATE service_registrations SET state = 'architect', pending_json = ? WHERE activity_id = ?", (canonical_json(pending), row["activity_id"]))
                self._activity(tx, row["activity_id"], "assessing", f"Review round {fresh['reviews_used']} of {fresh['review_limit']} requested changes; the architect is amending")
                self._say(tx, row["project_id"], row["activity_id"], f"Independent review round {fresh['reviews_used']} of {fresh['review_limit']} requested changes ({len(findings)} finding(s)).")
            else:
                tx.execute("UPDATE service_registrations SET state = 'limit_paused', pending_json = ? WHERE activity_id = ?", (canonical_json(pending), row["activity_id"]))
                self._limit_message(tx, fresh)

    def _limit_pause(self, row: Mapping[str, Any]) -> None:
        with self.database.transaction() as tx:
            tx.execute("UPDATE service_registrations SET state = 'limit_paused' WHERE activity_id = ?", (row["activity_id"],))
            self._limit_message(tx, self._row(tx, "SELECT * FROM service_registrations WHERE activity_id = ?", (row["activity_id"],)))

    def _limit_message(self, tx: Transaction, row: Mapping[str, Any]) -> None:
        text = f"Review limit reached: {row['reviews_used']} of {row['review_limit']} rounds used and blocking findings remain. Registration is paused for an Owner decision; it is not approved and the count is not reset."
        self._activity(tx, row["activity_id"], "paused", text, (ActivityAction(f"{row['activity_id']}-cancel", "Cancel registration", "action"),))
        self._say(tx, row["project_id"], row["activity_id"], text)

    def _pause(self, row: Mapping[str, Any], reason: str) -> None:
        with self.database.transaction() as tx:
            tx.execute("UPDATE service_registrations SET state = 'paused', note = ? WHERE activity_id = ?", (reason[:500], row["activity_id"]))
            self._activity(tx, row["activity_id"], "paused", f"Paused: {reason[:300]}", (ActivityAction(f"{row['activity_id']}-cancel", "Cancel registration", "action"),))
            self._say(tx, row["project_id"], row["activity_id"], f"Registration paused: {reason[:400]}")

    # -- publication and confirmation

    def _advance_publish(self, row: Mapping[str, Any]) -> None:
        activity_id = row["activity_id"]
        profile = self._profile_of(row)
        destination = self._destination(profile)
        operation_id = f"{activity_id}-candidate-{row['pass_number']}-{row['reviews_used']}"
        op = self._read("SELECT * FROM service_registration_publications WHERE operation_id = ?", (operation_id,))
        latest = self._read("SELECT * FROM service_registration_passes WHERE activity_id = ? ORDER BY pass_number DESC LIMIT 1", (activity_id,))
        assert latest is not None
        if op is None:
            model = self._model(row, destination)
            scope = json.loads(row["scope_json"])
            candidate_id = row["candidate_id"] or f"cand-{uuid.uuid4().hex[:10]}"
            reviews = self._reviews(activity_id)
            candidate = json.loads(latest["candidate_json"])
            assessment = json.loads(latest["assessment_json"])
            profile_snapshot = json.loads(row["profile_json"])
            selection = {
                "source_repository": row["repository"], "source_ref": row["source_ref"], "source_commit": row["source_commit"],
                "source_provenance": row["source_provenance"], "publication_branch": row["publication_branch"], "branch_provenance": row["branch_provenance"],
                "resolved_at": row["selected_at"], "repository_profile_snapshot": profile_snapshot,
                "authority": f"Owner {self.owner_id} through the CLI request that started this registration and the intake answers recorded as decisions",
            }
            decisions = self._decisions(activity_id)
            findings = json.loads(latest["findings_json"])["findings"]
            review_inputs = [
                {"round": int(r["review_round"]), "assignment_id": r["assignment_id"], "run_id": r["run_id"], "reviewer_identity": r["reviewer_identity"],
                 "limit": int(r["review_limit"]), "outcome": r["outcome"], "findings": json.loads(r["findings_json"])["findings"],
                 "content_hash": "", "covers_final": r["candidate_sha256"] == latest["candidate_sha256"] and r["assessment_sha256"] == latest["assessment_sha256"]}
                for r in reviews
            ]
            files, manifest, manifest_path = build_package(
                project_id=row["project_id"], registration_version=int(row["registration_version"]), candidate_id=candidate_id,
                repository=row["repository"], source_ref=row["source_ref"], source_commit=row["source_commit"], publication_branch=row["publication_branch"],
                decision_version=int(row["decision_version"]), model=model, scope=scope, candidate=candidate, assessment=assessment, findings=findings,
                decisions=[{"subject": d["subject"], "question": d["question_text"], "answers": [{"answer_id": d["question_id"], "author": d["authority"], "text": d["answer_text"], "time": d["created_at"]}], "resolution": d["resolution"], "authority": d["authority"]} for d in decisions],
                selection=selection, reviews=review_inputs, assessment_run={"assignment_id": latest["assignment_id"], "run_id": latest["run_id"]},
                previous_ref=self._active_package(row["project_id"]),
            )
            try:
                validate_package(files, manifest_path, row["source_commit"], scope)
            except CandidateError as error:
                self._pause(row, f"the frozen candidate failed validation: {error}")
                return
            manifest_bytes = files[manifest_path]
            with self.database.transaction() as tx:
                tx.execute("UPDATE service_registrations SET candidate_id = ? WHERE activity_id = ?", (candidate_id, activity_id))
                tx.execute(
                    "INSERT INTO service_registration_publications(operation_id, activity_id, kind, repository, branch, files_json, state, profile_json) VALUES (?, ?, 'candidate', ?, ?, ?, 'prepared', ?)",
                    (operation_id, activity_id, row["repository"], row["publication_branch"],
                     canonical_json({"files": {p: sha256(d) for p, d in files.items()}, "manifest_path": manifest_path, "manifest_sha256": sha256(manifest_bytes)}), row["profile_json"]),
                )
            self._frozen(operation_id, files)
            op = self._read("SELECT * FROM service_registration_publications WHERE operation_id = ?", (operation_id,))
        assert op is not None
        files = self._frozen(operation_id)
        frozen = json.loads(op["files_json"])
        if op["state"] in {"prepared", "writing"}:
            destination.check_publication_branch(row["repository"], row["publication_branch"])
            with self.database.transaction() as tx:
                tx.execute("UPDATE service_registration_publications SET state = 'writing' WHERE operation_id = ?", (operation_id,))
            commit = destination.publish(row["repository"], row["publication_branch"], files, f"Publish registration candidate {frozen['manifest_path'].split('/')[-2]} (version {row['registration_version']})")
            destination.verify_files(row["repository"], commit, files)
            with self.database.transaction() as tx:
                tx.execute("UPDATE service_registration_publications SET state = 'verified', commit_sha = ? WHERE operation_id = ?", (commit, operation_id))
            op = self._read("SELECT * FROM service_registration_publications WHERE operation_id = ?", (operation_id,))
        assert op is not None
        manifest = json.loads(files[frozen["manifest_path"]])
        reference = package_reference(row["repository"], op["commit_sha"], manifest, frozen["manifest_path"], files[frozen["manifest_path"]])
        comparison = self._comparison(row, files, frozen["manifest_path"])
        with self.database.transaction() as tx:
            tx.execute("UPDATE service_registration_publications SET state = 'applied' WHERE operation_id = ?", (operation_id,))
            if comparison is not None:
                fresh = self._row(tx, "SELECT pending_json FROM service_registrations WHERE activity_id = ?", (activity_id,))
                kept = json.loads(fresh["pending_json"] or "{}")
                kept["comparison"] = comparison
                tx.execute("UPDATE service_registrations SET pending_json = ? WHERE activity_id = ?", (canonical_json(kept), activity_id))
                self._say(tx, row["project_id"], activity_id, self._comparison_text(comparison))
            tx.execute("UPDATE service_registrations SET state = 'ready', package_json = ? WHERE activity_id = ?", (canonical_json(reference), activity_id))
            self._activity(tx, activity_id, "ready", f"Candidate {reference['candidate_id']} (version {reference['registration_version']}) is published and reviewed; awaiting your confirmation",
                           self._ready_actions(activity_id, reference))
            self._say(tx, row["project_id"], activity_id,
                      f"Candidate {reference['candidate_id']} published to {reference['repository']} at commit {reference['commit'][:12]} ({reference['manifest_path']}). Inspect it, then confirm or cancel registration.")

    def _ready_actions(self, activity_id: str, package: Mapping[str, Any]) -> tuple[ActivityAction, ...]:
        label = f"Confirm registration of candidate {package['candidate_id']} (version {package['registration_version']})"
        return (
            ActivityAction(f"{activity_id}-confirm", label, "decision"),
            ActivityAction(f"{activity_id}-cancel", "Cancel registration", "action"),
        )

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

    def _check_source(self, row: Mapping[str, Any]) -> None:
        """Before confirmation, show relevant input changes: symbolic refs only, documents the review used only."""
        pending = json.loads(row["pending_json"] or "{}")
        checked = pending.get("source_checked_at", 0)
        now = datetime.now(timezone.utc).timestamp()
        if now - checked < 20 or not str(row["source_ref"]).startswith("refs/"):
            return
        destination = self._destination(self._profile_of(row))
        _, head, _ = destination.resolve_source(row["repository"], row["source_ref"])
        pending["source_checked_at"] = now
        changed: list[str] = []
        if head != row["source_commit"] and pending.get("source_checked") != {"commit": head}:
            model = self._model(row, destination)
            for path in model.documents:
                if destination.read_file(row["repository"], head, path) != destination.read_file(row["repository"], row["source_commit"], path):
                    changed.append(path)
        with self.database.transaction() as tx:
            if not changed:
                tx.execute("UPDATE service_registrations SET pending_json = ? WHERE activity_id = ?", (canonical_json(pending), row["activity_id"]))
                return
            pending["latest"] = {"commit": head, "documents": changed}
            fresh = self._row(tx, "SELECT * FROM service_registrations WHERE activity_id = ?", (row["activity_id"],))
            tx.execute("UPDATE service_registrations SET pending_json = ?, state = 'source_changed' WHERE activity_id = ?", (canonical_json(pending), row["activity_id"]))
            fresh = self._row(tx, "SELECT * FROM service_registrations WHERE activity_id = ?", (row["activity_id"],))
            self._ask(tx, fresh, "source_change", "Planning inputs changed during review",
                      f"Planning documents changed after the reviewed commit {row['source_commit'][:12]}: {', '.join(changed)} (now at {head[:12]}). "
                      "Retain the reviewed source, or include the updated source and recheck affected findings within the existing review budget (the review count is not reset).",
                      self._source_choices())
            tx.execute("UPDATE service_registrations SET state = 'source_changed' WHERE activity_id = ?", (row["activity_id"],))

    def _advance_confirm(self, row: Mapping[str, Any]) -> None:
        activity_id = row["activity_id"]
        operation_id = f"{activity_id}-confirm"
        op = self._read("SELECT * FROM service_registration_publications WHERE operation_id = ?", (operation_id,))
        assert op is not None
        destination = self._destination(self._profile_of(row))
        pending = json.loads(row["pending_json"] or "{}")["confirmation"]
        package = json.loads(row["package_json"])
        if op["state"] == "prepared":
            head = destination.head(row["repository"], row["publication_branch"])
            index_path = f"{ROOT}/index.json"
            previous = destination.read_file(row["repository"], head, index_path)
            files, reference = receipt_and_index(
                project_id=row["project_id"], confirmation_id=pending["confirmation_id"], request_id=pending["request_id"], package_ref=package,
                owner_id=self.owner_id, confirmed_at=pending["confirmed_at"], previous_confirmation_ref=self._active_receipt(row["project_id"]), previous_index=json.loads(previous) if previous else None,
            )
            with self.database.transaction() as tx:
                tx.execute("UPDATE service_registration_publications SET files_json = ?, state = 'writing' WHERE operation_id = ?",
                           (canonical_json({"files": {p: sha256(d) for p, d in files.items()}, "reference": reference}), operation_id))
            self._frozen(operation_id, files)
            op = self._read("SELECT * FROM service_registration_publications WHERE operation_id = ?", (operation_id,))
            assert op is not None
        if op["state"] == "writing":
            files = self._frozen(operation_id)
            destination.check_publication_branch(row["repository"], row["publication_branch"])
            head = destination.head(row["repository"], row["publication_branch"])
            index_path = f"{ROOT}/index.json"
            if destination.read_file(row["repository"], head, index_path) is not None and destination.read_file(row["repository"], head, index_path) != files[index_path]:
                # The index moved since the receipt was prepared: rebuild on the current index; the receipt bytes stay identical.
                previous = json.loads(destination.read_file(row["repository"], head, index_path))
                if not any(r["path"].endswith(f"{pending['confirmation_id']}.json") for r in previous["confirmation_refs"]):
                    files, _ = receipt_and_index(
                        project_id=row["project_id"], confirmation_id=pending["confirmation_id"], request_id=pending["request_id"], package_ref=package,
                        owner_id=self.owner_id, confirmed_at=pending["confirmed_at"], previous_confirmation_ref=previous["current_confirmation_ref"], previous_index=previous,
                    )
                    self._frozen(operation_id, files)
            commit = destination.publish(row["repository"], row["publication_branch"], files, f"Confirm registration {package['candidate_id']} (version {package['registration_version']})", frozenset({index_path}))
            destination.verify_files(row["repository"], commit, files)
            with self.database.transaction() as tx:
                tx.execute("UPDATE service_registration_publications SET state = 'verified', commit_sha = ? WHERE operation_id = ?", (commit, operation_id))
            op = self._read("SELECT * FROM service_registration_publications WHERE operation_id = ?", (operation_id,))
            assert op is not None
        if op["state"] == "verified":
            self._activate(row, op, package, pending)

    def _activate(self, row: Mapping[str, Any], op: Mapping[str, Any], package: Mapping[str, Any], pending: Mapping[str, Any]) -> None:
        activity_id, project_id = row["activity_id"], row["project_id"]
        frozen = json.loads(op["files_json"])
        confirmation = {"confirmation_id": pending["confirmation_id"], "receipt": frozen["reference"], "commit": op["commit_sha"], "repository": row["repository"]}
        with self.database.transaction() as tx:
            tx.execute("UPDATE service_registration_publications SET state = 'applied' WHERE operation_id = ?", (op["operation_id"],))
            tx.execute("UPDATE service_registrations SET state = 'confirmed', confirmation_json = ? WHERE activity_id = ?", (canonical_json(confirmation), activity_id))
            tx.execute(
                "INSERT INTO service_registration_active(project_id, activity_id, package_json, confirmation_json, activated_at) VALUES (?, ?, ?, ?, ?) "
                "ON CONFLICT(project_id) DO UPDATE SET activity_id = excluded.activity_id, package_json = excluded.package_json, confirmation_json = excluded.confirmation_json, activated_at = excluded.activated_at",
                (project_id, activity_id, canonical_json(package), canonical_json(confirmation), _now()),
            )
            project = self._row(tx, "SELECT * FROM service_projects WHERE project_id = ?", (project_id,))
            self.records.update_project(tx, ProjectRecord(project_id, project["name"], "registered", int(project["version"]) + 1), expected_record_version=int(project["version"]))
            self._activity(tx, activity_id, "completed", f"Registered: candidate {package['candidate_id']} (version {package['registration_version']}) is active; no development was started", (), ended=True)
            self.reservations.release(tx, project_id, activity_id)
            tx.execute("UPDATE service_request_results SET status = 'completed' WHERE request_id = ?", (pending["request_id"],))
            self._say(tx, project_id, activity_id, f"Registered. Receipt {confirmation['receipt']['path']} verified on GitHub at commit {op['commit_sha'][:12]}; the package is active. No development was started.")
            self._emit(tx, project_id, activity_id, "registration.confirmed", {"activity_id": activity_id, "package_ref": dict(package)})

    # -- cancellation

    def _advance_cancel(self, row: Mapping[str, Any]) -> None:
        activity_id = row["activity_id"]
        pending = json.loads(row["pending_json"] or "{}")
        if self.runs is not None:
            for role in ("architect", "reviewer"):
                current = pending.get(f"{role}_run")
                if current is None:
                    continue
                view = self.runs.view(current["run_id"])
                if view.state in {"reserved", "running", "stopping"}:
                    view = self.runs.stop(current["run_id"], "registration_cancelled")
                if view.state in {"reserved", "running", "stopping", "blocked"}:
                    with self.database.transaction() as tx:
                        self._activity(tx, activity_id, "cancelling", "Stop unconfirmed: the agent run has not been confirmed stopped; the attempt stays open")
                    return
        publications = self._read("SELECT COUNT(*) AS n FROM service_registration_publications WHERE activity_id = ? AND state IN ('prepared', 'writing')", (activity_id,))
        if publications and publications["n"]:
            return  # a write is in flight: reconcile it before ending
        with self.database.transaction() as tx:
            tx.execute("UPDATE service_registrations SET state = 'cancelled' WHERE activity_id = ?", (activity_id,))
            for qid, info in pending.get("questions", {}).items():
                q = self._row(tx, "SELECT * FROM service_questions WHERE question_id = ?", (qid,))
                if q is not None and q["status"] in {"awaiting_answer", "clarification_required"}:
                    self.records.update_question(tx, QuestionRecord(qid, q["project_id"], q["activity_id"], q["subject"], q["prompt"], q["requester"], "cancelled", int(q["version"]) + 1), expected_record_version=int(q["version"]))
                    tx.execute("INSERT INTO entity_versions(entity_id, version) VALUES (?, ?) ON CONFLICT(entity_id) DO UPDATE SET version = excluded.version", (qid, int(q["version"]) + 1))
            project = self._row(tx, "SELECT * FROM service_projects WHERE project_id = ?", (row["project_id"],))
            active = tx.execute("SELECT 1 FROM service_registration_active WHERE project_id = ?", (row["project_id"],)).fetchone()
            restored = "registered" if active else "not_registered"
            if project["registration_status"] != restored:
                self.records.update_project(tx, ProjectRecord(row["project_id"], project["name"], restored, int(project["version"]) + 1), expected_record_version=int(project["version"]))
            self._activity(tx, activity_id, "cancelled", "Registration cancelled; saved findings and decisions are retained", (), ended=True)
            self.reservations.release(tx, row["project_id"], activity_id)
            if pending.get("cancel_request_id"):
                tx.execute("UPDATE service_request_results SET status = 'completed' WHERE request_id = ?", (pending["cancel_request_id"],))
            self._say(tx, row["project_id"], activity_id, "Registration cancelled. Saved history, findings and any published candidate are retained.")
            self._emit(tx, row["project_id"], activity_id, "registration.cancelled", {"activity_id": activity_id})

    # ----------------------------------------------------------------- records

    def _save_findings(self, tx: Transaction, row: Mapping[str, Any], findings, source: str) -> None:
        marker = f"{row['activity_id']}-{source[:1]}{row['pass_number']}-{row['reviews_used']}"
        for finding in findings:
            detail = (f"{finding['explanation']} Impact: {finding['impact']} Requested correction: {finding['requested_correction']} "
                      + " ".join(f"[{s['path']}:{s.get('line') or s.get('heading') or s.get('locator')}]" for s in finding["source_refs"]))
            finding_id = f"{marker}-{finding['local_key']}"
            if tx.execute("SELECT 1 FROM service_findings WHERE finding_id = ?", (finding_id,)).fetchone() is None:
                self.records.create_finding(tx, FindingRecord(finding_id, row["project_id"], row["activity_id"], f"{'Architect' if source == 'architect' else 'Reviewer'}: {finding['subject']}", detail, finding["severity"], 1))
        self._supersede(tx, row["activity_id"], source, marker)

    def _supersede(self, tx: Transaction, activity_id: str, source: str, keep_marker: str) -> None:
        """Findings from an earlier pass or round stay on record but are marked superseded once a newer one exists."""
        prefix = f"{activity_id}-{source[:1]}"
        for row in tx.execute("SELECT finding_id, project_id, subject, detail, status, version FROM service_findings WHERE activity_id = ? AND finding_id LIKE ? AND status IN ('blocking', 'non_blocking')",
                              (activity_id, prefix + "%")).fetchall():
            if str(row[0]).startswith(keep_marker + "-"):
                continue
            self.records.update_finding(tx, FindingRecord(row[0], row[1], activity_id, row[2], row[3], "superseded", int(row[5]) + 1), expected_record_version=int(row[5]))

    def _say(self, tx: Transaction, project_id: str, activity_id: str, text: str) -> None:
        self.records.append_conversation(tx, ConversationRecord(f"registration-{uuid.uuid4().hex}", project_id, "maestro", "status", text, _now(), activity_id))
        self._emit(tx, project_id, activity_id, "registration.updated", {"activity_id": activity_id})

    def _activity(self, tx: Transaction, activity_id: str, state: str | None, waiting: str | None, actions: tuple[ActivityAction, ...] | None = None, *, ended: bool = False, version: int | None = None) -> None:
        current = self._row(tx, "SELECT * FROM service_activities WHERE activity_id = ?", (activity_id,))
        assert current is not None
        existing = tuple(ActivityAction(r[0], r[1], r[2]) for r in tx.execute("SELECT action_id, label, kind FROM service_activity_actions WHERE activity_id = ? ORDER BY sequence", (activity_id,)).fetchall())
        record_version = int(current["version"])
        next_version = record_version + 1 if version is None else version
        if version is not None and version != record_version + 1:
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
            (f"registration-{uuid.uuid4().hex}", _now(), project_id, activity_id, event_type, canonical_json(data)),
        )

    # ------------------------------------------------------------------ reads

    def view(self, activity_id: str) -> dict[str, Any] | None:
        """The registration as the CLI shows it: selections, roles, review count, candidate and confirmation."""
        row = self._read("SELECT * FROM service_registrations WHERE activity_id = ?", (activity_id,))
        if row is None:
            return None
        version = self._read("SELECT version FROM entity_versions WHERE entity_id = ?", (activity_id,))
        active = self._read("SELECT package_json FROM service_registration_active WHERE project_id = ?", (row["project_id"],))
        return {
            "activity_id": activity_id, "project_id": row["project_id"], "state": row["state"], "activity_version": None if version is None else int(version["version"]),
            "repository": row["repository"], "overview_path": row["overview_path"], "scope": json.loads(row["scope_json"]),
            "source": {"ref": row["source_ref"], "commit": row["source_commit"], "provenance": row["source_provenance"]},
            "publication": {"branch": row["publication_branch"], "provenance": row["branch_provenance"]},
            "roles": {"architect": {"tool": row["architect_tool"], "model": row["architect_model"]}, "reviewer": {"tool": row["reviewer_tool"], "model": row["reviewer_model"]}},
            "review": {"used": int(row["reviews_used"]), "limit": int(row["review_limit"])},
            "registration_version": int(row["registration_version"]), "candidate_id": row["candidate_id"],
            "package_ref": None if row["package_json"] is None else json.loads(row["package_json"]),
            "confirmation": None if row["confirmation_json"] is None else json.loads(row["confirmation_json"]),
            "active_package_ref": None if active is None else json.loads(active["package_json"]),
            "comparison": json.loads(row["pending_json"] or "{}").get("comparison"),
            "note": row["note"],
        }

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

    def _project_row(self, project_id: str) -> dict[str, Any] | None:
        return self._read("SELECT * FROM service_projects WHERE project_id = ?", (project_id,))

    def _project_of(self, tx: Transaction, activity_id: str) -> str:
        return str(tx.execute("SELECT project_id FROM service_activities WHERE activity_id = ?", (activity_id,)).fetchone()[0])

    def _active_package(self, project_id: str) -> dict[str, Any] | None:
        active = self._read("SELECT package_json FROM service_registration_active WHERE project_id = ?", (project_id,))
        return None if active is None else json.loads(active["package_json"])

    def _active_receipt(self, project_id: str) -> dict[str, Any] | None:
        active = self._read("SELECT confirmation_json FROM service_registration_active WHERE project_id = ?", (project_id,))
        return None if active is None else json.loads(active["confirmation_json"])["receipt"]

    def _active_selection(self, project_id: str) -> dict[str, Any] | None:
        """The registration row of the project's active version, whose selections a re-registration inherits."""
        return self._read(
            "SELECT r.* FROM service_registrations r JOIN service_registration_active a ON a.activity_id = r.activity_id WHERE a.project_id = ?",
            (project_id,),
        )

    def _comparison(self, row: Mapping[str, Any], files: Mapping[str, bytes], manifest_path: str) -> dict[str, Any] | None:
        """Additions, changes and removals of the candidate against the active version, with reasons from findings and decisions."""
        active = self._read("SELECT package_json, activity_id FROM service_registration_active WHERE project_id = ?", (row["project_id"],))
        if active is None:
            return None
        previous = json.loads(active["package_json"])
        destination = self._destination(self._profile_of(row))
        old_manifest = json.loads(destination.read_file(row["repository"], previous["commit"], previous["manifest_path"]))
        new_manifest = json.loads(files[manifest_path])
        kinds = {"milestone", "requirement", "declaration", "summary"}

        def records(manifest: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
            return {f"{f['record_type']}:{f['record_id']}": f for f in manifest["files"] if f["record_type"] in kinds}

        before, after = records(old_manifest), records(new_manifest)
        base_old = previous["manifest_path"].rsplit("/", 1)[0]
        base_new = manifest_path.rsplit("/", 1)[0]

        def body(base: str, entry: Mapping[str, Any], reader) -> Any:
            return json.loads(reader(f"{base}/{entry['path']}"))["data"]

        def content(base: str, entry: Mapping[str, Any], reader) -> Any:
            """The record's data without source locations, which move with every source commit."""
            stripped = json.loads(json.dumps(body(base, entry, reader)))

            def drop(value: Any) -> Any:
                if isinstance(value, dict):
                    return {k: drop(v) for k, v in value.items() if k != "source_refs"}
                if isinstance(value, list):
                    return [drop(v) for v in value]
                return value

            return drop(stripped)

        old_reader = lambda path: destination.read_file(row["repository"], previous["commit"], path)
        new_reader = lambda path: files[path]
        added, removed, changed = [], [], []
        for key in sorted(after.keys() - before.keys()):
            added.append({"record": key, "subject": after[key]["subject"], "version": after[key]["record_version"]})
        for key in sorted(before.keys() - after.keys()):
            removed.append({"record": key, "subject": before[key]["subject"], "version": before[key]["record_version"]})
        for key in sorted(before.keys() & after.keys()):
            if before[key]["record_version"] != after[key]["record_version"] or content(base_old, before[key], old_reader) != content(base_new, after[key], new_reader):
                changed.append({"record": key, "subject": after[key]["subject"], "version_before": before[key]["record_version"], "version_after": after[key]["record_version"]})
        old_scope = body(base_old, before["summary:summary"], old_reader)["scope"] if "summary:summary" in before else None
        new_scope = body(base_new, after["summary:summary"], new_reader)["scope"] if "summary:summary" in after else None
        scope: dict[str, Any] = {}
        if old_scope is not None and new_scope is not None:
            was, now = {i["reference"] for i in old_scope["included"]}, {i["reference"] for i in new_scope["included"]}
            scope = {"now_included": sorted(now - was), "no_longer_included": sorted(was - now)}
        old_profile = json.loads(self._read("SELECT profile_json FROM service_registrations WHERE activity_id = ?", (active["activity_id"],))["profile_json"])
        profile_change = None if old_profile == json.loads(row["profile_json"]) else {"before": old_profile, "after": json.loads(row["profile_json"])}
        completion = [c for c in changed + added + removed if c["record"] == "requirement:project-completion"]
        reasons = [{"decision": d["subject"], "resolution": d["resolution"]} for d in self._decisions(row["activity_id"])]
        latest = self._latest_pass(row["activity_id"])
        if latest is not None:
            reasons += [{"finding": f.get("subject") or f.get("summary") or f.get("title"), "severity": f.get("severity")} for f in json.loads(latest["findings_json"])["findings"]]
        return {
            "active_version": int(previous["registration_version"]), "active_candidate": previous["candidate_id"], "active_commit": previous["commit"],
            "candidate_version": int(new_manifest["registration_version"]), "added": added, "changed": changed, "removed": removed,
            "scope": scope, "completion_requirement_changed": bool(completion), "profile_change": profile_change, "reasons": reasons,
        }

    @staticmethod
    def _comparison_text(comparison: Mapping[str, Any]) -> str:
        parts = [f"Compared with active version {comparison['active_version']} ({comparison['active_candidate']}): "
                 f"{len(comparison['added'])} added, {len(comparison['changed'])} changed, {len(comparison['removed'])} removed."]
        for label, key in (("Added", "added"), ("Changed", "changed"), ("Removed", "removed")):
            if comparison[key]:
                parts.append(f"{label}: " + "; ".join(item["subject"] for item in comparison[key]) + ".")
        scope = comparison["scope"]
        if scope.get("now_included"):
            parts.append("Now in scope: " + ", ".join(scope["now_included"]) + ".")
        if scope.get("no_longer_included"):
            parts.append("No longer in scope: " + ", ".join(scope["no_longer_included"]) + ".")
        if comparison["completion_requirement_changed"]:
            parts.append("The project completion requirement changed.")
        if comparison["profile_change"]:
            parts.append("The repository profile changed; it becomes active only with this confirmation.")
        if comparison["reasons"]:
            parts.append("Reasons: " + "; ".join(str(r.get("decision") or r.get("finding")) for r in comparison["reasons"][:6]) + ".")
        return " ".join(parts)

    def _open_registration(self, project_id: str, tx: Transaction | None = None) -> str | None:
        sql = f"SELECT activity_id FROM service_registrations WHERE project_id = ? AND state IN ({','.join('?' for _ in _OPEN_STATES)}) ORDER BY created_at DESC LIMIT 1"
        params = (project_id, *_OPEN_STATES)
        found = self._row(tx, sql, params) if tx is not None else self._read(sql, params)
        return None if found is None else str(found["activity_id"])

    def _decisions(self, activity_id: str) -> list[dict[str, Any]]:
        return self._rows("SELECT * FROM service_registration_decisions WHERE activity_id = ? ORDER BY decision_id", (activity_id,))

    def _reviews(self, activity_id: str) -> list[dict[str, Any]]:
        return self._rows("SELECT * FROM service_registration_reviews WHERE activity_id = ? ORDER BY review_round", (activity_id,))

    def _latest_pass(self, activity_id: str) -> dict[str, Any] | None:
        return self._read("SELECT * FROM service_registration_passes WHERE activity_id = ? ORDER BY pass_number DESC LIMIT 1", (activity_id,))
