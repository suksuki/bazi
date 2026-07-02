from __future__ import annotations

from collections import defaultdict

from v40.contracts.base import AssertionLevel, Polarity, RoleKey, Topic
from v40.contracts.decision import (
    AdvicePlan,
    BranchCandidate,
    DecisionEngineOutput,
    DecisionInputBundle,
    DecisionVerdict,
    ProbeCandidate,
)
from v40.contracts.signal import RuntimeSignal, SignalRegistrySnapshot, SignalSource
from v40.decision.domain_adapters import build_domain_adapter_signals


POLICY_VERSION = "v40.decision.native_product.v1"

CORE_CONTEXT_TOPICS = [Topic.STRUCTURE, Topic.USEFUL_GOD, Topic.TIMING]
PRODUCT_TOPICS = [
    Topic.CAREER,
    Topic.WEALTH,
    Topic.RELATIONSHIP,
    Topic.HEALTH,
    Topic.FAMILY,
    Topic.HIDDEN_ATTRIBUTE,
    Topic.USEFUL_GOD,
    Topic.TIMING,
    Topic.STRUCTURE,
]
TIMELINE_PROBE_TOPICS = {Topic.CAREER, Topic.WEALTH, Topic.RELATIONSHIP, Topic.TIMING}

TOPIC_LABELS = {
    Topic.STRUCTURE: "结构",
    Topic.USEFUL_GOD: "用神",
    Topic.TIMING: "时运",
    Topic.WEALTH: "财运",
    Topic.CAREER: "事业",
    Topic.RELATIONSHIP: "感情",
    Topic.HEALTH: "健康",
    Topic.FAMILY: "亲情",
    Topic.HIDDEN_ATTRIBUTE: "隐藏线索",
    Topic.OVERVIEW: "总览",
}

QUESTION_TOPIC_HINTS = {
    Topic.WEALTH: ["财", "钱", "收入", "投资", "赚钱", "资产"],
    Topic.CAREER: ["事业", "工作", "职业", "岗位", "转型", "平台"],
    Topic.RELATIONSHIP: ["感情", "关系", "婚", "伴侣", "恋爱"],
    Topic.HEALTH: ["健康", "身体", "病", "压力", "睡眠"],
    Topic.FAMILY: ["家庭", "父母", "亲情", "孩子"],
    Topic.TIMING: ["今年", "流年", "大运", "什么时候", "时间"],
    Topic.HIDDEN_ATTRIBUTE: ["隐藏", "暗", "反复", "看不出来"],
    Topic.USEFUL_GOD: ["用神", "喜忌", "忌神"],
}


def build_decision_output(
    *,
    reading_id: str,
    registry: SignalRegistrySnapshot,
    topic: Topic = Topic.OVERVIEW,
    role_key: RoleKey = "user",
    user_question: str = "",
    policy_version: str = POLICY_VERSION,
) -> DecisionEngineOutput:
    eligible_signals = _decision_eligible_signals(registry.signals)
    decision_topics = _select_decision_topics(signals=eligible_signals, topic=topic, user_question=user_question)
    eligible_signals = [
        *eligible_signals,
        *build_domain_adapter_signals(
            reading_id=reading_id,
            signals=eligible_signals,
            topics=decision_topics,
        ),
    ]
    decision_signals = _select_decision_signals(eligible_signals, decision_topics)
    input_bundle = DecisionInputBundle(
        bundle_id=f"decision-input:{reading_id}",
        reading_id=reading_id,
        signal_ids=[signal.signal_id for signal in decision_signals],
        signals=decision_signals,
        policy_version=policy_version,
    )
    branch_candidates = _build_branch_candidates(reading_id=reading_id, signals=decision_signals, topics=decision_topics)
    verdicts = _build_verdicts(
        reading_id=reading_id,
        topics=decision_topics,
        signals=decision_signals,
        branches=branch_candidates,
        user_question=user_question,
    )
    advice_plans = _build_advice_plans(reading_id=reading_id, verdicts=verdicts)
    probes = _build_probes(reading_id=reading_id, verdicts=verdicts, branches=branch_candidates, role_key=role_key)
    return DecisionEngineOutput(
        output_id=f"decision-output:{reading_id}",
        reading_id=reading_id,
        input_bundle=input_bundle,
        branch_candidates=branch_candidates,
        verdicts=verdicts,
        advice_plans=advice_plans,
        probes=probes,
        policy_version=policy_version,
    )


