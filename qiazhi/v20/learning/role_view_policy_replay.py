from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from v20.learning.role_view_policy_candidates import (
    BASELINE_POLICY_VERSION,
    build_role_view_policy_candidate_report,
)
from v20.storage.local_jsonl import LocalJsonlStore, local_jsonl_store_from_env


def build_role_view_policy_replay_report(
    *,
    policy_candidate_report: dict[str, object] | None = None,
    store: LocalJsonlStore | None = None,
) -> dict[str, object]:
    candidate = policy_candidate_report or build_role_view_policy_candidate_report(store=store)
    comparisons = _comparisons(candidate)
    ab_test_summary = _ab_test_summary(comparisons)
    return {
        "version": "v20.role_view_policy_replay_report.v1",
        "status": "ready_for_review" if comparisons else "not_enough_data",
        "baseline_policy_version": candidate.get("baseline_policy_version", BASELINE_POLICY_VERSION),
        "candidate_policy_version": candidate.get("candidate_policy_version", ""),
        "source_candidate_count": candidate.get("candidate_count", 0),
        "comparison_count": len(comparisons),
        "comparisons": comparisons,
        "ab_test_summary": ab_test_summary,
        "impact_summary": _impact_summary(comparisons),
        "replay_result": _replay_result(comparisons, ab_test_summary),
        "runtime_mutation": False,
        "guardrails": [
            "ROLE_VIEW_REPLAY_IS_POLICY_DIFF_ONLY",
            "ROLE_VIEW_AB_REPLAY_IS_OFFLINE_ONLY",
            "NO_RUNTIME_ROLE_VIEW_POLICY_MUTATION",
            "NO_CHART_FACT_MUTATION",
            "RUNTIME_POINTER_NOT_ENABLED_FOR_ROLE_VIEW_POLICY",
        ],
    }


def write_role_view_policy_replay_artifact(
    *,
    store: LocalJsonlStore | None = None,
    output_dir: Path | None = None,
) -> dict[str, object]:
    storage = store or local_jsonl_store_from_env()
    report = build_role_view_policy_replay_report(store=storage)
    directory = output_dir or storage.runtime_dir / "training" / "role_view_policy_replay"
    directory.mkdir(parents=True, exist_ok=True)
    latest_path = directory / "latest.json"
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_path = directory / f"role_view_policy_replay_{stamp}.json"
    payload = report | {
        "written_at": datetime.now(timezone.utc).isoformat(),
        "runtime_mutation": True,
    }
    latest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    run_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return {
        "version": "v20.role_view_policy_replay_artifact_write.v1",
        "status": "written",
        "latest_path": str(latest_path),
        "run_path": str(run_path),
        "report_status": report["status"],
        "comparison_count": report["comparison_count"],
        "runtime_mutation": True,
        "guardrails": [
            "LOCAL_RUNTIME_ARTIFACT_ONLY",
            "NO_POSTGRES_WRITE",
            "NO_RUNTIME_POLICY_PROMOTION",
        ],
    }


def read_role_view_policy_replay_artifact(*, output_dir: Path | None = None) -> dict[str, object]:
    runtime_dir = local_jsonl_store_from_env().runtime_dir
    latest_path = (output_dir or runtime_dir / "training" / "role_view_policy_replay") / "latest.json"
    if not latest_path.exists():
        return {
            "version": "v20.role_view_policy_replay_artifact_status.v1",
            "status": "not_built",
            "latest_path": str(latest_path),
            "runtime_mutation": False,
        }
    return json.loads(latest_path.read_text(encoding="utf-8")) | {"runtime_mutation": False}


def _comparisons(candidate: dict[str, object]) -> list[dict[str, object]]:
    payload = candidate.get("policy_payload", {})
    if not isinstance(payload, dict):
        return []
    rows: list[dict[str, object]] = []
    policy_map = {
        "question_limit_policy": "may_change_role_question_count_after_pointer",
        "group_boost_policy": "may_change_role_question_group_priority_after_pointer",
        "domain_boost_policy": "may_change_role_question_domain_priority_after_pointer",
        "strategy_boost_policy": "may_change_role_question_strategy_priority_after_pointer",
        "seed_fit_policy": "may_change_role_seed_question_priority_after_pointer",
        "reward_policy": "may_change_question_priority_from_interaction_reward_after_pointer",
    }
    for policy_key, effect in policy_map.items():
        policy_rows = payload.get(policy_key, ())
        if not isinstance(policy_rows, list):
            continue
        for row in policy_rows:
            if not isinstance(row, dict):
                continue
            rows.append({
                "policy_key": policy_key,
                "candidate_id": row.get("candidate_id", ""),
                "source_role": row.get("source_role", ""),
                "baseline_action": "keep_current_role_view_policy",
                "candidate_action": row.get("suggested_action", ""),
                "expected_effect": effect,
                "ab_variant": "candidate",
                "baseline_score": 0.0,
                "basis": row.get("basis", ""),
                "offline_score": _offline_score(row),
                "score_reason": _score_reason(row),
                "requires_replay_review": True,
                "runtime_allowed": False,
            })
    return rows


