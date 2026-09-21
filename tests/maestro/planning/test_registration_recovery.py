from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
import threading
import unittest
from dataclasses import dataclass, replace
from pathlib import Path

from maestro.agents.preflight import ResolvedAgentRoute, ResolvedRoleRoutes, RunningToolIdentity
from maestro.foundation import Database, StorageSettings, canonical_json
from maestro.foundation.credentials import (
    RepositoryAuthorizer,
    RepositoryBinding,
    RepositoryProfile,
    ServiceGitRoute,
    ServiceGitTransport,
)
from maestro.foundation.git_publication import (
    PublicationAccessError,
    PublicationConflictError,
    PublicationJournal,
    publication_migrations,
)
from maestro.foundation.github_destination import (
    BranchPolicyObservation,
    GitHubAppCredential,
    GitHubAppDestinationProfile,
    GitHubDestinationProvider,
    GitHubInstallationToken,
)
from maestro.planning.registration import AssessmentContext, AssessmentRun, RegistrationAssessment
from maestro.planning.intake import (
    RegistrationIntakeResult,
    _selection_decision_reference,
)
from maestro.planning.registration_plugin import REGISTRATION_ASSESSMENT_RUNTIME_MIGRATION
from maestro.planning.registration_confirmation import (
    OwnerConfirmation,
    RegistrationConfirmationService,
    RegistrationPackageReference,
    registration_confirmation_migrations,
)
from maestro.planning.registration_records import (
    RegistrationAgentResponse,
    RegistrationPackageContext,
    canonical_record_bytes,
    package_content_hash,
)
from maestro.planning.registration_recovery import (
    HistoricalDestinationProfiles,
    HistoricalPublicationRoute,
    RegistrationRecoveryError,
    RegistrationRecoveryService,
    RegistrationRecoverySetupError,
    registration_recovery_migrations,
)
from maestro.planning.sources import OutcomeReference, SourceBlob, SourceInventory, SourceReference
from maestro.service.activities import (
    ACTIVITY_ACTIONS_MIGRATION,
    ACTIVITY_RECORDS_MIGRATION,
    ActivityRecord,
    ActivityAction,
    ActivityRepository,
    ProjectRecord,
    QuestionRecord,
)
from maestro.service.authentication import VerifiedActor
from maestro.service.processes import PROCESS_POLICY_MIGRATION, ProcessSnapshot
from maestro.service.questions import QUESTION_MIGRATION
from maestro.service.resources import BundleSnapshot
from tests.maestro.registration_package_fixture import complete_package


class RegistrationRecoveryTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.remote = self.root / "remote.git"
        self.work = self.root / "work"
        self.git("git", "init", "--bare", "--initial-branch=main", str(self.remote))
        self.git("git", "clone", "--quiet", str(self.remote), str(self.work))
        self.git("git", "-C", str(self.work), "config", "user.name", "Fixture")
        self.git("git", "-C", str(self.work), "config", "user.email", "fixture@example.invalid")
        (self.work / "README.md").write_text("seed\n", encoding="utf-8")
        self.git("git", "-C", str(self.work), "add", "README.md")
        self.git("git", "-C", str(self.work), "commit", "--quiet", "-m", "seed")
        self.git("git", "-C", str(self.work), "push", "--quiet", "origin", "main")
        self.seed = self.output("git", "-C", str(self.work), "rev-parse", "HEAD")

        repository_profile = RepositoryProfile(
            "project-github", "github-app-project", ("owner/project",), ("main",)
        )
        self.credentials = {"github-app-project": "fixture-credential"}
        self.transport = ServiceGitTransport(
            (ServiceGitRoute("owner/project", "github-app-project", str(self.remote)),),
            lambda reference: self.credentials[reference],
        )
        self.authorizer = RepositoryAuthorizer(
            {repository_profile.name: repository_profile},
            (RepositoryBinding("binding-project", "owner/project", repository_profile.name),),
        )
        self.profile = GitHubAppDestinationProfile(
            profile_name="project-github",
            binding_id="binding-project",
            credential=GitHubAppCredential("github-app-project"),
            app_id=101,
            installation_id=202,
            app_slug="maestro-coordinator",
            allowed_repositories=("owner/project",),
            allowed_branches=("main",),
        )
        self.api = _DestinationApi()
        self.provider = GitHubDestinationProvider(self.profile, self.api)
        self.database = Database(
            StorageSettings(path=self.root / "maestro.sqlite3"),
            (
                *publication_migrations(),
                *registration_confirmation_migrations(),
                *registration_recovery_migrations(),
                REGISTRATION_ASSESSMENT_RUNTIME_MIGRATION,
                PROCESS_POLICY_MIGRATION,
                ACTIVITY_RECORDS_MIGRATION,
                ACTIVITY_ACTIONS_MIGRATION,
                QUESTION_MIGRATION,
            ),
        )
        self.journal = PublicationJournal(
            self.database, self.authorizer, self.transport, self.provider
        )
        self.confirmation = RegistrationConfirmationService(
            self.database, self.journal, self.provider
        )
        self.activities = ActivityRepository(self.database)
        with self.database.transaction() as transaction:
            self.activities.create_project(
                transaction, ProjectRecord("project-1", "Project one", "Registered", 1)
            )
            self.activities.create_activity(
                transaction,
                ActivityRecord(
                    "activity-1", "project-1", "registration", "Initial registration",
                    "completed", 1,
                ),
            )
        first_assessment, _manifest, _records, first_package = self.publish(
            "activity-1", 1, "candidate-1", self.seed, None, "1"
        )
        self.first = self.confirmation.confirm(
            first_assessment,
            VerifiedActor("owner-local"),
            OwnerConfirmation(
                "confirmation-1", "confirmation-request-1", "project-1", "activity-1",
                1, first_package, "2026-09-20T10:00:00Z",
            ),
        )
        self.first_assessment = first_assessment
        self.first_package = first_package
        self.authorization = self.provider.authorize("owner/project", "main")
        self.snapshot_reference = _snapshot_reference(self.authorization.snapshot)
        self.route = HistoricalPublicationRoute(self.journal, self.provider)
        process_definition = {
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
        definition_json = canonical_json(process_definition)
        self.process_snapshot = ProcessSnapshot(
            "registration",
            definition_json,
            hashlib.sha256(definition_json.encode("utf-8")).hexdigest(),
            BundleSnapshot(
                "registration-process@1", "registrationProcessDefinition",
                (("schema.json", "e" * 64),),
            ),
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def recovery(
        self, routes: dict[str, HistoricalPublicationRoute] | None = None
    ) -> RegistrationRecoveryService:
        return RegistrationRecoveryService(
            self.database,
            self.journal,
            HistoricalDestinationProfiles(
                {self.snapshot_reference: self.route} if routes is None else routes
            ),
        )

    def test_historical_route_uses_profile_identity_for_matching_branch_pattern(self) -> None:
        profile = replace(self.profile, allowed_branches=("release/*",))
        provider = GitHubDestinationProvider(profile, self.api)
        authorization = provider.authorize("owner/project", "release/2026-09")
        snapshot_reference = _snapshot_reference(authorization.snapshot)
        historical_route = HistoricalPublicationRoute(self.journal, provider)
        profiles = HistoricalDestinationProfiles(
            {profile.configuration_hash: historical_route}
        )

        route, authorization = profiles.resolve(
            authorization.snapshot, snapshot_reference
        )

        self.assertIs(historical_route, route)
        self.assertEqual("allowed", authorization.decision)

    def begin(self, service: RegistrationRecoveryService, activity_id: str, request_id: str):
        self.save_registration_history(activity_id)
        continuity = service.load_continuity("project-1", activity_id)
        return service.begin(
            request_id=request_id,
            project_id="project-1",
            activity_id=activity_id,
            destination_authorization=self.authorization,
            continuity=continuity,
            process_snapshot=self.process_snapshot,
        )

    def save_registration_history(self, activity_id: str) -> None:
        with self.database.read_connection() as connection:
            if connection.execute(
                "SELECT 1 FROM registration_assessment_intake WHERE activity_id = ?",
                (activity_id,),
            ).fetchone() is not None:
                return
        assessment, _manifest, _records = self.package(
            activity_id, 2, f"saved-{activity_id}", self.first_package
        )
        context = assessment.context
        intake = RegistrationIntakeResult(
            context.source_inventory,
            (),
            "binding-project",
            context.selected_scope,
            "supplied",
            self.snapshot_reference,
            self.authorization.durable_record(),
            context.source_inventory.source_ref,
            "main",
            None,
            "owner/project",
            context.decision_version,
            "b" * 40,
        )
        state = assessment.to_record()
        with self.database.transaction() as transaction:
            self.activities.create_activity(
                transaction,
                ActivityRecord(
                    activity_id, "project-1", "registration",
                    f"Update registration {activity_id}", "starting", 1,
                    available_actions=(
                        ActivityAction(
                            f"{activity_id}-source-decision",
                            "Retain saved source", "decision",
                        ),
                    ),
                ),
            )
            self.activities.create_question(
                transaction,
                QuestionRecord(
                    f"{activity_id}-question", "project-1", activity_id,
                    "Retained context", "Keep this saved context?",
                    "project-architect", "open", 1,
                ),
            )
            transaction.execute(
                """INSERT INTO registration_assessment_intake(
                       activity_id, project_id, selections_json, intake_json
                   ) VALUES (?, ?, ?, ?)""",
                (
                    activity_id, "project-1",
                    canonical_json({
                        "architect": {"tool": "codex", "model_id": "openai/model-1"},
                        "fidelity_reviewer": {
                            "tool": "claude_code", "model_id": "anthropic/model-1"
                        },
                    }),
                    intake.to_json(),
                ),
            )
            for role, run, route in (
                ("project_architect", context.architect_run, context.routes.architect),
                ("fidelity_reviewer", context.reviewer_run, context.routes.fidelity_reviewer),
            ):
                transaction.execute(
                    """INSERT INTO registration_assessment_runs(
                           activity_id, role, assignment_id, run_id, route_json,
                           runtime_identity_json
                       ) VALUES (?, ?, ?, ?, ?, ?)""",
                    (
                        activity_id, role, run.assignment_id, run.run_id,
                        canonical_json({
                            "role": route.role,
                            "tool": route.tool,
                            "requested_model_id": route.requested_model_id,
                            "provider": route.provider,
                            "tool_version": route.tool_version,
                            "executable": route.executable,
                            "credential_profile": route.credential_profile,
                            "settings_profile": route.settings_profile,
                            "location": route.location,
                            "capabilities": list(route.capabilities),
                            "context_limit_tokens": route.context_limit_tokens,
                            "permitted_destinations": [
                                item.as_dict() for item in route.permitted_destinations
                            ],
                            "configuration_hash": route.configuration_hash,
                        }),
                        canonical_json({
                            "source": "tool_metadata",
                            "provider": route.provider,
                            "model_id": route.requested_model_id,
                            "tool_version": route.tool_version,
                            "configuration_hash": route.configuration_hash,
                        }),
                    ),
                )
            transaction.execute(
                """INSERT INTO registration_assessment_state(activity_id, state_json)
                   VALUES (?, ?)""",
                (activity_id, canonical_json(state)),
            )
            transaction.execute(
                """INSERT INTO service_process_snapshots(
                       activity_id, process_name, definition_json,
                       definition_sha256, bundle_snapshot_json
                   ) VALUES (?, ?, ?, ?, ?)""",
                (
                    activity_id, self.process_snapshot.process_name,
                    self.process_snapshot.definition_json,
                    self.process_snapshot.definition_sha256,
                    canonical_json(self.process_snapshot.bundle.as_dict()),
                ),
            )
            transaction.execute(
                """INSERT INTO service_process_counters(
                       activity_id, counter_name, scope_id, consumed
                   ) VALUES (?, ?, ?, ?)""",
                (activity_id, "automatic_recovery_attempts", "architect-assignment", 1),
            )

    def test_atomic_idle_reservation_comparison_and_retained_active_approval(self) -> None:
        service = self.recovery()
        with self.database.transaction() as transaction:
            self.activities.create_activity(
                transaction,
                ActivityRecord(
                    "execution-activity", "project-1", "execution",
                    "Existing project work", "running", 1,
                ),
            )
        with self.assertRaisesRegex(RegistrationRecoveryError, "not idle"):
            self.begin(service, "blocked-registration", "blocked-request")
        with self.database.transaction() as transaction:
            self.activities.update_activity(
                transaction,
                ActivityRecord(
                    "execution-activity", "project-1", "execution",
                    "Existing project work", "completed", 2,
                ),
                expected_record_version=1,
            )
        barrier = threading.Barrier(2)
        results: list[object] = []

        def start(activity_id: str) -> None:
            barrier.wait()
            try:
                results.append(self.begin(service, activity_id, f"request-{activity_id}"))
            except RegistrationRecoveryError as error:
                results.append(error)

        threads = [
            threading.Thread(target=start, args=("activity-2",)),
            threading.Thread(target=start, args=("activity-3",)),
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        successes = [item for item in results if not isinstance(item, Exception)]
        failures = [item for item in results if isinstance(item, Exception)]
        self.assertEqual((1, 1), (len(successes), len(failures)))
        activity_id = successes[0].activity_id

        with self.database.transaction() as transaction:
            service.require_work_start_allowed(transaction, "project-1", activity_id)
            with self.assertRaisesRegex(RegistrationRecoveryError, "cannot start"):
                service.require_work_start_allowed(
                    transaction, "project-1", "execution-activity"
                )

        assessment2, _manifest, _records, package2 = self.publish(
            activity_id, 2, "candidate-2", self.first.remote_commit,
            self.first_package, "2",
        )
        with self.assertRaisesRegex(RegistrationRecoveryError, "unknown finding or decision"):
            service.record_candidate(
                activity_id,
                package2,
                {
                    "summary-project-1": ("caller-invented-reason",),
                    "milestone-2": ("finding-2",),
                },
            )
        comparison = service.record_candidate_from_saved_reasons(
            activity_id, package2
        )
        self.assertTrue(comparison.differences)
        self.assertEqual(
            {"changed"}, {item.kind for item in comparison.differences}
        )
        self.assertEqual(self.first_package, self.confirmation.active("project-1").package_ref)
        self.assertEqual(
            service.load_continuity("project-1", activity_id),
            service.status(activity_id).continuity,
        )
        self.assertEqual(
            f"{activity_id}-question",
            service.status(activity_id).continuity.questions[0]["question_id"],
        )
        continuity = service.status(activity_id).continuity
        self.assertEqual("decision", continuity.decisions[0]["record_type"])
        self.assertIn(
            "decision-2",
            {item["record_id"] for item in continuity.decisions},
        )
        self.assertEqual(
            ("fidelity_reviewer", "project_architect"),
            tuple(item["role"] for item in continuity.runs),
        )
        self.assertEqual(
            ("anthropic/model-1", "openai/model-1"),
            tuple(item["runtime_identity"]["model_id"] for item in continuity.runs),
        )
        self.assertEqual(
            [{
                "counter_name": "automatic_recovery_attempts",
                "scope_id": "architect-assignment",
                "consumed": 1,
            }],
            list(continuity.recovery_counters),
        )
        self.assertEqual(self.process_snapshot, service.status(activity_id).process_snapshot)
        self.assertEqual(comparison, service.comparison(activity_id))

        cancelled = service.cancel(activity_id, "cancel-request")
        self.assertEqual("cancelled", cancelled.state)
        self.assertEqual(self.first_package, self.confirmation.active("project-1").package_ref)
        self.assertEqual(assessment2.status.review_count, 1)

    def test_cancellation_before_and_after_remote_write_reconciles_exact_git_state(self) -> None:
        service = self.recovery()
        self.begin(service, "activity-2", "begin-2")
        before_head = self.remote_head()
        self.interrupt_candidate_publication(
            "activity-2", "candidate-2", "cancel-before", before_head
        )
        cancelled = service.cancel(
            "activity-2", "cancel-before-action",
            operation_id="candidate-operation-cancel-before",
        )
        self.assertEqual("cancelled", cancelled.state)
        self.assertEqual(before_head, self.remote_head())
        self.assertEqual(
            "reconciled",
            self.journal.operation("candidate-operation-cancel-before").state,
        )

        self.begin(service, "activity-3", "begin-3")
        self.interrupt_candidate_publication(
            "activity-3", "candidate-3", "cancel-after", before_head
        )
        operation = self.journal.operation("candidate-operation-cancel-after")
        self.push_exact_files(operation.files)
        written_head = self.remote_head()
        with self.database.transaction() as transaction:
            transaction.execute(
                "UPDATE publication_operations SET state = 'writing' WHERE operation_id = ?",
                ("candidate-operation-cancel-after",),
            )
        restarted = self.recovery()
        cancelled = restarted.cancel(
            "activity-3", "cancel-after-action",
            operation_id="candidate-operation-cancel-after",
        )
        self.assertEqual("cancelled", cancelled.state)
        self.assertEqual(written_head, self.remote_head())
        self.assertEqual(
            "verified", self.journal.operation("candidate-operation-cancel-after").state
        )
        manifest_path = (
            ".maestro/registrations/versions/2/candidates/candidate-3/manifest.json"
        )
        self.assertEqual(
            operation.files[manifest_path],
            subprocess.check_output([
                "git", "--git-dir", str(self.remote), "show",
                f"main:{manifest_path}",
            ]),
        )
        self.assertEqual(self.first_package, self.confirmation.active("project-1").package_ref)

    def test_cancellation_conflict_pauses_and_keeps_the_reservation(self) -> None:
        service = self.recovery()
        self.begin(service, "activity-2", "begin-2")
        original_head = self.remote_head()
        self.interrupt_candidate_publication(
            "activity-2", "candidate-2", "cancel-conflict", original_head
        )
        operation_id = "candidate-operation-cancel-conflict"
        operation = self.journal.operation(operation_id)
        target = sorted(operation.files)[0]
        self.push_exact_files({target: b"conflicting package bytes\n"})
        conflict_head = self.remote_head()

        with self.assertRaisesRegex(PublicationConflictError, "conflicting"):
            service.cancel(
                "activity-2", "cancel-conflict-action", operation_id=operation_id
            )

        status = service.status("activity-2")
        self.assertEqual("paused", status.state)
        self.assertIn("Cancellation paused", status.failure or "")
        self.assertEqual(conflict_head, self.remote_head())
        self.assertEqual(self.first_package, self.confirmation.active("project-1").package_ref)
        with self.assertRaisesRegex(RegistrationRecoveryError, "already reserves"):
            self.begin(self.recovery(), "activity-3", "begin-3")

    def test_restart_recovers_pending_confirmation_with_only_original_profile(self) -> None:
        service = self.recovery()
        self.begin(service, "activity-2", "begin-2")
        assessment2, _manifest, _records, package2 = self.publish(
            "activity-2", 2, "candidate-2", self.first.remote_commit,
            self.first_package, "2",
        )
        service.record_candidate_from_saved_reasons("activity-2", package2)
        action = OwnerConfirmation(
            "confirmation-2", "confirmation-request-2", "project-1", "activity-2",
            1, package2, "2026-09-20T11:00:00Z",
        )
        self.api.block_at_authorization = self.api.authorization_count + 2
        with self.assertRaises(PublicationAccessError):
            self.confirmation.confirm(assessment2, VerifiedActor("owner-local"), action)
        self.api.block_at_authorization = None
        head_before = self.remote_head()
        self.assertEqual(self.first_package, self.confirmation.active("project-1").package_ref)

        operation_id = "registration-confirmation-confirmation-2"
        operation = self.journal.operation(operation_id)
        missing_credential_snapshot = dict(self.authorization.snapshot)
        missing_credential_snapshot.pop("credential_reference")
        missing_credential_reference = _snapshot_reference(missing_credential_snapshot)
        missing_operation_record = dict(operation.authorization_snapshot)
        missing_operation_record["snapshot"] = missing_credential_snapshot
        with self.database.transaction() as transaction:
            transaction.execute(
                """UPDATE registration_recovery_attempts
                   SET destination_snapshot_json = ?, destination_snapshot_reference = ?
                   WHERE activity_id = ?""",
                (
                    canonical_json(missing_credential_snapshot),
                    missing_credential_reference,
                    "activity-2",
                ),
            )
            transaction.execute(
                """UPDATE publication_operations SET authorization_snapshot = ?
                   WHERE operation_id = ?""",
                (canonical_json(missing_operation_record), operation_id),
            )
        missing_credential = self.recovery({
            missing_credential_reference: self.route
        })
        with self.assertRaisesRegex(RegistrationRecoverySetupError, "credential reference"):
            missing_credential.recover_confirmation(
                "activity-2", self.confirmation, assessment2,
                VerifiedActor("owner-local"), action,
                retry_request_id="confirmation-retry-1", automatic=True,
            )
        self.assertEqual("paused", missing_credential.status("activity-2").state)
        self.assertEqual(head_before, self.remote_head())
        with self.database.transaction() as transaction:
            transaction.execute(
                """UPDATE registration_recovery_attempts
                   SET destination_snapshot_json = ?, destination_snapshot_reference = ?
                   WHERE activity_id = ?""",
                (
                    canonical_json(dict(self.authorization.snapshot)),
                    self.snapshot_reference,
                    "activity-2",
                ),
            )
            transaction.execute(
                """UPDATE publication_operations SET authorization_snapshot = ?
                   WHERE operation_id = ?""",
                (canonical_json(operation.authorization_snapshot), operation_id),
            )

        missing = self.recovery({})
        with self.assertRaisesRegex(RegistrationRecoverySetupError, "unavailable"):
            missing.recover_confirmation(
                "activity-2", self.confirmation, assessment2,
                VerifiedActor("owner-local"), action,
                retry_request_id="confirmation-retry-1", automatic=True,
            )
        self.assertEqual("paused", missing.status("activity-2").state)
        self.assertEqual(head_before, self.remote_head())

        changed_profile = replace(self.profile, app_slug="changed-app")
        changed_provider = GitHubDestinationProvider(changed_profile, _DestinationApi())
        changed_journal = PublicationJournal(
            self.database, self.authorizer, self.transport, changed_provider
        )
        changed = self.recovery({
            self.snapshot_reference: HistoricalPublicationRoute(changed_journal, changed_provider)
        })
        with self.assertRaisesRegex(RegistrationRecoverySetupError, "changed"):
            changed.recover_confirmation(
                "activity-2",
                RegistrationConfirmationService(self.database, changed_journal, changed_provider),
                assessment2, VerifiedActor("owner-local"), action,
                retry_request_id="confirmation-retry-1", automatic=True,
            )
        self.assertEqual("paused", changed.status("activity-2").state)
        self.assertEqual(head_before, self.remote_head())

        blocked_api = _DestinationApi()
        blocked_api.policy = BranchPolicyObservation(True, ())
        blocked_provider = GitHubDestinationProvider(self.profile, blocked_api)
        blocked_journal = PublicationJournal(
            self.database, self.authorizer, self.transport, blocked_provider
        )
        blocked = self.recovery({
            self.snapshot_reference: HistoricalPublicationRoute(blocked_journal, blocked_provider)
        })
        with self.assertRaisesRegex(RegistrationRecoverySetupError, "blocked"):
            blocked.recover_confirmation(
                "activity-2",
                RegistrationConfirmationService(self.database, blocked_journal, blocked_provider),
                assessment2, VerifiedActor("owner-local"), action,
                retry_request_id="confirmation-retry-1", automatic=True,
            )
        self.assertEqual("paused", blocked.status("activity-2").state)
        self.assertEqual(head_before, self.remote_head())

        failed_api = _DestinationApi()
        failed_api.unverifiable = True
        failed_provider = GitHubDestinationProvider(self.profile, failed_api)
        failed_journal = PublicationJournal(
            self.database, self.authorizer, self.transport, failed_provider
        )
        unverifiable = self.recovery({
            self.snapshot_reference: HistoricalPublicationRoute(failed_journal, failed_provider)
        })
        with self.assertRaisesRegex(RegistrationRecoverySetupError, "unverifiable"):
            unverifiable.recover_confirmation(
                "activity-2",
                RegistrationConfirmationService(self.database, failed_journal, failed_provider),
                assessment2, VerifiedActor("owner-local"), action,
                retry_request_id="confirmation-retry-1", automatic=True,
            )
        self.assertEqual("paused", unverifiable.status("activity-2").state)
        self.assertEqual(head_before, self.remote_head())

        restarted = self.recovery()
        result = restarted.recover_confirmation(
            "activity-2", self.confirmation, assessment2,
            VerifiedActor("owner-local"), action,
            retry_request_id="confirmation-retry-1", automatic=True,
        )
        self.assertEqual(package2, result.package_ref)
        self.assertEqual(package2, self.confirmation.active("project-1").package_ref)
        status = restarted.status("activity-2")
        self.assertEqual("completed", status.state)
        self.assertEqual(
            restarted.load_continuity("project-1", "activity-2"),
            status.continuity,
        )
        self.assertEqual((1, 0), (
            status.automatic_publication_retries, status.manual_publication_retries
        ))
        self.assertEqual(
            ("confirmation-1", "confirmation-2"),
            tuple(item.confirmation_id for item in self.confirmation.history("project-1")),
        )
        replay = self.recovery().recover_confirmation(
            "activity-2", self.confirmation, assessment2,
            VerifiedActor("owner-local"), action,
            retry_request_id="confirmation-retry-1", automatic=True,
        )
        self.assertEqual(result, replay)
        self.assertEqual(
            1, self.recovery().status("activity-2").automatic_publication_retries
        )

    def test_retry_reconciles_before_write_and_preserves_counts_across_restart(self) -> None:
        service = self.recovery()
        self.begin(service, "activity-2", "begin-2")
        head = self.remote_head()
        assessment, manifest, records = self.interrupt_candidate_publication(
            "activity-2", "candidate-2", "retry", head
        )
        package = service.recover_candidate_publication(
            "activity-2", self.confirmation, assessment,
            activity_version=1,
            manifest=manifest,
            records=records,
            remote=str(self.remote),
            expected_parent=head,
            operation_id="candidate-operation-retry",
            publication_request_id="candidate-request-retry",
            retry_request_id="automatic-retry-1",
            automatic=True,
        )
        self.assertEqual("candidate-2", package.candidate_id)
        self.assertEqual("applied", self.journal.operation("candidate-operation-retry").state)
        status = service.status("activity-2")
        self.assertEqual(1, status.automatic_publication_retries)
        self.assertEqual(
            service.load_continuity("project-1", "activity-2"),
            status.continuity,
        )
        self.assertEqual(1, status.continuity.retry_counts["automatic_publication"])
        self.assertIn(
            {
                "counter_name": "automatic_recovery_attempts",
                "scope_id": "candidate-operation-retry",
                "consumed": 1,
            },
            status.continuity.recovery_counters,
        )

        restarted = self.recovery()
        replay = restarted.recover_candidate_publication(
            "activity-2", self.confirmation, assessment,
            activity_version=1,
            manifest=manifest,
            records=records,
            remote=str(self.remote),
            expected_parent=head,
            operation_id="candidate-operation-retry",
            publication_request_id="candidate-request-retry",
            retry_request_id="automatic-retry-1",
            automatic=True,
        )
        self.assertEqual(package, replay)
        self.assertEqual(1, restarted.status("activity-2").automatic_publication_retries)
        manifest_path = package.manifest_path
        self.assertEqual(
            self.journal.operation("candidate-operation-retry").files[manifest_path],
            subprocess.check_output([
                "git", "--git-dir", str(self.remote), "show",
                f"main:{manifest_path}",
            ]),
        )

    def test_each_candidate_retry_dispatch_is_counted_once_and_limit_pauses(self) -> None:
        service = self.recovery()
        self.begin(service, "activity-2", "begin-2")
        head = self.remote_head()
        assessment, manifest, records = self.interrupt_candidate_publication(
            "activity-2", "candidate-2", "counted", head
        )

        for request_id in ("automatic-retry-1", "automatic-retry-2"):
            self.api.block_at_authorization = self.api.authorization_count + 3
            with self.assertRaises(PublicationAccessError):
                service.recover_candidate_publication(
                    "activity-2", self.confirmation, assessment,
                    activity_version=1, manifest=manifest, records=records,
                    remote=str(self.remote), expected_parent=head,
                    operation_id="candidate-operation-counted",
                    publication_request_id="candidate-request-counted",
                    retry_request_id=request_id, automatic=True,
                )
            self.api.block_at_authorization = None
            self.assertEqual(head, self.remote_head())

        with self.assertRaisesRegex(RegistrationRecoveryError, "allowance is exhausted"):
            service.recover_candidate_publication(
                "activity-2", self.confirmation, assessment,
                activity_version=1, manifest=manifest, records=records,
                remote=str(self.remote), expected_parent=head,
                operation_id="candidate-operation-counted",
                publication_request_id="candidate-request-counted",
                retry_request_id="automatic-retry-3", automatic=True,
            )
        status = service.status("activity-2")
        self.assertEqual("paused", status.state)
        self.assertEqual(2, status.automatic_publication_retries)
        self.assertIn("allowance is exhausted", status.failure or "")
        self.assertEqual(head, self.remote_head())

        with self.assertRaisesRegex(RegistrationRecoveryError, "already dispatched"):
            service.recover_candidate_publication(
                "activity-2", self.confirmation, assessment,
                activity_version=1, manifest=manifest, records=records,
                remote=str(self.remote), expected_parent=head,
                operation_id="candidate-operation-counted",
                publication_request_id="candidate-request-counted",
                retry_request_id="automatic-retry-1", automatic=True,
            )
        self.assertEqual(2, service.status("activity-2").automatic_publication_retries)
        self.assertEqual(head, self.remote_head())

    def test_confirmation_retry_limit_and_saved_continuity_are_enforced(self) -> None:
        service = self.recovery()
        self.save_registration_history("activity-2")
        continuity = service.load_continuity("project-1", "activity-2")
        reviewer_run = next(
            item for item in continuity.runs if item["role"] == "fidelity_reviewer"
        )
        with self.database.transaction() as transaction:
            transaction.execute(
                """UPDATE registration_assessment_runs SET runtime_identity_json = NULL
                   WHERE activity_id = ? AND role = ?""",
                ("activity-2", "fidelity_reviewer"),
            )
        with self.assertRaisesRegex(RegistrationRecoveryError, "runtime identity"):
            service.load_continuity("project-1", "activity-2")
        with self.database.transaction() as transaction:
            transaction.execute(
                """UPDATE registration_assessment_runs SET runtime_identity_json = ?
                   WHERE activity_id = ? AND role = ?""",
                (
                    canonical_json(reviewer_run["runtime_identity"]),
                    "activity-2", "fidelity_reviewer",
                ),
            )
        changed_definition = dict(self.process_snapshot.definition)
        changed_definition["maximum_fidelity_reviews"] = 3
        changed_definition_json = canonical_json(changed_definition)
        forged_process = ProcessSnapshot(
            "registration", changed_definition_json,
            hashlib.sha256(changed_definition_json.encode("utf-8")).hexdigest(),
            self.process_snapshot.bundle,
        )
        with self.assertRaisesRegex(RegistrationRecoveryError, "authoritative saved policy"):
            service.begin(
                request_id="forged-process", project_id="project-1",
                activity_id="activity-2", destination_authorization=self.authorization,
                continuity=continuity, process_snapshot=forged_process,
            )
        fabricated = replace(
            continuity,
            questions=({"question_id": "invented", "answer": "unsupported"},),
        )
        with self.assertRaisesRegex(RegistrationRecoveryError, "authoritative saved history"):
            service.begin(
                request_id="fabricated-begin", project_id="project-1",
                activity_id="activity-2", destination_authorization=self.authorization,
                continuity=fabricated, process_snapshot=self.process_snapshot,
            )
        self.begin(service, "activity-2", "begin-2")
        assessment, _manifest, _records, package = self.publish(
            "activity-2", 2, "candidate-2", self.first.remote_commit,
            self.first_package, "2",
        )
        service.record_candidate_from_saved_reasons("activity-2", package)
        action = OwnerConfirmation(
            "confirmation-2", "confirmation-request-2", "project-1", "activity-2",
            1, package, "2026-09-20T11:00:00Z",
        )
        self.api.block_at_authorization = self.api.authorization_count + 2
        with self.assertRaises(PublicationAccessError):
            self.confirmation.confirm(
                assessment, VerifiedActor("owner-local"), action
            )
        self.api.block_at_authorization = None
        with self.database.transaction() as transaction:
            transaction.execute(
                """UPDATE registration_recovery_attempts
                   SET automatic_publication_limit = 0 WHERE activity_id = ?""",
                ("activity-2",),
            )
        head = self.remote_head()
        with self.assertRaisesRegex(RegistrationRecoveryError, "allowance is exhausted"):
            service.recover_confirmation(
                "activity-2", self.confirmation, assessment,
                VerifiedActor("owner-local"), action,
                retry_request_id="confirmation-retry-limit", automatic=True,
            )
        status = service.status("activity-2")
        self.assertEqual("paused", status.state)
        self.assertEqual(0, status.automatic_publication_retries)
        self.assertIn("allowance is exhausted", status.failure or "")
        self.assertEqual(head, self.remote_head())

        with self.database.transaction() as transaction:
            row = transaction.execute(
                """SELECT state_json FROM registration_assessment_state
                   WHERE activity_id = ?""",
                ("activity-2",),
            ).fetchone()
            assert row is not None
            changed = json.loads(str(row[0]))
            changed["review_count"] = 0
            transaction.execute(
                """UPDATE registration_assessment_state SET state_json = ?
                   WHERE activity_id = ?""",
                (canonical_json(changed), "activity-2"),
            )
        with self.assertRaisesRegex(RegistrationRecoveryError, "authoritative history"):
            self.recovery().status("activity-2")

    def interrupt_candidate_publication(
        self, activity_id: str, candidate_id: str, publication_id: str, parent: str
    ):
        assessment, manifest, records = self.package(
            activity_id, 2, candidate_id, self.first_package
        )
        self.api.block_at_authorization = self.api.authorization_count + 2
        with self.assertRaises(PublicationAccessError):
            self.confirmation.publish_candidate(
                assessment,
                activity_version=1,
                manifest=manifest,
                records=records,
                remote=str(self.remote),
                expected_parent=parent,
                operation_id=f"candidate-operation-{publication_id}",
                request_id=f"candidate-request-{publication_id}",
            )
        self.api.block_at_authorization = None
        return assessment, manifest, records

    def package(
        self,
        activity_id: str,
        registration_version: int,
        candidate_id: str,
        previous: RegistrationPackageReference | None,
    ) -> tuple[RegistrationAssessment, dict[str, object], dict[str, dict[str, object]]]:
        inventory = SourceInventory(
            "refs/heads/main", "b" * 40, "docs/overview.md",
            (SourceBlob.from_bytes("docs/overview.md", b"# Overview\n"),),
            source_references=(SourceReference("Architecture", "Overview", "docs/overview.md"),),
            outcomes=(OutcomeReference("APP", "Application", 1, "APP-PM1", "Start", 1),),
        )
        snapshot_reference = getattr(self, "snapshot_reference", None)
        if snapshot_reference is None:
            snapshot_reference = _snapshot_reference(
                self.provider.authorize("owner/project", "main").snapshot
            )
        decision_reference = _selection_decision_reference(
            "owner/project", "supplied", inventory.source_ref,
            inventory.source_commit, inventory.overview_path, "main",
            snapshot_reference, "b" * 40, selected_scope="APP-PM1",
        )
        context = RegistrationPackageContext(
            "project-1", "owner/project", inventory, decision_reference, "main",
            snapshot_reference, decision_reference,
        )
        manifest, records = complete_package(
            context,
            registration_version=registration_version,
            candidate_id=candidate_id,
            previous_registration_ref=(
                None if previous is None else previous.as_dict()
            ),
            review_context={
                "architect_assignment_id": "architect-assignment",
                "architect_run_id": "architect-run",
                "assignment_id": "reviewer-assignment",
                "run_id": "reviewer-run",
                "reviewer_identity": "reviewer-agent",
                "review_round": 1,
                "review_limit": 2,
            },
        )
        artifact = {
            "path": "candidate/manifest.json",
            "sha256": hashlib.sha256(canonical_record_bytes(manifest)).hexdigest(),
            "version": candidate_id,
        }
        route = ResolvedAgentRoute(
            "architect", "codex", "openai/model-1", "openai", "1", "/tool",
            "credential", "settings", "cloud",
            ("code_edit", "local_command", "repository_search", "approved_network"),
            65536, (), "c" * 64,
        )
        reviewer = replace(
            route, role="fidelity_reviewer", tool="claude_code",
            requested_model_id="anthropic/model-1", provider="anthropic",
        )
        assessment = RegistrationAssessment(AssessmentContext(
            "project-1", activity_id, inventory, decision_reference, "APP-PM1",
            "architect-agent", "reviewer-agent", ResolvedRoleRoutes(route, reviewer),
            AssessmentRun("architect-assignment", "architect-run"),
            AssessmentRun("reviewer-assignment", "reviewer-run"), context,
        ))
        assessment.submit_architect(
            _response("project_architect", activity_id, artifact, decision_reference),
            RunningToolIdentity("tool_metadata", "openai", "openai/model-1", "1", "c" * 64),
        )
        assessment.submit_reviewer(
            _response("fidelity_reviewer", activity_id, artifact, decision_reference),
            RunningToolIdentity("tool_metadata", "anthropic", "anthropic/model-1", "1", "c" * 64),
        )
        return assessment, manifest, records

    def publish(
        self,
        activity_id: str,
        version: int,
        candidate_id: str,
        parent: str,
        previous: RegistrationPackageReference | None,
        publication_id: str,
    ):
        assessment, manifest, records = self.package(
            activity_id, version, candidate_id, previous
        )
        package = self.confirmation.publish_candidate(
            assessment,
            activity_version=1,
            manifest=manifest,
            records=records,
            remote=str(self.remote),
            expected_parent=parent,
            operation_id=f"candidate-operation-{publication_id}",
            request_id=f"candidate-request-{publication_id}",
        )
        return assessment, manifest, records, package

    def remote_head(self) -> str:
        return self.output("git", "--git-dir", str(self.remote), "rev-parse", "main")

    def push_exact_files(self, files: dict[str, bytes]) -> None:
        clone = self.root / f"lost-ack-{len(list(self.root.glob('lost-ack-*')))}"
        self.git("git", "clone", "--quiet", "--branch", "main", str(self.remote), str(clone))
        self.git("git", "-C", str(clone), "config", "user.name", "Fixture")
        self.git("git", "-C", str(clone), "config", "user.email", "fixture@example.invalid")
        for path, content in files.items():
            target = clone / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
            self.git("git", "-C", str(clone), "add", path)
        self.git("git", "-C", str(clone), "commit", "--quiet", "-m", "lost acknowledgment")
        self.git("git", "-C", str(clone), "push", "--quiet", "origin", "main")

    def git(self, *command: str) -> None:
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        if result.returncode:
            self.fail(result.stderr.decode("utf-8", "replace"))

    def output(self, *command: str) -> str:
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        if result.returncode:
            self.fail(result.stderr.decode("utf-8", "replace"))
        return result.stdout.decode("ascii").strip()


def _response(
    role: str, activity_id: str, artifact: dict[str, str], decision_version: str
) -> RegistrationAgentResponse:
    return RegistrationAgentResponse.from_mapping({
        "contract_version": 1,
        "assignment_id": "architect-assignment" if role == "project_architect" else "reviewer-assignment",
        "run_id": "architect-run" if role == "project_architect" else "reviewer-run",
        "project_id": "project-1",
        "activity_id": activity_id,
        "role": role,
        "source_commit": "b" * 40,
        "decision_version": decision_version,
        "result": "completed",
        "summary": "Ready candidate.",
        "findings": [],
        "questions": [],
        "candidate": artifact,
        "assessment": (
            {"path": "assessment.json", "sha256": "d" * 64, "version": "assessment-1"}
            if role == "project_architect" else None
        ),
        "reviewed_assessment": (
            {"path": "assessment.json", "sha256": "d" * 64, "version": "assessment-1"}
            if role == "fidelity_reviewer" else None
        ),
        "review_outcome": "APPROVE" if role == "fidelity_reviewer" else None,
        "failure": None,
    })


class _DestinationApi:
    """Controlled authorization input; publication itself uses real Git."""

    def __init__(self) -> None:
        self.policy = BranchPolicyObservation(False, ())
        self.authorization_count = 0
        self.block_at_authorization: int | None = None
        self.unverifiable = False

    def app_identity(self, profile):
        self.authorization_count += 1
        if self.unverifiable:
            raise OSError("provider unavailable")
        return {"id": profile.app_id, "slug": profile.app_slug}

    def installation_identity(self, profile):
        return {"id": profile.installation_id, "app_id": profile.app_id}

    def installation_token(self, profile):
        return GitHubInstallationToken(
            "fixture-installation-token",
            {"contents": "write", "administration": "read"},
            4_102_444_800,
            profile.api_base_url,
        )

    def repository_identity(self, _token, repository):
        return {"id": 1, "full_name": repository}

    def branch_identity(self, _token, _repository, branch):
        return {"name": branch, "commit": {"sha": "a" * 40}}

    def branch_policy(self, _token, _repository, _branch):
        if (
            self.block_at_authorization is not None
            and self.authorization_count >= self.block_at_authorization
        ):
            return BranchPolicyObservation(True, ())
        return self.policy


def _snapshot_reference(snapshot) -> str:
    return hashlib.sha256(
        json.dumps(dict(snapshot), sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


if __name__ == "__main__":
    unittest.main()
