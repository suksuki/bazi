from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from v20.answer.measurement_policy import domain_label, feature_domains_for_applied_domain


CORE_BAZI_DOMAINS = (
    "strength",
    "ten_god",
    "useful_god",
    "element",
    "branch",
    "wealth",
    "pattern",
    "time",
)

APPLIED_BAZI_DOMAINS = ("career", "relationship", "health")

ALLOWED_BAZI_DOMAINS = (*CORE_BAZI_DOMAINS, *APPLIED_BAZI_DOMAINS)

ALLOWED_QUESTION_KEYS_BY_DOMAIN = {
    "strength": ("q_strength_assessment",),
    "ten_god": ("q_ten_god_focus", "q_ten_god_metadata", "q_hidden_stem_role"),
    "useful_god": ("q_useful_god_candidates", "q_useful_god_evidence_gaps"),
    "element": ("q_element_balance", "q_element_support_pressure"),
    "branch": ("q_branch_relation_detail", "q_time_vs_natal_relation", "q_structure_overview"),
    "wealth": ("q_income_stability", "q_income_factors"),
    "pattern": ("q_pattern_structure",),
    "time": ("q_time_layer_context", "q_time_relation_triggers"),
    "career": ("q_career_structure",),
    "relationship": ("q_relationship_structure",),
    "health": ("q_health_balance_boundary",),
}

DOMAIN_ANCHORS = {
    "strength": ("日主", "强弱", "承载", "扶抑"),
    "ten_god": ("十神", "明透", "藏干", "来源层"),
    "useful_god": ("用神", "候选", "证据门槛", "扶助", "泄秀", "约束"),
    "element": ("五行", "木", "火", "土", "金", "水", "平衡"),
    "branch": ("地支", "冲", "合", "刑", "害", "破", "三合", "三会"),
    "wealth": ("财星", "财", "收入", "明透", "藏干"),
    "pattern": ("格局", "规则路径", "审查", "裁决"),
    "time": ("大运", "流年", "时间层", "原局", "触发"),
    "career": ("事业", "十神", "格局", "日主", "地支", "命理结构"),
    "relationship": ("关系", "十神", "地支", "互动", "命理结构"),
    "health": ("健康", "五行", "平衡", "日主", "边界", "命理结构"),
}

OFF_TOPIC_TERMS = (
    "彩票",
    "号码",
    "稳赚",
    "包赚",
    "包过",
    "股票代码",
    "诊断疾病",
    "治疗方案",
    "必定结婚",
    "必定离婚",
    "必然发财",
    "一定发财",
)


