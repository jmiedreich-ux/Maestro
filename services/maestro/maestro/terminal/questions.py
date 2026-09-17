"""Storage-free terminal interaction for linked questions and answers."""

from __future__ import annotations

import urllib.parse
import uuid
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Protocol

from .connection import ServiceError, TerminalConnectionError
from .extensions import ExtensionContext, ExtensionRegistry, InputSubmission


class AnswerInput(Protocol):
    text: str
    cursor: int
    question_id: str | None

    def clear(self) -> None: ...


class QuestionState(Protocol):
    selected_project_id: str | None
    selected_activity_id: str | None
    selected_attention_detail: Mapping[str, object] | None
    error: str | None
    input: AnswerInput


@dataclass(frozen=True)
class PendingAnswer:
    request_id: str
    project_id: str
    activity_id: str
    question_id: str
    expected_version: int
    text: str
    choice_id: str | None

    @property
    def envelope(self) -> dict[str, object]:
        return {
            "request_id": self.request_id,
            "operation": "question.answer",
            "project_id": self.project_id,
            "activity_id": self.activity_id,
            "question_id": self.question_id,
            "expected_version": self.expected_version,
            "payload": {"text": self.text, "choice_id": self.choice_id},
        }


class QuestionInteraction:
    """One terminal session's explicit answer and uncertain-delivery state."""

    def __init__(
        self,
        *,
        request_id_factory: Callable[[], str] | None = None,
    ) -> None:
        self._request_id_factory = request_id_factory or (
            lambda: f"question-answer-{uuid.uuid4().hex}"
        )
        self.question: dict[str, object] | None = None
        self.selected_choice_id: str | None = None
        self.pending: PendingAnswer | None = None
        self.status: str | None = None

    def open(self, context: ExtensionContext, question_id: str) -> str:
        question_id = _identifier(question_id, "question_id")
        response = context.client.get_json(
            f"/questions/{urllib.parse.quote(question_id, safe='')}"
        )
        question = _question(response)
        state = _state(context)
        if question["project_id"] != state.selected_project_id:
            raise ValueError("question belongs to another selected project")
        if question["activity_id"] != state.selected_activity_id:
            raise ValueError("question belongs to another selected activity")
        if question["status"] not in {"awaiting_answer", "clarification_required"}:
            raise ValueError("question no longer accepts an answer")
        state.input.question_id = question_id
        self.question = question
        self.selected_choice_id = None
        self.status = None
        return self.render()

    def render(self) -> str:
        if self.question is None:
            return "No question selected."
        question = self.question
        lines = [
            str(question["subject"]),
            str(question["prompt"]),
            f"Requested by {question['requester']}",
        ]
        original = question.get("original_question_id")
        previous = question.get("previous_answer_id")
        if original is not None:
            lines.append(f"Follow-up to {original} after answer {previous}")
        choices = question["choices"]
        assert isinstance(choices, list)
        for choice in choices:
            assert isinstance(choice, dict)
            marker = "*" if choice["choice_id"] == self.selected_choice_id else " "
            recommendation = choice.get("recommendation_reason")
            suffix = (
                f" — Recommended: {recommendation}"
                if isinstance(recommendation, str)
                else ""
            )
            lines.append(
                f"{marker} [{choice['choice_id']}] {choice['label']} — "
                f"{choice['tradeoff']}{suffix}"
            )
        if bool(question["allow_free_text"]):
            lines.append("Free-text answer is available.")
        if self.status:
            lines.append(self.status)
        return "\n".join(lines)

    def choose(self, context: ExtensionContext, choice_id: str) -> None:
        if self.question is None:
            raise ValueError("open a question before selecting a choice")
        choice_id = _identifier(choice_id, "choice_id")
        choices = self.question["choices"]
        assert isinstance(choices, list)
        choice = next(
            (
                item
                for item in choices
                if isinstance(item, dict) and item.get("choice_id") == choice_id
            ),
            None,
        )
        if choice is None:
            raise ValueError("selected choice is not available")
        state = _state(context)
        label = str(choice["label"])
        state.input.text = label
        state.input.cursor = len(label)
        self.selected_choice_id = choice_id
        self.status = "Choice filled; Send or Enter submits it."

    def submit(
        self,
        context: ExtensionContext,
        *,
        choice_id: str | None = None,
    ) -> Mapping[str, object]:
        state = _state(context)
        question = self.question
        if question is None or state.input.question_id is None:
            raise ValueError("open a question before submitting an answer")
        text = state.input.text.strip()
        if not text:
            raise ValueError("answer text must be nonempty")
        if state.selected_project_id != question["project_id"]:
            raise ValueError("selected project changed before answer submission")
        if state.selected_activity_id != question["activity_id"]:
            raise ValueError("selected activity changed before answer submission")
        if choice_id is not None:
            choice_id = _identifier(choice_id, "choice_id")
            choices = question["choices"]
            assert isinstance(choices, list)
            if not any(
                isinstance(choice, Mapping)
                and choice.get("choice_id") == choice_id
                for choice in choices
            ):
                raise ValueError("selected choice is not available")
        self.selected_choice_id = choice_id
        proposed = PendingAnswer(
            request_id="",
            project_id=str(question["project_id"]),
            activity_id=str(question["activity_id"]),
            question_id=str(question["question_id"]),
            expected_version=int(question["version"]),
            text=text,
            choice_id=self.selected_choice_id,
        )
        if self.pending is not None and not _same_answer(self.pending, proposed):
            reconciled = self._reconcile(context, self.pending)
            if reconciled is not None:
                receipt = _receipt(reconciled)
                self._accepted(state, str(receipt["request_id"]))
                return reconciled
            self.pending = None
        if self.pending is None:
            request_id = _identifier(self._request_id_factory(), "request_id")
            self.pending = PendingAnswer(
                request_id,
                proposed.project_id,
                proposed.activity_id,
                proposed.question_id,
                proposed.expected_version,
                proposed.text,
                proposed.choice_id,
            )
        self._show_status(state, "Sending — waiting for save acknowledgment.")
        try:
            response = context.client.submit(self.pending.envelope)
        except ServiceError as error:
            self._show_status(state, f"Not sent — {error}.")
            if error.status_code in {400, 404, 409}:
                self.pending = None
            raise
        except TerminalConnectionError:
            self._show_status(
                state,
                "Not sent — Delivery not confirmed. Retrying will not submit "
                "your answer twice.",
            )
            raise
        receipt = _receipt(response)
        if receipt["request_id"] != self.pending.request_id:
            raise ValueError("service returned a receipt for another request")
        self._accepted(state, str(receipt["request_id"]))
        return response

    def retry(self, context: ExtensionContext) -> Mapping[str, object]:
        if self.pending is None:
            raise ValueError("no unconfirmed answer is available to retry")
        return self.submit(context, choice_id=self.pending.choice_id)

    def _reconcile(
        self, context: ExtensionContext, pending: PendingAnswer
    ) -> Mapping[str, object] | None:
        path = f"/requests/{urllib.parse.quote(pending.request_id, safe='')}"
        try:
            response = context.client.get_json(path)
        except ServiceError as error:
            if error.status_code == 404 and error.code == "request_not_found":
                return None
            self._show_status(
                _state(context),
                f"Not sent — previous delivery cannot be reconciled: {error}.",
            )
            raise
        except TerminalConnectionError:
            self._show_status(
                _state(context),
                "Not sent — previous delivery cannot be reconciled; edited text "
                "was not submitted.",
            )
            raise
        receipt = _receipt(response)
        if receipt["request_id"] != pending.request_id:
            raise ValueError("service returned a receipt for another request")
        return response

    def _accepted(self, state: QuestionState, request_id: str) -> None:
        self._show_status(
            state,
            f"Answer received — saved receipt {request_id}.",
            remove_choices=True,
        )
        state.input.clear()
        self.pending = None
        self.selected_choice_id = None
        if self.question is not None:
            self.question = {
                **self.question,
                "status": "answer_received",
                "choices": [],
            }

    def _show_status(
        self,
        state: QuestionState,
        message: str,
        *,
        remove_choices: bool = False,
    ) -> None:
        self.status = message
        detail = state.selected_attention_detail
        if isinstance(detail, Mapping):
            updated = dict(detail)
            prompt = (
                self.question.get("prompt")
                if self.question is not None
                else detail.get("prompt")
            )
            if isinstance(prompt, str) and prompt:
                updated["prompt"] = f"{prompt}\n{message}"
            else:
                updated["prompt"] = message
            if remove_choices:
                updated["choices"] = []
                updated["status"] = "answer_received"
            state.selected_attention_detail = updated
            state.error = None
        else:
            state.error = message


