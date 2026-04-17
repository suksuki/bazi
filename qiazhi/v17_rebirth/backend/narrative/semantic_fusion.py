from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class MicroLlmClient(Protocol):
    async def fuse(self, *, fragments: list[str], will_proxy: str, max_tokens: int = 80) -> str | dict:
        ...


@dataclass
class SemanticFusion:
    """Micro-LLM fusion wrapper for clean narrative generation."""

    llm_client: MicroLlmClient

    async def to_render_text(
        self,
        *,
        clean_fragments: list[str],
        will_proxy: str,
        action_signal: bool = False,
        decision_anchor: str = "",
        history_context: list[str] | None = None,
    ) -> tuple[str, dict]:
        rows = [x.strip() for x in clean_fragments if x and x.strip()]
        if not rows:
            return "", {}
        # Action signal forcibly resets narrative inertia from prior context.
        if action_signal:
            history_context = []
            anchor = str(decision_anchor).strip()
            prefix = f"（因采纳{anchor}策略）" if anchor else "基于您的决策，"
            rows = [f"{prefix}{rows[0]}", *rows[1:]]
        llm_raw = await self.llm_client.fuse(fragments=rows, will_proxy=will_proxy, max_tokens=80)
        llm_meta: dict = {}
        if isinstance(llm_raw, dict):
            text = str(llm_raw.get("text", "")).strip()
            llm_meta = llm_raw.get("llm_meta", {}) if isinstance(llm_raw.get("llm_meta"), dict) else {}
        else:
            text = str(llm_raw or "").strip()
        if action_signal and text:
            anchor = str(decision_anchor).strip()
            if anchor:
                required = f"（因采纳{anchor}策略）"
                if required not in text:
                    text = f"{required}{text}"
            elif not text.startswith("基于您的决策"):
                text = f"基于您的决策，{text}"
        return text, llm_meta
