"""Local-only CLI for the Alpha foundation and its synthetic packet wrapper."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .config import RuntimeConfig
from .packet_wrapper import PacketWrapper
from .storage import SQLiteFoundation


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="maestro", description="Maestro Alpha local synthetic operations")
    commands = parser.add_subparsers(dest="command", required=True)
    health = commands.add_parser("health", help="verify local SQLite readiness")
    health.add_argument("--runtime-dir", type=Path, default=None, help="local directory for the SQLite database")
    run_packet = commands.add_parser("run-packet", help="run one approved synthetic packet and stop")
    run_packet.add_argument("--packet", type=Path, required=True, help="local approved synthetic packet JSON")
    run_packet.add_argument("--runtime-dir", type=Path, default=None, help="local directory for SQLite and fixture evidence")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "health":
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
        return
    if args.command == "run-packet":
        print(PacketWrapper(RuntimeConfig.from_runtime_dir(args.runtime_dir)).run(args.packet).as_json())
        return
    raise ValueError(f"Unsupported Maestro command: {args.command}")


if __name__ == "__main__":
    main()
