# M2 outcome review — blocked

Candidate: `cfde1dce51b1c11ee60432bac26d114bcfc3444e` on `maestro/manual-20260917-supervised-shared-processes/milestone/supervised-shared-processes`.

All five allocated M2 packets are integrated and independently reviewed. Focused agent checks (37), policy checks (6), two real isolated provider-route checks, and a live systemd-supervised-process check passed.

The independent outcome review found the required composed service path is absent. `service/main.py` does not compose `ProcessPolicyService`, route preflight, workspace/transport, `AgentSupervisor`, and `SessionManager`; the delivered modules remain providers/components. Therefore the required real assignment cannot be supervised, restart-reconciled, session-linked, and observed through the installed service. This is `UNTESTED` and blocks M2 promotion.

This cannot be corrected within any confirmed M2 packet: the required service integration path is not a permitted output of the five packets, which explicitly defer later consumer/lifecycle integration. An architectural decision is required to add an in-scope bounded correction packet or amend the confirmed milestone scope.

Do not start M3. Preserve the candidate branch and retained QA artifacts under `var/qa`.
