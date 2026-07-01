from __future__ import annotations

from v40.contracts.base import Polarity, RoleKey, Topic
from v40.contracts.decision import ProbeCandidate
from v40.contracts.probe import AnswerSignal, HiddenAttributeUpdate, ProbeAnswerResult
from v40.contracts.runtime import RuntimeResult
from v40.contracts.training import LabelSource, LabelTargetType, LabelValue, LocalOverlay, TrainingLabelEvent


def build_probe_answer_result(
    *,
    answer_id: str,
    runtime: RuntimeResult,
    probe_id: str = "",
    answer_text: str = "",
    selected_option: str = "",
    mismatch_area: str = "",
    created_by_role: RoleKey = "user",
) -> ProbeAnswerResult:
    clean_answer_id = answer_id.strip()
    if not clean_answer_id:
        raise ValueError("Probe answer requires answer_id")
    clean_answer = (selected_option or answer_text).strip()
    if not clean_answer:
        raise ValueError("Probe answer requires selected_option or answer_text")
    if created_by_role not in {"guest", "user", "practitioner"}:
        raise ValueError("Probe answer requires guest, user, or practitioner role")

    probe = _find_probe(runtime, probe_id)
    topic = probe.topic if probe else _fallback_topic(runtime, mismatch_area)
    question = probe.question if probe else _fallback_question(mismatch_area, topic)
    target_verdict_ids = _target_verdict_ids(runtime=runtime, probe=probe, topic=topic)
    target_branch_ids = probe.target_branch_ids if probe else []
    target_ids = [*target_verdict_ids, *target_branch_ids]
    interpreted_claim = _interpreted_claim(topic=topic, answer=clean_answer, mismatch_area=mismatch_area)
    confidence = _answer_confidence(clean_answer)

    answer_signal = AnswerSignal(
        signal_id=f"answer_signal:{clean_answer_id}",
        reading_id=runtime.reading_id,
        probe_id=probe.probe_id if probe else "",
        topic=topic,
        question=question,
        answer_text=clean_answer,
        selected_option=selected_option.strip(),
        interpreted_claim=interpreted_claim,
        polarity=Polarity.NEUTRAL if _is_uncertain(clean_answer) else Polarity.SUPPORT,
        supports_target_ids=target_ids if not _is_uncertain(clean_answer) else [],
        weakens_target_ids=target_verdict_ids if _is_mismatch(mismatch_area) else [],
        confidence=confidence,
        evidence_refs=[
            f"runtime:{runtime.reading_id}",
            *(target_ids[:6]),
        ],
    )
    hidden_update = HiddenAttributeUpdate(
        update_id=f"hidden_attribute:{clean_answer_id}",
        reading_id=runtime.reading_id,
        probe_id=probe.probe_id if probe else "",
        answer_signal_id=answer_signal.signal_id,
        topic=topic if topic != Topic.UNKNOWN else Topic.HIDDEN_ATTRIBUTE,
        attribute_key=_attribute_key(topic, mismatch_area),
        value=clean_answer,
        confidence=confidence,
        evidence_refs=[answer_signal.signal_id, *target_ids[:4]],
    )
    label = TrainingLabelEvent(
        event_id=f"label:probe_answer:{clean_answer_id}",
        reading_id=runtime.reading_id,
        source=LabelSource.PROBE_ANSWER,
        target_type=LabelTargetType.PROBE if probe else LabelTargetType.HIDDEN_ATTRIBUTE,
        target_ids=[probe.probe_id] if probe else [hidden_update.update_id],
        label=LabelValue.NEEDS_PROBE if _is_uncertain(clean_answer) else LabelValue.PROBE_HELPFUL,
        also_supports=target_ids if not _is_uncertain(clean_answer) else [],
        weakens=target_verdict_ids if _is_mismatch(mismatch_area) else [],
        affected_trainable_refs=[f"probe_voi.{probe.probe_id}"] if probe else ["probe_voi.recovery"],
        strength=0.54 if _is_uncertain(clean_answer) else 0.70,
        confidence=confidence,
        reason=_label_reason(topic=topic, answer=clean_answer, mismatch_area=mismatch_area),
        evidence_refs=[answer_signal.signal_id, hidden_update.update_id, *target_ids[:4]],
        created_by_role=created_by_role,
        local_only=True,
        chart_fact_mutation_allowed=False,
    )
    overlay = LocalOverlay(
        overlay_id=f"overlay:probe_answer:{clean_answer_id}",
        reading_id=runtime.reading_id,
        label_event_ids=[label.event_id],
        affected_target_ids=[answer_signal.signal_id, hidden_update.update_id, *target_ids],
        expires_after_reading=True,
        global_update_allowed=False,
    )
    refined_advice = _refined_advice(runtime=runtime, topic=topic, answer=clean_answer, claim=interpreted_claim)
    return ProbeAnswerResult(
        result_id=f"probe_answer:{clean_answer_id}",
        reading_id=runtime.reading_id,
        answer_signal=answer_signal,
        hidden_attribute_update=hidden_update,
        training_label=label,
        local_overlay=overlay,
        refined_advice_points=refined_advice,
        user_message=_user_message(topic=topic, answer=clean_answer),
        changes_verdict=False,
        changes_chart_facts=False,
        writes_v40_production=False,
        writes_v30_state=False,
    )


