"""Durable, process-safe agent sessions and continuation decisions."""
from __future__ import annotations

from contextlib import contextmanager
import fcntl
import json
import os
import threading
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Iterator

from .measurements import ContextPolicy, ContextReading, UsageMeasurement
from .supervisor import OperationIdentity


class SessionError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class Checkpoint:
    """A checkpoint which the service has verified at a segment boundary."""
    reference: str
    segment_id: str
    verified_at: float = 0
    verifier: str = "service"
    verified: bool = True

    def __post_init__(self) -> None:
        if not isinstance(self.reference, str) or not self.reference:
            raise SessionError("invalid_checkpoint", "checkpoint reference is required")
        if not isinstance(self.segment_id, str) or not self.segment_id:
            raise SessionError("invalid_checkpoint", "checkpoint segment is required")
        if not isinstance(self.verifier, str) or not self.verifier or not self.verified:
            raise SessionError("invalid_checkpoint", "checkpoint must be verified")
        if not isinstance(self.verified_at, (int, float)) or isinstance(self.verified_at, bool) or self.verified_at < 0:
            raise SessionError("invalid_checkpoint", "checkpoint verification time is invalid")


@dataclass(frozen=True)
class AgentSession:
    session_id: str
    operation: OperationIdentity
    tool: str
    provider_session_id: str
    state: str = "idle"
    active_seconds: float = 0
    action_count: int = 0
    checkpoint: Checkpoint | None = None
    segment_id: str = "initial"
    reading: ContextReading | None = None
    continuation_required: bool = False
    usage_provenance: tuple[UsageMeasurement, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.session_id, str) or not self.session_id:
            raise ValueError("session identifier is invalid")
        if not isinstance(self.operation, OperationIdentity):
            raise ValueError("operation identity is invalid")
        if not isinstance(self.tool, str) or not self.tool or not isinstance(self.provider_session_id, str) or not self.provider_session_id:
            raise ValueError("session route is invalid")
        if self.state not in {"idle", "active", "lost"} or not isinstance(self.segment_id, str) or not self.segment_id:
            raise ValueError("session state is invalid")
        if self.checkpoint is not None and not isinstance(self.checkpoint, Checkpoint):
            raise ValueError("checkpoint is invalid")
        if self.reading is not None and not isinstance(self.reading, ContextReading):
            raise ValueError("context reading is invalid")
        if not isinstance(self.usage_provenance, tuple) or any(not isinstance(item, UsageMeasurement) for item in self.usage_provenance):
            raise ValueError("usage provenance is invalid")

    @property
    def operation_id(self) -> str:
        return self.operation.key


class FileSessionStore:
    """Service-owned JSON state, serialized across managers and processes."""
    _path_locks: dict[Path, threading.RLock] = {}
    _path_locks_guard = threading.Lock()

    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        if not self.path.is_absolute():
            raise SessionError("unsafe_store", "session store path must be absolute")
        self._lock_path = self.path.with_name(f".{self.path.name}.lock")
        key = self.path.resolve(strict=False)
        with self._path_locks_guard:
            self._thread_lock = self._path_locks.setdefault(key, threading.RLock())

    @contextmanager
    def transaction(self) -> Iterator[None]:
        """Hold an advisory file lock over one read/modify/write operation."""
        with self._thread_lock:
            self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            flags = os.O_RDWR | os.O_CREAT | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
            try:
                descriptor = os.open(self._lock_path, flags, 0o600)
            except OSError as error:
                raise SessionError("unsafe_store", "session lock is unsafe") from error
            try:
                if os.fstat(descriptor).st_mode & 0o077:
                    os.fchmod(descriptor, 0o600)
                fcntl.flock(descriptor, fcntl.LOCK_EX)
                yield
            finally:
                try:
                    fcntl.flock(descriptor, fcntl.LOCK_UN)
                finally:
                    os.close(descriptor)

    def load(self, session_id: str) -> AgentSession | None:
        with self.transaction():
            return self._read().get(session_id)

    def save(self, session: AgentSession) -> None:
        with self.transaction():
            values = self._read()
            values[session.session_id] = session
            self._write(values)

    def _read(self) -> dict[str, AgentSession]:
        if not self.path.exists():
            return {}
        if self.path.is_symlink() or self.path.stat().st_mode & 0o077:
            raise SessionError("unsafe_store", "session store is unsafe")
        try:
            values = json.loads(self.path.read_text(encoding="utf-8"))
            if not isinstance(values, dict):
                raise ValueError
            return {key: _decode(value) for key, value in values.items()}
        except (OSError, TypeError, ValueError, KeyError) as error:
            raise SessionError("corrupt_store", "session state is invalid") from error

    def _write(self, values: dict[str, AgentSession]) -> None:
        temporary = self.path.with_name(f".{self.path.name}.new")
        try:
            descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | getattr(os, "O_NOFOLLOW", 0), 0o600)
            with os.fdopen(descriptor, "w", encoding="utf-8") as output:
                json.dump({key: _encode(value) for key, value in values.items()}, output, sort_keys=True)
                output.flush()
                os.fsync(output.fileno())
            os.replace(temporary, self.path)
        except OSError as error:
            raise SessionError("store_write_failed", "could not save session state") from error


