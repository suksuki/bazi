from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from v40.contracts.output import LLMExpressionResult, LLMExpressionTask
from v40.contracts.runtime import RuntimeResult


class OllamaExpressionError(RuntimeError):
    pass


@dataclass(frozen=True)
class OllamaExpressionConfig:
    provider: str
    host: str
    port: int
    model: str
    timeout_seconds: float
    temperature: float
    max_tokens: int
    enabled: bool
    execute: bool

    @property
    def base_url(self) -> str:
        normalized = self.host.strip()
        if normalized.startswith("http://") or normalized.startswith("https://"):
            return normalized.rstrip("/")
        return f"http://{normalized}:{self.port}".rstrip("/")

    @property
    def effective_thinking_max_tokens(self) -> int:
        return _completion_max_tokens(self, enable_thinking=True)

    @property
    def effective_thinking_timeout_seconds(self) -> float:
        return _provider_timeout(self, enable_thinking=True)


def resolve_ollama_expression_config() -> OllamaExpressionConfig:
    return OllamaExpressionConfig(
        provider=os.getenv("V40_LLM_PROVIDER", "ollama_native"),
        host=os.getenv("V40_LLM_HOST", "127.0.0.1"),
        port=_int_env("V40_LLM_PORT", 11434),
        model=os.getenv("V40_LLM_MODEL", "gemma4:latest"),
        timeout_seconds=_float_env("V40_LLM_HTTP_TIMEOUT_SEC", 30.0),
        temperature=_float_env("V40_LLM_TEMPERATURE", 0.2),
        max_tokens=_int_env("V40_LLM_MAX_TOKENS", 600),
        enabled=_bool_env("V40_LLM_ENABLED", True),
        execute=_bool_env("V40_LLM_EXECUTE", True),
    )


def render_ollama_expression_result(
    *,
    result_id: str,
    task: LLMExpressionTask,
    runtime: RuntimeResult,
    config: OllamaExpressionConfig | None = None,
    transport: Callable[[str, dict[str, object], float], dict[str, object]] | None = None,
) -> LLMExpressionResult:
    resolved = config or resolve_ollama_expression_config()
    if not resolved.enabled or not resolved.execute:
        raise OllamaExpressionError("V40 LLM execution is disabled")
    prompt = build_ollama_expression_prompt(task=task, runtime=runtime)
    payload = {
        "model": resolved.model,
        "messages": _messages(prompt),
        "stream": False,
        "think": True,
        "options": {
            "temperature": resolved.temperature,
            "num_predict": _completion_max_tokens(resolved, enable_thinking=True),
        },
    }
    response_payload = (transport or _post_json)(
        f"{resolved.base_url}/api/chat",
        payload,
        _provider_timeout(resolved, enable_thinking=True),
    )
    text = _extract_response_text(response_payload)
    thinking = _extract_thinking(response_payload)
    return LLMExpressionResult(
        result_id=result_id,
        task_id=task.task_id,
        reading_id=runtime.reading_id,
        text=text,
        raw_thinking=thinking,
        provider=resolved.provider,
        model=str(response_payload.get("model") or resolved.model),
    )


def list_ollama_models(
    *,
    config: OllamaExpressionConfig | None = None,
    transport: Callable[[str, dict[str, object], float], dict[str, object]] | None = None,
) -> dict[str, object]:
    resolved = config or resolve_ollama_expression_config()
    if not resolved.enabled:
        raise OllamaExpressionError("V40 LLM provider is disabled")
    response_payload = (transport or _get_json)(
        f"{resolved.base_url}/api/tags",
        {},
        _provider_timeout(resolved, enable_thinking=False),
    )
    models = _extract_model_names(response_payload)
    return {
        "version": "v40.ollama_model_discovery.v1",
        "provider": resolved.provider,
        "base_url": resolved.base_url,
        "configured_model": resolved.model,
        "model_count": len(models),
        "models": models,
        "configured_model_available": resolved.model in models,
        "writes_v30_state": False,
        "writes_v40_production": False,
        "boundary": "ollama_model_discovery_reads_provider_catalog_without_runtime_mutation",
    }


def build_ollama_expression_prompt(*, task: LLMExpressionTask, runtime: RuntimeResult) -> str:
    projection = runtime.product_projection
    verdict_lines: list[str] = []
    advice_lines: list[str] = []
    branch_lines: list[str] = []
    if projection:
        for card in projection.verdict_cards:
            verdict_lines.append(f"- {card.title}: {card.primary_text}")
        for card in projection.advice_cards:
            for point in card.action_points:
                advice_lines.append(f"- {point}")
            for point in card.avoid_points:
                advice_lines.append(f"- 注意: {point}")
            for point in card.condition_points:
                advice_lines.append(f"- 校准: {point}")
        if task.role_key == "practitioner":
            for card in projection.branch_cards:
                branch_lines.append(f"- {card.title}: {card.practitioner_summary}")
    return "\n".join(
        [
            "你是掐指一算 V40 的表达层，只负责把已给出的结论和建议改写成自然中文。",
            "严禁改变结论，严禁新增命盘事实，严禁新增年份断语，严禁使用工程语言。",
            "输出只包含用户可读内容，优先结论和建议，简洁、有边界、有行动感。",
            "必须至少逐字保留一条“允许表达的断言”或一条“建议卡片”内容，用来证明没有改写核心判断。",
            "",
            "表达指令:",
            task.instruction,
            "",
            "允许表达的断言:",
            *_bullet_lines(task.allowed_assertions),
            "",
            "禁止表达的断言:",
            *_bullet_lines(task.forbidden_assertions),
            "",
            "结论卡片:",
            *(verdict_lines or ["- 暂无结论卡片"]),
            "",
            "建议卡片:",
            *(advice_lines or ["- 暂无建议卡片"]),
            "",
            "命理师分支，仅命理师可见:",
            *(branch_lines or ["- 无"]),
            "",
            "请输出:",
            "结论",
            "- ...",
            "建议",
            "- ...",
            "校准",
            "- ...",
        ]
    )


