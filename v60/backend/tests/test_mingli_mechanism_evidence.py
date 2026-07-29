from __future__ import annotations

from datetime import date, time

from abu_v60.decision import DecisionKind
from abu_v60.knowledge import KnowledgeAuthority
from abu_v60.mingli import (
    MingliMechanismComparisonService,
    MingliMechanismEvidenceCompiler,
    MingliQuantFoundationCompiler,
)
from abu_v60.mingli.calendar import BirthInput, ChartPillars
from abu_v60.mingli.compiler import compile_case


def _compile(
    *,
    case_ref: str = "case-liu-jin-mechanism-test",
    chart: ChartPillars | None = None,
):
    chart = chart or ChartPillars(
        year="丁巳",
        month="乙巳",
        day="乙丑",
        hour="乙酉",
    )
    compiled = compile_case(
        case_ref=case_ref,
        birth_input=BirthInput(
            calendar_type="solar",
            birth_date=date(1977, 5, 8),
            birth_time=time(17, 30),
            timezone="Asia/Shanghai",
        ),
        chart=chart,
    )
    quant = MingliQuantFoundationCompiler().compile(
        case_ref=case_ref,
        chart_version_ref=compiled.chart_version_ref,
        pillars=compiled.pillars,
        facts=compiled.facts,
    )
    mechanism = MingliMechanismEvidenceCompiler().compile(
        quant_vector=quant,
        facts=compiled.facts,
    )
    return compiled, quant, mechanism


def test_real_chart_compiles_selective_candidates_not_every_known_pattern() -> None:
    _, _, vector = _compile()

    assert vector.comparison_status == "MULTIPLE_CANDIDATES"
    assert {item.pattern_label for item in vector.candidates} == {
        "食伤生财结构候选",
        "食伤制官杀结构候选",
    }
    assert all(item.professional_selection_qualified is False for item in vector.candidates)
    assert all(item.effect_status == "UNRESOLVED" for item in vector.candidates)
    assert all(
        item.support_score_status == "NOT_COMPUTED_NO_ADMITTED_WEIGHTS"
        for item in vector.candidates
    )
    assert all("CAPACITY_MODEL_NOT_ADMITTED" in item.blocker_codes for item in vector.candidates)
    assert all(item.counter_evidence_refs == () for item in vector.candidates)


def test_mechanism_vector_is_deterministic_and_chart_specific() -> None:
    compiled, quant, first = _compile()
    replay = MingliMechanismEvidenceCompiler().compile(
        quant_vector=quant,
        facts=tuple(reversed(compiled.facts)),
    )
    _, _, different = _compile(
        case_ref="case-different-mechanism-test",
        chart=ChartPillars(
            year="甲子",
            month="乙丑",
            day="丙寅",
            hour="丁午",
        ),
    )

    assert replay == first
    assert replay.vector_hash == first.vector_hash
    assert different.vector_ref != first.vector_ref
    assert {item.pattern_ref for item in different.candidates} != {
        item.pattern_ref for item in first.candidates
    }


def test_mechanism_profile_is_hash_locked_and_forbids_effective_work() -> None:
    profile = KnowledgeAuthority().active_mechanism_evidence_profile()

    assert profile.profile_hash
    assert profile.professionally_reviewed is False
    assert profile.runtime_scope == "MECHANISM_CANDIDATE_EVIDENCE_ONLY"
    assert "effective_work" in profile.forbidden_conclusions
    assert "empirical_probability" in profile.forbidden_conclusions
    assert profile.candidate_presence_rule == "ALL_ROLES_PRESENT_AND_SOURCE_OR_BRIDGE_VISIBLE"


def test_reasoner_input_is_bounded_to_vector_candidates_and_derived_evidence() -> None:
    _, _, vector = _compile()
    request, context = MingliMechanismComparisonService._request_and_context(vector)

    assert request.decision_kind is DecisionKind.INTERPRETATION
    assert request.subject_ref == vector.vector_ref
    assert request.llm_allowed is True
    assert context is not None
    assert {item.candidate_ref for item in context.candidates} == {
        item.candidate_ref for item in vector.candidates
    }
    assert {item.evidence_ref for item in context.evidence} == set(request.evidence_refs)
    assert all("不能裁定有效做功" in item.statement for item in context.candidates)
    assert all(item.visible_at_decision is True for item in context.evidence)
