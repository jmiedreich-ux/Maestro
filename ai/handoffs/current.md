# Maestro Repository Handoff

## Start here

- [Repository working rules](../../AGENTS.md) and [additional agent instructions](../../CLAUDE.md).
- [Project overview](../../docs/project-overview.md) — authoritative source entry and current-state evidence.
- [Architecture](../../docs/architecture.md) — system behavior and remaining mechanisms.
- [Runtime Service declaration](../../docs/milestones/runtime-service-milestones.md), [CLI declaration](../../docs/milestones/cli-milestones.md), and [registration declaration](../../docs/milestones/registration-milestones.md).
- [Architecture-loop declaration](../../docs/milestones/architecture-loop-milestones.md).
- [Execution declaration](../../docs/milestones/execution-milestones.md).
- [Planning Guide and templates](../../docs/planning-guide/README.md).
- [Maestro Project Architect — Software Architecture Role](../../docs/agents/architecture-agent.md).
- [Independent Fidelity Reviewer](../../docs/agents/decision-fidelity-reviewer.md).

## Where the discussion paused

The missing Execution project milestone declaration is recorded in [Execution](../../docs/milestones/execution-milestones.md), with its source entry and current-state boundary in the project overview. See [Execution delivery milestone checkpoint](#execution-delivery-milestone-checkpoint). Earlier statements that an Execution delivery declaration is absent are historical; implementation remains unverified.

Milestone review assignment, correction routing and limits, dependency readiness, automatic continuation and automatic completion are now recorded. See [milestone review and execution completion checkpoint](#milestone-review-and-execution-completion-checkpoint). Earlier unresolved statements on these specific decisions are superseded; remaining technical contracts are identified there.

Today's Execution conversation has now received an independent decision-fidelity review against a frozen master snapshot. No gaps were found within the recorded coverage of ten journeys; no source corrections were required. See [independent Execution fidelity review](#independent-execution-fidelity-review) for coverage and limits. Architectural completeness and runtime behavior were not certified.

Independent packet review, persistent Integration Manager authority, FIFO integration and development-milestone branching/promotion are now documented. See [integration and milestone delivery checkpoint](#integration-and-milestone-delivery-checkpoint). Earlier statements that all merge or implementation-review authority is undecided are superseded within this agreed scope. Current documentation changes still go directly to master.

The follow-up agreements on Owner-selected work disposition, normal-lifecycle completion, specialist review and configured backup agents are saved. See [architectural-support checkpoint](#architectural-support-checkpoint). Earlier unresolved notes on those subjects are superseded by this checkpoint; general Execution lifecycle and delivery policy remain unfinished.

Execution design resumed after the earlier check and is now paused for a short break. The agreed initiation, Development Manager work planning and architectural-support discussion is saved below. See [Execution design checkpoint](#execution-design-checkpoint). The earlier [pre-Execution check](#pause-before-execution-design) remains historical coverage.

The remaining smaller third-party review items were checked and corrected where applicable. See [consistency cleanup](#consistency-cleanup). GitHub App credential verification remains deferred; this cleanup is not a full readiness review.

Registration's effective configuration and publication retry binding are now specified. See [registration configuration correction](#registration-configuration-correction).

The schema installation decision is documented and the architecture-loop configuration schema now selects `architecture-loop@1` — Architecture-loop validation bundle, version 1. See [schema installation correction](#schema-installation-correction). This is an installation contract, not an installation performed on the AI box.

The registration-reference mismatch is corrected in [candidate publication](../../docs/architecture.md#candidate-publication) and the shared `registrationRef` definition in [the schema](../../docs/schemas/architecture-loop.schema.json). Registration produces the six-field package reference; architecture consumes it unchanged. All fourteen registration-reference schema properties now use that definition; generic file references remain separate.

The four recent agreements are incorporated: both role selections are collected at registration intake; SQLite has service-owned writes; process settings use a matching nested layout with separate budgets; and the specialist template uses the required role headings. See [the agreement incorporation record](#agreed-foundation-corrections). GitHub App credential verification is deferred until the local machine is available; the reported local secret file's location and service binding remain unverified.

Source and publication selection is now specified in [Architecture](../../docs/architecture.md#source-and-publication-selection), with delivery evidence in the [registration declaration](../../docs/milestones/registration-milestones.md). The architecture owns the rule; the declaration references it. This is a documentation correction, not implemented registration behavior.

Initial intake pins a resolved source commit and records an authorized publication branch. Re-registration resolves its selected source again; recovery retains saved selections; the architecture loop inherits the confirmed baseline and destination. Existing master-only policy, confirmation authority and review budgets remain unchanged. See [the correction record](#source-selection-correction) for scope and verification.

Installed schema resolution is defined in [installed validation schemas](../../docs/architecture.md#installed-validation-schemas). Registration process-definition and publication-operation recovery-limit bindings are now documented; installation and runtime verification remain development work; GitHub App/local-secret verification waits for the local machine. The registration-reference conversion issue is superseded by the shared-reference correction. The historical validation below describes earlier frozen snapshots; its source/destination omission is superseded by this correction, not by a blanket readiness claim.

The documentation-review procedure is now defined in the [shared review method](../../skills/project-architecture-workshop/references/reviews.md), with record fields in [workshop state](../../skills/project-architecture-workshop/references/workshop-state.md#review-coverage-record). [AGENTS.md](../../AGENTS.md#cross-document-alignment) defines Maestro's journey scope; the [reviewer role](../../docs/agents/decision-fidelity-reviewer.md#inputs-and-independence) applies the method within unchanged authority. It separates fidelity, completeness and consistency, requires independent inputs and per-journey evidence, and distinguishes full coverage from targeted corrections. Existing review limits and the no-standalone-report rule remain in effect.

Blind full completeness and consistency passes, followed by one targeted selection-evidence correction check, surfaced the six requested benchmark subjects. The first full passes missed reviewer-input collection; the method and coverage fields were strengthened, and the targeted check found it independently. [Coverage, limits and disposition](#review-method-validation) are retained below. Existing review bounds were preserved. The source/destination disposition is updated by the later correction above; the later correction records distinguish resolved subjects from remaining gaps.

The reusable [Project Architecture Workshop skill](../../skills/project-architecture-workshop/SKILL.md) is packaged with a generalized Planning Guide, templates, durable workshop state and bounded independent-review instructions. It is intended for new or existing projects, not reproduction of Maestro's design. [Installation instructions](../../skills/project-architecture-workshop/INSTALL.md) cover Codex and Claude Code. The package is committed, not installed into the owner's machines. No general Execution design was added by creating the skill.

Shared agent performance and context management are now defined in [Architecture](../../docs/architecture.md#agent-performance-and-context-management) and covered by the runtime, CLI, registration and architecture-loop declarations. Defaults warn at 75% context, hand off at 85%, and resume below 70%. Every supported runtime uses the same capacity classification; the planned Qwen execution adapter must apply it without penalizing context exhaustion. Qwen is now the primary Execution coder in the design, while its transport remains unspecified and registration/architecture-loop tool selections are unchanged. Persistent sessions retain occupancy across runs. Capacity continuation preserves verified work and remaining active-time budget without consuming failure/correction/review allowances. Adapter capability verification remains implementation work; this does not select Qwen for registration or change exact model choices.

The pre-execution gap closures define stable saved finding references, the fixed architecture `decisions.json` snapshot, typed Owner decisions for one extra review/correction attempt, per-run deadlines with separate next-run duration exceptions, and the local Owner credential boundary. These contracts remain recorded; the validation below identifies unresolved cross-document gaps. SQL backup and restore are explicitly out of scope; the contradictory backup procedure is removed. Ordinary restart and recorded-operation recovery remain included.

The architecture-loop agreements are saved in [Architecture](../../docs/architecture.md#architecture-loop) and the [architecture-loop declaration](../../docs/milestones/architecture-loop-milestones.md).

Settled behavior includes `/architecture start` and `/architecture`, selected-project and idle-only entry, exact tool/model selection, persistent-session replacement from verified records, active-run limits, fixed output names and paths, manifest hashes, separate working/confirmed references, stale-data rejection, targeted review, exact-version confirmation, interrupted-operation recovery, cancellation/restart without budget resets, and later-registration invalidation.

Specialist roles use `role-<role-title>.md` beside source, with assigned `context.md` and optional `memory.md`. The architect owns the role and starting context; specialists maintain verified knowledge without changing authority or overwriting a newer file. Wrapper errors return to the architect for bounded technical correction before independent review.

Session continuation, active/waiting mapping, assignment/response and API shapes, saved-record schemas, policy bindings, and canonical hashing are now defined. The schema bundle is `docs/schemas/architecture-loop.schema.json`. Replanning occurs only after confirmed re-registration and a manual architecture-loop start; there is no independent trigger or separate replanning-design task.

Earlier targeted rechecks did not establish full architectural completeness. Documentation readiness must be assessed using the recorded coverage required by the updated review method.

The review-method validation below is historical evidence for its frozen snapshots. Later corrections have their own linked records; live implementation evidence remains separate.

No implementation, runtime configuration installation, or live AI box verification has been performed. Those belong to development. Continue directly on `master` and retain no separate review reports.

## Milestone review and execution completion checkpoint

The Owner agreed the following after the independent Execution fidelity review:

- A fresh Independent Implementation Reviewer session assesses the whole milestone branch and its connected outcomes. It cannot have authored or integrated the reviewed code; Integration prepares evidence without approving its own work.
- The architect assesses failed milestone findings: Integration corrects implementation defects, the architect defines bounded packets for missing in-scope work and the Development Manager schedules them, or the issue follows re-registration and work disposition.
- Correction review covers named corrections and their effects, retaining valid coverage of unchanged work. Wider checks require an explained impact.
- Milestone review has a configurable maximum of two completed rounds by default. Remaining blocking findings go to the Owner through the CLI with the architect's recommendation; the milestone stays unmerged. Non-blocking observations neither prevent merge nor require another round. Sessions and reviewer changes do not reset the budget.
- Execution continues automatically across eligible confirmed milestones. Unrelated eligible work continues when another milestone is blocked, subject to stop or finish-current-work instructions.
- Failed milestone outcomes block new dependent starts; running affected work follows the existing disposition process.
- Approved, integrated packets may satisfy dependencies before their milestone finishes. The architect explicitly marks dependencies requiring completed milestones.
- Once all authorized milestones are merged and required checks pass, Execution closes automatically with a CLI completion summary and no additional Owner approval.

Behavior is authoritative in [milestone outcome review](../../docs/architecture.md#milestone-outcome-review), [dependency readiness and automatic continuation](../../docs/architecture.md#dependency-readiness-and-automatic-continuation) and [authorized merges](../../docs/architecture.md#authorized-integration-merges). The reviewer, architect, Development Manager and Integration Manager role files reference those rules.

Routine elaborations preserve service ownership: exact result binding for dependencies, recorded correction supplements instead of silently rewriting the confirmed breakdown, saved milestone review counts, and closure checks against unresolved required work. These details were authored within delegated technical authority; they are not represented as individually approved Owner choices.

### Validation and limits

This update is self-checked against the conversation from the agreement on fresh milestone review through automatic completion and packet-level dependencies. Changed files: architecture and the four affected role files, plus this handoff. Checks covered controlling decisions, correction authority, preserved packet/integration budgets, stale unresolved wording and local heading links. No independent review was performed on this update; the earlier independent pass applies only to its recorded snapshot. This is an interim design checkpoint, not a declaration of complete or operationally verified sources.

Reviewer model selection, the milestone configuration key, machine-readable review/completion records, correction-supplement activation, and cross-milestone source-delivery mechanics remain open technical details. Packet/integration review limits and remaining general Execution policy are not supplied by the milestone limit. The proposed requirement to incorporate current master before every milestone merge was not explicitly accepted; the existing changed-target reconciliation rule remains authoritative.

## Independent Execution fidelity review

**Result: pass.** Reviewer `/root/today_execution_fidelity` found no gaps within the recorded decision-fidelity coverage and returned no blocking or non-blocking findings. No correction or second round was required. This does not establish architectural completeness or operational readiness.

| Review field | Recorded value |
|---|---|
| Identity and subject | `execution-conversation-fidelity-20260916-round1` — 2026-09-16 Execution conversation fidelity |
| Pass and mode | Decision fidelity; full within today's selected conversation scope; no parent review |
| Budget | `2026-09-16 Execution conversation fidelity`; round 1 of maximum 2; first pass ends this review. Earlier pre-execution completeness/consistency budgets remain unchanged. |
| Coverage and consumption | Coverage complete: true; round consumed: true |
| Reviewer | `/root/today_execution_fidelity`; separate agent context; host session identifier unavailable |
| Independence | Reviewer authored/corrected none of the documents and reported no prohibited-input exposure. Received original dialogue evidence, scope, instructions and frozen source packet, not the author's verdict, suspected defects or previous findings. |
| Repository snapshot | `jmiedreich-ux/Maestro` at `8309144b856c4d88fa3db618850471800ceabb7a` |
| Packet SHA-256 | `96863d77bec6e0a0bd5fb92c81c70ed30a7d92ac7c5284d9432a2e28bbe955f5` |
| Evidence SHA-256 | `4b94f5aaeb3214f66b494c3495ff66a07b88a0839d98f2bb46c41f9049e6c9b6`; chronological original-dialogue excerpt selection from today's hooks discussion through milestone branching and this review request |
| Findings and corrections | None; correction references empty; no invalidating changes to the reviewed design during this pass |
| Publication verification | Parent fetched the frozen files from GitHub and confirmed master still matched the snapshot before recording this result. The reviewer verified all 16 packet file hashes, not remote Git independently. |

### Input filtering and evidence limits

The handoff packet retained the unchanged technical passages from **Integration and milestone delivery checkpoint** before **Validation and remaining design**, **Architectural-support checkpoint** before **Validation**, and **Execution design checkpoint** before **Validation coverage and limits**, including **Resume here**. All other handoff passages were excluded to remove earlier findings, self-check outcomes, readiness conclusions and unrelated historical review material. Within the retained material, the sentence claiming role documents already agreed with the flow and the **Decisions preserved** heading were also removed. Technical statements and accepted deferrals remained available for checking.

Temporary packet preparation added one final newline to each unfiltered source document. The parent verified that removing that byte reproduced each Git blob hash; packet hashes describe the actual reviewed bytes. The reviewer was told this normalization and reported it. No other changes were made to unfiltered documents. The filtered handoff SHA-256 was `4c439ce67b72a94c8ef11dd44b8d16d92ce22bdfd0cef17537d88d7072e4ba06`.

Original evidence consisted of the available dialogue excerpts, with speaker labels, acceptance turns, corrections and standing Owner excerpts. Tool logs, save reports, review conclusions and redundant acknowledgments were omitted. Exact message timestamps were unavailable. Source evidence remains the conversation; no raw transcript or standalone review report is added to the repository.

Examples of controlling Owner evidence retained: “the current work should be allowed to finish through the natural life cycle”; “the integration manager is the 'code' manager where the development manager is the 'process' manager”; “work packet is complete, goes to indepent review cycle, once approved, goes to the intergration agent”; “first in, first out queueu only one at a time”; and milestone merge “I don't need to approve that”. The reviewer also received accepted assistant proposals with their agreement/correction turns, rather than assuming proposals were decisions.

### Sources actually examined

At the frozen commit: AGENTS.md, CLAUDE.md, project overview, role index, Project Architect, common coding instructions, Decision Fidelity Reviewer, Independent Implementation Reviewer, Integration Manager and Development Manager; all supplied text read. The filtered handoff, evidence selection, review method and coverage-record instructions were read in full.

Architecture sections examined: **Returned implementation plan**; **Agent performance and context management** and its performance/context/checkpoint subsections; **Local Owner identity and credentials**; **CLI request and event contract**; **SQLite storage**; **Record ownership**; **Save and delivery sequence**; **Questions and answers**; **Answer identity and uncertain delivery**; **Re-registration**; **Comparison, activation, and cancellation**; **Adapter configuration**; **Lasting project structure and specialist guidance**; **Replanning after re-registration**; **Current versions and stale-data prevention**; all of **Execution**; **Journeys and interactions** and its supplied subsections; **Constraints and unresolved details**. The reviewer inspected the heading inventory but did not claim to read every other architecture section.

### Journey coverage

Every journey below records the method's eight trace categories. “Defined” means faithful to the decision or authorized technical elaboration, not proven implementation. “Open” means undecided behavior remains visibly undecided. Architecture headings below refer to `docs/architecture.md`. Conversation heading references identify the original evidence selection, not source-document interpretations.

<details>
<summary>Ten journeys and their decision-fidelity evidence</summary>

#### Hooks boundary

Evidence: conversation **Hooks**.
- Starting conditions — defined in **Internal hooks**: optional organization during implementation, not a prerequisite.
- Input and recipient — defined there: required checks remain in service/wrappers; detailed hook interfaces not assessed because not agreed.
- Configuration and selections — defined there: configurable framework excluded; internal Python handlers permitted.
- Credentials and authority — defined there: no second authority; a separate hook-credential journey is not applicable.
- Storage and transactions — defined there: no second process-state source; no hook-specific storage decision was agreed.
- Interfaces and state — defined there: mandatory checks remain mandatory; no new state contract claimed.
- Results and completion — defined there: implementation organization does not weaken the checks.
- Failure and recovery — defined there: hooks cannot grant retries; detailed failure mechanics not assessed.

#### Execution entry and initial understanding

Evidence: conversation **Execution start and discussion boundary**, **Development Manager launch and purpose**, **Initial understanding**.
- Starting conditions — **Execution initiation**: explicit selected-project start, current confirmed breakdown, conflict/access/configuration and eligible-packet checks.
- Input and recipient — **Execution initiation** and **Development Manager preparation and continuity**: service launches manager first with registration, breakdown, packets, dependencies and saved progress.
- Configuration and selections — **Execution initiation**: manager model collected during start, separate from coder selection; exact payload/controls remain open.
- Credentials and authority — **Execution initiation**, **Development Manager preparation and continuity**, **Local Owner identity and credentials**: confirmed scope only; no manager redesign/replan authority. Live provisioning not assessed.
- Storage and transactions — **Execution initiation**, **SQLite storage**: save before dispatch, duplicate opens existing activity, shared start reservation; provenance of earlier engine choice not assessed.
- Interfaces and state — **Execution initiation**: command/repetition retained; display states remain open and the unaccepted Starting/Running/Blocked proposal is not adopted.
- Results and completion — **Development Manager preparation and continuity**; manager role **Initiation and inputs**: understanding precedes work requests and respects existing progress.
- Failure and recovery — **Execution initiation**: conflicts prevent start, other projects remain independent; detailed Execution lifecycle remains open.

#### Planning, coder selection, notifications and questions

Evidence: conversation **Work choice and coder routing**, **Scheduling and event triggers**, **Planning result and CLI questions**.
- Starting conditions — **Work planning and coder selection**: confirmed dependencies, boundaries, progress and capacity; manager chooses, service validates/reserves.
- Input and recipient — same heading and **Planning results and questions**: completed/blocked/failed work, answers and availability events; grouping and next-pass answer delivery retained.
- Configuration and selections — same headings: permitted routes originate in configuration; manager selects during planning, returns exact model and reason; service validates availability/current state before launch. Qwen primary; justified cloud choice needs no Qwen failure. Registry/location/transport remain open.
- Credentials and authority — **Work planning and coder selection**: no silent substitution, service enforcement and architectural attention for missing dependencies; detailed tool credentials not assessed.
- Storage and transactions — **Planning results and questions**, **SQLite storage**, **Save and delivery sequence**, **Answer identity and uncertain delivery**: durable questions/answers and reservations.
- Interfaces and state — **Planning results and questions**: launch requests, priorities, blockers, questions, checkpoint and stale-request reasons; exact schemas/events remain open.
- Results and completion — **Work planning and coder selection**, **Planning results and questions**: unblocker/parallel priorities, delivery order, reason recording, only dependent work waits.
- Failure and recovery — same headings plus **Questions and answers**: rejected invalid requests and linked reconciliation; replanning pending work cannot automatically interrupt running work.

#### Persistent manager context

Evidence: conversation **Persistent Development Manager**.
- Starting conditions — **Development Manager preparation and continuity**: persistent session per project execution activity.
- Input and recipient — same heading: compact current view with detailed records on demand.
- Configuration and selections — same heading and **Context readings and thresholds**: existing shared policy applies; earlier threshold provenance not assessed.
- Credentials and authority — same heading: memory is not authority; separate persistence credentials not applicable.
- Storage and transactions — same heading and **Checkpoints and safe continuation**: service-saved decisions and versioned checkpoints.
- Interfaces and state — same heading: one planning action, idle between actions, no repeated handled events; exact session protocol remains open.
- Results and completion — same heading; manager role **Persistent context**: preserve useful decisions/reasons/issues, not transcript accumulation.
- Failure and recovery — same heading and **Checkpoints and safe continuation**: verified reconstruction/compaction with retained allowances; live adapter operation not assessed.

#### Specialist gap, support, review, publication and fallback

Evidence: conversation **Specialists and architectural support**, **New-role activation and review**, **Support configuration and backups**, **Common instructions and excluded specialists**.
- Starting conditions — **Specialist assignment and architectural support**: packet-linked gap starts bounded support, not the completed architecture loop.
- Input and recipient — same heading and **Support validation and publication**: packet, roles, confirmed architecture, exact source/context and reviewed inventory.
- Configuration and selections — manager chooses applicable specialist in **Specialist assignment and architectural support**; architect determines existing/new role. **Architectural-support configuration and fallback** separately defines primary/backup tool/model for architect and reviewer, configuration origin, assignment snapshot, hash, availability/capability validation and launch consumption. **Support validation and publication** binds service-assigned paths before drafting through inventory/review to activated references. Configuration authoring UI not assessed.
- Credentials and authority — **Architectural-support configuration and fallback**, **Adapter configuration**, **Support validation and publication**: tool profiles separate from service publication credentials; bounded creation, separate non-author reviewer sessions and no new Owner gate. Machine credential verification remains deferred.
- Storage and transactions — **Support validation and publication**: SQL owns support state/routes/counts/bindings; immutable support/review/activation records, source-local role/context, journal and verified remote publication before atomic activation.
- Interfaces and state — same heading and architect/reviewer support-role sections: existing-role validation versus new-role review, exact versions and activation eligibility; executable validators remain implementation work.
- Results and completion — **Support validation and publication**: required validation/review/publication precede use; unchanged breakdown supplemented, two separate completed-review rounds by default, first pass sufficient, no repeat contents review for unchanged role.
- Failure and recovery — **Architectural-support configuration and fallback**, **Support validation and publication**: prelaunch fallback, normal recovery/confirmed stopping, linked new session with verified progress and preserved budgets; no verdict shopping; at-limit Owner issue and unrelated work continuation; changed inputs invalidate affected binding.
The other project's specialists are excluded in **Coder preparation and submitted results**; their contents were not inspected.

#### Work disposition and finish-current-work

Evidence: conversation **Four dispositions**, **Disposition authority**, **Normal lifecycle clarification**.
- Starting conditions — **Work disposition before re-registration** separates re-registration need from continuation choice.
- Input and recipient — same heading: architect reasons/affected work → saved CLI choice → Owner → manager/service.
- Configuration and selections — same heading: all four Owner choices, exact recommendation/activity/question/version/packet context; fourth remains available even when queued work could continue.
- Credentials and authority — same heading: verified Owner, recommendation or clarification alone not stopping authority; no automatic re-registration/replan.
- Storage and transactions — same heading: saved restriction/in-progress set, atomic first-launch reservation and disposition; including already-reserved work is explicit delegated mechanics.
- Interfaces and state — same heading, **Re-registration**, **Replanning after re-registration**: typed choices, replay/stale handling and distinct manual stages; general lifecycle/stop mechanics remain open.
- Results and completion — **Work disposition before re-registration**: started packets finish normal lifecycle; manager tracks, service closes only after settlement; then explicit re-registration.
- Failure and recovery — same heading: no special retry question/prohibition; unsafe work requires explicit stopping decision; preserved restrictions and no false idle/completion.

#### Coder plan and result

Evidence: conversation **Coder plan and result**, **Common instructions and excluded specialists**.
- Starting conditions — **Coder preparation and submitted results**; coding SOP **Before changing files**: exact packet, role, revision and boundaries.
- Input and recipient — same locations: common instructions plus project specialist and packet; service exposes plan and routes result to manager.
- Configuration and selections — **Specialist assignment and architectural support**, **Work planning and coder selection**: exact assignment and manager route choices; no invented coder model or branch naming.
- Credentials and authority — **Returned implementation plan**; coding SOP **Before changing files**, **Implementation**: no plan-approval gate; scope controls and no coder merge/deploy authority. Credential operation not assessed.
- Storage and transactions — **Coder preparation and submitted results**, **Returned implementation plan**: intermediate plan distinct from validated final result; detailed Execution schemas/transactions remain open.
- Interfaces and state — same headings: intended changes, existing code, connections, checks/blockers, exact revisions/files and known limitations.
- Results and completion — **Coder preparation and submitted results**; coding SOP **Result and handoff**: ready for review is not complete or authorized to merge.
- Failure and recovery — same architecture section and coding SOP **Corrections**: material conflict blocks, limits not invented, older one-correction rule not adopted.

#### Independent implementation review

Evidence: conversation **Reviewer identity and scope**, **Queues and final review/integration ordering**.
- Starting conditions — **Independent implementation review**; reviewer role **Purpose and independence**: exact result/evidence reviewed before Integration.
- Input and recipient — same headings: packet, architecture, common/specialist instructions and evidence; service routes to manager.
- Configuration and selections — **Independent implementation review**; role index **Roles**: Implementation Reviewer distinct from Fidelity Reviewer. Model/config selection remains open/not assessed, not borrowed from support.
- Credentials and authority — **Independent implementation review**: read-only non-author, no code editing/dispatch/merge authority. Retained work-definition-author exclusion's earlier provenance not assessed.
- Storage and transactions — same heading; reviewer **Outcomes and report**, **Corrections and unresolved policy**: exact review/correction coverage saved through service; detailed persistence remains open.
- Interfaces and state — **Independent implementation review**; reviewer **Findings and routing**: requirement/code/impact/minimum correction; defects to coder, missing decisions to architecture, preferences non-blocking.
- Results and completion — same heading and reviewer **Review stages**: exact approval permits Integration, not merge/completion; final Owner ordering correction preserved.
- Failure and recovery — same locations: material correction/escalation; implementation limits/exceptions remain open without borrowing planning budgets.

#### FIFO integration and integration-change review

Evidence: conversation **Queues and final review/integration ordering**, **Integration code authority**, **Integration-change review**, **FIFO integration**.
- Starting conditions — **Integration management and queue**: approved packets, persistent manager and one active integration per project.
- Input and recipient — same heading; integration role **Inputs and continuity**: exact approved code, latest accepted target, evidence, dependencies/shared boundaries.
- Configuration and selections — **Integration management and queue**: durable FIFO order and retained slot through corrections/review; model/session/event/exception details remain open.
- Credentials and authority — same heading; integration role **Purpose and authority**: Integration code manager, Development Manager process manager, necessary in-scope changes, no self-approval; service merge authority separate.
- Storage and transactions — **Integration management and queue**: service queue and durable records authoritative, not memory; detailed queue transaction protocol not assessed/open.
- Interfaces and state — same heading: one active across project milestones, no silent blocked-item skipping, other projects independent and permitted parallel coding/review.
- Results and completion — same heading; integration role **Review and evidence**: review new integration changes/affected behavior, retain valid unchanged coverage; no automatic repeat packet review if no code changes.
- Failure and recovery — same heading and **Authorized integration merges**: corrections return to Integration, next waits for resolution, invalidated target evidence reconciled; exceptional queue handling open.

#### Milestone branching, outcome review, gap analysis and merge

Evidence: conversation **Merge authority and milestone branches**.
- Starting conditions — **Milestone branches and product integration**: milestone from baseline, packets from milestone, assembled milestone checked after its work.
- Input and recipient — same heading: assembled code, completion criteria, confirmed outcomes and connections reviewed; failures to architect.
- Configuration and selections — same heading: exact branch/base identity mapping; naming, branch lifecycle, milestone reviewer/model/limits and result contract remain open. **Authorized integration merges** leaves merge strategy open.
- Credentials and authority — **Authorized integration merges**; AGENTS.md **Git changes**: Integration requests, service verifies/performs, passing milestones need no extra Owner approval; documentation remains direct master. Service credentials remain deferred.
- Storage and transactions — **Milestone branches and product integration**, **Authorized integration merges**: recorded branches/bases and remote verification before success; detailed journals/APIs/completion shapes remain open.
- Interfaces and state — **Milestone branches and product integration**: coder → independent review → FIFO Integration → milestone → outcome review/gap analysis → master eligibility.
- Results and completion — same heading, **Authorized integration merges**; integration role **Merge handoff**: both milestone checks required, packet approval insufficient; detailed delivery/completion records unfinished.
- Failure and recovery — same headings; architect role **Execution findings and milestone gaps**: in-scope determination or re-registration, no silent scope change/replan, changed-target reconciliation.

</details>

### Review disposition and exclusions

No findings were returned; no source correction is required by this review. The reviewer found the technical elaborations in support configuration, records, publication, fallback accounting and disposition receipts within delegated authority, not falsely described as individually approved settings.

The evidence is a chronological excerpt selection without exact timestamps, not all prior conversation. Earlier decisions' provenance is available only where supplied. Excluded: unrelated specialists, code, unsupplied schemas/declarations, prior review reports, live master inspection by the reviewer, credentials and runtime behavior. General Execution protocols, correction limits, Quality Assurance, milestone reviewer assignment, branch naming, merge strategy and completion remain open. Faithfully retaining those open matters is not a defect in this fidelity pass.


## Integration and milestone delivery checkpoint

The Owner clarified the final sequence after an intervening misunderstanding: coder finishes → independent review cycle → approval → Integration Manager. The temporary suggestion to omit independent review was explicitly corrected and is not adopted.

### Decisions and coverage

| Agreed subject | Authoritative architecture section |
|---|---|
| Coder reads packet and returns plan without another approval gate; validated final result goes through service to Development Manager | Coder preparation and submitted results |
| Independent read-only review against exact work, architecture and evidence; author cannot review own implementation | Independent implementation review |
| Concrete defects block; preferences do not; findings route through service and Development Manager | Independent implementation review |
| Role-based queues and saved state belong to service, not conversation memory | Integration management and queue |
| Development Manager manages process; persistent Integration Manager manages product code and may make needed in-scope integration changes | Integration management and queue |
| Independent review of integration changes and affected behavior; retain unchanged coverage; no automatic repeat review when no code changes | Integration management and queue |
| One FIFO integration queue and one active integration assignment per project, retained through reviews/corrections | Integration management and queue |
| Development milestone branch from product baseline; packet branches from and merged into their milestone branch | Milestone branches and product integration |
| Whole-milestone outcome review and gap analysis before master promotion | Milestone branches and product integration |
| Service checks exact approved revision, current destination and authorization, performs merge; no extra Owner approval for passing milestone | Authorized integration merges |
| Failed milestone checks require architectural determination or re-registration/replanning | Milestone branches and product integration |

The existing Integration Agent file is retained as `docs/agents/integration-agent.md` with role title Integration Manager; no duplicate role is created. The independent reviewer, Development Manager, Project Architect and common coding instructions now agree with this flow. The specialists folder remains untouched and excluded from assignment choices for this work. The role index links to the updated responsibilities.

AGENTS.md distinguishes the explicitly approved future Execution branching model from current direct-to-master documentation work. No branch, pull request, code implementation, merge operation on product code, new milestone declaration or runtime schema was created.

### Validation and remaining design

Author self-check, not independent review. Sources: the current master versions of AGENTS.md, CLAUDE.md, architecture, role index, Integration Agent, Independent Implementation Reviewer, Development Manager, Project Architect, common coding instructions and this handoff; decision evidence: the available conversation from coder handoff through the Owner's milestone-branch agreement.

The table traces fidelity to authoritative sections. Consistency checks traced coder → independent review → FIFO Integration → review of changed integration code → milestone branch → milestone outcome review/gap analysis → authorized master merge; also checked failed-review routing, changed-target reconciliation, unchanged-code review retention and separation from registration publication. Role links and architecture headings were checked. No new independent review round or budget reset was claimed. Saved remote contents are verified after writing.

Remaining decisions include implementation correction/review limits and exceptions, Integration Manager model/session details, blocked-queue resolution, exact branch naming/lifecycle and merge strategy, milestone outcome-review role/model/limits, Quality Assurance and detailed completion/recovery records. The old fixed one-correction and automatic-escalation assumptions are not adopted. The earlier support-review and fallback rules do not determine implementation review budgets.

Executable protocols, code, live model operation and full product readiness were not tested or established. This is a bounded evolving-design checkpoint, not a complete Execution specification or a full independent fidelity verdict. Next discussion should continue with the unfinished milestone outcome-review and gap-analysis responsibility before assuming it is assigned to an existing role.

## Architectural-support checkpoint

The Owner approved writing the subsequent agreements and delegated routine configuration, record, validation and handoff mechanics. Architecture owns the behavior; the Development Manager, Project Architect and Fidelity Reviewer roles reference it. Existing milestone declarations and runtime JSON schemas are unchanged because they do not yet declare these Execution capabilities delivered.

| Agreement | Defining location in Architecture |
|---|---|
| Architect recommends; Owner selects one of four dispositions through a linked CLI decision | Work disposition before re-registration |
| No new packets; already-started work completes its natural lifecycle, including permitted reviews, corrections and recovery | Work disposition before re-registration |
| No extra retry question or special transition failure policy | Work disposition before re-registration |
| Manager tracks results; service ends execution only when work and operations are settled; explicit re-registration remains required | Work disposition before re-registration |
| Existing role applicability or new source-local role/context; exact versions supplement the unchanged confirmed breakdown | Support validation and publication |
| New roles receive independent fidelity review; unchanged existing contents do not need repeat review | Support validation and publication |
| Two configurable completed reviews per support assignment, separate accounting, first pass sufficient, unresolved material issues reach Owner | Support validation and publication |
| Separate configured architect/reviewer tools and exact model versions; primary and backup for each | Architectural-support configuration and fallback |
| Prelaunch availability fallback; recovery and confirmed stopping before an active-run replacement | Architectural-support configuration and fallback |
| No switch merely for an unsatisfactory result; unusable routes pause affected work | Architectural-support configuration and fallback |
| Linked replacement session receives exact inputs and verified progress, retains remaining allowances and reviewer independence | Architectural-support configuration and fallback |

Routine technical choices are recorded explicitly: the shared TOML section, required role durations, separate recovery accounting with default two attempts, service-assigned support identities and publication paths, fixed support/review/activation records, exact-version bindings, and durable disposition receipts. These choices implement the delegated mechanics; they do not establish general coding review, correction, merge or completion rules. Configured backup routing here applies to the two architectural-support roles, not a silent expansion of registration or coder routing.

### Validation

Author self-check only. Examined the available conversation from the prior checkpoint through this write request and current master versions of the architecture, three affected agent-role files, repository instructions and handoff. Decision fidelity is traced above. Consistency coverage follows disposition → saved start restriction → normal work lifecycle → idle closure; support request → configured route → result → independent review → verified publication → role binding; and primary failure → stopping/recovery → backup inputs/counters. Checked new heading links, obsolete unresolved statements and isolation from provisional implementation correction rules.

Publication records do not embed their own unknown commit: same-publication references use paths/hashes and the journal supplies the verified commit. The service activates no unreviewed new role and changes no confirmed manifest. Distinct backup sessions cannot reuse author history as independent review. No review-budget reset or additional independent round was claimed.

Runtime implementations, complete executable Execution schemas, live model availability, storage durability and overall Execution readiness were not tested. The normal lifecycle and detailed stop implementation still depend on the remaining Execution design. This checkpoint is not a declaration of full completeness; no standalone review report was created.

## Execution design checkpoint

The Owner authorized writing the agreed discussion and validating it on master before a short break. [Execution](../../docs/architecture.md#execution) owns behavior; the [Development Manager](../../docs/agents/maestro-development-manager.md) and [Project Architect](../../docs/agents/architecture-agent.md#execution-architectural-support) describe their responsibilities. The role index and overview point to those boundaries. Existing milestone declarations and machine-readable contracts were not expanded to imply complete Execution delivery.

### Decisions preserved

| Conversation agreement | Authoritative location |
|---|---|
| Explicit selected-project start; current confirmed breakdown, conflict/access/configuration/eligible-packet checks; save before dispatch; duplicate opens existing activity; independent projects | Architecture — Execution initiation |
| Model selected at start; service launches the Development Manager first | Architecture — Execution initiation |
| Manager coordinates approved work, not scope changes or replanning; reads sources/progress and returns initial understanding | Architecture — Development Manager preparation and continuity |
| Manager chooses work; service validates, reserves and launches | Architecture — Work planning and coder selection |
| Qwen primary; justified Codex or Claude Code model level/version without requiring Qwen failure | Architecture — Work planning and coder selection |
| Configured permitted routes, capabilities/context/concurrency; no invented model or silent substitution | Architecture — Work planning and coder selection |
| Use architecture dependencies, parallel boundaries and integration points; prioritize unblockers while considering delivery order and capacity | Architecture — Work planning and coder selection |
| Event-driven reassessment, related-event grouping, pending work only; running work not automatically interrupted/reassigned | Architecture — Work planning and coder selection |
| Persistent per-activity manager session; idle between actions; one active planning action; compact context and verified replacement | Architecture — Development Manager preparation and continuity |
| Structured launch requests, reasons, priorities, blockers, questions and checkpoint; reject stale requests | Architecture — Planning results and questions |
| Saved CLI questions/answers; only dependent work waits | Architecture — Planning results and questions |
| Existing specialist role/context assigned with exact packet, source and change bounds | Architecture — Specialist assignment and architectural support |
| Bounded architect support chooses existing role or creates one in confirmed boundaries; material changes require re-registration | Architecture — Specialist assignment and architectural support |
| Four work dispositions, including deliberate finish-current-work choice even when queued work could continue | Architecture — Work disposition before re-registration |
| Idle-only re-registration and separate manual architecture/execution starts preserved | Architecture — Work disposition before re-registration |
| Required checks stay in service/wrappers; internal hooks optional, configurable framework excluded | Architecture — Internal hooks |

The earlier assistant proposals for service-only work selection and specific Starting/Running/Blocked display states were not adopted. Model choice for the Development Manager is separate from its coder choices. The finish-current-work choice does not silently approve continuing work known unsafe or invalid, nor bypass the existing idle conditions.

### Resume here

The Owner chooses work disposition through the CLI. Finish-current-work follows the normal packet lifecycle, with no special retry branch. Specialist validation/review/publication and configured primary/backup behavior are now defined in the later [architectural-support checkpoint](#architectural-support-checkpoint).

The later integration checkpoint now defines implementation-result routing, independent review, Integration Manager authority and merge boundaries. Remaining correction/review limits, Quality Assurance and detailed completion rules must finish the normal lifecycle used when finishing current work. General Execution request/result/event contracts, coder registry and Qwen transport remain to be defined. GitHub App/service credentials remain deferred to the local machine.

### Validation coverage and limits

Author self-check, not an independent pass. Inputs were the available conversation from the hooks discussion through this save request, current master architecture, both affected role files, role index, overview, repository rules and existing handoff. The table above traces decision fidelity. Consistency checks covered command wording, Qwen's execution-versus-registration boundary, service/agent authority, role status, unchanged initial declaration scope, idle-only replanning and the separation of proposals from agreements. New architecture heading links were checked. The older Development Manager role's assumed service mechanics and correction rules were replaced with the agreed responsibilities and an explicit unresolved-policy boundary; they were not silently adopted.

No independent review budget was restarted or round consumed. This is an evolving design checkpoint, not a claim that sources are sufficient for registration or that the full Execution design is complete. Existing earlier review coverage remains tied to its original snapshots. Live model capabilities, installation, schema validation and full end-to-end readiness were not assessed. No standalone review report was created.

## Pause before Execution design

Execution design is paused at the Owner's request. The proposed execution command, eligibility, dispatch and completion discussion has not been adopted as new architecture.

An author self-check used frozen master commit `46849407227a2d025a2bd4882d16f619a14ebae2` and the available conversation decisions. This is a decision/status reconciliation, not a full independent completeness review. Earlier assistant replies absent from the supplied history cannot be reconstructed as decision evidence.

| Checked subject | Supporting location and result |
|---|---|
| Functional boundaries and runtime | Architecture — Purpose and boundaries, Functional areas, Runtime and prerequisites: Planning/Execution/Monitoring, persistent Python Linux service and initial CLI scope retained. |
| CLI and data | Architecture — CLI connection configuration, Questions and answers, Save and delivery sequence, SQLite storage: localhost fallback, explicit linked answers, SQL-before-acknowledgment and service-owned writes retained. |
| Registration | Architecture — Intake and scope, Source and publication selection, Purpose and dependency checks, Review limits and decisions: both role selections, pinned source/authorized destination, connected-outcome checks and bounded reviews retained. |
| Registration update and recovery | Architecture — Re-registration, Publication recovery, Technical recovery: idle-only updates, prior-version preservation, reconciled writes, distinct counters and no automatic budget reset retained. |
| Architecture loop | Architecture — Entry and responsibility, Initial code investigation, Lasting project structure and specialist guidance, Work-packet-first breakdown: source investigation, persistent guidance, smallest bounded packets and designed parallelism retained; scheduling remains Execution. |
| Confirmation and replanning | Architecture — Confirmation and completion, Replanning after re-registration: exact-version confirmation stops the loop; confirmed re-registration and manual architecture start are required for replanning. |
| Installed contracts | Architecture — Installed validation schemas, Registration process-definition binding; both JSON schema files: installed bundle references and configuration-only registration schema distinction retained. Both JSON files parse and all 97 internal references resolve. This is not full schema validation. |
| Authority and completion evidence | Planning Guide — Verification expectations, Relationship to development breakdown; Project Architect — Assignment and authority; Reviewer — Inputs and independence; four declarations — Unresolved details: basic real verification, routine architect authority and unfinished delivery-review policy remain explicit. |

Architecture heading references from the four declarations, Planning Guide and two architecture/reviewer role files resolve. Specialist template headings match the architecture. Current source observations remain historical evidence; runtime operation is not established.

Outstanding qualifications: GitHub App/service credential verification is deferred to the local machine; complete registration output schemas and executable validators are implementation work; installed tool compatibility, isolation, startup and recovery need operational evidence. General delivery-review authority must be defined before affected development breakdown. Recent corrections have author self-checks, not completed independent correction review. Existing consumed review budgets remain unchanged.

No additional decision change was identified in this recorded coverage. Full requirement-by-requirement fidelity across unavailable earlier replies, all schema field semantics, workshop package contents, source code and live provider capabilities were not assessed. This check does not declare registration readiness or that no gaps remain.

## Consistency cleanup

- [Agent performance and context management](../../docs/architecture.md#agent-performance-and-context-management) marks Qwen as future adapter support while retaining the shared no-penalty capacity rule.
- [Agent workspaces](../../docs/architecture.md#agent-workspaces) uses the registration activity ID for the attempt directory and explains the older placeholder as the same identity.
- [Context readings and thresholds](../../docs/architecture.md#context-readings-and-thresholds) distinguishes sampling cadence from fresh observations, preserves observation timestamps and explains long-turn visibility limits. [Runtime service milestones](../../docs/milestones/runtime-service-milestones.md) require evidence of those limits.
- Development Manager, Developer, Integration, Quality Assurance and Common Coding files now carry a provisional marker linked to [the existing role authority boundary](../../docs/agents/README.md#roles). Their retained rules were not rewritten or granted new authority.
- The [Planning Guide](../../docs/planning-guide/README.md) example now points to the existing runtime prerequisites heading.
- GitHub repository metadata confirms the canonical name is `jmiedreich-ux/Maestro`; the existing spelling is correct. GitHub also resolves [the overview's baseline commit](https://github.com/jmiedreich-ux/Maestro/commit/8d1448473c7f95fa830fac9e49d36b8cdb7cf17d). The [overview](../../docs/project-overview.md#source-observations) now links directly to that commit; historical source observations remain tied to it, not asserted as current operation.

Author self-check: examined current revisions of the linked files and all five affected role files; checked changed headings, links, role-content preservation, identity wording, context behavior and declaration versions. Repository name and baseline existence were verified through GitHub. No adapter was run and historical code behavior was not re-audited. No independent pass, new review round, standalone report or full completeness claim was made. Existing review limits remain unchanged; broader readiness and installed credentials remain outside this check.

## Registration configuration correction

[Registration process-definition binding](../../docs/architecture.md#registration-process-definition-binding) defines the effective table, required sections, default application and policy-to-handler mapping. [Registration process configuration schema](../../docs/schemas/registration-process.schema.json) validates that table and is installed as its own configuration-only bundle. Output record and agent-response checks retain their existing contracts; no complete output-schema bundle or implemented validator is claimed.

[Publication recovery](../../docs/architecture.md#publication-recovery) now names the configured maximum, separate per-operation counters and write-attempt accounting. [Registration milestones](../../docs/milestones/registration-milestones.md) and [runtime service milestones](../../docs/milestones/runtime-service-milestones.md) link the implementation evidence to these rules. Tool/model choices stay at intake, role authority is unchanged, registration does not acquire architecture-loop output-correction allowances, and confirmation stops.

Author self-check coverage: current architecture sections for intake, assignments, review limits, response validation, publication, recovery and installed schemas; the new configuration schema; affected declaration rows and this handoff. Traced configuration → defaults → handler selection → saved activity → recovery, including invalid settings and separate retry counters. Eight focused checks exercised the schema's used keywords against valid and invalid tables (required sections, policy values, integer limits, output root, role fields and forbidden correction setting). JSON parsed and the internal definition reference resolved. These used a limited evaluator, not a full JSON Schema validator, which was unavailable. No independent pass or additional review round was started. Live installation, output-validator implementation, full schema validation and broad documentation completeness were not assessed.

This correction resolves the recorded configuration binding subjects, not overall registration readiness. GitHub App credential location and service binding still await the local machine. Historical findings below refer to their frozen snapshots.

## Schema installation correction

[Architecture — Installed validation schemas](../../docs/architecture.md#installed-validation-schemas) owns bundle location, exact selection, activity snapshot and recovery behavior. The [architecture-loop schema](../../docs/schemas/architecture-loop.schema.json) replaces the repository-path constant with the installed bundle reference. [Runtime service milestones](../../docs/milestones/runtime-service-milestones.md) require installation and recovery evidence. Project application schemas remain separate.

Author self-check only: examined the current source revisions of those three files and this handoff; traced installation → configured selection → activity snapshot → recovery and missing/changed-bundle failure. Checked the schema edit changes only the configuration constant, JSON parsing and internal references, and the affected declaration versions and architecture links. No independent review round was started; existing review limits remain unchanged. No installation, runtime validation, full schema-validator test or operational recovery test was performed. Broader documentation completeness was not assessed. Historical findings below retain their original snapshot scope; the installed-locator finding is resolved by this contract, not evidence of implementation.

## Agreed foundation corrections

Authoritative changes:

- [Tool and model selection](../../docs/architecture.md#tool-and-model-selection): registration collects and saves both role choices before architect launch; intake, request prose and journey coverage agree. [Registration milestones](../../docs/milestones/registration-milestones.md) require corresponding evidence.
- [SQLite storage](../../docs/architecture.md#sqlite-storage): local database configuration, service-owned writes, short serialized transactions, reader concurrency, durability settings and failure boundaries. [Runtime service milestones](../../docs/milestones/runtime-service-milestones.md) reference this contract rather than redefining it.
- [Shared process definitions](../../docs/architecture.md#shared-process-definitions) and [adapter configuration](../../docs/architecture.md#adapter-configuration): matching nested settings, unchanged defaults and separate budgets; old registration keys are invalid.
- [Specialist template](../../docs/agents/specialists/specialist-overlay-template.md): the required role title and four headings contain the existing boundary, policy, source, dependency, verification and handoff guidance. The [specialist index](../../docs/agents/specialists/README.md) points to the authoritative format.

Verification is an author self-check, not an independent review. Coverage: the changed architecture sections and intake journey, affected declaration outcomes and versions, template headings and retained guidance, obsolete registration keys, and remote source revisions before writing. The architecture-loop schema was inspected; its existing nested process settings and role-file handling require no shape change for these corrections. No full implementation, installed configuration, database durability test, adapter capability test or broader completeness review was performed. No additional review round was started; completeness and consistency remain at two of two under the existing method-validation subject. Independent review of these corrections remains pending within existing authority and limits.

The GitHub App secret location and service credential binding remain deferred until the local machine is available. Installed schema-resource resolution is superseded by the later correction below. Registration process-definition and publication-operation recovery-limit bindings are superseded by the later configuration correction. These edits do not establish readiness for execution or close those gaps. Historical coverage below applies to its recorded snapshots.


## Shared registration reference correction

At commit `b57fcd2cfc5b9a1508e813f9f226e5bbbdd0f95a`, `docs/architecture.md` **Candidate publication** names the shared registration reference and its publication-versus-source meaning; **Architecture record contract** distinguishes generic file references. `docs/schemas/architecture-loop.schema.json` defines `registrationRef` once and uses it in all fourteen `registration_ref` and `validated_registration_ref` properties, including start, assignments, saved/prepared records, views and carry-forward checks. The existing `publishedRef` definition is unchanged. The earlier frozen review's reference-conversion finding is addressed in these documents, not left as a current unanswered decision.

Verification was an author self-check: JSON parsing, resolution of all 96 internal schema references, inspection of all fourteen consumers and unchanged generic reference shape, and five focused checks for the new shape, old generic shape, missing repository, unsafe manifest path and invalid manifest hash. These were temporary contract examples, not repository fixtures or operational evidence. A full JSON Schema validator was unavailable; full schema validation was not run. Saved GitHub bytes were checked. No independent correction review was claimed or extra review round started; the existing limits remain unchanged. Independent review of this correction remains pending under those limits. No standalone report was created.

## Source selection correction

The current Owner instruction authorized defining source commit and publication branch selection. The correction is specified in `docs/architecture.md#source-and-publication-selection`; affected intake, manifest, publication and architecture-entry sections reference it. The registration declaration's initial, update and recovery outcomes contain corresponding acceptance evidence. No runtime code or schema was changed.

CONSISTENCY-SOURCE — Source and destination correction check links to CONSISTENCY-1 — Pre-execution documentation consistency. Reviewer `/root/source_target_consistency` used a separate context, authored/corrected none of the reviewed files, and received only the named correction and controlling requirements under the targeted-check exception. This consumed consistency round two of two under `pre-execution documentation method validation`. The earlier completeness budget also remains two of two; no budget was restarted.

The reviewer compared baseline `f259ea929b249f62bde3660a15c8d8d4d3d07bf1` with corrected commit `d1d121269e149be4abdd770f2a11126eff1974c7`. Repository instructions and the shared review method were read at the corrected revision. Architecture was read by the exact headings below; milestone reads included declaration identity/order plus the relevant architecture-reference and acceptance sections. Unresolved-detail conclusions, handoff and prior review outputs were not supplied. Separate host session ID and packet hash were not recorded; exact commits and selected headings identify the examined sources.

| Journey | Supporting locations and targeted coverage |
|---|---|
| Initial registration | Architecture **CLI request and event contract**, **Intake and scope**, **Source and publication selection**, **Source consistency**, **Package record contract**, **Candidate publication**; registration declaration **REG-PM1 — Register and confirm a project through the CLI**, **Architecture and journeys/Acceptance criteria**. Input source, caller/default selection, authority, SQL/Decision/manifest binding, visible CLI values, assignment/publication use and invalid-ref/access/destination behavior agree. |
| Registration update | The selection/source headings plus **Re-registration**; declaration **REG-PM2 — Update a registration without losing approved history**, **Architecture and journeys/Acceptance criteria**. Idle-only entry, inherited or amended selection, resolution for the new attempt, unchanged authority, candidate/active-history separation, visible choices and rejection without fallback agree. |
| Interrupted publication | **Source and publication selection**, **Candidate publication**, **Publication recovery**; declaration **REG-PM3 — Recover registration without losing decisions or exceeding limits**, **Architecture and journeys/Acceptance criteria**. Saved inputs/target, service authority, journal ownership, remote/SQL result and lost-acknowledgment/conflict behavior agree; recovery does not re-resolve source or substitute a target. |
| Architecture entry/continuation/publication | **Source and publication selection**, **Entry and responsibility**, **Architecture API operations**, **Persistent-session adapter contract**, **Current versions and stale-data prevention**, **Publication, recovery, and cancellation**. Entry prerequisites, confirmed source/destination origin, authority, session/assignment/journal binding, output-reference separation, completion boundaries and stale/unavailable-input recovery agree. |

All architecture headings above are in `docs/architecture.md`; declaration headings are in `docs/milestones/registration-milestones.md`. Declaration and affected milestone version changes were checked. Coverage is complete for this targeted assignment, with no findings: no gaps were found within its recorded consistency coverage. The source/destination omission is addressed in documentation; this does not establish overall readiness.

The reviewer did not assess service credential configuration, SQL engine choice, reviewer selection intake, registration-reference shape, TOML/resource bindings, broader guide/role/schema consistency, other journeys or live operation. General storage mechanics and failure cases unrelated to the selected source/target were outside this check. No fresh completeness or decision-fidelity pass was performed. No standalone report was created.

## Review-method validation

<details>
<summary>Frozen inputs, review coverage and benchmark disposition</summary>

### Snapshot, independence and accounting

The full validation used commit `91ec57af13d9bfc14455eb9adb3936df9d212760`. Both reviewers independently reproduced filtered-packet SHA-256 `e6e79ee2efaaf051f65ea3a33b2936b915eb8e6cf8569c3d591ac44dd37794cf`. They read all 41 files: `AGENTS.md`, `CLAUDE.md`, `README.md`, all files under `docs/` and `skills/project-architecture-workshop/`, and the filtered handoff. All surviving headings, tables, template fields and schema definitions were examined. Service implementation and external references were not examined.

| Coverage record | Reviewer and separate context | Mode and accounting | Result |
|---|---|---|---|
| COMPLETENESS-1 — Pre-execution documentation method validation | `/root/clean_completeness` | Full; first completed completeness round | Material changes required |
| CONSISTENCY-1 — Pre-execution documentation consistency | `/root/clean_consistency` | Full; first completed consistency round | Material changes required |

Both were eligible non-authors, reported no prohibited-input exposure, and returned complete coverage. Each consumed one round under the same subject, `pre-execution documentation method validation`, with the existing maximum of two per pass. Neither full record has a parent, applied corrections or subsequent architectural invalidations. Separate host session identifiers were unavailable; the recorded agent contexts identify the actual reviewers.

Earlier attempts by `/root/blind_completeness` and `/root/blind_consistency` used commit `dabfa4014fafa0ae0bed5717d33393f825b92709` and encountered embedded author readiness conclusions. They are retained as ineligible attempts, not completed independent reviews, and consume no round. Their findings were not supplied to the replacement reviewers.

The packet hash covers compact UTF-8 JSON of sorted `{path, sha256}` entries, with each inner hash covering the filtered UTF-8 file. The packet retained original source locations while filtering verdict clauses in Architecture **Architecture-loop implementation boundary**, the CLI/architecture-loop/runtime declarations' **Unresolved details**, and the handoff. Only handoff **Decisions to preserve** and **Remaining design** were supplied; its role-input sentence was labeled a coordinator paraphrase. Owner evidence also included the supplied excerpts requiring breakdown after registration, excluding SQL backup, allowing replanning only after re-registration, and restricting re-registration to periods with no work in progress. The full conversation and decision index were unavailable to reviewers; no full decision-fidelity conclusion is claimed.

The two handoff replacements are the exact role-input paraphrase stated in the source-filter assignment and the heading `# Handoff: preserved decisions and accepted deferrals` followed by two newlines. The paraphrase is: “Role inputs and the [structured registration response](../../docs/architecture.md#registration-agent-response-contract) remain accepted decisions.”

For reproducibility, these are descending UTF-16 ranges in the frozen originals, applied before display. A range is start-inclusive and end-exclusive. Unlisted bytes remain unchanged.

| Original path | Filtered ranges and retained replacement |
|---|---|
| `docs/architecture.md` | 166695–166974: retain “Implementing those contracts and verifying installed tool support belong to development.” |
| `docs/milestones/architecture-loop-milestones.md` | 15027–15072: period; 9476–9513: remove |
| `docs/milestones/cli-milestones.md` | 18168–18236 and 11865–11933: remove |
| `docs/milestones/runtime-service-milestones.md` | 27814–27865: period; 16818–16853 and 8831–8885: remove |
| `ai/handoffs/current.md` | 8978–9494: remove; 6522–6706: labeled role-input paraphrase; 0–5863: replace with a neutral heading introducing preserved decisions and deferrals |

### Retained full-review coverage

The following shared location groups compress the two reviewers' source traces. All architecture headings refer to `docs/architecture.md` at the frozen revision. Locations identify examined definitions; missing items in the disposition table override any apparent agreement. Each runtime storage trace includes the absent engine/deployment decision. Every service publication trace includes the absent service credential and destination binding.

| Location group | Concrete headings and compared representations |
|---|---|
| Runtime | **Runtime and prerequisites**, **Shared process definitions**, **Adapter configuration**; runtime declaration **Capability and scope**, **Dependencies**, **Acceptance criteria**, **Unresolved details** for the affected service outcomes |
| Connection | **CLI connection configuration**, **Local Owner identity and credentials**, **CLI request and event contract**; both CLI milestones and runtime connection outcome **Acceptance criteria** |
| Workspace | **Startup and connection states**, **Projects and targeting**, **Project activities and registration labels**, **Attention**, **Commands**, **Empty results**, **Keyboard and terminal behavior**; CLI workspace **Acceptance criteria** |
| Answers | **Questions and answers**, **Answer identity and uncertain delivery**, **Assignment delivery and clarification**; CLI answers **Acceptance criteria** |
| Storage | **Record ownership**, **Save and delivery sequence**, **Answer identity and uncertain delivery**, **Assignment and run identity**, **Re-registration**; runtime storage **Acceptance criteria** |
| Agents | **Tool and model selection**, **Agent workspaces**, **Assignment and run identity**, **Process supervision and interruption recovery**, **Technical recovery**, **Activity retry request**, **Checkpoints and safe continuation**; runtime agent and registration recovery **Acceptance criteria** |
| Registration | **Source format and inputs**, **Intake and scope**, **Source consistency**, **Purpose and authority**, **Assessment and independent review**, **Review limits and decisions**, **Registration agent response contract**; registration initial/update outcomes, Planning Guide **Entry document and source references**, architect **Registration responsibilities**, fidelity reviewer **Registration assignment/Registration review authority** |
| Registration files | **Package structure**, **Package record contract**, **Publication and SQL consistency**, **Candidate publication**, **Confirmation and activation**, **Publication recovery**, **Comparison, activation, and cancellation**; registration declarations' criteria and Planning Guide **Naming, ordering, and versions** |
| Entry | **Entry and responsibility**, **Persistent architect session**, **Persistent-session adapter contract**, **Architecture assignment and response contract**, **Architecture API operations**; architecture foundations criteria and both roles' **Architecture-loop assignment** |
| Investigation | **Initial code investigation**, **Whole-product architectural evaluation**, **Saved findings and architecture decisions**; architecture foundations criteria, architect role and overview **Source observations** |
| Foundations | **Lasting project structure and specialist guidance**, **Architecture output locations and records**, **Architecture schema and process-definition binding**; architecture foundations criteria and all specialist README/template headings |
| Breakdown | **Information sufficiency and clarification**, **Work-packet-first breakdown**, **Architecture record contract**; architecture breakdown criteria, architect role, alignment guide **Sufficient information for breakdown** |
| Review | **Deterministic packet checks and correction**, **Independent review and amendments**, **Owner decisions at a process limit**, **Run deadlines and duration exceptions**; architecture confirmation criteria and fidelity role |
| Publication | **Confirmation and completion**, **Publication, recovery, and cancellation**, **Current versions and stale-data prevention**; architecture confirmation and runtime shared-process criteria |
| Reconciliation | **Replanning after re-registration**, **Current versions and stale-data prevention**, **Architecture schema and process-definition binding**; registration update and architecture confirmation criteria |
| Schema | `docs/schemas/architecture-loop.schema.json`: all `$defs`, especially selection/assignment/startPayload, prepared/saved findings and reviews, processDefinition, publishedRef/setRef, specialist/projectStructure, workPacket/developmentMilestone, manifest/index/confirmation, carryForward and request/receipt/view |
| Workshop | Skill **Start or resume**, **Work through a subject**, **Save, review, and continue**, **Stop conditions and final output**; installation **Use the workshop skill**; review method and workshop state all headings; state/interface fields; both guides and their three source templates |

Milestone references include the following exact headings and their **Architecture and journeys**, **Dependencies**, **Acceptance criteria**, **Definition of done**, and **Unresolved details** subsections.

| Coverage name | Exact declaration path and heading |
|---|---|
| CLI workspace | `docs/milestones/cli-milestones.md` — CLI-PM1 — Connected multi-project CLI workspace |
| CLI answers | Same path — CLI-PM2 — Reliable project questions and answers |
| Service installation | `docs/milestones/runtime-service-milestones.md` — SVC-PM1 — Operate the persistent Maestro service |
| Service storage | Same path — SVC-PM2 — Preserve project activity and requests |
| Service connection | Same path — SVC-PM3 — Connect the CLI to recorded service activity |
| Service agent | Same path — SVC-PM4 — Run and recover assigned agents |
| Service shared-process | Same path — SVC-PM5 — Apply shared process definitions |
| Registration initial | `docs/milestones/registration-milestones.md` — REG-PM1 — Register and confirm a project through the CLI |
| Registration update | Same path — REG-PM2 — Update a registration without losing approved history |
| Registration recovery | Same path — REG-PM3 — Recover registration without losing decisions or exceeding limits |
| Architecture foundations | `docs/milestones/architecture-loop-milestones.md` — ARC-PM1 — Establish the project's architectural foundations |
| Architecture breakdown | Same path — ARC-PM2 — Produce a bounded and parallel-ready work breakdown |
| Architecture confirmation | Same path — ARC-PM3 — Review and confirm the development breakdown |

Role paths are `docs/agents/architecture-agent.md` and `docs/agents/decision-fidelity-reviewer.md`; specialist paths are under `docs/agents/specialists/`; guide and alignment paths are `docs/planning-guide/README.md` and `docs/planning-guide/architecture-milestone-alignment.md`. The frozen file inventory fixes each path.

| Journey | Starting conditions | Input and recipient | Configuration and selections | Credentials and authority |
|---|---|---|---|---|
| Open/use workspace | Runtime, Workspace | Connection, Workspace | Connection, Workspace | Connection |
| Answer question | Answers | Answers, Connection | Answers, Connection | Connection, Registration |
| Initial registration | Runtime, Registration | Registration, Agents | Runtime, Registration; source/destination gaps | Registration, Agents; publication-access gap |
| Registration update | Registration, Storage | Registration files | Registration, Runtime; inherited selection gaps | Registration files; publication-access gap |
| Interrupted registration recovery | Agents, Registration files | Agents, Registration files | Agents, Runtime; inherited selection gaps | Connection, Review; publication-access gap |
| Architecture entry/session continuation | Entry, Storage | Entry, Answers | Entry, Runtime, Schema; source-baseline gap | Entry, Connection, role assignments |
| Code investigation | Entry, Investigation | Investigation, Entry | Entry, Schema; source-baseline gap | Investigation, role assignment |
| Structure/specialist guidance | Investigation, Foundations | Foundations, Publication | Foundations, Schema; format/destination gaps | Foundations, role assignment; publication-access gap |
| Breakdown/clarification | Foundations, Breakdown | Breakdown, Answers | Breakdown, Schema, Runtime | Breakdown, role assignment |
| Review/amendment | Review | Review, Entry | Review, Runtime, Schema | Review, fidelity role |
| Publication/confirmation | Publication, Review | Publication, Connection | Publication, Schema; destination/resource-binding gaps | Publication, Connection; publication-access gap |
| Architecture cancellation/recovery | Publication, Agents | Publication, Agents | Runtime, Agents, Schema | Connection, Review, Publication |
| Reconciliation after re-registration | Registration, Reconciliation | Reconciliation, Entry | Reconciliation, Schema; baseline/reference gaps | Registration, Reconciliation |
| Workshop installation/start/resume | Workshop installation/start | Workshop start/interface | Workshop installation, state paths | Workshop start, repository Git rules |
| Workshop discussion/drafting | Workshop subject, guides | Workshop subject | Guides/templates, Workshop save | Workshop subject, architect authority |
| Workshop save/review/handoff | Workshop save, Review method | Review method, state | State bound/coverage, publication fields | Workshop save, method disposition |

| Journey | Storage and transactions | Interfaces and state | Results and completion | Failure and recovery |
|---|---|---|---|---|
| Open/use workspace | Storage | Connection, Workspace | **Open and use the workspace**; CLI workspace done criteria | Workspace, Connection |
| Answer question | Storage, Answers | Connection, Answers | **Answer a project question**; CLI answers done criteria | Answers |
| Initial registration | Storage, Registration files | Registration, Registration files | **Register a project or selected portion**; registration initial done criteria | Registration, Agents, Registration files |
| Registration update | Storage, Registration files | Registration files | **Update a registration**; registration update done criteria | Registration files, Agents |
| Interrupted registration recovery | Storage, Agents, Registration files | Agents, Registration files | **Recover an interrupted registration**; registration recovery done criteria | Agents, Registration files |
| Architecture entry/session continuation | Storage, Entry, Agents | Entry, Schema; registration-reference gap | Entry; architecture foundations criteria | Entry, Agents |
| Code investigation | Storage, Investigation | Investigation, Schema | Investigation; architecture foundations done criteria | Investigation, Review, Publication |
| Structure/specialist guidance | Storage, Foundations, Publication | Foundations, Schema; specialist-format gap | Foundations; architecture foundations done criteria | Foundations, Publication |
| Breakdown/clarification | Storage, Breakdown, Investigation | Breakdown, Schema | Breakdown; architecture breakdown done criteria | Breakdown, Review, Publication |
| Review/amendment | Storage, Review, Publication | Review, Schema | Review; architecture confirmation criteria | Review, Agents |
| Publication/confirmation | Storage, Publication | Publication, Schema | Publication; architecture confirmation done criteria | Publication |
| Architecture cancellation/recovery | Storage, Publication, Agents | Publication, Entry, Schema | Publication; architecture confirmation criteria | Agents, Publication; recovery-limit binding gap |
| Reconciliation after re-registration | Storage, Reconciliation | Reconciliation, Schema; registration-reference gap | Reconciliation; architecture confirmation/update criteria | Reconciliation, Publication |
| Workshop installation/start/resume | Workshop state; SQL not applicable | Installation/interface, state paths | Workshop start and installation outcome | Workshop start/state recovery |
| Workshop discussion/drafting | Workshop save/state; SQL not applicable | Guides/templates, state decisions | Workshop final-output/source-readiness conditions | Workshop subject, guide missing-information rules |
| Workshop save/review/handoff | State save/recovery; SQL not applicable | Review method/state fields | Method disposition; Workshop final output | Method eligibility/bounds; state recovery |

Both full passes covered the thirteen runtime journeys. Completeness also returned three workshop journeys; consistency grouped workshop discussion with save/review/resume in two workshop records. The table preserves that distinction rather than claiming another independently assigned pass. Supporting locations are evidence of examination, not verified implementation.

### Findings and disposition

No underlying architecture, guide, template, milestone or schema correction was applied in this task. The following returned findings remain open for architect disposition within existing authority.

| Subject and classification | Missing or contradictory information and location | Affected outcome, impact and minimum correction |
|---|---|---|
| Source and destination selection — blocking | Architecture **Intake and scope**, **Source consistency**, **Candidate publication**, **Entry and responsibility** do not define initial source resolution, later code-baseline derivation, or another project's branch selection. | Registration and architecture can otherwise inspect/publish different revisions or destinations from identical intake. Define chooser, input/default, resolution, saved binding, validation and downstream use; retain Maestro's `master` rule. Both full passes found this. |
| Service publication access — blocking | **Agent workspaces**, **Adapter configuration**, **Candidate publication** and architecture publication assign service writes without a service GitHub credential/reference and repository/branch authorization binding. | Real publication and recovery need a service identity distinct from agent-tool and Owner API credentials. Define provisioning/reference, permitted destination, access validation and failure handling. Both full passes found this. |
| SQL engine and deployment — blocking | **Record ownership**, **Answer identity and uncertain delivery**, **Re-registration** and runtime storage criteria require transactions without a recorded engine/deployment choice or explicit engine-selection deferral. | Durable acceptance, concurrency exclusion and recovery depend on that choice. Record it and its guarantees, or an authorized deferral with decision owner/selection point and unverified guarantees. Both full passes found this; backup remains excluded. |
| Process configuration and installed resource binding — blocking | Consistency compared `registration_architect.run_timeout_seconds` with `architecture_loop.architect.run_timeout_seconds`, and root `automatic_recovery_attempts` with `architecture_loop.recovery.automatic_recovery_attempts` under **Adapter configuration**, **Shared process definitions** and Schema `processDefinition`. The full registration effective-table/policy contract, publication-operation recovery-limit binding and installed resolution of `saved_outputs.schema` remain missing. | Configuration authors and runtime validators need the same literal contract. Define the effective registration table, explicit cross-process mapping/differences, publication recovery setting and installed schema locator. The consistency pass captured the differing layouts and these missing bindings; it did not declare every differing key an error merely because it differs. |
| Registration reference conversion — blocking | **Candidate publication** supplies a package reference; **Architecture API operations** and Schema `publishedRef` require a differently shaped reference without a mapping. | Architecture start/reconciliation cannot compare the same confirmed package unambiguously. Define the shared shape or lossless conversion, including repository/candidate/version/manifest/hash binding. Found by consistency. |
| Specialist role format — non-blocking | **Architecture schema and process-definition binding** requires role headings that `docs/agents/specialists/specialist-overlay-template.md` does not provide; the specialist README recommends that template without an applicability distinction. | Following the template does not produce the specified role artifact. Align it or distinguish its purpose and identify the correct format. Found by consistency. |

The third-party benchmark was compared only after the independent outputs returned. Source/branch selection, service credentials, storage choice, process-configuration differences/bindings, and specialist formats were surfaced. Both full passes missed the registration reviewer's input collection point: they treated a separate selection and pre-launch validation as sufficient. That miss led to a narrower method correction requiring separate evidence for each selection step and separate coverage subitems.

### Targeted selection-evidence check

COMPLETENESS-1-SELECTION — Selection collection-to-use correction check was performed by `/root/selection_evidence_check` in a separate context, with no source authorship/correction or prohibited-input exposure. It links to COMPLETENESS-1 — Pre-execution documentation method validation, uses the same budget subject, and consumes the second and final completeness round. Consistency remains at one of two rounds. No budget was reset.

The corrected method is commit `2d110644fc0a6f9551741d6c57dcf6ad4091d494`; its state fields/template are included in frozen commit `009d32b5d16b2d6b462f6a4b0f5fe670ebbe7105`. The supplied packet hash is `0082b108a7f65625c4a2ca31c0b255ae92229bfd47fa389df73501f150782405`; this reviewer did not independently recompute it. Filtering was unchanged. The check examined collection-to-use selections and their setup dependencies only, not another full review.

The reviewer read the revised method/state/template, repository instructions, architecture selection/setup headings below, relevant passages in all four declarations, Planning Guide input/reference/naming sections, relevant schema definitions, filtered handoff, fidelity role, and skill/installation instructions. Truncated displays were not credited without subsequently reading the relevant passages. An unsuccessful request for `docs/agents/project-architect.md` supplied no evidence. Unread parts of the 41-file packet and unrelated categories were not assessed.

The evidence below uses exact headings in `docs/architecture.md`, or the already-defined source groups where named. Each chain is recorded separately; later validation does not fill an absent input step.

| Selection | Input source | Choosing actor | Collection point | Saved value | Validation | Consumer |
|---|---|---|---|---|---|---|
| Registration repository/overview | Caller; **Intake and scope** | Caller; same heading | **CLI request and event contract** intake | **Package record contract** source repository/overview | **Intake and scope** access/identity; package checks | **Assignment delivery and clarification** |
| Architecture/declaration source paths | Planning Guide **Entry document and source references** | Source author; same heading | Service follows overview references; same heading | **Assignment delivery and clarification**, package references | **Package record contract**, assessment | Architect/reviewer inputs; **Assignment delivery and clarification** |
| Whole/partial scope | Plan and caller boundary; **Intake and scope** | Caller; same heading | Saved questions and boundary confirmation; intake/API contract | **Package record contract** scope/decisions | **Intake and scope** dependency/boundary checks | Assessment, package and architecture inputs |
| Registration architect tool | Installed allowlist; **Adapter configuration** | Caller; **CLI request and event contract** | Saved intake question; same heading | **Tool and model selection** run evidence | Same heading: tool/capability checks | **Assignment delivery and clarification** launch |
| Registration architect exact model | Full identifiers; **Adapter configuration** | Caller; **CLI request and event contract** | Saved intake question; same heading | **Tool and model selection** requested/reported model | Same heading: exact model and no substitution | Architect launch/result acceptance; same heading |
| Registration reviewer tool | Separate selection required; **Tool and model selection** | **Missing** | **Missing**; intake names only architect | **Tool and model selection** run evidence | Same heading: separate role's prelaunch checks | Independent reviewer launch; same heading |
| Registration reviewer exact model | Full identifiers; **Adapter configuration** | **Missing** | **Missing** | **Tool and model selection** requested/reported model | Same heading: exact-model checks | Reviewer launch/result acceptance; same heading |
| Initial source ref/commit | Repository known; **Intake and scope**; selector/default **missing** | **Missing** | Ref input/resolution point **missing** | Assignment and **Package record contract** exact commit | Package/source equality checks | Architect/reviewer/publication; Registration and Registration files |
| Retain/update changed source | Changed input; **Source consistency** | Owner; same heading and initial registration criteria | Explicit source choice; **Source consistency**, Answers | Package source/decision versions | Relevant-change/coverage checks; **Source consistency** | Amended package/review/confirmation; Registration files |
| Publication repository | Registered repository; package and architecture record contracts | Service inherits accepted project; same contracts | Accepted repository intake | **Candidate publication** journal; published refs | Same heading: repository/path/remote checks | Registration and architecture publication |
| Publication branch | Authorized branch required; **Candidate publication** | **Missing for projects generally**; Maestro itself fixed to master | **Missing for projects generally** | **Candidate publication** intended-branch journal | Same heading: expected branch/head checks | Registration and architecture publication |
| Registration output paths | Fixed **Package structure** | Contract/service; package/assignment contracts | Assignment output locations | Manifest inventory and publication journal | **Package record contract**, **Candidate publication** | Publication/review/confirmation |
| Architecture project/registration | Selected project and active registration; **Architecture API operations** | Caller project; service active reference | Project selection/start payload; same heading | Activity inputs; same heading | Exact active reference; same heading | Session/assignments; Entry |
| Architecture architect tool/model | Allowed explicit selection; **Persistent architect session** | Caller; **Architecture API operations** | Start form collects missing selection; same heading | Session and assignment selection; Entry, Schema | **Tool and model selection** checks | Initial/resumed/replacement architect; Entry |
| Architecture reviewer tool/model | Separate allowed selection; **Persistent architect session** | Caller; **Architecture API operations** | Start form's reviewer selection; same heading, Schema startPayload | Activity/session/assignment; Entry | Exact-model/independent-session checks; Entry, Agents | Reviewer runs; Entry, Review |
| Architecture source baseline | Confirmed registration/exact source required; Entry | Initial derivation/chooser **missing** | Registration-to-investigation baseline mapping **missing** | Session/assignment source_commit; Entry | **Current versions and stale-data prevention** | Investigation/continuation/review |
| Architecture output IDs/paths | Fixed layout and architect allocation request; **Architecture assignment and response contract** | Service binds IDs/paths; same heading | Required outputs/allocation exchange; same heading | Assignment/manifest; architecture record contracts | Ownership/uniqueness/hash checks; Foundations, Schema | Artifact preparation/staged publication; Publication |
| Specialist title/source area/path | Investigated area; **Architecture output locations and records** | Architect title/area; service permitted path | Allocation request/binding; assignment contract | Structure/manifest; architecture record contracts | Assigned location/ownership; Foundations | Role/context publication and later inputs; Publication |
| Packet deliverables/permitted paths | Confirmed outcomes/investigation; **Work-packet-first breakdown** | Architect; same heading | Packet returned through assignment contract | **Architecture record contract** packet fields | **Deterministic packet checks and correction**, Schema | Later packet use; Execution not assessed |
| Continuation/recovery bindings | Prior verified session/inputs; Entry, Publication | Service retrieves saved choices; same groups | Exact saved identity retrieval; Entry | Linked sessions/runs/checkpoints; Entry, Agents | Exact identity/stale checks; Entry, Publication | Resumed/replacement work; Entry |
| Confirmation/cancel/allowance target | Displayed exact target/action; Registration files, Publication, Review | Owner; same groups | Explicit action/typed decision; Connection, Review | Requests/decisions/confirmation; same groups | Identity/version/eligibility/replay checks | Activation, confirmation, cancellation or allowance; same groups |

Setup dependencies were also traced:

| Setup selection | Collection-to-use evidence and disposition |
|---|---|
| Tool executables/profiles/model allowlist/workspace | Installation supplies **Adapter configuration** fields/defaults; service installation/agent milestones assign delivery; effective values are hashed/validated and consumed by adapters. Installed values/operation remain development evidence. |
| Process policies, durations and limits | **Shared process definitions**, **Review limits and decisions**, **Context readings and thresholds**, **Publication, recovery, and cancellation**, and Schema processDefinition identify configuration/defaults, validation, activity snapshots and consuming operations. This targeted selection trace does not close the full consistency findings about the incomplete registration table or publication-limit binding. |
| CLI address/Owner credential path | **CLI connection configuration** and **Local Owner identity and credentials** define configuration/defaults, installation provenance, file handling and consuming API/authentication checks. |
| Service repository credentials | Agent profiles exist, but service credential source, chooser/collection and project/operation binding remain **missing** under **Adapter configuration** and **Candidate publication**. Define that setup contract before service reads/writes; agent authentication is insufficient evidence. |
| Installed runtime schema | **Architecture schema and process-definition binding** and Schema processDefinition name a repository path; installed resolution/version binding remain **missing**. Define how installation supplies the resource and runtime resolves it. |
| SQL engine/deployment | **Record ownership**, **Save and delivery sequence** and service storage criteria specify durable transactions; engine/deployment/configuration selection remains **missing**. Record the decision or an authorized deferral and its unverified guarantees. |

The check independently found the previously missed reviewer tool/model chooser and collection point. This is blocking for registration review: **Tool and model selection** defines separate selection and validation, while **CLI request and event contract** collects only the architect's choices. The minimum correction is to define the reviewer input mechanism, chooser, collection timing and saved selection before review. It remains open; no architectural correction was made.

The check also independently found the already-recorded source/baseline, publication branch, service credentials, installed-schema mapping and SQL-selection omissions. Its result is `material_changes_required` for those definitions and complete coverage for the targeted method test. The full passes' earlier assumption about reviewer collection is superseded by this finding. Other full-review coverage is retained without expansion.

Together, the blind full passes and this blind targeted check surfaced all six requested benchmark subjects. The configuration result is bounded as described above: different layouts were recorded, and missing effective-table/resource mappings were found; uniform spelling was not imposed as a new architectural requirement. The stronger method improved detection in this trial, not proof of universal completeness.

No full conversation-fidelity pass, historical-code verification, installed-tool check, live credential/publication check, SQL operation, systemd behavior or connected acceptance was performed. General Execution policy, command center/mobile, future agent routes and SQL backup/restore remain outside coverage. The recorded findings describe documentation gaps found within this coverage; they do not establish that all possible gaps have been found.


</details>

## Decisions to preserve

- The architect is a software architecture role responsible for technical coherence and usable connected outcomes. It both assesses sources and prepares the candidate package.
- Routine technical choices within scope do not need Owner approval. Changed outcomes, expanded scope, conflicts with agreed requirements, reserved decisions, and final registration confirmation retain their agreed authority boundaries.
- The independent reviewer checks both assessment and candidate fidelity. Routine corrections go to the architect; justified material disagreement at the review limit reaches the Owner. No extra review loop was added.
- Role inputs and the [structured registration response](../../docs/architecture.md#registration-agent-response-contract) are already defined. Do not reopen them as unanswered questions.
- The adapter runs an agent tool; the service owns validation, durable records, budgets, question routing, and registration state. One adapter may run different roles in separate independent runs.
- For later execution work packets, the agent returns its implementation plan after reading the packet and then continues. Maestro records and displays it. No plan-review, approval, or pause gate is included now; such a gate is only a possible future addition.
- CLI implementation precedes registration development. Final connected CLI acceptance uses real initial registration integration. Re-registration display evidence belongs to REG-PM2 — Update a registration without losing approved history.
- Initial delivery remains CLI-only; the command center is excluded.

## Remaining design

Registration architect and reviewer runs each default to 30 minutes, configured separately; other planning and execution assignments do not inherit that setting. The automatic technical recovery maximum is two attempts per assignment, separate from fidelity reviews. Failure classification determines whether another run is appropriate. Timeouts pause after confirmed stopping. Manual retry follows intervention, permits one run, and preserves the automatic budget and history. Unknown original-run status blocks replacement. Workspaces remain until explicit removal and cannot be removed while needed by a run, review, or recovery. See the architecture for authoritative rules.

Broader implementation-review authority, coding corrections, merge authority, and development completion remain provisional for separate Execution design. Registration needs agents to perform its own work, but its controls must not be treated as approval of general Execution policy. Executable package schemas, physical SQL tables, publication operations, and adapter verification belong to implementation of the defined contracts. Technical adapter configuration is defined in `/etc/maestro/agents.toml`. Routine technical settings can be resolved by the architect within the agreed scope.

The current documents specify outcomes and behavior, not implementation completion. Existing code is assessed during relevant development preparation; registration only checks claimed dependencies as needed.

## Working rules

Commit authorized changes directly to `master`; no branches or pull requests. Use plain, concise wording and include subjects with coded references. Architecture explains behavior; declarations explain delivery outcomes. Keep each fact authoritative in one place and use references elsewhere.

Apply review corrections to the main documents. Do not create or present separate review reports unless requested. Resume from the current documents and this handoff, without reopening settled decisions.


## Milestone Quality Assurance and test-data checkpoint

The Owner confirmed that Quality Assurance is a milestone-level function. It checks the assembled milestone rather than individual work packets or Integration Manager changes. Coders verify their changes; independent reviewers assess packet changes, Integration Manager changes, and the whole-milestone outcome and gap analysis. Quality Assurance separately exercises user journeys, connected behavior, and failure cases. Findings use the existing correction path and the affected checks are rerun; no additional approval loop was created.

Quality Assurance may start the product and required supporting services in an isolated test environment when needed to exercise actual behavior.

The architecture loop defines each milestone's required data sources, preparation and setup, expected results, and actual capability paths. Quality Assurance prepares or uses that data and records its origin, entry path, actual result path, expected and actual results, and limitations. Missing setup tooling is planned work with an explicit dependency; Quality Assurance does not improvise it.

The controlling safeguard is that test data may supply inputs but cannot replace the capability under verification. Directly creating an expected result, bypassing a required service or journey, or relying on a mock does not verify the bypassed path. Every bypassed required step remains `UNTESTED` and cannot establish milestone completion.

Unavailable required verification is neither a defect nor a pass. It keeps the milestone unmerged and appears as a specific CLI blocker while unrelated eligible work may continue. Quality Assurance runs the affected verification after its prerequisite becomes available.

The authoritative behavior is in [milestone Quality Assurance and test data](../../docs/architecture.md#milestone-quality-assurance-and-test-data). The Quality Assurance, Project Architect, Development Manager, Integration Manager, Independent Implementation Reviewer and role-index files now align with it. The milestone delivery sequence requires both completed required Quality Assurance with no failed or unverified required path and a passing milestone outcome review and gap analysis before promotion to product `master`.

### Validation and limits

This documentation update was self-checked against the available conversation decision sequence and current master files. It defines responsibilities and safeguards, not implementation completion. Detailed isolated-environment mechanics remain open, and deployed-environment testing remains separately authorized. Packet and Integration Manager review/correction limits and detailed completion records remain unresolved. Earlier handoff statements that Quality Assurance responsibilities were open are superseded by this checkpoint; their other recorded open subjects remain unchanged.


## Independent milestone Quality Assurance and test-data fidelity review

**Result: pass.** Read-only reviewer `/root/qa_test_data_fidelity` reviewed master snapshot `9b3997ff560c5c65edd3cc3ec3d730469a0f8ac7` and returned no blocking or non-blocking findings. No correction or second review round was required.

The reviewer traced the complete milestone journey: Integration Manager assembly; milestone Quality Assurance against actual journeys, connected behavior and failure cases; existing correction routing and affected-check reruns; `UNTESTED` handling for missing prerequisites or bypassed paths; fresh independent milestone outcome review and gap analysis using Quality Assurance evidence; and the two required gates before promotion to product `master`.

Coverage included the architecture, Quality Assurance, Project Architect, Development Manager, Integration Manager, Independent Implementation Reviewer and role-index files, repository rules, this handoff, and related test-data language in the Planning Guide and milestone declarations. The reviewer found no active text that makes Quality Assurance packet-level, lets test data replace the capability under verification, treats unavailable verification as a pass or defect, or allows promotion without both gates. Older handoff statements that Quality Assurance remained open were correctly treated as historical snapshots superseded by the later checkpoint.

The reviewer checked 121 local Markdown links across the nine required files, covering 24 unique local targets, and found no missing target or heading anchor.

Implementation, runtime and live CLI behavior, environment provisioning, deployed-environment testing and unrelated Execution-policy gaps were excluded. The review made no repository changes and does not claim those areas are complete.


## Packet and integration-change review-limit checkpoint

The Owner had already confirmed this decision before the milestone Quality Assurance discussion; its omission from the active master documents was a recording gap, not an open policy question.

Packet implementation review and review of Integration Manager code changes have separate configurable limits. Each defaults to two completed rounds for the exact assignment: the initial review and, if required, one targeted correction review. Invalid or interrupted review output and technical recovery do not consume a completed round. Reassignment, reviewer replacement, a new session, renamed work or workspace movement does not reset the limit.

If blocking findings remain at the applicable limit, the affected work stays unapproved and unmerged. The Project Architect supplies a recommendation and the Owner is notified through the CLI. No automatic extra review is permitted. Unrelated eligible work continues.

The authoritative rule is [packet and integration-change review limits](../../docs/architecture.md#packet-and-integration-change-review-limits). The Development Manager, Project Architect, Integration Manager, Independent Implementation Reviewer and role-index files now align with it. Registration, architecture-loop, architectural-support and milestone-review budgets remain separate.

### Validation and remaining design

This correction was checked against the recorded September 16 Owner agreement and the current delivery sequence. Active statements that packet and integration-change review limits were unresolved were removed. Detailed result records, milestone reviewer model selection, correction-supplement activation, cross-milestone source delivery, exceptional FIFO queue resolution and other implementation mechanics remain separate technical design.

## Execution technical architecture completion checkpoint

This checkpoint supersedes the active-status assertions in earlier handoff sections that general Execution review authority, completion records, isolated-environment mechanics, reviewer routing, correction supplements, cross-milestone source delivery, exceptional FIFO handling or result contracts were still provisional. Those passages remain historical records of their snapshots.

The authoritative Execution contracts are now in [Execution](../../docs/architecture.md#execution), with aligned role, overview and milestone-declaration text. They define exact route/model configuration and deadlines; the shared request/state/record contract; deterministic coder-route matching; service-owned worktrees and credentialed Git operations; strict FIFO integration; branch mechanics; independent packet, integration-change and milestone review; typed Owner grants and manual retry; bounded milestone-gap assignments and correction supplements; versioned Quality Assurance plans, isolated environments and retained evidence artifacts; cross-milestone dependency delivery and invalidation; pause/stop settlement; and distinct successful-completion and stopped-closure records.

Routine technical choices remain architectural decisions. The settled Owner boundaries, review defaults and no-silent-substitution rules are unchanged. Executable `execution@1` schemas and handlers, physical SQL tables, installed tools/systemd/environments, operational evidence and an Execution milestone declaration remain implementation or later delivery work. SQL backup and restore remain out of scope.

When snapshot `148678a717061074ab8dfc8ebe8e0ecaa8574d6c` was frozen, none of the three fresh passes had completed. Decision fidelity later approved it. Architectural completeness and cross-document consistency requested the changes recorded below. Corrections were published through snapshot `6ec49bc24e3bfb38824f8bf00ca2c1e921a7d968`; each original reviewer then completed a targeted correction check, and all three final conclusions are `APPROVE`.

### Journey coverage

All full passes used the same ten end-to-end journeys: start/configuration/model selection; persistent Development Manager planning and coder dispatch; packet review and correction limit; strict FIFO integration and Integration Manager change review; correction-supplement activation; cross-milestone dependency delivery; isolated milestone Quality Assurance; milestone outcome review and promotion; pause/resume/graceful stop/re-registration/restart recovery; and milestone/Execution completion publication. Each journey covered starting conditions, inputs and recipients, configuration and selections, credentials and authority, storage and transactions, interfaces and state, results/completion evidence, and failure/recovery.

### Review coverage records

#### Decision fidelity

- id: `execution-fidelity-v1`
- subject: Execution technical architecture and aligned roles/declarations
- pass_type: `decision_fidelity`
- mode: fresh full review, followed by targeted changed-scope fidelity check
- scope_budget_round: one full pass at the frozen snapshot; one targeted delta check; no runtime product review budget consumed
- reviewer: `/root/execution_fidelity_v1`
- snapshot: full review `148678a717061074ab8dfc8ebe8e0ecaa8574d6c`; targeted delta through `6ec49bc24e3bfb38824f8bf00ca2c1e921a7d968`
- sources: `AGENTS.md`, `skills/project-architecture-workshop/references/reviews.md`, `docs/architecture.md`, `docs/project-overview.md`, the seven selected Execution/architecture review role files, and the Runtime Service, Registration and Architecture Loop milestone declarations
- journeys: all ten listed above
- not_assessed: executable schemas/handlers, physical SQL design, installed or live behavior, SQL backup/restore, an Execution milestone declaration, and unrelated files
- findings: none in the full pass; none in the correction delta
- result: full `APPROVE`; targeted delta `APPROVE`
- coverage_complete: true; original full coverage retained across the corrected delta
- round_consumed: one full documentation-review pass; targeted check did not create another full pass
- correction_refs: none required for fidelity; delta commits were checked for regression

#### Architectural completeness

- id: `execution-completeness-v1`
- subject: implementable completeness of the ten Execution journeys
- pass_type: `architectural_completeness`
- mode: fresh full review, followed by targeted correction check
- scope_budget_round: one full pass at the frozen snapshot; one targeted check of the twelve findings
- reviewer: `/root/execution_completeness_v1`
- snapshot: full review `148678a717061074ab8dfc8ebe8e0ecaa8574d6c`; corrected snapshot `6ec49bc24e3bfb38824f8bf00ca2c1e921a7d968`
- sources: the same frozen governance and twelve selected architecture/role/overview/declaration sources
- journeys: all ten listed above
- not_assessed: executable `execution@1`, source behavior, physical SQL tables, installed services/tools/credentials/environments, live evidence, SQL backup/restore, an Execution milestone declaration, and unrelated files
- findings: `EC-001` run deadlines; `EC-002` review-limit Owner actions; `EC-003` manual retry grants; `EC-004` worktrees/Git/reviewer isolation; `EC-005` coder route eligibility; `EC-006` milestone-gap architect assignment; `EC-007` confirmed QA inputs; `EC-008` QA artifact durability; `EC-009` dependency invalidation; `EC-010` repository credential authority; `EC-011` supplement self-hash; `EC-012` pause/stop and stopped-record shape
- result: initial `REQUEST_CHANGES`; every finding `RESOLVED`; amended conclusion `APPROVE`
- coverage_complete: true for the full pass and targeted correction scope
- round_consumed: one full documentation-review pass; targeted check did not create another full pass
- correction_refs: `bcaf72c4cd15ae46b476f35e2acf15c2331da638`, `f51544dbf165cabb2ef2a846ac372457322d7e20`, the aligned role/declaration commits, and final corrected snapshot `6ec49bc24e3bfb38824f8bf00ca2c1e921a7d968`

#### Cross-document consistency

- id: `execution-consistency-v1`
- subject: names, authority, operations, configuration, records, links and scope across the selected documents and handoff checkpoint
- pass_type: `cross_document_consistency`
- mode: fresh full review, followed by targeted correction check
- scope_budget_round: one full pass at the frozen snapshot; one targeted check of four findings
- reviewer: `/root/execution_consistency_v1`
- snapshot: full review `148678a717061074ab8dfc8ebe8e0ecaa8574d6c`; corrected snapshot `6ec49bc24e3bfb38824f8bf00ca2c1e921a7d968`
- sources: the same frozen governance and twelve selected sources; current handoff conclusions were excluded from fresh inputs and this checkpoint's historical wording was supplied separately
- journeys: all ten listed above
- not_assessed: completeness and fidelity as separate verdicts, executable or live behavior, unrelated files, and earlier handoff review conclusions
- findings: `XDC-001` stale unfinished Execution-interface statement; `XDC-002` conflicting Owner-decision operation registry; `XDC-003` stale Registration milestone prerequisite; `XDC-004` present-tense pending-review wording in the proposed handoff
- result: initial `REQUEST_CHANGES`; every finding `RESOLVED`; amended conclusion `APPROVE`
- coverage_complete: true for the full pass and targeted correction scope
- round_consumed: one full documentation-review pass; targeted check did not create another full pass
- correction_refs: command/operation/Owner-decision corrections in `bcaf72c4cd15ae46b476f35e2acf15c2331da638`; Registration declaration and aligned role corrections through `6ec49bc24e3bfb38824f8bf00ca2c1e921a7d968`; this time-anchored checkpoint wording

### Publication state

The architecture and aligned documents are ready as technical design, not as implemented capability. Continue from the current `master` documents. Do not reopen the settled Execution decisions unless new evidence, changed scope or a reserved Owner decision requires it.


## Execution delivery milestone checkpoint

### Scope and decision evidence

The Owner requested the missing Execution project milestones in the current conversation: “Ok do the mission project milestones”, immediately corrected to “Missing”. This follows the clarification that Maestro's own Execution declaration was absent, distinct from the development milestones Maestro generates for registered projects. The Owner also agreed to project progress, agent activity, attention and history as the Monitoring scope and identified notification behavior as already decided. No notification policy was reopened.

The architect organized the existing Execution contracts into five project outcomes in [EXE — Execution](../../docs/milestones/execution-milestones.md): reviewed packet delivery; integration and declared dependencies; bounded architectural corrections; milestone verification and completed Execution; and pause, stop and recovery. Grouping and delivery order are architect choices within the requested declaration, not new Owner behavior decisions. The project overview is version 12 and lists the declaration as an authoritative registration source.

The declaration owns Execution-specific service and CLI delivery over the existing foundations. It keeps source/current-state limitations, genuine connected acceptance, milestone-only QA, test-data safeguards, separate review limits, authorized automatic promotion, and distinct completed/stopped closure. It records shared correction/QA acceptance and lifecycle controls alongside affected stages so delivery order creates no circular implementation prerequisite or permission to omit safeguards. No development packets, implementation, installation, registration or Execution start were performed.

### Prerequisite corrections

The declaration review identified missing producer/consumer definitions. The architect clarified the repository credential-profile input chain through operator-provisioned repository bindings, registration intake and confirmation, and inherited Execution use. Execution now explicitly derives its product code baseline from the confirmed breakdown/registration source and separately records the observed product-master start head. These are technical definitions under the existing source, credential and confirmation authority; no additional Owner approval step or credential selection during Execution is added.

The supplied architecture-loop schema lacks the packet execution requirements, milestone QA-plan reference and QA-plan records/inventory required by the architecture. Their executable-schema and publication alignment is explicitly assigned to ARC-PM2 — Produce a bounded and parallel-ready work breakdown, with confirmation/Execution consumption dependent on that actual delivered validation. No executable schema was implemented in this documentation task. Stale wording about coder correction limits and the Qwen adapter contract was aligned with the existing authoritative rules; no allowance or model policy changed. The architecture-loop declaration is version 6; its milestone versions are 6, 5 and 6 in declaration order. The registration declaration is version 22; its milestone versions are 17, 11 and 16 in declaration order. Existing histories remain in Git.

### Documentation review coverage

The full passes assessed the same ten journeys below against source commit `1d3e3a3a06e7ac0983beb4cfa2251cc1d25a4f9f` and the initial draft. Initial packet manifest SHA-256: `80f6f168fc3ea7ad17f7cd278cb64c6ca93872d69771b24cb9d90c6f521b68cf`. The corrected packet manifest is `2909e5ddc586ca8b0e8162969b2f20a44ed35f2ead4313635d5876a48c54b693`. Each reviewer checked the manifest against the supplied bytes. Original input availability was the current conversation excerpts and frozen authoritative sources; full historical transcripts were not available. The exact request and its correction are retained above, separately from the architect's grouping and technical choices.

Fresh review inputs excluded all earlier handoff history and review conclusions and the proposed review-state/next-action bookkeeping. Only the new checkpoint's Scope and decision evidence was supplied; its filtered hash was `8d20f840b0b65efe55d0037a8368291ff66aaf0ba22a59f52286bdd8f266824c`. Targeted inputs added the prerequisite-correction section, named findings and exact changed-source diff; corrected filtered handoff hash: `81d313a79fbfbc0835e4df9b985ecdc5d218ab8c87f09438483e0ec276bd15de`. Reviewer sessions were separate, read-only, non-author and not exposed to prohibited author or prior-review conclusions in the fresh passes. No standalone reports were created.

| Review identity and subject | Pass and scope | Reviewer | Full result and round | Targeted result |
|---|---|---|---|---|
| execution-declaration-fidelity-1 — Execution project milestone declaration | Decision fidelity of the declaration, overview, filtered checkpoint and connected authority/input boundaries | `/root/execution_milestones_fidelity` | Round 1: pass, no findings; coverage complete and round consumed | Round 2 targeted delta: pass; coverage complete and round consumed |
| execution-milestones-completeness-full-1 — Execution milestone prerequisite and delivery completeness | Architectural completeness of all ten delivery journeys and prerequisite input chains | `/root/execution_milestones_completeness` | Round 1: material changes required; three findings; coverage complete and round consumed | Round 2 targeted correction check: pass; all named findings resolved; coverage complete and round consumed |
| execution-declaration-consistency-1 — Execution declaration and connected source consistency | Cross-document consistency of declaration, architecture, overview, roles, guide, producer schema and foundation declarations | `/root/execution_milestones_consistency` | Round 1: material changes required; four findings; coverage complete and round consumed | Round 2 targeted correction check: pass; all named findings resolved; coverage complete and round consumed |

Each pass retains its own budget key (Execution milestone declaration version 1 / its pass type), maximum two rounds: the full pass and one targeted correction check. Full coverage is retained separately from the corrected delta. The findings and corrections are:

| Finding and subject | Classification | Impact and minimum correction | Canonical correction | Disposition |
|---|---|---|---|---|
| AC-1 / C2 — Repository credential-profile binding | Blocking | Execution used an already-saved profile without its choosing/collection/save chain. Define and assign its producer without an Execution credential override. | Architecture — Source and publication selection; Adapter configuration; registration declaration initial/update acceptance | Resolved by targeted verification |
| AC-2 — Execution product baseline | Blocking | Branch creation consumed an unexplained baseline. Define derivation, pinning, validation and recovery binding separately from current master. | Architecture — Execution initiation; Execution declaration reviewed-packet start acceptance | Resolved by targeted verification |
| AC-3 / C1 — Execution inputs absent from producer schema | Blocking prerequisite alignment | Supplied schema rejects required packet requirements and milestone QA reference and lacks QA-plan/inventory/allocation support. Explicitly assign the missing producer-schema work or implement it; never weaken consumer checks. | Architecture — Architecture-loop implementation boundary; architecture-loop declaration breakdown/confirmation; Execution dependencies; overview status | Resolved as explicit unimplemented prerequisite delivery; targeted verification passed |
| C3 — Stale coder correction-limit statement | Non-blocking | Coding instructions called limits undefined despite the controlling configured review rules. | Common Coding Agent Instructions — Corrections | Resolved; targeted verification passed |
| C4 — Stale Qwen adapter-status statement | Non-blocking | Context introduction called the adapter unspecified despite its Execution contract. | Architecture — Agent performance and context management | Resolved; targeted verification passed; implementation/installed checks remain unverified |

#### Examined sources and exact snapshots

The hash table preserves the relevant source bytes independently of any later source edit. Unchanged hashes remain the initial value. Review-packet metadata files are temporary evidence packaging, not new project deliverables.

| Source | Initial SHA-256 | Corrected SHA-256 if changed |
|---|---|---|
| `AGENTS.md` | `c64a97b69cc3485c98bf84e792366729d1f8292492bbfbbb74a349ff9496ed25` | Unchanged |
| `CLAUDE.md` | `fc35ea4c8df3e90a0cddffafd23ed6937f379d308d80005643b33c3408883cf0` | Unchanged |
| `REVIEW-SCOPE.md` | `18c976d91eefb23742832a9b0167e93a4226138678c35cca71b2d6e25c40c893` | Unchanged |
| `docs/agents/README.md` | `37cf5448fbcf6f9c4aa9eea7a45cbb9365ff96d8f65bbd1b160f934863a737da` | Unchanged |
| `docs/agents/architecture-agent.md` | `e3d491513f0729fd90b593d7c201658df27a64132062528c0fe8b8aaa3f97151` | Unchanged |
| `docs/agents/coding-agent-sop.md` | `5e9df78036c10713ad7f9d45538010d67cc33d175f4746dd51ac52a8a9ea0619` | `3a6df86cdd8b5d9d0626feb32b393d0bac309be45d38962ad8ade811f94e42f2` |
| `docs/agents/decision-fidelity-reviewer.md` | `4c8eb2727e450eab28cf8161d834bd9f9b5a694b491cea4739e5f71575f9100f` | Unchanged |
| `docs/agents/independent-review-agent.md` | `b1088e2543e88c31267fb60eaf55ae68af29de8458ec3bb1ed914ce70d446356` | Unchanged |
| `docs/agents/integration-agent.md` | `75d12e65dc65695ac6ec4d64d6768bded619f64d25098ef441d5ce8301120fed` | Unchanged |
| `docs/agents/maestro-development-manager.md` | `3150782e9e91b7b7a7cf208e477d640aae50b03cc6791f362f89978c8a30de58` | Unchanged |
| `docs/agents/qa-agent.md` | `cc4f374792f5490d14ad25a07fe5c2d96edd461e40de8c9b5584789cc4cf52dd` | Unchanged |
| `docs/architecture.md` | `0b2b5151b1506a899cd284f9440a808c117537429bcdfcddd61c56cc96b2fcc7` | `d5424d855e577746e3069ddb10f5a82b56cf9194a461b5339ec3aa45fab01090` |
| `docs/milestones/architecture-loop-milestones.md` | `5df8b135b562c482b6bcc10f5338888c379a1dc3104b9c3e2f68a9cfe3e34f4d` | `f6cfe14f0f043e973378a49d8f20db9d17949fc7f0ad4cc69a63cc7c51d94d74` |
| `docs/milestones/cli-milestones.md` | `210987bac9d380997d054c815b63f55a08e9725ae2ad46147683b13bca21a44b` | Unchanged |
| `docs/milestones/execution-milestones.md` | `bc39a9a0fbd808f97f71e8adbb69aaa54ce1427300c7c427fd40e5d45aa882dc` | `1a159637542b65c1f279418bce08a827d91819862d933a18eaca5a640a6bf25f` |
| `docs/milestones/registration-milestones.md` | `eaff1a200da9a7d33eba1d0b7d027f324557651d93b73b2d75af3b7926628c92` | `a58460130a2fee7b34877b75e7f8e9a30a95347c65d35a3c386734c3c00748d1` |
| `docs/milestones/runtime-service-milestones.md` | `824ce8f547a39a374683e2414d3cd0089c308bddc9ab45a0a1506a7877252d25` | Unchanged |
| `docs/planning-guide/README.md` | `7dc1a70a362aef5331a4f75ca3acd66fbcb15e54bc715eaaeb0ad60ecb88efeb` | Unchanged |
| `docs/planning-guide/templates/milestone-declaration.md` | `ec0fdc48b92fdf7935af4f96268447ceef161322fda86811cd0a782ceeb117e3` | Unchanged |
| `docs/project-overview.md` | `a13167fedd928e6737dda5c11d98998a7750917c8241592e72bf518e0dcf0b1a` | `3dc554f060ac851f2e9dc3bed1430ab40815e5ab7d918e724c36767a24bdce88` |
| `docs/schemas/architecture-loop.schema.json` | `6bae8e665a2e407da7922af42e8377989b2e22f5a89227d26183191a505e5daa` | Unchanged |
| `skills/project-architecture-workshop/SKILL.md` | `c167c809ddbe921cdbcf1490643b59d75c8540bd54940e09cfe83726aa79e423` | Unchanged |
| `skills/project-architecture-workshop/references/planning-guide.md` | `fb48e5768e904e56643d13664e5de4e8daa92df499448fceec6e4c5d09c9ae9c` | Unchanged |
| `skills/project-architecture-workshop/references/reviews.md` | `84b9d32b891b194dd9ddbb983f8b2202a12a7f0c3004a3959aaceeb4d7031dd7` | Unchanged |
| `skills/project-architecture-workshop/references/workshop-state.md` | `40c296cd297f52e263a6e623aeb5f404ce1fa10211e6a0c5ef1285eb4e0769e0` | Unchanged |

All passes examined the entire new declaration and overview, the filtered checkpoint, Planning Guide/template, review method, and all Execution headings in Architecture. Applicable shared headings were: installed schemas and process handling; adapters/tool selection/transport/workspaces/assignment identity/supervision; implementation plans; performance/context/checkpoints; credentials, API/events, SQLite/ownership/transactions; CLI workspace/attention/questions/answers/reconnect; source/publication selection and registration reuse; architecture start, record/manifest contracts, confirmation/reconciliation; Owner grants and durations.

All passes examined runtime, CLI, registration and architecture-loop declarations for source/consumer responsibility and acceptance boundaries; coder, manager, integrator, independent reviewer, QA, architect and fidelity-reviewer roles for applicable authority. Completeness and consistency inspected all applicable foundation outcome sections and the role index; fidelity inspected their scope/outcome boundaries and architecture review/confirmation outcome, and did not use CLAUDE.md or the role index as decision evidence. Completeness read CLAUDE.md. Sources supplied but not used do not imply coverage.

Schema coverage: `workPacket`, `developmentMilestone`, `manifest`, `inventoryEntry`, `publishedRef`, `registrationRef`, `assignment`, `requiredOutput`, `startPayload`, `selection`, `specialist` and record-definition inventory for producer compatibility. Completeness additionally inspected `packetDeliverable`; consistency inspected `allocation`; fidelity inspected `request`, `setRef`, `projectStructure`. Schema existence was never treated as proof of installed compatibility.

#### Selection and shared-contract trace

For each applicable journey, all reviewers traced input, selecting actor, collection point, saved identity/provenance, validation and consumer separately. The corrected selection chains under targeted review are explicitly identified; no original full pass is represented as having checked their later bytes.

| Subject | Source, chooser and collection | Saving, checks and consumer | Controlling locations |
|---|---|---|---|
| Source and planning publication branch | Verified caller request/linked intake; documented source default or inherited selector; explicit or retained destination authority | SQL selector/resolved commit/branch/provenance, candidate decision and manifest; readability/authorization/current-input checks; exact assignments and journal destinations | Architecture — Source and publication selection; Source consistency; registration initial/update declaration |
| Registration architect and reviewer | Separate Owner tool/exact-model choices collected before architect launch; separate missing-choice questions | Separate SQL selections and requested/reported identity checks; architect assessment and independent reviewer assignments | Architecture — Tool and model selection; CLI request and event contract; registration initial acceptance |
| Architecture architect and reviewer | Separate explicit start-form choices | `startPayload.architect` and `.reviewer`, `selection.tool/model_id`; SQL/session bindings, exact-model/capability/independence checks; separate architecture assignments | Architecture — Persistent architect session; Architecture API operations; producer schema |
| Repository profile | Initial full review: missing producer, AC-1 / C2. Correction: operator provisions unique normalized repository binding; registration resolves before first read and validates branch after collection | Attempt profile/configuration/provenance and selection Decision; allowlists/access validated; confirmation activates project binding; publication/recovery inherit exact profile | Architecture — Source and publication selection; Adapter configuration; Execution configuration; registration initial/update acceptance |
| Product baseline | Initial full review: missing derivation, AC-2. Correction: service derives confirmed breakdown source, checks confirmed registration; observes current master separately at start | Atomic baseline/master-start commits, input references and time; source/current-input checks; lazy milestone branches and recovery consume pinned value | Architecture — Execution initiation; Milestone branches and product integration; Execution API/state contract |
| Development Manager | Owner selects installed named route at explicit start | Activity configuration/route/session snapshot, capability/access/exact-model checks; first manager launch and event-driven planning | Architecture — Execution initiation; Execution configuration; Development Manager preparation and continuity |
| Coder and specialist | Manager chooses permitted route/exact model/reason and applicable source-local specialist from confirmed inputs | Assignment saves exact packet/role/context/base; service validates capability subset, location, context minimum, concurrency, identity and applicability; coder launch consumes | Architecture — Work planning and coder selection; Planning results and questions; Specialist assignment and architectural support |
| Integration, packet/integration-change/milestone review, QA, milestone-gap roles | Separate installation-provisioned exact primary/backup pairs and positive role durations; service chooses eligible configured route | Activity snapshot and independent assignment/session evidence; actual identity/authority/preflight and cause-based fallback; corresponding run consumes | Architecture — Execution process definition and configuration; applicable role files |
| Support architect and fidelity reviewer | Separately configured exact primary/backup pairs and timeouts, selected by service | Assignment-created snapshot, separate sessions, authority/identity/independence checks, unchanged counts; bounded support and role review | Architecture — Architectural-support configuration and fallback; Support validation and publication |
| Branches, workspaces and destinations | Service-assigned identity/path patterns and exact recorded current base/target | Assignment/journal expected heads, paths, objects and credential reference; collision, permissions, graph, clean diff and remote checks; coder/integration/import/publication handlers | Architecture — Execution workspaces and repository writes; Milestone branches and product integration; API/state contract |
| QA plan, environment and evidence | Architect supplies reviewed/confirmed versioned plan; installation supplies routes, roots and limits; service allocates environment/artifact identities | Source/plan/configuration hashes, named test secrets/network/data paths and lineage; setup/health/isolation/capture/hash/reset checks; supervisor and authorized artifact retrieval | Architecture — Architecture record contract; Isolated Quality Assurance environment; architecture-loop breakdown/confirmation delivery |
| Owner grants, durations and disposition | Verified Owner chooses linked typed action; architect recommendation when required | Exact decision/target/version/grant or restriction, atomic validation/reservation/consumption; eligible review/retry/next-run/settlement consumes, never free text | Architecture — Owner decisions at a process limit; Run deadlines and duration exceptions; Work disposition before re-registration |

Shared storage trace: local SQLite, service-only writer, WAL/FULL, short serialized write transactions, atomic eligibility/reservations/state, and external Git/agent operations outside transactions. SQL receipt/events follow commit; Git intent precedes effect and verified remote bytes precede advancement. Physical tables remain delivery work. Locations: Architecture — SQLite storage; Record ownership; Save and delivery sequence; Execution API, state and record contract; runtime storage declaration.

Shared authority trace: protected local Owner credential for CLI actions, separate agent identities/tool profiles, and service-only repository credentials. No role output becomes an Owner decision; writer cannot approve its own work. Locations: Architecture — Local Owner identity and credentials; Adapter configuration; Execution workspaces and repository writes; role authority boundaries.

Shared settings comparison: Execution `execution@1` repository source and installed bundle path remain distinct; exact route/model values and positive role timeouts are installed choices. Packet/integration/milestone review defaults remain separate two-round limits; Execution recovery remains two automatic/one manual by default; support has its own configured budget. Context defaults remain 75/85/70 percent and 10/30 seconds; QA defaults remain one environment and 90 days post-close retention. Registration and architecture-loop tool/model fields and default durations are not silently inherited by Execution. Source and installed schema paths are compared literally in the cited contracts; deferred implementations are not claimed present.

#### Full journey coverage retained across the three passes

The following entries preserve all eight examined categories and their concrete locations. Each full pass assessed this same journey set for its distinct question: fidelity compared controlling decisions, completeness checked definitions/delivery ownership, and consistency compared declarations/roles/schema with those definitions. Status was defined/preserved at the decision level in fidelity; completeness/consistency recorded the explicit missing chains and incompatible producer shapes above. Those findings affect the indicated categories without erasing other covered categories. Corrected bytes are covered only by each later targeted record.

**Journey 1 — Start and persistent planning.** Architecture headings: Execution initiation; Execution process definition and configuration; Development Manager preparation and continuity; Planning results and questions. Compared delivery/role sources: Execution declaration — reviewed-packet outcome; Development Manager role — Initiation and inputs, Work planning, Persistent context.

- Starting conditions: Current confirmed registration/breakdown, no conflicting or uncertain work, configured access and eligible packet; foundation delivery explicitly required.
- Input and recipient: Owner start request to service, then exact saved inputs to Development Manager; understanding precedes work requests.
- Configuration and selections: Source and separate producer role selections, manager route, repository binding and product-baseline chains as traced above; missing binding/baseline recorded in full completeness.
- Credentials and authority: Authenticated Owner starts only confirmed scope; manager requests and service validates/reserves; no automatic startup from confirmation.
- Storage and transactions: Atomic single-activity reservation/configuration/input snapshot; persistent session, checkpoint and handled-event identities saved.
- Interfaces and state: Common request/idempotency plus execution.start/status and structured planning results; required producer packet input gap recorded.
- Results and completion: Real CLI/service/manager path yields saved understanding, priorities, blockers and visible questions; start is not packet completion.
- Failure and recovery: Repeated start opens existing activity; stale/ineligible/configuration/unknown-run requests cannot dispatch; checkpoint/current saved state governs continuation.

**Journey 2 — Coder preparation and exact published result.** Architecture headings: Work planning and coder selection; Returned implementation plan; Coder preparation and submitted results; Execution workspaces and repository writes. Compared delivery/role sources: Execution declaration — reviewed-packet outcome; Common Coding Agent Instructions.

- Starting conditions: Eligible reserved packet, adequate specialist, dependencies/capacity and assigned constrained workspace.
- Input and recipient: Manager route request to service; immutable packet/source/role/context to coder; plan and structured result back through service.
- Configuration and selections: Coder route/model/reason, packet capabilities/location/context and specialist paths checked separately; supplied producer execution_requirements gap recorded.
- Credentials and authority: Coder writes assigned paths and local commits only; privileged service publishes; no coder approval or merge.
- Storage and transactions: Plan saved before continuation; assignment/result/workspace and intended push journal retained; remote equality precedes success.
- Interfaces and state: Execution typed result binds revisions/files/checks/limitations; wrapper verifies base/branch/graph/allowed paths and clean output.
- Results and completion: Visible plan adds no approval gate; actual verified remote revision is only review-ready, not accepted packet.
- Failure and recovery: Conflicts/missing inputs block; invalid/stale output or changed remote head quarantines/reconciles without force or silent substitution.

**Journey 3 — Independent packet review and Owner limit action.** Architecture headings: Independent implementation review; Packet and integration-change review limits; Owner decisions at a process limit. Compared delivery/role sources: Execution declaration — reviewed-packet and architectural-correction criteria; Independent Implementation Reviewer role; coder Corrections.

- Starting conditions: Exact submitted revision/evidence, non-author reviewer and separate read-only checkout.
- Input and recipient: Service supplies packet/code/architecture/rules/evidence; findings return through manager to coder or architectural attention.
- Configuration and selections: Separate packet-review route/timeout and saved default-two completed-round limit; typed Owner action binds exact review.
- Credentials and authority: Reviewer cannot edit/dispatch/merge; architect recommends at limit; only verified Owner grants allowance.
- Storage and transactions: Exact findings/revisions/count/base/grants retained; decision validation and grant save atomic.
- Interfaces and state: Validated review result and execution_packet_review target with grant_one/remain_paused; free text cannot grant.
- Results and completion: Passing exact revision becomes integration-eligible; targeted correction retains unaffected coverage; no approval at exhausted limit.
- Failure and recovery: Malformed/interrupted output consumes no completed round; replacement/rename/recovery never resets counts; unrelated eligible work continues.

**Journey 4 — FIFO integration and branch delivery.** Architecture headings: Integration management and queue; Milestone branches and product integration; Authorized integration merges; Packet and integration-change review limits. Compared delivery/role sources: Execution declaration — integration outcome; Integration Manager role; independent reviewer role.

- Starting conditions: Independently approved exact packet at durable project FIFO head; one active integration across milestones.
- Input and recipient: Service supplies exact packet/current target to persistent Integration Manager; own changes go to independent review.
- Configuration and selections: Independent configured integration/reviewer routes, assigned integration branch/current head; original baseline/profile gaps recorded.
- Credentials and authority: Manager makes in-scope local connection fixes; service alone performs authorized credentialed merge after review.
- Storage and transactions: Durable sequence/source/target/counts and intent journal; remote verification required for advancement.
- Interfaces and state: Fixed integration/milestone branch patterns; exact reviewed head; non-fast-forward merge; separate integration-change accounting.
- Results and completion: Verified milestone result resolves head; no-change integration retains evidence without automatic duplicate packet review.
- Failure and recovery: Blocked head cannot be skipped; only authorized resolved dispositions remove it; changed targets require reconciliation/affected review.

**Journey 5 — Missing specialist and role activation.** Architecture headings: Specialist assignment and architectural support; Architectural-support configuration and fallback; Support validation and publication. Compared delivery/role sources: Execution declaration — architectural-correction outcome; architect and fidelity-reviewer support responsibilities.

- Starting conditions: No adequate role for named packet; completed architecture session is not assumed running.
- Input and recipient: Service bounded assignment supplies exact packet/roles/architecture; new role/context goes to separate independent reviewer.
- Configuration and selections: Separate support architect/reviewer selection chains and assignment-created snapshots; service-assigned allowed paths and source refs.
- Credentials and authority: Architect cannot change confirmed scope/responsibilities or dispatch; new-role reviewer independent; service publishes.
- Storage and transactions: SQL working state/counts/route history; immutable support/review/activation records; verified remote bytes then atomic binding.
- Interfaces and state: Use-existing/create-role/replanning dispositions and exact role/context inventory; coder consumes original confirmed plus activated binding.
- Results and completion: Existing unchanged role needs applicability check; new role needs review and verified activation before manager reconsideration.
- Failure and recovery: Invalid ownership/paths/stale inputs block; cause-based fallback preserves counts and requires stopping; no verdict-shopping or silent overwrite.

**Journey 6 — Milestone finding and correction supplement.** Architecture headings: Milestone outcome review; Milestone-gap architectural assignment; Correction-supplement activation. Compared delivery/role sources: Execution declaration — architectural-correction and milestone-verification outcomes; architect milestone-gap responsibilities.

- Starting conditions: Actual QA/outcome-review finding and remaining allowances; separate bounded assignment, not missing-role support.
- Input and recipient: Service supplies exact branch/registration/breakdown/QA/finding/dependency/supplement/work state to read-only architect.
- Configuration and selections: Separate milestone-gap route/timeout and service-assigned supplement identity/version; inherited publication binding.
- Credentials and authority: Architect determines defect/supplement/re-registration only; cannot approve, dispatch or change scope; valid in-scope supplement adds no approval gate.
- Storage and transactions: SQL working/active supplement; external final-byte hash and journal; verified publication before atomic activation/releases.
- Interfaces and state: Typed disposition and bounded payload include exact finding/paths/ownership/dependencies; original breakdown preserved.
- Results and completion: Actual finding-to-determination-to-correction/verification journey; implementation defects to Integration, valid missing work through normal lifecycle.
- Failure and recovery: Duplicates/cycles/stale findings/changed outcomes reject; replay idempotent; started version immutable and review counts unchanged.

**Journey 7 — Dependency import and invalidation.** Architecture headings: Dependency readiness and automatic continuation; Milestone branches and product integration; Execution API, state and record contract. Compared delivery/role sources: Execution declaration — integration outcome; manager/integrator roles; schema packet/milestone dependencies.

- Starting conditions: Provider packet reviewed and integrated; accumulated source set within declared consumer dependency closure.
- Input and recipient: Confirmed dependency semantics and exact providing commit/set to service FIFO import then Integration Manager.
- Configuration and selections: Architect declares closure; service binds current source/consumer/import branch; initial baseline/profile gaps recorded.
- Credentials and authority: No undeclared code or promotion-order override; new integration changes independently reviewed; service owns merge.
- Storage and transactions: SQL delivery/source/import/readiness and atomic transitive invalidation; external merge journal retained.
- Interfaces and state: FIFO dependency_import and fixed dependency branch; verified non-fast-forward consumer head becomes dependent packet base.
- Results and completion: Exact imported objects establish readiness; provider promotion precedes consumer except confirmed outcome assignment.
- Failure and recovery: Ineligible imports wait; source changes invalidate affected starts/merges/QA/review; running results quarantine; replacement import/affected checks preserve history.

**Journey 8 — Isolated milestone QA and evidence.** Architecture headings: Architecture record contract; Milestone Quality Assurance and test data; Isolated Quality Assurance environment. Compared delivery/role sources: Execution declaration — milestone-verification outcome; architecture-loop breakdown/confirmation; QA role; supplied producer schema.

- Starting conditions: Assembled exact milestone and confirmed QA plan with real setup/data prerequisites; producer-schema gap explicitly found.
- Input and recipient: Architect plan to service supervisor/QA; actual data source, entry and result paths plus expected outcomes supplied.
- Configuration and selections: Installed QA route/roots/limits and confirmed scripts/health/ports/test-secret/network/data/artifact plan; service saves exact hashes/identities.
- Credentials and authority: Separate storage/test credentials, named network dependencies, no automatic production access; QA cannot alter acceptance or approve code.
- Storage and transactions: Service SQL run/lineage/artifact state; temporary capture/size/secret/hash checks and atomic artifact publication; retention/tombstone records.
- Interfaces and state: Exact source/plan/config/process/health and expected/actual results; PASS/FAIL/UNTESTED plus cleanup state and artifact metadata.
- Results and completion: Actual connected required paths and retrievable evidence; generated input cannot manufacture expected result; milestone-level only.
- Failure and recovery: Missing/bypassed required path stays UNTESTED; absent/corrupt artifact invalidates affected check; failed cleanup/reset quarantines; affected rerun after remedy.

**Journey 9 — Outcome review, promotion and successful closure.** Architecture headings: Milestone outcome review; Authorized integration merges; Dependency readiness and automatic continuation; Execution completion and recovery. Compared delivery/role sources: Execution declaration — milestone-verification outcome; independent reviewer and integrator roles.

- Starting conditions: Assembled milestone, exact outcomes/dependencies/current QA evidence and fresh non-author/non-integrator reviewer.
- Input and recipient: Service supplies branch/outcome/evidence to reviewer; findings to bounded architect; eligible promotion to service.
- Configuration and selections: Separate milestone review route/limit, exact branch/current master and assigned completion identities; no inherited planning review budget.
- Credentials and authority: Standing authorized promotion and closure require no new Owner approval; no self-approval/protection bypass; service Git credential chain applies.
- Storage and transactions: Exact gate/import/review/merge references; immutable completion bytes remotely verified before SQL completion.
- Interfaces and state: Milestone completion path and execution-completion@1/kind completed; all authorized milestones and no active/uncertain work required.
- Results and completion: Both no failed/unverified QA path and passing outcome review permit verified merge; eligible continuation and final CLI summary follow saved evidence.
- Failure and recovery: Blocking findings stop affected promotion/dependants; stale target causes affected reconciliation; lost publication receipt reconciles same version, conflicts pause.

**Journey 10 — Pause, stop, re-registration and recovery.** Architecture headings: Pause and graceful-stop settlement; Work disposition before re-registration; Execution completion and recovery; Owner decisions at a process limit; Run deadlines and duration exceptions; Checkpoints and safe continuation. Compared delivery/role sources: Execution declaration — lifecycle outcome; registration update; architecture confirmation/reconciliation; shared CLI reconnect.

- Starting conditions: Existing current activity, eligible paused/failed action; intervention/grant/stopping prerequisites; idle-only later re-registration.
- Input and recipient: Explicit CLI lifecycle or typed Owner disposition to service; managers/supervisors receive saved restrictions; subsequent starts remain separate.
- Configuration and selections: Original model/configuration/source/deadline/allowances retained; exact grant and next-run exception bound; capacity continuation retains remaining active time.
- Credentials and authority: Credential-verified Owner authorizes; service enforces and confirms stopping; prose/recommendation alone grants nothing.
- Storage and transactions: Atomic exact settlement set/restrictions and grant reservation/consumption; restart reloads sessions/queue/journal/environment/artifacts.
- Interfaces and state: Pause/resume/stop/retry and typed dispositions; held/unfinished entries; execution-stop@1/kind stopped separate from successful record.
- Results and completion: Only permitted downstream stages settle; pause becomes resumable or verified stopped closure lists unfinished work; idle readiness requires reconciliation.
- Failure and recovery: No outside packet/supplement or FIFO skip; unknown effects block replacement/closure; counters/deadlines preserved; unsafe context/cleanup pauses or quarantines.

Cross-journey monitoring compared Architecture — CLI workspace; Attention; Questions and answers; Answer identity and uncertain delivery; CLI request and event contract; Performance records; Visibility and delivery boundary against both CLI outcomes and each Execution stage. SQL-backed facts distinguish agent progress, verified results and unknown/stale telemetry. Viewing does not acknowledge or authorize; exact linked answers are saved before receipt/delivery; snapshot/event cursor and reconnect restore state without mutation replay or implied stopping. No notification policy was reopened.

#### Targeted correction records

| Record and subject | Parent full record | Reviewer | Mode, round and conclusion |
|---|---|---|---|
| execution-declaration-fidelity-2 — Fidelity of prerequisite and wording corrections | execution-declaration-fidelity-1 — Execution project milestone declaration | `/root/execution_milestones_fidelity` | Targeted, round 2: pass, no findings; original full fidelity retained |
| execution-milestones-completeness-targeted-2 — Execution prerequisite correction check | execution-milestones-completeness-full-1 — Execution milestone prerequisite and delivery completeness | `/root/execution_milestones_completeness` | Targeted, round 2: pass; all three completeness findings resolved |
| execution-declaration-consistency-2 — Targeted Execution prerequisite corrections | execution-declaration-consistency-1 — Execution declaration and connected source consistency | `/root/execution_milestones_consistency` | Targeted, round 2: pass; all four consistency findings resolved; baseline clarification consistent |

All targeted records have `coverage_complete: true`, `round_consumed: true`, no unresolved findings and no invalidated broader coverage. Reviewer independence and original exclusions remain unchanged. Scope is the named corrections and directly affected dependencies only. Correction references are the corrected source hashes above, manifest `2909e5ddc586ca8b0e8162969b2f20a44ed35f2ead4313635d5876a48c54b693`, instruction hash `698a87f0ea03cbf85f6df667d9249168931b1bacac63c61d7e64725d695e541b` and exact delta hash `a07eb65632f0b39f878fe6e02d11503e35cc963c147fa110cb5f13b1cee0b5f2`. Each reviewer verified the corrected packet bytes. The following affected trace was completed separately by each reviewer for its pass type.

| Trace category | Repository-profile correction | Product-baseline correction | Producer-schema delivery correction |
|---|---|---|---|
| Starting conditions | Unique configured binding before first read; initial registration acceptance owns missing/ambiguous binding rejection | Confirmed matching registration/breakdown and accessible source before start | Producer extension required before affected confirmation/consumption |
| Input and recipient | Operator mapping to registration service, then saved attempt/confirmed profile to publishers | Existing registration source choice to service derivation; separate master observation | Architect packet/milestone/QA inputs to extended producer validation/publication, then Execution consumers |
| Configuration and selections | Operator chooser; TOML keys; intake collection; SQL/Decision/provenance; unique/known/profile/credential/allowlist/access checks; exact inherited consumer | Original Owner source selection; pinned producer commits; start derivation/observation; saved commits/references/time; equality/object/current-input checks; branch/recovery consumer | Existing semantic fields, service identities and confirmed plan selections; explicit schema/allocation/inventory delivery; validation before consumption |
| Credentials and authority | Service-held credential references; existing publication authorization remains separate; no agent/Execution override or added approval | Observed master grants no new source authority; existing re-registration path owns baseline change | Existing architect/service/reviewer/Owner responsibilities retained; no startup or acceptance bypass |
| Storage and transactions | Attempt profile saved, Decision retained, activation after publication; prior active binding retained during update | Both commits and input provenance saved in start transaction; recovery consumes saved facts | Existing exact paths/manifests/hashes/SQL working/confirmed references; extension includes producer publication |
| Interfaces and state | Named configuration binding maps to attempt and confirmed project field, then activity/journal; registrationRef remains unchanged | Confirmed source_commit distinct from product_master_start_commit and later publication/branch heads | Supplied executable schema omissions explicitly retained as delivery work; no claim of present compatibility |
| Results and completion | Actual initial/update acceptance binds saved exact profile; availability alone is insufficient | Declaration start evidence includes both commits; branch and completion use correct lineage | Breakdown requires real validated/inventoried/hashed/published set; confirmation and Execution require it |
| Failure and recovery | Missing/duplicate/unknown/incompatible mapping rejects; original operation profile retained on recovery; changed binding activates only after replacement confirmation | Missing/inconsistent/current-input failure blocks; changed target reconciles; changed approved baseline requires existing confirmation path | Missing extensions cannot produce confirmed usable inputs; existing stale/publication/recovery checks apply; no fabricated QA plan |

Canonical locations for the table are Architecture — Source and publication selection, Adapter configuration, Execution initiation, Architecture-loop implementation boundary, Architecture record contract, Confirmation and activation, Milestone branches and product integration, Execution completion and recovery; registration initial/update acceptance; architecture-loop foundation/breakdown/confirmation; Execution reviewed-packet and QA dependencies; overview Current state. All three checks examined these changed locations and directly affected original definitions.

Targeted mapping to the ten retained journeys: start/coordination gained defined profile, baseline and producer prerequisites; coder delivery gained exact baseline/profile and assigned packet-schema inputs; packet review retained its rules with stale coder wording removed; integration gained explicit baseline/profile origins while FIFO/merge behavior stayed fixed; specialist and supplement publication inherited the clarified profile; dependency delivery retained exact branch/import lineage; QA gained explicit producer-plan/schema ownership; milestone promotion/closure retained its gates with separate baseline/master evidence; lifecycle/re-registration retained original operation bindings and explicit activation/change authority. Each unaffected category retains its full-pass location and explanation rather than claiming another full review.

The two wording corrections were checked against the existing authoritative contracts: Common Coding Agent Instructions — Corrections now references established configured accounting without another allowance; Architecture — Agent performance and context management references the defined Qwen adapter while retaining unimplemented/installed status and role-selection exclusions. Declaration and milestone versions match the checkpoint's metadata.

The final review conclusion for each pass is no gaps found within its recorded coverage. This is documentation readiness, not executable-schema compatibility, installed capability or operating evidence. The unchanged producer schema still requires its explicitly assigned extensions during delivery. Review-result bookkeeping appended after the frozen substantive snapshot was self-checked against the actual independent outputs; it is not represented as an additional independent pass.

#### Limits and next action

Full historical conversation fidelity, unrelated registration/architecture internals, source audit, installed tools/accounts/configuration, executable validation, physical SQL implementation and live runtime behavior were not assessed. Foundation processes were examined only for relevant setup, selections, authority, producer/consumer contracts, confirmation and recovery transitions. Command center/mobile, unsolicited conversation, configurable hooks, SQL backup/restore and unauthorized production testing remain excluded. There is no operational readiness or successful registration claim.

The declaration and its prerequisite alignment have completed the required independent documentation reviews. Delivery remains directly to master under repository policy. The next planning step is selecting the registration scope and producing its later development breakdown through the established process; these have not been started. This documentation does not start implementation or Execution.
