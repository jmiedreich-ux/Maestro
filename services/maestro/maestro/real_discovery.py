"""Real (non-fixture) project discovery orchestration (M3 A1).

Fetches a registered project's real repository metadata and declared
process file via :mod:`maestro.github_client`, and hands the result to
:mod:`maestro.synthetic_discovery`'s already-existing, already-tested
``build_inventory``/``build_proposed_binding``/``build_escalation_reason``
functions — the same normalization engine Alpha's fixture-driven path
already uses, now fed from a real repository instead of a fixture file.

What this module deliberately does **not** do: guess at a project's
delivery/verification/operations policy from free-form prose with
per-project heuristics. Interpreting a project's own declared docs into
the discovery schema is real judgment work (master plan operating
principle #7: "Cloud models do planning, contracts, integration,
high-judgment work"), not something to fake with brittle regex parsing
that would silently misread one project's conventions as another's. A
field genuinely not found in what was actually read is left absent —
the existing inventory/escalation machinery already handles "missing"
correctly, surfacing it as a real open question rather than a fabricated
value.
"""

from __future__ import annotations

from typing import Any, Callable

from .github_client import fetch_file_content, fetch_repository_metadata
from .synthetic_discovery import build_escalation_reason, build_inventory, build_proposed_binding

FileFetcher = Callable[[str, str, str], "str | None"]


def fetch_real_repository_metadata(installation_token: str, owner: str, repo: str) -> dict[str, Any]:
    """Thin, real wrapper naming exactly what A1 needs from repo metadata."""
    metadata = fetch_repository_metadata(installation_token, owner, repo)
    return {
        "repository_identifier": metadata["full_name"],
        "default_branch": metadata["default_branch"],
    }


def fetch_real_process_file(installation_token: str, owner: str, repo: str, ref: str, path: str = "AGENTS.md") -> str | None:
    """Fetch a project's own declared root process file, verbatim.

    Returns ``None`` (not an empty string) when the path does not exist
    at ``ref`` — the caller decides what that absence means, this
    function never invents placeholder content.
    """
    return fetch_file_content(installation_token, owner, repo, path, ref)


def evaluate_snapshot(snapshot: dict[str, Any]) -> dict[str, Any]:
    """Run one already-constructed discovery snapshot through the
    existing (unmodified) inventory/binding/escalation engine.

    Returns a dict with ``inventory``, ``proposed_binding`` (``None``
    when not yet reviewable), and ``escalation_reason`` (``None`` when
    nothing is missing or conflicting) — the complete real discovery
    result for one project at one point in time.
    """
    return {
        "inventory": build_inventory(snapshot),
        "proposed_binding": build_proposed_binding(snapshot),
        "escalation_reason": build_escalation_reason(snapshot),
    }
