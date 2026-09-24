"""Installed Maestro service entry point and startup validation."""

from __future__ import annotations

import argparse
import json
import logging
import os
import signal
import sqlite3
import stat
import sys
import threading
import time
import tomllib
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Mapping
from urllib.parse import SplitResult, parse_qs, unquote, urlsplit

from maestro.foundation import Database, StorageSettings

from .activities import ActivityRepository
from .authentication import (
    HTTPRejection,
    OwnerAuthenticationSettings,
    OwnerAuthenticator,
)
from .events import EventHTTPResponse, EventStreamHTTPApplication, EventStreamService
from .http import MAX_REQUEST_BYTES, HTTPResponse
from .projections import ProjectionError, ProjectionNotFound, ProjectionReader, _event_cursor
from .questions import QuestionHTTPApplication, QuestionRequestService, QuestionService
from .process_definitions import PROCESS_TABLES, ProcessDefinitions, process_registry
from .processes import ProcessPolicyService
from .registry import OperationRegistry
from .resources import InstalledSchemaResources, ProcessResourceError
from .requests import RequestService


log = logging.getLogger("maestro.service")
DEFAULT_CONFIG_PATH = Path("/etc/maestro/agents.toml")
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8787
MAX_CONFIG_BYTES = 1_048_576
_LOOPBACK_HOSTS = frozenset({"127.0.0.1", "::1", "localhost"})
_BASE_TABLES = frozenset({"service", "storage", "owner"})
# Later process packets own validation of these architecture-defined sections.
_RESERVED_TABLES = frozenset(
    {
        "tools",
        "repositories",
        "repository_bindings",
        "registration",
        "architecture_loop",
        "execution",
    }
)


class ServiceConfigurationError(ValueError):
    """The installed service configuration is missing, unsafe, or invalid."""


@dataclass(frozen=True)
class ServiceSettings:
    """Validated startup settings needed by the installed service wrapper."""

    storage: StorageSettings
    owner: OwnerAuthenticationSettings
    host: str = DEFAULT_HOST
    port: int = DEFAULT_PORT
    agent_user: str = "maestro-agent"
    workspace_root: Path = Path("/var/lib/maestro/workspaces")
    config_path: Path | None = None
    process_tables: Mapping[str, object] = field(default_factory=dict)
    registration_tables: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.host not in _LOOPBACK_HOSTS:
            raise ServiceConfigurationError("service.host must be a loopback host")
        if isinstance(self.port, bool) or not isinstance(self.port, int):
            raise ServiceConfigurationError("service.port must be an integer")
        if not 1 <= self.port <= 65535:
            raise ServiceConfigurationError("service.port must be between 1 and 65535")
        if not _account_name(self.agent_user):
            raise ServiceConfigurationError("service.agent_user is invalid")
        if not self.workspace_root.is_absolute():
            raise ServiceConfigurationError("workspace_root must be absolute")


