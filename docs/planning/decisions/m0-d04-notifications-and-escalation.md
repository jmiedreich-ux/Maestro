# M0-D04 — Notifications and Escalation

**Status:** Accepted  
**Decision owner:** Maestro project owner  
**Scope:** Notification policy only; this record does not connect, post to, or grant access to a Slack workspace.

## Decision

Maestro records every important operational change as a durable notification before attempting external delivery. Atlas always shows the same current state, but notification delivery does not depend on Atlas remaining open or on an active chat turn.

Slack is the required first owner-controlled notification channel for V1 unattended operation.

## Required events

| Event | Notification behavior |
|---|---|
| Run or worker starts | Informational: task, role, model/location, and expected next action |
| Known wait begins | Visible immediately: awaited worker/gate, start time, timeout, and next permitted action |
| Worker finishes | Informational: outcome plus the next gate Maestro begins or awaits |
| Verification/review fails or requests rework | Action-needed: failed gate, evidence reference, and current owner |
| Timeout, expired lease, recovery, or resource conflict | Action-needed: blocker and recovery path |
| Owner decision/approval needed | Action-needed: plain question, options, recommendation, impact, and authority link |
| Milestone reaches owner acceptance | Completion-ready: PR/evidence and exact remaining owner action |
| Milestone closes | Completion summary and durable run record |

## Delivery and acknowledgement rules

1. The Maestro database stores a notification before Slack delivery: event, audience, severity, delivery attempts/outcome, and acknowledgement state.
2. Informational events may be grouped into a digest. Action-needed events send promptly to the approved Maestro Slack destination.
3. A failed delivery is a visible operational failure. Maestro never assumes an owner was informed merely because it attempted a message.
4. Repeated notices are grouped and rate-limited. An unresolved critical blocker is escalated again on its declared timeout schedule.
5. Acknowledgement means only that a person saw a message. It does not approve a decision, merge a PR, waive review, or unblock work.
6. Notification content contains task/status/evidence references only—never secrets, credentials, or unredacted sensitive traces.

## Slack setup boundary

Slack is configured as a separate least-privilege integration step. Joining the workspace, selecting the Maestro destination channel, and granting the notification scope are explicit setup actions. Atlas remains a live reporting layer regardless of Slack delivery.

## Remaining implementation choice

Select the Maestro Slack channel and configure the least-privilege notification integration before V1 unattended operation.
