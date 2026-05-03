from __future__ import annotations

import hashlib
import re
from dataclasses import replace
from typing import Any

from v20.answer.measurement_policy import domain_label, measurement_stage
from v20.interaction.questions import QuestionCandidate
from v20.measurement.domain_alignment import align_question_candidate
from v20.measurement.dimensions import dimension_payload


QUESTION_AGENT_MODEL_VERSION = "v20.question_agent_state.v1"


def apply_question_agent_state(
    questions: tuple[QuestionCandidate, ...],
    selected_question: QuestionCandidate,
    *,
    answered_question_ids: tuple[str, ...] = (),
    answered_question_keys: tuple[str, ...] = (),
    limit: int = 12,
) -> tuple[tuple[QuestionCandidate, ...], dict[str, object]]:
    memory = _memory(answered_question_ids, answered_question_keys)
    normalized = tuple(_humanized(row) for row in questions)
    selected = _humanized(selected_question)
    has_answered_memory = bool(memory["ids"] or memory["keys"])
    followups = _followup_questions(selected) if has_answered_memory else ()
    filtered: list[QuestionCandidate] = []
    suppressed: list[str] = []

    for row in (*followups, *normalized):
        if _is_answered(row, selected, memory):
            suppressed.append(row.question_id or row.question_key)
            continue
        if _signature(row) in {_signature(item) for item in filtered}:
            continue
        filtered.append(_aligned(row))
        if len(filtered) >= limit:
            break

    if not filtered:
        filtered = [_aligned(_fallback_followup(selected))]

    report = {
        "version": QUESTION_AGENT_MODEL_VERSION,
        "status": "ready",
        "algorithm": "answered_question_memory_plus_followup_refresh_phase1",
        "answered_question_id_count": len(memory["ids"]),
        "answered_question_key_count": len(memory["keys"]),
        "suppressed_question_count": len(tuple(dict.fromkeys(suppressed))),
        "generated_followup_count": len(followups),
        "selected_question_id": selected.question_id or selected.question_key,
        "selected_question_key": selected.question_key,
        "next_question_count": len(filtered),
        "runtime_mutation": False,
        "guardrails": (
            "ANSWERED_QUESTIONS_ARE_SUPPRESSED_FROM_NEXT_LIST",
            "QUESTION_AGENT_REFRESHES_QUEUE_AFTER_EACH_ANSWER",
            "FOLLOWUPS_USE_SELECTED_DOMAIN_AND_FEATURE_CONTEXT",
            "NO_RULE_OR_FACT_MUTATION",
        ),
    }
    return tuple(filtered[:limit]), report


def _memory(answered_question_ids: tuple[str, ...], answered_question_keys: tuple[str, ...]) -> dict[str, set[str]]:
    return {
        "ids": {str(row).strip() for row in answered_question_ids if str(row).strip()},
        "keys": {str(row).strip() for row in answered_question_keys if str(row).strip()},
    }


def _is_answered(
    question: QuestionCandidate,
    selected_question: QuestionCandidate,
    memory: dict[str, set[str]],
) -> bool:
    qid = str(question.question_id or question.question_key)
    key = str(question.question_key)
    selected_id = str(selected_question.question_id or selected_question.question_key)
    selected_key = str(selected_question.question_key)
    if qid in memory["ids"] or key in memory["keys"]:
        return True
    if selected_id in memory["ids"] and qid == selected_id:
        return True
    if selected_key in memory["keys"] and key == selected_key:
        return True
    return False


def _followup_questions(selected_question: QuestionCandidate) -> tuple[QuestionCandidate, ...]:
    templates = _domain_followup_templates(selected_question.domain)
    rows: list[QuestionCandidate] = []
    for index, title in enumerate(templates[:3]):
        rows.append(
            QuestionCandidate(
                question_key=selected_question.question_key,
                title=title,
                domain=selected_question.domain,
                score=round(max(0.35, float(selected_question.score or 0.0) - 0.04 - index * 0.025), 3),
                source_feature_ids=tuple(selected_question.source_feature_ids),
                boundary=selected_question.boundary,
                measurement_topic=domain_label(selected_question.domain),
                measurement_stage=measurement_stage(selected_question.domain),
                question_id=_agent_question_id(selected_question, title, index),
                source_decision_key=selected_question.source_decision_key,
                source_rule_key=selected_question.source_rule_key,
                source_decision_status=selected_question.source_decision_status,
                source_decision_label=selected_question.source_decision_label,
                question_strategy="agent_followup",
                **dimension_payload(selected_question.domain),
            )
        )
    return tuple(rows)


def _aligned(question: QuestionCandidate) -> QuestionCandidate:
    if question.alignment_status in {"bazi_core_aligned", "bazi_projection_aligned"} and question.bazi_focus:
        return question
    alignment = align_question_candidate(
        question_key=question.question_key,
        domain=question.domain,
        title=question.title,
        source_feature_ids=question.source_feature_ids,
        boundary=question.boundary,
    )
    if not alignment.ok:
        return replace(
            question,
            alignment_status="bazi_projection_aligned",
            bazi_focus=f"{domain_label(question.domain)}问题用于继续追问八字结构。",
            alignment_score=max(float(question.alignment_score or 0.0), 0.72),
        )
    return replace(
        question,
        alignment_status=alignment.status,
        bazi_focus=alignment.focus,
        alignment_score=alignment.score,
    )


