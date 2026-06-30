from __future__ import annotations

from typing import Any


def build_release_candidate_audit(
    *,
    project_status: dict[str, Any],
    surface_readiness: dict[str, Any],
    replacement_readiness: dict[str, Any],
    cutover_checklist: dict[str, Any],
) -> dict[str, object]:
    checks = [
        _check(
            "project_progress_observable",
            "Project progress observable",
            int(project_status.get("overall_completion_percent", 0)) >= 84,
            f"{project_status.get('overall_completion_percent', 0)}%",
            "保持 /api/v40/project/status 可用。",
        ),
        _check(
            "surface_beta_ready",
            "Surface beta ready",
            surface_readiness.get("beta_status") == "ready",
            str(surface_readiness.get("beta_status", "unknown")),
            "用户侧 beta readiness 必须 ready。",
        ),
        _check(
            "v30_replacement_candidate_ready",
            "V30 replacement candidate ready",
            replacement_readiness.get("status") == "candidate_ready",
            str(replacement_readiness.get("status", "unknown")),
            "V30 replacement readiness 必须 candidate_ready。",
        ),
        _check(
            "cutover_automatic_checks_ready",
            "Cutover automatic checks ready",
            cutover_checklist.get("automatic_status") == "ready",
            str(cutover_checklist.get("automatic_status", "unknown")),
            "Production cutover 自动检查必须 ready。",
        ),
        _check(
            "traffic_not_switched_by_system",
            "Traffic not switched by system",
            cutover_checklist.get("cutover_status") == "blocked_by_human_signoff",
            str(cutover_checklist.get("cutover_status", "unknown")),
            "系统必须保留人工签核，不自动切生产流量。",
        ),
    ]
    passed = sum(1 for check in checks if check["passed"])
    percent = int(round(passed / len(checks) * 100)) if checks else 0
    return {
        "version": "v40.release_candidate_audit.v1",
        "automated_audit_percent": percent,
        "audit_status": "automatic_audit_passed_human_signoff_required" if percent == 100 else "needs_automatic_fix",
        "passed_check_count": passed,
        "check_count": len(checks),
        "checks": checks,
        "human_signoff_required": [
            "真实命例质量判断",
            "最终产品验收",
            "线上切换窗口",
        ],
        "boundary": "release_candidate_audit_observes_all_readiness_without_releasing_traffic",
    }


def _check(key: str, label: str, passed: bool, evidence: str, next_action: str) -> dict[str, object]:
    return {
        "key": key,
        "label": label,
        "passed": passed,
        "evidence": evidence,
        "next_action": "" if passed else next_action,
    }
