"""Exact, read-only registration source selection and inventory."""

from __future__ import annotations

import base64
import hashlib
import json
import re
import tempfile
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Callable, Iterable

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
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_REF_COMPONENT = re.compile(r"[A-Za-z0-9][A-Za-z0-9._/-]*\Z")
GitCommand = Callable[..., object]


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

    def __post_init__(self) -> None:
        try:
            object.__setattr__(self, "path", validate_repository_path(self.path))
        except GitReadError as error:
            raise SourceIntakeError(str(error)) from error
        if not isinstance(self.content, bytes):
            raise SourceIntakeError("source content must be bytes")
        if not isinstance(self.object_id, str) or _FULL_SHA.fullmatch(self.object_id) is None:
            raise SourceIntakeError("source blob object_id is invalid")
        if not isinstance(self.sha256, str) or _SHA256.fullmatch(self.sha256) is None:
            raise SourceIntakeError("source blob sha256 is invalid")
        git_header = f"blob {len(self.content)}\0".encode("ascii")
        if self.object_id != hashlib.sha1(git_header + self.content).hexdigest():
            raise SourceIntakeError("source blob object_id does not match its content")
        if self.sha256 != hashlib.sha256(self.content).hexdigest():
            raise SourceIntakeError("source blob sha256 does not match its content")

    @classmethod
    def from_bytes(cls, path: str, content: bytes) -> "SourceBlob":
        try:
            path = validate_repository_path(path)
        except GitReadError as error:
            raise SourceIntakeError(str(error)) from error
        if not isinstance(content, bytes):
            raise SourceIntakeError("source content must be bytes")
        git_header = f"blob {len(content)}\0".encode("ascii")
        return cls(path, hashlib.sha1(git_header + content).hexdigest(), hashlib.sha256(content).hexdigest(), content)

    def to_record(self) -> dict[str, str]:
        """Return a JSON-safe copy of this exact source blob."""
        return {
            "path": self.path,
            "object_id": self.object_id,
            "sha256": self.sha256,
            "content_base64": base64.b64encode(self.content).decode("ascii"),
        }

    @classmethod
    def from_record(cls, value: object) -> "SourceBlob":
        record = _record_object(value, {"path", "object_id", "sha256", "content_base64"}, "source blob")
        content = record["content_base64"]
        if not isinstance(content, str):
            raise SourceIntakeError("source blob content_base64 must be text")
        try:
            decoded = base64.b64decode(content.encode("ascii"), validate=True)
        except (UnicodeEncodeError, ValueError) as error:
            raise SourceIntakeError("source blob content_base64 is invalid") from error
        return cls(
            _record_text(record, "path", "source blob"),
            _record_text(record, "object_id", "source blob"),
            _record_text(record, "sha256", "source blob"),
            decoded,
        )


@dataclass(frozen=True)
class SourceReference:
    """An authoritative source location named by the overview."""

    source_type: str
    subject: str
    path: str

    def __post_init__(self) -> None:
        if self.source_type not in {"Architecture", "Milestone declaration"}:
            raise SourceIntakeError("source reference type is invalid")
        if not isinstance(self.subject, str) or not self.subject.strip():
            raise SourceIntakeError("source reference subject is invalid")
        try:
            object.__setattr__(self, "path", validate_repository_path(self.path))
        except GitReadError as error:
            raise SourceIntakeError(str(error)) from error

    def to_record(self) -> dict[str, str]:
        return {"source_type": self.source_type, "subject": self.subject, "path": self.path}

    @classmethod
    def from_record(cls, value: object) -> "SourceReference":
        record = _record_object(value, {"source_type", "subject", "path"}, "source reference")
        return cls(*(_record_text(record, key, "source reference") for key in ("source_type", "subject", "path")))


