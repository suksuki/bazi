from __future__ import annotations

from v30.brain.decision_engine import DECISION_ENGINE_VERSION, build_decision_result
from v30.brain.final_synthesis import build_final_synthesis
from v30.brain.reading_engine import build_central_reading_state


def test_decision_engine_preserves_branches_and_blocks_llm_fact_authority() -> None:
    result = build_decision_result(
        reading_id="pytest-dca-branch",
        active_stage_id="stage:career",
        diagnosis={
            "claims": [
                {
                    "claim_id": "claim:career:stable",
                    "domain": "career",
                    "claim_level": "domain",
                    "claim_text": "事业主线更适合先稳住职责和资质承接。",
                    "evidence_ids": ["ev:career:role"],
                    "path_ids": ["path:guan-yin"],
                },
                {
                    "claim_id": "claim:career:breakthrough",
                    "domain": "career",
                    "claim_level": "domain",
                    "claim_text": "事业也存在转型突破分支，需要看输出是否能承接压力。",
                    "evidence_ids": ["ev:career:output"],
                    "path_ids": ["path:shi-shang"],
                },
            ]
        },
        claim_scores=[
            {
                "claim_id": "claim:career:stable",
                "domain": "career",
                "claim_level": "domain",
                "score": 0.72,
                "requires_question": False,
                "components": {"path_coherence": 0.56, "counter_evidence": 0.0, "missing_context_penalty": 0.0},
            },
            {
                "claim_id": "claim:career:breakthrough",
                "domain": "career",
                "claim_level": "domain",
                "score": 0.66,
                "requires_question": False,
                "components": {"path_coherence": 0.52, "counter_evidence": 0.0, "missing_context_penalty": 0.0},
            },
        ],
        central_feedback_overlay={"practitioner_selection_count": 0},
    )

    assert result["engine_version"] == DECISION_ENGINE_VERSION
    assert result["decision_input_bundle"]["llm_text_as_fact_allowed"] is False
    assert result["llm_expression_contract"]["llm_can_override_verdict"] is False
    assert result["llm_expression_contract"]["must_stay_within_allowed_assertions"] is True
    assert result["verdicts"][0]["assertion_level"] == "mixed"
    assert result["verdicts"][0]["alternative_branch_ids"]
    assert result["verdicts"][0]["allowed_assertions"]
    assert "不能把候选分支说成已经完全定死。" in result["verdicts"][0]["forbidden_assertions"]
    assert result["chart_fact_mutation_allowed"] is False


def test_final_synthesis_consumes_verdicts_before_llm_expression() -> None:
    decision_result = build_decision_result(
        reading_id="pytest-dca-final",
        active_stage_id="stage:career",
        diagnosis={
            "claims": [
                {
                    "claim_id": "claim:career",
                    "domain": "career",
                    "claim_level": "domain",
                    "claim_text": "事业压力需要先转成资质、平台和可交付成果。",
                    "evidence_ids": ["ev:career"],
                    "path_ids": ["path:guan-yin"],
                }
            ]
        },
        claim_scores=[
            {
                "claim_id": "claim:career",
                "domain": "career",
                "claim_level": "domain",
                "score": 0.84,
                "requires_question": False,
                "components": {"path_coherence": 0.72, "counter_evidence": 0.0, "missing_context_penalty": 0.0},
            }
        ],
    )
    synthesis = build_final_synthesis(
        diagnosis={
            "claims": [
                {
                    "claim_id": "claim:career",
                    "domain": "career",
                    "claim_level": "domain",
                    "claim_text": "这段原始 claim 不应该绕过 Verdict 成为最终断语。",
                    "evidence_ids": ["ev:career"],
                }
            ],
            "paths": [],
            "portraits": [],
        },
        claim_scores=[],
        practical_reading_context={},
        feedback_weight_update={},
        decision_result=decision_result,
    )

    assert synthesis["quality_contract"]["uses_decision_verdicts"] is True
    assert synthesis["decision_engine"]["uses_decision_verdicts"] is True
    assert synthesis["decision_verdicts"][0]["assertion_level"] == "confirmed"
    assert "事业压力需要先转成资质、平台和可交付成果" in synthesis["conclusion"]
    assert "这段原始 claim" not in synthesis["conclusion"]
    assert synthesis["decision_engine"]["llm_expression_only"] is True
    assert synthesis["quality_contract"]["llm_can_rewrite_expression_only"] is True


