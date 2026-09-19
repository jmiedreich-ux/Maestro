from __future__ import annotations

import json
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

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
from maestro.foundation.git_read import RemoteGitReader
from maestro.planning import ExactSourceReader, IntakeError, RegistrationIntake, RegistrationIntakeRequest, SourceIntakeError


class _Questions:
    def __init__(self) -> None:
        self.questions = []

    def publish_intake_question(self, question) -> None:
        self.questions.append(question)


class _DestinationApi:
    def __init__(self) -> None:
        self.protected = False
        self.rulesets: tuple[dict[str, object], ...] = ()
        self.permissions = {"contents": "write", "administration": "read"}
        self.calls: list[str] = []

    def app_identity(self, _profile):
        self.calls.append("app")
        return {"id": 42, "slug": "maestro"}

    def installation_identity(self, _profile):
        self.calls.append("installation")
        return {"id": 99, "app_id": 42}

    def installation_token(self, _profile):
        self.calls.append("token")
        return GitHubInstallationToken("installation-token", self.permissions, time.time() + 300)

    def repository_identity(self, _token, repository):
        self.calls.append("repository")
        return {"full_name": repository}

    def branch_identity(self, _token, _repository, branch):
        self.calls.append("branch")
        return {"name": branch}

    def branch_policy(self, _token, _repository, _branch):
        self.calls.append("policy")
        return BranchPolicyObservation(self.protected, self.rulesets)


class _MovingBranchReader(RemoteGitReader):
    def __init__(self, move) -> None:
        super().__init__()
        self._move = move

    def snapshot(self, remote, branch, paths, **kwargs):
        self._move()
        return super().snapshot(remote, branch, paths, **kwargs)


