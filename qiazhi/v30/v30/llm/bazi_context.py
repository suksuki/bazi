from __future__ import annotations

from typing import Any

from v30.contracts import CoreRuntimeResult


BAZI_LLM_CONTEXT_PACK_VERSION = "v30.bazi_llm_context_pack.v1"

MAX_CONTEXT_SECTIONS = 7
MAX_EVIDENCE_ITEMS = 8
MAX_RANKED_CANDIDATES_PER_DOMAIN = 3
MAX_USER_HISTORY_ITEMS = 3

FORBIDDEN_MODULES_ALL = [
    "chart_fact_generation",
    "policy_pointer_write",
    "raw_runtime_payload",
]

ROLE_LLM_PROFILES: dict[str, dict[str, object]] = {
    "guest": {
        "role_contract_id": "v30.bazi_llm_role.guest.v1",
        "audience": "guest_preview",
        "expression_density": "brief",
        "terminology_depth": "low",
        "diagnostics_visible": False,
        "allowed_tasks": ["customer_initial_reading", "locale_rewrite"],
        "forbidden_sections": ["diagnostics_summary", "structure_dynamics", "evidence"],
        "forbidden_modules": ["admin_diagnostics", "diagnostics_summary", "training", "policy_weights"],
        "max_context_sections": 3,
    },
    "user": {
        "role_contract_id": "v30.bazi_llm_role.user.v1",
        "audience": "customer_reading",
        "expression_density": "standard",
        "terminology_depth": "medium",
        "diagnostics_visible": False,
        "allowed_tasks": [
            "customer_initial_reading",
            "domain_followup",
            "useful_god_candidate_explanation",
            "hidden_factor_dialogue",
            "locale_rewrite",
        ],
        "forbidden_sections": ["diagnostics_summary"],
        "forbidden_modules": ["admin_diagnostics", "diagnostics_summary", "training", "policy_weights"],
        "max_context_sections": 7,
    },
    "practitioner": {
        "role_contract_id": "v30.bazi_llm_role.practitioner.v1",
        "audience": "practitioner_review",
        "expression_density": "dense",
        "terminology_depth": "high",
        "diagnostics_visible": True,
        "allowed_tasks": [
            "customer_initial_reading",
            "domain_followup",
            "useful_god_candidate_explanation",
            "hidden_factor_dialogue",
            "practitioner_analysis",
            "locale_rewrite",
        ],
        "forbidden_sections": [],
        "forbidden_modules": ["training", "policy_pointer_write"],
        "max_context_sections": 7,
    },
    "analyst": {
        "role_contract_id": "v30.bazi_llm_role.analyst.v1",
        "audience": "diagnostic_analysis",
        "expression_density": "diagnostic",
        "terminology_depth": "high",
        "diagnostics_visible": True,
        "allowed_tasks": ["practitioner_analysis", "locale_rewrite"],
        "forbidden_sections": [],
        "forbidden_modules": ["policy_pointer_write"],
        "max_context_sections": 5,
    },
    "admin": {
        "role_contract_id": "v30.bazi_llm_role.admin.v1",
        "audience": "operator_diagnostics",
        "expression_density": "diagnostic",
        "terminology_depth": "high",
        "diagnostics_visible": True,
        "allowed_tasks": ["practitioner_analysis", "locale_rewrite"],
        "forbidden_sections": [],
        "forbidden_modules": ["policy_pointer_write"],
        "max_context_sections": 5,
    },
    "lab": {
        "role_contract_id": "v30.bazi_llm_role.lab.v1",
        "audience": "validation_and_training_lab",
        "expression_density": "diagnostic",
        "terminology_depth": "high",
        "diagnostics_visible": True,
        "allowed_tasks": ["practitioner_analysis", "locale_rewrite"],
        "forbidden_sections": [],
        "forbidden_modules": ["policy_pointer_write"],
        "max_context_sections": 5,
    },
}

