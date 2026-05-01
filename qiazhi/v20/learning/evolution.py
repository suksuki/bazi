from __future__ import annotations

from v20.corpus.coverage import CorpusCoveragePlan, build_corpus_coverage_plan
from v20.validation.suite import run_synthetic_suite


def build_evolution_dry_run_plan(
    *,
    corpus_plan: CorpusCoveragePlan | None = None,
    validation_report: dict[str, object] | None = None,
) -> dict[str, object]:
    plan = corpus_plan or build_corpus_coverage_plan()
    validation = validation_report or run_synthetic_suite()
    validation_ok = bool(validation.get("ok"))
    return {
        "version": "v20.learning_evolution_plan.v1",
        "status": "ready_for_dry_run" if validation_ok else "blocked_by_validation",
        "corpus_target_case_count": plan.target_case_count,
        "corpus_shard_count": plan.shard_count,
        "validation_ok": validation_ok,
        "allowed_algorithm_tracks": [
            "embedding_retrieval_recall",
            "bayesian_confidence_calibration",
            "learning_to_rank_question_order",
            "coverage_gap_clustering",
        ],
        "deferred_algorithm_tracks": [
            "gnn_rule_graph_embedding",
            "reinforcement_learning_dialog_policy",
            "neural_conclusion_generation",
        ],
        "blocked_actions": [
            "core_rule_mutation_without_decision",
            "feature_compiler_rewrite_from_model_output",
            "automatic_fortune_conclusion_generation",
            "production_promotion_without_artifact_and_decision_records",
        ],
        "required_registries": [
            "DatasetRegistry",
            "ArtifactRegistry",
            "RunRegistry",
            "DecisionRegistry",
            "FeedbackLedger",
        ],
        "promotable_policy_targets": [
            "question_ranking_policy",
            "knowledge_retrieval_weight",
            "confidence_calibration_weight",
            "embedding_recall_shadow_policy",
        ],
        "runtime_mutation": False,
        "guardrails": [
            "EVOLUTION_PLAN_DRY_RUN_ONLY",
            "LEARNING_ASSISTS_RANKING_RETRIEVAL_AND_CALIBRATION",
            "VALIDATION_GATE_REQUIRED",
            "NO_BLACK_BOX_BAZI_VERDICT",
        ],
    }
