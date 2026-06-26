from __future__ import annotations

from v20.answer.plan import AnswerPlan
from v20.features.schema import FeatureLayer
from v20.interaction.questions import QuestionCandidate
from v20.knowledge.schema import KnowledgeUnit
from v20.role_view.narrative_prompt_framework import answer_prompt_profile_for_role


ROLE_PROFILES = {
    "intent_router": {
        "role": "bazi_question_router",
        "responsibility": "understand the user's topic and map it to existing question/domain candidates",
        "style": "brief structured routing only",
    },
    "question_designer": {
        "role": "bazi_followup_question_designer",
        "responsibility": "suggest follow-up questions only from existing candidates",
        "style": "short, practical, no new conclusions",
    },
    "feature_assistant": {
        "role": "bazi_feature_gap_assistant",
        "responsibility": "name possible evidence gaps without writing runtime features",
        "style": "cautious candidate language",
    },
    "rule_drafter": {
        "role": "bazi_knowledge_rule_drafter",
        "responsibility": "extract draft rule atoms from reviewed knowledge only",
        "style": "structured, auditable, no activation",
    },
    "answer_rewriter": {
        "role": "plain_language_bazi_editor",
        "responsibility": "rewrite verified answers clearly while preserving facts and boundaries",
        "style": "plain language, concise, no extra claims",
    },
    "practitioner": {
        "role": "professional_bazi_practitioner",
        "responsibility": "act as the Bazi practitioner who interprets the verified chart evidence and gives the user a direct reading",
        "style": "decisive practitioner reading, plain-language, practical",
    },
    "safety_reviewer": {
        "role": "bazi_answer_safety_reviewer",
        "responsibility": "check for unsupported claims, fixed fortune verdicts, private inferences, and missing boundaries",
        "style": "strict structured review",
    },
}


def prompt_profile(role_key: str, locale: str = "zh") -> dict[str, object]:
    profile = dict(ROLE_PROFILES.get(role_key, ROLE_PROFILES["practitioner"]))
    profile["role_key"] = role_key
    profile["locale"] = locale
    profile["language_instruction"] = _language_instruction(locale)
    if role_key == "practitioner":
        profile["answer_prompt_profile"] = answer_prompt_profile_for_role("practitioner", locale=locale)
    return profile


def answer_rewrite_prompt(
    plan: AnswerPlan,
    *,
    locale: str = "en",
    tone: str = "clear",
    verified_answer_text: str = "",
    brain_state: dict[str, object] | None = None,
) -> dict[str, object]:
    answer_profile = answer_prompt_profile_for_role("user", locale=locale)
    context = _answer_rewrite_context(
        plan,
        verified_answer_text=verified_answer_text,
        brain_state=brain_state or {},
    )
    return {
        "task": "answer_plan_rewrite",
        "locale": locale,
        "prompt_profile": prompt_profile("answer_rewriter", locale),
        "answer_prompt_profile": answer_profile,
        "answer_contract": _answer_contract(answer_profile, locale),
        "tone": tone,
        "context": context,
        "output_schema": {"text": "string"},
        "instruction": (
            "Return only {\"text\":\"...\"}. Rewrite the verified answer for the user using the provided context. "
            "Keep the direct answer, strongest evidence, and boundary; do not add new chart facts or claims."
        ),
    }


def practitioner_answer_prompt(
    *,
    chart_facts: dict[str, object],
    time_context: dict[str, object],
    selected_question: dict[str, object],
    knowledge_semantic_model: dict[str, object],
    answer_plan: AnswerPlan,
    verified_answer_text: str,
    decision_report: dict[str, object] | None = None,
    portrait_projection: dict[str, object] | None = None,
    feature_state_model: dict[str, object] | None = None,
    question_intent_model: dict[str, object] | None = None,
    interaction_session: dict[str, object] | None = None,
    mainline_arbitration: dict[str, object] | None = None,
    brain_state: dict[str, object] | None = None,
    locale: str = "zh",
) -> dict[str, object]:
    answer_profile = answer_prompt_profile_for_role("practitioner", locale=locale)
    answer_card = _compact_practitioner_answer_card(
        chart_facts=chart_facts,
        time_context=time_context,
        selected_question=selected_question,
        verified_answer_text=verified_answer_text,
        answer_profile=answer_profile,
        knowledge_semantic_model=knowledge_semantic_model or {},
        decision_report=decision_report or {},
        portrait_projection=portrait_projection or {},
        feature_state_model=feature_state_model or {},
        question_intent_model=question_intent_model or {},
        interaction_session=interaction_session or {},
        mainline_arbitration=mainline_arbitration or {},
        brain_state=brain_state or {},
    )
    return {
        "task": "practitioner_answer",
        "locale": locale,
        "prompt_profile": prompt_profile("practitioner", locale),
        "answer_prompt_profile": answer_profile,
        "answer_contract": _answer_contract(answer_profile, locale),
        "context_version": "v20.practitioner_answer_card.v2",
        "context": answer_card,
        "output_schema": {
            "text": "string",
        },
        "instruction": (
            "Return only {\"text\":\"...\"}. Answer the selected question from verified context as a Bazi practitioner. "
            "Use chart/time/dynamic_context/selected_question_anchor only. "
            "Lead with conclusion, evidence and boundary. Do not add facts outside context. "
            "chart.day_master is immutable; never replace it with another heavenly stem. "
            "Stay connected to selected_question_anchor.why_this_question."
        ),
    }


