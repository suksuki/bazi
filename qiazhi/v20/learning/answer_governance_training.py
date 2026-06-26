from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from v20.storage.local_jsonl import local_jsonl_store_from_env
from v20.storage.local_jsonl import LocalJsonlStore
from v20.validation.answer_safety_evaluator import evaluate_answer_governance_quality
from v20.validation.synthetic_replay import run_synthetic_bazi_replay


ANSWER_GOVERNANCE_TRAINING_VERSION = "v20.answer_governance_training_report.v1"


def build_answer_governance_training_report(
    *,
    replay_report: dict[str, object] | None = None,
    max_cases: int = 3,
    store: LocalJsonlStore | None = None,
) -> dict[str, object]:
    replay = replay_report or run_synthetic_bazi_replay(max_cases=max(0, max_cases))
    storage = store or local_jsonl_store_from_env()
    rows = []
    for result in replay.get("results", ()) if isinstance(replay, dict) else ():
        if not isinstance(result, dict):
            continue
        actual = result.get("actual", {})
        answer_text = str(actual.get("answer_text") or "") if isinstance(actual, dict) else ""
        quality = evaluate_answer_governance_quality(answer_text)
        rows.append(
            {
                "case_id": str(result.get("case_id", "")),
                "case_type": str(result.get("case_type", "")),
                "quality_score": float(quality.get("quality_score", 0.0) or 0.0),
                "quality_band": str(quality.get("quality_band", "")),
                "dimensions": quality.get("dimensions", {}),
                "findings": tuple(str(item) for item in quality.get("findings", ()) if str(item)),
                "runtime_mutation": False,
            }
        )
    average = round(sum(float(row["quality_score"]) for row in rows) / max(1, len(rows)), 4)
    weak_count = sum(1 for row in rows if row["quality_band"] in {"weak", "thin"})
    role_summary = replay.get("role_answer_governance_summary", {}) if isinstance(replay, dict) else {}
    stream_summary = _stream_answer_governance_summary(replay, storage)
    role_missing_profile_count = int(role_summary.get("missing_profile_count", 0) or 0) if isinstance(role_summary, dict) else 0
    role_average_quality = float(role_summary.get("average_quality_score", 0.0) or 0.0) if isinstance(role_summary, dict) else 0.0
    return {
        "version": ANSWER_GOVERNANCE_TRAINING_VERSION,
        "status": "ready",
        "case_count": len(rows),
        "average_quality_score": average,
        "strong_case_count": sum(1 for row in rows if row["quality_band"] == "strong"),
        "weak_or_thin_case_count": weak_count,
        "role_answer_governance_summary": role_summary if isinstance(role_summary, dict) else {},
        "stream_answer_governance_summary": stream_summary,
        "quality_findings": (
            ([f"answer_governance_weak_or_thin_count:{weak_count}"] if weak_count else [])
            + (
                [f"role_answer_governance_missing_profile_count:{role_missing_profile_count}"]
                if role_missing_profile_count
                else []
            )
            + (
                [f"stream_answer_governance_weak_or_thin_count:{stream_summary['weak_or_thin_count']}"]
                if int(stream_summary.get("weak_or_thin_count", 0) or 0)
                else []
            )
        ),
        "parameter_targets": {
            "answer_guidance_weight": _answer_guidance_weight_delta(average, weak_count),
            "role_answer_governance_weight": _role_answer_governance_weight_delta(
                role_average_quality,
                role_missing_profile_count,
            ),
            "prompt_context_budget_weight": _prompt_context_budget_weight_delta(stream_summary),
            "stream_answer_quality_weight": _stream_answer_quality_weight_delta(stream_summary),
            "boundary_hint_weight": _dimension_average(rows, "boundary_hint"),
            "evidence_language_weight": _dimension_average(rows, "evidence_language"),
            "review_counterevidence_weight": _dimension_average(rows, "review_or_counterevidence"),
            "next_step_guidance_weight": _dimension_average(rows, "next_step_guidance"),
        },
        "rows": rows,
        "runtime_mutation": False,
        "guardrails": [
            "ANSWER_GOVERNANCE_TRAINING_IS_SYNTHETIC_SIGNAL",
            "QUALITY_SCORE_FEEDS_RUNTIME_POINTER_WEIGHT_ONLY",
            "ROLE_ANSWER_GOVERNANCE_FEEDS_RUNTIME_STYLE_WEIGHT",
            "STREAM_ANSWER_QUALITY_FEEDS_PROMPT_CONTEXT_BUDGET_WEIGHT",
            "NO_ANSWER_TEXT_REWRITE_FROM_TRAINING",
            "NO_HUMAN_REVIEW_GATE",
        ],
    }


def write_answer_governance_training_artifact(
    *,
    replay_report: dict[str, object] | None = None,
    max_cases: int = 3,
    output_dir: Path | None = None,
) -> dict[str, object]:
    report = build_answer_governance_training_report(replay_report=replay_report, max_cases=max_cases)
    runtime_dir = local_jsonl_store_from_env().runtime_dir
    directory = output_dir or runtime_dir / "training" / "answer_governance"
    directory.mkdir(parents=True, exist_ok=True)
    latest_path = directory / "latest.json"
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_path = directory / f"answer_governance_{stamp}.json"
    payload = report | {
        "written_at": datetime.now(timezone.utc).isoformat(),
        "runtime_mutation": True,
    }
    latest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    run_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return {
        "version": "v20.answer_governance_training_artifact_write.v1",
        "status": "written",
        "latest_path": str(latest_path),
        "run_path": str(run_path),
        "report_status": report["status"],
        "average_quality_score": report["average_quality_score"],
        "runtime_mutation": True,
        "guardrails": [
            "LOCAL_RUNTIME_ARTIFACT_ONLY",
            "ANSWER_GOVERNANCE_POINTER_SIGNAL_READY",
        ],
    }


