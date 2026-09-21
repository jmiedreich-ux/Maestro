from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from maestro.agents.preflight import AgentRoutePreflight, ResolvedAgentRoute, ResolvedRoleRoutes, RunningToolIdentity
from maestro.agents.routes import ConfiguredAgentRouteProvider, RoleSelections, ToolModelSelection
from maestro.agents.supervisor import AgentSupervisor, FileSupervisorJournal, LaunchRequest, LocalProcessUnits, OperationIdentity
from maestro.foundation import StorageSettings
from maestro.planning.intake import RegistrationIntakeResult, _selection_decision_reference
from maestro.planning.registration import (
    AssessmentContext,
    AssessmentRun,
    RegistrationAssessment,
    RegistrationAssessmentError,
    validate_completion_mapping,
)
from maestro.planning.registration_records import (
    RegistrationAgentResponse,
    RegistrationRecordError,
    RegistrationPackageContext,
    package_content_hash,
    validate_registration_package,
)
from maestro.planning.sources import OutcomeReference, SourceBlob, SourceInventory, SourceReference
from maestro.planning.registration_plugin import RegistrationProcessPlugin
from maestro.service.authentication import OwnerAuthenticationSettings
from maestro.service.main import InstalledServiceApplication, ServiceSettings
from maestro.service.processes import ProcessSnapshot
from maestro.service.resources import BundleSnapshot
from tests.maestro.registration_package_fixture import complete_package


def _artifact(path: str, version: str) -> dict[str, str]:
    return {"path": path, "sha256": "a" * 64, "version": version}


def _response(role: str, *, outcome: str | None = None, blocker: bool = False, candidate: dict[str, str] | None = None) -> RegistrationAgentResponse:
    candidate = candidate or _artifact("candidate/manifest.json", "candidate-1")
    finding = {
        "local_key": "dependency", "subject": "Missing essential dependency", "severity": "blocking",
        "explanation": "The selected outcome needs an unavailable service.", "impact": "Registration cannot claim readiness.",
        "requested_correction": "Include it or explicitly narrow scope.", "source_refs": [], "affected_items": [],
        "missing_information": "No source evidence establishes the dependency.",
    }
    return RegistrationAgentResponse.from_mapping({
        "contract_version": 1, "assignment_id": f"{role}-assignment", "run_id": f"{role}-run", "project_id": "project-1",
        "activity_id": "activity-1", "role": role, "source_commit": "b" * 40, "decision_version": "decision-1",
        "result": "completed", "summary": "Assessment response.", "findings": [finding] if blocker else [], "questions": [],
        "candidate": candidate, "assessment": _artifact("assessment.json", "assessment-1") if role == "project_architect" else None,
        "reviewed_assessment": _artifact("assessment.json", "assessment-1") if role == "fidelity_reviewer" else None,
        "review_outcome": outcome if role == "fidelity_reviewer" else None, "failure": None,
    })


