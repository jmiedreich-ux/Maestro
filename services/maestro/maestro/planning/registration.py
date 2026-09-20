"""Registration assessment state machine with bounded independent review."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable, Mapping

from maestro.agents.preflight import (
    ResolvedRoleRoutes,
    RunningToolIdentity,
    verify_running_identity,
)
from maestro.service.processes import ProcessSnapshot

from .registration_records import (
    ArtifactReference,
    Finding,
    RegistrationAgentResponse,
    RegistrationPackageContext,
    RegistrationRecordError,
)
from .sources import SourceInventory


class RegistrationAssessmentError(ValueError):
    """Assessment cannot safely advance toward candidate confirmation."""


@dataclass(frozen=True)
class AssessmentRun:
    """The one service-reserved assignment/run permitted to update a role."""

    assignment_id: str
    run_id: str

    def __post_init__(self) -> None:
        for field in ("assignment_id", "run_id"):
            value = getattr(self, field)
            if not isinstance(value, str) or not value.strip():
                raise RegistrationAssessmentError(f"{field} must be nonempty")


@dataclass(frozen=True)
class AssessmentContext:
    project_id: str
    activity_id: str
    source_inventory: SourceInventory
    decision_version: str
    selected_scope: str
    architect_identity: str
    reviewer_identity: str
    routes: ResolvedRoleRoutes
    architect_run: AssessmentRun
    reviewer_run: AssessmentRun
    package_context: RegistrationPackageContext
    review_limit: int = 2

    def __post_init__(self) -> None:
        for field in ("project_id", "activity_id", "decision_version", "selected_scope", "architect_identity", "reviewer_identity"):
            value = getattr(self, field)
            if not isinstance(value, str) or not value.strip():
                raise RegistrationAssessmentError(f"{field} must be nonempty")
        if not isinstance(self.source_inventory, SourceInventory):
            raise RegistrationAssessmentError("assessment requires immutable exact source inventory")
        if not isinstance(self.routes, ResolvedRoleRoutes):
            raise RegistrationAssessmentError("assessment requires preflighted exact role routes")
        if not isinstance(self.architect_run, AssessmentRun) or not isinstance(self.reviewer_run, AssessmentRun):
            raise RegistrationAssessmentError("assessment requires current architect and reviewer runs")
        if not isinstance(self.package_context, RegistrationPackageContext):
            raise RegistrationAssessmentError("assessment requires package context derived from saved intake")
        if self.package_context.project_id != self.project_id or self.package_context.source_inventory != self.source_inventory:
            raise RegistrationAssessmentError("package context differs from pinned assessment intake")
        if self.architect_identity == self.reviewer_identity:
            raise RegistrationAssessmentError("independent reviewer cannot be the architect")
        if isinstance(self.review_limit, bool) or not isinstance(self.review_limit, int) or self.review_limit < 1:
            raise RegistrationAssessmentError("review_limit must be positive")


@dataclass(frozen=True)
class AssessmentStatus:
    state: str
    review_count: int
    review_limit: int
    candidate: ArtifactReference | None
    assessment: ArtifactReference | None
    blockers: tuple[str, ...]
    execution_eligible: bool


class RegistrationAssessment:
    """Keep assessment, reviewer coverage, and correction accounting separate.

    This object has no execution-start method: a candidate only becomes eligible
    for the later explicit confirmation operation.  It accepts responses only
    after callers have run the service-owned artifact and tool identity checks.
    """

    def __init__(self, context: AssessmentContext) -> None:
        if not isinstance(context, AssessmentContext):
            raise TypeError("registration assessment requires AssessmentContext")
        self.context = context
        self._candidate: ArtifactReference | None = None
        self._assessment: ArtifactReference | None = None
        self._architect_findings: tuple = ()
        self._review_findings: tuple = ()
        self._review_count = 0
        self._state = "awaiting_architect"
        self._reviewed_candidate: ArtifactReference | None = None
        self._reviewed_assessment: ArtifactReference | None = None
        self._current_runs = {
            "project_architect": context.architect_run,
            "fidelity_reviewer": context.reviewer_run,
        }
        self._process_snapshot: ProcessSnapshot | None = None

    def bind_process_snapshot(self, snapshot: ProcessSnapshot) -> None:
        """Attach the immutable service snapshot that authorized this assessment."""
        if not isinstance(snapshot, ProcessSnapshot) or snapshot.process_name != "registration":
            raise RegistrationAssessmentError("assessment requires the registration process snapshot")
        if self._process_snapshot is not None and self._process_snapshot != snapshot:
            raise RegistrationAssessmentError("assessment process snapshot cannot be replaced")
        self._process_snapshot = snapshot

    @property
    def process_snapshot(self) -> ProcessSnapshot:
        if self._process_snapshot is None:
            raise RegistrationAssessmentError("assessment lacks a service process snapshot")
        return self._process_snapshot

    @property
    def status(self) -> AssessmentStatus:
        blockers = tuple(item.subject for item in (*self._architect_findings, *self._review_findings) if item.severity == "blocking")
        ready = self._state == "ready" and not blockers
        return AssessmentStatus(self._state, self._review_count, self.context.review_limit, self._candidate, self._assessment, blockers, ready)

    def set_current_run(self, role: str, run: AssessmentRun) -> None:
        """Accept a service-confirmed recovery/follow-up run without resetting review budget."""
        if role not in self._current_runs or not isinstance(run, AssessmentRun):
            raise RegistrationAssessmentError("current run binding is invalid")
        expected_state = "awaiting_architect" if role == "project_architect" else "awaiting_reviewer"
        if self._state != expected_state:
            raise RegistrationAssessmentError("run replacement is not eligible at this assessment step")
        self._current_runs[role] = run

    def to_record(self) -> dict[str, object]:
        """Return mutable state for durable recovery, separate from intake."""
        return {
            "state": self._state,
            "review_count": self._review_count,
            "candidate": _artifact_record(self._candidate),
            "assessment": _artifact_record(self._assessment),
            "architect_findings": [asdict(item) for item in self._architect_findings],
            "review_findings": [asdict(item) for item in self._review_findings],
            "reviewed_candidate": _artifact_record(self._reviewed_candidate),
            "reviewed_assessment": _artifact_record(self._reviewed_assessment),
            "current_runs": {
                role: {"assignment_id": run.assignment_id, "run_id": run.run_id}
                for role, run in self._current_runs.items()
            },
        }

    @classmethod
    def from_record(cls, context: AssessmentContext, value: object) -> "RegistrationAssessment":
        """Rehydrate saved state without contacting or rereading the source."""
        fields = {
            "state", "review_count", "candidate", "assessment", "architect_findings",
            "review_findings", "reviewed_candidate", "reviewed_assessment", "current_runs",
        }
        if not isinstance(value, Mapping) or set(value) != fields:
            raise RegistrationAssessmentError("saved registration assessment state is invalid")
        state, review_count = value["state"], value["review_count"]
        states = {
            "awaiting_architect", "awaiting_reviewer", "changes_requested", "clarification_required",
            "technical_recovery", "ready", "blocked", "review_limit_owner_decision",
        }
        if state not in states or isinstance(review_count, bool) or not isinstance(review_count, int) or not 0 <= review_count <= context.review_limit:
            raise RegistrationAssessmentError("saved registration assessment state is invalid")
        runs = value["current_runs"]
        if not isinstance(runs, Mapping) or set(runs) != {"project_architect", "fidelity_reviewer"}:
            raise RegistrationAssessmentError("saved registration assessment runs are invalid")
        try:
            restored = cls(context)
            restored._state = state
            restored._review_count = review_count
            restored._candidate = _artifact_from_record(value["candidate"])
            restored._assessment = _artifact_from_record(value["assessment"])
            restored._architect_findings = _findings_from_record(value["architect_findings"])
            restored._review_findings = _findings_from_record(value["review_findings"])
            restored._reviewed_candidate = _artifact_from_record(value["reviewed_candidate"])
            restored._reviewed_assessment = _artifact_from_record(value["reviewed_assessment"])
            restored._current_runs = {
                role: AssessmentRun(runs[role]["assignment_id"], runs[role]["run_id"])
                for role in ("project_architect", "fidelity_reviewer")
            }
        except (KeyError, TypeError, RegistrationRecordError) as error:
            raise RegistrationAssessmentError("saved registration assessment state is invalid") from error
        return restored

    def submit_architect(
        self, response: RegistrationAgentResponse, running_identity: RunningToolIdentity,
    ) -> AssessmentStatus:
        self._validate_context(response, "project_architect", running_identity)
        if self._state not in {"awaiting_architect", "changes_requested", "clarification_required"}:
            raise RegistrationAssessmentError("architect response is not expected at this assessment step")
        if response.result == "technical_failure":
            self._state = "technical_recovery"
            return self.status
        if response.result == "clarification_required":
            self._state = "clarification_required"
            return self.status
        assert response.candidate is not None and response.assessment is not None
        if self._candidate is not None and response.candidate == self._candidate:
            raise RegistrationAssessmentError("an amendment must create a new immutable candidate")
        self._candidate, self._assessment = response.candidate, response.assessment
        self._architect_findings, self._review_findings = response.findings, ()
        self._reviewed_candidate = self._reviewed_assessment = None
        self._state = "awaiting_reviewer"
        return self.status

    def submit_reviewer(
        self, response: RegistrationAgentResponse, running_identity: RunningToolIdentity,
    ) -> AssessmentStatus:
        self._validate_context(response, "fidelity_reviewer", running_identity)
        if self._state != "awaiting_reviewer":
            raise RegistrationAssessmentError("reviewer response is not expected at this assessment step")
        if response.result == "technical_failure":
            self._state = "technical_recovery"
            return self.status
        if response.result == "clarification_required":
            self._state = "clarification_required"
            return self.status
        assert self._candidate is not None and self._assessment is not None
        if response.candidate != self._candidate or response.reviewed_assessment != self._assessment:
            raise RegistrationAssessmentError("reviewer must review the exact assigned candidate and assessment")
        self._review_count += 1
        self._reviewed_candidate, self._reviewed_assessment = response.candidate, response.reviewed_assessment
        self._review_findings = response.findings
        assert response.review_outcome is not None
        if response.review_outcome == "APPROVE":
            self._state = "ready" if not self._blocking() else "blocked"
        elif self._review_count >= self.context.review_limit:
            self._state = "review_limit_owner_decision"
        else:
            self._state = "changes_requested"
        return self.status

    def require_ready_candidate(self) -> ArtifactReference:
        status = self.status
        if not status.execution_eligible or status.candidate is None:
            raise RegistrationAssessmentError("candidate is not eligible: unresolved blockers, review, or confirmation boundary")
        return status.candidate

    def _blocking(self) -> bool:
        return any(item.severity == "blocking" for item in (*self._architect_findings, *self._review_findings))

    def _validate_context(
        self, response: RegistrationAgentResponse, role: str, running_identity: RunningToolIdentity,
    ) -> None:
        if not isinstance(response, RegistrationAgentResponse):
            raise TypeError("assessment requires a validated registration response")
        expected = self.context
        if response.role != role:
            raise RegistrationAssessmentError("response role does not match the assigned assessment step")
        if (response.assignment_id, response.run_id) != (
            self._current_runs[role].assignment_id, self._current_runs[role].run_id,
        ):
            raise RegistrationAssessmentError("response does not match the current assigned run")
        route = expected.routes.architect if role == "project_architect" else expected.routes.fidelity_reviewer
        try:
            verify_running_identity(route, running_identity)
        except ValueError as error:
            raise RegistrationAssessmentError("response lacks verified exact running tool identity") from error
        if (response.project_id, response.activity_id, response.source_commit, response.decision_version) != (
            expected.project_id, expected.activity_id, expected.source_inventory.source_commit, expected.decision_version,
        ):
            raise RegistrationAssessmentError("response does not match the pinned project, source, or decisions")


def _artifact_record(value: ArtifactReference | None) -> dict[str, str] | None:
    return None if value is None else value.as_dict()


def _artifact_from_record(value: object) -> ArtifactReference | None:
    return None if value is None else ArtifactReference.from_mapping(value)


def _findings_from_record(value: object) -> tuple[Finding, ...]:
    if not isinstance(value, list):
        raise RegistrationAssessmentError("saved registration assessment findings are invalid")
    try:
        return tuple(Finding(**item) for item in value)
    except (TypeError, ValueError) as error:
        raise RegistrationAssessmentError("saved registration assessment findings are invalid") from error


def validate_completion_mapping(inventory: SourceInventory, included_outcomes: Iterable[str], completion_requirements: Iterable[str]) -> None:
    """Reject a candidate that claims a selected outcome without completion mapping."""
    if not isinstance(inventory, SourceInventory):
        raise TypeError("completion mapping requires exact source inventory")
    included = tuple(included_outcomes)
    requirements = frozenset(completion_requirements)
    known = {outcome.milestone for outcome in inventory.outcomes}
    if not included or any(not isinstance(item, str) or item not in known for item in included):
        raise RegistrationAssessmentError("selected scope contains an unknown or missing essential outcome")
    missing = [item for item in included if item not in requirements]
    if missing:
        raise RegistrationAssessmentError("selected outcome has no completion requirement mapping")
