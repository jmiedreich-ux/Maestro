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
| Agent workspaces | `/var/lib/maestro/workspaces`, mode 0770 for the shared workspace group |
| Process schema bundles | `/opt/maestro/schemas/<name>/<version>/` |
| Owner credential | `~OPERATOR/.config/maestro/owner.token`, operator-owned, mode 0600 |
| Terminal configuration | `~OPERATOR/.config/maestro/cli.toml`, operator-owned, mode 0600 |
| Service unit | `/etc/systemd/system/maestro.service` |

The plaintext Owner credential is written only to the operator file. The
service configuration contains its SHA-256 digest. The agent identity is not a
member of the service group and cannot read `/etc/maestro`, the database, the
Owner home, or either credential. Both service and agent identities share only
the workspace group. Never place credentials in a workspace or repository.

Installation copies versioned schema resources declared by the installed
package. Bundles are local, immutable directories named `<name>/<version>` and
must contain `schema.json`; linked or malformed bundles fail installation.

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

## Safe isolated installation tests

Automated tests must use `--staged-test` with a newly created absolute `--root`
and an operator home inside that root. Staged mode never creates accounts,
calls `systemctl`, or writes `/etc`, `/var`, `/opt`, or a real home outside the
test root. It requires explicit, distinct numeric test identities. Remove only
the run-owned root after retaining the required evidence. Host boot, crash
restart, and real cross-identity denial remain `UNTESTED` unless executed on an
approved disposable Linux/systemd environment.
