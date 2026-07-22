from __future__ import annotations
import hashlib
import json
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from core.life_case.contracts import (
    FormalInsight,
    InsightBasis,
    InsightNextAction,
    InsightProvenance,
    InsightUncertainty,
    InsightValidationReceipt,
    LifeCase,
    ReasoningPathStep,
)
from core.life_case.service_support import (
    _require_active_life_case,
    _unique,
)
from core.mingli_agent.assertion_gate import accepted_assertion_refs
from core.mingli_agent.contracts import (
    ChartWorldInstance,
    DomainCausalReading,
    DomainExploration,
    MingliCognitiveRecord,
)
from core.mingli_agent.professional_review import (
    professional_projection_payload,
    review_professional_payload,
    review_professional_record,
)
from core.contracts.professional_review import ProfessionalReviewBundle
from core.mingli_agent.reliability import cognition_semantic_signature


def build_baseline_insight(
    *,
    record: MingliCognitiveRecord,
    world: ChartWorldInstance,
    case_version: str = "v1",
    professional_review: ProfessionalReviewBundle | None = None,
) -> FormalInsight:
    professional_review = professional_review or review_professional_record(
        record=record,
        world=world,
        persistence_status="persisted",
    )
    release_status = professional_review.overlay.professional_release_status
    projection_record = record
    if release_status == "partially_blocked":
        projected = professional_projection_payload(
            payload=record.cognition.model_dump(mode="json"),
            bundle=professional_review,
        )
        projection_record = record.model_copy(update={
            "cognition": record.cognition.model_validate(projected),
        })
    cognition = projection_record.cognition
    primary = next(
        (item for item in cognition.hypotheses if item.hypothesis_id == cognition.selected_hypothesis_id),
        cognition.hypotheses[0] if cognition.hypotheses else None,
    )
    accepted_refs = accepted_assertion_refs(record.assertion_gate)
    work_path_accepted = not record.assertion_gate.decisions or "baseline:work-path" in accepted_refs
    allowed_fact_ids = {item.fact_id for item in world.facts}
    cited = _unique([
        *cognition.evidence_refs,
        *(ref for item in cognition.salient_phenomena for ref in item.evidence_refs),
        *(primary.supporting_evidence_refs if primary is not None else []),
        *cognition.work_path.evidence_refs,
        *(ref for item in cognition.portrait for ref in item.evidence_refs),
    ])
    chart_fact_refs = [ref for ref in cited if ref in allowed_fact_ids]
    context_hash = str(record.context_manifest[0].get("content_hash") or "") if record.context_manifest else ""
    now = datetime.now(timezone.utc).isoformat()
    reasoning_path: list[ReasoningPathStep] = []
    for phenomenon in cognition.salient_phenomena[:2]:
        reasoning_path.append(ReasoningPathStep(
            premise=phenomenon.observation,
            conclusion=phenomenon.why_it_matters,
            source_refs=[ref for ref in phenomenon.evidence_refs if ref in world.allowed_evidence_refs],
        ))
    if work_path_accepted:
        reasoning_path.append(ReasoningPathStep(
            premise=" → ".join([
                *cognition.work_path.source,
                *cognition.work_path.transformations,
                *cognition.work_path.target,
            ]),
            conclusion=cognition.work_path.path_statement,
            source_refs=[ref for ref in cognition.work_path.evidence_refs if ref in world.allowed_evidence_refs],
        ))
    if (
        not reasoning_path
        and primary is not None
        and (
            not record.assertion_gate.decisions
            or primary.hypothesis_id in accepted_refs
        )
    ):
        primary_refs = [
            ref
            for ref in primary.supporting_evidence_refs
            if ref in world.allowed_evidence_refs
        ]
        reasoning_path.append(ReasoningPathStep(
            premise="、".join(primary_refs) or "已核验命盘事实",
            conclusion=primary.thesis,
            source_refs=primary_refs,
        ))
    strategy_dimensions: dict[str, list[dict[str, Any]]] = {}
    for item in cognition.useful_god_reasoning:
        strategy_dimensions.setdefault(item.lens, []).append(item.model_dump(mode="json"))
    epistemic_state = "blocked" if release_status == "blocked" else (
        record.reliability_disposition
        if record.reliability_disposition != "legacy_unreviewed"
        else "reliable" if record.review.passed and not any(issue.severity == "error" for issue in record.review.issues)
        else "blocked"
    )
    formal_assertion_gate = record.assertion_gate.model_copy(update={
        "decisions": [
            item.model_copy(update={"original_text": ""})
            if item.disposition in {"candidate", "suppressed"}
            else item
            for item in record.assertion_gate.decisions
        ],
    })
    return FormalInsight(
        insight_id=f"insight-baseline-{uuid4().hex[:18]}",
        case_id=record.case_id,
        case_version=case_version,
        type="baseline",
        claim=cognition.whole_chart_thesis,
        scope={"domain": "whole_chart", "temporal_activation": "not_applicable"},
        basis=InsightBasis(
            chart_fact_refs=chart_fact_refs,
            holistic_belief_refs=[item.hypothesis_id for item in cognition.hypotheses],
        ),
        reasoning_path=reasoning_path,
        conditions=_unique([
            *(primary.success_conditions if primary is not None else []),
            *(cognition.work_path.success_conditions if work_path_accepted else []),
        ]),
        expected_manifestations=[item.claim for item in cognition.prior_predictions],
        counter_signals=_unique([
            *(primary.failure_conditions if primary is not None else []),
            *(cognition.work_path.failure_conditions if work_path_accepted else []),
        ]),
        uncertainty=InsightUncertainty(
            level=(
                {"high": "low", "medium": "medium", "low": "high"}[primary.confidence]
                if primary is not None
                else "high"
            ),
            reasons=list(cognition.unresolved_questions),
            competing_hypotheses=[
                item.thesis
                for item in cognition.hypotheses
                if primary is None or item.hypothesis_id != primary.hypothesis_id
            ],
        ),
        next_action=InsightNextAction(
            text="选择一个现在真正关心的人生领域，再沿这条整盘主线继续推演。",
            category="observe",
        ),
        provenance=InsightProvenance(
            reasoner_id="deepbazi.mingli_agent",
            reasoner_version="baseline-cognition-v1",
            theory_version="deepbazi-world-v1",
            model_version=record.model,
            context_hash=context_hash,
            generated_at=now,
            source_record_id=record.record_id,
        ),
        status="draft",
        persistence_status=professional_review.overlay.persistence_status,
        professional_release_status=release_status,
        professional_review_overlay=professional_review.overlay,
        epistemic_state=epistemic_state,
        source_review_gate=professional_review.overlay.review_version,
        source_review_issue_codes=[item.issue_class for item in professional_review.overlay.issues],
        strategy_dimensions=strategy_dimensions,
        baseline_record_id=record.record_id,
        baseline_semantic_signature=record.reliability_signature or cognition_semantic_signature(cognition),
        projection_payload={
            "assertion_gate": formal_assertion_gate.model_dump(mode="json"),
            "professional_review": professional_review.overlay.model_dump(mode="json"),
            "record_projection": projection_record.model_copy(update={
                "user_evidence": [],
                "revisions": [],
                "domain_explorations": {},
                "assertion_gate": formal_assertion_gate,
            }).model_dump(mode="json") if release_status != "blocked" else None,
        },
    )