def load_settings(path: Path = DEFAULT_CONFIG_PATH) -> ServiceSettings:
    """Load and validate startup settings without accepting a linked config file."""
    path = Path(path)
    if not path.is_absolute():
        raise ServiceConfigurationError("service configuration path must be absolute")
    _reject_linked_components(path)
    try:
        details = os.lstat(path)
        if not stat.S_ISREG(details.st_mode):
            raise ServiceConfigurationError(
                "service configuration must be a regular file, not a link"
            )
        if stat.S_IMODE(details.st_mode) & 0o022:
            raise ServiceConfigurationError(
                "service configuration must not be writable by group or other"
            )
        if details.st_size > MAX_CONFIG_BYTES:
            raise ServiceConfigurationError("service configuration is too large")
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
        try:
            raw = os.read(descriptor, MAX_CONFIG_BYTES + 1)
        finally:
            os.close(descriptor)
    except FileNotFoundError as error:
        raise ServiceConfigurationError(
            f"service configuration does not exist: {path}"
        ) from error
    except OSError as error:
        raise ServiceConfigurationError(
            f"service configuration cannot be read: {path}"
        ) from error

    try:
        value = tomllib.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, tomllib.TOMLDecodeError) as error:
        raise ServiceConfigurationError("service configuration is not valid TOML") from error
    if not isinstance(value, dict):
        raise ServiceConfigurationError("service configuration must be a TOML table")
    unknown = set(value) - _BASE_TABLES - _RESERVED_TABLES - {"workspace_root"}
    if unknown:
        raise ServiceConfigurationError(
            f"unsupported service setting(s): {', '.join(sorted(unknown))}"
        )
    missing = _BASE_TABLES - set(value)
    if missing:
        raise ServiceConfigurationError(
            f"missing service configuration table(s): {', '.join(sorted(missing))}"
        )
    service = _table(value["service"], "service")
    unknown_service = set(service) - {"host", "port", "agent_user"}
    if unknown_service:
        raise ServiceConfigurationError(
            f"unsupported service setting(s): {', '.join(sorted(unknown_service))}"
        )
    workspace_root = value.get("workspace_root", "/var/lib/maestro/workspaces")
    if not isinstance(workspace_root, str):
        raise ServiceConfigurationError("workspace_root must be text")
    try:
        storage = StorageSettings.from_mapping(_table(value["storage"], "storage"))
        owner = OwnerAuthenticationSettings.from_mapping(_table(value["owner"], "owner"))
    except ValueError as error:
        raise ServiceConfigurationError(str(error)) from error
    host = service.get("host", DEFAULT_HOST)
    port = service.get("port", DEFAULT_PORT)
    agent_user = service.get("agent_user", "maestro-agent")
    if not isinstance(host, str):
        raise ServiceConfigurationError("service.host must be text")
    if isinstance(port, bool) or not isinstance(port, int):
        raise ServiceConfigurationError("service.port must be an integer")
    if not isinstance(agent_user, str):
        raise ServiceConfigurationError("service.agent_user must be text")
    process_tables = {name: value[name] for name in PROCESS_TABLES if name in value}
    registration_tables = {name: value[name] for name in ("tools", "repositories", "repository_bindings", "execution") if name in value}
    return ServiceSettings(
        process_tables=process_tables,
        registration_tables=registration_tables,
        storage=storage,
        owner=owner,
        host=host,
        port=port,
        agent_user=agent_user,
        workspace_root=Path(workspace_root),
        config_path=path,
    )


