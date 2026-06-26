from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from v20.storage.local_jsonl import LocalJsonlStore, local_jsonl_store_from_env


ProgressCallback = Callable[[str], None]

LEDGER_NAME = "orchestrator_memory_ledger"
MIN_REVIEW_SAMPLES = 3
MIN_DIRECTION_RATIO = 0.66


def build_orchestrator_memory_training_report(
    *,
    store: LocalJsonlStore | None = None,
    signals: tuple[dict[str, object], ...] | None = None,
    progress: ProgressCallback | None = None,
) -> dict[str, object]:
    storage = store or local_jsonl_store_from_env()
    records = [] if signals is not None else _read_records(storage)
    memory_rows = list(signals) if signals is not None else _memory_rows(records)
    _emit(progress, f"orchestrator memory signals: {len(memory_rows)}")
    signal_rows = _signal_rows(memory_rows)
    _emit(progress, f"compiled memory signal rows: {len(signal_rows)}")
    mainline_summaries = _mainline_summaries(memory_rows, signal_rows)
    domain_summaries = _domain_summaries(signal_rows)
    training_proposals = _training_proposals(mainline_summaries, domain_summaries)
    return {
        "version": "v20.orchestrator_memory_training_report.v1",
        "status": "ready" if memory_rows else "not_enough_data",
        "ok": True,
        "ledger_name": LEDGER_NAME,
        "record_count": len(records),
        "memory_signal_count": len(memory_rows),
        "compiled_signal_count": len(signal_rows),
        "mainline_summaries": mainline_summaries,
        "domain_summaries": domain_summaries,
        "training_proposals": training_proposals,
        "activation_thresholds": {
            "min_review_samples": MIN_REVIEW_SAMPLES,
            "min_direction_ratio": MIN_DIRECTION_RATIO,
        },
        "training_targets": (
            "mainline_arbitration_weight_policy",
            "question_focus_policy",
            "brain_memory_policy",
        ),
        "runtime_mutation": False,
        "guardrails": [
            "ORCHESTRATOR_MEMORY_TRAINING_IS_OFFLINE_ONLY",
            "NO_RUNTIME_MAINLINE_MUTATION",
            "NO_RUNTIME_RULE_MUTATION",
            "POLICY_PROMOTION_REQUIRES_REVIEW_AND_REPLAY",
        ],
    }


def write_orchestrator_memory_training_artifact(
    *,
    store: LocalJsonlStore | None = None,
    output_dir: Path | None = None,
    progress: ProgressCallback | None = None,
) -> dict[str, object]:
    storage = store or local_jsonl_store_from_env()
    report = build_orchestrator_memory_training_report(store=storage, progress=progress)
    directory = output_dir or storage.runtime_dir / "training" / "orchestrator_memory"
    directory.mkdir(parents=True, exist_ok=True)
    latest_path = directory / "latest.json"
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_path = directory / f"orchestrator_memory_training_{stamp}.json"
    payload = report | {
        "written_at": datetime.now(timezone.utc).isoformat(),
        "runtime_mutation": True,
    }
    latest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    run_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return {
        "version": "v20.orchestrator_memory_training_artifact_write.v1",
        "status": "written",
        "latest_path": str(latest_path),
        "run_path": str(run_path),
        "report_status": report["status"],
        "memory_signal_count": report["memory_signal_count"],
        "compiled_signal_count": report["compiled_signal_count"],
        "proposal_count": len(report["training_proposals"]),
        "runtime_mutation": True,
        "guardrails": [
            "LOCAL_RUNTIME_ARTIFACT_ONLY",
            "NO_POSTGRES_WRITE",
            "NO_RUNTIME_POLICY_PROMOTION",
        ],
    }


