# Milestones Remaining — Plain Language

**Written 2026-09-09.** This is the milestone set as it stands, described in
plain terms rather than by number. It is a reading aid over
[M0-D19 §8](decisions/m0-d19-next-milestone-round.md), which holds the full
scope, findings and open questions for each entry. Where the two differ, M0-D19
is the record; this file is not authority.

**The set and its order are still awaiting an Owner ruling** (M0-D19 §14). M5
runs in parallel and is not superseded.

- **M5** — Make Atlas navigable: real tabs and routing, and screens that show
  what the coordination layer is actually doing instead of placeholders.
- **M6** — Find out how well a model actually completes a packet. Reconcile the
  two samples that exist, work out why one failed, then run more packets through
  the loop and record the numbers. Everything after this is guesswork without it.
- **M7** — A CI check that catches code nobody calls: commands with no caller,
  tables nothing writes, components mounted nowhere. The mechanical answer to
  "is this real, or is it scaffolding?"
- **M8** — Back up the database and prove a restore works. Accepted a while ago,
  zero code written.
- **M9** — Decide what a work-graph file actually looks like, then write the
  parser that turns one into rows. No format exists today.
- **M10** — Give Maestro an identity: a service account, a GitHub App, and
  something that actually reads the secrets store. Needed before anything can
  commit on its own.
- **M11** — Be able to run an agent that isn't a coding worker: spawn a role,
  load its contract, talk to a cloud model, route by task. Everything with the
  word "agent" in it depends on this. Biggest item in the round.
- **M12** — The Architect reads a repository and writes the work graph itself,
  instead of work items being hand-typed into JSON. First real agent role, end
  to end.
- **M13** — Serve the work graph to Atlas and wire the real data through, so the
  operator commands that already exist become reachable and the fake cost
  numbers go away.
- **M14** — Tell the Owner when something needs them: the six missing events,
  escalation, acknowledgement, Slack.
- **M15** — The Architect's own loop: break milestones into packets, review
  them, stop, and wait for Owner approval in Atlas. The configuration file
  ships here.
- **M16** — The Development Manager starts actually managing: decides what runs
  next using a cloud model, restarts stuck workers, allocates context, escalates
  to a bigger model.
- **M17** — Real reviewers. An independent one, and an Integration Agent that
  wires the work in and checks the pieces fit. Also fixes the dead end where a
  corrected packet can never be accepted, and restores Owner acceptance.
- **M18** — When a packet turns out to be mis-scoped, split it: part now, part
  later, with a fresh correction budget.
- **M19** — Re-register a project after it changes, superseding the old
  registration without reopening finished work.
- **M20** — Run more than one project at once on shared hardware.

## Not in this list, and unscheduled

M0-D19 §15 flags nine Accepted decision records carrying live obligations that
the round above does not schedule: M0-D13, M0-D10, M0-D12, M0-D05, M0-D17,
M0-D02, M0-D14, M0-D03, and M0-D08/D09.

M0-D19 §9 defers, by name: QA/Murphy, the Decision Fidelity Reviewer,
language-agnostic orphan checking over joined projects, an Atlas host, and the
plain-language start-up runbook.
