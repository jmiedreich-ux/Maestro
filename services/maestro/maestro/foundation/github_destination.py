"""Service-owned GitHub App destination authorization.

This module is the sole foundation boundary that obtains GitHub App
installation tokens for repository reads and publication.  Its durable result
contains only immutable non-secret evidence; the token remains private to the
provider instance and is consumed by the bound Git transport immediately.
"""

from __future__ import annotations

import hashlib
import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Mapping, Protocol
from urllib.parse import quote, urlsplit

from .credentials import (
    AuthorizedRepository,
    GitHubAppCredential,
    RepositoryCredentialError,
    ServiceGitHubAppCredentials,
    ServiceGitTransport,
    normalize_repository,
    validate_branch,
)


class GitHubDestinationError(RuntimeError):
    """A configured GitHub destination cannot be safely authorized."""


class GitHubDestinationConfigurationError(GitHubDestinationError):
    """The typed service-owned destination profile is invalid."""


class GitHubDestinationAuthorizationError(GitHubDestinationError):
    """A journal attempted to use stale or mismatched authorization evidence."""


_MAX_EVIDENCE_AGE_SECONDS = 60


def _identifier(value: object, field: str) -> str:
    if not isinstance(value, str) or not value or len(value) > 128:
        raise GitHubDestinationConfigurationError(f"{field} is invalid")
    if any(character.isspace() or character == "\x00" for character in value):
        raise GitHubDestinationConfigurationError(f"{field} is invalid")
    return value


