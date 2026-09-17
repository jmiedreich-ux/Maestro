from __future__ import annotations

import json
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit

from maestro.foundation import Database, StorageSettings
from maestro.service.activities import (
    ActivityAction,
    ActivityRecord,
    ActivityRepository,
    ConversationRecord,
    FindingRecord,
    ProjectRecord,
    QuestionRecord,
)
from maestro.service.authentication import (
    OwnerAuthenticationSettings,
    OwnerAuthenticator,
    token_digest,
)
from maestro.service.events import (
    EventStreamHTTPApplication,
    EventStreamHTTPServer,
    EventStreamService,
)
from maestro.service.projections import (
    ProjectionError,
    ProjectionNotFound,
    ProjectionReader,
)
from maestro.service.registry import (
    OperationHandler,
    OperationRegistry,
    OperationResult,
    PreparedOperation,
)
from maestro.service.requests import RequestService
from maestro.terminal.connection import (
    ConnectionConfiguration,
    ConnectionState,
    ConnectionStatus,
    ServiceClient,
    ServiceError,
)
from maestro.terminal.extensions import ExtensionContext, ExtensionRegistry
from maestro.terminal.rendering import TerminalRenderer, TerminalSize
from maestro.terminal.workspace import View, Workspace, WorkspaceError


OWNER_TOKEN = "a" * 64
AUTHORIZATION = f"Bearer {OWNER_TOKEN}"


class ProjectionServer:
    """Expose the integrated projection reader through the documented read API."""

    def __init__(self, reader: ProjectionReader, authenticator: OwnerAuthenticator) -> None:
        self.reader = reader
        self.authenticator = authenticator
        outer = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:
                try:
                    outer.authenticator.authenticate_read(self.headers.get("Authorization"))
                    body = outer.dispatch(self.path)
                    status = 200
                except (ProjectionError, ProjectionNotFound) as error:
                    status = 404 if isinstance(error, ProjectionNotFound) else 400
                    body = {"error": {"code": error.code, "message": str(error)}}
                except Exception as error:  # pragma: no cover - defensive test server boundary
                    status = getattr(error, "status_code", 500)
                    body = {"error": {"code": "read_failed", "message": str(error)}}
                encoded = json.dumps(body).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(encoded)))
                self.end_headers()
                self.wfile.write(encoded)

            def log_message(self, _format: str, *_args: object) -> None:
                return

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    @property
    def service_url(self) -> str:
        host, port = self.server.server_address[:2]
        return f"http://{host}:{port}"

    def start(self) -> None:
        self.thread.start()

    def close(self) -> None:
        self.server.shutdown()
        self.thread.join()
        self.server.server_close()

    def dispatch(self, path: str) -> dict[str, object]:
        parsed = urlsplit(path)
        if parsed.path == "/api/v1/workspace":
            return self.reader.workspace().as_dict()
        parts = parsed.path.split("/")
        query = parse_qs(parsed.query)
        if len(parts) == 6 and parts[:4] == ["", "api", "v1", "projects"]:
            project_id = unquote(parts[4])
            if parts[5] == "activities":
                return self.reader.activities(project_id).as_dict()
            if parts[5] == "conversation":
                before = query.get("before", [None])[0]
                return self.reader.conversation(
                    project_id,
                    before=None if before is None else int(before),
                    limit=int(query.get("limit", [50])[0]),
                ).as_dict()
        if len(parts) == 5 and parts[:4] == ["", "api", "v1", "activities"]:
            return self.reader.activity(unquote(parts[4])).as_dict()
        raise ProjectionNotFound("route_not_found", "read route was not found")


