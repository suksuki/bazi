from __future__ import annotations
import hashlib
import json
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from core.life_case.contracts import (
    CaseRevisionCandidate,
    FormalInsight,
    LifeCase,
    LifeCaseRevision,
    MonthlyReview,
    MonthlyReviewVerdict,
    RealityEvidence,
    RealityEvidenceRevision,
    TemporalSnapshot,
)
from core.life_case.service_support import (
    _next_case_version,
    _require_active_life_case,
    _unique,
)


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
