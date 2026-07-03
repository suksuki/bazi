from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any, Iterator

from v30.contracts import AnswerContext, AnswerResult, CoreRuntimeResult
from v30.llm.acceptance import (
    bazi_llm_output_text,
    validate_bazi_llm_output_payload,
    validate_thinking_step_summary_text,
)
from v30.brain.judge import BRAIN_JUDGE_VERSION, judge_llm_derivation_quality
from v30.brain.stage_points import build_stage_point_set, selected_stage_points
from v30.brain.text_options import enrich_stage_point_set_with_text_options
from v30.llm.context import build_llm_role_prompt_context
from v30.llm.drift import check_llm_answer_drift
from v30.llm.prompt_registry import build_bazi_llm_prompt_request, build_thinking_step_prompt_request
from v30.llm.provider import V30LLMProviderConfig, llm_provider_readiness_report, load_v30_llm_provider_config_from_env


def compose_bazi_llm_answer_draft(
    runtime: CoreRuntimeResult,
    answer_context: AnswerContext,
    rule_answer: AnswerResult,
    *,
    reading_surface: dict[str, object] | None = None,
    task_type: str | None = None,
    role_key: str | None = None,
    locale: str | None = None,
    client: str = "web",
    domain: str = "",
    config: V30LLMProviderConfig | None = None,
) -> AnswerResult:
    selected_task = task_type or _bazi_answer_task_type(runtime)
    selected_role = role_key or str(runtime.question_plan.role_key)
    selected_locale = locale or str(runtime.chart_context.locale)
    cfg = config or load_v30_llm_provider_config_from_env()
    if config is None and _llm_sync_mode() != "blocking":
        call = _deferred_call_metadata(
            runtime,
            answer_context,
            rule_answer,
            reading_surface=reading_surface or {},
            task_type=selected_task,
            role_key=selected_role,
            locale=selected_locale,
            client=client,
            domain=domain or _selected_domain(runtime),
            config=cfg,
        )
        return rule_answer.model_copy(
            update={
                "source": "rule_bound_llm_deferred",
                "llm_metadata": call,
            }
        )
    call = call_bazi_llm_answer_draft(
        runtime,
        answer_context,
        rule_answer,
        reading_surface=reading_surface or {},
        task_type=selected_task,
        role_key=selected_role,
        locale=selected_locale,
        client=client,
        domain=domain or _selected_domain(runtime),
        config=cfg,
    )
    if call["status"] != "accepted":
        return rule_answer.model_copy(
            update={
                "source": "rule_bound_fallback",
                "llm_metadata": call,
            }
        )
    return rule_answer.model_copy(
        update={
            "text": str(call["text"]),
            "source": "llm_bazi_answer_draft",
            "llm_metadata": call,
        }
    )


def call_bazi_llm_answer_draft(
    runtime: CoreRuntimeResult,
    answer_context: AnswerContext,
    rule_answer: AnswerResult,
    *,
    reading_surface: dict[str, object],
    task_type: str,
    role_key: str,
    locale: str,
    client: str,
    domain: str,
    config: V30LLMProviderConfig | None = None,
) -> dict[str, object]:
    cfg = config or load_v30_llm_provider_config_from_env()
    try:
        prompt_request = build_bazi_llm_prompt_request(
            runtime,
            task_type=task_type,
            domain=domain,
            role_key=role_key,
            locale=locale,
            client=client,
        )
    except ValueError as exc:
        readiness = llm_provider_readiness_report(cfg)
        product_context_summary = _product_context_pack_summary(reading_surface, task_type=task_type, role_key=role_key)
        return _fallback(
            f"prompt_request_rejected:{type(exc).__name__}",
            readiness,
            prompt_request={},
            task_type=task_type,
            role_key=role_key,
            product_context_summary=product_context_summary,
        )
    readiness = llm_provider_readiness_report(cfg)
    product_context_summary = _product_context_pack_summary(reading_surface, task_type=task_type, role_key=role_key)
    if not readiness["ready_for_connection"]:
        return _fallback(
            "provider_not_ready",
            readiness,
            executed=False,
            prompt_request=prompt_request,
            product_context_summary=product_context_summary,
        )
    if not cfg.execute_llm:
        return _fallback(
            "execute_flag_disabled",
            readiness,
            executed=False,
            prompt_request=prompt_request,
            product_context_summary=product_context_summary,
        )
    prompt_context = build_llm_role_prompt_context(answer_context, role_key=role_key)
    prompt = _bazi_answer_prompt(prompt_request, answer_context, rule_answer, reading_surface)
    try:
        if cfg.provider.lower() == "ollama_native":
            payload = _post_ollama_native_completion_with_thinking(prompt, cfg)
        else:
            payload = _post_chat_completion(prompt, cfg)
    except Exception as exc:
        if cfg.provider.lower() == "ollama":
            try:
                payload = _post_ollama_native_completion(prompt, cfg)
            except Exception as native_exc:
                return _fallback(
                    f"call_failed:{type(exc).__name__};ollama_native_failed:{type(native_exc).__name__}",
                    readiness,
                    prompt_request=prompt_request,
                    product_context_summary=product_context_summary,
                )
        else:
            return _fallback(
                f"call_failed:{type(exc).__name__}",
                readiness,
                prompt_request=prompt_request,
                product_context_summary=product_context_summary,
            )
    payload = payload if isinstance(payload, dict) else {}
    payload = _coerce_bazi_output_schema(payload, prompt_request=prompt_request, rule_answer=rule_answer, domain=domain)
    text = bazi_llm_output_text(payload, task_type)
    drift = check_llm_answer_drift(text, prompt_context)
    acceptance = validate_bazi_llm_output_payload(
        payload,
        prompt_request=prompt_request,
        text=text,
        drift_check=drift.model_dump(mode="json"),
    )
    if not text:
        return _fallback(
            "empty_text",
            readiness,
            executed=True,
            drift=drift.model_dump(mode="json"),
            acceptance=acceptance,
            prompt_request=prompt_request,
            product_context_summary=product_context_summary,
        )
    if not drift.passed:
        return _fallback(
            "drift_check_failed",
            readiness,
            executed=True,
            drift=drift.model_dump(mode="json"),
            acceptance=acceptance,
            text=text,
            prompt_request=prompt_request,
            product_context_summary=product_context_summary,
        )
    if not acceptance["accepted"]:
        return _fallback(
            "output_acceptance_failed",
            readiness,
            executed=True,
            drift=drift.model_dump(mode="json"),
            acceptance=acceptance,
            text=text,
            prompt_request=prompt_request,
            product_context_summary=product_context_summary,
        )
    return {
        "version": "v30.bazi_llm_answer_draft_call.v1",
        "status": "accepted",
        "text": text,
        "provider": cfg.provider,
        "model": cfg.model,
        "executed": True,
        "task_type": task_type,
        "role_key": role_key,
        "context_pack_summary": product_context_summary,
        "prompt_request": _prompt_request_metadata(prompt_request),
        "output_acceptance": acceptance,
        "thinking_mode": {
            "requested": cfg.provider.lower() == "ollama_native",
            "provider_flag": "think" if cfg.provider.lower() == "ollama_native" else "",
            "trace_available": bool(payload.get("_llm_thinking_trace_available")),
            "trace_chars": int(payload.get("_llm_thinking_trace_chars") or 0),
            "trace_policy": "provider_thinking_captured_for_dialogue_observability_public_ui_shows_summary_only",
        },
        "readiness": readiness,
        "drift_check": drift.model_dump(mode="json"),
        "boundary": "bazi_llm_answer_draft_expression_only_no_chart_fact_mutation",
    }


def _post_ollama_native_completion_with_thinking(
    prompt: dict[str, object],
    cfg: V30LLMProviderConfig,
) -> dict[str, object]:
    try:
        return _post_ollama_native_completion(prompt, cfg, enable_thinking=True)
    except TypeError:
        return _post_ollama_native_completion(prompt, cfg)


