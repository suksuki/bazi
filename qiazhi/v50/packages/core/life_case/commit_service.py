from __future__ import annotations
from datetime import datetime, timezone
from uuid import uuid4

from core.life_case.contracts import (
    ChartVersionRef,
    FormalInsight,
    InsightValidationReceipt,
    LifeCase,
    LifeCaseRevision,
)
from core.life_case.insight_service import validate_formal_insight
from core.life_case.relation_path import build_committed_relation_path_assertions
from core.life_case.service_support import (
    _chart_hash,
    _next_case_version,
    _require_active_life_case,
    _version_snapshot,
)
from core.mingli_agent.contracts import ChartWorldInstance


def commit_baseline_life_case(
    *,
    insight: FormalInsight,
    world: ChartWorldInstance,
    profile_id: str | None,
) -> tuple[LifeCase, InsightValidationReceipt]:
    _require_committable_status(insight)
    receipt = validate_formal_insight(insight=insight, world=world)
    if not receipt.passed:
        raise ValueError(f"formal_insight_validation_failed:{','.join(receipt.errors)}")
    now = datetime.now(timezone.utc).isoformat()
    committed = insight.model_copy(update={
        "status": "committed",
        "persistence_status": "persisted",
    })
    life_case_id = f"life-case-{uuid4().hex[:20]}"
    chart_version = ChartVersionRef(
        version_id=f"chart-version-{uuid4().hex[:16]}",
        world_id=world.world_id,
        chart_hash=_chart_hash(world),
        created_at=now,
    )
    relation_assertions, path_assertions = (
        build_committed_relation_path_assertions(
            insight=committed,
            world=world,
            life_case_id=life_case_id,
            chart_version=chart_version,
            case_version=committed.case_version,
        )
        if committed.professional_release_status == "passed"
        else ([], [])
    )
    life_case = LifeCase(
        life_case_id=life_case_id,
        case_id=insight.case_id,
        profile_id=profile_id,
        chart_version=chart_version,
        baseline_insight=committed,
        relation_assertions=relation_assertions,
        path_assertions=path_assertions,
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


def commit_domain_insight(
    *,
    life_case: LifeCase,
    insight: FormalInsight,
    world: ChartWorldInstance,
) -> tuple[LifeCase, InsightValidationReceipt]:
    _require_committable_status(insight)
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
    _require_committable_status(insight)
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
    _require_committable_status(insight)
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


def _require_committable_status(insight: FormalInsight) -> None:
    if insight.status not in {"draft", "reviewed", "validated"}:
        raise ValueError(f"formal_insight_status_not_committable:{insight.status}")
