# M3 — Real Execution Roadmap

**Status:** Architect-authored draft, scoped in a 2026-09-06 planning session
with the Owner; not yet released for packet-level execution.
**Scope:** Decomposes `maestro-master-plan.md`'s M3 line ("replaces fixture
execution with a real packet compiler, real agent executor, and mechanical
grading") into ordered slices, per
[M0-D15](decisions/m0-d15-real-m1-m4-implementation-path.md). Foundry is the
named proving project ([M0-D10](decisions/m0-d10-foundry-v1-proving-project.md),
[M0-D13](decisions/m0-d13-synthetic-control-loop-qualification.md)); an
alternative of using Maestro's own repository as the proving project was
considered and rejected by the Owner in the same session — M0-D10 stands
unchanged.

## Why this exists

M1 already provides a real, tested packet state machine — claim, execution
start/heartbeat/finish, review-control routing (with one bounded correction
pass), acceptance routing, merge-observation routing, correction dispatch —
but every packet that has moved through it so far has been fixture data.
No packet compiler, executor, or grading code exists anywhere in
`services/maestro` today: M3 is greenfield on top of a real but narrow state
machine, not an extension of partial work. This roadmap is the one place
that greenfield build gets decomposed, so no packet has to re-derive it.

## What "packet compiler," "real agent executor," and "mechanical grading"
concretely mean

Cross-referenced against `agent-workforce-control-plane.md` §6.1/§6.2/§11.1:

- **Packet compiler** — turns one owner-approved graph node (§6.1: stable ID,
  outcome, dependencies, allowed change domains) into a materialized packet
  (§6.2: base commit, expected branch, exact allowed/forbidden paths,
  validation commands, evidence format) for a real registered project. Today
  this only happens by hand against fixture data.
- **Real agent executor** — the executor-adapter contract already specified
  in §11.1 (`submit`, `observe/poll`, bounded status request, `cancel`,
  retrieve evidence) actually wired to one real local or cloud worker
  operating in an isolated worktree against a real repository, instead of
  the scripted local actors M0-D13's Alpha-04 qualification used.
- **Mechanical grading** — running a project's own declared checks (for
  Foundry: `npm run check`, `build`, `test:foundation`, `test:browser`) as
  the real verification gate feeding M1's already-built review-control
  routing, instead of a scripted pass/fail result.

## Wave ordering and dependency

Waves are ordered by hard dependency: nothing in Wave A onward can touch a
real repository until Wave 0 (access/credentials) exists; nothing in Wave
C–F can run against a real packet until Wave A (a real registered project)
and Wave B (a real packet materialized from it) exist.

### Wave 0 — Access, secrets, and GitHub identity (backend, gates everything)
[M0-D03](decisions/m0-d03-access-and-secrets.md) is an accepted access-design
decision, but its own "Remaining implementation choices" section lists four
choices never actually implemented. Every later wave that touches Foundry's
real repository depends on this one — even Wave A's read-only discovery,
since M0-D03 rule 1 forbids an ad-hoc personal access token standing in for
a real scoped identity.

1. **W0.1 — Select the local Linux secret provider.** M0-D03's remaining
   choice 1: pick and configure the provider that injects secret values at
   run time; the database only ever stores a reference, never a value.
2. **W0.2 — Register/configure Foundry's GitHub identity.** M0-D03's
   remaining choice 2. **Status (2026-09-06):** the App is provisioned and
   verified directly against the GitHub API — App ID `4746601`
   ("maestro-coordinator"), Installation ID `157167451`, owner
   `jmiedreich-ux`, real PEM private key transferred to the Linux
   coordinator box and permission-locked (`chmod 600`). **Owner decision,
   confirmed 2026-09-06, overriding this slice's original least-privilege
   default:** the App is installed with `repository_selection: "all"`
   (every repo under the account, not scoped to Foundry alone) and holds
   broad write permissions (`actions`, `actions_variables`, `agent_secrets`,
   `checks`, `contents`, `deployments`, `discussions`, `environments`,
   `issues`, `merge_queues`, `pull_requests`, `statuses` — all `write`).
   This is intentionally broader than M0-D03's read-default/scoped-write
   policy and than this slice's original recommended permission table; the
   Owner confirmed this is the wanted configuration, not a misconfiguration
   to remediate. Recorded here so the gap between this App's real scope and
   M0-D03's default guidance is traceable, not silently present. The key
   itself is intentionally not referenced by path in this document (M0-D03:
   secret values/locations are never copied into Maestro packets or
   planning records) — W0.1's actual packet names the reference, not this
   roadmap.
