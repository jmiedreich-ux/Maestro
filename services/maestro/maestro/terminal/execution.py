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
                                              "expected_version": data["version"], "payload": {"target": target.get("target", "packet_review"), "choice": choice, "assignment_id": target["assignment_id"]}})
        except ServiceError as error:
            self._unconfirmed.pop(key, None)
            raise ExecutionError(f"The decision was not accepted: {error}") from error
        except TerminalConnectionError as error:
            self._unconfirmed[key] = request_id
            raise ExecutionError(f"Outcome not confirmed: {error}. Doing it again reuses the same request and cannot happen twice.") from error
        self._unconfirmed.pop(key, None)
        _receipt(response)
        what = "fidelity review" if target.get("target") == "execution_support_fidelity_review" else "review attempt"
        _status(context.state, f"One extra {what} granted for {target['packet_key']}; nothing is approved or activated by the grant." if choice == "grant_one" else f"{target['packet_key']} stays paused; nothing was approved.")
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
    integration = view.get("integration")
    if isinstance(integration, Mapping):
        lines.extend(_render_integration(integration, full=full))
    lines.extend(_render_support(view, full=full))
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


_TARGETS = {"packet_review": "packet review", "integration_review": "integration review", "execution_support_fidelity_review": "support fidelity review"}


def _render_support(view: Mapping[str, object], *, full: bool) -> list[str]:
    lines: list[str] = []
    for a in view.get("support", []) or []:  # type: ignore[union-attr]
        parts = [f"support {a['support_id']} [{a['state']}] for {a['packet_key']}"]
        if a.get("disposition"):
            parts.append(f"{a['disposition'].replace('_', ' ')}" + (f": {a['role_path']}" if a.get("role_path") else ""))
        if a["reviews"]["completed"]:
            parts.append(f"fidelity review {a['reviews']['completed']} of {a['reviews']['limit']}: " + ", ".join(f"round {r['round']} {r['outcome']} ({r['blocking']} blocking)" for r in a["review_results"]))
        if a.get("note"):
            parts.append(str(a["note"]))
        lines.append("  " + " | ".join(parts))
        if full:
            lines.append(f"      why: {str(a.get('reason'))[:240]}")
            routes = a.get("routes") or {}
            for name in ("architect", "reviewer"):
                if routes.get(name):
                    lines.append(f"      {name}: {routes[name]['tool']} {routes[name]['model']}")
            for switch in routes.get("switches", []):
                lines.append(f"      route switch: {switch['role']} moved to {switch['switched_to']} because {switch['reason']}")
    for d in view.get("owner_decisions", []) or []:  # type: ignore[union-attr]
        if d.get("recommendation"):
            lines.append(f"Decision pending, {_TARGETS.get(d['target'], d['target'])} for {d['packet_key']}: the architect recommends {d['recommendation']}" + (f" ({str(d['rationale'])[:300]})" if d.get("rationale") else "") + ". Grant one extra attempt or keep it paused.")
    return lines


def _render_integration(integration: Mapping[str, object], *, full: bool) -> list[str]:
    lines: list[str] = []
    for m in integration.get("milestones", []):  # type: ignore[union-attr]
        if m["branch"]:
            lines.append(f"Milestone {m['key']}: branch {m['branch']} at {str(m['head_commit'])[:12]} (from baseline {str(m['base_commit'])[:12]})" + (f"; depends on {', '.join(m['dependencies'])}" if m["dependencies"] else ""))
    for e in integration.get("queue", []):  # type: ignore[union-attr]
        what = e["packet_key"] if e["kind"] == "packet" else f"import {e['delivery_id']}"
        parts = [f"queue {e['entry_id']} [{e['state']}] {what} -> milestone {e['milestone']}"]
        if e.get("integration_head"):
            parts.append(f"integration {str(e['integration_head'])[:12]} on {e['branch']}" + (" (code changed)" if e.get("code_changed") else " (clean merge, no code change)" if e.get("code_changed") is False else ""))
        if e.get("conflicts"):
            parts.append("conflicts: " + ", ".join(e["conflicts"]))
        if e.get("merged_commit"):
            parts.append(f"merged into the milestone at {str(e['merged_commit'])[:12]}")
        if e["reviews"]:
            parts.append(f"integration review {e['review']['completed']} of {e['review']['limit']}: " + ", ".join(f"round {r['round']} {r['outcome']} ({r['blocking']} blocking)" for r in e["reviews"]))
        if e.get("note"):
            parts.append(str(e["note"]))
        lines.append("  " + " | ".join(parts))
        if full and e.get("manager"):
            lines.append(f"      integration manager: {e['manager']['tool']} {e['manager']['model']}; source {str(e['source_commit'])[:12]}, target before {str(e['target_before'])[:12]}")
    for d in integration.get("deliveries", []):  # type: ignore[union-attr]
        lines.append(f"  dependency {d['delivery_id']} [{d['state']}] {', '.join(d['packets'])} from {d['provider']} to {d['consumer']} at {str(d['source_commit'])[:12]}"
                     + (f", imported as {str(d['import_commit'])[:12]}" if d.get("import_commit") else "") + (f" | {d['note']}" if d.get("note") else ""))
    return lines


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
