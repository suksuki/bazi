from __future__ import annotations

from v20.corpus.artifacts import read_corpus_artifact_status
from v20.validation.rule_portrait_batch import read_rule_portrait_batch_artifact
from v20.validation.rule_synthetic import read_rule_synthetic_training_artifact


def build_decision_training_plan() -> dict[str, object]:
    synthetic = read_rule_synthetic_training_artifact()
    batch = read_rule_portrait_batch_artifact()
    corpus = read_corpus_artifact_status()
    return {
        "version": "v20.decision_training_plan.v1",
        "status": "ready",
        "ui_surface": "scripts_and_admin_only",
        "runtime_user_visible": False,
        "training_targets": [
            {
                "target": "knowledge_base",
                "learns": "知识条目的覆盖、边界、术语和证据挂钩",
                "promotion_gate": "source_review_and_coverage_report",
                "current_artifact_status": "reviewed_seed_units",
            },
            {
                "target": "rule_library",
                "learns": "从知识库与 LLM 草案抽取的规则原子、碰撞条件和反例",
                "promotion_gate": "synthetic_rule_suite_and_decision_registry",
                "current_artifact_status": synthetic.get("status", "not_built"),
            },
            {
                "target": "portrait_library",
                "learns": "RuleDecision 到 DynamicPortraitTag 的映射和命理主题表达",
                "promotion_gate": "rule_portrait_batch_validation",
                "current_artifact_status": batch.get("status", "not_built"),
            },
            {
                "target": "decision_parameters",
                "learns": "裁决状态、权重、削弱条件、主线排序和推荐问题排序",
                "promotion_gate": "synthetic_cases_practitioner_controls_and_offline_priors",
                "current_artifact_status": _combined_status(synthetic, batch, corpus),
            },
        ],
        "managed_scripts": [
            "v20/scripts/extract_rules_llm.py",
            "v20/scripts/run_rule_synthetic_training.py",
            "v20/scripts/run_rule_portrait_batch.py",
            "v20/scripts/run_full_precompute.py",
            "v20/scripts/build_corpus_artifacts.py",
        ],
        "admin_surface": [
            "DB status",
            "LLM status",
            "future training artifact dashboard",
        ],
        "forbidden_runtime_sources": [
            "full_corpus_static_portrait_truth",
            "unpromoted_rule_candidate",
            "llm_direct_rule_truth",
            "free_text_practitioner_override_for_core_decision",
        ],
        "runtime_mutation": False,
        "guardrails": [
            "TRAINING_IS_OFFLINE_ONLY",
            "USER_MEASUREMENT_USES_CURRENT_CHART_DECISIONS",
            "PRACTITIONER_CONTROLS_ARE_STRUCTURED_SIGNALS",
            "PROMOTION_REQUIRES_VALIDATION_AND_REVIEW",
        ],
    }


def _combined_status(*reports: dict[str, object]) -> str:
    statuses = {str(report.get("status", "not_built")) for report in reports}
    if "fail" in statuses or "blocked" in statuses:
        return "blocked"
    if "not_built" in statuses:
        return "partial"
    return "ready"
