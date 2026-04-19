from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

from v17_rebirth.backend.logic.L1_atomic_ops.plugin_condition_protocol import (
    build_static_basis,
    choose_dominant_origin_type,
    collect_origin_types_from_rows,
    detect_interaction_layer,
    detect_relation_origin_type,
    relation_origin_multiplier,
)
from v17_rebirth.backend.logic.L1_atomic_ops.relation_cluster_projection import god_cluster_projection
from v17_rebirth.backend.logic.L0_physics_fields.ten_gods_engine import BRANCH_HIDDEN, _parse_gz, ten_god_from_stems
from v17_rebirth.backend.logic.plugin_discovery import deity_scores_from_tensor, rows_dict_to_v17_facts
from v17_rebirth.backend.logic.configs.manager import get_plugin_config
from v17_rebirth.backend.plugins.spec import V17Fact, V17PluginSpec


PATTERN_DEFAULTS = {
    "classical.pattern.dynamic_scope.v1": {
        "SCOPE_MIX_LABEL_BOOST": 1.1,
        "SCOPE_MIN_WEIGHT": 0.06,
        "SCOPE_PRIORITY": 0.72,
        "SCOPE_MATCH_BASE": 0.62,
    },
    "classical.pattern.axis.v1": {
        "CANDIDATE_FOLLOWER_RATIO": 2.0,
        "CANDIDATE_FOLLOWER_SCORE": 35.0,
        "CANDIDATE_OFFICER_WEALTH": 25.0,
        "AXIS_MATCH_BASE": 0.42,
        "AXIS_TOP_SHARE_WEIGHT": 0.5,
        "AXIS_DOMINANT_WEIGHT": 0.25,
        "AXIS_DOMINANT_DIVISOR": 1.5,
        "AXIS_ORIGIN_SCALE_MIN": 0.92,
        "FORMATION_STRENGTH_RATIO": 2.0,
        "FINANCE_STRONG_MATCH_RATIO": 0.6,
    },
    "classical.pattern.congshi.v1": {
        "CONGSHI_RATIO_THRESHOLD": 2.0,
        "CONGSHI_SCORE_THRESHOLD": 35.0,
        "CONGSHI_RATIO_DIVISOR": 2.0,
        "CONGSHI_ORIGIN_SCALE_MIN": 0.92,
        "CONGSHI_STRONG_RATIO": 2.2,
    },
    "classical.pattern.jianlu_yuejie.v1": {
        "JIANLU_MATCH_BASE": 0.82,
        "JIANLU_ORIGIN_SCALE_MIN": 0.92,
    },
    "classical.pattern.finance_officer.v1": {
        "FINANCE_MIN_GOD_SUM": 25.0,
        "FINANCE_MATCH_MIN_ORIGIN_SCALE": 0.92,
    },
    "classical.pattern.wealth_star.v1": {
        "WEALTH_MATCH_BASE": 0.72,
        "WEALTH_MIN_SCORE": 14.0,
        "WEALTH_ORIGIN_SCALE_MIN": 0.92,
    },
    "classical.pattern.seal_star.v1": {
        "SEAL_MATCH_BASE": 0.74,
        "SEAL_MIN_SCORE": 14.0,
        "SEAL_ORIGIN_SCALE_MIN": 0.92,
    },
    "classical.pattern.yangren.v1": {
        "YANGREN_MATCH_BASE": 0.8,
        "YANGREN_MIN_SCORE": 16.0,
        "YANGREN_ORIGIN_SCALE_MIN": 0.92,
    },
    "classical.pattern.guanyin.v1": {
        "GUANYIN_MIN_GUAN": 16.0,
        "GUANYIN_MIN_SEAL": 16.0,
        "GUANYIN_MATCH_BASE": 0.76,
    },
    "classical.pattern.shayin.v1": {
        "SHAYIN_MIN_SHA": 16.0,
        "SHAYIN_MIN_SEAL": 15.0,
        "SHAYIN_MATCH_BASE": 0.76,
    },
    "classical.pattern.shishen_zhisha.v1": {
        "SHISHEN_ZHISHA_MIN_SHA": 16.0,
        "SHISHEN_ZHISHA_MIN_SHISHEN": 16.0,
        "SHISHEN_ZHISHA_MATCH_BASE": 0.78,
    },
    "classical.pattern.shangguan_peiyin.v1": {
        "SHANGGUAN_PEIYIN_MIN_HURT": 16.0,
        "SHANGGUAN_PEIYIN_MIN_SEAL": 15.0,
        "SHANGGUAN_PEIYIN_MATCH_BASE": 0.76,
    },
    "classical.pattern.shishen_shengcai.v1": {
        "SHISHEN_SHENGCAI_MIN_SHISHEN": 16.0,
        "SHISHEN_SHENGCAI_MIN_WEALTH": 15.0,
        "SHISHEN_SHENGCAI_MATCH_BASE": 0.76,
    },
    "classical.pattern.shangguan_shengcai.v1": {
        "SHANGGUAN_SHENGCAI_MIN_HURT": 16.0,
        "SHANGGUAN_SHENGCAI_MIN_WEALTH": 15.0,
        "SHANGGUAN_SHENGCAI_MATCH_BASE": 0.76,
    },
    "classical.pattern.yangren_jiasha.v1": {
        "YANGREN_JIASHA_MIN_REN": 16.0,
        "YANGREN_JIASHA_MIN_SHA": 16.0,
        "YANGREN_JIASHA_MATCH_BASE": 0.78,
    },
    "classical.pattern.zaqi_caiguan.v1": {
        "ZAQI_CAIGUAN_MIN_SCORE": 14.0,
        "ZAQI_CAIGUAN_MATCH_BASE": 0.72,
    },
    "classical.pattern.zaqi_yin.v1": {
        "ZAQI_YIN_MIN_SCORE": 14.0,
        "ZAQI_YIN_MATCH_BASE": 0.72,
    },
    "classical.pattern.zaqi_qisha.v1": {
        "ZAQI_QISHA_MIN_SCORE": 14.0,
        "ZAQI_QISHA_MATCH_BASE": 0.72,
    },
    "classical.pattern.congcai.v1": {
        "CONGCAI_MIN_WEALTH": 22.0,
        "CONGCAI_MAX_PEER": 12.0,
        "CONGCAI_MATCH_BASE": 0.74,
    },
    "classical.pattern.congsha.v1": {
        "CONGSHA_MIN_SHA": 22.0,
        "CONGSHA_MAX_PEER": 12.0,
        "CONGSHA_MATCH_BASE": 0.74,
    },
    "classical.pattern.conger.v1": {
        "CONGER_MIN_OUTPUT": 24.0,
        "CONGER_MAX_SEAL": 12.0,
        "CONGER_MATCH_BASE": 0.74,
    },
    "classical.pattern.congwang.v1": {
        "CONGWANG_MIN_PEER": 30.0,
        "CONGWANG_MAX_OTHER": 14.0,
        "CONGWANG_MATCH_BASE": 0.76,
    },
    "classical.pattern.congqiang.v1": {
        "CONGQIANG_MIN_PEER": 28.0,
        "CONGQIANG_MAX_OTHER": 15.0,
        "CONGQIANG_MATCH_BASE": 0.75,
    },
    "classical.pattern.congruo.v1": {
        "CONGRUO_MAX_PEER": 10.0,
        "CONGRUO_MIN_OTHER": 24.0,
        "CONGRUO_MATCH_BASE": 0.72,
    },
    "classical.pattern.huaqi.v1": {
        "HUAQI_MIN_MATCH": 0.72,
    },
    "classical.pattern.quzhi.v1": {
        "SPECIALIZED_MIN_SCORE": 26.0,
        "SPECIALIZED_MAX_OTHER": 14.0,
        "SPECIALIZED_MATCH_BASE": 0.76,
    },
    "classical.pattern.yanshang.v1": {
        "SPECIALIZED_MIN_SCORE": 26.0,
        "SPECIALIZED_MAX_OTHER": 14.0,
        "SPECIALIZED_MATCH_BASE": 0.76,
    },
    "classical.pattern.jiase.v1": {
        "SPECIALIZED_MIN_SCORE": 26.0,
        "SPECIALIZED_MAX_OTHER": 14.0,
        "SPECIALIZED_MATCH_BASE": 0.76,
    },
    "classical.pattern.congge.v1": {
        "SPECIALIZED_MIN_SCORE": 26.0,
        "SPECIALIZED_MAX_OTHER": 14.0,
        "SPECIALIZED_MATCH_BASE": 0.76,
    },
    "classical.pattern.runxia.v1": {
        "SPECIALIZED_MIN_SCORE": 26.0,
        "SPECIALIZED_MAX_OTHER": 14.0,
        "SPECIALIZED_MATCH_BASE": 0.76,
    },
    "classical.pattern.liangshen.v1": {
        "LIANGSHEN_MIN_PAIR": 18.0,
        "LIANGSHEN_MATCH_BASE": 0.72,
    },
    "classical.pattern.tianyuan.v1": {
        "TIANYUAN_MIN_SAME": 3.0,
        "TIANYUAN_MATCH_BASE": 0.7,
    },
}

YANGREN_BRANCH_BY_DAYMASTER: Dict[str, str] = {
    "甲": "卯",
    "丙": "午",
    "戊": "午",
    "庚": "酉",
    "壬": "子",
}


def _scope_weights_from_rows(rows: List[Dict[str, Any]], *, member_filter: List[str] | None = None) -> Dict[str, float]:
    filtered: List[Dict[str, Any]] = []
    need_members = {str(item).strip() for item in (member_filter or []) if str(item).strip()}
    for row in rows:
        if not isinstance(row, dict):
            continue
        if need_members:
            row_members = set()
            for key in ("pair", "group", "branches", "matched_branches", "branch"):
                value = row.get(key)
                if isinstance(value, (list, tuple, set)):
                    row_members.update({str(item).strip() for item in value if str(item).strip()})
                elif str(value or "").strip():
                    row_members.add(str(value).strip())
            if not (need_members & row_members):
                continue
        origin = str(row.get("origin_type") or "").strip()
        if not origin:
            origin = detect_relation_origin_type(row.get("pillars") if isinstance(row.get("pillars"), list) else [])
        if not origin:
            continue
        filtered.append({"origin_type": origin, "row": row})
    if not filtered:
        return {"natal": 1.0}
    scope_weights: Dict[str, float] = {
        "natal": 0.0,
        "luck_background": 0.0,
        "luck_only": 0.0,
        "flow_trigger": 0.0,
        "flow_only": 0.0,
        "runtime_pair": 0.0,
        "mixed": 0.0,
        "unknown": 0.0,
    }
    for payload in filtered:
        origin = str(payload["origin_type"]).strip().lower()
        row = payload["row"]
        strength = float(
            row.get("pivot_factor")
            if row.get("pivot_factor") is not None
            else row.get("strength")
            if row.get("strength") is not None
            else row.get("stress")
            if row.get("stress") is not None
            else 1.0
        )
        scope_weights[origin] = scope_weights.get(origin, 0.0) + max(0.2, strength) * relation_origin_multiplier(origin)
    total = sum(scope_weights.values()) or 1.0
    return {k: round(v / total, 4) for k, v in scope_weights.items() if v > 0.0}


def _classify_dynamic_scope(scope_weights: Dict[str, float]) -> str:
    present = {k for k, v in scope_weights.items() if v > 0.0 and k != "mixed"}
    if not present:
        return "natal"
    if "natal" in present and len(present) > 1:
        return "mixed"
    if "natal" in present and "flow_only" in present:
        return "flow_trigger"
    if {"luck_background", "luck_only"} & present and "natal" in present:
        return "luck_background"
    if "runtime_pair" in present and "luck_only" in present and "flow_only" in present:
        return "mixed"
    if "luck_only" in present and "flow_only" in present:
        return "runtime_pair"
    if "flow_only" in present:
        return "flow_only"
    if "luck_only" in present:
        return "luck_only"
    if "runtime_pair" in present:
        return "runtime_pair"
    if "luck_background" in present:
        return "luck_background"
    return "mixed" if len(present) > 1 else next(iter(present), "natal")


def _pattern_cfg(plugin_id: str, key: str, fallback: float) -> float:
    cfg = get_plugin_config(plugin_id)
    defaults = PATTERN_DEFAULTS.get(plugin_id, {})
    return float(cfg.get(key, defaults.get(key, fallback)))


def _month_main_god(physics_tensor: Dict[str, Any]) -> str:
    four = physics_tensor.get("four_pillars") if isinstance(physics_tensor.get("four_pillars"), dict) else {}
    day_gz = str(four.get("day", "")).strip()
    month_gz = str(four.get("month", "")).strip()
    if len(day_gz) < 2 or len(month_gz) < 2:
        return ""
    daymaster = day_gz[0]
    month_branch = month_gz[1]
    hidden = BRANCH_HIDDEN.get(month_branch, [])
    if not hidden:
        return ""
    return ten_god_from_stems(daymaster, hidden[0][0])


def _month_branch(physics_tensor: Dict[str, Any]) -> str:
    four = physics_tensor.get("four_pillars") if isinstance(physics_tensor.get("four_pillars"), dict) else {}
    month_gz = str(four.get("month", "")).strip()
    if len(month_gz) < 2:
        return ""
    return month_gz[1]


