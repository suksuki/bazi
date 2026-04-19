from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Sequence

from v17_rebirth.backend.logic.L1_atomic_ops.plugin_condition_protocol import (
    choose_dominant_origin_type,
    collect_origin_types_from_rows,
    relation_origin_multiplier,
)
from v17_rebirth.backend.logic.L1_atomic_ops.relation_cluster_projection import god_cluster_projection
from v17_rebirth.backend.logic.plugin_discovery import deity_scores_from_tensor, rows_dict_to_v17_facts
from v17_rebirth.backend.plugins.spec import V17Fact, V17PluginSpec

# V17.99 Skill Specification
V17_SKILL_MANIFEST = {
    "id": "ten_god_pattern",
    "Layer": "L2",
    "Skill_Type": "Pattern",
    "Domain": "Logic",
    "Description": "在十神分布上给出主轴观察与家族混合摘要，不再输出旧式格局 headline。",
    "Rationale": "十神主轴只负责结构观察，古典格局解释权统一交给 classical.pattern.* 链路。"
}

DECLARED_PARAMS = {
    "GUAN_THRESHOLD": 40.0,        # 正官格激活能量阈值
    "SHI_SHANG_THRESHOLD": 35.0,   # 食伤格激活能量阈值
    "CAI_THRESHOLD": 35.0,         # 财星格激活能量阈值
    "PATTERN_PRIORITY": 0.78       # 事实输出优先级
}


PATTERN_FAMILY_MAP = {
    "正官": "官杀主轴",
    "七杀": "官杀主轴",
    "食神": "食伤主轴",
    "伤官": "食伤主轴",
    "偏财": "财星主轴",
    "正财": "财星主轴",
    "正印": "印星主轴",
    "偏印": "印星主轴",
    "比肩": "比劫主轴",
    "劫财": "比劫主轴",
}


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def judge_ten_god_pattern(deity_scores: Dict[str, float], cfg: Dict[str, Any] = {}) -> str:
    if not deity_scores:
        return "未定主轴"
    
    gt = float(cfg.get("GUAN_THRESHOLD", DECLARED_PARAMS["GUAN_THRESHOLD"]))
    st = float(cfg.get("SHI_SHANG_THRESHOLD", DECLARED_PARAMS["SHI_SHANG_THRESHOLD"]))
    ct = float(cfg.get("CAI_THRESHOLD", DECLARED_PARAMS["CAI_THRESHOLD"]))

    top = sorted(deity_scores.items(), key=lambda kv: kv[1], reverse=True)
    name, score = top[0]
    if name == "正官" and score >= gt:
        return "官杀主轴"
    if name in {"食神", "伤官"} and score >= st:
        return "食伤主轴"
    if name in {"偏财", "正财"} and score >= ct:
        return "财星主轴"
    return PATTERN_FAMILY_MAP.get(name, f"{name}主轴")


def _build_pattern_profile(
    deity_scores: Dict[str, float],
    cfg: Dict[str, Any],
) -> List[Dict[str, Any]]:
    raw_top = sorted(deity_scores.items(), key=lambda kv: float(kv[1]), reverse=True)
    min_score = float(cfg.get("PROFILE_MIN_SCORE", 10.0))
    top_count = int(cfg.get("PROFILE_TOP_GODS", 3))
    ranked: Sequence[tuple[str, float]] = tuple((str(name), float(score)) for name, score in raw_top if float(score) >= min_score)
    if not ranked:
        return []
    selected = list(ranked[: top_count]) if top_count > 0 else list(ranked)
    family_scores: Dict[str, Dict[str, Any]] = {}
    for god, score in selected:
        family = PATTERN_FAMILY_MAP.get(god, "综合格局")
        entry = family_scores.setdefault(family, {"score": 0.0, "gods": []})
        entry["score"] += score
        entry["gods"].append(god)
    total = sum(float(v["score"]) for v in family_scores.values())
    if total <= 0:
        return []
    out: List[Dict[str, Any]] = []
    for family, payload in sorted(family_scores.items(), key=lambda item: float(item[1]["score"]), reverse=True):
        share = float(payload["score"]) / total
        out.append(
            {
                "family": family,
                "gods": payload["gods"],
                "score": round(float(payload["score"]), 3),
                "share": round(share, 4),
                "percent": round(share * 100.0, 1),
            }
        )
    return out


def _format_pattern_profile_text(profile: List[Dict[str, Any]], primary: str) -> str:
    if not profile:
        return f"十神主轴暂定：{primary}，当前更适合作为结构观察。"
    compact = " / ".join(f"{item['family']} {int(item['percent']) if item['percent'].is_integer() else item['percent']}%" for item in profile)
    if len(profile) == 1:
        return f"十神主轴表述：{compact}，当前以{primary}为中心。"
    return f"十神主轴表述：{compact}；当前以{primary}为主向。"


