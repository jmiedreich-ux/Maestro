"""Cursor-consistent read projections for the connected workspace."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Iterable, Iterator

from maestro.foundation import ContractError, Database, canonical_identifier


DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 100
_ENDED_ACTIVITY_STATES = frozenset({"cancelled", "completed", "failed"})
_CLOSED_ATTENTION_STATES = frozenset(
    {"answered", "cancelled", "closed", "dismissed", "resolved"}
)


class ProjectionError(ValueError):
    """Base typed read rejection; an error is never represented as an empty list."""

    def __init__(self, code: str, message: str, **fields: object) -> None:
        super().__init__(message)
        self.code = code
        self.fields = dict(fields)


class ProjectionNotFound(ProjectionError):
    """The requested projection context does not exist."""


@dataclass(frozen=True)
class ProjectionPage:
    data: tuple[dict[str, object], ...]
    event_cursor: int
    next_cursor: int | str | None

    def as_dict(self) -> dict[str, object]:
        return {
            "data": [dict(item) for item in self.data],
            "event_cursor": self.event_cursor,
            "next_cursor": self.next_cursor,
        }


@dataclass(frozen=True)
class ProjectionResult:
    data: dict[str, object]
    event_cursor: int

    def as_dict(self) -> dict[str, object]:
        return {"data": dict(self.data), "event_cursor": self.event_cursor}


@dataclass(frozen=True)
class WorkspaceSnapshot:
    projects: tuple[dict[str, object], ...]
    activities: tuple[dict[str, object], ...]
    questions: tuple[dict[str, object], ...]
    findings: tuple[dict[str, object], ...]
    conversation: tuple[dict[str, object], ...]
    attention: tuple[dict[str, object], ...]
    event_cursor: int

    def as_dict(self) -> dict[str, object]:
        return {
            "data": {
                "projects": [dict(item) for item in self.projects],
                "activities": [dict(item) for item in self.activities],
                "questions": [dict(item) for item in self.questions],
                "findings": [dict(item) for item in self.findings],
                "conversation": [dict(item) for item in self.conversation],
                "attention": [dict(item) for item in self.attention],
            },
            "event_cursor": self.event_cursor,
        }


class ProjectionReader:
    """Read one SQLite snapshot and its matching committed-event cursor."""

    def __init__(self, database: Database) -> None:
        if not isinstance(database, Database):
            raise TypeError("projection reader requires the service Database")
        self.database = database

    def workspace(self) -> WorkspaceSnapshot:
        with self.database.read_connection() as connection:
            connection.execute("BEGIN")
            event_cursor = _event_cursor(connection)
            activity_rows = connection.execute(
                """
                SELECT rowid, activity_id, project_id, kind, subject, state,
                       waiting_reason, started_at, ended_at, version
                FROM service_activities
                ORDER BY project_id, rowid
                """
            ).fetchall()
            activities = tuple(_activity(row) for row in activity_rows)
            question_rows = connection.execute(
                """
                SELECT question_id, project_id, activity_id, subject, prompt,
                       requester, status, version
                FROM service_questions
                ORDER BY question_id
                """
            ).fetchall()
            questions = tuple(_question(row) for row in question_rows)
            finding_rows = connection.execute(
                """
                SELECT finding_id, project_id, activity_id, subject, detail,
                       status, version
                FROM service_findings
                ORDER BY finding_id
                """
            ).fetchall()
            findings = tuple(_finding(row) for row in finding_rows)
            conversation_rows = connection.execute(
                """
                SELECT message_id, project_id, activity_id, source, kind,
                       occurred_at, sequence
                FROM service_conversation
                ORDER BY sequence
                """
            ).fetchall()
            conversation = tuple(_conversation_reference(row) for row in conversation_rows)
            attention = tuple(
                list(_question_attention(question_rows))
                + list(_finding_attention(finding_rows))
            )
            attention_count: dict[str, int] = {}
            for item in attention:
                project_id = str(item["project_id"])
                attention_count[project_id] = attention_count.get(project_id, 0) + 1

            by_project: dict[str, list[sqlite3.Row | tuple[object, ...]]] = {}
            for row in activity_rows:
                by_project.setdefault(str(row[2]), []).append(row)
            project_rows = connection.execute(
                """
                SELECT project_id, name, registration_status, version
                FROM service_projects
                ORDER BY name COLLATE NOCASE, project_id
                """
            ).fetchall()
            projects = tuple(
                _project_summary(row, by_project.get(str(row[0]), ()), attention_count)
                for row in project_rows
            )
            projects = tuple(sorted(projects, key=_project_order))

        return WorkspaceSnapshot(
            projects=projects,
            activities=activities,
            questions=questions,
            findings=findings,
            conversation=conversation,
            attention=attention,
            event_cursor=event_cursor,
        )

    def activities(
        self,
        project_id: str,
        *,
        before: int | None = None,
        limit: int = DEFAULT_PAGE_SIZE,
    ) -> ProjectionPage:
        project_id = _identifier(project_id, "project_id")
        limit = _page_size(limit)
        if before is not None and (
            isinstance(before, bool) or not isinstance(before, int) or before < 1
        ):
            raise ProjectionError(
                "invalid_cursor", "before cursor must be a positive integer"
            )
        with self.database.read_connection() as connection:
            connection.execute("BEGIN")
            event_cursor = _event_cursor(connection)
            _require_project(connection, project_id)
            boundary = "" if before is None else "AND rowid < ?"
            parameters: tuple[object, ...] = (project_id,)
            if before is not None:
                parameters += (before,)
            rows = connection.execute(
                f"""
                SELECT rowid, activity_id, project_id, kind, subject, state,
                       waiting_reason, started_at, ended_at, version
                FROM service_activities
                WHERE project_id = ? {boundary}
                ORDER BY rowid DESC LIMIT ?
                """,
                parameters + (limit + 1,),
            ).fetchall()
            has_older = len(rows) > limit
            selected = rows[:limit]
            items = tuple(_activity(row) for row in selected)
            next_cursor = int(selected[-1][0]) if has_older and selected else None
        return ProjectionPage(items, event_cursor, next_cursor)

    def activity(self, activity_id: str) -> ProjectionResult:
        activity_id = _identifier(activity_id, "activity_id")
        with self.database.read_connection() as connection:
            connection.execute("BEGIN")
            event_cursor = _event_cursor(connection)
            row = connection.execute(
                """
                SELECT rowid, activity_id, project_id, kind, subject, state,
                       waiting_reason, started_at, ended_at, version
                FROM service_activities WHERE activity_id = ?
                """,
                (activity_id,),
            ).fetchone()
            if row is None:
                raise ProjectionNotFound(
                    "activity_not_found",
                    "activity projection was not found",
                    activity_id=activity_id,
                )
            questions = connection.execute(
                """
                SELECT question_id, project_id, activity_id, subject, prompt,
                       requester, status, version
                FROM service_questions WHERE activity_id = ? ORDER BY question_id
                """,
                (activity_id,),
            ).fetchall()
            findings = connection.execute(
                """
                SELECT finding_id, project_id, activity_id, subject, detail,
                       status, version
                FROM service_findings WHERE activity_id = ? ORDER BY finding_id
                """,
                (activity_id,),
            ).fetchall()
            data = _activity(row)
            data["questions"] = [_question(question) for question in questions]
            data["findings"] = [_finding(finding) for finding in findings]
        return ProjectionResult(data, event_cursor)

    def conversation(
        self,
        project_id: str,
        *,
        before: int | None = None,
        limit: int = DEFAULT_PAGE_SIZE,
    ) -> ProjectionPage:
        project_id = _identifier(project_id, "project_id")
        limit = _page_size(limit)
        if before is not None and (
            isinstance(before, bool) or not isinstance(before, int) or before < 1
        ):
            raise ProjectionError(
                "invalid_cursor", "before cursor must be a positive integer"
            )
        with self.database.read_connection() as connection:
            connection.execute("BEGIN")
            event_cursor = _event_cursor(connection)
            _require_project(connection, project_id)
            if before is None:
                rows = connection.execute(
                    """
                    SELECT sequence, message_id, project_id, activity_id, source,
                           kind, text, occurred_at
                    FROM service_conversation
                    WHERE project_id = ?
                    ORDER BY sequence DESC LIMIT ?
                    """,
                    (project_id, limit + 1),
                ).fetchall()
            else:
                rows = connection.execute(
                    """
                    SELECT sequence, message_id, project_id, activity_id, source,
                           kind, text, occurred_at
                    FROM service_conversation
                    WHERE project_id = ? AND sequence < ?
                    ORDER BY sequence DESC LIMIT ?
                    """,
                    (project_id, before, limit + 1),
                ).fetchall()
            has_older = len(rows) > limit
            selected = rows[:limit]
            items = tuple(_conversation(row) for row in reversed(selected))
            next_cursor = int(selected[-1][0]) if has_older and selected else None
        return ProjectionPage(items, event_cursor, next_cursor)

    def findings(
        self,
        project_id: str,
        activity_id: str,
        *,
        before: str | None = None,
        limit: int = DEFAULT_PAGE_SIZE,
    ) -> ProjectionPage:
        project_id = _identifier(project_id, "project_id")
        activity_id = _identifier(activity_id, "activity_id")
        if before is not None:
            before = _identifier(before, "before")
        limit = _page_size(limit)
        with self.database.read_connection() as connection:
            connection.execute("BEGIN")
            event_cursor = _event_cursor(connection)
            _require_activity(connection, project_id, activity_id)
            boundary = "" if before is None else "AND finding_id < ?"
            parameters: tuple[object, ...] = (project_id, activity_id)
            if before is not None:
                parameters += (before,)
            rows = connection.execute(
                f"""
                SELECT finding_id, project_id, activity_id, subject, detail,
                       status, version
                FROM service_findings
                WHERE project_id = ? AND activity_id = ? {boundary}
                ORDER BY finding_id DESC LIMIT ?
                """,
                parameters + (limit + 1,),
            ).fetchall()
            has_older = len(rows) > limit
            selected = rows[:limit]
            items = tuple(_finding(row) for row in selected)
            next_cursor = str(selected[-1][0]) if has_older and selected else None
        return ProjectionPage(items, event_cursor, next_cursor)


def _event_cursor(connection: sqlite3.Connection) -> int:
    row = connection.execute(
        "SELECT COALESCE(MAX(sequence), 0) FROM outbox_events"
    ).fetchone()
    return int(row[0])


def _require_project(connection: sqlite3.Connection, project_id: str) -> None:
    if connection.execute(
        "SELECT 1 FROM service_projects WHERE project_id = ?", (project_id,)
    ).fetchone() is None:
        raise ProjectionNotFound(
            "project_not_found", "project projection was not found", project_id=project_id
        )


def _require_activity(
    connection: sqlite3.Connection, project_id: str, activity_id: str
) -> None:
    row = connection.execute(
        "SELECT project_id FROM service_activities WHERE activity_id = ?",
        (activity_id,),
    ).fetchone()
    if row is None:
        raise ProjectionNotFound(
            "activity_not_found",
            "activity projection was not found",
            activity_id=activity_id,
        )
    if str(row[0]) != project_id:
        raise ProjectionNotFound(
            "wrong_project_reference",
            "activity belongs to another project",
            project_id=project_id,
            activity_id=activity_id,
        )


def _project_summary(
    row: tuple[object, ...],
    activity_rows: Iterable[tuple[object, ...]],
    attention_count: dict[str, int],
) -> dict[str, object]:
    records = list(activity_rows)
    current = [record for record in records if str(record[5]) not in _ENDED_ACTIVITY_STATES]
    selected = current[-1] if current else (records[-1] if records else None)
    project_id = str(row[0])
    if len(current) > 1:
        activity_id: str | None = None
        activity_state = "multiple"
    else:
        activity_id = None if selected is None else str(selected[1])
        activity_state = "idle" if not current else str(selected[5])
    return {
        "project_id": project_id,
        "name": str(row[1]),
        "registration_status": str(row[2]),
        "version": int(row[3]),
        "activity_id": activity_id,
        "activity_state": activity_state,
        "current_activity_count": len(current),
        "attention_count": attention_count.get(project_id, 0),
    }


def _project_order(project: dict[str, object]) -> tuple[object, ...]:
    if int(project["attention_count"]) > 0:
        group = 0
    elif int(project["current_activity_count"]) > 0:
        group = 1
    else:
        group = 2
    return (group, str(project["name"]).casefold(), str(project["project_id"]))


def _activity(row: tuple[object, ...]) -> dict[str, object]:
    return {
        "activity_id": str(row[1]),
        "project_id": str(row[2]),
        "kind": str(row[3]),
        "subject": str(row[4]),
        "state": str(row[5]),
        "waiting_reason": None if row[6] is None else str(row[6]),
        "started_at": None if row[7] is None else str(row[7]),
        "ended_at": None if row[8] is None else str(row[8]),
        "version": int(row[9]),
    }


def _question(row: tuple[object, ...]) -> dict[str, object]:
    return {
        "question_id": str(row[0]),
        "project_id": str(row[1]),
        "activity_id": str(row[2]),
        "subject": str(row[3]),
        "prompt": str(row[4]),
        "requester": str(row[5]),
        "status": str(row[6]),
        "version": int(row[7]),
    }


def _finding(row: tuple[object, ...]) -> dict[str, object]:
    return {
        "finding_id": str(row[0]),
        "project_id": str(row[1]),
        "activity_id": str(row[2]),
        "subject": str(row[3]),
        "detail": str(row[4]),
        "status": str(row[5]),
        "version": int(row[6]),
    }


def _conversation(row: tuple[object, ...]) -> dict[str, object]:
    return {
        "sequence": int(row[0]),
        "message_id": str(row[1]),
        "project_id": str(row[2]),
        "activity_id": None if row[3] is None else str(row[3]),
        "source": str(row[4]),
        "kind": str(row[5]),
        "text": str(row[6]),
        "occurred_at": str(row[7]),
    }


def _conversation_reference(row: tuple[object, ...]) -> dict[str, object]:
    return {
        "message_id": str(row[0]),
        "project_id": str(row[1]),
        "activity_id": None if row[2] is None else str(row[2]),
        "source": str(row[3]),
        "kind": str(row[4]),
        "occurred_at": str(row[5]),
        "sequence": int(row[6]),
    }


def _question_attention(rows: list[tuple[object, ...]]) -> Iterator[dict[str, object]]:
    for row in rows:
        if str(row[6]) not in _CLOSED_ATTENTION_STATES:
            yield {
                "type": "question",
                "question_id": str(row[0]),
                "project_id": str(row[1]),
                "activity_id": str(row[2]),
                "subject": str(row[3]),
                "requester": str(row[5]),
            }


def _finding_attention(rows: list[tuple[object, ...]]) -> Iterator[dict[str, object]]:
    for row in rows:
        if str(row[5]) not in _CLOSED_ATTENTION_STATES:
            yield {
                "type": "finding",
                "finding_id": str(row[0]),
                "project_id": str(row[1]),
                "activity_id": str(row[2]),
                "subject": str(row[3]),
            }


def _identifier(value: str, field: str) -> str:
    try:
        return canonical_identifier(value, field)
    except (ContractError, TypeError) as error:
        raise ProjectionError("invalid_context", str(error), field=field) from error


def _page_size(value: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= MAX_PAGE_SIZE:
        raise ProjectionError(
            "invalid_page_size",
            f"limit must be an integer from 1 through {MAX_PAGE_SIZE}",
            limit=value,
        )
    return value
