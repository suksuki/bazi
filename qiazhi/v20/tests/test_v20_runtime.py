from __future__ import annotations

import copy
import json

from v20.api.runtime import run_runtime_from_pillars as _run_runtime_from_pillars_uncached
from v20.access.projection import project_runtime_for_role
from v20.llm.client import _plain_text_messages
from v20.llm.contracts import ANSWER_PLAN_REWRITE, PRACTITIONER_ANSWER
from v20.llm.practitioner import accept_or_fallback_practitioner_answer
from v20.llm.prompts import practitioner_answer_prompt
from v20.llm.tasks import (
    accept_or_fallback_rewrite,
    draft_rule_extraction_from_knowledge,
    interpret_user_intent,
    propose_feature_candidates,
    review_output_safety,
    suggest_question_candidates,
)
from v20.knowledge.alignment import knowledge_feature_alignment
from v20.knowledge.audit import audit_default_knowledge_units
from v20.knowledge.loader import default_knowledge_units
from v20.validation.evaluator import evaluate_answer_plan, evaluate_runtime_result
from v20.validation.golden import GOLDEN_CASES
from v20.validation.synthetic_schema import SyntheticCase


_RUNTIME_CACHE: dict[tuple[object, ...], dict[str, object]] = {}


def run_runtime_from_pillars(year_pillar: str, month_pillar: str, day_pillar: str, hour_pillar: str, **kwargs):
    cache_kwargs = tuple(sorted((key, value) for key, value in kwargs.items() if key != "input_id"))
    cache_key = (year_pillar, month_pillar, day_pillar, hour_pillar, cache_kwargs)
    try:
        hash(cache_key)
    except TypeError:
        return _run_runtime_from_pillars_uncached(year_pillar, month_pillar, day_pillar, hour_pillar, **kwargs)

    if cache_key not in _RUNTIME_CACHE:
        _RUNTIME_CACHE[cache_key] = _run_runtime_from_pillars_uncached(
            year_pillar,
            month_pillar,
            day_pillar,
            hour_pillar,
            **kwargs,
        )
    result = copy.deepcopy(_RUNTIME_CACHE[cache_key])
    if "input_id" in kwargs and "input_id" in result:
        result["input_id"] = kwargs["input_id"]
    return result


