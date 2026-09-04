"""Mechanical proof gate for immutable review candidates."""

from __future__ import annotations

import hashlib
import json
import os
import signal
import subprocess
import tempfile
import time
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any


REQUEST_SCHEMA = "maestro.review-readiness.request/v1"
RESULT_SCHEMA = "maestro.review-readiness.result/v1"
MAX_CAPTURE_BYTES = 65_536

_REQUEST_KEYS = {
    "schema",
    "slice_id",
    "review_kind",
    "repository",
    "base",
    "head",
    "allowed_paths",
    "validation_commands",
    "reconstruction_commands",
    "timeout_seconds",
}
_COMMAND_KEYS = {"check_id", "argv"}
_RESULT_KEYS = {
    "schema",
    "request",
    "request_bytes_sha256",
    "resolved_base",
    "resolved_head",
    "checked_out_head_before",
    "checked_out_head_after",
    "changed_paths",
    "clean_before",
    "clean_after",
    "checks",
    "callback",
    "blockers",
    "ready",
    "record_digest",
}
_CHECK_KEYS = {
    "check_id",
    "category",
    "argv",
    "outcome",
    "exit_code",
    "elapsed_milliseconds",
    "stdout",
    "stderr",
    "skip_reason",
}
_STREAM_KEYS = {"bytes_total", "sha256", "truncated", "text_utf8"}
_CALLBACK_KEYS = {"outcome", "detail"}
_BLOCKER_KEYS = {"code", "check_id", "detail"}
_REVIEW_KINDS = {
    "DecisionFidelity",
    "TargetedDecisionFidelity",
    "IndependentImplementation",
    "TargetedImplementation",
}
_CHECK_OUTCOMES = {"Passed", "Failed", "TimedOut", "LaunchError", "Skipped"}
_SKIP_REASONS = {
    "RepositoryInvalid",
    "RevisionInvalid",
    "HeadMismatchBefore",
    "EmptyRange",
    "DirtyBefore",
    "PathNotAllowed",
}
_BLOCKER_CODES = {
    "MALFORMED_REQUEST",
    "REPOSITORY_INVALID",
    "BASE_NOT_COMMIT",
    "HEAD_NOT_COMMIT",
    "HEAD_NOT_CHECKED_OUT_BEFORE",
    "EMPTY_COMMIT_RANGE",
    "EMPTY_CHANGED_PATHS",
    "DIRTY_BEFORE",
    "PATH_NOT_ALLOWED",
    "VALIDATION_FAILED",
    "VALIDATION_TIMED_OUT",
    "VALIDATION_LAUNCH_ERROR",
    "RECONSTRUCTION_FAILED",
    "RECONSTRUCTION_TIMED_OUT",
    "RECONSTRUCTION_LAUNCH_ERROR",
    "DIRTY_AFTER",
    "HEAD_NOT_CHECKED_OUT_AFTER",
    "CALLBACK_EXCEPTION",
}
_CALLBACK_OUTCOMES = {"NotRequested", "Suppressed", "Succeeded", "Raised"}
_HEX_DIGEST = set("0123456789abcdef")


class RequestError(ValueError):
    """A deterministic request-contract violation."""


class ResultError(ValueError):
    """A deterministic result-contract violation."""


def canonical_json(value: Any) -> bytes:
    """Return the canonical UTF-8 JSON representation used by the wire contract."""
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _reject_constant(value: str) -> None:
    raise RequestError(f"non-finite JSON number {value}")


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise RequestError(f"duplicate object key {key}")
        result[key] = value
    return result


def parse_request(request_bytes: bytes) -> dict[str, Any]:
    """Decode and validate one closed review-readiness request."""
    try:
        text = request_bytes.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise RequestError(f"invalid UTF-8 at byte {error.start}") from error
    try:
        value = json.loads(text, object_pairs_hook=_unique_object, parse_constant=_reject_constant)
    except RequestError:
        raise
    except json.JSONDecodeError as error:
        raise RequestError(f"invalid JSON at byte {error.pos}") from error
    _validate_request(value, RequestError)
    return value


