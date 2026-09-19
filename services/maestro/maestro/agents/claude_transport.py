"""Claude Code print-mode launch and stream-json result decoding."""

from __future__ import annotations

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


class ClaudeTransport:
    def launch(
        self,
        route: ResolvedAgentRoute,
        assignment: AgentAssignment,
        workspace: PreparedWorkspace,
        profile: ServiceProfileBinding,
    ) -> TransportLaunch:
        validate_transport_context("claude_code", route, assignment, workspace, profile)
        arguments = (
            route.executable,
            "--print",
            "Read assignment.json and perform only that assignment.",
            "--model",
            route.requested_model_id,
            "--output-format",
            "stream-json",
            "--verbose",
            "--json-schema",
            canonical_json(assignment.response_schema),
            "--allowedTools",
            "Read",
            "Write",
            "--permission-mode",
            "acceptEdits",
        )
        sandbox_arguments = workspace.isolated_command(arguments, profile=profile)
        return TransportLaunch(
            arguments,
            workspace.egress_command(route.tool, sandbox_arguments),
            str(workspace.paths.root),
            sandbox_arguments=sandbox_arguments,
        )

    def decode(
        self,
        raw: bytes | str,
        route: ResolvedAgentRoute,
    ) -> DecodedToolResult:
        if isinstance(raw, bytes):
            try:
                raw = raw.decode("utf-8")
            except UnicodeDecodeError as error:
                raise TransportError("malformed_output", "Claude stream is not UTF-8") from error
        if not isinstance(raw, str):
            raise TransportError("malformed_output", "Claude stream is invalid")
        identity: RunningToolIdentity | None = None
        session_id: str | None = None
        response: Mapping[str, Any] | None = None
        saw_result = False
        for line in raw.splitlines():
            if not line.strip():
                continue
            event = decode_json_object(line)
            if saw_result:
                raise TransportError("protocol_error", "Claude emitted data after its result")
            event_type = event.get("type")
            if event_type == "system" and event.get("subtype") == "init":
                if identity is not None:
                    raise TransportError("protocol_error", "Claude initialized more than once")
                session_id = _text(event.get("session_id"), "session_id")
                model = _text(event.get("model"), "model")
                if model != route.requested_model_id:
                    raise TransportError("identity_unverified", "Claude started a different model")
                version = _text(event.get("claude_code_version"), "claude_code_version")
                if version != route.tool_version:
                    raise TransportError("identity_unverified", "Claude tool version differs")
                identity = RunningToolIdentity(
                    "tool_metadata",
                    route.provider,
                    model,
                    version,
                    route.configuration_hash,
                )
            elif event_type == "result":
                if identity is None:
                    raise TransportError("identity_unverified", "Claude result preceded startup identity")
                saw_result = True
                if event.get("is_error") is not False:
                    raise TransportError("tool_failure", "Claude reported a terminal failure")
                structured = event.get("structured_output")
                if not isinstance(structured, Mapping):
                    raise TransportError("missing_output", "Claude result has no structured output")
                response = dict(structured)
        if identity is None:
            raise TransportError("identity_unverified", "Claude startup identity is missing")
        if response is None:
            raise TransportError("missing_output", "Claude terminal result is missing")
        return DecodedToolResult(response, identity, session_id=session_id)


def _text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise TransportError("protocol_error", f"Claude {field} is invalid")
    return value
