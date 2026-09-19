"""Durable, expected-parent publication of exact bytes through service Git."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from .contracts import DomainMigration, canonical_identifier
from .credentials import (
    AuthorizedRepository,
    RepositoryAuthorizer,
    RepositoryCredentialError,
    ServiceGitTransport,
)
from .database import Database
from .github_destination import (
    GitHubDestinationAuthorization,
    GitHubDestinationAuthorizationError,
    GitHubDestinationProvider,
)
from .git_read import GitReadError, RemoteGitReader, RemoteSnapshot, run_git, validate_object_id, validate_repository_path


class PublicationError(RuntimeError):
    """Base error for an operation that cannot be reported as published."""


class PublicationConflictError(PublicationError):
    """The target paths no longer match this operation's intended bytes."""


class PublicationAccessError(PublicationError):
    """The remote cannot be read or written with the configured service route."""


class PublicationStateError(PublicationError):
    """A publication operation is not in a state that permits that action."""


_MIGRATION_V1 = DomainMigration(
    domain="publication",
    version=1,
    identity="publication-journal-v1",
    statements=(
        """
        CREATE TABLE publication_operations (
            operation_id TEXT PRIMARY KEY,
            binding_id TEXT NOT NULL,
            repository TEXT NOT NULL,
            profile_name TEXT NOT NULL,
            credential_reference TEXT NOT NULL,
            remote TEXT NOT NULL,
            branch TEXT NOT NULL,
            expected_parent TEXT NOT NULL,
            state TEXT NOT NULL,
            reconciled_parent TEXT,
            remote_commit TEXT,
            failure TEXT
        )
        """,
        """
        CREATE TABLE publication_files (
            operation_id TEXT NOT NULL REFERENCES publication_operations(operation_id),
            path TEXT NOT NULL,
            content BLOB NOT NULL,
            sha256 TEXT NOT NULL,
            PRIMARY KEY(operation_id, path)
        )
        """,
    ),
)

_MIGRATION_V2 = DomainMigration(
    domain="publication",
    version=2,
    identity="publication-journal-v2",
    statements=(
        "ALTER TABLE publication_operations ADD COLUMN authorization_snapshot TEXT",
    ),
)


def publication_migrations() -> tuple[DomainMigration, ...]:
    """Return the publication journal's installed-domain migration definition."""
    return (_MIGRATION_V1, _MIGRATION_V2)


@dataclass(frozen=True)
class PublicationOperation:
    operation_id: str
    authorization: AuthorizedRepository
    remote: str
    expected_parent: str
    files: dict[str, bytes]
    state: str
    reconciled_parent: str | None
    remote_commit: str | None
    failure: str | None
    authorization_snapshot: dict[str, object]


@dataclass(frozen=True)
class PublicationResult:
    operation_id: str
    remote_commit: str
    state: str
    reused_remote_bytes: bool


