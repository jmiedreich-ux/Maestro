# M1-02AR — Exhaustive Constraint-Proof Remediation

**Status:** candidate pending Decision Fidelity and Project Architect release;
not dispatchable
**Packet / node:** `maestro-m1-02ar-exhaustive-constraint-proof-remediation` /
`MAESTRO-M1-02AR-EXHAUSTIVE-CONSTRAINT-PROOF-REMEDIATION`
**Planning / implementation bases:** `7fc702182a32f01e3c3dfd48f327651aa61c05d0` /
`08a9702d9c9ca29681a4d3ba73c487c89a14c87d`
**Authority:** accepted M0-D16 at
`c5a3326e05c0ba4a35529ef70a5939a03bdc2609`
**Roles:** Coordinator dispatches; Maestro Developer implements; Integration
validates; fresh Independent Reviewer reviews; Project Architect accepts and
routes only an M0-D15 reserved choice to Owner.

## Purpose and authority

M1-02A produced `56b4dfb5e4d4bef860616cde93d172affb0e4210`
through `7ae9bf4c3e37d658fd56bfbb8f5c9935d45a79b2`, then its sole correction to
`08a9702d9c9ca29681a4d3ba73c487c89a14c87d`. The correction review approved,
but Integration failed: proof 4 used an ambiguous universal claim with only
representative CHECK/JSON/ID/digest/timestamp/size cases. AR is a new attempt,
not correction 2.

This packet replaces that assurance wording while preserving product/schema
behavior. “Exhaustive” in its stable name means only the named sets
`DB-R01..DB-R20`, `DB-PK01..DB-PK05`, `APP-V01..APP-V25`,
`APP-MAP-01..APP-MAP-21`, `APP-REL-01..APP-REL-19`, and `AR-P01..AR-P13`.

Controls: M0-D01..D06/D11/D12/D14/D15/D16, M1-02, Master Plan, control plane,
active `ai/handoffs/current.md`, and `docs/agents/{maestro-developer,
coding-agent-sop,integration-agent,independent-review-agent,
maestro-development-manager}.md`. M0-D15/current handoff control conflicts.

## Dispatch contract

| Field | Fixed value |
|---|---|
| Project / workstream / milestone | `maestro` / `operational-state` / `M1` |
| Outcome | Static schema identity; 25 DB, 25 validator, 21 wiring, and 19 relation cases |
| Priority / dependency | `P0`; M1-02B remains blocked until combined M1-02A+AR Project Architect acceptance |
| Branch / worktree | `implementation/m1-02ar-exhaustive-constraint-proof-remediation` / `/home/jeremy/Development/Maestro-m1-02ar-implementation`, clean from the exact implementation base |
| Route | `codex-cloud-maestro-developer`; Integration `validate-only`; fresh high-risk review |
| Locks | `shared:sqlite-schema`, `path:maestro-operational-state`, `file:services-maestro-storage`, `path:tests-m1-02` |
| Time | one 150-minute initial attempt; at most one combined-finding correction |
| Context | `32768` + `8192` reserve; warn `16384`, handoff `12288`, stop `8192`; dispatch-only |
| Non-goals | B/C; redesign; parser/framework; external/live/credential/worker/Atlas/delivery/merge/deploy/USB/dependency work |

Release requires exact source history, Decision Fidelity `APPROVE`, Project
Architect release, locks, and recheck of `/tmp/tmp.Py0ofuraFb/deps` as
`PYTHONPATH`: CPython `>=3.12`, SQLite FK/WAL/JSON1, `PyYAML>=6.0.2,<7`,
`jsonschema>=4.10,<5`. No install, upgrade, or network.

Normal owned paths are:

```text
tests/m1_02/test_schema_and_records.py
tests/m1_02/test_context_and_payloads.py
```

`storage.py` or `operational_state.py` may change only after a listed case fails
on the base and proves a frozen contract unenforced: preserve DB-S01, record
red/green evidence, make the smallest repair. Schema/API/semantic change returns
to Project Architect. No other path may change.

## Frozen schema identity and database cases

