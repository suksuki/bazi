from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from core.life_case.contracts import (
    CaseRevisionCandidate,
    ChartVersionRef,
    FormalInsight,
    InsightBasis,
    InsightNextAction,
    InsightProvenance,
    InsightUncertainty,
    InsightValidationReceipt,
    LifeCase,
    LifeCaseRevision,
    LifeCaseVersionSnapshot,
    MonthlyReview,
    MonthlyReviewVerdict,
    RealityEvidence,
    RealityEvidenceRevision,
    ReasoningPathStep,
    TemporalSnapshot,
    WorkspaceState,
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


def commit_baseline_life_case(
    *,
    insight: FormalInsight,
    world: ChartWorldInstance,
    profile_id: str | None,
) -> tuple[LifeCase, InsightValidationReceipt]:
    receipt = validate_formal_insight(insight=insight, world=world)
    if not receipt.passed:
        raise ValueError(f"formal_insight_validation_failed:{','.join(receipt.errors)}")
    now = datetime.now(timezone.utc).isoformat()
    committed = insight.model_copy(update={"status": "committed"})
    life_case = LifeCase(
        life_case_id=f"life-case-{uuid4().hex[:20]}",
        case_id=insight.case_id,
        profile_id=profile_id,
        chart_version=ChartVersionRef(
            version_id=f"chart-version-{uuid4().hex[:16]}",
            world_id=world.world_id,
            chart_hash=_chart_hash(world),
            created_at=now,
        ),
        baseline_insight=committed,
        revisions=[LifeCaseRevision(
            revision_id=f"life-revision-{uuid4().hex[:16]}",
            kind="baseline_committed",
            created_at=now,
            insight_id=committed.insight_id,
            summary="整盘基线认知已经通过引用与版本检查并提交。",
        )],
        created_at=now,
        updated_at=now,
    )
    return life_case, receipt


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


def commit_domain_insight(
    *,
    life_case: LifeCase,
    insight: FormalInsight,
    world: ChartWorldInstance,
) -> tuple[LifeCase, InsightValidationReceipt]:
    if insight.case_id != life_case.case_id or insight.case_version != life_case.case_version:
        raise ValueError("formal_insight_case_version_mismatch")
    baseline_reference_matches = bool(
        insight.baseline_insight_id
        and insight.baseline_insight_id == life_case.baseline_insight.insight_id
        and insight.baseline_record_id == life_case.baseline_insight.baseline_record_id
        and insight.baseline_semantic_signature == life_case.baseline_insight.baseline_semantic_signature
    )
    if not baseline_reference_matches:
        raise ValueError("domain_baseline_reference_mismatch")
    receipt = validate_formal_insight(insight=insight, world=world)
    if not receipt.passed:
        raise ValueError(f"formal_insight_validation_failed:{','.join(receipt.errors)}")
    domain = str(insight.scope.get("domain") or "")
    if not domain:
        raise ValueError("domain_scope_missing")
    existing = life_case.domain_insights.get(domain, [])
    if any(item.insight_id == insight.insight_id for item in existing):
        return life_case, receipt
    now = datetime.now(timezone.utc).isoformat()
    committed = insight.model_copy(update={"status": "committed"})
    return life_case.model_copy(update={
        "domain_insights": {
            **life_case.domain_insights,
            domain: [*existing, committed],
        },
        "revisions": [
            *life_case.revisions,
            LifeCaseRevision(
                revision_id=f"life-revision-{uuid4().hex[:16]}",
                kind="domain_insight_committed",
                created_at=now,
                insight_id=committed.insight_id,
                summary=f"{domain} 专题洞察已经通过引用检查并写入当前案例。",
            ),
        ],
        "updated_at": now,
    }), receipt


def record_reality_evidence(
    *,
    life_case: LifeCase,
    evidence: RealityEvidence | dict[str, Any],
) -> LifeCase:
    updated, _, _ = upsert_reality_evidence(life_case=life_case, evidence=evidence)
    return updated


def build_reality_evidence(
    *,
    life_case: LifeCase,
    idempotency_key: str,
    source: str,
    summary: str,
    period_key: str,
    domain: str = "whole_chart",
    source_ref: str = "",
    kind: str = "life_event",
    occurred_at: str = "",
    confirmation_status: str = "reported",
    severity: str = "unknown",
    subjective_impact: str = "",
    structured_payload: dict[str, Any] | None = None,
) -> RealityEvidence:
    _require_active_life_case(life_case)
    normalized_key = idempotency_key.strip()
    if not normalized_key:
        raise ValueError("reality_evidence_idempotency_key_missing")
    normalized_summary = " ".join(summary.strip().split())
    if not normalized_summary:
        raise ValueError("reality_evidence_summary_missing")
    period = normalize_period_key(period_key)
    now = datetime.now(timezone.utc).isoformat()
    suffix = hashlib.sha256(f"{life_case.case_id}|{normalized_key}".encode("utf-8")).hexdigest()[:20]
    return RealityEvidence(
        evidence_id=f"reality-{suffix}",
        idempotency_key=normalized_key,
        case_id=life_case.case_id,
        case_version_at_recording=life_case.case_version,
        source=source,
        source_ref=source_ref,
        kind=kind,
        summary=normalized_summary,
        domain=domain,
        period_key=period,
        occurred_at=occurred_at,
        recorded_at=now,
        updated_at=now,
        confirmation_status=confirmation_status,
        severity=severity,
        subjective_impact=subjective_impact,
        structured_payload=structured_payload or {},
    )


def upsert_reality_evidence(
    *,
    life_case: LifeCase,
    evidence: RealityEvidence | dict[str, Any],
) -> tuple[LifeCase, RealityEvidence, bool]:
    _require_active_life_case(life_case)
    parsed = evidence if isinstance(evidence, RealityEvidence) else _coerce_reality_evidence(
        life_case=life_case,
        evidence=evidence,
    )
    if parsed.case_id != life_case.case_id:
        raise ValueError("reality_evidence_case_mismatch")
    index = next(
        (
            position
            for position, item in enumerate(life_case.reality_evidence)
            if item.idempotency_key == parsed.idempotency_key or item.evidence_id == parsed.evidence_id
        ),
        None,
    )
    if index is not None:
        current = life_case.reality_evidence[index]
        if _evidence_semantic_payload(current) == _evidence_semantic_payload(parsed):
            return life_case, current, False
        now = datetime.now(timezone.utc).isoformat()
        revised = current.model_copy(update={
            "summary": parsed.summary,
            "domain": parsed.domain,
            "period_key": parsed.period_key,
            "occurred_at": parsed.occurred_at,
            "confirmation_status": parsed.confirmation_status,
            "severity": parsed.severity,
            "subjective_impact": parsed.subjective_impact,
            "structured_payload": parsed.structured_payload,
            "revision_number": current.revision_number + 1,
            "updated_at": now,
            "revisions": [
                *current.revisions,
                RealityEvidenceRevision(
                    revision_id=f"evidence-revision-{uuid4().hex[:16]}",
                    revision_number=current.revision_number + 1,
                    changed_at=now,
                    summary="现实记录内容已修订，原记录 ID 与幂等键保持不变。",
                ),
            ],
        })
        rows = list(life_case.reality_evidence)
        rows[index] = revised
        updated = life_case.model_copy(update={
            "reality_evidence": rows,
            "revisions": [
                *life_case.revisions,
                LifeCaseRevision(
                    revision_id=f"life-revision-{uuid4().hex[:16]}",
                    kind="reality_evidence_updated",
                    created_at=now,
                    summary="同一现实记录已按幂等键修订；没有创建重复业务记录。",
                ),
            ],
            "updated_at": now,
        })
        return updated, revised, False
    now = datetime.now(timezone.utc).isoformat()
    updated = life_case.model_copy(update={
        "reality_evidence": [*life_case.reality_evidence, parsed],
        "revisions": [
            *life_case.revisions,
            LifeCaseRevision(
                revision_id=f"life-revision-{uuid4().hex[:16]}",
                kind="reality_evidence_added",
                created_at=now,
                summary="现实反馈已加入当前案例；原始命盘事实与全局理论保持不变。",
            ),
        ],
        "updated_at": now,
    })
    return updated, parsed, True


def commit_temporal_prior(
    *,
    life_case: LifeCase,
    insight: FormalInsight,
    world: ChartWorldInstance,
) -> tuple[LifeCase, InsightValidationReceipt]:
    return _commit_followup_insight(
        life_case=life_case,
        insight=insight,
        world=world,
        expected_type="temporal_prior",
        collection="temporal_priors",
        revision_kind="temporal_prior_committed",
        revision_summary="阶段先验已在观察窗口前独立提交，后续现实反馈不得覆盖原文。",
    )


def commit_case_revision(
    *,
    life_case: LifeCase,
    insight: FormalInsight,
    world: ChartWorldInstance,
) -> tuple[LifeCase, InsightValidationReceipt]:
    _require_active_life_case(life_case)
    if insight.type != "case_revision":
        raise ValueError("formal_insight_type_mismatch:case_revision")
    next_version = _next_case_version(life_case.case_version)
    if insight.case_id != life_case.case_id or insight.case_version not in {life_case.case_version, next_version}:
        raise ValueError("formal_insight_case_version_mismatch")
    receipt = validate_formal_insight(insight=insight, world=world)
    if not receipt.passed:
        raise ValueError(f"formal_insight_validation_failed:{','.join(receipt.errors)}")
    if any(item.insight_id == insight.insight_id for item in life_case.case_revisions):
        return life_case, receipt
    now = datetime.now(timezone.utc).isoformat()
    committed = insight.model_copy(update={"status": "committed"})
    versioned = insight.case_version == next_version
    history = list(life_case.version_history)
    if versioned:
        history.append(_version_snapshot(life_case=life_case, superseded_at=now))
    candidate_id = insight.provenance.source_record_id
    candidates = [
        item.model_copy(update={"status": "committed"})
        if item.candidate_id == candidate_id and item.status == "pending"
        else item
        for item in life_case.case_revision_candidates
    ]
    return life_case.model_copy(update={
        "case_version": insight.case_version if versioned else life_case.case_version,
        "case_revisions": [*life_case.case_revisions, committed],
        "case_revision_candidates": candidates,
        "version_history": history,
        "revisions": [
            *life_case.revisions,
            LifeCaseRevision(
                revision_id=f"life-revision-{uuid4().hex[:16]}",
                kind="case_revision_committed",
                created_at=now,
                insight_id=committed.insight_id,
                summary=(
                    f"事后案例修正已提交为 {insight.case_version}；旧版本保留审计。"
                    if versioned
                    else "事后案例修正已独立提交；原始先验保持不变。"
                ),
            ),
        ],
        "updated_at": now,
    }), receipt


def ensure_temporal_snapshot(
    *,
    life_case: LifeCase,
    period_key: str,
    system_period_key: str | None = None,
) -> tuple[LifeCase, TemporalSnapshot, bool]:
    _require_active_life_case(life_case)
    period = normalize_period_key(period_key)
    system_period = normalize_period_key(system_period_key or datetime.now(timezone.utc).strftime("%Y-%m"))
    temporal_insight = _temporal_insight_for(life_case=life_case, period_key=period)
    reality_refs = [item.evidence_id for item in life_case.reality_evidence if item.period_key == period]
    fingerprint_payload = {
        "chart_version": life_case.chart_version.version_id,
        "case_version": life_case.case_version,
        "baseline_insight": life_case.baseline_insight.insight_id,
        "temporal_insight": temporal_insight.insight_id if temporal_insight else "",
        "period": period,
        "reality_evidence_refs": reality_refs,
        "contract": "temporal_snapshot_v1",
    }
    fingerprint = hashlib.sha256(
        json.dumps(fingerprint_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()[:24]
    existing = next(
        (
            item
            for item in reversed(life_case.temporal_snapshots)
            if item.period_key == period
            and item.status == "active"
            and item.implementation_fingerprint == fingerprint
        ),
        None,
    )
    if existing:
        return life_case, existing, False
    perspective = "past" if period < system_period else "future" if period > system_period else "current"
    if temporal_insight:
        observation_theme = temporal_insight.claim
        conditions = temporal_insight.conditions
        counters = temporal_insight.counter_signals
        uncertainties = temporal_insight.uncertainty.reasons
    else:
        observation_theme = "该月的阶段专题尚未按需形成"
        conditions = []
        counters = []
        uncertainties = ["当前只有命盘时间位置，尚无经过可靠性门禁的月度命理解释。"]
    summary = {
        "past": f"{period} 用于复盘；已关联 {len(reality_refs)} 条现实记录。",
        "current": f"{period} 是当前现实月份；页面与 Abu 共享这个时间上下文。",
        "future": f"{period} 只作为先验观察窗口，不引用尚未发生的现实。",
    }[perspective]
    now = datetime.now(timezone.utc).isoformat()
    snapshot = TemporalSnapshot(
        snapshot_id=f"temporal-{hashlib.sha256(f'{life_case.case_id}|{fingerprint}'.encode()).hexdigest()[:20]}",
        case_id=life_case.case_id,
        case_version=life_case.case_version,
        chart_version_id=life_case.chart_version.version_id,
        period_key=period,
        system_period_key=system_period,
        perspective=perspective,
        baseline_insight_id=life_case.baseline_insight.insight_id,
        temporal_insight_id=temporal_insight.insight_id if temporal_insight else "",
        reality_evidence_refs=reality_refs,
        observation_theme=observation_theme,
        summary=summary,
        conditions=conditions,
        counter_signals=counters,
        uncertainties=uncertainties,
        implementation_fingerprint=fingerprint,
        generated_at=now,
    )
    snapshots = [
        item.model_copy(update={"status": "superseded"})
        if item.period_key == period and item.status == "active"
        else item
        for item in life_case.temporal_snapshots
    ]
    updated = life_case.model_copy(update={
        "temporal_snapshots": [*snapshots, snapshot],
        "revisions": [
            *life_case.revisions,
            LifeCaseRevision(
                revision_id=f"life-revision-{uuid4().hex[:16]}",
                kind="temporal_snapshot_selected",
                created_at=now,
                insight_id=snapshot.temporal_insight_id,
                summary=f"{period} 的时间快照已建立；整盘基线没有改变。",
            ),
        ],
        "updated_at": now,
    })
    return updated, snapshot, True


def build_workspace_state(
    *,
    case_id: str,
    selected_period: str | None = None,
    active_mode: str = "member",
    active_domain: str = "whole_chart",
) -> WorkspaceState:
    now = datetime.now(timezone.utc)
    system_period = now.strftime("%Y-%m")
    return WorkspaceState(
        workspace_id=f"workspace-{uuid4().hex[:18]}",
        case_id=case_id,
        selected_period=normalize_period_key(selected_period or system_period),
        system_period=system_period,
        active_mode=active_mode,
        active_domain=active_domain,
        updated_at=now.isoformat(),
    )


def select_workspace_period(
    *,
    workspace: WorkspaceState,
    period_key: str,
) -> WorkspaceState:
    return workspace.model_copy(update={
        "selected_period": normalize_period_key(period_key),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    })


def complete_monthly_review(
    *,
    life_case: LifeCase,
    period_key: str,
    temporal_snapshot_id: str,
    evidence_refs: list[str],
    verdict: MonthlyReviewVerdict,
    user_note: str = "",
) -> tuple[LifeCase, MonthlyReview, CaseRevisionCandidate]:
    _require_active_life_case(life_case)
    period = normalize_period_key(period_key)
    snapshot = next(
        (
            item
            for item in life_case.temporal_snapshots
            if item.snapshot_id == temporal_snapshot_id and item.period_key == period and item.status == "active"
        ),
        None,
    )
    if snapshot is None:
        raise ValueError("temporal_snapshot_not_found")
    allowed_evidence = {item.evidence_id for item in life_case.reality_evidence if item.period_key == period}
    refs = _unique(evidence_refs)
    if any(ref not in allowed_evidence for ref in refs):
        raise ValueError("monthly_review_evidence_scope_mismatch")
    if verdict not in {"not_observed", "insufficient_evidence"} and not refs:
        raise ValueError("monthly_review_evidence_required")
    normalized_note = " ".join(user_note.strip().split())
    existing_review = next(
        (
            item
            for item in reversed(life_case.monthly_reviews)
            if item.status == "completed"
            and item.period_key == period
            and item.temporal_snapshot_id == snapshot.snapshot_id
            and item.evidence_refs == refs
            and item.verdict == verdict
            and item.user_note == normalized_note
        ),
        None,
    )
    if existing_review is not None:
        existing_candidate = next(
            (
                item
                for item in reversed(life_case.case_revision_candidates)
                if item.monthly_review_id == existing_review.review_id
            ),
            None,
        )
        if existing_candidate is not None:
            return life_case, existing_review, existing_candidate
    now = datetime.now(timezone.utc).isoformat()
    verdict_text = {
        "supported": "现实记录支持该月先验",
        "partially_supported": "现实记录部分支持该月先验",
        "not_observed": "本月尚未观察到先验表现",
        "contradicted": "现实记录与该月先验形成反证",
        "insufficient_evidence": "现有记录不足以判断该月先验",
    }[verdict]
    review = MonthlyReview(
        review_id=f"monthly-review-{uuid4().hex[:18]}",
        case_id=life_case.case_id,
        case_version=life_case.case_version,
        period_key=period,
        temporal_snapshot_id=snapshot.snapshot_id,
        evidence_refs=refs,
        verdict=verdict,
        user_note=normalized_note,
        system_summary=verdict_text,
        created_at=now,
        updated_at=now,
    )
    next_version = _next_case_version(life_case.case_version)
    candidate = CaseRevisionCandidate(
        candidate_id=f"case-revision-candidate-{uuid4().hex[:16]}",
        case_id=life_case.case_id,
        from_case_version=life_case.case_version,
        to_case_version=next_version,
        monthly_review_id=review.review_id,
        period_key=period,
        prior_insight_refs=_unique([snapshot.temporal_insight_id, snapshot.baseline_insight_id]),
        reality_evidence_refs=refs,
        proposed_claim=f"{period} 月度复盘：{verdict_text}。",
        preserved_claims=[life_case.baseline_insight.claim],
        uncertainty_change=(
            "相关阶段判断的不确定性下降，但整盘基线不变。"
            if verdict in {"supported", "contradicted"}
            else "证据仍不足，保留原有不确定性。"
        ),
        reliability_state="eligible",
        created_at=now,
    )
    previous_reviews = [
        item.model_copy(update={"status": "withdrawn", "updated_at": now})
        if item.period_key == period and item.status == "completed"
        else item
        for item in life_case.monthly_reviews
    ]
    updated = life_case.model_copy(update={
        "monthly_reviews": [*previous_reviews, review],
        "case_revision_candidates": [*life_case.case_revision_candidates, candidate],
        "revisions": [
            *life_case.revisions,
            LifeCaseRevision(
                revision_id=f"life-revision-{uuid4().hex[:16]}",
                kind="monthly_review_completed",
                created_at=now,
                summary=f"{period} 月度复盘已完成；现实事实与命理认知仍分开保存。",
            ),
            LifeCaseRevision(
                revision_id=f"life-revision-{uuid4().hex[:16]}",
                kind="case_revision_candidate_created",
                created_at=now,
                summary=f"已形成从 {life_case.case_version} 到 {next_version} 的案例修正候选。",
            ),
        ],
        "updated_at": now,
    })
    return updated, review, candidate


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


def _commit_followup_insight(
    *,
    life_case: LifeCase,
    insight: FormalInsight,
    world: ChartWorldInstance,
    expected_type: str,
    collection: str,
    revision_kind: str,
    revision_summary: str,
) -> tuple[LifeCase, InsightValidationReceipt]:
    if insight.type != expected_type:
        raise ValueError(f"formal_insight_type_mismatch:{expected_type}")
    if insight.case_id != life_case.case_id or insight.case_version != life_case.case_version:
        raise ValueError("formal_insight_case_version_mismatch")
    receipt = validate_formal_insight(insight=insight, world=world)
    if not receipt.passed:
        raise ValueError(f"formal_insight_validation_failed:{','.join(receipt.errors)}")
    values = list(getattr(life_case, collection))
    if any(item.insight_id == insight.insight_id for item in values):
        return life_case, receipt
    now = datetime.now(timezone.utc).isoformat()
    committed = insight.model_copy(update={"status": "committed"})
    return life_case.model_copy(update={
        collection: [*values, committed],
        "revisions": [
            *life_case.revisions,
            LifeCaseRevision(
                revision_id=f"life-revision-{uuid4().hex[:16]}",
                kind=revision_kind,
                created_at=now,
                insight_id=committed.insight_id,
                summary=revision_summary,
            ),
        ],
        "updated_at": now,
    }), receipt


def project_life_case(life_case: LifeCase, *, role_mode: str) -> dict[str, Any]:
    baseline = life_case.baseline_insight
    latest_case_revision = next(
        (item for item in reversed(life_case.case_revisions) if item.status == "committed"),
        None,
    )
    public = {
        "life_case_id": life_case.life_case_id,
        "case_version": life_case.case_version,
        "status": life_case.status,
        "read_only": life_case.status != "active" or not life_case.chart_version.active,
        "chart_version_id": life_case.chart_version.version_id,
        "baseline": {
            "insight_id": baseline.insight_id,
            "status": baseline.status,
            "claim": baseline.claim,
            "conditions": baseline.conditions,
            "expected_manifestations": baseline.expected_manifestations,
            "counter_signals": baseline.counter_signals,
            "uncertainty": baseline.uncertainty.model_dump(mode="json"),
            "next_action": baseline.next_action.model_dump(mode="json") if baseline.next_action else None,
        },
        "temporal_prior_count": len(life_case.temporal_priors),
        "temporal_snapshot_count": len([item for item in life_case.temporal_snapshots if item.status == "active"]),
        "reality_evidence_count": len([item for item in life_case.reality_evidence if item.confirmation_status != "withdrawn"]),
        "monthly_review_count": len([item for item in life_case.monthly_reviews if item.status == "completed"]),
        "available_domain_insights": sorted(life_case.domain_insights),
        "case_revision_count": len(life_case.case_revisions),
        "version_history_count": len(life_case.version_history),
        "latest_case_revision": {
            "insight_id": latest_case_revision.insight_id,
            "case_version": latest_case_revision.case_version,
            "summary": latest_case_revision.claim,
            "interpretation": (
                latest_case_revision.uncertainty.reasons[0]
                if latest_case_revision.uncertainty.reasons
                else "这次修正只更新案例理解，不改变出生资料和原局事实。"
            ),
            "scope": latest_case_revision.scope,
            "committed_at": latest_case_revision.provenance.generated_at,
        } if latest_case_revision else None,
    }
    if role_mode in {"practitioner", "research"}:
        public["baseline"]["basis"] = baseline.basis.model_dump(mode="json")
        public["baseline"]["reasoning_path"] = [item.model_dump(mode="json") for item in baseline.reasoning_path]
        public["baseline"]["provenance"] = baseline.provenance.model_dump(mode="json")
    return public


def formal_projection_record(
    *,
    life_case: LifeCase,
    fallback_record: MingliCognitiveRecord,
) -> MingliCognitiveRecord:
    """Rebuild the visible cognition from committed LifeCase insights.

    Legacy cases may not yet contain a projection payload, so they retain a
    read-only fallback. New cases never need RunRecord conclusions for page
    restoration.
    """

    payload = life_case.baseline_insight.projection_payload.get("record_projection")
    if isinstance(payload, dict):
        try:
            record = MingliCognitiveRecord.model_validate(payload)
        except Exception:  # noqa: BLE001 - compatibility read only.
            record = fallback_record
    else:
        record = fallback_record
    committed_domains = dict(record.domain_explorations)
    for domain, insights in life_case.domain_insights.items():
        committed = next((item for item in reversed(insights) if item.status == "committed"), None)
        if committed is None:
            continue
        exploration = committed.projection_payload.get("domain_exploration")
        if not isinstance(exploration, dict):
            continue
        try:
            from core.mingli_agent.contracts import DomainExploration

            parsed = DomainExploration.model_validate(exploration)
        except Exception:  # noqa: BLE001 - malformed legacy projection is ignored.
            continue
        committed_domains[parsed.domain] = parsed
    return record.model_copy(update={"domain_explorations": committed_domains})


def normalize_period_key(value: str) -> str:
    candidate = value.strip()
    if len(candidate) != 7 or candidate[4] != "-":
        raise ValueError("period_key_must_be_yyyy_mm")
    try:
        year = int(candidate[:4])
        month = int(candidate[5:])
    except ValueError as exc:
        raise ValueError("period_key_must_be_yyyy_mm") from exc
    if not 1900 <= year <= 2100 or not 1 <= month <= 12:
        raise ValueError("period_key_out_of_range")
    return f"{year:04d}-{month:02d}"


def _chart_hash(world: ChartWorldInstance) -> str:
    payload = {
        "pillars": world.pillars,
        "birth_profile": world.birth_profile,
        "world_id": world.world_id,
    }
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:24]


def _unique(items: list[str]) -> list[str]:
    return list(dict.fromkeys(item for item in items if item))


def _require_active_life_case(life_case: LifeCase) -> None:
    if life_case.status != "active" or not life_case.chart_version.active:
        raise ValueError("life_case_read_only")


def _coerce_reality_evidence(*, life_case: LifeCase, evidence: dict[str, Any]) -> RealityEvidence:
    evidence_id = str(evidence.get("evidence_id") or "").strip()
    idempotency_key = str(evidence.get("idempotency_key") or f"legacy:{evidence_id}").strip()
    if not evidence_id:
        raise ValueError("reality_evidence_id_missing")
    recorded_at = str(evidence.get("recorded_at") or datetime.now(timezone.utc).isoformat())
    year_value = evidence.get("year_value")
    period_key = str(evidence.get("period_key") or "")
    if not period_key:
        period_key = f"{int(year_value):04d}-01" if isinstance(year_value, int) else recorded_at[:7]
    source = str(evidence.get("source") or "import")
    if source in {"user_reported", "practitioner_reported", "research_observation"}:
        source = {
            "user_reported": "probe" if evidence.get("plan_id") else "import",
            "practitioner_reported": "practitioner",
            "research_observation": "research",
        }[source]
    return RealityEvidence(
        evidence_id=evidence_id,
        idempotency_key=idempotency_key,
        case_id=life_case.case_id,
        case_version_at_recording=life_case.case_version,
        source=source,
        source_ref=str(evidence.get("source_ref") or evidence.get("source_probe_id") or evidence.get("plan_id") or ""),
        kind=str(evidence.get("kind") or evidence.get("evidence_kind") or "life_event"),
        summary=str(evidence.get("summary") or evidence.get("event_note") or evidence.get("option_label") or "现实记录"),
        domain=str(evidence.get("domain") or "whole_chart"),
        period_key=normalize_period_key(period_key),
        occurred_at=str(evidence.get("occurred_at") or ""),
        recorded_at=recorded_at,
        updated_at=str(evidence.get("updated_at") or recorded_at),
        confirmation_status=str(evidence.get("confirmation_status") or "reported"),
        severity=str(evidence.get("severity") or "unknown"),
        subjective_impact=str(evidence.get("subjective_impact") or ""),
        structured_payload=dict(evidence.get("structured_payload") or evidence),
    )


def _evidence_semantic_payload(evidence: RealityEvidence) -> dict[str, Any]:
    return {
        "summary": evidence.summary,
        "domain": evidence.domain,
        "period_key": evidence.period_key,
        "occurred_at": evidence.occurred_at,
        "confirmation_status": evidence.confirmation_status,
        "severity": evidence.severity,
        "subjective_impact": evidence.subjective_impact,
        "structured_payload": evidence.structured_payload,
    }


def _temporal_insight_for(*, life_case: LifeCase, period_key: str) -> FormalInsight | None:
    matching_priors = [
        item
        for item in life_case.temporal_priors
        if item.status == "committed" and str(item.scope.get("period_key") or "") == period_key
    ]
    if matching_priors:
        return matching_priors[-1]
    timing_insights = [
        item
        for item in life_case.domain_insights.get("life_timing", [])
        if item.status == "committed"
    ]
    return timing_insights[-1] if timing_insights else None


def _next_case_version(case_version: str) -> str:
    try:
        number = int(case_version.removeprefix("v"))
    except ValueError as exc:
        raise ValueError("unsupported_case_version") from exc
    return f"v{number + 1}"


def _version_snapshot(*, life_case: LifeCase, superseded_at: str) -> LifeCaseVersionSnapshot:
    return LifeCaseVersionSnapshot(
        snapshot_id=f"life-case-version-{uuid4().hex[:16]}",
        case_version=life_case.case_version,
        baseline_insight_id=life_case.baseline_insight.insight_id,
        domain_insight_ids=[
            item.insight_id
            for insights in life_case.domain_insights.values()
            for item in insights
            if item.status == "committed"
        ],
        temporal_snapshot_ids=[
            item.snapshot_id for item in life_case.temporal_snapshots if item.status == "active"
        ],
        reality_evidence_refs=[item.evidence_id for item in life_case.reality_evidence],
        case_revision_ids=[item.insight_id for item in life_case.case_revisions],
        created_at=life_case.updated_at,
        superseded_at=superseded_at,
    )
