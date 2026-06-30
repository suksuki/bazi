from __future__ import annotations

from v40.migration.v30_export import V30ExportEnvelope
from v40.contracts.base import AssertionLevel, Polarity, RoleKey, Topic
from v40.contracts.decision import AdvicePlan, DecisionVerdict
from v40.contracts.runtime import RuntimeRequest, RuntimeResult
from v40.contracts.signal import RuntimeSignal, SignalRegistrySnapshot, SignalSource
from v40.presentation import build_product_projection


def build_runtime_from_v30_export(
    envelope: V30ExportEnvelope,
    *,
    role_key: RoleKey = "user",
) -> RuntimeResult:
    reading_id = f"{envelope.reading_id}:v40-shadow"
    request = RuntimeRequest(
        request_id=f"request:{envelope.export_id}",
        reading_id=reading_id,
        role_key=role_key,
        imported_case_ref=envelope.export_id,
        user_question=_first_text(envelope.verdict_rows, "user_question"),
        topic=_topic_from_rows(envelope.verdict_rows + envelope.signal_rows),
    )
    signals = adapt_signals(envelope, target_reading_id=reading_id)
    registry = SignalRegistrySnapshot(
        registry_id=f"registry:{envelope.export_id}",
        reading_id=reading_id,
        signals=signals,
    )
    verdicts = adapt_verdicts(envelope, target_reading_id=reading_id)
    advice_plans = adapt_advice(envelope, target_reading_id=reading_id, verdicts=verdicts)
    product_projection = build_product_projection(
        reading_id=reading_id,
        role_key=role_key,
        verdicts=verdicts,
        advice_plans=advice_plans,
    )
    return RuntimeResult(
        reading_id=reading_id,
        request=request,
        signal_registry=registry,
        verdicts=verdicts,
        advice_plans=advice_plans,
        product_projection=product_projection,
    )


def adapt_signals(envelope: V30ExportEnvelope, *, target_reading_id: str) -> list[RuntimeSignal]:
    rows = [*envelope.signal_rows, *_feature_rows_as_signals(envelope.feature_rows)]
    signals: list[RuntimeSignal] = []
    seen: set[str] = set()
    for index, row in enumerate(rows, start=1):
        signal_id = str(row.get("signal_id") or row.get("id") or f"v30-signal:{index}")
        if signal_id in seen:
            signal_id = f"{signal_id}:{index}"
        seen.add(signal_id)
        claim = str(row.get("claim") or row.get("statement") or row.get("text") or row.get("label") or "").strip()
        if not claim:
            continue
        signals.append(
            RuntimeSignal(
                signal_id=signal_id,
                reading_id=target_reading_id,
                source=_signal_source(row),
                source_ref=str(row.get("source_ref") or row.get("source_module") or row.get("source_type") or ""),
                topic=_topic(str(row.get("topic") or row.get("domain") or row.get("stage") or "")),
                claim=claim,
                claim_key=str(row.get("claim_key") or row.get("key") or ""),
                polarity=_polarity(str(row.get("polarity") or "")),
                strength=_bounded_float(row.get("strength") or row.get("score") or row.get("weight"), default=0.5),
                confidence=_bounded_float(row.get("confidence"), default=0.5),
                assertion_hint=_assertion_level(str(row.get("assertion_level_hint") or row.get("assertion_level") or "")),
                evidence_refs=_string_list(row.get("evidence_refs") or row.get("evidence_ids")),
                counter_evidence_refs=_string_list(row.get("counter_evidence_refs") or row.get("counter_evidence_ids")),
                branch_group_id=str(row.get("branch_group_id") or ""),
                role_visibility=_role_visibility(row.get("role_visibility")),
                trainable_targets=_string_list(row.get("training_targets") or row.get("trainable_targets")),
            )
        )
    return signals


