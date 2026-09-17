from __future__ import annotations

import tempfile
import threading
import unittest
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit

from maestro.foundation import Database, StorageSettings
from maestro.service.activities import ActivityRecord, ActivityRepository, ProjectRecord
from maestro.service.authentication import (
    OwnerAuthenticationSettings,
    OwnerAuthenticator,
    token_digest,
)
from maestro.service.http import RequestHTTPServer
from maestro.service.main import (
    InstalledServiceApplication,
    InstalledServiceServer,
    ServiceSettings,
)
from maestro.service.questions import (
    AnswerChoice,
    DeliveredAnswer,
    LinkedQuestion,
    QuestionHTTPApplication,
    QuestionRequestService,
    QuestionService,
)
from maestro.service.projections import ProjectionReader
from maestro.service.registry import OperationRegistry
from maestro.service.requests import RequestService
from maestro.terminal.connection import (
    ConnectionConfiguration,
    ConnectionUnavailable,
    ServiceClient,
    ServiceError,
)
from maestro.terminal.questions import QuestionInteraction, QuestionsExtension
from maestro.terminal.rendering import TerminalRenderer, TerminalSize
from maestro.terminal.workspace import Workspace


OWNER_TOKEN = "a" * 64


class RecordingRecipient:
    """Apply once, then lose the first delivery acknowledgement."""

    def __init__(self, *, interrupt_once: bool = False) -> None:
        self.interrupt_once = interrupt_once
        self.calls: list[str] = []
        self.effects: dict[str, DeliveredAnswer] = {}

    def __call__(self, answer: DeliveredAnswer) -> None:
        self.calls.append(answer.answer_id)
        self.effects.setdefault(answer.answer_id, answer)
        if self.interrupt_once:
            self.interrupt_once = False
            raise ConnectionError("recipient acknowledgement was interrupted")


class LoseFirstResponseClient:
    def __init__(self, client: ServiceClient) -> None:
        self.client = client
        self.lost = False
        self.before_submit = None

    def get_json(self, path: str, *, timeout: int = 15):
        return self.client.get_json(path, timeout=timeout)

    def submit(self, envelope):
        if self.before_submit is not None:
            self.before_submit()
        response = self.client.submit(envelope)
        if not self.lost:
            self.lost = True
            raise ConnectionUnavailable("committed response was lost")
        return response


class WorkspaceQuestionClient:
    """Connect real Workspace reads to projections and question HTTP routes."""

    def __init__(
        self,
        reader: ProjectionReader,
        client: ServiceClient | LoseFirstResponseClient,
    ) -> None:
        self.reader = reader
        self.client = client

    def workspace(self, *, connect_timeout: bool = False):
        return self.reader.workspace().as_dict()

    def get_json(self, path: str, *, timeout: int = 15):
        parsed = urlsplit(path)
        if parsed.path.startswith(("/questions/", "/requests/")):
            return self.client.get_json(path, timeout=timeout)
        parts = parsed.path.split("/")
        query = parse_qs(parsed.query)
        if len(parts) == 4 and parts[1] == "projects":
            project_id = unquote(parts[2])
            if parts[3] == "activities":
                return self.reader.activities(project_id).as_dict()
            if parts[3] == "conversation":
                before = query.get("before", [None])[0]
                return self.reader.conversation(
                    project_id,
                    before=None if before is None else int(before),
                ).as_dict()
        if len(parts) == 3 and parts[1] == "activities":
            return self.reader.activity(unquote(parts[2])).as_dict()
        raise AssertionError(f"unexpected Workspace read path: {path}")

    def submit(self, envelope):
        return self.client.submit(envelope)


