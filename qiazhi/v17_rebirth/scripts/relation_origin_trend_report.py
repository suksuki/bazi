from __future__ import annotations

import json
import math
import statistics
import sys
from collections import defaultdict
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v17_rebirth.backend.logic.plugin_discovery import collect_all_spec_facts
from v17_rebirth.backend.logic.L1_atomic_ops.plugin_condition_protocol import relation_origin_multiplier

from v17_rebirth.scripts import calibrate_synthetic_relation_cases
from v17_rebirth.scripts import calibrate_synthetic_sanhe_cases


RELATION_PLUGINS = {
    "l1.physics.op_branch_liuhe",
    "l1.physics.op_branch_liuhai",
    "l1.physics.op_branch_liupo",
    "l1.physics.op_branch_liuchong",
    "l1.physics.op_branch_sanhe",
    "l1.physics.op_stem_fusion",
    "l1.physics.op_branch_muku",
}

ORIGIN_PRIORITY = ["natal", "luck_background", "mixed", "runtime_pair", "flow_trigger", "flow_only", "unknown"]


def _safe_float(value: Any, fallback: float = 0.0) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return float(fallback)


def _extract_relation_facts(tensor: Dict[str, Any]) -> List[Dict[str, Any]]:
    facts = collect_all_spec_facts(tensor)
    rows: List[Dict[str, Any]] = []
    for fact in facts:
        plugin_id = str(fact.plugin_id or "").strip()
        if plugin_id not in RELATION_PLUGINS:
            continue
        meta = fact.meta or {}
        row = {
            "plugin_id": plugin_id,
            "text": str(fact.text or ""),
            "target_god": str(meta.get("target_god") or ""),
            "match_ratio": _safe_float(meta.get("match_ratio"), 0.0),
            "origin_type": str(meta.get("origin_type") or "unknown").strip() or "unknown",
            "condition_state": str(meta.get("condition_state") or ""),
        }
        rows.append(row)
    return rows


def _relation_family_signature(case: Mapping[str, Any], relation_rows: List[Dict[str, Any]]) -> List[str]:
    signatures = []
    for row in relation_rows:
        key = f"{row['plugin_id']}::{row['target_god']}"
        signatures.append(key)
    signatures.sort()
    return signatures


def _collect_base_cases() -> List[Dict[str, Any]]:
    cases = []
    for item in calibrate_synthetic_relation_cases.CASES:
        cases.append(
            {
                "case_id": f"rel::{item['label']}",
                "label": item["label"],
                "tensor": deepcopy(item["tensor"]),
            }
        )
    for item in calibrate_synthetic_sanhe_cases.CASES:
        cases.append(
            {
                "case_id": f"sanhe::{item['label']}",
                "label": item["label"],
                "tensor": deepcopy(item["tensor"]),
            }
        )
    return cases


def _clone_with_scores(tensor: Dict[str, Any], scale: float) -> Dict[str, Any]:
    mutated = deepcopy(tensor)
    base = mutated.get("ten_gods_base_l0")
    if isinstance(base, dict):
        mutated["ten_gods_base_l0"] = {k: v * scale for k, v in base.items()}
        mutated["ten_gods_absolute"] = {k: v * scale for k, v in base.items()}
        mutated["ten_gods_runtime"] = {k: v * scale for k, v in base.items()}
    return mutated


def _replace_origin_type(tensor: Dict[str, Any], *, new_origin: str) -> Dict[str, Any]:
    mutated = deepcopy(tensor)
    meta = mutated.get("meta")
    if not isinstance(meta, dict):
        return mutated
    iv2 = meta.get("interaction_v2")
    if not isinstance(iv2, dict):
        return mutated
    target_keys = ("liu_he", "liu_hai", "liu_po", "liu_chong", "san_he")
    replaced = False
    for key in target_keys:
        rows = iv2.get(key)
        if not isinstance(rows, list):
            continue
        for row in rows:
            if isinstance(row, dict):
                row["origin_type"] = new_origin
                replaced = True
    if replaced:
        return mutated
    return mutated


def _normalize_origin(origin: str) -> str:
    if not origin:
        return "unknown"
    return str(origin).strip()


