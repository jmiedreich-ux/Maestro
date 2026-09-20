"""Durable, identity-checked supervision for one isolated agent run.

The supervisor records intent *before* asking systemd to start a unit.  A
restart can therefore distinguish an acknowledged run from a launch whose
outcome is unknown; it never starts a replacement itself.
"""

from __future__ import annotations

import json
import os
import re
import signal
import subprocess
import threading
import time
import uuid
from dataclasses import asdict, dataclass, field, replace
from pathlib import Path
from typing import Callable, Mapping, Protocol, Sequence

from maestro.foundation import ContractError, canonical_identifier

from .preflight import (
    ResolvedAgentRoute,
    RunningToolIdentity,
    verify_running_identity,
)
from .routes import AgentRouteError


_START_FIELD = 21  # Linux /proc/<pid>/stat field 22, zero-indexed.
_UNIT_RUN = re.compile(r"[A-Za-z0-9_.-]{1,128}\Z")


class SupervisionError(RuntimeError):
    """A launch, identity, or termination operation could not be confirmed."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class OperationIdentity:
    project_id: str
    activity_id: str
    assignment_id: str
    run_id: str

    def __post_init__(self) -> None:
        for value, name in (
            (self.project_id, "project_id"),
            (self.activity_id, "activity_id"),
            (self.assignment_id, "assignment_id"),
            (self.run_id, "run_id"),
        ):
            canonical_identifier(value, name)

    @property
    def key(self) -> str:
        return ":".join((self.project_id, self.activity_id, self.assignment_id, self.run_id))

    @property
    def unit_name(self) -> str:
        # This deliberately rejects identifiers that systemd would reinterpret.
        if _UNIT_RUN.fullmatch(self.run_id) is None:
            raise SupervisionError("invalid_run_id", "run identifier cannot name a systemd unit")
        return f"maestro-agent-{self.run_id}.service"


@dataclass(frozen=True)
class LaunchRequest:
    identity: OperationIdentity
    command: tuple[str, ...]
    cwd: str
    timeout_seconds: float
    stall_seconds: float

    def __post_init__(self) -> None:
        if not self.command or any(not isinstance(part, str) or not part for part in self.command):
            raise SupervisionError("invalid_launch", "launch command must contain nonempty text")
        if not Path(self.command[0]).is_absolute():
            raise SupervisionError("invalid_launch", "launch executable must be absolute")
        if not Path(self.cwd).is_absolute():
            raise SupervisionError("invalid_launch", "launch working directory must be absolute")
        for value, name in ((self.timeout_seconds, "timeout"), (self.stall_seconds, "stall")):
            if not isinstance(value, (int, float)) or isinstance(value, bool) or value <= 0:
                raise SupervisionError("invalid_launch", f"{name} duration must be positive")


@dataclass(frozen=True)
class UnitIdentity:
    unit_name: str
    pid: int
    boot_id: str
    start_identity: str
    invocation_id: str
    active: bool
    cgroup_empty: bool

    def matches(self, saved: "RunRecord") -> bool:
        invocation_matches = bool(self.invocation_id) and self.invocation_id == saved.invocation_id
        if not invocation_matches:
            return False
        # systemd clears MainPID after an invocation exits.  Its InvocationID
        # remains attached to the retained transient unit, so that is the
        # durable proof for a known, empty completed invocation.
        if not self.active and self.cgroup_empty:
            return self.unit_name == saved.unit_name and self.boot_id == saved.boot_id
        return (
            self.unit_name == saved.unit_name
            and self.pid == saved.pid
            and self.boot_id == saved.boot_id
            and self.start_identity == saved.start_identity
        )


@dataclass
class ManagedUnit:
    identity: UnitIdentity
    process: subprocess.Popen[bytes] | None = None
    stdout: object | None = None
    stderr: object | None = None
    readers: list[threading.Thread] = field(default_factory=list)


class UnitController(Protocol):
    def launch(self, request: LaunchRequest) -> ManagedUnit: ...
    def inspect(self, unit_name: str) -> UnitIdentity | None: ...
    def stop(self, unit_name: str) -> None: ...


@dataclass(frozen=True)
class SupervisorRuntimeIdentity:
    """Adapter metadata delivered only after the reserved run is confirmed."""

    operation: OperationIdentity
    tool_identity: RunningToolIdentity
    pid: int
    boot_id: str
    start_identity: str
    invocation_id: str


RuntimeIdentityConsumer = Callable[[SupervisorRuntimeIdentity], None]


@dataclass(frozen=True)
class RunRecord:
    identity: OperationIdentity
    unit_name: str
    command: tuple[str, ...]
    cwd: str
    timeout_seconds: float
    stall_seconds: float
    state: str
    launched_monotonic: float
    pid: int | None = None
    boot_id: str | None = None
    start_identity: str | None = None
    invocation_id: str | None = None
    last_activity_monotonic: float | None = None
    terminal_reason: str | None = None
    events: tuple[Mapping[str, object], ...] = ()


class SupervisorJournal(Protocol):
    def get(self, key: str) -> RunRecord | None: ...
    def save(self, record: RunRecord) -> None: ...


class FileSupervisorJournal:
    """Small service-owned snapshot journal, intentionally outside workspaces."""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        if not self.path.is_absolute():
            raise SupervisionError("unsafe_journal", "supervision journal must be absolute")
        self._lock = threading.Lock()

    def get(self, key: str) -> RunRecord | None:
        with self._lock:
            return self._read().get(key)

    def save(self, record: RunRecord) -> None:
        with self._lock:
            records = self._read()
            records[record.identity.key] = record
            self._write(records)

    def _read(self) -> dict[str, RunRecord]:
        if not self.path.exists():
            return {}
        self._safe_file()
        try:
            value = json.loads(self.path.read_text(encoding="utf-8"))
            rows = value["records"]
            if value.get("version") != 1 or not isinstance(rows, Mapping):
                raise ValueError
            return {key: _record_from_mapping(row) for key, row in rows.items()}
        except (OSError, ValueError, TypeError, KeyError, ContractError) as error:
            raise SupervisionError("corrupt_journal", "supervision journal is invalid") from error

    def _write(self, records: Mapping[str, RunRecord]) -> None:
        self.path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        self._safe_parent()
        temporary = self.path.with_suffix(self.path.suffix + ".new")
        payload = {
            "version": 1,
            "records": {key: _record_mapping(value) for key, value in sorted(records.items())},
        }
        descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, sort_keys=True, separators=(",", ":"))
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, self.path)
        finally:
            if temporary.exists():
                temporary.unlink()

    def _safe_parent(self) -> None:
        metadata = self.path.parent.stat()
        if self.path.parent.is_symlink() or metadata.st_uid != os.getuid() or metadata.st_mode & 0o022:
            raise SupervisionError("unsafe_journal", "journal parent is not service-owned")

    def _safe_file(self) -> None:
        metadata = self.path.stat()
        if self.path.is_symlink() or metadata.st_uid != os.getuid() or metadata.st_mode & 0o077:
            raise SupervisionError("unsafe_journal", "journal is not service-owned")


class SystemdUserUnits:
    """The production controller: a separate systemd user unit per run."""

    def __init__(self, *, systemd_run: str = "/usr/bin/systemd-run", systemctl: str = "/usr/bin/systemctl") -> None:
        self.systemd_run = systemd_run
        self.systemctl = systemctl

    def launch(self, request: LaunchRequest) -> ManagedUnit:
        unit = request.identity.unit_name
        arguments = (
            self.systemd_run, "--user", "--unit", unit, "--quiet", "--pipe",
            "--property=KillMode=control-group", "--property=TimeoutStopSec=30s",
            "--property=SendSIGKILL=yes", "--property=RemainAfterExit=yes",
            f"--working-directory={request.cwd}", "--", *request.command,
        )
        process = subprocess.Popen(
            arguments,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=self._user_bus_environment(),
        )
        deadline = time.monotonic() + 5
        observed: UnitIdentity | None = None
        while time.monotonic() < deadline:
            observed = self.inspect(unit)
            if observed is not None and observed.pid > 0 and observed.active:
                return ManagedUnit(observed, process, process.stdout, process.stderr)
            if process.poll() is not None:
                break
            time.sleep(0.05)
        process.kill()
        raise SupervisionError("launch_unconfirmed", "systemd did not confirm the launched unit")

    def inspect(self, unit_name: str) -> UnitIdentity | None:
        completed = subprocess.run(
            (
                self.systemctl, "--user", "show", unit_name,
                "--property=MainPID", "--property=ActiveState", "--property=ControlGroup", "--property=InvocationID",
            ),
            capture_output=True, text=True, check=False, env=self._user_bus_environment(),
        )
        if completed.returncode != 0:
            return None
        fields = dict(line.split("=", 1) for line in completed.stdout.splitlines() if "=" in line)
        try:
            pid = int(fields.get("MainPID", "0"))
        except ValueError:
            return None
        active = pid > 0 and fields.get("ActiveState") in {"active", "activating", "deactivating"}
        invocation_id = fields.get("InvocationID", "")
        if pid <= 0:
            return UnitIdentity(unit_name, 0, _boot_id(), "", invocation_id, active, self._cgroup_empty(fields.get("ControlGroup", "")))
        return UnitIdentity(unit_name, pid, _boot_id(), _proc_start_identity(pid), invocation_id, active, self._cgroup_empty(fields.get("ControlGroup", "")))

    def stop(self, unit_name: str) -> None:
        completed = subprocess.run(
            (self.systemctl, "--user", "stop", unit_name),
            capture_output=True, text=True, check=False, env=self._user_bus_environment(),
        )
        if completed.returncode != 0:
            raise SupervisionError("stop_failed", "systemd did not accept the stop request")

    @staticmethod
    def _user_bus_environment() -> dict[str, str]:
        """Address this UID's user manager even from a system service."""
        runtime_dir = f"/run/user/{os.getuid()}"
        environment = dict(os.environ)
        environment["XDG_RUNTIME_DIR"] = runtime_dir
        environment["DBUS_SESSION_BUS_ADDRESS"] = f"unix:path={runtime_dir}/bus"
        return environment

    @staticmethod
    def _cgroup_empty(control_group: str) -> bool:
        if not control_group or not control_group.startswith("/"):
            return True
        try:
            return not Path("/sys/fs/cgroup", control_group.lstrip("/"), "cgroup.procs").read_text(encoding="utf-8").strip()
        except OSError:
            return False


