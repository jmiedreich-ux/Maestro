"""Idle re-registration, comparison, cancellation, and publication recovery."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import dataclass
from typing import Any, Mapping

from maestro.foundation import Database, DomainMigration, Transaction, canonical_identifier, canonical_json
from maestro.foundation.git_publication import (
    PublicationAccessError,
    PublicationConflictError,
    PublicationJournal,
    PublicationStateError,
)
from maestro.foundation.github_destination import (
    GitHubDestinationAuthorization,
    GitHubDestinationProvider,
    destination_provider_for,
)
from maestro.service.authentication import VerifiedActor
from maestro.service.processes import ProcessSnapshot
from maestro.service.resources import BundleSnapshot, ProcessResourceError

from .intake import IntakeError, RegistrationIntakeResult
from .registration import RegistrationAssessment
from .registration_confirmation import (
    ConfirmationResult,
    OwnerConfirmation,
    RegistrationConfirmationError,
    RegistrationConfirmationService,
    RegistrationPackageReference,
)
from .registration_records import (
    RegistrationRecordError,
    canonical_record_bytes,
    package_content_hash,
    validate_package_record,
)


class RegistrationRecoveryError(ValueError):
    """A re-registration transition cannot safely proceed."""


class RegistrationRecoverySetupError(RegistrationRecoveryError):
    """The original saved publication authority cannot be safely re-established."""


REGISTRATION_RECOVERY_MIGRATION = DomainMigration(
    domain="registration_recovery",
    version=1,
    identity="registration-recovery-v1",
    statements=(
        """
        CREATE TABLE registration_recovery_attempts(
            activity_id TEXT PRIMARY KEY,
            request_id TEXT NOT NULL UNIQUE,
            project_id TEXT NOT NULL,
            previous_package_ref_json TEXT NOT NULL,
            previous_confirmation_ref_json TEXT NOT NULL,
            next_registration_version INTEGER NOT NULL CHECK(next_registration_version > 1),
            destination_snapshot_json TEXT NOT NULL,
            destination_snapshot_reference TEXT NOT NULL,
            continuity_json TEXT NOT NULL,
            state TEXT NOT NULL CHECK(state IN (
                'reserved', 'candidate_ready', 'pending_confirmation',
                'cancelling', 'paused', 'cancelled', 'completed'
            )),
            candidate_package_ref_json TEXT,
            comparison_json TEXT,
            pending_operation_id TEXT,
            automatic_publication_limit INTEGER NOT NULL CHECK(automatic_publication_limit >= 0),
            automatic_publication_retries INTEGER NOT NULL DEFAULT 0
                CHECK(automatic_publication_retries >= 0),
            manual_publication_retries INTEGER NOT NULL DEFAULT 0
                CHECK(manual_publication_retries >= 0),
            failure TEXT,
            process_snapshot_json TEXT NOT NULL,
            cancellation_request_id TEXT UNIQUE
        )
        """,
        """
        CREATE UNIQUE INDEX registration_recovery_active_project
        ON registration_recovery_attempts(project_id)
        WHERE state NOT IN ('cancelled', 'completed')
        """,
        """
        CREATE TABLE registration_recovery_retry_requests(
            request_id TEXT PRIMARY KEY,
            activity_id TEXT NOT NULL
                REFERENCES registration_recovery_attempts(activity_id),
            operation_id TEXT NOT NULL,
            kind TEXT NOT NULL CHECK(kind IN ('automatic', 'manual')),
            intervention TEXT,
            state TEXT NOT NULL CHECK(state IN ('reserved', 'completed'))
        )
        """,
    ),
)

REGISTRATION_RECOVERY_RETRY_DISPATCH_MIGRATION = DomainMigration(
    domain="registration_recovery",
    version=2,
    identity="registration-recovery-retry-dispatch-v2",
    statements=(
        """ALTER TABLE registration_recovery_retry_requests
           ADD COLUMN dispatched INTEGER NOT NULL DEFAULT 0
           CHECK(dispatched IN (0, 1))""",
        "UPDATE registration_recovery_retry_requests SET dispatched = 1",
    ),
)

REGISTRATION_RECOVERY_START_RESERVATION_MIGRATION = DomainMigration(
    domain="registration_recovery",
    version=3,
    identity="registration-recovery-start-reservation-v3",
    statements=(
        """
        CREATE TABLE registration_project_reservations(
            activity_id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            state TEXT NOT NULL CHECK(state IN ('reserved', 'bound', 'released'))
        )
        """,
        """
        CREATE UNIQUE INDEX registration_project_active_reservation
        ON registration_project_reservations(project_id)
        WHERE state != 'released'
        """,
    ),
)


def registration_recovery_migrations() -> tuple[DomainMigration, ...]:
    return (
        REGISTRATION_RECOVERY_MIGRATION,
        REGISTRATION_RECOVERY_RETRY_DISPATCH_MIGRATION,
        REGISTRATION_RECOVERY_START_RESERVATION_MIGRATION,
    )


@dataclass(frozen=True)
class RegistrationContinuity:
    """Exact saved registration information that recovery must not reset."""

    source: Mapping[str, object]
    questions: tuple[Mapping[str, object], ...]
    decisions: tuple[Mapping[str, object], ...]
    runs: tuple[Mapping[str, object], ...]
    review: Mapping[str, object]
    retry_counts: Mapping[str, int]
    recovery_counters: tuple[Mapping[str, object], ...]

    def __post_init__(self) -> None:
        value = _plain_json(self.as_dict())
        retry_counts = value["retry_counts"]
        if not isinstance(retry_counts, dict) or any(
            not isinstance(name, str)
            or not name
            or isinstance(count, bool)
            or not isinstance(count, int)
            or count < 0
            for name, count in retry_counts.items()
        ):
            raise RegistrationRecoveryError("registration retry counts are invalid")
        object.__setattr__(self, "source", value["source"])
        object.__setattr__(self, "questions", tuple(value["questions"]))
        object.__setattr__(self, "decisions", tuple(value["decisions"]))
        object.__setattr__(self, "runs", tuple(value["runs"]))
        object.__setattr__(self, "review", value["review"])
        object.__setattr__(self, "retry_counts", value["retry_counts"])
        object.__setattr__(self, "recovery_counters", tuple(value["recovery_counters"]))

    def as_dict(self) -> dict[str, object]:
        return {
            "source": dict(self.source),
            "questions": [dict(item) for item in self.questions],
            "decisions": [dict(item) for item in self.decisions],
            "runs": [dict(item) for item in self.runs],
            "review": dict(self.review),
            "retry_counts": dict(self.retry_counts),
            "recovery_counters": [dict(item) for item in self.recovery_counters],
        }

    @classmethod
    def from_mapping(cls, value: object) -> "RegistrationContinuity":
        if not isinstance(value, Mapping) or set(value) != {
            "source", "questions", "decisions", "runs", "review", "retry_counts",
            "recovery_counters",
        }:
            raise RegistrationRecoveryError("saved registration continuity is invalid")
        if (
            not isinstance(value["source"], Mapping)
            or not isinstance(value["questions"], list)
            or any(not isinstance(item, Mapping) for item in value["questions"])
            or not isinstance(value["decisions"], list)
            or any(not isinstance(item, Mapping) for item in value["decisions"])
            or not isinstance(value["runs"], list)
            or any(not isinstance(item, Mapping) for item in value["runs"])
            or not isinstance(value["review"], Mapping)
            or not isinstance(value["retry_counts"], Mapping)
            or not isinstance(value["recovery_counters"], list)
            or any(not isinstance(item, Mapping) for item in value["recovery_counters"])
        ):
            raise RegistrationRecoveryError("saved registration continuity is invalid")
        return cls(
            value["source"], tuple(value["questions"]), tuple(value["decisions"]),
            tuple(value["runs"]), value["review"], value["retry_counts"],
            tuple(value["recovery_counters"]),  # type: ignore[arg-type]
        )


@dataclass(frozen=True)
class ComparisonItem:
    item_id: str
    subject: str
    version: int
    sha256: str
    area: str

    def __post_init__(self) -> None:
        canonical_identifier(self.item_id, "comparison item_id")
        _text(self.subject, "comparison subject")
        _positive(self.version, "comparison version")
        _sha256(self.sha256, "comparison sha256")
        if self.area not in {"project_milestone", "scope", "completion_requirement"}:
            raise RegistrationRecoveryError("comparison area is invalid")

    def as_dict(self) -> dict[str, object]:
        return {
            "item_id": self.item_id,
            "subject": self.subject,
            "version": self.version,
            "sha256": self.sha256,
            "area": self.area,
        }


@dataclass(frozen=True)
class RegistrationDifference:
    kind: str
    item_id: str
    subject: str
    area: str
    previous_version: int | None
    candidate_version: int | None
    reason_refs: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "kind": self.kind,
            "item_id": self.item_id,
            "subject": self.subject,
            "area": self.area,
            "previous_version": self.previous_version,
            "candidate_version": self.candidate_version,
            "reason_refs": list(self.reason_refs),
        }


@dataclass(frozen=True)
class RegistrationComparison:
    active_package_ref: RegistrationPackageReference
    candidate_package_ref: RegistrationPackageReference
    differences: tuple[RegistrationDifference, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "active_package_ref": self.active_package_ref.as_dict(),
            "candidate_package_ref": self.candidate_package_ref.as_dict(),
            "differences": [item.as_dict() for item in self.differences],
        }


@dataclass(frozen=True)
class RegistrationRecoveryStatus:
    activity_id: str
    project_id: str
    state: str
    previous_package_ref: RegistrationPackageReference
    candidate_package_ref: RegistrationPackageReference | None
    continuity: RegistrationContinuity
    process_snapshot: ProcessSnapshot
    automatic_publication_retries: int
    manual_publication_retries: int
    failure: str | None


@dataclass(frozen=True)
class HistoricalPublicationRoute:
    journal: PublicationJournal
    destination_provider: GitHubDestinationProvider

    def __post_init__(self) -> None:
        if not isinstance(self.journal, PublicationJournal):
            raise TypeError("historical publication route requires PublicationJournal")
        if not isinstance(self.destination_provider, GitHubDestinationProvider):
            raise TypeError("historical publication route requires GitHubDestinationProvider")


class HistoricalDestinationProfiles:
    """Resolve only an explicitly installed route for the exact saved snapshot."""

    def __init__(self, routes: Mapping[str, HistoricalPublicationRoute]) -> None:
        checked: dict[str, HistoricalPublicationRoute] = {}
        for reference, route in routes.items():
            _sha256(reference, "destination snapshot reference")
            if not isinstance(route, HistoricalPublicationRoute):
                raise TypeError("historical destination routes are invalid")
            checked[reference] = route
        self._routes = checked

    def resolve(
        self,
        snapshot: Mapping[str, object],
        snapshot_reference: str,
    ) -> tuple[HistoricalPublicationRoute, GitHubDestinationAuthorization]:
        if _snapshot_reference(snapshot) != snapshot_reference:
            raise RegistrationRecoverySetupError(
                "saved destination-profile snapshot fails its immutable reference"
            )
        credential = snapshot.get("credential_reference")
        repository = snapshot.get("repository")
        branch = snapshot.get("branch")
        if not isinstance(credential, str) or not credential:
            raise RegistrationRecoverySetupError(
                "saved destination-profile credential reference is missing"
            )
        if not isinstance(repository, str) or not isinstance(branch, str):
            raise RegistrationRecoverySetupError(
                "saved destination-profile target is incomplete"
            )
        route = self._routes.get(snapshot_reference)
        if route is None:
            configuration_hash = snapshot.get("configuration_hash")
            if isinstance(configuration_hash, str):
                route = self._routes.get(configuration_hash)
        if route is None:
            raise RegistrationRecoverySetupError(
                "saved destination-profile identity is unavailable"
            )
        expected = route.destination_provider.profile.snapshot(repository, branch)
        if dict(snapshot) != expected:
            raise RegistrationRecoverySetupError(
                "saved destination profile changed and cannot be substituted"
            )
        authorization = route.destination_provider.authorize(repository, branch)
        if authorization.decision != "allowed" or dict(authorization.snapshot) != dict(snapshot):
            reason = authorization.reason or "destination authorization is unavailable"
            raise RegistrationRecoverySetupError(
                f"saved destination profile is {authorization.decision}: {reason}"
            )
        return route, authorization


class RegistrationRecoveryService:
    """Coordinate re-registration without replacing provider-owned confirmation."""

    def __init__(
        self,
        database: Database,
        journal_reader: PublicationJournal,
        historical_profiles: HistoricalDestinationProfiles,
    ) -> None:
        if not isinstance(database, Database):
            raise TypeError("registration recovery requires the service Database")
        if not isinstance(journal_reader, PublicationJournal):
            raise TypeError("registration recovery requires PublicationJournal")
        if not isinstance(historical_profiles, HistoricalDestinationProfiles):
            raise TypeError("registration recovery requires historical destination profiles")
        self.database = database
        self.journal_reader = journal_reader
        self.historical_profiles = historical_profiles
        for migration in registration_recovery_migrations():
            self.database.registry.register(migration)
        self.database.initialize()

    def load_continuity(
        self, project_id: str, activity_id: str
    ) -> RegistrationContinuity:
        """Load the exact service-saved intake and assessment history."""
        canonical_identifier(project_id, "project_id")
        canonical_identifier(activity_id, "activity_id")
        with self.database.read_connection() as connection:
            return self._authoritative_continuity_in(connection, project_id, activity_id)

    def reserve_intake_in(
        self, transaction: Transaction, project_id: str, activity_id: str
    ) -> None:
        """Atomically prove idleness and reserve before re-registration intake."""
        canonical_identifier(project_id, "project_id")
        canonical_identifier(activity_id, "activity_id")
        self._require_idle(transaction, project_id, activity_id)
        try:
            transaction.execute(
                """INSERT INTO registration_project_reservations(
                       activity_id, project_id, state
                   ) VALUES (?, ?, 'reserved')""",
                (activity_id, project_id),
            )
        except sqlite3.IntegrityError as error:
            raise RegistrationRecoveryError(
                "another project-work start already holds the project reservation"
            ) from error

    def release_intake_reservation_in(
        self, transaction: Transaction, activity_id: str
    ) -> None:
        canonical_identifier(activity_id, "activity_id")
        transaction.execute(
            """UPDATE registration_project_reservations SET state = 'released'
               WHERE activity_id = ? AND state != 'released'""",
            (activity_id,),
        )

    def begin(
        self,
        *,
        request_id: str,
        project_id: str,
        activity_id: str,
        destination_authorization: GitHubDestinationAuthorization,
        continuity: RegistrationContinuity,
        process_snapshot: ProcessSnapshot,
    ) -> RegistrationRecoveryStatus:
        """Atomically prove project idleness and hold its re-registration reservation."""
        for field, value in (
            ("request_id", request_id), ("project_id", project_id), ("activity_id", activity_id)
        ):
            canonical_identifier(value, field)
        if not isinstance(destination_authorization, GitHubDestinationAuthorization):
            raise TypeError("re-registration requires destination authorization")
        if destination_authorization.decision != "allowed":
            raise RegistrationRecoverySetupError("re-registration destination is not allowed")
        if not isinstance(continuity, RegistrationContinuity):
            raise TypeError("re-registration requires saved continuity")
        if not isinstance(process_snapshot, ProcessSnapshot):
            raise TypeError("re-registration requires its saved process snapshot")
        process_record = _process_snapshot_record(process_snapshot)
        snapshot = dict(destination_authorization.snapshot)
        snapshot_reference = _snapshot_reference(snapshot)
        self.historical_profiles.resolve(snapshot, snapshot_reference)
        with self.database.transaction() as transaction:
            authoritative_process = self._authoritative_process_snapshot_in(
                transaction, activity_id
            )
            authoritative_process_record = _process_snapshot_record(authoritative_process)
            if process_record != authoritative_process_record:
                raise RegistrationRecoveryError(
                    "registration process snapshot differs from authoritative saved policy"
                )
            recovery_definition = authoritative_process.definition.get("recovery")
            automatic_publication_limit = (
                recovery_definition.get("automatic_recovery_attempts")
                if isinstance(recovery_definition, Mapping) else None
            )
            _nonnegative(automatic_publication_limit, "automatic publication limit")
            authoritative_continuity = self._authoritative_continuity_in(
                transaction, project_id, activity_id
            )
            if continuity != authoritative_continuity:
                raise RegistrationRecoveryError(
                    "registration continuity differs from authoritative saved history"
                )
            replay = transaction.execute(
                "SELECT activity_id FROM registration_recovery_attempts WHERE request_id = ?",
                (request_id,),
            ).fetchone()
            if replay is not None:
                status = self._status_in(transaction, str(replay[0]))
                saved_row = self._attempt_in(transaction, str(replay[0]))
                if (
                    status.project_id != project_id
                    or status.activity_id != activity_id
                    or str(saved_row[6]) != canonical_json(snapshot)
                    or str(saved_row[8]) != canonical_json(continuity.as_dict())
                    or int(saved_row[13]) != automatic_publication_limit
                    or str(saved_row[17]) != canonical_json(process_record)
                ):
                    raise RegistrationRecoveryError(
                        "re-registration request identity was reused with changed content"
                    )
                return status
            active = self._active_in(transaction, project_id)
            if active is None:
                raise RegistrationRecoveryError(
                    "re-registration requires a confirmed active registration"
                )
            previous_package = RegistrationPackageReference.from_mapping(
                json.loads(str(active[1]))
            )
            if snapshot.get("repository") != previous_package.repository:
                raise RegistrationRecoverySetupError(
                    "re-registration destination repository differs from the active registration"
                )
            self._require_idle(transaction, project_id, activity_id)
            try:
                transaction.execute(
                    """INSERT INTO registration_recovery_attempts(
                           activity_id, request_id, project_id,
                           previous_package_ref_json, previous_confirmation_ref_json,
                           next_registration_version, destination_snapshot_json,
                           destination_snapshot_reference, continuity_json, state,
                           candidate_package_ref_json, comparison_json,
                           pending_operation_id, automatic_publication_limit,
                           automatic_publication_retries, manual_publication_retries, failure,
                           process_snapshot_json, cancellation_request_id
                       ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'reserved',
                                 NULL, NULL, NULL, ?, 0, 0, NULL, ?, NULL)""",
                    (
                        activity_id, request_id, project_id,
                        canonical_json(previous_package.as_dict()), str(active[2]),
                        previous_package.registration_version + 1,
                        canonical_json(snapshot), snapshot_reference,
                        canonical_json(authoritative_continuity.as_dict()),
                        automatic_publication_limit,
                        canonical_json(authoritative_process_record),
                    ),
                )
                transaction.execute(
                    """UPDATE registration_project_reservations SET state = 'bound'
                       WHERE activity_id = ? AND project_id = ? AND state = 'reserved'""",
                    (activity_id, project_id),
                )
            except sqlite3.IntegrityError as error:
                raise RegistrationRecoveryError(
                    "another re-registration start already holds the project reservation"
                ) from error
            return self._status_in(transaction, activity_id)

    def require_work_start_allowed(
        self, transaction: Transaction, project_id: str, activity_id: str
    ) -> None:
        """Consumer boundary used in the same transaction as any project-work start."""
        canonical_identifier(project_id, "project_id")
        canonical_identifier(activity_id, "activity_id")
        row = transaction.execute(
            """SELECT activity_id FROM registration_recovery_attempts
               WHERE project_id = ? AND state NOT IN ('cancelled', 'completed')""",
            (project_id,),
        ).fetchone()
        if row is not None and str(row[0]) != activity_id:
            raise RegistrationRecoveryError(
                "project work cannot start while re-registration is reserved"
            )
        early = transaction.execute(
            """SELECT activity_id FROM registration_project_reservations
               WHERE project_id = ? AND state != 'released'""",
            (project_id,),
        ).fetchone()
        if early is not None and str(early[0]) != activity_id:
            raise RegistrationRecoveryError(
                "project work cannot start while re-registration intake is reserved"
            )

    def record_candidate(
        self,
        activity_id: str,
        candidate_package_ref: RegistrationPackageReference,
        reasons: Mapping[str, tuple[str, ...]],
    ) -> RegistrationComparison:
        canonical_identifier(activity_id, "activity_id")
        if not isinstance(candidate_package_ref, RegistrationPackageReference):
            raise TypeError("candidate comparison requires an exact package reference")
        comparison: RegistrationComparison
        with self.database.transaction() as transaction:
            row = self._attempt_in(transaction, activity_id)
            if str(row[9]) not in {"reserved", "candidate_ready"}:
                raise RegistrationRecoveryError("re-registration cannot accept a candidate now")
            active_package = RegistrationPackageReference.from_mapping(json.loads(str(row[3])))
            current = self._active_in(transaction, str(row[2]))
            if current is None or RegistrationPackageReference.from_mapping(
                json.loads(str(current[1]))
            ) != active_package:
                raise RegistrationRecoveryError(
                    "active registration changed before candidate comparison"
                )
            self._require_published_replacement(
                transaction, str(row[2]), activity_id, active_package, candidate_package_ref,
                int(row[5]),
            )
            active_records, exact_active = self._package_records_in(
                transaction, active_package
            )
            candidate_records, exact_candidate = self._package_records_in(
                transaction, candidate_package_ref
            )
            comparison = _compare(
                active_package, candidate_package_ref,
                exact_active, exact_candidate, reasons,
                _reason_references((*active_records.values(), *candidate_records.values())),
            )
            saved_candidate = row[10]
            if saved_candidate is not None:
                if (
                    RegistrationPackageReference.from_mapping(json.loads(str(saved_candidate)))
                    != candidate_package_ref
                    or json.loads(str(row[11])) != comparison.as_dict()
                ):
                    raise RegistrationRecoveryError("saved registration comparison changed")
                return comparison
            transaction.execute(
                """UPDATE registration_recovery_attempts
                   SET state = 'candidate_ready', candidate_package_ref_json = ?,
                       comparison_json = ? WHERE activity_id = ? AND state = 'reserved'""",
                (
                    canonical_json(candidate_package_ref.as_dict()),
                    canonical_json(comparison.as_dict()), activity_id,
                ),
            )
            continuity = self._authoritative_continuity_in(
                transaction, str(row[2]), activity_id
            )
            transaction.execute(
                """UPDATE registration_recovery_attempts SET continuity_json = ?
                   WHERE activity_id = ?""",
                (canonical_json(continuity.as_dict()), activity_id),
            )
        return comparison

    def record_candidate_from_saved_reasons(
        self,
        activity_id: str,
        candidate_package_ref: RegistrationPackageReference,
    ) -> RegistrationComparison:
        """Build comparison reasons only from the published package records."""
        with self.database.read_connection() as connection:
            row = self._attempt_in(connection, activity_id)
            active = RegistrationPackageReference.from_mapping(json.loads(str(row[3])))
            _active_records, active_items = self._package_records_in(connection, active)
            candidate_records, candidate_items = self._package_records_in(
                connection, candidate_package_ref
            )
        before = _unique_items(active_items)
        after = _unique_items(candidate_items)
        changed = {
            item_id
            for item_id in set(before) | set(after)
            if before.get(item_id) != after.get(item_id)
        }
        affected: dict[str, list[str]] = {item_id: [] for item_id in changed}
        fallback: list[str] = []
        for record in candidate_records.values():
            record_type = record.get("record_type")
            identifier = record.get("record_id")
            data = record.get("data")
            if record_type == "decision" and isinstance(identifier, str):
                fallback.append(identifier)
                refs = data.get("affected_refs") if isinstance(data, Mapping) else None
                if isinstance(refs, list):
                    for item_id in changed & {str(value) for value in refs}:
                        affected[item_id].append(identifier)
            elif record_type in {"assessment", "review"} and isinstance(data, Mapping):
                findings = data.get("findings")
                if isinstance(findings, list):
                    for finding in findings:
                        if not isinstance(finding, Mapping):
                            continue
                        identifier = finding.get("finding_id", finding.get("local_key"))
                        if isinstance(identifier, str) and identifier:
                            fallback.append(identifier)
                            items = finding.get("affected_items", [])
                            if isinstance(items, list):
                                for item in items:
                                    if isinstance(item, Mapping):
                                        item_id = item.get("record_id")
                                        if item_id in affected:
                                            affected[str(item_id)].append(identifier)
        if not fallback and changed:
            raise RegistrationRecoveryError(
                "changed registration candidate lacks saved finding or decision reasons"
            )
        reasons = {
            item_id: tuple(dict.fromkeys(values or fallback[:1]))
            for item_id, values in affected.items()
        }
        return self.record_candidate(activity_id, candidate_package_ref, reasons)

    def bind_publication(self, activity_id: str, operation_id: str) -> None:
        canonical_identifier(activity_id, "activity_id")
        canonical_identifier(operation_id, "operation_id")
        operation = self.journal_reader.operation(operation_id)
        with self.database.transaction() as transaction:
            row = self._attempt_in(transaction, activity_id)
            self._require_operation_snapshot(row, operation.authorization_snapshot)
            if operation.operation_type == "registration_candidate":
                owner = transaction.execute(
                    """SELECT project_id, activity_id
                       FROM registration_candidate_publications WHERE operation_id = ?""",
                    (operation_id,),
                ).fetchone()
            elif operation.operation_type == "registration_confirmation":
                owner = transaction.execute(
                    """SELECT project_id, activity_id
                       FROM registration_confirmations WHERE operation_id = ?""",
                    (operation_id,),
                ).fetchone()
            else:
                owner = None
            if owner is None or (str(owner[0]), str(owner[1])) != (
                str(row[2]), activity_id
            ):
                raise RegistrationRecoveryError(
                    "publication operation does not belong to this re-registration activity"
                )
            existing = row[12]
            if existing is not None and str(existing) != operation_id:
                raise RegistrationRecoveryError(
                    "another publication operation is already bound to re-registration"
                )
            transaction.execute(
                """UPDATE registration_recovery_attempts SET pending_operation_id = ?
                   WHERE activity_id = ?""",
                (operation_id, activity_id),
            )

    def recover_candidate_publication(
        self,
        activity_id: str,
        confirmation_service: RegistrationConfirmationService,
        assessment: RegistrationAssessment,
        *,
        activity_version: int,
        manifest: Mapping[str, Any],
        records: Mapping[str, Mapping[str, Any]],
        remote: str,
        expected_parent: str,
        operation_id: str,
        publication_request_id: str,
        retry_request_id: str,
        automatic: bool,
        intervention: str | None = None,
    ) -> RegistrationPackageReference:
        """Reconcile, write if needed, and let the candidate provider apply SQL."""
        if not isinstance(confirmation_service, RegistrationConfirmationService):
            raise TypeError("candidate recovery requires RegistrationConfirmationService")
        try:
            self.bind_publication(activity_id, operation_id)
        except RegistrationRecoverySetupError as error:
            self._pause(activity_id, str(error))
            raise
        canonical_identifier(retry_request_id, "retry_request_id")
        if not automatic:
            _text(intervention, "publication retry intervention")
        row = self._attempt(activity_id)
        reserved = False
        try:
            route, authorization = self._route_for(row, operation_id)
            if (
                confirmation_service.journal is not route.journal
                or destination_provider_for(
                    confirmation_service.destination_provider,
                    str(authorization.snapshot["repository"]),
                ) is not route.destination_provider
            ):
                raise RegistrationRecoverySetupError(
                    "candidate service is not bound to the saved destination profile"
                )
            try:
                route.journal.reconcile(operation_id, authorization)
            except PublicationStateError:
                if route.journal.operation(operation_id).state != "reconciled":
                    raise
                self._reserve_retry(
                    activity_id, operation_id, retry_request_id, automatic, intervention
                )
                reserved = True
            package = confirmation_service.publish_candidate(
                assessment,
                activity_version=activity_version,
                manifest=manifest,
                records=records,
                remote=remote,
                expected_parent=expected_parent,
                operation_id=operation_id,
                request_id=publication_request_id,
                recovery_write_reserved=reserved,
            )
            if reserved:
                self._complete_retry(retry_request_id, activity_id)
            else:
                self._finish_retry_request_if_present(retry_request_id)
                self._clear_failure(activity_id)
            return package
        except (
            RegistrationRecoveryError,
            PublicationAccessError,
            PublicationConflictError,
            PublicationStateError,
            RegistrationConfirmationError,
        ) as error:
            self._pause(activity_id, str(error))
            raise

    def cancel(
        self,
        activity_id: str,
        request_id: str,
        *,
        operation_id: str | None = None,
    ) -> RegistrationRecoveryStatus:
        """Cancel only after any in-flight external write has a known outcome."""
        canonical_identifier(activity_id, "activity_id")
        canonical_identifier(request_id, "request_id")
        if operation_id is not None:
            try:
                self.bind_publication(activity_id, operation_id)
            except RegistrationRecoverySetupError as error:
                self._pause(activity_id, str(error), cancelling=True)
                raise
        with self.database.transaction() as transaction:
            row = self._attempt_in(transaction, activity_id)
            if row[18] is not None and str(row[18]) != request_id:
                raise RegistrationRecoveryError(
                    "cancellation request identity was reused with changed content"
                )
            if str(row[9]) in {"cancelled", "completed"}:
                return self._status_from_row(row)
            pending = transaction.execute(
                """SELECT 1 FROM registration_confirmations
                   WHERE project_id = ? AND state = 'pending'""",
                (str(row[2]),),
            ).fetchone()
            if pending is not None:
                raise RegistrationRecoveryError(
                    "pending confirmation must be recovered before cancellation"
                )
            transaction.execute(
                """UPDATE registration_recovery_attempts
                   SET state = 'cancelling', failure = NULL, cancellation_request_id = ?
                   WHERE activity_id = ?""",
                (request_id, activity_id),
            )
            bound = None if row[12] is None else str(row[12])
        if bound is not None:
            try:
                route, authorization = self._route_for(self._attempt(activity_id), bound)
                try:
                    route.journal.reconcile(bound, authorization)
                except PublicationStateError:
                    if route.journal.operation(bound).state != "reconciled":
                        raise
            except (
                RegistrationRecoverySetupError,
                PublicationAccessError,
                PublicationConflictError,
            ) as error:
                self._pause(activity_id, str(error), cancelling=True)
                raise
        with self.database.transaction() as transaction:
            row = self._attempt_in(transaction, activity_id)
            transaction.execute(
                """UPDATE registration_recovery_attempts
                   SET state = 'cancelled', failure = NULL WHERE activity_id = ?""",
                (activity_id,),
            )
            return self._status_in(transaction, activity_id)

    def recover_confirmation(
        self,
        activity_id: str,
        confirmation_service: RegistrationConfirmationService,
        assessment: RegistrationAssessment,
        actor: VerifiedActor,
        action: OwnerConfirmation,
        *,
        retry_request_id: str,
        automatic: bool,
        intervention: str | None = None,
    ) -> ConfirmationResult:
        """Resume the saved Owner action through the existing confirmation provider."""
        canonical_identifier(activity_id, "activity_id")
        if not isinstance(confirmation_service, RegistrationConfirmationService):
            raise TypeError("confirmation recovery requires RegistrationConfirmationService")
        canonical_identifier(retry_request_id, "retry_request_id")
        if not automatic:
            _text(intervention, "confirmation retry intervention")
        row = self._attempt(activity_id)
        candidate = _optional_package(row[10])
        if (
            candidate is None
            or action.activity_id != activity_id
            or action.project_id != str(row[2])
            or action.package_ref != candidate
        ):
            raise RegistrationRecoveryError(
                "confirmation recovery differs from the saved replacement candidate"
            )
        with self.database.read_connection() as connection:
            pending = connection.execute(
                """SELECT operation_id, state FROM registration_confirmations
                   WHERE request_id = ? AND project_id = ? AND activity_id = ?
                     AND state IN ('pending', 'confirmed')""",
                (action.request_id, action.project_id, action.activity_id),
            ).fetchone()
        if pending is None:
            raise RegistrationRecoveryError("saved confirmation is unavailable for recovery")
        operation_id = str(pending[0])
        try:
            self.bind_publication(activity_id, operation_id)
        except RegistrationRecoverySetupError as error:
            self._pause(activity_id, str(error))
            raise
        row = self._attempt(activity_id)
        reserved = False
        try:
            route, authorization = self._route_for(row, operation_id)
        except RegistrationRecoverySetupError as error:
            self._pause(activity_id, str(error))
            raise
        if (
            confirmation_service.journal is not route.journal
            or destination_provider_for(
                confirmation_service.destination_provider,
                str(authorization.snapshot["repository"]),
            ) is not route.destination_provider
        ):
            error = RegistrationRecoverySetupError(
                "confirmation service is not bound to the saved destination profile"
            )
            self._pause(activity_id, str(error))
            raise error
        try:
            try:
                route.journal.reconcile(operation_id, authorization)
            except PublicationStateError:
                if route.journal.operation(operation_id).state != "reconciled":
                    raise
                self._reserve_retry(
                    activity_id, operation_id, retry_request_id, automatic, intervention
                )
                reserved = True
        except (
            RegistrationRecoveryError,
            PublicationAccessError,
            PublicationConflictError,
            PublicationStateError,
        ) as error:
            self._pause(activity_id, str(error))
            raise
        with self.database.transaction() as transaction:
            transaction.execute(
                """UPDATE registration_recovery_attempts SET state = 'pending_confirmation'
                   WHERE activity_id = ?""",
                (activity_id,),
            )
        try:
            result = confirmation_service.confirm(
                assessment,
                actor,
                action,
                recovery_write_reserved=reserved,
            )
        except Exception as error:
            self._pause(activity_id, str(error))
            raise
        with self.database.transaction() as transaction:
            current = self._active_in(transaction, action.project_id)
            if current is None or RegistrationPackageReference.from_mapping(
                json.loads(str(current[1]))
            ) != candidate:
                raise RegistrationRecoveryError(
                    "confirmation completed without activating the exact replacement"
                )
            transaction.execute(
                """UPDATE registration_recovery_attempts
                   SET state = 'completed', failure = NULL WHERE activity_id = ?""",
                (activity_id,),
            )
        if reserved:
            self._complete_retry(retry_request_id, activity_id, preserve_completed=True)
        else:
            self._finish_retry_request_if_present(retry_request_id)
        return result

    def confirm_replacement(
        self,
        activity_id: str,
        confirmation_service: RegistrationConfirmationService,
        assessment: RegistrationAssessment,
        actor: VerifiedActor,
        action: OwnerConfirmation,
    ) -> ConfirmationResult:
        """Confirm a compared replacement while retaining the old active record."""
        canonical_identifier(activity_id, "activity_id")
        if not isinstance(confirmation_service, RegistrationConfirmationService):
            raise TypeError("replacement confirmation requires RegistrationConfirmationService")
        row = self._attempt(activity_id)
        candidate = _optional_package(row[10])
        if (
            str(row[9]) != "candidate_ready"
            or candidate is None
            or action.activity_id != activity_id
            or action.project_id != str(row[2])
            or action.package_ref != candidate
        ):
            raise RegistrationRecoveryError(
                "replacement confirmation differs from the saved compared candidate"
            )
        with self.database.transaction() as transaction:
            transaction.execute(
                """UPDATE registration_recovery_attempts
                   SET state = 'pending_confirmation', failure = NULL
                   WHERE activity_id = ? AND state = 'candidate_ready'""",
                (activity_id,),
            )
        try:
            result = confirmation_service.confirm(assessment, actor, action)
        except Exception as error:
            self._pause(activity_id, str(error))
            raise
        with self.database.transaction() as transaction:
            current = self._active_in(transaction, action.project_id)
            if current is None or RegistrationPackageReference.from_mapping(
                json.loads(str(current[1]))
            ) != candidate:
                raise RegistrationRecoveryError(
                    "replacement confirmation did not activate the exact candidate"
                )
            transaction.execute(
                """UPDATE registration_recovery_attempts
                   SET state = 'completed', failure = NULL WHERE activity_id = ?""",
                (activity_id,),
            )
        return result

    def status(self, activity_id: str) -> RegistrationRecoveryStatus:
        return self._status_from_row(self._attempt(activity_id))

    def comparison(self, activity_id: str) -> RegistrationComparison:
        row = self._attempt(activity_id)
        if row[11] is None:
            raise RegistrationRecoveryError("registration comparison is not available")
        return _comparison_from_mapping(json.loads(str(row[11])))

    def _route_for(
        self, row: tuple[object, ...], operation_id: str
    ) -> tuple[HistoricalPublicationRoute, GitHubDestinationAuthorization]:
        operation = self.journal_reader.operation(operation_id)
        self._require_operation_snapshot(row, operation.authorization_snapshot)
        snapshot = json.loads(str(row[6]))
        return self.historical_profiles.resolve(snapshot, str(row[7]))

    @staticmethod
    def _require_operation_snapshot(
        row: tuple[object, ...], operation_snapshot: Mapping[str, object]
    ) -> None:
        saved = operation_snapshot.get("snapshot")
        if not isinstance(saved, Mapping) or _snapshot_reference(saved) != str(row[7]):
            raise RegistrationRecoverySetupError(
                "publication operation does not use the original saved destination profile"
            )

    def _reserve_retry(
        self,
        activity_id: str,
        operation_id: str,
        request_id: str,
        automatic: bool,
        intervention: str | None,
    ) -> None:
        with self.database.transaction() as transaction:
            replay = transaction.execute(
                """SELECT activity_id, operation_id, kind, intervention, state, dispatched
                   FROM registration_recovery_retry_requests
                   WHERE request_id = ?""",
                (request_id,),
            ).fetchone()
            kind = "automatic" if automatic else "manual"
            if replay is not None:
                saved_intervention = None if replay[3] is None else str(replay[3])
                if (
                    tuple(map(str, replay[:3])) != (activity_id, operation_id, kind)
                    or saved_intervention != intervention
                ):
                    raise RegistrationRecoveryError(
                        "publication retry request identity was reused with changed content"
                    )
                if int(replay[5]) == 1:
                    raise RegistrationRecoveryError(
                        "publication retry request was already dispatched; reconcile it "
                        "or reserve a new counted retry"
                    )
                transaction.execute(
                    """UPDATE registration_recovery_retry_requests SET dispatched = 1
                       WHERE request_id = ? AND dispatched = 0""",
                    (request_id,),
                )
                return
            row = self._attempt_in(transaction, activity_id)
            if automatic:
                shared = transaction.execute(
                    """SELECT consumed FROM service_process_counters
                       WHERE activity_id = ? AND counter_name = ? AND scope_id = ?""",
                    (activity_id, "automatic_recovery_attempts", operation_id),
                ).fetchone()
                consumed = 0 if shared is None else int(shared[0])
                if consumed >= int(row[13]):
                    raise RegistrationRecoveryError(
                        "automatic publication recovery allowance is exhausted"
                    )
                transaction.execute(
                    """INSERT INTO service_process_counters(
                           activity_id, counter_name, scope_id, consumed
                       ) VALUES (?, ?, ?, ?)
                       ON CONFLICT(activity_id, counter_name, scope_id)
                       DO UPDATE SET consumed = excluded.consumed""",
                    (
                        activity_id, "automatic_recovery_attempts", operation_id,
                        consumed + 1,
                    ),
                )
            transaction.execute(
                """INSERT INTO registration_recovery_retry_requests(
                       request_id, activity_id, operation_id, kind, intervention,
                       state, dispatched
                   ) VALUES (?, ?, ?, ?, ?, 'reserved', 1)""",
                (request_id, activity_id, operation_id, kind, intervention),
            )
            column = (
                "automatic_publication_retries" if automatic
                else "manual_publication_retries"
            )
            transaction.execute(
                f"UPDATE registration_recovery_attempts SET {column} = {column} + 1 "
                "WHERE activity_id = ?",
                (activity_id,),
            )
            continuity = self._authoritative_continuity_in(
                transaction, str(row[2]), activity_id
            )
            transaction.execute(
                """UPDATE registration_recovery_attempts SET continuity_json = ?
                   WHERE activity_id = ?""",
                (canonical_json(continuity.as_dict()), activity_id),
            )

    def _complete_retry(
        self, request_id: str, activity_id: str, *, preserve_completed: bool = False
    ) -> None:
        with self.database.transaction() as transaction:
            transaction.execute(
                """UPDATE registration_recovery_retry_requests SET state = 'completed'
                   WHERE request_id = ?""",
                (request_id,),
            )
            if preserve_completed:
                transaction.execute(
                    """UPDATE registration_recovery_attempts SET failure = NULL
                       WHERE activity_id = ? AND state = 'completed'""",
                    (activity_id,),
                )
            else:
                transaction.execute(
                    """UPDATE registration_recovery_attempts
                       SET state = CASE WHEN candidate_package_ref_json IS NULL
                                        THEN 'reserved' ELSE 'candidate_ready' END,
                           failure = NULL WHERE activity_id = ?""",
                    (activity_id,),
                )

    def _finish_retry_request_if_present(self, request_id: str) -> None:
        with self.database.transaction() as transaction:
            transaction.execute(
                """UPDATE registration_recovery_retry_requests SET state = 'completed'
                   WHERE request_id = ?""",
                (request_id,),
            )

    def _clear_failure(self, activity_id: str) -> None:
        with self.database.transaction() as transaction:
            transaction.execute(
                "UPDATE registration_recovery_attempts SET failure = NULL WHERE activity_id = ?",
                (activity_id,),
            )

    def _pause(self, activity_id: str, failure: str, *, cancelling: bool = False) -> None:
        with self.database.transaction() as transaction:
            transaction.execute(
                """UPDATE registration_recovery_attempts SET state = 'paused', failure = ?
                   WHERE activity_id = ?""",
                (("Cancellation paused: " if cancelling else "") + failure, activity_id),
            )

    def _authoritative_continuity_in(
        self, transaction: Any, project_id: str, activity_id: str
    ) -> RegistrationContinuity:
        activity = transaction.execute(
            """SELECT project_id, kind FROM service_activities
               WHERE activity_id = ?""",
            (activity_id,),
        ).fetchone()
        if activity is None or (str(activity[0]), str(activity[1])) != (
            project_id, "registration"
        ):
            raise RegistrationRecoveryError(
                "re-registration activity history is missing or mismatched"
            )
        intake_row = transaction.execute(
            """SELECT project_id, intake_json FROM registration_assessment_intake
               WHERE activity_id = ?""",
            (activity_id,),
        ).fetchone()
        state_row = transaction.execute(
            """SELECT state_json FROM registration_assessment_state
               WHERE activity_id = ?""",
            (activity_id,),
        ).fetchone()
        run_rows = transaction.execute(
            """SELECT role, assignment_id, run_id, route_json, runtime_identity_json
               FROM registration_assessment_runs
               WHERE activity_id = ? ORDER BY role""",
            (activity_id,),
        ).fetchall()
        if (
            intake_row is None
            or str(intake_row[0]) != project_id
            or state_row is None
            or len(run_rows) != 2
            or {str(row[0]) for row in run_rows}
            != {"project_architect", "fidelity_reviewer"}
        ):
            raise RegistrationRecoveryError(
                "saved registration intake, assessment, review, or retry history is incomplete"
            )
        try:
            intake = RegistrationIntakeResult.from_json(str(intake_row[1]))
            state = json.loads(str(state_row[0]))
        except (IntakeError, TypeError, ValueError, json.JSONDecodeError) as error:
            raise RegistrationRecoveryError(
                "saved registration intake or assessment history is invalid"
            ) from error
        if intake.inventory is None or not isinstance(state, Mapping):
            raise RegistrationRecoveryError(
                "saved registration intake or assessment history is incomplete"
            )
        expected_state_fields = {
            "state", "review_count", "candidate", "assessment",
            "architect_findings", "review_findings", "reviewed_candidate",
            "reviewed_assessment", "current_runs",
        }
        if (
            not expected_state_fields.issubset(state)
            or set(state) - expected_state_fields - {
                "review_grants", "review_limit_resume"
            }
            or state.get("state") != "ready"
            or isinstance(state.get("review_grants", 0), bool)
            or not isinstance(state.get("review_grants", 0), int)
            or int(state.get("review_grants", 0)) < 0
            or state.get("review_limit_resume") not in {
                None, "changes_requested", "awaiting_reviewer"
            }
        ):
            raise RegistrationRecoveryError(
                "saved registration assessment and review are not complete"
            )
        current_runs = state.get("current_runs")
        saved_runs = {
            str(row[0]): {
                "assignment_id": str(row[1]), "run_id": str(row[2])
            }
            for row in run_rows
        }
        if current_runs != saved_runs:
            raise RegistrationRecoveryError(
                "saved registration retry identities differ from assessment history"
            )
        run_records: list[Mapping[str, object]] = []
        for row in run_rows:
            try:
                route = json.loads(str(row[3]))
                runtime_identity = json.loads(str(row[4]))
            except (TypeError, ValueError, json.JSONDecodeError) as error:
                raise RegistrationRecoveryError(
                    "saved registration route or runtime identity is invalid"
                ) from error
            _validate_saved_run(str(row[0]), route, runtime_identity)
            run_records.append({
                "role": str(row[0]),
                "assignment_id": str(row[1]),
                "run_id": str(row[2]),
                "route": route,
                "runtime_identity": runtime_identity,
            })
        has_answer_history = transaction.execute(
            """SELECT 1 FROM sqlite_master
               WHERE type = 'table' AND name = 'service_question_answers'"""
        ).fetchone() is not None
        if has_answer_history:
            questions = transaction.execute(
                """SELECT q.question_id, q.subject, q.prompt, q.requester,
                          q.status, q.version, a.answer_id, a.text, a.choice_id,
                          a.answered_at, a.question_version
                   FROM service_questions AS q
                   LEFT JOIN service_question_answers AS a
                     ON a.question_id = q.question_id
                   WHERE q.project_id = ? AND q.activity_id = ?
                   ORDER BY q.question_id""",
                (project_id, activity_id),
            ).fetchall()
        else:
            questions = transaction.execute(
                """SELECT question_id, subject, prompt, requester, status, version
                   FROM service_questions WHERE project_id = ? AND activity_id = ?
                   ORDER BY question_id""",
                (project_id, activity_id),
            ).fetchall()
            if questions:
                raise RegistrationRecoveryError(
                    "saved registration question and answer history is incomplete"
                )
        question_records_list: list[Mapping[str, object]] = []
        for row in questions:
            answer = None
            if len(row) > 6 and row[6] is not None:
                answer = {
                    "answer_id": str(row[6]),
                    "text": str(row[7]),
                    "choice_id": None if row[8] is None else str(row[8]),
                    "answered_at": str(row[9]),
                    "question_version": int(row[10]),
                }
            if str(row[4]) == "answered" and answer is None:
                raise RegistrationRecoveryError(
                    "saved registration question answer is missing"
                )
            question_records_list.append({
                "question_id": str(row[0]),
                "subject": str(row[1]),
                "prompt": str(row[2]),
                "requester": str(row[3]),
                "status": str(row[4]),
                "version": int(row[5]),
                "answer": answer,
            })
        question_records = tuple(question_records_list)
        previous = transaction.execute(
            """SELECT previous_package_ref_json, candidate_package_ref_json
               FROM registration_recovery_attempts
               WHERE activity_id = ?""",
            (activity_id,),
        ).fetchone()
        if previous is None:
            active = self._active_in(transaction, project_id)
            previous_package = None if active is None else RegistrationPackageReference.from_mapping(
                json.loads(str(active[1]))
            )
        else:
            previous_package = RegistrationPackageReference.from_mapping(
                json.loads(str(previous[1] if previous[1] is not None else previous[0]))
            )
        if previous_package is None:
            raise RegistrationRecoveryError(
                "saved registration decision history is incomplete"
            )
        previous_records, _items = self._package_records_in(
            transaction, previous_package
        )
        decision_records = tuple(
            dict(record) for _path, record in sorted(previous_records.items())
            if record.get("record_type") == "decision"
        )
        if not decision_records:
            raise RegistrationRecoveryError(
                "saved registration decision history is incomplete"
            )
        retry_rows = transaction.execute(
            """SELECT kind, COUNT(*) FROM registration_recovery_retry_requests
               WHERE activity_id = ? GROUP BY kind""",
            (activity_id,),
        ).fetchall()
        observed_retry_counts = {str(row[0]): int(row[1]) for row in retry_rows}
        retry_counts = {
            "automatic_publication": observed_retry_counts.get("automatic", 0),
            "manual_publication": observed_retry_counts.get("manual", 0),
        }
        counter_rows = transaction.execute(
            """SELECT counter_name, scope_id, consumed
               FROM service_process_counters
               WHERE activity_id = ? AND counter_name = 'automatic_recovery_attempts'
               ORDER BY counter_name, scope_id""",
            (activity_id,),
        ).fetchall()
        recovery_counters = tuple({
            "counter_name": str(row[0]),
            "scope_id": str(row[1]),
            "consumed": int(row[2]),
        } for row in counter_rows)
        return RegistrationContinuity(
            source={"intake": intake.to_record()},
            questions=question_records,
            decisions=decision_records,
            runs=tuple(run_records),
            review=state,
            retry_counts=retry_counts,
            recovery_counters=recovery_counters,
        )

    def _package_records_in(
        self, transaction: Transaction, package: RegistrationPackageReference
    ) -> tuple[dict[str, Mapping[str, Any]], tuple[ComparisonItem, ...]]:
        row = transaction.execute(
            """SELECT operation_id, manifest_sha256, content_hash, remote_commit,
                      package_ref_json, state, project_id
               FROM registration_candidate_publications
               WHERE repository = ? AND registration_version = ? AND candidate_id = ?
                 AND package_ref_json = ?""",
            (
                package.repository, package.registration_version, package.candidate_id,
                canonical_json(package.as_dict()),
            ),
        ).fetchone()
        if (
            row is None
            or str(row[1]) != package.manifest_sha256
            or str(row[3]) != package.commit
            or str(row[4]) != canonical_json(package.as_dict())
            or str(row[5]) != "published"
        ):
            raise RegistrationRecoveryError(
                "registration comparison package is not the exact published package"
            )
        operation = self.journal_reader.operation(str(row[0]))
        if (
            operation.operation_type != "registration_candidate"
            or operation.remote_commit != package.commit
            or operation.state not in {"verified", "applied"}
            or package.manifest_path not in operation.files
        ):
            raise RegistrationRecoveryError(
                "registration comparison package publication is not verified"
            )
        manifest_bytes = operation.files[package.manifest_path]
        if hashlib.sha256(manifest_bytes).hexdigest() != package.manifest_sha256:
            raise RegistrationRecoveryError(
                "registration comparison manifest differs from its exact reference"
            )
        try:
            manifest = json.loads(manifest_bytes)
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise RegistrationRecoveryError(
                "registration comparison manifest bytes are invalid"
            ) from error
        if (
            not isinstance(manifest, Mapping)
            or manifest.get("project_id") != str(row[6])
            or manifest.get("registration_version") != package.registration_version
            or manifest.get("candidate_id") != package.candidate_id
            or manifest.get("content_hash") != str(row[2])
            or not isinstance(manifest.get("files"), list)
        ):
            raise RegistrationRecoveryError(
                "registration comparison manifest identity is invalid"
            )
        if canonical_record_bytes(manifest) != manifest_bytes:
            raise RegistrationRecoveryError(
                "registration comparison manifest bytes are not canonical"
            )
        root = package.manifest_path.rsplit("/", 1)[0]
        records: dict[str, Mapping[str, Any]] = {}
        items: list[ComparisonItem] = []
        areas = {
            "summary": "scope",
            "declaration": "scope",
            "naming_conventions": "scope",
            "milestone": "project_milestone",
            "requirement": "completion_requirement",
        }
        try:
            for entry in manifest["files"]:
                if (
                    not isinstance(entry, Mapping)
                    or set(entry) != {
                        "path", "record_id", "record_type", "record_version",
                        "subject", "sha256",
                    }
                    or not isinstance(entry.get("path"), str)
                ):
                    raise RegistrationRecordError("manifest file entry is invalid")
                relative = str(entry["path"])
                target = f"{root}/{relative}"
                if target not in operation.files:
                    raise RegistrationRecordError("manifest record bytes are missing")
                raw = operation.files[target]
                record = validate_package_record(json.loads(raw))
                if canonical_record_bytes(record) != raw:
                    raise RegistrationRecordError("package record bytes are not canonical")
                if hashlib.sha256(raw).hexdigest() != entry.get("sha256"):
                    raise RegistrationRecordError("manifest record hash differs")
                if any(
                    entry.get(field) != record[field]
                    for field in ("record_id", "record_type", "record_version", "subject")
                ):
                    raise RegistrationRecordError("manifest record identity differs")
                records[relative] = record
                area = areas.get(str(record["record_type"]))
                if area is not None:
                    items.append(ComparisonItem(
                        str(record["record_id"]), str(record["subject"]),
                        int(record["record_version"]),
                        hashlib.sha256(raw).hexdigest(), area,
                    ))
            if len(records) != len(manifest["files"]):
                raise RegistrationRecordError("manifest file inventory is not unique")
            if set(operation.files) != {
                package.manifest_path, *(f"{root}/{path}" for path in records)
            }:
                raise RegistrationRecordError("published package contains untracked files")
            if package_content_hash(records) != str(row[2]):
                raise RegistrationRecordError("published package content hash differs")
        except (
            KeyError, TypeError, ValueError, UnicodeDecodeError,
            json.JSONDecodeError, RegistrationRecordError,
        ) as error:
            raise RegistrationRecoveryError(
                "registration comparison package inventory is invalid"
            ) from error
        return records, tuple(sorted(items, key=lambda item: item.item_id))

    def _require_idle(
        self, transaction: Transaction, project_id: str, activity_id: str
    ) -> None:
        active_attempt = transaction.execute(
            """SELECT activity_id FROM registration_recovery_attempts
               WHERE project_id = ? AND state NOT IN ('cancelled', 'completed')""",
            (project_id,),
        ).fetchone()
        if active_attempt is not None:
            raise RegistrationRecoveryError(
                "another re-registration already reserves this project"
            )
        activities = transaction.execute(
            """SELECT subject, state, kind FROM service_activities
               WHERE project_id = ? AND activity_id != ?
                 AND state NOT IN ('completed', 'cancelled')""",
            (project_id, activity_id),
        ).fetchall()
        activities = tuple(
            row for row in activities
            if not (str(row[1]) == "starting" and str(row[2]) == "registration")
        )
        if activities:
            reasons = ", ".join(f"{row[0]} ({row[1]})" for row in activities)
            raise RegistrationRecoveryError(
                f"project is not idle: {reasons}"
            )
        pending_candidate = transaction.execute(
            """SELECT candidate.activity_id
               FROM registration_candidate_publications AS candidate
               WHERE candidate.project_id = ? AND candidate.state = 'prepared'
                 AND NOT EXISTS (
                     SELECT 1 FROM registration_recovery_attempts AS recovery
                     WHERE recovery.activity_id = candidate.activity_id
                       AND recovery.state = 'cancelled'
                 )""",
            (project_id,),
        ).fetchone()
        pending_confirmation = transaction.execute(
            """SELECT confirmation_id FROM registration_confirmations
               WHERE project_id = ? AND state = 'pending'""",
            (project_id,),
        ).fetchone()
        if pending_candidate is not None or pending_confirmation is not None:
            raise RegistrationRecoveryError(
                "project has an unresolved registration publication or activation"
            )

    @staticmethod
    def _active_in(transaction: Transaction, project_id: str) -> tuple[object, ...] | None:
        row = transaction.execute(
            """SELECT confirmation_id, package_ref_json, confirmation_ref_json,
                      index_bytes, remote_commit, activity_version
               FROM active_registrations WHERE project_id = ?""",
            (project_id,),
        ).fetchone()
        return None if row is None else tuple(row)

    @staticmethod
    def _require_published_replacement(
        transaction: Transaction,
        project_id: str,
        activity_id: str,
        active: RegistrationPackageReference,
        candidate: RegistrationPackageReference,
        next_version: int,
    ) -> None:
        row = transaction.execute(
            """SELECT activity_id, state, package_ref_json, previous_registration_ref_json
               FROM registration_candidate_publications
               WHERE project_id = ? AND registration_version = ? AND candidate_id = ?""",
            (project_id, candidate.registration_version, candidate.candidate_id),
        ).fetchone()
        if row is None or str(row[0]) != activity_id or str(row[1]) != "published":
            raise RegistrationRecoveryError(
                "replacement candidate is not the exact published re-registration activity"
            )
        saved = RegistrationPackageReference.from_mapping(json.loads(str(row[2])))
        previous = RegistrationPackageReference.from_mapping(json.loads(str(row[3])))
        if saved != candidate or previous != active or candidate.registration_version != next_version:
            raise RegistrationRecoveryError(
                "replacement candidate does not extend the active registration exactly"
            )

    def _attempt(self, activity_id: str) -> tuple[object, ...]:
        canonical_identifier(activity_id, "activity_id")
        with self.database.read_connection() as connection:
            row = connection.execute(
                "SELECT * FROM registration_recovery_attempts WHERE activity_id = ?",
                (activity_id,),
            ).fetchone()
            if row is not None:
                self._require_continuity_in(connection, tuple(row))
        if row is None:
            raise RegistrationRecoveryError("re-registration attempt was not found")
        return tuple(row)

    def _attempt_in(
        self, transaction: Transaction, activity_id: str
    ) -> tuple[object, ...]:
        row = transaction.execute(
            "SELECT * FROM registration_recovery_attempts WHERE activity_id = ?",
            (activity_id,),
        ).fetchone()
        if row is None:
            raise RegistrationRecoveryError("re-registration attempt was not found")
        result = tuple(row)
        self._require_continuity_in(transaction, result)
        return result

    def _require_continuity_in(
        self, transaction: Any, row: tuple[object, ...]
    ) -> None:
        authoritative_process = self._authoritative_process_snapshot_in(
            transaction, str(row[0])
        )
        if canonical_json(_process_snapshot_record(authoritative_process)) != str(row[17]):
            raise RegistrationRecoveryError(
                "saved registration process snapshot no longer matches authoritative policy"
            )
        authoritative = self._authoritative_continuity_in(
            transaction, str(row[2]), str(row[0])
        )
        if canonical_json(authoritative.as_dict()) != str(row[8]):
            raise RegistrationRecoveryError(
                "saved registration continuity no longer matches authoritative history"
            )

    @staticmethod
    def _authoritative_process_snapshot_in(
        transaction: Any, activity_id: str
    ) -> ProcessSnapshot:
        row = transaction.execute(
            """SELECT process_name, definition_json, definition_sha256,
                      bundle_snapshot_json
               FROM service_process_snapshots WHERE activity_id = ?""",
            (activity_id,),
        ).fetchone()
        if row is None:
            raise RegistrationRecoveryError(
                "saved registration process snapshot is unavailable"
            )
        try:
            snapshot = ProcessSnapshot(
                str(row[0]), str(row[1]), str(row[2]),
                BundleSnapshot.from_dict(json.loads(str(row[3]))),
            )
        except (TypeError, ValueError, json.JSONDecodeError, ProcessResourceError) as error:
            raise RegistrationRecoveryError(
                "saved registration process snapshot is invalid"
            ) from error
        _process_snapshot_record(snapshot)
        return snapshot

    def _status_in(
        self, transaction: Transaction, activity_id: str
    ) -> RegistrationRecoveryStatus:
        return self._status_from_row(self._attempt_in(transaction, activity_id))

    @staticmethod
    def _status_from_row(row: tuple[object, ...]) -> RegistrationRecoveryStatus:
        return RegistrationRecoveryStatus(
            str(row[0]), str(row[2]), str(row[9]),
            RegistrationPackageReference.from_mapping(json.loads(str(row[3]))),
            _optional_package(row[10]),
            RegistrationContinuity.from_mapping(json.loads(str(row[8]))),
            _process_snapshot_from_mapping(json.loads(str(row[17]))),
            int(row[14]), int(row[15]), None if row[16] is None else str(row[16]),
        )


def _reason_references(
    records: tuple[Mapping[str, Any], ...]
) -> set[str]:
    references: set[str] = set()
    for record in records:
        record_type = record.get("record_type")
        if record_type == "decision":
            references.add(str(record["record_id"]))
        if record_type not in {"assessment", "review"}:
            continue
        data = record.get("data")
        findings = data.get("findings") if isinstance(data, Mapping) else None
        if not isinstance(findings, list):
            continue
        for finding in findings:
            if not isinstance(finding, Mapping):
                continue
            identifier = finding.get("finding_id", finding.get("local_key"))
            if isinstance(identifier, str) and identifier:
                references.add(identifier)
    return references


def _validate_saved_run(
    role: str, route: object, runtime_identity: object
) -> None:
    route_fields = {
        "role", "tool", "requested_model_id", "provider", "tool_version",
        "executable", "credential_profile", "settings_profile", "location",
        "capabilities", "context_limit_tokens", "permitted_destinations",
        "configuration_hash",
    }
    identity_fields = {
        "source", "provider", "model_id", "tool_version", "configuration_hash",
    }
    if (
        not isinstance(route, Mapping)
        or set(route) != route_fields
        or not isinstance(runtime_identity, Mapping)
        or set(runtime_identity) != identity_fields
    ):
        raise RegistrationRecoveryError(
            "saved registration route or runtime identity is invalid"
        )
    expected_route_role = {
        "project_architect": "architect",
        "fidelity_reviewer": "fidelity_reviewer",
    }.get(role)
    if (
        expected_route_role is None
        or route["role"] != expected_route_role
        or runtime_identity["source"] != "tool_metadata"
        or runtime_identity["provider"] != route["provider"]
        or runtime_identity["model_id"] != route["requested_model_id"]
        or runtime_identity["tool_version"] != route["tool_version"]
        or runtime_identity["configuration_hash"] != route["configuration_hash"]
    ):
        raise RegistrationRecoveryError(
            "saved registration runtime identity differs from its route"
        )
    _plain_json(route)
    _plain_json(runtime_identity)


def _compare(
    active_ref: RegistrationPackageReference,
    candidate_ref: RegistrationPackageReference,
    active_items: tuple[ComparisonItem, ...],
    candidate_items: tuple[ComparisonItem, ...],
    reasons: Mapping[str, tuple[str, ...]],
    authoritative_reason_refs: set[str],
) -> RegistrationComparison:
    if any(not isinstance(item, ComparisonItem) for item in (*active_items, *candidate_items)):
        raise TypeError("registration comparison requires typed items")
    active = _unique_items(active_items)
    candidate = _unique_items(candidate_items)
    differences: list[RegistrationDifference] = []
    for item_id in sorted(set(active) | set(candidate)):
        before, after = active.get(item_id), candidate.get(item_id)
        if before is not None and after is not None and before == after:
            continue
        reason_refs = reasons.get(item_id)
        if (
            not isinstance(reason_refs, tuple)
            or not reason_refs
            or any(not isinstance(item, str) or not item for item in reason_refs)
        ):
            raise RegistrationRecoveryError(
                f"comparison difference {item_id} lacks finding or decision reasons"
            )
        unknown_reasons = set(reason_refs) - authoritative_reason_refs
        if unknown_reasons:
            raise RegistrationRecoveryError(
                f"comparison difference {item_id} cites an unknown finding or decision"
            )
        if before is None:
            assert after is not None
            kind, subject, area = "added", after.subject, after.area
        elif after is None:
            kind, subject, area = "removed", before.subject, before.area
        else:
            if after.version != before.version + 1:
                raise RegistrationRecoveryError(
                    f"changed comparison item {item_id} must advance exactly one version"
                )
            kind, subject, area = "changed", after.subject, after.area
        differences.append(RegistrationDifference(
            kind, item_id, subject, area,
            None if before is None else before.version,
            None if after is None else after.version,
            reason_refs,
        ))
    if set(reasons) != {item.item_id for item in differences}:
        raise RegistrationRecoveryError(
            "comparison reasons must match the exact changed package items"
        )
    return RegistrationComparison(active_ref, candidate_ref, tuple(differences))


def _unique_items(items: tuple[ComparisonItem, ...]) -> dict[str, ComparisonItem]:
    result = {item.item_id: item for item in items}
    if len(result) != len(items):
        raise RegistrationRecoveryError("registration comparison item identities are not unique")
    return result


def _comparison_from_mapping(value: object) -> RegistrationComparison:
    if not isinstance(value, Mapping) or set(value) != {
        "active_package_ref", "candidate_package_ref", "differences"
    } or not isinstance(value["differences"], list):
        raise RegistrationRecoveryError("saved registration comparison is invalid")
    differences: list[RegistrationDifference] = []
    for item in value["differences"]:
        if not isinstance(item, Mapping) or set(item) != {
            "kind", "item_id", "subject", "area", "previous_version",
            "candidate_version", "reason_refs",
        }:
            raise RegistrationRecoveryError("saved registration comparison is invalid")
        differences.append(RegistrationDifference(
            str(item["kind"]), str(item["item_id"]), str(item["subject"]),
            str(item["area"]), item["previous_version"], item["candidate_version"],
            tuple(item["reason_refs"]),  # type: ignore[arg-type]
        ))
    return RegistrationComparison(
        RegistrationPackageReference.from_mapping(value["active_package_ref"]),
        RegistrationPackageReference.from_mapping(value["candidate_package_ref"]),
        tuple(differences),
    )


def _optional_package(value: object) -> RegistrationPackageReference | None:
    return None if value is None else RegistrationPackageReference.from_mapping(json.loads(str(value)))


def _snapshot_reference(snapshot: Mapping[str, object]) -> str:
    return hashlib.sha256(canonical_json(snapshot).encode("utf-8")).hexdigest()


def _process_snapshot_record(snapshot: ProcessSnapshot) -> dict[str, object]:
    if snapshot.process_name != "registration":
        raise RegistrationRecoveryError("re-registration process snapshot is not registration")
    if canonical_json(snapshot.definition) != snapshot.definition_json:
        raise RegistrationRecoveryError("re-registration process definition is not canonical")
    if hashlib.sha256(snapshot.definition_json.encode("utf-8")).hexdigest() != snapshot.definition_sha256:
        raise RegistrationRecoveryError("re-registration process snapshot hash differs")
    return {
        "process_name": snapshot.process_name,
        "definition_json": snapshot.definition_json,
        "definition_sha256": snapshot.definition_sha256,
        "bundle": snapshot.bundle.as_dict(),
    }


def _process_snapshot_from_mapping(value: object) -> ProcessSnapshot:
    if not isinstance(value, Mapping) or set(value) != {
        "process_name", "definition_json", "definition_sha256", "bundle"
    } or not isinstance(value["bundle"], Mapping):
        raise RegistrationRecoveryError("saved re-registration process snapshot is invalid")
    try:
        snapshot = ProcessSnapshot(
            str(value["process_name"]), str(value["definition_json"]),
            str(value["definition_sha256"]), BundleSnapshot.from_dict(value["bundle"]),
        )
    except (TypeError, ValueError, ProcessResourceError) as error:
        raise RegistrationRecoveryError(
            "saved re-registration process snapshot is invalid"
        ) from error
    _process_snapshot_record(snapshot)
    return snapshot


def _plain_json(value: object) -> Any:
    try:
        return json.loads(json.dumps(value, allow_nan=False))
    except (TypeError, ValueError, UnicodeError) as error:
        raise RegistrationRecoveryError("registration continuity must contain plain JSON") from error


def _text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RegistrationRecoveryError(f"{field} must be nonempty text")
    return value


def _positive(value: object, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise RegistrationRecoveryError(f"{field} must be a positive integer")
    return value


def _nonnegative(value: object, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise RegistrationRecoveryError(f"{field} must be nonnegative")
    return value


def _sha256(value: object, field: str) -> str:
    text = _text(value, field)
    if len(text) != 64 or any(character not in "0123456789abcdef" for character in text):
        raise RegistrationRecoveryError(f"{field} must be a lowercase SHA-256")
    return text
