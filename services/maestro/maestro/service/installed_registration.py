"""Production composition for the installed registration process."""

from __future__ import annotations

import hashlib
import os
import stat
import subprocess
from collections.abc import Mapping
from pathlib import Path
from urllib.parse import urlsplit

from maestro.agents.preflight import AdapterObservation, InstalledAdapter
from maestro.agents.routes import ConfiguredAgentRouteProvider, ToolRoute
from maestro.foundation import canonical_json
from maestro.foundation.credentials import (
    GitHubAppCredential,
    RepositoryAuthorizer,
    RepositoryBinding,
    RepositoryProfile,
    ServiceGitHubAppCredentials,
    ServiceGitRoute,
    ServiceGitTransport,
)
from maestro.foundation.github_destination import (
    GitHubAppDestinationProfile,
    GitHubDestinationProvider,
    GitHubRestDestinationApi,
)
from maestro.planning.registration_plugin import RegistrationProcessPlugin
from maestro.planning.sources import ExactSourceReader
from maestro.service.processes import prepare_process_snapshot
from maestro.service.resources import InstalledSchemaResources

from .registration import RegistrationRuntimeDependencies
from .registration_agents import InstalledRegistrationAgentLauncher


_CAPABILITIES = (
    "code_edit",
    "local_command",
    "repository_search",
    "approved_network",
)


class InstalledToolInspector:
    """Observe an exact configured executable at process-start preflight."""

    def __init__(self, tool: str, provider: str) -> None:
        self.tool = tool
        self.provider = provider

    def inspect(self, route: ToolRoute, configuration_hash: str) -> AdapterObservation:
        try:
            completed = subprocess.run(
                (str(route.executable), "--version"),
                check=False,
                capture_output=True,
                text=True,
                timeout=5,
                env={"PATH": "/usr/bin:/bin"},
            )
            version = (completed.stdout or completed.stderr).strip().splitlines()[0]
            available = completed.returncode == 0 and bool(version)
        except (OSError, subprocess.SubprocessError, IndexError):
            available, version = False, ""
        return AdapterObservation(
            available,
            version or None,
            self.provider if available else None,
            tuple(route.allowed_model_ids),
            (),
            _CAPABILITIES,
            "cloud" if available else None,
            {model: 65536 for model in route.allowed_model_ids},
            available,
            route.credential_profile if available else None,
            route.settings_profile if available else None,
            available,
            available,
            available,
            configuration_hash if available else None,
            None if available else f"configured {self.tool} executable is unavailable",
        )


