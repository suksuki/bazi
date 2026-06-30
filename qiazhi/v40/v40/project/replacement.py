from __future__ import annotations

from typing import Any


def build_v30_replacement_readiness(
    *,
    lab_summary: dict[str, Any] | None = None,
    surface_readiness: dict[str, Any] | None = None,
) -> dict[str, object]:
    counts = _counts(lab_summary)
    surface_status = str((surface_readiness or {}).get("beta_status", "review"))
    gates = [
        _gate(
            "shadow_compare_batch",
            "V30 shadow compare",
            counts.get("shadow_compare_runs", 0) >= 3,
            f"{counts.get('shadow_compare_runs', 0)} shadow compare runs",
            "至少保留三条迁移对比样本。",
        ),
        _gate(
            "evaluation_release_readiness",
            "Evaluation + readiness",
            counts.get("evaluation_batches", 0) > 0 and counts.get("release_readiness", 0) > 0,
            f"{counts.get('evaluation_batches', 0)} batches / {counts.get('release_readiness', 0)} readiness",
            "需要 evaluation batch 和 release readiness 同时存在。",
        ),
        _gate(
            "training_feedback_loop",
            "Feedback training loop",
            counts.get("training_examples", 0) > 0
            and counts.get("training_example_replays", 0) > 0
            and counts.get("training_replay_batches", 0) > 0,
            (
                f"{counts.get('training_examples', 0)} examples / "
                f"{counts.get('training_example_replays', 0)} replays / "
                f"{counts.get('training_replay_batches', 0)} replay batches"
            ),
            "训练样本、回放和批量回放都需要打通。",
        ),
        _gate(
            "candidate_weight_audit",
            "Candidate weight audit",
            counts.get("global_weight_versions", 0) > 0 and counts.get("weight_activation_reviews", 0) > 0,
            f"{counts.get('global_weight_versions', 0)} weights / {counts.get('weight_activation_reviews', 0)} reviews",
            "候选权重必须有审核记录，不能裸写生产。",
        ),
        _gate(
            "user_surface_beta",
            "User surface beta",
            surface_status == "ready",
            f"surface beta status: {surface_status}",
            "用户侧 report-first beta readiness 必须 ready。",
        ),
        _gate(
            "v40_isolated_runtime",
            "V40 isolated runtime",
            True,
            "V40 API/Admin/DB prefixes are isolated by contract.",
            "保持 V40 与 V30 独立隔离。",
        ),
    ]
    ready_count = sum(1 for gate in gates if gate["ready"])
    percent = int(round(ready_count / len(gates) * 100)) if gates else 0
    return {
        "version": "v40.v30_replacement_readiness.v1",
        "readiness_percent": percent,
        "status": "candidate_ready" if percent == 100 else "needs_evidence",
        "ready_gate_count": ready_count,
        "gate_count": len(gates),
        "gates": gates,
        "requires_human_signoff": [
            "真实命例质量判断",
            "最终产品验收",
            "线上切换窗口",
        ],
        "boundary": "v30_replacement_readiness_observes_v40_evidence_without_mutation",
    }


def _gate(key: str, label: str, ready: bool, evidence: str, next_action: str) -> dict[str, object]:
    return {
        "key": key,
        "label": label,
        "ready": ready,
        "evidence": evidence,
        "next_action": "" if ready else next_action,
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