def intent_parse_prompt(user_text: str, *, locale: str = "zh") -> dict[str, object]:
    return {
        "task": "intent_parse",
        "locale": locale,
        "prompt_profile": prompt_profile("intent_router", locale),
        "user_text": user_text,
        "instruction": "Extract routing intent only. Do not create chart facts, rule activations, or conclusions.",
    }


def question_suggestion_prompt(
    user_text: str,
    feature_layer: FeatureLayer,
    questions: tuple[QuestionCandidate, ...],
    *,
    locale: str = "zh",
) -> dict[str, object]:
    return {
        "task": "question_suggestion",
        "locale": locale,
        "prompt_profile": prompt_profile("question_designer", locale),
        "user_text": user_text,
        "feature_domains": sorted({feature.domain for feature in feature_layer.features}),
        "question_keys": [question.question_key for question in questions],
        "instruction": "Suggest only from existing feature-backed question keys.",
    }


def feature_candidate_prompt(user_text: str, feature_layer: FeatureLayer, *, locale: str = "zh") -> dict[str, object]:
    return {
        "task": "feature_candidate_proposal",
        "locale": locale,
        "prompt_profile": prompt_profile("feature_assistant", locale),
        "user_text": user_text,
        "feature_domains": sorted({feature.domain for feature in feature_layer.features}),
        "instruction": "Propose candidate domains only. The feature compiler owns runtime features.",
    }


def rule_extraction_prompt(
    unit: KnowledgeUnit,
    *,
    corpus_validation_signal: dict[str, object] | None = None,
    locale: str = "zh",
) -> dict[str, object]:
    return {
        "task": "rule_extraction_draft",
        "locale": locale,
        "prompt_profile": prompt_profile("rule_drafter", locale),
        "reviewed_knowledge_unit": unit.to_dict(),
        "feature_hook_contracts": list(unit.feature_hooks),
        "question_hook_contracts": list(unit.question_hooks),
        "corpus_validation_signal": corpus_validation_signal or {"status": "not_available"},
        "instruction": (
            "Extract draft condition atoms from the reviewed knowledge unit only. "
            "Corpus data may suggest validation gaps but must not author new rules. "
            "Do not activate runtime rules or add fortune conclusions."
        ),
    }


def safety_review_prompt(candidate_text: str, *, locale: str = "zh") -> dict[str, object]:
    return {
        "task": "safety_review",
        "locale": locale,
        "prompt_profile": prompt_profile("safety_reviewer", locale),
        "candidate_text": candidate_text,
        "instruction": "Review for forbidden claims, internal identifiers, privacy leaks, and missing boundaries.",
    }


def _language_instruction(locale: str) -> str:
    if str(locale).startswith("en"):
        return "Write the final user-facing text in English. Keep Bazi terms readable and briefly explain specialized terms."
    if str(locale).startswith("ko"):
        return "사용자에게 보이는 답변은 한국어로 작성하고, 사주 용어는 쉽게 풀어 설명하세요."
    return "用户可见回答必须使用中文白话文，命理术语要讲人话，不要堆内部标签。"


def _answer_rewrite_context(
    plan: AnswerPlan,
    *,
    verified_answer_text: str,
    brain_state: dict[str, object],
) -> dict[str, object]:
    return {
        "version": "v20.answer_rewrite_context.v2",
        "verified_answer_text": _clip(verified_answer_text, 900),
        "question_key": plan.question_key,
        "measurement_focus": plan.measurement_focus,
        "brain_state": _public_brain_state(brain_state),
        "answer_sections": [
            {
                "title": section.title,
                "section_type": section.section_type,
                "measurement_topic": section.measurement_topic,
                "body": _clip(section.body, 220),
            }
            for section in plan.sections[:5]
        ],
        "domain_boundary": {
            "measurement_topic": (plan.domain_projection or {}).get("measurement_topic", ""),
            "allowed_claim_types": (plan.domain_projection or {}).get("allowed_claim_types", ()),
            "blocked_claim_types": (plan.domain_projection or {}).get("blocked_claim_types", ()),
            "boundary": _clip(str((plan.domain_projection or {}).get("boundary", "")), 220),
        },
        "evidence_summary": {
            "feature_count": len(plan.evidence_pack.feature_ids),
            "evidence_ref_count": len(plan.evidence_pack.evidence_refs),
            "boundary_count": len(plan.evidence_pack.boundaries),
        },
        "runtime_mutation": False,
        "guardrails": [
            "REWRITE_CONTEXT_USES_VERIFIED_ANSWER",
            "NO_NEW_FACTS",
            "NO_UNSUPPORTED_CLAIMS",
            "NO_INTERNAL_IDS_IN_USER_TEXT",
        ],
    }


