from __future__ import annotations

from v30.contracts import CoreRuntimeResult
from v30.llm.bazi_context import (
    build_bazi_llm_context_pack,
    role_llm_profile,
    supported_bazi_llm_roles,
    supported_bazi_llm_tasks,
    task_context_spec,
)
from v30.llm.thinking_context import build_thinking_stage_context_pack


BAZI_LLM_PROMPT_REGISTRY_VERSION = "v30.bazi_llm_prompt_contract_registry.v1"

OUTPUT_SCHEMAS: dict[str, dict[str, object]] = {
    "customer_initial_reading": {
        "schema_id": "BaziCustomerAnswerDraft",
        "required_fields": ["answer_text", "evidence_ids", "boundaries", "next_question_hint"],
    },
    "domain_followup": {
        "schema_id": "BaziDomainFollowupAnswer",
        "required_fields": ["domain", "answer_text", "used_user_signals", "boundaries"],
    },
    "useful_god_candidate_explanation": {
        "schema_id": "BaziCandidatePathExplanation",
        "required_fields": ["candidate_paths", "supporting_evidence", "unresolved_boundaries"],
    },
    "hidden_factor_dialogue": {
        "schema_id": "BaziHiddenFactorDialogueTurn",
        "required_fields": ["dialogue_text", "probe_target", "confirmed_feedback_only", "boundaries"],
    },
    "practitioner_analysis": {
        "schema_id": "BaziPractitionerAnalysisDraft",
        "required_fields": ["analysis_text", "module_evidence", "candidate_boundaries", "diagnostics_used"],
    },
    "locale_rewrite": {
        "schema_id": "BaziLocaleRewrite",
        "required_fields": ["rewritten_text", "locale", "unchanged_fact_ids", "boundaries"],
    },
    "thinking_step_summary": {
        "schema_id": "BaziThinkingStagePointSummary",
        "required_fields": ["text", "public_derivation", "candidate_points", "derived_conclusion", "derived_advice"],
        "compatibility_fields": ["public_thinking_lines", "used_evidence", "uncertainty"],
    },
}


def prompt_contract_for_task(task_type: str, *, role_key: str = "user") -> dict[str, object]:
    spec = task_context_spec(task_type)
    role_profile = role_llm_profile(role_key)
    if task_type not in set(str(row) for row in role_profile.get("allowed_tasks", [])):
        raise ValueError(f"bazi llm task_type {task_type} is not allowed for role_key: {role_key}")
    return {
        "version": BAZI_LLM_PROMPT_REGISTRY_VERSION,
        "prompt_contract_id": f"v30.bazi_llm_prompt.{task_type}.{role_key}.v1",
        "task_type": task_type,
        "role_key": role_key,
        "required_context_pack": spec["context_pack"],
        "allowed_modules": list(spec["allowed_modules"]),
        "forbidden_modules": _unique_strs([*list(spec["forbidden_modules"]), *list(role_profile["forbidden_modules"])]),
        "role_contract": {
            "role_contract_id": role_profile["role_contract_id"],
            "audience": role_profile["audience"],
            "expression_density": role_profile["expression_density"],
            "terminology_depth": role_profile["terminology_depth"],
            "diagnostics_visible": role_profile["diagnostics_visible"],
            "allowed_tasks": role_profile["allowed_tasks"],
            "forbidden_sections": role_profile["forbidden_sections"],
        },
        "system_rules": [
            "Use only fields present in the supplied context pack.",
            "When decision_verdicts is present, treat it as the final verdict boundary.",
            "Do not override Decision Engine assertion_level, allowed_assertions, or forbidden_assertions.",
            "Keep Bazi chart facts, ranked decisions, hidden-factor state, and interaction state read-only.",
            "Do not add unverified event years, birth-time assumptions, or user history.",
            "If required evidence is absent, state the boundary instead of filling the gap.",
            "Respect role visibility, terminology depth, and expression density from role_contract.",
            "LLM output is expression or explanation only; it is never a policy or chart mutation.",
        ],
        "output_schema": OUTPUT_SCHEMAS[task_type],
        "verifier": {
            "verifier_id": "v30.bazi_llm_context_budget_and_module_gate.v1",
            "checks": [
                "context_pack_version",
                "task_context_pack_match",
                "allowed_module_gate",
                "forbidden_module_absence",
                "context_budget",
                "role_visibility_gate",
                "decision_verdict_boundary",
                "allowed_forbidden_assertion_gate",
                "chart_fact_mutation_block",
                "output_schema_presence",
            ],
        },
        "fallback": {
            "fallback_id": "rule_bound_answer_or_no_llm_output",
            "on_missing_context": "return_rule_bound_answer",
            "on_verifier_failure": "block_llm_output_and_keep_verified_answer",
            "on_provider_failure": "keep_rule_bound_answer",
        },
        "boundary": "prompt_contract_selects_task_specific_context_without_prompt_pileup",
    }


def build_bazi_llm_prompt_request(
    runtime: CoreRuntimeResult,
    *,
    task_type: str,
    domain: str = "",
    role_key: str = "user",
    locale: str = "zh",
    client: str = "web",
) -> dict[str, object]:
    contract = prompt_contract_for_task(task_type, role_key=role_key)
    context_pack = build_bazi_llm_context_pack(
        runtime,
        task_type=task_type,
        domain=domain,
        role_key=role_key,
        locale=locale,
        client=client,
    )
    if context_pack["context_pack"] != contract["required_context_pack"]:
        raise ValueError(f"context pack mismatch for task_type: {task_type}")
    return {
        "version": "v30.bazi_llm_prompt_request.v1",
        "request_id": f"{runtime.reading_id}:llm-prompt:{task_type}:{role_key}:{locale}:{client}",
        "reading_id": runtime.reading_id,
        "task_type": task_type,
        "prompt_contract": contract,
        "context_pack": context_pack,
        "llm_execution_allowed": True,
        "chart_fact_mutation_allowed": False,
        "raw_runtime_payload_included": False,
        "boundary": "bazi_llm_prompt_request_is_task_bound_and_module_gated",
    }


