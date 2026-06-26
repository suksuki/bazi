from __future__ import annotations

from v30.hidden_factor import build_hidden_factor_probes
from v30.runtime import create_smoke_runtime


def test_hidden_factor_probe_requires_dialogue_feedback() -> None:
    runtime = create_smoke_runtime("hidden-factor-runtime")
    probes = runtime.question_plan.hidden_factor_probes
    assert probes
    assert probes[0]["status"] == "needs_dialogue"
    assert probes[0]["boundary"] == "hypothesis_only_not_deterministic_chart_conclusion"
    assert "special_event_year" in probes[0]["required_feedback"]


def test_hidden_factor_question_is_recommended_without_final_claim() -> None:
    runtime = create_smoke_runtime("hidden-factor-question")
    hidden_anchor = next(
        anchor for anchor in runtime.question_anchors
        if anchor.question_id == "q_v30_hidden_factor_boundary_discovery"
    )
    recommendation = next(
        row for row in runtime.question_plan.recommended_questions
        if row["question_id"] == hidden_anchor.question_id
    )
    assert hidden_anchor.intent_id == "discover_hidden_factor_amplifier"
    assert hidden_anchor.missing_requirements == ["special_event_year_or_repeated_state_feedback"]
    assert recommendation["topic"] == "hidden_factor"
    assert recommendation["stage"] == "dialogue_discovery"
    assert "hidden_factor_requires_dialogue_discovery" in recommendation["reasons"]
    assert "before treating hidden stems as amplifying factors" in hidden_anchor.why_this_question


def test_hidden_factor_probe_builder_returns_empty_without_hidden_evidence() -> None:
    runtime = create_smoke_runtime("hidden-factor-empty")
    visible_evidence = [row for row in runtime.feature_evidence if row.kind != "hidden_stem"]
    assert build_hidden_factor_probes(runtime.chart_context, visible_evidence) == []
