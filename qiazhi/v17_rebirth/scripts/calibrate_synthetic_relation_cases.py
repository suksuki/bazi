from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v17_rebirth.backend.logic.plugin_discovery import collect_all_spec_facts


TARGET_PLUGINS = {
    "l1.physics.op_stem_fusion",
    "l1.physics.op_branch_liuhe",
    "l1.physics.op_branch_liuhai",
    "l1.physics.op_branch_liupo",
}


def _relation_rows(pt: Dict[str, Any]) -> List[Dict[str, Any]]:
    facts = collect_all_spec_facts(pt)
    rows: List[Dict[str, Any]] = []
    for fact in facts:
        plugin_id = str(fact.plugin_id or "")
        if plugin_id not in TARGET_PLUGINS:
            continue
        meta = fact.meta or {}
        rows.append(
            {
                "plugin_id": plugin_id,
                "text": fact.text,
                "target_god": str(meta.get("target_god") or ""),
                "match_ratio": float(meta.get("match_ratio") or 0.0),
                "impact_ratio": float(meta.get("impact_ratio") or 0.0),
                "condition_state": str(meta.get("condition_state") or ""),
                "condition_trigger": str(meta.get("condition_trigger") or ""),
                "origin_type": str(meta.get("origin_type") or ""),
            }
        )
    rows.sort(key=lambda row: (row["plugin_id"], -row["match_ratio"], row["target_god"]))
    return rows