class RegistrationAssessmentTest(unittest.TestCase):
    def _assessment(self, limit: int = 2) -> RegistrationAssessment:
        blob = SourceBlob.from_bytes("docs/overview.md", b"# Overview\n")
        inventory = SourceInventory(
            "refs/heads/main", "b" * 40, "docs/overview.md", (blob,),
            source_references=(SourceReference("Architecture", "Overview", "docs/overview.md"),),
            outcomes=(OutcomeReference("APP", 1, "APP-PM1", "Start", 1),),
        )
        route = ResolvedAgentRoute("architect", "codex", "openai/model-1", "openai", "1", "/tool", "credential", "settings", "cloud", ("code_edit", "local_command", "repository_search", "approved_network"), 65536, (), "c" * 64)
        reviewer = replace(route, role="fidelity_reviewer", tool="claude_code", requested_model_id="anthropic/model-1", provider="anthropic")
        package_context = RegistrationPackageContext(
            "project-1", "owner/project", inventory, "decision-1", "main", "c" * 64,
            "decision/source-selection-1",
        )
        return RegistrationAssessment(AssessmentContext(
            "project-1", "activity-1", inventory, "decision-1", "APP-PM1", "architect-agent", "reviewer-agent",
            ResolvedRoleRoutes(route, reviewer),
            AssessmentRun("project_architect-assignment", "project_architect-run"),
            AssessmentRun("fidelity_reviewer-assignment", "fidelity_reviewer-run"), package_context, limit,
        ))

    @staticmethod
    def _identity(role: str) -> RunningToolIdentity:
        if role == "project_architect":
            return RunningToolIdentity("tool_metadata", "openai", "openai/model-1", "1", "c" * 64)
        return RunningToolIdentity("tool_metadata", "anthropic", "anthropic/model-1", "1", "c" * 64)

    def _configured_routes(self) -> ConfiguredAgentRouteProvider:
        """A configured provider fixture; live inspection is isolated below."""
        provider = object.__new__(ConfiguredAgentRouteProvider)
        provider._registry = type("Routes", (), {"resolve": lambda _self, selection: selection})()
        return provider

    def _saved_intake(self) -> RegistrationIntakeResult:
        inventory = self._assessment().context.source_inventory
        snapshot = {"repository": "owner/project", "branch": "main", "binding_id": "binding-1"}
        snapshot_reference = hashlib.sha256(json.dumps(snapshot, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        decision = _selection_decision_reference(
            "owner/project", "supplied", inventory.source_ref, inventory.source_commit,
            inventory.overview_path, "main", snapshot_reference, "b" * 40,
        )
        return RegistrationIntakeResult(
            inventory, (), "binding-1", "APP-PM1", "supplied", snapshot_reference,
            {"decision": "allowed", "snapshot": snapshot, "observed_at": 1, "evidence_hashes": {}, "reason": None},
            inventory.source_ref, "main", None, "owner/project", decision, "b" * 40,
        )

    def test_exact_assessment_and_independent_review_make_ready_candidate(self) -> None:
        assessment = self._assessment()
        assessment.submit_architect(_response("project_architect"), self._identity("project_architect"))
        status = assessment.submit_reviewer(_response("fidelity_reviewer", outcome="APPROVE"), self._identity("fidelity_reviewer"))
        self.assertEqual("ready", status.state)
        self.assertTrue(status.execution_eligible)
        self.assertEqual("candidate/manifest.json", assessment.require_ready_candidate().path)

    def test_missing_essential_mapping_and_exhausted_material_review_block_readiness(self) -> None:
        assessment = self._assessment(limit=1)
        with self.assertRaisesRegex(RegistrationAssessmentError, "completion requirement"):
            validate_completion_mapping(assessment.context.source_inventory, ("APP-PM1",), ())
        assessment.submit_architect(_response("project_architect"), self._identity("project_architect"))
        status = assessment.submit_reviewer(_response("fidelity_reviewer", outcome="REQUEST_CHANGES", blocker=True), self._identity("fidelity_reviewer"))
        self.assertEqual("review_limit_owner_decision", status.state)
        self.assertFalse(status.execution_eligible)
        with self.assertRaisesRegex(RegistrationAssessmentError, "not eligible"):
            assessment.require_ready_candidate()

    def test_one_owner_grant_adds_exactly_one_review_without_resetting_use(self) -> None:
        assessment = self._assessment(limit=1)
        assessment.submit_architect(
            _response("project_architect"), self._identity("project_architect")
        )
        first = assessment.submit_reviewer(
            _response("fidelity_reviewer", outcome="REQUEST_CHANGES", blocker=True),
            self._identity("fidelity_reviewer"),
        )
        self.assertEqual("review_limit_owner_decision", first.state)
        granted = assessment.grant_one_review()
        self.assertEqual((1, 1, 2), (
            granted.review_count, granted.review_grants, granted.review_limit
        ))
        with self.assertRaisesRegex(RegistrationAssessmentError, "not waiting"):
            assessment.grant_one_review()
        assessment.continue_after_review(
            AssessmentRun("project_architect-assignment", "project_architect-run-2")
        )
        amended = replace(
            _response("project_architect"),
            run_id="project_architect-run-2",
            candidate=type(_response("project_architect").candidate)(
                "candidate/manifest-2.json", "a" * 64, "candidate-2"
            ),
        )
        assessment.submit_architect(amended, self._identity("project_architect"))
        assessment.set_current_run(
            "fidelity_reviewer",
            AssessmentRun("fidelity_reviewer-assignment", "fidelity_reviewer-run-2"),
        )
        second_review = replace(
            _response(
                "fidelity_reviewer",
                outcome="REQUEST_CHANGES",
                blocker=True,
                candidate=_artifact("candidate/manifest-2.json", "candidate-2"),
            ),
            run_id="fidelity_reviewer-run-2",
        )
        exhausted = assessment.submit_reviewer(
            second_review, self._identity("fidelity_reviewer")
        )
        self.assertEqual("review_limit_owner_decision", exhausted.state)
        self.assertEqual(2, exhausted.review_count)

    def test_exhausted_updated_source_review_resumes_at_reviewer_after_grant(self) -> None:
        previous = self._assessment(limit=1)
        previous.submit_architect(
            _response("project_architect"), self._identity("project_architect")
        )
        previous.submit_reviewer(
            _response("fidelity_reviewer", outcome="APPROVE"),
            self._identity("fidelity_reviewer"),
        )
        replacement = self._assessment(limit=1)
        replacement.carry_review_accounting_from(previous)
        replacement.submit_architect(
            _response("project_architect"), self._identity("project_architect")
        )
        paused = replacement.pause_for_review_limit()
        self.assertEqual("review_limit_owner_decision", paused.state)
        granted = replacement.grant_one_review()
        self.assertEqual("awaiting_reviewer", granted.state)
        self.assertEqual((1, 1, 2), (
            granted.review_count, granted.review_grants, granted.review_limit
        ))

    def test_reviewer_must_cover_exact_immutable_architect_artifacts(self) -> None:
        assessment = self._assessment()
        assessment.submit_architect(_response("project_architect"), self._identity("project_architect"))
        with self.assertRaisesRegex(RegistrationAssessmentError, "exact assigned"):
            assessment.submit_reviewer(_response("fidelity_reviewer", outcome="APPROVE", candidate=_artifact("candidate/other.json", "candidate-2")), self._identity("fidelity_reviewer"))

    def test_response_requires_current_run_and_verified_tool_identity(self) -> None:
        assessment = self._assessment()
        response = _response("project_architect")
        stale = replace(response, run_id="previous-run")
        with self.assertRaisesRegex(RegistrationAssessmentError, "current assigned run"):
            assessment.submit_architect(stale, self._identity("project_architect"))
        unverified = replace(self._identity("project_architect"), source="agent_text")
        with self.assertRaisesRegex(RegistrationAssessmentError, "verified exact running tool identity"):
            assessment.submit_architect(response, unverified)

    def test_package_manifest_hashes_exact_record_bytes(self) -> None:
        context = RegistrationPackageContext(
            "project-1", "owner/project", self._assessment().context.source_inventory, "decision-1", "main", "c" * 64,
            "decision/source-selection-1",
        )
        manifest, records = complete_package(
            context, registration_version=1, candidate_id="candidate-1"
        )
        self.assertIs(validate_registration_package(manifest, records, context), manifest)
        manifest["content_hash"] = "0" * 64
        with self.assertRaisesRegex(RegistrationRecordError, "content_hash"):
            validate_registration_package(manifest, records, context)

    def test_package_rejects_context_substitution_and_duplicate_record_id(self) -> None:
        context = RegistrationPackageContext("project-1", "owner/project", self._assessment().context.source_inventory, "decision-1", "main", "c" * 64, "decision/source-selection-1")
        manifest, records = complete_package(
            context, registration_version=1, candidate_id="candidate-1"
        )
        duplicate = dict(records["summary.json"])
        records["also-summary.json"] = duplicate
        manifest["files"].append({
            "path": "also-summary.json",
            "record_id": duplicate["record_id"],
            "record_type": duplicate["record_type"],
            "record_version": duplicate["record_version"],
            "subject": duplicate["subject"],
            "sha256": hashlib.sha256(
                json.dumps(duplicate, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
            ).hexdigest(),
        })
        manifest["content_hash"] = package_content_hash(records)
        with self.assertRaisesRegex(RegistrationRecordError, "record_id"):
            validate_registration_package(manifest, records, context)
        manifest, records = complete_package(
            context, registration_version=1, candidate_id="candidate-1"
        )
        manifest["source_commit"] = "d" * 40
        with self.assertRaisesRegex(RegistrationRecordError, "source_commit"):
            validate_registration_package(manifest, records, context)

    def test_package_rejects_missing_typed_topology_and_unknown_manifest_fields(self) -> None:
        context = self._assessment().context.package_context
        manifest, records = complete_package(
            context, registration_version=1, candidate_id="candidate-1"
        )
        requirement_path = next(
            path for path, record in records.items()
            if record["record_type"] == "requirement"
        )
        del records[requirement_path]
        manifest["files"] = [
            item for item in manifest["files"]
            if item["path"] != requirement_path
        ]
        manifest["content_hash"] = package_content_hash(records)
        with self.assertRaisesRegex(RegistrationRecordError, "requirement"):
            validate_registration_package(manifest, records, context)
        manifest, records = complete_package(
            context, registration_version=1, candidate_id="candidate-1"
        )
        manifest["agent_readiness"] = True
        with self.assertRaisesRegex(RegistrationRecordError, "manifest fields"):
            validate_registration_package(manifest, records, context)

    def test_process_provider_rejects_caller_supplied_assessment_facts(self) -> None:
        plugin = RegistrationProcessPlugin(self._configured_routes())
        snapshot = ProcessSnapshot("registration", "{}", "a" * 64, BundleSnapshot("registration-process@1", "processDefinition", (("schema.json", "a" * 64),)))
        with self.assertRaisesRegex(RegistrationAssessmentError, "installed service binding"):
            plugin.provider.handlers["initiation"]["registration_intake_or_idle_update"](
                snapshot, intake=self._saved_intake(), source_repository="owner/project", decision_version="forged"
            )

    def test_installed_service_composes_non_interchangeable_runtime_identity_capabilities(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            settings = ServiceSettings(
                StorageSettings.from_mapping({"path": f"{temporary}/maestro.sqlite3"}),
                OwnerAuthenticationSettings("owner-local", "a" * 64),
                agent_route_provider=self._configured_routes(),
            )
            application = InstalledServiceApplication(settings, supervisor_units=LocalProcessUnits())
            self.assertTrue(callable(application.agent_supervisor._runtime_identity_reporter.publish))
            self.assertFalse(hasattr(application, "runtime_identity_core"))
            self.assertFalse(hasattr(application, "runtime_identity_server"))
            self.assertFalse(hasattr(application, "runtime_identity_socket"))
            self.assertFalse(hasattr(application.agent_supervisor._runtime_identity_reporter, "consume"))
            application.stop()

    def test_service_rehydrates_saved_intake_and_rejects_forged_runtime_delivery(self) -> None:
        baseline = self._assessment()
        preflight = object.__new__(AgentRoutePreflight)
        preflight.resolve_process_roles = lambda *_args: baseline.context.routes
        with tempfile.TemporaryDirectory() as temporary:
            settings = ServiceSettings(
                StorageSettings.from_mapping({"path": f"{temporary}/maestro.sqlite3"}),
                OwnerAuthenticationSettings("owner-local", "a" * 64),
                agent_route_provider=self._configured_routes(),
            )
            application = InstalledServiceApplication(
                settings, preflight, supervisor_units=LocalProcessUnits(),
            )
            assert application.registration_assessment is not None
            supervisor = application.agent_supervisor
            definition = {
                "maximum_fidelity_reviews": 2,
                "initiation": {"policy": "registration_intake_or_idle_update"},
                "agent_session": {"policy": "fixed_assignment_followups"},
                "saved_outputs": {"policy": "versioned_registration_package"},
                "review": {"policy": "bounded_independent_fidelity"},
                "confirmation": {"policy": "explicit_exact_candidate_activation"},
                "recovery": {"policy": "reconcile_preserved_registration"},
            }
            snapshot = ProcessSnapshot("registration", json.dumps(definition), "a" * 64, BundleSnapshot("registration-process@1", "processDefinition", (("schema.json", "a" * 64),)))
            binding = application.registration_assessment
            self.assertIs(binding.supervisor, application.agent_supervisor)
            intake = self._saved_intake()
            selections = RoleSelections(ToolModelSelection("codex", "openai/model-1"), ToolModelSelection("claude_code", "anthropic/model-1"))
            binding.save_intake("activity-1", "project-1", intake, selections)
            started = binding.start(snapshot, "activity-1")
            manifest, records = complete_package(
                started.context.package_context,
                registration_version=1,
                candidate_id="candidate-1",
            )
            self.assertIs(binding.validate_package("activity-1", manifest, records), manifest)
            manifest["publication_branch"] = "wrong-branch"
            with self.assertRaisesRegex(RegistrationRecordError, "publication_branch"):
                binding.validate_package("activity-1", manifest, records)
            architect_operation = OperationIdentity("project-1", "activity-1", started.context.architect_run.assignment_id, started.context.architect_run.run_id)
            self.assertFalse(hasattr(binding, "reserve_runtime_identity_callback"))
            self.assertFalse(hasattr(supervisor, "runtime_identity_callback"))
            self.assertEqual(architect_operation, binding.reserve_runtime_identity("activity-1", "project_architect"))
            alternate = AgentSupervisor(
                FileSupervisorJournal(Path(temporary) / "alternate-supervisor.json"), LocalProcessUnits(),
            )
            with self.assertRaisesRegex(AttributeError, "has no setter"):
                binding.supervisor = alternate
            with self.assertRaisesRegex(AttributeError, "authority is immutable"):
                setattr(binding, "_RegistrationServiceBinding__supervisor_authority", alternate)
            self.assertIs(binding.supervisor, application.agent_supervisor)
            with application.database.read_connection() as connection:
                self.assertEqual(0, connection.execute("SELECT COUNT(*) FROM registration_assessment_runs WHERE runtime_identity_json IS NOT NULL").fetchone()[0])
            supervisor.launch(LaunchRequest(architect_operation, ("/bin/sh", "-c", "sleep 5"), temporary, 5, 2))
            supervisor.report_runtime_identity(architect_operation, self._identity("project_architect"))
            architect = replace(_response("project_architect"), assignment_id=started.context.architect_run.assignment_id, run_id=started.context.architect_run.run_id, decision_version=intake.selection_decision_ref)
            binding.submit_architect(architect)
            recovered = binding.rehydrate(snapshot, "activity-1")
            self.assertEqual("awaiting_reviewer", recovered.status.state)
            reviewer_operation = OperationIdentity("project-1", "activity-1", recovered.context.reviewer_run.assignment_id, recovered.context.reviewer_run.run_id)
            self.assertEqual(reviewer_operation, binding.reserve_runtime_identity("activity-1", "fidelity_reviewer"))
            supervisor.launch(LaunchRequest(reviewer_operation, ("/bin/sh", "-c", "sleep 5"), temporary, 5, 2))
            supervisor.report_runtime_identity(reviewer_operation, self._identity("fidelity_reviewer"))
            reviewer = replace(_response("fidelity_reviewer", outcome="APPROVE"), assignment_id=recovered.context.reviewer_run.assignment_id, run_id=recovered.context.reviewer_run.run_id, decision_version=intake.selection_decision_ref)
            status = binding.submit_reviewer(reviewer)
            self.assertTrue(status.execution_eligible)
            with application.database.read_connection() as connection:
                self.assertEqual(2, connection.execute("SELECT COUNT(*) FROM registration_assessment_runs WHERE runtime_identity_json IS NOT NULL").fetchone()[0])
            supervisor.stop(architect_operation, "test_complete")
            supervisor.stop(reviewer_operation, "test_complete")


if __name__ == "__main__":
    unittest.main()
