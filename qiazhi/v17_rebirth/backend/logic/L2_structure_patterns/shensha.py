from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from v17_rebirth.backend.logic.L1_atomic_ops.plugin_condition_protocol import (
    choose_dominant_origin_type,
    collect_origin_types_from_rows,
    detect_relation_origin_type,
    relation_origin_multiplier,
)
from v17_rebirth.backend.logic.L0_physics_fields.vector_physics_engine import _branch_dominant_ten_god
from v17_rebirth.backend.logic.L1_atomic_ops.relation_cluster_projection import god_cluster_projection
from v17_rebirth.backend.logic.plugin_discovery import deity_scores_from_tensor, rows_dict_to_v17_facts
from v17_rebirth.backend.plugins.spec import V17Fact, V17PluginSpec

# V17.99 Skill Specification
V17_SKILL_MANIFEST = {
    "id": "shensha",
    "Layer": "L2",
    "Skill_Type": "Pattern",
    "Domain": "Aura",
    "Description": "把传统神煞语义压缩为可量化的物理场强 Buff/Debuff。",
    "Rationale": "神煞是 L2 级的场变量修正项，它并不改变 L0/L1 的质量与矢量，但改变外部压力的感知强度。"
}

DECLARED_PARAMS = {
    "TIAN_YI_THRESHOLD": 40.0,     # 天乙显化所需正印能量
    "YANG_REN_THRESHOLD": 45.0,     # 羊刃显化所需劫财能量
    "RESISTANCE_BUFF": 0.1,         # 天乙抗性加成比例
    "TENSION_MULTIPLIER": 1.4,      # 羊刃张力乘数
    "PRIORITY_BASE": 0.94,          # 事实输出优先级
    "BRANCH_SHENSHA_PRIORITY": 0.82,
    "BRANCH_SHENSHA_MATCH_RATIO": 0.68,
    "BRANCH_SHENSHA_MAX_ROWS": 8,
}


TIAN_YI_BRANCHES = {
    "甲": ("丑", "未"),
    "戊": ("丑", "未"),
    "庚": ("丑", "未"),
    "乙": ("子", "申"),
    "己": ("子", "申"),
    "丙": ("亥", "酉"),
    "丁": ("亥", "酉"),
    "壬": ("卯", "巳"),
    "癸": ("卯", "巳"),
    "辛": ("寅", "午"),
}

WEN_CHANG_BRANCH = {
    "甲": "巳",
    "乙": "午",
    "丙": "申",
    "丁": "酉",
    "戊": "申",
    "己": "酉",
    "庚": "亥",
    "辛": "子",
    "壬": "寅",
    "癸": "卯",
}

LU_BRANCH = {
    "甲": "寅",
    "乙": "卯",
    "丙": "巳",
    "丁": "午",
    "戊": "巳",
    "己": "午",
    "庚": "申",
    "辛": "酉",
    "壬": "亥",
    "癸": "子",
}

YANG_REN_BRANCH = {
    "甲": "卯",
    "乙": "寅",
    "丙": "午",
    "丁": "巳",
    "戊": "午",
    "己": "巳",
    "庚": "酉",
    "辛": "申",
    "壬": "子",
    "癸": "亥",
}

GROUP_SHENSHA_BRANCHES = {
    frozenset(("申", "子", "辰")): {"桃花": "酉", "驿马": "寅", "华盖": "辰", "将星": "子"},
    frozenset(("寅", "午", "戌")): {"桃花": "卯", "驿马": "申", "华盖": "戌", "将星": "午"},
    frozenset(("巳", "酉", "丑")): {"桃花": "午", "驿马": "亥", "华盖": "丑", "将星": "酉"},
    frozenset(("亥", "卯", "未")): {"桃花": "子", "驿马": "巳", "华盖": "未", "将星": "卯"},
}

SHENSHA_HINTS = {
    "天乙贵人": "护持、解围与资源托底",
    "文昌": "学习、表达、文书与技术说明",
    "禄神": "稳定资源、职位落点与自持力",
    "羊刃": "强行动力、边界张力与冲突风险",
    "桃花": "人缘、审美、曝光与关系吸引",
    "驿马": "移动、迁移、差旅与变化机会",
    "华盖": "孤高、研究、宗教艺术与内向专注",
    "将星": "主导、组织、号令与承担责任",
}


def _branch_from_ganzhi(value: Any) -> str:
    raw = str(value or "").strip()
    if len(raw) >= 2:
        return raw[1]
    return raw


def _stem_from_ganzhi(value: Any) -> str:
    raw = str(value or "").strip()
    return raw[0] if len(raw) >= 2 else ""


