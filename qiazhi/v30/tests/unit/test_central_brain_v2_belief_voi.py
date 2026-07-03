from __future__ import annotations

from copy import deepcopy

from v30.brain.reading_engine import build_central_reading_state


def test_cbi_v2_belief_state_updates_claim_posterior_from_user_feedback() -> None:
    confirmed = build_central_reading_state(
        reading_id="pytest-cbi-v2-belief-confirm",
        role_key="user",
        diagnosis=_diagnosis("pytest-cbi-v2-belief-confirm"),
        recommendations=[],
        question_dialogue_graph={},
        interaction_state={},
        question_outcomes=[
            {
                "event_id": "evt.confirm.career",
                "question_id": "q.career",
                "topic": "career",
                "selected_option": "career:pressure",
                "confidence": 0.9,
                "outcome_status": "answered",
            }
        ],
    )
    denied = build_central_reading_state(
        reading_id="pytest-cbi-v2-belief-deny",
        role_key="user",
        diagnosis=_diagnosis("pytest-cbi-v2-belief-deny"),
        recommendations=[],
        question_dialogue_graph={},
        interaction_state={},
        question_outcomes=[
            {
                "event_id": "evt.deny.career",
                "question_id": "q.career",
                "topic": "career",
                "selected_option": "career:pressure",
                "confidence": 0.9,
                "outcome_status": "denied",
            }
        ],
    )

    confirmed_delta = _belief_delta(confirmed, "claim:career")
    denied_delta = _belief_delta(denied, "claim:career")

    assert confirmed_delta > 0
    assert denied_delta < confirmed_delta
    assert denied_delta < 0
    assert confirmed["belief_state"]["boundary"] == "belief_state_updates_claim_confidence_not_chart_facts"


def test_central_feedback_overlay_applies_practitioner_selection_to_claim_score() -> None:
    baseline = build_central_reading_state(
        reading_id="pytest-central-feedback-baseline",
        role_key="practitioner",
        diagnosis=_diagnosis("pytest-central-feedback-baseline"),
        recommendations=[],
        question_dialogue_graph={},
        interaction_state={},
    )
    selected = build_central_reading_state(
        reading_id="pytest-central-feedback-selected",
        role_key="practitioner",
        diagnosis=_diagnosis("pytest-central-feedback-selected"),
        recommendations=[],
        question_dialogue_graph={},
        interaction_state={},
        practitioner_selections=[
            {
                "selection_id": "sel.career.rank",
                "option_set_id": "opt.career",
                "action": "rank",
                "selected_option_ids": ["career"],
                "confidence": 0.9,
                "option_set": {"topic": "career", "source_id": "stage.career"},
                "effect": {
                    "topic": "career",
                    "source_id": "stage.career",
                    "belief_delta": {"delta": 0.20, "confidence": 0.9, "direction": "raise"},
                },
            }
        ],
    )

    base_claim = baseline["claim_scores"][0]
    selected_claim = selected["claim_scores"][0]

    assert selected["central_feedback_overlay"]["practitioner_selection_count"] == 1
    assert selected["central_feedback_overlay"]["domain_deltas"]["career"] > 0
    assert selected_claim["score"] > base_claim["score"]
    assert selected_claim["components"]["central_feedback_overlay"] > 0
    assert selected["final_synthesis"]["feedback_overlay_summary"]["practitioner_selection_count"] == 1
    assert selected["central_feedback_overlay"]["chart_fact_mutation_allowed"] is False


def test_cbi_v2_value_of_information_selects_single_high_value_question() -> None:
    state = build_central_reading_state(
        reading_id="pytest-cbi-v2-voi",
        role_key="user",
        diagnosis=_diagnosis("pytest-cbi-v2-voi"),
        recommendations=[
            {
                "question_id": "q.career.pressure_boundary",
                "question": "事业压力更像岗位责任，还是转化成资质平台？",
                "topic": "career",
                "stage": "candidate_review",
                "score": 0.86,
                "answer_mode": "single_choice",
                "answer_constraints": {"options": ["岗位责任", "资质平台"]},
                "expected_information_gain": {"score": 0.86},
                "candidate_source": "central_brain_v2_test",
            }
        ],
        question_dialogue_graph={"next_question_id": "q.career.pressure_boundary"},
        interaction_state={},
    )

    policy = state["value_of_information_policy"]
    trace = state["brain_decision_trace"]

    assert policy["selected_action"] == "ask_stage_question"
    assert policy["question_id"] == "q.career.pressure_boundary"
    assert policy["question_value"] > policy["user_cost"]
    assert trace["selected_action"] == "ask_stage_question"
    assert trace["selected_question_id"] == "q.career.pressure_boundary"
    assert len(trace["question_candidates"]) == 1
    assert trace["question_candidates"][0]["target_claim_ids"] == ["claim:career"]
    assert "value_of_information_policy" in trace["training_targets"]