def _select_decision_topics(*, signals: list[RuntimeSignal], topic: Topic, user_question: str) -> list[Topic]:
    requested = topic if topic not in {Topic.OVERVIEW, Topic.UNKNOWN} else _infer_topic(user_question)
    available = [row for row in PRODUCT_TOPICS if any(signal.topic == row for signal in signals)]
    if requested not in {Topic.OVERVIEW, Topic.UNKNOWN}:
        selected = [requested]
    else:
        selected = [row for row in available if row not in CORE_CONTEXT_TOPICS][:3]
        if not selected:
            selected = [Topic.STRUCTURE]
    return selected[:3]


def _decision_eligible_signals(signals: list[RuntimeSignal]) -> list[RuntimeSignal]:
    return [signal for signal in signals if signal.source != SignalSource.ZIWEI_ENGINE]


def _infer_topic(user_question: str) -> Topic:
    question = user_question.strip()
    for topic, hints in QUESTION_TOPIC_HINTS.items():
        if any(hint in question for hint in hints):
            return topic
    return Topic.OVERVIEW


def _select_decision_signals(signals: list[RuntimeSignal], topics: list[Topic]) -> list[RuntimeSignal]:
    selected = [signal for signal in signals if signal.topic in topics or signal.topic in CORE_CONTEXT_TOPICS]
    if selected:
        return selected
    return sorted(signals, key=_signal_score, reverse=True)[:5]


def _build_branch_candidates(
    *,
    reading_id: str,
    signals: list[RuntimeSignal],
    topics: list[Topic],
) -> list[BranchCandidate]:
    grouped = _group_by_topic(signals)
    branches: list[BranchCandidate] = []
    for topic in topics:
        topic_signals = sorted(grouped.get(topic, []), key=_signal_score, reverse=True)
        if not topic_signals and topic not in CORE_CONTEXT_TOPICS:
            topic_signals = sorted(_context_signals(signals), key=_signal_score, reverse=True)[:2]
        if not topic_signals:
            continue
        total = sum(max(0.01, _signal_score(signal)) for signal in topic_signals[:3])
        for index, signal in enumerate(topic_signals[:3], start=1):
            score = max(0.01, _signal_score(signal))
            probability = round(score / total, 2) if total else 0.0
            branches.append(
                BranchCandidate(
                    branch_id=f"branch:{reading_id}:{topic.value}:{index}",
                    reading_id=reading_id,
                    topic=topic,
                    claim=_clean_claim(signal.claim),
                    polarity=signal.polarity,
                    probability=probability,
                    confidence=round(signal.confidence, 2),
                    evidence_refs=[signal.signal_id, *signal.evidence_refs],
                    counter_evidence_refs=signal.counter_evidence_refs,
                    needs_probe=_branch_needs_probe(signal=signal, probability=probability),
                    probe_question=_probe_question(topic),
                )
            )
    return branches


def _build_verdicts(
    *,
    reading_id: str,
    topics: list[Topic],
    signals: list[RuntimeSignal],
    branches: list[BranchCandidate],
    user_question: str,
) -> list[DecisionVerdict]:
    verdicts: list[DecisionVerdict] = []
    grouped_signals = _group_by_topic(signals)
    grouped_branches = _group_branches(branches)
    for topic in topics:
        topic_signals = grouped_signals.get(topic) or _context_signals(signals)
        if not topic_signals:
            continue
        ranked = sorted(topic_signals, key=_signal_score, reverse=True)
        topic_branches = sorted(grouped_branches.get(topic, []), key=lambda row: row.probability, reverse=True)
        primary_branch = topic_branches[0] if topic_branches else None
        context_claims = [_clean_claim(signal.claim) for signal in ranked[:3]]
        confidence = _verdict_confidence(ranked, primary_branch)
        assertion = _assertion_level(confidence=confidence, signals=ranked, primary_branch=primary_branch)
        headline = _headline(topic=topic, primary_branch=primary_branch, user_question=user_question)
        verdicts.append(
            DecisionVerdict(
                verdict_id=f"verdict:{reading_id}:{topic.value}",
                reading_id=reading_id,
                topic=topic,
                headline=headline,
                assertion_level=assertion,
                confidence=confidence,
                allowed_assertions=context_claims,
                forbidden_assertions=[
                    "不要把候选用神直接说成唯一答案。",
                    "不要把时运入口直接说成确定年份结果。",
                    "不要绕开证据链直接给人生定性。",
                ],
                evidence_refs=_evidence_refs(ranked, primary_branch),
                counter_evidence_refs=_counter_evidence_refs(ranked, primary_branch),
                primary_branch_id=primary_branch.branch_id if primary_branch else "",
                alternative_branch_ids=[branch.branch_id for branch in topic_branches[1:3]],
                next_probe_ids=[f"probe:{reading_id}:{topic.value}:1"],
            )
        )
    if verdicts:
        return verdicts
    fallback = sorted(signals, key=_signal_score, reverse=True)[:3]
    claim = _clean_claim(fallback[0].claim) if fallback else "当前信号不足，先补充命盘和现实背景。"
    return [
        DecisionVerdict(
            verdict_id=f"verdict:{reading_id}:overview",
            reading_id=reading_id,
            topic=Topic.OVERVIEW,
            headline="先补齐关键证据，再进入结论",
            assertion_level=AssertionLevel.WEAK_CANDIDATE,
            confidence=0.34,
            allowed_assertions=[claim],
            forbidden_assertions=["不要在证据不足时给强断语。"],
            evidence_refs=[signal.signal_id for signal in fallback],
            next_probe_ids=[f"probe:{reading_id}:overview:1"],
        )
    ]


