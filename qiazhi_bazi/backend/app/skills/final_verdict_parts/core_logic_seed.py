"""终判 User：[Core Logic Seed] — 由物理/结构侧压缩一句命题，供 narrator 展开，不增加浮点泄漏。"""
from __future__ import annotations

from typing import Any, Dict, List


def format_core_logic_seed_user_block(
    *,
    metadata: Dict[str, Any],
    physics_tensor: Dict[str, Any],
    blind_work: Dict[str, Any],
    l1_flags: Dict[str, Any],
    final_decision_v0: Dict[str, Any],
    school_audit: Dict[str, Any],
) -> str:
    """返回带标题的若干短行，紧接在 [Verified Facts] 之后。"""
    lines: List[str] = []
    if bool(l1_flags.get("SHANG_GUAN_JIAN_GUAN")):
        lines.append("枢轴命题：伤官与正官张力显性，通关制化为叙事主轴。")

    pm = metadata.get("conflict_matrix") if isinstance(metadata.get("conflict_matrix"), dict) else {}
    pts = pm.get("points") if isinstance(pm.get("points"), list) else []
    for p in pts[:6]:
        if not isinstance(p, dict):
            continue
        kind = str(p.get("kind") or "").strip()
        detail = str(p.get("detail") or "").strip()[:120]
        if detail or kind:
            lines.append(f"物理枢纽：[{kind}] {detail}".strip())
            break

    prim = str(final_decision_v0.get("primary_structure") or "").strip()
    risk = str(final_decision_v0.get("stability_risk") or "").strip()
    if prim:
        tail = f"；结构风险={risk}" if risk else ""
        lines.append(f"格局路由：{prim}{tail}。")

    if bool(school_audit.get("has_conflict")):
        w = str(school_audit.get("logic_conflict_warning") or "").strip()[:200]
        if w:
            lines.append(f"学派张力：{w}")

    top = str(physics_tensor.get("top_anomaly") or "").strip()[:160]
    bad_markers = ("未拿到", "JSON", "结构化", "回退", "LLM", "审计链路")
    if top and not any(m in top for m in bad_markers):
        lines.append(f"审计焦点：{top}")

    if len(lines) < 2:
        morph = blind_work.get("morphing_hints") if isinstance(blind_work.get("morphing_hints"), list) else []
        first = str(morph[0]).strip()[:140] if morph else ""
        if first:
            lines.append(f"气机形变：{first}")

    if not lines:
        lines.append("命题域：仅以干支、VF 证据链与已勾选意志为据，铺陈喜忌与应机。")

    bullets = "\n".join(f"- {x}" for x in lines[:4])
    return f"[Core Logic Seed]\n{bullets}\n"
