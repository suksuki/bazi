from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from v20.storage.local_jsonl import LocalJsonlStore, local_jsonl_store_from_env


ProgressCallback = Callable[[str], None]

LEDGER_NAME = "orchestrator_policy_observability_ledger"
ROLLBACK_AUDIT_LEDGER = "orchestrator_policy_rollback_audit"
ACTIVE_POINTER_RELATIVE_PATH = "training/orchestrator_policy_versions/active_pointer.json"


def build_policy_observability_training_report(
    *,
    store: LocalJsonlStore | None = None,
    observations: tuple[dict[str, object], ...] | None = None,
    progress: ProgressCallback | None = None,
) -> dict[str, object]:
    storage = store or local_jsonl_store_from_env()
    records = [] if observations is not None else _read_records(storage)
    rows = list(observations) if observations is not None else _observation_rows(records)
    audit_records = [] if observations is not None else _read_ledger_records(storage, ROLLBACK_AUDIT_LEDGER)
    _emit(progress, f"policy observability rows: {len(rows)}")
    consumer_rows = _consumer_rows(rows)
    status_counts = Counter(str(row.get("status", "")) for row in rows if row.get("status"))
    active_versions = Counter(str(row.get("active_policy_version", "")) for row in rows if row.get("active_policy_version"))
    fallback_count = sum(1 for row in rows if row.get("fallback_active"))
    candidate_consumed_count = sum(1 for row in rows if row.get("status") == "candidate_consumed")
    version_summaries = _version_summaries(rows)
    consumer_summaries = _consumer_summaries(consumer_rows)
    trend_summary = _trend_summary(
        rows=rows,
        status_counts=status_counts,
        active_versions=active_versions,
        fallback_count=fallback_count,
        candidate_consumed_count=candidate_consumed_count,
    )
    strategy_recommendations = _strategy_recommendations(
        trend_summary=trend_summary,
        version_summaries=version_summaries,
        consumer_summaries=consumer_summaries,
    )
    version_switch_timeline = _version_switch_timeline(storage=storage, audit_records=audit_records, observations=rows)
    return {
        "version": "v20.orchestrator_policy_observability_training_report.v1",
        "status": "ready" if rows else "not_enough_data",
        "ok": True,
        "ledger_name": LEDGER_NAME,
        "record_count": len(records),
        "observation_count": len(rows),
        "consumer_event_count": len(consumer_rows),
        "status_counts": dict(sorted(status_counts.items())),
        "active_policy_version_counts": dict(sorted(active_versions.items())),
        "fallback_count": fallback_count,
        "candidate_consumed_count": candidate_consumed_count,
        "candidate_consumed_ratio": round(candidate_consumed_count / len(rows), 4) if rows else 0,
        "fallback_ratio": round(fallback_count / len(rows), 4) if rows else 0,
        "version_summaries": version_summaries,
        "consumer_summaries": consumer_summaries,
        "trend_summary": trend_summary,
        "strategy_recommendations": strategy_recommendations,
        "version_switch_timeline": version_switch_timeline,
        "runtime_mutation": False,
        "guardrails": [
            "POLICY_OBSERVABILITY_TRAINING_IS_OFFLINE_ONLY",
            "NO_POLICY_WRITE_FROM_OBSERVATION",
            "NO_USER_TEXT_IN_POLICY_OBSERVABILITY",
            "ROLLBACK_POINTER_REMAINS_OPERATOR_VISIBLE",
            "TREND_SUMMARY_IS_READ_ONLY",
            "AUTO_RECOMMENDATION_DOES_NOT_BLOCK_FAST_TRACK",
            "VERSION_SWITCH_TIMELINE_IS_READ_ONLY",
        ],
    }