def _build_advice_plans(*, reading_id: str, verdicts: list[DecisionVerdict]) -> list[AdvicePlan]:
    return [
        AdvicePlan(
            advice_id=f"advice:{verdict.verdict_id}",
            reading_id=reading_id,
            topic=verdict.topic,
            source_verdict_ids=[verdict.verdict_id],
            action_points=_action_points(verdict.topic),
            avoid_points=_avoid_points(verdict.topic),
            condition_points=_condition_points(verdict.topic, verdict),
            priority=round(verdict.confidence, 2),
            evidence_refs=verdict.evidence_refs,
        )
        for verdict in verdicts
    ]


def _build_probes(
    *,
    reading_id: str,
    verdicts: list[DecisionVerdict],
    branches: list[BranchCandidate],
    role_key: RoleKey,
) -> list[ProbeCandidate]:
    branch_lookup = _group_branches(branches)
    probes: list[ProbeCandidate] = []
    for verdict in verdicts:
        topic_branches = branch_lookup.get(verdict.topic, [])
        target_branches = [branch.branch_id for branch in topic_branches[:2]]
        probes.append(
            ProbeCandidate(
                probe_id=f"probe:{reading_id}:{verdict.topic.value}:1",
                reading_id=reading_id,
                probe_type="manifestation",
                topic=verdict.topic,
                question=_probe_question(verdict.topic),
                options=_probe_options(verdict.topic),
                target_branch_ids=target_branches,
                target_verdict_ids=[verdict.verdict_id],
                target_domains=[verdict.topic],
                target_hidden_attribute_ids=[verdict.verdict_id] if verdict.topic == Topic.HIDDEN_ATTRIBUTE else [],
                impact_preview=_probe_impact_preview(verdict.topic, "manifestation"),
                expected_information_gain=_information_gain(verdict, topic_branches),
                user_cost=0.25 if role_key == "practitioner" else 0.32,
                ask_now=False,
            )
        )
        if verdict.topic in TIMELINE_PROBE_TOPICS:
            probes.append(
                ProbeCandidate(
                    probe_id=f"probe:{reading_id}:{verdict.topic.value}:timeline",
                    reading_id=reading_id,
                    probe_type="timeline",
                    topic=verdict.topic,
                    question=_timeline_probe_question(verdict.topic),
                    options=_timeline_probe_options(),
                    target_branch_ids=target_branches,
                    target_verdict_ids=[verdict.verdict_id],
                    target_domains=[verdict.topic, Topic.TIMING],
                    target_years=_timeline_probe_years(),
                    impact_preview=_probe_impact_preview(verdict.topic, "timeline"),
                    expected_information_gain=min(0.86, _information_gain(verdict, topic_branches) + 0.08),
                    user_cost=0.30 if role_key == "practitioner" else 0.38,
                    ask_now=False,
                )
            )
    return probes


def _group_by_topic(signals: list[RuntimeSignal]) -> dict[Topic, list[RuntimeSignal]]:
    grouped: dict[Topic, list[RuntimeSignal]] = defaultdict(list)
    for signal in signals:
        grouped[signal.topic].append(signal)
    return grouped


def _group_branches(branches: list[BranchCandidate]) -> dict[Topic, list[BranchCandidate]]:
    grouped: dict[Topic, list[BranchCandidate]] = defaultdict(list)
    for branch in branches:
        grouped[branch.topic].append(branch)
    return grouped


def _context_signals(signals: list[RuntimeSignal]) -> list[RuntimeSignal]:
    return [signal for signal in signals if signal.topic in CORE_CONTEXT_TOPICS]


def _signal_score(signal: RuntimeSignal) -> float:
    polarity_factor = 0.86 if signal.polarity in {Polarity.MIXED, Polarity.NEUTRAL} else 1.0
    return round(max(0.01, signal.strength * 0.55 + signal.confidence * 0.45) * polarity_factor, 4)


