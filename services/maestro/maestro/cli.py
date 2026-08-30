"""Command line interface for the Alpha-01 local foundation only."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .config import RuntimeConfig
from .storage import SQLiteFoundation


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="maestro", description="Maestro Alpha-01 local foundation")
    commands = parser.add_subparsers(dest="command", required=True)
    health = commands.add_parser("health", help="verify local SQLite readiness")
    health.add_argument("--runtime-dir", type=Path, default=None, help="local directory for the SQLite database")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command != "health":  # Defensive guard for future commands outside Alpha-01.
        raise ValueError(f"Unsupported Alpha-01 command: {args.command}")

    result = SQLiteFoundation(RuntimeConfig.from_runtime_dir(args.runtime_dir)).health()
    print(
        json.dumps(
            {
                "status": "ready",
                "database_path": result.database_path,
                "schema_version": result.schema_version,
                "journal_mode": result.journal_mode,
                "foreign_keys_enabled": result.foreign_keys_enabled,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
