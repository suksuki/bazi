"""V30 validation cases and evaluators."""

from v30.validation.synthetic_case import (
    SYNTHETIC_GRADIENT_CASES,
    SYNTHETIC_CORE_CALCULATION_CASES,
    SYNTHETIC_PRACTICAL_MAINLINE_CASES,
    SYNTHETIC_INTERACTION_LOOP_CASES,
    SYNTHETIC_INTERACTION_BRAIN_STRUCTURED_CONSTRAINT_CASES,
    SYNTHETIC_CENTRAL_BRAIN_CASES,
    SYNTHETIC_BAZI_LLM_ACCEPTANCE_CASES,
    SYNTHETIC_UI_CORE_READING_PRODUCT_CASES,
    SYNTHETIC_REAL_BAZI_DIAGNOSIS_CASES,
    SYNTHETIC_ARCHETYPE_RULE_CLAIM_CASES,
    SYNTHETIC_TYPICAL_BAZI_ANSWER_CASES,
    SYNTHETIC_CANONICAL_BAZI_CALIBRATION_CASES,
    SYNTHETIC_TRAINING_PIPELINE_CASES,
    SYNTHETIC_M1_M2_BAZI_CALCULATION_CASES,
    SYNTHETIC_M4_TEN_GOD_REAL_CASE_REPLAY_CASES,
    SYNTHETIC_REAL_CASE_CALIBRATION_PACK_CASES,
    SYNTHETIC_REAL_CASE_VALIDATION_CASES,
    SYNTHETIC_SMOKE_CASES,
    SYNTHETIC_SUITES,
    SyntheticBaziCase,
    SyntheticValidationResult,
    SyntheticValidationSuiteResult,
    run_synthetic_case,
    run_synthetic_suite,
    run_synthetic_tier,
)
from v30.validation.corpus_518k import Corpus518KValidationResult, CorpusSourceCase, run_518k_validation
from v30.validation.corpus_518k_readiness_matrix import (
    build_518k_readiness_matrix,
    run_518k_readiness_matrix,
)
from v30.validation.llm_live_smoke import LLMLiveSmokeResult, run_llm_live_smoke
from v30.validation.production_replay_metadata import build_production_replay_metadata, summarize_production_replay_metadata
from v30.validation.production_replay_intake import build_production_replay_intake_batch, build_production_replay_intake_row, summarize_production_replay_intake
from v30.validation.release_gate import ReleaseGateCheck, ReleaseGateResult, run_release_gate
from v30.validation.release_artifact_review import build_release_artifact_review
from v30.validation.post_seal_status_review import build_post_seal_status_review
from v30.validation.release_candidate_review import build_release_candidate_review
from v30.validation.release_candidate_gate_review import build_release_candidate_gate_review
from v30.validation.release_boundary_finalization import build_release_boundary_finalization
from v30.validation.frozen_core_calibration_review import (
    DEFAULT_FROZEN_CORE_CALIBRATION_TIERS,
    build_frozen_core_calibration_review,
    run_frozen_core_calibration_review,
)
from v30.validation.targeted_calibration_candidate_review import (
    DEFAULT_TARGETED_CALIBRATION_FAMILIES,
    build_targeted_calibration_candidate_review,
    run_targeted_calibration_candidate_review,
)
from v30.validation.targeted_calibration_validation_gate import (
    build_targeted_calibration_validation_gate,
    run_targeted_calibration_validation_gate,
)
from v30.validation.targeted_calibration_pointer_review import (
    build_targeted_calibration_pointer_review,
    run_targeted_calibration_pointer_review,
)
from v30.validation.targeted_calibration_pointer_decision import (
    build_targeted_calibration_pointer_decision,
    run_targeted_calibration_pointer_decision,
)
from v30.validation.targeted_calibration_closeout import (
    build_targeted_calibration_closeout,
    run_targeted_calibration_closeout,
)
from v30.validation.mainline_selection import build_mainline_selection, run_mainline_selection
from v30.validation.core_calibration_observation_summary import (
    build_core_calibration_observation_summary,
    run_core_calibration_observation_summary,
)
from v30.validation.core_calibration_drift_watch import (
    build_core_calibration_drift_watch,
    run_core_calibration_drift_watch,
)
from v30.validation.focused_core_calibration_evidence_queue import (
    build_focused_core_calibration_evidence_queue,
    run_focused_core_calibration_evidence_queue,
)
from v30.validation.core_calibration_queue_review import (
    build_core_calibration_queue_review,
    run_core_calibration_queue_review,
)
from v30.validation.core_calibration_watch_closeout import (
    build_core_calibration_watch_closeout,
    run_core_calibration_watch_closeout,
)
from v30.validation.central_brain_acceptance import (
    build_central_brain_acceptance,
    run_central_brain_acceptance,
)
from v30.validation.central_brain_session_replay import (
    build_central_brain_session_replay,
    run_central_brain_session_replay,
)
from v30.validation.central_brain_failure_routing import (
    build_central_brain_failure_routing,
    run_central_brain_failure_routing,
)
from v30.validation.central_reading_synthetic_validation import (
    CENTRAL_READING_SYNTHETIC_VALIDATION_VERSION,
    build_central_reading_synthetic_validation,
    run_central_reading_synthetic_validation,
)
from v30.validation.dialogue_training_calibration_loop import (
    DIALOGUE_TRAINING_CALIBRATION_VALIDATION_VERSION,
    build_dialogue_training_calibration_validation,
    run_dialogue_training_calibration_validation,
)
from v30.validation.dialogue_policy_candidate_review import (
    DIALOGUE_POLICY_CANDIDATE_REVIEW_VALIDATION_VERSION,
    build_dialogue_policy_candidate_review_validation,
    run_dialogue_policy_candidate_review_validation,
)
from v30.validation.dialogue_strategy_validation_gate import (
    DIALOGUE_STRATEGY_VALIDATION_GATE_VALIDATION_VERSION,
    build_dialogue_strategy_validation_gate_validation,
    run_dialogue_strategy_validation_gate_validation,
)
from v30.validation.dialogue_synthetic_replay_queue import (
    DIALOGUE_SYNTHETIC_REPLAY_QUEUE_VALIDATION_VERSION,
    build_dialogue_synthetic_replay_queue_validation,
    run_dialogue_synthetic_replay_queue_validation,
)
from v30.validation.dialogue_operator_review_pack import (
    DIALOGUE_OPERATOR_REVIEW_PACK_VALIDATION_VERSION,
    build_dialogue_operator_review_pack_validation,
    run_dialogue_operator_review_pack_validation,
)
from v30.validation.dialogue_heavy_validation_decision import (
    DIALOGUE_HEAVY_VALIDATION_DECISION_VALIDATION_VERSION,
    build_dialogue_heavy_validation_decision_validation,
    run_dialogue_heavy_validation_decision_validation,
)
from v30.validation.dialogue_heavy_validation_authorization import (
    DIALOGUE_HEAVY_VALIDATION_AUTHORIZATION_VALIDATION_VERSION,
    build_dialogue_heavy_validation_authorization_validation,
    run_dialogue_heavy_validation_authorization_validation,
)
from v30.validation.dialogue_heavy_validation_execution_plan import (
    DIALOGUE_HEAVY_VALIDATION_EXECUTION_PLAN_VALIDATION_VERSION,
    build_dialogue_heavy_validation_execution_plan_validation,
    run_dialogue_heavy_validation_execution_plan_validation,
)
from v30.validation.training_system_closeout import (
    build_training_system_closeout,
    run_training_system_closeout,
)
from v30.validation.training_candidate_quarantine import (
    build_training_candidate_quarantine,
    run_training_candidate_quarantine,
)
from v30.validation.synthetic_coverage_manifest import (
    build_synthetic_coverage_manifest,
    run_synthetic_coverage_manifest,
)
from v30.validation.stage_option_intelligence_replay import (
    STAGE_OPTION_INTELLIGENCE_REPLAY_VERSION,
    run_stage_option_intelligence_replay,
)
from v30.validation.text_option_synthetic_validation import (
    TEXT_OPTION_SYNTHETIC_VALIDATION_VERSION,
    run_text_option_synthetic_validation,
)
from v30.validation.llm_prompt_profile_quality_audit import (
    LLM_PROMPT_PROFILE_QUALITY_AUDIT_VERSION,
    run_llm_prompt_profile_quality_audit,
)
from v30.validation.brain_training_synthetic_closeout import (
    build_brain_training_synthetic_closeout,
    run_brain_training_synthetic_closeout,
)
from v30.validation.multi_user_terminal_locale_readiness import (
    build_multi_user_terminal_locale_readiness,
    run_multi_user_terminal_locale_readiness,
)
from v30.validation.session_owner_boundary_readiness import (
    build_session_owner_boundary_readiness,
    run_session_owner_boundary_readiness,
)
from v30.validation.ui_core_reading_product_acceptance import (
    UI_CORE_READING_PRODUCT_ACCEPTANCE_VERSION,
    build_ui_core_reading_product_acceptance,
    run_ui_core_reading_product_acceptance,
)
from v30.validation.locale_terminology_readiness import (
    build_locale_terminology_readiness,
    run_locale_terminology_readiness,
)
from v30.validation.terminal_contract_freeze import (
    build_terminal_contract_freeze,
    run_terminal_contract_freeze,
)
from v30.validation.productization_closeout import (
    build_productization_closeout,
    run_productization_closeout,
)
from v30.validation.real_bazi_product_reading_acceptance import (
    build_real_bazi_product_reading_acceptance,
    run_real_bazi_product_reading_acceptance,
)
from v30.validation.real_bazi_distribution_replay import (
    build_real_bazi_distribution_replay,
    run_real_bazi_distribution_replay,
)
from v30.validation.real_bazi_training_calibration_queue import (
    build_real_bazi_training_calibration_queue,
    run_real_bazi_training_calibration_queue,
)
from v30.validation.real_bazi_diagnosis_steady_state import (
    build_real_bazi_diagnosis_steady_state,
    run_real_bazi_diagnosis_steady_state,
)
from v30.validation.synthetic_canonical_bazi_calibration_review import (
    build_synthetic_canonical_bazi_calibration_review,
    run_synthetic_canonical_bazi_calibration_review,
)
from v30.validation.synthetic_canonical_pack_decision import (
    build_synthetic_canonical_pack_decision,
    run_synthetic_canonical_pack_decision,
)
from v30.validation.synthetic_canonical_steady_state import (
    build_synthetic_canonical_steady_state,
    run_synthetic_canonical_steady_state,
)
from v30.validation.synthetic_canonical_await_trigger import (
    build_synthetic_canonical_await_trigger,
    run_synthetic_canonical_await_trigger,
)
from v30.validation.latent_bazi_divergence import (
    LATENT_BAZI_DIVERGENCE_VERSION,
    LATENT_DIVERGENCE_CASES,
    run_latent_bazi_divergence_case,
    run_latent_bazi_divergence_synthetic_suite,
)
from v30.validation.latent_policy_observability import (
    LATENT_POLICY_OBSERVABILITY_VERSION,
    build_latent_policy_observability_readiness,
    run_latent_policy_observability_readiness,
)
from v30.validation.latent_attribute_admin_training_review import (
    LATENT_ATTRIBUTE_ADMIN_TRAINING_REVIEW_VERSION,
    build_latent_attribute_admin_training_review,
    run_latent_attribute_admin_training_review,
)
from v30.validation.latent_attribute_workflow_closeout import (
    LATENT_ATTRIBUTE_WORKFLOW_CLOSEOUT_VERSION,
    build_latent_attribute_workflow_closeout,
    run_latent_attribute_workflow_closeout,
)
from v30.validation.controlled_release_readiness import (
    build_controlled_release_readiness,
    run_controlled_release_readiness,
)
from v30.validation.explicit_release_gate_authorization import (
    build_explicit_release_gate_authorization,
    run_explicit_release_gate_authorization,
)
from v30.validation.stage_a_release_gate_execution import (
    build_stage_a_release_gate_execution,
    run_stage_a_release_gate_execution,
)
from v30.validation.stage_a_evidence_review import (
    build_stage_a_evidence_review,
    run_stage_a_evidence_review,
)
from v30.validation.core_mainline_selection_after_release_hold import (
    build_core_mainline_selection_after_release_hold,
    run_core_mainline_selection_after_release_hold,
)
from v30.validation.synthetic_archetype_rule_claim_calibration import (
    build_synthetic_archetype_rule_claim_calibration,
    run_synthetic_archetype_rule_claim_calibration,
)
from v30.validation.synthetic_archetype_tier_registration import (
    build_synthetic_archetype_tier_registration,
    run_synthetic_archetype_tier_registration,
)
from v30.validation.synthetic_archetype_training_signal_review import (
    build_synthetic_archetype_training_signal_review,
    run_synthetic_archetype_training_signal_review,
)
from v30.validation.synthetic_archetype_calibration_closeout import (
    build_synthetic_archetype_calibration_closeout,
    run_synthetic_archetype_calibration_closeout,
)
from v30.validation.core_calibration_steady_state_queue import (
    build_core_calibration_steady_state_queue,
    run_core_calibration_steady_state_queue,
)
from v30.validation.bazi_llm_context_prompt_readiness import (
    build_bazi_llm_context_prompt_readiness,
    run_bazi_llm_context_prompt_readiness,
)
from v30.validation.decision_centered_architecture import (
    build_decision_centered_architecture_validation,
    run_decision_centered_architecture_validation,
)
from v30.validation.bazi_llm_answer_generator_readiness import (
    build_bazi_llm_answer_generator_readiness,
    run_bazi_llm_answer_generator_readiness,
)
from v30.validation.bazi_llm_output_acceptance_readiness import (
    build_bazi_llm_output_acceptance_readiness,
    run_bazi_llm_output_acceptance_readiness,
)
from v30.validation.bazi_llm_training_synthetic_readiness import (
    build_bazi_llm_training_synthetic_readiness,
    run_bazi_llm_training_synthetic_readiness,
)
from v30.validation.bazi_llm_role_locale_production_smoke import (
    build_bazi_llm_role_locale_production_smoke,
    run_bazi_llm_role_locale_production_smoke,
)
from v30.validation.bazi_llm_closeout import (
    build_bazi_llm_closeout,
    run_bazi_llm_closeout,
)
from v30.validation.bazi_intelligence_requirements_coverage import (
    build_bazi_intelligence_requirements_coverage,
    run_bazi_intelligence_requirements_coverage,
)
from v30.validation.bazi_backend_api_journey_acceptance import (
    build_bazi_backend_api_journey_acceptance,
    run_bazi_backend_api_journey_acceptance,
)
from v30.validation.intelligent_question_interaction_audit import (
    build_intelligent_question_interaction_audit,
    run_intelligent_question_interaction_audit,
)
from v30.validation.question_model_signal_training_readiness import (
    build_question_model_signal_training_readiness,
    run_question_model_signal_training_readiness,
)
from v30.validation.intelligent_question_chain_readiness import (
    build_intelligent_question_chain_readiness,
    run_intelligent_question_chain_readiness,
)
from v30.validation.intelligent_question_closeout import (
    build_intelligent_question_closeout,
    run_intelligent_question_closeout,
)
from v30.validation.main_module_completion_review import (
    build_main_module_completion_review,
    run_main_module_completion_review,
)
from v30.validation.customer_surface_bazi_context_reconciliation import (
    build_customer_surface_bazi_context_reconciliation,
    run_customer_surface_bazi_context_reconciliation,
)
from v30.validation.m3_core_spine_snapshot import (
    build_m3_core_spine_snapshot,
    run_m3_core_spine_snapshot,
)
from v30.validation.m3_source_governed_calibration import (
    build_m3_source_governed_calibration,
)
from v30.validation.m3_training_candidate_review import (
    build_m3_training_candidate_review,
    run_m3_training_candidate_review,
)
from v30.validation.m3_source_extraction_backlog import (
    build_m3_source_extraction_backlog,
    run_m3_source_extraction_backlog,
)
from v30.validation.m3_source_backlog_review_surface import (
    build_m3_source_backlog_review_surface,
    run_m3_source_backlog_review_surface,
)
from v30.validation.m3_source_backlog_closeout import (
    build_m3_source_backlog_closeout,
    run_m3_source_backlog_closeout,
)
from v30.validation.m5_evidence_consumption_hardening import (
    build_m5_evidence_consumption_hardening,
    run_m5_evidence_consumption_hardening,
)
from v30.validation.m5_calibration_replay_review import (
    build_m5_calibration_replay_review,
    run_m5_calibration_replay_review,
)
from v30.validation.m5_calibration_replay_closeout import (
    build_m5_calibration_replay_closeout,
    run_m5_calibration_replay_closeout,
)
from v30.validation.m6_practical_reading_consumption_hardening import (
    build_m6_practical_reading_consumption_hardening,
    run_m6_practical_reading_consumption_hardening,
)
from v30.validation.m6_practical_reading_closeout import (
    build_m6_practical_reading_closeout,
    run_m6_practical_reading_closeout,
)
from v30.validation.m7_real_case_calibration_steady_state_review import (
    build_m7_real_case_calibration_steady_state_review,
    run_m7_real_case_calibration_steady_state_review,
)
from v30.validation.m7_real_case_calibration_closeout import (
    build_m7_real_case_calibration_closeout,
    run_m7_real_case_calibration_closeout,
)
from v30.validation.m8_projection_api_contract_closeout import (
    build_m8_projection_api_contract_closeout,
    run_m8_projection_api_contract_closeout,
)
from v30.validation.iq_intelligent_question_support_review import (
    build_iq_intelligent_question_support_review,
    run_iq_intelligent_question_support_review,
)
from v30.validation.llm_bazi_expression_support_review import (
    build_llm_bazi_expression_support_review,
    run_llm_bazi_expression_support_review,
)
from v30.validation.training_synthetic_support_review import (
    build_training_synthetic_support_review,
    run_training_synthetic_support_review,
)
from v30.validation.core_chain_steady_state_summary import (
    build_core_chain_steady_state_summary,
    run_core_chain_steady_state_summary,
)
from v30.validation.evidence_driven_calibration_queue import (
    build_evidence_driven_calibration_queue,
    run_evidence_driven_calibration_queue,
)
from v30.validation.await_new_calibration_evidence_status import (
    build_await_new_calibration_evidence_status,
    run_await_new_calibration_evidence_status,
)
from v30.validation.real_business_bazi_reading_acceptance import (
    build_real_business_bazi_reading_acceptance,
    run_real_business_bazi_reading_acceptance,
)
from v30.validation.real_business_bazi_reading_regression_pack import (
    build_real_business_bazi_reading_regression_pack,
    run_real_business_bazi_reading_regression_pack,
)
from v30.validation.real_business_answer_refresh_regression import (
    build_real_business_answer_refresh_regression,
    run_real_business_answer_refresh_regression,
)
from v30.validation.real_business_boundary_blocked_input_regression import (
    build_real_business_boundary_blocked_input_regression,
    run_real_business_boundary_blocked_input_regression,
)
from v30.validation.real_business_api_contract_freeze import (
    build_real_business_api_contract_freeze,
    run_real_business_api_contract_freeze,
)
from v30.validation.real_business_acceptance_closeout import (
    build_real_business_acceptance_closeout,
    run_real_business_acceptance_closeout,
)
from v30.validation.real_business_steady_state import (
    build_real_business_steady_state,
    run_real_business_steady_state,
)
from v30.validation.answer_quality_delta_review import (
    ANSWER_QUALITY_DELTA_REVIEW_VERSION,
    build_answer_quality_delta_review,
    run_answer_quality_delta_review,
)
from v30.validation.llm_prompt_context_delta_review import (
    LLM_PROMPT_CONTEXT_DELTA_REVIEW_VERSION,
    build_llm_prompt_context_delta_review,
    run_llm_prompt_context_delta_review,
)
from v30.validation.llm_answer_output_delta_review import (
    LLM_ANSWER_OUTPUT_DELTA_REVIEW_VERSION,
    build_llm_answer_output_delta_review,
    run_llm_answer_output_delta_review,
)
from v30.validation.runtime_answer_integration_delta_review import (
    RUNTIME_ANSWER_INTEGRATION_DELTA_REVIEW_VERSION,
    build_runtime_answer_integration_delta_review,
    run_runtime_answer_integration_delta_review,
)
from v30.validation.core_evidence_closeout import (
    CORE_EVIDENCE_CLOSEOUT_VERSION,
    build_core_evidence_closeout,
    run_core_evidence_closeout,
)
from v30.validation.synthetic_typical_bazi_answer_calibration import (
    SYNTHETIC_TYPICAL_BAZI_ANSWER_CALIBRATION_VERSION,
    build_synthetic_typical_bazi_answer_calibration,
    run_synthetic_typical_bazi_answer_calibration,
)
from v30.validation.synthetic_typical_answer_training_signal_review import (
    SYNTHETIC_TYPICAL_ANSWER_TRAINING_SIGNAL_REVIEW_VERSION,
    build_synthetic_typical_answer_training_signal_review,
    run_synthetic_typical_answer_training_signal_review,
)
from v30.validation.synthetic_typical_answer_calibration_closeout import (
    SYNTHETIC_TYPICAL_ANSWER_CALIBRATION_CLOSEOUT_VERSION,
    build_synthetic_typical_answer_calibration_closeout,
    run_synthetic_typical_answer_calibration_closeout,
)
from v30.validation.core_answer_calibration_steady_state_queue import (
    CORE_ANSWER_CALIBRATION_STEADY_STATE_QUEUE_VERSION,
    build_core_answer_calibration_steady_state_queue,
    run_core_answer_calibration_steady_state_queue,
)
from v30.validation.core_answer_calibration_wait_status import (
    CORE_ANSWER_CALIBRATION_WAIT_STATUS_VERSION,
    build_core_answer_calibration_wait_status,
    run_core_answer_calibration_wait_status,
)
from v30.validation.evaluation_training_spine import (
    EVALUATION_TRAINING_SPINE_RUNNER_VERSION,
    run_evaluation_training_spine,
)
from v30.validation.training_signals import SyntheticTrainingSignal, extract_training_signals

