# System Foundations

This file records reusable technical foundations already present in Maestro. It is not a plan, completion record, or proof that the system works end to end.

## Local service and data

Maestro uses a local Python service and SQLite for durable operational state. The runtime-data directory is configurable and defaults to the repository's `var/` directory. SQLite uses foreign-key enforcement, write-ahead logging, versioned schema migrations, and transactional writes.

Durable operations use stable request identities so repeated requests return the existing result or reject conflicting reuse. State changes use concurrency controls where needed.

## Packet processing

Packet inputs are validated before durable state is changed. Claims, execution evidence, results, and handoffs are stored so work can be inspected after a process restart.

Execution can be restricted to approved paths and named checks. Invalid configuration, unauthorized paths, incomplete evidence, and failed checks are recorded as controlled outcomes instead of being treated as successful work.

## Project discovery

Repository facts are normalized as confirmed, missing, or conflicting. A proposed project binding is produced only when the required facts are complete and conflict-free. Missing information is not guessed. Malformed input is rejected before related project state is written.

## Project authority

Project configuration and declared authority files can be read from an exact local Git commit. Reads come from the pinned commit rather than mutable index or working-tree content.

The loader rejects unsafe paths, unsupported Git objects, unknown configuration fields, malformed references, and oversized inputs. A complete result produces a reviewable project candidate. An incomplete or conflicting result produces a blocked record with evidence.

## Current boundary

These foundations provide controlled storage, validation, discovery, and evidence handling. They do not prove full agent coordination, independent review, automatic merging, Atlas control, or complete end-to-end operation.