def test_v20_runtime_builds_dynamic_decision_answer_plan() -> None:
    result = run_runtime_from_pillars("甲子", "戊辰", "甲午", "辛酉", input_id="v20.test")

    assert result["version"] == "v20.runtime_result.v1"
    assert result["runtime_mutation"] is False
    assert result["locale"] == "zh"
    assert result["chart_facts"]["day_master"] == "甲"
    assert result["time_context"]["status"] == "not_provided"
    assert result["core_inference"]["guardrails"]
    assert result["feature_layer"]["status"] == "ready"
    assert result["feature_layer"]["feature_count"] >= 5
    assert result["feature_layer"]["macro_feature_count"] >= 4
    feature_state_model = result["feature_state_model"]
    assert feature_state_model["status"] == "ready"
    assert feature_state_model["algorithm"] == "feature_state_fusion_phase1"
    assert feature_state_model["feature_state_count"] == result["feature_layer"]["feature_count"]
    assert feature_state_model["priority_features"]
    assert "FEATURE_STATE_IS_FUSED_RUNTIME_VIEW" in feature_state_model["guardrails"]
    trace = result["feature_layer"]["discovery_trace"]
    assert trace["status"] == "ready"
    assert trace["algorithm"] == "evidence_first_feature_discovery_phase1"
    assert trace["source"] == "ChartFacts+CoreInference+TimeContext"
    assert trace["feature_count"] == result["feature_layer"]["feature_count"]
    assert trace["evidence_atom_count"] >= result["feature_layer"]["feature_count"]
    assert trace["rule_path_count"] >= 5
    assert trace["mechanism_path_count"] >= 4
    assert trace["topic_projection_count"] >= 3
    assert trace["feature_binding_count"] == result["feature_layer"]["feature_count"]
    assert trace["counter_evidence_count"] >= 4
    assert trace["trace_node_count"] >= 5
    assert trace["model_layer_coverage_count"] == 12
    assert set(trace["model_layer_coverage"]) >= {f"L{index}" for index in range(13)} - {"L9"}
    assert trace["algorithm_completeness"]["status"] == "needs_layer_coverage"
    assert trace["algorithm_completeness"]["missing_layers"] == ("L9",)
    assert "EVIDENCE_FIRST_FEATURE_DISCOVERY" in trace["guardrails"]
    assert "BaziFeature_REMAINS_PRODUCT_CONTRACT" in trace["guardrails"]
    assert {row["state"] for row in trace["decision_states"]} & {"candidate", "weak_candidate", "requires_review"}
    assert {row["topic_domain"] for row in trace["topic_projections"]} >= {"wealth", "career", "relationship"}
    assert {row["domain"] for row in trace["evidence_atoms"]} >= {
        "chart_fact",
        "strength",
        "ten_god",
        "branch",
        "element",
        "pattern",
        "useful_god",
        "palace",
        "blind_lifa",
        "wealth",
        "archive",
        "governance",
    }
    assert any(str(row["atom_id"]).startswith("evidence.l0.") for row in trace["evidence_atoms"])
    assert any(str(row["atom_id"]).startswith("evidence.l3.") for row in trace["evidence_atoms"])
    assert any(str(row["atom_id"]).startswith("evidence.l4.") for row in trace["evidence_atoms"])
    assert any(str(row["atom_id"]).startswith("evidence.l5.") for row in trace["evidence_atoms"])
    assert any(str(row["atom_id"]).startswith("evidence.l6.") for row in trace["evidence_atoms"])
    assert any(str(row["atom_id"]).startswith("evidence.l7.") for row in trace["evidence_atoms"])
    assert any(str(row["atom_id"]).startswith("evidence.l8.") for row in trace["evidence_atoms"])
    assert any(str(row["atom_id"]).startswith("evidence.l11.") for row in trace["evidence_atoms"])
    assert any(str(row["atom_id"]).startswith("evidence.l12.") for row in trace["evidence_atoms"])
    assert any(row["rule_path_id"] for row in trace["feature_bindings"])
    assert {"pattern", "useful_god", "palace", "blind_lifa", "archive", "governance"} <= {
        row["domain"] for row in trace["rule_paths"]
    }
    assert {"trace.fact_to_evidence", "trace.decision_to_projection"} <= {
        row["trace_id"] for row in trace["trace_nodes"]
    }
    assert "counter.l11.archive_not_runtime_authority" in {
        row["counter_id"] for row in trace["counter_evidence"]
    }
    assert {row["domain"] for row in result["feature_layer"]["macro_features"]} >= {"strength", "branch", "wealth"}
    assert {row["domain"] for row in result["feature_layer"]["features"]} >= {"strength", "useful_god", "element", "branch", "wealth"}
    assert result["questions"]
    assert result["selected_question"]["question_key"]
    question_intent_model = result["question_intent_model"]
    assert question_intent_model["status"] == "ready"
    assert question_intent_model["algorithm"] == "utility_intent_ranking_phase1"
    assert question_intent_model["intent_count"] >= 8
    assert question_intent_model["question_binding_count"] == len(result["questions"])
    assert question_intent_model["selected_question_intent"]["question_key"] == result["selected_question"]["question_key"]
    assert "QUESTION_INTENTS_ARE_GENERATED_FROM_DECISION_AND_FEATURE_STATE" in question_intent_model["guardrails"]
    assert result["mainline_arbitration"]["version"] == "v20.mainline_arbitration.v1"
    assert result["mainline_arbitration"]["primary_mainline"]["nodes"]
    assert "NO_LLM_CAN_OVERRIDE_PRIMARY_MAINLINE" in result["mainline_arbitration"]["guardrails"]
    assert result["reasoning_orchestrator"]["version"] == "v20.reasoning_orchestrator.v1"
    assert result["reasoning_orchestrator"]["step_count"] >= 15
    assert any(row["step_key"] == "mainline_arbitration" for row in result["reasoning_orchestrator"]["steps"])
    assert result["knowledge_alignment"]["status"] == "pass"
    assert result["knowledge_semantic_model"]["status"] == "ready"
    assert result["knowledge_semantic_validation"]["ok"] is True
    assert result["decision_report"]["version"] == "v20.decision_report.v1"
    assert result["decision_report"]["decision_count"] >= 5
    rule_runtime = result["decision_report"]["rule_runtime_report"]
    rule_runtime_hits = result["decision_report"]["rule_runtime_hits"]
    assert result["decision_report"]["rule_runtime_source"] == "bazi_rule_spec_engine"
    assert result["decision_report"]["core_seed_decision_status"] == "active_runtime_seed"
    assert rule_runtime["status"] == "rulespec_engine_ready"
    assert rule_runtime_hits
    assert isinstance(rule_runtime_hits, (list, tuple))
    assert len(rule_runtime_hits) == rule_runtime["executed_rule_count"]
    assert all(row["rule_key"] for row in rule_runtime_hits)
    assert any(row["match_status"] in {"matched", "partial", "review_required", "blocked", "not_matched"} for row in rule_runtime_hits)
    assert rule_runtime["source"] == "bazi_rule_spec_catalog"
    assert rule_runtime["engine"] == "rulespec_evidence_atom_engine_phase1"
    assert rule_runtime["rule_count"] >= 40
    assert rule_runtime["executed_rule_count"] == rule_runtime["rule_count"]
    assert rule_runtime["directory_node_count"] == 13
    assert set(rule_runtime["covered_directory_nodes"]) == {f"L{index}" for index in range(13)}
    assert rule_runtime["runtime_allowed_count"] >= 10
    assert rule_runtime["blocked_rule_count"] >= 1
    assert any(row["rule_id"] == "rule.l3.output_to_wealth" for row in rule_runtime["rules"])
    assert any(row["match_status"] in {"matched", "partial"} for row in rule_runtime["rules"])
    assert "RULESPEC_ENGINE_IS_PRIMARY_RULE_RUNTIME" in rule_runtime["guardrails"]
    decision_model = result["decision_report"]["defeasible_decision_model"]
    assert decision_model["status"] == "ready"
    assert decision_model["algorithm"] == "defeasible_argumentation_certainty_phase1"
    assert decision_model["argument_count"] == rule_runtime["rule_count"]
    assert decision_model["decision_state_count"] == decision_model["argument_count"]
    assert decision_model["rule_decision_candidate_count"] >= 30
    assert decision_model["mainline_candidate_count"] >= 8
    assert decision_model["topic_projection_count"] >= 20
    assert {"confirmed", "mixed", "requires_review", "blocked"} <= set(decision_model["state_counts"])
    assert "out_of_scope" not in decision_model["state_counts"]
    assert any(row["rule_id"] == "rule.l3.output_to_wealth" for row in decision_model["argument_nodes"])
    assert any(row["decision_key"] == "decision.rulespec.l3.output_to_wealth" for row in decision_model["rule_decision_candidates"])
    assert "RULESPEC_RUNTIME_IS_DECISION_SOURCE" in decision_model["guardrails"]
    portrait_projection = result["decision_report"]["portrait_projection"]
    assert portrait_projection["status"] == "ready"
    assert portrait_projection["version"] == "v20.portrait_projection.v1"
    assert portrait_projection["axis_source"] == "DecisionState+MainlineDecision+TopicProjection"
    assert portrait_projection["axis_count"] >= 6
    assert portrait_projection["source_decision_model_version"] == "v20.defeasible_decision_model.v1"
    assert "PORTRAIT_IS_DECISION_STATE_PROJECTION" in portrait_projection["guardrails"]
    assert result["decision_report"]["knowledge_rule_bridge"]["version"] == "v20.decision_knowledge_rule_bridge.v1"
    assert result["decision_report"]["knowledge_rule_bridge"]["mapped_decision_count"] >= 1
    assert result["decision_report"]["knowledge_rule_bridge"]["validation_status"] == "active_ready"
    assert result["decision_report"]["decisions"][0]["knowledge_rule_refs"]
    assert result["decision_report"]["decisions"][0]["knowledge_rule_refs"][0]["runtime_allowed"] is True
    assert result["decision_report"]["decisions"][0]["knowledge_rule_refs"][0]["question_outputs"]
    assert result["decision_report"]["decisions"][0]["knowledge_rule_refs"][0]["synthetic_state"] == "unknown"
    assert result["decision_report"]["decisions"][0]["knowledge_rule_refs"][0]["runtime_activation_candidate"] is True
    assert result["decision_validation"]["ok"] is True
    assert result["decision_validation"]["knowledge_rule_bridge_status"] == "ready"
    assert result["decision_validation"]["defeasible_argument_count"] == decision_model["argument_count"]
    assert result["decision_validation"]["portrait_projection_axis_count"] == portrait_projection["axis_count"]
    assert "dynamic_portrait" not in result
    assert portrait_projection["axes"][0]["axis_id"].startswith("portrait.axis.")
    assert portrait_projection["axes"][0]["evidence_boundaries"]
    assert result["questions"][0]["dimension_layer"] in {"micro", "macro", "decision", "time"}
    assert result["answer_plan"]["dimension_context"]["version"] == "v20.answer_dimension_context.v1"
    assert result["answer_plan"]["dimension_context"]["primary_mainline"]["nodes"]
    assert result["latent_signal_report"]["version"] == "v20.latent_signal_report.v1"
    assert result["latent_signal_report"]["personal_calibration_factor_manifest"]["latent_factor_count"] == 12
    assert result["latent_event_session"]["version"] == "v20.latent_event_session_lens.v1"
    assert result["latent_event_session"]["runtime_mutation"] is False
    assert result["interaction_session"]["version"] == "v20.interaction_session_model.v1"
    assert result["interaction_session"]["status"] == "ready"
    assert result["interaction_session"]["selected_question_key"] == result["selected_question"]["question_key"]
    assert result["interaction_session"]["next_actions"]
    assert "INTERACTION_SIGNALS_RERANK_AND_CALIBRATE_ONLY" in result["interaction_session"]["guardrails"]
    assert "baseline_amplifier" in {
        row["factor_id"]
        for row in result["latent_signal_report"]["personal_calibration_factor_manifest"]["latent_factors"]
    }
    assert "feature_discovery" not in result
    assert "portrait_projection" not in result
    assert "portrait_intelligence" not in result
    assert "rule_candidate_support" not in result
    assert result["knowledge_report"]["count"] >= 6
    assert all(row["reviewed"] and row["evidence_template"] for row in result["knowledge_refs"])
    assert len(result["llm_capabilities"]) >= 6
    assert result["answer_plan"]["sections"]
    assert result["decision_report"]["mainline_count"] >= 1
    assert result["decision_report"]["mainlines"][0]["source_decision_keys"]
    sections = result["answer_plan"]["sections"]
    section_types = [row["section_type"] for row in sections]
    assert "orchestrator_mainline" in section_types
    assert "mainline_decision" in section_types
    assert "portrait_profile_summary" in section_types
    mainline_sections = [row["body"] for row in sections if row["section_type"] == "mainline_decision"]
    assert mainline_sections and "主线入口" in mainline_sections[0]
    assert any("复核重点" in row["body"] for row in result["answer_plan"]["sections"])
    assert any("复核状态" in row["body"] for row in result["answer_plan"]["sections"])
    assert result["answer_plan"]["measurement_focus"] == "bazi_measurement"
    assert result["answer_plan"]["domain_projection"]["guardrails"]
    assert "guaranteed_event" in result["answer_plan"]["domain_projection"]["blocked_claim_types"]
    assert result["prediction_policy"]["core_focus"] == "bazi_measurement"
    assert result["llm_assist"]["status"] == "idle"
    assert result["llm_assist"]["context_pack"]["publishable"] is False
    assert result["llm_assist"]["context_pack"]["runtime_mutation"] is False
    assert "answer_plan_rewrite" in result["llm_assist"]["context_pack"]["task_contexts"]
    assert "practitioner_answer" in result["llm_assist"]["context_pack"]["task_contexts"]
    assert result["llm_assist"]["answer_safety_review"]["result"]["ok"] is True