def validate_formal_insight(
    *,
    insight: FormalInsight,
    world: ChartWorldInstance,
) -> InsightValidationReceipt:
    allowed = set(world.allowed_evidence_refs)
    cited = _unique([
        *insight.basis.chart_fact_refs,
        *(ref for step in insight.reasoning_path for ref in step.source_refs),
    ])
    invalid_refs = [ref for ref in cited if ref not in allowed]
    traceable = [ref for ref in cited if ref in allowed]
    errors: list[str] = []
    warnings: list[str] = []
    if insight.status not in {"draft", "reviewed", "validated", "committed"}:
        errors.append(f"insight_status_not_formally_eligible:{insight.status}")
    if not insight.claim.strip():
        errors.append("baseline_claim_missing")
    if not insight.reasoning_path:
        errors.append("reasoning_path_missing")
    if not insight.basis.chart_fact_refs:
        errors.append("chart_fact_basis_missing")
    if insight.epistemic_state not in {"reliable", "competing"}:
        errors.append(f"epistemic_state_not_committable:{insight.epistemic_state}")
    if insight.persistence_status != "persisted":
        errors.append(f"persistence_status_not_committable:{insight.persistence_status}")
    if insight.professional_release_status not in {"passed", "partially_blocked"}:
        errors.append(
            f"professional_release_not_committable:{insight.professional_release_status}"
        )
    if insight.professional_review_overlay is None:
        errors.append("professional_review_overlay_missing")
    if insight.type == "domain_analysis" and insight.professional_review_overlay is not None:
        domain = str(insight.scope.get("domain") or "")
        if any(
            block.scope == "domain" and block.scope_ref == domain
            for block in insight.professional_review_overlay.scope_blocks
        ):
            errors.append(f"professional_domain_release_blocked:{domain}")
    if "mixed" in insight.strategy_dimensions:
        errors.append("ambiguous_strategy_dimension:mixed")
    if invalid_refs:
        errors.append(f"unknown_evidence_refs:{','.join(invalid_refs)}")
    if not insight.counter_signals:
        warnings.append("counter_signals_missing")
    if not insight.uncertainty.reasons and insight.uncertainty.level != "low":
        warnings.append("uncertainty_reason_missing")
    traceability = 1.0 if not cited else round(len(traceable) / len(cited), 4)
    return InsightValidationReceipt(
        passed=not errors,
        insight_id=insight.insight_id,
        errors=errors,
        warnings=warnings,
        checked_at=datetime.now(timezone.utc).isoformat(),
        fact_traceability_rate=traceability,
        epistemic_state=insight.epistemic_state,
    )


