"""Bounded, side-effect-free observations of a remote Git branch."""

from __future__ import annotations

import os
import re
import subprocess
import tempfile
from dataclasses import dataclass
from typing import Callable, Mapping

from .credentials import validate_branch


class GitReadError(RuntimeError):
    """A remote Git observation could not be completed safely."""


_OBJECT_ID = re.compile(r"[0-9a-f]{40}\Z")


def validate_object_id(value: object, field: str = "object_id") -> str:
    if not isinstance(value, str) or _OBJECT_ID.fullmatch(value.lower()) is None:
        raise GitReadError(f"{field} must be one full lowercase SHA-1 object ID")
    return value.lower()


def validate_repository_path(value: object) -> str:
    if (
        not isinstance(value, str)
        or not value
        or value.startswith("/")
        or value.startswith(".git/")
        or value == ".git"
        or "\x00" in value
        or any(part in {"", ".", ".."} for part in value.split("/"))
    ):
        raise GitReadError("repository path must be a relative regular-file path")
    return value


@dataclass(frozen=True)
class RemoteSnapshot:
    """The one observed branch head and exact requested blob bytes."""

    branch: str
    head: str
    files: dict[str, bytes | None]


def _environment() -> dict[str, str]:
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
    return environment


def run_git(
    *arguments: str,
    cwd: str | None = None,
    environment: Mapping[str, str] | None = None,
) -> subprocess.CompletedProcess[bytes]:
    """Run one fixed Git argument array without prompts or ambient config."""
    result = subprocess.run(
        ["git", "--no-pager", *arguments],
        cwd=cwd,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=_environment() | ({} if environment is None else dict(environment)),
        check=False,
    )
    return result


class RemoteGitReader:
    """Reads named files at an observed remote branch head without a write operation."""

    def snapshot(
        self,
        remote: str,
        branch: str,
        paths: tuple[str, ...],
        *,
        command: Callable[..., subprocess.CompletedProcess[bytes]] = run_git,
    ) -> RemoteSnapshot:
        if not isinstance(remote, str) or not remote or "\x00" in remote:
            raise GitReadError("remote must be nonempty text")
        branch = validate_branch(branch)
        paths = tuple(validate_repository_path(path) for path in paths)
        if len(set(paths)) != len(paths):
            raise GitReadError("requested repository paths must be unique")
        reference = f"refs/heads/{branch}"
        listed = command("ls-remote", "--exit-code", remote, reference)
        if listed.returncode != 0:
            detail = listed.stderr.decode("utf-8", "replace").strip()
            raise GitReadError(f"cannot read remote branch {branch}: {detail or 'unavailable'}")
        try:
            head, returned_ref = listed.stdout.decode("ascii").strip().split("\t", 1)
            head = validate_object_id(head, "remote branch head")
        except (UnicodeDecodeError, ValueError) as error:
            raise GitReadError("remote returned an invalid branch head") from error
        if returned_ref != reference:
            raise GitReadError("remote returned an unexpected branch reference")

        with tempfile.TemporaryDirectory(prefix="maestro-git-read-") as temporary:
            initialized = command("init", "--bare", "--quiet", temporary)
            if initialized.returncode != 0:
                raise GitReadError("cannot prepare local Git reader")
            fetched = command("-C", temporary, "fetch", "--no-tags", "--quiet", remote, head)
            if fetched.returncode != 0:
                raise GitReadError("cannot fetch observed remote commit")
            files: dict[str, bytes | None] = {}
            for path in paths:
                shown = command("-C", temporary, "show", f"{head}:{path}")
                if shown.returncode == 0:
                    files[path] = shown.stdout
                    continue
                entry = command("-C", temporary, "ls-tree", "--name-only", head, "--", path)
                if entry.returncode == 0 and not entry.stdout:
                    files[path] = None
                    continue
                raise GitReadError(f"cannot read remote path {path}")
        return RemoteSnapshot(branch=branch, head=head, files=files)
