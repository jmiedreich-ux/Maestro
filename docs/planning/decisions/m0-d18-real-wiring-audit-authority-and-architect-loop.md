# M0-D18 — Wiring Audit Findings, Architect Loop, and Execution Authority

**Status:** **Owner-approved 2026-09-08.** All rulings in this record are
authority. The two configuration boundaries in §11a were approved with it. Any
item still marked [PROPOSAL] is a recommendation the milestones may settle, not
a constraint. One **[OPEN]** item remains on the decision list: §5.3, per-step reasoning
budget enforcement.
**Type:** Superseding authority and design amendment.

**Provenance rule for this record.** This document is the authority the next
round of milestone planning is built from, so every statement is marked with
where it came from:

- **[OWNER]** — the Owner said this. Quoted verbatim.
- **[PROPOSAL]** — the assistant's inference or recommendation. Not authority
  until the Owner rules on it.
- **[OPEN]** — genuinely unresolved. Must be answered before the affected
  planning proceeds.

An earlier draft of this record blurred these three, presenting proposals and
questions as Owner rulings. A conversation fidelity review caught it. The
separation below exists because that failure is the same failure the record
itself documents.

**Amends:** the
[Maestro Development Manager role contract](../../agents/maestro-development-manager.md)
(§5) and the [Bootstrap Convergence Policy](../bootstrap-convergence-policy.md)
(§6.1). [M0-D04](m0-d04-notifications-and-escalation.md) and
[M0-D15](m0-d15-real-m1-m4-implementation-path.md) appear here only as
**findings** in §2 — no amendment to either is written yet.
[M0-D16](m0-d16-real-m5-atlas-navigation-and-visibility.md) and M5 are
**unaffected and remain in force** (see §8).

---

## 1. Why this exists

On 2026-09-08 the Owner asked how to start Maestro. The answers kept exposing
designed capabilities with no code behind them. The Owner's own framing:

> "this all was in the design I thought, I'm finding lots of parts of the
> product are not connected"

and, on an earlier occasion in the same session:

> "we havew deisgn plans for this already, why are they not surfacing here"

Four independent audits were then run against the real codebase.

**[OWNER] Standing instruction implied by both quotes:** mine the existing
design records before designing anything new. The design mostly exists; what is
missing is code and connection.

---

## 2. The audit finding

Full report: <https://claude.ai/code/artifact/08bb795b-0bfa-43e7-a4be-a3e6142c3087>
**[PROPOSAL]** This report should be committed into the repository rather than
left as an external link, since it is a durable planning input.

**The pattern.** The durable-state layer — tables, validated commands,
idempotency, optimistic versioning, append-only events, immutability triggers —
is built and heavily tested nearly everywhere. The **actor** that would call
those commands in production is missing nearly everywhere. Grouped by
capability: roughly 6 built, 9 partial, 23 not built, 7 built-but-orphaned.
(Groupings are the auditors'; the boundaries between categories are judgement
calls, not a precise inventory.)

A green test suite over a store command reads as "the capability ships." It
does not. It means the command is correct *when something calls it*, and in
most cases nothing does.

**Specific findings, all verified against code:**

- **The development-manager loop approves its own work and merges it.** It
  records `Approve` from a readiness boolean, satisfies the store's
  independence check with the literal string
  `"development-manager-loop-independent"`, then grants itself
  `required_authority="Owner"` and performs a real `git merge`. Its own role
  contract forbids exactly this. The durable record afterwards asserts a
  review, an Owner acceptance and a merge; only the merge happened.
- **[OWNER] Maestro has never built anything.** The Owner's correction when the
  assistant called this "self-approval": *"Yes but the so called loop didn't
  develop this"*. Every line of M4 was written by the assistant, not produced
  by Maestro's own loop. Maestro has not authored a feature. Any claim about
  what the loop "does" must be read against that.
- **Six of nine designed roles exist only as string literals** — Project
  Architect, Integration Agent, Independent Reviewer, QA/Murphy,
  Coordinator/scheduler, Decision Fidelity Reviewer. One subprocess spawn
  exists in the entire repository: the `qwen` worker.
- **`docs/agents/` holds seven role contracts and five specialist overlays that
  no code has ever opened.** `role_contract_reference` is a filename pasted
  into a prompt line; its contents are never loaded.
