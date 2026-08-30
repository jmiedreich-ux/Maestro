# Alpha-01 — Establish Local Foundation

**Status:** Authored; not executable until a fresh Decision Fidelity Reviewer
approves this packet.  
**Owner:** Jeremy Miedreich  
**Authority:** [Maestro Alpha Decision-Fidelity Review](../maestro-alpha-decision-fidelity-review.md)  
**Base:** Current `master` at execution time  
**Execution class:** Bootstrap implementation in a clean isolated worktree  
**Worker route:** Maestro Implementor bootstrap route  
**Reviewer route:** Independent implementation reviewer; cloud GPT-5.6 Sol with high reasoning is the preferred route  
**Timeout:** Stop and report if the packet cannot complete within one focused implementation run.

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
2. It has an explicit configuration boundary for the local runtime directory.
   Its default local database path is under `var/`; it must not write inside
   source, project, or external-repository directories.
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

- the database is created only beneath the supplied runtime directory;
- rerunning it is safe and preserves the recorded schema version; and
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
| Runtime data stays out of Git | `var/.gitignore` and runtime-path tests |
| Project-neutral / synthetic-only Alpha | No adapter, project repository, worker, or external input |
| Atlas read-only and service-mediated | Atlas/API work explicitly excluded |
| Packet wrapper remains mandatory | Explicitly deferred to Alpha-02; no partial/fake wrapper |
| M0-D05 escalation boundary | No worker execution in this packet; it is preserved for Alpha-02 |
| USB recovery gate | Backup implementation and physical provisioning excluded; later Alpha packet |
| No secret inspection | `.env`, credentials, and external access explicitly forbidden |
