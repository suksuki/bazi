from __future__ import annotations

from v40.contracts.base import RoleKey, Topic
from v40.contracts.decision import AdvicePlan, DecisionVerdict
from v40.contracts.output import ProductAdviceCard, ProductProjectionBundle, ProductVerdictCard


def build_product_projection(
    *,
    reading_id: str,
    role_key: RoleKey,
    verdicts: list[DecisionVerdict],
    advice_plans: list[AdvicePlan],
) -> ProductProjectionBundle:
    product_verdict_cards = [
        ProductVerdictCard(
            card_id=f"card:{verdict.verdict_id}",
            source_verdict_id=verdict.verdict_id,
            topic=verdict.topic,
            title=verdict.headline,
            primary_text=(verdict.allowed_assertions[0] if verdict.allowed_assertions else verdict.headline),
            confidence_label=_confidence_label(verdict.confidence),
            assertion_level=verdict.assertion_level,
            evidence_count=len(verdict.evidence_refs),
            role_visibility=_role_visibility(role_key),
        )
        for verdict in verdicts
    ]
    product_advice_cards = [
        ProductAdviceCard(
            card_id=f"card:{advice.advice_id}",
            source_advice_id=advice.advice_id,
            topic=advice.topic,
            title=_advice_title(advice.topic),
            action_points=advice.action_points,
            avoid_points=advice.avoid_points,
            condition_points=advice.condition_points,
            role_visibility=_role_visibility(role_key),
        )
        for advice in advice_plans
    ]
    return ProductProjectionBundle(
        reading_id=reading_id,
        role_key=role_key,
        verdict_cards=product_verdict_cards,
        advice_cards=product_advice_cards,
        leakage_scan_passed=_projection_is_clean(product_verdict_cards, product_advice_cards),
    )


def _role_visibility(role_key: RoleKey) -> list[RoleKey]:
    if role_key in {"guest", "user"}:
        return ["guest", "user", "practitioner"]
    return [role_key]


def _confidence_label(value: float) -> str:
    if value >= 0.72:
        return "证据较集中"
    if value >= 0.55:
        return "证据支持"
    if value >= 0.38:
        return "需要保留边界"
    return "待校准"


def _advice_title(topic: Topic) -> str:
    labels = {
        Topic.CAREER: "事业建议",
        Topic.WEALTH: "财运建议",
        Topic.RELATIONSHIP: "关系建议",
        Topic.HEALTH: "健康建议",
        Topic.TIMING: "时运建议",
        Topic.USEFUL_GOD: "用神建议",
    }
    return labels.get(topic, "行动建议")


def _projection_is_clean(*groups: object) -> bool:
    rendered = str(groups)
    forbidden = [
        "policy_key",
        "training_target",
        "runtime_debug",
        "claim_key",
        "conflict_group_id",
    ]
    return not any(token in rendered for token in forbidden)
