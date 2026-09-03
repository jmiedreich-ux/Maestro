# M1-02AR2 — Observable Wiring-Proof Remediation

**Status:** withdrawn by Owner direction on 2026-09-02; never released or dispatchable
**Packet / node:** `maestro-m1-02ar-observable-wiring-proof-remediation` /
`MAESTRO-M1-02AR2-OBSERVABLE-WIRING-PROOF-REMEDIATION`  
**Implementation base:** `27e924f2871c026e8befc236f46025e57a9a7a77` (`H1`)  
**Supersedes:** the returned M1-02AR evidence packet, only for `AR-P05` /
`AR-R04`; it does not supersede accepted M1-02A behavior  
**Authority:** M0-D05, M0-D12, M0-D15, M0-D16, and M0-D17 at
`17bcb10cf21653433abd02e4ec56fe98172c66f7` (to be inherited into the
released planning source); original frozen M1-02AR contract at
`f7e66df`

## Why this is a new packet

The initial AR result `H0=5a7aa234cf92c9b8cb73de64023dfb94a9475ca9` and its
sole correction `H1` changed tests only. Targeted Integration passed and a
fresh adjudicating review confirmed `AR-P06` / `AR-R05` passes. That review
returned only `AR-P05` / `AR-R04`: the M1-02AR map test manually inserted
relation (`Rnn`) labels and the `V24`/`V25` labels rather than observing the
corresponding real route, validation, relation, or failure behavior. Therefore
the old packet has exhausted its frozen correction allowance and cannot receive
another correction. This packet has a fresh base and a smaller, fixed purpose.

The source of truth remains the named finite M1-02AR inventory:
`APP-MAP-01..APP-MAP-21`, `APP-V01..APP-V25`, and
`APP-REL-01..APP-REL-19`, as defined in the original AR packet. This packet
does not reinterpret that inventory or add a new universal claim.

## Dispatch contract

| Field | Fixed value |
|---|---|
| Outcome | Observable, non-injected proof for every named map member, including real V24 and V25 behavior |
| Dependency | Project Architect acceptance of this packet is required before M1-02B/C; no other M1 work is unlocked |
| Roles | Coordinator dispatches; Maestro Developer implements; Integration validates; fresh Independent Reviewer reviews; Project Architect accepts routine result. Owner only receives an M0-D15 reserved choice. |
| Initial route | `codex-cloud-maestro-developer`; Integration `validate-only`; fresh high-risk reviewer |
| Worktree / branch | a clean implementation worktree/branch created from exact `H1`; branch name is recorded at release |
| Locks | `path:tests-m1-02`, `path:maestro-operational-state`, `file:services-maestro-storage` |
| Time / context | one 120-minute initial attempt; `32768` context plus `8192` reserve; report normally below `16384`, hand off below `12288`, stop below `8192` |
| Non-goals | M1-02B/C, schema/API/semantic redesign, parser/framework, dependency/configuration/environment work, external/live/GitHub/credential work, worker/Atlas/service work, merge/deploy/USB |

Normal owned paths are only:

```text
tests/m1_02/test_schema_and_records.py
tests/m1_02/test_context_and_payloads.py
```

`services/maestro/maestro/storage.py` or
`services/maestro/maestro/operational_state.py` may change only when an exact
case below fails at `H1` and shows that existing frozen M1-02 behavior is not
enforced. Record red/green evidence and make the smallest source repair. Any
schema, API, semantic, authority, environment, or dependency change returns to
the Project Architect; it is not a correction inside this packet. No other
path may change.

Release preflight records the source blob IDs for those four paths at `H1`, the
same pinned local Python/SQLite/PyYAML/jsonschema environment used by M1-02AR,
and acquired locks. It does not install, upgrade, or use the network.

## Closed observable proof

`OW-R01` is exact base, environment, paths, and locks. `OW-R02` is complete
observable coverage of the 21 frozen map rows. `OW-R03` is specifically real
SQLite constraint-to-`InvalidRecord` evidence for `V24`. `OW-R04` is specifically
real SQLite busy-exhaustion-to-`ResourceBusy` evidence for `V25`. `OW-R05` is
durable rejection and regression stability. `OW-R06` is scope/handoff.
`OW-R07` is terminal gates and bounded correction. `OW-R08` is acceptance.
`OW-R09` is return/learning.

