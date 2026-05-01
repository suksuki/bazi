from __future__ import annotations

from v20.features.schema import BaziFeature

DOMAIN_LABELS = {
    "strength": "日主强弱",
    "useful_god": "用神候选",
    "ten_god": "十神结构",
    "element": "五行分布",
    "branch": "地支关系",
    "time": "时间层与流年触发",
    "wealth": "财星与收入结构",
    "career": "事业角色与工作结构",
    "relationship": "关系互动结构",
    "health": "五行平衡与健康边界",
    "pattern": "格局审查",
}

MEASUREMENT_FOCUS = {
    "strength": "判断日主承载力、扶抑压力与后续取用边界",
    "useful_god": "打开用神候选路径，等待证据门槛和规则路径裁决",
    "ten_god": "读取十神显隐、来源层级与可进入的测算主题",
    "element": "读取五行分布、偏旺偏弱与结构平衡边界",
    "branch": "识别冲合刑害等结构互动，但不直接推出吉凶",
    "time": "读取显式时间干支与原局互动，只作为有证据的触发背景",
    "wealth": "评估财星材料、显隐来源与收入结构可讨论边界",
    "pattern": "建立格局审查索引，等待规则图和证据包裁决",
}

MEASUREMENT_STAGE = {
    "strength": "foundation",
    "useful_god": "arbitration",
    "ten_god": "structure",
    "element": "foundation",
    "branch": "structure",
    "time": "time_context",
    "wealth": "domain_reading",
    "career": "domain_reading",
    "relationship": "domain_reading",
    "health": "domain_reading",
    "pattern": "arbitration",
}

APPLIED_DOMAIN_FEATURE_MAP = {
    "wealth": ("wealth", "ten_god", "strength", "branch"),
    "career": ("ten_god", "pattern", "strength", "branch"),
    "relationship": ("ten_god", "branch", "strength"),
    "health": ("element", "strength", "branch", "pattern"),
}

FEATURE_LABELS = {
    "feature.strength.supported_capacity": "日主承载力有扶助证据",
    "feature.strength.capacity_needs_support": "日主承载力需要扶助复核",
    "feature.strength.borderline_capacity": "日主承载力接近边界",
    "feature.useful_god.evidence_gate": "用神候选需要证据门槛",
    "feature.useful_god.candidate_paths": "用神候选路径已编译",
    "feature.ten_god.visible_relation": "明透十神关系可进入测算",
    "feature.ten_god.hidden_relation": "藏干十神关系可进入测算",
    "feature.element.balance_distribution": "五行分布可进入结构测算",
    "feature.branch.visible_relation": "可见地支关系需要分层判断",
    "feature.branch.relation_quiet": "地支关系相对平静",
    "feature.time.explicit_context": "显式时间层可进入触发测算",
    "feature.wealth.material_available": "财星材料在结构中可见",
    "feature.wealth.material_not_visible": "财星材料未直接显现",
    "feature.pattern.review_index": "格局审查索引已建立",
}

ELEMENT_LABELS_ZH = {
    "wood": "木",
    "fire": "火",
    "earth": "土",
    "metal": "金",
    "water": "水",
}

USEFUL_GOD_PATH_LABELS_ZH = {
    "resource_support": "印星扶助路径",
    "peer_stabilizer": "比劫稳定路径",
    "output_release": "食伤泄秀路径",
    "wealth_channel": "财星通道路径",
    "authority_constraint_review": "官杀约束复核路径",
    "support_vs_release_review": "扶助与泄秀裁决路径",
    "output_pressure_review": "食伤压力复核路径",
    "weak_element_gap_review": "弱项证据缺口复核路径",
}


def domain_label(domain: str) -> str:
    return DOMAIN_LABELS.get(domain, domain)


def measurement_focus(feature: BaziFeature) -> str:
    return MEASUREMENT_FOCUS.get(feature.domain, "解释该命理特征的结构意义和证据边界")


def measurement_stage(domain: str) -> str:
    return MEASUREMENT_STAGE.get(domain, "structure")


def feature_domains_for_applied_domain(domain: str) -> tuple[str, ...]:
    return APPLIED_DOMAIN_FEATURE_MAP.get(domain, (domain,))


def applied_domains() -> tuple[str, ...]:
    return tuple(APPLIED_DOMAIN_FEATURE_MAP)


def feature_label(feature: BaziFeature) -> str:
    return FEATURE_LABELS.get(feature.feature_id, feature.title)


def feature_public_summary(feature: BaziFeature) -> str:
    if feature.domain == "strength":
        return _strength_summary(feature)
    if feature.feature_id == "feature.useful_god.candidate_paths":
        return _useful_god_summary(feature.calibration_state)
    if feature.domain == "ten_god":
        return _ten_god_summary(feature)
    if feature.feature_id == "feature.element.balance_distribution":
        return _element_summary(feature.calibration_state)
    if feature.domain == "branch":
        return _branch_summary(feature)
    if feature.domain == "time":
        return _time_summary(feature)
    if feature.domain == "wealth":
        return _wealth_summary(feature)
    return ""


