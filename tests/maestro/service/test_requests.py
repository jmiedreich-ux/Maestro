from __future__ import annotations

import json
import tempfile
import unittest
import urllib.error
import urllib.request
from pathlib import Path

from maestro.foundation import Database, DomainMigration, StorageSettings
from maestro.service.authentication import (
    OwnerAuthenticationSettings,
    OwnerAuthenticator,
    token_digest,
)
from maestro.service.http import RequestHTTPApplication, RequestHTTPServer
from maestro.service.registry import (
    OperationHandler,
    OperationRegistry,
    OperationResult,
    PreparedOperation,
    RegistryError,
)
from maestro.service.requests import RequestService


OWNER_TOKEN = "a" * 64
ANSWER_MIGRATION = DomainMigration(
    domain="test_answers",
    version=1,
    identity="test-answers-v1",
    statements=(
        """
        CREATE TABLE test_answers(
            sequence INTEGER PRIMARY KEY AUTOINCREMENT,
            question_id TEXT NOT NULL,
            version INTEGER NOT NULL,
            text TEXT NOT NULL
        )
        """,
    ),
)


def answer_handler(request) -> PreparedOperation:
    if request.project_id is None or request.activity_id is None or request.question_id is None:
        raise ValueError("question.answer requires project, activity, and question context")
    if set(request.payload) != {"text"}:
        raise ValueError("question.answer payload requires only text")
    text = request.payload["text"]
    if not isinstance(text, str) or not text.strip():
        raise ValueError("answer text must be nonempty")

    def apply(transaction, next_version: int) -> OperationResult:
        transaction.execute(
            "INSERT INTO test_answers(question_id, version, text) VALUES (?, ?, ?)",
            (request.question_id, next_version, text),
        )
        return OperationResult(
            data={"question_id": request.question_id, "text": text},
            project_id=request.project_id,
            activity_id=request.activity_id,
        )

    return PreparedOperation(
        entity_id=request.question_id,
        event_type="question.answered",
        event_data={"question_id": request.question_id},
        apply=apply,
    )


class DurableRequestTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        path = Path(self.temporary.name) / "maestro.sqlite3"
        self.database = Database(StorageSettings(path=path), [ANSWER_MIGRATION])
        authenticator = OwnerAuthenticator(
            OwnerAuthenticationSettings(
                owner_id="owner-local", token_sha256=token_digest(OWNER_TOKEN)
            )
        )
        registry = OperationRegistry(
            (OperationHandler("question.answer", answer_handler),)
        )
        service = RequestService(self.database, authenticator, registry)
        self.server = RequestHTTPServer(RequestHTTPApplication(service))
        self.server.start()
        self.addCleanup(self.server.close)
        host, port = self.server.address
        self.base_url = f"http://{host}:{port}/api/v1"

    @staticmethod
    def envelope(
        request_id: str = "request-one",
        *,
        text: str = "The saved answer",
        expected_version: int = 0,
    ) -> dict[str, object]:
        return {
            "request_id": request_id,
            "operation": "question.answer",
            "project_id": "project-one",
            "activity_id": "activity-one",
            "question_id": "question-one",
            "expected_version": expected_version,
            "payload": {"text": text},
        }

    def request(
        self,
        method: str,
        path: str,
        body: dict[str, object] | None = None,
        *,
        token: str = OWNER_TOKEN,
    ) -> tuple[int, dict[str, object], dict[str, str]]:
        encoded = None if body is None else json.dumps(body).encode("utf-8")
        request = urllib.request.Request(
            self.base_url + path,
            data=encoded,
            method=method,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
        )
        try:
            response = urllib.request.urlopen(request, timeout=5)
        except urllib.error.HTTPError as error:
            response = error
        with response:
            return (
                response.status,
                json.loads(response.read().decode("utf-8")),
                dict(response.headers.items()),
            )

    def test_post_commits_effect_receipt_and_event_before_lookup(self) -> None:
        status, submitted, _headers = self.request(
            "POST", "/requests", self.envelope()
        )
        lookup_status, looked_up, _headers = self.request(
            "GET", "/requests/request-one"
        )

        self.assertEqual(200, status)
        self.assertEqual(200, lookup_status)
        self.assertEqual(submitted, looked_up)
        receipt = submitted["receipt"]
        self.assertEqual("request-one", receipt["request_id"])
        self.assertEqual("completed", receipt["status"])
        self.assertEqual("question-one", receipt["entity_id"])
        self.assertEqual(1, receipt["resulting_version"])
        self.assertEqual("project-one", receipt["project_id"])
        self.assertEqual("activity-one", receipt["activity_id"])

        with self.database.read_connection() as connection:
            answer = connection.execute(
                "SELECT question_id, version, text FROM test_answers"
            ).fetchone()
            saved = connection.execute(
                """
                SELECT r.actor_id, r.resulting_version, s.status, e.type
                FROM request_receipts AS r
                JOIN service_request_results AS s USING(request_id)
                JOIN outbox_events AS e ON e.event_id = s.event_id
                """
            ).fetchone()
        self.assertEqual(("question-one", 1, "The saved answer"), answer)
        self.assertEqual(("owner-local", 1, "completed", "question.answered"), saved)

    def test_lost_response_reconciles_and_retry_does_not_repeat_effect(self) -> None:
        # The caller deliberately discards the committed POST response, as after a
        # connection loss, and reconciles solely from its stable request identity.
        self.request("POST", "/requests", self.envelope())
        lookup_status, looked_up, _headers = self.request(
            "GET", "/requests/request-one"
        )
        retry_status, retried, _headers = self.request(
            "POST", "/requests", self.envelope()
        )

        self.assertEqual(200, lookup_status)
        self.assertEqual(200, retry_status)
        self.assertEqual(looked_up, retried)
        with self.database.read_connection() as connection:
            counts = tuple(
                connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                for table in (
                    "test_answers",
                    "request_receipts",
                    "service_request_results",
                    "outbox_events",
                )
            )
        self.assertEqual((1, 1, 1, 1), counts)

    def test_reused_id_with_different_content_and_stale_version_are_409(self) -> None:
        self.request("POST", "/requests", self.envelope())
        conflict_status, conflict, _headers = self.request(
            "POST", "/requests", self.envelope(text="Different")
        )
        stale_status, stale, _headers = self.request(
            "POST", "/requests", self.envelope("request-two", expected_version=0)
        )

        self.assertEqual(409, conflict_status)
        self.assertEqual("request_content_conflict", conflict["error"]["code"])
        self.assertEqual(409, stale_status)
        self.assertEqual("version_conflict", stale["error"]["code"])
        self.assertEqual(1, stale["error"]["fields"]["current_version"])
        with self.database.read_connection() as connection:
            self.assertEqual(
                1, connection.execute("SELECT COUNT(*) FROM test_answers").fetchone()[0]
            )

    def test_authentication_validation_not_found_and_fixed_registry_boundaries(self) -> None:
        unauthorized_status, unauthorized, unauthorized_headers = self.request(
            "POST", "/requests", self.envelope(), token="b" * 64
        )
        missing_status, missing, _headers = self.request(
            "GET", "/requests/request-missing"
        )
        invalid = self.envelope()
        invalid["actor_id"] = "spoofed-owner"
        invalid_status, invalid_body, _headers = self.request(
            "POST", "/requests", invalid
        )

        self.assertEqual(401, unauthorized_status)
        self.assertEqual("unauthorized", unauthorized["error"]["code"])
        self.assertEqual("Bearer", unauthorized_headers["WWW-Authenticate"])
        self.assertEqual(404, missing_status)
        self.assertEqual("request_not_found", missing["error"]["code"])
        self.assertEqual(400, invalid_status)
        self.assertEqual("invalid_request", invalid_body["error"]["code"])
        with self.assertRaisesRegex(RegistryError, "not approved"):
            OperationHandler("caller.selected", answer_handler)


if __name__ == "__main__":
    unittest.main()
