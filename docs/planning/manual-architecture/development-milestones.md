# Maestro development roadmap

This roadmap describes how Maestro itself is built. It does not define the planning, execution, or monitoring processes Maestro will provide to registered projects.

## Ordered outcomes

1. **Run an installed, authenticated Maestro workspace.** An Owner can start the service and terminal, open a project workspace, and recover after a restart.
2. **Run and observe supervised agent work.** The service launches a real assigned agent through a selected route, saves its result and activity, and resumes or reports an interruption.
3. **Register and update a project.** The Owner can submit real project sources, answer questions, confirm a reviewed registration, update it, and recover interrupted work.
4. **Develop and confirm project architecture.** A project architect can investigate actual code, define structure and specialist guidance, produce a reviewed development breakdown, and confirm its exact revision.
5. **Execute and integrate development work.** A confirmed project can run assigned work, review connected results, integrate eligible changes, and recover failures within its limits.
6. **Verify and close a milestone.** Assembled QA checks a usable result, records evidence and gaps, and promotes an eligible milestone.
7. **Monitor and control active work.** The Owner can see current activity, blockers, decisions, progress and completion through the workspace.

These are Maestro product outcomes. The detailed behavior of each product area remains in its architecture and product milestone declarations.

## Development planning

Plan Maestro development in this order: outcomes, prerequisite pass, end-to-end features, dependencies, then milestone markers. The prerequisite pass checks environment and host setup, credentials, external services, migration, installation, observability and every assumption on which a feature relies. A blocking prerequisite with its own observable proof becomes a feature.

A feature begins at a real command, screen, API call or event and ends with a saved or visible result. Include its wiring, essential failure handling and recovery. One owner delivers and is reviewed on the connected feature. Split by usable flow, never by technical layer. Only the next milestone's features receive detailed plans; later work stays coarse.

The project architect checks the next feature against real code and traces entry, dependencies, state changes, visible result and failure recovery. Before implementation, a bounded feasibility or pseudocode walkthrough exposes missing scope and environment assumptions. The walkthrough may clarify the feature; it cannot grow the outcome. The owner of the feature saves its packet breakdown inside the feature plan during implementation. No repository-wide packet inventory is planned in advance.

Place a milestone after features form a usable, testable checkpoint. Features merge to its branch after review. Run assembled QA, outcome review and a retrospective before promotion to master. Keep master usable. A changed outcome requires an Owner decision and roadmap update; optional improvements go to later work.

## Current planning state

This roadmap identifies outcomes and their order. Detailed feature specifications, milestone membership, assigned owners and QA evidence are created as each next milestone approaches. An outcome or milestone is not complete merely because it is listed here.
