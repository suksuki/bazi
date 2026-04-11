"""Chronos：月令本气「司令」与余气/进气修正的 meta 层（不改写 L1 delta）。"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Mapping, Optional

from app.core.config.physics_settings import resolve_physics_settings
from app.core.bazi.engine import branch_hidden_stems_effective
from app.skills.physics_rules import MONTH_BRANCH_TO_SEASON, STEM_TO_ELEMENT

PLUGIN_ID = "base.chronos"

# 交季地支对「进气」的符号偏置（可经 CHRONOS_* 杠杆整体缩放）
_INTAKE_BRANCH_BIAS: Dict[str, float] = {"辰": 0.02, "戌": -0.02, "丑": 0.015, "未": -0.015}


def _utc_audit_ts() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _pillars_dict(metadata: Any) -> Dict[str, Any]:
    if metadata is None:
        return {}
    p = getattr(metadata, "pillars", None)
    if p is None and isinstance(metadata, dict):
        p = metadata.get("pillars")
    if p is None:
        return {}
    if hasattr(p, "model_dump"):
        return p.model_dump()
    if isinstance(p, dict):
        return p
    return {}


def _month_branch(pillars: Mapping[str, Any]) -> str:
    col = pillars.get("month")
    if not col:
        return ""
    if isinstance(col, dict):
        return str(col.get("branch") or "")
    return str(getattr(col, "branch", "") or "")


def _main_qi_split(branch: str) -> tuple[str, float, float]:
    """返回 (本气天干, 本气占比, 余气+中气占比之和)。"""
    hidden = branch_hidden_stems_effective().get(branch) or {}
    if not hidden:
        return "", 0.0, 0.0
    total = float(sum(hidden.values()) or 1.0)
    main_stem = max(hidden, key=lambda s: hidden[s])
    r_main = float(hidden[main_stem]) / total
    r_other = max(0.0, 1.0 - r_main)
    return main_stem, round(r_main, 6), round(r_other, 6)


def run_chronos_plugin(
    *,
    physics_tensor: Dict[str, Any],
    metadata: Any,
    physics_config: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """写入 `meta.chronos_v1` 并返回审计行；若已存在 `chronos_v1` 则幂等跳过。"""
    meta = physics_tensor.setdefault("meta", {})
    if not isinstance(meta, dict):
        return {"skipped": True, "reason": "meta_not_dict", "audit_items": []}
    if meta.get("chronos_v1"):
        return {"skipped": True, "reason": "already_applied", "audit_items": []}

    cfg_src = physics_config
    if cfg_src is None and isinstance(meta.get("runtime_physics_config"), dict):
        cfg_src = meta.get("runtime_physics_config")
    settings = resolve_physics_settings(cfg_src if isinstance(cfg_src, dict) else None)
    lever_cmd = float(settings.get("CHRONOS_COMMAND_LEVER", 0.0))
    lever_res = float(settings.get("CHRONOS_RESIDUAL_LEVER", 0.12))

    pillars = _pillars_dict(metadata)
    mb = _month_branch(pillars)
    ts = _utc_audit_ts()
    if not mb:
        meta["chronos_v1"] = {"applied": False, "reason": "missing_month_branch"}
        return {"applied": False, "audit_items": []}

    season = str(MONTH_BRANCH_TO_SEASON.get(mb, "spring"))
    main_stem, r_main, r_residual = _main_qi_split(mb)
    main_el = str(STEM_TO_ELEMENT.get(main_stem, "") or "")
    intake = float(_INTAKE_BRANCH_BIAS.get(mb, 0.0))

    w_cmd = round(max(0.25, min(1.35, r_main * (1.0 + lever_cmd))), 4)
    delta_res = round(r_residual * lever_res + intake, 4)
    w_eff = round(max(0.25, min(1.35, w_cmd + delta_res)), 4)

    block: Dict[str, Any] = {
        "month_branch": mb,
        "season": season,
        "command_stem": main_stem,
        "command_element": main_el,
        "main_qi_weight": w_cmd,
        "residual_intake_correction": delta_res,
        "effective_chronos_weight": w_eff,
        "raw_main_qi_ratio": round(r_main, 6),
        "raw_residual_ratio": round(r_residual, 6),
    }
    meta["chronos_v1"] = {"applied": True, **block}

    audit_items: List[Dict[str, Any]] = [
        {
            "id": "chronos-mp-command",
            "step": "CH-01",
            "role": "Chronos",
            "action": "mp_chronos_command · base.chronos",
            "timestamp": ts,
            "payload": {
                "skill_id": "mp_chronos_command",
                "plugin": PLUGIN_ID,
                "month_branch": mb,
                "season": season,
                "command_stem": main_stem,
                "command_element": main_el,
                "main_qi_weight": w_cmd,
            },
        },
        {
            "id": "chronos-mp-residual",
            "step": "CH-02",
            "role": "Chronos",
            "action": "mp_chronos_residual · base.chronos",
            "timestamp": ts,
            "payload": {
                "skill_id": "mp_chronos_residual",
                "plugin": PLUGIN_ID,
                "month_branch": mb,
                "residual_intake_correction": delta_res,
                "intake_branch_bias": intake,
                "effective_chronos_weight": w_eff,
            },
        },
    ]

    return {"applied": True, "chronos": block, "audit_items": audit_items}
