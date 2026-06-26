from __future__ import annotations

import re
from dataclasses import replace

from v20.answer.measurement_policy import domain_label
from v20.interaction.questions import QuestionCandidate
from v20.measurement.domain_alignment import align_question_candidate


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
    filtered: list[QuestionCandidate] = []
    suppressed: list[str] = []

    for row in normalized:
        if _is_answered(row, selected, memory):
            suppressed.append(row.question_id or row.question_key)
            continue
        if _signature(row) in {_signature(item) for item in filtered}:
            continue
        filtered.append(_aligned(row))
        if len(filtered) >= limit:
            break

    report = {
        "version": QUESTION_AGENT_MODEL_VERSION,
        "status": "ready",
        "algorithm": "answered_question_memory_suppression_only_anchor_refactor",
        "answered_question_id_count": len(memory["ids"]),
        "answered_question_key_count": len(memory["keys"]),
        "suppressed_question_count": len(tuple(dict.fromkeys(suppressed))),
        "generated_followup_count": 0,
        "selected_question_id": selected.question_id or selected.question_key,
        "selected_question_key": selected.question_key,
        "next_question_count": len(filtered),
        "runtime_mutation": False,
        "guardrails": (
            "ANSWERED_QUESTIONS_ARE_SUPPRESSED_FROM_NEXT_LIST",
            "QUESTION_AGENT_DOES_NOT_GENERATE_DISPLAY_QUESTIONS",
            "FOLLOWUPS_ARE_HANDLED_BY_QUESTION_ATOMS_DAG_AND_BAZI_ANCHOR",
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
    return f"{domain_label(domain)}问题需要回到当前八字主线继续确认？"


def _signature(question: QuestionCandidate) -> str:
    return "|".join(
        (
            str(question.question_key),
            str(question.domain),
            _compact(question.title)[:32],
        )
    )


def _compact(value: str) -> str:
    return re.sub(r"[\s，。；;：:！？?（）()\"'“”]+", "", str(value or ""))