def _public_brain_state(brain_state: dict[str, object] | None) -> dict[str, object]:
    if not isinstance(brain_state, dict):
        return {}
    summary = brain_state.get("public_summary")
    if not isinstance(summary, dict):
        return {}
    return {
        "headline": summary.get("headline", ""),
        "primary_title": summary.get("primary_title", ""),
        "primary_domain": summary.get("primary_domain", ""),
        "selection_reasons": list(summary.get("selection_reasons", ()))[:4] if isinstance(summary.get("selection_reasons", ()), list) else [],
        "selected_question_title": summary.get("selected_question_title", ""),
        "answer_guidance": list(summary.get("answer_guidance", ()))[:3] if isinstance(summary.get("answer_guidance", ()), list) else [],
        "question_focus_status": summary.get("question_focus_status", ""),
        "coordination_status": summary.get("coordination_status", ""),
        "coordination_note": summary.get("coordination_note", ""),
        "runtime_policy_coordination": summary.get("runtime_policy_coordination", {}) if isinstance(summary.get("runtime_policy_coordination", {}), dict) else {},
        "next_action": summary.get("next_action", ""),
    }


def _compact_selected_question(selected_question: dict[str, object]) -> dict[str, object]:
    narrative = selected_question.get("question_narrative", {})
    if not isinstance(narrative, dict):
        narrative = {}
    anchor = selected_question.get("question_anchor", {})
    if not isinstance(anchor, dict):
        anchor = {}
    return {
        "title": selected_question.get("display_title", "") or selected_question.get("title", ""),
        "domain": selected_question.get("domain", ""),
        "measurement_topic": selected_question.get("measurement_topic", ""),
        "boundary": _clip(str(selected_question.get("boundary", "")), 180),
        "anchor": {
            "anchor_status": anchor.get("anchor_status", ""),
            "context_id": anchor.get("context_id", ""),
            "day_master": anchor.get("day_master", ""),
            "primary_dynamic_chain_label": anchor.get("primary_dynamic_chain_label", ""),
            "luck_pillar": anchor.get("luck_pillar", ""),
            "flow_year_pillar": anchor.get("flow_year_pillar", ""),
            "why_this_question": _clip(str(anchor.get("why_this_question", "")), 72),
        },
        "narrative": {
            "why_now": _clip(str(narrative.get("why_now", "")), 96),
            "bazi_basis": _clip(str(narrative.get("bazi_basis", "")), 96),
            "next_step": _clip(str(narrative.get("next_step", "")), 96),
        },
    }


def _compact_feature_states(model: dict[str, object]) -> list[dict[str, object]]:
    rows = []
    source = model.get("priority_features") or model.get("states") or []
    for row in source[:8]:
        if not isinstance(row, dict):
            continue
        rows.append(
            {
                "title": row.get("title", ""),
                "domain": row.get("domain", ""),
                "state": row.get("state", ""),
                "priority": row.get("priority", 0),
                "boundary": _clip(str(row.get("boundary", "")), 140),
            }
        )
    return rows


def _compact_practitioner_answer_card(
    *,
    chart_facts: dict[str, object],
    time_context: dict[str, object],
    selected_question: dict[str, object],
    verified_answer_text: str,
    answer_profile: dict[str, object],
    knowledge_semantic_model: dict[str, object],
    decision_report: dict[str, object],
    portrait_projection: dict[str, object],
    feature_state_model: dict[str, object],
    question_intent_model: dict[str, object],
    interaction_session: dict[str, object],
    mainline_arbitration: dict[str, object],
    brain_state: dict[str, object],
) -> dict[str, object]:
    selected_domain = str(selected_question.get("domain") or "")
    mainline = _compact_arbitrated_mainline_cards(mainline_arbitration) or _compact_mainline_cards(decision_report, selected_domain=selected_domain)
    evidence = _compact_evidence_lines(
        decisions=mainline,
        feature_state_model=feature_state_model,
        time_context=time_context,
    )
    return {
        "system_understanding": _compact_system_understanding(
            chart_facts=chart_facts,
            time_context=time_context,
            selected_question=selected_question,
            answer_profile=answer_profile,
            decision_report=decision_report,
            portrait_projection=portrait_projection,
            feature_state_model=feature_state_model,
            knowledge_semantic_model=knowledge_semantic_model,
            brain_state=brain_state,
        ),
        "question": _compact_selected_question(selected_question),
        "selected_question_anchor": _compact_selected_question(selected_question).get("anchor", {}),
        "chart": _compact_chart_for_answer(chart_facts),
        "time": _compact_time_for_answer(time_context),
        "brain_state": _compact_brain_state(brain_state),
        "dynamic_context": _compact_dynamic_context(brain_state),
        "mainline": mainline,
        "answer_strategy": _compact_answer_strategy(mainline_arbitration),
        "portrait_tags": _compact_portrait_tags(portrait_projection, feature_state_model),
        "evidence": evidence,
        "intent": _compact_selected_question_intent(question_intent_model),
        "next_questions": _compact_next_questions(interaction_session, mainline),
        "answer_boundary": _compact_answer_boundary(selected_question, portrait_projection),
        "deterministic_fallback": _clip(verified_answer_text, 180),
        "context_budget": {
            "policy": "compact_verified_context",
            "target_chars": 5200,
            "priority": ("chart", "time", "dynamic_context", "selected_question_anchor", "brain_state", "mainline", "boundary"),
        },
    }