- **Nothing reads the work graph.** `authority.work_graph_path` is validated as
  a string and hashed as an opaque blob. No parser, no format, no example file.
  Work items reach the database only by being typed into registration JSON. See
  §4 — the Owner rejected this as the intended design.
- **Five fields are decorative.** `planned_rank`, `dependencies_json`,
  `change_domains_json`, `execution_classes_json` and `priority` are validated
  on write and read by nobody. Declared dependencies block nothing.
- **Re-projection is impossible by construction.** Graph rows are insert-only
  and `source_hash` derives from operator input rather than project bytes, so
  `Stale` and `NeedsReplan` on a graph are unreachable states.
- **Atlas: three of four mobile tabs are fixtures.** `systemState` is never
  derived from anything real, so crash, disconnect and empty states cannot
  appear — with the read API down, the app still renders confident fixture
  data. Desktop Performance/Agents/History render literal placeholder text.
  All four operator commands are unreachable from the UI. The cost strip is a
  hardcoded `61% / 14% / 5% / 80%`.
- **Operations:** backup/recovery is zero code; the context/token/cost stack is
  schema-only and never called; escalation never fires (`escalation_at` is
  written `NULL` and read by nobody); acknowledgement is an unreachable state;
  notification triggers cover 2 of 8 required events; the GitHub API
  integration is dead code; secrets have no consumer.
- **A stopped or killed worker is not reported.** Raised by the Owner during a
  real incident: *"How would this be reported and I assume maestro would resume
  it?"* and *"Did you ask it why it stopped?"*. `record_worker_progress` and
  its `blocker_payload_json` exist with zero callers, and the orchestrator only
  polls OS process liveness. Resolved in §5.2 — the Development Manager owns
  restart.

---

## 3. Governing authority — restated, not amended

These are prior Owner rulings that this record operates inside. They are
restated because the earlier draft granted new Architect authority without
citing the constitution it was working within.

**[OWNER] The authority split:**

> "The rule is 90% Maestro process 10% me, that should be the governing
> authority split"

**[OWNER] The three-tier refinement:**

> "changes what the project means, yes, redefining what a role is allowed to
> accept, yes, deciding the ruling-loop's own authority boundary, yes. However,
> adding new milestones or durability should fall into the project architect
> responsibility, that role is the closest to the owner. Should any other role
> get stuck or have questions, the architect assumes responsibilities for the
> answer. Sometimes sudden out of scope work will be discovered, it's the
> architect agents role to understand where this new scope fits into the
> process."

**[OWNER] What Owner acceptance requires:**

> "Owner acceptance can be granted when the definition of done is met or any
> limitations are deemed ok because the product or feature meets basic needs
> and the limitations can be tracked on the back log"

**[OWNER] Resolved 2026-09-08.** Asked how this squares with §7.4's stricter
completion bar:

> "Clearly the product has to function"

**The ruling:** functioning is the floor. A capability is not complete because
its schema exists and its tests pass — a real caller must exist in a real path.
Known limitations may still be accepted on top of a functioning product, when
they are judged acceptable and tracked on a real backlog. What may never be
accepted is a non-functioning capability reported as delivered.

**[OWNER] Bias when a rule threatens delivery:**

> "always lean towards giving the product the best chance to get built"

and

> "Ever packet will not come out 100% perfect"

---

## 4. Ruling — registration triggers an Architect review of the repository

**[OWNER]** When told work items are hand-written, the Owner rejected it as the
design:

> "I don't think that is true"

> "Thst the file would be written by hand" *(rejecting the premise that the
> work-graph file is authored by hand)*

> "So then why are you communicating it like we don't have process or something
> built for it?"

> "Ok I'm already stuck on the first command, doesn't the registration process
> supposed to do a review of the repo to build its file. I believe the SOP
> currently states the Maestro's architect does this, would this cli tell the
> agent to do they and we would need to give the repo address?"

**The ruling:** registration is supposed to trigger an **Architect review of
the repository** that produces the work-graph file. The Architect writes it —
the same way it fills the discovery overlay — not a human authoring YAML. The
work-graph parser and generator are both unbuilt; both are required.

**[OWNER] Registration also owns naming:**

> "The registrion process should make the milestone naming consistent."

**[OWNER] Conversational packet naming:**

