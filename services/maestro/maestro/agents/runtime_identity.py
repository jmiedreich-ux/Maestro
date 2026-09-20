"""A core-owned local protocol for confirmed agent runtime identities.

The supervisor, core, and planning worker are separate OS identities.  Only
the supervisor UID may publish a confirmed identity; only the planning UID
may consume it.  A planning process never receives a Python callback or a
mutable supervisor reference.
"""

from __future__ import annotations

import json
import os
import socket
import struct
import threading
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable, Mapping

_MAX_MESSAGE_BYTES = 16 * 1024


class RuntimeIdentityProtocolError(RuntimeError):
    """A local runtime-identity protocol request was not authorized."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class ConfirmedRuntimeIdentity:
    """The core record written after supervisor verification only."""

    operation_key: str
    provider: str
    model_id: str
    tool_version: str
    configuration_hash: str
    pid: int
    boot_id: str
    start_identity: str
    invocation_id: str

    def __post_init__(self) -> None:
        for name in (
            "operation_key", "provider", "model_id", "tool_version",
            "configuration_hash", "boot_id", "start_identity", "invocation_id",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value:
                raise RuntimeIdentityProtocolError("invalid_identity", f"{name} must be nonempty")
        if not isinstance(self.pid, int) or isinstance(self.pid, bool) or self.pid <= 0:
            raise RuntimeIdentityProtocolError("invalid_identity", "pid must be positive")

    @classmethod
    def from_mapping(cls, value: Mapping[str, object]) -> "ConfirmedRuntimeIdentity":
        if not isinstance(value, Mapping):
            raise RuntimeIdentityProtocolError("invalid_identity", "identity must be an object")
        fields = {
            "operation_key", "provider", "model_id", "tool_version", "configuration_hash",
            "pid", "boot_id", "start_identity", "invocation_id",
        }
        if set(value) != fields:
            raise RuntimeIdentityProtocolError("invalid_identity", "identity fields are invalid")
        return cls(**{field: value[field] for field in fields})  # type: ignore[arg-type]


class RuntimeIdentityCore:
    """Core-owned, single-consumption identity store.

    UID checks are performed at the protocol boundary using ``SO_PEERCRED``.
    They deliberately do not depend on an actor field supplied by a client.
    """

    def __init__(self, *, supervisor_uid: int, planning_uid: int) -> None:
        for value, name in ((supervisor_uid, "supervisor_uid"), (planning_uid, "planning_uid")):
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise ValueError(f"{name} must be a nonnegative UID")
        if supervisor_uid == planning_uid:
            raise ValueError("supervisor and planning identities must be separate")
        self.supervisor_uid = supervisor_uid
        self.planning_uid = planning_uid
        self._identities: dict[str, ConfirmedRuntimeIdentity] = {}
        # Keep operation keys after planning consumes their value.  Otherwise a
        # compromised supervisor endpoint could replay a new identity for the
        # same durable operation later in its lifecycle.
        self._published_operations: set[str] = set()
        self._lock = threading.Lock()

    def publish(self, peer_uid: int, identity: ConfirmedRuntimeIdentity) -> None:
        if peer_uid != self.supervisor_uid:
            raise RuntimeIdentityProtocolError("publisher_unauthorized", "only the supervisor may publish identity")
        if not isinstance(identity, ConfirmedRuntimeIdentity):
            raise RuntimeIdentityProtocolError("invalid_identity", "identity is invalid")
        with self._lock:
            if identity.operation_key in self._published_operations:
                raise RuntimeIdentityProtocolError("identity_already_published", "runtime identity already exists")
            self._identities[identity.operation_key] = identity
            self._published_operations.add(identity.operation_key)

    def consume(self, peer_uid: int, operation_key: str) -> ConfirmedRuntimeIdentity:
        if peer_uid != self.planning_uid:
            raise RuntimeIdentityProtocolError("consumer_unauthorized", "only planning may consume identity")
        if not isinstance(operation_key, str) or not operation_key:
            raise RuntimeIdentityProtocolError("invalid_operation", "operation key is invalid")
        with self._lock:
            try:
                return self._identities.pop(operation_key)
            except KeyError as error:
                raise RuntimeIdentityProtocolError("identity_unavailable", "confirmed runtime identity is unavailable") from error


class RuntimeIdentityServer:
    """A core process's Unix-socket server.

    The two clients use the same narrow protocol; the kernel peer credentials,
    not caller-supplied JSON, select their authority.
    """

    def __init__(self, path: Path, core: RuntimeIdentityCore, *, peer_uid: Callable[[socket.socket], int] | None = None) -> None:
        self.path = Path(path)
        if not self.path.is_absolute():
            raise ValueError("runtime identity socket must be absolute")
        if not isinstance(core, RuntimeIdentityCore):
            raise TypeError("runtime identity server needs a core")
        self.core = core
        self._peer_uid = peer_uid or _linux_peer_uid
        self._listener: socket.socket | None = None
        self._thread: threading.Thread | None = None
        self._stopped = threading.Event()

    def start(self) -> None:
        if self._listener is not None:
            raise RuntimeError("runtime identity server is already running")
        self.path.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
        if self.path.exists() or self.path.is_symlink():
            raise RuntimeError("runtime identity socket path already exists")
        listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            listener.bind(os.fspath(self.path))
            os.chmod(self.path, 0o660)
            listener.listen(8)
            listener.settimeout(0.1)
        except Exception:
            listener.close()
            if self.path.exists():
                self.path.unlink()
            raise
        self._listener = listener
        self._thread = threading.Thread(target=self._serve, name="maestro-runtime-identity", daemon=True)
        self._thread.start()

    def close(self) -> None:
        self._stopped.set()
        if self._listener is not None:
            self._listener.close()
        if self._thread is not None:
            self._thread.join(timeout=1)
        if self.path.exists() and not self.path.is_symlink():
            self.path.unlink()

    def _serve(self) -> None:
        assert self._listener is not None
        while not self._stopped.is_set():
            try:
                connection, _address = self._listener.accept()
            except (OSError, socket.timeout):
                continue
            with connection:
                self._serve_connection(connection)

    def _serve_connection(self, connection: socket.socket) -> None:
        try:
            peer_uid = self._peer_uid(connection)
            request = _read_message(connection)
            response = self._dispatch(peer_uid, request)
        except RuntimeIdentityProtocolError as error:
            response = {"ok": False, "code": error.code}
        except Exception:
            response = {"ok": False, "code": "protocol_failure"}
        _write_message(connection, response)

    def _dispatch(self, peer_uid: int, request: Mapping[str, object]) -> Mapping[str, object]:
        if set(request) not in ({"action", "identity"}, {"action", "operation_key"}):
            raise RuntimeIdentityProtocolError("invalid_request", "request fields are invalid")
        action = request.get("action")
        if action == "publish":
            self.core.publish(peer_uid, ConfirmedRuntimeIdentity.from_mapping(_mapping(request.get("identity"))))
            return {"ok": True}
        if action == "consume":
            identity = self.core.consume(peer_uid, _text(request.get("operation_key"), "operation_key"))
            return {"ok": True, "identity": asdict(identity)}
        raise RuntimeIdentityProtocolError("invalid_request", "request action is invalid")


class SupervisorIdentityReporter:
    """Supervisor-only client; it can publish but cannot read identities."""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)

    def publish(self, identity: ConfirmedRuntimeIdentity) -> None:
        response = _request(self.path, {"action": "publish", "identity": asdict(identity)})
        _require_success(response)


class PlanningIdentityConsumer:
    """Planning-only client; it can consume one service-confirmed identity."""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)

    def consume(self, operation_key: str) -> ConfirmedRuntimeIdentity:
        response = _request(self.path, {"action": "consume", "operation_key": operation_key})
        _require_success(response)
        return ConfirmedRuntimeIdentity.from_mapping(_mapping(response.get("identity")))


def _linux_peer_uid(connection: socket.socket) -> int:
    if not hasattr(socket, "SO_PEERCRED"):
        raise RuntimeIdentityProtocolError("peer_identity_unavailable", "Unix peer credentials are unavailable")
    raw = connection.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, struct.calcsize("3i"))
    _pid, uid, _gid = struct.unpack("3i", raw)
    return uid


def _request(path: Path, request: Mapping[str, object]) -> Mapping[str, object]:
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
        connection.connect(os.fspath(path))
        _write_message(connection, request)
        return _read_message(connection)


def _read_message(connection: socket.socket) -> Mapping[str, object]:
    chunks: list[bytes] = []
    size = 0
    while True:
        chunk = connection.recv(4096)
        if not chunk:
            break
        chunks.append(chunk)
        size += len(chunk)
        if size > _MAX_MESSAGE_BYTES:
            raise RuntimeIdentityProtocolError("message_too_large", "protocol message is too large")
        if b"\n" in chunk:
            break
    try:
        raw = b"".join(chunks)
        if not raw.endswith(b"\n") or raw.count(b"\n") != 1:
            raise ValueError
        value = json.loads(raw[:-1].decode("utf-8"))
    except (UnicodeDecodeError, ValueError, json.JSONDecodeError) as error:
        raise RuntimeIdentityProtocolError("invalid_request", "protocol message is invalid") from error
    return _mapping(value)


def _write_message(connection: socket.socket, value: Mapping[str, object]) -> None:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8") + b"\n"
    connection.sendall(encoded)


def _mapping(value: object) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise RuntimeIdentityProtocolError("invalid_request", "protocol object is invalid")
    return value


def _text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise RuntimeIdentityProtocolError("invalid_request", f"{field} is invalid")
    return value


def _require_success(response: Mapping[str, object]) -> None:
    if response.get("ok") is True:
        return
    code = response.get("code")
    if not isinstance(code, str):
        code = "protocol_failure"
    raise RuntimeIdentityProtocolError(code, "runtime identity protocol request was rejected")
