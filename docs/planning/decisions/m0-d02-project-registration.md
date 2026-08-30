# M0-D02 — Project Registration and Bootstrap

**Status:** Accepted  
**Decision owner:** Maestro project owner  
**Scope:** Project onboarding design only; no project is registered or changed by this record.

## Decision

Maestro supports two distinct onboarding paths:

- `maestro project register` for an existing repository.
- `maestro project create` for a new project.

Registration always begins with a read-only discovery pass. Maestro does not overwrite a project's process, architecture, records, tasks, or configuration while discovering it.

## Existing-project registration

`maestro project register` performs these steps:

1. Read the repository, default branch, project rules, current handoff, planning records, issue/PR conventions, declared checks, environments, and deployment/QA policies.
2. Produce an owner-readable inventory of the facts found, missing requirements, and any conflicts with the Maestro shared process.
3. Produce a proposed project binding: adapter identity/version, authoritative paths, project exceptions, specialist overlays, verification routes, and authority boundaries.
4. After review, create one small project-repository PR containing only the approved binding and necessary project-facing records.
5. Run a dry-run proving Maestro can read the binding, observe the repository, validate its declared checks, and report live state without dispatching real work.
6. Mark the project registered only after the binding PR merges and the dry run succeeds.

## New-project creation

`maestro project create` creates the new project record and generates the same minimum project-facing binding from the start. It creates one bootstrap PR for the repository-side records, then runs the same dry-run validation before the project can accept work.

## Required project binding facts

| Area | Required fact |
|---|---|
| Identity | Project name, repository, default branch, adapter version, process version |
| Authority | Architecture/plan paths, current handoff path, project rules/SOP path, task/issue conventions |
| Delivery | Branch/PR/merge policy, owner acceptance policy, deployment and rollback policy |
| Verification | Build, test, integration, UI/QA commands, evidence rules, honest `UNTESTED` handling |
| Roles | Allowed specialist overlays, reviewer route, QA/Murphy policy, local/cloud eligibility |
| Operations | Environment references, secret-reference names, resource locks, notification policy |
| Exceptions | Any stricter project rule or declared exception to the common Maestro process |

## Guardrails

- Registration is not implementation approval.
- A failed or incomplete discovery report cannot be papered over with defaults.
- Maestro records exceptions but may not weaken a project’s existing safety/approval rules.
- The project repository remains the authoritative home for project planning and engineering policy.
- The local Maestro database stores only the operational binding and observed projection needed to coordinate safely.

## First application

VennueSign will use `maestro project register`, not `project create`. Its current architecture-renewal authority must be versioned in VennueSign before any related work is dispatchable.