def _daymaster_stem(physics_tensor: Dict[str, Any]) -> str:
    four = physics_tensor.get("four_pillars") if isinstance(physics_tensor.get("four_pillars"), dict) else {}
    day_gz = str(four.get("day", "")).strip()
    if len(day_gz) < 2:
        return ""
    return day_gz[0]


def _score_sum(scores: Dict[str, float], *names: str) -> float:
    return sum(float(scores.get(name, 0.0)) for name in names)


def _is_zaji_month(branch: str) -> bool:
    return branch in {"辰", "戌", "丑", "未"}


def _dominant_element(scores: Dict[str, float]) -> Tuple[str, float, float]:
    element_scores = {"木": 0.0, "火": 0.0, "土": 0.0, "金": 0.0, "水": 0.0}
    god_to_element = {
        "比肩": "木", "劫财": "木",
        "食神": "火", "伤官": "火",
        "偏财": "土", "正财": "土",
        "七杀": "金", "正官": "金",
        "偏印": "水", "正印": "水",
    }
    for god, score in scores.items():
        element = god_to_element.get(str(god))
        if element:
            element_scores[element] += float(score)
    ranked = sorted(element_scores.items(), key=lambda kv: kv[1], reverse=True)
    top_el, top_score = ranked[0]
    second = float(ranked[1][1]) if len(ranked) > 1 else 0.0
    return top_el, float(top_score), second


def _visible_stems_and_branches(physics_tensor: Dict[str, Any]) -> Tuple[List[str], List[str]]:
    four = physics_tensor.get("four_pillars") if isinstance(physics_tensor.get("four_pillars"), dict) else {}
    stems: List[str] = []
    branches: List[str] = []
    for key in ("year", "month", "day", "hour"):
        stem, branch = _parse_gz(str(four.get(key, "")).strip())
        if stem:
            stems.append(stem)
        if branch:
            branches.append(branch)
    return stems, branches


def _pattern_candidates(physics_tensor: Dict[str, Any]) -> List[Tuple[str, str, float]]:
    scores = deity_scores_from_tensor(physics_tensor)
    candidates: List[Tuple[str, str, float]] = []
    if not scores:
        return candidates
    cfg = get_plugin_config("classical.pattern.axis.v1")
    follower_ratio_threshold = float(cfg.get("CANDIDATE_FOLLOWER_RATIO", 2.0))
    follower_score_threshold = float(cfg.get("CANDIDATE_FOLLOWER_SCORE", 35.0))
    officer_wealth_threshold = float(cfg.get("CANDIDATE_OFFICER_WEALTH", 25.0))

    top = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    top_name, top_score = top[0]
    candidates.append(("主轴格", top_name, float(top_score)))

    month_god = _month_main_god(physics_tensor)
    if month_god in {"比肩", "劫财"}:
        candidates.append(("建禄/月劫", month_god, float(scores.get(month_god, 0.0))))

    if len(top) >= 2:
        top2_score = float(top[1][1])
        ratio = float(top_score) / max(top2_score, 1.0)
        if ratio >= follower_ratio_threshold and float(top_score) >= follower_score_threshold:
            candidates.append(("从势候选", top_name, round(ratio, 3)))

    officer = float(scores.get("正官", 0.0) + scores.get("七杀", 0.0))
    wealth = float(scores.get("正财", 0.0) + scores.get("偏财", 0.0))
    if officer >= officer_wealth_threshold and wealth >= officer_wealth_threshold:
        candidates.append(("财官协同", "财官", min(officer, wealth)))

    guan = float(scores.get("正官", 0.0))
    sha = float(scores.get("七杀", 0.0))
    seal = _score_sum(scores, "正印", "偏印")
    if guan >= _pattern_cfg("classical.pattern.guanyin.v1", "GUANYIN_MIN_GUAN", 16.0) and seal >= _pattern_cfg("classical.pattern.guanyin.v1", "GUANYIN_MIN_SEAL", 16.0):
        candidates.append(("官印相生", "正官", min(guan, seal)))
    if sha >= _pattern_cfg("classical.pattern.shayin.v1", "SHAYIN_MIN_SHA", 16.0) and seal >= _pattern_cfg("classical.pattern.shayin.v1", "SHAYIN_MIN_SEAL", 15.0):
        candidates.append(("杀印相生", "七杀", min(sha, seal)))
    if sha >= _pattern_cfg("classical.pattern.shishen_zhisha.v1", "SHISHEN_ZHISHA_MIN_SHA", 16.0) and float(scores.get("食神", 0.0)) >= _pattern_cfg("classical.pattern.shishen_zhisha.v1", "SHISHEN_ZHISHA_MIN_SHISHEN", 16.0):
        candidates.append(("食神制杀", "七杀", min(sha, float(scores.get("食神", 0.0)))))
    if float(scores.get("伤官", 0.0)) >= _pattern_cfg("classical.pattern.shangguan_peiyin.v1", "SHANGGUAN_PEIYIN_MIN_HURT", 16.0) and seal >= _pattern_cfg("classical.pattern.shangguan_peiyin.v1", "SHANGGUAN_PEIYIN_MIN_SEAL", 15.0):
        candidates.append(("伤官配印", "伤官", min(float(scores.get("伤官", 0.0)), seal)))
    if float(scores.get("食神", 0.0)) >= _pattern_cfg("classical.pattern.shishen_shengcai.v1", "SHISHEN_SHENGCAI_MIN_SHISHEN", 16.0) and wealth >= _pattern_cfg("classical.pattern.shishen_shengcai.v1", "SHISHEN_SHENGCAI_MIN_WEALTH", 15.0):
        candidates.append(("食神生财", "食神", min(float(scores.get("食神", 0.0)), wealth)))
    if float(scores.get("伤官", 0.0)) >= _pattern_cfg("classical.pattern.shangguan_shengcai.v1", "SHANGGUAN_SHENGCAI_MIN_HURT", 16.0) and wealth >= _pattern_cfg("classical.pattern.shangguan_shengcai.v1", "SHANGGUAN_SHENGCAI_MIN_WEALTH", 15.0):
        candidates.append(("伤官生财", "伤官", min(float(scores.get("伤官", 0.0)), wealth)))
    ren_score = _score_sum(scores, "劫财", "比肩")
    if ren_score >= _pattern_cfg("classical.pattern.yangren_jiasha.v1", "YANGREN_JIASHA_MIN_REN", 16.0) and sha >= _pattern_cfg("classical.pattern.yangren_jiasha.v1", "YANGREN_JIASHA_MIN_SHA", 16.0):
        candidates.append(("阳刃驾杀", "七杀", min(ren_score, sha)))
    if wealth >= _pattern_cfg("classical.pattern.congcai.v1", "CONGCAI_MIN_WEALTH", 22.0) and ren_score <= _pattern_cfg("classical.pattern.congcai.v1", "CONGCAI_MAX_PEER", 12.0):
        candidates.append(("从财格", "财星", wealth))
    if sha >= _pattern_cfg("classical.pattern.congsha.v1", "CONGSHA_MIN_SHA", 22.0) and ren_score <= _pattern_cfg("classical.pattern.congsha.v1", "CONGSHA_MAX_PEER", 12.0):
        candidates.append(("从杀格", "七杀", sha))
    output_total = _score_sum(scores, "食神", "伤官")
    if output_total >= _pattern_cfg("classical.pattern.conger.v1", "CONGER_MIN_OUTPUT", 24.0) and seal <= _pattern_cfg("classical.pattern.conger.v1", "CONGER_MAX_SEAL", 12.0):
        candidates.append(("从儿格", "食伤", output_total))
    if ren_score >= _pattern_cfg("classical.pattern.congwang.v1", "CONGWANG_MIN_PEER", 30.0):
        candidates.append(("从旺格", "比劫", ren_score))
    if ren_score >= _pattern_cfg("classical.pattern.congqiang.v1", "CONGQIANG_MIN_PEER", 28.0):
        candidates.append(("从强格", "比劫", ren_score))

    return candidates


def _pattern_context(physics_tensor: Dict[str, Any]) -> Dict[str, Any]:
    scores = deity_scores_from_tensor(physics_tensor)
    month_god = _month_main_god(physics_tensor)
    top = sorted(scores.items(), key=lambda kv: kv[1], reverse=True) if scores else []
    top_name = top[0][0] if top else ""
    top_score = float(top[0][1]) if top else 0.0
    second_score = float(top[1][1]) if len(top) >= 2 else 0.0
    ratio = top_score / max(second_score, 1.0) if top_score else 0.0
    meta = physics_tensor.get("meta") if isinstance(physics_tensor.get("meta"), dict) else {}
    iv2 = meta.get("interaction_v2") if isinstance(meta.get("interaction_v2"), dict) else {}
    blockers: List[str] = []
    if iv2.get("liu_chong"):
        blockers.append("liu_chong")
    if iv2.get("sanxing"):
        blockers.append("sanxing")
    if iv2.get("liu_hai"):
        blockers.append("liu_hai")
    blocker_origin_types: List[str] = []
    blocker_origin_types.extend(collect_origin_types_from_rows(iv2.get("liu_chong") or [], member_key="pair"))
    blocker_origin_types.extend(collect_origin_types_from_rows(iv2.get("sanxing") or [], member_key="branches"))
    blocker_origin_types.extend(collect_origin_types_from_rows(iv2.get("liu_hai") or [], member_key="pair"))
    return {
        "scores": scores,
        "month_god": month_god,
        "top_name": top_name,
        "top_score": top_score,
        "dominant_ratio": round(ratio, 3),
        "blockers": blockers,
        "origin_type": choose_dominant_origin_type(blocker_origin_types) if blocker_origin_types else "natal",
    }


def _dynamic_scope_context(physics_tensor: Dict[str, Any], *, candidates: List[Tuple[str, str, float]]) -> Dict[str, Any]:
    meta = physics_tensor.get("meta") if isinstance(physics_tensor.get("meta"), dict) else {}
    iv2 = meta.get("interaction_v2") if isinstance(meta.get("interaction_v2"), dict) else {}
    relation_rows: List[Dict[str, Any]] = []
    relation_rows.extend([row for row in iv2.get("liu_chong", []) if isinstance(row, dict)])
    relation_rows.extend([row for row in iv2.get("liu_hai", []) if isinstance(row, dict)])
    relation_rows.extend([row for row in iv2.get("liu_po", []) if isinstance(row, dict)])
    relation_rows.extend([row for row in iv2.get("liu_he", []) if isinstance(row, dict)])
    relation_rows.extend([row for row in iv2.get("san_he", []) if isinstance(row, dict)])
    relation_rows.extend([row for row in iv2.get("ban_he", []) if isinstance(row, dict)])
    relation_rows.extend([row for row in iv2.get("sanxing", []) if isinstance(row, dict)])

    scope_weights = _scope_weights_from_rows(relation_rows)
    dominant_scope = _classify_dynamic_scope(scope_weights)
    # 只保留高于阈值的来源权重，避免无意义的长尾噪声被误读为主导
    min_weight = float(_pattern_cfg("classical.pattern.dynamic_scope.v1", "SCOPE_MIN_WEIGHT", 0.06))
    compact_scope = {
        k: v
        for k, v in sorted(scope_weights.items(), key=lambda kv: kv[1], reverse=True)
        if v >= min_weight
    }

    scope_labels = {
        "natal": "原局主导",
        "luck_background": "原局+大运共振",
        "luck_only": "大运主导",
        "flow_trigger": "原局+流年触发",
        "flow_only": "流年触发",
        "runtime_pair": "大运+流年触发",
        "mixed": "原局/运/流混合",
        "unknown": "待确认",
    }
    target = str(candidates[0][1] if candidates else "")
    return {
        "scope": dominant_scope,
        "scope_label": scope_labels.get(dominant_scope, "动态判定"),
        "scope_weights": compact_scope,
        "target_god": target,
        "candidate_count": len(candidates),
        "candidates": [
            {"candidate": name, "target_god": str(target_god), "raw_score": round(float(score), 3)}
            for name, target_god, score in candidates
        ],
    }


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _pattern_origin_meta(physics_tensor: Dict[str, Any]) -> Dict[str, Any]:
    context = _pattern_context(physics_tensor)
    origin_type = str(context.get("origin_type") or "natal")
    return {
        "origin_type": origin_type,
        "origin_multiplier": relation_origin_multiplier(origin_type),
    }


def _pattern_manifestation(blockers: List[str] | None, origin_type: str, *, target_is_strong: bool) -> str:
    if not blockers and target_is_strong:
        return "manifested"
    if blockers:
        return "supported" if len(blockers) <= 1 else "contested"
    if origin_type == "natal":
        return "supported"
    return "latent"


