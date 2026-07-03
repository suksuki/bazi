from __future__ import annotations

import pytest
from pydantic import ValidationError

from v30.brain import (
    BrainBeliefState,
    BrainClaimBelief,
    BrainDecisionOutcome,
    BrainDecisionTrace,
    BrainEvidenceGraphSnapshot,
    BrainLLMCandidateDerivation,
    BrainQuestionCandidate,
    BrainTrainingExample,
    BrainUncertaintySlot,
)


def test_cbi_v2_decision_trace_allows_explainable_stage_question() -> None:
    graph = _graph("cbi-v2-reading")
    belief = _belief(graph)
    question = BrainQuestionCandidate(
        question_id="q.career.pressure_boundary",
        prompt="事业压力更像岗位责任，还是转化成证书和平台？",
        domain="career",
        target_claim_ids=["career.pressure_to_credentials"],
        target_uncertainty_ids=["u.career.pressure_boundary"],
        option_labels=["岗位责任", "证书平台"],
        information_gain=0.72,
        user_cost=0.18,
    )
    llm = BrainLLMCandidateDerivation(
        provider="ollama",
        model="gemma4",
        stage_id="path_reasoning",
        accepted=True,
        public_thinking_lines=["官杀压力需要看是否由印星承接。"],
        derived_conclusion="事业压力适合转为资质、规则或平台能力。",
        derived_advice="先把责任边界和可交付成果定清楚。",
        used_evidence_ids=["node.path.guan_to_yin"],
    )

    trace = BrainDecisionTrace(
        decision_id="decision.cbi-v2.1",
        reading_id="cbi-v2-reading",
        stage_id="path_reasoning",
        selected_action="ask_stage_question",
        selected_claim_ids=["career.pressure_to_credentials"],
        selected_question_id="q.career.pressure_boundary",
        reason_codes=["high_information_gain", "claim_confidence_near_threshold"],
        feature_vector={"information_gain": 0.72, "user_cost": 0.18},
        belief_state=belief,
        question_candidates=[question],
        llm_candidate=llm,
        training_targets=["question_selection_policy", "claim_score_weights"],
    )

    assert trace.selected_question_id == "q.career.pressure_boundary"
    assert trace.llm_candidate is not None
    assert trace.llm_candidate.accepted is True
    assert trace.boundary == "brain_decision_trace_explains_action_without_mutating_facts_or_policies"


def test_cbi_v2_decision_trace_rejects_unexplained_or_missing_question_action() -> None:
    belief = _belief(_graph("cbi-v2-reading"))

    with pytest.raises(ValidationError, match="Question actions require selected_question_id"):
        BrainDecisionTrace(
            decision_id="decision.cbi-v2.missing-question",
            reading_id="cbi-v2-reading",
            selected_action="ask_stage_question",
            reason_codes=["high_information_gain"],
            belief_state=belief,
        )

    with pytest.raises(ValidationError, match="BrainDecisionTrace requires reason codes"):
        BrainDecisionTrace(
            decision_id="decision.cbi-v2.no-reason",
            reading_id="cbi-v2-reading",
            selected_action="conclude_stage",
            selected_claim_ids=["career.pressure_to_credentials"],
            belief_state=belief,
        )


def test_cbi_v2_llm_candidate_cannot_create_facts_or_use_unknown_evidence() -> None:
    belief = _belief(_graph("cbi-v2-reading"))

    with pytest.raises(ValidationError, match="cannot generate facts"):
        BrainLLMCandidateDerivation(
            accepted=False,
            llm_generated_facts=True,
        )

    question = BrainQuestionCandidate(
        question_id="q.career.pressure_boundary",
        prompt="事业压力更像岗位责任，还是转化成证书和平台？",
        target_claim_ids=["career.pressure_to_credentials"],
        information_gain=0.62,
    )
    llm = BrainLLMCandidateDerivation(
        accepted=True,
        used_evidence_ids=["node.not.in.belief"],
    )

    with pytest.raises(ValidationError, match="Accepted LLM evidence must be present"):
        BrainDecisionTrace(
            decision_id="decision.cbi-v2.unknown-evidence",
            reading_id="cbi-v2-reading",
            selected_action="ask_stage_question",
            selected_claim_ids=["career.pressure_to_credentials"],
            selected_question_id="q.career.pressure_boundary",
            reason_codes=["high_information_gain"],
            belief_state=belief,
            question_candidates=[question],
            llm_candidate=llm,
        )


