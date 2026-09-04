from __future__ import annotations

from datetime import date, time

from abu_v60.mingli import (
    MingliLifeDomainEvidenceCompiler,
    MingliMechanismEvidenceCompiler,
    MingliQuantFoundationCompiler,
    MingliReadingProjector,
    MingliRelationEffectResearchFrontierProjector,
    MingliSourceCoordinateReviewCompiler,
    MingliSourceDiscussionAbstentionProjector,
    MingliSourceUsabilityPrerequisiteProjector,
    MingliTimingEvidenceCompiler,
    StructuralCandidateCompiler,
)
from abu_v60.mingli.calendar import BirthInput, ChartPillars
from abu_v60.mingli.compiler import compile_research_case

ANALYSIS_DATE = date(2026, 7, 29)


def relation_effect_bundle(
    pillars: ChartPillars,
    *,
    reverse_facts: bool = False,
) -> dict[str, object]:
    case_ref = f"case-relation-frontier-{pillars.year}-{pillars.month}"
    birth_input = BirthInput(
        calendar_type="solar",
        birth_date=date(2000, 1, 1),
        birth_time=time(12, 0),
        timezone="Asia/Shanghai",
    )
    compiled = compile_research_case(
        case_ref=case_ref,
        chart=pillars,
    )
    facts = tuple(reversed(compiled.facts)) if reverse_facts else compiled.facts
    quant = MingliQuantFoundationCompiler().compile(
        case_ref=case_ref,
        chart_version_ref=compiled.chart_version_ref,
        pillars=compiled.pillars,
        facts=facts,
    )
    source_review = MingliSourceCoordinateReviewCompiler().compile(
        quant_vector=quant,
        facts=facts,
    )
    prerequisite = MingliSourceUsabilityPrerequisiteProjector().project(
        quant_vector=quant,
        source_review_vector=source_review,
    )
    mechanism = MingliMechanismEvidenceCompiler().compile(
        quant_vector=quant,
        facts=facts,
    )
    timing = MingliTimingEvidenceCompiler().compile(
        case_ref=case_ref,
        chart_version_ref=compiled.chart_version_ref,
        life_case_revision_ref=f"{case_ref}-life-v1",
        birth_input=birth_input,
        gender="male",
        pillars=compiled.pillars,
        facts=facts,
        analysis_date=ANALYSIS_DATE,
        mechanism_vector=mechanism,
    )
    domains = MingliLifeDomainEvidenceCompiler().compile(
        mechanism_vector=mechanism,
        timing_vector=timing,
    )
    reading = MingliReadingProjector().project(
        case_ref=case_ref,
        chart_version_ref=compiled.chart_version_ref,
        life_case_revision_ref=f"{case_ref}-life-v1",
        facts=facts,
        candidates=StructuralCandidateCompiler().compile(
            chart_version_ref=compiled.chart_version_ref,
            facts=facts,
        ),
        quant_vector=quant,
        source_review_vector=source_review,
        mechanism_vector=mechanism,
        timing_vector=timing,
        life_domain_vector=domains,
    )
    refusal = MingliSourceDiscussionAbstentionProjector().project(
        reading=reading,
        prerequisite=prerequisite,
    )
    return {
        "reading": reading,
        "source_review": source_review,
        "prerequisite": prerequisite,
        "refusal": refusal,
    }


def project_relation_effect_frontier(
    bundle: dict[str, object],
):
    return MingliRelationEffectResearchFrontierProjector().project(
        reading=bundle["reading"],
        source_review_vector=bundle["source_review"],
        prerequisite=bundle["prerequisite"],
        refusal=bundle["refusal"],
    )
