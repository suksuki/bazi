from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from sqlalchemy import text
from sqlalchemy.engine import Engine

from abu_v60.mingli.synthetic_suite_contracts import SyntheticSuiteCandidateIdentity
from abu_v60.mingli.synthetic_training_contracts import (
    SYNTHETIC_SUITE_RUN_REQUEST_VERSION,
)
from abu_v60.provenance import canonical_json, content_hash, stable_ref


class SyntheticTrainingStoreError(ValueError):
    pass


_REQUEST_COLUMNS = """
request_ref, request_version, requester_account_ref,
suite_ref, suite_definition_hash,
candidate_identity_json, candidate_identity_hash,
execution_fingerprint, idempotency_key, request_hash,
status, progress_event, current_position,
completed_count, total_count, current_experiment_ref,
suite_run_ref, suite_run_hash, review_disposition, error_code,
created_at, updated_at
"""


class MingliSyntheticTrainingStore:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def ensure_queued(
        self,
        *,
        requester_account_ref: str,
        suite_ref: str,
        suite_definition_hash: str,
        candidate_identity: SyntheticSuiteCandidateIdentity,
        execution_fingerprint: str,
        idempotency_key: str,
        total_count: int,
    ) -> dict[str, Any]:
        candidate_json = candidate_identity.model_dump(mode="json")
        candidate_hash = content_hash(candidate_json)
        identity = {
            "request_version": SYNTHETIC_SUITE_RUN_REQUEST_VERSION,
            "requester_account_ref": requester_account_ref,
            "suite_ref": suite_ref,
            "suite_definition_hash": suite_definition_hash,
            "candidate_identity_hash": candidate_hash,
            "execution_fingerprint": execution_fingerprint,
            "idempotency_key": idempotency_key,
        }
        request_hash = content_hash(identity)
        request_ref = stable_ref("v60-mingli-synthetic-suite-run-request", identity)
        with self._engine.begin() as connection:
            connection.execute(
                text("SELECT pg_advisory_xact_lock(hashtextextended(:execution_fingerprint, 0))"),
                {"execution_fingerprint": execution_fingerprint},
            )
            active = (
                connection.execute(
                    text(
                        f"""
                        SELECT {_REQUEST_COLUMNS}
                        FROM mingli.synthetic_suite_run_requests
                        WHERE execution_fingerprint = :execution_fingerprint
                          AND status IN ('QUEUED', 'RUNNING', 'SEALING')
                        ORDER BY updated_at DESC, request_ref DESC
                        LIMIT 1
                        """
                    ),
                    {"execution_fingerprint": execution_fingerprint},
                )
                .mappings()
                .first()
            )
            if active is not None:
                if active["requester_account_ref"] != requester_account_ref:
                    raise SyntheticTrainingStoreError(
                        "mingli_synthetic_training_execution_already_active"
                    )
                return dict(active)
            connection.execute(
                text(
                    """
                    INSERT INTO mingli.synthetic_suite_run_requests
                        (request_ref, request_version, requester_account_ref,
                         suite_ref, suite_definition_hash,
                         candidate_identity_json, candidate_identity_hash,
                         execution_fingerprint, idempotency_key, request_hash,
                         status, progress_event, current_position,
                         completed_count, total_count)
                    VALUES
                        (:request_ref, :request_version, :requester_account_ref,
                         :suite_ref, :suite_definition_hash,
                         CAST(:candidate_identity_json AS jsonb), :candidate_identity_hash,
                         :execution_fingerprint, :idempotency_key, :request_hash,
                         'QUEUED', 'QUEUED', 0, 0, :total_count)
                    ON CONFLICT (requester_account_ref, idempotency_key) DO NOTHING
                    """
                ),
                {
                    "request_ref": request_ref,
                    "request_version": SYNTHETIC_SUITE_RUN_REQUEST_VERSION,
                    "requester_account_ref": requester_account_ref,
                    "suite_ref": suite_ref,
                    "suite_definition_hash": suite_definition_hash,
                    "candidate_identity_json": canonical_json(candidate_json),
                    "candidate_identity_hash": candidate_hash,
                    "execution_fingerprint": execution_fingerprint,
                    "idempotency_key": idempotency_key,
                    "request_hash": request_hash,
                    "total_count": total_count,
                },
            )
        stored = self.by_idempotency(
            requester_account_ref=requester_account_ref,
            idempotency_key=idempotency_key,
        )
        if stored is None:
            raise SyntheticTrainingStoreError("mingli_synthetic_training_request_missing")
        if any(
            stored[key] != expected
            for key, expected in {
                "request_ref": request_ref,
                "request_hash": request_hash,
                "suite_ref": suite_ref,
                "suite_definition_hash": suite_definition_hash,
                "candidate_identity_hash": candidate_hash,
                "execution_fingerprint": execution_fingerprint,
                "total_count": total_count,
            }.items()
        ):
            raise SyntheticTrainingStoreError("mingli_synthetic_training_idempotency_conflict")
        return stored

    def claim(self, *, request_ref: str) -> bool:
        with self._engine.begin() as connection:
            result = connection.execute(
                text(
                    """
                    UPDATE mingli.synthetic_suite_run_requests
                    SET status = 'RUNNING', progress_event = 'START',
                        updated_at = now()
                    WHERE request_ref = :request_ref AND status = 'QUEUED'
                    RETURNING request_ref
                    """
                ),
                {"request_ref": request_ref},
            ).first()
        return result is not None

    def record_progress(
        self,
        *,
        request_ref: str,
        event: str,
        position: int,
        total: int,
        experiment_ref: str,
    ) -> None:
        if event not in {"START", "SEALED", "ERROR"}:
            raise SyntheticTrainingStoreError("mingli_synthetic_training_event_invalid")
        completed = position if event in {"SEALED", "ERROR"} else max(0, position - 1)
        with self._engine.begin() as connection:
            result = connection.execute(
                text(
                    """
                    UPDATE mingli.synthetic_suite_run_requests
                    SET progress_event = :event,
                        current_position = :position,
                        completed_count = :completed,
                        current_experiment_ref = :experiment_ref,
                        updated_at = now()
                    WHERE request_ref = :request_ref
                      AND status = 'RUNNING'
                      AND total_count = :total
                    RETURNING request_ref
                    """
                ),
                {
                    "request_ref": request_ref,
                    "event": event,
                    "position": position,
                    "completed": completed,
                    "total": total,
                    "experiment_ref": experiment_ref,
                },
            ).first()
        if result is None:
            raise SyntheticTrainingStoreError("mingli_synthetic_training_progress_conflict")

    def mark_sealing(self, *, request_ref: str) -> None:
        with self._engine.begin() as connection:
            result = connection.execute(
                text(
                    """
                    UPDATE mingli.synthetic_suite_run_requests
                    SET status = 'SEALING', progress_event = 'SEALING',
                        completed_count = total_count, updated_at = now()
                    WHERE request_ref = :request_ref AND status = 'RUNNING'
                    RETURNING request_ref
                    """
                ),
                {"request_ref": request_ref},
            ).first()
        if result is None:
            raise SyntheticTrainingStoreError("mingli_synthetic_training_sealing_conflict")

    def succeed(
        self,
        *,
        request_ref: str,
        suite_run_ref: str,
        suite_run_hash: str,
        review_disposition: str,
    ) -> None:
        with self._engine.begin() as connection:
            result = connection.execute(
                text(
                    """
                    UPDATE mingli.synthetic_suite_run_requests
                    SET status = 'SUCCEEDED', progress_event = 'SUCCEEDED',
                        current_position = total_count,
                        completed_count = total_count,
                        current_experiment_ref = NULL,
                        suite_run_ref = :suite_run_ref,
                        suite_run_hash = :suite_run_hash,
                        review_disposition = :review_disposition,
                        error_code = NULL,
                        updated_at = now()
                    WHERE request_ref = :request_ref AND status = 'SEALING'
                    RETURNING request_ref
                    """
                ),
                {
                    "request_ref": request_ref,
                    "suite_run_ref": suite_run_ref,
                    "suite_run_hash": suite_run_hash,
                    "review_disposition": review_disposition,
                },
            ).first()
        if result is None:
            raise SyntheticTrainingStoreError("mingli_synthetic_training_success_conflict")

    def fail(self, *, request_ref: str, error_code: str) -> None:
        with self._engine.begin() as connection:
            connection.execute(
                text(
                    """
                    UPDATE mingli.synthetic_suite_run_requests
                    SET status = 'FAILED', progress_event = 'FAILED',
                        error_code = :error_code,
                        current_experiment_ref = NULL,
                        updated_at = now()
                    WHERE request_ref = :request_ref
                      AND status IN ('QUEUED', 'RUNNING', 'SEALING')
                    """
                ),
                {"request_ref": request_ref, "error_code": error_code},
            )

    def get(
        self,
        *,
        request_ref: str,
        requester_account_ref: str | None = None,
    ) -> dict[str, Any] | None:
        where = "request_ref = :request_ref"
        parameters: dict[str, object] = {"request_ref": request_ref}
        if requester_account_ref is not None:
            where += " AND requester_account_ref = :requester_account_ref"
            parameters["requester_account_ref"] = requester_account_ref
        return self._one(where=where, parameters=parameters)

    def by_idempotency(
        self,
        *,
        requester_account_ref: str,
        idempotency_key: str,
    ) -> dict[str, Any] | None:
        return self._one(
            where=(
                "requester_account_ref = :requester_account_ref "
                "AND idempotency_key = :idempotency_key"
            ),
            parameters={
                "requester_account_ref": requester_account_ref,
                "idempotency_key": idempotency_key,
            },
        )

    def latest(self, *, requester_account_ref: str) -> dict[str, Any] | None:
        return self._one(
            where="requester_account_ref = :requester_account_ref",
            parameters={"requester_account_ref": requester_account_ref},
            order="updated_at DESC, request_ref DESC",
        )

    def _one(
        self,
        *,
        where: str,
        parameters: Mapping[str, object],
        order: str | None = None,
    ) -> dict[str, Any] | None:
        order_sql = f" ORDER BY {order}" if order else ""
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    text(
                        f"""
                    SELECT {_REQUEST_COLUMNS}
                    FROM mingli.synthetic_suite_run_requests
                    WHERE {where}{order_sql}
                    LIMIT 1
                    """
                    ),
                    dict(parameters),
                )
                .mappings()
                .first()
            )
        return dict(row) if row is not None else None
