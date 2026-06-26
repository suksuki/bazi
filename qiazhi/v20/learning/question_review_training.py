from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from v20.interaction.question_review import LEDGER_NAME
from v20.storage.local_jsonl import LocalJsonlStore, local_jsonl_store_from_env


MIN_REVIEW_SAMPLES = 2
NEGATIVE_ACTIONS = {"downrank", "delete", "merge", "rewrite"}


def build_question_review_training_report(
    *,
    store: LocalJsonlStore | None = None,
    reviews: tuple[dict[str, object], ...] | None = None,
) -> dict[str, object]:
    storage = store or local_jsonl_store_from_env()
    records = [] if reviews is not None else _read_records(storage)
    rows = list(reviews) if reviews is not None else _review_rows(records)
    action_summaries = _action_summaries(rows)
    reason_summaries = _reason_summaries(rows)
    question_summaries = _question_summaries(rows)
    role_stage_summaries = _role_stage_summaries(rows)
    recommendations = _recommendations(question_summaries, role_stage_summaries)
    return {
        "version": "v20.question_review_training_report.v1",
        "status": "ready" if rows else "not_enough_data",
        "ok": True,
        "ledger_name": LEDGER_NAME,
        "record_count": len(records),
        "review_count": len(rows),
        "action_summaries": action_summaries,
        "reason_summaries": reason_summaries,
        "question_summaries": question_summaries,
        "role_stage_summaries": role_stage_summaries,
        "recommendations": recommendations,
        "activation_thresholds": {
            "min_review_samples": MIN_REVIEW_SAMPLES,
        },
        "training_targets": (
            "question_template_quality",
            "role_question_fit",
            "question_dag_stage_fit",
            "question_priority_suppression",
        ),
        "runtime_mutation": False,
        "guardrails": [
            "QUESTION_REVIEW_TRAINING_IS_OFFLINE_ONLY",
            "NO_RAW_USER_TEXT_IN_REVIEW_LEDGER",
            "NO_QUESTION_TITLE_IN_REVIEW_LEDGER",
            "NO_RUNTIME_POLICY_MUTATION",
            "REVIEW_RECOMMENDATIONS_REQUIRE_REPLAY",
        ],
    }


def write_question_review_training_artifact(
    *,
    store: LocalJsonlStore | None = None,
    output_dir: Path | None = None,
) -> dict[str, object]:
    storage = store or local_jsonl_store_from_env()
    report = build_question_review_training_report(store=storage)
    directory = output_dir or storage.runtime_dir / "training" / "question_review"
    directory.mkdir(parents=True, exist_ok=True)
    latest_path = directory / "latest.json"
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_path = directory / f"question_review_training_{stamp}.json"
    payload = report | {
        "written_at": datetime.now(timezone.utc).isoformat(),
        "runtime_mutation": True,
    }
    latest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    run_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return {
        "version": "v20.question_review_training_artifact_write.v1",
        "status": "written",
        "latest_path": str(latest_path),
        "run_path": str(run_path),
        "report_status": report["status"],
        "review_count": report["review_count"],
        "recommendation_count": len(report["recommendations"]),
        "runtime_mutation": True,
        "guardrails": [
            "LOCAL_RUNTIME_ARTIFACT_ONLY",
            "NO_POSTGRES_WRITE",
            "NO_RUNTIME_POLICY_PROMOTION",
        ],
    }


