"""Storage-free registration publication, confirmation, and history controls."""

from __future__ import annotations

import json
import shlex
import urllib.parse
import uuid
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime, timezone

from .connection import ServiceError, TerminalConnectionError
from .extensions import ActionInput, ExtensionContext, ExtensionRegistry, InputSubmission


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
        self.cancel_confirmation = False

    def open(self, context: ExtensionContext) -> str:
        project_id = _selected_project(context)
        response = context.client.get_json(
            f"/projects/{urllib.parse.quote(project_id, safe='')}/registration"
        )
        detail = _registration_detail(response)
        if detail["project_id"] != project_id:
            raise ValueError("registration detail differs from the selected project")
        activity_id = str(detail["activity_id"])
        context.state.select_activity(activity_id)
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
        comparison = detail["comparison"]
        if isinstance(comparison, Mapping):
            active = comparison["active_package_ref"]
            candidate = comparison["candidate_package_ref"]
            assert isinstance(active, Mapping) and isinstance(candidate, Mapping)
            lines.append(
                "Update comparison: active "
                f"{active['candidate_id']} -> candidate {candidate['candidate_id']}"
            )
            for difference in comparison["differences"]:
                assert isinstance(difference, Mapping)
                reasons = ", ".join(str(item) for item in difference["reason_refs"])
                lines.append(
                    f"- {difference['kind']}: {difference['subject']} "
                    f"({difference['previous_version']} -> "
                    f"{difference['candidate_version']}); reasons: {reasons}"
                )
        agent_retry = detail["agent_retry"]
        if isinstance(agent_retry, Mapping):
            lines.append(
                "Agent retry: assignment "
                f"{agent_retry['assignment_id']} / failed run "
                f"{agent_retry['failed_run_id']} / automatic "
                f"{agent_retry['automatic_consumed']} of "
                f"{agent_retry['automatic_limit']} / manual "
                f"{agent_retry['manual_consumed']}"
            )
        assessment = detail.get("assessment")
        if isinstance(assessment, Mapping):
            worker = assessment["working_agent"] or "none"
            lines.append(
                f"Assessment: {assessment['current_step']} / working agent {worker} / "
                f"review {assessment['review_round']} of {assessment['effective_review_limit']} "
                f"(base {assessment['base_review_limit']}, grants {assessment['review_grants']})"
            )
            findings = [
                *assessment["architect_findings"], *assessment["review_findings"]
            ]
            for finding in findings:
                if isinstance(finding, Mapping):
                    lines.append(
                        f"- {finding.get('severity', 'finding')}: "
                        f"{finding.get('subject', 'Untitled finding')}"
                    )
                    for field in (
                        "local_key", "explanation", "impact",
                        "requested_correction", "missing_information",
                        "source_refs", "affected_items",
                    ):
                        if finding.get(field) not in (None, [], ""):
                            lines.append(
                                f"  {field.replace('_', ' ').title()}: "
                                f"{_display_value(finding[field])}"
                            )
        provenance = detail.get("provenance")
        if isinstance(provenance, Mapping):
            lines.append(
                f"Source: {provenance['source_repository']} "
                f"{provenance['source_ref']} at {provenance['source_commit']} "
                f"({provenance['source_selection']})"
            )
            lines.append(
                f"Destination: {provenance['publication_branch']} / "
                f"{provenance['destination_snapshot_reference']}"
            )
        manifest = detail.get("package_manifest")
        if isinstance(manifest, Mapping):
            lines.append(f"Package manifest: {_display_value(manifest)}")
        records = detail.get("package_records", [])
        if isinstance(records, list) and records:
            lines.append(f"Authoritative package records: {len(records)}")
            for record in records:
                if isinstance(record, Mapping):
                    lines.append(
                        f"- {record.get('record_type')}: {record.get('subject')} "
                        f"({record.get('record_id')} v{record.get('record_version')})"
                    )
                    lines.append(f"  Path: {record.get('path')}")
                    lines.append(
                        f"  Data: {_display_value(record.get('data'))}"
                    )
        consistency = detail.get("source_consistency")
        if isinstance(consistency, Mapping):
            lines.append(f"Source consistency: {consistency['state']}")
            for path in consistency.get("changed_paths", []):
                lines.append(f"- changed planning input: {path}")
        for decision in detail.get("owner_decisions", []):
            if isinstance(decision, Mapping) and decision.get("state") == "pending":
                lines.append(
                    f"Owner decision: {decision['reason']} "
                    f"(used {decision['used_attempts']}, base {decision['base_limit']}, "
                    f"prior grants {decision['prior_grants']})"
                )
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
        if self.cancel_confirmation:
            lines.extend((
                "Cancel registration?",
                f"Project: {detail['project_id']} / attempt: {detail['activity_id']}",
                "Effect: stop the active registration attempt. Confirmed history, "
                "saved findings, and published evidence remain retained.",
                "Choose Cancel registration or Go back.",
            ))
        if self.status:
            lines.append(self.status)
        return "\n".join(lines)

    def confirm(self, context: ExtensionContext, candidate_id: str) -> Mapping[str, object]:
        if self.detail is None:
            raise ValueError("open the registration before confirming it")
        detail = self.detail
        project_id, activity_id = self._detail_selection(context)
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
            project_id, activity_id = self._detail_selection(context)
            payload: dict[str, object]
            if publication_operation_id == "agent":
                failure = self.detail["agent_retry"]
                if not isinstance(failure, Mapping):
                    raise ValueError("registration has no displayed agent failure")
                payload = {
                    "assignment_id": failure["assignment_id"],
                    "failed_run_id": failure["failed_run_id"],
                    "intervention": reason,
                }
            else:
                operation_id = _identifier(
                    publication_operation_id, "publication_operation_id"
                )
                payload = {
                    "publication_operation_id": operation_id,
                    "intervention": reason,
                }
            response = context.client.submit(
                {
                    "request_id": self._request_id_factory(),
                    "operation": "registration.retry",
                    "project_id": project_id,
                    "activity_id": activity_id,
                    "question_id": None,
                    "expected_version": self.detail["activity_version"],
                    "payload": payload,
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

    def start(self, context: ExtensionContext, arguments: str) -> Mapping[str, object]:
        try:
            values = shlex.split(arguments)
        except ValueError as error:
            raise ValueError("register arguments are invalid") from error
        if len(values) != 2:
            raise ValueError(
                "register requires: /register <owner/repository> <overview-path>"
            )
        repository, overview_path = values
        response = context.client.submit(
            {
                "request_id": self._request_id_factory(),
                "operation": "registration.start",
                "project_id": None,
                "activity_id": None,
                "question_id": None,
                "expected_version": None,
                "payload": {
                    "repository": repository,
                    "overview_path": overview_path,
                },
            }
        )
        self.status = "Registration intake saved."
        return response

    def cancel(self, context: ExtensionContext) -> Mapping[str, object]:
        if self.detail is None:
            raise ValueError("open the registration before cancelling it")
        project_id, activity_id = self._detail_selection(context)
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
        result = response.get("result")
        state = result.get("state") if isinstance(result, Mapping) else None
        self.status = (
            "Stopping registration; reopen it to confirm the saved outcome."
            if state == "stopping"
            else "Registration cancelled; confirmed history is unchanged."
        )
        self.cancel_confirmation = False
        return response

    def begin_cancel(self, context: ExtensionContext) -> str:
        if self.detail is None:
            raise ValueError("open the registration before cancelling it")
        self._detail_selection(context)
        self.cancel_confirmation = True
        _replace_local_actions(context, [
            {
                "action_id": "registration-cancel-confirm",
                "label": "Cancel registration",
                "kind": "decision",
            },
            {
                "action_id": "registration-cancel-back",
                "label": "Go back",
                "kind": "decision",
            },
        ])
        return self.render()

    def cancel_back(self, context: ExtensionContext) -> str:
        self.cancel_confirmation = False
        return self.open(context)

    def source_choice(
        self, context: ExtensionContext, choice: str
    ) -> Mapping[str, object]:
        if self.detail is None:
            raise ValueError("open the registration before choosing source handling")
        consistency = self.detail.get("source_consistency")
        if not isinstance(consistency, Mapping) or consistency.get("state") != "changed":
            raise ValueError("registration has no displayed source update")
        if choice not in {"retain_reviewed_source", "include_updated_source"}:
            raise ValueError("registration source choice is invalid")
        project_id, activity_id = self._detail_selection(context)
        response = context.client.submit({
            "request_id": self._request_id_factory(),
            "operation": "registration.source-choice",
            "project_id": project_id,
            "activity_id": activity_id,
            "question_id": None,
            "expected_version": self.detail["activity_version"],
            "payload": {
                "choice": choice,
                "reviewed_commit": consistency["reviewed_commit"],
                "observed_commit": consistency["observed_commit"],
            },
        })
        self.status = (
            "The exact reviewed source was retained."
            if choice == "retain_reviewed_source"
            else "The updated source is being reassessed."
        )
        return response

    def owner_decision(
        self, context: ExtensionContext, decision_id: str, choice: str
    ) -> Mapping[str, object]:
        if self.detail is None:
            raise ValueError("open the registration before recording an Owner decision")
        decisions = self.detail.get("owner_decisions")
        if not isinstance(decisions, list):
            raise ValueError("registration has no pending Owner decision")
        decision = next(
            (
                item for item in decisions
                if isinstance(item, Mapping)
                and item.get("decision_id") == decision_id
                and item.get("state") == "pending"
            ),
            None,
        )
        if decision is None or choice not in {"grant_one", "remain_paused"}:
            raise ValueError("Owner decision does not match the displayed pending decision")
        project_id, activity_id = self._detail_selection(context)
        response = context.client.submit({
            "request_id": self._request_id_factory(),
            "operation": "owner.decision",
            "project_id": project_id,
            "activity_id": activity_id,
            "question_id": decision["question_id"],
            "expected_version": self.detail["activity_version"],
            "payload": {
                "decision_id": decision_id,
                "decision_version": decision["decision_version"],
                "target": decision["target"],
                "assignment_id": decision["assignment_id"],
                "choice": choice,
            },
        })
        self.status = (
            "One additional fidelity review was granted."
            if choice == "grant_one"
            else "Registration remains paused at the review limit."
        )
        return response

    def _detail_selection(self, context: ExtensionContext) -> tuple[str, str]:
        if self.detail is None:
            raise ValueError("open the registration first")
        project_id = _selected_project(context)
        if self.detail["project_id"] != project_id:
            raise ValueError("selected project changed after opening registration")
        return project_id, str(self.detail["activity_id"])

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
        registry.register_action("registration-cancel-confirm", self._cancel_confirm)
        registry.register_action("registration-cancel-back", self._cancel_back)
        registry.register_action("registration-source-choice", self._source_choice)
        registry.register_action("owner-decision", self._owner_decision)
        registry.register_input(
            "registration-retry", self._open_retry_input, self._submit_retry_input
        )

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
        detail = self.interaction.detail
        if detail is None or not isinstance(detail.get("package_ref"), Mapping):
            raise ValueError("open the registration before confirming it")
        candidate_id = arguments.strip() or str(
            detail["package_ref"]["candidate_id"]
        )
        consistency = detail.get("source_consistency")
        if (
            isinstance(consistency, Mapping)
            and consistency.get("state") == "changed"
            and not bool(consistency.get("retained"))
        ):
            self.interaction.status = (
                "Planning inputs changed after review. Choose whether to retain the "
                "reviewed source or include the updated source for reassessment."
            )
            _replace_local_actions(context, [
                {
                    "action_id": "registration-source-choice.retain_reviewed_source",
                    "label": "Retain reviewed source",
                    "kind": "decision",
                },
                {
                    "action_id": "registration-source-choice.include_updated_source",
                    "label": "Include updated source",
                    "kind": "decision",
                },
            ])
            return self.interaction.render()
        return self.interaction.confirm(
            context, candidate_id
        )

    def _retry(self, context: ExtensionContext, arguments: str) -> object:
        if self.interaction.pending is not None:
            if arguments.strip():
                raise ValueError(
                    "confirmation reconciliation retry takes no arguments"
                )
            return self.interaction.retry(context)
        operation_id = _identifier(arguments.strip(), "publication_operation_id")
        return ActionInput("registration-retry", operation_id)

    def _open_retry_input(
        self, _context: ExtensionContext, operation_id: str
    ) -> Mapping[str, object]:
        if operation_id == "agent":
            detail = self.interaction.detail
            failure = None if detail is None else detail.get("agent_retry")
            if not isinstance(failure, Mapping):
                raise ValueError("registration has no displayed agent failure")
            prompt = (
                "Describe the intervention before retrying assignment "
                f"{failure['assignment_id']} failed run {failure['failed_run_id']}."
            )
        else:
            prompt = "Describe the intervention before retrying publication."
        return {
            "action_id": f"registration-retry.{operation_id}",
            "prompt": prompt,
        }

    def _submit_retry_input(
        self, context: ExtensionContext, submission: InputSubmission
    ) -> object:
        operation_id = context.state.input.action_id  # type: ignore[attr-defined]
        return self.interaction.retry(context, operation_id, submission.text.strip())

    def _cancel(self, context: ExtensionContext, arguments: str) -> object:
        if arguments.strip():
            raise ValueError("registration cancel takes no arguments")
        return self.interaction.begin_cancel(context)

    def _cancel_confirm(self, context: ExtensionContext, arguments: str) -> object:
        if arguments.strip():
            raise ValueError("registration cancellation confirmation takes no arguments")
        return self.interaction.cancel(context)

    def _cancel_back(self, context: ExtensionContext, arguments: str) -> object:
        if arguments.strip():
            raise ValueError("registration cancellation return takes no arguments")
        return self.interaction.cancel_back(context)

    def _source_choice(self, context: ExtensionContext, arguments: str) -> object:
        return self.interaction.source_choice(context, arguments.strip())

    def _owner_decision(self, context: ExtensionContext, arguments: str) -> object:
        decision_id, separator, choice = arguments.rpartition(".")
        if not separator:
            raise ValueError("Owner decision action is invalid")
        return self.interaction.owner_decision(context, decision_id, choice)


def _selected_project(context: ExtensionContext) -> str:
    project_id = context.state.selected_project_id
    if not isinstance(project_id, str) or not project_id:
        raise ValueError("select a project before opening registration")
    return project_id


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
        "package_ref", "comparison", "agent_retry", "history", "can_confirm",
    }
    optional = {
        "owner_decisions", "assessment", "package_manifest", "package_records",
        "provenance", "source_consistency",
    }
    if not fields.issubset(detail) or set(detail) - fields - optional:
        raise ValueError("registration response fields do not match the contract")
    detail.setdefault("owner_decisions", [])
    detail.setdefault("assessment", None)
    detail.setdefault("package_manifest", None)
    detail.setdefault("package_records", [])
    detail.setdefault("provenance", None)
    detail.setdefault("source_consistency", None)
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
    _comparison(detail["comparison"])
    _agent_retry(detail["agent_retry"])
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
    if not isinstance(detail["owner_decisions"], list):
        raise ValueError("registration Owner decisions must be an array")
    if not isinstance(detail["package_records"], list):
        raise ValueError("registration package records must be an array")
    return detail


def _replace_local_actions(
    context: ExtensionContext, actions: list[dict[str, str]]
) -> None:
    detail = getattr(context.state, "activity_detail", None)
    if isinstance(detail, Mapping):
        updated = dict(detail)
        updated["available_actions"] = actions
        setattr(context.state, "activity_detail", updated)


def _display_value(value: object) -> str:
    if isinstance(value, (Mapping, list, tuple)):
        return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return str(value)


def _comparison(value: object) -> None:
    if value is None:
        return
    if not isinstance(value, Mapping) or set(value) != {
        "active_package_ref", "candidate_package_ref", "differences"
    }:
        raise ValueError("registration comparison is invalid")
    _package_ref(value["active_package_ref"])
    _package_ref(value["candidate_package_ref"])
    differences = value["differences"]
    if not isinstance(differences, list):
        raise ValueError("registration comparison differences must be an array")
    fields = {
        "kind", "item_id", "subject", "area", "previous_version",
        "candidate_version", "reason_refs",
    }
    for difference in differences:
        if not isinstance(difference, Mapping) or set(difference) != fields:
            raise ValueError("registration comparison difference is invalid")
        for field in ("kind", "item_id", "subject", "area"):
            _text(difference[field], f"comparison {field}")
        if not isinstance(difference["reason_refs"], list) or any(
            not isinstance(item, str) or not item for item in difference["reason_refs"]
        ):
            raise ValueError("registration comparison reasons are invalid")


def _agent_retry(value: object) -> None:
    if value is None:
        return
    fields = {
        "assignment_id", "failed_run_id", "role", "reason", "automatic_limit",
        "automatic_consumed", "manual_consumed", "state",
    }
    if not isinstance(value, Mapping) or set(value) != fields:
        raise ValueError("registration agent retry is invalid")
    for field in ("assignment_id", "failed_run_id", "role", "reason", "state"):
        _text(value[field], f"agent retry {field}")
    for field in ("automatic_limit", "automatic_consumed", "manual_consumed"):
        if isinstance(value[field], bool) or not isinstance(value[field], int) or value[field] < 0:
            raise ValueError(f"agent retry {field} must be nonnegative")


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
