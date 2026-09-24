"""Terminal commands and activity actions for the architecture loop.

`/architecture start` submits one explicit request for the selected project; `/architecture` only opens
the current activity and starts nothing. The service owns every decision. Cancel and retry are activity
actions, and a lost acknowledgment is reconciled through the saved request rather than repeated.
"""

from __future__ import annotations

import shlex
import urllib.parse
import uuid
from collections.abc import Callable, Mapping

from .connection import ServiceError, TerminalConnectionError
from .extensions import ExtensionContext, ExtensionRegistry

_USAGE = "usage: /architecture [start [--architect <tool:model>] [--reviewer <tool:model>] | retry <what you changed> | full]"


class ArchitectureError(ValueError):
    """A plain, user-facing architecture command problem."""


class ArchitectureExtension:
    """Register /architecture and handle the architecture activity's actions."""

    def __init__(self, request_id_factory: Callable[[], str] | None = None) -> None:
        self._request_id = request_id_factory or (lambda: f"architecture-{uuid.uuid4().hex}")
        self._unconfirmed: dict[tuple[str, str], str] = {}
        self._cancelling: set[str] = set()

    def install(self, registry: ExtensionRegistry) -> None:
        registry.register_command("architecture", self.command)

    # -- commands

    def command(self, context: ExtensionContext, arguments: str) -> object:
        try:
            words = shlex.split(arguments)
        except ValueError as error:
            raise ArchitectureError(f"{error}. {_USAGE}") from error
        if not words:
            return self._open(context)
        if words[0] == "start":
            return self._start(context, words[1:])
        if words[0] == "retry":
            return self._retry(context, " ".join(words[1:]).strip())
        if words[0] == "full":
            return self._full(context)
        raise ArchitectureError(_USAGE)

    def _open(self, context: ExtensionContext) -> object:
        state = context.state
        project_id = state.selected_project_id
        if project_id is None:
            raise ArchitectureError("Select a project first; /architecture opens its architecture activity.")
        response = context.client.get_json(f"/projects/{urllib.parse.quote(project_id, safe='')}/architecture")
        data = response.get("data")
        if not isinstance(data, Mapping):
            raise ArchitectureError("This project has no architecture activity. Start one with /architecture start; opening does not start anything.")
        _reload(state, str(data["activity_id"]))
        _status(state, _summary(data))
        return data["activity_id"]

    def _start(self, context: ExtensionContext, words: list[str]) -> object:
        state = context.state
        project_id = state.selected_project_id
        if project_id is None:
            raise ArchitectureError("Select a project first; /architecture start starts the loop for the selected project.")
        options: dict[str, str] = {}
        index = 0
        while index < len(words):
            if words[index] not in {"--architect", "--reviewer"} or index + 1 >= len(words):
                raise ArchitectureError(f"Unknown or incomplete option {words[index]}. {_USAGE}")
            options[words[index][2:]] = words[index + 1]
            index += 2
        registrations = [a for a in getattr(state, "activities", ()) if getattr(a, "kind", None) == "registration"]
        if not registrations:
            raise ArchitectureError("This project has no confirmed registration. Register and confirm it first; confirmation alone starts nothing.")
        view = None
        for activity in registrations:
            data = context.client.get_json(f"/registrations/{urllib.parse.quote(activity.activity_id, safe='')}").get("data")
            if isinstance(data, Mapping) and isinstance(data.get("active_package_ref"), Mapping):
                view = data
                break
        if view is None:
            raise ArchitectureError("This project has no confirmed registration. Register and confirm it first; confirmation alone starts nothing.")
        selections = {}
        for role in ("architect", "reviewer"):
            if role in options:
                tool, _, model = options[role].partition(":")
                if not tool or not model:
                    raise ArchitectureError(f"--{role} must be written tool:model. {_USAGE}")
            else:
                chosen = (view.get("roles") or {}).get(role) or {}
                tool, model = chosen.get("tool"), chosen.get("model")
                if not tool or not model:
                    raise ArchitectureError(f"Say which {role} to use: --{role} <tool:model>.")
            selections[role] = {"tool": tool, "model_id": model}
        payload = {"registration_ref": dict(view["active_package_ref"]), **selections}
        request_id = self._unconfirmed.get(("start", project_id)) or self._request_id()
        try:
            response = context.client.submit({"request_id": request_id, "operation": "architecture.start", "project_id": project_id, "activity_id": None,
                                              "question_id": None, "expected_version": None, "payload": payload})
        except ServiceError as error:
            self._unconfirmed.pop(("start", project_id), None)
            raise ArchitectureError(f"The architecture loop was not started: {error}") from error
        except TerminalConnectionError as error:
            self._unconfirmed[("start", project_id)] = request_id
            raise ArchitectureError(f"Outcome not confirmed: {error}. Starting again reuses the same request and cannot start twice.") from error
        self._unconfirmed.pop(("start", project_id), None)
        receipt = _receipt(response)
        result = receipt.get("result") if isinstance(receipt.get("result"), Mapping) else {}
        _reload(state, str(receipt.get("activity_id")))
        picked = f"architect {selections['architect']['tool']}:{selections['architect']['model_id']}, reviewer {selections['reviewer']['tool']}:{selections['reviewer']['model_id']}"
        _status(state, ("An architecture activity is already unfinished for this project; opened it." if result.get("duplicate") else f"Architecture started with {picked}."))
        return receipt

    def _retry(self, context: ExtensionContext, intervention: str) -> object:
        state = context.state
        activity_id, project_id = state.selected_activity_id, state.selected_project_id
        if activity_id is None or project_id is None:
            raise ArchitectureError("Select the architecture activity first.")
        if not intervention:
            raise ArchitectureError("Say what you changed: /architecture retry <what you changed>.")
        view = self._view(context, project_id)
        paused = view.get("paused")
        if not isinstance(paused, Mapping):
            raise ArchitectureError("This architecture activity is not paused by a technical failure; there is nothing to retry.")
        agent = paused["kind"] == "agent"
        payload = {"target": "agent" if agent else "publication", "operation_id": None if agent else paused["operation_id"],
                   "assignment_id": paused["assignment_id"] if agent else None, "intervention": intervention}
        response = self._submit(context, ("retry", f"{activity_id}:{paused.get('failed_run_id') or paused.get('operation_id')}:{intervention}"),
                                {"operation": "architecture.retry", "project_id": project_id, "activity_id": activity_id, "question_id": None,
                                 "expected_version": view["activity_version"], "payload": payload}, "Retry was not accepted")
        _status(state, "Retry accepted; it resumes from the last verified step.")
        _reload(state, activity_id)
        return response

    # -- actions

    def action(self, context: ExtensionContext, action_id: str) -> object:
        state = context.state
        activity_id, project_id = state.selected_activity_id, state.selected_project_id
        if activity_id is None or project_id is None:
            raise ArchitectureError("Select the architecture activity first.")
        if action_id.endswith("-retry"):
            view = self._view(context, project_id)
            what = "publication" if (view.get("paused") or {}).get("kind") == "publication" else "agent run"
            _status(state, f"Retry the {what}: first fix what stopped it, then run /architecture retry <what you changed>. The automatic recovery budget stays unchanged.")
            return None
        if action_id.endswith("-confirm"):
            return self._begin_confirm(context, project_id, activity_id, action_id)
        if action_id.endswith("-confirm-yes"):
            return self._confirm(context, project_id, activity_id)
        if action_id.endswith("-confirm-back"):
            _reload(state, activity_id)
            _status(state, "Confirmation not sent; the reviewed breakdown still waits for you.")
            return None
        if action_id.endswith("-grant") or action_id.endswith("-remain"):
            return self._limit_decision(context, project_id, activity_id, "grant_one" if action_id.endswith("-grant") else "remain_paused")
        if action_id.endswith("-cancel"):
            return self._begin_cancel(context, project_id, activity_id, action_id)
        if action_id.endswith("-cancel-yes"):
            return self._cancel(context, project_id, activity_id)
        if action_id.endswith("-cancel-back"):
            self._cancelling.discard(activity_id)
            _reload(state, activity_id)
            _status(state, "Cancellation abandoned; the architecture activity continues.")
            return None
        raise ArchitectureError("That action is not part of the architecture loop.")

    def _full(self, context: ExtensionContext) -> object:
        project_id = context.state.selected_project_id
        if project_id is None:
            raise ArchitectureError("Select a project first; /architecture full lists the saved records.")
        view = self._view(context, project_id)
        lines = [f"Saved records of architecture version {(view.get('working_ref') or {}).get('version')} in {view['repository']} (branch {view['publication_branch']}):"]
        lines += [f"{r['kind']} {r['id']} v{r['version']} {r['path']} sha256 {str(r['sha256'])[:12]} commit {str(r['commit'])[:12]}" for r in view.get("records") or []]
        for review in view.get("reviews") or []:
            record = review.get("record") or {}
            lines.append(f"review round {review['round']}: {review['outcome']}, {len(review['findings'])} finding(s) {record.get('path', '')}")
        _status(context.state, "\n".join(lines))
        return None

    def _begin_confirm(self, context: ExtensionContext, project_id: str, activity_id: str, action_id: str) -> object:
        view = self._view(context, project_id)
        state = context.state
        if view.get("state") != "waiting_for_confirmation" or not isinstance(view.get("working_ref"), Mapping):
            raise ArchitectureError("The breakdown is not reviewed and waiting for confirmation.")
        ref = view["working_ref"]
        base = action_id[: -len("-confirm")]
        detail = dict(state.activity_detail or {})
        detail["available_actions"] = [
            {"action_id": f"{base}-confirm-yes", "label": f"Confirm exactly version {ref['version']}", "kind": "decision"},
            {"action_id": f"{base}-confirm-back", "label": "Go back", "kind": "action"},
        ]
        state.activity_detail = detail
        breakdown = view.get("breakdown") or {}
        packets = breakdown.get("packets") or []
        milestones = breakdown.get("milestones") or []
        coverage = view.get("coverage") or {}
        dependencies = sum(len(p.get("depends_on") or []) for p in packets)
        parallel = [p["id"] for p in packets if p.get("parallel_with")]
        limitations = view.get("limitations") or []
        text = (f"Confirm architecture version {ref['version']} of {view['repository']} (commit {str(ref['commit'])[:12]}, manifest {str(ref['manifest_sha256'])[:12]}, content {str(ref['reviewed_content_hash'])[:12]})? "
                f"Independent review passed (round {view['review_count']} of {view['review_limit']}, coverage valid). "
                f"{len(milestones)} milestones and {len(packets)} packets cover {len([o for o, m in coverage.items() if m])} of {len(coverage)} confirmed outcomes; {dependencies} packet dependencies; "
                f"parallel opportunities: {', '.join(parallel) if parallel else 'none'}. "
                + ("Limitations you accept: " + "; ".join(f"{item['subject']} — {item['explanation']}" for item in limitations) + ". " if limitations else "No limitations need acceptance. ")
                + "Confirming saves only this exact version and does not start Execution. /architecture full lists every saved record.")
        _status(state, text)
        return None

    def _confirm(self, context: ExtensionContext, project_id: str, activity_id: str) -> object:
        view = self._view(context, project_id)
        ref = view.get("working_ref")
        if view.get("state") != "waiting_for_confirmation" or not isinstance(ref, Mapping):
            raise ArchitectureError("The breakdown is not reviewed and waiting for confirmation.")
        payload = {"expected_working_ref": dict(ref), "accepted_limitations": [{k: item[k] for k in ("id", "subject", "version", "container")} for item in view.get("limitations") or []]}
        response = self._submit(context, ("confirm", f"{activity_id}:{ref['manifest_sha256']}"),
                                {"operation": "architecture.confirm", "project_id": project_id, "activity_id": activity_id, "question_id": None,
                                 "expected_version": view["activity_version"], "payload": payload}, "Confirmation was not accepted")
        _status(context.state, f"Confirmation of version {ref['version']} accepted; the receipt is being published to GitHub before the loop completes. Execution is not started.")
        _reload(context.state, activity_id)
        return response

    def _limit_decision(self, context: ExtensionContext, project_id: str, activity_id: str, choice: str) -> object:
        view = self._view(context, project_id)
        decisions = view.get("owner_decisions") or []
        if not decisions:
            raise ArchitectureError("No review-limit decision is pending.")
        assignment_id = decisions[0]["assignment_id"]
        response = self._submit(context, ("decision", f"{activity_id}:{assignment_id}:{choice}"),
                                {"operation": "owner.decision", "project_id": project_id, "activity_id": activity_id, "question_id": None, "expected_version": view["activity_version"],
                                 "payload": {"target": "fidelity_review", "choice": choice, "assignment_id": assignment_id}}, "The decision was not accepted")
        _status(context.state, "One extra review attempt granted; the architect amends first." if choice == "grant_one" else "The architecture stays paused; nothing was approved.")
        _reload(context.state, activity_id)
        return response

    def _view(self, context: ExtensionContext, project_id: str) -> Mapping[str, object]:
        data = context.client.get_json(f"/projects/{urllib.parse.quote(project_id, safe='')}/architecture").get("data")
        if not isinstance(data, Mapping):
            raise ArchitectureError("The architecture activity is unavailable.")
        return data

    def _submit(self, context: ExtensionContext, key: tuple[str, str], envelope: dict[str, object], refused: str) -> object:
        request_id = self._unconfirmed.get(key) or self._request_id()
        try:
            response = context.client.submit({"request_id": request_id, **envelope})
        except ServiceError as error:
            self._unconfirmed.pop(key, None)
            raise ArchitectureError(f"{refused}: {error}") from error
        except TerminalConnectionError as error:
            self._unconfirmed[key] = request_id
            raise ArchitectureError(f"Outcome not confirmed: {error}. Doing it again reuses the same request and cannot happen twice.") from error
        self._unconfirmed.pop(key, None)
        _receipt(response)
        return response

    def _begin_cancel(self, context: ExtensionContext, project_id: str, activity_id: str, action_id: str) -> object:
        view = self._view(context, project_id)
        state = context.state
        self._cancelling.add(activity_id)
        base = action_id[: -len("-cancel")]
        detail = dict(state.activity_detail or {})
        detail["available_actions"] = [
            {"action_id": f"{base}-cancel-yes", "label": "Cancel architecture", "kind": "action"},
            {"action_id": f"{base}-cancel-back", "label": "Go back", "kind": "action"},
        ]
        state.activity_detail = detail
        _status(state, f"Cancel the architecture activity for {view['repository']} (state {view['stage']})? Any running agent is stopped first; saved findings, decisions and published foundations are kept; the project's registration is untouched and nothing restarts.")
        return None

    def _cancel(self, context: ExtensionContext, project_id: str, activity_id: str) -> object:
        view = self._view(context, project_id)
        response = self._submit(context, ("cancel", activity_id), {"operation": "architecture.cancel", "project_id": project_id, "activity_id": activity_id, "question_id": None,
                                "expected_version": view["activity_version"], "payload": {"reason": "cancelled by the Owner from the terminal"}}, "Cancellation was not accepted")
        self._cancelling.discard(activity_id)
        _status(context.state, "Stopping: cancellation accepted; the activity ends once its work is confirmed stopped.")
        _reload(context.state, activity_id)
        return response


