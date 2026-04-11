"""本地 Qwen（OpenAI 兼容）异步客户端，支持流式输出。"""
from __future__ import annotations

import json
import os
import time
from typing import Any, AsyncIterator, Dict, List, Optional, Tuple

import httpx
from urllib.parse import urlparse

FIRST_OBSERVATION_SYSTEM_PROMPT = (
    "你现在是一个逻辑严密的命理分析师。"
    "当你收到 BaziMetadata 时，不要直接下结论。"
    "请先列出你观察到的物理冲突点/组合点，"
    "最后向裁决人发起引导提问："
    "“我发现 A 与 B 正在对撞，我们是否需要深入分析这个局部？”"
)


class QwenClient:
    """
    对接 OpenAI 兼容 Chat Completions API（如 vLLM、Ollama openai 插件、LM Studio）。

    环境变量::

        QIAZHI_BAZI_LLM_BASE_URL=http://192.168.0.10:8000/v1
        QIAZHI_BAZI_LLM_API_KEY=empty
        QIAZHI_BAZI_LLM_MODEL=Qwen/Qwen2.5-32B-Instruct
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout_s: float = 120.0,
    ) -> None:
        self.base_url = (base_url or os.getenv("QIAZHI_BAZI_LLM_BASE_URL", "http://192.168.0.10:8000/v1")).rstrip("/")
        self.api_key = api_key or os.getenv("QIAZHI_BAZI_LLM_API_KEY", "empty")
        self.model = model or os.getenv("QIAZHI_BAZI_LLM_MODEL", "qwen")
        self._timeout = timeout_s

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _is_ollama(self) -> bool:
        try:
            p = urlparse(self.base_url)
            return p.port == 11434 or "11434" in self.base_url
        except Exception:
            return False

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
        对 Ollama 推理模型强制关闭思考输出，直接取结论。
        """
        url = f"{self._ollama_root()}/api/chat"
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "think": False,
            "options": {"temperature": temperature, "num_predict": max_tokens},
        }
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            r = await client.post(url, json=payload)
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
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            r = await client.post(url, headers=self._headers(), json=payload)
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
        async with httpx.AsyncClient(timeout=self._timeout) as client:
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
    metadata: Dict[str, Any],
    location_hint: str = "",
    lang: str = "ZH",
) -> List[Dict[str, str]]:
    """生成首轮“只观察不下结论”的提示词。"""
    output_hint = {
        "ZH": "请仅使用中文输出。",
        "EN": "Please output strictly in English. Use standard academic Pinyin for specific Chinese metaphysics terms if no direct English equivalent exists.",
        "KO": "최종 출력은 반드시 한국어로만 작성하세요.",
    }
    return [
        {"role": "system", "content": FIRST_OBSERVATION_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                "以下是 BaziMetadata，请仅做观察与提问，不要给最终判断：\n"
                f"{json.dumps(metadata, ensure_ascii=False)}\n"
                f"{location_hint}\n"
                f"{output_hint.get(lang, output_hint['ZH'])}"
            ),
        },
    ]