class LinkedQuestionsTest(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.database = Database(
            StorageSettings(path=self.root / "maestro.sqlite3")
        )
        self.recipient = RecordingRecipient()
        self.questions = QuestionService(
            self.database, {"registration-process": self.recipient}
        )
        self.records = ActivityRepository(self.database)
        self.reader = ProjectionReader(self.database)
        authenticator = OwnerAuthenticator(
            OwnerAuthenticationSettings(
                owner_id="owner-local", token_sha256=token_digest(OWNER_TOKEN)
            )
        )
        registry = OperationRegistry(self.questions.operation_handlers)
        requests = RequestService(self.database, authenticator, registry)
        boundary = QuestionRequestService(requests, self.questions)
        self.server = RequestHTTPServer(
            QuestionHTTPApplication(boundary, self.questions)  # type: ignore[arg-type]
        )
        self.server.start()
        self.addCleanup(self.server.close)
        host, port = self.server.address
        config = self.root / "config"
        config.mkdir(mode=0o700)
        token = config / "owner.token"
        token.write_text(OWNER_TOKEN, encoding="ascii")
        token.chmod(0o600)
        self.client = ServiceClient(
            ConnectionConfiguration(
                f"http://{host}:{port}", token, config / "cli.toml"
            )
        )
        self.workspace_client = WorkspaceQuestionClient(self.reader, self.client)
        self._create_project("project-one", "activity-one", "Project One")
        self._create_project("project-two", "activity-two", "Project Two")

    def _create_project(self, project_id: str, activity_id: str, name: str) -> None:
        with self.database.transaction() as transaction:
            self.records.create_project(
                transaction, ProjectRecord(project_id, name, "registering", 1)
            )
            self.records.create_activity(
                transaction,
                ActivityRecord(
                    activity_id,
                    project_id,
                    "registration",
                    f"Register {name}",
                    "waiting",
                    1,
                    "Owner answer required",
                ),
            )

    def _publish(
        self,
        question_id: str = "question-one",
        *,
        project_id: str = "project-one",
        activity_id: str = "activity-one",
        original_question_id: str | None = None,
        previous_answer_id: str | None = None,
    ) -> None:
        with self.database.transaction() as transaction:
            self.questions.publish(
                transaction,
                LinkedQuestion(
                    question_id=question_id,
                    project_id=project_id,
                    activity_id=activity_id,
                    subject="Choose the source",
                    prompt="Which source should the assessment use?",
                    requester="registration-architect",
                    recipient="registration-process",
                    choices=(
                        AnswerChoice(
                            "main",
                            "Use main",
                            "Uses the current default branch.",
                            "It matches the registered source.",
                        ),
                        AnswerChoice(
                            "revision",
                            "Use an exact revision",
                            "Requires supplying a commit identity.",
                        ),
                    ),
                    allow_free_text=True,
                    original_question_id=original_question_id,
                    previous_answer_id=previous_answer_id,
                ),
            )

    @staticmethod
    def _envelope(
        request_id: str,
        question_id: str,
        *,
        project_id: str = "project-one",
        activity_id: str = "activity-one",
        expected_version: int = 1,
        text: str = "Use main",
        choice_id: str | None = "main",
    ) -> dict[str, object]:
        return {
            "request_id": request_id,
            "operation": "question.answer",
            "project_id": project_id,
            "activity_id": activity_id,
            "question_id": question_id,
            "expected_version": expected_version,
            "payload": {"text": text, "choice_id": choice_id},
        }

    @staticmethod
    def _publish_envelope(
        request_id: str = "request-publish",
        *,
        question_id: str = "question-published",
        project_id: str | None = "project-one",
        activity_id: str | None = "activity-one",
    ) -> dict[str, object]:
        return {
            "request_id": request_id,
            "operation": "question.publish",
            "project_id": project_id,
            "activity_id": activity_id,
            "question_id": question_id,
            "expected_version": 0,
            "payload": {
                "subject": "Choose a source",
                "prompt": "Which source should be used?",
                "requester": "generic-process",
                "recipient": "generic-process",
                "choices": [
                    {
                        "choice_id": "main",
                        "label": "Use main",
                        "tradeoff": "Uses the current default branch.",
                        "recommendation_reason": "Matches the registered source.",
                    }
                ],
                "allow_free_text": True,
                "original_question_id": None,
                "previous_answer_id": None,
            },
        }

    def test_real_workspace_selects_choice_and_submits_with_clarification(self) -> None:
        self._publish()
        workspace = Workspace(self.workspace_client)
        extension = QuestionsExtension()
        extension.install(workspace.extensions)
        workspace.refresh()

        attention = next(
            item for item in workspace.attention if item.record_id == "question-one"
        )
        workspace.open_attention(attention.cursor)
        rendered = TerminalRenderer().render(workspace, TerminalSize(200, 30))
        self.assertIn("Which source should the assessment use?", rendered)
        self.assertIn("Recommended: It matches the registered source.", rendered)
        self.assertEqual(("question",), workspace.extensions.input_names)

        choice_index = next(
            index
            for index, target in enumerate(workspace.focus_targets())
            if target.kind == "choice" and target.identity == "main"
        )
        workspace.focus = choice_index
        workspace.handle_key("ENTER")
        self.assertEqual("main", workspace.input.choice_id)
        self.assertEqual("Use main", workspace.input.text)
        editor_index = next(
            index
            for index, target in enumerate(workspace.focus_targets())
            if target.kind == "editor"
        )
        workspace.focus = editor_index
        workspace.handle_key("SHIFT+ENTER")
        for character in "Use the default branch head.":
            workspace.handle_key(character)
        self.assertEqual(
            "Use main\nUse the default branch head.", workspace.input.text
        )
        self.assertEqual({}, self.recipient.effects)
        response = workspace.handle_key("ENTER")

        self.assertIsInstance(response, dict)
        assert isinstance(response, dict)
        self.assertEqual("completed", response["receipt"]["status"])
        request_id = str(response["receipt"]["request_id"])
        saved_rendering = TerminalRenderer().render(
            workspace, TerminalSize(200, 30)
        )
        self.assertIn(f"Answer received — saved receipt {request_id}.", saved_rendering)
        self.assertNotIn(
            "choice", {target.kind for target in workspace.focus_targets()}
        )
        delivered = self.recipient.effects[request_id]
        self.assertEqual("question-one", delivered.question_id)
        self.assertEqual("main", delivered.choice_id)
        self.assertEqual(
            "Use main\nUse the default branch head.", delivered.text
        )
        with self.database.read_connection() as connection:
            answer = connection.execute(
                """
                SELECT question_id, question_version, text, choice_id
                FROM service_question_answers
                """
            ).fetchone()
            question = connection.execute(
                "SELECT status, version FROM service_questions WHERE question_id = ?",
                ("question-one",),
            ).fetchone()
            delivery = connection.execute(
                "SELECT state, attempts FROM service_question_deliveries"
            ).fetchone()
            conversation = connection.execute(
                "SELECT source, kind, text FROM service_conversation"
            ).fetchone()
            migration = connection.execute(
                """
                SELECT domain, version, identity FROM domain_migrations
                WHERE domain = 'service_questions'
                """
            ).fetchone()
        self.assertEqual(
            (
                "question-one",
                2,
                "Use main\nUse the default branch head.",
                "main",
            ),
            answer,
        )
        self.assertEqual(("answer_received", 2), question)
        self.assertEqual(("delivered", 1), delivery)
        self.assertEqual(
            ("owner", "answer", "Use main\nUse the default branch head."),
            conversation,
        )
        self.assertEqual(
            ("service_questions", 1, "service-linked-questions-v1"), migration
        )

        self._publish(
            "question-follow-up",
            original_question_id="question-one",
            previous_answer_id=request_id,
        )
        workspace.refresh()
        follow_up = next(
            item
            for item in workspace.attention
            if item.record_id == "question-follow-up"
        )
        workspace.open_attention(follow_up.cursor)
        assert workspace.selected_attention_detail is not None
        self.assertEqual(
            "question-one",
            workspace.selected_attention_detail["original_question_id"],
        )
        self.assertEqual(
            request_id, workspace.selected_attention_detail["previous_answer_id"]
        )

    def test_real_workspace_submits_ordinary_free_text_without_choice(self) -> None:
        self._publish(
            "question-two", project_id="project-two", activity_id="activity-two"
        )
        workspace = Workspace(self.workspace_client)
        QuestionsExtension().install(workspace.extensions)
        workspace.refresh()
        attention = next(
            item for item in workspace.attention if item.record_id == "question-two"
        )
        workspace.open_attention(attention.cursor)

        for character in "Use the release branch":
            workspace.handle_key(character)
        response = workspace.handle_key("ENTER")

        self.assertIsInstance(response, dict)
        assert isinstance(response, dict)
        request_id = str(response["receipt"]["request_id"])
        delivered = self.recipient.effects[request_id]
        self.assertEqual("Use the release branch", delivered.text)
        self.assertIsNone(delivered.choice_id)
        self.assertEqual("", workspace.input.text)
        self.assertIsNone(workspace.input.question_id)

    def test_lost_acknowledgment_and_interrupted_delivery_reconcile_once(self) -> None:
        self.recipient.interrupt_once = True
        self._publish()
        transport = LoseFirstResponseClient(self.client)
        workspace = Workspace(WorkspaceQuestionClient(self.reader, transport))
        extension = QuestionsExtension(
            QuestionInteraction(request_id_factory=lambda: "request-uncertain")
        )
        extension.install(workspace.extensions)
        workspace.refresh()
        attention = next(
            item for item in workspace.attention if item.record_id == "question-one"
        )
        workspace.open_attention(attention.cursor)
        choice_index = next(
            index
            for index, target in enumerate(workspace.focus_targets())
            if target.kind == "choice" and target.identity == "main"
        )
        workspace.focus = choice_index
        workspace.handle_key("ENTER")
        workspace.focus = next(
            index
            for index, target in enumerate(workspace.focus_targets())
            if target.kind == "editor"
        )
        sending_renderings: list[str] = []
        transport.before_submit = lambda: sending_renderings.append(
            TerminalRenderer().render(workspace, TerminalSize(200, 30))
        )

        with self.assertRaises(ConnectionUnavailable):
            workspace.handle_key("ENTER")
        self.assertIn(
            "Sending — waiting for save acknowledgment.", sending_renderings[0]
        )
        self.assertEqual("Use main", workspace.input.text)
        self.assertEqual("main", workspace.input.choice_id)
        failed_rendering = TerminalRenderer().render(
            workspace, TerminalSize(200, 30)
        )
        self.assertIn("Not sent — Delivery not confirmed.", failed_rendering)
        self.assertIn("choice", {target.kind for target in workspace.focus_targets()})
        response = workspace.handle_key("ENTER")

        self.assertEqual("request-uncertain", response["receipt"]["request_id"])
        saved_rendering = TerminalRenderer().render(
            workspace, TerminalSize(200, 30)
        )
        self.assertIn(
            "Answer received — saved receipt request-uncertain.", saved_rendering
        )
        self.assertNotIn(
            "choice", {target.kind for target in workspace.focus_targets()}
        )
        self.assertEqual(["request-uncertain", "request-uncertain"], self.recipient.calls)
        self.assertEqual({"request-uncertain"}, set(self.recipient.effects))
        with self.database.read_connection() as connection:
            counts = tuple(
                connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                for table in (
                    "service_question_answers",
                    "request_receipts",
                    "service_request_results",
                    "outbox_events",
                    "service_conversation",
                )
            )
            delivery = connection.execute(
                "SELECT state, attempts FROM service_question_deliveries"
            ).fetchone()
        self.assertEqual((1, 1, 1, 1, 1), counts)
        self.assertEqual(("delivered", 2), delivery)

    def test_real_workspace_renders_typed_stale_rejection(self) -> None:
        self._publish()
        workspace = Workspace(self.workspace_client)
        QuestionsExtension().install(workspace.extensions)
        workspace.refresh()
        attention = next(
            item for item in workspace.attention if item.record_id == "question-one"
        )
        workspace.open_attention(attention.cursor)
        self.client.submit(self._envelope("request-other", "question-one"))
        for character in "A late answer":
            workspace.handle_key(character)

        with self.assertRaises(ServiceError) as rejected:
            workspace.handle_key("ENTER")

        self.assertEqual(409, rejected.exception.status_code)
        rendering = TerminalRenderer().render(workspace, TerminalSize(200, 30))
        self.assertIn("Not sent — the expected version is stale.", rendering)
        self.assertEqual("A late answer", workspace.input.text)

    def test_wrong_stale_and_late_answers_reject_without_inferring_silence(self) -> None:
        self._publish()
        self._publish(
            "question-two", project_id="project-two", activity_id="activity-two"
        )

        with self.assertRaises(ServiceError) as wrong_project:
            self.client.submit(
                self._envelope(
                    "request-wrong-project",
                    "question-one",
                    project_id="project-two",
                    activity_id="activity-two",
                )
            )
        self.assertEqual("wrong_question_context", wrong_project.exception.code)

        with self.assertRaises(ServiceError) as wrong_question:
            self.client.submit(
                self._envelope(
                    "request-wrong-question",
                    "question-two",
                )
            )
        self.assertEqual("wrong_question_context", wrong_question.exception.code)

        accepted = self.client.submit(
            self._envelope("request-correct", "question-one")
        )
        self.assertEqual("completed", accepted["receipt"]["status"])
        duplicate = self.client.submit(
            self._envelope("request-correct", "question-one")
        )
        self.assertEqual(accepted, duplicate)

        with self.assertRaises(ServiceError) as stale:
            self.client.submit(
                self._envelope("request-stale", "question-one")
            )
        self.assertEqual("version_conflict", stale.exception.code)
        with self.assertRaises(ServiceError) as late:
            self.client.submit(
                self._envelope(
                    "request-late",
                    "question-one",
                    expected_version=2,
                )
            )
        self.assertEqual("question_not_awaiting_answer", late.exception.code)

        self.assertEqual((), self.questions.deliver_pending())
        with self.database.read_connection() as connection:
            answers = connection.execute(
                "SELECT question_id, COUNT(*) FROM service_question_answers GROUP BY question_id"
            ).fetchall()
            silent = connection.execute(
                """
                SELECT status, version FROM service_questions
                WHERE question_id = 'question-two'
                """
            ).fetchone()
        self.assertEqual([("question-one", 1)], answers)
        self.assertEqual(("awaiting_answer", 1), silent)

    def test_malformed_question_route_is_a_typed_http_rejection(self) -> None:
        with self.assertRaises(ServiceError) as malformed:
            self.client.get_json("/questions/question%2Fescaped")

        self.assertEqual(400, malformed.exception.status_code)
        self.assertEqual("invalid_request", malformed.exception.code)

    def test_publish_parser_rejects_missing_context_and_malformed_choices(self) -> None:
        with self.assertRaises(ServiceError) as missing:
            self.client.submit(
                self._publish_envelope(
                    "request-publish-missing",
                    project_id=None,
                    activity_id=None,
                )
            )
        self.assertEqual(400, missing.exception.status_code)
        self.assertEqual("invalid_request", missing.exception.code)

        malformed = self._publish_envelope("request-publish-malformed")
        payload = malformed["payload"]
        assert isinstance(payload, dict)
        choices = payload["choices"]
        assert isinstance(choices, list)
        choice = choices[0]
        assert isinstance(choice, dict)
        choice["unknown"] = True
        with self.assertRaises(ServiceError) as rejected:
            self.client.submit(malformed)
        self.assertEqual(400, rejected.exception.status_code)
        self.assertEqual("invalid_request", rejected.exception.code)


class InstalledQuestionCompositionTest(unittest.TestCase):
    def test_installed_public_api_publishes_reads_answers_and_reconciles(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        workspace_root = root / "workspaces"
        workspace_root.mkdir()
        settings = ServiceSettings(
            storage=StorageSettings(path=root / "maestro.sqlite3"),
            owner=OwnerAuthenticationSettings(
                owner_id="owner-local", token_sha256=token_digest(OWNER_TOKEN)
            ),
            workspace_root=workspace_root,
        )
        application = InstalledServiceApplication(settings)
        with application.database.transaction() as transaction:
            application.activities.create_project(
                transaction,
                ProjectRecord("project-installed", "Installed project", "ready", 1),
            )
            application.activities.create_activity(
                transaction,
                ActivityRecord(
                    "activity-installed",
                    "project-installed",
                    "generic",
                    "Ask a generic question",
                    "waiting",
                    1,
                ),
            )

        server = InstalledServiceServer(application, "127.0.0.1", 0)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()

        def stop() -> None:
            server.shutdown()
            thread.join()

        self.addCleanup(stop)
        host, port = server.address
        config = root / "config"
        config.mkdir(mode=0o700)
        token = config / "owner.token"
        token.write_text(OWNER_TOKEN, encoding="ascii")
        token.chmod(0o600)
        client = ServiceClient(
            ConnectionConfiguration(
                f"http://{host}:{port}", token, config / "cli.toml"
            )
        )
        publish = LinkedQuestionsTest._publish_envelope(
            project_id="project-installed",
            activity_id="activity-installed",
        )

        missing_activity = LinkedQuestionsTest._publish_envelope(
            "request-publish-missing-activity",
            question_id="question-missing-activity",
            project_id="project-installed",
            activity_id="activity-missing",
        )
        with self.assertRaises(ServiceError) as missing:
            client.submit(missing_activity)
        self.assertEqual(404, missing.exception.status_code)
        self.assertEqual("activity_not_found", missing.exception.code)

        published = client.submit(publish)
        question = client.get_json("/questions/question-published")["data"]
        answer = {
            "request_id": "request-installed-answer",
            "operation": "question.answer",
            "project_id": "project-installed",
            "activity_id": "activity-installed",
            "question_id": "question-published",
            "expected_version": 1,
            "payload": {"text": "Use main", "choice_id": "main"},
        }
        lost_response = LoseFirstResponseClient(client)
        with self.assertRaises(ConnectionUnavailable):
            lost_response.submit(answer)
        reconciled = client.get_json("/requests/request-installed-answer")
        retried = client.submit(answer)
        invalid_follow_up = LinkedQuestionsTest._publish_envelope(
            "request-invalid-follow-up",
            question_id="question-invalid-follow-up",
            project_id="project-installed",
            activity_id="activity-installed",
        )
        follow_up_payload = invalid_follow_up["payload"]
        assert isinstance(follow_up_payload, dict)
        follow_up_payload["original_question_id"] = "question-published"
        follow_up_payload["previous_answer_id"] = "answer-missing"
        with self.assertRaises(ServiceError) as invalid_link:
            client.submit(invalid_follow_up)

        self.assertEqual("completed", published["receipt"]["status"])
        self.assertEqual("question-published", question["question_id"])
        self.assertEqual("awaiting_answer", question["status"])
        self.assertEqual(reconciled, retried)
        self.assertEqual("pending", retried["receipt"]["result"]["delivery_status"])
        self.assertEqual(409, invalid_link.exception.status_code)
        self.assertEqual("invalid_question_link", invalid_link.exception.code)
        with application.database.read_connection() as connection:
            counts = connection.execute(
                """
                SELECT
                  (SELECT COUNT(*) FROM service_questions),
                  (SELECT COUNT(*) FROM service_question_answers),
                  (SELECT COUNT(*) FROM request_receipts),
                  (SELECT COUNT(*) FROM outbox_events)
                """
            ).fetchone()
            delivery = connection.execute(
                "SELECT state, attempts FROM service_question_deliveries"
            ).fetchone()
        self.assertEqual((1, 1, 2, 2), counts)
        self.assertEqual(("pending", 0), delivery)


if __name__ == "__main__":
    unittest.main()
