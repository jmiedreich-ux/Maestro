"""Small authenticated HTTP adapter for durable request submission."""

from __future__ import annotations

import json
import threading
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Mapping
from urllib.parse import unquote, urlsplit

from .authentication import HTTPRejection
from .requests import RequestRejection, RequestService


MAX_REQUEST_BYTES = 1_048_576


@dataclass(frozen=True)
class HTTPResponse:
    status_code: int
    body: Mapping[str, object]
    headers: Mapping[str, str]


class RequestHTTPApplication:
    """Transport-neutral dispatch for the two `/api/v1` request routes."""

    def __init__(self, service: RequestService) -> None:
        self._service = service

    def handle(
        self,
        method: str,
        path: str,
        headers: Mapping[str, str],
        body: bytes = b"",
    ) -> HTTPResponse:
        try:
            authorization = headers.get("Authorization")
            parsed = urlsplit(path)
            if parsed.query or parsed.fragment:
                raise RequestRejection(404, "not_found", "the API route was not found")
            if method == "POST" and parsed.path == "/api/v1/requests":
                self._service.authenticate_write(authorization)
                request_body = _decode_body(body, headers.get("Content-Type"))
                receipt = self._service.submit(authorization, request_body)
                status = 202 if receipt.status == "accepted" else 200
                return _response(status, {"receipt": receipt.as_dict()})
            prefix = "/api/v1/requests/"
            if method == "GET" and parsed.path.startswith(prefix):
                encoded_id = parsed.path[len(prefix) :]
                if not encoded_id or "/" in encoded_id:
                    raise RequestRejection(
                        404, "not_found", "the API route was not found"
                    )
                self._service.authenticate_read(authorization)
                receipt = self._service.lookup(authorization, unquote(encoded_id))
                return _response(200, {"receipt": receipt.as_dict()})
            raise RequestRejection(404, "not_found", "the API route was not found")
        except HTTPRejection as error:
            return _response(error.status_code, error.as_body(), error.headers)


class RequestHTTPServer:
    """A stoppable loopback HTTP server used by the installed service wrapper."""

    def __init__(
        self,
        application: RequestHTTPApplication,
        host: str = "127.0.0.1",
        port: int = 0,
    ) -> None:
        handler = _handler_for(application)
        self._httpd = ThreadingHTTPServer((host, port), handler)
        self._thread: threading.Thread | None = None

    @property
    def address(self) -> tuple[str, int]:
        host, port = self._httpd.server_address[:2]
        return str(host), int(port)

    def start(self) -> None:
        if self._thread is not None:
            raise RuntimeError("request HTTP server is already running")
        self._thread = threading.Thread(target=self._httpd.serve_forever, daemon=True)
        self._thread.start()

    def close(self) -> None:
        if self._thread is not None:
            self._httpd.shutdown()
            self._thread.join()
            self._thread = None
        self._httpd.server_close()

    def __enter__(self) -> "RequestHTTPServer":
        self.start()
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()


def _decode_body(body: bytes, content_type: str | None) -> Mapping[str, object]:
    media_type = None if content_type is None else content_type.split(";", 1)[0]
    if media_type is None or media_type.strip().casefold() != "application/json":
        raise RequestRejection(
            400, "invalid_request", "Content-Type must be application/json"
        )
    if len(body) > MAX_REQUEST_BYTES:
        raise RequestRejection(400, "invalid_request", "request body is too large")
    try:
        value = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise RequestRejection(
            400,
            "invalid_request",
            "request body is not valid UTF-8 JSON",
        ) from error
    if not isinstance(value, dict):
        raise RequestRejection(
            400, "invalid_request", "request body must be a JSON object"
        )
    return value


def _response(
    status_code: int,
    body: Mapping[str, object],
    extra_headers: Mapping[str, str] | None = None,
) -> HTTPResponse:
    headers = {"Content-Type": "application/json; charset=utf-8"}
    if extra_headers is not None:
        headers.update(extra_headers)
    return HTTPResponse(status_code=status_code, body=dict(body), headers=headers)


def _handler_for(application: RequestHTTPApplication) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:
            self._dispatch("POST")

        def do_GET(self) -> None:
            self._dispatch("GET")

        def _dispatch(self, method: str) -> None:
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                length = MAX_REQUEST_BYTES + 1
            if 0 <= length <= MAX_REQUEST_BYTES:
                body = self.rfile.read(length)
            else:
                body = b"x" * (MAX_REQUEST_BYTES + 1)
            response = application.handle(method, self.path, self.headers, body)
            encoded = json.dumps(
                response.body,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
            ).encode("utf-8")
            self.send_response(response.status_code)
            for name, value in response.headers.items():
                self.send_header(name, value)
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

        def log_message(self, _format: str, *_args: object) -> None:
            return

    return Handler
