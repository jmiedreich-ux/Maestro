from __future__ import annotations

import io
import tempfile
import threading
import unittest
from collections.abc import Callable
from pathlib import Path

from maestro.foundation import StorageSettings
from maestro.service.authentication import OwnerAuthenticationSettings, token_digest
from maestro.service.main import (
    InstalledServiceApplication,
    InstalledServiceServer,
    ServiceSettings,
)
from maestro.terminal.connection import (
    ConnectionConfiguration,
    ConnectionUnavailable,
    ServiceClient,
    TerminalConnection,
)
from maestro.terminal.main import main as terminal_main


OWNER_TOKEN = "a" * 64


class AnswerClient:
    def __init__(
        self,
        configuration: ConnectionConfiguration,
        *,
        lose_first_answer: bool = False,
        stale_first_answer: bool = False,
        before_events: Callable[[], None] | None = None,
    ) -> None:
        self.client = ServiceClient(configuration)
        self.lose_first_answer = lose_first_answer
        self.stale_first_answer = stale_first_answer
        self.before_events = before_events

    def workspace(self, *, connect_timeout: bool = False):
        return self.client.workspace(connect_timeout=connect_timeout)

    def get_json(self, path: str, *, timeout: int = 15):
        return self.client.get_json(path, timeout=timeout)

    def events(self, last_event_id: str | None = None):
        if self.before_events is not None:
            callback, self.before_events = self.before_events, None
            callback()
        return self.client.events(last_event_id)

    def close_event_stream(self) -> None:
        self.client.close_event_stream()

    def submit(self, envelope):
        if envelope.get("operation") != "question.answer":
            return self.client.submit(envelope)
        if self.stale_first_answer:
            self.stale_first_answer = False
            self.client.submit(
                {
                    **envelope,
                    "request_id": "concurrent-answer",
                    "payload": {"text": "Concurrent answer", "choice_id": None},
                }
            )
        response = self.client.submit(envelope)
        if self.lose_first_answer:
            self.lose_first_answer = False
            raise ConnectionUnavailable("committed answer response was lost")
        return response


