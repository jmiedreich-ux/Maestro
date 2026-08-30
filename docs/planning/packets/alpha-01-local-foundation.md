# Alpha-01 — Establish Local Foundation

**Status:** Paused pending Decision Fidelity Review of the bounded M0-D11 reconciliation and final Alpha-01 repair packet  
**Owner:** Jeremy Miedreich  
**Authority:** [Maestro Alpha Decision-Fidelity Review](../maestro-alpha-decision-fidelity-review.md); [M0-D11 — Linux Runtime Filesystem Boundary](../decisions/m0-d11-linux-runtime-filesystem-boundary.md); [M0-D12 — Bounded Quality Contracts and Proportionality](../decisions/m0-d12-bounded-quality-contracts.md)  
**Execution class:** Bootstrap implementation in a clean isolated worktree  
**Worker route:** Maestro Implementor bootstrap route  
**Reviewer route:** Independent implementation reviewer under the bounded packet contract  
**Timeout:** Stop and report if the packet cannot complete within one focused implementation run.

## Outcome

Create the smallest runnable, Linux-first Python foundation for Maestro's local
service and SQLite operational store. It must be installable and testable, but
it must not create the packet wrapper, Atlas UI, project integration, or a
production host-security subsystem.

## Architecture lesson and current boundary

Earlier Alpha-01 contracts required absolute validation-to-mutation filesystem
protection without fully defining the threat model, sufficient proof, feasible
implementation boundary, proportionality ceiling, or stop rule. Repeated
implementation and review cycles resulted. The Owner classified that delay as
an Architecture Agent failure, not an implementor or reviewer failure.

[M0-D11](../decisions/m0-d11-linux-runtime-filesystem-boundary.md) now contains
the complete M0-D12 bounded quality contract for Alpha. It protects a trusted
local Linux process from incorrect, outside, source-tree, and pre-acquisition
symlinked paths. It explicitly excludes a malicious concurrent same-UID or root
process moving an already-open directory after directory-FD acquisition during
SQLite's internal opens. Alpha uses Python's standard library and built-in
`sqlite3`; stronger host-isolation assurance is later architecture work.

The R1 implementation at `e2c8a08` remains unaccepted. Its fresh independent
review returned `REQUEST_CHANGES` after proving the excluded post-FD move and
noting incomplete outside-path coverage for CLI/direct-constructor paths. The
post-FD move is no longer an Alpha gate; the in-scope coverage gap remains.

## Why this is bounded

Alpha requires one Python service, local SQLite, a safe ignored runtime area,
and a testable base before the wrapper can persist lifecycle state. This packet
establishes only that foundation. The `maestro run-packet` wrapper belongs to
Alpha-02.

## Original owned paths

Alpha-01 implementation work is restricted to:

- `services/maestro/pyproject.toml`
- `services/maestro/maestro/**`
- `tests/alpha_01/**`
- `docs/architecture/alpha-01-local-foundation.md`
- `docs/operations/alpha-01-local-run.md`
- `var/.gitignore`

A repair packet may narrow this list and may never expand it without new
Architecture/Owner approval.

## Required behavior

1. The service is a Python package rooted at `services/maestro/` and uses the
   standard library for runtime database behavior.
2. It enforces the bounded M0-D11 contract at every public command,
   configuration, constructor, and storage entry path before mutation.
   Outside-repository, source-tree, and pre-acquisition symlinked paths are
   rejected under the trusted local operating model.
3. It opens SQLite with foreign keys enabled and WAL mode requested/verified
   where supported.
4. It provides an idempotent migration mechanism with durable schema-version
   recording. Alpha-01 may create only migration metadata; it must not invent
   packet, queue, worker, or project-adapter schemas.
5. It provides a minimal health/readiness command or callable that confirms the
   runtime directory and database can be opened safely without creating a
   worker, dispatching a task, or reading another repository.
6. `var/.gitignore` keeps runtime database files, logs, evidence, and sockets
   out of Git while allowing its own ignore rule to remain tracked.
7. Architecture and operations notes explain the local-only boundary, run
   command, test command, database location, disposable-data removal, and the
   trusted-local Alpha assurance level without claiming excluded same-UID/root
   containment.

## Required checks and sufficient proof

Run and record:

```bash
cd services/maestro
python -m unittest discover -s ../../tests/alpha_01 -v
python -m maestro.cli health --runtime-dir ../../var/alpha-01-check
python -m maestro.cli health --runtime-dir ../../var/alpha-01-check
```

The named proof is sufficient when it demonstrates:

- command, direct configuration, direct constructor, and storage health paths
  reject outside-repository and source-tree runtime paths before mutation;
- pre-existing symlinked components and components changed before final safe
  acquisition are rejected without outside artifacts;
- each rejected test independently proves no database, journal, WAL/SHM, log,
  socket, or other artifact exists in its outside destination;
- the default path is independently derived as `<worktree-root>/var`;
- repeated health checks preserve foreign keys, requested/verified WAL, and
  durable schema version `1`; and
- no external repository, network, credential, adapter, worker, or Atlas UI is
  accessed.

No additional adversarial filesystem proof is required after these checks pass.

## Explicit exclusions

This packet must not:

- claim or implement protection from a malicious concurrent same-UID or root
  process moving an already-open runtime directory during SQLite internal opens;
- add dependencies, native extensions, a custom SQLite VFS, mount isolation,
  privileged helpers, or service-account provisioning;
- create `maestro run-packet`, worker dispatch, model invocation, worktree
  claiming, packet/lifecycle/evidence schemas, review routing, or escalation
  execution;
- create `apps/atlas/`, APIs/SSE, Slack/GitHub automation, webhooks,
  credentials, secrets, project registration, or Foundry/VennueSign adapters;
- modify `.env`, root `.gitignore`, `README.md`, `setup_env.sh`, or
  user-owned existing runtime data; or
- merge, deploy, push to `master`, or begin Alpha-02.

## Proportionality and stop rule

Use the smallest focused change needed to pass the named checks. One isolated
run and M0-D05's one targeted correction maximum apply.

Stop and return to Architecture/Owner if work would require an excluded
same-UID/root threat model, new dependency, native/custom VFS, OS isolation,
privileged operation, path outside the owned list, external system, secret, or
new filesystem policy. Do not begin another repair cycle for excluded
hardening.

## Completion and handoff

A valid final result has one scoped commit on a non-default branch, all named
checks passing, complete no-mutation evidence for in-scope rejected paths, and
no unsupported security claim. It receives independent implementation review
against the bounded contract. Approval still does not merge or trigger
Alpha-02.

## Decision-fidelity carrier map

| Governing choice | Alpha-01 carrier |
| --- | --- |
| Linux-first local operation | Python package, local runtime path, Linux commands |
| SQLite operational store | SQLite connection and idempotent migration metadata |
| Bounded runtime containment | M0-D11 trusted-local model, eight-field quality contract, named sufficient proof |
| Proportional work | Standard library only, focused owned paths, one run, one targeted correction maximum |
| Project-neutral synthetic Alpha | No adapter, project repository, worker, or external input |
| Atlas read-only and service-mediated | Atlas/API work explicitly excluded |
| Packet wrapper mandatory but later | Explicitly deferred to Alpha-02 |
| M0-D05 escalation boundary | One targeted correction; contract defects return to Architecture/Owner |
| USB recovery gate | Backup implementation and physical provisioning excluded |
| No secret inspection | `.env`, credentials, and external access explicitly forbidden |
