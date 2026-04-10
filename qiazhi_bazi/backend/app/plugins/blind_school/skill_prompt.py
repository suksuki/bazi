"""将 skill_manifest 展平为 LLM system 片段（与物理引擎 skill_id 对齐）。"""
from __future__ import annotations

from typing import Any, Dict, List

from app.plugins.blind_school.skill_manifest_loader import list_blind_skills

_BLIND_PLUGIN_ID = "classical.blind_school.v1"


def blind_school_plugin_active(physics_tensor: Dict[str, Any] | None) -> bool:
    pt = physics_tensor or {}
    meta = pt.get("meta") or {}
    if not isinstance(meta, dict):
        return False
    ep = meta.get("enabled_plugins")
    if isinstance(ep, list) and _BLIND_PLUGIN_ID in ep:
        return True
    po = pt.get("plugin_outputs") or {}
    return isinstance(po, dict) and _BLIND_PLUGIN_ID in po


def _active_skill_rows(physics_tensor: Dict[str, Any]) -> List[Dict[str, Any]]:
    """按 meta.blind_school_features 过滤，仅注入已开启子算子对应的 Skill。"""
    all_skills = list_blind_skills()
    meta = (physics_tensor or {}).get("meta") or {}
    flags = meta.get("blind_school_features") if isinstance(meta, dict) else None
    if not isinstance(flags, dict):
        return list(all_skills)
    keymap = {
        "mp_pierce_01": bool(flags.get("enable_pierce_harm", True)),
        "mp_tomb_01": bool(flags.get("enable_tomb_vault", True)),
        "mp_host_guest_01": bool(flags.get("enable_host_guest_bonus", True)),
    }
    out: List[Dict[str, Any]] = []
    for row in all_skills:
        if not isinstance(row, dict):
            continue
        sid = str(row.get("id") or "")
        if keymap.get(sid, True):
            out.append(row)
    return out


def format_blind_skill_registry_for_prompt(physics_tensor: Dict[str, Any] | None) -> str:
    """
    注入 description + assertion_template，约束 LLM 断言与引擎 chip / skill_id 语义一致。
    """
    if not blind_school_plugin_active(physics_tensor):
        return ""
    rows = _active_skill_rows(physics_tensor or {})
    if not rows:
        return ""
    lines: List[str] = [
        "## 盲派 Skill 注册表（物理引擎已挂载 classical.blind_school.v1）",
        "生成与盲派相关的自然语言断言时：必须引用下方 skill_id；句式应优先贴合 assertion_template 的语义，不得自造与模板冲突的定性。",
    ]
    for s in rows:
        sid = str(s.get("id") or "")
        name = str(s.get("name") or "")
        desc = str(s.get("description") or "").strip()
        tmpl = str(s.get("assertion_template") or "").strip()
        impact = str(s.get("impact_factor") or "").strip()
        lines.append(f"### {sid} · {name}")
        if impact:
            lines.append(f"- impact_factor: {impact}")
        if desc:
            lines.append(f"- description: {desc}")
        if tmpl:
            lines.append(f"- assertion_template: {tmpl}")
    return "\n".join(lines).strip()