class InstalledServiceApplication:
    """Compose authenticated reads, durable requests, and the event stream."""

    def __init__(self, settings: ServiceSettings) -> None:
        self.database = Database(settings.storage)
        # Register the currently installed core domain before final initialization.
        self.activities = ActivityRepository(self.database)
        self.authenticator = OwnerAuthenticator(settings.owner)
        self.questions = QuestionService(self.database)
        self.process_definitions = _process_definitions(self.database, settings.config_path)
        self.registration = _registration(self.database, self.activities, self.questions, self.process_definitions, settings)
        self.architecture = _architecture(self.database, self.registration, self.questions, self.process_definitions, settings)
        self.execution = _execution(self.database, self.registration, self.architecture, self.questions, settings)
        handlers = (
            self.questions.operation_handlers
            + (() if self.registration is None else self.registration.operation_handlers)
            + (() if self.architecture is None else self.architecture.operation_handlers)
            + (() if self.execution is None else self.execution.operation_handlers)
        )
        if self.registration is not None and self.architecture is not None:
            from .architecture import shared_owner_decision

            handlers = tuple(h for h in handlers if h.operation != "owner.decision") + (shared_owner_decision(self.registration, self.architecture, self.execution),)

        base_requests = RequestService(
            self.database,
            self.authenticator,
            OperationRegistry(handlers),
        )
        self.requests = QuestionRequestService(base_requests, self.questions)
        self.projections = ProjectionReader(self.database)
        self.request_application = QuestionHTTPApplication(
            self.requests, self.questions
        )
        self.event_application = EventStreamHTTPApplication(
            EventStreamService(self.database, self.authenticator)
        )
        self._worker_stop = threading.Event()
        self._worker: threading.Thread | None = None

    def start(self) -> None:
        self.event_application.start()
        if self.registration is not None:
            if self.registration.runs is not None:
                try:
                    self.registration.runs.recover()
                except Exception:  # noqa: BLE001 - recovery of earlier runs must not keep the service from starting
                    log.exception("recovering earlier agent runs failed")
            self._worker = threading.Thread(target=self._work, name="registration-worker", daemon=True)
            self._worker.start()

    def _work(self) -> None:
        while not self._worker_stop.wait(2.0):
            for name, service in (("registration", self.registration), ("architecture", self.architecture), ("execution", self.execution)):
                if service is None:
                    continue
                try:
                    service.tick()
                except Exception:  # noqa: BLE001 - the worker keeps running; each activity pauses itself on error
                    log.exception("%s worker tick failed", name)

    def stop(self) -> None:
        self._worker_stop.set()
        if self._worker is not None:
            self._worker.join(timeout=10)
        self.event_application.stop()

    def handle(
        self,
        method: str,
        path: str,
        headers: Mapping[str, str],
        body: bytes = b"",
    ) -> HTTPResponse | EventHTTPResponse:
        parsed = urlsplit(path)
        projection = self._projection_response(method, parsed, headers)
        if projection is not None:
            return projection
        if method == "GET" and parsed.path == "/api/v1/processes":
            return self._processes_response(headers)
        if method == "GET" and parsed.path.startswith("/api/v1/registrations/") and self.registration is not None:
            return self._registration_response(parsed.path.rsplit("/", 1)[1], headers)
        parts = parsed.path.split("/")
        if method == "GET" and len(parts) == 6 and parts[:4] == ["", "api", "v1", "projects"] and parts[5] == "architecture" and self.architecture is not None:
            return self._architecture_response(unquote(parts[4]), headers)
        if method == "GET" and len(parts) == 6 and parts[:4] == ["", "api", "v1", "projects"] and parts[5] == "execution" and self.execution is not None:
            return self._execution_response(unquote(parts[4]), headers)
        if parsed.path == "/api/v1/events":
            return self.event_application.handle(method, path, headers)
        return self.request_application.handle(method, path, headers, body)

    def _registration_response(self, activity_id: str, headers: Mapping[str, str]) -> HTTPResponse:
        content = {"Content-Type": "application/json; charset=utf-8"}
        try:
            self.authenticator.authenticate_read(headers.get("Authorization"))
        except HTTPRejection as error:
            return HTTPResponse(error.status_code, error.as_body(), {**content, **error.headers})
        view = self.registration.view(unquote(activity_id))  # type: ignore[union-attr]
        if view is None:
            return HTTPResponse(404, {"error": {"code": "registration_not_found", "message": "the registration was not found"}}, content)
        return HTTPResponse(200, {"data": view}, content)

    def _architecture_response(self, project_id: str, headers: Mapping[str, str]) -> HTTPResponse:
        content = {"Content-Type": "application/json; charset=utf-8"}
        try:
            self.authenticator.authenticate_read(headers.get("Authorization"))
        except HTTPRejection as error:
            return HTTPResponse(error.status_code, error.as_body(), {**content, **error.headers})
        with self.database.read_connection() as connection:
            known = connection.execute("SELECT 1 FROM service_projects WHERE project_id = ?", (project_id,)).fetchone()
            cursor = _event_cursor(connection)
        if known is None:
            return HTTPResponse(404, {"error": {"code": "project_not_found", "message": "the project was not found"}}, content)
        return HTTPResponse(200, {"data": self.architecture.project_view(project_id), "event_cursor": str(cursor)}, content)  # type: ignore[union-attr]

    def _execution_response(self, project_id: str, headers: Mapping[str, str]) -> HTTPResponse:
        content = {"Content-Type": "application/json; charset=utf-8"}
        try:
            self.authenticator.authenticate_read(headers.get("Authorization"))
        except HTTPRejection as error:
            return HTTPResponse(error.status_code, error.as_body(), {**content, **error.headers})
        with self.database.read_connection() as connection:
            known = connection.execute("SELECT 1 FROM service_projects WHERE project_id = ?", (project_id,)).fetchone()
            cursor = _event_cursor(connection)
        if known is None:
            return HTTPResponse(404, {"error": {"code": "project_not_found", "message": "the project was not found"}}, content)
        return HTTPResponse(200, {"data": self.execution.project_view(project_id), "configuration": self.execution.configuration_view(), "event_cursor": str(cursor)}, content)  # type: ignore[union-attr]

    def _processes_response(self, headers: Mapping[str, str]) -> HTTPResponse:
        content = {"Content-Type": "application/json; charset=utf-8"}
        try:
            self.authenticator.authenticate_read(headers.get("Authorization"))
        except HTTPRejection as error:
            return HTTPResponse(error.status_code, error.as_body(), {**content, **error.headers})
        if self.process_definitions is None:
            rows = [{"process": name, "state": "invalid", "error": {"code": "schema_bundles_unavailable", "message": "installed process schema bundles cannot be read"}} for name in PROCESS_TABLES]
        else:
            rows = self.process_definitions.report()
        return HTTPResponse(200, {"processes": rows}, content)

    def _projection_response(
        self,
        method: str,
        parsed: SplitResult,
        headers: Mapping[str, str],
    ) -> HTTPResponse | None:
        if method != "GET":
            return None
        parts = parsed.path.split("/")
        is_projection = parsed.path in {
            "/api/v1/workspace",
            "/api/v1/projects",
            "/api/v1/attention",
        } or (
            len(parts) == 6
            and parts[:4] == ["", "api", "v1", "projects"]
            and parts[5] in {"activities", "conversation"}
        ) or (
            len(parts) == 5
            and parts[:4] == ["", "api", "v1", "activities"]
        ) or (
            len(parts) == 8
            and parts[:4] == ["", "api", "v1", "projects"]
            and parts[5] == "activities"
            and parts[7] in {"questions", "findings", "actions"}
        )
        if not is_projection:
            return None
        try:
            if parsed.fragment:
                raise ProjectionError("invalid_query", "URL fragments are unsupported")
            self.authenticator.authenticate_read(headers.get("Authorization"))
            query = parse_qs(parsed.query, keep_blank_values=True)
            before = _single_query(query, "before")
            limit = _page_limit(query)
            if parsed.path == "/api/v1/workspace":
                _require_no_query(query)
                result = self.projections.workspace().as_dict()
            elif parsed.path == "/api/v1/projects":
                result = self.projections.projects(before=before, limit=limit).as_dict()
            elif parsed.path == "/api/v1/attention":
                result = self.projections.attention(before=before, limit=limit).as_dict()
            elif len(parts) == 6:
                project_id = unquote(parts[4])
                numeric_before = _numeric_cursor(before)
                if parts[5] == "activities":
                    result = self.projections.activities(
                        project_id, before=numeric_before, limit=limit
                    ).as_dict()
                else:
                    result = self.projections.conversation(
                        project_id, before=numeric_before, limit=limit
                    ).as_dict()
            elif len(parts) == 5:
                _require_no_query(query)
                result = self.projections.activity(unquote(parts[4])).as_dict()
            else:
                project_id = unquote(parts[4])
                activity_id = unquote(parts[6])
                resource = parts[7]
                reader = getattr(self.projections, resource)
                result = reader(
                    project_id,
                    activity_id,
                    before=before,
                    limit=limit,
                ).as_dict()
            return HTTPResponse(
                200,
                result,
                {"Content-Type": "application/json; charset=utf-8"},
            )
        except HTTPRejection as error:
            response_headers = {"Content-Type": "application/json; charset=utf-8"}
            response_headers.update(error.headers)
            return HTTPResponse(error.status_code, error.as_body(), response_headers)
        except ProjectionError as error:
            status = 404 if isinstance(error, ProjectionNotFound) else 400
            return HTTPResponse(
                status,
                {
                    "error": {
                        "code": error.code,
                        "message": str(error),
                        "fields": error.fields,
                    }
                },
                {"Content-Type": "application/json; charset=utf-8"},
            )


