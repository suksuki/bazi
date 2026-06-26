from __future__ import annotations

from v30.contracts import BaziQuestionAnchor, ChartContext, FeatureEvidence, MainlineState, StructureState


QUESTION_ANCHOR_SELECTOR_VERSION = "v30.question_anchor_selector.v1"


def select_question_anchors(
    context: ChartContext,
    structure: StructureState,
    mainline: MainlineState,
    evidence: list[FeatureEvidence],
    *,
    role_key: str = "user",
) -> list[BaziQuestionAnchor]:
    anchors = [_mainline_review_anchor(context, structure, mainline, evidence, role_key=role_key)]
    if _has_domain_rule_context(evidence):
        anchors.extend(_user_question_anchors(context, structure, mainline, evidence, role_key=role_key))
    if _has_missing_time(evidence):
        anchors.append(_time_boundary_anchor(context, structure, mainline, evidence, role_key=role_key))
    if _has_useful_god_gate(evidence):
        anchors.append(_useful_god_candidate_anchor(context, structure, mainline, evidence, role_key=role_key))
    if _has_hidden_stem_context(evidence):
        anchors.append(_hidden_factor_discovery_anchor(context, structure, mainline, evidence, role_key=role_key))
    if _has_domain_rule_context(evidence):
        anchors.append(_practical_domain_focus_anchor(context, structure, mainline, evidence, role_key=role_key))
    return anchors


def _user_question_anchors(
    context: ChartContext,
    structure: StructureState,
    mainline: MainlineState,
    evidence: list[FeatureEvidence],
    *,
    role_key: str,
) -> list[BaziQuestionAnchor]:
    rows = [
        (
            "q_v30_user_career_direction",
            "ask_user_career_direction",
            "Which career direction or work-pressure pattern should the reading answer first?",
        ),
        (
            "q_v30_user_wealth_tendency",
            "ask_user_wealth_tendency",
            "Which wealth pattern and risk boundary should the reading answer first?",
        ),
        (
            "q_v30_user_relationship_pattern",
            "ask_user_relationship_pattern",
            "Which relationship pattern or recurring tension should the reading answer first?",
        ),
        (
            "q_v30_user_timing_pressure",
            "ask_user_timing_pressure",
            "Which current luck or flow pressure should the reading answer first?",
        ),
        (
            "q_v30_user_decision_blindspot",
            "ask_user_decision_blindspot",
            "Which decision blind spot should the reading explain first?",
        ),
    ]
    return [
        _anchor(
            context,
            structure,
            mainline,
            question_id=question_id,
            intent_id=intent_id,
            role_key=role_key,
            evidence_ids=_evidence_ids(evidence, {"domain_rule", "structure_pattern", "branch_relation", "ten_god", "rule"}),
            why=why,
        )
        for question_id, intent_id, why in rows
    ]


def _mainline_review_anchor(
    context: ChartContext,
    structure: StructureState,
    mainline: MainlineState,
    evidence: list[FeatureEvidence],
    *,
    role_key: str,
) -> BaziQuestionAnchor:
    return _anchor(
        context,
        structure,
        mainline,
        question_id="q_v30_mainline_review",
        intent_id="review_current_chart_mainline",
        role_key=role_key,
        evidence_ids=_evidence_ids(evidence, {"chart", "ten_god", "element", "branch_relation", "rule"}),
        why="This question reviews the current evidence-bound chart structure before making downstream claims.",
    )


def _time_boundary_anchor(
    context: ChartContext,
    structure: StructureState,
    mainline: MainlineState,
    evidence: list[FeatureEvidence],
    *,
    role_key: str,
) -> BaziQuestionAnchor:
    return _anchor(
        context,
        structure,
        mainline,
        question_id="q_v30_time_context_boundary",
        intent_id="confirm_missing_time_context",
        role_key=role_key,
        evidence_ids=_evidence_ids(evidence, {"time_context", "rule"}),
        why="This question asks for explicit luck or flow context because timing claims are blocked without it.",
        missing_requirements=["explicit_luck_or_flow_pillar"],
    )