def _answer_guidance_weight_delta(average_quality_score: float, weak_count: int) -> float:
    if weak_count > 0:
        return 0.0
    if average_quality_score >= 0.8:
        return 0.014
    if average_quality_score >= 0.55:
        return 0.006
    return 0.0


def _role_answer_governance_weight_delta(average_quality_score: float, missing_profile_count: int) -> float:
    if missing_profile_count > 0:
        return 0.0
    if average_quality_score >= 0.8:
        return 0.012
    if average_quality_score >= 0.55:
        return 0.005
    return 0.0


def _prompt_context_budget_weight_delta(summary: dict[str, object]) -> float:
    count = int(summary.get("sample_count", 0) or 0)
    weak_count = int(summary.get("weak_or_thin_count", 0) or 0)
    average = float(summary.get("average_quality_score", 0.0) or 0.0)
    if count <= 0 or weak_count > 0:
        return 0.0
    if average >= 0.8:
        return 0.01
    if average >= 0.55:
        return 0.004
    return 0.0


def _stream_answer_quality_weight_delta(summary: dict[str, object]) -> float:
    count = int(summary.get("sample_count", 0) or 0)
    average = float(summary.get("average_quality_score", 0.0) or 0.0)
    if count <= 0:
        return 0.0
    if average >= 0.8:
        return 0.012
    if average >= 0.55:
        return 0.005
    return 0.0


def _dimension_average(rows: list[dict[str, Any]], key: str) -> float:
    values = []
    for row in rows:
        dimensions = row.get("dimensions", {})
        if isinstance(dimensions, dict):
            values.append(float(dimensions.get(key, 0.0) or 0.0))
    return round(sum(values) / max(1, len(values)), 4)


def _stream_answer_governance_summary(replay: dict[str, object], store: LocalJsonlStore) -> dict[str, object]:
    provided = replay.get("stream_answer_governance_summary", {}) if isinstance(replay, dict) else {}
    if isinstance(provided, dict) and provided.get("version") == "v20.stream_answer_governance_summary.v1":
        return _normalize_stream_summary(provided)
    rows = _stream_answer_quality_rows_from_replay(replay) or _stream_answer_quality_rows_from_ledger(store)
    weak_count = sum(1 for row in rows if str(row.get("quality_band", "")) in {"weak", "thin"})
    average = round(sum(float(row.get("quality_score", 0.0) or 0.0) for row in rows) / max(1, len(rows)), 4)
    return {
        "version": "v20.stream_answer_governance_summary.v1",
        "source": "replay_samples" if _stream_answer_quality_rows_from_replay(replay) else "llm_stream_answer_quality_ledger",
        "sample_count": len(rows),
        "average_quality_score": average,
        "weak_or_thin_count": weak_count,
        "quality_band_counts": _count_by(rows, "quality_band"),
        "runtime_mutation": False,
        "guardrails": [
            "STREAM_ANSWER_QUALITY_IS_TRAINING_SIGNAL",
            "NO_RAW_ANSWER_TEXT_REQUIRED",
            "NO_HUMAN_REVIEW_GATE",
        ],
    }


def _normalize_stream_summary(summary: dict[str, object]) -> dict[str, object]:
    return {
        "version": "v20.stream_answer_governance_summary.v1",
        "source": str(summary.get("source", "provided")),
        "sample_count": int(summary.get("sample_count", 0) or 0),
        "average_quality_score": float(summary.get("average_quality_score", 0.0) or 0.0),
        "weak_or_thin_count": int(summary.get("weak_or_thin_count", 0) or 0),
        "quality_band_counts": summary.get("quality_band_counts", {}) if isinstance(summary.get("quality_band_counts", {}), dict) else {},
        "runtime_mutation": False,
        "guardrails": tuple(summary.get("guardrails", ())) if isinstance(summary.get("guardrails", ()), (list, tuple)) else (),
    }


def _stream_answer_quality_rows_from_replay(replay: dict[str, object]) -> list[dict[str, object]]:
    rows = replay.get("stream_answer_quality_samples", ()) if isinstance(replay, dict) else ()
    if not isinstance(rows, (list, tuple)):
        return []
    return [
        {
            "quality_score": float(row.get("quality_score", 0.0) or 0.0),
            "quality_band": str(row.get("quality_band", "")),
        }
        for row in rows
        if isinstance(row, dict)
    ]


def _stream_answer_quality_rows_from_ledger(store: LocalJsonlStore, *, limit: int = 100) -> list[dict[str, object]]:
    path = store.runtime_dir / "ledger" / "llm_stream_answer_quality.jsonl"
    if not path.exists():
        return []
    rows: list[dict[str, object]] = []
    for line in path.read_text(encoding="utf-8").splitlines()[-limit:]:
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        payload = record.get("payload", {}) if isinstance(record, dict) else {}
        if not isinstance(payload, dict):
            continue
        rows.append(
            {
                "quality_score": float(payload.get("quality_score", 0.0) or 0.0),
                "quality_band": str(payload.get("quality_band", "")),
            }
        )
    return rows


def _count_by(rows: list[dict[str, object]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        value = str(row.get(key, ""))
        if value:
            counts[value] = counts.get(value, 0) + 1
    return counts
