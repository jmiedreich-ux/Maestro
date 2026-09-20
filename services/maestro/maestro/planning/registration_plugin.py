"""Registration process plugin joining intake, route preflight, and assessment."""

from __future__ import annotations

import json
import uuid
from typing import Any, Mapping

from maestro.agents.preflight import AgentRoutePreflight, ResolvedAgentRoute, ResolvedRoleRoutes, RunningToolIdentity, verify_running_identity
from maestro.agents.runtime_identity import ConfirmedRuntimeIdentity, PlanningIdentityConsumer, RuntimeIdentityProtocolError
from maestro.agents.routes import ConfiguredAgentRouteProvider, PermittedDestination, RoleSelections, RouteRequirements, ToolModelSelection
from maestro.agents.supervisor import AgentSupervisor, OperationIdentity
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
_SUPERVISOR_AUTHORITY_ATTRIBUTE = "_RegistrationServiceBinding__supervisor_authority"
_RUNTIME_IDENTITY_CONSUMER_ATTRIBUTE = "_RegistrationServiceBinding__runtime_identity_consumer"

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
            project_id TEXT NOT NULL,
            selections_json TEXT NOT NULL,
            intake_json TEXT NOT NULL
        )
        """,
        """
        CREATE TABLE registration_assessment_state(
            activity_id TEXT PRIMARY KEY,
            state_json TEXT NOT NULL
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

    def __init__(
        self, configured_routes: ConfiguredAgentRouteProvider | None,
        preflight: AgentRoutePreflight | None = None,
    ) -> None:
        if configured_routes is not None and not isinstance(configured_routes, ConfiguredAgentRouteProvider):
            raise TypeError("registration plugin requires the installed configured route provider")
        if preflight is not None and not isinstance(preflight, AgentRoutePreflight):
            raise TypeError("registration plugin requires a service-owned route preflight")
        self.configured_routes = configured_routes
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
        snapshot: ProcessSnapshot,
        activity_id: str,
        project_id: str,
        intake: RegistrationIntakeResult,
        selections: RoleSelections,
    ) -> RegistrationAssessment:
        if not isinstance(intake, RegistrationIntakeResult) or intake.inventory is None:
            raise RegistrationAssessmentError("registration assessment cannot start without exact authorized source intake")
        if intake.missing_questions:
            raise RegistrationAssessmentError("registration assessment cannot start while intake questions remain")
        if self.configured_routes is None or self.preflight is None:
            raise RegistrationAssessmentError("registration assessment start requires installed configured runtime preflight")
        # Check the service configuration before consulting live preflight.  A
        # plugin cannot select a route that is absent from the one configured
        # provider the installed service exposed to it.
        self.configured_routes.resolve(selections.architect)
        self.configured_routes.resolve(selections.fidelity_reviewer)
        routes = self.preflight.resolve_process_roles(
            self._provider, snapshot, selections,
            {"architect": REGISTRATION_REQUIREMENTS, "fidelity_reviewer": REGISTRATION_REQUIREMENTS},
        )
        review_limit = snapshot.definition.get("maximum_fidelity_reviews", 2)
        package_context = _package_context(project_id, intake)
        return RegistrationAssessment(AssessmentContext(
            project_id, activity_id, intake.inventory, package_context.decision_version, intake.selected_scope or "", "project_architect",
            "fidelity_reviewer", routes, _new_run("project_architect"),
            _new_run("fidelity_reviewer"), package_context, review_limit,
        ))

    @property
    def provider(self) -> ProcessProvider:
        return self._provider

    def _start_handler(self, _snapshot: ProcessSnapshot, **_kwargs: object) -> RegistrationAssessment:
        raise RegistrationAssessmentError(
            "registration.start is available only through the installed service binding"
        )

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

    def __setattr__(self, name: str, value: object) -> None:
        if name in {_SUPERVISOR_AUTHORITY_ATTRIBUTE, _RUNTIME_IDENTITY_CONSUMER_ATTRIBUTE} and hasattr(self, name):
            raise AttributeError("registration runtime authority is immutable")
        super().__setattr__(name, value)

    def __init__(
        self, database: Database, plugin: RegistrationProcessPlugin,
        registry: ProcessHandlerRegistry, supervisor: AgentSupervisor,
        runtime_identity_consumer: PlanningIdentityConsumer | None,
    ) -> None:
        if not isinstance(database, Database) or not isinstance(plugin, RegistrationProcessPlugin):
            raise TypeError("registration service binding requires installed service dependencies")
        if not isinstance(registry, ProcessHandlerRegistry):
            raise TypeError("registration service binding requires process registry")
        if type(supervisor) is not AgentSupervisor:
            raise TypeError("registration service binding requires the installed supervisor")
        if runtime_identity_consumer is not None and not callable(getattr(runtime_identity_consumer, "consume", None)):
            raise TypeError("registration service binding requires the protected planning identity consumer")
        self.__supervisor_authority = supervisor
        self.__runtime_identity_consumer = runtime_identity_consumer
        self.database, self.plugin, self.registry = database, plugin, registry
        self.registry.register(plugin.provider)
        self.database.registry.register(REGISTRATION_ASSESSMENT_RUNTIME_MIGRATION)
        self.database.initialize()
        self._assessments: dict[str, RegistrationAssessment] = {}

    @property
    def supervisor(self) -> AgentSupervisor:
        """Return the installed runtime supervisor without permitting replacement."""
        return self.__supervisor_authority

    def save_intake(
        self, activity_id: str, project_id: str, intake: RegistrationIntakeResult,
        selections: RoleSelections,
    ) -> None:
        """Persist completed intake before assessment; no source field is split out.

        This boundary is used by the installed intake flow, not by agents.  The
        assessment start operation subsequently accepts only the activity and
        the service's saved process snapshot.
        """
        if not isinstance(activity_id, str) or not activity_id or not isinstance(project_id, str) or not project_id:
            raise RegistrationAssessmentError("saved registration intake needs project and activity identities")
        if not isinstance(intake, RegistrationIntakeResult) or intake.inventory is None:
            raise RegistrationAssessmentError("registration assessment requires completed saved intake")
        if not isinstance(selections, RoleSelections):
            raise RegistrationAssessmentError("registration assessment requires saved role selections")
        try:
            intake_json = intake.to_json()
        except ValueError as error:
            raise RegistrationAssessmentError("registration assessment intake cannot be persisted") from error
        with self.database.transaction() as transaction:
            transaction.execute(
                """INSERT INTO registration_assessment_intake(
                       activity_id, project_id, selections_json, intake_json
                   ) VALUES (?, ?, ?, ?)""",
                (activity_id, project_id, canonical_json(_selections_mapping(selections)), intake_json),
            )

    def start(self, snapshot: ProcessSnapshot, activity_id: str) -> RegistrationAssessment:
        """Start from service-persisted intake only; callers cannot supply facts."""
        project_id, intake, selections = self._saved_intake(activity_id)
        assessment = self.plugin.start_assessment(
            snapshot=snapshot, activity_id=activity_id, project_id=project_id,
            intake=intake, selections=selections,
        )
        assessment.bind_process_snapshot(snapshot)
        context = assessment.context
        rows = (
            ("project_architect", context.architect_run, context.routes.architect),
            ("fidelity_reviewer", context.reviewer_run, context.routes.fidelity_reviewer),
        )
        with self.database.transaction() as transaction:
            for role, run, route in rows:
                transaction.execute(
                    """INSERT INTO registration_assessment_runs(
                        activity_id, role, assignment_id, run_id, route_json, runtime_identity_json
                    ) VALUES (?, ?, ?, ?, ?, NULL)""",
                    (context.activity_id, role, run.assignment_id, run.run_id, canonical_json(_route_mapping(route))),
                )
            transaction.execute(
                "INSERT INTO registration_assessment_state(activity_id, state_json) VALUES (?, ?)",
                (context.activity_id, canonical_json(assessment.to_record())),
            )
        self._assessments[context.activity_id] = assessment
        return assessment

    def reserve_runtime_identity(
        self, activity_id: str, role: str,
    ) -> OperationIdentity:
        """Reserve the service-created run for protected identity publication."""
        assessment = self._assessment(activity_id)
        run = assessment.context.architect_run if role == "project_architect" else assessment.context.reviewer_run if role == "fidelity_reviewer" else None
        if run is None:
            raise RegistrationAssessmentError("registration role is invalid")
        route = assessment.context.routes.architect if role == "project_architect" else assessment.context.routes.fidelity_reviewer
        operation = OperationIdentity(assessment.context.project_id, activity_id, run.assignment_id, run.run_id)

        self.__supervisor_authority.reserve_runtime_identity(operation, route)
        return operation

    def submit_architect(self, response: RegistrationAgentResponse) -> object:
        assessment = self._assessment_for_response(response, "project_architect")
        result = self.registry.dispatch(
            _snapshot_for(assessment), "agent_session", assessment=assessment,
            response=response, running_identity=self._saved_identity(assessment, "project_architect"),
        )
        self._save_assessment(assessment)
        return result

    def submit_reviewer(self, response: RegistrationAgentResponse) -> object:
        assessment = self._assessment_for_response(response, "fidelity_reviewer")
        result = self.registry.dispatch(
            _snapshot_for(assessment), "review", assessment=assessment,
            response=response, running_identity=self._saved_identity(assessment, "fidelity_reviewer"),
        )
        self._save_assessment(assessment)
        return result

    def validate_package(self, activity_id: str, manifest: object, records: object) -> object:
        assessment = self._assessment(activity_id)
        return self.registry.dispatch(
            _snapshot_for(assessment), "saved_outputs", assessment=assessment, manifest=manifest, records=records,
        )

    def rehydrate(self, snapshot: ProcessSnapshot, activity_id: str) -> RegistrationAssessment:
        """Restore exact saved intake, routes, runs, and assessment state offline."""
        project_id, intake, _selections = self._saved_intake(activity_id)
        with self.database.read_connection() as connection:
            rows = connection.execute(
                "SELECT role, assignment_id, run_id, route_json FROM registration_assessment_runs WHERE activity_id = ?",
                (activity_id,),
            ).fetchall()
            state = connection.execute(
                "SELECT state_json FROM registration_assessment_state WHERE activity_id = ?", (activity_id,)
            ).fetchone()
        if len(rows) != 2 or state is None:
            raise RegistrationAssessmentError("saved registration assessment is incomplete")
        try:
            saved = {str(row[0]): (AssessmentRun(str(row[1]), str(row[2])), _route_from_mapping(json.loads(str(row[3])))) for row in rows}
            if set(saved) != {"project_architect", "fidelity_reviewer"}:
                raise ValueError
            context = AssessmentContext(
                project_id, activity_id, intake.inventory, _decision_version(intake), intake.selected_scope or "",
                "project_architect", "fidelity_reviewer", ResolvedRoleRoutes(saved["project_architect"][1], saved["fidelity_reviewer"][1]),
                saved["project_architect"][0], saved["fidelity_reviewer"][0], _package_context(project_id, intake),
                snapshot.definition.get("maximum_fidelity_reviews", 2),
            )
            assessment = RegistrationAssessment.from_record(context, json.loads(str(state[0])))
        except (TypeError, ValueError, json.JSONDecodeError) as error:
            raise RegistrationAssessmentError("saved registration assessment is invalid") from error
        assessment.bind_process_snapshot(snapshot)
        self._assessments[activity_id] = assessment
        return assessment

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
        if row is None:
            raise RegistrationAssessmentError("service has no saved runtime identity record for the current run")
        if row[0] is None:
            operation, route = self._operation_and_route(assessment, role)
            if self.__runtime_identity_consumer is None:
                raise RegistrationAssessmentError("protected runtime identity authority is unavailable")
            try:
                confirmed = self.__runtime_identity_consumer.consume(operation.key)
            except RuntimeIdentityProtocolError as error:
                raise RegistrationAssessmentError("service has no verified runtime identity for the current run") from error
            _persist_protected_runtime_identity(self.database, operation, route, confirmed)
            return self._saved_identity(assessment, role)
        try:
            value = json.loads(str(row[0]))
            return RunningToolIdentity(**value)
        except (TypeError, ValueError, json.JSONDecodeError) as error:
            raise RegistrationAssessmentError("saved runtime identity is invalid") from error

    @staticmethod
    def _operation_and_route(
        assessment: RegistrationAssessment, role: str,
    ) -> tuple[OperationIdentity, ResolvedAgentRoute]:
        context = assessment.context
        if role == "project_architect":
            run, route = context.architect_run, context.routes.architect
        elif role == "fidelity_reviewer":
            run, route = context.reviewer_run, context.routes.fidelity_reviewer
        else:
            raise RegistrationAssessmentError("registration role is invalid")
        return OperationIdentity(context.project_id, context.activity_id, run.assignment_id, run.run_id), route

    def _assessment(self, activity_id: str) -> RegistrationAssessment:
        try:
            return self._assessments[activity_id]
        except KeyError as error:
            raise RegistrationAssessmentError("registration assessment is unavailable for unsafe continuation") from error

    def _saved_intake(self, activity_id: str) -> tuple[str, RegistrationIntakeResult, RoleSelections]:
        with self.database.read_connection() as connection:
            row = connection.execute(
                "SELECT project_id, selections_json, intake_json FROM registration_assessment_intake WHERE activity_id = ?",
                (activity_id,),
            ).fetchone()
        if row is None:
            raise RegistrationAssessmentError("registration assessment has no saved intake")
        try:
            project_id = str(row[0])
            intake = RegistrationIntakeResult.from_json(str(row[2]))
            selections = _selections_from_mapping(json.loads(str(row[1])))
        except (TypeError, ValueError, json.JSONDecodeError) as error:
            raise RegistrationAssessmentError("saved registration intake is invalid") from error
        if intake.inventory is None:
            raise RegistrationAssessmentError("saved registration intake is incomplete")
        return project_id, intake, selections

    def _save_assessment(self, assessment: RegistrationAssessment) -> None:
        with self.database.transaction() as transaction:
            updated = transaction.execute(
                "UPDATE registration_assessment_state SET state_json = ? WHERE activity_id = ?",
                (canonical_json(assessment.to_record()), assessment.context.activity_id),
            )
            if updated.rowcount != 1:
                raise RegistrationAssessmentError("saved registration assessment state is unavailable")


