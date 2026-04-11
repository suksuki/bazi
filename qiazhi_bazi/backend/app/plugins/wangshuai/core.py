"""WangShuai plugin (balance-school pressure audit)."""
from __future__ import annotations

from typing import Any, Dict

from app.plugins.wangshuai.wangshuai_engine import evaluate_wangshuai


def run_wangshuai_plugin(*, physics_tensor: Dict[str, Any], metadata: Dict[str, Any]) -> Dict[str, Any]:
    out = evaluate_wangshuai(physics_tensor=physics_tensor or {}, metadata=metadata or {})
    audit_items = list(out.get("audit_items") or [])
    audit = (physics_tensor or {}).setdefault("audit_log", {})
    if isinstance(audit, dict):
        audit["wangshuai_audit_items"] = audit_items
    return {
        "self_abs": out["self_abs"],
        "verdict": out["verdict"],
        "confidence_score": out["confidence_score"],
        "evidence": list(out.get("evidence") or []),
        "rule_source": str(out.get("rule_source") or ""),
        "wangshuai_axes": out.get("wangshuai_axes") or {},
        "audit_items": audit_items,
    }

