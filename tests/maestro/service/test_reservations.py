from __future__ import annotations

import tempfile
import threading
import unittest
from pathlib import Path

from maestro.foundation import Database, StorageSettings
from maestro.service.activities import ActivityRecord, ActivityRepository, ProjectRecord
from maestro.service.reservations import ProjectReservations, ReservationError, refuse_other_starts


class ProjectReservationTest(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.path = Path(temporary.name) / "maestro.sqlite3"
        self.database = Database(StorageSettings(path=self.path))
        self.records = ActivityRepository(self.database)
        self.reservations = ProjectReservations(self.database)
        with self.database.transaction() as transaction:
            for project in ("one", "two"):
                self.records.create_project(
                    transaction, ProjectRecord(project, project, "registered", 1)
                )

    def _activity(self, project: str, state: str) -> None:
        with self.database.transaction() as transaction:
            self.records.create_activity(
                transaction,
                ActivityRecord(
                    f"activity-{project}-{state}", project, "generic", "work", state, 1
                ),
            )

    def _reserve(self, project: str, purpose: str, holder: str):
        with self.database.transaction() as transaction:
            return self.reservations.reserve(transaction, project, purpose, holder)

    def test_simultaneous_starts_and_re_registration_admit_exactly_one(self) -> None:
        outcomes: list[str] = []
        gate = threading.Barrier(12)

        def compete(index: int) -> None:
            # Each thread opens its own connection to the same database file.
            database = Database(StorageSettings(path=self.path))
            reservations = ProjectReservations(database)
            purpose = "re_registration" if index % 3 == 0 else "start"
            gate.wait()
            try:
                with database.transaction() as transaction:
                    reservations.reserve(transaction, "one", purpose, f"holder-{index}")
                outcomes.append("won")
            except ReservationError as error:
                outcomes.append(error.code)

        threads = [threading.Thread(target=compete, args=(i,)) for i in range(12)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        self.assertEqual(1, outcomes.count("won"))
        self.assertEqual(11, outcomes.count("project_reserved"))
        self.assertIsNotNone(self.reservations.held("one"))
        # Other projects stay available while one is held.
        self.assertEqual("start", self._reserve("two", "start", "other").purpose)

    def test_unknown_or_running_activity_is_not_idle(self) -> None:
        self._activity("one", "unknown")
        with self.assertRaises(ReservationError) as raised:
            self._reserve("one", "start", "holder")
        self.assertEqual("project_not_idle", raised.exception.code)
        self.assertIsNone(self.reservations.held("one"))

    def test_ended_activities_allow_reservation_and_release_frees_it(self) -> None:
        self._activity("one", "completed")
        self._activity("one", "failed")
        self._reserve("one", "re_registration", "holder")
        with self.assertRaises(ReservationError):
            self._reserve("one", "start", "rival")
        with self.database.transaction() as transaction:
            self.assertFalse(self.reservations.release(transaction, "one", "rival"))
            self.assertTrue(self.reservations.release(transaction, "one", "holder"))
        self.assertEqual("start", self._reserve("one", "start", "rival").purpose)

    def test_repeat_by_same_holder_is_idempotent_and_survives_reopen(self) -> None:
        first = self._reserve("one", "start", "holder")
        self.assertEqual(first, self._reserve("one", "start", "holder"))
        reopened = ProjectReservations(Database(StorageSettings(path=self.path)))
        self.assertEqual(first, reopened.held("one"))

    def test_missing_project_and_invalid_purpose_are_rejected(self) -> None:
        with self.assertRaises(ReservationError) as raised:
            self._reserve("missing", "start", "holder")
        self.assertEqual("project_not_found", raised.exception.code)
        with self.assertRaises(ValueError):
            self._reserve("one", "other", "holder")

    def test_reserved_project_refuses_other_starts_but_not_the_holder(self) -> None:
        self._reserve("one", "re_registration", "holder")
        with self.database.transaction() as transaction:
            refuse_other_starts(transaction, "one", "holder")
            refuse_other_starts(transaction, "two", "anyone")
            with self.assertRaises(ReservationError) as raised:
                refuse_other_starts(transaction, "one", "someone-else")
        self.assertEqual("project_reserved", raised.exception.code)


if __name__ == "__main__":
    unittest.main()