class LocalProcessUnits:
    """A real process-group controller used only by isolated component tests."""

    def __init__(self) -> None:
        self._units: dict[str, subprocess.Popen[bytes]] = {}
        self._identities: dict[str, tuple[str, str, str]] = {}

    def launch(self, request: LaunchRequest) -> ManagedUnit:
        process = subprocess.Popen(request.command, cwd=request.cwd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
        self._units[request.identity.unit_name] = process
        self._identities[request.identity.unit_name] = (_boot_id(), _proc_start_identity(process.pid), uuid.uuid4().hex)
        return ManagedUnit(self._inspect(request.identity.unit_name), process, process.stdout, process.stderr)

    def inspect(self, unit_name: str) -> UnitIdentity | None:
        if unit_name not in self._units:
            return None
        return self._inspect(unit_name)

    def _inspect(self, unit_name: str) -> UnitIdentity:
        process = self._units[unit_name]
        active = process.poll() is None
        boot_id, start_identity, invocation_id = self._identities[unit_name]
        return UnitIdentity(
            unit_name,
            process.pid,
            boot_id,
            start_identity,
            invocation_id,
            active,
            _process_group_empty(process.pid),
        )

    def stop(self, unit_name: str) -> None:
        process = self._units.get(unit_name)
        if process is None:
            raise SupervisionError("unknown_unit", "the process unit is not known")
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait(timeout=5)
        for stream in (process.stdin, process.stdout, process.stderr):
            if stream is not None:
                stream.close()


def _synchronized(method: Callable[..., object]) -> Callable[..., object]:
    def synchronized(self: "AgentSupervisor", *args: object, **kwargs: object) -> object:
        with self._lock:
            return method(self, *args, **kwargs)
    return synchronized


class AgentSupervisor:
    def __init__(self, journal: SupervisorJournal, units: UnitController, *, clock: Callable[[], float] = time.monotonic) -> None:
        self.journal, self.units, self.clock = journal, units, clock
        self._managed: dict[str, ManagedUnit] = {}
        self._runtime_identity_callbacks: dict[
            str, tuple[ResolvedAgentRoute, RuntimeIdentityConsumer]
        ] = {}
        self._runtime_identity_delivered: set[str] = set()
        self._lock = threading.RLock()

    @_synchronized
    def reserve_runtime_identity_callback(
        self,
        identity: OperationIdentity,
        route: ResolvedAgentRoute,
        callback: RuntimeIdentityConsumer,
    ) -> None:
        """Reserve the sole service callback that may receive one run's identity.

        Reservation precedes launch, so an adapter cannot attach metadata to a
        different or already-existing operation.  The callback is intentionally
        in-memory capability wiring: it is not agent input and is not recovered
        as a substitute for a new service-owned reservation.
        """
        if (
            not isinstance(identity, OperationIdentity)
            or not isinstance(route, ResolvedAgentRoute)
            or not callable(callback)
        ):
            raise SupervisionError(
                "runtime_identity_callback_invalid",
                "runtime identity callback reservation is invalid",
            )
        key = identity.key
        if self.journal.get(key) is not None:
            raise SupervisionError(
                "runtime_identity_callback_late",
                "runtime identity callback must be reserved before launch",
            )
        if key in self._runtime_identity_callbacks:
            raise SupervisionError(
                "runtime_identity_callback_duplicate",
                "operation already has a runtime identity callback",
            )
        self._runtime_identity_callbacks[key] = (route, callback)

    @_synchronized
    def runtime_identity_callback(
        self, identity: OperationIdentity
    ) -> Callable[[RunningToolIdentity], None]:
        """Return the adapter-only reporter for one confirmed reserved operation."""
        if not isinstance(identity, OperationIdentity):
            raise SupervisionError(
                "runtime_identity_callback_invalid", "operation identity is invalid"
            )
        record = self._required(identity)
        key = identity.key
        if record.state != "running" or key not in self._runtime_identity_callbacks:
            raise SupervisionError(
                "runtime_identity_callback_unavailable",
                "runtime identity callback is not available for this operation",
            )
        if key in self._runtime_identity_delivered:
            raise SupervisionError(
                "runtime_identity_callback_delivered",
                "runtime identity was already delivered for this operation",
            )

        def report(tool_identity: RunningToolIdentity) -> None:
            self._deliver_runtime_identity(identity, tool_identity)

        return report

    @_synchronized
    def _deliver_runtime_identity(
        self, identity: OperationIdentity, tool_identity: RunningToolIdentity
    ) -> None:
        """Confirm the live unit before delivering trusted adapter metadata."""
        if not isinstance(tool_identity, RunningToolIdentity) or tool_identity.source != "tool_metadata":
            raise SupervisionError(
                "runtime_identity_unverified",
                "adapter runtime identity is not trusted tool metadata",
            )
        record = self._required(identity)
        key = identity.key
        reservation = self._runtime_identity_callbacks.get(key)
        if record.state != "running" or reservation is None or key in self._runtime_identity_delivered:
            raise SupervisionError(
                "runtime_identity_callback_unavailable",
                "runtime identity callback is not available for this operation",
            )
        route, callback = reservation
        try:
            tool_identity = verify_running_identity(route, tool_identity)
        except AgentRouteError as error:
            raise SupervisionError(
                "runtime_identity_mismatch",
                "adapter runtime identity differs from the reserved route",
            ) from error
        observed = self.units.inspect(record.unit_name)
        if observed is None or not observed.active or not observed.matches(record):
            raise SupervisionError(
                "runtime_identity_unconfirmed",
                "supervisor cannot confirm the operation receiving runtime identity",
            )
        delivery = SupervisorRuntimeIdentity(
            operation=identity,
            tool_identity=tool_identity,
            pid=observed.pid,
            boot_id=observed.boot_id,
            start_identity=observed.start_identity,
            invocation_id=observed.invocation_id,
        )
        try:
            callback(delivery)
        except Exception as error:
            raise SupervisionError(
                "runtime_identity_callback_failed",
                "reserved operation callback rejected runtime identity",
            ) from error
        self._runtime_identity_delivered.add(key)
        self._save(
            replace(
                record,
                events=(*record.events, self._event("runtime_identity_confirmed")),
            )
        )

    @_synchronized
    def launch(self, request: LaunchRequest) -> RunRecord:
        key = request.identity.key
        existing = self.journal.get(key)
        if existing is not None:
            raise SupervisionError("duplicate_operation", "saved operation already has a launch record")
        intent = RunRecord(
            request.identity,
            request.identity.unit_name,
            request.command,
            request.cwd,
            request.timeout_seconds,
            request.stall_seconds,
            "launch_intent",
            self.clock(),
            events=(self._event("intent"),),
        )
        self._save(intent)
        intent = self._required(request.identity)
        try:
            managed = self.units.launch(request)
        except Exception as error:
            self._save(replace(intent, state="launch_uncertain", events=(*intent.events, self._event("launch_unconfirmed"))))
            if isinstance(error, SupervisionError):
                raise
            raise SupervisionError("launch_unconfirmed", "agent launch was not acknowledged") from error
        unit = managed.identity
        if not unit.active or unit.pid <= 0 or not unit.start_identity or not unit.invocation_id:
            self._save(replace(intent, state="launch_uncertain", events=(*intent.events, self._event("launch_unconfirmed"))))
            raise SupervisionError("launch_unconfirmed", "agent launch identity was not confirmed")
        running = replace(
            intent,
            state="running",
            pid=unit.pid,
            boot_id=unit.boot_id,
            start_identity=unit.start_identity,
            invocation_id=unit.invocation_id,
            last_activity_monotonic=self.clock(),
            events=(*intent.events, self._event("launch_confirmed", pid=unit.pid)),
        )
        running = self._save(running)
        self._managed[key] = managed
        self._drain(key, managed, "stdout")
        self._drain(key, managed, "stderr")
        return running

    @_synchronized
    def poll(self, identity: OperationIdentity) -> RunRecord:
        record = self._required(identity)
        if record.state in {"completed", "failed", "cancelled", "timed_out", "stalled", "stopped", "stop_unconfirmed", "recovery_required"}:
            return record
        now = self.clock()
        if now >= record.launched_monotonic + record.timeout_seconds:
            return self.stop(identity, "timed_out")
        unit = self.units.inspect(record.unit_name)
        if unit is None or not unit.matches(record):
            return self._terminal(record, "stop_unconfirmed", "identity_unknown")
        if not unit.active and unit.cgroup_empty:
            # Retained systemd units keep the pipe endpoint open after their
            # main process exits.  The empty, identity-matched control group
            # is already the completion proof; release that exited unit so
            # the adapter pipes can close without starting a replacement.
            try:
                self.units.stop(record.unit_name)
            except Exception:
                return self._terminal(record, "stop_unconfirmed", "completed_unit_release_failed")
            self._join_readers(identity.key)
            record = self._required(identity)
            managed = self._managed.get(identity.key)
            completed = self._terminal(record, "completed", _exit_reason(managed))
            self._close_managed(identity.key)
            return completed
        if now - (record.last_activity_monotonic or record.launched_monotonic) >= record.stall_seconds:
            return self.stop(identity, "stalled")
        return record

    @_synchronized
    def heartbeat(self, identity: OperationIdentity, detail: str = "") -> RunRecord:
        """Record a trusted agent heartbeat; polling alone never resets a stall timer."""
        record = self._required(identity)
        if record.state != "running":
            raise SupervisionError("heartbeat_rejected", "only a running operation can report a heartbeat")
        return self._save(
            replace(
                record,
                last_activity_monotonic=self.clock(),
                events=(*record.events, self._event("heartbeat", detail=detail)),
            )
        )

    @_synchronized
    def stop(self, identity: OperationIdentity, reason: str, *, interrupt: Callable[[], None] | None = None) -> RunRecord:
        record = self._required(identity)
        if record.state in {"completed", "failed", "cancelled", "timed_out", "stalled", "stopped"}:
            return record
        unit = self.units.inspect(record.unit_name)
        if unit is None or not unit.matches(record):
            return self._terminal(record, "stop_unconfirmed", "identity_unknown")
        if interrupt is not None:
            interrupt()
        self._save(replace(record, state="stopping", terminal_reason=reason, events=(*record.events, self._event("stop_requested", reason=reason))))
        try:
            self.units.stop(record.unit_name)
        except Exception:
            return self._terminal(self._required(identity), "stop_unconfirmed", reason)
        observed = self.units.inspect(record.unit_name)
        if observed is not None and (observed.active or not observed.cgroup_empty):
            return self._terminal(self._required(identity), "stop_unconfirmed", reason)
        state = {"cancelled": "cancelled", "timed_out": "timed_out", "stalled": "stalled"}.get(reason, "stopped")
        stopped = self._terminal(self._required(identity), state, reason)
        self._close_managed(identity.key)
        return stopped

    def _drain(self, key: str, managed: ManagedUnit, stream_name: str) -> None:
        stream = getattr(managed, stream_name)
        if stream is None:
            return
        def reader() -> None:
            for raw in iter(stream.readline, b""):
                self._record_stream(key, stream_name, raw)
        thread = threading.Thread(target=reader, daemon=True)
        managed.readers.append(thread)
        thread.start()

    @_synchronized
    def _record_stream(self, key: str, stream_name: str, raw: bytes) -> None:
        record = self.journal.get(key)
        if record is None:
            return
        event = self._event(stream_name, data=raw.decode("utf-8", "replace"))
        self._save(replace(record, events=(*record.events, event), last_activity_monotonic=self.clock()))

    def _required(self, identity: OperationIdentity) -> RunRecord:
        record = self.journal.get(identity.key)
        if record is None:
            raise SupervisionError("unknown_operation", "no saved operation exists")
        return record

    def _save(self, record: RunRecord) -> RunRecord:
        events = tuple({**event, "sequence": sequence} for sequence, event in enumerate(record.events, 1))
        if events != record.events:
            record = replace(record, events=events)
        self.journal.save(record)
        return record

    def _close_managed(self, key: str) -> None:
        managed = self._managed.pop(key, None)
        if managed is None:
            return
        for stream in (managed.process.stdin if managed.process else None, managed.stdout, managed.stderr):
            if stream is not None:
                stream.close()

    def _join_readers(self, key: str) -> None:
        managed = self._managed.get(key)
        if managed is None:
            return
        for reader in managed.readers:
            reader.join(timeout=1)

    def _terminal(self, record: RunRecord, state: str, reason: str) -> RunRecord:
        if record.terminal_reason is not None and record.state == state:
            return record
        return self._save(
            replace(record, state=state, terminal_reason=reason, events=(*record.events, self._event("terminal", state=state, reason=reason)))
        )

    def _event(self, kind: str, **fields: object) -> dict[str, object]:
        return {"sequence": -1, "kind": kind, "at_monotonic": self.clock(), **fields}


def _boot_id() -> str:
    try:
        return Path("/proc/sys/kernel/random/boot_id").read_text(encoding="utf-8").strip()
    except OSError as error:
        raise SupervisionError("identity_unavailable", "host boot identity is unavailable") from error


def _proc_start_identity(pid: int) -> str:
    try:
        fields = Path(f"/proc/{pid}/stat").read_text(encoding="utf-8").rsplit(") ", 1)[1].split()
        return fields[_START_FIELD - 2]
    except (OSError, IndexError, ValueError) as error:
        raise SupervisionError("identity_unavailable", "process start identity is unavailable") from error


def _process_group_empty(process_group: int) -> bool:
    """Return whether the isolated local process group has any live members."""
    if process_group <= 0:
        return True
    try:
        os.killpg(process_group, 0)
    except ProcessLookupError:
        return True
    except PermissionError:
        return False
    return False


def _exit_reason(managed: ManagedUnit | None) -> str:
    if managed is None or managed.process is None or managed.process.returncode is None:
        return "unit_ended"
    return "exit_0" if managed.process.returncode == 0 else f"exit_{managed.process.returncode}"


def _record_mapping(record: RunRecord) -> dict[str, object]:
    result = asdict(record)
    result["identity"] = asdict(record.identity)
    result["command"] = list(record.command)
    result["events"] = list(record.events)
    return result


def _record_from_mapping(value: object) -> RunRecord:
    if not isinstance(value, Mapping):
        raise ValueError("record is invalid")
    identity = value["identity"]
    if not isinstance(identity, Mapping):
        raise ValueError("identity is invalid")
    return RunRecord(OperationIdentity(**identity), str(value["unit_name"]), tuple(value["command"]), str(value["cwd"]), float(value["timeout_seconds"]), float(value["stall_seconds"]), str(value["state"]), float(value["launched_monotonic"]), None if value.get("pid") is None else int(value["pid"]), value.get("boot_id"), value.get("start_identity"), value.get("invocation_id"), None if value.get("last_activity_monotonic") is None else float(value["last_activity_monotonic"]), value.get("terminal_reason"), tuple(value.get("events", ())))
