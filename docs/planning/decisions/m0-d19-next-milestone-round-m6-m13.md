# M0-D19 — The Next Milestone Round (M6–M13), Planned from M0-D18

**Status:** **Draft for Owner review, 2026-09-09.** The Owner approved writing
this record up; the milestone set in §5 has **not** been ruled on and is marked
`[PROPOSAL]` throughout. One prior `[OPEN]` item is closed here (§2).
**Type:** Milestone plan. Extends, and does not amend,
[M0-D18](m0-d18-real-wiring-audit-authority-and-architect-loop.md).

**Authority.** M0-D18 is the governing authority for this plan and is not
re-derived here. Its audit finding (§2), its rulings on the Architect loop
(§5), the ReturnSlice path (§6), registration triggering an Architect repository
review (§4), evidence and completion (§7), Atlas as first class (§8) and
configurability (§11a) are inputs to this record, not restated by it. Where this
record and M0-D18 differ, M0-D18 wins.

**Provenance rule, inherited from M0-D18 and kept.** Every statement below is
marked:

- **[OWNER]** — the Owner said this. Quoted verbatim.
- **[OWNER — substance]** — the Owner agreed this in a prior session and the
  substance is settled, but **no verbatim quote was captured**. Used only where
  that is genuinely the case, and never merged with the category above.
- **[PROPOSAL]** — the assistant's inference or recommendation. Not authority.
- **[FINDING]** — a fact verified against the code on 2026-09-09, with the file
  and line that proves it.
- **[OPEN]** — genuinely unresolved.

M0-D18 exists in part because an earlier draft blurred these. The extra
`[OWNER — substance]` category is added here rather than quietly filing
unquoted agreements as `[OWNER]`.

---

## 1. Scope of this record

M0-D18 §12 lists what the next milestone round must account for: the Architect
loop (§5), the ReturnSlice path (§6), registration triggering an Architect
repository review (§4), Atlas as a first-class surface (§8, alongside M5 which
stands), the evidence rules (§7) and the discipline in §9. This record proposes
that round as **M6–M13**, plus the pre-milestone corrections in §4.

It also writes up two items that M0-D18 does not contain: **re-registration
that supersedes** (§6) and **multi-project support** (§7). Both were agreed in
substance in the session that produced M0-D18 and were never written down.

This record does not authorize implementation. It proposes a plan for a ruling.

---

## 2. §5.3 resolved — per-step reasoning budget is measured, not enforced

M0-D18 §5.3 was the single remaining `[OPEN]` item on the decision list:
whether the reasoning budget is capped per step, whether dispatch is refused at
preflight, what happens at the checkpoint boundary, and whether history is
re-sent whole or summarised.

**[OWNER] Resolved 2026-09-09.** On whether the budget is capped per step:

> "Let's just collect for research and understanding so we know what the numbers
> actually represent"

On refusing dispatch at preflight:

> "Out of scope because of question 1"

On the checkpoint boundary:

> "Out of scope"

On history between steps:

> "Summarised after a threshold"

**The ruling.** Per-step reasoning usage is **instrumented and reported, not
enforced**. Maestro records what each step of an attempt actually consumed so
the numbers can be understood before any policy is built on them. There is no
per-step cap, no preflight refusal of dispatch, and no automatic action at the
checkpoint boundary — the second and third follow from the first and are
explicitly out of scope. Between steps of one attempt, history is **summarised
past a configured threshold** rather than re-sent whole.

**[PROPOSAL]** The threshold is a configuration value under M0-D18 §11a, not a
constant. What is pinned verbatim across every step — the packet specification,
allowed and forbidden paths, and the declared checks — versus what is summarised
is an implementation question for M10 (§5), not a policy question.

**[PROPOSAL]** The rest of M0-D18 §5.3's framing survives this ruling and is not
discarded: the exposure it names is real, and instrumentation is what makes it
visible. A later decision to enforce would then be made against Maestro's own
measured numbers rather than against another project's published account.
`attempt_context_usage` — written by no production path per M0-D18 §2 — is the
table this fills.

**[FINDING]** `context_policy_json` and `validate_context_policy` exist and
enforce ordering of the declared thresholds at write time. Nothing reads them at
run time. This ruling does not change that; it adds the measurement that would
make the thresholds meaningful.

---

## 3. Verified code state, 2026-09-09

