from __future__ import annotations

import hashlib
from typing import Any, Dict, List, Mapping, Sequence

from v17_rebirth.backend.logic.L0_physics_fields.ten_gods_engine import (
    BRANCH_ELEMENT,
    BRANCH_HIDDEN,
    STEM_ELEMENT,
    STEM_YIN,
    _collect_root_strengths,
    _collect_visible_stems,
    _parse_gz,
    ten_god_from_stems,
)


BAZI_IMAGE_CONTRACT = "v17.symbolic.bazi_image.v1"

FINAL_BAZI_IMAGE_KEYS: List[str] = [
    "contract",
    "is_l0_symbolic_layer",
    "chart_fingerprint",
    "day_master_stem",
    "stems",
    "branches",
    "palaces",
    "symbolic_facts",
    "prompt_digest",
    "evidence",
    "knowledge_base",
    "guardrails",
]

PILLAR_LABELS: Dict[str, str] = {
    "year": "年柱",
    "month": "月柱",
    "day": "日柱",
    "hour": "时柱",
    "luck": "大运",
    "flow": "流年",
}

PALACE_CONTEXT: Dict[str, Dict[str, str]] = {
    "year": {
        "life_domain": "family_origin",
        "label": "外部背景",
        "image_summary": "家族、早年环境、外部资源与社会入口。",
    },
    "month": {
        "life_domain": "career_environment",
        "label": "事业环境",
        "image_summary": "工作环境、平台规则、主气场与现实承载。",
    },
    "day": {
        "life_domain": "spouse_self",
        "label": "自身与亲密关系",
        "image_summary": "日主自身、亲密关系和贴身生活场景。",
    },
    "hour": {
        "life_domain": "later_output",
        "label": "后续输出",
        "image_summary": "子女、作品、长期输出、晚景与未来延展。",
    },
}

