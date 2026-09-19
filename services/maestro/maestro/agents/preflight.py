"""Live preflight and runtime identity checks for exact agent routes."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Callable, Mapping, Protocol

from maestro.foundation import canonical_json
from maestro.service.processes import ProcessProvider, ProcessSnapshot

from .routes import (
    AgentRouteError,
    AgentRouteRegistry,
    PermittedDestination,
    RoleSelections,
    RouteRequirements,
    ToolModelSelection,
    ToolRoute,
)


_DIGEST = re.compile(r"[0-9a-f]{64}\Z")
_ROLES = ("architect", "fidelity_reviewer")


@dataclass(frozen=True)
class InstalledAdapter:
    tool: str
    provider: str
    location: str
    capabilities: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.tool, str) or self.tool not in {"codex", "claude_code"}:
            raise AgentRouteError("unsupported_tool", f"adapter tool is unsupported: {self.tool}")
        if (
            not isinstance(self.provider, str)
            or not self.provider
            or any(character.isspace() for character in self.provider)
        ):
            raise AgentRouteError("invalid_adapter", "adapter provider identity is invalid")
        if self.location not in {"local_ai_box", "cloud"}:
            raise AgentRouteError("invalid_adapter", "adapter location is invalid")
        if (
            not isinstance(self.capabilities, tuple)
            or not self.capabilities
            or any(
                not isinstance(value, str)
                or not value
                or any(character.isspace() for character in value)
                for value in self.capabilities
            )
            or len(set(self.capabilities)) != len(self.capabilities)
        ):
            raise AgentRouteError("invalid_adapter", "adapter capabilities are invalid")


@dataclass(frozen=True)
class AdapterObservation:
    available: bool
    tool_version: str | None
    provider: str | None
    model_ids: tuple[str, ...]
    alias_model_ids: tuple[str, ...]
    capabilities: tuple[str, ...]
    location: str | None
    context_limits: Mapping[str, int]
    authenticated: bool
    credential_profile: str | None
    settings_profile: str | None
    structured_output: bool
    exact_model_enforcement: bool
    substitution_disabled: bool
    configuration_hash: str | None
    reason: str | None = None


class AdapterInspector(Protocol):
    def inspect(self, route: ToolRoute, configuration_hash: str) -> AdapterObservation: ...


ProfileFingerprint = Callable[[str], str | None]


@dataclass(frozen=True)
class ResolvedAgentRoute:
    role: str
    tool: str
    requested_model_id: str
    provider: str
    tool_version: str
    executable: str
    credential_profile: str
    settings_profile: str
    location: str
    capabilities: tuple[str, ...]
    context_limit_tokens: int
    permitted_destinations: tuple[PermittedDestination, ...]
    configuration_hash: str


@dataclass(frozen=True)
class ResolvedRoleRoutes:
    architect: ResolvedAgentRoute
    fidelity_reviewer: ResolvedAgentRoute


@dataclass(frozen=True)
class RunningToolIdentity:
    source: str
    provider: str
    model_id: str
    tool_version: str
    configuration_hash: str


class AgentRoutePreflight:
    """Resolve exactly one selected route; never search for a substitute."""

    def __init__(
        self,
        routes: AgentRouteRegistry,
        adapters: Mapping[str, tuple[InstalledAdapter, AdapterInspector]],
        *,
        credential_fingerprint: ProfileFingerprint,
        settings_fingerprint: ProfileFingerprint,
    ) -> None:
        if not isinstance(routes, AgentRouteRegistry):
            raise TypeError("agent preflight requires an AgentRouteRegistry")
        if not isinstance(adapters, Mapping):
            raise TypeError("agent preflight requires installed adapter registrations")
        if not callable(credential_fingerprint) or not callable(settings_fingerprint):
            raise TypeError("agent preflight requires service-owned profile resolvers")
        self.routes = routes
        self.adapters: dict[str, tuple[InstalledAdapter, AdapterInspector]] = {}
        for tool, pair in adapters.items():
            if not isinstance(pair, tuple) or len(pair) != 2:
                raise AgentRouteError("invalid_adapter", "installed adapter registration is invalid")
            adapter, inspector = pair
            if (
                not isinstance(adapter, InstalledAdapter)
                or adapter.tool != tool
                or not callable(getattr(inspector, "inspect", None))
            ):
                raise AgentRouteError("invalid_adapter", "installed adapter registration is invalid")
            self.adapters[tool] = (adapter, inspector)
        self.credential_fingerprint = credential_fingerprint
        self.settings_fingerprint = settings_fingerprint

    def resolve_process_roles(
        self,
        provider: ProcessProvider,
        snapshot: ProcessSnapshot,
        selections: RoleSelections,
        requirements: Mapping[str, RouteRequirements],
    ) -> ResolvedRoleRoutes:
        """Resolve process roles without reinterpreting its request-operation routes."""
        if not isinstance(provider, ProcessProvider) or provider.name != snapshot.process_name:
            raise AgentRouteError("process_mismatch", "process provider does not match the activity")
        if not isinstance(selections, RoleSelections):
            raise AgentRouteError("missing_selection", "both role selections are required")
        if set(requirements) != set(_ROLES):
            raise AgentRouteError("invalid_requirements", "requirements must be supplied for both roles")
        agent_session = snapshot.definition.get("agent_session")
        if not isinstance(agent_session, Mapping):
            raise AgentRouteError("process_mismatch", "activity has no agent-session definition")
        if (
            agent_session.get("architect_role") != "project_architect"
            or agent_session.get("reviewer_role") != "fidelity_reviewer"
        ):
            raise AgentRouteError("process_mismatch", "activity role definitions are unsupported")
        return ResolvedRoleRoutes(
            architect=self.resolve(
                "architect", selections.architect, requirements["architect"]
            ),
            fidelity_reviewer=self.resolve(
                "fidelity_reviewer",
                selections.fidelity_reviewer,
                requirements["fidelity_reviewer"],
            ),
        )

    def resolve(
        self,
        role: str,
        selection: ToolModelSelection,
        requirements: RouteRequirements,
    ) -> ResolvedAgentRoute:
        if role not in _ROLES:
            raise AgentRouteError("unsupported_role", f"agent role is unsupported: {role}")
        if not isinstance(requirements, RouteRequirements):
            raise AgentRouteError("invalid_requirements", "route requirements are invalid")
        route = self.routes.resolve(selection)
        adapter_pair = self.adapters.get(selection.tool)
        if adapter_pair is None:
            raise AgentRouteError(
                "adapter_not_installed", f"adapter is not installed: {selection.tool}"
            )
        adapter, inspector = adapter_pair
        if adapter.tool != selection.tool:
            raise AgentRouteError("adapter_mismatch", "installed adapter tool identity differs")
        if not route.executable_available:
            raise AgentRouteError(
                "transport_unavailable", f"selected tool executable is unavailable: {route.executable}"
            )
        credential_fingerprint = self.credential_fingerprint(route.credential_profile)
        if credential_fingerprint is None:
            raise AgentRouteError(
                "credential_unavailable", "selected tool credential profile is unavailable"
            )
        if _DIGEST.fullmatch(credential_fingerprint) is None:
            raise AgentRouteError("credential_unavailable", "credential profile identity is invalid")
        settings_fingerprint = self.settings_fingerprint(route.settings_profile)
        if settings_fingerprint is None:
            raise AgentRouteError("settings_unavailable", "selected tool settings profile is unavailable")
        if _DIGEST.fullmatch(settings_fingerprint) is None:
            raise AgentRouteError("settings_unavailable", "settings profile identity is invalid")
        configuration_hash = _configuration_hash(
            route, adapter, credential_fingerprint, settings_fingerprint
        )
        observation = inspector.inspect(route, configuration_hash)
        self._validate_observation(route, adapter, selection, requirements, observation, configuration_hash)
        context_limit = observation.context_limits[selection.model_id]
        return ResolvedAgentRoute(
            role=role,
            tool=selection.tool,
            requested_model_id=selection.model_id,
            provider=adapter.provider,
            tool_version=str(observation.tool_version),
            executable=str(route.executable),
            credential_profile=route.credential_profile,
            settings_profile=route.settings_profile,
            location=adapter.location,
            capabilities=tuple(sorted(adapter.capabilities)),
            context_limit_tokens=context_limit,
            permitted_destinations=route.permitted_destinations,
            configuration_hash=configuration_hash,
        )

    @staticmethod
    def _validate_observation(
        route: ToolRoute,
        adapter: InstalledAdapter,
        selection: ToolModelSelection,
        requirements: RouteRequirements,
        observation: AdapterObservation,
        configuration_hash: str,
    ) -> None:
        if not isinstance(observation, AdapterObservation):
            raise AgentRouteError("preflight_invalid", "adapter returned invalid preflight evidence")
        if not observation.available:
            raise AgentRouteError(
                "transport_unavailable", observation.reason or "selected adapter is unavailable"
            )
        if not isinstance(observation.tool_version, str) or not observation.tool_version:
            raise AgentRouteError("identity_unverified", "installed tool version is unavailable")
        if (
            not isinstance(observation.model_ids, tuple)
            or not isinstance(observation.alias_model_ids, tuple)
            or not isinstance(observation.capabilities, tuple)
            or not isinstance(observation.context_limits, Mapping)
            or any(not isinstance(value, str) or not value for value in observation.model_ids)
            or any(not isinstance(value, str) or not value for value in observation.alias_model_ids)
            or any(not isinstance(value, str) or not value for value in observation.capabilities)
            or any(
                not isinstance(value, bool)
                for value in (
                    observation.authenticated,
                    observation.structured_output,
                    observation.exact_model_enforcement,
                    observation.substitution_disabled,
                )
            )
        ):
            raise AgentRouteError("preflight_invalid", "adapter capability evidence is invalid")
        if observation.provider != adapter.provider:
            raise AgentRouteError("identity_mismatch", "installed adapter provider identity differs")
        if observation.location != adapter.location:
            raise AgentRouteError("location_mismatch", "installed adapter location differs")
        if selection.model_id in observation.alias_model_ids:
            raise AgentRouteError("model_alias", "moving model aliases are not accepted")
        if selection.model_id not in observation.model_ids:
            raise AgentRouteError("model_unavailable", "selected exact model is unavailable")
        if not observation.exact_model_enforcement or not observation.substitution_disabled:
            raise AgentRouteError(
                "model_not_enforceable", "selected exact model cannot be enforced without substitution"
            )
        if not observation.authenticated:
            raise AgentRouteError("authentication_failed", "selected tool authentication failed")
        if observation.credential_profile != route.credential_profile:
            raise AgentRouteError("credential_mismatch", "preflight used a different credential profile")
        if observation.settings_profile != route.settings_profile:
            raise AgentRouteError("settings_mismatch", "preflight used a different settings profile")
        if not observation.structured_output:
            raise AgentRouteError("capability_missing", "structured output is unavailable")
        observed_capabilities = frozenset(observation.capabilities)
        declared_capabilities = frozenset(adapter.capabilities)
        if not declared_capabilities.issubset(observed_capabilities):
            raise AgentRouteError("capability_mismatch", "installed adapter capabilities differ")
        missing = set(requirements.capabilities) - (
            observed_capabilities & declared_capabilities
        )
        if missing:
            raise AgentRouteError(
                "capability_missing", f"selected route lacks capability: {sorted(missing)[0]}"
            )
        if adapter.location not in requirements.allowed_locations:
            raise AgentRouteError(
                "location_not_allowed", f"selected route location is not allowed: {adapter.location}"
            )
        context_limit = observation.context_limits.get(selection.model_id)
        if isinstance(context_limit, bool) or not isinstance(context_limit, int) or context_limit < 1:
            raise AgentRouteError("context_unverified", "selected model context limit is unavailable")
        if context_limit < requirements.minimum_context_tokens:
            raise AgentRouteError(
                "context_insufficient",
                "selected model context limit is below the assignment requirement",
                available=context_limit,
                required=requirements.minimum_context_tokens,
            )
        if observation.configuration_hash != configuration_hash:
            raise AgentRouteError("configuration_changed", "live tool configuration differs")


def verify_running_identity(
    route: ResolvedAgentRoute, identity: RunningToolIdentity
) -> RunningToolIdentity:
    """Accept identity only from tool metadata matching the preflight snapshot."""
    if not isinstance(route, ResolvedAgentRoute) or not isinstance(identity, RunningToolIdentity):
        raise AgentRouteError("identity_unverified", "running tool identity evidence is missing")
    if identity.source != "tool_metadata":
        raise AgentRouteError("identity_unverified", "agent-written text is not identity evidence")
    if (
        identity.provider != route.provider
        or identity.model_id != route.requested_model_id
        or identity.tool_version != route.tool_version
        or identity.configuration_hash != route.configuration_hash
    ):
        raise AgentRouteError("identity_mismatch", "running tool identity differs from preflight")
    return identity


def _configuration_hash(
    route: ToolRoute,
    adapter: InstalledAdapter,
    credential_fingerprint: str,
    settings_fingerprint: str,
) -> str:
    value = canonical_json(
        {
            "allowed_model_ids": list(route.allowed_model_ids),
            "capabilities": sorted(adapter.capabilities),
            "credential_fingerprint": credential_fingerprint,
            "credential_profile": route.credential_profile,
            "executable": str(route.executable),
            "location": adapter.location,
            "permitted_destinations": [
                destination.as_dict() for destination in route.permitted_destinations
            ],
            "provider": adapter.provider,
            "settings_profile": route.settings_profile,
            "settings_fingerprint": settings_fingerprint,
            "tool": route.tool,
        }
    )
    return hashlib.sha256(value.encode("utf-8")).hexdigest()
