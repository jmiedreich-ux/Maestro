from __future__ import annotations

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
        database = Database(
            StorageSettings(path=self.root / "maestro.sqlite3"), publication_migrations()
        )
        profile = RepositoryProfile(
            name="project-github",
            credential_reference="github-app-project",
            allowed_repositories=("owner/project",),
            allowed_branch_patterns=("main",),
        )
        self.credentials = {"github-app-project": "fixture-credential"}
        transport = ServiceGitTransport(
            (ServiceGitRoute("owner/project", "github-app-project", str(self.remote)),),
            lambda reference: self.credentials[reference],
        )
        self.journal = PublicationJournal(
            database,
            RepositoryAuthorizer(
                {profile.name: profile},
                (RepositoryBinding("binding-project", "owner/project", profile.name),),
            ),
            transport,
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
        )

    def test_prepares_then_publishes_exact_bytes_to_real_remote_without_force(self) -> None:
        self.prepare()
        result = self.journal.attempt("publish-one")

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

    def test_moved_head_with_conflicting_bytes_pauses_and_never_overwrites(self) -> None:
        self.prepare()
        path = self.work / ".maestro/registrations/candidate.json"
        path.parent.mkdir(parents=True)
        path.write_bytes(b'{"candidate":"other"}\n')
        self.git_run("git", "-C", str(self.work), "add", ".maestro/registrations/candidate.json")
        self.git_run("git", "-C", str(self.work), "commit", "--quiet", "-m", "other publisher")
        self.git_run("git", "-C", str(self.work), "push", "--quiet", "origin", "main")

        with self.assertRaises(PublicationConflictError):
            self.journal.attempt("publish-one")

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
            self.journal.attempt("publish-one")
        reconciled = self.journal.operation("publish-one")
        self.assertEqual("reconciled", reconciled.state)
        self.assertEqual(
            self.output("git", "--git-dir", str(self.remote), "rev-parse", "main"),
            reconciled.reconciled_parent,
        )

        result = self.journal.attempt("publish-one")
        self.assertEqual("verified", result.state)
        self.assertEqual(
            b"preserve me\n",
            subprocess.check_output(["git", "--git-dir", str(self.remote), "show", "main:unrelated.txt"]),
        )

    def test_lost_acknowledgment_reconciles_matching_remote_bytes_without_another_write(self) -> None:
        self.prepare()
        first = self.journal.attempt("publish-one")
        # A process that lost its final state update has only ``writing`` saved.
        self.journal._set_state("publish-one", "writing", failure=None)

        recovered = self.journal.reconcile("publish-one")

        self.assertTrue(recovered.reused_remote_bytes)
        self.assertEqual(first.remote_commit, recovered.remote_commit)
        self.assertEqual("verified", self.journal.operation("publish-one").state)
        self.assertEqual(2, int(self.output("git", "--git-dir", str(self.remote), "rev-list", "--count", "main")))

    def test_restored_access_reconciles_before_retry_and_never_reports_local_success(self) -> None:
        self.prepare("publish-denied")
        unavailable = self.root / "remote-unavailable.git"
        self.remote.rename(unavailable)
        with self.assertRaises(PublicationAccessError):
            self.journal.attempt("publish-denied")
        operation = self.journal.operation("publish-denied")
        self.assertEqual("paused", operation.state)
        self.assertIsNone(operation.remote_commit)
        unavailable.rename(self.remote)

        with self.assertRaises(PublicationStateError):
            self.journal.reconcile("publish-denied")
        self.assertEqual("reconciled", self.journal.operation("publish-denied").state)
        result = self.journal.attempt("publish-denied")
        self.assertEqual(result.remote_commit, self.output("git", "--git-dir", str(self.remote), "rev-parse", "main"))

    def test_mismatched_or_unavailable_privileged_route_cannot_create_a_receipt(self) -> None:
        with self.assertRaises(PublicationAccessError):
            self.journal.prepare(
                operation_id="wrong-remote",
                repository="owner/project",
                remote=str(self.root / "unbound.git"),
                branch="main",
                expected_parent=self.seed,
                files={".maestro/registrations/candidate.json": b"candidate\n"},
            )
        self.prepare("credential-unavailable")
        self.credentials.clear()
        with self.assertRaises(PublicationAccessError):
            self.journal.attempt("credential-unavailable")
        operation = self.journal.operation("credential-unavailable")
        self.assertEqual("paused", operation.state)
        self.assertIsNone(operation.remote_commit)

    def test_profile_requires_one_allowlisted_repository_and_branch(self) -> None:
        profile = RepositoryProfile("profile", "credential", ("owner/project",), ("main",))
        authorizer = RepositoryAuthorizer(
            {"profile": profile}, (RepositoryBinding("binding", "owner/project", "profile"),)
        )
        with self.assertRaises(RepositoryCredentialError):
            authorizer.authorize("owner/other", "main")
        with self.assertRaises(RepositoryCredentialError):
            authorizer.authorize("owner/project", "feature")


if __name__ == "__main__":
    unittest.main()
