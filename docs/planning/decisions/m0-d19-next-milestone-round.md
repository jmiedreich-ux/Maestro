# M0-D19 — The Next Milestone Round, Planned from M0-D18

**Status:** **Draft for Owner review. Revision 2, 2026-09-09.**
Revision 1 was written the same day, subjected to three independent reviews at
the Owner's direction, and found defective. This revision replaces it entirely.
The milestone set in §8 has **not** been ruled on and is `[PROPOSAL]` throughout.
**Type:** Milestone plan. Extends, and does not amend,
[M0-D18](m0-d18-real-wiring-audit-authority-and-architect-loop.md).

**[PROPOSAL] What the Owner has actually seen.** The last milestone set the
Owner read is revision 1's M6–M13. **Revision 2's set (§8) has never been put in
front of the Owner** — it was written after the Owner ended the session, and M6,
the proving run that reorders the whole round, was offered in the session's
final assistant turn and left unanswered. Read §8 as unreviewed by the Owner in
the strongest sense: not merely unruled, but unseen.

**[PROPOSAL] How this record landed, recorded because §13 makes it a rule.** The
Owner directed the merge — *"upload it to master merge and do several
independent fidelity review"* — and it was taken directly to `master` with no
pull request, no Done Record, and the fidelity reviews run **after** the merge
rather than before it. That is the sequence the Owner asked for, and it is also
a departure from the discipline §13 states as binding on this round. M0-D18 §9's
lesson is that a grant of autonomy does not suspend the SOP, so the departure is
recorded here rather than left for someone to notice. **[OPEN]** whether a Done
Record and a retrospective pull request should be raised for M0-D19 itself.

**Authority.** M0-D18 is the governing authority. Its audit finding (§2) and its
rulings are inputs to this record, not restated by it. Where this record and
M0-D18 differ, M0-D18 wins — except on the two points of §5, where M0-D18 is
factually wrong about the code and an Owner ruling is requested.

## Provenance rule, inherited from M0-D18

- **[OWNER]** — the Owner said this. Quoted verbatim.
- **[OWNER — session]** — the Owner said this in the 2026-09-09 planning session
  that produced this record, rather than in M0-D18. **Checkable:** every such
  quote appears verbatim in
  [the committed session evidence](evidence/m0-d19-owner-session-2026-09-09.md).
- **[PROPOSAL]** — assistant inference or recommendation. **Not authority.**
- **[FINDING]** — verified against the code at `ad614b7`, with file and line.
- **[OPEN]** — genuinely unresolved.

**Revision 1 abused this convention and the abuse is recorded here rather than
quietly repaired.** It presented M0-D18 §10 — a section M0-D18 marks in bold as
**"Not agreed"** — as an inherited plan, six times, and never once reproduced
those words. The Owner had additionally flagged it in the session's opening
instruction: *"the recovery sequence (§10, which is a proposal, not agreed)"*.
Revision 1 also invented a category, `[OWNER — substance]`, for agreements it
could not quote. That category is withdrawn; the material it covered is now
`[OWNER — session]`, sourced to the Owner's own words in this session's
transcript, quoted in §10 and §11.

---

## 1. What this record is

M0-D18 §12 requires the next milestone round to account for the Architect loop
(§5), the ReturnSlice path (§6), registration triggering an Architect repository
review (§4), Atlas as first class (§8, alongside M5), the evidence rules (§7)
and the discipline (§9). This record proposes that round.

It also carries three things M0-D18 does not:

- the two loose ends the Owner named in this session — re-registration that
  supersedes, and multi-project support (§10, §11);
- **two factual errors in M0-D18 itself** (§5), which is Owner-approved and so
  cannot be corrected without a ruling;
- the results of the independent review round the Owner ordered (§6), including
  **the largest unknown in the plan, which revision 1 never named** (§7).

It does not authorize implementation.

---

## 2. §5.3 resolved — per-step reasoning budget is measured, not enforced

M0-D18 §5.3 was its last `[OPEN]` item.

**[OWNER — session] Resolved 2026-09-09.** On whether the budget is capped per step:

> "Let's just collect for research and understanding so we know what the numbers
> actually represent"

On refusing dispatch at preflight:

> "Out of scope because of question 1"

On the checkpoint boundary:

> "Out of scope"

On history between steps:

> "Summarised after a threshold"

**The ruling.** Per-step reasoning usage is **instrumented and reported, not
enforced**. No per-step cap. No preflight refusal. No automatic action at the
checkpoint boundary. History is **summarised after a threshold**.

### 2.1 The costing this ruling was given under was wrong

**[PROPOSAL] — a correction the Owner is owed.** The assistant presented
"measurement only" as cheap, and the ruling was made against that framing. It is
not cheap.

**[FINDING] There are no steps to measure.** `executor.py:113` submits one
prompt — `qwen -p <instructions> --yolo` — and `executor.py:125` observes it with
`process.poll()`. Maestro never sees a turn boundary, a token count or a message
history. It cannot summarise a history it does not hold, and it cannot count a
step it never observes.

**[FINDING]** `record_context_usage` (`operational_state.py:2462`) and
`update_context_usage` (`:2499`) have zero non-test callers, and
`record_context_usage` requires a `configured_context_limit` and
`starting_input_tokens` — numbers that need a tokenizer or a provider usage
report. Neither exists.

**[PROPOSAL]** Instrumenting per-step usage therefore requires replacing the
one-shot subprocess with a Maestro-driven agent loop that owns the conversation.
That is the largest single piece of engineering implied anywhere in this round.
It is scheduled at M11 (§8), not as a bullet inside a Development Manager
milestone as revision 1 had it. **The ruling stands; only its cost was
misstated.**

---

## 3. Verified code state, 2026-09-09 at `ad614b7`

M0-D18 §11 carries a standing Owner instruction to stop assuming. Every claim
below was re-verified before this plan was written.

- **[FINDING] The loop still asserts reviews that did not happen.**
  `development_manager.py:329`/`:334` record `result="Approve"` for an
  `IndependentImplementation` review with actor
  `"development-manager-loop-independent"`. `:414` calls `accept_packet` with
  `required_authority="Owner"`. `:425` calls `observe_merge`, a real merge. The
  only post-M0-D18 code commit (`ad614b7`) does not touch this path.
- **[FINDING] The Integration review is fabricated too.**
  `development_manager.py:310`/`:315` route `result="ValidateOnly"` with
  `reviewer_instance="development-manager-loop-integration"`. Revision 1's
  instruction to "stop at `MergeReady`" was wrong: stopping there leaves a
  durable record asserting an Integration review by an agent that does not
  exist. See §7.1.
