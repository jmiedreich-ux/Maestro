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
class SourceReference:
    """An authoritative source location named by the overview."""

    source_type: str
    subject: str
    path: str


@dataclass(frozen=True)
class OutcomeReference:
    """One ordered, versioned outcome retained from a declaration."""

    declaration: str
    declaration_version: int
    milestone: str
    subject: str
    version: int


@dataclass(frozen=True)
class SourceInventory:
    """The saved selector, resolved commit, and immutable input bytes."""

    source_ref: str
    source_commit: str
    overview_path: str
    blobs: tuple[SourceBlob, ...]
    source_references: tuple[SourceReference, ...] = ()
    outcomes: tuple[OutcomeReference, ...] = ()

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

    @staticmethod
    def default_branch(remote: str) -> str:
        """Return the one advertised default branch without choosing a fallback."""
        result = run_git("ls-remote", "--symref", remote, "HEAD")
        if result.returncode:
            raise SourceIntakeError("source repository has no readable default branch")
        try:
            lines = result.stdout.decode("ascii").splitlines()
            reference = next(line.split("\t", 1)[0][5:] for line in lines if line.startswith("ref: ") and line.endswith("\tHEAD"))
        except (UnicodeDecodeError, StopIteration, ValueError) as error:
            raise SourceIntakeError("source repository has no readable default branch") from error
        return validate_source_ref(reference)

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

    def read_registration(
        self,
        *,
        remote: str,
        source_ref: str,
        overview_path: str,
        referenced_paths: Iterable[str] = (),
    ) -> SourceInventory:
        """Read an overview and exactly its declared architecture/declarations.

        Callers cannot add a conflicting second list of authority documents.
        The overview is resolved once; all later reads use its fixed commit.
        """
        first = self.read(
            remote=remote,
            source_ref=source_ref,
            overview_path=overview_path,
        )
        references = _parse_overview_references(first.content_for(first.overview_path))
        declared_paths = tuple(reference.path for reference in references)
        supplied = tuple(referenced_paths)
        if supplied and supplied != declared_paths:
            raise SourceIntakeError("overview references contradict supplied source locations")
        inventory = self._read_exact(
            remote,
            first.source_ref,
            first.source_commit,
            first.overview_path,
            (first.overview_path, *declared_paths),
        )
        architecture = tuple(item for item in references if item.source_type == "Architecture")
        declarations = tuple(
            item for item in references if item.source_type == "Milestone declaration"
        )
        if len(architecture) != 1 or not declarations:
            raise SourceIntakeError(
                "overview must name one architecture and at least one milestone declaration"
            )
        outcomes = tuple(
            outcome
            for declaration in declarations
            for outcome in _parse_declaration(
                declaration,
                inventory.content_for(declaration.path),
                architecture[0].path,
            )
        )
        if not outcomes:
            raise SourceIntakeError("authoritative declarations contain no milestones")
        return SourceInventory(
            inventory.source_ref,
            inventory.source_commit,
            inventory.overview_path,
            inventory.blobs,
            references,
            outcomes,
        )

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


def _parse_overview_references(content: bytes) -> tuple[SourceReference, ...]:
    rows = _table_rows(content, "Authoritative sources")
    references: list[SourceReference] = []
    for row in rows:
        if len(row) != 3 or row[0] not in {"Architecture", "Milestone declaration"}:
            raise SourceIntakeError("overview authoritative sources table is invalid")
        references.append(SourceReference(row[0], row[1], _location_path(row[2])))
    if len({item.path for item in references}) != len(references):
        raise SourceIntakeError("overview authoritative source locations must be unique")
    return tuple(references)


def _parse_declaration(
    reference: SourceReference, content: bytes, architecture_path: str
) -> tuple[OutcomeReference, ...]:
    identity = {row[0]: row[1] for row in _table_rows(content, "Declaration identity") if len(row) == 2}
    declaration = identity.get("Declaration")
    version = _positive_version(identity.get("Declaration version"), "declaration version")
    if not declaration or declaration != reference.subject:
        raise SourceIntakeError("declaration identity contradicts the overview")
    architecture = identity.get("Architecture source")
    if architecture is None or _location_path(architecture) != architecture_path:
        raise SourceIntakeError("declaration architecture source contradicts the overview")
    outcomes: list[OutcomeReference] = []
    expected_position = 1
    for row in _table_rows(content, "Milestones and order"):
        if len(row) != 4:
            raise SourceIntakeError("declaration milestone order table is invalid")
        try:
            position = int(row[0])
        except ValueError as error:
            raise SourceIntakeError("declaration milestone position is invalid") from error
        if position != expected_position:
            raise SourceIntakeError("declaration milestone positions must be ordered")
        expected_position += 1
        milestone, subject = _qualified_subject(row[1], "milestone")
        outcomes.append(
            OutcomeReference(
                declaration,
                version,
                milestone,
                subject,
                _positive_version(row[2], "milestone version"),
            )
        )
    return tuple(outcomes)


def _table_rows(content: bytes, heading: str) -> tuple[tuple[str, ...], ...]:
    try:
        lines = content.decode("utf-8").splitlines()
    except UnicodeDecodeError as error:
        raise SourceIntakeError("authoritative source must be UTF-8 Markdown") from error
    marker = f"## {heading}"
    try:
        start = lines.index(marker) + 1
    except ValueError as error:
        raise SourceIntakeError(f"source is missing the {heading} section") from error
    rows: list[tuple[str, ...]] = []
    for line in lines[start:]:
        if line.startswith("## "):
            break
        if not line.startswith("|"):
            continue
        cells = tuple(cell.strip() for cell in line.strip().strip("|").split("|"))
        if all(cell and set(cell) <= {"-", ":"} for cell in cells):
            continue
        if cells and cells[0] in {
            "Source type",
            "Field",
            "Position",
        }:
            continue
        rows.append(cells)
    if not rows:
        raise SourceIntakeError(f"source has no {heading} entries")
    return tuple(rows)


def _location_path(value: str) -> str:
    try:
        return validate_repository_path(value.split("#", 1)[0])
    except GitReadError as error:
        raise SourceIntakeError(str(error)) from error


def _positive_version(value: str | None, field: str) -> int:
    try:
        version = int(value or "")
    except ValueError as error:
        raise SourceIntakeError(f"{field} must be a positive integer") from error
    if version <= 0:
        raise SourceIntakeError(f"{field} must be a positive integer")
    return version


def _qualified_subject(value: str, field: str) -> tuple[str, str]:
    for separator in (" — ", " - "):
        if separator in value:
            identifier, subject = value.split(separator, 1)
            if identifier and subject:
                return identifier, subject
    raise SourceIntakeError(f"{field} must include its plain subject")
