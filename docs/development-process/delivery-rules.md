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

The milestone branch receives reviewed features. Assembled QA and outcome review decide its promotion to master. When a passed milestone changes the installed service, CLI, schemas or installer, install the exact promoted master revision using the approved procedure and run post-install health and smoke checks; record success or a blocker before starting a dependent milestone. Before the first service-changing milestone is promoted, implement and verify the merge-triggered installation path against an isolated target: it must install only the exact passed master revision, report failure, preserve configured settings and run post-install smoke checks. Installation applies only to a milestone that changes the installed service, CLI, schemas or installer; other milestones skip it. The first such milestone is [Operate the persistent Maestro service](../outcomes/runtime-service.md#operate-the-persistent-maestro-service); the verified development environment milestone uses the manual procedure. Until then use the approved manual installation procedure and record that automation is unverified. A passed milestone closes; polish does not keep it open. Record timing and delay causes for a retrospective, then improve the relevant preflight, prerequisite check or rule when a real gap is found.