STEM_IMAGE_RULES: Dict[str, Dict[str, Any]] = {
    "甲": {
        "image_tags": ["大树", "梁柱", "长期生长", "组织骨架"],
        "domain_projection": {
            "wealth": ["长期项目", "组织资源", "成长型业务"],
            "career": ["框架建设", "管理骨干", "长期责任"],
            "relationship": ["稳定支撑", "边界较直"],
            "personality": ["向上", "直接", "有主干"],
            "risk": ["周期长", "转身慢", "过直"],
        },
    },
    "乙": {
        "image_tags": ["花草", "藤蔓", "柔性连接", "审美细节"],
        "domain_projection": {
            "wealth": ["细分服务", "审美产品", "关系复购"],
            "career": ["协调", "设计", "内容服务"],
            "relationship": ["柔和连接", "需要环境滋养"],
            "personality": ["细腻", "适应", "有韧性"],
            "risk": ["依附性", "边界弱", "易受环境影响"],
        },
    },
    "丙": {
        "image_tags": ["太阳", "曝光", "公开", "热度"],
        "domain_projection": {
            "wealth": ["品牌", "流量", "传播", "公开市场"],
            "career": ["表达", "影响力", "舞台"],
            "relationship": ["热情外放", "需要被看见"],
            "personality": ["开朗", "直接", "有感染力"],
            "risk": ["过热", "消耗快", "声量大于沉淀"],
        },
    },
    "丁": {
        "image_tags": ["灯火", "技术", "洞察", "精细判断"],
        "domain_projection": {
            "wealth": ["咨询", "技术", "手艺", "精密服务"],
            "career": ["策略", "研究", "专业判断"],
            "relationship": ["敏感", "照明", "细节关照"],
            "personality": ["洞察", "专注", "感受细"],
            "risk": ["能量不稳", "过度敏感", "需要载体"],
        },
    },
    "戊": {
        "image_tags": ["高山", "平台", "承载", "边界"],
        "domain_projection": {
            "wealth": ["平台", "地产", "重资产", "稳定承载"],
            "career": ["组织平台", "基础设施", "资源承接"],
            "relationship": ["稳定", "厚重", "边界清楚"],
            "personality": ["稳重", "能扛事", "讲秩序"],
            "risk": ["固化", "迟钝", "压住流通"],
        },
    },
    "己": {
        "image_tags": ["田园", "培育", "运营", "系统维护"],
        "domain_projection": {
            "wealth": ["运营", "库存", "供应链", "服务系统"],
            "career": ["流程", "管理细节", "持续经营"],
            "relationship": ["照料", "磨合", "日常维护"],
            "personality": ["细致", "务实", "能经营"],
            "risk": ["琐碎", "内耗", "泥沙混杂"],
        },
    },
    "庚": {
        "image_tags": ["矿石", "机器", "工具", "规则", "执行"],
        "domain_projection": {
            "wealth": ["硬资产", "工具化产品", "制造", "执行收益"],
            "career": ["工程", "制度", "攻坚", "执行"],
            "relationship": ["直接", "重规则", "有锋芒"],
            "personality": ["果断", "硬朗", "重效率"],
            "risk": ["刚硬", "冲突", "成本高"],
        },
    },
    "辛": {
        "image_tags": ["珠玉", "精密", "审美溢价", "凭证"],
        "domain_projection": {
            "wealth": ["金融凭证", "品牌质感", "精密产品"],
            "career": ["品控", "审美", "法务", "金融"],
            "relationship": ["讲品质", "重细节", "边界精确"],
            "personality": ["精致", "敏锐", "标准高"],
            "risk": ["挑剔", "脆弱", "过度包装"],
        },
    },
    "壬": {
        "image_tags": ["江河", "流通", "远方", "信息流"],
        "domain_projection": {
            "wealth": ["贸易", "流通", "跨区域资源", "信息差"],
            "career": ["资源调度", "市场", "迁移", "传播网络"],
            "relationship": ["流动", "包容", "边界易变"],
            "personality": ["开阔", "聪明", "流动性强"],
            "risk": ["漂移", "失控", "现金流波动"],
        },
    },
    "癸": {
        "image_tags": ["雨露", "数据", "隐性需求", "微循环"],
        "domain_projection": {
            "wealth": ["数据", "研究", "小额持续现金流", "隐性服务"],
            "career": ["研究", "分析", "隐性服务"],
            "relationship": ["细水长流", "敏感", "润物无声"],
            "personality": ["细腻", "观察力", "潜在适应"],
            "risk": ["隐蔽", "迟缓", "方向感弱"],
        },
    },
}

BRANCH_IMAGE_RULES: Dict[str, Dict[str, Any]] = {
    "子": {"image_tags": ["寒水", "流动", "夜间", "隐性需求"], "season_context": "冬水，主流动、信息和隐性需求。"},
    "丑": {"image_tags": ["湿土", "金库", "寒湿", "沉淀"], "season_context": "冬末湿土，主沉淀、库存和慢变量。"},
    "寅": {"image_tags": ["初春木", "启动", "生发", "远行"], "season_context": "初春木气，主启动、生长和外展。"},
    "卯": {"image_tags": ["仲春木", "审美", "关系", "细分"], "season_context": "仲春木气，主审美、关系与生长。"},
    "辰": {"image_tags": ["湿土", "水库", "混合资源", "蓄藏"], "season_context": "春末湿土，主混合资源、蓄藏和转化。"},
    "巳": {"image_tags": ["初夏火", "技术", "传播", "暗藏金土"], "season_context": "初夏火气，主技术、热度和显化。"},
    "午": {"image_tags": ["盛夏火", "曝光", "平台", "热度"], "season_context": "盛夏火气，主曝光、公开与高能量。"},
    "未": {"image_tags": ["燥土", "木库", "服务系统", "培育"], "season_context": "夏末燥土，主培育、经营和资源收束。"},
    "申": {"image_tags": ["初秋金", "工具", "规则", "流通入口"], "season_context": "初秋金气，主工具、制度与执行。"},
    "酉": {"image_tags": ["仲秋金", "精密", "审美", "凭证"], "season_context": "仲秋金气，主精密、品质和凭证。"},
    "戌": {"image_tags": ["燥土", "火库", "边界", "资产结构"], "season_context": "秋末燥土，主边界、资产结构和收束。"},
    "亥": {"image_tags": ["初冬水", "远方", "流通", "根源"], "season_context": "初冬水气，主远方、流通和潜在资源。"},
}

