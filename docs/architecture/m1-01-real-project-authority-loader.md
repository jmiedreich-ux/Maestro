# M1-01 Real Project Authority Loader

## Outcome

M1-01 adds the internal production foundation shared by later `project create`
and `project register` flows. It reads one `maestro.project.yaml` and all
declared authority files from one exact local Git commit, builds an honest
fact inventory, and atomically records either a reviewable Candidate or a
Blocked authority-load run.

It exposes no CLI command and cannot register a project, activate a binding,
write a source repository, contact a remote, use credentials, dispatch work,
open a pull request, merge, deploy, or notify an external system.

## Components

- `project_manifest.py` parses UTF-8 with a custom PyYAML `SafeLoader`. The
  closed version-1 shape rejects duplicate or non-string keys, aliases,
  anchors, merges, tags, unknown fields, invalid types, unsafe paths,
  inconsistent work-graph paths, malformed exceptions, and anything other
  than grammar-valid secret reference identifiers.
- `git_repository.py` accepts one existing local worktree and one full 40-hex
  commit object ID. Its argument-array commands are limited to read-only
  object/ref inspection. It reads blobs directly from the commit tree and
  rejects symlinks, submodules, non-blobs, missing objects, and bounded-size
  violations.
- `project_authority.py` emits the closed result contract. Every required
  manifest leaf and declared authority path becomes a confirmed, missing, or
  conflicting fact. Repository identity, local default-branch containment,
  and the reserved `owner` acceptance boundary are never defaulted.
- `storage.py` advances SQLite from schema version 2 to 3 additively. One
  `BEGIN IMMEDIATE` transaction writes the Candidate when reviewable, the run,
  and one event. Blocked input writes the run and event but no project;
  malformed input reaches no database write.

## Durable model

`projects` holds only Candidate project identity at this stage. M1-01 never
writes `Registered`, `Blocked`, or `active_binding_revision` project state.
`project_registration_runs` retains the immutable request, normalized
inventory, candidate binding when reviewable, authority descriptors, and
result. `events` retains the matching transition evidence. Existing Alpha
tables and rows remain unchanged.

The idempotency key is the SHA-256 digest of canonical JSON containing the
expected repository identity, exact commit, manifest path, and raw manifest
digest. A repeated identical load returns the original durable result. Reuse
of the request ID or idempotency key with different facts is rejected.

## Read-only and failure boundary

The source repository is observed through commit objects; index and worktree
content cannot affect a pinned result. Git uses no shell, checkout, reset,
clean, fetch, branch, commit, worktree, credential, or remote command. Each
authority blob is limited to 2 MiB and the combined payload to 16 MiB.

Migration and authority-load writes are rollback-safe. SQLite uses WAL,
foreign keys, a bounded busy timeout, and `BEGIN IMMEDIATE`, so two concurrent
identical calls serialize to one Candidate, run, and event. Closing and
reopening the service reconstructs the same result from durable columns and
canonical JSON.

## Later ownership

M1-02 may extend the operational state and recovery primitives. Later M1
packets own repository adapters, public create/register commands, binding PRs,
dry-run checks, service lifecycle, and machine-restart proof. Those behaviors
are deliberately absent here.
