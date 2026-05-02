from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from v20.storage.local_jsonl import LocalJsonlStore, local_jsonl_store_from_env

ProgressCallback = Callable[[str], None]

LEDGER_NAME = "practitioner_calibration_ledger"
MIN_PROMOTION_SAMPLES = 3
MIN_PROMOTION_RATIO = 0.67


def build_practitioner_calibration_training_report(
    *,
    store: LocalJsonlStore | None = None,
    progress: ProgressCallback | None = None,
) -> dict[str, object]:
    storage = store or local_jsonl_store_from_env()
    records = _read_records(storage)
    _emit(progress, f"practitioner calibration records: {len(records)}")
    selection_rows = _selection_rows(records)
    _emit(progress, f"structured selections: {len(selection_rows)}")
    control_summaries = _control_summaries(selection_rows)
    training_proposals = _training_proposals(control_summaries)
    status = "ready" if selection_rows else "not_enough_data"
    return {
        "version": "v20.practitioner_calibration_training_report.v1",
        "status": status,
        "ok": True,
        "record_count": len(records),
        "selection_count": len(selection_rows),
        "control_summaries": control_summaries,
        "training_proposals": training_proposals,
        "promotion_thresholds": {
            "min_samples": MIN_PROMOTION_SAMPLES,
            "min_ratio": MIN_PROMOTION_RATIO,
        },
        "training_targets": (
            "decision_parameters",
            "portrait_library",
            "question_seed_ranking",
        ),
        "runtime_mutation": False,
        "guardrails": [
            "PRACTITIONER_CALIBRATION_TRAINING_IS_OFFLINE_ONLY",
            "NO_RUNTIME_DECISION_MUTATION",
            "NO_DIRECT_RULE_PROMOTION",
            "PROMOTION_REQUIRES_SYNTHETIC_AND_BATCH_VALIDATION",
        ],
    }


def write_practitioner_calibration_training_artifact(
    *,
    store: LocalJsonlStore | None = None,
    output_dir: Path | None = None,
    progress: ProgressCallback | None = None,
) -> dict[str, object]:
    storage = store or local_jsonl_store_from_env()
    report = build_practitioner_calibration_training_report(store=storage, progress=progress)
    directory = output_dir or storage.runtime_dir / "training" / "practitioner_calibration"
    directory.mkdir(parents=True, exist_ok=True)
    latest_path = directory / "latest.json"
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_path = directory / f"practitioner_calibration_training_{stamp}.json"
    payload = report | {
        "written_at": datetime.now(timezone.utc).isoformat(),
        "runtime_mutation": True,
    }
    latest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    run_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return {
        "version": "v20.practitioner_calibration_training_artifact_write.v1",
        "status": "written",
        "latest_path": str(latest_path),
        "run_path": str(run_path),
        "report_status": report["status"],
        "record_count": report["record_count"],
        "selection_count": report["selection_count"],
        "proposal_count": len(report["training_proposals"]),
        "runtime_mutation": True,
        "guardrails": [
            "LOCAL_RUNTIME_ARTIFACT_ONLY",
            "NO_POSTGRES_WRITE",
            "NO_RUNTIME_DECISION_PROMOTION",
        ],
    }


def read_practitioner_calibration_training_artifact(*, output_dir: Path | None = None) -> dict[str, object]:
    runtime_dir = local_jsonl_store_from_env().runtime_dir
    latest_path = (output_dir or runtime_dir / "training" / "practitioner_calibration") / "latest.json"
    if not latest_path.exists():
        return {
            "version": "v20.practitioner_calibration_training_artifact_status.v1",
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


def _selection_rows(records: list[dict[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for record in records:
        payload = record.get("payload", {})
        if not isinstance(payload, dict):
            continue
        record_id = str(record.get("record_id", ""))
        source_hash = str(payload.get("source_hash", ""))
        for selection in payload.get("selections", ()):
            if not isinstance(selection, dict):
                continue
            rows.append({
                "record_id": record_id,
                "source_hash": source_hash,
                "control_key": str(selection.get("control_key", "")),
                "option": str(selection.get("option", "")),
                "source_decision_keys": tuple(
                    str(key)
                    for key in selection.get("source_decision_keys", ())
                    if str(key)
                ),
            })
    return [row for row in rows if row["control_key"] and row["option"]]


def _control_summaries(selection_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    by_control: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in selection_rows:
        by_control[str(row["control_key"])].append(row)

    summaries = []
    for control_key, rows in sorted(by_control.items()):
        option_counts = Counter(str(row["option"]) for row in rows)
        top_option, top_count = option_counts.most_common(1)[0]
        total = len(rows)
        ratio = round(top_count / total, 4) if total else 0
        decision_keys = tuple(sorted({
            str(key)
            for row in rows
            for key in row.get("source_decision_keys", ())
            if str(key)
        }))
        summaries.append({
            "control_key": control_key,
            "target": _target_for_control(control_key),
            "sample_count": total,
            "option_counts": dict(sorted(option_counts.items())),
            "top_option": top_option,
            "top_option_count": top_count,
            "top_option_ratio": ratio,
            "source_decision_keys": decision_keys,
            "promotion_candidate": total >= MIN_PROMOTION_SAMPLES and ratio >= MIN_PROMOTION_RATIO,
            "runtime_allowed": True,
        })
    return summaries


def _training_proposals(control_summaries: list[dict[str, object]]) -> list[dict[str, object]]:
    proposals = []
    for summary in control_summaries:
        candidate = bool(summary.get("promotion_candidate"))
        proposals.append({
            "proposal_type": "decision_parameter_calibration",
            "target": summary["target"],
            "control_key": summary["control_key"],
            "suggested_option": summary["top_option"],
            "sample_count": summary["sample_count"],
            "support_ratio": summary["top_option_ratio"],
            "status": "candidate" if candidate else "collect_more_signals",
            "next_gate": "synthetic_validation_and_rule_portrait_batch" if candidate else "more_practitioner_samples",
            "runtime_allowed": True,
        })
    return proposals


def _target_for_control(control_key: str) -> str:
    return {
        "control.day_master_strength": "decision_parameters.strength_capacity",
        "control.shang_guan_jian_guan": "decision_parameters.ten_god_collision",
        "control.wealth_capacity": "decision_parameters.wealth_capacity",
        "control.pattern_status": "decision_parameters.pattern_status",
    }.get(control_key, "decision_parameters")


def _emit(progress: ProgressCallback | None, message: str) -> None:
    if progress is not None:
        progress(message)