def test_central_reading_state_exposes_decision_verdicts_and_keeps_dialogue_separate() -> None:
    state = build_central_reading_state(
        reading_id="pytest-dca-central",
        role_key="user",
        diagnosis={
            "status": "ready",
            "claims": [
                {
                    "claim_id": "claim:career",
                    "claim_level": "domain",
                    "domain": "career",
                    "claim_text": "事业压力需要转为资质和平台能力。",
                    "confidence_band": "high",
                    "evidence_ids": ["ev:career"],
                    "path_ids": ["path:career"],
                    "needs_user_calibration": False,
                    "blocked_overclaim": [],
                }
            ],
            "paths": [{"path_id": "path:career", "score": 0.78, "timing_trigger": {}}],
            "portraits": [],
            "graph": {},
            "summaries": {},
        },
        recommendations=[],
        question_dialogue_graph={},
        interaction_state={},
    )

    assert state["decision_engine_version"] == DECISION_ENGINE_VERSION
    assert state["decision_input_bundle"]["version"] == "v30.decision_input_bundle.v1"
    assert state["decision_verdicts"]
    assert state["final_synthesis"]["quality_contract"]["uses_decision_verdicts"] is True
    assert state["final_synthesis"]["decision_engine"]["uses_decision_verdicts"] is True
    assert state["dialogue_plan"]["customer_decision_field"] == "reading_surface.conversation_surface"
    assert state["dialogue_plan"]["legacy_customer_decision_field"] == "reading_surface.current_dialogue_turn"
    assert state["decision_result"]["llm_expression_contract"]["llm_can_create_chart_facts"] is False


def test_decision_next_question_slots_feed_dialogue_without_becoming_steps() -> None:
    state = build_central_reading_state(
        reading_id="pytest-dca-dialogue-slot",
        role_key="user",
        diagnosis={
            "status": "ready",
            "claims": [
                {
                    "claim_id": "claim:wealth",
                    "claim_level": "domain",
                    "domain": "wealth",
                    "claim_text": "财务判断需要先确认主动争取、合作分配和保守积累的权重。",
                    "confidence_band": "medium",
                    "evidence_ids": ["ev:wealth"],
                    "path_ids": ["path:wealth"],
                    "needs_user_calibration": True,
                    "blocked_overclaim": [],
                }
            ],
            "paths": [{"path_id": "path:wealth", "score": 0.62, "timing_trigger": {}}],
            "portraits": [],
            "graph": {},
            "summaries": {},
        },
        recommendations=[],
        question_dialogue_graph={},
        interaction_state={},
    )

    assert state["decision_question_recommendations"]
    assert state["decision_question_recommendations"][0]["candidate_source"] == "decision_engine_next_question_slot"
    assert state["dialogue_plan"]["current_question"]["candidate_source"] == "decision_engine_next_question_slot"
    assert state["dialogue_plan"]["current_question_id"].startswith("decision-slot:")
    assert state["dialogue_plan"]["customer_decision_field"] == "reading_surface.conversation_surface"
    assert state["dialogue_plan"]["legacy_customer_decision_field"] == "reading_surface.current_dialogue_turn"
    assert state["dialogue_plan"]["stage_question_opportunities"][0]["display_mode"] == "inline_stage_question"
    assert state["decision_question_recommendations"][0]["boundary"] == "decision_question_recommendation_comes_from_verdict_slot_not_ghost_dialogue"


def test_decision_feedback_recalculation_summary_tracks_practitioner_selection() -> None:
    state = build_central_reading_state(
        reading_id="pytest-dca-feedback-recalc",
        role_key="practitioner",
        diagnosis={
            "status": "ready",
            "claims": [
                {
                    "claim_id": "claim:career",
                    "claim_level": "domain",
                    "domain": "career",
                    "claim_text": "事业压力需要转为资质和平台能力。",
                    "confidence_band": "medium",
                    "evidence_ids": ["ev:career"],
                    "path_ids": ["path:career"],
                    "needs_user_calibration": True,
                    "blocked_overclaim": [],
                }
            ],
            "paths": [{"path_id": "path:career", "score": 0.7, "timing_trigger": {}}],
            "portraits": [],
            "graph": {},
            "summaries": {},
        },
        recommendations=[],
        question_dialogue_graph={},
        interaction_state={},
        practitioner_selections=[
            {
                "selection_id": "sel.dca.career",
                "option_set_id": "opt.dca.career",
                "action": "rank",
                "selected_option_ids": ["career-main"],
                "confidence": 0.9,
                "option_set": {"topic": "career", "source_id": "claim:career"},
                "effect": {
                    "topic": "career",
                    "source_id": "claim:career",
                    "belief_delta": {"delta": 0.2, "confidence": 0.9, "direction": "raise"},
                },
            }
        ],
        active_stage_id="journey_decision_verdicts",
    )

    summary = state["decision_feedback_recalculation_summary"]

    assert summary["version"] == "v30.decision_feedback_recalculation_summary.v1"
    assert summary["feedback_applied"] is True
    assert summary["practitioner_selection_count"] == 1
    assert summary["domain_deltas"]["career"] > 0
    assert summary["affected_candidate_ids"]
    assert summary["affected_verdict_ids"]
    assert summary["admin_training_projection"]["trainable"] is True
    assert "feedback_to_decision_candidate_weight" in summary["admin_training_projection"]["targets"]
    assert summary["chart_fact_mutation_allowed"] is False
    assert "decision_feedback_recalculation_quality" in state["training_signal"]["targets"]
