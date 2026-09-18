"""Installed Maestro service entry point and startup validation."""

from __future__ import annotations

import argparse
import json
import os
import signal
import sqlite3
import stat
import sys
import threading
import tomllib
from dataclasses import dataclass
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
from .projections import ProjectionError, ProjectionNotFound, ProjectionReader
from .questions import QuestionHTTPApplication, QuestionRequestService, QuestionService
from .registry import OperationRegistry
from .requests import RequestService


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
    return ServiceSettings(
        storage=storage,
        owner=owner,
        host=host,
        port=port,
        agent_user=agent_user,
        workspace_root=Path(workspace_root),
    )


class InstalledServiceApplication:
    """Compose authenticated reads, durable requests, and the event stream."""

    def __init__(self, settings: ServiceSettings) -> None:
        self.database = Database(settings.storage)
        # Register the currently installed core domain before final initialization.
        self.activities = ActivityRepository(self.database)
        self.authenticator = OwnerAuthenticator(settings.owner)
        self.questions = QuestionService(self.database)
        base_requests = RequestService(
            self.database,
            self.authenticator,
            OperationRegistry(self.questions.operation_handlers),
        )
        self.requests = QuestionRequestService(base_requests, self.questions)
        self.projections = ProjectionReader(self.database)
        self.request_application = QuestionHTTPApplication(
            self.requests, self.questions
        )
        self.event_application = EventStreamHTTPApplication(
            EventStreamService(self.database, self.authenticator)
        )

    def start(self) -> None:
        self.event_application.start()

    def stop(self) -> None:
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
        if parsed.path == "/api/v1/events":
            return self.event_application.handle(method, path, headers)
        return self.request_application.handle(method, path, headers, body)

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