def _replay_result(comparisons: list[dict[str, object]], ab_test_summary: dict[str, object]) -> dict[str, object]:
    positive = sum(1 for row in comparisons if float(row.get("offline_score", 0.0) or 0.0) > 0)
    negative = sum(1 for row in comparisons if float(row.get("offline_score", 0.0) or 0.0) < 0)
    return {
        "status": "review_required" if comparisons else "no_candidate_policy",
        "eligible_for_runtime": False,
        "blocking_gate": "role_view_runtime_pointer_not_enabled",
        "comparison_count": len(comparisons),
        "positive_score_count": positive,
        "negative_score_count": negative,
        "ab_candidate_win": ab_test_summary.get("candidate_win", False),
        "ab_net_lift": ab_test_summary.get("net_lift", 0.0),
        "ab_risk_count": ab_test_summary.get("risk_count", 0),
    }


def _impact_summary(comparisons: list[dict[str, object]]) -> dict[str, object]:
    by_policy_key: dict[str, int] = {}
    by_source_role: dict[str, int] = {}
    by_expected_effect: dict[str, int] = {}
    score_total = 0.0
    for row in comparisons:
        policy_key = str(row.get("policy_key", "")) or "unknown"
        source_role = str(row.get("source_role", "")) or "unknown"
        expected_effect = str(row.get("expected_effect", "")) or "unknown"
        by_policy_key[policy_key] = by_policy_key.get(policy_key, 0) + 1
        by_source_role[source_role] = by_source_role.get(source_role, 0) + 1
        by_expected_effect[expected_effect] = by_expected_effect.get(expected_effect, 0) + 1
        score_total += float(row.get("offline_score", 0.0) or 0.0)
    return {
        "version": "v20.role_view_policy_replay_impact_summary.v1",
        "comparison_count": len(comparisons),
        "offline_score_total": round(score_total, 3),
        "offline_score_average": round(score_total / max(1, len(comparisons)), 3),
        "by_policy_key": dict(sorted(by_policy_key.items())),
        "by_source_role": dict(sorted(by_source_role.items())),
        "by_expected_effect": dict(sorted(by_expected_effect.items())),
        "runtime_allowed": False,
    }


def _ab_test_summary(comparisons: list[dict[str, object]]) -> dict[str, object]:
    by_role: dict[str, dict[str, object]] = {}
    by_policy_key: dict[str, dict[str, object]] = {}
    net_lift = 0.0
    risk_count = 0
    for row in comparisons:
        score = float(row.get("offline_score", 0.0) or 0.0)
        role = str(row.get("source_role", "")) or "unknown"
        policy_key = str(row.get("policy_key", "")) or "unknown"
        net_lift += score
        if score < 0:
            risk_count += 1
        _add_ab_bucket(by_role, role, score)
        _add_ab_bucket(by_policy_key, policy_key, score)
    candidate_count = len(comparisons)
    average_lift = round(net_lift / max(1, candidate_count), 3)
    return {
        "version": "v20.role_view_policy_ab_replay_summary.v1",
        "baseline_variant": "baseline_keep_current_role_view_policy",
        "candidate_variant": "candidate_apply_role_view_policy_payload",
        "candidate_count": candidate_count,
        "baseline_score_total": 0.0,
        "candidate_score_total": round(net_lift, 3),
        "net_lift": round(net_lift, 3),
        "average_lift": average_lift,
        "candidate_win": bool(candidate_count and net_lift > 0 and risk_count == 0),
        "risk_count": risk_count,
        "by_role": _finalize_ab_buckets(by_role),
        "by_policy_key": _finalize_ab_buckets(by_policy_key),
        "runtime_allowed": False,
        "guardrails": [
            "AB_REPLAY_IS_OFFLINE_ONLY",
            "AB_REPLAY_DOES_NOT_PROMOTE_POLICY",
            "AB_REPLAY_DOES_NOT_CHANGE_CHART_FACTS",
        ],
    }


def _add_ab_bucket(target: dict[str, dict[str, object]], key: str, score: float) -> None:
    row = target.setdefault(key, {"comparison_count": 0, "candidate_score_total": 0.0, "risk_count": 0})
    row["comparison_count"] = int(row["comparison_count"]) + 1
    row["candidate_score_total"] = float(row["candidate_score_total"]) + score
    if score < 0:
        row["risk_count"] = int(row["risk_count"]) + 1


def _finalize_ab_buckets(buckets: dict[str, dict[str, object]]) -> dict[str, dict[str, object]]:
    finalized: dict[str, dict[str, object]] = {}
    for key, row in sorted(buckets.items()):
        count = int(row.get("comparison_count", 0) or 0)
        total = round(float(row.get("candidate_score_total", 0.0) or 0.0), 3)
        finalized[key] = {
            "comparison_count": count,
            "baseline_score_total": 0.0,
            "candidate_score_total": total,
            "net_lift": total,
            "average_lift": round(total / max(1, count), 3),
            "risk_count": int(row.get("risk_count", 0) or 0),
        }
    return finalized


def _offline_score(row: dict[str, object]) -> float:
    action = str(row.get("suggested_action", ""))
    if action == "boost_question_candidate":
        return 1.0
    if action == "suppress_question_candidate":
        return -1.0
    if action == "keep_collecting_reward":
        return 0.0
    if action.startswith("consider_") or action in {"review_seed_question_fit", "review_question_limit_and_ordering"}:
        return 0.25
    return 0.0


def _score_reason(row: dict[str, object]) -> str:
    action = str(row.get("suggested_action", ""))
    if action == "boost_question_candidate":
        return "positive_interaction_reward_candidate"
    if action == "suppress_question_candidate":
        return "negative_interaction_reward_candidate"
    if action == "keep_collecting_reward":
        return "insufficient_reward_margin"
    return "structural_candidate_requires_replay"
