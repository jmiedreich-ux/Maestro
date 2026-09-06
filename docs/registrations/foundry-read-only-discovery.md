# Foundry — Read-Only Registration Discovery

**Status:** Refreshed 2026-09-06 during M3 Wave A (A1) — real, live discovery
via `maestro.github_client`/`maestro.real_discovery` against the GitHub API,
superseding the manual discovery below. **Not yet reviewable**: 9 of 29
schema leaves are genuinely undeclared in Foundry's own docs (see "Refreshed
discovery result" below) — a binding proposal (A2) cannot be produced until
the Owner resolves these. This is the machine-checkable result under
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

**Result:** `reviewable: false`, 20 confirmed / 9 missing / 0 conflicting
leaves. Missing (real, not fabricated — Foundry's own docs genuinely do
not declare these): `delivery.owner_acceptance_policy`,
`delivery.deployment_rollback_policy`, `verification.integration_commands`,
`roles.qa_murphy_policy`, `operations.environment_reference_names`,
`operations.secret_reference_names`, `operations.notification_policy`,
`exceptions.disposition`, `exceptions.items`. These are real open questions
for A2 (several are Maestro-side operational concepts — Murphy, notification
policy — that a project like Foundry would never have reason to declare on
its own; the Owner resolves them as part of the binding proposal, not by A1
inventing an answer).

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
