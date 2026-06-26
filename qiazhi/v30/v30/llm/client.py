from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

from v30.contracts import AnswerContext, AnswerResult, CoreRuntimeResult
from v30.llm.acceptance import bazi_llm_output_text, validate_bazi_llm_output_payload
from v30.llm.context import build_llm_role_prompt_context
from v30.llm.drift import check_llm_answer_drift
from v30.llm.prompt_registry import build_bazi_llm_prompt_request
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
            payload = _post_ollama_native_completion(prompt, cfg)
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
        "readiness": readiness,
        "drift_check": drift.model_dump(mode="json"),
        "boundary": "bazi_llm_answer_draft_expression_only_no_chart_fact_mutation",
    }


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


def _post_chat_completion(prompt: dict[str, object], cfg: V30LLMProviderConfig) -> dict[str, object]:
    body = {
        "model": cfg.model,
        "temperature": cfg.temperature,
        "max_tokens": cfg.max_tokens,
        "response_format": {"type": "json_object"},
        "messages": _messages(prompt),
    }
    if cfg.provider.lower() == "ollama":
        body["think"] = False
    request = urllib.request.Request(
        f"{cfg.resolved_base_url().rstrip('/')}/chat/completions",
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        headers=_headers(cfg),
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=_provider_timeout(cfg)) as response:
        raw = response.read().decode("utf-8")
    response_payload = json.loads(raw)
    content = response_payload["choices"][0]["message"]["content"]
    return _parse_json_or_text(str(content))


def _post_ollama_native_completion(prompt: dict[str, object], cfg: V30LLMProviderConfig) -> dict[str, object]:
    body = {
        "model": cfg.model,
        "messages": _messages(prompt),
        "stream": False,
        "format": "json",
        "think": False,
        "options": {
            "temperature": cfg.temperature,
            "num_predict": cfg.max_tokens,
        },
    }
    request = urllib.request.Request(
        f"{cfg.resolved_base_url().rstrip('/').removesuffix('/v1')}/api/chat",
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        headers=_headers(cfg),
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=_provider_timeout(cfg)) as response:
        raw = response.read().decode("utf-8")
    response_payload = json.loads(raw)
    message = response_payload.get("message") if isinstance(response_payload, dict) else {}
    content = str(message.get("content") or "") if isinstance(message, dict) else ""
    return _parse_json_or_text(content)


def _messages(prompt: dict[str, object]) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": (
                "You are V30's bounded Bazi expression layer. Return exactly one JSON object with key text. "
                "Use only the provided deterministic chart summary, answer context, customer surface, and rule answer. "
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
                "boundary notes, or phrases like 复核、边界、不能直接断定、后续我们可以. "
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
                "Avoid phrases like 复核、边界、不能直接断定、后续我们可以. "
                "Put any next-step prompt only in next_question_hint or structured fields, not in answer_text. "
                "Match role_contract terminology. No markdown, no internal ids."
            ),
        },
        "forbidden": answer_context.forbidden_drift,
        "boundary": "bazi_task_role_context_prompt_for_llm_expression_only_not_chart_fact_source",
    }


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


def _provider_timeout(cfg: V30LLMProviderConfig) -> float:
    timeout = float(cfg.http_timeout_sec or 15.0)
    if cfg.provider.lower() in {"ollama", "ollama_native"}:
        return max(timeout, 1.0)
    return max(timeout, 1.0)


def _llm_sync_mode() -> str:
    return os.getenv("V30_LLM_SYNC_MODE", "fast").strip().lower() or "fast"


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
