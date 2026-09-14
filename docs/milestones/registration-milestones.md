# REG — Project Registration Milestone Declaration

## Declaration identity

| Field | Value |
|---|---|
| Project | Maestro |
| Declaration | REG — Project registration |
| Declaration version | 18 |
| Status | Proposed outcomes; no recorded implementation completion |
| Architecture source | `docs/architecture.md` |

## Capability and scope

The declaration delivers project registration through the CLI: source intake, bounded assessment and independent review, recorded decisions, versioned GitHub packages, explicit activation, re-registration, and technical recovery. Current-state evidence belongs in the [project overview](../project-overview.md).

Registration uses SVC-PM5 — Apply shared process definitions for common initiation, output handling, review accounting, confirmation, and recovery dispatch. Registration owns its package schema, eligibility, publication/activation policies, and process-specific handlers; shared mechanics are not reimplemented here.

Implemented runtime interfaces and CLI foundation precede registration integration. Final connected CLI acceptance is completed with initial registration, using its real projects and questions; final runtime recovery evidence is shared with registration recovery. The [Runtime Service declaration](runtime-service-milestones.md) owns service installation, storage/request mechanisms, API transport, start reservations, adapters, and agent supervision. Registration owns process-specific eligibility, role assignments and response semantics, review policy, package schema/publication/activation, and their actual use of those runtime capabilities. Implemented dependencies are required; their final shared acceptance is not a prerequisite to starting registration development. Command center, project implementation, automatic development start, development breakdown, full code audits, and execution-rule overrides are excluded.

Verification follows `docs/planning-guide/README.md#verification-expectations`: real data and connected operation, a basic main journey and essential failures, and no exhaustive outcome-by-outcome test suite. Evidence can cover several criteria in one journey. Fake data is used only when necessary with the reason recorded; it cannot prove real registration or agent integration.

The complete registration capability requires all three outcomes below. Initial registration completion does not establish re-registration or interruption recovery. Acceptance of each outcome uses its stated boundary.

Only unresolved design decisions require clarification in their authoritative sources before affected development breakdown. Listed implementation work and installed verification are performed during development; they are not prerequisites to starting it or to completing this documentation review. Existing-code claims retain the evidence levels and limitations in the project overview. Undefined behavior must not be invented during implementation.

Completion evidence for each milestone identifies the implementation revision, reproducible setup, observed main journey, essential failures, and the required review records with material findings resolved. Delivery-review roles and acceptance authority remain provisional for separate Execution design and must be defined before affected development breakdown. Registration's agent controls and fidelity reviews do not approve broader software execution policy.

## Milestones and order

| Position | Qualified milestone reference and plain subject | Milestone version | Milestone section |
|---|---|---|---|
| 1 | REG-PM1 — Register and confirm a project through the CLI | 13 | `docs/milestones/registration-milestones.md#reg-pm1--register-and-confirm-a-project-through-the-cli` |
| 2 | REG-PM2 — Update a registration without losing approved history | 9 | `docs/milestones/registration-milestones.md#reg-pm2--update-a-registration-without-losing-approved-history` |
| 3 | REG-PM3 — Recover registration without losing decisions or exceeding limits | 14 | `docs/milestones/registration-milestones.md#reg-pm3--recover-registration-without-losing-decisions-or-exceeding-limits` |

## REG-PM1 — Register and confirm a project through the CLI

**Outcome:** A whole project or defined portion reaches explicit confirmation and a retrievable registration package through the real CLI and service.

**Included:** Overview-based intake, source validation, scope and dependency assessment, independent fidelity review, naming/versions, questions and decisions, package publication, exact-candidate confirmation, and cancellation.

**Excluded:** Re-registration history changes, agent/service interruption recovery, command center, and development execution.

### Architecture and journeys

