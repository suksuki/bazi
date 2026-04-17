from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from .sanitizer import NarrativeSanitizer
from .semantic_fusion import SemanticFusion


@dataclass
class RealtimeNarrativePipeline:
    sanitizer: NarrativeSanitizer
    fusion: SemanticFusion

    async def run(
        self,
        *,
        fact_fragments: list[str],
        will_proxy: str,
        god_of_use: list[str] | None = None,
        god_of_taboo: list[str] | None = None,
    ) -> dict[str, Any]:
        clean = [self.sanitizer.sanitize(x) for x in (fact_fragments or [])]
        clean = [x for x in clean if x]
        render_text = await self.fusion.to_render_text(clean_fragments=clean, will_proxy=will_proxy)
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "layer": "NARRATOR",
            "payload": {
                "render_text": render_text,
                "will_proxy": str(will_proxy or "stable"),
                "god_rings": {
                    "god_of_use": list(god_of_use or []),
                    "god_of_taboo": list(god_of_taboo or []),
                },
            },
        }