def call_bazi_llm_thinking_step_summary(
    runtime: CoreRuntimeResult,
    step: dict[str, object],
    *,
    role_key: str | None = None,
    locale: str | None = None,
    client: str = "web",
    config: V30LLMProviderConfig | None = None,
) -> dict[str, object]:
    cfg = config or load_v30_llm_provider_config_from_env()
    readiness = llm_provider_readiness_report(cfg)
    prompt_request = build_thinking_step_prompt_request(
        runtime,
        step,
        role_key=role_key or str(runtime.question_plan.role_key),
        locale=locale or str(runtime.chart_context.locale),
        client=client,
    )
    prompt = _thinking_step_summary_prompt_from_request(prompt_request)
    if not readiness["ready_for_connection"]:
        return _thinking_summary_fallback("provider_not_ready", readiness, prompt=prompt, config=cfg)
    if not cfg.execute_llm:
        return _thinking_summary_fallback("execute_flag_disabled", readiness, prompt=prompt, config=cfg)
    payload: dict[str, object] = {}
    text = ""
    acceptance: dict[str, object] = {}
    active_prompt = prompt
    attempts: list[dict[str, object]] = []
    for attempt_index in range(1):
        try:
            payload = _execute_thinking_summary_prompt(active_prompt, cfg)
        except Exception as exc:
            if cfg.provider.lower() == "ollama":
                try:
                    payload = _post_ollama_native_completion(active_prompt, cfg, enable_thinking=True)
                except Exception as native_exc:
                    return _thinking_summary_fallback(
                        f"call_failed:{type(exc).__name__};ollama_native_failed:{type(native_exc).__name__}",
                        readiness,
                        prompt=active_prompt,
                        config=cfg,
                    )
            else:
                return _thinking_summary_fallback(f"call_failed:{type(exc).__name__}", readiness, prompt=active_prompt, config=cfg)
        derivation = _thinking_derivation_from_payload(payload)
        text = _normalize_thinking_derivation_text(str(derivation.get("text") or "").strip())
        if not text:
            attempts.append({"attempt": attempt_index + 1, "status": "empty_text"})
            active_prompt = _retry_thinking_step_summary_prompt(active_prompt, ["empty_text"])
            continue
        acceptance = validate_thinking_step_summary_text(text, prompt_request=prompt_request)
        derivation_failures = _thinking_derivation_failures(derivation)
        if derivation_failures:
            acceptance = {**acceptance, "accepted": False, "failures": [*_list(acceptance.get("failures")), *derivation_failures]}
        attempts.append({
            "attempt": attempt_index + 1,
            "status": "accepted" if acceptance.get("accepted") else "rejected",
            "failures": acceptance.get("failures", []),
        })
        if acceptance["accepted"]:
            break
    if not text:
        fallback = _thinking_summary_fallback("empty_text", readiness, prompt=active_prompt, config=cfg, executed=True)
        fallback["attempts"] = attempts
        return fallback
    hard_acceptance_failures = _thinking_acceptance_hard_failures(acceptance)
    if hard_acceptance_failures:
        acceptance = {**acceptance, "hard_failures": hard_acceptance_failures}
        fallback = _thinking_summary_fallback(
            "thinking_summary_hard_boundary_failed",
            readiness,
            prompt=active_prompt,
            config=cfg,
            executed=True,
            text=text,
            acceptance=acceptance,
        )
        fallback["attempts"] = attempts
        return fallback
    review = _central_brain_review_thinking_derivation(derivation, step)
    if not acceptance.get("accepted"):
        if review.get("status") == "accepted":
            return {
                "version": "v30.bazi_llm_thinking_step_summary_call.v1",
                "status": "accepted",
                "text": _trim_summary_text(str(review.get("cleaned_stage_text") or text)),
                "derivation": _trim_thinking_derivation(derivation),
                "central_brain_review": review,
                "provider": cfg.provider,
                "model": cfg.model,
                "executed": True,
                "step_id": str(step.get("step_id") or ""),
                "role_key": role_key or str(runtime.question_plan.role_key),
                "locale": locale or str(runtime.chart_context.locale),
                "client": client,
                "prompt_request": _thinking_prompt_metadata(active_prompt),
                "output_acceptance": acceptance,
                "attempts": attempts,
                "thinking_mode": {
                    "requested": True,
                    "provider_flag": "think",
                    "trace_available": bool(payload.get("_llm_thinking_trace_available")) if isinstance(payload, dict) else False,
                    "trace_chars": int(payload.get("_llm_thinking_trace_chars") or 0) if isinstance(payload, dict) else 0,
                    "trace_policy": "raw_model_thinking_captured_once_final_decision_uses_central_brain_cleaning",
                },
                "readiness": readiness,
                "boundary": "thinking_step_llm_candidate_reviewed_by_central_brain_without_llm_rewrite",
            }
        fallback = _thinking_summary_fallback(
            "thinking_summary_acceptance_failed",
            readiness,
            prompt=active_prompt,
            config=cfg,
            executed=True,
            text=text,
            acceptance=acceptance,
            central_brain_review=review,
        )
        fallback["attempts"] = attempts
        return fallback
    return {
        "version": "v30.bazi_llm_thinking_step_summary_call.v1",
        "status": "accepted",
        "text": _trim_summary_text(str(review.get("cleaned_stage_text") or text)),
        "derivation": _trim_thinking_derivation(derivation),
        "central_brain_review": review,
        "provider": cfg.provider,
        "model": cfg.model,
        "executed": True,
        "step_id": str(step.get("step_id") or ""),
        "role_key": role_key or str(runtime.question_plan.role_key),
        "locale": locale or str(runtime.chart_context.locale),
        "client": client,
        "prompt_request": _thinking_prompt_metadata(active_prompt),
        "output_acceptance": acceptance,
        "attempts": attempts,
        "thinking_mode": {
            "requested": True,
            "provider_flag": "think",
            "trace_available": bool(payload.get("_llm_thinking_trace_available")) if isinstance(payload, dict) else False,
            "trace_chars": int(payload.get("_llm_thinking_trace_chars") or 0) if isinstance(payload, dict) else 0,
            "trace_policy": "raw_model_thinking_captured_once_final_decision_uses_central_brain_cleaning",
        },
        "readiness": readiness,
        "boundary": "thinking_step_llm_candidate_reviewed_by_central_brain_without_llm_rewrite",
    }


def stream_bazi_llm_thinking_step_summary_events(
    runtime: CoreRuntimeResult,
    step: dict[str, object],
    *,
    role_key: str | None = None,
    locale: str | None = None,
    client: str = "web",
    config: V30LLMProviderConfig | None = None,
) -> Iterator[dict[str, object]]:
    cfg = config or load_v30_llm_provider_config_from_env()
    readiness = llm_provider_readiness_report(cfg)
    prompt_request = build_thinking_step_prompt_request(
        runtime,
        step,
        role_key=role_key or str(runtime.question_plan.role_key),
        locale=locale or str(runtime.chart_context.locale),
        client=client,
    )
    prompt = _thinking_step_summary_prompt_from_request(prompt_request)
    if not readiness["ready_for_connection"]:
        yield {
            "event": "final_call",
            "call": _thinking_summary_fallback("provider_not_ready", readiness, prompt=prompt, config=cfg),
        }
        return
    if not cfg.execute_llm:
        yield {
            "event": "final_call",
            "call": _thinking_summary_fallback("execute_flag_disabled", readiness, prompt=prompt, config=cfg),
        }
        return
    if cfg.provider.lower() != "ollama_native":
        call = call_bazi_llm_thinking_step_summary(
            runtime,
            step,
            role_key=role_key,
            locale=locale,
            client=client,
            config=cfg,
        )
        yield {"event": "final_call", "call": call}
        return

    content_parts: list[str] = []
    thinking_parts: list[str] = []
    try:
        for chunk in _stream_ollama_native_completion(prompt, cfg, enable_thinking=True):
            delta = str(chunk.get("thinking_delta") or "")
            if delta:
                thinking_parts.append(delta)
                yield {
                    "event": "thinking_delta",
                    "step_id": str(step.get("step_id") or ""),
                    "delta": delta,
                    "trace_chars": sum(len(row) for row in thinking_parts),
                    "boundary": "ollama_native_message_thinking_stream",
                }
            content_delta = str(chunk.get("content_delta") or "")
            if content_delta:
                content_parts.append(content_delta)
    except Exception as exc:
        yield {
            "event": "final_call",
            "call": _thinking_summary_fallback(
                f"call_failed:{type(exc).__name__}",
                readiness,
                prompt=prompt,
                config=cfg,
                executed=True,
            ),
        }
        return

    raw_thinking = "".join(thinking_parts)
    parsed = _parse_json_or_text("".join(content_parts))
    if isinstance(parsed, dict):
        parsed.update(_thinking_transport_metadata(True, raw_thinking))
    call = _finalize_thinking_summary_payload(
        parsed,
        readiness,
        prompt=prompt,
        runtime=runtime,
        step=step,
        cfg=cfg,
        role_key=role_key,
        locale=locale,
        client=client,
        attempts=[{
            "attempt": 1,
            "status": "streamed",
            "thinking_trace_chars": len(raw_thinking),
        }],
    )
    yield {"event": "final_call", "call": call}


def compose_llm_answer_draft(
    answer_context: AnswerContext,
    rule_answer: AnswerResult,
    *,
    reading_surface: dict[str, object] | None = None,
    config: V30LLMProviderConfig | None = None,
) -> AnswerResult:
    cfg = config or load_v30_llm_provider_config_from_env()
    call = call_llm_answer_draft(
        answer_context,
        rule_answer,
        reading_surface=reading_surface or {},
        config=cfg,
    )
    if call["status"] != "accepted":
        return rule_answer.model_copy(
            update={
                "source": "rule_bound_fallback",
                "llm_metadata": call,
            }
        )
    return rule_answer.model_copy(
        update={
            "text": str(call["text"]),
            "source": "llm_bounded_answer_draft",
            "llm_metadata": call,
        }
    )


def call_llm_answer_draft(
    answer_context: AnswerContext,
    rule_answer: AnswerResult,
    *,
    reading_surface: dict[str, object],
    config: V30LLMProviderConfig | None = None,
) -> dict[str, object]:
    cfg = config or load_v30_llm_provider_config_from_env()
    readiness = llm_provider_readiness_report(cfg)
    if not readiness["ready_for_connection"]:
        return _fallback("provider_not_ready", readiness, executed=False)
    if not cfg.execute_llm:
        return _fallback("execute_flag_disabled", readiness, executed=False)
    prompt_context = build_llm_role_prompt_context(answer_context)
    prompt = _answer_prompt(answer_context, rule_answer, reading_surface)
    try:
        if cfg.provider.lower() == "ollama_native":
            payload = _post_ollama_native_completion(prompt, cfg)
        else:
            payload = _post_chat_completion(prompt, cfg)
    except Exception as exc:
        if cfg.provider.lower() == "ollama":
            try:
                payload = _post_ollama_native_completion(prompt, cfg)
            except Exception as native_exc:
                return _fallback(f"call_failed:{type(exc).__name__};ollama_native_failed:{type(native_exc).__name__}", readiness)
        else:
            return _fallback(f"call_failed:{type(exc).__name__}", readiness)
    text = str(payload.get("text") or "").strip() if isinstance(payload, dict) else ""
    drift = check_llm_answer_drift(text, prompt_context)
    if not text:
        return _fallback("empty_text", readiness, executed=True, drift=drift.model_dump(mode="json"))
    if not drift.passed:
        return _fallback("drift_check_failed", readiness, executed=True, drift=drift.model_dump(mode="json"), text=text)
    return {
        "version": "v30.llm_answer_draft_call.v1",
        "status": "accepted",
        "text": text,
        "provider": cfg.provider,
        "model": cfg.model,
        "executed": True,
        "readiness": readiness,
        "drift_check": drift.model_dump(mode="json"),
        "boundary": "llm_answer_draft_expression_only_no_chart_fact_mutation",
    }


