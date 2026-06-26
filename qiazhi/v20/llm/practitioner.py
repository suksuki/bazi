from __future__ import annotations

import json
from dataclasses import replace

from v20.answer.plan import AnswerPlan
from v20.llm.client import call_structured_llm, stream_plain_llm_text
from v20.llm.contracts import PRACTITIONER_ANSWER
from v20.llm.prompts import practitioner_answer_prompt
from v20.llm.provider import load_llm_provider_config_from_env
from v20.llm.validators import validate_llm_output, validate_llm_structured_output


def build_practitioner_answer_with_llm(
    *,
    chart_facts: dict[str, object],
    time_context: dict[str, object],
    selected_question: dict[str, object],
    knowledge_semantic_model: dict[str, object],
    answer_plan: AnswerPlan,
    deterministic_answer_text: str,
    decision_report: dict[str, object] | None = None,
    portrait_projection: dict[str, object] | None = None,
    feature_state_model: dict[str, object] | None = None,
    question_intent_model: dict[str, object] | None = None,
    interaction_session: dict[str, object] | None = None,
    mainline_arbitration: dict[str, object] | None = None,
    brain_state: dict[str, object] | None = None,
    locale: str = "zh",
) -> dict[str, object]:
    prompt = practitioner_answer_prompt(
        chart_facts=chart_facts,
        time_context=time_context,
        selected_question=selected_question,
        decision_report=decision_report or {},
        knowledge_semantic_model=knowledge_semantic_model,
        portrait_projection=portrait_projection or {},
        feature_state_model=feature_state_model or {},
        question_intent_model=question_intent_model or {},
        interaction_session=interaction_session or {},
        mainline_arbitration=mainline_arbitration or {},
        brain_state=brain_state or {},
        answer_plan=answer_plan,
        verified_answer_text=deterministic_answer_text,
        locale=locale,
    )
    cfg = load_llm_provider_config_from_env()
    provider = "ollama_native" if cfg.provider == "ollama" else cfg.provider
    prompt_metrics = {
        "context_version": prompt.get("context_version", ""),
        "prompt_char_count": len(json.dumps(prompt, ensure_ascii=False, sort_keys=True)),
        "mode": "compact_answer_card",
    }
    fallback_text = compact_practitioner_fallback_text(prompt, deterministic_answer_text)
    call = call_structured_llm(
        PRACTITIONER_ANSWER,
        prompt,
        config=replace(
            cfg,
            provider=provider,
            max_tokens=min(max(cfg.max_tokens, 360), 480),
            temperature=min(cfg.temperature, 0.3),
            http_timeout_sec=min(max(cfg.http_timeout_sec, 24.0), 28.0),
        ),
    )
    if call["status"] == "accepted":
        output = call.get("output", {})
        accepted = accept_or_fallback_practitioner_answer(
            output,
            fallback_text,
            expected_day_master=str(chart_facts.get("day_master", "")),
        )
        if accepted["ok"]:
            return {
                "version": "v20.llm_practitioner_answer.v1",
                "status": "accepted",
                "text": accepted["text"],
                "source": "llm_practitioner_answer",
                "structured_output": output,
                "llm_call": call,
                "prompt_metrics": prompt_metrics,
                "validation": accepted["validation"],
                "runtime_mutation": False,
                "guardrails": [
                    "LLM_ACTS_AS_EVIDENCE_BOUNDED_PRACTITIONER",
                    "VERIFIED_CONTEXT_IS_SOURCE_OF_TRUTH",
                    "DETERMINISTIC_VALIDATOR_FINAL",
                    "FALLBACK_ON_CONTRACT_FAILURE",
                ],
            }
    return {
        "version": "v20.llm_practitioner_answer.v1",
        "status": "fallback",
        "text": fallback_text,
        "source": "deterministic_fallback",
        "structured_output": {},
        "llm_call": call,
        "prompt_metrics": prompt_metrics,
        "validation": call.get("validation", {}),
        "runtime_mutation": False,
        "guardrails": [
            "LLM_PRACTITIONER_ANSWER_NOT_PUBLISHED",
            "DETERMINISTIC_ANSWER_USED",
            "NO_FACT_OR_RULE_MUTATION",
        ],
    }


