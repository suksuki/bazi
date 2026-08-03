from __future__ import annotations

from abu_v60.mingli.agent_adjudication import aggregate_method_rulings
from abu_v60.mingli.agent_contracts import MingliAgentCasePacket, MingliAgentModelOutput
from abu_v60.mingli.agent_method_cards import (
    FALLBACK_METHOD_CARD_REF,
    method_card_catalog,
)


def validate_adjudication_output(
    *,
    output: MingliAgentModelOutput,
    packet: MingliAgentCasePacket,
) -> None:
    cards = method_card_catalog(packet.mechanism_observations)
    natal_ids = {item.evidence_id for item in packet.evidence_catalog if item.kind != "TIMING"}
    by_id = {item.hypothesis_id: item for item in output.hypotheses}
    if (
        len(packet.mechanism_observations) >= 2
        and len({item.method_card_ref for item in output.hypotheses}) != 2
    ):
        raise ValueError("mingli_agent_hypothesis_cards_not_competing")
    for hypothesis in output.hypotheses:
        card = cards.get(hypothesis.method_card_ref)
        if card is None:
            raise ValueError("mingli_agent_unknown_method_card")
        expected = tuple(card["required_checks"])
        actual = tuple(item.check_code for item in hypothesis.method_rulings)
        if actual != expected:
            raise ValueError("mingli_agent_method_checks_not_exact_order")
        if any(
            item.method_card_ref != hypothesis.method_card_ref for item in hypothesis.method_rulings
        ):
            raise ValueError("mingli_agent_method_ruling_card_mismatch")
        if any(
            not set(item.evidence_ids).issubset(natal_ids) for item in hypothesis.method_rulings
        ):
            raise ValueError("mingli_agent_method_ruling_uses_non_natal_evidence")
        if hypothesis.method_card_ref == FALLBACK_METHOD_CARD_REF:
            if hypothesis.mechanism_evidence_ids:
                raise ValueError("mingli_agent_fallback_card_has_mechanism_evidence")
        elif hypothesis.mechanism_evidence_ids != (hypothesis.method_card_ref,):
            raise ValueError("mingli_agent_method_card_mechanism_mismatch")
        expected_aggregate = aggregate_method_rulings(
            rulings=hypothesis.method_rulings,
            blocking_checks=tuple(card["blocking_checks"]),
        )
        if hypothesis.adjudication != expected_aggregate:
            raise ValueError("mingli_agent_method_aggregate_mismatch")
        if expected_aggregate == "BROKEN" and hypothesis.judgment != "BLOCKED":
            raise ValueError("mingli_agent_broken_method_not_blocked")
        if expected_aggregate == "SUPPORTED" and hypothesis.judgment != "SUPPORTED":
            raise ValueError("mingli_agent_supported_method_not_supported")
        if expected_aggregate == "CONDITIONAL" and hypothesis.judgment not in {
            "WORKS_IF",
            "PARTIAL",
        }:
            raise ValueError("mingli_agent_conditional_method_judgment_conflict")
        if expected_aggregate == "UNRESOLVED" and hypothesis.judgment != "COMPETING":
            raise ValueError("mingli_agent_unresolved_method_not_competing")
        if hypothesis.confidence == "HIGH":
            raise ValueError("mingli_agent_hypothesis_confidence_exceeds_adjudication")
        if expected_aggregate in {"BROKEN", "UNRESOLVED"} and hypothesis.confidence != "LOW":
            raise ValueError("mingli_agent_unresolved_method_confidence_too_high")

    selected_cards = {
        item.method_card_ref
        for item in output.hypotheses
        if item.method_card_ref != FALLBACK_METHOD_CARD_REF
    }
    expected_excluded = tuple(
        item.evidence_id
        for item in packet.mechanism_observations
        if item.evidence_id not in selected_cards
    )
    if tuple(item.method_card_ref for item in output.excluded_candidates) != expected_excluded:
        raise ValueError("mingli_agent_candidate_coverage_incomplete")
    for item in output.excluded_candidates:
        card = cards[item.method_card_ref]
        if item.decisive_check not in set(card["required_checks"]):
            raise ValueError("mingli_agent_excluded_candidate_check_invalid")
        if not set(item.evidence_ids).issubset(natal_ids):
            raise ValueError("mingli_agent_excluded_candidate_uses_non_natal_evidence")
    candidate_count = len(packet.mechanism_observations)
    expected_selected = min(candidate_count, 2)
    if len(selected_cards) != expected_selected and not (
        candidate_count >= 1
        and any(item.adjudication == "BROKEN" for item in output.hypotheses)
        and FALLBACK_METHOD_CARD_REF in {item.method_card_ref for item in output.hypotheses}
    ):
        raise ValueError("mingli_agent_candidate_selection_count_invalid")

    decision = output.hypothesis_decision
    primary = next(item for item in output.hypotheses if item.role == "PRIMARY")
    alternative = next(item for item in output.hypotheses if item.role == "ALTERNATIVE")
    if (decision.winner_id, decision.loser_id) != (
        primary.hypothesis_id,
        alternative.hypothesis_id,
    ):
        raise ValueError("mingli_agent_decision_role_conflict")
    for side, hypothesis in (
        (decision.winner, by_id[decision.winner_id]),
        (decision.loser, by_id[decision.loser_id]),
    ):
        allowed_checks = {item.check_code for item in hypothesis.method_rulings}
        if not set(side.decisive_checks).issubset(allowed_checks):
            raise ValueError("mingli_agent_decisive_check_not_in_method_card")
    rank = {"BROKEN": 0, "UNRESOLVED": 1, "CONDITIONAL": 2, "SUPPORTED": 3}
    if rank[primary.adjudication] < rank[alternative.adjudication] and primary.confidence != "LOW":
        raise ValueError("mingli_agent_weaker_working_primary_requires_low_confidence")
    if primary.adjudication == "BROKEN":
        raise ValueError("mingli_agent_broken_primary")
    if primary.adjudication != "SUPPORTED" and output.work_path.closure == "CLOSED":
        raise ValueError("mingli_agent_work_path_closed_without_supported_method")
    if primary.adjudication == "UNRESOLVED" and primary.confidence != "LOW":
        raise ValueError("mingli_agent_working_primary_must_be_low_confidence")