class InstalledServiceServer:
    """One loopback listener whose lifetime is owned by systemd, not the CLI."""

    def __init__(self, application: InstalledServiceApplication, host: str, port: int) -> None:
        self.application = application
        self._server = ThreadingHTTPServer((host, port), _handler(application))
        self._server.daemon_threads = True

    @property
    def address(self) -> tuple[str, int]:
        host, port = self._server.server_address[:2]
        return str(host), int(port)

    def serve_forever(self) -> None:
        self.application.start()
        try:
            self._server.serve_forever()
        finally:
            self.application.stop()
            self._server.server_close()

    def shutdown(self) -> None:
        self.application.stop()
        self._server.shutdown()


def _process_definitions(database: Database, config_path: Path | None) -> ProcessDefinitions | None:
    """Bind the shared process policy to the installed bundles and the live configuration file."""
    if config_path is None:
        return None
    try:
        policy = ProcessPolicyService(database, InstalledSchemaResources(), process_registry())
    except (ValueError, ProcessResourceError):
        return None

    def source() -> Mapping[str, object]:
        try:
            return load_settings(config_path).process_tables
        except ServiceConfigurationError as error:
            raise ValueError(str(error)) from error

    return ProcessDefinitions(policy, source)


def _registration(database: Database, activities: ActivityRepository, questions: QuestionService, definitions: ProcessDefinitions | None, settings: ServiceSettings):
    """Compose registration when the operator configured repositories, bindings and the registration process."""
    tables = settings.registration_tables
    if definitions is None or "repositories" not in tables or "repository_bindings" not in tables or "registration" not in settings.process_tables:
        return None
    from maestro.agents.inspectors import installed_resolvers
    from maestro.agents.routes import AgentRouteError
    from maestro.agents.supervisor import AgentSupervisor, FileSupervisorJournal, SystemdUserUnits
    from maestro.agents.workspaces import WorkspaceManager

    from .agent_runs import AgentRunService
    from .registration import RegistrationService
    from .registration_github import DestinationError, GitHubDestination, parse_repository_configuration
    from .reservations import ProjectReservations

    profiles, bindings = parse_repository_configuration(tables)
    home = Path(os.environ.get("MAESTRO_HOME") or Path.home())
    state_dir = Path(os.environ.get("MAESTRO_STATE_DIR") or settings.storage.path.parent / "registration")
    state_dir.mkdir(parents=True, exist_ok=True)
    credentials = Path(os.environ.get("MAESTRO_CREDENTIALS_DIR") or home / "credentials")
    runs = None
    role_choices: tuple[tuple[str, str], ...] = ()
    tools = tables.get("tools")
    if isinstance(tools, Mapping):
        try:
            route_resolver, profile_resolver = installed_resolvers(tools, home)
            supervisor = AgentSupervisor(FileSupervisorJournal(state_dir / "journal" / "journal.json"), SystemdUserUnits())
            runs = AgentRunService(
                database, supervisor, WorkspaceManager(settings.workspace_root),
                route_resolver=route_resolver, profile_resolver=profile_resolver,
                artifact_root=state_dir / "artifacts", clock=time.monotonic,
            )
            role_choices = tuple(
                (str(tool), str(model)) for tool, value in tools.items() if tool in {"codex", "claude_code"}
                for model in (value.get("allowed_model_ids") or [])
            )
        except (AgentRouteError, ValueError, OSError):
            log.exception("agent routes for registration could not be prepared")
    cache: dict[str, GitHubDestination] = {}

    def destination(profile) -> GitHubDestination:
        if profile.name not in cache:
            key = credentials / f"{profile.credential_profile}.pem"
            try:
                cache[profile.name] = GitHubDestination(profile, key.read_text(encoding="utf-8"))
            except OSError as error:
                raise DestinationError("credential_unavailable", "the repository credential for this profile cannot be read") from error
        return cache[profile.name]

    service = RegistrationService(
        database, records=activities, questions=questions, reservations=ProjectReservations(database), definitions=definitions,
        runs=runs, profiles=profiles, bindings=bindings, destination=destination, role_choices=role_choices,
        state_dir=state_dir, owner_id=settings.owner.owner_id if hasattr(settings.owner, "owner_id") else "owner",
    )
    for identity, recipient in service.recipients.items():
        questions.register_recipient(identity, recipient)
    return service


