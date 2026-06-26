from __future__ import annotations

import json
import os
import time
import urllib.request
from dataclasses import asdict, dataclass
from typing import Any

from v20.llm.contracts import LLMTaskContract
from v20.llm.provider import LLMProviderConfig, llm_provider_readiness_report, load_llm_provider_config_from_env
from v20.llm.validators import validate_llm_structured_output


class LLMRetryExhausted(Exception):
    def __init__(self, cause: Exception, attempts: int) -> None:
        super().__init__(str(cause))
        self.cause = cause
        self.attempts = attempts


@dataclass(frozen=True)
class LLMStructuredCallResult:
    status: str
    provider: str
    model: str
    task_name: str
    output: dict[str, object]
    validation: dict[str, object]
    fallback_reason: str
    retry_attempts: int = 0
    executed: bool = False
    runtime_mutation: bool = False
    guardrails: tuple[str, ...] = (
        "LLM_CALL_RESULT_IS_DRAFT_ONLY",
        "NO_SECRET_VALUES_RENDERED",
        "DETERMINISTIC_VALIDATOR_REQUIRED",
        "LLM_TRANSPORT_RETRY_BOUNDED",
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def call_structured_llm(
    contract: LLMTaskContract,
    prompt: dict[str, object],
    *,
    config: LLMProviderConfig | None = None,
) -> dict[str, object]:
    cfg = config or load_llm_provider_config_from_env()
    readiness = llm_provider_readiness_report(cfg)
    if not readiness["ready_for_connection"]:
        return _fallback_result(contract, cfg, "provider_not_ready")
    if not cfg.execute_llm:
        return _fallback_result(contract, cfg, "execute_flag_disabled")
    call_error = ""
    retry_attempts = 0
    try:
        if cfg.provider == "ollama_native":
            payload, retry_attempts = _call_with_retries(lambda: _post_ollama_native_completion(contract, prompt, cfg))
        else:
            payload, retry_attempts = _call_with_retries(lambda: _post_chat_completion(contract, prompt, cfg))
    except Exception as exc:
        retry_attempts += _exception_attempts(exc)
        call_error = f"openai_compatible_failed:{_exception_type_name(exc)}"
        if cfg.provider == "ollama":
            try:
                payload, native_attempts = _call_with_retries(lambda: _post_ollama_native_completion(contract, prompt, cfg))
                retry_attempts += native_attempts
            except Exception as native_exc:
                retry_attempts += _exception_attempts(native_exc)
                return _fallback_result(
                    contract,
                    cfg,
                    f"{call_error};ollama_native_failed:{_exception_type_name(native_exc)}",
                    retry_attempts=retry_attempts,
                )
        else:
            return _fallback_result(contract, cfg, f"call_failed:{_exception_type_name(exc)}", retry_attempts=retry_attempts)
    validation = validate_llm_structured_output(contract, payload)
    return LLMStructuredCallResult(
        status="accepted" if validation["ok"] else "rejected",
        provider=cfg.provider,
        model=cfg.model,
        task_name=contract.task_name,
        output=payload if validation["ok"] else {},
        validation=validation,
        fallback_reason=call_error if validation["ok"] else "validation_failed",
        retry_attempts=retry_attempts,
        executed=True,
    ).to_dict()


def stream_plain_llm_text(
    contract: LLMTaskContract,
    prompt: dict[str, object],
    *,
    config: LLMProviderConfig | None = None,
):
    cfg = config or load_llm_provider_config_from_env()
    readiness = llm_provider_readiness_report(cfg)
    if not readiness["ready_for_connection"] or not cfg.execute_llm:
        return
    if cfg.provider not in {"ollama", "ollama_native"}:
        return
    yield from _stream_ollama_native_text(contract, prompt, cfg)


def _post_chat_completion(
    contract: LLMTaskContract,
    prompt: dict[str, object],
    cfg: LLMProviderConfig,
) -> dict[str, object]:
    body = {
        "model": cfg.model,
        "temperature": cfg.temperature,
        "max_tokens": cfg.max_tokens,
        "response_format": {"type": "json_object"},
        "messages": _structured_messages(contract, prompt),
    }
    if cfg.provider == "ollama":
        body["think"] = False
    request = urllib.request.Request(
        f"{cfg.resolved_base_url().rstrip('/')}/chat/completions",
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        headers=_headers(cfg),
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=_compatible_timeout(cfg)) as response:
        raw = response.read().decode("utf-8")
    response_payload = json.loads(raw)
    content = response_payload["choices"][0]["message"]["content"]
    return _parse_json_content(str(content))


def _post_ollama_native_completion(
    contract: LLMTaskContract,
    prompt: dict[str, object],
    cfg: LLMProviderConfig,
) -> dict[str, object]:
    body = {
        "model": cfg.model,
        "messages": _structured_messages(contract, prompt),
        "stream": False,
        "format": "json",
        "think": False,
        "options": {
            "temperature": cfg.temperature,
            "num_predict": cfg.max_tokens,
            "num_ctx": 2048 if contract.task_name == "practitioner_answer" else 4096,
        },
    }
    request = urllib.request.Request(
        f"{cfg.resolved_base_url().rstrip('/').removesuffix('/v1')}/api/chat",
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        headers=_headers(cfg),
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=cfg.http_timeout_sec) as response:
        raw = response.read().decode("utf-8")
    response_payload = json.loads(raw)
    message = response_payload.get("message") if isinstance(response_payload, dict) else {}
    content = ""
    if isinstance(message, dict):
        content = str(message.get("content") or message.get("thinking") or "").strip()
    if not content and isinstance(response_payload, dict):
        content = str(response_payload.get("response") or "").strip()
    return _parse_json_content(content)


def _stream_ollama_native_text(
    contract: LLMTaskContract,
    prompt: dict[str, object],
    cfg: LLMProviderConfig,
):
    body = {
        "model": cfg.model,
        "messages": _plain_text_messages(contract, prompt),
        "stream": True,
        "think": False,
        "options": {
            "temperature": cfg.temperature,
            "num_predict": cfg.max_tokens,
            "num_ctx": 2048 if contract.task_name == "practitioner_answer" else 4096,
        },
    }
    request = urllib.request.Request(
        f"{cfg.resolved_base_url().rstrip('/').removesuffix('/v1')}/api/chat",
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        headers=_headers(cfg),
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=cfg.http_timeout_sec) as response:
        for raw_line in response:
            line = raw_line.decode("utf-8").strip()
            if not line:
                continue
            payload = json.loads(line)
            message = payload.get("message") if isinstance(payload, dict) else {}
            content = str(message.get("content") or "") if isinstance(message, dict) else ""
            if content:
                yield content
            if payload.get("done"):
                break


def _structured_messages(contract: LLMTaskContract, prompt: dict[str, object]) -> list[dict[str, str]]:
    contract_brief = {
        "task_name": contract.task_name,
        "required_outputs": contract.required_outputs,
        "forbidden_outputs": contract.forbidden_outputs,
        "fallback": contract.fallback,
    }
    return [
        {
            "role": "system",
            "content": (
                "You are a bounded Bazi assistant. Return exactly one JSON object in message.content "
                f"with these keys only: {', '.join(contract.required_outputs)}. "
                "Do not echo the input. Do not add chart facts, activate rules, or write unsupported conclusions."
            ),
        },
        {
            "role": "user",
            "content": json.dumps(
                {
                    "contract": contract_brief,
                    "prompt": prompt,
                },
                ensure_ascii=False,
                sort_keys=True,
            ),
        },
    ]


def _plain_text_messages(contract: LLMTaskContract, prompt: dict[str, object]) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": (
                "You are the user's Bazi practitioner. Use only the verified answer card. "
                "Start with a direct conclusion, then evidence, boundary, and next step. "
                "Plain text only; no JSON, markdown headings, internal ids, or unsupported claims."
            ),
        },
        {
            "role": "user",
            "content": json.dumps(_plain_text_prompt_payload(contract, prompt), ensure_ascii=False, sort_keys=True),
        },
    ]


