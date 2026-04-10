"""宾主：年月为宾、日时为主；财官在日时能量占比 → 因果红利指标（η_host_guest 缩放）。"""
from __future__ import annotations

from typing import Any, Dict, List, Tuple

from app.core.config.physics_settings import resolve_physics_settings


def resolve_host_guest_eta(settings: Dict[str, float]) -> float:
    """宾主红利指标缩放系数，默认 1.0 不改变归一化占比。"""
    return float(max(0.0, min(2.0, float(settings.get("MANGPAI_ETA_HOST_GUEST", 1.0)))))


def compute_causal_dividend_index(physics_tensor: Dict[str, Any]) -> Tuple[float, str]:
    """
    财官（正官、七杀、正财、偏财）在日时柱上的能量占比 → 因果红利指标 0..1。
    应用 MANGPAI_ETA_HOST_GUEST 对占比做缩放后再截断到 [0,1]。
    """
    trace = ((physics_tensor or {}).get("deity_trace_details") or {}) if isinstance(physics_tensor, dict) else {}
    if not isinstance(trace, dict):
        return 0.0, ""
    runtime_cfg = (((physics_tensor or {}).get("meta") or {}).get("runtime_physics_config") or {})
    settings = resolve_physics_settings(runtime_cfg if isinstance(runtime_cfg, dict) else None)
    eta = resolve_host_guest_eta(settings)

    use_wealth = ("正财", "偏财", "正官", "七杀")
    host_e = 0.0
    total_e = 0.0
    for d in use_wealth:
        det = trace.get(d)
        if not isinstance(det, dict):
            continue
        base = det.get("base_energy")
        if not isinstance(base, dict):
            continue
        for item in base.get("contribution_sources") or []:
            if not isinstance(item, dict):
                continue
            src = str(item.get("source") or "")
            e = float(item.get("contribution_energy", 0.0) or 0.0)
            total_e += e
            if src.startswith("day.") or src.startswith("hour."):
                host_e += e
    if total_e <= 1e-12:
        return 0.0, ""
    ratio = host_e / total_e
    idx = round(min(1.0, max(0.0, ratio * eta)), 4)
    if idx < 0.08:
        return idx, ""
    return idx, f"宾主主权：财官能量在日主时柱占比高，因果红利指标={idx:.2f}。"


def host_guest_chip_logs(physics_tensor: Dict[str, Any]) -> List[str]:
    _, msg = compute_causal_dividend_index(physics_tensor)
    if not msg:
        return []
    return [f"[MANGPAI_CHIP] {msg}"]
