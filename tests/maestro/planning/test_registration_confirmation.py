from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
import unittest
from dataclasses import dataclass, replace
from pathlib import Path

from maestro.agents.preflight import ResolvedAgentRoute, ResolvedRoleRoutes, RunningToolIdentity
from maestro.foundation import Database, StorageSettings
from maestro.foundation.credentials import (
    RepositoryAuthorizer,
    RepositoryBinding,
    RepositoryProfile,
    ServiceGitRoute,
    ServiceGitTransport,
)
from maestro.foundation.git_publication import (
    PublicationAccessError,
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
from maestro.planning.registration_confirmation import (
    OwnerConfirmation,
    RegistrationConfirmationError,
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
from maestro.planning.sources import OutcomeReference, SourceBlob, SourceInventory, SourceReference
from maestro.service.authentication import VerifiedActor
from maestro.terminal.connection import TerminalConnectionError
from maestro.terminal.extensions import ExtensionContext, ExtensionRegistry
from maestro.terminal.registration import RegistrationExtension, RegistrationInteraction


class RegistrationConfirmationTest(unittest.TestCase):
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
        transport = ServiceGitTransport(
            (ServiceGitRoute("owner/project", "github-app-project", str(self.remote)),),
            lambda reference: self.credentials[reference],
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
        self.destination_api = _DestinationApi()
        self.destination = GitHubDestinationProvider(self.profile, self.destination_api)
        database = Database(
            StorageSettings(path=self.root / "maestro.sqlite3"),
            (*publication_migrations(), *registration_confirmation_migrations()),
        )
        journal = PublicationJournal(
            database,
            RepositoryAuthorizer(
                {repository_profile.name: repository_profile},
                (RepositoryBinding("binding-project", "owner/project", repository_profile.name),),
            ),
            transport,
            self.destination,
        )
        self.journal = journal
        self.service = RegistrationConfirmationService(database, journal, self.destination)
        initial = self.destination.authorize("owner/project", "main")
        self.snapshot_reference = hashlib.sha256(
            json.dumps(
                dict(initial.snapshot), sort_keys=True, separators=(",", ":")
            ).encode("utf-8")
        ).hexdigest()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def git(self, *command: str) -> None:
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        if result.returncode:
            self.fail(result.stderr.decode("utf-8", "replace"))

    def output(self, *command: str) -> str:
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        if result.returncode:
            self.fail(result.stderr.decode("utf-8", "replace"))
        return result.stdout.decode("ascii").strip()

    def package(
        self,
        *,
        activity_id: str,
        registration_version: int,
        candidate_id: str,
        previous: RegistrationPackageReference | None = None,
    ) -> tuple[RegistrationAssessment, dict[str, object], dict[str, dict[str, object]]]:
        record = {
            "schema_version": 1,
            "record_type": "summary",
            "record_id": f"summary-{registration_version}",
            "subject": "Project summary",
            "record_version": registration_version,
            "data": {},
        }
        record_hash = hashlib.sha256(canonical_record_bytes(record)).hexdigest()
        records = {"summary.json": record}
        inventory = SourceInventory(
            "refs/heads/main",
            "b" * 40,
            "docs/overview.md",
            (SourceBlob.from_bytes("docs/overview.md", b"# Overview\n"),),
            source_references=(SourceReference("Architecture", "Overview", "docs/overview.md"),),
            outcomes=(OutcomeReference("APP", 1, "APP-PM1", "Start", 1),),
        )
        context = RegistrationPackageContext(
            "project-1",
            "owner/project",
            inventory,
            "decision-1",
            "main",
            self.snapshot_reference,
            "decision/source-selection-1",
        )
        manifest: dict[str, object] = {
            "project_id": "project-1",
            "registration_version": registration_version,
            "candidate_id": candidate_id,
            "previous_registration_ref": None if previous is None else previous.as_dict(),
            "source_repository": "owner/project",
            "source_commit": inventory.source_commit,
            "overview_path": inventory.overview_path,
            "decision_version": "decision-1",
            "source_ref": inventory.source_ref,
            "publication_branch": "main",
            "destination_snapshot_reference": self.snapshot_reference,
            "selection_decision_ref": "decision/source-selection-1",
            "content_hash": package_content_hash(records),
            "files": [
                {
                    "path": "summary.json",
                    "record_id": record["record_id"],
                    "record_type": record["record_type"],
                    "record_version": record["record_version"],
                    "subject": record["subject"],
                    "sha256": record_hash,
                }
            ],
        }
        manifest_hash = hashlib.sha256(canonical_record_bytes(manifest)).hexdigest()
        route = ResolvedAgentRoute(
            "architect", "codex", "openai/model-1", "openai", "1", "/tool",
            "credential", "settings", "cloud",
            ("code_edit", "local_command", "repository_search", "approved_network"),
            65536, (), "c" * 64,
        )
        reviewer = replace(
            route,
            role="fidelity_reviewer",
            tool="claude_code",
            requested_model_id="anthropic/model-1",
            provider="anthropic",
        )
        assessment = RegistrationAssessment(
            AssessmentContext(
                "project-1", activity_id, inventory, "decision-1", "APP-PM1",
                "architect-agent", "reviewer-agent", ResolvedRoleRoutes(route, reviewer),
                AssessmentRun("architect-assignment", "architect-run"),
                AssessmentRun("reviewer-assignment", "reviewer-run"), context,
            )
        )
        artifact = {"path": "candidate/manifest.json", "sha256": manifest_hash, "version": candidate_id}
        assessment.submit_architect(
            _response("project_architect", activity_id, artifact),
            RunningToolIdentity("tool_metadata", "openai", "openai/model-1", "1", "c" * 64),
        )
        assessment.submit_reviewer(
            _response("fidelity_reviewer", activity_id, artifact),
            RunningToolIdentity("tool_metadata", "anthropic", "anthropic/model-1", "1", "c" * 64),
        )
        return assessment, manifest, records

    def publish(
        self, activity_id: str, version: int, candidate_id: str,
        parent: str, previous: RegistrationPackageReference | None = None,
        publication_id: str | None = None,
    ):
        assessment, manifest, records = self.package(
            activity_id=activity_id,
            registration_version=version,
            candidate_id=candidate_id,
            previous=previous,
        )
        reference = self.service.publish_candidate(
            assessment,
            activity_version=1,
            manifest=manifest,
            records=records,
            remote=str(self.remote),
            expected_parent=parent,
            operation_id=f"candidate-operation-{publication_id or version}",
            request_id=f"candidate-request-{publication_id or version}",
        )
        return assessment, reference

    def test_publishes_confirms_updates_index_and_preserves_history(self) -> None:
        assessment1, package1 = self.publish("activity-1", 1, "candidate-1", self.seed)
        published_manifest = subprocess.check_output(
            [
                "git", "--git-dir", str(self.remote), "show",
                f"{package1.commit}:{package1.manifest_path}",
            ]
        )
        self.assertEqual(
            package1.manifest_sha256, hashlib.sha256(published_manifest).hexdigest()
        )
        first = self.service.confirm(
            assessment1,
            VerifiedActor("owner-local"),
            OwnerConfirmation(
                "confirmation-1", "confirmation-request-1", "project-1", "activity-1",
                1, package1, "2026-09-20T10:00:00Z",
            ),
        )
        first_replay = self.service.confirm(
            assessment1,
            VerifiedActor("owner-local"),
            OwnerConfirmation(
                "confirmation-1", "confirmation-request-1", "project-1", "activity-1",
                1, package1, "2026-09-20T10:00:00Z",
            ),
        )
        self.assertEqual(first, first_replay)
        self.assertEqual("applied", self.journal.operation("candidate-operation-1").state)
        self.assertEqual(
            "applied", self.journal.operation("registration-confirmation-confirmation-1").state
        )

        assessment2, package2 = self.publish(
            "activity-2", 2, "candidate-2", first.remote_commit, package1
        )
        second = self.service.confirm(
            assessment2,
            VerifiedActor("owner-local"),
            OwnerConfirmation(
                "confirmation-2", "confirmation-request-2", "project-1", "activity-2",
                1, package2, "2026-09-20T11:00:00Z",
            ),
        )

        self.assertEqual("Registered", second.status)
        self.assertEqual(package2, self.service.active("project-1").package_ref)
        self.assertEqual(
            ("confirmation-1", "confirmation-2"),
            tuple(item.confirmation_id for item in self.service.history("project-1")),
        )
        index = json.loads(
            subprocess.check_output(
                ["git", "--git-dir", str(self.remote), "show", "main:.maestro/registrations/index.json"]
            )
        )
        self.assertEqual("confirmation-2", index["current_confirmation_ref"]["confirmation_id"])
        self.assertEqual(2, len(index["confirmation_refs"]))
        self.assertGreaterEqual(self.destination_api.authorization_count, 10)
        self.assertFalse(hasattr(self.service, "start_architecture"))
        self.assertFalse(hasattr(self.service, "start_execution"))

    def test_older_candidate_cannot_replace_newer_active_registration(self) -> None:
        assessment1, package1 = self.publish("activity-1", 1, "candidate-1", self.seed)
        first = self.service.confirm(
            assessment1,
            VerifiedActor("owner-local"),
            OwnerConfirmation(
                "confirmation-1", "confirmation-request-1", "project-1", "activity-1",
                1, package1, "2026-09-20T10:00:00Z",
            ),
        )
        assessment2, package2 = self.publish(
            "activity-2", 2, "candidate-2", first.remote_commit, package1,
            publication_id="2",
        )
        assessment3, package3 = self.publish(
            "activity-3", 2, "candidate-3", package2.commit, package1,
            publication_id="3",
        )
        self.service.confirm(
            assessment3,
            VerifiedActor("owner-local"),
            OwnerConfirmation(
                "confirmation-3", "confirmation-request-3", "project-1", "activity-3",
                1, package3, "2026-09-20T12:00:00Z",
            ),
        )
        head_before = self.output("git", "--git-dir", str(self.remote), "rev-parse", "main")
        index_before = subprocess.check_output(
            ["git", "--git-dir", str(self.remote), "show", "main:.maestro/registrations/index.json"]
        )
        history_before = self.service.history("project-1")
        active_before = self.service.active("project-1")

        with self.assertRaisesRegex(
            RegistrationConfirmationError, "previous registration differs"
        ):
            self.service.confirm(
                assessment2,
                VerifiedActor("owner-local"),
                OwnerConfirmation(
                    "confirmation-2", "confirmation-request-2", "project-1", "activity-2",
                    1, package2, "2026-09-20T11:00:00Z",
                ),
            )

        self.assertEqual(
            head_before,
            self.output("git", "--git-dir", str(self.remote), "rev-parse", "main"),
        )
        self.assertEqual(
            index_before,
            subprocess.check_output(
                ["git", "--git-dir", str(self.remote), "show", "main:.maestro/registrations/index.json"]
            ),
        )
        self.assertEqual(history_before, self.service.history("project-1"))
        self.assertEqual(active_before, self.service.active("project-1"))

    def test_rejects_unpublished_stale_changed_and_competing_confirmation(self) -> None:
        assessment, package = self.publish("activity-1", 1, "candidate-1", self.seed)
        remote_before = self.output("git", "--git-dir", str(self.remote), "rev-parse", "main")
        unpublished_assessment, unpublished_manifest, _unpublished_records = self.package(
            activity_id="activity-2", registration_version=2, candidate_id="candidate-2"
        )
        unpublished = RegistrationPackageReference(
            "owner/project",
            remote_before,
            2,
            "candidate-2",
            ".maestro/registrations/versions/2/candidates/candidate-2/manifest.json",
            hashlib.sha256(canonical_record_bytes(unpublished_manifest)).hexdigest(),
        )
        with self.assertRaisesRegex(RegistrationConfirmationError, "unpublished"):
            self.service.confirm(
                unpublished_assessment,
                VerifiedActor("owner-local"),
                OwnerConfirmation(
                    "unknown-confirmation", "unknown-request", "project-1", "activity-2", 1,
                    unpublished, "2026-09-20T10:00:00Z",
                ),
            )
        with self.assertRaisesRegex(RegistrationConfirmationError, "stale"):
            self.service.confirm(
                assessment,
                VerifiedActor("owner-local"),
                OwnerConfirmation(
                    "stale-confirmation", "stale-request", "project-1", "activity-1", 2,
                    package, "2026-09-20T10:00:00Z",
                ),
            )
        with self.assertRaisesRegex(RegistrationConfirmationError, "reference changed"):
            self.service.confirm(
                assessment,
                VerifiedActor("owner-local"),
                OwnerConfirmation(
                    "changed-confirmation", "changed-request", "project-1", "activity-1", 1,
                    replace(package, manifest_sha256="f" * 64), "2026-09-20T10:00:00Z",
                ),
            )
        self.destination_api.policy = BranchPolicyObservation(True, ())
        with self.assertRaises(PublicationAccessError):
            self.service.confirm(
                assessment,
                VerifiedActor("owner-local"),
                OwnerConfirmation(
                    "pending-confirmation", "pending-request", "project-1", "activity-1", 1,
                    package, "2026-09-20T10:00:00Z",
                ),
            )
        with self.assertRaisesRegex(RegistrationConfirmationError, "another confirmation is pending"):
            self.service.confirm(
                assessment,
                VerifiedActor("owner-local"),
                OwnerConfirmation(
                    "competing-confirmation", "competing-request", "project-1", "activity-1", 1,
                    package, "2026-09-20T10:01:00Z",
                ),
            )
        self.assertIsNone(self.service.active("project-1"))
        self.assertEqual(
            remote_before,
            self.output("git", "--git-dir", str(self.remote), "rev-parse", "main"),
        )
        self.destination_api.policy = BranchPolicyObservation(False, ())
        recovered = self.service.confirm(
            assessment,
            VerifiedActor("owner-local"),
            OwnerConfirmation(
                "pending-confirmation", "pending-request", "project-1", "activity-1", 1,
                package, "2026-09-20T10:00:00Z",
            ),
        )
        self.assertEqual("Registered", recovered.status)

    def test_terminal_extension_submits_only_the_displayed_exact_candidate(self) -> None:
        package = {
            "repository": "owner/project", "commit": "a" * 40,
            "registration_version": 1, "candidate_id": "candidate-1",
            "manifest_path": ".maestro/registrations/versions/1/candidates/candidate-1/manifest.json",
            "manifest_sha256": "b" * 64,
        }
        client = _TerminalClient({
            "data": {
                "project_id": "project-1", "activity_id": "activity-1",
                "activity_version": 3, "state": "Ready to confirm",
                "package_ref": package, "comparison": None, "agent_retry": None,
                "history": [], "can_confirm": True,
            }
        })
        state = _TerminalState("project-1", "unrelated-activity")
        context = ExtensionContext(client, state)
        registry = ExtensionRegistry()
        interaction = RegistrationInteraction(
            request_id_factory=lambda: "request-1",
            confirmation_id_factory=lambda: "confirmation-1",
            time_factory=lambda: "2026-09-20T10:00:00Z",
        )
        RegistrationExtension(interaction).install(registry)

        rendered = registry.invoke_command("registration", context)
        self.assertIn("candidate-1", rendered)
        self.assertEqual("activity-1", state.selected_activity_id)
        self.assertEqual(
            "/projects/project-1/registration", client.requested_paths[0]
        )
        with self.assertRaisesRegex(ValueError, "displayed exact candidate"):
            registry.invoke_action("registration-confirm", context, "candidate-other")
        registry.invoke_action("registration-confirm", context, "candidate-1")

        self.assertEqual("registration.confirm", client.submissions[0]["operation"])
        self.assertEqual(package, client.submissions[0]["payload"]["package_ref"])
        self.assertEqual(3, client.submissions[0]["expected_version"])

    def test_terminal_preserves_lost_acknowledgment_across_projects(self) -> None:
        package1 = _terminal_package("candidate-1", "a")
        package2 = _terminal_package("candidate-2", "c")
        client = _TerminalClient(_terminal_detail("project-1", "activity-1", package1))
        client.connection_failures = 1
        state = _TerminalState("project-1", "activity-1")
        context = ExtensionContext(client, state)
        interaction = RegistrationInteraction(
            request_id_factory=lambda: "request-1",
            confirmation_id_factory=lambda: "confirmation-1",
            time_factory=lambda: "2026-09-20T10:00:00Z",
        )
        registry = ExtensionRegistry()
        RegistrationExtension(interaction).install(registry)
        registry.invoke_command("registration", context)
        with self.assertRaises(TerminalConnectionError):
            registry.invoke_action("registration-confirm", context, "candidate-1")

        state.selected_project_id = "project-2"
        state.selected_activity_id = "activity-2"
        client.detail = _terminal_detail("project-2", "activity-2", package2)
        rendered = registry.invoke_command("registration", context)
        self.assertIn("request-1", rendered)
        with self.assertRaisesRegex(ValueError, "remains unresolved"):
            registry.invoke_action("registration-confirm", context, "candidate-2")
        self.assertEqual("request-1", interaction.pending.request_id)
        self.assertEqual(1, len(client.submissions))

        client.request_response = {
            "receipt": {"request_id": "request-1", "status": "completed"}
        }
        registry.invoke_action("registration-retry", context)
        self.assertIsNone(interaction.pending)

    def test_terminal_shows_exact_update_and_retries_displayed_agent_run(self) -> None:
        active = _terminal_package("candidate-active", "a")
        candidate = _terminal_package("candidate-update", "c")
        candidate["registration_version"] = 2
        detail = _terminal_detail("project-1", "activity-2", candidate)
        detail["data"]["comparison"] = {
            "active_package_ref": active,
            "candidate_package_ref": candidate,
            "differences": [
                {
                    "kind": "changed",
                    "item_id": "scope-one",
                    "subject": "Registration scope",
                    "area": "scope",
                    "previous_version": 1,
                    "candidate_version": 2,
                    "reason_refs": ["decision-one"],
                }
            ],
        }
        detail["data"]["agent_retry"] = {
            "assignment_id": "architect-assignment-one",
            "failed_run_id": "architect-run-one",
            "role": "project_architect",
            "reason": "tool exited",
            "automatic_limit": 2,
            "automatic_consumed": 1,
            "manual_consumed": 0,
            "state": "paused",
        }
        client = _TerminalClient(detail)
        state = _TerminalState("project-1", "unrelated-activity")
        context = ExtensionContext(client, state)
        interaction = RegistrationInteraction(request_id_factory=lambda: "retry-one")

        rendered = interaction.open(context)
        self.assertIn("candidate-active -> candidate candidate-update", rendered)
        self.assertIn("changed: Registration scope", rendered)
        self.assertIn("architect-assignment-one / failed run architect-run-one", rendered)
        interaction.retry(context, "agent", "Operator verified the credential.")

        self.assertEqual(
            {
                "assignment_id": "architect-assignment-one",
                "failed_run_id": "architect-run-one",
                "intervention": "Operator verified the credential.",
            },
            client.submissions[0]["payload"],
        )

    def test_terminal_preserves_lost_acknowledgment_when_candidate_changes(self) -> None:
        package1 = _terminal_package("candidate-1", "a")
        package2 = _terminal_package("candidate-2", "c")
        client = _TerminalClient(_terminal_detail("project-1", "activity-1", package1))
        client.connection_failures = 1
        state = _TerminalState("project-1", "activity-1")
        context = ExtensionContext(client, state)
        interaction = RegistrationInteraction(
            request_id_factory=lambda: "request-1",
            confirmation_id_factory=lambda: "confirmation-1",
            time_factory=lambda: "2026-09-20T10:00:00Z",
        )
        registry = ExtensionRegistry()
        RegistrationExtension(interaction).install(registry)
        registry.invoke_command("registration", context)
        with self.assertRaises(TerminalConnectionError):
            registry.invoke_action("registration-confirm", context, "candidate-1")

        client.detail = _terminal_detail("project-1", "activity-1", package2)
        rendered = registry.invoke_command("registration", context)
        self.assertIn("request-1", rendered)
        with self.assertRaisesRegex(ValueError, "remains unresolved"):
            registry.invoke_action("registration-confirm", context, "candidate-2")
        self.assertEqual(package1, interaction.pending.package_ref)
        self.assertEqual(1, len(client.submissions))

    def test_changed_immutable_destination_profile_cannot_write_or_activate(self) -> None:
        assessment, package = self.publish("activity-1", 1, "candidate-1", self.seed)
        remote_before = self.output("git", "--git-dir", str(self.remote), "rev-parse", "main")
        original_provider = self.service.destination_provider
        changed_profile = replace(self.profile, app_slug="different-maestro-app")
        self.service.destination_provider = GitHubDestinationProvider(
            changed_profile, _DestinationApi()
        )
        action = OwnerConfirmation(
            "changed-profile-confirmation", "changed-profile-request",
            "project-1", "activity-1", 1, package, "2026-09-20T10:00:00Z",
        )

        with self.assertRaisesRegex(RegistrationConfirmationError, "profile changed"):
            self.service.confirm(assessment, VerifiedActor("owner-local"), action)

        self.assertIsNone(self.service.active("project-1"))
        self.assertEqual(
            remote_before,
            self.output("git", "--git-dir", str(self.remote), "rev-parse", "main"),
        )
        self.service.destination_provider = original_provider
        self.assertEqual(
            "Registered",
            self.service.confirm(assessment, VerifiedActor("owner-local"), action).status,
        )


def _response(role: str, activity_id: str, artifact: dict[str, str]) -> RegistrationAgentResponse:
    return RegistrationAgentResponse.from_mapping({
        "contract_version": 1,
        "assignment_id": "architect-assignment" if role == "project_architect" else "reviewer-assignment",
        "run_id": "architect-run" if role == "project_architect" else "reviewer-run",
        "project_id": "project-1",
        "activity_id": activity_id,
        "role": role,
        "source_commit": "b" * 40,
        "decision_version": "decision-1",
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
    """Controlled authorization input; package and index publication use real Git."""

    def __init__(self) -> None:
        self.policy = BranchPolicyObservation(False, ())
        self.authorization_count = 0

    def app_identity(self, profile):
        self.authorization_count += 1
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
        return self.policy


@dataclass
class _TerminalState:
    selected_project_id: str | None
    selected_activity_id: str | None

    def select_activity(self, activity_id: str) -> None:
        self.selected_activity_id = activity_id


class _TerminalClient:
    def __init__(self, detail):
        self.detail = detail
        self.submissions: list[dict[str, object]] = []
        self.requested_paths: list[str] = []
        self.connection_failures = 0
        self.request_response = None

    def get_json(self, path: str, *, timeout: int = 15):
        self.requested_paths.append(path)
        if path.startswith("/requests/") and self.request_response is not None:
            return self.request_response
        return self.detail

    def submit(self, envelope):
        self.submissions.append(dict(envelope))
        if self.connection_failures:
            self.connection_failures -= 1
            raise TerminalConnectionError("acknowledgment was lost")
        return {"receipt": {"request_id": envelope["request_id"], "status": "completed"}}


def _terminal_package(candidate_id: str, commit_character: str) -> dict[str, object]:
    return {
        "repository": "owner/project",
        "commit": commit_character * 40,
        "registration_version": 1,
        "candidate_id": candidate_id,
        "manifest_path": (
            f".maestro/registrations/versions/1/candidates/{candidate_id}/manifest.json"
        ),
        "manifest_sha256": "b" * 64,
    }


def _terminal_detail(
    project_id: str, activity_id: str, package: dict[str, object]
) -> dict[str, object]:
    return {
        "data": {
            "project_id": project_id,
            "activity_id": activity_id,
            "activity_version": 3,
            "state": "Ready to confirm",
            "package_ref": package,
            "comparison": None,
            "agent_retry": None,
            "history": [],
            "can_confirm": True,
        }
    }


if __name__ == "__main__":
    unittest.main()