TASK_CONTEXT_SPECS: dict[str, dict[str, object]] = {
    "customer_initial_reading": {
        "context_pack": "BaziCoreContext",
        "allowed_modules": ["M1_M2", "DecisionEngine", "M4", "M5", "M6", "M8"],
        "required_sections": ["chart_facts", "decision_verdicts", "model_signals", "ranked_decisions", "practical_reading", "answer_surface"],
        "forbidden_modules": ["training", "policy_weights", "admin_diagnostics"],
        "allowed_answer_scope": "express Decision Engine verdicts, verified Bazi reading, ranked domain tendencies, and next question boundaries",
        "max_prompt_tokens_estimate": 1400,
    },
    "domain_followup": {
        "context_pack": "BaziDomainContext",
        "allowed_modules": ["DecisionEngine", "M3", "M4", "M5", "M6", "interaction_state", "known_user_signals"],
        "required_sections": [
            "decision_verdicts",
            "structure_dynamics",
            "model_signals",
            "ranked_decisions",
            "practical_reading",
            "interaction_state",
            "known_user_signals",
        ],
        "forbidden_modules": ["training", "policy_weights", "admin_diagnostics"],
        "allowed_answer_scope": (
            "answer within one selected domain using M3 structure evidence, M4 model signals, "
            "M5 ranked decisions, M6 practical reading, and known user feedback only"
        ),
        "max_prompt_tokens_estimate": 1400,
    },
    "useful_god_candidate_explanation": {
        "context_pack": "BaziCandidatePathContext",
        "allowed_modules": ["DecisionEngine", "M3", "M4", "M5"],
        "required_sections": ["decision_verdicts", "structure_dynamics", "model_signals", "ranked_decisions", "evidence"],
        "forbidden_modules": ["training", "policy_weights", "admin_diagnostics"],
        "allowed_answer_scope": "explain useful-god candidate path and unresolved boundaries without fixing a final verdict",
        "max_prompt_tokens_estimate": 1200,
    },
    "hidden_factor_dialogue": {
        "context_pack": "BaziHiddenFactorDialogueContext",
        "allowed_modules": ["hidden_factor_state", "interaction_state"],
        "required_sections": ["hidden_factor_state", "interaction_state", "known_user_signals"],
        "forbidden_modules": ["training", "policy_weights", "admin_diagnostics", "ranked_decision_mutation"],
        "allowed_answer_scope": "ask or explain hidden-factor follow-up using confirmed feedback only as dialogue signal",
        "max_prompt_tokens_estimate": 900,
    },
    "practitioner_analysis": {
        "context_pack": "BaziPractitionerContext",
        "allowed_modules": ["M1_M2", "DecisionEngine", "M3", "M4", "M5", "M6", "diagnostics_summary"],
        "required_sections": ["chart_facts", "decision_verdicts", "structure_dynamics", "model_signals", "ranked_decisions", "practical_reading"],
        "forbidden_modules": ["training", "policy_pointer_write"],
        "allowed_answer_scope": "provide denser evidence, candidate paths, and diagnostic boundaries for practitioner review",
        "max_prompt_tokens_estimate": 1800,
    },
    "locale_rewrite": {
        "context_pack": "BaziLocaleRewriteContext",
        "allowed_modules": ["verified_answer_draft", "locale_terminology"],
        "required_sections": ["answer_surface", "locale_terminology"],
        "forbidden_modules": ["training", "policy_weights", "admin_diagnostics", "chart_fact_generation"],
        "allowed_answer_scope": "rewrite a verified answer for locale and role tone without changing facts",
        "max_prompt_tokens_estimate": 700,
    },
}


