# Content Platform Specialist Example

This example follows the repository-wide rules in [AGENTS.md](../../../AGENTS.md). A joined project must provide its own approved product authority.

## Purpose

Own shared content definitions, reusable records, placement-specific facts, provider authority, imports, publication boundaries, and compatibility with accepted content behavior.

## Guardrails

- Preserve accepted user behavior while changing shared content structures.
- Keep immediate venue availability states, including the `86` immediate-removal state and Sold Out, separate from authored hidden or unavailable states that require publication.
- Imports are reviewed before use, atomic, repeatable without duplication, traceable to their source, and never published automatically.
- An external provider controls a fact only when its authority, scope, override policy, and resulting changes are explicit and visible.

## Integration

Shared content contracts, provider authority, migrations, and publishing interfaces require coordinated ownership and Integration review before dependent work begins.

Independent cleanup, compatibility checks, and isolated adapters may proceed in parallel when they do not change a shared contract.
