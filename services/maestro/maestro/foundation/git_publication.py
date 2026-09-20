"""Durable, expected-parent publication of exact bytes through service Git."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
import stat
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
from .database import Database, Transaction
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

_MIGRATION_V3 = DomainMigration(
    domain="publication",
    version=3,
    identity="publication-journal-compare-and-replace-v1",
    statements=(
        "ALTER TABLE publication_operations ADD COLUMN operation_type TEXT",
        "ALTER TABLE publication_operations ADD COLUMN request_id TEXT",
        "UPDATE publication_operations SET operation_type = 'legacy_publication', request_id = operation_id",
        "CREATE UNIQUE INDEX publication_request_identity ON publication_operations(request_id)",
        "ALTER TABLE publication_files ADD COLUMN expected_content BLOB",
        "ALTER TABLE publication_files ADD COLUMN expected_sha256 TEXT",
        "ALTER TABLE publication_files ADD COLUMN expected_exists INTEGER NOT NULL DEFAULT 0 CHECK(expected_exists IN (0, 1))",
    ),
)


def publication_migrations() -> tuple[DomainMigration, ...]:
    """Return the publication journal's installed-domain migration definition."""
    return (_MIGRATION_V1, _MIGRATION_V2, _MIGRATION_V3)


@dataclass(frozen=True)
class PublicationOperation:
    operation_id: str
    operation_type: str
    request_id: str
    authorization: AuthorizedRepository
    remote: str
    expected_parent: str
    files: dict[str, bytes]
    expected_files: dict[str, bytes | None]
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
        operation_type: str = "generic_publication",
        request_id: str | None = None,
        repository: str,
        remote: str,
        branch: str,
        expected_parent: str,
        files: Mapping[str, bytes],
        expected_files: Mapping[str, bytes | None] | None = None,
        destination_authorization: GitHubDestinationAuthorization,
    ) -> PublicationOperation:
        """Persist exact intended and prior target bytes before any network write.

        Existing callers that only create immutable paths may omit
        ``expected_files``; every target is then expected to be absent.  A
        compare-and-replace caller supplies the same target set with either
        the exact prior bytes or ``None`` for an absent path.
        """
        canonical_identifier(operation_id, "operation_id")
        canonical_identifier(operation_type, "operation_type")
        request_id = operation_id if request_id is None else request_id
        canonical_identifier(request_id, "request_id")
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
        normalized_expected = self._normalize_expected_files(
            expected_files, tuple(normalized_files)
        )
        try:
            with self._database.transaction() as transaction:
                transaction.execute(
                    """
                    INSERT INTO publication_operations(
                        operation_id, binding_id, repository, profile_name, credential_reference,
                        remote, branch, expected_parent, state, reconciled_parent, remote_commit, failure,
                        authorization_snapshot, operation_type, request_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'prepared', NULL, NULL, NULL, ?, ?, ?)
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
                        operation_type,
                        request_id,
                    ),
                )
                for path, content in normalized_files.items():
                    expected = normalized_expected[path]
                    transaction.execute(
                        """INSERT INTO publication_files(
                               operation_id, path, content, sha256,
                               expected_content, expected_sha256, expected_exists
                           ) VALUES (?, ?, ?, ?, ?, ?, ?)""",
                        (
                            operation_id,
                            path,
                            content,
                            hashlib.sha256(content).hexdigest(),
                            expected,
                            None if expected is None else hashlib.sha256(expected).hexdigest(),
                            0 if expected is None else 1,
                        ),
                    )
        except sqlite3.IntegrityError as error:
            raise PublicationStateError(
                "publication operation or request identity already exists"
            ) from error
        return self.operation(operation_id)

    def attempt(
        self, operation_id: str, destination_authorization: GitHubDestinationAuthorization
    ) -> PublicationResult:
        """Publish once, never force-pushing, then verify remote bytes before success."""
        operation = self.operation(operation_id)
        if operation.state in {"verified", "applied"}:
            assert operation.remote_commit is not None
            return PublicationResult(
                operation_id, operation.remote_commit, operation.state, True
            )
        current = self._fresh_destination(operation, destination_authorization)
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
                command = lambda *args: run_git(
                    *args, environment=transport.environment()
                )
                snapshot = self._reader.snapshot(
                    transport.remote,
                    operation.authorization.branch,
                    tuple(operation.files),
                    command=command,
                )
                self._require_regular_remote_targets(
                    transport.remote, snapshot, tuple(operation.files), command
                )
                return snapshot
        except (GitReadError, RepositoryCredentialError) as error:
            raise PublicationAccessError("cannot observe the configured publication target") from error

    def reconcile(
        self, operation_id: str, destination_authorization: GitHubDestinationAuthorization
    ) -> PublicationResult:
        """Resolve an uncertain write from remote facts before any retry."""
        operation = self.operation(operation_id)
        if operation.state in {"verified", "applied"}:
            assert operation.remote_commit is not None
            return PublicationResult(
                operation_id, operation.remote_commit, operation.state, True
            )
        if operation.state not in {"writing", "paused", "prepared", "reconciled"}:
            raise PublicationStateError("publication operation cannot be reconciled")
        current = self._fresh_destination(operation, destination_authorization)
        snapshot = self._observe_or_pause(operation_id, current)
        matches, expected = self._target_state(operation, snapshot)
        if matches:
            self._set_verified(operation_id, snapshot.head)
            return PublicationResult(operation_id, snapshot.head, "verified", True)
        if not expected:
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
                          state, reconciled_parent, remote_commit, failure, authorization_snapshot,
                          operation_type, request_id
                   FROM publication_operations WHERE operation_id = ?""",
                (operation_id,),
            ).fetchone()
            if row is None:
                raise PublicationStateError("publication operation does not exist")
            file_rows = connection.execute(
                """SELECT path, content, sha256, expected_content,
                          expected_sha256, expected_exists
                   FROM publication_files WHERE operation_id = ? ORDER BY path""",
                (operation_id,),
            ).fetchall()
        files: dict[str, bytes] = {}
        expected_files: dict[str, bytes | None] = {}
        for path, content, digest, expected_content, expected_digest, expected_exists in file_rows:
            raw = bytes(content)
            if hashlib.sha256(raw).hexdigest() != digest:
                raise PublicationStateError("saved publication bytes fail their stored hash")
            normalized_path = str(path)
            files[normalized_path] = raw
            if int(expected_exists) == 0:
                if expected_content is not None or expected_digest is not None:
                    raise PublicationStateError("saved absent prior publication bytes are invalid")
                expected_files[normalized_path] = None
            elif int(expected_exists) == 1:
                if expected_content is None:
                    raise PublicationStateError("saved prior publication bytes are missing")
                expected_raw = bytes(expected_content)
                if hashlib.sha256(expected_raw).hexdigest() != expected_digest:
                    raise PublicationStateError("saved prior publication bytes fail their stored hash")
                expected_files[normalized_path] = expected_raw
            else:
                raise PublicationStateError("saved prior publication state is invalid")
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
            operation_id=str(row[0]), operation_type=str(row[13]), request_id=str(row[14]),
            authorization=authorization, remote=str(row[5]),
            expected_parent=str(row[7]), files=files, state=str(row[8]),
            expected_files=expected_files,
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
        matches, expected = self._target_state(operation, snapshot)
        if matches:
            self._set_verified(operation_id, snapshot.head)
            return PublicationResult(operation_id, snapshot.head, "verified", True)
        if not expected:
            self._pause(operation_id, "remote target contains conflicting publication bytes")
            raise PublicationConflictError("remote target contains conflicting publication bytes")
        permitted_parent = operation.expected_parent if operation.state == "prepared" else operation.reconciled_parent
        if snapshot.head != permitted_parent:
            self._set_reconciled(operation_id, snapshot.head)
            raise PublicationStateError("remote branch moved; reconciliation completed before retry")
        self._set_state(operation_id, "writing", failure=None)
        try:
            commit = self._write_once(operation, snapshot.head, destination_authorization)
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
                self._require_regular_local_targets(directory, tuple(operation.files))
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

            # The branch policy can change while this bounded local commit is
            # being prepared.  Re-authorize only after all local work and
            # immediately before the irreversible network push.
            current = self._fresh_destination(operation, destination_authorization)
            with self._destination_provider.bind_transport(
                current, self._transport, operation.authorization
            ) as push_transport:
                push_command = lambda *args: run_git(*args, environment=push_transport.environment())
                pushed = push_command(
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

    @staticmethod
    def _normalize_expected_files(
        expected_files: Mapping[str, bytes | None] | None,
        target_paths: tuple[str, ...],
    ) -> dict[str, bytes | None]:
        if expected_files is None:
            return {path: None for path in target_paths}
        if not isinstance(expected_files, Mapping):
            raise PublicationError("expected publication files must be a mapping")
        normalized: dict[str, bytes | None] = {}
        for path, content in expected_files.items():
            path = validate_repository_path(path)
            if content is not None and not isinstance(content, bytes):
                raise PublicationError("expected publication content must be exact bytes or absent")
            if path in normalized:
                raise PublicationError("expected publication paths must be unique")
            normalized[path] = content
        if set(normalized) != set(target_paths):
            raise PublicationError(
                "expected publication paths must exactly match intended publication paths"
            )
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
        except (
            PublicationAccessError,
            PublicationConflictError,
            GitHubDestinationAuthorizationError,
        ) as error:
            self._pause(operation_id, str(error))
            raise

    @classmethod
    def _require_regular_remote_targets(
        cls,
        remote: str,
        snapshot: RemoteSnapshot,
        paths: tuple[str, ...],
        command,
    ) -> None:
        """Reject symlinks, submodules, and path-shape conflicts before a write."""
        with tempfile.TemporaryDirectory(prefix="maestro-git-entry-check-") as temporary:
            cls._checked(command, "init", "--bare", "--quiet", temporary)
            cls._checked(
                command,
                "-C", temporary,
                "fetch", "--no-tags", "--quiet", remote, snapshot.head,
            )
            for path in paths:
                parts = path.split("/")
                for end in range(1, len(parts)):
                    prefix = "/".join(parts[:end])
                    entry = cls._tree_entry(command, temporary, snapshot.head, prefix)
                    if entry is None:
                        break
                    if entry != ("040000", "tree"):
                        raise PublicationConflictError(
                            f"remote publication target parent is not a directory: {prefix}"
                        )
                entry = cls._tree_entry(command, temporary, snapshot.head, path)
                if entry is not None and entry not in {
                    ("100644", "blob"),
                    ("100755", "blob"),
                }:
                    raise PublicationConflictError(
                        f"remote publication target is not a regular file: {path}"
                    )

    @classmethod
    def _tree_entry(
        cls, command, repository: str, commit: str, path: str
    ) -> tuple[str, str] | None:
        result = cls._checked(
            command,
            "-C", repository,
            "ls-tree", "-z", "--full-tree", commit, "--", path,
        )
        entries = tuple(item for item in result.stdout.split(b"\0") if item)
        if not entries:
            return None
        if len(entries) != 1:
            raise PublicationConflictError(
                f"remote publication target has an ambiguous tree entry: {path}"
            )
        try:
            metadata, returned_path = entries[0].split(b"\t", 1)
            mode, entry_type, _object_id = metadata.decode("ascii").split(" ", 2)
        except (UnicodeDecodeError, ValueError) as error:
            raise PublicationConflictError(
                f"remote publication target has an invalid tree entry: {path}"
            ) from error
        if returned_path != path.encode("utf-8"):
            raise PublicationConflictError(
                f"remote publication target resolved to another path: {path}"
            )
        return mode, entry_type

    @staticmethod
    def _require_regular_local_targets(root: Path, paths: tuple[str, ...]) -> None:
        """Preflight every checked-out target before materializing any bytes."""
        for path in paths:
            destination = root / path
            current = root
            for part in destination.relative_to(root).parts[:-1]:
                current /= part
                try:
                    metadata = os.lstat(current)
                except FileNotFoundError:
                    break
                if not stat.S_ISDIR(metadata.st_mode):
                    raise PublicationConflictError(
                        f"local publication target parent is not a directory: {path}"
                    )
            try:
                metadata = os.lstat(destination)
            except FileNotFoundError:
                continue
            if not stat.S_ISREG(metadata.st_mode):
                raise PublicationConflictError(
                    f"local publication target is not a regular file: {path}"
                )

    @staticmethod
    def _target_state(operation: PublicationOperation, snapshot: RemoteSnapshot) -> tuple[bool, bool]:
        return (
            all(snapshot.files[path] == content for path, content in operation.files.items()),
            all(
                snapshot.files[path] == expected
                for path, expected in operation.expected_files.items()
            ),
        )

    def mark_applied(
        self,
        transaction: Transaction,
        *,
        operation_id: str,
        request_id: str,
    ) -> PublicationResult:
        """Record domain activation in its caller-owned SQL transaction.

        Remote verification remains a separate prerequisite.  Replaying the
        same request after an interrupted activation is idempotent; another
        request or an unverified operation cannot claim application.
        """
        if not isinstance(transaction, Transaction):
            raise TypeError("publication application requires the service transaction")
        canonical_identifier(operation_id, "operation_id")
        canonical_identifier(request_id, "request_id")
        row = transaction.execute(
            """SELECT request_id, state, remote_commit
               FROM publication_operations WHERE operation_id = ?""",
            (operation_id,),
        ).fetchone()
        if row is None:
            raise PublicationStateError("publication operation does not exist")
        if str(row[0]) != request_id:
            raise PublicationStateError("publication request identity does not match")
        state = str(row[1])
        remote_commit = None if row[2] is None else str(row[2])
        if state == "verified":
            if remote_commit is None:
                raise PublicationStateError("verified publication lacks a remote commit")
            transaction.execute(
                """UPDATE publication_operations SET state = 'applied'
                   WHERE operation_id = ? AND state = 'verified'""",
                (operation_id,),
            )
        elif state != "applied":
            raise PublicationStateError("only a verified publication can be applied")
        if remote_commit is None:
            raise PublicationStateError("applied publication lacks a remote commit")
        return PublicationResult(operation_id, remote_commit, "applied", True)

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
