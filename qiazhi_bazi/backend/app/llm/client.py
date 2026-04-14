"""本地 Qwen（OpenAI 兼容）异步客户端，支持流式输出。"""
from __future__ import annotations

import asyncio
import json
import os
import time
from typing import Any, AsyncIterator, Dict, List, Optional, Tuple

import httpcore
import httpx

from app.core.llm_ollama import looks_like_native_ollama_base_url, merge_ollama_chat_options
from app.core.runtime_config import get_runtime_config
from app.prompts.first_observation import FIRST_OBSERVATION_SYSTEM_PROMPT
from app.prompts.language import LanguageEngine
from app.utils.semantic_firewall import strip_float_literals

# FIRST_OBSERVATION_SYSTEM_PROMPT 仍可从本模块 import（定义见 app.prompts.first_observation）


class QwenClient:
    """
    对接 OpenAI 兼容 Chat Completions API（如 vLLM、Ollama openai 插件、LM Studio）。

    环境变量::

        QIAZHI_BAZI_LLM_BASE_URL（OpenAI 兼容根路径，通常以 /v1 结尾）
        QIAZHI_BAZI_LLM_API_KEY
        QIAZHI_BAZI_LLM_MODEL
        QIAZHI_OLLAMA_NATIVE_PORTS（可选，逗号分隔；用于判定是否走 Ollama /api/chat）
        QIAZHI_LLM_HTTP_RETRIES（可选，默认 3）：对 httpx 传输层瞬时错误（含 LocalProtocolError）重试次数。
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout_s: float = 120.0,
    ) -> None:
        self.base_url = (base_url or os.getenv("QIAZHI_BAZI_LLM_BASE_URL", "") or "").rstrip("/")
        self.api_key = api_key if api_key is not None else (os.getenv("QIAZHI_BAZI_LLM_API_KEY", "") or "")
        self.model = model or os.getenv("QIAZHI_BAZI_LLM_MODEL", "")
        self._timeout = timeout_s

    def _transport_retry_attempts(self) -> int:
        raw = (os.getenv("QIAZHI_LLM_HTTP_RETRIES", "") or "3").strip()
        try:
            n = int(raw)
        except ValueError:
            n = 3
        return max(1, min(5, n))

    def _async_client(self) -> httpx.AsyncClient:
        # 显式 HTTP/1.1：部分反向代理 / 推理服务在 h2 或连接复用上会触发 LocalProtocolError
        return httpx.AsyncClient(
            timeout=self._timeout,
            http2=False,
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=20),
        )

    async def _post_json_with_transport_retry(
        self,
        url: str,
        *,
        headers: Dict[str, str],
        json_body: Dict[str, Any],
    ) -> httpx.Response:
        attempts = self._transport_retry_attempts()
        last: BaseException | None = None
        for i in range(attempts):
            try:
                async with self._async_client() as client:
                    return await client.post(url, headers=headers, json=json_body)
            except (httpx.TimeoutException, httpx.TransportError, httpcore.ProtocolError) as exc:
                last = exc
                if i + 1 >= attempts:
                    raise
                await asyncio.sleep(0.2 * (2**i))
        assert last is not None
        raise last

    def _headers(self) -> Dict[str, str]:
        # 空 api_key 时禁止发送「Authorization: Bearer 」——httpx/httpcore 会报 Illegal header value（日志里误显为 LocalProtocolError）
        h: Dict[str, str] = {"Content-Type": "application/json"}
        key = (self.api_key or "").strip()
        if key:
            h["Authorization"] = f"Bearer {key}"
        return h

    def _is_ollama(self) -> bool:
        return looks_like_native_ollama_base_url(self.base_url)

    def _ollama_root(self) -> str:
        root = self.base_url.rstrip("/")
        if root.endswith("/v1"):
            root = root[:-3]
        return root

    async def _chat_via_ollama_native(
        self,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
    ) -> Optional[str]:
        """
        Ollama 原生 /api/chat（非流式）。默认不传 think（与常见指令模型一致）；
        需 think:false 时设环境变量 QIAZHI_OLLAMA_CHAT_THINK_FALSE=1。
        """
        url = f"{self._ollama_root()}/api/chat"
        cfg = get_runtime_config().get("llm") or {}
        ro = cfg.get("ollama_options") if isinstance(cfg, dict) else None
        runtime_opts = ro if isinstance(ro, dict) else None
        opts = merge_ollama_chat_options(
            temperature=temperature,
            num_predict=max_tokens,
            request_options=None,
            runtime_options=runtime_opts,
        )
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": opts,
        }
        if (os.getenv("QIAZHI_OLLAMA_CHAT_THINK_FALSE", "") or "").lower() in ("1", "true", "yes"):
            payload["think"] = False
        r = await self._post_json_with_transport_retry(url, headers={}, json_body=payload)
        if r.status_code >= 400:
            return None
        data = r.json()
        content = ((data.get("message") or {}).get("content") or "").strip()
        return content or None

    def _telemetry_from_text(self, text: str, elapsed_ms: float, usage: Any) -> Dict[str, Any]:
        approx = round(len(text) / 1.8, 2) if text else 0.0
        u: Dict[str, Any] = {}
        if isinstance(usage, dict):
            u = {k: usage.get(k) for k in ("prompt_tokens", "completion_tokens", "total_tokens") if usage.get(k) is not None}
        return {
            "elapsed_ms": round(float(elapsed_ms), 2),
            "approx_tokens": float(approx),
            "usage": u,
        }

    async def chat_with_telemetry(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.4,
        max_tokens: int = 2048,
        stop: Optional[List[str]] = None,
    ) -> Tuple[str, Dict[str, Any]]:
        t0 = time.perf_counter()
        usage: Any = None
        if self._is_ollama():
            native = await self._chat_via_ollama_native(messages, temperature, max_tokens)
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            if native:
                return native, self._telemetry_from_text(native, elapsed_ms, usage)
            # fall through to OpenAI-compatible path
        url = f"{self.base_url}/chat/completions"
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }
        if stop:
            payload["stop"] = stop
        r = await self._post_json_with_transport_retry(url, headers=self._headers(), json_body=payload)
        r.raise_for_status()
        data = r.json()
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        usage = data.get("usage") if isinstance(data, dict) else None
        choice = (data.get("choices") or [{}])[0]
        msg = choice.get("message") or {}
        content = (msg.get("content") or "").strip()
        if content:
            return content, self._telemetry_from_text(content, elapsed_ms, usage)
        reasoning = (msg.get("reasoning") or msg.get("reasoning_content") or "").strip()
        if reasoning:
            return reasoning, self._telemetry_from_text(reasoning, elapsed_ms, usage)
        text = (choice.get("text") or "").strip()
        if text:
            return text, self._telemetry_from_text(text, elapsed_ms, usage)
        return "", self._telemetry_from_text("", elapsed_ms, usage)

    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.4,
        max_tokens: int = 2048,
        stop: Optional[List[str]] = None,
    ) -> str:
        text, _ = await self.chat_with_telemetry(
            messages, temperature=temperature, max_tokens=max_tokens, stop=stop
        )
        return text

    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.4,
        max_tokens: int = 2048,
        stop: Optional[List[str]] = None,
    ) -> AsyncIterator[str]:
        """逐块产出 assistant 文本增量（OpenAI SSE 格式）。"""
        url = f"{self.base_url}/chat/completions"
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }
        if stop:
            payload["stop"] = stop
        async with self._async_client() as client:
            async with client.stream("POST", url, headers=self._headers(), json=payload) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line or not line.startswith("data: "):
                        continue
                    raw = line.removeprefix("data: ").strip()
                    if raw == "[DONE]":
                        break
                    try:
                        obj = json.loads(raw)
                    except json.JSONDecodeError:
                        continue
                    delta = obj.get("choices", [{}])[0].get("delta", {})
                    piece = delta.get("content") or delta.get("reasoning") or delta.get("reasoning_content")
                    if piece:
                        yield piece


def build_first_observation_messages(
    node_context: str,
    location_hint: str = "",
    lang: str = "ZH",
    *,
    semantic_label_json: str | None = None,
) -> List[Dict[str, str]]:
    """V12.2 Nano-Prompting：只允许注入节点级窄带上下文。"""
    label_block = (semantic_label_json or "").strip()
    node_line = str(node_context or "").strip()[:100]
    user_raw = (
        (f"{label_block}\n\n" if label_block else "")
        + "Node_Chain_Execution: 仅将以下节点描述翻译为自然语言，不扩展、不断盘、不引入新事实。\n"
        f"NODE_CONTEXT: {node_line}\n"
        f"{location_hint}\n"
        f"{LanguageEngine.first_observation_output_hint(lang)}"
    )
    user_raw = user_raw[:170]
    return [
        {"role": "system", "content": strip_float_literals(FIRST_OBSERVATION_SYSTEM_PROMPT)},
        {"role": "user", "content": strip_float_literals(user_raw)},
    ]