def adapt_verdicts(envelope: V30ExportEnvelope, *, target_reading_id: str) -> list[DecisionVerdict]:
    verdicts: list[DecisionVerdict] = []
    for index, row in enumerate(envelope.verdict_rows, start=1):
        headline = str(row.get("headline") or row.get("title") or row.get("primary_text") or "").strip()
        if not headline:
            continue
        evidence_refs = _string_list(row.get("evidence_refs") or row.get("evidence_ids"))
        level = _assertion_level(str(row.get("assertion_level") or ""))
        if level in {AssertionLevel.CONFIRMED, AssertionLevel.SUPPORTED} and not evidence_refs:
            level = AssertionLevel.WEAK_CANDIDATE
        verdicts.append(
            DecisionVerdict(
                verdict_id=str(row.get("verdict_id") or row.get("id") or f"v40-verdict:{index}"),
                reading_id=target_reading_id,
                topic=_topic(str(row.get("topic") or row.get("domain") or "")),
                headline=headline,
                assertion_level=level,
                confidence=_bounded_float(row.get("confidence"), default=0.5),
                allowed_assertions=_string_list(row.get("allowed_assertions") or row.get("allowed_user_text")),
                forbidden_assertions=_string_list(row.get("forbidden_assertions")),
                evidence_refs=evidence_refs,
                counter_evidence_refs=_string_list(row.get("counter_evidence_refs") or row.get("counter_evidence_ids")),
                primary_branch_id=str(row.get("primary_branch_id") or ""),
                alternative_branch_ids=_string_list(row.get("alternative_branch_ids")),
                next_probe_ids=_string_list(row.get("next_probe_ids") or row.get("next_question_slots")),
            )
        )
    return verdicts


def adapt_advice(
    envelope: V30ExportEnvelope,
    *,
    target_reading_id: str,
    verdicts: list[DecisionVerdict],
) -> list[AdvicePlan]:
    verdict_ids = [verdict.verdict_id for verdict in verdicts]
    fallback_verdict_id = verdict_ids[0] if verdict_ids else "unbound-v30-verdict"
    plans: list[AdvicePlan] = []
    for index, row in enumerate(envelope.advice_rows, start=1):
        action_points = _string_list(row.get("action_points") or row.get("advice_points") or row.get("actions"))
        avoid_points = _string_list(row.get("avoid_points") or row.get("avoid"))
        condition_points = _string_list(row.get("condition_points") or row.get("conditions"))
        if not (action_points or avoid_points or condition_points):
            text = str(row.get("text") or row.get("advice") or "").strip()
            action_points = [text] if text else []
        if not (action_points or avoid_points or condition_points):
            continue
        source_verdict_ids = [
            verdict_id for verdict_id in _string_list(row.get("source_verdict_ids") or row.get("verdict_ids"))
            if verdict_id in set(verdict_ids)
        ] or [fallback_verdict_id]
        plans.append(
            AdvicePlan(
                advice_id=str(row.get("advice_id") or row.get("id") or f"v40-advice:{index}"),
                reading_id=target_reading_id,
                topic=_topic(str(row.get("topic") or row.get("domain") or "")),
                source_verdict_ids=source_verdict_ids,
                action_points=action_points,
                avoid_points=avoid_points,
                condition_points=condition_points,
                priority=_bounded_float(row.get("priority"), default=0.5),
                evidence_refs=_string_list(row.get("evidence_refs") or row.get("evidence_ids")),
            )
        )
    if plans or not verdicts:
        return plans
    for verdict in verdicts:
        points = [text for text in verdict.allowed_assertions[:1] if text] or [verdict.headline]
        plans.append(
            AdvicePlan(
                advice_id=f"advice:{verdict.verdict_id}",
                reading_id=target_reading_id,
                topic=verdict.topic,
                source_verdict_ids=[verdict.verdict_id],
                action_points=points,
                priority=verdict.confidence,
                evidence_refs=verdict.evidence_refs,
            )
        )
    return plans