def test_v20_portrait_profile_summary_is_generated_for_runtime_answer_plan() -> None:
    result = run_runtime_from_pillars("庚午", "辛巳", "丁丑", "乙巳", input_id="v20.portrait.profile")
    sections = result["answer_plan"]["sections"]
    profile_sections = [row for row in sections if row["section_type"] == "portrait_profile_summary"]

    assert profile_sections, sections
    assert profile_sections[0]["body"]
    assert "本段为结构化合成" in profile_sections[0]["body"]
    assert "一页图谱画像" in result["answer_text"]
    assert any("复核重点" in row["body"] for row in result["answer_plan"]["sections"])


def test_v20_dynamic_decisions_drive_questions_portrait_and_interaction() -> None:
    result = run_runtime_from_pillars(
        "庚午",
        "辛巳",
        "丁丑",
        "乙巳",
        input_id="v20.feature.discovery",
        user_text="我想重点看事业和财运",
        flow_year_pillar="丙午",
        luck_pillar="甲申",
    )
    decision_domains = {row["domain"] for row in result["decision_report"]["decisions"]}
    question_domains = {row["domain"] for row in result["questions"]}

    assert result["decision_report"]["status"] == "ready"
    assert result["decision_validation"]["status"] == "pass"
    assert result["decision_report"]["portrait_projection"]["status"] == "ready"
    assert result["portrait_graph_summary"]["status"] == "ready"
    assert result["portrait_graph_summary"]["headline"]
    assert result["portrait_graph_summary"]["profile_tags"]
    assert result["portrait_graph_summary"]["suggested_questions"]
    assert "PORTRAIT_GRAPH_USES_TAGS_NOT_RULE_DEBUG" in result["portrait_graph_summary"]["guardrails"]
    assert {"career", "wealth"} & decision_domains
    assert {"career", "wealth"} & question_domains
    assert result["llm_assist"]["status"] == "ready"
    assert result["knowledge_semantic_validation"]["status"] == "pass"
    assert result["runtime_mutation"] is False
    assert "当前命局可见" in result["answer_text"]
    assert "八字测算重点" not in result["answer_text"]
    assert "知识依据" not in result["answer_text"]
    assert "core." not in result["answer_text"]
    assert "feature." not in result["answer_text"]
    assert result["measurement_report"]["core_focus"] == "bazi_measurement"
    assert result["measurement_report"]["selected_question_key"] == result["selected_question"]["question_key"]
    assert result["questions"][0]["question_key"] == result["selected_question"]["question_key"]
    context = result["bazi_context_frame"]
    context_id = context["context_id"]
    assert context["natal_pillars"] == {"year": "庚午", "month": "辛巳", "day": "丁丑", "hour": "乙巳"}
    assert {row["layer_key"] for row in context["time_layers"]} == {"luck", "flow_year"}
    assert result["structure_dynamics"]["context_binding"]["context_id"] == context_id
    assert result["structure_dynamics"]["context_binding"]["evidence_anchor_count"] >= 1
    assert result["decision_report"]["portrait_projection"]["context_binding"]["context_id"] == context_id
    assert result["decision_report"]["portrait_projection"]["context_binding"]["evidence_anchor_count"] >= 1
    assert result["question_intent_model"]["context_binding"]["context_id"] == context_id
    assert result["question_intent_model"]["context_binding"]["evidence_anchor_count"] >= 1
    assert result["question_context_binding"]["context_id"] == context_id
    assert result["llm_assist"]["context_pack"]["context_binding"]["context_id"] == context_id
    context_alignment = result["context_alignment_report"]
    assert context_alignment["context_id"] == context_id
    assert context_alignment["drift_score"] == 0
    assert context_alignment["aligned_count"] == context_alignment["module_count"]
    assert all(row["evidence_anchor_count"] >= 1 for row in context_alignment["modules"])
    assert {row["module_key"] for row in context_alignment["modules"]} == {
        "structure_dynamics",
        "portrait_projection",
        "question_intent_model",
        "mainline_arbitration",
        "llm_context_pack",
    }
    assert all(row["role"] == "bazi_measurement_entry" for row in result["questions"])
    assert all(row["measurement_topic"] for row in result["questions"])
    assert all(row["alignment_status"] in {"bazi_core_aligned", "bazi_projection_aligned"} for row in result["questions"])
    assert all(row["bazi_focus"] for row in result["questions"])
    assert {"career", "wealth", "element"} & {row["domain"] for row in result["questions"]}
    trace = result["feature_layer"]["discovery_trace"]
    assert trace["algorithm"] == "evidence_first_feature_discovery_phase1"
    assert "time" in {row["domain"] for row in trace["evidence_atoms"]}
    assert any(str(row["atom_id"]).startswith("evidence.l9.") for row in trace["evidence_atoms"])
    assert "volatile" in {row["state"] for row in trace["decision_states"]}
    assert trace["algorithm_completeness"]["status"] == "complete_phase1_model"
    assert trace["algorithm_completeness"]["missing_layers"] == ()
    assert set(trace["model_layer_coverage"]) == {f"L{index}" for index in range(13)}


