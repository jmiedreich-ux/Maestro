"""Real installed-tool inspection for the two supported agent routes.

Codex reports its exact model catalog through its app server. Claude Code has
no catalog, so its exact model is enforced with ``--model`` and verified again
from the tool's own startup metadata on every run (see the transports).
"""

from __future__ import annotations

import hashlib
import json
import os
import selectors
import subprocess
import time
from pathlib import Path
from typing import Mapping

from .preflight import (
    AdapterObservation,
    AgentRoutePreflight,
    InstalledAdapter,
    ResolvedAgentRoute,
)
from .routes import AgentRouteRegistry, RouteRequirements, ToolModelSelection, ToolRoute
from .workspaces import ServiceProfileBinding

CAPABILITIES = ("approved_network", "code_edit", "local_command", "repository_search")
# Declared context windows; a run's own readings replace these when a tool reports them.
CONTEXT_LIMITS = {"codex": 272000, "claude_code": 200000, "qwen": 65536}
REQUIREMENTS = RouteRequirements(CAPABILITIES, ("cloud",), 100000)
# The local coder route runs on the AI box with the same edit and command capabilities but no cloud network access.
QWEN_CAPABILITIES = ("code_edit", "local_command", "repository_search")
LOCAL_REQUIREMENTS = RouteRequirements(QWEN_CAPABILITIES, ("local_ai_box",), 8000)
_PROFILE_FILES = {
    "codex": (".codex/auth.json",),
    "claude_code": (".claude.json", ".claude/.credentials.json"),
    "qwen": (".qwen/settings.json",),
}