def _answer_contract(answer_profile: dict[str, object], locale: str) -> dict[str, object]:
    return {
        "version": "v20.llm_answer_contract.v1",
        "voice_profile": answer_profile.get("voice_profile", ""),
        "structure": answer_profile.get("answer_structure", ()),
        "required": answer_profile.get("required_elements", ()),
        "forbidden": answer_profile.get("forbidden_patterns", ()),
        "locale_policy": answer_profile.get("locale_policy", {"locale": locale}),
        "length_limit": "zh/ko <= 480 chars; en <= 680 chars",
        "output": "JSON only: {\"text\":\"...\"}",
        "runtime_mutation": False,
    }


def _compact_system_understanding(
    *,
    chart_facts: dict[str, object],
    time_context: dict[str, object],
    selected_question: dict[str, object],
    answer_profile: dict[str, object],
    decision_report: dict[str, object],
    portrait_projection: dict[str, object],
    feature_state_model: dict[str, object],
    knowledge_semantic_model: dict[str, object],
    brain_state: dict[str, object],
) -> dict[str, object]:
    return {
        "version": "v20.llm_system_understanding.v1",
        "role_context": _role_context_for_llm(answer_profile, selected_question),
        "bazi_context_profile": _bazi_context_profile(
            selected_question=selected_question,
            time_context=time_context,
            decision_report=decision_report,
            feature_state_model=feature_state_model,
        ),
        "mainline_rules": _compact_rule_signals(decision_report)[:1],
        "feature_states": _compact_feature_states_light(feature_state_model),
        "portrait_axes": _compact_portrait_projection_light(portrait_projection),
        "knowledge_domains": _compact_knowledge_domains_light(knowledge_semantic_model),
        "answer_policy": "只使用上下文里的八字、大运流年、结构主链、画像和知识要点；冲突时以 brain_state/mainline 为准。",
        "runtime_mutation": False,
    }


def _role_context_for_llm(answer_profile: dict[str, object], selected_question: dict[str, object]) -> dict[str, object]:
    role_key = str(answer_profile.get("role_key", "analyst") or "analyst")
    domain = str(selected_question.get("domain", "") or "")
    voice_profile = str(answer_profile.get("voice_profile", "") or "")
    if role_key in {"guest"}:
        density = "plain_entry"
        focus = ("what_to_read_first", "soft_boundary", "next_step")
    elif role_key in {"user"}:
        density = "guided_plain_language"
        focus = ("direct_answer", "why_this_matters", "bazi_basis_plain", "next_step")
    elif role_key in {"admin", "lab"}:
        density = "runtime_observation"
        focus = ("source", "policy_effect", "runtime_pointer", "blocker")
    else:
        density = "practitioner_evidence_review"
        focus = ("direct_answer", "evidence", "boundary", "counterexample_condition", "next_review")
    return {
        "version": "v20.llm_role_context.v1",
        "role_key": role_key,
        "voice_profile": voice_profile,
        "context_density": density,
        "domain_focus": domain,
        "focus": focus,
        "runtime_mutation": False,
    }


def _bazi_context_profile(
    *,
    selected_question: dict[str, object],
    time_context: dict[str, object],
    decision_report: dict[str, object],
    feature_state_model: dict[str, object],
) -> dict[str, object]:
    selected_domain = str(selected_question.get("domain", "") or "")
    feature_domains = [
        str(row.get("domain", ""))
        for row in (feature_state_model.get("priority_features") or feature_state_model.get("states") or [])[:6]
        if isinstance(row, dict) and row.get("domain")
    ]
    decision_domains = [
        str(row.get("domain", ""))
        for row in (decision_report.get("decisions") or [])[:6]
        if isinstance(row, dict) and row.get("domain")
    ]
    active_domains = tuple(dict.fromkeys([selected_domain, *feature_domains, *decision_domains]))
    has_time = bool(time_context.get("layers") or time_context.get("relation_hits"))
    return {
        "version": "v20.llm_bazi_context_profile.v1",
        "selected_domain": selected_domain,
        "active_domains": active_domains,
        "has_time_context": has_time,
        "structure_mode": _structure_mode(active_domains, has_time),
        "runtime_mutation": False,
    }


