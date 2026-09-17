"""Deterministic text renderer for the connected terminal workspace."""

from __future__ import annotations

from dataclasses import dataclass

from .workspace import View, Workspace


MINIMUM_COLUMNS = 80
MINIMUM_ROWS = 24
MAXIMUM_INPUT_LINES = 6


@dataclass(frozen=True)
class TerminalSize:
    columns: int
    rows: int


class TerminalRenderer:
    """Render actual workspace state without performing service operations."""

    def render(self, workspace: Workspace, size: TerminalSize) -> str:
        if size.columns < MINIMUM_COLUMNS or size.rows < MINIMUM_ROWS:
            return "Enlarge the terminal to continue."
        lines = [self._header(workspace)]
        if workspace.error:
            prefix = "STALE" if workspace.stale else "ERROR"
            lines.append(f"{prefix}: {workspace.error}")
        if workspace.view == View.PROJECTS:
            lines.extend(self._projects(workspace))
        elif workspace.view == View.ATTENTION:
            lines.extend(self._attention(workspace))
        elif workspace.view == View.FINDINGS:
            lines.extend(self._findings(workspace))
        else:
            lines.extend(self._conversation(workspace, size.rows))
        lines.extend(self._input(workspace))
        return "\n".join(line[: size.columns] for line in lines)

    @staticmethod
    def _header(workspace: Workspace) -> str:
        selected = next(
            (
                item.name
                for item in workspace.projects
                if item.project_id == workspace.selected_project_id
            ),
            "No project selected",
        )
        state = workspace.connection_state.value
        return f"Maestro | {selected} | {state}"

    @staticmethod
    def _projects(workspace: Workspace) -> list[str]:
        if not workspace.projects and workspace.error is None:
            return ["No projects registered", "[Register project]"]
        lines = ["Projects"]
        for project in workspace.projects:
            attention = (
                f" | attention: {project.attention_count}"
                if project.attention_count else ""
            )
            lines.append(
                f"  {project.name} | {project.registration_status} | "
                f"{project.activity_state}{attention}"
            )
        return lines

    @staticmethod
    def _attention(workspace: Workspace) -> list[str]:
        if not workspace.attention and workspace.error is None:
            return ["No questions or decisions need your attention."]
        lines = ["Attention"]
        names = {project.project_id: project.name for project in workspace.projects}
        for item in workspace.attention:
            lines.append(
                f"  {names.get(item.project_id, item.project_id)} | {item.subject} "
                f"| {item.source} | {item.type}"
            )
        return lines

    @staticmethod
    def _findings(workspace: Workspace) -> list[str]:
        detail = workspace.activity_detail or {}
        findings = detail.get("findings", [])
        if not isinstance(findings, list) or not findings:
            return ["No findings recorded for this activity."]
        lines = ["Findings"]
        for finding in findings:
            if isinstance(finding, dict):
                lines.append(
                    f"  {finding.get('subject', 'Finding')}: "
                    f"{finding.get('detail', '')}"
                )
        return lines

    @staticmethod
    def _conversation(workspace: Workspace, rows: int) -> list[str]:
        lines: list[str] = []
        activity = next(
            (
                item
                for item in workspace.activities
                if item.activity_id == workspace.selected_activity_id
            ),
            None,
        )
        if activity is None and len(workspace.activities) > 1:
            lines.append("Select an activity")
        elif activity is not None:
            waiting = (
                f" — {activity.waiting_reason}" if activity.waiting_reason else ""
            )
            lines.append(f"{activity.subject} | {activity.state}{waiting}")
        if workspace.conversation_cursor is not None:
            lines.append("Load earlier messages")
        available = max(1, rows - 9)
        end = max(0, len(workspace.messages) - workspace.conversation_offset)
        start = max(0, end - available)
        for message in workspace.messages[start:end]:
            lines.append(f"{message.source}: {message.text}")
        if workspace.new_messages:
            lines.append("New messages")
        return lines

    @staticmethod
    def _input(workspace: Workspace) -> list[str]:
        if workspace.input.question_id:
            context = f"Answer question {workspace.input.question_id}"
        elif workspace.selected_project_id:
            context = "Commands only"
        else:
            context = "No project selected — commands only"
        text_lines = workspace.input.text.split("\n")[-MAXIMUM_INPUT_LINES:]
        return [f"Input | {context}"] + [f"> {line}" for line in text_lines]
