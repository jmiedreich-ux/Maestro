"""Installed request and read composition for confirmed registration."""

from __future__ import annotations

import hashlib
import json
import os
import stat
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Callable, Mapping

from maestro.agents.preflight import AgentRoutePreflight
from maestro.agents.routes import RoleSelections, ToolModelSelection
from maestro.agents.supervisor import SupervisionError
from maestro.foundation import (
    Command,
    Database,
    DomainMigration,
    Event,
    Transaction,
    canonical_json,
)
from maestro.foundation.credentials import RepositoryAuthorizer, ServiceGitTransport
from maestro.foundation.git_publication import (
    PublicationAccessError,
    PublicationConflictError,
    PublicationError,
    PublicationJournal,
    PublicationStateError,
)
from maestro.foundation.github_destination import (
    GitHubDestination,
    GitHubDestinationError,
    GitHubDestinationProvider,
    GitHubDestinationRouter,
    destination_providers,
)
from maestro.planning.intake import (
    IntakeError,
    IntakeQuestion,
    RegistrationIntake,
    RegistrationIntakeRequest,
    RegistrationIntakeResult,
)
from maestro.planning.registration_confirmation import (
    ConfirmationResult,
    OwnerConfirmation,
    RegistrationConfirmationError,
    RegistrationConfirmationService,
    RegistrationPackageReference,
)
from maestro.planning.registration_plugin import RegistrationServiceBinding
from maestro.planning.registration_recovery import (
    HistoricalPublicationRoute,
    HistoricalDestinationProfiles,
    RegistrationRecoveryError,
    RegistrationRecoveryService,
)
from maestro.planning.registration import RegistrationAssessment, RegistrationAssessmentError
from maestro.planning.registration_records import (
    ArtifactReference,
    canonical_record_bytes,
    validate_registration_package,
)
from maestro.planning.sources import ExactSourceReader

from .activities import ActivityAction, ActivityRecord, ActivityRepository, ProjectRecord
from .authentication import VerifiedActor
from .processes import ProcessSnapshot
from .questions import DeliveredAnswer, LinkedQuestion, QuestionService
from .receipts import ReceiptRepository
from .registry import OperationHandler, OperationResult, PreparedOperation
from .requests import RequestEnvelope, RequestRejection


REGISTRATION_COMPOSITION_MIGRATION = DomainMigration(
    domain="registration_composition",
    version=1,
    identity="installed-registration-composition-v1",
    statements=(
        """
        CREATE TABLE installed_registration_intake(
            activity_id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            request_id TEXT NOT NULL UNIQUE,
            request_json TEXT NOT NULL,
            intake_json TEXT,
            state TEXT NOT NULL CHECK(state IN (
                'waiting_for_intake', 'assessment_started', 'cancelled'
            ))
        )
        """,
        """
        CREATE TABLE installed_registration_intake_questions(
            question_id TEXT PRIMARY KEY,
            activity_id TEXT NOT NULL
                REFERENCES installed_registration_intake(activity_id),
            field TEXT NOT NULL,
            UNIQUE(activity_id, field)
        )
        """,
    ),
)

REGISTRATION_COMPOSITION_RECOVERY_MIGRATION = DomainMigration(
    domain="registration_composition",
    version=2,
    identity="installed-registration-agent-recovery-v2",
    statements=(
        """
        CREATE TABLE installed_registration_agent_failures(
            activity_id TEXT PRIMARY KEY,
            role TEXT NOT NULL CHECK(role IN ('project_architect', 'fidelity_reviewer')),
            assignment_id TEXT NOT NULL,
            failed_run_id TEXT NOT NULL,
            reason TEXT NOT NULL,
            state TEXT NOT NULL CHECK(state IN ('paused', 'retrying', 'resolved')),
            automatic_limit INTEGER NOT NULL CHECK(automatic_limit >= 0),
            automatic_consumed INTEGER NOT NULL DEFAULT 0 CHECK(automatic_consumed >= 0),
            manual_consumed INTEGER NOT NULL DEFAULT 0 CHECK(manual_consumed >= 0)
        )
        """,
        """
        CREATE TABLE installed_registration_agent_retry_requests(
            request_id TEXT PRIMARY KEY,
            activity_id TEXT NOT NULL,
            assignment_id TEXT NOT NULL,
            failed_run_id TEXT NOT NULL,
            replacement_run_id TEXT NOT NULL,
            kind TEXT NOT NULL CHECK(kind IN ('automatic', 'manual')),
            intervention TEXT,
            state TEXT NOT NULL CHECK(state IN ('reserved', 'launched', 'failed'))
        )
        """,
    ),
)

REGISTRATION_COMPOSITION_AUTOMATIC_RECOVERY_MIGRATION = DomainMigration(
    domain="registration_composition",
    version=3,
    identity="installed-registration-automatic-recovery-v3",
    statements=(
        """ALTER TABLE installed_registration_agent_failures
           ADD COLUMN failed_launch_evidence INTEGER NOT NULL DEFAULT 0
               CHECK(failed_launch_evidence IN (0, 1))""",
        """
        CREATE TABLE installed_registration_publication_failures(
            operation_id TEXT PRIMARY KEY,
            activity_id TEXT NOT NULL,
            reason TEXT NOT NULL,
            state TEXT NOT NULL CHECK(state IN ('paused', 'retrying', 'resolved')),
            automatic_limit INTEGER NOT NULL CHECK(automatic_limit >= 0),
            automatic_consumed INTEGER NOT NULL DEFAULT 0
                CHECK(automatic_consumed >= 0)
        )
        """,
        """
        CREATE TABLE installed_registration_publication_retry_requests(
            request_id TEXT PRIMARY KEY,
            activity_id TEXT NOT NULL,
            operation_id TEXT NOT NULL,
            kind TEXT NOT NULL CHECK(kind IN ('automatic', 'manual')),
            state TEXT NOT NULL CHECK(state IN (
                'reserved', 'dispatched', 'completed', 'failed'
            )),
            failure TEXT
        )
        """,
    ),
)

REGISTRATION_COMPOSITION_OWNER_DECISION_MIGRATION = DomainMigration(
    domain="registration_composition",
    version=4,
    identity="installed-registration-owner-review-decisions-v4",
    statements=(
        """
        CREATE TABLE installed_registration_owner_decisions(
            decision_id TEXT PRIMARY KEY,
            request_id TEXT UNIQUE,
            project_id TEXT NOT NULL,
            activity_id TEXT NOT NULL,
            question_id TEXT NOT NULL UNIQUE,
            decision_version INTEGER NOT NULL CHECK(decision_version >= 1),
            target TEXT NOT NULL CHECK(target = 'fidelity_review'),
            assignment_id TEXT NOT NULL,
            reason TEXT NOT NULL,
            base_limit INTEGER NOT NULL CHECK(base_limit >= 1),
            used_attempts INTEGER NOT NULL CHECK(used_attempts >= 0),
            prior_grants INTEGER NOT NULL CHECK(prior_grants >= 0),
            choice TEXT CHECK(choice IN ('grant_one', 'remain_paused')),
            state TEXT NOT NULL CHECK(state IN ('pending', 'completed'))
        )
        """,
        """
        CREATE TABLE installed_registration_review_grants(
            decision_id TEXT PRIMARY KEY
                REFERENCES installed_registration_owner_decisions(decision_id),
            activity_id TEXT NOT NULL,
            assignment_id TEXT NOT NULL,
            state TEXT NOT NULL CHECK(state IN ('unconsumed', 'reserved', 'consumed'))
        )
        """,
    ),
)

REGISTRATION_COMPOSITION_SOURCE_CHOICE_MIGRATION = DomainMigration(
    domain="registration_composition",
    version=5,
    identity="installed-registration-source-consistency-v5",
    statements=(
        """
        CREATE TABLE installed_registration_source_choices(
            request_id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            activity_id TEXT NOT NULL,
            source_ref TEXT NOT NULL,
            reviewed_commit TEXT NOT NULL,
            observed_commit TEXT NOT NULL,
            changed_paths_json TEXT NOT NULL,
            choice TEXT NOT NULL CHECK(choice IN (
                'retain_reviewed_source', 'include_updated_source'
            )),
            state TEXT NOT NULL CHECK(state IN ('retained', 'reassessment_started'))
        )
        """,
    ),
)

REGISTRATION_COMPOSITION_CANCELLATION_MIGRATION = DomainMigration(
    domain="registration_composition",
    version=6,
    identity="installed-registration-cancellation-intent-v6",
    statements=(
        """
        CREATE TABLE installed_registration_cancellations(
            activity_id TEXT PRIMARY KEY,
            request_id TEXT NOT NULL UNIQUE,
            project_id TEXT NOT NULL,
            operation_id TEXT,
            state TEXT NOT NULL CHECK(state IN ('stopping', 'cancelled')),
            failure TEXT
        )
        """,
    ),
)


def registration_composition_migrations() -> tuple[DomainMigration, ...]:
    return (
        REGISTRATION_COMPOSITION_MIGRATION,
        REGISTRATION_COMPOSITION_RECOVERY_MIGRATION,
        REGISTRATION_COMPOSITION_AUTOMATIC_RECOVERY_MIGRATION,
        REGISTRATION_COMPOSITION_OWNER_DECISION_MIGRATION,
        REGISTRATION_COMPOSITION_SOURCE_CHOICE_MIGRATION,
        REGISTRATION_COMPOSITION_CANCELLATION_MIGRATION,
    )


@dataclass(frozen=True)
class RegistrationRuntimeDependencies:
    """Typed installed dependencies; secrets remain behind their providers."""

    source_reader: ExactSourceReader
    authorizer: RepositoryAuthorizer
    transport: ServiceGitTransport
    destination_provider: GitHubDestination
    preflight: AgentRoutePreflight
    process_snapshot: ProcessSnapshot
    remote_for_repository: Callable[[str], str]
    workspace_root: Path | None = None
    assignment_launcher: Callable[[RegistrationServiceBinding, RegistrationAssessment, str], None] | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.source_reader, ExactSourceReader):
            raise TypeError("registration runtime requires ExactSourceReader")
        if not isinstance(self.authorizer, RepositoryAuthorizer):
            raise TypeError("registration runtime requires RepositoryAuthorizer")
        if not isinstance(self.transport, ServiceGitTransport):
            raise TypeError("registration runtime requires ServiceGitTransport")
        if not isinstance(
            self.destination_provider,
            (GitHubDestinationProvider, GitHubDestinationRouter),
        ):
            raise TypeError("registration runtime requires GitHubDestinationProvider")
        if not isinstance(self.preflight, AgentRoutePreflight):
            raise TypeError("registration runtime requires configured route preflight")
        if (
            not isinstance(self.process_snapshot, ProcessSnapshot)
            or self.process_snapshot.process_name != "registration"
        ):
            raise TypeError("registration runtime requires registration process snapshot")
        if not callable(self.remote_for_repository):
            raise TypeError("registration runtime requires a remote resolver")
        if self.workspace_root is not None and (
            not isinstance(self.workspace_root, Path)
            or not self.workspace_root.is_absolute()
        ):
            raise ValueError("registration workspace root must be absolute")
        if self.assignment_launcher is not None and not callable(self.assignment_launcher):
            raise TypeError("registration assignment launcher must be callable")


class _CollectedQuestions:
    def __init__(self) -> None:
        self.values: list[IntakeQuestion] = []

    def publish_intake_question(self, question: IntakeQuestion) -> None:
        if not isinstance(question, IntakeQuestion):
            raise TypeError("registration intake question is invalid")
        self.values.append(question)