def _post_chat_completion(
    prompt: dict[str, object],
    cfg: V30LLMProviderConfig,
    *,
    enable_thinking: bool = False,
) -> dict[str, object]:
    body = {
        "model": cfg.model,
        "temperature": cfg.temperature,
        "max_tokens": _completion_max_tokens(cfg, enable_thinking=enable_thinking),
        "response_format": {"type": "json_object"},
        "messages": _messages(prompt),
    }
    if cfg.provider.lower() == "ollama":
        body["think"] = enable_thinking
    request = urllib.request.Request(
        f"{cfg.resolved_base_url().rstrip('/')}/chat/completions",
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        headers=_headers(cfg),
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=_provider_timeout(cfg, enable_thinking=enable_thinking)) as response:
        raw = response.read().decode("utf-8")
    response_payload = json.loads(raw)
    message = response_payload["choices"][0]["message"]
    content = message["content"]
    parsed = _parse_json_or_text(str(content))
    if isinstance(parsed, dict):
        trace = message.get("thinking") or message.get("reasoning_content") or ""
        parsed.update(_thinking_transport_metadata(enable_thinking, trace))
    return parsed


def _execute_thinking_summary_prompt(prompt: dict[str, object], cfg: V30LLMProviderConfig) -> dict[str, object]:
    if cfg.provider.lower() == "ollama_native":
        return _post_ollama_native_completion(prompt, cfg, enable_thinking=True)
    return _post_chat_completion(prompt, cfg, enable_thinking=True)


def _post_ollama_native_completion(
    prompt: dict[str, object],
    cfg: V30LLMProviderConfig,
    *,
    enable_thinking: bool = False,
) -> dict[str, object]:
    body = {
        "model": cfg.model,
        "messages": _messages(prompt),
        "stream": False,
        "format": "json",
        "think": enable_thinking,
        "options": {
            "temperature": cfg.temperature,
            "num_predict": _completion_max_tokens(cfg, enable_thinking=enable_thinking),
        },
    }
    request = urllib.request.Request(
        f"{cfg.resolved_base_url().rstrip('/').removesuffix('/v1')}/api/chat",
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        headers=_headers(cfg),
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=_provider_timeout(cfg, enable_thinking=enable_thinking)) as response:
        raw = response.read().decode("utf-8")
    response_payload = json.loads(raw)
    message = response_payload.get("message") if isinstance(response_payload, dict) else {}
    content = str(message.get("content") or "") if isinstance(message, dict) else ""
    parsed = _parse_json_or_text(content)
    if isinstance(parsed, dict):
        parsed.update(_thinking_transport_metadata(enable_thinking, message.get("thinking") if isinstance(message, dict) else ""))
    return parsed


def _stream_ollama_native_completion(
    prompt: dict[str, object],
    cfg: V30LLMProviderConfig,
    *,
    enable_thinking: bool = False,
) -> Iterator[dict[str, object]]:
    body = {
        "model": cfg.model,
        "messages": _messages(prompt),
        "stream": True,
        "format": "json",
        "think": enable_thinking,
        "options": {
            "temperature": cfg.temperature,
            "num_predict": _completion_max_tokens(cfg, enable_thinking=enable_thinking),
        },
    }
    request = urllib.request.Request(
        f"{cfg.resolved_base_url().rstrip('/').removesuffix('/v1')}/api/chat",
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        headers=_headers(cfg),
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=_provider_timeout(cfg, enable_thinking=enable_thinking)) as response:
        for raw_line in response:
            line = raw_line.decode("utf-8").strip()
            if not line:
                continue
            payload = json.loads(line)
            message = payload.get("message") if isinstance(payload, dict) else {}
            if not isinstance(message, dict):
                continue
            yield {
                "thinking_delta": message.get("thinking") or "",
                "content_delta": message.get("content") or "",
                "done": bool(payload.get("done")) if isinstance(payload, dict) else False,
            }


def _retry_thinking_step_summary_prompt(prompt: dict[str, object], failures: list[object]) -> dict[str, object]:
    retry_prompt = dict(prompt)
    required = dict(_dict(retry_prompt.get("required_output")))
    base_text = str(required.get("text") or "")
    failure_text = "、".join(str(row) for row in failures if row) or "quality_failure"
    required["text"] = (
        f"{base_text} Retry because the previous output failed: {failure_text}. "
        "Write a fresh derivation. Start with a concrete chart/rule/path fact, not a generic opening. "
        "Avoid every rejected phrase and do not mention that this is a retry."
    )
    retry_prompt["required_output"] = required
    retry_prompt["retry_policy"] = {
        "reason": failure_text,
        "must_change_sentence_shape": True,
        "boundary": "retry_prompt_improves_expression_only_not_bazi_facts",
    }
    return retry_prompt


def _thinking_transport_metadata(enable_thinking: bool, trace: object) -> dict[str, object]:
    raw = str(trace or "")
    return {
        "_llm_thinking_requested": bool(enable_thinking),
        "_llm_thinking_trace_available": bool(raw.strip()),
        "_llm_thinking_trace_chars": len(raw),
        "_llm_thinking_trace_policy": "captured_for_transport_diagnostics_not_customer_display",
    }


def _messages(prompt: dict[str, object]) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": (
                "You are V30's bounded Bazi expression layer. Return exactly one JSON object. "
                "Use only the provided deterministic context, prompt contract, and task payload. "
                "Do not create pillars, luck cycles, flow years, event years, hidden-factor facts, or fixed verdicts."
            ),
        },
        {"role": "user", "content": json.dumps(prompt, ensure_ascii=False, sort_keys=True)},
    ]


def _answer_prompt(
    answer_context: AnswerContext,
    rule_answer: AnswerResult,
    reading_surface: dict[str, object],
) -> dict[str, object]:
    return {
        "version": "v30.llm_answer_prompt.v1",
        "task": "answer_draft",
        "locale": "zh",
        "customer_surface": _compact_surface(reading_surface),
        "selected_question": {
            "question_id": answer_context.selected_question_anchor.question_id,
            "intent_id": answer_context.selected_question_anchor.intent_id,
            "anchor_status": answer_context.selected_question_anchor.anchor_status,
        },
        "chart_summary": answer_context.chart_summary,
        "mainline_summary": answer_context.mainline_summary,
        "role_answer_contract": answer_context.role_answer_contract,
        "rule_answer": {
            "text": rule_answer.text,
            "evidence_ids": rule_answer.evidence_ids,
            "boundary": rule_answer.boundary,
        },
        "required_output": {
            "text": (
                "A concise customer-facing Chinese answer, 2-3 sentences, no markdown, no internal ids. "
                "Answer the selected question directly. Do not include diagnostic headings, evidence counts, source status, "
                "internal boundary notes, or empty hedge phrases like 不好说、仅供参考、后续我们可以. "
                "If the Bazi evidence supports multiple branches, state the primary branch first and name the key alternative with its evidence or confirmation condition. "
                "Do not ask a new question inside the answer text."
            ),
        },
        "forbidden": answer_context.forbidden_drift,
        "boundary": "prompt_context_for_llm_expression_only_not_chart_fact_source",
    }


def _bazi_answer_prompt(
    prompt_request: dict[str, object],
    answer_context: AnswerContext,
    rule_answer: AnswerResult,
    reading_surface: dict[str, object],
) -> dict[str, object]:
    contract = prompt_request.get("prompt_contract", {})
    context_pack = prompt_request.get("context_pack", {})
    return {
        "version": "v30.bazi_llm_answer_prompt.v1",
        "task": prompt_request.get("task_type"),
        "role_key": context_pack.get("role_key") if isinstance(context_pack, dict) else "user",
        "locale": context_pack.get("locale") if isinstance(context_pack, dict) else "zh",
        "prompt_contract": {
            "prompt_contract_id": contract.get("prompt_contract_id") if isinstance(contract, dict) else "",
            "output_schema": contract.get("output_schema") if isinstance(contract, dict) else {},
            "system_rules": contract.get("system_rules") if isinstance(contract, dict) else [],
            "role_contract": contract.get("role_contract") if isinstance(contract, dict) else {},
            "fallback": contract.get("fallback") if isinstance(contract, dict) else {},
        },
        "context_pack": context_pack,
        "customer_surface": _compact_surface(reading_surface),
        "selected_question": {
            "question_id": answer_context.selected_question_anchor.question_id,
            "intent_id": answer_context.selected_question_anchor.intent_id,
            "anchor_status": answer_context.selected_question_anchor.anchor_status,
        },
        "rule_answer": {
            "text": rule_answer.text,
            "evidence_ids": rule_answer.evidence_ids,
            "boundary": rule_answer.boundary,
        },
        "required_output": {
            "text": (
                "Return one JSON object matching prompt_contract.output_schema.required_fields. "
                "For customer_initial_reading include answer_text, evidence_ids, boundaries, next_question_hint. "
                "For domain_followup include domain, answer_text, used_user_signals, boundaries. "
                "The answer_text must be customer-facing Chinese, 2-3 sentences, and answer the selected question directly. "
                "Do not put diagnostic headings, evidence counts, source status, boundary notes, or internal routing details in answer_text. "
                "Avoid empty hedge phrases like 不好说、仅供参考、后续我们可以. "
                "Evidence-bound branches are allowed: if multiple Bazi paths remain live, name the primary path, one meaningful alternative, and what evidence or user signal would raise/lower that alternative. "
                "Put any next-step prompt only in next_question_hint or structured fields, not in answer_text. "
                "Match role_contract terminology. No markdown, no internal ids."
            ),
        },
        "forbidden": answer_context.forbidden_drift,
        "boundary": "bazi_task_role_context_prompt_for_llm_expression_only_not_chart_fact_source",
    }


