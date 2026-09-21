"""Storage-free registration publication, confirmation, and history controls."""

from __future__ import annotations

import urllib.parse
import uuid
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime, timezone

from .connection import ServiceError, TerminalConnectionError
from .extensions import ExtensionContext, ExtensionRegistry


@dataclass(frozen=True)
class PendingConfirmation:
    request_id: str
    confirmation_id: str
    project_id: str
    activity_id: str
    expected_version: int
    package_ref: Mapping[str, object]
    confirmed_at: str

    @property
    def envelope(self) -> dict[str, object]:
        return {
            "request_id": self.request_id,
            "operation": "registration.confirm",
            "project_id": self.project_id,
            "activity_id": self.activity_id,
            "expected_version": self.expected_version,
            "payload": {
                "confirmation_id": self.confirmation_id,
                "package_ref": dict(self.package_ref),
                "confirmed_at": self.confirmed_at,
            },
        }


class RegistrationInteraction:
    """One terminal session's exact package view and explicit confirmation."""

    def __init__(
        self,
        *,
        request_id_factory: Callable[[], str] | None = None,
        confirmation_id_factory: Callable[[], str] | None = None,
        time_factory: Callable[[], str] | None = None,
    ) -> None:
        self._request_id_factory = request_id_factory or (
            lambda: f"registration-confirm-{uuid.uuid4().hex}"
        )
        self._confirmation_id_factory = confirmation_id_factory or (
            lambda: f"confirmation-{uuid.uuid4().hex}"
        )
        self._time_factory = time_factory or (
            lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        )
        self.detail: dict[str, object] | None = None
        self.pending: PendingConfirmation | None = None
        self.status: str | None = None

    def open(self, context: ExtensionContext) -> str:
        project_id, activity_id = _selection(context)
        response = context.client.get_json(
            f"/registrations/{urllib.parse.quote(activity_id, safe='')}"
        )
        detail = _registration_detail(response)
        if detail["project_id"] != project_id or detail["activity_id"] != activity_id:
            raise ValueError("registration detail differs from the selected activity")
        self.detail = detail
        self.status = None
        if self.pending is not None and not self._pending_matches(
            project_id, activity_id, detail
        ):
            self.status = self._pending_block_message()
        return self.render()

    def render(self) -> str:
        if self.detail is None:
            return "No registration selected."
        detail = self.detail
        package = detail["package_ref"]
        lines = [
            f"Registration — {detail['project_id']}",
            f"State: {detail['state']}",
        ]
        if isinstance(package, Mapping):
            lines.append(
                f"Candidate: version {package['registration_version']} / "
                f"{package['candidate_id']} / {package['manifest_sha256']}"
            )
        else:
            lines.append("Candidate: not yet available")
        history = detail["history"]
        assert isinstance(history, list)
        lines.append(f"Confirmed history: {len(history)}")
        for item in history:
            assert isinstance(item, Mapping)
            lines.append(f"- {item['confirmation_id']} — {item['sha256']}")
        if bool(detail["can_confirm"]):
            assert isinstance(package, Mapping)
            lines.append(
                "Confirm registration action is available for exact candidate "
                f"{package['candidate_id']}."
            )
        if self.status:
            lines.append(self.status)
        return "\n".join(lines)

    def confirm(self, context: ExtensionContext, candidate_id: str) -> Mapping[str, object]:
        if self.detail is None:
            raise ValueError("open the registration before confirming it")
        detail = self.detail
        project_id, activity_id = _selection(context)
        if detail["project_id"] != project_id or detail["activity_id"] != activity_id:
            raise ValueError("selected registration changed before confirmation")
        if not bool(detail["can_confirm"]):
            raise ValueError("registration is not currently eligible for confirmation")
        package = detail["package_ref"]
        if not isinstance(package, Mapping):
            raise ValueError("registration has no candidate to confirm")
        if candidate_id.strip() != package["candidate_id"]:
            raise ValueError("confirmation must name the displayed exact candidate")
        if self.pending is not None and not self._pending_matches(
            project_id, activity_id, detail
        ):
            self.status = self._pending_block_message()
            raise ValueError(self.status)
        if self.pending is None:
            self.pending = PendingConfirmation(
                _identifier(self._request_id_factory(), "request_id"),
                _identifier(self._confirmation_id_factory(), "confirmation_id"),
                project_id,
                activity_id,
                int(detail["activity_version"]),
                dict(package),
                _text(self._time_factory(), "confirmed_at"),
            )
        self.status = "Confirming — waiting for publication and activation acknowledgment."
        try:
            response = context.client.submit(self.pending.envelope)
        except ServiceError as error:
            self.status = f"Not confirmed — {error}."
            if error.status_code in {400, 404, 409}:
                self.pending = None
            raise
        except TerminalConnectionError:
            self.status = (
                "Outcome not confirmed. Reconnect and retry to reconcile the saved request."
            )
            raise
        receipt = _receipt(response)
        if receipt["request_id"] != self.pending.request_id:
            raise ValueError("service returned a receipt for another confirmation request")
        self.status = "Registered. Confirmation and history are saved."
        self.pending = None
        return response

    def retry(
        self,
        context: ExtensionContext,
        publication_operation_id: str | None = None,
        intervention: str | None = None,
    ) -> Mapping[str, object]:
        if self.pending is None:
            if self.detail is None:
                raise ValueError("open the registration before retrying it")
            operation_id = _identifier(
                publication_operation_id, "publication_operation_id"
            )
            reason = _text(intervention, "intervention")
            project_id, activity_id = _selection(context)
            response = context.client.submit(
                {
                    "request_id": self._request_id_factory(),
                    "operation": "registration.retry",
                    "project_id": project_id,
                    "activity_id": activity_id,
                    "question_id": None,
                    "expected_version": self.detail["activity_version"],
                    "payload": {
                        "publication_operation_id": operation_id,
                        "intervention": reason,
                    },
                }
            )
            self.status = "Registration recovery reconciled from saved state."
            return response
        try:
            response = context.client.get_json(
                f"/requests/{urllib.parse.quote(self.pending.request_id, safe='')}"
            )
        except ServiceError as error:
            if error.status_code != 404 or error.code != "request_not_found":
                raise
            self.status = "Retrying the saved registration confirmation request."
            try:
                response = context.client.submit(self.pending.envelope)
            except ServiceError as submit_error:
                self.status = f"Not confirmed — {submit_error}."
                if submit_error.status_code in {400, 404, 409}:
                    self.pending = None
                raise
            except TerminalConnectionError:
                self.status = (
                    "Outcome not confirmed. Reconnect and retry to reconcile the saved request."
                )
                raise
        receipt = _receipt(response)
        if receipt["request_id"] != self.pending.request_id:
            raise ValueError("service returned a receipt for another confirmation request")
        self.status = "Registered. Confirmation and history are saved."
        self.pending = None
        return response

    def start(self, context: ExtensionContext, repository: str) -> Mapping[str, object]:
        repository = repository.strip()
        if not repository:
            raise ValueError("register requires an owner/repository")
        response = context.client.submit(
            {
                "request_id": self._request_id_factory(),
                "operation": "registration.start",
                "project_id": None,
                "activity_id": None,
                "question_id": None,
                "expected_version": None,
                "payload": {"repository": repository},
            }
        )
        self.status = "Registration intake saved."
        return response

    def cancel(self, context: ExtensionContext) -> Mapping[str, object]:
        if self.detail is None:
            raise ValueError("open the registration before cancelling it")
        project_id, activity_id = _selection(context)
        response = context.client.submit(
            {
                "request_id": self._request_id_factory(),
                "operation": "registration.cancel",
                "project_id": project_id,
                "activity_id": activity_id,
                "question_id": None,
                "expected_version": self.detail["activity_version"],
                "payload": {},
            }
        )
        self.status = "Registration cancelled; confirmed history is unchanged."
        return response

    def _pending_matches(
        self,
        project_id: str,
        activity_id: str,
        detail: Mapping[str, object],
    ) -> bool:
        pending = self.pending
        if pending is None:
            return True
        package = detail["package_ref"]
        if not isinstance(package, Mapping):
            return False
        envelope = pending.envelope
        return (
            envelope["request_id"] == pending.request_id
            and pending.project_id == project_id
            and pending.activity_id == activity_id
            and pending.expected_version == detail["activity_version"]
            and dict(pending.package_ref) == dict(package)
        )

    def _pending_block_message(self) -> str:
        assert self.pending is not None
        return (
            "A different registration confirmation request remains unresolved "
            f"({self.pending.request_id}). Use the registration retry action before "
            "confirming this candidate."
        )