__all__ = [
    "SYNTHETIC_SMOKE_CASES",
    "SYNTHETIC_GRADIENT_CASES",
    "SYNTHETIC_CORE_CALCULATION_CASES",
    "SYNTHETIC_M1_M2_BAZI_CALCULATION_CASES",
    "SYNTHETIC_M4_TEN_GOD_REAL_CASE_REPLAY_CASES",
    "SYNTHETIC_PRACTICAL_MAINLINE_CASES",
    "SYNTHETIC_INTERACTION_LOOP_CASES",
    "SYNTHETIC_INTERACTION_BRAIN_STRUCTURED_CONSTRAINT_CASES",
    "SYNTHETIC_CENTRAL_BRAIN_CASES",
    "SYNTHETIC_BAZI_LLM_ACCEPTANCE_CASES",
    "SYNTHETIC_UI_CORE_READING_PRODUCT_CASES",
    "SYNTHETIC_TYPICAL_BAZI_ANSWER_CASES",
    "SYNTHETIC_CANONICAL_BAZI_CALIBRATION_CASES",
    "SYNTHETIC_TRAINING_PIPELINE_CASES",
    "SYNTHETIC_REAL_CASE_CALIBRATION_PACK_CASES",
    "SYNTHETIC_REAL_CASE_VALIDATION_CASES",
    "SYNTHETIC_SUITES",
    "SyntheticBaziCase",
    "SyntheticValidationResult",
    "SyntheticValidationSuiteResult",
    "run_synthetic_case",
    "run_synthetic_suite",
    "run_synthetic_tier",
    "Corpus518KValidationResult",
    "CorpusSourceCase",
    "run_518k_validation",
    "build_518k_readiness_matrix",
    "run_518k_readiness_matrix",
    "LLMLiveSmokeResult",
    "run_llm_live_smoke",
    "build_production_replay_metadata",
    "summarize_production_replay_metadata",
    "build_production_replay_intake_row",
    "build_production_replay_intake_batch",
    "summarize_production_replay_intake",
    "ReleaseGateCheck",
    "ReleaseGateResult",
    "run_release_gate",
    "build_release_artifact_review",
    "build_post_seal_status_review",
    "build_release_candidate_review",
    "build_release_candidate_gate_review",
    "build_release_boundary_finalization",
    "DEFAULT_FROZEN_CORE_CALIBRATION_TIERS",
    "build_frozen_core_calibration_review",
    "run_frozen_core_calibration_review",
    "DEFAULT_TARGETED_CALIBRATION_FAMILIES",
    "build_targeted_calibration_candidate_review",
    "run_targeted_calibration_candidate_review",
    "build_targeted_calibration_validation_gate",
    "run_targeted_calibration_validation_gate",
    "build_targeted_calibration_pointer_review",
    "run_targeted_calibration_pointer_review",
    "build_targeted_calibration_pointer_decision",
    "run_targeted_calibration_pointer_decision",
    "build_targeted_calibration_closeout",
    "run_targeted_calibration_closeout",
    "build_mainline_selection",
    "run_mainline_selection",
    "build_core_calibration_observation_summary",
    "run_core_calibration_observation_summary",
    "build_core_calibration_drift_watch",
    "run_core_calibration_drift_watch",
    "build_focused_core_calibration_evidence_queue",
    "run_focused_core_calibration_evidence_queue",
    "build_core_calibration_queue_review",
    "run_core_calibration_queue_review",
    "build_core_calibration_watch_closeout",
    "run_core_calibration_watch_closeout",
    "build_central_brain_acceptance",
    "run_central_brain_acceptance",
    "build_central_brain_session_replay",
    "run_central_brain_session_replay",
    "build_central_brain_failure_routing",
    "run_central_brain_failure_routing",
    "DIALOGUE_TRAINING_CALIBRATION_VALIDATION_VERSION",
    "build_dialogue_training_calibration_validation",
    "run_dialogue_training_calibration_validation",
    "build_training_system_closeout",
    "run_training_system_closeout",
    "build_training_candidate_quarantine",
    "run_training_candidate_quarantine",
    "build_synthetic_coverage_manifest",
    "run_synthetic_coverage_manifest",
    "STAGE_OPTION_INTELLIGENCE_REPLAY_VERSION",
    "run_stage_option_intelligence_replay",
    "TEXT_OPTION_SYNTHETIC_VALIDATION_VERSION",
    "run_text_option_synthetic_validation",
    "LLM_PROMPT_PROFILE_QUALITY_AUDIT_VERSION",
    "run_llm_prompt_profile_quality_audit",
    "build_brain_training_synthetic_closeout",
    "run_brain_training_synthetic_closeout",
    "build_multi_user_terminal_locale_readiness",
    "run_multi_user_terminal_locale_readiness",
    "build_session_owner_boundary_readiness",
    "run_session_owner_boundary_readiness",
    "build_locale_terminology_readiness",
    "run_locale_terminology_readiness",
    "build_terminal_contract_freeze",
    "run_terminal_contract_freeze",
    "build_productization_closeout",
    "run_productization_closeout",
    "build_real_bazi_product_reading_acceptance",
    "run_real_bazi_product_reading_acceptance",
    "build_real_bazi_distribution_replay",
    "run_real_bazi_distribution_replay",
    "build_real_bazi_training_calibration_queue",
    "run_real_bazi_training_calibration_queue",
    "build_real_bazi_diagnosis_steady_state",
    "run_real_bazi_diagnosis_steady_state",
    "build_synthetic_canonical_bazi_calibration_review",
    "run_synthetic_canonical_bazi_calibration_review",
    "build_synthetic_canonical_pack_decision",
    "run_synthetic_canonical_pack_decision",
    "build_synthetic_canonical_steady_state",
    "run_synthetic_canonical_steady_state",
    "build_synthetic_canonical_await_trigger",
    "run_synthetic_canonical_await_trigger",
    "LATENT_BAZI_DIVERGENCE_VERSION",
    "LATENT_DIVERGENCE_CASES",
    "run_latent_bazi_divergence_case",
    "run_latent_bazi_divergence_synthetic_suite",
    "build_controlled_release_readiness",
    "run_controlled_release_readiness",
    "build_synthetic_archetype_rule_claim_calibration",
    "run_synthetic_archetype_rule_claim_calibration",
    "build_synthetic_archetype_tier_registration",
    "run_synthetic_archetype_tier_registration",
    "build_synthetic_archetype_training_signal_review",
    "run_synthetic_archetype_training_signal_review",
    "build_synthetic_archetype_calibration_closeout",
    "run_synthetic_archetype_calibration_closeout",
    "build_core_calibration_steady_state_queue",
    "run_core_calibration_steady_state_queue",
    "build_bazi_llm_context_prompt_readiness",
    "run_bazi_llm_context_prompt_readiness",
    "build_decision_centered_architecture_validation",
    "run_decision_centered_architecture_validation",
    "build_bazi_llm_answer_generator_readiness",
    "run_bazi_llm_answer_generator_readiness",
    "build_bazi_llm_output_acceptance_readiness",
    "run_bazi_llm_output_acceptance_readiness",
    "build_bazi_llm_training_synthetic_readiness",
    "run_bazi_llm_training_synthetic_readiness",
    "build_bazi_llm_role_locale_production_smoke",
    "run_bazi_llm_role_locale_production_smoke",
    "build_bazi_llm_closeout",
    "run_bazi_llm_closeout",
    "build_bazi_intelligence_requirements_coverage",
    "run_bazi_intelligence_requirements_coverage",
    "build_bazi_backend_api_journey_acceptance",
    "run_bazi_backend_api_journey_acceptance",
    "build_intelligent_question_interaction_audit",
    "run_intelligent_question_interaction_audit",
    "build_question_model_signal_training_readiness",
    "run_question_model_signal_training_readiness",
    "build_intelligent_question_chain_readiness",
    "run_intelligent_question_chain_readiness",
    "build_intelligent_question_closeout",
    "run_intelligent_question_closeout",
    "build_main_module_completion_review",
    "run_main_module_completion_review",
    "build_customer_surface_bazi_context_reconciliation",
    "run_customer_surface_bazi_context_reconciliation",
    "build_m3_core_spine_snapshot",
    "run_m3_core_spine_snapshot",
    "build_m3_source_governed_calibration",
    "build_m3_training_candidate_review",
    "run_m3_training_candidate_review",
    "build_m3_source_extraction_backlog",
    "run_m3_source_extraction_backlog",
    "build_m3_source_backlog_review_surface",
    "run_m3_source_backlog_review_surface",
    "build_m3_source_backlog_closeout",
    "run_m3_source_backlog_closeout",
    "build_m5_evidence_consumption_hardening",
    "run_m5_evidence_consumption_hardening",
    "build_m5_calibration_replay_review",
    "run_m5_calibration_replay_review",
    "build_m5_calibration_replay_closeout",
    "run_m5_calibration_replay_closeout",
    "build_m6_practical_reading_consumption_hardening",
    "run_m6_practical_reading_consumption_hardening",
    "build_m6_practical_reading_closeout",
    "run_m6_practical_reading_closeout",
    "build_m7_real_case_calibration_steady_state_review",
    "run_m7_real_case_calibration_steady_state_review",
    "build_m7_real_case_calibration_closeout",
    "run_m7_real_case_calibration_closeout",
    "build_m8_projection_api_contract_closeout",
    "run_m8_projection_api_contract_closeout",
    "build_iq_intelligent_question_support_review",
    "run_iq_intelligent_question_support_review",
    "build_llm_bazi_expression_support_review",
    "run_llm_bazi_expression_support_review",
    "build_training_synthetic_support_review",
    "run_training_synthetic_support_review",
    "build_core_chain_steady_state_summary",
    "run_core_chain_steady_state_summary",
    "build_evidence_driven_calibration_queue",
    "run_evidence_driven_calibration_queue",
    "build_await_new_calibration_evidence_status",
    "run_await_new_calibration_evidence_status",
    "build_real_business_bazi_reading_acceptance",
    "run_real_business_bazi_reading_acceptance",
    "build_real_business_bazi_reading_regression_pack",
    "run_real_business_bazi_reading_regression_pack",
    "build_real_business_answer_refresh_regression",
    "run_real_business_answer_refresh_regression",
    "build_real_business_boundary_blocked_input_regression",
    "run_real_business_boundary_blocked_input_regression",
    "build_real_business_api_contract_freeze",
    "run_real_business_api_contract_freeze",
    "build_real_business_acceptance_closeout",
    "run_real_business_acceptance_closeout",
    "build_real_business_steady_state",
    "run_real_business_steady_state",
    "ANSWER_QUALITY_DELTA_REVIEW_VERSION",
    "build_answer_quality_delta_review",
    "run_answer_quality_delta_review",
    "LLM_PROMPT_CONTEXT_DELTA_REVIEW_VERSION",
    "build_llm_prompt_context_delta_review",
    "run_llm_prompt_context_delta_review",
    "LLM_ANSWER_OUTPUT_DELTA_REVIEW_VERSION",
    "build_llm_answer_output_delta_review",
    "run_llm_answer_output_delta_review",
    "RUNTIME_ANSWER_INTEGRATION_DELTA_REVIEW_VERSION",
    "build_runtime_answer_integration_delta_review",
    "run_runtime_answer_integration_delta_review",
    "CORE_EVIDENCE_CLOSEOUT_VERSION",
    "build_core_evidence_closeout",
    "run_core_evidence_closeout",
    "SYNTHETIC_TYPICAL_BAZI_ANSWER_CALIBRATION_VERSION",
    "build_synthetic_typical_bazi_answer_calibration",
    "run_synthetic_typical_bazi_answer_calibration",
    "SYNTHETIC_TYPICAL_ANSWER_TRAINING_SIGNAL_REVIEW_VERSION",
    "build_synthetic_typical_answer_training_signal_review",
    "run_synthetic_typical_answer_training_signal_review",
    "SYNTHETIC_TYPICAL_ANSWER_CALIBRATION_CLOSEOUT_VERSION",
    "build_synthetic_typical_answer_calibration_closeout",
    "run_synthetic_typical_answer_calibration_closeout",
    "CORE_ANSWER_CALIBRATION_STEADY_STATE_QUEUE_VERSION",
    "build_core_answer_calibration_steady_state_queue",
    "run_core_answer_calibration_steady_state_queue",
    "CORE_ANSWER_CALIBRATION_WAIT_STATUS_VERSION",
    "build_core_answer_calibration_wait_status",
    "run_core_answer_calibration_wait_status",
    "EVALUATION_TRAINING_SPINE_RUNNER_VERSION",
    "run_evaluation_training_spine",
    "LATENT_POLICY_OBSERVABILITY_VERSION",
    "build_latent_policy_observability_readiness",
    "run_latent_policy_observability_readiness",
    "LATENT_ATTRIBUTE_ADMIN_TRAINING_REVIEW_VERSION",
    "build_latent_attribute_admin_training_review",
    "run_latent_attribute_admin_training_review",
    "LATENT_ATTRIBUTE_WORKFLOW_CLOSEOUT_VERSION",
    "build_latent_attribute_workflow_closeout",
    "run_latent_attribute_workflow_closeout",
    "SyntheticTrainingSignal",
    "extract_training_signals",
]
