from __future__ import annotations

import json
from typing import Any

import pytest
from abu_v60.db import engine
from abu_v60.db.schema import mingli_synthetic_distillation_runs
from abu_v60.mingli.agent_method_cards import method_card_catalog
from abu_v60.mingli.synthetic_distillation_contracts import (
    DistillationCandidateOutput,
    DistillationCertaintyOutput,
    DistillationRegimeOutput,
    SyntheticDistillationRun,
)
from abu_v60.mingli.synthetic_distillation_logic import (
    assemble_candidate_output,
    assemble_certainty,
    evaluate_distillation_outputs,
)
from abu_v60.mingli.synthetic_distillation_runtime import (
    MINGLI_SYNTHETIC_DISTILLATION_CONTEXT_MAX_CHARS,
    MINGLI_SYNTHETIC_DISTILLATION_NUM_CTX,
    MINGLI_SYNTHETIC_DISTILLATION_NUM_PREDICT,
    MINGLI_SYNTHETIC_DISTILLATION_SEED,
    MINGLI_SYNTHETIC_DISTILLATION_TOP_K,
    MingliSyntheticDistillationRuntime,
    OllamaSyntheticDistillationProvider,
    mingli_synthetic_distillation_runtime_manifest,
)
from abu_v60.mingli.synthetic_distillation_service import (
    MingliSyntheticDistillationService,
)
from abu_v60.mingli.synthetic_distillation_store import (
    MingliSyntheticDistillationStore,
)
from abu_v60.mingli.synthetic_experiment_catalog import (
    MONTH_COMMAND_REGIME_GENERALIZATION_EXPERIMENT,
    MONTH_COMMAND_REGIME_GENERALIZATION_EXPERIMENT_REF,
)
from abu_v60.mingli.synthetic_experiment_gold import synthetic_experiment_dev_gold
from abu_v60.mingli.synthetic_experiment_seed import seed_synthetic_experiment
from abu_v60.mingli.synthetic_experiment_service import SyntheticExperimentService
from sqlalchemy import inspect, text
from sqlalchemy.exc import DBAPIError


class MemoryStore:
    def __init__(self) -> None:
        self.values: dict[str, SyntheticDistillationRun] = {}

    def find_generation(self, *, generation_key: str):
        return self.values.get(generation_key)

    def ensure(self, run: SyntheticDistillationRun):
        self.values.setdefault(run.generation_key, run)
        return self.values[run.generation_key]


def _packet(variant: str) -> Any:
    seeded = seed_synthetic_experiment(
        engine,
        experiment_ref=MONTH_COMMAND_REGIME_GENERALIZATION_EXPERIMENT_REF,
    )
    by_case = {item["case_ref"]: item for item in seeded["members"]}
    member = MONTH_COMMAND_REGIME_GENERALIZATION_EXPERIMENT.member_by_variant[variant]
    return SyntheticExperimentService(engine).compile_packet(
        case_ref=member.case_ref,
        reading_ref=str(by_case[member.case_ref]["reading_ref"]),
    )


def _regime_output(packet: Any, variant: str) -> dict[str, Any]:
    gold, _ = synthetic_experiment_dev_gold(MONTH_COMMAND_REGIME_GENERALIZATION_EXPERIMENT_REF)
    prefix = f"{variant}_"
    classification = gold[f"{prefix}allowed_regime_classifications"][0]
    return {
        "regime_decision": {
            "method_asset_ref": "REGIME_WEAK_VS_FOLLOW_TREND_001",
            "classification": classification,
            "effective_root_status": gold[f"{prefix}required_effective_root_status"],
            "effective_root_coordinates": gold[f"{prefix}required_effective_root_coordinates"],
            "rooted_visible_support_status": gold[
                f"{prefix}required_rooted_visible_support_status"
            ],
            "dominant_chain_status": "UNRESOLVED",
            "competition_kinds": gold[f"{prefix}required_competition_kinds"],
            "evidence_ids": [packet.day_master_support.evidence_id],
        },
        "day_master_state": (
            "UNCERTAIN" if classification in {"UNRESOLVED", "FALSE_FOLLOW_COMPETITION"} else "WEAK"
        ),
        "rationale": "依据根候选、印比竞争与当前事实边界，暂按现有证据完成判型。",
    }