class InstalledTerminalEntryTest(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        workspace_root = self.root / "workspaces"
        workspace_root.mkdir()
        self.application = InstalledServiceApplication(
            ServiceSettings(
                storage=StorageSettings(path=self.root / "maestro.sqlite3"),
                owner=OwnerAuthenticationSettings(
                    owner_id="owner-local", token_sha256=token_digest(OWNER_TOKEN)
                ),
                workspace_root=workspace_root,
            )
        )
        self.server = InstalledServiceServer(self.application, "127.0.0.1", 0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

        def stop() -> None:
            self.server.shutdown()
            self.thread.join()

        self.addCleanup(stop)
        host, port = self.server.address
        self.config_root = self.root / "config"
        config = self.config_root / "maestro"
        config.mkdir(parents=True, mode=0o700)
        token = config / "owner.token"
        token.write_text(OWNER_TOKEN, encoding="ascii")
        token.chmod(0o600)
        (config / "cli.toml").write_text(
            f'service_url = "http://{host}:{port}"\n'
            f'owner_credential_file = "{token}"\n',
            encoding="utf-8",
        )
        self.configuration = ConnectionConfiguration(
            f"http://{host}:{port}", token, config / "cli.toml"
        )
        self.seed = ServiceClient(self.configuration)
        self.seed.submit(
            {
                "request_id": "bootstrap-terminal",
                "operation": "project.bootstrap",
                "project_id": "project-terminal",
                "activity_id": "activity-terminal",
                "question_id": None,
                "expected_version": 0,
                "payload": {
                    "project_name": "Terminal project",
                    "activity_subject": "Answer through the installed terminal",
                },
            }
        )
        self.seed.submit(
            {
                "request_id": "publish-terminal-question",
                "operation": "question.publish",
                "project_id": "project-terminal",
                "activity_id": "activity-terminal",
                "question_id": "question-terminal",
                "expected_version": 0,
                "payload": {
                    "subject": "Select a source",
                    "prompt": "Which source should the terminal use?",
                    "requester": "generic-process",
                    "recipient": "generic-process",
                    "choices": [],
                    "allow_free_text": True,
                    "original_question_id": None,
                    "previous_answer_id": None,
                },
            }
        )

    def run_terminal(self, client_factory, keys: str) -> str:
        connection = TerminalConnection(
            environ={"XDG_CONFIG_HOME": str(self.config_root)},
            client_factory=client_factory,
        )
        output = io.StringIO()
        self.assertEqual(
            0,
            terminal_main(
                argv=[],
                connection_factory=lambda: connection,
                input_stream=io.StringIO(keys),
                output_stream=output,
            ),
        )
        return output.getvalue()

    def test_entrypoint_navigates_question_and_retries_lost_acknowledgment(self) -> None:
        output = self.run_terminal(
            lambda configuration: AnswerClient(
                configuration, lose_first_answer=True
            ),
            "\t/attention\n\n"
            "\x1b[200~Use the published source\nwith supporting detail\x1b[201~"
            "\n\n/exit\n",
        )

        self.assertIn("Maestro | No project selected | connected", output)
        self.assertIn("Terminal project | Not registered | waiting | attention: 1", output)
        self.assertIn("Question: Which source should the terminal use?", output)
        self.assertIn("Delivery not confirmed", output)
        self.assertIn("Answer received — saved receipt", output)
        self.assertIn("service work continues", output)
        with self.application.database.read_connection() as connection:
            answer = connection.execute(
                "SELECT text FROM service_question_answers"
            ).fetchone()
        self.assertEqual(
            ("Use the published source\nwith supporting detail",), answer
        )

    def test_entrypoint_warns_before_discarding_unsent_pasted_text(self) -> None:
        output = self.run_terminal(
            lambda configuration: AnswerClient(
                configuration, before_events=self.publish_additional_question
            ),
            "\t/attention\n\n"
            "\x1b[200~Unsent first line\nUnsent second line\x1b[201~"
            "/exit\n/exit\n",
        )

        warning = "Unsent text remains. Enter /exit again to discard it and exit."
        self.assertIn(warning, output)
        self.assertLess(output.index(warning), output.index("service work continues"))
        self.assertIn("Unsent first line", output)
        self.assertIn("Unsent second line", output)
        with self.application.database.read_connection() as connection:
            count = connection.execute(
                "SELECT COUNT(*) FROM service_question_answers"
            ).fetchone()
        self.assertEqual((0,), count)

    def publish_additional_question(self) -> None:
        self.seed.submit(
            {
                "request_id": "publish-additional-question",
                "operation": "question.publish",
                "project_id": "project-terminal",
                "activity_id": "activity-terminal",
                "question_id": "question-additional",
                "expected_version": 0,
                "payload": {
                    "subject": "Additional question",
                    "prompt": "This update exercises the terminal event stream.",
                    "requester": "generic-process",
                    "recipient": "generic-process",
                    "choices": [],
                    "allow_free_text": True,
                    "original_question_id": None,
                    "previous_answer_id": None,
                },
            }
        )

    def test_entrypoint_renders_stale_answer_failure_without_rerouting(self) -> None:
        output = self.run_terminal(
            lambda configuration: AnswerClient(
                configuration, stale_first_answer=True
            ),
            "\t/attention\n\nLate terminal answer\n",
        )

        self.assertIn("Question: Which source should the terminal use?", output)
        self.assertIn("Not sent — the expected version is stale.", output)
        self.assertIn("ERROR: the expected version is stale", output)
        with self.application.database.read_connection() as connection:
            answers = connection.execute(
                "SELECT request_id, text FROM service_question_answers"
            ).fetchall()
        self.assertEqual([("concurrent-answer", "Concurrent answer")], answers)


if __name__ == "__main__":
    unittest.main()