class RegistrationCoordinator:
    """Join reviewed registration domains at the installed application boundary."""

    def __init__(
        self,
        database: Database,
        records: ActivityRepository,
        questions: QuestionService,
        binding: RegistrationServiceBinding,
        owner_id: str,
        dependencies: RegistrationRuntimeDependencies | None,
        confirmation: RegistrationConfirmationService | None,
        recovery: RegistrationRecoveryService | None,
        configuration_error: str | None = None,
    ) -> None:
        self.database = database
        self.records = records
        self.questions = questions
        self.binding = binding
        self.owner_id = owner_id
        self.dependencies = dependencies
        self.confirmation = confirmation
        self.recovery = recovery
        self.configuration_error = configuration_error
        self.intake = (
            None
            if dependencies is None
            else RegistrationIntake(
                dependencies.source_reader,
                dependencies.authorizer,
                dependencies.transport,
                dependencies.destination_provider,
            )
        )
        if dependencies is not None and callable(
            getattr(dependencies.assignment_launcher, "connect_failure_listener", None)
        ):
            dependencies.assignment_launcher.connect_failure_listener(
                self._assignment_failed
            )
        self.binding.connect_assessment_listener(self._assessment_changed)

    @property
    def operation_handlers(self) -> tuple[OperationHandler, ...]:
        return (
            OperationHandler("registration.start", self.prepare_start),
            OperationHandler("registration.confirm", self.prepare_confirm),
            OperationHandler("registration.cancel", self.prepare_cancel),
            OperationHandler("registration.retry", self.prepare_retry),
            OperationHandler("owner.decision", self.prepare_owner_decision),
            OperationHandler("registration.source-choice", self.prepare_source_choice),
        )

    def receive_answer(self, answer: DeliveredAnswer) -> None:
        """Route a committed linked answer back to its saved registration."""
        with self.database.read_connection() as connection:
            intake_question = connection.execute(
                """SELECT 1 FROM installed_registration_intake_questions
                   WHERE question_id = ?""",
                (answer.question_id,),
            ).fetchone()
        if intake_question is not None:
            self._receive_intake_answer(answer)
            return
        self.binding.receive_answer(answer)

    def prepare_start(self, request: RequestEnvelope) -> PreparedOperation:
        if request.activity_id is not None or request.question_id is not None:
            raise ValueError(
                "registration.start creates its activity and does not accept question context"
            )
        if request.expected_version not in {None, 0}:
            raise ValueError("registration.start expected_version must be zero or null")
        allowed = {
            "repository", "overview_path", "referenced_paths", "source_ref",
            "publication_branch", "scope", "architect_selection",
            "reviewer_selection",
        }
        if set(request.payload) - allowed or "repository" not in request.payload:
            raise ValueError("registration.start payload fields do not match the contract")
        repository = _text(request.payload["repository"], "repository").lower()
        project_id = _project_id(repository)
        if request.project_id is not None and request.project_id != project_id:
            raise ValueError(
                "registration project does not match the repository identity"
            )
        with self.database.read_connection() as connection:
            unfinished = connection.execute(
                """SELECT activity_id, version FROM service_activities
                   WHERE project_id = ? AND kind = 'registration'
                     AND state NOT IN ('completed', 'cancelled', 'failed')
                   ORDER BY rowid DESC LIMIT 1""",
                (project_id,),
            ).fetchone()
            attempt_number = int(
                connection.execute(
                    """SELECT COUNT(*) FROM service_activities
                       WHERE project_id = ? AND kind = 'registration'""",
                    (project_id,),
                ).fetchone()[0]
            ) + 1
            active_registration_row = connection.execute(
                "SELECT confirmation_id FROM active_registrations WHERE project_id = ?",
                (project_id,),
            ).fetchone()
            active_registration = active_registration_row is not None
            active_confirmation_id = (
                None
                if active_registration_row is None
                else str(active_registration_row[0])
            )
            active_intake_row = connection.execute(
                """SELECT intake.intake_json
                   FROM active_registrations AS active
                   JOIN registration_confirmations AS confirmation
                     ON confirmation.confirmation_id = active.confirmation_id
                   JOIN registration_assessment_intake AS intake
                     ON intake.activity_id = confirmation.activity_id
                   WHERE active.project_id = ?""",
                (project_id,),
            ).fetchone()
        if unfinished is not None:
            existing_activity = str(unfinished[0])

            def open_existing(
                _transaction: Transaction, _next_version: int
            ) -> OperationResult:
                return OperationResult(
                    data={
                        "project_id": project_id,
                        "activity_id": existing_activity,
                        "state": "existing_registration",
                    },
                    status="accepted",
                    project_id=project_id,
                    activity_id=existing_activity,
                )

            return PreparedOperation(
                entity_id=_open_entity_id(request.request_id),
                event_type="registration.opened",
                event_data={
                    "project_id": project_id,
                    "activity_id": existing_activity,
                },
                apply=open_existing,
            )
        dependencies = self._require_runtime()
        activity_id = _activity_id(request.request_id)
        payload = dict(request.payload)
        overview_path = _optional_text(payload.get("overview_path"))
        referenced = payload.get("referenced_paths", [])
        if not isinstance(referenced, list) or any(
            not isinstance(item, str) or not item for item in referenced
        ):
            raise ValueError("registration referenced_paths must be an array of paths")
        active_intake = (
            None
            if active_intake_row is None
            else RegistrationIntakeResult.from_json(str(active_intake_row[0]))
        )
        branch = _optional_text(payload.get("publication_branch"))
        if branch is None and active_intake is not None:
            branch = active_intake.publication_branch
        source_ref = _optional_text(payload.get("source_ref"))
        prior_source_ref = (
            active_intake.source_ref
            if source_ref is None and active_intake is not None
            else None
        )
        remote = "" if branch is None else dependencies.remote_for_repository(repository)
        intake_request = RegistrationIntakeRequest(
            repository=repository,
            remote=remote,
            overview_path=overview_path,
            referenced_paths=tuple(referenced),
            source_ref=source_ref,
            prior_source_ref=prior_source_ref,
            publication_branch=branch,
            scope=_optional_text(payload.get("scope")),
            architect_selection=_selection_text(payload.get("architect_selection")),
            reviewer_selection=_selection_text(payload.get("reviewer_selection")),
        )
        intake = RegistrationIntakeResult(
            None, (), None, intake_request.scope, None, None, None,
            source_ref=intake_request.source_ref,
            publication_branch=intake_request.publication_branch,
            repository=repository,
        )

        def apply(transaction: Transaction, next_version: int) -> OperationResult:
            current_active = transaction.execute(
                "SELECT confirmation_id FROM active_registrations WHERE project_id = ?",
                (project_id,),
            ).fetchone()
            current_confirmation_id = (
                None if current_active is None else str(current_active[0])
            )
            if current_confirmation_id != active_confirmation_id:
                raise ValueError(
                    "active registration changed before the registration start was reserved"
                )
            if active_registration:
                if self.recovery is None:
                    raise ValueError("installed re-registration recovery is not configured")
                self.recovery.reserve_intake_in(transaction, project_id, activity_id)
            existing = transaction.execute(
                "SELECT name, version FROM service_projects WHERE project_id = ?",
                (project_id,),
            ).fetchone()
            if existing is None:
                self.records.create_project(
                    transaction,
                    ProjectRecord(project_id, repository, "registering", 1),
                )
            elif transaction.execute(
                "SELECT 1 FROM active_registrations WHERE project_id = ?",
                (project_id,),
            ).fetchone() is None:
                self.records.update_project(
                    transaction,
                    ProjectRecord(
                        project_id,
                        str(existing[0]),
                        "registering",
                        int(existing[1]) + 1,
                    ),
                    expected_record_version=int(existing[1]),
                )
            self.records.create_activity(
                transaction,
                ActivityRecord(
                    activity_id,
                    project_id,
                    "registration",
                    f"Register {repository}",
                    "waiting",
                    next_version,
                    waiting_reason="Registration intake is reserved",
                    started_at=_utc_now(),
                    available_actions=(
                        ActivityAction(
                            "registration-cancel", "Cancel registration", "decision"
                        ),
                    ),
                ),
            )
            transaction.execute(
                "INSERT INTO entity_versions(entity_id, version) VALUES (?, ?)",
                (activity_id, next_version),
            )
            _save_process_snapshot(
                transaction, activity_id, dependencies.process_snapshot
            )
            transaction.execute(
                """INSERT INTO installed_registration_intake(
                       activity_id, project_id, request_id, request_json,
                       intake_json, state
                   ) VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    activity_id,
                    project_id,
                    request.request_id,
                    canonical_json(_intake_request_record(intake_request)),
                    intake.to_json(),
                    "waiting_for_intake",
                ),
            )
            return OperationResult(
                data={
                    "project_id": project_id,
                    "activity_id": activity_id,
                    "state": "intake_reserved",
                },
                status="accepted",
                project_id=project_id,
                activity_id=activity_id,
            )

        return PreparedOperation(
            entity_id=_start_entity_id(project_id, attempt_number),
            event_type="registration.started",
            event_data={"project_id": project_id, "activity_id": activity_id},
            apply=apply,
            after_commit=lambda _result: self._continue_reserved_intake(activity_id),
        )

    def prepare_confirm(self, request: RequestEnvelope) -> PreparedOperation:
        confirmation = self._require_confirmation()
        if request.project_id is None or request.activity_id is None:
            raise ValueError("registration.confirm requires project and activity context")
        if request.question_id is not None or request.expected_version is None:
            raise ValueError("registration.confirm requires an exact activity version")
        if set(request.payload) != {"confirmation_id", "package_ref", "confirmed_at"}:
            raise ValueError("registration.confirm payload fields do not match the contract")
        action = OwnerConfirmation(
            _text(request.payload["confirmation_id"], "confirmation_id"),
            request.request_id,
            request.project_id,
            request.activity_id,
            request.expected_version,
            RegistrationPackageReference.from_mapping(request.payload["package_ref"]),
            _text(request.payload["confirmed_at"], "confirmed_at"),
        )
        assessment = self.binding.assessment(request.activity_id)
        consistency, _updated_intake = self._source_consistency(assessment)
        if consistency["state"] == "changed" and not self._has_retained_source_choice(
            request.activity_id,
            str(consistency["reviewed_commit"]),
            str(consistency["observed_commit"]),
        ):
            raise ValueError(
                "relevant symbolic source changed; explicitly retain the reviewed source "
                "or include the updated source for reassessment"
            )
        actor = VerifiedActor(self.owner_id)
        with self.database.read_connection() as connection:
            recovery_attempt = connection.execute(
                "SELECT 1 FROM registration_recovery_attempts WHERE activity_id = ?",
                (request.activity_id,),
            ).fetchone()
        try:
            if recovery_attempt is not None:
                if self.recovery is None:
                    raise ValueError("installed registration recovery is not configured")
                result = self.recovery.confirm_replacement(
                    request.activity_id, confirmation, assessment, actor, action
                )
            else:
                result = confirmation.confirm(assessment, actor, action)
        except (
            GitHubDestinationError,
            PublicationError,
            RegistrationConfirmationError,
            RegistrationRecoveryError,
        ) as error:
            with self.database.read_connection() as connection:
                pending = connection.execute(
                    """SELECT operation_id FROM registration_confirmations
                       WHERE request_id = ? AND activity_id = ? AND state = 'pending'""",
                    (request.request_id, request.activity_id),
                ).fetchone()
            if pending is None:
                raise
            self._recover_publication_automatically(
                assessment, str(pending[0]), str(error)
            )
            active = confirmation.active(request.project_id)
            if active is None or active.package_ref != action.package_ref:
                raise RegistrationConfirmationError(
                    "automatic confirmation recovery did not activate the exact candidate"
                ) from error
            result = active

        def apply(transaction: Transaction, next_version: int) -> OperationResult:
            return self._finalize_confirmation_in(
                transaction,
                request.activity_id,
                request.project_id,
                request.expected_version,
                next_version,
                result,
            )

        return PreparedOperation(
            entity_id=request.activity_id,
            event_type="registration.confirmed",
            event_data={"confirmation_id": action.confirmation_id},
            apply=apply,
        )

    def prepare_cancel(self, request: RequestEnvelope) -> PreparedOperation:
        self._require_confirmation()
        if request.project_id is None or request.activity_id is None:
            raise ValueError("registration.cancel requires project and activity context")
        if request.question_id is not None or request.expected_version is None:
            raise ValueError("registration.cancel requires an exact activity version")
        if set(request.payload) - {"operation_id"}:
            raise ValueError("registration.cancel payload fields do not match the contract")
        with self.database.read_connection() as connection:
            confirmed = connection.execute(
                """SELECT 1 FROM registration_confirmations
                   WHERE activity_id = ? AND state = 'confirmed' LIMIT 1""",
                (request.activity_id,),
            ).fetchone()
        if confirmed is not None:
            raise ValueError("a confirmed registration cannot be cancelled")
        with self.database.read_connection() as connection:
            pending_confirmation = connection.execute(
                """SELECT 1 FROM registration_confirmations
                   WHERE activity_id = ? AND state = 'pending' LIMIT 1""",
                (request.activity_id,),
            ).fetchone()
        if pending_confirmation is not None:
            raise ValueError(
                "a pending confirmation must be reconciled before cancellation"
            )
        operation_id = _optional_text(request.payload.get("operation_id"))

        def apply(transaction: Transaction, next_version: int) -> OperationResult:
            row = _activity_row(transaction, request.activity_id)
            transaction.execute(
                """INSERT INTO installed_registration_cancellations(
                       activity_id, request_id, project_id, operation_id, state, failure
                   ) VALUES (?, ?, ?, ?, 'stopping', NULL)""",
                (
                    request.activity_id, request.request_id, request.project_id,
                    operation_id,
                ),
            )
            self.records.update_activity(
                transaction,
                ActivityRecord(
                    request.activity_id,
                    request.project_id,
                    "registration",
                    str(row[1]),
                    "stopping",
                    next_version,
                    started_at=None if row[3] is None else str(row[3]),
                    waiting_reason="Stopping the active registration work.",
                    available_actions=(),
                ),
                expected_record_version=request.expected_version,
            )
            return OperationResult(
                data={"state": "stopping"},
                status="accepted",
                project_id=request.project_id,
                activity_id=request.activity_id,
            )

        return PreparedOperation(
            entity_id=request.activity_id,
            event_type="registration.cancellation-requested",
            event_data={"activity_id": request.activity_id},
            apply=apply,
            after_commit=lambda _result: self._continue_registration_cancellation(
                request.activity_id
            ),
        )

    def prepare_retry(self, request: RequestEnvelope) -> PreparedOperation:
        confirmation = self._require_confirmation()
        if request.project_id is None or request.activity_id is None:
            raise ValueError("registration.retry requires project and activity context")
        if request.question_id is not None or request.expected_version is None:
            raise ValueError("registration.retry requires an exact activity version")
        if set(request.payload) == {"assignment_id", "failed_run_id", "intervention"}:
            return self._prepare_agent_retry(request)
        if set(request.payload) != {"publication_operation_id", "intervention"}:
            raise ValueError(
                "registration.retry requires an exact publication or agent failure identity and intervention"
            )
        operation_id = _text(
            request.payload["publication_operation_id"],
            "publication_operation_id",
        )
        intervention = _text(request.payload["intervention"], "intervention")
        with self.database.read_connection() as connection:
            candidate = connection.execute(
                """SELECT state FROM registration_candidate_publications
                   WHERE operation_id = ? AND activity_id = ?""",
                (operation_id, request.activity_id),
            ).fetchone()
            pending_confirmation = connection.execute(
                """SELECT state FROM registration_confirmations
                   WHERE operation_id = ? AND activity_id = ?""",
                (operation_id, request.activity_id),
            ).fetchone()
        if candidate is None and pending_confirmation is None:
            raise ValueError(
                "publication retry operation does not belong to this registration"
            )
        if (
            candidate is not None and str(candidate[0]) == "published"
        ) or (
            pending_confirmation is not None
            and str(pending_confirmation[0]) == "confirmed"
        ):
            raise ValueError("publication retry operation is already complete")
        with self.database.read_connection() as connection:
            recovery_attempt = connection.execute(
                "SELECT 1 FROM registration_recovery_attempts WHERE activity_id = ?",
                (request.activity_id,),
            ).fetchone()
        recovered_candidate = candidate is not None
        update_recovery = recovery_attempt is not None and recovered_candidate
        if update_recovery:
            if self.recovery is None:
                raise ValueError("installed registration recovery is not configured")
            dependencies = self._require_runtime()
            if dependencies.workspace_root is None:
                raise ValueError("installed registration workspace is not configured")
            assessment = self.binding.assessment(request.activity_id)
            ready = assessment.require_ready_candidate()
            manifest, records = _load_candidate_workspace(
                dependencies.workspace_root, assessment, ready.path, ready.sha256
            )
            active = confirmation.active(request.project_id)
            if active is None:
                raise ValueError("re-registration retry has no active registration")
            package = self.recovery.recover_candidate_publication(
                request.activity_id,
                confirmation,
                assessment,
                activity_version=request.expected_version,
                manifest=manifest,
                records=records,
                remote=dependencies.remote_for_repository(
                    assessment.context.package_context.source_repository
                ),
                expected_parent=active.remote_commit,
                operation_id=operation_id,
                publication_request_id=(
                    f"registration-publication-{request.activity_id}-{ready.version}"
                ),
                retry_request_id=request.request_id,
                automatic=False,
                intervention=intervention,
            )
            self.recovery.record_candidate_from_saved_reasons(
                request.activity_id, package
            )
            recovered: object = ({"kind": "candidate", "state": "published"},)
        else:
            recovered = confirmation.recover_pending(
                request.activity_id,
                reserved_operation_ids=frozenset((operation_id,)),
            )

        def apply(transaction: Transaction, next_version: int) -> OperationResult:
            row = _activity_row(transaction, request.activity_id)
            self.records.update_activity(
                transaction,
                ActivityRecord(
                    request.activity_id,
                    request.project_id,
                    "registration",
                    str(row[1]),
                    "waiting" if recovered_candidate else str(row[2]),
                    next_version,
                    waiting_reason=(
                        "Exact reviewed candidate is ready for confirmation"
                        if recovered_candidate
                        else None
                    ),
                    started_at=None if row[3] is None else str(row[3]),
                    available_actions=(
                        (
                            ActivityAction(
                                "registration-confirm",
                                "Confirm registration",
                                "decision",
                            ),
                            ActivityAction(
                                "registration-cancel",
                                "Cancel registration",
                                "decision",
                            ),
                        )
                        if recovered_candidate
                        else ()
                    ),
                ),
                expected_record_version=request.expected_version,
            )
            if recovered_candidate:
                transaction.execute(
                    """UPDATE registration_candidate_publications
                       SET activity_version = ? WHERE operation_id = ?""",
                    (next_version, operation_id),
                )
            return OperationResult(
                data={
                    "publication_operation_id": operation_id,
                    "intervention": intervention,
                    "recovered": recovered,
                },
                project_id=request.project_id,
                activity_id=request.activity_id,
            )

        return PreparedOperation(
            entity_id=request.activity_id,
            event_type="registration.retried",
            event_data={"activity_id": request.activity_id},
            apply=apply,
        )

    def _prepare_agent_retry(self, request: RequestEnvelope) -> PreparedOperation:
        assert request.project_id is not None and request.activity_id is not None
        assert request.expected_version is not None
        assignment_id = _text(request.payload["assignment_id"], "assignment_id")
        failed_run_id = _text(request.payload["failed_run_id"], "failed_run_id")
        intervention = _text(request.payload["intervention"], "intervention")
        with self.database.read_connection() as connection:
            row = connection.execute(
                """SELECT role, assignment_id, failed_run_id, state,
                          automatic_limit, automatic_consumed, manual_consumed
                   FROM installed_registration_agent_failures
                   WHERE activity_id = ?""",
                (request.activity_id,),
            ).fetchone()
        if row is None or str(row[3]) != "paused":
            raise ValueError("registration has no paused agent failure to retry")
        if (str(row[1]), str(row[2])) != (assignment_id, failed_run_id):
            raise ValueError("agent retry does not match the displayed failed assignment")
        role = str(row[0])
        assessment = self.binding.assessment(request.activity_id)
        failed = assessment.current_run(role)
        if (failed.assignment_id, failed.run_id) != (assignment_id, failed_run_id):
            raise ValueError("agent retry failure is no longer the current saved run")
        try:
            observed = self.binding.poll_current_agent(assessment, role)
        except SupervisionError as error:
            raise ValueError(
                f"agent retry cannot prove the failed run is terminal: {error}"
            ) from error
        else:
            if observed.state not in {
                "completed", "failed", "cancelled", "timed_out", "stalled", "stopped"
            }:
                raise ValueError(
                    f"agent retry is blocked until the failed run is terminal ({observed.state})"
                )
        replacement_run_id = f"{role}-run-{uuid.uuid4().hex}"

        def apply(transaction: Transaction, next_version: int) -> OperationResult:
            current = transaction.execute(
                """SELECT state, assignment_id, failed_run_id, manual_consumed
                   FROM installed_registration_agent_failures
                   WHERE activity_id = ?""",
                (request.activity_id,),
            ).fetchone()
            if current is None or (
                str(current[0]), str(current[1]), str(current[2])
            ) != ("paused", assignment_id, failed_run_id):
                raise ValueError("agent retry failure changed before reservation")
            replacement = self.binding.retry_technical_in(
                transaction, assessment, role, failed, replacement_run_id
            )
            transaction.execute(
                """INSERT INTO installed_registration_agent_retry_requests(
                       request_id, activity_id, assignment_id, failed_run_id,
                       replacement_run_id, kind, intervention, state
                   ) VALUES (?, ?, ?, ?, ?, 'manual', ?, 'reserved')""",
                (
                    request.request_id,
                    request.activity_id,
                    assignment_id,
                    failed_run_id,
                    replacement.run_id,
                    intervention,
                ),
            )
            transaction.execute(
                """UPDATE installed_registration_agent_failures
                   SET state = 'retrying', manual_consumed = manual_consumed + 1
                   WHERE activity_id = ?""",
                (request.activity_id,),
            )
            activity = _activity_row(transaction, request.activity_id)
            self.records.update_activity(
                transaction,
                ActivityRecord(
                    request.activity_id,
                    request.project_id,
                    "registration",
                    str(activity[1]),
                    "running",
                    next_version,
                    waiting_reason="Retrying the saved agent assignment",
                    started_at=None if activity[3] is None else str(activity[3]),
                    available_actions=(
                        ActivityAction(
                            "registration-cancel", "Cancel registration", "decision"
                        ),
                    ),
                ),
                expected_record_version=request.expected_version,
            )
            return OperationResult(
                data={
                    "assignment_id": assignment_id,
                    "failed_run_id": failed_run_id,
                    "replacement_run_id": replacement.run_id,
                    "intervention": intervention,
                    "automatic_limit": int(row[4]),
                    "automatic_consumed": int(row[5]),
                    "manual_consumed": int(current[3]) + 1,
                },
                project_id=request.project_id,
                activity_id=request.activity_id,
            )

        def after_commit(_result: OperationResult) -> None:
            launched = self._launch_assignment(assessment, role)
            with self.database.transaction() as transaction:
                transaction.execute(
                    """UPDATE installed_registration_agent_retry_requests
                       SET state = ? WHERE request_id = ?""",
                    ("launched" if launched else "failed", request.request_id),
                )

        return PreparedOperation(
            entity_id=request.activity_id,
            event_type="registration.agent-retried",
            event_data={
                "activity_id": request.activity_id,
                "assignment_id": assignment_id,
                "failed_run_id": failed_run_id,
            },
            apply=apply,
            after_commit=after_commit,
        )

    def prepare_owner_decision(self, request: RequestEnvelope) -> PreparedOperation:
        """Apply the shared Owner-decision contract for registration review grants."""
        if request.project_id is None or request.activity_id is None:
            raise ValueError("owner.decision requires project and activity context")
        if request.question_id is None or request.expected_version is None:
            raise ValueError("owner.decision requires a linked question and exact activity version")
        fields = {
            "decision_id", "decision_version", "target", "assignment_id", "choice",
        }
        if set(request.payload) != fields:
            raise ValueError("owner.decision payload fields do not match the contract")
        decision_id = _text(request.payload["decision_id"], "decision_id")
        target = _text(request.payload["target"], "target")
        assignment_id = _text(request.payload["assignment_id"], "assignment_id")
        choice = _text(request.payload["choice"], "choice")
        decision_version = request.payload["decision_version"]
        if (
            isinstance(decision_version, bool)
            or not isinstance(decision_version, int)
            or decision_version < 1
        ):
            raise ValueError("owner.decision decision_version must be positive")
        if target != "fidelity_review" or choice not in {"grant_one", "remain_paused"}:
            raise ValueError("owner.decision target or choice is invalid for registration")
        with self.database.read_connection() as connection:
            saved = connection.execute(
                """SELECT project_id, activity_id, question_id, decision_version,
                          target, assignment_id, state
                   FROM installed_registration_owner_decisions
                   WHERE decision_id = ?""",
                (decision_id,),
            ).fetchone()
        if saved is None:
            raise ValueError("owner.decision is not linked to a pending registration decision")
        expected = (
            request.project_id,
            request.activity_id,
            request.question_id,
            decision_version,
            target,
            assignment_id,
            "pending",
        )
        if tuple(saved) != expected:
            raise ValueError("owner.decision context is stale or differs from the pending decision")
        assessment = self.binding.assessment(request.activity_id)

        def apply(transaction: Transaction, next_version: int) -> OperationResult:
            current = transaction.execute(
                """SELECT state, decision_version, assignment_id
                   FROM installed_registration_owner_decisions
                   WHERE decision_id = ? AND activity_id = ?""",
                (decision_id, request.activity_id),
            ).fetchone()
            if current is None or tuple(current) != (
                "pending", decision_version, assignment_id
            ):
                raise ValueError("owner.decision changed before it could be applied")
            row = _activity_row(transaction, request.activity_id)
            if int(row[4]) != request.expected_version:
                raise ValueError("owner.decision activity version changed")
            if choice == "grant_one":
                self.binding.grant_one_review_in(transaction, assessment)
                transaction.execute(
                    """INSERT INTO installed_registration_review_grants(
                           decision_id, activity_id, assignment_id, state
                       ) VALUES (?, ?, ?, 'unconsumed')""",
                    (decision_id, request.activity_id, assignment_id),
                )
                state = "running"
                reason = "One additional fidelity review was granted for this exact registration."
                actions = (
                    ActivityAction(
                        "registration-cancel", "Cancel registration", "decision"
                    ),
                )
            else:
                state = "paused"
                reason = "Registration remains paused at its fidelity-review limit."
                actions = (
                    ActivityAction(
                        "registration-cancel", "Cancel registration", "decision"
                    ),
                )
            transaction.execute(
                """UPDATE installed_registration_owner_decisions
                   SET request_id = ?, choice = ?, state = 'completed'
                   WHERE decision_id = ? AND state = 'pending'""",
                (request.request_id, choice, decision_id),
            )
            self.records.update_activity(
                transaction,
                ActivityRecord(
                    request.activity_id,
                    request.project_id,
                    "registration",
                    str(row[1]),
                    state,
                    next_version,
                    waiting_reason=reason,
                    started_at=None if row[3] is None else str(row[3]),
                    available_actions=actions,
                ),
                expected_record_version=request.expected_version,
            )
            return OperationResult(
                data={
                    "decision_id": decision_id,
                    "decision_version": decision_version,
                    "target": target,
                    "choice": choice,
                    "grant_state": "unconsumed" if choice == "grant_one" else None,
                },
                project_id=request.project_id,
                activity_id=request.activity_id,
            )

        def after_commit(_result: OperationResult) -> None:
            if choice == "grant_one":
                self._assessment_changed(assessment)

        return PreparedOperation(
            entity_id=request.activity_id,
            event_type="owner.decision-recorded",
            event_data={"decision_id": decision_id, "target": target, "choice": choice},
            apply=apply,
            after_commit=after_commit,
        )

    def prepare_source_choice(self, request: RequestEnvelope) -> PreparedOperation:
        if request.project_id is None or request.activity_id is None:
            raise ValueError("registration.source-choice requires project and activity context")
        if request.question_id is not None or request.expected_version is None:
            raise ValueError("registration.source-choice requires an exact activity version")
        if set(request.payload) != {"choice", "reviewed_commit", "observed_commit"}:
            raise ValueError("registration.source-choice payload fields do not match the contract")
        choice = _text(request.payload["choice"], "choice")
        if choice not in {"retain_reviewed_source", "include_updated_source"}:
            raise ValueError("registration source choice is invalid")
        assessment = self.binding.assessment(request.activity_id)
        consistency, updated_intake = self._source_consistency(assessment)
        if consistency["state"] != "changed":
            raise ValueError("registration source has no relevant change requiring a choice")
        reviewed_commit = _text(request.payload["reviewed_commit"], "reviewed_commit")
        observed_commit = _text(request.payload["observed_commit"], "observed_commit")
        if (
            reviewed_commit != consistency["reviewed_commit"]
            or observed_commit != consistency["observed_commit"]
        ):
            raise ValueError("registration source choice is stale")
        replacement: RegistrationAssessment | None = None
        selections: RoleSelections | None = None
        if choice == "include_updated_source":
            replacement, selections = self.binding.prepare_source_update(
                assessment, updated_intake
            )

        def apply(transaction: Transaction, next_version: int) -> OperationResult:
            row = _activity_row(transaction, request.activity_id)
            if int(row[4]) != request.expected_version:
                raise ValueError("registration source choice activity version changed")
            transaction.execute(
                """INSERT INTO installed_registration_source_choices(
                       request_id, project_id, activity_id, source_ref,
                       reviewed_commit, observed_commit, changed_paths_json,
                       choice, state
                   ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    request.request_id,
                    request.project_id,
                    request.activity_id,
                    assessment.context.source_inventory.source_ref,
                    reviewed_commit,
                    observed_commit,
                    canonical_json(consistency["changed_paths"]),
                    choice,
                    (
                        "retained"
                        if choice == "retain_reviewed_source"
                        else "reassessment_started"
                    ),
                ),
            )
            if replacement is not None:
                assert selections is not None
                self.binding.replace_source_update_in(
                    transaction, replacement, updated_intake, selections
                )
                state = "running"
                reason = "Updated source is being reassessed within the saved review budget."
            else:
                state = "waiting"
                reason = "The Owner retained the exact reviewed source after inspecting the update."
            self.records.update_activity(
                transaction,
                ActivityRecord(
                    request.activity_id,
                    request.project_id,
                    "registration",
                    str(row[1]),
                    state,
                    next_version,
                    waiting_reason=reason,
                    started_at=None if row[3] is None else str(row[3]),
                    available_actions=(
                        ActivityAction(
                            "registration-cancel", "Cancel registration", "decision"
                        ),
                    )
                    if replacement is not None
                    else (
                        ActivityAction(
                            "registration-confirm", "Confirm registration", "decision"
                        ),
                        ActivityAction(
                            "registration-cancel", "Cancel registration", "decision"
                        ),
                    ),
                ),
                expected_record_version=request.expected_version,
            )
            return OperationResult(
                data={
                    "choice": choice,
                    "reviewed_commit": reviewed_commit,
                    "observed_commit": observed_commit,
                    "changed_paths": consistency["changed_paths"],
                },
                project_id=request.project_id,
                activity_id=request.activity_id,
            )

        def after_commit(_result: OperationResult) -> None:
            if replacement is not None:
                self.binding.adopt_source_update(replacement)
                self._launch_assignment(replacement, "project_architect")

        return PreparedOperation(
            entity_id=request.activity_id,
            event_type="registration.source-choice-recorded",
            event_data={"choice": choice, "observed_commit": observed_commit},
            apply=apply,
            after_commit=after_commit,
        )

    def detail(self, activity_id: str) -> dict[str, object]:
        with self.database.read_connection() as connection:
            activity = connection.execute(
                """SELECT project_id, state, version FROM service_activities
                   WHERE activity_id = ? AND kind = 'registration'""",
                (activity_id,),
            ).fetchone()
            if activity is None:
                raise RequestRejection(
                    404, "registration_not_found", "the registration was not found"
                )
            candidate = connection.execute(
                """SELECT package_ref_json FROM registration_candidate_publications
                   WHERE activity_id = ? AND state = 'published'
                   ORDER BY registration_version DESC LIMIT 1""",
                (activity_id,),
            ).fetchone()
            assessment = connection.execute(
                "SELECT state_json FROM registration_assessment_state WHERE activity_id = ?",
                (activity_id,),
            ).fetchone()
            comparison = connection.execute(
                """SELECT comparison_json FROM registration_recovery_attempts
                   WHERE activity_id = ?""",
                (activity_id,),
            ).fetchone()
            agent_failure = connection.execute(
                """SELECT assignment_id, failed_run_id, role, reason,
                          automatic_limit, automatic_consumed, manual_consumed, state
                   FROM installed_registration_agent_failures
                   WHERE activity_id = ?""",
                (activity_id,),
            ).fetchone()
            owner_decisions = connection.execute(
                """SELECT decision_id, question_id, decision_version, target,
                          assignment_id, reason, base_limit, used_attempts,
                          prior_grants, choice, state
                   FROM installed_registration_owner_decisions
                   WHERE activity_id = ? ORDER BY rowid""",
                (activity_id,),
            ).fetchall()
        package = None if candidate is None else json.loads(str(candidate[0]))
        activity_state = str(activity[1])
        state = activity_state
        ready = False
        if activity_state == "paused":
            state = "Paused"
        elif assessment is not None and activity_state not in {
            "completed", "cancelled", "failed"
        }:
            saved = json.loads(str(assessment[0]))
            state = str(saved.get("state", state)).replace("_", " ").title()
            ready = saved.get("state") == "ready"
        history = (
            []
            if self.confirmation is None
            else [item.as_dict() for item in self.confirmation.history(str(activity[0]))]
        )
        assessment_detail: dict[str, object] | None = None
        package_manifest: Mapping[str, object] | None = None
        package_records: list[dict[str, object]] = []
        provenance: dict[str, object] | None = None
        source_consistency: dict[str, object] | None = None
        live_assessment: RegistrationAssessment | None = None
        if package is not None:
            confirmation = self._require_confirmation()
            package_manifest, records = confirmation.package_detail(
                RegistrationPackageReference.from_mapping(package)
            )
            package_records = [
                {"path": path, **dict(record)}
                for path, record in sorted(records.items())
            ]
        try:
            live_assessment = self.binding.assessment(activity_id)
        except RegistrationAssessmentError:
            pass
        if live_assessment is not None:
            status = live_assessment.status
            saved_state = live_assessment.to_record()
            working_agent = None
            if status.state == "awaiting_architect":
                working_agent = "project_architect"
            elif status.state == "awaiting_reviewer":
                working_agent = "fidelity_reviewer"
            assessment_detail = {
                "current_step": status.state,
                "working_agent": working_agent,
                "review_round": status.review_count,
                "base_review_limit": status.base_review_limit,
                "review_grants": status.review_grants,
                "effective_review_limit": status.review_limit,
                "blockers": list(status.blockers),
                "architect_findings": saved_state["architect_findings"],
                "review_findings": saved_state["review_findings"],
            }
            candidate_ref = status.candidate
            if candidate_ref is not None:
                context = live_assessment.context
                provenance = {
                    "source_repository": context.package_context.source_repository,
                    "source_selection": self.binding.saved_intake_result(
                        activity_id
                    ).source_selection,
                    "source_ref": context.source_inventory.source_ref,
                    "source_commit": context.source_inventory.source_commit,
                    "publication_branch": context.package_context.publication_branch,
                    "destination_snapshot_reference": context.package_context.destination_snapshot_reference,
                    "selection_decision_ref": context.package_context.selection_decision_ref,
                    "architect_identity": context.architect_identity,
                    "reviewer_identity": context.reviewer_identity,
                }
            if ready:
                try:
                    source_consistency, _updated = self._source_consistency(live_assessment)
                except (IntakeError, GitHubDestinationError, ValueError) as error:
                    source_consistency = {
                        "state": "unavailable",
                        "reason": str(error),
                        "retained": False,
                    }
        source_allows_confirmation = (
            source_consistency is None
            or source_consistency.get("state") in {"exact_commit", "unchanged"}
            or bool(source_consistency.get("retained"))
        )
        return {
            "project_id": str(activity[0]),
            "activity_id": activity_id,
            "activity_version": int(activity[2]),
            "state": state,
            "package_ref": package,
            "comparison": (
                None
                if comparison is None or comparison[0] is None
                else json.loads(str(comparison[0]))
            ),
            "agent_retry": (
                None
                if agent_failure is None or str(agent_failure[7]) == "resolved"
                else {
                    "assignment_id": str(agent_failure[0]),
                    "failed_run_id": str(agent_failure[1]),
                    "role": str(agent_failure[2]),
                    "reason": str(agent_failure[3]),
                    "automatic_limit": int(agent_failure[4]),
                    "automatic_consumed": int(agent_failure[5]),
                    "manual_consumed": int(agent_failure[6]),
                    "state": str(agent_failure[7]),
                }
            ),
            "history": history,
            "owner_decisions": [
                {
                    "decision_id": str(row[0]),
                    "question_id": str(row[1]),
                    "decision_version": int(row[2]),
                    "target": str(row[3]),
                    "assignment_id": str(row[4]),
                    "reason": str(row[5]),
                    "base_limit": int(row[6]),
                    "used_attempts": int(row[7]),
                    "prior_grants": int(row[8]),
                    "choice": None if row[9] is None else str(row[9]),
                    "state": str(row[10]),
                }
                for row in owner_decisions
            ],
            "assessment": assessment_detail,
            "package_manifest": package_manifest,
            "package_records": package_records,
            "provenance": provenance,
            "source_consistency": source_consistency,
            "can_confirm": bool(
                ready
                and package is not None
                and source_allows_confirmation
                and activity_state not in {"completed", "cancelled", "failed"}
            ),
        }

    def rehydrate(self) -> dict[str, object]:
        """Restore independently recoverable state without hiding storage faults."""
        errors: list[dict[str, str]] = []
        try:
            restored = self.binding.rehydrate_saved()
        except RegistrationAssessmentError as error:
            restored = ()
            errors.append({"kind": "assessment", "message": str(error)})
        with self.database.read_connection() as connection:
            pending_cancellations = tuple(
                str(row[0]) for row in connection.execute(
                    """SELECT activity_id FROM installed_registration_cancellations
                       WHERE state = 'stopping' ORDER BY activity_id"""
                ).fetchall()
            )
        for activity_id in pending_cancellations:
            try:
                self._continue_registration_cancellation(activity_id)
            except (OSError, RuntimeError, TypeError, ValueError) as error:
                errors.append(
                    {
                        "kind": "registration cancellation",
                        "activity_id": activity_id,
                        "message": str(error),
                    }
                )
        with self.database.read_connection() as connection:
            pending_intakes = tuple(
                str(row[0]) for row in connection.execute(
                    """SELECT activity_id FROM installed_registration_intake
                       WHERE state = 'waiting_for_intake'
                         AND activity_id NOT IN (
                             SELECT activity_id FROM installed_registration_cancellations
                             WHERE state = 'stopping'
                         )
                       ORDER BY activity_id"""
                ).fetchall()
            )
        for activity_id in pending_intakes:
            try:
                self._continue_reserved_intake(activity_id)
            except (IntakeError, OSError, RuntimeError, TypeError, ValueError) as error:
                errors.append(
                    {
                        "kind": "registration intake",
                        "activity_id": activity_id,
                        "message": str(error),
                    }
                )
        recovered: tuple[dict[str, object], ...] = ()
        if self.confirmation is not None:
            recovered_items: list[dict[str, object]] = []
            with self.database.read_connection() as connection:
                pending_publications = tuple(
                    (str(row[0]), str(row[1]))
                    for row in connection.execute(
                        """SELECT operation_id, activity_id
                           FROM registration_candidate_publications
                           WHERE state = 'prepared'
                           UNION
                           SELECT operation_id, activity_id
                           FROM registration_confirmations
                           WHERE state = 'pending'
                           ORDER BY operation_id"""
                    ).fetchall()
                )
            for operation_id, activity_id in pending_publications:
                try:
                    assessment = self.binding.assessment(activity_id)
                    recovered_items.extend(
                        self._recover_publication_automatically(
                            assessment, operation_id,
                            "startup recovered an unfinished publication",
                        )
                    )
                except (
                    GitHubDestinationError,
                    PublicationError,
                    RegistrationConfirmationError,
                    RegistrationAssessmentError,
                    ValueError,
                ) as error:
                    recovered_items.append(
                        {
                            "kind": "publication",
                            "operation_id": operation_id,
                            "state": "paused",
                            "error": str(error),
                        }
                    )
            recovered = tuple(recovered_items)
        try:
            finalized_candidates = self._recover_candidate_finalizations()
        except (
            IntakeError,
            RegistrationConfirmationError,
            RegistrationRecoveryError,
            ValueError,
        ) as error:
            finalized_candidates = ()
            errors.append(
                {"kind": "candidate finalization", "message": str(error)}
            )
        recovery_activities: list[str] = []
        if self.recovery is not None:
            with self.database.read_connection() as connection:
                activity_ids = tuple(
                    str(row[0])
                    for row in connection.execute(
                        """SELECT activity_id FROM registration_recovery_attempts
                           WHERE state NOT IN ('cancelled', 'completed')
                           ORDER BY activity_id"""
                    ).fetchall()
                )
            for activity_id in activity_ids:
                try:
                    self.recovery.status(activity_id)
                    recovery_activities.append(activity_id)
                except RegistrationRecoveryError as error:
                    errors.append(
                        {
                            "kind": "registration recovery",
                            "activity_id": activity_id,
                            "message": str(error),
                        }
                    )
        assignment_recovery: list[dict[str, str]] = []
        try:
            finalized_confirmations = self._recover_confirmation_finalizations()
        except (RegistrationConfirmationError, ValueError) as error:
            finalized_confirmations = ()
            errors.append(
                {"kind": "confirmation finalization", "message": str(error)}
            )
        for activity_id in restored:
            try:
                result = self._reconcile_saved_assignment(activity_id)
                if result is not None:
                    assignment_recovery.append(result)
            except (RegistrationAssessmentError, SupervisionError, ValueError) as error:
                errors.append(
                    {
                        "kind": "agent assignment",
                        "activity_id": activity_id,
                        "message": str(error),
                    }
                )
        return {
            "restored_assessments": restored,
            "recovered_publications": recovered,
            "finalized_candidates": finalized_candidates,
            "unfinished_recoveries": tuple(recovery_activities),
            "finalized_confirmations": finalized_confirmations,
            "agent_assignments": tuple(assignment_recovery),
            "errors": tuple(errors),
        }

    def _recover_candidate_finalizations(self) -> tuple[str, ...]:
        if self.confirmation is None:
            return ()
        with self.database.read_connection() as connection:
            rows = connection.execute(
                """SELECT operation_id, activity_id, package_ref_json
                   FROM registration_candidate_publications
                   WHERE state = 'published'
                   ORDER BY rowid"""
            ).fetchall()
        finalized: list[str] = []
        for operation_id, activity_id, package_ref_json in rows:
            with self.database.read_connection() as connection:
                activity = connection.execute(
                    """SELECT state FROM service_activities
                       WHERE activity_id = ? AND kind = 'registration'""",
                    (str(activity_id),),
                ).fetchone()
            if activity is None or str(activity[0]) in {
                "completed", "cancelled", "failed"
            }:
                continue
            if package_ref_json is None:
                raise RegistrationConfirmationError(
                    "published candidate finalization lacks its package reference"
                )
            package = RegistrationPackageReference.from_mapping(
                json.loads(str(package_ref_json))
            )
            self._finalize_published_candidate(str(activity_id), package)
            finalized.append(str(operation_id))
        return tuple(finalized)

    def _publication_parent(
        self,
        assessment: RegistrationAssessment,
        active: ConfirmationResult | None,
    ) -> str:
        if active is not None:
            return active.remote_commit
        with self.database.read_connection() as connection:
            row = connection.execute(
                """SELECT intake_json FROM registration_assessment_intake
                   WHERE activity_id = ?""",
                (assessment.context.activity_id,),
            ).fetchone()
        if row is None:
            raise IntakeError(
                "registration publication lacks its saved intake"
            )
        intake = RegistrationIntakeResult.from_json(str(row[0]))
        context = assessment.context.package_context
        if (
            intake.repository != context.source_repository
            or intake.publication_branch != context.publication_branch
            or intake.publication_head is None
        ):
            raise IntakeError(
                "registration publication parent differs from its saved intake"
            )
        return intake.publication_head

    def _finalize_published_candidate(
        self,
        activity_id: str,
        package: RegistrationPackageReference,
    ) -> None:
        with self.database.read_connection() as connection:
            candidate = connection.execute(
                """SELECT project_id, activity_version, package_ref_json
                   FROM registration_candidate_publications
                   WHERE activity_id = ? AND state = 'published'
                     AND registration_version = ? AND candidate_id = ?""",
                (activity_id, package.registration_version, package.candidate_id),
            ).fetchone()
            recovery_attempt = connection.execute(
                """SELECT 1 FROM registration_recovery_attempts
                   WHERE activity_id = ? AND state NOT IN ('cancelled', 'completed')""",
                (activity_id,),
            ).fetchone()
        if candidate is None or RegistrationPackageReference.from_mapping(
            json.loads(str(candidate[2]))
        ) != package:
            raise RegistrationConfirmationError(
                "published candidate finalization differs from its saved reference"
            )
        if recovery_attempt is not None:
            if self.recovery is None:
                raise RegistrationRecoveryError(
                    "re-registration candidate finalization is not configured"
                )
            self.recovery.record_candidate_from_saved_reasons(activity_id, package)
        with self.database.transaction() as transaction:
            activity = _activity_row(transaction, activity_id)
            if str(activity[0]) != str(candidate[0]):
                raise RegistrationConfirmationError(
                    "published candidate finalization belongs to another project"
                )
            if int(activity[4]) != int(candidate[1]):
                raise RegistrationConfirmationError(
                    "published candidate finalization activity version changed"
                )
            if str(activity[2]) in {"completed", "cancelled", "failed"}:
                return
            self._set_activity_presentation_in(
                transaction,
                activity_id,
                "waiting",
                "Exact reviewed candidate is ready for confirmation",
                (
                    ActivityAction(
                        "registration-confirm", "Confirm registration", "decision"
                    ),
                    ActivityAction(
                        "registration-cancel", "Cancel registration", "decision"
                    ),
                ),
            )

    def _recover_confirmation_finalizations(self) -> tuple[str, ...]:
        if self.confirmation is None:
            return ()
        with self.database.read_connection() as connection:
            rows = connection.execute(
                """SELECT confirmation.confirmation_id, confirmation.request_id,
                          confirmation.project_id, confirmation.activity_id,
                          confirmation.expected_activity_version,
                          confirmation.confirmed_at, confirmation.package_ref_json,
                          confirmation.remote_commit,
                          confirmation.confirmation_ref_json,
                          confirmation.owner_id
                   FROM registration_confirmations AS confirmation
                   LEFT JOIN request_receipts AS receipt
                     ON receipt.request_id = confirmation.request_id
                   WHERE confirmation.state = 'confirmed'
                     AND receipt.request_id IS NULL
                   ORDER BY confirmation.sequence"""
            ).fetchall()
        finalized: list[str] = []
        for row in rows:
            package_ref = RegistrationPackageReference.from_mapping(
                json.loads(str(row[6]))
            )
            confirmation_ref_value = json.loads(str(row[8]))
            active = self.confirmation.active(str(row[2]))
            if (
                active is None
                or active.package_ref != package_ref
                or active.confirmation_ref.as_dict() != confirmation_ref_value
                or active.remote_commit != str(row[7])
            ):
                raise RegistrationConfirmationError(
                    "confirmed registration finalization differs from the active pointer"
                )
            request = RequestEnvelope(
                str(row[1]),
                "registration.confirm",
                str(row[2]),
                str(row[3]),
                None,
                int(row[4]),
                {
                    "confirmation_id": str(row[0]),
                    "package_ref": package_ref.as_dict(),
                    "confirmed_at": str(row[5]),
                },
            )
            event_key = hashlib.sha256(
                f"{request.request_id}\0{request.content_digest}".encode("utf-8")
            ).hexdigest()
            event_id = f"request-{event_key}"
            result = active
            command = Command(
                request_id=request.request_id,
                operation=request.operation,
                actor_id=str(row[9]),
                entity_id=str(row[3]),
                expected_version=int(row[4]),
                content_digest=request.content_digest,
            )
            event = Event(
                schema_version=1,
                event_id=event_id,
                occurred_at=_utc_now(),
                project_id=str(row[2]),
                activity_id=str(row[3]),
                type="registration.confirmed",
                data={"confirmation_id": str(row[0])},
            )

            def apply(
                transaction: Transaction,
                next_version: int,
                *,
                activity_id: str = str(row[3]),
                project_id: str = str(row[2]),
                expected_version: int = int(row[4]),
                confirmation_result: ConfirmationResult = result,
                saved_request_id: str = request.request_id,
                saved_event_id: str = event_id,
            ) -> OperationResult:
                operation_result = self._finalize_confirmation_in(
                    transaction,
                    activity_id,
                    project_id,
                    expected_version,
                    next_version,
                    confirmation_result,
                )
                ReceiptRepository.save_result(
                    transaction,
                    saved_request_id,
                    saved_event_id,
                    operation_result,
                )
                return operation_result

            self.database.commit_command(command, event, apply)
            finalized.append(str(row[0]))
        return tuple(finalized)

    def _finalize_confirmation_in(
        self,
        transaction: Transaction,
        activity_id: str,
        project_id: str,
        expected_version: int,
        next_version: int,
        result: ConfirmationResult,
    ) -> OperationResult:
        row = _activity_row(transaction, activity_id)
        self.records.update_activity(
            transaction,
            ActivityRecord(
                activity_id,
                project_id,
                "registration",
                str(row[1]),
                "completed",
                next_version,
                started_at=None if row[3] is None else str(row[3]),
                ended_at=_utc_now(),
            ),
            expected_record_version=expected_version,
        )
        project = transaction.execute(
            "SELECT name, version FROM service_projects WHERE project_id = ?",
            (project_id,),
        ).fetchone()
        if project is None:
            raise ValueError("registration project is unavailable")
        self.records.update_project(
            transaction,
            ProjectRecord(
                project_id, str(project[0]), "registered", int(project[1]) + 1
            ),
            expected_record_version=int(project[1]),
        )
        if self.recovery is not None:
            transaction.execute(
                """UPDATE registration_recovery_attempts
                   SET state = 'completed', failure = NULL
                   WHERE activity_id = ? AND state NOT IN ('cancelled', 'completed')""",
                (activity_id,),
            )
            self.recovery.release_intake_reservation_in(transaction, activity_id)
        return OperationResult(
            data={
                "status": result.status,
                "package_ref": result.package_ref.as_dict(),
                "confirmation_ref": result.confirmation_ref.as_dict(),
                "remote_commit": result.remote_commit,
            },
            project_id=project_id,
            activity_id=activity_id,
        )

    def _receive_intake_answer(self, answer: DeliveredAnswer) -> None:
        with self.database.read_connection() as connection:
            row = connection.execute(
                """SELECT links.activity_id, links.field, intake.project_id,
                          intake.request_json, intake.state, intake.intake_json
                   FROM installed_registration_intake_questions AS links
                   JOIN installed_registration_intake AS intake USING(activity_id)
                   WHERE links.question_id = ?""",
                (answer.question_id,),
            ).fetchone()
        if row is None or str(row[0]) != answer.activity_id:
            raise ValueError("registration intake answer is not linked to this activity")
        if str(row[4]) == "assessment_started":
            return
        dependencies = self._require_runtime()
        try:
            saved_request = json.loads(str(row[3]))
        except (TypeError, json.JSONDecodeError) as error:
            raise ValueError("saved registration intake request is invalid") from error
        if not isinstance(saved_request, dict):
            raise ValueError("saved registration intake request is invalid")
        field = str(row[1])
        if field not in {
            "overview_path", "scope", "publication_branch",
            "architect_selection", "reviewer_selection"
        }:
            raise ValueError("saved registration intake question field is invalid")
        saved_request[field] = answer.text.strip()
        branch = _optional_text(saved_request.get("publication_branch"))
        repository = _text(saved_request.get("repository"), "repository")
        saved_request["remote"] = (
            "" if branch is None else dependencies.remote_for_repository(repository)
        )
        with self.database.transaction() as transaction:
            transaction.execute(
                """UPDATE installed_registration_intake
                   SET request_json = ?
                   WHERE activity_id = ? AND state = 'waiting_for_intake'""",
                (
                    canonical_json(saved_request),
                    answer.activity_id,
                ),
            )
        self._continue_reserved_intake(answer.activity_id)

    def _continue_reserved_intake(self, activity_id: str) -> None:
        """Persist source identity before reading or launching assessment work."""
        with self.database.read_connection() as connection:
            row = connection.execute(
                """SELECT project_id, request_json, intake_json
                   FROM installed_registration_intake
                   WHERE activity_id = ? AND state = 'waiting_for_intake'""",
                (activity_id,),
            ).fetchone()
        if row is None:
            return
        project_id = str(row[0])
        try:
            saved_request = json.loads(str(row[1]))
            if not isinstance(saved_request, Mapping):
                raise ValueError("saved registration intake request is invalid")
            intake_request = _intake_request_from_record(saved_request)
            assert self.intake is not None
            intake = RegistrationIntakeResult.from_json(str(row[2]))
            if intake.inventory is None and intake.source_commit is None:
                collector = _CollectedQuestions()
                intake = self.intake.reserve(intake_request, questions=collector)
                with self.database.transaction() as transaction:
                    transaction.execute(
                        """UPDATE installed_registration_intake
                           SET intake_json = ?
                           WHERE activity_id = ? AND state = 'waiting_for_intake'""",
                        (intake.to_json(), activity_id),
                    )
                    existing_questions = {
                        str(item[0]) for item in transaction.execute(
                            """SELECT field FROM installed_registration_intake_questions
                               WHERE activity_id = ?""",
                            (activity_id,),
                        ).fetchall()
                    }
                    for question in collector.values:
                        if question.field not in existing_questions:
                            self._publish_intake_question(
                                transaction, project_id, activity_id, question
                            )
                if intake.missing_questions:
                    self._set_activity_presentation(
                        activity_id,
                        "waiting",
                        "Registration intake needs answers.",
                        (
                            ActivityAction(
                                "registration-cancel", "Cancel registration", "decision"
                            ),
                        ),
                    )
                    return
            if intake.inventory is None:
                intake = self.intake.complete(intake_request, intake)
                with self.database.transaction() as transaction:
                    transaction.execute(
                        """UPDATE installed_registration_intake
                           SET intake_json = ?
                           WHERE activity_id = ? AND state = 'waiting_for_intake'""",
                        (intake.to_json(), activity_id),
                    )
            selections = RoleSelections(
                _tool_selection(
                    intake_request.architect_selection, "architect_selection"
                ),
                _tool_selection(
                    intake_request.reviewer_selection, "reviewer_selection"
                ),
            )
            dependencies = self._require_runtime()
            assessment = self.binding.plugin.start_assessment(
                snapshot=dependencies.process_snapshot,
                activity_id=activity_id,
                project_id=project_id,
                intake=intake,
                selections=selections,
            )
            assessment.bind_process_snapshot(dependencies.process_snapshot)
        except (IntakeError, OSError, RuntimeError, TypeError, ValueError) as error:
            attempted = error.attempt if isinstance(error, IntakeError) else None
            if attempted is not None:
                with self.database.transaction() as transaction:
                    transaction.execute(
                        """UPDATE installed_registration_intake SET intake_json = ?
                           WHERE activity_id = ?""",
                        (attempted.to_json(), activity_id),
                    )
            self._set_activity_presentation(
                activity_id,
                "paused",
                f"Registration intake needs intervention: {error}",
                (
                    ActivityAction(
                        "registration-cancel", "Cancel registration", "decision"
                    ),
                ),
            )
            return
        with self.database.transaction() as transaction:
            if self.recovery is not None:
                self.recovery.require_work_start_allowed(
                    transaction, project_id, activity_id
                )
            activity = _activity_row(transaction, activity_id)
            current_version = int(activity[4])
            next_version = current_version + 1
            self.records.update_activity(
                transaction,
                ActivityRecord(
                    activity_id,
                    project_id,
                    "registration",
                    str(activity[1]),
                    "running",
                    next_version,
                    waiting_reason=None,
                    started_at=None if activity[3] is None else str(activity[3]),
                    available_actions=(
                        ActivityAction(
                            "registration-cancel", "Cancel registration", "decision"
                        ),
                    ),
                ),
                expected_record_version=current_version,
            )
            transaction.execute(
                "UPDATE entity_versions SET version = ? WHERE entity_id = ?",
                (next_version, activity_id),
            )
            transaction.execute(
                """UPDATE installed_registration_intake
                   SET intake_json = ?, state = ? WHERE activity_id = ?""",
                (
                    intake.to_json(),
                    "assessment_started",
                    activity_id,
                ),
            )
            self.binding.save_intake_in(
                transaction, activity_id, project_id, intake, selections
            )
            self.binding.install_started(transaction, assessment)
            _append_registration_event_in(
                transaction,
                project_id,
                activity_id,
                "registration.assessment-started",
                {
                    "activity_id": activity_id,
                    "state": "running",
                    "version": next_version,
                },
            )
        self._launch_assignment(assessment, "project_architect")

    def _publish_intake_question(
        self,
        transaction: Transaction,
        project_id: str,
        activity_id: str,
        question: IntakeQuestion,
    ) -> None:
        question_id = f"{activity_id}-{question.field}"
        self.questions.publish(
            transaction,
            LinkedQuestion(
                question_id,
                project_id,
                activity_id,
                question.subject,
                question.prompt,
                "registration-process",
                "registration-process",
                choices=(),
                allow_free_text=True,
            ),
            emit_event=True,
        )
        transaction.execute(
            """INSERT INTO installed_registration_intake_questions(
                   question_id, activity_id, field
               ) VALUES (?, ?, ?)""",
            (question_id, activity_id, question.field),
        )

    def _assessment_changed(self, assessment: RegistrationAssessment) -> None:
        """Publish an independently approved candidate from its saved workspace."""
        if assessment.status.state == "changes_requested":
            assessment = self.binding.continue_after_review(assessment)
            self._launch_assignment(assessment, "project_architect")
            return
        if assessment.status.state == "awaiting_architect":
            self._launch_assignment(assessment, "project_architect")
            return
        if assessment.status.state == "awaiting_reviewer":
            if assessment.status.review_count >= assessment.status.review_limit:
                self.binding.pause_for_review_limit(assessment)
                self._ensure_review_limit_decision(assessment)
                return
            if assessment.status.review_count:
                assessment = self.binding.prepare_next_review(assessment)
            grant_id = self._reserve_review_grant(assessment)
            launched = self._launch_assignment(assessment, "fidelity_reviewer")
            if grant_id is not None:
                with self.database.transaction() as transaction:
                    transaction.execute(
                        """UPDATE installed_registration_review_grants SET state = ?
                           WHERE decision_id = ? AND state = 'reserved'""",
                        ("consumed" if launched else "unconsumed", grant_id),
                    )
            return
        if assessment.status.state == "review_limit_owner_decision":
            self._ensure_review_limit_decision(assessment)
            return
        if assessment.status.state != "ready":
            return
        if self.dependencies is None or self.confirmation is None:
            return
        dependencies = self._require_runtime()
        confirmation = self._require_confirmation()
        if dependencies.workspace_root is None:
            return
        activity_id = assessment.context.activity_id
        project_id = assessment.context.project_id
        candidate = self._finalize_reviewed_candidate(assessment)
        operation_id = f"registration-candidate-{activity_id}-{candidate.version}"
        request_id = f"registration-publication-{activity_id}-{candidate.version}"
        version = self._advance_for_publication(activity_id, project_id)
        active: ConfirmationResult | None = None
        try:
            manifest, records = _load_candidate_workspace(
                dependencies.workspace_root, assessment, candidate.path, candidate.sha256
            )
            active = confirmation.active(project_id)
            if active is not None:
                if self.recovery is None:
                    raise RegistrationRecoveryError(
                        "installed registration recovery is not configured"
                    )
                authorization = dependencies.destination_provider.authorize(
                    assessment.context.package_context.source_repository,
                    assessment.context.package_context.publication_branch,
                )
                self.recovery.begin(
                    request_id=f"registration-recovery-{activity_id}",
                    project_id=project_id,
                    activity_id=activity_id,
                    destination_authorization=authorization,
                    continuity=self.recovery.load_continuity(project_id, activity_id),
                    process_snapshot=assessment.process_snapshot,
                )
            package = confirmation.publish_candidate(
                assessment,
                activity_version=version,
                manifest=manifest,
                records=records,
                remote=dependencies.remote_for_repository(
                    assessment.context.package_context.source_repository
                ),
                expected_parent=self._publication_parent(assessment, active),
                operation_id=operation_id,
                request_id=request_id,
            )
            self._finalize_published_candidate(activity_id, package)
        except (OSError, RuntimeError, ValueError) as error:
            try:
                self._recover_publication_automatically(
                    assessment, operation_id, str(error)
                )
                with self.database.read_connection() as connection:
                    published = connection.execute(
                        """SELECT package_ref_json
                           FROM registration_candidate_publications
                           WHERE operation_id = ? AND state = 'published'""",
                        (operation_id,),
                    ).fetchone()
                if published is None:
                    raise ValueError("automatic publication recovery did not publish the candidate")
                package = RegistrationPackageReference.from_mapping(
                    json.loads(str(published[0]))
                )
                self._finalize_published_candidate(activity_id, package)
            except (OSError, RuntimeError, ValueError) as recovery_error:
                self._set_activity_presentation(
                    activity_id,
                    "paused",
                    f"Candidate publication needs intervention: {recovery_error}",
                    (
                        ActivityAction(
                            f"registration-retry.{operation_id}",
                            "Retry publication",
                            "recovery",
                        ),
                        ActivityAction(
                            "registration-cancel", "Cancel registration", "decision"
                        ),
                    ),
                )

    def _finalize_reviewed_candidate(
        self, assessment: RegistrationAssessment
    ) -> ArtifactReference:
        """Add service-owned review evidence without changing reviewed content bytes."""
        dependencies = self._require_runtime()
        if dependencies.workspace_root is None:
            raise ValueError("installed registration workspace is not configured")
        candidate = assessment.require_ready_candidate()
        manifest, records = _load_candidate_workspace(
            dependencies.workspace_root,
            assessment,
            candidate.path,
            candidate.sha256,
        )
        if any(record.get("record_type") == "review" for record in records.values()):
            validate_registration_package(
                manifest,
                records,
                assessment.context.package_context,
                review_context=assessment.package_review_context(),
            )
            return candidate
        validate_registration_package(
            manifest,
            records,
            assessment.context.package_context,
            require_review=False,
        )
        assessments = [
            (path, record)
            for path, record in records.items()
            if record.get("record_type") == "assessment"
        ]
        if len(assessments) != 1:
            raise ValueError("approved candidate lacks one exact assessment record")
        assessment_path, assessment_record = assessments[0]
        review_context = assessment.package_review_context()
        state = assessment.to_record()
        review_id = (
            f"registration-review-{candidate.version}-"
            f"{review_context['review_round']}"
        )
        review_path = f"reviews/{review_id}.json"
        review_record: dict[str, object] = {
            "schema_version": 1,
            "record_type": "review",
            "record_id": review_id,
            "subject": "Independent review of the registration candidate",
            "record_version": int(review_context["review_round"]),
            "data": {
                **{
                    key: value for key, value in review_context.items()
                    if key not in {
                        "architect_assignment_id", "architect_run_id"
                    }
                },
                "reviewed_content_hash": manifest["content_hash"],
                "reviewed_assessment_ref": {
                    "record_id": assessment_record["record_id"],
                    "subject": assessment_record["subject"],
                    "record_version": assessment_record["record_version"],
                    "path": assessment_path,
                },
                "outcome": "APPROVE",
                "findings": state["review_findings"],
            },
        }
        finalized_records = dict(records)
        finalized_records[review_path] = review_record
        review_hash = hashlib.sha256(canonical_record_bytes(review_record)).hexdigest()
        finalized_manifest = dict(manifest)
        finalized_manifest["files"] = sorted(
            [
                *manifest["files"],
                {
                    "path": review_path,
                    "record_id": review_id,
                    "record_type": "review",
                    "record_version": int(review_context["review_round"]),
                    "subject": review_record["subject"],
                    "sha256": review_hash,
                },
            ],
            key=lambda item: str(item["path"]),
        )
        validate_registration_package(
            finalized_manifest,
            finalized_records,
            assessment.context.package_context,
            review_context=review_context,
        )
        architect = assessment.current_run("project_architect")
        root = (
            dependencies.workspace_root
            / assessment.context.project_id
            / assessment.context.activity_id
            / "runs"
            / architect.run_id
            / "output"
            / "reviewed-candidate"
        )
        root.mkdir(mode=0o700, parents=True, exist_ok=True)
        if root.is_symlink():
            raise ValueError("reviewed candidate output directory is unsafe")
        for path, record in finalized_records.items():
            target = root.joinpath(*PurePosixPath(path).parts)
            target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            if target.is_symlink():
                raise ValueError("reviewed candidate output path is unsafe")
            target.write_bytes(canonical_record_bytes(record))
        manifest_bytes = canonical_record_bytes(finalized_manifest)
        (root / "manifest.json").write_bytes(manifest_bytes)
        finalized = ArtifactReference(
            "reviewed-candidate/manifest.json",
            hashlib.sha256(manifest_bytes).hexdigest(),
            candidate.version,
        )
        self.binding.replace_ready_candidate(assessment, finalized)
        return finalized

    def _ensure_review_limit_decision(
        self, assessment: RegistrationAssessment
    ) -> str:
        """Save and display the exact pending Owner decision once."""
        status = assessment.status
        if status.state != "review_limit_owner_decision":
            raise RegistrationAssessmentError(
                "registration is not waiting for an Owner review-limit decision"
            )
        activity_id = assessment.context.activity_id
        project_id = assessment.context.project_id
        assignment = assessment.current_run("fidelity_reviewer")
        with self.database.transaction() as transaction:
            existing = transaction.execute(
                """SELECT decision_id FROM installed_registration_owner_decisions
                   WHERE activity_id = ? AND target = 'fidelity_review'
                     AND state = 'pending'""",
                (activity_id,),
            ).fetchone()
            if existing is not None:
                return str(existing[0])
            sequence = int(
                transaction.execute(
                    """SELECT COUNT(*) FROM installed_registration_owner_decisions
                       WHERE activity_id = ? AND target = 'fidelity_review'""",
                    (activity_id,),
                ).fetchone()[0]
            ) + 1
            decision_id = f"registration-review-decision-{activity_id}-{sequence}"
            question_id = decision_id
            transaction.execute(
                """INSERT INTO installed_registration_owner_decisions(
                       decision_id, request_id, project_id, activity_id,
                       question_id, decision_version, target, assignment_id,
                       reason, base_limit, used_attempts, prior_grants, choice, state
                   ) VALUES (?, NULL, ?, ?, ?, 1, 'fidelity_review', ?, ?, ?, ?, ?,
                             NULL, 'pending')""",
                (
                    decision_id,
                    project_id,
                    activity_id,
                    question_id,
                    assignment.assignment_id,
                    "Material review findings remain at the saved fidelity-review limit.",
                    status.base_review_limit,
                    status.review_count,
                    status.review_grants,
                ),
            )
            self._set_activity_presentation_in(
                transaction,
                activity_id,
                "paused",
                "Owner decision required: grant one additional fidelity review or remain paused.",
                (
                    ActivityAction(
                        f"owner-decision.{decision_id}.grant_one",
                        "Grant one fidelity review",
                        "decision",
                    ),
                    ActivityAction(
                        f"owner-decision.{decision_id}.remain_paused",
                        "Remain paused",
                        "decision",
                    ),
                    ActivityAction(
                        "registration-cancel", "Cancel registration", "decision"
                    ),
                ),
            )
        return decision_id

    def _reserve_review_grant(
        self, assessment: RegistrationAssessment
    ) -> str | None:
        status = assessment.status
        if status.review_count < status.base_review_limit:
            return None
        run = assessment.current_run("fidelity_reviewer")
        with self.database.transaction() as transaction:
            grant = transaction.execute(
                """SELECT decision_id FROM installed_registration_review_grants
                   WHERE activity_id = ? AND state = 'unconsumed'
                   ORDER BY rowid LIMIT 1""",
                (assessment.context.activity_id,),
            ).fetchone()
            if grant is None:
                raise RegistrationAssessmentError(
                    "an additional fidelity review requires an unconsumed Owner grant"
                )
            decision_id = str(grant[0])
            updated = transaction.execute(
                """UPDATE installed_registration_review_grants
                   SET assignment_id = ?, state = 'reserved'
                   WHERE decision_id = ? AND state = 'unconsumed'""",
                (run.assignment_id, decision_id),
            )
            if updated.rowcount != 1:
                raise RegistrationAssessmentError(
                    "the fidelity-review grant changed before reservation"
                )
        return decision_id

    def _recover_publication_automatically(
        self,
        assessment: RegistrationAssessment,
        operation_id: str,
        reason: str,
    ) -> tuple[dict[str, object], ...]:
        confirmation = self._require_confirmation()
        operation = confirmation.journal.operation(operation_id)
        authorization = confirmation.destination_provider.authorize(
            operation.authorization.repository,
            operation.authorization.branch,
        )
        try:
            confirmation.journal.reconcile(operation_id, authorization)
        except PublicationStateError:
            if confirmation.journal.operation(operation_id).state != "reconciled":
                self._pause_publication_failure(
                    assessment, operation_id, reason
                )
                raise
        except (PublicationAccessError, PublicationConflictError) as error:
            self._pause_publication_failure(assessment, operation_id, str(error))
            raise

        reserved: frozenset[str] = frozenset()
        if confirmation.journal.operation(operation_id).state == "reconciled":
            request_id = self._reserve_automatic_publication_retry(
                assessment, operation_id, reason
            )
            with self.database.transaction() as transaction:
                transaction.execute(
                    """UPDATE installed_registration_publication_retry_requests
                       SET state = 'dispatched'
                       WHERE request_id = ? AND state = 'reserved'""",
                    (request_id,),
                )
            reserved = frozenset((operation_id,))
        try:
            recovered = confirmation.recover_pending(
                assessment.context.activity_id,
                reserved_operation_ids=reserved,
            )
        except Exception as error:
            with self.database.transaction() as transaction:
                transaction.execute(
                    """UPDATE installed_registration_publication_retry_requests
                       SET state = 'failed', failure = ?
                       WHERE operation_id = ? AND state IN ('reserved', 'dispatched')""",
                    (str(error), operation_id),
                )
                transaction.execute(
                    """UPDATE installed_registration_publication_failures
                       SET state = 'paused', reason = ? WHERE operation_id = ?""",
                    (str(error), operation_id),
                )
            raise
        with self.database.transaction() as transaction:
            transaction.execute(
                """UPDATE installed_registration_publication_retry_requests
                   SET state = 'completed', failure = NULL
                   WHERE operation_id = ? AND state IN ('reserved', 'dispatched')""",
                (operation_id,),
            )
            transaction.execute(
                """UPDATE installed_registration_publication_failures
                   SET state = 'resolved' WHERE operation_id = ?""",
                (operation_id,),
            )
        return recovered

    def _reserve_automatic_publication_retry(
        self,
        assessment: RegistrationAssessment,
        operation_id: str,
        reason: str,
    ) -> str:
        recovery = assessment.process_snapshot.definition.get("recovery")
        automatic_limit = (
            recovery.get("automatic_recovery_attempts")
            if isinstance(recovery, Mapping)
            else None
        )
        if (
            isinstance(automatic_limit, bool)
            or not isinstance(automatic_limit, int)
            or automatic_limit < 0
        ):
            automatic_limit = 0
        activity_id = assessment.context.activity_id
        exhausted = False
        request_id = ""
        with self.database.transaction() as transaction:
            pending = transaction.execute(
                """SELECT request_id
                   FROM installed_registration_publication_retry_requests
                   WHERE operation_id = ? AND state IN ('reserved', 'dispatched')
                   ORDER BY rowid DESC LIMIT 1""",
                (operation_id,),
            ).fetchone()
            if pending is not None:
                return str(pending[0])
            saved = transaction.execute(
                """SELECT automatic_consumed
                   FROM installed_registration_publication_failures
                   WHERE operation_id = ?""",
                (operation_id,),
            ).fetchone()
            consumed = 0 if saved is None else int(saved[0])
            if consumed >= automatic_limit:
                transaction.execute(
                    """INSERT INTO installed_registration_publication_failures(
                           operation_id, activity_id, reason, state,
                           automatic_limit, automatic_consumed
                       ) VALUES (?, ?, ?, 'paused', ?, ?)
                       ON CONFLICT(operation_id) DO UPDATE SET
                           reason = excluded.reason,
                           state = 'paused',
                           automatic_limit = excluded.automatic_limit""",
                    (operation_id, activity_id, reason, automatic_limit, consumed),
                )
                exhausted = True
            else:
                request_id = (
                    f"registration-publication-automatic-{activity_id}-{consumed + 1}"
                )
                transaction.execute(
                    """INSERT INTO installed_registration_publication_retry_requests(
                           request_id, activity_id, operation_id, kind, state, failure
                       ) VALUES (?, ?, ?, 'automatic', 'reserved', NULL)""",
                    (request_id, activity_id, operation_id),
                )
                transaction.execute(
                    """INSERT INTO installed_registration_publication_failures(
                           operation_id, activity_id, reason, state,
                           automatic_limit, automatic_consumed
                       ) VALUES (?, ?, ?, 'retrying', ?, ?)
                       ON CONFLICT(operation_id) DO UPDATE SET
                           reason = excluded.reason,
                           state = 'retrying',
                           automatic_limit = excluded.automatic_limit,
                           automatic_consumed = excluded.automatic_consumed""",
                    (
                        operation_id,
                        activity_id,
                        reason,
                        automatic_limit,
                        consumed + 1,
                    ),
                )
                self._set_activity_presentation_in(
                    transaction,
                    activity_id,
                    "running",
                    f"Automatically retrying publication: {reason}",
                    (
                        ActivityAction(
                            "registration-cancel", "Cancel registration", "decision"
                        ),
                    ),
                )
        if exhausted:
            raise ValueError("automatic publication recovery allowance is exhausted")
        return request_id

    def _pause_publication_failure(
        self,
        assessment: RegistrationAssessment,
        operation_id: str,
        reason: str,
    ) -> None:
        recovery = assessment.process_snapshot.definition.get("recovery")
        limit = (
            recovery.get("automatic_recovery_attempts")
            if isinstance(recovery, Mapping)
            else 0
        )
        if isinstance(limit, bool) or not isinstance(limit, int) or limit < 0:
            limit = 0
        with self.database.transaction() as transaction:
            transaction.execute(
                """INSERT INTO installed_registration_publication_failures(
                       operation_id, activity_id, reason, state,
                       automatic_limit, automatic_consumed
                   ) VALUES (?, ?, ?, 'paused', ?, 0)
                   ON CONFLICT(operation_id) DO UPDATE SET
                       reason = excluded.reason,
                       state = 'paused',
                       automatic_limit = excluded.automatic_limit""",
                (
                    operation_id,
                    assessment.context.activity_id,
                    reason,
                    limit,
                ),
            )

    def _launch_assignment(
        self, assessment: RegistrationAssessment, role: str
    ) -> bool:
        if self.dependencies is None or self.dependencies.assignment_launcher is None:
            return False
        try:
            if self.recovery is not None:
                with self.database.transaction() as transaction:
                    self.recovery.require_work_start_allowed(
                        transaction,
                        assessment.context.project_id,
                        assessment.context.activity_id,
                    )
            self.dependencies.assignment_launcher(self.binding, assessment, role)
            return True
        except (OSError, RuntimeError, ValueError) as error:
            run = assessment.current_run(role)
            self._assignment_failed(
                assessment.context.activity_id,
                role,
                run.assignment_id,
                run.run_id,
                f"assignment could not start: {error}",
                isinstance(error, (OSError, RuntimeError))
                and not isinstance(error, SupervisionError),
                failed_launch=not isinstance(error, SupervisionError),
            )
            return False

    def _stop_active_assignment_before_cancel(self, activity_id: str) -> None:
        try:
            assessment = self.binding.assessment(activity_id)
        except RegistrationAssessmentError:
            return
        state = assessment.status.state
        if state == "awaiting_architect":
            role = "project_architect"
        elif state == "awaiting_reviewer":
            role = "fidelity_reviewer"
        elif state == "technical_recovery":
            with self.database.read_connection() as connection:
                failure = connection.execute(
                    """SELECT role, failed_launch_evidence
                       FROM installed_registration_agent_failures
                       WHERE activity_id = ? AND state = 'paused'""",
                    (activity_id,),
                ).fetchone()
            if failure is None:
                raise ValueError(
                    "registration cancellation is paused with Stop unconfirmed; "
                    "technical recovery lacks exact failed-run evidence"
                )
            if int(failure[1]) == 1:
                return
            role = str(failure[0])
        else:
            return
        try:
            observed = self.binding.poll_current_agent(assessment, role)
        except SupervisionError as error:
            raise ValueError(
                "registration cancellation is paused with Stop unconfirmed; "
                f"active agent state could not be reconciled: {error}"
            ) from error
        if observed.state in {"running", "launch_uncertain"}:
            observed = self.binding.stop_current_agent(
                assessment, role, "cancelled"
            )
        if observed.state not in {
            "completed", "failed", "cancelled", "timed_out", "stalled", "stopped"
        }:
            raise ValueError(
                "registration cancellation is paused until the active agent stop "
                f"is confirmed ({observed.state})"
            )

    def _continue_registration_cancellation(self, activity_id: str) -> None:
        """Finish a durable cancellation only after work and writes are reconciled."""
        with self.database.read_connection() as connection:
            intent = connection.execute(
                """SELECT request_id, project_id, operation_id, state
                   FROM installed_registration_cancellations
                   WHERE activity_id = ?""",
                (activity_id,),
            ).fetchone()
        if intent is None or str(intent[3]) == "cancelled":
            return
        request_id = str(intent[0])
        project_id = str(intent[1])
        operation_id = None if intent[2] is None else str(intent[2])
        try:
            self._stop_active_assignment_before_cancel(activity_id)
            confirmation = self._require_confirmation()
            confirmation.recover_pending(activity_id)
            with self.database.read_connection() as connection:
                confirmed = connection.execute(
                    """SELECT 1 FROM registration_confirmations
                       WHERE activity_id = ? AND state = 'confirmed' LIMIT 1""",
                    (activity_id,),
                ).fetchone()
                recovery_attempt = connection.execute(
                    """SELECT 1 FROM registration_recovery_attempts
                       WHERE activity_id = ?""",
                    (activity_id,),
                ).fetchone()
            if confirmed is not None:
                raise ValueError(
                    "registration became confirmed before cancellation completed"
                )
            if self.recovery is not None and recovery_attempt is not None:
                self.recovery.cancel(
                    activity_id, request_id, operation_id=operation_id
                )
        except (OSError, RuntimeError, ValueError) as error:
            with self.database.transaction() as transaction:
                transaction.execute(
                    """UPDATE installed_registration_cancellations
                       SET failure = ?
                       WHERE activity_id = ? AND state = 'stopping'""",
                    (str(error), activity_id),
                )
            self._set_activity_presentation(
                activity_id,
                "stopping",
                f"Stop unconfirmed: {error}",
                (),
            )
            return
        with self.database.transaction() as transaction:
            row = _activity_row(transaction, activity_id)
            current_version = int(row[4])
            next_version = current_version + 1
            self.records.update_activity(
                transaction,
                ActivityRecord(
                    activity_id,
                    project_id,
                    "registration",
                    str(row[1]),
                    "cancelled",
                    next_version,
                    started_at=None if row[3] is None else str(row[3]),
                    ended_at=_utc_now(),
                ),
                expected_record_version=current_version,
            )
            transaction.execute(
                "UPDATE entity_versions SET version = ? WHERE entity_id = ?",
                (next_version, activity_id),
            )
            transaction.execute(
                """UPDATE installed_registration_intake SET state = 'cancelled'
                   WHERE activity_id = ?""",
                (activity_id,),
            )
            open_questions = transaction.execute(
                """SELECT question_id, version FROM service_questions
                   WHERE activity_id = ?
                     AND status IN ('awaiting_answer', 'clarification_required')""",
                (activity_id,),
            ).fetchall()
            for question_id, version in open_questions:
                transaction.execute(
                    """UPDATE service_questions SET status = 'cancelled', version = ?
                       WHERE question_id = ? AND version = ?""",
                    (int(version) + 1, str(question_id), int(version)),
                )
                transaction.execute(
                    "UPDATE entity_versions SET version = ? WHERE entity_id = ?",
                    (int(version) + 1, str(question_id)),
                )
            active = transaction.execute(
                "SELECT 1 FROM active_registrations WHERE project_id = ?",
                (project_id,),
            ).fetchone()
            if active is None:
                project = transaction.execute(
                    "SELECT name, version FROM service_projects WHERE project_id = ?",
                    (project_id,),
                ).fetchone()
                if project is None:
                    raise ValueError("registration project is unavailable")
                self.records.update_project(
                    transaction,
                    ProjectRecord(
                        project_id, str(project[0]), "not_registered",
                        int(project[1]) + 1,
                    ),
                    expected_record_version=int(project[1]),
                )
            if self.recovery is not None:
                self.recovery.release_intake_reservation_in(transaction, activity_id)
            transaction.execute(
                """UPDATE installed_registration_cancellations
                   SET state = 'cancelled', failure = NULL
                   WHERE activity_id = ? AND state = 'stopping'""",
                (activity_id,),
            )
            _append_registration_event_in(
                transaction,
                project_id,
                activity_id,
                "registration.cancelled",
                {
                    "activity_id": activity_id,
                    "state": "cancelled",
                    "version": next_version,
                },
            )

    def _reconcile_saved_assignment(
        self, activity_id: str
    ) -> dict[str, str] | None:
        assessment = self.binding.assessment(activity_id)
        with self.database.read_connection() as connection:
            activity = connection.execute(
                "SELECT state FROM service_activities WHERE activity_id = ?",
                (activity_id,),
            ).fetchone()
            saved_failure = connection.execute(
                """SELECT role, assignment_id, failed_run_id, reason, state,
                          failed_launch_evidence
                   FROM installed_registration_agent_failures
                   WHERE activity_id = ?""",
                (activity_id,),
            ).fetchone()
        if activity is None or str(activity[0]) in {"completed", "cancelled", "failed"}:
            return None
        state = assessment.status.state
        if state == "changes_requested":
            self._assessment_changed(assessment)
            return {
                "activity_id": activity_id,
                "state": "architect-correction-dispatched",
            }
        if state == "technical_recovery":
            if saved_failure is None or str(saved_failure[4]) != "paused":
                self._set_activity_presentation(
                    activity_id,
                    "paused",
                    "Saved technical recovery lacks its failed assignment identity; "
                    "cancel or inspect the preserved supervisor record.",
                    (
                        ActivityAction(
                            "registration-cancel", "Cancel registration", "decision"
                        ),
                    ),
                )
                return {"activity_id": activity_id, "state": "paused-incomplete"}
            if int(saved_failure[5]) == 0:
                role = str(saved_failure[0])
                try:
                    observed = self.binding.poll_current_agent(assessment, role)
                except SupervisionError as error:
                    self._set_activity_presentation(
                        activity_id,
                        "paused",
                        "Stop unconfirmed: the saved agent launch cannot yet be "
                        f"reconciled ({error}).",
                        (
                            ActivityAction(
                                "registration-cancel", "Cancel registration", "decision"
                            ),
                        ),
                    )
                    return {"activity_id": activity_id, "state": "stop-unconfirmed"}
                if observed.state not in {
                    "completed", "failed", "cancelled", "timed_out", "stalled", "stopped"
                }:
                    self._set_activity_presentation(
                        activity_id,
                        "paused",
                        "Stop unconfirmed: the saved agent launch is not terminal "
                        f"({observed.state}).",
                        (
                            ActivityAction(
                                "registration-cancel", "Cancel registration", "decision"
                            ),
                        ),
                    )
                    return {"activity_id": activity_id, "state": "stop-unconfirmed"}
            self._set_activity_presentation(
                activity_id,
                "paused",
                f"Saved agent assignment needs intervention: {saved_failure[3]}",
                (
                    ActivityAction(
                        "registration-retry.agent", "Retry activity", "recovery"
                    ),
                    ActivityAction(
                        "registration-cancel", "Cancel registration", "decision"
                    ),
                ),
            )
            return {"activity_id": activity_id, "state": "paused"}
        if state == "awaiting_architect":
            role = "project_architect"
        elif state == "awaiting_reviewer":
            role = "fidelity_reviewer"
        else:
            return None
        current = assessment.current_run(role)
        with self.database.read_connection() as connection:
            reserved_retry = connection.execute(
                """SELECT request_id FROM installed_registration_agent_retry_requests
                   WHERE activity_id = ? AND replacement_run_id = ?
                     AND state = 'reserved'""",
                (activity_id, current.run_id),
            ).fetchone()
        if reserved_retry is not None:
            request_id = str(reserved_retry[0])
            try:
                observed = self.binding.poll_current_agent(assessment, role)
            except SupervisionError as error:
                if error.code != "unknown_operation":
                    raise
                self._dispatch_reserved_agent_retry(
                    activity_id, role, request_id
                )
                return {"activity_id": activity_id, "state": "retry-dispatched"}
            with self.database.transaction() as transaction:
                transaction.execute(
                    """UPDATE installed_registration_agent_retry_requests
                       SET state = 'launched' WHERE request_id = ? AND state = 'reserved'""",
                    (request_id,),
                )
        try:
            observed = self.binding.poll_current_agent(assessment, role)
        except SupervisionError as error:
            if error.code != "unknown_operation":
                raise
            if role == "project_architect":
                with self.database.read_connection() as connection:
                    granted_correction = connection.execute(
                        """SELECT 1 FROM installed_registration_review_grants
                           WHERE activity_id = ? AND state = 'unconsumed'
                           LIMIT 1""",
                        (activity_id,),
                    ).fetchone()
                if granted_correction is not None:
                    launched = self._launch_assignment(assessment, role)
                    return {
                        "activity_id": activity_id,
                        "state": (
                            "architect-correction-dispatched"
                            if launched else "paused"
                        ),
                    }
            self._set_activity_presentation(
                activity_id,
                "paused",
                "Stop unconfirmed: the saved agent assignment has no supervisor "
                "record, so replacement and cancellation remain blocked.",
                (
                    ActivityAction(
                        "registration-cancel", "Cancel registration", "decision"
                    ),
                ),
            )
            return {"activity_id": activity_id, "state": "stop-unconfirmed"}
        if observed.state == "running":
            resume = (
                None
                if self.dependencies is None
                else getattr(self.dependencies.assignment_launcher, "resume", None)
            )
            if not callable(resume):
                self._set_activity_presentation(
                    activity_id,
                    "paused",
                    "Saved agent assignment is still running, but this configured "
                    "assignment launcher has no durable resume capability.",
                    (
                        ActivityAction(
                            "registration-cancel", "Cancel registration", "decision"
                        ),
                    ),
                )
                return {"activity_id": activity_id, "state": "running-paused"}
            resume(self.binding, assessment, role)
            self._set_activity_presentation(
                activity_id,
                "running",
                "Saved agent assignment remains supervised; durable protocol events "
                "are being replayed after restart.",
                (
                    ActivityAction(
                        "registration-cancel", "Cancel registration", "decision"
                    ),
                ),
            )
            return {"activity_id": activity_id, "state": "running-resumed"}
        if observed.state == "completed":
            resume = (
                None
                if self.dependencies is None
                else getattr(self.dependencies.assignment_launcher, "resume", None)
            )
            if not callable(resume):
                raise ValueError(
                    "installed registration runner cannot replay a completed assignment"
                )
            resume(self.binding, assessment, role)
            self._set_activity_presentation(
                activity_id,
                "running",
                "Completed agent result is being replayed from durable supervisor files.",
                (
                    ActivityAction(
                        "registration-cancel", "Cancel registration", "decision"
                    ),
                ),
            )
            return {"activity_id": activity_id, "state": "result-replaying"}
        if observed.state in {
            "failed", "cancelled", "timed_out", "stalled", "stopped"
        }:
            self._assignment_failed(
                activity_id,
                role,
                current.assignment_id,
                current.run_id,
                f"startup reconciled saved supervisor state {observed.state}",
                observed.state in {"completed", "failed", "stalled", "stopped"},
            )
            with self.database.read_connection() as connection:
                failure_state = connection.execute(
                    """SELECT state FROM installed_registration_agent_failures
                       WHERE activity_id = ?""",
                    (activity_id,),
                ).fetchone()
            return {
                "activity_id": activity_id,
                "state": (
                    "retrying"
                    if failure_state is not None and str(failure_state[0]) == "retrying"
                    else "paused"
                ),
            }
        self._set_activity_presentation(
            activity_id,
            "paused",
            f"Saved agent assignment needs stop reconciliation ({observed.state}).",
            (
                ActivityAction(
                    "registration-cancel", "Cancel registration", "decision"
                ),
            ),
        )
        return {"activity_id": activity_id, "state": "stop-unconfirmed"}

    def _assignment_failed(
        self,
        activity_id: str,
        role: str,
        assignment_id: str,
        failed_run_id: str,
        reason: str,
        automatic_eligible: bool = False,
        *,
        failed_launch: bool = False,
    ) -> None:
        assessment = self.binding.assessment(activity_id)
        failed = assessment.current_run(role)
        if (failed.assignment_id, failed.run_id) != (assignment_id, failed_run_id):
            return
        recovery = assessment.process_snapshot.definition.get("recovery")
        automatic_limit = (
            recovery.get("automatic_recovery_attempts")
            if isinstance(recovery, Mapping)
            else None
        )
        if (
            isinstance(automatic_limit, bool)
            or not isinstance(automatic_limit, int)
            or automatic_limit < 0
        ):
            automatic_limit = 0
        terminal_confirmed = failed_launch
        stop_unconfirmed = False
        if not failed_launch:
            try:
                observed = self.binding.poll_current_agent(assessment, role)
            except SupervisionError:
                automatic_eligible = False
                stop_unconfirmed = True
            else:
                terminal_confirmed = observed.state in {
                    "completed", "failed", "cancelled", "timed_out", "stalled", "stopped"
                }
                stop_unconfirmed = not terminal_confirmed
                if observed.state in {"cancelled", "timed_out"}:
                    automatic_eligible = False
        retry_request_id: str | None = None
        with self.database.transaction() as transaction:
            self.binding.pause_technical_in(transaction, assessment, role)
            saved = transaction.execute(
                """SELECT assignment_id, automatic_consumed, manual_consumed
                   FROM installed_registration_agent_failures
                   WHERE activity_id = ?""",
                (activity_id,),
            ).fetchone()
            automatic_consumed = (
                int(saved[1])
                if saved is not None and str(saved[0]) == assignment_id
                else 0
            )
            manual_consumed = (
                int(saved[2])
                if saved is not None and str(saved[0]) == assignment_id
                else 0
            )
            retry_automatically = (
                automatic_eligible
                and terminal_confirmed
                and automatic_consumed < automatic_limit
            )
            if retry_automatically:
                replacement_run_id = f"{role}-run-{uuid.uuid4().hex}"
                replacement = self.binding.retry_technical_in(
                    transaction, assessment, role, failed, replacement_run_id
                )
                retry_request_id = (
                    f"registration-agent-automatic-{activity_id}-{automatic_consumed + 1}"
                )
                transaction.execute(
                    """INSERT INTO installed_registration_agent_retry_requests(
                           request_id, activity_id, assignment_id, failed_run_id,
                           replacement_run_id, kind, intervention, state
                       ) VALUES (?, ?, ?, ?, ?, 'automatic', NULL, 'reserved')""",
                    (
                        retry_request_id,
                        activity_id,
                        assignment_id,
                        failed_run_id,
                        replacement.run_id,
                    ),
                )
            transaction.execute(
                """INSERT INTO installed_registration_agent_failures(
                       activity_id, role, assignment_id, failed_run_id, reason,
                       state, automatic_limit, automatic_consumed, manual_consumed,
                       failed_launch_evidence
                   ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(activity_id) DO UPDATE SET
                       role = excluded.role,
                       assignment_id = excluded.assignment_id,
                       failed_run_id = excluded.failed_run_id,
                       reason = excluded.reason,
                       state = excluded.state,
                       automatic_limit = excluded.automatic_limit,
                       automatic_consumed = excluded.automatic_consumed,
                       manual_consumed = excluded.manual_consumed,
                       failed_launch_evidence = excluded.failed_launch_evidence""",
                (
                    activity_id,
                    role,
                    assignment_id,
                    failed_run_id,
                    reason,
                    "retrying" if retry_automatically else "paused",
                    automatic_limit,
                    automatic_consumed + (1 if retry_automatically else 0),
                    manual_consumed,
                    1 if failed_launch else 0,
                ),
            )
            actions = (
                (
                    ActivityAction(
                        "registration-cancel", "Cancel registration", "decision"
                    ),
                )
                if retry_automatically or stop_unconfirmed
                else (
                    ActivityAction(
                        "registration-retry.agent", "Retry activity", "recovery"
                    ),
                    ActivityAction(
                        "registration-cancel", "Cancel registration", "decision"
                    ),
                )
            )
            self._set_activity_presentation_in(
                transaction,
                activity_id,
                "running" if retry_automatically else "paused",
                (
                    f"Automatically retrying the saved agent assignment: {reason}"
                    if retry_automatically
                    else (
                        f"Stop unconfirmed: {reason}"
                        if stop_unconfirmed
                        else f"Agent assignment needs intervention: {reason}"
                    )
                ),
                actions,
            )
        if retry_request_id is not None:
            self._dispatch_reserved_agent_retry(activity_id, role, retry_request_id)

    def _dispatch_reserved_agent_retry(
        self, activity_id: str, role: str, request_id: str
    ) -> None:
        assessment = self.binding.assessment(activity_id)
        launched = self._launch_assignment(assessment, role)
        with self.database.transaction() as transaction:
            transaction.execute(
                """UPDATE installed_registration_agent_retry_requests
                   SET state = ? WHERE request_id = ? AND state = 'reserved'""",
                ("launched" if launched else "failed", request_id),
            )

    def _advance_for_publication(self, activity_id: str, project_id: str) -> int:
        with self.database.transaction() as transaction:
            row = _activity_row(transaction, activity_id)
            version = int(row[4]) + 1
            self.records.update_activity(
                transaction,
                ActivityRecord(
                    activity_id,
                    project_id,
                    "registration",
                    str(row[1]),
                    "running",
                    version,
                    waiting_reason="Publishing reviewed registration candidate",
                    started_at=None if row[3] is None else str(row[3]),
                ),
                expected_record_version=int(row[4]),
            )
            transaction.execute(
                "UPDATE entity_versions SET version = ? WHERE entity_id = ?",
                (version, activity_id),
            )
            _append_registration_event_in(
                transaction,
                project_id,
                activity_id,
                "registration.publication-started",
                {
                    "activity_id": activity_id,
                    "state": "running",
                    "version": version,
                },
            )
        return version

    def _set_activity_presentation(
        self,
        activity_id: str,
        state: str,
        reason: str,
        actions: tuple[ActivityAction, ...],
    ) -> None:
        with self.database.transaction() as transaction:
            self._set_activity_presentation_in(
                transaction, activity_id, state, reason, actions
            )

    @staticmethod
    def _set_activity_presentation_in(
        transaction: Transaction,
        activity_id: str,
        state: str,
        reason: str,
        actions: tuple[ActivityAction, ...],
    ) -> None:
        current = transaction.execute(
            """SELECT project_id, state, waiting_reason, version
               FROM service_activities WHERE activity_id = ?""",
            (activity_id,),
        ).fetchone()
        if current is None:
            raise ValueError("registration activity is unavailable")
        current_actions = tuple(
            (str(row[0]), str(row[1]), str(row[2]))
            for row in transaction.execute(
                """SELECT action_id, kind, label FROM service_activity_actions
                   WHERE activity_id = ? ORDER BY sequence""",
                (activity_id,),
            ).fetchall()
        )
        next_actions = tuple(
            (action.action_id, action.kind, action.label) for action in actions
        )
        if (
            str(current[1]) == state
            and (None if current[2] is None else str(current[2])) == reason
            and current_actions == next_actions
        ):
            return
        next_version = int(current[3]) + 1
        transaction.execute(
            """UPDATE service_activities
               SET state = ?, waiting_reason = ?, version = ?
               WHERE activity_id = ? AND version = ?""",
            (state, reason, next_version, activity_id, int(current[3])),
        )
        transaction.execute(
            """INSERT INTO entity_versions(entity_id, version) VALUES (?, ?)
               ON CONFLICT(entity_id) DO UPDATE SET version = excluded.version""",
            (activity_id, next_version),
        )
        transaction.execute(
            """UPDATE registration_candidate_publications
               SET activity_version = ?
               WHERE activity_id = ? AND state IN ('prepared', 'published')""",
            (next_version, activity_id),
        )
        transaction.execute(
            "DELETE FROM service_activity_actions WHERE activity_id = ?",
            (activity_id,),
        )
        transaction.executemany(
            """INSERT INTO service_activity_actions(
                   action_id, activity_id, project_id, kind, label
               ) SELECT ?, activity_id, project_id, ?, ?
                 FROM service_activities WHERE activity_id = ?""",
            tuple(
                (action.action_id, action.kind, action.label, activity_id)
                for action in actions
            ),
        )
        _append_registration_event_in(
            transaction,
            str(current[0]),
            activity_id,
            "registration.activity-updated",
            {
                "activity_id": activity_id,
                "state": state,
                "waiting_reason": reason,
                "version": next_version,
            },
        )

    def _source_consistency(
        self, assessment: RegistrationAssessment
    ) -> tuple[dict[str, object], RegistrationIntakeResult]:
        """Resolve a symbolic selector and compare only authoritative planning inputs."""
        context = assessment.context
        reviewed = context.source_inventory
        if not reviewed.source_ref.startswith(("refs/heads/", "refs/tags/")):
            return (
                {
                    "state": "exact_commit",
                    "source_ref": reviewed.source_ref,
                    "reviewed_commit": reviewed.source_commit,
                    "observed_commit": reviewed.source_commit,
                    "changed_paths": [],
                    "retained": False,
                },
                self.binding.saved_intake_result(context.activity_id),
            )
        dependencies = self._require_runtime()
        if self.intake is None:
            raise ValueError("installed registration intake is not configured")
        request = RegistrationIntakeRequest(
            repository=context.package_context.source_repository,
            remote=dependencies.remote_for_repository(
                context.package_context.source_repository
            ),
            overview_path=reviewed.overview_path,
            referenced_paths=tuple(
                item.path for item in reviewed.source_references
            ),
            source_ref=reviewed.source_ref,
            prior_source_ref=None,
            publication_branch=context.package_context.publication_branch,
            scope=context.selected_scope,
            architect_selection=(
                f"{context.routes.architect.tool}:"
                f"{context.routes.architect.requested_model_id}"
            ),
            reviewer_selection=(
                f"{context.routes.fidelity_reviewer.tool}:"
                f"{context.routes.fidelity_reviewer.requested_model_id}"
            ),
        )
        updated = self.intake.begin(request, questions=_CollectedQuestions())
        assert updated.inventory is not None
        current = updated.inventory
        before = {item.path: item.sha256 for item in reviewed.blobs}
        after = {item.path: item.sha256 for item in current.blobs}
        changed_paths = sorted(
            path for path in set(before) | set(after) if before.get(path) != after.get(path)
        )
        relevant = (
            bool(changed_paths)
            or reviewed.source_references != current.source_references
            or reviewed.outcomes != current.outcomes
        )
        state = "changed" if relevant else "unchanged"
        retained = (
            relevant
            and self._has_retained_source_choice(
                context.activity_id, reviewed.source_commit, current.source_commit
            )
        )
        return (
            {
                "state": state,
                "source_ref": reviewed.source_ref,
                "reviewed_commit": reviewed.source_commit,
                "observed_commit": current.source_commit,
                "changed_paths": changed_paths,
                "retained": retained,
            },
            updated,
        )

    def _has_retained_source_choice(
        self, activity_id: str, reviewed_commit: str, observed_commit: str
    ) -> bool:
        with self.database.read_connection() as connection:
            return connection.execute(
                """SELECT 1 FROM installed_registration_source_choices
                   WHERE activity_id = ? AND reviewed_commit = ?
                     AND observed_commit = ?
                     AND choice = 'retain_reviewed_source' AND state = 'retained'
                   LIMIT 1""",
                (activity_id, reviewed_commit, observed_commit),
            ).fetchone() is not None

    def _require_runtime(self) -> RegistrationRuntimeDependencies:
        if self.dependencies is None:
            raise ValueError(
                self.configuration_error
                or "installed registration runtime is not configured"
            )
        return self.dependencies

    def _require_confirmation(self) -> RegistrationConfirmationService:
        if self.confirmation is None:
            raise ValueError("installed registration publication is not configured")
        return self.confirmation


