from __future__ import annotations

import tempfile
import unittest
from dataclasses import dataclass, field
from pathlib import Path

from maestro.foundation import Database, StorageSettings
from maestro.service.activities import ActivityRecord, ActivityRepository, ProjectRecord
from maestro.service.authentication import (
    OwnerAuthenticationSettings,
    OwnerAuthenticator,
    token_digest,
)
from maestro.service.http import RequestHTTPServer
from maestro.service.questions import (
    AnswerChoice,
    DeliveredAnswer,
    LinkedQuestion,
    QuestionHTTPApplication,
    QuestionRequestService,
    QuestionService,
)
from maestro.service.registry import OperationRegistry
from maestro.service.requests import RequestService
from maestro.terminal.connection import (
    ConnectionConfiguration,
    ConnectionUnavailable,
    ServiceClient,
    ServiceError,
)
from maestro.terminal.extensions import ExtensionContext, ExtensionRegistry
from maestro.terminal.questions import QuestionInteraction, QuestionsExtension
from maestro.terminal.workspace import InputBuffer


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


@dataclass
class TerminalState:
    selected_project_id: str | None
    selected_activity_id: str | None
    input: InputBuffer = field(default_factory=InputBuffer)


class LoseFirstResponseClient:
    def __init__(self, client: ServiceClient) -> None:
        self.client = client
        self.lost = False

    def get_json(self, path: str, *, timeout: int = 15):
        return self.client.get_json(path, timeout=timeout)

    def submit(self, envelope):
        response = self.client.submit(envelope)
        if not self.lost:
            self.lost = True
            raise ConnectionUnavailable("committed response was lost")
        return response


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
        authenticator = OwnerAuthenticator(
            OwnerAuthenticationSettings(
                owner_id="owner-local", token_sha256=token_digest(OWNER_TOKEN)
            )
        )
        registry = OperationRegistry((self.questions.operation_handler,))
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

    def test_terminal_renders_choices_saves_answer_and_links_follow_up(self) -> None:
        self._publish()
        state = TerminalState("project-one", "activity-one")
        context = ExtensionContext(self.client, state)
        extension = QuestionsExtension(
            QuestionInteraction(request_id_factory=lambda: "request-answer-one")
        )
        registry = ExtensionRegistry()
        extension.install(registry)

        rendered = registry.render_view("question", context, "question-one")
        self.assertIn("Which source should the assessment use?", rendered)
        self.assertIn("Recommended: It matches the registered source.", rendered)
        self.assertIn("Free-text answer is available.", rendered)
        extension.interaction.choose(context, "main")
        self.assertEqual("Use main", state.input.text)
        self.assertEqual({}, self.recipient.effects)
        state.input.text += "\nUse the default branch head."
        response = extension.interaction.submit(context)

        self.assertEqual("completed", response["receipt"]["status"])
        self.assertEqual("", state.input.text)
        self.assertIsNone(state.input.question_id)
        delivered = self.recipient.effects["request-answer-one"]
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
            previous_answer_id="request-answer-one",
        )
        follow_up = extension.interaction.open(context, "question-follow-up")
        self.assertIn(
            "Follow-up to question-one after answer request-answer-one", follow_up
        )

    def test_lost_acknowledgment_and_interrupted_delivery_reconcile_once(self) -> None:
        self.recipient.interrupt_once = True
        self._publish()
        state = TerminalState("project-one", "activity-one")
        client = LoseFirstResponseClient(self.client)
        context = ExtensionContext(client, state)
        interaction = QuestionInteraction(
            request_id_factory=lambda: "request-uncertain"
        )
        interaction.open(context, "question-one")
        interaction.choose(context, "main")

        with self.assertRaises(ConnectionUnavailable):
            interaction.submit(context)
        self.assertIn("Delivery not confirmed", interaction.status or "")
        self.assertEqual("Use main", state.input.text)
        response = interaction.retry(context)

        self.assertEqual("request-uncertain", response["receipt"]["request_id"])
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


if __name__ == "__main__":
    unittest.main()
