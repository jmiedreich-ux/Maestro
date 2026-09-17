"""Connected terminal workspace over service projections and committed events."""

from __future__ import annotations

import urllib.parse
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from typing import Protocol

from .connection import (
    ConnectionState,
    ConnectionStatus,
    SSEEvent,
    TerminalConnectionError,
)
from .extensions import ExtensionContext, ExtensionRegistry


class WorkspaceError(ValueError):
    """A service projection cannot safely be displayed."""


class WorkspaceClient(Protocol):
    def workspace(self, *, connect_timeout: bool = False) -> Mapping[str, object]: ...

    def get_json(self, path: str, *, timeout: int = 15) -> Mapping[str, object]: ...

    def submit(self, envelope: Mapping[str, object]) -> Mapping[str, object]: ...


class View(str, Enum):
    PROJECTS = "projects"
    CONVERSATION = "conversation"
    ATTENTION = "attention"
    FINDINGS = "findings"


@dataclass(frozen=True)
class Project:
    project_id: str
    name: str
    registration_status: str
    activity_id: str | None
    activity_state: str
    current_activity_count: int
    attention_count: int
    version: int

    @classmethod
    def parse(cls, value: object) -> "Project":
        item = _object(value, "project")
        return cls(
            _text(item, "project_id"),
            _text(item, "name"),
            _text(item, "registration_status"),
            _optional_text(item, "activity_id"),
            _text(item, "activity_state"),
            _integer(item, "current_activity_count", minimum=0),
            _integer(item, "attention_count", minimum=0),
            _integer(item, "version", minimum=1),
        )


@dataclass(frozen=True)
class AttentionItem:
    cursor: str
    type: str
    record_id: str
    project_id: str
    activity_id: str
    subject: str
    source: str

    @classmethod
    def parse(cls, value: object) -> "AttentionItem":
        item = _object(value, "attention item")
        return cls(*(_text(item, name) for name in (
            "cursor", "type", "record_id", "project_id", "activity_id",
            "subject", "source",
        )))


@dataclass(frozen=True)
class Activity:
    activity_id: str
    project_id: str
    kind: str
    subject: str
    state: str
    waiting_reason: str | None
    started_at: str | None
    ended_at: str | None
    version: int

    @classmethod
    def parse(cls, value: object) -> "Activity":
        item = _object(value, "activity")
        return cls(
            _text(item, "activity_id"), _text(item, "project_id"),
            _text(item, "kind"), _text(item, "subject"), _text(item, "state"),
            _optional_text(item, "waiting_reason"),
            _optional_text(item, "started_at"), _optional_text(item, "ended_at"),
            _integer(item, "version", minimum=1),
        )


@dataclass(frozen=True)
class ConversationMessage:
    sequence: int
    message_id: str
    project_id: str
    activity_id: str | None
    source: str
    kind: str
    text: str
    occurred_at: str

    @classmethod
    def parse(cls, value: object) -> "ConversationMessage":
        item = _object(value, "conversation message")
        return cls(
            _integer(item, "sequence", minimum=1), _text(item, "message_id"),
            _text(item, "project_id"), _optional_text(item, "activity_id"),
            _text(item, "source"), _text(item, "kind"), _text(item, "text"),
            _text(item, "occurred_at"),
        )


@dataclass
class InputBuffer:
    text: str = ""
    cursor: int = 0
    question_id: str | None = None

    def clear(self) -> None:
        self.text = ""
        self.cursor = 0
        self.question_id = None

    def insert(self, value: str) -> None:
        self.text = self.text[: self.cursor] + value + self.text[self.cursor :]
        self.cursor += len(value)

    def backspace(self) -> None:
        if self.cursor:
            self.text = self.text[: self.cursor - 1] + self.text[self.cursor :]
            self.cursor -= 1