def _verdict_confidence(signals: list[RuntimeSignal], primary_branch: BranchCandidate | None) -> float:
    if not signals:
        return 0.32
    top = max(_signal_score(signal) for signal in signals)
    support_density = sum(1 for signal in signals if signal.polarity == Polarity.SUPPORT) / max(1, len(signals))
    branch_bonus = (primary_branch.probability * 0.1) if primary_branch else 0.0
    return round(max(0.32, min(0.82, top * 0.78 + support_density * 0.12 + branch_bonus)), 2)


def _assertion_level(
    *,
    confidence: float,
    signals: list[RuntimeSignal],
    primary_branch: BranchCandidate | None,
) -> AssertionLevel:
    if any(signal.polarity == Polarity.MIXED for signal in signals) or (
        primary_branch is not None and primary_branch.needs_probe
    ):
        return AssertionLevel.MIXED
    if confidence >= 0.58:
        return AssertionLevel.SUPPORTED
    return AssertionLevel.WEAK_CANDIDATE


def _branch_needs_probe(*, signal: RuntimeSignal, probability: float) -> bool:
    if signal.polarity == Polarity.MIXED:
        return True
    if signal.counter_evidence_refs:
        return True
    return probability < 0.46 or signal.confidence < 0.55


def _information_gain(verdict: DecisionVerdict, branches: list[BranchCandidate]) -> float:
    if not branches:
        return 0.45
    ranked = sorted(branches, key=lambda branch: branch.probability, reverse=True)
    gap = ranked[0].probability - (ranked[1].probability if len(ranked) > 1 else 0.0)
    uncertainty = 1.0 - verdict.confidence
    return round(max(0.35, min(0.82, uncertainty + max(0.0, 0.35 - gap))), 2)


def _evidence_refs(signals: list[RuntimeSignal], primary_branch: BranchCandidate | None) -> list[str]:
    refs: list[str] = []
    if primary_branch:
        refs.extend(primary_branch.evidence_refs)
    for signal in signals[:3]:
        refs.append(signal.signal_id)
        refs.extend(signal.evidence_refs)
    return _unique(refs)


def _counter_evidence_refs(signals: list[RuntimeSignal], primary_branch: BranchCandidate | None) -> list[str]:
    refs: list[str] = []
    if primary_branch:
        refs.extend(primary_branch.counter_evidence_refs)
    for signal in signals[:3]:
        refs.extend(signal.counter_evidence_refs)
    return _unique(refs)


def _unique(rows: list[str]) -> list[str]:
    result: list[str] = []
    for row in rows:
        if row and row not in result:
            result.append(row)
    return result


def _headline(*, topic: Topic, primary_branch: BranchCandidate | None, user_question: str) -> str:
    label = TOPIC_LABELS.get(topic, "命局")
    if user_question.strip() and topic not in CORE_CONTEXT_TOPICS:
        return f"{label}先回答这一个问题"
    if primary_branch is None:
        return f"{label}先补关键证据"
    return f"{label}主线：{_short_text(primary_branch.claim, limit=22)}"


def _action_points(topic: Topic) -> list[str]:
    table = {
        Topic.CAREER: [
            "优先选择能承接责任、形成资质或稳定交付的方向。",
            "把外部压力拆成流程、作品和可复用能力。",
        ],
        Topic.WEALTH: [
            "先确认钱从哪里来，再确认风险由谁承担。",
            "收益判断要绑定资源、职责和分配结构，不单看机会大小。",
        ],
        Topic.RELATIONSHIP: [
            "先看互动节奏和边界，再谈承诺或推进速度。",
            "把反复出现的沟通模式记录下来，用来校准关系分支。",
        ],
        Topic.HEALTH: [
            "先观察压力、作息和身体反馈哪条最明显。",
            "把健康建议落到节奏管理和消耗控制上。",
        ],
        Topic.TIMING: [
            "把大运和流年作为触发背景，先看被触发的是职责、资源还是关系。",
            "年份判断只在证据集中时提高权重。",
        ],
        Topic.USEFUL_GOD: [
            "先保留用神候选，再用现实反馈拉开权重。",
            "看候选五行是否对应到资源、输出、压力承接或关系协同。",
        ],
        Topic.STRUCTURE: [
            "先锁定身强身弱和月令关系，再进入领域判断。",
            "结构未拉开前，领域结论保持边界。",
        ],
    }
    return table.get(topic, ["先把结论绑定到一个可验证的现实问题上。"])