def build_registration_publication(
    database: Database,
    dependencies: RegistrationRuntimeDependencies,
) -> tuple[PublicationJournal, RegistrationConfirmationService, RegistrationRecoveryService]:
    journal = PublicationJournal(
        database,
        dependencies.authorizer,
        dependencies.transport,
        dependencies.destination_provider,
    )
    confirmation = RegistrationConfirmationService(
        database, journal, dependencies.destination_provider
    )
    routes = {}
    for provider in destination_providers(dependencies.destination_provider):
        profile = provider.profile
        reference = profile.configuration_hash
        if reference in routes:
            raise ValueError("destination profiles require unique configuration hashes")
        routes[reference] = HistoricalPublicationRoute(journal, provider)
    recovery = RegistrationRecoveryService(
        database, journal, HistoricalDestinationProfiles(routes)
    )
    return journal, confirmation, recovery


def _role_selections(payload: Mapping[str, object]) -> RoleSelections:
    return RoleSelections(
        _tool_selection(payload.get("architect_selection"), "architect_selection"),
        _tool_selection(payload.get("reviewer_selection"), "reviewer_selection"),
    )


def _tool_selection(value: object, field: str) -> ToolModelSelection:
    if isinstance(value, Mapping) and set(value) == {"tool", "model_id"}:
        return ToolModelSelection(value["tool"], value["model_id"])  # type: ignore[arg-type]
    text = _text(value, field)
    tool, separator, model_id = text.partition(":")
    if not separator:
        raise ValueError(f"{field} must be tool:model_id")
    return ToolModelSelection(tool, model_id)