def _structure_mode(active_domains: tuple[str, ...], has_time: bool) -> str:
    if has_time or "time" in active_domains:
        return "time_triggered_structure"
    if {"wealth", "career", "relationship", "health"} & set(active_domains):
        return "applied_domain_structure"
    if {"strength", "useful_god", "ten_god", "element", "branch", "pattern"} & set(active_domains):
        return "core_bazi_structure"
    return "general_structure"


def _compact_rule_signals(report: dict[str, object]) -> list[dict[str, object]]:
    rows = []
    for decision in _compact_decisions(report)[:2]:
        atoms = []
        for ref in decision.pop("knowledge_rules", []) if isinstance(decision, dict) else []:
            if not isinstance(ref, dict):
                continue
            atoms.extend(ref.get("condition_atoms", []) if isinstance(ref.get("condition_atoms"), list) else [])
        rows.append(
            {
                "label": decision.get("label", ""),
                "domain": decision.get("domain", ""),
                "status": decision.get("status", ""),
                "score": decision.get("score", 0),
                "support": list(decision.get("support", ())[:1]) if isinstance(decision.get("support", ()), (list, tuple)) else [],
                "weakening": list(decision.get("weakening", ())[:1]) if isinstance(decision.get("weakening", ()), (list, tuple)) else [],
                "condition_atoms": atoms[:1],
            }
        )
    return rows


def _compact_brain_state_light(brain_state: dict[str, object]) -> dict[str, object]:
    summary = _compact_brain_state(brain_state)
    return {
        "primary_title": summary.get("primary_title", ""),
        "primary_domain": summary.get("primary_domain", ""),
        "selected_question_title": summary.get("selected_question_title", ""),
        "selection_reasons": list(summary.get("selection_reasons", [])[:2]) if isinstance(summary.get("selection_reasons"), list) else [],
        "next_action": summary.get("next_action", ""),
    }


def _compact_feature_states_light(model: dict[str, object]) -> list[dict[str, object]]:
    return [
        {
            "title": row.get("title", ""),
            "domain": row.get("domain", ""),
            "state": row.get("state", ""),
        }
        for row in _compact_feature_states(model)[:3]
    ]


def _compact_portrait_projection_light(projection: dict[str, object]) -> list[dict[str, object]]:
    return [
        {
            "label": row.get("label", ""),
            "domain": row.get("domain", ""),
            "state": row.get("calibration_state", ""),
        }
        for row in _compact_portrait_projection(projection)[:2]
    ]


def _compact_knowledge_domains_light(model: dict[str, object]) -> list[dict[str, object]]:
    return [
        {
            "label": row.get("label", ""),
            "stage": row.get("stage", ""),
            "boundary": _clip(str(row.get("boundary", "")), 80),
        }
        for row in _compact_knowledge_semantic_domains(model)[:2]
    ]


def _compact_brain_state(brain_state: dict[str, object]) -> dict[str, object]:
    summary = brain_state.get("public_summary") if isinstance(brain_state, dict) else {}
    if not isinstance(summary, dict):
        return {}
    support = []
    for row in summary.get("supporting_evidence", []) if isinstance(summary.get("supporting_evidence", []), list) else []:
        if not isinstance(row, dict):
            continue
        support.append(
            {
                "label": row.get("label", ""),
                "summary": _clip(str(row.get("summary", "")), 120),
                "confidence": row.get("confidence", 0),
            }
        )
        if len(support) >= 3:
            break
    return {
        "headline": _clip(str(summary.get("headline", "")), 120),
        "primary_title": summary.get("primary_title", ""),
        "primary_domain": summary.get("primary_domain", ""),
        "selection_reasons": [_clip(str(row), 90) for row in summary.get("selection_reasons", [])[:3]] if isinstance(summary.get("selection_reasons", []), list) else [],
        "selected_question_title": summary.get("selected_question_title", ""),
        "question_focus_status": summary.get("question_focus_status", ""),
        "coordination_status": summary.get("coordination_status", ""),
        "coordination_note": _clip(str(summary.get("coordination_note", "")), 120),
        "next_action": _clip(str(summary.get("next_action", "")), 120),
        "supporting_evidence": support,
    }


def _compact_dynamic_context(brain_state: dict[str, object]) -> dict[str, object]:
    summary = brain_state.get("public_summary") if isinstance(brain_state, dict) else {}
    if not isinstance(summary, dict):
        return {}
    work_path = summary.get("dynamic_work_path", {})
    if not isinstance(work_path, dict):
        work_path = {}
    return {
        "label": _clip(str(work_path.get("label", "") or summary.get("dynamic_chain", "")), 72),
        "path": _clip(str(work_path.get("path", "") or summary.get("dynamic_chain", "")), 140),
        "action": _clip(str(work_path.get("action", "")), 90),
        "state": _clip(str(work_path.get("state", "") or summary.get("chain_state", "")), 60),
        "confidence": work_path.get("confidence", 0),
        "boundary": "结构动态只定本局做功主线，回答必须回到当前八字、大运和流年。",
    }


