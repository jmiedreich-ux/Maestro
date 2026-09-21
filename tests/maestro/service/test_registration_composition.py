from __future__ import annotations

import hashlib
import io
import json
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from maestro.agents.preflight import (
    AdapterObservation,
    AgentRoutePreflight,
    InstalledAdapter,
    RunningToolIdentity,
)
from maestro.agents.routes import (
    AgentRouteRegistry,
    ConfiguredAgentRouteProvider,
    PermittedDestination,
    ToolRoute,
)
from maestro.agents.supervisor import (
    LaunchRequest,
    LocalProcessUnits,
    SupervisionError,
)
from maestro.foundation import StorageSettings, canonical_json
from maestro.foundation.credentials import (
    GitHubAppCredential,
    RepositoryAuthorizer,
    RepositoryBinding,
    RepositoryProfile,
    ServiceGitRoute,
    ServiceGitTransport,
)
from maestro.foundation.github_destination import (
    BranchPolicyObservation,
    GitHubAppDestinationProfile,
    GitHubDestinationProvider,
    GitHubDestinationRouter,
    GitHubInstallationToken,
    GitHubRestDestinationApi,
)
from maestro.planning.registration_confirmation import (
    ConfirmationReference,
    ConfirmationResult,
    RegistrationConfirmationService,
    RegistrationPackageReference,
)
from maestro.planning.intake import RegistrationIntakeResult
from maestro.planning.registration_recovery import RegistrationRecoveryService
from maestro.planning.registration_records import (
    ArtifactReference,
    RegistrationAgentResponse,
)
from maestro.planning.sources import (
    ExactSourceReader,
    OutcomeReference,
    SourceBlob,
    SourceInventory,
    SourceReference,
)
from maestro.service.activities import ActivityAction, ActivityRecord, ProjectRecord
from maestro.service.authentication import OwnerAuthenticationSettings
from maestro.service.events import EventStreamService
from maestro.service.installed_registration import InstalledToolInspector
from maestro.service.main import (
    InstalledServiceApplication,
    ServiceSettings,
    build_application,
    load_settings,
)
from maestro.service.processes import ProcessSnapshot
from maestro.service.registration import (
    RegistrationCoordinator,
    RegistrationRuntimeDependencies,
)
from maestro.service.registration_agents import InstalledRegistrationAgentLauncher
from maestro.service.resources import BundleSnapshot
from maestro.terminal.main import TerminalApplication
from tests.maestro.registration_package_fixture import complete_package


OWNER_TOKEN = "c" * 64


class _DestinationApi:
    def __init__(self, head: str = "a" * 40) -> None:
        self.head = head

    def app_identity(self, _profile):
        return {"id": 1, "slug": "maestro"}

    def installation_identity(self, _profile):
        return {"id": 2, "app_id": 1}

    def installation_token(self, _profile):
        return GitHubInstallationToken(
            "installation-token",
            {"contents": "write", "administration": "read"},
            time.time() + 300,
        )

    def repository_identity(self, _token, repository):
        return {"full_name": repository}

    def branch_identity(self, _token, _repository, branch):
        return {"name": branch, "commit": {"sha": self.head}}

    def branch_policy(self, _token, _repository, _branch):
        return BranchPolicyObservation(False, ())


class _TerminalConnection:
    client = object()

    def subscribe(self, callback):
        self.callback = callback


class _Inspector:
    def inspect(self, route, configuration_hash):
        return AdapterObservation(
            True,
            "1.0",
            "openai",
            tuple(route.allowed_model_ids),
            (),
            (
                "code_edit",
                "local_command",
                "repository_search",
                "approved_network",
            ),
            "cloud",
            {model_id: 65536 for model_id in route.allowed_model_ids},
            True,
            route.credential_profile,
            route.settings_profile,
            True,
            True,
            True,
            configuration_hash,
        )