@dataclass
class PatternAxisPlugin(V17PluginSpec):
    plugin_id: str = "classical.pattern.axis.v1"
    causal_tier: int = 3
    registry_priority: float = 0.77

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        scores = deity_scores_from_tensor(physics_tensor)
        if not scores:
            return []
        origin_meta = _pattern_origin_meta(physics_tensor)
        context = _pattern_context(physics_tensor)
        base = _pattern_cfg(self.plugin_id, "AXIS_MATCH_BASE", 0.42)
        top_share_weight = _pattern_cfg(self.plugin_id, "AXIS_TOP_SHARE_WEIGHT", 0.5)
        dominant_weight = _pattern_cfg(self.plugin_id, "AXIS_DOMINANT_WEIGHT", 0.25)
        dominant_divisor = max(0.1, _pattern_cfg(self.plugin_id, "AXIS_DOMINANT_DIVISOR", 1.5))
        origin_scale = max(0.92, _pattern_cfg(self.plugin_id, "AXIS_ORIGIN_SCALE_MIN", 0.92))
        ordered = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
        top = ordered[0]
        top_score = float(top[1])
        second_score = float(ordered[1][1]) if len(ordered) >= 2 else 0.0
        total_score = max(sum(float(v) for _k, v in ordered), 1.0)
        top_share = top_score / total_score
        dominant_ratio = top_score / max(second_score, 1.0) if top_score else 0.0
        fp = physics_tensor.get("four_pillars") if isinstance(physics_tensor.get("four_pillars"), dict) else {}
        day_gz = str(fp.get("day", "")).strip()
        daymaster = day_gz[0] if len(day_gz) >= 2 else "壬"
        projection = god_cluster_projection(
            physics_tensor=physics_tensor,
            base_god=top[0],
            day_master=daymaster,
            focus_branches=[str(str(fp.get("month", ""))[1:2] or "")],
        )
        axis_match_ratio = _clamp01(
            base
            + top_share_weight * top_share
            + dominant_weight * min(1.0, max(0.0, (dominant_ratio - 1.0) / dominant_divisor))
        ) * max(origin_scale, float(origin_meta["origin_multiplier"]))
        rows = [
            {
                "plugin": self.plugin_id,
                "fact": f"格局轴线候选：{top[0]} 当前为最强主轴，可作为格局专题的第一观察面。",
                "priority": 0.77,
                "label": "格局轴线",
                "meta": {
                    "pattern_axis": top[0],
                    "target_god": top[0],
                    "axis_score": top_score,
                    "projection_share": round(float((projection or {}).get(top[0], 1.0)), 4),
                    "cluster_projection": projection,
                    "top_share": round(top_share, 3),
                    "dominant_ratio": round(dominant_ratio, 3),
                    "match_ratio": round(axis_match_ratio, 3),
                    "claim_type": "pattern_candidate",
                    "entity_scope": "pattern",
                    "exclusivity_key": "pattern_family",
                    "source_event": "pattern_family",
                    "confidence": 0.77,
                    "static_basis": build_static_basis(
                        physics_tensor=physics_tensor,
                        target_god=top[0],
                        relation_family="pattern_axis",
                        relation_members=[],
                    ),
                    "interaction_layer": detect_interaction_layer(
                        {"interaction_layer": "cross_layer"},
                        relation_family="pattern_axis",
                    ),
                    "manifestation_state": _pattern_manifestation(
                        blockers=context.get("blockers"),
                        origin_type=str(origin_meta.get("origin_type") or ""),
                        target_is_strong=True,
                    ),
                    **origin_meta,
                },
            }
        ]
        return rows_dict_to_v17_facts(rows, causal_tier=self.causal_tier, default_plugin_id=self.plugin_id)


@dataclass
class PatternDynamicScopePlugin(V17PluginSpec):
    plugin_id: str = "classical.pattern.dynamic_scope.v1"
    causal_tier: int = 3
    registry_priority: float = 0.72

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        candidates = _pattern_candidates(physics_tensor)
        if not candidates:
            return []
        scope_meta = _dynamic_scope_context(physics_tensor, candidates=candidates)
        match_base = _pattern_cfg(self.plugin_id, "SCOPE_MATCH_BASE", 0.62)
        scope = str(scope_meta.get("scope") or "natal")
        scope_multipliers = {"natal": 1.0, "luck_background": 0.96, "luck_only": 0.89, "flow_trigger": 0.9, "flow_only": 0.84, "runtime_pair": 0.88, "mixed": 1.0}
        scope_boost = float(_pattern_cfg(self.plugin_id, "SCOPE_MIX_LABEL_BOOST", 1.1)) if scope == "mixed" else 1.0
        scope_weight_sum = sum(float(v) for v in scope_meta.get("scope_weights", {}).values())
        match_ratio = round(min(0.92, match_base * min(1.0, scope_weight_sum) * scope_boost * scope_multipliers.get(scope, 1.0)), 3)
        rows = [
            {
                "plugin": self.plugin_id,
                "fact": (
                    f"动态格局来源：{scope_meta.get('scope_label') or ''}；"
                    f"候选{scope_meta.get('candidate_count', 0)}条，"
                    f"以{scope_meta.get('target_god') or '主轴神'}为核心观察。"
                ).strip(),
                "priority": 0.72,
                "label": "动态格局来源",
                "meta": {
                    "pattern_scope_mode": "natal_luck_flow_mix",
                    "scope_weights": scope_meta.get("scope_weights", {}),
                    "pattern_scope": scope,
                    "pattern_scope_label": scope_meta.get("scope_label"),
                    "pattern_dynamic_candidates": scope_meta.get("candidates", []),
                    "candidate_count": scope_meta.get("candidate_count", 0),
                    "observe_only": True,
                    "claim_type": "pattern_observation",
                    "entity_scope": "pattern",
                    "exclusivity_key": "pattern_family",
                    "source_event": "pattern_family",
                    "match_ratio": match_ratio,
                    "pattern_mix_mode": "dynamic_scope",
                    "origin_type": scope,
                    "origin_multiplier": relation_origin_multiplier(scope),
                    **build_static_basis(
                        physics_tensor=physics_tensor,
                        target_god=scope_meta.get("target_god") or "",
                        relation_family="pattern_dynamic_scope",
                        relation_members=[],
                    ),
                    "interaction_layer": detect_interaction_layer(
                        {"interaction_layer": "cross_layer"},
                        relation_family="pattern_dynamic_scope",
                    ),
                    "manifestation_state": "supported",
                },
            }
        ]
        return rows_dict_to_v17_facts(rows, causal_tier=self.causal_tier, default_plugin_id=self.plugin_id)


@dataclass
class JianLuYueJiePlugin(V17PluginSpec):
    plugin_id: str = "classical.pattern.jianlu_yuejie.v1"
    causal_tier: int = 3
    registry_priority: float = 0.75

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        month_god = _month_main_god(physics_tensor)
        if month_god not in {"比肩", "劫财"}:
            return []
        origin_meta = _pattern_origin_meta(physics_tensor)
        context = _pattern_context(physics_tensor)
        fp = physics_tensor.get("four_pillars") if isinstance(physics_tensor.get("four_pillars"), dict) else {}
        day_gz = str(fp.get("day", "")).strip()
        daymaster = day_gz[0] if len(day_gz) >= 2 else "壬"
        projection = god_cluster_projection(
            physics_tensor=physics_tensor,
            base_god=month_god,
            day_master=daymaster,
            focus_branches=[str(str(fp.get("month", ""))[1:2] or "")],
        )
        name = "建禄" if month_god == "比肩" else "月劫"
        match_base = _pattern_cfg(self.plugin_id, "JIANLU_MATCH_BASE", 0.82)
        origin_scale = max(_pattern_cfg(self.plugin_id, "JIANLU_ORIGIN_SCALE_MIN", 0.92), float(origin_meta["origin_multiplier"]))
        rows = [
            {
                "plugin": self.plugin_id,
                "fact": f"格局候选：月令主气落在 {month_god}，本局存在「{name}」方向。",
                "priority": 0.75,
                "label": "格局候选",
                "meta": {
                    "pattern_candidate": name,
                    "target_god": month_god,
                    "month_main_god": month_god,
                    "projection_share": round(float((projection or {}).get(month_god, 1.0)), 4),
                    "cluster_projection": projection,
                    "match_ratio": round(_clamp01(match_base * max(origin_scale, float(origin_meta["origin_multiplier"]))), 3),
                    "claim_type": "pattern_candidate",
                    "entity_scope": "pattern",
                    "exclusivity_key": "pattern_family",
                    "source_event": "pattern_family",
                    "confidence": 0.75,
                    "static_basis": build_static_basis(
                        physics_tensor=physics_tensor,
                        target_god=month_god,
                        relation_family="pattern_jianlu_yuejie",
                        relation_members=[],
                    ),
                    "interaction_layer": detect_interaction_layer(
                        {"interaction_layer": "cross_layer"},
                        relation_family="pattern_jianlu_yuejie",
                    ),
                    "manifestation_state": _pattern_manifestation(
                        blockers=context.get("blockers"),
                        origin_type=str(origin_meta.get("origin_type") or ""),
                        target_is_strong=True,
                    ),
                    **origin_meta,
                },
            }
        ]
        return rows_dict_to_v17_facts(rows, causal_tier=self.causal_tier, default_plugin_id=self.plugin_id)


@dataclass
class CongShiPlugin(V17PluginSpec):
    plugin_id: str = "classical.pattern.congshi.v1"
    causal_tier: int = 3
    registry_priority: float = 0.74

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        scores = deity_scores_from_tensor(physics_tensor)
        origin_meta = _pattern_origin_meta(physics_tensor)
        context = _pattern_context(physics_tensor)
        top = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)[:2]
        if len(top) < 2:
            return []
        (g1, v1), (_g2, v2) = top
        fp = physics_tensor.get("four_pillars") if isinstance(physics_tensor.get("four_pillars"), dict) else {}
        day_gz = str(fp.get("day", "")).strip()
        daymaster = day_gz[0] if len(day_gz) >= 2 else "壬"
        projection = god_cluster_projection(
            physics_tensor=physics_tensor,
            base_god=g1,
            day_master=daymaster,
            focus_branches=[str(str(fp.get("month", ""))[1:2] or "")],
        )
        ratio = v1 / max(v2, 1.0)
        cfg = get_plugin_config(self.plugin_id)
        ratio_threshold = float(cfg.get("CONGSHI_RATIO_THRESHOLD", PATTERN_DEFAULTS[self.plugin_id]["CONGSHI_RATIO_THRESHOLD"]))
        score_threshold = float(cfg.get("CONGSHI_SCORE_THRESHOLD", PATTERN_DEFAULTS[self.plugin_id]["CONGSHI_SCORE_THRESHOLD"]))
        ratio_divisor = max(0.1, float(cfg.get("CONGSHI_RATIO_DIVISOR", PATTERN_DEFAULTS[self.plugin_id]["CONGSHI_RATIO_DIVISOR"])))
        origin_scale = max(
            float(cfg.get("CONGSHI_ORIGIN_SCALE_MIN", PATTERN_DEFAULTS[self.plugin_id]["CONGSHI_ORIGIN_SCALE_MIN"])),
            float(origin_meta["origin_multiplier"]),
        )
        strong_ratio = float(cfg.get("CONGSHI_STRONG_RATIO", PATTERN_DEFAULTS[self.plugin_id]["CONGSHI_STRONG_RATIO"]))
        if ratio < ratio_threshold or v1 < score_threshold:
            return []
        rows = [
            {
                "plugin": self.plugin_id,
                "fact": f"格局候选：{g1} 一枝独强，存在「从势 / 从强」候选，需要专题条件进一步核验。",
                "priority": 0.74,
                "label": "从势候选",
                "meta": {
                    "pattern_candidate": "从势候选",
                    "dominant_god": g1,
                    "target_god": g1,
                    "projection_share": round(float((projection or {}).get(g1, 1.0)), 4),
                    "cluster_projection": projection,
                    "dominant_ratio": round(ratio, 3),
                    "match_ratio": round(_clamp01(_clamp01((ratio - 1.0) / ratio_divisor) * origin_scale), 3),
                    "claim_type": "pattern_candidate",
                    "entity_scope": "pattern",
                    "exclusivity_key": "pattern_family",
                    "source_event": "pattern_family",
                    "confidence": 0.74,
                    "static_basis": build_static_basis(
                        physics_tensor=physics_tensor,
                        target_god=g1,
                        relation_family="pattern_congshi",
                        relation_members=[],
                    ),
                    "interaction_layer": detect_interaction_layer(
                        {"interaction_layer": "cross_layer"},
                        relation_family="pattern_congshi",
                    ),
                    "manifestation_state": _pattern_manifestation(
                        blockers=context.get("blockers"),
                        origin_type=str(origin_meta.get("origin_type") or ""),
                        target_is_strong=ratio >= strong_ratio,
                    ),
                    **origin_meta,
                },
            }
        ]
        return rows_dict_to_v17_facts(rows, causal_tier=self.causal_tier, default_plugin_id=self.plugin_id)