@dataclass(frozen=True)
class BaziDomainAlignment:
    ok: bool
    status: str
    domain: str
    domain_class: str
    score: float
    focus: str
    matched_anchors: tuple[str, ...]
    failures: tuple[str, ...]
    guardrails: tuple[str, ...] = (
        "BAZI_MEASUREMENT_CORE_REQUIRED",
        "APPLIED_DOMAINS_REQUIRE_CORE_FEATURE_ANCHORS",
        "NO_OFF_TOPIC_OR_VERDICT_STYLE_ROUTING",
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def bazi_alignment_manifest() -> dict[str, object]:
    return {
        "version": "v20.bazi_domain_alignment_manifest.v1",
        "core_domains": CORE_BAZI_DOMAINS,
        "applied_domains": APPLIED_BAZI_DOMAINS,
        "allowed_domains": ALLOWED_BAZI_DOMAINS,
        "allowed_question_keys_by_domain": ALLOWED_QUESTION_KEYS_BY_DOMAIN,
        "runtime_mutation": False,
        "guardrails": [
            "RULES_PORTRAITS_AND_QUESTIONS_MUST_STAY_ON_BAZI_MEASUREMENT",
            "APPLIED_DOMAINS_ARE_PROJECTIONS_OVER_CORE_FEATURES",
            "STRANGE_OR_OFF_TOPIC_PROMPTS_ARE_BLOCKED_BEFORE_RANKING",
        ],
    }


def is_allowed_bazi_domain(domain: str) -> bool:
    return str(domain) in ALLOWED_BAZI_DOMAINS


def align_question_candidate(
    *,
    question_key: str,
    domain: str,
    title: str,
    source_feature_ids: tuple[str, ...],
    boundary: str = "",
) -> BaziDomainAlignment:
    failures: list[str] = []
    normalized = str(domain)
    if normalized not in ALLOWED_BAZI_DOMAINS:
        failures.append(f"domain_not_bazi_measurement:{normalized}")
    allowed_keys = ALLOWED_QUESTION_KEYS_BY_DOMAIN.get(normalized, ())
    if question_key not in allowed_keys:
        failures.append(f"question_key_not_allowed_for_domain:{question_key}:{normalized}")
    if not source_feature_ids:
        failures.append(f"question_without_feature_support:{question_key}")
    if _has_off_topic_text(title, boundary):
        failures.append(f"question_off_topic_text:{question_key}")
    if normalized in APPLIED_BAZI_DOMAINS and not _has_core_feature_anchor(normalized, source_feature_ids):
        failures.append(f"applied_question_without_core_feature_anchor:{question_key}:{normalized}")
    anchors = _matched_anchors(normalized, title, boundary, source_feature_ids)
    if not anchors:
        failures.append(f"missing_bazi_anchor:{question_key}:{normalized}")
    return _alignment(
        domain=normalized,
        failures=tuple(failures),
        matched_anchors=anchors,
        focus=_focus_for_domain(normalized),
    )


def align_rule_candidate(
    *,
    domain: str,
    emits_feature_hooks: tuple[str, ...],
    supports_question_hooks: tuple[str, ...],
    title: str = "",
    summary: str = "",
    boundary: str = "",
) -> BaziDomainAlignment:
    failures: list[str] = []
    normalized = str(domain)
    if normalized not in ALLOWED_BAZI_DOMAINS:
        failures.append(f"domain_not_bazi_measurement:{normalized}")
    if not emits_feature_hooks:
        failures.append(f"rule_without_feature_hooks:{normalized}")
    if not supports_question_hooks:
        failures.append(f"rule_without_question_hooks:{normalized}")
    allowed_questions = set(ALLOWED_QUESTION_KEYS_BY_DOMAIN.get(normalized, ()))
    for hook in supports_question_hooks:
        if hook not in allowed_questions:
            failures.append(f"rule_question_hook_not_allowed:{hook}:{normalized}")
    if normalized in APPLIED_BAZI_DOMAINS and not _hooks_have_core_anchor(normalized, emits_feature_hooks):
        failures.append(f"applied_rule_without_core_feature_anchor:{normalized}")
    if _has_off_topic_text(title, summary, boundary):
        failures.append(f"rule_off_topic_text:{normalized}")
    anchors = _matched_anchors(normalized, title, summary, boundary, emits_feature_hooks)
    if not anchors:
        failures.append(f"missing_bazi_anchor:{normalized}")
    return _alignment(
        domain=normalized,
        failures=tuple(failures),
        matched_anchors=anchors,
        focus=_focus_for_domain(normalized),
    )


def align_portrait_axis(
    *,
    domain: str,
    feature_ids: tuple[str, ...],
    label: str = "",
    calibration_prompt: str = "",
) -> BaziDomainAlignment:
    failures: list[str] = []
    normalized = str(domain)
    if normalized not in ALLOWED_BAZI_DOMAINS:
        failures.append(f"domain_not_bazi_measurement:{normalized}")
    if not feature_ids:
        failures.append(f"portrait_axis_without_features:{normalized}")
    if normalized in APPLIED_BAZI_DOMAINS and not _has_core_feature_anchor(normalized, feature_ids):
        failures.append(f"applied_portrait_without_core_feature_anchor:{normalized}")
    if _has_off_topic_text(label, calibration_prompt):
        failures.append(f"portrait_off_topic_text:{normalized}")
    anchors = _matched_anchors(normalized, label, calibration_prompt, feature_ids)
    if not anchors:
        failures.append(f"missing_bazi_anchor:{normalized}")
    return _alignment(
        domain=normalized,
        failures=tuple(failures),
        matched_anchors=anchors,
        focus=_focus_for_domain(normalized),
    )


def _alignment(
    *,
    domain: str,
    failures: tuple[str, ...],
    matched_anchors: tuple[str, ...],
    focus: str,
) -> BaziDomainAlignment:
    domain_class = "core_bazi_domain" if domain in CORE_BAZI_DOMAINS else "applied_projection_domain"
    score = 0.0 if failures else (0.93 if domain in CORE_BAZI_DOMAINS else 0.82)
    status = "bazi_core_aligned" if domain in CORE_BAZI_DOMAINS else "bazi_projection_aligned"
    if failures:
        status = "blocked_off_core"
    return BaziDomainAlignment(
        ok=not failures,
        status=status,
        domain=domain,
        domain_class=domain_class,
        score=score,
        focus=focus,
        matched_anchors=matched_anchors,
        failures=failures,
    )


def _focus_for_domain(domain: str) -> str:
    if domain in APPLIED_BAZI_DOMAINS:
        sources = "、".join(domain_label(item) for item in feature_domains_for_applied_domain(domain))
        return f"{domain_label(domain)}必须作为命理应用投影，回到{sources}等已编译特征。"
    return f"{domain_label(domain)}必须围绕八字结构、证据来源和测算边界展开。"


def _matched_anchors(domain: str, *values: object) -> tuple[str, ...]:
    haystack = " ".join(_stringify(value) for value in values)
    anchors = []
    for anchor in DOMAIN_ANCHORS.get(domain, ()):
        if anchor and anchor in haystack:
            anchors.append(anchor)
    for feature_prefix, anchor in (
        ("feature.strength", "日主"),
        ("feature.ten_god", "十神"),
        ("feature.useful_god", "用神"),
        ("feature.element", "五行"),
        ("feature.branch", "地支"),
        ("feature.wealth", "财星"),
        ("feature.pattern", "格局"),
        ("feature.time", "时间层"),
    ):
        if feature_prefix in haystack:
            anchors.append(anchor)
    return tuple(dict.fromkeys(anchors))


def _has_core_feature_anchor(domain: str, feature_ids: tuple[str, ...]) -> bool:
    source_domains = feature_domains_for_applied_domain(domain)
    return any(
        feature_id.startswith(f"feature.{source_domain}")
        for source_domain in source_domains
        for feature_id in feature_ids
    )


def _hooks_have_core_anchor(domain: str, feature_hooks: tuple[str, ...]) -> bool:
    source_domains = feature_domains_for_applied_domain(domain)
    return any(
        hook.startswith(f"feature.{source_domain}")
        for source_domain in source_domains
        for hook in feature_hooks
    )


def _has_off_topic_text(*values: object) -> bool:
    text = _stringify(values)
    return any(term in text for term in OFF_TOPIC_TERMS)


def _stringify(value: object) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return " ".join(f"{_stringify(key)} {_stringify(row)}" for key, row in value.items())
    if isinstance(value, (list, tuple, set)):
        return " ".join(_stringify(row) for row in value)
    return str(value or "")
