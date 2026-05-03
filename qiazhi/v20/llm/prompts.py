from __future__ import annotations

from v20.answer.prompt_context import answer_plan_prompt_context
from v20.answer.plan import AnswerPlan
from v20.features.schema import FeatureLayer
from v20.interaction.questions import QuestionCandidate
from v20.knowledge.schema import KnowledgeUnit


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
        "responsibility": "answer the user's question from a compact verified Bazi answer card",
        "style": "warm, direct, plain-language, concise",
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
    return profile


def answer_rewrite_prompt(
    plan: AnswerPlan,
    *,
    locale: str = "en",
    tone: str = "clear",
    verified_answer_text: str = "",
) -> dict[str, object]:
    context = answer_plan_prompt_context(plan)
    if verified_answer_text:
        context = {
            "version": "v20.answer_rewrite_compact_context.v1",
            "verified_answer_text": verified_answer_text,
            "domain_boundary": context["domain_boundary"],
            "evidence_summary": context["evidence_summary"],
            "guardrails": context["guardrails"],
        }
    return {
        "task": "answer_plan_rewrite",
        "locale": locale,
        "prompt_profile": prompt_profile("answer_rewriter", locale),
        "tone": tone,
        "context": context,
        "output_schema": {"text": "string"},
        "instruction": (
            "Return only {\"text\":\"...\"}. Rewrite the verified answer into a concise professional reply. "
            "Preserve concrete stems/branches, ten-god names, relation names, and evidence counts already present in the verified answer. "
            "Answer the selected question directly before stating boundaries. Do not echo the context, do not include answer_plan, and do not add facts or conclusions."
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
    locale: str = "zh",
) -> dict[str, object]:
    answer_card = _compact_practitioner_answer_card(
        chart_facts=chart_facts,
        time_context=time_context,
        selected_question=selected_question,
        verified_answer_text=verified_answer_text,
        decision_report=decision_report or {},
        portrait_projection=portrait_projection or {},
        feature_state_model=feature_state_model or {},
        question_intent_model=question_intent_model or {},
        interaction_session=interaction_session or {},
    )
    return {
        "task": "practitioner_answer",
        "locale": locale,
        "prompt_profile": prompt_profile("practitioner", locale),
        "context_version": "v20.practitioner_answer_card.v1",
        "context": answer_card,
        "output_schema": {
            "text": "string",
        },
        "instruction": (
            "Return only {\"text\":\"...\"}. You are a professional Bazi practitioner answering the selected question. "
            "Use only the compact answer card: question, chart, time, mainline, portrait_tags, evidence, next_questions, and answer_boundary. "
            "The first sentence must answer the selected question directly, then explain the strongest Bazi evidence in plain language. "
            "Do not mention internal ids, rule/debug labels, prompt/context names, or section headings. "
            "Do not create chart facts, activate rules, invent events, guarantee outcomes, infer private facts, or make fixed fortune verdicts. "
            "Keep the text under the locale-appropriate limit: zh/ko under 360 characters, en under 520 characters. "
            "Write in the requested locale exactly: zh=Chinese, en=English, ko=Korean."
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


def _compact_bazi_metadata(chart_facts: dict[str, object], time_context: dict[str, object]) -> dict[str, object]:
    return {
        **_compact_chart(chart_facts),
        "time_layers": _compact_time_context(time_context).get("layers", []),
    }


def _compact_chart(chart_facts: dict[str, object]) -> dict[str, object]:
    return {
        "day_master": chart_facts.get("day_master", ""),
        "day_master_element": chart_facts.get("day_master_element", ""),
        "pillars": chart_facts.get("pillars", {}),
        "visible_ten_gods": chart_facts.get("visible_ten_gods", [])[:8],
        "hidden_ten_gods": chart_facts.get("hidden_ten_gods", [])[:12],
    }


def _compact_time_context(time_context: dict[str, object]) -> dict[str, object]:
    return {
        "status": time_context.get("status", ""),
        "layers": time_context.get("layers", [])[:4],
        "relation_hits": time_context.get("relation_hits", [])[:8],
    }


def _compact_selected_question(selected_question: dict[str, object]) -> dict[str, object]:
    return {
        "title": selected_question.get("title", ""),
        "domain": selected_question.get("domain", ""),
        "measurement_topic": selected_question.get("measurement_topic", ""),
        "boundary": _clip(str(selected_question.get("boundary", "")), 220),
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
    decision_report: dict[str, object],
    portrait_projection: dict[str, object],
    feature_state_model: dict[str, object],
    question_intent_model: dict[str, object],
    interaction_session: dict[str, object],
) -> dict[str, object]:
    mainline = _compact_mainline_cards(decision_report)
    evidence = _compact_evidence_lines(
        decisions=mainline,
        feature_state_model=feature_state_model,
        time_context=time_context,
    )
    return {
        "question": _compact_selected_question(selected_question),
        "chart": _compact_chart_for_answer(chart_facts),
        "time": _compact_time_for_answer(time_context),
        "mainline": mainline,
        "portrait_tags": _compact_portrait_tags(portrait_projection, feature_state_model),
        "evidence": evidence,
        "intent": _compact_selected_question_intent(question_intent_model),
        "next_questions": _compact_next_questions(interaction_session, mainline),
        "answer_boundary": _compact_answer_boundary(selected_question, portrait_projection),
        "deterministic_fallback": _clip(verified_answer_text, 520),
    }


def _compact_chart_for_answer(chart_facts: dict[str, object]) -> dict[str, object]:
    return {
        "day_master": chart_facts.get("day_master", ""),
        "day_master_element": chart_facts.get("day_master_element", ""),
        "pillars": _compact_pillars(chart_facts.get("pillars", {})),
        "visible_ten_gods": _compact_ten_god_lines(chart_facts.get("visible_ten_gods", []), 5),
        "hidden_ten_gods": _compact_ten_god_lines(chart_facts.get("hidden_ten_gods", []), 6),
    }


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


def _compact_mainline_cards(report: dict[str, object]) -> list[dict[str, object]]:
    rows = []
    for row in (report.get("decisions") or [])[:5]:
        if not isinstance(row, dict):
            continue
        rows.append(
            {
                "label": _clip(str(row.get("label", "")), 80),
                "domain": row.get("domain", ""),
                "status": row.get("status", ""),
                "score": row.get("score", 0),
                "support": [_clip(str(item), 56) for item in _list_items(row.get("support"), 4) if item],
                "weakening": [_clip(str(item), 56) for item in _list_items(row.get("weakening"), 2) if item],
                "question_seeds": [_clip(str(item), 64) for item in _list_items(row.get("question_seeds"), 2) if item],
            }
        )
    return rows


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
    return rows[:10]


def _compact_portrait_tags(
    projection: dict[str, object],
    feature_state_model: dict[str, object],
) -> list[dict[str, object]]:
    rows = []
    for row in (projection.get("axes") or [])[:5]:
        if not isinstance(row, dict):
            continue
        rows.append(
            {
                "label": _clip(str(row.get("label", "")), 64),
                "domain": row.get("domain", ""),
                "state": _clip(str(row.get("calibration_state", row.get("state", ""))), 60),
                "summary": _clip("；".join(str(item) for item in (row.get("evidence_boundaries") or [])[:1] if item), 120),
            }
        )
    if rows:
        return rows
    for row in (feature_state_model.get("priority_features") or [])[:5]:
        if isinstance(row, dict):
            rows.append(
                {
                    "label": _clip(str(row.get("title", "")), 64),
                    "domain": row.get("domain", ""),
                    "state": row.get("state", ""),
                    "summary": _clip(str(row.get("boundary", "")), 120),
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


def _compact_interaction_session(session: dict[str, object]) -> dict[str, object]:
    return {
        "selected_question_title": session.get("selected_question_title", ""),
        "selected_domain": session.get("selected_domain", ""),
        "signals": [
            {
                "signal_type": row.get("signal_type", ""),
                "domain": row.get("domain", ""),
                "effect": row.get("effect", row.get("primary_intent_type", "")),
            }
            for row in (session.get("signals") or [])[:4]
            if isinstance(row, dict)
        ],
        "next_actions": [
            {
                "action_type": row.get("action_type", ""),
                "domain": row.get("domain", ""),
                "reason": row.get("reason", ""),
            }
            for row in (session.get("next_actions") or [])[:3]
            if isinstance(row, dict)
        ],
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


def _compact_answer_plan(plan: AnswerPlan) -> dict[str, object]:
    return {
        "question_key": plan.question_key,
        "sections": [
            {
                "title": section.title,
                "domain": section.domain,
                "body": _clip(section.body, 260),
            }
            for section in plan.sections[:6]
        ],
        "guardrails": list(plan.guardrails),
    }


def _clip(value: str, limit: int) -> str:
    text = str(value or "").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"