def _pillar_branch_rows(physics_tensor: Dict[str, Any]) -> List[tuple[str, str]]:
    four = physics_tensor.get("four_pillars") if isinstance(physics_tensor.get("four_pillars"), dict) else {}
    rows: List[tuple[str, str]] = []
    for scope in ("year", "month", "day", "hour"):
        branch = _branch_from_ganzhi(four.get(scope, ""))
        if branch:
            rows.append((scope, branch))
    for scope, key in (("luck", "luck_pillar"), ("flow", "flow_pillar")):
        branch = _branch_from_ganzhi(physics_tensor.get(key, ""))
        if branch:
            rows.append((scope, branch))
    return rows


def _day_stem(physics_tensor: Dict[str, Any]) -> str:
    four = physics_tensor.get("four_pillars") if isinstance(physics_tensor.get("four_pillars"), dict) else {}
    return _stem_from_ganzhi(four.get("day", ""))


def _day_branch(physics_tensor: Dict[str, Any]) -> str:
    four = physics_tensor.get("four_pillars") if isinstance(physics_tensor.get("four_pillars"), dict) else {}
    return _branch_from_ganzhi(four.get("day", ""))


def _year_branch(physics_tensor: Dict[str, Any]) -> str:
    four = physics_tensor.get("four_pillars") if isinstance(physics_tensor.get("four_pillars"), dict) else {}
    return _branch_from_ganzhi(four.get("year", ""))


def _group_rules_for_branch(branch: str) -> Dict[str, str]:
    for group, rules in GROUP_SHENSHA_BRANCHES.items():
        if branch in group:
            return dict(rules)
    return {}


def _append_branch_hit(
    rows: List[dict],
    *,
    name: str,
    gate: str,
    branch: str,
    scopes: List[str],
    daymaster: str,
    priority: float,
    match_ratio: float,
) -> None:
    if not branch or not scopes:
        return
    origin_type = detect_relation_origin_type(scopes)
    target_god = _branch_dominant_ten_god(branch, daymaster) if daymaster else ""
    rows.append(
        {
            "plugin": "shensha",
            "fact": f"神煞命中：{name} 落在 {branch}（{','.join(scopes)}），提示{SHENSHA_HINTS.get(name, '传统象意线索')}。",
            "label": f"{name}只作象意观察，不单独定吉凶。",
            "priority": priority,
            "meta": {
                "gate": gate,
                "shensha_name": name,
                "branch": branch,
                "hit_scopes": scopes,
                "target_god": target_god,
                "observe_only": True,
                "claim_type": "classical_aura",
                "entity_scope": "shensha",
                "origin_type": origin_type,
                "origin_multiplier": round(relation_origin_multiplier(origin_type), 3),
                "match_ratio": match_ratio,
            },
        }
    )


def _collect_branch_rows(physics_tensor: Dict[str, Any], cfg: Dict[str, Any]) -> List[dict]:
    daymaster = _day_stem(physics_tensor)
    if not daymaster:
        return []
    branch_rows = _pillar_branch_rows(physics_tensor)
    if not branch_rows:
        return []
    branch_to_scopes: Dict[str, List[str]] = {}
    for scope, branch in branch_rows:
        branch_to_scopes.setdefault(branch, []).append(scope)
    priority = float(cfg.get("BRANCH_SHENSHA_PRIORITY", DECLARED_PARAMS["BRANCH_SHENSHA_PRIORITY"]))
    match_ratio = float(cfg.get("BRANCH_SHENSHA_MATCH_RATIO", DECLARED_PARAMS["BRANCH_SHENSHA_MATCH_RATIO"]))
    max_rows = int(cfg.get("BRANCH_SHENSHA_MAX_ROWS", DECLARED_PARAMS["BRANCH_SHENSHA_MAX_ROWS"]))
    rows: List[dict] = []

    for branch in TIAN_YI_BRANCHES.get(daymaster, ()):
        _append_branch_hit(
            rows,
            name="天乙贵人",
            gate="SHENSHA_TIAN_YI_BRANCH",
            branch=branch,
            scopes=branch_to_scopes.get(branch, []),
            daymaster=daymaster,
            priority=priority + 0.03,
            match_ratio=match_ratio + 0.04,
        )
    for name, mapping, gate, delta in (
        ("文昌", WEN_CHANG_BRANCH, "SHENSHA_WENCHANG", 0.02),
        ("禄神", LU_BRANCH, "SHENSHA_LU", 0.025),
        ("羊刃", YANG_REN_BRANCH, "SHENSHA_YANG_REN_BRANCH", 0.015),
    ):
        branch = mapping.get(daymaster, "")
        _append_branch_hit(
            rows,
            name=name,
            gate=gate,
            branch=branch,
            scopes=branch_to_scopes.get(branch, []),
            daymaster=daymaster,
            priority=priority + delta,
            match_ratio=match_ratio + delta,
        )

    group_source = _day_branch(physics_tensor) or _year_branch(physics_tensor)
    for name, branch in _group_rules_for_branch(group_source).items():
        _append_branch_hit(
            rows,
            name=name,
            gate=f"SHENSHA_{name}",
            branch=branch,
            scopes=branch_to_scopes.get(branch, []),
            daymaster=daymaster,
            priority=priority,
            match_ratio=match_ratio,
        )
    return rows[:max(0, max_rows)]


