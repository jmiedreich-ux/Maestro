# Verify the Maestro development environment

## Outcome and result
Deliver [the first roadmap outcome](../../docs/outcomes/development-environment.md#prepare-a-verified-development-environment). On the actual Linux development host, a developer runs one preflight for a selected feature. It reports every applicable prerequisite and missing item. A real assigned agent starts in a clean, reusable workspace, reads the assigned repository revision and inputs, writes an output, runs a baseline check and exits cleanly. The same preflight reports a deliberately absent prerequisite clearly.

## Existing implementation assessment
Inspect the deployment instructions and current scripts, CLI, agent route and supervisor modules, workspace handling, tests and installed host first. Reuse working checks and launch paths; adapt incomplete ones. Write new preflight or reset behavior only for a demonstrated gap. Source files and local tests do not establish installed readiness.

## Connected path and limits
1. Select an actual development feature and its required host tools, repository access, Owner and service credential status, route, mounts and permissions, ports and dependencies, realistic test target/data, reset method and observable logs. Service revision and running service checks apply only when that feature depends on an installed service.
2. Run one command or entry path that checks all applicable prerequisites, returns non-secret pass/fail evidence and names every missing requirement together. Unavailable checks remain unverified.
3. Create a clean workspace at a pinned source revision, launch the real selected agent, observe its identity and output, run the existing baseline check, and verify clean exit. Reset run-owned data and repeat to show a known-good starting state.
4. Remove one safe prerequisite in a test setup; verify a blocked dispatch and actionable aggregate report. Restore it and re-run. Environment corrections are rechecked outside the coder review count.

## Dependencies and ownership
This is the first feature; no later product outcome is presumed complete. Access to the actual Linux host, selected model route, repository and credentials is necessary for acceptance. Assign a feature owner before dispatch. The owner narrows permitted files after inspecting the source; likely areas are `services/maestro/deploy/`, agent route/supervisor/workspace modules and their focused tests. Do not implement the service or registration as a substitute for a missing environment check. Record small implementation packet notes inside this feature plan only if code changes are needed.

## Verification and stop
Capture host/tool versions, non-secret credential and route status, preflight output, pinned source, agent launch/output/exit, baseline result, reset result and the absent-prerequisite report. Stop and report a real access or route blocker if the actual target cannot be reached; a mock route or documentation-only result cannot close the outcome.
