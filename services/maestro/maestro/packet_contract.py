"""Validation for Alpha-02's local, synthetic packet format."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


_PACKET_ID = re.compile(r"^[a-z][a-z0-9-]{2,63}$")
_SYNTHETIC_EXECUTORS = {"synthetic-local"}
_DISCOVERY_SCENARIOS = frozenset({
    "discovery-complete",
    "discovery-missing",
    "discovery-conflicting",
})
_LEGACY_SCENARIOS = frozenset({
    "success",
    "gate-failure",
    "missing-commit",
    "missing-diff",
    "out-of-scope",
    "dependency-violation",
    "configuration-violation",
    "placeholder-violation",
})
_SYNTHETIC_SCENARIOS = _DISCOVERY_SCENARIOS | _LEGACY_SCENARIOS


class PacketValidationError(ValueError):
    """Raised before a packet can claim runtime state or launch a fixture."""


@dataclass(frozen=True)
class ValidationGate:
    """One named, declarative synthetic validation gate."""

    name: str
    command: str


@dataclass(frozen=True)
class ApprovedPacket:
    """The deliberately small packet authority required by the wrapper."""

    packet_id: str
    title: str
    approval_reference: str
    fidelity_reference: str
    owned_paths: tuple[str, ...]
    gates: tuple[ValidationGate, ...]
    executor_kind: str
    scenario: str
    discovery_fixture: str | None
    independent_review_route: str
    owner_stop_boundary: str

    @classmethod
    def from_file(cls, packet_path: str | Path) -> "ApprovedPacket":
        try:
            payload = json.loads(Path(packet_path).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise PacketValidationError(f"Cannot read local synthetic packet: {error}") from error
        return cls.from_mapping(payload)

    @classmethod
    def from_mapping(cls, payload: Any) -> "ApprovedPacket":
        if not isinstance(payload, dict):
            raise PacketValidationError("Packet must be a JSON object")

        packet_id = _required_text(payload, "packet_id")
        if not _PACKET_ID.fullmatch(packet_id):
            raise PacketValidationError("packet_id must be a stable lowercase identifier")
        title = _required_text(payload, "title")
        if len(title) > 160:
            raise PacketValidationError("title must be concise (160 characters or fewer)")

        authority = _required_mapping(payload, "authority")
        approval_reference = _required_text(authority, "approval_reference")
        fidelity_reference = _required_text(authority, "fidelity_reference")
        owned_paths = _owned_paths(payload.get("owned_paths"))
        gates = _gates(payload.get("gates"))

        executor = _required_mapping(payload, "executor")
        executor_kind = _required_text(executor, "kind")
        if executor_kind not in _SYNTHETIC_EXECUTORS:
            raise PacketValidationError("executor.kind must be the permitted synthetic-local executor")
        scenario = _required_text(executor, "scenario")
        if scenario not in _SYNTHETIC_SCENARIOS:
            raise PacketValidationError("executor.scenario must be a supported synthetic fixture case")
        discovery_fixture = _safe_fixture_basename(payload.get("discovery_fixture"))
        _enforce_discovery_pairing(scenario, discovery_fixture)

        return cls(
            packet_id=packet_id,
            title=title,
            approval_reference=approval_reference,
            fidelity_reference=fidelity_reference,
            owned_paths=owned_paths,
            gates=gates,
            executor_kind=executor_kind,
            scenario=scenario,
            discovery_fixture=discovery_fixture,
            independent_review_route=_required_text(payload, "independent_review_route"),
            owner_stop_boundary=_required_text(payload, "owner_stop_boundary"),
        )

    def as_evidence(self) -> dict[str, object]:
        """Return local authority facts suitable for durable SQLite evidence."""
        result: dict[str, object] = {
            "packet_id": self.packet_id,
            "title": self.title,
            "approval_reference": self.approval_reference,
            "fidelity_reference": self.fidelity_reference,
            "owned_paths": list(self.owned_paths),
            "gates": [{"name": gate.name, "command": gate.command} for gate in self.gates],
            "executor_kind": self.executor_kind,
            "scenario": self.scenario,
            "independent_review_route": self.independent_review_route,
            "owner_stop_boundary": self.owner_stop_boundary,
        }
        if self.discovery_fixture is not None:
            result["discovery_fixture"] = self.discovery_fixture
        return result


def _required_mapping(payload: dict[str, Any], field: str) -> dict[str, Any]:
    value = payload.get(field)
    if not isinstance(value, dict):
        raise PacketValidationError(f"Packet requires {field}")
    return value


def _required_text(payload: dict[str, Any], field: str) -> str:
    value = payload.get(field)
    if not isinstance(value, str) or not value.strip():
        raise PacketValidationError(f"Packet requires non-empty {field}")
    return value.strip()


def _owned_paths(value: Any) -> tuple[str, ...]:
    if not isinstance(value, list) or not value:
        raise PacketValidationError("Packet requires declared owned_paths")
    paths: list[str] = []
    for path in value:
        if not isinstance(path, str) or not path.strip() or path.startswith("/") or ".." in Path(path).parts:
            raise PacketValidationError("owned_paths must contain safe relative paths")
        paths.append(path.strip().rstrip("/"))
    return tuple(paths)


def _gates(value: Any) -> tuple[ValidationGate, ...]:
    if not isinstance(value, list) or not value:
        raise PacketValidationError("Packet requires named validation gates")
    gates: list[ValidationGate] = []
    names: set[str] = set()
    for gate in value:
        if not isinstance(gate, dict):
            raise PacketValidationError("Each gate must be an object")
        name = _required_text(gate, "name")
        if name in names:
            raise PacketValidationError("Gate names must be unique")
        names.add(name)
        gates.append(ValidationGate(name=name, command=_required_text(gate, "command")))
    return tuple(gates)


def _safe_fixture_basename(value: Any) -> str | None:
    """Validate and return a safe JSON basename for the discovery fixture, or None."""
    if value is None:
        return None
    if not isinstance(value, str):
        raise PacketValidationError("discovery_fixture must be a string or absent")
    trimmed = value.strip()
    if not trimmed:
        raise PacketValidationError("discovery_fixture must not be empty")
    if trimmed.startswith("/") or "\\" in trimmed or "/" in trimmed:
        raise PacketValidationError("discovery_fixture must be a plain basename")
    if trimmed in (".", ".."):
        raise PacketValidationError("discovery_fixture must not be '.' or '..'")
    if not trimmed.endswith(".json"):
        raise PacketValidationError("discovery_fixture must end with .json")
    return trimmed


def _enforce_discovery_pairing(scenario: str, discovery_fixture: str | None) -> None:
    """Discovery scenarios require a discovery_fixture; legacy scenarios reject one."""
    if scenario in _DISCOVERY_SCENARIOS:
        if discovery_fixture is None:
            raise PacketValidationError(
                f"Scenario {scenario!r} requires a discovery_fixture"
            )
    elif scenario in _LEGACY_SCENARIOS:
        if discovery_fixture is not None:
            raise PacketValidationError(
                f"Legacy scenario {scenario!r} must not carry a discovery_fixture"
            )
