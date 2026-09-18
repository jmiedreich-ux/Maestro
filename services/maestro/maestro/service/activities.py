"""Durable project and activity records for service-owned process handlers.

The repository deliberately accepts the foundation ``Transaction`` instead of
opening a connection.  A request handler can therefore save its domain effect,
durable receipt, and outbox event in the one transaction owned by
``RequestService``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from maestro.foundation import (
    Database,
    DomainMigration,
    Transaction,
    canonical_identifier,
    positive_version,
)


ACTIVITY_RECORDS_MIGRATION = DomainMigration(
    domain="service_activities",
    version=1,
    identity="service-activity-records-v1",
    statements=(
        """
        CREATE TABLE service_projects(
            project_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            registration_status TEXT NOT NULL,
            version INTEGER NOT NULL CHECK(version > 0)
        )
        """,
        """
        CREATE TABLE service_activities(
            activity_id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL
                REFERENCES service_projects(project_id) ON DELETE RESTRICT,
            kind TEXT NOT NULL,
            subject TEXT NOT NULL,
            state TEXT NOT NULL,
            waiting_reason TEXT,
            started_at TEXT,
            ended_at TEXT,
            version INTEGER NOT NULL CHECK(version > 0)
        )
        """,
        """
        CREATE INDEX service_activities_project_state
            ON service_activities(project_id, state, activity_id)
        """,
        """
        CREATE TABLE service_questions(
            question_id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL
                REFERENCES service_projects(project_id) ON DELETE RESTRICT,
            activity_id TEXT NOT NULL
                REFERENCES service_activities(activity_id) ON DELETE RESTRICT,
            subject TEXT NOT NULL,
            prompt TEXT NOT NULL,
            requester TEXT NOT NULL,
            status TEXT NOT NULL,
            version INTEGER NOT NULL CHECK(version > 0)
        )
        """,
        """
        CREATE INDEX service_questions_attention
            ON service_questions(project_id, status, question_id)
        """,
        """
        CREATE TABLE service_findings(
            finding_id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL
                REFERENCES service_projects(project_id) ON DELETE RESTRICT,
            activity_id TEXT NOT NULL
                REFERENCES service_activities(activity_id) ON DELETE RESTRICT,
            subject TEXT NOT NULL,
            detail TEXT NOT NULL,
            status TEXT NOT NULL,
            version INTEGER NOT NULL CHECK(version > 0)
        )
        """,
        """
        CREATE INDEX service_findings_activity
            ON service_findings(project_id, activity_id, finding_id)
        """,
        """
        CREATE TABLE service_conversation(
            sequence INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id TEXT NOT NULL UNIQUE,
            project_id TEXT NOT NULL
                REFERENCES service_projects(project_id) ON DELETE RESTRICT,
            activity_id TEXT
                REFERENCES service_activities(activity_id) ON DELETE RESTRICT,
            source TEXT NOT NULL,
            kind TEXT NOT NULL,
            text TEXT NOT NULL,
            occurred_at TEXT NOT NULL
        )
        """,
        """
        CREATE INDEX service_conversation_project_sequence
            ON service_conversation(project_id, sequence)
        """,
    ),
)

ACTIVITY_ACTIONS_MIGRATION = DomainMigration(
    domain="service_activities",
    version=2,
    identity="service-activity-actions-v2",
    statements=(
        """
        CREATE TABLE service_activity_actions(
            sequence INTEGER PRIMARY KEY AUTOINCREMENT,
            action_id TEXT NOT NULL UNIQUE,
            activity_id TEXT NOT NULL
                REFERENCES service_activities(activity_id) ON DELETE CASCADE,
            project_id TEXT NOT NULL
                REFERENCES service_projects(project_id) ON DELETE RESTRICT,
            kind TEXT NOT NULL CHECK(kind IN ('action', 'decision', 'recovery')),
            label TEXT NOT NULL
        )
        """,
        """
        CREATE INDEX service_activity_actions_context
            ON service_activity_actions(project_id, activity_id, sequence)
        """,
    ),
)


class ActivityRecordError(ValueError):
    """A typed domain rejection that leaves the caller's transaction intact."""

    def __init__(self, code: str, message: str, **fields: object) -> None:
        super().__init__(message)
        self.code = code
        self.fields = dict(fields)


class RecordReferenceError(ActivityRecordError):
    """A referenced record is absent or belongs to a different project."""


class RecordVersionConflict(ActivityRecordError):
    """A record update was prepared against an obsolete version."""


@dataclass(frozen=True)
class ProjectRecord:
    project_id: str
    name: str
    registration_status: str
    version: int


@dataclass(frozen=True)
class ActivityRecord:
    activity_id: str
    project_id: str
    kind: str
    subject: str
    state: str
    version: int
    waiting_reason: str | None = None
    started_at: str | None = None
    ended_at: str | None = None
    available_actions: tuple[ActivityAction, ...] = ()


