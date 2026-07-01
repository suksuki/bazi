from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


CURRENT_PHASE = 50
CURRENT_PHASE_NAME = "User UI Visual QA"


@dataclass(frozen=True)
class CompletionDomain:
    key: str
    label: str
    percent: int
    status: str
    evidence_keys: tuple[str, ...]
    next_step: str


DOMAINS: tuple[CompletionDomain, ...] = (
    CompletionDomain(
        key="architecture",
        label="架构主线",
        percent=99,
        status="on_track",
        evidence_keys=("runtime_records", "training_examples", "training_example_replays", "training_replay_batches", "trainable_policy_registries", "global_weight_versions", "release_readiness"),
        next_step="把 active policy 来源、影响和回滚路径在 Admin 中解释清楚。",
    ),
    CompletionDomain(
        key="user_beta",
        label="用户侧 beta",
        percent=99,
        status="on_track",
        evidence_keys=("runtime_records", "conversation_turns", "training_label_events"),
        next_step="补齐 ConsentGrant 与 Practitioner Review Queue 合同，然后做真实命例验收。",
    ),
    CompletionDomain(
        key="training_validation",
        label="训练验证闭环",
        percent=98,
        status="accelerating",
        evidence_keys=("training_label_events", "local_overlays", "training_examples", "training_example_replays", "training_replay_batches", "trainable_policy_registries", "release_readiness"),
        next_step="把训练后直接生效、影响差异和回滚补救展示到 Admin。",
    ),
    CompletionDomain(
        key="v30_replacement",
        label="替代 V30",
        percent=99,
        status="needs_more_runtime_cases",
        evidence_keys=("shadow_compare_runs", "evaluation_batches", "release_readiness"),
        next_step="增加 V30 shadow compare、真实案例回归和迁移验收。",
    ),
)


PHASE_GROUPS: tuple[dict[str, object], ...] = (
    {"range": "1-11", "label": "隔离骨架、合约、Admin/Lab、训练验证底座", "status": "complete"},
    {"range": "12-20", "label": "原生八字 runtime、Decision/Output、LLM 表达、用户页面", "status": "complete"},
    {"range": "21-24", "label": "报告后智能对话、反馈到训练", "status": "complete"},
    {"range": "25-27", "label": "紫微 Domain Lens 与命理师专业视角", "status": "complete"},
    {"range": "28-33", "label": "命理师校准、训练样本、replay 与 replay batch", "status": "complete"},
    {"range": "34", "label": "完成度实时控制面", "status": "complete"},
    {"range": "35", "label": "Replay batch -> candidate weight 前置门禁", "status": "complete"},
    {"range": "36", "label": "Release readiness 聚合 evaluation/replay evidence", "status": "complete"},
    {"range": "37", "label": "Admin candidate risk、source 与 rollback read model", "status": "complete"},
    {"range": "38", "label": "V30 shadow compare batch risk summary", "status": "complete"},
    {"range": "39", "label": "User report-first surface beta readiness", "status": "complete"},
    {"range": "40", "label": "V30 replacement readiness closeout", "status": "complete"},
    {"range": "41", "label": "Production beta cutover checklist", "status": "complete"},
    {"range": "42", "label": "Release candidate automatic audit", "status": "complete"},
    {"range": "43", "label": "Production smoke and handoff", "status": "complete"},
    {"range": "44", "label": "Final operating guide", "status": "complete"},
    {"range": "45", "label": "UI product flow、Probe calibration、Practitioner Lens IA", "status": "complete"},
    {"range": "46", "label": "User product shell runtime", "status": "complete"},
    {"range": "47", "label": "Probe answer runtime", "status": "complete"},
    {"range": "48", "label": "Probe-aware conversation context", "status": "complete"},
    {"range": "49", "label": "auth-derived user role context", "status": "complete"},
    {"range": "50", "label": "user UI visual QA", "status": "active"},
    {"range": "51+", "label": "consent/review queue、user acceptance、online cutover", "status": "requires_user"},
)


def build_project_status(*, lab_summary: dict[str, Any] | None = None) -> dict[str, object]:
    counts = _counts(lab_summary)
    domains = [_domain_status(domain, counts) for domain in DOMAINS]
    overall = _weighted_overall(domains)
    return {
        "version": "v40.project_status.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "current_phase": CURRENT_PHASE,
        "current_phase_name": CURRENT_PHASE_NAME,
        "overall_completion_percent": overall,
        "can_auto_continue": True,
        "requires_user_for": [
            "最终产品验收",
            "真实命例质量判断",
            "线上切换窗口",
            "外部账号或凭证",
        ],
        "domains": domains,
        "phase_groups": list(PHASE_GROUPS),
        "next_mainline_tasks": [
            "UI-8: ConsentGrant and practitioner review queue contracts",
            "UI-9: practitioner review queue runtime skeleton",
            "UI-10: real-case acceptance and cutover checklist rehearsal",
            "UI-11: online cutover decision with user acceptance evidence",
        ],
        "runtime_evidence_counts": counts,
        "boundary": "project_status_observes_v40_progress_without_mutating_runtime_or_weights",
    }


def _domain_status(domain: CompletionDomain, counts: dict[str, int]) -> dict[str, object]:
    evidence = {key: counts.get(key, 0) for key in domain.evidence_keys}
    active_evidence_count = sum(1 for value in evidence.values() if value > 0)
    evidence_rate = 0.0
    if evidence:
        evidence_rate = round(active_evidence_count / len(evidence), 4)
    adjusted = domain.percent
    if domain.key == "training_validation" and evidence_rate >= 0.8:
        adjusted = max(adjusted, 64)
    if domain.key == "v30_replacement" and counts and evidence.get("shadow_compare_runs", 0) == 0:
        adjusted = min(adjusted, 45)
    return {
        "key": domain.key,
        "label": domain.label,
        "completion_percent": adjusted,
        "status": domain.status,
        "evidence": evidence,
        "evidence_rate": evidence_rate,
        "next_step": domain.next_step,
    }


def _weighted_overall(domains: list[dict[str, object]]) -> int:
    weights = {
        "architecture": 0.30,
        "user_beta": 0.20,
        "training_validation": 0.30,
        "v30_replacement": 0.20,
    }
    total = 0.0
    for domain in domains:
        key = str(domain["key"])
        total += float(domain["completion_percent"]) * weights.get(key, 0.0)
    return int(round(total))


def _counts(lab_summary: dict[str, Any] | None) -> dict[str, int]:
    if not lab_summary:
        return {}
    raw_counts = lab_summary.get("counts", {})
    if not isinstance(raw_counts, dict):
        return {}
    counts: dict[str, int] = {}
    for key, value in raw_counts.items():
        try:
            counts[str(key)] = int(value)
        except (TypeError, ValueError):
            counts[str(key)] = 0
    return counts
