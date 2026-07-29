from __future__ import annotations

from datetime import date, time

import pytest
from abu_v60.abu import MingliAbuExpressionProjector
from abu_v60.knowledge import (
    KnowledgeAuthority,
    KnowledgeProfileSelection,
    bazi_candidate_qualification_profile,
    bazi_foundation_profile,
    bazi_quant_foundation_profile,
)
from abu_v60.mingli import (
    CandidateQualificationEngine,
    MingliQuantFoundationCompiler,
    MingliReadingProjector,
    StructuralCandidateCompiler,
)
from abu_v60.mingli.calendar import BirthInput, ChartPillars
from abu_v60.mingli.compiler import CompiledCase, compile_case
from abu_v60.mingli.quant_contracts import MingliQuantFoundationVector
from abu_v60.mingli.reading import MingliReadingEnvelope
from abu_v60.provenance import content_hash, stable_ref


def _compiled_case(
    authority: KnowledgeAuthority | None = None,
) -> tuple[CompiledCase, MingliQuantFoundationVector]:
    compiled = compile_case(
        case_ref="case-1",
        birth_input=BirthInput(
            calendar_type="solar",
            birth_date=date(2000, 1, 1),
            birth_time=time(12, 0),
            timezone="Asia/Shanghai",
        ),
        chart=ChartPillars(
            year="甲子",
            month="乙丑",
            day="丙寅",
            hour="丁午",
        ),
        knowledge=authority,
    )
    vector = MingliQuantFoundationCompiler(authority).compile(
        case_ref="case-1",
        chart_version_ref=compiled.chart_version_ref,
        pillars=compiled.pillars,
        facts=compiled.facts,
    )
    return compiled, vector


def test_reading_is_stable_and_binds_exact_knowledge_profiles() -> None:
    compiled, quant_vector = _compiled_case()
    facts = compiled.facts
    candidates = StructuralCandidateCompiler().compile(
        chart_version_ref=compiled.chart_version_ref,
        facts=facts,
    )
    projector = MingliReadingProjector()

    first = projector.project(
        case_ref="case-1",
        chart_version_ref=compiled.chart_version_ref,
        life_case_revision_ref="life-v1",
        facts=facts,
        candidates=candidates,
        quant_vector=quant_vector,
    )
    second = projector.project(
        case_ref="case-1",
        chart_version_ref=compiled.chart_version_ref,
        life_case_revision_ref="life-v1",
        facts=list(reversed(facts)),
        candidates=tuple(reversed(candidates)),
        quant_vector=quant_vector,
    )

    assert first == second
    assert first.reading_ref.startswith("v60-mingli-reading-")
    assert first.foundation_profile.profile_hash
    assert first.candidate_rule_profile.profile_hash
    assert first.quant_foundation_profile is not None
    assert first.quant_foundation_profile.profile_hash
    assert first.quant_vector_ref == quant_vector.vector_ref
    assert first.mechanism_evidence_profile is not None
    assert first.mechanism_evidence_profile.profile_hash
    assert first.mechanism_vector_ref is not None
    assert first.foundation_profile.professionally_reviewed is False
    assert first.candidate_rule_profile.professionally_reviewed is False
    assert first.decision_refs == ()
    assert first.status == "MECHANISM_CANDIDATES_UNRESOLVED"
    assert "relation_effect" in first.unresolved_dimensions


def test_reading_rejects_candidate_from_another_chart() -> None:
    compiled, quant_vector = _compiled_case()
    facts = compiled.facts
    candidates = StructuralCandidateCompiler().compile(
        chart_version_ref=compiled.chart_version_ref,
        facts=facts,
    )

    with pytest.raises(ValueError, match="mingli_reading_candidate_chart_mismatch"):
        MingliReadingProjector().project(
            case_ref="case-1",
            chart_version_ref="chart-v2",
            life_case_revision_ref="life-v1",
            facts=facts,
            candidates=candidates,
            quant_vector=quant_vector,
        )