> "When communicating I just need to know M4.01 or M4.01A etc"

---

## 5. The Architect loop

**[OWNER] The Architect has its own loop and its own repository:**

> "And possibly escalation to the project architect which lives in it's own
> repo"

> "The review process by architect should have its own loop because there will
> be fidelity reviews of the milestones and packets."

The Architect's context lives in **its own repository**, separate from Maestro
and from any project it plans. (Its current working files —
`architect/handoff.md`, `architect/memory.md` — are the practice today, not the
intended home.) Escalation to it is a real handoff of facts, not a function
call.

**[OWNER] The loop, in the Owner's own words:**

> "I presume that this phase will packetize all available milestones in the
> review? Then once it's done developing the packets it stops for owner review
> which should be in atlas. Once approved by owner, the architect then assigns
> and reviews the work that can happen in parallel, at the end, the integration
> agent does and independent review to make sure the parts align properly. This
> will be a configurable x amount of review times here but should not be so
> strict it never proceeds further. Once approved, it's handed off to the
> developer manager"

Broken out:

1. Packetize all available milestones.
2. Fidelity reviews over those milestones and packets, iterating a
   **configurable number of rounds**, bounded — *"should not be so strict it
   never proceeds further."*
3. **Stop for Owner review, presented in Atlas.**
4. Owner approves.
5. The Architect assigns work that can run in parallel, and reviews it.
6. At the end, the **Integration Agent performs an independent review that the
   parts align properly.**
7. Handoff to the Development Manager.

**[OWNER] Packetization standard the fidelity reviews enforce:**

> "packetize M4 and then have an independent architecture fidelity review done
> to make sure the packets are the smallest they can be and to ensure there is
> no sudden scope issues or things that will be unknown"

Two standards: **smallest possible packets**, and **no latent or unknown
scope**.

### 5.1 [OWNER] Who assigns work — RESOLVED 2026-09-08

> "we agreed at the end the development manager would be in charge of
> continuous scheduling"

**The ruling:** the Architect decides **suitability** at plan time — rank,
dependencies, specialist role, execution class. The Development Manager is in
charge of **continuous scheduling**: a small, reusable process that
re-evaluates every cycle and decides which eligible packet runs next, on which
worker, given current locks, leases, worker health and WIP. This makes the five
decorative fields of §2 live inputs.

The Owner's two earlier statements below are superseded by this ruling and kept
for provenance.

- **[OWNER]** *"I can see step 3 being the project architect doing the packet
  assignments and deciding which packet run in parallel. However, there is no
  step 4, step 4 is the development manager picking up the milestone and work
  packets, then delegate out to the assigned agent"*
- **[OWNER]** *"Once approved by owner, the architect then assigns and reviews
  the work that can happen in parallel"*
- **[OWNER]**, asking rather than ruling: *"So would you prefer the dev manager
  do a small scheduling process before delegating, maybe something that is
  reusable and continually evaluates assignments?"*

Rationale for the split: assignments go stale as locks free and packets return,
and the Manager already holds every input a scheduler needs. Its role contract
already says *"Select the highest-ranked eligible item, not simply the oldest
queue entry."*

**[PROPOSAL]** Scheduling runs every cycle: many turns, little judgment per
turn. "Cloud reasoning" should therefore name a *fast* model here, not a
careful one — the distinction that the account cited in §5.3 turned on. Which
model serves scheduling belongs in the §11a configuration file, not in code.

**[OWNER] Resolved 2026-09-08:**

> "The manager should use cloud reasoning for scheduling"

Scheduling is a reasoning task, not a sort. This settles the role contract's
open *"may use cloud reasoning"* permission: scheduling is the named case.

### 5.2 [OWNER] The Development Manager owns worker context and restart

> "the dev manager restarts and is also in charge of how much context the agent
> gets and it will keep restarting or use another model if it happens to much"

Three responsibilities, all the Development Manager's:

1. **Restart.** A stopped, killed or silent worker is restarted by the Manager.
   Restart is automatic and needs no Owner or Architect involvement.
2. **Context allocation.** The Manager decides how much context each agent
   gets. This makes M0-D14's context stack — `attempt_context_usage`, context
   preflight, the policy thresholds — a live input with a named owner, rather
   than the schema-only tables §2 found.
