"""Durable public request receipts backed by the service database."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Mapping

from maestro.foundation import Database, DomainMigration, Transaction, canonical_json

from .registry import OperationResult


REQUEST_MIGRATION = DomainMigration(
    domain="service_requests",
    version=1,
    identity="service-request-results-v1",
    statements=(
        """
        CREATE TABLE service_request_results(
            request_id TEXT PRIMARY KEY
                REFERENCES request_receipts(request_id) ON DELETE RESTRICT,
            status TEXT NOT NULL
                CHECK(status IN ('accepted', 'completed', 'rejected')),
            project_id TEXT,
            activity_id TEXT,
            event_id TEXT NOT NULL UNIQUE,
            result_json TEXT NOT NULL
        )
        """,
    ),
)


class ReceiptDataError(RuntimeError):
    """Raised when a saved receipt projection is incomplete or corrupt."""


@dataclass(frozen=True)
class RequestReceipt:
    request_id: str
    status: str
    entity_id: str
    resulting_version: int
    event_id: str
    result: Mapping[str, object]
    project_id: str | None = None
    activity_id: str | None = None

    def as_dict(self) -> dict[str, object]:
        value: dict[str, object] = {
            "request_id": self.request_id,
            "status": self.status,
            "entity_id": self.entity_id,
            "resulting_version": self.resulting_version,
            "event_id": self.event_id,
            "result": dict(self.result),
        }
        if self.project_id is not None:
            value["project_id"] = self.project_id
        if self.activity_id is not None:
            value["activity_id"] = self.activity_id
        return value


class ReceiptRepository:
    """Read and write request receipt projections at the shared SQL boundary."""

    def __init__(self, database: Database) -> None:
        self._database = database

    @staticmethod
    def save_result(
        transaction: Transaction,
        request_id: str,
        event_id: str,
        result: OperationResult,
    ) -> None:
        transaction.execute(
            """
            INSERT INTO service_request_results(
                request_id, status, project_id, activity_id, event_id, result_json
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                request_id,
                result.status,
                result.project_id,
                result.activity_id,
                event_id,
                canonical_json(result.data),
            ),
        )

    def find(self, request_id: str) -> tuple[RequestReceipt, str] | None:
        with self._database.read_connection() as connection:
            row = connection.execute(
                """
                SELECT r.request_id, s.status, r.entity_id, r.resulting_version,
                       s.event_id, s.result_json, s.project_id, s.activity_id,
                       r.content_digest
                FROM request_receipts AS r
                LEFT JOIN service_request_results AS s USING(request_id)
                WHERE r.request_id = ?
                """,
                (request_id,),
            ).fetchone()
        if row is None:
            return None
        if row[1] is None:
            raise ReceiptDataError("saved request receipt has no public result")
        try:
            result = json.loads(str(row[5]))
        except (TypeError, ValueError, json.JSONDecodeError) as error:
            raise ReceiptDataError("saved request result is invalid") from error
        if not isinstance(result, dict):
            raise ReceiptDataError("saved request result is not an object")
        return (
            RequestReceipt(
                request_id=str(row[0]),
                status=str(row[1]),
                entity_id=str(row[2]),
                resulting_version=int(row[3]),
                event_id=str(row[4]),
                result=result,
                project_id=None if row[6] is None else str(row[6]),
                activity_id=None if row[7] is None else str(row[7]),
            ),
            str(row[8]),
        )
