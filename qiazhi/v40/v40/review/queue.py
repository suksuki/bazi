from __future__ import annotations

from v40.contracts.base import RoleKey, Topic
from v40.contracts.output import ProductAdviceCard, ProductVerdictCard
from v40.contracts.review import (
    AnonymizedCaseView,
    ConsentGrant,
    ConsentScope,
    PractitionerReviewDecision,
    PractitionerReviewQueueItem,
    PractitionerReviewRequest,
    PractitionerReviewResult,
)
from v40.contracts.runtime import RuntimeResult
from v40.contracts.training import LabelSource, LabelTargetType, LabelValue, TrainingLabelEvent


def build_consent_grant(
    *,
    grant_id: str,
    reading_id: str,
    granted_by_role: RoleKey = "user",
    allow_practitioner_review: bool = True,
    allow_training_use: bool = True,
    note: str = "",
) -> ConsentGrant:
    scopes = [ConsentScope.ANONYMIZED_CASE_SHARE]
    if allow_practitioner_review:
        scopes.append(ConsentScope.PRACTITIONER_REVIEW)
    if allow_training_use:
        scopes.append(ConsentScope.TRAINING_FEEDBACK)
    return ConsentGrant(
        grant_id=grant_id,
        reading_id=reading_id,
        granted_by_role=granted_by_role,
        scopes=scopes,
        allow_practitioner_review=allow_practitioner_review,
        allow_training_use=allow_training_use,
        anonymized_case_only=True,
        note=note,
    )


def build_anonymized_case_view(
    *,
    case_view_id: str,
    consent_grant: ConsentGrant,
    runtime: RuntimeResult,
    topic: Topic | None = None,
) -> AnonymizedCaseView:
    _ensure_consent_allows_review(consent_grant, runtime)
    resolved_topic = topic or runtime.request.topic
    verdict_cards = runtime.product_projection.verdict_cards if runtime.product_projection else []
    advice_cards = runtime.product_projection.advice_cards if runtime.product_projection else []
    verdict_summaries = _verdict_summaries(verdict_cards, runtime)
    advice_summaries = _advice_summaries(advice_cards, runtime)
    probe_questions = [probe.question for probe in runtime.probes[:5]]
    evidence_refs = _evidence_refs(runtime)
    source_signal_ids = [signal.signal_id for signal in (runtime.signal_registry.signals if runtime.signal_registry else [])[:12]]
    summary = verdict_summaries[0] if verdict_summaries else "本案例需要命理师复核结构判断和建议落点。"
    return AnonymizedCaseView(
        case_view_id=case_view_id,
        consent_grant_id=consent_grant.grant_id,
        reading_id=runtime.reading_id,
        topic=resolved_topic,
        summary=summary,
        verdict_summaries=verdict_summaries,
        advice_summaries=advice_summaries,
        probe_questions=probe_questions,
        evidence_refs=evidence_refs,
        source_signal_ids=source_signal_ids,
        chart_facts_included=False,
        raw_runtime_included=False,
    )


def build_practitioner_review_request(
    *,
    review_request_id: str,
    consent_grant: ConsentGrant,
    runtime: RuntimeResult,
    requested_topic: Topic | None = None,
    requested_by_role: RoleKey = "user",
    note: str = "",
) -> PractitionerReviewRequest:
    case_view = build_anonymized_case_view(
        case_view_id=f"case_view:{review_request_id}",
        consent_grant=consent_grant,
        runtime=runtime,
        topic=requested_topic,
    )
    return PractitionerReviewRequest(
        review_request_id=review_request_id,
        consent_grant_id=consent_grant.grant_id,
        reading_id=runtime.reading_id,
        requested_topic=requested_topic or runtime.request.topic,
        case_view=case_view,
        requested_by_role=requested_by_role,
        note=note,
        runtime_ref=runtime.reading_id,
    )


def build_review_queue_item(request: PractitionerReviewRequest) -> PractitionerReviewQueueItem:
    return PractitionerReviewQueueItem(
        queue_item_id=f"queue:{request.review_request_id}",
        review_request_id=request.review_request_id,
        reading_id=request.reading_id,
        topic=request.requested_topic,
        status=request.status,
        summary=request.case_view.summary,
        consent_scopes=[ConsentScope.PRACTITIONER_REVIEW, ConsentScope.ANONYMIZED_CASE_SHARE],
        assigned_to_practitioner_ref=request.assigned_to_practitioner_ref,
    )