def _selection_text(value: object) -> str | None:
    if value is None:
        return None
    if isinstance(value, Mapping) and set(value) == {"tool", "model_id"}:
        return f"{value['tool']}:{value['model_id']}"
    return _text(value, "tool selection")


def _project_id(repository: str) -> str:
    return "project-" + hashlib.sha256(repository.encode("utf-8")).hexdigest()[:24]


def _activity_id(request_id: str) -> str:
    return "registration-" + hashlib.sha256(request_id.encode("utf-8")).hexdigest()[:24]


def _open_entity_id(request_id: str) -> str:
    return "registration-open-" + hashlib.sha256(
        request_id.encode("utf-8")
    ).hexdigest()[:24]


def _start_entity_id(project_id: str, attempt_number: int) -> str:
    return "registration-start-" + hashlib.sha256(
        f"{project_id}\0{attempt_number}".encode("utf-8")
    ).hexdigest()[:24]


def _save_process_snapshot(
    transaction: Transaction, activity_id: str, snapshot: ProcessSnapshot
) -> None:
    transaction.execute(
        """INSERT INTO service_process_snapshots(
               activity_id, process_name, definition_json, definition_sha256,
               bundle_snapshot_json
           ) VALUES (?, ?, ?, ?, ?)""",
        (
            activity_id,
            snapshot.process_name,
            snapshot.definition_json,
            snapshot.definition_sha256,
            canonical_json(snapshot.bundle.as_dict()),
        ),
    )


