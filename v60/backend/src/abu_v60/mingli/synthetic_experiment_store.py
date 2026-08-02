from __future__ import annotations

from datetime import date
from typing import Any

from sqlalchemy import text
from sqlalchemy.engine import Engine

from abu_v60.mingli.synthetic_experiment_contracts import (
    SyntheticExperimentRunIdentity,
)
from abu_v60.provenance import canonical_json, content_hash, stable_ref


class MingliSyntheticExperimentRunStoreError(ValueError):
    pass


class MingliSyntheticExperimentRunStore:
    """Append-only sealed paired-experiment results owned by Mingli."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def ensure(self, *, identity: SyntheticExperimentRunIdentity) -> dict[str, Any]:
        payload = identity.model_dump(mode="json")
        run_ref = stable_ref("v60-mingli-synthetic-run", payload)
        run_hash = content_hash(payload)
        with self._engine.begin() as connection:
            connection.execute(
                text(
                    """
                    INSERT INTO mingli.synthetic_experiment_runs
                        (run_ref, run_version, experiment_ref, definition_hash,
                         evaluator_version, analysis_date,
                         member_a_agent_reading_ref,
                         member_b_agent_reading_ref,
                         member_a_stage_json, member_b_stage_json, outcome,
                         evaluation_json, run_hash)
                    VALUES
                        (:run_ref, :run_version, :experiment_ref, :definition_hash,
                         :evaluator_version, :analysis_date,
                         :member_a_agent_reading_ref,
                         :member_b_agent_reading_ref,
                         CAST(:member_a_stage_json AS jsonb),
                         CAST(:member_b_stage_json AS jsonb), :outcome,
                         CAST(:evaluation_json AS jsonb), :run_hash)
                    ON CONFLICT (run_ref) DO NOTHING
                    """
                ),
                {
                    **payload,
                    "analysis_date": date.fromisoformat(payload["analysis_date"]),
                    "member_a_stage_json": canonical_json(
                        payload["member_a_stage_json"]
                    ),
                    "member_b_stage_json": canonical_json(
                        payload["member_b_stage_json"]
                    ),
                    "evaluation_json": canonical_json(payload["evaluation_json"]),
                    "run_ref": run_ref,
                    "run_hash": run_hash,
                },
            )
        stored = self.get(run_ref=run_ref)
        if stored is None or stored["run_hash"] != run_hash:
            raise MingliSyntheticExperimentRunStoreError(
                "mingli_synthetic_experiment_run_conflict"
            )
        return stored

    def latest(self, *, experiment_ref: str) -> dict[str, Any] | None:
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    text(
                        f"""
                        {self._select_sql()}
                        WHERE experiment_ref = :experiment_ref
                        ORDER BY created_at DESC, run_ref DESC
                        LIMIT 1
                        """
                    ),
                    {"experiment_ref": experiment_ref},
                )
                .mappings()
                .one_or_none()
            )
        return None if row is None else self._validated(dict(row))

    def get(self, *, run_ref: str) -> dict[str, Any] | None:
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    text(f"{self._select_sql()} WHERE run_ref = :run_ref"),
                    {"run_ref": run_ref},
                )
                .mappings()
                .one_or_none()
            )
        return None if row is None else self._validated(dict(row))

    @staticmethod
    def _select_sql() -> str:
        return """
            SELECT run_ref, run_version, experiment_ref, definition_hash,
                   evaluator_version, analysis_date,
                   member_a_agent_reading_ref, member_b_agent_reading_ref,
                   member_a_stage_json, member_b_stage_json,
                   outcome, evaluation_json, run_hash, created_at
            FROM mingli.synthetic_experiment_runs
        """

    @staticmethod
    def _validated(row: dict[str, Any]) -> dict[str, Any]:
        identity = SyntheticExperimentRunIdentity.model_validate(
            {
                "run_version": row["run_version"],
                "experiment_ref": row["experiment_ref"],
                "definition_hash": row["definition_hash"],
                "evaluator_version": row["evaluator_version"],
                "analysis_date": row["analysis_date"].isoformat(),
                "member_a_agent_reading_ref": row["member_a_agent_reading_ref"],
                "member_b_agent_reading_ref": row["member_b_agent_reading_ref"],
                "member_a_stage_json": row["member_a_stage_json"],
                "member_b_stage_json": row["member_b_stage_json"],
                "outcome": row["outcome"],
                "evaluation_json": row["evaluation_json"],
            }
        )
        payload = identity.model_dump(mode="json")
        if row["run_hash"] != content_hash(payload):
            raise MingliSyntheticExperimentRunStoreError(
                "mingli_synthetic_experiment_run_hash_mismatch"
            )
        if row["run_ref"] != stable_ref("v60-mingli-synthetic-run", payload):
            raise MingliSyntheticExperimentRunStoreError(
                "mingli_synthetic_experiment_run_ref_mismatch"
            )
        return row