def _utf8(value: str, label: str, error_type: type[ValueError]) -> None:
    try:
        value.encode("utf-8")
    except UnicodeEncodeError as error:
        raise error_type(f"{label} is not valid UTF-8") from error


def _closed_keys(
    value: Any,
    expected: set[str],
    label: str,
    error_type: type[ValueError],
) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        raise error_type(f"{label} must be an object")
    actual = set(value)
    for key in sorted(expected | actual, key=lambda item: item.encode("utf-8")):
        if key not in actual:
            raise error_type(f"{label} is missing key {key}")
        if key not in expected:
            raise error_type(f"{label} has unknown key {key}")
    return value


def _nonempty_text(value: Any, label: str, error_type: type[ValueError]) -> str:
    if not isinstance(value, str) or not value:
        raise error_type(f"{label} must be a nonempty string")
    _utf8(value, label, error_type)
    return value


def _validate_request(value: Any, error_type: type[ValueError]) -> None:
    request = _closed_keys(value, _REQUEST_KEYS, "request", error_type)
    seen_check_ids: set[str] = set()
    validators: dict[str, Callable[[], None]] = {
        "allowed_paths": lambda: _validate_allowed_paths(request["allowed_paths"], error_type),
        "base": lambda: _nonempty_text(request["base"], "base", error_type),
        "head": lambda: _nonempty_text(request["head"], "head", error_type),
        "reconstruction_commands": lambda: _validate_commands(
            request["reconstruction_commands"],
            "reconstruction_commands",
            seen_check_ids,
            error_type,
        ),
        "repository": lambda: _validate_repository_field(request["repository"], error_type),
        "review_kind": lambda: _validate_enum(
            request["review_kind"], _REVIEW_KINDS, "review_kind", error_type
        ),
        "schema": lambda: _validate_literal(request["schema"], REQUEST_SCHEMA, "schema", error_type),
        "slice_id": lambda: _nonempty_text(request["slice_id"], "slice_id", error_type),
        "timeout_seconds": lambda: _validate_timeout(request["timeout_seconds"], error_type),
        "validation_commands": lambda: _validate_commands(
            request["validation_commands"],
            "validation_commands",
            seen_check_ids,
            error_type,
        ),
    }
    for key in sorted(validators, key=lambda item: item.encode("utf-8")):
        validators[key]()


def _validate_literal(
    value: Any, expected: str, label: str, error_type: type[ValueError]
) -> None:
    if value != expected or not isinstance(value, str):
        raise error_type(f"{label} must equal {expected}")


def _validate_enum(
    value: Any, allowed: set[str], label: str, error_type: type[ValueError]
) -> None:
    if not isinstance(value, str) or value not in allowed:
        raise error_type(f"{label} has an invalid value")


def _validate_repository_field(value: Any, error_type: type[ValueError]) -> None:
    repository = _nonempty_text(value, "repository", error_type)
    if not Path(repository).is_absolute():
        raise error_type("repository must be an absolute path")


def _validate_timeout(value: Any, error_type: type[ValueError]) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 3600:
        raise error_type("timeout_seconds must be an integer from 1 through 3600")


def _validate_allowed_paths(value: Any, error_type: type[ValueError]) -> None:
    if not isinstance(value, list) or not value:
        raise error_type("allowed_paths must be a nonempty array")
    paths: list[str] = []
    for index, path in enumerate(value):
        path = _nonempty_text(path, f"allowed_paths[{index}]", error_type)
        if path.startswith("/") or "\\" in path:
            raise error_type(f"allowed_paths[{index}] is not repository-relative")
        directory = path.endswith("/")
        body = path[:-1] if directory else path
        segments = body.split("/")
        if not body or any(segment in {"", ".", ".."} for segment in segments):
            raise error_type(f"allowed_paths[{index}] has an invalid path segment")
        paths.append(path)
    ordered = sorted(paths, key=lambda item: item.encode("utf-8"))
    if paths != ordered:
        raise error_type("allowed_paths must be sorted by UTF-8 bytes")
    if len(set(paths)) != len(paths):
        raise error_type("allowed_paths must contain unique entries")