3. **W0.3 — Project-level permission templates.** M0-D03's remaining choice
   3: the general (not Foundry-only) template shape Wave A's registration
   flow assigns from, keyed by adapter capability/action class.
4. **W0.4 — Cloud-worker credential boundary.** M0-D03's remaining choice 4.
   **Not needed for M3's first proof:** `docs/registrations/foundry-read-only-discovery.md`'s
   own proposed binding already states Foundry registration should "permit
   local-Qwen execution only" for its first packets — Wave C's executor
   choice is not actually open, it is local. This slice is deferred, not
   built, until a future milestone chooses a cloud executor.

### Wave A — Real project registration (backend, unblocks everything)
General and project-neutral, not Foundry-hardcoded — M0-D10/M0-D13's own
proving sequence requires read-only discovery, a binding proposal, and a dry
run before any registration, and a general flow means any future project
(VennueSign included) follows the same path, not a Foundry-only shortcut.

5. **A1 — Read-only project discovery.** Given a repository reference, walk
   its declared structure (manifest, SOP, environments, gates) per
   `agent-workforce-control-plane.md` §12's adapter requirements. No writes,
   no binding yet. Uses Wave 0's GitHub identity. **Foundry-specific note:**
   `docs/registrations/foundry-read-only-discovery.md` already exists but is
   explicitly self-described as stale — it references packet/assignment
   state (e.g. CG-M4-18's disputed status across Issue #6, `tracker/
   assignments.json`, and `PROJECT_STATUS.md`) that predates this session
   and that document's own text says must be refreshed before real
   registration. This slice must re-run discovery against Foundry's current
   state, not reuse that cached document as authoritative input to A2.
6. **A2 — Project binding proposal.** Turn a completed discovery into a
   reviewable, Owner-approvable binding record: branch/PR/merge policy,
   authoritative SOP path, environment/credential-reference policy, gate
   commands. Not yet active. This is M0-D10's proving-sequence step 1.
7. **A3 — Non-dispatching dry run.** Validate an approved binding against
   the project's declared paths and gates without dispatching any work —
   proves the binding is honest before anything real depends on it. This is
   M0-D10's proving-sequence step 2.
8. **A4 — Register.** Persist an approved, dry-run-passed binding as an
   active project record. Foundry is the first real project to walk it, but
   the flow itself is not Foundry-specific. **Correction from the Decision
   Fidelity check:** this wave only covers M0-D10's proving-sequence steps
   1–2, not 1–3 as an earlier draft of this file claimed — step 3 ("show
   Foundry's live observed state in the fresh reporting view") is not
   satisfied until Wave E's Atlas wiring (E4) is real; step 4 (packet
   selection) is B3, not A4.

### Wave B — Packet compiler (backend)
9. **B1 — Graph node ingestion.** Read one approved graph node (§6.1 fields:
   stable ID, outcome, dependencies, allowed change domains) from a
   registered project's declared graph source at an exact commit.
10. **B2 — Packet materialization.** Compile one ingested node into a real
    packet record (§6.2: base commit, expected branch, exact allowed/
    forbidden paths, validation commands, evidence format, reviewer route) —
    the same packet shape M1's state machine already consumes, now populated
    from real project data instead of a fixture.
11. **B3 — Packet selection for Foundry's first proof.** Apply M0-D10's
    selection rule (one unclaimed, explicitly released packet — not the
    active Popover packet or anything with in-flight state) against
    Foundry's real registered graph. This is M0-D10's proving-sequence step
    4.

### Wave C — Real agent executor (backend)
12. **C1 — Executor adapter scaffold.** The versioned capability contract
    from §11.1 (`submit`/`observe`/`cancel`/retrieve evidence) as an
    interface with no real backend wired yet — proves the shape against a
    still-scripted implementation first. Must implement §9.1's required
    preflight (base commit, clean worktree, allowed/forbidden paths, locks,
    context/model identity) as the adapter's own precondition contract, not
    a later add-on.
13. **C2 — Local Qwen wired to C1.** **Decided, not open:** per
    `docs/registrations/foundry-read-only-discovery.md`'s own proposed
    binding, Foundry's first packets permit local-Qwen execution only —
    the first real executor is a local worker, not a cloud one. Isolated
    worktree, scoped repository/environment access per §11.1's
    least-privilege baseline (no production credentials, protected branches
    remain protected) and Wave 0's W0.2 credential boundary. W0.4 (cloud
    credential boundary) is not required for this slice.
14. **C3 — Real dispatch of one materialized packet.** Submit a Wave B
    packet through C2 and observe it to completion — no grading or merge
    yet, proves the executor loop alone. The attempt's result must satisfy
    §9.2's required handoff shape (branch/commit identifiers, changed-file
    list and scope check, executed commands and verbatim evidence,
    `PASS`/`N/A`/`UNTESTED` per check) so Wave D has a real handoff to grade
    rather than an ad-hoc result shape.

### Wave D — Mechanical grading (backend)
15. **D1 — Declared-check runner.** Given a registered project's declared
    gate commands (Foundry: `npm run check`, `build`, `test:foundation`,
    `test:browser`), run them against C3's §9.2 handoff evidence and record
    a structured pass/fail evidence record.
16. **D2 — Wire D1's result into M1's existing review-control routing.**
    Real mechanical grading now feeds the same `record_and_route_review`
    path M1's fixture packets already used — no new routing logic, only a
    real evidence source.

### Wave E — Real event stream and reconnect (backend; unblocks Atlas M2 follow-ups)
Named in `m2-atlas-roadmap.md` as dependent on this exact milestone
("real live data first exists to synthesize from"); building it here both
serves M3's own executor (which needs to emit real events) and unblocks the
three M2 Atlas slices that were rescheduled to M3.
17. **E1 — Event stream (SSE).** `GET /stream/events`: live-tails new
    `events` rows as Wave C/D's real executor and grading activity produces
    them. This is exactly `m2-atlas-roadmap.md`'s **A6**, carried here.
18. **E2 — Reconnect/resync contract.** Client-supplied last-seen event id;
    server replies with exact gap-fill or a resync-from-snapshot signal.
    Exactly `m2-atlas-roadmap.md`'s **A7**.
19. **E3 — Narrative-synthesis layer over the real event stream.** The
    actual product-design gap `m2-atlas-roadmap.md`'s C2 entry identified:
    today's `events` carry machine `event_type`/`before_json`/`after_json`/
    `reason`, not authored prose a packet thread can render. **Decided (not
    an open question):** a read-time synthesis layer over E1's structured
    events, not a new written "thread message" record — per master plan
    operating principle #3 ("there must never be two independently
    writable truths for the same fact"), a second write-time narrative
    surface alongside `events` would itself be the violation this principle
    forbids. `events` stays the single writer; this slice only adds a read
    path.
20. **E4 — Wire Atlas's packet thread to E1–E3 (`m2-atlas-roadmap.md` C2).**
    Same view C1 already built, now reading real snapshot + stream data
    instead of fixtures. This is also what satisfies M0-D10's
    proving-sequence step 3 (see A4's correction note above).
21. **E5 — Wire owner-decision card buttons to the real D2 command
    (`m2-atlas-roadmap.md` D3).** Requires a real `packet_id` and
    `expected_version` from Wave B/E4. **Correction from the Decision
    Fidelity check:** `record_and_dispatch_correction` is not missing — it
    is a real, already-implemented M1 command
    (`services/maestro/maestro/operational_state.py:809`), exactly as this
    roadmap's own "Why this exists" section already lists "correction
    dispatch" among M1's built routing. The actual, narrower gap is that
    D2's guarded HTTP command endpoint never calls it for the "Amend the
    A.1 contract" option — this slice is that wiring only (map D2's amend
    branch to the existing internal method with a real `packet_id`/
    `expected_packet_version`/`review_id`), not new command design. No open
    judgment call remains for E5.
22. **E6 — Wire crash-card recovery buttons to the real D6 command
    (`m2-atlas-roadmap.md` D7).** Same real-packet dependency as E5. Of the
    crash card's three options (resume / re-dispatch / hold), only "hold"
    has a real backend counterpart today — confirmed against
    `operational_state.py:555-584`: `NeedsReplan` closure only ever
    transitions to `Cancelled`, no automatic resume/re-dispatch path
    exists. **Decided (not an open question):** build real resume/
    re-dispatch semantics in this wave, not a re-defer. Resume/re-dispatch
    are meaningless against a synthetic executor — they only become
    buildable once Wave C's real executor exists to resume or re-dispatch
    against, and that dependency lands exactly here, in M3, per the same
    standing policy already applied to A6/A7 and C2/D3/D7. Sequenced after
    Wave C.

### Wave F — Foundry proving run (end to end)
23. **F1 — One full real proof.** Run Wave A's registered Foundry project
    through Wave B's compiler, Wave C's executor, Wave D's grading, and
    M1's existing review-control routing to `AwaitingOwner`/`MergeReady`,
    with Wave E's real event stream visible in Atlas throughout (this is
    M0-D10's proving-sequence step 5). Stop for Owner acceptance. **No
    automatic merge** — matches M0-D10/M0-D13 exactly.

## Open questions

None remaining. E3, E5, and E6 were each flagged as open judgment calls in
an earlier draft of this file; all three are now resolved by direct
Architect application of already-standing policy (master plan operating
principle #3 for E3; the same dependency-lands-in-M3 scheduling policy
already used for A6/A7/register-create for E6; a Decision Fidelity
correction of a false claim for E5) rather than deferred back to the Owner
for a call this roadmap's own governing documents already answer. See each
slice's entry above for the specific reasoning.

## What is explicitly out of scope for M3

- Specialist planned queues, real local-model routing policy, and
  first-class Integration-role operation. **Note (Decision Fidelity
  check):** `agent-workforce-control-plane.md` §13 describes these as later
  work but never states a V2/M4+ correspondence table — the "V2/M4+" label
  here is this roadmap's own Architect inference from the old phasing
  described in `maestro-master-plan.md` §9, not a directly cited fact. It
  should be confirmed (or corrected) as part of packetizing this exclusion.
- Parallel dispatch of independent packets, numeric concurrency/cost
  thresholds (same inference basis as above).
- Webhook transport as a primary signal — polling/reconciliation remains
  the recovery authority per §11.1; a webhook may accelerate observation
  only as a later addition.
- Any auto-merge or autonomous-next-work authority (master plan §2.12: this
  is always explicit, project-bound, reviewed, and revocable — never
  implied by this roadmap).
- The M4 autonomous Architect/Development-Manager ruling loop itself.
- Registering VennueSign or any project other than Foundry (Wave A's flow
  is built general-purpose, but only Foundry is actually registered here).

M3 is one packet, one worker, one review, one Owner-gated merge proven real
— not workforce or parallelism.

## Execution order

Wave 0 must complete before A (M0-D03 rule 1 forbids read-only discovery
itself using an ad-hoc credential — W0.1/W0.2 gate A1). A must complete
before B (no real graph to compile from without a registered project). B
must complete before C (nothing to dispatch without a materialized
packet). C before D (nothing to grade without an attempt). E can start
once C begins producing real events (E1/E2 do not depend on D), but
E4–E6 depend on E3 being built first (its design is decided, not open —
see E3's entry above — but the read path itself must exist before
anything can be wired to it).

**Correction from the Decision Fidelity check:** F does not depend only on
D. F1 requires Owner acceptance, and Atlas is the only Owner interface
(master plan §3) — so F also depends on at least E1/E2/E4 being real, not
only on D. The prior draft's execution-order section omitted this. Revised
order: **Wave 0 → A → B → {C → D, and E1/E2 in parallel once C exists} →
E3 (decision) → E4 → {E5, E6 in parallel} → F.** F is last regardless: it
is the actual proof, exercising every prior wave together.

Each numbered item above becomes its own canonical packet contract
(`docs/planning/packets/m3-*.md`), reviewed and executed one at a time under
the Bootstrap Convergence Policy's bounded review sequence.
