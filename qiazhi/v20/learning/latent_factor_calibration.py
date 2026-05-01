from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


ALLOWED_USES = (
    "personal_route_rerank",
    "question_priority",
    "calibration_posterior",
    "synthetic_profile_review",
)

BLOCKED_USES = (
    "rule_truth_update",
    "deterministic_prediction",
    "user_visible_score",
    "medical_or_lifespan_inference",
)


@dataclass(frozen=True)
class LatentCalibrationFactor:
    factor_id: str
    label: str
    domain: str
    factor_kind: str
    description: str
    allowed_use: tuple[str, ...] = ALLOWED_USES
    blocked_use: tuple[str, ...] = BLOCKED_USES

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def latent_factor_catalog() -> tuple[LatentCalibrationFactor, ...]:
    return (
        _factor("baseline_amplifier", "基础兑现放大因子", "global", "change_amplifier", "同样结构下现实兑现的整体放大率。"),
        _factor("action_efficiency", "行动效率", "global", "hidden_setting", "命主把行动转化为结果的隐藏出厂设置，不等同于吉凶。"),
        _factor("resource_support", "资源支持", "global", "hidden_setting", "家庭、平台、人脉、地域资源对结构兑现的隐藏支持量。"),
        _factor("opportunity_access", "机会可达性", "global", "hidden_setting", "命主接触机会和进入平台的隐藏可达性。"),
        _factor("risk_tolerance", "风险承受", "global", "hidden_setting", "路径波动承受度，用于问题排序和解释边界。"),
        _factor("timing_sensitivity", "时间引动敏感度", "time", "change_amplifier", "大运流年触发时现实事件被放大的敏感度。"),
        _factor("wealth_amplifier", "财富兑现放大因子", "wealth", "change_amplifier", "财富相关结构在个人现实中的变化放大率。"),
        _factor("career_amplifier", "事业兑现放大因子", "career", "change_amplifier", "事业与角色变化在个人现实中的变化放大率。"),
        _factor("relationship_sensitivity", "关系事件敏感度", "relationship", "change_amplifier", "关系领域事件对结构路径的变化放大率。"),
        _factor("relocation_mobility", "迁移流动性", "relocation", "hidden_setting", "地域、迁移、工作环境变化对现实路径的隐藏影响量。"),
        _factor("stress_recovery_capacity", "压力恢复能力", "stress", "hidden_setting", "压力事件后的恢复和稳定能力。"),
        _factor("health_safety_modifier", "健康安全边界修正", "health", "safety_modifier", "只用于健康安全提醒边界，不用于疾病、寿命或诊断推断。"),
    )


def latent_factor_calibration_manifest() -> dict[str, object]:
    factors = latent_factor_catalog()
    return {
        "version": "v20.latent_factor_calibration_manifest.v1",
        "status": "ready",
        "source_lineage": "v19.p64_interactive_calibration_design",
        "definition": {
            "bazi_structure": "结构先验",
            "user_events": "观测证据",
            "personal_hidden_settings": "命主级隐藏出厂设置；同八字不同命的个体差异入口",
            "change_amplifiers": "命主对大运流年、领域变化和现实触发的放大率",
            "latent_factors": "隐藏出厂设置和放大因子的统一可学习参数集合",
            "calibration_result": "只影响问题排序、路径排序和后续询问优先级",
        },
        "hypothesis": "同样八字可以共享结构先验，但不同命主拥有不同隐藏出厂设置和变化放大率。",
        "latent_factor_count": len(factors),
        "factor_kind_counts": _factor_kind_counts(factors),
        "latent_factors": [factor.to_dict() for factor in factors],
        "event_evidence_schema": _event_evidence_schema(),
        "calibration_inquiries": _calibration_inquiry_catalog(),
        "active_models_now": (
            "rule_graph_structural_prior",
            "deterministic_factor_scoring",
            "bayesian_update_for_internal_posterior",
            "active_learning_question_selection",
        ),
        "reserved_models_later": {
            "factor_graph": "Use when event ledger has enough time-node observations.",
            "contextual_bandit": "Use only for next-question ranking.",
            "gnn": "Use only for path embedding/rerank, not core inference.",
            "rl": "Use only for dialogue strategy, not rule truth.",
        },
        "runtime_mutation": False,
        "guardrails": [
            "LATENT_FACTORS_ARE_PERSONAL_CALIBRATION_PARAMETERS",
            "HIDDEN_SETTINGS_AND_CHANGE_AMPLIFIERS_EXPLAIN_PERSON_LEVEL_VARIATION",
            "AMPLIFIERS_RERANK_ROUTES_NOT_RULE_TRUTH",
            "USER_EVENTS_ARE_OBSERVATION_EVIDENCE_ONLY",
            "NO_USER_VISIBLE_LUCK_OR_PROBABILITY_SCORE",
        ],
    }


