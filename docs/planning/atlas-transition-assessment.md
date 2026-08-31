# Atlas Transition Assessment

## Plain conclusion

Atlas is a valuable planning-record generator and should be retained as source material, but it is not the right operational database or persistent coordinator. Maestro should preserve Atlas's clear repository planning surface while moving live execution state to Maestro's local operational database and making Atlas the live reporting UI over that state.

## Atlas today

Atlas is a reusable Node/GitHub Action that builds a static site from a project's repository Markdown, JSON manifests, and GitHub issues. It produces a deterministic `state.json` orientation file for agents and renders workstreams, milestones, tasks, issue buckets, and owner triage.

Strengths to retain:

- Project-neutral convention and configuration.
- Stable workstream/milestone identifiers and explicit status vocabulary.
- Plain owner-facing triage and `ownerAction` wording.
- Repository-relative records that stay reviewable in the project repository.
- A generated state projection so people and agents see the same planning facts.
- Task parsing that already supports short task IDs, plain task text, and local/cloud location markers.
- Strong validation around record shape and output safety.

## Why it cannot be Maestro's operational core

| Need | Current Atlas model | Maestro target |
|---|---|---|
| Live execution state | Derived at static-site build time from repository files and GitHub | Durable database rows for runs, packets, attempts, waits, events, evidence, retries, and locks |
| Worker completion | No persistent worker subscription or coordinator | Poll-first coordinator with idempotent next actions; webhooks later if useful |
| Waiting visibility | Planning/issue view; no durable worker heartbeat model | Who is awaited, start time, latest worker-reported plan/current step/blocker, ETA/confidence or `unknown`, observation time, expected result, timeout, and next permitted action |
| Task routing | Optional parsed owner and local/cloud marker | Required planned executor location, agent role, model/class, reviewer route, then actual run facts |
| Reporting access | GitHub Action/static site, with GitHub fetches and rate-limit tolerance | Local AI-box reporting UI reading the operational database or local API |
| Recovery | Rebuild static records | Resume safely after restart, duplicate poll, timeout, or stale completion |

## Transition boundary

1. Keep versioned feature briefs, questions, decisions, milestone plans, packet specifications, acceptance records, and project-specific rules in each project repository.
2. Introduce a Maestro project adapter that reads those records and projects the required planning facts into the Maestro database.
3. Store Maestro-only facts only in the database: claims, locks, worker attempts, model fingerprints, events, evidence output, reviews, notifications, waits, retries, and resource reservations.
4. Local Atlas becomes a live reporting UI over this projection. It shows
   current operational facts—including bounded worker-reported progress and an
   honest unknown ETA—as soon as Maestro records them, but it does not request
   worker status or perform orchestration actions. It must not become a second
   editor for project plan/code facts or a direct database client.
5. Preserve Atlas's stable identifiers and concise owner/task language wherever compatible with the new shared schema.

## M0 decisions needed before migration work

- Define the canonical project manifest and record schema Maestro adapters consume.
- Define the first database projection tables and ID mapping from Atlas workstreams/milestones/tasks.
- Decide whether the initial local Atlas UI reuses Atlas presentation code, replaces it, or uses Atlas only as a design/reference source.
- Define how existing project GitHub issue checklists remain synchronized during transition without making GitHub the operational polling database.
- Define the migration path for existing Atlas consumers; do not break their current static-site workflow during M0.
- Define the local Atlas read API, live-update transport, and safe reconnect/snapshot behavior.

## Recommendation

Treat Atlas as the **planning-record ancestor and control-plane presentation reference** for Maestro, not as a codebase to merge wholesale. M0 should extract its record conventions, owner-focused UI behavior, and control-surface requirements into explicit Maestro contracts first. Any code reuse should be decided only after that contract is complete.
