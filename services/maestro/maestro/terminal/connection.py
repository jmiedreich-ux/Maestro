"""Protected connection from the local terminal to the Maestro service."""

from __future__ import annotations

import json
import os
import stat
import threading
import tomllib
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable, Iterator, Mapping
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import BinaryIO

from maestro.service.authentication import (
    CredentialProtectionError,
    owner_authorization_header,
)


DEFAULT_SERVICE_URL = "http://localhost:8787"
CONNECT_TIMEOUT_SECONDS = 5
REQUEST_TIMEOUT_SECONDS = 15
EVENT_SILENCE_TIMEOUT_SECONDS = 45
RECONNECT_DELAYS_SECONDS = (1, 2, 4, 8, 16, 30)
_CONFIG_KEYS = frozenset({"service_url", "owner_credential_file"})
_LOOPBACK_HOSTS = frozenset({"localhost", "127.0.0.1", "::1"})


class TerminalConnectionError(RuntimeError):
    """Base class for safe, user-facing terminal connection failures."""


class ConfigurationError(TerminalConnectionError):
    """The terminal configuration cannot be used."""


class CredentialError(TerminalConnectionError):
    """The Owner credential is missing or unsafe to use."""


class ServiceError(TerminalConnectionError):
    """The service returned an error response."""

    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code


class ConnectionUnavailable(TerminalConnectionError):
    """The selected service address could not be reached."""


@dataclass(frozen=True)
class ConnectionConfiguration:
    """Effective paths and address, including any safe fallback explanation."""

    service_url: str
    credential_file: Path
    config_file: Path
    fallback_reason: str | None = None

    @property
    def used_fallback(self) -> bool:
        return self.fallback_reason is not None


class ConnectionState(str, Enum):
    CONNECTING = "connecting"
    CONNECTED = "connected"
    UNAVAILABLE = "unavailable"
    DISCONNECTED = "disconnected"
    SETUP_ERROR = "setup_error"


@dataclass(frozen=True)
class ConnectionStatus:
    state: ConnectionState
    service_url: str
    message: str
    retry_in_seconds: int | None = None
    clear_service_context: bool = False


@dataclass(frozen=True)
class SSEEvent:
    event_id: str | None
    event: str | None
    data: object


class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001
        return None


def load_configuration(
    *,
    environ: Mapping[str, str] | None = None,
    home: Path | None = None,
) -> ConnectionConfiguration:
    """Load CLI TOML, falling back only when the configuration is unusable."""
    environment = os.environ if environ is None else environ
    config_root = _configuration_root(environment, home)
    config_file = config_root / "maestro" / "cli.toml"
    default_credential = config_root / "maestro" / "owner.token"
    try:
        raw = config_file.read_bytes()
        value = tomllib.loads(raw.decode("utf-8"))
        if not isinstance(value, dict):
            raise ConfigurationError("configuration must be a TOML table")
        unknown = set(value) - _CONFIG_KEYS
        if unknown:
            raise ConfigurationError(
                f"unsupported setting(s): {', '.join(sorted(unknown))}"
            )
        service_url = value.get("service_url", DEFAULT_SERVICE_URL)
        if not isinstance(service_url, str):
            raise ConfigurationError("service_url must be text")
        service_url = validate_service_url(service_url)
        credential_value = value.get("owner_credential_file")
        if credential_value is None:
            credential_file = default_credential
        elif not isinstance(credential_value, str):
            raise ConfigurationError("owner_credential_file must be text")
        else:
            credential_file = Path(credential_value)
            if not credential_file.is_absolute():
                raise ConfigurationError("owner_credential_file must be absolute")
        return ConnectionConfiguration(
            service_url=service_url,
            credential_file=credential_file,
            config_file=config_file,
        )
    except FileNotFoundError:
        reason = f"configuration not found at {config_file}"
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError, ConfigurationError) as error:
        reason = f"configuration unavailable: {error}"
    return ConnectionConfiguration(
        service_url=DEFAULT_SERVICE_URL,
        credential_file=default_credential,
        config_file=config_file,
        fallback_reason=reason,
    )