def _plain_text_prompt_payload(contract: LLMTaskContract, prompt: dict[str, object]) -> dict[str, object]:
    if contract.task_name == "practitioner_answer":
        return {
            "task": contract.task_name,
            "locale": prompt.get("locale", "zh"),
            "required_output": "plain_text_only_no_json_no_markdown",
            "answer_contract": _compact_plain_answer_contract(prompt.get("answer_contract", {})),
            "context": prompt.get("context", {}),
            "instruction": prompt.get("instruction", ""),
        }
    return {
        "task": contract.task_name,
        "required_output": "plain_text_only_no_json_no_markdown",
        "prompt": prompt,
    }


def _compact_plain_answer_contract(contract: object) -> dict[str, object]:
    if not isinstance(contract, dict):
        return {}
    return {
        "voice_profile": contract.get("voice_profile", ""),
        "structure": contract.get("structure", ()),
        "required": contract.get("required", ()),
        "forbidden": contract.get("forbidden", ()),
        "length_limit": contract.get("length_limit", ""),
    }


def _headers(cfg: LLMProviderConfig) -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    api_key = os.getenv(cfg.api_key_env, "")
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    return headers


def _compatible_timeout(cfg: LLMProviderConfig) -> float:
    if cfg.provider == "ollama":
        return min(cfg.http_timeout_sec, 8.0)
    return cfg.http_timeout_sec