def prediction_policy() -> dict[str, object]:
    return {
        "version": "v20.prediction_policy.v1",
        "core_focus": "bazi_measurement",
        "allowed": [
            "structure_assessment",
            "feature_evidence_explanation",
            "candidate_useful_god_path",
            "domain_reading_with_boundaries",
            "timing_context_when_time_layer_exists",
        ],
        "blocked": [
            "guaranteed_event_prediction",
            "fixed_fortune_verdict",
            "unsupported_health_legal_financial_claim",
            "private_data_inference",
            "rule_mutation_by_llm_or_feedback",
        ],
        "guardrails": [
            "PREDICTION_IS_EVIDENCE_BOUNDED_MEASUREMENT",
            "NO_DETERMINISTIC_FORTUNE_VERDICT",
            "TIME_PREDICTION_REQUIRES_TIME_CONTEXT",
        ],
    }


def _useful_god_summary(calibration_state: str) -> str:
    rows = []
    for item in calibration_state.split(";"):
        parts = item.split(":")
        if len(parts) < 2:
            continue
        path_key, element = parts[0], parts[1]
        path_label = USEFUL_GOD_PATH_LABELS_ZH.get(path_key)
        element_label = ELEMENT_LABELS_ZH.get(element)
        if path_label and element_label:
            rows.append(f"{path_label}（{element_label}）")
    if not rows:
        return ""
    return "候选摘要：" + "、".join(rows[:4]) + "。"


def _strength_summary(feature: BaziFeature) -> str:
    values = {}
    for ref in feature.evidence_refs:
        key, _, value = ref.title.partition("=")
        if key and value:
            values[key] = value
    support = values.get("support")
    pressure = values.get("pressure")
    if support and pressure:
        return f"结构材料：扶助分 {support}，压力分 {pressure}，用于判断承载力边界。"
    return ""


def _ten_god_summary(feature: BaziFeature) -> str:
    labels = _unique(ref.title for ref in feature.evidence_refs if ref.title)
    if not labels:
        return ""
    prefix = "藏干十神材料" if "hidden" in feature.source_layers else "明透十神材料"
    return f"{prefix}：" + "、".join(labels[:8]) + "。"


def _branch_summary(feature: BaziFeature) -> str:
    relations = _unique(ref.title for ref in feature.evidence_refs if ref.kind == "branch_relation" and ref.title)
    if not relations:
        return ""
    return "地支结构材料：" + "、".join(relations[:6]) + "。"


def _time_summary(feature: BaziFeature) -> str:
    pillars = _unique(ref.title for ref in feature.evidence_refs if ref.kind == "time_pillar" and ref.title)
    ten_gods = _unique(ref.title for ref in feature.evidence_refs if ref.kind == "ten_god" and ref.title)
    relations = _unique(ref.title for ref in feature.evidence_refs if ref.kind == "branch_relation" and ref.title)
    rows = []
    if pillars:
        rows.append("时间干支：" + "、".join(pillars[:4]))
    if ten_gods:
        rows.append("对应十神：" + "、".join(ten_gods[:4]))
    if relations:
        rows.append("触发关系：" + "、".join(relations[:6]))
    if not rows:
        return ""
    return "结构材料：" + "；".join(rows) + "。"


def _wealth_summary(feature: BaziFeature) -> str:
    labels = [
        f"{ref.title}（{_source_layer_label(ref.source_layer)}）"
        for ref in feature.evidence_refs
        if ref.title and ref.title != "no wealth ten-god material found"
    ]
    if labels:
        return "财星材料：" + "、".join(_unique(labels)[:6]) + "。"
    if feature.feature_id == "feature.wealth.material_not_visible":
        return "财星材料：原局明透与藏干未直接形成财星入口，需从结构路径复核。"
    return ""


def _element_summary(calibration_state: str) -> str:
    parsed: dict[str, str] = {}
    for item in calibration_state.split(";"):
        key, _, value = item.partition("=")
        if key and value:
            parsed[key] = value
    strongest = _element_list(parsed.get("strongest", ""))
    weakest = _element_list(parsed.get("weakest", ""))
    if strongest and weakest:
        return f"结构摘要：相对集中在{strongest}，相对不足在{weakest}。"
    if strongest:
        return f"结构摘要：相对集中在{strongest}。"
    if weakest:
        return f"结构摘要：相对不足在{weakest}。"
    return ""


def _element_list(value: str) -> str:
    labels = [ELEMENT_LABELS_ZH.get(row, "") for row in value.split(",") if row]
    return "、".join(label for label in labels if label)


def _source_layer_label(value: str) -> str:
    return {
        "visible": "明透",
        "hidden": "藏干",
        "time": "时间层",
        "core": "核心",
    }.get(value, value)


def _unique(items) -> list[str]:
    return list(dict.fromkeys(str(item) for item in items if str(item)))
