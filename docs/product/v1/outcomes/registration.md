# Registration outcomes

## Capability and scope

The outcome area delivers project registration through the CLI: source intake, mechanical checks of the planning documents against the workshop's rules file, a check of the workshop's independent review record, a small versioned registration record in GitHub, explicit activation, re-registration, and recovery of interrupted publication. The workshop does the interpretation, the questions to the Owner and the independent review before registration. Current-state evidence belongs in the [project overview](../project-overview.md). The registration process is described in [the registration process](../../../../skills/maestro-workshop/process/registration-process.md).

Registration uses Apply shared process definitions for common initiation, output handling, confirmation, and recovery dispatch. Registration owns its record schema, eligibility, the rules check, publication and activation policies, and process-specific handlers; shared mechanics are not reimplemented here. Registration launches no agents.

Implemented runtime interfaces and CLI foundation precede registration integration. The [Runtime Service outcomes](runtime-service.md) owns service installation, storage and request mechanisms, API transport, and start reservations. Registration owns eligibility, the rules check, the record schema, publication and activation, and their actual use of those runtime capabilities. Command center, project implementation, automatic development start, development breakdown, full code audits, and execution-rule overrides are excluded.

Verification follows `skills/maestro-workshop/process/planning-guide.md#verification-expectations`: real data and connected operation, a basic main journey and essential failures, and no exhaustive outcome-by-outcome test suite. Evidence can cover several criteria in one journey. Fake data is used only when necessary with the reason recorded.

The complete registration capability requires all three outcomes below. Initial registration completion does not establish re-registration or interruption recovery.

