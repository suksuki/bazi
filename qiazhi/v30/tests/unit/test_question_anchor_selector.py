from __future__ import annotations

from v30.core.chart_context import build_chart_context_from_displays
from v30.evidence import compile_feature_evidence
from v30.knowledge import build_knowledge_rule_portrait_signals, build_macro_dimension_signals, load_core_macro_pack
from v30.mainline import select_mainline_state
from v30.questions import select_question_anchors
from v30.questions.recommender import recommend_questions
from v30.structure import select_structure_state


def _spine(*, luck_pillar: str = ""):
    context = build_chart_context_from_displays(
        reading_id="anchor-test",
        year="甲子",
        month="戊辰",
        day="甲午",
        hour="辛酉",
        luck_pillar=luck_pillar,
    )
    evidence = compile_feature_evidence(context)
    signals = build_knowledge_rule_portrait_signals(evidence)
    structure = select_structure_state(context, evidence, signals)
    mainline = select_mainline_state(structure, evidence, signals)
    anchors = select_question_anchors(context, structure, mainline, evidence)
    return context, evidence, structure, mainline, anchors, signals


def test_question_anchors_bind_to_current_spine() -> None:
    context, _evidence, structure, mainline, anchors, _signals = _spine()
    assert anchors
    for anchor in anchors:
        assert anchor.anchor_status == "bound"
        assert anchor.context_id == context.context_id
        assert anchor.primary_structure_id == structure.structure_id
        assert anchor.mainline_id == mainline.mainline_id
        assert anchor.evidence_ids
        assert anchor.day_master == context.day_master


def test_missing_time_anchor_is_boundary_not_prediction() -> None:
    _context, _evidence, _structure, _mainline, anchors, _signals = _spine()
    time_anchor = next(row for row in anchors if row.question_id == "q_v30_time_context_boundary")
    assert time_anchor.missing_requirements == ["explicit_luck_or_flow_pillar"]
    assert "timing claims are blocked" in time_anchor.why_this_question
    assert time_anchor.time_binding["status"] == "not_provided"


def test_explicit_time_context_removes_missing_time_anchor() -> None:
    _context, _evidence, _structure, _mainline, anchors, _signals = _spine(luck_pillar="庚午")
    assert all(row.question_id != "q_v30_time_context_boundary" for row in anchors)
    assert all(row.time_binding["status"] == "ready" for row in anchors)


def test_useful_god_anchor_is_candidate_review_only() -> None:
    _context, _evidence, _structure, _mainline, anchors, _signals = _spine()
    useful = next(row for row in anchors if row.question_id == "q_v30_useful_god_candidate_review")
    assert useful.intent_id == "review_useful_god_candidate_paths"
    assert "candidate paths only" in useful.why_this_question
    assert "fixed favorable" in useful.why_this_question


def test_question_recommendations_are_evidence_and_policy_driven() -> None:
    _context, evidence, structure, mainline, anchors, signals = _spine()
    rows = recommend_questions(
        anchors,
        structure=structure,
        mainline=mainline,
        evidence=evidence,
        active_policy_versions={"question_policy": "question_policy.test"},
        knowledge_rule_portrait_signals=signals,
        macro_dimension_signals=[
            row.model_dump(mode="json")
            for row in build_macro_dimension_signals(evidence, load_core_macro_pack())
        ],
    )
    assert rows[0]["question_id"] == "q_v30_user_career_direction"
    assert rows[0]["stage"] == "user_question_entry"
    assert rows[0]["topic"] == "career"
    assert rows[0]["interaction_type"] == "user_question"
    time_row = next(row for row in rows if row["question_id"] == "q_v30_time_context_boundary")
    assert "missing_requirement_blocks_downstream_claims" in time_row["reasons"]
    assert "question_policy:question_policy.test" in rows[0]["reasons"]
    assert any("knowledge_signal_supports_ten_god_context" in row["reasons"] for row in rows)
    assert any("rule_signal_blocks_fixed_useful_god" in row["reasons"] for row in rows)
    assert any("rule_evidence_bound_to_question" in row["reasons"] for row in rows)
    assert any("mechanism_paths_scored" in row["reasons"] for row in rows)
    assert any(any(str(reason).startswith("macro_dimension_context:") for reason in row["reasons"]) for row in rows)