M0-D18's audit was run on 2026-09-08. These are the findings re-verified at
`ad614b7` before this plan was written, because M0-D18 §11 carries a standing
Owner instruction to stop assuming.

- **[FINDING] The loop still asserts reviews that did not happen.**
  `services/maestro/maestro/development_manager.py:329` and `:334` record
  `result="Approve"` for an `IndependentImplementation` review with the actor
  literal `"development-manager-loop-independent"`. `:414` calls `accept_packet`
  with `required_authority="Owner"` and delegation
  `"development-manager-loop"`. `:425` calls `observe_merge`, which performs a
  real merge. No guard, flag or configuration disables any of it. **The single
  post-M0-D18 code commit (`ad614b7`, the `run-attempt` CLI) does not touch
  this path.** M0-D18 §10 step 1 is therefore **not** implemented.
- **[FINDING] No operational configuration file exists.**
  `services/maestro/maestro/config.py` defines `RuntimeConfig` as paths only.
  The repository contains one `.toml` (`services/maestro/pyproject.toml`) and no
  `.yaml`/`.yml` at all. M0-D18 §11a is entirely unbuilt.
- **[FINDING] No role contract is ever read.** `role_contract_reference` is
  interpolated into a prompt line at `development_manager.py:180` and stored as
  a string. No code path opens any file under `docs/agents/`.
- **[FINDING] The work graph has no parser and no generator.** `work_graph_path`
  appears only in `project_manifest.py` (lines 27, 58, 125, 181), where it is
  validated as a string and required to occur in `plan_paths`. Nothing reads
  the file's contents.
- **[FINDING] `resource_locks` has no `project_id`.**
  `storage.py:905` defines the table; `storage.py:1106` creates
  `one_active_resource_key` as a **globally** unique index on `resource_key`
  where `state='Active'`. Two projects contending on the same resource key
  cross-block each other.
- **[FINDING] Atlas is still largely fixture-rendered.** Of 56 non-test source
  files under `apps/atlas/src`, four reach the read API
  (`readApiBaseUrl.ts`, `thread/useRealPacketThread.ts`,
  `crash/realCrashCommands.ts`, `decision/realDecisionCommands.ts`).
  `shell/NowTab.tsx`, `shell/PlanTab.tsx` and `shell/ActivityTab.tsx` import
  from fixture modules in production code, not only in tests.
- **[FINDING] One agent-shaped subprocess path exists.**
  `executor.py`'s `LocalQwenExecutorAdapter`, driven by
  `attempt_onboarding.run_attempt`. Other `subprocess` use is git and check
  execution (`git_repository.py`, `check_runner.py`, `review_readiness.py`).
- **[FINDING] The Alpha wrapper is still synthetic and still separate.**
  `packet_wrapper.py:40` — *"Controlled local fixture executor; it never invokes
  a model or subprocess"* — confirming M0-D18 §5.4.2's note that the grading
  concept existed and did not survive into the real execution path.
- **[FINDING] The CLI exposes ten commands** (`health`, `run-packet`,
  `review-readiness`, `serve-read-api`, `discover-project`, `register-project`,
  `materialize-packet`, `claim-packet`, `run-attempt`, and the development
  manager loop). There is no Architect command, no scheduler command, and no
  configuration command.

Nothing in the 2026-09-08 audit has been overtaken by events. The plan below is
built on that.

---

## 4. Before any milestone: two corrections, not scope

**[PROPOSAL]** M0-D18 §10 steps 1 and 2 are not milestone work and should not be
scheduled as any. They should land on `master` directly, ahead of M6.

**Step 1 — stop the loop asserting reviews that did not happen.** This is a
deletion, not a design: remove the two self-authored writes at
`development_manager.py:329`/`:334`, stop the cycle at `MergeReady`, and notify.
The loop then becomes what it honestly is — a scope-and-checks gate that hands
off.

**[PROPOSAL] Why it is urgent rather than merely correct.** Every cycle that
runs writes durable, append-only records asserting an independent review and an
Owner acceptance that never occurred. Those records are precisely what the
milestones below read. The cost of leaving it compounds; the fix is an hour.

**[PROPOSAL] Why it is not a milestone.** M9 (§5) deletes it. The stop-and-
notify is interim safety with a known, scheduled replacement — a real
Independent Reviewer. Designing it as scope would be designing something with a
committed expiry date.

