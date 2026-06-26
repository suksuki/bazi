from __future__ import annotations


CENTRAL_BRAIN_ARCHITECTURE_VERSION = "v20.central_brain_architecture.v1"


def build_central_brain_architecture_status() -> dict[str, object]:
    modules = _modules()
    training_topics = _training_topics()
    pointer_targets = tuple(
        dict.fromkeys(
            target
            for topic in training_topics
            for target in topic["runtime_pointer_targets"]
            if isinstance(target, str) and target
        )
    )
    return {
        "version": CENTRAL_BRAIN_ARCHITECTURE_VERSION,
        "status": "active_ready",
        "completion_percent": 100,
        "architecture_doc": "docs/V20_CENTRAL_BRAIN_INTELLIGENCE_ARCHITECTURE.md",
        "principles": {
            "central_brain_controls_modules": True,
            "high_iteration_training": True,
            "no_human_review_gate": True,
            "training_outputs_apply_directly": True,
            "training_signals_unified_by_tuning_package": True,
            "ui_must_show_start_progress_effect_and_rollback": True,
        },
        "brain_graph": {
            "version": "v20.central_brain_graph_contract.v1",
            "nodes": _brain_graph_nodes(),
            "node_output_contract": (
                "status",
                "inputs",
                "outputs",
                "metrics",
                "parameter_targets",
                "runtime_pointer_targets",
                "blocking_machine_reason",
                "runtime_mutation",
            ),
            "runtime_mutation": False,
        },
        "modules": modules,
        "llm_prompt_context_design": _llm_prompt_context_design(),
        "training_topics": training_topics,
        "tuning_package_contract": _tuning_package_contract(),
        "runtime_pointer_targets": pointer_targets,
        "ui_alignment": {
            "admin_surface": "admin_training_console",
            "required_panels": (
                "mainline_status",
                "central_brain_graph",
                "training_topics",
                "atomic_training_tasks",
                "current_background_task",
                "parameter_targets",
                "runtime_pointer_effects",
                "rollback_entry",
            ),
            "required_task_fields": (
                "description",
                "parameter_targets",
                "impacted_modules",
                "runtime_pointer_targets",
                "background_execution",
                "progress",
                "latest_effect",
                "blocking_machine_reason",
            ),
            "runtime_mutation": False,
        },
        "framework_patterns": (
            _framework("langgraph", "state_graph_and_conditional_edges", "BrainGraph"),
            _framework("ray", "distributed_replay_and_training", "518k_shard_executor"),
            _framework("mlflow", "run_artifact_registry", "runtime_artifact_and_pointer_registry"),
            _framework("feast", "offline_online_feature_store", "bazi_portrait_role_feature_layers"),
            _framework("great_expectations", "data_quality_validation", "synthetic_and_corpus_validation"),
            _framework("opentelemetry", "traces_metrics_logs", "training_and_pointer_observability"),
            _framework("dspy", "program_parameter_optimization", "answer_governance_and_question_policy_optimization"),
        ),
        "next_actions": (
            {
                "step": "admin_ui_central_brain_console",
                "target": "frontend/admin.js",
                "reason": "Admin UI must show central brain graph, training topics, pointer effects, and rollback.",
            },
            {
                "step": "brain_graph_registry",
                "target": "ops/training_tasks.py",
                "reason": "Training task registry should group atomic tasks by BrainGraph node.",
            },
            {
                "step": "corpus_518k_brain_node",
                "target": "learning_orchestrator/nightly_executor.py",
                "reason": "518K shard executor should report parameter targets and pointer targets through BrainGraph.",
            },
        ),
        "runtime_mutation": False,
        "guardrails": [
            "CENTRAL_BRAIN_ARCHITECTURE_STATUS_READ_ONLY",
            "NO_HUMAN_REVIEW_GATE_FOR_TRAINING",
            "TRAINING_OUTPUTS_MUST_DECLARE_PARAMETER_TARGETS",
            "CENTRAL_BRAIN_TUNING_PACKAGE_UNIFIES_TRAINING_SIGNALS",
            "UI_ALIGNMENT_REQUIRED_FOR_NEW_TRAINING_SURFACES",
        ],
    }


