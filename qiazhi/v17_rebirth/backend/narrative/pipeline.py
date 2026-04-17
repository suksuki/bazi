from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from .sanitizer import NarrativeSanitizer
from .semantic_fusion import SemanticFusion


@dataclass
class DialogueLayer:
    sanitizer: NarrativeSanitizer

    def inject(self, *, user_message: str, will_proxy: str, fact_fragments: list[str]) -> tuple[str, list[str]]:
        msg = self.sanitizer.sanitize(user_message)
        if not msg:
            return will_proxy, fact_fragments
        lowered = msg.lower()
        shifted = will_proxy
        if any(k in lowered for k in ["冲", "快", "破", "加码", "进攻"]):
            shifted = "aggressive"
        elif any(k in lowered for k in ["稳", "守", "谨慎", "风险", "保守"]):
            shifted = "stable"
        enhanced = [f"用户意志闪光：{msg}", *fact_fragments]
        return shifted, enhanced


@dataclass
class RealtimeNarrativePipeline:
    sanitizer: NarrativeSanitizer
    fusion: SemanticFusion
    dialogue: DialogueLayer | None = None

    async def run(
        self,
        *,
        fact_fragments: list[str],
        will_proxy: str,
        user_message: str = "",
        action_signal: bool = False,
        decision_anchor: str = "",
        god_of_use: list[str] | None = None,
        god_of_taboo: list[str] | None = None,
    ) -> dict[str, Any]:
        shifted_proxy = will_proxy
        source_rows = list(fact_fragments or [])
        if self.dialogue is not None and str(user_message).strip():
            shifted_proxy, source_rows = self.dialogue.inject(
                user_message=user_message,
                will_proxy=shifted_proxy,
                fact_fragments=source_rows,
            )
        clean = [self.sanitizer.sanitize(x) for x in source_rows]
        clean = [x for x in clean if x]
        render_text, llm_meta = await self.fusion.to_render_text(
            clean_fragments=clean,
            will_proxy=shifted_proxy,
            action_signal=action_signal,
            decision_anchor=decision_anchor,
            history_context=[],
        )
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "layer": "NARRATOR",
            "payload": {
                "render_text": render_text,
                "will_proxy": str(shifted_proxy or "stable"),
                "will_flash": bool(str(user_message or "").strip()),
                "llm_meta": llm_meta if isinstance(llm_meta, dict) else {},
                "source_facts": clean[:6],
                "god_rings": {
                    "god_of_use": list(god_of_use or []),
                    "god_of_taboo": list(god_of_taboo or []),
                },
            },
        }
