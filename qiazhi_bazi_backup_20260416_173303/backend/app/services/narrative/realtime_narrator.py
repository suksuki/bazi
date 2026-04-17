"""Realtime narrator service: single entry for narrative output."""
from __future__ import annotations

from typing import Any, Dict, List

from app.services.narrative.pipeline import RealtimeNarrativePipeline


def _collect_raw_fragments(metadata: Dict[str, Any], physics_tensor: Dict[str, Any]) -> List[str]:
    md = metadata if isinstance(metadata, dict) else {}
    pt = physics_tensor if isinstance(physics_tensor, dict) else {}
    out: List[str] = []
    for row in list(md.get("narrative_fragments_v14") or [])[-6:]:
        if isinstance(row, dict):
            s = str(row.get("narrative_fragment") or "").strip()
            if s:
                out.append(s)
    p_out = pt.get("plugin_outputs") if isinstance(pt.get("plugin_outputs"), dict) else {}
    for prow in p_out.values():
        if not isinstance(prow, dict):
            continue
        payload = prow.get("payload") if isinstance(prow.get("payload"), dict) else {}
        facts = payload.get("facts") if isinstance(payload.get("facts"), list) else []
        for f in facts[:3]:
            if isinstance(f, dict):
                s = str(f.get("narrative_fragment") or f.get("fact") or f.get("text") or "").strip()
                if s:
                    out.append(s)
    return out[-6:]


async def compose_realtime_narration(
    *,
    metadata: Dict[str, Any],
    physics_tensor: Dict[str, Any],
    lang: str = "ZH",
    max_chars: int = 220,
) -> Dict[str, Any]:
    md = metadata if isinstance(metadata, dict) else {}
    will_proxy = str((((md.get("m5_will_anchor_v14") or {}) if isinstance(md.get("m5_will_anchor_v14"), dict) else {}).get("mode") or "stable")).strip().lower()
    if will_proxy not in {"stable", "aggressive"}:
        will_proxy = "stable"
    text = await RealtimeNarrativePipeline.render_text(
        raw_fragments=_collect_raw_fragments(md, physics_tensor if isinstance(physics_tensor, dict) else {}),
        will_proxy=will_proxy,
        max_chars=max_chars,
        action_mode=False,
    )
    return {
        "ok": True,
        "protocol": "realtime_narrator.v16_2",
        "lang": lang,
        "will_proxy": will_proxy,
        "text": text,
    }


async def rewrite_fragments_tone_v15(*, fragments: List[str], will_proxy: str, max_items: int = 3) -> List[str]:
    text = await RealtimeNarrativePipeline.render_text(
        raw_fragments=[str(x).strip() for x in (fragments or []) if str(x).strip()][: max(1, int(max_items or 3))],
        will_proxy=will_proxy,
        max_chars=220,
        action_mode=True,
    )
    return [text] if text else []