def build_practitioner_review_result(
    *,
    result_id: str,
    review_request: PractitionerReviewRequest,
    reviewer_role: RoleKey = "practitioner",
    decision: PractitionerReviewDecision = PractitionerReviewDecision.UNSURE,
    selected_signal_ids: list[str] | None = None,
    selected_verdict_ids: list[str] | None = None,
    advice_notes: list[str] | None = None,
    probe_suggestions: list[str] | None = None,
) -> PractitionerReviewResult:
    signal_ids = selected_signal_ids or []
    verdict_ids = selected_verdict_ids or []
    notes = advice_notes or []
    probes = probe_suggestions or []
    label = _label_for_decision(decision)
    target_ids = verdict_ids or signal_ids or [review_request.review_request_id]
    target_type = LabelTargetType.VERDICT if verdict_ids else LabelTargetType.SIGNAL if signal_ids else LabelTargetType.SURFACE
    event = TrainingLabelEvent(
        event_id=f"label:review:{result_id}",
        reading_id=review_request.reading_id,
        source=LabelSource.PRACTITIONER_SELECTION,
        target_type=target_type,
        target_ids=target_ids,
        label=label,
        strength=0.72 if decision in {PractitionerReviewDecision.SUPPORTS, PractitionerReviewDecision.REVISE} else 0.52,
        confidence=0.7,
        reason=_reason_for_decision(decision, notes, probes),
        evidence_refs=review_request.case_view.evidence_refs[:8],
        created_by_role=reviewer_role,
        local_only=True,
    )
    return PractitionerReviewResult(
        result_id=result_id,
        review_request_id=review_request.review_request_id,
        reading_id=review_request.reading_id,
        reviewer_role=reviewer_role,
        decision=decision,
        selected_signal_ids=signal_ids,
        selected_verdict_ids=verdict_ids,
        advice_notes=notes,
        probe_suggestions=probes,
        training_label_events=[event],
    )


def _ensure_consent_allows_review(consent: ConsentGrant, runtime: RuntimeResult) -> None:
    if consent.reading_id != runtime.reading_id:
        raise ValueError("ConsentGrant reading_id must match runtime")
    if consent.revoked:
        raise ValueError("ConsentGrant is revoked")
    if not consent.allow_practitioner_review or ConsentScope.PRACTITIONER_REVIEW not in consent.scopes:
        raise ValueError("ConsentGrant does not allow practitioner review")
    if not consent.anonymized_case_only:
        raise ValueError("Practitioner review requires anonymized case only")


def _verdict_summaries(cards: list[ProductVerdictCard], runtime: RuntimeResult) -> list[str]:
    if cards:
        return [f"{card.title}：{card.primary_text}" for card in cards[:5]]
    return [verdict.headline for verdict in runtime.verdicts[:5]]


def _advice_summaries(cards: list[ProductAdviceCard], runtime: RuntimeResult) -> list[str]:
    if cards:
        rows = []
        for card in cards[:4]:
            points = card.action_points + card.avoid_points + card.condition_points
            rows.extend(points[:3])
        return rows
    rows = []
    for advice in runtime.advice_plans[:4]:
        rows.extend((advice.action_points + advice.avoid_points + advice.condition_points)[:3])
    return rows


def _evidence_refs(runtime: RuntimeResult) -> list[str]:
    refs: list[str] = []
    for verdict in runtime.verdicts:
        refs.extend(verdict.evidence_refs)
    for branch in runtime.branches:
        refs.extend(branch.evidence_refs)
    return list(dict.fromkeys(refs))[:12]


def _label_for_decision(decision: PractitionerReviewDecision) -> LabelValue:
    if decision == PractitionerReviewDecision.SUPPORTS:
        return LabelValue.SUPPORTS
    if decision == PractitionerReviewDecision.REVISE:
        return LabelValue.MISMATCH
    if decision == PractitionerReviewDecision.NEEDS_PROBE:
        return LabelValue.NEEDS_PROBE
    return LabelValue.PROBE_HELPFUL


def _reason_for_decision(decision: PractitionerReviewDecision, notes: list[str], probes: list[str]) -> str:
    parts = [f"命理师复核结论：{decision.value}"]
    if notes:
        parts.append("建议：" + "；".join(notes[:3]))
    if probes:
        parts.append("后续追问：" + "；".join(probes[:3]))
    return "。".join(parts)
