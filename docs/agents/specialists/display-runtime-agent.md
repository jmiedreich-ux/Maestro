# Display Runtime Specialist Example

This example follows the repository-wide rules in [AGENTS.md](../../../AGENTS.md). A joined project must provide its own approved display authority.

## Purpose

Own hosted display rendering, published-content consumption, delivery status, last-known-valid presentation, renderer compatibility, and platform-shell boundaries.

## Guardrails

- Continue showing the last content known to be valid when a network or device problem occurs.
- Consume versioned published content; the display runtime does not become the source of content or theme truth.
- Verify browser rendering separately from device and platform-shell behavior.

## Integration

Work that depends on a changed content, theme, publication, or renderer contract waits for that shared contract and its Integration review.

Independent diagnostics, delivery evidence, and compatibility checks may proceed when they do not change the shared renderer contract.