def stream_practitioner_answer_with_llm(
    *,
    chart_facts: dict[str, object],
    time_context: dict[str, object],
    selected_question: dict[str, object],
    knowledge_semantic_model: dict[str, object],
    answer_plan: object,
    deterministic_answer_text: str,
    decision_report: dict[str, object] | None = None,
    portrait_projection: dict[str, object] | None = None,
    feature_state_model: dict[str, object] | None = None,
    question_intent_model: dict[str, object] | None = None,
    interaction_session: dict[str, object] | None = None,
    mainline_arbitration: dict[str, object] | None = None,
    brain_state: dict[str, object] | None = None,
    locale: str = "zh",
):
    prompt = practitioner_answer_prompt(
        chart_facts=chart_facts,
        time_context=time_context,
        selected_question=selected_question,
        decision_report=decision_report or {},
        knowledge_semantic_model=knowledge_semantic_model,
        portrait_projection=portrait_projection or {},
        feature_state_model=feature_state_model or {},
        question_intent_model=question_intent_model or {},
        interaction_session=interaction_session or {},
        mainline_arbitration=mainline_arbitration or {},
        brain_state=brain_state or {},
        answer_plan=answer_plan,  # type: ignore[arg-type]
        verified_answer_text=deterministic_answer_text,
        locale=locale,
    )
    fallback_text = compact_practitioner_fallback_text(prompt, deterministic_answer_text)
    cfg = load_llm_provider_config_from_env()
    provider = "ollama_native" if cfg.provider == "ollama" else cfg.provider
    emitted = False
    try:
        for chunk in stream_plain_llm_text(
            PRACTITIONER_ANSWER,
            prompt,
            config=replace(
                cfg,
                provider=provider,
                max_tokens=min(max(cfg.max_tokens, 360), 480),
                temperature=min(cfg.temperature, 0.3),
                http_timeout_sec=min(max(cfg.http_timeout_sec, 24.0), 30.0),
            ),
        ):
            emitted = True
            yield str(chunk)
    except Exception:
        if emitted:
            return
    if not emitted:
        yield fallback_text


def unwrap_practitioner_text(value: str) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        payload = None
    if isinstance(payload, dict) and isinstance(payload.get("text"), str):
        return payload["text"].strip()
    if text.startswith('{"text"') or text.startswith("{'text'"):
        start = text.find(":")
        if start > -1:
            candidate = text[start + 1 :].strip()
            if candidate.endswith("}"):
                candidate = candidate[:-1].strip()
            return candidate.strip().strip('"').strip("'")
    return text


def compact_practitioner_fallback_text(prompt: dict[str, object], deterministic_answer_text: str) -> str:
    context = prompt.get("context", {})
    if not isinstance(context, dict):
        return deterministic_answer_text
    question = context.get("question", {})
    chart = context.get("chart", {})
    mainline = context.get("mainline", [])
    portrait_tags = context.get("portrait_tags", [])
    evidence = context.get("evidence", [])
    next_questions = context.get("next_questions", [])
    boundary = str(context.get("answer_boundary") or "只按当前八字结构回答，不作固定吉凶或具体事件断语。")
    locale = str(prompt.get("locale") or "zh")

    if not isinstance(question, dict) or not isinstance(chart, dict):
        return deterministic_answer_text
    title = str(question.get("title") or question.get("measurement_topic") or "这个问题")
    day_master = str(chart.get("day_master") or "")
    main = _first_label(mainline, "label") or _first_label(portrait_tags, "label") or str(question.get("measurement_topic") or "当前主题")
    strategy = context.get("answer_strategy", {})
    strategy_line = _strategy_line(strategy if isinstance(strategy, dict) else {}, locale=locale)
    support = "、".join(_string_items(evidence, 3))
    follow = _string_items(next_questions, 1)

    if locale.startswith("en"):
        text = (
            f"For {title}, the first reading is {main}. "
            f"With day master {day_master or '-'}, the visible evidence is {support or 'the current verified chart structure'}. "
            f"So this should be read as a structural tendency, not a fixed event. {strategy_line}"
        )
        if follow:
            text += f" A useful next question is: {follow[0]}"
        return _clip_local(text, 620)
    if locale.startswith("ko"):
        text = (
            f"{title}은 먼저 {main}로 봅니다. "
            f"일간 {day_master or '-'} 기준으로 확인된 근거는 {support or '현재 검증된 명식 구조'}입니다. "
            f"따라서 확정 사건이 아니라 구조적 경향으로 해석하는 것이 좋습니다. {strategy_line}"
        )
        if follow:
            text += f" 다음 질문은 {follow[0]}입니다."
        return _clip_local(text, 420)

    text = (
        f"{title}先看「{main}」。"
        f"这个盘日主{day_master or '已定'}，当前能抓到的关键证据是：{support or '四柱结构、十神关系和主题画像已经形成主线'}。"
        f"所以这里先按结构倾向来断，不把它说成固定事件。{strategy_line}{_clip_local(boundary, 90)}"
    )
    if follow:
        text += f" 下一步适合追问：{follow[0]}"
    return _clip_local(text, 420)