VAULT_RULES: Dict[str, Dict[str, str]] = {
    "辰": {"vault_element": "水", "plain_material": "资金流、信息流或隐性资源的蓄藏"},
    "戌": {"vault_element": "火", "plain_material": "品牌、曝光、项目热度或资产结构的蓄藏"},
    "丑": {"vault_element": "金", "plain_material": "凭证、硬资产、金融或精密资源的蓄藏"},
    "未": {"vault_element": "木", "plain_material": "项目、客户、成长资源或服务系统的蓄藏"},
}

TEN_GOD_FAMILY: Dict[str, Dict[str, str]] = {
    "正财": {"fact_type": "wealth_material", "topic_hint": "wealth", "role": "稳定收入"},
    "偏财": {"fact_type": "wealth_material", "topic_hint": "wealth", "role": "项目机会"},
    "食神": {"fact_type": "output_material", "topic_hint": "wealth", "role": "稳定输出"},
    "伤官": {"fact_type": "output_material", "topic_hint": "wealth", "role": "表达与销售转化"},
    "正官": {"fact_type": "authority_material", "topic_hint": "career", "role": "平台规则"},
    "七杀": {"fact_type": "authority_material", "topic_hint": "career", "role": "高压任务"},
    "正印": {"fact_type": "seal_material", "topic_hint": "career", "role": "资质信用"},
    "偏印": {"fact_type": "seal_material", "topic_hint": "career", "role": "专业方法"},
    "比肩": {"fact_type": "peer_material", "topic_hint": "relationship", "role": "同辈合作"},
    "劫财": {"fact_type": "peer_material", "topic_hint": "wealth", "role": "竞争分利"},
}

RELATION_TAGS: Dict[str, str] = {
    "liu_chong": "冲动",
    "liu_hai": "隐性牵制",
    "liu_po": "破损",
    "liuhe": "六合绑定",
    "san_he": "三合聚势",
    "ban_he": "半合聚势",
    "san_hui": "三会成势",
    "sanxing": "刑压",
    "anhe": "暗合牵引",
}


def _clean_label(value: Any, *, limit: int = 180) -> str:
    text = str(value or "").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def _clean_str_list(values: Sequence[Any] | None, *, limit: int = 8) -> List[str]:
    if not isinstance(values, Sequence) or isinstance(values, (str, bytes)):
        return []
    rows: List[str] = []
    seen: set[str] = set()
    for value in values:
        label = _clean_label(value)
        if not label or label in seen:
            continue
        seen.add(label)
        rows.append(label)
        if len(rows) >= limit:
            break
    return rows


def _safe_float(value: Any, fallback: float = 0.0) -> float:
    try:
        next_value = float(value)
    except (TypeError, ValueError):
        return fallback
    if next_value != next_value:
        return fallback
    return next_value


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, float(value)))


def _four_pillars(physics_tensor: Mapping[str, Any]) -> Dict[str, str]:
    raw = physics_tensor.get("four_pillars")
    return {str(k): str(v) for k, v in raw.items()} if isinstance(raw, Mapping) else {}


def _day_master(physics_tensor: Mapping[str, Any], four: Mapping[str, str]) -> str:
    explicit = _clean_label(physics_tensor.get("day_master_stem"))
    if explicit in STEM_ELEMENT:
        return explicit
    stem, _branch = _parse_gz(str(four.get("day") or ""))
    return stem if stem in STEM_ELEMENT else ""


