from __future__ import annotations

from v20.corpus.artifacts import read_corpus_artifact_status
from v20.learning.arbitration_loop import read_arbitration_loop_artifact
from v20.learning.decision_registry_iteration import read_decision_registry_iteration_artifact
from v20.learning.dynamic_decision_training import read_dynamic_decision_training_artifact
from v20.learning.knowledge_rule_review_overlay import read_knowledge_rule_review_overlay_artifact
from v20.learning.practitioner_calibration_training import read_practitioner_calibration_training_artifact
from v20.learning.rule_replay_eval import read_rule_replay_eval_artifact
from v20.learning.rule_subcondition_split import read_rule_subcondition_split_artifact
from v20.learning.question_ranking_learning import read_question_ranking_learning_artifact
from v20.validation.rule_portrait_batch import read_rule_portrait_batch_artifact
from v20.validation.rule_synthetic import read_rule_synthetic_training_artifact


def build_decision_training_plan() -> dict[str, object]:
    synthetic = read_rule_synthetic_training_artifact()
    batch = read_rule_portrait_batch_artifact()
    dynamic = read_dynamic_decision_training_artifact()
    practitioner = read_practitioner_calibration_training_artifact()
    subcondition = read_rule_subcondition_split_artifact()
    replay_eval = read_rule_replay_eval_artifact()
    decision_registry = read_decision_registry_iteration_artifact()
    rule_overlay = read_knowledge_rule_review_overlay_artifact()
    corpus = read_corpus_artifact_status()
    question_ranking = read_question_ranking_learning_artifact()
    arbitration = read_arbitration_loop_artifact()
    return {
        "version": "v20.decision_training_plan.v1",
        "status": "ready",
        "ui_surface": "scripts_and_admin_only",
        "runtime_user_visible": False,
        "training_targets": [
            {
                "target": "knowledge_base",
                "learns": "知识条目的覆盖、边界、术语和证据挂钩",
                "activation": "source_review_and_coverage_report",
                "current_artifact_status": "reviewed_seed_units",
            },
            {
                "target": "rule_library",
                "learns": "从知识库与 LLM 草案抽取的规则原子、碰撞条件、子条件和反例",
                "activation": "synthetic_rule_suite_subcondition_split_replay_eval_decision_registry_iteration",
                "current_artifact_status": _combined_status(synthetic, rule_overlay, subcondition, replay_eval, decision_registry),
            },
            {
                "target": "knowledge_rule_review_overlay",
                "learns": "把知识规则的 synthetic、corpus、activation 状态固化为可版本锁定的后台 artifact",
                "activation": "artifact_registry_or_postgres_import_for_runtime_iteration",
                "current_artifact_status": rule_overlay.get("status", "not_built"),
            },
            {
                "target": "decision_registry",
                "learns": "把规则、子条件、反例和 replay eval 证据整理成可持续迭代的台账记录",
                "activation": "system_iteration_records_active_runtime_updates",
                "current_artifact_status": decision_registry.get("status", "not_built"),
            },
            {
                "target": "rule_replay_eval",
                "learns": "检查子条件信号是否已连上画像映射、裁决域覆盖和回放记录",
                "activation": "continuous_replay_eval_for_active_rules",
                "current_artifact_status": replay_eval.get("status", "not_built"),
            },
            {
                "target": "portrait_library",
                "learns": "RuleDecision / DecisionState 到 PortraitAxis 的映射和命理主题表达",
                "activation": "rule_portrait_batch_validation",
                "current_artifact_status": batch.get("status", "not_built"),
            },
            {
                "target": "decision_parameters",
                "learns": "裁决状态、权重、削弱条件、主线排序和推荐问题排序",
                "activation": "dynamic_decision_training_batch_practitioner_controls_arbitration_loop_and_offline_priors",
                "current_artifact_status": _combined_status(synthetic, batch, dynamic, practitioner, arbitration, corpus),
            },
            {
                "target": "arbitration_loop",
                "learns": "mixed/countered/requires_review 冲突快照、反证权重和命理师复核队列",
                "activation": "practitioner_calibration_rule_replay_eval_and_counterexample_weighting",
                "current_artifact_status": arbitration.get("status", "not_built"),
            },
            {
                "target": "question_ranking",
                "learns": "问题排序偏好、领域优先级、规则前缀与状态倾斜",
                "activation": "runtime_question_backfill + shadow_ranking_report + practitioner_feedback",
                "current_artifact_status": question_ranking.get("status", "not_built"),
            },
        ],
        "managed_scripts": [
            "v20/scripts/extract_rules_llm.py",
            "v20/scripts/run_rule_synthetic_training.py",
            "v20/scripts/run_knowledge_rule_review_overlay.py",
            "v20/scripts/run_rule_subcondition_split.py",
            "v20/scripts/run_rule_replay_eval.py",
            "v20/scripts/run_decision_registry_iteration.py",
            "v20/scripts/run_question_source_training.py",
            "v20/scripts/run_question_dag_training.py",
            "v20/scripts/run_role_interaction_training.py",
            "v20/scripts/run_synthetic_case_suite.py",
            "v20/scripts/run_question_ranking_training.py",
            "v20/scripts/run_rule_portrait_batch.py",
            "v20/scripts/run_practitioner_calibration_training.py",
            "v20/scripts/run_training_iteration.py",
            "v20/scripts/run_knowledge_rule_orchestrator.py",
            "v20/scripts/run_nightly_learning_executor.py",
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
            "untraced_rule_signal",
            "llm_direct_rule_truth",
            "free_text_practitioner_override_for_core_decision",
        ],
        "runtime_mutation": False,
        "guardrails": [
            "TRAINING_FEEDS_ACTIVE_ITERATION",
            "USER_MEASUREMENT_USES_CURRENT_CHART_DECISIONS",
            "PRACTITIONER_CONTROLS_ARE_STRUCTURED_SIGNALS",
            "VALIDATION_REFINES_ACTIVE_RULES",
        ],
    }


def _combined_status(*reports: dict[str, object]) -> str:
    statuses = {str(report.get("status", "not_built")) for report in reports}
    if "fail" in statuses or "blocked" in statuses:
        return "blocked"
    if "not_built" in statuses:
        return "partial"
    return "ready"