Baseline source blobs are: `storage.py`
`498cb4c9125e9c72961f6f7f90aa378a3296c352`, `operational_state.py`
`862d91841370ebaee352147d16e30ef294364962`, schema tests
`7558bd78da5ad77c4b8058509ffb845c39c640c7`, and context tests
`b65c957dfbf1ab5701ff3a8e656c8a16bf2b1d02`.

`DB-S01` is the static schema oracle. Create schema 3 through the accepted
fixture, upgrade once through `SQLiteFoundation`, then select
`type,name,tbl_name,sql` for the following 47 objects in the displayed order.
Serialize objects as `{"type":type,"name":name,"table":tbl_name,"sql":sql}`
using UTF-8 JSON, sorted object keys, compact separators, no final newline. The
result is 36,914 bytes and SHA-256
`3bf7930f669752d89590a7590cc580bbaf08dd21ff36ddcbe4042fa30a2084af`.
This is a named-object equality check, not a DDL tokenizer.

```text
TABLES (20): events, project_bindings, secret_reference_observations,
graph_projections, work_items, runs, packets, leases, attempts, resource_locks,
evidence, waits, reviews, notifications, acceptance_records, merge_observations,
worker_progress_observations, attempt_context_usage, provider_allowance_windows,
usage_reconciliations
INDEXES (6): one_active_binding_per_project, one_active_graph_per_project,
one_active_lease_per_packet, one_active_lease_per_worktree,
one_active_resource_key, one_open_wait_per_packet_gate
TRIGGERS (21): events_require_v4_metadata, events_validate_v4_shape,
events_closed_event_type, events_no_update, events_no_delete,
evidence_no_update, evidence_no_delete, reviews_no_update, reviews_no_delete,
secret_reference_observations_no_update, secret_reference_observations_no_delete,
worker_progress_observations_no_update, worker_progress_observations_no_delete,
provider_allowance_windows_no_update, provider_allowance_windows_no_delete,
usage_reconciliations_no_update, usage_reconciliations_no_delete,
acceptance_records_no_update, acceptance_records_no_delete,
merge_observations_no_update, merge_observations_no_delete
```

The direct SQLite negative cases are fixed. Each uses the stated single invalid
fact and expects `sqlite3.IntegrityError` with the applicable exact extended
name (`SQLITE_CONSTRAINT_CHECK` or `SQLITE_CONSTRAINT_PRIMARYKEY`).

```text
DB-R01 lease expires_at<=acquired_at
DB-R02 attempt_number outside {1,2}
DB-R03 attempt_kind outside {Initial,TargetedCorrection}
DB-R04 attempt 1/Initial with non-null correction_for_review_id
DB-R05 attempt 2/TargetedCorrection with null correction_for_review_id
DB-R06 acceptance subject_type outside {Packet,Run}
DB-R07 Packet acceptance with subject_id!=packet_id
DB-R08 Packet acceptance with non-null run_id
DB-R09 Run acceptance with subject_id!=run_id
DB-R10 Run acceptance with non-null packet_id
DB-R11 acceptance sequence_number outside {1,2}
DB-R12 merge performer outside {Owner,DelegatedIdentity}
DB-R13 Owner merge with non-null delegation_reference
DB-R14 DelegatedIdentity merge with null delegation_reference
DB-R15 version=0 in each listed table: graph_projections, work_items, runs,
  packets, leases, attempts, resource_locks, waits, notifications,
  attempt_context_usage
DB-R16 packets.correction_count outside {0,1}
DB-R17 notifications.attempt_count<0
DB-R18 work_items.planned_rank<0
DB-R19 reviews.correction_number outside {0,1}
DB-R20 attempt_context_usage.configured_context_limit non-null and <=0
DB-PK01 duplicate notifications.notification_id
DB-PK02 duplicate merge_observations.merge_observation_id
DB-PK03 duplicate worker_progress_observations.progress_id
DB-PK04 duplicate provider_allowance_windows.allowance_observation_id
DB-PK05 duplicate usage_reconciliations.usage_reconciliation_id
```

## Frozen application cases and wiring

Each validator boundary is behaviorally proved once with its positive edge,
negative edge, exact exception/message, and canonical output:

