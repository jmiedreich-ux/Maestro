from __future__ import annotations

import json
import subprocess
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from maestro.foundation.credentials import (
    RepositoryAuthorizer,
    RepositoryBinding,
    RepositoryProfile,
    ServiceGitRoute,
    ServiceGitTransport,
)
from maestro.foundation.git_read import RemoteGitReader
from maestro.planning import (
    ExactSourceReader,
    GitHubDirectWriteVerifier,
    IntakeError,
    RegistrationIntake,
    RegistrationIntakeRequest,
    SourceIntakeError,
)


class RecordingQuestions:
    def __init__(self) -> None:
        self.questions = []

    def publish_intake_question(self, question) -> None:
        self.questions.append(question)


class MovingBranchReader(RemoteGitReader):
    """Moves the real fixture branch after selection and before shared reading."""

    def __init__(self, move) -> None:
        super().__init__()
        self._move = move

    def snapshot(self, remote, branch, paths, **kwargs):
        self._move()
        return super().snapshot(remote, branch, paths, **kwargs)


class GitHubEvidenceServer:
    """A real HTTP boundary for bound-credential allow/deny evidence."""

    def __init__(self, token: str) -> None:
        self.token = token
        self.push = True
        self.protected = False
        outer = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.headers.get("Authorization") != f"Bearer {outer.token}":
                    self.send_error(401)
                    return
                if self.path == "/repos/owner/project":
                    outer._respond(self, {"full_name": "owner/project", "permissions": {"push": outer.push}})
                    return
                if self.path == "/repos/owner/project/branches/main":
                    outer._respond(self, {"name": "main", "protected": outer.protected})
                    return
                self.send_error(404)

            def log_message(self, *_):
                return

        self._server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()

    @property
    def api_base(self) -> str:
        host, port = self._server.server_address[:2]
        return f"http://{host}:{port}"

    def close(self) -> None:
        self._server.shutdown()
        self._thread.join()
        self._server.server_close()

    @staticmethod
    def _respond(handler, payload: dict[str, object]) -> None:
        body = json.dumps(payload).encode("utf-8")
        handler.send_response(200)
        handler.send_header("Content-Type", "application/json")
        handler.send_header("Content-Length", str(len(body)))
        handler.end_headers()
        handler.wfile.write(body)


