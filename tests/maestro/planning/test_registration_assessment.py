from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from dataclasses import replace

from maestro.agents.preflight import AgentRoutePreflight, ResolvedAgentRoute, ResolvedRoleRoutes, RunningToolIdentity
from maestro.agents.routes import RoleSelections, ToolModelSelection
from maestro.agents.supervisor import OperationIdentity
from maestro.foundation import StorageSettings
from maestro.planning.intake import RegistrationIntakeResult
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
from maestro.planning.sources import OutcomeReference, SourceBlob, SourceInventory
from maestro.planning.registration_plugin import RegistrationProcessPlugin
from maestro.service.authentication import OwnerAuthenticationSettings
from maestro.service.main import InstalledServiceApplication, ServiceSettings
from maestro.service.processes import ProcessSnapshot
from maestro.service.resources import BundleSnapshot


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
        inventory = SourceInventory("refs/heads/main", "b" * 40, "docs/overview.md", (blob,), outcomes=(OutcomeReference("APP", 1, "APP-PM1", "Start", 1),))
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
        record = {"schema_version": 1, "record_type": "summary", "record_id": "summary-1", "subject": "Project summary", "record_version": 1, "data": {"purpose": "Start"}}
        records = {"summary.json": record}
        file_hash = hashlib.sha256(json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()
        manifest = {
            "project_id": "project-1", "registration_version": 1, "candidate_id": "candidate-1", "previous_registration_ref": None,
            "source_repository": "owner/project", "source_commit": "b" * 40, "overview_path": "docs/overview.md", "decision_version": "decision-1",
            "source_ref": "refs/heads/main", "publication_branch": "main", "destination_snapshot_reference": "c" * 64,
            "selection_decision_ref": "decision/source-selection-1",
            "content_hash": package_content_hash(records),
            "files": [{"path": "summary.json", "record_id": "summary-1", "record_type": "summary", "record_version": 1, "subject": "Project summary", "sha256": file_hash}],
        }
        context = RegistrationPackageContext(
            "project-1", "owner/project", self._assessment().context.source_inventory, "decision-1", "main", "c" * 64,
            "decision/source-selection-1",
        )
        self.assertIs(validate_registration_package(manifest, records, context), manifest)
        manifest["content_hash"] = "0" * 64
        with self.assertRaisesRegex(RegistrationRecordError, "content_hash"):
            validate_registration_package(manifest, records, context)

    def test_package_rejects_context_substitution_and_duplicate_record_id(self) -> None:
        record = {"schema_version": 1, "record_type": "summary", "record_id": "summary-1", "subject": "Project summary", "record_version": 1, "data": {}}
        second = dict(record)
        records = {"summary.json": record, "also-summary.json": second}
        entry_hash = hashlib.sha256(json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()
        manifest = {
            "project_id": "project-1", "registration_version": 1, "candidate_id": "candidate-1", "previous_registration_ref": None,
            "source_repository": "owner/project", "source_commit": "b" * 40, "overview_path": "docs/overview.md", "decision_version": "decision-1",
            "source_ref": "refs/heads/main", "publication_branch": "main", "destination_snapshot_reference": "c" * 64,
            "selection_decision_ref": "decision/source-selection-1", "content_hash": package_content_hash(records),
            "files": [
                {"path": path, "record_id": "summary-1", "record_type": "summary", "record_version": 1, "subject": "Project summary", "sha256": entry_hash}
                for path in records
            ],
        }
        context = RegistrationPackageContext("project-1", "owner/project", self._assessment().context.source_inventory, "decision-1", "main", "c" * 64, "decision/source-selection-1")
        with self.assertRaisesRegex(RegistrationRecordError, "record_id"):
            validate_registration_package(manifest, records, context)
        manifest["source_commit"] = "d" * 40
        with self.assertRaisesRegex(RegistrationRecordError, "source_commit"):
            validate_registration_package(manifest, {"summary.json": record}, context)

    def test_process_provider_dispatches_start_and_both_response_roles(self) -> None:
        baseline = self._assessment()
        preflight = object.__new__(AgentRoutePreflight)
        preflight.resolve_process_roles = lambda *_args: baseline.context.routes
        plugin = RegistrationProcessPlugin(preflight)
        snapshot = ProcessSnapshot("registration", "{}", "a" * 64, BundleSnapshot("registration-process@1", "processDefinition", (("schema.json", "a" * 64),)))
        intake = RegistrationIntakeResult(baseline.context.source_inventory, (), "binding-1", "APP-PM1", "supplied", "snapshot-1", {"decision": "allowed"}, "refs/heads/main", "main")
        started = plugin.provider.handlers["initiation"]["registration_intake_or_idle_update"](
            snapshot, intake=intake, selections=RoleSelections(ToolModelSelection("codex", "openai/model-1"), ToolModelSelection("claude_code", "anthropic/model-1")),
            project_id="project-1", activity_id="activity-1", decision_version="decision-1", architect_identity="architect-agent", reviewer_identity="reviewer-agent",
            architect_assignment_id="project_architect-assignment", architect_run_id="project_architect-run", reviewer_assignment_id="fidelity_reviewer-assignment", reviewer_run_id="fidelity_reviewer-run",
            source_repository="owner/project", selection_decision_ref="decision/source-selection-1",
        )
        self.assertIsInstance(started, RegistrationAssessment)
        plugin.provider.handlers["agent_session"]["fixed_assignment_followups"](snapshot, assessment=started, response=_response("project_architect"), running_identity=self._identity("project_architect"))
        status = plugin.provider.handlers["review"]["bounded_independent_fidelity"](snapshot, assessment=started, response=_response("fidelity_reviewer", outcome="APPROVE"), running_identity=self._identity("fidelity_reviewer"))
        self.assertTrue(status.execution_eligible)

    def test_installed_service_binds_durable_runs_and_dispatches_without_identity_arguments(self) -> None:
        baseline = self._assessment()
        preflight = object.__new__(AgentRoutePreflight)
        preflight.resolve_process_roles = lambda *_args: baseline.context.routes
        with tempfile.TemporaryDirectory() as temporary:
            settings = ServiceSettings(
                StorageSettings.from_mapping({"path": f"{temporary}/maestro.sqlite3"}),
                OwnerAuthenticationSettings("owner-local", "a" * 64),
            )
            application = InstalledServiceApplication(settings, RegistrationProcessPlugin(preflight))
            assert application.registration_assessment is not None
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
            intake = RegistrationIntakeResult(baseline.context.source_inventory, (), "binding-1", "APP-PM1", "supplied", "c" * 64, {"decision": "allowed"}, "refs/heads/main", "main")
            binding = application.registration_assessment
            binding.start(
                snapshot, intake=intake, selections=RoleSelections(ToolModelSelection("codex", "openai/model-1"), ToolModelSelection("claude_code", "anthropic/model-1")),
                project_id="project-1", activity_id="activity-1", decision_version="decision-1", architect_identity="architect-agent", reviewer_identity="reviewer-agent",
                architect_assignment_id="project_architect-assignment", architect_run_id="project_architect-run", reviewer_assignment_id="fidelity_reviewer-assignment", reviewer_run_id="fidelity_reviewer-run",
                source_repository="owner/project", selection_decision_ref="decision/source-selection-1",
            )
            record = {"schema_version": 1, "record_type": "summary", "record_id": "summary-1", "subject": "Project summary", "record_version": 1, "data": {}}
            record_hash = hashlib.sha256(json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()
            manifest = {
                "project_id": "project-1", "registration_version": 1, "candidate_id": "candidate-1", "previous_registration_ref": None,
                "source_repository": "owner/project", "source_commit": "b" * 40, "overview_path": "docs/overview.md", "decision_version": "decision-1",
                "source_ref": "refs/heads/main", "publication_branch": "main", "destination_snapshot_reference": "c" * 64,
                "selection_decision_ref": "decision/source-selection-1", "content_hash": package_content_hash({"summary.json": record}),
                "files": [{"path": "summary.json", "record_id": "summary-1", "record_type": "summary", "record_version": 1, "subject": "Project summary", "sha256": record_hash}],
            }
            self.assertIs(binding.validate_package("activity-1", manifest, {"summary.json": record}), manifest)
            manifest["publication_branch"] = "wrong-branch"
            with self.assertRaisesRegex(RegistrationRecordError, "publication_branch"):
                binding.validate_package("activity-1", manifest, {"summary.json": record})
            binding.record_runtime_identity(OperationIdentity("project-1", "activity-1", "project_architect-assignment", "project_architect-run"), self._identity("project_architect"))
            binding.submit_architect(_response("project_architect"))
            binding.record_runtime_identity(OperationIdentity("project-1", "activity-1", "fidelity_reviewer-assignment", "fidelity_reviewer-run"), self._identity("fidelity_reviewer"))
            status = binding.submit_reviewer(_response("fidelity_reviewer", outcome="APPROVE"))
            self.assertTrue(status.execution_eligible)
            with application.database.read_connection() as connection:
                self.assertEqual(2, connection.execute("SELECT COUNT(*) FROM registration_assessment_runs WHERE runtime_identity_json IS NOT NULL").fetchone()[0])


if __name__ == "__main__":
    unittest.main()