CASES: List[Dict[str, Any]] = [
    {
        "label": "五合不化",
        "tensor": {
            "four_pillars": {"year": "丁巳", "month": "乙酉", "day": "乙丑", "hour": "乙巳"},
            "luck_pillar": "庚子",
            "flow_pillar": "丙午",
            "ten_gods_absolute": {"比肩": 28.0, "正官": 16.0, "七杀": 10.0},
            "ten_gods_base_l0": {"比肩": 28.0, "正官": 16.0, "七杀": 10.0},
            "ten_gods_runtime": {"比肩": 28.0, "正官": 16.0, "七杀": 10.0},
            "meta": {
                "interaction_v2": {"liu_chong": [], "liu_hai": [], "liu_po": [], "liu_he": [], "san_he": [], "ban_he": [], "sanxing": []},
                "stem_fusion_v1": {
                    "cases": [
                        {
                            "pillars": ["month", "luck"],
                            "stems": ["乙", "庚"],
                            "mode": "stuck",
                            "hua_element": "metal",
                            "month_stem_supports": False,
                            "branch_hua_ratio": 0.1667,
                        }
                    ]
                },
            },
        },
    },
    {
        "label": "五合成化",
        "tensor": {
            "four_pillars": {"year": "辛酉", "month": "乙酉", "day": "乙丑", "hour": "庚申"},
            "luck_pillar": "庚辰",
            "flow_pillar": "辛巳",
            "ten_gods_absolute": {"正官": 22.0, "七杀": 17.0, "比肩": 14.0},
            "ten_gods_base_l0": {"正官": 22.0, "七杀": 17.0, "比肩": 14.0},
            "ten_gods_runtime": {"正官": 22.0, "七杀": 17.0, "比肩": 14.0},
            "meta": {
                "interaction_v2": {"liu_chong": [], "liu_hai": [], "liu_po": [], "liu_he": [], "san_he": [], "ban_he": [], "sanxing": []},
                "stem_fusion_v1": {
                    "cases": [
                        {
                            "pillars": ["month", "luck"],
                            "stems": ["乙", "庚"],
                            "mode": "transformed",
                            "hua_element": "metal",
                            "month_stem_supports": False,
                            "branch_hua_ratio": 0.52,
                        }
                    ]
                },
            },
        },
    },
    {
        "label": "六合稳合",
        "tensor": {
            "four_pillars": {"year": "甲子", "month": "乙丑", "day": "丙寅", "hour": "丁卯"},
            "luck_pillar": "戊辰",
            "flow_pillar": "己巳",
            "ten_gods_absolute": {"正官": 18.0, "七杀": 11.0, "食神": 14.0, "偏财": 12.0},
            "ten_gods_base_l0": {"正官": 18.0, "七杀": 11.0, "食神": 14.0, "偏财": 12.0},
            "ten_gods_runtime": {"正官": 18.0, "七杀": 11.0, "食神": 14.0, "偏财": 12.0},
            "meta": {
                "interaction_v2": {
                    "liu_chong": [],
                    "liu_hai": [],
                    "liu_po": [],
                    "liu_he": [{"pair": ["子", "丑"], "pillars": ["year", "month"], "origin_type": "natal"}],
                    "san_he": [],
                    "ban_he": [],
                    "sanxing": [],
                }
            },
        },
    },
    {
        "label": "六合运助",
        "tensor": {
            "four_pillars": {"year": "甲子", "month": "丙寅", "day": "丁卯", "hour": "戊辰"},
            "luck_pillar": "己丑",
            "flow_pillar": "庚午",
            "ten_gods_absolute": {"正官": 18.0, "七杀": 11.0, "食神": 14.0, "偏财": 12.0},
            "ten_gods_base_l0": {"正官": 18.0, "七杀": 11.0, "食神": 14.0, "偏财": 12.0},
            "ten_gods_runtime": {"正官": 18.0, "七杀": 11.0, "食神": 14.0, "偏财": 12.0},
            "meta": {
                "interaction_v2": {
                    "liu_chong": [],
                    "liu_hai": [],
                    "liu_po": [],
                    "liu_he": [{"pair": ["子", "丑"], "pillars": ["year", "luck"], "origin_type": "luck_background"}],
                    "san_he": [],
                    "ban_he": [],
                    "sanxing": [],
                }
            },
        },
    },
    {
        "label": "六合流引",
        "tensor": {
            "four_pillars": {"year": "甲子", "month": "丙寅", "day": "丁卯", "hour": "戊辰"},
            "luck_pillar": "己未",
            "flow_pillar": "庚丑",
            "ten_gods_absolute": {"正官": 18.0, "七杀": 11.0, "食神": 14.0, "偏财": 12.0},
            "ten_gods_base_l0": {"正官": 18.0, "七杀": 11.0, "食神": 14.0, "偏财": 12.0},
            "ten_gods_runtime": {"正官": 18.0, "七杀": 11.0, "食神": 14.0, "偏财": 12.0},
            "meta": {
                "interaction_v2": {
                    "liu_chong": [],
                    "liu_hai": [],
                    "liu_po": [],
                    "liu_he": [{"pair": ["子", "丑"], "pillars": ["year", "flow"], "origin_type": "flow_trigger"}],
                    "san_he": [],
                    "ban_he": [],
                    "sanxing": [],
                }
            },
        },
    },
    {
        "label": "六害暗耗",
        "tensor": {
            "four_pillars": {"year": "甲子", "month": "乙未", "day": "丙寅", "hour": "丁卯"},
            "luck_pillar": "戊辰",
            "flow_pillar": "己巳",
            "ten_gods_absolute": {"正官": 18.0, "七杀": 11.0, "食神": 14.0, "偏财": 12.0},
            "ten_gods_base_l0": {"正官": 18.0, "七杀": 11.0, "食神": 14.0, "偏财": 12.0},
            "ten_gods_runtime": {"正官": 18.0, "七杀": 11.0, "食神": 14.0, "偏财": 12.0},
            "meta": {
                "interaction_v2": {
                    "liu_chong": [],
                    "liu_hai": [{"pair": ["子", "未"], "pillars": ["year", "month"], "origin_type": "natal"}],
                    "liu_po": [],
                    "liu_he": [],
                    "san_he": [],
                    "ban_he": [],
                    "sanxing": [],
                }
            },
        },
    },
    {
        "label": "六害运助",
        "tensor": {
            "four_pillars": {"year": "甲子", "month": "乙卯", "day": "丙寅", "hour": "丁卯"},
            "luck_pillar": "戊未",
            "flow_pillar": "己巳",
            "ten_gods_absolute": {"正官": 18.0, "七杀": 11.0, "食神": 14.0, "偏财": 12.0},
            "ten_gods_base_l0": {"正官": 18.0, "七杀": 11.0, "食神": 14.0, "偏财": 12.0},
            "ten_gods_runtime": {"正官": 18.0, "七杀": 11.0, "食神": 14.0, "偏财": 12.0},
            "meta": {
                "interaction_v2": {
                    "liu_chong": [],
                    "liu_hai": [{"pair": ["子", "未"], "pillars": ["year", "luck"], "origin_type": "luck_background"}],
                    "liu_po": [],
                    "liu_he": [],
                    "san_he": [],
                    "ban_he": [],
                    "sanxing": [],
                }
            },
        },
    },
    {
        "label": "六害流引",
        "tensor": {
            "four_pillars": {"year": "甲子", "month": "乙卯", "day": "丙寅", "hour": "丁卯"},
            "luck_pillar": "戊辰",
            "flow_pillar": "己未",
            "ten_gods_absolute": {"正官": 18.0, "七杀": 11.0, "食神": 14.0, "偏财": 12.0},
            "ten_gods_base_l0": {"正官": 18.0, "七杀": 11.0, "食神": 14.0, "偏财": 12.0},
            "ten_gods_runtime": {"正官": 18.0, "七杀": 11.0, "食神": 14.0, "偏财": 12.0},
            "meta": {
                "interaction_v2": {
                    "liu_chong": [],
                    "liu_hai": [{"pair": ["子", "未"], "pillars": ["year", "flow"], "origin_type": "flow_trigger"}],
                    "liu_po": [],
                    "liu_he": [],
                    "san_he": [],
                    "ban_he": [],
                    "sanxing": [],
                }
            },
        },
    },
    {
        "label": "六破轻损",
        "tensor": {
            "four_pillars": {"year": "甲子", "month": "乙酉", "day": "丙寅", "hour": "丁卯"},
            "luck_pillar": "戊辰",
            "flow_pillar": "己巳",
            "ten_gods_absolute": {"正官": 18.0, "七杀": 11.0, "食神": 14.0, "偏财": 12.0},
            "ten_gods_base_l0": {"正官": 18.0, "七杀": 11.0, "食神": 14.0, "偏财": 12.0},
            "ten_gods_runtime": {"正官": 18.0, "七杀": 11.0, "食神": 14.0, "偏财": 12.0},
            "meta": {
                "interaction_v2": {
                    "liu_chong": [],
                    "liu_hai": [],
                    "liu_po": [{"pair": ["子", "酉"], "pillars": ["year", "month"], "origin_type": "natal"}],
                    "liu_he": [],
                    "san_he": [],
                    "ban_he": [],
                    "sanxing": [],
                }
            },
        },
    },
    {
        "label": "六破运助",
        "tensor": {
            "four_pillars": {"year": "甲子", "month": "乙卯", "day": "丙寅", "hour": "丁卯"},
            "luck_pillar": "戊酉",
            "flow_pillar": "己巳",
            "ten_gods_absolute": {"正官": 18.0, "七杀": 11.0, "食神": 14.0, "偏财": 12.0},
            "ten_gods_base_l0": {"正官": 18.0, "七杀": 11.0, "食神": 14.0, "偏财": 12.0},
            "ten_gods_runtime": {"正官": 18.0, "七杀": 11.0, "食神": 14.0, "偏财": 12.0},
            "meta": {
                "interaction_v2": {
                    "liu_chong": [],
                    "liu_hai": [],
                    "liu_po": [{"pair": ["子", "酉"], "pillars": ["year", "luck"], "origin_type": "luck_background"}],
                    "liu_he": [],
                    "san_he": [],
                    "ban_he": [],
                    "sanxing": [],
                }
            },
        },
    },
    {
        "label": "六破流引",
        "tensor": {
            "four_pillars": {"year": "甲子", "month": "乙卯", "day": "丙寅", "hour": "丁卯"},
            "luck_pillar": "戊辰",
            "flow_pillar": "己酉",
            "ten_gods_absolute": {"正官": 18.0, "七杀": 11.0, "食神": 14.0, "偏财": 12.0},
            "ten_gods_base_l0": {"正官": 18.0, "七杀": 11.0, "食神": 14.0, "偏财": 12.0},
            "ten_gods_runtime": {"正官": 18.0, "七杀": 11.0, "食神": 14.0, "偏财": 12.0},
            "meta": {
                "interaction_v2": {
                    "liu_chong": [],
                    "liu_hai": [],
                    "liu_po": [{"pair": ["子", "酉"], "pillars": ["year", "flow"], "origin_type": "flow_trigger"}],
                    "liu_he": [],
                    "san_he": [],
                    "ban_he": [],
                    "sanxing": [],
                }
            },
        },
    },
]


def main() -> None:
    payload = {
        "protocol": "v17.synthetic.relation_focus.v1",
        "cases": [{"label": case["label"], "facts": _relation_rows(case["tensor"])} for case in CASES],
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
