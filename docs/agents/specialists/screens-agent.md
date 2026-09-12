# Screens Specialist Example

This example follows the repository-wide rules in [AGENTS.md](../../../AGENTS.md). A joined project must provide its own approved screen-composition authority.

## Purpose

Own screen composition and screen-specific settings that consume published content and approved theme outputs.

## Boundaries

The role may own isolated presentation behavior, compatibility checks, and evidence inside the declared screen boundary.

It does not own the source of content truth, authored theme definitions, publication policy, or external-provider authority. A screen consumes published contracts; it is not a competing content editor.

## Integration

Work that consumes a changed content, theme, publication, or renderer contract waits for that shared contract and its Integration review.

Independent screen diagnostics and presentation checks may proceed when they do not claim a shared renderer or publication boundary.

Escalate when screen behavior would reinterpret accepted display behavior or requires an unresolved shared contract.
