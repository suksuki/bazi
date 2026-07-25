from __future__ import annotations

import json
from pathlib import Path

from core.contracts import BirthInputCanonical
from core.mingli_agent import compile_chart_world
from core.mingli_agent.fact_review import classify_claim_modality, deterministic_fact_conflicts
from scripts.v50_prepare_vnext_phase0_g1_6 import (
    DEFAULT_PRIOR_RAW,
    audit_lane_isolation,
    audit_nonsealed_resource_access,
    audit_pairwise_contract,
    audit_repair_scope,
    audit_retained_fact_conflict,
)
from scripts.v50_run_vnext_phase0_benchmark import DEVELOPMENT_FIXTURE_PACK_PATH


def _development_world():
    pack = json.loads(DEVELOPMENT_FIXTURE_PACK_PATH.read_text(encoding="utf-8"))
    birth = dict(pack["cases"][0]["birth_input"])
    birth["birth_time"] = "12:00"
    return compile_chart_world(
        reading_id="g1-6-unit",
        birth_input=BirthInputCanonical.model_validate(birth),
        include_research_fixture_prior=False,
    )


def test_timing_and_counterfactual_relations_are_not_natal_fact_conflicts() -> None:
    world = _development_world()

    assert deterministic_fact_conflicts(text="子午冲在流年可能引发动荡", world=world) == []
    assert deterministic_fact_conflicts(text="若逢午火冲子，则观察印星是否受损", world=world) == []


def test_unqualified_absent_natal_relation_remains_a_hard_conflict() -> None:
    world = _development_world()

    assert deterministic_fact_conflicts(text="命局明确存在子午冲。", world=world) == [
        "地支关系冲突:盘中不存在子午冲所需地支"
    ]


def test_phase0_modality_taxonomy_only_sends_natal_assertions_to_fact_conflict_review() -> None:
    world = _development_world()
    samples = {
        "命局明确存在子午冲。": "asserted_natal_fact",
        "因此可见命局存在子午冲。": "derived_natal_claim",
        "这可能形成子午冲。": "hypothesis",
        "如果形成子午冲，则需要观察。": "counterfactual",
        "流年遇午可能引动子午冲。": "timing_condition",
        "是否存在子午冲？": "question",
        "用户说：“命局存在子午冲。”": "quoted_claim",
    }

    for text, expected in samples.items():
        start = text.index("子午冲")
        assert classify_claim_modality(text=text, start=start) == expected

    assert deterministic_fact_conflicts(text="是否存在子午冲？", world=world) == []
    assert deterministic_fact_conflicts(text="用户说：“命局存在子午冲。”", world=world) == []


def test_retained_holistic_conflict_is_classified_as_parser_scope_failure() -> None:
    audit = audit_retained_fact_conflict(prior_raw_path=DEFAULT_PRIOR_RAW)

    assert audit["status"] == "classified"
    assert len(audit["records"]) == 1
    assert audit["records"][0]["classification"] == "parser_failure"
    assert audit["records"][0]["parser_output_after_scope_fix"] == []


def test_nonsealed_probe_does_not_load_formal_or_expert_assets(tmp_path: Path) -> None:
    audit = audit_nonsealed_resource_access(output_dir=tmp_path)

    assert audit["status"] == "passed"
    assert audit["resource_access"]["full_taxonomy_accessed"] is False
    assert audit["resource_access"]["formal_manifest_accessed"] is False
    assert audit["resource_access"]["expert_reference_accessed"] is False
    assert audit["formal_case_ids_loaded"] == []


def test_lane_prompt_and_repair_scope_require_explicit_analyst_decisions() -> None:
    lane = audit_lane_isolation()
    repair = audit_repair_scope()

    assert lane["declared_lane_contract_passed"] is True
    assert lane["status"] == "analyst_decision_required"
    assert "主做功" in lane["method_tokens_found_in_direct_prompt"]
    assert repair["status"] == "analyst_decision_required"
    assert "hypotheses" in repair["substantive_fields_modified_by_current_fact_repair"]
    assert "work_path" in repair["substantive_fields_modified_by_current_fact_repair"]


def test_pairwise_contract_covers_the_six_critical_comparisons() -> None:
    audit = audit_pairwise_contract()

    assert audit["status"] == "passed"
    assert len(audit["required_comparisons"]) == 6
    assert ["vnext", "current_v50"] in audit["required_comparisons"]
    assert ["holistic_synthesis", "fact_only_deepbazi"] in audit["required_comparisons"]