```text
APP-V01 closed mapping root/required/extra
APP-V02 text nonempty/UTF-8/512/control
APP-V03 optional text; APP-V04 lowercase 40-hex commit; APP-V05 lowercase 64-hex digest
APP-V06 provider grammar; APP-V07 reference grammar/value-carrier rejection
APP-V08 valid canonical timestamp; APP-V09 optional timestamp
APP-V10 positive int excluding bool; APP-V11 nonnegative int excluding bool
APP-V12 sorted unique text array
APP-V13 canonical JSON root/key/type/NaN/Inf/banned-key/UTF-8/1-MiB
APP-V14 JSON object plus V13; APP-V15 nonnegative normalized decimal
APP-V16 context-policy keys/positivity/order/sum/starting-fit
APP-V17 eight payload kinds/exact fields/context/redaction
APP-V18 measurement value/quality/confidence/source/time; APP-V19 cost matrix
APP-V20 same-period preference; APP-V21 five token categories plus V18
APP-V22 actor shape/causation; APP-V23 replay/fingerprint conflict/no mutation
APP-V24 SQLite-to-InvalidRecord mapping; APP-V25 ResourceBusy/no partial mutation
```

For one valid invocation of each named builder/route, test-only `unittest.mock`
wrappers record existing helper calls; the exact trace must equal this map.
No AST/DDL framework is created. `Vnn` means `APP-Vnn`; `Rnn` means
`APP-REL-nn`; `?` means validate only when non-null.

