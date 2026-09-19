"""Registration intake bound to a saved GitHub destination authorization."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Iterable, Mapping, Protocol

from maestro.foundation.credentials import (
    AuthorizedRepository,
    RepositoryAuthorizer,
    RepositoryCredentialError,
    ServiceGitTransport,
)
from maestro.foundation.git_read import run_git
from maestro.foundation.github_destination import (
    GitHubDestinationAuthorization,
    GitHubDestinationAuthorizationError,
    GitHubDestinationProvider,
)

from .sources import ExactSourceReader, SourceIntakeError, SourceInventory, validate_source_ref


class IntakeError(ValueError):
    """Registration intake cannot safely make or replace a selection."""


@dataclass(frozen=True)
class IntakeQuestion:
    """A service-owned question required before registration assessment."""

    field: str
    subject: str
    prompt: str


class IntakeQuestionPublisher(Protocol):
    """The registration process's service boundary for durable questions."""

    def publish_intake_question(self, question: IntakeQuestion) -> None: ...


@dataclass(frozen=True)
class RegistrationIntakeRequest:
    repository: str
    remote: str
    overview_path: str
    referenced_paths: tuple[str, ...] = ()
    source_ref: str | None = None
    prior_source_ref: str | None = None
    publication_branch: str | None = None
    scope: str | None = None
    architect_selection: str | None = None
    reviewer_selection: str | None = None


@dataclass(frozen=True)
class RegistrationIntakeResult:
    """Non-secret, durable intake data; never contains an App token."""

    inventory: SourceInventory | None
    missing_questions: tuple[IntakeQuestion, ...]
    repository_binding_id: str | None
    selected_scope: str | None
    source_selection: str | None
    destination_snapshot_reference: str | None
    destination_evidence: Mapping[str, object] | None


class RegistrationIntake:
    """Collect choices, authorize the destination, then read exact source once."""

    def __init__(
        self,
        sources: ExactSourceReader,
        authorizer: RepositoryAuthorizer,
        transport: ServiceGitTransport,
        destination_provider: GitHubDestinationProvider,
    ) -> None:
        if not isinstance(sources, ExactSourceReader):
            raise TypeError("registration intake requires an exact source reader")
        if not isinstance(authorizer, RepositoryAuthorizer):
            raise TypeError("registration intake requires a repository authorizer")
        if not isinstance(transport, ServiceGitTransport):
            raise TypeError("registration intake requires service Git transport")
        if not isinstance(destination_provider, GitHubDestinationProvider):
            raise TypeError("registration intake requires the publication-owned GitHub destination provider")
        self._sources = sources
        self._authorizer = authorizer
        self._transport = transport
        self._destination_provider = destination_provider

    def begin(
        self, request: RegistrationIntakeRequest, *, questions: IntakeQuestionPublisher,
    ) -> RegistrationIntakeResult:
        if not isinstance(request, RegistrationIntakeRequest):
            raise TypeError("registration intake requires RegistrationIntakeRequest")
        if questions is None or not hasattr(questions, "publish_intake_question"):
            raise TypeError("registration intake requires a service question publisher")
        source_selection = self._source_selection_kind(request)
        missing = tuple(self._missing(request))
        if missing:
            for question in missing:
                questions.publish_intake_question(question)
            return RegistrationIntakeResult(None, missing, None, request.scope, source_selection, None, None)

        assert request.publication_branch is not None
        try:
            authorization = self._authorizer.authorize(request.repository, request.publication_branch)
            remote = self._transport.remote_for(authorization)
            if remote != request.remote:
                raise IntakeError("source remote does not match the authorized repository profile")
            provider_result = self._destination_provider.authorize(
                authorization.repository, authorization.branch
            )
            self._destination_provider.require_fresh_match(provider_result, authorization)
            selector, source_selection = self._source_selection(request, authorization, provider_result)
            selector = validate_source_ref(selector)
            with self._destination_provider.bind_transport(
                provider_result, self._transport, authorization
            ) as bound:
                command = lambda *arguments: run_git(*arguments, environment=bound.environment())
                inventory = self._sources.read_registration(
                    remote=remote,
                    source_ref=selector,
                    overview_path=request.overview_path,
                    referenced_paths=request.referenced_paths,
                    command=command,
                )
        except (
            SourceIntakeError,
            RepositoryCredentialError,
            GitHubDestinationAuthorizationError,
        ) as error:
            raise IntakeError(str(error)) from error
        return RegistrationIntakeResult(
            inventory,
            (),
            authorization.binding_id,
            request.scope,
            source_selection,
            _snapshot_reference(provider_result),
            _durable_evidence(provider_result),
        )

    def _source_selection(
        self,
        request: RegistrationIntakeRequest,
        authorization: AuthorizedRepository,
        provider_result: GitHubDestinationAuthorization,
    ) -> tuple[str, str]:
        if isinstance(request.source_ref, str) and request.source_ref.strip():
            return request.source_ref, "supplied"
        if isinstance(request.prior_source_ref, str) and request.prior_source_ref.strip():
            return request.prior_source_ref, "inherited"
        try:
            with self._destination_provider.bind_transport(
                provider_result, self._transport, authorization
            ) as bound:
                return self._sources.default_branch(
                    self._transport.remote_for(authorization),
                    command=lambda *arguments: run_git(*arguments, environment=bound.environment()),
                ), "defaulted"
        except (SourceIntakeError, RepositoryCredentialError, GitHubDestinationAuthorizationError) as error:
            raise IntakeError(str(error)) from error

    @staticmethod
    def _source_selection_kind(request: RegistrationIntakeRequest) -> str:
        if isinstance(request.source_ref, str) and request.source_ref.strip():
            return "supplied"
        if isinstance(request.prior_source_ref, str) and request.prior_source_ref.strip():
            return "inherited"
        return "defaulted"

    @staticmethod
    def _missing(request: RegistrationIntakeRequest) -> Iterable[IntakeQuestion]:
        fields = (
            ("scope", request.scope, "Choose registration scope", "Which supplied project outcomes are included in this registration?"),
            ("publication_branch", request.publication_branch, "Choose publication branch", "Which authorized existing branch may receive registration outputs?"),
            ("architect_selection", request.architect_selection, "Choose registration architect", "Which configured tool and exact model will assess this registration?"),
            ("reviewer_selection", request.reviewer_selection, "Choose registration reviewer", "Which configured tool and exact model will independently review this registration?"),
        )
        for field, value, subject, prompt in fields:
            if not isinstance(value, str) or not value.strip():
                yield IntakeQuestion(field, subject, prompt)


def _snapshot_reference(result: GitHubDestinationAuthorization) -> str:
    """Stable reference for the exact effective profile snapshot, not its token."""
    snapshot = json.dumps(dict(result.snapshot), sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    return hashlib.sha256(snapshot.encode("utf-8")).hexdigest()


def _durable_evidence(result: GitHubDestinationAuthorization) -> Mapping[str, object]:
    """Copy the provider's persistable evidence while it still owns its token."""
    return json.loads(json.dumps(result.durable_record(), sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False))
