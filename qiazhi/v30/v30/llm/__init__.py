"""V30 bounded LLM contracts."""
"""LLM role context contracts for V30."""

from v30.llm.acceptance import (
    BAZI_LLM_OUTPUT_ACCEPTANCE_VERSION,
    bazi_llm_output_text,
    validate_bazi_llm_output_payload,
)
from v30.llm.context import LLMRolePromptContext, build_llm_role_prompt_context
from v30.llm.bazi_context import (
    BAZI_LLM_CONTEXT_PACK_VERSION,
    build_bazi_llm_context_pack,
    role_llm_profile,
    supported_bazi_llm_roles,
    supported_bazi_llm_tasks,
    task_context_spec,
)
from v30.llm.drift import LLMDriftCheckResult, check_llm_answer_drift
from v30.llm.client import (
    call_bazi_llm_answer_draft,
    call_llm_answer_draft,
    compose_bazi_llm_answer_draft,
    compose_llm_answer_draft,
)
from v30.llm.output_contracts import (
    LLM_OUTPUT_CONTRACT_VERSION,
    LLMOutputContract,
    build_answer_draft_contract,
    build_failure_cluster_summary_contract,
    build_question_explanation_contract,
    build_synthetic_case_draft_contract,
    summarize_llm_output_contracts,
)
from v30.llm.provider import (
    V30LLMProviderConfig,
    llm_provider_readiness_report,
    load_v30_llm_provider_config_from_env,
)
from v30.llm.prompt_registry import (
    BAZI_LLM_PROMPT_REGISTRY_VERSION,
    build_bazi_llm_prompt_request,
    prompt_contract_for_task,
    supported_prompt_contracts,
)

__all__ = [
    "LLM_OUTPUT_CONTRACT_VERSION",
    "LLMDriftCheckResult",
    "LLMOutputContract",
    "LLMRolePromptContext",
    "BAZI_LLM_CONTEXT_PACK_VERSION",
    "BAZI_LLM_OUTPUT_ACCEPTANCE_VERSION",
    "BAZI_LLM_PROMPT_REGISTRY_VERSION",
    "V30LLMProviderConfig",
    "build_answer_draft_contract",
    "build_bazi_llm_context_pack",
    "build_bazi_llm_prompt_request",
    "build_failure_cluster_summary_contract",
    "build_llm_role_prompt_context",
    "build_question_explanation_contract",
    "build_synthetic_case_draft_contract",
    "check_llm_answer_drift",
    "call_llm_answer_draft",
    "call_bazi_llm_answer_draft",
    "compose_bazi_llm_answer_draft",
    "compose_llm_answer_draft",
    "llm_provider_readiness_report",
    "load_v30_llm_provider_config_from_env",
    "prompt_contract_for_task",
    "role_llm_profile",
    "supported_bazi_llm_roles",
    "supported_bazi_llm_tasks",
    "supported_prompt_contracts",
    "summarize_llm_output_contracts",
    "task_context_spec",
    "bazi_llm_output_text",
    "validate_bazi_llm_output_payload",
]
