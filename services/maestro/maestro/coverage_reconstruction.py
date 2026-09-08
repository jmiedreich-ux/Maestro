"""M4.05 — real coverage reconstruction.

Wraps `review_readiness.py`'s own already-built, already-CLI-wired
`evaluate_review_readiness` as the real closed coverage-json shape
`_validate_review_coverage` (`operational_state.py`) requires:
`{"kind": "review-readiness-coverage", "result": <real evaluate_
review_readiness output>}`. No code anywhere did this wrapping before
this — the original packet breakdown draft cited the wrong reuse
target (`check_runner.py`, which produces none of the fields the real
validator checks); this is the corrected, much smaller real job.

Real, subtle constraint verified directly against the real validator
(`_validate_review_coverage`, `operational_state.py`): the coverage
result's own embedded `request.review_kind` must always be
`"IndependentImplementation"`, literally, regardless of which real
review command (Integration/`ValidateOnly`, M4.06, or
`IndependentImplementation`, M4.07) the coverage is being submitted
for — this session's own real end-to-end proof
(`test_foundry_end_to_end_proof.py`) reused the exact same real
coverage result for both. `reconstruct_coverage` therefore takes no
`review_kind` parameter at all; there is only one real shape.
"""

from __future__ import annotations

import shlex

from .review_readiness import REQUEST_SCHEMA, canonical_json, evaluate_review_readiness


def _to_command(raw: str) -> dict:
    """A real packet's own `checks_json` stores plain shell command
    strings (e.g. ``"npm run check"``) — this is the real, established
    shape every dispatch this session used. Splits into the
    `{"check_id", "argv"}` `review_readiness.py`'s own request schema
    requires.
    """
    argv = shlex.split(raw)
    if not argv:
        raise ValueError(f"empty command: {raw!r}")
    check_id = "-".join(argv).lower().replace("/", "-")
    return {"check_id": check_id, "argv": argv}


def reconstruct_coverage(
    packet: dict,
    *,
    repository: str,
    head: str,
    slice_id: str,
    reconstruction_commands: list[str],
    timeout_seconds: int = 180,
    base: str | None = None,
) -> dict:
    """``packet`` is a real packet row (e.g. from
    ``store.snapshot("Packet", packet_id)``) — its own real
    `owned_paths_json` and `checks_json` are reused verbatim, never
    re-typed. ``head`` is the real commit to check (the Succeeded
    attempt's own real `result_commit`).

    ``base`` defaults to the packet's own `base_commit` — correct for
    a real Integration/`IndependentImplementation` review (M4.06/M4.07).
    A real correction review (M4.08) must pass it explicitly instead:
    `record_and_route_correction_review` requires the coverage's own
    `base` to be the *Initial* attempt's real `result_commit`, not the
    packet's own original `base_commit` — a real, checked distinction
    (`operational_state.py`'s own correction-review routing), not the
    same field reused twice.
    """
    resolved_base = packet["base_commit"] if base is None else base
    request = {
        "schema": REQUEST_SCHEMA,
        "slice_id": slice_id,
        "review_kind": "IndependentImplementation",
        "repository": repository,
        "base": resolved_base,
        "head": head,
        "allowed_paths": sorted(packet["owned_paths_json"], key=lambda item: item.encode("utf-8")),
        "validation_commands": [_to_command(command) for command in packet["checks_json"]],
        "reconstruction_commands": [_to_command(command) for command in reconstruction_commands],
        "timeout_seconds": timeout_seconds,
    }
    request_bytes = canonical_json(request)
    result = evaluate_review_readiness(request_bytes)
    return {"kind": "review-readiness-coverage", "result": result}
