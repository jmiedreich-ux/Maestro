"""Real executor adapter contract (M3 Wave C) and one real local worker.

Implements the versioned capability contract from
`agent-workforce-control-plane.md` §11.1 (submit/observe/cancel/retrieve
evidence) as an actual interface (C1), then wires it to one real local
worker (C2): the `qwen` CLI (Qwen Code) against a local Ollama model —
the same local-Qwen executor Foundry's own AGENTS.md and this session's
registered manifest both name as the first real executor class.

Preflight (§9.1) and handoff (§9.2) are represented as their own real,
typed shapes rather than loose dicts, so a caller cannot accidentally
skip a required field.
"""

from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol


class ExecutorError(RuntimeError):
    """Raised when an executor adapter operation cannot proceed safely."""


@dataclass(frozen=True)
class ExecutorPreflight:
    """§9.1's required preflight, checked before any dispatch.

    ``worktree_path`` must already be an isolated, clean checkout at
    ``base_commit`` — this adapter does not create or clean worktrees
    itself; that is the caller's own responsibility, kept separate so
    a bug in one does not silently mask a bug in the other.
    """

    base_commit: str
    worktree_path: Path
    allowed_paths: tuple[str, ...]
    forbidden_paths: tuple[str, ...]
    model_identity: str


@dataclass(frozen=True)
class ExecutorObservation:
    """Real, current status of one submitted attempt."""

    handle: str
    running: bool
    exit_code: int | None


@dataclass(frozen=True)
class ExecutorHandoff:
    """§9.2's required handoff shape, read once an attempt has finished."""

    branch_name: str
    commit_sha: str | None
    changed_files: tuple[str, ...]
    raw_output: str
    completed: bool


class ExecutorAdapter(Protocol):
    """The versioned capability contract: submit/observe/cancel/evidence."""

    def submit(self, preflight: ExecutorPreflight, instructions: str) -> str:
        """Dispatch one real attempt; returns a real execution handle."""
        ...

    def observe(self, handle: str) -> ExecutorObservation:
        """Real, current status — never invented from silence."""
        ...

    def cancel(self, handle: str) -> None:
        ...

    def retrieve_evidence(self, handle: str, *, branch_name: str) -> ExecutorHandoff:
        """Only valid once ``observe`` reports the attempt is finished."""
        ...


@dataclass
class _LocalAttempt:
    process: subprocess.Popen
    log_path: Path
    worktree_path: Path
    base_commit: str


class LocalQwenExecutorAdapter:
    """C2: one real local worker — the `qwen` CLI against Ollama.

    Each ``submit`` spawns a real, isolated subprocess (`qwen -p ... --yolo`)
    in the given worktree, capturing its output to a real log file rather
    than buffering it in memory (a real coding-agent run can produce a lot
    of output). ``observe``/``cancel``/``retrieve_evidence`` operate on the
    real OS process — no simulated timing.
    """

    def __init__(self, *, qwen_binary: str = "qwen") -> None:
        self._qwen_binary = qwen_binary
        self._attempts: dict[str, _LocalAttempt] = {}

    def submit(self, preflight: ExecutorPreflight, instructions: str) -> str:
        if not preflight.worktree_path.is_dir():
            raise ExecutorError(f"worktree does not exist: {preflight.worktree_path}")
        handle = f"local-qwen-{int(time.time() * 1000)}"
        log_path = preflight.worktree_path.parent / f"{handle}.log"
        with log_path.open("wb") as log_file:
            process = subprocess.Popen(
                [self._qwen_binary, "-p", instructions, "--yolo"],
                cwd=preflight.worktree_path,
                stdout=log_file,
                stderr=subprocess.STDOUT,
            )
        # The child inherited its own duplicate file descriptor at Popen
        # time; closing this parent-side handle here does not affect it.
        self._attempts[handle] = _LocalAttempt(process, log_path, preflight.worktree_path, preflight.base_commit)
        return handle

    def observe(self, handle: str) -> ExecutorObservation:
        attempt = self._require_attempt(handle)
        exit_code = attempt.process.poll()
        return ExecutorObservation(handle=handle, running=exit_code is None, exit_code=exit_code)

    def cancel(self, handle: str) -> None:
        attempt = self._require_attempt(handle)
        if attempt.process.poll() is None:
            attempt.process.terminate()
            try:
                attempt.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                attempt.process.kill()
                attempt.process.wait(timeout=5)

    def retrieve_evidence(self, handle: str, *, branch_name: str) -> ExecutorHandoff:
        attempt = self._require_attempt(handle)
        observation = self.observe(handle)
        if observation.running:
            raise ExecutorError(f"attempt {handle} has not finished yet")
        raw_output = attempt.log_path.read_text(errors="replace") if attempt.log_path.exists() else ""
        head_commit = _real_head_commit(attempt.worktree_path)
        made_a_commit = head_commit is not None and head_commit != attempt.base_commit
        changed_files = (
            _real_changed_files(attempt.worktree_path, attempt.base_commit) if made_a_commit else ()
        )
        commit_sha = head_commit if made_a_commit else None
        return ExecutorHandoff(
            branch_name=branch_name,
            commit_sha=commit_sha,
            changed_files=changed_files,
            raw_output=raw_output,
            completed=observation.exit_code == 0,
        )

    def _require_attempt(self, handle: str) -> _LocalAttempt:
        try:
            return self._attempts[handle]
        except KeyError as error:
            raise ExecutorError(f"unknown execution handle: {handle}") from error


def _real_changed_files(worktree_path: Path, base_commit: str) -> tuple[str, ...]:
    completed = subprocess.run(
        ["git", "diff", "--name-only", f"{base_commit}..HEAD"],
        cwd=worktree_path,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        return ()
    return tuple(sorted(line for line in completed.stdout.splitlines() if line))


def _real_head_commit(worktree_path: Path) -> str | None:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=worktree_path, capture_output=True, text=True
    )
    if completed.returncode != 0:
        return None
    return completed.stdout.strip()
