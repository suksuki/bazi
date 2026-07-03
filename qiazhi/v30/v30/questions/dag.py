from __future__ import annotations

from pydantic import Field

from v30.contracts import V30Model


class QuestionDialogueNode(V30Model):
    node_id: str
    question_id: str
    topic: str
    stage: str
    score: float
    reasons: list[str] = Field(default_factory=list)


class QuestionDialogueEdge(V30Model):
    edge_id: str
    source_question_id: str
    target_question_id: str
    relation: str
    weight: float
    reason: str


class QuestionDialogueGraph(V30Model):
    version: str = "v30.question_dialogue_graph.v1"
    graph_id: str
    nodes: list[QuestionDialogueNode]
    edges: list[QuestionDialogueEdge]
    next_question_id: str | None = None
    internal_next_question_id: str | None = None
    followup_reason: str = ""
    policy_notes: list[str] = Field(default_factory=list)
    decision_owner: str = "dialogue_brain"
    customer_decision_field: str = "reading_surface.conversation_surface"
    legacy_customer_decision_field: str = "reading_surface.current_dialogue_turn"
    surface_decision_fields: dict[str, str] = Field(
        default_factory=lambda: {
            "calibration": "reading_surface.calibration_surface",
            "conversation": "reading_surface.conversation_surface",
            "thinking": "reading_surface.thinking_surface",
        }
    )
    legacy_customer_decision_field_status: str = "diagnostic_compatibility_only"
    boundary: str = "question_dialogue_graph_is_memory_relation_graph_not_customer_decision_owner"


def build_question_dialogue_graph(
    *,
    reading_id: str,
    recommendations: list[dict[str, object]],
    hidden_factor_calibration: dict[str, object],
    hidden_factor_state: dict[str, object] | None = None,
    question_outcomes: list[dict[str, object]] | None = None,
) -> QuestionDialogueGraph:
    hidden_factor_state = hidden_factor_state or {}
    question_outcomes = question_outcomes or []
    nodes = [
        QuestionDialogueNode(
            node_id=f"{reading_id}:question-node:{row.get('question_id')}",
            question_id=str(row.get("question_id") or ""),
            topic=str(row.get("topic") or ""),
            stage=str(row.get("stage") or ""),
            score=float(row.get("score") or 0.0),
            reasons=[str(reason) for reason in row.get("reasons", [])],
        )
        for row in recommendations
    ]
    edges = _dialogue_edges(reading_id, nodes, hidden_factor_calibration, hidden_factor_state, question_outcomes)
    next_question_id = _next_question_id(nodes, question_outcomes)
    internal_next_question_id = _internal_next_question_id(nodes, question_outcomes) or next_question_id
    return QuestionDialogueGraph(
        graph_id=f"{reading_id}:question-dialogue-graph",
        nodes=nodes,
        edges=edges,
        next_question_id=next_question_id,
        internal_next_question_id=internal_next_question_id,
        followup_reason=_followup_reason(next_question_id, edges, question_outcomes),
        policy_notes=_policy_notes(nodes, hidden_factor_calibration, hidden_factor_state, question_outcomes),
    )


def _dialogue_edges(
    reading_id: str,
    nodes: list[QuestionDialogueNode],
    hidden_factor_calibration: dict[str, object],
    hidden_factor_state: dict[str, object],
    question_outcomes: list[dict[str, object]],
) -> list[QuestionDialogueEdge]:
    edges: list[QuestionDialogueEdge] = []
    by_topic = {node.topic: node for node in nodes}
    if "time_context" in by_topic and "hidden_factor" in by_topic:
        edges.append(
            _edge(
                reading_id,
                by_topic["time_context"],
                by_topic["hidden_factor"],
                "unlock_hidden_factor_dialogue",
                0.82,
                "time context should be clarified before hidden-factor amplifier calibration",
            )
        )
    if "time_context" in by_topic and "useful_god" in by_topic:
        edges.append(
            _edge(
                reading_id,
                by_topic["time_context"],
                by_topic["useful_god"],
                "unlock_candidate_review",
                0.78,
                "time context reduces overreach before useful-god candidate review",
            )
        )
    if "structure_dynamic" in by_topic and "useful_god" in by_topic:
        edges.append(
            _edge(
                reading_id,
                by_topic["structure_dynamic"],
                by_topic["useful_god"],
                "explain_before_candidate_review",
                0.66,
                "structure dynamic paths provide context for candidate review",
            )
        )
    if (
        hidden_factor_calibration.get("amplifier_candidate")
        or hidden_factor_state.get("amplifier_candidate")
    ) and "hidden_factor" in by_topic:
        hidden_node = by_topic["hidden_factor"]
        for node in nodes:
            if node.question_id != hidden_node.question_id:
                edges.append(
                    _edge(
                        reading_id,
                        hidden_node,
                        node,
                        "calibrated_hidden_factor_can_condition_followup",
                        0.58,
                        "feedback-calibrated or persisted hidden factor state can inform follow-up ordering without changing chart facts",
                    )
                )
    selected_topics = {_selected_topic(row) for row in question_outcomes if isinstance(row, dict)}
    selected_topics.discard("")
    for topic in selected_topics:
        if topic not in by_topic:
            continue
        for node in nodes:
            if node.topic != topic:
                continue
            edges.append(
                _edge(
                    reading_id,
                    by_topic[topic],
                    node,
                    "structured_option_selects_topic_focus",
                    0.62,
                    "structured user choice can prioritize the next same-topic question without changing chart facts",
                )
            )
    return edges