@dataclass(frozen=True)
class DeclaredDependency:
    """One dependency row retained from an exact milestone declaration."""

    record_id: str
    subject: str
    required_outcome: str
    evidence: str
    referenced_outcomes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for field in ("record_id", "subject", "required_outcome", "evidence"):
            value = getattr(self, field)
            if not isinstance(value, str) or not value.strip():
                raise SourceIntakeError(f"declared dependency {field} is invalid")
        if (
            not isinstance(self.referenced_outcomes, tuple)
            or any(not isinstance(item, str) or not item for item in self.referenced_outcomes)
            or len(set(self.referenced_outcomes)) != len(self.referenced_outcomes)
        ):
            raise SourceIntakeError("declared dependency outcome references are invalid")

    def to_record(self) -> dict[str, object]:
        return {
            "record_id": self.record_id,
            "subject": self.subject,
            "required_outcome": self.required_outcome,
            "evidence": self.evidence,
            "referenced_outcomes": list(self.referenced_outcomes),
        }

    @classmethod
    def from_record(cls, value: object) -> "DeclaredDependency":
        record = _record_object(
            value,
            {"record_id", "subject", "required_outcome", "evidence", "referenced_outcomes"},
            "declared dependency",
        )
        referenced = record["referenced_outcomes"]
        if not isinstance(referenced, list):
            raise SourceIntakeError("declared dependency outcome references are invalid")
        return cls(
            *(
                _record_text(record, field, "declared dependency")
                for field in ("record_id", "subject", "required_outcome", "evidence")
            ),
            tuple(_record_text({"value": item}, "value", "declared dependency reference") for item in referenced),
        )


@dataclass(frozen=True)
class OutcomeReference:
    """One ordered, versioned outcome retained from a declaration."""

    declaration: str
    declaration_subject: str
    declaration_version: int
    milestone: str
    subject: str
    version: int
    dependencies: tuple[DeclaredDependency, ...] = ()

    def __post_init__(self) -> None:
        for field in ("declaration", "declaration_subject", "milestone", "subject"):
            value = getattr(self, field)
            if not isinstance(value, str) or not value.strip():
                raise SourceIntakeError(f"outcome {field} is invalid")
        for field in ("declaration_version", "version"):
            value = getattr(self, field)
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise SourceIntakeError(f"outcome {field} is invalid")
        if not isinstance(self.dependencies, tuple) or any(
            not isinstance(item, DeclaredDependency) for item in self.dependencies
        ):
            raise SourceIntakeError("outcome dependencies are invalid")
        if len({item.record_id for item in self.dependencies}) != len(self.dependencies):
            raise SourceIntakeError("outcome dependency identities must be unique")

    def to_record(self) -> dict[str, object]:
        return {
            "declaration": self.declaration,
            "declaration_subject": self.declaration_subject,
            "declaration_version": self.declaration_version,
            "milestone": self.milestone,
            "subject": self.subject,
            "version": self.version,
            "dependencies": [item.to_record() for item in self.dependencies],
        }

    @classmethod
    def from_record(cls, value: object) -> "OutcomeReference":
        record = _record_object(value, {"declaration", "declaration_subject", "declaration_version", "milestone", "subject", "version", "dependencies"}, "outcome")
        integers = ("declaration_version", "version")
        if any(isinstance(record[field], bool) or not isinstance(record[field], int) for field in integers):
            raise SourceIntakeError("outcome version is invalid")
        dependencies = record["dependencies"]
        if not isinstance(dependencies, list):
            raise SourceIntakeError("outcome dependencies are invalid")
        return cls(
            _record_text(record, "declaration", "outcome"),
            _record_text(record, "declaration_subject", "outcome"),
            record["declaration_version"],
            _record_text(record, "milestone", "outcome"), _record_text(record, "subject", "outcome"), record["version"],
            tuple(DeclaredDependency.from_record(item) for item in dependencies),
        )


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
        if not isinstance(self.blobs, tuple) or any(not isinstance(item, SourceBlob) for item in self.blobs):
            raise SourceIntakeError("source inventory blobs must be an ordered tuple")
        if not isinstance(self.source_references, tuple) or any(not isinstance(item, SourceReference) for item in self.source_references):
            raise SourceIntakeError("source inventory references must be an ordered tuple")
        if not isinstance(self.outcomes, tuple) or any(not isinstance(item, OutcomeReference) for item in self.outcomes):
            raise SourceIntakeError("source inventory outcomes must be an ordered tuple")
        paths = tuple(item.path for item in self.blobs)
        if self.overview_path not in paths:
            raise SourceIntakeError("source inventory does not contain the overview")
        if len(paths) != len(set(paths)):
            raise SourceIntakeError("source inventory paths must be unique")
        reference_paths = tuple(item.path for item in self.source_references)
        if len(reference_paths) != len(set(reference_paths)):
            raise SourceIntakeError("source inventory references must be unique")
        if any(path not in paths for path in reference_paths):
            raise SourceIntakeError("source inventory does not contain a referenced source")

    def content_for(self, path: str) -> bytes:
        for blob in self.blobs:
            if blob.path == path:
                return blob.content
        raise SourceIntakeError(f"selected source does not contain {path}")

    def to_record(self) -> dict[str, object]:
        """Return a detached JSON-safe record retaining the inventory order."""
        return {
            "source_ref": self.source_ref,
            "source_commit": self.source_commit,
            "overview_path": self.overview_path,
            "blobs": [item.to_record() for item in self.blobs],
            "source_references": [item.to_record() for item in self.source_references],
            "outcomes": [item.to_record() for item in self.outcomes],
        }

    def to_json(self) -> str:
        return json.dumps(self.to_record(), sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)

    @classmethod
    def from_record(cls, value: object) -> "SourceInventory":
        record = _record_object(
            value, {"source_ref", "source_commit", "overview_path", "blobs", "source_references", "outcomes"}, "source inventory"
        )
        collections = ("blobs", "source_references", "outcomes")
        if any(not isinstance(record[field], list) for field in collections):
            raise SourceIntakeError("source inventory collections must be arrays")
        return cls(
            _record_text(record, "source_ref", "source inventory"),
            _record_text(record, "source_commit", "source inventory"),
            _record_text(record, "overview_path", "source inventory"),
            tuple(SourceBlob.from_record(item) for item in record["blobs"]),
            tuple(SourceReference.from_record(item) for item in record["source_references"]),
            tuple(OutcomeReference.from_record(item) for item in record["outcomes"]),
        )

    @classmethod
    def from_json(cls, value: object) -> "SourceInventory":
        if not isinstance(value, (str, bytes, bytearray)):
            raise SourceIntakeError("source inventory JSON must be text or bytes")
        try:
            return cls.from_record(json.loads(value))
        except (UnicodeDecodeError, json.JSONDecodeError, TypeError) as error:
            raise SourceIntakeError("source inventory JSON is invalid") from error