| Required behavior or journey | Architecture section |
|---|---|
| Register a project or selected portion | `docs/architecture.md#register-a-project-or-selected-portion` |
| Project entries, activities, and visible labels | `docs/architecture.md#project-activities-and-registration-labels` |
| Inputs and overview entry | `docs/architecture.md#source-format-and-inputs` |
| Source consistency | `docs/architecture.md#source-consistency` |
| Review budget and Owner decisions | `docs/architecture.md#review-limits-and-decisions` |
| Identity and naming | `docs/architecture.md#identity-declarations-and-ordering` |
| Agent response and adapter boundaries | `docs/architecture.md#registration-agent-response-contract`; `docs/architecture.md#model-execution-adapters` |
| Actual publication checks | `docs/architecture.md#agent-delegation` |
| Assessment and limits | `docs/architecture.md#assessment-and-independent-review` |
| Purpose and dependency checks | `docs/architecture.md#purpose-and-dependency-checks` |
| Package and activation | `docs/architecture.md#package-structure` |
| Guarded confirmation and cancellation | `docs/architecture.md#comparison-activation-and-cancellation` |

### Dependencies

| Required dependency | Reference | Current state or delivery responsibility |
|---|---|---|
| Shared process handling | SVC-PM5 — Apply shared process definitions | Implemented common handlers support registration; registration supplies its exact schemas and policies. Final runtime acceptance shares the connected process evidence. |
| CLI foundation | CLI-PM2 — Reliable project questions and answers, following CLI-PM1 — Connected multi-project CLI workspace | Implemented workspace and answer interfaces precede development; final connected acceptance is shared here. Prior final acceptance of those integrated CLI journeys is not a prerequisite. |
| Project sources | `docs/planning-guide/README.md` | Markdown source structure and package record contracts are specified. Executable validators are included implementation work. |
| Runtime records, API, and agents | SVC-PM2 — Preserve project activity and requests; SVC-PM3 — Connect the CLI to recorded service activity; SVC-PM4 — Run and recover assigned agents | Runtime Service implements shared storage, request delivery, tool setup, routing mechanics, and supervision. Registration supplies real architect/reviewer assignments and verifies their use. Final shared acceptance follows integration. |
| Registration repository access and publication | `docs/architecture.md#agent-delegation`; `docs/architecture.md#publication-and-sql-consistency` | Current operation unverified. Registration owns source access, package publication credentials and journal, wrapper publication checks, and SQL/GitHub activation consistency; generic SQL persistence is supplied by Runtime Service. |
| Package storage and activation | `docs/architecture.md#package-structure` | Package records, locations, publication, and activation are specified in the architecture. Executable schemas and connected persistence are included implementation work. |

### Acceptance criteria

