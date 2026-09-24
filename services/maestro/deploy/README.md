# Maestro Linux installation

Maestro runs as a persistent, loopback-only `systemd` service. The `maestro`
terminal command connects to that service; closing the terminal does not stop
service work.

## Installed paths and identities

Install the Python package into an isolated environment at `/opt/maestro` so
that `/opt/maestro/bin/maestro-service` and `/opt/maestro/bin/maestro` exist.
Run `deploy/install.py` as root from the same release:

```text
/opt/maestro/bin/python /opt/maestro/share/maestro/deploy/install.py --operator-user OPERATOR
```

The installer creates these separate identities and paths:

| Item | Installed value |
|---|---|
| Service process | user and group `maestro` |
| Agent processes | unprivileged user and group `maestro-agent` |
| Shared workspaces only | group `maestro-workspace` |
| Service configuration | `/etc/maestro/agents.toml`, root:`maestro`, mode 0640 |
| Database and journals | `/var/lib/maestro/maestro.sqlite3`, service-created with mode 0600 |
| Agent workspaces | `/var/lib/maestro/workspaces`, mode 0771; the agent may traverse but not list the hierarchy |
| Process schema bundles | `/opt/maestro/schemas/<name>/<version>/` |
| Owner credential | `~OPERATOR/.config/maestro/owner.token`, operator-owned, mode 0600 |
| Terminal configuration | `~OPERATOR/.config/maestro/cli.toml`, operator-owned, mode 0600 |
| Service unit | `/etc/systemd/system/maestro.service` |
| Agent egress launcher | `/usr/local/libexec/maestro-agent-egress` (service-only sudo rule) |

The plaintext Owner credential is written only to the operator file. The
service configuration contains its SHA-256 digest. The agent identity is not a
member of the service group and cannot read `/etc/maestro`, the database, the
Owner home, or either credential. Both service and agent identities share only
the workspace group. Never place credentials in a workspace or repository.

The root-supervised egress runner reads `service.agent_user` from the protected
service configuration and starts Bubblewrap as that configured account. The
sudo rule permits only the service account to invoke the launcher. Supported
Codex and Claude CLI profile files are opened as no-follow, read-only
descriptors and mounted only at their expected private scratch-home paths; the
agent does not receive the service configuration, database, Owner credential,
or the service profile directory.

The service owns every workspace inode. Run ancestors are traverse-only for the
agent; only the assigned source, input, assignment, output, and scratch leaves
are made accessible before Bubblewrap changes to the agent user-namespace
identity. The egress runner still accepts mounts only for those exact leaves of
the selected run.

Installation copies versioned schema resources declared by the installed
package. Bundles are local, immutable directories named `<name>/<version>` and
must contain `schema.json`; linked or malformed bundles fail installation.

## Registration configuration

`registration.start` is available only when `/etc/maestro/agents.toml` holds a
valid `registration` process table, a `repositories.<profile>` table with its
`github` App identity and allowlists, and a `repository_bindings.<name>` table
binding the project repository to that profile. The agent tool routes come from
the existing `tools` tables. Without them the service still runs and reports
`operation is unavailable` for registration requests.

```text
[repositories.project]
credential_profile = "coordinator-app"
allowed_repositories = ["OWNER/REPOSITORY"]
allowed_branch_patterns = ["registration/*"]
[repositories.project.github]
app_id = 1
installation_id = 2
app_slug = "app-slug"
[repository_bindings.project]
repository = "OWNER/REPOSITORY"
profile = "project"
```

The App private key is the service-only file `~maestro/credentials/<credential_profile>.pem`
(mode 0600, directory 0700, owned by `maestro`). Agents, the terminal and repositories never
receive it or the installation tokens the service creates from it. Registration writes only to
an existing branch that matches the allowlist, has no branch protection and no active rules; the
App needs contents write and administration read permission. The service keeps its source
mirrors, frozen candidates and run journal under `<database folder>/registration`. The Owner
starts a registration from the terminal with `/register OWNER/REPOSITORY docs/project-overview.md`
and answers the questions that follow; confirmation and cancellation are actions in the
registration view.

## Verification and operation

Validate configuration and storage without starting another listener:

```text
sudo -u maestro /opt/maestro/bin/maestro-service --config /etc/maestro/agents.toml --check-ready
sudo systemctl status maestro.service
sudo journalctl -u maestro.service
```

An authenticated terminal read of `/api/v1/workspace` establishes API
readiness; a running process alone does not establish process or registration
readiness. The listener is fixed to loopback and defaults to port 8787.

The unit starts at boot and uses `Restart=on-failure`. To exercise a controlled
restart, record the main PID, send it `SIGKILL`, and verify that systemd assigns
a new PID and the same saved workspace/receipt is readable. Use a dedicated
test database and test Owner credential for this check. Do not perform it
against production state.

