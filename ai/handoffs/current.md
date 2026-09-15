# Maestro Repository Handoff

## Start here

- [Repository working rules](../../AGENTS.md) and [additional agent instructions](../../CLAUDE.md).
- [Project overview](../../docs/project-overview.md) — authoritative source entry and current-state evidence.
- [Architecture](../../docs/architecture.md) — system behavior and remaining mechanisms.
- [Runtime Service declaration](../../docs/milestones/runtime-service-milestones.md), [CLI declaration](../../docs/milestones/cli-milestones.md), and [registration declaration](../../docs/milestones/registration-milestones.md).
- [Architecture-loop declaration](../../docs/milestones/architecture-loop-milestones.md).
- [Planning Guide and templates](../../docs/planning-guide/README.md).
- [Maestro Project Architect — Software Architecture Role](../../docs/agents/architecture-agent.md).
- [Independent Fidelity Reviewer](../../docs/agents/decision-fidelity-reviewer.md).

## Where the discussion paused

The registration-reference mismatch is corrected in [candidate publication](../../docs/architecture.md#candidate-publication) and the shared `registrationRef` definition in [the schema](../../docs/schemas/architecture-loop.schema.json). Registration produces the six-field package reference; architecture consumes it unchanged. All fourteen registration-reference schema properties now use that definition; generic file references remain separate.

Other recent agreements still need incorporation into their authoritative sections: collect both architect and reviewer tool/model choices at registration intake; retain SQLite with service-owned writes; use consistently nested registration/architecture-loop TOML sections with separate budgets; align the specialist template with the required role headings. These are agreed directions, not unanswered Owner choices. GitHub App credential verification is deferred until the local machine is available; the reported local secret file's location and service binding remain unverified.

Source and publication selection is now specified in [Architecture](../../docs/architecture.md#source-and-publication-selection), with delivery evidence in the [registration declaration](../../docs/milestones/registration-milestones.md). The architecture owns the rule; the declaration references it. This is a documentation correction, not implemented registration behavior.

Initial intake pins a resolved source commit and records an authorized publication branch. Re-registration resolves its selected source again; recovery retains saved selections; the architecture loop inherits the confirmed baseline and destination. Existing master-only policy, confirmation authority and review budgets remain unchanged. See [the correction record](#source-selection-correction) for scope and verification.

Next: incorporate the agreed intake, SQLite, configuration-layout and specialist-format decisions. Installed resource bindings and remaining technical detail still need definition; GitHub App/local-secret verification waits for the local machine. The registration-reference conversion issue is superseded by the shared-reference correction. The historical validation below describes earlier frozen snapshots; its source/destination omission is superseded by this correction, not by a blanket readiness claim.

The documentation-review procedure is now defined in the [shared review method](../../skills/project-architecture-workshop/references/reviews.md), with record fields in [workshop state](../../skills/project-architecture-workshop/references/workshop-state.md#review-coverage-record). [AGENTS.md](../../AGENTS.md#cross-document-alignment) defines Maestro's journey scope; the [reviewer role](../../docs/agents/decision-fidelity-reviewer.md#inputs-and-independence) applies the method within unchanged authority. It separates fidelity, completeness and consistency, requires independent inputs and per-journey evidence, and distinguishes full coverage from targeted corrections. Existing review limits and the no-standalone-report rule remain in effect.

Blind full completeness and consistency passes, followed by one targeted selection-evidence correction check, surfaced the six requested benchmark subjects. The first full passes missed reviewer-input collection; the method and coverage fields were strengthened, and the targeted check found it independently. [Coverage, limits and disposition](#review-method-validation) are retained below. Existing review bounds were preserved. The source/destination disposition is updated by the later correction above; other gaps remain open.

The reusable [Project Architecture Workshop skill](../../skills/project-architecture-workshop/SKILL.md) is packaged with a generalized Planning Guide, templates, durable workshop state and bounded independent-review instructions. It is intended for new or existing projects, not reproduction of Maestro's design. [Installation instructions](../../skills/project-architecture-workshop/INSTALL.md) cover Codex and Claude Code. The package is committed, not installed into the owner's machines. No general Execution design was added by creating the skill.

Shared agent performance and context management are now defined in [Architecture](../../docs/architecture.md#agent-performance-and-context-management) and covered by the runtime, CLI, registration and architecture-loop declarations. Defaults warn at 75% context, hand off at 85%, and resume below 70%. Every runtime uses the same capacity classification; Qwen is not penalized for context exhaustion. Persistent sessions retain occupancy across runs. Capacity continuation preserves verified work and remaining active-time budget without consuming failure/correction/review allowances. Adapter capability verification remains implementation work; this does not select Qwen for registration or change exact model choices.

The pre-execution gap closures define stable saved finding references, the fixed architecture `decisions.json` snapshot, typed Owner decisions for one extra review/correction attempt, per-run deadlines with separate next-run duration exceptions, and the local Owner credential boundary. These contracts remain recorded; the validation below identifies unresolved cross-document gaps. SQL backup and restore are explicitly out of scope; the contradictory backup procedure is removed. Ordinary restart and recorded-operation recovery remain included.

The architecture-loop agreements are saved in [Architecture](../../docs/architecture.md#architecture-loop) and the [architecture-loop declaration](../../docs/milestones/architecture-loop-milestones.md).

Settled behavior includes `/architecture start` and `/architecture`, selected-project and idle-only entry, exact tool/model selection, persistent-session replacement from verified records, active-run limits, fixed output names and paths, manifest hashes, separate working/confirmed references, stale-data rejection, targeted review, exact-version confirmation, interrupted-operation recovery, cancellation/restart without budget resets, and later-registration invalidation.

Specialist roles use `role-<role-title>.md` beside source, with assigned `context.md` and optional `memory.md`. The architect owns the role and starting context; specialists maintain verified knowledge without changing authority or overwriting a newer file. Wrapper errors return to the architect for bounded technical correction before independent review.

Session continuation, active/waiting mapping, assignment/response and API shapes, saved-record schemas, policy bindings, and canonical hashing are now defined. The schema bundle is `docs/schemas/architecture-loop.schema.json`. Replanning occurs only after confirmed re-registration and a manual architecture-loop start; there is no independent trigger or separate replanning-design task.

Earlier targeted rechecks did not establish full architectural completeness. Documentation readiness must be assessed using the recorded coverage required by the updated review method.

The review-method validation below is historical evidence for its frozen snapshots. Later corrections have their own linked records; live implementation evidence remains separate.

No implementation, runtime configuration installation, or live AI box verification has been performed. Those belong to development. Continue directly on `master` and retain no separate review reports.

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