def write_policy_observability_training_artifact(
    *,
    store: LocalJsonlStore | None = None,
    output_dir: Path | None = None,
    progress: ProgressCallback | None = None,
) -> dict[str, object]:
    storage = store or local_jsonl_store_from_env()
    report = build_policy_observability_training_report(store=storage, progress=progress)
    directory = output_dir or storage.runtime_dir / "training" / "orchestrator_policy_observability"
    directory.mkdir(parents=True, exist_ok=True)
    latest_path = directory / "latest.json"
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_path = directory / f"orchestrator_policy_observability_{stamp}.json"
    payload = report | {
        "written_at": datetime.now(timezone.utc).isoformat(),
        "runtime_mutation": True,
    }
    latest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    run_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return {
        "version": "v20.orchestrator_policy_observability_artifact_write.v1",
        "status": "written",
        "latest_path": str(latest_path),
        "run_path": str(run_path),
        "report_status": report["status"],
        "observation_count": report["observation_count"],
        "candidate_consumed_ratio": report["candidate_consumed_ratio"],
        "fallback_ratio": report["fallback_ratio"],
        "runtime_mutation": True,
        "guardrails": [
            "LOCAL_RUNTIME_ARTIFACT_ONLY",
            "NO_POSTGRES_WRITE",
            "NO_POLICY_PROMOTION_FROM_OBSERVATION",
        ],
    }


def read_policy_observability_training_artifact(*, output_dir: Path | None = None) -> dict[str, object]:
    runtime_dir = local_jsonl_store_from_env().runtime_dir
    latest_path = (output_dir or runtime_dir / "training" / "orchestrator_policy_observability") / "latest.json"
    if not latest_path.exists():
        return {
            "version": "v20.orchestrator_policy_observability_artifact_status.v1",
            "status": "not_built",
            "latest_path": str(latest_path),
            "runtime_mutation": False,
        }
    return json.loads(latest_path.read_text(encoding="utf-8")) | {"runtime_mutation": False}


def _read_records(store: LocalJsonlStore) -> list[dict[str, object]]:
    return _read_ledger_records(store, LEDGER_NAME)