def _candidate_output(packet: Any) -> dict[str, Any]:
    universe = tuple(item.evidence_id for item in packet.mechanism_observations)
    selected = universe[:2]
    cards = method_card_catalog(packet.mechanism_observations)
    return {
        "primary_method_card_ref": selected[0],
        "alternative_method_card_ref": selected[1],
        "assessments": [
            {
                "method_card_ref": candidate_ref,
                "rulings": [
                    {
                        "check_code": check_code,
                        "ruling": "CONDITIONAL",
                        "rationale": "现有事实支持有限，仍需相反证据复核。",
                        "evidence_ids": [candidate_ref],
                    }
                    for check_code in cards[candidate_ref]["required_checks"]
                ],
                "summary": "该候选可以解释部分结构，但成立条件仍未完全闭合。",
            }
            for candidate_ref in selected
        ],
        "excluded_method_card_refs": [item for item in universe if item not in selected],
        "comparison_rationale": "两个候选均能解释局部结构，暂按方法检查覆盖顺序保留主次。",
        "reversal_condition": "若备选的关键检查获得更完整证据，主次关系应当翻转。",
    }


def _certainty_output(*, overclaim: bool = False) -> dict[str, Any]:
    return {
        "primary_judgment": "SUPPORTED" if overclaim else "WORKS_IF",
        "alternative_judgment": "SUPPORTED" if overclaim else "PARTIAL",
        "work_path_closure": "CLOSED" if overclaim else "CONDITIONAL",
        "confidence": "MEDIUM" if overclaim else "LOW",
        "rationale": "严格依据本地裁决映射结论强度，不额外提高确定性。",
    }


def _provider(
    packet: Any,
    variant: str,
    *,
    overclaim: bool = False,
) -> tuple[OllamaSyntheticDistillationProvider, list[dict[str, Any]]]:
    calls: list[dict[str, Any]] = []
    responses = (
        _regime_output(packet, variant),
        _candidate_output(packet),
        _certainty_output(overclaim=overclaim),
    )

    def transport(**values: Any) -> dict[str, Any]:
        index = len(calls)
        calls.append(values)
        return {
            "response": json.dumps(responses[index], ensure_ascii=False),
            "prompt_eval_count": 100 + index,
            "eval_count": 30 + index,
            "created_at": f"2026-08-27T00:00:0{index}Z",
        }

    return (
        OllamaSyntheticDistillationProvider(
            model_ref="qwen3.8:27b-test",
            model_digest="d" * 64,
            base_url="http://private-model.invalid",
            timeout_seconds=12,
            temperature=0,
            top_p=0.95,
            top_k=20,
            keep_alive="30m",
            transport=transport,
        ),
        calls,
    )


def _service(
    packet: Any,
    variant: str,
    *,
    overclaim: bool = False,
) -> tuple[MingliSyntheticDistillationService, MemoryStore, list[dict[str, Any]]]:
    provider, calls = _provider(packet, variant, overclaim=overclaim)
    memory = MemoryStore()
    service = MingliSyntheticDistillationService(
        engine,
        runtime=MingliSyntheticDistillationRuntime(provider=provider, enabled=True),
        store=memory,  # type: ignore[arg-type]
    )
    return service, memory, calls


@pytest.mark.parametrize("variant", ["A", "B"])
def test_three_small_calls_are_locally_assembled_and_cached(variant: str) -> None:
    packet = _packet(variant)
    service, memory, calls = _service(packet, variant)

    first = service.run(
        experiment_ref=MONTH_COMMAND_REGIME_GENERALIZATION_EXPERIMENT_REF,
        variant=variant,  # type: ignore[arg-type]
    )
    replay = service.run(
        experiment_ref=MONTH_COMMAND_REGIME_GENERALIZATION_EXPERIMENT_REF,
        variant=variant,  # type: ignore[arg-type]
    )

    assert first.cache_hit is False
    assert replay.cache_hit is True
    assert replay.run == first.run
    assert len(calls) == 3
    assert len(memory.values) == 1
    assert tuple(item.stage for item in first.run.passes) == (
        "REGIME",
        "CANDIDATE_COMPARISON",
        "CERTAINTY",
    )
    assert first.run.evaluation.outcome == "DEV_PASS"
    assert first.run.evaluation.model_independence == "PASS"
    assert first.run.evaluation.candidate_assembly.primary_adjudication == ("CONDITIONAL")
    assert first.run.evaluation.certainty_assembly.work_path_closure == ("CONDITIONAL")
    assert first.run.publication_allowed is False
    assert first.run.canonical_fact_write_allowed is False
    assert first.run.read_only is True
    for index, call in enumerate(calls):
        stage = ("REGIME", "CANDIDATE_COMPARISON", "CERTAINTY")[index]
        payload = call["payload"]
        prompt = payload["prompt"]
        assert "gold" not in prompt.lower()
        assert "analysis_date" not in prompt
        assert "life_domains" not in prompt
        assert "timing_coordinates" not in prompt
        assert len(prompt) <= MINGLI_SYNTHETIC_DISTILLATION_CONTEXT_MAX_CHARS[stage]
        assert payload["format"]["additionalProperties"] is False
        assert payload["think"] is False
        assert payload["options"]["temperature"] == 0
        assert payload["options"]["top_k"] == MINGLI_SYNTHETIC_DISTILLATION_TOP_K
        assert payload["options"]["seed"] == MINGLI_SYNTHETIC_DISTILLATION_SEED
        assert payload["options"]["num_ctx"] == MINGLI_SYNTHETIC_DISTILLATION_NUM_CTX
        assert (
            payload["options"]["num_predict"] == (MINGLI_SYNTHETIC_DISTILLATION_NUM_PREDICT[stage])
        )