| Expected result and conditions | Pass boundary | Verification and evidence | Accepted exception |
|---|---|---|---|
| The Owner follows startup and access instructions | The preceding CLI/service foundation is available, and the registration process reaches configured agents and the project repository using real authorized access. No missing service account or unpublished manual command is needed to reach intake. | Startup and connection evidence from the AI box, including access to the running service; record configuration references without secret values. | None |
| Source prepared using the Planning Guide is submitted | The explicit repository-relative overview path locates the architecture and declarations; Python validates identity, scope, architecture, current state, project milestones, project-level completion requirements, and authoritative document locations. The responsible project architect may be a person, an agent, or both. Missing required inputs are identified specifically. | Guide and validation-format references, source commit, accepted input record, and a rejected-input example identifying the missing field or document. Coding rules are not demanded as registration inputs. | None |
| Whole-project or partial-project scope is selected | The interpreted boundary is presented for explicit scope confirmation before assessment proceeds. The candidate records included outcomes, explicit exclusions, partial-milestone boundaries, and outside dependencies. Missing essentials produce a finding, not a silent scope expansion. | Inspect the presented boundary, recorded scope confirmation, candidate boundaries, and a dependency finding. Scope confirmation is distinct from final registration activation. Include a targeted source check distinguishing reported existence, source-supported implementation, and operationally verified behavior. No full code audit is required. | None |
| A milestone promises a usable capability | The architect records its usage journey, prerequisite coverage, and completion evidence. Essential operations cannot be excluded while the completion claim remains unchanged. Optional improvements do not block. | A source-backed assessment showing how required connections are covered and why each blocker prevents the stated purpose; a non-blocking finding retained without preventing readiness. | None |
| The architect submits findings for review | A separate agent performs fidelity review against the same source commit. The architect may amend its report. Rechecks cover affected findings only. With the configured initial maximum of two rounds, unresolved blockers or disagreement pause and reach the Owner; readiness may occur after one round. | Distinct architect and reviewer results, source references, amendments, and round counts. No invented reviewer approval, extra requirements, automatic third round, or forced approval. | None |
| The Owner needs to understand or answer registration | Registration creates real project/activity identities before approval. The project entry and labels follow the architecture, including Registering, waiting, and Not registered after an ended unsuccessful attempt. The CLI shows the current step, working agent, round and limit, findings, failures, and progress or waiting state. A choice or written clarification is recorded against its question and version, routed back to the paused step, and retained with affected milestones or criteria. Ambiguous responses request clarification. | Connected CLI records of the same process, including a decision and resumed step. Answering a question does not confirm registration. | None |
| A second registration request arrives for the same project | The CLI shows the existing active process; no competing process or new registration version is created. | Submit duplicate CLI requests and inspect the single activity and candidate. A request for another project remains separately addressable; its questions and decisions cannot be applied to this project. | None |
| Relevant planning inputs change during review | Both agents retain a consistent source version. Before confirmation, the Owner sees the change and chooses to retain the reviewed source or update the candidate and recheck affected findings. The two-round limit is not silently reset. Unrelated commits or report updates do not count as input changes. | Before-and-after source references, Owner choice, resulting candidate, and unchanged review-budget accounting. | None |
| A candidate is ready for confirmation | The package contains the summary, supplied project milestone outline, project-level completion requirements, review records, and retained Owner decisions. Exact content versions are identified. It preserves qualified milestone identities with plain subjects, declaration versions and ordered milestone references, dependencies, item versions, and the Owner-authorized naming-convention record. Ordering-only changes leave unchanged milestone versions intact. It contains no generated development breakdown. | Inspect the JSON package against the defined output schema and index; validate required fields and references. | None |
| The Owner confirms through the CLI | Only explicit confirmation makes the exact unchanged, eligible candidate active. Changed or ineligible candidates require renewed inspection before confirmation. That version is available in the project's GitHub repository; confirmation does not launch development. The confirmed contents cannot silently change afterward. Publish and verify the confirmation receipt before SQL activation; pending confirmation retains the prior active version and prevents competing changes. | Owner confirmation tied to the candidate, authoritative GitHub commit and package location, active-version record, and evidence that no development was started. Required wrapper checks verify repository, branch, allowed files, remote commit existence, and agreement with the reported commit before publication is counted as successful. | None |
| Registration is cancelled or action acknowledgment is lost | Explicit cancellation ends the attempt after its agent runs and external operations are resolved, with saved history retained. Pending confirmation rejects competing cancellation. Cancellation during candidate publication prevents advancement while the write is reconciled. Confirmation/cancellation are deliberate view actions, not ordinary text submission. An uncertain result shows Outcome not confirmed; reconnect queries the saved outcome and explicit retry cannot duplicate effects. | Main cancellation path and a necessary lost-acknowledgment case using the actual service. | None |