def _thinking_step_summary_prompt(
    runtime: CoreRuntimeResult,
    step: dict[str, object],
    *,
    role_key: str,
    locale: str,
    client: str,
) -> dict[str, object]:
    chart = runtime.chart_context
    summary_panel = step.get("summary_panel", {})
    evidence_digest = step.get("evidence_digest", {})
    return {
        "version": "v30.bazi_llm_thinking_step_summary_prompt.v1",
        "task": "thinking_step_summary",
        "role_key": role_key,
        "locale": locale,
        "client": client,
        "stage": {
            "step_id": step.get("step_id"),
            "phase": step.get("phase"),
            "title": step.get("title"),
            "summary": step.get("summary"),
            "tasks": _safe_prompt_rows(step.get("tasks"), limit=5),
            "evidence_digest": evidence_digest if isinstance(evidence_digest, dict) else {},
            "central_brain_summary": summary_panel if isinstance(summary_panel, dict) else {},
            "analysis_result": step.get("analysis_result") if isinstance(step.get("analysis_result"), dict) else {},
            "confidence": step.get("confidence"),
        },
        "chart_summary": {
            "day_master": chart.day_master,
            "day_master_element": chart.day_master_element,
            "pillars": chart.natal_pillars,
            "time_layers": chart.time_layers,
        },
        "required_output": {
            "text": (
                "Return exactly one JSON object with key text. text must be a polished Chinese customer-facing stage summary, "
                "2-4 short sentences. Explain what this step has concluded and why it matters for the next step. "
                "Prefer stage.analysis_result as the source of judgment. Use stage data and chart_summary only as support. "
                "Do not use fixed labels such as 结论：, 建议：, 依据：, 判断：, or 要点：. "
                "Do not invent pillars, luck cycles, flow years, event years, "
                "or hidden user facts. Do not expose internal ids, source ids, context ids, evidence ids, JSON keys, or diagnostics. "
                "Do not use markdown."
            ),
        },
        "forbidden": [
            "新增四柱事实",
            "新增大运流年事实",
            "内部编号",
            "context_id",
            "v30.",
            "krp.",
            "evidence_id",
            "source_id",
            "JSON",
        ],
        "boundary": "thinking_step_summary_prompt_for_llm_expression_only_not_chart_fact_source",
    }


def _thinking_step_summary_prompt_from_request(prompt_request: dict[str, object]) -> dict[str, object]:
    contract = _dict(prompt_request.get("prompt_contract"))
    context_pack = _dict(prompt_request.get("context_pack"))
    prompt_profile = _dict(context_pack.get("prompt_profile"))
    return {
        "version": "v30.thinking_step_summary_prompt.v3",
        "task": "thinking_step_summary",
        "reading_id": prompt_request.get("reading_id"),
        "step_id": prompt_request.get("step_id"),
        "prompt_contract": {
            "prompt_contract_id": contract.get("prompt_contract_id"),
            "output_schema": contract.get("output_schema"),
            "role_contract": contract.get("role_contract"),
            "system_rules": _safe_prompt_rows(contract.get("system_rules"), limit=8),
            "fallback": contract.get("fallback"),
        },
        "context_pack": context_pack,
        "stage_prompt_profile": prompt_profile,
        "required_output": {
            "text": (
                "Return exactly one JSON object with keys: text, public_thinking_lines, public_derivation, candidate_points, derived_conclusion, derived_advice, used_evidence, uncertainty. "
                "candidate_points is REQUIRED and must contain at least one verdict point and one advice point. "
                "Keep derived_conclusion and derived_advice for compatibility, but the main output is candidate_points. "
                f"Stage scene: {prompt_profile.get('scene') or 'stage_summary'}. "
                f"Stage task: {prompt_profile.get('task') or 'Write a concrete Bazi derivation for this exact page stage only.'} "
                f"Required named anchors: {', '.join(str(row) for row in _safe_prompt_rows(prompt_profile.get('must_name'), limit=6)) or 'stage evidence and conclusion'}. "
                f"Answer shape: {prompt_profile.get('answer_shape') or 'evidence -> mechanism -> conclusion -> advice'}. "
                f"Scene-specific avoid list: {'; '.join(str(row) for row in _safe_prompt_rows(prompt_profile.get('avoid'), limit=6))}. "
                "Write a concrete Bazi derivation for this exact page stage only, not a reusable summary template and not a final full-report answer. "
                "First obey context_pack.stage.summary_policy.signals.focus_scope. Never import conclusions from another page unless they are already present in this stage context. "
                "Use context_pack.stage.summary_decision as the decision anchor, but you MUST also use stage-specific details "
                "from context_pack.module_context and context_pack.xuanming_reasoning. Name the actual mechanism, feature, rule, "
                "portrait, path, timing gap, or domain landing that appears in this stage. "
                "The stage_prompt_profile is the primary scene contract; follow it before any generic stage rule. "
                "The text should read like a practitioner deriving the result: connect evidence -> mechanism -> conclusion -> action, "
                "without using numbered headings or a fixed sentence frame. "
                "derived_conclusion must be one sharp stage-local verdict. derived_advice must be one practical stage-local action. "
                "candidate_points must be an array of JSON objects with kind, text, short_label, bazi_terms, macro_domains, and evidence_refs. "
                "Use kind=branch when this stage has multiple live candidates. A branch point may include confidence, probability, branch_role, counter_refs, resolution_conditions, and option_hints. "
                "Preserve meaningful Bazi alternatives instead of forcing one fake-certain answer; always put the primary branch first and explain why it currently leads. "
                "candidate_points may include option_hints when the text clearly contains alternatives, lists, numbers, or a practitioner-selectable tradeoff; "
                "option_hints are suggestions only and the central brain will re-extract and gate OptionSets. "
                "Allowed point kinds: verdict, branch, evidence, mechanism, advice, risk, question. "
                "The first candidate point should usually be kind=verdict; include kind=advice for the practical stage-local action. "
                "Every candidate point must stay inside this page stage and bind to actual stage evidence, Bazi terms, or module anchors. "
                "Do not prefix text, derived_conclusion, or derived_advice with labels such as 结论：, 建议：, 依据：, 判断：, or 要点：; "
                "write the content itself so the UI can list it directly. "
                "Start directly from concrete Bazi evidence, such as the day master, month branch, ten-god combination, matched rule, "
                "portrait signal, or force-flow path. Do not begin with 从...来看、本次分析、当前、目前、综合来看. "
                "Do not write generic process phrases such as 后续、请注意、请您、综合来看、当前阶段、目前阶段、本次分析、不是最终定论、需要进一步、可以参考. "
                "Do not use empty uncertainty phrases. Words like 可能、候选、分支、概率、置信、待复核 are allowed only when tied to concrete Bazi evidence, branch weights, counter-evidence, or resolution conditions. "
                "Do not describe the workflow, the system, the model, token usage, or that this is a current stage. "
                "Do not expose internal ids, JSON keys, diagnostics, or source labels. "
                "Do not invent chart facts, event years, user history, or hidden-factor confirmations. "
                "public_thinking_lines or public_derivation must contain 3-5 short customer-safe derivation lines, not hidden chain-of-thought; each line should show evidence, mechanism, conclusion pressure, or action implication. "
                "derived_conclusion must be the stage conclusion after derivation. derived_advice must be the concrete advice after derivation. "
                "Target text 180-420 Chinese characters. If the stage lacks timing data, state the concrete missing item and how it limits this stage."
            ),
        },
        "boundary": "thinking_step_summary_prompt_consumes_formal_prompt_request",
    }


def _summary_text_from_payload(payload: object) -> str:
    if not isinstance(payload, dict):
        return ""
    for key in ("text", "summary", "body", "answer_text"):
        value = str(payload.get(key) or "").strip()
        if value:
            return value
    return ""


def _thinking_derivation_from_payload(payload: object) -> dict[str, object]:
    data = _dict(payload)
    candidate_points = _candidate_points_from_payload(data.get("candidate_points"))
    public_derivation = _string_rows(data.get("public_derivation"))
    lines = data.get("public_thinking_lines")
    if isinstance(lines, str):
        lines = [row.strip() for row in lines.split("\n") if row.strip()]
    if not isinstance(lines, list):
        lines = []
    if not lines and public_derivation:
        lines = public_derivation
    derived_conclusion = str(data.get("derived_conclusion") or "").strip()
    derived_advice = str(data.get("derived_advice") or "").strip()
    if candidate_points:
        if not derived_conclusion:
            derived_conclusion = _first_candidate_point_text(candidate_points, "verdict")
        if not derived_advice:
            derived_advice = _first_candidate_point_text(candidate_points, "advice")
    used_evidence = [str(row).strip() for row in _list(data.get("used_evidence")) if str(row).strip()][:6]
    if not used_evidence:
        used_evidence = _candidate_evidence_refs(candidate_points)[:6]
    text = str(data.get("text") or data.get("summary") or data.get("body") or "").strip()
    if not text:
        text = " ".join([*public_derivation[:3], *[str(row.get("text") or "") for row in candidate_points[:3]]]).strip()
    return {
        "version": "v30.llm_stage_derivation.v1",
        "text": text,
        "public_thinking_lines": [str(row).strip() for row in lines if str(row).strip()][:5],
        "public_derivation": public_derivation[:5],
        "candidate_points": candidate_points[:8],
        "derived_conclusion": derived_conclusion,
        "derived_advice": derived_advice,
        "used_evidence": used_evidence,
        "uncertainty": [str(row).strip() for row in _list(data.get("uncertainty")) if str(row).strip()][:4],
        "boundary": "llm_derivation_is_candidate_for_central_brain_review_not_chart_fact",
    }


