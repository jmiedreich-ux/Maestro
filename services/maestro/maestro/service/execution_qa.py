"""Isolated Quality Assurance environment helpers: plan resolution, argument-array setup, support processes and artifact capture.

Nothing here talks to an agent or to SQL. The milestone verification code calls these to build a clean directory
under ``execution.qa.environment_root``, run only the setup that the confirmed plan names (argument arrays or
hash-checked scripts, never agent-supplied shell text), start and health-check declared support processes, and
store evidence beneath ``execution.qa.artifact_root`` with a hash, size and media type.
"""

from __future__ import annotations

import hashlib
import mimetypes
import os
import re
import shutil
import signal
import socket
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import Any, Mapping, Sequence

from maestro.foundation import canonical_json

DEFAULT_SECRET_PATTERNS = (
    r"ghp_[A-Za-z0-9]{20,}", r"github_pat_[A-Za-z0-9_]{20,}", r"sk-[A-Za-z0-9_-]{20,}", r"xox[baprs]-[A-Za-z0-9-]{10,}",
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----", r"AKIA[0-9A-Z]{16}",
)
_STEP_OUTPUT = 2000


class QaError(Exception):
    """A plain reason the verification cannot run or an artifact cannot be kept; the caller records it as UNTESTED."""


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def binding_snapshot(config: Mapping[str, Any], project_id: str) -> tuple[dict[str, Any] | None, str | None]:
    """The operator's non-secret test binding for a project and its SHA-256 (UTF-8 JSON, sorted keys, no extra whitespace)."""
    binding = (config.get("qa") or {}).get("project_bindings", {}).get(project_id)
    if binding is None:
        return None, None
    return binding, sha256_bytes(canonical_json(binding).encode("utf-8"))


def resolve_selection(plan: Mapping[str, Any], config: Mapping[str, Any], project_id: str) -> dict[str, Any]:
    """Check the plan's environment, secret and network selections against the operator's binding; return non-secret evidence.

    A self-contained plan (no selections and no binding hash) needs no binding. Any selection needs the exact saved binding.
    """
    environment_refs = list(plan.get("environment_refs") or [])
    secret_refs = list(plan.get("secret_refs") or [])
    network_refs = list(plan.get("allowed_network_dependencies") or [])
    if not (environment_refs or secret_refs or network_refs or plan.get("project_binding_hash")):
        return {"binding_hash": None, "environments": {}, "secrets": [], "network": []}
    binding, digest = binding_snapshot(config, project_id)
    if binding is None:
        raise QaError("the plan selects project test resources, but the operator has configured no test binding for this project (execution.qa.project_bindings)")
    if plan.get("project_binding_hash") and plan["project_binding_hash"] != digest:
        raise QaError("the operator's current test binding differs from the one the confirmed plan was written against; the plan must be amended and confirmed again")
    variables: dict[str, str] = {}
    for name in environment_refs:
        environment = binding["environments"].get(name)
        if environment is None:
            raise QaError(f"the plan selects test environment {name}, which the operator's binding does not provide")
        overlap = sorted(set(variables) & set(environment["variables"]))
        if overlap:
            raise QaError(f"test environments conflict on variable(s) {', '.join(overlap)}")
        variables.update(environment["variables"])
    for name in secret_refs:
        if name not in binding["secrets"]:
            raise QaError(f"the plan selects test secret {name}, which the operator's binding does not provide")
    for name in network_refs:
        if name not in binding["network_dependencies"]:
            raise QaError(f"the plan selects network destination {name}, which the operator's binding does not allow")
    if secret_refs:
        raise QaError("the plan needs test credentials; injecting them from the service credential store is not available yet, so these checks stay untested")
    return {"binding_hash": digest, "environments": {n: sorted(binding["environments"][n]["variables"]) for n in environment_refs}, "variables": variables,
            "secrets": [], "network": network_refs}


def _resolve_executable(command: Sequence[str]) -> list[str]:
    command = list(command)
    if shutil.which(command[0]) is None and command[0] in {"python", "python3"}:
        command[0] = sys.executable
    return command


