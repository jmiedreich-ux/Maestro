from __future__ import annotations

import hashlib
import io
import json
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

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
from maestro.agents.supervisor import LaunchRequest, LocalProcessUnits
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
    GitHubInstallationToken,
)
from maestro.planning.registration_confirmation import RegistrationConfirmationService
from maestro.planning.registration_recovery import RegistrationRecoveryService
from maestro.planning.registration_records import RegistrationAgentResponse
from maestro.planning.sources import ExactSourceReader
from maestro.service.activities import ActivityRecord, ProjectRecord
from maestro.service.authentication import OwnerAuthenticationSettings
from maestro.service.main import InstalledServiceApplication, ServiceSettings
from maestro.service.processes import ProcessSnapshot
from maestro.service.registration import RegistrationRuntimeDependencies
from maestro.service.resources import BundleSnapshot
from maestro.terminal.main import TerminalApplication


OWNER_TOKEN = "c" * 64


class _DestinationApi:
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
        return {"name": branch}

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
            {"registration-cancel", "registration-confirm", "registration-retry"},
            set(terminal.workspace.extensions.action_names),
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
            _DestinationApi(),
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
        runtime = RegistrationRuntimeDependencies(
            ExactSourceReader(), authorizer, transport, destination, preflight,
            snapshot, lambda _repository: str(self.root / "remote.git"),
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
                    "expected_version": 1,
                    "payload": {},
                }
            ).encode(),
        )
        self.assertEqual(200, cancelled.status_code)
        self.assertEqual("cancelled", cancelled.body["receipt"]["result"]["state"])
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
            "assessment_started",
            preflighted.body["receipt"]["result"]["state"],
        )
        assessed_activity = preflighted.body["receipt"]["activity_id"]

        assessment = application.registration_assessment.assessment(
            str(assessed_activity)
        )
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
        application.agent_supervisor.stop(operation, "composition_test_complete")

        seed = subprocess.run(
            ["git", "-C", str(work), "rev-parse", "HEAD"],
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
        self.assertEqual("awaiting_architect", restored.status.state)
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