def test_v20_hidden_wealth_stays_boundary_not_mainline() -> None:
    result = run_runtime_from_pillars("甲子", "丙寅", "甲辰", "辛酉", input_id="v20.hidden.wealth")

    wealth_features = {
        row["feature_id"]
        for row in result["feature_layer"]["features"]
        if row["domain"] == "wealth"
    }
    mainline_domains = [row["domain"] for row in result["decision_report"]["mainlines"]]
    wealth_decisions = {
        row["decision_key"]: row
        for row in result["decision_report"]["decisions"]
        if row["domain"] == "wealth"
    }

    assert "feature.wealth.hidden_material" in wealth_features
    assert "feature.wealth.visible_material" not in wealth_features
    assert "wealth" not in mainline_domains[:3]
    assert wealth_decisions["decision.wealth.material"]["status"] == "hidden_material_review"
    assert all("食伤生财" not in row["title"] for row in result["questions"][:3])


def test_v20_output_authority_structure_not_demoted_to_output_wealth() -> None:
    result = run_runtime_from_pillars(
        "丁巳",
        "乙巳",
        "乙丑",
        "乙酉",
        luck_pillar="庚子",
        flow_year_pillar="丙午",
        source_role="admin",
    )

    chain = result["structure_dynamics"]["primary_dynamic_chain"]
    primary = result["mainline_arbitration"]["primary_mainline"]
    brain = result["brain_state"]["public_summary"]

    assert result["chart_facts"]["day_master"] == "乙"
    assert tuple(chain["nodes"][:2]) == ("output", "authority")
    assert "食伤生财" not in chain["pattern_label"]
    assert primary["domain"] == "career"
    assert {"output", "authority"}.issubset(set(primary["nodes"]))
    assert primary["title"] != "食伤生财规则：明确成立"
    assert brain["primary_title"] != "食伤生财"
    assert "食伤生财" not in result["answer_text"]

    knowledge_sections = [
        row for row in result["answer_plan"]["sections"]
        if row["section_type"] == "decision_knowledge_support"
    ]
    assert knowledge_sections
    assert "食伤生财" not in knowledge_sections[0]["body"]
    assert "财星" not in knowledge_sections[0]["body"]

    projected = project_runtime_for_role(result, "admin")
    assert "dominant_chain" not in projected["structure_dynamics"]
    assert projected["structure_dynamics"]["primary_dynamic_chain"]["pattern_label"] == chain["pattern_label"]


def test_v20_dynamic_decisions_use_practitioner_ready_bazi_rule_language() -> None:
    result = run_runtime_from_pillars(
        "甲子",
        "戊辰",
        "甲午",
        "辛酉",
        input_id="v20.rule.language",
        user_text="我想看事业和财运",
    )
    decisions = {row["rule_key"]: row for row in result["decision_report"]["decisions"]}
    questions = [row["title"] for row in result["questions"]]

    shang_guan = decisions["rule.ten_god.shang_guan_jian_guan"]
    wealth_capacity = decisions["rule.wealth.capacity_gate"]
    output_to_wealth = decisions["rule.ten_god.output_to_wealth"]

    assert shang_guan["label"] == "伤官见官见印缓冲"
    assert shang_guan["status"] == "weakened_by_resource"
    assert "表达冲规则但见印星缓冲" in shang_guan["portrait_tags"]
    assert wealth_capacity["label"] == "财星可见但日主承接需扶助"
    assert "财运要先看扶身与承接" in wealth_capacity["portrait_tags"]
    assert output_to_wealth["label"] == "食伤生财通道候选"
    assert any("伤官@" in row for row in output_to_wealth["support"])
    assert any("财@" in row for row in output_to_wealth["support"])
    assert "事业上官星、伤官和印星谁是主导？" in questions
    assert "食伤生财时，日主承接够不够？" in questions
    assert "把官星规则、伤官表达和印星缓冲放在一起裁决主次" in result["answer_text"]