def validate_service_url(value: str) -> str:
    """Return the canonical supported loopback service origin."""
    try:
        parsed = urllib.parse.urlsplit(value)
        port = parsed.port
    except (TypeError, ValueError) as error:
        raise ConfigurationError("service_url is not a valid URL") from error
    if (
        parsed.scheme != "http"
        or parsed.hostname not in _LOOPBACK_HOSTS
        or port is None
        or not 1 <= port <= 65535
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
        or parsed.path not in ("", "/")
    ):
        raise ConfigurationError(
            "service_url must be an HTTP loopback address with an explicit port"
        )
    host = f"[{parsed.hostname}]" if parsed.hostname == "::1" else parsed.hostname
    return f"http://{host}:{port}"


def load_owner_credential(path: Path) -> str:
    """Read a protected installation credential without retaining file contents."""
    try:
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
        try:
            details = os.fstat(descriptor)
            if not stat.S_ISREG(details.st_mode):
                raise CredentialError("Owner credential path is not a regular file")
            if stat.S_IMODE(details.st_mode) != 0o600:
                raise CredentialError("Owner credential file must have mode 0600")
            if hasattr(os, "getuid") and details.st_uid != os.getuid():
                raise CredentialError(
                    "Owner credential file must be owned by the operator"
                )
            token_bytes = os.read(descriptor, 65)
        finally:
            os.close(descriptor)
    except CredentialError:
        raise
    except OSError as error:
        raise CredentialError(
            f"cannot read Owner credential: {type(error).__name__}"
        ) from error
    try:
        token = token_bytes.decode("ascii")
    except UnicodeError as error:
        raise CredentialError("Owner credential has an invalid format") from error
    if len(token) != 64 or any(character not in "0123456789abcdef" for character in token):
        raise CredentialError("Owner credential has an invalid format")
    return token


