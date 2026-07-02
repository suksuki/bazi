from __future__ import annotations

from v40.contracts.base import EngineKey, RoleKey, SurfaceKey, Topic
from v40.contracts.context import ClientContext, LocaleContext, RoleContext, default_client_context, default_locale_context, default_role_context
from v40.contracts.decision import AdvicePlan, BranchCandidate, DecisionVerdict, ProbeCandidate
from v40.contracts.engine import MultiEngineRunResult
from v40.contracts.output import (
    BranchCard,
    MingliCandidateBoard,
    MingliCandidateGroup,
    ProductAdviceCard,
    ProductProjectionBundle,
    ProductVerdictCard,
    SurfaceBundle,
    SurfaceSection,
    SystemAssertionCandidate,
)
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
    locale_context: LocaleContext | None = None,
    role_context: RoleContext | None = None,
    client_context: ClientContext | None = None,
) -> SurfaceBundle:
    resolved_locale = locale_context or default_locale_context("zh-CN")
    resolved_role = role_context or default_role_context(role_key)
    resolved_client = client_context or default_client_context("web")
    practitioner_lens = build_practitioner_lens(
        reading_id=reading_id,
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
        locale=resolved_locale.locale,
        device_type=resolved_client.device_type,
        locale_context=resolved_locale,
        role_context=resolved_role,
        client_context=resolved_client,
        sections=_surface_sections(role_key=role_key, client_context=resolved_client),
        surfaces=surfaces,
        report_first=True,
        probe_invited_only=True,
        conversation_invited_only=True,
        thinking_requested_only=True,
    )


def _surface_sections(*, role_key: RoleKey, client_context: ClientContext) -> list[SurfaceSection]:
    mobile = client_context.device_type == "mobile"
    sections = [
        SurfaceSection(
            section_id="reading.core",
            section_type=SurfaceKey.READING,
            priority=100,
            default_collapsed=False,
            mobile_collapsed=False,
            role_visibility=["guest", "user", "practitioner"],
        ),
        SurfaceSection(
            section_id="conversation.invited",
            section_type=SurfaceKey.CONVERSATION,
            priority=70,
            default_collapsed=False,
            mobile_collapsed=False,
            role_visibility=["user", "practitioner"],
        ),
        SurfaceSection(
            section_id="calibration.practitioner",
            section_type=SurfaceKey.CALIBRATION,
            priority=60,
            default_collapsed=role_key != "practitioner",
            mobile_collapsed=True,
            role_visibility=["practitioner"],
        ),
        SurfaceSection(
            section_id="thinking.requested",
            section_type=SurfaceKey.THINKING,
            priority=20,
            default_collapsed=True,
            mobile_collapsed=True,
            role_visibility=["practitioner", "admin"],
        ),
    ]
    if mobile:
        return sorted(sections, key=lambda item: (-item.priority, item.mobile_collapsed))
    return sorted(sections, key=lambda item: -item.priority)