def test_v20_useful_god_and_pattern_decisions_use_bazi_language() -> None:
    support_case = run_runtime_from_pillars(
        "甲子",
        "戊辰",
        "甲午",
        "辛酉",
        input_id="v20.useful.support",
        user_text="我想看用神",
    )
    release_case = run_runtime_from_pillars(
        "壬寅",
        "甲辰",
        "丙子",
        "甲午",
        input_id="v20.useful.release",
        user_text="我想看用神",
    )
    support_decisions = {row["rule_key"]: row for row in support_case["decision_report"]["decisions"]}
    release_decisions = {row["rule_key"]: row for row in release_case["decision_report"]["decisions"]}

    assert support_decisions["rule.useful_god.candidate_gate"]["label"] == "用神候选先看扶身路径"
    assert "用神候选偏向扶助日主" in support_decisions["rule.useful_god.candidate_gate"]["portrait_tags"]
    assert "这个盘的用神和调节方向是什么" in support_case["selected_question"]["title"]
    assert "先扶身" not in support_case["selected_question"]["title"]
    assert release_decisions["rule.useful_god.candidate_gate"]["label"] == "用神候选先看泄秀路径"
    assert "这个盘的用神和调节方向是什么" in release_case["selected_question"]["title"]
    assert "先看泄秀还是" not in release_case["selected_question"]["title"]
    assert support_decisions["rule.pattern.review_gate"]["label"] == "格局需先看墓库藏气"
    assert "月柱墓库藏气需要格局复核" in support_decisions["rule.pattern.review_gate"]["support"]
    assert "support:" not in support_case["answer_text"]
    assert "release:" not in release_case["answer_text"]


def test_v20_strength_decision_exposes_support_and_pressure_materials() -> None:
    weak_case = run_runtime_from_pillars(
        "甲子",
        "戊辰",
        "甲午",
        "辛酉",
        input_id="v20.strength.weak",
        user_text="我想看强弱",
    )
    border_case = run_runtime_from_pillars(
        "乙亥",
        "己丑",
        "辛酉",
        "丙申",
        input_id="v20.strength.border",
        user_text="我想看强弱",
    )
    weak_strength = next(
        row for row in weak_case["decision_report"]["decisions"]
        if row["rule_key"] == "rule.strength.capacity"
    )
    border_strength = next(
        row for row in border_case["decision_report"]["decisions"]
        if row["rule_key"] == "rule.strength.capacity"
    )

    assert weak_strength["label"] == "日主偏弱需扶身复核"
    assert "日主需先看扶身" in weak_strength["portrait_tags"]
    assert any(row.startswith("扶身材料：") for row in weak_strength["support"])
    assert any(row.startswith("泄耗克制材料：") for row in weak_strength["support"])
    assert weak_case["selected_question"]["title"] == "日主需要扶身时，先看印星、比劫还是通关？"
    assert "先找印星、比劫和通关条件" in weak_case["answer_text"]
    assert border_strength["label"] == "日主强弱接近分界需裁决"
    assert border_case["selected_question"]["title"] == "日主强弱接近分界时，先比较哪类证据？"
    assert "不能急着定强弱" in border_case["answer_text"]


def test_v20_combination_chain_decisions_drive_main_questions() -> None:
    wealth_case = run_runtime_from_pillars(
        "甲子",
        "戊辰",
        "甲午",
        "辛酉",
        input_id="v20.chain.wealth",
        user_text="我想看财运",
    )
    career_case = run_runtime_from_pillars(
        "壬寅",
        "甲辰",
        "丙子",
        "甲午",
        input_id="v20.chain.career",
        user_text="我想看事业",
    )
    wealth_decisions = {row["rule_key"]: row for row in wealth_case["decision_report"]["decisions"]}
    career_decisions = {row["rule_key"]: row for row in career_case["decision_report"]["decisions"]}

    assert wealth_decisions["rule.wealth.output_wealth_capacity_chain"]["label"] == "食伤生财需先过承载关"
    assert "日主偏弱需扶身复核" in wealth_decisions["rule.wealth.output_wealth_capacity_chain"]["support"]
    assert wealth_case["selected_question"]["title"] == "食伤生财时，日主承接够不够？"
    assert "有食伤生财线索，但要先过日主承载关" in wealth_case["answer_text"]
    assert career_decisions["rule.career.output_authority_resource_chain"]["label"] == "官伤印三方需要合参"
    assert career_case["selected_question"]["title"] == "事业上官星、伤官和印星谁是主导？"
    assert "官星规则、伤官表达和印星缓冲" in career_case["answer_text"]
    source_report = career_case["question_source_ranking_report"]
    assert source_report["version"] == "v20.question_source_ranking_report.v1"
    assert source_report["question_count"] == len(career_case["questions"])
    assert source_report["rows"][0]["question_id"] == career_case["questions"][0]["question_id"]
    assert "QUESTION_SOURCE_REPORT_IS_READ_ONLY" in source_report["guardrails"]


def test_v20_practitioner_selection_refreshes_question_ranking_without_rule_mutation() -> None:
    result = run_runtime_from_pillars(
        "壬寅",
        "甲辰",
        "丙子",
        "甲午",
        input_id="v20.practitioner.selection",
        user_text="我想看事业和财运",
        practitioner_selections=(
            {
                "control_key": "control.shang_guan_jian_guan",
                "option": "成立",
                "source_decision_keys": ("decision.ten_god.shang_guan_jian_guan",),
            },
        ),
    )

    assert result["practitioner_session"]["selection_count"] == 1
    assert result["practitioner_session"]["questions_refreshed"] is True
    assert result["practitioner_session"]["runtime_mutation"] is False
    assert result["practitioner_session"]["selection_effects"][0]["effect"] == "question_ranking_refresh"
    assert result["practitioner_session"]["selection_effects"][0]["runtime_rule_mutation"] is False
    assert result["selected_question"]["question_key"] == "q_career_structure"
    assert result["questions"][0]["title"] == "伤官见官已判成立，先看冲突来源还是化解路径？"
    assert "PRACTITIONER_SELECTIONS_ARE_SESSION_LENS_ONLY" in result["practitioner_session"]["guardrails"]
    assert "QUESTION_RANKING_REFRESHES_CURRENT_SESSION" in result["practitioner_session"]["guardrails"]
    assert result["decision_report"]["runtime_mutation"] is False


