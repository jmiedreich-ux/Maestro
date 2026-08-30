"""Explicit local-runtime configuration for the Alpha-01 foundation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_RUNTIME_DIR = REPOSITORY_ROOT / "var"
DATABASE_NAME = "maestro.sqlite3"


class RuntimePathError(ValueError):
    """Raised before any mutation when a runtime path is outside repository var/."""


def validate_runtime_dir(runtime_dir: str | Path) -> Path:
    """Resolve and constrain a runtime path before any caller can mutate it."""
    resolved = Path(runtime_dir).expanduser().resolve()
    runtime_root = DEFAULT_RUNTIME_DIR.resolve()
    try:
        resolved.relative_to(runtime_root)
    except ValueError as error:
        raise RuntimePathError(f"Runtime directory must be inside {runtime_root}") from error
    return resolved


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
        self.runtime_dir.mkdir(parents=True, exist_ok=True)
