# Alpha-01 — Establish Local Foundation

**Status:** Paused for packet-contract amendment and renewed Decision Fidelity Review. The review finding is not counted as a worker/model delivery failure.  
**Owner:** Jeremy Miedreich  
**Authority:** [Maestro Alpha Decision-Fidelity Review](../maestro-alpha-decision-fidelity-review.md); [M0-D11 — Linux Runtime Filesystem Boundary](../decisions/m0-d11-linux-runtime-filesystem-boundary.md)  
**Base:** Current `master` at execution time  
**Execution class:** Bootstrap implementation in a clean isolated worktree  
**Worker route:** Maestro Implementor bootstrap route  
**Reviewer route:** Independent implementation reviewer; cloud GPT-5.6 Sol with high reasoning is the preferred route  
**Timeout:** Stop and report if the packet cannot complete within one focused implementation run.

## Packet-contract defect record

The first implementation review found that a caller-supplied runtime path could
create SQLite state outside the repository runtime boundary. The permitted
targeted correction at `2a3f7b9` protected the CLI path, but the renewed
review found that direct `RuntimeConfig(...)` construction and
`SQLiteFoundation(...).health()` still bypass that validation; it also found
a tautological default-path test.

The original packet also did not define Linux symlink traversal or a
validation-to-mutation race. The later coordinator repair correctly covered
public construction/call paths, but its renewed review found that a valid
runtime path could be replaced by a symlink before SQLite mutated it.

[M0-D11 — Linux Runtime Filesystem Boundary](../decisions/m0-d11-linux-runtime-filesystem-boundary.md)
is now the controlling owner-approved rule. Treat both findings as
packet-contract defects, not worker/model failures or hard escalations. This
packet must receive fresh Decision Fidelity Review before a new bounded repair
packet may be issued.

## Decision Fidelity approval

A fresh GPT-5.6 Sol Decision Fidelity Reviewer approved this packet after a
clean tracked-state check and fast-forward. The review confirmed the precise
owned paths, synthetic-only/project-neutral boundary, explicit Alpha-02 wrapper
deferral, exclusions, checks, and isolated-worktree/non-default-branch
requirements.

## Outcome

Create the smallest runnable, Linux-first Python foundation for Maestro's local
service and SQLite operational store. It must be installable and testable, but
it must not yet create the packet wrapper, Atlas UI, or any project integration.

## Why this is bounded

Alpha requires one Python service, local SQLite, a safe ignored runtime area,
and a testable base before the wrapper can persist lifecycle state. This packet
establishes only that foundation. The `maestro run-packet` wrapper is required
by Alpha but belongs to Alpha-02, where it can be implemented and tested as one
cohesive lifecycle boundary.

## Owned paths

The worker may create or change only:

- `services/maestro/pyproject.toml`
- `services/maestro/maestro/**`
- `tests/alpha_01/**`
- `docs/architecture/alpha-01-local-foundation.md`
- `docs/operations/alpha-01-local-run.md`
- `var/.gitignore`

No other path is authorized.

## Required behavior

1. The service is a Python package rooted at `services/maestro/` and uses the
   standard library for its runtime database behavior.
2. It enforces [M0-D11](../decisions/m0-d11-linux-runtime-filesystem-boundary.md)
   at every public command, configuration, constructor, and storage callable.
   Its default local database path is independently derived as
   `<worktree-root>/var`. Runtime artifacts may exist only inside the
   repository's real physical `var/` tree: every component must be
   non-symlinked, and Linux-safe mutation operations must prevent a
   validation-to-mutation symlink substitution from escaping that tree.
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
7. The architecture and operations notes explain the local-only boundary, run
   command, test command, database location, and how to remove only disposable
   Alpha runtime data.

## Required checks and evidence

Run and record all of the following:

```bash
cd services/maestro
python -m unittest discover -s ../../tests/alpha_01 -v
python -m maestro.cli health --runtime-dir ../../var/alpha-01-check
```

The health check must demonstrate that:

- every valid runtime artifact is created only beneath the repository's real
  physical `var/` tree;
- command, configuration, constructor, and storage paths reject outside,
  source-tree, and symlinked paths before mutation;
- a symlink-swap/race attempt cannot redirect a database, WAL/SHM file, log,
  socket, or directory outside `var/`; rejected attempts leave no artifact;
- rerunning a valid health check is safe and preserves the recorded schema
  version; and
- no external repository, network, credential, project adapter, worker, or
  Atlas UI is accessed.

Evidence must include the exact commands, exit status, changed-file list, and
the resulting schema version. Do not commit generated database files or logs.

## Explicit exclusions

This packet must not:

- create `maestro run-packet`, worker dispatch, model invocation, worktree
  claiming, packet/lifecycle/evidence schemas, review routing, or escalation
  execution;
- create `apps/atlas/`, a browser/UI project, API/SSE endpoints, Slack,
  GitHub automation, webhooks, credentials, secrets, project registration, or
  any Foundry/VennueSign adapter;
- modify root `.gitignore`, `.env`, `var/` runtime contents, RunPod
  artifacts, `README.md`, or `setup_env.sh`;
- merge, deploy, push to `master`, or start a later Alpha packet.

## Stop and escalate

Stop without improvising if:

- the isolated worktree is not clean or the base cannot be established;
- a required path outside the owned-path list is needed;
- a dependency beyond the Python standard library appears necessary;
- the local runtime path conflicts with user-owned `var/` data;
- a secret, external project, or network access would be needed; or
- the packet would need to define wrapper/lifecycle behavior beyond this
  foundation.

## Completion and handoff

A valid result has one scoped commit on a non-default branch, all required
checks passing, and complete evidence. It goes to an independent implementation
reviewer. It does not merge or trigger Alpha-02.

## Decision-fidelity carrier map

| Governing choice | Alpha-01 carrier |
| --- | --- |
| Linux-first local operation | Python package, local runtime path, Linux commands |
| SQLite is Maestro's operational store | SQLite connection and idempotent migration metadata |
| Runtime data stays out of Git and within the physical runtime boundary | `var/.gitignore`, M0-D08 enforcement, public-path no-mutation tests, and symlink-race test |
| Project-neutral / synthetic-only Alpha | No adapter, project repository, worker, or external input |
| Atlas read-only and service-mediated | Atlas/API work explicitly excluded |
| Packet wrapper remains mandatory | Explicitly deferred to Alpha-02; no partial/fake wrapper |
| M0-D05 escalation boundary | No worker execution in this packet; it is preserved for Alpha-02 |
| USB recovery gate | Backup implementation and physical provisioning excluded; later Alpha packet |
| No secret inspection | `.env`, credentials, and external access explicitly forbidden |