Completion evidence for each outcome identifies the implementation revision, reproducible setup, observed main journey, and essential failures. Delivery-review roles, acceptance authority, isolated Quality Assurance, promotion and completion follow the defined [Execution architecture](../architecture.md#execution) when this work is later executed.

## Outcomes

## Register and confirm a project through the CLI

**Outcome:** A whole project or defined portion reaches explicit confirmation and a retrievable registration record through the real CLI and service.

**Included:** Overview-based intake, the rules check, the check of the workshop's review record, scope confirmation, record publication, exact-candidate confirmation, and cancellation.

**Excluded:** Re-registration history changes, service interruption recovery, the workshop's interpretation and review, command center, and development execution.

### Architecture and journeys

| Required behavior or journey | Architecture section |
|---|---|
| Register a project or selected portion | `docs/product/v1/architecture.md#register-a-project-or-selected-portion` |
| Project entries, activities, and visible labels | `docs/product/v1/architecture.md#project-activities-and-registration-labels` |
| Inputs and overview entry | `docs/product/v1/architecture.md#source-format-and-inputs` |
| Source consistency | `docs/product/v1/architecture.md#source-consistency` |
| Source revision and authorized publication destination | `docs/product/v1/architecture.md#source-and-publication-selection` |
| Identity and ordering | `docs/product/v1/architecture.md#identity-and-ordering` |
| Actual publication checks | `docs/product/v1/architecture.md#agent-delegation` |
| Checking the documents | `docs/product/v1/architecture.md#checking-the-documents` |
| The rules file | `docs/product/v1/architecture.md#the-rules-file` |
| Registration record and activation | `docs/product/v1/architecture.md#registration-record` |
| Guarded confirmation and cancellation | `docs/product/v1/architecture.md#comparison-activation-and-cancellation` |

### Dependencies

| Required dependency | Reference | Current state or delivery responsibility |
|---|---|---|
| Shared process handling | Apply shared process definitions | Implemented common handlers support registration; registration supplies its exact schemas and policies. Final runtime acceptance shares the connected process evidence. |
| CLI foundation | Reliable project questions and answers, following Connected multi-project CLI workspace | Implemented workspace and answer interfaces precede development; final connected acceptance is shared here. Prior final acceptance of those integrated CLI journeys is not a prerequisite. |
| Project sources and rules | `skills/maestro-workshop/process/planning-guide.md`; `skills/maestro-workshop/process/registration-rules.json` | The document structure and the rules file are specified. The loader that reads the rules file is included implementation work. |
| Runtime records and API | Preserve project activity and requests; Connect the CLI to recorded service activity | Runtime Service implements shared storage and request delivery. Registration uses them and verifies their use. |
| Registration repository access and publication | `docs/product/v1/architecture.md#agent-delegation`; `docs/product/v1/architecture.md#publication-and-sql-consistency` | Current operation unverified. Registration owns source access, record publication credentials and journal, wrapper publication checks, and SQL/GitHub activation consistency; generic SQL persistence is supplied by Runtime Service. |
| Record storage and activation | `docs/product/v1/architecture.md#registration-record` | The record, its locations, publication and activation are specified in the architecture. Executable schemas and connected persistence are included implementation work. |

### Acceptance criteria

| Expected result and conditions | Pass boundary | Verification and evidence | Accepted exception | Result |
|---|---|---|---|---|
| Source and publication choices are established | Intake resolves and records source, destination and the operator-configured repository-profile binding using `docs/product/v1/architecture.md#source-and-publication-selection`; checks and published records use those exact selections. | Real intake shows defaults or supplied choices, recorded authority and commit, and matching candidate references. Include essential unresolved-ref, unauthorized-destination or missing/ambiguous-binding rejection evidence; no silent fallback or exposed credentials. | None | Done 2026-09-24. Revision cb8cd78 on feature/register-and-confirm (merge revision recorded at acceptance in the handoff). Real intake against the private QA repository `jmiedreich-ux/Maestro-qa` refused an unbound repository, short ref, unresolved ref, branch outside the allowlist, missing branch, protected branch, absent overview, missing source fields and an unsupported model, each with a named reason and no project created (`var/qa/registration-live/intake-rejections-evidence.json`). Missing choices became questions; `main` was suggested but refused until an allowed branch was named (`var/qa/registration-live/gap-evidence.json`). Binding rules (missing, unknown profile, ambiguous) are in `tests/maestro/service/test_registration.py`. |
| The Owner follows startup and access instructions | The preceding CLI/service foundation is available, and the registration process reaches the project repository using real authorized access. No missing service account or unpublished manual command is needed to reach intake. | Startup and connection evidence from the AI box, including access to the running service; record configuration references without secret values. | None | Done 2026-09-24. Real service run as the `maestro` user with the GitHub App key from the credential directory (no secret values recorded) and the installed Codex and Claude Code routes; the terminal connected with the Owner token file. Setup steps are in `services/maestro/deploy/README.md` (Registration configuration); the scripts are `var/qa/registration-live/setup.py` and `var/qa/registration-live/start.sh`. |
| The planning documents are submitted and checked against the rules file | The explicit repository-relative overview path locates the architecture and the roadmap. The service applies the rules file version pinned for this registration to every document at the pinned revision. A failed rule stops registration with a plain report of which rule failed, in which document and where. | The rules file version, the source commit, an accepted check, and a rejected example that names the rule and document. Change one rule in the file and show the result change with no code change. | None |  |
| Whole-project or partial-project scope is selected | The interpreted boundary is presented for explicit scope confirmation. The record holds the included outcomes, explicit exclusions and outside dependencies. A missing essential dependency in the workshop's review record stops registration with a report, not a silent scope expansion. | Inspect the presented boundary, the recorded scope confirmation and the record's boundary. Scope confirmation is distinct from final registration activation. | None |  |
| The workshop's independent review record is checked | The service checks that the review record exists, covers exactly the pinned revision by document fingerprint, that no document changed afterwards, that its coverage is complete, and that it records a reviewer other than the author. The service does not review the plan itself. | A passing record, and rejected examples for a missing record, a changed document and incomplete coverage. No invented approval. | None |  |
| The Owner understands a failed check and can act on it | The CLI shows the current step, the pinned revision, the rules version and the check result. A failed check shows a plain report and saves it with the pinned revision, and the next workshop session reads that report first. Answering or viewing a report does not confirm registration. | Connected CLI records of a failed and a passing check, the saved report, and a workshop session that opens with it. | None |  |
| A second registration request arrives for the same project | The CLI shows the existing active process; no competing process or new registration version is created. | Submit duplicate CLI requests and inspect the single activity and candidate. A request for another project remains separately addressable; its questions and decisions cannot be applied to this project. | None | Done 2026-09-24. A repeated start returned the existing activity (`duplicate: true`, one activity for the project); the terminal reopened it with 'already in progress'. A second project ran at the same time, and answering its question inside the first project was refused with 409 (`var/qa/registration-live/partial-evidence.json`, `var/qa/registration-live/tui-confirm-evidence.json`). |
| Relevant planning inputs change before confirmation | Before confirmation, the Owner sees the change and chooses to retain the checked source or check the updated source. The updated revision is checked again and the workshop's review record must cover it. Unrelated commits or report updates do not count as input changes. | Before-and-after source references, the Owner's choice, the resulting candidate, and the recheck. | None |  |
| A candidate is ready for confirmation | The registration record holds the pinned revision, the document fingerprints, the rules version, the review record reference and the scope. It contains no copy of the plan and no generated development breakdown. | Inspect the record against its contract in [registration record](../architecture.md#registration-record); validate required fields, hashes and references. | None |  |
| The Owner confirms through the CLI | Only explicit confirmation makes the exact unchanged, eligible candidate active. Changed or ineligible candidates require renewed inspection before confirmation. That version is available in the project's GitHub repository; confirmation does not launch development. The confirmed contents cannot silently change afterward. Publish and verify the confirmation receipt before SQL activation; pending confirmation retains the prior active version and prevents competing changes. | Owner confirmation tied to the candidate, authoritative GitHub commit and record location, active-version record, and evidence that no development was started. Required wrapper checks verify repository, branch, allowed files, remote commit existence, and agreement with the reported commit before publication is counted as successful. | None |  |
| Registration is cancelled or action acknowledgment is lost | Explicit cancellation ends the attempt after its external operations are resolved, with saved history retained. Pending confirmation rejects competing cancellation. Cancellation during candidate publication prevents advancement while the write is reconciled. Confirmation/cancellation are deliberate view actions, not ordinary text submission. An uncertain result shows Outcome not confirmed; reconnect queries the saved outcome and explicit retry cannot duplicate effects. | Main cancellation path and a necessary lost-acknowledgment case using the actual service. | None |  |

### Definition of done

The real CLI registration journey supplies evidence for every criterion: source reading, the rules check, the review-record check, a retained plain report for a failed check, exact record publication, and deliberate confirmation. Basic essential-failure evidence establishes rule failure, a missing or stale review record, stale-candidate protection, and uncertain-action handling; criteria can share one journey.

The confirmed JSON record is retrievable in GitHub and usable by the next process without relying on mutable latest files. Fake-data screens or fabricated approvals cannot demonstrate registration. No development breakdown or work start occurs.

### Unresolved details

| Missing detail | Effect on the outcome | Clarification needed |
|---|---|---|
| Rules-file loader | Registration must read the workshop's rules file instead of its hardcoded checks. | Implement the loader, version pinning per registration and the CLI check for a newer approved version, as described in [the rules file](../architecture.md#the-rules-file). |
| Record layout and rejection report | The exact file layout of the registration record, and how the workshop reads a saved rejection report, are not yet specified. | Settle both when this is built. |
| Registration process-definition binding | The configured recovery limit must survive changes and recovery. | Implement [registration process-definition binding](../architecture.md#registration-process-definition-binding), including effective defaults, installed configuration validation and saved activity snapshots. |
| Output and persistence implementation | The record contract needs executable validation and durable publication. | Implement `docs/product/v1/architecture.md#registration-record` and `docs/product/v1/architecture.md#publication-and-sql-consistency`; validate the actual connected journey before completion. |

## Update a registration without losing approved history

**Outcome:** An idle project can revise registration coverage or its outcomes while preserving prior approval and controlling exactly what becomes active.

**Included:** Idle-only entry, prevention of new work during re-registration, version history, comparison, a new check of the documents, confirmation, and cancellation.

**Excluded:** A full execution engine or authorization to rewrite source plans or break down development work.

### Architecture and journeys

| Required behavior or journey | Architecture section |
|---|---|
| Update a registration | `docs/product/v1/architecture.md#update-a-registration` |
| Idle-only entry and versions | `docs/product/v1/architecture.md#re-registration` |
| Changes, confirmation, and cancellation | `docs/product/v1/architecture.md#comparison-activation-and-cancellation` |
| Source versions | `docs/product/v1/architecture.md#source-consistency` |

### Dependencies

| Required dependency | Reference | Current state or delivery responsibility |
|---|---|---|
| Initial registration | Register and confirm a project through the CLI | Required preceding outcome. |
| Real project-work state and new-start prevention | Preserve project activity and requests | Runtime Service supplies atomic state/reservation mechanisms. Registration owns idle eligibility and reservation lifetime and verifies the connected boundary. No full execution engine is assumed. |

### Acceptance criteria

| Expected result and conditions | Pass boundary | Verification and evidence | Accepted exception | Result |
|---|---|---|---|---|
| Registration is rerun | Inherited or amended selections follow `docs/product/v1/architecture.md#source-and-publication-selection`; the chosen source and configured repository binding are resolved for the new attempt while the prior active version retains its own selections. A profile change is shown and becomes active only with replacement confirmation. | Saved selectors, resolved commits, authorization and before/after active references; failed intake does not alter the prior package. | None |  |
| Project work is active | Re-registration cannot begin until all active work finishes or is explicitly stopped. The idle check and registration reservation are atomic. Reserved starts, unfinished waiting work, pending external operations, and uncertain runs prevent entry with named reasons. Once re-registration begins, only that registration's assignments and operations may start until it ends; other projects continue normally. | Runtime work-state evidence, a rejected re-registration request through the CLI, and a rejected new-work attempt at the service boundary. The work-state and start-inhibition connection is an explicit dependency, not a checkbox supplied by the reviewer. | None | Done 2026-09-24. With unfinished work running, the update request was refused 409 `project_not_idle` naming the activity, and no reservation was left (`var/qa/registration-live/update-evidence.json`). While updating, a second start returned the same activity and the `re_registration` reservation was held. Refusal of a new agent run for the reserved project is proven by unit test (`test_reservations.py`), not live. Pending external writes and uncertain runs are also unit-tested only. |
| An idle project is re-registered | Create the next registration version while preserving previous versions. The documents are checked at a newly pinned revision under the same rules, and the workshop's review record must cover it. | Successive version folders, pinned revisions, rules versions and the check results. | None |  |
| A candidate differs from the active version | Show the differences from the active version: the pinned revision, the documents whose fingerprints changed, the scope and the rules version, with the reason for each change where the workshop's review record gives one. | Comparison visible before confirmation, tied to the exact candidate. The project remains Registered with Updating registration displayed while the prior version stays active. | None |  |
| The Owner confirms the candidate | The candidate becomes active only on explicit confirmation of the unchanged eligible version shown. Previous records remain retrievable, and a new registration version is created. | Confirmation, version references, and GitHub history comparison. | None |  |
| Re-registration fails or is cancelled | The previous registration remains active. Project work does not automatically restart. | Failure or cancellation record, unchanged active-version reference, and observed stopped-work state. | None | Done 2026-09-24. Cancelling the first update left the project Registered with `cand-1416c686d8` still active, reservations 0, and no work restarted (`var/qa/registration-live/update-evidence.json`). Accepted exception from the independent Codex review: cancelling while the candidate is mid-publication is not reconciled and can leave the reservation held; not exercised live. |

### Definition of done

The connected re-registration journey and essential rejection/cancellation paths establish all criteria with preserved GitHub history, explicit comparison, and exact-candidate activation. Work-state enforcement must use actual service state; a reviewer checkbox is not proof. The prior version remains available, and project work never restarts automatically. Completion evidence and delivery reviews meet the common completion requirements above.

### Unresolved details

| Missing detail | Effect on the outcome | Clarification needed |
|---|---|---|
| Work-state enforcement implementation | The defined idle check requires actual activity and run state. | Use the atomic project start lock supplied by Preserve project activity and requests. Implement registration eligibility and reservation lifetime under `docs/product/v1/architecture.md#re-registration`, including pending, waiting, and uncertain work. |
| Candidate and active-version implementation | Published receipts and SQL activation must reconcile without replacing prior approval early. | Implement `docs/product/v1/architecture.md#confirmation-and-activation`, including pending confirmation and conflicts. |

## Recover registration without losing decisions or exceeding limits

**Outcome:** Interrupted registration resumes from verified work or pauses visibly without losing results, duplicating effects, or exceeding its limits.

**Included:** Registration integration with Runtime Service checkpoints and technical limits; registration publication wrapper checks and interrupted-publication reconciliation; preserved check results and initial/re-registration continuity. Generic supervisor and retry mechanisms are delivered by Runtime Service.

**Excluded:** Unlimited retries, forced approval, and unrelated execution recovery.

### Architecture and journeys

| Required behavior or journey | Architecture section |
|---|---|
| Recover an interrupted registration | `docs/product/v1/architecture.md#recover-an-interrupted-registration` |
| Recovery and limits | `docs/product/v1/architecture.md#technical-recovery` |
| GitHub wrapper verification | `docs/product/v1/architecture.md#agent-delegation` |
| Uncertain action outcome | `docs/product/v1/architecture.md#comparison-activation-and-cancellation` |

### Dependencies

| Required dependency | Reference | Current state or delivery responsibility |
|---|---|---|
| Registration journeys | Register and confirm a project through the CLI; Update a registration without losing approved history | Required connected predecessors. |
| Shared configured recovery | Apply shared process definitions | Registration retains the publication journal and activation semantics; shared handlers apply its policy and recorded definition without resetting budgets. |
| Durable checkpoints and remote evidence | `docs/product/v1/architecture.md#technical-recovery` | CLI request identity is defined in `docs/product/v1/architecture.md#answer-identity-and-uncertain-delivery`; publication reconciliation is defined in `docs/product/v1/architecture.md#publication-recovery`. The automatic recovery default is two attempts per publication operation. |

### Acceptance criteria

| Expected result and conditions | Pass boundary | Verification and evidence | Accepted exception | Result |
|---|---|---|---|---|
| An interrupted publication resumes | Recovery retains the journaled source and branch under `docs/product/v1/architecture.md#source-and-publication-selection`, even if branch heads or repository defaults change. | Correlate saved selections and resumed operation with the verified remote target; no new source resolution or target substitution. | None | Done 2026-09-24 at f25c6b9 plus review fixes. A publication refused because its branch was not allowed paused with Retry publication; after the service restarted with the branch allowed, Retry publication published the same journaled candidate (commit `e2af11af35fc`), and no agent was rerun (`var/qa/registration-live/recover.out`, `recover-evidence.json`). |
| A push fails or the service restarts | Preserve completed check results and the pinned revision. Resume from the last verified step; unverified results are not treated as completed. | Before-and-after records for each interruption, resumed step, retained exact source and candidate versions, supervisor reconciliation, and confirmation that no duplicate or child run remains. | None |  |
| A delegated operation requires a GitHub commit | The wrapper checks the expected repository and branch, committed and pushed changes, remote commit existence, permitted changed files, and agreement with the reported commit. A local commit or agent assertion alone cannot pass. Read-only reviews do not require unnecessary commits. | Wrapper results and remote GitHub evidence for successful publication and a deliberately unsuccessful publication. Verify lost-write acknowledgment and interrupted SQL activation without a duplicate confirmation, repeated Owner approval, or architect rerun. | Recorded in Result | Done 2026-09-24. Real commits on the qa branch: the refused publication wrote nothing, then the retry wrote one commit and confirmation one receipt commit (`var/qa/registration-live/recover.out`, `recover-evidence.json`). Accepted exception from the independent Codex review, detail outside the result: verification checks commit existence and file bytes but not the commit's changed paths. |
| Publication retries occur | A configurable limit, default two automatic recovery attempts, applies per publication operation after the initial write. Retries follow the architecture's failure classification; intervention-dependent or unknown causes pause without exhausting attempts. At the limit, registration pauses and explains the failure. Manual Retry publication follows intervention, permits one additional write attempt after reconciliation, and preserves the automatic budget and history. | Configuration value used, retry count, and a visible Owner alert linked to the paused activity and the correct retry action. Duplicate manual retry requests write at most once. | None |  |
| Recovery concerns a re-registration candidate | Preserve the previous active registration until explicit confirmation of the recovered candidate. Failure or cancellation does not restart project work. Duplicate requests still return the existing process. | Active and candidate version records, duplicate-request result, and work-state evidence after recovery. | None |  |

### Definition of done

Basic controlled interruptions of publication and service operations establish recovery from the last verified step and preserved check results. Evidence under [registration process-definition binding](../architecture.md#registration-process-definition-binding) shows the publication counter, no allowance reset on configuration edits, and reconciliation without a duplicate write. Retained results, versions and remote commits are checked directly. Necessary simulated conditions identify their reason and limitation; no exhaustive failure-combination suite is required.

Both registration journeys remain valid after recovery. Successful publication checks are already required by Register and confirm a project through the CLI; this outcome adds interruption and recovery evidence. Retry functions alone do not establish completion.

### Unresolved details

| Missing detail | Effect on the outcome | Clarification needed |
|---|---|---|
| Publication recovery implementation | External writes must be reconciled independently. | Implement the publication operation journal, exact-byte reconciliation, idempotent activation, and targeted Retry publication action under `docs/product/v1/architecture.md#publication-recovery`. |
| Connected recovery verification | Runtime recovery is supplied by the Runtime Service; registration must preserve its own process state. | Verify check results, versions, active versions and explicit retry actions across runtime recovery. Registration owns publication reconciliation and activation. |

## Partial-registration boundary

No narrower portion is declared. A selected subset must identify included outcomes, exclusions, the journey/criteria references above, and external dependencies before confirmation. Registration of a subset is not a claim that the complete capability is covered.