- **[FINDING] No production path produces `RequestChanges`.**
  `review_dispatch.py:70` defaults `result: str = "Approve"`, and no production
  caller passes anything else. `development_manager.py:269-280` says the loop
  "can never mechanically produce a real `RequestChanges` **from a coverage
  blocker**" — narrower than revision 3 implied, but the grep is decisive:
  `RequestChanges` appears in no production code path. `correction_count` is
  therefore always 0 in practice.
- **[FINDING] The bound that is missing is the Architect's, not the packet's.**
  Revision 3 said there is "no bounded review-round count anywhere in the code",
  which is false: `storage.py:964` — `correction_number INTEGER NOT NULL
  CHECK(correction_number IN (0,1))` — is exactly that, and `storage.py:854`
  bounds `correction_count` the same way. What does not exist is **M0-D18 §5's
  configurable N**, the number of Architect fidelity review rounds. The two are
  different bounds and M15 must not conflate them: the correction budget is a
  durable schema constraint and stays out of the config file per M0-D18 §11a;
  N is genuinely absent and is the file's first real value.
- **[FINDING] One correction per packet, enforced in the schema.**
  `storage.py:854` — `correction_count INTEGER NOT NULL DEFAULT 0 CHECK(correction_count IN (0,1))`.
  Per M0-D18 §11a, schema constraints are not tuning knobs, so this cannot be
  relaxed in the configuration file.
- **[FINDING] One `Initial` attempt per packet.** `storage.py:899-901` —
  `UNIQUE(packet_id,attempt_number)` plus a CHECK confining attempt 2 to a
  `TargetedCorrection` with a non-null `correction_for_review_id`. See §5.1.
- **[FINDING] A packet corrected *through the correction helper* can never be
  accepted.** `operational_state.py:2141` rejects the acceptance unless the
  approving review carries `review_correction_number == 0`, and
  `review_dispatch.route_correction_review` hardcodes `correction_number=1`.
  `development_manager.py:408` already dodges it with
  `if packet is None or packet["correction_count"] != 0: continue`.
  **Narrower than revision 3's "never":** `operational_state.py:1723-1726`
  explicitly permits a packet with `correction_count == 1` down the ordinary
  approval route, whose review carries `correction_number == 0` and which
  acceptance accepts. The defect is in the correction helper, not the store.
- **[FINDING] No operational configuration file exists.** `config.py` defines
  paths only. The repository holds one `.toml` and no `.yaml`.
- **[FINDING] No role contract is ever read.** `role_contract_reference` is
  interpolated as a filename at `development_manager.py:180`. No code path opens
  anything under `docs/agents/`.
- **[FINDING] The work graph has no format, no parser and no generator.**
  `work_graph_path` appears in `project_manifest.py` (27, 58, 125, 181, 184), the
  project schema and two test modules — everywhere as a validated string. `docs/schemas/maestro-project-v1.schema.json:28` types it as
  a repository path. No specification file exists anywhere.
- **[FINDING] Neither real project has a manifest.** `project_authority.py:126`/`:134`
  reads `maestro.project.yaml` and raises without it; `project_manifest.py:184` requires
  `work_graph_path` to occur in `plan_paths`. Neither
  `/home/jeremy/Development/Foundry` nor this repository contains one.
- **[FINDING] Registration still takes hand-typed work items.**
  `project_onboarding.py:66` reads `request["work_items"]`; `:68` computes
  `source_hash` from `graph_projection_id` plus sorted work-item ids — operator
  input, never project bytes. This is the design M0-D18 §4 rejects.
- **[FINDING] `ExecutorAdapter` is the only agent entry point, and its *inputs*
  are git-typed.** `executor.py:65`. `ExecutorPreflight` requires `base_commit`
  and an existing clean `worktree_path` at that commit, plus `allowed_paths`,
  `forbidden_paths` and `model_identity`. A role with no packet — the Architect
  at registration — cannot supply them. **Correcting revision 3:** the *outputs*
  are less constrained than it claimed — `ExecutorHandoff` also carries
  `raw_output: str` and `completed: bool`, and `commit_sha` is `str | None` — so
  a non-commit result can be returned. The blocker is the mandatory git input,
  not the output shape.
- **[FINDING] There is no cloud model client, and no dependency that could be
  one.** No reference to any cloud model API anywhere in `services/`.
  `services/maestro/pyproject.toml:6` declares three runtime dependencies:
  `PyYAML`, `PyJWT`, `cryptography`. No HTTP client.
- **[FINDING] `secrets.py` has no production importer.** Its only importers are
  three test modules under `tests/m3_wave_0/` and `tests/m3_wave_a/`. (Revision 3
  said "no importer at all. Not one." — false as written.)
- **[FINDING] The GitHub integration is dead in a precise sense**, and M0-D18
  §2's "dead code" is true but not in the obvious way. `real_discovery.py`
  imports `github_client`'s `fetch_file_content` and `fetch_repository_metadata`
  and wraps them as `fetch_real_repository_metadata` and
  `fetch_real_process_file` — and **those two wrappers have no callers
  anywhere**. The path that *does* reach `real_discovery` from the CLI
  (`discover-project` → `project_discovery.discover_project` →
  `evaluate_snapshot`) evaluates a snapshot it is handed and fetches nothing.
- **[FINDING] There is no `git clone` anywhere in the codebase.**
  `git_repository.py` exposes three public read-only operations against a path it is
  handed. The Architect's own repository has no transport.
- **[FINDING] `resource_locks` has no `project_id`**, and `storage.py:1106`
  creates `one_active_resource_key` as a **globally** unique index on
  `resource_key`. Two projects contending on the same key cross-block.
- **[FINDING] The migration contract forbids the fix as written.**
  `storage.py:424-431` — versions 4 and 5 "deliberately use only `CREATE`,
  `ALTER ... ADD COLUMN` and index/trigger creation. In particular, accepted
  tables are never rebuilt." A `NOT NULL project_id` needs a rebuild, and
  replacing the index needs a `DROP INDEX`. See §7.3.
- **[FINDING] No `UPDATE work_items`, no `UPDATE graph_projections`, no
  `UPDATE project_bindings` exists.** The `Superseded`, `Stale` and `NeedsReplan`
  planning states are unreachable by construction, and
  `storage.py:1103`'s `one_active_graph_per_project` means a second projection
  cannot be inserted while the first is `Active`.
