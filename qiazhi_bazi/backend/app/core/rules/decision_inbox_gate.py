"""Decision Inbox 信噪比门控：低 Abs 且无 CRITICAL 时不推送判词观察类卡片。"""
from __future__ import annotations

from typing import Any, Dict, Optional


def apply_decision_inbox_signal_gate(
    *,
    meta: Dict[str, Any],
    settings: Dict[str, float],
    clash_abs_loss_total: Optional[float],
) -> Dict[str, Any]:
    """
    使用 L1 合成中的冲战 Abs 损耗估计与 L1 能级：
    - 若 abs_estimate < GLOBAL_DECISION_ABS_THRESHOLD 且无「可绕过门控」的 CRITICAL，则不向 Inbox 推送冲突观察项。
    - 可绕过：伤官见官 CRITICAL，或任意双侧 Surface 的其它 L1 核心冲突（见 l1_inbox_signal_bypass）。
    """
    threshold = float(settings.get("GLOBAL_DECISION_ABS_THRESHOLD", 5.0))
    jf = meta.get("l1_junction_flags") if isinstance(meta.get("l1_junction_flags"), dict) else {}
    has_critical = bool(jf.get("l1_inbox_signal_bypass")) or str(jf.get("sgjg_severity") or "") == "CRITICAL"
    if clash_abs_loss_total is None:
        eligible = True
    else:
        eligible = (float(clash_abs_loss_total) >= threshold) or has_critical
    block: Dict[str, Any] = {
        "abs_estimate": round(float(clash_abs_loss_total), 4) if clash_abs_loss_total is not None else None,
        "threshold": threshold,
        "has_critical_marker": has_critical,
        "inbox_conflict_cards_eligible": eligible,
    }
    meta["decision_signal_to_noise"] = block
    return block
