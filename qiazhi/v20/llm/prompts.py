from __future__ import annotations

from v20.answer.prompt_context import answer_plan_prompt_context
from v20.answer.plan import AnswerPlan
from v20.features.schema import FeatureLayer
from v20.interaction.questions import QuestionCandidate
from v20.knowledge.schema import KnowledgeUnit


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
    dynamic_portrait: dict[str, object] | None = None,
    locale: str = "zh",
) -> dict[str, object]:
    return {
        "task": "practitioner_answer",
        "locale": locale,
        "role": "evidence_bounded_bazi_practitioner",
        "context": {
            "chart": _compact_chart(chart_facts),
            "time_context": _compact_time_context(time_context),
            "selected_question": _compact_selected_question(selected_question),
            "rule_decisions": _compact_decisions(decision_report or {}),
            "dynamic_portrait": _compact_dynamic_portrait(dynamic_portrait or {}),
            "knowledge_semantic_domains": _compact_knowledge_semantic_domains(knowledge_semantic_model),
            "answer_plan": _compact_answer_plan(answer_plan),
            "verified_answer_text": _clip(verified_answer_text, 2200),
        },
        "output_schema": {
            "text": "string",
            "mainline": "string",
            "question_answer": "string",
            "evidence_notes": ["string"],
            "next_questions": ["string"],
            "boundary_notes": ["string"],
        },
        "instruction": (
            "Return only one JSON object. Act as a professional Bazi practitioner, but use only the supplied verified context. "
            "Write a useful answer for the selected question. Start directly with the reading, not with meta commentary. "
            "Do not begin with phrases like 本次分析, 八字测算重点, 命理测算主线, 知识依据, 下一步, or 测算边界. "
            "Do not use markdown headings or bold markers in the text field. "
            "Use the provided rule decisions and dynamic portrait to answer the question, then briefly mention key evidence and boundaries. "
            "Keep the text field under 650 Chinese characters; keep evidence_notes 1-3 items, next_questions 2-4 items, and boundary_notes 1-2 items. "
            "Do not wrap JSON in markdown fences. "
            "Do not create stems, branches, ten-gods, events, timing, private facts, or conclusions that are not present in the context. "
            "Do not mention internal ids. Do not output fixed good/bad verdicts or guarantee outcomes."
        ),
    }


def intent_parse_prompt(user_text: str, *, locale: str = "zh") -> dict[str, object]:
    return {
        "task": "intent_parse",
        "locale": locale,
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
        "user_text": user_text,
        "feature_domains": sorted({feature.domain for feature in feature_layer.features}),
        "question_keys": [question.question_key for question in questions],
        "instruction": "Suggest only from existing feature-backed question keys.",
    }


def feature_candidate_prompt(user_text: str, feature_layer: FeatureLayer, *, locale: str = "zh") -> dict[str, object]:
    return {
        "task": "feature_candidate_proposal",
        "locale": locale,
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
        "candidate_text": candidate_text,
        "instruction": "Review for forbidden claims, internal identifiers, privacy leaks, and missing boundaries.",
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
                "runtime_allowed": False,
            }
        )
    return rows


def _compact_dynamic_portrait(portrait: dict[str, object]) -> list[dict[str, object]]:
    rows = []
    for row in (portrait.get("tags") or [])[:6]:
        if not isinstance(row, dict):
            continue
        rows.append(
            {
                "label": row.get("label", ""),
                "domain": row.get("domain", ""),
                "summary": _clip(str(row.get("summary", "")), 160),
                "score": row.get("score", 0),
            }
        )
    return rows


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