def read_orchestrator_memory_training_artifact(*, output_dir: Path | None = None) -> dict[str, object]:
    runtime_dir = local_jsonl_store_from_env().runtime_dir
    latest_path = (output_dir or runtime_dir / "training" / "orchestrator_memory") / "latest.json"
    if not latest_path.exists():
        return {
            "version": "v20.orchestrator_memory_training_artifact_status.v1",
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


def _memory_rows(records: list[dict[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for record in records:
        payload = record.get("payload", {})
        if not isinstance(payload, dict):
            continue
        signal = payload.get("brain_memory_signal", payload)
        if isinstance(signal, dict) and signal.get("version") == "v20.orchestrator_brain_memory_signal.v1":
            rows.append(signal)
    return rows


def _signal_rows(memory_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for memory in memory_rows:
        primary_key = str(memory.get("primary_mainline_key", ""))
        primary_domain = str(memory.get("primary_domain", ""))
        selected_domain = str(memory.get("selected_question_domain", ""))
        coordination_status = str(memory.get("coordination_status", ""))
        for signal in memory.get("signals", ()):
            if not isinstance(signal, dict):
                continue
            rows.append({
                "memory_key": str(memory.get("memory_key", "")),
                "primary_mainline_key": primary_key,
                "primary_domain": primary_domain,
                "selected_question_domain": selected_domain,
                "coordination_status": coordination_status,
                "signal_type": str(signal.get("signal_type", "")),
                "domain": str(signal.get("domain", "")) or selected_domain or primary_domain,
                "direction": str(signal.get("direction", "")),
                "target": str(signal.get("target", "")),
                "strength": _float(signal.get("strength", 0)),
                "allowed_use": str(signal.get("allowed_use", "")),
            })
    return [row for row in rows if row["signal_type"]]


def _mainline_summaries(memory_rows: list[dict[str, object]], signal_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    by_mainline: dict[str, list[dict[str, object]]] = defaultdict(list)
    for memory in memory_rows:
        key = str(memory.get("primary_mainline_key", "")) or "unknown"
        by_mainline[key].append(memory)
    signals_by_mainline: dict[str, list[dict[str, object]]] = defaultdict(list)
    for signal in signal_rows:
        signals_by_mainline[str(signal["primary_mainline_key"]) or "unknown"].append(signal)

    rows = []
    for key, memories in sorted(by_mainline.items()):
        directions = Counter(str(signal.get("direction", "")) for signal in signals_by_mainline.get(key, ()) if signal.get("direction"))
        coordination = Counter(str(memory.get("coordination_status", "")) for memory in memories if memory.get("coordination_status"))
        top_direction, top_count = directions.most_common(1)[0] if directions else ("", 0)
        total_direction = sum(directions.values())
        top_ratio = round(top_count / total_direction, 4) if total_direction else 0
        rows.append({
            "primary_mainline_key": key,
            "sample_count": len(memories),
            "primary_title": _first_text(memories, "primary_title"),
            "primary_domain": _first_text(memories, "primary_domain"),
            "coordination_status_counts": dict(sorted(coordination.items())),
            "direction_counts": dict(sorted(directions.items())),
            "top_direction": top_direction,
            "top_direction_ratio": top_ratio,
            "review_candidate": len(memories) >= MIN_REVIEW_SAMPLES and top_ratio >= MIN_DIRECTION_RATIO,
            "runtime_allowed": False,
        })
    return rows


def _domain_summaries(signal_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    by_domain: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in signal_rows:
        by_domain[str(row.get("domain", "")) or "unknown"].append(row)
    rows = []
    for domain, signals in sorted(by_domain.items()):
        signal_types = Counter(str(row.get("signal_type", "")) for row in signals if row.get("signal_type"))
        directions = Counter(str(row.get("direction", "")) for row in signals if row.get("direction"))
        avg_strength = round(sum(_float(row.get("strength", 0)) for row in signals) / len(signals), 4) if signals else 0
        rows.append({
            "domain": domain,
            "signal_count": len(signals),
            "signal_type_counts": dict(sorted(signal_types.items())),
            "direction_counts": dict(sorted(directions.items())),
            "average_strength": avg_strength,
            "runtime_allowed": False,
        })
    return rows


def _training_proposals(
    mainline_summaries: list[dict[str, object]],
    domain_summaries: list[dict[str, object]],
) -> list[dict[str, object]]:
    proposals = []
    for summary in mainline_summaries:
        if not summary.get("review_candidate"):
            continue
        proposals.append({
            "proposal_type": "orchestrator_mainline_memory_review",
            "target": "mainline_arbitration_weight_policy",
            "primary_mainline_key": summary["primary_mainline_key"],
            "suggested_direction": summary["top_direction"],
            "sample_count": summary["sample_count"],
            "support_ratio": summary["top_direction_ratio"],
            "status": "candidate",
            "next_gate": "offline_replay_and_practitioner_review",
            "runtime_allowed": False,
        })
    for summary in domain_summaries:
        if int(summary.get("signal_count", 0) or 0) < MIN_REVIEW_SAMPLES:
            continue
        proposals.append({
            "proposal_type": "orchestrator_question_focus_memory_review",
            "target": "question_focus_policy",
            "domain": summary["domain"],
            "signal_count": summary["signal_count"],
            "average_strength": summary["average_strength"],
            "status": "collect_for_review",
            "next_gate": "question_ranking_replay",
            "runtime_allowed": False,
        })
    return proposals


def _first_text(rows: list[dict[str, object]], key: str) -> str:
    for row in rows:
        value = str(row.get(key, ""))
        if value:
            return value
    return ""


def _float(value: object) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _emit(progress: ProgressCallback | None, message: str) -> None:
    if progress is not None:
        progress(message)