def test_cbi_v2_training_example_captures_decision_without_fact_targets() -> None:
    state = build_central_reading_state(
        reading_id="pytest-cbi-v2-training-example",
        role_key="user",
        diagnosis=_diagnosis("pytest-cbi-v2-training-example"),
        recommendations=[
            {
                "question_id": "q.career.pressure_boundary",
                "question": "事业压力更像岗位责任，还是转化成资质平台？",
                "topic": "career",
                "stage": "candidate_review",
                "score": 0.86,
                "answer_mode": "single_choice",
                "expected_information_gain": {"score": 0.86},
                "candidate_source": "central_brain_v2_test",
            }
        ],
        question_dialogue_graph={"next_question_id": "q.career.pressure_boundary"},
        interaction_state={},
        question_outcomes=[
            {
                "event_id": "evt.confirm.career",
                "question_id": "q.career",
                "topic": "career",
                "selected_option": "career:pressure",
                "confidence": 0.9,
                "outcome_status": "answered",
            }
        ],
    )
    example = state["brain_training_example"]

    assert example["version"] == "v30.brain_training_example.v1"
    assert example["decision"]["decision_id"] == state["brain_decision_trace"]["decision_id"]
    assert example["input"]["version"] == "v30.brain_training.input_snapshot.v1"
    assert example["structured_labels"]["version"] == "v30.brain_training.labels.v1"
    assert example["safety"]["chart_fact_mutation_allowed"] is False
    assert example["candidate_claim_ids"] == ["claim:career"]
    assert example["candidate_question_ids"] == ["q.career.pressure_boundary"]
    assert example["outcome"]["user_answered"] is True
    assert example["outcome"]["claim_delta"]["claim:career"] > 0
    assert "chart_facts" in example["blocked_targets"]
    assert "pillar_calculation" in example["blocked_targets"]
    assert "value_of_information_policy" in example["trainable_targets"]
    assert example["production_policy_write_allowed"] is False


def _diagnosis(reading_id: str) -> dict[str, object]:
    diagnosis = {
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
        "paths": [
            {
                "path_id": "path:career",
                "score": 0.7,
                "timing_trigger": {},
            }
        ],
        "portraits": [],
        "graph": {
            "graph_id": f"{reading_id}:graph",
            "reading_id": reading_id,
            "nodes": [
                {
                    "node_id": "node:feature:career",
                    "node_kind": "feature",
                    "ref_id": "feature:career",
                    "domain": "career",
                    "weight": 0.82,
                    "metadata": {},
                },
                {
                    "node_id": "node:claim:career",
                    "node_kind": "claim",
                    "ref_id": "claim:career",
                    "domain": "career",
                    "weight": 0.68,
                    "metadata": {},
                },
            ],
            "edges": [
                {
                    "edge_id": "edge:supports:feature->claim",
                    "source_node_id": "node:feature:career",
                    "target_node_id": "node:claim:career",
                    "edge_kind": "supports",
                    "weight": 0.82,
                    "evidence_ids": ["ev:career"],
                },
                {
                    "edge_id": "edge:asks:claim->claim",
                    "source_node_id": "node:claim:career",
                    "target_node_id": "node:claim:career",
                    "edge_kind": "asks_followup",
                    "weight": 0.72,
                    "evidence_ids": ["ev:career"],
                },
            ],
            "top_claim_ids": ["claim:career"],
            "top_path_ids": ["path:career"],
        },
        "summaries": {},
        "public_projection": {},
    }
    return deepcopy(diagnosis)


def _belief_delta(state: dict[str, object], claim_id: str) -> float:
    belief = state["belief_state"]
    assert isinstance(belief, dict)
    for key in ("top_claims", "weak_claims", "blocked_claims"):
        rows = belief.get(key, [])
        assert isinstance(rows, list)
        for row in rows:
            if isinstance(row, dict) and row.get("claim_id") == claim_id:
                return float(row.get("posterior_delta") or 0.0)
    raise AssertionError(f"missing belief claim: {claim_id}")
