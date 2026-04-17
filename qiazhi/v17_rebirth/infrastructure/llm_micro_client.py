from __future__ import annotations

import asyncio
import base64
import json
from dataclasses import dataclass
from urllib import request

from .llm_bridge import V17LlmBridge


@dataclass
class V17MicroLlmClient:
    """OpenAI-compatible tiny client for semantic fusion."""

    bridge: V17LlmBridge

    async def fuse(self, *, fragments: list[str], will_proxy: str, max_tokens: int = 80) -> str:
        cfg = self.bridge.resolve()
        polarity_rule = ""
        if will_proxy == "stable":
            polarity_rule = "你的立场是【稳健、防御】。必须体现‘正官’或‘官杀’的约束力与持重感，文案侧重于克制、收敛与底线思维。"
        elif will_proxy == "aggressive":
            polarity_rule = "你的立场是【激进、破局】。必须体现‘偏财’或‘食伤生财’的扩张性与进攻性，文案侧重于突破、进取与高风险收益。"
        elif will_proxy == "neutral":
            polarity_rule = "你的立场是【中庸、调和】。体现中正平和、左右逢源的智慧。"
        
        prompt = (
            f"将以下碎片提炼为一句不超过50字的叙事判词。严禁重复，极度凝练。\n"
            f"【极化要求】：{polarity_rule}\n"
            f"物理数据流：{' | '.join(fragments[:6])}"
        )
        body = {
            "model": cfg["model"],
            "messages": [
                {"role": "system", "content": "你是V17叙事织机，擅长玄学与赛博朋克极客文风。严禁工程词汇泄露。"},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
            "max_tokens": int(max_tokens or 80),
        }
        try:
            return await asyncio.wait_for(self._chat(cfg["base_url"], cfg["api_key"], body), timeout=0.8)
        except Exception:
            # 保底：仍输出自然句，避免工程词泄漏。
            return "局势火势偏旺，宜守中求进，先稳后发。"

    async def _chat(self, base_url: str, api_key: str, body: dict) -> str:
        def _sync_call() -> str:
            endpoint = base_url.rstrip("/") + "/chat/completions"
            payload = json.dumps(body).encode("utf-8")
            req = request.Request(endpoint, data=payload, method="POST")
            req.add_header("Content-Type", "application/json")
            cfg = self.bridge.resolve()
            username = str(cfg.get("username", "")).strip()
            password = str(cfg.get("password", "")).strip()
            if api_key:
                req.add_header("Authorization", f"Bearer {api_key}")
            elif username and password:
                token = base64.b64encode(f"{username}:{password}".encode("utf-8")).decode("utf-8")
                req.add_header("Authorization", f"Basic {token}")
            with request.urlopen(req, timeout=0.7) as resp:
                raw = json.loads(resp.read().decode("utf-8"))
            text = (
                (((raw.get("choices") or [{}])[0] or {}).get("message") or {}).get("content")
                if isinstance(raw, dict)
                else ""
            )
            return str(text or "").strip()

        return await asyncio.to_thread(_sync_call)
