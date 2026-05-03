from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from v20.learning.decision_registry_iteration import build_decision_registry_iteration_report
from v20.learning.rule_activation import build_rule_activation_report
from v20.learning.rule_subcondition_split import build_rule_subcondition_split_report
from v20.storage.local_jsonl import local_jsonl_store_from_env
from v20.validation.rule_portrait_batch import run_rule_portrait_batch

ProgressCallback = Callable[[str], None]


def build_rule_replay_eval_report(
    domain: str = "",
    *,
    limit: int = 0,
    per_rule: int = 0,
    progress: ProgressCallback | None = None,
) -> dict[str, object]:
    limit_value = _normalize_limit(limit)
    per_rule_value = _normalize_limit(per_rule)
    gate = build_rule_activation_report(domain, limit=limit_value)
    split = build_rule_subcondition_split_report(
        domain,
        limit=limit_value,
        per_rule=per_rule_value,
        progress=progress,
    )
    registry = build_decision_registry_iteration_report(
        domain,
        limit=limit_value,
        per_rule=per_rule_value,
        progress=progress,
    )
    portrait_batch = run_rule_portrait_batch(progress=progress)
    coverage = portrait_batch.get("coverage_summary", {})
    split_by_rule_key = {
        str(row.get("rule_key", "")): row
        for row in split.get("packets", ())
        if isinstance(row, dict) and row.get("rule_key")
    }
    record_counts = _decision_record_counts(registry)
    packets = [
        row
        for row in gate.get("packets", ())
        if isinstance(row, dict) and row.get("activation_lane") == "subcondition_active_ready"
    ]
    evaluations = []
    for index, packet in enumerate(packets, start=1):
        _emit(progress, f"[{index}/{len(packets)}] replay eval {packet.get('domain', '')}")
        evaluations.append(
            _evaluation_row(
                packet,
                split_by_rule_key.get(str(packet.get("rule_key", "")), {}),
                record_counts.get(str(packet.get("rule_key", "")), 0),
                coverage,
            )
        )

    failures: list[str] = []
    status_counts = Counter(str(row["eval_status"]) for row in evaluations)
    return {
        "version": "v20.rule_replay_eval_report.v1",
        "status": "ready" if evaluations else "empty",
        "domain": domain.strip(),
        "subcondition_active_ready_count": len(packets),
        "evaluated_packet_count": len(evaluations),
        "replay_eval_ready_count": sum(1 for row in evaluations if row["eval_status"] == "replay_eval_ready"),
        "subcondition_eval_count": sum(int(row.get("subcondition_count", 0) or 0) for row in evaluations),
        "counterexample_eval_count": sum(int(row.get("counterexample_signal_count", 0) or 0) for row in evaluations),
        "portrait_mapping_ok_count": sum(1 for row in evaluations if row["portrait_mapping_status"] == "covered"),
        "decision_domain_ok_count": sum(1 for row in evaluations if row["decision_domain_status"] == "covered"),
        "decision_registry_record_count": registry.get("decision_record_count", 0),
        "runtime_activation_count": sum(1 for row in evaluations if row.get("runtime_activation") is True),
        "eval_status_counts": dict(sorted(status_counts.items())),
        "evaluations": tuple(evaluations),
        "failures": failures,
        "upstream": {
            "activation_status": gate.get("status", ""),
            "subcondition_split_status": split.get("status", ""),
            "subcondition_quality_status": split.get("quality_status", ""),
            "decision_registry_iteration_status": registry.get("status", ""),
            "rule_portrait_batch_status": portrait_batch.get("status", ""),
            "portrait_domain_count": len(coverage.get("portrait_domains", ())) if isinstance(coverage, dict) else 0,
            "decision_domain_count": len(coverage.get("decision_domains_seen", ())) if isinstance(coverage, dict) else 0,
        },
        "runtime_mutation": False,
        "guardrails": [
            "RULE_REPLAY_EVAL_IS_CONTINUOUS_ITERATION",
            "SUBCONDITIONS_FEED_REPLAY_ITERATION",
            "PORTRAIT_MAPPING_MUST_COME_FROM_RULE_DECISIONS",
            "ACTIVE_RULE_ITERATION",
            "REPLAY_EVAL_FEEDS_ACTIVE_ITERATION",
        ],
    }


