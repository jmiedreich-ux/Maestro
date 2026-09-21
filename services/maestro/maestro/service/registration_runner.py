"""Systemd-owned registration protocol runner with durable ordered output."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
from pathlib import Path
from typing import Mapping

from maestro.agents.claude_transport import ClaudeTransport
from maestro.agents.codex_transport import CodexConversation
from maestro.agents.preflight import ResolvedAgentRoute, RunningToolIdentity
from maestro.agents.routes import PermittedDestination
from maestro.agents.transport import AgentAssignment, ArtifactReference, decode_json_object
from maestro.agents.workspaces import PreparedWorkspace, WorkspacePaths
from maestro.foundation import canonical_json


def _route(value: Mapping[str, object]) -> ResolvedAgentRoute:
    return ResolvedAgentRoute(
        role=str(value["role"]), tool=str(value["tool"]),
        requested_model_id=str(value["requested_model_id"]),
        provider=str(value["provider"]), tool_version=str(value["tool_version"]),
        executable=str(value["executable"]),
        credential_profile=str(value["credential_profile"]),
        settings_profile=str(value["settings_profile"]), location=str(value["location"]),
        capabilities=tuple(value["capabilities"]),
        context_limit_tokens=int(value["context_limit_tokens"]),
        permitted_destinations=tuple(
            PermittedDestination(str(item["hostname"]), int(item["port"]))
            for item in value["permitted_destinations"]
        ),
        configuration_hash=str(value["configuration_hash"]),
    )


def _assignment(value: Mapping[str, object]) -> AgentAssignment:
    required = value["required_response"]
    assert isinstance(required, Mapping)
    artifacts = value["assigned_artifacts"]
    assert isinstance(artifacts, Mapping)
    return AgentAssignment(
        project_id=str(value["project_id"]), activity_id=str(value["activity_id"]),
        assignment_id=str(value["assignment_id"]), run_id=str(value["run_id"]),
        parent_assignment_id=(
            None if value["parent_assignment_id"] is None
            else str(value["parent_assignment_id"])
        ),
        role=str(value["role"]),
        role_responsibilities=tuple(value["role_responsibilities"]),
        task=str(value["task"]), source_commit=str(value["source_commit"]),
        decision_version=str(value["decision_version"]),
        instructions=value["instructions"],
        permitted_actions=tuple(value["permitted_actions"]),
        writable_locations=tuple(value["writable_locations"]), limits=value["limits"],
        clarification_conditions=tuple(value["clarification_conditions"]),
        response_schema=required["schema"], response_path=str(required["path"]),
        assigned_artifacts={
            str(name): ArtifactReference.from_mapping(item, str(name))
            for name, item in artifacts.items()
        },
    )


def _workspace(value: Mapping[str, object]) -> PreparedWorkspace:
    root = Path(str(value["root"]))
    paths = WorkspacePaths(
        root, root / "source", root / "input", root / "output", root / "scratch",
        root / "assignment.json",
    )
    return PreparedWorkspace(
        str(value["project_id"]), str(value["activity_id"]), str(value["run_id"]),
        str(value["source_commit"]), paths, str(value["assignment_sha256"]), (),
        Path(str(value["isolation_executable"])), Path(str(value["workspace_root"])),
    )


class _Journal:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.lock = threading.Lock()
        self.sequence = 0

    def append(self, kind: str, **data: object) -> None:
        with self.lock:
            self.sequence += 1
            payload = canonical_json({"sequence": self.sequence, "kind": kind, **data}) + "\n"
            descriptor = os.open(
                self.path, os.O_WRONLY | os.O_CREAT | os.O_APPEND | os.O_NOFOLLOW, 0o600
            )
            try:
                os.write(descriptor, payload.encode("utf-8"))
                os.fsync(descriptor)
            finally:
                os.close(descriptor)


def _identity(identity: RunningToolIdentity) -> dict[str, str]:
    return {
        "source": identity.source, "provider": identity.provider,
        "model_id": identity.model_id, "tool_version": identity.tool_version,
        "configuration_hash": identity.configuration_hash,
    }


def run(plan_path: Path) -> int:
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    route = _route(plan["route"])
    assignment = _assignment(plan["assignment"])
    workspace = _workspace(plan["workspace"])
    event_path = Path(plan["event_path"])
    result_path = Path(plan["result_path"])
    journal = _Journal(event_path)
    process = subprocess.Popen(
        tuple(plan["command"]), cwd=str(plan["cwd"]), stdin=subprocess.PIPE,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    assert process.stdin is not None and process.stdout is not None and process.stderr is not None

    def drain_stderr() -> None:
        for line in iter(process.stderr.readline, b""):
            journal.append("stderr", data=line.decode("utf-8", "replace"))

    stderr_thread = threading.Thread(target=drain_stderr, daemon=True)
    stderr_thread.start()
    identity: RunningToolIdentity | None = None
    try:
        if route.tool == "codex":
            conversation = CodexConversation.replay(route, assignment, workspace)
            for value in plan["initial_stdin"]:
                process.stdin.write(str(value).encode("utf-8"))
            process.stdin.flush()
            while conversation.state != "completed":
                line = process.stdout.readline()
                if not line:
                    raise RuntimeError("Codex closed before returning a complete result")
                journal.append("stdout", data=line.decode("utf-8", "replace"))
                outgoing = conversation.receive(line)
                if identity is None and conversation.runtime_identity is not None:
                    identity = conversation.runtime_identity
                    journal.append("runtime_identity", identity=_identity(identity))
                for value in outgoing:
                    process.stdin.write(value)
                process.stdin.flush()
            decoded = conversation.result()
        else:
            chunks: list[bytes] = []
            for line in iter(process.stdout.readline, b""):
                journal.append("stdout", data=line.decode("utf-8", "replace"))
                chunks.append(line)
                event = decode_json_object(line)
                if identity is None and event.get("type") == "system" and event.get("subtype") == "init":
                    identity = RunningToolIdentity(
                        "tool_metadata", route.provider, str(event["model"]),
                        str(event["claude_code_version"]), route.configuration_hash,
                    )
                    journal.append("runtime_identity", identity=_identity(identity))
            decoded = ClaudeTransport().decode(b"".join(chunks), route)
        process.stdin.close()
        code = process.wait()
        stderr_thread.join(timeout=1)
        process.stdout.close()
        process.stderr.close()
        if code != 0:
            raise RuntimeError(f"registration tool exited with status {code}")
        temporary = result_path.with_suffix(".new")
        result_bytes = canonical_json({
            "response": dict(decoded.response), "identity": _identity(decoded.identity)
        }).encode("utf-8")
        descriptor = os.open(
            temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW, 0o600
        )
        try:
            os.write(descriptor, result_bytes)
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        os.replace(temporary, result_path)
        journal.append("result_saved")
        return 0
    except Exception as error:
        journal.append("runner_failure", error=f"{type(error).__name__}: {error}")
        if process.poll() is None:
            process.terminate()
            process.wait(timeout=5)
        for stream in (process.stdin, process.stdout, process.stderr):
            if stream is not None and not stream.closed:
                stream.close()
        return 1


def main() -> int:
    if len(sys.argv) != 2:
        return 2
    return run(Path(sys.argv[1]))


if __name__ == "__main__":
    raise SystemExit(main())