def _candidate_points_from_payload(value: object) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for row in _list(value):
        if isinstance(row, dict):
            text = str(row.get("text") or row.get("summary") or row.get("body") or "").strip()
            if text:
                rows.append({**row, "text": text})
        elif str(row).strip():
            rows.append({"kind": "mechanism", "text": str(row).strip()})
    return rows


def _string_rows(value: object) -> list[str]:
    if isinstance(value, str):
        return [row.strip() for row in value.split("\n") if row.strip()]
    return [str(row).strip() for row in _list(value) if str(row).strip()]


def _first_candidate_point_text(points: list[dict[str, object]], kind: str) -> str:
    for point in points:
        if str(point.get("kind") or "").lower() == kind:
            return str(point.get("text") or "").strip()
    return ""


def _candidate_evidence_refs(points: list[dict[str, object]]) -> list[str]:
    rows: list[str] = []
    for point in points:
        rows.extend(str(row).strip() for row in _list(point.get("evidence_refs")) if str(row).strip())
        rows.extend(str(row).strip() for row in _list(point.get("bazi_terms")) if str(row).strip())
    return rows


def _finalize_thinking_summary_payload(
    payload: dict[str, object],
    readiness: dict[str, object],
    *,
    prompt: dict[str, object],
    runtime: CoreRuntimeResult,
    step: dict[str, object],
    cfg: V30LLMProviderConfig,
    role_key: str | None,
    locale: str | None,
    client: str,
    attempts: list[dict[str, object]],
) -> dict[str, object]:
    derivation = _thinking_derivation_from_payload(payload)
    text = _normalize_thinking_derivation_text(str(derivation.get("text") or "").strip())
    if not text:
        fallback = _thinking_summary_fallback("empty_text", readiness, prompt=prompt, config=cfg, executed=True)
        fallback["attempts"] = attempts
        return fallback
    acceptance = validate_thinking_step_summary_text(text, prompt_request=_prompt_request_from_prompt(prompt))
    derivation_failures = _thinking_derivation_failures(derivation)
    if derivation_failures:
        acceptance = {**acceptance, "accepted": False, "failures": [*_list(acceptance.get("failures")), *derivation_failures]}
    hard_acceptance_failures = _thinking_acceptance_hard_failures(acceptance)
    if hard_acceptance_failures:
        acceptance = {**acceptance, "hard_failures": hard_acceptance_failures}
        fallback = _thinking_summary_fallback(
            "thinking_summary_hard_boundary_failed",
            readiness,
            prompt=prompt,
            config=cfg,
            executed=True,
            text=text,
            acceptance=acceptance,
        )
        fallback["attempts"] = attempts
        return fallback
    review = _central_brain_review_thinking_derivation(derivation, step)
    if not acceptance.get("accepted") and review.get("status") != "accepted":
        fallback = _thinking_summary_fallback(
            "thinking_summary_acceptance_failed",
            readiness,
            prompt=prompt,
            config=cfg,
            executed=True,
            text=text,
            acceptance=acceptance,
            central_brain_review=review,
        )
        fallback["attempts"] = attempts
        return fallback
    return {
        "version": "v30.bazi_llm_thinking_step_summary_call.v1",
        "status": "accepted",
        "text": _trim_summary_text(str(review.get("cleaned_stage_text") or text)),
        "derivation": _trim_thinking_derivation(derivation),
        "central_brain_review": review,
        "provider": cfg.provider,
        "model": cfg.model,
        "executed": True,
        "step_id": str(step.get("step_id") or ""),
        "role_key": role_key or str(runtime.question_plan.role_key),
        "locale": locale or str(runtime.chart_context.locale),
        "client": client,
        "prompt_request": _thinking_prompt_metadata(prompt),
        "output_acceptance": acceptance,
        "attempts": attempts,
        "thinking_mode": {
            "requested": True,
            "provider_flag": "think",
            "trace_available": bool(payload.get("_llm_thinking_trace_available")),
            "trace_chars": int(payload.get("_llm_thinking_trace_chars") or 0),
            "trace_policy": "raw_model_thinking_streamed_to_customer_surface_while_final_decision_uses_public_derivation",
        },
        "readiness": readiness,
        "boundary": "thinking_step_llm_candidate_reviewed_by_central_brain_without_llm_rewrite",
    }


def _prompt_request_from_prompt(prompt: dict[str, object]) -> dict[str, object]:
    return {
        "prompt_contract": prompt.get("prompt_contract") if isinstance(prompt.get("prompt_contract"), dict) else {},
        "context_pack": prompt.get("context_pack") if isinstance(prompt.get("context_pack"), dict) else {},
        "raw_runtime_payload_included": False,
    }


def _thinking_derivation_failures(derivation: dict[str, object]) -> list[str]:
    failures: list[str] = []
    candidate_points = _list(derivation.get("candidate_points"))
    has_candidate_verdict = any(isinstance(row, dict) and str(row.get("kind") or "").lower() == "verdict" and str(row.get("text") or "").strip() for row in candidate_points)
    has_candidate_advice = any(isinstance(row, dict) and str(row.get("kind") or "").lower() == "advice" and str(row.get("text") or "").strip() for row in candidate_points)
    if not str(derivation.get("derived_conclusion") or "").strip() and not has_candidate_verdict:
        failures.append("missing_derived_conclusion")
    if not str(derivation.get("derived_advice") or "").strip() and not has_candidate_advice:
        failures.append("missing_derived_advice")
    if len(_list(derivation.get("public_thinking_lines"))) < 2 and len(candidate_points) < 2:
        failures.append("missing_public_thinking_lines")
    joined = " ".join(str(row) for row in [
        derivation.get("text"),
        derivation.get("derived_conclusion"),
        derivation.get("derived_advice"),
        *_list(derivation.get("public_thinking_lines")),
        *[str(_dict(row).get("text") or "") for row in candidate_points],
    ])
    if _contains_internal_identifier(joined):
        failures.append("internal_identifier_in_derivation")
    return failures


def _thinking_acceptance_hard_failures(acceptance: dict[str, object]) -> list[str]:
    hard_failures: list[str] = []
    for failure in _list(acceptance.get("failures")):
        code = str(failure or "")
        if (
            code.startswith("internal_identifier:")
            or code.startswith("customer_role_leaks_")
            or code in {"chart_fact_boundary_not_locked", "high_risk_fixed_verdict"}
        ):
            hard_failures.append(code)
    return hard_failures


def _derivation_soft_language_notes(text: str) -> list[str]:
    if _is_soft_noncommittal(text):
        return ["soft_or_noncommittal_derivation_language_cleaned_by_central_brain"]
    return []


def _trim_thinking_derivation(derivation: dict[str, object]) -> dict[str, object]:
    return {
        **derivation,
        "text": _trim_summary_text(str(derivation.get("text") or "")),
        "derived_conclusion": _trim_summary_text(str(derivation.get("derived_conclusion") or "")),
        "derived_advice": _trim_summary_text(str(derivation.get("derived_advice") or "")),
        "public_thinking_lines": [_trim_summary_text(str(row)) for row in _list(derivation.get("public_thinking_lines"))[:5]],
        "public_derivation": [_trim_summary_text(str(row)) for row in _list(derivation.get("public_derivation"))[:5]],
        "candidate_points": [
            {
                **row,
                "text": _trim_summary_text(str(row.get("text") or "")),
                "short_label": _trim_summary_text(str(row.get("short_label") or ""))[:40],
            }
            for row in _list(derivation.get("candidate_points"))[:8]
            if isinstance(row, dict)
        ],
    }