class TerminalWorkspaceTest(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.config = self.root / "config"
        self.config.mkdir(mode=0o700)
        self.token = self.config / "owner.token"
        self.token.write_text(OWNER_TOKEN, encoding="ascii")
        self.token.chmod(0o600)
        self.database = Database(StorageSettings(path=self.root / "maestro.sqlite3"))
        self.records = ActivityRepository(self.database)
        self.reader = ProjectionReader(self.database)
        self.authenticator = OwnerAuthenticator(
            OwnerAuthenticationSettings(
                owner_id="owner-local", token_sha256=token_digest(OWNER_TOKEN)
            )
        )
        registry = OperationRegistry(
            (
                OperationHandler("registration.start", self._prepare_project),
                OperationHandler("owner.decision", self._prepare_message),
            )
        )
        self.requests = RequestService(self.database, self.authenticator, registry)
        self.projection_server = ProjectionServer(self.reader, self.authenticator)
        self.projection_server.start()
        self.addCleanup(self.projection_server.close)
        self.client = ServiceClient(
            ConnectionConfiguration(
                self.projection_server.service_url,
                self.token,
                self.config / "cli.toml",
            )
        )

    def _prepare_project(self, request) -> PreparedOperation:
        project_id = str(request.payload["project_id"])
        activity_id = str(request.payload["activity_id"])
        name = str(request.payload["name"])

        def apply(transaction, version: int) -> OperationResult:
            self.records.create_records(
                transaction,
                project=ProjectRecord(project_id, name, "registering", version),
                activity=ActivityRecord(
                    activity_id, project_id, "registration", f"Register {name}",
                    "waiting", version, "Owner answer required",
                    available_actions=(
                        ActivityAction(
                            f"retry-{project_id}", "Retry activity", "recovery"
                        ),
                    ),
                ),
                questions=(QuestionRecord(
                    f"question-{project_id}", project_id, activity_id, "Choose source",
                    "Which source should be used?", "registration-architect",
                    "awaiting_answer", 1,
                ),),
                findings=(FindingRecord(
                    f"finding-{project_id}", project_id, activity_id, "Source incomplete",
                    "A source choice is required.", "open", 1,
                ),),
                conversation=tuple(
                    ConversationRecord(
                        f"message-{project_id}-{number:02d}", project_id, "service",
                        "progress", f"Update {number}",
                        f"2026-09-17T12:00:{number:02d}.000000Z", activity_id,
                    )
                    for number in range(1, 56)
                ),
            )
            return OperationResult({}, project_id=project_id, activity_id=activity_id)

        return PreparedOperation(
            entity_id=project_id,
            event_type="project.created",
            event_data={"project_id": project_id},
            apply=apply,
        )

    def _prepare_message(self, request) -> PreparedOperation:
        project_id = str(request.project_id)
        activity_id = str(request.activity_id)
        message_id = str(request.payload["message_id"])
        text = str(request.payload["text"])

        def apply(transaction, _version: int) -> OperationResult:
            self.records.append_conversation(
                transaction,
                ConversationRecord(
                    message_id, project_id, "architect", "finding", text,
                    "2026-09-17T13:00:00.000000Z", activity_id,
                ),
            )
            return OperationResult({}, project_id=project_id, activity_id=activity_id)

        return PreparedOperation(
            entity_id=project_id,
            event_type="conversation.message",
            event_data={"message_id": message_id},
            apply=apply,
        )

    def create_project(self, project_id: str, name: str) -> None:
        self.requests.submit(
            AUTHORIZATION,
            {
                "request_id": f"request-{project_id}",
                "operation": "registration.start",
                "project_id": None,
                "activity_id": None,
                "question_id": None,
                "expected_version": None,
                "payload": {
                    "project_id": project_id,
                    "activity_id": f"activity-{project_id}",
                    "name": name,
                },
            },
        )

    def test_real_service_snapshots_select_page_and_render_workspace(self) -> None:
        self.create_project("project-one", "Project One")
        workspace = Workspace(self.client)

        workspace.refresh()
        self.assertEqual(["Project One"], [item.name for item in workspace.projects])
        self.assertEqual(ConnectionState.CONNECTED, workspace.connection_state)
        workspace.select_project("project-one")
        self.assertEqual("activity-project-one", workspace.selected_activity_id)
        self.assertEqual(50, len(workspace.messages))
        self.assertTrue(workspace.load_earlier_messages())
        self.assertEqual(55, len(workspace.messages))
        self.assertEqual(0, workspace.conversation_offset)

        rendered = TerminalRenderer().render(workspace, TerminalSize(100, 30))
        self.assertIn("Maestro | Project One | connected", rendered)
        self.assertIn("Register Project One | waiting — Owner answer required", rendered)
        self.assertIn("service: Update", rendered)
        self.assertIn("Input | Commands only", rendered)
        self.assertEqual(
            "Enlarge the terminal to continue.",
            TerminalRenderer().render(workspace, TerminalSize(79, 24)),
        )

    def test_attention_input_keys_switch_and_disconnect_preserve_only_visible_context(self) -> None:
        self.create_project("project-one", "Project One")
        self.create_project("project-two", "Project Two")
        workspace = Workspace(self.client)
        workspace.refresh()
        workspace.select_project("project-one")
        workspace.handle_key("h")
        workspace.handle_key("i")
        workspace.handle_key("SHIFT+ENTER")
        workspace.handle_key("!")
        self.assertEqual("hi\n!", workspace.input.text)

        question = next(
            item
            for item in workspace.attention
            if item.project_id == "project-one" and item.type == "question"
        )
        workspace.open_attention(question.cursor)
        self.assertEqual("question-project-one", workspace.input.question_id)
        workspace.input.insert("draft answer")
        workspace.select_project("project-two")
        self.assertEqual("", workspace.input.text)
        self.assertIsNone(workspace.input.question_id)
        preserved = workspace.messages

        action = next(
            item
            for item in workspace.attention
            if item.project_id == "project-two" and item.type == "recovery"
        )
        workspace.open_attention(action.cursor)
        self.assertIsNone(workspace.input.question_id)
        self.assertEqual("activity-project-two", workspace.selected_activity_id)

        workspace.handle_connection_status(
            ConnectionStatus(
                ConnectionState.DISCONNECTED,
                self.projection_server.service_url,
                "stream ended",
                retry_in_seconds=1,
            )
        )
        self.assertEqual(preserved, workspace.messages)
        self.assertTrue(workspace.stale)
        rendered = TerminalRenderer().render(workspace, TerminalSize(100, 30))
        self.assertIn("STALE: Disconnected—information may be out of date.", rendered)

        workspace.handle_connection_status(
            ConnectionStatus(
                ConnectionState.CONNECTING,
                "http://localhost:8787",
                "service address changed",
                clear_service_context=True,
            )
        )
        self.assertEqual((), workspace.messages)
        self.assertIsNone(workspace.selected_project_id)
        self.assertEqual("", workspace.input.text)

    def test_committed_sse_refresh_holds_scrolled_position_and_marks_new_messages(self) -> None:
        self.create_project("project-one", "Project One")
        workspace = Workspace(self.client)
        workspace.refresh()
        workspace.select_project("project-one")
        workspace.load_earlier_messages()
        initial_cursor = workspace.event_cursor
        workspace.scroll_messages(-3)

        event_server = EventStreamHTTPServer(
            EventStreamHTTPApplication(EventStreamService(self.database, self.authenticator))
        )
        event_server.start()
        self.addCleanup(event_server.close)
        host, port = event_server.address
        event_client = ServiceClient(
            ConnectionConfiguration(
                f"http://{host}:{port}", self.token, self.config / "events.toml"
            )
        )
        self.requests.submit(
            AUTHORIZATION,
            {
                "request_id": "request-message-new",
                "operation": "owner.decision",
                "project_id": "project-one",
                "activity_id": "activity-project-one",
                "question_id": None,
                "expected_version": 1,
                "payload": {"message_id": "message-new", "text": "New committed finding"},
            },
        )
        event = next(event_client.events(str(initial_cursor)))

        workspace.apply_event(event)
        self.assertEqual("project-one", workspace.selected_project_id)
        self.assertFalse(workspace.at_bottom)
        self.assertTrue(workspace.new_messages)
        self.assertEqual(56, len(workspace.messages))
        self.assertIn("message-new", [item.message_id for item in workspace.messages])
        self.assertIn(
            "New messages", TerminalRenderer().render(workspace, TerminalSize(100, 30))
        )
        workspace.scroll_to_latest()
        self.assertFalse(workspace.new_messages)

    def test_empty_failure_and_malformed_data_never_look_like_success(self) -> None:
        empty = Workspace(self.client)
        empty.refresh()
        rendered = TerminalRenderer().render(empty, TerminalSize(100, 30))
        self.assertIn("No projects registered", rendered)
        self.assertNotIn("ERROR:", rendered)

        class FailedClient:
            def workspace(self, *, connect_timeout: bool = False):
                raise ServiceError(503, "service_unavailable", "database unavailable")

        failed = Workspace(FailedClient())
        failed.refresh()
        rendered = TerminalRenderer().render(failed, TerminalSize(100, 30))
        self.assertIn("ERROR: database unavailable", rendered)
        self.assertNotIn("No projects registered", rendered)

        class MalformedClient:
            def workspace(self, *, connect_timeout: bool = False):
                return {"data": {"projects": [], "attention": "not-a-list"}, "event_cursor": 0}

        malformed = Workspace(MalformedClient())
        malformed.refresh()
        self.assertIn("attention must be a list", malformed.error or "")

    def test_extensions_receive_client_and_projection_not_storage_authority(self) -> None:
        self.create_project("project-one", "Project One")
        registry = ExtensionRegistry()
        seen: list[tuple[object, str | None, str]] = []

        def command(context: ExtensionContext, arguments: str) -> str:
            seen.append((context.client, context.state.selected_project_id, arguments))
            return "opened"

        registry.register_command("registration", command)
        registry.register_view("registration", command)
        registry.register_action("retry", command)
        with self.assertRaisesRegex(ValueError, "already registered"):
            registry.register_command("/registration", command)
        workspace = Workspace(self.client, extensions=registry)
        workspace.refresh()
        workspace.select_project("project-one")

        self.assertEqual("opened", workspace.run_command("registration", "latest"))
        context = ExtensionContext(self.client, workspace)
        self.assertEqual("opened", registry.render_view("registration", context, "view"))
        self.assertEqual("opened", registry.invoke_action("retry", context, "now"))
        self.assertEqual(self.client, seen[0][0])
        self.assertEqual("project-one", seen[0][1])
        self.assertFalse(hasattr(context, "database"))
        with self.assertRaises(KeyError):
            workspace.run_command("not-installed")
        workspace.input.text = "ordinary conversation"
        workspace.input.cursor = len(workspace.input.text)
        with self.assertRaisesRegex(WorkspaceError, "accepts commands"):
            workspace.submit_input()


if __name__ == "__main__":
    unittest.main()
