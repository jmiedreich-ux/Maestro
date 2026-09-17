"""Cursor-consistent read projections for the connected workspace."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from maestro.foundation import ContractError, Database, canonical_identifier


DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 100


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
    attention: tuple[dict[str, object], ...]
    event_cursor: int
    project_next_cursor: int | None
    attention_next_cursor: str | None

    def as_dict(self) -> dict[str, object]:
        return {
            "data": {
                "projects": [dict(item) for item in self.projects],
                "attention": [dict(item) for item in self.attention],
            },
            "event_cursor": self.event_cursor,
            "project_next_cursor": self.project_next_cursor,
            "attention_next_cursor": self.attention_next_cursor,
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
            projects, project_next_cursor = _project_page(
                connection, before=None, limit=MAX_PAGE_SIZE
            )
            attention, attention_next_cursor = _attention_page(
                connection, before=None, limit=MAX_PAGE_SIZE
            )

        return WorkspaceSnapshot(
            projects=projects,
            attention=attention,
            event_cursor=event_cursor,
            project_next_cursor=project_next_cursor,
            attention_next_cursor=attention_next_cursor,
        )

    def projects(
        self,
        *,
        before: int | None = None,
        limit: int = DEFAULT_PAGE_SIZE,
    ) -> ProjectionPage:
        before = _integer_cursor(before)
        limit = _page_size(limit)
        with self.database.read_connection() as connection:
            connection.execute("BEGIN")
            event_cursor = _event_cursor(connection)
            items, next_cursor = _project_page(connection, before=before, limit=limit)
        return ProjectionPage(items, event_cursor, next_cursor)

    def attention(
        self,
        *,
        before: str | None = None,
        limit: int = DEFAULT_PAGE_SIZE,
    ) -> ProjectionPage:
        if before is not None:
            before = _identifier(before, "before")
        limit = _page_size(limit)
        with self.database.read_connection() as connection:
            connection.execute("BEGIN")
            event_cursor = _event_cursor(connection)
            items, next_cursor = _attention_page(connection, before=before, limit=limit)
        return ProjectionPage(items, event_cursor, next_cursor)

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
                FROM service_questions
                WHERE activity_id = ? ORDER BY question_id DESC LIMIT ?
                """,
                (activity_id, MAX_PAGE_SIZE + 1),
            ).fetchall()
            findings = connection.execute(
                """
                SELECT finding_id, project_id, activity_id, subject, detail,
                       status, version
                FROM service_findings
                WHERE activity_id = ? ORDER BY finding_id DESC LIMIT ?
                """,
                (activity_id, MAX_PAGE_SIZE + 1),
            ).fetchall()
            actions = connection.execute(
                """
                SELECT action_id, project_id, activity_id, kind, label, sequence
                FROM service_activity_actions
                WHERE activity_id = ? ORDER BY action_id DESC LIMIT ?
                """,
                (activity_id, MAX_PAGE_SIZE + 1),
            ).fetchall()
            data = _activity(row)
            data["questions"] = [
                _question(question) for question in questions[:MAX_PAGE_SIZE]
            ]
            data["question_next_cursor"] = _next_identity(questions)
            data["findings"] = [
                _finding(finding) for finding in findings[:MAX_PAGE_SIZE]
            ]
            data["finding_next_cursor"] = _next_identity(findings)
            data["available_actions"] = [
                _action(action) for action in actions[:MAX_PAGE_SIZE]
            ]
            data["action_next_cursor"] = _next_identity(actions)
        return ProjectionResult(data, event_cursor)

    def questions(
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
            boundary = "" if before is None else "AND question_id < ?"
            parameters: tuple[object, ...] = (project_id, activity_id)
            if before is not None:
                parameters += (before,)
            rows = connection.execute(
                f"""
                SELECT question_id, project_id, activity_id, subject, prompt,
                       requester, status, version
                FROM service_questions
                WHERE project_id = ? AND activity_id = ? {boundary}
                ORDER BY question_id DESC LIMIT ?
                """,
                parameters + (limit + 1,),
            ).fetchall()
            selected = rows[:limit]
            items = tuple(_question(row) for row in selected)
            next_cursor = _next_identity(rows, page_size=limit)
        return ProjectionPage(items, event_cursor, next_cursor)

    def actions(
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
            boundary = "" if before is None else "AND action_id < ?"
            parameters: tuple[object, ...] = (project_id, activity_id)
            if before is not None:
                parameters += (before,)
            rows = connection.execute(
                f"""
                SELECT action_id, project_id, activity_id, kind, label, sequence
                FROM service_activity_actions
                WHERE project_id = ? AND activity_id = ? {boundary}
                ORDER BY action_id DESC LIMIT ?
                """,
                parameters + (limit + 1,),
            ).fetchall()
            selected = rows[:limit]
            items = tuple(_action(row) for row in selected)
            next_cursor = _next_identity(rows, page_size=limit)
        return ProjectionPage(items, event_cursor, next_cursor)

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


def _project_page(
    connection: sqlite3.Connection, *, before: int | None, limit: int
) -> tuple[tuple[dict[str, object], ...], int | None]:
    boundary = "" if before is None else "WHERE rowid < ?"
    parameters: tuple[object, ...] = () if before is None else (before,)
    rows = connection.execute(
        f"""
        SELECT rowid, project_id, name, registration_status, version,
               (SELECT COUNT(*) FROM service_questions AS q
                WHERE q.project_id = service_projects.project_id
                  AND q.status IN ('awaiting_answer', 'clarification_required'))
               +
               (SELECT COUNT(*) FROM service_activity_actions AS aa
                WHERE aa.project_id = service_projects.project_id
                  AND aa.kind IN ('decision', 'recovery')) AS attention_count,
               (SELECT COUNT(*) FROM service_activities AS a
                WHERE a.project_id = service_projects.project_id
                  AND a.state NOT IN ('cancelled', 'completed', 'failed'))
                   AS current_activity_count
        FROM service_projects {boundary}
        ORDER BY rowid DESC LIMIT ?
        """,
        parameters + (limit + 1,),
    ).fetchall()
    selected = rows[:limit]
    projects = tuple(_project_summary(connection, row) for row in selected)
    projects = tuple(sorted(projects, key=_project_order))
    next_cursor = int(selected[-1][0]) if len(rows) > limit and selected else None
    return projects, next_cursor


def _project_summary(
    connection: sqlite3.Connection, row: tuple[object, ...]
) -> dict[str, object]:
    project_id = str(row[1])
    current = connection.execute(
        """
        SELECT rowid, activity_id, state FROM service_activities
        WHERE project_id = ? AND state NOT IN ('cancelled', 'completed', 'failed')
        ORDER BY rowid DESC LIMIT 1
        """,
        (project_id,),
    ).fetchall()
    selected = current[0] if current else connection.execute(
        """
        SELECT rowid, activity_id, state FROM service_activities
        WHERE project_id = ? ORDER BY rowid DESC LIMIT 1
        """,
        (project_id,),
    ).fetchone()
    current_count = int(row[6])
    if current_count > 1:
        activity_id: str | None = None
        activity_state = "multiple"
    else:
        activity_id = None if selected is None else str(selected[1])
        activity_state = "idle" if not current else str(selected[2])
    return {
        "project_id": project_id,
        "name": str(row[2]),
        "registration_status": str(row[3]),
        "version": int(row[4]),
        "activity_id": activity_id,
        "activity_state": activity_state,
        "current_activity_count": current_count,
        "attention_count": int(row[5]),
    }


def _attention_page(
    connection: sqlite3.Connection, *, before: str | None, limit: int
) -> tuple[tuple[dict[str, object], ...], str | None]:
    rows = connection.execute(
        """
        SELECT cursor, type, record_id, project_id, activity_id, subject, source
        FROM (
            SELECT 'question:' || question_id AS cursor,
                   'question' AS type,
                   question_id AS record_id,
                   project_id,
                   activity_id,
                   subject,
                   requester AS source
            FROM service_questions
            WHERE status IN ('awaiting_answer', 'clarification_required')
            UNION ALL
            SELECT kind || ':' || action_id AS cursor,
                   kind AS type,
                   action_id AS record_id,
                   project_id,
                   activity_id,
                   label AS subject,
                   'service' AS source
            FROM service_activity_actions
            WHERE kind IN ('decision', 'recovery')
        )
        WHERE (? IS NULL OR cursor < ?)
        ORDER BY cursor DESC LIMIT ?
        """,
        (before, before, limit + 1),
    ).fetchall()
    selected = rows[:limit]
    items = tuple(
        {
            "cursor": str(row[0]),
            "type": str(row[1]),
            "record_id": str(row[2]),
            "project_id": str(row[3]),
            "activity_id": str(row[4]),
            "subject": str(row[5]),
            "source": str(row[6]),
        }
        for row in selected
    )
    next_cursor = str(selected[-1][0]) if len(rows) > limit and selected else None
    return items, next_cursor


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


def _action(row: tuple[object, ...]) -> dict[str, object]:
    return {
        "action_id": str(row[0]),
        "project_id": str(row[1]),
        "activity_id": str(row[2]),
        "kind": str(row[3]),
        "label": str(row[4]),
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


def _next_identity(
    rows: list[tuple[object, ...]], *, page_size: int = MAX_PAGE_SIZE
) -> str | None:
    selected = rows[:page_size]
    return str(selected[-1][0]) if len(rows) > page_size and selected else None


def _identifier(value: str, field: str) -> str:
    try:
        return canonical_identifier(value, field)
    except (ContractError, TypeError) as error:
        raise ProjectionError("invalid_context", str(error), field=field) from error


def _integer_cursor(value: int | None) -> int | None:
    if value is not None and (
        isinstance(value, bool) or not isinstance(value, int) or value < 1
    ):
        raise ProjectionError(
            "invalid_cursor", "before cursor must be a positive integer"
        )
    return value


def _page_size(value: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= MAX_PAGE_SIZE:
        raise ProjectionError(
            "invalid_page_size",
            f"limit must be an integer from 1 through {MAX_PAGE_SIZE}",
            limit=value,
        )
    return value
