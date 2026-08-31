# Alpha-03 Synthetic Project Discovery — Operations

## Purpose

Rehearses project registration by reading one safe synthetic discovery snapshot,
returning an M0-D02 inventory, and persisting a proposed binding only when every
required fact is complete and non-conflicting. Never contacts a real project.

## Commands

### Run one discovery packet

```bash
python -m maestro.cli run-packet \
  --packet fixtures/alpha/alpha-03-complete-discovery-packet.json \
  --runtime-dir var/alpha-03-check
```

### Health check (post-run)

```bash
python -m maestro.cli health --runtime-dir var/alpha-03-check
```

### Run full test suite

```bash
cd services/maestro
python -m unittest discover -s ../../tests/alpha_01 -v
python -m unittest discover -s ../../tests/alpha_02 -v
python -m unittest discover -s ../../tests/alpha_03 -v
```

## Discovery fixture format

Located under `fixtures/alpha/project-discovery/`. JSON object with up to
eight top-level keys: seven area objects (`identity`, `authority`, `delivery`,
`verification`, `roles`, `operations`, `exceptions`) and optional `conflicts`.

| Area | Required leaves |
|------|----------------|
| Identity | `project_name`, `repository_identifier`, `default_branch`, `adapter_version`, `process_version` (non-empty strings) |
| Authority | `architecture_paths`, `plan_paths` (non-empty string arrays); `handoff_path`, `rules_sop_path`, `task_issue_conventions` (non-empty strings) |
| Delivery | `branch_pr_merge_policy`, `owner_acceptance_policy`, `deployment_rollback_policy` (non-empty strings) |
| Verification | `build_commands`, `test_commands`, `integration_commands`, `ui_qa_commands` (string arrays); `evidence_rules`, `untested_handling` (non-empty strings) |
| Roles | `specialist_overlays` (string array); `reviewer_route`, `qa_murphy_policy`, `local_cloud_eligibility` (non-empty strings) |
| Operations | `environment_reference_names`, `secret_reference_names`, `resource_locks` (string arrays); `notification_policy` (non-empty string) |
| Exceptions | `disposition`: `none` or `declared`; `items`: unique non-empty string array |

### Conflicts extension

The optional `conflicts` key maps a required dotted leaf path (e.g.
`identity.default_branch`) to an array of at least two distinct valid values.

## Outcomes

| Condition | Status | Handoff | Evidence |
|-----------|--------|---------|----------|
| All leaves confirmed | `AwaitingReview` | `IndependentReview` | inventory + proposed binding + digest |
| Missing or conflicting leaves | `Rejected` | `CoordinatorEscalation` | inventory (no binding) + digest |
| Malformed JSON / unknown keys / schema violation | Error before claim | — | no mutation |
| Fixture name unsafe or file missing | Error before claim | — | no mutation |

## Runtime directory

All SQLite artifacts live in the specified `--runtime-dir` beneath
`var/`. The `discovery_evidence` table stores one row per packet_id:

- `inventory_json`: full inventory with per-leaf status, summary, reviewable flag
- `proposed_binding_json`: binding dict (null when not reviewable)
- `fixture_digest`: SHA-256 hex of raw fixture file

Evidence is immutable after initial insert; replay returns existing terminal
state without altering records.

## Safety constraints

- Fixture resolved path must remain inside `fixtures/alpha/project-discovery/`.
- No real repository access, network, credentials, or secret values.
- One fixture root, one fixture per packet; no general filesystem sandbox.
- All paths validated before any claim, mutation, or SQLite write.
