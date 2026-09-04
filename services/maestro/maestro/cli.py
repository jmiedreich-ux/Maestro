"""Local-only CLI for the Alpha foundation and its synthetic packet wrapper."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .config import RuntimeConfig
from .packet_wrapper import PacketWrapper
from .review_readiness import (
    canonical_json,
    evaluate_review_readiness,
    malformed_request_result,
    result_exit_code,
)
from .storage import SQLiteFoundation


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="maestro", description="Maestro Alpha local synthetic operations")
    commands = parser.add_subparsers(dest="command", required=True)
    health = commands.add_parser("health", help="verify local SQLite readiness")
    health.add_argument("--runtime-dir", type=Path, default=None, help="local directory for the SQLite database")
    run_packet = commands.add_parser("run-packet", help="run one approved synthetic packet and stop")
    run_packet.add_argument("--packet", type=Path, required=True, help="local approved synthetic packet JSON")
    run_packet.add_argument("--runtime-dir", type=Path, default=None, help="local directory for SQLite and fixture evidence")
    readiness = commands.add_parser("review-readiness", help="prove an immutable candidate is ready for review")
    readiness.add_argument("--request", type=Path, required=True, help="closed local review-readiness request JSON")
    return parser


def main() -> int:
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
        return 0
    if args.command == "run-packet":
        print(PacketWrapper(RuntimeConfig.from_runtime_dir(args.runtime_dir)).run(args.packet).as_json())
        return 0
    if args.command == "review-readiness":
        try:
            request_bytes = args.request.read_bytes()
        except OSError as error:
            result = malformed_request_result(
                b"", f"cannot read request file: {type(error).__name__}: {error}"
            )
        else:
            result = evaluate_review_readiness(request_bytes)
        sys.stdout.buffer.write(canonical_json(result))
        return result_exit_code(result)
    raise ValueError(f"Unsupported Maestro command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