def test_explicit_profile_activation_changes_new_reading_not_source_facts() -> None:
    compiled, quant_vector = _compiled_case()
    facts = compiled.facts
    default_reading = MingliReadingProjector().project(
        case_ref="case-1",
        chart_version_ref=compiled.chart_version_ref,
        life_case_revision_ref="life-v1",
        facts=facts,
        candidates=StructuralCandidateCompiler().compile(
            chart_version_ref=compiled.chart_version_ref,
            facts=facts,
        ),
        quant_vector=quant_vector,
    )
    foundation_v1 = bazi_foundation_profile()
    candidate_v1 = bazi_candidate_qualification_profile()
    quant_v1 = bazi_quant_foundation_profile()
    foundation_v2 = foundation_v1.model_copy(
        update={
            "profile_version": "1.0.1-test",
            "source_refs": foundation_v1.source_refs
            + ("test-only:admitted-foundation-profile",),
        }
    )
    candidate_v2 = candidate_v1.model_copy(
        update={
            "profile_version": "1.0.1-test",
            "source_refs": candidate_v1.source_refs
            + ("test-only:admitted-candidate-profile",),
        }
    )
    authority = KnowledgeAuthority(
        profiles=(foundation_v1, foundation_v2),
        candidate_rule_profiles=(candidate_v1, candidate_v2),
        active_selection=KnowledgeProfileSelection.from_profiles(
            foundation=foundation_v2,
            candidate_rules=candidate_v2,
            quant_foundation=quant_v1,
        ),
    )
    candidates = StructuralCandidateCompiler(
        CandidateQualificationEngine(authority)
    ).compile(
        chart_version_ref=compiled.chart_version_ref,
        facts=facts,
    )
    upgraded_quant_vector = MingliQuantFoundationCompiler(authority).compile(
        case_ref="case-1",
        chart_version_ref=compiled.chart_version_ref,
        pillars=compiled.pillars,
        facts=facts,
    )
    upgraded = MingliReadingProjector(authority).project(
        case_ref="case-1",
        chart_version_ref=compiled.chart_version_ref,
        life_case_revision_ref="life-v1",
        facts=facts,
        candidates=candidates,
        quant_vector=upgraded_quant_vector,
    )

    assert upgraded.fact_refs == default_reading.fact_refs
    assert upgraded.reading_ref != default_reading.reading_ref
    assert upgraded.foundation_profile.profile_version == "1.0.1-test"
    assert upgraded.candidate_rule_profile.profile_version == "1.0.1-test"


def test_abu_expression_is_bound_to_reading_and_cannot_create_truth() -> None:
    compiled, quant_vector = _compiled_case()
    facts = compiled.facts
    candidates = StructuralCandidateCompiler().compile(
        chart_version_ref=compiled.chart_version_ref,
        facts=facts,
    )
    reading = MingliReadingProjector().project(
        case_ref="case-1",
        chart_version_ref=compiled.chart_version_ref,
        life_case_revision_ref="life-v1",
        facts=facts,
        candidates=candidates,
        quant_vector=quant_vector,
    )

    expression = MingliAbuExpressionProjector().project(reading=reading)

    assert expression.reading_ref == reading.reading_ref
    assert expression.explanation_ref is None
    assert expression.explanation_hash is None
    assert expression.reading_hash == reading.reading_hash
    assert expression.fact_refs == reading.fact_refs
    assert expression.candidate_refs == reading.candidate_refs
    assert expression.authority == "EXPRESSION_ONLY"
    assert expression.fact_creation is False
    assert expression.decision_creation is False
    assert "做功" in expression.boundary


def test_legacy_v1_reading_remains_hash_replayable_without_quant_fields() -> None:
    compiled, quant_vector = _compiled_case()
    facts = compiled.facts
    current = MingliReadingProjector().project(
        case_ref="case-1",
        chart_version_ref=compiled.chart_version_ref,
        life_case_revision_ref="life-v1",
        facts=facts,
        candidates=StructuralCandidateCompiler().compile(
            chart_version_ref=compiled.chart_version_ref,
            facts=facts,
        ),
        quant_vector=quant_vector,
    )
    legacy_identity = current.model_dump(
        mode="json",
        exclude={
            "reading_ref",
            "reading_hash",
            "quant_foundation_profile",
            "quant_vector_ref",
            "quant_vector_hash",
            "source_review_profile",
            "source_review_vector_ref",
            "source_review_vector_hash",
            "mechanism_evidence_profile",
            "mechanism_vector_ref",
            "mechanism_vector_hash",
            "timing_evidence_profile",
            "timing_vector_ref",
            "timing_vector_hash",
            "life_domain_vector_ref",
            "life_domain_vector_hash",
        },
    )
    legacy_identity["reading_version"] = "v60.mingli-reading.001"
    legacy = MingliReadingEnvelope.model_validate(
        {
            "reading_ref": stable_ref("v60-mingli-reading", legacy_identity),
            "reading_hash": content_hash(legacy_identity),
            **legacy_identity,
        }
    )

    assert legacy.reading_version == "v60.mingli-reading.001"
    assert legacy.quant_foundation_profile is None
    assert legacy.quant_vector_ref is None