def _version(executable: Path, home: Path, tool: str = "") -> str | None:
    command = [str(executable), "--version"]
    if tool == "qwen":
        command = [str(executable), str(executable.with_name("qwen-code") / "cli-entry.js"), "--version"]
    try:
        done = subprocess.run(
            command, capture_output=True, text=True, timeout=20, check=False,
            env={"PATH": "/usr/bin:/bin", "HOME": str(home)},
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    words = done.stdout.split()
    return next((word for word in words if word[:1].isdigit()), None) if done.returncode == 0 else None


def _codex_models(executable: Path, home: Path) -> tuple[str, ...] | None:
    messages = (
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"clientInfo": {"name": "maestro", "version": "1"}, "capabilities": {"experimentalApi": False}}},
        {"jsonrpc": "2.0", "method": "initialized", "params": {}},
        {"jsonrpc": "2.0", "id": 2, "method": "model/list", "params": {}},
    )
    process = subprocess.Popen(
        [str(executable), "app-server"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
        env={"PATH": "/usr/bin:/bin", "HOME": str(home)},
    )
    try:
        assert process.stdin and process.stdout
        process.stdin.write(("".join(json.dumps(m) + "\n" for m in messages)).encode())
        process.stdin.flush()
        selector = selectors.DefaultSelector()
        selector.register(process.stdout, selectors.EVENT_READ)
        buffer, deadline = b"", time.monotonic() + 30
        while time.monotonic() < deadline:
            if not selector.select(timeout=1):
                continue
            chunk = os.read(process.stdout.fileno(), 1 << 20)
            if not chunk:
                return None
            buffer += chunk
            while b"\n" in buffer:
                line, buffer = buffer.split(b"\n", 1)
                try:
                    message = json.loads(line)
                except ValueError:
                    continue
                if message.get("id") == 2:
                    data = (message.get("result") or {}).get("data")
                    if not isinstance(data, list):
                        return None
                    return tuple(m["id"] for m in data if isinstance(m, dict) and m.get("id") == m.get("model"))
        return None
    finally:
        process.kill()
        process.wait()


class InstalledInspector:
    """Observe the installed tool for one route without starting agent work."""

    def __init__(self, tool: str, provider: str, home: Path) -> None:
        self.tool, self.provider, self.home = tool, provider, home

    def inspect(self, route: ToolRoute, configuration_hash: str) -> AdapterObservation:
        version = _version(route.executable, self.home, self.tool)
        if version is None:
            return _unavailable("the tool did not report a version")
        if self.tool == "qwen":
            return self._qwen(route, version, configuration_hash)
        if self.tool == "codex":
            models = _codex_models(route.executable, self.home)
            if models is None:
                return _unavailable("the Codex model catalog could not be read")
        else:
            models = route.allowed_model_ids
        return AdapterObservation(
            True, version, self.provider, tuple(models), (), CAPABILITIES, "cloud",
            {model: CONTEXT_LIMITS[self.tool] for model in models}, True,
            route.credential_profile, route.settings_profile, True, True, True, configuration_hash,
        )

    def _qwen(self, route: ToolRoute, version: str, configuration_hash: str) -> AdapterObservation:
        served = _served_models(route)
        if served is None:
            return _unavailable("the local model server is not reachable")
        models = tuple(model for model in route.allowed_model_ids if model in served)
        if not models:
            return _unavailable("the configured local model is not installed on the local server")
        return AdapterObservation(
            True, version, self.provider, models, (), QWEN_CAPABILITIES, "local_ai_box",
            {model: CONTEXT_LIMITS["qwen"] for model in models}, True,
            route.credential_profile, route.settings_profile, True, True, True, configuration_hash,
        )


def _served_models(route: ToolRoute) -> set[str] | None:
    """Model names the configured local server reports, or None when it cannot be reached."""
    import urllib.request

    for destination in route.permitted_destinations:
        try:
            with urllib.request.urlopen(f"http://{destination.hostname}:{destination.port}/api/tags", timeout=10) as reply:
                return {str(m.get("name")) for m in json.loads(reply.read()).get("models", []) if isinstance(m, dict)}
        except (OSError, ValueError):
            continue
    return None


def _unavailable(reason: str) -> AdapterObservation:
    return AdapterObservation(False, None, None, (), (), (), None, {}, False, None, None, False, False, False, None, reason)


def installed_resolvers(tools: Mapping[str, object], service_home: Path):
    """Route and profile resolvers backed by the installed tools and configured routes."""
    registry = AgentRouteRegistry.from_mapping(tools)

    def fingerprint(tool: str):
        def compute(profile: str) -> str | None:
            digest = hashlib.sha256(profile.encode())
            for name in _PROFILE_FILES[tool]:
                path = service_home / name
                if not path.is_file():
                    return None
                digest.update(name.encode())
            return digest.hexdigest()
        return compute

    def settings(profile: str) -> str:
        return hashlib.sha256(profile.encode()).hexdigest()

    preflights: dict[str, AgentRoutePreflight] = {}
    for tool, provider in (("codex", "openai"), ("claude_code", "anthropic"), ("qwen", "ollama")):
        if tool not in registry._routes:
            continue
        local = tool == "qwen"
        preflights[tool] = AgentRoutePreflight(
            registry,
            {tool: (InstalledAdapter(tool, provider, "local_ai_box" if local else "cloud", QWEN_CAPABILITIES if local else CAPABILITIES), InstalledInspector(tool, provider, service_home))},
            credential_fingerprint=fingerprint(tool),
            settings_fingerprint=settings,
        )

    def route_resolver(role: str, tool: str, model_id: str) -> ResolvedAgentRoute:
        if tool not in preflights:
            raise AgentRouteError("adapter_not_installed", f"adapter is not installed: {tool}")
        return preflights[tool].resolve(role, ToolModelSelection(tool, model_id), LOCAL_REQUIREMENTS if tool == "qwen" else REQUIREMENTS)

    def profile_resolver(route: ResolvedAgentRoute) -> ServiceProfileBinding:
        return ServiceProfileBinding(route.tool, route.credential_profile, route.settings_profile, service_home)

    return route_resolver, profile_resolver
