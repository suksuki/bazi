from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from v20.storage.local_jsonl import LocalJsonlStore, local_jsonl_store_from_env


LEDGER_NAME = "role_question_click_ledger"
MIN_POLICY_SAMPLES = 3


def build_role_question_click_training_report(
    *,
    store: LocalJsonlStore | None = None,
    clicks: tuple[dict[str, object], ...] | None = None,
) -> dict[str, object]:
    storage = store or local_jsonl_store_from_env()
    records = [] if clicks is not None else _read_records(storage)
    rows = list(clicks) if clicks is not None else _click_rows(records)
    role_summaries = _role_summaries(rows)
    group_summaries = _group_summaries(rows)
    domain_summaries = _domain_summaries(rows)
    strategy_summaries = _strategy_summaries(rows)
    seed_summaries = _seed_summaries(rows)
    next_question_atom_summaries = _next_question_atom_summaries(rows)
    action_summaries = _action_summaries(rows)
    reward_summaries = _reward_summaries(rows)
    recommendations = _recommendations(
        role_summaries,
        group_summaries,
        domain_summaries,
        strategy_summaries,
        seed_summaries,
        reward_summaries,
    )
    return {
        "version": "v20.role_question_click_training_report.v1",
        "status": "ready" if rows else "not_enough_data",
        "ok": True,
        "ledger_name": LEDGER_NAME,
        "record_count": len(records),
        "click_count": len(rows),
        "role_summaries": role_summaries,
        "group_summaries": group_summaries,
        "domain_summaries": domain_summaries,
        "strategy_summaries": strategy_summaries,
        "seed_summaries": seed_summaries,
        "next_question_atom_summaries": next_question_atom_summaries,
        "action_summaries": action_summaries,
        "reward_summaries": reward_summaries,
        "next_question_feedback_policy": _next_question_feedback_policy(next_question_atom_summaries),
        "recommendations": recommendations,
        "activation_thresholds": {
            "min_policy_samples": MIN_POLICY_SAMPLES,
        },
        "training_targets": (
            "role_view_question_ordering",
            "role_view_question_grouping",
            "role_view_policy_question_limits",
            "seed_question_role_fit",
            "role_interaction_reward_policy",
            "next_question_atom_reward_policy",
        ),
        "runtime_mutation": False,
        "guardrails": [
            "ROLE_QUESTION_CLICK_TRAINING_IS_OFFLINE_ONLY",
            "NO_RAW_USER_TEXT_IN_CLICK_LEDGER",
            "NO_QUESTION_TITLE_IN_CLICK_LEDGER",
            "NO_RUNTIME_POLICY_MUTATION",
            "POLICY_PROMOTION_REQUIRES_REPLAY",
        ],
    }


def write_role_question_click_training_artifact(
    *,
    store: LocalJsonlStore | None = None,
    output_dir: Path | None = None,
) -> dict[str, object]:
    storage = store or local_jsonl_store_from_env()
    report = build_role_question_click_training_report(store=storage)
    directory = output_dir or storage.runtime_dir / "training" / "role_question_click"
    directory.mkdir(parents=True, exist_ok=True)
    latest_path = directory / "latest.json"
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_path = directory / f"role_question_click_training_{stamp}.json"
    payload = report | {
        "written_at": datetime.now(timezone.utc).isoformat(),
        "runtime_mutation": True,
    }
    latest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    run_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return {
        "version": "v20.role_question_click_training_artifact_write.v1",
        "status": "written",
        "latest_path": str(latest_path),
        "run_path": str(run_path),
        "report_status": report["status"],
        "click_count": report["click_count"],
        "recommendation_count": len(report["recommendations"]),
        "runtime_mutation": True,
        "guardrails": [
            "LOCAL_RUNTIME_ARTIFACT_ONLY",
            "NO_POSTGRES_WRITE",
            "NO_RUNTIME_POLICY_PROMOTION",
        ],
    }


def read_role_question_click_training_artifact(*, output_dir: Path | None = None) -> dict[str, object]:
    runtime_dir = local_jsonl_store_from_env().runtime_dir
    latest_path = (output_dir or runtime_dir / "training" / "role_question_click") / "latest.json"
    if not latest_path.exists():
        return {
            "version": "v20.role_question_click_training_artifact_status.v1",
            "status": "not_built",
            "latest_path": str(latest_path),
            "runtime_mutation": False,
        }
    return json.loads(latest_path.read_text(encoding="utf-8")) | {"runtime_mutation": False}


def _read_records(store: LocalJsonlStore) -> list[dict[str, object]]:
    path = store.runtime_dir / "ledger" / f"{LEDGER_NAME}.jsonl"
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


