"""M4.02 — real staleness detection.

Real threshold, not a newly-invented number: a `Running` attempt whose
real lease has already expired (`leases.expires_at < now`).
`DispatchOrchestrator` (M4.01) re-extends the lease by a real
`lease_extension_seconds` on every successful heartbeat — so an
expired lease on a still-`Running` attempt is definitionally one that
has gone the whole real extension window without a successful
heartbeat, a signal `start_attempt_execution`/`heartbeat_attempt_
execution` already enforce elsewhere in this codebase, not a second,
independently-guessed value.

Read-only, matching `read_api.py`'s own established pattern: a fresh
process opens its own read-only connection to the real database file
directly, rather than reaching into `OperationalStateStore`'s own
internals.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from .config import RuntimeConfig


@dataclass(frozen=True)
class StaleAttempt:
    """One real `Running` attempt whose real lease has already expired."""

    attempt_id: str
    packet_id: str
    lease_id: str
    attempt_version: int
    packet_version: int
    lease_version: int
    expires_at: str


def find_stale_attempts(config: RuntimeConfig, now: str) -> list[StaleAttempt]:
    """Real, read-only: every `Running` attempt whose real, `Active`
    lease has already expired as of ``now``. Never mutates state — real
    recovery's own separate write (M4.03) is the only thing that acts on
    what this finds.
    """
    connection = sqlite3.connect(
        f"file:{config.database_path.as_posix()}?mode=ro", uri=True, timeout=5.0,
    )
    try:
        rows = connection.execute(
            "SELECT a.attempt_id, a.packet_id, a.lease_id, a.version, p.version, l.version, l.expires_at "
            "FROM attempts a "
            "JOIN packets p ON p.packet_id = a.packet_id "
            "JOIN leases l ON l.lease_id = a.lease_id "
            "WHERE a.state='Running' AND l.state='Active' AND l.expires_at < ? "
            "ORDER BY a.attempt_id",
            (now,),
        ).fetchall()
    finally:
        connection.close()
    return [
        StaleAttempt(
            attempt_id=str(row[0]), packet_id=str(row[1]), lease_id=str(row[2]),
            attempt_version=int(row[3]), packet_version=int(row[4]), lease_version=int(row[5]),
            expires_at=str(row[6]),
        )
        for row in rows
    ]
