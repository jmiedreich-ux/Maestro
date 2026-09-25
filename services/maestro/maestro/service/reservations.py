"""Atomic project start and re-registration reservations.

The idle check and the reservation share one immediate write transaction, so
competing requests recheck committed state after they acquire it and only one
can hold a project. Reservations belong to one project; other projects stay
available.
"""

from __future__ import annotations

from dataclasses import dataclass

from maestro.foundation import (
    Database,
    DomainMigration,
    Transaction,
    canonical_identifier,
)


RESERVATION_MIGRATION = DomainMigration(
    domain="service_project_reservations",
    version=1,
    identity="service-project-reservations-v1",
    statements=(
        """
        CREATE TABLE service_project_reservations(
            project_id TEXT PRIMARY KEY
                REFERENCES service_projects(project_id) ON DELETE RESTRICT,
            purpose TEXT NOT NULL CHECK(purpose IN ('start', 're_registration')),
            holder_id TEXT NOT NULL
        )
        """,
    ),
)

PURPOSES = frozenset({"start", "re_registration"})
# Only these activity states are known to be finished. Any other state,
# including an unknown one, means the project is not idle.
_ENDED_STATES = ("cancelled", "completed", "failed", "stopped")


class ReservationError(ValueError):
    """A typed refusal; the caller's transaction is left unchanged."""

    def __init__(self, code: str, message: str, **fields: object) -> None:
        super().__init__(message)
        self.code = code
        self.fields = dict(fields)


@dataclass(frozen=True)
class Reservation:
    project_id: str
    purpose: str
    holder_id: str


class ProjectReservations:
    """Repository for the one reservation a project can hold."""

    def __init__(self, database: Database) -> None:
        if not isinstance(database, Database):
            raise TypeError("reservations require the service Database")
        self.database = database
        # Reservations reference projects, so the activity domain registers first.
        from .activities import ActivityRepository

        ActivityRepository(database)
        database.registry.register(RESERVATION_MIGRATION)
        database.initialize()

    def reserve(
        self,
        transaction: Transaction,
        project_id: str,
        purpose: str,
        holder_id: str,
        *,
        check_unresolved: bool = False,
    ) -> Reservation:
        """Reserve an idle project inside the caller's write transaction.

        Re-registration, and any start that asks for it, also refuses while an agent run or external write
        is not confirmed ended.
        """
        canonical_identifier(project_id, "project_id")
        canonical_identifier(holder_id, "holder_id")
        if purpose not in PURPOSES:
            raise ValueError("reservation purpose is invalid")
        if transaction.execute(
            "SELECT 1 FROM service_projects WHERE project_id = ?", (project_id,)
        ).fetchone() is None:
            raise ReservationError(
                "project_not_found", "the project does not exist", project_id=project_id
            )
        held = transaction.execute(
            """
            SELECT purpose, holder_id FROM service_project_reservations
            WHERE project_id = ?
            """,
            (project_id,),
        ).fetchone()
        if held is not None:
            if (held[0], held[1]) == (purpose, holder_id):
                return Reservation(project_id, purpose, holder_id)
            raise ReservationError(
                "project_reserved",
                "the project is already reserved",
                project_id=project_id,
                purpose=held[0],
            )
        placeholders = ", ".join("?" for _ in _ENDED_STATES)
        busy = transaction.execute(
            f"""
            SELECT activity_id, state FROM service_activities
            WHERE project_id = ? AND state NOT IN ({placeholders})
            ORDER BY rowid LIMIT 1
            """,
            (project_id, *_ENDED_STATES),
        ).fetchone()
        if busy is not None:
            raise ReservationError(
                "project_not_idle",
                "the project has an activity that is not known to be finished",
                project_id=project_id,
                activity_id=busy[0],
                activity_state=busy[1],
            )
        if purpose == "re_registration" or check_unresolved:
            self._refuse_unresolved(transaction, project_id)
        transaction.execute(
            """
            INSERT INTO service_project_reservations(project_id, purpose, holder_id)
            VALUES (?, ?, ?)
            """,
            (project_id, purpose, holder_id),
        )
        return Reservation(project_id, purpose, holder_id)

    def _refuse_unresolved(self, transaction: Transaction, project_id: str) -> None:
        """Agent runs and external writes that are not confirmed ended also mean the project is not idle."""
        tables = {row[0] for row in transaction.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
        if "service_agent_runs" in tables:
            run = transaction.execute(
                """
                SELECT r.run_id, r.state FROM service_agent_runs r
                JOIN service_agent_assignments a ON a.assignment_id = r.assignment_id
                WHERE a.project_id = ? AND r.state IN ('reserved', 'running', 'stopping', 'blocked') LIMIT 1
                """,
                (project_id,),
            ).fetchone()
            if run is not None:
                raise ReservationError(
                    "project_not_idle", "an agent run is not confirmed ended",
                    project_id=project_id, run_id=run[0], run_state=run[1],
                )
        if "service_registration_publications" in tables:
            write = transaction.execute(
                """
                SELECT p.operation_id, p.state FROM service_registration_publications p
                JOIN service_registrations g ON g.activity_id = p.activity_id
                WHERE g.project_id = ? AND p.state IN ('prepared', 'writing', 'verified') LIMIT 1
                """,
                (project_id,),
            ).fetchone()
            if write is not None:
                raise ReservationError(
                    "project_not_idle", "an external write is not confirmed resolved",
                    project_id=project_id, operation_id=write[0], operation_state=write[1],
                )

    def release(
        self, transaction: Transaction, project_id: str, holder_id: str
    ) -> bool:
        """Release the holder's reservation; other holders are never released."""
        cursor = transaction.execute(
            """
            DELETE FROM service_project_reservations
            WHERE project_id = ? AND holder_id = ?
            """,
            (project_id, holder_id),
        )
        return cursor.rowcount == 1

    def held(self, project_id: str) -> Reservation | None:
        with self.database.read_connection() as connection:
            row = connection.execute(
                """
                SELECT purpose, holder_id FROM service_project_reservations
                WHERE project_id = ?
                """,
                (project_id,),
            ).fetchone()
        return None if row is None else Reservation(project_id, row[0], row[1])


def refuse_other_starts(transaction: Transaction, project_id: str, holder_id: str) -> None:
    """Refuse work for a project reserved by someone else; the holder's own work proceeds."""
    exists = transaction.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'service_project_reservations'"
    ).fetchone()
    if exists is None:
        return
    held = transaction.execute(
        "SELECT purpose, holder_id FROM service_project_reservations WHERE project_id = ?", (project_id,)
    ).fetchone()
    if held is not None and held[1] != holder_id:
        raise ReservationError(
            "project_reserved", "the project is reserved; only the reserving activity may start work",
            project_id=project_id, purpose=held[0],
        )