def _identity_mapping(identity: RunningToolIdentity) -> dict[str, str]:
    return {
        "source": identity.source,
        "provider": identity.provider,
        "model_id": identity.model_id,
        "tool_version": identity.tool_version,
        "configuration_hash": identity.configuration_hash,
    }


def _persist_protected_runtime_identity(
    database: Database,
    reserved: OperationIdentity,
    route: ResolvedAgentRoute,
    confirmed: ConfirmedRuntimeIdentity,
) -> None:
    """Persist a one-time identity consumed from protected core authority."""
    if not isinstance(confirmed, ConfirmedRuntimeIdentity) or confirmed.operation_key != reserved.key:
        raise RegistrationAssessmentError("protected runtime identity differs from the reserved operation")
    try:
        identity = verify_running_identity(route, RunningToolIdentity(
            "tool_metadata", confirmed.provider, confirmed.model_id,
            confirmed.tool_version, confirmed.configuration_hash,
        ))
    except ValueError as error:
        raise RegistrationAssessmentError("protected runtime identity differs from the saved route") from error
    roles = {"architect": "project_architect", "fidelity_reviewer": "fidelity_reviewer"}
    try:
        role = roles[route.role]
    except KeyError as error:
        raise RegistrationAssessmentError("saved registration route role is invalid") from error
    with database.transaction() as transaction:
        updated = transaction.execute(
            """UPDATE registration_assessment_runs SET runtime_identity_json = ?
               WHERE activity_id = ? AND role = ? AND assignment_id = ? AND run_id = ?""",
            (
                canonical_json(_identity_mapping(identity)), reserved.activity_id,
                role, reserved.assignment_id, reserved.run_id,
            ),
        )
        if updated.rowcount != 1:
            raise RegistrationAssessmentError("runtime identity does not match a current saved assignment run")


