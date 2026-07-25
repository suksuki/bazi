from __future__ import annotations

import json
import os
import re
import socket
import threading
import time
import urllib.error
import urllib.request
from typing import Any, Callable, Protocol, TypeVar

from pydantic import BaseModel


T = TypeVar("T", bound=BaseModel)
_MODEL_LOCKS: dict[str, threading.Lock] = {}
_MODEL_LOCKS_GUARD = threading.Lock()


class CognitiveModel(Protocol):
    model: str

    def generate(
        self,
        *,
        prompt: str,
        schema: type[T],
        temperature: float = 0.2,
        thinking: bool = True,
        max_tokens: int = 3200,
        on_text_chunk: Callable[[str], None] | None = None,
    ) -> T: ...

class OllamaCognitiveModel:
    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        timeout_seconds: int = 180,
        num_ctx: int = 32768,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.num_ctx = num_ctx
        self._local = threading.local()
        with _MODEL_LOCKS_GUARD:
            self._request_lock = _MODEL_LOCKS.setdefault(f"{self.base_url}|{self.model}", threading.Lock())

    def generate(
        self,
        *,
        prompt: str,
        schema: type[T],
        temperature: float = 0.2,
        thinking: bool = True,
        max_tokens: int = 3200,
        on_text_chunk: Callable[[str], None] | None = None,
    ) -> T:
        self._local.last_metrics = {}
        self._local.last_raw_response = ""
        schema_json = json.dumps(schema.model_json_schema(), ensure_ascii=False, separators=(",", ":"))
        base_prompt = f"{prompt}\n\n输出必须是单个 JSON 对象，严格符合以下 JSON Schema，不要 Markdown：\n{schema_json}"
        last_error: Exception | None = None
        raw = ""
        # A second full model call is too expensive for an interactive reading. Recover
        # locally when possible and surface an unrecoverable schema error immediately.
        schema_attempts = 1
        with self._request_lock:
            for attempt in range(schema_attempts):
                attempt_prompt = base_prompt
                if attempt:
                    attempt_prompt += "\n上一次输出没有形成完整 JSON。请压缩解释长度，确保所有括号和字符串闭合，优先保证结构完整。"
                payload = {
                    "model": self.model,
                    "prompt": attempt_prompt,
                    "stream": on_text_chunk is not None,
                    "think": thinking,
                    "format": schema.model_json_schema(),
                    "options": {
                        "temperature": temperature if attempt == 0 else 0.0,
                        "top_p": 0.9 if attempt == 0 else 0.75,
                        "top_k": 30,
                        "num_ctx": self.num_ctx,
                        "num_predict": max_tokens,
                        "repeat_penalty": 1.08,
                    },
                    "keep_alive": "30m",
                }
                request = urllib.request.Request(
                    f"{self.base_url}/api/generate",
                    data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                try:
                    with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:  # noqa: S310 - configured local model.
                        if on_text_chunk is None:
                            body = json.loads(response.read().decode("utf-8"))
                            raw = str(body.get("response") or body.get("thinking") or "{}").strip()
                        else:
                            body, raw = _read_streaming_ollama_response(
                                response=response,
                                on_text_chunk=on_text_chunk,
                            )
                except (urllib.error.URLError, TimeoutError, socket.timeout, json.JSONDecodeError) as exc:
                    # Replaying an expensive cognitive request does not repair transport failure and
                    # can turn one visible timeout into several minutes of silent waiting.
                    last_error = exc
                    break
                self._local.last_metrics = _ollama_metrics(
                    body=body,
                    schema_attempts=attempt + 1,
                    response_bytes=len(raw.encode("utf-8")),
                )
                self._local.last_raw_response = raw
                try:
                    return _validate_model_json(raw=raw, schema=schema)
                except (ValueError, TypeError) as exc:
                    last_error = exc
                    if attempt + 1 < schema_attempts:
                        time.sleep(0.5)
                        continue
                    break
        error_detail = f"{type(last_error).__name__}:{last_error}" if last_error else "unknown_model_error"
        self._local.last_metrics = {
            "schema_attempts": min(schema_attempts, attempt + 1),
            "response_bytes": len(raw.encode("utf-8")),
        }
        self._local.last_raw_response = raw
        raise ValueError(f"model_generation_failed:{error_detail}:{raw[:1600]}") from last_error

    @property
    def last_metrics(self) -> dict[str, Any]:
        return dict(getattr(self._local, "last_metrics", {}))

    @property
    def last_raw_response(self) -> str:
        """Expose the latest model payload for local audit; product storage never reads it."""

        return str(getattr(self._local, "last_raw_response", ""))

def _read_streaming_ollama_response(
    *,
    response: Any,
    on_text_chunk: Callable[[str], None],
) -> tuple[dict[str, Any], str]:
    response_chunks: list[str] = []
    thinking_chunks: list[str] = []
    final_body: dict[str, Any] = {}
    for raw_line in response:
        line = raw_line.decode("utf-8") if isinstance(raw_line, bytes) else str(raw_line)
        if not line.strip():
            continue
        item = json.loads(line)
        final_body = item
        response_part = str(item.get("response") or "")
        thinking_part = str(item.get("thinking") or "")
        if response_part:
            response_chunks.append(response_part)
            on_text_chunk(response_part)
        elif thinking_part:
            thinking_chunks.append(thinking_part)
    raw = "".join(response_chunks) or "".join(thinking_chunks) or "{}"
    return final_body, raw.strip()

def _ollama_metrics(*, body: dict[str, Any], schema_attempts: int, response_bytes: int) -> dict[str, Any]:
    def duration_ms(key: str) -> int | None:
        value = body.get(key)
        return round(value / 1_000_000) if isinstance(value, (int, float)) else None

    return {
        "transport_total_ms": duration_ms("total_duration"),
        "load_duration_ms": duration_ms("load_duration"),
        "prompt_eval_count": body.get("prompt_eval_count") if isinstance(body.get("prompt_eval_count"), int) else None,
        "prompt_eval_duration_ms": duration_ms("prompt_eval_duration"),
        "eval_count": body.get("eval_count") if isinstance(body.get("eval_count"), int) else None,
        "eval_duration_ms": duration_ms("eval_duration"),
        "schema_attempts": schema_attempts,
        "response_bytes": response_bytes,
    }

def default_reasoning_model() -> CognitiveModel:
    return OllamaCognitiveModel(
        base_url=os.getenv("V50_MINGLI_AGENT_BASE_URL", "http://dblife.com:11888"),
        model=os.getenv("V50_MINGLI_AGENT_MODEL", "qwen3.5:35b"),
        timeout_seconds=int(os.getenv("V50_MINGLI_AGENT_TIMEOUT_SECONDS", "180")),
        num_ctx=int(os.getenv("V50_MINGLI_AGENT_NUM_CTX", "32768")),
    )

def default_pattern_model() -> CognitiveModel:
    return OllamaCognitiveModel(
        base_url=os.getenv("V50_MINGLI_AGENT_BASE_URL", "http://dblife.com:11888"),
        model=os.getenv("V50_MINGLI_PATTERN_MODEL", os.getenv("V50_MINGLI_AGENT_MODEL", "qwen3.5:35b")),
        timeout_seconds=int(os.getenv("V50_MINGLI_AGENT_TIMEOUT_SECONDS", "240")),
        num_ctx=int(os.getenv("V50_MINGLI_AGENT_NUM_CTX", "32768")),
    )

def default_work_model() -> CognitiveModel:
    return OllamaCognitiveModel(
        base_url=os.getenv("V50_MINGLI_AGENT_BASE_URL", "http://dblife.com:11888"),
        model=os.getenv("V50_MINGLI_WORK_MODEL", os.getenv("V50_MINGLI_AGENT_MODEL", "qwen3.5:35b")),
        timeout_seconds=int(os.getenv("V50_MINGLI_AGENT_TIMEOUT_SECONDS", "180")),
        num_ctx=int(os.getenv("V50_MINGLI_AGENT_NUM_CTX", "32768")),
    )

def default_domain_model() -> CognitiveModel:
    return OllamaCognitiveModel(
        base_url=os.getenv("V50_MINGLI_AGENT_BASE_URL", "http://dblife.com:11888"),
        model=os.getenv("V50_MINGLI_DOMAIN_MODEL", os.getenv("V50_MINGLI_AGENT_MODEL", "qwen3.5:35b")),
        timeout_seconds=int(os.getenv("V50_MINGLI_AGENT_TIMEOUT_SECONDS", "180")),
        num_ctx=int(os.getenv("V50_MINGLI_DOMAIN_NUM_CTX", "32768")),
    )

def _normalize_json_object(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key).strip(): _normalize_json_object(child) for key, child in value.items()}
    if isinstance(value, list):
        return [_normalize_json_object(item) for item in value]
    return value

def _validate_model_json(*, raw: str, schema: type[T]) -> T:
    try:
        return schema.model_validate(_normalize_json_object(json.loads(raw)))
    except Exception as first_error:
        match = re.search(r"\{.*\}", raw, flags=re.DOTALL)
        if not match:
            raise ValueError(f"model_json_missing:{raw[:1200]}") from first_error
        try:
            return schema.model_validate(_normalize_json_object(json.loads(match.group(0))))
        except Exception as second_error:
            raise ValueError(f"model_json_invalid:{raw[:1600]}") from second_error
