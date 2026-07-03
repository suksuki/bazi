from __future__ import annotations

from typing import Any

from v30.brain.dialogue_planner import (
    CUSTOMER_DECISION_FIELD,
    DIALOGUE_PLANNER_VERSION,
    LEGACY_CUSTOMER_DECISION_FIELD,
    SURFACE_DECISION_FIELDS,
    build_dialogue_plan,
)
from v30.brain.decision_engine import (
    DECISION_ENGINE_VERSION,
    build_decision_result,
)
from v30.brain.central_feedback_overlay import (
    CENTRAL_FEEDBACK_OVERLAY_VERSION,
    build_central_feedback_overlay,
    overlay_adjustment_for_claim,
)
from v30.brain.feedback_weight_updater import (
    FEEDBACK_WEIGHT_UPDATER_VERSION,
    build_feedback_weight_update,
)
from v30.brain.final_synthesis import (
    FINAL_SYNTHESIS_ENGINE_VERSION,
    build_final_synthesis,
)
from v30.brain.dialogue_training import build_dialogue_training_trace
from v30.brain.contracts import (
    BrainBeliefState,
    BrainClaimBelief,
    BrainDecisionTrace,
    BrainEvidenceGraphSnapshot,
    BrainQuestionCandidate,
    BrainTrainingExample,
    BrainUncertaintySlot,
)
from v30.brain.training_examples import build_brain_training_example
from v30.production.adapters import signals_from_diagnosis, signals_from_ranked_decisions
from v30.production.signal_registry import build_signal_registry
from v30.semantics import (
    BAZI_SEMANTIC_ONTOLOGY_VERSION,
    get_bazi_semantic_ontology,
    semantic_projection_for_claim,
)


CENTRAL_READING_ENGINE_VERSION = "v30.central_reading_engine.v1"
CENTRAL_READING_STATE_VERSION = "v30.central_reading_state.v1"