def build_bazi_llm_context_pack(
    runtime: CoreRuntimeResult,
    *,
    task_type: str,
    domain: str = "",
    role_key: str = "user",
    locale: str = "zh",
    client: str = "web",
) -> dict[str, object]:
    spec = _task_spec(task_type)
    role_profile = role_llm_profile(role_key)
    if task_type not in set(str(row) for row in _list(role_profile.get("allowed_tasks"))):
        raise ValueError(f"bazi llm task_type {task_type} is not allowed for role_key: {role_key}")
    sections = _build_sections(runtime, task_type=task_type, domain=domain, locale=locale)
    selected_sections = _select_required_sections(sections, spec, role_profile)
    evidence_ids = _evidence_ids(selected_sections)
    max_context_sections = int(role_profile.get("max_context_sections") or MAX_CONTEXT_SECTIONS)
    return {
        "version": BAZI_LLM_CONTEXT_PACK_VERSION,
        "context_pack_id": f"{runtime.reading_id}:llm-context:{task_type}:{role_key}:{locale}:{client}",
        "reading_id": runtime.reading_id,
        "task_type": task_type,
        "domain": domain,
        "role_key": role_key,
        "locale": locale,
        "client": client,
        "context_pack": spec["context_pack"],
        "included_modules": list(spec["allowed_modules"]),
        "excluded_modules": _unique_strs([
            *FORBIDDEN_MODULES_ALL,
            *list(spec["forbidden_modules"]),
            *_list(role_profile.get("forbidden_modules")),
        ]),
        "role_contract": {
            "role_contract_id": role_profile["role_contract_id"],
            "audience": role_profile["audience"],
            "expression_density": role_profile["expression_density"],
            "terminology_depth": role_profile["terminology_depth"],
            "diagnostics_visible": role_profile["diagnostics_visible"],
            "allowed_tasks": role_profile["allowed_tasks"],
            "forbidden_sections": role_profile["forbidden_sections"],
            "boundary": "llm_role_contract_controls_visibility_and_expression_not_bazi_facts",
        },
        "why_included": _why_included(task_type),
        "budget": {
            "max_context_sections": max_context_sections,
            "max_evidence_items": MAX_EVIDENCE_ITEMS,
            "max_ranked_candidates_per_domain": MAX_RANKED_CANDIDATES_PER_DOMAIN,
            "max_user_history_items": MAX_USER_HISTORY_ITEMS,
            "max_prompt_tokens_estimate": spec["max_prompt_tokens_estimate"],
            "observed_context_sections": len(selected_sections),
            "observed_evidence_items": len(evidence_ids),
        },
        "sections": selected_sections,
        "evidence_ids": evidence_ids,
        "fact_boundary": {
            "chart_fact_mutation_allowed": False,
            "training_signal_mutation_allowed": False,
            "policy_pointer_write_allowed": False,
            "raw_runtime_payload_allowed": False,
            "llm_can_override_decision_verdict": False,
            "llm_must_stay_within_allowed_assertions": True,
            "boundary": "llm_context_pack_reads_module_outputs_and_decision_verdicts_without_fact_mutation",
        },
        "uncertainty_policy": {
            "version": "v30.evidence_bound_uncertainty_policy.v1",
            "allow_candidate_branches": True,
            "allowed_branch_language": ["可能", "候选", "分支", "概率", "置信", "取向", "待复核"],
            "required_branch_binding": ["bazi_evidence", "confidence_or_probability", "counter_evidence_or_resolution_condition"],
            "reject_empty_hedges": ["不好说", "仅供参考", "后续再看"],
            "practitioner_option_target": "OptionSet",
            "boundary": "uncertainty_language_is_allowed_only_when_evidence_bound_and_trainable",
        },
        "forbidden_claims": [
            "create_or_change_four_pillars",
            "invent_birth_time_or_calendar_conversion",
            "invent_event_year_or_user_history",
            "turn_hidden_factor_hypothesis_into_confirmed_fact",
            "make_fixed_useful_god_verdict_without_ranked_decision_support",
            "override_decision_engine_verdict_or_assertion_level",
            "ignore_forbidden_assertions_from_decision_engine",
            "write_training_or_policy_pointer_changes",
        ],
        "allowed_answer_scope": spec["allowed_answer_scope"],
    }


def task_context_spec(task_type: str) -> dict[str, object]:
    return dict(_task_spec(task_type))


def supported_bazi_llm_tasks() -> list[str]:
    return list(TASK_CONTEXT_SPECS)


def role_llm_profile(role_key: str) -> dict[str, object]:
    if role_key not in ROLE_LLM_PROFILES:
        raise ValueError(f"unsupported bazi llm role_key: {role_key}")
    return dict(ROLE_LLM_PROFILES[role_key])


def supported_bazi_llm_roles() -> list[str]:
    return list(ROLE_LLM_PROFILES)


def _task_spec(task_type: str) -> dict[str, object]:
    if task_type not in TASK_CONTEXT_SPECS:
        raise ValueError(f"unsupported bazi llm task_type: {task_type}")
    return TASK_CONTEXT_SPECS[task_type]


