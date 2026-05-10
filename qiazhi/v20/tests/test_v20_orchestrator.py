from __future__ import annotations

from v20.api.runtime import run_runtime_from_pillars
from v20.orchestrator.mainline import arbitrate_mainline


def test_v20_mainline_arbitration_selects_weighted_primary_mainline() -> None:
    result = run_runtime_from_pillars(
        "庚午",
        "辛巳",
        "丁丑",
        "乙巳",
        input_id="v20.orchestrator.contract",
        user_text="我想重点看事业和财运主线",
        flow_year_pillar="丙午",
        luck_pillar="甲申",
    )

    arbitration = result["mainline_arbitration"]
    primary = arbitration["primary_mainline"]
    orchestrator = result["reasoning_orchestrator"]

    assert arbitration["version"] == "v20.mainline_arbitration.v1"
    assert arbitration["status"] == "ready"
    assert arbitration["source"] == "DecisionReport+FeatureStateModel+StructureDynamics+QuestionIntent+TimeContext"
    assert arbitration["candidate_count"] >= 3
    assert primary["nodes"]
    assert len(primary["nodes"]) <= 3
    assert primary["source"]
    assert primary["score"] > 0
    assert arbitration["why_selected"]
    assert arbitration["quality_gate"]["version"] == "v20.mainline_quality_gate.v1"
    assert arbitration["quality_gate"]["evidence_coverage"] > 0
    assert isinstance(arbitration["requires_review"], bool)
    assert "NO_LLM_CAN_OVERRIDE_PRIMARY_MAINLINE" in arbitration["guardrails"]
    assert "QUALITY_GATE_CAN_REQUIRE_PRACTITIONER_REVIEW" in arbitration["guardrails"]

    assert orchestrator["version"] == "v20.reasoning_orchestrator.v1"
    assert orchestrator["status"] == "ready"
    assert orchestrator["step_count"] >= 15
    assert orchestrator["primary_outputs"]["primary_mainline"] == "mainline_arbitration.primary_mainline"
    assert any(row["step_key"] == "mainline_arbitration" for row in orchestrator["steps"])
    assert all(row["elapsed_ms"] >= 0 for row in orchestrator["steps"])
    assert result["answer_plan"]["dimension_context"]["primary_mainline"]["candidate_key"] == primary["candidate_key"]
    assert any(row["section_type"] == "orchestrator_mainline" for row in result["answer_plan"]["sections"])
    prompt = result["llm_assist"]["context_pack"]["task_contexts"]["practitioner_answer"]["prompt"]
    assert prompt["context"]["mainline"][0]["label"] == primary["title"]
    if arbitration["requires_review"]:
        control_keys = {row["control_key"] for row in result["decision_report"]["practitioner_controls"]}
        assert "control.mainline_arbitration" in control_keys
    assert result["runtime_mutation"] is False


def test_v20_mainline_arbitration_prefers_decision_mainline_over_plain_structure_when_weighted() -> None:
    arbitration = arbitrate_mainline(
        decision_report={
            "mainlines": (
                {
                    "mainline_key": "mainline.wealth.output_capacity",
                    "title": "食伤生财承载链",
                    "domain": "wealth",
                    "status": "chain_review",
                    "score": 0.74,
                    "support": ("食伤见财", "日主承载待复核"),
                },
            ),
            "decisions": (),
            "portrait_projection": {"axes": ()},
            "rule_runtime_hits": (),
        },
        feature_state_model={"priority_features": ()},
        structure_dynamics={
            "dominant_chain": {
                "chain_key": "wealth->authority->resource",
                "nodes": ("wealth", "authority", "resource"),
                "evidence": ("正财", "正官", "正印"),
            },
            "chain_state": "closed",
            "volatility_score": 0.2,
        },
        question_intent_model={"selected_question_intent": {"domain": "wealth"}},
        time_context={"status": "ready"},
    )

    primary = arbitration["primary_mainline"]
    assert primary["candidate_key"] == "mainline.wealth.output_capacity"
    assert primary["nodes"] == ("output", "wealth", "self")
    assert "decision_mainline" in primary["source"]
    assert arbitration["quality_gate"]["requires_review"] is True
    assert "single_source_bias" in arbitration["quality_gate"]["risk_flags"]


def test_v20_mainline_quality_gate_flags_thin_or_competing_evidence() -> None:
    arbitration = arbitrate_mainline(
        decision_report={
            "mainlines": (
                {
                    "mainline_key": "mainline.career.guan_shang_yin",
                    "title": "官伤印三方链",
                    "domain": "career",
                    "status": "chain_review",
                    "score": 0.7,
                    "support": ("伤官见官",),
                },
                {
                    "mainline_key": "mainline.wealth.output_capacity",
                    "title": "食伤生财承载链",
                    "domain": "wealth",
                    "status": "chain_review",
                    "score": 0.68,
                    "support": ("财星可见",),
                },
            ),
            "decisions": (),
            "portrait_projection": {"axes": ()},
            "rule_runtime_hits": (),
        },
        feature_state_model={"priority_features": ()},
        structure_dynamics={
            "dominant_chain": {
                "chain_key": "output->authority->resource",
                "nodes": ("output", "authority", "resource"),
                "evidence": ("伤官",),
            },
            "chain_state": "volatile",
            "volatility_score": 0.5,
        },
        question_intent_model={"selected_question_intent": {"domain": "career"}},
        time_context={"status": "not_provided"},
    )

    gate = arbitration["quality_gate"]
    assert gate["status"] in {"review_recommended", "review_required", "pass_with_review_notes"}
    assert gate["requires_review"] is True
    assert {"evidence_thin", "single_source_bias", "close_competing_mainline", "time_layer_not_ready"} & set(gate["risk_flags"])
    assert gate["review_targets"]


