# M0-D06 — Project Manifest Contract

**Status:** Accepted  
**Scope:** The small project-owned binding used when a repository joins Maestro.

## Decision

Each joined repository has one thin, versioned manifest named `maestro.project.yaml`.
It binds that project to a named Maestro process and adapter version.

The manifest contains only project-specific facts and declared exceptions. It does
not copy the shared Maestro workflow, create a second planning system, or grant
new authority.

## Required contents

| Area | Manifest records |
|---|---|
| Identity | Project name, repository identity, default branch, adapter version, Maestro process version |
| Authority | Architecture/plan, handoff, and project-rule paths; task/issue convention |
| Delivery | Branch, PR, merge, owner-acceptance, deployment, and rollback policy |
| Verification | Declared build, test, integration, UI/QA commands; evidence and `UNTESTED` rule |
| Routing | Eligible worker routes, independent reviewer route, Murphy/remote-QA policy |
| Operations | Named environment and secret references only, resource locks, notification policy |
| Exceptions | Stricter project rules or explicit exceptions to the shared process |

Secret values, personal credentials, live operational state, task queue state,
and implementation instructions do not belong in the manifest.

## Registration behavior

`maestro project register` first discovers the existing project read-only and
proposes this file. It creates or changes the file only in the small approved
binding PR defined by M0-D02. Maestro then dry-runs the manifest without
dispatching work. The project becomes registered only after that PR is merged
and the dry run succeeds.

For a new project, `maestro project create` generates the same manifest in
its bootstrap PR.

## Guardrails

- The project repository remains authoritative for its code, architecture,
  plans, and engineering rules.
- The shared Maestro process remains versioned in the Maestro repository.
- A manifest may make a rule stricter, but may not weaken Maestro or the
  project's existing safety, review, or approval requirements.
- Maestro's database stores the active operational binding and observations;
  Atlas may report them live but cannot edit the manifest or route work.
- A missing required field blocks registration rather than being silently
  defaulted.

## First application

VennueSign is an existing repository and will receive a proposed
`maestro.project.yaml` only after its read-only registration discovery is
reviewed.
