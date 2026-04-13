"""Modern plugin: socialized wealth-risk portrait."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List


def _utc_audit_ts() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _skill_audit_rows(
    *,
    host_abs: float,
    work_net: float,
    is_locked: bool,
    structure_label: str,
    risk: str,
) -> List[Dict[str, Any]]:
    ts = _utc_audit_ts()
    pid = "modern.wealth_risk.v1"
    return [
        {
            "id": "mw-host-abs",
            "step": "MW-01",
            "role": "WealthRisk",
            "action": f"mw_host_abs · {pid}",
            "timestamp": ts,
            "payload": {
                "skill_id": "mw_host_abs",
                "plugin": pid,
                "abs_contribution": round(host_abs, 4),
                "channel": "host_abs",
            },
        },
        {
            "id": "mw-work-net",
            "step": "MW-02",
            "role": "WealthRisk",
            "action": f"mw_work_net · {pid}",
            "timestamp": ts,
            "payload": {
                "skill_id": "mw_work_net",
                "plugin": pid,
                "abs_contribution": round(work_net, 4),
                "channel": "work_expectation",
            },
        },
        {
            "id": "mw-exit-lock",
            "step": "MW-03",
            "role": "WealthRisk",
            "action": f"mw_exit_lock · {pid}",
            "timestamp": ts,
            "payload": {
                "skill_id": "mw_exit_lock",
                "plugin": pid,
                "abs_contribution": round(1.0 if is_locked else 0.0, 4),
                "channel": "is_exit_locked",
            },
        },
        {
            "id": "mw-structure",
            "step": "MW-04",
            "role": "WealthRisk",
            "action": f"mw_structure · {pid}",
            "timestamp": ts,
            "payload": {
                "skill_id": "mw_structure",
                "plugin": pid,
                "abs_contribution": round(float(len(structure_label)), 4),
                "channel": structure_label[:120],
            },
        },
        {
            "id": "mw-risk-band",
            "step": "MW-05",
            "role": "WealthRisk",
            "action": f"mw_risk_band · {pid}",
            "timestamp": ts,
            "payload": {
                "skill_id": "mw_risk_band",
                "plugin": pid,
                "risk_band": risk,
                "abs_contribution": round({"high": 3.0, "medium": 1.5, "medium-high": 2.2}.get(risk, 1.0), 4),
            },
        },
    ]


def run_modern_wealth_risk_plugin(
    *,
    work_vector: Dict[str, Any],
    structure_final_decision: Dict[str, Any],
    metadata: Dict[str, Any],
    is_preview: bool = False,
    dry_run: bool = False,
) -> Dict[str, Any]:
    del metadata
    _ = (is_preview, dry_run)
    host_abs = float((work_vector or {}).get("host_abs", 0.0) or 0.0)
    work_net = float((work_vector or {}).get("work_expectation", 0.0) or 0.0)
    is_locked = bool((((work_vector or {}).get("spatial_audit") or {}).get("is_exit_locked", False)))
    confidence = 0.66

    if host_abs >= 20 and work_net <= 0 and is_locked:
        verdict = "高能闭锁型：财富转化受阻，需先破局再扩张。"
        risk = "high"
        confidence = 0.83
    elif work_net > 0:
        verdict = "可转化型：存在可持续做功路径，建议稳态放大。"
        risk = "medium"
        confidence = 0.72
    else:
        verdict = "过渡型：资源可见但效率不足，建议先修复出口。"
        risk = "medium-high"

    structure_label = str((structure_final_decision or {}).get("primary_structure_humanized") or "")
    audit_items = _skill_audit_rows(
        host_abs=host_abs,
        work_net=work_net,
        is_locked=is_locked,
        structure_label=structure_label,
        risk=risk,
    )

    return {
        "verdict": verdict,
        "risk_band": risk,
        "confidence_score": confidence,
        "evidence": [
            f"host_abs={host_abs:.2f}",
            f"work_net={work_net:.2f}",
            f"is_exit_locked={is_locked}",
            f"structure={structure_label}",
        ],
        "rule_source": "BLIND_SCHOOL_ENCYCLOPEDIA.md#第五部分",
        "audit_items": audit_items,
    }

