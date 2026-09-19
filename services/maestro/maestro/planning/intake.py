"""Registration intake that preserves missing Owner choices as questions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Protocol

from maestro.foundation.credentials import RepositoryAuthorizer, RepositoryCredentialError

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
    publication_branch: str | None = None
    scope: str | None = None
    architect_selection: str | None = None
    reviewer_selection: str | None = None


@dataclass(frozen=True)
class RegistrationIntakeResult:
    inventory: SourceInventory | None
    missing_questions: tuple[IntakeQuestion, ...]
    repository_binding_id: str | None


class RegistrationIntake:
    """Collect required choices before one exact, side-effect-free source read."""

    def __init__(self, sources: ExactSourceReader, authorizer: RepositoryAuthorizer) -> None:
        self._sources = sources
        self._authorizer = authorizer

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
        missing = tuple(self._missing(request))
        if missing:
            for question in missing:
                questions.publish_intake_question(question)
            return RegistrationIntakeResult(None, missing, None)
        assert request.source_ref is not None
        assert request.publication_branch is not None
        try:
            selector = validate_source_ref(request.source_ref)
            authorization = self._authorizer.authorize(request.repository, request.publication_branch)
            inventory = self._sources.read(
                remote=request.remote,
                source_ref=selector,
                overview_path=request.overview_path,
                referenced_paths=request.referenced_paths,
            )
        except (SourceIntakeError, RepositoryCredentialError) as error:
            raise IntakeError(str(error)) from error
        return RegistrationIntakeResult(inventory, (), authorization.binding_id)

    @staticmethod
    def _missing(request: RegistrationIntakeRequest) -> Iterable[IntakeQuestion]:
        fields = (
            ("scope", request.scope, "Choose registration scope", "Which supplied project outcomes are included in this registration?"),
            ("source_ref", request.source_ref, "Choose registration source", "Which full branch, tag, or commit should registration assess?"),
            ("publication_branch", request.publication_branch, "Choose publication branch", "Which authorized existing branch may receive registration outputs?"),
            ("architect_selection", request.architect_selection, "Choose registration architect", "Which configured tool and exact model will assess this registration?"),
            ("reviewer_selection", request.reviewer_selection, "Choose registration reviewer", "Which configured tool and exact model will independently review this registration?"),
        )
        for field, value, subject, prompt in fields:
            if not isinstance(value, str) or not value.strip():
                yield IntakeQuestion(field, subject, prompt)