def _intake_request_record(value: RegistrationIntakeRequest) -> dict[str, object]:
    return {
        "repository": value.repository,
        "remote": value.remote,
        "overview_path": value.overview_path,
        "referenced_paths": list(value.referenced_paths),
        "source_ref": value.source_ref,
        "prior_source_ref": value.prior_source_ref,
        "publication_branch": value.publication_branch,
        "scope": value.scope,
        "architect_selection": value.architect_selection,
        "reviewer_selection": value.reviewer_selection,
    }


def _intake_request_from_record(value: Mapping[str, object]) -> RegistrationIntakeRequest:
    required = {
        "repository", "remote", "overview_path", "referenced_paths", "source_ref",
        "prior_source_ref", "publication_branch", "scope", "architect_selection",
        "reviewer_selection",
    }
    if set(value) != required or not isinstance(value["referenced_paths"], list):
        raise ValueError("saved registration intake request is invalid")
    return RegistrationIntakeRequest(
        repository=_text(value["repository"], "repository"),
        remote=(
            value["remote"]
            if isinstance(value["remote"], str)
            else _text(value["remote"], "remote")
        ),
        overview_path=_optional_text(value["overview_path"]),
        referenced_paths=tuple(
            _text(item, "referenced path") for item in value["referenced_paths"]
        ),
        source_ref=_optional_text(value["source_ref"]),
        prior_source_ref=_optional_text(value["prior_source_ref"]),
        publication_branch=_optional_text(value["publication_branch"]),
        scope=_optional_text(value["scope"]),
        architect_selection=_optional_text(value["architect_selection"]),
        reviewer_selection=_optional_text(value["reviewer_selection"]),
    )