def _validate_commands(
    value: Any,
    label: str,
    seen: set[str],
    error_type: type[ValueError],
) -> None:
    if not isinstance(value, list) or not value:
        raise error_type(f"{label} must be a nonempty array")
    for index, candidate in enumerate(value):
        command = _closed_keys(candidate, _COMMAND_KEYS, f"{label}[{index}]", error_type)
        # Object members are validated in canonical UTF-8-byte key order.
        argv = command["argv"]
        if not isinstance(argv, list) or not argv:
            raise error_type(f"{label}[{index}].argv must be a nonempty array")
        for arg_index, argument in enumerate(argv):
            _nonempty_text(argument, f"{label}[{index}].argv[{arg_index}]", error_type)
        check_id = _nonempty_text(command["check_id"], f"{label}[{index}].check_id", error_type)
        if check_id in seen:
            raise error_type(f"duplicate check_id {check_id}")
        seen.add(check_id)


def _empty_stream() -> dict[str, Any]:
    return {
        "bytes_total": 0,
        "sha256": _digest(b""),
        "truncated": False,
        "text_utf8": "",
    }


def _read_stream(stream: Any) -> dict[str, Any]:
    stream.seek(0)
    hasher = hashlib.sha256()
    retained = bytearray()
    total = 0
    while True:
        chunk = stream.read(64 * 1024)
        if not chunk:
            break
        total += len(chunk)
        hasher.update(chunk)
        if len(retained) < MAX_CAPTURE_BYTES:
            retained.extend(chunk[: MAX_CAPTURE_BYTES - len(retained)])
    return {
        "bytes_total": total,
        "sha256": hasher.hexdigest(),
        "truncated": total > MAX_CAPTURE_BYTES,
        "text_utf8": bytes(retained).decode("utf-8", errors="replace"),
    }


def _exception_text(error: BaseException) -> str:
    return f"{type(error).__name__}: {error}"