def _build_sections(
    runtime: CoreRuntimeResult,
    *,
    task_type: str,
    domain: str,
    locale: str,
) -> dict[str, dict[str, object]]:
    policy = runtime.question_plan.policy_effect
    practical = _dict(policy.get("practical_reading_context"))
    ranked = _dict(policy.get("ranked_decisions"))
    return {
        "chart_facts": _chart_fact_section(runtime),
        "decision_verdicts": _decision_verdict_section(policy, domain=domain),
        "structure_dynamics": _structure_section(runtime, policy),
        "model_signals": _model_signal_section(runtime, policy),
        "ranked_decisions": _ranked_decision_section(ranked, domain=domain),
        "practical_reading": _practical_section(practical, domain=domain),
        "interaction_state": _compact_section("interaction_state", policy.get("interaction_state")),
        "hidden_factor_state": _compact_section(
            "hidden_factor_state",
            policy.get("hidden_factor_state") or policy.get("hidden_factor_calibration"),
        ),
        "known_user_signals": _known_user_signal_section(runtime),
        "answer_surface": _answer_surface_section(runtime),
        "locale_terminology": _locale_terminology_section(locale),
        "evidence": _evidence_section(runtime),
        "diagnostics_summary": _diagnostics_section(policy),
    }


def _select_required_sections(
    sections: dict[str, dict[str, object]],
    spec: dict[str, object],
    role_profile: dict[str, object],
) -> list[dict[str, object]]:
    selected: list[dict[str, object]] = []
    forbidden_sections = {str(row) for row in _list(role_profile.get("forbidden_sections"))}
    max_context_sections = int(role_profile.get("max_context_sections") or MAX_CONTEXT_SECTIONS)
    for key in list(spec["required_sections"]):
        if str(key) in forbidden_sections:
            continue
        section = sections.get(str(key))
        if section:
            selected.append(section)
    return selected[:max_context_sections]


def _decision_verdict_section(policy: dict[str, Any], *, domain: str) -> dict[str, object]:
    central = _dict(policy.get("central_reading_state"))
    result = _dict(central.get("decision_result"))
    verdicts = _list(result.get("verdicts")) or _list(central.get("decision_verdicts"))
    rows: list[dict[str, object]] = []
    for raw in verdicts:
        row = _dict(raw)
        if not row:
            continue
        row_domain = str(row.get("domain") or "")
        if domain and row_domain != domain:
            continue
        rows.append(
            {
                "verdict_id": str(row.get("verdict_id") or ""),
                "domain": row_domain,
                "headline": str(row.get("headline") or ""),
                "assertion_level": str(row.get("assertion_level") or ""),
                "confidence": _float(row.get("confidence"), 0.0),
                "evidence_refs": [str(item) for item in _list(row.get("evidence_refs"))][:MAX_EVIDENCE_ITEMS],
                "counter_evidence_refs": [str(item) for item in _list(row.get("counter_evidence_refs"))][:MAX_EVIDENCE_ITEMS],
                "allowed_assertions": [str(item) for item in _list(row.get("allowed_assertions"))][:3],
                "forbidden_assertions": [str(item) for item in _list(row.get("forbidden_assertions"))][:3],
                "advice_points": [str(item) for item in _list(row.get("advice_points"))][:3],
                "next_question_slots": [
                    {
                        "domain": str(_dict(slot).get("domain") or ""),
                        "question": str(_dict(slot).get("question") or ""),
                        "answer_shape": str(_dict(slot).get("answer_shape") or ""),
                    }
                    for slot in _list(row.get("next_question_slots"))[:2]
                ],
            }
        )
    contract = _dict(result.get("llm_expression_contract"))
    return {
        "section_id": "decision_verdicts",
        "module_id": "DecisionEngine",
        "content": {
            "engine_version": str(result.get("engine_version") or central.get("decision_engine_version") or ""),
            "domain": domain or "all",
            "verdicts": rows[:MAX_RANKED_CANDIDATES_PER_DOMAIN],
            "llm_expression_contract": {
                "llm_can_rewrite_expression_only": contract.get("llm_can_rewrite_expression_only") is not False,
                "llm_can_override_verdict": contract.get("llm_can_override_verdict") is True,
                "must_stay_within_allowed_assertions": contract.get("must_stay_within_allowed_assertions") is not False,
                "must_respect_forbidden_assertions": contract.get("must_respect_forbidden_assertions") is not False,
            },
        },
        "evidence_ids": _decision_verdict_evidence_ids(rows),
        "boundary": "decision_verdicts_are_final_verdict_boundary_for_llm_expression_not_raw_material",
    }