| Proof | Required evidence |
|---|---|
| `OW-P01` | Coordinator preflight records `H1`, environment, source blobs, locks, and clean worktree. |
| `OW-P02` | Developer produces a machine-checked ledger with exactly `APP-MAP-01..21`; every row arises from one valid real existing public route/builder invocation, records actual validator calls and actual relation observation, and has no injected label or trace entry. |
| `OW-P03` | Developer proves `APP-MAP-21` / `V24` by causing the actual existing SQLite constraint path through the public append route; evidence contains caught `InvalidRecord`, its chained SQLite extended constraint name, and before/after durable state equality. No direct `("V24", ...)` addition or mocked exception is allowed. |
| `OW-P04` | Developer proves `APP-MAP-21` / `V25` by holding a real SQLite write lock until the existing busy timeout expires and invoking the public append route; evidence contains actual `ResourceBusy`, elapsed bounded timeout observation, and before/after durable state equality. No direct `("V25", ...)` addition or mocked exception is allowed. |
| `OW-P05` | Developer reruns the frozen `APP-V01..25` and `APP-REL-01..19` real negative public-route cases; each exact failure has close/reopen, no-row/no-event, FK/WAL, and artifact evidence. This confirms the already-passing AR-P06 result at the new exact head. |
| `OW-P06` | Integration repeats P02--P05 plus all Alpha-01/02/03, M1-01, and M1-02 suites, `compileall`, diff/path/artifact/secret scans, and ten fresh-process M1-02 runs. |
| `OW-P07` | Developer handoff records command outputs, exact observed ledger, each map/member result, V24/V25 causal observations, durable state comparisons, range, source changes (if any), context/usage, gaps, and released locks. |
| `OW-P08` | Integration returns one terminal full crosswalk; a fresh reviewer returns one terminal full exact-range crosswalk. |
| `OW-P09` | Coordinator records either no correction, or one combined normal correction and its targeted Integration/review coverage; a discretionary final correction is possible only under the explicit M0-D17 record below. |
| `OW-P10` | Project Architect records `Accepted` only at a fully covered exact head and records the complete learning/return branch. |

Coverage is closed: `OW-R01->OW-P01`; `OW-R02->OW-P02`; `OW-R03->OW-P03`;
`OW-R04->OW-P04`; `OW-R05->OW-P05,OW-P06`; `OW-R06->OW-P07`;
`OW-R07->OW-P08,OW-P09`; `OW-R08->OW-P10`; `OW-R09->OW-P10`.
Allowed proof states are only `PASS|FAIL`; review states only
`APPROVE|REQUEST_CHANGES`; acceptance only `Accepted|Returned`. No `N/A`,
`UNTESTED`, manually supplied labels, or unobserved map member is permitted.

### What “observable” means

The test may use `unittest.mock` **wrappers** around existing validation helpers
to observe calls, but wrappers must delegate to the original function and may
not manufacture a call, label, return, exception, relation, or trace entry.
The ledger label must derive from the observed helper identity and argument
field, with its deterministic mapping visible in the test. A relation is
observed by the existing route’s actual successful state/output or actual
rejected input relation, not by adding `Rnn` to a set. The test must assert
that the observed ledger equals the frozen map row exactly and that it contains
no unmapped observation.

For each `APP-MAP-01..20`, the route invocation must be the existing named
route/builder in the frozen map and use valid representative facts already
accepted by the M1-02 test fixtures. The implementation may reuse fixture
construction but must not call another test method merely to obtain a prebuilt
ledger. `APP-MAP-21` must execute real append/replay behavior and its V24/V25
subcases must satisfy P03/P04. The original frozen map remains the exact field
and validator/relation enumeration; the released test records its digest and
asserts the compiled expected map is byte-stable from that literal inventory.

## Commands and terminal gates

From `services/maestro/`, with the recorded pinned `PYTHONPATH`, run:

```text
python -m unittest discover -s ../../tests/alpha_01 -v
python -m unittest discover -s ../../tests/alpha_02 -v
python -m unittest discover -s ../../tests/alpha_03 -v
python -m unittest discover -s ../../tests/m1_01 -v
python -m unittest discover -s ../../tests/m1_02 -v
python -m compileall -q maestro
git diff --check H1..HEAD
```

