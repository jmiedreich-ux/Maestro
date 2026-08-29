# Maestro Agent Role Library

This directory holds versioned role contracts for the Maestro agent workforce. A role contract is loaded by a fresh agent instance together with the joined-project adapter and a packet or planning handoff. It is not a replacement for project engineering policy and it is not a reusable chat history.

## Authority hierarchy

1. Joined-project engineering policy and approved design/architecture records.
2. Maestro master plan and common Coding Agent SOP.
3. This role contract.
4. Project specialist overlay.
5. Packet/run-specific instructions.

A lower layer may add constraints. It may never weaken a higher layer.

## Generic roles

| Role | Contract |
|---|---|
| Project Architecture Agent | [architecture-agent.md](architecture-agent.md) |
| Maestro Development Manager | [maestro-development-manager.md](maestro-development-manager.md) |
| Integration Agent | [integration-agent.md](integration-agent.md) |
| Independent Review Agent | [independent-review-agent.md](independent-review-agent.md) |
| QA Agent | [qa-agent.md](qa-agent.md) |
| Every coding worker | [coding-agent-sop.md](coding-agent-sop.md) |

Project-specific specialist overlays and a reusable overlay template live in [specialists/](specialists/).

## Contract standard

Every role contract must declare:

- purpose and scope;
- required inputs and records to read first;
- owned decisions/actions and explicit prohibitions;
- queue behavior and eligible work;
- required outputs, evidence, and handoff destination;
- escalation conditions;
- review/SOP relationship;
- routing and resource constraints.

Any material role change is versioned in this directory and reviewed as process/architecture work. A running packet records the role-contract version it used.