class RegistrationExtension:
    def __init__(self, interaction: RegistrationInteraction | None = None) -> None:
        self.interaction = interaction or RegistrationInteraction()

    def install(self, registry: ExtensionRegistry) -> None:
        registry.register_command("register", self._start)
        registry.register_command("registration", self._open)
        registry.register_view("registration", self._view)
        registry.register_action("registration-confirm", self._confirm)
        registry.register_action("registration-retry", self._retry)
        registry.register_action("registration-cancel", self._cancel)

    def _open(self, context: ExtensionContext, arguments: str) -> object:
        if arguments.strip():
            raise ValueError("registration command takes no arguments")
        return self.interaction.open(context)

    def _start(self, context: ExtensionContext, arguments: str) -> object:
        return self.interaction.start(context, arguments)

    def _view(self, _context: ExtensionContext, arguments: str) -> object:
        if arguments.strip():
            raise ValueError("registration view takes no arguments")
        return self.interaction.render()

    def _confirm(self, context: ExtensionContext, arguments: str) -> object:
        return self.interaction.confirm(context, arguments.strip())

    def _retry(self, context: ExtensionContext, arguments: str) -> object:
        if self.interaction.pending is not None:
            if arguments.strip():
                raise ValueError(
                    "confirmation reconciliation retry takes no arguments"
                )
            return self.interaction.retry(context)
        operation_id, separator, intervention = arguments.strip().partition(" ")
        if not separator or not intervention.strip():
            raise ValueError(
                "registration retry requires an operation ID and intervention"
            )
        return self.interaction.retry(
            context, operation_id, intervention.strip()
        )

    def _cancel(self, context: ExtensionContext, arguments: str) -> object:
        if arguments.strip():
            raise ValueError("registration cancel takes no arguments")
        return self.interaction.cancel(context)