def _compact_chart_for_answer(chart_facts: dict[str, object]) -> dict[str, object]:
    day_master = str(chart_facts.get("day_master", ""))
    day_master_element = str(chart_facts.get("day_master_element", ""))
    day_master_element_label = _element_label(day_master_element)
    return {
        "day_master": day_master,
        "day_master_element": day_master_element,
        "day_master_label": f"{day_master}{day_master_element_label}" if day_master else "",
        "immutable_fact": f"日主={day_master}{day_master_element_label}，不得改写或重算。",
        "pillars": _compact_pillars(chart_facts.get("pillars", {})),
        "visible_ten_gods": _compact_ten_god_lines(chart_facts.get("visible_ten_gods", []), 4),
        "hidden_ten_gods": _compact_ten_god_lines(chart_facts.get("hidden_ten_gods", []), 4),
    }


def _element_label(element: str) -> str:
    return {
        "wood": "木",
        "fire": "火",
        "earth": "土",
        "metal": "金",
        "water": "水",
    }.get(str(element or ""), str(element or ""))


def _compact_pillars(pillars: object) -> dict[str, str]:
    if not isinstance(pillars, dict):
        return {}
    rows: dict[str, str] = {}
    for key in ("year", "month", "day", "hour"):
        pillar = pillars.get(key, {})
        if isinstance(pillar, dict):
            rows[key] = f"{pillar.get('stem', '')}{pillar.get('branch', '')}"
        else:
            rows[key] = str(pillar or "")
    return rows


def _compact_ten_god_lines(items: object, limit: int) -> list[str]:
    rows = []
    for item in list(items or [])[:limit] if isinstance(items, (list, tuple)) else []:
        if not isinstance(item, dict):
            continue
        label = item.get("label", "")
        stem = item.get("stem", "")
        pillar = item.get("pillar", "")
        layer = item.get("layer", "")
        rows.append("".join(part for part in (str(label), f"@{stem}" if stem else "", f"/{pillar}" if pillar else "", f"/{layer}" if layer else "") if part))
    return rows


def _compact_time_for_answer(time_context: dict[str, object]) -> dict[str, object]:
    lines = []
    for layer in (time_context.get("layers") or [])[:3]:
        if not isinstance(layer, dict):
            continue
        pillar = layer.get("pillar", {})
        ten_god = layer.get("ten_god", {})
        pillar_text = ""
        if isinstance(pillar, dict):
            pillar_text = f"{pillar.get('stem', '')}{pillar.get('branch', '')}"
        ten_god_text = ten_god.get("label", "") if isinstance(ten_god, dict) else ""
        lines.append(" ".join(item for item in (str(layer.get("layer_key", "")), pillar_text, str(ten_god_text)) if item))
    for hit in (time_context.get("relation_hits") or [])[:4]:
        if not isinstance(hit, dict):
            continue
        branches = hit.get("branches", [])
        relation = hit.get("relation_type", "")
        if isinstance(branches, (list, tuple)) and relation:
            lines.append(f"{''.join(str(item) for item in branches)} {relation}")
    return {
        "status": time_context.get("status", ""),
        "signals": lines[:6],
    }


def _compact_mainline_cards(report: dict[str, object], *, selected_domain: str = "") -> list[dict[str, object]]:
    rows = []
    decisions = [row for row in (report.get("decisions") or []) if isinstance(row, dict)]
    same_domain = [row for row in decisions if selected_domain and row.get("domain") == selected_domain]
    ordered = [*same_domain, *[row for row in decisions if row not in same_domain]]
    for row in ordered[:4]:
        if not isinstance(row, dict):
            continue
        rows.append(
            {
                "label": _clip(str(row.get("label", "")), 80),
                "domain": row.get("domain", ""),
                "status": row.get("status", ""),
                "score": row.get("score", 0),
                "support": [_clip(str(item), 52) for item in _list_items(row.get("support"), 2) if item],
                "weakening": [_clip(str(item), 52) for item in _list_items(row.get("weakening"), 1) if item],
                "question_seeds": [_clip(str(item), 56) for item in _list_items(row.get("question_seeds"), 1) if item],
            }
        )
    return rows


def _compact_arbitrated_mainline_cards(arbitration: dict[str, object]) -> list[dict[str, object]]:
    primary = arbitration.get("primary_mainline", {})
    if not isinstance(primary, dict):
        return []
    title = str(primary.get("title", "")).strip()
    nodes = _list_items(primary.get("nodes"), 4)
    if not title and not nodes:
        return []
    evidence = _list_items(primary.get("evidence"), 3)
    why = _list_items(arbitration.get("why_selected"), 2)
    quality_gate = arbitration.get("quality_gate", {})
    practitioner_review = arbitration.get("practitioner_review", {})
    rows = [
        {
            "label": _clip(title or " → ".join(str(row) for row in nodes), 72),
            "domain": primary.get("domain", ""),
            "status": primary.get("status", ""),
            "score": primary.get("score", 0),
            "source": primary.get("source", ""),
            "nodes": [str(row) for row in nodes[:3]],
            "support": [_clip(str(item), 60) for item in evidence if item],
            "why_selected": [_clip(str(item), 72) for item in why if item],
            "quality_gate": _compact_quality_gate(quality_gate if isinstance(quality_gate, dict) else {}),
            "practitioner_review": _compact_practitioner_review(practitioner_review if isinstance(practitioner_review, dict) else {}),
            "question_seeds": [],
        }
    ]
    for row in _list_items(arbitration.get("supporting_mainlines"), 1):
        if not isinstance(row, dict):
            continue
        rows.append(
            {
                "label": _clip(str(row.get("title", "")), 64),
                "domain": row.get("domain", ""),
                "status": row.get("status", ""),
                "score": row.get("score", 0),
                "source": row.get("source", ""),
                "nodes": [str(item) for item in _list_items(row.get("nodes"), 3)],
                "support": [_clip(str(item), 56) for item in _list_items(row.get("evidence"), 2) if item],
                "why_selected": [],
                "question_seeds": [],
            }
        )
    return rows


