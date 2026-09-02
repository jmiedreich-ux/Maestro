from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Iterator

import yaml

from maestro.config import DEFAULT_RUNTIME_DIR, RuntimeConfig
from maestro.storage import SQLiteFoundation


def complete_manifest() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "identity": {
            "project_id": "example-project",
            "name": "Example Project",
            "repository": "owner/example-project",
            "default_branch": "main",
            "adapter_version": "maestro-project-v1",
            "process_version": "maestro-m1",
        },
        "authority": {
            "architecture_paths": ["docs/architecture/project-foundation.md"],
            "plan_paths": ["docs/planning/work-graph.yaml"],
            "work_graph_path": "docs/planning/work-graph.yaml",
            "handoff_path": "ai/handoffs/current.md",
            "rules_sop_path": "AGENTS.md",
            "task_issue_convention": "github-issues",
        },
        "delivery": {
            "branch_policy": "feature-branch",
            "pull_request_policy": "draft-required",
            "merge_policy": "no-automatic-merge",
            "acceptance_authority": "project-architect",
            "deployment_policy": "none",
            "rollback_policy": "revert-commit",
        },
        "verification": {
            "build_commands": [],
            "test_commands": [],
            "integration_commands": [],
            "ui_qa_commands": [],
            "evidence_rules": "record-command-output",
            "untested_handling": "explicit-untested-with-impact",
        },
        "routing": {
            "specialist_overlays": [],
            "worker_routes": [],
            "integration_route": "integration-agent",
            "independent_reviewer_route": "independent-implementation-reviewer",
            "qa_murphy_policy": "disabled",
        },
        "operations": {
            "environment_references": [],
            "secret_references": [],
            "resource_locks": [],
            "notification_policy": "local-durable-only",
        },
        "exceptions": {"disposition": "none", "items": []},
    }


def dump_manifest(manifest: dict[str, Any]) -> bytes:
    return yaml.safe_dump(manifest, sort_keys=False).encode("utf-8")


class TemporaryProjectRepository:
    def __init__(self, manifest: dict[str, Any] | None = None) -> None:
        self._temporary = tempfile.TemporaryDirectory()
        self.path = Path(self._temporary.name)
        run_git(self.path, "init", "-b", "main")
        run_git(self.path, "config", "user.name", "Maestro Test")
        run_git(self.path, "config", "user.email", "maestro@example.invalid")
        self.write_manifest(complete_manifest() if manifest is None else manifest)
        self.write_authority_files()
        run_git(self.path, "add", ".")
        run_git(self.path, "commit", "-m", "initial authority")

    @property
    def commit(self) -> str:
        return run_git(self.path, "rev-parse", "HEAD").stdout.strip()

    def write_manifest(self, manifest: dict[str, Any] | bytes) -> None:
        raw = manifest if isinstance(manifest, bytes) else dump_manifest(manifest)
        (self.path / "maestro.project.yaml").write_bytes(raw)

    def write_authority_files(self) -> None:
        files = {
            "docs/architecture/project-foundation.md": b"# Architecture\n",
            "docs/planning/work-graph.yaml": b"nodes: []\n",
            "ai/handoffs/current.md": b"# Handoff\n",
            "AGENTS.md": b"# Rules\n",
        }
        for relative, content in files.items():
            target = self.path / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)

    def commit_all(self, message: str = "change") -> str:
        run_git(self.path, "add", ".")
        run_git(self.path, "commit", "-m", message)
        return self.commit

    def close(self) -> None:
        self._temporary.cleanup()


class RuntimeDirectory:
    def __init__(self) -> None:
        DEFAULT_RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
        self._temporary = tempfile.TemporaryDirectory(dir=DEFAULT_RUNTIME_DIR)
        self.path = Path(self._temporary.name) / "runtime"

    def foundation(self) -> SQLiteFoundation:
        return SQLiteFoundation(RuntimeConfig.from_runtime_dir(self.path))

    def close(self) -> None:
        self._temporary.cleanup()


def run_git(path: Path, *arguments: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(path), *arguments],
        capture_output=True,
        text=True,
        check=check,
    )


def repository_snapshot(path: Path) -> dict[str, Any]:
    git_dir = Path(run_git(path, "rev-parse", "--absolute-git-dir").stdout.strip())
    index = git_dir / "index"
    config = git_dir / "config"
    return {
        "status": run_git(path, "status", "--porcelain=v2", "--untracked-files=all").stdout,
        "refs": run_git(path, "show-ref").stdout,
        "head": run_git(path, "symbolic-ref", "-q", "HEAD").stdout,
        "index": hashlib.sha256(index.read_bytes()).hexdigest() if index.exists() else None,
        "config": hashlib.sha256(config.read_bytes()).hexdigest() if config.exists() else None,
        "worktree": _worktree_digest(path, git_dir),
    }


def _worktree_digest(path: Path, git_dir: Path) -> str:
    records: list[tuple[str, str]] = []
    for item in sorted(path.rglob("*")):
        if item == git_dir or git_dir in item.parents or item.is_dir():
            continue
        relative = item.relative_to(path).as_posix()
        if item.is_symlink():
            records.append((relative, f"symlink:{item.readlink()}"))
        else:
            records.append((relative, hashlib.sha256(item.read_bytes()).hexdigest()))
    return hashlib.sha256(json.dumps(records, separators=(",", ":")).encode()).hexdigest()


def without_leaf(manifest: dict[str, Any], dotted: str) -> dict[str, Any]:
    changed = copy.deepcopy(manifest)
    if "." not in dotted:
        del changed[dotted]
    else:
        area, leaf = dotted.split(".", 1)
        del changed[area][leaf]
    return changed