**Step 2 — correct the record.** M0-D18 §7.4 keeps M2 and M4 closed, and
`[PROPOSAL]` there notes that closure asserts delivered packets only, not a
working product. `docs/planning/maestro-development-status.md` and the M4
roadmap should say so plainly, so the next session does not build on "M4
complete" as though the product functions.

**M0-D18 §10 steps 3 and 4 are scheduled**, not pre-milestone: step 3 (the
wiring check) lands in M6, and step 4 (one real agent role end to end, the
Architect recommended) is M6 plus M7.

---

## 5. [PROPOSAL] The milestone round: M6–M13

### 5.0 A standing rule, applying to every milestone in this round

**[PROPOSAL]** Every milestone in this round ships **its own Atlas surface as
part of its own definition of done**. Atlas is not a trailing milestone and no
milestone in this round is complete while its states are visible only in a
terminal.

This follows from M0-D18 §8 — *"there will be no terminal window eventually"* —
and from its `[PROPOSAL]` that a fixture-rendered surface is a defect rather
than a placeholder. It is stated as a rule because a trailing Atlas milestone
is how the fixtures in §3 came to exist: the surface was scheduled after the
capability, the capability shipped, and the surface rendered a fixture.

**M5 is unaffected.** Its navigation scope is separately Owner-approved, remains
in force per M0-D18 §8, and continues in parallel. This rule adds surfaces for
new states; it does not redefine M5.

---

### M6 — Agent runtime foundation

**Why first.** Six of nine designed roles are string literals and one agent-
shaped subprocess path exists (§3). Every milestone after this one is "build a
real role". M6 is the machinery that makes a role real, built once, so that M7
onward add judgment rather than plumbing.

Scope, deliberately small, per the standing instruction to split aggressively:

1. **The deterministic wrapper** (M0-D18 §5.4, §5.4.1, §5.4.2). A script wraps
   the packet's agent delegation. It commits the whole worktree when the worker
   did not (§5.4, scope already resolved by the Owner: commit all, let the
   existing `allowed_paths` check produce the precise finding), creates the
   branch if the worker did not, caps captured output, and runs the
   **model-shaped check set** — leftover stubs, `TODO: implement`, placeholder
   headings, duplicated sections, debug output, accidentally committed generated
   artifacts. **A single failure blocks; nothing proceeds to review.**
2. **The configuration file** (M0-D18 §11a). Maestro's own operational tuning,
   with the two Owner-approved boundaries: project policy stays in each
   project's `maestro.project.yaml`, and durable schema constraints stay in
   code. M6 moves the thresholds it needs and establishes the file; later
   milestones add their own values to it rather than adding constants.
3. **Role contracts actually loaded.** `docs/agents/` files are opened, read and
   supplied to the agent. `role_contract_reference` stops being a filename in a
   prompt line.
4. **The wiring/orphan gate** (M0-D18 §7.3, recovery step 3). Mechanical:
   commands with no non-test caller, tables with no production writer, columns
   read by nobody, components mounted nowhere. Run as a gate. Note the Owner's
   scope — **both** Maestro and the products Maestro builds.

**Proved by** re-hosting the **existing** qwen worker on the wrapper. M6
introduces no new role. That is what keeps it small and what makes its claim
falsifiable.

**Consequence for the reviewer contract.** M0-D18 §5.4.2 rules that
`docs/agents/independent-review-agent.md`'s *"secrets, generated artifacts,
debug code, placeholders, unsafe defaults"* belong in the wrapper. M6 moves
them and amends the contract, so the reviewer is told what was already
verified rather than asked to re-check it.

---

### M7 — Architect: repository review produces the work graph

**M0-D18 §4**, the Owner's ruling that registration triggers an Architect review
of the repository which writes the work-graph file — *"doesn't the registration
process supposed to do a review of the repo to build its file"* — rather than a
human authoring YAML.

Scope: `register-project` spawns a real Architect against a real repository; the
Architect writes a real work-graph file; a parser reads that file into real work
items. Both the generator and the parser are unbuilt (§3) and both are required.
Registration also owns **consistent milestone naming** (M0-D18 §4:
*"The registrion process should make the milestone naming consistent"*), with
the conversational form the Owner asked for — `M4.01`, `M4.01A`.