def _brain_graph_nodes() -> tuple[dict[str, object], ...]:
    return (
        _node("knowledge_gap_pick", "Knowledge Brain", "Find missing bazi knowledge topics."),
        _node("knowledge_atom_contract", "Knowledge Brain", "Require rules, portraits, questions, boundaries, counterexamples."),
        _node("rule_candidate_generation", "Rule Brain", "Generate traceable rule candidates from knowledge."),
        _node("portrait_mapping_generation", "Portrait Brain", "Map rule and topic evidence to portrait axes."),
        _node("question_policy_generation", "Question Brain", "Generate question source, ranking, and DAG candidates."),
        _node("role_policy_generation", "Role Brain", "Generate role-specific visibility and expression policy."),
        _node("llm_context_policy_generation", "LLM Context Brain", "Generate prompt context contracts, role context, bazi context, and answer contract weights."),
        _node("synthetic_case_binding", "Synthetic Lab", "Bind synthetic cases and forbidden outputs."),
        _node("synthetic_validation", "Synthetic Lab", "Validate rule collision, boundaries, and counterexamples."),
        _node("corpus_replay_518k", "Corpus Trainer", "Run deterministic shard/full replay for distribution calibration."),
        _node("parameter_optimizer", "Parameter Optimizer", "Emit parameter targets from training artifacts."),
        _node("runtime_pointer_publish", "Runtime Publisher", "Write active runtime pointers after machine success."),
        _node("ui_observability", "Admin Console", "Show start, progress, result, pointer effect, and rollback."),
    )


def _modules() -> tuple[dict[str, object], ...]:
    return (
        _module("knowledge", "知识库", "knowledge_runtime_policy_pointer", ("knowledge_rule_orchestrator", "knowledge_rule_review_overlay")),
        _module("rule", "八字规则", "rule_runtime_policy_pointer", ("rule_synthetic_training", "rule_replay_eval", "decision_registry_iteration")),
        _module("portrait", "八字画像", "portrait_runtime_policy_pointer", ("rule_portrait_batch", "practitioner_calibration_training")),
        _module("question", "智能问题", "question_runtime_policy_pointer", ("question_source_training", "question_ranking_training", "question_dag_training")),
        _module("role_view", "角色视图", "role_view_runtime_policy_pointer", ("role_interaction_training",)),
        _module("llm_context", "LLM 上下文", "role_view_runtime_policy_pointer", ("answer_governance_training", "role_interaction_training", "synthetic_case_suite")),
        _module("synthetic", "合成数据", "synthetic_training_artifact", ("synthetic_case_suite", "rule_synthetic_training")),
        _module("corpus_518k", "518K 全量训练", "corpus_runtime_policy_pointer", ("nightly_executor_skeleton", "full_precompute_preview")),
        _module("orchestrator", "中枢策略", "orchestrator_runtime_policy_pointer", ("training_iteration_fast", "training_iteration_deep")),
    )


def _training_topics() -> tuple[dict[str, object], ...]:
    return (
        _topic(
            "central_brain",
            "中枢联合训练",
            ("knowledge_rule_orchestrator", "training_iteration_fast", "training_iteration_deep"),
            ("orchestrator_knowledge_rule_loop_weight", "mainline_focus_weight"),
            ("orchestrator_runtime_policy_pointer", "knowledge_runtime_policy_pointer", "rule_runtime_policy_pointer"),
        ),
        _topic(
            "knowledge_rule",
            "知识规则联合训练",
            ("knowledge_rule_orchestrator", "knowledge_rule_review_overlay", "rule_synthetic_training"),
            ("knowledge_rule_mapping_weight", "rule_synthetic_confidence_weight", "counterexample_gap_weight"),
            ("knowledge_runtime_policy_pointer", "rule_runtime_policy_pointer"),
        ),
        _topic(
            "portrait_question_role",
            "画像问题角色联合训练",
            ("rule_portrait_batch", "question_dag_training", "role_interaction_training"),
            ("portrait_axis_weight", "question_rank_weight", "role_question_order"),
            ("portrait_runtime_policy_pointer", "question_runtime_policy_pointer", "role_view_runtime_policy_pointer"),
        ),
        _topic(
            "llm_context",
            "LLM 上下文训练",
            ("answer_governance_training", "role_interaction_training", "synthetic_case_suite", "training_iteration_fast"),
            ("role_context_density_weight", "bazi_context_profile_weight", "answer_contract_structure_weight", "prompt_context_budget_weight"),
            ("role_view_runtime_policy_pointer", "knowledge_runtime_policy_pointer", "orchestrator_runtime_policy_pointer"),
        ),
        _topic(
            "synthetic",
            "合成数据验证训练",
            ("synthetic_case_suite", "rule_synthetic_training"),
            ("rule_synthetic_confidence_weight", "counterexample_gap_weight"),
            ("rule_runtime_policy_pointer",),
        ),
        _topic(
            "corpus_518k",
            "518K 全量训练",
            ("nightly_executor_skeleton", "full_precompute_preview"),
            ("feature_threshold", "coverage_prior", "similar_case_weight", "corpus_shard_quality"),
            ("corpus_runtime_policy_pointer",),
        ),
    )


