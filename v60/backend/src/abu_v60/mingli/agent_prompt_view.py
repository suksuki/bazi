from __future__ import annotations

from typing import TYPE_CHECKING, Any

from abu_v60.mingli.agent_method_cards import (
    fallback_hypothesis_method_card,
    mechanism_method_card,
)
from abu_v60.mingli.agent_method_distillation import (
    bound_method_context,
    cross_card_discriminator,
    day_master_regime_method_asset,
    domain_method_assets,
)
from abu_v60.mingli.agent_root_gate import packet_root_candidate_assessments

if TYPE_CHECKING:
    from abu_v60.mingli.agent_contracts import MingliAgentCasePacket


_BRANCH_ELEMENT = {
    "寅": "wood",
    "卯": "wood",
    "辰": "earth",
    "巳": "fire",
    "午": "fire",
    "未": "earth",
    "申": "metal",
    "酉": "metal",
    "戌": "earth",
    "亥": "water",
    "子": "water",
    "丑": "earth",
}
_GENERATES = {
    "wood": "fire",
    "fire": "earth",
    "earth": "metal",
    "metal": "water",
    "water": "wood",
}
_CONTROLS = {
    "wood": "earth",
    "earth": "water",
    "water": "fire",
    "fire": "metal",
    "metal": "wood",
}
_THREE_HARMONY_GROUPS = (
    ("申子辰", "water"),
    ("亥卯未", "wood"),
    ("寅午戌", "fire"),
    ("巳酉丑", "metal"),
)
_ELEMENT_LABEL = {
    "wood": "木",
    "fire": "火",
    "earth": "土",
    "metal": "金",
    "water": "水",
}