@dataclass
class FinanceOfficerPatternPlugin(V17PluginSpec):
    plugin_id: str = "classical.pattern.finance_officer.v1"
    causal_tier: int = 3
    registry_priority: float = 0.73

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        scores = deity_scores_from_tensor(physics_tensor)
        origin_meta = _pattern_origin_meta(physics_tensor)
        context = _pattern_context(physics_tensor)
        officer = float(scores.get("正官", 0.0) + scores.get("七杀", 0.0))
        wealth = float(scores.get("正财", 0.0) + scores.get("偏财", 0.0))
        min_total = _pattern_cfg(self.plugin_id, "FINANCE_MIN_GOD_SUM", 25.0)
        if officer < min_total or wealth < min_total:
            return []
        dominant_god = "正官" if float(scores.get("正官", 0.0)) >= float(scores.get("七杀", 0.0)) else "七杀"
        match_scale = max(
            _pattern_cfg(self.plugin_id, "FINANCE_MATCH_MIN_ORIGIN_SCALE", 0.92),
            float(origin_meta["origin_multiplier"]),
        )
        fp = physics_tensor.get("four_pillars") if isinstance(physics_tensor.get("four_pillars"), dict) else {}
        day_gz = str(fp.get("day", "")).strip()
        daymaster = day_gz[0] if len(day_gz) >= 2 else "壬"
        projection = god_cluster_projection(
            physics_tensor=physics_tensor,
            base_god=dominant_god,
            day_master=daymaster,
            focus_branches=[str(str(fp.get("month", ""))[1:2] or "")],
        )
        match_ratio = _clamp01((min(officer, wealth) / max(officer, wealth, 1.0)) * match_scale)
        rows = [
            {
                "plugin": self.plugin_id,
                "fact": "格局候选：财官双线并举，可进入财官协同专题继续核验。",
                "priority": 0.73,
                "label": "财官协同",
                "meta": {
                    "pattern_candidate": "财官协同",
                    "target_god": dominant_god,
                    "officer_total": officer,
                    "wealth_total": wealth,
                    "projection_share": round(float((projection or {}).get(dominant_god, 1.0)), 4),
                    "cluster_projection": projection,
                    "match_ratio": round(match_ratio, 3),
                    "claim_type": "pattern_candidate",
                    "entity_scope": "pattern",
                    "exclusivity_key": "pattern_family",
                    "source_event": "pattern_family",
                    "confidence": 0.73,
                    "static_basis": build_static_basis(
                        physics_tensor=physics_tensor,
                        target_god=dominant_god,
                        relation_family="pattern_finance_officer",
                        relation_members=[],
                    ),
                    "interaction_layer": detect_interaction_layer(
                        {"interaction_layer": "cross_layer"},
                        relation_family="pattern_finance_officer",
                    ),
                    "manifestation_state": _pattern_manifestation(
                        blockers=context.get("blockers"),
                        origin_type=str(origin_meta.get("origin_type") or ""),
                        target_is_strong=match_ratio >= _pattern_cfg("classical.pattern.axis.v1", "FINANCE_STRONG_MATCH_RATIO", 0.6),
                    ),
                    **origin_meta,
                },
            }
        ]
        return rows_dict_to_v17_facts(rows, causal_tier=self.causal_tier, default_plugin_id=self.plugin_id)


@dataclass
class WealthStarPatternPlugin(V17PluginSpec):
    plugin_id: str = "classical.pattern.wealth_star.v1"
    causal_tier: int = 3
    registry_priority: float = 0.735

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        month_god = _month_main_god(physics_tensor)
        if month_god not in {"正财", "偏财"}:
            return []
        scores = deity_scores_from_tensor(physics_tensor)
        target_score = float(scores.get(month_god, 0.0))
        min_score = _pattern_cfg(self.plugin_id, "WEALTH_MIN_SCORE", 14.0)
        if target_score < min_score:
            return []
        origin_meta = _pattern_origin_meta(physics_tensor)
        context = _pattern_context(physics_tensor)
        fp = physics_tensor.get("four_pillars") if isinstance(physics_tensor.get("four_pillars"), dict) else {}
        day_gz = str(fp.get("day", "")).strip()
        daymaster = day_gz[0] if len(day_gz) >= 2 else "壬"
        projection = god_cluster_projection(
            physics_tensor=physics_tensor,
            base_god=month_god,
            day_master=daymaster,
            focus_branches=[_month_branch(physics_tensor)],
        )
        base = _pattern_cfg(self.plugin_id, "WEALTH_MATCH_BASE", 0.72)
        origin_scale = max(_pattern_cfg(self.plugin_id, "WEALTH_ORIGIN_SCALE_MIN", 0.92), float(origin_meta["origin_multiplier"]))
        match_ratio = _clamp01(base * min(1.0, target_score / max(min_score * 1.8, 1.0)) * origin_scale)
        candidate_name = "正财格" if month_god == "正财" else "偏财格"
        rows = [
            {
                "plugin": self.plugin_id,
                "fact": f"格局候选：月令财星落在 {month_god}，本局存在「{candidate_name}」方向。",
                "priority": self.registry_priority,
                "label": "财格候选",
                "meta": {
                    "pattern_candidate": candidate_name,
                    "target_god": month_god,
                    "month_main_god": month_god,
                    "projection_share": round(float((projection or {}).get(month_god, 1.0)), 4),
                    "cluster_projection": projection,
                    "match_ratio": round(match_ratio, 3),
                    "claim_type": "pattern_candidate",
                    "entity_scope": "pattern",
                    "exclusivity_key": "pattern_family",
                    "source_event": "pattern_family",
                    "confidence": self.registry_priority,
                    "static_basis": build_static_basis(
                        physics_tensor=physics_tensor,
                        target_god=month_god,
                        relation_family="pattern_wealth_star",
                        relation_members=[],
                    ),
                    "interaction_layer": detect_interaction_layer(
                        {"interaction_layer": "cross_layer"},
                        relation_family="pattern_wealth_star",
                    ),
                    "manifestation_state": _pattern_manifestation(
                        blockers=context.get("blockers"),
                        origin_type=str(origin_meta.get("origin_type") or ""),
                        target_is_strong=match_ratio >= 0.7,
                    ),
                    **origin_meta,
                },
            }
        ]
        return rows_dict_to_v17_facts(rows, causal_tier=self.causal_tier, default_plugin_id=self.plugin_id)


@dataclass
class SealStarPatternPlugin(V17PluginSpec):
    plugin_id: str = "classical.pattern.seal_star.v1"
    causal_tier: int = 3
    registry_priority: float = 0.738

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        month_god = _month_main_god(physics_tensor)
        if month_god not in {"正印", "偏印"}:
            return []
        scores = deity_scores_from_tensor(physics_tensor)
        target_score = float(scores.get(month_god, 0.0))
        min_score = _pattern_cfg(self.plugin_id, "SEAL_MIN_SCORE", 14.0)
        if target_score < min_score:
            return []
        origin_meta = _pattern_origin_meta(physics_tensor)
        context = _pattern_context(physics_tensor)
        fp = physics_tensor.get("four_pillars") if isinstance(physics_tensor.get("four_pillars"), dict) else {}
        day_gz = str(fp.get("day", "")).strip()
        daymaster = day_gz[0] if len(day_gz) >= 2 else "壬"
        projection = god_cluster_projection(
            physics_tensor=physics_tensor,
            base_god=month_god,
            day_master=daymaster,
            focus_branches=[_month_branch(physics_tensor)],
        )
        base = _pattern_cfg(self.plugin_id, "SEAL_MATCH_BASE", 0.74)
        origin_scale = max(_pattern_cfg(self.plugin_id, "SEAL_ORIGIN_SCALE_MIN", 0.92), float(origin_meta["origin_multiplier"]))
        match_ratio = _clamp01(base * min(1.0, target_score / max(min_score * 1.8, 1.0)) * origin_scale)
        candidate_name = "正印格" if month_god == "正印" else "偏印格"
        rows = [
            {
                "plugin": self.plugin_id,
                "fact": f"格局候选：月令印星落在 {month_god}，本局存在「{candidate_name}」方向。",
                "priority": self.registry_priority,
                "label": "印格候选",
                "meta": {
                    "pattern_candidate": candidate_name,
                    "target_god": month_god,
                    "month_main_god": month_god,
                    "projection_share": round(float((projection or {}).get(month_god, 1.0)), 4),
                    "cluster_projection": projection,
                    "match_ratio": round(match_ratio, 3),
                    "claim_type": "pattern_candidate",
                    "entity_scope": "pattern",
                    "exclusivity_key": "pattern_family",
                    "source_event": "pattern_family",
                    "confidence": self.registry_priority,
                    "static_basis": build_static_basis(
                        physics_tensor=physics_tensor,
                        target_god=month_god,
                        relation_family="pattern_seal_star",
                        relation_members=[],
                    ),
                    "interaction_layer": detect_interaction_layer(
                        {"interaction_layer": "cross_layer"},
                        relation_family="pattern_seal_star",
                    ),
                    "manifestation_state": _pattern_manifestation(
                        blockers=context.get("blockers"),
                        origin_type=str(origin_meta.get("origin_type") or ""),
                        target_is_strong=match_ratio >= 0.72,
                    ),
                    **origin_meta,
                },
            }
        ]
        return rows_dict_to_v17_facts(rows, causal_tier=self.causal_tier, default_plugin_id=self.plugin_id)


@dataclass
class YangRenPatternPlugin(V17PluginSpec):
    plugin_id: str = "classical.pattern.yangren.v1"
    causal_tier: int = 3
    registry_priority: float = 0.742

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        daymaster = _daymaster_stem(physics_tensor)
        month_branch = _month_branch(physics_tensor)
        blade_branch = YANGREN_BRANCH_BY_DAYMASTER.get(daymaster, "")
        if not daymaster or not blade_branch or month_branch != blade_branch:
            return []
        scores = deity_scores_from_tensor(physics_tensor)
        target_god = "劫财"
        target_score = float(scores.get(target_god, 0.0) + scores.get("比肩", 0.0))
        min_score = _pattern_cfg(self.plugin_id, "YANGREN_MIN_SCORE", 16.0)
        if target_score < min_score:
            return []
        origin_meta = _pattern_origin_meta(physics_tensor)
        context = _pattern_context(physics_tensor)
        projection = god_cluster_projection(
            physics_tensor=physics_tensor,
            base_god=target_god,
            day_master=daymaster,
            focus_branches=[month_branch],
        )
        base = _pattern_cfg(self.plugin_id, "YANGREN_MATCH_BASE", 0.8)
        origin_scale = max(_pattern_cfg(self.plugin_id, "YANGREN_ORIGIN_SCALE_MIN", 0.92), float(origin_meta["origin_multiplier"]))
        match_ratio = _clamp01(base * min(1.0, target_score / max(min_score * 1.7, 1.0)) * origin_scale)
        rows = [
            {
                "plugin": self.plugin_id,
                "fact": f"格局候选：日主 {daymaster} 于月令见羊刃位 {month_branch}，本局存在「羊刃格」方向。",
                "priority": self.registry_priority,
                "label": "羊刃候选",
                "meta": {
                    "pattern_candidate": "羊刃格",
                    "target_god": target_god,
                    "month_main_god": target_god,
                    "blade_branch": blade_branch,
                    "projection_share": round(float((projection or {}).get(target_god, 1.0)), 4),
                    "cluster_projection": projection,
                    "match_ratio": round(match_ratio, 3),
                    "claim_type": "pattern_candidate",
                    "entity_scope": "pattern",
                    "exclusivity_key": "pattern_family",
                    "source_event": "pattern_family",
                    "confidence": self.registry_priority,
                    "static_basis": build_static_basis(
                        physics_tensor=physics_tensor,
                        target_god=target_god,
                        relation_family="pattern_yangren",
                        relation_members=[month_branch],
                    ),
                    "interaction_layer": detect_interaction_layer(
                        {"interaction_layer": "cross_layer"},
                        relation_family="pattern_yangren",
                    ),
                    "manifestation_state": _pattern_manifestation(
                        blockers=context.get("blockers"),
                        origin_type=str(origin_meta.get("origin_type") or ""),
                        target_is_strong=match_ratio >= 0.76,
                    ),
                    **origin_meta,
                },
            }
        ]
        return rows_dict_to_v17_facts(rows, causal_tier=self.causal_tier, default_plugin_id=self.plugin_id)


@dataclass
class GuanYinPatternPlugin(V17PluginSpec):
    plugin_id: str = "classical.pattern.guanyin.v1"
    causal_tier: int = 3
    registry_priority: float = 0.748

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        scores = deity_scores_from_tensor(physics_tensor)
        guan = float(scores.get("正官", 0.0))
        seal = _score_sum(scores, "正印", "偏印")
        min_guan = _pattern_cfg(self.plugin_id, "GUANYIN_MIN_GUAN", 16.0)
        min_seal = _pattern_cfg(self.plugin_id, "GUANYIN_MIN_SEAL", 16.0)
        if guan < min_guan or seal < min_seal:
            return []
        origin_meta = _pattern_origin_meta(physics_tensor)
        context = _pattern_context(physics_tensor)
        fp = physics_tensor.get("four_pillars") if isinstance(physics_tensor.get("four_pillars"), dict) else {}
        day_gz = str(fp.get("day", "")).strip()
        daymaster = day_gz[0] if len(day_gz) >= 2 else "壬"
        projection = god_cluster_projection(
            physics_tensor=physics_tensor,
            base_god="正官",
            day_master=daymaster,
            focus_branches=[_month_branch(physics_tensor)],
        )
        base = _pattern_cfg(self.plugin_id, "GUANYIN_MATCH_BASE", 0.76)
        synergy = min(guan, seal) / max(guan, seal, 1.0)
        match_ratio = _clamp01(base * synergy * max(0.92, float(origin_meta["origin_multiplier"])))
        rows = [{
            "plugin": self.plugin_id,
            "fact": "格局候选：官星得印星相生，本局存在「官印相生」路线。",
            "priority": self.registry_priority,
            "label": "官印相生",
            "meta": {
                "pattern_candidate": "官印相生",
                "target_god": "正官",
                "guan_score": guan,
                "seal_score": seal,
                "projection_share": round(float((projection or {}).get("正官", 1.0)), 4),
                "cluster_projection": projection,
                "match_ratio": round(match_ratio, 3),
                "claim_type": "pattern_candidate",
                "entity_scope": "pattern",
                "exclusivity_key": "pattern_family",
                "source_event": "pattern_family",
                "confidence": self.registry_priority,
                "static_basis": build_static_basis(physics_tensor=physics_tensor, target_god="正官", relation_family="pattern_guanyin", relation_members=[]),
                "interaction_layer": detect_interaction_layer({"interaction_layer": "cross_layer"}, relation_family="pattern_guanyin"),
                "manifestation_state": _pattern_manifestation(blockers=context.get("blockers"), origin_type=str(origin_meta.get("origin_type") or ""), target_is_strong=match_ratio >= 0.74),
                **origin_meta,
            },
        }]
        return rows_dict_to_v17_facts(rows, causal_tier=self.causal_tier, default_plugin_id=self.plugin_id)


