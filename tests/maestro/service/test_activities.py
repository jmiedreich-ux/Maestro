from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from maestro.foundation import Database, StorageSettings
from maestro.service.activities import (
    ActivityRecord,
    ActivityRepository,
    ConversationRecord,
    FindingRecord,
    ProjectRecord,
    QuestionRecord,
    RecordReferenceError,
    RecordVersionConflict,
)
from maestro.service.authentication import (
    OwnerAuthenticationSettings,
    OwnerAuthenticator,
    token_digest,
)
from maestro.service.projections import ProjectionNotFound, ProjectionReader
from maestro.service.registry import (
    OperationHandler,
    OperationRegistry,
    OperationResult,
    PreparedOperation,
)
from maestro.service.requests import RequestRejection, RequestService


OWNER_TOKEN = "a" * 64
AUTHORIZATION = f"Bearer {OWNER_TOKEN}"


class ProjectActivityRecordsTest(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.database = Database(
            StorageSettings(path=Path(temporary.name) / "maestro.sqlite3")
        )
        self.records = ActivityRepository(self.database)
        self.reader = ProjectionReader(self.database)
        authenticator = OwnerAuthenticator(
            OwnerAuthenticationSettings(
                owner_id="owner-local", token_sha256=token_digest(OWNER_TOKEN)
            )
        )
        registry = OperationRegistry(
            (OperationHandler("registration.start", self._registration_start),)
        )
        self.service = RequestService(self.database, authenticator, registry)

    def _registration_start(self, request) -> PreparedOperation:
        if request.project_id is not None or request.activity_id is not None:
            raise ValueError("registration.start creates its project context")
        required = {"project_id", "activity_id", "name"}
        if set(request.payload) != required:
            raise ValueError("registration.start payload is invalid")
        project_id = str(request.payload["project_id"])
        activity_id = str(request.payload["activity_id"])
        name = str(request.payload["name"])

        def apply(transaction, next_version: int) -> OperationResult:
            self.records.create_records(
                transaction,
                project=ProjectRecord(project_id, name, "registering", next_version),
                activity=ActivityRecord(
                    activity_id,
                    project_id,
                    "registration",
                    f"Register {name}",
                    "waiting",
                    next_version,
                    "Owner answer required",
                ),
                questions=(
                    QuestionRecord(
                        f"question-{project_id}",
                        project_id,
                        activity_id,
                        "Choose source",
                        "Which source reference should be used?",
                        "registration-architect",
                        "awaiting_answer",
                        1,
                    ),
                ),
                findings=(
                    FindingRecord(
                        f"finding-{project_id}",
                        project_id,
                        activity_id,
                        "Missing source choice",
                        "The source must be selected before assessment.",
                        "blocking",
                        1,
                    ),
                ),
                conversation=tuple(
                    ConversationRecord(
                        f"message-{project_id}-{number}",
                        project_id,
                        "service",
                        "progress",
                        text,
                        f"2026-09-17T12:00:0{number}.000000Z",
                        activity_id,
                    )
                    for number, text in enumerate(
                        ("Registration accepted", "Assessment started", "Answer needed"),
                        start=1,
                    )
                ),
            )
            return OperationResult(
                data={
                    "project_id": project_id,
                    "activity_id": activity_id,
                    "question_id": f"question-{project_id}",
                    "finding_id": f"finding-{project_id}",
                    "conversation_id": f"message-{project_id}-1",
                },
                status="accepted",
                project_id=project_id,
                activity_id=activity_id,
            )

        return PreparedOperation(
            entity_id=project_id,
            event_type="project.created",
            event_data={"project_id": project_id, "activity_id": activity_id},
            apply=apply,
        )

    @staticmethod
    def envelope(project_id: str, activity_id: str) -> dict[str, object]:
        return {
            "request_id": f"request-{project_id}",
            "operation": "registration.start",
            "project_id": None,
            "activity_id": None,
            "question_id": None,
            "expected_version": None,
            "payload": {
                "project_id": project_id,
                "activity_id": activity_id,
                "name": project_id.replace("-", " ").title(),
            },
        }

    def test_service_command_creates_linked_records_and_cursor_consistent_snapshot(self) -> None:
        receipt = self.service.submit(
            AUTHORIZATION, self.envelope("project-one", "activity-one")
        )
        snapshot = self.reader.workspace().as_dict()

        self.assertEqual("accepted", receipt.status)
        self.assertEqual("project-one", receipt.project_id)
        self.assertEqual("activity-one", receipt.activity_id)
        self.assertEqual(
            {
                "project_id": "project-one",
                "activity_id": "activity-one",
                "question_id": "question-project-one",
                "finding_id": "finding-project-one",
                "conversation_id": "message-project-one-1",
            },
            receipt.result,
        )
        self.assertEqual(1, snapshot["event_cursor"])
        data = snapshot["data"]
        self.assertEqual("project-one", data["projects"][0]["project_id"])
        self.assertEqual("waiting", data["projects"][0]["activity_state"])
        self.assertEqual(2, data["projects"][0]["attention_count"])
        self.assertEqual("activity-one", data["activities"][0]["activity_id"])
        self.assertEqual(
            "question-project-one", data["questions"][0]["question_id"]
        )
        self.assertEqual("finding-project-one", data["findings"][0]["finding_id"])
        self.assertEqual(3, len(data["conversation"]))
        self.assertEqual(
            {"finding", "question"}, {item["type"] for item in data["attention"]}
        )

        latest = self.reader.conversation("project-one", limit=2)
        earlier = self.reader.conversation(
            "project-one", before=latest.next_cursor, limit=2
        )
        self.assertEqual(1, latest.event_cursor)
        self.assertEqual(
            ["message-project-one-2", "message-project-one-3"],
            [item["message_id"] for item in latest.data],
        )
        self.assertEqual(
            ["message-project-one-1"],
            [item["message_id"] for item in earlier.data],
        )
        activities = self.reader.activities("project-one")
        detail = self.reader.activity("activity-one")
        self.assertEqual(1, activities.event_cursor)
        self.assertEqual("activity-one", activities.data[0]["activity_id"])
        self.assertEqual("activity-one", detail.data["activity_id"])
        self.assertEqual(
            "question-project-one", detail.data["questions"][0]["question_id"]
        )
        self.assertEqual(
            "finding-project-one", detail.data["findings"][0]["finding_id"]
        )
        with self.database.read_connection() as connection:
            self.assertEqual(
                ("service_activities", 1, "service-activity-records-v1"),
                connection.execute(
                    """
                    SELECT domain, version, identity FROM domain_migrations
                    WHERE domain = 'service_activities'
                    """
                ).fetchone(),
            )
            self.assertEqual(
                (1, 1, 1),
                connection.execute(
                    """
                    SELECT
                      (SELECT COUNT(*) FROM request_receipts),
                      (SELECT COUNT(*) FROM service_projects),
                      (SELECT COUNT(*) FROM outbox_events)
                    """
                ).fetchone(),
            )

    def test_cross_project_reference_rolls_back_without_corrupting_either_activity(self) -> None:
        self.service.submit(
            AUTHORIZATION, self.envelope("project-one", "activity-one")
        )
        self.service.submit(
            AUTHORIZATION, self.envelope("project-two", "activity-two")
        )

        with self.assertRaises(RecordReferenceError) as raised:
            with self.database.transaction() as transaction:
                self.records.append_conversation(
                    transaction,
                    ConversationRecord(
                        "message-wrong-context",
                        "project-two",
                        "service",
                        "progress",
                        "Must not be saved",
                        "2026-09-17T12:01:00.000000Z",
                        "activity-one",
                    ),
                )

        self.assertEqual("wrong_project_reference", raised.exception.code)
        one = self.reader.conversation("project-one")
        two = self.reader.conversation("project-two")
        self.assertEqual(3, len(one.data))
        self.assertEqual(3, len(two.data))
        self.assertNotIn(
            "message-wrong-context",
            [item["message_id"] for item in one.data + two.data],
        )
        with self.assertRaises(ProjectionNotFound) as missing:
            self.reader.conversation("project-missing")
        self.assertEqual("project_not_found", missing.exception.code)

    def test_stale_update_is_typed_and_preserves_saved_history(self) -> None:
        self.service.submit(
            AUTHORIZATION, self.envelope("project-one", "activity-one")
        )
        updated = ActivityRecord(
            "activity-one",
            "project-one",
            "registration",
            "Register Project One",
            "working",
            2,
        )
        with self.database.transaction() as transaction:
            self.records.update_activity(
                transaction, updated, expected_record_version=1
            )

        with self.assertRaises(RecordVersionConflict) as raised:
            with self.database.transaction() as transaction:
                self.records.update_activity(
                    transaction,
                    ActivityRecord(
                        "activity-one",
                        "project-one",
                        "registration",
                        "Stale replacement",
                        "failed",
                        2,
                    ),
                    expected_record_version=1,
                )

        self.assertEqual("record_version_conflict", raised.exception.code)
        snapshot = self.reader.workspace().as_dict()
        activity = snapshot["data"]["activities"][0]
        self.assertEqual("working", activity["state"])
        self.assertEqual(2, activity["version"])
        self.assertEqual(3, len(snapshot["data"]["conversation"]))

        with self.assertRaises(RequestRejection) as stale_command:
            stale = self.envelope("project-one", "activity-replacement")
            stale["request_id"] = "request-project-one-stale"
            stale["expected_version"] = 0
            self.service.submit(AUTHORIZATION, stale)
        self.assertEqual("version_conflict", stale_command.exception.code)


if __name__ == "__main__":
    unittest.main()
