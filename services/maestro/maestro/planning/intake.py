"""Registration intake that preserves missing Owner choices as questions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Protocol

from maestro.foundation.credentials import (
    RepositoryAuthorizer,
    RepositoryCredentialError,
    ServiceGitTransport,
)
from maestro.foundation.git_read import GitReadError, RemoteGitReader, run_git

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
    inventory: SourceInventory | None
    missing_questions: tuple[IntakeQuestion, ...]
    repository_binding_id: str | None
    selected_scope: str | None
    source_selection: str | None


class RegistrationIntake:
    """Collect required choices before one exact, side-effect-free source read."""

    def __init__(
        self,
        sources: ExactSourceReader,
        authorizer: RepositoryAuthorizer,
        transport: ServiceGitTransport,
    ) -> None:
        self._sources = sources
        self._authorizer = authorizer
        self._transport = transport

    def begin(
        self,
        request: RegistrationIntakeRequest,
        *,
        questions: IntakeQuestionPublisher,
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
            return RegistrationIntakeResult(None, missing, None, request.scope, source_selection)
        assert request.publication_branch is not None
        try:
            authorization = self._authorizer.authorize(request.repository, request.publication_branch)
            remote = self._transport.remote_for(authorization)
            if remote != request.remote:
                raise IntakeError("source remote does not match the authorized repository profile")
            self._verify_destination(authorization, remote)
            selector, source_selection = self._source_selection(request)
            selector = validate_source_ref(selector)
            inventory = self._sources.read_registration(
                remote=request.remote,
                source_ref=selector,
                overview_path=request.overview_path,
                referenced_paths=request.referenced_paths,
            )
        except (SourceIntakeError, RepositoryCredentialError) as error:
            raise IntakeError(str(error)) from error
        return RegistrationIntakeResult(
            inventory, (), authorization.binding_id, request.scope, source_selection
        )

    def _source_selection(self, request: RegistrationIntakeRequest) -> tuple[str, str]:
        if isinstance(request.source_ref, str) and request.source_ref.strip():
            return request.source_ref, "supplied"
        if isinstance(request.prior_source_ref, str) and request.prior_source_ref.strip():
            return request.prior_source_ref, "inherited"
        try:
            return self._sources.default_branch(request.remote), "defaulted"
        except SourceIntakeError as error:
            raise IntakeError(str(error)) from error

    @staticmethod
    def _source_selection_kind(request: RegistrationIntakeRequest) -> str:
        if isinstance(request.source_ref, str) and request.source_ref.strip():
            return "supplied"
        if isinstance(request.prior_source_ref, str) and request.prior_source_ref.strip():
            return "inherited"
        return "defaulted"

    def _verify_destination(self, authorization, remote: str) -> None:
        """Check the configured privileged route before any source read.

        The profile branch allowlist is the installed protection policy.  A
        credentialed, read-only destination observation proves the branch
        exists and the configured service route can access it; it never
        creates a branch or probes a different target.
        """
        try:
            with self._transport.bind(authorization) as bound:
                RemoteGitReader().snapshot(
                    remote,
                    authorization.branch,
                    (),
                    command=lambda *arguments: run_git(
                        *arguments, environment=bound.environment()
                    ),
                )
        except (GitReadError, RepositoryCredentialError) as error:
            raise IntakeError("authorized publication destination is unavailable") from error

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
