"""Terminal commands and activity actions for project registration.

The service owns every decision; this extension only submits the Owner's
explicit requests. Confirmation and cancellation are activity actions, never
ordinary text, and a lost acknowledgment is reconciled through the saved
request rather than repeated.
"""

from __future__ import annotations

import shlex
import urllib.parse
import uuid
from collections.abc import Callable, Mapping

from .connection import ServiceError, TerminalConnectionError
from .extensions import ExtensionContext, ExtensionRegistry

_USAGE = (
    "usage: /register <owner/repository> <overview-path> [--ref <full ref or commit>] [--branch <publication branch>] "
    "[--scope <milestone,milestone>] [--architect <tool:model>] [--reviewer <tool:model>]"
)


class RegistrationError(ValueError):
    """A plain, user-facing registration command problem."""


class RegistrationExtension:
    """Register /register, /registration and the registration actions on the workspace."""

    def __init__(self, request_id_factory: Callable[[], str] | None = None) -> None:
        self._request_id = request_id_factory or (lambda: f"registration-{uuid.uuid4().hex}")
        self._unconfirmed: dict[tuple[str, str], str] = {}
        self._cancelling: set[str] = set()

    def install(self, registry: ExtensionRegistry) -> None:
        registry.register_command("register", self.register)
        registry.register_command("registration", self.open_registration)
        registry.register_action("decision", self.action)
        registry.register_action("action", self.action)

    # -- commands

    def register(self, context: ExtensionContext, arguments: str) -> Mapping[str, object]:
        payload = _parse(arguments)
        request_id = self._request_id()
        try:
            response = context.client.submit(
                {"request_id": request_id, "operation": "registration.start", "project_id": None, "activity_id": None,
                 "question_id": None, "expected_version": None, "payload": payload}
            )
        except ServiceError as error:
            raise RegistrationError(f"Registration was not started: {error}") from error
        except TerminalConnectionError as error:
            self._unconfirmed[("start", request_id)] = request_id
            raise RegistrationError(f"Outcome not confirmed: {error}. Reconnect and check the project list before trying again.") from error
        receipt = _receipt(response)
        result = receipt.get("result") if isinstance(receipt.get("result"), Mapping) else {}
        state = context.state
        refresh = getattr(state, "refresh", None)
        if callable(refresh):
            refresh()
        project_id, activity_id = receipt.get("project_id"), receipt.get("activity_id")
        if isinstance(project_id, str) and hasattr(state, "select_project"):
            state.select_project(project_id)
            if isinstance(activity_id, str):
                _select(state, activity_id)
        note = "A registration is already in progress for this project; opened it." if result.get("duplicate") else "Registration started."
        _status(state, note)
        return receipt

    def open_registration(self, context: ExtensionContext, arguments: str) -> object:
        state = context.state
        project_id = state.selected_project_id
        if project_id is None:
            raise RegistrationError("Select a project first; /registration opens its registration process.")
        registrations = [a for a in getattr(state, "activities", ()) if getattr(a, "kind", None) == "registration"]
        if not registrations:
            raise RegistrationError("This project has no registration record. Start one with /register.")
        underway = [a for a in registrations if a.state not in {"completed", "cancelled", "failed"}]
        chosen = (underway or registrations)[0]
        _select(state, chosen.activity_id)
        return chosen.activity_id

    # -- actions

    def action(self, context: ExtensionContext, action_id: str) -> object:
        state = context.state
        detail = getattr(state, "activity_detail", None)
        actions = detail.get("available_actions") if isinstance(detail, Mapping) else None
        action = next((a for a in (actions or []) if isinstance(a, Mapping) and a.get("action_id") == action_id), None)
        if action is None:
            raise RegistrationError("That action is no longer available.")
        activity_id = state.selected_activity_id
        project_id = state.selected_project_id
        if activity_id is None or project_id is None:
            raise RegistrationError("Select the registration activity first.")
        if action_id.endswith("-confirm"):
            return self._confirm(context, project_id, activity_id)
        if action_id.endswith("-cancel"):
            return self._begin_cancel(context, activity_id, action_id)
        if action_id.endswith("-cancel-yes"):
            return self._cancel(context, project_id, activity_id)
        if action_id.endswith("-cancel-back"):
            self._cancelling.discard(activity_id)
            _select(state, activity_id)
            _status(state, "Cancellation abandoned; the registration continues.")
            return None
        raise RegistrationError("That action is not part of registration.")

    def _view(self, context: ExtensionContext, activity_id: str) -> Mapping[str, object]:
        response = context.client.get_json(f"/registrations/{urllib.parse.quote(activity_id, safe='')}")
        data = response.get("data")
        if not isinstance(data, Mapping):
            raise RegistrationError("The registration record is unavailable.")
        return data

    def _confirm(self, context: ExtensionContext, project_id: str, activity_id: str) -> object:
        view = self._view(context, activity_id)
        package = view.get("package_ref")
        if not isinstance(package, Mapping):
            raise RegistrationError("There is no candidate ready to confirm; open the current candidate first.")
        key = ("confirm", f"{activity_id}:{package['manifest_sha256']}")
        request_id = self._unconfirmed.get(key) or self._request_id()
        envelope = {"request_id": request_id, "operation": "registration.confirm", "project_id": project_id, "activity_id": activity_id,
                    "question_id": None, "expected_version": view["activity_version"], "payload": {"package_ref": dict(package)}}
        try:
            response = context.client.submit(envelope)
        except ServiceError as error:
            self._unconfirmed.pop(key, None)
            raise RegistrationError(f"Confirmation was not accepted: {error}") from error
        except TerminalConnectionError as error:
            self._unconfirmed[key] = request_id
            raise RegistrationError(f"Outcome not confirmed: {error}. Activating Confirm again reuses the same request and cannot confirm twice.") from error
        self._unconfirmed.pop(key, None)
        _receipt(response)
        _status(context.state, f"Confirmation of candidate {package['candidate_id']} accepted; the receipt is being published to GitHub before registration becomes active.")
        _reload(context.state, activity_id)
        return response

    def _begin_cancel(self, context: ExtensionContext, activity_id: str, action_id: str) -> object:
        view = self._view(context, activity_id)
        state = context.state
        self._cancelling.add(activity_id)
        base = action_id[: -len("-cancel")]
        detail = dict(state.activity_detail or {})
        detail["available_actions"] = [
            {"action_id": f"{base}-cancel-yes", "label": "Cancel registration", "kind": "action"},
            {"action_id": f"{base}-cancel-back", "label": "Go back", "kind": "action"},
        ]
        state.activity_detail = detail
        published = view.get("package_ref")
        _status(
            state,
            f"Cancel registration of {view['repository']} (attempt version {view['registration_version']}, state {view['state']})? "
            "Any running agent is stopped first; saved findings, decisions and any published candidate are kept; the project keeps its earlier "
            "registration status and its active version, and no work restarts." + ("" if published is None else f" Candidate {published['candidate_id']} stays in GitHub."),
        )
        return None

    def _cancel(self, context: ExtensionContext, project_id: str, activity_id: str) -> object:
        view = self._view(context, activity_id)
        key = ("cancel", activity_id)
        request_id = self._unconfirmed.get(key) or self._request_id()
        envelope = {"request_id": request_id, "operation": "registration.cancel", "project_id": project_id, "activity_id": activity_id,
                    "question_id": None, "expected_version": view["activity_version"], "payload": {}}
        try:
            response = context.client.submit(envelope)
        except ServiceError as error:
            self._unconfirmed.pop(key, None)
            raise RegistrationError(f"Cancellation was not accepted: {error}") from error
        except TerminalConnectionError as error:
            self._unconfirmed[key] = request_id
            raise RegistrationError(f"Outcome not confirmed: {error}. Activating Cancel again reuses the same request.") from error
        self._unconfirmed.pop(key, None)
        self._cancelling.discard(activity_id)
        _receipt(response)
        _status(context.state, "Stopping: cancellation accepted; the attempt ends once its work is confirmed stopped.")
        _reload(context.state, activity_id)
        return response


