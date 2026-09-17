"""Authentication and credential-protection boundaries for the local Owner."""

from __future__ import annotations

import hashlib
import hmac
import re
import threading
from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping
from urllib.parse import SplitResult, urlsplit

from maestro.foundation import canonical_identifier


OWNER_AUTHORITY = "Owner"
_TOKEN_PATTERN = re.compile(r"[0-9a-f]{64}\Z")
_LOOPBACK_HOSTS = frozenset({"127.0.0.1", "::1", "localhost"})


class AuthenticationConfigurationError(ValueError):
    """Raised when installed Owner authentication settings are invalid."""


class CredentialProtectionError(ValueError):
    """Raised before an Owner credential could be sent to an unsafe destination."""


class HTTPRejection(Exception):
    """A safe, transport-neutral HTTP error produced before handler dispatch."""

    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message

    @property
    def headers(self) -> Mapping[str, str]:
        if self.status_code == 401:
            return MappingProxyType({"WWW-Authenticate": "Bearer"})
        return MappingProxyType({})

    def as_body(self) -> dict[str, object]:
        return {"error": {"code": self.code, "message": self.message}}


@dataclass(frozen=True)
class OwnerAuthenticationSettings:
    """The non-secret Owner identity and token digest loaded by the service."""

    owner_id: str
    token_sha256: str

    def __post_init__(self) -> None:
        try:
            canonical_identifier(self.owner_id, "owner.id")
        except ValueError as error:
            raise AuthenticationConfigurationError(str(error)) from error
        if (
            not isinstance(self.token_sha256, str)
            or _TOKEN_PATTERN.fullmatch(self.token_sha256) is None
        ):
            raise AuthenticationConfigurationError(
                "owner.token_sha256 must be a lowercase SHA-256 digest"
            )

    @classmethod
    def from_mapping(cls, value: Mapping[str, object]) -> "OwnerAuthenticationSettings":
        """Build settings from the closed ``owner`` configuration table."""
        if not isinstance(value, Mapping):
            raise AuthenticationConfigurationError("owner settings must be a table")
        unknown = set(value) - {"id", "token_sha256"}
        if unknown:
            raise AuthenticationConfigurationError(
                f"unsupported owner setting(s): {', '.join(sorted(unknown))}"
            )
        owner_id = value.get("id")
        token_sha256 = value.get("token_sha256")
        if not isinstance(owner_id, str) or not isinstance(token_sha256, str):
            raise AuthenticationConfigurationError(
                "owner.id and owner.token_sha256 must be text"
            )
        return cls(owner_id=owner_id, token_sha256=token_sha256)


@dataclass(frozen=True)
class VerifiedActor:
    """Request authority derived from a credential, with no secret retained."""

    actor_id: str
    authority: str = OWNER_AUTHORITY


class OwnerAuthenticator:
    """Authenticate requests against the currently installed Owner digest."""

    def __init__(self, settings: OwnerAuthenticationSettings) -> None:
        if not isinstance(settings, OwnerAuthenticationSettings):
            raise AuthenticationConfigurationError(
                "authenticator requires validated Owner authentication settings"
            )
        self._lock = threading.RLock()
        self._settings = settings

    def replace_settings(self, settings: OwnerAuthenticationSettings) -> None:
        """Atomically activate a validated replacement identity and digest."""
        if not isinstance(settings, OwnerAuthenticationSettings):
            raise AuthenticationConfigurationError(
                "replacement requires validated Owner authentication settings"
            )
        with self._lock:
            self._settings = settings

    def authenticate(
        self,
        authorization: str | None,
        *,
        required_authority: str = OWNER_AUTHORITY,
    ) -> VerifiedActor:
        """Return the configured Owner or raise a typed 401/403 rejection."""
        token = _bearer_token(authorization)
        supplied_digest = hashlib.sha256(token.encode("ascii")).hexdigest()
        with self._lock:
            settings = self._settings
            if not hmac.compare_digest(supplied_digest, settings.token_sha256):
                raise _unauthorized()
            actor = VerifiedActor(actor_id=settings.owner_id)
        if required_authority != actor.authority:
            raise HTTPRejection(
                403,
                "forbidden",
                "the authenticated actor lacks the required authority",
            )
        return actor

    def authenticate_read(self, authorization: str | None) -> VerifiedActor:
        """Protect a service read with the Owner credential."""
        return self.authenticate(authorization)

    def authenticate_write(self, authorization: str | None) -> VerifiedActor:
        """Protect a service write with the Owner credential."""
        return self.authenticate(authorization)


def token_digest(token: str) -> str:
    """Validate an installation-generated token and return its service digest."""
    _validate_token(token, AuthenticationConfigurationError)
    return hashlib.sha256(token.encode("ascii")).hexdigest()


def owner_authorization_header(
    token: str,
    *,
    destination: str,
    configured_service_url: str,
    redirected: bool = False,
) -> Mapping[str, str]:
    """Create a bearer header only for the configured direct loopback origin."""
    _validate_token(token, CredentialProtectionError)
    if redirected:
        raise CredentialProtectionError("Owner credentials are not sent on redirects")

    configured = _safe_loopback_url(configured_service_url)
    target = _safe_loopback_url(destination)
    if _origin(configured) != _origin(target):
        raise CredentialProtectionError(
            "Owner credentials are restricted to the configured service origin"
        )
    return MappingProxyType({"Authorization": f"Bearer {token}"})


def _bearer_token(authorization: str | None) -> str:
    if not isinstance(authorization, str):
        raise _unauthorized()
    parts = authorization.split(" ")
    if len(parts) != 2 or parts[0].casefold() != "bearer":
        raise _unauthorized()
    token = parts[1]
    try:
        _validate_token(token, ValueError)
    except ValueError:
        raise _unauthorized() from None
    return token


def _validate_token(token: str, error_type: type[ValueError]) -> None:
    if not isinstance(token, str) or _TOKEN_PATTERN.fullmatch(token) is None:
        raise error_type("Owner token must be 64 lowercase hexadecimal characters")


def _unauthorized() -> HTTPRejection:
    return HTTPRejection(401, "unauthorized", "a valid Owner credential is required")


def _safe_loopback_url(value: str) -> SplitResult:
    if not isinstance(value, str):
        raise CredentialProtectionError("service destination must be a URL")
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError as error:
        raise CredentialProtectionError("service destination is invalid") from error
    if (
        parsed.scheme != "http"
        or parsed.hostname not in _LOOPBACK_HOSTS
        or parsed.username is not None
        or parsed.password is not None
        or port is None
        or parsed.fragment
    ):
        raise CredentialProtectionError(
            "Owner credentials require an explicit loopback HTTP service origin"
        )
    return parsed


def _origin(value: SplitResult) -> tuple[str, str, int]:
    # ``_safe_loopback_url`` has already established that hostname and port exist.
    return value.scheme, str(value.hostname), int(value.port)  # type: ignore[arg-type]
