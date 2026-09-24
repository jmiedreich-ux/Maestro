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
        elif workspace.view == View.EXTENSION:
            lines.extend(self._extension(workspace))
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
            focus = _focus(workspace, "project", project.project_id)
            attention = (
                f" | attention: {project.attention_count}"
                if project.attention_count else ""
            )
            lines.append(
                f"{focus} {project.name} | {project.registration_status} | "
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
            focus = _focus(workspace, "attention", item.cursor)
            lines.append(
                f"{focus} {names.get(item.project_id, item.project_id)} | "
                f"{item.subject} "
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
        names = {project.project_id: project.name for project in workspace.projects}
        for item in workspace.notices():
            focus = _focus(workspace, "attention", item.cursor)
            lines.append(
                f"{focus} Attention: {names.get(item.project_id, item.project_id)}"
                f" needs a response | {item.subject} | {item.source} | {item.type}"
            )
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
            for candidate in workspace.activities:
                focus = _focus(workspace, "activity", candidate.activity_id)
                lines.append(f"{focus} {candidate.subject} | {candidate.state}")
        elif activity is not None:
            waiting = (
                f" — {activity.waiting_reason}" if activity.waiting_reason else ""
            )
            lines.append(f"{activity.subject} | {activity.state}{waiting}")
            lines.extend(_runtime_lines(workspace.activity_detail))
            for finding in workspace.findings():
                identity = str(finding["finding_id"])
                focus = _focus(workspace, "finding", identity)
                lines.append(
                    f"{focus} Finding: {finding.get('subject', '')} | "
                    f"{finding.get('status', '')}"
                )
                if workspace.detail_open and workspace.open_finding == identity:
                    lines.append(f"    {finding.get('detail', '')}")
        detail = workspace.selected_attention_detail
        if detail is not None:
            prompt = detail.get("prompt")
            label = detail.get("label")
            subject = detail.get("subject")
            if isinstance(prompt, str):
                lines.append(f"Question: {prompt}")
            elif isinstance(label, str):
                lines.append(f"Action: {label}")
            elif isinstance(subject, str):
                lines.append(f"Question: {subject}")
            for target in workspace.focus_targets():
                if target.kind == "choice":
                    lines.append(
                        f"{_focus(workspace, target.kind, target.identity)} "
                        f"{target.label}"
                    )
        for target in workspace.focus_targets():
            if target.kind == "action":
                lines.append(
                    f"{_focus(workspace, target.kind, target.identity)} "
                    f"{target.label}"
                )
        if workspace.conversation_cursor is not None:
            lines.append(
                f"{_focus(workspace, 'control', 'load-earlier')} "
                "Load earlier messages"
            )
        available = max(1, rows - 9)
        end = max(0, len(workspace.messages) - workspace.conversation_offset)
        start = max(0, end - available)
        for message in workspace.messages[start:end]:
            lines.append(f"{message.source}: {message.text}")
        if workspace.new_messages:
            lines.append(
                f"{_focus(workspace, 'control', 'new-messages')} New messages"
            )
        return lines

    @staticmethod
    def _extension(workspace: Workspace) -> list[str]:
        title = workspace.extension_view_name or "Extension"
        content = workspace.extension_view_content
        if isinstance(content, str):
            rendered = content.splitlines() or [""]
        else:
            rendered = [str(content)]
        return [title] + rendered

    @staticmethod
    def _input(workspace: Workspace) -> list[str]:
        if workspace.input.question_id:
            context = f"Answer question {workspace.input.question_id}"
        elif workspace.selected_project_id:
            context = "Commands only"
        else:
            context = "No project selected — commands only"
        text_lines = workspace.input.text.split("\n")[-MAXIMUM_INPUT_LINES:]
        focus = _focus(workspace, "editor", "input")
        return [f"{focus} Input | {context}"] + [f"> {line}" for line in text_lines]


def _focus(workspace: Workspace, kind: str, identity: str) -> str:
    target = workspace.focused_target
    return ">" if target is not None and (target.kind, target.identity) == (
        kind,
        identity,
    ) else " "


def _runtime_lines(detail: object) -> list[str]:
    """Show recorded runtime readings; unknown, estimated and stale stay explicit."""
    runtime = detail.get("runtime") if isinstance(detail, dict) else None
    if not isinstance(runtime, dict):
        return []
    entries = [
        item
        for name in ("runs", "sessions", "assignment_totals")
        for item in (runtime.get(name) or [])
        if isinstance(item, dict)
    ]
    if not entries:
        return ["Runtime: no measurements recorded"]
    lines = []
    for item in entries:
        quality = str(item.get("quality") or "unknown")
        if item.get("stale"):
            quality += ", stale"
        percent = item.get("context_percent")
        context = (
            "context unknown"
            if item.get("context_used") is None
            else f"context {item.get('context_used')}/{_reading(item.get('context_limit'))}"
            + ("" if percent is None else f" ({percent}%)")
        )
        lines.append(
            f"Runtime {item.get('role') or item.get('run_id') or item.get('session_id') or ''}: "
            f"active {_reading(item.get('active_seconds'))}s, "
            f"waiting {_reading(item.get('waiting_seconds'))}s, "
            f"tokens in {_reading(item.get('input_tokens'))} "
            f"out {_reading(item.get('output_tokens'))}, {context} "
            f"[{quality}; {item.get('observed_at') or 'time unknown'}]"
        )
    return lines


def _reading(value: object) -> str:
    return "unknown" if value is None else str(value)
