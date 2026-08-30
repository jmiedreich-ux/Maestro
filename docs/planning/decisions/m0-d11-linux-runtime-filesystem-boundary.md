# M0-D11 — Linux Runtime Filesystem Boundary

**Status:** Accepted; Alpha assurance profile amended under M0-D12  
**Scope:** Maestro local runtime directories and SQLite files on the Linux AI box  
**Authority:** Owner decisions, 2026-08-30  
**Related:** [M0-D12 — Bounded Quality Contracts and Proportionality](m0-d12-bounded-quality-contracts.md)

## Core decision

Maestro accepts runtime paths only beneath the repository's real physical
`var/` tree. Under the approved operating model, outside-repository paths,
source-tree paths, and paths containing a symlinked component are invalid and
must be rejected before runtime mutation.

This rule applies to every public command, configuration object, constructor,
and storage callable. A rejected path must leave no created directory,
database, journal, WAL/SHM file, log, socket, or other runtime artifact at the
requested or outside location.

## Alpha bounded quality contract

### 1. Protected outcome

Prevent Maestro's trusted local Alpha process from accidentally creating or
opening runtime artifacts outside the repository's physical `var/` tree
because of caller misconfiguration, a source-tree path, an outside path, or a
symlink that exists before the runtime path is acquired for use.

### 2. Operating, threat, and failure model

Alpha runs locally on the Linux AI box as a trusted Maestro user or service
identity. The repository and its `var/` tree are controlled by that trusted
identity.

In scope:

- accidental or incorrect caller-supplied runtime paths;
- direct use of CLI, configuration, constructor, and storage entry points;
- outside-repository and source-tree runtime paths;
- a symlinked component present before the runtime path is acquired; and
- a path component changed before final safe acquisition, where normal
  standard-library checks can observe and reject the change.

The trusted Maestro identity, another same-UID process, and root are not modeled
as concurrent hostile filesystem actors during SQLite's internal open.

### 3. Explicit exclusions

Alpha does not claim protection against:

- a malicious or compromised process running concurrently as the same Linux
  user after Maestro has acquired an open directory file descriptor;
- root, a compromised host or kernel, hostile mount manipulation, or a
  malicious filesystem;
- moving or renaming an already-open runtime directory outside `var/` between
  directory-FD acquisition and SQLite's internal database/WAL/SHM opens;
- multi-tenant or mutually untrusted local users sharing write authority over
  the repository runtime tree;
- a custom SQLite VFS, native extension, mount namespace, privileged helper,
  mandatory-access-control policy, or service-account provisioning; or
- user-selectable/shared runtime volumes, backup/USB behavior, or Alpha-02
  packet-wrapper behavior.

These exclusions are boundaries of the Alpha assurance claim, not permission
for Maestro to knowingly accept an outside or symlinked path.

### 4. Practical assurance level

Alpha requires practical local-development containment for a trusted
single-user/service environment. It does not require adversarial same-privilege
or root containment.

### 5. Sufficient acceptance proof

The Alpha boundary is satisfied when focused tests and recorded commands prove:

- CLI, direct configuration, direct constructor, and storage health paths
  reject outside-repository and source-tree runtime paths before mutation;
- a pre-existing symlinked runtime component, and a component changed before
  final safe acquisition, are rejected without outside artifacts;
- each rejected-path test independently asserts that the attacker-controlled
  outside destination contains no database, journal, WAL/SHM, log, socket, or
  other artifact;
- the default runtime path is independently derived as
  `<worktree-root>/var`, not from the implementation constant;
- repeated valid health checks create state only beneath the physical `var/`
  tree and preserve foreign keys, requested/verified WAL behavior, and durable
  schema version `1`; and
- the evidence and documentation do not claim protection for an excluded
  concurrent same-UID/root rename.

No additional adversarial filesystem proof is required for Alpha once these
named checks pass.

### 6. Permitted implementation boundary and complexity

Use only Python's standard library and built-in `sqlite3`. Keep the correction
within the existing Alpha-01 configuration, storage, and focused-test files.
Do not add dependencies, native code, a custom SQLite VFS, privileged
operations, mount isolation, service provisioning, or a new runtime subsystem.

### 7. Proportionality ceiling

Use the smallest focused change needed to complete the named acceptance proof.
Alpha-01 remains a local foundation packet, not a production host-security
project. One isolated implementation run and M0-D05's one targeted correction
maximum apply.

### 8. Stop and escalation rule

Stop before implementation or further correction if satisfying a proposed
finding would require protection against an excluded same-UID/root race, a
custom VFS/native facility, operating-system isolation, a new dependency, or a
new security policy choice. Record that stronger assurance as later hardening
work; it does not block Alpha-01 when the named proof above passes.

If an in-scope named check fails, classify it as an implementation defect under
M0-D05. If the model or sufficient proof is missing or must change, classify it
as an architecture-contract defect and return it to Architecture and the Owner.

## Alpha-01 consequence

The earlier absolute validation-to-mutation wording did not state a feasible
Alpha threat model or proportionality boundary. That omission caused repeated
implementation/review cycles and is recorded as an Architecture Agent failure.

Alpha-01 now uses this complete bounded contract. The reviewer-confirmed
post-directory-FD same-UID move is outside the Alpha assurance claim and must
not be used as another Alpha implementation gate. The remaining in-scope
outside-path coverage gap may receive one final bounded repair packet after
fresh Decision Fidelity Review.

## Future hardening

Before Maestro is used in a multi-user, hostile-local-process, privileged, or
production service environment, Architecture and the Owner must approve a new
quality contract for that environment. It must choose and fund the required
service identity, permissions, OS isolation, SQLite VFS, or other mechanism
before implementation.