def _architecture(database: Database, registration, questions: QuestionService, definitions: ProcessDefinitions | None, settings: ServiceSettings):
    """Compose the architecture loop on registration's agent runs, repositories and reservations."""
    if registration is None or definitions is None or "architecture_loop" not in settings.process_tables:
        return None
    from .architecture import ArchitectureService

    schema = None
    try:
        schema = InstalledSchemaResources().resolve("architecture-loop@1").schema
    except ProcessResourceError:
        log.exception("the architecture-loop schema bundle is unavailable; saved records are not schema-checked")
    breakdown_schema = None
    try:
        breakdown_schema = InstalledSchemaResources().resolve("architecture-breakdown@1").schema
    except ProcessResourceError:
        log.exception("the architecture-breakdown schema bundle is unavailable; saved breakdown records are not schema-checked")
    execution = settings.registration_tables.get("execution")
    bindings = ((execution.get("qa") or {}).get("project_bindings") or {}) if isinstance(execution, Mapping) and isinstance(execution.get("qa"), Mapping) else {}
    service = ArchitectureService(
        database, records=registration.records, questions=questions, reservations=registration.reservations, definitions=definitions,
        runs=registration.runs, profiles=registration.profiles, destination=registration._destination, state_dir=registration.state_dir / "architecture",
        owner_id=registration.owner_id, schema=schema, breakdown_schema=breakdown_schema, qa_bindings=lambda project_id: bindings.get(project_id),
    )
    (service.state_dir).mkdir(parents=True, exist_ok=True)
    architecture_receive, registration_receive = service.receive_answer, registration.receive_answer

    def deliver(answer) -> None:
        (architecture_receive if service.owns(answer.activity_id) else registration_receive)(answer)

    for identity in ("owner", "project_architect"):
        questions.register_recipient(identity, deliver)
    return service


