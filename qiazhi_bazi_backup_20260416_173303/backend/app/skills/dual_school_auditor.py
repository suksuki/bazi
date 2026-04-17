"""Dual-school auditor: keep Balance and Work verdicts independent and check conflicts."""
from __future__ import annotations

from typing import Any, Dict


def build_dual_school_audit(*, final_decision: Dict[str, Any], work_vector: Dict[str, Any]) -> Dict[str, Any]:
    balance_verdict = str(final_decision.get("balance_verdict") or "未提供旺衰结论。")
    work_verdict = str(final_decision.get("work_verdict") or "未提供盲派结论。")
    self_abs = float((final_decision.get("self_abs") or 0.0) if isinstance(final_decision, dict) else 0.0)
    net_effect = str(work_vector.get("net_effect") or "neutral")
    risk_ratio = float(work_vector.get("risk_ratio", 0.0) or 0.0)
    work_net = float(work_vector.get("work_expectation", 0.0) or 0.0)

    balance_action = "扶助" if self_abs < 0.8 else "泄耗"
    work_action = "止损" if (net_effect == "risk" or risk_ratio > 0.5 or work_net < 0) else "求进"
    has_conflict = balance_action == "扶助" and work_action == "止损"

    return {
        "balance_line": f"[BALANCE_SCHOOL] {balance_verdict}",
        "work_line": f"[WORK_SCHOOL] {work_verdict}",
        "logic_conflict_warning": "[LOGIC_CONFLICT_WARNING] 旺衰建议扶助，但盲派显示高反噬/止损优先；请先止损再扶助。"
        if has_conflict
        else "",
        "has_conflict": has_conflict,
    }
