"""Terminal commands and activity actions for Execution.

`/execution start` submits one explicit request for the selected project's confirmed breakdown; `/execution`
only opens the current activity and starts nothing. The service owns every decision: this module shows what
it saved (plans, reservations, revisions, review counts, measurements) and sends the Owner's typed choices.
"""

from __future__ import annotations

import shlex
import urllib.parse
import uuid
from collections.abc import Callable, Mapping

from .connection import ServiceError, TerminalConnectionError
from .extensions import ExtensionContext, ExtensionRegistry

_USAGE = "usage: /execution [start [--manager <route>] | full]"


class ExecutionError(ValueError):
    """A plain, user-facing Execution command problem."""


class ExecutionExtension:
    """Register /execution and handle the Execution activity's actions."""

    def __init__(self, request_id_factory: Callable[[], str] | None = None) -> None:
        self._request_id = request_id_factory or (lambda: f"execution-{uuid.uuid4().hex}")
        self._unconfirmed: dict[tuple[str, str], str] = {}

    def install(self, registry: ExtensionRegistry) -> None:
        registry.register_command("execution", self.command)

    def command(self, context: ExtensionContext, arguments: str) -> object:
        try:
            words = shlex.split(arguments)
        except ValueError as error:
            raise ExecutionError(f"{error}. {_USAGE}") from error
        if not words:
            return self._open(context, full=False)
        if words[0] == "start":
            return self._start(context, words[1:])
        if words[0] == "full":
            return self._open(context, full=True)
        raise ExecutionError(_USAGE)

    def _project(self, context: ExtensionContext, what: str) -> str:
        project_id = context.state.selected_project_id
        if project_id is None:
            raise ExecutionError(f"Select a project first; {what}")
        return project_id

    def _load(self, context: ExtensionContext, project_id: str) -> Mapping[str, object]:
        return context.client.get_json(f"/projects/{urllib.parse.quote(project_id, safe='')}/execution")

    def _open(self, context: ExtensionContext, *, full: bool) -> object:
        project_id = self._project(context, "/execution opens its Execution activity.")
        response = self._load(context, project_id)
        data = response.get("data")
        if not isinstance(data, Mapping):
            raise ExecutionError("This project has no Execution activity. Start one with /execution start; opening does not start anything.")
        _reload(context.state, str(data["activity_id"]))
        _status(context.state, render(data, full=full))
        return data["activity_id"]

    def _start(self, context: ExtensionContext, words: list[str]) -> object:
        state = context.state
        project_id = self._project(context, "/execution start starts Execution for the selected project.")
        route = None
        if words:
            if words[0] != "--manager" or len(words) != 2:
                raise ExecutionError(f"Unknown or incomplete option. {_USAGE}")
            route = words[1]
        architecture = context.client.get_json(f"/projects/{urllib.parse.quote(project_id, safe='')}/architecture").get("data")
        confirmed = architecture.get("confirmed_ref") if isinstance(architecture, Mapping) else None
        if not isinstance(confirmed, Mapping):
            raise ExecutionError("This project has no confirmed breakdown. Confirm one in the architecture loop first; confirmation alone starts nothing.")
        configuration = self._load(context, project_id).get("configuration")
        routes = [r["route_id"] for r in (configuration or {}).get("manager_routes", [])] if isinstance(configuration, Mapping) else []
        if isinstance(configuration, Mapping) and configuration.get("valid") is False:
            raise ExecutionError(f"Execution is not configured: {configuration.get('error')}")
        if route is None:
            if len(routes) != 1:
                raise ExecutionError("Say which Development Manager route to use: /execution start --manager <route>. Configured: " + (", ".join(routes) or "none") + ".")
            route = routes[0]
        request_id = self._unconfirmed.get(("start", project_id)) or self._request_id()
        try:
            response = context.client.submit({"request_id": request_id, "operation": "execution.start", "project_id": project_id, "activity_id": None, "question_id": None,
                                              "expected_version": None, "payload": {"confirmed_ref": dict(confirmed), "manager_route_id": route}})
        except ServiceError as error:
            self._unconfirmed.pop(("start", project_id), None)
            raise ExecutionError(f"Execution was not started: {error}") from error
        except TerminalConnectionError as error:
            self._unconfirmed[("start", project_id)] = request_id
            raise ExecutionError(f"Outcome not confirmed: {error}. Starting again reuses the same request and cannot start twice.") from error
        self._unconfirmed.pop(("start", project_id), None)
        receipt = _receipt(response)
        result = receipt.get("result") if isinstance(receipt.get("result"), Mapping) else {}
        _reload(state, str(receipt.get("activity_id")))
        _status(state, "An Execution activity is already unfinished for this project; opened it." if result.get("duplicate")
                else f"Execution started with Development Manager route {route}: {result.get('packets')} packets, code baseline {str(result.get('source_commit'))[:12]}, product master observed at {str(result.get('product_master_start_commit'))[:12]}.")
        return receipt

    def action(self, context: ExtensionContext, action_id: str) -> object:
        state = context.state
        activity_id, project_id = state.selected_activity_id, state.selected_project_id
        if activity_id is None or project_id is None:
            raise ExecutionError("Select the Execution activity first.")
        if action_id.endswith("-grant") or action_id.endswith("-remain"):
            return self._decision(context, project_id, activity_id, "grant_one" if action_id.endswith("-grant") else "remain_paused")
        raise ExecutionError("That action is not part of Execution.")

    def _decision(self, context: ExtensionContext, project_id: str, activity_id: str, choice: str) -> object:
        data = self._load(context, project_id).get("data")
        decisions = (data or {}).get("owner_decisions") if isinstance(data, Mapping) else None
        if not decisions:
            raise ExecutionError("No review-limit decision is pending.")
        target = decisions[0]
        key = ("decision", f"{activity_id}:{target['assignment_id']}:{choice}")
        request_id = self._unconfirmed.get(key) or self._request_id()
        try:
            response = context.client.submit({"request_id": request_id, "operation": "owner.decision", "project_id": project_id, "activity_id": activity_id, "question_id": None,
                                              "expected_version": data["version"], "payload": {"target": "packet_review", "choice": choice, "assignment_id": target["assignment_id"]}})
        except ServiceError as error:
            self._unconfirmed.pop(key, None)
            raise ExecutionError(f"The decision was not accepted: {error}") from error
        except TerminalConnectionError as error:
            self._unconfirmed[key] = request_id
            raise ExecutionError(f"Outcome not confirmed: {error}. Doing it again reuses the same request and cannot happen twice.") from error
        self._unconfirmed.pop(key, None)
        _receipt(response)
        _status(context.state, f"One extra review attempt granted for {target['packet_key']}; approval is not forced." if choice == "grant_one" else f"{target['packet_key']} stays paused; nothing was approved.")
        _reload(context.state, activity_id)
        return response