@dataclass(frozen=True)
class ActivityAction:
    action_id: str
    label: str
    kind: str = "action"


@dataclass(frozen=True)
class QuestionRecord:
    question_id: str
    project_id: str
    activity_id: str
    subject: str
    prompt: str
    requester: str
    status: str
    version: int


@dataclass(frozen=True)
class FindingRecord:
    finding_id: str
    project_id: str
    activity_id: str
    subject: str
    detail: str
    status: str
    version: int


@dataclass(frozen=True)
class ConversationRecord:
    message_id: str
    project_id: str
    source: str
    kind: str
    text: str
    occurred_at: str
    activity_id: str | None = None


class ActivityRepository:
    """Write project projections through a caller-owned service transaction."""

    def __init__(self, database: Database) -> None:
        if not isinstance(database, Database):
            raise TypeError("activity repository requires the service Database")
        self.database = database
        self.database.registry.register(ACTIVITY_RECORDS_MIGRATION)
        self.database.registry.register(ACTIVITY_ACTIONS_MIGRATION)
        self.database.initialize()

    def create_project(self, transaction: Transaction, record: ProjectRecord) -> None:
        _project(record)
        transaction.execute(
            """
            INSERT INTO service_projects(project_id, name, registration_status, version)
            VALUES (?, ?, ?, ?)
            """,
            (record.project_id, record.name, record.registration_status, record.version),
        )

    def update_project(
        self,
        transaction: Transaction,
        record: ProjectRecord,
        *,
        expected_record_version: int,
    ) -> None:
        _project(record)
        positive_version(expected_record_version, "expected record version")
        if record.version != expected_record_version + 1:
            raise ValueError("project version must advance exactly once")
        cursor = transaction.execute(
            """
            UPDATE service_projects
            SET name = ?, registration_status = ?, version = ?
            WHERE project_id = ? AND version = ?
            """,
            (
                record.name,
                record.registration_status,
                record.version,
                record.project_id,
                expected_record_version,
            ),
        )
        if cursor.rowcount != 1:
            self._raise_version_or_missing(
                transaction,
                "service_projects",
                "project_id",
                record.project_id,
                expected_record_version,
            )

    def create_activity(self, transaction: Transaction, record: ActivityRecord) -> None:
        _activity(record)
        self._require_project(transaction, record.project_id)
        transaction.execute(
            """
            INSERT INTO service_activities(
                activity_id, project_id, kind, subject, state, waiting_reason,
                started_at, ended_at, version
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.activity_id,
                record.project_id,
                record.kind,
                record.subject,
                record.state,
                record.waiting_reason,
                record.started_at,
                record.ended_at,
                record.version,
            ),
        )
        self._replace_actions(transaction, record)

    def update_activity(
        self,
        transaction: Transaction,
        record: ActivityRecord,
        *,
        expected_record_version: int,
    ) -> None:
        _activity(record)
        positive_version(expected_record_version, "expected record version")
        if record.version != expected_record_version + 1:
            raise ValueError("activity version must advance exactly once")
        self._require_activity(transaction, record.project_id, record.activity_id)
        cursor = transaction.execute(
            """
            UPDATE service_activities
            SET kind = ?, subject = ?, state = ?, waiting_reason = ?,
                started_at = ?, ended_at = ?, version = ?
            WHERE activity_id = ? AND project_id = ? AND version = ?
            """,
            (
                record.kind,
                record.subject,
                record.state,
                record.waiting_reason,
                record.started_at,
                record.ended_at,
                record.version,
                record.activity_id,
                record.project_id,
                expected_record_version,
            ),
        )
        if cursor.rowcount != 1:
            self._raise_version_or_missing(
                transaction,
                "service_activities",
                "activity_id",
                record.activity_id,
                expected_record_version,
            )
        self._replace_actions(transaction, record)

    def create_question(self, transaction: Transaction, record: QuestionRecord) -> None:
        _question(record)
        self._require_activity(transaction, record.project_id, record.activity_id)
        transaction.execute(
            """
            INSERT INTO service_questions(
                question_id, project_id, activity_id, subject, prompt,
                requester, status, version
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.question_id,
                record.project_id,
                record.activity_id,
                record.subject,
                record.prompt,
                record.requester,
                record.status,
                record.version,
            ),
        )

    def update_question(
        self,
        transaction: Transaction,
        record: QuestionRecord,
        *,
        expected_record_version: int,
    ) -> None:
        _question(record)
        self._update_linked_record(
            transaction,
            table="service_questions",
            identity_column="question_id",
            identity=record.question_id,
            project_id=record.project_id,
            activity_id=record.activity_id,
            expected_record_version=expected_record_version,
            next_record_version=record.version,
            statement="""
                UPDATE service_questions
                SET subject = ?, prompt = ?, requester = ?, status = ?, version = ?
                WHERE question_id = ? AND project_id = ? AND activity_id = ?
                  AND version = ?
            """,
            parameters=(record.subject, record.prompt, record.requester, record.status),
        )

    def create_finding(self, transaction: Transaction, record: FindingRecord) -> None:
        _finding(record)
        self._require_activity(transaction, record.project_id, record.activity_id)
        transaction.execute(
            """
            INSERT INTO service_findings(
                finding_id, project_id, activity_id, subject, detail, status, version
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.finding_id,
                record.project_id,
                record.activity_id,
                record.subject,
                record.detail,
                record.status,
                record.version,
            ),
        )

    def update_finding(
        self,
        transaction: Transaction,
        record: FindingRecord,
        *,
        expected_record_version: int,
    ) -> None:
        _finding(record)
        self._update_linked_record(
            transaction,
            table="service_findings",
            identity_column="finding_id",
            identity=record.finding_id,
            project_id=record.project_id,
            activity_id=record.activity_id,
            expected_record_version=expected_record_version,
            next_record_version=record.version,
            statement="""
                UPDATE service_findings
                SET subject = ?, detail = ?, status = ?, version = ?
                WHERE finding_id = ? AND project_id = ? AND activity_id = ?
                  AND version = ?
            """,
            parameters=(record.subject, record.detail, record.status),
        )

    def append_conversation(
        self, transaction: Transaction, record: ConversationRecord
    ) -> None:
        _conversation(record)
        self._require_project(transaction, record.project_id)
        if record.activity_id is not None:
            self._require_activity(
                transaction, record.project_id, record.activity_id
            )
        transaction.execute(
            """
            INSERT INTO service_conversation(
                message_id, project_id, activity_id, source, kind, text, occurred_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.message_id,
                record.project_id,
                record.activity_id,
                record.source,
                record.kind,
                record.text,
                record.occurred_at,
            ),
        )

    def create_records(
        self,
        transaction: Transaction,
        *,
        project: ProjectRecord,
        activity: ActivityRecord,
        questions: Iterable[QuestionRecord] = (),
        findings: Iterable[FindingRecord] = (),
        conversation: Iterable[ConversationRecord] = (),
    ) -> None:
        """Create an intake projection as one caller-owned command effect."""
        if activity.project_id != project.project_id:
            raise RecordReferenceError(
                "wrong_project_reference",
                "activity does not belong to the command project",
                project_id=project.project_id,
                activity_id=activity.activity_id,
            )
        self.create_project(transaction, project)
        self.create_activity(transaction, activity)
        for question in questions:
            self.create_question(transaction, question)
        for finding in findings:
            self.create_finding(transaction, finding)
        for message in conversation:
            self.append_conversation(transaction, message)

    @staticmethod
    def _require_project(transaction: Transaction, project_id: str) -> None:
        row = transaction.execute(
            "SELECT 1 FROM service_projects WHERE project_id = ?", (project_id,)
        ).fetchone()
        if row is None:
            raise RecordReferenceError(
                "project_not_found",
                "project record was not found",
                project_id=project_id,
            )

    @staticmethod
    def _require_activity(
        transaction: Transaction, project_id: str, activity_id: str
    ) -> None:
        row = transaction.execute(
            "SELECT project_id FROM service_activities WHERE activity_id = ?",
            (activity_id,),
        ).fetchone()
        if row is None:
            raise RecordReferenceError(
                "activity_not_found",
                "activity record was not found",
                activity_id=activity_id,
            )
        if str(row[0]) != project_id:
            raise RecordReferenceError(
                "wrong_project_reference",
                "activity belongs to another project",
                project_id=project_id,
                activity_id=activity_id,
                actual_project_id=str(row[0]),
            )

    def _update_linked_record(
        self,
        transaction: Transaction,
        *,
        table: str,
        identity_column: str,
        identity: str,
        project_id: str,
        activity_id: str,
        expected_record_version: int,
        next_record_version: int,
        statement: str,
        parameters: tuple[object, ...],
    ) -> None:
        positive_version(expected_record_version, "expected record version")
        if next_record_version != expected_record_version + 1:
            raise ValueError("record version must advance exactly once")
        self._require_activity(transaction, project_id, activity_id)
        row = transaction.execute(
            f"SELECT project_id, activity_id, version FROM {table} "
            f"WHERE {identity_column} = ?",
            (identity,),
        ).fetchone()
        if row is None:
            raise RecordReferenceError(
                "record_not_found", "linked record was not found", record_id=identity
            )
        if (str(row[0]), str(row[1])) != (project_id, activity_id):
            raise RecordReferenceError(
                "wrong_project_reference",
                "linked record belongs to another project or activity",
                record_id=identity,
                project_id=project_id,
                activity_id=activity_id,
            )
        cursor = transaction.execute(
            statement,
            parameters
            + (
                next_record_version,
                identity,
                project_id,
                activity_id,
                expected_record_version,
            ),
        )
        if cursor.rowcount != 1:
            raise RecordVersionConflict(
                "record_version_conflict",
                "the record version is stale",
                record_id=identity,
                expected_version=expected_record_version,
                current_version=int(row[2]),
            )

    @staticmethod
    def _replace_actions(transaction: Transaction, record: ActivityRecord) -> None:
        transaction.execute(
            "DELETE FROM service_activity_actions WHERE activity_id = ?",
            (record.activity_id,),
        )
        transaction.executemany(
            """
            INSERT INTO service_activity_actions(
                action_id, activity_id, project_id, kind, label
            ) VALUES (?, ?, ?, ?, ?)
            """,
            tuple(
                (
                    action.action_id,
                    record.activity_id,
                    record.project_id,
                    action.kind,
                    action.label,
                )
                for action in record.available_actions
            ),
        )

    @staticmethod
    def _raise_version_or_missing(
        transaction: Transaction,
        table: str,
        identity_column: str,
        identity: str,
        expected_record_version: int,
    ) -> None:
        row = transaction.execute(
            f"SELECT version FROM {table} WHERE {identity_column} = ?", (identity,)
        ).fetchone()
        if row is None:
            raise RecordReferenceError(
                "record_not_found", "record was not found", record_id=identity
            )
        raise RecordVersionConflict(
            "record_version_conflict",
            "the record version is stale",
            record_id=identity,
            expected_version=expected_record_version,
            current_version=int(row[0]),
        )


