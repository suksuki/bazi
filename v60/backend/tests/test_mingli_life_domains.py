from __future__ import annotations

from datetime import date, time

import pytest
from abu_v60.mingli import (
    MingliLifeDomainEvidenceCompiler,
    MingliMechanismEvidenceCompiler,
    MingliQuantFoundationCompiler,
    MingliTimingEvidenceCompiler,
)
from abu_v60.mingli.calendar import BirthInput, resolve_four_pillars
from abu_v60.mingli.compiler import compile_case

ANALYSIS_DATE = date(2026, 7, 29)


def _compile(*, case_ref: str, birth_date: date, birth_time: time):
    birth_input = BirthInput(
        calendar_type="solar",
        birth_date=birth_date,
        birth_time=birth_time,
        timezone="Asia/Shanghai",
    )
    compiled = compile_case(
        case_ref=case_ref,
        birth_input=birth_input,
        chart=resolve_four_pillars(birth_input),
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
    timing = MingliTimingEvidenceCompiler().compile(
        case_ref=case_ref,
        chart_version_ref=compiled.chart_version_ref,
        life_case_revision_ref=f"{case_ref}-life-v1",
        birth_input=birth_input,
        gender="male",
        pillars=compiled.pillars,
        facts=compiled.facts,
        analysis_date=ANALYSIS_DATE,
        mechanism_vector=mechanism,
    )
    domains = MingliLifeDomainEvidenceCompiler().compile(
        mechanism_vector=mechanism,
        timing_vector=timing,
    )
    return compiled, mechanism, timing, domains


def test_real_cases_produce_distinct_bounded_domain_windows() -> None:
    _, _, _, liu = _compile(
        case_ref="case-domain-liu",
        birth_date=date(1977, 5, 8),
        birth_time=time(17, 30),
    )
    _, _, _, yanzhou = _compile(
        case_ref="case-domain-yanzhou",
        birth_date=date(1991, 8, 14),
        birth_time=time(9, 20),
    )

    assert [
        (item.domain, item.signal_status)
        for item in liu.observations
    ] == [
        ("career", "TIMING_MECHANISM_OVERLAP"),
        ("wealth", "TIMING_MECHANISM_OVERLAP"),
        ("relationship", "TIMING_ONLY"),
    ]
    assert [
        (item.domain, item.signal_status)
        for item in yanzhou.observations
    ] == [
        ("career", "TIMING_MECHANISM_OVERLAP"),
        ("wealth", "MECHANISM_ONLY"),
        ("relationship", "TIMING_ONLY"),
    ]
    assert liu.vector_ref != yanzhou.vector_ref


def test_domain_vector_is_stable_and_never_claims_outcome_or_probability() -> None:
    _, mechanism, timing, first = _compile(
        case_ref="case-domain-stable",
        birth_date=date(1977, 5, 8),
        birth_time=time(17, 30),
    )
    replay = MingliLifeDomainEvidenceCompiler().compile(
        mechanism_vector=mechanism,
        timing_vector=timing,
    )

    assert replay == first
    assert replay.evidence_semantics == "ATTENTION_WINDOW_ONLY"
    assert replay.outcome_status == "UNRESOLVED"
    assert replay.probability_status == "NOT_COMPUTED"
    assert replay.professional_verdict_allowed is False
    assert replay.canonical_write_allowed is False
    assert all(
        observation.outcome_status == "UNRESOLVED"
        and observation.probability_status == "NOT_COMPUTED"
        and "event_outcome" in observation.unresolved_dimensions
        for observation in replay.observations
    )


def test_domain_vector_rejects_cross_case_inputs() -> None:
    _, mechanism, _, _ = _compile(
        case_ref="case-domain-a",
        birth_date=date(1977, 5, 8),
        birth_time=time(17, 30),
    )
    _, _, timing, _ = _compile(
        case_ref="case-domain-b",
        birth_date=date(1991, 8, 14),
        birth_time=time(9, 20),
    )

    with pytest.raises(ValueError, match="life_domain_vector_lineage_mismatch"):
        MingliLifeDomainEvidenceCompiler().compile(
            mechanism_vector=mechanism,
            timing_vector=timing,
        )
