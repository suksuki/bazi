from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v17_rebirth.backend.logic.L0_physics_fields.ten_gods_engine import calc_deity_scores
from v17_rebirth.backend.logic.plugin_discovery import collect_all_spec_facts


def _l0_case(*, four_pillars: Dict[str, str], luck_pillar: str, flow_pillar: str, gender: str = "male") -> Dict[str, Any]:
    scores, top, total, meta = calc_deity_scores(
        four_pillars=four_pillars,
        luck_pillar=luck_pillar,
        flow_pillar=flow_pillar,
        gender=gender,
    )
    return {
        "scores": scores,
        "top": top,
        "total": total,
        "meta": meta,
    }


def _sanhe_tensor(
    *,
    four_pillars: Dict[str, str],
    luck_pillar: str,
    flow_pillar: str,
    blockers: Dict[str, List[Dict[str, Any]]] | None = None,
) -> Dict[str, Any]:
    l0 = _l0_case(four_pillars=four_pillars, luck_pillar=luck_pillar, flow_pillar=flow_pillar)
    return {
        "four_pillars": four_pillars,
        "luck_pillar": luck_pillar,
        "flow_pillar": flow_pillar,
        "ten_gods_base_l0": dict(l0["scores"]),
        "ten_gods_runtime": dict(l0["scores"]),
        "ten_gods_absolute": dict(l0["scores"]),
        "meta": {
            "interaction_v2": {
                "liu_chong": list((blockers or {}).get("liu_chong") or []),
                "liu_hai": list((blockers or {}).get("liu_hai") or []),
                "liu_po": list((blockers or {}).get("liu_po") or []),
                "liu_he": list((blockers or {}).get("liu_he") or []),
                "san_he": [{"group": ["巳", "酉", "丑"], "pillars": ["year", "month", "day"], "origin_type": "natal"}],
                "ban_he": [],
                "sanxing": [],
            }
        },
    }


def _sanhe_projection_rows(pt: Dict[str, Any]) -> List[Dict[str, Any]]:
    facts = collect_all_spec_facts(pt)
    rows: List[Dict[str, Any]] = []
    for fact in facts:
        if str(fact.plugin_id or "") != "l1.physics.op_branch_sanhe":
            continue
        meta = fact.meta or {}
        rows.append(
            {
                "target_god": str(meta.get("target_god") or ""),
                "projection_share": float(meta.get("projection_share") or 0.0),
                "match_ratio": float(meta.get("match_ratio") or 0.0),
                "impact_ratio": float(meta.get("impact_ratio") or 0.0),
                "condition_state": str(meta.get("condition_state") or ""),
                "condition_mode": str(meta.get("condition_mode") or ""),
                "cluster_projection": meta.get("cluster_projection") or {},
            }
        )
    rows.sort(key=lambda row: (-row["projection_share"], row["target_god"]))
    return rows


def main() -> None:
    floating_peer = _l0_case(
        four_pillars={"year": "丁巳", "month": "乙巳", "day": "乙丑", "hour": "乙酉"},
        luck_pillar="庚子",
        flow_pillar="丙午",
    )
    rooted_peer = _l0_case(
        four_pillars={"year": "丁卯", "month": "乙卯", "day": "乙未", "hour": "乙亥"},
        luck_pillar="庚子",
        flow_pillar="丙午",
    )

    sanhe_with_geng = _sanhe_tensor(
        four_pillars={"year": "丁巳", "month": "乙巳", "day": "乙丑", "hour": "乙酉"},
        luck_pillar="庚子",
        flow_pillar="丙午",
        blockers={
            "liu_hai": [{"pair": ["丑", "午"], "pillars": ["day", "flow"], "origin_type": "flow_trigger"}],
            "liu_po": [{"pair": ["子", "酉"], "pillars": ["luck", "hour"], "origin_type": "luck_background"}],
        },
    )
    sanhe_without_geng = _sanhe_tensor(
        four_pillars={"year": "丁巳", "month": "乙巳", "day": "乙丑", "hour": "乙酉"},
        luck_pillar="辛亥",
        flow_pillar="丙午",
        blockers={
            "liu_hai": [{"pair": ["丑", "午"], "pillars": ["day", "flow"], "origin_type": "flow_trigger"}],
            "liu_po": [{"pair": ["亥", "巳"], "pillars": ["luck", "month"], "origin_type": "luck_background"}],
        },
    )

    output = {
        "protocol": "v17.synthetic.visibility.v1",
        "cases": {
            "floating_peer_vs_rooted_peer": {
                "floating_peer_chart": {
                    "pillars": "丁巳 / 乙巳 / 乙丑 / 乙酉 · 庚子 / 丙午",
                    "scores": floating_peer["scores"],
                    "top": floating_peer["top"],
                    "total": floating_peer["total"],
                },
                "rooted_peer_chart": {
                    "pillars": "丁卯 / 乙卯 / 乙未 / 乙亥 · 庚子 / 丙午",
                    "scores": rooted_peer["scores"],
                    "top": rooted_peer["top"],
                    "total": rooted_peer["total"],
                },
            },
            "sanhe_visible_geng_projection": {
                "with_visible_geng": {
                    "pillars": "丁巳 / 乙巳 / 乙丑 / 乙酉 · 庚子 / 丙午",
                    "base_scores": sanhe_with_geng["ten_gods_base_l0"],
                    "sanhe_projection": _sanhe_projection_rows(sanhe_with_geng),
                },
                "without_visible_geng": {
                    "pillars": "丁巳 / 乙巳 / 乙丑 / 乙酉 · 辛亥 / 丙午",
                    "base_scores": sanhe_without_geng["ten_gods_base_l0"],
                    "sanhe_projection": _sanhe_projection_rows(sanhe_without_geng),
                },
            },
        },
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