def _pillar_items(physics_tensor: Mapping[str, Any], four: Mapping[str, str]) -> List[tuple[str, str, str]]:
    rows: List[tuple[str, str, str]] = []
    for scope in ("year", "month", "day", "hour"):
        stem, branch = _parse_gz(str(four.get(scope) or ""))
        if stem or branch:
            rows.append((scope, stem, branch))
    for scope, field_name in (("luck", "luck_pillar"), ("flow", "flow_pillar")):
        stem, branch = _parse_gz(str(physics_tensor.get(field_name) or ""))
        if stem or branch:
            rows.append((scope, stem, branch))
    return rows


def _chart_fingerprint(rows: Sequence[tuple[str, str, str]]) -> str:
    material = "|".join(f"{scope}:{stem}{branch}" for scope, stem, branch in rows)
    if not material:
        return ""
    return hashlib.sha1(material.encode("utf-8")).hexdigest()[:16]


def _yin_yang(stem: str) -> str:
    return "yin" if STEM_YIN.get(stem, False) else "yang"


def _branch_relation_index(physics_tensor: Mapping[str, Any]) -> Dict[str, List[str]]:
    meta = physics_tensor.get("meta") if isinstance(physics_tensor.get("meta"), Mapping) else {}
    interaction = meta.get("interaction_v2") if isinstance(meta.get("interaction_v2"), Mapping) else {}
    out: Dict[str, List[str]] = {}
    for key, label in RELATION_TAGS.items():
        rows = interaction.get(key)
        if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)):
            continue
        for hit in rows:
            if not isinstance(hit, Mapping):
                continue
            branches: List[str] = []
            for field in ("pair", "group", "matched_branches", "branches"):
                raw = hit.get(field)
                if isinstance(raw, Sequence) and not isinstance(raw, (str, bytes)):
                    branches.extend(str(item).strip() for item in raw if str(item).strip())
            for branch in branches:
                out.setdefault(branch, [])
                if label not in out[branch]:
                    out[branch].append(label)
    return out


def _stem_visibility(scope: str, stem: str, day_master: str, root_strengths: Mapping[str, Any]) -> str:
    if scope == "day" and stem == day_master:
        return "day_master"
    if _safe_float(root_strengths.get(stem), 0.0) >= 0.18:
        return "rooted"
    return "floating"


def _projection_for(stem: str) -> Dict[str, List[str]]:
    rule = STEM_IMAGE_RULES.get(stem, {})
    raw = rule.get("domain_projection") if isinstance(rule.get("domain_projection"), Mapping) else {}
    return {
        str(key): _clean_str_list(value, limit=6)
        for key, value in raw.items()
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes))
    }


def _stem_row(
    *,
    scope: str,
    stem: str,
    day_master: str,
    root_strengths: Mapping[str, Any],
) -> Dict[str, Any]:
    god = "日主" if scope == "day" and stem == day_master else ten_god_from_stems(day_master, stem)
    projection = _projection_for(stem)
    return {
        "pillar": scope,
        "pillar_label": PILLAR_LABELS.get(scope, scope),
        "stem": stem,
        "yin_yang": _yin_yang(stem),
        "element": STEM_ELEMENT.get(stem, ""),
        "ten_god": god,
        "image_tags": _clean_str_list(STEM_IMAGE_RULES.get(stem, {}).get("image_tags"), limit=8),
        "domain_projection": projection,
        "visibility": _stem_visibility(scope, stem, day_master, root_strengths),
        "root_strength": round(_clamp(_safe_float(root_strengths.get(stem), 0.0)), 4),
        "evidence": [
            f"{PILLAR_LABELS.get(scope, scope)}天干{stem}"
            + (f"对应{god}" if god != "日主" else "为日主")
        ],
    }


def _storage_context(branch: str) -> Dict[str, Any]:
    rule = VAULT_RULES.get(branch)
    if not rule:
        return {
            "has_vault_signal": False,
            "vault_element": "",
            "plain_material": "",
            "default_state": "not_vault",
            "school_note": "",
        }
    return {
        "has_vault_signal": True,
        "vault_element": rule["vault_element"],
        "plain_material": rule["plain_material"],
        "default_state": "stored_not_released",
        "school_note": "财库开合存在派别差异，第一版只标记象义事实，不直接断进财。",
    }


