from __future__ import annotations

from v40.contracts.base import AssertionLevel, Polarity, RoleKey, Topic
from v40.contracts.decision import BranchCandidate, DecisionVerdict, ProbeCandidate
from v40.contracts.probe import ProbeAnswerResult
from v40.contracts.signal import RuntimeSignal, SignalSource


HIDDEN_FACTOR_POLICY_VERSION = "v40.hidden_factor_probe_engine.v1"

DOMAIN_PRIORITY = [
    Topic.CAREER,
    Topic.WEALTH,
    Topic.RELATIONSHIP,
    Topic.HEALTH,
    Topic.TIMING,
    Topic.USEFUL_GOD,
    Topic.FAMILY,
    Topic.HIDDEN_ATTRIBUTE,
]


def build_hidden_factor_probe_candidates(
    *,
    reading_id: str,
    verdicts: list[DecisionVerdict],
    branches: list[BranchCandidate],
    signals: list[RuntimeSignal],
    role_key: RoleKey = "user",
    limit: int = 1,
) -> list[ProbeCandidate]:
    if limit <= 0 or not verdicts:
        return []
    focus_rows = _rank_focus_topics(verdicts=verdicts, branches=branches, signals=signals)
    probes: list[ProbeCandidate] = []
    for focus_topic, gain in focus_rows[:limit]:
        target_verdicts = [verdict for verdict in verdicts if verdict.topic == focus_topic] or verdicts[:1]
        target_branches = [branch for branch in branches if branch.topic == focus_topic][:3]
        if not target_branches and branches:
            target_branches = branches[:2]
        user_cost = 0.22 if role_key == "practitioner" else 0.30
        if gain < 0.42:
            continue
        probes.append(
            ProbeCandidate(
                probe_id=f"probe:{reading_id}:hidden_factor:{focus_topic.value}",
                reading_id=reading_id,
                probe_type="event",
                topic=Topic.HIDDEN_ATTRIBUTE,
                question=_hidden_factor_question(focus_topic),
                options=_hidden_factor_options(focus_topic),
                target_branch_ids=[branch.branch_id for branch in target_branches],
                target_verdict_ids=[verdict.verdict_id for verdict in target_verdicts],
                target_domains=_unique_topics([focus_topic, Topic.HIDDEN_ATTRIBUTE]),
                target_hidden_attribute_ids=[
                    f"hidden_factor:{reading_id}:{focus_topic.value}",
                    *[verdict.verdict_id for verdict in target_verdicts],
                ],
                impact_preview=_hidden_factor_impact_preview(focus_topic),
                expected_information_gain=gain,
                user_cost=user_cost,
                ask_now=gain > user_cost + 0.18,
            )
        )
    return probes


def build_hidden_factor_answer_runtime_signal(*, result: ProbeAnswerResult) -> RuntimeSignal:
    answer_signal = result.answer_signal
    hidden_update = result.hidden_attribute_update
    trainable_probe_ref = f"probe_voi.{answer_signal.probe_id}" if answer_signal.probe_id else "probe_voi.hidden_factor.recovery"
    topic = hidden_update.topic if hidden_update.topic != Topic.UNKNOWN else Topic.HIDDEN_ATTRIBUTE
    return RuntimeSignal(
        signal_id=f"runtime:{answer_signal.signal_id}",
        reading_id=result.reading_id,
        source=SignalSource.REALITY_PROBE,
        source_ref="hidden_factor_probe_answer",
        topic=topic,
        claim=answer_signal.interpreted_claim,
        claim_key=f"hidden_factor.answer.{hidden_update.attribute_key}",
        polarity=answer_signal.polarity,
        strength=0.46 if answer_signal.polarity == Polarity.NEUTRAL else 0.62,
        confidence=answer_signal.confidence,
        assertion_hint=AssertionLevel.WEAK_CANDIDATE,
        evidence_refs=[
            answer_signal.signal_id,
            hidden_update.update_id,
            result.training_label.event_id,
            result.local_overlay.overlay_id,
            *answer_signal.evidence_refs[:4],
        ],
        trainable_targets=[
            trainable_probe_ref,
            f"hidden_factor.{hidden_update.attribute_key}",
            "signal_weight.reality_probe.hidden_attribute",
        ],
    )


def _rank_focus_topics(
    *,
    verdicts: list[DecisionVerdict],
    branches: list[BranchCandidate],
    signals: list[RuntimeSignal],
) -> list[tuple[Topic, float]]:
    topics = _candidate_topics(verdicts)
    ranked: list[tuple[Topic, float]] = []
    for topic in topics:
        topic_verdicts = [verdict for verdict in verdicts if verdict.topic == topic]
        topic_branches = [branch for branch in branches if branch.topic == topic]
        topic_signals = [signal for signal in signals if signal.topic in {topic, Topic.HIDDEN_ATTRIBUTE}]
        gain = _information_gain(topic_verdicts=topic_verdicts, topic_branches=topic_branches, topic_signals=topic_signals)
        ranked.append((topic, gain))
    return sorted(ranked, key=lambda row: (row[1], -_topic_rank(row[0])), reverse=True)


