"""语义快照：active_verdict_skeleton — 引擎预判骨架 + 意志硬编码（中控终判 v1）。"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.schemas.bazi_metadata import ActiveVerdictSkeleton


def _pillar_line(pillars: Any) -> str:
    if not isinstance(pillars, dict):
        return ""
    parts: List[str] = []
    for key in ("year", "month", "day", "hour"):
        col = pillars.get(key)
        if not isinstance(col, dict):
            continue
        stem = str(col.get("stem") or "").strip()
        br = str(col.get("branch") or "").strip()
        if stem or br:
            parts.append(f"{stem}{br}")
    return " / ".join(parts) if parts else ""


def build_active_verdict_skeleton(
    metadata: Dict[str, Any],
    physics_tensor: Optional[Dict[str, Any]] = None,
    *,
    selected_cards: Optional[List[Dict[str, Any]]] = None,
) -> ActiveVerdictSkeleton:
    """由当前盘面元数据 + 物理张量拼装引擎骨架；意志行由 Inbox 勾选注入。"""
    bullets: List[str] = []
    pillars = metadata.get("pillars")
    pline = _pillar_line(pillars)
    if pline:
        bullets.append(f"[Pillars] {pline}")

    cm = metadata.get("conflict_matrix") if isinstance(metadata.get("conflict_matrix"), dict) else {}
    pts = cm.get("points") if isinstance(cm.get("points"), list) else []
    for p in pts[:16]:
        if not isinstance(p, dict):
            continue
        kind = str(p.get("kind") or "").strip()
        detail = str(p.get("detail") or "").strip()
        if detail:
            bullets.append(f"结构·{kind}:{detail}"[:220])

    bud: Dict[str, Any] = {}
    if isinstance(physics_tensor, dict):
        meta = physics_tensor.get("meta")
        if isinstance(meta, dict):
            raw = meta.get("semantic_label_bundle_v1")
            if isinstance(raw, dict):
                bud = raw
    vf_lines = bud.get("verified_fact_lines") if isinstance(bud.get("verified_fact_lines"), list) else []
    for line in vf_lines[:20]:
        s = str(line or "").strip()
        if s:
            bullets.append(f"VF:{s[:240]}")

    user_will: List[str] = []
    for c in selected_cards or []:
        if not isinstance(c, dict):
            continue
        title = str(c.get("title") or "").strip()
        dt = str(c.get("displayText") or "").strip()
        blob = " / ".join(x for x in (title, dt) if x)
        if blob:
            user_will.append(blob[:420])

    return ActiveVerdictSkeleton(
        engine_bullets=bullets[:48],
        user_will_lines=user_will,
        updated_at=datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
    )


def format_skeleton_for_system_prompt(sk: ActiveVerdictSkeleton) -> str:
    """供终判 System [MANDATORY_NARRATION] 注入；禁浮点由上游 VF 行保证。"""
    lines: List[str] = []
    if sk.engine_bullets:
        lines.append("【引擎骨架】")
        lines.extend(f"- {x}" for x in sk.engine_bullets[:36])
    if sk.user_will_lines:
        lines.append("【用户意志·须显著呈现】")
        lines.extend(f"- {x}" for x in sk.user_will_lines[:20])
    return "\n".join(lines).strip()
