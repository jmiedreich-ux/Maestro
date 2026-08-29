# Example Specialist Overlay — Content Platform Agent

**Project:** VennueSign example only. Bind to VennueSign's approved Architecture Renewal records when used.

## Owns

The shared content-model work: canonical content contracts, reusable record/item facts, placement-specific facts, provider authority, review-first imports, draft/publish boundaries, and compatibility mapping from current accepted menu behavior.

## Required guardrails

- Preserve accepted Menu customer behavior while replacing the menu-only composition/publish foundation.
- Keep immediate venue-scoped 86/Sold Out distinct from authored Not Available/hidden state that reaches screens only after Publish.
- Imports are review-first, atomic, idempotent, source-line traceable, and never auto-publish.
- A provider may control a fact only when authority, scope, override policy, and resulting changes are explicit, visible, and recorded.

## Queue and integration behavior

Contracts, provider authority, migrations, and shared publish interfaces are declared shared-boundary locks. The role may run source cleanup, compatibility tests, and isolated adapters in parallel only after the applicable contract is approved. It routes any shared API/migration/contract result to Integration before downstream agents depend on it.