```text
APP-MAP-01 _actor: V02[actor_type,actor_id,correlation_id]; V10?[causation_event_id]; R17
APP-MAP-02 _binding: V02[binding_id,project_id,binding_revision,adapter_version,process_version,authority_reference,merge_policy,acceptance_authority,merge_execution_authority,state]; V04[source_commit]; V05[manifest_digest]; V03[merge_delegation_reference]; V14[binding_json]; V09[activated_at,superseded_at]; V08[now]; R01
APP-MAP-03 _secret_reference: V02[id,project_id,binding_id,owner_reference]; V06[provider]; V07[reference_name]; V09[rotation_at,expires_at]; V08[observed_at]; R02; id=secret_reference_observation_id
APP-MAP-04 _graph: V02[id,project_id,binding_id,graph_revision,authority_reference,state]; V04[source_base_sha]; V05[source_hash]; V08[observed_at,now]; R03; id=graph_projection_id
APP-MAP-05 _work_item: V02[id,graph_projection_id,architecture_node_id,task_reference,workstream_ref,milestone_ref,title,priority,specialist_role,planning_state]; V11[planned_rank]; V12[execution_classes_json,dependencies_json,change_domains_json]; V14[input_contract_json,output_contract_json]; V08[now]; R04; id=work_item_id
APP-MAP-06 _run: V02[run_id,project_id,binding_id,graph_projection_id,milestone_ref,approved_authority_reference,state,acceptance_boundary]; V05[run_fingerprint]; V03[branch_name,pull_request_reference,current_head_source_reference,candidate_head_source_reference]; V04?[current_head,candidate_head]; V08[now]; R05
APP-MAP-07 _packet: V02[packet_id,run_id,work_item_id,packet_revision,authority_reference,expected_branch,role_contract_reference,sop_reference,executor_class,integration_route,reviewer_route,state]; V04[base_commit]; V04?[current_head]; V12[owned_paths_json,forbidden_paths_json,resource_claims_json]; V13[checks_json]; V16[context_policy_json]; V11[correction_count]; V08[now]; R06
APP-MAP-08 _attempt: V02[attempt_id,packet_id,lease_id,executor_class,model_identity,runtime_identity]; V10[attempt_number]; V03[correction_for_review_id]; V04?[result_commit]; V09[started_at,finished_at]; V08[now]; R06
APP-MAP-09 _evidence: V02[evidence_id,idempotency_key,run_id,packet_id,evidence_kind]; V03[attempt_id,source_reference]; V17[payload_json]; V05[content_digest]; V08[created_at]; R07
APP-MAP-10 _wait: V02[wait_id,run_id,gate_type,awaited_role,awaited_reference,expected_result,next_permitted_action,state]; V03[packet_id]; V09[timeout_at]; V08[now]; R08[resolution_reason_payload_json,state]
APP-MAP-11 _review: V02[review_id,packet_id,reviewer_role,reviewer_instance]; V03[attempt_id]; V04[base_commit,head_commit]; V17[findings_json items]; V14[coverage_json]; V11[correction_number]; V08[created_at]; R09
APP-MAP-12 _notification: V02[notification_id,run_id,destination_reference,audience,message_type,grouping_key]; V10[event_id]; V03[packet_id]; V09[escalation_at]; V17[payload_json]; V08[now]; R10[channel,severity,state,attempt_count,last_error_payload_json,next_attempt_at]
APP-MAP-13 _worker_progress: V02[progress_id,attempt_id,next_permitted_action]; V17[plan_payload_json,current_step_payload_json,blocker_payload_json]; V08[observed_at,received_at]; R11[eta_text,confidence,status_request_state]
APP-MAP-14 _context_usage: V02[context_usage_id,attempt_id,model_identity,runtime_identity]; V03[quantization]; V10?[configured_context_limit]; V05[context_policy_digest]; V18[starting_input_measurement_json]; V21[token_measurements_json]; V19[cost_measurement_json]; V08[observed_at,now]; R12[future_growth_estimate_json,counting_method,availability_state]
APP-MAP-15 _allowance: V02[allowance_observation_id,account_reference,native_window_type]; V06[provider]; V15?[used_value,remaining_value]; V03[native_unit]; V09[reset_at]; V08[observed_at]; R13[precision,measurement_quality,freshness]
APP-MAP-16 _reconciliation: V02[usage_reconciliation_id,allowance_observation_id,native_unit]; V15[window_change_value,tracked_controlled_value,registered_coarse_value,unattributed_value]; V08[observed_at]; R14[measurement_quality,balance]
APP-MAP-17 _acceptance: V02[acceptance_id,subject_id,authority_reference]; V03[packet_id,run_id,supersedes_acceptance_id]; V10[sequence_number]; V04[exact_head]; V14[review_coverage_json]; V17[reason_payload_json]; V08[created_at]; R15[subject_type,required_authority,decision]
APP-MAP-18 _merge_observation: V02[merge_observation_id,run_id,packet_id,repository_reference,default_branch,source_reference,performed_by_reference]; V03[acceptance_id,delegation_reference]; V04[accepted_head,merge_commit]; V14?[review_coverage_json]; V08[observed_at]; R16[source_kind,performed_by_authority]
APP-MAP-19 update_context_usage: V02[attempt_id]; V10[expected_version]; V01[update keys]; V21[token_measurements]; V19[cost_measurement]; V08[observed_at,now]; R12[availability,version,precedence]
APP-MAP-20 snapshot/events_after: V02[entity_type,entity_id]; V11[event_id]; R19[entity allowlist,limit 1..1000]
APP-MAP-21 shared append: V02[idempotency_key]; V22[actor]; V08[now]; V23[replay/conflict]; V24[constraint mapping]; V25[busy exhaustion]
```

Context-dependent relation cases are:

```text
APP-REL-01 binding Candidate|Blocked, acceptance authority, merge delegation, null lifecycle times
APP-REL-02 secret status enum
APP-REL-03 graph Active-only and sorted unique work IDs
APP-REL-04 work graph identity and planning-state enum
APP-REL-05 run Planned-only, acceptance boundary, four initial head/source nulls
APP-REL-06 packet Planned/count-zero/head-null; attempt number/kind/correction/result/time
APP-REL-07 evidence digest, redaction enum, redacted-prose relation
APP-REL-08 wait Open and unresolved creation
APP-REL-09 review kind/result/correction and findings payload array
APP-REL-10 notification enums, source-event equality, pending unsent values
APP-REL-11 progress redacted payloads, ETA alternatives, confidence/request enums
APP-REL-12 context policy digest/fit, growth keys/quality/source/time/order, availability/precedence
APP-REL-13 allowance quality labels and available/unavailable value relation
APP-REL-14 reconciliation FK/unit/quality and exact decimal balance
APP-REL-15 acceptance Packet|Run identity/exactly-one, sequence/authority/decision/reason
APP-REL-16 merge source and performer/delegation relation
APP-REL-17 event legacy exception, metadata/shape/type/causation, append-only
APP-REL-18 public append FK/unique/check mapping plus replay/conflict
APP-REL-19 snapshot entity allowlist and events-after limit
```

