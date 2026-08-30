# Operating the Alpha-02 synthetic packet wrapper

Run an approved synthetic fixture locally from `services/maestro`:

```bash
python -m maestro.cli run-packet \
  --packet ../../fixtures/alpha/approved-success-packet.json \
  --runtime-dir ../../var/alpha-02-check
```

The command prints a local JSON lifecycle summary. A successful synthetic
fixture reports `AwaitingReview` and `IndependentReview`; it has stopped before
any review, merge, retry, successor selection, or external action.

Use only fixture packets whose executor kind is `synthetic-local`. Packets are
validated before claims, worktrees, SQLite writes, or executor activity. The
runtime directory must remain under this worktree's `var/` boundary; SQLite and
temporary fixture worktrees are local runtime artifacts only.

For a repeated command using the same packet ID, the wrapper returns the
existing durable state and does not launch another synthetic worker. Gate
failure fixtures record one targeted-correction eligibility handoff, while
missing commit/diff, scope, dependency, configuration, or placeholder fixtures
record coordinator escalation and stop.

Alpha-02 has no project registration, real agent, GitHub, CI, credentials,
network, Atlas/API/UI, backup, or USB operation.