def _chart_fact_section(runtime: CoreRuntimeResult) -> dict[str, object]:
    time_layers = runtime.chart_context.time_layers
    return {
        "section_id": "chart_facts",
        "module_id": "M1_M2",
        "content": {
            "day_master": runtime.chart_context.day_master,
            "day_master_element": runtime.chart_context.day_master_element,
            "natal_pillars": runtime.chart_context.natal_pillars,
            "time_status": time_layers.get("status", "not_provided"),
            "luck_pillar": time_layers.get("luck_pillar", ""),
            "flow_year_pillar": time_layers.get("flow_year_pillar", ""),
            "source": "ChartContext",
        },
        "evidence_ids": [],
        "boundary": "deterministic_chart_facts_read_only",
    }


def _structure_section(runtime: CoreRuntimeResult, policy: dict[str, Any]) -> dict[str, object]:
    return {
        "section_id": "structure_dynamics",
        "module_id": "M3",
        "content": {
            "state": runtime.structure_state.state,
            "semantic_label": _public_structure_label(runtime.structure_state.semantic_label),
            "primary_chain": [_public_chain_label(row) for row in runtime.structure_state.primary_chain[:8]],
            "candidate_chain_count": len(runtime.structure_state.candidate_chains),
            "path_scores": runtime.structure_state.path_scores,
            "m3_completion_summary": _dict(policy.get("m3_completion_summary")),
            "krp_library_summary": _dict(policy.get("krp_library_summary")),
            "macro_portrait_summary": _dict(policy.get("macro_portrait_summary")),
        },
        "evidence_ids": list(runtime.structure_state.evidence_ids)[:MAX_EVIDENCE_ITEMS],
        "boundary": runtime.structure_state.boundary or "structure_state_read_only",
    }


def _model_signal_section(runtime: CoreRuntimeResult, policy: dict[str, Any]) -> dict[str, object]:
    return {
        "section_id": "model_signals",
        "module_id": "M4",
        "content": {
            "ten_god_energy_summary": _dict(policy.get("ten_god_energy_summary")),
            "model_signal_summary": _dict(policy.get("model_signal_summary")),
        },
        "evidence_ids": _feature_evidence_ids(runtime, domain="ten_god")[:MAX_EVIDENCE_ITEMS],
        "boundary": "model_signal_summary_is_calibration_signal_not_chart_fact",
    }


def _ranked_decision_section(ranked: dict[str, object], *, domain: str) -> dict[str, object]:
    domain_rows: dict[str, object] = {}
    for key, value in ranked.items():
        if domain and key != domain:
            continue
        row = _dict(value)
        scores = row.get("candidate_scores", {})
        if isinstance(scores, dict):
            row = {
                **row,
                "candidate_scores": {
                    _public_candidate_label(key): value
                    for key, value in list(scores.items())[:MAX_RANKED_CANDIDATES_PER_DOMAIN]
                },
            }
        domain_rows[key] = {
            **row,
            "primary_candidate": _public_candidate_label(row.get("primary_candidate", "")),
            "alternatives": [_public_candidate_label(item) for item in _list(row.get("alternatives"))[:MAX_RANKED_CANDIDATES_PER_DOMAIN]],
        }
    return {
        "section_id": "ranked_decisions",
        "module_id": "M5",
        "content": {
            "domain": domain or "all",
            "decisions": domain_rows,
        },
        "evidence_ids": _ranked_evidence_ids(domain_rows),
        "boundary": "ranked_decisions_are_candidate_scores_not_fixed_verdicts",
    }


def _practical_section(practical: dict[str, object], *, domain: str) -> dict[str, object]:
    domain_readings = _dict(practical.get("domain_readings"))
    if domain:
        domain_readings = {domain: domain_readings.get(domain, {})}
    return {
        "section_id": "practical_reading",
        "module_id": "M6",
        "content": {
            "status": practical.get("status", ""),
            "role_modes": practical.get("role_modes", []),
            "domain_readings": domain_readings,
            "timing_summary": _dict(practical.get("timing_summary")),
            "question_gaps": _list(practical.get("question_gaps"))[:MAX_EVIDENCE_ITEMS],
            "boundaries": _list(practical.get("boundaries")),
        },
        "evidence_ids": [],
        "boundary": "practical_reading_context_is_module_projection_not_new_fact",
    }


