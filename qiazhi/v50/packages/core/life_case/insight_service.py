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
from core.mingli_agent.contracts import ChartWorldInstance, DomainExploration, MingliCognitiveRecord
from core.mingli_agent.reliability import cognition_semantic_signature


def build_baseline_insight(
    *,
    record: MingliCognitiveRecord,
    world: ChartWorldInstance,
    case_version: str = "v1",
) -> FormalInsight:
    cognition = record.cognition
    primary = next(
        (item for item in cognition.hypotheses if item.hypothesis_id == cognition.selected_hypothesis_id),
        cognition.hypotheses[0],
    )
    allowed_fact_ids = {item.fact_id for item in world.facts}
    cited = _unique([
        *cognition.evidence_refs,
        *(ref for item in cognition.salient_phenomena for ref in item.evidence_refs),
        *primary.supporting_evidence_refs,
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
    reasoning_path.append(ReasoningPathStep(
        premise=" → ".join([
            *cognition.work_path.source,
            *cognition.work_path.transformations,
            *cognition.work_path.target,
        ]),
        conclusion=cognition.work_path.path_statement,
        source_refs=[ref for ref in cognition.work_path.evidence_refs if ref in world.allowed_evidence_refs],
    ))
    strategy_dimensions: dict[str, list[dict[str, Any]]] = {}
    for item in cognition.useful_god_reasoning:
        strategy_dimensions.setdefault(item.lens, []).append(item.model_dump(mode="json"))
    epistemic_state = (
        record.reliability_disposition
        if record.reliability_disposition != "legacy_unreviewed"
        else "reliable" if record.review.passed and not any(issue.severity == "error" for issue in record.review.issues)
        else "blocked"
    )
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
        conditions=_unique([*primary.success_conditions, *cognition.work_path.success_conditions]),
        expected_manifestations=[item.claim for item in cognition.prior_predictions],
        counter_signals=_unique([*primary.failure_conditions, *cognition.work_path.failure_conditions]),
        uncertainty=InsightUncertainty(
            level={"high": "low", "medium": "medium", "low": "high"}[primary.confidence],
            reasons=list(cognition.unresolved_questions),
            competing_hypotheses=[
                item.thesis for item in cognition.hypotheses if item.hypothesis_id != primary.hypothesis_id
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
        epistemic_state=epistemic_state,
        source_review_gate=record.review.gate_version,
        source_review_issue_codes=[item.code for item in record.review.issues],
        strategy_dimensions=strategy_dimensions,
        baseline_record_id=record.record_id,
        baseline_semantic_signature=record.reliability_signature or cognition_semantic_signature(cognition),
        projection_payload={
            "record_projection": record.model_copy(update={
                "user_evidence": [],
                "revisions": [],
                "domain_explorations": {},
            }).model_dump(mode="json"),
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
    if not insight.claim.strip():
        errors.append("baseline_claim_missing")
    if not insight.reasoning_path:
        errors.append("reasoning_path_missing")
    if not insight.basis.chart_fact_refs:
        errors.append("chart_fact_basis_missing")
    if insight.epistemic_state != "reliable":
        errors.append(f"epistemic_state_not_committable:{insight.epistemic_state}")
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
    generated_at = exploration.generated_at or datetime.now(timezone.utc).isoformat()
    stable_key = f"{record.case_id}|{case_version}|{reading.domain.value}|{generated_at}"
    insight_suffix = hashlib.sha256(stable_key.encode("utf-8")).hexdigest()[:18]
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
        epistemic_state=exploration.reliability_disposition,
        source_review_gate=exploration.review.gate_version,
        source_review_issue_codes=[item.code for item in exploration.review.issues],
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