def _feature_rows_as_signals(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    converted: list[dict[str, object]] = []
    for row in rows:
        converted.append(
            {
                **row,
                "signal_id": row.get("signal_id") or row.get("feature_id") or row.get("id"),
                "source_type": row.get("source_type") or "feature_evidence",
                "claim": row.get("claim") or row.get("statement") or row.get("label"),
            }
        )
    return converted


def _signal_source(row: dict[str, object]) -> SignalSource:
    raw = " ".join(
        str(row.get(key) or "")
        for key in ("source", "source_type", "source_module", "engine")
    ).lower()
    if "ziwei" in raw:
        return SignalSource.ZIWEI_ENGINE
    if "reality" in raw or "probe" in raw:
        return SignalSource.REALITY_PROBE
    if "practitioner" in raw:
        return SignalSource.PRACTITIONER_FEEDBACK
    if "user" in raw:
        return SignalSource.USER_FEEDBACK
    if "golden" in raw:
        return SignalSource.GOLDEN_CASE
    if "llm" in raw:
        return SignalSource.LLM_HYPOTHESIS
    return SignalSource.BAZI_ENGINE


def _topic(value: str) -> Topic:
    normalized = value.strip().lower()
    aliases = {
        "career": Topic.CAREER,
        "事业": Topic.CAREER,
        "wealth": Topic.WEALTH,
        "财运": Topic.WEALTH,
        "relationship": Topic.RELATIONSHIP,
        "感情": Topic.RELATIONSHIP,
        "health": Topic.HEALTH,
        "健康": Topic.HEALTH,
        "timing": Topic.TIMING,
        "时运": Topic.TIMING,
        "structure": Topic.STRUCTURE,
        "结构": Topic.STRUCTURE,
        "useful_god": Topic.USEFUL_GOD,
        "用神": Topic.USEFUL_GOD,
        "hidden_factor": Topic.HIDDEN_ATTRIBUTE,
        "hidden_attribute": Topic.HIDDEN_ATTRIBUTE,
        "隐藏线索": Topic.HIDDEN_ATTRIBUTE,
        "advice": Topic.ADVICE,
        "建议": Topic.ADVICE,
        "overview": Topic.OVERVIEW,
        "整体": Topic.OVERVIEW,
    }
    return aliases.get(normalized, Topic.UNKNOWN)


def _topic_from_rows(rows: list[dict[str, object]]) -> Topic:
    for row in rows:
        topic = _topic(str(row.get("topic") or row.get("domain") or ""))
        if topic != Topic.UNKNOWN:
            return topic
    return Topic.OVERVIEW


def _polarity(value: str) -> Polarity:
    normalized = value.strip().lower()
    if normalized in {"support", "supports", "positive", "正向"}:
        return Polarity.SUPPORT
    if normalized in {"oppose", "opposes", "negative", "反向"}:
        return Polarity.OPPOSE
    if normalized in {"mixed", "分支", "混合"}:
        return Polarity.MIXED
    return Polarity.NEUTRAL


def _assertion_level(value: str) -> AssertionLevel:
    normalized = value.strip().lower()
    for level in AssertionLevel:
        if normalized == level.value:
            return level
    return AssertionLevel.WEAK_CANDIDATE


def _role_visibility(value: object) -> list[RoleKey]:
    allowed = {"guest", "user", "practitioner", "analyst", "admin", "lab"}
    if isinstance(value, list):
        rows = [str(row) for row in value if str(row) in allowed]
        if rows:
            return rows  # type: ignore[return-value]
    return ["user", "practitioner", "admin"]


def _string_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(row) for row in value if str(row)]
    if isinstance(value, tuple):
        return [str(row) for row in value if str(row)]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def _bounded_float(value: object, *, default: float = 0.0) -> float:
    try:
        return max(0.0, min(1.0, float(value)))
    except (TypeError, ValueError):
        return default


def _first_text(rows: list[dict[str, object]], key: str) -> str:
    for row in rows:
        value = str(row.get(key) or "").strip()
        if value:
            return value
    return ""