class PublicationJournal:
    """Prepare, attempt, observe, and reconcile an exact repository write.

    The caller supplies a :class:`Database` created with
    :func:`publication_migrations`; this class never creates an alternate
    SQLite writer.  Credential values are resolved by the service's Git
    transport.  The journal stores only the validated profile reference.
    """

    def __init__(
        self,
        database: Database,
        authorizer: RepositoryAuthorizer,
        transport: ServiceGitTransport,
        destination_provider: GitHubDestinationProvider,
    ) -> None:
        if not isinstance(database, Database):
            raise TypeError("PublicationJournal requires the service Database")
        if not isinstance(authorizer, RepositoryAuthorizer):
            raise TypeError("PublicationJournal requires RepositoryAuthorizer")
        if not isinstance(transport, ServiceGitTransport):
            raise TypeError("PublicationJournal requires ServiceGitTransport")
        if not isinstance(destination_provider, GitHubDestinationProvider):
            raise TypeError("PublicationJournal requires GitHubDestinationProvider")
        self._database = database
        self._authorizer = authorizer
        self._transport = transport
        self._destination_provider = destination_provider
        self._reader = RemoteGitReader()

    def prepare(
        self,
        *,
        operation_id: str,
        repository: str,
        remote: str,
        branch: str,
        expected_parent: str,
        files: Mapping[str, bytes],
        destination_authorization: GitHubDestinationAuthorization,
    ) -> PublicationOperation:
        """Persist the exact authorized target and bytes before any network write."""
        canonical_identifier(operation_id, "operation_id")
        authorization = self._authorizer.authorize(repository, branch)
        self._require_destination(destination_authorization, authorization)
        expected_parent = validate_object_id(expected_parent, "expected_parent")
        try:
            configured_remote = self._transport.remote_for(authorization)
        except RepositoryCredentialError as error:
            raise PublicationAccessError("configured privileged Git route is unavailable") from error
        if remote != configured_remote:
            raise PublicationAccessError("publication remote does not match its authorized profile")
        normalized_files = self._normalize_files(files)
        with self._database.transaction() as transaction:
            transaction.execute(
                """
                INSERT INTO publication_operations(
                    operation_id, binding_id, repository, profile_name, credential_reference,
                    remote, branch, expected_parent, state, reconciled_parent, remote_commit, failure,
                    authorization_snapshot
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'prepared', NULL, NULL, NULL, ?)
                """,
                (
                    operation_id,
                    authorization.binding_id,
                    authorization.repository,
                    authorization.profile_name,
                    authorization.credential_reference,
                    remote,
                    authorization.branch,
                    expected_parent,
                    self._snapshot_json(destination_authorization),
                ),
            )
            for path, content in normalized_files.items():
                transaction.execute(
                    """INSERT INTO publication_files(operation_id, path, content, sha256)
                       VALUES (?, ?, ?, ?)""",
                    (operation_id, path, content, hashlib.sha256(content).hexdigest()),
                )
        return self.operation(operation_id)

    def attempt(
        self, operation_id: str, destination_authorization: GitHubDestinationAuthorization
    ) -> PublicationResult:
        """Publish once, never force-pushing, then verify remote bytes before success."""
        operation = self.operation(operation_id)
        current = self._fresh_destination(operation, destination_authorization)
        if operation.state == "verified":
            assert operation.remote_commit is not None
            return PublicationResult(operation_id, operation.remote_commit, "verified", True)
        if operation.state not in {"prepared", "reconciled"}:
            raise PublicationStateError("publication operation is not retryable")
        return self._attempt(operation_id, current)

    def observe(
        self, operation_id: str, destination_authorization: GitHubDestinationAuthorization
    ) -> RemoteSnapshot:
        """Read the current target state without a write or state transition."""
        operation = self.operation(operation_id)
        self._require_destination(destination_authorization, operation.authorization)
        try:
            with self._destination_provider.bind_transport(
                destination_authorization, self._transport, operation.authorization
            ) as transport:
                return self._reader.snapshot(
                    transport.remote,
                    operation.authorization.branch,
                    tuple(operation.files),
                    command=lambda *args: run_git(*args, environment=transport.environment()),
                )
        except (GitReadError, RepositoryCredentialError) as error:
            raise PublicationAccessError("cannot observe the configured publication target") from error

    def reconcile(
        self, operation_id: str, destination_authorization: GitHubDestinationAuthorization
    ) -> PublicationResult:
        """Resolve an uncertain write from remote facts before any retry."""
        operation = self.operation(operation_id)
        current = self._fresh_destination(operation, destination_authorization)
        if operation.state == "verified":
            assert operation.remote_commit is not None
            return PublicationResult(operation_id, operation.remote_commit, "verified", True)
        if operation.state not in {"writing", "paused", "prepared", "reconciled"}:
            raise PublicationStateError("publication operation cannot be reconciled")
        snapshot = self._observe_or_pause(operation_id, current)
        matches, missing = self._target_state(operation, snapshot)
        if matches:
            self._set_verified(operation_id, snapshot.head)
            return PublicationResult(operation_id, snapshot.head, "verified", True)
        if not missing:
            self._pause(operation_id, "remote target contains conflicting publication bytes")
            raise PublicationConflictError("remote target contains conflicting publication bytes")
        self._set_reconciled(operation_id, snapshot.head)
        raise PublicationStateError("remote state is reconciled; retry publication explicitly")

    def operation(self, operation_id: str) -> PublicationOperation:
        canonical_identifier(operation_id, "operation_id")
        with self._database.read_connection() as connection:
            row = connection.execute(
                """SELECT operation_id, binding_id, repository, profile_name,
                          credential_reference, remote, branch, expected_parent,
                          state, reconciled_parent, remote_commit, failure, authorization_snapshot
                   FROM publication_operations WHERE operation_id = ?""",
                (operation_id,),
            ).fetchone()
            if row is None:
                raise PublicationStateError("publication operation does not exist")
            file_rows = connection.execute(
                "SELECT path, content, sha256 FROM publication_files WHERE operation_id = ? ORDER BY path",
                (operation_id,),
            ).fetchall()
        files: dict[str, bytes] = {}
        for path, content, digest in file_rows:
            raw = bytes(content)
            if hashlib.sha256(raw).hexdigest() != digest:
                raise PublicationStateError("saved publication bytes fail their stored hash")
            files[str(path)] = raw
        authorization = AuthorizedRepository(
            binding_id=str(row[1]),
            repository=str(row[2]),
            branch=str(row[6]),
            profile_name=str(row[3]),
            credential_reference=str(row[4]),
        )
        try:
            snapshot = json.loads(str(row[12]))
        except (TypeError, ValueError, json.JSONDecodeError) as error:
            raise PublicationStateError("saved GitHub destination snapshot is invalid") from error
        if not isinstance(snapshot, dict):
            raise PublicationStateError("saved GitHub destination snapshot is invalid")
        return PublicationOperation(
            operation_id=str(row[0]), authorization=authorization, remote=str(row[5]),
            expected_parent=str(row[7]), files=files, state=str(row[8]),
            reconciled_parent=None if row[9] is None else str(row[9]),
            remote_commit=None if row[10] is None else str(row[10]),
            failure=None if row[11] is None else str(row[11]),
            authorization_snapshot=snapshot,
        )

    def _attempt(
        self, operation_id: str, destination_authorization: GitHubDestinationAuthorization
    ) -> PublicationResult:
        operation = self.operation(operation_id)
        snapshot = self._observe_or_pause(operation_id, destination_authorization)
        matches, missing = self._target_state(operation, snapshot)
        if matches:
            self._set_verified(operation_id, snapshot.head)
            return PublicationResult(operation_id, snapshot.head, "verified", True)
        if not missing:
            self._pause(operation_id, "remote target contains conflicting publication bytes")
            raise PublicationConflictError("remote target contains conflicting publication bytes")
        permitted_parent = operation.expected_parent if operation.state == "prepared" else operation.reconciled_parent
        if snapshot.head != permitted_parent:
            self._set_reconciled(operation_id, snapshot.head)
            raise PublicationStateError("remote branch moved; reconciliation completed before retry")
        self._set_state(operation_id, "writing", failure=None)
        try:
            # Obtain a new live authorization/policy observation at the last
            # possible point before the irreversible push.
            current = self._fresh_destination(operation, destination_authorization)
            commit = self._write_once(operation, snapshot.head, current)
        except PublicationAccessError as error:
            self._set_state(operation_id, "paused", failure=str(error))
            raise
        except PublicationConflictError as error:
            self._set_state(operation_id, "paused", failure=str(error))
            raise
        observed = self._observe_or_pause(operation_id, destination_authorization)
        if observed.head != commit or not all(
            observed.files[path] == content for path, content in operation.files.items()
        ):
            message = "remote write outcome is not the exact intended commit and bytes"
            self._pause(operation_id, message)
            raise PublicationConflictError(message)
        self._set_verified(operation_id, commit)
        return PublicationResult(operation_id, commit, "verified", False)

    def _write_once(
        self, operation: PublicationOperation, parent: str,
        destination_authorization: GitHubDestinationAuthorization,
    ) -> str:
        directory = Path(tempfile.mkdtemp(prefix="maestro-git-publication-"))
        try:
            with self._destination_provider.bind_transport(
                destination_authorization, self._transport, operation.authorization
            ) as transport:
                command = lambda *args: run_git(*args, environment=transport.environment())
                self._checked(command, "init", "--quiet", str(directory))
                self._checked(command, "-C", str(directory), "remote", "add", "origin", transport.remote)
                self._checked(command, "-C", str(directory), "fetch", "--no-tags", "--quiet", "origin", parent)
                self._checked(command, "-C", str(directory), "checkout", "--quiet", "--detach", "FETCH_HEAD")
                for path, content in operation.files.items():
                    destination = directory / path
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    destination.write_bytes(content)
                self._checked(command, "-C", str(directory), "add", "--", *operation.files)
                message = f"Maestro publication {operation.operation_id}"
                self._checked(
                    command,
                    "-C", str(directory), "-c", "user.name=Maestro service",
                    "-c", "user.email=maestro@localhost", "commit", "--quiet", "-m", message,
                )
                commit = self._checked(command, "-C", str(directory), "rev-parse", "HEAD").stdout.decode("ascii").strip()
                commit = validate_object_id(commit, "published commit")
                pushed = command(
                    "-C", str(directory), "push", "--porcelain", "origin",
                    f"{commit}:refs/heads/{operation.authorization.branch}",
                )
                if pushed.returncode != 0:
                    detail = pushed.stderr.decode("utf-8", "replace").strip()
                    raise PublicationConflictError(
                        f"remote branch changed before non-force publication: {detail or 'rejected'}"
                    )
                return commit
        except (GitReadError, RepositoryCredentialError) as error:
            raise PublicationAccessError("configured Git route rejected publication") from error
        except OSError as error:
            raise PublicationAccessError("cannot prepare bounded local publication worktree") from error
        finally:
            shutil.rmtree(directory, ignore_errors=True)

    @staticmethod
    def _checked(command, *arguments: str):
        result = command(*arguments)
        if result.returncode != 0:
            detail = result.stderr.decode("utf-8", "replace").strip()
            raise PublicationAccessError(f"Git operation failed: {detail or 'unavailable'}")
        return result

    @staticmethod
    def _normalize_files(files: Mapping[str, bytes]) -> dict[str, bytes]:
        if not isinstance(files, Mapping) or not files:
            raise PublicationError("publication requires a nonempty mapping of exact files")
        normalized: dict[str, bytes] = {}
        for path, content in files.items():
            path = validate_repository_path(path)
            if not isinstance(content, bytes):
                raise PublicationError("publication content must be exact bytes")
            if path in normalized:
                raise PublicationError("publication paths must be unique")
            normalized[path] = content
        return dict(sorted(normalized.items()))

    def _set_state(self, operation_id: str, state: str, *, failure: str | None) -> None:
        with self._database.transaction() as transaction:
            transaction.execute(
                "UPDATE publication_operations SET state = ?, failure = ? WHERE operation_id = ?",
                (state, failure, operation_id),
            )

    def _set_reconciled(self, operation_id: str, parent: str) -> None:
        with self._database.transaction() as transaction:
            transaction.execute(
                """UPDATE publication_operations
                   SET state = 'reconciled', reconciled_parent = ?, failure = NULL
                   WHERE operation_id = ?""",
                (parent, operation_id),
            )

    def _pause(self, operation_id: str, failure: str) -> None:
        self._set_state(operation_id, "paused", failure=failure)

    def _observe_or_pause(
        self, operation_id: str, destination_authorization: GitHubDestinationAuthorization
    ) -> RemoteSnapshot:
        try:
            return self.observe(operation_id, destination_authorization)
        except (PublicationAccessError, GitHubDestinationAuthorizationError) as error:
            self._pause(operation_id, str(error))
            raise

    @staticmethod
    def _target_state(operation: PublicationOperation, snapshot: RemoteSnapshot) -> tuple[bool, bool]:
        return (
            all(snapshot.files[path] == content for path, content in operation.files.items()),
            all(snapshot.files[path] is None for path in operation.files),
        )

    def _set_verified(self, operation_id: str, commit: str) -> None:
        with self._database.transaction() as transaction:
            transaction.execute(
                """UPDATE publication_operations
                   SET state = 'verified', remote_commit = ?, failure = NULL
                   WHERE operation_id = ?""",
                (commit, operation_id),
            )

    def _require_destination(
        self, destination_authorization: GitHubDestinationAuthorization,
        authorization: AuthorizedRepository,
    ) -> None:
        try:
            self._destination_provider.require_fresh_match(destination_authorization, authorization)
        except GitHubDestinationAuthorizationError as error:
            raise PublicationAccessError("GitHub destination authorization is unavailable") from error

    def _fresh_destination(
        self,
        operation: PublicationOperation,
        supplied: GitHubDestinationAuthorization,
    ) -> GitHubDestinationAuthorization:
        """Require supplied evidence and a new matching provider observation.

        The saved profile snapshot is immutable: recovery must never adopt a
        changed App, installation, allowlist, API base, or credential profile.
        A failed live recheck pauses the operation before any remote write.
        """
        try:
            self._require_destination(supplied, operation.authorization)
            fresh = self._destination_provider.authorize(
                operation.authorization.repository, operation.authorization.branch
            )
            self._require_destination(fresh, operation.authorization)
            saved = operation.authorization_snapshot.get("snapshot")
            if not isinstance(saved, dict) or saved != dict(fresh.snapshot):
                raise PublicationAccessError(
                    "GitHub destination profile changed since publication preparation"
                )
            return fresh
        except PublicationAccessError as error:
            self._pause(operation.operation_id, str(error))
            raise

    @staticmethod
    def _snapshot_json(destination_authorization: GitHubDestinationAuthorization) -> str:
        return json.dumps(
            destination_authorization.durable_record(), sort_keys=True,
            separators=(",", ":"), ensure_ascii=False, allow_nan=False,
        )
