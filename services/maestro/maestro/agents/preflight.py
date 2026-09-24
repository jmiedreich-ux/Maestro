"""Live preflight and runtime identity checks for exact agent routes."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import time
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Mapping, Protocol, Sequence

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


PASS, FAIL, EXCLUDED, UNVERIFIED = "pass", "fail", "excluded", "unverified"
ENVIRONMENT_CATEGORIES = (
    "host_and_tools",
    "source_and_workspace",
    "identity_and_credentials",
    "agent_routes",
    "github_and_test_targets",
    "service_and_network",
    "install_and_upgrade",
    "data_and_migration",
    "observability_and_smoke",
)


@dataclass(frozen=True)
class CheckResult:
    category: str
    check: str
    status: str
    detail: str


@dataclass(frozen=True)
class FeatureProfile:
    """One selected development feature and the real targets it needs."""

    name: str
    repository: Path
    revision: str | None
    agents_config: Path
    workspace_root: Path
    tools: tuple[tuple[str, str], ...] = ()
    credential_files: Mapping[str, Path] | None = None
    github_repository: str | None = None
    require_app_administration_read: bool = False
    require_protected_branch: bool = False
    needs_service: bool = False
    progress_log: Path | None = None
    require_progress_channel: bool = False


@dataclass(frozen=True)
class EnvironmentProbes:
    """Host observations; tests substitute fakes, the command uses real ones."""

    run: Callable[[Sequence[str]], tuple[int, str]]
    now_ms: Callable[[], int]
    github_api: Callable[[str], Mapping[str, object] | None]
    github_app_permissions: Callable[[], Mapping[str, str] | None]


@dataclass(frozen=True)
class PreflightReport:
    feature: str
    results: tuple[CheckResult, ...]

    @property
    def blocking(self) -> tuple[CheckResult, ...]:
        return tuple(r for r in self.results if r.status in (FAIL, UNVERIFIED))

    @property
    def passed(self) -> bool:
        return not self.blocking

    def as_dict(self) -> dict[str, object]:
        return {
            "feature": self.feature,
            "passed": self.passed,
            "categories": {
                category: [
                    {"check": r.check, "status": r.status, "detail": r.detail}
                    for r in self.results
                    if r.category == category
                ]
                for category in ENVIRONMENT_CATEGORIES
            },
            "missing": [
                {"category": r.category, "check": r.check, "status": r.status, "detail": r.detail}
                for r in self.blocking
            ],
        }

    def render(self) -> str:
        lines = [f"Environment preflight for: {self.feature}"]
        for category in ENVIRONMENT_CATEGORIES:
            lines.append(f"[{category}]")
            for r in (r for r in self.results if r.category == category):
                lines.append(f"  {r.status.upper():10} {r.check}: {r.detail}")
        if self.blocking:
            lines.append(f"BLOCKED: {len(self.blocking)} requirement(s) not met")
            lines.extend(f"  - {r.category}/{r.check}: {r.detail}" for r in self.blocking)
        else:
            lines.append("PASSED: every applicable check passed")
        return "\n".join(lines)


def run_environment_preflight(
    profile: FeatureProfile, probes: EnvironmentProbes
) -> PreflightReport:
    """Evaluate every contract category; one failing check never hides another."""
    results: list[CheckResult] = []
    for category, check in (
        ("host_and_tools", _check_host),
        ("source_and_workspace", _check_source),
        ("identity_and_credentials", _check_credentials),
        ("agent_routes", _check_routes),
        ("github_and_test_targets", _check_github),
        ("service_and_network", _check_service),
        ("install_and_upgrade", _check_install),
        ("data_and_migration", _check_data),
        ("observability_and_smoke", _check_observability),
    ):
        try:
            results.extend(check(profile, probes))
        except Exception as error:  # a broken probe is a finding, never an omission
            results.append(
                CheckResult(category, "check_error", UNVERIFIED, f"{type(error).__name__}: {error}")
            )
    return PreflightReport(profile.name, tuple(results))


def _ok(category: str, check: str, detail: str) -> CheckResult:
    return CheckResult(category, check, PASS, detail)


def _bad(category: str, check: str, detail: str) -> CheckResult:
    return CheckResult(category, check, FAIL, detail)


def _unknown(category: str, check: str, detail: str) -> CheckResult:
    return CheckResult(category, check, UNVERIFIED, detail)


def _version(probes: EnvironmentProbes, command: Sequence[str]) -> str | None:
    code, output = probes.run(command)
    return output.strip().splitlines()[0] if code == 0 and output.strip() else None


def _check_host(profile: FeatureProfile, probes: EnvironmentProbes) -> list[CheckResult]:
    c = "host_and_tools"
    out = [
        _ok(c, "platform", f"{platform.system()} {platform.release()}")
        if platform.system() == "Linux"
        else _bad(c, "platform", f"not a Linux host: {platform.system()}")
    ]
    for label, command in (("git", ["git", "--version"]), ("python", [sys.executable, "--version"])):
        version = _version(probes, command)
        out.append(_ok(c, label, version) if version else _bad(c, label, "not runnable"))
    baseline = _version(probes, [sys.executable, "-m", "unittest", "--help"])
    out.append(
        _ok(c, "baseline_runner", "python unittest available")
        if baseline
        else _bad(c, "baseline_runner", "python unittest is not runnable")
    )
    bwrap = shutil.which("bwrap") or "/usr/bin/bwrap"
    out.append(
        _ok(c, "isolation_tool", bwrap)
        if os.access(bwrap, os.X_OK)
        else _bad(c, "isolation_tool", "bwrap is not installed or not executable")
    )
    probe_dir = profile.workspace_root if profile.workspace_root.exists() else profile.workspace_root.parent
    free = shutil.disk_usage(probe_dir).free if probe_dir.exists() else 0
    out.append(
        _ok(c, "disk_space", f"{free // 2**30} GiB free")
        if free >= 2**30
        else _bad(c, "disk_space", f"under 1 GiB free at {probe_dir}")
    )
    return out


def _check_source(profile: FeatureProfile, probes: EnvironmentProbes) -> list[CheckResult]:
    c = "source_and_workspace"
    repo = str(profile.repository)
    out: list[CheckResult] = []
    code, head = probes.run(["git", "-C", repo, "rev-parse", "HEAD"])
    if code != 0:
        out.append(_bad(c, "repository", f"not a readable git repository: {repo}"))
    else:
        if profile.revision:
            code, pinned = probes.run(
                ["git", "-C", repo, "rev-parse", "--verify", f"{profile.revision}^{{commit}}"]
            )
            out.append(
                _ok(c, "pinned_revision", pinned.strip())
                if code == 0
                else _bad(c, "pinned_revision", f"revision does not resolve: {profile.revision}")
            )
        else:
            out.append(
                _unknown(c, "pinned_revision", f"no revision pinned; checkout is at {head.strip()}")
            )
        code, status = probes.run(["git", "-C", repo, "status", "--porcelain"])
        out.append(
            _ok(c, "clean_checkout", "no uncommitted changes")
            if code == 0 and not status.strip()
            else _bad(
                c,
                "clean_checkout",
                "uncommitted changes present" if code == 0 else "status unreadable",
            )
        )
    root = profile.workspace_root
    writable = root.is_dir() and os.access(root, os.W_OK | os.X_OK)
    out.append(
        _ok(c, "workspace_root", f"{root} writable")
        if writable
        else _bad(c, "workspace_root", f"{root} missing or not writable by this user")
    )
    return out


def _claude_expiry(path: Path) -> tuple[int | None, bool]:
    document = json.loads(path.read_text(encoding="utf-8"))
    entry = document.get("claudeAiOauth") if isinstance(document, dict) else None
    if not isinstance(entry, dict) or not isinstance(entry.get("expiresAt"), int):
        return None, False
    return entry["expiresAt"], bool(entry.get("refreshToken"))


def _check_credentials(profile: FeatureProfile, probes: EnvironmentProbes) -> list[CheckResult]:
    c = "identity_and_credentials"
    files = dict(profile.credential_files or {})
    if not profile.tools:
        return [_unknown(c, "selected_tools", "no agent tool selected for this feature")]
    out: list[CheckResult] = []
    for tool, _model in profile.tools:
        path = files.get(tool)
        if path is None:
            out.append(_unknown(c, f"{tool}_credential", "no credential location supplied"))
            continue
        try:
            if not path.is_file():
                out.append(_bad(c, f"{tool}_credential", f"credential file missing: {path}"))
                continue
            if tool == "claude_code":
                expires, refreshable = _claude_expiry(path)
                if expires is None:
                    out.append(_bad(c, "claude_oauth", "no OAuth expiry recorded"))
                elif expires <= probes.now_ms():
                    when = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(expires / 1000))
                    out.append(
                        _bad(
                            c,
                            "claude_oauth",
                            f"expired {when}; refresh token {'present' if refreshable else 'absent'}; "
                            "an interactive Owner login is needed if refresh fails",
                        )
                    )
                else:
                    when = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(expires / 1000))
                    out.append(_ok(c, "claude_oauth", f"valid until {when}"))
            else:
                out.append(_ok(c, f"{tool}_credential", "credential file present (contents not inspected)"))
        except PermissionError:
            out.append(_bad(c, f"{tool}_credential", f"credential file unreadable by this user: {path}"))
        except (OSError, ValueError) as error:
            out.append(_bad(c, f"{tool}_credential", f"credential file invalid: {type(error).__name__}"))
    return out


def _check_routes(profile: FeatureProfile, probes: EnvironmentProbes) -> list[CheckResult]:
    c = "agent_routes"
    try:
        document = tomllib.loads(profile.agents_config.read_text(encoding="utf-8"))
    except PermissionError:
        return [_bad(c, "agents_toml", f"unreadable by this user: {profile.agents_config}")]
    except (OSError, ValueError) as error:
        return [_bad(c, "agents_toml", f"cannot read {profile.agents_config}: {type(error).__name__}")]
    try:
        registry = AgentRouteRegistry.from_mapping(document.get("tools", {}))
    except AgentRouteError as error:
        return [_bad(c, "agents_toml", f"{error.code}: {error}")]
    out = [_ok(c, "agents_toml", f"parsed {profile.agents_config}")]
    for tool, model in profile.tools:
        try:
            route = registry.resolve(ToolModelSelection(tool, model))
        except AgentRouteError as error:
            out.append(_bad(c, f"{tool}_route", f"{error.code}: {error}"))
            continue
        if not route.executable_available:
            out.append(_bad(c, f"{tool}_executable", f"missing or not executable: {route.executable}"))
            continue
        version = _version(probes, [str(route.executable), "--version"])
        if not version:
            out.append(_bad(c, f"{tool}_executable", f"--version failed: {route.executable}"))
            continue
        out.append(_ok(c, f"{tool}_route", f"{model} via {route.executable} reports '{version}'"))
        destinations = ", ".join(f"{d.hostname}:{d.port}" for d in route.permitted_destinations)
        out.append(_ok(c, f"{tool}_egress", f"permitted destinations: {destinations}"))
    return out


def _check_github(profile: FeatureProfile, probes: EnvironmentProbes) -> list[CheckResult]:
    c = "github_and_test_targets"
    if not profile.github_repository:
        return [CheckResult(c, "github", EXCLUDED, "selected feature names no GitHub target")]
    repo = probes.github_api(f"repos/{profile.github_repository}")
    if repo is None:
        return [_unknown(c, "repository_access", f"cannot read {profile.github_repository}")]
    permissions = repo.get("permissions") if isinstance(repo.get("permissions"), Mapping) else {}
    out = [
        _ok(c, "read_access", profile.github_repository)
        if permissions.get("pull")
        else _bad(c, "read_access", "no read access"),
        _ok(c, "write_access", "token reports push permission (a write was not exercised)")
        if permissions.get("push")
        else _bad(c, "write_access", "token lacks push permission"),
    ]
    if profile.require_app_administration_read:
        app = probes.github_app_permissions()
        if app is None:
            out.append(_unknown(c, "app_administration_read", "GitHub app permissions could not be read"))
        elif app.get("administration") in ("read", "write"):
            out.append(_ok(c, "app_administration_read", f"granted ({app['administration']})"))
        else:
            out.append(_bad(c, "app_administration_read", "GitHub app lacks Administration: read"))
    if profile.require_protected_branch:
        if repo.get("private") is False:
            out.append(_ok(c, "protected_branch_case", "public repository; branch protection is available"))
        else:
            out.append(
                _unknown(
                    c,
                    "protected_branch_case",
                    "private repository; enabling protection needs a paid plan and was not exercised. "
                    "Use an eligible isolated target",
                )
            )
    return out


def _check_service(profile: FeatureProfile, probes: EnvironmentProbes) -> list[CheckResult]:
    c = "service_and_network"
    if not profile.needs_service:
        return [CheckResult(c, "service", EXCLUDED, "selected feature does not require the running service")]
    code, state = probes.run(["systemctl", "is-active", "maestro.service"])
    return [
        _ok(c, "service_state", "maestro.service active")
        if code == 0 and state.strip() == "active"
        else _bad(c, "service_state", f"maestro.service is {state.strip() or 'not reachable'}")
    ]


def _check_install(profile: FeatureProfile, probes: EnvironmentProbes) -> list[CheckResult]:
    c = "install_and_upgrade"
    if profile.needs_service:
        return [_unknown(c, "service_upgrade", "upgrade and rollback path not exercised by this preflight")]
    return [CheckResult(c, "service_upgrade", EXCLUDED, "baseline agent run installs no service; tool versions are recorded under host_and_tools and agent_routes")]


def _check_data(profile: FeatureProfile, probes: EnvironmentProbes) -> list[CheckResult]:
    c = "data_and_migration"
    root = profile.workspace_root
    out = [CheckResult(c, "schema_migration", EXCLUDED, "no service schema is involved in the baseline run")]
    if not (root.is_dir() and os.access(root, os.W_OK | os.X_OK)):
        return out + [_bad(c, "run_data_reset", f"cannot exercise reset; {root} is not writable")]
    marker = root / f".preflight-reset-{os.getpid()}"
    try:
        marker.mkdir()
        (marker / "output.txt").write_text("run-owned\n", encoding="utf-8")
        shutil.rmtree(marker)
    except OSError as error:
        return out + [_bad(c, "run_data_reset", f"reset probe failed: {type(error).__name__}")]
    return out + [
        _ok(c, "run_data_reset", "created and removed a run-owned directory; no unrelated entry touched")
        if not marker.exists()
        else _bad(c, "run_data_reset", "run-owned directory survived reset")
    ]


def _check_observability(profile: FeatureProfile, probes: EnvironmentProbes) -> list[CheckResult]:
    c = "observability_and_smoke"
    if profile.progress_log is None:
        if not profile.require_progress_channel:
            return [CheckResult(c, "progress_channel", EXCLUDED, "selected feature does not require an external progress channel")]
        return [_unknown(c, "progress_channel", "no Slack receipt log supplied; a LocalDurable row is not Slack delivery")]
    try:
        text = profile.progress_log.read_text(encoding="utf-8")
    except OSError:
        return [_unknown(c, "progress_channel", f"receipt log unreadable: {profile.progress_log}")]
    receipts = [line for line in text.splitlines() if "sent heartbeat" in line]
    if not receipts:
        return [_unknown(c, "progress_channel", "no delivered receipt recorded")]
    return [_ok(c, "progress_channel", f"{len(receipts)} delivered receipt(s); latest: {receipts[-1][:32]}")]


def host_probes(app: tuple[str, str, Path] | None = None) -> EnvironmentProbes:
    """Real observations: subprocesses, the gh CLI, and the coordinator app JWT."""

    def run(command: Sequence[str]) -> tuple[int, str]:
        try:
            done = subprocess.run(
                list(command), capture_output=True, text=True, timeout=30, check=False
            )
        except (OSError, subprocess.SubprocessError):
            return 127, ""
        return done.returncode, done.stdout or done.stderr

    def github_api(path: str) -> Mapping[str, object] | None:
        code, output = run(["gh", "api", path])
        try:
            value = json.loads(output) if code == 0 else None
        except ValueError:
            return None
        return value if isinstance(value, dict) else None

    def app_permissions() -> Mapping[str, str] | None:
        if app is None:
            return None
        import urllib.error
        import urllib.request

        from maestro import github_client

        app_id, installation_id, key_file = app
        try:
            credentials = github_client.GitHubAppCredentials(
                app_id, installation_id, key_file.read_text(encoding="utf-8")
            )
            token = github_client._app_jwt(credentials, int(time.time()))
            request = urllib.request.Request(
                f"https://api.github.com/app/installations/{installation_id}",
                headers=github_client._jwt_headers(token),
            )
            with urllib.request.urlopen(request, timeout=20) as response:
                value = json.load(response)
        except (OSError, ValueError, urllib.error.URLError, github_client.GitHubClientError):
            return None
        permissions = value.get("permissions") if isinstance(value, dict) else None
        return permissions if isinstance(permissions, dict) else None

    return EnvironmentProbes(run, lambda: int(time.time() * 1000), github_api, app_permissions)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the Maestro development environment preflight")
    parser.add_argument("--feature", required=True)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--revision")
    parser.add_argument("--agents-config", type=Path, required=True)
    parser.add_argument("--workspace-root", type=Path, required=True)
    parser.add_argument("--tool", action="append", default=[], metavar="TOOL:MODEL")
    parser.add_argument("--credential", action="append", default=[], metavar="TOOL=PATH")
    parser.add_argument("--github-repository")
    parser.add_argument("--github-app", metavar="APP_ID:INSTALLATION_ID:KEYFILE")
    parser.add_argument("--require-app-administration-read", action="store_true")
    parser.add_argument("--require-protected-branch", action="store_true")
    parser.add_argument("--needs-service", action="store_true")
    parser.add_argument("--progress-log", type=Path)
    parser.add_argument("--require-progress-channel", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    tools = tuple(tuple(value.split(":", 1)) for value in args.tool if ":" in value)
    credentials = {k: Path(v) for k, _, v in (item.partition("=") for item in args.credential) if v}
    profile = FeatureProfile(
        name=args.feature,
        repository=args.repository,
        revision=args.revision,
        agents_config=args.agents_config,
        workspace_root=args.workspace_root,
        tools=tools,  # type: ignore[arg-type]
        credential_files=credentials,
        github_repository=args.github_repository,
        require_app_administration_read=args.require_app_administration_read,
        require_protected_branch=args.require_protected_branch,
        needs_service=args.needs_service,
        progress_log=args.progress_log,
        require_progress_channel=args.require_progress_channel,
    )
    app = None
    if args.github_app:
        app_id, installation_id, key_file = args.github_app.split(":", 2)
        app = (app_id, installation_id, Path(key_file))
    report = run_environment_preflight(profile, host_probes(app))
    print(json.dumps(report.as_dict(), indent=2) if args.json else report.render())
    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