3. **Model escalation.** Repeated restarts are a signal, not just a retry
   count. Past a threshold the Manager switches the packet to **another
   model**. This makes model routing (control-plane §11,
   `execution_classes_json`) a runtime decision the Manager makes, not only a
   plan-time label the Architect sets.

**[PROPOSAL]** The restart threshold that triggers a model switch, and whether
a switch consumes any part of the packet's correction budget, are not yet set.
Per §6.1 the bias is to let the work proceed.

### 5.3 [OPEN] Per-step reasoning budget enforcement

**Added to the decision list 2026-09-08 at the Owner's direction**, prompted by
a published account of an agent pipeline that failed exactly this way: a
careful model was given a seventeen-step loop, spent its full reasoning budget
on early steps, and hit the run timeout having published nothing. The author's
own diagnosis was that the reasoning budget was not capped *per step*, the
whole history was re-sent every turn, and the only timeout was the one that
eventually killed the run rather than one that showed where it got stuck.

Maestro is exposed to the same shape. `context_policy_json` declares real
thresholds — `minimum_context_tokens`, `output_reserve_tokens`, and the
warning, checkpoint and stop remaining-token boundaries — and
`validate_context_policy` enforces that they are ordered correctly. **Nothing
enforces them at run time.** There is no context preflight before dispatch, no
per-step cap, and no checkpoint at the pressure boundary; `attempt_context_
usage` is written by no production path (§2). A packet can therefore burn its
whole budget on one step, and the first signal is an expired lease.

Maestro is better off than the article's author in one respect: per-attempt
leases and heartbeats already localise a stall to an attempt rather than a
whole run. What is missing is the step-level view inside an attempt.

**To be decided:** whether the reasoning budget is capped per step; whether
dispatch is refused at preflight when the context does not fit; what happens at
the checkpoint boundary — a forced worker checkpoint, a model switch under
§5.2, or a return to the Architect; and whether history is re-sent whole or
summarised between steps.

**[PROPOSAL]** This interacts with §5.2's model escalation and §11a's
configurability: the caps belong in the config file, and exhausting a budget is
plausibly the same signal as a repeated restart. The related observation on
§5.1 — that scheduling is a high-turn, low-judgment-per-turn task and so wants
a *fast* reasoning model rather than a careful one — is recorded there.

### 5.4 [OWNER] The script commits the worker's work before review

> "One thing thst routinely happens is the qwen routinely forgets to commit, we
> should not hold that against the model, when it finishes the script should
> check first and do the commit before it gets into the review, that will save
> time"

**The ruling:** committing is deterministic work with a right answer, so it
belongs in the script, not in the model's instructions. When a worker finishes,
the harness checks for uncommitted work and commits it before the packet enters
review. A model forgetting to commit is not a failure of the work.

**Why this matters more than the time saved.** Today a worker that produced
good code but no commit is recorded as a **failed attempt**:
`retrieve_evidence` compares HEAD against the base commit, finds no new commit,
returns `commit_sha=None`, and `finish_attempt_execution` records `Failed`. The
work is intact in the working tree and is thrown away, consuming one of the
packet's two attempts. Separately, an uncommitted tree would fail review
readiness anyway on its dirty-worktree blocker. Committing first fixes both.

This is the same principle as §5.3's counterpart observation — *"everything
with a right answer moved into a script"* — which Maestro already applies to
validation through `review_readiness.py`, and which now extends to the commit
itself.

**[OWNER] Scope resolved 2026-09-08 — commit the whole worktree.** Committing
only owned paths would leave the rest uncommitted, and review readiness would
then fail with its dirty-worktree blocker: *"worktree is dirty"*, which says
nothing useful. Committing everything lets the existing path check produce the
precise finding instead — *"changed path is outside allowed_paths: <file>"* —
and the same applies to anything landing in `forbidden_paths_json`. Genuine
build debris is a `.gitignore` concern, not Maestro's. Commit all; let the
existing checks judge.

### 5.4.1 [OWNER] The wrapper principle

> "those little tricks is what I was trying to explain when I said a script
> wrapper is around the packet agent delegation"

