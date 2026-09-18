"""Codex app-server launch and bounded JSON-RPC conversation handling."""

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
from .workspaces import PreparedWorkspace


class CodexTransport:
    def open(
        self,
        route: ResolvedAgentRoute,
        assignment: AgentAssignment,
        workspace: PreparedWorkspace,
    ) -> "CodexConversation":
        validate_transport_context("codex", route, assignment, workspace)
        return CodexConversation(route, assignment, workspace)


class CodexConversation:
    """One fresh Codex app-server conversation; process ownership stays external."""

    def __init__(
        self,
        route: ResolvedAgentRoute,
        assignment: AgentAssignment,
        workspace: PreparedWorkspace,
    ) -> None:
        self.route = route
        self.assignment = assignment
        self.workspace = workspace
        self.state = "initialize"
        self.thread_id: str | None = None
        self.turn_id: str | None = None
        self._server_version: str | None = None
        self._response: Mapping[str, Any] | None = None
        self._identity: RunningToolIdentity | None = None
        initial = _request(
            1,
            "initialize",
            {
                "clientInfo": {"name": "maestro", "version": "1"},
                "capabilities": {"experimentalApi": False},
            },
        )
        tool_arguments = (route.executable, "app-server")
        self.launch = TransportLaunch(
            tool_arguments,
            workspace.isolated_command(tool_arguments),
            str(workspace.paths.root),
            (_line(initial),),
        )

    def receive(self, raw: bytes | str) -> tuple[bytes, ...]:
        message = decode_json_object(raw)
        if "method" in message and self.state in {"initialize", "models", "thread", "turn"}:
            # The installed app server may interleave lifecycle/status notifications
            # before the correlated response that advances this conversation.
            return ()
        if self.state == "initialize":
            result = self._expect_result(message, 1)
            user_agent = result.get("userAgent")
            if (
                not isinstance(user_agent, str)
                or not user_agent
                or self.route.tool_version not in user_agent
            ):
                raise TransportError("identity_unverified", "Codex server identity is missing")
            self._server_version = self.route.tool_version
            self.state = "models"
            return (
                _line({"jsonrpc": "2.0", "method": "initialized", "params": {}}),
                _line(_request(2, "model/list", {})),
            )
        if self.state == "models":
            result = self._expect_result(message, 2)
            models = result.get("data")
            if not isinstance(models, list):
                raise TransportError("protocol_error", "Codex model catalog is invalid")
            selected = [
                value
                for value in models
                if isinstance(value, Mapping)
                and value.get("id") == self.route.requested_model_id
                and value.get("model") == self.route.requested_model_id
            ]
            if len(selected) != 1:
                raise TransportError("model_mismatch", "Codex exact model is absent or an alias")
            self.state = "thread"
            return (
                _line(
                    _request(
                        3,
                        "thread/start",
                        {
                            "model": self.route.requested_model_id,
                            "cwd": str(self.workspace.paths.root),
                            "approvalPolicy": "never",
                            "sandbox": "workspace-write",
                        },
                    )
                ),
            )
        if self.state == "thread":
            result = self._expect_result(message, 3)
            thread = result.get("thread")
            if not isinstance(thread, Mapping):
                raise TransportError("protocol_error", "Codex did not return a thread")
            if (
                result.get("model") != self.route.requested_model_id
                or result.get("modelProvider") != self.route.provider
            ):
                raise TransportError("identity_unverified", "Codex started a different model route")
            self.thread_id = _identifier(thread.get("id"), "thread")
            assert self._server_version is not None
            self._identity = RunningToolIdentity(
                "tool_metadata",
                self.route.provider,
                self.route.requested_model_id,
                self._server_version,
                self.route.configuration_hash,
            )
            self.state = "turn"
            return (
                _line(
                    _request(
                        4,
                        "turn/start",
                        {
                            "threadId": self.thread_id,
                            "input": [
                                {
                                    "type": "text",
                                    "text": "Read assignment.json and perform only that assignment.",
                                }
                            ],
                            "outputSchema": dict(self.assignment.response_schema),
                        },
                    )
                ),
            )
        if self.state == "turn":
            result = self._expect_result(message, 4)
            turn = result.get("turn")
            if not isinstance(turn, Mapping):
                raise TransportError("protocol_error", "Codex did not return a turn")
            self.turn_id = _identifier(turn.get("id"), "turn")
            self.state = "running"
            return ()
        if self.state == "running":
            method = message.get("method")
            params = message.get("params")
            if not isinstance(params, Mapping):
                raise TransportError("protocol_error", "Codex event parameters are invalid")
            if method == "item/completed":
                self._correlate_item(params)
                item = params.get("item")
                if not isinstance(item, Mapping) or item.get("type") != "agentMessage":
                    return ()
                if self._response is not None:
                    raise TransportError("protocol_error", "Codex returned multiple final messages")
                self._response = decode_json_object(item.get("text"))
                return ()
            if method == "turn/completed":
                if params.get("threadId") != self.thread_id:
                    raise TransportError("stale_output", "Codex event belongs to another thread")
                turn = params.get("turn")
                if not isinstance(turn, Mapping) or turn.get("id") != self.turn_id:
                    raise TransportError("stale_output", "Codex event belongs to another turn")
                if turn.get("status") != "completed":
                    raise TransportError("tool_failure", "Codex turn did not complete successfully")
                if self._response is None or self._identity is None:
                    raise TransportError("missing_output", "Codex turn completed without structured output")
                self.state = "completed"
                return ()
            return ()
        raise TransportError("protocol_error", "Codex emitted data after terminal completion")

    def result(self) -> DecodedToolResult:
        if self.state != "completed" or self._response is None or self._identity is None:
            raise TransportError("result_unavailable", "Codex result is not complete")
        return DecodedToolResult(
            self._response,
            self._identity,
            thread_id=self.thread_id,
            turn_id=self.turn_id,
        )

    @staticmethod
    def _expect_result(message: Mapping[str, Any], request_id: int) -> Mapping[str, Any]:
        if message.get("jsonrpc") not in {None, "2.0"} or message.get("id") != request_id:
            raise TransportError("protocol_error", "Codex response correlation is invalid")
        if "error" in message:
            raise TransportError("tool_failure", "Codex app server returned an error")
        result = message.get("result")
        if not isinstance(result, Mapping):
            raise TransportError("protocol_error", "Codex response result is invalid")
        return result

    def _correlate_item(self, params: Mapping[str, Any]) -> None:
        if params.get("threadId") != self.thread_id or params.get("turnId") != self.turn_id:
            raise TransportError("stale_output", "Codex event belongs to another thread or turn")


def _request(request_id: int, method: str, params: Mapping[str, Any]) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "method": method, "params": dict(params)}


def _line(value: Mapping[str, Any]) -> bytes:
    return (canonical_json(value) + "\n").encode("utf-8")


def _identifier(value: object, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise TransportError("protocol_error", f"Codex {field} identity is invalid")
    return value
