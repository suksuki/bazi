from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.engine import Connection, Engine

from abu_v60.mingli.synthetic_distillation_contracts import (
    SyntheticDistillationRun,
)
from abu_v60.provenance import canonical_json


class MingliSyntheticDistillationStoreError(ValueError):
    pass


class MingliSyntheticDistillationStore:
    """Append-only DEV probes keyed by exact packet and candidate identity."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def ensure(self, run: SyntheticDistillationRun) -> SyntheticDistillationRun:
        with self._engine.begin() as connection:
            connection.execute(
                text(
                    """
                    INSERT INTO mingli.synthetic_distillation_runs
                        (run_ref, run_version, generation_key, experiment_ref,
                         definition_hash, variant, case_ref, reading_ref,
                         reading_hash, packet_ref, packet_hash, runtime_ref,
                         provider_id, model_ref, model_digest,
                         provider_profile_ref, provider_profile_hash,
                         prompt_version, prompt_hash, outcome,
                         model_independence, run_json, run_hash,
                         input_tokens, output_tokens, total_tokens, duration_ms)
                    VALUES
                        (:run_ref, :run_version, :generation_key, :experiment_ref,
                         :definition_hash, :variant, :case_ref, :reading_ref,
                         :reading_hash, :packet_ref, :packet_hash, :runtime_ref,
                         :provider_id, :model_ref, :model_digest,
                         :provider_profile_ref, :provider_profile_hash,
                         :prompt_version, :prompt_hash, :outcome,
                         :model_independence, CAST(:run_json AS jsonb), :run_hash,
                         :input_tokens, :output_tokens, :total_tokens, :duration_ms)
                    ON CONFLICT DO NOTHING
                    """
                ),
                {
                    **self._columns(run),
                    "run_json": canonical_json(run.model_dump(mode="json")),
                },
            )
            stored = self._load_generation(
                connection,
                generation_key=run.generation_key,
            )
        if stored is None:
            raise MingliSyntheticDistillationStoreError(
                "mingli_distillation_store_identity_conflict"
            )
        restored = self._validated(stored)
        if restored.run_ref != run.run_ref or restored.run_hash != run.run_hash:
            raise MingliSyntheticDistillationStoreError("mingli_distillation_generation_conflict")
        return restored

    def find_generation(
        self,
        *,
        generation_key: str,
    ) -> SyntheticDistillationRun | None:
        with self._engine.connect() as connection:
            row = self._load_generation(
                connection,
                generation_key=generation_key,
            )
        return None if row is None else self._validated(row)

    def history(
        self,
        *,
        experiment_ref: str,
        variant: str,
    ) -> tuple[SyntheticDistillationRun, ...]:
        with self._engine.connect() as connection:
            rows = (
                connection.execute(
                    text(
                        """
                        SELECT *
                        FROM mingli.synthetic_distillation_runs
                        WHERE experiment_ref = :experiment_ref
                          AND variant = :variant
                        ORDER BY created_at DESC, run_ref DESC
                        """
                    ),
                    {"experiment_ref": experiment_ref, "variant": variant},
                )
                .mappings()
                .all()
            )
        return tuple(self._validated(dict(row)) for row in rows)

    @staticmethod
    def _load_generation(
        connection: Connection,
        *,
        generation_key: str,
    ) -> dict[str, Any] | None:
        row = (
            connection.execute(
                text(
                    """
                SELECT *
                FROM mingli.synthetic_distillation_runs
                WHERE generation_key = :generation_key
                """
                ),
                {"generation_key": generation_key},
            )
            .mappings()
            .first()
        )
        return None if row is None else dict(row)

    @staticmethod
    def _validated(row: dict[str, Any]) -> SyntheticDistillationRun:
        run = SyntheticDistillationRun.model_validate(row["run_json"])
        if (
            row["run_ref"] != run.run_ref
            or row["run_hash"] != run.run_hash
            or row["generation_key"] != run.generation_key
        ):
            raise MingliSyntheticDistillationStoreError("mingli_distillation_store_row_mismatch")
        return run

    @staticmethod
    def _columns(run: SyntheticDistillationRun) -> dict[str, Any]:
        return {
            "run_ref": run.run_ref,
            "run_version": run.run_version,
            "generation_key": run.generation_key,
            "experiment_ref": run.experiment_ref,
            "definition_hash": run.definition_hash,
            "variant": run.variant,
            "case_ref": run.case_ref,
            "reading_ref": run.reading_ref,
            "reading_hash": run.reading_hash,
            "packet_ref": run.packet_ref,
            "packet_hash": run.packet_hash,
            "runtime_ref": run.runtime_ref,
            "provider_id": run.provider_id,
            "model_ref": run.model_ref,
            "model_digest": run.model_digest,
            "provider_profile_ref": run.provider_profile_ref,
            "provider_profile_hash": run.provider_profile_hash,
            "prompt_version": run.prompt_version,
            "prompt_hash": run.prompt_hash,
            "outcome": run.evaluation.outcome,
            "model_independence": run.evaluation.model_independence,
            "run_hash": run.run_hash,
            "input_tokens": run.input_tokens,
            "output_tokens": run.output_tokens,
            "total_tokens": run.total_tokens,
            "duration_ms": run.duration_ms,
        }
