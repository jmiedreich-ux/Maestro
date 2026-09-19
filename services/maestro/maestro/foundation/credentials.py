"""Non-secret authorization bindings for service-owned repository operations."""

from __future__ import annotations

import fnmatch
import os
import re
import shutil
import tempfile
from dataclasses import dataclass
from typing import Callable, Mapping


class RepositoryCredentialError(ValueError):
    """A repository operation is not covered by one configured profile."""


_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}\Z")
_REPOSITORY = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\Z")
_BRANCH = re.compile(r"[A-Za-z0-9][A-Za-z0-9._/-]{0,255}\Z")


def _name(value: object, field: str) -> str:
    if not isinstance(value, str) or _NAME.fullmatch(value) is None:
        raise RepositoryCredentialError(f"{field} is not a canonical non-secret name")
    return value


def normalize_repository(value: object) -> str:
    """Return the one supported, case-normalized ``owner/repository`` identity."""
    if not isinstance(value, str) or _REPOSITORY.fullmatch(value) is None:
        raise RepositoryCredentialError("repository must be an owner/repository identity")
    return value.lower()


def validate_branch(value: object) -> str:
    if (
        not isinstance(value, str)
        or _BRANCH.fullmatch(value) is None
        or value.startswith("/")
        or value.endswith("/")
        or "//" in value
        or ".." in value
        or "@{" in value
    ):
        raise RepositoryCredentialError("branch is not a supported branch name")
    return value


@dataclass(frozen=True)
class RepositoryProfile:
    """One operator-provisioned, non-secret Git credential profile."""

    name: str
    credential_reference: str
    allowed_repositories: tuple[str, ...]
    allowed_branch_patterns: tuple[str, ...]

    def __post_init__(self) -> None:
        _name(self.name, "profile name")
        _name(self.credential_reference, "credential_reference")
        repositories = tuple(normalize_repository(item) for item in self.allowed_repositories)
        if not repositories or len(set(repositories)) != len(repositories):
            raise RepositoryCredentialError("allowed_repositories must be a unique nonempty list")
        patterns = tuple(self.allowed_branch_patterns)
        if not patterns or any(not isinstance(item, str) or not item for item in patterns):
            raise RepositoryCredentialError("allowed_branch_patterns must be a nonempty list")
        object.__setattr__(self, "allowed_repositories", repositories)
        object.__setattr__(self, "allowed_branch_patterns", patterns)

    def allows(self, repository: str, branch: str) -> bool:
        return repository in self.allowed_repositories and any(
            fnmatch.fnmatchcase(branch, pattern) for pattern in self.allowed_branch_patterns
        )


@dataclass(frozen=True)
class RepositoryBinding:
    """The exact configured association between a project repository and profile."""

    binding_id: str
    repository: str
    profile_name: str

    def __post_init__(self) -> None:
        _name(self.binding_id, "binding_id")
        object.__setattr__(self, "repository", normalize_repository(self.repository))
        _name(self.profile_name, "profile_name")


@dataclass(frozen=True)
class AuthorizedRepository:
    """A validated operation binding.  It deliberately contains no secret value."""

    binding_id: str
    repository: str
    branch: str
    profile_name: str
    credential_reference: str


@dataclass(frozen=True)
class ServiceGitRoute:
    """One operator-owned Git endpoint for an authorized repository profile."""

    repository: str
    credential_reference: str
    remote: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "repository", normalize_repository(self.repository))
        _name(self.credential_reference, "credential_reference")
        if not isinstance(self.remote, str) or not self.remote or "\x00" in self.remote:
            raise RepositoryCredentialError("service Git remote must be nonempty text")


class BoundGitTransport:
    """A short-lived privileged Git route; its credential is never journaled."""

    def __init__(self, remote: str, credential: str) -> None:
        self.remote = remote
        self._credential = credential
        self._temporary: str | None = None

    def __enter__(self) -> "BoundGitTransport":
        directory = tempfile.mkdtemp(prefix="maestro-git-credential-")
        askpass = os.path.join(directory, "askpass")
        with open(askpass, "w", encoding="utf-8") as stream:
            stream.write(
                "#!/bin/sh\n"
                "case \"$1\" in *Username*) printf '%s\\n' x-access-token ;; *) "
                "printf '%s\\n' \"$MAESTRO_GIT_TRANSPORT_TOKEN\" ;; esac\n"
            )
        os.chmod(askpass, 0o700)
        self._temporary = directory
        return self

    def __exit__(self, *_: object) -> None:
        directory, self._temporary = self._temporary, None
        if directory is not None:
            shutil.rmtree(directory, ignore_errors=True)
        self._credential = ""

    def environment(self) -> dict[str, str]:
        if self._temporary is None or not self._credential:
            raise RepositoryCredentialError("privileged Git transport is not active")
        return {
            "GIT_ASKPASS": os.path.join(self._temporary, "askpass"),
            "GIT_TERMINAL_PROMPT": "0",
            "MAESTRO_GIT_TRANSPORT_TOKEN": self._credential,
        }


