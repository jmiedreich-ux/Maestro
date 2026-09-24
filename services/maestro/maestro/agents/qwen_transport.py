"""Local Qwen Code print-mode launch and result decoding.

Qwen Code has no structured-output option, so the assignment tells it to write the response to
``output/response.json``. Its stream-json init event carries the running model and version, which
is the identity evidence; the response file is read only after the tool reports a successful result.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from maestro.foundation import canonical_json

from .preflight import ResolvedAgentRoute, RunningToolIdentity
from .transport import (
    AgentAssignment,
    DecodedToolResult,
    TransportError,
    TransportLaunch,
    decode_json_object,
    validate_transport_context,
)
from .workspaces import PreparedWorkspace, ServiceProfileBinding

_PROMPT = (
    "Read assignment.json and perform only that assignment. When finished, write your final answer as one JSON object "
    "that matches the schema in assignment.json field required_response.schema to output/response.json, and then reply done."
)


def entry_point(executable: str) -> Path:
    return Path(executable).with_name("qwen-code") / "cli-entry.js"


class QwenTransport:
    def launch(
        self,
        route: ResolvedAgentRoute,
        assignment: AgentAssignment,
        workspace: PreparedWorkspace,
        profile: ServiceProfileBinding,
        session: object | None = None,
    ) -> TransportLaunch:
        validate_transport_context("qwen", route, assignment, workspace, profile)
        entry = entry_point(route.executable)
        if not entry.is_file():
            raise TransportError("transport_unavailable", "the Qwen Code entry point is unavailable")
        arguments = (
            route.executable, str(entry), "-m", route.requested_model_id, "-o", "stream-json", "-p", _PROMPT, "--yolo",
        )
        sandbox_arguments = workspace.isolated_command(arguments, profile=profile)
        return TransportLaunch(arguments, workspace.egress_command(route.tool, sandbox_arguments), str(workspace.paths.root), sandbox_arguments=sandbox_arguments)

    def decode(self, raw: bytes | str, route: ResolvedAgentRoute, workspace: PreparedWorkspace) -> DecodedToolResult:
        if isinstance(raw, bytes):
            try:
                raw = raw.decode("utf-8")
            except UnicodeDecodeError as error:
                raise TransportError("malformed_output", "Qwen stream is not UTF-8") from error
        identity: RunningToolIdentity | None = None
        session_id: str | None = None
        succeeded = False
        for line in str(raw).splitlines():
            if not line.strip() or not line.lstrip().startswith("{"):
                continue  # the tool prints a plain warning before its stream
            event = decode_json_object(line)
            kind = event.get("type")
            if kind == "system" and event.get("subtype") == "init":
                if identity is not None:
                    raise TransportError("protocol_error", "Qwen initialized more than once")
                model, version = event.get("model"), event.get("qwen_code_version")
                if model != route.requested_model_id:
                    raise TransportError("identity_unverified", "Qwen started a different model")
                if version != route.tool_version:
                    raise TransportError("identity_unverified", "Qwen tool version differs")
                session_id = event.get("session_id") if isinstance(event.get("session_id"), str) else None
                identity = RunningToolIdentity("tool_metadata", route.provider, model, version, route.configuration_hash)
            elif kind == "result":
                if identity is None:
                    raise TransportError("identity_unverified", "Qwen result preceded startup identity")
                if event.get("is_error") is not False:
                    raise TransportError("tool_failure", "Qwen reported a terminal failure")
                succeeded = True
        if identity is None:
            raise TransportError("identity_unverified", "Qwen startup identity is missing")
        if not succeeded:
            raise TransportError("missing_output", "Qwen terminal result is missing")
        try:
            path = workspace.resolve_artifact("output/response.json")
            response = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError, Exception) as error:  # noqa: BLE001 - any unreadable response file is a missing output
            raise TransportError("missing_output", f"output/response.json is missing or invalid: {type(error).__name__}") from error
        if not isinstance(response, Mapping):
            raise TransportError("malformed_output", "the Qwen response must be one JSON object")
        return DecodedToolResult(dict(response), identity, session_id=session_id)