@dataclass
class Workspace:
    """Mutable presentation state; authoritative records remain in the service."""

    client: WorkspaceClient
    extensions: ExtensionRegistry = field(default_factory=ExtensionRegistry)
    projects: tuple[Project, ...] = ()
    attention: tuple[AttentionItem, ...] = ()
    activities: tuple[Activity, ...] = ()
    messages: tuple[ConversationMessage, ...] = ()
    activity_detail: Mapping[str, object] | None = None
    selected_project_id: str | None = None
    selected_activity_id: str | None = None
    selected_attention: str | None = None
    view: View = View.PROJECTS
    event_cursor: int = 0
    conversation_cursor: int | None = None
    connection_state: ConnectionState = ConnectionState.CONNECTING
    stale: bool = False
    error: str | None = None
    input: InputBuffer = field(default_factory=InputBuffer)
    conversation_offset: int = 0
    at_bottom: bool = True
    new_messages: bool = False
    focus: int = 0
    detail_open: bool = False
    detail_reading_offset: int = 0

    def refresh(self) -> None:
        """Load a cursor-consistent snapshot, preserving still-valid selection."""
        try:
            response = self.client.workspace()
            data = _object(response.get("data"), "workspace data")
            projects = tuple(Project.parse(item) for item in _list(data, "projects"))
            attention = tuple(
                AttentionItem.parse(item) for item in _list(data, "attention")
            )
            cursor = _integer(response, "event_cursor", minimum=0)
        except (
            TerminalConnectionError,
            WorkspaceError,
            TypeError,
            ValueError,
        ) as error:
            self.error = str(error)
            self.stale = bool(self.projects or self.messages)
            return
        self.projects = projects
        self.attention = attention
        self.event_cursor = cursor
        self.connection_state = ConnectionState.CONNECTED
        self.stale = False
        self.error = None
        if self.selected_project_id not in {item.project_id for item in projects}:
            self._clear_project_context()
        elif self.selected_project_id is not None:
            try:
                self._load_selected_project(preserve_activity=True)
            except (
                TerminalConnectionError,
                WorkspaceError,
                TypeError,
                ValueError,
            ) as error:
                self.error = str(error)
                self.stale = True

    def select_project(self, project_id: str) -> None:
        if project_id not in {item.project_id for item in self.projects}:
            raise WorkspaceError("selected project is not in the workspace")
        if project_id != self.selected_project_id:
            self.input.clear()
            self.selected_activity_id = None
            self.selected_attention = None
            self.messages = ()
            self.activities = ()
            self.conversation_cursor = None
            self.conversation_offset = 0
            self.at_bottom = True
            self.new_messages = False
        self.selected_project_id = project_id
        self.view = View.CONVERSATION
        self._load_selected_project(preserve_activity=False)

    def select_activity(self, activity_id: str) -> None:
        activity = next(
            (item for item in self.activities if item.activity_id == activity_id), None
        )
        if activity is None or activity.project_id != self.selected_project_id:
            raise WorkspaceError("selected activity is not available for this project")
        if activity_id != self.selected_activity_id:
            self.input.clear()
        self.selected_activity_id = activity_id
        self.activity_detail = self._read_data(
            f"/activities/{_segment(activity_id)}", "activity detail"
        )

    def open_attention(self, cursor: str) -> None:
        item = next((entry for entry in self.attention if entry.cursor == cursor), None)
        if item is None:
            raise WorkspaceError("attention item is no longer available")
        self.select_project(item.project_id)
        if item.activity_id != self.selected_activity_id:
            self.select_activity(item.activity_id)
        self.selected_attention = cursor
        if item.type == "question":
            self.input.question_id = item.record_id
        else:
            self.input.question_id = None
        self.view = View.CONVERSATION

    def load_earlier_messages(self) -> bool:
        if self.selected_project_id is None or self.conversation_cursor is None:
            return False
        response = self.client.get_json(
            self._conversation_path(before=self.conversation_cursor)
        )
        earlier, cursor, event_cursor = _message_page(response)
        existing = {message.message_id for message in self.messages}
        added = tuple(
            message for message in earlier if message.message_id not in existing
        )
        self.messages = added + self.messages
        self.conversation_cursor = cursor
        self.event_cursor = max(self.event_cursor, event_cursor)
        return bool(added)

    def apply_event(self, event: SSEEvent) -> None:
        """Refresh projections after a committed event, ignoring duplicates."""
        if event.event_id is None or not event.event_id.isdecimal():
            raise WorkspaceError("event is missing a durable numeric cursor")
        cursor = int(event.event_id)
        if cursor <= self.event_cursor:
            return
        was_bottom = self.at_bottom
        old_messages = {message.message_id for message in self.messages}
        self.refresh()
        if self.error is not None:
            return
        self.event_cursor = max(self.event_cursor, cursor)
        has_new = any(
            message.message_id not in old_messages for message in self.messages
        )
        if has_new and not was_bottom:
            self.at_bottom = False
            self.new_messages = True
        elif was_bottom:
            self.scroll_to_latest()

    def handle_connection_status(self, status: ConnectionStatus) -> None:
        self.connection_state = status.state
        if status.clear_service_context:
            self.projects = ()
            self.attention = ()
            self._clear_project_context()
            self.error = status.message
            self.stale = False
        elif status.state == ConnectionState.DISCONNECTED:
            self.stale = True
            self.error = "Disconnected—information may be out of date."
        elif status.state in {ConnectionState.UNAVAILABLE, ConnectionState.SETUP_ERROR}:
            self.error = status.message
            self.stale = bool(self.projects or self.messages)
        elif status.state == ConnectionState.CONNECTED:
            self.refresh()

    def scroll_messages(self, lines: int) -> None:
        if lines < 0:
            self.conversation_offset = min(
                max(0, len(self.messages) - 1), self.conversation_offset + abs(lines)
            )
            self.at_bottom = False
        elif lines > 0:
            self.conversation_offset = max(0, self.conversation_offset - lines)
            self.at_bottom = self.conversation_offset == 0
            if self.at_bottom:
                self.new_messages = False

    def scroll_to_latest(self) -> None:
        self.conversation_offset = 0
        self.at_bottom = True
        self.new_messages = False

    def handle_key(self, key: str) -> object | None:
        normalized = key.upper()
        if normalized == "TAB":
            self.focus += 1
        elif normalized == "SHIFT+TAB":
            self.focus = max(0, self.focus - 1)
        elif normalized == "UP":
            self.scroll_messages(-1)
        elif normalized == "DOWN":
            self.scroll_messages(1)
        elif normalized == "ESCAPE":
            self.detail_open = False
            self.detail_reading_offset = 0
        elif normalized == "SHIFT+ENTER":
            self.input.insert("\n")
        elif normalized == "BACKSPACE":
            self.input.backspace()
        elif normalized == "ENTER":
            return self.submit_input()
        elif len(key) == 1:
            self.input.insert(key)
        return None

    def submit_input(self) -> object | None:
        text = self.input.text
        if not text:
            return None
        if not text.startswith("/"):
            if self.input.question_id is None:
                raise WorkspaceError(
                    "input accepts commands until a question is selected"
                )
            raise WorkspaceError("answer submission is not installed in this workspace")
        command, _, arguments = text[1:].partition(" ")
        result = self.run_command(command, arguments)
        self.input.clear()
        return result

    def run_command(self, command: str, arguments: str = "") -> object | None:
        name = command.casefold()
        if name == "projects":
            self.view = View.PROJECTS
            return None
        if name == "attention":
            self.view = View.ATTENTION
            return None
        if name == "findings":
            if self.selected_activity_id is None:
                raise WorkspaceError("select an activity before opening findings")
            self.view = View.FINDINGS
            return None
        if name == "help":
            return ("projects", "attention", "findings") + self.extensions.command_names
        return self.extensions.invoke_command(
            name, ExtensionContext(self.client, self), arguments
        )

    def _load_selected_project(self, *, preserve_activity: bool) -> None:
        assert self.selected_project_id is not None
        prior_messages = self.messages
        prior_cursor = self.conversation_cursor
        encoded = _segment(self.selected_project_id)
        activities_response = self.client.get_json(f"/projects/{encoded}/activities")
        activities = tuple(
            Activity.parse(item) for item in _list(activities_response, "data")
        )
        for activity in activities:
            if activity.project_id != self.selected_project_id:
                raise WorkspaceError("service returned an activity for another project")
        self.activities = activities
        available = {item.activity_id for item in activities}
        if not preserve_activity or self.selected_activity_id not in available:
            summary = next(
                item for item in self.projects if item.project_id == self.selected_project_id
            )
            if summary.activity_id in available:
                self.selected_activity_id = summary.activity_id
            elif len(activities) == 1:
                self.selected_activity_id = activities[0].activity_id
            else:
                self.selected_activity_id = None
        response = self.client.get_json(self._conversation_path())
        messages, cursor, event_cursor = _message_page(response)
        if preserve_activity and prior_messages:
            by_identity = {message.message_id: message for message in prior_messages}
            by_identity.update({message.message_id: message for message in messages})
            self.messages = tuple(
                sorted(by_identity.values(), key=lambda message: message.sequence)
            )
            self.conversation_cursor = prior_cursor
        else:
            self.messages = messages
            self.conversation_cursor = cursor
        self.event_cursor = max(self.event_cursor, event_cursor)
        if self.selected_activity_id is not None:
            self.activity_detail = self._read_data(
                f"/activities/{_segment(self.selected_activity_id)}", "activity detail"
            )
        else:
            self.activity_detail = None

    def _read_data(self, path: str, label: str) -> Mapping[str, object]:
        response = self.client.get_json(path)
        self.event_cursor = max(
            self.event_cursor, _integer(response, "event_cursor", minimum=0)
        )
        return _object(response.get("data"), label)

    def _conversation_path(self, *, before: int | None = None) -> str:
        assert self.selected_project_id is not None
        path = f"/projects/{_segment(self.selected_project_id)}/conversation?limit=50"
        return path if before is None else f"{path}&before={before}"

    def _clear_project_context(self) -> None:
        self.selected_project_id = None
        self.selected_activity_id = None
        self.selected_attention = None
        self.activities = ()
        self.messages = ()
        self.activity_detail = None
        self.conversation_cursor = None
        self.input.clear()
        self.view = View.PROJECTS


