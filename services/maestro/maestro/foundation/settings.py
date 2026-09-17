"""Validated settings for Maestro's service-owned SQLite database."""

from __future__ import annotations

import os
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping


DEFAULT_DATABASE_PATH = Path("/var/lib/maestro/maestro.sqlite3")


class StorageConfigurationError(ValueError):
    """Raised when configured storage cannot safely identify one local file."""


@dataclass(frozen=True)
class StorageSettings:
    """The installed storage selection accepted by the Maestro service."""

    engine: str = "sqlite"
    path: Path = DEFAULT_DATABASE_PATH

    def __post_init__(self) -> None:
        if self.engine != "sqlite":
            raise StorageConfigurationError("storage.engine must be sqlite")

        raw_path = os.fspath(self.path)
        if not isinstance(raw_path, str) or not raw_path:
            raise StorageConfigurationError("storage.path must be a nonempty filesystem path")
        if "\x00" in raw_path:
            raise StorageConfigurationError("storage.path contains a null byte")
        if raw_path == ":memory:" or raw_path.startswith("file:"):
            raise StorageConfigurationError("in-memory and URI SQLite storage are unsupported")

        normalized = Path(raw_path)
        if not normalized.is_absolute():
            raise StorageConfigurationError("storage.path must be absolute")
        object.__setattr__(self, "path", normalized)

    @classmethod
    def from_mapping(cls, value: Mapping[str, object]) -> "StorageSettings":
        """Build settings from the closed ``storage`` configuration table."""
        if not isinstance(value, Mapping):
            raise StorageConfigurationError("storage settings must be a table")
        unknown = set(value) - {"engine", "path"}
        if unknown:
            raise StorageConfigurationError(
                f"unsupported storage setting(s): {', '.join(sorted(unknown))}"
            )
        engine = value.get("engine", "sqlite")
        path = value.get("path", DEFAULT_DATABASE_PATH)
        if not isinstance(engine, str) or not isinstance(path, (str, os.PathLike)):
            raise StorageConfigurationError("storage.engine and storage.path must be text")
        return cls(engine=engine, path=Path(path))

    def validate_host_path(self) -> None:
        """Reject unavailable or link-mediated installed paths before SQLite opens."""
        parent = self.path.parent
        if not parent.exists() or not parent.is_dir():
            raise StorageConfigurationError(
                f"storage directory does not exist or is not a directory: {parent}"
            )

        current = Path(self.path.anchor)
        for component in self.path.parts[1:]:
            current /= component
            try:
                status = os.lstat(current)
            except FileNotFoundError:
                break
            if stat.S_ISLNK(status.st_mode):
                raise StorageConfigurationError(
                    f"storage.path contains a symbolic link: {current}"
                )

        if self.path.exists():
            status = os.lstat(self.path)
            if not stat.S_ISREG(status.st_mode):
                raise StorageConfigurationError("storage.path must identify a regular file")