def _central_brain_review_thinking_derivation(derivation: dict[str, object], step: dict[str, object]) -> dict[str, object]:
    analysis = _dict(step.get("analysis_result"))
    policy = _dict(step.get("summary_policy"))
    policy_signals = _dict(policy.get("signals"))
    prompt_profile = _dict(policy_signals.get("prompt_profile"))
    candidate_failures = _thinking_derivation_failures(derivation)
    joined_candidate = " ".join(str(row) for row in [
        derivation.get("text"),
        derivation.get("derived_conclusion"),
        derivation.get("derived_advice"),
        *_list(derivation.get("public_thinking_lines")),
        *[str(_dict(row).get("text") or "") for row in _list(derivation.get("candidate_points"))],
    ])
    quality_notes = _derivation_soft_language_notes(joined_candidate)
    conclusion = _central_brain_clean_conclusion(
        str(derivation.get("derived_conclusion") or analysis.get("conclusion") or "").strip(),
        analysis,
    )
    advice = _central_brain_clean_advice(
        str(derivation.get("derived_advice") or analysis.get("next_focus") or "").strip(),
        analysis,
    )
    public_lines = [
        _normalize_thinking_derivation_text(str(row))
        for row in _list(derivation.get("public_thinking_lines"))[:5]
        if str(row).strip()
    ]
    if not public_lines:
        public_lines = _central_brain_public_lines_from_stage(analysis)
    public_lines = _central_brain_strengthen_stage_anchors(step, public_lines)
    coverage_failures = _stage_anchor_coverage_failures(step, [conclusion, advice, *public_lines, *_list(derivation.get("used_evidence"))])
    stage_anchor_evidence = _central_brain_stage_anchor_evidence(step)
    conclusion = _central_brain_make_decisive(conclusion, analysis)
    advice = _central_brain_make_decisive(advice, analysis)
    public_lines = _central_brain_merge_stage_anchor_lines(public_lines, stage_anchor_evidence)
    brain_judge = judge_llm_derivation_quality(
        derived_conclusion=conclusion,
        derived_advice=advice,
        public_thinking_lines=public_lines,
        used_evidence=_list(derivation.get("used_evidence")) or stage_anchor_evidence,
    )
    hard_failures = [failure for failure in candidate_failures if failure == "internal_identifier_in_derivation"]
    quality_failures = [failure for failure in candidate_failures if failure != "internal_identifier_in_derivation"]
    if not conclusion:
        hard_failures.append("central_brain_missing_final_conclusion")
    if not advice:
        hard_failures.append("central_brain_missing_final_advice")
    if not public_lines:
        hard_failures.append("central_brain_missing_public_reasoning_lines")
    if not brain_judge.get("accepted"):
        quality_failures.extend([f"brain_judge:{failure}" for failure in _list(brain_judge.get("failures"))])
    cleaned_text = _central_brain_clean_stage_text(
        derivation,
        analysis,
        conclusion=conclusion,
        advice=advice,
        stage_anchor_evidence=stage_anchor_evidence,
    )
    stage_point_set = enrich_stage_point_set_with_text_options(build_stage_point_set(
        step,
        candidate_points=_list(derivation.get("candidate_points")),
        public_derivation=public_lines or _list(derivation.get("public_derivation")),
        conclusion=conclusion,
        advice=advice,
        stage_anchor_evidence=stage_anchor_evidence,
        used_evidence=_list(derivation.get("used_evidence")),
        source="central_brain_reviewed_llm",
    ))
    selected_points = selected_stage_points(stage_point_set)
    return {
        "version": "v30.central_brain_llm_derivation_review.v1",
        "brain_judge_version": BRAIN_JUDGE_VERSION,
        "status": "accepted" if not hard_failures else "rejected",
        "adoption_mode": (
            "direct_llm_derivation"
            if brain_judge.get("accepted") and not quality_failures and not coverage_failures and not quality_notes
            else "central_brain_cleaned_llm_derivation"
        ),
        "final_conclusion": conclusion,
        "final_advice": advice,
        "stage_focus_scope": str(policy_signals.get("focus_scope") or ""),
        "stage_prompt_profile": prompt_profile,
        "stage_anchor_evidence": stage_anchor_evidence,
        "public_thinking_lines": public_lines,
        "used_evidence": _list(derivation.get("used_evidence"))[:6],
        "uncertainty": _list(derivation.get("uncertainty"))[:4],
        "stage_point_set": stage_point_set,
        "stage_points": selected_points,
        "candidate_failures": candidate_failures,
        "coverage_notes": coverage_failures,
        "quality_notes": [*quality_notes, *coverage_failures, *quality_failures],
        "quality_gate": {
            "version": "v30.central_brain_llm_quality_gate.v1",
            "hard_boundary_passed": not hard_failures,
            "brain_judge_accepted": bool(brain_judge.get("accepted")),
            "brain_judge_is_blocking": False,
            "quality_failures_are_cleaned_not_blocked": True,
        },
        "brain_judge": brain_judge,
        "failures": hard_failures,
        "cleaned_stage_text": cleaned_text,
        "rules": [
            "llm_derivation_cannot_mutate_chart_facts",
            "central_brain_cleans_soft_language_without_llm_rewrite",
            "brain_judge_quality_failures_do_not_block_nonempty_llm_derivation",
            "final_conclusion_requires_stage_anchor_evidence",
            "final_advice_requires_action",
        ],
        "boundary": "central_brain_reviews_llm_derivation_before_customer_final_conclusion",
    }


def _central_brain_clean_conclusion(text: str, analysis: dict[str, object]) -> str:
    cleaned = _normalize_thinking_derivation_text(text)
    fallback = _normalize_thinking_derivation_text(str(analysis.get("conclusion") or ""))
    if not cleaned or _is_soft_noncommittal(cleaned):
        return fallback
    return cleaned


def _central_brain_clean_advice(text: str, analysis: dict[str, object]) -> str:
    cleaned = _normalize_thinking_derivation_text(text)
    fallback = _normalize_thinking_derivation_text(str(analysis.get("next_focus") or ""))
    if not cleaned or _is_soft_noncommittal(cleaned):
        return fallback
    return cleaned


def _central_brain_clean_stage_text(
    derivation: dict[str, object],
    analysis: dict[str, object],
    *,
    conclusion: str,
    advice: str,
    stage_anchor_evidence: list[str],
) -> str:
    text = _normalize_thinking_derivation_text(str(derivation.get("text") or ""))
    if not text or _is_soft_noncommittal(text):
        summary = str(analysis.get("user_summary") or conclusion)
        text = _normalize_thinking_derivation_text(summary)
    evidence_text = "；".join(stage_anchor_evidence[:2])
    prefix = []
    if conclusion:
        prefix.append(conclusion)
    if advice:
        prefix.append(advice)
    if evidence_text:
        prefix.append(evidence_text)
    prefix_text = "。".join(row.rstrip("。") for row in prefix if row).strip()
    if prefix_text:
        return f"{prefix_text}。{text}".strip()
    return text.strip()


def _central_brain_public_lines_from_stage(analysis: dict[str, object]) -> list[str]:
    rows: list[str] = []
    for row in _list(analysis.get("public_trace")):
        if not isinstance(row, dict):
            continue
        label = str(row.get("label") or "").strip()
        text = _normalize_thinking_derivation_text(str(row.get("text") or ""))
        if label and text:
            rows.append(f"{label}：{text}")
    if not rows:
        rows = [_normalize_thinking_derivation_text(str(row)) for row in _list(analysis.get("reasoning_points")) if str(row)]
    return rows[:5]


def _central_brain_strengthen_stage_anchors(step: dict[str, object], rows: list[str]) -> list[str]:
    step_id = str(step.get("step_id") or "")
    analysis = _dict(step.get("analysis_result"))
    trace = _list(analysis.get("public_trace"))
    strengthened = [row for row in rows if row]
    if step_id == "rule_matching" and not any("匹配规则" in row for row in strengthened):
        for row in trace:
            if isinstance(row, dict) and row.get("label") == "匹配规则":
                strengthened.insert(0, f"匹配规则：{_normalize_thinking_derivation_text(str(row.get('text') or ''))}")
                break
    if step_id == "portrait_projection" and not any("画像" in row for row in strengthened):
        strengthened.insert(0, "画像结论：本页把结构信号转成人的稳定表现倾向。")
    if step_id == "path_reasoning" and not any(token in " ".join(strengthened) for token in ("路径", "做功", "力量")):
        strengthened.insert(0, "路径结论：本页判断命局力量如何流动、在哪里落地。")
    if step_id == "useful_god_arbitration" and not any(token in " ".join(strengthened) for token in ("用神", "忌避", "取舍")):
        strengthened.insert(0, "用神取舍：本页判断取用策略、忌避风险和反证边界。")
    return strengthened[:5]


def _central_brain_stage_anchor_evidence(step: dict[str, object]) -> list[str]:
    analysis = _dict(step.get("analysis_result"))
    rows: list[str] = []
    for row in _list(analysis.get("public_trace")):
        if not isinstance(row, dict):
            continue
        label = str(row.get("label") or "").strip()
        text = _normalize_thinking_derivation_text(str(row.get("text") or ""))
        if label and text and label in {"匹配规则", "画像结论", "路径结论", "结构主线", "用神取向", "候选五行", "忌避风险", "领域结论", "时运入口", "报告结论", "测算作用"}:
            rows.append(f"{label}：{text}")
    if not rows:
        rows = [
            _normalize_thinking_derivation_text(str(row))
            for row in _list(analysis.get("reasoning_points"))[:3]
            if str(row).strip()
        ]
    return rows[:4]


def _central_brain_merge_stage_anchor_lines(rows: list[str], anchors: list[str]) -> list[str]:
    merged = [row for row in rows if row]
    joined = " ".join(merged)
    for anchor in anchors:
        key = anchor.split("：", 1)[0]
        if key and key not in joined:
            merged.insert(0, anchor)
    return merged[:5]


def _central_brain_make_decisive(text: str, analysis: dict[str, object]) -> str:
    cleaned = _normalize_thinking_derivation_text(text)
    fallback = _normalize_thinking_derivation_text(str(analysis.get("conclusion") or analysis.get("next_focus") or ""))
    if not cleaned:
        return fallback
    if _is_evidence_bound_branch_text(cleaned):
        return " ".join(cleaned.split()).strip(" ，,。") or fallback
    replacements = {
        "可以考虑": "优先",
        "可考虑": "优先",
        "可能会": "会",
        "可能": "",
        "倾向于": "指向",
        "大致": "",
        "一定程度": "",
    }
    for old, new in replacements.items():
        cleaned = cleaned.replace(old, new)
    cleaned = " ".join(cleaned.split()).strip(" ，,。")
    return cleaned or fallback


def _is_soft_noncommittal(text: str) -> bool:
    soft_terms = ("可能", "大概", "潜在", "初步", "候选状态", "无法定论", "不能作为阶段结论", "仅凭", "多个候选", "不好说", "仅供参考")
    clean = str(text or "")
    return any(term in clean for term in soft_terms) and not _is_evidence_bound_branch_text(clean)


def _is_evidence_bound_branch_text(text: str) -> bool:
    clean = str(text or "")
    branch_terms = ("候选", "分支", "概率", "置信", "权重", "评分", "可能", "倾向", "取向", "优先看")
    evidence_terms = (
        "证据",
        "反证",
        "路径",
        "十神",
        "用神",
        "忌神",
        "日主",
        "月令",
        "官杀",
        "印星",
        "财星",
        "食伤",
        "比劫",
        "地支",
        "规则",
        "画像",
        "大运",
        "流年",
        "结构",
        "确认",
        "复核",
        "降权",
        "升权",
    )
    return any(term in clean for term in branch_terms) and any(term in clean for term in evidence_terms)