def _avoid_points(topic: Topic) -> list[str]:
    table = {
        Topic.CAREER: ["不要把岗位变化直接等同于转型成功。"],
        Topic.WEALTH: ["不要只看赚钱冲动，忽略分配和风险边界。"],
        Topic.RELATIONSHIP: ["不要把一时情绪当作长期关系定论。"],
        Topic.HEALTH: ["不要把压力反馈说成确定病症。"],
        Topic.TIMING: ["不要把大运流年入口说成单一年份断语。"],
        Topic.USEFUL_GOD: ["不要把候选用神说成唯一答案。"],
        Topic.STRUCTURE: ["不要在结构证据不足时强行定格局。"],
    }
    return table.get(topic, ["不要绕开证据链直接下强断语。"])


def _condition_points(topic: Topic, verdict: DecisionVerdict) -> list[str]:
    if verdict.assertion_level == AssertionLevel.MIXED:
        return ["如果用户反馈能排除一个分支，再把主分支升权。"]
    if topic == Topic.TIMING:
        return ["如果补充关键年份和事件，再把时运触发点细化。"]
    return ["如果后续反馈与当前结论相反，保留反证并降低断语强度。"]


def _probe_question(topic: Topic) -> str:
    table = {
        Topic.CAREER: "最近更明显的是职责压力、平台资源，还是想换方向？",
        Topic.WEALTH: "最近财务更像主动争取、稳步积累，还是风险压力？",
        Topic.RELATIONSHIP: "关系里最反复的是表达冲突、距离边界，还是承诺节奏？",
        Topic.HEALTH: "最近更明显的是压力消耗、作息紊乱，还是身体反馈？",
        Topic.FAMILY: "家庭里更明显的是责任牵引、资源支持，还是边界压力？",
        Topic.HIDDEN_ATTRIBUTE: "是否有反复出现但命盘表层不容易直接解释的经历？",
        Topic.USEFUL_GOD: "近期更能帮你稳定状态的是资源支持、减少消耗，还是承担压力？",
        Topic.TIMING: "当前大运和流年更触发事业、财务、关系，还是健康节奏？",
        Topic.STRUCTURE: "当前更能印证身强、身弱，还是中和待复核？",
    }
    return table.get(topic, "这个问题最需要补充哪一条现实线索？")


def _probe_options(topic: Topic) -> list[str]:
    table = {
        Topic.CAREER: ["职责压力", "平台资源", "想换方向", "都不明显"],
        Topic.WEALTH: ["固定收入", "项目客户", "合伙分配", "投资波动", "暂不确定"],
        Topic.RELATIONSHIP: ["表达冲突", "距离边界", "承诺节奏", "暂不确定"],
        Topic.HEALTH: ["压力消耗", "作息紊乱", "身体反馈", "暂不确定"],
        Topic.FAMILY: ["责任牵引", "资源支持", "边界压力", "暂不确定"],
        Topic.HIDDEN_ATTRIBUTE: ["反复经历明显", "偶尔出现", "暂时没有", "不确定"],
        Topic.USEFUL_GOD: ["更像扶身", "更像疏通", "更像承压后转化", "还不确定"],
        Topic.TIMING: ["事业触发", "财务触发", "关系触发", "健康节奏", "暂不明显"],
        Topic.STRUCTURE: ["更像身强", "更像身弱", "中和待复核", "还不确定"],
    }
    return table.get(topic, ["更像前者", "更像后者", "暂不确定"])


def _timeline_probe_question(topic: Topic) -> str:
    label = TOPIC_LABELS.get(topic, "命局")
    if topic == Topic.TIMING:
        return "这几年里，哪一年变化最明显？"
    return f"从{label}来看，这几年里哪一年变化最明显？"


def _timeline_probe_options() -> list[str]:
    return [*_timeline_probe_years(), "都不明显"]


def _timeline_probe_years() -> list[str]:
    return ["2023", "2024", "2025", "2026"]


def _probe_impact_preview(topic: Topic, probe_type: str) -> list[str]:
    label = TOPIC_LABELS.get(topic, "命局")
    if probe_type == "timeline":
        return [
            f"会影响{label}判断里哪一年应事更明显。",
            "会影响时运触发点和下一条事件追问。",
            "会把年份反馈转成后续训练素材。",
        ]
    return [
        f"会影响{label}主分支和备选分支的权重。",
        "会影响本页建议从宽泛判断转成现实可执行建议。",
        "会生成可回放的用户反馈训练素材。",
    ]


def _clean_claim(text: str) -> str:
    return " ".join(text.replace("；", "，").split())


def _short_text(text: str, *, limit: int) -> str:
    clean = _clean_claim(text)
    if len(clean) <= limit:
        return clean
    return f"{clean[:limit]}..."
