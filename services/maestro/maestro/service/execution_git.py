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
INTEGRATOR = ("Maestro Integration", "integration@maestro.invalid")


class GitError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def _environment(identity: tuple[str, str] = AUTHOR) -> dict[str, str]:
    return {
        "PATH": "/usr/bin:/bin", "HOME": "/nonexistent", "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_TERMINAL_PROMPT": "0", "GIT_OPTIONAL_LOCKS": "0",
        "GIT_AUTHOR_NAME": identity[0], "GIT_AUTHOR_EMAIL": identity[1], "GIT_COMMITTER_NAME": identity[0], "GIT_COMMITTER_EMAIL": identity[1],
    }


def git(workdir: Path, *arguments: str, check: bool = True, identity: tuple[str, str] = AUTHOR) -> str:
    done = subprocess.run(
        ["git", "-c", "safe.directory=*", "-C", str(workdir), *arguments],
        stdin=subprocess.DEVNULL, capture_output=True, env=_environment(identity), check=False,
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
    make_writable(destination)


def make_writable(destination: Path) -> None:
    """The agent runs as another account; let it write everywhere in the clone (ownership is reclaimed after the run)."""
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


def _drop_bytecode_caches(workdir: Path) -> None:
    """Untracked Python bytecode left by the agent running tests is not part of its change."""
    for path in git(workdir, "ls-files", "--others", "--exclude-standard").split("\n"):
        if path.endswith(".pyc") and "__pycache__/" in path:
            (workdir / path).unlink(missing_ok=True)


def seal(workdir: Path, base: str, branch: str, message: str) -> dict[str, object]:
    """Commit what the agent left uncommitted and describe the result relative to the base commit."""
    current = git(workdir, "rev-parse", "--abbrev-ref", "HEAD").strip()
    if current != branch:
        raise GitError("wrong_branch", f"the work clone is on {current}, not the assigned branch")
    ancestor = subprocess.run(["git", "-c", "safe.directory=*", "-C", str(workdir), "merge-base", "--is-ancestor", base, "HEAD"], env=_environment(), capture_output=True)
    if ancestor.returncode != 0:
        raise GitError("bad_graph", "the recorded base commit is not an ancestor of the result")
    _drop_bytecode_caches(workdir)
    if git(workdir, "status", "--porcelain", "--untracked-files=all").strip():
        git(workdir, "add", "-A")
        git(workdir, "commit", "--quiet", "-m", message)
    head =git(workdir, "rev-parse", "HEAD").strip()
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


def is_ancestor(workdir: Path, ancestor: str, descendant: str) -> bool:
    done = subprocess.run(["git", "-c", "safe.directory=*", "-C", str(workdir), "merge-base", "--is-ancestor", ancestor, descendant], env=_environment(), capture_output=True)
    return done.returncode == 0


def prepare_merge(mirror: Path, target: str, source: str, destination: Path, branch: str, message: str) -> list[str]:
    """A clone on a new branch at ``target`` with ``source`` merged without fast-forward.

    Returns the conflicted paths: empty when the merge completed cleanly (the merge commit exists), otherwise
    the clone is left in the merge-in-progress state for the Integration Manager to resolve.
    """
    prepare_clone(mirror, target, destination, branch)
    for name in (target, source):
        if git(destination, "cat-file", "-t", name, check=False).strip() != "commit":
            raise GitError("commit_missing", f"commit {name[:12]} is not available in the work clone")
    done = subprocess.run(
        ["git", "-c", "safe.directory=*", "-C", str(destination), "merge", "--no-ff", "--no-edit", "-m", message, source],
        stdin=subprocess.DEVNULL, capture_output=True, env=_environment(INTEGRATOR), check=False,
    )
    if done.returncode == 0:
        return []
    conflicted = sorted(p for p in git(destination, "diff", "--name-only", "--diff-filter=U").split("\n") if p)
    if not conflicted:
        raise GitError("merge_failed", "the merge failed: " + (done.stderr or done.stdout).decode("utf-8", errors="replace").strip()[-300:])
    make_writable(destination)
    return conflicted


def seal_integration(workdir: Path, branch: str, target: str, source: str, message: str) -> dict[str, object]:
    """Finish an integration clone: complete a resolved merge, commit leftovers and check the graph.

    The result must be on the assigned branch, hold no unresolved paths or conflict markers, and descend from
    both the target and the source, so the eventual merge into the milestone branch is a real merge.
    """
    current = git(workdir, "rev-parse", "--abbrev-ref", "HEAD").strip()
    if current != branch:
        raise GitError("wrong_branch", f"the work clone is on {current}, not the assigned branch")
    merging = (workdir / ".git" / "MERGE_HEAD").exists()
    dirty = git(workdir, "status", "--porcelain", "--untracked-files=all").strip()
    if merging or dirty:
        git(workdir, "add", "-A")  # a resolved file the agent forgot to stage still counts as resolved; markers are checked below
        if git(workdir, "ls-files", "--unmerged").strip():
            raise GitError("unresolved_conflicts", "paths are still unmerged")
        markers = [p for p in git(workdir, "diff", "--cached", "--name-only", "--no-renames").split("\n") if p and _has_marker(workdir / p)]
        if markers:
            raise GitError("conflict_markers", "conflict markers remain in " + ", ".join(markers[:5]), )
        if merging:
            git(workdir, "commit", "--quiet", "--no-edit", identity=INTEGRATOR)
        elif git(workdir, "status", "--porcelain").strip():
            git(workdir, "commit", "--quiet", "-m", message, identity=INTEGRATOR)
    head = git(workdir, "rev-parse", "HEAD").strip()
    if git(workdir, "status", "--porcelain", "--untracked-files=all").strip():
        raise GitError("dirty_after_commit", "uncommitted output remains after the commit")
    for name, label in ((target, "target"), (source, "source")):
        if not is_ancestor(workdir, name, head):
            raise GitError("bad_graph", f"the integration result does not contain the {label} commit {name[:12]}")
    paths = sorted(p for p in git(workdir, "diff", "--name-only", "--no-renames", target, head).split("\n") if p)
    return {"head": head, "changed_paths": paths}


def _has_marker(path: Path) -> bool:
    try:
        with path.open("rb") as handle:
            return any(line.startswith((b"<<<<<<< ", b">>>>>>> ")) for line in handle)
    except OSError:
        return False


def merge_into(mirror: Path, target: str, source: str, destination: Path, branch: str, message: str) -> str:
    """A non-fast-forward merge of ``source`` into ``target`` in a clone; the merge commit is returned."""
    conflicted = prepare_merge(mirror, target, source, destination, branch, message)
    if conflicted:
        raise GitError("merge_conflict", "the reviewed integration branch no longer merges cleanly: " + ", ".join(conflicted[:5]))
    head = git(destination, "rev-parse", "HEAD").strip()
    if len(git(destination, "rev-list", "--parents", "-n", "1", "HEAD").split()) != 3:
        raise GitError("bad_graph", "the milestone merge is not a two-parent merge commit")
    return head
