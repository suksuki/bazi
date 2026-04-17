"""Single source narrative pipeline + payload guardrails."""
from __future__ import annotations

import asyncio
import os
from typing import Any, Dict, List

from app.services.narrative.sanitizer import sanitize_fragment_text
from app.skills.final_verdict_parts.llm_client import run_final_verdict_chat

_DEBUG_MODE = str(os.getenv("QIAZHI_NARRATIVE_DEBUG", "0")).strip().lower() in {"1", "true", "yes", "on"}
_ALLOWED_RENDER_KEYS = {
    "render_text",
    "protocol",
    "will_proxy",
    "trigger",
    "shadow_cursor",
    "skeleton_excerpt",
    "god_of_use",
    "god_of_taboo",
    "runtime_deity_map",
    "action_id",
    "optimistic",
}
_DROP_DEBUG_KEYS = {"raw_data", "audit_trace", "node_id"}


def guard_narrative_payload(payload: Any, *, layer: str) -> Dict[str, Any]:
    """Enforce narrative payload contract for frontend-bound frames."""
    src = payload if isinstance(payload, dict) else {}
    out = {str(k): v for k, v in src.items()}
    if not _DEBUG_MODE:
        for k in list(out.keys()):
            if k in _DROP_DEBUG_KEYS:
                out.pop(k, None)
    narrative_layers = {"NARRATOR", "PLUGIN", "SNAPSHOT", "ACTION_TAKEN"}
    if str(layer or "").upper() not in narrative_layers:
        return out
    if "render_text" not in out or not str(out.get("render_text") or "").strip():
        if _DEBUG_MODE:
            raise ValueError(f"narrative payload missing render_text for layer={layer}")
        return {}
    if _DEBUG_MODE:
        illegal = [k for k in out.keys() if k not in _ALLOWED_RENDER_KEYS]
        if illegal:
            raise ValueError(f"illegal narrative payload keys: {illegal}")
    else:
        out = {k: v for k, v in out.items() if k in _ALLOWED_RENDER_KEYS}
    out["render_text"] = sanitize_fragment_text(str(out.get("render_text") or ""))
    if not str(out.get("render_text") or "").strip():
        return {}
    return out


def sanitize_frame_for_client(frame: Dict[str, Any]) -> Dict[str, Any]:
    row = dict(frame or {})
    if not _DEBUG_MODE:
        for k in list(row.keys()):
            if k in _DROP_DEBUG_KEYS:
                row.pop(k, None)
    if isinstance(row.get("payload"), dict):
        layer = str(row.get("layer") or "").upper()
        row["payload"] = guard_narrative_payload(row.get("payload"), layer=layer)
    return row


class RealtimeNarrativePipeline:
    @staticmethod
    async def render_text(
        *,
        raw_fragments: List[str],
        will_proxy: str,
        max_chars: int = 220,
        action_mode: bool = False,
    ) -> str:
        rows = [sanitize_fragment_text(x) for x in (raw_fragments or [])]
        rows = [x for x in rows if x]
        if not rows:
            return ""
        mode = str(will_proxy or "stable").strip().lower()
        style = "偏向持盈保泰与风险缓释" if mode != "aggressive" else "偏向主动进取与破局扩张"
        task = "请将碎屑融合成一句完整命理判词。"
        if action_mode:
            task = "用户刚完成意志操作，请输出一句立场鲜明、可直接上屏的实时判词。"
        msgs = [
            {"role": "system", "content": "你是因果叙事织机。只输出一句简体中文，不要列表，不要解释。"},
            {"role": "user", "content": f"{task}\nWILL_PROXY={mode}（{style}）\n碎屑：{' | '.join(rows[:6])}"},
        ]
        try:
            raw, _ = await asyncio.wait_for(
                run_final_verdict_chat(msgs, temperature=0.15, max_tokens=80),
                timeout=0.2 if action_mode else 0.45,
            )
            text = str(raw or "").strip().replace("\n", " ")
            if text:
                return text[:max_chars]
        except Exception:
            return ""
        return ""