def _snapshot_for(assessment: RegistrationAssessment) -> ProcessSnapshot:
    """The service binds dispatch to the exact snapshot supplied at start."""
    return assessment.process_snapshot


def registration_process_provider(
    configured_routes: ConfiguredAgentRouteProvider | None,
    preflight: AgentRoutePreflight | None = None,
) -> ProcessProvider:
    """Entry point used by the shared process registry at installation."""
    return RegistrationProcessPlugin(configured_routes, preflight).provider


def _new_run(role: str) -> AssessmentRun:
    token = uuid.uuid4().hex
    return AssessmentRun(f"{role}-{token}", f"{role}-{token}")


def _decision_version(intake: RegistrationIntakeResult) -> str:
    if not intake.selection_decision_ref:
        raise RegistrationAssessmentError("saved intake lacks a selection decision reference")
    return intake.selection_decision_ref


def _package_context(project_id: str, intake: RegistrationIntakeResult) -> RegistrationPackageContext:
    if intake.inventory is None or not intake.repository:
        raise RegistrationAssessmentError("saved intake lacks an authorized repository inventory")
    return RegistrationPackageContext.from_intake(
        project_id=project_id, source_repository=intake.repository, intake=intake,
        decision_version=_decision_version(intake), selection_decision_ref=_decision_version(intake),
    )