def _summary(view: Mapping[str, object]) -> str:
    text = f"Architecture {view['stage']} — source {view['repository']} at {str(view['source']['commit'])[:12]}."  # type: ignore[index]
    foundations = view.get("foundations")
    if isinstance(foundations, Mapping):
        text += f" Foundations saved: version {foundations['version']} at {str(foundations['commit'])[:12]}."
    breakdown = view.get("breakdown")
    if isinstance(breakdown, Mapping):
        packets = breakdown.get("packets") or []
        parallel = sum(1 for p in packets if p.get("parallel_with"))
        text += f" Work breakdown saved: {len(breakdown.get('milestones') or [])} milestones, {len(packets)} packets ({parallel} with parallel opportunities)."
    if view.get("review_count"):
        text += f" Independent review: {view['review_count']} of {view['review_limit']} rounds used" + ("; coverage valid for the working version." if view.get("review_coverage_valid") else ".")
    confirmed = view.get("confirmed_ref")
    if isinstance(confirmed, Mapping):
        text += f" Confirmed: version {confirmed['version']} at {str(confirmed['commit'])[:12]}. Execution has not been started."
    elif view.get("state") == "waiting_for_confirmation":
        text += " Waiting for your confirmation of the exact reviewed version."
    reasons = view.get("blocking_reasons")
    if isinstance(reasons, list) and reasons:
        text += " " + " ".join(str(r) for r in reasons)
    return text


def _receipt(response: Mapping[str, object]) -> Mapping[str, object]:
    receipt = response.get("receipt")
    if not isinstance(receipt, Mapping) or receipt.get("status") not in {"accepted", "completed"}:
        raise ArchitectureError("The service did not accept the request.")
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