class SessionManager:
    def __init__(self, store: FileSessionStore, policy: ContextPolicy = ContextPolicy()) -> None:
        self.store, self.policy = store, policy

    def create(self, session_id: str, operation: OperationIdentity, tool: str, provider_session_id: str) -> AgentSession:
        if not isinstance(operation, OperationIdentity):
            raise SessionError("invalid_operation", "session requires an OperationIdentity")
        if not tool or not provider_session_id:
            raise SessionError("invalid_session", "tool and provider session are required")
        with self.store.transaction():
            values = self.store._read()
            if session_id in values:
                raise SessionError("duplicate_session", "session already exists")
            session = AgentSession(session_id, operation, tool, provider_session_id)
            values[session_id] = session
            self.store._write(values)
            return session

    def begin_action(self, session_id: str) -> AgentSession:
        with self.store.transaction():
            session = self._required_locked(session_id)
            if session.state != "idle" or session.continuation_required:
                raise SessionError("session_busy", "only one ready session action may run")
            return self._save_locked(replace(session, state="active"))

    def finish_action(self, session_id: str, usage: UsageMeasurement) -> AgentSession:
        with self.store.transaction():
            session = self._required_locked(session_id)
            if usage.session_id != session_id:
                raise SessionError("action_mismatch", "session action cannot finish")
            duplicate = next((item for item in session.usage_provenance if item.provenance_key == usage.provenance_key), None)
            if duplicate is not None:
                if duplicate != usage:
                    raise SessionError("provenance_conflict", "usage event has conflicting provenance")
                return session
            if session.state != "active":
                raise SessionError("action_mismatch", "session action cannot finish")
            return self._save_locked(replace(
                session, state="idle", action_count=session.action_count + 1,
                active_seconds=session.active_seconds + usage.active_seconds,
                usage_provenance=(*session.usage_provenance, usage),
            ))

    def observe_context(self, session_id: str, reading: ContextReading, *, now: float | None = None) -> str:
        with self.store.transaction():
            session = self._required_locked(session_id)
            if session.state == "lost" or reading.segment_id != session.segment_id:
                raise SessionError("stale_measurement", "context reading is from another or lost segment")
            classification = reading.classification(self.policy, now=now)
            # A handoff is a durable safety latch.  A later warning/normal
            # sample belongs to the same exhausted provider session and must
            # never make that session runnable again.  Only _replace_locked,
            # after a verified checkpoint, clears it for a distinct provider.
            self._save_locked(replace(
                session,
                reading=reading,
                continuation_required=session.continuation_required or classification == "handoff",
            ))
            return classification

    def checkpoint(self, session_id: str, checkpoint: Checkpoint) -> AgentSession:
        if not isinstance(checkpoint, Checkpoint):
            raise SessionError("invalid_checkpoint", "checkpoint must be structured and verified")
        with self.store.transaction():
            session = self._required_locked(session_id)
            if session.state == "active":
                raise SessionError("session_busy", "checkpoint needs a safe boundary")
            if checkpoint.segment_id != session.segment_id:
                raise SessionError("invalid_checkpoint", "checkpoint belongs to another segment")
            return self._save_locked(replace(session, checkpoint=checkpoint))

    def continue_capacity(self, session_id: str, new_provider_session_id: str) -> AgentSession:
        with self.store.transaction():
            session = self._required_locked(session_id)
            if session.state != "idle" or not session.continuation_required or not self._verified_checkpoint(session):
                raise SessionError("continuation_unavailable", "handoff and verified current checkpoint are required")
            return self._replace_locked(session, new_provider_session_id)

    def mark_lost(self, session_id: str) -> AgentSession:
        with self.store.transaction():
            session = self._required_locked(session_id)
            if session.state != "idle" or not self._verified_checkpoint(session):
                raise SessionError("replacement_unavailable", "lost replacement requires an idle verified checkpoint")
            return self._save_locked(replace(session, state="lost"))

    def replace_lost(self, session_id: str, new_provider_session_id: str) -> AgentSession:
        with self.store.transaction():
            session = self._required_locked(session_id)
            if session.state != "lost" or not self._verified_checkpoint(session):
                raise SessionError("replacement_unavailable", "session must be marked lost with a verified checkpoint")
            return self._replace_locked(session, new_provider_session_id)

    def _replace_locked(self, session: AgentSession, new_provider_session_id: str) -> AgentSession:
        if not isinstance(new_provider_session_id, str) or not new_provider_session_id or new_provider_session_id == session.provider_session_id:
            raise SessionError("invalid_replacement", "replacement provider session must be new")
        return self._save_locked(replace(
            session, provider_session_id=new_provider_session_id, state="idle",
            segment_id=f"{session.segment_id}-next", checkpoint=None, reading=None,
            continuation_required=False,
        ))

    @staticmethod
    def _verified_checkpoint(session: AgentSession) -> bool:
        return bool(session.checkpoint and session.checkpoint.verified and session.checkpoint.segment_id == session.segment_id)

    def _required_locked(self, session_id: str) -> AgentSession:
        session = self.store._read().get(session_id)
        if session is None:
            raise SessionError("unknown_session", "session is not saved")
        return session

    def _save_locked(self, session: AgentSession) -> AgentSession:
        values = self.store._read()
        values[session.session_id] = session
        self.store._write(values)
        return session


def _encode(session: AgentSession) -> dict[str, object]:
    return asdict(session)


def _decode(value: object) -> AgentSession:
    if not isinstance(value, dict):
        raise ValueError
    try:
        decoded = dict(value)
        operation = decoded.get("operation")
        if not isinstance(operation, dict):
            raise ValueError("operation identity is missing")
        decoded["operation"] = OperationIdentity(**operation)

        checkpoint = decoded.get("checkpoint")
        if checkpoint is not None:
            if not isinstance(checkpoint, dict):
                raise ValueError("checkpoint is malformed")
            decoded["checkpoint"] = Checkpoint(**checkpoint)

        reading = decoded.get("reading")
        if reading is not None:
            if not isinstance(reading, dict):
                raise ValueError("context reading is malformed")
            decoded["reading"] = ContextReading(**reading)

        provenance = decoded.get("usage_provenance", ())
        if not isinstance(provenance, list) or any(not isinstance(item, dict) for item in provenance):
            raise ValueError("usage provenance is malformed")
        decoded["usage_provenance"] = tuple(UsageMeasurement(**item) for item in provenance)
        return AgentSession(**decoded)
    except (KeyError, TypeError, ValueError, SessionError) as error:
        raise ValueError("session persistence is malformed") from error
