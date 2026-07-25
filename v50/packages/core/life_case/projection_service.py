from __future__ import annotations
from typing import Any

from core.life_case.contracts import LifeCase
from core.mingli_agent.contracts import MingliCognitiveRecord


def project_life_case(life_case: LifeCase, *, role_mode: str) -> dict[str, Any]:
    baseline = life_case.baseline_insight
    _require_professionally_released_baseline(baseline)
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
    restoration. Callers are agent_api and agent_reading_projection. Retire
    after all retained cases have committed record projections and Agent reads
    consume formal Case projections directly, during Legacy read retirement.
    """

    _require_professionally_released_baseline(life_case.baseline_insight)
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


def _require_professionally_released_baseline(baseline: Any) -> None:
    if (
        baseline.status != "committed"
        or baseline.professional_review_overlay is None
        or baseline.professional_release_status not in {"passed", "partially_blocked"}
    ):
        raise ValueError("life_case_professional_release_required")