class InstalledRegistrationCompositionTest(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        (self.root / "workspaces").mkdir()
        self.settings = ServiceSettings(
            StorageSettings(path=self.root / "maestro.sqlite3"),
            OwnerAuthenticationSettings(
                "owner-local", hashlib.sha256(OWNER_TOKEN.encode("ascii")).hexdigest()
            ),
            workspace_root=self.root / "workspaces",
        )

    def test_architect_amendment_assignment_carries_exact_parent_artifacts(self) -> None:
        application = InstalledServiceApplication(self.settings)
        project_id = "project-one"
        activity_id = "activity-one"
        prior_run_id = "project-architect-run-one"
        current_run = SimpleNamespace(
            assignment_id="project-architect-assignment-two",
            run_id="project-architect-run-two",
        )
        candidate_record = b'{"record":"one"}\n'
        candidate_bytes = canonical_json({
            "files": [{
                "path": "summary.json",
                "sha256": hashlib.sha256(candidate_record).hexdigest(),
            }]
        }).encode()
        assessment_bytes = b'{"assessment":"one"}\n'
        prior_output = (
            self.settings.workspace_root / project_id / activity_id
            / "runs" / prior_run_id / "output"
        )
        (prior_output / "candidate").mkdir(parents=True)
        (prior_output / "candidate" / "manifest.json").write_bytes(candidate_bytes)
        (prior_output / "candidate" / "summary.json").write_bytes(candidate_record)
        (prior_output / "assessment.json").write_bytes(assessment_bytes)
        candidate = ArtifactReference(
            "output/candidate/manifest.json",
            hashlib.sha256(candidate_bytes).hexdigest(),
            "candidate-one",
        )
        prior_assessment = ArtifactReference(
            "output/assessment.json",
            hashlib.sha256(assessment_bytes).hexdigest(),
            "assessment-one",
        )
        inventory = SourceInventory(
            "a" * 40,
            "a" * 40,
            "docs/overview.md",
            (SourceBlob.from_bytes("docs/overview.md", b"# Overview\n"),),
        )
        assessment = mock.Mock()
        assessment.context = SimpleNamespace(
            project_id=project_id,
            activity_id=activity_id,
            source_inventory=inventory,
            selected_scope="APP-PM1 — Register the project",
            decision_version="decision-one",
            routes=SimpleNamespace(architect=object(), fidelity_reviewer=object()),
            package_context=SimpleNamespace(
                source_repository="owner/project",
                publication_branch="main",
                scope_boundary=SimpleNamespace(as_dict=lambda: {
                    "confirmed": True,
                    "included_outcomes": ["APP-PM1"],
                }),
            ),
            review_limit=2,
        )
        assessment.current_run.return_value = current_run
        assessment.status = SimpleNamespace(
            candidate=candidate,
            assessment=prior_assessment,
        )
        assessment.to_record.return_value = {
            "architect_findings": [], "review_findings": []
        }
        assessment.process_snapshot = SimpleNamespace(
            definition={
                "architect": {"run_timeout_seconds": 1800},
                "fidelity_reviewer": {"run_timeout_seconds": 1800},
                "saved_outputs": {"root": ".maestro/registrations"},
            }
        )
        binding = SimpleNamespace(
            database=application.database,
            candidate_manifest_values=lambda _assessment: {
                "project_id": project_id,
                "registration_version": 1,
                "candidate_id": current_run.assignment_id,
                "previous_registration_ref": None,
                "source_repository": "owner/project",
                "source_commit": "a" * 40,
                "overview_path": "docs/overview.md",
                "decision_version": "decision-one",
                "source_ref": "a" * 40,
                "publication_branch": "main",
                "destination_snapshot_reference": "b" * 64,
                "selection_decision_ref": "decision-one",
                "scope_boundary": {
                    "confirmed": True,
                    "included_outcomes": ["APP-PM1"],
                },
            },
            assignment_lineage=lambda _assessment, _role: {
                "parent_assignment_id": "project-architect-assignment-one",
                "continuation_question_id": None,
                "previous_answer_id": None,
            },
            assignment_runs=lambda _assessment, _role: (
                current_run.run_id, prior_run_id
            ),
        )
        launcher = object.__new__(InstalledRegistrationAgentLauncher)
        launcher.workspaces = SimpleNamespace(root=self.settings.workspace_root)

        assignment, inputs, originals = launcher._assignment(
            binding, assessment, "project_architect"
        )

        self.assertEqual(
            "project-architect-assignment-one", assignment.parent_assignment_id
        )
        self.assertEqual(
            {"prior_candidate", "prior_assessment"},
            set(assignment.assigned_artifacts),
        )
        self.assertEqual(candidate_bytes, inputs["prior_candidate/manifest.json"])
        self.assertEqual(candidate_record, inputs["prior_candidate/summary.json"])
        self.assertIn("contract/registration-package-v1.json", inputs)
        self.assertEqual(assessment_bytes, inputs["prior_assessment/assessment.json"])
        self.assertEqual(candidate, originals["prior_candidate"])
        self.assertEqual(prior_assessment, originals["prior_assessment"])

        saved_status = assessment.status
        saved_lineage = binding.assignment_lineage
        assessment.status = SimpleNamespace(candidate=None, assessment=None)
        binding.assignment_lineage = lambda _assessment, _role: {
            "parent_assignment_id": None,
            "continuation_question_id": None,
            "previous_answer_id": None,
        }
        initial_assignment, initial_inputs, _initial_originals = launcher._assignment(
            binding, assessment, "project_architect"
        )
        self.assertEqual({}, initial_assignment.assigned_artifacts)
        self.assertEqual(
            "input/contract/registration-package-v1.json",
            initial_assignment.instructions["package_contract_path"],
        )
        self.assertIn("contract/registration-package-v1.json", initial_inputs)
        self.assertEqual(
            current_run.assignment_id,
            initial_assignment.instructions["candidate_manifest_values"]["candidate_id"],
        )
        assessment.status = saved_status
        binding.assignment_lineage = saved_lineage

        review_assignment, review_inputs, _review_originals = launcher._assignment(
            binding, assessment, "fidelity_reviewer"
        )
        self.assertEqual(
            {"candidate", "reviewed_assessment"},
            set(review_assignment.assigned_artifacts),
        )
        self.assertEqual(candidate_record, review_inputs["candidate/summary.json"])

        (prior_output / "candidate" / "summary.json").write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "differs from its manifest"):
            launcher._assignment(binding, assessment, "fidelity_reviewer")

    def test_unknown_supervisor_state_keeps_cancellation_stop_unconfirmed(self) -> None:
        coordinator = object.__new__(RegistrationCoordinator)
        assessment = mock.Mock()
        assessment.status.state = "awaiting_architect"
        coordinator.binding = mock.Mock()
        coordinator.binding.assessment.return_value = assessment
        coordinator.binding.poll_current_agent.side_effect = SupervisionError(
            "unknown_operation", "the saved supervisor operation is missing"
        )

        with self.assertRaisesRegex(ValueError, "Stop unconfirmed"):
            coordinator._stop_active_assignment_before_cancel("activity-one")
        coordinator.binding.stop_current_agent.assert_not_called()

    def test_restart_dispatches_committed_owner_grant_correction(self) -> None:
        coordinator = object.__new__(RegistrationCoordinator)
        assessment = mock.Mock()
        assessment.status.state = "changes_requested"
        coordinator.binding = mock.Mock()
        coordinator.binding.assessment.return_value = assessment
        connection = mock.Mock()
        connection.execute.side_effect = (
            SimpleNamespace(fetchone=lambda: ("running",)),
            SimpleNamespace(fetchone=lambda: None),
        )
        coordinator.database = mock.MagicMock()
        coordinator.database.read_connection.return_value.__enter__.return_value = connection
        coordinator._assessment_changed = mock.Mock()

        recovered = coordinator._reconcile_saved_assignment("activity-one")

        self.assertEqual(
            {"activity_id": "activity-one", "state": "architect-correction-dispatched"},
            recovered,
        )
        coordinator._assessment_changed.assert_called_once_with(assessment)

    def test_restart_dispatches_reserved_grant_architect_run_before_launch(self) -> None:
        coordinator = object.__new__(RegistrationCoordinator)
        assessment = mock.Mock()
        assessment.status.state = "awaiting_architect"
        assessment.current_run.return_value = SimpleNamespace(
            assignment_id="architect-assignment", run_id="architect-run"
        )
        coordinator.binding = mock.Mock()
        coordinator.binding.assessment.return_value = assessment
        coordinator.binding.poll_current_agent.side_effect = SupervisionError(
            "unknown_operation", "the launch has not been journaled"
        )
        first_connection = mock.Mock()
        first_connection.execute.side_effect = (
            SimpleNamespace(fetchone=lambda: ("running",)),
            SimpleNamespace(fetchone=lambda: None),
        )
        retry_connection = mock.Mock()
        retry_connection.execute.return_value.fetchone.return_value = None
        grant_connection = mock.Mock()
        grant_connection.execute.return_value.fetchone.return_value = (1,)
        first_context = mock.MagicMock()
        first_context.__enter__.return_value = first_connection
        retry_context = mock.MagicMock()
        retry_context.__enter__.return_value = retry_connection
        grant_context = mock.MagicMock()
        grant_context.__enter__.return_value = grant_connection
        coordinator.database = mock.MagicMock()
        coordinator.database.read_connection.side_effect = (
            first_context, retry_context, grant_context,
        )
        coordinator._launch_assignment = mock.Mock(return_value=True)

        recovered = coordinator._reconcile_saved_assignment("activity-one")

        self.assertEqual(
            {"activity_id": "activity-one", "state": "architect-correction-dispatched"},
            recovered,
        )
        coordinator._launch_assignment.assert_called_once_with(
            assessment, "project_architect"
        )

    def test_unconfirmed_launch_is_not_saved_as_proven_prelaunch_failure(self) -> None:
        coordinator = object.__new__(RegistrationCoordinator)
        launcher = mock.Mock(
            side_effect=SupervisionError(
                "launch_unconfirmed", "agent launch was not acknowledged"
            )
        )
        coordinator.dependencies = SimpleNamespace(assignment_launcher=launcher)
        coordinator.recovery = None
        coordinator.binding = mock.Mock()
        coordinator._assignment_failed = mock.Mock()
        run = SimpleNamespace(
            assignment_id="architect-assignment",
            run_id="architect-run",
        )
        assessment = mock.Mock()
        assessment.context.activity_id = "activity-one"
        assessment.current_run.return_value = run

        self.assertFalse(coordinator._launch_assignment(assessment, "project_architect"))

        coordinator._assignment_failed.assert_called_once()
        self.assertFalse(
            coordinator._assignment_failed.call_args.kwargs["failed_launch"]
        )

    def test_active_confirmation_commit_is_the_update_publication_parent(self) -> None:
        coordinator = object.__new__(RegistrationCoordinator)
        active = ConfirmationResult(
            "Registered",
            RegistrationPackageReference(
                "owner/project", "1" * 40, 1, "candidate-one",
                ".maestro/registrations/versions/1/candidates/candidate-one/manifest.json",
                "2" * 64,
            ),
            ConfirmationReference(
                "confirmation-one",
                ".maestro/registrations/confirmations/confirmation-one.json",
                "3" * 64,
            ),
            "4" * 40,
            2,
        )

        self.assertEqual(
            active.remote_commit,
            coordinator._publication_parent(mock.Mock(), active),
        )

    def test_published_candidate_startup_finalization_is_idempotent(self) -> None:
        application = InstalledServiceApplication(self.settings)
        application.registration.confirmation = mock.Mock()
        package = RegistrationPackageReference(
            "owner/project",
            "1" * 40,
            1,
            "candidate-one",
            ".maestro/registrations/versions/1/candidates/candidate-one/manifest.json",
            "2" * 64,
        )
        with application.database.transaction() as transaction:
            application.activities.create_project(
                transaction,
                ProjectRecord("project-one", "Project one", "registering", 1),
            )
            application.activities.create_activity(
                transaction,
                ActivityRecord(
                    "activity-one", "project-one", "registration",
                    "Register Project one", "running", 3,
                    waiting_reason="Publishing reviewed registration candidate",
                ),
            )
            transaction.execute(
                "INSERT INTO entity_versions(entity_id, version) VALUES (?, ?)",
                ("activity-one", 3),
            )
            transaction.execute(
                """INSERT INTO registration_candidate_publications(
                       project_id, activity_id, activity_version,
                       registration_version, candidate_id, repository, branch,
                       remote, destination_snapshot_reference, manifest_path,
                       manifest_sha256, content_hash, assessment_candidate_sha256,
                       operation_id, request_id, expected_parent, state,
                       remote_commit, package_ref_json,
                       previous_registration_ref_json
                   ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                             'published', ?, ?, NULL)""",
                (
                    "project-one", "activity-one", 3, 1, "candidate-one",
                    "owner/project", "main", "https://github.com/owner/project.git",
                    "5" * 64, package.manifest_path, package.manifest_sha256,
                    "6" * 64, package.manifest_sha256,
                    "candidate-operation-one", "candidate-request-one", "0" * 40,
                    package.commit, canonical_json(package.as_dict()),
                ),
            )

        first = application.registration.rehydrate()
        second = application.registration.rehydrate()
        self.assertEqual(
            ("candidate-operation-one",), first["finalized_candidates"]
        )
        self.assertEqual(
            ("candidate-operation-one",), second["finalized_candidates"]
        )
        with application.database.read_connection() as connection:
            activity = connection.execute(
                """SELECT state, waiting_reason, version FROM service_activities
                   WHERE activity_id = ?""",
                ("activity-one",),
            ).fetchone()
            actions = tuple(
                str(row[0])
                for row in connection.execute(
                    """SELECT action_id FROM service_activity_actions
                       WHERE activity_id = ? ORDER BY sequence""",
                    ("activity-one",),
                ).fetchall()
            )
        self.assertEqual(
            ("waiting", "Exact reviewed candidate is ready for confirmation", 4),
            tuple(activity),
        )
        self.assertEqual(
            ("registration-confirm", "registration-cancel"), actions
        )

    def test_confirmed_pointer_startup_atomically_finalizes_request_and_actions(self) -> None:
        application = InstalledServiceApplication(self.settings)
        package = RegistrationPackageReference(
            "owner/project",
            "1" * 40,
            1,
            "candidate-one",
            ".maestro/registrations/versions/1/candidates/candidate-one/manifest.json",
            "2" * 64,
        )
        confirmation_ref = ConfirmationReference(
            "confirmation-one",
            ".maestro/registrations/confirmations/confirmation-one.json",
            "3" * 64,
        )
        active = ConfirmationResult(
            "Registered", package, confirmation_ref, "4" * 40, 2
        )
        with application.database.transaction() as transaction:
            application.activities.create_project(
                transaction,
                ProjectRecord("project-one", "Project one", "registering", 1),
            )
            application.activities.create_activity(
                transaction,
                ActivityRecord(
                    "activity-one",
                    "project-one",
                    "registration",
                    "Register Project one",
                    "waiting",
                    1,
                    available_actions=(
                        ActivityAction(
                            "registration-confirm", "Confirm registration", "decision"
                        ),
                    ),
                ),
            )
            transaction.execute(
                "INSERT INTO entity_versions(entity_id, version) VALUES (?, ?)",
                ("activity-one", 1),
            )
            transaction.execute(
                """INSERT INTO registration_confirmations(
                       confirmation_id, request_id, operation_id, project_id,
                       activity_id, expected_activity_version, owner_id, confirmed_at,
                       package_ref_json, previous_confirmation_ref_json,
                       receipt_path, receipt_sha256, receipt_bytes, index_bytes,
                       expected_index_bytes, state, remote_commit, confirmation_ref_json
                   ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, ?, ?, ?, ?, NULL,
                             'confirmed', ?, ?)""",
                (
                    "confirmation-one",
                    "confirmation-request-one",
                    "confirmation-operation-one",
                    "project-one",
                    "activity-one",
                    1,
                    "owner-local",
                    "2026-09-21T12:00:00Z",
                    canonical_json(package.as_dict()),
                    confirmation_ref.path,
                    confirmation_ref.sha256,
                    b"{}\n",
                    b"{}\n",
                    active.remote_commit,
                    canonical_json(confirmation_ref.as_dict()),
                ),
            )
            transaction.execute(
                """INSERT INTO active_registrations(
                       project_id, confirmation_id, package_ref_json,
                       confirmation_ref_json, index_bytes, remote_commit, activity_version
                   ) VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    "project-one",
                    "confirmation-one",
                    canonical_json(package.as_dict()),
                    canonical_json(confirmation_ref.as_dict()),
                    b"{}\n",
                    active.remote_commit,
                    2,
                ),
            )
        confirmation = mock.Mock()
        confirmation.active.return_value = active
        application.registration.confirmation = confirmation

        self.assertEqual(
            ("confirmation-one",),
            application.registration._recover_confirmation_finalizations(),
        )
        self.assertEqual(
            (), application.registration._recover_confirmation_finalizations()
        )
        with application.database.read_connection() as connection:
            activity = connection.execute(
                "SELECT state, version FROM service_activities WHERE activity_id = ?",
                ("activity-one",),
            ).fetchone()
            project = connection.execute(
                "SELECT registration_status FROM service_projects WHERE project_id = ?",
                ("project-one",),
            ).fetchone()
            receipt = connection.execute(
                "SELECT resulting_version FROM request_receipts WHERE request_id = ?",
                ("confirmation-request-one",),
            ).fetchone()
            event = connection.execute(
                "SELECT type FROM outbox_events WHERE activity_id = ?",
                ("activity-one",),
            ).fetchone()
            actions = connection.execute(
                "SELECT action_id FROM service_activity_actions WHERE activity_id = ?",
                ("activity-one",),
            ).fetchall()
        self.assertEqual(("completed", 2), activity)
        self.assertEqual(("registered",), project)
        self.assertEqual((2,), receipt)
        self.assertEqual(("registration.confirmed",), event)
        self.assertEqual([], actions)

    def test_eligible_agent_failure_atomically_reserves_counted_automatic_retry(self) -> None:
        application = InstalledServiceApplication(self.settings)
        with application.database.transaction() as transaction:
            application.activities.create_project(
                transaction,
                ProjectRecord("project-one", "Project one", "registering", 1),
            )
            application.activities.create_activity(
                transaction,
                ActivityRecord(
                    "activity-one", "project-one", "registration",
                    "Register Project one", "running", 1,
                ),
            )
        failed = SimpleNamespace(
            assignment_id="assignment-one", run_id="run-one"
        )
        replacement = SimpleNamespace(
            assignment_id="assignment-one", run_id="run-two"
        )
        assessment = mock.Mock()
        assessment.process_snapshot.definition = {
            "recovery": {"automatic_recovery_attempts": 2}
        }
        assessment.current_run.return_value = failed
        binding = mock.Mock()
        binding.assessment.return_value = assessment
        binding.poll_current_agent.return_value = SimpleNamespace(state="failed")
        binding.retry_technical_in.return_value = replacement
        application.registration.binding = binding

        with mock.patch.object(
            application.registration, "_dispatch_reserved_agent_retry"
        ) as dispatch:
            application.registration._assignment_failed(
                "activity-one",
                "project_architect",
                "assignment-one",
                "run-one",
                "temporary tool interruption",
                True,
            )

        dispatch.assert_called_once()
        with application.database.read_connection() as connection:
            failure = connection.execute(
                """SELECT state, automatic_limit, automatic_consumed
                   FROM installed_registration_agent_failures
                   WHERE activity_id = ?""",
                ("activity-one",),
            ).fetchone()
            retry = connection.execute(
                """SELECT assignment_id, failed_run_id, replacement_run_id,
                          kind, state
                   FROM installed_registration_agent_retry_requests
                   WHERE activity_id = ?""",
                ("activity-one",),
            ).fetchone()
            activity = connection.execute(
                "SELECT state FROM service_activities WHERE activity_id = ?",
                ("activity-one",),
            ).fetchone()
        self.assertEqual(("retrying", 2, 1), failure)
        self.assertEqual(
            ("assignment-one", "run-one", "run-two", "automatic", "reserved"),
            retry,
        )
        self.assertEqual(("running",), activity)

    def test_publication_retry_reservation_is_persisted_once_across_restart(self) -> None:
        application = InstalledServiceApplication(self.settings)
        with application.database.transaction() as transaction:
            application.activities.create_project(
                transaction,
                ProjectRecord("project-one", "Project one", "registering", 1),
            )
            application.activities.create_activity(
                transaction,
                ActivityRecord(
                    "activity-one", "project-one", "registration",
                    "Register Project one", "paused", 1,
                ),
            )
        assessment = SimpleNamespace(
            process_snapshot=SimpleNamespace(
                definition={"recovery": {"automatic_recovery_attempts": 2}}
            ),
            context=SimpleNamespace(activity_id="activity-one"),
        )

        first = application.registration._reserve_automatic_publication_retry(
            assessment, "publication-one", "temporary publication failure"
        )
        second = application.registration._reserve_automatic_publication_retry(
            assessment, "publication-one", "startup replay"
        )

        self.assertEqual(first, second)
        with application.database.read_connection() as connection:
            failure = connection.execute(
                """SELECT state, automatic_limit, automatic_consumed
                   FROM installed_registration_publication_failures
                   WHERE operation_id = ?""",
                ("publication-one",),
            ).fetchone()
            retries = connection.execute(
                """SELECT request_id, state
                   FROM installed_registration_publication_retry_requests
                   WHERE operation_id = ?""",
                ("publication-one",),
            ).fetchall()
        self.assertEqual(("retrying", 2, 1), failure)
        self.assertEqual([(first, "reserved")], retries)

    def test_installed_boundary_exposes_routes_controls_and_all_migrations(self) -> None:
        application = InstalledServiceApplication(self.settings)
        authorization = {"Authorization": f"Bearer {OWNER_TOKEN}"}
        response = application.handle(
            "POST",
            "/api/v1/requests",
            {**authorization, "Content-Type": "application/json"},
            json.dumps(
                {
                    "request_id": "registration-start-one",
                    "operation": "registration.start",
                    "project_id": None,
                    "activity_id": None,
                    "question_id": None,
                    "expected_version": None,
                    "payload": {"repository": "owner/project"},
                }
            ).encode(),
        )
        self.assertEqual(400, response.status_code)
        self.assertIn("runtime is not configured", response.body["error"]["message"])
        self.assertNotIn("operation is unavailable", response.body["error"]["message"])

        with application.database.transaction() as transaction:
            application.activities.create_project(
                transaction, ProjectRecord("project-one", "Project one", "registering", 1)
            )
            application.activities.create_activity(
                transaction,
                ActivityRecord(
                    "registration-one", "project-one", "registration",
                    "Register Project one", "waiting", 1,
                ),
            )
        detail = application.handle(
            "GET", "/api/v1/registrations/registration-one", authorization
        )
        self.assertEqual(200, detail.status_code)
        self.assertEqual("registration-one", detail.body["data"]["activity_id"])
        self.assertIsInstance(detail.body["event_cursor"], int)
        by_project = application.handle(
            "GET", "/api/v1/projects/project-one/registration", authorization
        )
        self.assertEqual(detail.body, by_project.body)
        hidden = application.handle(
            "GET", "/api/v1/projects/unknown-project/registration", {}
        )
        self.assertEqual(401, hidden.status_code)

        with application.database.read_connection() as connection:
            domains = {
                str(row[0])
                for row in connection.execute(
                    "SELECT domain FROM domain_migrations"
                ).fetchall()
            }
        self.assertTrue(
            {
                "publication", "registration_confirmation", "registration_recovery",
                "registration_assessment", "registration_composition",
                "service_process_policy",
            }.issubset(domains)
        )

        terminal = TerminalApplication(
            _TerminalConnection(), input_stream=io.StringIO(), output_stream=io.StringIO()
        )
        self.assertTrue(
            {"register", "registration"}.issubset(
                terminal.workspace.extensions.command_names
            )
        )
        self.assertNotIn(
            "registration-confirm", terminal.workspace.extensions.command_names
        )
        self.assertNotIn(
            "registration-cancel", terminal.workspace.extensions.command_names
        )
        self.assertEqual(
            {
                "owner-decision", "registration-cancel", "registration-cancel-back",
                "registration-cancel-confirm", "registration-confirm",
                "registration-retry", "registration-source-choice",
            },
            set(terminal.workspace.extensions.action_names),
        )

    def test_version_output_cannot_fabricate_live_tool_evidence(self) -> None:
        executable = self.root / "version-only-codex"
        executable.write_text("#!/bin/sh\nprintf 'codex-cli 1.2.3\\n'\n", encoding="utf-8")
        executable.chmod(0o700)
        route = ToolRoute(
            "codex",
            executable,
            "agent-credential",
            "agent-settings",
            ("openai/model-1",),
            (PermittedDestination("api.openai.com", 443),),
        )

        observation = InstalledToolInspector(
            "codex", "openai", self.root, self.root / "workspaces"
        ).inspect(route, "1" * 64)

        self.assertFalse(observation.available)
        self.assertFalse(observation.authenticated)
        self.assertFalse(observation.structured_output)
        self.assertFalse(observation.exact_model_enforcement)
        self.assertFalse(observation.substitution_disabled)
        self.assertEqual({}, observation.context_limits)

    def test_tool_preflight_uses_isolated_root_supervised_egress(self) -> None:
        executable = self.root / "codex"
        executable.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        executable.chmod(0o700)
        route = ToolRoute(
            "codex",
            executable,
            "agent-credential",
            "agent-settings",
            ("openai/model-1",),
            (PermittedDestination("api.openai.com", 443),),
        )
        inspector = InstalledToolInspector(
            "codex", "openai", self.root, self.root / "workspaces"
        )
        workspace = mock.Mock()
        workspace.paths.scratch = self.root / "preflight-scratch"
        workspace.isolated_command.return_value = ("/usr/bin/bwrap", "--", str(executable))
        workspace.egress_command.return_value = (
            "/usr/bin/sudo", "-n", "/usr/local/libexec/maestro-agent-egress"
        )
        inspector.workspaces.prepare_preflight = mock.Mock(return_value=workspace)

        command, cwd = inspector._isolated_launch(
            route, (str(executable), "app-server")
        )

        self.assertEqual(workspace.egress_command.return_value, command)
        self.assertEqual(workspace.paths.scratch, cwd)
        workspace.isolated_command.assert_called_once()
        self.assertEqual(
            (str(executable), "app-server"),
            workspace.isolated_command.call_args.args[0],
        )
        profile = workspace.isolated_command.call_args.kwargs["profile"]
        self.assertEqual("codex", profile.tool)
        self.assertEqual(self.root, profile.service_home)
        workspace.egress_command.assert_called_once_with(
            "codex", workspace.isolated_command.return_value
        )

    def test_restarted_assignment_rejects_changed_repository_profile_before_fetch(self) -> None:
        profile = RepositoryProfile(
            "current-profile", "github-app", ("owner/project",), ("main",)
        )
        authorizer = RepositoryAuthorizer(
            {"current-profile": profile},
            (RepositoryBinding("binding", "owner/project", "current-profile"),),
        )
        transport = ServiceGitTransport(
            (
                ServiceGitRoute(
                    "owner/project", "github-app", str(self.root / "remote.git")
                ),
            ),
            lambda _reference: "unused",
        )
        destination = GitHubDestinationProvider(
            GitHubAppDestinationProfile(
                "current-profile",
                "binding",
                GitHubAppCredential("github-app"),
                1,
                2,
                "maestro",
                ("owner/project",),
                ("main",),
            ),
            _DestinationApi(),
        )
        launcher = InstalledRegistrationAgentLauncher(
            workspace_root=self.root / "workspaces",
            source_cache_root=self.root / "registration-sources",
            service_home=self.root,
            authorizer=authorizer,
            transport=transport,
            destination_provider=destination,
        )
        assessment = SimpleNamespace(
            context=SimpleNamespace(
                project_id="project-one",
                activity_id="activity-one",
                source_inventory=SimpleNamespace(source_commit="a" * 40),
                package_context=SimpleNamespace(
                    source_repository="owner/project",
                    publication_branch="main",
                    destination_snapshot_reference="f" * 64,
                ),
            )
        )

        with (
            mock.patch(
                "maestro.service.registration_agents.run_git"
            ) as source_command,
            self.assertRaisesRegex(ValueError, "profile changed since registration intake"),
        ):
            launcher._source_repository(assessment)

        source_command.assert_not_called()
        self.assertFalse(
            (self.root / "registration-sources" / "project-one" / "activity-one.git").exists()
        )

    def test_load_settings_composes_configured_registration_runtime(self) -> None:
        executable = self.root / "codex"
        executable.write_text(
            """#!/usr/bin/python3
import json
import sys

for raw in sys.stdin:
    request = json.loads(raw)
    method = request.get("method")
    request_id = request.get("id")
    if method == "initialize":
        result = {"userAgent": "codex-cli 1.2.3"}
    elif method == "initialized":
        continue
    elif method == "model/list":
        result = {"data": [{"id": "openai/model-1", "model": "openai/model-1", "contextWindow": 65536}]}
    elif method == "thread/start":
        model = request["params"]["model"]
        result = {"thread": {"id": "preflight-thread"}, "model": model, "modelProvider": "openai"}
    elif method == "turn/start":
        result = {"turn": {"id": "preflight-turn"}}
    else:
        continue
    print(json.dumps({"jsonrpc": "2.0", "id": request_id, "result": result}), flush=True)
    if method == "turn/start":
        print(json.dumps({"jsonrpc": "2.0", "method": "item/completed", "params": {"threadId": "preflight-thread", "turnId": "preflight-turn", "item": {"type": "agentMessage", "text": "{\\\"preflight\\\":\\\"ok\\\"}"}}}), flush=True)
        print(json.dumps({"jsonrpc": "2.0", "method": "turn/completed", "params": {"threadId": "preflight-thread", "turn": {"id": "preflight-turn", "status": "completed"}}}), flush=True)
""",
            encoding="utf-8",
        )
        executable.chmod(0o700)
        (self.root / ".codex").mkdir()
        (self.root / ".codex" / "auth.json").write_text("{}\n", encoding="utf-8")
        (self.root / ".codex" / "auth.json").chmod(0o600)
        configuration = self.root / "agents.toml"
        configuration.write_text(
            f'''workspace_root = "{self.root / "workspaces"}"

[service]
host = "127.0.0.1"
port = 8787
agent_user = "maestro-agent"

[storage]
engine = "sqlite"
path = "{self.root / "production.sqlite3"}"

[owner]
id = "owner-local"
token_sha256 = "{hashlib.sha256(OWNER_TOKEN.encode("ascii")).hexdigest()}"

[tools.codex]
executable = "{executable}"
credential_profile = "agent-credential"
settings_profile = "agent-settings"
allowed_model_ids = ["openai/model-1"]
permitted_destinations = [{{ hostname = "api.openai.com", port = 443 }}]

[repositories.project]
credential_profile = "github-app"
allowed_repositories = ["owner/project"]
allowed_branch_patterns = ["main"]

[repositories.project.github]
app_id = 1
installation_id = 2
app_slug = "maestro"

[repository_bindings.binding]
repository = "owner/project"
profile = "project"

[registration]
schema_version = 1
maximum_fidelity_reviews = 2

[registration.architect]
run_timeout_seconds = 1800

[registration.fidelity_reviewer]
run_timeout_seconds = 1800

[registration.initiation]
policy = "registration_intake_or_idle_update"
start_operation = "registration.start"

[registration.agent_session]
policy = "fixed_assignment_followups"
architect_role = "project_architect"
reviewer_role = "fidelity_reviewer"

[registration.saved_outputs]
policy = "versioned_registration_package"
contract = "registration_package_v1"
root = ".maestro/registrations"

[registration.review]
policy = "bounded_independent_fidelity"

[registration.confirmation]
policy = "explicit_exact_candidate_activation"
on_complete = "stop"

[registration.recovery]
policy = "reconcile_preserved_registration"
automatic_recovery_attempts = 2
''',
            encoding="utf-8",
        )
        configuration.chmod(0o600)

        def snapshot(_resources, _provider, _name, definition):
            encoded = canonical_json(definition)
            return ProcessSnapshot(
                "registration",
                encoded,
                hashlib.sha256(encoded.encode()).hexdigest(),
                BundleSnapshot(
                    "registration-process@1", "processDefinition",
                    (("schema.json", "0" * 64),),
                ),
            )

        with mock.patch(
            "maestro.service.installed_registration.prepare_process_snapshot",
            side_effect=snapshot,
        ):
            settings = load_settings(configuration)

        self.assertIsNone(settings.registration_error)
        self.assertIsNotNone(settings.registration_runtime)
        self.assertIsInstance(
            settings.registration_runtime.preflight, AgentRoutePreflight
        )
        self.assertTrue(callable(settings.registration_runtime.assignment_launcher))
        application = InstalledServiceApplication(
            settings, supervisor_units=LocalProcessUnits()
        )
        inventory = SourceInventory(
            "refs/heads/main",
            "a" * 40,
            "README.md",
            (
                SourceBlob.from_bytes("README.md", b"overview\n"),
                SourceBlob.from_bytes("docs/architecture.md", b"architecture\n"),
                SourceBlob.from_bytes("docs/milestones.md", b"milestones\n"),
            ),
            (
                SourceReference("Architecture", "Architecture", "docs/architecture.md"),
                SourceReference(
                    "Milestone declaration", "Milestones", "docs/milestones.md"
                ),
            ),
            (OutcomeReference("Milestones", "Milestones", 1, "M1", "First outcome", 1),),
        )
        reserved_before_read: list[str] = []

        def read_reserved_source(**_kwargs):
            with application.database.read_connection() as connection:
                saved = connection.execute(
                    """SELECT intake_json FROM installed_registration_intake
                       WHERE request_id = 'configured-registration-start'
                         AND state = 'waiting_for_intake'"""
                ).fetchone()
            self.assertIsNotNone(saved)
            reserved = RegistrationIntakeResult.from_json(str(saved[0]))
            self.assertIsNone(reserved.inventory)
            self.assertEqual("a" * 40, reserved.source_commit)
            reserved_before_read.append(str(reserved.selection_decision_ref))
            return inventory

        with (
            mock.patch.object(
                InstalledToolInspector,
                "_isolated_launch",
                return_value=((str(executable), "app-server"), self.root),
            ),
            mock.patch.object(
                GitHubRestDestinationApi,
                "app_identity",
                return_value={"id": 1, "slug": "maestro"},
            ),
            mock.patch.object(
                GitHubRestDestinationApi,
                "installation_identity",
                return_value={"id": 2, "app_id": 1},
            ),
            mock.patch.object(
                GitHubRestDestinationApi,
                "installation_token",
                return_value=GitHubInstallationToken(
                    "installation-token",
                    {"contents": "write", "administration": "read"},
                    time.time() + 300,
                ),
            ),
            mock.patch.object(
                GitHubRestDestinationApi,
                "repository_identity",
                return_value={"full_name": "owner/project"},
            ),
            mock.patch.object(
                GitHubRestDestinationApi,
                "branch_identity",
                return_value={"name": "main", "commit": {"sha": "a" * 40}},
            ),
            mock.patch.object(
                GitHubRestDestinationApi,
                "branch_policy",
                return_value=BranchPolicyObservation(False, ()),
            ),
            mock.patch.object(
                ExactSourceReader, "resolve", return_value="a" * 40
            ),
            mock.patch.object(
                ExactSourceReader, "read_registration_at", side_effect=read_reserved_source
            ),
            mock.patch.object(
                InstalledRegistrationAgentLauncher, "__call__", autospec=True
            ) as launched,
        ):
            response = application.handle(
                "POST",
                "/api/v1/requests",
                {
                    "Authorization": f"Bearer {OWNER_TOKEN}",
                    "Content-Type": "application/json",
                },
                json.dumps(
                    {
                        "request_id": "configured-registration-start",
                        "operation": "registration.start",
                        "project_id": None,
                        "activity_id": None,
                        "question_id": None,
                        "expected_version": None,
                        "payload": {
                            "repository": "owner/project",
                            "overview_path": "README.md",
                            "source_ref": "refs/heads/main",
                            "publication_branch": "main",
                            "scope": "First outcome",
                            "architect_selection": "codex:openai/model-1",
                            "reviewer_selection": "codex:openai/model-1",
                        },
                    }
                ).encode(),
            )
        self.assertEqual(202, response.status_code, response.body)
        self.assertEqual(
            "intake_reserved", response.body["receipt"]["result"]["state"]
        )
        self.assertEqual(1, launched.call_count)
        self.assertEqual(1, len(reserved_before_read))

    def test_installed_schema_and_two_repository_production_composition(self) -> None:
        installed_root = self.root / "installed"
        installed_schema = installed_root / "schemas/registration-process/1/schema.json"
        installed_schema.parent.mkdir(parents=True)
        source_schema = (
            Path(__file__).resolve().parents[3]
            / "services/maestro/schemas/registration-process/1/schema.json"
        )
        installed_schema.write_bytes(source_schema.read_bytes())
        configuration = self.root / "two-repositories.toml"
        configuration.write_text(
            f'''workspace_root = "{self.root / "workspaces"}"

[service]
host = "127.0.0.1"
port = 8787
agent_user = "maestro-agent"

[storage]
engine = "sqlite"
path = "{self.root / "two-repositories.sqlite3"}"

[owner]
id = "owner-local"
token_sha256 = "{hashlib.sha256(OWNER_TOKEN.encode("ascii")).hexdigest()}"

[tools.codex]
executable = "/bin/true"
credential_profile = "agent-credential"
settings_profile = "agent-settings"
allowed_model_ids = ["openai/model-1"]
permitted_destinations = [{{ hostname = "api.openai.com", port = 443 }}]

[repositories.alpha]
credential_profile = "alpha-app"
allowed_repositories = ["owner/alpha"]
allowed_branch_patterns = ["main"]

[repositories.alpha.github]
app_id = 11
installation_id = 21
app_slug = "maestro-alpha"

[repositories.beta]
credential_profile = "beta-app"
allowed_repositories = ["owner/beta"]
allowed_branch_patterns = ["release/*"]

[repositories.beta.github]
app_id = 12
installation_id = 22
app_slug = "maestro-beta"

[repository_bindings.alpha]
repository = "owner/alpha"
profile = "alpha"

[repository_bindings.beta]
repository = "owner/beta"
profile = "beta"

[registration]
schema_version = 1
maximum_fidelity_reviews = 2

[registration.architect]
run_timeout_seconds = 1800

[registration.fidelity_reviewer]
run_timeout_seconds = 1800

[registration.initiation]
policy = "registration_intake_or_idle_update"
start_operation = "registration.start"

[registration.agent_session]
policy = "fixed_assignment_followups"
architect_role = "project_architect"
reviewer_role = "fidelity_reviewer"

[registration.saved_outputs]
policy = "versioned_registration_package"
contract = "registration_package_v1"
root = ".maestro/registrations"

[registration.review]
policy = "bounded_independent_fidelity"

[registration.confirmation]
policy = "explicit_exact_candidate_activation"
on_complete = "stop"

[registration.recovery]
policy = "reconcile_preserved_registration"
automatic_recovery_attempts = 2
''',
            encoding="utf-8",
        )
        configuration.chmod(0o600)

        with mock.patch.object(sys, "prefix", str(installed_root)):
            settings = load_settings(configuration)
            self.assertIsNone(settings.registration_error)
            application = build_application(settings)

        runtime = settings.registration_runtime
        self.assertIsNotNone(runtime)
        assert runtime is not None
        self.assertIsInstance(runtime.destination_provider, GitHubDestinationRouter)
        alpha = runtime.authorizer.authorize("owner/alpha", "main")
        beta = runtime.authorizer.authorize("owner/beta", "release/2026-09")
        self.assertEqual("alpha", alpha.binding_id)
        self.assertEqual("beta", beta.binding_id)
        self.assertEqual(
            "alpha",
            runtime.destination_provider.provider_for("owner/alpha").profile.binding_id,
        )
        self.assertEqual(
            "beta",
            runtime.destination_provider.provider_for("owner/beta").profile.binding_id,
        )
        self.assertEqual("https://github.com/owner/alpha.git", runtime.transport.remote_for(alpha))
        self.assertEqual("https://github.com/owner/beta.git", runtime.transport.remote_for(beta))
        self.assertIsNotNone(application.registration_recovery)

        authorization = {
            "Authorization": f"Bearer {OWNER_TOKEN}",
            "Content-Type": "application/json",
        }
        for repository in ("owner/alpha", "owner/beta"):
            response = application.handle(
                "POST",
                "/api/v1/requests",
                authorization,
                json.dumps(
                    {
                        "request_id": f"start-{repository.replace('/', '-')}",
                        "operation": "registration.start",
                        "project_id": None,
                        "activity_id": None,
                        "question_id": None,
                        "expected_version": None,
                        "payload": {"repository": repository},
                    }
                ).encode(),
            )
            self.assertEqual(202, response.status_code, response.body)
            self.assertEqual(
                "intake_reserved", response.body["receipt"]["result"]["state"]
            )

    def test_typed_runtime_constructs_real_publication_confirmation_and_recovery(self) -> None:
        remote = self.root / "remote.git"
        work = self.root / "source"
        subprocess.run(
            ["git", "init", "--bare", "--initial-branch=main", str(remote)],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "clone", "--quiet", str(remote), str(work)],
            check=True,
            capture_output=True,
        )
        for command in (
            ["git", "-C", str(work), "config", "user.name", "Fixture"],
            ["git", "-C", str(work), "config", "user.email", "fixture@example.invalid"],
        ):
            subprocess.run(command, check=True, capture_output=True)
        docs = work / "docs"
        docs.mkdir()
        (docs / "overview.md").write_text(
            "# Project\n\n## Authoritative sources\n\n"
            "| Source type | Subject or designation | Repository-relative location |\n"
            "| --- | --- | --- |\n"
            "| Architecture | Project architecture | docs/architecture.md |\n"
            "| Milestone declaration | APP — Application | docs/milestones.md |\n",
            encoding="utf-8",
        )
        (docs / "architecture.md").write_text("# Architecture\n", encoding="utf-8")
        (docs / "milestones.md").write_text(
            "# Milestones\n\n## Declaration identity\n\n"
            "| Field | Value |\n| --- | --- |\n"
            "| Declaration | APP — Application |\n"
            "| Declaration version | 1 |\n"
            "| Architecture source | docs/architecture.md |\n\n"
            "## Milestones and order\n\n"
            "| Position | Qualified milestone reference and plain subject | "
            "Milestone version | Milestone section |\n"
            "| --- | --- | --- | --- |\n"
            "| 1 | APP-PM1 — Start application | 1 | docs/milestones.md#start |\n",
            encoding="utf-8",
        )
        for command in (
            ["git", "-C", str(work), "add", "."],
            ["git", "-C", str(work), "commit", "-m", "Initial source"],
            ["git", "-C", str(work), "push", "origin", "HEAD:main"],
        ):
            subprocess.run(command, check=True, capture_output=True)

        registry = AgentRouteRegistry(
            {
                "codex": ToolRoute(
                    "codex",
                    Path("/bin/true"),
                    "agent-credential",
                    "agent-settings",
                    ("openai/model-1",),
                    (PermittedDestination("api.openai.com", 443),),
                )
            }
        )
        provider = ConfiguredAgentRouteProvider(registry)
        preflight = AgentRoutePreflight(
            registry,
            {
                "codex": (
                    InstalledAdapter(
                        "codex",
                        "openai",
                        "cloud",
                        (
                            "code_edit",
                            "local_command",
                            "repository_search",
                            "approved_network",
                        ),
                    ),
                    _Inspector(),
                )
            },
            credential_fingerprint=lambda _name: "1" * 64,
            settings_fingerprint=lambda _name: "2" * 64,
        )
        repository_profile = RepositoryProfile(
            "project", "github-app", ("owner/project",), ("main",)
        )
        authorizer = RepositoryAuthorizer(
            {"project": repository_profile},
            (RepositoryBinding("binding", "owner/project", "project"),),
        )
        transport = ServiceGitTransport(
            (ServiceGitRoute("owner/project", "github-app", str(self.root / "remote.git")),),
            lambda _reference: "unused",
        )
        destination = GitHubDestinationProvider(
            GitHubAppDestinationProfile(
                "project", "binding", GitHubAppCredential("github-app"),
                1, 2, "maestro", ("owner/project",), ("main",),
            ),
            _DestinationApi(
                subprocess.run(
                    ["git", "--git-dir", str(remote), "rev-parse", "refs/heads/main"],
                    check=True, capture_output=True, text=True,
                ).stdout.strip()
            ),
        )
        definition = {
            "initiation": {"policy": "registration_intake_or_idle_update"},
            "agent_session": {
                "policy": "fixed_assignment_followups",
                "architect_role": "project_architect",
                "reviewer_role": "fidelity_reviewer",
            },
            "saved_outputs": {"policy": "versioned_registration_package"},
            "review": {"policy": "bounded_independent_fidelity"},
            "confirmation": {"policy": "explicit_exact_candidate_activation"},
            "recovery": {
                "policy": "reconcile_preserved_registration",
                "automatic_recovery_attempts": 2,
            },
            "maximum_fidelity_reviews": 2,
        }
        encoded = canonical_json(definition)
        snapshot = ProcessSnapshot(
            "registration",
            encoded,
            hashlib.sha256(encoded.encode()).hexdigest(),
            BundleSnapshot(
                "registration-process@1", "processDefinition",
                (("schema.json", "0" * 64),),
            ),
        )
        assignment_launches = []
        runtime = RegistrationRuntimeDependencies(
            ExactSourceReader(), authorizer, transport, destination, preflight,
            snapshot, lambda _repository: str(self.root / "remote.git"),
            workspace_root=self.settings.workspace_root,
            assignment_launcher=lambda _binding, current, role: assignment_launches.append(
                (current.context.activity_id, current.current_run(role).run_id, role)
            ),
        )
        settings = ServiceSettings(
            self.settings.storage,
            self.settings.owner,
            workspace_root=self.settings.workspace_root,
            agent_route_provider=provider,
            registration_runtime=runtime,
        )
        application = InstalledServiceApplication(
            settings, supervisor_units=LocalProcessUnits()
        )

        self.assertIsNotNone(application.publication_journal)
        self.assertIsInstance(
            application.registration_confirmation, RegistrationConfirmationService
        )
        self.assertIsInstance(
            application.registration_recovery, RegistrationRecoveryService
        )
        self.assertIs(
            runtime.preflight, application.registration_assessment.plugin.preflight
        )

        authorization = {
            "Authorization": f"Bearer {OWNER_TOKEN}",
            "Content-Type": "application/json",
        }
        started = application.handle(
            "POST",
            "/api/v1/requests",
            authorization,
            json.dumps(
                {
                    "request_id": "registration-connected-start",
                    "operation": "registration.start",
                    "project_id": None,
                    "activity_id": None,
                    "question_id": None,
                    "expected_version": None,
                    "payload": {"repository": "owner/project"},
                }
            ).encode(),
        )
        self.assertEqual(202, started.status_code)
        receipt = started.body["receipt"]
        self.assertIsInstance(receipt, dict)
        project_id = str(receipt["project_id"])
        activity_id = str(receipt["activity_id"])
        with application.database.read_connection() as connection:
            question = connection.execute(
                """SELECT links.question_id FROM installed_registration_intake_questions AS links
                   WHERE links.activity_id = ? AND links.field = 'scope'""",
                (activity_id,),
            ).fetchone()
        self.assertIsNotNone(question)
        answered = application.handle(
            "POST",
            "/api/v1/requests",
            authorization,
            json.dumps(
                {
                    "request_id": "registration-connected-answer",
                    "operation": "question.answer",
                    "project_id": project_id,
                    "activity_id": activity_id,
                    "question_id": str(question[0]),
                    "expected_version": 1,
                    "payload": {"text": "Current planning scope", "choice_id": None},
                }
            ).encode(),
        )
        self.assertEqual(200, answered.status_code)
        with application.database.read_connection() as connection:
            delivery = connection.execute(
                """SELECT state FROM service_question_deliveries
                   WHERE answer_id = 'registration-connected-answer'"""
            ).fetchone()
            saved = connection.execute(
                """SELECT request_json FROM installed_registration_intake
                   WHERE activity_id = ?""",
                (activity_id,),
            ).fetchone()
            activity_version = connection.execute(
                "SELECT version FROM service_activities WHERE activity_id = ?",
                (activity_id,),
            ).fetchone()
        self.assertEqual(("delivered",), delivery)
        self.assertEqual("Current planning scope", json.loads(str(saved[0]))["scope"])

        reopened = application.handle(
            "POST",
            "/api/v1/requests",
            authorization,
            json.dumps(
                {
                    "request_id": "registration-connected-reopen",
                    "operation": "registration.start",
                    "project_id": None,
                    "activity_id": None,
                    "question_id": None,
                    "expected_version": None,
                    "payload": {"repository": "owner/project"},
                }
            ).encode(),
        )
        self.assertEqual(202, reopened.status_code)
        self.assertEqual(
            activity_id, reopened.body["receipt"]["activity_id"]
        )
        with application.database.read_connection() as connection:
            activity_count = connection.execute(
                """SELECT COUNT(*) FROM service_activities
                   WHERE project_id = ? AND kind = 'registration'""",
                (project_id,),
            ).fetchone()
        self.assertEqual((1,), activity_count)

        cancelled = application.handle(
            "POST",
            "/api/v1/requests",
            authorization,
            json.dumps(
                {
                    "request_id": "registration-connected-cancel",
                    "operation": "registration.cancel",
                    "project_id": project_id,
                    "activity_id": activity_id,
                    "question_id": None,
                    "expected_version": int(activity_version[0]),
                    "payload": {},
                }
            ).encode(),
        )
        self.assertEqual(202, cancelled.status_code)
        self.assertEqual("stopping", cancelled.body["receipt"]["result"]["state"])
        with application.database.read_connection() as connection:
            cancelled_questions = {
                str(row[0])
                for row in connection.execute(
                    """SELECT status FROM service_questions
                       WHERE activity_id = ?""",
                    (activity_id,),
                ).fetchall()
            }
            project_status = connection.execute(
                """SELECT registration_status FROM service_projects
                   WHERE project_id = ?""",
                (project_id,),
            ).fetchone()
        self.assertEqual({"answer_received", "cancelled"}, cancelled_questions)
        self.assertEqual(("not_registered",), project_status)

        application.start()
        self.assertEqual((), application.startup_recovery["errors"])
        application.stop()

        preflighted = application.handle(
            "POST",
            "/api/v1/requests",
            authorization,
            json.dumps(
                {
                    "request_id": "registration-connected-preflight",
                    "operation": "registration.start",
                    "project_id": None,
                    "activity_id": None,
                    "question_id": None,
                    "expected_version": None,
                    "payload": {
                        "repository": "owner/project",
                        "overview_path": "docs/overview.md",
                        "source_ref": "refs/heads/main",
                        "publication_branch": "main",
                        "scope": "APP-PM1",
                        "architect_selection": "codex:openai/model-1",
                        "reviewer_selection": "codex:openai/model-1",
                    },
                }
            ).encode(),
        )
        self.assertEqual(202, preflighted.status_code)
        self.assertEqual(
            "intake_reserved",
            preflighted.body["receipt"]["result"]["state"],
        )
        assessed_activity = preflighted.body["receipt"]["activity_id"]
        self.assertEqual(
            [(str(assessed_activity), application.registration_assessment.assessment(
                str(assessed_activity)
            ).current_run("project_architect").run_id, "project_architect")],
            assignment_launches,
        )

        assessment = application.registration_assessment.assessment(
            str(assessed_activity)
        )
        failed_run = assessment.current_run("project_architect")
        failed_operation = application.registration_assessment.reserve_runtime_identity(
            str(assessed_activity), "project_architect"
        )
        application.agent_supervisor.launch(
            LaunchRequest(
                failed_operation,
                ("/bin/sh", "-c", "sleep 5"),
                str(self.root),
                5,
                2,
            )
        )
        application.agent_supervisor.stop(failed_operation, "adapter_failure")
        application.registration._assignment_failed(
            str(assessed_activity),
            "project_architect",
            failed_run.assignment_id,
            failed_run.run_id,
            "fixture tool exit",
        )
        failed_detail = application.registration.detail(str(assessed_activity))
        self.assertEqual(
            {
                "assignment_id": failed_run.assignment_id,
                "failed_run_id": failed_run.run_id,
                "role": "project_architect",
                "reason": "fixture tool exit",
                "automatic_limit": 2,
                "automatic_consumed": 0,
                "manual_consumed": 0,
                "state": "paused",
            },
            failed_detail["agent_retry"],
        )
        retried = application.handle(
            "POST",
            "/api/v1/requests",
            authorization,
            json.dumps(
                {
                    "request_id": "registration-agent-retry",
                    "operation": "registration.retry",
                    "project_id": project_id,
                    "activity_id": str(assessed_activity),
                    "question_id": None,
                    "expected_version": failed_detail["activity_version"],
                    "payload": {
                        "assignment_id": failed_run.assignment_id,
                        "failed_run_id": failed_run.run_id,
                        "intervention": "Operator verified the tool configuration.",
                    },
                }
            ).encode(),
        )
        self.assertEqual(200, retried.status_code, retried.body)
        assessment = application.registration_assessment.assessment(
            str(assessed_activity)
        )
        self.assertEqual(
            failed_run.assignment_id,
            assessment.current_run("project_architect").assignment_id,
        )
        self.assertNotEqual(
            failed_run.run_id,
            assessment.current_run("project_architect").run_id,
        )
        self.assertEqual(1, retried.body["receipt"]["result"]["manual_consumed"])
        operation = application.registration_assessment.reserve_runtime_identity(
            str(assessed_activity), "project_architect"
        )
        application.agent_supervisor.launch(
            LaunchRequest(
                operation,
                ("/bin/sh", "-c", "sleep 5"),
                str(self.root),
                5,
                2,
            )
        )
        route = assessment.context.routes.architect
        application.agent_supervisor.report_runtime_identity(
            operation,
            RunningToolIdentity(
                "tool_metadata",
                route.provider,
                route.requested_model_id,
                route.tool_version,
                route.configuration_hash,
            ),
        )
        clarification = RegistrationAgentResponse.from_mapping(
            {
                "contract_version": 1,
                "assignment_id": operation.assignment_id,
                "run_id": operation.run_id,
                "project_id": project_id,
                "activity_id": str(assessed_activity),
                "role": "project_architect",
                "source_commit": assessment.context.source_inventory.source_commit,
                "decision_version": assessment.context.decision_version,
                "result": "clarification_required",
                "summary": "The architect needs one explicit boundary answer.",
                "findings": [],
                "questions": [
                    {
                        "local_key": "boundary",
                        "subject": "Registration boundary",
                        "question": "Should the stated scope remain unchanged?",
                        "reason": "The source needs an explicit boundary decision.",
                        "recipient": "owner",
                        "finding_keys": [],
                        "options": [],
                    }
                ],
                "candidate": None,
                "assessment": None,
                "reviewed_assessment": None,
                "review_outcome": None,
                "failure": None,
            }
        )
        application.registration_assessment.submit_architect(clarification)
        with application.database.read_connection() as connection:
            process_question = connection.execute(
                """SELECT question_id, version FROM service_questions
                   WHERE activity_id = ? AND requester = 'project_architect'
                   ORDER BY rowid DESC LIMIT 1""",
                (str(assessed_activity),),
            ).fetchone()
        self.assertIsNotNone(process_question)
        continued = application.handle(
            "POST",
            "/api/v1/requests",
            authorization,
            json.dumps(
                {
                    "request_id": "registration-process-answer",
                    "operation": "question.answer",
                    "project_id": project_id,
                    "activity_id": str(assessed_activity),
                    "question_id": str(process_question[0]),
                    "expected_version": int(process_question[1]),
                    "payload": {"text": "Keep the stated scope.", "choice_id": None},
                }
            ).encode(),
        )
        self.assertEqual(200, continued.status_code)
        resumed = application.registration_assessment.assessment(
            str(assessed_activity)
        )
        self.assertEqual("awaiting_architect", resumed.status.state)
        self.assertNotEqual(operation.run_id, resumed.current_run("project_architect").run_id)
        with application.database.read_connection() as connection:
            lineage = connection.execute(
                """SELECT parent_assignment_id, continuation_question_id,
                          previous_answer_id
                   FROM registration_assignment_lineage
                   WHERE activity_id = ? AND role = 'project_architect'
                     AND assignment_id = ? AND run_id = ?""",
                (
                    str(assessed_activity),
                    resumed.current_run("project_architect").assignment_id,
                    resumed.current_run("project_architect").run_id,
                ),
            ).fetchone()
        self.assertEqual(
            (
                operation.assignment_id,
                str(process_question[0]),
                "registration-process-answer",
            ),
            tuple(lineage),
        )
        self.assertEqual(
            (str(assessed_activity), resumed.current_run("project_architect").run_id,
             "project_architect"),
            assignment_launches[-1],
        )
        application.agent_supervisor.stop(operation, "composition_test_complete")

        architect_operation = application.registration_assessment.reserve_runtime_identity(
            str(assessed_activity), "project_architect"
        )
        application.agent_supervisor.launch(
            LaunchRequest(
                architect_operation, ("/bin/sh", "-c", "sleep 5"),
                str(self.root), 5, 2,
            )
        )
        architect_route = resumed.context.routes.architect
        application.agent_supervisor.report_runtime_identity(
            architect_operation,
            RunningToolIdentity(
                "tool_metadata", architect_route.provider,
                architect_route.requested_model_id, architect_route.tool_version,
                architect_route.configuration_hash,
            ),
        )
        with application.database.read_connection() as connection:
            event_cursor = int(
                connection.execute(
                    "SELECT COALESCE(MAX(sequence), 0) FROM outbox_events"
                ).fetchone()[0]
            )
        connected_events = EventStreamService(
            application.database, application.authenticator
        ).subscribe(authorization["Authorization"], str(event_cursor))
        follow_up = RegistrationAgentResponse.from_mapping(
            {
                "contract_version": 1,
                "assignment_id": architect_operation.assignment_id,
                "run_id": architect_operation.run_id,
                "project_id": project_id,
                "activity_id": str(assessed_activity),
                "role": "project_architect",
                "source_commit": resumed.context.source_inventory.source_commit,
                "decision_version": resumed.context.decision_version,
                "result": "clarification_required",
                "summary": "The architect needs a linked follow-up answer.",
                "findings": [],
                "questions": [
                    {
                        "local_key": "boundary-follow-up",
                        "subject": "Registration boundary follow-up",
                        "question": "Does the prior answer also cover the retained history?",
                        "reason": "The amendment must retain the confirmed boundary.",
                        "recipient": "owner",
                        "finding_keys": [],
                        "options": [],
                    }
                ],
                "candidate": None,
                "assessment": None,
                "reviewed_assessment": None,
                "review_outcome": None,
                "failure": None,
            }
        )
        application.registration_assessment.submit_architect(follow_up)
        self.assertIn(
            "question.published",
            {event.type for event in connected_events.next_batch()},
        )
        with application.database.read_connection() as connection:
            linked_question = connection.execute(
                """SELECT questions.question_id, questions.version,
                          details.original_question_id, details.previous_answer_id
                   FROM service_questions AS questions
                   JOIN service_question_details AS details USING(question_id)
                   WHERE questions.activity_id = ?
                     AND questions.subject = 'Registration boundary follow-up'""",
                (str(assessed_activity),),
            ).fetchone()
        self.assertEqual(
            (str(process_question[0]), "registration-process-answer"),
            (str(linked_question[2]), str(linked_question[3])),
        )
        followed_up = application.handle(
            "POST",
            "/api/v1/requests",
            authorization,
            json.dumps(
                {
                    "request_id": "registration-process-follow-up-answer",
                    "operation": "question.answer",
                    "project_id": project_id,
                    "activity_id": str(assessed_activity),
                    "question_id": str(linked_question[0]),
                    "expected_version": int(linked_question[1]),
                    "payload": {
                        "text": "Yes, retain the confirmed history.",
                        "choice_id": None,
                    },
                }
            ).encode(),
        )
        self.assertEqual(200, followed_up.status_code)
        application.agent_supervisor.stop(
            architect_operation, "composition_follow_up_complete"
        )
        resumed = application.registration_assessment.assessment(
            str(assessed_activity)
        )
        with application.database.read_connection() as connection:
            follow_up_lineage = connection.execute(
                """SELECT parent_assignment_id, continuation_question_id,
                          previous_answer_id
                   FROM registration_assignment_lineage
                   WHERE activity_id = ? AND role = 'project_architect'
                     AND assignment_id = ? AND run_id = ?""",
                (
                    str(assessed_activity),
                    resumed.current_run("project_architect").assignment_id,
                    resumed.current_run("project_architect").run_id,
                ),
            ).fetchone()
        self.assertEqual(
            (
                architect_operation.assignment_id,
                str(process_question[0]),
                "registration-process-follow-up-answer",
            ),
            tuple(follow_up_lineage),
        )
        architect_operation = application.registration_assessment.reserve_runtime_identity(
            str(assessed_activity), "project_architect"
        )
        application.agent_supervisor.launch(
            LaunchRequest(
                architect_operation, ("/bin/sh", "-c", "sleep 5"),
                str(self.root), 5, 2,
            )
        )
        application.agent_supervisor.report_runtime_identity(
            architect_operation,
            RunningToolIdentity(
                "tool_metadata", architect_route.provider,
                architect_route.requested_model_id, architect_route.tool_version,
                architect_route.configuration_hash,
            ),
        )
        manifest, package_records = complete_package(
            resumed.context.package_context,
            registration_version=1,
            candidate_id=architect_operation.assignment_id,
            review_context={
                **resumed.package_review_context(),
                "architect_assignment_id": architect_operation.assignment_id,
                "architect_run_id": architect_operation.run_id,
            },
            include_review=False,
        )
        manifest_bytes = canonical_json(manifest).encode()
        candidate_root = (
            self.settings.workspace_root / project_id / str(assessed_activity)
            / "runs" / architect_operation.run_id / "output" / "candidate"
        )
        candidate_root.mkdir(parents=True)
        (candidate_root / "manifest.json").write_bytes(manifest_bytes)
        for path, package_record in package_records.items():
            target = candidate_root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(canonical_json(package_record).encode())
        candidate_ref = {
            "path": "candidate/manifest.json",
            "sha256": hashlib.sha256(manifest_bytes).hexdigest(),
            "version": architect_operation.assignment_id,
        }
        assessment_ref = {
            "path": "assessment.json",
            "sha256": "3" * 64,
            "version": "assessment-initial",
        }

        def completed_response(role, operation_identity, *, reviewed=False):
            return RegistrationAgentResponse.from_mapping({
                "contract_version": 1,
                "assignment_id": operation_identity.assignment_id,
                "run_id": operation_identity.run_id,
                "project_id": project_id,
                "activity_id": str(assessed_activity),
                "role": role,
                "source_commit": resumed.context.source_inventory.source_commit,
                "decision_version": resumed.context.decision_version,
                "result": "completed",
                "summary": "The exact registration candidate is ready.",
                "findings": [],
                "questions": [],
                "candidate": candidate_ref,
                "assessment": None if reviewed else assessment_ref,
                "reviewed_assessment": assessment_ref if reviewed else None,
                "review_outcome": "APPROVE" if reviewed else None,
                "failure": None,
            })

        application.registration_assessment.submit_architect(
            completed_response("project_architect", architect_operation)
        )
        self.assertEqual(
            "fidelity_reviewer", assignment_launches[-1][2]
        )
        reviewer_operation = application.registration_assessment.reserve_runtime_identity(
            str(assessed_activity), "fidelity_reviewer"
        )
        application.agent_supervisor.launch(
            LaunchRequest(
                reviewer_operation, ("/bin/sh", "-c", "sleep 5"),
                str(self.root), 5, 2,
            )
        )
        reviewer_route = resumed.context.routes.fidelity_reviewer
        application.agent_supervisor.report_runtime_identity(
            reviewer_operation,
            RunningToolIdentity(
                "tool_metadata", reviewer_route.provider,
                reviewer_route.requested_model_id, reviewer_route.tool_version,
                reviewer_route.configuration_hash,
            ),
        )
        with application.database.read_connection() as connection:
            ready_cursor = int(
                connection.execute(
                    "SELECT COALESCE(MAX(sequence), 0) FROM outbox_events"
                ).fetchone()[0]
            )
        ready_events = EventStreamService(
            application.database, application.authenticator
        ).subscribe(authorization["Authorization"], str(ready_cursor))
        application.registration_assessment.submit_reviewer(
            completed_response(
                "fidelity_reviewer", reviewer_operation, reviewed=True
            )
        )
        ready_batch = ready_events.next_batch()
        self.assertIn(
            "registration.activity-updated",
            {event.type for event in ready_batch},
        )
        reviewed_root = (
            self.settings.workspace_root / project_id / str(assessed_activity)
            / "runs" / architect_operation.run_id / "output" / "reviewed-candidate"
        )
        (reviewed_root / "manifest.json").write_bytes(b"{}\n")
        detail = application.registration.detail(str(assessed_activity))
        with application.database.read_connection() as connection:
            presentation = connection.execute(
                "SELECT state, waiting_reason FROM service_activities WHERE activity_id = ?",
                (str(assessed_activity),),
            ).fetchone()
        self.assertTrue(detail["can_confirm"], (detail, tuple(presentation)))
        self.assertEqual(
            architect_operation.assignment_id,
            detail["package_ref"]["candidate_id"],
        )
        self.assertEqual(
            architect_operation.assignment_id,
            detail["package_manifest"]["candidate_id"],
        )
        self.assertTrue(detail["package_records"])
        with application.database.read_connection() as connection:
            actions = {
                str(row[0]) for row in connection.execute(
                    "SELECT action_id FROM service_activity_actions WHERE activity_id = ?",
                    (str(assessed_activity),),
                ).fetchall()
            }
        self.assertEqual(
            {"registration-confirm", "registration-cancel"}, actions
        )
        confirmed = application.handle(
            "POST",
            "/api/v1/requests",
            authorization,
            json.dumps(
                {
                    "request_id": "connected-registration-confirm",
                    "operation": "registration.confirm",
                    "project_id": project_id,
                    "activity_id": str(assessed_activity),
                    "question_id": None,
                    "expected_version": detail["activity_version"],
                    "payload": {
                        "confirmation_id": "connected-confirmation",
                        "package_ref": detail["package_ref"],
                        "confirmed_at": "2026-09-20T12:00:00Z",
                    },
                }
            ).encode(),
        )
        self.assertEqual(200, confirmed.status_code)
        confirmed_detail = application.registration.detail(str(assessed_activity))
        self.assertEqual(1, len(confirmed_detail["history"]))
        self.assertFalse(confirmed_detail["can_confirm"])
        application.agent_supervisor.stop(
            architect_operation, "composition_test_complete"
        )
        application.agent_supervisor.stop(
            reviewer_operation, "composition_test_complete"
        )

        reregistered = application.handle(
            "POST",
            "/api/v1/requests",
            authorization,
            json.dumps(
                {
                    "request_id": "connected-registration-update",
                    "operation": "registration.start",
                    "project_id": None,
                    "activity_id": None,
                    "question_id": None,
                    "expected_version": None,
                    "payload": {
                        "repository": "owner/project",
                        "overview_path": "docs/overview.md",
                        "scope": "APP-PM1",
                        "architect_selection": "codex:openai/model-1",
                        "reviewer_selection": "codex:openai/model-1",
                    },
                }
            ).encode(),
        )
        self.assertEqual(202, reregistered.status_code, reregistered.body)
        self.assertEqual(
            "intake_reserved", reregistered.body["receipt"]["result"]["state"]
        )
        update_activity = str(reregistered.body["receipt"]["activity_id"])
        update_assessment = application.registration_assessment.assessment(
            update_activity
        )
        update_manifest_values = (
            application.registration_assessment.candidate_manifest_values(
                update_assessment
            )
        )
        self.assertEqual(2, update_manifest_values["registration_version"])
        self.assertEqual(
            detail["package_ref"],
            update_manifest_values["previous_registration_ref"],
        )
        self.assertEqual(
            update_assessment.current_run("project_architect").assignment_id,
            update_manifest_values["candidate_id"],
        )
        update_operation = application.registration_assessment.reserve_runtime_identity(
            update_activity, "project_architect"
        )
        application.agent_supervisor.launch(
            LaunchRequest(
                update_operation,
                ("/bin/sh", "-c", "sleep 5"),
                str(self.root),
                5,
                2,
            )
        )
        restarted = application.registration.rehydrate()
        self.assertIn(
            {"activity_id": update_activity, "state": "running-paused"},
            restarted["agent_assignments"],
        )
        self.assertEqual("Paused", application.registration.detail(update_activity)["state"])
        update_detail = application.registration.detail(update_activity)
        original_stop = application.registration_assessment.stop_current_agent
        cancellation_state_before_stop: list[str] = []

        def stop_after_intent(*args, **kwargs):
            with application.database.read_connection() as connection:
                intent = connection.execute(
                    """SELECT state FROM installed_registration_cancellations
                       WHERE activity_id = ?""",
                    (update_activity,),
                ).fetchone()
            cancellation_state_before_stop.append(str(intent[0]))
            return original_stop(*args, **kwargs)

        with mock.patch.object(
            application.registration_assessment,
            "stop_current_agent",
            side_effect=stop_after_intent,
        ):
            cancelled_update = application.handle(
                "POST",
                "/api/v1/requests",
                authorization,
                json.dumps(
                    {
                        "request_id": "connected-registration-update-cancel",
                        "operation": "registration.cancel",
                        "project_id": project_id,
                        "activity_id": update_activity,
                        "question_id": None,
                        "expected_version": update_detail["activity_version"],
                        "payload": {},
                    }
                ).encode(),
            )
        self.assertEqual(202, cancelled_update.status_code, cancelled_update.body)
        self.assertEqual(["stopping"], cancellation_state_before_stop)
        self.assertEqual(
            "cancelled",
            application.agent_supervisor.poll(update_operation).state,
        )
        self.assertEqual(
            "cancelled", application.registration.detail(update_activity)["state"]
        )
        active_after_cancel = application.registration_confirmation.active(project_id)
        self.assertIsNotNone(active_after_cancel)
        self.assertEqual(
            "connected-confirmation",
            active_after_cancel.confirmation_ref.confirmation_id,
        )
        with application.database.read_connection() as connection:
            reservation = connection.execute(
                """SELECT state FROM registration_project_reservations
                   WHERE activity_id = ?""",
                (update_activity,),
            ).fetchone()
        self.assertEqual(("released",), reservation)

        seed = subprocess.run(
            ["git", "--git-dir", str(remote), "rev-parse", "refs/heads/main"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        publication_operation = "startup-pending-candidate"
        publication_request = "startup-pending-candidate-request"
        manifest_path = (
            ".maestro/registrations/versions/1/candidates/"
            "startup-candidate/manifest.json"
        )
        manifest_bytes = b'{"candidate":"startup-candidate"}\n'
        destination_authorization = destination.authorize("owner/project", "main")
        destination_reference = hashlib.sha256(
            canonical_json(dict(destination_authorization.snapshot)).encode("utf-8")
        ).hexdigest()
        assert application.publication_journal is not None
        application.publication_journal.prepare(
            operation_id=publication_operation,
            operation_type="registration_candidate",
            request_id=publication_request,
            repository="owner/project",
            remote=str(remote),
            branch="main",
            expected_parent=seed,
            files={manifest_path: manifest_bytes},
            expected_files={manifest_path: None},
            destination_authorization=destination_authorization,
        )
        with application.database.transaction() as transaction:
            transaction.execute(
                """INSERT INTO registration_candidate_publications(
                       project_id, activity_id, activity_version,
                       registration_version, candidate_id, repository, branch,
                       remote, destination_snapshot_reference, manifest_path,
                       manifest_sha256, content_hash, assessment_candidate_sha256,
                       operation_id, request_id, expected_parent, state,
                       remote_commit, package_ref_json,
                       previous_registration_ref_json
                   ) VALUES (?, ?, 1, 1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                             'prepared', NULL, NULL, NULL)""",
                (
                    project_id,
                    str(assessed_activity),
                    "startup-candidate",
                    "owner/project",
                    "main",
                    str(remote),
                    destination_reference,
                    manifest_path,
                    hashlib.sha256(manifest_bytes).hexdigest(),
                    "1" * 64,
                    "2" * 64,
                    publication_operation,
                    publication_request,
                    seed,
                ),
            )

        restarted = InstalledServiceApplication(settings)
        restarted.start()
        self.addCleanup(restarted.stop)
        restored = restarted.registration_assessment.assessment(
            str(assessed_activity)
        )
        self.assertEqual("ready", restored.status.state)
        self.assertIn(
            str(assessed_activity),
            restarted.startup_recovery["restored_assessments"],
        )
        with restarted.database.read_connection() as connection:
            recovered_publication = connection.execute(
                """SELECT state, remote_commit
                   FROM registration_candidate_publications
                   WHERE operation_id = ?""",
                (publication_operation,),
            ).fetchone()
        self.assertEqual("published", recovered_publication[0])
        self.assertIsNotNone(recovered_publication[1])
        self.assertIn(
            publication_operation,
            {
                item["operation_id"]
                for item in restarted.startup_recovery["recovered_publications"]
                if item["kind"] == "candidate"
            },
        )


if __name__ == "__main__":
    unittest.main()
