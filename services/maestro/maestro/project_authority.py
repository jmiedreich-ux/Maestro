"""Production M1 project-authority inventory and persistence orchestration."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

from .git_repository import GitEntryMissing, GitRepositoryError, ReadOnlyGitRepository
from .project_manifest import authority_paths, manifest_leaf_paths, parse_project_manifest
from .storage import SQLiteFoundation


_REPOSITORY = re.compile(r"[^/\s]+/[^/\s]+\Z")
_MAX_BLOB_BYTES = 2 * 1024 * 1024
_MAX_AUTHORITY_BYTES = 16 * 1024 * 1024


@dataclass(frozen=True)
class AuthorityFile:
    path: str
    git_object_id: str
    sha256: str
    byte_length: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "git_object_id": self.git_object_id,
            "sha256": self.sha256,
            "byte_length": self.byte_length,
        }


@dataclass(frozen=True)
class AuthorityFact:
    dotted_path: str
    status: str
    observed_value: Any = None
    observed_values: tuple[Any, ...] | None = None
    reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        value: dict[str, Any] = {"dotted_path": self.dotted_path, "status": self.status}
        if self.observed_value is not None:
            value["observed_value"] = self.observed_value
        if self.observed_values is not None:
            value["observed_values"] = list(self.observed_values)
        if self.reason is not None:
            value["reason"] = self.reason
        return value


@dataclass(frozen=True)
class ProjectAuthorityLoadResult:
    request_id: str
    repository_path: str
    expected_repository: str
    source_revision: str
    source_commit: str
    manifest_path: str
    manifest_digest: str
    normalized_manifest: dict[str, Any]
    authority_files: tuple[AuthorityFile, ...]
    facts: tuple[AuthorityFact, ...]
    summary: dict[str, int]
    disposition: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "repository_path": self.repository_path,
            "expected_repository": self.expected_repository,
            "source_revision": self.source_revision,
            "source_commit": self.source_commit,
            "manifest_path": self.manifest_path,
            "manifest_digest": self.manifest_digest,
            "normalized_manifest": self.normalized_manifest,
            "authority_files": [item.to_dict() for item in self.authority_files],
            "facts": [fact.to_dict() for fact in self.facts],
            "summary": self.summary,
            "disposition": self.disposition,
        }

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "ProjectAuthorityLoadResult":
        return cls(
            request_id=value["request_id"],
            repository_path=value["repository_path"],
            expected_repository=value["expected_repository"],
            source_revision=value["source_revision"],
            source_commit=value["source_commit"],
            manifest_path=value["manifest_path"],
            manifest_digest=value["manifest_digest"],
            normalized_manifest=value["normalized_manifest"],
            authority_files=tuple(AuthorityFile(**item) for item in value["authority_files"]),
            facts=tuple(
                AuthorityFact(
                    dotted_path=fact["dotted_path"],
                    status=fact["status"],
                    observed_value=fact.get("observed_value"),
                    observed_values=tuple(fact["observed_values"]) if "observed_values" in fact else None,
                    reason=fact.get("reason"),
                )
                for fact in value["facts"]
            ),
            summary={key: int(count) for key, count in value["summary"].items()},
            disposition=value["disposition"],
        )


class ProjectAuthorityLoader:
    """Load authority from one Git commit and atomically retain its outcome."""

    def __init__(self, storage: SQLiteFoundation) -> None:
        self.storage = storage

    def load(
        self,
        repository_path: Path,
        source_revision: str,
        expected_repository: str,
        manifest_path: str = "maestro.project.yaml",
    ) -> ProjectAuthorityLoadResult:
        if not isinstance(expected_repository, str) or not _REPOSITORY.fullmatch(expected_repository):
            raise ValueError("expected_repository must have owner/name form")
        _validate_manifest_path(manifest_path)

        repository = ReadOnlyGitRepository(repository_path)
        commit = repository.exact_commit(source_revision)
        manifest_blob = repository.read_blob(commit, manifest_path, maximum_bytes=_MAX_BLOB_BYTES)
        manifest = parse_project_manifest(manifest_blob.content)
        manifest_digest = hashlib.sha256(manifest_blob.content).hexdigest()

        facts = _manifest_facts(manifest, expected_repository)
        authority_files: list[AuthorityFile] = []
        total_bytes = 0
        for path in authority_paths(manifest):
            dotted = f"authority_files.{path}"
            try:
                blob = repository.read_blob(commit, path, maximum_bytes=_MAX_BLOB_BYTES)
            except GitEntryMissing:
                facts.append(AuthorityFact(dotted, "missing", reason="path is absent at source commit"))
                continue
            total_bytes += len(blob.content)
            if total_bytes > _MAX_AUTHORITY_BYTES:
                raise GitRepositoryError("total authority payload exceeds 16777216 bytes")
            descriptor = AuthorityFile(
                path=path,
                git_object_id=blob.object_id,
                sha256=hashlib.sha256(blob.content).hexdigest(),
                byte_length=len(blob.content),
            )
            authority_files.append(descriptor)
            facts.append(AuthorityFact(dotted, "confirmed", observed_value=descriptor.to_dict()))

        identity = manifest.get("identity")
        if isinstance(identity, dict) and isinstance(identity.get("default_branch"), str):
            branch = identity["default_branch"]
            if not repository.branch_contains(branch, commit):
                _replace_fact(
                    facts,
                    "identity.default_branch",
                    AuthorityFact(
                        "identity.default_branch",
                        "conflicting",
                        observed_value=branch,
                        reason="local default-branch ref is missing or does not contain source commit",
                    ),
                )

        counts = {
            status: sum(fact.status == status for fact in facts)
            for status in ("confirmed", "missing", "conflicting")
        }
        disposition = "Reviewable" if counts["missing"] == 0 and counts["conflicting"] == 0 else "Blocked"
        idempotency_key = _idempotency_key(expected_repository, commit, manifest_path, manifest_digest)
        request_id = f"authority-load-{idempotency_key[:32]}"
        result = ProjectAuthorityLoadResult(
            request_id=request_id,
            repository_path=str(repository.path),
            expected_repository=expected_repository,
            source_revision=commit,
            source_commit=commit,
            manifest_path=manifest_path,
            manifest_digest=manifest_digest,
            normalized_manifest=manifest,
            authority_files=tuple(authority_files),
            facts=tuple(facts),
            summary=counts,
            disposition=disposition,
        )
        durable = self.storage.record_project_authority_load(result.to_dict(), idempotency_key)
        return ProjectAuthorityLoadResult.from_dict(durable)


def _manifest_facts(manifest: dict[str, Any], expected_repository: str) -> list[AuthorityFact]:
    facts: list[AuthorityFact] = []
    for dotted in manifest_leaf_paths():
        present, value = _lookup(manifest, dotted)
        if not present:
            facts.append(AuthorityFact(dotted, "missing", reason="required manifest leaf is absent"))
            continue
        if dotted == "identity.repository" and value != expected_repository:
            facts.append(
                AuthorityFact(
                    dotted,
                    "conflicting",
                    observed_values=(value, expected_repository),
                    reason="manifest repository does not match expected repository",
                )
            )
        elif dotted == "delivery.acceptance_authority" and value == "owner":
            facts.append(
                AuthorityFact(
                    dotted,
                    "conflicting",
                    observed_value=value,
                    reason="owner acceptance requires an M0-D15 reserved material return",
                )
            )
        else:
            facts.append(AuthorityFact(dotted, "confirmed", observed_value=value))
    return facts


def _lookup(manifest: dict[str, Any], dotted: str) -> tuple[bool, Any]:
    if "." not in dotted:
        return dotted in manifest, manifest.get(dotted)
    area, leaf = dotted.split(".", 1)
    area_value = manifest.get(area)
    if not isinstance(area_value, dict) or leaf not in area_value:
        return False, None
    return True, area_value[leaf]


def _replace_fact(facts: list[AuthorityFact], dotted: str, replacement: AuthorityFact) -> None:
    for index, fact in enumerate(facts):
        if fact.dotted_path == dotted:
            facts[index] = replacement
            return
    facts.append(replacement)


def _validate_manifest_path(path: str) -> None:
    if (
        not isinstance(path, str)
        or not path
        or path != path.strip()
        or "\\" in path
        or any(ord(character) < 32 or ord(character) == 127 for character in path)
    ):
        raise ValueError("manifest_path must be a repository-relative POSIX path")
    parsed = PurePosixPath(path)
    if parsed.is_absolute() or any(item in {"", ".", "..", ".git"} for item in path.split("/")):
        raise ValueError("manifest_path must be a repository-relative POSIX path")


def _idempotency_key(repository: str, commit: str, path: str, digest: str) -> str:
    canonical = json.dumps([repository, commit, path, digest], separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
