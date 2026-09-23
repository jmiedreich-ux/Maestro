# Manual milestone retrospective

Manual procedure for a promoted development milestone. It does not allocate runtime work, reopen accepted code, or authorize another milestone.

## Purpose

Compare the delivered milestone with its pinned architecture, milestone requirements and evidence. Identify what was missing or discovered too late, explain measured delay or rework, and save lessons that improve later milestones.

## Required inputs

- Exact promoted milestone and product-master revisions.
- Pinned architecture, milestone requirements, packet specifications and dependency records.
- Packet, integration, independent-review, Quality Assurance, outcome-review and promotion evidence, including cause classifications for blocking findings.
- Saved lifecycle measurements and operation counts. Missing historical measurements remain unknown.

## Manual procedure

1. Trace each stated milestone contribution and required connection to its delivered code and evidence.
2. Record every late-discovered architecture, dependency, setup, integration or verification gap. Classify every blocking correction as `architecture_requirement`, `packet_specification`, `dependency_or_setup`, `implementation`, `integration`, `verification_or_qa`, `provider_or_external`, or `unknown`; state the controlling source or evidence.
3. Use saved measurements to describe queue, preflight, active, waiting, review, integration, Quality Assurance, correction, blocked and wall-time impact. Never infer active time from commit timestamps, message order or calendar gaps.
4. Calculate and save separately: first-pass approval rate, specification-sufficiency rate, and blocking-finding cause distribution. If any applicable finding is `unknown`, label the affected measure partial.
5. Save two plain lists:
   - **Architecture and delivery gaps:** requirement/source, observed condition, measured impact or `unknown`, and the existing authority or future work that may address it.
   - **Lessons learned:** a specific preparation, execution or reporting change, its evidence, and the later milestone or process it can improve.
6. Save the record in the current handoff or the service's durable execution record before starting the next development milestone.

## Applying lessons

Before the next development milestone starts, the Coordinator reads applicable earlier retrospectives and saves a safeguard checklist for that milestone. Each checklist entry names the lesson, the concrete prevention action, the delivery stage, the evidence required and its owner. A later milestone does not start until this checklist exists; the listed actions run at their named stage and their results are retained with the milestone evidence.

When a repeatable defect exposed an unverified prerequisite or missing connection, name one focused check at the stage where the same failure could first be observed. Reuse its recorded observation for later affected work when the environment and source still match; do not expand every packet into a general regression suite. Feed the actual correction cause and measured delay, or `unknown`, into the next feature's current-code investigation and walkthrough. This records whether the changed delivery method reduces late integration and correction work without changing a completed milestone's evidence.

For example, a measurement lesson starts a manual lifecycle log at dispatch; a real-host validation lesson schedules a protected smoke check at the first integrated candidate; a receipt lesson validates candidate, run and source identities before accepting QA evidence; and a scope lesson attaches the stated inclusion and exclusion boundary to the outcome-review input. The checklist applies lessons without silently expanding a milestone's confirmed scope. A needed scope change follows the existing architecture and Owner authority.

## Boundaries

This retrospective is not Quality Assurance, an independent review or a correction round. It cannot change the completed milestone result, invent a defect from a preference, add work to a later milestone automatically or alter scope. A required outcome found incomplete before promotion uses the normal milestone-gap process. A concern discovered after promotion follows the existing architecture and Owner change authority.

The Coordinator performs this procedure manually until Maestro implements equivalent record collection and presentation. Later automation preserves the same evidence, unknown-measurement and authority boundaries.