def _compact_answer_strategy(arbitration: dict[str, object]) -> dict[str, object]:
    if not isinstance(arbitration, dict):
        return {}
    gate = arbitration.get("quality_gate", {})
    review = arbitration.get("practitioner_review", {})
    gate = gate if isinstance(gate, dict) else {}
    review = review if isinstance(review, dict) else {}
    action = str(review.get("action", ""))
    requires_review = bool(gate.get("requires_review"))
    if action == "accepted_primary":
        mode = "confirmed_by_practitioner"
        instruction = "Use the confirmed primary mainline as the answer spine; keep event claims bounded."
    elif action == "promoted_supporting":
        mode = "practitioner_switched_needs_review"
        instruction = "Use the promoted supporting mainline first and note the session-level switch."
    elif action == "evidence_gap":
        mode = "evidence_gap_review"
        instruction = "Lead with evidence gaps and avoid firm conclusions."
    elif action in {"deferred_primary", "no_supporting_candidate"}:
        mode = "deferred_review"
        instruction = "Keep the mainline provisional and list review targets."
    elif requires_review:
        mode = "quality_gate_review"
        instruction = "Present the mainline as provisional and explain review targets."
    else:
        mode = "quality_gate_passed"
        instruction = "Use the primary mainline as the answer spine while preserving boundaries."
    return {
        "mode": mode,
        "requires_review": requires_review,
        "quality_gate_status": gate.get("status", ""),
        "practitioner_action": action,
        "instruction": _clip(instruction, 90),
    }


def _compact_quality_gate(gate: dict[str, object]) -> dict[str, object]:
    if not gate:
        return {}
    return {
        "status": gate.get("status", ""),
        "requires_review": bool(gate.get("requires_review")),
        "risk_flags": [str(row) for row in _list_items(gate.get("risk_flags"), 4)],
    }


def _compact_practitioner_review(review: dict[str, object]) -> dict[str, object]:
    if review.get("status") != "applied":
        return {}
    return {
        "status": review.get("status", ""),
        "option": review.get("option", ""),
        "action": review.get("action", ""),
    }


def _compact_evidence_lines(
    *,
    decisions: list[dict[str, object]],
    feature_state_model: dict[str, object],
    time_context: dict[str, object],
) -> list[str]:
    seen = set()
    rows = []

    def add(value: object) -> None:
        text = _clip(str(value), 70)
        if text and text not in seen:
            seen.add(text)
            rows.append(text)

    for decision in decisions:
        for item in decision.get("support", []) if isinstance(decision, dict) else []:
            add(item)
        for item in decision.get("weakening", []) if isinstance(decision, dict) else []:
            add(item)
    for feature in (feature_state_model.get("priority_features") or [])[:4]:
        if isinstance(feature, dict):
            add(f"{feature.get('title', '')}：{feature.get('state', '')}")
    for item in _compact_time_for_answer(time_context).get("signals", [])[:3]:
        add(item)
    return rows[:6]


def _compact_portrait_tags(
    projection: dict[str, object],
    feature_state_model: dict[str, object],
) -> list[dict[str, object]]:
    rows = []
    for row in (projection.get("axes") or [])[:3]:
        if not isinstance(row, dict):
            continue
        rows.append(
            {
                "label": _clip(str(row.get("label", "")), 56),
                "domain": row.get("domain", ""),
                "state": _clip(str(row.get("calibration_state", row.get("state", ""))), 48),
                "summary": _clip("；".join(str(item) for item in (row.get("evidence_boundaries") or [])[:1] if item), 90),
            }
        )
    if rows:
        return rows
    for row in (feature_state_model.get("priority_features") or [])[:3]:
        if isinstance(row, dict):
            rows.append(
                {
                    "label": _clip(str(row.get("title", "")), 56),
                    "domain": row.get("domain", ""),
                    "state": row.get("state", ""),
                    "summary": _clip(str(row.get("boundary", "")), 90),
                }
            )
    return rows


