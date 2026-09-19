"""Durable, expected-parent publication of exact bytes through service Git."""

from __future__ import annotations

import hashlib
import os
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from .contracts import DomainMigration, canonical_identifier
from .credentials import AuthorizedRepository, RepositoryAuthorizer
from .database import Database
from .git_read import GitReadError, RemoteGitReader, RemoteSnapshot, run_git, validate_object_id, validate_repository_path


class PublicationError(RuntimeError):
    """Base error for an operation that cannot be reported as published."""


class PublicationConflictError(PublicationError):
    """The target paths no longer match this operation's intended bytes."""


class PublicationAccessError(PublicationError):
    """The remote cannot be read or written with the configured service route."""


class PublicationStateError(PublicationError):
    """A publication operation is not in a state that permits that action."""


_MIGRATION = DomainMigration(
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


def publication_migrations() -> tuple[DomainMigration, ...]:
    """Return the publication journal's installed-domain migration definition."""
    return (_MIGRATION,)


@dataclass(frozen=True)
class PublicationOperation:
    operation_id: str
    authorization: AuthorizedRepository
    remote: str
    expected_parent: str
    files: dict[str, bytes]
    state: str
    remote_commit: str | None
    failure: str | None


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

    def __init__(self, database: Database, authorizer: RepositoryAuthorizer) -> None:
        if not isinstance(database, Database):
            raise TypeError("PublicationJournal requires the service Database")
        if not isinstance(authorizer, RepositoryAuthorizer):
            raise TypeError("PublicationJournal requires RepositoryAuthorizer")
        self._database = database
        self._authorizer = authorizer
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
    ) -> PublicationOperation:
        """Persist the exact authorized target and bytes before any network write."""
        canonical_identifier(operation_id, "operation_id")
        authorization = self._authorizer.authorize(repository, branch)
        expected_parent = validate_object_id(expected_parent, "expected_parent")
        if not isinstance(remote, str) or not remote or "\x00" in remote:
            raise PublicationError("remote must be nonempty text")
        normalized_files = self._normalize_files(files)
        with self._database.transaction() as transaction:
            transaction.execute(
                """
                INSERT INTO publication_operations(
                    operation_id, binding_id, repository, profile_name, credential_reference,
                    remote, branch, expected_parent, state, remote_commit, failure
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'prepared', NULL, NULL)
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
                ),
            )
            for path, content in normalized_files.items():
                transaction.execute(
                    """INSERT INTO publication_files(operation_id, path, content, sha256)
                       VALUES (?, ?, ?, ?)""",
                    (operation_id, path, content, hashlib.sha256(content).hexdigest()),
                )
        return self.operation(operation_id)

    def attempt(self, operation_id: str) -> PublicationResult:
        """Publish once, never force-pushing, then verify remote bytes before success."""
        operation = self.operation(operation_id)
        if operation.state == "verified":
            assert operation.remote_commit is not None
            return PublicationResult(operation_id, operation.remote_commit, "verified", True)
        if operation.state not in {"prepared", "writing", "paused"}:
            raise PublicationStateError("publication operation is not retryable")
        self._set_state(operation_id, "writing", failure=None)
        return self._attempt_or_reconcile(operation_id, allow_write=True)

    def observe(self, operation_id: str) -> RemoteSnapshot:
        """Read the current target state without a write or state transition."""
        operation = self.operation(operation_id)
        try:
            return self._reader.snapshot(operation.remote, operation.authorization.branch, tuple(operation.files))
        except GitReadError as error:
            raise PublicationAccessError("cannot observe the configured publication target") from error

    def reconcile(self, operation_id: str) -> PublicationResult:
        """Resolve an uncertain write from remote facts before any retry."""
        operation = self.operation(operation_id)
        if operation.state == "verified":
            assert operation.remote_commit is not None
            return PublicationResult(operation_id, operation.remote_commit, "verified", True)
        if operation.state not in {"writing", "paused", "prepared"}:
            raise PublicationStateError("publication operation cannot be reconciled")
        return self._attempt_or_reconcile(operation_id, allow_write=False)

    def operation(self, operation_id: str) -> PublicationOperation:
        canonical_identifier(operation_id, "operation_id")
        with self._database.read_connection() as connection:
            row = connection.execute(
                """SELECT operation_id, binding_id, repository, profile_name,
                          credential_reference, remote, branch, expected_parent,
                          state, remote_commit, failure
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
        return PublicationOperation(
            operation_id=str(row[0]), authorization=authorization, remote=str(row[5]),
            expected_parent=str(row[7]), files=files, state=str(row[8]),
            remote_commit=None if row[9] is None else str(row[9]),
            failure=None if row[10] is None else str(row[10]),
        )

    def _attempt_or_reconcile(self, operation_id: str, *, allow_write: bool) -> PublicationResult:
        operation = self.operation(operation_id)
        try:
            snapshot = self.observe(operation_id)
        except PublicationAccessError as error:
            self._set_state(operation_id, "paused", failure=str(error))
            raise
        matches = all(snapshot.files[path] == content for path, content in operation.files.items())
        missing = all(snapshot.files[path] is None for path in operation.files)
        if matches:
            self._set_verified(operation_id, snapshot.head)
            return PublicationResult(operation_id, snapshot.head, "verified", True)
        if not allow_write:
            message = "remote target does not contain the intended bytes"
            self._set_state(operation_id, "paused", failure=message)
            raise PublicationConflictError(message)
        if not missing:
            message = "remote target contains conflicting publication bytes"
            self._set_state(operation_id, "paused", failure=message)
            raise PublicationConflictError(message)
        try:
            commit = self._write_once(operation, snapshot.head)
        except PublicationAccessError as error:
            self._set_state(operation_id, "paused", failure=str(error))
            raise
        except PublicationConflictError as error:
            self._set_state(operation_id, "paused", failure=str(error))
            raise
        observed = self.observe(operation_id)
        if observed.head != commit or not all(
            observed.files[path] == content for path, content in operation.files.items()
        ):
            message = "remote write outcome is not the exact intended commit and bytes"
            self._set_state(operation_id, "paused", failure=message)
            raise PublicationConflictError(message)
        self._set_verified(operation_id, commit)
        return PublicationResult(operation_id, commit, "verified", False)

    def _write_once(self, operation: PublicationOperation, parent: str) -> str:
        directory = Path(tempfile.mkdtemp(prefix="maestro-git-publication-"))
        try:
            self._checked("init", "--quiet", str(directory))
            self._checked("-C", str(directory), "remote", "add", "origin", operation.remote)
            self._checked("-C", str(directory), "fetch", "--no-tags", "--quiet", "origin", parent)
            self._checked("-C", str(directory), "checkout", "--quiet", "--detach", "FETCH_HEAD")
            for path, content in operation.files.items():
                destination = directory / path
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(content)
            self._checked("-C", str(directory), "add", "--", *operation.files)
            message = f"Maestro publication {operation.operation_id}"
            self._checked(
                "-C", str(directory), "-c", "user.name=Maestro service",
                "-c", "user.email=maestro@localhost", "commit", "--quiet", "-m", message,
            )
            commit = self._checked("-C", str(directory), "rev-parse", "HEAD").stdout.decode("ascii").strip()
            commit = validate_object_id(commit, "published commit")
            pushed = run_git(
                "-C", str(directory), "push", "--porcelain", "origin",
                f"{commit}:refs/heads/{operation.authorization.branch}",
            )
            if pushed.returncode != 0:
                detail = pushed.stderr.decode("utf-8", "replace").strip()
                raise PublicationConflictError(
                    f"remote branch changed before non-force publication: {detail or 'rejected'}"
                )
            return commit
        except GitReadError as error:
            raise PublicationAccessError("configured Git route rejected publication") from error
        except OSError as error:
            raise PublicationAccessError("cannot prepare bounded local publication worktree") from error
        finally:
            shutil.rmtree(directory, ignore_errors=True)

    @staticmethod
    def _checked(*arguments: str):
        result = run_git(*arguments)
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

    def _set_verified(self, operation_id: str, commit: str) -> None:
        with self._database.transaction() as transaction:
            transaction.execute(
                """UPDATE publication_operations
                   SET state = 'verified', remote_commit = ?, failure = NULL
                   WHERE operation_id = ?""",
                (commit, operation_id),
            )