def _edge(
    reading_id: str,
    source: QuestionDialogueNode,
    target: QuestionDialogueNode,
    relation: str,
    weight: float,
    reason: str,
) -> QuestionDialogueEdge:
    return QuestionDialogueEdge(
        edge_id=f"{reading_id}:question-edge:{source.question_id}:{target.question_id}:{relation}",
        source_question_id=source.question_id,
        target_question_id=target.question_id,
        relation=relation,
        weight=weight,
        reason=reason,
    )


def _policy_notes(
    nodes: list[QuestionDialogueNode],
    hidden_factor_calibration: dict[str, object],
    hidden_factor_state: dict[str, object],
    question_outcomes: list[dict[str, object]],
) -> list[str]:
    notes = ["question_graph_preserves_recommendation_score_order"]
    if any(node.topic == "time_context" for node in nodes):
        notes.append("time_context_first_blocks_unbound_timing_claims")
    if hidden_factor_calibration.get("status") == "needs_dialogue":
        notes.append("hidden_factor_requires_dialogue_before_amplifier_use")
    if hidden_factor_calibration.get("amplifier_candidate"):
        notes.append("hidden_factor_feedback_can_condition_followups")
    if hidden_factor_state.get("amplifier_candidate"):
        notes.append("persisted_hidden_factor_state_can_condition_followups")
    if hidden_factor_state.get("status") == "expired":
        notes.append("persisted_hidden_factor_state_expired_requires_refresh")
    if _alignment_score(hidden_factor_state):
        notes.append(f"hidden_factor_event_alignment:{_alignment_score(hidden_factor_state)}")
    if question_outcomes:
        notes.append("question_dialogue_outcome_consumed")
        for topic in sorted({str(row.get("topic")) for row in question_outcomes if isinstance(row, dict) and row.get("topic")}):
            notes.append(f"question_outcome_topic:{topic}")
        for option in sorted({str(row.get("selected_option")) for row in question_outcomes if isinstance(row, dict) and row.get("selected_option")}):
            notes.append(f"structured_option_selected:{option}")
    return notes


def _next_question_id(nodes: list[QuestionDialogueNode], question_outcomes: list[dict[str, object]]) -> str | None:
    answered_ids = {str(row.get("question_id")) for row in question_outcomes if isinstance(row, dict)}
    selected_topics = [_selected_topic(row) for row in reversed(question_outcomes) if isinstance(row, dict)]
    for topic in selected_topics:
        if not topic:
            continue
        for node in nodes:
            if node.question_id not in answered_ids and node.topic == topic:
                return node.question_id
    for node in nodes:
        if node.question_id not in answered_ids:
            return node.question_id
    return nodes[0].question_id if nodes else None


def _internal_next_question_id(
    nodes: list[QuestionDialogueNode],
    question_outcomes: list[dict[str, object]],
) -> str | None:
    selected_topics = [_selected_topic(row) for row in reversed(question_outcomes) if isinstance(row, dict)]
    if any(topic for topic in selected_topics):
        return _next_question_id(nodes, question_outcomes)
    answered_ids = {str(row.get("question_id")) for row in question_outcomes if isinstance(row, dict)}
    internal_stages = {
        "context_completion",
        "dialogue_discovery",
        "candidate_review",
        "mainline_review",
        "practical_reading_followup",
    }
    for node in nodes:
        if node.question_id not in answered_ids and node.stage in internal_stages:
            return node.question_id
    return None


def _followup_reason(
    next_question_id: str | None,
    edges: list[QuestionDialogueEdge],
    question_outcomes: list[dict[str, object]],
) -> str:
    if not next_question_id:
        return "no_next_question_available"
    answered_ids = {
        str(row.get("question_id"))
        for row in question_outcomes
        if isinstance(row, dict) and row.get("question_id")
    }
    selected_topics = [_selected_topic(row) for row in reversed(question_outcomes) if isinstance(row, dict)]
    if any(topic for topic in selected_topics):
        for edge in edges:
            if edge.target_question_id == next_question_id and edge.source_question_id in answered_ids:
                return edge.reason
        topic = next((topic for topic in selected_topics if topic), "")
        if topic:
            return f"selected_domain:{topic}:prioritizes_followup_without_changing_chart_facts"
    return "highest_ranked_unanswered_question"


def _alignment_score(hidden_factor_state: dict[str, object]) -> float:
    try:
        return round(float(hidden_factor_state.get("alignment_score") or 0.0), 3)
    except (TypeError, ValueError):
        return 0.0


def _selected_topic(outcome: dict[str, object]) -> str:
    option = str(outcome.get("selected_option") or "")
    if option.startswith("domain:"):
        return option.split(":", 1)[1]
    if option in {"career", "wealth", "relationship", "health", "timing", "decision"}:
        return option
    topic = str(outcome.get("topic") or "")
    return topic if option else ""