Agent integration acceptance also follows [adapter behavior](../architecture.md#model-execution-adapters): explicit architect tool/model selection at initiation, separate reviewer selection and workspace, immutable assignment inputs, linked clarification follow-ups, SQL-recorded progress, and validated output before advancement. Unsupported or unverifiable model selection prevents launch. The architect returns an explicit assessment artifact and candidate; the reviewer receives exact staged copies. Every result includes assignment and run identities. Tool-reported model evidence, effective permissions, and immutable inputs must be checked rather than inferred from agent prose. Cancellation displays Stopping until confirmed or Stop unconfirmed when uncertain; completion during pending cancellation cannot advance registration.

### Definition of done

The real CLI registration journey also supplies final connected workspace/answer acceptance evidence for the CLI declaration and supplies evidence for every criterion, including source reading, genuine architect/reviewer activity, a retained response, exact package publication, and deliberate confirmation. Basic essential-failure evidence establishes source rejection, review limits, stale-candidate protection, and uncertain-action handling; criteria can share one journey.

The confirmed JSON package is retrievable in GitHub and usable by the next process without relying on mutable latest files. Completion evidence and delivery reviews meet the common completion requirements above. Fake-data screens or fabricated approvals cannot demonstrate registration. No development breakdown or work start occurs.

### Unresolved details

| Missing detail | Effect on the outcome | Clarification needed |
|---|---|---|
| Connected adapter use | Runtime Service owns adapter implementation and installed capability verification. | Use SVC-PM4 — Run and recover assigned agents for actual registration role assignments, validate assessment/candidate response meaning, and demonstrate distinct reviewer use. Shared evidence must include actual model identity, permissions, source isolation, and failure reporting before assessment. |
| Delivery-review contract | Completion review cannot rely on an unnamed reviewer or assumed authority. | Define required implementation-review roles, evidence, and acceptance authority before affected breakdown. |
| Planning-review configuration implementation | The configured limit must survive changes and recovery. | Implement `registration.maximum_fidelity_reviews` under the architecture's review-limit contract, snapshotting the limit at initiation and counting accepted completed reviews once. |
| Output and persistence implementation | Defined package contracts need executable validation and durable publication. | Implement `docs/architecture.md#package-record-contract` and `docs/architecture.md#publication-and-sql-consistency`; validate the actual connected journey before completion. |

## REG-PM2 — Update a registration without losing approved history

**Outcome:** An idle project can revise registration coverage or project milestones while preserving prior approval and controlling exactly what becomes active.

**Included:** Idle-only entry, prevention of new work during re-registration, version history, comparison, bounded reassessment, confirmation, and cancellation.

**Excluded:** A full execution engine or authorization to rewrite source plans or break down development work.

### Architecture and journeys

| Required behavior or journey | Architecture section |
|---|---|
| Update a registration | `docs/architecture.md#update-a-registration` |
| Idle-only entry and versions | `docs/architecture.md#re-registration` |
| Changes, confirmation, and cancellation | `docs/architecture.md#comparison-activation-and-cancellation` |
| Source versions and review budget | `docs/architecture.md#source-consistency` |

### Dependencies

| Required dependency | Reference | Current state or delivery responsibility |
|---|---|---|
| Initial registration | REG-PM1 — Register and confirm a project through the CLI | Required preceding outcome. |
| Real project-work state and new-start prevention | SVC-PM2 — Preserve project activity and requests | Runtime Service supplies atomic state/reservation mechanisms. Registration owns idle eligibility and reservation lifetime and verifies the connected boundary. No full execution engine is assumed. |

### Acceptance criteria

| Expected result and conditions | Pass boundary | Verification and evidence | Accepted exception |
|---|---|---|---|
| Project work is active | Re-registration cannot begin until all active work finishes or is explicitly stopped. The idle check and registration reservation are atomic. Reserved starts, unfinished waiting work, pending external operations, and uncertain runs prevent entry with named reasons. Once re-registration begins, only that registration's assignments and operations may start until it ends; other projects continue normally. | Runtime work-state evidence, a rejected re-registration request through the CLI, and a rejected new-work attempt at the service boundary. The work-state and start-inhibition connection is an explicit dependency, not a checkbox supplied by the reviewer. | None |
| An idle project is re-registered | Create the next registration version while preserving previous versions. Additions or amendments concern project milestones, not development milestones or work packets. Apply the same fidelity loop and two-round configured limit. | Successive version folders, source and milestone versions, and real review records. | None |
| A candidate differs from the active version | Show additions, changes, removals, affected scope or completion requirements, and reasons linked to findings or Owner decisions. | Comparison visible before confirmation, tied to the exact candidate. The project remains Registered with Updating registration displayed while the prior version stays active. | None |
| The Owner confirms the candidate | The candidate becomes active only on explicit confirmation of the unchanged eligible version shown. Previous records remain retrievable. Item identities remain stable; changed items increment versions and unchanged items retain theirs. | Confirmation, version references, and GitHub history comparison. | None |
| Re-registration fails or is cancelled | The previous registration remains active. Project work does not automatically restart. | Failure or cancellation record, unchanged active-version reference, and observed stopped-work state. | None |

### Definition of done

The connected re-registration journey and essential rejection/cancellation paths establish all criteria with preserved GitHub history, explicit comparison, and exact-candidate activation. Work-state enforcement must use actual service state; a reviewer checkbox is not proof. The prior version remains available, and project work never restarts automatically. Completion evidence and delivery reviews meet the common completion requirements above.

### Unresolved details

| Missing detail | Effect on the outcome | Clarification needed |
|---|---|---|
| Work-state enforcement implementation | The defined idle check requires actual activity and run state. | Use the atomic project start lock supplied by SVC-PM2 — Preserve project activity and requests. Implement registration eligibility and reservation lifetime under `docs/architecture.md#re-registration`, including pending, waiting, and uncertain work. |
| Candidate and active-version implementation | Published receipts and SQL activation must reconcile without replacing prior approval early. | Implement `docs/architecture.md#confirmation-and-activation`, including pending confirmation and conflicts. |

## REG-PM3 — Recover registration without losing decisions or exceeding limits

**Outcome:** Interrupted registration resumes from verified work or pauses visibly without losing decisions, duplicating effects, or exceeding its budgets.

**Included:** Registration integration with Runtime Service checkpoints, agent recovery and technical limits; registration publication wrapper checks and interrupted-publication reconciliation; preserved decisions, review budgets, and initial/re-registration continuity. Generic supervisor and retry mechanisms are delivered by Runtime Service.

**Excluded:** Unlimited retries, forced approval, and unrelated execution recovery.

### Architecture and journeys

| Required behavior or journey | Architecture section |
|---|---|
| Recover an interrupted registration | `docs/architecture.md#recover-an-interrupted-registration` |
| Technical recovery and limits | `docs/architecture.md#technical-recovery` |
| GitHub wrapper verification | `docs/architecture.md#agent-delegation` |
| Uncertain action outcome | `docs/architecture.md#comparison-activation-and-cancellation` |

### Dependencies

| Required dependency | Reference | Current state or delivery responsibility |
|---|---|---|
| Registration journeys | REG-PM1 — Register and confirm a project through the CLI; REG-PM2 — Update a registration without losing approved history | Required connected predecessors. |
| Shared configured recovery | SVC-PM5 — Apply shared process definitions | Registration retains the publication journal and activation semantics; shared handlers apply its policy and recorded definition without resetting budgets. |
| Durable checkpoints and remote evidence | SVC-PM4 — Run and recover assigned agents; `docs/architecture.md#technical-recovery` | CLI request identity is defined in `docs/architecture.md#answer-identity-and-uncertain-delivery`. Run identity, supervision, and event replay are defined in `docs/architecture.md#process-supervision-and-interruption-recovery`; publication reconciliation is defined in `docs/architecture.md#publication-recovery`. The automatic agent recovery default is two attempts per assignment. |

### Acceptance criteria

| Expected result and conditions | Pass boundary | Verification and evidence | Accepted exception |
|---|---|---|---|
| An agent crashes, a push fails, or the service restarts | Preserve completed reports, reviews, and Owner decisions. Resume from the last verified step; unverified results are not treated as completed. | Before-and-after records for each interruption, resumed step, retained exact source and candidate versions, supervisor reconciliation, and confirmation that no duplicate or child run remains. | None |
| A delegated operation requires a GitHub commit | The wrapper checks the expected repository and branch, committed and pushed changes, remote commit existence, permitted changed files, and agreement with the reported commit. A local commit or agent assertion alone cannot pass. Read-only reviews do not require unnecessary commits. | Wrapper results and remote GitHub evidence for successful publication and a deliberately unsuccessful publication. Verify lost-write acknowledgment and interrupted SQL activation without a duplicate confirmation, repeated Owner approval, or architect rerun. | None |
| Technical retries occur | A separate configurable technical limit defaults to two automatic recovery attempts per agent assignment after the initial run. Technical failures do not consume planning review rounds. Retries follow the architecture's failure classification; intervention-dependent or unknown causes pause without exhausting attempts. At the limit, registration pauses and explains the failure. Manual Retry activity follows intervention, permits one additional run, and preserves the automatic budget and history. Unknown original-run status blocks replacement; only confirmed termination permits recovery. | Configuration value used, retry count, unchanged planning-review count, and visible Owner alert linked to the paused activity and correct retry action, without creating a question or executing retry merely by opening attention. Verify the default two-attempt limit and confirm that recovery runs do not reset assignment accounting. Internal tool retries stay within one run and its deadline. Duplicate manual retry requests launch at most once; late output from an old run cannot change the candidate. | None |
| A registration agent reaches its configured duration | Apply the 30-minute per-run default separately to the registration architect and reviewer. Request termination, preserve output, and pause after confirmed stopping; timeout alone cannot trigger automatic retry. Other planning and execution roles do not inherit this default. | Configured limit, elapsed time, last progress, confirmed or uncertain stop, and retained output. Basic controlled timeout evidence may use a shorter configured duration. | None |
| Recovery concerns a re-registration candidate | Preserve the previous active registration until explicit confirmation of the recovered candidate. Failure or cancellation does not restart project work. Duplicate requests still return the existing process. | Active and candidate version records, duplicate-request result, and work-state evidence after recovery. | None |
| A fidelity-review allowance is exhausted | The linked CLI decision displays counts and offers one extra attempt or remaining paused. Only the credential-identified Owner can apply a grant, once, to the exact assignment; replay and restart preserve it. Timeout duration exceptions remain separate and do not replenish attempts. | Main limit-response journey and essential replay evidence using `docs/architecture.md#owner-decisions-at-a-process-limit` and `docs/architecture.md#run-deadlines-and-duration-exceptions`; shared runtime handling supplies mechanics. | None |
| A registration agent reaches context capacity | Use shared checkpoint/continuation handling, preserve accepted reports and decisions, and keep capacity transitions separate from failure, correction and review accounting. Retain cumulative time/usage and the remaining active-time budget. | Connected registration continuation uses `docs/architecture.md#checkpoints-and-safe-continuation`; runtime owns mechanics and registration retains its existing eligibility and confirmation rules. | None |

### Definition of done

Basic controlled interruptions of actual agent, publication, and service operations establish recovery from the last verified step and preserved review budgets. Retained reports, decisions, versions, and remote commits are checked directly. Necessary simulated conditions identify their reason and limitation; no exhaustive failure-combination suite is required.

Both registration journeys remain valid after recovery. Completion evidence and delivery reviews meet the common completion requirements above. Successful publication checks are already required by REG-PM1 — Register and confirm a project through the CLI; this outcome adds interruption and recovery evidence. Retry functions alone do not establish completion.

### Unresolved details

| Missing detail | Effect on the outcome | Clarification needed |
|---|---|---|
| Publication recovery implementation | External writes must be reconciled independently from agent execution. | Implement the publication operation journal, exact-byte reconciliation, idempotent activation, and targeted Retry publication action under `docs/architecture.md#publication-recovery`. |
| Connected recovery verification | Runtime recovery is supplied by SVC-PM4 — Run and recover assigned agents; registration must preserve its own process state. | Verify registration decisions, review budgets, candidates, active versions, and explicit retry actions across runtime recovery. Registration owns publication reconciliation and activation; runtime owns generic launch limits and supervisor recovery. |

## Partial-registration boundary

No narrower portion is declared. A selected subset must identify included outcomes, exclusions, the journey/criteria references above, and external dependencies before confirmation. Registration of a subset is not a claim that the complete capability is covered.
