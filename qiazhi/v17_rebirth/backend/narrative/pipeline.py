from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, Dict, Optional

from .sanitizer import NarrativeSanitizer
from .semantic_fusion import SemanticFusion
from v17_rebirth.backend.services.physics_canonical import strip_client_pillar_echoes
from v17_rebirth.infrastructure.llm_bridge import V17_ROLE_WEAVER
from v17_rebirth.infrastructure.llm_micro_client import build_llm_audit_payload


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
        elif any(k in lowered for k in ["稳", "守", "谨慎", "风险", "保守", "避险"]):
            shifted = "stable"
        enhanced = [f"用户意志闪光：{msg}", *fact_fragments]
        return shifted, enhanced


@dataclass
class RealtimeNarrativePipeline:
    sanitizer: NarrativeSanitizer
    fusion: SemanticFusion
    dialogue: DialogueLayer | None = None

    def compute_llm_audit_preview(
        self,
        *,
        fact_fragments: list[str],
        will_proxy: str,
        user_message: str = "",
        action_signal: bool = False,
        decision_anchor: str = "",
        max_tokens: int = 512,
        role_style: str = V17_ROLE_WEAVER,
        physics_tensor: Optional[Dict[str, Any]] = None,
        session_id: str = "",
    ) -> Dict[str, Any]:
        """与 run() 内送入 LLM 的碎片与意志参数一致，供 SNAPSHOT（llm_audit_preview）在 fuse 前下发。"""
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
        if isinstance(physics_tensor, dict):
            clean = strip_client_pillar_echoes(clean)
        return build_llm_audit_payload(
            clean,
            will_proxy=str(shifted_proxy or "stable"),
            decision_anchor=str(decision_anchor or ""),
            action_signal=bool(action_signal),
            max_tokens=max_tokens,
            role_style=str(role_style or V17_ROLE_WEAVER),
            physics_tensor=physics_tensor if isinstance(physics_tensor, dict) else None,
            session_id=str(session_id or ""),
        )

    async def run(
        self,
        *,
        fact_fragments: list[str],
        will_proxy: str,
        physics_tensor: Optional[Dict[str, Any]] = None,
        session_id: str = "",
        user_message: str = "",
        action_signal: bool = False,
        decision_anchor: str = "",
        god_of_use: list[str] | None = None,
        god_of_taboo: list[str] | None = None,
        action_queue: Optional[asyncio.Queue[Dict[str, Any]]] = None,
        on_llm_partial: Optional[Callable[[str], Awaitable[None]]] = None,
        role_style: str = V17_ROLE_WEAVER,
        status_callback: Optional[Callable[[Dict[str, Any]], Awaitable[None]]] = None,
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
        pt = physics_tensor if isinstance(physics_tensor, dict) else None
        if pt is not None:
            clean = strip_client_pillar_echoes(clean)
        render_text, llm_meta = await self.fusion.to_render_text(
            clean_fragments=clean,
            will_proxy=shifted_proxy,
            action_signal=action_signal,
            decision_anchor=decision_anchor,
            history_context=[],
            action_queue=action_queue,
            on_llm_partial=on_llm_partial,
            role_style=str(role_style or V17_ROLE_WEAVER),
            status_callback=status_callback,
            physics_tensor=pt,
            session_id=str(session_id or ""),
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
