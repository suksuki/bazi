"""本地 Qwen（OpenAI 兼容）异步客户端，支持流式输出。"""
from __future__ import annotations

import json
import os
import time
from typing import Any, AsyncIterator, Dict, List, Optional, Tuple

import httpx

from app.core.llm_ollama import looks_like_native_ollama_base_url, merge_ollama_chat_options
from app.core.runtime_config import get_runtime_config

FIRST_OBSERVATION_SYSTEM_PROMPT = (
    "你是子平/干支语境下的分析师（只做 BaziMetadata 字段级观察；禁止西洋十二星座、行星宫位、紫微斗数等本任务未给出的体系）。"
    "收到 JSON 后：不下吉凶/运势/人际后果等结论；只复述 conflict_matrix.points、四柱干支等 JSON 已载信息；"
    "未出现的组合关系一律不得虚构。"
    "若附地理经纬度，仅作地点标注，不得据此发明「与经纬度对撞」「星座」「星象」「天体位置」等机制。"
    "输出固定为两段、总字数约 260 字内："
    "第一段用短句或条列列出观察到的物理冲突点/组合点（仅 JSON 有据可查者；若无点则明确写矩阵当前无探测点）。"
    "第二段仅一句向裁决人提问，须与第一段一致，语义贴近：「我发现 A 与 B 形成××关系，我们是否需要深入分析这个局部？」"
    "其中 A、B 为干支或柱位，×× 与 points[].detail 用词一致。"
    "禁止编号展开（如 1.2.3.）、「建议从以下几方面」「仅供参考」等泛化清单或咨询套话。"
)


class QwenClient:
    """
    对接 OpenAI 兼容 Chat Completions API（如 vLLM、Ollama openai 插件、LM Studio）。

    环境变量::

        QIAZHI_BAZI_LLM_BASE_URL（OpenAI 兼容根路径，通常以 /v1 结尾）
        QIAZHI_BAZI_LLM_API_KEY
        QIAZHI_BAZI_LLM_MODEL
        QIAZHI_OLLAMA_NATIVE_PORTS（可选，逗号分隔；用于判定是否走 Ollama /api/chat）
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

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

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
    lang_u = (lang or "ZH").upper()
    zh_guard = ""
    if lang_u == "ZH":
        zh_guard = (
            "除 JSON 已列字段外不得引入新实体；勿写星座/行星/占星盘/天体运行；"
            "勿把经纬度解释成新的冲合刑害理由；勿输出多段「分析建议」清单。\n"
        )
    return [
        {"role": "system", "content": FIRST_OBSERVATION_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                "以下是 BaziMetadata，请仅做观察与提问，不要给最终判断：\n"
                f"{json.dumps(metadata, ensure_ascii=False)}\n"
                f"{location_hint}\n"
                f"{zh_guard}"
                f"{output_hint.get(lang, output_hint['ZH'])}"
            ),
        },
    ]
