"""A minimal, real GitHub App API client (M3 A1 dependency).

Wraps GitHub App JWT auth, installation-token exchange, and the two
REST calls real project discovery needs: repository metadata and file
content. This module never touches a stored secret directly — callers
resolve the App's private key through a secret provider (see
:mod:`maestro.secrets`) and pass the PEM text in explicitly.
"""

from __future__ import annotations

import base64
import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


class GitHubClientError(RuntimeError):
    """Raised when a GitHub API call fails or returns an unexpected shape.

    ``status`` carries the HTTP status code when the failure came from
    an HTTP response (``None`` for a shape/decoding failure with no
    response at all).
    """

    def __init__(self, message: str, *, status: int | None = None) -> None:
        super().__init__(message)
        self.status = status


@dataclass(frozen=True)
class GitHubAppCredentials:
    """The three real, non-secret identifiers plus the one real secret
    a GitHub App needs to authenticate — the secret is held here only
    transiently, by the caller, never persisted by this module."""

    app_id: str
    installation_id: str
    private_key_pem: str


def fetch_installation_token(credentials: GitHubAppCredentials, *, now: int | None = None) -> str:
    """Exchange the App's JWT for a real, short-lived installation token."""
    issued_at = now if now is not None else int(time.time())
    jwt_token = _app_jwt(credentials, issued_at)
    request = urllib.request.Request(
        f"https://api.github.com/app/installations/{credentials.installation_id}/access_tokens",
        method="POST",
        headers=_jwt_headers(jwt_token),
    )
    data = _request_json(request)
    token = data.get("token")
    if not isinstance(token, str) or not token:
        raise GitHubClientError("installation token response missing a real 'token' field")
    return token


def fetch_repository_metadata(installation_token: str, owner: str, repo: str) -> dict[str, Any]:
    """Return the real repository metadata GitHub reports for owner/repo."""
    request = urllib.request.Request(
        f"https://api.github.com/repos/{owner}/{repo}",
        headers=_token_headers(installation_token),
    )
    return _request_json(request)


def fetch_file_content(
    installation_token: str, owner: str, repo: str, path: str, ref: str
) -> str | None:
    """Return the real, decoded UTF-8 text of one repository file at
    ``ref``, or ``None`` if that exact path does not exist there.

    Never silently truncates or partially decodes — any response shape
    other than a base64-encoded single file is a real error, not a
    best-effort guess.
    """
    request = urllib.request.Request(
        f"https://api.github.com/repos/{owner}/{repo}/contents/{path}?ref={ref}",
        headers=_token_headers(installation_token),
    )
    try:
        data = _request_json(request)
    except GitHubClientError as error:
        if error.status == 404:
            return None
        raise
    if not isinstance(data, dict) or data.get("encoding") != "base64" or "content" not in data:
        raise GitHubClientError(f"unexpected content response shape for {path!r} at {ref!r}")
    return base64.b64decode(data["content"]).decode("utf-8")


def _app_jwt(credentials: GitHubAppCredentials, issued_at: int) -> str:
    import jwt  # local import: only real-discovery callers need PyJWT

    payload = {"iat": issued_at - 60, "exp": issued_at + 300, "iss": credentials.app_id}
    return jwt.encode(payload, credentials.private_key_pem, algorithm="RS256")


def _jwt_headers(jwt_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {jwt_token}", "Accept": "application/vnd.github+json"}


def _token_headers(installation_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {installation_token}", "Accept": "application/vnd.github+json"}


def _request_json(request: urllib.request.Request) -> dict[str, Any]:
    try:
        with urllib.request.urlopen(request) as response:
            return json.loads(response.read())
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", "replace")
        raise GitHubClientError(
            f"GitHub API {error.code} for {request.full_url}: {body}", status=error.code
        ) from error