def _call_with_retries(call):
    attempts = _retry_attempts()
    last_exc: Exception | None = None
    for index in range(attempts):
        try:
            return call(), index + 1
        except Exception as exc:
            last_exc = exc
            if index + 1 >= attempts:
                break
            time.sleep(_retry_backoff_seconds() * (index + 1))
    if last_exc is not None:
        raise LLMRetryExhausted(last_exc, attempts) from last_exc
    raise RuntimeError("llm_retry_exhausted_without_exception")


def _exception_attempts(exc: Exception) -> int:
    if isinstance(exc, LLMRetryExhausted):
        return exc.attempts
    return 0


def _exception_type_name(exc: Exception) -> str:
    if isinstance(exc, LLMRetryExhausted):
        return type(exc.cause).__name__
    return type(exc).__name__


def _retry_attempts() -> int:
    try:
        return max(1, min(4, int(os.getenv("V20_LLM_RETRY_ATTEMPTS", "2"))))
    except ValueError:
        return 2


def _retry_backoff_seconds() -> float:
    try:
        return max(0.0, min(2.0, float(os.getenv("V20_LLM_RETRY_BACKOFF_SEC", "0.15"))))
    except ValueError:
        return 0.15


def _parse_json_content(content: str) -> dict[str, object]:
    try:
        payload = json.loads(content)
    except json.JSONDecodeError:
        for candidate in _json_object_candidates(content):
            try:
                payload = json.loads(candidate)
                break
            except json.JSONDecodeError:
                continue
        else:
            raise
    if not isinstance(payload, dict):
        raise TypeError("LLM structured output must be a JSON object.")
    return payload


def _json_object_candidates(content: str) -> list[str]:
    candidates: list[str] = []
    starts = [index for index, char in enumerate(content) if char == "{"]
    for start in starts:
        depth = 0
        in_string = False
        escaped = False
        for index in range(start, len(content)):
            char = content[index]
            if in_string:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    in_string = False
                continue
            if char == '"':
                in_string = True
            elif char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    candidates.append(content[start : index + 1])
                    break
    return candidates


def _fallback_result(
    contract: LLMTaskContract,
    cfg: LLMProviderConfig,
    reason: str,
    *,
    retry_attempts: int = 0,
) -> dict[str, object]:
    validation = {
        "ok": False,
        "task_name": contract.task_name,
        "failures": [reason],
        "fallback": contract.fallback,
        "guardrails": ["LLM_CALL_SKIPPED_OR_FAILED", "DETERMINISTIC_FALLBACK_REQUIRED"],
    }
    return LLMStructuredCallResult(
        status="fallback",
        provider=cfg.provider,
        model=cfg.model,
        task_name=contract.task_name,
        output={},
        validation=validation,
        fallback_reason=reason,
        retry_attempts=retry_attempts,
    ).to_dict()