def build_central_reading_state(
    *,
    reading_id: str,
    role_key: str,
    diagnosis: dict[str, object],
    recommendations: list[dict[str, object]],
    question_dialogue_graph: dict[str, object],
    interaction_state: dict[str, object],
    practical_reading_context: dict[str, object] | None = None,
    ranked_decisions: dict[str, object] | None = None,
    model_signal_summary: dict[str, object] | None = None,
    question_policy: dict[str, object] | None = None,
    question_outcomes: list[dict[str, object]] | None = None,
    practitioner_selections: list[dict[str, object]] | None = None,
    active_stage_id: str = "",
) -> dict[str, object]:
    claims = _list(diagnosis.get("claims"))
    graph = diagnosis.get("graph") if isinstance(diagnosis.get("graph"), dict) else {}
    summaries = diagnosis.get("summaries") if isinstance(diagnosis.get("summaries"), dict) else {}
    graph_summary = summaries.get("graph") if isinstance(summaries.get("graph"), dict) else {}
    evidence_graph_snapshot = _evidence_graph_snapshot(
        reading_id=reading_id,
        graph=graph if isinstance(graph, dict) else {},
        graph_summary=graph_summary if isinstance(graph_summary, dict) else {},
    )
    graph_claim_metrics = _graph_claim_metrics(graph if isinstance(graph, dict) else {})
    paths = {str(row.get("path_id") or ""): row for row in _list(diagnosis.get("paths")) if isinstance(row, dict)}
    portraits = {
        str(row.get("portrait_id") or ""): row
        for row in _list(diagnosis.get("portraits"))
        if isinstance(row, dict)
    }
    outcomes = question_outcomes or []
    central_feedback_overlay = build_central_feedback_overlay(
        question_outcomes=outcomes,
        practitioner_selections=practitioner_selections or [],
    )
    feedback_weight_update = build_feedback_weight_update(
        claims=claims,
        question_outcomes=outcomes,
    )
    feedback_signals = {
        str(row.get("claim_id") or ""): row
        for row in _list(feedback_weight_update.get("claim_alignment_signals"))
        if isinstance(row, dict)
    }
    claim_scores = [
        _score_claim(
            claim,
            paths=paths,
            portraits=portraits,
            question_outcomes=outcomes,
            feedback_signal=feedback_signals.get(str(claim.get("claim_id") or ""), {}),
            practical_reading_context=practical_reading_context or {},
            ranked_decisions=ranked_decisions or {},
            graph_metrics=graph_claim_metrics.get(str(claim.get("claim_id") or ""), {}),
            central_feedback_overlay=central_feedback_overlay,
        )
        for claim in claims
        if isinstance(claim, dict)
    ]
    claim_scores.sort(key=lambda row: (-float(row.get("score") or 0.0), str(row.get("claim_id") or "")))
    decision_signal_registry = build_signal_registry(
        reading_id=reading_id,
        signals=[
            *signals_from_diagnosis(diagnosis),
            *signals_from_ranked_decisions(ranked_decisions or {}),
        ],
        registry_id=f"{reading_id}:{active_stage_id or 'reading'}:decision-signal-registry",
    )
    decision_result = build_decision_result(
        reading_id=reading_id,
        active_stage_id=active_stage_id,
        diagnosis=diagnosis,
        claim_scores=claim_scores,
        central_feedback_overlay=central_feedback_overlay,
        signal_registry=decision_signal_registry.model_dump(mode="json"),
        candidate_builder_mode="compatibility",
    )
    decision_question_recommendations = _decision_question_recommendations(decision_result)
    dialogue_recommendations = _merge_question_recommendations(
        decision_question_recommendations,
        recommendations,
    )
    final_synthesis = build_final_synthesis(
        diagnosis=diagnosis,
        claim_scores=claim_scores,
        practical_reading_context=practical_reading_context or {},
        feedback_weight_update=feedback_weight_update,
        central_feedback_overlay=central_feedback_overlay,
        synthesis_policy=_central_brain_synthesis_policy(question_policy or {}),
        decision_result=decision_result,
    )
    dialogue_plan = build_dialogue_plan(
        claim_scores=claim_scores,
        recommendations=dialogue_recommendations,
        question_dialogue_graph=question_dialogue_graph,
        interaction_state=interaction_state,
        central_feedback_overlay=central_feedback_overlay,
    )
    next_question = dialogue_plan.get("current_question", {})
    next_question = next_question if isinstance(next_question, dict) else {}
    next_action = dialogue_plan.get("next_action", {})
    next_action = next_action if isinstance(next_action, dict) else {}
    stage_opportunities = dialogue_plan.get("stage_question_opportunities", [])
    stage_opportunities = stage_opportunities if isinstance(stage_opportunities, list) else []
    current_turn_seed = dialogue_plan.get("current_turn_seed", {})
    current_turn_seed = current_turn_seed if isinstance(current_turn_seed, dict) else {}
    belief_state = _build_belief_state(
        reading_id=reading_id,
        active_stage_id=active_stage_id,
        evidence_graph_snapshot=evidence_graph_snapshot,
        claim_scores=claim_scores,
        feedback_signals=feedback_signals,
    )
    value_of_information_policy = _value_of_information_policy(
        claim_scores=claim_scores,
        recommendations=dialogue_recommendations,
        next_question=next_question,
        interaction_state=interaction_state,
        dialogue_plan=dialogue_plan,
    )
    brain_decision_trace = _build_brain_decision_trace(
        reading_id=reading_id,
        active_stage_id=active_stage_id,
        belief_state=belief_state,
        claim_scores=claim_scores,
        recommendations=dialogue_recommendations,
        next_question=next_question,
        next_action=next_action,
        value_of_information_policy=value_of_information_policy,
    )
    brain_training_example = _build_brain_training_example(
        reading_id=reading_id,
        active_stage_id=active_stage_id,
        evidence_graph_snapshot=evidence_graph_snapshot,
        claim_scores=claim_scores,
        brain_decision_trace=brain_decision_trace,
        question_outcomes=outcomes,
        value_of_information_policy=value_of_information_policy,
    )
    dialogue_training_trace = build_dialogue_training_trace(
        dialogue_plan=dialogue_plan,
        feedback_weight_update=feedback_weight_update,
        question_outcomes=outcomes,
    )
    return {
        "version": CENTRAL_READING_STATE_VERSION,
        "engine_version": CENTRAL_READING_ENGINE_VERSION,
        "dialogue_planner_version": DIALOGUE_PLANNER_VERSION,
        "feedback_weight_updater_version": FEEDBACK_WEIGHT_UPDATER_VERSION,
        "central_feedback_overlay_version": CENTRAL_FEEDBACK_OVERLAY_VERSION,
        "decision_engine_version": DECISION_ENGINE_VERSION,
        "final_synthesis_engine_version": FINAL_SYNTHESIS_ENGINE_VERSION,
        "semantic_ontology_version": BAZI_SEMANTIC_ONTOLOGY_VERSION,
        "reading_id": reading_id,
        "role_key": role_key,
        "active_stage_id": active_stage_id,
        "dialogue_decision_owner": "dialogue_brain",
        "customer_decision_field": CUSTOMER_DECISION_FIELD,
        "legacy_customer_decision_field": LEGACY_CUSTOMER_DECISION_FIELD,
        "surface_decision_fields": SURFACE_DECISION_FIELDS,
        "legacy_customer_decision_field_status": "diagnostic_compatibility_only",
        "candidate_sources": ["diagnosis_graph", "signal_registry", "question_recommender", "question_dialogue_graph"],
        "evidence_graph_snapshot": evidence_graph_snapshot.model_dump(mode="json"),
        "graph_detail_status": "ready" if graph_claim_metrics else "graph_detail_missing",
        "graph_claim_metric_count": len(graph_claim_metrics),
        "candidate_claim_count": len(claim_scores),
        "top_claim_ids": [str(row.get("claim_id") or "") for row in claim_scores[:8]],
        "blocked_claim_ids": [
            str(row.get("claim_id") or "")
            for row in claim_scores
            if row.get("blocked") is True
        ][:8],
        "needs_question_claim_ids": [
            str(row.get("claim_id") or "")
            for row in claim_scores
            if row.get("requires_question") is True
        ][:8],
        "claim_scores": claim_scores[:18],
        "decision_signal_registry": _decision_signal_registry_projection(decision_signal_registry.model_dump(mode="json")),
        "candidate_builder_summary": decision_result.get("candidate_builder_summary", {}),
        "conflict_resolver_summary": decision_result.get("conflict_resolver_summary", {}),
        "conflict_resolver_audit": decision_result.get("conflict_resolver_audit", []),
        "decision_input_bundle": decision_result.get("decision_input_bundle", {}),
        "decision_verdicts": decision_result.get("verdicts", []),
        "decision_result": decision_result,
        "decision_feedback_recalculation_summary": decision_result.get("feedback_recalculation_summary", {}),
        "decision_question_recommendations": decision_question_recommendations,
        "belief_state": belief_state.model_dump(mode="json"),
        "value_of_information_policy": value_of_information_policy,
        "brain_decision_trace": brain_decision_trace.model_dump(mode="json"),
        "brain_training_example": brain_training_example.model_dump(mode="json"),
        "feedback_weight_update": feedback_weight_update,
        "central_feedback_overlay": central_feedback_overlay,
        "semantic_ontology": _semantic_ontology_summary(),
        "final_synthesis": final_synthesis,
        "central_brain_synthesis_policy": _central_brain_synthesis_policy(question_policy or {}),
        "dialogue_plan": dialogue_plan,
        "dialogue_training_trace": dialogue_training_trace,
        "next_action": next_action,
        "next_question": next_question,
        "stage_question_opportunities": stage_opportunities,
        "current_turn_seed": current_turn_seed,
        "synthesis_inputs": _synthesis_inputs(
            diagnosis=diagnosis,
            practical_reading_context=practical_reading_context or {},
            model_signal_summary=model_signal_summary or {},
            ranked_decisions=ranked_decisions or {},
        ),
        "training_signal": {
            "version": "v30.training_signal.central_reading_state.v1",
            "trainable": True,
            "targets": [
                "claim_score_weights",
                "next_action_policy",
                "stage_question_policy",
                "dialogue_turn_policy",
                "dialogue_action_policy",
                "question_selection_policy",
                "feedback_alignment_weight",
                "central_feedback_overlay_weight",
                "claim_selection_for_final_synthesis",
                "advice_actionability_weight",
                "path_and_portrait_alignment",
                "graph_claim_score_weight",
                "graph_counterevidence_weight",
                "semantic_driver_claim_weight",
                "macro_domain_question_slot_weight",
                "claim_posterior_delta_weight",
                "value_of_information_policy",
                "brain_decision_trace_quality",
                "decision_candidate_weight",
                "decision_assertion_level_threshold",
                "decision_conflict_resolution_policy",
                "decision_feedback_recalculation_quality",
            ],
            "blocked_targets": [
                "chart_facts",
                "calendar_conversion",
                "pillar_calculation",
                "unconfirmed_hidden_factor_facts",
            ],
        },
        "boundary": "central_reading_state_selects_claims_questions_and_actions_without_mutating_chart_facts",
}