def _post_json(url: str, payload: dict[str, object], timeout_seconds: float) -> dict[str, object]:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raise OllamaExpressionError(f"Ollama request failed with HTTP {exc.code}") from exc
    except URLError as exc:
        raise OllamaExpressionError(f"Ollama is unreachable: {exc.reason}") from exc
    except TimeoutError as exc:
        raise OllamaExpressionError("Ollama request timed out") from exc
    except json.JSONDecodeError as exc:
        raise OllamaExpressionError("Ollama returned invalid JSON") from exc


def _get_json(url: str, _payload: dict[str, object], timeout_seconds: float) -> dict[str, object]:
    request = Request(url, headers={"Content-Type": "application/json"}, method="GET")
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raise OllamaExpressionError(f"Ollama request failed with HTTP {exc.code}") from exc
    except URLError as exc:
        raise OllamaExpressionError(f"Ollama is unreachable: {exc.reason}") from exc
    except TimeoutError as exc:
        raise OllamaExpressionError("Ollama request timed out") from exc
    except json.JSONDecodeError as exc:
        raise OllamaExpressionError("Ollama returned invalid JSON") from exc


def _extract_model_names(payload: dict[str, object]) -> list[str]:
    rows = payload.get("models")
    if not isinstance(rows, list):
        return []
    names: list[str] = []
    for row in rows:
        name = ""
        if isinstance(row, dict):
            name = str(row.get("name") or row.get("model") or row.get("id") or "").strip()
        elif isinstance(row, str):
            name = row.strip()
        if name and name not in names:
            names.append(name)
    return names


def _extract_response_text(payload: dict[str, object]) -> str:
    response = payload.get("response")
    if isinstance(response, str) and response.strip():
        return _visible_text(response)
    message = payload.get("message")
    if isinstance(message, dict):
        content = message.get("content")
        if isinstance(content, str) and content.strip():
            return _visible_text(content)
    done_reason = str(payload.get("done_reason") or "")
    if done_reason == "length":
        raise OllamaExpressionError("Ollama response did not contain visible text; thinking token budget was exhausted")
    raise OllamaExpressionError("Ollama response did not contain visible text")


def _extract_thinking(payload: dict[str, object]) -> str:
    thinking = payload.get("thinking")
    if isinstance(thinking, str):
        return thinking.strip()
    message = payload.get("message")
    if isinstance(message, dict):
        thinking_content = message.get("thinking") or message.get("reasoning_content")
        if isinstance(thinking_content, str):
            return thinking_content.strip()
        content = message.get("content")
        if isinstance(content, str):
            return _embedded_thinking(content)
    return ""


def _messages(prompt: str) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": (
                "You are V40's bounded Bazi expression layer. Use only the provided product cards. "
                "Do not create pillars, luck cycles, flow years, event years, hidden-factor facts, or fixed promises. "
                "Return customer-visible Chinese text, not diagnostics."
            ),
        },
        {"role": "user", "content": prompt},
    ]


def _completion_max_tokens(config: OllamaExpressionConfig, *, enable_thinking: bool = False) -> int:
    base = int(config.max_tokens or 600)
    if enable_thinking:
        return max(base, 2400)
    return base


def _provider_timeout(config: OllamaExpressionConfig, *, enable_thinking: bool = False) -> float:
    base = float(config.timeout_seconds or 30.0)
    if enable_thinking:
        return max(base, 180.0)
    return max(base, 1.0)


def _visible_text(content: str) -> str:
    text = _strip_embedded_thinking(content).strip()
    if not text:
        return ""
    parsed = _parse_json_text(text)
    if parsed:
        return parsed
    return _strip_json_fence(text).strip()


def _parse_json_text(text: str) -> str:
    candidate = _strip_json_fence(text).strip()
    if "{" not in candidate or "}" not in candidate:
        return ""
    start = candidate.find("{")
    end = candidate.rfind("}")
    if end <= start:
        return ""
    try:
        payload = json.loads(candidate[start : end + 1])
    except json.JSONDecodeError:
        return ""
    if not isinstance(payload, dict):
        return ""
    for key in ("text", "accepted_text", "answer_text", "summary", "body"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _strip_json_fence(text: str) -> str:
    clean = text.strip()
    if not clean.startswith("```"):
        return clean
    clean = clean.strip("`").strip()
    if clean.startswith("json"):
        clean = clean[4:].strip()
    return clean


def _embedded_thinking(content: str) -> str:
    match = re.search(r"<think>(.*?)</think>", content, flags=re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else ""


def _strip_embedded_thinking(content: str) -> str:
    return re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL | re.IGNORECASE)


def _bullet_lines(rows: list[str]) -> list[str]:
    return [f"- {row}" for row in rows if row.strip()] or ["- 无"]


def _bool_env(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _int_env(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


def _float_env(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except ValueError:
        return default