- **[FINDING] Notifications cover 2 of 8 required events.**
  `notification_triggers.py` defines four; `development_manager.py:64` imports
  two. `escalation_at` is written literally `None` at
  `notification_triggers.py:59` and read by nobody. **Acknowledgement has no
  code** — one comment at `operational_state.py:2345`. Slack does not exist.
- **[FINDING] Backup and recovery is zero code.** No snapshot writer, no
  manifest, no retention, no restore test.
- **[FINDING] Atlas has no reachable write path.** The read API exposes six
  routes (`read_api.py:455`), five of them snapshots — packets, attempts, reviews, events, stream —
  and **no `work_items` or `graph_projections` endpoint**. Four POST command
  routes exist (`read_api.py:1007`) but every UI button is gated on an optional
  `real?:` prop that no non-test file ever passes. **Two of the four are worse
  than disabled:** `OwnerDecisionCard.tsx:135` uses `disabled={!real || …}` and
  renders disabled, but `CrashCard.tsx:127-128` uses
  `disabled={real && index !== 0 ? … : undefined}`, so without `real` the
  buttons render **enabled and silently inert**.
  `App.tsx:29` passes no `systemState`, so crash, disconnect and empty states are
  unreachable. The active packet is a hardcoded constant in
  `shell/realActivePacket.ts`.
- **[FINDING] The read API has no authentication, and is not loopback-bound.**
  `_validate_command_envelope` (`:465`) checks that `idempotency_key` is
  non-empty and `actor` is a dict — nothing else. Anything that can reach it can
  POST `actor: Owner`. And it is **not** confined to loopback as revision 3
  said: `read_api.py:32-37` reads `MAESTRO_READ_API_ALLOWED_HOST` from the
  environment and `:51` unions it into the allowed set, an Owner-approved
  exception of 2026-09-06. The unauthenticated Owner-authority surface can be
  bound to an arbitrary host by an environment variable.
- **[FINDING] Executor handles live in memory.** `executor.py:104` — a plain
  dict on the adapter instance. If the Development Manager process dies, every
  running attempt becomes unobservable and uncancellable.

---

## 4. What has and has not happened — corrected

**[OWNER]** M0-D18 §2 records the Owner's own correction:

> "Yes but the so called loop didn't develop this"

Its scope is precise, and M0-D18 states it precisely: *"Every line of **M4** was
written by the assistant, not produced by Maestro's own loop."* That is about
**Maestro's own development**.

**[FINDING] Revision 2 over-generalised it to "no model has completed a Maestro
packet," and that is false.** A record-consistency review found the
counter-evidence and it verifies in the world, not only in prose:

- `docs/registrations/foundry-read-only-discovery.md:77-103` records a real
  dispatch proof against Foundry on 2026-09-06.
- `/home/jeremy/Development/Foundry` contains commit
  `740f548ebf23d60b5e1e951b0e718b420ac7bd4a` — *"CG-M4-19: add Menu browser
  checks"* — on `origin/codex/m4-19-menu-browser-checks`. Real, pushed.
- `var/foundry-persistent/runtime/maestro.sqlite3` holds two `Succeeded`
  attempts by `qwen3.6:27b`, and three reviews:
  `('review-cg-m4-19-integration-1','maestro-integration-1','NeedsReplan')`,
  then `ValidateOnly`, then
  `('review-cg-m4-19-independent-2','owner-real-review-1','Approve')`.

So a local model completed a real packet against a real project, **including the
correction-and-replan path**, and a real reviewer — not the fabricated
`development-manager-loop-*` literal — approved it.

**[FINDING] The sample is small and mixed.** `var/maestro.sqlite3` also holds
`('attempt-cg-m4-20-1','Failed',None,'qwen3.6:27b')` and
`('attempt-cg-m4-20-2','Running',None,'qwen3.6:27b')`. One packet completed; the
next failed and its retry was never resolved.

**What has actually never happened**, stated at the width the evidence supports:

1. **Maestro's own loop has never driven a packet end to end.** The Foundry proof
   was driven by hand through the CLI — its reviewer instances are
   `maestro-integration-1` and `owner-real-review-1`, operator identities, not
   `run_cycle`. This is the Owner's finding, unchanged.
2. **Maestro has never built any part of Maestro.** Also unchanged.
3. **No one has measured the distribution.** One success, one failure, one
   unresolved. Nothing supports a review-round bound, a restart threshold or a
   correction budget.

§8's M6 is rewritten accordingly: it is not "can an executor complete a packet",
which is answered, but "what do the existing samples say, and what does the loop
do when it drives them."

**[PROPOSAL] A second reading the Owner should rule on.** If
`docs/registrations/foundry-read-only-discovery.md` overstates what happened,
then it is a false capability record on master — exactly the class M0-D18 §7.4
and §7.2 exist to correct — and it must be corrected rather than relied on. It
cannot both stand as proof and be ignored as the plan's premise. Revision 2 did
the latter by never opening it.

---

## 5. [OPEN] Two factual errors in M0-D18, for an Owner ruling

M0-D18 is Owner-approved, so these are raised rather than corrected.

### 5.1 §5.4's "one of the packet's two attempts" understates the cost

M0-D18 §5.4 says a worker that produced good code but no commit consumes "one of
the packet's two attempts."

**[FINDING]** `storage.py:899-901` gives a packet exactly one `Initial` attempt.
Attempt 2 is constructible only as a `TargetedCorrection` carrying a real
`correction_for_review_id` — which requires a real `RequestChanges`, which no
production path produces (§3). A forgotten commit therefore consumes the
packet's **only** attempt, and recovery is a whole new packet via
`redispatch_after_needs_replan`.

**[PROPOSAL]** The ruling in §5.4 is strengthened, not weakened, by this. Only
the stated cost needs correcting.

### 5.2 WITHDRAWN — M0-D18 §5.4.2 is correct and this record was wrong

**Revision 3 of this record claimed M0-D18 §5.4.2's "This existed and was lost"
was false. An independent verification review found the claim was a misreading,
and it verifies. The charge is withdrawn.**

M0-D18 §5.4.2 says: *"The Alpha packet wrapper graded exactly this class —
`lifecycle.py` rejects on 'dependency/configuration/placeholder violation' — and
the concept did not survive into the real execution path."*

**[FINDING] Both halves are true.** `lifecycle.py:52-57`:

```python
if result.violations:
    return LifecycleDecision(
        REJECTED,
        "CoordinatorEscalation",
        f"dependency/configuration/placeholder violation: {result.violations[0]}",
    )
```