def _message_page(
    response: Mapping[str, object],
) -> tuple[tuple[ConversationMessage, ...], int | None, int]:
    messages = tuple(
        ConversationMessage.parse(item) for item in _list(response, "data")
    )
    cursor_value = response.get("next_cursor")
    if cursor_value is not None and (
        isinstance(cursor_value, bool) or not isinstance(cursor_value, int)
    ):
        raise WorkspaceError("conversation next_cursor must be an integer or null")
    return messages, cursor_value, _integer(response, "event_cursor", minimum=0)


def _object(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise WorkspaceError(f"{label} must be an object")
    return value


def _list(value: Mapping[str, object], name: str) -> list[object]:
    result = value.get(name)
    if not isinstance(result, list):
        raise WorkspaceError(f"{name} must be a list")
    return result


def _text(value: Mapping[str, object], name: str) -> str:
    result = value.get(name)
    if not isinstance(result, str) or not result:
        raise WorkspaceError(f"{name} must be nonempty text")
    return result


def _optional_text(value: Mapping[str, object], name: str) -> str | None:
    result = value.get(name)
    if result is None:
        return None
    if not isinstance(result, str) or not result:
        raise WorkspaceError(f"{name} must be nonempty text or null")
    return result


def _integer(value: Mapping[str, object], name: str, *, minimum: int) -> int:
    result = value.get(name)
    if isinstance(result, bool) or not isinstance(result, int) or result < minimum:
        raise WorkspaceError(f"{name} must be an integer of at least {minimum}")
    return result


def _segment(value: str) -> str:
    return urllib.parse.quote(value, safe="")