def _text(value: str, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be nonempty text")
    return value


def _project(record: ProjectRecord) -> None:
    if not isinstance(record, ProjectRecord):
        raise TypeError("project record is invalid")
    canonical_identifier(record.project_id, "project_id")
    _text(record.name, "project name")
    canonical_identifier(record.registration_status, "registration status")
    positive_version(record.version, "project version")


def _activity(record: ActivityRecord) -> None:
    if not isinstance(record, ActivityRecord):
        raise TypeError("activity record is invalid")
    canonical_identifier(record.activity_id, "activity_id")
    canonical_identifier(record.project_id, "project_id")
    canonical_identifier(record.kind, "activity kind")
    _text(record.subject, "activity subject")
    canonical_identifier(record.state, "activity state")
    if record.waiting_reason is not None:
        _text(record.waiting_reason, "waiting reason")
    if record.started_at is not None:
        _text(record.started_at, "activity started_at")
    if record.ended_at is not None:
        _text(record.ended_at, "activity ended_at")
    if not isinstance(record.available_actions, tuple):
        raise ValueError("available actions must be a tuple")
    seen: set[str] = set()
    for action in record.available_actions:
        if not isinstance(action, ActivityAction):
            raise TypeError("available activity action is invalid")
        canonical_identifier(action.action_id, "action_id")
        _text(action.label, "action label")
        if action.kind not in {"action", "decision", "recovery"}:
            raise ValueError("activity action kind is invalid")
        if action.action_id in seen:
            raise ValueError("activity action identities must be unique")
        seen.add(action.action_id)
    positive_version(record.version, "activity version")


def _question(record: QuestionRecord) -> None:
    if not isinstance(record, QuestionRecord):
        raise TypeError("question record is invalid")
    canonical_identifier(record.question_id, "question_id")
    canonical_identifier(record.project_id, "project_id")
    canonical_identifier(record.activity_id, "activity_id")
    _text(record.subject, "question subject")
    _text(record.prompt, "question prompt")
    canonical_identifier(record.requester, "question requester")
    canonical_identifier(record.status, "question status")
    positive_version(record.version, "question version")


def _finding(record: FindingRecord) -> None:
    if not isinstance(record, FindingRecord):
        raise TypeError("finding record is invalid")
    canonical_identifier(record.finding_id, "finding_id")
    canonical_identifier(record.project_id, "project_id")
    canonical_identifier(record.activity_id, "activity_id")
    _text(record.subject, "finding subject")
    _text(record.detail, "finding detail")
    canonical_identifier(record.status, "finding status")
    positive_version(record.version, "finding version")


def _conversation(record: ConversationRecord) -> None:
    if not isinstance(record, ConversationRecord):
        raise TypeError("conversation record is invalid")
    canonical_identifier(record.message_id, "message_id")
    canonical_identifier(record.project_id, "project_id")
    if record.activity_id is not None:
        canonical_identifier(record.activity_id, "activity_id")
    canonical_identifier(record.source, "conversation source")
    canonical_identifier(record.kind, "conversation kind")
    _text(record.text, "conversation text")
    _text(record.occurred_at, "conversation occurred_at")
