"""Explicit local-runtime configuration for the Alpha-01 foundation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_RUNTIME_DIR = REPOSITORY_ROOT / "var"
DATABASE_NAME = "maestro.sqlite3"


@dataclass(frozen=True)
class RuntimeConfig:
    """Paths owned by Maestro's local runtime, never by a joined project."""

    runtime_dir: Path

    @classmethod
    def from_runtime_dir(cls, runtime_dir: str | Path | None = None) -> "RuntimeConfig":
        chosen = DEFAULT_RUNTIME_DIR if runtime_dir is None else Path(runtime_dir)
        return cls(chosen.expanduser().resolve())

    @property
    def database_path(self) -> Path:
        return self.runtime_dir / DATABASE_NAME

    def ensure_runtime_dir(self) -> None:
        self.runtime_dir.mkdir(parents=True, exist_ok=True)