def _tail(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[:limit] + f"... [{len(text) - limit} more characters]"


def _environment(env_dir: Path, name: str, variables: Mapping[str, str]) -> dict[str, str]:
    home = env_dir / "home"
    home.mkdir(parents=True, exist_ok=True)
    return {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "HOME": str(home), "LANG": "C.UTF-8", "PYTHONDONTWRITEBYTECODE": "1",
            "MAESTRO_QA_ENVIRONMENT": name, "TMPDIR": str(env_dir / "tmp"), **variables}


def run_setup(plan: Mapping[str, Any], work: Path, env_dir: Path, name: str, variables: Mapping[str, str], timeout: int) -> list[dict[str, Any]]:
    """Run the plan's setup steps in order inside the clean directory. A step that cannot run or fails raises QaError with its result recorded."""
    (env_dir / "tmp").mkdir(parents=True, exist_ok=True)
    results: list[dict[str, Any]] = []
    for step in plan.get("setup_steps") or []:
        command, script = step.get("command"), step.get("script_path")
        if command and not script:
            arguments = _resolve_executable(command)
        elif script and not command:
            path = (work / script).resolve()
            if work.resolve() not in path.parents or not path.is_file():
                raise QaError(f"setup script {script} is not a file inside the milestone source")
            if not step.get("script_sha256") or sha256_bytes(path.read_bytes()) != step["script_sha256"]:
                raise QaError(f"setup script {script} does not match the hash in the confirmed plan")
            arguments = [str(path)]
        else:
            raise QaError(f"setup step '{step.get('subject')}' must give exactly one argument-array command or one hash-checked script")
        if not all(isinstance(a, str) for a in arguments):
            raise QaError(f"setup step '{step.get('subject')}' has a non-text argument")
        started = time.monotonic()
        try:
            done = subprocess.run(arguments, cwd=work, env=_environment(env_dir, name, variables), capture_output=True, text=True, timeout=timeout)
            record = {"subject": step.get("subject"), "command": arguments, "exit_code": done.returncode, "stdout": _tail(done.stdout, _STEP_OUTPUT), "stderr": _tail(done.stderr, _STEP_OUTPUT)}
        except FileNotFoundError:
            record = {"subject": step.get("subject"), "command": arguments, "exit_code": None, "stdout": "", "stderr": f"{arguments[0]}: command not found"}
        except subprocess.TimeoutExpired:
            record = {"subject": step.get("subject"), "command": arguments, "exit_code": None, "stdout": "", "stderr": f"timed out after {timeout} seconds"}
        record["seconds"] = round(time.monotonic() - started, 2)
        results.append(record)
        if record["exit_code"] != 0:
            error = QaError(f"setup step '{step.get('subject')}' failed: {record['stderr'].strip().splitlines()[-1] if record['stderr'].strip() else 'exit ' + str(record['exit_code'])}")
            error.results = results  # type: ignore[attr-defined]
            raise error
    return results


def start_support(plan: Mapping[str, Any], work: Path, env_dir: Path, name: str, variables: Mapping[str, str]) -> list[dict[str, Any]]:
    """Start each declared support process in its own process group and wait for its declared health condition."""
    started: list[dict[str, Any]] = []
    try:
        for entry in plan.get("support_processes") or []:
            command = entry.get("command")
            if not isinstance(command, list) or not command:
                raise QaError(f"support process '{entry.get('subject')}' has no argument-array command")
            log = env_dir / f"support-{len(started) + 1}.log"
            with log.open("wb") as sink:
                process = subprocess.Popen(_resolve_executable(command), cwd=work, env=_environment(env_dir, name, variables), stdout=sink, stderr=subprocess.STDOUT, start_new_session=True)
            record = {"subject": entry.get("subject"), "command": command, "pid": process.pid, "log": str(log), "health": None}
            started.append(record)
            health = entry.get("health_check") or {}
            deadline = time.monotonic() + int(health.get("timeout_seconds", 30))
            while health and True:
                if process.poll() is not None:
                    raise QaError(f"support process '{entry.get('subject')}' exited with {process.returncode} before it became healthy")
                if "port" in health:
                    try:
                        socket.create_connection((health.get("host", "127.0.0.1"), int(health["port"])), 1).close()
                        record["health"] = {"type": "tcp", "port": int(health["port"]), "healthy": True}
                        break
                    except OSError:
                        pass
                elif isinstance(health.get("command"), list) and subprocess.run(_resolve_executable(health["command"]), cwd=work, capture_output=True, timeout=30).returncode == 0:
                    record["health"] = {"type": "command", "healthy": True}
                    break
                else:
                    raise QaError(f"support process '{entry.get('subject')}' declares a health check this service cannot run")
                if time.monotonic() > deadline:
                    raise QaError(f"support process '{entry.get('subject')}' did not become healthy in time")
                time.sleep(0.5)
    except Exception:
        stop_processes(started)
        raise
    return started


def stop_processes(processes: Sequence[Mapping[str, Any]]) -> None:
    for record in processes:
        try:
            os.killpg(int(record["pid"]), signal.SIGTERM)
        except (ProcessLookupError, PermissionError):
            continue
    time.sleep(0.2)
    for record in processes:
        try:
            os.killpg(int(record["pid"]), signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            continue


def clean_environment(env_dir: Path) -> bool:
    """Remove the environment and confirm it is gone; False means it must be quarantined."""
    shutil.rmtree(env_dir, ignore_errors=True)
    return not env_dir.exists()


def scan_secrets(data: bytes, patterns: Sequence[str]) -> str | None:
    text = data.decode("utf-8", errors="ignore")
    for pattern in (*DEFAULT_SECRET_PATTERNS, *patterns):
        if re.search(pattern, text):
            return pattern
    return None


def store_artifact(source: Path, output: Path, destination_dir: Path, patterns: Sequence[str], maximum: int) -> dict[str, Any]:
    """Copy one agent-produced file into service-owned storage: verify it, scan for secrets, hash it and publish it atomically."""
    try:
        resolved = source.resolve(strict=True)
    except (OSError, RuntimeError) as error:
        raise QaError(f"artifact {source.name} does not exist") from error
    if output.resolve() not in resolved.parents or source.is_symlink() or not resolved.is_file():
        raise QaError(f"artifact {source.name} is not a regular file inside the run's output")
    size = resolved.stat().st_size
    if size > maximum:
        raise QaError(f"artifact {source.name} is {size} bytes, over the {maximum} byte limit")
    data = resolved.read_bytes()
    if scan_secrets(data, patterns) is not None:
        raise QaError(f"artifact {source.name} matches a secret pattern and was discarded")
    destination_dir.mkdir(parents=True, exist_ok=True)
    artifact_id = f"artifact-{uuid.uuid4().hex[:12]}"
    temporary = destination_dir / f".{artifact_id}.part"
    temporary.write_bytes(data)
    if temporary.stat().st_size != size:
        temporary.unlink(missing_ok=True)
        raise QaError(f"artifact {source.name} changed size while it was captured")
    final = destination_dir / artifact_id
    os.replace(temporary, final)
    media = mimetypes.guess_type(source.name)[0] or ("text/plain" if _is_text(data) else "application/octet-stream")
    return {"artifact_id": artifact_id, "path": str(final), "sha256": sha256_bytes(data), "size": size, "media_type": media}


def store_bytes(name: str, data: bytes, destination_dir: Path, media_type: str) -> dict[str, Any]:
    """Store service-produced evidence (setup log) the same way as an agent file."""
    destination_dir.mkdir(parents=True, exist_ok=True)
    artifact_id = f"artifact-{uuid.uuid4().hex[:12]}"
    temporary = destination_dir / f".{artifact_id}.part"
    temporary.write_bytes(data)
    final = destination_dir / artifact_id
    os.replace(temporary, final)
    return {"artifact_id": artifact_id, "path": str(final), "sha256": sha256_bytes(data), "size": len(data), "media_type": media_type, "name": name}


def verify_stored(record: Mapping[str, Any]) -> str | None:
    """A plain reason when stored evidence is missing or no longer matches its recorded size and hash; None when intact."""
    path = Path(str(record["path"]))
    if not path.is_file():
        return f"artifact {record['artifact_id']} is missing"
    data = path.read_bytes()
    if len(data) != int(record["size"]) or sha256_bytes(data) != record["sha256"]:
        return f"artifact {record['artifact_id']} no longer matches its recorded hash"
    return None


def _is_text(data: bytes) -> bool:
    try:
        data.decode("utf-8")
        return True
    except UnicodeDecodeError:
        return False
