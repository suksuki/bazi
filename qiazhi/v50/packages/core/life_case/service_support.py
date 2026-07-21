from __future__ import annotations
import hashlib
import json
from uuid import uuid4

from core.life_case.contracts import LifeCase, LifeCaseVersionSnapshot
from core.mingli_agent.contracts import ChartWorldInstance


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
