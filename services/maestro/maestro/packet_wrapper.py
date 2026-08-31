"""The single Alpha `maestro run-packet` synthetic lifecycle wrapper."""

from __future__ import annotations

import json
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path

from .config import RuntimeConfig
from .lifecycle import LifecycleDecision, SyntheticWorkerResult, grade_result
from .packet_contract import ApprovedPacket, _ALPHA03_SCENARIOS
from .storage import SQLiteFoundation
from .synthetic_discovery import (
    build_inventory,
    build_proposed_binding,
    compute_fixture_digest,
    load_and_validate_discovery_fixture,
    validate_discovery_fixture_name,
)

MAX_CAPTURED_LOG_BYTES = 2048


@dataclass(frozen=True)
class RunPacketResult:
    """Local command result that reports facts and never performs a next action."""

    packet_id: str
    status: str
    handoff_kind: str | None
    launched: bool
    worktree_path: str | None

    def as_json(self) -> str:
        return json.dumps(asdict(self), sort_keys=True)


class SyntheticLocalExecutor:
    """Controlled local fixture executor; it never invokes a model or subprocess."""

    def execute(self, packet: ApprovedPacket, worktree_path: Path) -> SyntheticWorkerResult:
        result = _scenario_result(packet)
        if worktree_path:
            (worktree_path / "synthetic-worker-result.json").write_text(
                json.dumps(_result_evidence(result), sort_keys=True), encoding="utf-8"
            )
        return result


class PacketWrapper:
    """Validate, claim, run once, grade, hand off, and stop for one packet key."""

    def __init__(self, config: RuntimeConfig, executor: SyntheticLocalExecutor | None = None) -> None:
        self.config = RuntimeConfig(config.runtime_dir)
        self.storage = SQLiteFoundation(self.config)
        self.executor = executor or SyntheticLocalExecutor()

    def run(self, packet_path: str | Path) -> RunPacketResult:
        # This deliberately precedes storage construction/claiming/worktree creation.
        packet = ApprovedPacket.from_file(packet_path)

        # Validate discovery fixture before claim for discovery scenarios.
        if packet.is_discovery and packet.discovery_fixture:
            validate_discovery_fixture_name(packet.discovery_fixture)
            load_and_validate_discovery_fixture(packet.discovery_fixture)

        claim = self.storage.claim_packet(packet.packet_id, packet.as_evidence())
        if not claim.claimed:
            return RunPacketResult(packet.packet_id, claim.status, None, False, claim.worktree_path)

        worktree_path = self._create_fixture_worktree(packet.packet_id)
        started = self.storage.start_packet(
            packet.packet_id,
            str(worktree_path),
            {"worktree_path": str(worktree_path), "executor": packet.executor_kind, "event": "synthetic worker started"},
        )
        if not started.claimed:
            return RunPacketResult(packet.packet_id, started.status, None, False, started.worktree_path)

        worker_result = self.executor.execute(packet, worktree_path)
        decision = grade_result(packet, worker_result)

        # Record discovery-specific evidence (inventory, binding, digest).
        if packet.is_discovery and worker_result.inventory:
            self.storage.record_discovery_evidence(
                packet.packet_id,
                worker_result.inventory,
                worker_result.proposed_binding,
                worker_result.fixture_digest,
            )

        completed = self.storage.finish_packet(
            packet.packet_id,
            decision.status,
            decision.handoff_kind,
            decision.reason,
            _result_evidence(worker_result),
        )
        return RunPacketResult(
            packet.packet_id,
            completed.status,
            decision.handoff_kind,
            completed.claimed,
            completed.worktree_path,
        )

    def _create_fixture_worktree(self, packet_id: str) -> Path:
        # This is an isolated fixture directory, not a real project checkout or Git worktree.
        self.config.ensure_runtime_dir()
        root = self.config.runtime_dir / "packet-worktrees"
        root.mkdir(mode=0o700, exist_ok=True)
        return Path(tempfile.mkdtemp(prefix=f"{packet_id}-", dir=root))


def _scenario_result(packet: ApprovedPacket) -> SyntheticWorkerResult:
    """Return only explicit fixture cases, so no arbitrary command is ever executed."""
    successful_paths = ("synthetic-output/result.txt",)
    successful_gates = {gate.name: True for gate in packet.gates}
    scenario = packet.scenario

    # Discovery scenarios process fixture data.
    if scenario in _ALPHA03_SCENARIOS:
        return _discovery_result(packet)

    if scenario == "success":
        return SyntheticWorkerResult(0, "synthetic-commit-alpha-02", successful_paths, successful_gates, (), "synthetic success")
    if scenario == "gate-failure":
        gates = dict(successful_gates)
        gates[packet.gates[0].name] = False
        return SyntheticWorkerResult(1, "synthetic-commit-alpha-02", successful_paths, gates, (), "named gate failed")
    if scenario == "missing-commit":
        return SyntheticWorkerResult(1, None, successful_paths, successful_gates, (), "commit fact missing")
    if scenario == "missing-diff":
        return SyntheticWorkerResult(1, "synthetic-commit-alpha-02", (), successful_gates, (), "scoped diff missing")
    if scenario == "out-of-scope":
        return SyntheticWorkerResult(1, "synthetic-commit-alpha-02", ("outside/result.txt",), successful_gates, (), "scope violation")
    if scenario in {"dependency-violation", "configuration-violation", "placeholder-violation"}:
        return SyntheticWorkerResult(
            1,
            "synthetic-commit-alpha-02",
            successful_paths,
            successful_gates,
            (f"unapproved {scenario.removesuffix('-violation')}",),
            f"{scenario.removesuffix('-violation')} violation",
        )
    raise ValueError(f"Unsupported synthetic fixture scenario: {scenario}")


def _discovery_result(packet: ApprovedPacket) -> SyntheticWorkerResult:
    """Process discovery fixture and produce inventory, binding, digest."""
    from .synthetic_discovery import build_escalation_reason

    fixture_name = packet.discovery_fixture
    if fixture_name is None:
        return SyntheticWorkerResult(1, None, (), {}, (), "no discovery fixture", None, None, None)

    data = load_and_validate_discovery_fixture(fixture_name)
    inventory = build_inventory(data)
    proposed_binding = build_proposed_binding(data)
    digest = compute_fixture_digest(fixture_name)
    escalation_reason = build_escalation_reason(data)

    log = "complete discovery inventory produced" if proposed_binding else (escalation_reason or "incomplete discovery")
    return SyntheticWorkerResult(
        exit_code=0 if proposed_binding else 1,
        commit="synthetic-discovery-alpha-03",
        scoped_diff=(),
        gate_results={},
        violations=(),
        log=log,
        inventory=inventory,
        proposed_binding=proposed_binding,
        fixture_digest=digest,
    )


def _result_evidence(result: SyntheticWorkerResult) -> dict[str, object]:
    """Persist bounded structured facts rather than worker prose or external artifacts."""
    evidence = {
        "exit_code": result.exit_code,
        "commit": result.commit,
        "scoped_diff": list(result.scoped_diff),
        "gate_results": dict(result.gate_results),
        "violations": list(result.violations),
        "log": result.log.encode("utf-8")[:MAX_CAPTURED_LOG_BYTES].decode("utf-8", errors="ignore"),
    }
    if result.inventory is not None:
        evidence["inventory"] = result.inventory
    if result.proposed_binding is not None:
        evidence["proposed_binding"] = result.proposed_binding
    if result.fixture_digest is not None:
        evidence["fixture_digest"] = result.fixture_digest
    return evidence