A verbatim match for M0-D18's quoted string, in the Alpha wrapper, grading that
class — and absent from the real path. This record had cited `lifecycle.py:18`,
a docstring on the *input* dataclass, and never opened lines 52–57, which are the
code under discussion.

**[FINDING] The true, narrower finding.** The **grading rule** existed and still
exists. Only the **detector** feeding `result.violations` was fixture-fed:
`packet_wrapper.py:139-146` returns `(f"unapproved {scenario…}",)` from a
scenario string in the packet JSON.

**[PROPOSAL] What survives for M17.** The check set still has to be built —
there has never been a detector — but it is **restoration of a rule with a
missing implementation**, not net-new invention, and M0-D18's framing was right.
The check list remains an explicit unknown at M17.

**[PROPOSAL] Why this is recorded rather than deleted.** This record asked the
Owner to rule that an Owner-approved document was factually wrong about the
code, on the strength of a line the record had not read. That is the same
failure — asserting without verifying — that M0-D18 §11's standing instruction
exists to stop, committed by the record written to apply it.

---

## 6. The independent review round

**[OWNER — session]** The Owner ordered this after reading revision 1's
milestone set:

> "Consider doing a independent ago fidelity check on what you just gave me, the
> build order doesn't hold for me"

Three independent reviews were run against the code and the documents: a
decision-fidelity review of revision 1 against M0-D18, an adversarial attack on
the build order, and a scope-and-sizing review against the Owner's two
packetization standards. **The Owner's objection was correct.** Revision 1's
central ordering argument was wrong on both halves:

- **[FINDING] It was a category error.** Revision 1 argued the wrapper must
  precede the Architect. A packet requires a work item, which requires a graph
  projection — the artifact the Architect *produces*. At registration there is
  no packet, no attempt, no lease, no `base_commit`, no branch. The wrapper had
  nothing to wrap. `review_readiness.py:80-98`'s entire blocker vocabulary
  presupposes a commit range on a checked-out repository.
- **[FINDING] The cost it protects does not exist yet.** With no production
  `RequestChanges` and no bounded round count (§3), the wrapper would have
  protected a budget of zero until real reviewers exist.

The reviews also found: nine of M0-D18 §2's findings mapped to no milestone;
six of eight milestones broke revision 1's own Atlas rule; M6 bundled four
deliverables sharing no dependency; and the plan's largest unknown was unnamed.
All are addressed below.

---

## 7. Before the round

**[PROPOSAL] These are corrections, not milestones — but they follow the SOP.**
Revision 1 said they "should land on `master` directly." That was wrong and
contradicted revision 1's own §9: M0-D18 §9's whole lesson is that a grant of
autonomy does not suspend the discipline. Each goes on a branch, through a pull
request, with independent review and a Done Record.

### 7.1 Stop the loop asserting reviews that did not happen

**[PROPOSAL]** Stop the cycle at **`AwaitingIntegration`**, not `MergeReady`, and
notify. M0-D18 §10 step 1 and revision 1 both said `MergeReady`; both were
wrong, because the Integration review is fabricated too (§3). Deleting only the
independent review leaves packets piling up behind a review that never comes,
while the durable record still asserts an Integration review by a
non-existent agent.

This is a deletion with a known replacement (M17), which is why it is not
scope. It is urgent because every cycle writes append-only records asserting a
review and an Owner acceptance that never occurred, and those records are what
the milestones below read.

### 7.2 Correct the record

M0-D18 §7.4 keeps M2 and M4 closed while noting closure asserts delivered
packets only. `docs/planning/maestro-development-status.md` and the M4 roadmap
should say so plainly.

### 7.3 Scope the lock index now, while the database is disposable

**[PROPOSAL]** Add `project_id` to `resource_locks` and make the active-lock
index unique per `(project_id, resource_key)` for `Path` and `SharedBoundary`;
`FiniteResource` stays global for the GPU and the model host.

**Why now rather than at the multi-project milestone — corrected.** Revision 3
argued this was not an additive migration and asked the Owner to rule on relaxing
the never-rebuild invariant `storage.py:424-431` declares. **A verification
review showed that argument was wrong**, and the test reproduces on this machine
(SQLite 3.45.1, `PRAGMA foreign_keys=ON` as `storage.py:593` sets):

```
ALTER TABLE … ADD COLUMN project_id TEXT NOT NULL DEFAULT 'legacy'              -> OK
ALTER TABLE … ADD COLUMN project_id TEXT NOT NULL DEFAULT 'legacy' REFERENCES … -> FAILED
    "Cannot add a REFERENCES column with non-NULL default value"
```

So a `NOT NULL` column with a default is legal and needs **no rebuild**. A
rebuild is forced only if `project_id` is declared a **foreign key** to
`projects`, which is the actual decision. The `DROP INDEX` half is genuinely
outside the docstring's enumerated set, though it copies and rewrites nothing,
which is the rationale that set exists to protect.

Revision 3 also argued the cost rises "behind the `_no_update`/`_no_delete`
triggers". **[FINDING]** `resource_locks` carries neither — `storage.py:1176-1183`
applies them to eight other tables — and `operational_state.py:1599` already
issues `UPDATE resource_locks`. The doing-it-now argument survives on the
smaller ground that both live databases hold real Foundry history (§4) and a
default-backfilled `legacy` project id is honest only while that history is
disposable.

**[OPEN]** Whether `project_id` is a foreign key to `projects`. FK gives
referential integrity and forces a rebuild; no FK is a pure `ADD COLUMN`. Two
real databases exist, so the backfill value matters either way.

**[PROPOSAL]** M0-D07 requires a snapshot immediately before every schema
migration. No snapshot machinery exists. A minimal snapshot-and-verify step
ships with 7.3 as its precondition; the full M0-D07 obligation is M8.

---

## 8. [PROPOSAL] The milestone round

**[OWNER] Atlas rule, restored to its true marking.** M0-D18 §8 is an Owner
statement, not a proposal:

> "It's important to remember that atlas has to be first class feature reporting
> all this because there will be no terminal window eventually"

Every milestone below names its Atlas surface or states explicitly that it has
no operator-visible state. Revision 1 stated this rule and then broke it in six
of eight milestones.

**M5 continues in parallel and is not superseded** (M0-D18 §8). **[FINDING]** M5
does not cover the `real?:` prop wiring, `systemState` derivation, the hardcoded
cost strip, or the desktop Performance tab; those are picked up at M13 rather
than assumed into M5.

---

### M6 — Establish the baseline: read the samples that exist, then take more

