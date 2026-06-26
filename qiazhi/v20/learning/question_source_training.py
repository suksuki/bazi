from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from v20.storage.local_jsonl import LocalJsonlStore, local_jsonl_store_from_env


ProgressCallback = Callable[[str], None]

LEDGER_NAME = "question_source_ranking_ledger"
MIN_SOURCE_SAMPLES = 3
MIN_AVERAGE_GRAPH_SCORE = 0.18


def build_question_source_training_report(
    *,
    store: LocalJsonlStore | None = None,
    reports: tuple[dict[str, object], ...] | None = None,
    progress: ProgressCallback | None = None,
) -> dict[str, object]:
    storage = store or local_jsonl_store_from_env()
    records = [] if reports is not None else _read_records(storage)
    report_rows = list(reports) if reports is not None else _report_rows(records)
    _emit(progress, f"question source reports: {len(report_rows)}")
    source_rows = _source_rows(report_rows)
    _emit(progress, f"compiled question source rows: {len(source_rows)}")
    source_summaries = _source_summaries(source_rows)
    domain_summaries = _domain_summaries(source_rows)
    training_proposals = _training_proposals(source_summaries)
    return {
        "version": "v20.question_source_training_report.v1",
        "status": "ready" if report_rows else "not_enough_data",
        "ok": True,
        "ledger_name": LEDGER_NAME,
        "record_count": len(records),
        "report_count": len(report_rows),
        "compiled_source_row_count": len(source_rows),
        "source_summaries": source_summaries,
        "domain_summaries": domain_summaries,
        "training_proposals": training_proposals,
        "activation_thresholds": {
            "min_source_samples": MIN_SOURCE_SAMPLES,
            "min_average_graph_score": MIN_AVERAGE_GRAPH_SCORE,
        },
        "training_targets": (
            "question_source_graph_quality_policy",
            "question_focus_policy",
        ),
        "runtime_mutation": False,
        "guardrails": [
            "QUESTION_SOURCE_TRAINING_IS_OFFLINE_ONLY",
            "NO_RUNTIME_QUESTION_ORDER_MUTATION",
            "NO_RUNTIME_POLICY_WRITE",
            "POLICY_PROMOTION_REQUIRES_REPLAY",
        ],
    }


def write_question_source_training_artifact(
    *,
    store: LocalJsonlStore | None = None,
    output_dir: Path | None = None,
    progress: ProgressCallback | None = None,
) -> dict[str, object]:
    storage = store or local_jsonl_store_from_env()
    report = build_question_source_training_report(store=storage, progress=progress)
    directory = output_dir or storage.runtime_dir / "training" / "question_source"
    directory.mkdir(parents=True, exist_ok=True)
    latest_path = directory / "latest.json"
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_path = directory / f"question_source_training_{stamp}.json"
    payload = report | {
        "written_at": datetime.now(timezone.utc).isoformat(),
        "runtime_mutation": True,
    }
    latest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    run_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return {
        "version": "v20.question_source_training_artifact_write.v1",
        "status": "written",
        "latest_path": str(latest_path),
        "run_path": str(run_path),
        "report_status": report["status"],
        "report_count": report["report_count"],
        "compiled_source_row_count": report["compiled_source_row_count"],
        "proposal_count": len(report["training_proposals"]),
        "runtime_mutation": True,
        "guardrails": [
            "LOCAL_RUNTIME_ARTIFACT_ONLY",
            "NO_POSTGRES_WRITE",
            "NO_RUNTIME_POLICY_PROMOTION",
        ],
    }


def read_question_source_training_artifact(*, output_dir: Path | None = None) -> dict[str, object]:
    runtime_dir = local_jsonl_store_from_env().runtime_dir
    latest_path = (output_dir or runtime_dir / "training" / "question_source") / "latest.json"
    if not latest_path.exists():
        return {
            "version": "v20.question_source_training_artifact_status.v1",
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


def _report_rows(records: list[dict[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for record in records:
        payload = record.get("payload", {})
        if not isinstance(payload, dict):
            continue
        report = payload.get("question_source_ranking_report", payload)
        if isinstance(report, dict) and report.get("version") == "v20.question_source_ranking_report.v1":
            rows.append(report)
    return rows


def _source_rows(reports: list[dict[str, object]]) -> list[dict[str, object]]:
    rows = []
    for report in reports:
        for row in report.get("rows", ()):
            if not isinstance(row, dict):
                continue
            rows.append(
                {
                    "source_key": str(row.get("source_key", "")) or "unknown",
                    "domain": str(row.get("domain", "")) or "unknown",
                    "question_strategy": str(row.get("question_strategy", "")),
                    "source_graph_score": _float(row.get("source_graph_score", 0)),
                    "question_score": _float(row.get("question_score", 0)),
                    "rank": int(row.get("rank", 0) or 0),
                }
            )
    return [row for row in rows if row["source_key"]]


def _source_summaries(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    by_source: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        by_source[str(row["source_key"])].append(row)
    summaries = []
    for source_key, items in sorted(by_source.items()):
        domains = Counter(str(row["domain"]) for row in items)
        avg_graph = _average(row["source_graph_score"] for row in items)
        avg_question = _average(row["question_score"] for row in items)
        summaries.append(
            {
                "source_key": source_key,
                "sample_count": len(items),
                "average_graph_score": avg_graph,
                "average_question_score": avg_question,
                "top_domain": domains.most_common(1)[0][0] if domains else "",
                "domain_counts": dict(sorted(domains.items())),
                "training_candidate": len(items) >= MIN_SOURCE_SAMPLES and avg_graph >= MIN_AVERAGE_GRAPH_SCORE,
                "runtime_allowed": False,
            }
        )
    return summaries


def _domain_summaries(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    by_domain: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        by_domain[str(row["domain"])].append(row)
    return [
        {
            "domain": domain,
            "sample_count": len(items),
            "source_counts": dict(sorted(Counter(str(row["source_key"]) for row in items).items())),
            "average_graph_score": _average(row["source_graph_score"] for row in items),
            "average_question_score": _average(row["question_score"] for row in items),
            "runtime_allowed": False,
        }
        for domain, items in sorted(by_domain.items())
    ]


def _training_proposals(source_summaries: list[dict[str, object]]) -> list[dict[str, object]]:
    proposals = []
    for summary in source_summaries:
        if not summary.get("training_candidate"):
            continue
        proposals.append(
            {
                "target": "question_source_graph_quality_policy",
                "source_key": summary["source_key"],
                "suggested_action": "increase_source_quality_prior",
                "sample_count": summary["sample_count"],
                "average_graph_score": summary["average_graph_score"],
                "average_question_score": summary["average_question_score"],
                "status": "candidate_from_offline_training",
                "runtime_allowed": False,
            }
        )
    return proposals


def _average(values) -> float:
    rows = [float(value or 0.0) for value in values]
    return round(sum(rows) / len(rows), 4) if rows else 0.0


def _float(value: object) -> float:
    try:
        return round(float(value or 0.0), 4)
    except (TypeError, ValueError):
        return 0.0


def _emit(progress: ProgressCallback | None, message: str) -> None:
    if progress:
        progress(message)