def test_v20_latent_event_answers_refresh_question_ranking_without_rule_mutation() -> None:
    result = run_runtime_from_pillars(
        "壬寅",
        "甲辰",
        "丙子",
        "甲午",
        input_id="v20.latent.event.selection",
        user_text="我想看事业和财运",
        latent_event_answers=(
            {
                "scenario_id": "latent.wealth_change",
                "year_option": "25_to_30",
                "result_option": "resource_pressure",
                "intensity": "strong",
                "confidence": "high",
            },
        ),
    )

    assert result["latent_event_session"]["answer_count"] == 1
    assert result["latent_event_session"]["questions_refreshed"] is True
    assert result["latent_event_session"]["runtime_mutation"] is False
    assert result["latent_event_session"]["selection_effects"][0]["effect"] == "personal_factor_question_ranking_refresh"
    assert result["latent_event_session"]["selection_effects"][0]["runtime_rule_mutation"] is False
    assert result["selected_question"]["domain"] == "wealth"
    assert result["questions"][0]["title"] == "财务压力出现时，命局里先看承载力还是外部牵动？"
    assert "LATENT_EVENTS_ARE_PERSONAL_CALIBRATION_LENS_ONLY" in result["latent_event_session"]["guardrails"]
    assert result["decision_report"]["runtime_mutation"] is False


def test_v20_validation_and_llm_fallback_are_guarded(monkeypatch) -> None:
    monkeypatch.setenv("V20_LLM_ENABLED", "0")
    monkeypatch.setenv("V20_LLM_EXECUTE", "0")
    result = run_runtime_from_pillars("甲子", "戊辰", "甲午", "辛酉", input_id="v20.validation")
    rewritten = _run_runtime_from_pillars_uncached(
        "甲子",
        "戊辰",
        "甲午",
        "辛酉",
        input_id="v20.validation.rewrite",
        user_text="请按命理结构说明一下",
        llm_mode="rewrite",
    )
    practitioner = _run_runtime_from_pillars_uncached(
        "甲子",
        "戊辰",
        "甲午",
        "辛酉",
        input_id="v20.validation.practitioner",
        user_text="请像命理师一样说明主线",
        llm_mode="practitioner",
    )
    case = GOLDEN_CASES[0]
    eval_result = evaluate_answer_plan(
        case,
        _feature_layer_obj(result),
        _question_objs(result),
        _answer_plan_obj(result),
    )

    assert eval_result["ok"] is True
    bad = accept_or_fallback_rewrite(_answer_plan_obj(result), "一定发财，feature.x")
    assert bad["ok"] is False
    assert bad["source"] == "deterministic_fallback"
    hidden_bad = accept_or_fallback_rewrite(_answer_plan_obj(result), "你会在未来发大财")
    assert hidden_bad["ok"] is False
    assert "forbidden_semantic_pattern" in hidden_bad["validation"]["failures"]
    assert ANSWER_PLAN_REWRITE.task_name == "answer_plan_rewrite"
    safe = review_output_safety(result["answer_text"])
    assert safe["result"]["ok"] is True
    assert safe["answer_governance_quality"]["quality_score"] > 0
    assert "answer_governance_quality" in result["llm_assist"]["answer_safety_review"]
    assert rewritten["llm_assist"]["answer_rewrite"]["status"] == "fallback"
    assert rewritten["llm_assist"]["answer_rewrite"]["source"] == "deterministic_fallback"
    assert rewritten["llm_assist"]["answer_safety_review"]["result"]["ok"] is True
    assert practitioner["llm_assist"]["practitioner_answer"]["status"] == "fallback"
    assert practitioner["llm_assist"]["practitioner_answer"]["source"] == "deterministic_fallback"
    assert practitioner["llm_assist"]["answer_safety_review"]["result"]["ok"] is True


def test_v20_practitioner_answer_accepts_only_verified_context_text() -> None:
    safe = accept_or_fallback_practitioner_answer(
        {
            "text": "命理主线先看日主承载、十神来源和地支互动，再回答当前问题的结构边界。",
            "mainline": "日主承载、十神来源、地支互动。",
            "question_answer": "只解释已验证结构，不扩展为事件。",
            "evidence_notes": ["已接入特征发现和知识边界。"],
            "next_questions": ["是否继续看用神候选？"],
            "boundary_notes": ["不输出固定吉凶。"],
        },
        "deterministic",
    )
    bad = accept_or_fallback_practitioner_answer(
        {
            "text": "你一定发财。",
            "mainline": "越界",
            "question_answer": "越界",
            "evidence_notes": [],
            "next_questions": [],
            "boundary_notes": [],
        },
        "deterministic",
    )

    assert safe["ok"] is True
    assert safe["source"] == "llm_practitioner_answer"
    assert bad["ok"] is False
    assert bad["source"] == "deterministic_fallback"


def test_v20_practitioner_answer_rejects_wrong_day_master() -> None:
    wrong = accept_or_fallback_practitioner_answer(
        {
            "text": "这个盘是甲木日主，先看日主承载和财官结构。",
            "mainline": "日主承载。",
            "question_answer": "按结构说明。",
            "evidence_notes": ["当前命盘。"],
            "next_questions": [],
            "boundary_notes": ["不重算命盘。"],
        },
        "deterministic fallback",
        expected_day_master="乙",
    )
    safe = accept_or_fallback_practitioner_answer(
        {
            "text": "这个盘是乙木日主，先看日主承载和财官结构。",
            "mainline": "日主承载。",
            "question_answer": "按结构说明。",
            "evidence_notes": ["当前命盘。"],
            "next_questions": [],
            "boundary_notes": ["不重算命盘。"],
        },
        "deterministic fallback",
        expected_day_master="乙",
    )

    assert wrong["ok"] is False
    assert wrong["source"] == "deterministic_fallback"
    assert "day_master_mismatch:甲_mentioned_expected_乙" in wrong["validation"]["failures"]
    assert safe["ok"] is True


def test_v20_explicit_time_layer_routes_to_time_measurement() -> None:
    result = run_runtime_from_pillars(
        "甲子",
        "戊辰",
        "甲午",
        "辛酉",
        input_id="v20.time",
        user_text="我想看流年触发",
        flow_year_pillar="庚子",
    )

    assert result["time_context"]["status"] == "ready"
    assert result["time_context"]["layers"][0]["layer_key"] == "flow_year"
    assert result["time_context"]["layers"][0]["ten_god"]["label"] == "七杀"
    assert {row["layer"] for row in result["time_context"]["relation_hits"]} == {"time"}
    assert "time" in {row["domain"] for row in result["feature_layer"]["features"]}
    assert result["selected_question"]["question_key"] == "q_time_layer_context"
    assert result["selected_question"]["domain"] == "time"
    assert {"q_time_layer_context", "q_time_relation_triggers"} <= {
        row["question_key"] for row in result["questions"]
    }
    assert "time" in {row["domain"] for row in result["knowledge_refs"]}
    assert result["llm_assist"]["routed_question_key"] == "q_time_layer_context"
    assert "大运流年正在参与判断" in result["answer_text"]
    assert "庚子=七杀" in result["answer_text"]
    assert "日柱午与流年子冲" in result["answer_text"]
    assert "发财" not in result["answer_text"]


