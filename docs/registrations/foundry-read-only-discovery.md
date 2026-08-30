# Foundry — Read-Only Registration Discovery

**Status:** Discovery complete; binding and dry run blocked on current-work reconciliation.  
**Repository:** `jmiedreich-ux/Foundry`  
**Default branch:** `main`  
**Discovery mode:** Read-only; no Foundry files, issue bodies, assignments, or worktrees were changed.

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

Maestro treats this as a reconciliation blocker. It will not claim, reroute, or use CG-M4-18 as the first proof packet until the coordinator inspects the preserved worktree and updates Foundry's authoritative records.

## Proposed binding

The eventual `maestro.project.yaml` will bind Foundry to repository `jmiedreich-ux/Foundry`, branch `main`, and the existing Foundry authority paths; preserve its packet, review, owner-acceptance, and no-auto-merge policy; use the declared Node/npm and verification commands; and permit local-Qwen execution only for explicitly released, unclaimed packets.

Foundry's existing `atlas.config.json` is observed project material only. It does not grant Atlas authority over Maestro and is not changed by registration.

## Exact next action

Coordinator inspection of the preserved CG-M4-18 worktree: establish whether its diff and gate state qualify for the one permitted targeted correction or require immediate escalation. Then synchronize Foundry's status, tracker, handoff, and issue facts before Maestro produces the binding and dry run.
