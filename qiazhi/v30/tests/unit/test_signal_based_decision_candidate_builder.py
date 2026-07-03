from __future__ import annotations

from v30.brain.decision_engine import build_decision_result
from v30.brain.reading_engine import build_central_reading_state
from v30.production.adapters import signals_from_diagnosis
from v30.production.signal_registry import build_signal_registry
from v30.runtime import create_smoke_runtime


def test_signal_registry_binds_candidates_without_changing_verdicts() -> None:
    diagnosis = {
        "claims": [
            {
                "claim_id": "claim:career:signal",
                "domain": "career",
                "claim_level": "domain",
                "claim_text": "事业压力需要先转成资质、平台和可交付成果。",
                "confidence_band": "high",
                "evidence_ids": ["ev:career"],
                "path_ids": ["path:career"],
                "blocked_overclaim": [],
            }
        ],
        "paths": [
            {
                "path_id": "path:career",
                "family_chain": ["authority", "resource"],
                "mechanism": "官印相生",
                "domain_targets": ["career"],
                "diagnosis_statement": "压力通过印星承接成资质和平台。",
                "score": 0.82,
                "evidence_ids": ["ev:career"],
            }
        ],
        "portraits": [],
        "features": [],
        "matched_rules": [],
    }
    claim_scores = [
        {
            "claim_id": "claim:career:signal",
            "domain": "career",
            "claim_level": "domain",
            "score": 0.84,
            "requires_question": False,
            "components": {"path_coherence": 0.72, "counter_evidence": 0.0, "missing_context_penalty": 0.0},
        }
    ]
    registry = build_signal_registry(
        reading_id="pytest-dca15",
        signals=signals_from_diagnosis(diagnosis),
    )

    baseline = build_decision_result(
        reading_id="pytest-dca15",
        active_stage_id="stage:career",
        diagnosis=diagnosis,
        claim_scores=claim_scores,
    )
    signal_bound = build_decision_result(
        reading_id="pytest-dca15",
        active_stage_id="stage:career",
        diagnosis=diagnosis,
        claim_scores=claim_scores,
        signal_registry=registry.model_dump(mode="json"),
    )

    assert [(row["domain"], row["assertion_level"], row["headline"]) for row in signal_bound["verdicts"]] == [
        (row["domain"], row["assertion_level"], row["headline"]) for row in baseline["verdicts"]
    ]
    candidate = signal_bound["decision_input_bundle"]["candidates"][0]
    assert candidate["confidence"] == baseline["decision_input_bundle"]["candidates"][0]["confidence"]
    assert candidate["source_signal_ids"]
    assert candidate["candidate_builder"]["mode"] == "compatibility"
    assert candidate["candidate_builder"]["score_mutation_allowed"] is False
    assert candidate["candidate_builder"]["score_mutated"] is False
    assert candidate["signal_source_summary"]["source_type_counts"]["diagnosis_claim"] == 1
    assert signal_bound["candidate_builder_summary"]["claims_with_direct_signal_count"] == 1
    assert signal_bound["candidate_builder_summary"]["score_mutation_allowed"] is False
    assert signal_bound["verdicts"][0]["trace"]["source_signal_ids"]
    assert signal_bound["verdicts"][0]["trace"]["candidate_builder"]["score_mutated"] is False


def test_central_reading_state_exposes_signal_candidate_builder_projection() -> None:
    state = build_central_reading_state(
        reading_id="pytest-dca15-central",
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
            "paths": [{"path_id": "path:wealth", "score": 0.62, "evidence_ids": ["ev:wealth"], "domain_targets": ["wealth"]}],
            "portraits": [],
            "features": [],
            "matched_rules": [],
            "graph": {},
            "summaries": {},
        },
        recommendations=[],
        question_dialogue_graph={},
        interaction_state={},
        ranked_decisions={
            "useful_god": {
                "decision_id": "decision:useful",
                "domain": "useful_god",
                "primary_candidate": "候选取用待复核",
                "confidence": 0.62,
                "supporting_evidence": ["ev:wealth"],
                "weakening_evidence": [],
                "boundary": "ranked_decision_ranked_candidate_not_final_verdict",
            }
        },
    )

    assert "signal_registry" in state["candidate_sources"]
    assert state["decision_signal_registry"]["signal_count"] >= 2
    assert state["decision_signal_registry"]["score_mutation_allowed"] is False
    assert state["candidate_builder_summary"]["mode"] == "compatibility"
    assert state["candidate_builder_summary"]["claims_with_direct_signal_count"] == 1
    candidate = state["decision_input_bundle"]["candidates"][0]
    assert candidate["source_signal_ids"]
    assert candidate["candidate_builder"]["confidence_source"] == "claim_scores"
    assert candidate["candidate_builder"]["score_mutation_allowed"] is False
    assert state["decision_result"]["llm_expression_contract"]["llm_can_override_verdict"] is False


def test_runtime_keeps_smoke_verdict_count_while_binding_candidate_signals() -> None:
    runtime = create_smoke_runtime("pytest-dca15-runtime")
    central = runtime.question_plan.policy_effect["central_reading_state"]

    assert len(central["decision_verdicts"]) == 9
    assert central["candidate_builder_summary"]["mode"] == "compatibility"
    assert central["candidate_builder_summary"]["claims_with_direct_signal_count"] > 0
    assert central["decision_input_bundle"]["candidates"][0]["source_signal_ids"]
    assert central["decision_input_bundle"]["candidates"][0]["candidate_builder"]["score_mutated"] is False