def _known_user_signal_section(runtime: CoreRuntimeResult) -> dict[str, object]:
    signals = _list(runtime.question_plan.session_state.get("known_user_signals"))
    if not signals:
        signals = _list(runtime.question_plan.policy_effect.get("known_user_signals"))
    return {
        "section_id": "known_user_signals",
        "module_id": "known_user_signals",
        "content": {
            "signals": signals[:MAX_USER_HISTORY_ITEMS],
            "signal_count": len(signals),
        },
        "evidence_ids": [],
        "boundary": "known_user_signals_are_feedback_not_chart_facts",
    }


def _answer_surface_section(runtime: CoreRuntimeResult) -> dict[str, object]:
    answer = runtime.answer_result
    return {
        "section_id": "answer_surface",
        "module_id": "M8",
        "content": {
            "answer_id": answer.answer_id if answer else "",
            "question_id": answer.question_id if answer else "",
            "verified_answer_draft": answer.text if answer else "",
            "source": answer.source if answer else "not_available",
            "boundary": answer.boundary if answer else "rule_bound_answer_required_before_llm",
        },
        "evidence_ids": list(answer.evidence_ids)[:MAX_EVIDENCE_ITEMS] if answer else [],
        "boundary": "verified_answer_surface_can_be_rewritten_not_fact_mutated",
    }


def _locale_terminology_section(locale: str) -> dict[str, object]:
    return {
        "section_id": "locale_terminology",
        "module_id": "locale_terminology",
        "content": {
            "locale": locale,
            "terms_required": ["day_master", "structure", "ten_god", "useful_god", "luck_cycle", "flow_year"],
            "fallback_allowed": False,
        },
        "evidence_ids": [],
        "boundary": "locale_terms_change_language_not_bazi_facts",
    }


def _evidence_section(runtime: CoreRuntimeResult) -> dict[str, object]:
    rows = [row.model_dump(mode="json") for row in runtime.feature_evidence[:MAX_EVIDENCE_ITEMS]]
    return {
        "section_id": "evidence",
        "module_id": "M3",
        "content": {"rows": rows},
        "evidence_ids": [str(row.get("evidence_id")) for row in rows if row.get("evidence_id")],
        "boundary": "evidence_rows_are_read_only",
    }


def _diagnostics_section(policy: dict[str, Any]) -> dict[str, object]:
    return {
        "section_id": "diagnostics_summary",
        "module_id": "diagnostics_summary",
        "content": {
            "central_brain_version": policy.get("central_brain_version", ""),
            "llm_provider_readiness": _dict(policy.get("llm_provider_readiness")),
            "llm_output_contract_summary": _dict(policy.get("llm_output_contract_summary")),
            "adaptive_question_diagnostics_available": bool(policy.get("adaptive_question_diagnostics")),
        },
        "evidence_ids": [],
        "boundary": "diagnostics_visible_only_for_diagnostic_roles",
    }


def _compact_section(section_id: str, value: object) -> dict[str, object]:
    return {
        "section_id": section_id,
        "module_id": section_id,
        "content": _dict(value),
        "evidence_ids": [],
        "boundary": f"{section_id}_is_dialogue_signal_not_chart_fact",
    }


def _why_included(task_type: str) -> dict[str, str]:
    return {
        "customer_initial_reading": "customer answer needs verified chart facts, ranked tendencies, and practical surface only",
        "domain_followup": "follow-up answers need selected M3/M4/M5/M6 domain context plus interaction memory, not full runtime",
        "useful_god_candidate_explanation": "candidate-path explanation needs M3/M4/M5 evidence and explicit uncertainty",
        "hidden_factor_dialogue": "hidden-factor dialogue needs feedback state and next-question state only",
        "practitioner_analysis": "practitioner output needs denser module evidence but remains read-only",
        "locale_rewrite": "locale rewrite needs verified answer and terminology only",
    }[task_type]


def _evidence_ids(sections: list[dict[str, object]]) -> list[str]:
    ids: list[str] = []
    for section in sections:
        for evidence_id in _list(section.get("evidence_ids")):
            text = str(evidence_id)
            if text and text not in ids:
                ids.append(text)
    return ids[:MAX_EVIDENCE_ITEMS]


