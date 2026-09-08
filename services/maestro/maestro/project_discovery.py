"""Real step 1 of M0-D02 registration: the read-only discovery pass.

M0-D02 says `project register` begins by reading the repository,
producing an owner-readable inventory of what was found/missing/
conflicting, and *proposing* a binding — never by making a human
hand-write the binding that discovery was supposed to produce. The
normalization engine for that already exists
(`synthetic_discovery.build_inventory`/`build_proposed_binding`/
`build_escalation_reason`, reused verbatim here) and
`real_discovery.py` already feeds it from a real GitHub repository.
What never existed is a command that reads a real *local* checkout and
runs the pass. This is that.

**The judgment boundary is deliberate and unchanged** (see
`real_discovery.py`'s own docstring): this module observes only facts
it can read mechanically — the repository identifier, the real default
branch, which declared authority paths actually exist at HEAD, and the
real test/build commands declared in a `package.json`'s own scripts. It
never guesses a project's delivery, verification, roles, or operations
*policy* from free-form prose. Every leaf it cannot observe is left
absent, so the existing inventory machinery reports it honestly as
`missing` and `build_escalation_reason` names it — that named list is
exactly the Architect's own worklist, per the SOP.

The Architect (or the Owner) answers those named leaves in a small
overlay file; `discover_project` merges the overlay over the observed
facts, and once nothing is missing or conflicting the same engine
returns a real `proposed_binding`. Nothing is auto-approved: a
reviewable binding is a proposal, and `register-project` is still the
separate, explicit act that persists it.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from .real_discovery import evaluate_snapshot

_CANDIDATE_ARCHITECTURE_PATHS = (
    "docs/architecture", "docs/architecture/project-foundation.md", "ARCHITECTURE.md",
)
_CANDIDATE_PLAN_PATHS = ("docs/planning", "docs/planning/work-graph.yaml", "PLAN.md", "ROADMAP.md")
_CANDIDATE_HANDOFF_PATHS = ("ai/handoffs/current.md", "docs/handoff.md", "HANDOFF.md")
_CANDIDATE_RULES_PATHS = ("AGENTS.md", "CLAUDE.md", "CONTRIBUTING.md", "docs/sop.md")


class DiscoveryError(ValueError):
    """The repository could not be read as a real Git worktree."""


def _git(repository_path: Path, *arguments: str) -> str | None:
    result = subprocess.run(
        ["git", "-C", str(repository_path), *arguments],
        stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        return None
    return result.stdout.decode("utf-8", errors="replace").strip()


def _tracked_paths(repository_path: Path) -> set[str]:
    listing = _git(repository_path, "ls-files")
    if listing is None:
        raise DiscoveryError(f"not a readable Git worktree: {repository_path}")
    return {line for line in listing.splitlines() if line}


def _first_present(candidates: tuple[str, ...], tracked: set[str]) -> str | None:
    for candidate in candidates:
        if candidate in tracked:
            return candidate
        prefix = candidate.rstrip("/") + "/"
        if any(path.startswith(prefix) for path in tracked):
            return candidate
    return None


def _all_present(candidates: tuple[str, ...], tracked: set[str]) -> list[str]:
    found = []
    for candidate in candidates:
        prefix = candidate.rstrip("/") + "/"
        if candidate in tracked or any(path.startswith(prefix) for path in tracked):
            found.append(candidate)
    return found


def _declared_commands(repository_path: Path, tracked: set[str]) -> dict[str, list[str]]:
    """Real declared commands, read only from a real `package.json`'s own
    `scripts` — a fact, not an interpretation. Absent when there is no
    package.json or no matching script."""
    if "package.json" not in tracked:
        return {}
    try:
        manifest = json.loads((repository_path / "package.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    scripts = manifest.get("scripts")
    if not isinstance(scripts, dict):
        return {}
    found: dict[str, list[str]] = {}
    if "build" in scripts:
        found["build_commands"] = ["npm run build"]
    for name in ("test", "check"):
        if name in scripts:
            found["test_commands"] = [f"npm run {name}" if name != "test" else "npm test"]
            break
    for name in ("test:integration", "integration"):
        if name in scripts:
            found["integration_commands"] = [f"npm run {name}"]
            break
    for name in ("test:e2e", "e2e", "test:ui"):
        if name in scripts:
            found["ui_qa_commands"] = [f"npm run {name}"]
            break
    return found


def observe_repository(repository_path: str | Path, github_reference: str) -> dict[str, Any]:
    """Read-only pass over a real local checkout. Returns a discovery
    snapshot containing **only** mechanically observed facts; every
    unobservable leaf is absent on purpose."""
    path = Path(repository_path)
    tracked = _tracked_paths(path)
    branch = _git(path, "rev-parse", "--abbrev-ref", "HEAD")

    identity: dict[str, Any] = {
        "project_name": github_reference.split("/")[-1],
        "repository_identifier": github_reference,
    }
    if branch and branch != "HEAD":
        identity["default_branch"] = branch

    authority: dict[str, Any] = {}
    architecture = _all_present(_CANDIDATE_ARCHITECTURE_PATHS, tracked)
    if architecture:
        authority["architecture_paths"] = architecture
    plans = _all_present(_CANDIDATE_PLAN_PATHS, tracked)
    if plans:
        authority["plan_paths"] = plans
    handoff = _first_present(_CANDIDATE_HANDOFF_PATHS, tracked)
    if handoff:
        authority["handoff_path"] = handoff
    rules = _first_present(_CANDIDATE_RULES_PATHS, tracked)
    if rules:
        authority["rules_sop_path"] = rules

    snapshot: dict[str, Any] = {"identity": identity}
    if authority:
        snapshot["authority"] = authority
    verification = _declared_commands(path, tracked)
    if verification:
        snapshot["verification"] = verification
    return snapshot


def _merge(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    merged = {key: dict(value) if isinstance(value, dict) else value for key, value in base.items()}
    for area, value in overlay.items():
        if isinstance(value, dict) and isinstance(merged.get(area), dict):
            merged[area] = {**merged[area], **value}
        else:
            merged[area] = value
    return merged


def discover_project(
    repository_path: str | Path, github_reference: str, overlay: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """The real discovery pass. ``overlay`` carries the Architect's own
    answers for leaves discovery cannot observe; without it the result
    honestly reports every one of them as missing.

    Returns ``{"snapshot", "inventory", "proposed_binding",
    "escalation_reason", "architect_worklist"}``. ``proposed_binding``
    is ``None`` until nothing is missing or conflicting —
    ``architect_worklist`` is the exact list of dotted leaves still
    owed, which is the Architect's job per the SOP."""
    observed = observe_repository(repository_path, github_reference)
    snapshot = _merge(observed, overlay or {})
    evaluated = evaluate_snapshot(snapshot)
    escalation = evaluated["escalation_reason"]
    return {
        "snapshot": snapshot,
        "inventory": evaluated["inventory"],
        "proposed_binding": evaluated["proposed_binding"],
        "escalation_reason": escalation,
        "architect_worklist": [] if escalation is None else escalation.split(", "),
    }
