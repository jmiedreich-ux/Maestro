# Prerequisite pass for the verified development environment

Status: **not proved**. This is the planning coverage record, not a passing host check. Every assumption must have a proving check or a reasoned exclusion before the feature plan is confirmed for dispatch. For each item ask: **What must exist? How will we prove it? What happens if it is absent?** Use the [single environment contract](../development-process/environment-contract.md) as the full check list.

| Assumption or category | Proof or exclusion for this feature | Current status and absent-path response |
|---|---|---|
| Actual Linux host and tools | Record host and versions; baseline runner | Unverified; stop affected dispatch |
| Repository and clean workspace | Pin source, read/write output, reset and repeat | Unverified; stop launch |
| Owner/service credentials | Check non-secret status on host | Unverified; block affected operation |
| Claude OAuth | Check selected route authentication and expiry | Reported expired; verify, renew if needed, then rerun |
| `agents.toml` and selected model route | Inspect actual config and observed identity | Reported route concern; verify before launch |
| GitHub app Administration: read | Check whether selected operation requires it and current app permission | Reported missing; block only an operation that requires it |
| Protected-branch test case | Verify the private QA repository's plan and branch-protection availability; use an eligible isolated repository if that case is required | Reported unavailable on the private QA repository without GitHub Pro; cannot pass this case there. Do not weaken the test or infer that ordinary writes are blocked |
| Mounts, permissions and egress | Check isolated workspace and route destination | Unverified; block launch |
| Service installation, ports and store | Excluded for baseline agent run; required for a later service feature | Excluded for baseline with reason; later check unverified |
| Install/upgrade and rollback | Baseline tools/install versions; service upgrade excluded until applicable | Unverified for baseline tools; service upgrade excluded |
| Data migration and reset | Reset run-owned workspace data; service schema migration excluded for baseline | Unverified reset; schema excluded until applicable |
| Logs, smoke and failure report | Real output/exit, baseline check, absent-prerequisite case | Unverified; no outcome acceptance |

Implementation owner: Claude Code. Evidence reviewer: Codex. No prerequisite pass or outcome completion is recorded. The feature owner must replace the unverified cells with observed evidence, revision and date, or a justified exclusion; a simulated route or unknown permission cannot close the pass.
