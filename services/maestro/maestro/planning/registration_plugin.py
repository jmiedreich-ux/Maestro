"""Registration process plugin joining intake, route preflight, and assessment."""

from __future__ import annotations

import json
from typing import Any, Mapping

from maestro.agents.preflight import AgentRoutePreflight, RunningToolIdentity, verify_running_identity
from maestro.agents.routes import RoleSelections, RouteRequirements
from maestro.agents.supervisor import OperationIdentity
from maestro.foundation import Database, DomainMigration, canonical_json
from maestro.service.processes import ProcessHandlerRegistry, ProcessProvider, ProcessSnapshot

from .intake import RegistrationIntakeResult
from .registration import AssessmentContext, AssessmentRun, RegistrationAssessment, RegistrationAssessmentError
from .registration_records import (
    RegistrationAgentResponse,
    RegistrationPackageContext,
    validate_registration_package,
)


REGISTRATION_REQUIREMENTS = RouteRequirements(
    ("code_edit", "local_command", "repository_search", "approved_network"),
    ("local_ai_box", "cloud"),
    65536,
)

REGISTRATION_ASSESSMENT_RUNTIME_MIGRATION = DomainMigration(
    domain="registration_assessment",
    version=1,
    identity="registration-assessment-runtime-v1",
    statements=(
        """
        CREATE TABLE registration_assessment_runs(
            activity_id TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('project_architect', 'fidelity_reviewer')),
            assignment_id TEXT NOT NULL,
            run_id TEXT NOT NULL,
            route_json TEXT NOT NULL,
            runtime_identity_json TEXT,
            PRIMARY KEY(activity_id, role)
        )
        """,
        """
        CREATE TABLE registration_assessment_intake(
            activity_id TEXT PRIMARY KEY,
            intake_json TEXT NOT NULL
        )
        """,
    ),
)


def validate_registration_process_definition(definition: Mapping[str, Any]) -> None:
    """Validate the fixed registration policies; shared service checks types/defaults."""
    if not isinstance(definition, Mapping):
        raise RegistrationAssessmentError("registration definition must be an object")
    expected = {
        "initiation": "registration_intake_or_idle_update",
        "agent_session": "fixed_assignment_followups",
        "saved_outputs": "versioned_registration_package",
        "review": "bounded_independent_fidelity",
        "confirmation": "explicit_exact_candidate_activation",
        "recovery": "reconcile_preserved_registration",
    }
    for section, policy in expected.items():
        value = definition.get(section)
        if not isinstance(value, Mapping) or value.get("policy") != policy:
            raise RegistrationAssessmentError(f"registration {section} policy is unsupported")
    session = definition["agent_session"]
    if session.get("architect_role") != "project_architect" or session.get("reviewer_role") != "fidelity_reviewer":
        raise RegistrationAssessmentError("registration must use project_architect and fidelity_reviewer roles")


