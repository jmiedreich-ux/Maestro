# Produce the work breakdown from saved foundations

## Outcome and result
Closes [Produce a bounded and parallel-ready work breakdown](../../outcomes/architecture-loop.md#produce-a-bounded-and-parallel-ready-work-breakdown): after the foundations are saved, the same architecture activity and the same persistent architect session turn the confirmed outcomes and the saved findings into development milestones, bounded work packets with dependencies and parallel opportunities, and one Quality Assurance plan per milestone. The service checks them deterministically, assigns identities and hashes, and publishes them as the next architecture version. Nothing is scheduled, no worker is launched, no source changes.

## Existing implementation assessment
Reused as built: the architecture activity, its persistent session, the agent run service with its recovery limit (this is the output-correction allowance), linked Owner questions and answers, the finding identity table, the GitHub journaled publication, the discovery index and the terminal view. Gaps found: the activity stopped at saved foundations; the installed schema bundle `architecture-loop@1` has no packet `execution_requirements`, milestone `qa_plan_ref`, Quality Assurance plan or its inventory entry, and a published bundle may not change; there was no operator Quality Assurance catalog; no record carried an earlier record forward; a cancel could not finish while a publication had a definite conflict.

## Decisions
- New bundle `architecture-breakdown@1` (`docs/schemas/architecture-breakdown.schema.json`, packaged and added by the upgrade) holds the extensions and full copies of the shared definitions. Foundation records still use `architecture-loop@1`.
- Foundations lead straight into the breakdown stage. `service/architecture_breakdown.py` validates the architect's `breakdown.json` (local keys, one file) and builds the records; the service assigns `milestone-N`, `packet-N`, `qa-plan-N`, keeps them stable and hashes every file.
- The breakdown is the next version. Foundation records are carried forward by exact reference (not rewritten). Later versions rewrite a record only when its content changed or it links to a rewritten record (links carry versions); every other record is carried forward.
- Deterministic checks: shape, outcome coverage by milestones and packets, a milestone's packets match the packets naming it, dependency links and cycles, parallel packets are independent and state a shared-code boundary when their paths overlap, bounded size, permitted paths and required outputs, saved finding ids, specialist keys, execution requirement values, QA selections against the catalog, script hashes against the source, missing setup scripts planned by a packet of the same milestone.
- Quality Assurance catalog: read from `execution.qa.project_bindings.<project_id>` in the service configuration, validated (test classification only, no secret values), saved once per activity as a non-secret snapshot with its SHA-256 (of the non-secret snapshot), written to the assignment as `qa-catalog.json`. Credential existence is not checked here; Execution owns that.
- Output corrections use the existing run recovery allowance (two automatic attempts per assignment).

## Verification
Unit tests in `tests/maestro/service/test_architecture_breakdown.py` and `test_architecture.py`; real proof on a disposable service with a real Codex architect and a real repository under `var/qa/architecture-live/`.
