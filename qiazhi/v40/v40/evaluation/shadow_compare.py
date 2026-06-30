from __future__ import annotations

from collections import Counter

from v40.contracts.base import ReleaseRecommendation, Topic
from v40.contracts.evaluation import ShadowCompareBatchSummary, ShadowCompareResult
from v40.contracts.runtime import RuntimeResult
from v40.migration.v30_export import V30ExportEnvelope


def build_shadow_compare_result(
    *,
    compare_id: str,
    envelope: V30ExportEnvelope,
    runtime_result: RuntimeResult,
) -> ShadowCompareResult:
    v30_topics = _topics_from_rows(envelope.verdict_rows)
    v40_topics = {verdict.topic for verdict in runtime_result.verdicts}
    overlap = len(v30_topics & v40_topics)
    topic_union_count = len(v30_topics | v40_topics)
    verdict_overlap = (overlap / topic_union_count) if topic_union_count else 1.0
    v30_signal_count = len(envelope.signal_rows) + len(envelope.feature_rows)
    v40_signal_count = len(runtime_result.signal_registry.signals) if runtime_result.signal_registry else 0
    import_coverage = _coverage(v40_signal_count, v30_signal_count)
    v30_verdict_count = len(envelope.verdict_rows)
    v40_verdict_count = len(runtime_result.verdicts)
    v30_advice_count = len(envelope.advice_rows)
    v40_advice_count = len(runtime_result.advice_plans)
    product_ready = bool(
        runtime_result.product_projection
        and runtime_result.product_projection.verdict_cards
        and runtime_result.product_projection.leakage_scan_passed
    )
    failures: list[str] = []
    if v30_signal_count and not v40_signal_count:
        failures.append("signals_missing_after_importer")
    if v30_verdict_count and not v40_verdict_count:
        failures.append("verdicts_missing_after_importer")
    if v30_advice_count and not v40_advice_count:
        failures.append("advice_missing_after_importer")
    if v30_verdict_count and verdict_overlap < 0.5:
        failures.append("verdict_topic_overlap_low")
    if not product_ready:
        failures.append("product_projection_not_ready")
    regression = bool(failures)
    return ShadowCompareResult(
        compare_id=compare_id,
        v30_export_id=envelope.export_id,
        v40_reading_id=runtime_result.reading_id,
        v30_signal_count=v30_signal_count,
        v40_signal_count=v40_signal_count,
        v30_verdict_count=v30_verdict_count,
        v40_verdict_count=v40_verdict_count,
        v30_advice_count=v30_advice_count,
        v40_advice_count=v40_advice_count,
        import_coverage_rate=import_coverage,
        verdict_topic_overlap_rate=verdict_overlap,
        product_projection_ready=product_ready,
        leakage_free=bool(runtime_result.product_projection and runtime_result.product_projection.leakage_scan_passed),
        regression_detected=regression,
        failed_reasons=failures,
        recommendation=ReleaseRecommendation.NEEDS_REVIEW,
    )


def build_shadow_compare_batch_summary(
    *,
    batch_id: str,
    compares: list[ShadowCompareResult],
) -> ShadowCompareBatchSummary:
    reason_counts: Counter[str] = Counter()
    for compare in compares:
        reason_counts.update(compare.failed_reasons)
        if compare.import_coverage_rate < 0.9:
            reason_counts["import_coverage_low"] += 1
        if compare.verdict_topic_overlap_rate < 0.8:
            reason_counts["verdict_topic_overlap_low"] += 1
        if not compare.product_projection_ready:
            reason_counts["product_projection_not_ready"] += 1
        if not compare.leakage_free:
            reason_counts["leakage_not_free"] += 1

    passed_count = sum(1 for compare in compares if _shadow_compare_passed(compare))
    regression_count = sum(1 for compare in compares if compare.regression_detected)
    review_count = len(compares) - passed_count - regression_count
    average_import = _average([compare.import_coverage_rate for compare in compares])
    average_overlap = _average([compare.verdict_topic_overlap_rate for compare in compares])
    product_ready_rate = _average([1.0 if compare.product_projection_ready else 0.0 for compare in compares])
    recommendation = ReleaseRecommendation.NEEDS_REVIEW
    if regression_count:
        recommendation = ReleaseRecommendation.REJECT
    elif compares and passed_count == len(compares) and not reason_counts:
        recommendation = ReleaseRecommendation.APPROVE
    return ShadowCompareBatchSummary(
        batch_id=batch_id,
        compare_count=len(compares),
        compare_ids=[compare.compare_id for compare in compares],
        passed_count=passed_count,
        review_count=review_count,
        regression_count=regression_count,
        average_import_coverage_rate=average_import,
        average_verdict_topic_overlap_rate=average_overlap,
        product_projection_ready_rate=product_ready_rate,
        failed_reason_counts=dict(sorted(reason_counts.items())),
        recommendation=recommendation,
    )


def _topics_from_rows(rows: list[dict[str, object]]) -> set[Topic]:
    topics: set[Topic] = set()
    for row in rows:
        raw = str(row.get("topic") or row.get("domain") or "").strip().lower()
        for topic in Topic:
            if raw == topic.value:
                topics.add(topic)
                break
    return topics


def _coverage(converted_count: int, source_count: int) -> float:
    if source_count <= 0:
        return 1.0
    return max(0.0, min(1.0, converted_count / source_count))


def _shadow_compare_passed(compare: ShadowCompareResult) -> bool:
    return (
        not compare.regression_detected
        and compare.import_coverage_rate >= 0.9
        and compare.verdict_topic_overlap_rate >= 0.8
        and compare.product_projection_ready
        and compare.leakage_free
    )


def _average(values: list[float]) -> float:
    if not values:
        return 0.0
    return round(sum(values) / len(values), 4)