def _selections_mapping(value: RoleSelections) -> dict[str, dict[str, str]]:
    return {
        "architect": {"tool": value.architect.tool, "model_id": value.architect.model_id},
        "fidelity_reviewer": {"tool": value.fidelity_reviewer.tool, "model_id": value.fidelity_reviewer.model_id},
    }


def _selections_from_mapping(value: object) -> RoleSelections:
    if not isinstance(value, Mapping) or set(value) != {"architect", "fidelity_reviewer"}:
        raise ValueError("saved role selections are invalid")
    try:
        return RoleSelections(
            ToolModelSelection(**value["architect"]), ToolModelSelection(**value["fidelity_reviewer"]),
        )
    except (TypeError, ValueError) as error:
        raise ValueError("saved role selections are invalid") from error


def _route_mapping(route: ResolvedAgentRoute) -> dict[str, object]:
    return {
        "role": route.role, "tool": route.tool, "requested_model_id": route.requested_model_id,
        "provider": route.provider, "tool_version": route.tool_version, "executable": route.executable,
        "credential_profile": route.credential_profile, "settings_profile": route.settings_profile,
        "location": route.location, "capabilities": list(route.capabilities),
        "context_limit_tokens": route.context_limit_tokens,
        "permitted_destinations": [item.as_dict() for item in route.permitted_destinations],
        "configuration_hash": route.configuration_hash,
    }


def _route_from_mapping(value: object) -> ResolvedAgentRoute:
    if not isinstance(value, Mapping):
        raise ValueError("saved route is invalid")
    try:
        return ResolvedAgentRoute(
            role=value["role"], tool=value["tool"], requested_model_id=value["requested_model_id"],
            provider=value["provider"], tool_version=value["tool_version"], executable=value["executable"],
            credential_profile=value["credential_profile"], settings_profile=value["settings_profile"],
            location=value["location"], capabilities=tuple(value["capabilities"]),
            context_limit_tokens=value["context_limit_tokens"],
            permitted_destinations=tuple(PermittedDestination(**item) for item in value["permitted_destinations"]),
            configuration_hash=value["configuration_hash"],
        )
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError("saved route is invalid") from error
