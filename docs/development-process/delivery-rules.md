# Maestro development delivery rules

These rules govern people and agents building Maestro. They do not prescribe how Maestro will execute work for registered projects.

## Feature boundary

Each feature has one observable finish line, one owner and a connected implementation. The owner includes necessary wiring, essential errors and recovery. Packet notes are saved within the feature plan as progress and recovery context; they are not separate repository planning files. Delegation to other agents is explicit, and the owner still delivers the whole flow.

Before dispatch, use the existing implementation assessment. Reuse or adapt a working path whenever it can meet the feature's result; authorize replacement only for a recorded technical or behavioral incompatibility. A new feature should close the demonstrated gap, not recreate working code. Provide a short brief pointing to authoritative sources. Check the [single environment contract](environment-contract.md) with one preflight command. At each milestone start rerun its applicable checks and a small smoke check. If setup is absent, report the exact blocker; do not improvise a substitute or count it as a code defect. Use a known-good workspace and perform a small authorized feasibility check for an uncertain route.

## Review and correction

Review the finished connected feature once, with one targeted correction by default. Reviewers check the required result and material in-scope failures proportionately. An unresolved blocker after that allowance goes to the architect for a determination and the Owner for a decision. A split or rename does not reset the allowance.

Classify a finding before acting:

| Finding | Action |
| --- | --- |
| In-scope defect | Targeted correction |
| Missing in-scope work | Bounded supplement within the feature |
| Changed outcome | Owner decision and roadmap update |
| Optional improvement | Future work; do not block closure |
| Unavailable required check | Keep affected work unverified |
| Environment failure | Fix setup and rerun preflight outside code review limits |

The milestone branch receives reviewed features. Assembled QA and outcome review decide its promotion to master. When a passed milestone changes the installed service, CLI, schemas or installer, tag the promoted master commit `passed/<plain name>`. The [automatic upgrade](../../services/maestro/deploy/README.md#automatic-upgrade) installs only that exact revision, preserves configured settings, runs post-install health and smoke checks and restores its backup on failure. Record its receipt or blocker before starting a dependent milestone. A milestone that does not change these skips installation, and only the Owner-approved promotion step creates `passed/*` tags. A passed milestone closes; polish does not keep it open. Record timing and delay causes for a retrospective, then improve the relevant preflight, prerequisite check or rule when a real gap is found.

## Autopilot

The autopilot works through the [ordered outcomes](../planning/outcomes.md) without waiting for the Owner. The Owner has delegated these decisions to it:

- **Accepting an outcome.** Accept it when every acceptance criterion is met with real evidence or carries an accepted exception. Do not keep working on anything that can wait; record it as an accepted exception and move on. Do not polish.
- **Promoting.** Tag the merged master commit `passed/<plain name>`. The timer installs it when the installed service changes.
- **Shaping the work.** Map each outcome to existing code and the installed host first. An outcome may need several features, each with one finish line and one owner; an outcome that is mostly built may need none. Plan only what the gap requires.
- **Independent review.** Every feature is reviewed once by a different agent than the one that built it, by default Codex, against the code and real evidence rather than the builder's summary. Apply one targeted correction. A finding that changes the outcome goes to the Owner.
- **Continuing.** After accepting an outcome, start the next one in roadmap order.

There are no blockers. When something is missing or fails, work through it: try another route, tool, agent or credential source, build the missing piece, or choose the most sensible default for a decision and record the choice in the handoff. If an acceptance criterion truly cannot be met after real attempts, file it as an accepted exception with what was tried and continue. The loop ends only when every outcome in the roadmap is closed; if usage runs out it waits and resumes. Record any temporary obstacle in the checkpoint with what is being tried next. Safety limits still hold: never expose credentials, rewrite history, or delete installed data or backups; find a safe path instead.