def test_cbi_v2_training_example_blocks_fact_training_and_policy_write() -> None:
    graph = _graph("cbi-v2-reading")
    belief = _belief(graph)
    trace = BrainDecisionTrace(
        decision_id="decision.cbi-v2.conclude",
        reading_id="cbi-v2-reading",
        selected_action="conclude_stage",
        selected_claim_ids=["career.pressure_to_credentials"],
        reason_codes=["evidence_sufficient"],
        belief_state=belief,
    )

    example = BrainTrainingExample(
        example_id="example.cbi-v2.1",
        reading_id="cbi-v2-reading",
        source_decision_id="decision.cbi-v2.conclude",
        input_stage_id="path_reasoning",
        evidence_graph_snapshot=graph,
        candidate_claim_ids=["career.pressure_to_credentials"],
        decision=trace,
        outcome=BrainDecisionOutcome(status="confirmed", user_answered=True),
        trainable_targets=["claim_score_weights", "final_synthesis_ranking"],
    )

    assert "chart_facts" in example.blocked_targets
    assert example.production_policy_write_allowed is False

    with pytest.raises(ValidationError, match="cannot train deterministic fact targets"):
        BrainTrainingExample(
            example_id="example.cbi-v2.bad-target",
            reading_id="cbi-v2-reading",
            source_decision_id="decision.cbi-v2.conclude",
            evidence_graph_snapshot=graph,
            decision=trace,
            trainable_targets=["chart_facts"],
        )

    with pytest.raises(ValidationError, match="cannot write production policy"):
        BrainTrainingExample(
            example_id="example.cbi-v2.policy-write",
            reading_id="cbi-v2-reading",
            source_decision_id="decision.cbi-v2.conclude",
            evidence_graph_snapshot=graph,
            decision=trace,
            production_policy_write_allowed=True,
        )


def _graph(reading_id: str) -> BrainEvidenceGraphSnapshot:
    return BrainEvidenceGraphSnapshot(
        graph_id=f"{reading_id}:graph",
        reading_id=reading_id,
        node_count=3,
        edge_count=2,
        node_kinds=["chart_fact", "path", "claim"],
        edge_kinds=["supports"],
        top_claim_ids=["career.pressure_to_credentials"],
        top_path_ids=["path.guan_to_yin"],
    )


def _belief(graph: BrainEvidenceGraphSnapshot) -> BrainBeliefState:
    claim = BrainClaimBelief(
        claim_id="career.pressure_to_credentials",
        domain="career",
        status="selected",
        confidence=0.74,
        actionability=0.82,
        uncertainty=0.31,
        supporting_node_ids=["node.path.guan_to_yin"],
        missing_context=["career_pressure_boundary"],
        requires_question=True,
    )
    uncertainty = BrainUncertaintySlot(
        uncertainty_id="u.career.pressure_boundary",
        domain="career",
        target_claim_ids=["career.pressure_to_credentials"],
        missing_context=["career_pressure_boundary"],
        information_gain=0.72,
        user_cost=0.18,
    )
    return BrainBeliefState(
        reading_id=graph.reading_id,
        active_stage_id="path_reasoning",
        user_goal="career",
        evidence_graph=graph,
        top_claims=[claim],
        uncertainty_map=[uncertainty],
        known_context=["chart_bound"],
        missing_context=["career_pressure_boundary"],
        final_decision_readiness=0.64,
    )