def _professional_adjudication_view(packet: MingliAgentCasePacket) -> dict[str, Any]:
    month_element = _BRANCH_ELEMENT[packet.month_command_branch]
    day_element = packet.day_master_element
    if month_element == day_element:
        seasonal_relation = "SAME_ELEMENT_SEASONAL_SUPPORT"
    elif _GENERATES[month_element] == day_element:
        seasonal_relation = "RESOURCE_SEASONAL_SUPPORT"
    elif _GENERATES[day_element] == month_element:
        seasonal_relation = "OUTPUT_SEASONAL_DRAIN"
    elif _CONTROLS[month_element] == day_element:
        seasonal_relation = "OFFICIAL_SEASONAL_PRESSURE"
    else:
        seasonal_relation = "WEALTH_SEASONAL_DRAIN"

    branch_coordinates: dict[str, list[dict[str, str]]] = {}
    for pillar in packet.pillars:
        branch_coordinates.setdefault(pillar.branch, []).append(
            {
                "slot": pillar.slot,
                "branch": pillar.branch,
                "evidence_id": pillar.evidence_id,
            }
        )
    structure_candidates = []
    present_branches = set(branch_coordinates)
    for members, result_element in _THREE_HARMONY_GROUPS:
        if not set(members).issubset(present_branches):
            continue
        member_coordinates = tuple(
            coordinate for member in members for coordinate in branch_coordinates[member]
        )
        structure_candidates.append(
            {
                "relation_type": "three_harmony_membership_candidate",
                "label": f"{members}三合{_ELEMENT_LABEL[result_element]}成员齐备候选",
                "members": tuple(members),
                "result_element": result_element,
                "member_coordinates": member_coordinates,
                "evidence_ids": tuple(
                    dict.fromkeys(coordinate["evidence_id"] for coordinate in member_coordinates)
                ),
                "membership_status": "CLASSICAL_MEMBER_SET_PRESENT",
                "effect_status": "REQUIRES_WHOLE_CHART_ADJUDICATION",
            }
        )

    occurrence_map: dict[str, list[str]] = {}
    for pillar in packet.pillars:
        occurrence_map.setdefault(pillar.visible_ten_god, []).append(
            f"{pillar.slot}干{pillar.stem}"
        )
        for hidden_stem, ten_god in zip(
            pillar.hidden_stems,
            pillar.hidden_ten_gods,
            strict=True,
        ):
            occurrence_map.setdefault(ten_god, []).append(f"{pillar.slot}支藏{hidden_stem}")
    natal_evidence_ids = tuple(
        item.evidence_id for item in packet.evidence_catalog if item.kind != "TIMING"
    )
    timing_evidence_ids = tuple(
        item.evidence_id for item in packet.evidence_catalog if item.kind == "TIMING"
    )
    mechanism_evidence_ids = {item.evidence_id for item in packet.mechanism_observations}
    chart_basis_evidence_ids = tuple(
        item for item in natal_evidence_ids if item not in mechanism_evidence_ids
    )
    root_assessments = packet_root_candidate_assessments(packet)
    mechanism_cards = tuple(
        mechanism_method_card(
            item,
            include_distilled_guidance=True,
            distilled_context=bound_method_context(
                pattern_ref=item.pattern_ref,
                ten_god_occurrences=occurrence_map,
                root_candidates=packet.day_master_support.same_element_hidden_support,
                visible_peers=packet.day_master_support.visible_peer_support,
                hidden_resources=packet.day_master_support.resource_support,
            ),
        )
        for item in packet.mechanism_observations
    )
    fallback_card = fallback_hypothesis_method_card()
    return {
        "natal_evidence_ids": natal_evidence_ids,
        "timing_evidence_ids": timing_evidence_ids,
        "field_evidence_scope": {
            "natal_only_fields": (
                "first_look",
                "whole_chart_thesis",
                "hypotheses",
                "work_path",
                "life_image",
                "domains",
                "timing.natal_baseline",
            ),
            "natal_allowed": natal_evidence_ids,
            "primary_requires_chart_basis_from": chart_basis_evidence_ids,
            "natal_prose_forbidden": (
                "大运",
                "流年",
                "岁运",
                *(item.pillar for item in packet.timing_coordinates),
            ),
        },
        "output_field_contract": {
            "support_selection": {
                "meaning": "OBSERVED_CANDIDATE_LIST_ACKNOWLEDGEMENT_NOT_EFFECTIVE_ROOT_RULING",
                "root_status": (
                    "PRESENT_IFF_DAY_MASTER_SUPPORT_SAME_ELEMENT_HIDDEN_SUPPORT_IS_NONEMPTY_"
                    "ELSE_NONE"
                ),
                "root_coordinates": "EXACT_COPY_DAY_MASTER_SUPPORT_SAME_ELEMENT_HIDDEN_SUPPORT",
                "peer_coordinates": "EXACT_COPY_DAY_MASTER_SUPPORT_VISIBLE_PEER_SUPPORT",
                "resource_coordinates": "EXACT_COPY_DAY_MASTER_SUPPORT_RESOURCE_SUPPORT",
            },
            "regime_decision": {
                "required_non_null": True,
                "packet_specific_allowed_projections": _regime_output_scaffold(
                    packet,
                    root_assessments=root_assessments,
                ),
                "candidate_strength_shortcuts_forbidden": (
                    "微弱比肩",
                    "微弱帮扶",
                    "力量有限",
                    "根浅",
                    "根系尚浅",
                    "无力",
                ),
            },
            "work_path": {
                "scope": "NATAL_PRIMARY_HYPOTHESIS_ONLY",
                "evidence_ids_allowed": natal_evidence_ids,
                "evidence_ids_forbidden": timing_evidence_ids,
                "timing_prose_forbidden": True,
                "transformation_codes": "UNIQUE_VALUES_ONLY",
            },
        },
        "seasonal_context": {
            "month_command_branch": packet.month_command_branch,
            "month_command_element": month_element,
            "relation_to_day_master": seasonal_relation,
            "counting_warning": "SEASON_ROOT_POSITION_AND_PATH_MUST_BE_WEIGHED_NOT_COUNTED",
        },
        "support_order": {
            "hidden_root_candidates": packet.day_master_support.same_element_hidden_support,
            "visible_peer_support": packet.day_master_support.visible_peer_support,
            "hidden_resource_support": packet.day_master_support.resource_support,
            "decision_warning": (
                "VISIBLE_PEERS_OR_HIDDEN_RESOURCE_CANNOT_BY_THEMSELVES_OVERRIDE_"
                "SEASON_AND_ROOT_STATUS"
            ),
        },
        "day_master_regime_method": day_master_regime_method_asset(
            seasonal_relation=seasonal_relation,
            root_candidates=packet.day_master_support.same_element_hidden_support,
            visible_peers=packet.day_master_support.visible_peer_support,
            hidden_resources=packet.day_master_support.resource_support,
            root_candidate_assessments=root_assessments,
        ),
        "ten_god_occurrences": tuple(
            {
                "ten_god": ten_god,
                "coordinates": tuple(coordinates),
            }
            for ten_god, coordinates in sorted(occurrence_map.items())
        ),
        "professional_structure_candidates": tuple(structure_candidates),
        "candidate_method_cards": {
            "authority": "CHECKS_REQUIRE_AGENT_RULING",
            "three_harmony": tuple(
                {
                    "candidate_label": item["label"],
                    "required_checks": (
                        "MEMBER_COMPLETION_TYPE",
                        "MONTH_COMMAND_SUPPORT_OR_RESISTANCE",
                        "RESULT_ELEMENT_STEM_VISIBILITY",
                        "DISRUPTION_OR_COMPETING_PATH",
                        "DAY_MASTER_AND_WHOLE_CHART_CAPACITY",
                    ),
                    "shortcut_forbidden": (
                        "MEMBERS_PRESENT_DOES_NOT_MEAN_EFFECT_OR_TRANSFORMATION"
                    ),
                }
                for item in structure_candidates
            ),
            "mechanisms": mechanism_cards,
            "fallback_hypothesis": fallback_card,
            "hypothesis_output_scaffold": _hypothesis_output_scaffold(
                mechanism_cards=mechanism_cards,
                fallback_card=fallback_card,
            ),
            "cross_card_discriminator": cross_card_discriminator(),
            "work_path_closure": {
                "closed_allowed_when": ("ALL_PRIMARY_BLOCKING_AND_CONDITIONING_CHECKS_SUPPORT"),
                "otherwise_allowed": ("CONDITIONAL", "UNCERTAIN", "BROKEN"),
            },
        },
        "domain_method_assets": domain_method_assets(
            gender=packet.gender,
            ten_god_occurrences=occurrence_map,
            spouse_palace={
                "slot": "day",
                "pillar": packet.pillars[2].pillar,
                "branch": packet.pillars[2].branch,
                "evidence_id": packet.pillars[2].evidence_id,
                "hidden_stems": packet.pillars[2].hidden_stems,
                "hidden_ten_gods": packet.pillars[2].hidden_ten_gods,
            },
        ),
        "required_decision_order": (
            "WEIGH_SEASON_ROOT_PEER_RESOURCE_DRAIN_WEALTH_AND_PRESSURE",
            "LOCK_NATAL_PRIMARY_AND_ALTERNATIVE_EXPLANATIONS",
            "COMPARE_PATTERN_SUCCESS_FAILURE_RESCUE_AND_TRANSFORMATION",
            "DERIVE_LIFE_DOMAINS_FROM_THE_NATAL_PRIMARY_ONLY",
            "APPLY_DAYUN_THEN_ANNUAL_WITHOUT_BACKFLOW_TO_NATAL",
            "ASK_ONE_REALITY_QUESTION_THAT_CAN_REVERSE_THE_PRIMARY_CHOICE",
        ),
    }