def test_v20_answers_include_verified_hidden_ten_god_material() -> None:
    result = run_runtime_from_pillars(
        "壬寅",
        "甲辰",
        "丙子",
        "甲午",
        input_id="v20.hidden-ten-god",
        question_key="q_hidden_stem_role",
    )

    assert result["selected_question"]["question_key"] == "q_hidden_stem_role"
    assert "明透和藏干要分开看" in result["answer_text"]
    assert "正官" in result["answer_text"]
    assert "七杀" in result["answer_text"]
    assert "feature." not in result["answer_text"]


def test_v20_p85_applied_domain_answers_use_professional_reading_paths() -> None:
    result = run_runtime_from_pillars(
        "壬寅",
        "甲辰",
        "丙子",
        "甲午",
        input_id="v20.p85.wealth",
        question_key="q_income_stability",
        flow_year_pillar="丙午",
        luck_pillar="庚戌",
    )

    assert "q_income_stability" in {row["question_key"] for row in result["questions"]}
    assert result["selected_question"]["question_key"] == "q_income_stability"
    assert result["selected_question"]["domain"] == "wealth"
    assert "当前命局可见" in result["answer_text"]
    assert "财星" in result["answer_text"]
    assert "知识依据" not in result["answer_text"]
    assert "财运判断范围" not in result["answer_text"]
    assert "规则候选" not in result["answer_text"]
    assert "影子复核" not in result["answer_text"]
    assert "下一步" not in result["answer_text"]
    assert "收益结果" not in result["answer_text"]
    assert "feature." not in result["answer_text"]
    assert "decision_knowledge_support" in {
        row["section_type"] for row in result["answer_plan"]["sections"]
    }
    assert "portrait_projection_reading" in {row["section_type"] for row in result["answer_plan"]["sections"]}
    synthetic = SyntheticCase(
        "v20.synthetic.wealth-rule-candidate",
        ("壬寅", "甲辰", "丙子", "甲午"),
        expected_feature_domains=("wealth", "ten_god", "strength"),
        expected_question_keys=("q_income_stability",),
        expected_rule_candidate_domains=("wealth",),
    )
    assert evaluate_runtime_result(synthetic, result)["ok"] is True


def test_v20_p85_time_answer_preserves_trigger_path_section() -> None:
    result = run_runtime_from_pillars(
        "壬寅",
        "甲辰",
        "丙子",
        "甲午",
        input_id="v20.p85.time",
        question_key="q_time_relation_triggers",
        flow_year_pillar="丙午",
        luck_pillar="庚戌",
    )

    assert "大运流年正在参与判断" in result["answer_text"]
    assert "庚戌=偏财" in result["answer_text"]
    assert "丙午=比肩" in result["answer_text"]
    assert "月柱辰与大运戌冲" in result["answer_text"]
    assert "大运流年判断范围" not in result["answer_text"]
    assert "下一步" not in result["answer_text"]
    assert "feature." not in result["answer_text"]


def test_v20_multilingual_answer_rendering_uses_deterministic_terms() -> None:
    en = run_runtime_from_pillars(
        "甲子",
        "戊辰",
        "甲午",
        "辛酉",
        input_id="v20.locale.en",
        locale="en",
        user_text="timing",
        flow_year_pillar="庚子",
    )
    ko = run_runtime_from_pillars(
        "甲子",
        "戊辰",
        "甲午",
        "辛酉",
        input_id="v20.locale.ko",
        locale="ko",
        user_text="세운",
        flow_year_pillar="庚子",
    )

    assert "time layer and flow triggers" in en["answer_text"]
    assert "命理测算主线" not in en["answer_text"]
    assert "시간층과 세운 촉발" in ko["answer_text"]
    assert "命理测算主线" not in ko["answer_text"]
    assert en["llm_assist"]["answer_safety_review"]["result"]["ok"] is True
    assert ko["llm_assist"]["answer_safety_review"]["result"]["ok"] is True


