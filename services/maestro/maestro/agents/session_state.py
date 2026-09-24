"""Saved tool conversation state for persistent architect sessions.

Each run works in a fresh isolated home. A persistent session keeps only the
tool's own conversation history in a service-owned directory: it is copied into
the next run's home before launch and copied back after the run ends. The
history is untrusted memory, never an authoritative record.
"""

from __future__ import annotations

import os
import re
import shutil
from dataclasses import dataclass
from pathlib import Path

# Where each supported tool keeps conversations, relative to its home.
_HISTORY = {"codex": ".codex/sessions", "claude_code": ".claude/projects"}


@dataclass(frozen=True)
class SessionUse:
    """The persistent conversation a run belongs to."""

    session_id: str  # the service's session identity
    state_dir: Path  # service-owned saved history for this session
    provider_session_id: str | None  # the tool's conversation to resume; None on the first run
    assigned_provider_id: str | None = None  # first-run id the service gives a tool that accepts one

    def as_dict(self) -> dict[str, str | None]:
        return {
            "session_id": self.session_id, "state_dir": str(self.state_dir),
            "provider_session_id": self.provider_session_id, "assigned_provider_id": self.assigned_provider_id,
        }

    @classmethod
    def from_dict(cls, value: dict[str, str | None]) -> "SessionUse":
        return cls(str(value["session_id"]), Path(str(value["state_dir"])), value["provider_session_id"], value["assigned_provider_id"])


def project_key(cwd: Path | str) -> str:
    """Claude Code names a project's history directory after its working directory."""
    return re.sub(r"[^A-Za-z0-9]", "-", str(cwd))


def seed(tool: str, session: SessionUse, home: Path, cwd: Path) -> bool:
    """Put the saved history where the tool will look for it. Returns whether anything was restored."""
    relative = _HISTORY.get(tool)
    saved = session.state_dir / "history"
    if relative is None or not saved.is_dir():
        return False
    target = home / relative
    if tool == "claude_code":
        # The run's working directory differs each time, so re-key every saved conversation to it.
        target = target / project_key(cwd)
        source = next((p for p in sorted(saved.iterdir()) if p.is_dir()), None)
        if source is None:
            return False
        saved = source
    _copy_tree(saved, target)
    return True


def harvest(tool: str, session: SessionUse, home: Path) -> bool:
    """Save the run's conversation history for the next run. Returns whether anything was saved."""
    relative = _HISTORY.get(tool)
    if relative is None:
        return False
    source = home / relative
    if not source.is_dir() or source.is_symlink():
        return False
    saved = session.state_dir / "history"
    if tool == "claude_code":
        projects = [p for p in sorted(source.iterdir()) if p.is_dir() and not p.is_symlink()]
        if not projects:
            return False
        saved = saved / "project"
        _copy_tree(projects[0], saved)
        return True
    _copy_tree(source, saved)
    return True


def _copy_tree(source: Path, target: Path) -> None:
    """Copy regular files only; the tool's state is data, so links and special files are ignored."""
    for base, directories, files in os.walk(source, followlinks=False):
        relative = Path(base).relative_to(source)
        directories[:] = [d for d in directories if not (Path(base) / d).is_symlink()]
        destination = target / relative
        destination.mkdir(parents=True, exist_ok=True, mode=0o707)
        os.chmod(destination, 0o707)
        for name in files:
            path = Path(base) / name
            if path.is_symlink() or not path.is_file():
                continue
            copy = destination / name
            shutil.copyfile(path, copy)
            os.chmod(copy, 0o606)
