from __future__ import annotations

from v40.contracts.base import RoleKey, SurfaceKey, Topic
from v40.contracts.decision import AdvicePlan, BranchCandidate, DecisionVerdict, ProbeCandidate
from v40.contracts.output import BranchCard, ProductAdviceCard, ProductProjectionBundle, ProductVerdictCard, SurfaceBundle


def build_product_projection(
    *,
    reading_id: str,
    role_key: RoleKey,
    verdicts: list[DecisionVerdict],
    advice_plans: list[AdvicePlan],
    branches: list[BranchCandidate] | None = None,
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
    branch_cards = _build_branch_cards(role_key=role_key, branches=branches or [])
    return ProductProjectionBundle(
        reading_id=reading_id,
        role_key=role_key,
        verdict_cards=product_verdict_cards,
        branch_cards=branch_cards,
        advice_cards=product_advice_cards,
        leakage_scan_passed=_projection_is_clean(product_verdict_cards, branch_cards, product_advice_cards),
    )


def build_surface_bundle(
    *,
    reading_id: str,
    role_key: RoleKey,
    projection: ProductProjectionBundle,
    probes: list[ProbeCandidate],
    signal_count: int,
    branch_count: int,
) -> SurfaceBundle:
    surfaces = {
        SurfaceKey.READING: {
            "title": "命理测算结果",
            "verdict_card_ids": [card.card_id for card in projection.verdict_cards],
            "advice_card_ids": [card.card_id for card in projection.advice_cards],
            "signal_count": signal_count,
            "report_first": True,
        },
        SurfaceKey.CALIBRATION: {
            "available": role_key == "practitioner",
            "branch_card_ids": [card.card_id for card in projection.branch_cards],
            "branch_count": branch_count,
            "selection_endpoint": "/api/v40/calibration/practitioner-selection",
            "auto_open": False,
        },
        SurfaceKey.CONVERSATION: {
            "available": bool(probes),
            "probe_ids": [probe.probe_id for probe in probes],
            "auto_start": False,
            "invited_only": True,
        },
        SurfaceKey.THINKING: {
            "available": False,
            "requested_only": True,
            "reason": "V40 separates internal reasoning, user report, and optional dialogue surfaces.",
        },
    }
    return SurfaceBundle(
        reading_id=reading_id,
        role_key=role_key,
        surfaces=surfaces,
        report_first=True,
        probe_invited_only=True,
        conversation_invited_only=True,
        thinking_requested_only=True,
    )


def _build_branch_cards(*, role_key: RoleKey, branches: list[BranchCandidate]) -> list[BranchCard]:
    if role_key != "practitioner":
        return []
    return [
        BranchCard(
            card_id=f"card:{branch.branch_id}",
            source_branch_id=branch.branch_id,
            topic=branch.topic,
            title=f"{_topic_label(branch.topic)}分支 {index}",
            user_summary=_branch_user_summary(branch),
            practitioner_summary=_branch_practitioner_summary(branch),
            key_question=branch.probe_question,
            confidence_label=_confidence_label(branch.confidence),
            role_visibility=["practitioner"],
        )
        for index, branch in enumerate(branches, start=1)
    ]


def _branch_user_summary(branch: BranchCandidate) -> str:
    label = _topic_label(branch.topic)
    return f"{label}当前保留这一种可能：{branch.claim}"


def _branch_practitioner_summary(branch: BranchCandidate) -> str:
    percent = int(round(branch.probability * 100))
    if branch.needs_probe:
        return f"权重约{percent}%，需要通过追问或命理师校准拉开分支。"
    return f"权重约{percent}%，可作为当前主分支或备选分支审阅。"


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


def _topic_label(topic: Topic) -> str:
    labels = {
        Topic.CAREER: "事业",
        Topic.WEALTH: "财运",
        Topic.RELATIONSHIP: "关系",
        Topic.HEALTH: "健康",
        Topic.TIMING: "时运",
        Topic.USEFUL_GOD: "用神",
        Topic.STRUCTURE: "结构",
        Topic.FAMILY: "亲情",
        Topic.HIDDEN_ATTRIBUTE: "隐藏线索",
    }
    return labels.get(topic, "命局")


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