@dataclass
class ShaYinPatternPlugin(V17PluginSpec):
    plugin_id: str = "classical.pattern.shayin.v1"
    causal_tier: int = 3
    registry_priority: float = 0.749

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        scores = deity_scores_from_tensor(physics_tensor)
        sha = float(scores.get("七杀", 0.0))
        seal = _score_sum(scores, "正印", "偏印")
        min_sha = _pattern_cfg(self.plugin_id, "SHAYIN_MIN_SHA", 16.0)
        min_seal = _pattern_cfg(self.plugin_id, "SHAYIN_MIN_SEAL", 15.0)
        if sha < min_sha or seal < min_seal:
            return []
        origin_meta = _pattern_origin_meta(physics_tensor)
        context = _pattern_context(physics_tensor)
        fp = physics_tensor.get("four_pillars") if isinstance(physics_tensor.get("four_pillars"), dict) else {}
        day_gz = str(fp.get("day", "")).strip()
        daymaster = day_gz[0] if len(day_gz) >= 2 else "壬"
        projection = god_cluster_projection(
            physics_tensor=physics_tensor,
            base_god="七杀",
            day_master=daymaster,
            focus_branches=[_month_branch(physics_tensor)],
        )
        base = _pattern_cfg(self.plugin_id, "SHAYIN_MATCH_BASE", 0.76)
        synergy = min(sha, seal) / max(sha, seal, 1.0)
        match_ratio = _clamp01(base * synergy * max(0.92, float(origin_meta["origin_multiplier"])))
        rows = [{
            "plugin": self.plugin_id,
            "fact": "格局候选：七杀得印化生，本局存在「杀印相生」路线。",
            "priority": self.registry_priority,
            "label": "杀印相生",
            "meta": {
                "pattern_candidate": "杀印相生",
                "target_god": "七杀",
                "sha_score": sha,
                "seal_score": seal,
                "projection_share": round(float((projection or {}).get("七杀", 1.0)), 4),
                "cluster_projection": projection,
                "match_ratio": round(match_ratio, 3),
                "claim_type": "pattern_candidate",
                "entity_scope": "pattern",
                "exclusivity_key": "pattern_family",
                "source_event": "pattern_family",
                "confidence": self.registry_priority,
                "static_basis": build_static_basis(physics_tensor=physics_tensor, target_god="七杀", relation_family="pattern_shayin", relation_members=[]),
                "interaction_layer": detect_interaction_layer({"interaction_layer": "cross_layer"}, relation_family="pattern_shayin"),
                "manifestation_state": _pattern_manifestation(blockers=context.get("blockers"), origin_type=str(origin_meta.get("origin_type") or ""), target_is_strong=match_ratio >= 0.74),
                **origin_meta,
            },
        }]
        return rows_dict_to_v17_facts(rows, causal_tier=self.causal_tier, default_plugin_id=self.plugin_id)


@dataclass
class ShiShenZhiShaPatternPlugin(V17PluginSpec):
    plugin_id: str = "classical.pattern.shishen_zhisha.v1"
    causal_tier: int = 3
    registry_priority: float = 0.751

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        scores = deity_scores_from_tensor(physics_tensor)
        sha = float(scores.get("七杀", 0.0))
        shishen = float(scores.get("食神", 0.0))
        min_sha = _pattern_cfg(self.plugin_id, "SHISHEN_ZHISHA_MIN_SHA", 16.0)
        min_shishen = _pattern_cfg(self.plugin_id, "SHISHEN_ZHISHA_MIN_SHISHEN", 16.0)
        if sha < min_sha or shishen < min_shishen:
            return []
        origin_meta = _pattern_origin_meta(physics_tensor)
        context = _pattern_context(physics_tensor)
        fp = physics_tensor.get("four_pillars") if isinstance(physics_tensor.get("four_pillars"), dict) else {}
        day_gz = str(fp.get("day", "")).strip()
        daymaster = day_gz[0] if len(day_gz) >= 2 else "壬"
        projection = god_cluster_projection(
            physics_tensor=physics_tensor,
            base_god="七杀",
            day_master=daymaster,
            focus_branches=[_month_branch(physics_tensor)],
        )
        base = _pattern_cfg(self.plugin_id, "SHISHEN_ZHISHA_MATCH_BASE", 0.78)
        synergy = min(sha, shishen) / max(sha, shishen, 1.0)
        match_ratio = _clamp01(base * synergy * max(0.92, float(origin_meta["origin_multiplier"])))
        rows = [{
            "plugin": self.plugin_id,
            "fact": "格局候选：食神透而制杀，本局存在「食神制杀」路线。",
            "priority": self.registry_priority,
            "label": "食神制杀",
            "meta": {
                "pattern_candidate": "食神制杀",
                "target_god": "七杀",
                "sha_score": sha,
                "shishen_score": shishen,
                "projection_share": round(float((projection or {}).get("七杀", 1.0)), 4),
                "cluster_projection": projection,
                "match_ratio": round(match_ratio, 3),
                "claim_type": "pattern_candidate",
                "entity_scope": "pattern",
                "exclusivity_key": "pattern_family",
                "source_event": "pattern_family",
                "confidence": self.registry_priority,
                "static_basis": build_static_basis(physics_tensor=physics_tensor, target_god="七杀", relation_family="pattern_shishen_zhisha", relation_members=[]),
                "interaction_layer": detect_interaction_layer({"interaction_layer": "cross_layer"}, relation_family="pattern_shishen_zhisha"),
                "manifestation_state": _pattern_manifestation(blockers=context.get("blockers"), origin_type=str(origin_meta.get("origin_type") or ""), target_is_strong=match_ratio >= 0.76),
                **origin_meta,
            },
        }]
        return rows_dict_to_v17_facts(rows, causal_tier=self.causal_tier, default_plugin_id=self.plugin_id)


@dataclass
class ShangGuanPeiYinPatternPlugin(V17PluginSpec):
    plugin_id: str = "classical.pattern.shangguan_peiyin.v1"
    causal_tier: int = 3
    registry_priority: float = 0.747

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        scores = deity_scores_from_tensor(physics_tensor)
        hurt = float(scores.get("伤官", 0.0))
        seal = _score_sum(scores, "正印", "偏印")
        min_hurt = _pattern_cfg(self.plugin_id, "SHANGGUAN_PEIYIN_MIN_HURT", 16.0)
        min_seal = _pattern_cfg(self.plugin_id, "SHANGGUAN_PEIYIN_MIN_SEAL", 15.0)
        if hurt < min_hurt or seal < min_seal:
            return []
        origin_meta = _pattern_origin_meta(physics_tensor)
        context = _pattern_context(physics_tensor)
        fp = physics_tensor.get("four_pillars") if isinstance(physics_tensor.get("four_pillars"), dict) else {}
        day_gz = str(fp.get("day", "")).strip()
        daymaster = day_gz[0] if len(day_gz) >= 2 else "壬"
        projection = god_cluster_projection(
            physics_tensor=physics_tensor,
            base_god="伤官",
            day_master=daymaster,
            focus_branches=[_month_branch(physics_tensor)],
        )
        base = _pattern_cfg(self.plugin_id, "SHANGGUAN_PEIYIN_MATCH_BASE", 0.76)
        synergy = min(hurt, seal) / max(hurt, seal, 1.0)
        match_ratio = _clamp01(base * synergy * max(0.92, float(origin_meta["origin_multiplier"])))
        rows = [{
            "plugin": self.plugin_id,
            "fact": "格局候选：伤官旺而得印护，本局存在「伤官配印」路线。",
            "priority": self.registry_priority,
            "label": "伤官配印",
            "meta": {
                "pattern_candidate": "伤官配印",
                "target_god": "伤官",
                "hurt_score": hurt,
                "seal_score": seal,
                "projection_share": round(float((projection or {}).get("伤官", 1.0)), 4),
                "cluster_projection": projection,
                "match_ratio": round(match_ratio, 3),
                "claim_type": "pattern_candidate",
                "entity_scope": "pattern",
                "exclusivity_key": "pattern_family",
                "source_event": "pattern_family",
                "confidence": self.registry_priority,
                "static_basis": build_static_basis(physics_tensor=physics_tensor, target_god="伤官", relation_family="pattern_shangguan_peiyin", relation_members=[]),
                "interaction_layer": detect_interaction_layer({"interaction_layer": "cross_layer"}, relation_family="pattern_shangguan_peiyin"),
                "manifestation_state": _pattern_manifestation(blockers=context.get("blockers"), origin_type=str(origin_meta.get("origin_type") or ""), target_is_strong=match_ratio >= 0.74),
                **origin_meta,
            },
        }]
        return rows_dict_to_v17_facts(rows, causal_tier=self.causal_tier, default_plugin_id=self.plugin_id)


@dataclass
class ShiShenShengCaiPatternPlugin(V17PluginSpec):
    plugin_id: str = "classical.pattern.shishen_shengcai.v1"
    causal_tier: int = 3
    registry_priority: float = 0.746

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        scores = deity_scores_from_tensor(physics_tensor)
        shishen = float(scores.get("食神", 0.0))
        wealth = _score_sum(scores, "正财", "偏财")
        min_shishen = _pattern_cfg(self.plugin_id, "SHISHEN_SHENGCAI_MIN_SHISHEN", 16.0)
        min_wealth = _pattern_cfg(self.plugin_id, "SHISHEN_SHENGCAI_MIN_WEALTH", 15.0)
        if shishen < min_shishen or wealth < min_wealth:
            return []
        origin_meta = _pattern_origin_meta(physics_tensor)
        context = _pattern_context(physics_tensor)
        fp = physics_tensor.get("four_pillars") if isinstance(physics_tensor.get("four_pillars"), dict) else {}
        day_gz = str(fp.get("day", "")).strip()
        daymaster = day_gz[0] if len(day_gz) >= 2 else "壬"
        projection = god_cluster_projection(
            physics_tensor=physics_tensor,
            base_god="食神",
            day_master=daymaster,
            focus_branches=[_month_branch(physics_tensor)],
        )
        base = _pattern_cfg(self.plugin_id, "SHISHEN_SHENGCAI_MATCH_BASE", 0.76)
        synergy = min(shishen, wealth) / max(shishen, wealth, 1.0)
        match_ratio = _clamp01(base * synergy * max(0.92, float(origin_meta["origin_multiplier"])))
        rows = [{
            "plugin": self.plugin_id,
            "fact": "格局候选：食神有力而顺泄到财，本局存在「食神生财」路线。",
            "priority": self.registry_priority,
            "label": "食神生财",
            "meta": {
                "pattern_candidate": "食神生财",
                "target_god": "食神",
                "shishen_score": shishen,
                "wealth_score": wealth,
                "projection_share": round(float((projection or {}).get("食神", 1.0)), 4),
                "cluster_projection": projection,
                "match_ratio": round(match_ratio, 3),
                "claim_type": "pattern_candidate",
                "entity_scope": "pattern",
                "exclusivity_key": "pattern_family",
                "source_event": "pattern_family",
                "confidence": self.registry_priority,
                "static_basis": build_static_basis(physics_tensor=physics_tensor, target_god="食神", relation_family="pattern_shishen_shengcai", relation_members=[]),
                "interaction_layer": detect_interaction_layer({"interaction_layer": "cross_layer"}, relation_family="pattern_shishen_shengcai"),
                "manifestation_state": _pattern_manifestation(blockers=context.get("blockers"), origin_type=str(origin_meta.get("origin_type") or ""), target_is_strong=match_ratio >= 0.74),
                **origin_meta,
            },
        }]
        return rows_dict_to_v17_facts(rows, causal_tier=self.causal_tier, default_plugin_id=self.plugin_id)