def _strategy_line(strategy: dict[str, object], *, locale: str) -> str:
    mode = str(strategy.get("mode", ""))
    if not mode:
        return ""
    if locale.startswith("en"):
        if mode == "confirmed_by_practitioner":
            return "The mainline is practitioner-confirmed for this session. "
        if bool(strategy.get("requires_review")):
            return "The mainline remains provisional and needs review. "
        return ""
    if locale.startswith("ko"):
        if mode == "confirmed_by_practitioner":
            return "이번 세션에서는 명리사가 이 주선을 확인했습니다. "
        if bool(strategy.get("requires_review")):
            return "이 주선은 아직 후보이며 검토가 필요합니다. "
        return ""
    if mode == "confirmed_by_practitioner":
        return "本轮主线已经命理师确认。"
    if mode == "practitioner_switched_needs_review":
        return "本轮已按命理师选择切换主线，但仍保留复核边界。"
    if mode == "evidence_gap_review":
        return "本轮主线证据不足，先看缺口和可验证方向。"
    if bool(strategy.get("requires_review")):
        return "本轮主线仍是候选，需要保留复核边界。"
    return ""


def accept_or_fallback_practitioner_answer(
    candidate_payload: dict[str, object],
    deterministic_answer_text: str,
    *,
    expected_day_master: str = "",
) -> dict[str, object]:
    structured_validation = validate_llm_structured_output(PRACTITIONER_ANSWER, candidate_payload)
    text = str(candidate_payload.get("text") or "")
    text = unwrap_practitioner_text(text)
    text_validation = validate_llm_output(PRACTITIONER_ANSWER, text)
    failures = [
        *structured_validation.get("failures", ()),
        *text_validation.get("failures", ()),
        *_day_master_fact_failures(text, expected_day_master),
    ]
    validation = {
        "ok": not failures,
        "task_name": PRACTITIONER_ANSWER.task_name,
        "failures": failures,
        "structured_validation": structured_validation,
        "text_validation": text_validation,
        "fallback": PRACTITIONER_ANSWER.fallback if failures else "",
        "guardrails": [
            "PRACTITIONER_ANSWER_STRUCTURED_AND_TEXT_VALIDATED",
            "DAY_MASTER_FACT_VALIDATED_AGAINST_CHART_FACTS",
            "DETERMINISTIC_FALLBACK_ON_FAILURE",
        ],
    }
    if validation["ok"]:
        return {"ok": True, "text": text, "validation": validation, "source": "llm_practitioner_answer"}
    return {
        "ok": False,
        "text": deterministic_answer_text,
        "validation": validation,
        "source": "deterministic_fallback",
    }


def validate_practitioner_answer_day_master(text: str, expected_day_master: str) -> dict[str, object]:
    failures = _day_master_fact_failures(text, expected_day_master)
    return {
        "version": "v20.practitioner_answer_day_master_validation.v1",
        "ok": not failures,
        "expected_day_master": expected_day_master,
        "failures": failures,
        "runtime_mutation": False,
        "guardrails": [
            "DAY_MASTER_IS_IMMUTABLE_CHART_FACT",
            "WRONG_DAY_MASTER_FORCES_DETERMINISTIC_FALLBACK",
        ],
    }


def _day_master_fact_failures(text: str, expected_day_master: str) -> list[str]:
    expected = str(expected_day_master or "").strip()
    if not expected:
        return []
    stems = ("甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸")
    wrong = [stem for stem in stems if stem != expected]
    value = str(text or "")
    failures: list[str] = []
    for stem in wrong:
        patterns = (
            f"{stem}木日主",
            f"{stem}火日主",
            f"{stem}土日主",
            f"{stem}金日主",
            f"{stem}水日主",
            f"日主{stem}",
            f"日主为{stem}",
            f"日主是{stem}",
            f"{stem}日主",
        )
        if any(pattern in value for pattern in patterns):
            failures.append(f"day_master_mismatch:{stem}_mentioned_expected_{expected}")
    return failures


def _first_label(rows: object, key: str) -> str:
    if not isinstance(rows, (list, tuple)):
        return ""
    for row in rows:
        if isinstance(row, dict) and row.get(key):
            return str(row.get(key))
    return ""


def _string_items(rows: object, limit: int) -> list[str]:
    if not isinstance(rows, (list, tuple)):
        return []
    return [str(item) for item in rows if item][:limit]


def _clip_local(value: str, limit: int) -> str:
    text = str(value or "").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"