def _activity_row(transaction: Transaction, activity_id: str):
    row = transaction.execute(
        """SELECT project_id, subject, state, started_at, version
           FROM service_activities WHERE activity_id = ?""",
        (activity_id,),
    ).fetchone()
    if row is None:
        raise ValueError("registration activity is unavailable")
    return row


def _text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be nonempty text")
    return value.strip()


def _optional_text(value: object) -> str | None:
    return None if value is None else _text(value, "optional value")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _append_registration_event_in(
    transaction: Transaction,
    project_id: str,
    activity_id: str,
    event_type: str,
    data: Mapping[str, object],
) -> None:
    """Wake connected projections in the same commit as a background transition."""
    transaction.execute(
        """INSERT INTO outbox_events(
               schema_version, event_id, occurred_at, project_id, activity_id,
               type, data_json
           ) VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (
            1,
            f"registration-transition-{uuid.uuid4().hex}",
            _utc_now(),
            project_id,
            activity_id,
            event_type,
            canonical_json(data),
        ),
    )


def _load_candidate_workspace(
    workspace_root: Path,
    assessment: RegistrationAssessment,
    manifest_reference: str,
    manifest_sha256: str,
) -> tuple[Mapping[str, object], Mapping[str, Mapping[str, object]]]:
    run_id = assessment.current_run("project_architect").run_id
    root = workspace_root / assessment.context.project_id / assessment.context.activity_id / "runs" / run_id
    relative = PurePosixPath(manifest_reference)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("candidate manifest path is outside its assigned workspace")
    choices = [root.joinpath(*relative.parts)]
    if not relative.parts or relative.parts[0] not in {"input", "output"}:
        choices.insert(0, root / "output" / relative)
    manifest_path = next((path for path in choices if path.is_file() and not path.is_symlink()), None)
    if manifest_path is None:
        raise ValueError("reviewed candidate manifest is unavailable")
    raw = manifest_path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != manifest_sha256:
        raise ValueError("reviewed candidate manifest hash differs from the saved reference")
    try:
        manifest = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("reviewed candidate manifest is invalid JSON") from error
    if not isinstance(manifest, Mapping) or not isinstance(manifest.get("files"), list):
        raise ValueError("reviewed candidate manifest has no file inventory")
    records: dict[str, Mapping[str, object]] = {}
    for entry in manifest["files"]:
        if not isinstance(entry, Mapping) or not isinstance(entry.get("path"), str):
            raise ValueError("reviewed candidate file inventory is invalid")
        path = PurePosixPath(str(entry["path"]))
        if path.is_absolute() or ".." in path.parts:
            raise ValueError("reviewed candidate record path is unsafe")
        target = manifest_path.parent.joinpath(*path.parts)
        details = os.lstat(target)
        if not stat.S_ISREG(details.st_mode) or target.is_symlink():
            raise ValueError("reviewed candidate record is not a regular file")
        try:
            record = json.loads(target.read_bytes())
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ValueError("reviewed candidate record is invalid JSON") from error
        if not isinstance(record, Mapping):
            raise ValueError("reviewed candidate record must be an object")
        records[str(path)] = record
    return manifest, records
