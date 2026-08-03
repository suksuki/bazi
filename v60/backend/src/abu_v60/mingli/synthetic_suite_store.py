from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.engine import Engine

from abu_v60.mingli.synthetic_suite_contracts import SyntheticSuiteRunIdentity
from abu_v60.provenance import canonical_json, content_hash, stable_ref


class MingliSyntheticSuiteRunStoreError(ValueError):
    pass


class MingliSyntheticSuiteRunStore:
    """Append-only ledger for one ordered synthetic training execution."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def ensure(self, *, identity: SyntheticSuiteRunIdentity) -> dict[str, Any]:
        payload = identity.model_dump(mode="json")
        suite_run_ref = stable_ref("v60-mingli-synthetic-suite-run", payload)
        suite_run_hash = content_hash(payload)
        with self._engine.begin() as connection:
            connection.execute(
                text(
                    """
                    INSERT INTO mingli.synthetic_suite_runs
                        (suite_run_ref, suite_run_version, suite_ref,
                         suite_definition_hash, suite_mode, runner_version,
                         status, experiment_count, sealed_count, error_count,
                         review_required_count, run_json, run_hash)
                    VALUES
                        (:suite_run_ref, :suite_run_version, :suite_ref,
                         :suite_definition_hash, :suite_mode, :runner_version,
                         :status, :experiment_count, :sealed_count, :error_count,
                         :review_required_count, CAST(:run_json AS jsonb), :run_hash)
                    ON CONFLICT (suite_run_ref) DO NOTHING
                    """
                ),
                {
                    "suite_run_ref": suite_run_ref,
                    "suite_run_version": payload["suite_run_version"],
                    "suite_ref": payload["suite_ref"],
                    "suite_definition_hash": payload["suite_definition_hash"],
                    "suite_mode": payload["suite_mode"],
                    "runner_version": payload["runner_version"],
                    "status": payload["status"],
                    "experiment_count": payload["counts"]["experiments"],
                    "sealed_count": payload["counts"]["sealed"],
                    "error_count": payload["counts"]["runner_errors"],
                    "review_required_count": payload["counts"]["review_required"],
                    "run_json": canonical_json(payload),
                    "run_hash": suite_run_hash,
                },
            )
        stored = self.get(suite_run_ref=suite_run_ref)
        if stored is None or stored["suite_run_hash"] != suite_run_hash:
            raise MingliSyntheticSuiteRunStoreError("mingli_synthetic_suite_run_conflict")
        return stored

    def latest(self, *, suite_ref: str) -> dict[str, Any] | None:
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    text(
                        f"""
                        {self._select_sql()}
                        WHERE suite_ref = :suite_ref
                        ORDER BY created_at DESC, suite_run_ref DESC
                        LIMIT 1
                        """
                    ),
                    {"suite_ref": suite_ref},
                )
                .mappings()
                .one_or_none()
            )
        return None if row is None else self._validated(dict(row))

    def history(
        self,
        *,
        suite_ref: str,
        limit: int = 12,
    ) -> tuple[dict[str, Any], ...]:
        if limit < 1 or limit > 50:
            raise ValueError("mingli_synthetic_suite_history_limit_invalid")
        with self._engine.connect() as connection:
            rows = (
                connection.execute(
                    text(
                        f"""
                        {self._select_sql()}
                        WHERE suite_ref = :suite_ref
                        ORDER BY created_at DESC, suite_run_ref DESC
                        LIMIT :limit
                        """
                    ),
                    {"suite_ref": suite_ref, "limit": limit},
                )
                .mappings()
                .all()
            )
        return tuple(self._validated(dict(row)) for row in rows)

    def get(self, *, suite_run_ref: str) -> dict[str, Any] | None:
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    text(f"{self._select_sql()} WHERE suite_run_ref = :suite_run_ref"),
                    {"suite_run_ref": suite_run_ref},
                )
                .mappings()
                .one_or_none()
            )
        return None if row is None else self._validated(dict(row))

    @staticmethod
    def _select_sql() -> str:
        return """
            SELECT suite_run_ref, suite_run_version, suite_ref,
                   suite_definition_hash, suite_mode, runner_version,
                   status, experiment_count, sealed_count, error_count,
                   review_required_count, run_json, run_hash, created_at
            FROM mingli.synthetic_suite_runs
        """

    @staticmethod
    def _validated(row: dict[str, Any]) -> dict[str, Any]:
        payload = row["run_json"]
        identity = SyntheticSuiteRunIdentity.model_validate(payload)
        scalar_bindings = {
            "suite_run_version": identity.suite_run_version,
            "suite_ref": identity.suite_ref,
            "suite_definition_hash": identity.suite_definition_hash,
            "suite_mode": identity.suite_mode,
            "runner_version": identity.runner_version,
            "status": identity.status,
            "experiment_count": identity.counts.experiments,
            "sealed_count": identity.counts.sealed,
            "error_count": identity.counts.runner_errors,
            "review_required_count": identity.counts.review_required,
        }
        if any(row[key] != value for key, value in scalar_bindings.items()):
            raise MingliSyntheticSuiteRunStoreError("mingli_synthetic_suite_run_row_mismatch")
        if row["run_hash"] != content_hash(payload):
            raise MingliSyntheticSuiteRunStoreError("mingli_synthetic_suite_run_hash_mismatch")
        if row["suite_run_ref"] != stable_ref("v60-mingli-synthetic-suite-run", payload):
            raise MingliSyntheticSuiteRunStoreError("mingli_synthetic_suite_run_ref_mismatch")
        return {
            "suite_run_ref": row["suite_run_ref"],
            "suite_run_hash": row["run_hash"],
            "created_at": row["created_at"],
            **payload,
        }