def _hidden_stem_rows(branch: str, day_master: str, visible_stems: Sequence[str]) -> List[Dict[str, Any]]:
    visible = set(visible_stems)
    rows: List[Dict[str, Any]] = []
    for hidden_stem, weight in BRANCH_HIDDEN.get(branch, []):
        rows.append(
            {
                "stem": hidden_stem,
                "weight": round(_safe_float(weight), 4),
                "element": STEM_ELEMENT.get(hidden_stem, ""),
                "ten_god": ten_god_from_stems(day_master, hidden_stem),
                "image_tags": _clean_str_list(STEM_IMAGE_RULES.get(hidden_stem, {}).get("image_tags"), limit=5),
                "visibility": "exposed_hidden" if hidden_stem in visible else "stored_hidden",
            }
        )
    return rows


def _branch_row(
    *,
    scope: str,
    branch: str,
    day_master: str,
    visible_stems: Sequence[str],
    relation_index: Mapping[str, Sequence[str]],
) -> Dict[str, Any]:
    relation_tags = _clean_str_list(relation_index.get(branch), limit=6)
    storage = _storage_context(branch)
    needs_trigger = ["岁运引动", "合冲刑害", "透藏联动"] if storage.get("has_vault_signal") else []
    movement_risk = "开库不等于进财，也可能是资金流动、投入、回款或资产转换。" if storage.get("has_vault_signal") else ""
    if relation_tags and not movement_risk:
        movement_risk = "关系触发只代表场景被引动，不直接等同吉凶。"
    return {
        "pillar": scope,
        "pillar_label": PILLAR_LABELS.get(scope, scope),
        "branch": branch,
        "element": BRANCH_ELEMENT.get(branch, ""),
        "image_tags": _clean_str_list(BRANCH_IMAGE_RULES.get(branch, {}).get("image_tags"), limit=8),
        "season_context": _clean_label(BRANCH_IMAGE_RULES.get(branch, {}).get("season_context")),
        "hidden_stems": _hidden_stem_rows(branch, day_master, visible_stems),
        "storage_context": storage,
        "movement_context": {
            "relation_tags": relation_tags,
            "needs_trigger": needs_trigger,
            "risk": movement_risk,
        },
        "evidence": [f"{PILLAR_LABELS.get(scope, scope)}地支{branch}"],
    }