Configuration, inaccessible storage, unsupported existing databases, and
migration conflicts make `--check-ready` exit nonzero with `Maestro service is
not ready`. Maestro never substitutes in-memory storage or replaces an
unsupported database. Correct the reported prerequisite, rerun the readiness
check, then restart the unit.

Credential replacement is an explicit administrative reinstall with
`--replace`; it writes a new Owner token and digest together, invalidating the
old token. Replacement verifies every installed schema byte against the
protected manifest and the package copy before changing credentials. A missing
or conflicting immutable bundle fails without rotating the credential; older
manifested versions remain installed. Preserve the protected new token before
restarting. The installer never prints token contents.

Run the read-only installed-host preflight before claiming host evidence:

```text
/opt/maestro/bin/python /opt/maestro/share/maestro/deploy/install.py \
  --verify-installed-host --operator-user OPERATOR
```

Unavailable accounts, paths, systemd state, or identity-switch authority are
printed as `UNTESTED`, and the command exits 2. The preflight deliberately also
reports package entry, boot and controlled crash/restart, terminal-exit
persistence, and durable-request restart as `UNTESTED`: those observations
require the approved disposable-host procedure below and cannot be replaced by
a staged directory or a user unit running as the operator.

## Automatic upgrade

`deploy/upgrade.py` upgrades the installed service to a revision that has passed. A revision is installable only when it is a full commit on `master` that carries a `passed/*` tag; tag the merge commit after assembled QA and outcome review, for example `passed/verified-development-environment`. Anything else is refused.

An upgrade backs up the installed package, deployment files, egress launchers, configuration and database under `/var/lib/maestro/upgrades/<time>/`, stops the service, installs the exact revision, re-renders the egress launchers from the new template with the installed values, and starts the service. Configuration, the Owner credential and provider profiles are never rewritten. Post-install checks require the service to be active, an authenticated workspace read to return 200 and an unauthenticated read to return 401; extra checks can be added with `--smoke`. If anything fails the backup is restored, the service is restarted and checked again, and the command exits 1 (`rolled_back`) or 2 (`rollback_failed`). Each attempt leaves `receipt.json` in its backup folder, and the installed revision is recorded in `/opt/maestro/share/maestro/INSTALLED_REVISION`.

```text
sudo python3 upgrade.py upgrade --source-repository /var/lib/maestro/upgrade-source \
  --revision FULL_COMMIT --owner-token ~OPERATOR/.config/maestro/owner.token --port 18787
```

To install passed revisions automatically, enable the trigger once. It mirrors the repository and starts a timer that fetches `master` and its tags every minute and installs the newest passed revision that is not already installed:

```text
sudo /opt/maestro/bin/python /opt/maestro/share/maestro/deploy/upgrade.py install-trigger \
  --source-repository /var/lib/maestro/upgrade-source --source-url REPOSITORY_URL \
  --owner-token ~OPERATOR/.config/maestro/owner.token --port 18787
```

Anyone who can push a `passed/*` tag to the repository can cause an install, so restrict tag creation to the Owner.

## Development environment preflight

One command applies the [environment contract](../../../docs/development-process/environment-contract.md) to a selected feature. It reports every category as pass, fail, excluded with a reason, or unverified, and lists all missing items together. It exits 0 only when every applicable check passes, and 1 otherwise.

```text
sudo -u maestro /opt/maestro/bin/python -m maestro.agents.preflight \
  --feature NAME --repository PATH --revision REVISION \
  --agents-config /etc/maestro/agents.toml --workspace-root /var/lib/maestro/workspaces \
  --tool codex:gpt-5.6-sol --tool claude_code:claude-opus-4-6 --tool qwen:qwen3.6:27b \
  --credential codex=/var/lib/maestro/.codex/auth.json \
  --credential claude_code=/var/lib/maestro/.claude/.credentials.json \
  --credential qwen=/var/lib/maestro/.qwen/settings.json
```

Run it as the service user to read the protected configuration and credentials; as another user those checks fail and are reported. Optional flags check GitHub (`--github-repository`, `--github-app APP_ID:INSTALLATION_ID:KEYFILE`, `--require-app-administration-read`, `--exercise-github-write`, which creates and deletes one scratch branch), the running service (`--needs-service`) and a Slack receipt log (`--progress-log`, `--require-progress-channel`). `--json` prints the report as JSON. Credential contents are never printed. The local Qwen route also needs the Ollama server reachable at its configured loopback address with the exact model installed.

## Safe isolated installation tests

Automated tests must use `--staged-test` with a newly created absolute `--root`
and an operator home inside that root. Staged mode never creates accounts,
calls `systemctl`, or writes `/etc`, `/var`, `/opt`, or a real home outside the
test root. It requires explicit, distinct numeric test identities. Remove only
the run-owned root after retaining the required evidence. Host boot, crash
restart, and real cross-identity denial remain `UNTESTED` unless executed on an
approved disposable Linux/systemd environment.