The commit fix is one instance of a general rule, and it is the rule that
matters rather than the instance: **a deterministic script wraps the packet's
agent delegation and absorbs the model's routine misses before they become
recorded failures.** Anything with a right answer that a model reliably forgets
belongs in that wrapper — committing finished work, creating the branch if the
worker did not, capping captured output, clearing debris — and never in the
model's instructions, where it is one more thing to forget.

This is the same separation §5.3 noted from outside: everything with a right
answer moves into a script, and the model is left only the judgment. Maestro
already applies it to validation through `review_readiness.py`; §5.4 extends it
to the commit; the principle extends it to whatever comes next.

**How to apply:** when a model's routine behaviour repeatedly costs an attempt,
the first question is whether the harness can simply do it, not how to word the
prompt better. Do not hold a deterministic omission against the model.

---

## 6. Mis-scoped packets — the ReturnSlice path

**[OWNER] The scenario, in the Owner's own words:**

> "a packet will fail because something is not scooped correctly and the packet
> needs to be split up smaller or part of it can continue and the other part
> might need to be slotted into a layer milestone. Now, I assume the agent
> doing the review would fail it or maybe the actual coding agent says it's a
> problem, I assume they would hand this beck to the development manager who
> would then subsequently hand the information back to the architect loop, in
> the meantime some if not all work could be blocked because of the dependency
> chains. Back in the architect loop, the architect breaks the packet into two
> … review signs off or it could do a few reviews, ultimately signs off. The
> development manager now gets two packets back one that is eligible for
> scheduling in this milestone and a new second one that is scheduled for a
> later milestone. Now the coder starts working on the new packet and when it's
> done and passes its review, it then heads over to the integrate agents queue
> where that agent wires the new packet into the product and a review is done
> then it goes to the dev manager to commit the feature and update the
> dependency chain so other work packets can be released by the development
> manager."

Note both Integration Agent functions the Owner named across the two
statements: it **wires the part into the product** *and* it performs an
**independent review that the parts align**. Both are required.

Note also: *"some if not all work could be blocked"* — total blockage is a
legitimate state, not only partial.

**Existing vocabulary this maps onto** (built, unwired): `ReturnSlice` as a
finding disposition — and the store already refuses to dispatch a correction
for a packet carrying one; `Assemble` as a review result; `NeedsReplan` as both
a packet state and a review result; `blocker_payload_json` on worker progress
for the coding agent raising the problem itself.

### 6.1 Correction budget on split packets

**[OWNER]** on the assistant's raising this as a conflict:

> "The split packets' correction budget, I think you're making this out to be
> to complex, always lean towards giving the product the best chance to get
> built."

**[OWNER] Confirmed 2026-09-08**, when asked whether the specific amendment
followed from the principle:

> "my answer still stands, don't be inflexible"

**The ruling:** a packet produced by an Architect split is new scope and starts
with a **fresh** review/correction budget. This **amends the Bootstrap
Convergence Policy**, which currently requires counts never reset across packet
replacement. Do not apply the old rule inflexibly to work the Architect has
deliberately re-scoped.

**[OWNER] standing instruction, beyond this case:** do not make these questions
more complex than they need to be.

### 6.2 What carries forward from completed work

**[OWNER]**

> "I'm leaning towards if something needs to go back to planning we should
> start over on the packet. I'm also ok if the architect agent makes the call
> during that review"

Recorded as stated: a **leaning**, not yet a fixed default, plus an explicit
willingness to let the Architect make the call during its review.

**[OWNER] Resolved 2026-09-08:**

> "as we said, the project architect has the last word on this, as long as it
> doesn't cause more replanning issues"

**The ruling:** starting the packet over is the default, and the **Project
Architect has the last word** on whether anything carries forward — bounded by
one condition: the decision must not cause further replanning. Preserving work
that then has to be unpicked is the failure this bound exists to prevent.

---

## 7. Evidence, completion, and testing

**7.1 [OWNER] Fake data is banned.**

> "I don't want fake data for any tests going forward"

> "Fake data is banned"

**[PROPOSAL]** Scope of the ban, for confirmation: invented work-item ids,
fixture manifests, stand-in worker scripts, and fixture-driven frontend tests.
Where something genuinely cannot be tested with real data, report it
**UNTESTED** with residual risk rather than substituting a fixture.

