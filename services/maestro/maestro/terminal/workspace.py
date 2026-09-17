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
    ServiceError,
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
    EXTENSION = "extension"


@dataclass(frozen=True)
class FocusTarget:
    kind: str
    identity: str
    label: str


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
    selected_attention_detail: Mapping[str, object] | None = None
    extension_view_name: str | None = None
    extension_view_content: object | None = None

    def refresh(self) -> None:
        """Load a cursor-consistent snapshot, preserving still-valid selection."""
        try:
            response = self.client.workspace()
            data = _object(response.get("data"), "workspace data")
            cursor = _integer(response, "event_cursor", minimum=0)
            projects = self._complete_projects(
                tuple(Project.parse(item) for item in _list(data, "projects")),
                _optional_cursor(response, "project_next_cursor"),
                cursor,
            )
            attention = self._complete_attention(
                tuple(
                    AttentionItem.parse(item) for item in _list(data, "attention")
                ),
                _optional_cursor(response, "attention_next_cursor"),
                cursor,
            )
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
        self._bound_focus()
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
        self._require_online()
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
        self._focus_editor()

    def select_activity(self, activity_id: str) -> None:
        self._require_online()
        activity = next(
            (item for item in self.activities if item.activity_id == activity_id), None
        )
        if activity is None or activity.project_id != self.selected_project_id:
            raise WorkspaceError("selected activity is not available for this project")
        if activity_id != self.selected_activity_id:
            self.input.clear()
        self.selected_activity_id = activity_id
        self.activity_detail = self._read_activity_detail(activity_id)
        self.selected_attention = None
        self.selected_attention_detail = None
        self._focus_editor()

    def open_attention(self, cursor: str) -> None:
        self._require_online()
        item = next((entry for entry in self.attention if entry.cursor == cursor), None)
        if item is None:
            raise WorkspaceError("attention item is no longer available")
        self.select_project(item.project_id)
        if item.activity_id != self.selected_activity_id:
            self.select_activity(item.activity_id)
        self.selected_attention = cursor
        if item.type == "question":
            self.input.question_id = item.record_id
            self.selected_attention_detail = _find_detail(
                self.activity_detail, "questions", "question_id", item.record_id
            ) or {
                "question_id": item.record_id,
                "subject": item.subject,
                "requester": item.source,
            }
        else:
            self.input.question_id = None
            self.selected_attention_detail = _find_detail(
                self.activity_detail,
                "available_actions",
                "action_id",
                item.record_id,
            ) or {
                "action_id": item.record_id,
                "kind": item.type,
                "label": item.subject,
            }
        self.view = View.CONVERSATION
        if item.type in {"decision", "recovery"}:
            self._focus_target("action", item.record_id)
        else:
            self._focus_editor()

    def load_earlier_messages(self) -> bool:
        self._require_online()
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
        anchor = self._reading_anchor()
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
            self._restore_reading_anchor(anchor)
        elif was_bottom:
            self.scroll_to_latest()

    def handle_event_error(self, error: TerminalConnectionError) -> None:
        """Recover an unavailable durable cursor only by loading a fresh snapshot."""
        if isinstance(error, ServiceError) and error.code == "event_cursor_unavailable":
            self.refresh()
            return
        self.handle_connection_status(
            ConnectionStatus(
                ConnectionState.DISCONNECTED,
                "service",
                str(error),
            )
        )

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
            self._move_focus(1, same_kind=False)
        elif normalized == "SHIFT+TAB":
            self._move_focus(-1, same_kind=False)
        elif normalized == "UP":
            if not self._move_focus(-1, same_kind=True):
                self.scroll_messages(-1)
        elif normalized == "DOWN":
            if not self._move_focus(1, same_kind=True):
                self.scroll_messages(1)
        elif normalized == "ESCAPE":
            self.detail_open = False
            self.detail_reading_offset = 0
        elif normalized == "SHIFT+ENTER":
            if self._editor_focused():
                self.input.insert("\n")
        elif normalized == "BACKSPACE":
            if self._editor_focused():
                self.input.backspace()
        elif normalized == "ENTER":
            return self.activate_focused()
        elif len(key) == 1 and self._editor_focused():
            self.input.insert(key)
        return None

    @property
    def focused_target(self) -> FocusTarget | None:
        targets = self.focus_targets()
        if not targets:
            return None
        self.focus = min(max(0, self.focus), len(targets) - 1)
        return targets[self.focus]

    def focus_targets(self) -> tuple[FocusTarget, ...]:
        targets: list[FocusTarget] = []
        if self.view == View.PROJECTS:
            targets.extend(
                FocusTarget("project", item.project_id, item.name)
                for item in self.projects
            )
        elif self.view == View.ATTENTION:
            targets.extend(
                FocusTarget("attention", item.cursor, item.subject)
                for item in self.attention
            )
        elif self.view == View.CONVERSATION:
            if len(self.activities) > 1:
                targets.extend(
                    FocusTarget("activity", item.activity_id, item.subject)
                    for item in self.activities
                )
            if self.conversation_cursor is not None:
                targets.append(
                    FocusTarget("control", "load-earlier", "Load earlier messages")
                )
            if self.new_messages:
                targets.append(FocusTarget("control", "new-messages", "New messages"))
            targets.extend(self._choice_targets())
            targets.extend(self._activity_action_targets())
        targets.append(FocusTarget("editor", "input", "Input"))
        return tuple(targets)

    def activate_focused(self) -> object | None:
        target = self.focused_target
        if target is None:
            return None
        if target.kind == "project":
            self.select_project(target.identity)
            return None
        if target.kind == "activity":
            self.select_activity(target.identity)
            return None
        if target.kind == "attention":
            self.open_attention(target.identity)
            return None
        if target.kind == "choice":
            self.input.text = target.label
            self.input.cursor = len(target.label)
            return None
        if target.kind == "action":
            return self.invoke_activity_action(target.identity)
        if target.kind == "control" and target.identity == "load-earlier":
            return self.load_earlier_messages()
        if target.kind == "control" and target.identity == "new-messages":
            self.scroll_to_latest()
            return None
        if target.kind == "editor":
            return self.submit_input()
        raise WorkspaceError("focused terminal control is unavailable")

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
            self.focus = 0
            return None
        if name == "attention":
            self.view = View.ATTENTION
            self.focus = 0
            return None
        if name == "findings":
            if self.selected_activity_id is None:
                raise WorkspaceError("select an activity before opening findings")
            self.view = View.FINDINGS
            self.focus = 0
            return None
        if name == "help":
            return ("projects", "attention", "findings") + self.extensions.command_names
        self._require_online()
        return self.extensions.invoke_command(
            name, ExtensionContext(self.client, self), arguments
        )

    def open_extension_view(self, name: str, arguments: str = "") -> object:
        self._require_online()
        content = self.extensions.render_view(
            name, ExtensionContext(self.client, self), arguments
        )
        self.extension_view_name = name
        self.extension_view_content = content
        self.view = View.EXTENSION
        self.focus = 0
        return content

    def invoke_action(self, name: str, arguments: str = "") -> object:
        self._require_online()
        return self.extensions.invoke_action(
            name, ExtensionContext(self.client, self), arguments
        )

    def invoke_selected_action(self) -> object:
        item = next(
            (
                entry
                for entry in self.attention
                if entry.cursor == self.selected_attention
                and entry.type in {"decision", "recovery"}
            ),
            None,
        )
        if item is None:
            raise WorkspaceError("no recovery or decision action is selected")
        return self.invoke_activity_action(item.record_id)

    def invoke_activity_action(self, action_id: str) -> object:
        action = _find_detail(
            self.activity_detail, "available_actions", "action_id", action_id
        )
        if action is None:
            raise WorkspaceError("activity action is no longer available")
        kind = action.get("kind")
        if not isinstance(kind, str) or not kind:
            raise WorkspaceError("activity action kind is unavailable")
        return self.invoke_action(kind, action_id)

    def _require_online(self) -> None:
        if self.connection_state != ConnectionState.CONNECTED or self.stale:
            raise WorkspaceError(
                "service command is unavailable while disconnected or stale"
            )

    def _complete_projects(
        self,
        initial: tuple[Project, ...],
        cursor: str | None,
        event_cursor: int,
    ) -> tuple[Project, ...]:
        items = list(initial)
        seen_cursors: set[str] = set()
        seen_ids = {item.project_id for item in initial}
        while cursor is not None:
            if cursor in seen_cursors:
                raise WorkspaceError("project pagination cursor repeated")
            seen_cursors.add(cursor)
            response = self.client.get_json(
                f"/projects?before={urllib.parse.quote(cursor, safe='')}&limit=100"
            )
            _same_event_cursor(response, event_cursor)
            page = tuple(Project.parse(item) for item in _list(response, "data"))
            if any(item.project_id in seen_ids for item in page):
                raise WorkspaceError("project pagination repeated an entry")
            items.extend(page)
            seen_ids.update(item.project_id for item in page)
            cursor = _optional_cursor(response, "next_cursor")
        return tuple(items)

    def _complete_attention(
        self,
        initial: tuple[AttentionItem, ...],
        cursor: str | None,
        event_cursor: int,
    ) -> tuple[AttentionItem, ...]:
        items = list(initial)
        seen_cursors: set[str] = set()
        seen_ids = {item.cursor for item in initial}
        while cursor is not None:
            if cursor in seen_cursors:
                raise WorkspaceError("attention pagination cursor repeated")
            seen_cursors.add(cursor)
            response = self.client.get_json(
                f"/attention?before={urllib.parse.quote(cursor, safe='')}&limit=100"
            )
            _same_event_cursor(response, event_cursor)
            page = tuple(
                AttentionItem.parse(item) for item in _list(response, "data")
            )
            if any(item.cursor in seen_ids for item in page):
                raise WorkspaceError("attention pagination repeated an entry")
            items.extend(page)
            seen_ids.update(item.cursor for item in page)
            cursor = _optional_cursor(response, "next_cursor")
        return tuple(items)

    def _load_selected_project(self, *, preserve_activity: bool) -> None:
        assert self.selected_project_id is not None
        prior_messages = self.messages
        prior_cursor = self.conversation_cursor
        encoded = _segment(self.selected_project_id)
        activities_response = self.client.get_json(f"/projects/{encoded}/activities")
        activities = tuple(
            Activity.parse(item) for item in _list(activities_response, "data")
        )
        activities = self._complete_activities(
            activities,
            _optional_integer_cursor(activities_response, "next_cursor"),
            _integer(activities_response, "event_cursor", minimum=0),
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
            self.activity_detail = self._read_activity_detail(
                self.selected_activity_id
            )
        else:
            self.activity_detail = None

    def _complete_activities(
        self,
        initial: tuple[Activity, ...],
        cursor: int | None,
        event_cursor: int,
    ) -> tuple[Activity, ...]:
        assert self.selected_project_id is not None
        items = list(initial)
        seen_cursors: set[int] = set()
        seen_ids = {item.activity_id for item in initial}
        if len(seen_ids) != len(initial):
            raise WorkspaceError("activity page repeated an entry")
        encoded = _segment(self.selected_project_id)
        while cursor is not None:
            if cursor in seen_cursors:
                raise WorkspaceError("activity pagination cursor repeated")
            seen_cursors.add(cursor)
            response = self.client.get_json(
                f"/projects/{encoded}/activities?before={cursor}&limit=50"
            )
            _same_event_cursor(response, event_cursor)
            page = tuple(Activity.parse(item) for item in _list(response, "data"))
            page_ids = [item.activity_id for item in page]
            if len(set(page_ids)) != len(page_ids) or any(
                identity in seen_ids for identity in page_ids
            ):
                raise WorkspaceError("activity pagination repeated an entry")
            items.extend(page)
            seen_ids.update(page_ids)
            cursor = _optional_integer_cursor(response, "next_cursor")
        return tuple(items)

    def _read_activity_detail(self, activity_id: str) -> Mapping[str, object]:
        response = self.client.get_json(f"/activities/{_segment(activity_id)}")
        event_cursor = _integer(response, "event_cursor", minimum=0)
        self.event_cursor = max(self.event_cursor, event_cursor)
        detail = dict(_object(response.get("data"), "activity detail"))
        assert self.selected_project_id is not None
        routes = (
            ("questions", "question_next_cursor", "question_id"),
            ("findings", "finding_next_cursor", "finding_id"),
            ("available_actions", "action_next_cursor", "action_id"),
        )
        for collection, cursor_name, identity_name in routes:
            initial = detail.get(collection)
            if not isinstance(initial, list):
                raise WorkspaceError(f"{collection} must be a list")
            detail[collection] = self._complete_activity_details(
                activity_id,
                collection,
                identity_name,
                initial,
                _optional_cursor(detail, cursor_name),
                event_cursor,
            )
            detail[cursor_name] = None
        return detail

    def _complete_activity_details(
        self,
        activity_id: str,
        collection: str,
        identity_name: str,
        initial: list[object],
        cursor: str | None,
        event_cursor: int,
    ) -> list[object]:
        assert self.selected_project_id is not None
        items = list(initial)
        seen_ids = {_detail_identity(item, identity_name) for item in items}
        if len(seen_ids) != len(items):
            raise WorkspaceError(f"{collection} page repeated an entry")
        seen_cursors: set[str] = set()
        resource = "actions" if collection == "available_actions" else collection
        project = _segment(self.selected_project_id)
        activity = _segment(activity_id)
        while cursor is not None:
            if cursor in seen_cursors:
                raise WorkspaceError(f"{resource} pagination cursor repeated")
            seen_cursors.add(cursor)
            response = self.client.get_json(
                f"/projects/{project}/activities/{activity}/{resource}"
                f"?before={urllib.parse.quote(cursor, safe='')}&limit=100"
            )
            _same_event_cursor(response, event_cursor)
            page = _list(response, "data")
            page_ids = [_detail_identity(item, identity_name) for item in page]
            if len(set(page_ids)) != len(page_ids) or any(
                identity in seen_ids for identity in page_ids
            ):
                raise WorkspaceError(f"{resource} pagination repeated an entry")
            for item in page:
                value = _object(item, f"{resource} entry")
                if (
                    value.get("project_id") != self.selected_project_id
                    or value.get("activity_id") != activity_id
                ):
                    raise WorkspaceError(
                        f"{resource} pagination returned another activity context"
                    )
            items.extend(page)
            seen_ids.update(page_ids)
            cursor = _optional_cursor(response, "next_cursor")
        return items

    def _conversation_path(self, *, before: int | None = None) -> str:
        assert self.selected_project_id is not None
        path = f"/projects/{_segment(self.selected_project_id)}/conversation?limit=50"
        return path if before is None else f"{path}&before={before}"

    def _reading_anchor(self) -> str | None:
        if self.at_bottom or not self.messages:
            return None
        end = max(0, len(self.messages) - self.conversation_offset)
        if end == 0:
            return self.messages[0].message_id
        return self.messages[end - 1].message_id

    def _restore_reading_anchor(self, message_id: str | None) -> None:
        if message_id is None:
            return
        for index, message in enumerate(self.messages):
            if message.message_id == message_id:
                self.conversation_offset = len(self.messages) - index - 1
                return

    def _choice_targets(self) -> tuple[FocusTarget, ...]:
        detail = self.selected_attention_detail
        choices = None if detail is None else detail.get("choices")
        if not isinstance(choices, list):
            return ()
        targets: list[FocusTarget] = []
        for index, choice in enumerate(choices):
            if isinstance(choice, str) and choice:
                targets.append(FocusTarget("choice", str(index), choice))
            elif isinstance(choice, Mapping):
                label = choice.get("label")
                identity = choice.get("choice_id", choice.get("id", index))
                if isinstance(label, str) and label:
                    targets.append(FocusTarget("choice", str(identity), label))
        return tuple(targets)

    def _activity_action_targets(self) -> tuple[FocusTarget, ...]:
        values = (
            None
            if self.activity_detail is None
            else self.activity_detail.get("available_actions")
        )
        if not isinstance(values, list):
            return ()
        targets: list[FocusTarget] = []
        for value in values:
            if isinstance(value, Mapping):
                action_id = value.get("action_id")
                label = value.get("label")
                if isinstance(action_id, str) and isinstance(label, str):
                    targets.append(FocusTarget("action", action_id, label))
        return tuple(targets)

    def _move_focus(self, step: int, *, same_kind: bool) -> bool:
        targets = self.focus_targets()
        if not targets:
            self.focus = 0
            return False
        self._bound_focus()
        if not same_kind:
            self.focus = min(max(0, self.focus + step), len(targets) - 1)
            return True
        kind = targets[self.focus].kind
        candidate = self.focus + step
        if 0 <= candidate < len(targets) and targets[candidate].kind == kind:
            self.focus = candidate
            return True
        return kind in {"project", "activity", "attention", "choice"}

    def _editor_focused(self) -> bool:
        target = self.focused_target
        return target is not None and target.kind == "editor"

    def _focus_editor(self) -> None:
        self._focus_target("editor", "input")

    def _focus_target(self, kind: str, identity: str) -> None:
        for index, target in enumerate(self.focus_targets()):
            if target.kind == kind and target.identity == identity:
                self.focus = index
                return
        self._bound_focus()

    def _bound_focus(self) -> None:
        targets = self.focus_targets()
        self.focus = min(max(0, self.focus), max(0, len(targets) - 1))

    def _clear_project_context(self) -> None:
        self.selected_project_id = None
        self.selected_activity_id = None
        self.selected_attention = None
        self.selected_attention_detail = None
        self.activities = ()
        self.messages = ()
        self.activity_detail = None
        self.conversation_cursor = None
        self.input.clear()
        self.view = View.PROJECTS
        self.focus = 0


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


def _find_detail(
    detail: Mapping[str, object] | None,
    collection: str,
    identity_name: str,
    identity: str,
) -> Mapping[str, object] | None:
    values = None if detail is None else detail.get(collection)
    if not isinstance(values, list):
        return None
    for value in values:
        if isinstance(value, Mapping) and value.get(identity_name) == identity:
            return value
    return None


def _optional_cursor(value: Mapping[str, object], name: str) -> str | None:
    result = value.get(name)
    if result is None:
        return None
    if not isinstance(result, str) or not result:
        raise WorkspaceError(f"{name} must be nonempty text or null")
    return result


def _optional_integer_cursor(
    value: Mapping[str, object], name: str
) -> int | None:
    result = value.get(name)
    if result is None:
        return None
    if isinstance(result, bool) or not isinstance(result, int) or result < 1:
        raise WorkspaceError(f"{name} must be a positive integer or null")
    return result


def _detail_identity(value: object, name: str) -> str:
    item = _object(value, "activity detail entry")
    return _text(item, name)


def _same_event_cursor(value: Mapping[str, object], expected: int) -> None:
    observed = _integer(value, "event_cursor", minimum=0)
    if observed != expected:
        raise WorkspaceError("workspace changed while loading its remaining pages")


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
