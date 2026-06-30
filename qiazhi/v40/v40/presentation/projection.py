from __future__ import annotations

from v40.contracts.base import EngineKey, RoleKey, SurfaceKey, Topic
from v40.contracts.decision import AdvicePlan, BranchCandidate, DecisionVerdict, ProbeCandidate
from v40.contracts.engine import MultiEngineRunResult
from v40.contracts.output import BranchCard, ProductAdviceCard, ProductProjectionBundle, ProductVerdictCard, SurfaceBundle
from v40.contracts.signal import SignalRegistrySnapshot, SignalSource


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
    signal_registry: SignalRegistrySnapshot | None = None,
    engine_result: MultiEngineRunResult | None = None,
) -> SurfaceBundle:
    practitioner_lens = build_practitioner_lens(
        role_key=role_key,
        signal_registry=signal_registry,
        engine_result=engine_result,
        branches=projection.branch_cards,
        probes=probes,
    )
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
            "practitioner_lens": practitioner_lens,
            "selection_endpoint": "/api/v40/calibration/practitioner-lens-action",
            "legacy_selection_endpoint": "/api/v40/calibration/practitioner-selection",
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


def build_practitioner_lens(
    *,
    role_key: RoleKey,
    signal_registry: SignalRegistrySnapshot | None,
    engine_result: MultiEngineRunResult | None,
    branches: list[BranchCard],
    probes: list[ProbeCandidate],
) -> dict[str, object]:
    if role_key != "practitioner":
        return {
            "available": False,
            "reason": "专业视角仅命理师可见，普通用户只看融合后的报告和追问。",
        }
    signals = signal_registry.signals if signal_registry else []
    bazi_signals = [signal for signal in signals if signal.source == SignalSource.BAZI_ENGINE]
    ziwei_signals = [signal for signal in signals if signal.source == SignalSource.ZIWEI_ENGINE]
    bazi_topics = {signal.topic for signal in bazi_signals}
    ziwei_topics = {signal.topic for signal in ziwei_signals}
    sidecar_probes = _ziwei_probe_triggers(engine_result)
    return {
        "available": True,
        "mode": "practitioner_lens",
        "summary": {
            "bazi_signal_count": len(bazi_signals),
            "ziwei_signal_count": len(ziwei_signals),
            "branch_count": len(branches),
            "probe_count": len(probes),
            "ziwei_probe_trigger_count": len(sidecar_probes),
        },
        "agreement_topics": [_topic_label(topic) for topic in sorted(bazi_topics.intersection(ziwei_topics), key=lambda row: row.value)],
        "ziwei_sidecar_topics": [_topic_label(topic) for topic in sorted(ziwei_topics, key=lambda row: row.value)],
        "ziwei_signals": [
            {
                "signal_id": signal.signal_id,
                "topic": _topic_label(signal.topic),
                "claim": signal.claim,
                "confidence_label": _confidence_label(signal.confidence),
                "evidence_refs": signal.evidence_refs,
            }
            for signal in ziwei_signals[:8]
        ],
        "probe_triggers": sidecar_probes[:6],
        "calibration_actions": [
            {"key": "more_like_this", "label": "更像这个表现", "training_label": "supports"},
            {"key": "supporting_context", "label": "作为辅助参考", "training_label": "probe_helpful"},
            {"key": "do_not_use_now", "label": "暂不采用", "training_label": "weakens"},
            {"key": "ask_to_confirm", "label": "需要追问确认", "training_label": "needs_probe"},
            {"key": "user_mismatch", "label": "用户反馈不符合", "training_label": "mismatch"},
        ],
        "boundaries": {
            "changes_verdict": False,
            "changes_chart_facts": False,
            "writes_global_weight": False,
            "ordinary_user_visible": False,
        },
    }


def _ziwei_probe_triggers(engine_result: MultiEngineRunResult | None) -> list[dict[str, object]]:
    if engine_result is None:
        return []
    triggers: list[dict[str, object]] = []
    for result in engine_result.results:
        if result.engine != EngineKey.ZIWEI:
            continue
        triggers.extend(result.probe_candidates)
    return triggers


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
