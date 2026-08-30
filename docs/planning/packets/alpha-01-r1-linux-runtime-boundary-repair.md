# Alpha-01-R1 — Enforce Linux Runtime Filesystem Boundary

**Status:** Draft; requires fresh Decision Fidelity Review before implementation  
**Owner:** Jeremy Miedreich  
**Authority:** [Alpha-01 — Establish Local Foundation](alpha-01-local-foundation.md); [M0-D11 — Linux Runtime Filesystem Boundary](../decisions/m0-d11-linux-runtime-filesystem-boundary.md)  
**Base:** The complete Alpha-01 coordinator-repair result at `b476cdc`, after verifying its provenance and establishing a clean isolated worktree. Stop if that base is unavailable or has a different full diff.  
**Execution class:** One bounded repair in a clean isolated worktree on a new non-default branch  
**Worker route:** Normal bounded Maestro Implementor route  
**Review route:** Fresh independent implementation review; GPT-5.6 Sol at high reasoning  
**Timeout:** Stop and report if one focused repair cannot meet this packet without expanding scope.

## Purpose

Repair the explicit M0-D11 gap found by independent review: a runtime directory
that passed validation could be replaced by a symlink before a SQLite mutation,
allowing an artifact to escape the repository's physical `var/` boundary.

This packet is a new packet-contract repair, not a second correction to a
previous worker run. It does not change the classification of prior work as a
packet-contract failure.

## Owned paths

The worker may change only:

- `services/maestro/maestro/config.py`
- `services/maestro/maestro/storage.py`
- `tests/alpha_01/test_local_foundation.py`

No other path is authorized.

## Required behavior

1. Enforce M0-D11 at every public command, configuration, constructor, and
   storage entry path before any directory or SQLite/runtime mutation.
2. Treat the repository's physical `var/` directory as the only runtime
   boundary. A path outside it, a source-tree path, or a path with a symlinked
   component is rejected.
3. Defend against validation-to-mutation substitution on Linux. The mutation
   operation itself must not be redirectable outside the physical `var/`
   boundary by replacing an approved path component with a symlink after
   validation. A prior `Path.resolve()`-style check by itself is insufficient.
4. Apply the same protection to SQLite database creation/opening and its
   related journal, WAL, and SHM artifacts, not only directory creation.
5. Preserve valid repeated health behavior: foreign keys enabled, WAL
   requested/verified where supported, and schema version `1` durable and
   idempotent.
6. Preserve the independently derived default path assertion:
   `<worktree-root>/var`.

## Required tests and evidence

Add or adjust focused tests that prove:

- command, direct configuration, direct constructor, and storage health paths
  reject source-tree and outside-repository runtime paths before mutation;
- a symlinked runtime component is rejected with no directory, database,
  journal, WAL/SHM, log, socket, or other artifact created outside `var/`;
- a controlled symlink-swap/race attempt immediately before mutation cannot
  redirect any runtime or SQLite artifact outside `var/`;
- the default path is independently derived from the worktree root, not the
  implementation constant; and
- repeated valid health checks still pass and preserve schema version `1`.

Run and record:

```bash
cd services/maestro
python -m unittest discover -s ../../tests/alpha_01 -v
python -m maestro.cli health --runtime-dir ../../var/alpha-01-r1-check
python -m maestro.cli health --runtime-dir ../../var/alpha-01-r1-check
```

Evidence must include commands, exit status, changed files, the valid health
output, and an explicit no-artifact check for every rejected and raced path.
Remove only generated test/runtime artifacts within the isolated worktree after
capturing evidence; do not touch user-owned runtime data.

## Explicit exclusions

Do not:

- add dependencies, native extensions, shell helpers, network access, secret
  access, GitHub automation, RunPod use, or external-project access;
- create a packet wrapper, worker dispatch, queue/lifecycle schema, API/UI,
  Atlas work, Foundry/VennueSign integration, or USB recovery support;
- modify `.env`, root `.gitignore`, `README.md`, `setup_env.sh`,
  existing `var/` contents, or any path outside this packet's owned paths;
- merge, deploy, push to `master`, or begin Alpha-02.

## Stop and escalate

Stop without improvising if:

- the required coordinator-repair base cannot be verified;
- enforcing M0-D11 needs a path outside the owned list or a non-standard
  dependency;
- the implementation cannot protect SQLite and all related artifacts at the
  actual mutation boundary;
- a test requires a real external repository, secret, network, or user-owned
  runtime path; or
- a new filesystem policy choice is needed.

## Completion and handoff

A valid result is one scoped commit on a new non-default branch, all required
checks passing, and complete no-mutation evidence. It goes to a fresh
independent implementation reviewer. It does not merge, start Alpha-02, or
authorize any successor packet.
