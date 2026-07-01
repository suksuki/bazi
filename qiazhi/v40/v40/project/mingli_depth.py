from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class MingliDepthDomain:
    key: str
    label: str
    percent: int
    status: str
    evidence_keys: tuple[str, ...]
    next_step: str


DOMAINS: tuple[MingliDepthDomain, ...] = (
    MingliDepthDomain(
        key="fact_depth",
        label="排盘事实深度",
        percent=45,
        status="needs_fact_engine_pro",
        evidence_keys=("runtime_records",),
        next_step="建立 Bazi Fact Engine Pro：节气、真太阳时、大运起运、藏干和标准版本。",
    ),
    MingliDepthDomain(
        key="signal_depth",
        label="信号覆盖深度",
        percent=62,
        status="migration_required",
        evidence_keys=("runtime_records", "training_label_events"),
        next_step="把 V30 core/evidence/rules/diagnosis 资产迁入 RuntimeSignal。",
    ),
    MingliDepthDomain(
        key="domain_depth",
        label="领域判断深度",
        percent=38,
        status="domain_adapters_missing",
        evidence_keys=("evaluation_batches", "release_readiness"),
        next_step="新增 wealth/career/relationship/health/useful_god/luck_timing/family 领域 adapter。",
    ),
    MingliDepthDomain(
        key="probe_depth",
        label="现实校准深度",
        percent=42,
        status="hidden_factor_probe_required",
        evidence_keys=("conversation_turns", "local_overlays"),
        next_step="建立 Hidden Factor Probe Engine，让回答能更新 hidden attribute 和训练标签。",
    ),
    MingliDepthDomain(
        key="training_depth",
        label="训练闭环深度",
        percent=72,
        status="spine_ready_needs_real_cases",
        evidence_keys=("training_examples", "training_example_replays", "training_replay_batches", "trainable_policy_registries"),
        next_step="训练闭环已通，下一步接真实案例验收、active policy before/after diff 和回滚补救。",
    ),
    MingliDepthDomain(
        key="evaluation_depth",
        label="验收案例深度",
        percent=48,
        status="acceptance_window_required",
        evidence_keys=("evaluation_cases", "evaluation_runs", "shadow_compare_runs"),
        next_step="建立 Real Case Bank / Acceptance Window，先收 100-200 个高质量案例。",
    ),
)


def build_mingli_depth_index(*, lab_summary: dict[str, Any] | None = None) -> dict[str, object]:
    counts = _counts(lab_summary)
    domains = [_domain_status(domain, counts) for domain in DOMAINS]
    index = int(round(sum(int(domain["completion_percent"]) for domain in domains) / len(domains)))
    return {
        "version": "v40.mingli_depth_index.v1",
        "mingli_depth_percent": index,
        "architecture_completion_reference": 98,
        "status": "rc2_mingli_depth_migration_required",
        "domains": domains,
        "priorities": [
            "P0: Real Case Bank / Acceptance Window",
            "P1: Bazi Fact Engine Pro",
            "P2: V30 Mingli Asset Migration Pipeline",
            "P3: Domain Verdict Adapters",
            "P4: Hidden Factor Probe Engine",
            "P5: Knowledge / Portrait enrichment",
        ],
        "hard_gates": [
            "V30 assets must enter through plain JSON DTO, never direct v30 import",
            "Rules become RuntimeSignal / CandidateSeed / Evidence, not Verdict",
            "Knowledge becomes KnowledgeCard / ExplanationBasis, not judge",
            "Portrait becomes low-weight PortraitSignal, not user-facing certainty",
            "Every migrated asset starts sidecar before evaluating or enabled",
            "Every migration must run before/after diff and overclaim checks",
        ],
        "runtime_evidence_counts": counts,
        "boundary": "mingli_depth_index_observes_depth_without_enabling_migrated_assets",
    }


def _domain_status(domain: MingliDepthDomain, counts: dict[str, int]) -> dict[str, object]:
    evidence = {key: counts.get(key, 0) for key in domain.evidence_keys}
    active = sum(1 for value in evidence.values() if value > 0)
    evidence_rate = round(active / len(evidence), 4) if evidence else 0.0
    return {
        "key": domain.key,
        "label": domain.label,
        "completion_percent": domain.percent,
        "status": domain.status,
        "evidence": evidence,
        "evidence_rate": evidence_rate,
        "next_step": domain.next_step,
    }


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