class RegistrationProcessPlugin:
    """A real minimal consumer of the source-intake and route contracts."""

    def __init__(self, preflight: AgentRoutePreflight) -> None:
        if not isinstance(preflight, AgentRoutePreflight):
            raise TypeError("registration plugin requires the service-owned route preflight")
        self.preflight = preflight
        self._provider = ProcessProvider(
            "registration", "registration-process@1", validate_registration_process_definition,
            {
                "initiation": {"registration_intake_or_idle_update": self._start_handler},
                "agent_session": {"fixed_assignment_followups": self._architect_response_handler},
                "saved_outputs": {"versioned_registration_package": self._package_handler},
                "review": {"bounded_independent_fidelity": self._reviewer_response_handler},
                "confirmation": {"explicit_exact_candidate_activation": self._confirmation_handler},
                "recovery": {"reconcile_preserved_registration": self._recovery_handler},
            },
            routes=("registration.start",), required_outputs=("registration_package",),
        )

    def start_assessment(
        self,
        *,
        intake: RegistrationIntakeResult,
        snapshot: ProcessSnapshot,
        selections: RoleSelections,
        project_id: str,
        activity_id: str,
        decision_version: str,
        architect_identity: str,
        reviewer_identity: str,
        architect_assignment_id: str,
        architect_run_id: str,
        reviewer_assignment_id: str,
        reviewer_run_id: str,
        source_repository: str,
        selection_decision_ref: str,
    ) -> RegistrationAssessment:
        if not isinstance(intake, RegistrationIntakeResult) or intake.inventory is None:
            raise RegistrationAssessmentError("registration assessment cannot start without exact authorized source intake")
        if intake.missing_questions:
            raise RegistrationAssessmentError("registration assessment cannot start while intake questions remain")
        routes = self.preflight.resolve_process_roles(
            self._provider, snapshot, selections,
            {"architect": REGISTRATION_REQUIREMENTS, "fidelity_reviewer": REGISTRATION_REQUIREMENTS},
        )
        review_limit = snapshot.definition.get("maximum_fidelity_reviews", 2)
        package_context = RegistrationPackageContext.from_intake(
            project_id=project_id,
            source_repository=source_repository,
            intake=intake,
            decision_version=decision_version,
            selection_decision_ref=selection_decision_ref,
        )
        return RegistrationAssessment(AssessmentContext(
            project_id, activity_id, intake.inventory, decision_version, intake.selected_scope or "", architect_identity,
            reviewer_identity, routes, AssessmentRun(architect_assignment_id, architect_run_id),
            AssessmentRun(reviewer_assignment_id, reviewer_run_id), package_context, review_limit,
        ))

    @property
    def provider(self) -> ProcessProvider:
        return self._provider

    def _start_handler(self, snapshot: ProcessSnapshot, **kwargs: object) -> RegistrationAssessment:
        """Dispatch the validated ``registration.start`` operation into assessment."""
        return self.start_assessment(snapshot=snapshot, **kwargs)

    @staticmethod
    def _architect_response_handler(
        _snapshot: ProcessSnapshot, *, assessment: RegistrationAssessment,
        response: RegistrationAgentResponse, running_identity: object,
    ) -> object:
        return assessment.submit_architect(response, running_identity)

    @staticmethod
    def _reviewer_response_handler(
        _snapshot: ProcessSnapshot, *, assessment: RegistrationAssessment,
        response: RegistrationAgentResponse, running_identity: object,
    ) -> object:
        return assessment.submit_reviewer(response, running_identity)

    @staticmethod
    def _package_handler(
        _snapshot: ProcessSnapshot, *, assessment: RegistrationAssessment,
        manifest: object, records: object,
    ) -> object:
        return validate_registration_package(manifest, records, assessment.context.package_context)

    @staticmethod
    def _confirmation_handler(
        _snapshot: ProcessSnapshot, *, assessment: RegistrationAssessment,
    ) -> object:
        return assessment.require_ready_candidate()

    @staticmethod
    def _recovery_handler(
        _snapshot: ProcessSnapshot, *, assessment: RegistrationAssessment,
    ) -> object:
        """Expose durable state for service recovery; it never fabricates a rerun."""
        return assessment.status