def _execution(database: Database, registration, architecture, questions: QuestionService, settings: ServiceSettings):
    """Compose Execution on registration's agent runs, repositories and reservations."""
    if registration is None or architecture is None or "execution" not in settings.registration_tables:
        return None
    from .execution import ExecutionService
    from .resources import InstalledSchemaResources

    try:
        resources = InstalledSchemaResources()
    except Exception:  # noqa: BLE001 - a missing bundle registry blocks new Execution work; status stays readable
        log.exception("the execution schema bundle registry is unavailable")
        resources = None
    service = ExecutionService(
        database, records=registration.records, questions=questions, reservations=registration.reservations, runs=registration.runs,
        profiles=registration.profiles, destination=registration._destination, state_dir=registration.state_dir / "execution",
        owner_id=registration.owner_id, config_source=lambda: settings.registration_tables.get("execution"), resources=resources,
    )
    service.state_dir.mkdir(parents=True, exist_ok=True)
    registration_receive = registration.receive_answer

    def deliver(answer) -> None:
        if service.owns(answer.activity_id):
            service.receive_answer(answer)
        elif architecture.owns(answer.activity_id):
            architecture.receive_answer(answer)
        else:
            registration_receive(answer)

    for identity in ("owner", "project_architect"):
        questions.register_recipient(identity, deliver)
    return service


def build_application(settings: ServiceSettings) -> InstalledServiceApplication:
    """Build and initialize the real installed application boundary."""
    settings.storage.validate_host_path()
    _validate_workspace_root(settings.workspace_root)
    application = InstalledServiceApplication(settings)
    details = os.lstat(settings.storage.path)
    if not stat.S_ISREG(details.st_mode):
        raise ServiceConfigurationError("configured storage is not a regular file")
    os.chmod(settings.storage.path, 0o600)
    return application


