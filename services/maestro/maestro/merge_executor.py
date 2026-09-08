"""M4.10 (I1) — real merge execution, happy path only.

No command anywhere in this codebase performs a merge today — every
merge before this session's own M4 commits was a human running `git
merge`/`gh pr merge` by hand. This module performs the real merge for
a packet that has already reached a real `MergeReady`/accepted state
(depends on I0 — `owner_acceptance.py`); it is deliberately local-Git
only (`git merge`), not `gh pr merge`, since the real fixture repos
this session tests against have no GitHub remote and M4's own scope
never required one.

An automated merge executor is definitionally a `DelegatedIdentity`
per `merge_observations.performed_by_authority`'s own real constraint
(`_merge_observation` in `operational_state.py`), which requires a
non-null `delegation_reference` — this module's caller (M4.11) is
responsible for recording that; this module only performs the actual
merge and reports the real resulting commit.

**Explicitly out of scope, not silently handled:** merge conflicts,
branch-protection/required-checks gating, and CI-check state. This
module only handles the case where the merge applies cleanly — a real
conflict raises `MergeFailed` with the real `git merge` stderr instead
of attempting any resolution. Those cases are real, disclosed
follow-up scope, not yet packetized (see `m4-packet-breakdown.md`).
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path


class MergeExecutorError(RuntimeError):
    """Base class for real, disclosed merge-executor failures."""


class MergeFailed(MergeExecutorError):
    """The real `git merge` did not apply cleanly (conflict or other
    real failure). Conflict resolution is explicitly out of scope for
    this happy-path-only executor — see this module's own docstring."""


def _run(repository_path: Path, *arguments: str, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    environment = os.environ.copy()
    environment.update(
        {
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_TERMINAL_PROMPT": "0",
            "GIT_OPTIONAL_LOCKS": "0",
        }
    )
    result = subprocess.run(
        ["git", "--no-pager", "-C", str(repository_path), *arguments],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=environment,
        check=False,
    )
    if check and result.returncode != 0:
        message = result.stderr.decode("utf-8", errors="replace").strip()
        raise MergeExecutorError(f"git command failed: {message}")
    return result


def perform_merge(
    repository_path: str,
    default_branch: str,
    accepted_head: str,
    *,
    committer_name: str = "Maestro Merge Executor",
    committer_email: str = "maestro-merge-executor@example.invalid",
) -> str:
    """Merge ``accepted_head`` into ``default_branch`` for real, returning
    the real resulting commit on ``default_branch`` (the merge_commit).

    If ``accepted_head`` is already reachable from ``default_branch``'s
    own current tip (nothing to merge — the common case in this
    session's own single-branch test fixtures), returns that tip
    unchanged rather than fabricating a merge commit that never
    happened.
    """
    path = Path(repository_path)
    _run(path, "checkout", default_branch)
    base_tip = _run(path, "rev-parse", default_branch).stdout.decode("ascii").strip()

    already_merged = _run(
        path, "merge-base", "--is-ancestor", accepted_head, base_tip, check=False,
    )
    if already_merged.returncode == 0:
        return base_tip
    if already_merged.returncode != 1:
        message = already_merged.stderr.decode("utf-8", errors="replace").strip()
        raise MergeExecutorError(f"cannot determine merge ancestry: {message}")

    environment_overrides = [
        "-c", f"user.name={committer_name}",
        "-c", f"user.email={committer_email}",
    ]
    merge = _run(
        path, *environment_overrides, "merge", "--no-ff", accepted_head,
        "-m", f"Merge {accepted_head} via Maestro merge executor",
        check=False,
    )
    if merge.returncode != 0:
        message = merge.stderr.decode("utf-8", errors="replace").strip()
        _run(path, "merge", "--abort", check=False)
        raise MergeFailed(f"real merge of {accepted_head} into {default_branch} failed: {message}")

    return _run(path, "rev-parse", default_branch).stdout.decode("ascii").strip()
