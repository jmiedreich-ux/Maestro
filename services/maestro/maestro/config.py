"""Explicit local-runtime configuration for the Alpha-01 foundation."""

from __future__ import annotations

import errno
import os
import stat
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_RUNTIME_DIR = REPOSITORY_ROOT / "var"
DATABASE_NAME = "maestro.sqlite3"


class RuntimePathError(ValueError):
    """Raised before any mutation when a runtime path is outside repository var/."""


def validate_runtime_dir(runtime_dir: str | Path) -> Path:
    """Resolve and constrain a runtime path before any caller can mutate it."""
    resolved = Path(os.path.abspath(os.fspath(Path(runtime_dir).expanduser())))
    runtime_root = DEFAULT_RUNTIME_DIR.resolve()
    try:
        relative_parts = resolved.relative_to(runtime_root).parts
    except ValueError as error:
        raise RuntimePathError(f"Runtime directory must be inside {runtime_root}") from error
    _reject_existing_symlink_components(runtime_root, relative_parts)
    return resolved


def _reject_existing_symlink_components(runtime_root: Path, relative_parts: tuple[str, ...]) -> None:
    """Reject any extant link before a configuration object is accepted."""
    try:
        root_status = os.lstat(runtime_root)
    except FileNotFoundError as error:
        raise RuntimePathError(f"Physical runtime root is missing: {runtime_root}") from error
    if stat.S_ISLNK(root_status.st_mode) or not stat.S_ISDIR(root_status.st_mode):
        raise RuntimePathError(f"Physical runtime root is not a directory: {runtime_root}")

    current = runtime_root
    for part in relative_parts:
        current = current / part
        try:
            component_status = os.lstat(current)
        except FileNotFoundError:
            return
        if stat.S_ISLNK(component_status.st_mode):
            raise RuntimePathError(f"Runtime directory contains a symlinked component: {current}")
        if not stat.S_ISDIR(component_status.st_mode):
            raise RuntimePathError(f"Runtime directory component is not a directory: {current}")


@dataclass(frozen=True)
class RuntimeConfig:
    """Paths owned by Maestro's local runtime, never by a joined project."""

    runtime_dir: Path

    def __post_init__(self) -> None:
        object.__setattr__(self, "runtime_dir", validate_runtime_dir(self.runtime_dir))

    @classmethod
    def from_runtime_dir(cls, runtime_dir: str | Path | None = None) -> "RuntimeConfig":
        chosen = DEFAULT_RUNTIME_DIR if runtime_dir is None else Path(runtime_dir)
        return cls(chosen)

    @property
    def database_path(self) -> Path:
        return self.runtime_dir / DATABASE_NAME

    def ensure_runtime_dir(self) -> None:
        with self.open_runtime_dir_fd():
            return

    @contextmanager
    def open_runtime_dir_fd(self) -> Iterator[int]:
        """Open/create only non-symlink components beneath the physical var root."""
        # Revalidate immediately before the mutation boundary. The descriptor
        # walk below is the race-resistant enforcement mechanism on Linux.
        validated = RuntimeConfig(self.runtime_dir)
        runtime_root = DEFAULT_RUNTIME_DIR.resolve()
        relative_parts = validated.runtime_dir.relative_to(runtime_root).parts
        current_fd = _open_directory(runtime_root)
        try:
            for part in relative_parts:
                child_fd = _open_or_create_directory(current_fd, part)
                os.close(current_fd)
                current_fd = child_fd
            yield current_fd
        finally:
            os.close(current_fd)


_DIRECTORY_FLAGS = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)


def _open_directory(path: Path) -> int:
    try:
        return os.open(path, _DIRECTORY_FLAGS)
    except OSError as error:
        raise RuntimePathError(f"Cannot open physical runtime directory: {path}") from error


def _open_or_create_directory(parent_fd: int, component: str) -> int:
    """Use openat/mkdirat semantics so a component swap cannot escape var/."""
    while True:
        try:
            return os.open(component, _DIRECTORY_FLAGS, dir_fd=parent_fd)
        except FileNotFoundError:
            try:
                os.mkdir(component, mode=0o700, dir_fd=parent_fd)
            except FileExistsError:
                continue
        except OSError as error:
            if error.errno in (errno.ELOOP, errno.ENOTDIR):
                raise RuntimePathError(f"Runtime directory component is unsafe: {component}") from error
            raise RuntimePathError(f"Cannot create runtime directory component: {component}") from error