class ServiceGitTransport:
    """Bind a configured remote to one profile and resolve its secret only at use."""

    def __init__(
        self,
        routes: tuple[ServiceGitRoute, ...],
        resolve_credential: Callable[[str], str],
    ) -> None:
        self._routes = {route.repository: route for route in routes}
        if len(self._routes) != len(routes) or not self._routes:
            raise RepositoryCredentialError("service Git routes must be unique and nonempty")
        self._resolve_credential = resolve_credential

    def remote_for(self, authorization: AuthorizedRepository) -> str:
        route = self._routes.get(authorization.repository)
        if route is None or route.credential_reference != authorization.credential_reference:
            raise RepositoryCredentialError("no matching privileged Git route is configured")
        return route.remote

    def bind(self, authorization: AuthorizedRepository) -> BoundGitTransport:
        remote = self.remote_for(authorization)
        try:
            credential = self._resolve_credential(authorization.credential_reference)
        except Exception as error:
            raise RepositoryCredentialError("configured service Git credential is unavailable") from error
        if not isinstance(credential, str) or not credential:
            raise RepositoryCredentialError("configured service Git credential is unavailable")
        return BoundGitTransport(remote, credential)

    def bind_installation_token(
        self, authorization: AuthorizedRepository, installation_token: str
    ) -> BoundGitTransport:
        """Bind an ephemeral GitHub App installation token to its configured route.

        Only the destination-authorization provider calls this service boundary.
        The token is deliberately accepted only for the lifetime of the returned
        context manager and is never attached to an authorization record.
        """
        remote = self.remote_for(authorization)
        if not isinstance(installation_token, str) or not installation_token:
            raise RepositoryCredentialError("GitHub installation token is unavailable")
        return BoundGitTransport(remote, installation_token)


@dataclass(frozen=True)
class GitHubAppCredential:
    """The non-secret locator of a service-owned GitHub App private key."""

    credential_reference: str

    def __post_init__(self) -> None:
        _name(self.credential_reference, "credential_reference")


class ServiceGitHubAppCredentials:
    """Resolve an App private key only while a service API request is assembled.

    The supplied resolver is owned by the service credential store.  This small
    boundary deliberately exposes no operation for callers to inspect or retain
    all configured credential values.
    """

    def __init__(self, resolve_private_key: Callable[[str], str]) -> None:
        if not callable(resolve_private_key):
            raise TypeError("GitHub App credential resolver must be callable")
        self._resolve_private_key = resolve_private_key

    def private_key_for(self, credential: GitHubAppCredential) -> str:
        if not isinstance(credential, GitHubAppCredential):
            raise TypeError("GitHub App credential must be typed")
        try:
            private_key = self._resolve_private_key(credential.credential_reference)
        except Exception as error:
            raise RepositoryCredentialError("configured GitHub App private key is unavailable") from error
        if not isinstance(private_key, str) or not private_key.strip():
            raise RepositoryCredentialError("configured GitHub App private key is unavailable")
        return private_key


class RepositoryAuthorizer:
    """Resolve one repository/branch to exactly one configured service profile."""

    def __init__(
        self,
        profiles: Mapping[str, RepositoryProfile],
        bindings: tuple[RepositoryBinding, ...],
    ) -> None:
        self._profiles = dict(profiles)
        if not self._profiles:
            raise RepositoryCredentialError("at least one repository profile is required")
        for profile_name, profile in self._profiles.items():
            if profile_name != profile.name:
                raise RepositoryCredentialError("repository profile key must match its name")
        self._bindings = tuple(bindings)
        if not self._bindings:
            raise RepositoryCredentialError("at least one repository binding is required")
        seen = set()
        for binding in self._bindings:
            if binding.repository in seen:
                raise RepositoryCredentialError("repository has more than one configured binding")
            seen.add(binding.repository)
            if binding.profile_name not in self._profiles:
                raise RepositoryCredentialError("repository binding names an unknown profile")

    def authorize(self, repository: str, branch: str) -> AuthorizedRepository:
        normalized = normalize_repository(repository)
        validated_branch = validate_branch(branch)
        matches = [item for item in self._bindings if item.repository == normalized]
        if len(matches) != 1:
            raise RepositoryCredentialError("repository has no unique configured binding")
        binding = matches[0]
        profile = self._profiles[binding.profile_name]
        if not profile.allows(normalized, validated_branch):
            raise RepositoryCredentialError("repository profile does not authorize this branch")
        return AuthorizedRepository(
            binding_id=binding.binding_id,
            repository=normalized,
            branch=validated_branch,
            profile_name=profile.name,
            credential_reference=profile.credential_reference,
        )