def run(settings: ServiceSettings) -> None:
    """Run until systemd sends SIGTERM or the process fails."""
    application = build_application(settings)
    server = InstalledServiceServer(application, settings.host, settings.port)
    stopped = threading.Event()

    def stop(_signal_number: int, _frame: object) -> None:
        if stopped.is_set():
            return
        stopped.set()
        threading.Thread(target=server.shutdown, daemon=True).start()

    previous = {
        name: signal.signal(name, stop) for name in (signal.SIGTERM, signal.SIGINT)
    }
    try:
        server.serve_forever()
    finally:
        for name, handler in previous.items():
            signal.signal(name, handler)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the persistent Maestro service")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    parser.add_argument(
        "--check-ready",
        action="store_true",
        help="validate configuration and initialize storage without listening",
    )
    arguments = parser.parse_args(argv)
    try:
        settings = load_settings(arguments.config)
        if arguments.check_ready:
            build_application(settings)
            print("Maestro service configuration and storage are ready")
            return 0
        run(settings)
        return 0
    except (OSError, RuntimeError, ValueError, sqlite3.Error) as error:
        print(f"Maestro service is not ready: {error}", file=sys.stderr)
        return 1


def _single_query(query: Mapping[str, list[str]], name: str) -> str | None:
    unknown = set(query) - {"before", "limit"}
    if unknown:
        raise ProjectionError(
            "invalid_query", f"unsupported query field: {sorted(unknown)[0]}"
        )
    values = query.get(name)
    if values is None:
        return None
    if len(values) != 1:
        raise ProjectionError("invalid_query", f"{name} must be supplied once")
    return values[0]


def _page_limit(query: Mapping[str, list[str]]) -> int:
    value = _single_query(query, "limit")
    if value is None:
        return 50
    try:
        return int(value)
    except ValueError as error:
        raise ProjectionError("invalid_query", "limit must be an integer") from error


def _numeric_cursor(value: str | None) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except ValueError as error:
        raise ProjectionError(
            "invalid_cursor", "before cursor must be a positive integer"
        ) from error


def _require_no_query(query: Mapping[str, list[str]]) -> None:
    if query:
        raise ProjectionError("invalid_query", "this route does not accept a query")


def _handler(application: InstalledServiceApplication) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            self._dispatch("GET")

        def do_POST(self) -> None:
            self._dispatch("POST")

        def _dispatch(self, method: str) -> None:
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                length = MAX_REQUEST_BYTES + 1
            body = (
                self.rfile.read(length)
                if 0 <= length <= MAX_REQUEST_BYTES
                else b"x" * (MAX_REQUEST_BYTES + 1)
            )
            response = application.handle(method, self.path, self.headers, body)
            self.send_response(response.status_code)
            for name, value in response.headers.items():
                self.send_header(name, value)
            if isinstance(response.body, Mapping):
                encoded = json.dumps(
                    response.body,
                    sort_keys=True,
                    separators=(",", ":"),
                    ensure_ascii=False,
                ).encode("utf-8")
                self.send_header("Content-Length", str(len(encoded)))
                self.end_headers()
                self.wfile.write(encoded)
            else:
                self.end_headers()
                try:
                    for chunk in response.body:
                        self.wfile.write(chunk)
                        self.wfile.flush()
                except (BrokenPipeError, ConnectionResetError, OSError):
                    return
                finally:
                    close = getattr(response.body, "close", None)
                    if close is not None:
                        close()

        def log_message(self, _format: str, *_args: object) -> None:
            return

    return Handler


def _table(value: object, name: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ServiceConfigurationError(f"{name} settings must be a table")
    return value


def _account_name(value: object) -> bool:
    if not isinstance(value, str) or not value or len(value) > 32:
        return False
    return value[0].islower() and all(
        character.islower() or character.isdigit() or character in "_-"
        for character in value
    )


def _reject_linked_components(path: Path) -> None:
    current = Path(path.anchor)
    for component in path.parts[1:]:
        current /= component
        try:
            details = os.lstat(current)
        except FileNotFoundError:
            return
        if stat.S_ISLNK(details.st_mode):
            raise ServiceConfigurationError(
                f"service configuration path contains a symbolic link: {current}"
            )


def _validate_workspace_root(path: Path) -> None:
    _reject_linked_components(path)
    if not path.is_dir():
        raise ServiceConfigurationError(
            f"workspace_root does not exist or is not a directory: {path}"
        )


if __name__ == "__main__":
    raise SystemExit(main())