class ExactSourceIntakeTest(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.remote = self.root / "project.git"
        self.work = self.root / "project"
        self._git("git", "init", "--bare", "--initial-branch=main", str(self.remote))
        self._git("git", "clone", "--quiet", str(self.remote), str(self.work))
        self._git("git", "-C", str(self.work), "config", "user.name", "Fixture")
        self._git("git", "-C", str(self.work), "config", "user.email", "fixture@example.invalid")
        docs = self.work / "docs"
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
            "| Declaration version | 2 |\n"
            "| Architecture source | docs/architecture.md |\n\n"
            "## Milestones and order\n\n"
            "| Position | Qualified milestone reference and plain subject | Milestone version | Milestone section |\n"
            "| --- | --- | --- | --- |\n"
            "| 1 | APP-PM1 — Start application | 3 | docs/milestones.md#start |\n",
            encoding="utf-8",
        )
        self._commit("initial project documents")
        self.initial_commit = self._output("git", "-C", str(self.work), "rev-parse", "HEAD")
        self.authorizer = RepositoryAuthorizer(
            {"project-profile": RepositoryProfile("project-profile", "github-app", ("owner/project",), ("main",))},
            (RepositoryBinding("project-binding", "owner/project", "project-profile"),),
        )
        self.transport = ServiceGitTransport(
            (ServiceGitRoute("owner/project", "github-app", str(self.remote)),), lambda _reference: "unused",
        )
        self.api = _DestinationApi()
        profile = GitHubAppDestinationProfile(
            "project-profile", "project-binding", GitHubAppCredential("github-app"), 42, 99,
            "maestro", ("owner/project",), ("main",),
        )
        self.provider = GitHubDestinationProvider(profile, self.api)

    def _git(self, *command: str) -> None:
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        if result.returncode:
            self.fail(result.stderr.decode("utf-8", "replace"))

    def _output(self, *command: str) -> str:
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        if result.returncode:
            self.fail(result.stderr.decode("utf-8", "replace"))
        return result.stdout.decode("ascii").strip()

    def _commit(self, message: str) -> None:
        self._git("git", "-C", str(self.work), "add", ".")
        self._git("git", "-C", str(self.work), "commit", "--quiet", "-m", message)
        self._git("git", "-C", str(self.work), "push", "--quiet", "origin", "main")

    def _intake(self, reader: ExactSourceReader | None = None) -> RegistrationIntake:
        return RegistrationIntake(reader or ExactSourceReader(), self.authorizer, self.transport, self.provider)

    def _request(self, **changes) -> RegistrationIntakeRequest:
        values = {
            "repository": "OWNER/PROJECT", "remote": str(self.remote), "overview_path": "docs/overview.md",
            "referenced_paths": ("docs/architecture.md", "docs/milestones.md"), "source_ref": "refs/heads/main",
            "publication_branch": "main", "scope": "All supplied milestones",
            "architect_selection": "codex/gpt-5.6-sol", "reviewer_selection": "claude/opus",
        }
        values.update(changes)
        return RegistrationIntakeRequest(**values)

    def test_reads_authorized_exact_source_and_retains_provider_snapshot_evidence(self) -> None:
        result = self._intake().begin(self._request(), questions=_Questions())

        self.assertEqual(self.initial_commit, result.inventory.source_commit)
        self.assertEqual(("docs/overview.md", "docs/architecture.md", "docs/milestones.md"), tuple(blob.path for blob in result.inventory.blobs))
        self.assertEqual((("APP-PM1", "Start application", 3),), tuple((item.milestone, item.subject, item.version) for item in result.inventory.outcomes))
        self.assertEqual("supplied", result.source_selection)
        self.assertEqual("project-binding", result.repository_binding_id)
        self.assertEqual(64, len(result.destination_snapshot_reference))
        self.assertEqual("allowed", result.destination_evidence["decision"])
        self.assertEqual("project-profile", result.destination_evidence["snapshot"]["profile_name"])
        self.assertNotIn("installation-token", json.dumps(result.destination_evidence))
        self.assertEqual(["app", "installation", "token", "repository", "branch", "policy"], self.api.calls)

    def test_missing_questions_prevent_provider_and_source_read(self) -> None:
        questions = _Questions()
        result = self._intake().begin(self._request(scope=None, publication_branch=None), questions=questions)

        self.assertIsNone(result.inventory)
        self.assertEqual(("scope", "publication_branch"), tuple(question.field for question in questions.questions))
        self.assertEqual([], self.api.calls)

    def test_blocked_or_unverifiable_destination_fails_before_source_read(self) -> None:
        self.api.protected = True
        with self.assertRaisesRegex(IntakeError, "not allowed"):
            self._intake().begin(self._request(), questions=_Questions())

    def test_missing_destination_permission_or_allowlist_fails_closed(self) -> None:
        self.api.permissions = {"contents": "read", "administration": "read"}
        with self.assertRaisesRegex(IntakeError, "not allowed"):
            self._intake().begin(self._request(), questions=_Questions())
        with self.assertRaisesRegex(IntakeError, "does not authorize"):
            self._intake().begin(self._request(publication_branch="release"), questions=_Questions())

    def test_moving_branch_cannot_retarget_saved_source(self) -> None:
        def move() -> None:
            (self.work / "docs" / "overview.md").write_text("# Changed\n", encoding="utf-8")
            self._commit("move source")

        reader = ExactSourceReader(_MovingBranchReader(move))
        with self.assertRaisesRegex(SourceIntakeError, "moved"):
            reader.read(remote=str(self.remote), source_ref="refs/heads/main", overview_path="docs/overview.md")

    def test_contradictory_or_missing_paths_fail_closed(self) -> None:
        with self.assertRaisesRegex(SourceIntakeError, "does not contain"):
            ExactSourceReader().read(remote=str(self.remote), source_ref="refs/heads/main", overview_path="docs/missing.md")
        with self.assertRaisesRegex(IntakeError, "contradict"):
            self._intake().begin(self._request(referenced_paths=("docs/milestones.md", "docs/architecture.md")), questions=_Questions())


if __name__ == "__main__":
    unittest.main()