def _palace_rows(rows: Sequence[tuple[str, str, str]]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for scope, stem, branch in rows:
        if scope not in PALACE_CONTEXT:
            continue
        context = PALACE_CONTEXT[scope]
        out.append(
            {
                "pillar": scope,
                "pillar_label": PILLAR_LABELS.get(scope, scope),
                "life_domain": context["life_domain"],
                "label": context["label"],
                "image_summary": context["image_summary"],
                "pillar_symbol": f"{stem}{branch}",
                "evidence": [f"{PILLAR_LABELS.get(scope, scope)}{stem}{branch}"],
            }
        )
    return out


def _wealth_projection_text(stem: str) -> str:
    wealth = _projection_for(stem).get("wealth", [])
    return "、".join(wealth[:3]) if wealth else ""


def _symbolic_facts(stems: Sequence[Mapping[str, Any]], branches: Sequence[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    facts: List[Dict[str, Any]] = []
    for row in stems:
        god = _clean_label(row.get("ten_god"))
        stem = _clean_label(row.get("stem"))
        if not stem or god == "日主":
            continue
        family = TEN_GOD_FAMILY.get(god)
        if not family:
            continue
        projection = row.get("domain_projection") if isinstance(row.get("domain_projection"), Mapping) else {}
        wealth_text = "、".join(_clean_str_list(projection.get("wealth"), limit=3))
        role = family["role"]
        plain = f"{god}见{stem}{row.get('element', '')}，{role}更像{wealth_text or '对应材质的现实资源'}"
        facts.append(
            {
                "id": f"symbolic.fact.{row.get('pillar')}.{stem}.{god}",
                "topic_hint": family["topic_hint"],
                "fact_type": family["fact_type"],
                "classic_terms": [god, f"{stem}{row.get('element', '')}"],
                "plain_meaning": plain,
                "confidence": 0.72 if row.get("visibility") == "rooted" else 0.64,
                "evidence": list(row.get("evidence") or []),
            }
        )
    for branch in branches:
        storage = branch.get("storage_context") if isinstance(branch.get("storage_context"), Mapping) else {}
        if storage.get("has_vault_signal"):
            facts.append(
                {
                    "id": f"symbolic.fact.{branch.get('pillar')}.{branch.get('branch')}.vault",
                    "topic_hint": "wealth",
                    "fact_type": "vault_material",
                    "classic_terms": [str(branch.get("branch") or ""), f"{storage.get('vault_element', '')}库"],
                    "plain_meaning": f"{branch.get('branch')}带库象，偏向{storage.get('plain_material')}",
                    "confidence": 0.62,
                    "evidence": list(branch.get("evidence") or []),
                }
            )
        for hidden in branch.get("hidden_stems") or []:
            if not isinstance(hidden, Mapping):
                continue
            god = _clean_label(hidden.get("ten_god"))
            if god not in {"正财", "偏财"}:
                continue
            hidden_stem = _clean_label(hidden.get("stem"))
            facts.append(
                {
                    "id": f"symbolic.fact.{branch.get('pillar')}.{branch.get('branch')}.{hidden_stem}.{god}",
                    "topic_hint": "wealth",
                    "fact_type": "hidden_wealth_material",
                    "classic_terms": [god, f"{hidden_stem}{hidden.get('element', '')}", "藏干"],
                    "plain_meaning": f"{branch.get('branch')}中藏{god}{hidden_stem}，财富线索更像{_wealth_projection_text(hidden_stem) or '隐藏资源'}",
                    "confidence": 0.52 if hidden.get("visibility") == "stored_hidden" else 0.58,
                    "evidence": [f"{branch.get('pillar_label')}地支{branch.get('branch')}藏{hidden_stem}"],
                }
            )
    return facts[:18]


def _prompt_digest(symbolic_facts: Sequence[Mapping[str, Any]]) -> str:
    wealth_rows = [
        _clean_label(row.get("plain_meaning"), limit=80)
        for row in symbolic_facts
        if row.get("topic_hint") == "wealth" and _clean_label(row.get("plain_meaning"))
    ]
    if wealth_rows:
        return "；".join(wealth_rows[:3])
    rows = [
        _clean_label(row.get("plain_meaning"), limit=80)
        for row in symbolic_facts
        if _clean_label(row.get("plain_meaning"))
    ]
    return "；".join(rows[:3])


def build_bazi_image_contract() -> Dict[str, Any]:
    return {
        "contract": BAZI_IMAGE_CONTRACT,
        "is_l0_symbolic_layer": True,
        "read_only_sources": [
            "four_pillars",
            "day_master_stem",
            "luck_pillar",
            "flow_pillar",
            "ten_god_from_stems",
            "hidden_stems",
            "interaction_v2",
        ],
        "outputs": list(FINAL_BAZI_IMAGE_KEYS),
        "constraints": [
            "只输出干支、十神、宫位、藏透、库象和触发场景的象义事实。",
            "不得裁决体用，不得修改十神能量、格局候选、参数或权威裁决。",
            "不得把象义事实直接写成发财、破财、婚姻或健康结论。",
            "LLM 只能消费 bazi_image 合同，不得自由回读原始八字重新断事。",
        ],
        "guardrails": [
            "symbolic_layer_is_not_verdict",
            "do_not_equate_symbol_with_event",
            "do_not_modify_body_use_or_parameters",
        ],
    }


def normalize_bazi_image_meta(value: Any) -> Dict[str, Any]:
    if not isinstance(value, Mapping) or not value:
        return {}
    normalized = {key: value.get(key) for key in FINAL_BAZI_IMAGE_KEYS if key in value}
    normalized["contract"] = _clean_label(normalized.get("contract")) or BAZI_IMAGE_CONTRACT
    normalized["is_l0_symbolic_layer"] = bool(normalized.get("is_l0_symbolic_layer", True))
    normalized["chart_fingerprint"] = _clean_label(normalized.get("chart_fingerprint"))
    normalized["day_master_stem"] = _clean_label(normalized.get("day_master_stem"))
    for list_key in ("stems", "branches", "palaces", "symbolic_facts", "evidence", "guardrails"):
        raw = normalized.get(list_key)
        normalized[list_key] = list(raw) if isinstance(raw, list) else []
    normalized["prompt_digest"] = _clean_label(normalized.get("prompt_digest"), limit=240)
    knowledge = normalized.get("knowledge_base")
    normalized["knowledge_base"] = dict(knowledge) if isinstance(knowledge, Mapping) else {
        "id": "v17.knowledge.bazi_symbolic_primitives.v1",
        "mode": "curated_static_rules",
    }
    return normalized


def resolve_bazi_image(physics_tensor: Dict[str, Any]) -> Dict[str, Any]:
    pt = physics_tensor if isinstance(physics_tensor, dict) else {}
    four = _four_pillars(pt)
    day_master = _day_master(pt, four)
    if not day_master:
        return {"bazi_image": {}, "confidence": 0.0}
    pillar_rows = _pillar_items(pt, four)
    if not pillar_rows:
        return {"bazi_image": {}, "confidence": 0.0}
    luck = str(pt.get("luck_pillar") or "")
    flow = str(pt.get("flow_pillar") or "")
    root_strengths = _collect_root_strengths(four, luck, flow)
    visible_stems = _collect_visible_stems(four, luck, flow, parse_gz=_parse_gz)
    relation_index = _branch_relation_index(pt)

    stem_rows = [
        _stem_row(scope=scope, stem=stem, day_master=day_master, root_strengths=root_strengths)
        for scope, stem, _branch in pillar_rows
        if stem in STEM_ELEMENT
    ]
    branch_rows = [
        _branch_row(
            scope=scope,
            branch=branch,
            day_master=day_master,
            visible_stems=visible_stems,
            relation_index=relation_index,
        )
        for scope, _stem, branch in pillar_rows
        if branch in BRANCH_HIDDEN
    ]
    symbolic_facts = _symbolic_facts(stem_rows, branch_rows)
    evidence = [
        f"日主{day_master}作为十神参照轴。",
        f"已解析柱位：{'、'.join(PILLAR_LABELS.get(scope, scope) for scope, _stem, _branch in pillar_rows)}。",
    ]
    if symbolic_facts:
        evidence.extend(_clean_label(row.get("plain_meaning"), limit=120) for row in symbolic_facts[:4])
    image = {
        "contract": BAZI_IMAGE_CONTRACT,
        "is_l0_symbolic_layer": True,
        "chart_fingerprint": _chart_fingerprint(pillar_rows),
        "day_master_stem": day_master,
        "stems": stem_rows,
        "branches": branch_rows,
        "palaces": _palace_rows(pillar_rows),
        "symbolic_facts": symbolic_facts,
        "prompt_digest": _prompt_digest(symbolic_facts),
        "evidence": _clean_str_list(evidence, limit=8),
        "knowledge_base": {
            "id": "v17.knowledge.bazi_symbolic_primitives.v1",
            "mode": "curated_static_rules",
            "version": "2026-04-26",
        },
        "guardrails": build_bazi_image_contract()["guardrails"],
    }
    confidence = 0.72
    if len(stem_rows) >= 4 and len(branch_rows) >= 4:
        confidence = 0.82
    if any(scope in {"luck", "flow"} for scope, _stem, _branch in pillar_rows):
        confidence += 0.04
    return {"bazi_image": normalize_bazi_image_meta(image), "confidence": round(_clamp(confidence), 4)}
