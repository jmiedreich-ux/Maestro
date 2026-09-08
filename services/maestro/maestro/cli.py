"""Local-only CLI for the Alpha foundation and its synthetic packet wrapper."""

from __future__ import annotations

import argparse
import json
import signal
import sys
from pathlib import Path

from .config import RuntimeConfig
from .development_manager import run_cycle
from .dispatch_orchestrator import now_iso
from .operational_state import Actor, OperationalStateStore
from .packet_wrapper import PacketWrapper
from .read_api import ReadApiBindError, ReadApiConfig, ReadApiServer, canonical_response_json
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
    serve_read_api = commands.add_parser("serve-read-api", help="run the loopback-only Atlas read API scaffold")
    serve_read_api.add_argument("--host", default="127.0.0.1", help="loopback host to bind")
    serve_read_api.add_argument("--port", type=int, default=8765, help="port to bind (0 for an OS-assigned ephemeral port)")
    dev_manager = commands.add_parser(
        "development-manager-loop",
        help="run the real M4 driver: recovery, review, acceptance, merge, notification -- one cycle, repeatedly",
    )
    dev_manager.add_argument("--run-id", required=True, help="real run_id whose packets this cycle drives")
    dev_manager.add_argument("--repository", type=Path, required=True, help="real local git worktree for this run")
    dev_manager.add_argument("--default-branch", default="main", help="real default branch to merge into")
    dev_manager.add_argument(
        "--reconstruction-command", action="append", dest="reconstruction_commands", required=True,
        help="real shell command run to reconstruct coverage (repeatable, at least one required)",
    )
    dev_manager.add_argument("--runtime-dir", type=Path, default=None, help="local directory for the SQLite database")
    dev_manager.add_argument("--actor-id", default="development-manager-loop", help="real actor_id recorded on every command this cycle issues")
    dev_manager.add_argument(
        "--interval-seconds", type=float, default=None,
        help="if set, run continuously, sleeping this many real seconds between cycles; omit to run exactly one cycle and exit",
    )
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
    if args.command == "serve-read-api":
        return _serve_read_api(args.host, args.port)
    if args.command == "development-manager-loop":
        return _development_manager_loop(args)
    raise ValueError(f"Unsupported Maestro command: {args.command}")


def _development_manager_loop(args: argparse.Namespace) -> int:
    config = RuntimeConfig.from_runtime_dir(args.runtime_dir)
    store = OperationalStateStore(config)
    actor = Actor("MaestroDeveloper", args.actor_id, "development-manager-loop")
    repository_path = str(args.repository)

    def cycle() -> None:
        report = run_cycle(
            store, config, repository_path=repository_path, run_id=args.run_id,
            default_branch=args.default_branch, actor=actor, now=now_iso(),
            reconstruction_commands=args.reconstruction_commands,
        )
        print(
            json.dumps(
                {
                    "timed_out": report.timed_out, "redispatched": report.redispatched,
                    "reviewed": report.reviewed, "accepted": report.accepted,
                    "merged": report.merged, "notifications_delivered": report.notifications_delivered,
                },
                sort_keys=True,
            )
        )

    if args.interval_seconds is None:
        cycle()
        return 0

    stop = {"requested": False}

    def _handle_stop(signum, frame):
        stop["requested"] = True

    signal.signal(signal.SIGINT, _handle_stop)
    signal.signal(signal.SIGTERM, _handle_stop)
    while not stop["requested"]:
        cycle()
        _sleep(args.interval_seconds, stop)
    return 0


def _sleep(seconds: float, stop: dict) -> None:
    import time

    deadline = time.monotonic() + seconds
    while not stop["requested"] and time.monotonic() < deadline:
        time.sleep(min(1.0, deadline - time.monotonic()))


def _serve_read_api(host: str, port: int) -> int:
    try:
        config = ReadApiConfig(host=host, port=port)
    except ReadApiBindError as error:
        sys.stderr.buffer.write(
            canonical_response_json({"error": "invalid_host", "detail": str(error)}) + b"\n"
        )
        return 2
    server = ReadApiServer(config)
    server.start()
    sys.stdout.buffer.write(
        canonical_response_json({"host": config.host, "port": server.bound_port, "status": "listening"}) + b"\n"
    )
    sys.stdout.flush()

    def _handle_sigint(signum, frame) -> None:
        server.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, _handle_sigint)
    server.wait_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