def build_practitioner_lens(
    *,
    reading_id: str,
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
    candidate_board = _build_candidate_board(reading_id=reading_id, branches=branches, probes=probes)
    return {
        "available": True,
        "mode": "practitioner_lens",
        "summary": {
            "bazi_signal_count": len(bazi_signals),
            "ziwei_signal_count": len(ziwei_signals),
            "branch_count": len(branches),
            "probe_count": len(probes),
            "ziwei_probe_trigger_count": len(sidecar_probes),
            "candidate_count": sum(len(group["candidates"]) for group in candidate_board["groups"]),
        },
        "candidate_board": candidate_board,
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
            {"key": "more_like_this", "label": "采为主断", "training_label": "supports"},
            {"key": "supporting_context", "label": "作为辅助", "training_label": "probe_helpful"},
            {"key": "do_not_use_now", "label": "暂不采用", "training_label": "weakens"},
            {"key": "ask_to_confirm", "label": "需要追问", "training_label": "needs_probe"},
            {"key": "user_mismatch", "label": "用户反馈不符", "training_label": "mismatch"},
            {"key": "note", "label": "添加备注", "training_label": "probe_helpful"},
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


def _build_candidate_board(
    *,
    reading_id: str,
    branches: list[BranchCard],
    probes: list[ProbeCandidate],
) -> dict[str, object]:
    grouped: dict[str, list[SystemAssertionCandidate]] = {}
    branch_rank: dict[Topic, int] = {}
    for branch in branches:
        branch_rank[branch.topic] = branch_rank.get(branch.topic, 0) + 1
        candidate = SystemAssertionCandidate(
            candidate_id=f"candidate:{branch.source_branch_id}",
            candidate_type=_branch_candidate_type(branch.topic),
            topic=branch.topic,
            title=branch.title,
            summary=branch.practitioner_summary or branch.user_summary,
            current_status="primary" if branch_rank[branch.topic] == 1 else "alternative",
            confidence_label=branch.confidence_label,
            target_type="branch",
            target_ids=[branch.source_branch_id],
            suggested_probe_question=branch.key_question,
            impact_preview=_candidate_impact_preview(branch.topic, "branch"),
        )
        grouped.setdefault(_candidate_group_id(branch.topic), []).append(candidate)
    for probe in probes:
        candidate = SystemAssertionCandidate(
            candidate_id=f"candidate:{probe.probe_id}",
            candidate_type="timeline_probe" if probe.probe_type == "timeline" else "probe_candidate",
            topic=probe.topic,
            title=_probe_candidate_title(probe),
            summary=probe.question,
            current_status="needs_probe",
            confidence_label=_probe_gain_label(probe.expected_information_gain),
            target_type="probe",
            target_ids=[probe.probe_id],
            suggested_probe_question=probe.question,
            impact_preview=probe.impact_preview or _candidate_impact_preview(probe.topic, "probe"),
        )
        grouped.setdefault(_candidate_group_id(probe.topic), []).append(candidate)
    groups = [
        MingliCandidateGroup(
            group_id=group_id,
            title=_candidate_group_title(group_id),
            candidates=candidates[:5],
        )
        for group_id, candidates in grouped.items()
        if candidates
    ]
    board = MingliCandidateBoard(
        board_id=f"candidate-board:{reading_id}",
        reading_id=reading_id,
        groups=sorted(groups, key=lambda group: _candidate_group_order(group.group_id)),
        actions=_candidate_board_actions(),
    )
    return board.model_dump(mode="json")


def _candidate_board_actions() -> list[dict[str, str]]:
    return [
        {"key": "more_like_this", "label": "采为主断"},
        {"key": "supporting_context", "label": "作为辅助"},
        {"key": "do_not_use_now", "label": "暂不采用"},
        {"key": "ask_to_confirm", "label": "需要追问"},
        {"key": "user_mismatch", "label": "用户反馈不符"},
        {"key": "note", "label": "添加备注"},
    ]


def _branch_candidate_type(topic: Topic) -> str:
    table = {
        Topic.STRUCTURE: "structure_candidate",
        Topic.USEFUL_GOD: "useful_god_candidate",
        Topic.TIMING: "timing_window",
        Topic.WEALTH: "wealth_branch",
        Topic.CAREER: "career_branch",
        Topic.RELATIONSHIP: "relationship_branch",
        Topic.HEALTH: "health_branch",
        Topic.FAMILY: "family_branch",
        Topic.HIDDEN_ATTRIBUTE: "hidden_attribute_candidate",
    }
    return table.get(topic, "mingli_branch")


def _candidate_group_id(topic: Topic) -> str:
    table = {
        Topic.STRUCTURE: "structure",
        Topic.USEFUL_GOD: "structure",
        Topic.TIMING: "timing",
        Topic.WEALTH: "wealth",
        Topic.CAREER: "career",
        Topic.RELATIONSHIP: "relationship",
        Topic.HEALTH: "health",
        Topic.FAMILY: "family",
        Topic.HIDDEN_ATTRIBUTE: "hidden_attribute",
    }
    return table.get(topic, "overview")


def _candidate_group_title(group_id: str) -> str:
    table = {
        "structure": "命局骨架",
        "wealth": "财富断项",
        "career": "事业断项",
        "relationship": "感情断项",
        "timing": "时运断项",
        "health": "健康断项",
        "family": "亲情断项",
        "hidden_attribute": "隐藏线索",
    }
    return table.get(group_id, "综合断项")


def _candidate_group_order(group_id: str) -> int:
    order = {
        "structure": 10,
        "wealth": 20,
        "career": 30,
        "relationship": 40,
        "timing": 50,
        "health": 60,
        "family": 70,
        "hidden_attribute": 80,
    }
    return order.get(group_id, 99)


def _probe_candidate_title(probe: ProbeCandidate) -> str:
    label = _topic_label(probe.topic)
    if probe.probe_type == "timeline":
        years = " / ".join(probe.target_years[:3])
        return f"{label}年份探针" if not years else f"{label}年份探针：{years}"
    if probe.probe_type == "event":
        return f"{label}事件探针"
    if probe.probe_type == "luck_transition":
        return f"{label}大运切换探针"
    return f"{label}显化探针"


def _probe_gain_label(value: float) -> str:
    if value >= 0.72:
        return "信息增益高"
    if value >= 0.50:
        return "值得追问"
    return "轻量校准"


def _candidate_impact_preview(topic: Topic, target_kind: str) -> list[str]:
    label = _topic_label(topic)
    if target_kind == "branch":
        return [
            f"会影响{label}主断与备选断项排序。",
            f"会调整{label}建议的表达重点。",
            "会形成命理师本地校准记录并进入训练素材。",
        ]
    return [
        f"会补足{label}判断的现实线索。",
        "会影响下一轮 Probe 或对话问题。",
        "会把用户回答转成可回放训练素材。",
    ]


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
