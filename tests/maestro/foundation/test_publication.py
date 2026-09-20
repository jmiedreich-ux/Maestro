from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from maestro.foundation.credentials import (
    RepositoryAuthorizer,
    RepositoryBinding,
    RepositoryCredentialError,
    RepositoryProfile,
    ServiceGitRoute,
    ServiceGitTransport,
)
from maestro.foundation.database import Database
from maestro.foundation.github_destination import (
    BranchPolicyObservation,
    GitHubAppCredential,
    GitHubAppDestinationProfile,
    GitHubDestinationProvider,
    GitHubInstallationToken,
)
from maestro.foundation.git_publication import (
    PublicationAccessError,
    PublicationConflictError,
    PublicationJournal,
    PublicationStateError,
    publication_migrations,
)
from maestro.foundation.settings import StorageSettings


class PublicationJournalTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.remote = self.root / "remote.git"
        self.work = self.root / "work"
        self.git_run("git", "init", "--bare", "--initial-branch=main", str(self.remote))
        self.git_run("git", "clone", "--quiet", str(self.remote), str(self.work))
        self.git_run("git", "-C", str(self.work), "config", "user.name", "Fixture")
        self.git_run("git", "-C", str(self.work), "config", "user.email", "fixture@example.invalid")
        (self.work / "README.md").write_text("seed\n", encoding="utf-8")
        self.git_run("git", "-C", str(self.work), "add", "README.md")
        self.git_run("git", "-C", str(self.work), "commit", "--quiet", "-m", "seed")
        self.git_run("git", "-C", str(self.work), "push", "--quiet", "origin", "main")
        self.seed = self.output("git", "-C", str(self.work), "rev-parse", "HEAD")
        self.database = Database(
            StorageSettings(path=self.root / "maestro.sqlite3"), publication_migrations()
        )
        repository_profile = RepositoryProfile(
            name="project-github",
            credential_reference="github-app-project",
            allowed_repositories=("owner/project",),
            allowed_branch_patterns=("main",),
        )
        self.credentials = {"github-app-project": "fixture-credential"}
        self.transport = ServiceGitTransport(
            (ServiceGitRoute("owner/project", "github-app-project", str(self.remote)),),
            lambda reference: self.credentials[reference],
        )
        profile = GitHubAppDestinationProfile(
            profile_name="project-github",
            binding_id="binding-project",
            credential=GitHubAppCredential("github-app-project"),
            app_id=101,
            installation_id=202,
            app_slug="maestro-coordinator",
            allowed_repositories=("owner/project",),
            allowed_branches=("main",),
        )
        self.destination_api = _FixtureDestinationApi()
        self.destination = GitHubDestinationProvider(profile, self.destination_api)
        self.authorizer = RepositoryAuthorizer(
            {repository_profile.name: repository_profile},
            (RepositoryBinding("binding-project", "owner/project", repository_profile.name),),
        )
        self.journal = PublicationJournal(
            self.database,
            self.authorizer,
            self.transport,
            self.destination,
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def git_run(self, *command: str) -> None:
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        if result.returncode:
            self.fail(result.stderr.decode("utf-8", "replace"))

    def output(self, *command: str) -> str:
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        if result.returncode:
            self.fail(result.stderr.decode("utf-8", "replace"))
        return result.stdout.decode("ascii").strip()

    def prepare(self, operation_id: str = "publish-one") -> None:
        self.journal.prepare(
            operation_id=operation_id,
            repository="OWNER/PROJECT",
            remote=str(self.remote),
            branch="main",
            expected_parent=self.seed,
            files={".maestro/registrations/candidate.json": b'{"candidate":"one"}\n'},
            destination_authorization=self.authorize(),
        )

    def authorize(self):
        return self.destination.authorize("owner/project", "main")

    def prepare_confirmation(
        self,
        *,
        number: int,
        parent: str,
        index: bytes,
        expected_index: bytes | None,
    ) -> str:
        operation_id = f"confirmation-{number}"
        receipt_path = f".maestro/registrations/confirmations/{operation_id}.json"
        index_path = ".maestro/registrations/index.json"
        self.journal.prepare(
            operation_id=operation_id,
            operation_type="registration_confirmation",
            request_id=f"request-{number}",
            repository="owner/project",
            remote=str(self.remote),
            branch="main",
            expected_parent=parent,
            files={
                receipt_path: json.dumps(
                    {"confirmation_id": operation_id}, separators=(",", ":")
                ).encode("utf-8"),
                index_path: index,
            },
            expected_files={receipt_path: None, index_path: expected_index},
            destination_authorization=self.authorize(),
        )
        return operation_id

    def test_prepares_then_publishes_exact_bytes_to_real_remote_without_force(self) -> None:
        self.prepare()
        result = self.journal.attempt("publish-one", self.authorize())

        self.assertEqual("verified", result.state)
        self.assertFalse(result.reused_remote_bytes)
        self.assertEqual(result.remote_commit, self.output("git", "--git-dir", str(self.remote), "rev-parse", "main"))
        self.assertEqual(
            b'{"candidate":"one"}\n',
            subprocess.check_output(
                ["git", "--git-dir", str(self.remote), "show", "main:.maestro/registrations/candidate.json"]
            ),
        )
        operation = self.journal.operation("publish-one")
        self.assertEqual(self.seed, operation.expected_parent)
        self.assertEqual("binding-project", operation.authorization.binding_id)
        self.assertEqual("github-app-project", operation.authorization.credential_reference)
        self.assertEqual("verified", operation.state)

    def test_creates_then_compare_and_replaces_receipt_and_index_in_one_commit(self) -> None:
        first_index = b'{"confirmation_refs":["confirmation-1"]}\n'
        first_id = self.prepare_confirmation(
            number=1, parent=self.seed, index=first_index, expected_index=None
        )
        first = self.journal.attempt(first_id, self.authorize())

        second_index = b'{"confirmation_refs":["confirmation-1","confirmation-2"]}\n'
        second_id = self.prepare_confirmation(
            number=2,
            parent=first.remote_commit,
            index=second_index,
            expected_index=first_index,
        )
        second = self.journal.attempt(second_id, self.authorize())

        self.assertEqual("verified", second.state)
        self.assertEqual(
            second_index,
            subprocess.check_output(
                [
                    "git", "--git-dir", str(self.remote), "show",
                    "main:.maestro/registrations/index.json",
                ]
            ),
        )
        operation = self.journal.operation(second_id)
        self.assertEqual("registration_confirmation", operation.operation_type)
        self.assertEqual("request-2", operation.request_id)
        self.assertEqual(first_index, operation.expected_files[".maestro/registrations/index.json"])
        self.assertIsNone(
            operation.expected_files[
                ".maestro/registrations/confirmations/confirmation-2.json"
            ]
        )

    def test_compare_and_replace_reconciles_unrelated_head_before_retry(self) -> None:
        first_index = b'{"confirmation_refs":["confirmation-1"]}\n'
        first_id = self.prepare_confirmation(
            number=1, parent=self.seed, index=first_index, expected_index=None
        )
        first = self.journal.attempt(first_id, self.authorize())
        second_id = self.prepare_confirmation(
            number=2,
            parent=first.remote_commit,
            index=b'{"confirmation_refs":["confirmation-1","confirmation-2"]}\n',
            expected_index=first_index,
        )

        self.git_run("git", "-C", str(self.work), "pull", "--quiet", "--ff-only")
        (self.work / "unrelated.txt").write_text("preserve me\n", encoding="utf-8")
        self.git_run("git", "-C", str(self.work), "add", "unrelated.txt")
        self.git_run("git", "-C", str(self.work), "commit", "--quiet", "-m", "unrelated move")
        self.git_run("git", "-C", str(self.work), "push", "--quiet", "origin", "main")

        with self.assertRaises(PublicationStateError):
            self.journal.attempt(second_id, self.authorize())
        moved_head = self.output("git", "--git-dir", str(self.remote), "rev-parse", "main")
        self.assertEqual(moved_head, self.journal.operation(second_id).reconciled_parent)

        result = self.journal.attempt(second_id, self.authorize())
        self.assertEqual("verified", result.state)
        self.assertEqual(
            b"preserve me\n",
            subprocess.check_output(
                ["git", "--git-dir", str(self.remote), "show", "main:unrelated.txt"]
            ),
        )

    def test_compare_and_replace_rejects_a_conflicting_index(self) -> None:
        first_index = b'{"confirmation_refs":["confirmation-1"]}\n'
        first_id = self.prepare_confirmation(
            number=1, parent=self.seed, index=first_index, expected_index=None
        )
        first = self.journal.attempt(first_id, self.authorize())
        second_id = self.prepare_confirmation(
            number=2,
            parent=first.remote_commit,
            index=b'{"confirmation_refs":["confirmation-1","confirmation-2"]}\n',
            expected_index=first_index,
        )

        self.git_run("git", "-C", str(self.work), "pull", "--quiet", "--ff-only")
        index_path = self.work / ".maestro/registrations/index.json"
        conflicting = b'{"confirmation_refs":["competing-confirmation"]}\n'
        index_path.write_bytes(conflicting)
        self.git_run("git", "-C", str(self.work), "add", ".maestro/registrations/index.json")
        self.git_run("git", "-C", str(self.work), "commit", "--quiet", "-m", "competing index")
        self.git_run("git", "-C", str(self.work), "push", "--quiet", "origin", "main")

        with self.assertRaises(PublicationConflictError):
            self.journal.attempt(second_id, self.authorize())

        self.assertEqual("paused", self.journal.operation(second_id).state)
        self.assertEqual(
            conflicting,
            subprocess.check_output(
                [
                    "git", "--git-dir", str(self.remote), "show",
                    "main:.maestro/registrations/index.json",
                ]
            ),
        )

    def test_compare_and_replace_lost_acknowledgment_reuses_exact_remote_commit(self) -> None:
        first_index = b'{"confirmation_refs":["confirmation-1"]}\n'
        first_id = self.prepare_confirmation(
            number=1, parent=self.seed, index=first_index, expected_index=None
        )
        first = self.journal.attempt(first_id, self.authorize())
        second_id = self.prepare_confirmation(
            number=2,
            parent=first.remote_commit,
            index=b'{"confirmation_refs":["confirmation-1","confirmation-2"]}\n',
            expected_index=first_index,
        )
        written = self.journal.attempt(second_id, self.authorize())
        self.journal._set_state(second_id, "writing", failure=None)

        recovered = self.journal.reconcile(second_id, self.authorize())

        self.assertTrue(recovered.reused_remote_bytes)
        self.assertEqual(written.remote_commit, recovered.remote_commit)
        self.assertEqual("verified", self.journal.operation(second_id).state)

    def test_applied_transition_is_transactional_and_replayable(self) -> None:
        operation_id = "activation-publication"
        self.journal.prepare(
            operation_id=operation_id,
            operation_type="registration_confirmation",
            request_id="confirmation-request",
            repository="owner/project",
            remote=str(self.remote),
            branch="main",
            expected_parent=self.seed,
            files={".maestro/registrations/index.json": b'{"current":"one"}\n'},
            expected_files={".maestro/registrations/index.json": None},
            destination_authorization=self.authorize(),
        )
        verified = self.journal.attempt(operation_id, self.authorize())

        with self.database.transaction() as transaction:
            first = self.journal.mark_applied(
                transaction,
                operation_id=operation_id,
                request_id="confirmation-request",
            )
        with self.database.transaction() as transaction:
            replay = self.journal.mark_applied(
                transaction,
                operation_id=operation_id,
                request_id="confirmation-request",
            )

        self.assertEqual(verified.remote_commit, first.remote_commit)
        self.assertEqual(first, replay)
        self.assertEqual("applied", self.journal.operation(operation_id).state)
        self.assertEqual(
            "applied", self.journal.attempt(operation_id, self.authorize()).state
        )

    def test_migration_backfills_existing_operations_as_absent_target_writes(self) -> None:
        settings = StorageSettings(path=self.root / "legacy.sqlite3")
        legacy_database = Database(settings, publication_migrations()[:2])
        legacy_database.initialize()
        content = b"legacy candidate\n"
        with legacy_database.transaction() as transaction:
            transaction.execute(
                """INSERT INTO publication_operations(
                       operation_id, binding_id, repository, profile_name,
                       credential_reference, remote, branch, expected_parent,
                       state, reconciled_parent, remote_commit, failure,
                       authorization_snapshot
                   ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'prepared', NULL, NULL, NULL, ?)""",
                (
                    "legacy-operation",
                    "binding-project",
                    "owner/project",
                    "project-github",
                    "github-app-project",
                    str(self.remote),
                    "main",
                    self.seed,
                    json.dumps(self.authorize().durable_record(), sort_keys=True),
                ),
            )
            transaction.execute(
                """INSERT INTO publication_files(operation_id, path, content, sha256)
                   VALUES (?, ?, ?, ?)""",
                (
                    "legacy-operation",
                    ".maestro/registrations/legacy.json",
                    content,
                    hashlib.sha256(content).hexdigest(),
                ),
            )

        upgraded_database = Database(settings, publication_migrations())
        upgraded_journal = PublicationJournal(
            upgraded_database,
            self.authorizer,
            self.transport,
            self.destination,
        )
        operation = upgraded_journal.operation("legacy-operation")

        self.assertEqual("legacy_publication", operation.operation_type)
        self.assertEqual("legacy-operation", operation.request_id)
        self.assertEqual(
            {".maestro/registrations/legacy.json": None},
            operation.expected_files,
        )

    def test_moved_head_with_conflicting_bytes_pauses_and_never_overwrites(self) -> None:
        self.prepare()
        path = self.work / ".maestro/registrations/candidate.json"
        path.parent.mkdir(parents=True)
        path.write_bytes(b'{"candidate":"other"}\n')
        self.git_run("git", "-C", str(self.work), "add", ".maestro/registrations/candidate.json")
        self.git_run("git", "-C", str(self.work), "commit", "--quiet", "-m", "other publisher")
        self.git_run("git", "-C", str(self.work), "push", "--quiet", "origin", "main")

        with self.assertRaises(PublicationConflictError):
            self.journal.attempt("publish-one", self.authorize())

        self.assertEqual("paused", self.journal.operation("publish-one").state)
        self.assertEqual(
            b'{"candidate":"other"}\n',
            subprocess.check_output(
                ["git", "--git-dir", str(self.remote), "show", "main:.maestro/registrations/candidate.json"]
            ),
        )

    def test_moved_head_is_reconciled_before_a_preserving_retry(self) -> None:
        self.prepare()
        (self.work / "unrelated.txt").write_text("preserve me\n", encoding="utf-8")
        self.git_run("git", "-C", str(self.work), "add", "unrelated.txt")
        self.git_run("git", "-C", str(self.work), "commit", "--quiet", "-m", "unrelated move")
        self.git_run("git", "-C", str(self.work), "push", "--quiet", "origin", "main")

        with self.assertRaises(PublicationStateError):
            self.journal.attempt("publish-one", self.authorize())
        reconciled = self.journal.operation("publish-one")
        self.assertEqual("reconciled", reconciled.state)
        self.assertEqual(
            self.output("git", "--git-dir", str(self.remote), "rev-parse", "main"),
            reconciled.reconciled_parent,
        )

        result = self.journal.attempt("publish-one", self.authorize())
        self.assertEqual("verified", result.state)
        self.assertEqual(
            b"preserve me\n",
            subprocess.check_output(["git", "--git-dir", str(self.remote), "show", "main:unrelated.txt"]),
        )

    def test_lost_acknowledgment_reconciles_matching_remote_bytes_without_another_write(self) -> None:
        self.prepare()
        first = self.journal.attempt("publish-one", self.authorize())
        # A process that lost its final state update has only ``writing`` saved.
        self.journal._set_state("publish-one", "writing", failure=None)

        recovered = self.journal.reconcile("publish-one", self.authorize())

        self.assertTrue(recovered.reused_remote_bytes)
        self.assertEqual(first.remote_commit, recovered.remote_commit)
        self.assertEqual("verified", self.journal.operation("publish-one").state)
        self.assertEqual(2, int(self.output("git", "--git-dir", str(self.remote), "rev-list", "--count", "main")))

    def test_restored_access_reconciles_before_retry_and_never_reports_local_success(self) -> None:
        self.prepare("publish-denied")
        unavailable = self.root / "remote-unavailable.git"
        self.remote.rename(unavailable)
        with self.assertRaises(PublicationAccessError):
            self.journal.attempt("publish-denied", self.authorize())
        operation = self.journal.operation("publish-denied")
        self.assertEqual("paused", operation.state)
        self.assertIsNone(operation.remote_commit)
        unavailable.rename(self.remote)

        with self.assertRaises(PublicationStateError):
            self.journal.reconcile("publish-denied", self.authorize())
        self.assertEqual("reconciled", self.journal.operation("publish-denied").state)
        result = self.journal.attempt("publish-denied", self.authorize())
        self.assertEqual(result.remote_commit, self.output("git", "--git-dir", str(self.remote), "rev-parse", "main"))

    def test_mismatched_route_or_expired_destination_result_cannot_create_a_receipt(self) -> None:
        with self.assertRaises(PublicationAccessError):
            self.journal.prepare(
                operation_id="wrong-remote",
                repository="owner/project",
                remote=str(self.root / "unbound.git"),
                branch="main",
                expected_parent=self.seed,
                files={".maestro/registrations/candidate.json": b"candidate\n"},
                destination_authorization=self.authorize(),
            )
        self.prepare("credential-unavailable")
        self.credentials.clear()
        expired = self.destination.authorize("owner/project", "main", now=4_102_444_801)
        with self.assertRaises(PublicationAccessError):
            self.journal.attempt("credential-unavailable", expired)
        operation = self.journal.operation("credential-unavailable")
        self.assertEqual("paused", operation.state)
        self.assertIsNone(operation.remote_commit)

    def test_changed_profile_snapshot_pauses_attempt_and_reconciliation_without_writing(self) -> None:
        self.prepare("profile-changed")
        updated_profile = GitHubAppDestinationProfile(
            profile_name="project-github",
            binding_id="binding-project",
            credential=GitHubAppCredential("github-app-project"),
            app_id=303,
            installation_id=404,
            app_slug="maestro-coordinator-next",
            allowed_repositories=("owner/project",),
            allowed_branches=("main",),
        )
        updated_provider = GitHubDestinationProvider(updated_profile, _FixtureDestinationApi())
        self.journal._destination_provider = updated_provider
        current = updated_provider.authorize("owner/project", "main")

        with self.assertRaises(PublicationAccessError):
            self.journal.reconcile("profile-changed", current)
        with self.assertRaises(PublicationAccessError):
            self.journal.attempt("profile-changed", current)

        operation = self.journal.operation("profile-changed")
        self.assertEqual("paused", operation.state)
        self.assertIsNone(operation.remote_commit)
        self.assertEqual(self.seed, self.output("git", "--git-dir", str(self.remote), "rev-parse", "main"))

    def test_live_recheck_blocks_a_branch_that_becomes_protected_before_push(self) -> None:
        self.prepare("protected-before-push")
        original_checked = self.journal._checked
        state = {"local_commit_created": False}

        def change_policy_after_local_commit(command, *arguments):
            result = original_checked(command, *arguments)
            if "commit" in arguments:
                state["local_commit_created"] = True
                self.destination_api.policy = BranchPolicyObservation(True, ())
            return result

        self.journal._checked = change_policy_after_local_commit

        with self.assertRaises(PublicationAccessError):
            self.journal.attempt("protected-before-push", self.authorize())

        self.assertTrue(state["local_commit_created"])
        operation = self.journal.operation("protected-before-push")
        self.assertEqual("paused", operation.state)
        self.assertIsNone(operation.remote_commit)
        self.assertEqual(self.seed, self.output("git", "--git-dir", str(self.remote), "rev-parse", "main"))

    def test_profile_requires_one_allowlisted_repository_and_branch(self) -> None:
        profile = RepositoryProfile("profile", "credential", ("owner/project",), ("main",))
        authorizer = RepositoryAuthorizer(
            {"profile": profile}, (RepositoryBinding("binding", "owner/project", "profile"),)
        )
        with self.assertRaises(RepositoryCredentialError):
            authorizer.authorize("owner/other", "main")
        with self.assertRaises(RepositoryCredentialError):
            authorizer.authorize("owner/project", "feature")


class _FixtureDestinationApi:
    """Controlled provider component input; publication itself uses real Git."""

    def __init__(self) -> None:
        self.policy_sequence: list[BranchPolicyObservation] = []
        self.policy = BranchPolicyObservation(False, ())

    def app_identity(self, profile):
        return {"id": profile.app_id, "slug": profile.app_slug}

    def installation_identity(self, profile):
        return {"id": profile.installation_id, "app_id": profile.app_id}

    def installation_token(self, profile):
        return GitHubInstallationToken("fixture-installation-token", {"contents": "write", "administration": "read"}, 4_102_444_800, profile.api_base_url)

    def repository_identity(self, token, repository):
        return {"id": 1, "full_name": repository}

    def branch_identity(self, token, repository, branch):
        return {"name": branch}

    def branch_policy(self, token, repository, branch):
        if self.policy_sequence:
            return self.policy_sequence.pop(0)
        return self.policy


if __name__ == "__main__":
    unittest.main()