def _semantic_ontology_summary() -> dict[str, object]:
    ontology = get_bazi_semantic_ontology()
    ten_gods = ontology.get("ten_gods", {})
    macro_domains = ontology.get("macro_domains", {})
    return {
        "version": ontology.get("version", ""),
        "ten_god_count": len(ten_gods) if isinstance(ten_gods, dict) else 0,
        "macro_domain_count": len(macro_domains) if isinstance(macro_domains, dict) else 0,
        "macro_domains": list(macro_domains.keys()) if isinstance(macro_domains, dict) else [],
        "trainable_slots": ontology.get("trainable_slots", []),
        "boundary": "central_state_references_semantic_ontology_without_exposing_full_internal_table",
    }


def _decision_question_recommendations(decision_result: dict[str, object]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for verdict in _list(decision_result.get("verdicts")):
        if not isinstance(verdict, dict):
            continue
        verdict_id = str(verdict.get("verdict_id") or "")
        domain = str(verdict.get("domain") or "overview")
        confidence = _float(verdict.get("confidence"), 0.0)
        assertion_level = str(verdict.get("assertion_level") or "")
        slots = _list(verdict.get("next_question_slots"))
        for index, slot_raw in enumerate(slots):
            slot = _dict(slot_raw)
            question = str(slot.get("question") or "")
            if not question:
                continue
            slot_domain = str(slot.get("domain") or domain)
            question_id = f"decision-slot:{verdict_id or domain}:{index + 1}"
            score = min(
                0.94,
                max(
                    0.42,
                    (1.0 - confidence) * 0.45
                    + (0.28 if assertion_level in {"mixed", "weak_candidate", "blocked"} else 0.08)
                    + 0.36,
                ),
            )
            rows.append(
                {
                    "question_id": question_id,
                    "intent_id": f"decision_slot:{slot_domain}",
                    "question": question,
                    "title": question,
                    "topic": slot_domain,
                    "stage": "decision_verdict_calibration",
                    "score": round(score, 3),
                    "answer_mode": "single_choice",
                    "answer_constraints": {
                        "options": ["更符合", "不符合", "暂不确定"],
                        "allow_free_text": False,
                    },
                    "expected_information_gain": {
                        "score": round(score, 3),
                        "primary_gain": "reduce_decision_verdict_branch_uncertainty",
                    },
                    "candidate_source": "decision_engine_next_question_slot",
                    "decision_verdict_id": verdict_id,
                    "target_claim_ids": [str(verdict.get("primary_branch_id") or "")],
                    "semantic_projection": {
                        "version": "v30.decision_slot_semantic_projection.v1",
                        "macro_domain": slot_domain,
                        "assertion_level": assertion_level,
                        "source": "decision_engine_verdict_next_question_slot",
                    },
                    "boundary": "decision_question_recommendation_comes_from_verdict_slot_not_ghost_dialogue",
                }
            )
    return rows[:6]


def _merge_question_recommendations(
    decision_recommendations: list[dict[str, object]],
    recommendations: list[dict[str, object]],
) -> list[dict[str, object]]:
    if recommendations:
        return recommendations
    rows: list[dict[str, object]] = []
    seen: set[str] = set()
    for row in [*decision_recommendations, *recommendations]:
        if not isinstance(row, dict):
            continue
        question_id = str(row.get("question_id") or "")
        if not question_id or question_id in seen:
            continue
        seen.add(question_id)
        rows.append(row)
    return rows


def _central_brain_synthesis_policy(question_policy: dict[str, object]) -> dict[str, object]:
    weights = question_policy.get("weights")
    if not isinstance(weights, dict):
        return {}
    policy = weights.get("central_brain_synthesis_policy")
    if not isinstance(policy, dict):
        return {}
    if policy.get("can_tune_chart_facts") is True:
        return {}
    return policy


def _score_claim(
    claim: dict[str, object],
    *,
    paths: dict[str, dict[str, object]],
    portraits: dict[str, dict[str, object]],
    question_outcomes: list[dict[str, object]],
    feedback_signal: dict[str, object],
    practical_reading_context: dict[str, object],
    ranked_decisions: dict[str, object],
    graph_metrics: dict[str, object],
    central_feedback_overlay: dict[str, object],
) -> dict[str, object]:
    confidence = _band_score(str(claim.get("confidence_band") or "medium"))
    evidence_ids = _list(claim.get("evidence_ids"))
    rule_ids = _list(claim.get("rule_ids"))
    path_ids = [str(row) for row in _list(claim.get("path_ids"))]
    portrait_ids = [str(row) for row in _list(claim.get("portrait_ids"))]
    path_score = max([_float(paths.get(path_id, {}).get("score"), 0.0) for path_id in path_ids] or [0.0])
    portrait_score = max([_band_score(str(portraits.get(portrait_id, {}).get("confidence_band") or "low")) for portrait_id in portrait_ids] or [0.0])
    support_strength = min(1.0, confidence + len(evidence_ids) * 0.035 + len(rule_ids) * 0.045)
    graph_support = _float(graph_metrics.get("support_weight"), 0.0) if isinstance(graph_metrics, dict) else 0.0
    graph_prior = _float(graph_metrics.get("top_claim_prior"), 0.0) if isinstance(graph_metrics, dict) else 0.0
    support_strength = min(1.0, support_strength + graph_support * 0.10 + graph_prior * 0.04)
    evidence_diversity = _diversity_score(
        evidence=bool(evidence_ids),
        rule=bool(rule_ids),
        path=bool(path_ids),
        portrait=bool(portrait_ids),
        graph=bool(graph_metrics),
    )
    graph_path_coherence = _float(graph_metrics.get("path_coherence"), 0.0) if isinstance(graph_metrics, dict) else 0.0
    path_coherence = max(path_score, portrait_score * 0.75, graph_path_coherence)
    timing_activation = _timing_activation_score(claim, paths)
    feedback_alignment = _feedback_alignment_score(claim, question_outcomes, feedback_signal)
    feedback_contradiction = _feedback_contradiction_score(feedback_signal)
    actionability = _actionability_score(claim, practical_reading_context, ranked_decisions)
    counter_evidence = max(_counter_evidence_score(claim), _float(graph_metrics.get("counter_weight"), 0.0) if isinstance(graph_metrics, dict) else 0.0)
    missing_context_penalty = max(
        _missing_context_penalty(claim),
        min(1.0, _float(graph_metrics.get("requires_weight"), 0.0) * 0.65) if isinstance(graph_metrics, dict) else 0.0,
    )
    overclaim_risk = _overclaim_risk(claim)
    overlay_adjustment = overlay_adjustment_for_claim(claim, central_feedback_overlay)
    overlay_delta = _float(overlay_adjustment.get("score_delta"), 0.0)
    raw_score = (
        support_strength * 0.28
        + evidence_diversity * 0.18
        + path_coherence * 0.18
        + timing_activation * 0.12
        + feedback_alignment * 0.16
        + actionability * 0.08
        - feedback_contradiction * 0.16
        - counter_evidence * 0.18
        - missing_context_penalty * 0.14
        - overclaim_risk * 0.20
        + overlay_delta
    )
    score = round(max(0.0, min(1.0, raw_score)), 3)
    requires_question = bool(claim.get("needs_user_calibration")) or (
        0.42 <= score < 0.72 and str(claim.get("domain") or "") not in {"overview", "structure"}
    )
    row = {
        "version": "v30.central_claim_score.v1",
        "claim_id": str(claim.get("claim_id") or ""),
        "domain": str(claim.get("domain") or "overview"),
        "claim_level": str(claim.get("claim_level") or ""),
        "score": score,
        "confidence_band": _score_band(score),
        "requires_question": requires_question,
        "blocked": bool(claim.get("blocked_overclaim")),
        "components": {
            "support_strength": round(support_strength, 3),
            "evidence_diversity": round(evidence_diversity, 3),
            "path_coherence": round(path_coherence, 3),
            "timing_activation": round(timing_activation, 3),
            "feedback_alignment": round(feedback_alignment, 3),
            "feedback_contradiction": round(feedback_contradiction, 3),
            "actionability": round(actionability, 3),
            "counter_evidence": round(counter_evidence, 3),
            "missing_context_penalty": round(missing_context_penalty, 3),
            "overclaim_risk": round(overclaim_risk, 3),
            "graph_support": round(graph_support, 3),
            "graph_prior": round(graph_prior, 3),
            "graph_path_coherence": round(graph_path_coherence, 3),
            "central_feedback_overlay": round(overlay_delta, 3),
        },
        "central_feedback_adjustment": overlay_adjustment,
        "graph_metrics": _public_graph_metrics(graph_metrics if isinstance(graph_metrics, dict) else {}),
        "feedback_signal": _public_feedback_signal(feedback_signal),
        "semantic_projection": {},
        "training_scope": ["claim_score_weight", "question_policy"] if requires_question else ["claim_score_weight"],
        "boundary": "central_claim_score_ranks_existing_claim_without_generating_new_fact",
    }
    row["semantic_projection"] = semantic_projection_for_claim(row)
    if requires_question:
        row["training_scope"] = [*row["training_scope"], str(row["semantic_projection"].get("weight_slot") or "")]
    return row


def _evidence_graph_snapshot(
    *,
    reading_id: str,
    graph: dict[str, object],
    graph_summary: dict[str, object],
) -> BrainEvidenceGraphSnapshot:
    nodes = _list(graph.get("nodes"))
    edges = _list(graph.get("edges"))
    if nodes or edges:
        return BrainEvidenceGraphSnapshot(
            graph_id=str(graph.get("graph_id") or ""),
            reading_id=str(graph.get("reading_id") or reading_id),
            node_count=len(nodes),
            edge_count=len(edges),
            node_kinds=_sorted_unique(str(row.get("node_kind") or "") for row in nodes if isinstance(row, dict)),
            edge_kinds=_sorted_unique(str(row.get("edge_kind") or "") for row in edges if isinstance(row, dict)),
            top_claim_ids=[str(row) for row in _list(graph.get("top_claim_ids"))],
            top_path_ids=[str(row) for row in _list(graph.get("top_path_ids"))],
            graph_missing=False,
        )
    return BrainEvidenceGraphSnapshot(
        graph_id=str(graph_summary.get("graph_id") or ""),
        reading_id=str(graph_summary.get("reading_id") or reading_id),
        node_count=int(_float(graph_summary.get("node_count"), 0.0)),
        edge_count=int(_float(graph_summary.get("edge_count"), 0.0)),
        node_kinds=list((_dict(graph_summary.get("node_counts"))).keys()),
        edge_kinds=list((_dict(graph_summary.get("edge_counts"))).keys()),
        top_claim_ids=[str(row) for row in _list(graph_summary.get("top_claim_ids"))],
        top_path_ids=[str(row) for row in _list(graph_summary.get("top_path_ids"))],
        graph_missing=True,
    )


def _graph_claim_metrics(graph: dict[str, object]) -> dict[str, dict[str, object]]:
    nodes = [row for row in _list(graph.get("nodes")) if isinstance(row, dict)]
    edges = [row for row in _list(graph.get("edges")) if isinstance(row, dict)]
    if not nodes or not edges:
        return {}
    node_by_id = {str(row.get("node_id") or ""): row for row in nodes}
    claim_node_by_id = {
        str(row.get("node_id") or ""): str(row.get("ref_id") or "")
        for row in nodes
        if str(row.get("node_kind") or "") == "claim"
    }
    metrics: dict[str, dict[str, object]] = {}
    top_claim_ids = {str(row) for row in _list(graph.get("top_claim_ids"))}
    for node_id, claim_id in claim_node_by_id.items():
        incoming = [edge for edge in edges if str(edge.get("target_node_id") or "") == node_id]
        source_kinds = _sorted_unique(
            str(node_by_id.get(str(edge.get("source_node_id") or ""), {}).get("node_kind") or "")
            for edge in incoming
            if str(edge.get("source_node_id") or "") != node_id
        )
        support_edges = [edge for edge in incoming if str(edge.get("edge_kind") or "") in {"supports", "explains", "activates"}]
        counter_edges = [edge for edge in incoming if str(edge.get("edge_kind") or "") in {"weakens", "blocks"}]
        requires_edges = [edge for edge in incoming if str(edge.get("edge_kind") or "") in {"requires", "asks_followup"}]
        support_weight = _avg_weight(support_edges)
        counter_weight = _avg_weight(counter_edges)
        requires_weight = _avg_weight(requires_edges)
        metrics[claim_id] = {
            "version": "v30.central_brain.graph_claim_metrics.v1",
            "claim_node_id": node_id,
            "incoming_edge_count": len(incoming),
            "support_edge_count": len(support_edges),
            "counter_edge_count": len(counter_edges),
            "requires_edge_count": len(requires_edges),
            "support_weight": support_weight,
            "counter_weight": counter_weight,
            "requires_weight": requires_weight,
            "source_kinds": source_kinds,
            "path_coherence": min(1.0, support_weight + len(source_kinds) * 0.04),
            "top_claim_prior": 1.0 if claim_id in top_claim_ids else 0.0,
            "boundary": "graph_claim_metrics_score_existing_graph_edges_without_new_facts",
        }
    return metrics


def _public_graph_metrics(metrics: dict[str, object]) -> dict[str, object]:
    if not metrics:
        return {}
    return {
        "version": str(metrics.get("version") or ""),
        "incoming_edge_count": int(_float(metrics.get("incoming_edge_count"), 0.0)),
        "support_edge_count": int(_float(metrics.get("support_edge_count"), 0.0)),
        "counter_edge_count": int(_float(metrics.get("counter_edge_count"), 0.0)),
        "requires_edge_count": int(_float(metrics.get("requires_edge_count"), 0.0)),
        "support_weight": round(_float(metrics.get("support_weight"), 0.0), 3),
        "counter_weight": round(_float(metrics.get("counter_weight"), 0.0), 3),
        "requires_weight": round(_float(metrics.get("requires_weight"), 0.0), 3),
        "source_kinds": [str(row) for row in _list(metrics.get("source_kinds"))],
        "path_coherence": round(_float(metrics.get("path_coherence"), 0.0), 3),
        "top_claim_prior": round(_float(metrics.get("top_claim_prior"), 0.0), 3),
        "boundary": "public_graph_metrics_explain_claim_score_without_exposing_full_graph",
    }


def _build_belief_state(
    *,
    reading_id: str,
    active_stage_id: str,
    evidence_graph_snapshot: BrainEvidenceGraphSnapshot,
    claim_scores: list[dict[str, object]],
    feedback_signals: dict[str, dict[str, object]],
) -> BrainBeliefState:
    top_claims: list[BrainClaimBelief] = []
    weak_claims: list[BrainClaimBelief] = []
    blocked_claims: list[BrainClaimBelief] = []
    uncertainties: list[BrainUncertaintySlot] = []
    missing_context: list[str] = []

    for row in claim_scores[:18]:
        if not isinstance(row, dict):
            continue
        claim_id = str(row.get("claim_id") or "")
        if not claim_id:
            continue
        score = _float(row.get("score"), 0.0)
        graph_metrics = _dict(row.get("graph_metrics"))
        feedback_signal = feedback_signals.get(claim_id, {})
        net_alignment = _float(feedback_signal.get("net_alignment"), 0.0) if isinstance(feedback_signal, dict) else 0.0
        support_nodes = [str(row) for row in _list(graph_metrics.get("supporting_node_ids"))]
        weakening_nodes = [str(row) for row in _list(graph_metrics.get("weakening_node_ids"))]
        if not support_nodes and graph_metrics:
            support_nodes = [str(graph_metrics.get("claim_node_id") or claim_id)]
        claim_missing = []
        if row.get("requires_question") is True:
            claim_missing.append(f"needs_user_calibration:{claim_id}")
            missing_context.append(f"needs_user_calibration:{claim_id}")
        belief = BrainClaimBelief(
            claim_id=claim_id,
            domain=str(row.get("domain") or "overview"),
            status=_claim_belief_status(row),
            confidence=score,
            actionability=_float(_dict(row.get("components")).get("actionability"), 0.0),
            uncertainty=round(max(0.0, min(1.0, 1.0 - score + len(claim_missing) * 0.08)), 3),
            supporting_node_ids=support_nodes or [claim_id],
            weakening_node_ids=weakening_nodes,
            missing_context=claim_missing,
            overclaim_risk=_float(_dict(row.get("components")).get("overclaim_risk"), 0.0),
            requires_question=bool(row.get("requires_question")),
            posterior_delta=round(max(-1.0, min(1.0, net_alignment)), 3),
        )
        if belief.status == "blocked":
            blocked_claims.append(belief)
        elif belief.status == "weak":
            weak_claims.append(belief)
        else:
            top_claims.append(belief)
        if row.get("requires_question") is True:
            uncertainty = min(
                1.0,
                _float(_dict(row.get("components")).get("missing_context_penalty"), 0.0)
                + _float(_dict(row.get("components")).get("counter_evidence"), 0.0) * 0.35
                + max(0.0, 0.72 - score) * 0.45,
            )
            uncertainties.append(
                BrainUncertaintySlot(
                    uncertainty_id=f"uncertainty:{claim_id}",
                    domain=str(row.get("domain") or "overview"),
                    target_claim_ids=[claim_id],
                    missing_context=claim_missing,
                    information_gain=round(uncertainty, 3),
                    user_cost=0.34 if str(row.get("domain") or "") == "hidden_factor" else 0.22,
                    hidden_attribute_gain=0.55 if str(row.get("domain") or "") == "hidden_factor" else 0.0,
                )
            )

    readiness = _final_decision_readiness(top_claims, uncertainties)
    return BrainBeliefState(
        reading_id=reading_id,
        active_stage_id=active_stage_id,
        user_goal=_infer_user_goal(claim_scores),
        evidence_graph=evidence_graph_snapshot,
        top_claims=top_claims[:8],
        weak_claims=weak_claims[:8],
        blocked_claims=blocked_claims[:8],
        uncertainty_map=uncertainties[:8],
        known_context=["diagnosis_claims_ranked", "evidence_graph_snapshot_ready"],
        missing_context=_sorted_unique(missing_context),
        final_decision_readiness=readiness,
    )


def _value_of_information_policy(
    *,
    claim_scores: list[dict[str, object]],
    recommendations: list[dict[str, object]],
    next_question: dict[str, object],
    interaction_state: dict[str, object],
    dialogue_plan: dict[str, object],
) -> dict[str, object]:
    top = claim_scores[0] if claim_scores else {}
    answered = _list(interaction_state.get("answered_question_ids"))
    question_score = _float(next_question.get("score"), 0.0)
    top_score = _float(top.get("score"), 0.0)
    requires_question_count = sum(1 for row in claim_scores if isinstance(row, dict) and row.get("requires_question") is True)
    user_cost = 0.34 if str(next_question.get("topic") or "") == "hidden_factor" else 0.22 if next_question else 0.0
    overask_penalty = min(0.62, len(answered) * 0.12)
    information_gain = min(1.0, question_score * 0.62 + requires_question_count * 0.06 + max(0.0, 0.72 - top_score) * 0.24)
    claim_impact = min(1.0, max(0.0, 0.82 - top_score) + requires_question_count * 0.05)
    hidden_attribute_gain = 0.55 if str(next_question.get("topic") or "") == "hidden_factor" else 0.0
    training_value = 0.18 if requires_question_count else 0.08
    question_value = (
        information_gain * 0.32
        + claim_impact * 0.22
        + hidden_attribute_gain * 0.14
        + training_value * 0.08
        - user_cost * 0.12
        - overask_penalty * 0.12
    )
    question_value = round(max(0.0, min(1.0, question_value)), 3)
    should_ask = bool(next_question) and (
        (question_value >= 0.45 and requires_question_count > 0)
        or (question_value >= 0.18 and (bool(top.get("requires_question")) or top_score < 0.72 or hidden_attribute_gain > 0))
    )
    selected_action = str(_dict(dialogue_plan.get("next_action")).get("action") or "")
    if should_ask:
        selected_action = "ask_stage_question"
    elif top_score >= 0.72:
        selected_action = "conclude_stage"
    elif not claim_scores:
        selected_action = "continue_next_stage"
    return {
        "version": "v30.central_brain.value_of_information_policy.v1",
        "selected_action": selected_action,
        "question_id": str(next_question.get("question_id") or ""),
        "question_value": question_value,
        "information_gain": round(information_gain, 3),
        "claim_impact": round(claim_impact, 3),
        "hidden_attribute_gain": round(hidden_attribute_gain, 3),
        "training_value": round(training_value, 3),
        "user_cost": round(user_cost, 3),
        "overask_penalty": round(overask_penalty, 3),
        "top_claim_id": str(top.get("claim_id") or ""),
        "top_claim_score": round(top_score, 3),
        "candidate_question_count": len(recommendations),
        "requires_question_count": requires_question_count,
        "reason": "ask_only_when_information_gain_exceeds_user_cost" if should_ask else "conclude_or_continue_when_question_value_is_low",
        "boundary": "value_of_information_policy_selects_dialogue_action_without_mutating_chart_facts",
    }


def _build_brain_decision_trace(
    *,
    reading_id: str,
    active_stage_id: str,
    belief_state: BrainBeliefState,
    claim_scores: list[dict[str, object]],
    recommendations: list[dict[str, object]],
    next_question: dict[str, object],
    next_action: dict[str, object],
    value_of_information_policy: dict[str, object],
) -> BrainDecisionTrace:
    policy_action = str(value_of_information_policy.get("selected_action") or "")
    action = policy_action or str(next_action.get("action") or "continue_next_stage")
    if action not in {
        "conclude_stage",
        "ask_stage_question",
        "ask_hidden_attribute_probe",
        "request_timing_context",
        "continue_next_stage",
        "final_synthesis",
        "blocked",
    }:
        action = "continue_next_stage"
    top_claim_ids = [str(row.get("claim_id") or "") for row in claim_scores[:3] if isinstance(row, dict) and str(row.get("claim_id") or "")]
    question_candidates = _brain_question_candidates(recommendations, claim_scores)
    selected_question_id = str(next_question.get("question_id") or "") or None
    if action in {"ask_stage_question", "ask_hidden_attribute_probe"} and not selected_question_id:
        action = "continue_next_stage"
    if action in {"conclude_stage", "final_synthesis"} and not top_claim_ids:
        action = "continue_next_stage"
    reason_codes = [
        str(next_action.get("reason") or "central_brain_v2_policy"),
        str(value_of_information_policy.get("reason") or ""),
    ]
    if belief_state.uncertainty_map:
        reason_codes.append("belief_state_has_uncertainty_slots")
    if belief_state.evidence_graph.graph_missing:
        reason_codes.append("evidence_graph_detail_missing")
    else:
        reason_codes.append("evidence_graph_detail_ready")
    return BrainDecisionTrace(
        decision_id=f"{reading_id}:{active_stage_id or 'reading'}:brain-decision",
        reading_id=reading_id,
        stage_id=active_stage_id,
        selected_action=action,  # type: ignore[arg-type]
        selected_claim_ids=top_claim_ids if action in {"conclude_stage", "final_synthesis", "ask_stage_question", "ask_hidden_attribute_probe"} else [],
        rejected_claim_ids=[str(row.get("claim_id") or "") for row in claim_scores[8:12] if isinstance(row, dict) and str(row.get("claim_id") or "")],
        selected_question_id=selected_question_id if action in {"ask_stage_question", "ask_hidden_attribute_probe"} else None,
        reason_codes=[row for row in reason_codes if row],
        feature_vector={
            "top_claim_score": _float(value_of_information_policy.get("top_claim_score"), 0.0),
            "question_value": _float(value_of_information_policy.get("question_value"), 0.0),
            "information_gain": _float(value_of_information_policy.get("information_gain"), 0.0),
            "user_cost": _float(value_of_information_policy.get("user_cost"), 0.0),
            "overask_penalty": _float(value_of_information_policy.get("overask_penalty"), 0.0),
            "final_decision_readiness": belief_state.final_decision_readiness,
        },
        belief_state=belief_state,
        question_candidates=question_candidates,
        training_targets=["claim_score_weights", "claim_posterior_delta_weight", "value_of_information_policy"],
    )


def _build_brain_training_example(
    *,
    reading_id: str,
    active_stage_id: str,
    evidence_graph_snapshot: BrainEvidenceGraphSnapshot,
    claim_scores: list[dict[str, object]],
    brain_decision_trace: BrainDecisionTrace,
    question_outcomes: list[dict[str, object]],
    value_of_information_policy: dict[str, object],
) -> BrainTrainingExample:
    latest_outcome = question_outcomes[-1] if question_outcomes and isinstance(question_outcomes[-1], dict) else {}
    claim_delta = {
        str(row.get("claim_id") or ""): _float(_dict(row.get("feedback_signal")).get("net_alignment"), 0.0)
        for row in claim_scores
        if isinstance(row, dict) and _float(_dict(row.get("feedback_signal")).get("net_alignment"), 0.0) != 0.0
    }
    outcome_payload = dict(latest_outcome) if isinstance(latest_outcome, dict) else {}
    outcome_payload["status"] = _training_outcome_status(latest_outcome)
    outcome_payload["claim_delta"] = claim_delta
    outcome_payload["followup_useful"] = None if not latest_outcome else bool(claim_delta)
    outcome_payload["contradiction_found"] = any(value < 0 for value in claim_delta.values())
    return build_brain_training_example(
        example_id=f"{reading_id}:{active_stage_id or 'reading'}:brain-training-example",
        reading_id=reading_id,
        source="runtime_trace",
        decision=brain_decision_trace,
        evidence_graph_snapshot=evidence_graph_snapshot,
        question_outcome=outcome_payload,
        labels={
            "question_information_gain": _float(value_of_information_policy.get("information_gain"), 0.0),
            "advice_actionability": max([
                _float(_dict(row.get("components")).get("actionability"), 0.0)
                for row in claim_scores
                if isinstance(row, dict)
            ] or [0.0]),
            "user_cost": _float(value_of_information_policy.get("user_cost"), 0.0),
            "overask": _float(value_of_information_policy.get("overask_penalty"), 0.0) >= 0.5,
        },
        trainable_targets=[
            "claim_score_weights",
            "claim_posterior_delta_weight",
            "value_of_information_policy",
            "question_selection_policy",
            "final_synthesis_ranking",
        ],
    )


def _brain_question_candidates(
    recommendations: list[dict[str, object]],
    claim_scores: list[dict[str, object]],
) -> list[BrainQuestionCandidate]:
    candidates: list[BrainQuestionCandidate] = []
    for row in recommendations[:8]:
        if not isinstance(row, dict):
            continue
        question_id = str(row.get("question_id") or "")
        if not question_id:
            continue
        topic = str(row.get("topic") or "overview")
        target_claim_ids = [
            str(claim.get("claim_id") or "")
            for claim in claim_scores
            if isinstance(claim, dict)
            and str(claim.get("domain") or "") in {topic, "hidden_factor", "useful_god"}
            and str(claim.get("claim_id") or "")
        ][:4]
        if not target_claim_ids and claim_scores:
            target_claim_ids = [str(claim_scores[0].get("claim_id") or "")]
        candidates.append(
            BrainQuestionCandidate(
                question_id=question_id,
                prompt=str(row.get("question") or row.get("title") or row.get("label") or question_id),
                domain=topic,
                answer_shape=_answer_shape(row),
                target_claim_ids=target_claim_ids,
                target_uncertainty_ids=[f"uncertainty:{claim_id}" for claim_id in target_claim_ids],
                option_labels=_option_labels(row),
                information_gain=_float(_dict(row.get("expected_information_gain")).get("score"), _float(row.get("score"), 0.0)),
                user_cost=0.34 if topic == "hidden_factor" else 0.22,
                overask_penalty=0.0,
                hidden_attribute_probe=topic == "hidden_factor",
            )
        )
    return candidates


def _claim_belief_status(row: dict[str, object]) -> str:
    if row.get("blocked") is True:
        return "blocked"
    score = _float(row.get("score"), 0.0)
    if score >= 0.45:
        return "selected"
    return "weak"


def _final_decision_readiness(top_claims: list[BrainClaimBelief], uncertainties: list[BrainUncertaintySlot]) -> float:
    if not top_claims:
        return 0.0
    top_confidence = max(claim.confidence for claim in top_claims)
    uncertainty_penalty = min(0.45, len(uncertainties) * 0.06)
    return round(max(0.0, min(1.0, top_confidence - uncertainty_penalty)), 3)


def _infer_user_goal(claim_scores: list[dict[str, object]]) -> str:
    for row in claim_scores:
        if isinstance(row, dict):
            domain = str(row.get("domain") or "")
            if domain and domain not in {"overview", "structure"}:
                return domain
    return "overview"


def _answer_shape(row: dict[str, object]) -> str:
    mode = str(row.get("answer_mode") or "")
    if mode in {"single_choice", "choice", "multi_choice"}:
        return "choice"
    if mode in {"number", "year"}:
        return mode
    if mode in {"short_text", "text"}:
        return "short_text"
    constraints = row.get("answer_constraints")
    if isinstance(constraints, dict) and constraints.get("type") in {"number", "year"}:
        return str(constraints.get("type"))
    return "choice"


def _training_outcome_status(outcome: dict[str, object]) -> str:
    if not outcome:
        return "pending"
    status = str(outcome.get("outcome_status") or "answered")
    if status in {"skipped", "unclear"}:
        return "skipped"
    if status == "denied":
        return "contradicted"
    if status == "confirmed":
        return "confirmed"
    if status == "blocked":
        return "blocked"
    return "answered"


def _option_labels(row: dict[str, object]) -> list[str]:
    options = row.get("options") or row.get("answer_options")
    if not isinstance(options, list):
        constraints = row.get("answer_constraints")
        options = constraints.get("options") if isinstance(constraints, dict) else []
    labels: list[str] = []
    for option in options if isinstance(options, list) else []:
        if isinstance(option, dict):
            labels.append(str(option.get("label") or option.get("value") or ""))
        else:
            labels.append(str(option))
    return [label for label in labels if label][:6]

def _synthesis_inputs(
    *,
    diagnosis: dict[str, object],
    practical_reading_context: dict[str, object],
    model_signal_summary: dict[str, object],
    ranked_decisions: dict[str, object],
) -> dict[str, object]:
    summaries = diagnosis.get("summaries") if isinstance(diagnosis.get("summaries"), dict) else {}
    public_projection = diagnosis.get("public_projection") if isinstance(diagnosis.get("public_projection"), dict) else {}
    return {
        "version": "v30.central_synthesis_inputs.v1",
        "diagnosis_status": diagnosis.get("status") or "",
        "claim_summary": summaries.get("claims") if isinstance(summaries, dict) else {},
        "path_summary": summaries.get("paths") if isinstance(summaries, dict) else {},
        "diagnosis_overview": public_projection.get("diagnosis_overview") if isinstance(public_projection, dict) else "",
        "timing_status": _nested(practical_reading_context, "timing_summary", "status"),
        "model_signal_summary": model_signal_summary,
        "ranked_decision_status": ranked_decisions.get("status") or "",
        "boundary": "synthesis_inputs_feed_final_summary_without_new_facts",
    }


def _diversity_score(**flags: bool) -> float:
    return round(sum(1 for value in flags.values() if value) / max(1, len(flags)), 3)


def _timing_activation_score(claim: dict[str, object], paths: dict[str, dict[str, object]]) -> float:
    if str(claim.get("domain") or "") == "timing" or str(claim.get("claim_level") or "") == "timing":
        return 0.55
    path_ids = [str(row) for row in _list(claim.get("path_ids"))]
    for path_id in path_ids:
        trigger = paths.get(path_id, {}).get("timing_trigger")
        if isinstance(trigger, dict) and any(str(value) for value in trigger.values()):
            return 0.48
    return 0.0


def _feedback_alignment_score(
    claim: dict[str, object],
    question_outcomes: list[dict[str, object]],
    feedback_signal: dict[str, object],
) -> float:
    signal_score = _float(feedback_signal.get("support"), 0.0) if isinstance(feedback_signal, dict) else 0.0
    if signal_score:
        return min(1.0, signal_score)
    domain = str(claim.get("domain") or "")
    if not domain or not question_outcomes:
        return 0.0
    score = 0.0
    for row in question_outcomes:
        if not isinstance(row, dict):
            continue
        if str(row.get("topic") or "") == domain:
            score += 0.18
        selected = str(row.get("selected_option") or "")
        if domain and domain in selected:
            score += 0.08
    return min(1.0, score)


def _feedback_contradiction_score(feedback_signal: dict[str, object]) -> float:
    if not isinstance(feedback_signal, dict):
        return 0.0
    return min(1.0, _float(feedback_signal.get("contradiction"), 0.0))


def _public_feedback_signal(feedback_signal: dict[str, object]) -> dict[str, object]:
    if not isinstance(feedback_signal, dict) or not feedback_signal:
        return {}
    return {
        "version": str(feedback_signal.get("version") or ""),
        "support": _float(feedback_signal.get("support"), 0.0),
        "contradiction": _float(feedback_signal.get("contradiction"), 0.0),
        "net_alignment": _float(feedback_signal.get("net_alignment"), 0.0),
        "source_outcome_count": len(_list(feedback_signal.get("source_outcome_ids"))),
        "chart_fact_mutation_allowed": False,
        "boundary": "claim_score_feedback_signal_is_weight_update_not_chart_fact",
    }


def _decision_signal_registry_projection(registry: dict[str, object]) -> dict[str, object]:
    signals = _list(registry.get("signals"))
    source_type_counts: dict[str, int] = {}
    source_module_counts: dict[str, int] = {}
    for signal in signals:
        if not isinstance(signal, dict):
            continue
        source_type = str(signal.get("source_type") or "")
        source_module = str(signal.get("source_module") or "")
        if source_type:
            source_type_counts[source_type] = source_type_counts.get(source_type, 0) + 1
        if source_module:
            source_module_counts[source_module] = source_module_counts.get(source_module, 0) + 1
    return {
        "version": "v30.decision_signal_registry_projection.v1",
        "registry_id": str(registry.get("registry_id") or ""),
        "signal_count": len(signals),
        "source_type_counts": dict(sorted(source_type_counts.items())),
        "source_module_counts": dict(sorted(source_module_counts.items())),
        "validation_issue_count": len(_list(registry.get("validation_issues"))),
        "score_mutation_allowed": False,
        "boundary": "decision_signal_registry_projection_is_candidate_builder_context_not_final_verdict",
    }


def _actionability_score(
    claim: dict[str, object],
    practical_reading_context: dict[str, object],
    ranked_decisions: dict[str, object],
) -> float:
    domain = str(claim.get("domain") or "")
    score = 0.35 if domain in {"overview", "structure"} else 0.58
    domain_readings = practical_reading_context.get("domain_readings")
    if isinstance(domain_readings, dict) and domain in domain_readings:
        score += 0.22
    if ranked_decisions:
        score += 0.08
    if str(claim.get("claim_text") or ""):
        score += 0.08
    return min(1.0, score)


def _counter_evidence_score(claim: dict[str, object]) -> float:
    score = min(1.0, len(_list(claim.get("blocked_overclaim"))) * 0.24)
    if claim.get("needs_user_calibration"):
        score += 0.16
    return min(1.0, score)


def _missing_context_penalty(claim: dict[str, object]) -> float:
    if claim.get("needs_user_calibration"):
        return 0.45
    if str(claim.get("domain") or "") == "timing":
        return 0.32
    return 0.0


def _overclaim_risk(claim: dict[str, object]) -> float:
    risk = 0.0
    if _list(claim.get("blocked_overclaim")):
        risk += 0.42
    if str(claim.get("domain") or "") in {"health", "timing"}:
        risk += 0.18
    return min(1.0, risk)


def _band_score(value: str) -> float:
    return {"high": 0.78, "medium": 0.55, "low": 0.32}.get(value, 0.5)


def _score_band(score: float) -> str:
    if score >= 0.72:
        return "high"
    if score >= 0.45:
        return "medium"
    return "low"


def _nested(payload: dict[str, object], *keys: str) -> object:
    current: object = payload
    for key in keys:
        if not isinstance(current, dict):
            return ""
        current = current.get(key, "")
    return current


def _dict(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list(value: object) -> list[Any]:
    return value if isinstance(value, list) else []


def _float(value: object, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _avg_weight(edges: list[dict[str, object]]) -> float:
    if not edges:
        return 0.0
    return round(sum(_float(edge.get("weight"), 0.0) for edge in edges) / len(edges), 3)


def _sorted_unique(values: object) -> list[str]:
    return sorted({str(value) for value in values if str(value)})