def _feature_evidence_ids(runtime: CoreRuntimeResult, *, domain: str) -> list[str]:
    return [
        row.evidence_id
        for row in runtime.feature_evidence
        if domain in row.domain or domain in row.kind or domain in row.evidence_id
    ]


def _ranked_evidence_ids(domain_rows: dict[str, object]) -> list[str]:
    ids: list[str] = []
    for value in domain_rows.values():
        row = _dict(value)
        for key in ("supporting_evidence", "weakening_evidence"):
            for evidence_id in _list(row.get(key)):
                if str(evidence_id) not in ids:
                    ids.append(str(evidence_id))
    return ids[:MAX_EVIDENCE_ITEMS]


def _decision_verdict_evidence_ids(rows: list[dict[str, object]]) -> list[str]:
    ids: list[str] = []
    for row in rows:
        for key in ("evidence_refs", "counter_evidence_refs"):
            for evidence_id in _list(row.get(key)):
                text = str(evidence_id)
                if text and text not in ids:
                    ids.append(text)
    return ids[:MAX_EVIDENCE_ITEMS]


def _public_structure_label(value: str) -> str:
    raw = str(value or "").strip()
    lowered = raw.lower()
    traits: list[str] = []
    if any(token in lowered for token in ("branch", "dynamic")):
        traits.append("地支动态")
    if any(token in lowered for token in ("strength", "pattern")):
        traits.append("旺衰候选")
    if "ten-god" in lowered or "ten_god" in lowered:
        traits.append("十神评分")
    if "counter" in lowered:
        traits.append("反证")
    if any(token in lowered for token in ("path", "mechanism")):
        traits.append("路径评分")
    if "time layer missing" in lowered:
        traits.append("时运待补")
    if any(token in lowered for token in ("evidence", "chart", "knowledge/rule/portrait", "rule evidence")):
        traits.insert(0, "证据约束")
    priority = ["证据约束", "反证", "地支动态", "旺衰候选", "路径评分", "十神评分", "时运待补"]
    traits = [row for row in priority if row in _unique_strs(traits)][:4]
    if traits:
        detail = "、".join(row for row in traits if row != "证据约束")
        return f"证据约束型结构（含{detail}）" if detail else "证据约束型结构"
    return raw[:80] or "结构待复核"


def _public_chain_label(value: str) -> str:
    labels = {
        "chart_context": "命盘事实",
        "ten_god_visibility": "十神显隐",
        "ten_god_energy_model": "十神能量",
        "element_distribution": "五行分布",
        "branch_relation": "地支关系",
        "branch_relations": "地支关系",
        "rule_evidence": "规则证据",
        "mechanism_paths": "做功路径",
        "domain_rules": "领域规则",
    }
    return labels.get(str(value or ""), str(value or "").replace("_", " "))


def _public_candidate_label(value: object) -> str:
    raw = str(value or "").strip()
    labels = {
        "strong": "日主偏旺候选",
        "slightly_strong": "日主略偏旺候选",
        "balanced": "平衡取向",
        "slightly_weak": "日主略偏弱候选",
        "weak": "日主偏弱候选",
        "dynamic_structure_review": "动态结构复核",
        "ordinary_structure_review": "常规格局复核",
        "special_structure_boundary_review": "特殊格局边界复核",
        "mediation_path_review": "通关承接路径",
        "resource_or_self_support_review": "印比扶助方向",
        "output_or_wealth_release_review": "食伤生财或财星释放方向",
        "authority_regulation_review": "官杀约束承接方向",
        "climate_regulation_review": "调候平衡方向",
        "balance_review": "平衡调候方向",
        "needs_time_layer_review": "需要时运复核",
    }
    if raw in labels:
        return labels[raw]
    if "evidence-bound" in raw.lower():
        return _public_structure_label(raw)
    return raw.replace("_", " ") or "候选待复核"


def _dict(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list(value: object) -> list[Any]:
    return value if isinstance(value, list) else []


def _float(value: object, default: float) -> float:
    try:
        return round(float(value), 3)
    except (TypeError, ValueError):
        return default


def _unique_strs(values: list[object]) -> list[str]:
    rows: list[str] = []
    for value in values:
        text = str(value)
        if text and text not in rows:
            rows.append(text)
    return rows
