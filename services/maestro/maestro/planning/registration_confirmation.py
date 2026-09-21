"""Exact registration package publication and explicit Owner activation."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import dataclass
from typing import Any, Mapping

from maestro.foundation import (
    Database,
    DomainMigration,
    Transaction,
    canonical_identifier,
    canonical_json,
)
from maestro.foundation.git_publication import (
    PublicationError,
    PublicationJournal,
    PublicationResult,
    PublicationStateError,
)
from maestro.foundation.github_destination import (
    GitHubDestination,
    GitHubDestinationAuthorization,
    GitHubDestinationError,
    GitHubDestinationProvider,
    GitHubDestinationRouter,
)
from maestro.foundation.git_read import GitReadError, validate_object_id
from maestro.service.authentication import OWNER_AUTHORITY, VerifiedActor

from .registration import RegistrationAssessment
from .registration_records import (
    RegistrationRecordError,
    canonical_record_bytes,
    validate_registration_package,
)


class RegistrationConfirmationError(ValueError):
    """A package publication or confirmation cannot safely proceed."""


REGISTRATION_CONFIRMATION_MIGRATION = DomainMigration(
    domain="registration_confirmation",
    version=1,
    identity="registration-confirmation-v1",
    statements=(
        """
        CREATE TABLE registration_candidate_publications(
            project_id TEXT NOT NULL,
            activity_id TEXT NOT NULL,
            activity_version INTEGER NOT NULL CHECK(activity_version > 0),
            registration_version INTEGER NOT NULL CHECK(registration_version > 0),
            candidate_id TEXT NOT NULL,
            repository TEXT NOT NULL,
            branch TEXT NOT NULL,
            remote TEXT NOT NULL,
            destination_snapshot_reference TEXT NOT NULL,
            manifest_path TEXT NOT NULL,
            manifest_sha256 TEXT NOT NULL,
            content_hash TEXT NOT NULL,
            assessment_candidate_sha256 TEXT NOT NULL,
            operation_id TEXT NOT NULL UNIQUE,
            request_id TEXT NOT NULL UNIQUE,
            expected_parent TEXT NOT NULL,
            state TEXT NOT NULL CHECK(state IN ('prepared', 'published')),
            remote_commit TEXT,
            package_ref_json TEXT,
            PRIMARY KEY(project_id, registration_version, candidate_id)
        )
        """,
        """
        CREATE TABLE registration_confirmations(
            sequence INTEGER PRIMARY KEY AUTOINCREMENT,
            confirmation_id TEXT NOT NULL UNIQUE,
            request_id TEXT NOT NULL UNIQUE,
            operation_id TEXT NOT NULL UNIQUE,
            project_id TEXT NOT NULL,
            activity_id TEXT NOT NULL,
            expected_activity_version INTEGER NOT NULL CHECK(expected_activity_version > 0),
            owner_id TEXT NOT NULL,
            confirmed_at TEXT NOT NULL,
            package_ref_json TEXT NOT NULL,
            previous_confirmation_ref_json TEXT,
            receipt_path TEXT NOT NULL,
            receipt_sha256 TEXT NOT NULL,
            receipt_bytes BLOB NOT NULL,
            index_bytes BLOB NOT NULL,
            expected_index_bytes BLOB,
            state TEXT NOT NULL CHECK(state IN ('pending', 'confirmed')),
            remote_commit TEXT,
            confirmation_ref_json TEXT
        )
        """,
        """
        CREATE UNIQUE INDEX registration_pending_confirmation
        ON registration_confirmations(project_id) WHERE state = 'pending'
        """,
        """
        CREATE TABLE active_registrations(
            project_id TEXT PRIMARY KEY,
            confirmation_id TEXT NOT NULL UNIQUE,
            package_ref_json TEXT NOT NULL,
            confirmation_ref_json TEXT NOT NULL,
            index_bytes BLOB NOT NULL,
            remote_commit TEXT NOT NULL,
            activity_version INTEGER NOT NULL CHECK(activity_version > 0)
        )
        """,
    ),
)

REGISTRATION_CONFIRMATION_LINEAGE_MIGRATION = DomainMigration(
    domain="registration_confirmation",
    version=2,
    identity="registration-confirmation-lineage-v2",
    statements=(
        """ALTER TABLE registration_candidate_publications
           ADD COLUMN previous_registration_ref_json TEXT""",
        """UPDATE registration_candidate_publications
           SET previous_registration_ref_json = (
               SELECT json_extract(CAST(publication_files.content AS TEXT),
                                   '$.previous_registration_ref')
               FROM publication_files
               WHERE publication_files.operation_id =
                         registration_candidate_publications.operation_id
                 AND publication_files.path =
                         registration_candidate_publications.manifest_path
           )""",
    ),
)


def registration_confirmation_migrations() -> tuple[DomainMigration, ...]:
    return (
        REGISTRATION_CONFIRMATION_MIGRATION,
        REGISTRATION_CONFIRMATION_LINEAGE_MIGRATION,
    )


@dataclass(frozen=True)
class RegistrationPackageReference:
    repository: str
    commit: str
    registration_version: int
    candidate_id: str
    manifest_path: str
    manifest_sha256: str

    def __post_init__(self) -> None:
        _text(self.repository, "package repository")
        validate_object_id(self.commit, "package commit")
        _positive(self.registration_version, "registration_version")
        canonical_identifier(self.candidate_id, "candidate_id")
        _text(self.manifest_path, "manifest_path")
        _sha256(self.manifest_sha256, "manifest_sha256")

    @classmethod
    def from_mapping(cls, value: object) -> "RegistrationPackageReference":
        fields = {
            "repository", "commit", "registration_version", "candidate_id",
            "manifest_path", "manifest_sha256",
        }
        if not isinstance(value, Mapping) or set(value) != fields:
            raise RegistrationConfirmationError("registration package reference is invalid")
        try:
            return cls(**value)  # type: ignore[arg-type]
        except (TypeError, ValueError, GitReadError) as error:
            raise RegistrationConfirmationError(str(error)) from error

    def as_dict(self) -> dict[str, object]:
        return {
            "repository": self.repository,
            "commit": self.commit,
            "registration_version": self.registration_version,
            "candidate_id": self.candidate_id,
            "manifest_path": self.manifest_path,
            "manifest_sha256": self.manifest_sha256,
        }


@dataclass(frozen=True)
class ConfirmationReference:
    confirmation_id: str
    path: str
    sha256: str

    def as_dict(self) -> dict[str, str]:
        return {
            "confirmation_id": self.confirmation_id,
            "path": self.path,
            "sha256": self.sha256,
        }


@dataclass(frozen=True)
class OwnerConfirmation:
    confirmation_id: str
    request_id: str
    project_id: str
    activity_id: str
    expected_activity_version: int
    package_ref: RegistrationPackageReference
    confirmed_at: str

    def __post_init__(self) -> None:
        for field in ("confirmation_id", "request_id", "project_id", "activity_id"):
            canonical_identifier(getattr(self, field), field)
        _positive(self.expected_activity_version, "expected_activity_version")
        if not isinstance(self.package_ref, RegistrationPackageReference):
            raise RegistrationConfirmationError("confirmation requires an exact package reference")
        _text(self.confirmed_at, "confirmed_at")


@dataclass(frozen=True)
class ConfirmationResult:
    status: str
    package_ref: RegistrationPackageReference
    confirmation_ref: ConfirmationReference
    remote_commit: str
    activity_version: int


class RegistrationConfirmationService:
    """Persist, publish, and activate only an exact eligible registration."""

    def __init__(
        self,
        database: Database,
        journal: PublicationJournal,
        destination_provider: GitHubDestination,
    ) -> None:
        if not isinstance(database, Database):
            raise TypeError("registration confirmation requires the service Database")
        if not isinstance(journal, PublicationJournal):
            raise TypeError("registration confirmation requires PublicationJournal")
        if not isinstance(
            destination_provider, (GitHubDestinationProvider, GitHubDestinationRouter)
        ):
            raise TypeError("registration confirmation requires GitHubDestinationProvider")
        self.database = database
        self.journal = journal
        self.destination_provider = destination_provider
        for migration in registration_confirmation_migrations():
            self.database.registry.register(migration)
        self.database.initialize()

    def publish_candidate(
        self,
        assessment: RegistrationAssessment,
        *,
        activity_version: int,
        manifest: Mapping[str, Any],
        records: Mapping[str, Mapping[str, Any]],
        remote: str,
        expected_parent: str,
        operation_id: str,
        request_id: str,
        recovery_write_reserved: bool = False,
    ) -> RegistrationPackageReference:
        """Publish and record one complete immutable eligible candidate."""
        assessment = _assessment(assessment)
        _positive(activity_version, "activity_version")
        canonical_identifier(operation_id, "operation_id")
        canonical_identifier(request_id, "request_id")
        try:
            expected_parent = validate_object_id(expected_parent, "expected_parent")
        except GitReadError as error:
            raise RegistrationConfirmationError(str(error)) from error
        ready = assessment.require_ready_candidate()
        try:
            validated = validate_registration_package(
                manifest, records, assessment.context.package_context
            )
        except RegistrationRecordError as error:
            raise RegistrationConfirmationError(str(error)) from error
        registration_version = _positive(
            validated["registration_version"], "registration_version"
        )
        previous_value = validated["previous_registration_ref"]
        previous_registration_ref = (
            None
            if previous_value is None
            else RegistrationPackageReference.from_mapping(previous_value)
        )
        candidate_id = str(validated["candidate_id"])
        canonical_identifier(candidate_id, "candidate_id")
        if ready.version != candidate_id:
            raise RegistrationConfirmationError(
                "eligible assessment candidate differs from the package candidate"
            )
        manifest_bytes = canonical_record_bytes(validated)
        manifest_sha256 = hashlib.sha256(manifest_bytes).hexdigest()
        if ready.sha256 != manifest_sha256:
            raise RegistrationConfirmationError(
                "eligible assessment candidate hash differs from the package manifest"
            )
        context = assessment.context.package_context
        root = (
            f".maestro/registrations/versions/{registration_version}/"
            f"candidates/{candidate_id}"
        )
        manifest_path = f"{root}/manifest.json"
        files: dict[str, bytes] = {manifest_path: manifest_bytes}
        for path, record in records.items():
            destination = f"{root}/{path}"
            if destination in files:
                raise RegistrationConfirmationError("candidate package paths are not unique")
            files[destination] = canonical_record_bytes(record)
        authorization = self._fresh_authorization(
            context.source_repository,
            context.publication_branch,
            context.destination_snapshot_reference,
        )
        self._ensure_journal_operation(
            operation_id=operation_id,
            operation_type="registration_candidate",
            request_id=request_id,
            repository=context.source_repository,
            remote=remote,
            branch=context.publication_branch,
            expected_parent=expected_parent,
            files=files,
            expected_files={path: None for path in files},
            authorization=authorization,
        )
        self._save_candidate_prepared(
            assessment=assessment,
            activity_version=activity_version,
            registration_version=registration_version,
            candidate_id=candidate_id,
            remote=remote,
            manifest_path=manifest_path,
            manifest_sha256=manifest_sha256,
            content_hash=str(validated["content_hash"]),
            assessment_candidate_sha256=ready.sha256,
            operation_id=operation_id,
            request_id=request_id,
            expected_parent=expected_parent,
            previous_registration_ref=previous_registration_ref,
        )
        result = self._write_or_recover(
            operation_id,
            context.source_repository,
            context.publication_branch,
            context.destination_snapshot_reference,
            recovery_write_reserved=recovery_write_reserved,
        )
        package_ref = RegistrationPackageReference(
            context.source_repository,
            result.remote_commit,
            registration_version,
            candidate_id,
            manifest_path,
            manifest_sha256,
        )
        with self.database.transaction() as transaction:
            row = transaction.execute(
                """SELECT state, package_ref_json FROM registration_candidate_publications
                   WHERE operation_id = ?""",
                (operation_id,),
            ).fetchone()
            if row is None:
                raise RegistrationConfirmationError("candidate publication record is missing")
            if str(row[0]) == "published":
                saved = RegistrationPackageReference.from_mapping(json.loads(str(row[1])))
                if saved != package_ref:
                    raise RegistrationConfirmationError("published candidate reference changed")
            else:
                transaction.execute(
                    """UPDATE registration_candidate_publications
                       SET state = 'published', remote_commit = ?, package_ref_json = ?
                       WHERE operation_id = ? AND state = 'prepared'""",
                    (result.remote_commit, canonical_json(package_ref.as_dict()), operation_id),
                )
            self.journal.mark_applied(
                transaction, operation_id=operation_id, request_id=request_id
            )
        return package_ref

    def confirm(
        self,
        assessment: RegistrationAssessment,
        actor: VerifiedActor,
        action: OwnerConfirmation,
        *,
        recovery_write_reserved: bool = False,
    ) -> ConfirmationResult:
        """Publish the explicit Owner receipt/index and atomically activate it."""
        assessment = _assessment(assessment)
        if not isinstance(actor, VerifiedActor) or actor.authority != OWNER_AUTHORITY:
            raise RegistrationConfirmationError("confirmation requires authenticated Owner authority")
        canonical_identifier(actor.actor_id, "owner_id")
        if not isinstance(action, OwnerConfirmation):
            raise TypeError("confirmation requires OwnerConfirmation")
        if action.project_id != assessment.context.project_id:
            raise RegistrationConfirmationError("confirmation project differs from assessment")
        if action.activity_id != assessment.context.activity_id:
            raise RegistrationConfirmationError("confirmation activity differs from assessment")
        existing = self._confirmation_by_request(action.request_id)
        if existing is not None:
            self._require_same_confirmation(existing, action, actor)
            return self._complete_confirmation(
                existing, recovery_write_reserved=recovery_write_reserved
            )
        self._eligible_candidate(assessment, action)
        pending = self._pending_confirmation(action.project_id)
        if pending is not None:
            raise RegistrationConfirmationError("another confirmation is pending for this project")
        active = self._active_row(action.project_id)
        previous_ref = None if active is None else json.loads(str(active[2]))
        previous_index = None if active is None else bytes(active[3])
        prior_refs = self._confirmed_refs(action.project_id)
        receipt_path = (
            f".maestro/registrations/confirmations/{action.confirmation_id}.json"
        )
        receipt = {
            "schema_version": 1,
            "confirmation_id": action.confirmation_id,
            "request_id": action.request_id,
            "project_id": action.project_id,
            "package_ref": action.package_ref.as_dict(),
            "owner_id": actor.actor_id,
            "confirmed_at": action.confirmed_at,
            "previous_confirmation_ref": previous_ref,
        }
        receipt_bytes = _json_bytes(receipt)
        confirmation_ref = ConfirmationReference(
            action.confirmation_id,
            receipt_path,
            hashlib.sha256(receipt_bytes).hexdigest(),
        )
        index = {
            "schema_version": 1,
            "project_id": action.project_id,
            "current_confirmation_ref": confirmation_ref.as_dict(),
            "confirmation_refs": [*prior_refs, confirmation_ref.as_dict()],
        }
        index_bytes = _json_bytes(index)
        operation_id = f"registration-confirmation-{action.confirmation_id}"
        try:
            with self.database.transaction() as transaction:
                self._require_current_candidate_lineage(
                    transaction, action.project_id, action.package_ref
                )
                transaction.execute(
                    """INSERT INTO registration_confirmations(
                           confirmation_id, request_id, operation_id, project_id,
                           activity_id, expected_activity_version, owner_id, confirmed_at,
                           package_ref_json, previous_confirmation_ref_json,
                           receipt_path, receipt_sha256, receipt_bytes, index_bytes,
                           expected_index_bytes, state, remote_commit, confirmation_ref_json
                       ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', NULL, NULL)""",
                    (
                        action.confirmation_id,
                        action.request_id,
                        operation_id,
                        action.project_id,
                        action.activity_id,
                        action.expected_activity_version,
                        actor.actor_id,
                        action.confirmed_at,
                        canonical_json(action.package_ref.as_dict()),
                        None if previous_ref is None else canonical_json(previous_ref),
                        receipt_path,
                        confirmation_ref.sha256,
                        receipt_bytes,
                        index_bytes,
                        previous_index,
                    ),
                )
        except sqlite3.IntegrityError as error:
            raise RegistrationConfirmationError(
                "another confirmation or request is already reserved"
            ) from error
        row = self._confirmation_by_request(action.request_id)
        assert row is not None
        return self._complete_confirmation(
            row, recovery_write_reserved=recovery_write_reserved
        )

    def active(self, project_id: str) -> ConfirmationResult | None:
        canonical_identifier(project_id, "project_id")
        row = self._active_row(project_id)
        if row is None:
            return None
        package_ref = RegistrationPackageReference.from_mapping(json.loads(str(row[1])))
        confirmation_ref = _confirmation_ref(json.loads(str(row[2])))
        return ConfirmationResult(
            "Registered", package_ref, confirmation_ref, str(row[4]), int(row[5])
        )

    def history(self, project_id: str) -> tuple[ConfirmationReference, ...]:
        canonical_identifier(project_id, "project_id")
        return tuple(_confirmation_ref(item) for item in self._confirmed_refs(project_id))

    def recover_pending(
        self,
        activity_id: str | None = None,
        *,
        continue_on_error: bool = False,
        reserved_operation_ids: frozenset[str] = frozenset(),
    ) -> tuple[dict[str, object], ...]:
        """Reconcile saved unfinished publications without reconstructing inputs.

        Every byte and destination fact comes from the journal and the
        service-owned registration rows.  Startup recovery never rereads source
        files or invents a replacement candidate.
        """
        if activity_id is not None:
            canonical_identifier(activity_id, "activity_id")
        parameters: tuple[object, ...] = () if activity_id is None else (activity_id,)
        activity_filter = "" if activity_id is None else " AND activity_id = ?"
        with self.database.read_connection() as connection:
            candidates = connection.execute(
                """SELECT operation_id, request_id, repository, branch,
                          destination_snapshot_reference, registration_version,
                          candidate_id, manifest_path, manifest_sha256
                   FROM registration_candidate_publications
                   WHERE state = 'prepared'"""
                + activity_filter
                + " ORDER BY operation_id",
                parameters,
            ).fetchall()
        recovered: list[dict[str, object]] = []
        for row in candidates:
            try:
                result = self._write_or_recover(
                    str(row[0]), str(row[2]), str(row[3]), str(row[4]),
                    recovery_write_reserved=str(row[0]) in reserved_operation_ids,
                )
                package = RegistrationPackageReference(
                    str(row[2]), result.remote_commit, int(row[5]), str(row[6]),
                    str(row[7]), str(row[8]),
                )
                with self.database.transaction() as transaction:
                    transaction.execute(
                        """UPDATE registration_candidate_publications
                           SET state = 'published', remote_commit = ?, package_ref_json = ?
                           WHERE operation_id = ? AND state = 'prepared'""",
                        (
                            result.remote_commit,
                            canonical_json(package.as_dict()),
                            str(row[0]),
                        ),
                    )
                    self.journal.mark_applied(
                        transaction,
                        operation_id=str(row[0]),
                        request_id=str(row[1]),
                    )
                recovered.append(
                    {
                        "kind": "candidate",
                        "operation_id": str(row[0]),
                        "state": "published",
                    }
                )
            except (
                GitHubDestinationError,
                PublicationError,
                RegistrationConfirmationError,
            ) as error:
                if not continue_on_error:
                    raise
                recovered.append(
                    {
                        "kind": "candidate",
                        "operation_id": str(row[0]),
                        "state": "paused",
                        "error": str(error),
                    }
                )

        with self.database.read_connection() as connection:
            confirmations = connection.execute(
                """SELECT confirmation_id, request_id, operation_id, project_id,
                          activity_id, expected_activity_version, owner_id, confirmed_at,
                          package_ref_json, previous_confirmation_ref_json,
                          receipt_path, receipt_sha256, receipt_bytes, index_bytes,
                          expected_index_bytes, state, remote_commit,
                          confirmation_ref_json
                   FROM registration_confirmations
                   WHERE state = 'pending'"""
                + activity_filter
                + " ORDER BY sequence",
                parameters,
            ).fetchall()
        for row in confirmations:
            try:
                result = self._complete_confirmation(
                    tuple(row),
                    recovery_write_reserved=str(row[2]) in reserved_operation_ids,
                )
                recovered.append(
                    {
                        "kind": "confirmation",
                        "confirmation_id": str(row[0]),
                        "state": result.status,
                    }
                )
            except (
                GitHubDestinationError,
                PublicationError,
                RegistrationConfirmationError,
            ) as error:
                if not continue_on_error:
                    raise
                recovered.append(
                    {
                        "kind": "confirmation",
                        "confirmation_id": str(row[0]),
                        "state": "paused",
                        "error": str(error),
                    }
                )
        return tuple(recovered)

    def _complete_confirmation(
        self,
        row: sqlite3.Row | tuple[object, ...],
        *,
        recovery_write_reserved: bool = False,
    ) -> ConfirmationResult:
        state = str(row[15])
        package_ref = RegistrationPackageReference.from_mapping(json.loads(str(row[8])))
        if state == "confirmed":
            return ConfirmationResult(
                "Registered",
                package_ref,
                _confirmation_ref(json.loads(str(row[17]))),
                str(row[16]),
                int(row[5]) + 1,
            )
        candidate = self._candidate_for_reference(package_ref, str(row[3]))
        repository, branch, _remote, snapshot_reference = candidate[0:4]
        authorization = self._fresh_authorization(
            repository, branch, snapshot_reference
        )
        self._ensure_journal_operation(
            operation_id=str(row[2]),
            operation_type="registration_confirmation",
            request_id=str(row[1]),
            repository=repository,
            remote=str(candidate[2]),
            branch=branch,
            expected_parent=package_ref.commit,
            files={
                str(row[10]): bytes(row[12]),
                ".maestro/registrations/index.json": bytes(row[13]),
            },
            expected_files={
                str(row[10]): None,
                ".maestro/registrations/index.json": (
                    None if row[14] is None else bytes(row[14])
                ),
            },
            authorization=authorization,
        )
        result = self._write_or_recover(
            str(row[2]), repository, branch, snapshot_reference,
            recovery_write_reserved=recovery_write_reserved,
        )
        confirmation_ref = ConfirmationReference(
            str(row[0]), str(row[10]), str(row[11])
        )
        with self.database.transaction() as transaction:
            self._require_current_candidate_lineage(
                transaction, str(row[3]), package_ref
            )
            current = transaction.execute(
                """SELECT confirmation_id, confirmation_ref_json
                   FROM active_registrations WHERE project_id = ?""",
                (str(row[3]),),
            ).fetchone()
            expected_previous = None if row[9] is None else json.loads(str(row[9]))
            observed_previous = None if current is None else json.loads(str(current[1]))
            if observed_previous != expected_previous:
                raise RegistrationConfirmationError(
                    "active registration changed while confirmation was pending"
                )
            saved_candidate = transaction.execute(
                """SELECT state, package_ref_json FROM registration_candidate_publications
                   WHERE project_id = ? AND registration_version = ? AND candidate_id = ?""",
                (
                    str(row[3]),
                    package_ref.registration_version,
                    package_ref.candidate_id,
                ),
            ).fetchone()
            if saved_candidate is None or str(saved_candidate[0]) != "published":
                raise RegistrationConfirmationError("confirmation candidate is no longer published")
            if RegistrationPackageReference.from_mapping(
                json.loads(str(saved_candidate[1]))
            ) != package_ref:
                raise RegistrationConfirmationError("confirmation candidate changed before activation")
            self.journal.mark_applied(
                transaction, operation_id=str(row[2]), request_id=str(row[1])
            )
            transaction.execute(
                """UPDATE registration_confirmations
                   SET state = 'confirmed', remote_commit = ?, confirmation_ref_json = ?
                   WHERE confirmation_id = ? AND state = 'pending'""",
                (
                    result.remote_commit,
                    canonical_json(confirmation_ref.as_dict()),
                    str(row[0]),
                ),
            )
            transaction.execute(
                """INSERT INTO active_registrations(
                       project_id, confirmation_id, package_ref_json,
                       confirmation_ref_json, index_bytes, remote_commit, activity_version
                   ) VALUES (?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(project_id) DO UPDATE SET
                       confirmation_id = excluded.confirmation_id,
                       package_ref_json = excluded.package_ref_json,
                       confirmation_ref_json = excluded.confirmation_ref_json,
                       index_bytes = excluded.index_bytes,
                       remote_commit = excluded.remote_commit,
                       activity_version = excluded.activity_version""",
                (
                    str(row[3]),
                    str(row[0]),
                    canonical_json(package_ref.as_dict()),
                    canonical_json(confirmation_ref.as_dict()),
                    bytes(row[13]),
                    result.remote_commit,
                    int(row[5]) + 1,
                ),
            )
        return ConfirmationResult(
            "Registered", package_ref, confirmation_ref, result.remote_commit, int(row[5]) + 1
        )

    def _write_or_recover(
        self, operation_id: str, repository: str, branch: str,
        snapshot_reference: str,
        *,
        recovery_write_reserved: bool = False,
    ) -> PublicationResult:
        operation = self.journal.operation(operation_id)
        authorization = self._fresh_authorization(repository, branch, snapshot_reference)
        if operation.state in {"verified", "applied"}:
            return self.journal.attempt(operation_id, authorization)
        if operation.state == "prepared":
            return self.journal.attempt(operation_id, authorization)
        if operation.state == "reconciled":
            if not recovery_write_reserved:
                raise PublicationStateError(
                    "publication retry requires a saved retry reservation"
                )
            return self.journal.attempt(operation_id, authorization)
        if operation.state in {"writing", "paused"}:
            return self.journal.reconcile(operation_id, authorization)
        raise RegistrationConfirmationError("publication operation has an invalid state")

    def _fresh_authorization(
        self, repository: str, branch: str, snapshot_reference: str
    ) -> GitHubDestinationAuthorization:
        result = self.destination_provider.authorize(repository, branch)
        observed_reference = hashlib.sha256(
            _json_bytes(dict(result.snapshot))
        ).hexdigest()
        if observed_reference != snapshot_reference:
            raise RegistrationConfirmationError(
                "GitHub destination profile changed since registration intake"
            )
        return result

    def _ensure_journal_operation(self, **expected: object) -> None:
        operation_id = str(expected["operation_id"])
        try:
            operation = self.journal.operation(operation_id)
        except PublicationStateError:
            self.journal.prepare(
                operation_id=operation_id,
                operation_type=str(expected["operation_type"]),
                request_id=str(expected["request_id"]),
                repository=str(expected["repository"]),
                remote=str(expected["remote"]),
                branch=str(expected["branch"]),
                expected_parent=str(expected["expected_parent"]),
                files=expected["files"],  # type: ignore[arg-type]
                expected_files=expected["expected_files"],  # type: ignore[arg-type]
                destination_authorization=expected["authorization"],  # type: ignore[arg-type]
            )
            return
        if (
            operation.operation_type != expected["operation_type"]
            or operation.request_id != expected["request_id"]
            or operation.authorization.repository != expected["repository"]
            or operation.authorization.branch != expected["branch"]
            or operation.remote != expected["remote"]
            or operation.expected_parent != expected["expected_parent"]
            or operation.files != expected["files"]
            or operation.expected_files != expected["expected_files"]
        ):
            raise RegistrationConfirmationError(
                "saved publication operation differs from this exact request"
            )

    def _save_candidate_prepared(self, **value: object) -> None:
        assessment = value["assessment"]
        assert isinstance(assessment, RegistrationAssessment)
        previous = value["previous_registration_ref"]
        assert previous is None or isinstance(previous, RegistrationPackageReference)
        context = assessment.context.package_context
        try:
            with self.database.transaction() as transaction:
                existing = transaction.execute(
                    """SELECT project_id, activity_id, activity_version,
                              registration_version, candidate_id, operation_id, request_id,
                              previous_registration_ref_json
                       FROM registration_candidate_publications WHERE operation_id = ?""",
                    (value["operation_id"],),
                ).fetchone()
                if existing is not None:
                    saved_previous = (
                        None
                        if existing[7] is None
                        else RegistrationPackageReference.from_mapping(
                            json.loads(str(existing[7]))
                        )
                    )
                    if any(
                        str(existing[index]) != str(expected)
                        for index, expected in (
                            (0, assessment.context.project_id),
                            (1, assessment.context.activity_id),
                            (2, value["activity_version"]),
                            (3, value["registration_version"]),
                            (4, value["candidate_id"]),
                            (5, value["operation_id"]),
                            (6, value["request_id"]),
                        )
                    ) or saved_previous != previous:
                        raise RegistrationConfirmationError(
                            "candidate publication conflicts with a saved candidate"
                        )
                    return
                self._require_lineage(
                    transaction,
                    assessment.context.project_id,
                    int(value["registration_version"]),
                    previous,
                )
                transaction.execute(
                    """INSERT INTO registration_candidate_publications(
                           project_id, activity_id, activity_version,
                           registration_version, candidate_id, repository, branch,
                           remote, destination_snapshot_reference, manifest_path,
                           manifest_sha256, content_hash, assessment_candidate_sha256,
                           operation_id, request_id, expected_parent, state,
                           remote_commit, package_ref_json,
                           previous_registration_ref_json
                       ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                                 'prepared', NULL, NULL, ?)""",
                    (
                        assessment.context.project_id,
                        assessment.context.activity_id,
                        value["activity_version"],
                        value["registration_version"],
                        value["candidate_id"],
                        context.source_repository,
                        context.publication_branch,
                        value["remote"],
                        context.destination_snapshot_reference,
                        value["manifest_path"],
                        value["manifest_sha256"],
                        value["content_hash"],
                        value["assessment_candidate_sha256"],
                        value["operation_id"],
                        value["request_id"],
                        value["expected_parent"],
                        (
                            None
                            if previous is None
                            else canonical_json(previous.as_dict())
                        ),
                    ),
                )
        except sqlite3.IntegrityError:
            row = self._candidate_by_operation(str(value["operation_id"]))
            if row is None or any(
                str(row[index]) != str(expected)
                for index, expected in (
                    (0, assessment.context.project_id),
                    (1, assessment.context.activity_id),
                    (2, value["activity_version"]),
                    (3, value["registration_version"]),
                    (4, value["candidate_id"]),
                    (12, value["operation_id"]),
                    (13, value["request_id"]),
                )
            ):
                raise RegistrationConfirmationError(
                    "candidate publication conflicts with a saved candidate"
                ) from None

    @staticmethod
    def _require_lineage(
        transaction: Transaction,
        project_id: str,
        registration_version: int,
        previous: RegistrationPackageReference | None,
    ) -> None:
        active = transaction.execute(
            "SELECT package_ref_json FROM active_registrations WHERE project_id = ?",
            (project_id,),
        ).fetchone()
        current = (
            None
            if active is None
            else RegistrationPackageReference.from_mapping(json.loads(str(active[0])))
        )
        if current != previous:
            raise RegistrationConfirmationError(
                "candidate previous registration differs from the current active package"
            )
        expected_version = 1 if current is None else current.registration_version + 1
        if registration_version != expected_version:
            raise RegistrationConfirmationError(
                "candidate registration version is not the next active version"
            )

    def _require_current_candidate_lineage(
        self,
        transaction: Transaction,
        project_id: str,
        package_ref: RegistrationPackageReference,
    ) -> None:
        candidate = transaction.execute(
            """SELECT state, package_ref_json, previous_registration_ref_json
               FROM registration_candidate_publications
               WHERE project_id = ? AND registration_version = ? AND candidate_id = ?""",
            (project_id, package_ref.registration_version, package_ref.candidate_id),
        ).fetchone()
        if candidate is None or str(candidate[0]) != "published":
            raise RegistrationConfirmationError("confirmation candidate is no longer published")
        saved = RegistrationPackageReference.from_mapping(json.loads(str(candidate[1])))
        if saved != package_ref:
            raise RegistrationConfirmationError("confirmation candidate changed before activation")
        previous = (
            None
            if candidate[2] is None
            else RegistrationPackageReference.from_mapping(json.loads(str(candidate[2])))
        )
        self._require_lineage(
            transaction, project_id, package_ref.registration_version, previous
        )

    def _eligible_candidate(
        self, assessment: RegistrationAssessment, action: OwnerConfirmation
    ) -> tuple[str, str, str, str]:
        ready = assessment.require_ready_candidate()
        if ready.version != action.package_ref.candidate_id:
            raise RegistrationConfirmationError("confirmation candidate is no longer eligible")
        row = self._candidate_for_reference(action.package_ref, action.project_id)
        if str(row[4]) != assessment.context.activity_id:
            raise RegistrationConfirmationError("published candidate belongs to another activity")
        if int(row[5]) != action.expected_activity_version:
            raise RegistrationConfirmationError("confirmation activity version is stale")
        if str(row[6]) != ready.sha256:
            raise RegistrationConfirmationError("eligible candidate hash changed before confirmation")
        return str(row[0]), str(row[1]), str(row[2]), str(row[3])

    def _candidate_for_reference(
        self, package_ref: RegistrationPackageReference, project_id: str
    ) -> tuple[object, ...]:
        with self.database.read_connection() as connection:
            row = connection.execute(
                """SELECT repository, branch, remote, destination_snapshot_reference,
                          activity_id, activity_version, assessment_candidate_sha256,
                          state, package_ref_json
                   FROM registration_candidate_publications
                   WHERE project_id = ? AND registration_version = ? AND candidate_id = ?""",
                (
                    project_id,
                    package_ref.registration_version,
                    package_ref.candidate_id,
                ),
            ).fetchone()
        if row is None or str(row[7]) != "published":
            raise RegistrationConfirmationError("confirmation candidate is unpublished")
        saved = RegistrationPackageReference.from_mapping(json.loads(str(row[8])))
        if saved != package_ref:
            raise RegistrationConfirmationError("confirmation package reference changed")
        return tuple(row)

    def _candidate_by_operation(self, operation_id: str) -> tuple[object, ...] | None:
        with self.database.read_connection() as connection:
            row = connection.execute(
                """SELECT project_id, activity_id, activity_version,
                          registration_version, candidate_id, repository, branch,
                          remote, destination_snapshot_reference, manifest_path,
                          manifest_sha256, content_hash, operation_id, request_id
                   FROM registration_candidate_publications WHERE operation_id = ?""",
                (operation_id,),
            ).fetchone()
        return None if row is None else tuple(row)

    def _confirmation_by_request(self, request_id: str) -> tuple[object, ...] | None:
        with self.database.read_connection() as connection:
            row = connection.execute(
                """SELECT confirmation_id, request_id, operation_id, project_id,
                          activity_id, expected_activity_version, owner_id, confirmed_at,
                          package_ref_json, previous_confirmation_ref_json,
                          receipt_path, receipt_sha256, receipt_bytes, index_bytes,
                          expected_index_bytes, state, remote_commit, confirmation_ref_json
                   FROM registration_confirmations WHERE request_id = ?""",
                (request_id,),
            ).fetchone()
        return None if row is None else tuple(row)

    def _pending_confirmation(self, project_id: str) -> tuple[object, ...] | None:
        with self.database.read_connection() as connection:
            row = connection.execute(
                """SELECT confirmation_id FROM registration_confirmations
                   WHERE project_id = ? AND state = 'pending'""",
                (project_id,),
            ).fetchone()
        return None if row is None else tuple(row)

    def _active_row(self, project_id: str) -> tuple[object, ...] | None:
        with self.database.read_connection() as connection:
            row = connection.execute(
                """SELECT confirmation_id, package_ref_json, confirmation_ref_json,
                          index_bytes, remote_commit, activity_version
                   FROM active_registrations WHERE project_id = ?""",
                (project_id,),
            ).fetchone()
        return None if row is None else tuple(row)

    def _confirmed_refs(self, project_id: str) -> list[Mapping[str, object]]:
        with self.database.read_connection() as connection:
            rows = connection.execute(
                """SELECT confirmation_ref_json FROM registration_confirmations
                   WHERE project_id = ? AND state = 'confirmed' ORDER BY sequence""",
                (project_id,),
            ).fetchall()
        return [json.loads(str(row[0])) for row in rows]

    @staticmethod
    def _require_same_confirmation(
        row: tuple[object, ...], action: OwnerConfirmation, actor: VerifiedActor
    ) -> None:
        if (
            str(row[0]) != action.confirmation_id
            or str(row[3]) != action.project_id
            or str(row[4]) != action.activity_id
            or int(row[5]) != action.expected_activity_version
            or str(row[6]) != actor.actor_id
            or str(row[7]) != action.confirmed_at
            or RegistrationPackageReference.from_mapping(json.loads(str(row[8])))
            != action.package_ref
        ):
            raise RegistrationConfirmationError(
                "confirmation request identity was reused with changed content"
            )


def _assessment(value: object) -> RegistrationAssessment:
    if not isinstance(value, RegistrationAssessment):
        raise TypeError("registration confirmation requires RegistrationAssessment")
    return value


def _confirmation_ref(value: object) -> ConfirmationReference:
    if not isinstance(value, Mapping) or set(value) != {"confirmation_id", "path", "sha256"}:
        raise RegistrationConfirmationError("confirmation reference is invalid")
    confirmation_id = canonical_identifier(value["confirmation_id"], "confirmation_id")
    path = _text(value["path"], "confirmation path")
    digest = _sha256(value["sha256"], "confirmation sha256")
    return ConfirmationReference(confirmation_id, path, digest)


def _json_bytes(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode("utf-8")


def _text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RegistrationConfirmationError(f"{field} must be nonempty text")
    return value


def _positive(value: object, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise RegistrationConfirmationError(f"{field} must be a positive integer")
    return value


def _sha256(value: object, field: str) -> str:
    text = _text(value, field)
    if len(text) != 64 or any(character not in "0123456789abcdef" for character in text):
        raise RegistrationConfirmationError(f"{field} must be a lowercase SHA-256")
    return text
