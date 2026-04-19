from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v17_rebirth.backend.logic.L0_physics_fields.ten_gods_engine import BRANCH_HIDDEN, STEM_ELEMENT, ten_god_from_stems
from v17_rebirth.backend.logic.plugin_discovery import collect_all_spec_facts


def _seed_scores(day_master: str, branches: List[str], visible_stems: List[str]) -> Dict[str, float]:
    scores: Dict[str, float] = {}
    for branch in branches:
        for hidden_stem, weight in BRANCH_HIDDEN.get(branch, []):
            god = ten_god_from_stems(day_master, hidden_stem)
            scores[god] = scores.get(god, 0.0) + 12.0 * float(weight)
    for stem in visible_stems:
        if not stem:
            continue
        god = ten_god_from_stems(day_master, stem)
        scores[god] = scores.get(god, 0.0) + 10.0
    return {god: round(value, 2) for god, value in scores.items()}


def _build_tensor(
    *,
    year: str,
    month: str,
    day: str,
    hour: str,
    luck_pillar: str,
    flow_pillar: str,
    sanhe_group: List[str],
    blockers: Dict[str, List[Dict[str, Any]]] | None = None,
) -> Dict[str, Any]:
    day_master = str(day)[0]
    branches = [str(year)[1], str(month)[1], str(day)[1], str(hour)[1]]
    stems = [str(year)[0], str(month)[0], str(day)[0], str(hour)[0], str(luck_pillar)[0], str(flow_pillar)[0]]
    scores = _seed_scores(day_master, branches + [str(luck_pillar)[1], str(flow_pillar)[1]], stems)
    return {
        "four_pillars": {"year": year, "month": month, "day": day, "hour": hour},
        "luck_pillar": luck_pillar,
        "flow_pillar": flow_pillar,
        "ten_gods_base_l0": dict(scores),
        "ten_gods_runtime": dict(scores),
        "ten_gods_absolute": dict(scores),
        "meta": {
            "interaction_v2": {
                "liu_chong": list((blockers or {}).get("liu_chong") or []),
                "liu_hai": list((blockers or {}).get("liu_hai") or []),
                "liu_po": list((blockers or {}).get("liu_po") or []),
                "liu_he": list((blockers or {}).get("liu_he") or []),
                "san_he": [{"group": list(sanhe_group), "pillars": ["year", "month", "day"], "origin_type": "natal"}],
                "ban_he": [],
                "sanxing": [],
            }
        },
    }


CASES: List[Dict[str, Any]] = [
    {
        "label": "金局官杀簇",
        "tensor": _build_tensor(
            year="丁巳",
            month="乙酉",
            day="乙丑",
            hour="乙巳",
            luck_pillar="庚子",
            flow_pillar="丙午",
            sanhe_group=["巳", "酉", "丑"],
            blockers={
                "liu_hai": [{"pair": ["丑", "午"], "pillars": ["day", "flow"], "origin_type": "flow_trigger"}],
                "liu_po": [{"pair": ["子", "酉"], "pillars": ["luck", "month"], "origin_type": "luck_background"}],
            },
        ),
    },
    {
        "label": "木局财簇",
        "tensor": _build_tensor(
            year="癸亥",
            month="乙卯",
            day="庚未",
            hour="甲亥",
            luck_pillar="乙酉",
            flow_pillar="丁巳",
            sanhe_group=["亥", "卯", "未"],
        ),
    },
    {
        "label": "水局食伤簇",
        "tensor": _build_tensor(
            year="壬申",
            month="戊子",
            day="庚辰",
            hour="壬申",
            luck_pillar="癸亥",
            flow_pillar="丙午",
            sanhe_group=["申", "子", "辰"],
        ),
    },
    {
        "label": "火局官杀簇",
        "tensor": _build_tensor(
            year="甲寅",
            month="丙午",
            day="辛戌",
            hour="甲寅",
            luck_pillar="丁未",
            flow_pillar="壬子",
            sanhe_group=["寅", "午", "戌"],
        ),
    },
]


def main() -> None:
    rows: List[Dict[str, Any]] = []
    for case in CASES:
        tensor = case["tensor"]
        facts = collect_all_spec_facts(tensor)
        sanhe = [
            {
                "text": fact.text,
                "target_god": str((fact.meta or {}).get("target_god") or ""),
                "projection_share": float((fact.meta or {}).get("projection_share") or 0.0),
                "impact_ratio": float((fact.meta or {}).get("impact_ratio") or 0.0),
                "condition_state": str((fact.meta or {}).get("condition_state") or ""),
                "condition_mode": str((fact.meta or {}).get("condition_mode") or ""),
                "cluster_projection": (fact.meta or {}).get("cluster_projection") or {},
            }
            for fact in facts
            if str(fact.plugin_id or "") == "l1.physics.op_branch_sanhe"
        ]
        rows.append({"label": case["label"], "sanhe_projection": sanhe})
    print(json.dumps({"protocol": "v17.synthetic.sanhe.cluster.v1", "cases": rows}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