**The round's first milestone, because everything after it is unestimatable
until it returns numbers.** §4 corrects the premise: an executor *can* complete a
packet — once, by hand, with a correction. What is missing is a distribution and
a loop-driven run.

Three parts, smallest first:

1. **Reconcile the existing evidence.** Read
   `docs/registrations/foundry-read-only-discovery.md`, both runtime databases,
   and the CG-M4-19 and CG-M4-20 rows. State what actually happened, what was
   hand-driven, and whether the registration record overstates it (§4). Correct
   it if it does.
2. **Resolve CG-M4-20.** One `Failed` attempt and one `Running` attempt sit
   unresolved in `var/maestro.sqlite3`. Find out why it failed. That is one of
   the two samples in existence.
3. **Take more samples, loop-driven.** Run real packets through `run_cycle`
   rather than by hand, and record completion rate, granularity, corrections
   consumed, and failure modes.

**Why first.** M15's configurable review-round count, M16's
restart-before-model-switch threshold, M18's split path and §13's definition of
done are all parameters of a distribution with **two** observed samples, one of
each outcome.

**[FINDING] It cannot be fully loop-driven until §7.1 lands**, because
`run_cycle` today fabricates the reviews it would be measured on. Part 3 follows
the §7 corrections.

**Atlas:** none. This is a measurement, reported in the Done Record.

**[OPEN]** What "review standard" means before a real reviewer exists (M17).
**[PROPOSAL]** the project's own declared checks plus a human read — which is
what `owner-real-review-1` already was in the Foundry proof.

**[OPEN]** M0-D10 (Accepted) designates Foundry the proving project and mandates
register → dry run → *then* execute. M6 as written inverts that, and M12 holds
registration. See §15.

---

### M7 — The wiring/orphan gate, over Maestro only

M0-D18 §7.3. Commands with no non-test caller, tables with no production writer,
columns read by nobody, components mounted nowhere. Run as a gate.

Depends on nothing. It is the mechanical grader every later "is it real?" claim
is scored by.

**[PROPOSAL] Deferred and named as deferred:** M0-D18 §7.3's `[OWNER]` quote is
*"We need a check somewhere that the products maestro the product and you are
building actually get built"*, which D18's own following prose reads as covering
both Maestro and the products Maestro builds. An orphan check
over Maestro is a Python AST walk; over an arbitrary joined project in an
unnamed language it is a language-agnostic static analyser. That is its own
milestone and is not absorbed here.

**[OPEN]** What the gate does when a command has no caller *yet* because its
caller is the next packet.

**Atlas:** none; a CI gate.

---

### M8 — Backup and recovery (M0-D07)

`m0-d07-sqlite-backup-and-recovery.md` is **Accepted** and has zero code.
Nightly snapshots, snapshot before every schema migration, SHA-256 verification
manifests, retention, a monthly restore into a fresh database, durable
backup-health failure records.

**Why this early:** it is an accepted obligation the round was silently
ignoring, §7.3 already needs its migration-snapshot half, and the Development
Manager is about to be given ownership of `var/` (§11.1).

**Atlas:** D07 requires backup health shown live.

---

### M9 — Work-graph format specification, and the parser

M0-D18 §4 says the parser and generator are both unbuilt and both required. It
does not name the third thing: **there is no format specification** (§3), and it
is what both are written against.

Specify the format, then build the parser (format → `work_items` rows), tested
against a hand-written specimen. **[PROPOSAL]** Write the specimen as Maestro's
own real work graph for this round, so it is real data rather than a fixture
(M0-D18 §7.1).

Parser before generator: a parser makes "the Architect produced something"
falsifiable.

**[OPEN]** Whether the work graph lives in the joined project's repository or in
Maestro's store. `agent-workforce-control-plane.md:45` — *"There must never be
two independent writable truths for one fact"* — bears on this and the Owner
should rule.

**Atlas:** none.

---

### M10 — Identity and credentials

The service account, a GitHub App identity, and `secrets.py`'s first consumer.

**Why here and not last, as revision 1 had it.** The Architect writes the work
graph **into the joined project's repository** (M0-D18 §4), which under M0-D18
§9 means a branch, a commit and a pull request. M12 cannot run without an
identity to commit under. The cloud client at M11 needs credentials from the
same place.

**[OPEN]** The read API has no authentication (§3), and a service account is a
second principal on the same loopback port that grants Owner authority on an
unvalidated `actor` field. This must be ruled on before the service account
exists.

**Atlas:** none.

---

### M11 — Role-agnostic agent execution

**The dependency under the Architect, both reviewers, and the Owner's ruling
that scheduling uses cloud reasoning.** §3: `ExecutorAdapter` is git-typed end
to end and there is no cloud client, no HTTP dependency and no model router.

Scope: an agent invocation that is not packet-scoped — spawn a role, load its
`docs/agents/` contract, cap output, return a typed result that is not required
to be a commit. A cloud provider client. Model routing from role, risk and task
type to an execution class, making `execution_classes_json` a live field. The
Maestro-driven turn loop that §2.1 shows per-step measurement requires.

**[PROPOSAL]** This is the largest milestone in the round and should be split
further at packetization: the role-agnostic invocation, the cloud client, the
router, and the turn loop are four units.

**Atlas:** none directly; it makes M13's agent surfaces possible.

---

### M12 — The Architect produces the work graph

M0-D18 §4. Registration triggers an Architect review of the repository that
writes the work-graph file.

Scope: commit a `maestro.project.yaml` for both real projects (§3 — neither has
one, and registration raises without it); the Architect generator; a real
`source_hash` over project bytes; and `register-project` no longer accepting
hand-typed `work_items`. Registration owns consistent milestone naming — the
conversational form the Owner asked for, `M4.01`, `M4.01A`.

**This is one real agent role, end to end, on real data.**

**[PROPOSAL]** `discover-project --overlay` is documented as the Architect's own
answers, hand-written today. If the Architect is real, that file is its output,
not its input. That inversion belongs here.

**Atlas:** registration state and its refusal reasons (§10).

---

### M13 — Work-graph read API and Atlas wiring

**Nothing can be approved before it can be displayed.** §3: there is no
`work_items` or `graph_projections` endpoint, no `real?:` prop is ever passed,
`systemState` is never derived, and the active packet is a hardcoded constant.

