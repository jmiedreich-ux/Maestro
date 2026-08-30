# Alpha-02 synthetic `maestro run-packet` wrapper

Alpha-02 adds one local command boundary: `maestro run-packet`. It accepts a
declarative local synthetic packet, validates its authority and execution
fields before it creates runtime state, then records one bounded lifecycle
attempt through the Maestro SQLite service boundary.

The wrapper is intentionally not a project coordinator. Its executor is a
Python fixture function, not a subprocess, model, real worker, GitHub action,
or CI invocation. A temporary fixture worktree is created beneath the selected
repository `var/` runtime directory. Structured start/result evidence, the
claim, and exactly one terminal handoff are stored in SQLite.

```text
valid packet -> durable claim -> isolated fixture worktree -> synthetic result
             -> mechanical M0-D05 grade -> one handoff -> stop
```

The grade is deterministic:

- missing commit/diff, a dependency/configuration/placeholder violation, or a
  scope breach produces a coordinator-escalation handoff;
- a committed in-scope result with one or more named gate failures produces
  one targeted-correction eligibility handoff; and
- a committed in-scope result with every named gate passing produces an
  independent-review handoff in `AwaitingReview`.

The command never performs that correction, independent review, merge, packet
selection, project registration, Atlas/API/UI work, or a second worker launch.
Packet-key claims and unique evidence/handoff records make duplicate or restart
invocations observe the prior lifecycle rather than replace it.
