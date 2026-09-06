# Foundry — Read-Only Registration Discovery

**Status:** Refreshed 2026-09-06 during M3 Wave A (A1) — real, live discovery
via `maestro.github_client`/`maestro.real_discovery` against the GitHub API,
superseding the manual discovery below. **Now fully reviewable**: 20 of 29
schema leaves are Foundry's own real declared facts; the other 9 (see below)
are explicit Architect decisions applying Maestro's own already-Owner-
approved standing policy (M0-D03/D04/D10), not fabricated Foundry-specific
facts — each cited to its own source decision. A real `proposed_binding` now
exists. This is the machine-checkable result under
`tests/m3_wave_a/test_foundry_real_discovery.py`, not free-standing prose.
**Repository:** `jmiedreich-ux/Foundry`  
**Default branch:** `main`  
**Discovery mode:** Read-only; no Foundry files, issue bodies, assignments, or worktrees were changed.

## Refreshed discovery result (2026-09-06, real)

Fetched live via the Foundry GitHub App (installation `157167451`):
`AGENTS.md` (9,593 real characters), `package.json` scripts, the repo root
listing, `docs/features/` listing, `PROJECT_STATUS.md`, and
`tracker/assignments.json`. Full cited mapping lives in
`tests/m3_wave_a/test_foundry_real_discovery.py`'s `FOUNDRY_SNAPSHOT`.

**Confirmed stale, now corrected:** the "Current work discovered" section
below (CG-M4-18 disputed/in-progress across three sources) is **no longer
Foundry's real state**. `PROJECT_STATUS.md` now reads: *"M4-18 merged
through PR #56 after the local Qwen run was stopped before its required
commit and the coordinator completed the browser packet... Resume at
CG-M4-19 only."* This confirms, concretely, the exact staleness this
document's own original text warned it would have — real discovery must
be re-run before registration, not reuse this cached snapshot, which A1
now does mechanically via `real_discovery.evaluate_snapshot`.

**Result:** `reviewable: true`, 29 confirmed / 0 missing / 0 conflicting
leaves. The 9 leaves Foundry's own docs never declared (several are
Maestro-side operational concepts a project like Foundry would have no
reason to declare on its own — Murphy QA policy, notification policy) are
resolved by explicit Architect decision, each citing its own source policy:
`delivery.owner_acceptance_policy` (M0-D10 step 5: owner acceptance, no
automatic merge), `delivery.deployment_rollback_policy` (M3 deploys nothing
at this milestone), `verification.integration_commands` (Foundry's own full
declared check suite — no separate gate exists), `roles.qa_murphy_policy`
(master plan §8: manual/Owner-approved, not applicable here),
`operations.environment_reference_names` (none needed — no deployment
target in M3), `operations.secret_reference_names` (`GITHUB_APP_PRIVATE_KEY`
— the one real secret this milestone needs, already stored via W0.1/W0.2),
`operations.notification_policy` (M0-D04, no Foundry-specific addition),
`exceptions.disposition`/`exceptions.items` (`"none"`/`[]` — none found or
declared).

## A2 — real registration proof (2026-09-06)

Ran the real `maestro.project.yaml` (translating the facts above into
`project_manifest.py`'s actual schema — a different schema from the
inventory shape used for A1) through the real, already-accepted
`ProjectAuthorityLoader` against a locally-cloned, never-pushed copy of
Foundry at its real current HEAD (`5e01f5a0d02c78ced41a915042b49dd8ffd666c9`).
Result: `disposition: Reviewable`, 41/41 facts confirmed, and a real
`projects` row genuinely created
(`('foundry', 'jmiedreich-ux/Foundry', 'main', 'Candidate')`). Permanent,
network-free regression test: `tests/m3_wave_a/test_foundry_real_registration.py`.

## A3 — real dry run (2026-09-06)

Ran Foundry's actual declared gates for real against a clean clone of its
real current HEAD (same commit as above), via `maestro.check_runner`:

- `npm run check` — real pass.
- `npm run build` — real pass (Vite build, 82 modules, `dist/` produced).
- `npm run test:foundation` — real pass, 11/11 (Vitest).
- `npm run test:browser` — real pass, 83/83 (Playwright, Chromium).

Confirms Foundry's binding is currently honest: every declared gate is
real, runnable, and green on its actual current state, before anything
depends on it. No packet was claimed or dispatched.

## What Foundry already provides

- A mature repository contract in `AGENTS.md`, including scoped packets, required commits, exact gates, independent review, handoff, and owner acceptance rules.
- Approved Control Gallery authority under `docs/features/control-gallery/`, with M1–M3 accepted and M4/M5 defined.
- Node 22, npm 10, TypeScript, Vite, Vitest, and Playwright on a Linux-compatible workflow.
- Declared commands: `npm run check`, `npm run build`, `npm run test:foundation`, and `npm run test:browser`; packet-specific TypeScript and diff checks are additionally required where the packet says so.
- The same tested no-diff/no-commit rejection, targeted-correction, and R3/R4 invariant rules that Maestro must preserve.

## Current work discovered

Issue #6 lists CG-M4-18 through CG-M4-21 as the four remaining M4 browser packets, assigned to local Qwen. M5 remains unplanned. M4-18 owns only `tests/overlays/popover/**`.

The current records disagree about CG-M4-18:

| Source | Recorded state |
|---|---|
| Issue #6 | Unchecked and assigned to local Qwen |
| `tracker/assignments.json` | `in_progress` |
| `PROJECT_STATUS.md` and `ai/handoffs/current.md` | Owner-paused; an uncommitted Popover draft/worktree is preserved as unaccepted evidence |

M4-18 is now being completed under Foundry's existing process. This historical discrepancy does not block Maestro Alpha: Maestro will not claim, reroute, or use M4-18. Before Foundry onboarding begins after Alpha, discovery is refreshed against the then-current Foundry records.

## Proposed binding

The eventual `maestro.project.yaml` will bind Foundry to repository `jmiedreich-ux/Foundry`, branch `main`, and the existing Foundry authority paths; preserve its packet, review, owner-acceptance, and no-auto-merge policy; use the declared Node/npm and verification commands; and permit local-Qwen execution only for explicitly released, unclaimed packets.

Foundry's existing `atlas.config.json` is observed project material only. It does not grant Atlas authority over Maestro and is not changed by registration.

## Sequencing

Maestro Alpha is completed and accepted first, without changing Foundry. M4-18 completes through Foundry's existing process. After Alpha, Maestro refreshes this read-only discovery and registers Foundry only against the next explicitly released, unclaimed packet. That packet becomes the first Maestro-controlled Foundry proof.
