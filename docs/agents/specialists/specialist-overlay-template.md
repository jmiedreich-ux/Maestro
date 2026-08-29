# Specialist Agent Overlay Template

**Project:** `<project>`  
**Role:** `<specialist role>`  
**Status:** `<proposed | approved | retired>`

## Purpose and architectural boundary

State the outcome this role owns, its change domains, and the architectural boundary it serves. A role is not a blanket permission to change every related file.

## Read first

List the project adapter, approved architecture/design authority, current handoff, decision records, source map, and current graph/packet records required for this role.

## Owned invariants and behavior to preserve

List the customer behavior, contracts, data authority, compatibility rules, and safety properties that this role must preserve. State material non-goals separately.

## Packet boundary

Specify allowed change domains and prohibited boundaries here. The materialized packet, not this template, supplies exact allowed/forbidden file paths, base commit, commands, and worktree limits.

## Queue and dependency rules

Define entry gates, expected upstream/downstream contracts, role rank/serial assumptions, possible independent slices, shared-boundary locks, and when the role must route a result to Integration or NeedsReplan.

## Routing, resources, and verification

State allowed executor classes/models, WIP/resource limits, required validation evidence, and environment restrictions.

## Escalate when

List missing/stale authority, conflicting ownership, behavior/contract ambiguity, high-risk boundary changes, or any reason work is not safe to dispatch.

## SOP relationship

This overlay adds constraints to the joined-project engineering policy and Maestro Coding Agent SOP. It may never weaken either.