(The Owner subsequently closed discussion of this topic — *"I don't want to
discuss the fake data thing"* — so the rationale is not restated here.)

**7.2 [OWNER] The test/product balance is wrong, and the effort was wasted.**

> "Way to much effort is aligned at writing tests verse spent on writing the
> product"

> "But it was all useless"

Measured: 11,299 lines of backend product against 18,602 lines of backend
tests. **[PROPOSAL]** the more precise defect is *what* was tested — store
commands in isolation, the least uncertain part — while the uncertain parts had
no coverage. The Owner's verdict on the effort stands as recorded.

**7.3 [OWNER] A check that the product actually gets built.**

> "We need a check somewhere that the products maestro the product and you are
> building actually get built"

Note the scope: **both** Maestro itself **and** the products Maestro builds for
others. **[PROPOSAL]** implement as a mechanical orphan check — commands with
no non-test caller, tables with no production writer, columns read by nobody,
components mounted nowhere — run as a gate. Most audit findings are detectable
this way.

**7.4 [OWNER] M2 and M4 are closed.**

> "M2 and M4 are closed"

**[PROPOSAL]** They stay closed — their packets were delivered — but closure
asserts delivered packets only, not a working product. Before reporting any
future capability complete, verify a real caller exists in a real path, per the
Owner's ruling in §3: *"Clearly the product has to function."*

---

## 8. Atlas is first class

**[OWNER]**

> "It's important to remember that atlas has to be first class feature
> reporting all this because there will be no terminal window eventually"

Every transition in §5 and §6 requires a first-class Atlas surface, including
the Owner review gate at §5.3 and the blocked-waiting-on-Architect state.

**[PROPOSAL]** Fixture-rendered surfaces are a defect, not a placeholder: a
screen that cannot tell the viewer it has no backend is worse than one that is
visibly empty.

**[OWNER] M5 remains in force and is not superseded by this record.** Its scope
is already Owner-approved and explicitly non-blocking:

> "An example is, M5, those screens and features where approved, so work should
> not stop, they need to be slotted in."

M5's own roadmap ([m5-atlas-navigation-roadmap.md](../m5-atlas-navigation-roadmap.md),
[M0-D16](m0-d16-real-m5-atlas-navigation-and-visibility.md)) carries the
Owner's concrete Atlas rulings, including: defaulting to what is active now
with navigation back through milestones and packets; renaming Chat to Events
with the same navigation; Plan showing milestones then packets as a full list
while Now and Events show a single packet; surfacing only the most recent
worker check-in; a new tab for per-agent packet to-do lists; and plain-language
state labels rather than raw system vocabulary. Those are not restated here and
are not overridden.

---

## 9. Development discipline for Maestro itself

The [VennueSign SOP](../../../../Vennusign/AGENTS.md) is the discipline model,
and `docs/agents/independent-review-agent.md` is already a faithful translation
of it.

**The Owner's question that surfaced this:**

> "In the vennusign repo we have a well established disciplined development
> SOP. I thought we where using it for Maestro development and the maestro
> process"

Neither was followed. M4.01–M4.17e were pushed directly to `master` with no
branch, no PR, no independent review and no Done Record.

**Recorded accurately:** the Owner had granted merge authority for that work —
*"assume the roles needed to complete M4 end to end, you are local so you have
full system access and merge approved. I will be sleeping"*. **[PROPOSAL]** The
lesson is not that the grant was wrong, but that a grant of autonomy does not
suspend the SOP: independent review never by the author, a completed Done
Record as a merge precondition, and evidence that is a rerunnable command plus
its output, reported honestly as `PASS` / `N/A` / `UNTESTED`.

---

## 10. [PROPOSAL] Recovery sequence

**Not agreed.** The Owner asked *"How do we recover from this"*; this is the
assistant's answer, offered for a ruling.

1. **Stop the loop asserting reviews that did not happen** — stop at
   `MergeReady` and notify instead of self-approving, self-accepting and
   merging, so it becomes what it is: a scope-and-checks gate that hands off.
2. **Correct the record** so the next session does not build on "M4 complete"
   as though the product works.
3. **Build the wiring check** of §7.3.
4. **Build one real agent role end to end on real data** before scaffolding
   others. The Architect is the recommended first role — it unblocks the
   pipeline and produces the work graph everything else needs — with step 1 as
   the interim safety measure.

**[OWNER] Already authorized, and not yet delivered into M5:**