class ExactSourceIntakeTest(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.remote = self.root / "project.git"
        self.work = self.root / "project"
        self.git_run("git", "init", "--bare", "--initial-branch=main", str(self.remote))
        self.git_run("git", "clone", "--quiet", str(self.remote), str(self.work))
        self.git_run("git", "-C", str(self.work), "config", "user.name", "Fixture")
        self.git_run("git", "-C", str(self.work), "config", "user.email", "fixture@example.invalid")
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
        self.commit("initial project documents")
        self.initial_commit = self.output("git", "-C", str(self.work), "rev-parse", "HEAD")
        self.git_run("git", "-C", str(self.work), "tag", "-a", "registration-v1", "-m", "fixture")
        self.git_run("git", "-C", str(self.work), "push", "--quiet", "origin", "registration-v1")
        self.authorizer = RepositoryAuthorizer(
            {
                "project-profile": RepositoryProfile(
                    "project-profile",
                    "project-github-app",
                    ("owner/project",),
                    ("main",),
                )
            },
            (RepositoryBinding("project-binding", "owner/project", "project-profile"),),
        )
        self.transport = ServiceGitTransport(
            (ServiceGitRoute("owner/project", "project-github-app", str(self.remote)),),
            lambda reference: "fixture-token" if reference == "project-github-app" else "",
        )
        self.github = GitHubEvidenceServer("fixture-token")
        self.addCleanup(self.github.close)
        self.verifier = GitHubDirectWriteVerifier(self.github.api_base)

    def intake(self, reader: ExactSourceReader | None = None) -> RegistrationIntake:
        return RegistrationIntake(reader or ExactSourceReader(), self.authorizer, self.transport, self.verifier)

    def git_run(self, *command: str) -> None:
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        if result.returncode:
            self.fail(result.stderr.decode("utf-8", "replace"))

    def output(self, *command: str) -> str:
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        if result.returncode:
            self.fail(result.stderr.decode("utf-8", "replace"))
        return result.stdout.decode("ascii").strip()

    def commit(self, message: str) -> None:
        self.git_run("git", "-C", str(self.work), "add", ".")
        self.git_run("git", "-C", str(self.work), "commit", "--quiet", "-m", message)
        self.git_run("git", "-C", str(self.work), "push", "--quiet", "origin", "main")

    def request(self, **changes) -> RegistrationIntakeRequest:
        values = {
            "repository": "OWNER/PROJECT",
            "remote": str(self.remote),
            "overview_path": "docs/overview.md",
            "referenced_paths": ("docs/architecture.md", "docs/milestones.md"),
            "source_ref": "refs/heads/main",
            "publication_branch": "main",
            "scope": "All supplied milestones",
            "architect_selection": "codex/gpt-5.6-sol",
            "reviewer_selection": "claude/opus",
        }
        values.update(changes)
        return RegistrationIntakeRequest(**values)

    def test_reads_selected_real_branch_once_with_exact_inventory(self) -> None:
        questions = RecordingQuestions()
        result = self.intake().begin(
            self.request(), questions=questions
        )

        self.assertEqual([], questions.questions)
        self.assertEqual("project-binding", result.repository_binding_id)
        self.assertEqual(self.initial_commit, result.inventory.source_commit)
        self.assertEqual("refs/heads/main", result.inventory.source_ref)
        self.assertEqual(
            ("docs/overview.md", "docs/architecture.md", "docs/milestones.md"),
            tuple(blob.path for blob in result.inventory.blobs),
        )
        self.assertTrue(result.inventory.content_for("docs/overview.md").startswith(b"# Project\n"))
        self.assertEqual("All supplied milestones", result.selected_scope)
        self.assertEqual("supplied", result.source_selection)
        self.assertEqual("direct-write-allowed", result.direct_write_evidence.protection_state)
        self.assertEqual(
            (("APP-PM1", "Start application", 3),),
            tuple((item.milestone, item.subject, item.version) for item in result.inventory.outcomes),
        )
        self.assertTrue(all(len(blob.sha256) == 64 for blob in result.inventory.blobs))
        self.assertTrue(all(len(blob.object_id) == 40 for blob in result.inventory.blobs))

    def test_missing_choices_are_published_as_questions_before_source_read(self) -> None:
        questions = RecordingQuestions()
        result = self.intake().begin(
            self.request(source_ref=None, publication_branch=None, scope=None, reviewer_selection=None),
            questions=questions,
        )

        self.assertIsNone(result.inventory)
        self.assertEqual(
            ("scope", "publication_branch", "reviewer_selection"),
            tuple(question.field for question in questions.questions),
        )

    def test_missing_path_and_unauthorized_destination_are_rejected(self) -> None:
        reader = ExactSourceReader()
        with self.assertRaisesRegex(SourceIntakeError, "does not contain"):
            reader.read(
                remote=str(self.remote),
                source_ref="refs/heads/main",
                overview_path="docs/missing.md",
            )
        with self.assertRaisesRegex(IntakeError, "does not authorize"):
            self.intake(reader).begin(
                self.request(publication_branch="unapproved"), questions=RecordingQuestions()
            )

    def test_moved_branch_cannot_retarget_saved_source(self) -> None:
        def move_branch() -> None:
            (self.work / "docs" / "overview.md").write_text("# Changed\n", encoding="utf-8")
            self.commit("move source")

        reader = ExactSourceReader(MovingBranchReader(move_branch))
        with self.assertRaisesRegex(SourceIntakeError, "moved"):
            reader.read(
                remote=str(self.remote),
                source_ref="refs/heads/main",
                overview_path="docs/overview.md",
            )

    def test_exact_commit_remains_pinned_after_branch_moves(self) -> None:
        (self.work / "docs" / "overview.md").write_text("# Later\n", encoding="utf-8")
        self.commit("later source")
        inventory = ExactSourceReader().read(
            remote=str(self.remote),
            source_ref=self.initial_commit,
            overview_path="docs/overview.md",
        )
        self.assertEqual(self.initial_commit, inventory.source_commit)
        self.assertTrue(inventory.content_for("docs/overview.md").startswith(b"# Project\n"))

    def test_annotated_tag_resolves_to_its_exact_commit(self) -> None:
        inventory = ExactSourceReader().read(
            remote=str(self.remote),
            source_ref="refs/tags/registration-v1",
            overview_path="docs/overview.md",
        )
        self.assertEqual(self.initial_commit, inventory.source_commit)

    def test_re_registration_uses_saved_selector_and_default_is_recorded(self) -> None:
        defaulted = self.intake().begin(
            self.request(source_ref=None), questions=RecordingQuestions()
        )
        self.assertEqual("defaulted", defaulted.source_selection)
        self.assertEqual(self.initial_commit, defaulted.inventory.source_commit)
        inherited = self.intake().begin(
            self.request(source_ref=None, prior_source_ref="refs/tags/registration-v1"),
            questions=RecordingQuestions(),
        )
        self.assertEqual("inherited", inherited.source_selection)
        self.assertEqual(self.initial_commit, inherited.inventory.source_commit)

    def test_mismatched_or_missing_authorized_destination_is_rejected_before_source_read(self) -> None:
        with self.assertRaisesRegex(IntakeError, "does not match"):
            self.intake().begin(
                self.request(remote=str(self.root / "other.git")), questions=RecordingQuestions()
            )
        missing_profile = RepositoryProfile(
            "missing-profile", "project-github-app", ("owner/project",), ("main", "missing")
        )
        missing_authorizer = RepositoryAuthorizer(
            {"missing-profile": missing_profile},
            (RepositoryBinding("missing-binding", "owner/project", "missing-profile"),),
        )
        with self.assertRaisesRegex(IntakeError, "destination is unavailable"):
            RegistrationIntake(ExactSourceReader(), missing_authorizer, self.transport, self.verifier).begin(
                self.request(publication_branch="missing"), questions=RecordingQuestions()
            )

    def test_bound_service_credential_denies_nonwritable_or_protected_destination(self) -> None:
        self.github.push = False
        with self.assertRaisesRegex(IntakeError, "cannot directly write"):
            self.intake().begin(self.request(), questions=RecordingQuestions())
        self.github.push = True
        self.github.protected = True
        with self.assertRaisesRegex(IntakeError, "protected"):
            self.intake().begin(self.request(), questions=RecordingQuestions())

    def test_contradictory_authoritative_reference_is_rejected(self) -> None:
        milestones = self.work / "docs" / "milestones.md"
        milestones.write_text(
            milestones.read_text(encoding="utf-8").replace(
                "docs/architecture.md", "docs/not-the-overview-architecture.md"
            ),
            encoding="utf-8",
        )
        self.commit("contradict declaration architecture")
        with self.assertRaisesRegex(SourceIntakeError, "contradicts"):
            ExactSourceReader().read_registration(
                remote=str(self.remote),
                source_ref="refs/heads/main",
                overview_path="docs/overview.md",
            )


if __name__ == "__main__":
    unittest.main()