**This is M0-D18 §10 step 4**: one real agent role, end to end, on real data,
before scaffolding others. The Architect is the recommended first role because
it unblocks the pipeline and produces the graph everything else reads.

**Evidence bar** (M0-D18 §7.1, fake data banned): proved against a real
repository, not a fixture manifest. Foundry v1 (M0-D10) and Maestro's own
repository are both real candidates.

---

### M8 — The Architect loop, to the Owner gate

**M0-D18 §5, steps 1–4** of the Owner's own account of the loop.

Scope: packetize all available milestones; run **bounded** fidelity review
rounds — configurable N from M6's file, with the bound that stops it looping
forever, per *"should not be so strict it never proceeds further"*; **stop for
Owner review, presented in Atlas**; Owner approves in Atlas.

The two fidelity standards the Owner named are the reviews' criteria:
**smallest possible packets**, and **no latent or unknown scope**.

**Atlas surface (§5.0):** the Owner review gate itself, and the
blocked-waiting-on-Architect state. Per M0-D18 §8 these are required, not
optional.

**[PROPOSAL]** The Architect's own repository (M0-D18 §5 — *"escalation to the
project architect which lives in it's own repo"*) becomes real here. Its current
working files, `architect/handoff.md` and `architect/memory.md`, are the
practice today and not the intended home. Escalation to it is a handoff of
facts, not a function call.

---

### M9 — Real reviewers: Independent Reviewer and Integration Agent

**M0-D18 §5, steps 5–7.**

Scope: the Independent Reviewer and the Integration Agent become real spawned
agents with loaded contracts. The Integration Agent performs **both** functions
the Owner named across §5 and §6 — it **wires the part into the product**, and
it performs an **independent review that the parts align properly**. Both are
required.

**This milestone permanently replaces §4's pre-milestone stop-and-notify.** The
loop stops asserting reviews because a reviewer now actually exists, not because
a flag suppresses the write.

