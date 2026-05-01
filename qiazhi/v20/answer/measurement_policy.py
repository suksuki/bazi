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