def _candidate_topics(verdicts: list[DecisionVerdict]) -> list[Topic]:
    topics = [verdict.topic for verdict in verdicts if verdict.topic not in {Topic.OVERVIEW, Topic.UNKNOWN}]
    if not topics:
        return [Topic.HIDDEN_ATTRIBUTE]
    ordered = sorted(_unique_topics(topics), key=_topic_rank)
    return ordered


def _topic_rank(topic: Topic) -> int:
    try:
        return DOMAIN_PRIORITY.index(topic)
    except ValueError:
        return len(DOMAIN_PRIORITY)


def _information_gain(
    *,
    topic_verdicts: list[DecisionVerdict],
    topic_branches: list[BranchCandidate],
    topic_signals: list[RuntimeSignal],
) -> float:
    base = 0.42
    if not topic_verdicts:
        return base
    confidence_gap = max(0.0, 0.70 - max(verdict.confidence for verdict in topic_verdicts))
    base += confidence_gap * 0.42
    if any(verdict.assertion_level in {AssertionLevel.MIXED, AssertionLevel.WEAK_CANDIDATE} for verdict in topic_verdicts):
        base += 0.10
    if any(verdict.counter_evidence_refs for verdict in topic_verdicts):
        base += 0.08
    if topic_branches:
        ranked = sorted(topic_branches, key=lambda branch: branch.probability, reverse=True)
        top = ranked[0].probability
        second = ranked[1].probability if len(ranked) > 1 else 0.0
        if top - second <= 0.12:
            base += 0.10
        if any(branch.needs_probe or branch.counter_evidence_refs for branch in topic_branches):
            base += 0.08
    if any(signal.topic == Topic.HIDDEN_ATTRIBUTE or signal.polarity == Polarity.MIXED for signal in topic_signals):
        base += 0.06
    return round(max(0.42, min(0.86, base)), 2)


def _hidden_factor_question(topic: Topic) -> str:
    table = {
        Topic.CAREER: "事业判断里有没有一条反复出现的暗线：职责变化、平台资源，还是总想换方向？",
        Topic.WEALTH: "财务判断里有没有一条反复出现的暗线：收入波动、分配压力，还是项目资源反复？",
        Topic.RELATIONSHIP: "关系判断里有没有一条反复出现的暗线：表达冲突、距离边界，还是承诺节奏？",
        Topic.HEALTH: "身心状态里有没有一条反复出现的暗线：压力消耗、作息失衡，还是身体反馈？",
        Topic.TIMING: "最近几年里，有没有某类事件反复出现，影响当前大运流年的判断？",
        Topic.USEFUL_GOD: "用神候选里，现实中更反复验证的是被支持、被消耗，还是承压后转化？",
        Topic.FAMILY: "家庭关系里有没有一条反复出现的暗线：责任牵引、资源支持，还是边界压力？",
        Topic.HIDDEN_ATTRIBUTE: "是否有反复出现但命盘表层不容易直接解释的经历？",
    }
    return table.get(topic, "有没有一条反复出现的现实线索，可以帮助校准这次判断？")


def _hidden_factor_options(topic: Topic) -> list[str]:
    table = {
        Topic.CAREER: ["职责反复", "平台资源反复", "总想换方向", "暂不明显"],
        Topic.WEALTH: ["收入波动", "分配压力", "项目资源反复", "暂不明显"],
        Topic.RELATIONSHIP: ["表达冲突", "距离边界", "承诺节奏", "暂不明显"],
        Topic.HEALTH: ["压力消耗", "作息失衡", "身体反馈", "暂不明显"],
        Topic.TIMING: ["事业触发", "财务触发", "关系触发", "健康节奏", "暂不明显"],
        Topic.USEFUL_GOD: ["被支持更明显", "被消耗更明显", "承压后转化", "暂不明显"],
        Topic.FAMILY: ["责任牵引", "资源支持", "边界压力", "暂不明显"],
        Topic.HIDDEN_ATTRIBUTE: ["反复经历明显", "偶尔出现", "暂时没有", "不确定"],
    }
    return table.get(topic, ["反复明显", "偶尔出现", "暂不明显", "不确定"])


def _hidden_factor_impact_preview(topic: Topic) -> list[str]:
    label = _topic_label(topic)
    return [
        f"会把{label}判断里的暗线转成可训练的现实校准信号。",
        "会影响后续对话先问哪一类问题，但不直接改命盘事实。",
        "会帮助命理师区分主分支、备选分支和需要继续追问的分支。",
    ]


def _topic_label(topic: Topic) -> str:
    return {
        Topic.CAREER: "事业",
        Topic.WEALTH: "财务",
        Topic.RELATIONSHIP: "关系",
        Topic.HEALTH: "健康",
        Topic.TIMING: "时运",
        Topic.USEFUL_GOD: "用神",
        Topic.FAMILY: "家庭",
        Topic.HIDDEN_ATTRIBUTE: "隐藏线索",
    }.get(topic, "命局")


def _unique_topics(rows: list[Topic]) -> list[Topic]:
    result: list[Topic] = []
    for row in rows:
        if row not in result:
            result.append(row)
    return result