@dataclass
class ShangGuanShengCaiPatternPlugin(V17PluginSpec):
    plugin_id: str = "classical.pattern.shangguan_shengcai.v1"
    causal_tier: int = 3
    registry_priority: float = 0.745

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        scores = deity_scores_from_tensor(physics_tensor)
        hurt = float(scores.get("伤官", 0.0))
        wealth = _score_sum(scores, "正财", "偏财")
        min_hurt = _pattern_cfg(self.plugin_id, "SHANGGUAN_SHENGCAI_MIN_HURT", 16.0)
        min_wealth = _pattern_cfg(self.plugin_id, "SHANGGUAN_SHENGCAI_MIN_WEALTH", 15.0)
        if hurt < min_hurt or wealth < min_wealth:
            return []
        origin_meta = _pattern_origin_meta(physics_tensor)
        context = _pattern_context(physics_tensor)
        fp = physics_tensor.get("four_pillars") if isinstance(physics_tensor.get("four_pillars"), dict) else {}
        day_gz = str(fp.get("day", "")).strip()
        daymaster = day_gz[0] if len(day_gz) >= 2 else "壬"
        projection = god_cluster_projection(
            physics_tensor=physics_tensor,
            base_god="伤官",
            day_master=daymaster,
            focus_branches=[_month_branch(physics_tensor)],
        )
        base = _pattern_cfg(self.plugin_id, "SHANGGUAN_SHENGCAI_MATCH_BASE", 0.76)
        synergy = min(hurt, wealth) / max(hurt, wealth, 1.0)
        match_ratio = _clamp01(base * synergy * max(0.92, float(origin_meta["origin_multiplier"])))
        rows = [{
            "plugin": self.plugin_id,
            "fact": "格局候选：伤官旺而化财，本局存在「伤官生财」路线。",
            "priority": self.registry_priority,
            "label": "伤官生财",
            "meta": {
                "pattern_candidate": "伤官生财",
                "target_god": "伤官",
                "hurt_score": hurt,
                "wealth_score": wealth,
                "projection_share": round(float((projection or {}).get("伤官", 1.0)), 4),
                "cluster_projection": projection,
                "match_ratio": round(match_ratio, 3),
                "claim_type": "pattern_candidate",
                "entity_scope": "pattern",
                "exclusivity_key": "pattern_family",
                "source_event": "pattern_family",
                "confidence": self.registry_priority,
                "static_basis": build_static_basis(physics_tensor=physics_tensor, target_god="伤官", relation_family="pattern_shangguan_shengcai", relation_members=[]),
                "interaction_layer": detect_interaction_layer({"interaction_layer": "cross_layer"}, relation_family="pattern_shangguan_shengcai"),
                "manifestation_state": _pattern_manifestation(blockers=context.get("blockers"), origin_type=str(origin_meta.get("origin_type") or ""), target_is_strong=match_ratio >= 0.74),
                **origin_meta,
            },
        }]
        return rows_dict_to_v17_facts(rows, causal_tier=self.causal_tier, default_plugin_id=self.plugin_id)


@dataclass
class YangRenJiaShaPatternPlugin(V17PluginSpec):
    plugin_id: str = "classical.pattern.yangren_jiasha.v1"
    causal_tier: int = 3
    registry_priority: float = 0.752

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        scores = deity_scores_from_tensor(physics_tensor)
        ren_score = _score_sum(scores, "劫财", "比肩")
        sha = float(scores.get("七杀", 0.0))
        min_ren = _pattern_cfg(self.plugin_id, "YANGREN_JIASHA_MIN_REN", 16.0)
        min_sha = _pattern_cfg(self.plugin_id, "YANGREN_JIASHA_MIN_SHA", 16.0)
        if ren_score < min_ren or sha < min_sha:
            return []
        origin_meta = _pattern_origin_meta(physics_tensor)
        context = _pattern_context(physics_tensor)
        fp = physics_tensor.get("four_pillars") if isinstance(physics_tensor.get("four_pillars"), dict) else {}
        day_gz = str(fp.get("day", "")).strip()
        daymaster = day_gz[0] if len(day_gz) >= 2 else "壬"
        projection = god_cluster_projection(
            physics_tensor=physics_tensor,
            base_god="七杀",
            day_master=daymaster,
            focus_branches=[_month_branch(physics_tensor)],
        )
        base = _pattern_cfg(self.plugin_id, "YANGREN_JIASHA_MATCH_BASE", 0.78)
        synergy = min(ren_score, sha) / max(ren_score, sha, 1.0)
        match_ratio = _clamp01(base * synergy * max(0.92, float(origin_meta["origin_multiplier"])))
        rows = [{
            "plugin": self.plugin_id,
            "fact": "格局候选：刃势与七杀并行，本局存在「阳刃驾杀」路线。",
            "priority": self.registry_priority,
            "label": "阳刃驾杀",
            "meta": {
                "pattern_candidate": "阳刃驾杀",
                "target_god": "七杀",
                "ren_score": ren_score,
                "sha_score": sha,
                "projection_share": round(float((projection or {}).get("七杀", 1.0)), 4),
                "cluster_projection": projection,
                "match_ratio": round(match_ratio, 3),
                "claim_type": "pattern_candidate",
                "entity_scope": "pattern",
                "exclusivity_key": "pattern_family",
                "source_event": "pattern_family",
                "confidence": self.registry_priority,
                "static_basis": build_static_basis(physics_tensor=physics_tensor, target_god="七杀", relation_family="pattern_yangren_jiasha", relation_members=[]),
                "interaction_layer": detect_interaction_layer({"interaction_layer": "cross_layer"}, relation_family="pattern_yangren_jiasha"),
                "manifestation_state": _pattern_manifestation(blockers=context.get("blockers"), origin_type=str(origin_meta.get("origin_type") or ""), target_is_strong=match_ratio >= 0.76),
                **origin_meta,
            },
        }]
        return rows_dict_to_v17_facts(rows, causal_tier=self.causal_tier, default_plugin_id=self.plugin_id)


@dataclass
class ZaQiCaiGuanPatternPlugin(V17PluginSpec):
    plugin_id: str = "classical.pattern.zaqi_caiguan.v1"
    causal_tier: int = 3
    registry_priority: float = 0.739

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        month_branch = _month_branch(physics_tensor)
        if not _is_zaji_month(month_branch):
            return []
        scores = deity_scores_from_tensor(physics_tensor)
        guan = _score_sum(scores, "正官", "偏财", "正财")
        min_score = _pattern_cfg(self.plugin_id, "ZAQI_CAIGUAN_MIN_SCORE", 14.0)
        if guan < min_score:
            return []
        origin_meta = _pattern_origin_meta(physics_tensor)
        match_ratio = _clamp01(_pattern_cfg(self.plugin_id, "ZAQI_CAIGUAN_MATCH_BASE", 0.72) * min(1.0, guan / max(min_score * 1.8, 1.0)) * max(0.92, float(origin_meta["origin_multiplier"])))
        rows = [{
            "plugin": self.plugin_id,
            "fact": f"格局候选：{month_branch} 月属杂气月，财官透势可入「杂气财官格」专题。",
            "priority": self.registry_priority,
            "label": "杂气财官",
            "meta": {
                "pattern_candidate": "杂气财官格",
                "target_god": "正官",
                "month_branch": month_branch,
                "match_ratio": round(match_ratio, 3),
                "claim_type": "pattern_candidate",
                "entity_scope": "pattern",
                "exclusivity_key": "pattern_family",
                "source_event": "pattern_family",
                "confidence": self.registry_priority,
                "static_basis": build_static_basis(physics_tensor=physics_tensor, target_god="正官", relation_family="pattern_zaqi_caiguan", relation_members=[month_branch]),
                "interaction_layer": detect_interaction_layer({"interaction_layer": "hidden"}, relation_family="pattern_zaqi_caiguan"),
                "manifestation_state": "supported",
                **origin_meta,
            },
        }]
        return rows_dict_to_v17_facts(rows, causal_tier=self.causal_tier, default_plugin_id=self.plugin_id)


@dataclass
class ZaQiYinPatternPlugin(V17PluginSpec):
    plugin_id: str = "classical.pattern.zaqi_yin.v1"
    causal_tier: int = 3
    registry_priority: float = 0.739

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        month_branch = _month_branch(physics_tensor)
        if not _is_zaji_month(month_branch):
            return []
        scores = deity_scores_from_tensor(physics_tensor)
        seal = _score_sum(scores, "正印", "偏印")
        min_score = _pattern_cfg(self.plugin_id, "ZAQI_YIN_MIN_SCORE", 14.0)
        if seal < min_score:
            return []
        origin_meta = _pattern_origin_meta(physics_tensor)
        match_ratio = _clamp01(_pattern_cfg(self.plugin_id, "ZAQI_YIN_MATCH_BASE", 0.72) * min(1.0, seal / max(min_score * 1.8, 1.0)) * max(0.92, float(origin_meta["origin_multiplier"])))
        rows = [{
            "plugin": self.plugin_id,
            "fact": f"格局候选：{month_branch} 月属杂气月，印绶透势可入「杂气印绶格」专题。",
            "priority": self.registry_priority,
            "label": "杂气印绶",
            "meta": {
                "pattern_candidate": "杂气印绶格",
                "target_god": "正印",
                "month_branch": month_branch,
                "match_ratio": round(match_ratio, 3),
                "claim_type": "pattern_candidate",
                "entity_scope": "pattern",
                "exclusivity_key": "pattern_family",
                "source_event": "pattern_family",
                "confidence": self.registry_priority,
                "static_basis": build_static_basis(physics_tensor=physics_tensor, target_god="正印", relation_family="pattern_zaqi_yin", relation_members=[month_branch]),
                "interaction_layer": detect_interaction_layer({"interaction_layer": "hidden"}, relation_family="pattern_zaqi_yin"),
                "manifestation_state": "supported",
                **origin_meta,
            },
        }]
        return rows_dict_to_v17_facts(rows, causal_tier=self.causal_tier, default_plugin_id=self.plugin_id)


@dataclass
class ZaQiQiShaPatternPlugin(V17PluginSpec):
    plugin_id: str = "classical.pattern.zaqi_qisha.v1"
    causal_tier: int = 3
    registry_priority: float = 0.741

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        month_branch = _month_branch(physics_tensor)
        if not _is_zaji_month(month_branch):
            return []
        scores = deity_scores_from_tensor(physics_tensor)
        sha = float(scores.get("七杀", 0.0))
        min_score = _pattern_cfg(self.plugin_id, "ZAQI_QISHA_MIN_SCORE", 14.0)
        if sha < min_score:
            return []
        origin_meta = _pattern_origin_meta(physics_tensor)
        match_ratio = _clamp01(_pattern_cfg(self.plugin_id, "ZAQI_QISHA_MATCH_BASE", 0.72) * min(1.0, sha / max(min_score * 1.8, 1.0)) * max(0.92, float(origin_meta["origin_multiplier"])))
        rows = [{
            "plugin": self.plugin_id,
            "fact": f"格局候选：{month_branch} 月属杂气月，七杀透势可入「杂气七杀格」专题。",
            "priority": self.registry_priority,
            "label": "杂气七杀",
            "meta": {
                "pattern_candidate": "杂气七杀格",
                "target_god": "七杀",
                "month_branch": month_branch,
                "match_ratio": round(match_ratio, 3),
                "claim_type": "pattern_candidate",
                "entity_scope": "pattern",
                "exclusivity_key": "pattern_family",
                "source_event": "pattern_family",
                "confidence": self.registry_priority,
                "static_basis": build_static_basis(physics_tensor=physics_tensor, target_god="七杀", relation_family="pattern_zaqi_qisha", relation_members=[month_branch]),
                "interaction_layer": detect_interaction_layer({"interaction_layer": "hidden"}, relation_family="pattern_zaqi_qisha"),
                "manifestation_state": "supported",
                **origin_meta,
            },
        }]
        return rows_dict_to_v17_facts(rows, causal_tier=self.causal_tier, default_plugin_id=self.plugin_id)


@dataclass
class CongCaiPatternPlugin(V17PluginSpec):
    plugin_id: str = "classical.pattern.congcai.v1"
    causal_tier: int = 3
    registry_priority: float = 0.743

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        scores = deity_scores_from_tensor(physics_tensor)
        wealth = _score_sum(scores, "正财", "偏财")
        peer = _score_sum(scores, "比肩", "劫财")
        if wealth < _pattern_cfg(self.plugin_id, "CONGCAI_MIN_WEALTH", 22.0) or peer > _pattern_cfg(self.plugin_id, "CONGCAI_MAX_PEER", 12.0):
            return []
        origin_meta = _pattern_origin_meta(physics_tensor)
        match_ratio = _clamp01(_pattern_cfg(self.plugin_id, "CONGCAI_MATCH_BASE", 0.74) * min(1.0, wealth / max(peer + wealth, 1.0)) * max(0.92, float(origin_meta["origin_multiplier"])))
        rows = [{
            "plugin": self.plugin_id,
            "fact": "格局候选：财势独旺而比劫不敌，本局存在「从财格」方向。",
            "priority": self.registry_priority,
            "label": "从财候选",
            "meta": {
                "pattern_candidate": "从财格",
                "target_god": "财星",
                "wealth_score": wealth,
                "peer_score": peer,
                "match_ratio": round(match_ratio, 3),
                "claim_type": "pattern_candidate",
                "entity_scope": "pattern",
                "exclusivity_key": "pattern_family",
                "source_event": "pattern_family",
                "confidence": self.registry_priority,
                "static_basis": build_static_basis(physics_tensor=physics_tensor, target_god="正财", relation_family="pattern_congcai", relation_members=[]),
                "interaction_layer": detect_interaction_layer({"interaction_layer": "cross_layer"}, relation_family="pattern_congcai"),
                "manifestation_state": "supported",
                **origin_meta,
            },
        }]
        return rows_dict_to_v17_facts(rows, causal_tier=self.causal_tier, default_plugin_id=self.plugin_id)


