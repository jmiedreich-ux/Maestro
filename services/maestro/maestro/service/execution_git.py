"""Local Git operations for Execution workspaces: a writable clone, the service's own commit, and path checks.

The coder edits a clone under its workspace's ``output/work``; the service, never the agent, inspects it,
commits anything left uncommitted, checks the commit graph and changed paths, and pushes. Every command
runs with a fixed environment, no terminal prompts and no credential.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Mapping, Sequence

AUTHOR = ("Maestro Coder", "coder@maestro.invalid")


class GitError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def _environment() -> dict[str, str]:
    return {
        "PATH": "/usr/bin:/bin", "HOME": "/nonexistent", "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_TERMINAL_PROMPT": "0", "GIT_OPTIONAL_LOCKS": "0",
        "GIT_AUTHOR_NAME": AUTHOR[0], "GIT_AUTHOR_EMAIL": AUTHOR[1], "GIT_COMMITTER_NAME": AUTHOR[0], "GIT_COMMITTER_EMAIL": AUTHOR[1],
    }


def git(workdir: Path, *arguments: str, check: bool = True) -> str:
    done = subprocess.run(
        ["git", "-c", "safe.directory=*", "-C", str(workdir), *arguments],
        stdin=subprocess.DEVNULL, capture_output=True, env=_environment(), check=False,
    )
    if check and done.returncode != 0:
        raise GitError("git_failed", f"git {arguments[0]} failed: {done.stderr.decode('utf-8', errors='replace').strip()[-300:]}")
    return done.stdout.decode("utf-8", errors="replace")


def prepare_clone(mirror: Path, base: str, destination: Path, branch: str) -> None:
    """A writable clone at the exact base commit on a new local branch; no remote is kept."""
    done = subprocess.run(
        ["git", "clone", "--quiet", "--local", "--no-hardlinks", "--no-checkout", str(mirror), str(destination)],
        stdin=subprocess.DEVNULL, capture_output=True, env=_environment(), check=False,
    )
    if done.returncode != 0:
        raise GitError("clone_failed", f"cannot prepare the work clone: {done.stderr.decode('utf-8', errors='replace').strip()[-300:]}")
    git(destination, "checkout", "--quiet", "-b", branch, base)
    git(destination, "remote", "remove", "origin")
    if git(destination, "rev-parse", "HEAD").strip() != base:
        raise GitError("clone_failed", "the work clone is not at the recorded base commit")
    # The agent runs as another account; let it write everywhere in the clone (ownership is reclaimed after the run).
    for path in [destination, *destination.rglob("*")]:
        if path.is_symlink():
            continue
        path.chmod(path.stat().st_mode | 0o666 | (0o111 if path.is_dir() else 0))


def prepare_agent_home(home: Path) -> None:
    """A git identity and trust setting for the agent's own git commands inside its sandbox."""
    home.mkdir(mode=0o707, exist_ok=True)
    home.chmod(0o707)
    config = home / ".gitconfig"
    config.write_text(f"[user]\n\tname = {AUTHOR[0]}\n\temail = {AUTHOR[1]}\n[safe]\n\tdirectory = *\n", encoding="utf-8")
    config.chmod(0o644)


def seal(workdir: Path, base: str, branch: str, message: str) -> dict[str, object]:
    """Commit what the agent left uncommitted and describe the result relative to the base commit."""
    current = git(workdir, "rev-parse", "--abbrev-ref", "HEAD").strip()
    if current != branch:
        raise GitError("wrong_branch", f"the work clone is on {current}, not the assigned branch")
    ancestor = subprocess.run(["git", "-c", "safe.directory=*", "-C", str(workdir), "merge-base", "--is-ancestor", base, "HEAD"], env=_environment(), capture_output=True)
    if ancestor.returncode != 0:
        raise GitError("bad_graph", "the recorded base commit is not an ancestor of the result")
    if git(workdir, "status", "--porcelain", "--untracked-files=all").strip():
        git(workdir, "add", "-A")
        git(workdir, "commit", "--quiet", "-m", message)
    head = git(workdir, "rev-parse", "HEAD").strip()
    if git(workdir, "status", "--porcelain", "--untracked-files=all").strip():
        raise GitError("dirty_after_commit", "uncommitted output remains after the commit")
    changed = sorted(p for p in git(workdir, "diff", "--name-only", "--no-renames", base, head).split("\n") if p)
    merges = [c for c in git(workdir, "rev-list", "--merges", f"{base}..{head}").split() if c]
    if merges:
        raise GitError("bad_graph", "the result contains merge commits")
    return {"head": head, "changed_paths": changed, "commits": int(git(workdir, "rev-list", "--count", f"{base}..{head}").strip())}


def outside_scope(changed: Sequence[str], permitted: Sequence[str]) -> list[str]:
    """Changed paths not covered by a permitted path (an exact file or a directory prefix)."""
    def covered(path: str) -> bool:
        return any(path == p.rstrip("/") or path.startswith(p.rstrip("/") + "/") for p in permitted)
    return [p for p in changed if not covered(p)]


def diff_text(workdir: Path, base: str, head: str) -> str:
    return git(workdir, "diff", "--no-renames", "--no-color", base, head)
