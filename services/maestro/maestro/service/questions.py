"""Durable linked questions, answers, and recipient delivery.

Questions use the activity projection for their visible record and keep answer
choices, linkage, and delivery state in this domain.  Answer acceptance runs in
the transaction owned by :class:`RequestService`; recipient calls happen only
after that transaction has committed.
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol
from urllib.parse import unquote, urlsplit

from maestro.foundation import (
    ContractError,
    Database,
    DomainMigration,
    Transaction,
    canonical_identifier,
    positive_version,
)

from .activities import (
    ActivityRecord,
    ActivityRepository,
    ConversationRecord,
    ProjectRecord,
    QuestionRecord,
    RecordReferenceError,
)
from .authentication import HTTPRejection
from .http import HTTPResponse, RequestHTTPApplication
from .registry import OperationHandler, OperationResult, PreparedOperation
from .requests import RequestEnvelope, RequestRejection, RequestService


QUESTION_MIGRATION = DomainMigration(
    domain="service_questions",
    version=1,
    identity="service-linked-questions-v1",
    statements=(
        """
        CREATE TABLE service_question_details(
            question_id TEXT PRIMARY KEY
                REFERENCES service_questions(question_id) ON DELETE RESTRICT,
            recipient TEXT NOT NULL,
            original_question_id TEXT
                REFERENCES service_questions(question_id) ON DELETE RESTRICT,
            previous_answer_id TEXT
                REFERENCES service_question_answers(answer_id) ON DELETE RESTRICT,
            allow_free_text INTEGER NOT NULL CHECK(allow_free_text IN (0, 1)),
            CHECK(
                (original_question_id IS NULL AND previous_answer_id IS NULL)
                OR
                (original_question_id IS NOT NULL AND previous_answer_id IS NOT NULL)
            )
        )
        """,
        """
        CREATE TABLE service_question_choices(
            question_id TEXT NOT NULL
                REFERENCES service_question_details(question_id) ON DELETE RESTRICT,
            choice_id TEXT NOT NULL,
            label TEXT NOT NULL,
            tradeoff TEXT NOT NULL,
            recommendation_reason TEXT,
            position INTEGER NOT NULL CHECK(position >= 0),
            PRIMARY KEY(question_id, choice_id),
            UNIQUE(question_id, position)
        )
        """,
        """
        CREATE TABLE service_question_answers(
            answer_id TEXT PRIMARY KEY,
            request_id TEXT NOT NULL UNIQUE
                REFERENCES request_receipts(request_id) ON DELETE RESTRICT,
            question_id TEXT NOT NULL UNIQUE
                REFERENCES service_questions(question_id) ON DELETE RESTRICT,
            project_id TEXT NOT NULL,
            activity_id TEXT NOT NULL,
            question_version INTEGER NOT NULL CHECK(question_version > 0),
            text TEXT NOT NULL,
            choice_id TEXT,
            answered_at TEXT NOT NULL,
            FOREIGN KEY(question_id, choice_id)
                REFERENCES service_question_choices(question_id, choice_id)
                ON DELETE RESTRICT
        )
        """,
        """
        CREATE TABLE service_question_deliveries(
            answer_id TEXT PRIMARY KEY
                REFERENCES service_question_answers(answer_id) ON DELETE RESTRICT,
            recipient TEXT NOT NULL,
            state TEXT NOT NULL CHECK(state IN ('pending', 'delivered')),
            attempts INTEGER NOT NULL DEFAULT 0 CHECK(attempts >= 0),
            delivered_at TEXT
        )
        """,
        """
        CREATE INDEX service_question_delivery_pending
            ON service_question_deliveries(state, answer_id)
        """,
    ),
)


@dataclass(frozen=True)
class AnswerChoice:
    choice_id: str
    label: str
    tradeoff: str
    recommendation_reason: str | None = None


@dataclass(frozen=True)
class LinkedQuestion:
    question_id: str
    project_id: str
    activity_id: str
    subject: str
    prompt: str
    requester: str
    recipient: str
    version: int = 1
    choices: tuple[AnswerChoice, ...] = ()
    allow_free_text: bool = True
    original_question_id: str | None = None
    previous_answer_id: str | None = None


@dataclass(frozen=True)
class DeliveredAnswer:
    answer_id: str
    request_id: str
    question_id: str
    project_id: str
    activity_id: str
    recipient: str
    question_version: int
    text: str
    choice_id: str | None
    original_question_id: str | None
    previous_answer_id: str | None


class Recipient(Protocol):
    def __call__(self, answer: DeliveredAnswer) -> None: ...


class RecipientDeliveryInterrupted(RuntimeError):
    """Delivery remains pending and can be retried with the same answer identity."""


class QuestionService:
    """Question domain repository, request handler, and delivery coordinator."""

    def __init__(
        self,
        database: Database,
        recipients: Mapping[str, Recipient] | None = None,
    ) -> None:
        if not isinstance(database, Database):
            raise TypeError("question service requires the service Database")
        self.database = database
        self.records = ActivityRepository(database)
        database.registry.register(QUESTION_MIGRATION)
        database.initialize()
        self._recipients = dict(recipients or {})
        for identity, recipient in self._recipients.items():
            canonical_identifier(identity, "recipient")
            if not callable(recipient):
                raise TypeError("question recipient must be callable")

    def register_recipient(self, identity: str, recipient: Recipient) -> None:
        """Add a process's answer recipient after construction (the process needs this service first)."""
        canonical_identifier(identity, "recipient")
        if not callable(recipient):
            raise TypeError("question recipient must be callable")
        self._recipients[identity] = recipient

    @property
    def operation_handler(self) -> OperationHandler:
        return OperationHandler("question.answer", self.prepare_answer)

    @property
    def publish_operation_handler(self) -> OperationHandler:
        return OperationHandler("question.publish", self.prepare_publish)

    @property
    def bootstrap_operation_handler(self) -> OperationHandler:
        return OperationHandler("project.bootstrap", self.prepare_bootstrap)

    @property
    def operation_handlers(self) -> tuple[OperationHandler, ...]:
        return (
            self.bootstrap_operation_handler,
            self.publish_operation_handler,
            self.operation_handler,
        )

    def prepare_bootstrap(self, request: RequestEnvelope) -> PreparedOperation:
        if request.project_id is None or request.activity_id is None:
            raise ValueError("project.bootstrap requires project and activity context")
        if request.question_id is not None:
            raise ValueError("project.bootstrap does not accept question context")
        if request.expected_version != 0:
            raise ValueError("project.bootstrap expected_version must be zero")
        if set(request.payload) != {"project_name", "activity_subject"}:
            raise ValueError(
                "project.bootstrap payload requires project_name and activity_subject"
            )
        if request.project_id == request.activity_id:
            raise ValueError("project and activity identities must be distinct")
        project_name = request.payload["project_name"]
        activity_subject = request.payload["activity_subject"]
        if not isinstance(project_name, str) or not project_name.strip():
            raise ValueError("project_name must be nonempty text")
        if not isinstance(activity_subject, str) or not activity_subject.strip():
            raise ValueError("activity_subject must be nonempty text")

        project = ProjectRecord(
            request.project_id,
            project_name,
            "unregistered",
            1,
        )
        activity = ActivityRecord(
            request.activity_id,
            request.project_id,
            "generic",
            activity_subject,
            "waiting",
            1,
        )

        def apply(transaction: Transaction, next_version: int) -> OperationResult:
            if next_version != 1:
                raise RequestRejection(
                    409,
                    "project_already_exists",
                    "the project identity is already in use",
                    fields={"project_id": project.project_id},
                )
            if transaction.execute(
                "SELECT 1 FROM service_projects WHERE project_id = ?",
                (project.project_id,),
            ).fetchone() is not None:
                raise RequestRejection(
                    409,
                    "project_already_exists",
                    "the project identity is already in use",
                    fields={"project_id": project.project_id},
                )
            if transaction.execute(
                "SELECT 1 FROM service_activities WHERE activity_id = ?",
                (activity.activity_id,),
            ).fetchone() is not None or transaction.current_version(
                activity.activity_id
            ) != 0:
                raise RequestRejection(
                    409,
                    "activity_already_exists",
                    "the activity identity is already in use",
                    fields={"activity_id": activity.activity_id},
                )
            self.records.create_project(transaction, project)
            self.records.create_activity(transaction, activity)
            transaction.execute(
                "INSERT INTO entity_versions(entity_id, version) VALUES (?, ?)",
                (activity.activity_id, activity.version),
            )
            return OperationResult(
                data={
                    "project_id": project.project_id,
                    "activity_id": activity.activity_id,
                    "registration_status": project.registration_status,
                    "activity_kind": activity.kind,
                    "activity_state": activity.state,
                },
                project_id=project.project_id,
                activity_id=activity.activity_id,
            )

        return PreparedOperation(
            entity_id=project.project_id,
            event_type="project.bootstrapped",
            event_data={
                "project_id": project.project_id,
                "activity_id": activity.activity_id,
            },
            apply=apply,
        )

    def prepare_publish(self, request: RequestEnvelope) -> PreparedOperation:
        if (
            request.project_id is None
            or request.activity_id is None
            or request.question_id is None
        ):
            raise ValueError(
                "question.publish requires project, activity, and question context"
            )
        if request.expected_version != 0:
            raise ValueError("question.publish expected_version must be zero")
        required = {
            "subject",
            "prompt",
            "requester",
            "recipient",
            "choices",
            "allow_free_text",
            "original_question_id",
            "previous_answer_id",
        }
        if set(request.payload) != required:
            raise ValueError("question.publish payload fields do not match the contract")
        choices_value = request.payload["choices"]
        if not isinstance(choices_value, list):
            raise ValueError("question.publish choices must be a list")
        choices: list[AnswerChoice] = []
        choice_fields = {
            "choice_id",
            "label",
            "tradeoff",
            "recommendation_reason",
        }
        for value in choices_value:
            if not isinstance(value, Mapping) or set(value) != choice_fields:
                raise ValueError(
                    "question.publish choice fields do not match the contract"
                )
            choices.append(
                AnswerChoice(
                    choice_id=value["choice_id"],  # type: ignore[arg-type]
                    label=value["label"],  # type: ignore[arg-type]
                    tradeoff=value["tradeoff"],  # type: ignore[arg-type]
                    recommendation_reason=value["recommendation_reason"],  # type: ignore[arg-type]
                )
            )
        question = LinkedQuestion(
            question_id=request.question_id,
            project_id=request.project_id,
            activity_id=request.activity_id,
            subject=request.payload["subject"],  # type: ignore[arg-type]
            prompt=request.payload["prompt"],  # type: ignore[arg-type]
            requester=request.payload["requester"],  # type: ignore[arg-type]
            recipient=request.payload["recipient"],  # type: ignore[arg-type]
            choices=tuple(choices),
            allow_free_text=request.payload["allow_free_text"],  # type: ignore[arg-type]
            original_question_id=request.payload["original_question_id"],  # type: ignore[arg-type]
            previous_answer_id=request.payload["previous_answer_id"],  # type: ignore[arg-type]
        )
        self._validate_question(question)

        def apply(transaction: Transaction, next_version: int) -> OperationResult:
            if next_version != 1:
                raise RequestRejection(
                    409,
                    "question_already_exists",
                    "the question identity is already in use",
                    fields={"question_id": question.question_id},
                )
            try:
                self.publish(transaction, question)
            except RecordReferenceError as error:
                status = 404 if error.code.endswith("_not_found") else 409
                raise RequestRejection(
                    status,
                    error.code,
                    str(error),
                    fields=error.fields,
                ) from error
            except ValueError as error:
                raise RequestRejection(
                    409,
                    "invalid_question_link",
                    str(error),
                    fields={"question_id": question.question_id},
                ) from error
            return OperationResult(
                data={
                    "question_id": question.question_id,
                    "question_status": (
                        "clarification_required"
                        if question.original_question_id is not None
                        else "awaiting_answer"
                    ),
                },
                project_id=question.project_id,
                activity_id=question.activity_id,
            )

        return PreparedOperation(
            entity_id=question.question_id,
            event_type="question.published",
            event_data={"question_id": question.question_id},
            apply=apply,
        )

    def publish(self, transaction: Transaction, question: LinkedQuestion) -> None:
        """Publish a visible question and its answer contract atomically."""
        self._validate_question(question)
        if question.original_question_id is not None:
            self._validate_follow_up(transaction, question)
        status = (
            "clarification_required"
            if question.original_question_id is not None
            else "awaiting_answer"
        )
        self.records.create_question(
            transaction,
            QuestionRecord(
                question.question_id,
                question.project_id,
                question.activity_id,
                question.subject,
                question.prompt,
                question.requester,
                status,
                question.version,
            ),
        )
        transaction.execute(
            """
            INSERT INTO service_question_details(
                question_id, recipient, original_question_id,
                previous_answer_id, allow_free_text
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                question.question_id,
                question.recipient,
                question.original_question_id,
                question.previous_answer_id,
                int(question.allow_free_text),
            ),
        )
        transaction.executemany(
            """
            INSERT INTO service_question_choices(
                question_id, choice_id, label, tradeoff,
                recommendation_reason, position
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            tuple(
                (
                    question.question_id,
                    choice.choice_id,
                    choice.label,
                    choice.tradeoff,
                    choice.recommendation_reason,
                    position,
                )
                for position, choice in enumerate(question.choices)
            ),
        )
        transaction.execute(
            "INSERT INTO entity_versions(entity_id, version) VALUES (?, ?)",
            (question.question_id, question.version),
        )

    def prepare_answer(self, request: RequestEnvelope) -> PreparedOperation:
        if (
            request.project_id is None
            or request.activity_id is None
            or request.question_id is None
        ):
            raise ValueError(
                "question.answer requires project, activity, and question context"
            )
        if request.expected_version is None:
            raise ValueError("question.answer requires expected_version")
        if set(request.payload) != {"text", "choice_id"}:
            raise ValueError("question.answer payload requires text and choice_id")
        text = request.payload["text"]
        choice_id = request.payload["choice_id"]
        if not isinstance(text, str) or not text.strip():
            raise ValueError("answer text must be nonempty")
        if choice_id is not None:
            canonical_identifier(choice_id, "choice_id")  # type: ignore[arg-type]

        def apply(transaction: Transaction, next_version: int) -> OperationResult:
            return self._accept_answer(
                transaction, request, next_version, text.strip(), choice_id
            )

        return PreparedOperation(
            entity_id=request.question_id,
            event_type="question.answered",
            event_data={
                "question_id": request.question_id,
                "request_id": request.request_id,
            },
            apply=apply,
        )

    def question(self, question_id: str) -> dict[str, object]:
        canonical_identifier(question_id, "question_id")
        with self.database.read_connection() as connection:
            row = connection.execute(
                """
                SELECT q.question_id, q.project_id, q.activity_id, q.subject,
                       q.prompt, q.requester, q.status, q.version,
                       d.recipient, d.original_question_id,
                       d.previous_answer_id, d.allow_free_text
                FROM service_questions AS q
                JOIN service_question_details AS d USING(question_id)
                WHERE q.question_id = ?
                """,
                (question_id,),
            ).fetchone()
            if row is None:
                raise RequestRejection(
                    404,
                    "question_not_found",
                    "the requested question was not found",
                    fields={"question_id": question_id},
                )
            choices = connection.execute(
                """
                SELECT choice_id, label, tradeoff, recommendation_reason
                FROM service_question_choices
                WHERE question_id = ? ORDER BY position
                """,
                (question_id,),
            ).fetchall()
        return {
            "question_id": str(row[0]),
            "project_id": str(row[1]),
            "activity_id": str(row[2]),
            "subject": str(row[3]),
            "prompt": str(row[4]),
            "requester": str(row[5]),
            "status": str(row[6]),
            "version": int(row[7]),
            "recipient": str(row[8]),
            "original_question_id": None if row[9] is None else str(row[9]),
            "previous_answer_id": None if row[10] is None else str(row[10]),
            "allow_free_text": bool(row[11]),
            "choices": [
                {
                    "choice_id": str(choice[0]),
                    "label": str(choice[1]),
                    "tradeoff": str(choice[2]),
                    "recommendation_reason": (
                        None if choice[3] is None else str(choice[3])
                    ),
                }
                for choice in choices
            ],
        }

    def deliver_answer(self, answer_id: str) -> bool:
        """Deliver one pending answer; repeat calls reconcile by answer identity."""
        canonical_identifier(answer_id, "answer_id")
        answer = self._pending_answer(answer_id)
        if answer is None:
            return False
        recipient = self._recipients.get(answer.recipient)
        if recipient is None:
            raise RecipientDeliveryInterrupted(
                f"question recipient is unavailable: {answer.recipient}"
            )
        with self.database.transaction() as transaction:
            transaction.execute(
                """
                UPDATE service_question_deliveries
                SET attempts = attempts + 1
                WHERE answer_id = ? AND state = 'pending'
                """,
                (answer_id,),
            )
        try:
            recipient(answer)
        except Exception as error:
            raise RecipientDeliveryInterrupted(
                "answer delivery was interrupted; retry uses the same answer identity"
            ) from error
        with self.database.transaction() as transaction:
            transaction.execute(
                """
                UPDATE service_question_deliveries
                SET state = 'delivered', delivered_at = ?
                WHERE answer_id = ? AND state = 'pending'
                """,
                (_utc_now(), answer_id),
            )
        return True

    def deliver_pending(self) -> tuple[str, ...]:
        with self.database.read_connection() as connection:
            identities = tuple(
                str(row[0])
                for row in connection.execute(
                    """
                    SELECT answer_id FROM service_question_deliveries
                    WHERE state = 'pending' ORDER BY answer_id
                    """
                ).fetchall()
            )
        delivered: list[str] = []
        for identity in identities:
            if self.deliver_answer(identity):
                delivered.append(identity)
        return tuple(delivered)

    def _accept_answer(
        self,
        transaction: Transaction,
        request: RequestEnvelope,
        next_version: int,
        text: str,
        choice_id: object,
    ) -> OperationResult:
        assert request.project_id is not None
        assert request.activity_id is not None
        assert request.question_id is not None
        row = transaction.execute(
            """
            SELECT q.project_id, q.activity_id, q.subject, q.prompt,
                   q.requester, q.status, q.version, d.recipient,
                   d.allow_free_text
            FROM service_questions AS q
            JOIN service_question_details AS d USING(question_id)
            WHERE q.question_id = ?
            """,
            (request.question_id,),
        ).fetchone()
        if row is None:
            raise RequestRejection(
                404,
                "question_not_found",
                "the answered question was not found",
                fields={"question_id": request.question_id},
            )
        if (str(row[0]), str(row[1])) != (
            request.project_id,
            request.activity_id,
        ):
            raise RequestRejection(
                409,
                "wrong_question_context",
                "the question belongs to another project or activity",
                fields={
                    "project_id": request.project_id,
                    "activity_id": request.activity_id,
                    "question_id": request.question_id,
                },
            )
        current_version = int(row[6])
        if request.expected_version != current_version:
            raise RequestRejection(
                409,
                "stale_question",
                "the question version is stale",
                fields={
                    "question_id": request.question_id,
                    "expected_version": request.expected_version,
                    "current_version": current_version,
                },
            )
        if str(row[5]) not in {"awaiting_answer", "clarification_required"}:
            raise RequestRejection(
                409,
                "question_not_awaiting_answer",
                "the question no longer accepts an answer",
                fields={"question_id": request.question_id},
            )
        if choice_id is None and not bool(row[8]):
            raise RequestRejection(
                409,
                "choice_required",
                "this question requires one of its available choices",
                fields={"question_id": request.question_id},
            )
        if choice_id is not None and transaction.execute(
            """
            SELECT 1 FROM service_question_choices
            WHERE question_id = ? AND choice_id = ?
            """,
            (request.question_id, choice_id),
        ).fetchone() is None:
            raise RequestRejection(
                409,
                "choice_not_available",
                "the selected choice is not available for this question",
                fields={"question_id": request.question_id, "choice_id": choice_id},
            )
        if next_version != current_version + 1:
            raise RequestRejection(
                409,
                "stale_question",
                "the question version is stale",
                fields={"question_id": request.question_id},
            )

        answer_id = request.request_id
        answered_at = _utc_now()
        transaction.execute(
            """
            INSERT INTO service_question_answers(
                answer_id, request_id, question_id, project_id, activity_id,
                question_version, text, choice_id, answered_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                answer_id,
                request.request_id,
                request.question_id,
                request.project_id,
                request.activity_id,
                next_version,
                text,
                choice_id,
                answered_at,
            ),
        )
        transaction.execute(
            """
            INSERT INTO service_question_deliveries(answer_id, recipient, state)
            VALUES (?, ?, 'pending')
            """,
            (answer_id, str(row[7])),
        )
        self.records.update_question(
            transaction,
            QuestionRecord(
                request.question_id,
                request.project_id,
                request.activity_id,
                str(row[2]),
                str(row[3]),
                str(row[4]),
                "answer_received",
                next_version,
            ),
            expected_record_version=current_version,
        )
        message_id = "answer-" + hashlib.sha256(
            request.request_id.encode("utf-8")
        ).hexdigest()
        self.records.append_conversation(
            transaction,
            ConversationRecord(
                message_id,
                request.project_id,
                "owner",
                "answer",
                text,
                answered_at,
                request.activity_id,
            ),
        )
        return OperationResult(
            data={
                "answer_id": answer_id,
                "question_id": request.question_id,
                "question_status": "answer_received",
                "delivery_status": "pending",
            },
            project_id=request.project_id,
            activity_id=request.activity_id,
        )

    def _pending_answer(self, answer_id: str) -> DeliveredAnswer | None:
        with self.database.read_connection() as connection:
            row = connection.execute(
                """
                SELECT a.answer_id, a.request_id, a.question_id, a.project_id,
                       a.activity_id, d.recipient, a.question_version, a.text,
                       a.choice_id, q.original_question_id, q.previous_answer_id
                FROM service_question_answers AS a
                JOIN service_question_deliveries AS d USING(answer_id)
                JOIN service_question_details AS q USING(question_id)
                WHERE a.answer_id = ? AND d.state = 'pending'
                """,
                (answer_id,),
            ).fetchone()
        if row is None:
            return None
        return DeliveredAnswer(
            answer_id=str(row[0]),
            request_id=str(row[1]),
            question_id=str(row[2]),
            project_id=str(row[3]),
            activity_id=str(row[4]),
            recipient=str(row[5]),
            question_version=int(row[6]),
            text=str(row[7]),
            choice_id=None if row[8] is None else str(row[8]),
            original_question_id=None if row[9] is None else str(row[9]),
            previous_answer_id=None if row[10] is None else str(row[10]),
        )

    @staticmethod
    def _validate_question(question: LinkedQuestion) -> None:
        if not isinstance(question, LinkedQuestion):
            raise TypeError("linked question is invalid")
        for name, value in (
            ("question_id", question.question_id),
            ("project_id", question.project_id),
            ("activity_id", question.activity_id),
            ("requester", question.requester),
            ("recipient", question.recipient),
        ):
            canonical_identifier(value, name)
        positive_version(question.version, "question version")
        if question.version != 1:
            raise ValueError("new questions must start at version 1")
        for name, value in (("subject", question.subject), ("prompt", question.prompt)):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"question {name} must be nonempty text")
        if not isinstance(question.allow_free_text, bool):
            raise TypeError("allow_free_text must be boolean")
        if not question.choices and not question.allow_free_text:
            raise ValueError("question must accept a choice or free text")
        seen: set[str] = set()
        for choice in question.choices:
            if not isinstance(choice, AnswerChoice):
                raise TypeError("answer choice is invalid")
            canonical_identifier(choice.choice_id, "choice_id")
            if choice.choice_id in seen:
                raise ValueError("answer choice identities must be unique")
            seen.add(choice.choice_id)
            for name, value in (("label", choice.label), ("tradeoff", choice.tradeoff)):
                if not isinstance(value, str) or not value.strip():
                    raise ValueError(f"choice {name} must be nonempty text")
            if choice.recommendation_reason is not None and (
                not isinstance(choice.recommendation_reason, str)
                or not choice.recommendation_reason.strip()
            ):
                raise ValueError("recommendation reason must be nonempty text")
        linked = (question.original_question_id, question.previous_answer_id)
        if (linked[0] is None) != (linked[1] is None):
            raise ValueError(
                "follow-up requires original_question_id and previous_answer_id"
            )
        for name, value in (
            ("original_question_id", question.original_question_id),
            ("previous_answer_id", question.previous_answer_id),
        ):
            if value is not None:
                canonical_identifier(value, name)

    @staticmethod
    def _validate_follow_up(
        transaction: Transaction, question: LinkedQuestion
    ) -> None:
        row = transaction.execute(
            """
            SELECT a.question_id, d.original_question_id, a.project_id,
                   a.activity_id, d.recipient
            FROM service_question_answers AS a
            JOIN service_question_details AS d USING(question_id)
            WHERE a.answer_id = ?
            """,
            (question.previous_answer_id,),
        ).fetchone()
        previous_root = (
            None if row is None or row[1] is None else str(row[1])
        )
        if row is None or (previous_root or str(row[0])) != question.original_question_id:
            raise ValueError("follow-up does not link to the original saved answer")
        if (str(row[2]), str(row[3]), str(row[4])) != (
            question.project_id,
            question.activity_id,
            question.recipient,
        ):
            raise ValueError("follow-up context or recipient does not match")


class QuestionRequestService:
    """Request boundary that attempts recipient delivery only after commit."""

    def __init__(self, requests: RequestService, questions: QuestionService) -> None:
        self.requests = requests
        self.questions = questions

    def submit(self, authorization: str | None, body: Mapping[str, object]):
        receipt = self.requests.submit(authorization, body)
        if body.get("operation") == "question.answer":
            try:
                self.questions.deliver_answer(receipt.request_id)
            except RecipientDeliveryInterrupted:
                pass
        return receipt

    def lookup(self, authorization: str | None, request_id: str):
        return self.requests.lookup(authorization, request_id)

    def authenticate_write(self, authorization: str | None) -> None:
        self.requests.authenticate_write(authorization)

    def authenticate_read(self, authorization: str | None) -> None:
        self.requests.authenticate_read(authorization)


class QuestionHTTPApplication:
    """Question read route composed with the shared durable request routes."""

    def __init__(
        self, request_service: QuestionRequestService, questions: QuestionService
    ) -> None:
        self._requests = request_service
        self._questions = questions
        self._base = RequestHTTPApplication(request_service)  # type: ignore[arg-type]

    def handle(
        self,
        method: str,
        path: str,
        headers: Mapping[str, str],
        body: bytes = b"",
    ) -> HTTPResponse:
        parsed = urlsplit(path)
        prefix = "/api/v1/questions/"
        if method != "GET" or not parsed.path.startswith(prefix):
            return self._base.handle(method, path, headers, body)
        try:
            if parsed.query or parsed.fragment:
                raise RequestRejection(404, "not_found", "the API route was not found")
            encoded = parsed.path[len(prefix) :]
            if not encoded or "/" in encoded:
                raise RequestRejection(404, "not_found", "the API route was not found")
            self._requests.authenticate_read(headers.get("Authorization"))
            question_id = unquote(encoded)
            try:
                canonical_identifier(question_id, "question_id")
            except (ContractError, TypeError) as error:
                raise RequestRejection(
                    400,
                    "invalid_request",
                    "question_id is not a canonical identifier",
                    fields={"question_id": question_id},
                ) from error
            return HTTPResponse(
                200,
                {"data": self._questions.question(question_id)},
                {"Content-Type": "application/json; charset=utf-8"},
            )
        except HTTPRejection as error:
            response_headers = {"Content-Type": "application/json; charset=utf-8"}
            response_headers.update(error.headers)
            return HTTPResponse(error.status_code, error.as_body(), response_headers)


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