def _llm_prompt_context_design() -> dict[str, object]:
    return {
        "version": "v20.llm_prompt_context_design_status.v1",
        "status": "complete",
        "completion_percent": 100,
        "design_doc": "docs/V20_LLM_PROMPT_CONTEXT_DESIGN.md",
        "prompt_policy": "short_prompt_structured_context_answer_contract",
        "context_layers": (
            "context.system_understanding",
            "context.system_understanding.role_context",
            "context.system_understanding.bazi_context_profile",
            "context.context_budget",
            "answer_contract",
            "questions[].question_narrative",
            "answer_plan_rewrite.context.v2",
        ),
        "runtime_consumers": (
            "llm.prompts.practitioner_answer_prompt",
            "llm.prompts.answer_rewrite_prompt",
            "llm.context.build_llm_context_pack",
        ),
        "retired_context_paths": ("answer/prompt_context.py",),
        "prompt_budget": {
            "practitioner_answer_max_chars": 9000,
            "practitioner_answer_target_chars": 8500,
            "practitioner_stream_payload_max_chars": 7800,
            "answer_rewrite_target_max_chars": 6500,
        },
        "ui_labels": (
            "短提示词",
            "结构化上下文",
            "角色上下文",
            "八字结构上下文",
            "回答合同",
            "旧上下文已清理",
        ),
        "runtime_mutation": False,
    }


def _tuning_package_contract() -> dict[str, object]:
    return {
        "version": "v20.central_brain_tuning_package_contract.v1",
        "status": "active",
        "owner_node": "parameter_optimizer",
        "input_signals": (
            "bazi_context_drift_score",
            "synthetic_pass_rate",
            "rule_false_positive_rate",
            "portrait_drift_score",
            "question_focus_score",
            "corpus_distribution_shift",
            "similar_case_stability",
        ),
        "output_contract": (
            "decision",
            "parameter_updates",
            "runtime_pointer_targets",
            "gate_blockers",
            "activation_policy",
        ),
        "direct_apply_requirements": (
            "context_drift_score == 0",
            "synthetic_status == covered",
            "corpus_training_status == ready",
            "candidate_promotion_score >= promotion_threshold",
            "optimizer_writer_status == ready",
        ),
        "runtime_mutation": False,
        "guardrails": [
            "TUNING_PACKAGE_IS_CENTRAL_BRAIN_DECISION_INPUT",
            "NO_SEPARATE_MODULE_LOCAL_PROMOTION_WITHOUT_PACKAGE",
            "NO_HUMAN_REVIEW_GATE",
        ],
    }


def _node(node_key: str, owner: str, purpose: str) -> dict[str, object]:
    return {
        "node_key": node_key,
        "owner": owner,
        "purpose": purpose,
        "runtime_mutation": False,
    }


def _module(module_key: str, label: str, pointer_target: str, atomic_trainings: tuple[str, ...]) -> dict[str, object]:
    return {
        "module_key": module_key,
        "label": label,
        "control_status": "central_brain_controlled",
        "runtime_pointer_target": pointer_target,
        "atomic_trainings": atomic_trainings,
        "runtime_mutation": False,
    }


def _topic(
    topic_key: str,
    label: str,
    atomic_trainings: tuple[str, ...],
    parameter_targets: tuple[str, ...],
    runtime_pointer_targets: tuple[str, ...],
) -> dict[str, object]:
    return {
        "topic_key": topic_key,
        "label": label,
        "atomic_trainings": atomic_trainings,
        "parameter_targets": parameter_targets,
        "runtime_pointer_targets": runtime_pointer_targets,
        "activation_policy": "direct_apply_without_human_review_gate",
        "runtime_mutation": False,
    }


def _framework(framework_key: str, borrowed_pattern: str, v20_target: str) -> dict[str, object]:
    return {
        "framework_key": framework_key,
        "borrowed_pattern": borrowed_pattern,
        "v20_target": v20_target,
        "adoption_mode": "pattern_first_no_heavy_dependency",
        "runtime_mutation": False,
    }
