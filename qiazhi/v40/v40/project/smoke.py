from __future__ import annotations

from typing import Any


def build_production_smoke(
    *,
    project_status: dict[str, Any],
    surface_readiness: dict[str, Any],
    replacement_readiness: dict[str, Any],
    cutover_checklist: dict[str, Any],
    release_candidate_audit: dict[str, Any],
) -> dict[str, object]:
    checks = [
        _check("project_status", project_status.get("current_phase", 0) >= 42, str(project_status.get("current_phase", ""))),
        _check("surface", surface_readiness.get("beta_status") == "ready", str(surface_readiness.get("beta_status", ""))),
        _check("replacement", replacement_readiness.get("status") == "candidate_ready", str(replacement_readiness.get("status", ""))),
        _check("cutover", cutover_checklist.get("automatic_status") == "ready", str(cutover_checklist.get("automatic_status", ""))),
        _check(
            "release_candidate",
            release_candidate_audit.get("audit_status") == "automatic_audit_passed_human_signoff_required",
            str(release_candidate_audit.get("audit_status", "")),
        ),
    ]
    passed = sum(1 for check in checks if check["passed"])
    percent = int(round(passed / len(checks) * 100)) if checks else 0
    return {
        "version": "v40.production_smoke.v1",
        "smoke_percent": percent,
        "smoke_status": "passed_handoff_ready" if percent == 100 else "needs_fix",
        "passed_check_count": passed,
        "check_count": len(checks),
        "checks": checks,
        "handoff_notes": [
            "自动烟测不等于上线。",
            "下一步由用户进行真实命例验收。",
            "线上切换窗口必须人工确认。",
        ],
        "boundary": "production_smoke_observes_v40_readiness_without_switching_traffic",
    }


def _check(key: str, passed: bool, evidence: str) -> dict[str, object]:
    return {"key": key, "passed": passed, "evidence": evidence}