def _click_rows(records: list[dict[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for record in records:
        payload = record.get("payload", {})
        if not isinstance(payload, dict):
            continue
        signal = payload.get("click_signal", payload)
        if isinstance(signal, dict) and signal.get("version") == "v20.role_question_click_signal.v1":
            rows.append({
                "source_role": str(payload.get("source_role", "")),
                "question_key": str(signal.get("question_key", "")),
                "question_id": str(signal.get("question_id", "")),
                "domain": str(signal.get("domain", "")),
                "role_view_level": str(signal.get("role_view_level", "")),
                "question_strategy": str(signal.get("question_strategy", "")),
                "question_group": str(signal.get("question_group", "")),
                "measurement_stage": str(signal.get("measurement_stage", "")),
                "seed_source_key": str(signal.get("seed_source_key", "")),
                "next_question_atom_id": str(signal.get("next_question_atom_id", "")),
                "next_question_topic": str(signal.get("next_question_topic", "")),
                "next_question_stage": str(signal.get("next_question_stage", "")),
                "action_type": str(signal.get("action_type", "select") or "select"),
                "reward_value": _float_value(signal.get("reward_value", 1.0), default=1.0),
            })
    return rows


def _role_summaries(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("source_role", "")) or "unknown"].append(row)
    return [_summary("role", role, values) for role, values in sorted(grouped.items())]


def _group_summaries(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[(str(row.get("source_role", "")) or "unknown", str(row.get("question_group", "")) or "unknown")].append(row)
    return [
        _summary("group", group, values) | {"source_role": role}
        for (role, group), values in sorted(grouped.items())
    ]


def _domain_summaries(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[(str(row.get("source_role", "")) or "unknown", str(row.get("domain", "")) or "unknown")].append(row)
    return [
        _summary("domain", domain, values) | {"source_role": role}
        for (role, domain), values in sorted(grouped.items())
    ]


def _strategy_summaries(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[(str(row.get("source_role", "")) or "unknown", str(row.get("question_strategy", "")) or "unknown")].append(row)
    return [
        _summary("strategy", strategy, values) | {"source_role": role}
        for (role, strategy), values in sorted(grouped.items())
    ]


def _seed_summaries(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        seed_key = str(row.get("seed_source_key", ""))
        if not seed_key:
            continue
        grouped[(str(row.get("source_role", "")) or "unknown", seed_key)].append(row)
    return [
        _summary("seed", seed_key, values) | {"source_role": role}
        for (role, seed_key), values in sorted(grouped.items())
    ]


def _next_question_atom_summaries(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        atom_id = str(row.get("next_question_atom_id", ""))
        if atom_id:
            grouped[(str(row.get("source_role", "")) or "unknown", atom_id)].append(row)
    summaries: list[dict[str, object]] = []
    for (role, atom_id), values in sorted(grouped.items()):
        reward_total = _reward_total(values)
        sample_count = len(values)
        topics = Counter(str(row.get("next_question_topic", "")) or "unknown" for row in values)
        stages = Counter(str(row.get("next_question_stage", "")) or "unknown" for row in values)
        summaries.append({
            "source_role": role,
            "atom_id": atom_id,
            "sample_count": sample_count,
            "reward_total": reward_total,
            "reward_average": round(reward_total / max(1, sample_count), 3),
            "positive_count": sum(1 for row in values if _float_value(row.get("reward_value"), default=0.0) > 0),
            "negative_count": sum(1 for row in values if _float_value(row.get("reward_value"), default=0.0) < 0),
            "top_topic": _top_key(topics),
            "top_stage": _top_key(stages),
            "runtime_allowed": False,
        })
    return summaries


def _action_summaries(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[(str(row.get("source_role", "")) or "unknown", str(row.get("action_type", "")) or "select")].append(row)
    return [
        _summary("action", action, values) | {"source_role": role, "reward_total": _reward_total(values)}
        for (role, action), values in sorted(grouped.items())
    ]


def _reward_summaries(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[(str(row.get("source_role", "")) or "unknown", str(row.get("question_key", "")) or "unknown")].append(row)
    summaries: list[dict[str, object]] = []
    for (role, question_key), values in sorted(grouped.items()):
        reward_total = _reward_total(values)
        summaries.append(
            {
                "source_role": role,
                "question_key": question_key,
                "sample_count": len(values),
                "reward_total": reward_total,
                "reward_average": round(reward_total / max(1, len(values)), 3),
                "positive_count": sum(1 for row in values if _float_value(row.get("reward_value"), default=0.0) > 0),
                "negative_count": sum(1 for row in values if _float_value(row.get("reward_value"), default=0.0) < 0),
                "runtime_allowed": False,
            }
        )
    return summaries


def _summary(kind: str, key: str, rows: list[dict[str, object]]) -> dict[str, object]:
    domains = Counter(str(row.get("domain", "")) or "unknown" for row in rows)
    groups = Counter(str(row.get("question_group", "")) or "unknown" for row in rows)
    strategies = Counter(str(row.get("question_strategy", "")) or "unknown" for row in rows)
    question_keys = Counter(str(row.get("question_key", "")) or "unknown" for row in rows)
    return {
        f"{kind}_key": key,
        "click_count": len(rows),
        "top_domain": _top_key(domains),
        "domain_counts": dict(sorted(domains.items())),
        "top_group": _top_key(groups),
        "group_counts": dict(sorted(groups.items())),
        "top_strategy": _top_key(strategies),
        "strategy_counts": dict(sorted(strategies.items())),
        "top_question_keys": tuple(key for key, _count in question_keys.most_common(5)),
        "runtime_allowed": False,
    }


def _recommendations(
    role_summaries: list[dict[str, object]],
    group_summaries: list[dict[str, object]],
    domain_summaries: list[dict[str, object]],
    strategy_summaries: list[dict[str, object]],
    seed_summaries: list[dict[str, object]],
    reward_summaries: list[dict[str, object]],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for summary in role_summaries:
        if int(summary.get("click_count", 0)) >= MIN_POLICY_SAMPLES:
            rows.append({
                "recommendation_key": f"role_view.question_limit.review.{summary['role_key']}",
                "source_role": summary["role_key"],
                "recommendation_type": "review_question_limit_and_ordering",
                "basis": f"{summary['click_count']} clicks; top group {summary.get('top_group', '')}; top domain {summary.get('top_domain', '')}",
                "runtime_allowed": False,
            })
    for collection, kind in ((group_summaries, "group"), (domain_summaries, "domain"), (strategy_summaries, "strategy")):
        for summary in collection:
            if int(summary.get("click_count", 0)) < MIN_POLICY_SAMPLES:
                continue
            key = summary.get(f"{kind}_key", "")
            role = summary.get("source_role", "")
            rows.append({
                "recommendation_key": f"role_view.{kind}.boost.{role}.{key}",
                "source_role": role,
                "recommendation_type": f"consider_{kind}_boost",
                "basis": f"{summary['click_count']} clicks for {kind}={key}",
                "runtime_allowed": False,
            })
    for summary in seed_summaries:
        if int(summary.get("click_count", 0)) < MIN_POLICY_SAMPLES:
            continue
        rows.append({
            "recommendation_key": f"role_view.seed.review.{summary.get('source_role', '')}.{summary.get('seed_key', '')}",
            "source_role": summary.get("source_role", ""),
            "recommendation_type": "review_seed_question_fit",
            "basis": f"{summary['click_count']} clicks for seed={summary.get('seed_key', '')}; top domain {summary.get('top_domain', '')}",
            "runtime_allowed": False,
        })
    for summary in reward_summaries:
        if int(summary.get("sample_count", 0)) < MIN_POLICY_SAMPLES:
            continue
        reward_average = float(summary.get("reward_average", 0.0) or 0.0)
        if reward_average >= 0.6:
            action = "boost_question_candidate"
        elif reward_average <= -0.4:
            action = "suppress_question_candidate"
        else:
            action = "keep_collecting_reward"
        rows.append({
            "recommendation_key": f"role_view.reward.{action}.{summary.get('source_role', '')}.{summary.get('question_key', '')}",
            "source_role": summary.get("source_role", ""),
            "recommendation_type": action,
            "basis": f"{summary['sample_count']} structured interactions; avg reward {reward_average}",
            "runtime_allowed": False,
        })
    return rows


def _next_question_feedback_policy(atom_summaries: list[dict[str, object]]) -> dict[str, object]:
    atom_boosts: dict[str, float] = {}
    atom_penalties: dict[str, float] = {}
    topic_boosts: dict[str, float] = {}
    stage_boosts: dict[str, float] = {}
    for summary in atom_summaries:
        sample_count = int(summary.get("sample_count", 0) or 0)
        if sample_count < MIN_POLICY_SAMPLES:
            continue
        atom_id = str(summary.get("atom_id", ""))
        reward_average = float(summary.get("reward_average", 0.0) or 0.0)
        magnitude = round(min(0.08, abs(reward_average) * 0.05 + min(0.03, sample_count * 0.005)), 4)
        if reward_average >= 0.4:
            atom_boosts[atom_id] = magnitude
            topic = str(summary.get("top_topic", ""))
            stage = str(summary.get("top_stage", ""))
            if topic and topic != "unknown":
                topic_boosts[topic] = round(topic_boosts.get(topic, 0.0) + min(0.03, magnitude / 2), 4)
            if stage and stage != "unknown":
                stage_boosts[stage] = round(stage_boosts.get(stage, 0.0) + min(0.025, magnitude / 3), 4)
        elif reward_average <= -0.3:
            atom_penalties[atom_id] = -magnitude
    return {
        "version": "v20.next_question_feedback_policy.v1",
        "status": "ready" if atom_boosts or atom_penalties else "not_enough_data",
        "atom_boosts": atom_boosts,
        "atom_penalties": atom_penalties,
        "topic_boosts": topic_boosts,
        "stage_boosts": stage_boosts,
        "runtime_mutation": False,
        "guardrails": [
            "STRUCTURED_CLICK_REWARD_ONLY",
            "NO_RAW_USER_TEXT",
            "BOOSTS_AND_PENALTIES_ONLY",
        ],
    }


def _top_key(counter: Counter[str]) -> str:
    if not counter:
        return ""
    return counter.most_common(1)[0][0]


def _reward_total(rows: list[dict[str, object]]) -> float:
    return round(sum(_float_value(row.get("reward_value"), default=0.0) for row in rows), 3)


def _float_value(value: object, *, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default