Scope: graph read endpoints; `real=` wiring through the component tree so the
four already-built operator commands become reachable; `systemState` derived
from the read API so crash, disconnect and empty states can appear; an
active-work listing to replace the hardcoded constant; **the hardcoded cost
strip**; and **the desktop Performance tab**. The last two are here because
M5 does not cover them (§8 preamble) — stated in this milestone rather than
only in the preamble, so a reader of M13 sees all of M13.

**[FINDING] File-level collision to manage:** `MobileShell.tsx:10` declares four
hardcoded tabs and the app has no router, while M5 is concurrently renaming and
re-navigating those same tabs. Revision 1 asserted independence the file layout
does not permit.

---

### M14 — Notifications and escalation (M0-D04)

`m0-d04-notifications-and-escalation.md` is **Accepted**. §3: 2 of 8 events,
`escalation_at` written `None` and read by nobody, acknowledgement with no code,
no Slack.

**Why before the Owner gate:** M15 stops for Owner review. Without this, the
gate is a database state that nothing tells the Owner about — and M0-D18 §8 says
there will eventually be no terminal to discover it in.

---

### M15 — The Architect loop, to the Owner gate

M0-D18 §5 steps 1–4. Packetize all available milestones; bounded fidelity review
rounds; stop; present in Atlas; Owner approves in Atlas. Standards: **smallest
possible packets**, **no latent or unknown scope**.

**The configuration file ships here** (M0-D18 §11a), because the bounded round
count N is its first real value. Revision 1 put the file at M6, where it would
have had no reader — an orphan under M7's own gate.

**[FINDING] Latent scope revision 1 hid.** "Packetize" means authoring, per
packet, every `NOT NULL` column of `storage.py:834`: `packet_revision`,
`authority_reference`, `base_commit`, `expected_branch`, `role_contract_reference`,
`sop_reference`, `executor_class`, `integration_route`, `reviewer_route`,
`owned_paths_json`, `forbidden_paths_json`, `checks_json`, `resource_claims_json`,
`context_policy_json`. The Architect must choose lock keys, author checks the
target project can run, pick an execution class, and emit a context policy that
passes validation.

**[OPEN]** `base_commit` is `NOT NULL`, so packetizing every milestone up front
pins future packets to today's commit. Plan-time versus run-time is unruled.

**[OPEN]** What a milestone-level fidelity review record *is* — `reviews` is
packet-scoped.