def _regime_output_scaffold(
    packet: MingliAgentCasePacket,
    *,
    root_assessments: tuple[dict[str, object], ...],
) -> dict[str, object]:
    support = packet.day_master_support
    candidates = support.same_element_hidden_support
    minimum_roots = tuple(
        str(item["coordinate"])
        for item in root_assessments
        if item["minimum_anti_follow_gate"] == "PRESENT"
    )
    required_competition = (
        ("HIDDEN_RESOURCE",) if support.resource_support else ()
    )
    forbidden_competition = (
        ("VISIBLE_PEER",) if not support.visible_peer_support else ()
    )
    common = {
        "rooted_visible_support_status": (
            "ABSENT" if not support.visible_peer_support else "DERIVE_FROM_EFFECTIVE_ROOT"
        ),
        "required_competition_kinds": required_competition,
        "forbidden_competition_kinds": forbidden_competition,
        "required_evidence_ids": (support.evidence_id,),
    }
    if minimum_roots:
        options = (
            {
                "effective_root_status": "PRESENT",
                "effective_root_coordinates": minimum_roots,
                "classification_when_day_master_state_is_WEAK": "ORDINARY_WEAK",
                **common,
            },
        )
    elif candidates:
        options = (
            {
                "effective_root_status": "PRESENT",
                "effective_root_coordinates": {
                    "rule": "NONEMPTY_SUBSET_OF_ALLOWED_CANDIDATES",
                    "allowed": candidates,
                },
                "classification_when_day_master_state_is_WEAK": "ORDINARY_WEAK",
                **common,
            },
            {
                "effective_root_status": "UNRESOLVED",
                "effective_root_coordinates": (),
                "classification": "UNRESOLVED",
                **common,
            },
        )
    else:
        options = (
            {
                "effective_root_status": "ABSENT",
                "effective_root_coordinates": (),
                "classification": "DERIVE_FROM_DOMINANT_CHAIN_AND_COMPETITION",
                **common,
            },
        )
    return {
        "instruction": "SELECT_EXACTLY_ONE_OPTION_AND_COPY_ALL_DETERMINISTIC_FIELDS",
        "options": options,
    }


def _hypothesis_output_scaffold(
    *,
    mechanism_cards: tuple[dict[str, object], ...],
    fallback_card: dict[str, object],
) -> dict[str, object]:
    if len(mechanism_cards) not in {1, 2}:
        return {
            "mode": "SELECT_TWO_DISTINCT_CARDS",
            "allowed_method_card_refs": tuple(
                str(item["method_card_ref"]) for item in mechanism_cards
            ),
        }
    selected = (*mechanism_cards, fallback_card)[:2]
    return {
        "mode": "FIXED_SLOTS_COPY_EXACTLY",
        "slots": tuple(
            {
                "hypothesis_id": f"H{index}",
                "method_card_ref": card["method_card_ref"],
                "method_rulings_exact_order": tuple(
                    {
                        "method_card_ref": card["method_card_ref"],
                        "check_code": check_code,
                    }
                    for check_code in card["required_checks"]
                ),
            }
            for index, card in enumerate(selected, start=1)
        ),
        "role_policy": "EXACTLY_ONE_PRIMARY_AFTER_RULING_COMPARISON",
    }