def _compact_next_questions(
    interaction_session: dict[str, object],
    decisions: list[dict[str, object]],
) -> list[str]:
    rows = []
    for row in decisions:
        if isinstance(row, dict):
            rows.extend(str(item) for item in row.get("question_seeds", []) if item)
    selected_title = interaction_session.get("selected_question_title", "")
    if selected_title:
        rows.insert(0, str(selected_title))
    unique = []
    seen = set()
    for row in rows:
        text = _clip(row, 90)
        if text and text not in seen:
            seen.add(text)
            unique.append(text)
    return unique[:4]


def _compact_answer_boundary(
    selected_question: dict[str, object],
    portrait_projection: dict[str, object],
) -> str:
    boundary = str(selected_question.get("boundary") or "")
    if not boundary:
        for row in (portrait_projection.get("axes") or [])[:3]:
            if isinstance(row, dict):
                notes = row.get("evidence_boundaries") or []
                if notes:
                    boundary = str(notes[0])
                    break
    if not boundary:
        boundary = "只根据当前八字结构和已验证证据回答，不作固定吉凶、具体事件或确定时间断语。"
    return _clip(boundary, 220)


def _list_items(value: object, limit: int) -> list[object]:
    if isinstance(value, (list, tuple)):
        return list(value[:limit])
    return []


def _compact_decisions(report: dict[str, object]) -> list[dict[str, object]]:
    rows = []
    for row in (report.get("decisions") or [])[:7]:
        if not isinstance(row, dict):
            continue
        rows.append(
            {
                "label": row.get("label", ""),
                "domain": row.get("domain", ""),
                "status": row.get("status", ""),
                "role": row.get("role", ""),
                "score": row.get("score", 0),
                "support": list(row.get("support", ())[:4]) if isinstance(row.get("support", ()), (list, tuple)) else [],
                "weakening": list(row.get("weakening", ())[:3]) if isinstance(row.get("weakening", ()), (list, tuple)) else [],
                "question_seeds": list(row.get("question_seeds", ())[:3]) if isinstance(row.get("question_seeds", ()), (list, tuple)) else [],
                "knowledge_rules": _compact_decision_knowledge_rules(row),
            }
        )
    return rows


def _compact_decision_knowledge_rules(decision: dict[str, object]) -> list[dict[str, object]]:
    rows = []
    for ref in (decision.get("knowledge_rule_refs") or [])[:2]:
        if not isinstance(ref, dict):
            continue
        atoms = []
        for atom in (ref.get("condition_atoms") or [])[:3]:
            if isinstance(atom, dict):
                atoms.append(
                    {
                        "atom_type": atom.get("atom_type", ""),
                        "operator": atom.get("operator", ""),
                        "evidence_role": atom.get("evidence_role", ""),
                    }
                )
        rows.append(
            {
                "title": ref.get("title", ""),
                "domain": ref.get("domain", ""),
                "portrait_labels": list(ref.get("portrait_labels", ())[:2]) if isinstance(ref.get("portrait_labels", ()), (list, tuple)) else [],
                "question_titles": list(ref.get("question_titles", ())[:2]) if isinstance(ref.get("question_titles", ()), (list, tuple)) else [],
                "condition_atoms": atoms,
                "boundary": _clip(str(ref.get("boundary", "")), 180),
                "runtime_allowed": True,
            }
        )
    return rows


def _compact_portrait_projection(projection: dict[str, object]) -> list[dict[str, object]]:
    rows = []
    for row in (projection.get("axes") or [])[:6]:
        if not isinstance(row, dict):
            continue
        rows.append(
            {
                "label": row.get("label", ""),
                "domain": row.get("domain", ""),
                "calibration_state": _clip(str(row.get("calibration_state", "")), 160),
                "evidence_boundaries": [
                    _clip(str(item), 120)
                    for item in (row.get("evidence_boundaries") or [])[:2]
                    if item
                ],
                "score": row.get("peak_confidence", row.get("alignment_score", 0)),
            }
        )
    return rows


def _compact_selected_question_intent(model: dict[str, object]) -> dict[str, object]:
    binding = model.get("selected_question_intent", {})
    if not isinstance(binding, dict):
        return {}
    return {
        "question_key": binding.get("question_key", ""),
        "title": binding.get("title", ""),
        "domain": binding.get("domain", ""),
        "primary_intent_type": binding.get("primary_intent_type", ""),
        "intent_priority": binding.get("intent_priority", 0),
    }


def _compact_knowledge_semantic_domains(model: dict[str, object]) -> list[dict[str, object]]:
    rows = []
    for row in (model.get("domain_models") or [])[:7]:
        if not isinstance(row, dict):
            continue
        rows.append(
            {
                "label": row.get("label", ""),
                "stage": row.get("measurement_stage", ""),
                "portrait_labels": [
                    item.get("label", "")
                    for item in (row.get("portrait_label_candidates") or [])[:3]
                    if isinstance(item, dict)
                ],
                "boundary": _clip(str(row.get("boundary_summary", "")), 180),
            }
        )
    return rows


def _clip(value: str, limit: int) -> str:
    text = str(value or "").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"
