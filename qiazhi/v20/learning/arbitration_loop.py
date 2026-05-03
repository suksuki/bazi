from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from v20.api.runtime import run_runtime_from_pillars
from v20.storage.local_jsonl import local_jsonl_store_from_env

ProgressCallback = Callable[[str], None]

ARBITRATION_STATES = {"mixed", "countered", "requires_review", "blocked", "weak_candidate"}

DEFAULT_ARBITRATION_CASES = (
    {
        "case_id": "v20.arbitration.wealth_capacity",
        "pillars": ("甲子", "戊辰", "甲午", "辛酉"),
        "user_text": "看事业和财运的主线冲突",
        "flow_year_pillar": "庚子",
    },
    {
        "case_id": "v20.arbitration.output_authority",
        "pillars": ("庚午", "辛巳", "丁丑", "乙巳"),
        "user_text": "看伤官见官与资源缓冲",
        "luck_pillar": "甲申",
    },
    {
        "case_id": "v20.arbitration.element_health_boundary",
        "pillars": ("壬寅", "甲辰", "丙子", "甲午"),
        "user_text": "看五行偏枯和健康边界",
    },
)


def build_arbitration_loop_report(
    *,
    cases: tuple[dict[str, object], ...] = DEFAULT_ARBITRATION_CASES,
    progress: ProgressCallback | None = None,
) -> dict[str, object]:
    snapshots: list[dict[str, object]] = []
    for index, case in enumerate(cases, start=1):
        _emit(progress, f"arbitration case {index}/{len(cases)}: {case.get('case_id', '')}")
        pillars = tuple(str(row) for row in case.get("pillars", ()))
        if len(pillars) != 4:
            continue
        runtime = run_runtime_from_pillars(
            pillars[0],
            pillars[1],
            pillars[2],
            pillars[3],
            input_id=str(case.get("case_id", "")),
            user_text=str(case.get("user_text", "")),
            flow_year_pillar=str(case.get("flow_year_pillar", "")),
            luck_pillar=str(case.get("luck_pillar", "")),
            flow_month_pillar=str(case.get("flow_month_pillar", "")),
        )
        snapshots.extend(_case_snapshots(str(case.get("case_id", "")), runtime))

    domain_counts: dict[str, int] = {}
    state_counts: dict[str, int] = {}
    for row in snapshots:
        domain = str(row.get("domain", ""))
        state = str(row.get("state", ""))
        domain_counts[domain] = domain_counts.get(domain, 0) + 1
        state_counts[state] = state_counts.get(state, 0) + 1

    return {
        "version": "v20.arbitration_loop_report.v1",
        "status": "needs_review" if snapshots else "clean",
        "snapshot_count": len(snapshots),
        "case_count": len(cases),
        "domain_counts": dict(sorted(domain_counts.items())),
        "state_counts": dict(sorted(state_counts.items())),
        "snapshots": snapshots,
        "training_targets": [
            "counter_evidence_weight",
            "decision_state_transition",
            "topic_projection_weight",
            "question_priority_after_conflict",
            "practitioner_calibration_queue",
        ],
        "quality_findings": (
            [f"arbitration_snapshot_count:{len(snapshots)}"]
            if snapshots
            else []
        ),
        "runtime_mutation": False,
        "guardrails": [
            "ARBITRATION_GAPS_ARE_LEARNING_SIGNALS_NOT_RUNTIME_BLOCKERS",
            "PRACTITIONER_REVISES_WEIGHTS_NOT_CHART_FACTS",
            "CONFLICT_SNAPSHOT_FEEDS_CALIBRATION_AND_REPLAY",
            "NO_DIRECT_FORTUNE_CONCLUSION_FROM_ARBITRATION",
        ],
    }


def write_arbitration_loop_artifact(
    *,
    output_dir: Path | None = None,
    progress: ProgressCallback | None = None,
) -> dict[str, object]:
    report = build_arbitration_loop_report(progress=progress)
    runtime_dir = local_jsonl_store_from_env().runtime_dir
    directory = output_dir or runtime_dir / "training" / "arbitration_loop"
    directory.mkdir(parents=True, exist_ok=True)
    latest_path = directory / "latest.json"
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_path = directory / f"arbitration_loop_{stamp}.json"
    payload = report | {
        "written_at": datetime.now(timezone.utc).isoformat(),
        "runtime_mutation": True,
    }
    latest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    run_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return {
        "version": "v20.arbitration_loop_artifact_write.v1",
        "status": "written",
        "latest_path": str(latest_path),
        "run_path": str(run_path),
        "report_status": report["status"],
        "snapshot_count": report["snapshot_count"],
        "runtime_mutation": True,
        "guardrails": [
            "LOCAL_RUNTIME_ARTIFACT_ONLY",
            "NO_RULE_TRUTH_MUTATION",
            "ACTIVE_ARBITRATION_ITERATION",
        ],
    }


def read_arbitration_loop_artifact(*, output_dir: Path | None = None) -> dict[str, object]:
    runtime_dir = local_jsonl_store_from_env().runtime_dir
    latest_path = (output_dir or runtime_dir / "training" / "arbitration_loop") / "latest.json"
    if not latest_path.exists():
        return {
            "version": "v20.arbitration_loop_artifact_status.v1",
            "status": "not_built",
            "latest_path": str(latest_path),
            "runtime_mutation": False,
        }
    return json.loads(latest_path.read_text(encoding="utf-8")) | {"runtime_mutation": False}


def _case_snapshots(case_id: str, runtime: dict[str, object]) -> list[dict[str, object]]:
    decision_report = runtime.get("decision_report", {})
    if not isinstance(decision_report, dict):
        return []
    model = decision_report.get("defeasible_decision_model", {})
    if not isinstance(model, dict):
        return []
    rows = []
    for argument in model.get("argument_nodes", ()):
        if not isinstance(argument, dict):
            continue
        state = str(argument.get("state", ""))
        if state not in ARBITRATION_STATES:
            continue
        rows.append({
            "snapshot_id": f"{case_id}:{argument.get('argument_id', '')}",
            "case_id": case_id,
            "domain": str(argument.get("domain", "")),
            "state": state,
            "rule_id": str(argument.get("rule_id", "")),
            "title": str(argument.get("title", "")),
            "score": float(argument.get("score", 0.0) or 0.0),
            "support_evidence_atom_ids": tuple(str(row) for row in argument.get("support_evidence_atom_ids", ()) if str(row))[:8],
            "attack_counter_ids": tuple(str(row) for row in argument.get("attack_counter_ids", ()) if str(row)),
            "counter_effects": tuple(str(row) for row in argument.get("counter_effects", ()) if str(row)),
            "feature_ids": tuple(str(row) for row in argument.get("feature_ids", ()) if str(row))[:8],
            "recommended_queue": "practitioner_calibration" if state in {"mixed", "countered", "requires_review"} else "rule_replay_eval",
            "learning_action": _learning_action(state),
            "runtime_mutation": False,
        })
    return rows


def _learning_action(state: str) -> str:
    return {
        "mixed": "calibrate_conflicting_support_and_counter_weights",
        "countered": "increase_counterexample_weight_or_split_condition",
        "requires_review": "request_practitioner_revision_signal",
        "blocked": "keep_boundary_and_collect_replay_cases",
        "weak_candidate": "collect_more_support_or_demote_question_priority",
    }.get(state, "collect_more_signals")


def _emit(progress: ProgressCallback | None, message: str) -> None:
    if progress is not None:
        progress(message)