**[PROPOSAL]** Review capacity is the resource this round spends most carefully
(M0-D18 §5.4.1: *"it saved time and doesn't force time wasted on subsequent
reviews"*). M9 is where that becomes literal, and it is why M6's wrapper must
precede it.

---

### M10 — The Development Manager becomes a manager

**M0-D18 §5.1, §5.2, and §2's five decorative fields.**

Scope:

1. **Continuous scheduling**, using **cloud reasoning** (Owner-ruled, §5.1): a
   small reusable process re-evaluating every cycle which eligible packet runs
   next, on which worker, given current locks, leases, worker health and WIP.
   This makes `planned_rank`, `dependencies_json`, `change_domains_json`,
   `execution_classes_json` and `priority` live inputs. Declared dependencies
   start blocking.
2. **Restart** of stopped, killed or silent workers — automatic, no Owner or
   Architect involvement (§5.2).
3. **Context allocation** per agent (§5.2), making M0-D14's context stack a live
   input with a named owner.
4. **Model escalation** past a restart threshold (§5.2), making model routing a
   runtime decision rather than only a plan-time label.
5. **Per-step usage instrumentation** and history summarisation past a
   threshold, per §2 of this record. Measurement only.

**[PROPOSAL]** M0-D18 §5.1 notes scheduling is high-turn and low-judgment-per-
turn, so its "cloud reasoning" should name a **fast** model. That belongs in
M6's configuration file, not in code.

**[FINDING]** `record_worker_progress` is defined at
`operational_state.py:2457` and **called from nowhere**; `blocker_payload_json`
is likewise uncalled, and the orchestrator polls only OS process liveness. M10
is where they acquire callers, which is what makes M0-D18 §2's stopped-worker
finding — the Owner's *"How would this be reported and I assume maestro would
resume it?"* — actually answerable.

---

### M11 — The ReturnSlice path

**M0-D18 §6**, the Owner's scenario in full: a mis-scoped packet is raised by
the reviewer or by the coding agent itself, goes to the Development Manager, is
handed to the Architect loop, is split into two packets — one eligible now, one
scheduled into a later milestone — returns to the Manager, and on completion
goes to the Integration Agent to be wired in and reviewed, then back to the
Manager to commit and release dependents.

Rulings this carries:

- **Split packets get fresh review/correction budgets** (§6.1, amending the
  Bootstrap Convergence Policy). *"always lean towards giving the product the
  best chance to get built"*.
- **The Architect has the last word on carry-forward** (§6.2), bounded by one
  condition: the decision must not cause further replanning. Starting the packet
  over is the default.
- **Total blockage is a legitimate state**, not only partial — *"some if not all
  work could be blocked"*.

**Existing vocabulary this wires up, built but unused:** `ReturnSlice` as a
finding disposition, `Assemble` as a review result, `NeedsReplan` as both a
packet state and a review result, and `blocker_payload_json` for the coding
agent raising the problem itself.

**Why it is placed after M8, M9 and M10:** it is the one path that exercises all
three. Building it earlier means building it against roles that do not exist.

---

### M12 — Re-registration that supersedes

Loose end 1. Written up in full at §6 of this record.

---

### M13 — Multi-project

Loose end 2. Written up in full at §7 of this record.

---

## 6. Loose end 1 — re-registration that supersedes

**[OWNER — substance]** Agreed in the session that produced M0-D18 and never
written up. No verbatim quote was captured; the substance below is settled, the
mechanics are `[PROPOSAL]`.

**The requirement.** A project that is already registered must be able to be
registered again — its plan changed, its repository moved on, its milestones
were re-cut. Re-registration **supersedes** the previous binding rather than
replacing it, and it must **not reopen completed work**.

**[FINDING] The schema is already shaped for this and is entirely unreachable.**
`project_bindings` carries `binding_revision`, `superseded_at`, and a
`UNIQUE(project_id, binding_revision)` constraint (`storage.py:736`, `:750`,
`:751`). The `Superseded`, `Stale` and `NeedsReplan` states exist. **No
`UPDATE project_bindings` statement exists anywhere in the codebase**;
`project_onboarding.py:58` writes `superseded_at: None` and nothing ever
writes it again. `storage.py:344` updates `projects.active_binding_revision`,
which is the only moving part today.

**[PROPOSAL] What M12 must build:**

1. **A real `source_hash` over project bytes.** M0-D18 §2 found that graph rows
   are insert-only and `source_hash` derives from operator input rather than the
   project's own content, which makes `Stale` and `NeedsReplan` unreachable **by
   construction**. Re-registration is not detectable without a hash over what is
   actually in the repository. This is why M12 depends on M7 — the Architect's
   repository review is what reads those bytes.
2. **Supersede rather than replace.** The prior binding transitions to
   `Superseded` with a real `superseded_at`; the new revision becomes active.
   The history of what was registered when survives, which is the point of an
   append-only record.
3. **Re-projection that reconciles.** The new work graph is diffed against the
   existing work items. Merged and completed items **stay closed**. Only new,
   changed and unstarted items become actionable. Re-registration must never
   resurrect finished work.
4. **Staleness becomes reachable.** `Stale` and `NeedsReplan` on a graph become
   states the system can actually enter, which is what makes
   `staleness_detector.py` mean something.

**[PROPOSAL] The relationship to M0-D18 §6.2.** Re-projection reconciling is
the same principle as the Architect's carry-forward ruling, applied at project
scale instead of packet scale: preserve what is genuinely finished, redo what
the change has invalidated, and do not create further replanning by preserving
work that then has to be unpicked.

### 6.1 [OWNER] Registration is refused while work is in progress

**[OWNER] Ruled 2026-09-09**, when asked whether an in-flight packet whose work
item changed under re-registration is returned to the Architect or allowed to
finish against the superseded revision:

> "Simple, registration cannot take place when there is active work in progress"

**The ruling.** The question does not arise. Re-registration is **refused**
while the project has active work. Drain first, then re-register. There is no
in-flight packet straddling two binding revisions, because the state that would
produce one cannot be entered.

**[PROPOSAL] Why this is the better answer and not merely the simpler one.**
Routing the question to the Architect, as this record previously proposed, would
have made every re-registration a replanning event whose cost is unknown until
the Architect has judged it. Refusing registration makes the cost knowable
before the operator commits: the answer is either "yes" or "finish or cancel
these packets first", and the second is a list the operator can act on. It also
removes the entire class of reconciliation bug where a packet's work item
changes underneath a running worker. M0-D18 §6.2's bound — the decision must not
cause further replanning — is satisfied by construction rather than by judgment.

**[PROPOSAL] What counts as active**, implementing the ruling against the real
state vocabulary in `storage.py:826`. Registration is refused when the project
has any run in `Running`, `Blocked`, `AwaitingArchitect` or `AwaitingOwner`. It
is permitted when every run is `Complete` or `Cancelled` — and when every run is
`Planned`, which is the state `register-project` itself leaves a run in, so a
project that registered and never started can always be re-registered.

**[PROPOSAL]** The refusal reports **which** runs and packets are holding it, not
merely that it was refused. An operator told "refused" has to go looking; an
operator told "M4.03 is Running, M4.05 is AwaitingOwner" can act. This is the
same principle as M0-D18 §5.4's ruling on committing the worktree: let the
existing checks produce the precise finding rather than a useless generic one.

**[PROPOSAL] The Atlas surface** (§5.0) is the blocked-registration state and
the list of work holding it, so the drain is visible without a terminal.

---

## 7. Loose end 2 — multi-project support

**[OWNER — substance]** Agreed in the session that produced M0-D18 and never
written up. No verbatim quote was captured; the substance below is settled, the
mechanics are `[PROPOSAL]`.

**The requirement.** Maestro runs more than one project. Locks scope **per
project**; there is **one loop for all projects**, not one loop per project; and
the Development Manager runs as a Linux **service account**.

### 7.1 Locks scope per project

**[FINDING] Projects currently cross-block.** `resource_locks` (`storage.py:905`)
has **no `project_id` column**, and `one_active_resource_key`
(`storage.py:1106`) is a **globally** unique index on `resource_key` where
`state='Active'`. Two projects that both hold a packet touching, say,
`src/main.py` contend on the same key even though they share no code.

**[PROPOSAL]** Add `project_id` to `resource_locks` and make the active-lock
index unique per `(project_id, resource_key)` for `Path` and `SharedBoundary`
locks. **`FiniteResource` locks stay global** — the GPU, the local model host
and anything else genuinely shared are shared *across* projects, and that is
exactly the case the lock kind exists for.

### 7.2 One loop, not one per project

**[OWNER — substance]** One loop serves all projects.

**[PROPOSAL] The reason is arbitration, and it is what makes the single loop
non-negotiable rather than merely convenient.** The scarce resources —
the GPU, the local model host, cloud reasoning budget — are shared across every
project. Two independent loops would each schedule against a resource neither
of them owns, and the `FiniteResource` locks of §7.1 would become the only
arbiter, resolving contention by collision instead of by judgment. One loop
means one scheduler with the whole picture, which is what M10's continuous
scheduling assumes.

**[PROPOSAL]** M10's scheduling therefore ranks eligible packets **across
projects**, not within one. Whether projects carry relative priority, or are
served fairly, is a scheduling parameter belonging in M6's configuration file.

### 7.3 The service account

**[OWNER — substance]** The Development Manager runs as a Linux-hosted service
account.

**[FINDING] None of this exists.** There is no service account and no GitHub
App. The GitHub API integration is dead in the precise sense: `real_discovery.py`
imports `github_client`'s `fetch_file_content` and `fetch_repository_metadata`
and wraps them as `fetch_real_repository_metadata` and
`fetch_real_process_file`, and **those two wrappers have no callers anywhere**.
The one path that does reach `real_discovery` from the CLI
(`discover-project` -> `project_discovery.discover_project` ->
`evaluate_snapshot`) evaluates a snapshot it is handed and never fetches
anything. `secrets.py` has **no importer at all**.

**[PROPOSAL]** M13 gives the Manager a real identity: a Linux service account
that owns the runtime directory and the database, and a GitHub App identity for
the operations M0-D18 §9's discipline requires — branches, pull requests,
review submission. The commits Maestro authors then carry an identity that is
neither the Owner's nor a developer's, which is a precondition for the SOP in
§9 being followed rather than described.

**[OWNER] The `var/` constraint stays, ruled 2026-09-09**, when asked whether it
would have to move to accommodate a service account:

> "having the the var folder is fine for db, and installation"

**The ruling.** `var/` is the right home for the database and the installation.
`config.py`'s `validate_runtime_dir` is not a problem to be solved, and M13 does
not need to move it. The service account is given ownership of `var/` rather
than the runtime being relocated to suit the account.

This resolves, for the database and installation specifically, the tension left
by M0-D18 §11 — which places the runtime directory out of scope while recording
that the Owner had called the *"must live inside `<maestro-repo>/var/`"*
constraint *"unpractical"*. **[PROPOSAL]** Read together, the two statements are
consistent: `var/` is right for durable state Maestro owns, and the earlier
objection was to the constraint being applied to *everything* a runtime touches.
Nothing in M13 requires reopening it, and this record does not.

**[PROPOSAL]** M0-D18 §11's packaging layout is unaffected: versioned code under
`/usr/local/lib/maestro/<version>/` with `/usr/local/bin/maestro` as the symlink
remains the future install shape, with `var/` holding the database beneath it.

---

## 8. [PROPOSAL] Ordering, and why

**M6 before M7 is the load-bearing choice.** Building the Architect first,
without the wrapper, means the first real role spends attempts and bounded
review rounds on deterministic misses — the exact cost M0-D18 §5.4.1 exists to
prevent, incurred by the role whose output everything else depends on.

**M8, M9 and M10 before M11.** ReturnSlice is the path that exercises the
Architect loop, both reviewers and the Manager at once. Built earlier, it is
built against roles that do not exist.

**M12 and M13 last, but M13 is closer to mattering than its position suggests.**
Foundry v1 (M0-D10) and Maestro building Maestro are two real projects. The
global lock index in §7.1 means they cross-block the moment they run
concurrently. Running them sequentially is a legitimate answer until M13; it
should be a known constraint rather than a surprise.

**Recovery step 1 is throwaway by design** and that is the argument for doing it
as a deletion now rather than designing it as scope. M9 removes it.

---

## 9. [PROPOSAL] Definition of done for this round

M0-D18 §3 rules that **functioning is the floor** — *"Clearly the product has to
function"* — and §7.3 asks for a check that the product actually gets built.
Applied to this round:

- No milestone in M6–M13 is complete on schema plus tests. A **real caller in a
  real path** must exist, and M6's wiring gate is the mechanical check for it.
- No milestone is complete while its states are visible only in a terminal
  (§5.0).
- Evidence is a **rerunnable command plus its output**, reported honestly as
  `PASS` / `N/A` / `UNTESTED` (M0-D18 §9). Where something genuinely cannot be
  tested against real data, it is reported `UNTESTED` with residual risk — never
  substituted with a fixture (§7.1).
- The discipline of M0-D18 §9 applies to this round's own development: a branch,
  a pull request, an independent review never by the author, and a completed
  Done Record as a merge precondition. M4.01–M4.17e were pushed straight to
  `master`; this round is where that stops.

**[PROPOSAL]** Known limitations remain acceptable on top of a functioning
product when they are judged acceptable and tracked on a real backlog
(M0-D18 §3). What may never be accepted is a non-functioning capability reported
as delivered — which is the whole of what the audit found.

---

## 10. Open items

- **[OPEN] §5 as a whole.** The M6–M13 set, its ordering, and the pre-milestone
  corrections in §4 are `[PROPOSAL]` awaiting an Owner ruling. The Owner
  approved writing this record; the plan itself has not been ruled on.
- **Closed 2026-09-09 by Owner ruling:** §6.1 (registration is refused while work
  is in progress) and §7.3 (`var/` stays, for the database and the
  installation). Neither is open.
- **Carried from M0-D18, still outstanding:** the plain, non-technical start-up
  runbook the Owner asked for repeatedly — *"I don't want to see the code I want
  to see a list if steps to start maestro"* — and the missing start-up commands
  the Owner already authorized into M5 (*"Yes build those and I would like that
  process added to m5 as well"*). Neither is scheduled by this record.
  **[PROPOSAL]** the runbook is a deliverable of M6, since M6 is the first point
  at which the start path is stable enough to write down.
- **Carried from M0-D18 §2, still outstanding:** the audit report is an external
  artifact link. It should be committed into the repository as a durable
  planning input.

---

## 11. What this record would authorize

Once ruled on, this record authorizes the decomposition of M6–M13 into packets —
by the Architect loop itself once M8 exists, and by hand before that. It does
not authorize implementation of any milestone, and it does not amend M0-D18.

M0-D18 §5.3's `[OPEN]` item is closed by §2 of this record, and the two open
items this record itself raised were closed by Owner ruling on 2026-09-09
(§6.1, §7.3). **The milestone set in §5 is the only thing awaiting a ruling.**