def _parse(arguments: str) -> dict[str, object]:
    try:
        words = shlex.split(arguments)
    except ValueError as error:
        raise RegistrationError(f"{error}. {_USAGE}") from error
    positional: list[str] = []
    options: dict[str, str] = {}
    index = 0
    while index < len(words):
        word = words[index]
        if word.startswith("--"):
            if word not in {"--ref", "--branch", "--scope", "--architect", "--reviewer"} or index + 1 >= len(words):
                raise RegistrationError(f"Unknown or incomplete option {word}. {_USAGE}")
            options[word[2:]] = words[index + 1]
            index += 2
        else:
            positional.append(word)
            index += 1
    if len(positional) != 2:
        raise RegistrationError(_USAGE)
    payload: dict[str, object] = {
        "repository": positional[0], "overview_path": positional[1], "source_ref": options.get("ref"),
        "publication_branch": options.get("branch"), "scope": {"kind": "whole"}, "architect": None, "reviewer": None,
    }
    if "scope" in options:
        payload["scope"] = {"kind": "milestones", "milestones": [m.strip() for m in options["scope"].split(",") if m.strip()]}
    for role in ("architect", "reviewer"):
        if role in options:
            tool, _, model = options[role].partition(":")
            if not tool or not model:
                raise RegistrationError(f"--{role} must be written tool:model. {_USAGE}")
            payload[role] = {"tool": tool, "model": model}
    return payload


def _receipt(response: Mapping[str, object]) -> Mapping[str, object]:
    receipt = response.get("receipt")
    if not isinstance(receipt, Mapping) or receipt.get("status") not in {"accepted", "completed"}:
        raise RegistrationError("The service did not accept the request.")
    return receipt


def _select(state: object, activity_id: str) -> None:
    select = getattr(state, "select_activity", None)
    if callable(select):
        try:
            select(activity_id)
        except ValueError:
            pass


def _reload(state: object, activity_id: str) -> None:
    refresh = getattr(state, "refresh", None)
    if callable(refresh):
        refresh()
    _select(state, activity_id)


def _status(state: object, message: str) -> None:
    setattr(state, "error", message)
