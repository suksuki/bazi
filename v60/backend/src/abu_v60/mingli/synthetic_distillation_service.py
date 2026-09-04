from __future__ import annotations

from dataclasses import dataclass
from threading import Lock
from typing import Literal, cast

from sqlalchemy.engine import Engine

from abu_v60.mingli.synthetic_distillation_contracts import (
    DistillationCandidateOutput,
    DistillationCertaintyOutput,
    DistillationRegimeOutput,
    SyntheticDistillationRun,
)
from abu_v60.mingli.synthetic_distillation_logic import (
    evaluate_distillation_outputs,
)
from abu_v60.mingli.synthetic_distillation_runtime import (
    MingliSyntheticDistillationRuntime,
    MingliSyntheticDistillationRuntimeError,
    configured_mingli_synthetic_distillation_runtime,
)
from abu_v60.mingli.synthetic_distillation_store import (
    MingliSyntheticDistillationStore,
    MingliSyntheticDistillationStoreError,
)
from abu_v60.mingli.synthetic_experiment_catalog import (
    resolve_synthetic_experiment,
)
from abu_v60.mingli.synthetic_experiment_seed import seed_synthetic_experiment
from abu_v60.mingli.synthetic_experiment_service import (
    SyntheticExperimentError,
    SyntheticExperimentService,
)


class MingliSyntheticDistillationServiceError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class SyntheticDistillationExecution:
    run: SyntheticDistillationRun
    cache_hit: bool


class MingliSyntheticDistillationService:
    """Run one DEV-only three-pass probe against a canonical synthetic member."""

    def __init__(
        self,
        engine: Engine,
        *,
        runtime: MingliSyntheticDistillationRuntime | None = None,
        store: MingliSyntheticDistillationStore | None = None,
        experiment_service: SyntheticExperimentService | None = None,
    ) -> None:
        self._engine = engine
        self._runtime = runtime or configured_mingli_synthetic_distillation_runtime()
        self._store = store or MingliSyntheticDistillationStore(engine)
        self._experiments = experiment_service or SyntheticExperimentService(engine)
        self._generation_lock = Lock()

    def run(
        self,
        *,
        experiment_ref: str,
        variant: Literal["A", "B"],
    ) -> SyntheticDistillationExecution:
        try:
            experiment = resolve_synthetic_experiment(experiment_ref)
        except ValueError as exc:
            raise MingliSyntheticDistillationServiceError(str(exc)) from exc
        definition = experiment.public_definition()
        member = experiment.member_by_variant[variant]
        try:
            seeded = seed_synthetic_experiment(
                self._engine,
                experiment_ref=experiment.experiment_ref,
            )
            materialized = next(
                item for item in seeded["members"] if item["case_ref"] == member.case_ref
            )
            packet = self._experiments.compile_packet(
                case_ref=member.case_ref,
                reading_ref=str(materialized["reading_ref"]),
            )
        except (StopIteration, SyntheticExperimentError, ValueError) as exc:
            raise MingliSyntheticDistillationServiceError(
                f"mingli_distillation_packet_failed:{exc}"
            ) from exc
        if packet.subject_kind != "CANONICAL_SYNTHETIC":
            raise MingliSyntheticDistillationServiceError(
                "mingli_distillation_synthetic_subject_required"
            )
        if len(packet.mechanism_observations) < 2:
            raise MingliSyntheticDistillationServiceError(
                "mingli_distillation_two_candidates_required"
            )
        definition_hash = str(definition["definition_hash"])
        try:
            candidate_identity = self._runtime.candidate_identity()
            generation_key = self._runtime.generation_key(
                experiment_ref=experiment.experiment_ref,
                definition_hash=definition_hash,
                variant=variant,
                packet=packet,
            )
        except MingliSyntheticDistillationRuntimeError as exc:
            raise MingliSyntheticDistillationServiceError(str(exc)) from exc

        cached = self._store.find_generation(generation_key=generation_key)
        if cached is not None:
            return SyntheticDistillationExecution(run=cached, cache_hit=True)
        with self._generation_lock:
            cached = self._store.find_generation(generation_key=generation_key)
            if cached is not None:
                return SyntheticDistillationExecution(run=cached, cache_hit=True)
            try:
                passes = self._runtime.run(packet=packet)
            except MingliSyntheticDistillationRuntimeError as exc:
                raise MingliSyntheticDistillationServiceError(str(exc)) from exc
            regime_output = cast(DistillationRegimeOutput, passes[0].output)
            candidate_output = cast(DistillationCandidateOutput, passes[1].output)
            certainty_output = cast(DistillationCertaintyOutput, passes[2].output)
            evaluation = evaluate_distillation_outputs(
                experiment_ref=experiment.experiment_ref,
                variant=variant,
                packet=packet,
                regime_output=regime_output,
                candidate_output=candidate_output,
                certainty_output=certainty_output,
                raw_outputs=tuple(item.raw_output for item in passes),
            )
            run = SyntheticDistillationRun.issue(
                generation_key=generation_key,
                research_account_ref="v60-mingli-synthetic-research",
                experiment_ref=experiment.experiment_ref,
                definition_hash=definition_hash,
                variant=variant,
                case_ref=packet.case_ref,
                reading_ref=packet.reading_ref,
                reading_hash=packet.reading_hash,
                packet_ref=packet.packet_ref,
                packet_hash=packet.packet_hash,
                runtime_ref=candidate_identity["runtime_ref"],
                provider_id=candidate_identity["provider_id"],
                model_ref=candidate_identity["model_ref"],
                model_digest=candidate_identity["model_digest"],
                provider_profile_ref=candidate_identity["provider_profile_ref"],
                provider_profile_hash=candidate_identity["provider_profile_hash"],
                prompt_version=candidate_identity["prompt_version"],
                prompt_hash=candidate_identity["prompt_hash"],
                passes=passes,
                evaluation=evaluation,
                input_tokens=sum(item.input_tokens for item in passes),
                output_tokens=sum(item.output_tokens for item in passes),
                total_tokens=sum(item.total_tokens for item in passes),
                duration_ms=sum(item.duration_ms for item in passes),
            )
            try:
                stored = self._store.ensure(run)
            except MingliSyntheticDistillationStoreError as exc:
                raise MingliSyntheticDistillationServiceError(str(exc)) from exc
            return SyntheticDistillationExecution(run=stored, cache_hit=False)