@dataclass
class CongShaPatternPlugin(V17PluginSpec):
    plugin_id: str = "classical.pattern.congsha.v1"
    causal_tier: int = 3
    registry_priority: float = 0.744

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        scores = deity_scores_from_tensor(physics_tensor)
        sha = float(scores.get("七杀", 0.0))
        peer = _score_sum(scores, "比肩", "劫财")
        if sha < _pattern_cfg(self.plugin_id, "CONGSHA_MIN_SHA", 22.0) or peer > _pattern_cfg(self.plugin_id, "CONGSHA_MAX_PEER", 12.0):
            return []
        origin_meta = _pattern_origin_meta(physics_tensor)
        match_ratio = _clamp01(_pattern_cfg(self.plugin_id, "CONGSHA_MATCH_BASE", 0.74) * min(1.0, sha / max(peer + sha, 1.0)) * max(0.92, float(origin_meta["origin_multiplier"])))
        rows = [{
            "plugin": self.plugin_id,
            "fact": "格局候选：七杀成势而身党不敌，本局存在「从杀格」方向。",
            "priority": self.registry_priority,
            "label": "从杀候选",
            "meta": {
                "pattern_candidate": "从杀格",
                "target_god": "七杀",
                "sha_score": sha,
                "peer_score": peer,
                "match_ratio": round(match_ratio, 3),
                "claim_type": "pattern_candidate",
                "entity_scope": "pattern",
                "exclusivity_key": "pattern_family",
                "source_event": "pattern_family",
                "confidence": self.registry_priority,
                "static_basis": build_static_basis(physics_tensor=physics_tensor, target_god="七杀", relation_family="pattern_congsha", relation_members=[]),
                "interaction_layer": detect_interaction_layer({"interaction_layer": "cross_layer"}, relation_family="pattern_congsha"),
                "manifestation_state": "supported",
                **origin_meta,
            },
        }]
        return rows_dict_to_v17_facts(rows, causal_tier=self.causal_tier, default_plugin_id=self.plugin_id)


@dataclass
class CongErPatternPlugin(V17PluginSpec):
    plugin_id: str = "classical.pattern.conger.v1"
    causal_tier: int = 3
    registry_priority: float = 0.742

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        scores = deity_scores_from_tensor(physics_tensor)
        output_total = _score_sum(scores, "食神", "伤官")
        seal = _score_sum(scores, "正印", "偏印")
        if output_total < _pattern_cfg(self.plugin_id, "CONGER_MIN_OUTPUT", 24.0) or seal > _pattern_cfg(self.plugin_id, "CONGER_MAX_SEAL", 12.0):
            return []
        origin_meta = _pattern_origin_meta(physics_tensor)
        match_ratio = _clamp01(_pattern_cfg(self.plugin_id, "CONGER_MATCH_BASE", 0.74) * min(1.0, output_total / max(output_total + seal, 1.0)) * max(0.92, float(origin_meta["origin_multiplier"])))
        rows = [{
            "plugin": self.plugin_id,
            "fact": "格局候选：食伤成党而印比不足回身，本局存在「从儿格」方向。",
            "priority": self.registry_priority,
            "label": "从儿候选",
            "meta": {
                "pattern_candidate": "从儿格",
                "target_god": "食伤",
                "output_score": output_total,
                "seal_score": seal,
                "match_ratio": round(match_ratio, 3),
                "claim_type": "pattern_candidate",
                "entity_scope": "pattern",
                "exclusivity_key": "pattern_family",
                "source_event": "pattern_family",
                "confidence": self.registry_priority,
                "static_basis": build_static_basis(physics_tensor=physics_tensor, target_god="食神", relation_family="pattern_conger", relation_members=[]),
                "interaction_layer": detect_interaction_layer({"interaction_layer": "cross_layer"}, relation_family="pattern_conger"),
                "manifestation_state": "supported",
                **origin_meta,
            },
        }]
        return rows_dict_to_v17_facts(rows, causal_tier=self.causal_tier, default_plugin_id=self.plugin_id)


@dataclass
class CongWangPatternPlugin(V17PluginSpec):
    plugin_id: str = "classical.pattern.congwang.v1"
    causal_tier: int = 3
    registry_priority: float = 0.741

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        scores = deity_scores_from_tensor(physics_tensor)
        peer = _score_sum(scores, "比肩", "劫财")
        other = max(_score_sum(scores, "正财", "偏财"), _score_sum(scores, "正官", "七杀"), _score_sum(scores, "食神", "伤官"))
        if peer < _pattern_cfg(self.plugin_id, "CONGWANG_MIN_PEER", 30.0) or other > _pattern_cfg(self.plugin_id, "CONGWANG_MAX_OTHER", 14.0):
            return []
        origin_meta = _pattern_origin_meta(physics_tensor)
        match_ratio = _clamp01(_pattern_cfg(self.plugin_id, "CONGWANG_MATCH_BASE", 0.76) * min(1.0, peer / max(peer + other, 1.0)) * max(0.92, float(origin_meta["origin_multiplier"])))
        rows = [{
            "plugin": self.plugin_id,
            "fact": "格局候选：比劫印党一边独旺，本局存在「从旺格」方向。",
            "priority": self.registry_priority,
            "label": "从旺候选",
            "meta": {
                "pattern_candidate": "从旺格",
                "target_god": "比劫",
                "peer_score": peer,
                "other_score": other,
                "match_ratio": round(match_ratio, 3),
                "claim_type": "pattern_candidate",
                "entity_scope": "pattern",
                "exclusivity_key": "pattern_family",
                "source_event": "pattern_family",
                "confidence": self.registry_priority,
                "static_basis": build_static_basis(physics_tensor=physics_tensor, target_god="比肩", relation_family="pattern_congwang", relation_members=[]),
                "interaction_layer": detect_interaction_layer({"interaction_layer": "cross_layer"}, relation_family="pattern_congwang"),
                "manifestation_state": "supported",
                **origin_meta,
            },
        }]
        return rows_dict_to_v17_facts(rows, causal_tier=self.causal_tier, default_plugin_id=self.plugin_id)


@dataclass
class CongQiangPatternPlugin(V17PluginSpec):
    plugin_id: str = "classical.pattern.congqiang.v1"
    causal_tier: int = 3
    registry_priority: float = 0.74

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        scores = deity_scores_from_tensor(physics_tensor)
        peer = _score_sum(scores, "比肩", "劫财") + _score_sum(scores, "正印", "偏印")
        other = max(_score_sum(scores, "正财", "偏财"), _score_sum(scores, "正官", "七杀"), _score_sum(scores, "食神", "伤官"))
        if peer < _pattern_cfg(self.plugin_id, "CONGQIANG_MIN_PEER", 28.0) or other > _pattern_cfg(self.plugin_id, "CONGQIANG_MAX_OTHER", 15.0):
            return []
        origin_meta = _pattern_origin_meta(physics_tensor)
        match_ratio = _clamp01(_pattern_cfg(self.plugin_id, "CONGQIANG_MATCH_BASE", 0.75) * min(1.0, peer / max(peer + other, 1.0)) * max(0.92, float(origin_meta["origin_multiplier"])))
        rows = [{
            "plugin": self.plugin_id,
            "fact": "格局候选：印比同党压倒异党，本局存在「从强格」方向。",
            "priority": self.registry_priority,
            "label": "从强候选",
            "meta": {
                "pattern_candidate": "从强格",
                "target_god": "比劫",
                "peer_score": peer,
                "other_score": other,
                "match_ratio": round(match_ratio, 3),
                "claim_type": "pattern_candidate",
                "entity_scope": "pattern",
                "exclusivity_key": "pattern_family",
                "source_event": "pattern_family",
                "confidence": self.registry_priority,
                "static_basis": build_static_basis(physics_tensor=physics_tensor, target_god="比肩", relation_family="pattern_congqiang", relation_members=[]),
                "interaction_layer": detect_interaction_layer({"interaction_layer": "cross_layer"}, relation_family="pattern_congqiang"),
                "manifestation_state": "supported",
                **origin_meta,
            },
        }]
        return rows_dict_to_v17_facts(rows, causal_tier=self.causal_tier, default_plugin_id=self.plugin_id)


@dataclass
class CongRuoPatternPlugin(V17PluginSpec):
    plugin_id: str = "classical.pattern.congruo.v1"
    causal_tier: int = 3
    registry_priority: float = 0.738

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        scores = deity_scores_from_tensor(physics_tensor)
        peer = _score_sum(scores, "比肩", "劫财") + _score_sum(scores, "正印", "偏印")
        other = max(_score_sum(scores, "正财", "偏财"), _score_sum(scores, "正官", "七杀"), _score_sum(scores, "食神", "伤官"))
        if peer > _pattern_cfg(self.plugin_id, "CONGRUO_MAX_PEER", 10.0) or other < _pattern_cfg(self.plugin_id, "CONGRUO_MIN_OTHER", 24.0):
            return []
        origin_meta = _pattern_origin_meta(physics_tensor)
        match_ratio = _clamp01(_pattern_cfg(self.plugin_id, "CONGRUO_MATCH_BASE", 0.72) * min(1.0, other / max(peer + other, 1.0)) * max(0.92, float(origin_meta["origin_multiplier"])))
        rows = [{
            "plugin": self.plugin_id,
            "fact": "格局候选：身党极弱而异党成势，本局存在「从弱格」方向。",
            "priority": self.registry_priority,
            "label": "从弱候选",
            "meta": {
                "pattern_candidate": "从弱格",
                "target_god": "异党",
                "peer_score": peer,
                "other_score": other,
                "match_ratio": round(match_ratio, 3),
                "claim_type": "pattern_candidate",
                "entity_scope": "pattern",
                "exclusivity_key": "pattern_family",
                "source_event": "pattern_family",
                "confidence": self.registry_priority,
                "static_basis": build_static_basis(physics_tensor=physics_tensor, target_god="正官", relation_family="pattern_congruo", relation_members=[]),
                "interaction_layer": detect_interaction_layer({"interaction_layer": "cross_layer"}, relation_family="pattern_congruo"),
                "manifestation_state": "supported",
                **origin_meta,
            },
        }]
        return rows_dict_to_v17_facts(rows, causal_tier=self.causal_tier, default_plugin_id=self.plugin_id)


@dataclass
class HuaQiPatternPlugin(V17PluginSpec):
    plugin_id: str = "classical.pattern.huaqi.v1"
    causal_tier: int = 3
    registry_priority: float = 0.737

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        stems, branches = _visible_stems_and_branches(physics_tensor)
        pairs = {("甲", "己"): "土", ("乙", "庚"): "金", ("丙", "辛"): "水", ("丁", "壬"): "木", ("戊", "癸"): "火"}
        found = ""
        for (a, b), element in pairs.items():
            if a in stems and b in stems:
                found = f"{a}{b}化{element}"
                break
        if not found:
            return []
        origin_meta = _pattern_origin_meta(physics_tensor)
        match_ratio = round(max(_pattern_cfg(self.plugin_id, "HUAQI_MIN_MATCH", 0.72), min(0.9, 0.72 * max(0.92, float(origin_meta["origin_multiplier"])))), 3)
        rows = [{
            "plugin": self.plugin_id,
            "fact": f"格局候选：天干见合化胚象（{found}），本局存在「化气格」方向。",
            "priority": self.registry_priority,
            "label": "化气候选",
            "meta": {
                "pattern_candidate": "化气格",
                "target_god": "化气",
                "huaqi_signature": found,
                "branches": branches,
                "match_ratio": match_ratio,
                "claim_type": "pattern_candidate",
                "entity_scope": "pattern",
                "exclusivity_key": "pattern_family",
                "source_event": "pattern_family",
                "confidence": self.registry_priority,
                "static_basis": build_static_basis(physics_tensor=physics_tensor, target_god="", relation_family="pattern_huaqi", relation_members=branches[:2]),
                "interaction_layer": detect_interaction_layer({"interaction_layer": "stem"}, relation_family="pattern_huaqi"),
                "manifestation_state": "latent",
                **origin_meta,
            },
        }]
        return rows_dict_to_v17_facts(rows, causal_tier=self.causal_tier, default_plugin_id=self.plugin_id)


