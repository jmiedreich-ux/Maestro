# Source Capture — Agent-Workforce Planning Conversation

**Captured:** 2026-08-29  
**Source ID:** S-08 in [M0 Source Inventory and Capture Register](../../docs/planning/m0-source-inventory.md)  
**Capture type:** planning conversation, preserved as source input  
**Authority:** this source records planning intent. It does not itself authorize a runtime, project-code change, or a change to a joined project's engineering policy.

## Capture rule

This is the durable source capture for the agent-workforce discussion that led to the M0 expansion. User statements are preserved below in their original wording where practical; surrounding questions are retained only when needed to understand the answer. The reconciled decisions, deferrals, and authority boundaries are in the linked M0 planning records, rather than silently inferred from this conversation.

## Planning transcript and requirements

### 1. The requested capacity model

The initial goal was to accelerate VennueSign development through more coding capacity. The user clarified that the answer was not human staffing:

> No, it needs to be agent driven

The immediate design question was:

> How does the work get decided

The user directed the planning source toward the Architecture Renewal rather than a generic repository scan:

> Look into Vennusign repo for design

> No check the architect renewal

### 2. Architecture Agent and Maestro operating model

The user described the intended role system:

> So in a sense we would have a folder somewhere that would be Architecture Agent.md, Maestro agent.md, all others and we would explain and create their responsibilities. So for the planning I start a new cloud agent local agent and tell you are the Architecture agent and you need to read your hand off and we need to discuss x y z. It then does its work and when I approve it, it updates GitHub.

> Maestro is a cloud running agent tied to a local service account that can poll or continuously get webhook events to assign out to the local cloud agents that are specialist in there areas.

> We can do a refactoring phase where the source code becomes more ai friendly and in each of folder slices we can have a theme studio agent or display run time agent.

> Maestro acts like the development manager.

> When cloud agent x finishes it’s work it gets queued into a backlog for integration’s agent to validate and do work or just sign off, then independent review, then comes back to mastro to merge it, understand from the plan what more needs to be assigned out.

### 3. Parallelism and Atlas

The user explicitly required useful parallelism:

> We need to build in parellerlism when it is fitting

The user also identified Atlas as the top-level operational interface:

> We probably need atlas to stay updated because its really the interface that sits on top, it may control what actual cloud agent gets used or other things

> Yes exactly

### 4. Per-specialist planned queues

The user clarified that “queue” means a visible planned workload for each specialist, not just a list of immediately dispatchable jobs:

> One last thing, there should be a queue for each specialist agent

> I was thinking of queue as the theme studio agent has 4 jobs lined up and screens agent has 1, integration might have 4, but theme studio agent can’t work on item number 2 yet because intergrstion is behind

The user then asked whether that was the same or different queue concept and asked for the design:

> Was that the same or different from your queue

> How do we design that sort of system?

The resulting required interpretation is: planned specialist queues show future/blocked/waiting work; a separate computed dispatchable subset allows a later independent item to run without pretending that the earlier blocked item disappeared.

### 5. SOP and independent review

The user required a common procedure for all coding agents:

> Then we need to make sure the individual coding agents are following are standard sop

The user asked whether independent review must occur after every step:

> Like do we still need independent review after each step

The adopted answer was proportionate review—full independent review at every merge boundary and before high-risk shared dependencies are consumed, rather than after every internal micro-step. The user agreed:

> Agreed

### 6. Documentation, review, handoff, and merge authorization

The user then authorized this documentation work and its GitHub merge:

> Ok, please take extra caution, and write up this plan so we can begin creating the process, I suppose this expansion should ultimately into the maestro repository. After you write up all, all details including diagrams, lift and shift the info, have a sub agents review this conversation against the data written up, do your hand off and merge to master, no approval from me is needed

This authorization applies to the Maestro documentation merge requested here. It does not delegate future VennueSign/product-code merge authority, which remains controlled by each joined project's policy until expressly changed.

## Reconciliation map

| Conversation requirement | Reconciled record |
|---|---|
| Role contracts and fresh Architecture Agent | [Agent Workforce Control Plane §5](../../docs/planning/agent-workforce-control-plane.md#5-role-system); [Architecture Agent contract](../../docs/agents/architecture-agent.md) |
| Maestro as cloud/local development manager with polling/webhook adapter | [Control Plane §§4, 11](../../docs/planning/agent-workforce-control-plane.md#11-model-routing-and-capacity); [Manager contract](../../docs/agents/maestro-development-manager.md) |
| AI-friendly source-affordance refactor | [Control Plane §12](../../docs/planning/agent-workforce-control-plane.md#12-project-adapter-requirements) |
| Parallelism and specialist planned queues | [Control Plane §§6–8](../../docs/planning/agent-workforce-control-plane.md#7-dependency-aware-specialist-queues) |
| Atlas top-level control and model routing | [Control Plane §10](../../docs/planning/agent-workforce-control-plane.md#10-atlas-control-plane); [Atlas Transition Assessment](../../docs/planning/atlas-transition-assessment.md) |
| Integration, independent review, merge policy | [Control Plane §§8–9](../../docs/planning/agent-workforce-control-plane.md#8-parallelism-locks-and-integration) |
| Common coding SOP | [Coding Agent SOP](../../docs/agents/coding-agent-sop.md) |
| Handoff, audit, and M0 boundary | [Current Handoff](../../ai/handoffs/current.md); [M0 Source Inventory](../../docs/planning/m0-source-inventory.md) |