**[OPEN]** The Architect's own repository (M0-D18 §5). §3: there is no `git
clone` anywhere. Provisioning and transport are undesigned.

**Atlas:** the Owner review gate, the Owner approval command, and the
blocked-waiting-on-Architect state.

---

### M16 — The Development Manager becomes a manager

M0-D18 §5.1, §5.2. Continuous scheduling using cloud reasoning; restart; context
allocation; model escalation; per-step instrumentation and history
summarisation (§2, on M11's turn loop). Makes the five decorative fields live.

**The commit half of the wrapper ships here**, with the coding agent it was
designed for — where it saves the packet's only `Initial` attempt (§5.1), a cost
that exists today.

**[FINDING]** Executor handles are in-memory (§3), so the Manager's own restart
orphans every attempt it was holding. Revision 1 scoped restart as restarting
the *worker* and never noticed.

**Atlas:** scheduling decisions, restarts, model escalations, context
allocations — all operator-visible.

---

### M17 — Real reviewers, and the correction dead end

M0-D18 §5 steps 5–7. Independent Reviewer; Integration Agent, which **wires the
part into the product** *and* **independently reviews that the parts align**.

**It must also fix what it switches on.** §3: a corrected packet can never be
accepted. The milestone that first produces a real `RequestChanges` is the
milestone that must fix `operational_state.py:2141`.

**It must also restore Owner acceptance.** §7.1's deletion leaves `accept_packet`
and `observe_merge` unowned. M15 builds an Owner gate for the *plan*; this
builds one for *acceptance*. Revision 1 left that gap open — the exact defect
M0-D18 exists to fix.

**The model-shaped check set ships here**, because this is the first moment a
bounded review round exists for it to protect, and per §5.2 its check list is
net-new design, not restoration. The reviewer-contract amendment lands with the
reviewer.

**[OPEN]** How actor independence is checkable once actors are real. Today
`operational_state.py:1916` is satisfied by a string literal.

---

### M18 — ReturnSlice

M0-D18 §6. Split at the raise path and the resolve path.

**[FINDING] The layer revision 1 missed:** there is no `UPDATE work_items`
anywhere. A split needs new work-item rows and the original moved to
`Superseded`/`NeedsReplan` — planning states unreachable by construction. The
"scheduled into a later milestone" half needs a `milestone_ref` for a milestone
that does not exist in the graph, with no rule for creating one.

Carries: fresh correction budgets on split packets (§6.1, amending the Bootstrap
Convergence Policy); the **Architect has the last word** on carry-forward (§6.2),
bounded by causing no further replanning; total blockage as a legitimate state.

**[OPEN]** Fresh budgets versus `correction_count CHECK(0,1)` (§3).

---

### M19 — Re-registration that supersedes

§10 of this record.

### M20 — Multi-project runtime

§11 of this record. The schema half already landed at §7.3.

---

## 9. [PROPOSAL] Explicitly deferred, and why

Named rather than dropped, which is what revision 1 did.

- **QA/Murphy** (`docs/agents/qa-agent.md`) and the **Decision Fidelity
  Reviewer** (`docs/agents/decision-fidelity-reviewer.md`) — two of M0-D18 §2's
  six string-literal roles. Both deferred past this round. Worth the Owner's
  attention: the Decision Fidelity Reviewer is the role that would have caught
  revision 1's provenance failure automatically, and QA/Murphy is the role that
  independently tries to break a delivered feature — the missing check in a
  round whose premise is that schema and tests are not delivery.
- **Language-agnostic orphan checking** over joined projects (M7).
- **An Atlas host.** `apps/atlas/package.json` has no host: `vite`, `vite build`,
  `tsc`, `eslint`, `vitest`. The read API serves JSON only. Today the only way
  to see Atlas is `npm run dev` in a terminal, which is what M0-D18 §8 says must
  eventually not exist. M0-D18 §11's packaging layout is unbuilt.
- **The plain-language start-up runbook** the Owner asked for repeatedly — *"I
  don't want to see the code I want to see a list if steps to start maestro"* —
  and the start-up commands already authorized into M5 — **[OWNER]** *"Yes
  build those and I would like that process added to m5 as well"*. **[PROPOSAL]** the
  runbook follows M12, the first point at which the start path is stable.
- **The audit report** should be committed rather than left an external link
  (M0-D18 §2).
- **[OWNER] The Architect as answerer.** M0-D18 §3: *"Should any other role get
  stuck or have questions, the architect assumes responsibilities for the
  answer."* M18 covers the out-of-scope-discovery half of that sentence; the
  stuck-or-has-questions escalation channel is **deferred past this round and
  named here rather than dropped**. Revision 1 dropped it silently and revision
  2 repeated the drop until a fidelity review caught it. **[PROPOSAL]** it wants
  the same transport as the Architect's own repository (§8, M15), so it should
  follow whatever answers that.

---

## 10. Loose end 1 — re-registration that supersedes

**[OWNER — session]** The Owner named this in the session's opening instruction:

> "re-registration that supersedes without reopening completed work"

**[OWNER — session] Ruled 2026-09-09**, when asked whether an in-flight packet whose work
item changed is returned to the Architect or finishes against the superseded
revision:

> "Simple, registration cannot take place when there is active work in progress
> and having the the var folder is fine for db, and installation"

The second clause is a separate ruling, recorded at §11.1.

**The ruling.** The question does not arise. Re-registration is **refused** while
the project has active work. Drain first, then re-register.

**[PROPOSAL] What counts as active**, against `storage.py:826`: refused when any
run is `Running`, `Blocked`, `AwaitingArchitect` or `AwaitingOwner`; permitted
when every run is `Complete`, `Cancelled`, or `Planned` — the last because
`register-project` itself leaves a run `Planned`, so a project that registered
and never started can always be re-registered.

**[PROPOSAL]** The refusal names *which* runs and packets hold it, so the
operator has a list to act on rather than a verdict to investigate.

**[PROPOSAL] What M19 must build:**

1. A real `source_hash` over project bytes — delivered at M12, which is what
   reads them.
2. Supersession writes for **both** `project_bindings` **and**
   `graph_projections`. §3: neither has an `UPDATE` anywhere, and
   `one_active_graph_per_project` means the old projection must leave `Active`
   or the insert fails. Revision 1 named only the binding.
3. A reconciling re-projection: merged and completed items **stay closed**; only
   new, changed and unstarted become actionable.
4. `Stale` and `NeedsReplan` become reachable.

**[OPEN]** Whether the diff keys on `architecture_node_id` or on content, which
decides whether a renamed item reads as changed or as deleted-plus-new.

**Atlas:** the blocked-registration state and the work holding it.

---

## 11. Loose end 2 — multi-project support

**[OWNER — session]** The Owner named this in the session's opening instruction:

> "multi-project support (locks scoped per project, one loop for all projects,
> service account)"

**Locks scope per project** — §7.3, pulled forward for migration-cost reasons.

**One loop for all projects.** **[PROPOSAL]** The reason is arbitration: the GPU,
the model host and cloud reasoning budget are shared across every project. Two
loops would each schedule against a resource neither owns, and the
`FiniteResource` locks would become the only arbiter — resolving contention by
collision instead of judgment. M16's scheduling therefore ranks eligible packets
**across** projects; whether projects carry relative priority is a configuration
value.

**The service account** — delivered at M10, not last, because M12 needs an
identity to commit into the joined project's repository.

### 11.1 [OWNER — session] `var/` is the right home, and the service account owns it

The Owner's message of 2026-09-09 answered two open items in one sentence. Its
first clause is the re-registration ruling at §10. Its second:

> "Simple, registration cannot take place when there is active work in progress
> **and having the the var folder is fine for db, and installation**"

**The ruling.** `var/` is the right home for the database and the installation.
The service account is given ownership of `var/` rather than the runtime being
relocated to suit it.

**Recorded honestly:** revision 1 overreached this, extending "a var folder is
fine" into a blessing of `config.py`'s `validate_runtime_dir` — which enforces
something narrower and different, that the runtime live inside the *Maestro
repository*, the constraint M0-D18 §11 records the Owner calling
*"unpractical"*. Revision 2 then deleted the whole section rather than trimming
it, and lost the ruling with the overreach. This subsection restores what the
Owner actually said and claims nothing further.

**[OPEN]** The repo-relative half of `validate_runtime_dir` is untouched by this
ruling and remains unruled. M0-D18 §11 places the runtime directory out of
scope; M0-D18 §11's packaging layout puts `var/` beneath
`/usr/local/lib/maestro/<version>/`, which `validate_runtime_dir` as written
would reject. Whoever builds M10 will hit that and needs an answer.

---

## 12. [PROPOSAL] Coverage of M0-D18 §2

Every audit finding is scheduled or explicitly deferred. Revision 1 left nine
unmapped while claiming the plan was built on the audit.

| Finding | Where |
|---|---|
| Loop approves and merges its own work | §7.1; permanently M17 |
| **Maestro has never built anything** | **M6** |
| Project Architect a literal | M12, M15 |
| Integration Agent a literal | M17 |
| Independent Reviewer a literal | M17 |
| QA/Murphy a literal | §9, deferred and named |
| Coordinator/scheduler a literal | M16 |
| Decision Fidelity Reviewer a literal | §9, deferred and named |
| `docs/agents/` never opened | M11 |
| Nothing reads the work graph | M9 (format + parser), M12 (generator) |
| Five decorative fields | M16 |
| Re-projection impossible; fake `source_hash` | M12, M19 |
| Atlas: 3 of 4 mobile tabs fixtures | M5 |
| Atlas: `systemState` never derived | M13 |
| Atlas: desktop placeholders | M5 (Agents/History), M13 (Performance) |
| Atlas: four operator commands unreachable | M13 |
| Atlas: hardcoded cost strip | M13 |
| Backup/recovery zero code | M8 |
| Context/token/cost stack | M11 (turn loop), M16 (instrumentation) |
| Escalation never fires | M14 |
| Acknowledgement unreachable | M14 |
| Notification triggers 2 of 8 | M14 |
| GitHub integration dead | M10 |
| Secrets have no consumer | M10 |
| Stopped worker not reported | M16 |

---

## 13. [PROPOSAL] Definition of done

M0-D18 §3: *"Clearly the product has to function."*

- No milestone is complete on schema plus tests. A **real caller in a real path**
  must exist; M7's gate is the mechanical check for every milestone after it.
  M7 itself is exempt by construction — it builds the gate — so M7's own
  evidence is the gate's output over the milestones already delivered.
- No milestone is complete while its operator-visible states are terminal-only.
- Evidence is a rerunnable command plus output, reported `PASS` / `N/A` /
  `UNTESTED`. Where something cannot be tested against real data it is reported
  `UNTESTED` with residual risk — never substituted with a fixture (M0-D18 §7.1).
- M0-D18 §9's discipline applies to this round's own development: branch, pull
  request, independent review never by the author, Done Record as a merge
  precondition. That includes §7's corrections.
- **[PROPOSAL] New, and absent from revision 1:** M0-D18 §7.2 records the Owner's
  verdict on the test/product balance — *"Way to much effort is aligned at
  writing tests verse spent on writing the product"* and *"But it was all
  useless"* — 11,299 product lines against 18,602 test lines. A milestone that
  ends with more new test code than new product code is a signal to stop and
  report, not a milestone that passes.
- **[PROPOSAL]** M0-D18 §2's headline finding is not retired until **Maestro's own
  loop has authored a packet**. No milestone in M6–M20 asserts that by
  existing; M6 measures whether it is possible, and it should be re-tested at the
  end of the round.

---

## 15. [PROPOSAL] The coverage gap this record has not closed

A record-consistency review found that this record was verified thoroughly
against **the code** and against **M0-D18**, and was never checked against the
other seventeen decision records. It names three — M0-D18, M0-D07, M0-D04 — in
over 800 lines. The defect is not in what it verified; it is in what it never
opened. Scheduling this round without closing the gap would repeat M0-D18 §1's
own origin: acting on a partial reading of the record.

**Accepted records with live obligations this round does not carry:**

- **M0-D13** (Accepted 2026-08-31) requires synthetic control-loop qualification
  **before any live Foundry execution** — which M6 is. It appears nowhere in
  this record. **[OPEN]** and structurally deadlocked: D13's qualification is
  fixture-only by design, which M0-D18 §7.1's fake-data ban makes unsatisfiable.
  It needs explicit retirement, not silence. `architecture-agent.md:41-54`
  restates it as controlling text the Architect must read, so M12's Architect
  will load it.
- **M0-D10** (Accepted) designates Foundry the proving project and mandates
  register → dry run → execute. M6 inverts that order and M12 holds
  registration. The acceptance record already in the database cites
  `'M0-D10#step-5'`, so the sequence was partly executed (§4).
- **M0-D12** (Accepted) makes an eight-element bounded quality contract required
  per packet, and `independent-review-agent.md:51-58` makes its absence **block
  the review**. There is no column for it (`grep -rn "quality_contract"
  services/` → nothing). As scheduled, M15 would produce packets M17's reviewer
  must refuse.
- **M0-D05** (Accepted) is the record that actually states *"escalate
  immediately. Do not loop further corrections."* M0-D18 §6.1 amends the
  Bootstrap Convergence Policy; **M0-D05 is untouched and uncited by both**.
- **M0-D17** (Accepted) sets *"a minimum of one real review before acceptance or
  merge… a **hard floor, not a tunable**."* M15 ships the configuration file
  M0-D18 §11a mandates and nothing records the exemption.
- **M0-D02** (Accepted) specifies `maestro project create`, a binding PR into the
  project repository, and a dry run gating registration. None exists; M12 covers
  none of the three.
- **M0-D14** (Accepted) requires dispatch **rejection** on insufficient packet
  context. That is a different obligation from §5.3's per-step budget, and §2's
  "out of scope" ruling reads as retiring it. It does not. Either D14 needs
  amending or the gate is unscheduled.
- **M0-D03** (Accepted) requires that a stale or revoked credential *"blocks
  affected work visibly"*, and that backups never contain unencrypted secrets —
  a constraint on M8 that M8 does not carry.
- **M0-D08 / M0-D09** (both Accepted, both zero code) are the two most plausibly
  out-of-round, which is exactly why §9 should have said so and did not.

**Two documents that contradict this record and sit on master:**

- `docs/registrations/architect-registration-readiness-one-sheet.md:9,24,49-50`
  states that *the architect hands Maestro* an approved work graph — the exact
  inversion of M0-D18 §4 — and names two commands that do not exist.
- `bootstrap-convergence-policy.md:22-26` still states the rule M0-D18 §6.1
  amended, and `:7` gives it precedence over conflicting instructions. Five role
  contracts restate it, including `architecture-agent.md:167` — the contract of
  the role M0-D18 empowers to split packets.

**[PROPOSAL] Before M11 loads role contracts**, the contracts must be amended:
`docs/agents/` was last touched 2026-09-03, five days before M0-D18, and no file
there knows either record exists. `maestro-development-manager.md:16` still
offers cloud reasoning as optional; `:68` still forbids resetting correction
counts. The first time code opens these files it makes stale text executable,
which is worse than the string literals it replaces. This record schedules one
contract amendment across fifteen milestones.

**[PROPOSAL] The free corrections that should happen first**, because they are
the read-path that produced M0-D18 and they are untouched:
`README.md:7`, `maestro-master-plan.md:5`, `maestro-development-status.md`
(recorded at a commit 233 behind HEAD, and asserting M1's lifecycle is closed
with "every state having a real way in and a real way out"), `ai/handoffs/current.md`
(which tells the reader to read the status doc *before taking any Maestro
action*), and `m4-packet-breakdown.md`, which records the fabricated reviews as
delivered features. §7.2 names two of these five.

---

## 14. Open items

**Requiring an Owner ruling:**

- **§8 as a whole** — the milestone set and its order.
- **§5.1** — one factual error in Owner-approved M0-D18. (§5.2 alleged a second
  and was itself wrong; withdrawn.)
- **§7.3** — whether `resource_locks.project_id` is declared as a foreign key.
  That, not the never-rebuild invariant, is the real question (§7.3).
- **§10 (M10)** — read-API authentication, before a service account shares
  loopback with an unauthenticated Owner-authority POST.
- **§9 (M9)** — whether the work graph lives in the project repository or
  Maestro's store, against the single-writable-truth rule.

**Carried, not blocking:** M15's `base_commit` plan-time/run-time question; what
a milestone-level review record is; the Architect repository's transport; the
M18 budget-versus-`CHECK(0,1)` conflict; M19's diff key; M6's "review standard";
M7's not-yet-called verdict.

M0-D18 §5.3 is closed by §2. **[PROPOSAL]** M0-D18's own status header still
reads *"One **[OPEN]** item remains on the decision list: §5.3"* and now
misstates the record for anyone who reads M0-D18 alone — which its own status
line invites, since it calls itself the governing authority. This record does
not amend M0-D18, so the header is flagged rather than edited; it should be
corrected when the Owner rules on §5.1 and §5.2.

**The round cannot start before §8 is ruled on.**
