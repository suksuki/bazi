from __future__ import annotations

from v30.contracts import AnswerContext, AnswerResult, BaziQuestionAnchor, CoreRuntimeResult
from v30.expression import build_runtime_narrative_plan, render_narrative
from v30.portrait import build_macro_portrait_projection_views


def build_answer_context(runtime: CoreRuntimeResult, anchor: BaziQuestionAnchor) -> AnswerContext:
    evidence = [row for row in runtime.feature_evidence if row.evidence_id in set(anchor.evidence_ids)]
    macro_signals = _macro_signals_for_anchor(runtime, anchor)
    macro_portraits = _macro_portraits_for_signals(runtime, macro_signals)
    macro_portrait_views = _macro_portrait_views_for_projections(runtime, macro_portraits, anchor.role_key)
    return AnswerContext(
        answer_context_id=f"{runtime.reading_id}:answer-context:{anchor.question_id}",
        selected_question_anchor=anchor,
        chart_summary={
            "day_master": runtime.chart_context.day_master,
            "day_master_element": runtime.chart_context.day_master_element,
            "time_status": runtime.chart_context.time_layers.get("status", "not_provided"),
            "six_pillar_context": runtime.chart_context.time_layers.get("six_pillar_context", {}),
        },
        structure_summary={
            "state": runtime.structure_state.state,
            "semantic_label": runtime.structure_state.semantic_label,
            "path_scores": runtime.structure_state.path_scores,
        },
        mainline_summary={
            "title": runtime.mainline_state.title,
            "quality_gate": runtime.mainline_state.quality_gate,
            "why_selected": runtime.mainline_state.why_selected,
        },
        evidence_summary=[row.model_dump(mode="json") for row in evidence],
        knowledge_boundaries=[
            *[str(row.boundary) for row in evidence if row.boundary],
            *[
                str(boundary)
                for signal in macro_signals
                for boundary in signal.get("boundaries", [])
                if boundary
            ],
        ],
        role_answer_contract={
            "role": anchor.role_key,
            "llm_role": "explain_bound_context_only",
            "can_use": [
                "chart_summary",
                "structure_summary",
                "mainline_summary",
                "evidence_summary",
                "macro_dimension_signals",
                "macro_portrait_projections",
                "macro_portrait_projection_views",
                "ranked_decisions",
                "practical_reading_context",
                "agent_question_flow",
                "ten_god_energy_summary",
                "model_signal_summary",
            ],
            "cannot_do": ["mutate_chart_facts", "invent_timing", "make_fixed_useful_god_verdict"],
            "hidden_factor_state": runtime.question_plan.policy_effect.get("hidden_factor_state", {}),
            "macro_dimension_signals": macro_signals,
            "macro_portrait_projections": macro_portraits,
            "macro_portrait_projection_views": macro_portrait_views,
            "ranked_decisions": runtime.question_plan.policy_effect.get("ranked_decisions", {}),
            "practical_reading_context": runtime.question_plan.policy_effect.get("practical_reading_context", {}),
            "agent_question_flow": runtime.question_plan.policy_effect.get("agent_question_flow", {}),
            "ten_god_energy_summary": runtime.question_plan.policy_effect.get("ten_god_energy_summary", {}),
            "model_signal_summary": runtime.question_plan.policy_effect.get("model_signal_summary", {}),
        },
        forbidden_drift=[
            "NO_LLM_FACT_GENERATION",
            "NO_UNBOUND_FORTUNE_VERDICT",
            "NO_HIDDEN_FACTOR_AS_DETERMINISTIC_FACT",
        ],
    )


def _macro_signals_for_anchor(runtime: CoreRuntimeResult, anchor: BaziQuestionAnchor) -> list[dict[str, object]]:
    signals = runtime.question_plan.policy_effect.get("macro_dimension_signals", [])
    if not isinstance(signals, list):
        return []
    rows: list[dict[str, object]] = []
    anchor_domains = _anchor_domains(anchor)
    for signal in signals:
        if not isinstance(signal, dict):
            continue
        hooks = signal.get("question_hooks", [])
        if isinstance(hooks, list) and anchor.intent_id in {str(row) for row in hooks}:
            rows.append(signal)
            continue
        domain = str(signal.get("domain") or "")
        if domain and domain in anchor_domains:
            rows.append(signal)
    return rows


def _anchor_domains(anchor: BaziQuestionAnchor) -> set[str]:
    raw = f"{anchor.question_id} {anchor.intent_id}".lower()
    domains: set[str] = set()
    for domain in ("career", "wealth", "relationship", "romance", "health", "foundation", "hidden_factor"):
        if domain in raw:
            domains.add(domain)
    if "useful_god" in raw or "current_chart" in raw:
        domains.add("foundation")
    return domains


def _macro_portraits_for_signals(
    runtime: CoreRuntimeResult,
    macro_signals: list[dict[str, object]],
) -> list[dict[str, object]]:
    projections = runtime.question_plan.policy_effect.get("macro_portrait_projections", [])
    if not isinstance(projections, list):
        return []
    source_ids = {str(signal.get("signal_id", "")) for signal in macro_signals}
    return [
        projection
        for projection in projections
        if isinstance(projection, dict) and str(projection.get("source_signal_id", "")) in source_ids
    ]


def _macro_portrait_views_for_projections(
    runtime: CoreRuntimeResult,
    projections: list[dict[str, object]],
    role_key: str,
) -> list[dict[str, object]]:
    view_payload = runtime.question_plan.policy_effect.get("macro_portrait_projection_views", [])
    projection_ids = {str(row.get("projection_id", "")) for row in projections}
    if isinstance(view_payload, list):
        rows = [
            row for row in view_payload
            if (
                isinstance(row, dict)
                and str(row.get("projection_id", "")) in projection_ids
                and str(row.get("role_key", role_key)) == role_key
            )
        ]
        if rows:
            return rows
    return [
        row.model_dump(mode="json")
        for row in build_macro_portrait_projection_views(projections, role_key=role_key, client="web")
    ]


def compose_rule_bound_answer(
    context: AnswerContext,
    runtime: CoreRuntimeResult | None = None,
) -> AnswerResult:
    evidence_ids = [row.get("evidence_id", "") for row in context.evidence_summary if row.get("evidence_id")]
    if runtime is not None:
        narrative = render_narrative(build_runtime_narrative_plan(runtime, answer_context=context))
        text = narrative.text
    else:
        text = (
            f"{context.mainline_summary['title']}。"
            "当前只顺着已定问题和证据说明，不把未确认的年份或背景线索说成定论。"
        )
    return AnswerResult(
        answer_id=f"{context.answer_context_id}:answer",
        question_id=context.selected_question_anchor.question_id,
        text=text,
        evidence_ids=[str(row) for row in evidence_ids],
        boundary="rule_bound_answer_no_llm_fact_mutation",
    )