def test_question_policy_payload_can_change_recommendation_order() -> None:
    _context, evidence, structure, mainline, anchors, signals = _spine()
    rows = recommend_questions(
        anchors,
        structure=structure,
        mainline=mainline,
        evidence=evidence,
        active_policy_versions={"question_policy": "question_policy.weighted"},
        knowledge_rule_portrait_signals=signals,
        question_policy={"weights": {"topic_weights": {"hidden_factor": 1.25}}},
    )
    assert rows[0]["question_id"] == "q_v30_hidden_factor_boundary_discovery"
    assert rows[0]["topic"] == "hidden_factor"
    assert rows[0]["policy_weight"] == 1.25
    assert "question_policy_weight:1.25" in rows[0]["reasons"]


def test_question_recommendations_consume_central_brain_context() -> None:
    _context, evidence, structure, mainline, anchors, signals = _spine()
    rows = recommend_questions(
        anchors,
        structure=structure,
        mainline=mainline,
        evidence=evidence,
        active_policy_versions={"question_policy": "question_policy.brain"},
        knowledge_rule_portrait_signals=signals,
        central_brain_context={
            "unknown_context": ["time_layer_boundary", "hidden_factor_confirmation"],
            "feedback_slots": ["time_context_feedback", "hidden_factor_boundary_feedback"],
            "question_strategy": "context_first_question_strategy",
        },
    )

    assert rows[0]["question_id"] == "q_v30_time_context_boundary"
    assert "central_brain_unknown_context:time_layer_boundary" in rows[0]["reasons"]
    assert "central_brain_feedback_slot:time_context_feedback" in rows[0]["reasons"]
    assert any(
        "central_brain_unknown_context:hidden_factor_confirmation" in row["reasons"]
        for row in rows
    )
    assert any(
        "central_brain_feedback_slot:hidden_factor_boundary_feedback" in row["reasons"]
        for row in rows
    )


def test_question_recommendations_consume_practical_reading_gaps() -> None:
    _context, evidence, structure, mainline, anchors, signals = _spine()
    rows = recommend_questions(
        anchors,
        structure=structure,
        mainline=mainline,
        evidence=evidence,
        active_policy_versions={"question_policy": "question_policy.practical"},
        knowledge_rule_portrait_signals=signals,
        practical_reading_context={
            "question_gaps": [
                {
                    "domain": "wealth",
                    "gap": "clarify_wealth_priority_or_event_year",
                    "priority_score": 0.82,
                }
            ]
        },
    )
    practical = next(row for row in rows if row["question_id"] == "q_v30_practical_domain_focus")
    assert "practical_reading_gap:wealth" in practical["reasons"]
    assert practical["quality_contract"]["reading_focus"] == ["wealth"]
    assert practical["expected_information_gain"]["practical_focus_domains"] == ["wealth"]


def test_question_scoring_uses_interaction_uncertainty_and_invalid_retry() -> None:
    _context, evidence, structure, mainline, anchors, signals = _spine()
    rows = recommend_questions(
        anchors,
        structure=structure,
        mainline=mainline,
        evidence=evidence,
        active_policy_versions={"question_policy": "question_policy.uib5"},
        knowledge_rule_portrait_signals=signals,
        hidden_factor_state={"status": "dialogue_in_progress"},
        question_outcomes=[
            {
                "question_id": "q_v30_hidden_factor_boundary_discovery",
                "topic": "hidden_factor",
                "constraint_valid": False,
                "constraint_errors": [{"field": "state_tags", "error": "required_selection_missing"}],
            }
        ],
    )

    hidden = next(row for row in rows if row["question_id"] == "q_v30_hidden_factor_boundary_discovery")
    structure_dynamic = next(row for row in rows if row["topic"] == "structure_dynamic")
    useful = next(row for row in rows if row["topic"] == "useful_god")

    assert "invalid_input_retry_required" in hidden["reasons"]
    assert "next_question_retry:hidden_factor_invalid_structured_payload" in hidden["reasons"]
    assert "next_question_uncertainty:hidden_factor_needs_structured_feedback" in hidden["reasons"]
    assert "next_question_uncertainty:dynamic_structure_path_needs_review" in structure_dynamic["reasons"]
    assert "next_question_uncertainty:useful_god_candidate_needs_counterevidence" in useful["reasons"]


def test_hidden_factor_anchor_is_dialogue_discovery_not_claim() -> None:
    _context, _evidence, _structure, _mainline, anchors, _signals = _spine()
    hidden = next(row for row in anchors if row.question_id == "q_v30_hidden_factor_boundary_discovery")
    assert hidden.intent_id == "discover_hidden_factor_amplifier"
    assert hidden.missing_requirements == ["special_event_year_or_repeated_state_feedback"]
    assert "before treating hidden stems as amplifying factors" in hidden.why_this_question