def _record_object(value: object, fields: set[str], subject: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping) or set(value) != fields:
        raise SourceIntakeError(f"{subject} record is invalid")
    if any(not isinstance(key, str) for key in value):
        raise SourceIntakeError(f"{subject} record is invalid")
    return value


def _record_text(record: Mapping[str, object], field: str, subject: str) -> str:
    value = record[field]
    if not isinstance(value, str):
        raise SourceIntakeError(f"{subject} {field} must be text")
    return value


class ExactSourceReader:
    """Resolve one source selector and read named blobs at that exact commit.

    The caller provides the service-bound Git command.  This prevents a source
    read from falling back to ambient user credentials after destination
    authorization has selected the service-owned GitHub App route.
    """

    def __init__(self, remote_reader: RemoteGitReader | None = None) -> None:
        self._remote_reader = remote_reader or RemoteGitReader()

    @staticmethod
    def default_branch(remote: str, *, command: Callable[..., object] = run_git) -> str:
        result = command("ls-remote", "--symref", remote, "HEAD")
        if result.returncode:
            raise SourceIntakeError("source repository has no readable default branch")
        try:
            lines = result.stdout.decode("ascii").splitlines()
            reference = next(line.split("\t", 1)[0][5:] for line in lines if line.startswith("ref: ") and line.endswith("\tHEAD"))
        except (UnicodeDecodeError, StopIteration, ValueError) as error:
            raise SourceIntakeError("source repository has no readable default branch") from error
        return validate_source_ref(reference)

    def read(
        self, *, remote: str, source_ref: str, overview_path: str,
        referenced_paths: Iterable[str] = (), command: Callable[..., object] = run_git,
    ) -> SourceInventory:
        if not isinstance(remote, str) or not remote or "\x00" in remote:
            raise SourceIntakeError("source repository remote must be nonempty text")
        selector = validate_source_ref(source_ref)
        paths = self._paths(overview_path, referenced_paths)
        commit = self._resolve(remote, selector, command)
        if selector.startswith("refs/heads/"):
            branch = selector.removeprefix("refs/heads/")
            try:
                snapshot = self._remote_reader.snapshot(remote, branch, paths, command=command)
            except GitReadError as error:
                raise SourceIntakeError(str(error)) from error
            if snapshot.head != commit:
                raise SourceIntakeError("source branch moved while intake was reading it")
            return self._from_snapshot(selector, snapshot, overview_path)
        return self._read_exact(remote, selector, commit, overview_path, paths, command)

    def read_registration(
        self, *, remote: str, source_ref: str, overview_path: str,
        referenced_paths: Iterable[str] = (), command: Callable[..., object] = run_git,
    ) -> SourceInventory:
        first = self.read(remote=remote, source_ref=source_ref, overview_path=overview_path, command=command)
        references = _parse_overview_references(first.content_for(first.overview_path))
        declared_paths = tuple(reference.path for reference in references)
        supplied = tuple(referenced_paths)
        if supplied and supplied != declared_paths:
            raise SourceIntakeError("overview references contradict supplied source locations")
        inventory = self._read_exact(remote, first.source_ref, first.source_commit, first.overview_path, (first.overview_path, *declared_paths), command)
        architecture = tuple(item for item in references if item.source_type == "Architecture")
        declarations = tuple(item for item in references if item.source_type == "Milestone declaration")
        if len(architecture) != 1 or not declarations:
            raise SourceIntakeError("overview must name one architecture and at least one milestone declaration")
        outcomes = tuple(
            outcome for declaration in declarations
            for outcome in _parse_declaration(declaration, inventory.content_for(declaration.path), architecture[0].path)
        )
        if not outcomes:
            raise SourceIntakeError("authoritative declarations contain no milestones")
        return SourceInventory(inventory.source_ref, inventory.source_commit, inventory.overview_path, inventory.blobs, references, outcomes)

    def resolve(
        self, *, remote: str, source_ref: str,
        command: Callable[..., object] = run_git,
    ) -> str:
        """Resolve a selector without reading any planning document bytes."""
        if not isinstance(remote, str) or not remote or "\x00" in remote:
            raise SourceIntakeError("source repository remote must be nonempty text")
        return self._resolve(remote, validate_source_ref(source_ref), command)

    def read_registration_at(
        self, *, remote: str, source_ref: str, source_commit: str,
        overview_path: str, referenced_paths: Iterable[str] = (),
        command: Callable[..., object] = run_git,
    ) -> SourceInventory:
        """Read registration inputs only from a previously resolved exact commit."""
        if not isinstance(remote, str) or not remote or "\x00" in remote:
            raise SourceIntakeError("source repository remote must be nonempty text")
        selector = validate_source_ref(source_ref)
        try:
            commit = validate_object_id(source_commit, "source_commit")
        except GitReadError as error:
            raise SourceIntakeError(str(error)) from error
        first = self._read_exact(
            remote, selector, commit, overview_path, self._paths(overview_path, ()), command
        )
        references = _parse_overview_references(first.content_for(first.overview_path))
        declared_paths = tuple(reference.path for reference in references)
        supplied = tuple(referenced_paths)
        if supplied and supplied != declared_paths:
            raise SourceIntakeError("overview references contradict supplied source locations")
        inventory = self._read_exact(
            remote, selector, commit, first.overview_path,
            (first.overview_path, *declared_paths), command,
        )
        architecture = tuple(
            item for item in references if item.source_type == "Architecture"
        )
        declarations = tuple(
            item for item in references if item.source_type == "Milestone declaration"
        )
        if len(architecture) != 1 or not declarations:
            raise SourceIntakeError(
                "overview must name one architecture and at least one milestone declaration"
            )
        outcomes = tuple(
            outcome for declaration in declarations
            for outcome in _parse_declaration(
                declaration, inventory.content_for(declaration.path), architecture[0].path
            )
        )
        if not outcomes:
            raise SourceIntakeError("authoritative declarations contain no milestones")
        return SourceInventory(
            selector, commit, inventory.overview_path, inventory.blobs, references, outcomes
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
    def _from_snapshot(selector: str, snapshot: RemoteSnapshot, overview_path: str) -> SourceInventory:
        missing = [path for path, content in snapshot.files.items() if content is None]
        if missing:
            raise SourceIntakeError(f"selected source does not contain {missing[0]}")
        blobs = tuple(SourceBlob.from_bytes(path, content) for path, content in snapshot.files.items() if content is not None)
        return SourceInventory(selector, snapshot.head, overview_path, blobs)

    @staticmethod
    def _resolve(remote: str, selector: str, command: Callable[..., object]) -> str:
        if _FULL_SHA.fullmatch(selector):
            return selector
        result = command("ls-remote", "--exit-code", remote, selector, f"{selector}^{{}}")
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
    def _read_exact(remote: str, selector: str, commit: str, overview_path: str, paths: tuple[str, ...], command: Callable[..., object]) -> SourceInventory:
        with tempfile.TemporaryDirectory(prefix="maestro-source-read-") as temporary:
            initialized = command("init", "--bare", "--quiet", temporary)
            fetched = command("-C", temporary, "fetch", "--no-tags", "--quiet", remote, commit)
            checked = command("-C", temporary, "cat-file", "-e", f"{commit}^{{commit}}")
            if initialized.returncode or fetched.returncode or checked.returncode:
                raise SourceIntakeError("selected source commit is unavailable or is not a commit")
            blobs: list[SourceBlob] = []
            for path in paths:
                listed = command("-C", temporary, "ls-tree", "-z", commit, "--", path)
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
                content = command("-C", temporary, "show", f"{commit}:{path}")
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


def _parse_declaration(reference: SourceReference, content: bytes, architecture_path: str) -> tuple[OutcomeReference, ...]:
    identity = {row[0]: row[1] for row in _table_rows(content, "Declaration identity") if len(row) == 2}
    qualified_declaration = identity.get("Declaration")
    version = _positive_version(identity.get("Declaration version"), "declaration version")
    if not qualified_declaration or qualified_declaration != reference.subject:
        raise SourceIntakeError("declaration identity contradicts the overview")
    declaration, declaration_subject = _qualified_subject(
        qualified_declaration, "declaration"
    )
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
        dependencies = tuple(
            DeclaredDependency(
                _dependency_record_id(milestone, row, dependency_position),
                _plain_markdown(row[0]),
                _plain_markdown(row[1]),
                _plain_markdown(row[2]),
                tuple(dict.fromkeys(re.findall(r"\b[A-Z][A-Z0-9]*-PM[0-9]+\b", row[1]))),
            )
            for dependency_position, row in enumerate(
                _milestone_dependency_rows(content, milestone), start=1
            )
        )
        outcomes.append(
            OutcomeReference(
                declaration, declaration_subject, version, milestone, subject,
                _positive_version(row[2], "milestone version"),
                dependencies,
            )
        )
    return tuple(outcomes)


def _milestone_dependency_rows(
    content: bytes, milestone: str
) -> tuple[tuple[str, str, str], ...]:
    try:
        lines = content.decode("utf-8").splitlines()
    except UnicodeDecodeError as error:
        raise SourceIntakeError("authoritative source must be UTF-8 Markdown") from error
    section_start = next(
        (
            index
            for index, line in enumerate(lines)
            if line.startswith(f"## {milestone} — ")
            or line.startswith(f"## {milestone} - ")
        ),
        None,
    )
    if section_start is None:
        return ()
    section_end = next(
        (
            index
            for index in range(section_start + 1, len(lines))
            if lines[index].startswith("## ")
        ),
        len(lines),
    )
    dependency_start = next(
        (
            index
            for index in range(section_start + 1, section_end)
            if lines[index] == "### Dependencies"
        ),
        None,
    )
    if dependency_start is None:
        return ()
    dependency_end = next(
        (
            index
            for index in range(dependency_start + 1, section_end)
            if lines[index].startswith("### ")
        ),
        section_end,
    )
    rows: list[tuple[str, str, str]] = []
    for line in lines[dependency_start + 1:dependency_end]:
        if not line.startswith("|"):
            continue
        cells = tuple(cell.strip() for cell in line.strip().strip("|").split("|"))
        if cells == (
            "Required dependency", "Reference", "Current state or delivery responsibility"
        ):
            continue
        if all(cell and set(cell) <= {"-", ":"} for cell in cells):
            continue
        if len(cells) != 3 or any(not cell for cell in cells):
            raise SourceIntakeError(f"{milestone} dependency table is invalid")
        rows.append(cells)
    return tuple(rows)


def _dependency_record_id(
    milestone: str, row: tuple[str, str, str], position: int
) -> str:
    references = tuple(
        dict.fromkeys(re.findall(r"\b[A-Z][A-Z0-9]*-PM[0-9]+\b", row[1]))
    )
    return references[0] if len(references) == 1 else f"{milestone}-dependency-{position}"


def _plain_markdown(value: str) -> str:
    plain = re.sub(r"\[([^]]+)\]\([^)]+\)", r"\1", value)
    plain = plain.replace("`", "").strip()
    if not plain:
        raise SourceIntakeError("declared dependency text is invalid")
    return plain


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
        if cells and cells[0] in {"Source type", "Field", "Position"}:
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