class RegistrationServiceBinding:
    """Installed-service dispatcher with service-owned durable run identity facts.

    Agent output is never allowed to select its assignment, run, or runtime
    identity.  The service records those facts first, then passes the saved
    identity into the process provider when accepting a response.
    """

    def __init__(
        self, database: Database, plugin: RegistrationProcessPlugin,
        registry: ProcessHandlerRegistry,
    ) -> None:
        if not isinstance(database, Database) or not isinstance(plugin, RegistrationProcessPlugin):
            raise TypeError("registration service binding requires installed service dependencies")
        if not isinstance(registry, ProcessHandlerRegistry):
            raise TypeError("registration service binding requires process registry")
        self.database, self.plugin, self.registry = database, plugin, registry
        self.registry.register(plugin.provider)
        self.database.registry.register(REGISTRATION_ASSESSMENT_RUNTIME_MIGRATION)
        self.database.initialize()
        self._assessments: dict[str, RegistrationAssessment] = {}

    def start(self, snapshot: ProcessSnapshot, **arguments: object) -> RegistrationAssessment:
        assessment = self.registry.dispatch(snapshot, "initiation", **arguments)
        if not isinstance(assessment, RegistrationAssessment):
            raise RegistrationAssessmentError("registration.start did not create an assessment")
        assessment.bind_process_snapshot(snapshot)
        context = assessment.context
        rows = (
            ("project_architect", context.architect_run, context.routes.architect),
            ("fidelity_reviewer", context.reviewer_run, context.routes.fidelity_reviewer),
        )
        intake = context.package_context
        with self.database.transaction() as transaction:
            transaction.execute(
                "INSERT INTO registration_assessment_intake(activity_id, intake_json) VALUES (?, ?)",
                (context.activity_id, canonical_json({
                    "project_id": intake.project_id,
                    "source_repository": intake.source_repository,
                    "source_ref": intake.source_inventory.source_ref,
                    "source_commit": intake.source_inventory.source_commit,
                    "overview_path": intake.source_inventory.overview_path,
                    "decision_version": intake.decision_version,
                    "publication_branch": intake.publication_branch,
                    "destination_snapshot_reference": intake.destination_snapshot_reference,
                    "selection_decision_ref": intake.selection_decision_ref,
                })),
            )
            for role, run, route in rows:
                transaction.execute(
                    """INSERT INTO registration_assessment_runs(
                        activity_id, role, assignment_id, run_id, route_json, runtime_identity_json
                    ) VALUES (?, ?, ?, ?, ?, NULL)""",
                    (context.activity_id, role, run.assignment_id, run.run_id, canonical_json({
                        "provider": route.provider,
                        "model_id": route.requested_model_id,
                        "tool_version": route.tool_version,
                        "configuration_hash": route.configuration_hash,
                    })),
                )
        self._assessments[context.activity_id] = assessment
        return assessment

    def record_runtime_identity(self, operation: OperationIdentity, identity: RunningToolIdentity) -> None:
        """Save tool metadata for the current service-reserved role/run only."""
        if not isinstance(operation, OperationIdentity) or not isinstance(identity, RunningToolIdentity):
            raise TypeError("runtime identity requires service operation and tool metadata")
        assessment = self._assessment(operation.activity_id)
        role, route = self._role_for_assignment(assessment, operation)
        try:
            verify_running_identity(route, identity)
        except ValueError as error:
            raise RegistrationAssessmentError("running tool identity differs from service route") from error
        with self.database.transaction() as transaction:
            updated = transaction.execute(
                """UPDATE registration_assessment_runs SET runtime_identity_json = ?
                   WHERE activity_id = ? AND role = ? AND assignment_id = ? AND run_id = ?""",
                (canonical_json(_identity_mapping(identity)), operation.activity_id, role, operation.assignment_id, operation.run_id),
            )
            if updated.rowcount != 1:
                raise RegistrationAssessmentError("runtime identity does not match a current saved assignment run")

    def submit_architect(self, response: RegistrationAgentResponse) -> object:
        assessment = self._assessment_for_response(response, "project_architect")
        return self.registry.dispatch(
            _snapshot_for(assessment), "agent_session", assessment=assessment,
            response=response, running_identity=self._saved_identity(assessment, "project_architect"),
        )

    def submit_reviewer(self, response: RegistrationAgentResponse) -> object:
        assessment = self._assessment_for_response(response, "fidelity_reviewer")
        return self.registry.dispatch(
            _snapshot_for(assessment), "review", assessment=assessment,
            response=response, running_identity=self._saved_identity(assessment, "fidelity_reviewer"),
        )

    def validate_package(self, activity_id: str, manifest: object, records: object) -> object:
        assessment = self._assessment(activity_id)
        return self.registry.dispatch(
            _snapshot_for(assessment), "saved_outputs", assessment=assessment, manifest=manifest, records=records,
        )

    @staticmethod
    def _role_for_assignment(assessment: RegistrationAssessment, operation: OperationIdentity):
        context = assessment.context
        if operation.project_id != context.project_id or operation.activity_id != context.activity_id:
            raise RegistrationAssessmentError("operation is outside the saved registration assessment")
        if (operation.assignment_id, operation.run_id) == (context.architect_run.assignment_id, context.architect_run.run_id):
            return "project_architect", context.routes.architect
        if (operation.assignment_id, operation.run_id) == (context.reviewer_run.assignment_id, context.reviewer_run.run_id):
            return "fidelity_reviewer", context.routes.fidelity_reviewer
        raise RegistrationAssessmentError("operation is not a current registration assignment run")

    def _assessment_for_response(self, response: RegistrationAgentResponse, role: str) -> RegistrationAssessment:
        if not isinstance(response, RegistrationAgentResponse) or response.role != role:
            raise RegistrationAssessmentError("response is not for the dispatched registration role")
        assessment = self._assessment(response.activity_id)
        expected = assessment.context.architect_run if role == "project_architect" else assessment.context.reviewer_run
        if (response.assignment_id, response.run_id) != (expected.assignment_id, expected.run_id):
            raise RegistrationAssessmentError("response does not match the service-saved current run")
        return assessment

    def _saved_identity(self, assessment: RegistrationAssessment, role: str) -> RunningToolIdentity:
        with self.database.read_connection() as connection:
            row = connection.execute(
                "SELECT runtime_identity_json FROM registration_assessment_runs WHERE activity_id = ? AND role = ?",
                (assessment.context.activity_id, role),
            ).fetchone()
        if row is None or row[0] is None:
            raise RegistrationAssessmentError("service has no verified runtime identity for the current run")
        try:
            value = json.loads(str(row[0]))
            return RunningToolIdentity(**value)
        except (TypeError, ValueError, json.JSONDecodeError) as error:
            raise RegistrationAssessmentError("saved runtime identity is invalid") from error

    def _assessment(self, activity_id: str) -> RegistrationAssessment:
        try:
            return self._assessments[activity_id]
        except KeyError as error:
            raise RegistrationAssessmentError("registration assessment is unavailable for unsafe continuation") from error


def _identity_mapping(identity: RunningToolIdentity) -> dict[str, str]:
    return {
        "source": identity.source,
        "provider": identity.provider,
        "model_id": identity.model_id,
        "tool_version": identity.tool_version,
        "configuration_hash": identity.configuration_hash,
    }


def _snapshot_for(assessment: RegistrationAssessment) -> ProcessSnapshot:
    """The service binds dispatch to the exact snapshot supplied at start."""
    return assessment.process_snapshot


def registration_process_provider(preflight: AgentRoutePreflight) -> ProcessProvider:
    """Entry point used by the shared process registry at installation."""
    return RegistrationProcessPlugin(preflight).provider