def _positive(value: object, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise GitHubDestinationConfigurationError(f"{field} must be a positive integer")
    return value


def _api_base_url(value: object) -> str:
    if value is None:
        return "https://api.github.com"
    if not isinstance(value, str) or not value:
        raise GitHubDestinationConfigurationError("api_base_url must be an HTTPS URL")
    parsed = urlsplit(value)
    if (
        parsed.scheme != "https" or not parsed.hostname or parsed.username is not None
        or parsed.password is not None or parsed.query or parsed.fragment
    ):
        raise GitHubDestinationConfigurationError("api_base_url must be an HTTPS URL")
    return f"https://{parsed.netloc}{parsed.path.rstrip('/')}"


def _canonical(value: Mapping[str, Any]) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def _digest(value: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class GitHubAppDestinationProfile:
    """Validated non-secret configuration for one bound GitHub App profile."""

    profile_name: str
    binding_id: str
    credential: GitHubAppCredential
    app_id: int
    installation_id: int
    app_slug: str
    allowed_repositories: tuple[str, ...]
    allowed_branches: tuple[str, ...]
    api_base_url: str = "https://api.github.com"

    def __post_init__(self) -> None:
        _identifier(self.profile_name, "profile_name")
        _identifier(self.binding_id, "binding_id")
        if not isinstance(self.credential, GitHubAppCredential):
            raise GitHubDestinationConfigurationError("credential must be a typed GitHub App credential")
        _positive(self.app_id, "app_id")
        _positive(self.installation_id, "installation_id")
        slug = _identifier(self.app_slug, "app_slug").lower()
        repositories = tuple(normalize_repository(item) for item in self.allowed_repositories)
        branches = tuple(validate_branch(item) for item in self.allowed_branches)
        if not repositories or len(set(repositories)) != len(repositories):
            raise GitHubDestinationConfigurationError("allowed_repositories must be unique and nonempty")
        if not branches or len(set(branches)) != len(branches):
            raise GitHubDestinationConfigurationError("allowed_branches must be unique and nonempty")
        object.__setattr__(self, "app_slug", slug)
        object.__setattr__(self, "allowed_repositories", repositories)
        object.__setattr__(self, "allowed_branches", branches)
        object.__setattr__(self, "api_base_url", _api_base_url(self.api_base_url))

    def allows(self, repository: str, branch: str) -> bool:
        return repository in self.allowed_repositories and branch in self.allowed_branches

    @property
    def configuration_hash(self) -> str:
        return _digest(
            {
                "profile_name": self.profile_name,
                "binding_id": self.binding_id,
                "credential_reference": self.credential.credential_reference,
                "app_id": self.app_id,
                "installation_id": self.installation_id,
                "app_slug": self.app_slug,
                "allowed_repositories": list(self.allowed_repositories),
                "allowed_branches": list(self.allowed_branches),
                "api_base_url": self.api_base_url,
            }
        )

    def snapshot(self, repository: str, branch: str) -> dict[str, Any]:
        return {
            "profile_name": self.profile_name,
            "binding_id": self.binding_id,
            "credential_reference": self.credential.credential_reference,
            "app_id": self.app_id,
            "installation_id": self.installation_id,
            "app_slug": self.app_slug,
            "api_base_url": self.api_base_url,
            "repository": repository,
            "branch": branch,
            "allowed_repositories": list(self.allowed_repositories),
            "allowed_branches": list(self.allowed_branches),
            "configuration_hash": self.configuration_hash,
        }


@dataclass(frozen=True)
class GitHubInstallationToken:
    """An ephemeral token and the permissions GitHub actually returned."""

    value: str = field(repr=False, compare=False)
    permissions: Mapping[str, str] = field(repr=False, compare=False)
    expires_at: float
    api_base_url: str = field(default="https://api.github.com", repr=False, compare=False)

    def __post_init__(self) -> None:
        if not isinstance(self.value, str) or not self.value:
            raise GitHubDestinationError("GitHub installation token is unavailable")
        if not isinstance(self.permissions, Mapping):
            raise GitHubDestinationError("GitHub installation permissions are unavailable")
        if not isinstance(self.expires_at, (int, float)):
            raise GitHubDestinationError("GitHub installation token expiry is unavailable")
        _api_base_url(self.api_base_url)


@dataclass(frozen=True)
class BranchPolicyObservation:
    protected: bool
    rulesets: tuple[Mapping[str, Any], ...]


class GitHubDestinationApi(Protocol):
    """Small real-provider boundary, replaceable only in component tests."""

    def app_identity(self, profile: GitHubAppDestinationProfile) -> Mapping[str, Any]: ...
    def installation_identity(self, profile: GitHubAppDestinationProfile) -> Mapping[str, Any]: ...
    def installation_token(self, profile: GitHubAppDestinationProfile) -> GitHubInstallationToken: ...
    def repository_identity(self, token: GitHubInstallationToken, repository: str) -> Mapping[str, Any]: ...
    def branch_identity(
        self, token: GitHubInstallationToken, repository: str, branch: str
    ) -> Mapping[str, Any]: ...
    def branch_policy(
        self, token: GitHubInstallationToken, repository: str, branch: str
    ) -> BranchPolicyObservation: ...


@dataclass(frozen=True)
class GitHubDestinationAuthorization:
    """Non-secret authorization evidence for one exact repository branch."""

    decision: str
    snapshot: Mapping[str, Any]
    observed_at: float
    evidence_hashes: Mapping[str, str]
    reason: str | None = None
    _token: GitHubInstallationToken | None = field(default=None, repr=False, compare=False)

    def __post_init__(self) -> None:
        if self.decision not in {"allowed", "blocked", "unverifiable"}:
            raise ValueError("destination decision is invalid")
        if not isinstance(self.observed_at, (int, float)):
            raise ValueError("destination observation time is invalid")
        if any(not isinstance(value, str) or len(value) != 64 for value in self.evidence_hashes.values()):
            raise ValueError("destination evidence hashes are invalid")
        if self.decision == "allowed" and self._token is None:
            raise ValueError("allowed destination result requires an ephemeral installation token")

    def durable_record(self) -> dict[str, Any]:
        """Return the only form that callers may persist or expose."""
        return {
            "decision": self.decision,
            "snapshot": dict(self.snapshot),
            "observed_at": self.observed_at,
            "evidence_hashes": dict(self.evidence_hashes),
            "reason": self.reason,
        }


class GitHubDestinationProvider:
    """Authorize exact GitHub destinations with service-owned App credentials."""

    def __init__(self, profile: GitHubAppDestinationProfile, api: GitHubDestinationApi) -> None:
        if not isinstance(profile, GitHubAppDestinationProfile):
            raise TypeError("GitHub destination provider requires a typed profile")
        self.profile = profile
        self._api = api

    def authorize(
        self, repository: str, branch: str, *, now: float | None = None
    ) -> GitHubDestinationAuthorization:
        repository = normalize_repository(repository)
        branch = validate_branch(branch)
        observed_at = time.time() if now is None else now
        snapshot = self.profile.snapshot(repository, branch)
        if not self.profile.allows(repository, branch):
            return self._result("blocked", snapshot, observed_at, {}, "destination is outside the configured allowlist")
        try:
            app = self._api.app_identity(self.profile)
            installation = self._api.installation_identity(self.profile)
            if int(app.get("id", 0)) != self.profile.app_id or app.get("slug") != self.profile.app_slug:
                return self._result("blocked", snapshot, observed_at, {"app": _digest(app)}, "GitHub App identity does not match the configured profile")
            if int(installation.get("id", 0)) != self.profile.installation_id or int(installation.get("app_id", 0)) != self.profile.app_id:
                return self._result("blocked", snapshot, observed_at, {"app": _digest(app), "installation": _digest(installation)}, "GitHub installation does not match the configured App")
            token = self._api.installation_token(self.profile)
            permissions = dict(token.permissions)
            if permissions.get("contents") != "write" or permissions.get("administration") not in {"read", "write"}:
                return self._result("blocked", snapshot, observed_at, {"app": _digest(app), "installation": _digest(installation), "permissions": _digest(permissions)}, "GitHub installation lacks required contents-write or administration-read permission")
            repository_identity = self._api.repository_identity(token, repository)
            if repository_identity.get("full_name", "").lower() != repository:
                return self._result("blocked", snapshot, observed_at, {"repository": _digest(repository_identity)}, "GitHub repository identity does not match the configured destination")
            branch_identity = self._api.branch_identity(token, repository, branch)
            if branch_identity.get("name") != branch:
                return self._result("blocked", snapshot, observed_at, {"repository": _digest(repository_identity), "branch": _digest(branch_identity)}, "GitHub destination branch does not exist")
            policy = self._api.branch_policy(token, repository, branch)
            evidence = {
                "app": _digest(app), "installation": _digest(installation),
                "permissions": _digest(permissions), "repository": _digest(repository_identity),
                "branch": _digest(branch_identity),
                "policy": _digest({"protected": policy.protected, "rulesets": list(policy.rulesets)}),
            }
            if policy.protected or policy.rulesets:
                return self._result("blocked", snapshot, observed_at, evidence, "GitHub branch protection or an active ruleset blocks direct publication")
            if token.expires_at <= observed_at:
                return self._result("unverifiable", snapshot, observed_at, evidence, "GitHub installation token is already expired")
            return GitHubDestinationAuthorization("allowed", snapshot, observed_at, evidence, _token=token)
        except (GitHubDestinationError, RepositoryCredentialError, OSError, ValueError, TypeError, urllib.error.URLError) as error:
            return self._result("unverifiable", snapshot, observed_at, {}, f"GitHub destination could not be verified: {type(error).__name__}")

    def require_fresh_match(
        self,
        result: GitHubDestinationAuthorization,
        authorization: AuthorizedRepository,
        *,
        now: float | None = None,
    ) -> None:
        if not isinstance(result, GitHubDestinationAuthorization):
            raise GitHubDestinationAuthorizationError("a typed GitHub destination result is required")
        current = time.time() if now is None else now
        snapshot = result.snapshot
        if result.decision != "allowed" or result._token is None:
            raise GitHubDestinationAuthorizationError("GitHub destination is not allowed")
        if (
            authorization.binding_id != self.profile.binding_id
            or authorization.profile_name != self.profile.profile_name
            or authorization.credential_reference != self.profile.credential.credential_reference
        ):
            raise GitHubDestinationAuthorizationError("GitHub destination result is not bound to the configured service profile")
        if current < result.observed_at or current - result.observed_at > _MAX_EVIDENCE_AGE_SECONDS:
            raise GitHubDestinationAuthorizationError("GitHub destination authorization is stale")
        if result._token.expires_at <= current:
            raise GitHubDestinationAuthorizationError("GitHub installation token is expired")
        expected = self.profile.snapshot(authorization.repository, authorization.branch)
        if dict(snapshot) != expected:
            raise GitHubDestinationAuthorizationError("GitHub destination authorization does not match the saved profile and target")

    def bind_transport(
        self, result: GitHubDestinationAuthorization, transport: ServiceGitTransport,
        authorization: AuthorizedRepository, *, now: float | None = None,
    ):
        self.require_fresh_match(result, authorization, now=now)
        assert result._token is not None
        return transport.bind_installation_token(authorization, result._token.value)

    @staticmethod
    def _result(
        decision: str, snapshot: Mapping[str, Any], observed_at: float,
        hashes: Mapping[str, str], reason: str,
    ) -> GitHubDestinationAuthorization:
        return GitHubDestinationAuthorization(decision, snapshot, observed_at, hashes, reason)


class GitHubDestinationRouter:
    """Route each exact repository to its one configured destination provider."""

    def __init__(self, providers: Mapping[str, GitHubDestinationProvider]) -> None:
        checked: dict[str, GitHubDestinationProvider] = {}
        for repository, provider in providers.items():
            normalized = normalize_repository(repository)
            if not isinstance(provider, GitHubDestinationProvider):
                raise TypeError("GitHub destination routes require configured providers")
            if normalized in checked or normalized not in provider.profile.allowed_repositories:
                raise GitHubDestinationConfigurationError(
                    "each repository requires one matching GitHub destination provider"
                )
            checked[normalized] = provider
        if not checked:
            raise GitHubDestinationConfigurationError(
                "at least one GitHub destination route is required"
            )
        self._providers = checked

    @property
    def providers(self) -> tuple[GitHubDestinationProvider, ...]:
        return tuple(dict.fromkeys(self._providers.values()))

    def provider_for(self, repository: str) -> GitHubDestinationProvider:
        normalized = normalize_repository(repository)
        try:
            return self._providers[normalized]
        except KeyError as error:
            raise GitHubDestinationConfigurationError(
                "repository has no configured GitHub destination route"
            ) from error

    def authorize(
        self, repository: str, branch: str, *, now: float | None = None
    ) -> GitHubDestinationAuthorization:
        return self.provider_for(repository).authorize(repository, branch, now=now)

    def require_fresh_match(
        self,
        result: GitHubDestinationAuthorization,
        authorization: AuthorizedRepository,
        *,
        now: float | None = None,
    ) -> None:
        self.provider_for(authorization.repository).require_fresh_match(
            result, authorization, now=now
        )

    def bind_transport(
        self,
        result: GitHubDestinationAuthorization,
        transport: ServiceGitTransport,
        authorization: AuthorizedRepository,
        *,
        now: float | None = None,
    ):
        return self.provider_for(authorization.repository).bind_transport(
            result, transport, authorization, now=now
        )


GitHubDestination = GitHubDestinationProvider | GitHubDestinationRouter


def destination_provider_for(
    destination: GitHubDestination, repository: str
) -> GitHubDestinationProvider:
    if isinstance(destination, GitHubDestinationRouter):
        return destination.provider_for(repository)
    if isinstance(destination, GitHubDestinationProvider):
        return destination
    raise TypeError("GitHub destination provider is invalid")


def destination_providers(
    destination: GitHubDestination,
) -> tuple[GitHubDestinationProvider, ...]:
    if isinstance(destination, GitHubDestinationRouter):
        return destination.providers
    if isinstance(destination, GitHubDestinationProvider):
        return (destination,)
    raise TypeError("GitHub destination provider is invalid")


class GitHubRestDestinationApi:
    """The actual GitHub REST boundary used by installed service composition."""

    def __init__(self, credentials: ServiceGitHubAppCredentials) -> None:
        if not isinstance(credentials, ServiceGitHubAppCredentials):
            raise TypeError("GitHub REST destination API requires service credentials")
        self._credentials = credentials

    def app_identity(self, profile: GitHubAppDestinationProfile) -> Mapping[str, Any]:
        return self._app_request(profile, "GET", "/app")

    def installation_identity(self, profile: GitHubAppDestinationProfile) -> Mapping[str, Any]:
        return self._app_request(profile, "GET", f"/app/installations/{profile.installation_id}")

    def installation_token(self, profile: GitHubAppDestinationProfile) -> GitHubInstallationToken:
        payload = self._app_request(profile, "POST", f"/app/installations/{profile.installation_id}/access_tokens")
        token = payload.get("token")
        expires = payload.get("expires_at")
        if not isinstance(expires, str):
            raise GitHubDestinationError("GitHub installation token response lacks expiry")
        try:
            expiry = datetime.fromisoformat(expires.replace("Z", "+00:00")).astimezone(timezone.utc).timestamp()
        except ValueError as error:
            raise GitHubDestinationError("GitHub installation token expiry is invalid") from error
        return GitHubInstallationToken(token, payload.get("permissions", {}), expiry, profile.api_base_url)

    def repository_identity(self, token: GitHubInstallationToken, repository: str) -> Mapping[str, Any]:
        return self._token_request(token, "GET", f"/repos/{repository}")

    def branch_identity(
        self, token: GitHubInstallationToken, repository: str, branch: str
    ) -> Mapping[str, Any]:
        return self._token_request(token, "GET", f"/repos/{repository}/branches/{quote(branch, safe='')}")

    def branch_policy(self, token: GitHubInstallationToken, repository: str, branch: str) -> BranchPolicyObservation:
        encoded = quote(branch, safe="")
        protection_status, protection = self._token_request_with_status(token, "GET", f"/repos/{repository}/branches/{encoded}/protection")
        if protection_status not in {200, 404}:
            raise GitHubDestinationError("GitHub branch protection response is invalid")
        rules_status, rules = self._token_request_with_status(token, "GET", f"/repos/{repository}/rules/branches/{encoded}")
        if rules_status != 200 or not isinstance(rules, list):
            raise GitHubDestinationError("GitHub branch ruleset response is unavailable")
        return BranchPolicyObservation(protection_status == 200 and bool(protection), tuple(rules))

    def _app_request(self, profile: GitHubAppDestinationProfile, method: str, path: str) -> Mapping[str, Any]:
        import jwt

        now = int(time.time())
        private_key = self._credentials.private_key_for(profile.credential)
        jwt_token = jwt.encode({"iat": now - 60, "exp": now + 300, "iss": str(profile.app_id)}, private_key, algorithm="RS256")
        return self._request(profile.api_base_url, method, path, {"Authorization": f"Bearer {jwt_token}"}, {200, 201})

    def _token_request(self, token: GitHubInstallationToken, method: str, path: str) -> Mapping[str, Any]:
        status, payload = self._token_request_with_status(token, method, path)
        if status != 200 or not isinstance(payload, Mapping):
            raise GitHubDestinationError("GitHub API response is unavailable")
        return payload

    def _token_request_with_status(self, token: GitHubInstallationToken, method: str, path: str) -> tuple[int, Any]:
        return self._request_with_status(token.api_base_url, method, path, {"Authorization": f"token {token.value}"})

    def _request(
        self, base_url: str, method: str, path: str, headers: Mapping[str, str],
        success_statuses: set[int] = {200},
    ) -> Mapping[str, Any]:
        status, payload = self._request_with_status(base_url, method, path, headers)
        if status not in success_statuses or not isinstance(payload, Mapping):
            raise GitHubDestinationError("GitHub API response is unavailable")
        return payload

    def _request_with_status(self, base_url: str, method: str, path: str, headers: Mapping[str, str]) -> tuple[int, Any]:
        request = urllib.request.Request(
            base_url + path, method=method,
            headers={"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28", **headers},
        )
        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                return int(response.status), json.loads(response.read())
        except urllib.error.HTTPError as error:
            try:
                payload: Any = json.loads(error.read())
            except (UnicodeDecodeError, json.JSONDecodeError):
                payload = {}
            return error.code, payload
