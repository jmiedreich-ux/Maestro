# M0-D18 — Wiring Audit Findings, Architect Loop, and Execution Authority

**Status:** **DRAFTED FOR OWNER REVIEW, 2026-09-08. Not yet Owner-approved.**
**Type:** Superseding authority and design amendment, once approved.

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

**Amends, once approved:** the
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
  polls OS process liveness. **[OPEN]** whether resumption is automatic, and
  under whose authority.

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

**[OPEN]** §7.4 below sets a stricter completion bar ("verify a real caller
exists in a real path") than this acceptance criterion, which permits accepting
known limitations tracked on a backlog. These are in tension. Which governs,
and in which circumstances, needs an Owner ruling.

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

### 5.1 [OPEN] Who assigns work

Unresolved, and load-bearing for everything downstream.

- **[OWNER]** *"I can see step 3 being the project architect doing the packet
  assignments and deciding which packet run in parallel. However, there is no
  step 4, step 4 is the development manager picking up the milestone and work
  packets, then delegate out to the assigned agent"*
- **[OWNER]** *"Once approved by owner, the architect then assigns and reviews
  the work that can happen in parallel"*
- **[OWNER]**, asking rather than ruling: *"So would you prefer the dev manager
  do a small scheduling process before delegating, maybe something that is
  reusable and continually evaluates assignments?"*

**[PROPOSAL]** Split it: the Architect decides **suitability** at plan time
(rank, dependencies, specialist role, execution class); the Development Manager
runs a small, reusable process that **continually re-evaluates** and decides
**timing** — which eligible packet runs next, on which worker, given current
locks, leases, worker health and WIP. Rationale: assignments go stale as locks
free and packets return, and the Manager already holds every input a scheduler
needs. Its role contract already says *"Select the highest-ranked eligible
item, not simply the oldest queue entry."* Either resolution makes the five
decorative fields of §2 live.

**[OPEN]** Whether that scheduling process is purely deterministic or may use
cloud reasoning. The Owner probed this directly — *"So when does it start a so
called dev manager cloud role?"* — and it was not settled. The role contract
says the Manager *"may use cloud reasoning"* without saying when.

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

**[PROPOSAL]** derived from that instruction: a packet produced by an Architect
split is new scope and starts with a **fresh** review/correction budget. This
requires amending the Bootstrap Convergence Policy, which currently requires
counts never reset across packet replacement. The Owner stated the principle;
this specific amendment is the assistant's inference from it and needs
confirmation.

**[OWNER] standing instruction, beyond this case:** do not make these questions
more complex than they need to be.

### 6.2 What carries forward from completed work

**[OWNER]**

> "I'm leaning towards if something needs to go back to planning we should
> start over on the packet. I'm also ok if the architect agent makes the call
> during that review"

Recorded as stated: a **leaning**, not yet a fixed default, plus an explicit
willingness to let the Architect make the call during its review.

**[PROPOSAL]** Formalise as: starting over is the default; the Architect may
rule otherwise during its review. **[OPEN]** whether granting the Architect
that call is Owner-tier under M0-D17's "redefining what a role is allowed to
accept" — the assistant classified it that way; the Owner did not.

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
future capability complete, verify a real caller exists in a real path. See the
**[OPEN]** tension with §3's acceptance criterion.

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
- **[OPEN] Runtime directory.** The Owner called the "must live inside
  `<maestro-repo>/var/`" constraint *"unpractical"*. `~/.maestro/` was proposed
  and discussed but never agreed — the Owner's last word on it was a question.
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

## 12. What this record authorizes

Once approved, this record is the authority for planning the next round of
milestones. It does not itself schedule that work, decompose it, or authorize
implementation.

Milestones planned from it must account for: the Architect loop (§5), the
ReturnSlice path (§6), registration triggering an Architect repository review
(§4), Atlas as a first-class surface for all of it (§8, alongside M5 which
stands), the evidence rules (§7), and the discipline in §9.

**Before planning begins, the Owner must resolve every [OPEN] item**, in
particular §5.1 (who assigns work), §3 (the acceptance-criterion tension), and
§6.1–6.2 (the two ReturnSlice rulings, currently proposals). Planning on top of
an unresolved §5.1 would repeat this record's own root cause.