def _stage_anchor_coverage_failures(step: dict[str, object], rows: list[object]) -> list[str]:
    step_id = str(step.get("step_id") or "")
    analysis = _dict(step.get("analysis_result"))
    trace = _list(analysis.get("public_trace"))
    joined = " ".join(str(row) for row in rows if row)
    if step_id == "rule_matching":
        matched = ""
        for row in trace:
            if isinstance(row, dict) and row.get("label") == "匹配规则":
                matched = str(row.get("text") or "")
                break
        anchors = [token.strip() for token in matched.replace("、", "，").split("，") if token.strip()]
        hits = [token for token in anchors if token and token in joined]
        if len(hits) < min(2, len(anchors)):
            return ["rule_matching_requires_named_matched_rules"]
    if step_id == "portrait_projection" and "画像" not in joined:
        return ["portrait_projection_requires_portrait_wording"]
    if step_id == "path_reasoning" and not any(token in joined for token in ("路径", "做功", "力量")):
        return ["path_reasoning_requires_path_mechanism"]
    if step_id == "useful_god_arbitration" and not ("用神" in joined and any(token in joined for token in ("忌避", "风险", "反证"))):
        return ["useful_god_arbitration_requires_useful_god_and_avoidance_risk"]
    return []


def _normalize_thinking_derivation_text(text: str) -> str:
    import re

    clean = " ".join(str(text or "").split())
    clean = re.sub(r"^(结论|建议|依据|判断|要点)\s*[：:]\s*", "", clean)
    clean = re.sub(r"^从[^，。]{0,30}(角度|层面)(看|来看)?[，,]\s*", "", clean)
    clean = re.sub(r"^从[^，。]{0,30}来看[，,]\s*", "", clean)
    clean = re.sub(r"^(本次分析|当前阶段|目前阶段|当前|目前)[，,]\s*", "", clean)
    replacements = {
        "后续的分析": "",
        "后续分析": "",
        "后续的解读": "",
        "后续": "",
        "请注意，": "",
        "请注意": "",
        "请您": "",
        "请提供": "补充",
        "综合来看，": "",
        "综合来看": "",
        "当前阶段": "此处",
        "目前阶段": "此处",
        "当前": "",
        "目前": "",
        "此处": "",
        "不是最终定论": "仍需证据落地",
        "最终的定论": "阶段结论",
        "最终定论": "阶段结论",
        "并非最终的定论": "仍需证据落地",
        "并非最终定论": "仍需证据落地",
        "需要进一步": "还要",
        "建议您": "建议",
        "接下来": "",
        "初步": "",
        "潜在": "",
        "候选状态": "候选",
        "无法定论": "证据不足",
        "不能作为阶段结论": "作为候选证据",
        "仅凭": "依据",
    }
    for old, new in replacements.items():
        clean = clean.replace(old, new)
    clean = re.sub(r"^的(?=(命理判断|判断|结构判断|取用策略))", "", clean)
    clean = clean.replace("建议：的", "建议：")
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean


def _thinking_summary_fallback(
    reason: str,
    readiness: dict[str, object],
    *,
    prompt: dict[str, object],
    config: V30LLMProviderConfig,
    executed: bool = False,
    text: str = "",
    acceptance: dict[str, object] | None = None,
    central_brain_review: dict[str, object] | None = None,
) -> dict[str, object]:
    return {
        "version": "v30.bazi_llm_thinking_step_summary_call.v1",
        "status": "fallback",
        "fallback_reason": reason,
        "text": text,
        "provider": config.provider,
        "model": config.model,
        "executed": executed,
        "step_id": _thinking_prompt_step_id(prompt),
        "prompt_request": _thinking_prompt_metadata(prompt),
        "output_acceptance": acceptance or {},
        "central_brain_review": central_brain_review or {},
        "readiness": readiness,
        "boundary": "thinking_step_summary_fallback_keeps_central_brain_summary_and_does_not_mutate_chart_facts",
    }


def _thinking_prompt_metadata(prompt: dict[str, object]) -> dict[str, object]:
    if prompt.get("version") in {"v30.thinking_step_summary_prompt.v2", "v30.thinking_step_summary_prompt.v3"}:
        request_context = _dict(prompt.get("context_pack"))
        stage = _dict(request_context.get("stage"))
        evidence_digest = _dict(stage.get("evidence_digest"))
        contract = _dict(prompt.get("prompt_contract"))
        prompt_profile = _dict(prompt.get("stage_prompt_profile")) or _dict(request_context.get("prompt_profile"))
        return {
            "version": prompt.get("version"),
            "task": prompt.get("task"),
            "step_id": prompt.get("step_id") or stage.get("step_id"),
            "stage_prompt_profile_id": prompt_profile.get("profile_id"),
            "stage_prompt_scene": prompt_profile.get("scene"),
            "role_key": request_context.get("role_key"),
            "locale": request_context.get("locale"),
            "client": request_context.get("client"),
            "prompt_contract_id": contract.get("prompt_contract_id"),
            "context_pack_version": request_context.get("version"),
            "context_pack": request_context.get("context_pack"),
            "module_context_count": len(_safe_prompt_rows(request_context.get("module_context"), limit=20)),
            "evidence_digest_count": int(evidence_digest.get("raw_count") or 0),
            "raw_runtime_payload_included": False,
            "chart_fact_mutation_allowed": False,
            "boundary": "thinking_step_prompt_metadata_for_observability_not_raw_context",
        }
    stage = prompt.get("stage", {})
    stage = stage if isinstance(stage, dict) else {}
    evidence_digest = stage.get("evidence_digest", {})
    evidence_digest = evidence_digest if isinstance(evidence_digest, dict) else {}
    return {
        "version": prompt.get("version"),
        "task": prompt.get("task"),
        "step_id": stage.get("step_id"),
        "role_key": prompt.get("role_key"),
        "locale": prompt.get("locale"),
        "client": prompt.get("client"),
        "task_count": len(_safe_prompt_rows(stage.get("tasks"), limit=20)),
        "evidence_digest_count": int(evidence_digest.get("raw_count") or 0),
        "raw_runtime_payload_included": False,
        "chart_fact_mutation_allowed": False,
        "boundary": "thinking_step_prompt_metadata_for_observability_not_raw_context",
    }


def _thinking_prompt_step_id(prompt: dict[str, object]) -> str:
    if prompt.get("step_id"):
        return str(prompt.get("step_id"))
    return str(_dict(prompt.get("stage")).get("step_id") or "")


def _safe_prompt_rows(value: object, *, limit: int) -> list[object]:
    if not isinstance(value, list):
        return []
    return value[:limit]


def _contains_internal_identifier(text: str) -> bool:
    lowered = text.lower()
    forbidden = ("context_id", "evidence_id", "source_id", "v30.", "krp.", "trace_id")
    return any(token in lowered for token in forbidden)


def _trim_summary_text(text: str) -> str:
    clean = " ".join(str(text or "").split())
    limit = 560
    if len(clean) <= limit:
        return clean
    clipped = clean[:limit]
    sentence_end = max(clipped.rfind("。"), clipped.rfind("！"), clipped.rfind("？"))
    if sentence_end >= 120:
        return clipped[:sentence_end + 1]
    return clipped.rstrip("，,；;、") + "。"


def _compact_surface(payload: dict[str, object]) -> dict[str, object]:
    if not isinstance(payload, dict):
        return {}
    summary = payload.get("reading_summary", {})
    next_question = payload.get("next_question", {})
    return {
        "version": payload.get("version"),
        "reading_summary": summary if isinstance(summary, dict) else {},
        "basic_assertions": _compact_rows(payload.get("basic_assertions"), keys=("kind", "assertion", "evidence_labels"), limit=6),
        "domain_cards": _compact_rows(payload.get("domain_cards"), keys=("domain", "diagnosis_summary", "path_summary"), limit=5),
        "bazi_features": _compact_rows(payload.get("bazi_features"), keys=("domain", "label", "statement"), limit=5),
        "bazi_portraits": _compact_rows(payload.get("bazi_portraits"), keys=("domain", "label", "statement"), limit=5),
        "bazi_paths": _compact_rows(payload.get("bazi_paths"), keys=("path_label", "meaning", "domain_impact", "uncertainty_boundary"), limit=5),
        "time_context": payload.get("time_context") if isinstance(payload.get("time_context"), dict) else {},
        "role_contract": payload.get("role_contract") if isinstance(payload.get("role_contract"), dict) else {},
        "next_question": {
            "question_id": next_question.get("question_id"),
            "label": next_question.get("label"),
            "question_value": next_question.get("question_value"),
            "expected_information_gain": next_question.get("expected_information_gain"),
        } if isinstance(next_question, dict) else {},
        "boundary": payload.get("boundary"),
    }


def _compact_rows(value: object, *, keys: tuple[str, ...], limit: int) -> list[dict[str, object]]:
    if not isinstance(value, list):
        return []
    rows: list[dict[str, object]] = []
    for row in value[:limit]:
        if not isinstance(row, dict):
            continue
        rows.append({key: row.get(key) for key in keys if key in row})
    return rows


def _headers(cfg: V30LLMProviderConfig) -> dict[str, str]:
    headers = {"content-type": "application/json"}
    api_key = os.getenv(cfg.api_key_env)
    if api_key:
        headers["authorization"] = f"Bearer {api_key}"
    return headers


def _completion_max_tokens(cfg: V30LLMProviderConfig, *, enable_thinking: bool = False) -> int:
    base = int(cfg.max_tokens or 600)
    if enable_thinking:
        return max(base, 2400)
    return base


