# Evidence — Owner's words, planning session of 2026-09-09

**Why this file exists.** [M0-D19](../m0-d19-next-milestone-round.md) introduces
the marker `[OWNER — session]` for Owner rulings made in the 2026-09-09 planning
session rather than in M0-D18. That marker replaced an earlier one,
`[OWNER — substance]`, which a fidelity review rejected because it asserted
Owner authority nothing could check.

A second fidelity review then found the replacement had the same defect in a
different place: the transcript it pointed at was session-scoped scratch, not
anything in the repository. Every `[OWNER — session]` quote in M0-D19 is
checkable against this file.

**What this is.** Every message the Owner typed in that session, verbatim and in
order, extracted from the session transcript. Assistant turns are not included;
where a message is an answer, the question it answers is identified in M0-D19 at
the point of quotation.

**Provenance.** Extracted programmatically from
`~/.claude/projects/-home-jeremy-Development-Maestro/47af148e-4cd3-4232-98ea-df1074a22c13.jsonl`.
Tool results, system reminders and slash-command echoes were excluded; nothing
else was filtered, and no message was edited.

---

## The Owner's messages

```
--- OWNER MESSAGE 1 ---
Maestro milestone planning. Work in /home/jeremy/Development/Maestro-m2-atlas-review
(not the stale main Maestro dir). Everything is committed and pushed on master.

Read first, before anything else:
docs/planning/decisions/m0-d18-real-wiring-audit-authority-and-architect-loop.md

That's M0-D18, Owner-approved 2026-09-08, and it's the governing authority for
this work. It supersedes earlier planning docs on conflict. Don't re-derive the
audit behind it — it's summarised in §2 and linked in full.

Its convention: every statement is marked [OWNER] (my words, quoted),
[PROPOSAL] (assistant inference, not binding), or [OPEN] (unresolved). Keep that
convention in anything you write that extends it.

The task: plan the next round of milestones from D18. Specifically it needs to
account for the Architect loop (§5), the ReturnSlice path (§6), registration
triggering an Architect repo review that produces the work graph (§4), Atlas as
a first-class surface (§8 — M5 stands and is not superseded), the evidence rules
(§7), and the recovery sequence (§10, which is a proposal, not agreed).

Before proposing a plan:
- §5.3 is the one open decision (per-step reasoning budget enforcement). Ask me.
- Two loose ends are agreed in substance but not written up yet: re-registration
  that supersedes without reopening completed work, and multi-project support
  (locks scoped per project, one loop for all projects, service account). Both
  are summarised in the M0-D18 memory entry. They need writing up as part of
  planning.
- Recovery step 1 — stopping the loop from asserting reviews that didn't happen
  — is live in the code right now. Tell me where you think it sits relative to
  the rest.

Answer plainly and short. Don't assume — verify against the code before
asserting anything about what exists.

--- OWNER MESSAGE 2 ---
Ok

--- OWNER MESSAGE 3 ---
Simple, registration cannot take place when there is active work in progress and having the the var folder is fine for db, and installation

--- OWNER MESSAGE 4 ---
Which is what?

--- OWNER MESSAGE 5 ---
Consider doing a independent ago fidelity check on what you just gave me, the build order doesn’t hold for me

--- OWNER MESSAGE 6 ---
Ok

--- OWNER MESSAGE 7 ---
<task-notification>
<task-id>afa02572af278652a</task-id>
<tool-use-id>toolu_01WdA8BVP88y5VkSH1dEfnsE</tool-use-id>
<output-file>/tmp/claude-1000/-home-jeremy-Development-Maestro/8dbc64ad-0bd4-4902-b3c1-0bf7ec9cc09d/tasks/afa02572af278652a.output</output-file>
<status>completed</status>
<summary>Agent "Fidelity review D19 vs D18" finished</summary>
<note>A task-notification fires each time this agent stops with no live background children of its own. The user can send it another message and resume it, so the same task-id may notify more than once.</note>
<result>I've read both documents in full and verified every `[FINDING]`, every quote, and the code claims. Line-number spot checks on D19's `[FINDING]`s all pass (`storage.py:736/750/751/344/826/905/1106`, `operational_state.py:2457`, `packet_wrapper.py:40`, `development_manager.py:180/329/334/414/425`, 56 Atlas files, ten CLI commands). Every quote D19 draws from D18 matches D18 verbatim. The defects are elsewhere.

---

## SERIOUS

**1. §7.3's `var/` ruling states as Owner authority something the Owner's quote does not say, and it is contradicted by the code D19 cites.**

D19:552-556
&gt; **The ruling.** `var/` is the right home for the database and the installation. `config.py`'s `validate_runtime_dir` is not a problem to be solved, and M13 does not need to move it.

The Owner's 2026-09-09 quote is *"having the the var folder is fine for db, and installation"*. It says nothing about `validate_runtime_dir`, and nothing about `var/` being **inside the Maestro repository** — which is the only thing that constraint actually enforces. `services/maestro/maestro/config.py:14-15` defines `DEFAULT_RUNTIME_DIR = REPOSITORY_ROOT / "var"`, and line 20 documents `RuntimePathError` as *"Raised before any mutation when a runtime path is outside repository var/"*. That is precisely the *"must live inside `&lt;maestro-repo&gt;/var/`"* constraint D18:684-685 records the Owner calling **"unpractical"**. D19 turns "a var folder is fine" into "the repo-relative constraint the Owner objected to is not a problem", and puts it in an unmarked **The ruling** paragraph directly under an `[OWNER]` heading — the exact provenance failure D18 exists to document. It is then locked in at D19:625-627 as *"Closed 2026-09-09 by Owner ruling … Neither is open."*

Worse, D19's own next paragraph refutes it: D19:566-568 places `var/` beneath `/usr/local/lib/maestro/&lt;version&gt;/`, which is not a Maestro repository at all and which `validate_runtime_dir` as written would not accept.

**2. §7.3's "consistent" reasoning is rationalisation, and it decides a question D18 ruled out of scope while claiming not to.**

D19:561-564
&gt; **[PROPOSAL]** Read together, the two statements are consistent: `var/` is right for durable state Maestro owns, and the earlier objection was to the constraint being applied to *everything* a runtime touches. Nothing in M13 requires reopening it, and this record does not.

Nothing in D18 supports the second clause. D18:683-686 records exactly two things: `[OWNER]` *"Runtime is not in scope of this conversation"*, and that the Owner called the `&lt;maestro-repo&gt;/var/` constraint *"unpractical"* — followed by **"no location is decided and none is proposed here."** The gloss that the objection was really about "everything a runtime touches" is invented to make the two statements agree; the recorded objection is specifically to the repo-relative location, which is what §7.3 now blesses. And "this record does not [reopen it]" is false on its face — the paragraph it closes decides a location, which is the one thing D18 said would not be done. The `[PROPOSAL]` marker covers the reasoning but not the "Nothing in M13 requires reopening it, and this record does not" claim, which is an assertion about D18's status.

**3. D19 treats M0-D18 §10 as an agreed recovery sequence. D18 says in bold that it is not agreed, and D19 never once records that.**

D18:651-654
&gt; ## 10. [PROPOSAL] Recovery sequence
&gt; **Not agreed.** The Owner asked *"How do we recover from this"*; this is the assistant's answer, offered for a ruling.

D19 builds on it six times — D19:159 (*"M0-D18 §10 steps 1 and 2 are not milestone work"*), D19:184 (**"M0-D18 §10 steps 3 and 4 are scheduled"**, bolded and unmarked), D19:186, D19:236, D19:267 (*"**This is M0-D18 §10 step 4**"*), D19:589 — and the string "Not agreed" appears zero times in D19. D19's `[PROPOSAL]` markers in §4 attach to *how* to schedule the steps, taking the *what* as settled. The entire pre-milestone section and M7's identity as "the first real role" rest on an assistant proposal the Owner never ruled on, presented as an inherited plan. This is the single clearest case of D19 misrepresenting its source authority's provenance.

**4. `[OWNER — substance]` manufactures uncheckable Owner authority, and two of the eight milestones rest entirely on it.**

D19:400-402, D19:487-493, D19:511, D19:528
&gt; **[OWNER — substance]** Agreed in the session that produced M0-D18 and never written up. No verbatim quote was captured; the substance below is settled…
&gt; **The requirement.** Maestro runs more than one project. Locks scope **per project**; there is **one loop for all projects**, not one loop per project; and the Development Manager runs as a Linux **service account**.

D18 is the record of that session and contains no mention of multi-project operation, loop cardinality, service accounts, or re-registration. These are specific technical decisions — not remembered gist — asserted as settled Owner authority with nothing to check them against. M12 and M13 (D19:386-394) are scheduled milestones whose entire basis is this marker, and D19:643-645 would have the Owner authorize their decomposition into packets. D18:693-696 carries a standing `[OWNER]` instruction against exactly this: *"That's another thing, there is way to much assumptions being made"* … *"Verify before asserting."* The honest marker for an unquotable, unverifiable recollection is `[PROPOSAL]` — recommend the requirement, ask the Owner to confirm it. D19's preamble (D19:28-30) presents the new category as a fidelity improvement; it is the opposite, because `[OWNER — substance]` is treated as binding everywhere it appears.

**5. §4 instructs the corrections to be pushed straight to `master` — the precise practice §9 says this round exists to stop.**

D19:159-160
&gt; **[PROPOSAL]** M0-D18 §10 steps 1 and 2 are not milestone work and should not be scheduled as any. They should land on `master` directly, ahead of M6.

D19:608-611
&gt; The discipline of M0-D18 §9 applies to this round's own development: a branch, a pull request, an independent review never by the author, and a completed Done Record as a merge precondition. M4.01–M4.17e were pushed straight to `master`; this round is where that stops.

D18:638-639 names the failure in the same words: *"M4.01–M4.17e were pushed directly to `master` with no branch, no PR, no independent review and no Done Record."* Step 1 is not a doc change — it deletes durable-write calls from `development_manager.py`. Declaring it "not scope" exempts it from the definition of done, the Done Record, and independent review, and D18:641-647's whole point is that a grant of autonomy does not suspend the SOP.

**6. D18 §8's `[OWNER]` Atlas requirement is downgraded to `[PROPOSAL]` and then omitted from seven of the eight milestone scopes.**

D19:194-197
&gt; **[PROPOSAL]** Every milestone in this round ships **its own Atlas surface as part of its own definition of done**.

D18:596-602 marks this `[OWNER]` — *"atlas has to be first class feature reporting all this because there will be no terminal window eventually"* — followed by "Every transition in §5 and §6 requires a first-class Atlas surface", and D18:744 lists Atlas among what the round **must** account for. D19 restyles a binding requirement as its own proposal. Then it does not honour it: only M8 (D19:289-291) names an Atlas surface. M6, M7, M9, M10, M11, M12 and M13 specify none. D19:201-203 says the trailing-Atlas pattern "is how the fixtures in §3 came to exist" — and then repeats it.

**7. Audit findings with no milestone anywhere in the round, while §3 claims the plan is built on the audit.**

D19:152-153
&gt; Nothing in the 2026-09-08 audit has been overtaken by events. The plan below is built on that.

Grepped exhaustively against D19. The following D18 §2 findings appear in no milestone and, in most cases, nowhere in D19 at all:

- **Backup/recovery.** D18:111 — *"backup/recovery is zero code"*. Zero occurrences of "backup" in D19. `docs/planning/decisions/m0-d07-sqlite-backup-and-recovery.md` is **Accepted** and unimplemented; D19 never cites it. Verified: no `backup` identifier in `services/maestro/maestro/`.
- **Escalation never fires.** D18:112-113 — `escalation_at` written `NULL` and read by nobody. Confirmed still true (`notification_triggers.py:59` writes `"escalation_at": None`). Zero coverage in D19; every "escalat" hit in D19 is *model* escalation or Architect escalation.
- **Notification triggers cover 2 of 8 required events.** D18:113-114. No milestone. `m0-d04-notifications-and-escalation.md` is never referenced.
- **Acknowledgement is an unreachable state.** D18:113. Zero occurrences of "acknowledg" in D19.
- **Secrets have no consumer.** D18:115. Appears in D19 only as a `[FINDING]` (D19:539, *"`secrets.py` has **no importer at all**"*). No milestone gives it one; M13's `[PROPOSAL]` (D19:541-546) grants an identity, not a secrets consumer. `m0-d03-access-and-secrets.md` is never cited.
- **Atlas's existing fixture defects.** D18:105-110 — `systemState` never derived, so crash/disconnect/empty states cannot appear; desktop Performance/Agents/History are literal placeholders; all four operator commands unreachable from the UI; cost strip hardcoded `61% / 14% / 5% / 80%`. D19:132-137 re-verifies the fixtures, then D19:205-207 says *"This rule adds surfaces for new states; it does not redefine M5"* — deferring the existing defects to M5 without checking that M5 covers them. No milestone repairs them.
- **The token/cost stack.** D18:111-112 names the *context/token/cost* stack. D19 covers context (M10 items 3 and 5) and drops token and cost reporting; "token" appears zero times in D19.

**8. `[OWNER]` "Maestro has never built anything" is not carried into any completion bar.**

D18:83-87 marks this `[OWNER]`: *"Yes but the so called loop didn't develop this"* — *"Any claim about what the loop 'does' must be read against that."* D19's definition of done (§9, D19:594-616) requires a real caller in a real path, an Atlas surface, honest evidence and SOP discipline. It never requires that Maestro's own loop author anything. No milestone in M6–M13 has "Maestro's loop produced this packet" as a criterion, and D19:608-611 assumes the round is built by the assistant under the SOP. The round therefore ends with the audit's headline finding untested.

---

## MODERATE

**9. Two of the six string-literal roles get no milestone and no mention.** D18:88-91 names six: Project Architect, Integration Agent, Independent Reviewer, **QA/Murphy**, Coordinator/scheduler, **Decision Fidelity Reviewer**. D19 covers Architect (M7/M8), Integration Agent and Independent Reviewer (M9), Coordinator/scheduler (M10). "Murphy", "QA" and "Decision Fidelity" each appear **zero times** in D19. M8's bounded fidelity rounds are the Architect's own loop, not the Decision Fidelity Reviewer role. Yet D19:213-216 opens M6 by citing the six-of-nine finding as the round's rationale.

**10. D18 §11a's `[OWNER]` scope is narrowed without saying so.** D18:710-714: *"Everything should be configurable in a file to adjust"* … "Values currently hardcoded as module constants **must** move there", with notification retry constants and the escalation schedule as named examples (D18:722-723). D19:231-232 reduces this to *"M6 moves the thresholds it needs and establishes the file; later milestones add their own values to it"*. Since no milestone in the round owns notifications or escalation, those named constants are deferred indefinitely by a plan that presents itself as implementing §11a.

**11. D18 §7.2 is dropped.** D18:560-570 is `[OWNER]`: *"Way to much effort is aligned at writing tests verse spent on writing the product"* and *"But it was all useless"*, with 11,299 product lines against 18,602 test lines. D18:745 requires the round to account for "the evidence rules (§7)". D19 accounts for §7.1, §7.3 and §7.4 and says nothing about §7.2. Nothing in §9's definition of done guards against repeating the imbalance.

**12. D18 §3's Architect-as-answerer ruling has no home.** D18:140-144, `[OWNER]`: *"Should any other role get stuck or have questions, the architect assumes responsibilities for the answer."* M11 covers the out-of-scope-discovery half of that quote; the stuck/questions escalation channel is scheduled nowhere. D19:293-297 mentions Architect escalation only as a `[PROPOSAL]` aside about which repository it lives in.

**13. D18 `[PROPOSAL]`s are cited as D18 authority — inconsistently.** D19:604-611 cites *"(M0-D18 §9)"* for the evidence format and the SOP list, and D19:607 cites §7.1 for "never substituted with a fixture". All of that text lives inside D18's `[PROPOSAL]` paragraphs (D18:643-647 and D18:552-555), the latter explicitly *"Scope of the ban, for confirmation"*. D19:271-273 does the same in M7: *"**Evidence bar** (M0-D18 §7.1, fake data banned): proved against a real repository, not a fixture manifest"* — "fixture manifests" is from the unconfirmed proposal list, not from the `[OWNER]` ban. D19 knows how to do this correctly: D19:179 and D19:200 both flag the source as a D18 `[PROPOSAL]`. The inconsistency is the defect — a reader cannot tell which citations were checked.

**14. M6 elevates unmarked D18 prose to a "ruling" and schedules an amendment D18 did not authorize.**

D19:245-249
&gt; **Consequence for the reviewer contract.** M0-D18 §5.4.2 **rules** that `docs/agents/independent-review-agent.md`'s *"secrets, generated artifacts, debug code, placeholders, unsafe defaults"* belong in the wrapper. M6 moves them and amends the contract…

D18:450-456 is unmarked assistant reasoning ("By §5.4.1 they belong in the wrapper… **The reviewer should be told**"). The only `[OWNER]` marker nearby is D18:446, and it carries no Owner quote — it quotes `lifecycle.py`. D18's **Amends** header (D18:25-30) covers `maestro-development-manager.md` §5 and the Bootstrap Convergence Policy §6.1 only; `independent-review-agent.md` is not on it. D19:645 states *"it does not amend M0-D18"* while scheduling an amendment to a role contract on the strength of D18 text that was never marked as authority.

**15. "The standing instruction to split aggressively" is uncited and is not in D18.** D19:218: *"Scope, deliberately small, per the standing instruction to split aggressively."* D18's standard (D18:247-254) is `[OWNER]` *"smallest possible packets"* and "no latent or unknown scope"; "split aggressively" appears nowhere in D18. In a document whose subject is provenance, citing an unnamed standing instruction is a defect, and the phrase is doing rhetorical work in the one milestone that most needs the justification (see 16).

**16. M6 and M13 violate the standard they invoke.** M6 (D19:220-239) bundles four unrelated subsystems — the deterministic wrapper, the operational configuration file, role-contract loading, and the wiring/orphan gate — under the heading "Scope, deliberately small". Only the first shares a subject with the others. M13 (D19:485-568) bundles lock re-scoping, cross-project scheduler semantics, a Linux service account, a GitHub App identity, and by implication the secrets consumer. Against D18:253-254's **smallest possible packets**, calling M6 small does not make it small.

**17. Milestone scope is defined outside the milestone bodies — "latent scope" by D18's own second standard.** D19:522-524 adds cross-project ranking to M10 from inside §7.2; M10's own scope list (D19:328-341) says only "which eligible packet runs next". D19:633-634 makes the start-up runbook *"a deliverable of M6"* from inside §10; M6's four-item scope list does not contain it. A reader of M6 or M10 does not see its full scope, which is precisely what D18:253-254's "no latent or unknown scope" prohibits.

**18. Hand-decomposition of M6 and M7 bypasses the fidelity review D18 requires.** D19:643-645: *"this record authorizes the decomposition of M6–M13 into packets — by the Architect loop itself once M8 exists, and by hand before that."* D18:249-251 is `[OWNER]`: *"packetize M4 and then have an independent architecture fidelity review done to make sure the packets are the smallest they can be and to ensure there is no sudden scope issues."* The review, not the packetizer, is the `[OWNER]` requirement. D19 drops it for the two milestones that precede M8 and does not say so.

---

## MINOR

**19. §2's ruling pre-empts its own proposal.** D19:79-80 rules history is *"summarised past a **configured** threshold"*; the Owner said *"Summarised after a threshold"*. D19:82 then marks the configuration-ness `[PROPOSAL]`. The ruling has already asserted what the proposal asks for.

**20. D18 §5's `[OWNER]` Architect-repository item is placed under `[PROPOSAL]`.** D19:293-297. D18:209-221 marks it **`[OWNER]` The Architect has its own loop and its own repository**, and D19's `[PROPOSAL]` block absorbs D18's own following prose ("Escalation to it is a handoff of facts, not a function call") along with the scheduling claim. The quote is also trimmed from *"And possibly escalation to the project architect which lives in it's own repo"* — the qualifier is dropped, though not in a way that changes what D19 uses it for.

**21. D18's status header is now stale and D19 does not say so.** D18:5-7 reads *"One **[OPEN]** item remains on the decision list: §5.3."* D19:52 and D19:647 close it. D19:6 claims it *"Extends, and does not amend"* D18. Materially fine, but D18's front matter now misstates the record and nothing flags it.

**22. Unevidenced estimate under a "stop assuming" instruction.** D19:171: *"The cost of leaving it compounds; the fix is an hour."* No basis given, in the section that removes durable-write calls from `development_manager.py`.

**23. §9's completeness check is circular for M6.** D19:600-601 makes *"M6's wiring gate … the mechanical check"* for every milestone's real-caller bar, including M6, which builds the gate.

---

**Nothing found in one category:** I found **no altered or fabricated D18 quotes**. Every quoted string in D19 that is sourced from D18 matches D18 verbatim (allowing for line-wrap and dropped trailing periods), and every `[FINDING]`'s file and line reference is accurate against `ad614b7`. The provenance damage in D19 is done through mislabelling and silence, not through misquotation.</result>
<usage><subagent_tokens>101304</subagent_tokens><tool_uses>16</tool_uses><duration_ms>440342</duration_ms></usage>
</task-notification>

--- OWNER MESSAGE 8 ---
<task-notification>
<task-id>a1584ed9c4ecd314c</task-id>
<tool-use-id>toolu_01HiKGWPCsCek6b8oeqYoLQt</tool-use-id>
<output-file>/tmp/claude-1000/-home-jeremy-Development-Maestro/8dbc64ad-0bd4-4902-b3c1-0bf7ec9cc09d/tasks/a1584ed9c4ecd314c.output</output-file>
<status>completed</status>
<summary>Agent "Attack the M6-M13 build order" finished</summary>
<note>A task-notification fires each time this agent stops with no live background children of its own. The user can send it another message and resume it, so the same task-id may notify more than once.</note>
<result>I have what I need. Findings first, most serious first.

---

# FINDINGS

## 1. The central ordering argument (D19 §8) is a category error. M6's wrapper cannot protect M7's Architect, because the Architect cannot run through the machinery the wrapper wraps.

D19 §8 says the wrapper must precede the Architect so "the first real role" doesn't spend attempts and review rounds on deterministic misses. Mechanically, the wrapper wraps *packet agent delegation*, and the Architect of M7 is not a packet.

The chain, `/home/jeremy/Development/Maestro-m2-atlas-review/services/maestro/maestro/`:

- `attempt_onboarding.py:run_attempt` reads an **Attempt** row, its **Packet**, its **Lease**, and builds `ExecutorPreflight(base_commit=packet["base_commit"], worktree_path=Path(lease["worktree_path"]), allowed_paths=packet["owned_paths_json"], …)`.
- `executor.py:29-42` — `ExecutorPreflight` requires `base_commit` and an existing worktree dir. `LocalQwenExecutorAdapter.retrieve_evidence` decides success by `made_a_commit = head_commit is not None and head_commit != attempt.base_commit` (`executor.py:139-141`).
- `dispatch_orchestrator.py:107` — `DispatchOrchestrator.run` only drives an attempt that already exists; it explicitly "does not claim an assignment itself."
- `storage.py` packets DDL: `work_item_id TEXT NOT NULL REFERENCES work_items(work_item_id)`, `base_commit TEXT NOT NULL CHECK(length(base_commit)=40 …)`, `expected_branch TEXT NOT NULL`. `work_items.graph_projection_id` is a NOT NULL FK to `graph_projections` (`storage.py:788-791`). FKs are enforced (`storage.py:593`).

**A packet requires a work item, which requires a graph projection — which is exactly the artifact M7's Architect produces.** There is no packet, no attempt, no lease, no base_commit and no branch at registration time. The wrapper has nothing to wrap.

`review_readiness.py` is the same shape. Its entire blocker vocabulary (`review_readiness.py:80-98`) is `BASE_NOT_COMMIT`, `HEAD_NOT_COMMIT`, `EMPTY_COMMIT_RANGE`, `EMPTY_CHANGED_PATHS`, `DIRTY_BEFORE`, `PATH_NOT_ALLOWED`, `DIRTY_AFTER`. Every one presupposes a git commit range on a checked-out repo.

And the wrapper's three named deliverables:
- "commits the whole worktree when the worker did not" — no per-packet worktree exists for the Architect;
- "creates the branch if the worker did not" — no `expected_branch` exists;
- "caps captured output" — already done (`executor.py:107-114` streams to a log file; `review_readiness.py:19 MAX_CAPTURE_BYTES = 65_536`; `packet_wrapper.py:22 MAX_CAPTURED_LOG_BYTES = 2048`).

M6's wrapper de-risks the **coding agent**. The coding agent is not M7. So M6-before-M7 is not load-bearing; it is load-bearing for M10-era work.

## 2. The cost the wrapper saves does not exist yet, and will not until real reviewers exist.

D18 §5.4.1 is explicit that the saving is "not spending a bounded review round, and possibly the packet's one correction." Trace what a packet actually meets at review today:

- `development_manager.py:332` — `route_independent_implementation(…, result="Approve")`. The result is a **hardcoded literal**.
- `review_dispatch.py:69` — the parameter's default is `result: str = "Approve"`.
- The Integration review is equally fabricated: `development_manager.py:313` routes `result="ValidateOnly"` with `reviewer_instance="development-manager-loop-integration"`.
- The store's independence check (`operational_state.py:1911-1914`) only rejects a `reviewer_instance` equal to `model_identity`, `runtime_identity` or the lease `holder_id`. A string literal passes.
- `development_manager.py:271-281` states in its own docstring that this loop "can never mechanically produce a real `RequestChanges`."
- Grepping `RequestChanges` across `services/maestro/maestro/` returns only the schema CHECK, the two route tables, a comment and a notification-trigger docstring. **No production code path produces one.**

Consequences: `correction_count` is always 0. `attempts` CHECK requires `attempt_number=2 AND attempt_kind='TargetedCorrection' AND correction_for_review_id IS NOT NULL` — so a correction attempt has never been constructible. And there is **no bounded review-round count anywhere in the code** — no constant, no counter, no config key.

**During M7, the wrapper protects a budget of zero.** Its first real consumer is M9.

One nuance that cuts the other way and is worth keeping: `UNIQUE(packet_id, attempt_number)` plus the CHECK means a packet gets exactly **one** Initial attempt. So a forgotten commit does not cost "one of two attempts" as D18 §5.4 says — it costs the packet's only initial attempt, and recovery is a whole new packet via `redispatch_after_needs_replan`. The commit half of the wrapper has a real cost *today*. It is just a cost borne by the coding agent, not the Architect.

## 3. Unscheduled and blocking: M9 as written deadlocks the pipeline the moment a reviewer says no.

`operational_state.py:2141` — `record_and_accept_packet` rejects the acceptance unless `review_correction_number == 0`, unconditionally. `owner_acceptance.py`'s own docstring names this as a known M1 defect ("a packet that went through even one real correction … can never be accepted").

Meanwhile `_CORRECTION_REVIEW_ROUTES` (`operational_state.py:80`) routes a correction-pass `Approve` to `MergeReady` — and that review necessarily carries `correction_number=1`. **A corrected packet reaches MergeReady and can never be accepted or merged.** `development_manager.py:395` already dodges it: `if packet["correction_count"] != 0: continue`.

Also: first-pass `RequestChanges` routes to `AwaitingArchitect` (`operational_state.py:75`), whose only exit is `record_and_dispatch_correction`, whose only caller is an Atlas POST route Atlas never reaches (finding 7).

D19 schedules this nowhere. M9 turns on corrections into a dead end.

## 4. (c) M6 is scaffolding in exactly the sense D18 §10 step 4 warns against. Ruling: mostly yes.

**For M6-first:** item 4 (the orphan gate) *is* D18 §10 step 3, which explicitly precedes step 4. Role-contract loading and a config loader are shared plumbing; three roles arrive in M8–M10 and building them once is cheaper. D18 §5.4.1's "the first question is whether the harness can simply do it" is a standing rule, not a milestone.

**Against:** step 4 reads "Build one real agent role end to end on real data before scaffolding others." M6 ships four artifacts and **zero roles**, and its own proof is "re-hosting the existing qwen worker" — re-plumbing the one path that already works. Every deliverable's consumer is a role that does not exist yet. That is command-before-caller: precisely the pattern D18 §2 found (6 built / 9 partial / 23 not built / 7 built-but-orphaned) and precisely what §7.3's own orphan gate would flag if pointed at M6's output.

**Ruling:** item 4 is step 3 and belongs first — it depends on nothing and it is the mechanical grader for every later "is it real?" claim. Items 1 and 2 are scaffolding and should ship with their first real consumer. Item 3 is genuinely needed by M7 but M6 builds it in the wrong shape (see finding 5).

One supporting correction to D18 itself: §5.4.2's "This existed and was lost — `lifecycle.py` rejects on *dependency/configuration/placeholder violation*" is materially overstated. `lifecycle.py:57-62` rejects on `result.violations`, and `violations` is fixture-declared: `packet_wrapper.py:137-145` returns `(f"unapproved {scenario.removesuffix('-violation')}",)` from a scenario *string* in the packet JSON. **No placeholder detector has ever existed.** M6 item 1's model-shaped check set is net-new invention, not restoration — which makes it carry exactly the "latent or unknown scope" the fidelity standard in D18 §5 bans.

## 5. (e) M6 is at least four milestones with no technical dependency between them.

| # | Deliverable | Touches | Depends on any sibling? |
|---|---|---|---|
| 1 | commit / branch / output-cap wrapper | `executor.py`, `dispatch_orchestrator.py` | no |
| 2 | model-shaped check set (TODO/placeholder/dupe/dead-link) | a new diff linter | shares only a call site with 1 |
| 3 | configuration file | `config.py` | no |
| 4 | wiring / orphan gate | static analysis; imports no maestro module | no |
| 5 | (D19 §10) plain-language start-up runbook | docs | no |

They share nothing but a milestone number. Under "smallest packets they can be," that is four-to-five milestones.

Item 4 also hides a second capability: D18 §7.3's scope is "**both** Maestro **and** the products Maestro builds." Foundry is TypeScript/React; Maestro is Python plus a TS app. A language-agnostic orphan checker for arbitrary joined projects is a milestone of its own, buried in one bullet.

Item 3 in M6's form is also wrong-shaped for M7: it loads `packet["role_contract_reference"]` inside `build_instructions` (`development_manager.py:180`) — a **packet column**. The Architect has no packet. What M7 actually needs is a role-agnostic agent invocation (spawn a role, load its `docs/agents/` contract, capture bounded output, return a result) that isn't packet-scoped. **No such abstraction exists anywhere** — `ExecutorAdapter.submit` is the only agent entry point and it is git/worktree-typed. That is the one genuine piece of shared plumbing in M6, and D19 doesn't name it.

## 6. (d) The config file is speculative. Its real content is decided by M8 and M10.

Everything D18 §11a names as significant is downstream-determined:

| Value | Determined by |
|---|---|
| fidelity review rounds N, and the loop bound | M8 |
| restart threshold before model switch | M10 |
| context allocation per agent | M10 |
| WIP limits, scheduling parameters, fast-model choice | M10 |
| history summarisation threshold (D19 §2) | M10 |

What exists to move today is small and has nothing to do with the Architect: `MAX_CAPTURE_BYTES=65_536`, `MAX_CAPTURED_LOG_BYTES=2048`, `MAX_RETRYABLE_ATTEMPTS=5` / `BASE_RETRY_DELAY_SECONDS=30` / `MAX_RETRY_DELAY_SECONDS=3600` (`notification_delivery.py:35-37`), `_STREAM_POLL_INTERVAL_SECONDS=0.2` / `_STREAM_BATCH_LIMIT=200` (`read_api.py:327-328`), `SQLITE_BUSY_TIMEOUT_MS=5000`, and the orchestrator's three default kwargs (`dispatch_orchestrator.py:100-102`).

M7 needs none of them. D19 concedes the point in its own words — "later milestones add their own values to it rather than adding constants" — which describes a *mechanism*, not a milestone. A config file with no reader is an orphan under M6's own item-4 gate.

## 7. (f) M8's Owner gate is the largest uncounted scope in the round — Atlas cannot fetch or approve a work graph.

Decisive, and it is a backend fact, not a frontend one: the read API exposes only `/snapshot/packets`, `/snapshot/attempts`, `/snapshot/reviews`, `/snapshot/events`, `/stream/events` (`read_api.py:457-460`). **There is no endpoint for `work_items` or `graph_projections`.** The Owner gate of M8 approves the *work graph* — the one entity Atlas literally cannot read.

Nor is there a command for it. The four POST routes are `/command/resolve-decision`, `/command/dispatch-correction`, `/command/resolve-crash`, `/command/redispatch-crash` (`read_api.py:1007-1012`). None is "Owner approves an Architect plan."

On the frontend (`/home/jeremy/Development/Maestro-m2-atlas-review/apps/atlas/src/`), Atlas has **zero reachable write path**: `decision/OwnerDecisionCard.tsx` and `crash/CrashCard.tsx` gate every button on an optional `real?:` prop, and no non-test file ever passes `real=` — buttons render `disabled`. `App.tsx` has no router (a single `window.innerWidth &lt; 880` branch); three of five desktop views render the literal string `` `${VIEW_LABEL[selected]} view` ``; the active packet is a hardcoded constant `REAL_ACTIVE_PACKET_ID = "packet-foundry-cg-m4-20-v2"` in `shell/realActivePacket.ts` because no list-active-packets API exists; twelve fixture modules totalling ~1,112 lines are imported by production components.

So M8 as scoped silently contains: a graph read endpoint, a plan-approval command, `real=` wiring through the component tree, a work-graph rendering surface, and an active-work listing. That is a milestone. D19 §5.0's "every milestone ships its own Atlas surface" is the right rule, but M8's surface is the first one with a write path and it is not counted anywhere.

## 8. (f) M10 does not depend on M9. The plan orders them backwards on risk.

The scheduler's inputs are `work_items.{planned_rank, dependencies_json, priority, execution_classes_json}`, locks, leases, worker health, WIP. Restart, context allocation and model escalation are Manager-internal; `record_worker_progress` (`operational_state.py:2457`) and `blocker_payload_json` have no callers. **Not one of these needs a reviewer.**

M9, conversely, is the milestone that switches on the correction dead end of finding 3. D19 puts the blocked milestone first and the unblocked, throughput-creating one second.

## 9. (f) M11's stated dependency is overstated but its position is defensible.

M11 needs M8 (the Architect to split), *a raiser* — which can be the coding agent's own `blocker_payload_json`, needing no reviewer at all — and only M10's dependency-release, not its context allocation, model escalation or per-step instrumentation. The guard rail is already there: `record_and_dispatch_correction` refuses a `ReturnSlice` disposition (`operational_state.py:887-890`). Keep the position; the justification "it exercises all three" is true, "it requires all of all three" is not.

## 10. (f) M13 is correctly placed as a *capability* and wrongly placed as a *schema change*.

`storage.py:1106` — `CREATE UNIQUE INDEX one_active_resource_key ON resource_locks(resource_key) WHERE state='Active'`, globally unique, and `resource_locks` has no `project_id`.

The problem with deferring the fix is the migration contract. `storage.py:423-431`: "Versions 4 and 5 deliberately use only `CREATE`, `ALTER ... ADD COLUMN` and index/trigger creation. In particular, accepted tables are never rebuilt." Adding a `project_id` and swapping a unique index at M13 means backfilling against a database that by then holds real run history, in a schema where `evidence`, `reviews`, `acceptance_records`, `merge_observations` and others carry `_no_update` / `_no_delete` triggers (`storage.py:1178-1186`).

Today `/home/jeremy/Development/Maestro-m2-atlas-review/var/maestro.sqlite3` is 585 KB of throwaway M4 state. The index change is a near-free schema-6 migration **now**. Two real projects do exist (`/home/jeremy/Development/Foundry` and Maestro itself), so the constraint is live. D19's "run them sequentially until M13" is a legitimate answer for the *runtime* half; the *schema* half should not wait.

## 11. Unscheduled hard prerequisite for M7: neither real project has a `maestro.project.yaml`.

`project_authority.py:126,134-135` — `ProjectAuthorityLoader.load` reads `maestro.project.yaml` at the source commit and `parse_project_manifest` raises if it is absent. `find` over `/home/jeremy/Development/Foundry` and this repo returns **no manifest in either**. `project_manifest.py:184` additionally requires `authority.work_graph_path` to occur in `authority.plan_paths`, and `plan_paths` must be non-empty — so the work-graph path must be *declared in a committed manifest* before the Architect can write the file.

M7's evidence bar is "proved against a real repository, not a fixture manifest." That cannot happen until manifests are authored and committed. D19 schedules this nowhere.

## 12. Registration still takes hand-typed work items — D18 §4's rejected design is the only path that exists.

`project_onboarding.py:66-68` builds work items from `request["work_items"]`, and `project_onboarding.py:69-71` computes `source_hash = sha256(graph_projection_id + "".join(sorted(work_item_ids)))` — operator input, never project bytes. This is both the thing M7 must delete and the reason D19 §6's staleness claim is correct.

## 13. D19 §4's "pre-milestone deletion" is described wrong.

It says "remove the two self-authored writes at `development_manager.py:329`/`:334`, stop the cycle at `MergeReady`." But the **Integration** review at `:307`/`:313` is equally fabricated (`reviewer_instance="development-manager-loop-integration"`, `reviewer_role="IntegrationAgent"`). Delete only the independent review and packets pile up in `AwaitingReview` behind a review that never comes — while the durable record still asserts an Integration review by an agent that does not exist. To stop honestly, the loop must stop at **`AwaitingIntegration`**, not `MergeReady`. It is still an hour's work; the target state in the text is wrong.

---

# PROPOSED ORDER

**P0 — now, on `master`, not milestones**

1. Stop the loop fabricating reviews: stop at **`AwaitingIntegration`** (finding 13), notify. Both reviews are fabricated.
2. Correct the status record (unchanged from D19 §4 step 2).
3. **Schema 6: `resource_locks.project_id`, active-lock index unique per `(project_id, resource_key)` for `Path`/`SharedBoundary`, `FiniteResource` stays global.** *Forced position:* the migration is free against a disposable database and expensive against one holding append-only history (finding 10). Pulled out of M13.

**M6 — the wiring/orphan gate, over Maestro only.** *Forced by:* D18 §10 step 3, which explicitly precedes step 4; depends on nothing; it is the mechanical grader every later "is it real?" claim is scored by. Joined-project orphan checking is deferred and named as deferred scope, not absorbed silently.

**M7 — project manifests for Foundry and Maestro, plus the work-graph format and parser.** *Forced by:* `project_authority.py:134` (registration cannot run without a committed manifest) and `project_manifest.py:184` (`work_graph_path` must be declared inside `plan_paths`). Parser before generator: a parser makes "the Architect produced something" falsifiable. Write the specimen as Maestro's own real work graph for this round, so it is real data rather than a fixture.

**M8 — the Architect as the first real role: registration triggers a repository review that writes the work graph.** *Forced by:* D18 §10 step 4 verbatim, and by the FK chain — nothing downstream can have a packet until this exists. Includes the **role-agnostic agent invocation** (spawn a role, load its `docs/agents/` contract, cap output, return a result) built in the shape its first consumer needs (finding 5); a real `source_hash` over project bytes; and `register_project` no longer accepting hand-typed `work_items` (finding 12).

**M9 — work-graph read endpoints and the Atlas surface that renders them.** *Forced by:* finding 7 — there is no `/snapshot/work-items` or `/snapshot/graph-projections`, no `real=` wiring, and no active-work listing. Nothing can be approved before it can be displayed. This is the milestone D19 does not have and needs.

**M10 — the Architect loop: packetize, bounded fidelity rounds, stop at the Owner gate, Owner approves in Atlas.** *Forced by:* M8 (the graph) and M9 (the surface). This is also where the **configuration file** ships, because the bounded round count N is its first real value (finding 6). The Owner-approval command endpoint lands here.

**M11 — the Development Manager becomes a manager**: scheduling, restart, context allocation, model escalation, per-step instrumentation. *Forced by:* M8 and M10 (something to schedule); independent of reviewers (finding 8). The **commit/branch half of the wrapper ships here**, with the coding agent it was designed for — it saves the packet's only Initial attempt, which is a cost that exists today (finding 2).

**M12 — real reviewers**: Independent Reviewer + Integration Agent, **and the correction/acceptance defect**. *Forced by:* finding 3 — `operational_state.py:2141` rejects any acceptance whose Approve review carries `correction_number=1`, so the milestone that first produces corrections must be the milestone that fixes the dead end. The **model-shaped check set ships here**, because M12 is the first moment a bounded review round exists for it to protect. The reviewer-contract amendment (D18 §5.4.2) lands with the reviewer, not two milestones ahead of it.

**M13 — ReturnSlice.** Position unchanged from D19's M11.

**M14 — re-registration that supersedes.** *Forced by:* M8's real `source_hash` over project bytes. Unchanged from D19's M12.

**M15 — multi-project runtime**: one loop across projects, cross-project ranking, service account, GitHub App. The schema half already landed at P0.3.

**Net verdict on the interrogated claim:** D19 §8's "M6 before M7 is the load-bearing choice" is wrong on both halves. The wrapper does not apply to M7 (finding 1), and the cost it saves does not exist until M12 (finding 2). M6 as a package should be split four ways; only its orphan gate belongs first, and it belongs first for a different reason than D19 gives — because D18 §10 lists it as step 3.</result>
<usage><subagent_tokens>137757</subagent_tokens><tool_uses>37</tool_uses><duration_ms>489480</duration_ms></usage>
</task-notification>

--- OWNER MESSAGE 9 ---
<task-notification>
<task-id>ae0d2915372345c2e</task-id>
<tool-use-id>toolu_01VSXKfaNSs3CvFsA7Zbk42i</tool-use-id>
<output-file>/tmp/claude-1000/-home-jeremy-Development-Maestro/8dbc64ad-0bd4-4902-b3c1-0bf7ec9cc09d/tasks/ae0d2915372345c2e.output</output-file>
<status>completed</status>
<summary>Agent "Scope and sizing review of M6-M13" finished</summary>
<note>A task-notification fires each time this agent stops with no live background children of its own. The user can send it another message and resume it, so the same task-id may notify more than once.</note>
<result>I have the evidence I need. Writing the review.

## FINDINGS — most serious first

---

### 1. SERIOUS — The plan's largest unknown is unnamed: no model has ever completed a Maestro packet, and M7–M11 are five milestones stacked on the assumption that one can

This is the answer to question (B), and it belongs first.

D18 §2 carries the Owner's own correction as authority: **"Maestro has never built anything"** — *"Yes but the so called loop didn't develop this"*. D19 §3 re-verifies the code state at `ad614b7` and never re-states this. §10 "Open items" lists three carried items; this is not one of them.

The evidence that it is unresolved is in the code. The only agent-shaped execution path in the repository is `services/maestro/maestro/executor.py:92` `LocalQwenExecutorAdapter`, and its entire dispatch is one line:

```python
process = subprocess.Popen([self._qwen_binary, "-p", instructions, "--yolo"], cwd=..., stdout=log_file, ...)
```

One fire-and-forget prompt, no turns, no tools mediated by Maestro, no interaction. Success is judged afterwards by `retrieve_evidence` diffing HEAD against `base_commit`. Nothing in the repository records that this has ever produced an accepted packet.

Every milestone from M7 onward is "make a role real". M8's bounded fidelity rounds, M9's reviewers, M10's restart-and-escalate, M11's ReturnSlice split — all of them are machinery for *managing* agent output whose quality has never been observed once. The plan cannot be estimated at all if the answer is "qwen cannot complete a packet at this granularity," because then M8's configurable N, M10's restart threshold and M11's split path are all being tuned against an unknown distribution.

It is made worse by a hard schema bound the plan never mentions: `storage.py:854` — `correction_count INTEGER NOT NULL DEFAULT 0 CHECK(correction_count IN (0,1))`. One correction per packet, enforced by a `CHECK` constraint. D18 §11a rules that durable schema constraints stay in code and are *not* tuning knobs, so M6's configuration file cannot relax it. If a real agent needs two corrections, the loop cannot converge and the fix is a schema migration, not a config edit.

**Name it as:** whether Maestro's available executors can complete a packet to review standard at all, at what granularity, and with how many corrections. It should gate M8's parameters, not be discovered inside them. D19 §5's M6 "proved by re-hosting the **existing** qwen worker on the wrapper" is the closest the plan comes — but "re-hosting" proves the wrapper, not the worker.

---

### 2. SERIOUS — Backup and recovery is covered by no milestone in M6–M13, and it is a whole Accepted decision record with zero code

`docs/planning/decisions/m0-d07-sqlite-backup-and-recovery.md` is **Status: Accepted**. It requires nightly snapshots, snapshots before every schema migration, SHA-256 verification manifests, 21-daily/8-weekly retention, a **monthly restore into a fresh database** verifying run/packet/attempt/event/evidence/notification/wait records, durable backup-health failure records, a Slack notification on failure, and **"Atlas shows that condition live."**

Verified: zero code. `grep -riE "backup|restore|vacuum|wal_checkpoint"` over `services/maestro/maestro/*.py` returns only the words "recovery"/"recovered" used for packet redispatch (`auto_redispatch.py`, `auto_timeout.py`) — an unrelated concept. No snapshot writer, no manifest, no retention, no restore test, no drive check.

D19 mentions D07 nowhere. §5 has no milestone for it, §9's definition of done does not reference it, and §10's open items do not carry it. Meanwhile M13 §7.3 gives the service account ownership of `var/` — which is where the unbackupped database lives.

Note the compounding risk the plan creates: M13 §7.1 requires a schema change to `resource_locks`. D07 requires a snapshot **immediately before every schema migration**. That snapshot does not exist and is not scheduled.

---

### 3. SERIOUS — M10's "cloud reasoning" is one clause covering an entire unbuilt subsystem: there is no LLM client, no HTTP dependency for one, no credential consumer, and no model router

D18 §5.1 is an Owner ruling: *"The manager should use cloud reasoning for scheduling."* D19 M10 item 1 restates it and adds a `[PROPOSAL]` that the model choice "belongs in M6's configuration file, not in code." That is the whole of it.

Verified against the code:

- **No cloud model client of any kind.** `grep -rniE "anthropic|openai|claude-|gpt-|litellm|langchain|bedrock|vertex"` across `services/` and `apps/` returns only decorative strings in Atlas fixtures — `apps/atlas/src/performance/perfRecords.ts:46` hardcodes `"claude-opus-4 · hosted · ctx 200k"`, and `apps/atlas/src/shell/ActivityTab.tsx:477` renders the literal label `"openai weekly window"`. There is no client.
- **No dependency that could be one.** `services/maestro/pyproject.toml` declares exactly three runtime dependencies: `PyYAML`, `PyJWT`, `cryptography`. No `httpx`, no `requests`, no vendor SDK.
- **No credential path.** `secrets.py` has **no importer anywhere** — confirmed, `grep -rn "import.*secrets" services/maestro/maestro/*.py` returns nothing. The provider exists; nothing resolves a secret through it.
- **No model router.** D18 §11 records that control-plane §11 model routing "remains unbuilt". `execution_classes_json` is written and read by nobody (`operational_state.py:2947` writes it, no reader).

So M10 item 1 silently contains: an HTTP client dependency decision, a provider API client, an auth path from a secret reference to a live key (the first consumer `secrets.py` has ever had), a model router mapping role/risk/task-type to an execution class, rate-limit and failure handling, and cost accounting into `cost_measurement_json`. None named. This is precisely the "sudden scope" the Owner's standard bans.

It also lands identically on M10 item 4 ("model escalation") and M8 (the Architect's fidelity reviews are reasoning work too, on an unspecified model).

---

### 4. SERIOUS — M10's "per-step usage instrumentation" and "history summarised past a threshold" describe a step-based agent loop that does not exist and that no milestone builds

D19 §2 closes D18's last `[OPEN]` with an Owner ruling: per-step usage is measured, and *"Summarised after a threshold"* between steps. M10 item 5 schedules it as "Measurement only."

There are no steps to measure. `LocalQwenExecutorAdapter.submit` (`executor.py:106`) hands the model one prompt string and returns a handle; `observe` (`executor.py:121`) is `process.poll()`. Maestro never sees a turn boundary, a token count, or a message history. It cannot summarise a history it does not hold, and it cannot cap or count a step it never observes.

"Measurement only" reads as cheap. What it actually requires is replacing the one-shot subprocess with a Maestro-driven agent loop that owns the conversation — which is the largest single piece of engineering implied anywhere in M6–M13, and it is scheduled as bullet 5 of 5 in a milestone whose other four bullets are scheduling, restart, context allocation and model escalation.

Two more consequences the plan does not name:

- `record_context_usage` (`operational_state.py:2462`) and `update_context_usage` (`:2498`) have **zero non-test callers**, and `record_context_usage` validates that `context_policy_digest` matches the packet's `context_policy_json` and calls `validate_context_policy` with a `configured_context_limit` and `starting_input_tokens`. Producing those numbers requires a tokenizer or a provider usage report. Neither exists.
- `_LocalAttempt` handles live in an **in-memory dict** (`executor.py:104`, `self._attempts`). If the Development Manager process dies, every running attempt becomes unobservable and uncancellable. M10 item 2 ("restart of stopped, killed or silent workers") is scoped as restarting the *worker*; the plan never notices that the *manager's* restart orphans every handle it held.

---

### 5. SERIOUS — The notification and escalation stack (M0-D04, Accepted) is covered by no milestone: 6 of 8 required events, escalation, acknowledgement and Slack are all unowned

D18 §2 finds "notification triggers cover 2 of 8 required events; escalation never fires; acknowledgement is an unreachable state." Verified:

- `docs/planning/decisions/m0-d04-notifications-and-escalation.md` is **Accepted** and its "Required events" table lists eight rows.
- `notification_triggers.py` defines four functions (`:67` `notify_attempt_timed_out`, `:81` `notify_awaiting_architect`, `:94` `notify_coverage_not_ready`, `:111` `notify_merge_ready`). Only two are imported anywhere: `development_manager.py:64` imports `notify_coverage_not_ready, notify_merge_ready`. Two of eight, as D18 said — the other two triggers are themselves orphans.
- `escalation_at` is written literally `None` at `notification_triggers.py:59`, and the only other occurrences are the column definition (`storage.py:981`) and the write-validator field list (`operational_state.py:3131`). No reader, no scheduler.
- **Acknowledgement has no code at all.** `grep -rn "acknowledg" services/maestro/maestro/*.py` returns exactly one hit and it is a code comment (`operational_state.py:2345`). D04 §28 requires the database to store acknowledgement state.
- Slack: `notification_delivery.py:16` states it exists "to prove the real loop end-to-end before `Slack` (M4.15, blocked)". No Slack delivery exists.

M6–M13 mentions notifications exactly once: §4's pre-milestone "stop at `MergeReady` and notify" — which uses the one trigger that already works. Six missing events, escalation, acknowledgement and the Slack channel are in no milestone, no open item, and no definition of done.

This directly undercuts M8: the Architect loop **stops for Owner review**. Under D04 that is the "Owner decision/approval needed" row — an Action-needed notification with escalation on a declared timeout. Without it, M8's gate is a state in a database that nothing tells the Owner about, and D18 §8's *"there will be no terminal window eventually"* means nobody finds out.

---

### 6. SERIOUS — M6 is four deliverables that share no technical dependency. Splitting failure, and the clearest one in the plan

M6's four items:

1. The deterministic wrapper (commit, branch, output cap, model-shaped check set)
2. The configuration file (D18 §11a)
3. Role contracts actually loaded
4. The wiring/orphan gate (D18 §7.3)

Item 4 shares **nothing** with items 1–3. It is a static-analysis tool over the source tree; it never runs inside a packet, never touches the executor, never reads a role contract, and never reads the config file. It could be built first, last, or by a different worker on a different day. **Split line: item 4 is its own milestone.**

Item 3 shares nothing with item 1 either. Loading `docs/agents/*.md` and passing the text to the agent is a change to prompt assembly (`development_manager.py:180`, where `role_contract_reference` is interpolated as a filename). The wrapper is a change to what happens *after* the model's turn. They touch opposite ends of the delegation. **Split line: item 3 is its own packet at minimum.**

Item 2 is the only one with a genuine argument for co-location — the wrapper needs the check-set configured — but D19's own text concedes it is independent: "M6 moves the thresholds it needs and establishes the file; later milestones add their own values."

M6 as written is one milestone containing four independently shippable units. D19 §5.0 opens with "deliberately small, per the standing instruction to split aggressively" and then does the opposite.

**M6 latent scope.** Item 4's scope carries a bound nobody set: D18 §7.3's Owner scope is *"both Maestro itself and the products Maestro builds for others."* An orphan check over Maestro is a Python AST walk. An orphan check over an arbitrary joined project is a language-agnostic static analyser — for a project Maestro has never seen, in a language nobody has named. That is unbounded scope inside one bullet. It also has no defined verdict semantics: what does the gate do when a command has no caller *yet* because its caller is the next packet?

**M6 unknowns.** The model-shaped check set is listed by example ("leftover stubs, `TODO: implement`, placeholder headings, duplicated sections, debug output, accidentally committed generated artifacts") and D18 §5.4.2 rules that a single failure blocks. Nobody has decided what the actual check list is, and every false positive consumes a packet attempt. `lifecycle.py:18` — the Alpha wrapper D18 §5.4.2 says did this — is explicitly marked *"Controlled fixture result; it is not a real agent or subprocess result"*, so there is no prior implementation to lift.

**M6 also violates D19's own §5.0**: it names no Atlas surface. See finding 8.

---

### 7. SERIOUS — M8 "packetize all available milestones" hides the whole packet-authoring contract, which the Architect must generate and nothing validates it can

M8's scope is stated as: packetize, run bounded fidelity rounds, stop for Owner review in Atlas.

What "packetize" actually means, from `storage.py:834` — every one of these columns is `NOT NULL` and must be authored per packet:

`packet_revision`, `authority_reference`, `base_commit` (a real 40-hex commit), `expected_branch`, `role_contract_reference`, `sop_reference`, `executor_class`, `integration_route`, `reviewer_route`, `owned_paths_json`, `forbidden_paths_json`, `checks_json`, `resource_claims_json`, `context_policy_json`.

So the Architect must, per packet, choose the owned and forbidden path sets (which become the `resource_locks` keys and the review-readiness path check), author a `checks_json` of commands the target project can actually run, choose an executor class from a routing table that does not exist (finding 3), and emit a `context_policy_json` that passes `validate_context_policy`'s ordering constraints. None of this is named in M8. `base_commit NOT NULL` also means packetizing "all available milestones" up front pins every future packet to today's commit — a plan-time/run-time mismatch nobody has ruled on.

**M8 size.** Two deliverables with no shared dependency: (a) the packetizer, (b) the Owner review gate in Atlas plus the blocked-waiting-on-Architect state. The gate is an HTTP command route and a React surface; the packetizer is an agent that writes packet contracts. They meet only at a database state. **Split line: the Owner gate is its own milestone.** A third independent unit is hiding in the `[PROPOSAL]` at the end — "the Architect's own repository becomes real here."

**M8 latent scope — the Architect's own repository.** D18 §5 is an Owner quote: the Architect *"lives in it's own repo"*. D19 files this as a trailing `[PROPOSAL]` in M8. There is **no `git clone` anywhere in the repository** (`grep -rn "clone" services/maestro/maestro/*.py` → nothing). `git_repository.py` has four methods — `exact_commit`, `read_blob`, `branch_contains`, `_run` — all read-only operations against a path handed to it. There is no repo provisioning, no clone, no remote configuration, and no answer to how a Maestro process reaches a repository it does not have on disk. "Escalation to it is a handoff of facts, not a function call" describes a transport that does not exist and is not designed.

**M8 unknowns.** What a "fidelity review round" produces as a durable artifact (there is no reviews table row type for a milestone-level review — `reviews` is packet-scoped), what the bound is when N rounds elapse without convergence, and who the Architect escalates *to* when its own review fails.

---

### 8. SERIOUS — D19 §5.0 states a standing rule and then six of its own eight milestones break it

§5.0: *"Every milestone in this round ships **its own Atlas surface as part of its own definition of done**."* Stated emphatically, with the rationale that a trailing Atlas milestone is exactly how the current fixtures came to exist.

Applied to §5's own milestones:

| Milestone | Atlas surface named |
|---|---|
| M6 | **none** |
| M7 | **none** |
| M8 | yes (Owner gate, blocked-waiting-on-Architect) |
| M9 | **none** |
| M10 | **none** |
| M11 | **none** |
| M12 | yes (§6.1: blocked-registration state) |
| M13 | **none** |

Six of eight. The document commits the same failure it diagnoses, in the same section that diagnoses it. M10 in particular introduces scheduling decisions, restarts, model escalations and context allocations — every one of them an operator-visible state — and names no surface.

There is also a structural obstacle §5.0 does not acknowledge. `apps/atlas/src/shell/MobileShell.tsx:10` declares `export type MobileShellTab = "now" | "chat" | "plan" | "activity"` — four hardcoded tabs, no router anywhere in the app (`grep -rn "Router\|route" apps/atlas/src/shell/MobileShell.tsx` → nothing). Eight milestones adding surfaces into four fixed tabs, **while M5 is concurrently renaming and re-navigating those same four tabs**, is a direct collision on the same files. §5.0's "M5 is unaffected... This rule adds surfaces for new states; it does not redefine M5" asserts an independence that the file layout does not permit.

---

### 9. SERIOUS — M7 must write into the project's repository, but the identity that permits it is M13, six milestones later

D18 §4 is an Owner ruling: registration triggers an Architect review of the repository **that produces the work-graph file**. `docs/planning/agent-workforce-control-plane.md:39` places the approved work graph in the **joined project repository**, and `:45` states *"There must never be two independent writable truths for one fact."* So M7's Architect writes a file into someone else's repo — which under D18 §9's discipline means a branch, a commit and a pull request.

M13 §7.3 is where a GitHub App identity is delivered, and D19 §8 puts M13 last. M7 therefore has no identity to commit under. D19 never notices.

**M7 latent scope — the work-graph format has never been specified, and M7 does not name specifying it.** Verified: `work_graph_path` appears only in `project_manifest.py` (lines 27, 58, 125, 181) as a validated string that must occur in `plan_paths`. `docs/schemas/maestro-project-v1.schema.json:28` types it as `{"$ref": "#/$defs/repositoryPath"}` — a path, nothing more. `find . -iname "*work*graph*"` → **no file**. D18 §4 says "The work-graph parser and generator are both unbuilt; both are required" and M7 repeats that. Neither names the third thing: **a format specification**, which is what both the generator and the parser are written against and which is the estimation blocker for both.

**M7 latent scope — registration's real input contract changes.** `cli.py:53` — `register-project` takes `--request`, "closed local registration request JSON", and `project_onboarding.py:66` reads work items straight out of `request["work_items"]`. M7 replaces a JSON file with an agent run. Also unaddressed: `cli.py:49` — `discover-project --overlay` is documented as *"JSON of the Architect's own answers for leaves discovery cannot observe"*, i.e. today a human hand-writes the Architect's answers. If the Architect is real, that file is its output, not its input. D19 does not mention the overlay at all.

**M7 size.** At least three independently shippable units: (a) specify the work-graph format; (b) the parser (format → `work_items` rows); (c) the generator (a real Architect agent producing the file). (b) depends only on (a) and can be built and tested against a hand-written example before any agent exists. (c) additionally depends on the whole of M6. **Split line: parser before generator.** Milestone naming consistency (`M4.01`/`M4.01A`) is a fourth, wholly independent unit — a string convention with no dependency on any of the above.

**M7 unknowns.** Whether the Architect writes the work graph into the project repo or into Maestro's store (control-plane §45 forbids the latter becoming a second writable truth); whether the Architect is the same executor class as a coding agent; and whether a repository can be re-reviewed without re-registering (which is M12, scheduled after).

---

### 10. MODERATE — M9 bundles two roles that share nothing, and one of those roles bundles two functions that share nothing

M9 = Independent Reviewer + Integration Agent.

- The Independent Reviewer reads a diff and records a review result. It writes to `reviews`.
- The Integration Agent, per D18 §6 and D19 M9, does **two** things: it **wires the part into the product** (it changes code, produces a branch, and per control-plane §234 its result then goes to a *different* Independent Reviewer), and it performs an **independent review that the parts align**.

These are three deliverables in one milestone. The Reviewer and the Integrator share only the fact that both are spawned agents — which is M6's machinery, not M9's. **Split lines: (a) Independent Reviewer; (b) Integration Agent's wiring function; (c) Integration Agent's alignment review.** (b) is the only one of the three that writes code, and it is the one with real design content (integration branch strategy, conflict handling, `Assemble` routing).

**M9 latent scope.** D19 §4 says M9 "permanently replaces §4's pre-milestone stop-and-notify," but the code being replaced does more than record a review. `development_manager.py:414` calls `accept_packet(required_authority="Owner", delegation="development-manager-loop")` and `:425` calls `observe_merge`. Deleting the self-review (§4 step 1) leaves those two writes unowned. M9 gives the review to a reviewer; **nothing in M6–M13 gives Owner acceptance to the Owner.** M8 builds an Owner gate for the *plan*; no milestone builds one for *acceptance*. That is a live gap in the exact defect D18 exists to fix.

**M9 unknowns.** How reviewer independence is enforced once reviewers are real — today the store's independence check is satisfied by the literal string `"development-manager-loop-independent"`. Nobody has decided what an actor identity is such that "not the author" is checkable.

---

### 11. MODERATE — M11's ReturnSlice split has no write path to `work_items`, and the plan lists only packet-level vocabulary

M11 splits a packet into two, "one eligible now, one scheduled into a later milestone." `packets.work_item_id` is `NOT NULL REFERENCES work_items(work_item_id)` (`storage.py:837`), and `UNIQUE(run_id, work_item_id, packet_revision)` (`:858`). So a split needs new `work_items` rows, and the superseded original needs `planning_state` moved from `'Active'` to `'Superseded'` or `'NeedsReplan'` (`storage.py:804`).

Verified: **`grep -rn "UPDATE work_items" services/maestro --include=*.py` returns nothing.** There is no command anywhere that changes a work item's planning state, and the graph is insert-only (D18 §2). The `'NeedsReplan'` and `'Superseded'` planning states are unreachable by construction, exactly as the graph states are.

M11's "existing vocabulary this wires up" lists `ReturnSlice`, `Assemble`, `NeedsReplan` and `blocker_payload_json` — all packet- and review-level. The work-item layer the split actually lands on is not mentioned. The "scheduled into a later milestone" half additionally needs a `milestone_ref` for a milestone that does not exist in the graph, with no rule for creating one.

**M11 size.** Two independent halves: (a) the *raising* path — the coding agent or reviewer records a `ReturnSlice`/`blocker_payload_json` and the packet reaches `AwaitingArchitect` (this is a state-machine change, buildable and testable alone); (b) the *resolving* path — the Architect splits, budgets reset, dependents release. They meet at one state. **Split line at `AwaitingArchitect`.**

---

### 12. MODERATE — M12 supersedes the binding but never mentions the graph projection, which carries the same unique-active constraint and the same missing UPDATE

D19 §6 correctly identifies `project_bindings.binding_revision`/`superseded_at` and that no `UPDATE project_bindings` exists. It misses the second half.

`storage.py:1103` — `CREATE UNIQUE INDEX one_active_graph_per_project ON graph_projections(project_id) WHERE state='Active'`. Re-registration produces a new graph projection. The old one **must** leave `'Active'` or the insert fails on the index. And `grep -rn "UPDATE graph_projections"` returns **nothing** — same defect as the binding, in a table D19 §6 does not name. §6's item 4 ("Staleness becomes reachable") gestures at graph states but frames it as detection, not as the write path re-registration structurally requires.

D19 §6 item 1's diagnosis is otherwise correct and I verified it: `project_onboarding.py:68` computes `source_hash = sha256(graph_projection_id + sorted(work_item_ids))` — entirely from the operator's own request JSON, never from repository bytes.

**M12 size.** Three independent units: (a) a real `source_hash` over project bytes (belongs with M7, which is what reads those bytes — arguably it is M7 scope misfiled into M12); (b) supersession writes for both `project_bindings` and `graph_projections`; (c) the reconciling re-projection diff. (a) has no dependency on (b) or (c).

**M12 unknowns.** §6.1's Owner ruling (refuse registration during active work) is settled — that is *not* an unknown, and D19 correctly closes it. What is unknown: whether re-projection diffs by `architecture_node_id` (the `UNIQUE(graph_projection_id, architecture_node_id)` key) or by content, which determines whether a renamed work item reads as "changed" or as "deleted plus new".

---

### 13. MODERATE — M13's `resource_locks` change is not additive, and the migration machinery's stated invariant forbids it

D19 §7.1 proposes adding `project_id` to `resource_locks` and making the active index unique per `(project_id, resource_key)`.

`storage.py:422` documents the migration contract explicitly: *"Versions 4 and 5 deliberately use only `CREATE`, `ALTER ... ADD COLUMN` and index/trigger creation. In particular, **accepted tables are never rebuilt**: SQLite can therefore roll an injected DDL failure back without copying or rewriting any accepted row."*

`ALTER TABLE ... ADD COLUMN project_id TEXT NOT NULL` is not legal against existing rows without a default; a genuinely `NOT NULL` `project_id` needs a table rebuild, which the migration design deliberately forbids. Replacing `one_active_resource_key` also requires a `DROP INDEX`, which is not in the allowed set either. `supported_histories` at `storage.py:451` is a hardcoded tuple that a version 6 must extend.

So M13 §7.1 forces a decision nobody has made: relax the never-rebuild invariant (and lose the rollback property it buys), or make the column nullable and enforce project scoping in Python (and lose the database-level guarantee). One bullet, "Add `project_id` to `resource_locks`", contains it.

**M13 size.** Three unrelated deliverables: (a) the lock schema change; (b) cross-project scheduling in M10's scheduler; (c) the Linux service account and GitHub App identity. (c) shares nothing with (a) or (b) — it is provisioning and credentials, not code. **Split line: (c) is its own milestone**, and per finding 9 it is needed by M7, not after M12.

**M13 latent scope.** The GitHub App identity requires: `secrets.py` gaining its first consumer; a GitHub App registered and installed on each joined project; and `github_client.py`'s two wrapper functions in `real_discovery.py:33`/`:42` gaining the callers they have never had. D19 §7.3 correctly reports the dead-code finding but scopes the fix as "gives the Manager a real identity" — one sentence.

---

### 14. MODERATE — Two of D18 §2's six string-literal roles are mapped to no milestone

D18 §2: *"Six of nine designed roles exist only as string literals — Project Architect, Integration Agent, Independent Reviewer, QA/Murphy, Coordinator/scheduler, Decision Fidelity Reviewer."*

- Project Architect → M7, M8 ✓
- Integration Agent → M9 ✓
- Independent Reviewer → M9 ✓
- Coordinator/scheduler → M10 ✓
- **QA/Murphy → nothing.** `docs/agents/qa-agent.md` exists and is opened by no code.
- **Decision Fidelity Reviewer → nothing.** `docs/agents/decision-fidelity-reviewer.md` exists and is opened by no code.

Four of six. D19 never says these two are deferred, backlogged, or out of scope — they simply do not appear. That is a silent drop, not a scheduling decision. It is worth noting that the Decision Fidelity Reviewer is the role that would have caught the blurred-provenance failure D18 §1 says a fidelity review caught by hand, and QA/Murphy is the role that would independently break a delivered feature — the one check missing from a round whose entire premise is "schema and tests are not delivery."

---

### 15. MODERATE — Owner approval in Atlas has no authentication, which reproduces D18's core defect at the HTTP layer

M8 stops for Owner review "presented in Atlas," and the Owner approves there. D18 §2's headline finding is that the loop *"grants itself `required_authority="Owner"`."*

The write path exists — I checked, and the prompt's hypothesis that it might not is wrong: `read_api.py:1007` declares four POST command routes (`/command/resolve-decision`, `/command/dispatch-correction`, `/command/resolve-crash`, `/command/redispatch-crash`), and `_route` at `:1049` admits POST for them. The API is not read-only.

But there is no authentication of any kind. `read_api.py:30` restricts binding to `{"127.0.0.1", "::1", "localhost"}` and `:355` notes the CORS policy "carries no cookies/credentials." The `actor` field arrives in the request envelope, and `_validate_command_envelope` (`:465`) checks only its JSON shape. Anything that can reach loopback can POST `actor: {…"Owner"…}`.

Loopback-only is defensible today because the only thing on that box is Maestro. It stops being defensible when M13 §7.3 introduces a **service account** running the Development Manager on the same host — a second principal on loopback whose whole purpose is to act non-interactively, POSTing to the same unauthenticated port that grants Owner authority. M13 does not mention it and M8 does not mention it.

---

### 16. MINOR — The four existing Atlas operator commands stay unreachable, and no milestone owns them

D18 §2: *"All four operator commands are unreachable from the UI."* Verified precisely:

- `OwnerDecisionCard.tsx:77` — `if (!real || pendingIndex !== null) return;`. Every click is a no-op unless a `real` prop is supplied.
- `NowTab.tsx:202` — `{state.isBlocked ? &lt;OwnerDecisionCard /&gt; : null}`. Rendered with **no `real` prop**.
- `PacketThread.tsx:153` — `&lt;CrashCard /&gt;`, likewise with no `real` prop, and only when `systemState === "crashed"`.
- `App.tsx:29` — `return isMobile ? &lt;MobileShell /&gt; : &lt;DesktopShell /&gt;`. **No `systemState` prop is ever passed**, so it defaults to `"normal"` in both shells (`NowTab.tsx:115`, `DesktopShell.tsx:226`). `"crashed"`, `"empty"` and the disconnect states are unreachable in production, so `CrashCard` never renders at all.

M5's roadmap covers de-fixturing Plan, Now, Events, History and Agents — I checked all seven items. It does **not** cover wiring the `real` props, deriving `systemState` from the read API, the hardcoded cost strip, or the desktop Performance tab. D19 §5.0 explicitly limits itself to "surfaces for new states." So four already-built POST routes, their two already-built UI cards, and the entire crash/disconnect/empty state family are owned by no milestone in either plan.

Related staleness the plan's §3 re-verification should have caught: `docs/planning/m5-atlas-navigation-roadmap.md:63` asserts that claiming a materialized packet "has no command anywhere yet," while D19 §3 lists `claim-packet` among the ten CLI commands (`cli.py:65`). D19 §5.0 asserts "M5 is unaffected" without reconciling M5's own stale premises.

---

### 17. MINOR — M12 and M13 are titled "Loose end 1" and "Loose end 2" in §5, with their content in §6 and §7

§5's milestone list gives M12 and M13 two lines each, deferring to sections elsewhere in the document. Every other milestone is scoped in place. A reader assessing the round's size from §5 sees six milestones' worth of scope and two pointers. Given that §7's content includes a schema migration, cross-project scheduling and an entire identity/provisioning story (finding 13), the presentation understates the round.

---

### 18. MINOR — Atlas has no way to run outside a terminal, which the whole round depends on

`apps/atlas/package.json` scripts: `vite`, `vite build`, `tsc --noEmit`, `eslint`, `vitest run`. There is no host — `read_api.py` serves JSON only and no static files, there is no Electron shell, no installed entry point, and D18 §11's packaging layout (`/usr/local/lib/maestro/&lt;version&gt;/`) is unbuilt.

D18 §8 is an Owner statement — *"there will be no terminal window eventually"* — and D19 §5.0 turns it into a per-milestone rule. Today the only way to see Atlas is `npm run dev` in a terminal. Nothing in M6–M13 changes that, and D19 §10's carried-forward item is the *runbook*, not the host.

---

## Per-milestone summary

| | Splittable into | Biggest unnamed requirement | Blocking unknown |
|---|---|---|---|
| **M6** | 4 (wrapper / config file / contract loading / orphan gate — gate and contracts share nothing with the wrapper) | Orphan gate over arbitrary joined projects in unknown languages | The actual model-shaped check list; gate verdict semantics |
| **M7** | 4 (format spec / parser / generator / naming) | A work-graph **format specification**; write identity into the project repo (M13); the `discover-project --overlay` inversion | Where the work graph lives vs. control-plane §45's single-writable-truth rule |
| **M8** | 3 (packetizer / Owner gate + Atlas / Architect repo) | The full 14-field packet contract the Architect must author; repo provisioning with no `git clone` in the codebase | Model behind the fidelity reviews (see finding 3); what a milestone-level review record *is* |
| **M9** | 3 (reviewer / integrator-wires / integrator-reviews) | Owner **acceptance** is orphaned when §4 deletes the self-approval | How actor independence is checkable once actors are real |
| **M10** | 5 (scheduling / restart / context alloc / model escalation / instrumentation — restart shares nothing with scheduling) | The entire cloud LLM stack; a step-based agent loop that does not exist | Whether the one-shot `qwen -p` executor is replaced or extended |
| **M11** | 2 (raise path / resolve path, split at `AwaitingArchitect`) | No `UPDATE work_items` path exists; `milestone_ref` creation for the deferred half | `correction_count CHECK(0,1)` vs. fresh budgets on split packets |
| **M12** | 3 (real source_hash / supersession writes / reconciling diff) | `graph_projections` supersession and `one_active_graph_per_project` | Diff key: node id or content |
| **M13** | 3 (lock schema / cross-project scheduling / service account + GitHub App) | Non-additive migration vs. the never-rebuild invariant; `secrets.py`'s first consumer | Whether `NOT NULL project_id` is worth relaxing the rollback property |

---

## (A) D18 §2 findings, mapped exhaustively

| D18 §2 finding | Milestone |
|---|---|
| Loop approves its own work and merges it | §4 pre-milestone step 1; permanently M9 — **but Owner acceptance and `observe_merge` are orphaned** (finding 10) |
| **[OWNER] Maestro has never built anything** | **nothing** — and unnamed as a risk (finding 1) |
| Project Architect a string literal | M7, M8 |
| Integration Agent a string literal | M9 |
| Independent Reviewer a string literal | M9 |
| **QA/Murphy a string literal** | **nothing** |
| Coordinator/scheduler a string literal | M10 |
| **Decision Fidelity Reviewer a string literal** | **nothing** |
| `docs/agents/` contracts never opened | M6 item 3 (the five specialist overlays are not distinguished) |
| Nothing reads the work graph; no parser, no format | M7 — parser and generator named, **format spec not** |
| Five decorative fields | M10 item 1 |
| Re-projection impossible; `source_hash` from operator input | M12 — **`graph_projections` supersession missed** |
| Atlas: 3 of 4 mobile tabs fixtures | M5 (items 1, 4, 5) |
| Atlas: `systemState` never derived; crash/disconnect/empty unreachable | **nothing** |
| Atlas: desktop Performance/Agents/History placeholders | Agents/History → M5; **Performance → nothing** |
| **Atlas: four operator commands unreachable from UI** | **nothing** |
| Atlas: cost strip hardcoded `61%/14%/5%/80%` | **nothing** |
| **Backup/recovery is zero code (M0-D07 Accepted)** | **nothing** |
| Context/token/cost stack schema-only | M10 item 5 — **partial**: per-step usage only; `cost_measurement_json`, preflight and weekly-window reconciliation unowned |
| **Escalation never fires (`escalation_at` written NULL, read by nobody)** | **nothing** |
| **Acknowledgement is an unreachable state** | **nothing** (zero code exists — one comment) |
| **Notification triggers cover 2 of 8 required events** | **nothing** |
| GitHub API integration is dead code | M13 §7.3 |
| **Secrets have no consumer** | M13 §7.3 only implicitly — never named; and M10's cloud reasoning needs it first |
| Stopped/killed worker not reported; `record_worker_progress` uncalled | M10 item 2 (and M5 item 3 surfaces it) |

**Nine findings map to nothing**, and three of them — backup/recovery, escalation, and notification coverage — are requirements of two *Accepted* decision records (M0-D07, M0-D04) that D19 does not cite once.

---

## (B) The biggest single unknown

**No.** It is not named anywhere in D19 — not in §3's re-verification, not in any milestone, not in §10's open items.

It is: **whether any executor available to Maestro can actually complete a packet to review standard**, at what granularity, and within the one correction the schema permits (`storage.py:854`). D18 §2 records the Owner's own statement that Maestro has never built anything; the only executor in the codebase is a single `qwen -p ... --yolo` subprocess (`executor.py:112`); and M8's review-round bound, M10's restart-and-escalate threshold, M11's split path and the whole of §9's definition of done are all parameters of a distribution nobody has observed a single sample from.

D19 §9 says a milestone is complete only when "a real caller in a real path" exists. That standard tests whether Maestro's *code* runs. It does not test whether Maestro's *agents work* — which is the thing eight milestones are being built to orchestrate.</result>
<usage><subagent_tokens>123158</subagent_tokens><tool_uses>37</tool_uses><duration_ms>524454</duration_ms></usage>
</task-notification>

--- OWNER MESSAGE 10 ---
This to much for today upload it to master merge and do several independent fidelity review to make sure all this conversation context gob updates
```

---

## The Owner's answers to the §5.3 question

M0-D18 §5.3 (per-step reasoning budget enforcement) was its last `[OPEN]` item.
It was put to the Owner as four multiple-choice questions. The raw tool result,
carrying the Owner's selected answers verbatim:

```
"The user answered: \"\u00a75.3(a) \u2014 should the reasoning budget be capped per step within an attempt?\"=\"Let\u2019s just collect for research and understanding so we know what the numbers actually represent\", \"\u00a75.3(b) \u2014 should dispatch be refused at preflight when the packet's context does not fit the configured minimum?\"=\"Out of scope because of question 1\", \"\u00a75.3(c) \u2014 what happens when a running attempt crosses the checkpoint remaining-token boundary?\"=\"Out of scope\", \"\u00a75.3(d) \u2014 between steps of one attempt, is the history re-sent whole or summarised?\"=\"Summarised after a threshold\". Read the answers carefully \u2014 they may request clarification, changes, or that you not proceed \u2014 and follow what they actually say."
```

These four answers are quoted in M0-D19 §2 and close M0-D18 §5.3.
M0-D19 §2.1 records that the assistant's costing of the resulting work was
wrong, and that the ruling stands regardless.