def _factor(factor_id: str, label: str, domain: str, factor_kind: str, description: str) -> LatentCalibrationFactor:
    return LatentCalibrationFactor(factor_id, label, domain, factor_kind, description)


def _factor_kind_counts(factors: tuple[LatentCalibrationFactor, ...]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for factor in factors:
        counts[factor.factor_kind] = counts.get(factor.factor_kind, 0) + 1
    return dict(sorted(counts.items()))


def _event_evidence_schema() -> dict[str, object]:
    return {
        "ledger_name": "User Event Evidence Ledger",
        "required_fields": (
            "event_domain",
            "event_type",
            "time_range",
            "date_precision",
            "valence",
            "intensity",
            "confidence",
            "allowed_use",
        ),
        "allowed_domains": ("wealth", "career", "relationship", "health", "relocation", "family", "study", "stress"),
        "allowed_event_types": (
            "income_change",
            "career_transition",
            "relationship_status_change",
            "health_state_change",
            "relocation",
            "family_responsibility_change",
            "education_or_skill_change",
            "high_pressure_period",
        ),
        "allowed_date_precision": ("year", "year_range", "month", "quarter", "unknown"),
        "allowed_valence": ("positive", "neutral", "negative", "mixed", "unknown"),
        "allowed_use": ("personal_calibration_only",),
        "blocked_use": BLOCKED_USES,
    }


def _calibration_inquiry_catalog() -> tuple[dict[str, object], ...]:
    return (
        _inquiry("calib.wealth.change_window", "wealth", "在你记得比较清楚的年份里，收入或资源状态有没有出现过明显变化？", ("wealth_amplifier", "timing_sensitivity")),
        _inquiry("calib.career.transition_window", "career", "你的职业角色、岗位责任或工作平台，是否有过明显转换的阶段？", ("career_amplifier", "resource_support")),
        _inquiry("calib.relationship.status_context", "relationship", "关系状态或亲密关系重心，是否有过比较明确的变化阶段？", ("relationship_sensitivity", "timing_sensitivity")),
        _inquiry("calib.health.state_boundary", "health", "某些年份里，你的精力、压力承受或作息稳定性是否有明显变化？", ("health_safety_modifier", "stress_recovery_capacity")),
        _inquiry("calib.relocation.environment_change", "relocation", "居住地、工作城市或长期环境是否有过明显变化？", ("relocation_mobility", "opportunity_access")),
        _inquiry("calib.stress.recovery_pattern", "stress", "遇到压力较大的阶段时，你通常恢复得较快、较慢，还是波动较大？", ("stress_recovery_capacity", "action_efficiency")),
        _inquiry("calib.resource.support_pattern", "global", "关键转折阶段里，外部资源支持更像是增强、减弱，还是变化不明显？", ("resource_support", "baseline_amplifier")),
        _inquiry("calib.action.result_pattern", "global", "你投入行动后，结果通常来得较快、较慢，还是需要多次尝试？", ("action_efficiency", "baseline_amplifier")),
    )


def _inquiry(inquiry_id: str, domain: str, prompt: str, factor_ids: tuple[str, ...]) -> dict[str, object]:
    return {
        "inquiry_id": inquiry_id,
        "domain": domain,
        "prompt": prompt,
        "factor_ids": factor_ids,
        "allowed_use": "personal_calibration_only",
    }
