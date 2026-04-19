from __future__ import annotations

import io
import json
import sys
from contextlib import redirect_stdout
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v17_rebirth.backend.api.stream_v17 import _run_v17_physics_core
from v17_rebirth.backend.logic.L1_atomic_ops.l1_meta_hydration import hydrate_v17_physics_tensor


@dataclass
class CalibrationCase:
    label: str
    birth_time: datetime
    gender: str
    flow_year: int


CASES: List[CalibrationCase] = [
    CalibrationCase(
        label="食伤外放格样盘",
        birth_time=datetime(1977, 5, 8, 18, 0, 0),
        gender="male",
        flow_year=2026,
    ),
    CalibrationCase(
        label="冬金官财样盘",
        birth_time=datetime(1982, 11, 15, 5, 30, 0),
        gender="male",
        flow_year=2026,
    ),
    CalibrationCase(
        label="基线测试样盘",
        birth_time=datetime(2024, 1, 1, 12, 0, 0),
        gender="female",
        flow_year=2026,
    ),
]


def _top_match_claims(payload: Dict[str, Any], *, limit: int = 10) -> List[Dict[str, Any]]:
    meta = payload.get("meta") if isinstance(payload.get("meta"), dict) else {}
    claims = meta.get("plugin_claims") if isinstance(meta.get("plugin_claims"), list) else []
    rows: List[Dict[str, Any]] = []
    for row in claims:
        if not isinstance(row, dict):
            continue
        try:
            match_ratio = float(row.get("match_ratio", 0.0) or 0.0)
        except (TypeError, ValueError):
            match_ratio = 0.0
        if match_ratio <= 0.0:
            continue
        rows.append(
            {
                "plugin_id": str(row.get("plugin_id") or "").strip(),
                "target_god": str(row.get("target_god") or "").strip(),
                "claim_type": str(row.get("claim_type") or "").strip(),
                "match_ratio": round(match_ratio, 4),
                "confidence": round(float(row.get("confidence", 0.0) or 0.0), 4),
            }
        )
    rows.sort(key=lambda item: (item["match_ratio"], item["confidence"]), reverse=True)
    return rows[:limit]


def _recompute_rows(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    meta = payload.get("meta") if isinstance(payload.get("meta"), dict) else {}
    rows = meta.get("plugin_recompute_contributions") if isinstance(meta.get("plugin_recompute_contributions"), list) else []
    out: List[Dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        out.append(
            {
                "target_god": str(row.get("target_god") or "").strip(),
                "before": round(float(row.get("before", 0.0) or 0.0), 4),
                "after": round(float(row.get("after", 0.0) or 0.0), 4),
                "ratio_total": round(float(row.get("ratio_total", 0.0) or 0.0), 4),
                "delta_abs": round(float(row.get("delta_abs", 0.0) or 0.0), 4),
            }
        )
    out.sort(key=lambda item: abs(item["delta_abs"]), reverse=True)
    return out


def _plugin_match_summary(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    meta = payload.get("meta") if isinstance(payload.get("meta"), dict) else {}
    claims = meta.get("plugin_claims") if isinstance(meta.get("plugin_claims"), list) else []
    bucket: Dict[str, Dict[str, float | str]] = {}
    for row in claims:
        if not isinstance(row, dict):
            continue
        plugin_id = str(row.get("plugin_id") or "").strip()
        if not plugin_id:
            continue
        try:
            match_ratio = float(row.get("match_ratio", 0.0) or 0.0)
        except (TypeError, ValueError):
            match_ratio = 0.0
        if plugin_id not in bucket:
            bucket[plugin_id] = {"plugin_id": plugin_id, "count": 0.0, "sum_match": 0.0}
        bucket[plugin_id]["count"] = float(bucket[plugin_id]["count"]) + 1.0
        bucket[plugin_id]["sum_match"] = float(bucket[plugin_id]["sum_match"]) + match_ratio
    rows: List[Dict[str, Any]] = []
    for plugin_id, item in bucket.items():
        count = max(1.0, float(item["count"]))
        rows.append(
            {
                "plugin_id": plugin_id,
                "claim_count": int(count),
                "avg_match_ratio": round(float(item["sum_match"]) / count, 4),
            }
        )
    rows.sort(key=lambda item: (item["avg_match_ratio"], item["claim_count"]), reverse=True)
    return rows[:16]


def build_case_report(case: CalibrationCase) -> Dict[str, Any]:
    with redirect_stdout(io.StringIO()):
        payload = _run_v17_physics_core(
            birth_time=case.birth_time,
            gender=case.gender,
            flow_year=case.flow_year,
        )
        hydrate_v17_physics_tensor(payload)
    return {
        "label": case.label,
        "birth_time": case.birth_time.isoformat(),
        "gender": case.gender,
        "flow_year": case.flow_year,
        "four_pillars": payload.get("four_pillars", {}),
        "luck_pillar": payload.get("luck_pillar"),
        "flow_pillar": payload.get("flow_pillar"),
        "pattern": payload.get("hit_pattern_name") or payload.get("pattern"),
        "match_top": _top_match_claims(payload),
        "plugin_match_summary": _plugin_match_summary(payload),
        "recompute_contributions": _recompute_rows(payload),
    }


def main() -> None:
    report = {
        "protocol": "v17.plugin.match_calibration.v1",
        "cases": [build_case_report(case) for case in CASES],
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
