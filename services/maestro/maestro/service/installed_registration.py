"""Production composition for the installed registration process."""

from __future__ import annotations

import hashlib
import json
import os
import selectors
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
    GitHubDestinationRouter,
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
    """Obtain live tool-native route evidence without reading project sources."""

    def __init__(self, tool: str, provider: str, service_home: Path) -> None:
        self.tool = tool
        self.provider = provider
        self.service_home = Path(service_home)

    def inspect(self, route: ToolRoute, configuration_hash: str) -> AdapterObservation:
        try:
            evidence = (
                self._inspect_codex(route)
                if self.tool == "codex"
                else self._inspect_claude(route)
            )
        except (OSError, ValueError, subprocess.SubprocessError) as error:
            return AdapterObservation(
                False, None, None, (), (), (), None, {}, False, None, None,
                False, False, False, None,
                f"configured {self.tool} route could not produce live evidence: {error}",
            )
        models, context_limits, version = evidence
        return AdapterObservation(
            True,
            version,
            self.provider,
            models,
            (),
            _CAPABILITIES,
            "cloud",
            context_limits,
            True,
            route.credential_profile,
            route.settings_profile,
            True,
            True,
            True,
            configuration_hash,
            None,
        )

    def _inspect_codex(
        self, route: ToolRoute
    ) -> tuple[tuple[str, ...], dict[str, int], str]:
        process = subprocess.Popen(
            (str(route.executable), "app-server"),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=0,
            env=self._environment(),
        )
        try:
            if process.stdin is None or process.stdout is None:
                raise ValueError("Codex app-server pipes are unavailable")
            self._write_json(
                process,
                {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "clientInfo": {"name": "maestro-preflight", "version": "1"},
                        "capabilities": {"experimentalApi": False},
                    },
                },
            )
            initialized = self._codex_response(process, 1)
            version = initialized.get("userAgent")
            if not isinstance(version, str) or not version:
                raise ValueError("Codex app-server version metadata is unavailable")
            self._write_json(
                process, {"jsonrpc": "2.0", "method": "initialized", "params": {}}
            )
            self._write_json(
                process,
                {"jsonrpc": "2.0", "id": 2, "method": "model/list", "params": {}},
            )
            catalog = self._codex_response(process, 2).get("data")
            if not isinstance(catalog, list):
                raise ValueError("Codex model catalog is unavailable")
            exact_entries: dict[str, Mapping[str, object]] = {}
            context_limits: dict[str, int] = {}
            for model_id in route.allowed_model_ids:
                matches = [
                    item for item in catalog
                    if isinstance(item, Mapping)
                    and item.get("id") == model_id
                    and item.get("model") == model_id
                ]
                if len(matches) != 1:
                    continue
                limit = _reported_context_limit(matches[0])
                if limit is None:
                    continue
                exact_entries[model_id] = matches[0]
                context_limits[model_id] = limit
            verified: list[str] = []
            request_id = 10
            for model_id in route.allowed_model_ids:
                if model_id not in exact_entries:
                    continue
                self._write_json(
                    process,
                    {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "method": "thread/start",
                        "params": {
                            "model": model_id,
                            "cwd": str(self.service_home),
                            "approvalPolicy": "never",
                            "sandbox": "read-only",
                        },
                    },
                )
                thread_result = self._codex_response(process, request_id)
                thread = thread_result.get("thread")
                if (
                    not isinstance(thread, Mapping)
                    or not isinstance(thread.get("id"), str)
                    or thread_result.get("model") != model_id
                    or thread_result.get("modelProvider") != self.provider
                ):
                    continue
                thread_id = str(thread["id"])
                request_id += 1
                schema = _preflight_schema()
                self._write_json(
                    process,
                    {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "method": "turn/start",
                        "params": {
                            "threadId": thread_id,
                            "input": [{"type": "text", "text": "Return the required preflight object without using tools."}],
                            "outputSchema": schema,
                        },
                    },
                )
                turn_result = self._codex_response(process, request_id)
                turn = turn_result.get("turn")
                if not isinstance(turn, Mapping) or not isinstance(turn.get("id"), str):
                    continue
                if self._codex_turn_completed(process, thread_id, str(turn["id"])):
                    verified.append(model_id)
                request_id += 1
            if not verified:
                raise ValueError("Codex authentication and structured output were not verified")
            return tuple(verified), {
                model_id: context_limits[model_id] for model_id in verified
            }, version
        finally:
            _terminate_preflight(process)

    def _inspect_claude(
        self, route: ToolRoute
    ) -> tuple[tuple[str, ...], dict[str, int], str]:
        verified: list[str] = []
        limits: dict[str, int] = {}
        observed_version: str | None = None
        for model_id in route.allowed_model_ids:
            completed = subprocess.run(
                (
                    str(route.executable),
                    "--print",
                    "Return the required preflight object without using tools.",
                    "--model",
                    model_id,
                    "--output-format",
                    "stream-json",
                    "--verbose",
                    "--json-schema",
                    json.dumps(_preflight_schema(), separators=(",", ":")),
                ),
                check=False,
                capture_output=True,
                text=True,
                timeout=30,
                env=self._environment(),
            )
            if completed.returncode != 0:
                continue
            init: Mapping[str, object] | None = None
            result: Mapping[str, object] | None = None
            for raw in completed.stdout.splitlines():
                if not raw.strip():
                    continue
                event = json.loads(raw)
                if not isinstance(event, Mapping):
                    raise ValueError("Claude emitted a non-object event")
                if event.get("type") == "system" and event.get("subtype") == "init":
                    init = event
                elif event.get("type") == "result":
                    result = event
            if (
                init is None
                or result is None
                or init.get("model") != model_id
                or result.get("is_error") is not False
                or result.get("structured_output") != {"preflight": "ok"}
            ):
                continue
            version = init.get("claude_code_version")
            limit = _reported_context_limit(init)
            if not isinstance(version, str) or not version or limit is None:
                continue
            if observed_version is not None and observed_version != version:
                raise ValueError("Claude version changed during route preflight")
            observed_version = version
            verified.append(model_id)
            limits[model_id] = limit
        if not verified or observed_version is None:
            raise ValueError("Claude authentication and structured output were not verified")
        return tuple(verified), limits, observed_version

    def _environment(self) -> dict[str, str]:
        return {"HOME": str(self.service_home), "PATH": "/usr/bin:/bin"}

    @staticmethod
    def _write_json(process: subprocess.Popen[bytes], value: Mapping[str, object]) -> None:
        if process.stdin is None:
            raise ValueError("tool preflight input is unavailable")
        process.stdin.write((json.dumps(value, separators=(",", ":")) + "\n").encode("utf-8"))
        process.stdin.flush()

    @staticmethod
    def _codex_message(process: subprocess.Popen[bytes]) -> Mapping[str, object]:
        if process.stdout is None:
            raise ValueError("Codex app-server output is unavailable")
        selector = selectors.DefaultSelector()
        try:
            selector.register(process.stdout, selectors.EVENT_READ)
            if not selector.select(30):
                raise ValueError("Codex app-server preflight timed out")
            raw = process.stdout.readline()
        finally:
            selector.close()
        if not raw:
            raise ValueError("Codex app-server closed during preflight")
        value = json.loads(raw)
        if not isinstance(value, Mapping):
            raise ValueError("Codex app-server emitted a non-object message")
        return value

    @classmethod
    def _codex_response(
        cls, process: subprocess.Popen[bytes], request_id: int
    ) -> Mapping[str, object]:
        while True:
            value = cls._codex_message(process)
            if value.get("id") != request_id:
                if "method" in value:
                    continue
                raise ValueError("Codex preflight response identity differs")
            result = value.get("result")
            if "error" in value or not isinstance(result, Mapping):
                raise ValueError("Codex app-server rejected route preflight")
            return result

    @classmethod
    def _codex_turn_completed(
        cls, process: subprocess.Popen[bytes], thread_id: str, turn_id: str
    ) -> bool:
        structured = False
        while True:
            value = cls._codex_message(process)
            params = value.get("params")
            if not isinstance(params, Mapping):
                continue
            if params.get("threadId") != thread_id:
                continue
            if value.get("method") == "item/completed" and params.get("turnId") == turn_id:
                item = params.get("item")
                if isinstance(item, Mapping) and item.get("type") == "agentMessage":
                    try:
                        structured = json.loads(str(item.get("text"))) == {"preflight": "ok"}
                    except json.JSONDecodeError:
                        structured = False
            if value.get("method") == "turn/completed":
                turn = params.get("turn")
                return bool(
                    structured
                    and isinstance(turn, Mapping)
                    and turn.get("id") == turn_id
                    and turn.get("status") == "completed"
                )


