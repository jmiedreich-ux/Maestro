"""Planning Guide source validation for registration intake.

Python checks required fields, file locations, document structure and references
before any agent is launched. Every problem found is reported with the document
and field it concerns; meaning and completeness of content are judged later by
the architect and the fidelity reviewer.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Callable, Mapping

FileReader = Callable[[str], "bytes | None"]

_HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
_MILESTONE_ID = re.compile(r"^([A-Z][A-Z0-9]*)-PM([1-9][0-9]*)$")
_PATH = re.compile(r"^[A-Za-z0-9._][A-Za-z0-9._/\-]*$")
_PLACEHOLDER = re.compile(r"\[[^\]]*\]")
_IDENTITY_FIELDS = ("Project name", "Repository", "Responsible architect", "Document version")
_DECLARATION_FIELDS = ("Declaration", "Declaration version", "Architecture source")
_REQUIRED_ARCHITECTURE_HEADINGS = ("Components and responsibilities", "Journeys and interactions")
_MILESTONE_PARTS = ("Outcome", "Included", "Excluded")
_MILESTONE_TABLES = ("Architecture and journeys", "Dependencies", "Acceptance criteria")


class SourceError(ValueError):
    """The supplied sources cannot be registered; ``problems`` names every gap."""

    def __init__(self, problems: list[dict[str, str]]) -> None:
        self.problems = problems
        super().__init__("; ".join(f"{p['document']}: {p['problem']}" for p in problems))


@dataclass(frozen=True)
class Milestone:
    reference: str
    subject: str
    version: int
    section: str
    outcome: str
    included: str
    excluded: str
    journeys: tuple[tuple[str, str], ...]
    dependencies: tuple[tuple[str, str, str], ...]
    criteria: tuple[tuple[str, str, str, str], ...]
    definition_of_done: str


@dataclass(frozen=True)
class Declaration:
    designation: str
    subject: str
    version: int
    path: str
    architecture: str
    milestones: tuple[Milestone, ...]


@dataclass(frozen=True)
class SourceModel:
    overview_path: str
    project_name: str
    repository: str
    architect: str
    document_version: str
    purpose: str
    included: str
    excluded: str
    current_state: tuple[tuple[str, ...], ...]
    architecture_path: str
    declarations: tuple[Declaration, ...]
    documents: tuple[str, ...] = field(default=())

    def milestone(self, reference: str) -> Milestone | None:
        for declaration in self.declarations:
            for milestone in declaration.milestones:
                if milestone.reference == reference:
                    return milestone
        return None

    def as_summary(self) -> dict[str, object]:
        """Deterministic facts for assignments and the package."""
        return {
            "overview_path": self.overview_path,
            "project_name": self.project_name,
            "repository": self.repository,
            "architect": self.architect,
            "purpose": self.purpose,
            "included": self.included,
            "excluded": self.excluded,
            "architecture_path": self.architecture_path,
            "declarations": [
                {
                    "designation": d.designation,
                    "subject": d.subject,
                    "version": d.version,
                    "path": d.path,
                    "milestones": [
                        {"reference": m.reference, "subject": m.subject, "version": m.version, "section": m.section}
                        for m in d.milestones
                    ],
                }
                for d in self.declarations
            ],
        }


class _Document:
    """A Markdown document split into headed sections and tables."""

    def __init__(self, path: str, text: str) -> None:
        self.path = path
        self.lines = text.splitlines()
        self.sections: list[tuple[int, str, list[str]]] = []
        current: tuple[int, str, list[str]] | None = None
        in_fence = False
        for line in self.lines:
            if line.lstrip().startswith("```"):
                in_fence = not in_fence
            match = None if in_fence else _HEADING.match(line)
            if match:
                current = (len(match.group(1)), match.group(2), [])
                self.sections.append(current)
            elif current is not None:
                current[2].append(line)

    def section(self, title: str, level: int | None = None) -> list[str] | None:
        for depth, name, body in self.sections:
            if name == title and (level is None or depth == level):
                return body
        return None

    def has_heading(self, fragment: str) -> bool:
        wanted = _slug(fragment)
        return any(_slug(name) == wanted or name == fragment for _, name, _ in self.sections)

    def children(self, title: str, level: int) -> dict[str, list[str]]:
        """Sub-sections directly below a heading, with body lines."""
        found: dict[str, list[str]] = {}
        inside = False
        for depth, name, body in self.sections:
            if depth == level and name == title:
                inside = True
                continue
            if inside and depth <= level:
                break
            if inside and depth == level + 1:
                found[name] = body
        return found


def _slug(text: str) -> str:
    text = re.sub(r"[`*_]", "", text.strip().lower())
    text = re.sub(r"[^\w\- ]", "", text)
    return text.replace(" ", "-")


def _cells(line: str) -> list[str]:
    inner = line.strip().strip("|")
    return [cell.strip() for cell in inner.split("|")]


def _tables(lines: list[str]) -> list[list[list[str]]]:
    """Each table is a list of rows (header first), separator rows removed."""
    tables: list[list[list[str]]] = []
    current: list[list[str]] = []
    for line in lines:
        if line.strip().startswith("|"):
            cells = _cells(line)
            if all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells if cell):
                continue
            current.append(cells)
        elif current:
            tables.append(current)
            current = []
    if current:
        tables.append(current)
    return tables


def _first_table(lines: list[str] | None) -> list[list[str]]:
    if lines is None:
        return []
    tables = _tables(lines)
    return tables[0] if tables else []


def _field_table(lines: list[str] | None) -> dict[str, str]:
    rows = _first_table(lines)
    return {row[0]: row[1] for row in rows[1:] if len(row) >= 2}


def _prose(lines: list[str] | None) -> str:
    if lines is None:
        return ""
    return " ".join(line.strip() for line in lines if line.strip() and not line.strip().startswith(("<!--", "|"))).strip()


def _placeholder(value: str) -> bool:
    return not value.strip() or bool(_PLACEHOLDER.fullmatch(value.strip())) or "[Plain" in value or "[Name" in value


def _location(value: str) -> tuple[str, str]:
    path, _, fragment = value.partition("#")
    return path.strip(), fragment.strip()


def _safe_path(path: str) -> bool:
    return bool(_PATH.match(path)) and ".." not in path.split("/") and not path.startswith("/")


def validate_sources(overview_path: str, read: FileReader) -> SourceModel:
    """Read the overview and everything it names; raise SourceError listing every gap."""
    problems: list[dict[str, str]] = []

    def problem(document: str, text: str) -> None:
        problems.append({"document": document, "problem": text})

    if not _safe_path(overview_path):
        raise SourceError([{"document": overview_path, "problem": "the overview path must be repository-relative with no parent traversal"}])
    raw = read(overview_path)
    if raw is None:
        raise SourceError([{"document": overview_path, "problem": "the project overview is not present at this commit"}])
    overview = _Document(overview_path, raw.decode("utf-8", "replace"))
    cache: dict[str, _Document | None] = {overview_path: overview}
    touched: list[str] = [overview_path]

    def load(path: str) -> _Document | None:
        if path not in cache:
            content = read(path) if _safe_path(path) else None
            cache[path] = None if content is None else _Document(path, content.decode("utf-8", "replace"))
            if content is not None:
                touched.append(path)
        return cache[path]

    identity = _field_table(overview.section("Project identity"))
    for name in _IDENTITY_FIELDS:
        if name not in identity:
            problem(overview_path, f"'Project identity' has no '{name}' row")
        elif _placeholder(identity[name]):
            problem(overview_path, f"'Project identity' field '{name}' is empty or still a template prompt")
    purpose = _prose(overview.section("Purpose"))
    if not purpose or _placeholder(purpose):
        problem(overview_path, "'Purpose' is missing or still a template prompt")
    scope = _field_table(overview.section("Overall scope"))
    for name in ("Included", "Excluded"):
        if _placeholder(scope.get(name, "")):
            problem(overview_path, f"'Overall scope' has no '{name}' description")
    state_rows = _first_table(overview.section("Current state"))
    if len(state_rows) < 2:
        problem(overview_path, "'Current state' has no capability rows")
    sources = _first_table(overview.section("Authoritative sources"))
    architecture_paths: list[str] = []
    declaration_paths: list[tuple[str, str]] = []
    if len(sources) < 2:
        problem(overview_path, "'Authoritative sources' lists no architecture or milestone declarations")
    for row in sources[1:]:
        if len(row) < 3:
            problem(overview_path, "an 'Authoritative sources' row does not have three columns")
            continue
        kind, subject, location = row[0], row[1], row[2]
        path, fragment = _location(location)
        if kind == "Architecture":
            architecture_paths.append(path)
        elif kind == "Milestone declaration":
            declaration_paths.append((subject, path))
        else:
            problem(overview_path, f"authoritative source type '{kind}' is not Architecture or Milestone declaration")
            continue
        document = load(path)
        if document is None:
            problem(overview_path, f"authoritative source '{subject}' points to '{path}', which is not present at this commit")
        elif fragment and not document.has_heading(fragment):
            problem(path, f"the overview references heading '#{fragment}', which the document does not contain")
    if len(architecture_paths) != 1:
        problem(overview_path, "'Authoritative sources' must list exactly one Architecture document")
    if not declaration_paths:
        problem(overview_path, "'Authoritative sources' must list at least one Milestone declaration")

    architecture_path = architecture_paths[0] if architecture_paths else ""
    architecture = load(architecture_path) if architecture_path else None
    if architecture is not None:
        for heading in _REQUIRED_ARCHITECTURE_HEADINGS:
            if architecture.section(heading) is None:
                problem(architecture_path, f"the architecture has no '{heading}' section")
        version = _field_table(architecture.lines and _lines_before_first_heading(architecture))
        if _placeholder(version.get("Document version", "")):
            problem(architecture_path, "the architecture has no 'Document version' field")

    declarations: list[Declaration] = []
    for subject, path in declaration_paths:
        document = load(path)
        if document is None:
            continue
        declaration = _declaration(document, subject, architecture_path, load, problem)
        if declaration is not None:
            declarations.append(declaration)
    designations = [d.designation for d in declarations]
    if len(set(designations)) != len(designations):
        problem(overview_path, "declaration designations must be unique within the project")
    references = [m.reference for d in declarations for m in d.milestones]
    if len(set(references)) != len(references):
        problem(overview_path, "milestone references must be unique within the project")
    for declaration in declarations:
        for milestone in declaration.milestones:
            for name, reference, _state in milestone.dependencies:
                found = _MILESTONE_ID.match(reference.split(" ")[0]) if reference else None
                if found and reference.split(" ")[0] not in references and found.group(1) in designations:
                    problem(declaration.path, f"milestone {milestone.reference} depends on {reference.split(' ')[0]}, which no declaration lists")

    if problems:
        raise SourceError(problems)
    return SourceModel(
        overview_path=overview_path,
        project_name=identity["Project name"],
        repository=identity["Repository"],
        architect=identity["Responsible architect"],
        document_version=identity["Document version"],
        purpose=purpose,
        included=scope["Included"],
        excluded=scope["Excluded"],
        current_state=tuple(tuple(row) for row in state_rows[1:]),
        architecture_path=architecture_path,
        declarations=tuple(declarations),
        documents=tuple(dict.fromkeys(touched)),
    )


def _lines_before_first_heading(document: _Document) -> list[str]:
    lines: list[str] = []
    for line in document.lines:
        if line.startswith("## "):
            break
        lines.append(line)
    return lines


def _declaration(document: _Document, listed_subject: str, architecture_path: str, load, problem) -> Declaration | None:
    path = document.path
    identity = _field_table(document.section("Declaration identity"))
    for name in _DECLARATION_FIELDS:
        if _placeholder(identity.get(name, "")):
            problem(path, f"'Declaration identity' has no '{name}' value")
    designation_text = identity.get("Declaration", "")
    designation, _, subject = designation_text.partition("—")
    designation, subject = designation.strip(), subject.strip()
    if not designation or not subject:
        problem(path, "the declaration must give its designation and plain subject, as 'DESIGNATION — Subject'")
        return None
    version = _version(identity.get("Declaration version", ""))
    if version is None:
        problem(path, "'Declaration version' must be a positive integer")
        return None
    if identity.get("Architecture source") and _location(identity["Architecture source"])[0] != architecture_path:
        problem(path, "the declaration's architecture source is not the architecture the overview lists")
    order = _first_table(document.section("Milestones and order"))
    if len(order) < 2:
        problem(path, "'Milestones and order' lists no milestones")
        return None
    milestones: list[Milestone] = []
    for row in order[1:]:
        if len(row) < 4:
            problem(path, "a 'Milestones and order' row does not have position, reference, version and section")
            continue
        reference_text, version_text, section = row[1], row[2], row[3]
        reference, _, milestone_subject = reference_text.partition("—")
        reference, milestone_subject = reference.strip(), milestone_subject.strip()
        found = _MILESTONE_ID.match(reference)
        if not found or found.group(1) != designation or not milestone_subject:
            problem(path, f"milestone '{reference_text}' must read '{designation}-PM<number> — plain subject'")
            continue
        milestone_version = _version(version_text)
        if milestone_version is None:
            problem(path, f"milestone {reference} has no positive integer version")
            continue
        target_path, fragment = _location(section)
        if target_path != path:
            problem(path, f"milestone {reference} section '{section}' is not in this declaration")
            continue
        parsed = _milestone(document, reference, milestone_subject, milestone_version, section, problem)
        if parsed is not None:
            milestones.append(parsed)
    return Declaration(designation, subject, version, path, _location(identity.get("Architecture source", ""))[0], tuple(milestones))


def _milestone(document: _Document, reference: str, subject: str, version: int, section: str, problem) -> Milestone | None:
    path = document.path
    title = next((name for _, name, _ in document.sections if name.startswith(reference)), None)
    if title is None:
        problem(path, f"milestone {reference} has no section")
        return None
    body = document.section(title) or []
    text = "\n".join(body)
    parts: dict[str, str] = {}
    for name in _MILESTONE_PARTS:
        found = re.search(rf"\*\*{name}:\*\*\s*(.+)", text)
        parts[name] = found.group(1).strip() if found else ""
        if not parts[name] or _placeholder(parts[name]):
            problem(path, f"milestone {reference} has no '{name}' statement")
    children = document.children(title, 2)
    tables: dict[str, list[list[str]]] = {}
    for name in _MILESTONE_TABLES:
        rows = _first_table(children.get(name))
        tables[name] = rows
        if len(rows) < 2:
            problem(path, f"milestone {reference} has no rows in '{name}'")
    done = _prose(children.get("Definition of done"))
    if not done:
        problem(path, f"milestone {reference} has no 'Definition of done'")
    criteria = tuple(tuple(row[:4]) for row in tables["Acceptance criteria"][1:] if len(row) >= 4)
    if tables["Acceptance criteria"][1:] and len(criteria) != len(tables["Acceptance criteria"]) - 1:
        problem(path, f"milestone {reference} has an acceptance criterion without the four required columns")
    return Milestone(
        reference=reference,
        subject=subject,
        version=version,
        section=section,
        outcome=parts["Outcome"],
        included=parts["Included"],
        excluded=parts["Excluded"],
        journeys=tuple((row[0], row[1]) for row in tables["Architecture and journeys"][1:] if len(row) >= 2),
        dependencies=tuple((row[0], row[1], row[2]) for row in tables["Dependencies"][1:] if len(row) >= 3),
        criteria=criteria,
        definition_of_done=done,
    )


def _version(value: str) -> int | None:
    value = value.strip()
    return int(value) if value.isdigit() and int(value) > 0 else None


def interpret_scope(model: SourceModel, selection: Mapping[str, object] | None) -> dict[str, object]:
    """The boundary presented for confirmation; never expands a narrower selection by inference."""
    selection = selection or {"kind": "whole"}
    kind = selection.get("kind", "whole")
    everything = [m for d in model.declarations for m in d.milestones]
    if kind == "whole":
        included = everything
        description = "the whole supplied plan"
    elif kind == "milestones":
        wanted = selection.get("milestones")
        if not isinstance(wanted, list) or not wanted or not all(isinstance(w, str) for w in wanted):
            raise SourceError([{"document": "scope", "problem": "a milestone selection must list milestone references"}])
        unknown = [w for w in wanted if model.milestone(w) is None]
        if unknown:
            raise SourceError([{"document": "scope", "problem": f"unknown milestone reference(s): {', '.join(unknown)}"}])
        included = [m for m in everything if m.reference in wanted]
        description = "the selected milestones"
    elif kind == "described":
        text = selection.get("description")
        wanted = selection.get("milestones")
        if not isinstance(text, str) or not text.strip() or not isinstance(wanted, list) or not wanted:
            raise SourceError([{"document": "scope", "problem": "a written boundary needs a description and the milestones it touches"}])
        unknown = [w for w in wanted if model.milestone(w) is None]
        if unknown:
            raise SourceError([{"document": "scope", "problem": f"unknown milestone reference(s): {', '.join(unknown)}"}])
        included = [m for m in everything if m.reference in wanted]
        description = text.strip()
    else:
        raise SourceError([{"document": "scope", "problem": "scope kind must be whole, milestones or described"}])
    included_refs = {m.reference for m in included}
    outside: list[dict[str, str]] = []
    for milestone in included:
        for name, reference, state in milestone.dependencies:
            token = reference.split(" ")[0]
            if token not in included_refs:
                outside.append({"milestone": milestone.reference, "dependency": name, "reference": reference, "state": state})
    return {
        "kind": kind,
        "description": description,
        "included": [{"reference": m.reference, "subject": m.subject, "version": m.version} for m in included],
        "excluded": [{"reference": m.reference, "subject": m.subject, "version": m.version} for m in everything if m.reference not in included_refs],
        "outside_dependencies": outside,
    }
