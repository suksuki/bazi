from __future__ import annotations

from collections import Counter
from typing import Any

from v20.validation.structure_dynamics_synthetic import run_structure_dynamics_synthetic_suite


STRUCTURE_DYNAMICS_LEGACY_V2_SWITCH_VERSION = "v20.structure_dynamics_legacy_v2_switch.v1"


def build_structure_dynamics_legacy_v2_switch_report(*, synthetic_report: dict[str, Any] | None = None) -> dict[str, Any]:
    report = synthetic_report or run_structure_dynamics_synthetic_suite()
    rows = [row for row in report.get("results", ()) if isinstance(row, dict)]
    comparisons = [_comparison_row(row) for row in rows]
    exact = [row for row in comparisons if row["status"] == "same_label"]
    explainable = [row for row in comparisons if row["status"] in {"same_label", "v2_more_specific", "v2_expected_override"}]
    blockers = [row for row in comparisons if row["status"] == "unexplained_conflict"]
    status_counts = Counter(str(row["status"]) for row in comparisons)
    ready = bool(report.get("ok")) and not blockers and len(comparisons) >= 20
    return {
        "version": STRUCTURE_DYNAMICS_LEGACY_V2_SWITCH_VERSION,
        "status": "switch_ready_primary" if ready else "needs_legacy_compat",
        "case_count": len(comparisons),
        "same_label_count": len(exact),
        "explainable_count": len(explainable),
        "unexplained_conflict_count": len(blockers),
        "status_distribution": _counter_rows(status_counts),
        "comparisons": comparisons,
        "switch_policy": {
            "recommended_runtime_field": "primary_dynamic_chain" if ready else "primary_dynamic_chain_with_legacy_debug",
            "keep_legacy_field": "debug_only",
            "ui_primary": "primary_dynamic_chain" if ready else "legacy_dynamic_chain",
            "runtime_primary": "primary_dynamic_chain" if ready else "legacy_dynamic_chain",
            "reason": "v2 synthetic gate passed; runtime primary now reads primary_dynamic_chain backed by dominant_chain_v2" if ready else "keep legacy debug chain until unexplained conflicts are resolved",
        },
        "runtime_mutation": False,
        "guardrails": [
            "SWITCH_REPORT_IS_READ_ONLY",
            "LEGACY_FIELD_DEBUG_ONLY",
            "V2_SWITCH_REQUIRES_SYNTHETIC_GATE_AND_EXPLAINABLE_DIFFS",
            "PRIMARY_DYNAMIC_CHAIN_READS_DOMINANT_CHAIN_V2_WHEN_READY",
        ],
    }


def _comparison_row(row: dict[str, Any]) -> dict[str, Any]:
    observed = row.get("observed", {}) if isinstance(row.get("observed"), dict) else {}
    expected = row.get("expected", {}) if isinstance(row.get("expected"), dict) else {}
    case_id = str(row.get("case_id", ""))
    legacy_label = str(observed.get("legacy_label", ""))
    v2_label = str(observed.get("label", ""))
    expected_label = str(expected.get("expected_label", ""))
    status = _comparison_status(legacy_label=legacy_label, v2_label=v2_label, expected_label=expected_label)
    return {
        "case_id": case_id,
        "status": status,
        "legacy_label": legacy_label,
        "v2_label": v2_label,
        "expected_label": expected_label,
        "legacy_nodes": tuple(str(node) for node in observed.get("legacy_nodes", ()) if str(node)),
        "v2_nodes": tuple(str(node) for node in observed.get("nodes", ()) if str(node)),
        "reason": _status_reason(status),
        "runtime_mutation": False,
    }


def _comparison_status(*, legacy_label: str, v2_label: str, expected_label: str) -> str:
    if legacy_label == v2_label:
        return "same_label"
    if v2_label == expected_label:
        if _is_v2_more_specific(legacy_label=legacy_label, v2_label=v2_label):
            return "v2_more_specific"
        return "v2_expected_override"
    return "unexplained_conflict"


def _is_v2_more_specific(*, legacy_label: str, v2_label: str) -> bool:
    generic_to_specific = {
        "输出制官杀": {"食神制杀", "伤官制杀"},
        "食伤生财": {"食神制杀", "伤官制杀", "财生官/财滋杀"},
        "官印/杀印相生": {"食神制杀", "伤官制杀", "财生官/财滋杀"},
    }
    return v2_label in generic_to_specific.get(legacy_label, set())


def _status_reason(status: str) -> str:
    return {
        "same_label": "旧主链和 v2 命名一致。",
        "v2_more_specific": "v2 基于做功链给出更细机制命名，旧主链保留兼容。",
        "v2_expected_override": "v2 命中合成样本期望，旧主链差异作为可解释兼容差异。",
        "unexplained_conflict": "v2 与期望不一致，不能切换。",
    }.get(status, "")


def _counter_rows(counter: Counter[str]) -> list[dict[str, Any]]:
    total = sum(counter.values())
    return [
        {
            "key": key,
            "count": count,
            "ratio": round(count / max(1, total), 4),
        }
        for key, count in sorted(counter.items(), key=lambda item: (-item[1], item[0]))
    ]