def _collect_rows(deity_scores: Dict[str, float], cfg: Dict[str, Any] = {}) -> List[dict]:
    prio = float(cfg.get("PATTERN_PRIORITY", DECLARED_PARAMS["PATTERN_PRIORITY"]))
    pattern = judge_ten_god_pattern(deity_scores, cfg)
    if pattern == "未定主轴":
        return []
    top = sorted(deity_scores.items(), key=lambda kv: kv[1], reverse=True)
    target_god = str(top[0][0]) if top else ""
    top_score = float(top[0][1]) if top else 0.0
    second_score = float(top[1][1]) if len(top) >= 2 else 0.0
    dominant_ratio = top_score / max(second_score, 1.0) if top_score else 0.0
    profile = _build_pattern_profile(deity_scores, cfg)
    origin_scale = max(0.92, float(cfg.get("AXIS_ORIGIN_SCALE_MIN", 0.92)))
    dominant_share = profile[0]["share"] if profile else 0.5
    match_ratio = min(0.92, max(0.45, dominant_share * _clamp01(origin_scale)))
    if not profile:
        profile = [
            {
                "family": PATTERN_FAMILY_MAP.get(target_god, pattern),
                "gods": [target_god] if target_god else [],
                "score": round(top_score, 3),
                "share": 1.0,
                "percent": 100.0,
            }
        ]
    return [
        {
            "plugin": "ten_god_pattern",
            "fact": _format_pattern_profile_text(profile, pattern),
                "label": "围绕主轴格局统一资源优先级，避免多线分散。",
                "priority": prio,
                "meta": {
                    "observe_only": True,
                    "claim_type": "pattern_observation",
                    "entity_scope": "pattern",
                    "exclusivity_key": "pattern_family",
                    "source_event": "pattern_family",
                    "pattern_name": pattern,
                    "target_god": target_god,
                    "pattern_profile": profile,
                    "dominant_ratio": round(dominant_ratio, 3),
                "match_ratio": round(match_ratio, 3),
                "pattern_mix_mode": "soft_mix",
            },
        }
    ]


def _pattern_origin_meta(physics_tensor: Dict[str, Any]) -> Dict[str, Any]:
    meta = physics_tensor.get("meta") if isinstance(physics_tensor.get("meta"), dict) else {}
    iv2 = meta.get("interaction_v2") if isinstance(meta.get("interaction_v2"), dict) else {}
    origins: List[str] = []
    origins.extend(collect_origin_types_from_rows(iv2.get("liu_chong") or [], member_key="pair"))
    origins.extend(collect_origin_types_from_rows(iv2.get("liu_hai") or [], member_key="pair"))
    origins.extend(collect_origin_types_from_rows(iv2.get("liu_po") or [], member_key="pair"))
    origins.extend(collect_origin_types_from_rows(iv2.get("sanxing") or [], member_key="branches"))
    origin_type = choose_dominant_origin_type(origins) if origins else "natal"
    return {
        "origin_type": origin_type,
        "origin_multiplier": relation_origin_multiplier(origin_type),
    }


def _projection_meta(physics_tensor: Dict[str, Any], target_god: str) -> Dict[str, Any]:
    four = physics_tensor.get("four_pillars") if isinstance(physics_tensor.get("four_pillars"), dict) else {}
    day_gz = str(four.get("day", "")).strip()
    daymaster = day_gz[0] if len(day_gz) >= 2 else "壬"
    month_gz = str(four.get("month", "")).strip()
    month_branch = month_gz[1] if len(month_gz) >= 2 else ""
    projection = god_cluster_projection(
        physics_tensor=physics_tensor,
        base_god=target_god,
        day_master=daymaster,
        focus_branches=[month_branch] if month_branch else [],
    )
    return {
        "target_god": target_god,
        "projection_share": round(float((projection or {}).get(target_god, 1.0)), 4),
        "cluster_projection": projection,
    }


@dataclass
class TenGodPatternPlugin(V17PluginSpec):
    plugin_id: str = "ten_god_pattern"
    causal_tier: int = 3
    registry_priority: float = 0.55

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        from v17_rebirth.backend.logic.configs.manager import get_plugin_config
        cfg = get_plugin_config(self.plugin_id)
        scores = deity_scores_from_tensor(physics_tensor)
        origin_meta = _pattern_origin_meta(physics_tensor)
        rows = _collect_rows(scores, cfg)
        for row in rows:
            if not isinstance(row.get("meta"), dict):
                row["meta"] = {}
            target_god = str(row["meta"].get("target_god") or "")
            if target_god:
                row["meta"].update(_projection_meta(physics_tensor, target_god))
            base_match = float(row["meta"].get("match_ratio", 0.6) or 0.6)
            row["meta"]["match_ratio"] = round(min(0.92, base_match * max(0.92, float(origin_meta["origin_multiplier"]))), 3)
            row["meta"]["origin_type"] = origin_meta["origin_type"]
            row["meta"]["origin_multiplier"] = round(float(origin_meta["origin_multiplier"]), 3)
        return rows_dict_to_v17_facts(rows, causal_tier=self.causal_tier, default_plugin_id=self.plugin_id)


PLUGIN = TenGodPatternPlugin()
