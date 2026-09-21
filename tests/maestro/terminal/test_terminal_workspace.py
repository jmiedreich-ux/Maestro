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
    MAX_PAGE_SIZE,
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
from maestro.terminal.registration import RegistrationExtension
from maestro.terminal.workspace import View, Workspace, WorkspaceError


OWNER_TOKEN = "a" * 64
AUTHORIZATION = f"Bearer {OWNER_TOKEN}"


class ProjectionServer:
    """Expose the integrated projection reader through the documented read API."""

    def __init__(self, reader: ProjectionReader, authenticator: OwnerAuthenticator) -> None:
        self.reader = reader
        self.authenticator = authenticator
        self.paths: list[str] = []
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
        self.paths.append(path)
        parsed = urlsplit(path)
        if parsed.path == "/api/v1/workspace":
            return self.reader.workspace().as_dict()
        parts = parsed.path.split("/")
        query = parse_qs(parsed.query)
        if parsed.path == "/api/v1/projects":
            return self.reader.projects(
                before=query.get("before", [None])[0],
                limit=int(query.get("limit", [50])[0]),
            ).as_dict()
        if parsed.path == "/api/v1/attention":
            return self.reader.attention(
                before=query.get("before", [None])[0],
                limit=int(query.get("limit", [50])[0]),
            ).as_dict()
        if len(parts) == 6 and parts[:4] == ["", "api", "v1", "projects"]:
            project_id = unquote(parts[4])
            if parts[5] == "activities":
                before = query.get("before", [None])[0]
                return self.reader.activities(
                    project_id,
                    before=None if before is None else int(before),
                    limit=int(query.get("limit", [50])[0]),
                ).as_dict()
            if parts[5] == "conversation":
                before = query.get("before", [None])[0]
                return self.reader.conversation(
                    project_id,
                    before=None if before is None else int(before),
                    limit=int(query.get("limit", [50])[0]),
                ).as_dict()
        if (
            len(parts) == 8
            and parts[:4] == ["", "api", "v1", "projects"]
            and parts[5] == "activities"
        ):
            project_id = unquote(parts[4])
            activity_id = unquote(parts[6])
            resource = parts[7]
            before = query.get("before", [None])[0]
            limit = int(query.get("limit", [50])[0])
            if resource == "questions":
                return self.reader.questions(
                    project_id,
                    activity_id,
                    before=before,
                    limit=limit,
                ).as_dict()
            if resource == "findings":
                return self.reader.findings(
                    project_id,
                    activity_id,
                    before=before,
                    limit=limit,
                ).as_dict()
            if resource == "actions":
                return self.reader.actions(
                    project_id,
                    activity_id,
                    before=before,
                    limit=limit,
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

    def test_registration_extension_view_exposes_connected_activity_controls(self) -> None:
        self.create_project("project-controls", "Project Controls")
        with self.database.transaction() as transaction:
            transaction.execute(
                "DELETE FROM service_activity_actions WHERE activity_id = ?",
                ("activity-project-controls",),
            )
            transaction.executemany(
                """INSERT INTO service_activity_actions(
                       action_id, activity_id, project_id, kind, label
                   ) VALUES (?, ?, ?, ?, ?)""",
                (
                    (
                        "registration-confirm", "activity-project-controls",
                        "project-controls", "decision", "Confirm registration",
                    ),
                    (
                        "registration-cancel", "activity-project-controls",
                        "project-controls", "decision", "Cancel registration",
                    ),
                    (
                        "registration-retry.publication-one", "activity-project-controls",
                        "project-controls", "recovery", "Retry publication",
                    ),
                ),
            )
        workspace = Workspace(self.client)
        RegistrationExtension().install(workspace.extensions)
        workspace.refresh()
        workspace.select_project("project-controls")
        workspace.extension_view_name = "registration"
        workspace.extension_view_content = "State: Ready"
        workspace.view = View.EXTENSION

        controls = {
            target.identity for target in workspace.focus_targets()
            if target.kind == "action"
        }
        rendered = TerminalRenderer().render(workspace, TerminalSize(100, 30))
        self.assertEqual(
            {
                "registration-confirm",
                "registration-cancel",
                "registration-retry.publication-one",
            },
            controls,
        )
        self.assertIn("Confirm registration", rendered)
        self.assertIn("Cancel registration", rendered)
        self.assertIn("Retry publication", rendered)

        workspace.invoke_activity_action("registration-retry.publication-one")
        self.assertEqual("publication-one", workspace.input.action_id)
        self.assertIn(
            "Describe the intervention",
            str(workspace.selected_attention_detail["prompt"]),
        )

    def test_registration_command_reloads_controls_for_its_exact_activity(self) -> None:
        self.create_project("project-registration", "Project Registration")
        with self.database.transaction() as transaction:
            self.records.create_activity(
                transaction,
                ActivityRecord(
                    "registration-project-registration",
                    "project-registration",
                    "registration",
                    "Confirm registration",
                    "ready_to_confirm",
                    1,
                    available_actions=(
                        ActivityAction(
                            "registration-confirm", "Confirm registration", "decision"
                        ),
                    ),
                ),
            )

        underlying = self.client

        class RegistrationClient:
            def workspace(self, *, connect_timeout: bool = False):
                return underlying.workspace(connect_timeout=connect_timeout)

            def get_json(self, path: str, *, timeout: int = 15):
                if path == "/projects/project-registration/registration":
                    return {
                        "data": {
                            "project_id": "project-registration",
                            "activity_id": "registration-project-registration",
                            "activity_version": 1,
                            "state": "Ready to confirm",
                            "package_ref": {
                                "repository": "owner/project",
                                "commit": "a" * 40,
                                "registration_version": 1,
                                "candidate_id": "candidate-one",
                                "manifest_path": "manifest.json",
                                "manifest_sha256": "b" * 64,
                            },
                            "comparison": None,
                            "agent_retry": None,
                            "history": [],
                            "can_confirm": True,
                        }
                    }
                return underlying.get_json(path, timeout=timeout)

            def submit(self, envelope):
                return underlying.submit(envelope)

        workspace = Workspace(RegistrationClient())
        RegistrationExtension().install(workspace.extensions)
        workspace.refresh()
        workspace.select_project("project-registration")
        workspace.select_activity("activity-project-registration")
        self.assertEqual(
            "activity-project-registration", workspace.selected_activity_id
        )

        workspace.run_command("registration")

        self.assertEqual(
            "registration-project-registration", workspace.selected_activity_id
        )
        self.assertEqual(
            "registration-project-registration", workspace.activity_detail["activity_id"]
        )
        self.assertEqual(
            {"registration-confirm"},
            {
                target.identity
                for target in workspace.focus_targets()
                if target.kind == "action"
            },
        )

    def test_workspace_follows_bounded_project_and_attention_pages(self) -> None:
        self.create_project("project-one", "Project One")
        with self.database.transaction() as transaction:
            for number in range(MAX_PAGE_SIZE + 5):
                self.records.create_project(
                    transaction,
                    ProjectRecord(
                        f"project-page-{number:03d}",
                        f"Page project {number:03d}",
                        "registered",
                        1,
                    ),
                )
                self.records.create_question(
                    transaction,
                    QuestionRecord(
                        f"question-page-{number:03d}",
                        "project-one",
                        "activity-project-one",
                        f"Question {number:03d}",
                        "Choose a value",
                        "registration-architect",
                        "awaiting_answer",
                        1,
                    ),
                )

        workspace = Workspace(self.client)
        workspace.refresh()

        self.assertEqual(MAX_PAGE_SIZE + 6, len(workspace.projects))
        self.assertEqual(MAX_PAGE_SIZE + 7, len(workspace.attention))
        self.assertTrue(
            any(
                path.startswith("/api/v1/projects?before=")
                for path in self.projection_server.paths
            )
        )
        self.assertTrue(
            any(
                path.startswith("/api/v1/attention?before=")
                for path in self.projection_server.paths
            )
        )
        oldest = next(
            item
            for item in workspace.attention
            if item.record_id == "question-page-000"
        )
        workspace.open_attention(oldest.cursor)
        self.assertEqual(
            "Choose a value", workspace.selected_attention_detail["prompt"]
        )
        self.assertIn(
            "Question: Choose a value",
            TerminalRenderer().render(workspace, TerminalSize(100, 30)),
        )

    def test_activity_and_detail_continuations_preserve_older_current_context(self) -> None:
        self.create_project("project-one", "Project One")
        with self.database.transaction() as transaction:
            self.records.update_activity(
                transaction,
                ActivityRecord(
                    "activity-project-one",
                    "project-one",
                    "registration",
                    "Register Project One",
                    "waiting",
                    2,
                    "Owner answer required",
                    available_actions=(
                        ActivityAction(
                            "retry-project-one", "Retry activity", "recovery"
                        ),
                    )
                    + tuple(
                        ActivityAction(
                            f"action-detail-{number:03d}",
                            f"Detailed action {number:03d}",
                        )
                        for number in range(MAX_PAGE_SIZE + 5)
                    ),
                ),
                expected_record_version=1,
            )
            for number in range(55):
                self.records.create_activity(
                    transaction,
                    ActivityRecord(
                        f"activity-completed-{number:03d}",
                        "project-one",
                        "architecture",
                        f"Completed activity {number:03d}",
                        "completed",
                        1,
                    ),
                )
            for number in range(MAX_PAGE_SIZE + 5):
                self.records.create_question(
                    transaction,
                    QuestionRecord(
                        f"question-detail-{number:03d}",
                        "project-one",
                        "activity-project-one",
                        f"Detailed question {number:03d}",
                        f"Actual prompt {number:03d}",
                        "registration-architect",
                        "awaiting_answer",
                        1,
                    ),
                )
                self.records.create_finding(
                    transaction,
                    FindingRecord(
                        f"finding-detail-{number:03d}",
                        "project-one",
                        "activity-project-one",
                        f"Detailed finding {number:03d}",
                        f"Actual finding detail {number:03d}",
                        "open",
                        1,
                    ),
                )

        workspace = Workspace(self.client)
        workspace.refresh()
        workspace.select_project("project-one")

        self.assertEqual(56, len(workspace.activities))
        self.assertEqual("activity-project-one", workspace.selected_activity_id)
        self.assertTrue(
            any(
                path.startswith(
                    "/api/v1/projects/project-one/activities?before="
                )
                for path in self.projection_server.paths
            )
        )
        detail = workspace.activity_detail
        self.assertEqual(MAX_PAGE_SIZE + 6, len(detail["questions"]))
        self.assertEqual(MAX_PAGE_SIZE + 6, len(detail["findings"]))
        self.assertEqual(MAX_PAGE_SIZE + 6, len(detail["available_actions"]))
        question = next(
            item
            for item in detail["questions"]
            if item["question_id"] == "question-detail-000"
        )
        self.assertEqual("Actual prompt 000", question["prompt"])
        finding = next(
            item
            for item in detail["findings"]
            if item["finding_id"] == "finding-detail-000"
        )
        self.assertEqual("Actual finding detail 000", finding["detail"])
        self.assertIn(
            "action-detail-000",
            {item["action_id"] for item in detail["available_actions"]},
        )
        for resource in ("questions", "findings", "actions"):
            self.assertTrue(
                any(
                    f"/activities/activity-project-one/{resource}?before=" in path
                    for path in self.projection_server.paths
                )
            )
        attention = next(
            item
            for item in workspace.attention
            if item.record_id == "question-detail-000"
        )
        workspace.open_attention(attention.cursor)
        self.assertEqual("Actual prompt 000", workspace.selected_attention_detail["prompt"])

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
        self.assertIn(
            "Question: Which source should be used?",
            TerminalRenderer().render(workspace, TerminalSize(100, 30)),
        )
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
        before = [
            line
            for line in TerminalRenderer()
            .render(workspace, TerminalSize(100, 30))
            .splitlines()
            if line.startswith(("service:", "architect:"))
        ]

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
        after_render = TerminalRenderer().render(workspace, TerminalSize(100, 30))
        after = [
            line
            for line in after_render.splitlines()
            if line.startswith(("service:", "architect:"))
        ]
        self.assertEqual(before, after)
        self.assertIn("New messages", after_render)
        workspace.scroll_to_latest()
        self.assertFalse(workspace.new_messages)

        workspace.handle_event_error(
            ServiceError(
                409,
                "event_cursor_unavailable",
                "the event cursor is unavailable; load a fresh snapshot",
            )
        )
        self.assertFalse(workspace.stale)
        self.assertIsNone(workspace.error)

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
        registry.register_action("recovery", command)
        with self.assertRaisesRegex(ValueError, "already registered"):
            registry.register_command("/registration", command)
        workspace = Workspace(self.client, extensions=registry)
        workspace.refresh()
        workspace.select_project("project-one")

        self.assertEqual("opened", workspace.run_command("registration", "latest"))
        context = ExtensionContext(self.client, workspace)
        self.assertEqual("opened", workspace.open_extension_view("registration", "view"))
        self.assertIn(
            "opened", TerminalRenderer().render(workspace, TerminalSize(100, 30))
        )
        self.assertEqual("opened", registry.invoke_action("retry", context, "now"))
        self.assertEqual(self.client, seen[0][0])
        self.assertEqual("project-one", seen[0][1])
        self.assertFalse(hasattr(context, "database"))
        with self.assertRaises(KeyError):
            workspace.run_command("not-installed")
        recovery = next(item for item in workspace.attention if item.type == "recovery")
        workspace.open_attention(recovery.cursor)
        self.assertEqual("Retry activity", workspace.selected_attention_detail["label"])
        self.assertEqual("action", workspace.focused_target.kind)
        self.assertEqual("opened", workspace.handle_key("ENTER"))
        self.assertEqual(f"retry-project-one", seen[-1][2])

        calls_before_disconnect = len(seen)
        workspace.handle_connection_status(
            ConnectionStatus(
                ConnectionState.DISCONNECTED,
                self.projection_server.service_url,
                "offline",
                retry_in_seconds=1,
            )
        )
        for operation in (
            lambda: workspace.run_command("registration"),
            lambda: workspace.open_extension_view("registration"),
            lambda: workspace.invoke_action("retry"),
        ):
            with self.assertRaisesRegex(WorkspaceError, "disconnected or stale"):
                operation()
        self.assertEqual(calls_before_disconnect, len(seen))

        workspace.handle_connection_status(
            ConnectionStatus(
                ConnectionState.CONNECTED,
                self.projection_server.service_url,
                "connected",
            )
        )
        workspace.input.text = "ordinary conversation"
        workspace.input.cursor = len(workspace.input.text)
        with self.assertRaisesRegex(WorkspaceError, "accepts commands"):
            workspace.submit_input()

    def test_keyboard_focus_navigation_and_enter_activate_only_focused_target(self) -> None:
        self.create_project("project-one", "Project One")
        self.create_project("project-two", "Project Two")
        with self.database.transaction() as transaction:
            self.records.create_activity(
                transaction,
                ActivityRecord(
                    "activity-project-two-extra",
                    "project-two",
                    "architecture",
                    "Plan Project Two",
                    "working",
                    1,
                ),
            )
        workspace = Workspace(self.client)
        workspace.refresh()

        self.assertEqual("project", workspace.focused_target.kind)
        first_project = workspace.focused_target.identity
        workspace.handle_key("SHIFT+TAB")
        self.assertEqual(first_project, workspace.focused_target.identity)
        workspace.handle_key("DOWN")
        second_project = workspace.focused_target.identity
        self.assertNotEqual(first_project, second_project)
        workspace.handle_key("ENTER")
        self.assertEqual(second_project, workspace.selected_project_id)
        self.assertEqual("editor", workspace.focused_target.kind)

        activity_indexes = [
            index
            for index, target in enumerate(workspace.focus_targets())
            if target.kind == "activity"
        ]
        self.assertEqual(2, len(activity_indexes))
        workspace.focus = activity_indexes[1]
        selected_activity = workspace.focused_target.identity
        workspace.handle_key("ENTER")
        self.assertEqual(selected_activity, workspace.selected_activity_id)

        load_index = next(
            index
            for index, target in enumerate(workspace.focus_targets())
            if target.kind == "control"
            and target.identity == "load-earlier"
        )
        workspace.focus = load_index
        self.assertEqual(50, len(workspace.messages))
        workspace.handle_key("ENTER")
        self.assertEqual(55, len(workspace.messages))
        workspace.focus = len(workspace.focus_targets()) - 1

        workspace.handle_key("/")
        workspace.handle_key("p")
        workspace.handle_key("r")
        workspace.handle_key("o")
        workspace.handle_key("j")
        workspace.handle_key("e")
        workspace.handle_key("c")
        workspace.handle_key("t")
        workspace.handle_key("s")
        workspace.handle_key("ENTER")
        self.assertEqual(View.PROJECTS, workspace.view)
        self.assertEqual("", workspace.input.text)

        workspace.view = View.ATTENTION
        workspace.focus = 0
        attention_cursor = workspace.focused_target.identity
        workspace.handle_key("ENTER")
        self.assertEqual(attention_cursor, workspace.selected_attention)

        workspace.selected_attention_detail = {
            "choices": [
                {"choice_id": "choice-one", "label": "Use the pinned source"}
            ]
        }
        choice_index = next(
            index
            for index, target in enumerate(workspace.focus_targets())
            if target.kind == "choice"
        )
        workspace.focus = choice_index
        workspace.handle_key("ENTER")
        self.assertEqual("Use the pinned source", workspace.input.text)


if __name__ == "__main__":
    unittest.main()
