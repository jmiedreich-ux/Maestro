from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from maestro.foundation import Database, StorageSettings
from maestro.service.activities import (
    ActivityAction,
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
from maestro.service.projections import (
    MAX_PAGE_SIZE,
    ProjectionNotFound,
    ProjectionReader,
)
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
                        "informational",
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
        self.assertEqual(1, data["projects"][0]["attention_count"])
        self.assertEqual(
            {"question"}, {item["type"] for item in data["attention"]}
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
                [
                    ("service_activities", 1, "service-activity-records-v1"),
                    ("service_activities", 2, "service-activity-actions-v2"),
                ],
                connection.execute(
                    """
                    SELECT domain, version, identity FROM domain_migrations
                    WHERE domain = 'service_activities'
                    ORDER BY version
                    """
                ).fetchall(),
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
        activity = self.reader.activity("activity-one").data
        self.assertEqual("working", activity["state"])
        self.assertEqual(2, activity["version"])
        self.assertEqual(3, len(self.reader.conversation("project-one").data))

        with self.assertRaises(RequestRejection) as stale_command:
            stale = self.envelope("project-one", "activity-replacement")
            stale["request_id"] = "request-project-one-stale"
            stale["expected_version"] = 0
            self.service.submit(AUTHORIZATION, stale)
        self.assertEqual("version_conflict", stale_command.exception.code)

    def test_attention_excludes_findings_and_exposes_paused_recovery_action(self) -> None:
        self.service.submit(
            AUTHORIZATION, self.envelope("project-one", "activity-one")
        )
        initial = self.reader.workspace().as_dict()["data"]
        self.assertEqual(["question"], [item["type"] for item in initial["attention"]])

        with self.database.transaction() as transaction:
            self.records.update_activity(
                transaction,
                ActivityRecord(
                    "activity-one",
                    "project-one",
                    "registration",
                    "Register Project One",
                    "paused",
                    2,
                    "Publication failed",
                    available_actions=(
                        ActivityAction(
                            "retry-activity", "Retry activity", "recovery"
                        ),
                    ),
                ),
                expected_record_version=1,
            )

        snapshot = self.reader.workspace().as_dict()["data"]
        self.assertEqual(
            {"question", "recovery"},
            {item["type"] for item in snapshot["attention"]},
        )
        self.assertNotIn("finding", {item["type"] for item in snapshot["attention"]})
        detail = self.reader.activity("activity-one").data
        self.assertEqual("paused", detail["state"])
        self.assertEqual(
            {
                "action_id": "retry-activity",
                "project_id": "project-one",
                "activity_id": "activity-one",
                "kind": "recovery",
                "label": "Retry activity",
            },
            detail["available_actions"][0],
        )

    def test_workspace_and_activity_detail_are_bounded_with_continuations(self) -> None:
        self.service.submit(
            AUTHORIZATION, self.envelope("project-one", "activity-one")
        )
        excess = MAX_PAGE_SIZE + 5
        with self.database.transaction() as transaction:
            for number in range(MAX_PAGE_SIZE + 1):
                self.records.create_project(
                    transaction,
                    ProjectRecord(
                        f"project-bulk-{number:03d}",
                        f"Bulk project {number:03d}",
                        "registered",
                        1,
                    ),
                )
            self.records.create_project(
                transaction,
                ProjectRecord("project-working", "Z Working", "registered", 1),
            )
            self.records.create_activity(
                transaction,
                ActivityRecord(
                    "activity-working",
                    "project-working",
                    "execution",
                    "Working activity",
                    "working",
                    1,
                ),
            )
            for number in range(excess):
                self.records.create_question(
                    transaction,
                    QuestionRecord(
                        f"question-bulk-{number:03d}",
                        "project-one",
                        "activity-one",
                        f"Question {number:03d}",
                        "Provide an answer",
                        "registration-architect",
                        "awaiting_answer",
                        1,
                    ),
                )
                self.records.create_finding(
                    transaction,
                    FindingRecord(
                        f"finding-bulk-{number:03d}",
                        "project-one",
                        "activity-one",
                        f"Finding {number:03d}",
                        "Informational evidence",
                        "informational",
                        1,
                    ),
                )
            self.records.update_activity(
                transaction,
                ActivityRecord(
                    "activity-one",
                    "project-one",
                    "registration",
                    "Register Project One",
                    "paused",
                    2,
                    "Recovery required",
                    available_actions=tuple(
                        ActivityAction(
                            f"retry-{number:03d}",
                            f"Retry step {number:03d}",
                            "recovery",
                        )
                        for number in range(excess)
                    ),
                ),
                expected_record_version=1,
            )

        workspace = self.reader.workspace()
        self.assertEqual(MAX_PAGE_SIZE, len(workspace.projects))
        self.assertEqual(MAX_PAGE_SIZE, len(workspace.attention))
        self.assertEqual("project-one", workspace.projects[0]["project_id"])
        self.assertIsNotNone(workspace.project_next_cursor)
        self.assertIsNotNone(workspace.attention_next_cursor)
        self.assertEqual(
            {"projects", "attention"}, set(workspace.as_dict()["data"])
        )
        remaining_projects = self.reader.projects(
            before=workspace.project_next_cursor, limit=MAX_PAGE_SIZE
        )
        self.assertEqual(3, len(remaining_projects.data))
        project_ids = [
            item["project_id"]
            for item in workspace.projects + remaining_projects.data
        ]
        self.assertEqual(len(project_ids), len(set(project_ids)))
        self.assertEqual(
            ["project-one"]
            + ["project-working"]
            + [f"project-bulk-{number:03d}" for number in range(MAX_PAGE_SIZE + 1)],
            project_ids,
        )
        next_attention = self.reader.attention(
            before=workspace.attention_next_cursor, limit=MAX_PAGE_SIZE
        )
        final_attention = self.reader.attention(
            before=next_attention.next_cursor, limit=MAX_PAGE_SIZE
        )
        attention_ids = {
            item["cursor"]
            for item in workspace.attention
            + next_attention.data
            + final_attention.data
        }
        self.assertEqual((excess + 1) + excess, len(attention_ids))

        detail = self.reader.activity("activity-one").data
        self.assertEqual(MAX_PAGE_SIZE, len(detail["questions"]))
        self.assertEqual(MAX_PAGE_SIZE, len(detail["findings"]))
        self.assertEqual(MAX_PAGE_SIZE, len(detail["available_actions"]))
        self.assertIsNotNone(detail["question_next_cursor"])
        self.assertIsNotNone(detail["finding_next_cursor"])
        self.assertIsNotNone(detail["action_next_cursor"])

        older_questions = self.reader.questions(
            "project-one",
            "activity-one",
            before=detail["question_next_cursor"],
        )
        older_findings = self.reader.findings(
            "project-one",
            "activity-one",
            before=detail["finding_next_cursor"],
        )
        older_actions = self.reader.actions(
            "project-one",
            "activity-one",
            before=detail["action_next_cursor"],
        )
        self.assertGreater(len(older_questions.data), 0)
        self.assertGreater(len(older_findings.data), 0)
        self.assertGreater(len(older_actions.data), 0)
        self.assertEqual(
            excess + 1,
            len(detail["questions"]) + len(older_questions.data),
        )
        self.assertEqual(
            excess + 1,
            len(detail["findings"]) + len(older_findings.data),
        )
        self.assertEqual(
            excess,
            len(detail["available_actions"]) + len(older_actions.data),
        )


if __name__ == "__main__":
    unittest.main()