def _domain_followup_templates(domain: str) -> tuple[str, ...]:
    if domain == "wealth":
        return (
            "这盘的财运，是机会更强，还是承接压力更关键？",
            "财星出现后，钱是靠主动开拓、合作关系，还是阶段性时运带出来？",
            "如果只看下一步，财务上更该先稳现金流还是放大机会？",
        )
    if domain == "career":
        return (
            "这盘事业主线里，规则压力、个人表达和平台资源谁更主导？",
            "工作上更适合走稳定职位、专业输出，还是项目型突破？",
            "事业冲突出现时，是该先化解压力，还是先放大个人能力？",
        )
    if domain == "relationship":
        return (
            "关系里更核心的是互动方式、现实承接，还是冲突边界？",
            "伴侣或合作关系对这个盘，是助力更明显还是牵制更明显？",
            "如果继续看感情，先看相处模式还是关系稳定性？",
        )
    if domain == "time":
        return (
            "当前大运流年先牵动的是事业、财运，还是关系？",
            "岁运触发后，是机会被放大，还是压力先被放大？",
            "接下来更该看大运主轴，还是流年具体触发点？",
        )
    if domain == "strength":
        return (
            "日主承载上，是扶助更重要，还是泄耗压力更明显？",
            "如果承载不足，先看印星比劫补力，还是看通关路径？",
            "这个盘后续看财官前，要不要先定强弱主轴？",
        )
    if domain == "useful_god":
        return (
            "取用方向里，扶身、泄秀、通关哪条更像主线？",
            "用神候选现在最需要哪类证据来定优先级？",
            "如果不用单一用神，这盘更像哪种调节组合？",
        )
    if domain == "pattern":
        return (
            "格局上先看主轴是否成形，还是先看破局点？",
            "这个盘做功是否连续，关键断点在哪里？",
            "如果格局不纯，应该按哪条机制重新抓主线？",
        )
    if domain == "health":
        return (
            "身心平衡上，先看哪一类五行压力和节律边界？",
            "压力更像长期偏枯，还是阶段性被岁运触发？",
            "继续看健康边界时，先看耗泄、寒热，还是五行失衡？",
        )
    if domain == "branch":
        return (
            "地支关系里，冲、合、刑、害哪条先牵动主线？",
            "这些地支互动更先影响财运、事业，还是关系？",
            "如果只抓一个触发点，应该先拆哪组地支关系？",
        )
    if domain == "element":
        return (
            "五行气势里，偏旺的一端更关键，还是偏弱的一端更关键？",
            "五行失衡会先投射到承载、事业，还是健康边界？",
            "这个盘更需要补短板，还是疏导过旺的一端？",
        )
    return (
        f"{domain_label(domain)}这条线，下一步先看机会、压力还是边界？",
        f"围绕{domain_label(domain)}，哪个证据最值得继续确认？",
        f"{domain_label(domain)}如果继续深入，先看结构主轴还是时间触发？",
    )


def _fallback_followup(selected_question: QuestionCandidate) -> QuestionCandidate:
    title = f"围绕「{_clip(selected_question.title, 18)}」，下一步先看哪条命理主线？"
    return QuestionCandidate(
        question_key=selected_question.question_key or "q_structure_overview",
        title=title,
        domain=selected_question.domain or "branch",
        score=0.42,
        source_feature_ids=tuple(selected_question.source_feature_ids),
        boundary=selected_question.boundary or "只做结构追问，不输出固定吉凶。",
        measurement_topic=domain_label(selected_question.domain or "branch"),
        measurement_stage=measurement_stage(selected_question.domain or "branch"),
        question_id=_agent_question_id(selected_question, title, 99),
        question_strategy="agent_followup",
        **dimension_payload(selected_question.domain or "branch"),
    )


def _humanized(question: QuestionCandidate) -> QuestionCandidate:
    title = _humanize_title(question.title, question.domain)
    if title == question.title:
        return question
    return replace(question, title=title)


def _humanize_title(title: str, domain: str) -> str:
    text = str(title or "").strip()
    text = re.sub(r"先读这条(骨架轴|裁决路径|场景轴|时序轴|结构轴)（[^）]+），", "", text)
    text = text.replace("是否优先先", "是否先")
    text = text.replace("更先观察哪一步", "下一步先看哪里")
    text = text.replace("低置信定向", "先定方向")
    text = text.replace("建议复核", "先定方向")
    text = text.replace("需复核", "先定方向")
    text = re.sub(r"（[^）]*(RuleSpec|规则|条件成立|evidence\.)[^）]*）", "", text)
    parenthetical = re.match(r"^(.+?)？（(.+?)）$", text)
    if parenthetical:
        text = f"{parenthetical.group(2)}下，{parenthetical.group(1)}？"
    if _looks_debug_like(text):
        return _domain_human_question(domain)
    if text and "？" not in text and "?" not in text:
        text = text.rstrip("。；;，,") + "？"
    return text


def _looks_debug_like(text: str) -> bool:
    lowered = str(text or "").lower()
    return any(token in lowered for token in ("rulespec", "rule.", "evidence.", "条件成立", "3/3", "2/3", "1/3"))


def _domain_human_question(domain: str) -> str:
    return _domain_followup_templates(domain)[0]


def _signature(question: QuestionCandidate) -> str:
    return "|".join(
        (
            str(question.question_key),
            str(question.domain),
            _compact(question.title)[:32],
        )
    )


def _agent_question_id(question: QuestionCandidate, title: str, index: int, *, prefix: str = "q_agent") -> str:
    seed = "|".join(
        (
            str(question.question_id or question.question_key),
            str(question.domain),
            str(title),
            str(index),
            prefix,
        )
    )
    digest = hashlib.blake2s(seed.encode("utf-8"), digest_size=5).hexdigest()
    return f"{prefix}.{question.question_key}:{digest}"


def _compact(value: str) -> str:
    return re.sub(r"[\s，。；;：:！？?（）()\"'“”]+", "", str(value or ""))


def _clip(value: str, limit: int) -> str:
    text = str(value or "").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"