def read_question_review_training_artifact(*, output_dir: Path | None = None) -> dict[str, object]:
    runtime_dir = local_jsonl_store_from_env().runtime_dir
    latest_path = (output_dir or runtime_dir / "training" / "question_review") / "latest.json"
    if not latest_path.exists():
        return {
            "version": "v20.question_review_training_artifact_status.v1",
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


def _review_rows(records: list[dict[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for record in records:
        payload = record.get("payload", {})
        if not isinstance(payload, dict):
            continue
        signal = payload.get("review_signal", payload)
        if isinstance(signal, dict) and signal.get("version") == "v20.question_review_signal.v1":
            rows.append({
                "source_role": str(payload.get("source_role", "")),
                "action": str(payload.get("action", "")),
                "reason": str(payload.get("reason", "")),
                "question_key": str(payload.get("question_key", "")),
                "question_id": str(payload.get("question_id", "")),
                "domain": str(payload.get("domain", "")),
                "stage": str(payload.get("stage", "")),
                "role_target": str(payload.get("role_target", "")),
                "question_strategy": str(signal.get("question_strategy", "")),
                "source": str(signal.get("source", "")),
            })
    return rows


def _action_summaries(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[(str(row.get("source_role", "")) or "unknown", str(row.get("action", "")) or "unknown")].append(row)
    return [
        _summary("action", action, values) | {"source_role": role}
        for (role, action), values in sorted(grouped.items())
    ]


def _reason_summaries(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        reason = str(row.get("reason", "")) or "none"
        grouped[(str(row.get("source_role", "")) or "unknown", reason)].append(row)
    return [
        _summary("reason", reason, values) | {"source_role": role}
        for (role, reason), values in sorted(grouped.items())
    ]


def _question_summaries(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        key = str(row.get("question_key", "")) or str(row.get("question_id", "")) or "unknown"
        grouped[(str(row.get("role_target", "")) or "unknown", key)].append(row)
    summaries: list[dict[str, object]] = []
    for (role_target, question_key), values in sorted(grouped.items()):
        actions = Counter(str(row.get("action", "")) or "unknown" for row in values)
        reasons = Counter(str(row.get("reason", "")) or "none" for row in values)
        negative_count = sum(count for action, count in actions.items() if action in NEGATIVE_ACTIONS)
        summaries.append(
            _summary("question", question_key, values) | {
                "role_target": role_target,
                "negative_count": negative_count,
                "negative_ratio": round(negative_count / max(1, len(values)), 3),
                "top_action": _top_key(actions),
                "top_reason": _top_key(reasons),
            }
        )
    return summaries


def _role_stage_summaries(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[tuple[str, str, str], list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[
            (
                str(row.get("role_target", "")) or "unknown",
                str(row.get("stage", "")) or "unknown",
                str(row.get("domain", "")) or "unknown",
            )
        ].append(row)
    summaries: list[dict[str, object]] = []
    for (role_target, stage, domain), values in sorted(grouped.items()):
        actions = Counter(str(row.get("action", "")) or "unknown" for row in values)
        negative_count = sum(count for action, count in actions.items() if action in NEGATIVE_ACTIONS)
        summaries.append(
            _summary("role_stage", f"{role_target}.{stage}.{domain}", values) | {
                "role_target": role_target,
                "stage": stage,
                "domain": domain,
                "negative_count": negative_count,
                "negative_ratio": round(negative_count / max(1, len(values)), 3),
                "top_action": _top_key(actions),
            }
        )
    return summaries


def _recommendations(
    question_summaries: list[dict[str, object]],
    role_stage_summaries: list[dict[str, object]],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for summary in question_summaries:
        if int(summary.get("review_count", 0) or 0) < MIN_REVIEW_SAMPLES:
            continue
        negative_ratio = float(summary.get("negative_ratio", 0.0) or 0.0)
        if negative_ratio <= 0:
            rows.append(_recommendation(summary, "approve_question_candidate", "question_review_positive_fit"))
        elif negative_ratio >= 0.67:
            rows.append(_recommendation(summary, "suppress_question_candidate", "question_review_negative_fit"))
        else:
            rows.append(_recommendation(summary, "rewrite_question_candidate", "question_review_mixed_fit"))
    for summary in role_stage_summaries:
        if int(summary.get("review_count", 0) or 0) < MIN_REVIEW_SAMPLES:
            continue
        if float(summary.get("negative_ratio", 0.0) or 0.0) >= 0.5:
            rows.append({
                "recommendation_key": (
                    f"question_review.role_stage.suppress."
                    f"{summary.get('role_target', '')}.{summary.get('stage', '')}.{summary.get('domain', '')}"
                ),
                "source_role": "",
                "role_target": summary.get("role_target", ""),
                "stage": summary.get("stage", ""),
                "domain": summary.get("domain", ""),
                "recommendation_type": "suppress_role_stage_question_candidate",
                "basis": (
                    f"{summary['review_count']} reviews; negative ratio {summary.get('negative_ratio', 0)}; "
                    f"top action {summary.get('top_action', '')}"
                ),
                "runtime_allowed": False,
            })
    return rows


def _recommendation(summary: dict[str, object], recommendation_type: str, basis_key: str) -> dict[str, object]:
    question_key = str(summary.get("question_key", ""))
    role_target = str(summary.get("role_target", ""))
    return {
        "recommendation_key": f"question_review.{recommendation_type}.{role_target}.{question_key}",
        "source_role": "",
        "role_target": role_target,
        "question_key": question_key,
        "domain": summary.get("top_domain", ""),
        "stage": summary.get("top_stage", ""),
        "recommendation_type": recommendation_type,
        "basis": (
            f"{summary['review_count']} reviews; negative ratio {summary.get('negative_ratio', 0)}; "
            f"top action {summary.get('top_action', '')}; top reason {summary.get('top_reason', '')}; {basis_key}"
        ),
        "runtime_allowed": False,
    }


def _summary(kind: str, key: str, rows: list[dict[str, object]]) -> dict[str, object]:
    domains = Counter(str(row.get("domain", "")) or "unknown" for row in rows)
    stages = Counter(str(row.get("stage", "")) or "unknown" for row in rows)
    role_targets = Counter(str(row.get("role_target", "")) or "unknown" for row in rows)
    return {
        f"{kind}_key": key,
        "review_count": len(rows),
        "top_domain": _top_key(domains),
        "domain_counts": dict(sorted(domains.items())),
        "top_stage": _top_key(stages),
        "stage_counts": dict(sorted(stages.items())),
        "top_role_target": _top_key(role_targets),
        "role_target_counts": dict(sorted(role_targets.items())),
        "runtime_allowed": False,
    }


def _top_key(counter: Counter[str]) -> str:
    if not counter:
        return ""
    return counter.most_common(1)[0][0]