def prompt_contract_for_thinking_step(*, role_key: str = "user") -> dict[str, object]:
    role_profile = role_llm_profile(role_key) if role_key in set(supported_bazi_llm_roles()) else role_llm_profile("user")
    diagnostics_visible = role_profile.get("diagnostics_visible") is True
    return {
        "version": BAZI_LLM_PROMPT_REGISTRY_VERSION,
        "prompt_contract_id": f"v30.bazi_llm_prompt.thinking_step_summary.{role_key}.v1",
        "task_type": "thinking_step_summary",
        "role_key": role_key,
        "required_context_pack": "ThinkingStageContext",
        "allowed_modules": [
            "M1_M2",
            "M3",
            "M4",
            "M5",
            "M6",
            "M8",
            "central_brain",
            "xuanming_reasoning",
            "interaction_brain",
            "hidden_factor_state",
        ],
        "forbidden_modules": _unique_strs([
            "raw_runtime_payload",
            "chart_fact_generation",
            "policy_pointer_write",
            "training",
            "policy_weights",
            *list(role_profile.get("forbidden_modules", [])),
        ]),
        "role_contract": {
            "role_contract_id": role_profile["role_contract_id"],
            "audience": role_profile["audience"],
            "expression_density": role_profile["expression_density"],
            "terminology_depth": role_profile["terminology_depth"],
            "diagnostics_visible": diagnostics_visible,
            "allowed_tasks": ["thinking_step_summary"],
            "forbidden_sections": role_profile["forbidden_sections"],
        },
        "system_rules": [
            "Use only the supplied ThinkingStageContext.",
            "Prefer stage.analysis_result for the stage judgment.",
            "Use xuanming_reasoning and module_context only as support.",
            "Generate stage-local candidate_points: verdict, evidence/mechanism, advice, and optional risk.",
            "Evidence-bound uncertainty is allowed: when multiple branches remain live, express them as ranked candidate_points with confidence/probability, evidence, counter-evidence, and resolution conditions.",
            "When a candidate point contains clear alternatives, lists, numbers, or a practitioner-selectable tradeoff, include option_hints; the central brain decides final OptionSets.",
            "Every candidate point must include customer-facing text, short_label, Bazi terms or evidence refs, and must stay inside the current stage.",
            "Do not use fixed labels such as 结论：, 建议：, 依据：, 判断：, or 要点：.",
            "State the primary stage judgment first, then preserve meaningful alternatives instead of collapsing all branches into a fake-certain verdict.",
            "Do not create or alter pillars, luck cycles, flow years, user history, hidden-factor facts, or ranked decisions.",
            "Do not expose internal ids, JSON keys, diagnostics, source ids, or runtime traces.",
        ],
        "output_schema": OUTPUT_SCHEMAS["thinking_step_summary"],
        "verifier": {
            "verifier_id": "v30.thinking_step_summary_acceptance.v1",
            "checks": [
                "thinking_context_pack_version",
                "module_gate_by_step_id",
                "role_visibility_gate",
                "no_internal_identifier",
                "no_chart_fact_mutation",
                "max_output_chars",
            ],
        },
        "fallback": {
            "fallback_id": "central_brain_rule_summary",
            "on_missing_context": "keep_deterministic_stage_summary",
            "on_verifier_failure": "block_llm_output_and_keep_stage_summary",
            "on_provider_failure": "keep_deterministic_stage_summary",
        },
        "boundary": "thinking_prompt_contract_uses_stage_context_without_prompt_pileup",
    }


def build_thinking_step_prompt_request(
    runtime: CoreRuntimeResult,
    step: dict[str, object],
    *,
    role_key: str = "user",
    locale: str = "zh",
    client: str = "web",
) -> dict[str, object]:
    contract = prompt_contract_for_thinking_step(role_key=role_key)
    context_pack = build_thinking_stage_context_pack(
        runtime,
        step,
        role_key=role_key,
        locale=locale,
        client=client,
    )
    if context_pack["context_pack"] != contract["required_context_pack"]:
        raise ValueError("thinking context pack mismatch")
    return {
        "version": "v30.thinking_step_prompt_request.v1",
        "request_id": (
            f"{runtime.reading_id}:llm-prompt:thinking_step_summary:"
            f"{step.get('step_id') or 'unknown'}:{role_key}:{locale}:{client}"
        ),
        "reading_id": runtime.reading_id,
        "task_type": "thinking_step_summary",
        "step_id": str(step.get("step_id") or ""),
        "prompt_contract": contract,
        "context_pack": context_pack,
        "llm_execution_allowed": True,
        "chart_fact_mutation_allowed": False,
        "raw_runtime_payload_included": False,
        "boundary": "thinking_step_prompt_request_is_task_bound_and_module_gated",
    }


def supported_prompt_contracts(*, role_key: str = "user") -> list[dict[str, object]]:
    role_profile = role_llm_profile(role_key)
    return [
        prompt_contract_for_task(task_type, role_key=role_key)
        for task_type in supported_bazi_llm_tasks()
        if task_type in set(str(row) for row in role_profile.get("allowed_tasks", []))
    ]


def _unique_strs(values: list[object]) -> list[str]:
    rows: list[str] = []
    for value in values:
        text = str(value)
        if text and text not in rows:
            rows.append(text)
    return rows