def _useful_god_candidate_anchor(
    context: ChartContext,
    structure: StructureState,
    mainline: MainlineState,
    evidence: list[FeatureEvidence],
    *,
    role_key: str,
) -> BaziQuestionAnchor:
    return _anchor(
        context,
        structure,
        mainline,
        question_id="q_v30_useful_god_candidate_review",
        intent_id="review_useful_god_candidate_paths",
        role_key=role_key,
        evidence_ids=_evidence_ids(evidence, {"useful_god", "chart", "element", "rule"}),
        why="This question reviews useful-god candidate paths only; it does not assume a fixed favorable or unfavorable verdict.",
    )


def _hidden_factor_discovery_anchor(
    context: ChartContext,
    structure: StructureState,
    mainline: MainlineState,
    evidence: list[FeatureEvidence],
    *,
    role_key: str,
) -> BaziQuestionAnchor:
    return _anchor(
        context,
        structure,
        mainline,
        question_id="q_v30_hidden_factor_boundary_discovery",
        intent_id="discover_hidden_factor_amplifier",
        role_key=role_key,
        evidence_ids=_evidence_ids(evidence, {"ten_god", "rule"}),
        why=(
            "This question checks special years or repeated states before treating hidden stems as amplifying factors."
        ),
        missing_requirements=["special_event_year_or_repeated_state_feedback"],
    )


def _practical_domain_focus_anchor(
    context: ChartContext,
    structure: StructureState,
    mainline: MainlineState,
    evidence: list[FeatureEvidence],
    *,
    role_key: str,
) -> BaziQuestionAnchor:
    return _anchor(
        context,
        structure,
        mainline,
        question_id="q_v30_practical_domain_focus",
        intent_id="clarify_practical_reading_priority",
        role_key=role_key,
        evidence_ids=_evidence_ids(evidence, {"domain_rule", "structure_pattern", "time_context"}),
        why="This question asks which life domain should be prioritized before rendering practical reading conclusions.",
        missing_requirements=["career_wealth_relationship_health_priority_or_event_year"],
    )


def _anchor(
    context: ChartContext,
    structure: StructureState,
    mainline: MainlineState,
    *,
    question_id: str,
    intent_id: str,
    role_key: str,
    evidence_ids: list[str],
    why: str,
    missing_requirements: list[str] | None = None,
) -> BaziQuestionAnchor:
    return BaziQuestionAnchor(
        anchor_id=f"{context.context_id}:anchor:{question_id}",
        question_id=question_id,
        intent_id=intent_id,
        context_id=context.context_id,
        role_key=role_key,  # type: ignore[arg-type]
        anchor_status="bound",
        day_master=context.day_master,
        time_binding={"status": context.time_layers.get("status", "not_provided")},
        primary_structure_id=structure.structure_id,
        mainline_id=mainline.mainline_id,
        evidence_ids=evidence_ids,
        why_this_question=why,
        missing_requirements=missing_requirements or [],
    )


def _evidence_ids(evidence: list[FeatureEvidence], domains: set[str]) -> list[str]:
    rows = [row.evidence_id for row in evidence if row.domain in domains]
    return rows or [row.evidence_id for row in evidence[:1]]


def _has_missing_time(evidence: list[FeatureEvidence]) -> bool:
    return any(row.domain == "time_context" and row.kind == "missing_requirement" for row in evidence)


def _has_useful_god_gate(evidence: list[FeatureEvidence]) -> bool:
    return any(row.domain == "useful_god" and row.kind == "evidence_gate" for row in evidence)


def _has_hidden_stem_context(evidence: list[FeatureEvidence]) -> bool:
    return any(row.domain == "ten_god" and row.kind == "hidden_stem" for row in evidence)


def _has_domain_rule_context(evidence: list[FeatureEvidence]) -> bool:
    return any(row.domain == "domain_rule" for row in evidence)
