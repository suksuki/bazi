from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class MicroLlmClient(Protocol):
    async def fuse(self, *, fragments: list[str], will_proxy: str, max_tokens: int = 80) -> str:
        ...


@dataclass
class SemanticFusion:
    """Micro-LLM fusion wrapper for clean narrative generation."""

    llm_client: MicroLlmClient

    async def to_render_text(self, *, clean_fragments: list[str], will_proxy: str) -> str:
        rows = [x.strip() for x in clean_fragments if x and x.strip()]
        if not rows:
            return ""
        return (await self.llm_client.fuse(fragments=rows, will_proxy=will_proxy, max_tokens=80)).strip()