class ServiceClient:
    """The sole authenticated HTTP/SSE client used by terminal consumers."""

    def __init__(
        self,
        configuration: ConnectionConfiguration,
        *,
        opener: urllib.request.OpenerDirector | None = None,
    ) -> None:
        self.configuration = configuration
        self._opener = opener or urllib.request.build_opener(_NoRedirectHandler())

    def workspace(self, *, connect_timeout: bool = False) -> Mapping[str, object]:
        timeout = CONNECT_TIMEOUT_SECONDS if connect_timeout else REQUEST_TIMEOUT_SECONDS
        return self.get_json("/workspace", timeout=timeout)

    def receipt(self, request_id: str) -> Mapping[str, object]:
        if not request_id or "/" in request_id:
            raise ValueError("request_id must be a nonempty path segment")
        encoded = urllib.parse.quote(request_id, safe="")
        return self.get_json(f"/requests/{encoded}")

    def submit(self, envelope: Mapping[str, object]) -> Mapping[str, object]:
        return self.post_json("/requests", envelope)

    def get_json(
        self, path: str, *, timeout: int = REQUEST_TIMEOUT_SECONDS
    ) -> Mapping[str, object]:
        return self._json_request("GET", path, None, timeout)

    def post_json(
        self,
        path: str,
        value: Mapping[str, object],
        *,
        timeout: int = REQUEST_TIMEOUT_SECONDS,
    ) -> Mapping[str, object]:
        body = json.dumps(value, separators=(",", ":"), ensure_ascii=False).encode(
            "utf-8"
        )
        return self._json_request("POST", path, body, timeout)

    def events(self, last_event_id: str | None = None) -> Iterator[SSEEvent]:
        headers = {"Accept": "text/event-stream"}
        if last_event_id is not None:
            headers["Last-Event-ID"] = last_event_id
        response = self._open(
            "GET", "/events", None, EVENT_SILENCE_TIMEOUT_SECONDS, headers
        )
        return _event_iterator(response, last_event_id=last_event_id)

    def _json_request(
        self, method: str, path: str, body: bytes | None, timeout: int
    ) -> Mapping[str, object]:
        response = self._open(method, path, body, timeout, {"Accept": "application/json"})
        with response:
            try:
                value = json.loads(response.read().decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as error:
                raise ServiceError(
                    502, "invalid_response", "service returned invalid JSON"
                ) from error
        if not isinstance(value, dict):
            raise ServiceError(
                502, "invalid_response", "service returned a non-object response"
            )
        return value

    def _open(
        self,
        method: str,
        path: str,
        body: bytes | None,
        timeout: int,
        extra_headers: Mapping[str, str],
    ) -> BinaryIO:
        if not path.startswith("/") or path.startswith("//"):
            raise ValueError("service path must be absolute within /api/v1")
        destination = f"{self.configuration.service_url}/api/v1{path}"
        token = load_owner_credential(self.configuration.credential_file)
        try:
            protected = owner_authorization_header(
                token,
                destination=destination,
                configured_service_url=self.configuration.service_url,
            )
        except CredentialProtectionError as error:
            raise CredentialError(str(error)) from error
        headers = dict(extra_headers)
        headers.update(protected)
        if body is not None:
            headers["Content-Type"] = "application/json"
        request = urllib.request.Request(
            destination, data=body, method=method, headers=headers
        )
        try:
            return self._opener.open(request, timeout=timeout)
        except urllib.error.HTTPError as error:
            message, code = _http_error(error)
            raise ServiceError(error.code, code, message) from error
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            reason = getattr(error, "reason", error)
            raise ConnectionUnavailable(
                f"cannot reach {self.configuration.service_url}: {reason}"
            ) from error


class TerminalConnection:
    """Own configuration reload and deterministic reconnect state."""

    def __init__(
        self,
        *,
        environ: Mapping[str, str] | None = None,
        home: Path | None = None,
        client_factory: Callable[[ConnectionConfiguration], ServiceClient] = ServiceClient,
    ) -> None:
        self._environ = environ
        self._home = home
        self._client_factory = client_factory
        self.configuration = load_configuration(environ=environ, home=home)
        self.client = client_factory(self.configuration)
        self.status = ConnectionStatus(
            ConnectionState.CONNECTING,
            self.configuration.service_url,
            "not connected",
        )
        self._listeners: list[Callable[[ConnectionStatus], None]] = []
        self._was_connected = False
        self._retry_index: int | None = None
        self._attempt_lock = threading.RLock()

    def subscribe(self, listener: Callable[[ConnectionStatus], None]) -> None:
        self._listeners.append(listener)

    def credential_status(self) -> str:
        try:
            load_owner_credential(self.configuration.credential_file)
        except CredentialError as error:
            return f"setup error: {error}"
        return "Owner credential ready"

    def connect(self) -> Mapping[str, object]:
        with self._attempt_lock:
            self._publish(ConnectionState.CONNECTING, "contacting service")
            try:
                workspace = self.client.workspace(connect_timeout=True)
            except CredentialError as error:
                self._retry_index = None
                self._publish(ConnectionState.SETUP_ERROR, str(error))
                raise
            except TerminalConnectionError as error:
                self._retry_index = None
                self._publish(ConnectionState.UNAVAILABLE, str(error))
                raise
            self._was_connected = True
            self._retry_index = None
            self._publish(ConnectionState.CONNECTED, "connected")
            return workspace

    def disconnected(self, reason: str) -> int | None:
        """Record an established connection loss and schedule the bounded retry."""
        with self._attempt_lock:
            if not self._was_connected:
                self._retry_index = None
                self._publish(ConnectionState.UNAVAILABLE, reason)
                return None
            self._retry_index = 0 if self._retry_index is None else self._retry_index
            delay = RECONNECT_DELAYS_SECONDS[self._retry_index]
            self._publish(ConnectionState.DISCONNECTED, reason, retry_in_seconds=delay)
            return delay

    def automatic_retry(self) -> Mapping[str, object]:
        """Run one scheduled retry, advancing backoff only after another failure."""
        with self._attempt_lock:
            if self._retry_index is None:
                raise RuntimeError("no automatic retry is scheduled")
            attempted_index = self._retry_index
            try:
                return self.connect()
            except TerminalConnectionError:
                self._retry_index = min(
                    attempted_index + 1, len(RECONNECT_DELAYS_SECONDS) - 1
                )
                delay = RECONNECT_DELAYS_SECONDS[self._retry_index]
                self._publish(
                    ConnectionState.DISCONNECTED,
                    self.status.message,
                    retry_in_seconds=delay,
                )
                raise

    def reload_configuration(self) -> bool:
        """Reload settings and notify consumers when service context must clear."""
        with self._attempt_lock:
            previous_url = self.configuration.service_url
            self.configuration = load_configuration(
                environ=self._environ, home=self._home
            )
            changed = self.configuration.service_url != previous_url
            self.client = self._client_factory(self.configuration)
            if changed:
                self._publish(
                    ConnectionState.CONNECTING,
                    "service address changed; clearing prior service context",
                    clear_service_context=True,
                )
            return changed

    def retry_now(self) -> Mapping[str, object]:
        """Cancel scheduled retry, reload configuration and connect immediately."""
        with self._attempt_lock:
            self._retry_index = None
            self.reload_configuration()
            return self.connect()

    def _publish(
        self,
        state: ConnectionState,
        message: str,
        *,
        retry_in_seconds: int | None = None,
        clear_service_context: bool = False,
    ) -> None:
        self.status = ConnectionStatus(
            state,
            self.configuration.service_url,
            message,
            retry_in_seconds,
            clear_service_context,
        )
        for listener in tuple(self._listeners):
            listener(self.status)


def _configuration_root(environment: Mapping[str, str], home: Path | None) -> Path:
    configured = environment.get("XDG_CONFIG_HOME")
    if configured:
        return Path(configured).expanduser()
    return (Path.home() if home is None else home) / ".config"


def _http_error(error: urllib.error.HTTPError) -> tuple[str, str]:
    message = f"service request failed with HTTP {error.code}"
    code = "http_error"
    try:
        value = json.loads(error.read().decode("utf-8"))
        detail = value.get("error") if isinstance(value, dict) else None
        if isinstance(detail, dict):
            if isinstance(detail.get("message"), str):
                message = detail["message"]
            if isinstance(detail.get("code"), str):
                code = detail["code"]
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        pass
    return message, code


def _event_iterator(
    response: BinaryIO, *, last_event_id: str | None
) -> Iterator[SSEEvent]:
    def generate() -> Iterator[SSEEvent]:
        event_id: str | None = None
        event_type: str | None = None
        data_lines: list[str] = []
        seen_event_ids = set() if last_event_id is None else {last_event_id}
        with response:
            while True:
                try:
                    raw = response.readline()
                except (TimeoutError, OSError) as error:
                    raise ConnectionUnavailable(
                        f"event stream was interrupted: {error}"
                    ) from error
                if not raw:
                    if data_lines:
                        event = _make_event(event_id, event_type, data_lines)
                        if event.event_id not in seen_event_ids:
                            yield event
                    return
                try:
                    line = raw.decode("utf-8").rstrip("\r\n")
                except UnicodeDecodeError as error:
                    raise ServiceError(
                        502, "invalid_event", "event stream is not UTF-8"
                    ) from error
                if not line:
                    if data_lines:
                        event = _make_event(event_id, event_type, data_lines)
                        if event.event_id not in seen_event_ids:
                            yield event
                            if event.event_id is not None:
                                seen_event_ids.add(event.event_id)
                    event_id, event_type, data_lines = None, None, []
                    continue
                if line.startswith(":"):
                    continue
                field, separator, value = line.partition(":")
                if separator and value.startswith(" "):
                    value = value[1:]
                if field == "id":
                    event_id = value
                elif field == "event":
                    event_type = value
                elif field == "data":
                    data_lines.append(value)

    return generate()


def _make_event(
    event_id: str | None, event_type: str | None, data_lines: list[str]
) -> SSEEvent:
    text = "\n".join(data_lines)
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        data = text
    return SSEEvent(event_id=event_id, event=event_type, data=data)
