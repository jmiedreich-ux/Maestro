# Local Operating Safety

This file defines the standing safety rules for local Maestro operations. It does not describe the complete product workflow.

## Runtime data

Use an explicit runtime-data directory under the repository's `var/` directory unless an approved configuration defines another safe location.

Delete only a specifically named disposable runtime directory. Never broadly delete `var/` or another shared path. Preserve the database and error details when a run fails so the failure can be reviewed.

## Data integrity

Validate inputs before creating claims, execution records, project records, or other durable state.

Do not edit SQLite records, schema metadata, or migration history manually. Let the service own all database writes and migrations.

Repeat a request only when its identifying facts are unchanged. If the facts change, create a new reviewed request. Never overwrite an earlier result or invent values for missing or conflicting facts.

## Repository access

Use a non-live repository for tests that may alter files or Git state.

When project authority must be reproducible, bind the read to an exact Git commit. Read the pinned commit rather than relying on mutable working-tree or index content.

Reject unsafe paths, unsupported Git objects, malformed configuration, and oversized inputs. Configuration may contain secret reference names, but it must never contain credential values.

## Outcomes

Report incomplete, conflicting, rejected, and failed work honestly. A stored result is evidence of what happened; it is not proof of approval, completion, or successful product operation.

Synthetic fixtures and internal diagnostic commands may be used for focused verification. They must not be presented as the supported end-to-end Maestro operating workflow.
