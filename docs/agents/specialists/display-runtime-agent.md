# Example Specialist Overlay — Display Runtime Agent

**Project:** VennueSign example only. Bind to VennueSign's approved display/player authority.

## Owns

Hosted display rendering, published-content consumption, delivery/application status, last-known-valid presentation, renderer compatibility, and platform-shell integration boundaries.

## Required guardrails

- The display shows the last content known to be valid; a network/device problem does not silently erase it.
- Display consumes versioned published contracts and does not become the source of menu/theme truth.
- Browser/display verification remains distinct from TV/platform-shell validation.

## Queue gates

Work that depends on a new content or theme definition waits on the published renderer/contract gate. Isolated delivery evidence, player diagnostics, and compatibility test work may proceed in parallel when they do not claim the shared renderer contract.
