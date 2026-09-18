"""Durable, serialized agent sessions and context continuation decisions."""
from __future__ import annotations

import json
import os
import threading
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from time import monotonic

from .measurements import ContextPolicy, ContextReading, UsageMeasurement


class SessionError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message); self.code = code


@dataclass(frozen=True)
class AgentSession:
    session_id: str
    operation_id: str
    tool: str
    provider_session_id: str
    state: str = "idle"
    active_seconds: float = 0
    action_count: int = 0
    checkpoint: str | None = None
    segment_id: str = "initial"
    reading: ContextReading | None = None


class FileSessionStore:
    """Service-owned JSON state; agents receive identifiers, never this path."""
    def __init__(self, path: Path) -> None:
        self.path, self.lock = Path(path), threading.RLock()
        if not self.path.is_absolute(): raise SessionError("unsafe_store", "session store path must be absolute")
    def load(self, session_id: str) -> AgentSession | None:
        with self.lock: return self._read().get(session_id)
    def save(self, session: AgentSession) -> None:
        with self.lock:
            values = self._read(); values[session.session_id] = session; self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            temporary = self.path.with_suffix(".new")
            temporary.write_text(json.dumps({key: _encode(value) for key, value in values.items()}, sort_keys=True), encoding="utf-8")
            os.chmod(temporary, 0o600); os.replace(temporary, self.path)
    def _read(self) -> dict[str, AgentSession]:
        if not self.path.exists(): return {}
        if self.path.is_symlink() or self.path.stat().st_mode & 0o077: raise SessionError("unsafe_store", "session store is unsafe")
        try: return {key: _decode(value) for key, value in json.loads(self.path.read_text(encoding="utf-8")).items()}
        except (OSError, TypeError, ValueError, KeyError): raise SessionError("corrupt_store", "session state is invalid")


class SessionManager:
    def __init__(self, store: FileSessionStore, policy: ContextPolicy = ContextPolicy()) -> None:
        self.store, self.policy, self._lock = store, policy, threading.RLock()
    def create(self, session_id: str, operation_id: str, tool: str, provider_session_id: str) -> AgentSession:
        with self._lock:
            if self.store.load(session_id): raise SessionError("duplicate_session", "session already exists")
            session = AgentSession(session_id, operation_id, tool, provider_session_id); self.store.save(session); return session
    def begin_action(self, session_id: str) -> AgentSession:
        with self._lock:
            session = self._required(session_id)
            if session.state != "idle": raise SessionError("session_busy", "only one session action may run")
            session = replace(session, state="active"); self.store.save(session); return session
    def finish_action(self, session_id: str, usage: UsageMeasurement) -> AgentSession:
        with self._lock:
            session = self._required(session_id)
            if session.state != "active" or usage.session_id != session_id: raise SessionError("action_mismatch", "session action cannot finish")
            session = replace(session, state="idle", action_count=session.action_count + 1, active_seconds=session.active_seconds + usage.active_seconds)
            self.store.save(session); return session
    def observe_context(self, session_id: str, reading: ContextReading, *, now: float | None = None) -> str:
        with self._lock:
            session = self._required(session_id)
            if reading.segment_id != session.segment_id: raise SessionError("stale_measurement", "context reading is from another segment")
            self.store.save(replace(session, reading=reading)); return reading.classification(self.policy, now=now)
    def checkpoint(self, session_id: str, reference: str) -> AgentSession:
        with self._lock:
            if not reference: raise SessionError("invalid_checkpoint", "checkpoint reference is required")
            session = self._required(session_id)
            if session.state == "active": raise SessionError("session_busy", "checkpoint needs a safe boundary")
            session = replace(session, checkpoint=reference); self.store.save(session); return session
    def continue_capacity(self, session_id: str, new_provider_session_id: str) -> AgentSession:
        with self._lock:
            session = self._required(session_id)
            if session.state != "idle" or not session.checkpoint: raise SessionError("continuation_unavailable", "verified idle checkpoint is required")
            session = replace(session, provider_session_id=new_provider_session_id, segment_id=f"{session.segment_id}-next", reading=None)
            self.store.save(session); return session
    def replace_lost(self, session_id: str, new_provider_session_id: str) -> AgentSession:
        return self.continue_capacity(session_id, new_provider_session_id)
    def _required(self, session_id: str) -> AgentSession:
        session = self.store.load(session_id)
        if session is None: raise SessionError("unknown_session", "session is not saved")
        return session


def _encode(session: AgentSession) -> dict[str, object]:
    value = asdict(session); return value
def _decode(value: object) -> AgentSession:
    if not isinstance(value, dict): raise ValueError
    reading = value.get("reading")
    if isinstance(reading, dict): value = {**value, "reading": ContextReading(**reading)}
    return AgentSession(**value)
