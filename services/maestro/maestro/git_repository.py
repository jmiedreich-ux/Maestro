"""Read-only, exact-commit access to a local Git worktree."""

from __future__ import annotations

import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path


class GitRepositoryError(ValueError):
    """A requested Git fact is invalid, malformed, or unavailable."""


class GitEntryMissing(GitRepositoryError):
    """A path has no entry at the requested commit."""


@dataclass(frozen=True)
class GitBlob:
    path: str
    object_id: str
    content: bytes


_FULL_OBJECT_ID = re.compile(r"[0-9a-fA-F]{40}\Z")


class ReadOnlyGitRepository:
    """A small argument-array Git adapter with no write or network operation."""

    def __init__(self, repository_path: Path) -> None:
        self.path = repository_path.resolve()
        if not repository_path.exists() or not repository_path.is_dir():
            raise GitRepositoryError("repository_path must be an existing directory")
        check = self._run("rev-parse", "--is-inside-work-tree", check=False)
        if check.returncode != 0 or check.stdout.strip() != b"true":
            raise GitRepositoryError("repository_path must be an existing Git worktree")

    def exact_commit(self, source_revision: str) -> str:
        if not isinstance(source_revision, str) or not _FULL_OBJECT_ID.fullmatch(source_revision):
            raise GitRepositoryError("source_revision must be one full 40-hex object ID")
        object_id = source_revision.lower()
        result = self._run("cat-file", "-t", object_id, check=False)
        if result.returncode != 0:
            raise GitRepositoryError("source_revision does not name an existing object")
        if result.stdout.strip() != b"commit":
            raise GitRepositoryError("source_revision must name a commit object directly")
        return object_id

    def read_blob(self, commit: str, path: str, *, maximum_bytes: int) -> GitBlob:
        result = self._run("ls-tree", "-z", commit, "--", path)
        if not result.stdout:
            raise GitEntryMissing(path)
        records = [record for record in result.stdout.split(b"\0") if record]
        if len(records) != 1:
            raise GitRepositoryError(f"path resolves to multiple Git entries: {path}")
        try:
            metadata, raw_name = records[0].split(b"\t", 1)
            mode, entry_type, object_id = metadata.decode("ascii").split(" ")
            entry_name = raw_name.decode("utf-8")
        except (ValueError, UnicodeDecodeError) as exc:
            raise GitRepositoryError(f"invalid Git tree entry for {path}") from exc
        if entry_name != path:
            raise GitRepositoryError(f"Git returned an unexpected path for {path}")
        if mode == "120000":
            raise GitRepositoryError(f"Git symlink entries are prohibited: {path}")
        if mode == "160000" or entry_type == "commit":
            raise GitRepositoryError(f"Git submodule entries are prohibited: {path}")
        if entry_type != "blob" or mode not in {"100644", "100755"}:
            raise GitRepositoryError(f"authority entry must be a regular Git blob: {path}")
        size_result = self._run("cat-file", "-s", object_id)
        try:
            size = int(size_result.stdout.strip())
        except ValueError as exc:
            raise GitRepositoryError(f"Git returned an invalid object size for {path}") from exc
        if size > maximum_bytes:
            raise GitRepositoryError(f"Git blob exceeds {maximum_bytes} bytes: {path}")
        content = self._run("cat-file", "blob", object_id).stdout
        if len(content) != size or len(content) > maximum_bytes:
            raise GitRepositoryError(f"Git blob size changed while reading: {path}")
        return GitBlob(path, object_id, content)

    def branch_contains(self, branch: str, commit: str) -> bool:
        ref = f"refs/heads/{branch}"
        exists = self._run("show-ref", "--verify", "--quiet", ref, check=False)
        if exists.returncode == 1:
            return False
        if exists.returncode != 0:
            raise GitRepositoryError(f"cannot inspect default branch ref: {branch}")
        contains = self._run("merge-base", "--is-ancestor", commit, ref, check=False)
        if contains.returncode == 0:
            return True
        if contains.returncode == 1:
            return False
        raise GitRepositoryError(f"cannot test commit containment for branch: {branch}")

    def _run(self, *arguments: str, check: bool = True) -> subprocess.CompletedProcess[bytes]:
        environment = os.environ.copy()
        environment.update(
            {
                "GIT_CONFIG_NOSYSTEM": "1",
                "GIT_CONFIG_GLOBAL": os.devnull,
                "GIT_TERMINAL_PROMPT": "0",
                "GIT_OPTIONAL_LOCKS": "0",
                "GIT_LITERAL_PATHSPECS": "1",
            }
        )
        result = subprocess.run(
            ["git", "--no-pager", "-C", str(self.path), *arguments],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=environment,
            check=False,
        )
        if check and result.returncode != 0:
            message = result.stderr.decode("utf-8", errors="replace").strip()
            raise GitRepositoryError(f"read-only Git command failed: {message}")
        return result
