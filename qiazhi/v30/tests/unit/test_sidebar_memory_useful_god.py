from __future__ import annotations

import json

from v30.llm.thinking_context import build_thinking_stage_context_pack
from v30.presentation.thinking import build_thinking_projection
from v30.runtime import create_smoke_runtime


def test_sidebar_memory_exposes_progressive_useful_god_context() -> None:
    runtime = create_smoke_runtime(reading_id="pytest-sidebar-memory", locale="zh")
    projection = build_thinking_projection(runtime)

    assert projection["sidebar_memory"]["version"] == "v30.sidebar_memory.v1"
    assert projection["sidebar_memory"]["training_signal"]["trainable"] is True
    memory_items = projection["sidebar_memory"]["items"]
    useful_memory = next(row for row in memory_items if row["memory_id"] == "useful_god.primary")
    decision_memory = next(row for row in memory_items if row["memory_id"] == "decision.verdict")
    assert useful_memory["stage_id"] == "useful_god_arbitration"
    assert useful_memory["visibility_stage"] == "useful_god_arbitration"
    assert useful_memory["value"]
    assert useful_memory["counter_evidence"]
    assert useful_memory["boundary"] == "sidebar_memory_item_is_key_context_not_final_verdict"
    assert decision_memory["stage_id"] == "final_report"
    assert decision_memory["label"] == "裁决摘要"
    assert decision_memory["boundary"] == "sidebar_memory_item_is_decision_verdict_projection_not_llm_text"

    useful_step = next(step for step in projection["steps"] if step["step_id"] == "useful_god_arbitration")
    assert useful_step["title"] == "用神忌神与取舍"
    assert useful_step["stage_point_set"]["version"] == "v30.stage_point_set.v1"
    assert useful_step["stage_points"]
    assert {row["kind"] for row in useful_step["stage_points"]} >= {"verdict", "advice"}
    assert useful_step["summary_policy"]["llm_enhancement"] == "auto"
    assert useful_step["summary_policy"]["signals"]["prompt_profile"]["profile_id"] == "v30.stage_prompt.useful_god_arbitration.v1"
    assert any(row["label"] == "忌避风险" for row in useful_step["analysis_result"]["public_trace"])

    useful_model = projection["reasoning_model"]["useful_god_model"]
    assert useful_model["avoidance_model"]["version"] == "v30.useful_god_avoidance_model.v1"
    assert useful_model["avoidance_model"]["primary_risks"]
    assert useful_model["training_signal"]["trainable"] is True
    assert "fixed_unfavorable_element_verdict" in useful_model["training_signal"]["blocked_targets"]


def test_thinking_projection_exposes_seven_decision_centered_journey_steps() -> None:
    runtime = create_smoke_runtime(reading_id="pytest-seven-journey-steps", locale="zh")
    projection = build_thinking_projection(runtime)

    journey_steps = projection["journey_steps"]
    assert projection["progress"]["total_steps"] == 7
    assert len(journey_steps) == 7
    assert [step["step_id"] for step in journey_steps] == [
        "journey_chart_calibration",
        "journey_structure_useful_god",
        "journey_material_candidates",
        "journey_path_timing_domain",
        "journey_branch_calibration",
        "journey_decision_verdicts",
        "journey_final_expression",
    ]
    assert projection["material_step_count"] >= 10
    assert all(step["summary_policy"]["llm_enhancement"] == "not_required" for step in journey_steps)
    assert journey_steps[5]["stage_points"]
    assert journey_steps[5]["summary_policy"]["signals"]["central_brain_contract"] == "decision_engine_verdict_before_llm_expression"
    branch_stage = journey_steps[4]
    assert branch_stage["stage_point_set"]["option_sets"]
    assert all(
        row["source_type"] == "stage_point_branch"
        for row in branch_stage["stage_point_set"]["option_sets"]
    )
    assert all(
        row["visibility"]["practitioner"] == "interactive"
        for row in branch_stage["stage_point_set"]["option_sets"]
    )


def test_useful_god_stage_context_feeds_llm_with_avoidance_model() -> None:
    runtime = create_smoke_runtime(reading_id="pytest-useful-god-context", locale="zh")
    projection = build_thinking_projection(runtime)
    useful_step = next(step for step in projection["steps"] if step["step_id"] == "useful_god_arbitration")

    context = build_thinking_stage_context_pack(
        runtime,
        useful_step,
        role_key="user",
        locale="zh",
        client="web",
    )

    assert context["prompt_profile"]["scene"] == "useful_god_avoidance_arbitration"
    assert "avoidance_risk" in context["prompt_profile"]["must_name"]
    assert "useful_god_model" in context["xuanming_reasoning"]["selected_submodels"]
    module_ids = {row["module_id"] for row in context["module_context"]}
    assert {"xuanming_useful_god", "avoidance_model", "M5_ranked_decisions"} <= module_ids
    assert context["fact_boundary"]["chart_fact_mutation_allowed"] is False


def test_structure_stage_uses_customer_safe_labels_in_page_and_llm_context() -> None:
    runtime = create_smoke_runtime(reading_id="pytest-structure-public-labels", locale="zh")
    projection = build_thinking_projection(runtime)
    structure_step = next(step for step in projection["steps"] if step["step_id"] == "structure_reasoning")
    structure_memory = next(row for row in projection["sidebar_memory"]["items"] if row["memory_id"] == "structure.mainline")
    assert structure_memory["source_point_id"].startswith("stage.structure_reasoning.")
    context = build_thinking_stage_context_pack(
        runtime,
        structure_step,
        role_key="user",
        locale="zh",
        client="web",
    )

    public_payload = json.dumps(
        {
            "summary": structure_step["summary"],
            "tasks": structure_step["tasks"],
            "analysis_result": structure_step["analysis_result"],
            "sidebar_memory": structure_memory,
            "context": context,
        },
        ensure_ascii=False,
    )
    forbidden = [
        "evidence-bound",
        "candidate-bound",
        "ten-god",
        "mechanism paths",
        "dynamic_structure_review",
        "output_or_wealth_release_review",
    ]

    assert "证据约束型结构" in public_payload
    assert not any(token in public_payload for token in forbidden)


def test_thinking_stage_context_exposes_stage_points_for_llm() -> None:
    runtime = create_smoke_runtime(reading_id="pytest-stage-points-context", locale="zh")
    projection = build_thinking_projection(runtime)
    rule_step = next(step for step in projection["steps"] if step["step_id"] == "rule_matching")

    context = build_thinking_stage_context_pack(
        runtime,
        rule_step,
        role_key="user",
        locale="zh",
        client="web",
    )

    assert context["stage"]["stage_points"]
    assert context["stage"]["stage_point_set"]["version"] == "v30.stage_point_set.v1"
    assert context["output_policy"]["required_fields"][:3] == ["text", "public_derivation", "candidate_points"]
