from __future__ import annotations

from typing import Any, Dict, List


def strength_qualifier(abs_energy: float) -> str:
    if abs_energy < 0.5:
        return "熄灭/虚存"
    if abs_energy < 2.0:
        return "衰微/无力"
    if abs_energy < 5.0:
        return "中和/可用"
    return "强旺/执拗"


def get_logical_evidence(
    *,
    metadata: Dict[str, Any],
    physics_tensor: Dict[str, Any],
    selected_cards: List[Dict[str, Any]],
    consensus_history: List[Dict[str, Any]],
) -> List[str]:
    """
    元数据投影：把复杂 JSON 脱水为 Key-Value 证据行，便于 LLM 读取。
    """
    lines: List[str] = []
    pillars = ((metadata or {}).get("pillars", {}) if isinstance(metadata, dict) else {}) or {}
    if pillars:
        y = pillars.get("year", {})
        m = pillars.get("month", {})
        d = pillars.get("day", {})
        h = pillars.get("hour", {})
        lines.append(
            f"四柱={y.get('stem', '?')}{y.get('branch', '?')}/{m.get('stem', '?')}{m.get('branch', '?')}/"
            f"{d.get('stem', '?')}{d.get('branch', '?')}/{h.get('stem', '?')}{h.get('branch', '?')}"
        )
    if isinstance(metadata, dict) and metadata.get("gender"):
        lines.append(f"性别={metadata.get('gender')}")
    deity_axes = (physics_tensor.get("deity_energy_axes", {}) if isinstance(physics_tensor, dict) else {}) or {}
    climate_trace = (
        (((physics_tensor.get("meta", {}) or {}).get("climate_adjustment", {})) if isinstance(physics_tensor, dict) else {})
        or {}
    )
    deity_before = (climate_trace.get("deity_before", {}) if isinstance(climate_trace, dict) else {}) or {}
    deity_after = (climate_trace.get("deity_after", {}) if isinstance(climate_trace, dict) else {}) or {}
    for deity in ["比肩", "劫财", "食神", "伤官", "正财", "偏财", "正官", "七杀", "正印", "偏印"]:
        axis = deity_axes.get(deity) if isinstance(deity_axes, dict) else None
        if isinstance(axis, dict):
            abs_energy = float(axis.get("absolute_energy", 0.0) or 0.0)
            qualifier = strength_qualifier(abs_energy)
            before = float(deity_before.get(deity, 0.0) or 0.0)
            after = float(deity_after.get(deity, abs_energy) or abs_energy)
            factor = (after / before) if before > 0 else 1.0
            lines.append(
                f"十神.{deity}.Abs={abs_energy:.2f} "
                f"(Before:{before:.2f}, Climate_Factor:{factor:.2f}) [状态:{qualifier}]"
            )
    root_check = (
        (((physics_tensor.get("audit_log", {}) or {}).get("trace", {}) or {}).get("root_check", {}))
        if isinstance(physics_tensor, dict)
        else {}
    ) or {}
    if isinstance(root_check, dict):
        lines.append(f"根气.no_root={bool(root_check.get('no_root', False))}")
        lines.append(f"根气.decay_factor={root_check.get('decay_factor', 'N/A')}")
        lines.append(f"根气.record={str(root_check.get('record', ''))[:180]}")
    for i, c in enumerate(consensus_history or []):
        if isinstance(c, dict):
            lines.append(
                f"共识.{i + 1}={c.get('decision_key', '')}:{c.get('confirmed_value', '?')}|{str(c.get('reasoning', ''))[:80]}"
            )
    for i, s in enumerate(selected_cards or []):
        if isinstance(s, dict):
            lines.append(f"裁决项.{i + 1}={s.get('cardType', 'conflict')}|{s.get('displayText') or s.get('title') or ''}")
    return lines