def _collect_rows(deity_scores: Dict[str, float], cfg: Dict[str, Any] = {}) -> List[dict]:
    tian_yi_t = float(cfg.get("TIAN_YI_THRESHOLD", DECLARED_PARAMS["TIAN_YI_THRESHOLD"]))
    yang_ren_t = float(cfg.get("YANG_REN_THRESHOLD", DECLARED_PARAMS["YANG_REN_THRESHOLD"]))
    res_buff = float(cfg.get("RESISTANCE_BUFF", DECLARED_PARAMS["RESISTANCE_BUFF"]))
    tens_mul = float(cfg.get("TENSION_MULTIPLIER", DECLARED_PARAMS["TENSION_MULTIPLIER"]))
    prio = float(cfg.get("PRIORITY_BASE", DECLARED_PARAMS["PRIORITY_BASE"]))

    has_tian_yi = deity_scores.get("正印", 0) > tian_yi_t
    has_yang_ren = deity_scores.get("劫财", 0) > yang_ren_t
    
    rows = []
    if has_tian_yi:
        rows.append({
            "plugin": "shensha",
            "fact": f"天乙贵人显化：所在柱抗性 (Resistance) 额外提升 {int(res_buff*100)}%。",
            "label": "护持/守御为主",
            "priority": prio + 0.01,
            "meta": {"resistance_buff": res_buff, "gate": "TIAN_YI_BUFF"}
        })
    if has_yang_ren:
        rows.append({
            "plugin": "shensha",
            "fact": f"羊刃显化：所在场压张力系数 x {tens_mul}。",
            "label": "校准节奏，防范剧烈冲突",
            "priority": prio,
            "meta": {"tension_multiplier": tens_mul, "gate": "YANG_REN_STRESS"}
        })
    return rows


def _shensha_origin_meta(physics_tensor: Dict[str, Any]) -> Dict[str, Any]:
    meta = physics_tensor.get("meta") if isinstance(physics_tensor.get("meta"), dict) else {}
    iv2 = meta.get("interaction_v2") if isinstance(meta.get("interaction_v2"), dict) else {}
    origins: List[str] = []
    origins.extend(collect_origin_types_from_rows(iv2.get("liu_chong") or [], member_key="pair"))
    origins.extend(collect_origin_types_from_rows(iv2.get("liu_hai") or [], member_key="pair"))
    origins.extend(collect_origin_types_from_rows(iv2.get("liu_po") or [], member_key="pair"))
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
class ShenshaPlugin(V17PluginSpec):
    plugin_id: str = "shensha"
    causal_tier: int = 3
    registry_priority: float = 0.52

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        from v17_rebirth.backend.logic.configs.manager import get_plugin_config
        cfg = get_plugin_config(self.plugin_id)
        scores = deity_scores_from_tensor(physics_tensor)
        origin_meta = _shensha_origin_meta(physics_tensor)
        rows = _collect_rows(scores, cfg)
        rows.extend(_collect_branch_rows(physics_tensor, cfg))
        for row in rows:
            if not isinstance(row.get("meta"), dict):
                row["meta"] = {}
            if row["meta"].get("gate") == "TIAN_YI_BUFF":
                row["meta"].update(_projection_meta(physics_tensor, "正印"))
            elif row["meta"].get("gate") == "YANG_REN_STRESS":
                row["meta"].update(_projection_meta(physics_tensor, "劫财"))
            elif str(row["meta"].get("target_god") or "").strip():
                row["meta"].update(_projection_meta(physics_tensor, str(row["meta"].get("target_god") or "")))
            row_origin = str(row["meta"].get("origin_type") or origin_meta["origin_type"])
            row_origin_multiplier = relation_origin_multiplier(row_origin)
            row["meta"]["origin_type"] = row_origin
            row["meta"]["origin_multiplier"] = round(float(row_origin_multiplier), 3)
            base_match = float(row["meta"].get("match_ratio", 0.72) or 0.72)
            row["meta"]["match_ratio"] = round(min(0.86, base_match * max(0.9, float(row_origin_multiplier))), 3)
        return rows_dict_to_v17_facts(rows, causal_tier=self.causal_tier, default_plugin_id=self.plugin_id)


PLUGIN = ShenshaPlugin()
