"""Registration intake that preserves missing Owner choices as questions."""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
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
class DirectWriteEvidence:
    """Non-secret proof that the bound route may directly write its target."""

    repository: str
    branch: str
    binding_id: str
    protection_state: str


class DestinationWriteVerifier(Protocol):
    """Obtains service-credential evidence for one publication target."""

    def verify(self, authorization, transport: ServiceGitTransport) -> DirectWriteEvidence: ...


class GitHubDirectWriteVerifier:
    """Fail closed unless GitHub authoritatively allows a direct branch write.

    The credential is obtained only from the configured bound transport and is
    sent directly to the configured GitHub API endpoint.  It is never saved in
    an intake result, source inventory, log, or exception.
    """

    def __init__(self, api_base: str = "https://api.github.com") -> None:
        if not isinstance(api_base, str) or not api_base.startswith(("https://", "http://")):
            raise ValueError("GitHub API endpoint must be an absolute HTTP URL")
        self._api_base = api_base.rstrip("/")

    def verify(self, authorization, transport: ServiceGitTransport) -> DirectWriteEvidence:
        repository = authorization.repository
        branch = authorization.branch
        encoded_branch = urllib.parse.quote(branch, safe="")
        try:
            with transport.bind(authorization) as bound:
                token = bound.environment()["MAESTRO_GIT_TRANSPORT_TOKEN"]
                repository_data = self._get(f"/repos/{repository}", token)
                branch_data = self._get(
                    f"/repos/{repository}/branches/{encoded_branch}", token
                )
        except (KeyError, RepositoryCredentialError, urllib.error.URLError, ValueError) as error:
            raise IntakeError("authorized publication destination cannot be verified") from error
        permissions = repository_data.get("permissions")
        if (
            repository_data.get("full_name", "").lower() != repository
            or not isinstance(permissions, dict)
            or permissions.get("push") is not True
        ):
            raise IntakeError("authorized service credential cannot directly write the destination")
        if branch_data.get("name") != branch:
            raise IntakeError("authorized publication destination branch does not exist")
        if branch_data.get("protected") is not False:
            raise IntakeError("publication destination is protected against direct writes")
        return DirectWriteEvidence(
            repository=repository,
            branch=branch,
            binding_id=authorization.binding_id,
            protection_state="direct-write-allowed",
        )

    def _get(self, path: str, token: str) -> dict[str, object]:
        request = urllib.request.Request(
            f"{self._api_base}{path}",
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {token}",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                payload = json.loads(response.read())
        except urllib.error.HTTPError as error:
            raise IntakeError("authorized publication destination cannot be verified") from error
        if not isinstance(payload, dict):
            raise IntakeError("authorized publication destination returned invalid evidence")
        return payload


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
    direct_write_evidence: DirectWriteEvidence | None


class RegistrationIntake:
    """Collect required choices before one exact, side-effect-free source read."""

    def __init__(
        self,
        sources: ExactSourceReader,
        authorizer: RepositoryAuthorizer,
        transport: ServiceGitTransport,
        destination_verifier: DestinationWriteVerifier | None = None,
    ) -> None:
        self._sources = sources
        self._authorizer = authorizer
        self._transport = transport
        self._destination_verifier = destination_verifier or GitHubDirectWriteVerifier()

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
            return RegistrationIntakeResult(
                None, missing, None, request.scope, source_selection, None
            )
        assert request.publication_branch is not None
        try:
            authorization = self._authorizer.authorize(request.repository, request.publication_branch)
            remote = self._transport.remote_for(authorization)
            if remote != request.remote:
                raise IntakeError("source remote does not match the authorized repository profile")
            evidence = self._verify_destination(authorization, remote)
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
            inventory,
            (),
            authorization.binding_id,
            request.scope,
            source_selection,
            evidence,
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

    def _verify_destination(
        self, authorization, remote: str
    ) -> DirectWriteEvidence:
        """Check the configured privileged route before any source read.

        A service-credential GitHub permission/branch observation proves the
        configured app can directly write the exact existing branch under its
        current protection state.  A separate bound Git read confirms that the
        Git route itself reaches that same branch.  Both are required.
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
            return self._destination_verifier.verify(authorization, self._transport)
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