def _specialized_pattern_row(*, plugin_id: str, pattern_name: str, element: str, target_god: str, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
    scores = deity_scores_from_tensor(physics_tensor)
    dominant_element, top_score, second_score = _dominant_element(scores)
    if dominant_element != element:
        return []
    min_score = _pattern_cfg(plugin_id, "SPECIALIZED_MIN_SCORE", 26.0)
    max_other = _pattern_cfg(plugin_id, "SPECIALIZED_MAX_OTHER", 14.0)
    if top_score < min_score or second_score > max_other:
        return []
    origin_meta = _pattern_origin_meta(physics_tensor)
    match_ratio = _clamp01(_pattern_cfg(plugin_id, "SPECIALIZED_MATCH_BASE", 0.76) * min(1.0, top_score / max(top_score + second_score, 1.0)) * max(0.92, float(origin_meta["origin_multiplier"])))
    rows = [{
        "plugin": plugin_id,
        "fact": f"格局候选：{element}气专旺成势，本局存在「{pattern_name}」方向。",
        "priority": 0.736,
        "label": "专旺候选",
        "meta": {
            "pattern_candidate": pattern_name,
            "target_god": target_god,
            "dominant_element": element,
            "match_ratio": round(match_ratio, 3),
            "claim_type": "pattern_candidate",
            "entity_scope": "pattern",
            "exclusivity_key": "pattern_family",
            "source_event": "pattern_family",
            "confidence": 0.736,
            "static_basis": build_static_basis(physics_tensor=physics_tensor, target_god=target_god, relation_family=f"pattern_{plugin_id.split('.')[-2]}", relation_members=[]),
            "interaction_layer": detect_interaction_layer({"interaction_layer": "cross_layer"}, relation_family=f"pattern_{plugin_id.split('.')[-2]}"),
            "manifestation_state": "supported",
            **origin_meta,
        },
    }]
    return rows_dict_to_v17_facts(rows, causal_tier=3, default_plugin_id=plugin_id)


@dataclass
class QuZhiPatternPlugin(V17PluginSpec):
    plugin_id: str = "classical.pattern.quzhi.v1"
    causal_tier: int = 3
    registry_priority: float = 0.736

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        return _specialized_pattern_row(plugin_id=self.plugin_id, pattern_name="曲直格", element="木", target_god="比肩", physics_tensor=physics_tensor)


@dataclass
class YanShangPatternPlugin(V17PluginSpec):
    plugin_id: str = "classical.pattern.yanshang.v1"
    causal_tier: int = 3
    registry_priority: float = 0.736

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        return _specialized_pattern_row(plugin_id=self.plugin_id, pattern_name="炎上格", element="火", target_god="伤官", physics_tensor=physics_tensor)


@dataclass
class JiaSePatternPlugin(V17PluginSpec):
    plugin_id: str = "classical.pattern.jiase.v1"
    causal_tier: int = 3
    registry_priority: float = 0.736

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        return _specialized_pattern_row(plugin_id=self.plugin_id, pattern_name="稼穑格", element="土", target_god="正财", physics_tensor=physics_tensor)


@dataclass
class CongGePatternPlugin(V17PluginSpec):
    plugin_id: str = "classical.pattern.congge.v1"
    causal_tier: int = 3
    registry_priority: float = 0.736

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        return _specialized_pattern_row(plugin_id=self.plugin_id, pattern_name="从革格", element="金", target_god="正官", physics_tensor=physics_tensor)


@dataclass
class RunXiaPatternPlugin(V17PluginSpec):
    plugin_id: str = "classical.pattern.runxia.v1"
    causal_tier: int = 3
    registry_priority: float = 0.736

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        return _specialized_pattern_row(plugin_id=self.plugin_id, pattern_name="润下格", element="水", target_god="正印", physics_tensor=physics_tensor)


@dataclass
class LiangShenPatternPlugin(V17PluginSpec):
    plugin_id: str = "classical.pattern.liangshen.v1"
    causal_tier: int = 3
    registry_priority: float = 0.734

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        scores = deity_scores_from_tensor(physics_tensor)
        ordered = sorted(scores.items(), key=lambda kv: float(kv[1]), reverse=True)[:2]
        if len(ordered) < 2:
            return []
        (g1, v1), (g2, v2) = ordered
        min_pair = _pattern_cfg(self.plugin_id, "LIANGSHEN_MIN_PAIR", 18.0)
        if float(v1) < min_pair or float(v2) < min_pair:
            return []
        origin_meta = _pattern_origin_meta(physics_tensor)
        match_ratio = _clamp01(_pattern_cfg(self.plugin_id, "LIANGSHEN_MATCH_BASE", 0.72) * (min(float(v1), float(v2)) / max(float(v1), float(v2), 1.0)) * max(0.92, float(origin_meta["origin_multiplier"])))
        rows = [{
            "plugin": self.plugin_id,
            "fact": f"格局候选：{g1} 与 {g2} 双神并峙，本局存在「两神成象」方向。",
            "priority": self.registry_priority,
            "label": "两神成象",
            "meta": {
                "pattern_candidate": "两神成象",
                "target_god": str(g1),
                "pair_gods": [str(g1), str(g2)],
                "match_ratio": round(match_ratio, 3),
                "claim_type": "pattern_candidate",
                "entity_scope": "pattern",
                "exclusivity_key": "pattern_family",
                "source_event": "pattern_family",
                "confidence": self.registry_priority,
                "static_basis": build_static_basis(physics_tensor=physics_tensor, target_god=str(g1), relation_family="pattern_liangshen", relation_members=[]),
                "interaction_layer": detect_interaction_layer({"interaction_layer": "cross_layer"}, relation_family="pattern_liangshen"),
                "manifestation_state": "supported",
                **origin_meta,
            },
        }]
        return rows_dict_to_v17_facts(rows, causal_tier=self.causal_tier, default_plugin_id=self.plugin_id)


@dataclass
class TianYuanPatternPlugin(V17PluginSpec):
    plugin_id: str = "classical.pattern.tianyuan.v1"
    causal_tier: int = 3
    registry_priority: float = 0.733

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        stems, branches = _visible_stems_and_branches(physics_tensor)
        if not stems:
            return []
        unique_stems = set(stems)
        same_count = max(stems.count(stem) for stem in unique_stems)
        if same_count < _pattern_cfg(self.plugin_id, "TIANYUAN_MIN_SAME", 3.0):
            return []
        origin_meta = _pattern_origin_meta(physics_tensor)
        match_ratio = _clamp01(_pattern_cfg(self.plugin_id, "TIANYUAN_MATCH_BASE", 0.7) * min(1.0, same_count / 4.0) * max(0.92, float(origin_meta["origin_multiplier"])))
        dominant = max(unique_stems, key=stems.count)
        rows = [{
            "plugin": self.plugin_id,
            "fact": f"格局候选：天干同气重复达 {same_count} 次，本局存在「天元一气」方向。",
            "priority": self.registry_priority,
            "label": "天元一气",
            "meta": {
                "pattern_candidate": "天元一气",
                "target_god": ten_god_from_stems(_daymaster_stem(physics_tensor) or dominant, dominant),
                "dominant_stem": dominant,
                "branches": branches,
                "match_ratio": round(match_ratio, 3),
                "claim_type": "pattern_candidate",
                "entity_scope": "pattern",
                "exclusivity_key": "pattern_family",
                "source_event": "pattern_family",
                "confidence": self.registry_priority,
                "static_basis": build_static_basis(physics_tensor=physics_tensor, target_god="", relation_family="pattern_tianyuan", relation_members=branches[:2]),
                "interaction_layer": detect_interaction_layer({"interaction_layer": "stem"}, relation_family="pattern_tianyuan"),
                "manifestation_state": "supported",
                **origin_meta,
            },
        }]
        return rows_dict_to_v17_facts(rows, causal_tier=self.causal_tier, default_plugin_id=self.plugin_id)


@dataclass
class PatternResolverPlugin(V17PluginSpec):
    plugin_id: str = "classical.pattern.resolver.v1"
    causal_tier: int = 3
    registry_priority: float = 0.81

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        candidates = _pattern_candidates(physics_tensor)
        if len(candidates) < 2:
            return []
        origin_meta = _pattern_origin_meta(physics_tensor)
        candidate_names = [name for name, _axis, _score in candidates]
        axis_names = [axis for _name, axis, _score in candidates]
        unique_names = sorted(set(candidate_names))
        if len(unique_names) == 1:
            return []
        rows = [
            {
                "plugin": self.plugin_id,
                "fact": f"格局冲突审计：当前并存 {len(unique_names)} 条候选路径（{' / '.join(unique_names)}），需要以月令与主轴统一裁决。",
                "priority": 0.81,
                "label": "格局冲突裁决",
                "meta": {
                    "pattern_candidate_count": len(unique_names),
                    "pattern_candidates": unique_names,
                    "pattern_axes": sorted(set(axis_names)),
                    "observe_only": True,
                    "claim_type": "pattern_observation",
                    "entity_scope": "pattern",
                    "exclusivity_key": "pattern_family",
                    "source_event": "pattern_family",
                    "static_basis": build_static_basis(
                        physics_tensor=physics_tensor,
                        target_god=str(axis_names[0] if axis_names else ""),
                        relation_family="pattern_resolver",
                        relation_members=[],
                    ),
                    "interaction_layer": detect_interaction_layer(
                        {"interaction_layer": "cross_layer"},
                        relation_family="pattern_resolver",
                    ),
                    "manifestation_state": "supported",
                    **origin_meta,
                },
            }
        ]
        return rows_dict_to_v17_facts(rows, causal_tier=self.causal_tier, default_plugin_id=self.plugin_id)


@dataclass
class PatternFormationGatePlugin(V17PluginSpec):
    plugin_id: str = "classical.pattern.formation_gate.v1"
    causal_tier: int = 3
    registry_priority: float = 0.8

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        context = _pattern_context(physics_tensor)
        candidates = _pattern_candidates(physics_tensor)
        if not candidates:
            return []
        origin_meta = _pattern_origin_meta(physics_tensor)
        formation_ratio = _pattern_cfg("classical.pattern.axis.v1", "FORMATION_STRENGTH_RATIO", 2.0)
        month_god = str(context["month_god"] or "")
        top_name = str(context["top_name"] or "")
        top_ratio = float(context["dominant_ratio"] or 0.0)
        best_gate = "弱成立"
        best_reason = "候选已出现，但暂未形成稳定成格条件。"
        if month_god in {"比肩", "劫财"} and any(name == "建禄/月劫" for name, _axis, _score in candidates):
            best_gate = "月令成格"
            best_reason = "月令主气直接落在比劫轴，格局具备优先成形条件。"
        elif top_ratio >= formation_ratio and any(name == "从势候选" for name, _axis, _score in candidates):
            best_gate = "强轴成格"
            best_reason = f"{top_name} 一枝独强，主轴比值已达 {top_ratio:.2f}。"
        elif any(name == "财官协同" for name, _axis, _score in candidates):
            best_gate = "双线成格"
            best_reason = "财官双线并举，具备协同成格的结构基础。"
        rows = [
            {
                "plugin": self.plugin_id,
                "fact": f"成格条件审计：当前属于「{best_gate}」。{best_reason}",
                "priority": 0.8,
                "label": "成格条件",
                "meta": {
                    "pattern_gate": best_gate,
                    "pattern_gate_reason": best_reason,
                    "dominant_ratio": top_ratio,
                    "month_main_god": month_god,
                    "observe_only": True,
                    "claim_type": "pattern_observation",
                    "entity_scope": "pattern",
                    "exclusivity_key": "pattern_family",
                    "source_event": "pattern_family",
                    "static_basis": build_static_basis(
                        physics_tensor=physics_tensor,
                        target_god=str(context.get("top_name") or month_god or ""),
                        relation_family="pattern_formation_gate",
                        relation_members=[],
                    ),
                    "interaction_layer": detect_interaction_layer(
                        {"interaction_layer": "cross_layer"},
                        relation_family="pattern_formation_gate",
                    ),
                    "manifestation_state": "supported" if len(candidates) >= 2 else "contested",
                    **origin_meta,
                },
            }
        ]
        return rows_dict_to_v17_facts(rows, causal_tier=self.causal_tier, default_plugin_id=self.plugin_id)


@dataclass
class PatternBreakGuardPlugin(V17PluginSpec):
    plugin_id: str = "classical.pattern.break_guard.v1"
    causal_tier: int = 3
    registry_priority: float = 0.79

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        context = _pattern_context(physics_tensor)
        candidates = _pattern_candidates(physics_tensor)
        blockers = list(context.get("blockers") or [])
        if not candidates or not blockers:
            return []
        origin_meta = _pattern_origin_meta(physics_tensor)
        rows = [
            {
                "plugin": self.plugin_id,
                "fact": f"破格预警：当前格局候选受到 {' / '.join(blockers)} 干扰，后续专题应优先核验是否破格。",
                "priority": 0.79,
                "label": "破格预警",
                "meta": {
                    "pattern_break_risks": blockers,
                    "pattern_candidate_count": len(candidates),
                    "observe_only": True,
                    "claim_type": "pattern_observation",
                    "entity_scope": "pattern",
                    "exclusivity_key": "pattern_family",
                    "source_event": "pattern_family",
                    "static_basis": build_static_basis(
                        physics_tensor=physics_tensor,
                        target_god=str(context.get("top_name") or ""),
                        relation_family="pattern_break_guard",
                        relation_members=[],
                    ),
                    "interaction_layer": detect_interaction_layer(
                        {"interaction_layer": "cross_layer"},
                        relation_family="pattern_break_guard",
                    ),
                    "manifestation_state": "supported" if blockers else "contested",
                    **origin_meta,
                },
            }
        ]
        return rows_dict_to_v17_facts(rows, causal_tier=self.causal_tier, default_plugin_id=self.plugin_id)


PLUGINS = [
    PatternAxisPlugin(),
    PatternDynamicScopePlugin(),
    JianLuYueJiePlugin(),
    CongShiPlugin(),
    FinanceOfficerPatternPlugin(),
    WealthStarPatternPlugin(),
    SealStarPatternPlugin(),
    YangRenPatternPlugin(),
    GuanYinPatternPlugin(),
    ShaYinPatternPlugin(),
    ShiShenZhiShaPatternPlugin(),
    ShangGuanPeiYinPatternPlugin(),
    ShiShenShengCaiPatternPlugin(),
    ShangGuanShengCaiPatternPlugin(),
    YangRenJiaShaPatternPlugin(),
    ZaQiCaiGuanPatternPlugin(),
    ZaQiYinPatternPlugin(),
    ZaQiQiShaPatternPlugin(),
    CongCaiPatternPlugin(),
    CongShaPatternPlugin(),
    CongErPatternPlugin(),
    CongWangPatternPlugin(),
    CongQiangPatternPlugin(),
    CongRuoPatternPlugin(),
    HuaQiPatternPlugin(),
    QuZhiPatternPlugin(),
    YanShangPatternPlugin(),
    JiaSePatternPlugin(),
    CongGePatternPlugin(),
    RunXiaPatternPlugin(),
    LiangShenPatternPlugin(),
    TianYuanPatternPlugin(),
    PatternResolverPlugin(),
    PatternFormationGatePlugin(),
    PatternBreakGuardPlugin(),
]
