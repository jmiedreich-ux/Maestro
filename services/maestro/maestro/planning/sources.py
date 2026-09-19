"""Exact, read-only registration source selection and inventory."""

from __future__ import annotations

import hashlib
import re
import tempfile
from dataclasses import dataclass
from typing import Iterable

from maestro.foundation.git_read import (
    GitReadError,
    RemoteGitReader,
    RemoteSnapshot,
    run_git,
    validate_object_id,
    validate_repository_path,
)


class SourceIntakeError(ValueError):
    """A selected registration source cannot be read without substitution."""


_FULL_SHA = re.compile(r"[0-9a-f]{40}\Z")
_REF_COMPONENT = re.compile(r"[A-Za-z0-9][A-Za-z0-9._/-]*\Z")


def validate_source_ref(value: object) -> str:
    """Accept only an exact commit or an explicit head/tag reference."""
    if not isinstance(value, str):
        raise SourceIntakeError("source_ref must be text")
    normalized = value.lower() if _FULL_SHA.fullmatch(value.lower()) else value
    if _FULL_SHA.fullmatch(normalized):
        return normalized
    if not normalized.startswith(("refs/heads/", "refs/tags/")):
        raise SourceIntakeError("source_ref must be a full branch, tag, or commit selector")
    suffix = normalized.split("/", 2)[-1]
    if (
        not suffix
        or _REF_COMPONENT.fullmatch(suffix) is None
        or suffix.startswith(("/", "."))
        or suffix.endswith(("/", "."))
        or "//" in suffix
        or ".." in suffix
        or "@{" in suffix
    ):
        raise SourceIntakeError("source_ref is not a supported full Git reference")
    return normalized


@dataclass(frozen=True)
class SourceBlob:
    """One exact regular-file input consumed by registration."""

    path: str
    object_id: str
    sha256: str
    content: bytes

    @classmethod
    def from_bytes(cls, path: str, content: bytes) -> "SourceBlob":
        try:
            path = validate_repository_path(path)
        except GitReadError as error:
            raise SourceIntakeError(str(error)) from error
        if not isinstance(content, bytes):
            raise SourceIntakeError("source content must be bytes")
        git_header = f"blob {len(content)}\0".encode("ascii")
        return cls(
            path,
            hashlib.sha1(git_header + content).hexdigest(),
            hashlib.sha256(content).hexdigest(),
            content,
        )


@dataclass(frozen=True)
class SourceInventory:
    """The saved selector, resolved commit, and immutable input bytes."""

    source_ref: str
    source_commit: str
    overview_path: str
    blobs: tuple[SourceBlob, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "source_ref", validate_source_ref(self.source_ref))
        try:
            object.__setattr__(self, "source_commit", validate_object_id(self.source_commit, "source_commit"))
            object.__setattr__(self, "overview_path", validate_repository_path(self.overview_path))
        except GitReadError as error:
            raise SourceIntakeError(str(error)) from error
        paths = tuple(item.path for item in self.blobs)
        if self.overview_path not in paths:
            raise SourceIntakeError("source inventory does not contain the overview")
        if len(paths) != len(set(paths)):
            raise SourceIntakeError("source inventory paths must be unique")

    def content_for(self, path: str) -> bytes:
        for blob in self.blobs:
            if blob.path == path:
                return blob.content
        raise SourceIntakeError(f"selected source does not contain {path}")


