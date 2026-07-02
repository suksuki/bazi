from __future__ import annotations

from typing import Any


def build_online_cutover_decision_pack(
    *,
    project_status: dict[str, Any],
    cutover_checklist: dict[str, Any],
    real_case_evidence: dict[str, Any],
    training_activation_evidence: dict[str, Any],
    release_candidate_audit: dict[str, Any] | None = None,
) -> dict[str, object]:
    checks = [
        _check(
            key="project_status_ready",
            label="Project status ready",
            passed=int(project_status.get("overall_completion_percent", 0)) >= 99,
            evidence=f"{project_status.get('overall_completion_percent', 0)}%",
            next_action="继续补齐主线任务和状态证据。",
        ),
        _check(
            key="cutover_automatic_ready",
            label="Cutover automatic checks ready",
            passed=cutover_checklist.get("automatic_status") == "ready",
            evidence=str(cutover_checklist.get("automatic_status", "unknown")),
            next_action="先补齐 replacement、active weight、rollback、LLM 和 repository 配置。",
        ),
        _check(
            key="real_case_evidence_ready",
            label="Real case evidence ready",
            passed=real_case_evidence.get("automatic_status") == "ready",
            evidence=str(real_case_evidence.get("automatic_status", "unknown")),
            next_action="补齐真实命例数量、主题覆盖和 Acceptance Window。",
        ),
        _check(
            key="training_activation_explainable",
            label="Training activation explainable",
            passed=training_activation_evidence.get("automatic_status") == "ready"
            and bool(training_activation_evidence.get("rollback_ready")),
            evidence=str(training_activation_evidence.get("automatic_status", "unknown")),
            next_action="补齐训练影响 before/after、回滚指针或 replay 验收。",
        ),
        _check(
            key="release_audit_ready",
            label="Release audit ready",
            passed=_release_audit_ready(release_candidate_audit),
            evidence=str((release_candidate_audit or {}).get("audit_status", "not_supplied")),
            next_action="运行 release candidate audit 并处理自动检查失败项。",
        ),
    ]
    passed_count = sum(1 for check in checks if check["passed"])
    percent = int(round(passed_count / len(checks) * 100)) if checks else 0
    decision = _decision(percent=percent)
    return {
        "version": "v40.online_cutover_decision_pack.v1",
        "decision_status": decision,
        "decision_percent": percent,
        "passed_check_count": passed_count,
        "check_count": len(checks),
        "checks": checks,
        "manual_signoff_required": [
            "真实命例质量判断",
            "最终产品验收",
            "线上切换窗口",
        ],
        "traffic_switch_allowed_by_system": False,
        "user_acceptance_required": decision == "ready_for_human_signoff",
        "blockers": [check for check in checks if not check["passed"]],
        "decision_summary": _decision_summary(decision=decision, percent=percent),
        "next_actions": _next_actions(checks=checks, decision=decision),
        "writes_v30_state": False,
        "writes_v40_production": False,
        "boundary": "online_cutover_decision_reads_evidence_without_switching_traffic",
    }


def _release_audit_ready(release_candidate_audit: dict[str, Any] | None) -> bool:
    if not release_candidate_audit:
        return False
    return release_candidate_audit.get("audit_status") == "automatic_audit_passed_human_signoff_required"


def _decision(percent: int) -> str:
    if percent == 100:
        return "ready_for_human_signoff"
    if percent >= 80:
        return "near_ready_with_blockers"
    return "blocked_by_evidence"


def _decision_summary(*, decision: str, percent: int) -> str:
    if decision == "ready_for_human_signoff":
        return "自动证据已齐，系统仍不切流量，等待真实命例质量判断、最终产品验收和线上切换窗口。"
    if decision == "near_ready_with_blockers":
        return f"上线证据完成度 {percent}%，接近可验收，但仍有阻塞项需要补齐。"
    return f"上线证据完成度 {percent}%，当前不应进入人工切换窗口。"


def _next_actions(*, checks: list[dict[str, object]], decision: str) -> list[str]:
    if decision == "ready_for_human_signoff":
        return [
            "安排真实命例人工验收。",
            "确认线上切换窗口。",
            "保留 rollback registry / rollback weight 指针。",
        ]
    return [str(check["next_action"]) for check in checks if not check["passed"]]


def _check(key: str, label: str, passed: bool, evidence: str, next_action: str) -> dict[str, object]:
    return {
        "key": key,
        "label": label,
        "passed": passed,
        "evidence": evidence,
        "next_action": "" if passed else next_action,
    }
