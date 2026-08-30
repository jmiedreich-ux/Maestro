# Alpha-01-R2 — Complete Bounded Local Foundation

**Status:** Complete — exact implementation head `3124378f3ba885cb066d1426b1a0ed5a5d0ccb6f` received Independent Implementation Review `APPROVE` on 2026-08-30
**Approval record:** Full Decision Fidelity Review approved the exact planning head `65b6c7745c75f935430012cf49fef528120a6d5a`; its only provenance finding received targeted independent approval after `alpha-01-r1-runtime-boundary`, `b476cdc`, and `e2c8a08` became remotely verifiable. This status record changes no execution instruction or scope.  
**Owner:** Jeremy Miedreich  
**Authority:** [Alpha-01 — Establish Local Foundation](alpha-01-local-foundation.md); [M0-D11 — Linux Runtime Filesystem Boundary](../decisions/m0-d11-linux-runtime-filesystem-boundary.md); [M0-D12 — Bounded Quality Contracts and Proportionality](../decisions/m0-d12-bounded-quality-contracts.md)  
**Base:** The complete R1 implementation result at `e2c8a08` on `alpha-01-r1-runtime-boundary`, after verifying its provenance and exact diff from `b476cdc` in a clean isolated worktree  
**Execution class:** One final bounded repair in a new clean isolated worktree and non-default branch  
**Worker route:** Normal bounded Maestro Implementor route  
**Review route:** Fresh Independent Implementation Review of the complete result; serious renewed review uses GPT-5.6 Sol at high reasoning  
**Timeout:** One focused implementation run; stop rather than expanding scope

## Plain outcome

Complete only the remaining in-scope Alpha-01 outside-path coverage under the
trusted-local M0-D11 contract. Preserve the working R1 implementation unless a
new named in-scope test proves a concrete defect.

This packet does not attempt to defeat the excluded malicious concurrent
same-UID/root post-directory-FD rename. It does not redesign the runtime
boundary.

## Why this is the final bounded repair

R1's nine focused tests and repeated health checks passed. Independent review
found:

1. a post-directory-FD same-UID move that created SQLite artifacts outside
   `var/`; and
2. incomplete outside-repository coverage for CLI/direct-constructor paths.

The Owner-approved M0-D11 reconciliation explicitly excludes finding 1 from the
Alpha threat model. Finding 2 remains in scope and is the only implementation
defect this packet may address.

## Owned paths

The Implementor may change only:

- `services/maestro/maestro/config.py`
- `services/maestro/maestro/storage.py`
- `tests/alpha_01/test_local_foundation.py`

Prefer a test-only correction when the existing implementation already passes
the missing named coverage. Change `config.py` or `storage.py` only when a
new required test proves an in-scope implementation defect.

No other path is authorized.

## M0-D12 quality contract

The complete eight-field Alpha quality contract is in M0-D11 and controls this
packet:

1. **Protected outcome:** prevent accidental outside runtime mutation caused by
   invalid, source-tree, outside, or pre-acquisition symlinked paths.
2. **Model:** trusted local Linux Maestro identity; caller misuse and
   pre-acquisition path/symlink changes are in scope.
3. **Exclusions:** malicious concurrent same-UID/root mutation after
   directory-FD acquisition, compromised host/kernel/filesystem, custom VFS,
   native/privileged isolation, and multi-tenant hostile users.
4. **Assurance:** practical trusted-local Alpha containment, not adversarial
   same-privilege host containment.
5. **Sufficient proof:** the named entry-path/no-artifact tests plus repeated
   healthy SQLite checks described below.
6. **Implementation boundary:** Python standard library and built-in
   `sqlite3`; only the three owned files; no new subsystem.
7. **Proportionality ceiling:** smallest focused correction, one isolated run,
   M0-D05 correction limit.
8. **Stop rule:** stop if stronger excluded assurance, a new dependency,
   native/custom VFS, OS isolation, broader files, or a new policy choice would
   be required.

No field is N/A.

## Required behavior

1. Preserve the default runtime path independently derived as
   `<worktree-root>/var`.
2. Preserve rejection of source-tree, outside-repository, and pre-acquisition
   symlinked runtime paths at public CLI, configuration, constructor, and
   storage entry paths.
3. Preserve no-artifact behavior for every rejected in-scope path.
4. Preserve repeated valid health behavior: foreign keys enabled,
   requested/verified WAL, durable idempotent schema version `1`.
5. Do not claim or add the excluded post-directory-FD same-UID/root guarantee.

## Required focused tests

The test suite must explicitly and independently cover:

- CLI with an outside-repository runtime path;
- direct `RuntimeConfig` construction with an outside-repository runtime path;
- direct `SQLiteFoundation` construction with an outside-repository runtime
  path;
- a storage health call whose previously valid path becomes an invalid or
  symlinked path before final safe acquisition;
- the corresponding source-tree public-entry rejections already required by
  Alpha-01;
- a pre-existing symlinked runtime component;
- a component changed before final safe acquisition;
- independently derived default `<worktree-root>/var`; and
- repeated valid health with schema version `1`, foreign keys, and WAL.

Each rejected-path test must use its own controlled outside destination and
assert that destination remains empty of every database, journal, WAL/SHM, log,
socket, directory, or other runtime artifact.

Do not add a blocking test for moving an already-open directory after
directory-FD acquisition. That scenario is explicitly outside the Alpha
contract.

## Required commands and evidence

Run and record:

```bash
cd services/maestro
python -m unittest discover -s ../../tests/alpha_01 -v
python -m maestro.cli health --runtime-dir ../../var/alpha-01-r2-check
python -m maestro.cli health --runtime-dir ../../var/alpha-01-r2-check
```

Evidence must include:

- verified base `e2c8a08` and its exact provenance from `b476cdc`;
- new branch and final commit;
- exact changed-file list;
- complete command output and exit status;
- test names mapping to every required public-entry path;
- explicit per-test no-artifact assertions/results;
- both valid health outputs and resulting schema version;
- confirmation that generated runtime/test artifacts were removed only inside
  the isolated worktree; and
- confirmation that no excluded assurance claim, external access, secret,
  network, merge, or Alpha-02 work occurred.

## Explicit exclusions

Do not:

- implement or test the excluded post-directory-FD malicious same-UID/root
  rename as an Alpha gate;
- add dependencies, native code, a custom SQLite VFS, mount namespace,
  privileged helper, permission/service-account provisioning, or shell helper;
- create packet wrapper, worker, queue/lifecycle schema, API/UI, Atlas,
  Foundry/VennueSign integration, USB recovery, GitHub automation, or network
  behavior;
- modify `.env`, root `.gitignore`, documentation, runtime data, or any path
  outside the three owned files;
- merge, deploy, push to `master`, or begin Alpha-02.

## Stop and escalate

Stop without improvising if:

- base `e2c8a08` or its full provenance cannot be verified;
- the work requires any path outside the owned list;
- the existing implementation fails for a reason outside the named coverage;
- stronger assurance requires an excluded actor/mechanism;
- a dependency, native/custom VFS, OS policy, secret, network, external
  repository, or user-owned runtime path would be needed; or
- the packet cannot complete in one focused run.

## Completion and handoff

A valid result is one scoped commit on a new non-default branch, complete named
evidence, and all checks passing. It receives one full Independent
Implementation Review of the complete result. Any authorized correction then
receives only targeted follow-up verification under M0-D05. The final exact
merge candidate must have complete review coverage: the full reviewed range
plus every targeted-reviewed correction-only diff.

Approval does not itself merge or authorize Alpha-02.