def test_v20_knowledge_and_llm_are_aligned_but_assistive() -> None:
    result = run_runtime_from_pillars("甲子", "戊辰", "甲午", "辛酉", input_id="v20.llm")
    routed = run_runtime_from_pillars(
        "甲子",
        "戊辰",
        "甲午",
        "辛酉",
        input_id="v20.llm.routed",
        user_text="我想看财和用神",
    )
    feature_layer = _feature_layer_obj(result)
    questions = _question_objs(result)

    audit = audit_default_knowledge_units()
    alignment = knowledge_feature_alignment(feature_layer)
    intent = interpret_user_intent("我想看财和用神，以及有没有地支冲合", feature_layer)
    suggestions = suggest_question_candidates("我想看财和用神", feature_layer, questions)
    proposals = propose_feature_candidates("我想看财和用神", feature_layer)
    rule_draft = draft_rule_extraction_from_knowledge(default_knowledge_units()[0])

    assert audit["status"] == "pass"
    assert alignment["status"] == "pass"
    assert intent["runtime_mutation"] is False
    assert {"wealth", "useful_god", "branch"} <= set(intent["result"]["feature_domains"])
    assert suggestions["runtime_mutation"] is False
    assert proposals["runtime_mutation"] is False
    assert all(row["status"] == "proposal_only" for row in proposals["candidates"])
    assert rule_draft["runtime_mutation"] is False
    assert rule_draft["validation"]["ok"] is True
    assert rule_draft["draft"]["status"] == "draft_only"
    assert routed["llm_assist"]["status"] == "ready"
    assert routed["llm_assist"]["routed_question_key"] == "q_useful_god_candidates"
    assert routed["llm_assist"]["context_pack"]["user_text_present"] is True
    assert routed["llm_assist"]["context_pack"]["knowledge_ref_count"] >= 1
    practitioner_context = routed["llm_assist"]["context_pack"]["task_contexts"]["practitioner_answer"]["prompt"]
    assert practitioner_context["prompt_profile"]["role_key"] == "practitioner"
    assert practitioner_context["prompt_profile"]["role"] == "professional_bazi_practitioner"
    assert practitioner_context["prompt_profile"]["language_instruction"]
    assert practitioner_context["prompt_profile"]["answer_prompt_profile"]["voice_profile"] == "practitioner_evidence_review"
    assert practitioner_context["answer_prompt_profile"]["required_elements"] == ("evidence", "boundary", "counterexample_condition")
    assert practitioner_context["answer_contract"]["voice_profile"] == "practitioner_evidence_review"
    assert practitioner_context["context_version"] == "v20.practitioner_answer_card.v2"
    assert "system_understanding" in practitioner_context["context"]
    assert practitioner_context["context"]["system_understanding"]["mainline_rules"]
    assert practitioner_context["context"]["system_understanding"]["role_context"]["context_density"] == "practitioner_evidence_review"
    assert practitioner_context["context"]["system_understanding"]["bazi_context_profile"]["active_domains"]
    assert "knowledge_domains" in practitioner_context["context"]["system_understanding"]
    assert "question" in practitioner_context["context"]
    assert "chart" in practitioner_context["context"]
    assert "brain_state" in practitioner_context["context"]
    assert practitioner_context["context"]["brain_state"]["primary_title"]
    assert practitioner_context["context"]["brain_state"]["selected_question_title"] == routed["selected_question"]["title"]
    assert "mainline" in practitioner_context["context"]
    assert "portrait_tags" in practitioner_context["context"]
    assert "answer_plan" not in practitioner_context["context"]
    assert "decision_report" not in practitioner_context["context"]
    assert "knowledge_semantic_domains" not in practitioner_context["context"]
    assert practitioner_context["context"]["context_budget"]["target_chars"] == 5200
    assert practitioner_context["context"]["dynamic_context"]["boundary"]
    assert len(json.dumps(practitioner_context, ensure_ascii=False)) < 9000
    assert routed["selected_question"]["question_key"] == "q_useful_god_candidates"
    assert routed["llm_assist"]["answer_safety_review"]["result"]["ok"] is True
    prompt = practitioner_answer_prompt(
        chart_facts=routed["chart_facts"],
        time_context=routed["time_context"],
        selected_question=routed["selected_question"],
        knowledge_semantic_model=routed["knowledge_semantic_model"],
        answer_plan=_answer_plan_obj(routed),
        verified_answer_text=routed["answer_text"],
        decision_report=routed["decision_report"],
        portrait_projection=routed["decision_report"]["portrait_projection"],
        feature_state_model=routed["feature_state_model"],
        question_intent_model=routed["question_intent_model"],
        interaction_session=routed["interaction_session"],
        locale="en",
    )
    assert prompt["prompt_profile"]["language_instruction"].startswith("Write the final user-facing text in English")
    assert prompt["answer_prompt_profile"]["locale_policy"]["locale"] == "en"
    assert prompt["answer_contract"]["voice_profile"] == "practitioner_evidence_review"
    assert "system_understanding" in prompt["context"]
    assert prompt["context"]["system_understanding"]["role_context"]["focus"]
    assert prompt["context"]["system_understanding"]["bazi_context_profile"]["structure_mode"]
    assert prompt["context_version"] == "v20.practitioner_answer_card.v2"
    assert prompt["context"]["chart"]["day_master"]
    assert "immutable_fact" in prompt["context"]["chart"]
    assert "不得改写或重算" in prompt["context"]["chart"]["immutable_fact"]
    assert "wood" not in prompt["context"]["chart"]["immutable_fact"]
    assert prompt["context"]["question"]["title"] == (
        routed["selected_question"].get("display_title") or routed["selected_question"]["title"]
    )
    assert prompt["context"]["selected_question_anchor"]["context_id"] == routed["selected_question"]["question_anchor"]["context_id"]
    assert prompt["context"]["selected_question_anchor"]["day_master"] == routed["chart_facts"]["day_master"]
    assert prompt["context"]["selected_question_anchor"]["why_this_question"]
    assert prompt["context"]["intent"]["question_key"] == routed["selected_question"]["question_key"]
    assert prompt["context"]["mainline"]
    assert prompt["context"]["portrait_tags"]
    assert prompt["context"]["evidence"]
    assert prompt["context"]["context_budget"]["policy"] == "compact_verified_context"
    assert "knowledge_rules" not in json.dumps(prompt["context"], ensure_ascii=False)
    assert len(json.dumps(prompt, ensure_ascii=False)) < 9000
    stream_messages = _plain_text_messages(PRACTITIONER_ANSWER, prompt)
    stream_payload = json.dumps(stream_messages, ensure_ascii=False)
    assert len(stream_payload) < 7800
    assert "prompt_profile" not in stream_payload
    assert "answer_prompt_profile" not in stream_payload
    assert "output_schema" not in stream_payload


def _feature_layer_obj(result):
    from v20.features.schema import BaziFeature, EvidenceRef, FeatureLayer

    features = []
    for row in result["feature_layer"]["features"]:
        features.append(
            BaziFeature(
                feature_id=row["feature_id"],
                title=row["title"],
                domain=row["domain"],
                source_layers=tuple(row["source_layers"]),
                evidence_refs=tuple(EvidenceRef(**ref) for ref in row["evidence_refs"]),
                confidence=row["confidence"],
                readiness=row["readiness"],
                boundary=row["boundary"],
                question_hooks=tuple(row["question_hooks"]),
                answer_hooks=tuple(row["answer_hooks"]),
                calibration_state=row["calibration_state"],
            )
        )
    return FeatureLayer(version=result["feature_layer"]["version"], status=result["feature_layer"]["status"], features=tuple(features))


def _question_objs(result):
    from v20.interaction.questions import QuestionCandidate

    return tuple(QuestionCandidate(**row) for row in result["questions"])


def _answer_plan_obj(result):
    from v20.answer.evidence import EvidencePack
    from v20.answer.plan import AnswerPlan, AnswerSection

    pack = result["answer_plan"]["evidence_pack"]
    return AnswerPlan(
        version=result["answer_plan"]["version"],
        question_key=result["answer_plan"]["question_key"],
        sections=tuple(AnswerSection(**row) for row in result["answer_plan"]["sections"]),
        evidence_pack=EvidencePack(
            version=pack["version"],
            feature_ids=tuple(pack["feature_ids"]),
            evidence_refs=tuple(pack["evidence_refs"]),
            boundaries=tuple(pack["boundaries"]),
            measurement_domains=tuple(pack["measurement_domains"]),
            guardrails=tuple(pack["guardrails"]),
        ),
        measurement_focus=result["answer_plan"]["measurement_focus"],
        prediction_policy=result["answer_plan"]["prediction_policy"],
        domain_projection=result["answer_plan"]["domain_projection"],
        guardrails=tuple(result["answer_plan"]["guardrails"]),
    )