Then run each M1-02 module in ten new processes, exactly as the original AR
packet prescribes. The implementation handoff also records exact changed paths
and a scan proving no generated artifacts or secret/value carriers are added.
No accepted test may be removed, skipped, renamed out of discovery, weakened,
or broadened to an unqualified exception.

Initial Integration and fresh full independent review cover `H1..I0`, where
this packet’s `I0` is its first committed implementation head. Their
complete findings are collected before any normal correction. Targeted follow-up
covers only `I0..I1` and named findings, plus directly affected consistency;
the final coverage chain is recorded exactly. Integration PASS and reviewer
APPROVE do not accept the work; only the Project Architect does.

## Correction, return, and learning

This superseding packet explicitly adopts M0-D17. It allows at most two
implementation corrections: one normal combined correction under M0-D05/M0-D16,
then only one Project-Architect-authorized discretionary final correction.
The final correction is eligible only when all remaining findings are already
against the same frozen `OW-*` proof IDs and same failure class; the normal
correction is committed/in-scope; the remaining fix is localized to the same
owned paths without changing source contract, architecture, schema, API,
product behavior, authority, dependency, configuration, environment, security,
external boundary, lock, or execution route; terminal Integration and targeted
review evidence exists; and the Project Architect writes immutable evidence of
the finding/proof IDs, range, bounded expected diff, and proportionality reason.

No third correction exists. A new failure class, missing/changed requirement,
scope breach, non-delivery, failed correction, unverified observation, or any
ineligible final correction returns the exact head to the Project Architect for
rematerialization. Owner is involved only for an M0-D15 reserved material
choice. The Coordinator must not substitute chat for a durable resolution.

Return and learning records are content-digested and include packet ID, `H1`
base, exact terminal head, failed `OW-*` IDs/class, responsible authority, next
permitted action, evidence references, time at gates, first-pass result,
Integration/full-review/follow-up counts, correction type/count, whether the
failure was compiler-discoverable, and the reusable rule. The expected learning
rule is: “a wiring proof must obtain every map/relation/failure member from an
actual route observation; labels are not evidence.” If no return occurs,
record `PASS:NoReturnRequired` positively, not `N/A`.

## M0-D12 quality contracts

**Q1 — Observable wiring evidence.** Protected outcome: a test cannot claim a
validator/relation route was exercised when it only wrote a matching label.
Model: the finite 21-row frozen map, local Python/SQLite, existing public
routes/builders, wrappers that delegate, and ordinary SQLite errors/locks.
Excludes formal call-graph proof, future routes, alternate databases, hostile
processes, and parser frameworks. Assurance: deterministic test-observed route
and argument/relation evidence for the named finite rows. Proof: P02--P04.
Boundary: two M1-02 test files and conditional smallest existing-contract source
repair. Ceiling: no AST/DDL/general tracing framework or changed semantics.
Stop: any map member needing a new route/semantic/schema/API or an ambiguous
observation returns to the Project Architect.

**Q2 — Durable V24/V25 handling.** Protected outcome: actual SQLite constraint
and busy paths preserve state and translate to the existing public errors.
Model: single local SQLite/WAL database, one held writer lock, public append
route, close/reopen, and finite timeout. Excludes disk corruption, multi-host
writers, hostile mutation, and performance guarantees. Assurance: real local
failure observation and equality of durable pre/post state. Proof: P03--P06.
Boundary: existing database and test facilities only. Ceiling: one controlled
constraint and busy demonstration; no fault-injection framework. Stop: an
environmental/timeout nondeterminism or behavior needing contract change returns
to the Project Architect.

**Q3 — Closed completion.** Protected outcome: the replacement packet does not
reopen AR general discovery or drift into M1-02B/C. Model: exact base/ranges,
fixed proof IDs, paths, gates, and correction rules. Excludes external/live
work, merge/deploy, and unrelated improvement. Assurance: full initial review,
complete terminal Integration, targeted coverage of every correction, and
Project Architect acceptance. Proof: P01, P06--P10. Boundary: this packet.
Ceiling: 120-minute initial attempt and hard maximum of two governed
corrections. Stop: any listed return condition above.