def _provider_timeout(cfg: V30LLMProviderConfig, *, enable_thinking: bool = False) -> float:
    timeout = float(cfg.http_timeout_sec or 15.0)
    if enable_thinking:
        return max(timeout, 180.0)
    if cfg.provider.lower() in {"ollama", "ollama_native"}:
        return max(timeout, 1.0)
    return max(timeout, 1.0)


def _llm_sync_mode() -> str:
    return os.getenv("V30_LLM_SYNC_MODE", "blocking").strip().lower() or "blocking"


def _deferred_call_metadata(
    runtime: CoreRuntimeResult,
    answer_context: AnswerContext,
    rule_answer: AnswerResult,
    *,
    reading_surface: dict[str, object],
    task_type: str,
    role_key: str,
    locale: str,
    client: str,
    domain: str,
    config: V30LLMProviderConfig,
) -> dict[str, object]:
    readiness = llm_provider_readiness_report(config)
    try:
        prompt_request = build_bazi_llm_prompt_request(
            runtime,
            task_type=task_type,
            domain=domain,
            role_key=role_key,
            locale=locale,
            client=client,
        )
    except ValueError:
        prompt_request = {}
    return {
        "version": "v30.bazi_llm_answer_draft_call.v1",
        "status": "deferred",
        "fallback_reason": "sync_mode_fast_llm_deferred",
        "executed": False,
        "task_type": task_type,
        "role_key": role_key,
        "locale": locale,
        "client": client,
        "domain": domain,
        "provider": config.provider,
        "model": config.model,
        "sync_mode": _llm_sync_mode(),
        "prompt_request": _prompt_request_metadata(prompt_request) if prompt_request else {},
        "context_pack_summary": _product_context_pack_summary(
            reading_surface,
            task_type=task_type,
            role_key=role_key,
        ),
        "rule_answer_text_length": len(rule_answer.text),
        "llm_execution_required": False,
        "boundary": "fast_sync_mode_returns_rule_bound_rbd_answer_without_waiting_for_llm",
        "readiness": readiness,
    }


def _parse_json_content(content: str) -> dict[str, object]:
    text = content.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:].strip()
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start < 0 or end <= start:
            raise
        payload = json.loads(text[start:end + 1])
    return payload if isinstance(payload, dict) else {}


def _parse_json_or_text(content: str) -> dict[str, object]:
    try:
        return _parse_json_content(content)
    except json.JSONDecodeError:
        return {"text": content.strip()}


def _coerce_bazi_output_schema(
    payload: dict[str, object],
    *,
    prompt_request: dict[str, object],
    rule_answer: AnswerResult,
    domain: str,
) -> dict[str, object]:
    if not isinstance(payload, dict):
        return payload
    contract = prompt_request.get("prompt_contract", {})
    output_schema = contract.get("output_schema", {}) if isinstance(contract, dict) else {}
    required = output_schema.get("required_fields", []) if isinstance(output_schema, dict) else []
    required_fields = {str(row) for row in required} if isinstance(required, list) else set()
    if "answer_text" in payload:
        return payload
    text = str(payload.get("text") or "").strip()
    if not text:
        return payload
    coerced = dict(payload)
    if "answer_text" in required_fields and not str(coerced.get("answer_text") or "").strip():
        coerced["answer_text"] = text
    if "evidence_ids" in required_fields and not coerced.get("evidence_ids"):
        coerced["evidence_ids"] = list(rule_answer.evidence_ids)
    if "boundaries" in required_fields and not coerced.get("boundaries"):
        coerced["boundaries"] = [rule_answer.boundary]
    if "next_question_hint" in required_fields and not str(coerced.get("next_question_hint") or "").strip():
        coerced["next_question_hint"] = "继续确认一个近期反复出现的状态或具体关注方向。"
    if "domain" in required_fields and not str(coerced.get("domain") or "").strip():
        coerced["domain"] = domain or "general"
    if "used_user_signals" in required_fields and not coerced.get("used_user_signals"):
        coerced["used_user_signals"] = [domain or "answer_context"]
    coerced["schema_coercion"] = {
        "version": "v30.bazi_llm_plain_text_schema_coercion.v1",
        "source": "provider_plain_text",
        "chart_fact_mutation_allowed": False,
        "boundary": "plain_text_llm_output_is_wrapped_for_acceptance_without_adding_chart_facts",
    }
    return coerced


def _fallback(
    reason: str,
    readiness: dict[str, object],
    *,
    executed: bool = False,
    drift: dict[str, object] | None = None,
    acceptance: dict[str, object] | None = None,
    text: str = "",
    prompt_request: dict[str, object] | None = None,
    task_type: str = "",
    role_key: str = "",
    product_context_summary: dict[str, object] | None = None,
) -> dict[str, object]:
    prompt_request = prompt_request or {}
    context_pack = prompt_request.get("context_pack", {}) if isinstance(prompt_request, dict) else {}
    return {
        "version": "v30.bazi_llm_answer_draft_call.v1" if prompt_request or task_type else "v30.llm_answer_draft_call.v1",
        "status": "fallback",
        "fallback_reason": reason,
        "text": text,
        "executed": executed,
        "task_type": prompt_request.get("task_type", task_type) if isinstance(prompt_request, dict) else task_type,
        "role_key": context_pack.get("role_key", role_key) if isinstance(context_pack, dict) else role_key,
        "context_pack_summary": product_context_summary or {},
        "prompt_request": _prompt_request_metadata(prompt_request) if prompt_request else {},
        "output_acceptance": acceptance or {},
        "readiness": readiness,
        "drift_check": drift or {},
        "boundary": "llm_fallback_keeps_rule_answer_and_does_not_mutate_chart_facts",
    }


def _product_context_pack_summary(
    reading_surface: dict[str, object],
    *,
    task_type: str,
    role_key: str,
) -> dict[str, object]:
    surface = reading_surface if isinstance(reading_surface, dict) else {}
    layer_specs = (
        ("basic_assertions", surface.get("basic_assertions")),
        ("domain_card", surface.get("domain_cards")),
        ("bazi_features", surface.get("bazi_features")),
        ("bazi_portraits", surface.get("bazi_portraits")),
        ("bazi_paths", surface.get("bazi_paths")),
        ("time_context", surface.get("time_context")),
        ("role_contract", surface.get("role_contract")),
    )
    layers = [name for name, value in layer_specs if _surface_layer_present(value)]
    return {
        "version": "v30.bazi_llm_product_context_pack_summary.v1",
        "task_type": task_type,
        "role_key": role_key,
        "layers": layers,
        "required_layers": [name for name, _value in layer_specs],
        "missing_layers": [name for name, _value in layer_specs if name not in layers],
        "layer_counts": {
            name: len(value) if isinstance(value, list) else 1 if isinstance(value, dict) and value else 0
            for name, value in layer_specs
        },
        "raw_runtime_payload_included": False,
        "chart_fact_mutation_allowed": False,
        "boundary": "llm_product_context_summary_tracks_surface_layers_without_exposing_raw_runtime",
    }


def _surface_layer_present(value: object) -> bool:
    if isinstance(value, list):
        return bool(value)
    if isinstance(value, dict):
        return bool(value)
    return bool(value)


def _prompt_request_metadata(prompt_request: dict[str, object]) -> dict[str, object]:
    if not prompt_request:
        return {}
    contract = prompt_request.get("prompt_contract", {})
    context = prompt_request.get("context_pack", {})
    contract = contract if isinstance(contract, dict) else {}
    context = context if isinstance(context, dict) else {}
    budget = context.get("budget", {})
    role_contract = context.get("role_contract", {})
    sections = context.get("sections", [])
    return {
        "version": prompt_request.get("version"),
        "request_id": prompt_request.get("request_id"),
        "task_type": prompt_request.get("task_type"),
        "prompt_contract_id": contract.get("prompt_contract_id"),
        "context_pack": context.get("context_pack"),
        "context_pack_version": context.get("version"),
        "role_key": context.get("role_key"),
        "locale": context.get("locale"),
        "client": context.get("client"),
        "role_contract_id": role_contract.get("role_contract_id") if isinstance(role_contract, dict) else "",
        "diagnostics_visible": role_contract.get("diagnostics_visible") if isinstance(role_contract, dict) else False,
        "context_section_ids": [
            str(section.get("section_id"))
            for section in sections
            if isinstance(section, dict) and section.get("section_id")
        ] if isinstance(sections, list) else [],
        "included_modules": [
            str(row) for row in context.get("included_modules", [])
        ] if isinstance(context.get("included_modules"), list) else [],
        "excluded_modules": [
            str(row) for row in context.get("excluded_modules", [])
        ] if isinstance(context.get("excluded_modules"), list) else [],
        "budget": budget if isinstance(budget, dict) else {},
        "raw_runtime_payload_included": prompt_request.get("raw_runtime_payload_included", False),
        "chart_fact_mutation_allowed": prompt_request.get("chart_fact_mutation_allowed", False),
        "boundary": "prompt_request_metadata_for_observability_not_raw_context",
    }


def _dict(value: object) -> dict[str, object]:
    return value if isinstance(value, dict) else {}


def _list(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def _bazi_answer_task_type(runtime: CoreRuntimeResult) -> str:
    outcomes = runtime.question_plan.session_state.get("question_outcomes", [])
    if isinstance(outcomes, list) and outcomes:
        return "domain_followup"
    return "customer_initial_reading"


def _selected_domain(runtime: CoreRuntimeResult) -> str:
    interaction = runtime.question_plan.policy_effect.get("interaction_state", {})
    if isinstance(interaction, dict):
        selected = str(interaction.get("selected_domain") or "")
        if selected:
            return selected
    practical = runtime.question_plan.policy_effect.get("practical_reading_context", {})
    if isinstance(practical, dict):
        domain_readings = practical.get("domain_readings", {})
        if isinstance(domain_readings, dict) and domain_readings:
            return str(next(iter(domain_readings)))
    return ""