class ExactSourceReader:
    """Resolve one source selector and read only named blobs at that commit.

    Branch reads use the shared remote reader.  Its observed head must equal
    the prior resolution, so a branch move is visible rather than becoming a
    different saved baseline.  Tags and commit selectors are fetched by their
    already resolved commit and never use publication credentials.
    """

    def __init__(self, remote_reader: RemoteGitReader | None = None) -> None:
        self._remote_reader = remote_reader or RemoteGitReader()

    def read(
        self,
        *,
        remote: str,
        source_ref: str,
        overview_path: str,
        referenced_paths: Iterable[str] = (),
    ) -> SourceInventory:
        if not isinstance(remote, str) or not remote or "\x00" in remote:
            raise SourceIntakeError("source repository remote must be nonempty text")
        selector = validate_source_ref(source_ref)
        paths = self._paths(overview_path, referenced_paths)
        commit = self._resolve(remote, selector)
        if selector.startswith("refs/heads/"):
            branch = selector.removeprefix("refs/heads/")
            try:
                snapshot = self._remote_reader.snapshot(remote, branch, paths)
            except GitReadError as error:
                raise SourceIntakeError(str(error)) from error
            if snapshot.head != commit:
                raise SourceIntakeError("source branch moved while intake was reading it")
            return self._from_snapshot(selector, snapshot, overview_path)
        return self._read_exact(remote, selector, commit, overview_path, paths)

    @staticmethod
    def _paths(overview_path: str, referenced_paths: Iterable[str]) -> tuple[str, ...]:
        try:
            overview = validate_repository_path(overview_path)
            references = tuple(validate_repository_path(path) for path in referenced_paths)
        except GitReadError as error:
            raise SourceIntakeError(str(error)) from error
        paths = (overview, *references)
        if len(paths) != len(set(paths)):
            raise SourceIntakeError("overview and referenced source paths must be unique")
        return paths

    @staticmethod
    def _from_snapshot(
        selector: str, snapshot: RemoteSnapshot, overview_path: str
    ) -> SourceInventory:
        missing = [path for path, content in snapshot.files.items() if content is None]
        if missing:
            raise SourceIntakeError(f"selected source does not contain {missing[0]}")
        blobs = tuple(
            SourceBlob.from_bytes(path, content)
            for path, content in snapshot.files.items()
            if content is not None
        )
        return SourceInventory(selector, snapshot.head, overview_path, blobs)

    @staticmethod
    def _resolve(remote: str, selector: str) -> str:
        if _FULL_SHA.fullmatch(selector):
            # A direct commit is verified after fetching below.
            return selector
        result = run_git("ls-remote", "--exit-code", remote, selector, f"{selector}^{{}}")
        if result.returncode != 0:
            raise SourceIntakeError("selected source reference is unavailable")
        entries: dict[str, str] = {}
        try:
            for line in result.stdout.decode("ascii").splitlines():
                object_id, reference = line.split("\t", 1)
                entries[reference] = validate_object_id(object_id, "source reference")
        except (UnicodeDecodeError, ValueError, GitReadError) as error:
            raise SourceIntakeError("selected source reference is invalid") from error
        resolved = entries.get(f"{selector}^{{}}") or entries.get(selector)
        if resolved is None:
            raise SourceIntakeError("selected source reference is unavailable")
        return resolved

    @staticmethod
    def _read_exact(
        remote: str,
        selector: str,
        commit: str,
        overview_path: str,
        paths: tuple[str, ...],
    ) -> SourceInventory:
        with tempfile.TemporaryDirectory(prefix="maestro-source-read-") as temporary:
            initialized = run_git("init", "--bare", "--quiet", temporary)
            fetched = run_git("-C", temporary, "fetch", "--no-tags", "--quiet", remote, commit)
            checked = run_git("-C", temporary, "cat-file", "-e", f"{commit}^{{commit}}")
            if initialized.returncode or fetched.returncode or checked.returncode:
                raise SourceIntakeError("selected source commit is unavailable or is not a commit")
            blobs: list[SourceBlob] = []
            for path in paths:
                listed = run_git("-C", temporary, "ls-tree", "-z", commit, "--", path)
                if listed.returncode or not listed.stdout:
                    raise SourceIntakeError(f"selected source does not contain {path}")
                records = [item for item in listed.stdout.split(b"\0") if item]
                if len(records) != 1:
                    raise SourceIntakeError(f"selected source path is ambiguous: {path}")
                try:
                    metadata, raw_path = records[0].split(b"\t", 1)
                    mode, entry_type, _object_id = metadata.decode("ascii").split(" ")
                    returned_path = raw_path.decode("utf-8")
                except (UnicodeDecodeError, ValueError) as error:
                    raise SourceIntakeError(f"selected source path is invalid: {path}") from error
                if returned_path != path or entry_type != "blob" or mode not in {"100644", "100755"}:
                    raise SourceIntakeError(f"selected source path is not a regular file: {path}")
                content = run_git("-C", temporary, "show", f"{commit}:{path}")
                if content.returncode:
                    raise SourceIntakeError(f"cannot read selected source path: {path}")
                blobs.append(SourceBlob.from_bytes(path, content.stdout))
        return SourceInventory(selector, commit, overview_path, tuple(blobs))
