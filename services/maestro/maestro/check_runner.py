"""Real declared-check execution (M3 A3 dry run, shared with D1 grading).

Runs a project's own declared gate commands (from its manifest's
verification.* fields) against a real checkout and returns structured,
real evidence — never a scripted or assumed pass/fail. A3 uses this
without dispatching any packet, to prove a binding's declared gates are
real and currently honest before anything depends on them. D1 (Wave D)
reuses the exact same runner against a real executor attempt's result;
the mechanism does not change between "dry run" and "grade an attempt",
only what triggered it and what happens to the result afterward.
"""

from __future__ import annotations

import shlex
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path


class CheckCommandError(ValueError):
    """Raised when a declared command string cannot be safely parsed."""


@dataclass(frozen=True)
class CheckResult:
    command: str
    exit_code: int
    passed: bool
    stdout: str
    stderr: str
    duration_seconds: float


def run_declared_checks(
    repository_path: Path, commands: list[str], *, timeout_seconds: float = 600.0
) -> tuple[CheckResult, ...]:
    """Run each declared command, in order, in ``repository_path``.

    Commands run with ``shell=False`` (parsed via ``shlex.split``) —
    never a raw shell string — so a manifest's own declared command
    cannot smuggle shell metacharacters into an unintended pipeline,
    even though manifest scalars are already Owner-reviewed content by
    the time a binding is active, not untrusted external input.

    Does not stop at the first failure: every declared command is a
    real gate on its own, and an honest dry run/grading result reports
    all of them, not just the first one reached.
    """
    results: list[CheckResult] = []
    for command in commands:
        results.append(_run_one(repository_path, command, timeout_seconds))
    return tuple(results)


def _run_one(repository_path: Path, command: str, timeout_seconds: float) -> CheckResult:
    try:
        arguments = shlex.split(command)
    except ValueError as error:
        raise CheckCommandError(f"declared command is not safely parseable: {command!r}") from error
    if not arguments:
        raise CheckCommandError(f"declared command is empty: {command!r}")

    started_at = time.monotonic()
    try:
        completed = subprocess.run(
            arguments,
            cwd=repository_path,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            shell=False,
        )
        duration = time.monotonic() - started_at
        return CheckResult(
            command=command,
            exit_code=completed.returncode,
            passed=completed.returncode == 0,
            stdout=completed.stdout,
            stderr=completed.stderr,
            duration_seconds=duration,
        )
    except subprocess.TimeoutExpired as error:
        duration = time.monotonic() - started_at
        return CheckResult(
            command=command,
            exit_code=-1,
            passed=False,
            stdout=(error.stdout or b"").decode("utf-8", "replace") if isinstance(error.stdout, bytes) else (error.stdout or ""),
            stderr=f"timed out after {timeout_seconds}s",
            duration_seconds=duration,
        )
    except FileNotFoundError as error:
        duration = time.monotonic() - started_at
        return CheckResult(
            command=command,
            exit_code=-1,
            passed=False,
            stdout="",
            stderr=f"command not found: {error}",
            duration_seconds=duration,
        )


def all_passed(results: tuple[CheckResult, ...]) -> bool:
    return all(result.passed for result in results)