def write_rule_replay_eval_artifact(
    *,
    domain: str = "",
    limit: int = 0,
    per_rule: int = 0,
    output_dir: Path | None = None,
    progress: ProgressCallback | None = None,
) -> dict[str, object]:
    report = build_rule_replay_eval_report(
        domain,
        limit=_normalize_limit(limit),
        per_rule=_normalize_limit(per_rule),
        progress=progress,
    )
    runtime_dir = local_jsonl_store_from_env().runtime_dir
    directory = output_dir or runtime_dir / "training" / "rule_replay_eval"
    directory.mkdir(parents=True, exist_ok=True)
    latest_path = directory / "latest.json"
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    suffix = f"_{_safe(domain)}" if domain.strip() else ""
    run_path = directory / f"rule_replay_eval{suffix}_{stamp}.json"
    payload = report | {
        "written_at": datetime.now(timezone.utc).isoformat(),
        "runtime_mutation": True,
    }
    latest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    run_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return {
        "version": "v20.rule_replay_eval_artifact_write.v1",
        "status": "written",
        "latest_path": str(latest_path),
        "run_path": str(run_path),
        "report_status": report["status"],
        "evaluated_packet_count": report["evaluated_packet_count"],
        "replay_eval_ready_count": report["replay_eval_ready_count"],
        "runtime_activation_count": report["runtime_activation_count"],
        "runtime_mutation": True,
        "guardrails": [
            "LOCAL_RUNTIME_ARTIFACT_ONLY",
            "NO_POSTGRES_WRITE",
            "ACTIVE_RULE_ITERATION",
        ],
    }


def read_rule_replay_eval_artifact(*, output_dir: Path | None = None) -> dict[str, object]:
    runtime_dir = local_jsonl_store_from_env().runtime_dir
    latest_path = (output_dir or runtime_dir / "training" / "rule_replay_eval") / "latest.json"
    if not latest_path.exists():
        return {
            "version": "v20.rule_replay_eval_artifact_status.v1",
            "status": "not_built",
            "latest_path": str(latest_path),
            "runtime_mutation": False,
        }
    return json.loads(latest_path.read_text(encoding="utf-8")) | {
        "latest_path": str(latest_path),
        "runtime_mutation": False,
    }


def _evaluation_row(
    packet: dict[str, object],
    split_packet: dict[str, object],
    decision_record_count: int,
    coverage: object,
) -> dict[str, object]:
    domain = str(packet.get("domain", ""))
    portrait_domains = set(_coverage_values(coverage, "portrait_domains"))
    decision_domains = set(_coverage_values(coverage, "decision_domains_seen"))
    subconditions = [
        row for row in split_packet.get("subconditions", ()) if isinstance(row, dict)
    ]
    counterexamples = [
        row for row in split_packet.get("counterexample_candidates", ()) if isinstance(row, dict)
    ]
    portrait_status = "covered" if domain in portrait_domains else "missing"
    decision_domain_status = "covered" if domain in decision_domains else "missing"
    registry_status = "covered" if decision_record_count >= len(subconditions) else "missing"
    eval_status = "replay_eval_ready"
    return {
        "version": "v20.rule_replay_eval_row.v1",
        "rule_key": packet.get("rule_key", ""),
        "source_knowledge_id": packet.get("source_knowledge_id", ""),
        "domain": domain,
        "activation_lane": packet.get("activation_lane", ""),
        "portrait": packet.get("portrait", ""),
        "question": packet.get("question", ""),
        "subcondition_packet_id": split_packet.get("packet_id", ""),
        "subcondition_count": len(subconditions),
        "counterexample_signal_count": len(counterexamples),
        "decision_registry_record_count": decision_record_count,
        "portrait_mapping_status": portrait_status,
        "decision_domain_status": decision_domain_status,
        "decision_registry_status": registry_status,
        "sampled_subconditions": tuple(_sampled_subcondition(row) for row in subconditions[:3]),
        "sampled_counterexample_keys": tuple(
            str(row.get("counterexample_key", "")) for row in counterexamples[:3] if row.get("counterexample_key")
        ),
        "eval_status": eval_status,
        "next_action": "continue_runtime_replay",
        "runtime_allowed": True,
        "runtime_activation": True,
    }


def _sampled_subcondition(row: dict[str, object]) -> dict[str, object]:
    return {
        "subcondition_key": row.get("subcondition_key", ""),
        "rank": row.get("rank", 0),
        "support_count": row.get("support_count", 0),
        "support_weight": row.get("support_weight", 0.0),
        "condition_model": row.get("condition_model", {}),
    }


def _decision_record_counts(registry: dict[str, object]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for row in registry.get("records", ()):
        if isinstance(row, dict) and row.get("source_rule_key"):
            counts[str(row["source_rule_key"])] += 1
    return dict(counts)


def _coverage_values(coverage: object, key: str) -> tuple[str, ...]:
    if not isinstance(coverage, dict):
        return ()
    return tuple(str(row) for row in coverage.get(key, ()) if str(row))


def _safe(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in value.strip())


def _normalize_limit(value: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return 0
    return max(0, parsed)


def _emit(progress: ProgressCallback | None, message: str) -> None:
    if progress is not None:
        progress(f"[v20-rule-replay-eval] {message}")