## Evidence procedure and fixed definition of done

Each negative DB/APP case creates a fresh physical SQLite file, seeds the
minimum valid dependency chain, snapshots target/related rows and event
count/max ID, changes one named fact, and asserts the exact closed error. It
then rolls back, closes, reopens through `OperationalStateStore`, and proves
unchanged rows/events/schema/FK health/WAL/artifacts plus the valid boundary.
Broad exceptions, shared dirty fixtures, in-memory-only checks, and production-
derived expected values are prohibited.

Requirements are fixed as `AR-R01` exact authority/base/environment/locks;
`AR-R02` schema identity; `AR-R03` finite database behavior; `AR-R04`
validator/wiring/relations; `AR-R05` durable rejection; `AR-R06` regressions/
stress; `AR-R07` scope and handoff; `AR-R08` combined gates/one correction;
`AR-R09` fixed completion/coverage/acceptance; and `AR-R10` return/learning.

| Proof | Owner and passing evidence |
|---|---|
| `AR-P01` | Coordinator: AR-R01 preflight facts and acquired locks |
| `AR-P02` | Developer; Integration repeats: DB-S01 exact 47-object/count/byte/digest equality |
| `AR-P03` | Developer: passing DB-R01..R20 and DB-PK01..PK05 case rows |
| `AR-P04` | Developer: passing APP-V01..V25 boundary rows |
| `AR-P05` | Developer: exact APP-MAP-01..21 mock traces and APP-REL-01..19 rows |
| `AR-P06` | Developer: AR-R05 reopen/no-row/no-event evidence for each negative case |
| `AR-P07` | Developer; Integration repeats: AR-R06 named suites and ten-run stress |
| `AR-P08` | Developer: AR-R07 scoped diff, artifact/secret scan, handoff, released locks |
| `AR-P09` | Integration: one terminal full crosswalk result with one finding set |
| `AR-P10` | fresh reviewer: one full base-to-initial-head review and finding set |
| `AR-P11` | Coordinator/Developer/gates: no correction needed, or one union correction and targeted follow-up |
| `AR-P12` | Project Architect: AR-R10 learning/return record complete |
| `AR-P13` | Project Architect: AR-R09 exact-head combined M1-02A+AR acceptance |

Coverage is fixed: `AR-R01->AR-P01`; `AR-R02->AR-P02`;
`AR-R03->AR-P03,AR-P06`; `AR-R04->AR-P04,AR-P05`;
`AR-R05->AR-P06`; `AR-R06->AR-P07`; `AR-R07->AR-P08`;
`AR-R08->AR-P09,AR-P10,AR-P11`; `AR-R09->AR-P10,AR-P13`; and
`AR-R10->AR-P08,AR-P12`.
Allowed states are `PASS|FAIL`, review `APPROVE|REQUEST_CHANGES`, and acceptance
`Accepted|Returned`; no `N/A` or `UNTESTED`. Technical completion means P01..P12
pass at one exact head and P13 records `Accepted`. A later improvement cannot
add a proof ID. A direct governing-contract violation still blocks and records
a packet-contract learning defect.

## Gates, correction, return, and acceptance

From `services/maestro/`, run Alpha-01/02/03, M1-01, and M1-02 unittest
discovery plus `python -m compileall -q maestro`, `git diff --check
08a9702..HEAD`, and exact changed-path/artifact/secret scans. Run the two M1-02
modules in ten fresh processes:

```text
for n in 1 2 3 4 5 6 7 8 9 10; do
  python -m unittest discover -s ../../tests/m1_02 -p 'test_schema_and_records.py' -v || exit 1
  python -m unittest discover -s ../../tests/m1_02 -p 'test_context_and_payloads.py' -v || exit 1
done
```