def _run_command(
    repository: Path,
    command: Mapping[str, Any],
    category: str,
    timeout_seconds: int,
) -> dict[str, Any]:
    started = time.monotonic_ns()
    outcome = "LaunchError"
    exit_code: int | None = None
    with tempfile.TemporaryFile() as stdout_file, tempfile.TemporaryFile() as stderr_file:
        try:
            process = subprocess.Popen(
                command["argv"],
                cwd=repository,
                stdin=subprocess.DEVNULL,
                stdout=stdout_file,
                stderr=stderr_file,
                start_new_session=True,
            )
        except (OSError, ValueError, subprocess.SubprocessError) as error:
            elapsed = max(0, (time.monotonic_ns() - started) // 1_000_000)
            result = _check_result(command, category, "LaunchError", None, elapsed)
            result["stderr"] = _empty_stream()
            result["launch_exception"] = _exception_text(error)
            return result
        try:
            exit_code = process.wait(timeout=timeout_seconds)
            outcome = "Passed" if exit_code == 0 else "Failed"
        except subprocess.TimeoutExpired:
            outcome = "TimedOut"
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait()
        elapsed = max(0, (time.monotonic_ns() - started) // 1_000_000)
        result = _check_result(command, category, outcome, exit_code if outcome in {"Passed", "Failed"} else None, elapsed)
        result["stdout"] = _read_stream(stdout_file)
        result["stderr"] = _read_stream(stderr_file)
        return result


def _check_result(
    command: Mapping[str, Any],
    category: str,
    outcome: str,
    exit_code: int | None,
    elapsed: int,
    skip_reason: str | None = None,
) -> dict[str, Any]:
    return {
        "check_id": command["check_id"],
        "category": category,
        "argv": list(command["argv"]),
        "outcome": outcome,
        "exit_code": exit_code,
        "elapsed_milliseconds": elapsed,
        "stdout": _empty_stream(),
        "stderr": _empty_stream(),
        "skip_reason": skip_reason,
    }


def _skipped_checks(request: Mapping[str, Any], reason: str) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    for category, key in (
        ("Validation", "validation_commands"),
        ("Reconstruction", "reconstruction_commands"),
    ):
        for command in request[key]:
            checks.append(_check_result(command, category, "Skipped", None, 0, reason))
    return checks


def _blocker(code: str, detail: str, check_id: str | None = None) -> dict[str, Any]:
    return {"code": code, "check_id": check_id, "detail": detail}


def _git(repository: Path, *arguments: str) -> subprocess.CompletedProcess[bytes]:
    argv = ["git", "-C", str(repository), *arguments]
    try:
        return subprocess.run(
            argv,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        return subprocess.CompletedProcess(
            argv,
            127,
            stdout=b"",
            stderr=_exception_text(error).encode("utf-8", errors="replace"),
        )


def _repository_root(repository: str) -> Path | None:
    candidate = Path(repository)
    result = _git(candidate, "rev-parse", "--show-toplevel")
    if result.returncode != 0:
        return None
    try:
        root = Path(result.stdout.rstrip(b"\n").decode("utf-8", errors="strict"))
    except UnicodeDecodeError:
        return None
    return root if root.is_absolute() else None


def _resolve(repository: Path, revision: str) -> str | None:
    result = _git(repository, "rev-parse", "--verify", "--end-of-options", f"{revision}^{{commit}}")
    if result.returncode != 0:
        return None
    value = result.stdout.strip().decode("ascii", errors="ignore")
    return value if len(value) == 40 and set(value) <= _HEX_DIGEST else None


def _commit_count(repository: Path, base: str, head: str) -> int | None:
    result = _git(repository, "rev-list", "--count", f"{base}..{head}")
    try:
        return int(result.stdout.strip()) if result.returncode == 0 else None
    except ValueError:
        return None


def _changed_paths(repository: Path, base: str, head: str) -> list[str] | None:
    result = _git(repository, "diff", "--name-only", "-z", f"{base}..{head}")
    if result.returncode != 0:
        return None
    paths = {
        item.decode("utf-8", errors="replace")
        for item in result.stdout.split(b"\0")
        if item
    }
    return sorted(paths, key=lambda item: item.encode("utf-8"))


def _status_paths(repository: Path) -> list[str] | None:
    result = _git(repository, "status", "--porcelain=v1", "-z", "--untracked-files=all")
    if result.returncode != 0:
        return None
    records = [item for item in result.stdout.split(b"\0") if item]
    paths: set[str] = set()
    index = 0
    while index < len(records):
        record = records[index]
        if len(record) < 3 or record[2:3] != b" ":
            path_bytes = record
            rename = False
        else:
            path_bytes = record[3:]
            rename = record[:1] in {b"R", b"C"} or record[1:2] in {b"R", b"C"}
        paths.add(path_bytes.decode("utf-8", errors="replace"))
        if rename and index + 1 < len(records):
            index += 1
            paths.add(records[index].decode("utf-8", errors="replace"))
        index += 1
    return sorted(paths, key=lambda item: item.encode("utf-8"))


def _path_allowed(path: str, allowed_paths: list[str]) -> bool:
    for rule in allowed_paths:
        if rule.endswith("/"):
            if path.startswith(rule) and len(path) > len(rule):
                return True
        elif path == rule:
            return True
    return False


def _malformed_result(
    request_bytes: bytes,
    reason: str,
    callback_requested: bool,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "schema": RESULT_SCHEMA,
        "request": None,
        "request_bytes_sha256": _digest(request_bytes),
        "resolved_base": None,
        "resolved_head": None,
        "checked_out_head_before": None,
        "checked_out_head_after": None,
        "changed_paths": [],
        "clean_before": None,
        "clean_after": None,
        "checks": [],
        "callback": {
            "outcome": "Suppressed" if callback_requested else "NotRequested",
            "detail": None,
        },
        "blockers": [
            _blocker(
                "MALFORMED_REQUEST",
                f"request does not conform to {REQUEST_SCHEMA}: {reason}",
            )
        ],
        "ready": False,
        "record_digest": "",
    }
    return _seal(result)


def malformed_request_result(request_bytes: bytes, reason: str) -> dict[str, Any]:
    """Build the closed CLI result for bytes a request path could not supply."""
    return _malformed_result(request_bytes, reason, False)


def _seal(result: dict[str, Any]) -> dict[str, Any]:
    unsigned = dict(result)
    unsigned.pop("record_digest", None)
    result["record_digest"] = _digest(canonical_json(unsigned))
    return result


def evaluate_review_readiness(
    request_bytes: bytes,
    launch_callback: Callable[[], None] | None = None,
) -> dict[str, Any]:
    """Evaluate a candidate and invoke ``launch_callback`` only after all proof passes."""
    try:
        request = parse_request(request_bytes)
    except RequestError as error:
        return _malformed_result(request_bytes, str(error), launch_callback is not None)

    result: dict[str, Any] = {
        "schema": RESULT_SCHEMA,
        "request": request,
        "request_bytes_sha256": _digest(request_bytes),
        "resolved_base": None,
        "resolved_head": None,
        "checked_out_head_before": None,
        "checked_out_head_after": None,
        "changed_paths": [],
        "clean_before": None,
        "clean_after": None,
        "checks": [],
        "callback": {"outcome": "NotRequested", "detail": None},
        "blockers": [],
        "ready": False,
        "record_digest": "",
    }
    blockers: list[dict[str, Any]] = result["blockers"]
    repository = _repository_root(request["repository"])
    if repository is None:
        blockers.append(
            _blocker(
                "REPOSITORY_INVALID",
                f"repository is not a Git worktree: {request['repository']}",
            )
        )
        result["checks"] = _skipped_checks(request, "RepositoryInvalid")
        if launch_callback is not None:
            result["callback"]["outcome"] = "Suppressed"
        return _seal(result)

    resolved_base = _resolve(repository, request["base"])
    resolved_head = _resolve(repository, request["head"])
    checked_before = _resolve(repository, "HEAD")
    status_before = _status_paths(repository)
    result["resolved_base"] = resolved_base
    result["resolved_head"] = resolved_head
    result["checked_out_head_before"] = checked_before
    result["clean_before"] = None if status_before is None else not status_before

    if resolved_base is None:
        blockers.append(_blocker("BASE_NOT_COMMIT", f"base^{{commit}} did not resolve: {request['base']}"))
    if resolved_head is None:
        blockers.append(_blocker("HEAD_NOT_COMMIT", f"head^{{commit}} did not resolve: {request['head']}"))
    if resolved_head is not None and checked_before != resolved_head:
        blockers.append(
            _blocker(
                "HEAD_NOT_CHECKED_OUT_BEFORE",
                f"checked-out HEAD before commands is {checked_before or 'null'}, expected {resolved_head}",
            )
        )

    commit_count: int | None = None
    paths: list[str] | None = None
    if resolved_base is not None and resolved_head is not None:
        commit_count = _commit_count(repository, resolved_base, resolved_head)
        paths = _changed_paths(repository, resolved_base, resolved_head)
        result["changed_paths"] = paths or []
        if resolved_base == resolved_head or commit_count == 0:
            blockers.append(_blocker("EMPTY_COMMIT_RANGE", "base..head contains no commit"))
        if paths == []:
            blockers.append(_blocker("EMPTY_CHANGED_PATHS", "base..head contains no changed path"))
    if status_before:
        blockers.append(
            _blocker("DIRTY_BEFORE", f"worktree is dirty before commands: {','.join(status_before)}")
        )
    disallowed = [] if paths is None else [
        path for path in paths if not _path_allowed(path, request["allowed_paths"])
    ]
    blockers.extend(
        _blocker("PATH_NOT_ALLOWED", f"changed path is outside allowed_paths: {path}")
        for path in disallowed
    )

    skip_reason: str | None = None
    if resolved_base is None or resolved_head is None:
        skip_reason = "RevisionInvalid"
    elif checked_before != resolved_head:
        skip_reason = "HeadMismatchBefore"
    elif resolved_base == resolved_head or commit_count == 0 or paths == []:
        skip_reason = "EmptyRange"
    elif status_before:
        skip_reason = "DirtyBefore"
    elif disallowed:
        skip_reason = "PathNotAllowed"

    if skip_reason is not None:
        result["checks"] = _skipped_checks(request, skip_reason)
    else:
        checks: list[dict[str, Any]] = []
        for category, key, prefix in (
            ("Validation", "validation_commands", "VALIDATION"),
            ("Reconstruction", "reconstruction_commands", "RECONSTRUCTION"),
        ):
            for command in request[key]:
                check = _run_command(repository, command, category, request["timeout_seconds"])
                launch_exception = check.pop("launch_exception", None)
                checks.append(check)
                if check["outcome"] == "Failed":
                    blockers.append(
                        _blocker(
                            f"{prefix}_FAILED",
                            f"{category.lower()} check {check['check_id']} exited {check['exit_code']}",
                            check["check_id"],
                        )
                    )
                elif check["outcome"] == "TimedOut":
                    blockers.append(
                        _blocker(
                            f"{prefix}_TIMED_OUT",
                            f"{category.lower()} check {check['check_id']} exceeded {request['timeout_seconds']} seconds",
                            check["check_id"],
                        )
                    )
                elif check["outcome"] == "LaunchError":
                    blockers.append(
                        _blocker(
                            f"{prefix}_LAUNCH_ERROR",
                            f"{category.lower()} check {check['check_id']} could not launch: {launch_exception}",
                            check["check_id"],
                        )
                    )
        result["checks"] = checks

    status_after = _status_paths(repository)
    checked_after = _resolve(repository, "HEAD")
    result["clean_after"] = None if status_after is None else not status_after
    result["checked_out_head_after"] = checked_after
    if status_after:
        blockers.append(_blocker("DIRTY_AFTER", f"worktree is dirty after commands: {','.join(status_after)}"))
    if resolved_head is not None and checked_after != resolved_head:
        blockers.append(
            _blocker(
                "HEAD_NOT_CHECKED_OUT_AFTER",
                f"checked-out HEAD after commands is {checked_after or 'null'}, expected {resolved_head}",
            )
        )

    if blockers:
        if launch_callback is not None:
            result["callback"]["outcome"] = "Suppressed"
    elif launch_callback is not None:
        try:
            launch_callback()
        except Exception as error:  # callback boundary deliberately records user exceptions
            detail = _exception_text(error)
            result["callback"] = {"outcome": "Raised", "detail": detail}
            blockers.append(_blocker("CALLBACK_EXCEPTION", f"review callback raised: {detail}"))
        else:
            result["callback"] = {"outcome": "Succeeded", "detail": None}
    result["ready"] = not blockers and (
        launch_callback is None or result["callback"]["outcome"] == "Succeeded"
    )
    return _seal(result)


def validate_result(value: Any) -> None:
    """Reject any result outside the closed result schema or with a bad digest."""
    result = _closed_keys(value, _RESULT_KEYS, "result", ResultError)
    _validate_literal(result["schema"], RESULT_SCHEMA, "result.schema", ResultError)
    if result["request"] is not None:
        _validate_request(result["request"], ResultError)
    _validate_digest(result["request_bytes_sha256"], "result.request_bytes_sha256")
    _nullable_commit(result["resolved_base"], "result.resolved_base")
    _nullable_commit(result["resolved_head"], "result.resolved_head")
    _nullable_commit(result["checked_out_head_before"], "result.checked_out_head_before")
    _nullable_commit(result["checked_out_head_after"], "result.checked_out_head_after")
    if not isinstance(result["changed_paths"], list) or any(
        not isinstance(path, str) for path in result["changed_paths"]
    ):
        raise ResultError("result.changed_paths must be a string array")
    if result["changed_paths"] != sorted(set(result["changed_paths"]), key=lambda item: item.encode("utf-8")):
        raise ResultError("result.changed_paths must be unique and UTF-8-byte sorted")
    for field in ("clean_before", "clean_after"):
        if result[field] is not None and not isinstance(result[field], bool):
            raise ResultError(f"result.{field} must be boolean or null")
    if not isinstance(result["checks"], list):
        raise ResultError("result.checks must be an array")
    for index, check in enumerate(result["checks"]):
        _validate_check(check, index)
    _validate_callback(result["callback"])
    if not isinstance(result["blockers"], list):
        raise ResultError("result.blockers must be an array")
    for index, blocker in enumerate(result["blockers"]):
        _validate_blocker(blocker, index)
    if not isinstance(result["ready"], bool):
        raise ResultError("result.ready must be boolean")
    expected_ready = not result["blockers"] and result["callback"]["outcome"] in {
        "NotRequested",
        "Succeeded",
    }
    if result["ready"] != expected_ready:
        raise ResultError("result.ready is inconsistent with blockers and callback")
    if result["request"] is None:
        if result["checks"]:
            raise ResultError("a malformed result cannot contain command checks")
        if not any(blocker["code"] == "MALFORMED_REQUEST" for blocker in result["blockers"]):
            raise ResultError("a null request requires MALFORMED_REQUEST")
    else:
        expected_commands = [
            ("Validation", command)
            for command in result["request"]["validation_commands"]
        ] + [
            ("Reconstruction", command)
            for command in result["request"]["reconstruction_commands"]
        ]
        if len(result["checks"]) != len(expected_commands):
            raise ResultError("result.checks does not cover every named command")
        for index, (category, command) in enumerate(expected_commands):
            check = result["checks"][index]
            if (
                check["category"] != category
                or check["check_id"] != command["check_id"]
                or check["argv"] != command["argv"]
            ):
                raise ResultError("result.checks does not preserve command order and identity")
    _validate_digest(result["record_digest"], "result.record_digest")
    unsigned = dict(result)
    supplied = unsigned.pop("record_digest")
    if supplied != _digest(canonical_json(unsigned)):
        raise ResultError("result.record_digest does not reproduce")


def _validate_digest(value: Any, label: str) -> None:
    if not isinstance(value, str) or len(value) != 64 or set(value) - _HEX_DIGEST:
        raise ResultError(f"{label} must be a lowercase SHA-256")


def _nullable_commit(value: Any, label: str) -> None:
    if value is not None and (
        not isinstance(value, str) or len(value) != 40 or set(value) - _HEX_DIGEST
    ):
        raise ResultError(f"{label} must be a lowercase commit SHA or null")


def _validate_check(value: Any, index: int) -> None:
    label = f"result.checks[{index}]"
    check = _closed_keys(value, _CHECK_KEYS, label, ResultError)
    _nonempty_text(check["check_id"], f"{label}.check_id", ResultError)
    _validate_enum(check["category"], {"Validation", "Reconstruction"}, f"{label}.category", ResultError)
    if not isinstance(check["argv"], list) or not check["argv"]:
        raise ResultError(f"{label}.argv must be a nonempty array")
    for arg_index, argument in enumerate(check["argv"]):
        _nonempty_text(argument, f"{label}.argv[{arg_index}]", ResultError)
    _validate_enum(check["outcome"], _CHECK_OUTCOMES, f"{label}.outcome", ResultError)
    if check["outcome"] in {"Passed", "Failed"}:
        if isinstance(check["exit_code"], bool) or not isinstance(check["exit_code"], int):
            raise ResultError(f"{label}.exit_code must be an integer")
        if check["outcome"] == "Passed" and check["exit_code"] != 0:
            raise ResultError(f"{label}.Passed requires exit code zero")
        if check["outcome"] == "Failed" and check["exit_code"] == 0:
            raise ResultError(f"{label}.Failed requires nonzero exit code")
    elif check["exit_code"] is not None:
        raise ResultError(f"{label}.exit_code must be null")
    if (
        isinstance(check["elapsed_milliseconds"], bool)
        or not isinstance(check["elapsed_milliseconds"], int)
        or check["elapsed_milliseconds"] < 0
    ):
        raise ResultError(f"{label}.elapsed_milliseconds must be nonnegative")
    _validate_stream(check["stdout"], f"{label}.stdout")
    _validate_stream(check["stderr"], f"{label}.stderr")
    if check["outcome"] == "Skipped":
        _validate_enum(check["skip_reason"], _SKIP_REASONS, f"{label}.skip_reason", ResultError)
        if check["elapsed_milliseconds"] != 0 or check["stdout"] != _empty_stream() or check["stderr"] != _empty_stream():
            raise ResultError(f"{label}.Skipped requires zero elapsed time and empty streams")
    elif check["skip_reason"] is not None:
        raise ResultError(f"{label}.skip_reason must be null")


def _validate_stream(value: Any, label: str) -> None:
    stream = _closed_keys(value, _STREAM_KEYS, label, ResultError)
    if isinstance(stream["bytes_total"], bool) or not isinstance(stream["bytes_total"], int) or stream["bytes_total"] < 0:
        raise ResultError(f"{label}.bytes_total must be nonnegative")
    _validate_digest(stream["sha256"], f"{label}.sha256")
    if not isinstance(stream["truncated"], bool):
        raise ResultError(f"{label}.truncated must be boolean")
    if stream["truncated"] != (stream["bytes_total"] > MAX_CAPTURE_BYTES):
        raise ResultError(f"{label}.truncated is inconsistent")
    if not isinstance(stream["text_utf8"], str):
        raise ResultError(f"{label}.text_utf8 must be a string")


def _validate_callback(value: Any) -> None:
    callback = _closed_keys(value, _CALLBACK_KEYS, "result.callback", ResultError)
    _validate_enum(callback["outcome"], _CALLBACK_OUTCOMES, "result.callback.outcome", ResultError)
    if callback["outcome"] == "Raised":
        _nonempty_text(callback["detail"], "result.callback.detail", ResultError)
    elif callback["detail"] is not None:
        raise ResultError("result.callback.detail must be null")


def _validate_blocker(value: Any, index: int) -> None:
    label = f"result.blockers[{index}]"
    blocker = _closed_keys(value, _BLOCKER_KEYS, label, ResultError)
    _validate_enum(blocker["code"], _BLOCKER_CODES, f"{label}.code", ResultError)
    command_code = blocker["code"].startswith("VALIDATION_") or blocker["code"].startswith("RECONSTRUCTION_")
    if command_code:
        _nonempty_text(blocker["check_id"], f"{label}.check_id", ResultError)
    elif blocker["check_id"] is not None:
        raise ResultError(f"{label}.check_id must be null")
    _nonempty_text(blocker["detail"], f"{label}.detail", ResultError)


def result_exit_code(result: Mapping[str, Any]) -> int:
    """Return the closed CLI status mapping."""
    return 0 if result.get("ready") is True else 2
