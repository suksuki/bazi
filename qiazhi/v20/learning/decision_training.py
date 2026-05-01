from __future__ import annotations

from v20.corpus.artifacts import read_corpus_artifact_status
from v20.learning.decision_registry_review import read_decision_registry_review_artifact
from v20.learning.dynamic_decision_training import read_dynamic_decision_training_artifact
from v20.learning.knowledge_rule_review_overlay import read_knowledge_rule_review_overlay_artifact
from v20.learning.practitioner_calibration_training import read_practitioner_calibration_training_artifact
from v20.learning.rule_subcondition_split import read_rule_subcondition_split_artifact
from v20.validation.rule_portrait_batch import read_rule_portrait_batch_artifact
from v20.validation.rule_synthetic import read_rule_synthetic_training_artifact


def build_decision_training_plan() -> dict[str, object]:
    synthetic = read_rule_synthetic_training_artifact()
    batch = read_rule_portrait_batch_artifact()
    dynamic = read_dynamic_decision_training_artifact()
    practitioner = read_practitioner_calibration_training_artifact()
    subcondition = read_rule_subcondition_split_artifact()
    decision_registry = read_decision_registry_review_artifact()
    rule_overlay = read_knowledge_rule_review_overlay_artifact()
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
                "learns": "从知识库与 LLM 草案抽取的规则原子、碰撞条件、子条件和反例",
                "promotion_gate": "synthetic_rule_suite_subcondition_split_decision_registry_review",
                "current_artifact_status": _combined_status(synthetic, rule_overlay, subcondition, decision_registry),
            },
            {
                "target": "knowledge_rule_review_overlay",
                "learns": "把知识规则的 synthetic、corpus、promotion gate 状态固化为可版本锁定的后台 artifact",
                "promotion_gate": "artifact_registry_or_postgres_import_before_runtime_version_consumption",
                "current_artifact_status": rule_overlay.get("status", "not_built"),
            },
            {
                "target": "decision_registry",
                "learns": "把规则、子条件、反例和 shadow 权重候选整理成可批量裁决的台账记录",
                "promotion_gate": "human_or_admin_review_before_any_runtime_activation",
                "current_artifact_status": decision_registry.get("status", "not_built"),
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
                "promotion_gate": "dynamic_decision_training_batch_practitioner_controls_and_offline_priors",
                "current_artifact_status": _combined_status(synthetic, batch, dynamic, practitioner, corpus),
            },
        ],
        "managed_scripts": [
            "v20/scripts/extract_rules_llm.py",
            "v20/scripts/run_rule_synthetic_training.py",
            "v20/scripts/run_knowledge_rule_review_overlay.py",
            "v20/scripts/run_rule_subcondition_split.py",
            "v20/scripts/run_decision_registry_review.py",
            "v20/scripts/run_rule_portrait_batch.py",
            "v20/scripts/run_dynamic_decision_training.py",
            "v20/scripts/run_practitioner_calibration_training.py",
            "v20/scripts/run_training_iteration.py",
            "v20/scripts/import_calibration_postgres.py",
            "v20/scripts/import_decision_registry_postgres.py",
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