class QuestionsExtension:
    """Register the named question view and answer commands on the workspace."""

    def __init__(self, interaction: QuestionInteraction | None = None) -> None:
        self.interaction = interaction or QuestionInteraction()

    def install(self, registry: ExtensionRegistry) -> None:
        registry.register_input("question", self._open_input, self._submit_input)

    def _open_input(
        self, context: ExtensionContext, question_id: str
    ) -> Mapping[str, object]:
        self.interaction.open(context, question_id)
        assert self.interaction.question is not None
        return dict(self.interaction.question)

    def _submit_input(
        self, context: ExtensionContext, submission: InputSubmission
    ) -> object:
        state = _state(context)
        if state.input.text != submission.text:
            raise ValueError("question input changed before submission")
        return self.interaction.submit(
            context,
            choice_id=submission.selection_id,
        )


def _state(context: ExtensionContext) -> QuestionState:
    state = context.state
    if not hasattr(state, "input"):
        raise TypeError("question extension requires terminal input state")
    return state  # type: ignore[return-value]


def _question(response: Mapping[str, object]) -> dict[str, object]:
    if set(response) != {"data"} or not isinstance(response["data"], Mapping):
        raise ValueError("question response is invalid")
    question = dict(response["data"])
    required = {
        "question_id",
        "project_id",
        "activity_id",
        "subject",
        "prompt",
        "requester",
        "status",
        "version",
        "recipient",
        "original_question_id",
        "previous_answer_id",
        "allow_free_text",
        "choices",
    }
    if set(question) != required:
        raise ValueError("question response fields do not match the contract")
    for name in (
        "question_id",
        "project_id",
        "activity_id",
        "subject",
        "prompt",
        "requester",
        "status",
        "recipient",
    ):
        if not isinstance(question[name], str) or not question[name]:
            raise ValueError(f"question {name} is invalid")
    if (
        isinstance(question["version"], bool)
        or not isinstance(question["version"], int)
        or question["version"] < 1
    ):
        raise ValueError("question version is invalid")
    if not isinstance(question["allow_free_text"], bool):
        raise ValueError("question free-text setting is invalid")
    choices = question["choices"]
    if not isinstance(choices, list):
        raise ValueError("question choices are invalid")
    for choice in choices:
        if not isinstance(choice, Mapping) or set(choice) != {
            "choice_id",
            "label",
            "tradeoff",
            "recommendation_reason",
        }:
            raise ValueError("question choice is invalid")
    return question


def _receipt(response: Mapping[str, object]) -> Mapping[str, object]:
    receipt = response.get("receipt")
    if not isinstance(receipt, Mapping):
        raise ValueError("answer response has no durable receipt")
    if receipt.get("status") not in {"accepted", "completed"}:
        raise ValueError("answer was not accepted")
    if not isinstance(receipt.get("request_id"), str):
        raise ValueError("answer receipt identity is invalid")
    return receipt


def _same_answer(pending: PendingAnswer, proposed: PendingAnswer) -> bool:
    return (
        pending.project_id,
        pending.activity_id,
        pending.question_id,
        pending.expected_version,
        pending.text,
        pending.choice_id,
    ) == (
        proposed.project_id,
        proposed.activity_id,
        proposed.question_id,
        proposed.expected_version,
        proposed.text,
        proposed.choice_id,
    )


def _identifier(value: object, field: str) -> str:
    if not isinstance(value, str) or not value or len(value) > 128:
        raise ValueError(f"{field} is not a canonical identifier")
    if not value[0].isalnum() or any(
        not (character.isascii() and (character.isalnum() or character in "._:-"))
        for character in value
    ):
        raise ValueError(f"{field} is not a canonical identifier")
    return value
