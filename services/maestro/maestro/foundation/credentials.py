"""Non-secret authorization bindings for service-owned repository operations."""

from __future__ import annotations

import fnmatch
import re
from dataclasses import dataclass
from typing import Mapping


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