def compose_installed_registration(
    configuration: Mapping[str, object],
    *,
    route_provider: ConfiguredAgentRouteProvider | None,
    storage_path: Path,
    service_home: Path,
    workspace_root: Path,
) -> RegistrationRuntimeDependencies:
    """Validate and compose the one installed registration runtime."""
    if route_provider is None:
        raise ValueError("installed agent route configuration is missing")
    registration = _table(configuration.get("registration"), "registration")
    tools = _table(configuration.get("tools"), "tools")
    adapters = {}
    credential_files: dict[str, tuple[Path, ...]] = {}
    settings_fingerprints: dict[str, str] = {}
    for tool, raw in tools.items():
        route = _table(raw, f"tools.{tool}")
        credential = _text(route.get("credential_profile"), "credential_profile")
        settings = _text(route.get("settings_profile"), "settings_profile")
        if tool == "codex":
            provider = "openai"
            files = (service_home / ".codex" / "auth.json",)
        elif tool == "claude_code":
            provider = "anthropic"
            files = (
                service_home / ".claude.json",
                service_home / ".claude" / ".credentials.json",
            )
        else:
            raise ValueError(f"installed registration adapter is unsupported: {tool}")
        adapters[str(tool)] = (
            InstalledAdapter(str(tool), provider, "cloud", _CAPABILITIES),
            InstalledToolInspector(str(tool), provider),
        )
        credential_files[credential] = files
        settings_fingerprints[settings] = hashlib.sha256(
            canonical_json(route).encode("utf-8")
        ).hexdigest()

    preflight = route_provider.preflight(
        adapters,
        credential_fingerprint=lambda name: _files_fingerprint(
            credential_files.get(name, ())
        ),
        settings_fingerprint=lambda name: settings_fingerprints.get(name),
    )
    plugin = RegistrationProcessPlugin(route_provider, preflight)
    snapshot = prepare_process_snapshot(
        InstalledSchemaResources(), plugin.provider, "registration", registration
    )

    raw_profiles = _table(configuration.get("repositories"), "repositories")
    raw_bindings = _table(
        configuration.get("repository_bindings"), "repository_bindings"
    )
    profiles: dict[str, RepositoryProfile] = {}
    github_profiles: dict[str, Mapping[str, object]] = {}
    for name, raw in raw_profiles.items():
        profile = _table(raw, f"repositories.{name}")
        if set(profile) != {
            "credential_profile",
            "allowed_repositories",
            "allowed_branch_patterns",
            "github",
        }:
            raise ValueError(f"repositories.{name} fields do not match the contract")
        repositories = _text_list(
            profile["allowed_repositories"], f"repositories.{name}.allowed_repositories"
        )
        branches = _text_list(
            profile["allowed_branch_patterns"],
            f"repositories.{name}.allowed_branch_patterns",
        )
        profiles[str(name)] = RepositoryProfile(
            str(name),
            _text(profile["credential_profile"], "credential_profile"),
            repositories,
            branches,
        )
        github_profiles[str(name)] = _table(
            profile["github"], f"repositories.{name}.github"
        )
    bindings = tuple(
        RepositoryBinding(
            str(binding_id),
            _text(_table(raw, f"repository_bindings.{binding_id}").get("repository"), "repository"),
            _text(_table(raw, f"repository_bindings.{binding_id}").get("profile"), "profile"),
        )
        for binding_id, raw in raw_bindings.items()
        if set(_table(raw, f"repository_bindings.{binding_id}")) == {"repository", "profile"}
    )
    if len(bindings) != len(raw_bindings):
        raise ValueError("repository binding fields do not match the contract")
    authorizer = RepositoryAuthorizer(profiles, bindings)
    if len(profiles) != 1 or len(bindings) != 1:
        raise ValueError("registration currently requires one installed GitHub repository binding")
    binding = bindings[0]
    profile = profiles[binding.profile_name]
    github = github_profiles[binding.profile_name]
    required_github = {"app_id", "installation_id", "app_slug"}
    if (
        not required_github.issubset(github)
        or set(github) - required_github - {"api_base_url"}
    ):
        raise ValueError("GitHub destination profile fields do not match the contract")
    api_base_url = github.get("api_base_url", "https://api.github.com")
    destination_profile = GitHubAppDestinationProfile(
        profile.name,
        binding.binding_id,
        GitHubAppCredential(profile.credential_reference),
        github["app_id"],  # type: ignore[arg-type]
        github["installation_id"],  # type: ignore[arg-type]
        _text(github["app_slug"], "app_slug"),
        profile.allowed_repositories,
        profile.allowed_branch_patterns,
        api_base_url,  # type: ignore[arg-type]
    )
    secret_root = storage_path.parent / "secrets"
    resolver = lambda reference: _read_service_secret(secret_root, reference)
    destination = GitHubDestinationProvider(
        destination_profile,
        GitHubRestDestinationApi(ServiceGitHubAppCredentials(resolver)),
    )
    remote = _github_remote(str(api_base_url), binding.repository)
    transport = ServiceGitTransport(
        (ServiceGitRoute(binding.repository, profile.credential_reference, remote),),
        resolver,
    )
    assignment_launcher = InstalledRegistrationAgentLauncher(
        workspace_root=workspace_root,
        source_cache_root=storage_path.parent / "registration-sources",
        service_home=service_home,
        authorizer=authorizer,
        transport=transport,
        destination_provider=destination,
    )
    return RegistrationRuntimeDependencies(
        ExactSourceReader(),
        authorizer,
        transport,
        destination,
        preflight,
        snapshot,
        lambda repository: _github_remote(str(api_base_url), repository),
        workspace_root=workspace_root,
        assignment_launcher=assignment_launcher,
    )


def _github_remote(api_base_url: str, repository: str) -> str:
    parsed = urlsplit(api_base_url)
    host = "github.com" if parsed.hostname == "api.github.com" else parsed.hostname
    if not host:
        raise ValueError("GitHub API base URL has no host")
    return f"https://{host}/{repository}.git"


def _read_service_secret(root: Path, reference: str) -> str:
    root_details = root.lstat()
    if root.is_symlink() or not stat.S_ISDIR(root_details.st_mode):
        raise ValueError("service credential directory is unsafe")
    path = root / reference
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        details = os.fstat(descriptor)
        if (
            not stat.S_ISREG(details.st_mode)
            or stat.S_IMODE(details.st_mode) != 0o600
            or details.st_uid != root_details.st_uid
        ):
            raise ValueError(
                "service credential file must be a service-owned mode 0600 regular file"
            )
        return os.read(descriptor, 1024 * 1024).decode("utf-8")
    finally:
        os.close(descriptor)


def _files_fingerprint(paths: tuple[Path, ...]) -> str | None:
    if not paths:
        return None
    digest = hashlib.sha256()
    try:
        service_home = (
            paths[0].parent.parent
            if paths[0].parent.name in {".codex", ".claude"}
            else paths[0].parent
        )
        owner = service_home.lstat().st_uid
        if service_home.is_symlink() or not service_home.is_dir():
            return None
        for path in paths:
            details = path.lstat()
            if (
                path.is_symlink()
                or not stat.S_ISREG(details.st_mode)
                or details.st_uid != owner
                or stat.S_IMODE(details.st_mode) & 0o077
            ):
                return None
            digest.update(path.read_bytes())
    except OSError:
        return None
    return digest.hexdigest()


def _table(value: object, field: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{field} must be a table")
    return value


def _text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be nonempty text")
    return value.strip()


def _text_list(value: object, field: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not value:
        raise ValueError(f"{field} must be a nonempty list")
    return tuple(_text(item, field) for item in value)
