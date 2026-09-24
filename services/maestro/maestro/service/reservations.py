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
_ENDED_STATES = ("cancelled", "completed", "failed")


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
    ) -> Reservation:
        """Reserve an idle project inside the caller's write transaction."""
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
        transaction.execute(
            """
            INSERT INTO service_project_reservations(project_id, purpose, holder_id)
            VALUES (?, ?, ?)
            """,
            (project_id, purpose, holder_id),
        )
        return Reservation(project_id, purpose, holder_id)

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
