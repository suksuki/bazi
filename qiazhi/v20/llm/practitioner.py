from __future__ import annotations

import json
from dataclasses import replace

from v20.answer.plan import AnswerPlan
from v20.llm.client import call_structured_llm
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
    call = call_structured_llm(
        PRACTITIONER_ANSWER,
        prompt,
        config=replace(
            cfg,
            provider=provider,
            max_tokens=min(max(cfg.max_tokens, 520), 640),
            temperature=min(cfg.temperature, 0.3),
            http_timeout_sec=max(4.0, min(cfg.http_timeout_sec, 12.0)),
        ),
    )
    if call["status"] == "accepted":
        output = call.get("output", {})
        accepted = accept_or_fallback_practitioner_answer(output, deterministic_answer_text)
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
        "text": deterministic_answer_text,
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


def accept_or_fallback_practitioner_answer(
    candidate_payload: dict[str, object],
    deterministic_answer_text: str,
) -> dict[str, object]:
    structured_validation = validate_llm_structured_output(PRACTITIONER_ANSWER, candidate_payload)
    text = str(candidate_payload.get("text") or "")
    text_validation = validate_llm_output(PRACTITIONER_ANSWER, text)
    failures = [
        *structured_validation.get("failures", ()),
        *text_validation.get("failures", ()),
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