def test_v20_mainline_arbitration_applies_practitioner_review_accept_primary() -> None:
    result = run_runtime_from_pillars(
        "庚午",
        "辛巳",
        "丁丑",
        "乙巳",
        input_id="v20.orchestrator.accept.primary",
        user_text="我想重点看事业和财运主线",
        flow_year_pillar="丙午",
        luck_pillar="甲申",
        practitioner_selections=(
            {
                "control_key": "control.mainline_arbitration",
                "option": "采用第一主线",
                "source_decision_keys": (),
            },
        ),
    )

    arbitration = result["mainline_arbitration"]
    assert arbitration["practitioner_review"]["action"] == "accepted_primary"
    assert arbitration["primary_mainline"]["status"] == "confirmed"
    assert arbitration["requires_review"] is False
    assert arbitration["quality_gate"]["status"] == "pass_with_practitioner_review"
    assert "practitioner_confirmed_primary" in arbitration["quality_gate"]["risk_flags"]
    assert arbitration["quality_gate"]["review_targets"] == ["命理师已确认第一主线，本轮回答按该主线展开。"]
    mainline_sections = [
        row for row in result["answer_plan"]["sections"]
        if row["section_type"] == "orchestrator_mainline"
    ]
    assert mainline_sections
    assert "人工复核：命理师已确认采用第一主线" in mainline_sections[0]["body"]
    assert "来源：规则主线" in mainline_sections[0]["body"]
    dimension_context = result["answer_plan"]["dimension_context"]
    assert dimension_context["mainline_practitioner_review"]["action"] == "accepted_primary"
    assert dimension_context["answer_strategy"]["mode"] == "confirmed_by_practitioner"
    assert dimension_context["answer_strategy"]["requires_review"] is False
    assert any(
        row["section_type"] == "orchestrator_answer_strategy"
        and "本轮主线已由命理师确认" in row["body"]
        for row in result["answer_plan"]["sections"]
    )
    prompt_mainline = result["llm_assist"]["context_pack"]["task_contexts"]["practitioner_answer"]["prompt"]["context"]["mainline"][0]
    assert prompt_mainline["practitioner_review"]["action"] == "accepted_primary"
    assert prompt_mainline["quality_gate"]["status"] == "pass_with_practitioner_review"
    prompt_context = result["llm_assist"]["context_pack"]["task_contexts"]["practitioner_answer"]["prompt"]["context"]
    assert prompt_context["answer_strategy"]["mode"] == "confirmed_by_practitioner"
    assert "回答策略：本轮主线已由命理师确认" in result["answer_text"]


def test_v20_mainline_arbitration_applies_practitioner_review_switch_to_supporting() -> None:
    base = arbitrate_mainline(
        decision_report={
            "mainlines": (
                {
                    "mainline_key": "mainline.wealth.output_capacity",
                    "title": "食伤生财承载链",
                    "domain": "wealth",
                    "status": "chain_review",
                    "score": 0.74,
                    "support": ("食伤见财", "日主承载待复核"),
                },
                {
                    "mainline_key": "mainline.career.guan_shang_yin",
                    "title": "官伤印三方链",
                    "domain": "career",
                    "status": "chain_review",
                    "score": 0.68,
                    "support": ("伤官见官", "印星可化"),
                },
            ),
            "decisions": (),
            "portrait_projection": {"axes": ()},
            "rule_runtime_hits": (),
        },
        feature_state_model={"priority_features": ()},
        structure_dynamics={
            "dominant_chain": {
                "chain_key": "wealth->authority->resource",
                "nodes": ("wealth", "authority", "resource"),
                "evidence": ("财星", "官星"),
            },
            "chain_state": "volatile",
            "volatility_score": 0.3,
        },
        question_intent_model={"selected_question_intent": {"domain": "wealth"}},
        time_context={"status": "ready"},
    )
    reviewed = arbitrate_mainline(
        decision_report={
            "mainlines": (
                {
                    "mainline_key": "mainline.wealth.output_capacity",
                    "title": "食伤生财承载链",
                    "domain": "wealth",
                    "status": "chain_review",
                    "score": 0.74,
                    "support": ("食伤见财", "日主承载待复核"),
                },
                {
                    "mainline_key": "mainline.career.guan_shang_yin",
                    "title": "官伤印三方链",
                    "domain": "career",
                    "status": "chain_review",
                    "score": 0.68,
                    "support": ("伤官见官", "印星可化"),
                },
            ),
            "decisions": (),
            "portrait_projection": {"axes": ()},
            "rule_runtime_hits": (),
        },
        feature_state_model={"priority_features": ()},
        structure_dynamics={
            "dominant_chain": {
                "chain_key": "wealth->authority->resource",
                "nodes": ("wealth", "authority", "resource"),
                "evidence": ("财星", "官星"),
            },
            "chain_state": "volatile",
            "volatility_score": 0.3,
        },
        question_intent_model={"selected_question_intent": {"domain": "wealth"}},
        time_context={"status": "ready"},
        practitioner_selections=(
            {
                "control_key": "control.mainline_arbitration",
                "option": "切换到次级主线",
                "source_decision_keys": (),
            },
        ),
    )

    assert reviewed["practitioner_review"]["action"] == "promoted_supporting"
    assert reviewed["primary_mainline"]["candidate_key"] != base["primary_mainline"]["candidate_key"]
    assert reviewed["supporting_mainlines"][0]["candidate_key"] == base["primary_mainline"]["candidate_key"]
    assert "practitioner_switched_mainline" in reviewed["quality_gate"]["risk_flags"]
