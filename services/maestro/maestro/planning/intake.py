"""Registration intake bound to a saved GitHub destination authorization."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterator, Mapping as MappingABC
from dataclasses import dataclass, replace
from typing import Iterable, Mapping, Protocol

from maestro.foundation.credentials import (
    AuthorizedRepository,
    RepositoryAuthorizer,
    RepositoryCredentialError,
    ServiceGitTransport,
    normalize_repository,
    validate_branch,
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

    def __init__(self, message: str, *, attempt: "RegistrationIntakeResult | None" = None) -> None:
        super().__init__(message)
        self.attempt = attempt


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
    source_ref: str | None = None
    publication_branch: str | None = None
    failure: str | None = None
    repository: str | None = None
    selection_decision_ref: str | None = None

    @property
    def selection_decision_reference(self) -> str | None:
        """Long-form alias for the saved selection Decision reference."""
        return self.selection_decision_ref

    @property
    def source_commit(self) -> str | None:
        return None if self.inventory is None else self.inventory.source_commit

    @property
    def overview_path(self) -> str | None:
        return None if self.inventory is None else self.inventory.overview_path

    def to_record(self) -> dict[str, object]:
        """Return the complete detached JSON record for this intake state.

        A completed intake carries every value an assessment or recovery may
        consume.  Incomplete and failed attempts deliberately have no source
        inventory, so loading them cannot be interpreted as permission to read
        the repository again.
        """
        self._validate_persisted_state()
        record: dict[str, object] = {
            "schema_version": 1,
            "repository": self.repository,
            "repository_binding_id": self.repository_binding_id,
            "selected_scope": self.selected_scope,
            "source_selection": self.source_selection,
            "selection_decision_ref": self.selection_decision_ref,
            "destination_snapshot_reference": self.destination_snapshot_reference,
            "destination_evidence": _plain_json(self.destination_evidence),
            "source_ref": self.source_ref,
            "source_commit": self.source_commit,
            "overview_path": self.overview_path,
            "publication_branch": self.publication_branch,
            "inventory": None if self.inventory is None else self.inventory.to_record(),
            "missing_questions": [
                {"field": item.field, "subject": item.subject, "prompt": item.prompt}
                for item in self.missing_questions
            ],
            "failure": self.failure,
        }
        record["integrity_sha256"] = _record_digest(record)
        return record

    def to_json(self) -> str:
        """Serialize a canonical durable record without exposing credentials."""
        return _canonical_json(self.to_record())

    @classmethod
    def from_record(cls, value: object) -> "RegistrationIntakeResult":
        fields = {
            "schema_version", "repository", "repository_binding_id", "selected_scope",
            "source_selection", "selection_decision_ref", "destination_snapshot_reference",
            "destination_evidence", "source_ref", "source_commit", "overview_path",
            "publication_branch", "inventory",
            "missing_questions", "failure", "integrity_sha256",
        }
        if not isinstance(value, MappingABC) or set(value) != fields:
            raise IntakeError("saved intake record is invalid")
        if value.get("schema_version") != 1:
            raise IntakeError("saved intake record schema version is invalid")
        digest = value.get("integrity_sha256")
        if not isinstance(digest, str) or len(digest) != 64 or digest != _record_digest({key: item for key, item in value.items() if key != "integrity_sha256"}):
            raise IntakeError("saved intake record integrity check failed")
        questions_value = value.get("missing_questions")
        if not isinstance(questions_value, list):
            raise IntakeError("saved intake record questions are invalid")
        questions: list[IntakeQuestion] = []
        for item in questions_value:
            if not isinstance(item, MappingABC) or set(item) != {"field", "subject", "prompt"}:
                raise IntakeError("saved intake record question is invalid")
            question = tuple(item.get(key) for key in ("field", "subject", "prompt"))
            if any(not isinstance(part, str) or not part for part in question):
                raise IntakeError("saved intake record question is invalid")
            questions.append(IntakeQuestion(*question))
        inventory_value = value.get("inventory")
        try:
            inventory = None if inventory_value is None else SourceInventory.from_record(inventory_value)
        except SourceIntakeError as error:
            raise IntakeError(str(error)) from error
        evidence = value.get("destination_evidence")
        if evidence is not None and not isinstance(evidence, MappingABC):
            raise IntakeError("saved intake destination evidence is invalid")
        result = cls(
            inventory,
            tuple(questions),
            _optional_text(value, "repository_binding_id"),
            _optional_text(value, "selected_scope"),
            _optional_text(value, "source_selection"),
            _optional_text(value, "destination_snapshot_reference"),
            None if evidence is None else _freeze_json_evidence(evidence),
            _optional_text(value, "source_ref"),
            _optional_text(value, "publication_branch"),
            _optional_text(value, "failure"),
            _optional_text(value, "repository"),
            _optional_text(value, "selection_decision_ref"),
        )
        source_commit = _optional_text(value, "source_commit")
        overview_path = _optional_text(value, "overview_path")
        if inventory is None:
            if source_commit is not None or overview_path is not None:
                raise IntakeError("an incomplete intake cannot have saved source inventory details")
        elif source_commit != inventory.source_commit or overview_path != inventory.overview_path:
            raise IntakeError("saved intake source details do not match its inventory")
        try:
            result._validate_persisted_state()
        except (RepositoryCredentialError, SourceIntakeError) as error:
            raise IntakeError(str(error)) from error
        return result

    @classmethod
    def from_json(cls, value: object) -> "RegistrationIntakeResult":
        if not isinstance(value, (str, bytes, bytearray)):
            raise IntakeError("saved intake JSON must be text or bytes")
        try:
            return cls.from_record(json.loads(value))
        except (UnicodeDecodeError, json.JSONDecodeError, TypeError) as error:
            raise IntakeError("saved intake JSON is invalid") from error

    def _validate_persisted_state(self) -> None:
        if not isinstance(self.missing_questions, tuple) or any(not isinstance(item, IntakeQuestion) for item in self.missing_questions):
            raise IntakeError("saved intake questions are invalid")
        if self.inventory is None:
            if self.selection_decision_ref is not None:
                raise IntakeError("an incomplete intake cannot have a selection decision reference")
            if self.failure is None:
                return
            if not isinstance(self.failure, str) or not self.failure.strip() or self.missing_questions:
                raise IntakeError("a failed intake record is invalid")
            required = {
                "repository": self.repository,
                "repository_binding_id": self.repository_binding_id,
                "selected_scope": self.selected_scope,
                "source_selection": self.source_selection,
                "destination_snapshot_reference": self.destination_snapshot_reference,
                "destination_evidence": self.destination_evidence,
                "publication_branch": self.publication_branch,
            }
            text_fields = {key: value for key, value in required.items() if key != "destination_evidence"}
            if any(not isinstance(value, str) or not value for value in text_fields.values()) or not isinstance(self.destination_evidence, MappingABC):
                raise IntakeError("a failed intake record is incomplete")
            assert self.repository is not None
            assert self.source_selection is not None
            assert self.destination_snapshot_reference is not None
            assert self.destination_evidence is not None
            assert self.publication_branch is not None
            if normalize_repository(self.repository) != self.repository:
                raise IntakeError("saved intake repository is not normalized")
            validate_branch(self.publication_branch)
            if self.source_selection not in {"supplied", "inherited", "defaulted"}:
                raise IntakeError("saved intake source selection is invalid")
            if self.source_ref is None:
                if self.source_selection != "defaulted":
                    raise IntakeError("saved intake source selector is missing")
            elif validate_source_ref(self.source_ref) != self.source_ref:
                raise IntakeError("saved intake source selector is not normalized")
            _validate_destination_evidence(
                self.destination_evidence, self.repository, self.repository_binding_id,
                self.publication_branch, self.destination_snapshot_reference,
            )
            return
        if self.missing_questions or self.failure is not None:
            raise IntakeError("a successful intake cannot retain questions or failure")
        required = {
            "repository": self.repository,
            "repository_binding_id": self.repository_binding_id,
            "selected_scope": self.selected_scope,
            "source_selection": self.source_selection,
            "selection_decision_ref": self.selection_decision_ref,
            "destination_snapshot_reference": self.destination_snapshot_reference,
            "destination_evidence": self.destination_evidence,
            "source_ref": self.source_ref,
            "publication_branch": self.publication_branch,
        }
        text_fields = {key: value for key, value in required.items() if key != "destination_evidence"}
        if any(not isinstance(value, str) or not value for value in text_fields.values()) or not isinstance(self.destination_evidence, MappingABC):
            raise IntakeError("a successful intake record is incomplete")
        assert self.repository is not None
        assert self.source_selection is not None
        assert self.source_ref is not None
        assert self.publication_branch is not None
        assert self.destination_snapshot_reference is not None
        assert self.destination_evidence is not None
        assert self.selection_decision_ref is not None
        if normalize_repository(self.repository) != self.repository:
            raise IntakeError("saved intake repository is not normalized")
        validate_branch(self.publication_branch)
        if self.source_selection not in {"supplied", "inherited", "defaulted"}:
            raise IntakeError("saved intake source selection is invalid")
        if validate_source_ref(self.source_ref) != self.inventory.source_ref:
            raise IntakeError("saved intake selector does not match its inventory")
        if not self.inventory.source_references or not self.inventory.outcomes:
            raise IntakeError("saved intake inventory is incomplete")
        assert self.repository_binding_id is not None
        _validate_destination_evidence(
            self.destination_evidence, self.repository, self.repository_binding_id,
            self.publication_branch, self.destination_snapshot_reference,
        )
        if _selection_decision_reference(
            self.repository, self.source_selection, self.source_ref, self.inventory.source_commit,
            self.inventory.overview_path, self.publication_branch, self.destination_snapshot_reference,
        ) != self.selection_decision_ref:
            raise IntakeError("saved intake selection decision reference does not match its selection")


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
        attempt: RegistrationIntakeResult | None = None
        try:
            authorization = self._authorizer.authorize(request.repository, request.publication_branch)
            remote = self._transport.remote_for(authorization)
            if remote != request.remote:
                raise IntakeError("source remote does not match the authorized repository profile")
            provider_result = self._destination_provider.authorize(
                authorization.repository, authorization.branch
            )
            # This is deliberately built before the provider decision is used.
            # It is the non-secret record the registration service persists for
            # an allowed, blocked, or unverifiable authorization attempt.
            attempt = self._attempt_result(
                request, authorization, source_selection, self._attempted_source_ref(request), provider_result
            )
            self._destination_provider.require_fresh_match(provider_result, authorization)
            selector, source_selection = self._source_selection(request, authorization, provider_result)
            selector = validate_source_ref(selector)
            attempt = replace(attempt, source_selection=source_selection, source_ref=selector)
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
            saved_attempt = None if attempt is None else replace(attempt, failure=str(error))
            raise IntakeError(str(error), attempt=saved_attempt) from error
        except IntakeError as error:
            saved_attempt = error.attempt
            if saved_attempt is None and attempt is not None:
                saved_attempt = replace(attempt, failure=str(error))
            raise IntakeError(str(error), attempt=saved_attempt) from error
        assert attempt is not None
        return replace(
            attempt,
            inventory=inventory,
            repository=authorization.repository,
            selection_decision_ref=_selection_decision_reference(
                authorization.repository, source_selection, inventory.source_ref, inventory.source_commit,
                inventory.overview_path, authorization.branch, attempt.destination_snapshot_reference,
            ),
        )

    def rehydrate(self, saved_record: str | bytes | bytearray) -> RegistrationIntakeResult:
        """Rebuild saved intake state without authorizing or reading a source."""
        return RegistrationIntakeResult.from_json(saved_record)

    @staticmethod
    def _attempted_source_ref(request: RegistrationIntakeRequest) -> str | None:
        if isinstance(request.source_ref, str) and request.source_ref.strip():
            return request.source_ref
        if isinstance(request.prior_source_ref, str) and request.prior_source_ref.strip():
            return request.prior_source_ref
        return None

    @staticmethod
    def _attempt_result(
        request: RegistrationIntakeRequest,
        authorization: AuthorizedRepository,
        source_selection: str,
        source_ref: str | None,
        provider_result: GitHubDestinationAuthorization,
    ) -> RegistrationIntakeResult:
        return RegistrationIntakeResult(
            None,
            (),
            authorization.binding_id,
            request.scope,
            source_selection,
            _snapshot_reference(provider_result),
            _durable_evidence(provider_result),
            source_ref,
            authorization.branch,
            repository=authorization.repository,
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


def _snapshot_reference_from_evidence(evidence: Mapping[str, object]) -> str:
    snapshot = evidence.get("snapshot")
    if not isinstance(snapshot, MappingABC):
        raise IntakeError("saved intake destination evidence lacks a snapshot")
    return hashlib.sha256(_canonical_json(_plain_json(snapshot)).encode("utf-8")).hexdigest()


def _validate_destination_evidence(
    evidence: Mapping[str, object], repository: str, binding_id: str,
    publication_branch: str, snapshot_reference: str,
) -> None:
    fields = {"decision", "snapshot", "observed_at", "evidence_hashes", "reason"}
    if set(evidence) != fields:
        raise IntakeError("saved intake destination evidence is invalid")
    decision = evidence["decision"]
    snapshot = evidence["snapshot"]
    observed_at = evidence["observed_at"]
    hashes = evidence["evidence_hashes"]
    reason = evidence["reason"]
    if not isinstance(decision, str) or decision not in {"allowed", "blocked", "unverifiable"}:
        raise IntakeError("saved intake destination decision is invalid")
    if isinstance(observed_at, bool) or not isinstance(observed_at, (int, float)):
        raise IntakeError("saved intake destination observation is invalid")
    if not isinstance(reason, str | type(None)):
        raise IntakeError("saved intake destination reason is invalid")
    if not isinstance(snapshot, MappingABC) or not isinstance(hashes, MappingABC):
        raise IntakeError("saved intake destination evidence is invalid")
    if snapshot.get("repository") != repository or snapshot.get("branch") != publication_branch:
        raise IntakeError("saved intake destination snapshot does not match its target")
    if snapshot.get("binding_id") != binding_id:
        raise IntakeError("saved intake destination snapshot does not match its binding")
    if any(not isinstance(key, str) or not isinstance(value, str) or len(value) != 64 for key, value in hashes.items()):
        raise IntakeError("saved intake destination evidence hashes are invalid")
    if _snapshot_reference_from_evidence(evidence) != snapshot_reference:
        raise IntakeError("saved intake destination snapshot does not match its evidence")


def _selection_decision_reference(
    repository: str, source_selection: str, source_ref: str, source_commit: str,
    overview_path: str, publication_branch: str, destination_snapshot_reference: str | None,
) -> str:
    if destination_snapshot_reference is None:
        raise IntakeError("saved intake destination snapshot reference is missing")
    return hashlib.sha256(_canonical_json({
        "kind": "registration_source_selection_v1",
        "repository": repository,
        "source_selection": source_selection,
        "source_ref": source_ref,
        "source_commit": source_commit,
        "overview_path": overview_path,
        "publication_branch": publication_branch,
        "destination_snapshot_reference": destination_snapshot_reference,
    }).encode("utf-8")).hexdigest()


def _durable_evidence(result: GitHubDestinationAuthorization) -> Mapping[str, object]:
    """Deep-freeze persistable provider evidence while it still owns its token."""
    copied = json.loads(json.dumps(result.durable_record(), sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False))
    return _FrozenEvidence(copied)


def _optional_text(record: Mapping[str, object], field: str) -> str | None:
    value = record.get(field)
    if value is not None and not isinstance(value, str):
        raise IntakeError(f"saved intake {field} is invalid")
    return value


def _canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def _record_digest(record: Mapping[str, object]) -> str:
    return hashlib.sha256(_canonical_json(record).encode("utf-8")).hexdigest()


def _plain_json(value: object) -> object:
    if isinstance(value, MappingABC):
        if any(not isinstance(key, str) for key in value):
            raise IntakeError("saved intake JSON object keys must be text")
        return {key: _plain_json(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_plain_json(item) for item in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise IntakeError("saved intake contains a non-JSON value")


def _freeze_json_evidence(value: Mapping[str, object]) -> Mapping[str, object]:
    try:
        copied = json.loads(_canonical_json(_plain_json(value)))
    except (TypeError, ValueError, json.JSONDecodeError) as error:
        raise IntakeError("saved intake destination evidence is invalid") from error
    if not isinstance(copied, dict):
        raise IntakeError("saved intake destination evidence is invalid")
    return _FrozenEvidence(copied)


class _FrozenEvidence(MappingABC[str, object]):
    """A JSON-shaped, deep-immutable mapping for durable intake evidence."""

    __slots__ = ("_values",)

    def __init__(self, values: Mapping[str, object]) -> None:
        object.__setattr__(self, "_values", tuple((key, _freeze_evidence(value)) for key, value in values.items()))

    def __setattr__(self, _name: str, _value: object) -> None:
        raise TypeError("destination evidence is immutable")

    def __getitem__(self, key: str) -> object:
        for candidate, value in self._values:
            if candidate == key:
                return value
        raise KeyError(key)

    def __iter__(self) -> Iterator[str]:
        return (key for key, _value in self._values)

    def __len__(self) -> int:
        return len(self._values)


def _freeze_evidence(value: object) -> object:
    if isinstance(value, MappingABC):
        return _FrozenEvidence(value)
    if isinstance(value, list):
        return tuple(_freeze_evidence(item) for item in value)
    return value
