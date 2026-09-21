"""Installed request and read composition for confirmed registration."""

from __future__ import annotations

import hashlib
import json
import os
import stat
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Callable, Mapping

from maestro.agents.preflight import AgentRoutePreflight
from maestro.agents.routes import RoleSelections, ToolModelSelection
from maestro.foundation import Database, DomainMigration, Transaction, canonical_json
from maestro.foundation.credentials import RepositoryAuthorizer, ServiceGitTransport
from maestro.foundation.git_publication import PublicationError, PublicationJournal
from maestro.foundation.github_destination import (
    GitHubDestinationError,
    GitHubDestinationProvider,
)
from maestro.planning.intake import (
    IntakeQuestion,
    RegistrationIntake,
    RegistrationIntakeRequest,
    RegistrationIntakeResult,
)
from maestro.planning.registration_confirmation import (
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
from maestro.planning.sources import ExactSourceReader

from .activities import ActivityAction, ActivityRecord, ActivityRepository, ProjectRecord
from .authentication import VerifiedActor
from .processes import ProcessSnapshot
from .questions import DeliveredAnswer, LinkedQuestion, QuestionService
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


@dataclass(frozen=True)
class RegistrationRuntimeDependencies:
    """Typed installed dependencies; secrets remain behind their providers."""

    source_reader: ExactSourceReader
    authorizer: RepositoryAuthorizer
    transport: ServiceGitTransport
    destination_provider: GitHubDestinationProvider
    preflight: AgentRoutePreflight
    process_snapshot: ProcessSnapshot
    remote_for_repository: Callable[[str], str]
    overview_path: str = "README.md"
    workspace_root: Path | None = None
    assignment_launcher: Callable[[RegistrationServiceBinding, RegistrationAssessment, str], None] | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.source_reader, ExactSourceReader):
            raise TypeError("registration runtime requires ExactSourceReader")
        if not isinstance(self.authorizer, RepositoryAuthorizer):
            raise TypeError("registration runtime requires RepositoryAuthorizer")
        if not isinstance(self.transport, ServiceGitTransport):
            raise TypeError("registration runtime requires ServiceGitTransport")
        if not isinstance(self.destination_provider, GitHubDestinationProvider):
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
        if not isinstance(self.overview_path, str) or not self.overview_path.strip():
            raise ValueError("registration overview path must be nonempty text")
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
        overview_path = payload.get("overview_path", dependencies.overview_path)
        referenced = payload.get("referenced_paths", [])
        if not isinstance(referenced, list) or any(
            not isinstance(item, str) or not item for item in referenced
        ):
            raise ValueError("registration referenced_paths must be an array of paths")
        branch = _optional_text(payload.get("publication_branch"))
        remote = "" if branch is None else dependencies.remote_for_repository(repository)
        intake_request = RegistrationIntakeRequest(
            repository=repository,
            remote=remote,
            overview_path=_text(overview_path, "overview_path"),
            referenced_paths=tuple(referenced),
            source_ref=_optional_text(payload.get("source_ref")),
            publication_branch=branch,
            scope=_optional_text(payload.get("scope")),
            architect_selection=_selection_text(payload.get("architect_selection")),
            reviewer_selection=_selection_text(payload.get("reviewer_selection")),
        )
        collector = _CollectedQuestions()
        assert self.intake is not None
        intake = self.intake.begin(intake_request, questions=collector)
        selections = None if intake.inventory is None else _role_selections(payload)
        assessment = None
        if selections is not None:
            assessment = self.binding.plugin.start_assessment(
                snapshot=dependencies.process_snapshot,
                activity_id=activity_id,
                project_id=project_id,
                intake=intake,
                selections=selections,
            )
            assessment.bind_process_snapshot(dependencies.process_snapshot)

        def apply(transaction: Transaction, next_version: int) -> OperationResult:
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
                    "running" if assessment is not None else "waiting",
                    next_version,
                    waiting_reason=(
                        None if assessment is not None else "Registration intake needs answers"
                    ),
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
                    "assessment_started" if assessment is not None else "waiting_for_intake",
                ),
            )
            for question in collector.values:
                self._publish_intake_question(transaction, project_id, activity_id, question)
            if assessment is not None and selections is not None:
                self.binding.save_intake_in(
                    transaction, activity_id, project_id, intake, selections
                )
                self.binding.install_started(transaction, assessment)
            return OperationResult(
                data={
                    "project_id": project_id,
                    "activity_id": activity_id,
                    "state": (
                        "assessment_started"
                        if assessment is not None
                        else "waiting_for_intake"
                    ),
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
            after_commit=(
                None
                if assessment is None
                else lambda _result: self._launch_assignment(
                    assessment, "project_architect"
                )
            ),
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
        actor = VerifiedActor(self.owner_id)
        with self.database.read_connection() as connection:
            recovery_attempt = connection.execute(
                "SELECT 1 FROM registration_recovery_attempts WHERE activity_id = ?",
                (request.activity_id,),
            ).fetchone()
        if recovery_attempt is not None:
            if self.recovery is None:
                raise ValueError("installed registration recovery is not configured")
            result = self.recovery.confirm_replacement(
                request.activity_id, confirmation, assessment, actor, action
            )
        else:
            result = confirmation.confirm(assessment, actor, action)

        def apply(transaction: Transaction, next_version: int) -> OperationResult:
            row = _activity_row(transaction, request.activity_id)
            self.records.update_activity(
                transaction,
                ActivityRecord(
                    request.activity_id,
                    request.project_id,
                    "registration",
                    str(row[1]),
                    "completed",
                    next_version,
                    started_at=None if row[3] is None else str(row[3]),
                    ended_at=_utc_now(),
                ),
                expected_record_version=request.expected_version,
            )
            project = transaction.execute(
                "SELECT name, version FROM service_projects WHERE project_id = ?",
                (request.project_id,),
            ).fetchone()
            if project is None:
                raise ValueError("registration project is unavailable")
            self.records.update_project(
                transaction,
                ProjectRecord(
                    request.project_id, str(project[0]), "registered", int(project[1]) + 1
                ),
                expected_record_version=int(project[1]),
            )
            return OperationResult(
                data={
                    "status": result.status,
                    "package_ref": result.package_ref.as_dict(),
                    "confirmation_ref": result.confirmation_ref.as_dict(),
                    "remote_commit": result.remote_commit,
                },
                project_id=request.project_id,
                activity_id=request.activity_id,
            )

        return PreparedOperation(
            entity_id=request.activity_id,
            event_type="registration.confirmed",
            event_data={"confirmation_id": action.confirmation_id},
            apply=apply,
        )

    def prepare_cancel(self, request: RequestEnvelope) -> PreparedOperation:
        confirmation = self._require_confirmation()
        if request.project_id is None or request.activity_id is None:
            raise ValueError("registration.cancel requires project and activity context")
        if request.question_id is not None or request.expected_version is None:
            raise ValueError("registration.cancel requires an exact activity version")
        if set(request.payload) - {"operation_id"}:
            raise ValueError("registration.cancel payload fields do not match the contract")
        confirmation.recover_pending(request.activity_id)
        with self.database.read_connection() as connection:
            confirmed = connection.execute(
                """SELECT 1 FROM registration_confirmations
                   WHERE activity_id = ? AND state = 'confirmed' LIMIT 1""",
                (request.activity_id,),
            ).fetchone()
        if confirmed is not None:
            raise ValueError("a confirmed registration cannot be cancelled")
        if self.recovery is not None:
            with self.database.read_connection() as connection:
                recovery_attempt = connection.execute(
                    """SELECT 1 FROM registration_recovery_attempts
                       WHERE activity_id = ?""",
                    (request.activity_id,),
                ).fetchone()
            if recovery_attempt is not None:
                self.recovery.cancel(
                    request.activity_id,
                    request.request_id,
                    operation_id=_optional_text(request.payload.get("operation_id")),
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
                    "cancelled",
                    next_version,
                    started_at=None if row[3] is None else str(row[3]),
                    ended_at=_utc_now(),
                ),
                expected_record_version=request.expected_version,
            )
            transaction.execute(
                """UPDATE installed_registration_intake SET state = 'cancelled'
                   WHERE activity_id = ?""",
                (request.activity_id,),
            )
            open_questions = transaction.execute(
                """SELECT question_id, version FROM service_questions
                   WHERE activity_id = ?
                     AND status IN ('awaiting_answer', 'clarification_required')""",
                (request.activity_id,),
            ).fetchall()
            for question_id, version in open_questions:
                transaction.execute(
                    """UPDATE service_questions SET status = 'cancelled', version = ?
                       WHERE question_id = ? AND version = ?""",
                    (int(version) + 1, str(question_id), int(version)),
                )
                transaction.execute(
                    """UPDATE entity_versions SET version = ? WHERE entity_id = ?""",
                    (int(version) + 1, str(question_id)),
                )
            active = transaction.execute(
                "SELECT 1 FROM active_registrations WHERE project_id = ?",
                (request.project_id,),
            ).fetchone()
            if active is None:
                project = transaction.execute(
                    """SELECT name, version FROM service_projects
                       WHERE project_id = ?""",
                    (request.project_id,),
                ).fetchone()
                if project is None:
                    raise ValueError("registration project is unavailable")
                self.records.update_project(
                    transaction,
                    ProjectRecord(
                        request.project_id,
                        str(project[0]),
                        "not_registered",
                        int(project[1]) + 1,
                    ),
                    expected_record_version=int(project[1]),
                )
            return OperationResult(
                data={"state": "cancelled"},
                project_id=request.project_id,
                activity_id=request.activity_id,
            )

        return PreparedOperation(
            entity_id=request.activity_id,
            event_type="registration.cancelled",
            event_data={"activity_id": request.activity_id},
            apply=apply,
        )

    def prepare_retry(self, request: RequestEnvelope) -> PreparedOperation:
        confirmation = self._require_confirmation()
        if request.project_id is None or request.activity_id is None:
            raise ValueError("registration.retry requires project and activity context")
        if request.question_id is not None or request.expected_version is None:
            raise ValueError("registration.retry requires an exact activity version")
        if set(request.payload) != {"publication_operation_id", "intervention"}:
            raise ValueError(
                "registration.retry requires publication_operation_id and intervention"
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
                expected_parent=active.package_ref.commit,
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
            recovered = confirmation.recover_pending(request.activity_id)

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
        package = None if candidate is None else json.loads(str(candidate[0]))
        activity_state = str(activity[1])
        state = activity_state
        ready = False
        if assessment is not None:
            saved = json.loads(str(assessment[0]))
            state = str(saved.get("state", state)).replace("_", " ").title()
            ready = saved.get("state") == "ready"
        history = (
            []
            if self.confirmation is None
            else [item.as_dict() for item in self.confirmation.history(str(activity[0]))]
        )
        return {
            "project_id": str(activity[0]),
            "activity_id": activity_id,
            "activity_version": int(activity[2]),
            "state": state,
            "package_ref": package,
            "history": history,
            "can_confirm": bool(
                ready
                and package is not None
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
        recovered: tuple[dict[str, object], ...] = ()
        if self.confirmation is not None:
            try:
                recovered = self.confirmation.recover_pending(
                    continue_on_error=True
                )
            except (
                GitHubDestinationError,
                PublicationError,
                RegistrationConfirmationError,
            ) as error:
                errors.append({"kind": "publication", "message": str(error)})
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
        return {
            "restored_assessments": restored,
            "recovered_publications": recovered,
            "unfinished_recoveries": tuple(recovery_activities),
            "errors": tuple(errors),
        }

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
            "scope", "publication_branch", "architect_selection", "reviewer_selection"
        }:
            raise ValueError("saved registration intake question field is invalid")
        saved_request[field] = answer.text.strip()
        branch = _optional_text(saved_request.get("publication_branch"))
        repository = _text(saved_request.get("repository"), "repository")
        saved_request["remote"] = (
            "" if branch is None else dependencies.remote_for_repository(repository)
        )
        intake_request = _intake_request_from_record(saved_request)
        try:
            saved_intake = RegistrationIntakeResult.from_json(str(row[5]))
        except (TypeError, ValueError):
            saved_intake = None
        collector = _CollectedQuestions()
        if saved_intake is not None and saved_intake.inventory is not None:
            intake = saved_intake
        else:
            assert self.intake is not None
            intake = self.intake.begin(intake_request, questions=collector)
        if intake.inventory is None:
            with self.database.transaction() as transaction:
                transaction.execute(
                    """UPDATE installed_registration_intake
                       SET request_json = ?, intake_json = ?
                       WHERE activity_id = ? AND state = 'waiting_for_intake'""",
                    (
                        canonical_json(saved_request),
                        intake.to_json(),
                        answer.activity_id,
                    ),
                )
            return
        with self.database.transaction() as transaction:
            transaction.execute(
                """UPDATE installed_registration_intake
                   SET request_json = ?, intake_json = ?
                   WHERE activity_id = ? AND state = 'waiting_for_intake'""",
                (
                    canonical_json(saved_request),
                    intake.to_json(),
                    answer.activity_id,
                ),
            )
        selections = RoleSelections(
            _tool_selection(intake_request.architect_selection, "architect_selection"),
            _tool_selection(intake_request.reviewer_selection, "reviewer_selection"),
        )
        assessment = self.binding.plugin.start_assessment(
            snapshot=dependencies.process_snapshot,
            activity_id=answer.activity_id,
            project_id=str(row[2]),
            intake=intake,
            selections=selections,
        )
        assessment.bind_process_snapshot(dependencies.process_snapshot)
        with self.database.transaction() as transaction:
            activity = _activity_row(transaction, answer.activity_id)
            current_version = int(activity[4])
            self.records.update_activity(
                transaction,
                ActivityRecord(
                    answer.activity_id,
                    str(row[2]),
                    "registration",
                    str(activity[1]),
                    "running",
                    current_version + 1,
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
                (current_version + 1, answer.activity_id),
            )
            self.binding.save_intake_in(
                transaction, answer.activity_id, str(row[2]), intake, selections
            )
            self.binding.install_started(transaction, assessment)
            transaction.execute(
                """UPDATE installed_registration_intake
                   SET request_json = ?, intake_json = ?, state = 'assessment_started'
                   WHERE activity_id = ? AND state = 'waiting_for_intake'""",
                (
                    canonical_json(saved_request),
                    intake.to_json(),
                    answer.activity_id,
                ),
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
            if assessment.status.review_count:
                assessment = self.binding.prepare_next_review(assessment)
            self._launch_assignment(assessment, "fidelity_reviewer")
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
        candidate = assessment.require_ready_candidate()
        operation_id = f"registration-candidate-{activity_id}-{candidate.version}"
        request_id = f"registration-publication-{activity_id}-{candidate.version}"
        version = self._advance_for_publication(activity_id, project_id)
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
                expected_parent=(
                    assessment.context.source_inventory.source_commit
                    if active is None
                    else active.package_ref.commit
                ),
                operation_id=operation_id,
                request_id=request_id,
            )
            if active is not None:
                assert self.recovery is not None
                self.recovery.record_candidate_from_saved_reasons(activity_id, package)
            self._set_activity_presentation(
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
        except (OSError, RuntimeError, ValueError) as error:
            self._set_activity_presentation(
                activity_id,
                "paused",
                f"Candidate publication needs intervention: {error}",
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

    def _launch_assignment(
        self, assessment: RegistrationAssessment, role: str
    ) -> None:
        if self.dependencies is None or self.dependencies.assignment_launcher is None:
            return
        try:
            self.dependencies.assignment_launcher(self.binding, assessment, role)
        except (OSError, RuntimeError, ValueError) as error:
            self._set_activity_presentation(
                assessment.context.activity_id,
                "paused",
                f"Agent assignment could not start: {error}",
                (
                    ActivityAction(
                        "registration-cancel", "Cancel registration", "decision"
                    ),
                ),
            )

    def _assignment_failed(self, activity_id: str, reason: str) -> None:
        self._set_activity_presentation(
            activity_id,
            "paused",
            f"Agent assignment needs intervention: {reason}",
            (
                ActivityAction(
                    "registration-cancel", "Cancel registration", "decision"
                ),
            ),
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
        return version

    def _set_activity_presentation(
        self,
        activity_id: str,
        state: str,
        reason: str,
        actions: tuple[ActivityAction, ...],
    ) -> None:
        with self.database.transaction() as transaction:
            transaction.execute(
                "UPDATE service_activities SET state = ?, waiting_reason = ? WHERE activity_id = ?",
                (state, reason, activity_id),
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
    profile = dependencies.destination_provider.profile
    routes = {}
    for repository in profile.allowed_repositories:
        for branch in profile.allowed_branches:
            reference = hashlib.sha256(
                canonical_json(profile.snapshot(repository, branch)).encode("utf-8")
            ).hexdigest()
            routes[reference] = HistoricalPublicationRoute(
                journal, dependencies.destination_provider
            )
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
        overview_path=_text(value["overview_path"], "overview_path"),
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
