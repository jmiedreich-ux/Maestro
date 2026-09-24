"""Closed, immutable configuration for installed agent tool routes."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping


_REFERENCE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}\Z")
_HOST_LABEL = re.compile(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\Z")
_SUPPORTED_TOOLS = frozenset({"codex", "claude_code", "qwen"})
_TOOL_FIELDS = frozenset(
    {
        "executable",
        "credential_profile",
        "settings_profile",
        "allowed_model_ids",
        "permitted_destinations",
    }
)


class AgentRouteError(ValueError):
    """Typed configuration or selection rejection at the agent route boundary."""

    def __init__(self, code: str, message: str, **fields: object) -> None:
        super().__init__(message)
        self.code = code
        self.fields = dict(fields)


@dataclass(frozen=True)
class PermittedDestination:
    hostname: str
    port: int

    def __post_init__(self) -> None:
        hostname = _hostname(self.hostname)
        if (
            isinstance(self.port, bool)
            or not isinstance(self.port, int)
            or not 1 <= self.port <= 65535
        ):
            raise AgentRouteError(
                "invalid_configuration", "permitted destination port must be from 1 through 65535"
            )
        object.__setattr__(self, "hostname", hostname)

    def as_dict(self) -> dict[str, object]:
        return {"hostname": self.hostname, "port": self.port}


@dataclass(frozen=True)
class ToolModelSelection:
    tool: str
    model_id: str

    def __post_init__(self) -> None:
        if not isinstance(self.tool, str) or self.tool not in _SUPPORTED_TOOLS:
            raise AgentRouteError("unsupported_tool", f"agent tool is not supported: {self.tool}")
        _text(self.model_id, "model_id")


@dataclass(frozen=True)
class RoleSelections:
    architect: ToolModelSelection
    fidelity_reviewer: ToolModelSelection

    def __post_init__(self) -> None:
        if not isinstance(self.architect, ToolModelSelection):
            raise AgentRouteError("missing_selection", "architect tool and model selection is required")
        if not isinstance(self.fidelity_reviewer, ToolModelSelection):
            raise AgentRouteError(
                "missing_selection", "fidelity reviewer tool and model selection is required"
            )


@dataclass(frozen=True)
class RouteRequirements:
    capabilities: tuple[str, ...]
    allowed_locations: tuple[str, ...]
    minimum_context_tokens: int

    def __post_init__(self) -> None:
        capabilities = _unique_references(self.capabilities, "capability")
        locations = _unique_references(self.allowed_locations, "location")
        if not capabilities:
            raise AgentRouteError("invalid_requirements", "at least one capability is required")
        if not locations:
            raise AgentRouteError("invalid_requirements", "at least one location is required")
        if (
            isinstance(self.minimum_context_tokens, bool)
            or not isinstance(self.minimum_context_tokens, int)
            or self.minimum_context_tokens < 1
        ):
            raise AgentRouteError(
                "invalid_requirements", "minimum_context_tokens must be a positive integer"
            )
        object.__setattr__(self, "capabilities", capabilities)
        object.__setattr__(self, "allowed_locations", locations)


@dataclass(frozen=True)
class ToolRoute:
    tool: str
    executable: Path
    credential_profile: str
    settings_profile: str
    allowed_model_ids: tuple[str, ...]
    permitted_destinations: tuple[PermittedDestination, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.tool, str) or self.tool not in _SUPPORTED_TOOLS:
            raise AgentRouteError("unsupported_tool", f"agent tool is not supported: {self.tool}")
        if not isinstance(self.executable, Path) or not self.executable.is_absolute():
            raise AgentRouteError("invalid_configuration", "tool executable must be an absolute path")
        _reference(self.credential_profile, "credential_profile")
        _reference(self.settings_profile, "settings_profile")
        models = _unique_text(self.allowed_model_ids, "model_id")
        if not models:
            raise AgentRouteError("invalid_configuration", "allowed_model_ids cannot be empty")
        object.__setattr__(self, "allowed_model_ids", models)
        destinations = _destinations(self.permitted_destinations)
        object.__setattr__(self, "permitted_destinations", destinations)

    @property
    def executable_available(self) -> bool:
        return (
            self.executable.is_absolute()
            and self.executable.is_file()
            and os.access(self.executable, os.X_OK)
        )


class AgentRouteRegistry:
    """Parse the closed installed ``tools`` table and resolve exact selections."""

    def __init__(self, routes: Mapping[str, ToolRoute]) -> None:
        if not isinstance(routes, Mapping):
            raise AgentRouteError("invalid_configuration", "agent routes must be a table")
        unknown = set(routes) - _SUPPORTED_TOOLS
        if unknown:
            raise AgentRouteError(
                "unsupported_tool", f"agent tool is not supported: {sorted(unknown)[0]}"
            )
        for tool, route in routes.items():
            if not isinstance(route, ToolRoute) or route.tool != tool:
                raise AgentRouteError("invalid_configuration", "agent route identity differs")
        self._routes = dict(routes)

    @classmethod
    def from_mapping(cls, value: Mapping[str, object]) -> "AgentRouteRegistry":
        if not isinstance(value, Mapping):
            raise AgentRouteError("invalid_configuration", "tools configuration must be a table")
        routes: dict[str, ToolRoute] = {}
        for tool, raw in value.items():
            if tool not in _SUPPORTED_TOOLS:
                raise AgentRouteError("unsupported_tool", f"agent tool is not supported: {tool}")
            if not isinstance(raw, Mapping):
                raise AgentRouteError("invalid_configuration", f"tools.{tool} must be a table")
            unknown = set(raw) - _TOOL_FIELDS
            missing = _TOOL_FIELDS - set(raw)
            if unknown:
                raise AgentRouteError(
                    "unknown_field", f"unknown agent tool setting: tools.{tool}.{sorted(unknown)[0]}"
                )
            if missing:
                raise AgentRouteError(
                    "missing_field", f"missing agent tool setting: tools.{tool}.{sorted(missing)[0]}"
                )
            executable = raw["executable"]
            if not isinstance(executable, str) or not executable or not Path(executable).is_absolute():
                raise AgentRouteError(
                    "invalid_configuration", f"tools.{tool}.executable must be an absolute path"
                )
            credential = _reference(raw["credential_profile"], "credential_profile")
            settings = _reference(raw["settings_profile"], "settings_profile")
            model_ids = raw["allowed_model_ids"]
            if not isinstance(model_ids, list):
                raise AgentRouteError(
                    "invalid_configuration", f"tools.{tool}.allowed_model_ids must be a list"
                )
            normalized_models = _unique_text(model_ids, "model_id")
            if not normalized_models:
                raise AgentRouteError(
                    "invalid_configuration", f"tools.{tool}.allowed_model_ids cannot be empty"
                )
            raw_destinations = raw["permitted_destinations"]
            if not isinstance(raw_destinations, list):
                raise AgentRouteError(
                    "invalid_configuration",
                    f"tools.{tool}.permitted_destinations must be a list",
                )
            destinations: list[PermittedDestination] = []
            for destination in raw_destinations:
                if not isinstance(destination, Mapping) or set(destination) != {
                    "hostname",
                    "port",
                }:
                    raise AgentRouteError(
                        "invalid_configuration",
                        f"tools.{tool}.permitted_destinations entry is invalid",
                    )
                destinations.append(
                    PermittedDestination(destination["hostname"], destination["port"])
                )
            routes[tool] = ToolRoute(
                tool,
                Path(executable),
                credential,
                settings,
                normalized_models,
                tuple(destinations),
            )
        return cls(routes)

    def resolve(self, selection: ToolModelSelection) -> ToolRoute:
        if not isinstance(selection, ToolModelSelection):
            raise AgentRouteError("missing_selection", "explicit tool and model selection is required")
        route = self._routes.get(selection.tool)
        if route is None:
            raise AgentRouteError(
                "route_not_installed", f"selected agent tool is not installed: {selection.tool}"
            )
        if selection.model_id not in route.allowed_model_ids:
            raise AgentRouteError(
                "model_not_allowed",
                f"selected exact model is not allowed for {selection.tool}",
                tool=selection.tool,
                model_id=selection.model_id,
            )
        return route


def _reference(value: object, field: str) -> str:
    if not isinstance(value, str) or _REFERENCE.fullmatch(value) is None:
        raise AgentRouteError("invalid_configuration", f"{field} is not a valid reference")
    return value


def _text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value or value.strip() != value or any(c.isspace() for c in value):
        raise AgentRouteError("invalid_selection", f"{field} must be exact non-whitespace text")
    return value


def _unique_text(values: object, field: str) -> tuple[str, ...]:
    if not isinstance(values, (list, tuple)):
        raise AgentRouteError("invalid_configuration", f"{field} values must be a list")
    normalized = tuple(_text(value, field) for value in values)
    if len(set(normalized)) != len(normalized):
        raise AgentRouteError("invalid_configuration", f"duplicate {field} value")
    return normalized


def _unique_references(values: object, field: str) -> tuple[str, ...]:
    if not isinstance(values, tuple):
        raise AgentRouteError("invalid_requirements", f"{field} values must be a tuple")
    normalized = tuple(_reference(value, field) for value in values)
    if len(set(normalized)) != len(normalized):
        raise AgentRouteError("invalid_requirements", f"duplicate {field} value")
    return normalized


def _hostname(value: object) -> str:
    if not isinstance(value, str) or not value or len(value) > 253 or value.endswith("."):
        raise AgentRouteError("invalid_configuration", "permitted destination hostname is invalid")
    labels = value.split(".")
    if len(labels) < 2 or any(_HOST_LABEL.fullmatch(label) is None for label in labels):
        raise AgentRouteError(
            "invalid_configuration",
            "permitted destination hostname must be exact lowercase DNS without wildcards",
        )
    return value


def _destinations(values: object) -> tuple[PermittedDestination, ...]:
    if not isinstance(values, tuple) or not values:
        raise AgentRouteError(
            "invalid_configuration", "permitted_destinations must be a nonempty tuple"
        )
    if any(not isinstance(value, PermittedDestination) for value in values):
        raise AgentRouteError("invalid_configuration", "permitted destination is invalid")
    normalized = tuple(sorted(values, key=lambda value: (value.hostname, value.port)))
    if len(set(normalized)) != len(normalized):
        raise AgentRouteError("invalid_configuration", "permitted destination is duplicated")
    return normalized