def _read_ledger_records(store: LocalJsonlStore, ledger_name: str) -> list[dict[str, object]]:
    path = store.runtime_dir / "ledger" / f"{ledger_name}.jsonl"
    if not path.exists():
        return []
    rows: list[dict[str, object]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(record, dict):
            rows.append(record)
    return rows


def _observation_rows(records: list[dict[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for record in records:
        payload = record.get("payload", {})
        if not isinstance(payload, dict):
            continue
        observation = payload.get("policy_observability", payload)
        if isinstance(observation, dict) and observation.get("version") == "v20.orchestrator_policy_observability.v1":
            rows.append(observation)
    return rows


def _consumer_rows(observations: list[dict[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for observation in observations:
        for consumer in observation.get("consumers", ()):
            if not isinstance(consumer, dict):
                continue
            rows.append({
                "active_policy_version": str(observation.get("active_policy_version", "")),
                "module_key": str(consumer.get("module_key", "")),
                "status": str(consumer.get("status", "")),
                "applied_adjustment_count": int(consumer.get("applied_adjustment_count", 0) or 0),
                "domain_boost": float(consumer.get("domain_boost", 0) or 0),
            })
    return rows


def _consumer_summaries(consumer_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    by_module: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in consumer_rows:
        by_module[str(row.get("module_key", "")) or "unknown"].append(row)
    summaries = []
    for module_key, rows in sorted(by_module.items()):
        status_counts = Counter(str(row.get("status", "")) for row in rows if row.get("status"))
        applied = int(status_counts.get("applied", 0))
        summaries.append({
            "module_key": module_key,
            "event_count": len(rows),
            "status_counts": dict(sorted(status_counts.items())),
            "applied_count": applied,
            "applied_ratio": round(applied / len(rows), 4) if rows else 0,
            "adjustment_count": sum(int(row.get("applied_adjustment_count", 0) or 0) for row in rows),
            "domain_boost_total": round(sum(float(row.get("domain_boost", 0) or 0) for row in rows), 4),
        })
    return summaries


def _version_summaries(observations: list[dict[str, object]]) -> list[dict[str, object]]:
    by_version: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in observations:
        by_version[str(row.get("active_policy_version", "")) or "unknown"].append(row)
    summaries = []
    for version, rows in sorted(by_version.items()):
        status_counts = Counter(str(row.get("status", "")) for row in rows if row.get("status"))
        fallback_count = sum(1 for row in rows if row.get("fallback_active"))
        consumed_count = int(status_counts.get("candidate_consumed", 0))
        summaries.append({
            "active_policy_version": version,
            "observation_count": len(rows),
            "status_counts": dict(sorted(status_counts.items())),
            "candidate_consumed_count": consumed_count,
            "candidate_consumed_ratio": round(consumed_count / len(rows), 4) if rows else 0,
            "fallback_count": fallback_count,
            "fallback_ratio": round(fallback_count / len(rows), 4) if rows else 0,
        })
    return summaries


def _trend_summary(
    *,
    rows: list[dict[str, object]],
    status_counts: Counter[str],
    active_versions: Counter[str],
    fallback_count: int,
    candidate_consumed_count: int,
) -> dict[str, object]:
    observation_count = len(rows)
    dominant_version = active_versions.most_common(1)[0][0] if active_versions else ""
    dominant_status = status_counts.most_common(1)[0][0] if status_counts else ""
    candidate_ratio = round(candidate_consumed_count / observation_count, 4) if observation_count else 0
    fallback_ratio = round(fallback_count / observation_count, 4) if observation_count else 0
    if not observation_count:
        trend_status = "not_enough_data"
    elif fallback_ratio >= 0.5:
        trend_status = "fallback_pressure"
    elif candidate_ratio >= 0.66:
        trend_status = "candidate_effective"
    else:
        trend_status = "mixed_signal"
    return {
        "version": "v20.orchestrator_policy_observability_trend_summary.v1",
        "status": trend_status,
        "observation_count": observation_count,
        "dominant_active_policy_version": dominant_version,
        "dominant_status": dominant_status,
        "candidate_consumed_ratio": candidate_ratio,
        "fallback_ratio": fallback_ratio,
        "runtime_mutation": False,
        "guardrails": [
            "TREND_SUMMARY_IS_READ_ONLY",
            "NO_POLICY_WRITE_FROM_TREND",
            "NO_HUMAN_APPROVAL_GATE_REQUIRED",
        ],
    }


def _strategy_recommendations(
    *,
    trend_summary: dict[str, object],
    version_summaries: list[dict[str, object]],
    consumer_summaries: list[dict[str, object]],
) -> list[dict[str, object]]:
    recommendations: list[dict[str, object]] = []
    observation_count = int(trend_summary.get("observation_count", 0) or 0)
    fallback_ratio = float(trend_summary.get("fallback_ratio", 0) or 0)
    candidate_ratio = float(trend_summary.get("candidate_consumed_ratio", 0) or 0)
    if not observation_count:
        recommendations.append(_recommendation(
            key="collect_policy_observations",
            recommendation_type="data_collection",
            suggested_action="继续写入策略观测样本",
            reason="当前策略观测样本不足，无法形成稳定趋势。",
        ))
        return recommendations
    if candidate_ratio >= 0.66:
        recommendations.append(_recommendation(
            key="keep_fast_track_candidate_active",
            recommendation_type="promotion_signal",
            suggested_action="保持 latest candidate 为 active policy",
            reason="候选策略消费率较高，主线仲裁和问题聚焦已稳定消费候选权重。",
        ))
    if fallback_ratio >= 0.5:
        recommendations.append(_recommendation(
            key="inspect_fallback_pressure",
            recommendation_type="rollback_watch",
            suggested_action="保留 baseline 回滚指针并检查候选覆盖面",
            reason="fallback 占比偏高，说明 active policy 未被稳定消费或仍有模块未命中。",
        ))
    for row in consumer_summaries:
        applied_ratio = float(row.get("applied_ratio", 0) or 0)
        event_count = int(row.get("event_count", 0) or 0)
        module_key = str(row.get("module_key", "") or "unknown")
        if event_count >= 2 and applied_ratio < 0.5:
            recommendations.append(_recommendation(
                key=f"expand_{module_key}_coverage",
                recommendation_type="coverage_signal",
                suggested_action=f"扩大 {module_key} 的策略匹配覆盖",
                reason=f"{module_key} 的策略应用率偏低，当前为 {round(applied_ratio * 100)}%。",
            ))
    if not recommendations:
        recommendations.append(_recommendation(
            key="continue_fast_track_observation",
            recommendation_type="steady_state",
            suggested_action="继续按 fast-track 运行并积累跨版本观测",
            reason="当前策略消费与 fallback 没有明显异常，适合继续自动迭代。",
        ))
    return recommendations[:6]


def _version_switch_timeline(
    *,
    storage: LocalJsonlStore,
    audit_records: list[dict[str, object]],
    observations: list[dict[str, object]],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for record in audit_records:
        payload = record.get("payload", {})
        if not isinstance(payload, dict):
            continue
        event_version = str(payload.get("version", ""))
        if event_version not in {"v20.orchestrator_policy_rollback_audit.v1", "v20.orchestrator_policy_activation_audit.v1"}:
            continue
        rows.append({
            "event_type": "activate_latest_candidate" if "activation" in event_version else "rollback_to_baseline",
            "created_at": str(record.get("created_at", "")),
            "active_policy_version": str(payload.get("active_policy_version", "")),
            "candidate_policy_version": str(payload.get("candidate_policy_version", "")),
            "previous_active_policy_version": str(payload.get("previous_active_policy_version", "")),
            "rollback_policy_version": str(payload.get("rollback_policy_version", "")),
            "source_role": str(payload.get("source_role", "")),
            "reason": str(payload.get("reason", "")),
            "runtime_mutation": False,
            "guardrails": ["TIMELINE_READS_APPEND_ONLY_AUDIT"],
        })
    pointer = _read_active_pointer(storage)
    if pointer:
        rows.append({
            "event_type": "current_active_pointer",
            "created_at": str(pointer.get("written_at", "")),
            "active_policy_version": str(pointer.get("active_policy_version", "")),
            "candidate_policy_version": str(pointer.get("candidate_policy_version", "")),
            "previous_active_policy_version": str(pointer.get("previous_active_policy_version", "")),
            "rollback_policy_version": str(pointer.get("rollback_policy_version", "")),
            "source_role": str(pointer.get("source_role", "")),
            "reason": str(pointer.get("reason", "")),
            "runtime_mutation": False,
            "guardrails": ["TIMELINE_READS_ACTIVE_POINTER"],
        })
    if not rows and observations:
        latest_observation = observations[-1]
        rows.append({
            "event_type": "latest_observed_active_policy",
            "created_at": "",
            "active_policy_version": str(latest_observation.get("active_policy_version", "")),
            "candidate_policy_version": str(latest_observation.get("candidate_policy_version", "")),
            "previous_active_policy_version": "",
            "rollback_policy_version": str(latest_observation.get("rollback_policy_version", "")),
            "source_role": "runtime_observation",
            "reason": "latest policy observation without pointer audit",
            "runtime_mutation": False,
            "guardrails": ["TIMELINE_FALLS_BACK_TO_OBSERVATION"],
        })
    return sorted(rows, key=lambda row: str(row.get("created_at", "")), reverse=True)[:12]


def _read_active_pointer(storage: LocalJsonlStore) -> dict[str, object]:
    path = storage.runtime_dir / ACTIVE_POINTER_RELATIVE_PATH
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    if not isinstance(payload, dict):
        return {}
    if payload.get("version") != "v20.orchestrator_runtime_active_pointer.v1":
        return {}
    return payload


def _recommendation(
    *,
    key: str,
    recommendation_type: str,
    suggested_action: str,
    reason: str,
) -> dict[str, object]:
    return {
        "recommendation_key": key,
        "recommendation_type": recommendation_type,
        "suggested_action": suggested_action,
        "reason": reason,
        "runtime_allowed": True,
        "runtime_mutation": False,
        "guardrails": [
            "AUTO_RECOMMENDATION_IS_READ_ONLY",
            "NO_POLICY_WRITE_FROM_RECOMMENDATION",
            "FAST_TRACK_REMAINS_OPERATOR_ROLLBACKABLE",
        ],
    }


def _emit(progress: ProgressCallback | None, message: str) -> None:
    if progress is not None:
        progress(message)