def _selection(context: ExtensionContext) -> tuple[str, str]:
    project_id = context.state.selected_project_id
    activity_id = context.state.selected_activity_id
    if not isinstance(project_id, str) or not project_id:
        raise ValueError("select a project before opening registration")
    if not isinstance(activity_id, str) or not activity_id:
        raise ValueError("select a registration activity first")
    return project_id, activity_id


def _registration_detail(response: Mapping[str, object]) -> dict[str, object]:
    if set(response) not in ({"data"}, {"data", "event_cursor"}) or not isinstance(
        response["data"], Mapping
    ):
        raise ValueError("registration response is invalid")
    if "event_cursor" in response and (
        isinstance(response["event_cursor"], bool)
        or not isinstance(response["event_cursor"], int)
        or response["event_cursor"] < 0
    ):
        raise ValueError("registration event_cursor must be nonnegative")
    detail = dict(response["data"])
    fields = {
        "project_id", "activity_id", "activity_version", "state",
        "package_ref", "history", "can_confirm",
    }
    if set(detail) != fields:
        raise ValueError("registration response fields do not match the contract")
    for field in ("project_id", "activity_id", "state"):
        _text(detail[field], field)
    if (
        isinstance(detail["activity_version"], bool)
        or not isinstance(detail["activity_version"], int)
        or detail["activity_version"] < 1
    ):
        raise ValueError("registration activity_version must be positive")
    if not isinstance(detail["can_confirm"], bool):
        raise ValueError("registration can_confirm must be boolean")
    if detail["package_ref"] is not None:
        _package_ref(detail["package_ref"])
    elif detail["can_confirm"]:
        raise ValueError("registration cannot confirm without a package reference")
    history = detail["history"]
    if not isinstance(history, list):
        raise ValueError("registration history must be an array")
    for item in history:
        if not isinstance(item, Mapping) or set(item) != {
            "confirmation_id", "path", "sha256"
        }:
            raise ValueError("registration history reference is invalid")
        _identifier(item["confirmation_id"], "confirmation_id")
        _text(item["path"], "confirmation path")
        _digest(item["sha256"], "confirmation sha256")
    return detail


def _package_ref(value: object) -> Mapping[str, object]:
    fields = {
        "repository", "commit", "registration_version", "candidate_id",
        "manifest_path", "manifest_sha256",
    }
    if not isinstance(value, Mapping) or set(value) != fields:
        raise ValueError("registration package reference is invalid")
    _text(value["repository"], "package repository")
    commit = _text(value["commit"], "package commit")
    if len(commit) != 40 or any(character not in "0123456789abcdef" for character in commit):
        raise ValueError("package commit must be a full lowercase Git object ID")
    if (
        isinstance(value["registration_version"], bool)
        or not isinstance(value["registration_version"], int)
        or value["registration_version"] < 1
    ):
        raise ValueError("package registration_version must be positive")
    _identifier(value["candidate_id"], "candidate_id")
    _text(value["manifest_path"], "manifest_path")
    _digest(value["manifest_sha256"], "manifest_sha256")
    return value


def _receipt(response: Mapping[str, object]) -> Mapping[str, object]:
    receipt = response.get("receipt")
    if not isinstance(receipt, Mapping):
        raise ValueError("confirmation response lacks a receipt")
    request_id = receipt.get("request_id")
    status = receipt.get("status")
    _identifier(request_id, "receipt request_id")
    if status != "completed":
        raise ValueError("confirmation receipt is not completed")
    return receipt


def _identifier(value: object, field: str) -> str:
    text = _text(value, field)
    if any(not (character.isascii() and (character.isalnum() or character in "-_.")) for character in text):
        raise ValueError(f"{field} is invalid")
    return text


def _digest(value: object, field: str) -> str:
    text = _text(value, field)
    if len(text) != 64 or any(character not in "0123456789abcdef" for character in text):
        raise ValueError(f"{field} must be a lowercase SHA-256")
    return text


def _text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be nonempty text")
    return value