No accepted test may be removed, skipped, renamed out of discovery, loosened to
a broad exception, or have an assertion reduced. The handoff records base/head,
paths, case IDs/results, commands, environment/context/usage, red/green evidence,
reopen proof, stress results, artifacts, gaps, and released locks.

Let `H0` be the first committed AR result and `H1` be the one correction head,
or `H0` when correction is unused. For a committed, in-scope result that can
safely be reviewed, the Coordinator waits for terminal Integration and fresh
full review over `08a9702..H0`, then
unions their complete findings before authorizing one correction. Follow-up is
limited to that union, `H0..H1`, reruns, and directly affected consistency.
Immediate M0-D05 no-diff/no-commit/scope/dependency/configuration/placeholder or
rejection classes need not wait. A new failure class, failed/out-of-scope
correction, or correction exhaustion returns to the Project Architect. Final
coverage records the two prior A ranges, `08a9702..H0`, and `H0..H1` only when
used. Integration PASS and reviewer APPROVE do not accept work; the Project
Architect alone records routine combined M1-02A+AR acceptance at `H1`.

Bootstrap return evidence is immutable and content-digested:

```text
M1_02AR_RETURN_V1={packet_id,implementation_base,exact_head,terminal_gate,
failed_proof_ids[],classification,responsible_authority,next_permitted_action,
idempotency_key,evidence_references[],observed_at}
M1_02AR_LEARNING_V1={packet_id,H0,H1,active_seconds,queue_seconds,gate_seconds,
first_pass_result,integration_count,full_review_count,followup_count,
correction_count,hard_escalation,findings[{proof_ids,class,compiler_discoverable,
gate}],late_requirement,absence_reason,reusable_rule,reusable_authority,
recorded_at,evidence_references[]}
```

Classification/next action use the closed M0-D16/M0-D05 values. The known late
requirement is “proof 4 lacked a finite assurance carrier”; absence reason is
“ambiguous universal wording”; `compiler_discoverable=true`; reusable rule is
“static identity plus finite high-risk behavior and proportional validator
wiring replaces a general declaration parser”; authority is `M0-D16@c5a3326`.
Chat is not a wake mechanism. Only committed authority/environment change,
terminal gate, recorded resolution, expiry, or restart causes reread. No B work,
merge, deploy, project registration, external access, or live action is unlocked
until the exact `H1` Project Architect acceptance.

## M0-D12 quality contracts

**Q1 — Closed proportional proof.** Protected: listed schema/validation
assurance cannot be mistaken for broader proof. Model: exact base, DB-S01,
DB-R/PK, APP-V/MAP/REL sets. Excludes future schema and formal verification.
Assurance: deterministic static identity plus finite behavioral evidence.
Proof: P02..P06. Boundary: two tests and conditional minimal source repair.
Ceiling: no DDL tokenizer, AST framework, fuzzing, or new semantics. Stop: a
needed unlisted case or changed schema returns to Project Architect.

**Q2 — Durable rejection.** Protected: a listed rejection leaves no durable
row/event residue. Model: one-invalid-fact, rollback, close/reopen, SQLite WAL.
Excludes disk corruption, hostile host mutation, and multi-host writers.
Assurance: deterministic local persistence evidence. Proof: P03..P07.
Boundary: real temporary files and existing APIs. Ceiling: listed cases and ten
runs only. Stop: ambiguous error or non-isolatable mutation returns; never
weaken an assertion.

**Q3 — Scope and completion.** Protected: remediation cannot alter accepted
behavior or move done. Model: exact ranges, environment, regressions, combined
gates, one correction. Excludes B/C, dependencies, external/live systems,
merge/deploy. Assurance: bounded regression and complete listed-ID crosswalk.
Proof: P01,P07..P13. Boundary: owned paths/roles above. Ceiling: 150 minutes and
one correction. Stop: unsupported environment, scope/contract defect, reserved
choice, or new post-correction class returns Project-Architect-first; Owner is
consulted only through M0-D15.