def _find_probe(runtime: RuntimeResult, probe_id: str) -> ProbeCandidate | None:
    clean_probe_id = probe_id.strip()
    if not clean_probe_id:
        return None
    for probe in runtime.probes:
        if probe.probe_id == clean_probe_id:
            return probe
    raise ValueError("Probe answer references unknown probe_id")


def _fallback_topic(runtime: RuntimeResult, mismatch_area: str) -> Topic:
    area = mismatch_area.strip()
    if "财" in area:
        return Topic.WEALTH
    if "事业" in area:
        return Topic.CAREER
    if "感情" in area or "关系" in area:
        return Topic.RELATIONSHIP
    if runtime.verdicts:
        return runtime.verdicts[0].topic
    return runtime.request.topic


def _fallback_question(mismatch_area: str, topic: Topic) -> str:
    clean_area = mismatch_area.strip()
    if clean_area:
        return f"哪里不太像：{clean_area}？"
    return f"这个{_topic_label(topic)}判断哪里需要校准？"


def _target_verdict_ids(*, runtime: RuntimeResult, probe: ProbeCandidate | None, topic: Topic) -> list[str]:
    if probe and probe.target_verdict_ids:
        return list(probe.target_verdict_ids)
    return [verdict.verdict_id for verdict in runtime.verdicts if verdict.topic == topic][:2] or [
        verdict.verdict_id for verdict in runtime.verdicts[:1]
    ]


def _interpreted_claim(*, topic: Topic, answer: str, mismatch_area: str) -> str:
    area = mismatch_area.strip()
    prefix = f"{_topic_label(topic)}校准线索"
    if area:
        prefix = f"{prefix}（{area}）"
    if _is_uncertain(answer):
        return f"{prefix}暂不确定，当前判断应保留边界，等待更多现实反馈。"
    return f"{prefix}更偏向「{answer}」，本次建议应围绕这个现实线索收束。"


def _attribute_key(topic: Topic, mismatch_area: str) -> str:
    suffix = "reality_signal"
    area = mismatch_area.strip()
    if "财" in area:
        suffix = "money_mode"
    elif "事业" in area:
        suffix = "career_direction"
    elif "感情" in area or "关系" in area:
        suffix = "relationship_pattern"
    elif area:
        suffix = "mismatch_area"
    topic_key = topic.value if isinstance(topic, Topic) else str(topic)
    return f"{topic_key}.{suffix}"


def _answer_confidence(answer: str) -> float:
    if _is_uncertain(answer):
        return 0.42
    if len(answer.strip()) >= 2:
        return 0.68
    return 0.56


def _label_reason(*, topic: Topic, answer: str, mismatch_area: str) -> str:
    claim = _interpreted_claim(topic=topic, answer=answer, mismatch_area=mismatch_area)
    return f"用户回答 Probe 后形成现实校准线索：{claim}"


def _refined_advice(*, runtime: RuntimeResult, topic: Topic, answer: str, claim: str) -> list[str]:
    base_advice = next((advice for advice in runtime.advice_plans if advice.topic == topic), None)
    lines = [f"已按「{answer}」校准：{claim}"]
    if base_advice and base_advice.action_points:
        lines.append(f"原建议保留，但优先落在：{base_advice.action_points[0]}")
    if topic == Topic.CAREER:
        lines.append("下一步先把职责、平台和转型意愿拆开判断，不把岗位变化直接当成突破。")
    elif topic == Topic.WEALTH:
        lines.append("下一步先区分固定收入、项目客户、合伙分配和投资波动，避免把所有财运混成一个结论。")
    elif topic == Topic.RELATIONSHIP:
        lines.append("下一步先看表达冲突、距离边界和承诺节奏，不把单一事件当成关系定性。")
    elif topic == Topic.HEALTH:
        lines.append("下一步先把压力消耗、作息节奏和身体反馈分开看，建议只做提醒不做医疗判断。")
    else:
        lines.append("下一步保留这条现实线索，在后续对话和训练回放中继续校准。")
    return lines


def _user_message(*, topic: Topic, answer: str) -> str:
    if _is_uncertain(answer):
        return f"已记录：{_topic_label(topic)}线索暂不确定，本次判断会保留边界。"
    return f"已校准：{_topic_label(topic)}判断会更贴近「{answer}」。"


def _topic_label(topic: Topic) -> str:
    return {
        Topic.CAREER: "事业",
        Topic.WEALTH: "财富",
        Topic.RELATIONSHIP: "关系",
        Topic.HEALTH: "健康",
        Topic.TIMING: "时运",
        Topic.USEFUL_GOD: "用神",
        Topic.OVERVIEW: "综合",
    }.get(topic, "命盘")


def _is_uncertain(answer: str) -> bool:
    return answer.strip() in {"暂不确定", "不确定", "还不确定", "先不确定"}


def _is_mismatch(mismatch_area: str) -> bool:
    return bool(mismatch_area.strip())