def build_domain_insight(
    *,
    record: MingliCognitiveRecord,
    exploration: DomainExploration,
    world: ChartWorldInstance,
    case_version: str,
) -> FormalInsight:
    reading = exploration.reading
    generated_at = exploration.generated_at or datetime.now(timezone.utc).isoformat()
    stable_key = f"{record.case_id}|{case_version}|{reading.domain.value}|{generated_at}"
    insight_suffix = hashlib.sha256(stable_key.encode("utf-8")).hexdigest()[:18]
    professional_review = review_professional_payload(
        payload={reading.domain.value: reading.model_dump(mode="json")},
        world=world,
        cognitive_record_ref=f"{record.record_id}:domain:{reading.domain.value}:{insight_suffix}",
        persistence_status="persisted",
    )
    if (
        professional_review.overlay.professional_release_status == "partially_blocked"
        and not professional_review.overlay.scope_blocks
    ):
        projected = professional_projection_payload(
            payload={reading.domain.value: reading.model_dump(mode="json")},
            bundle=professional_review,
        )
        reading = DomainCausalReading.model_validate(projected[reading.domain.value])
    fact_by_id = {item.fact_id: item for item in world.facts}
    cited = _unique([
        *(ref for assertion in reading.assertions for ref in assertion.evidence_refs),
        *(ref for assertion in reading.assertions for ref in assertion.counter_evidence_refs),
    ])
    chart_fact_refs = [ref for ref in cited if ref in fact_by_id]
    temporal_refs = [
        ref for ref in chart_fact_refs
        if fact_by_id[ref].category in {"timing", "timing_material", "luck_cycle", "annual_timing"}
        or "timing" in fact_by_id[ref].category
    ]
    reasoning_refs = [ref for ref in chart_fact_refs if ref not in temporal_refs]
    if not reasoning_refs:
        reasoning_refs = chart_fact_refs
    chain = [item.strip() for item in reading.causal_chain if item.strip()]
    reasoning_path = [
        ReasoningPathStep(
            premise=chain[index],
            conclusion=chain[index + 1],
            source_refs=reasoning_refs,
        )
        for index in range(max(0, len(chain) - 1))
    ]
    if not reasoning_path and reading.assertions:
        reasoning_path = [
            ReasoningPathStep(
                premise=reading.assertions[0].rationale,
                conclusion=reading.assertions[0].claim,
                source_refs=reasoning_refs,
            )
        ]
    supported = [
        item for item in reading.assertions
        if item.epistemic_status == "supported"
    ]
    claim = (
        supported[0].claim
        if supported
        else reading.assertions[0].claim
        if reading.assertions
        else reading.stable_tendencies[0]
        if reading.stable_tendencies
        else reading.core_question
    )
    context_hash = hashlib.sha256(
        json.dumps(exploration.context_manifest, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()[:24]
    status_levels = {item.epistemic_status for item in reading.assertions}
    uncertainty_level = (
        "high" if not reading.assertions or status_levels == {"unresolved"}
        else "low" if status_levels == {"supported"} and not reading.unknowns
        else "medium"
    )
    return FormalInsight(
        insight_id=f"insight-domain-{insight_suffix}",
        case_id=record.case_id,
        case_version=case_version,
        type="domain_analysis",
        claim=claim,
        scope={"domain": reading.domain.value},
        basis=InsightBasis(
            chart_fact_refs=chart_fact_refs,
            holistic_belief_refs=[record.cognition.selected_hypothesis_id],
            temporal_activation_refs=temporal_refs,
        ),
        reasoning_path=reasoning_path,
        conditions=_unique([*reading.favorable_environments, *reading.opportunity_conditions]),
        expected_manifestations=_unique([*reading.stable_tendencies, *reading.prior_directions]),
        counter_signals=_unique([
            *reading.adverse_environments,
            *reading.risk_conditions,
            *(signal for assertion in reading.assertions for signal in assertion.falsifiers),
        ]),
        uncertainty=InsightUncertainty(
            level=uncertainty_level,
            reasons=list(reading.unknowns),
            competing_hypotheses=[
                item.thesis
                for item in record.cognition.hypotheses
                if item.hypothesis_id != record.cognition.selected_hypothesis_id
            ],
        ),
        next_action=InsightNextAction(
            text=(
                reading.next_probe.question
                if reading.next_probe is not None
                else "结合一个具体的现实问题继续验证这条领域判断。"
            ),
            category="observe",
        ),
        provenance=InsightProvenance(
            reasoner_id="deepbazi.mingli_agent.domain",
            reasoner_version="on-demand-domain-v1",
            theory_version="deepbazi-world-v1",
            model_version=record.model,
            context_hash=context_hash,
            generated_at=generated_at,
            source_record_id=record.record_id,
        ),
        status="draft",
        persistence_status=professional_review.overlay.persistence_status,
        professional_release_status=professional_review.overlay.professional_release_status,
        professional_review_overlay=professional_review.overlay,
        epistemic_state=exploration.reliability_disposition,
        source_review_gate=professional_review.overlay.review_version,
        source_review_issue_codes=[item.issue_class for item in professional_review.overlay.issues],
        baseline_insight_id=exploration.baseline_insight_id,
        baseline_record_id=exploration.baseline_record_id,
        baseline_semantic_signature=exploration.baseline_semantic_signature,
        projection_payload={"domain_exploration": exploration.model_dump(mode="json")},
    )


def build_case_revision_insight(
    *,
    life_case: LifeCase,
    candidate_id: str,
) -> FormalInsight:
    _require_active_life_case(life_case)
    candidate = next(
        (item for item in life_case.case_revision_candidates if item.candidate_id == candidate_id),
        None,
    )
    if candidate is None:
        raise ValueError("case_revision_candidate_not_found")
    if candidate.status != "pending" or candidate.reliability_state != "eligible":
        raise ValueError("case_revision_candidate_not_committable")
    baseline = life_case.baseline_insight
    now = datetime.now(timezone.utc).isoformat()
    return FormalInsight(
        insight_id=f"insight-case-revision-{uuid4().hex[:16]}",
        case_id=life_case.case_id,
        case_version=candidate.to_case_version,
        type="case_revision",
        claim=candidate.proposed_claim,
        scope={"period_key": candidate.period_key, "monthly_review_id": candidate.monthly_review_id},
        basis=InsightBasis(
            chart_fact_refs=baseline.basis.chart_fact_refs,
            holistic_belief_refs=baseline.basis.holistic_belief_refs,
            reality_context_refs=candidate.reality_evidence_refs,
        ),
        reasoning_path=[
            ReasoningPathStep(
                premise="月度先验与用户确认的现实记录已经按同一时间窗口完成比较。",
                conclusion=candidate.proposed_claim,
                source_refs=baseline.basis.chart_fact_refs,
            ),
        ],
        conditions=list(baseline.conditions),
        expected_manifestations=[],
        counter_signals=list(baseline.counter_signals),
        uncertainty=InsightUncertainty(
            level="medium" if "保留" in candidate.uncertainty_change else "low",
            reasons=[candidate.uncertainty_change],
            competing_hypotheses=list(baseline.uncertainty.competing_hypotheses),
        ),
        next_action=InsightNextAction(
            text="继续记录下一阶段的现实变化；不要用单月结果改写原局事实。",
            category="observe",
        ),
        provenance=InsightProvenance(
            reasoner_id="deepbazi.case_revision_protocol",
            reasoner_version="monthly-evidence-review-v1",
            theory_version=baseline.provenance.theory_version,
            model_version="deterministic-evidence-comparison-v1",
            context_hash=hashlib.sha256(candidate.model_dump_json().encode("utf-8")).hexdigest()[:24],
            generated_at=now,
            source_record_id=candidate.candidate_id,
        ),
        status="draft",
        persistence_status="persisted",
        professional_release_status=baseline.professional_release_status,
        professional_review_overlay=baseline.professional_review_overlay,
        epistemic_state="reliable",
        source_review_gate="life_case_revision_gate_v1",
        baseline_insight_id=baseline.insight_id,
        baseline_record_id=baseline.baseline_record_id,
        baseline_semantic_signature=baseline.baseline_semantic_signature,
        projection_payload={
            "candidate": candidate.model_dump(mode="json"),
            "preserved_baseline_insight_id": baseline.insight_id,
        },
    )