> "Yes build those and I would like that process added to m5 as well."

referring to the missing start-up commands. The Owner also asked repeatedly for
a plain, non-technical start-up runbook — *"I don't want to see the code I want
to see a list if steps to start maestro"* — which remains an outstanding
deliverable.

---

## 11. Smaller decisions and standing instructions

- **[OWNER] Packaging layout (future).** Versioned code under
  `/usr/local/lib/maestro/<version>/`, with `/usr/local/bin/maestro` as the
  symlink on `PATH`; upgrade and rollback repoint the symlink. Not yet built.
- **Runtime directory — out of scope.** **[OWNER]** *"Runtime is not in scope of
  this conversation"*. The Owner did call the "must live inside
  `<maestro-repo>/var/`" constraint *"unpractical"*; no location is decided and
  none is proposed here.
- **Model routing is part of the design.** Mapping packet risk, role and task
  type to eligible execution classes, local or cloud, is §11 of the
  control-plane design and remains unbuilt. **[OWNER]** *"It's part of the
  design"*. Model availability has never been a blocker: a local Ollama with
  six models including `qwen3.6:27b` is running, and **[OWNER]** *"Even if QWEN
  wasn't locally another cloud sub agent works"*.
- **[OWNER] Standing instruction — stop assuming.** *"That's another thing,
  there is way to much assumptions being made"*, and separately *"That's a
  stupid assumption"*. Verify before asserting. The RunPod-required claim in
  this session is one instance of a general problem, not the whole of it.
- **[OWNER] Standing instruction — answer style.** *"the policy is to answer
  plainly and shortly"*, raised repeatedly across the session including *"I keep
  asking for shorter answers but u keep reverting"* and *"Please did you follow
  the answer policy?"*.
- **[OWNER] Standing instruction — design questions are about the design.**
  *"when I ask a question like that, I know there is no code because of the
  report you have. Im talking in the future or how the product should be
  running based on the design that was made but was never implemented"*.

---

## 11a. [OWNER] Everything is configurable in a file

> "Everything should be configurable in a file to adjust"

Every operational threshold, bound, interval and limit is set in a
configuration file and adjustable without a code change. Values currently
hardcoded as module constants must move there. Known examples, not exhaustive:

- **Architect loop** — the configurable number of fidelity review rounds (§5),
  and the bound that stops it looping forever.
- **Development Manager** — restart threshold before switching models, context
  allocation per agent, WIP limits, scheduling parameters (§5.1, §5.2).
- **Execution** — heartbeat interval, lease extension, poll interval, attempt
  timeouts.
- **Notification** — `MAX_RETRYABLE_ATTEMPTS`, `BASE_RETRY_DELAY_SECONDS`,
  `MAX_RETRY_DELAY_SECONDS`, escalation schedule.
- **Capture and limits** — log capture caps, review-readiness command timeouts,
  stream poll interval and batch size.

**[OWNER] Approved 2026-09-08.** Two boundaries: project-specific policy
already belongs in the project's own
`maestro.project.yaml` binding, so this file is for Maestro's own operational
tuning rather than a second place to state project policy; and durable schema
constraints (text and JSON size limits, file modes) are correctness boundaries
rather than tuning knobs.

---

## 12. What this record authorizes

Once approved, this record is the authority for planning the next round of
milestones. It does not itself schedule that work, decompose it, or authorize
implementation.

Milestones planned from it must account for: the Architect loop (§5), the
ReturnSlice path (§6), registration triggering an Architect repository review
(§4), Atlas as a first-class surface for all of it (§8, alongside M5 which
stands), the evidence rules (§7), and the discipline in §9.

**The four blocking questions were resolved by the Owner on 2026-09-08:**
§5.1 (the Development Manager owns continuous scheduling), §3 (the product has
to function), §6.1 (fresh correction budgets — do not be inflexible), and §6.2
(the Architect has the last word on carry-forward, provided it causes no
further replanning).

Subsequently ruled the same day: the Development Manager's scheduling **uses
cloud reasoning** (§5.1), and the Manager owns **worker restart, context
allocation and model escalation** (§5.2). The runtime-directory question is
**out of scope** by Owner instruction (§11).

No **[OPEN]** item blocks planning. The remaining **[PROPOSAL]** items are
implementation details for the milestones themselves to settle.
