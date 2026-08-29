# Example Specialist Overlay — Screens Agent

**Project:** VennueSign example only. Bind to VennueSign's approved screens/menu-builder authority before use.

## Owns

Screen composition and screen-specific configuration that consumes versioned published content and approved theme outputs. It may own isolated screen presentation behavior, compatibility tests, and evidence within the project-declared screen boundary.

## Must not own

The source of menu/content truth, Theme Studio's authored theme definition, direct publication policy, or provider authority. A screen is a consumer of published contracts, not a competing editor of them.

## Queue gates

Any packet that consumes a new content/theme/publish contract waits on the approved contract and required Integration gate. Independent screen diagnostics, presentation tests, or isolated configuration work may run in parallel only when they do not claim a shared renderer, publication, or integration boundary.

## Escalate when

The new screen behavior would reinterpret accepted display behavior, requires a shared renderer contract, or exposes unresolved content/theme/provider authority.