def _preflight_schema() -> dict[str, object]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["preflight"],
        "properties": {"preflight": {"const": "ok"}},
    }


def _reported_context_limit(value: Mapping[str, object]) -> int | None:
    for field in ("contextWindow", "context_window", "context_window_tokens"):
        limit = value.get(field)
        if isinstance(limit, int) and not isinstance(limit, bool) and limit > 0:
            return limit
    return None


def _terminate_preflight(process: subprocess.Popen[bytes]) -> None:
    if process.stdin is not None:
        try:
            process.stdin.close()
        except OSError:
            pass
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
    for stream in (process.stdout, process.stderr):
        if stream is not None:
            stream.close()


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
            InstalledToolInspector(str(tool), provider, service_home),
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
    required_github = {"app_id", "installation_id", "app_slug"}
    secret_root = storage_path.parent / "secrets"
    resolver = lambda reference: _read_service_secret(secret_root, reference)
    github_credentials = ServiceGitHubAppCredentials(resolver)
    providers: dict[str, GitHubDestinationProvider] = {}
    git_routes: list[ServiceGitRoute] = []
    remotes: dict[str, str] = {}
    for binding in bindings:
        try:
            profile = profiles[binding.profile_name]
            github = github_profiles[binding.profile_name]
        except KeyError as error:
            raise ValueError(
                f"repository binding references an unknown profile: {binding.binding_id}"
            ) from error
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
        providers[binding.repository] = GitHubDestinationProvider(
            destination_profile, GitHubRestDestinationApi(github_credentials)
        )
        remote = _github_remote(str(api_base_url), binding.repository)
        remotes[binding.repository] = remote
        git_routes.append(
            ServiceGitRoute(
                binding.repository, profile.credential_reference, remote
            )
        )
    destination = GitHubDestinationRouter(providers)
    transport = ServiceGitTransport(
        tuple(git_routes), resolver,
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
        lambda repository: remotes[repository],
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