def render(view: Mapping[str, object], *, full: bool) -> str:
    lines = [f"Execution {view['state']}: {view.get('waiting') or ''}".rstrip(": ")]
    manager = view["manager"]  # type: ignore[index]
    lines.append(f"Development Manager {manager['tool']} {manager['model']} (route {manager['route_id']}), {manager['passes']} planning pass(es)" + (", planning now" if manager["planning"] else "") + ".")
    if manager.get("understanding"):
        lines.append(f"Understanding: {str(manager['understanding'])[:400]}")
    base = view["source_commit"]
    lines.append(f"Code baseline {str(base)[:12]}; product {view['product_master']['branch']} at {str(view['product_master']['start_commit'])[:12]} when started.")  # type: ignore[index]
    for packet in view["packets"]:  # type: ignore[union-attr]
        head = packet["state"]
        parts = [f"{packet['key']} [{head}] {packet['subject']}"]
        if packet.get("route"):
            parts.append(f"coder {packet['tool']} {packet['model']} (route {packet['route']})")
        if packet.get("head_commit"):
            parts.append(f"revision {str(packet['head_commit'])[:12]} on {packet['branch']}" + (" (verified on the remote)" if packet["remote_verified"] else ""))
        if packet["review"]["completed"] or packet["reviews"]:
            parts.append(f"review {packet['review']['completed']} of {packet['review']['limit']}: " + ", ".join(f"round {r['round']} {r['outcome']} ({r['blocking']} blocking)" for r in packet["reviews"]))
        if packet.get("note"):
            parts.append(str(packet["note"]))
        lines.append("  " + " | ".join(parts))
        if full:
            if packet.get("reason"):
                lines.append(f"      why this route: {packet['reason']}")
            plan = packet.get("plan")
            if plan:
                lines.append("      plan: " + "; ".join(plan["intended_changes"])[:300])
                lines.append("      connections: " + "; ".join(plan["connections"])[:300])
            if packet.get("changed_paths"):
                lines.append("      changed: " + ", ".join(packet["changed_paths"]))
            for review in packet["reviews"]:
                lines.append(f"      review {review['round']} by {review['reviewer']}: {review['summary'][:240]}")
                for finding in review["findings"]:
                    lines.append(f"        {finding['severity']}: {finding['subject']} — {finding['requested_correction'][:200]}")
            lines.append(f"      active time: coder {packet['active_seconds']['coder']}s, reviewer {packet['active_seconds']['reviewer']}s")
    if view.get("open_questions"):
        lines.append("Waiting for your answer to: " + ", ".join(view["open_questions"]))  # type: ignore[arg-type]
    measured = view["measurements"]  # type: ignore[index]
    lines.append(f"Measured: {measured['active_agent_seconds']}s of agent time; tokens, cost and context: {measured['tokens']}.")
    if full:
        for plan in view.get("plans", []):  # type: ignore[union-attr]
            lines.append(f"planning pass {plan['pass']}: reserved {[a['packet_key'] for a in plan['accepted']]}; rejected {[(r['packet_key'], r['reason']) for r in plan['rejected']]}")
        if manager.get("blockers"):
            lines.append("blockers: " + "; ".join(f"{b['packet_key']}: {b['reason']}" for b in manager["blockers"]))
    return "\n".join(lines)


def _receipt(response: Mapping[str, object]) -> Mapping[str, object]:
    receipt = response.get("receipt")
    if not isinstance(receipt, Mapping) or receipt.get("status") not in {"accepted", "completed"}:
        raise ExecutionError("The service did not accept the request.")
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