def _group_metrics(rows: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    bucket: Dict[str, List[float]] = defaultdict(list)
    for row in rows:
        bucket[row["origin_type"]].append(_safe_float(row["match_ratio"]))

    out: List[Dict[str, Any]] = []
    total = sum(len(values) for values in bucket.values())
    for origin, values in bucket.items():
        if not values:
            continue
        out.append(
            {
                "origin_type": origin,
                "fact_count": len(values),
                "share": round(len(values) / total, 4) if total else 0.0,
                "avg_match_ratio": round(statistics.mean(values), 4),
                "max_match_ratio": round(max(values), 4),
                "origin_multiplier": relation_origin_multiplier(origin),
            }
        )
    out.sort(key=lambda item: item["avg_match_ratio"], reverse=True)
    return out


def _per_plugin_metrics(rows: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    bucket: Dict[str, List[float]] = defaultdict(list)
    for row in rows:
        bucket[row["plugin_id"]].append(_safe_float(row["match_ratio"]))

    out: List[Dict[str, Any]] = []
    for plugin_id, values in bucket.items():
        out.append(
            {
                "plugin_id": plugin_id,
                "fact_count": len(values),
                "avg_match_ratio": round(statistics.mean(values), 4),
                "max_match_ratio": round(max(values), 4),
            }
        )
    out.sort(key=lambda item: item["avg_match_ratio"], reverse=True)
    return out


def _evaluate_case(case: Dict[str, Any]) -> Dict[str, Any]:
    tensor = case["tensor"]
    rows = _extract_relation_facts(tensor)
    origin_summary = _group_metrics(rows)
    plugin_summary = _per_plugin_metrics(rows)
    return {
        "case_id": str(case["case_id"]),
        "label": str(case["label"]),
        "relation_count": len(rows),
        "relation_plugins": sorted({row["plugin_id"] for row in rows}),
        "relation_signatures": _relation_family_signature(case, rows),
        "relation_signature_count": len(_relation_family_signature(case, rows)),
        "top_match": max(rows, key=lambda row: _safe_float(row.get("match_ratio"), 0.0), default=None),
        "origin_summary": origin_summary,
        "plugin_summary": plugin_summary,
        "rows": rows,
    }


def _build_trend_rows(base_cases: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    trend_rows: List[Dict[str, Any]] = []
    for index, case in enumerate(base_cases):
        tensor = case["tensor"]
        trend_rows.append(_evaluate_case(case))
        scales = (0.95, 1.05)
        for i, scale in enumerate(scales):
            trend_rows.append(_evaluate_case({
                "case_id": f"{case['case_id']}:scale={scale:.2f}:{i}",
                "label": f"{case['label']}（强度变体 {i+1}）",
                "tensor": _clone_with_scores(tensor, scale),
            }))

        if index % 2 == 0:
            trend_rows.append(_evaluate_case({
                "case_id": f"{case['case_id']}:origin=natal",
                "label": f"{case['label']}（natal 重打）",
                "tensor": _replace_origin_type(tensor, new_origin="natal"),
            }))
        if index % 3 == 0:
            trend_rows.append(_evaluate_case({
                "case_id": f"{case['case_id']}:origin=luck_background",
                "label": f"{case['label']}（luck_background 重打）",
                "tensor": _replace_origin_type(tensor, new_origin="luck_background"),
            }))
        if index % 4 == 0:
            trend_rows.append(_evaluate_case({
                "case_id": f"{case['case_id']}:origin=flow_trigger",
                "label": f"{case['label']}（flow_trigger 重打）",
                "tensor": _replace_origin_type(tensor, new_origin="flow_trigger"),
            }))

    if len(trend_rows) < 50:
        more_rows: List[Dict[str, Any]] = []
        for case in base_cases:
            for bonus_scale in (0.9, 1.0, 1.1, 1.2):
                if len(trend_rows) >= 50:
                    break
                more_rows.append(
                    _evaluate_case({
                        "case_id": f"{case['case_id']}:bonus={bonus_scale}",
                        "label": f"{case['label']}（扩展变体）",
                        "tensor": _clone_with_scores(case["tensor"], bonus_scale),
                    })
                )
            if len(trend_rows) >= 50:
                break
        trend_rows.extend(more_rows)

    return trend_rows[:50]


def _summary(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    flat_rows = [row for row in rows for row in row.get("rows", []) if isinstance(row, dict)]
    origin_distribution = _group_metrics(flat_rows)
    plugin_distribution = _per_plugin_metrics(flat_rows)

    compliance: List[Dict[str, Any]] = []
    for row in rows:
        for plugin_id in row.get("relation_plugins", []):
            plugin_rows = [r for r in row.get("rows", []) if r.get("plugin_id") == plugin_id]
            if len(plugin_rows) < 2:
                continue
            by_origin: Dict[str, float] = {}
            for plugin_row in plugin_rows:
                origin_type = _normalize_origin(plugin_row.get("origin_type", ""))
                by_origin[origin_type] = max(
                    by_origin.get(origin_type, 0.0),
                    _safe_float(plugin_row.get("match_ratio")),
                )
            sorted_candidates = sorted(
                by_origin.items(),
                key=lambda item: (ORIGIN_PRIORITY.index(item[0]) if item[0] in ORIGIN_PRIORITY else len(ORIGIN_PRIORITY)),
            )
            if len(sorted_candidates) >= 2:
                first_origin = sorted_candidates[0][0]
                last_origin = sorted_candidates[-1][0]
                if by_origin[first_origin] < by_origin[last_origin]:
                    compliance.append(
                        {
                            "case_id": str(row["case_id"]),
                            "plugin_id": plugin_id,
                            "warning": f"高优先级来源{first_origin}命中度低于低优先级来源{last_origin}",
                            "high_origin_match": by_origin[first_origin],
                            "low_origin_match": by_origin[last_origin],
                        }
                    )

    return {
        "case_count": len(rows),
        "relation_fact_total": len(flat_rows),
        "origin_distribution": origin_distribution,
        "plugin_distribution": plugin_distribution,
        "compliance": {
            "priority_violations": compliance,
            "violation_count": len(compliance),
        },
    }


def main() -> None:
    base_cases = _collect_base_cases()
    trend_rows = _build_trend_rows(base_cases)
    summary = _summary(trend_rows)
    payload = {
        "protocol": "v17.relation.origin.trend.v1",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "cases": [
            {
                "case_id": row["case_id"],
                "label": row["label"],
                "relation_count": row["relation_count"],
                "relation_plugins": row["relation_plugins"],
                "top_match": row["top_match"],
                "origin_summary": row["origin_summary"],
                "plugin_summary": row["plugin_summary"],
            }
            for row in trend_rows
        ],
        "summary": summary,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
