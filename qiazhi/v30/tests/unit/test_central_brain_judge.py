from __future__ import annotations

from v30.brain.final_synthesis import build_final_synthesis
from v30.brain.judge import (
    BRAIN_JUDGE_VERSION,
    judge_final_synthesis_quality,
    judge_llm_derivation_quality,
)


def test_brain_judge_accepts_traceable_conclusion_and_actionable_advice() -> None:
    result = judge_final_synthesis_quality(
        conclusion="结论：当前事业主线落在职责压力转资质平台，核心依据是官杀压力由印星承接。",
        advice="建议：先确认职责边界，把压力拆成证书、规则和可交付成果，避免同时转向多个方向。",
        evidence_chain=[
            {
                "claim_id": "claim.career",
                "domain": "career",
                "score": 0.82,
                "evidence": ["官杀 -> 印星", "事业画像以规则压力为主"],
            }
        ],
        top_claims=[
            {
                "claim_id": "claim.career",
                "domain": "career",
                "score": 0.82,
                "requires_question": False,
            }
        ],
        feedback_summary={"active_signal_count": 1},
    )

    assert result["version"] == BRAIN_JUDGE_VERSION
    assert result["accepted"] is True
    assert result["quality_score"] >= 0.58
    assert "evidence_chain_bound" in result["reason_codes"]
    assert result["chart_fact_mutation_allowed"] is False


def test_brain_judge_rejects_template_or_untraceable_summary() -> None:
    result = judge_final_synthesis_quality(
        conclusion="当前阶段综合来看，可以参考后续分析，暂时无法定论。",
        advice="建议您重点关注后续流程，当前仅供参考。",
        evidence_chain=[],
        top_claims=[],
    )

    assert result["accepted"] is False
    assert "weak_evidence_binding" in result["failures"]
    assert "template_or_filler_language" in result["failures"]
    assert "conclusion_not_first" in result["failures"]


def test_brain_judge_accepts_evidence_bound_branch_language() -> None:
    result = judge_final_synthesis_quality(
        conclusion="结论：用神取向有土火两条候选分支，土的置信更高，因为官杀压力需要先由承接路径稳定。",
        advice="建议：先按土承接路径执行，若火势过旺或燥性反证增强，则把火分支降权。",
        evidence_chain=[
            {
                "claim_id": "claim.useful_god",
                "domain": "structure",
                "score": 0.78,
                "evidence": ["用神候选：土承接为主", "反证：火过旺加重燥性"],
            }
        ],
        top_claims=[
            {
                "claim_id": "claim.useful_god",
                "domain": "structure",
                "score": 0.78,
                "requires_question": False,
            }
        ],
    )

    assert result["accepted"] is True
    assert result["scores"]["template_risk"] < 0.34
    assert "overclaim_or_fixed_verdict_risk" not in result["failures"]


def test_final_synthesis_exposes_brain_judge_quality_contract() -> None:
    synthesis = build_final_synthesis(
        diagnosis={
            "claims": [
                {
                    "claim_id": "claim.career",
                    "domain": "career",
                    "claim_level": "domain",
                    "claim_text": "事业主线落在职责压力与资质承接，需要先判断平台规则和可交付能力。",
                    "path_ids": ["path.career"],
                    "portrait_ids": ["portrait.career"],
                }
            ],
            "paths": [{"path_id": "path.career", "path_label": "官杀 -> 印星"}],
            "portraits": [{"portrait_id": "portrait.career", "statement": "事业画像以规则压力和资源承接为主。"}],
        },
        claim_scores=[
            {
                "claim_id": "claim.career",
                "domain": "career",
                "claim_level": "domain",
                "score": 0.82,
                "confidence_band": "high",
                "requires_question": False,
                "components": {"feedback_alignment": 0.4, "feedback_contradiction": 0.0},
            }
        ],
        practical_reading_context={
            "domain_readings": {
                "career": {
                    "priority_score": 0.91,
                    "action_prompt": "先确认当前职责压力能否转成资质、平台或可交付成果。",
                }
            }
        },
        feedback_weight_update={"active_signal_count": 1, "summary": {"positive_claim_ids": ["claim.career"]}},
    )

    assert synthesis["brain_judge"]["version"] == BRAIN_JUDGE_VERSION
    assert synthesis["brain_judge"]["accepted"] is True
    assert synthesis["quality_contract"]["brain_judge_accepted"] is True
    assert synthesis["quality_contract"]["brain_judge_quality_score"] >= 0.58
    assert synthesis["synthesis_blueprint"]["version"] == "v30.final_synthesis_blueprint.v1"
    assert synthesis["synthesis_blueprint"]["decision_focus"] == "职责压力能否转成资质、平台和可交付成果"
    assert "官杀 -> 印星" in synthesis["synthesis_blueprint"]["evidence_handles"]
    assert synthesis["synthesis_blueprint"]["action_steps"]
    assert synthesis["synthesis_blueprint"]["risk_boundary"]
    assert "核心依据是官杀 -> 印星" in synthesis["conclusion"]
    assert "避免" in synthesis["advice"]
    assert "central_brain_judge_quality" in synthesis["training_signal"]["targets"]
    assert "synthesis_blueprint_quality" in synthesis["training_signal"]["targets"]


def test_llm_derivation_judge_rejects_missing_evidence_and_filler() -> None:
    rejected = judge_llm_derivation_quality(
        derived_conclusion="综合来看，当前阶段需要进一步分析。",
        derived_advice="建议您后续可以参考。",
        public_thinking_lines=["当前阶段初步判断。"],
        used_evidence=[],
    )
    accepted = judge_llm_derivation_quality(
        derived_conclusion="结论：事业压力已经落到职责和平台规则，需要先看印星承接。",
        derived_advice="建议：先把岗位责任拆成证书、流程和可交付成果。",
        public_thinking_lines=["官杀压力需要印星承接。", "路径证据指向职责转资质。"],
        used_evidence=["path.guan_to_yin", "claim.career"],
    )

    assert rejected["accepted"] is False
    assert "llm_derivation_missing_used_evidence" in rejected["failures"]
    assert accepted["accepted"] is True
    assert accepted["quality_score"] > rejected["quality_score"]
