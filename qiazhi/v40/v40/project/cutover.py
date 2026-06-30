from __future__ import annotations

from typing import Any


def build_production_cutover_checklist(
    *,
    replacement_readiness: dict[str, Any],
    weights: list[dict[str, Any]],
    llm_ready: bool,
    repository_configured: bool,
) -> dict[str, object]:
    active_weight = next((weight for weight in weights if bool(weight.get("active"))), None)
    rollback_available = bool(active_weight and str(active_weight.get("rollback_version_id") or "").strip())
    checks = [
        _check(
            "replacement_candidate_ready",
            "V30 replacement candidate ready",
            replacement_readiness.get("status") == "candidate_ready",
            str(replacement_readiness.get("status", "unknown")),
            "先补齐 V30 replacement readiness gates。",
        ),
        _check(
            "active_weight_audited",
            "Active weight audited",
            active_weight is not None,
            str(active_weight.get("weight_version_id", "")) if active_weight else "no active weight",
            "需要至少一个已审计 active weight。",
        ),
        _check(
            "rollback_available",
            "Rollback available",
            rollback_available,
            str(active_weight.get("rollback_version_id", "")) if active_weight else "",
            "上线前必须有 rollback version。",
        ),
        _check(
            "llm_ready",
            "LLM ready",
            llm_ready,
            "enabled" if llm_ready else "not ready",
            "LLM execution must be enabled before beta cutover.",
        ),
        _check(
            "repository_configured",
            "Repository configured",
            repository_configured,
            "configured" if repository_configured else "not configured",
            "V40 Postgres repository must be configured.",
        ),
    ]
    ready_count = sum(1 for check in checks if check["ready"])
    percent = int(round(ready_count / len(checks) * 100)) if checks else 0
    automatic_status = "ready" if percent == 100 else "blocked"
    return {
        "version": "v40.production_cutover_checklist.v1",
        "automatic_ready_percent": percent,
        "automatic_status": automatic_status,
        "cutover_status": "blocked_by_human_signoff" if automatic_status == "ready" else "blocked_by_automatic_checks",
        "ready_check_count": ready_count,
        "check_count": len(checks),
        "checks": checks,
        "manual_signoff_required": [
            "真实命例质量判断",
            "最终产品验收",
            "线上切换窗口",
        ],
        "boundary": "production_cutover_checklist_observes_readiness_without_switching_traffic",
    }


def _check(key: str, label: str, ready: bool, evidence: str, next_action: str) -> dict[str, object]:
    return {
        "key": key,
        "label": label,
        "ready": ready,
        "evidence": evidence,
        "next_action": "" if ready else next_action,
    }