def test_certainty_overclaim_is_rejected_by_local_ceiling() -> None:
    variant = "A"
    packet = _packet(variant)
    regime = DistillationRegimeOutput.model_validate(_regime_output(packet, variant))
    candidate = DistillationCandidateOutput.model_validate(_candidate_output(packet))
    certainty = DistillationCertaintyOutput.model_validate(_certainty_output(overclaim=True))

    candidate_assembly = assemble_candidate_output(packet, candidate)
    local_certainty = assemble_certainty(candidate_assembly)
    evaluation = evaluate_distillation_outputs(
        experiment_ref=MONTH_COMMAND_REGIME_GENERALIZATION_EXPERIMENT_REF,
        variant=variant,
        packet=packet,
        regime_output=regime,
        candidate_output=candidate,
        certainty_output=certainty,
        raw_outputs=(
            regime.model_dump(mode="json"),
            candidate.model_dump(mode="json"),
            certainty.model_dump(mode="json"),
        ),
    )

    assert local_certainty.primary_judgment == "WORKS_IF"
    assert local_certainty.alternative_judgment == "PARTIAL"
    assert local_certainty.work_path_closure == "CONDITIONAL"
    assert evaluation.outcome == "DEV_REVIEW_REQUIRED"
    assert "CERTAINTY_LOCALLY_COHERENT" in evaluation.issue_keys


def test_distillation_table_is_append_only() -> None:
    packet = _packet("A")
    service, _, _ = _service(packet, "A")
    run = service.run(
        experiment_ref=MONTH_COMMAND_REGIME_GENERALIZATION_EXPERIMENT_REF,
        variant="A",
    ).run
    assert "synthetic_distillation_runs" in inspect(engine).get_table_names(schema="mingli")
    values = MingliSyntheticDistillationStore._columns(run)
    values["run_json"] = run.model_dump(mode="json")
    with engine.connect() as connection:
        transaction = connection.begin()
        try:
            connection.execute(mingli_synthetic_distillation_runs.insert(), values)
            with pytest.raises(
                DBAPIError,
                match="mingli_synthetic_distillation_runs_are_append_only",
            ):
                connection.execute(
                    text(
                        """
                        UPDATE mingli.synthetic_distillation_runs
                        SET outcome = outcome
                        WHERE run_ref = :run_ref
                        """
                    ),
                    {"run_ref": run.run_ref},
                )
        finally:
            transaction.rollback()


def test_runtime_manifest_keeps_probe_out_of_product_and_qualification() -> None:
    manifest = mingli_synthetic_distillation_runtime_manifest()

    assert manifest["runtime_role"] == "DEV_METHOD_TRAINING_ONLY"
    assert manifest["gold_in_model_context"] is False
    assert manifest["candidate_assembly_authority"] == "LOCAL_SYSTEM"
    assert manifest["certainty_ceiling_authority"] == "LOCAL_SYSTEM"
    assert manifest["strict_whole_chart_replacement_allowed"] is False
    assert manifest["publication_allowed"] is False
    assert manifest["canonical_fact_write_allowed"] is False
    assert manifest["qualification_effect"] == ("DEV_TRAINING_ONLY_NOT_QUALIFICATION")
