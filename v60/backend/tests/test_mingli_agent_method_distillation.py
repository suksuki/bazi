from __future__ import annotations

from types import SimpleNamespace

from abu_v60.mingli.agent_method_cards import mechanism_method_card
from abu_v60.mingli.agent_method_distillation import (
    OUTPUT_TO_PRESSURE,
    OUTPUT_TO_WEALTH,
    PRESSURE_RESOURCE_SELF,
    WEALTH_TO_PRESSURE,
    bound_method_context,
    cross_card_discriminator,
    day_master_regime_method_asset,
    domain_method_assets,
    exact_role_paths,
    research_output_path_gate,
    research_regime_outcome,
)

OWNER_OCCURRENCES = {
    "食神": ("year干丁",),
    "伤官": ("year支藏丙", "month支藏丙"),
    "正财": ("year支藏戊", "month支藏戊"),
    "偏财": ("day支藏己",),
    "正官": ("year支藏庚", "month支藏庚"),
    "七杀": ("day支藏辛", "hour支藏辛"),
    "偏印": ("day支藏癸",),
    "正印": ("hour支藏壬",),
    "日主": ("day干乙",),
}


def test_distillation_splits_broad_candidates_into_exact_ten_god_paths() -> None:
    pressure = exact_role_paths(OUTPUT_TO_PRESSURE, OWNER_OCCURRENCES)
    wealth = exact_role_paths(OUTPUT_TO_WEALTH, OWNER_OCCURRENCES)

    assert {item["role_path_ref"] for item in pressure} == {
        "FOOD_GOD_TO_SEVEN_KILLING",
        "HURTING_OFFICIAL_TO_SEVEN_KILLING",
        "HURTING_OFFICIAL_TO_PROPER_OFFICIAL",
        "FOOD_GOD_TO_PROPER_OFFICIAL",
    }
    assert {item["role_path_ref"] for item in wealth} == {
        "FOOD_GOD_TO_DIRECT_WEALTH",
        "FOOD_GOD_TO_INDIRECT_WEALTH",
        "HURTING_OFFICIAL_TO_DIRECT_WEALTH",
        "HURTING_OFFICIAL_TO_INDIRECT_WEALTH",
    }
    food_to_killing = next(
        item for item in pressure if item["role_path_ref"] == "FOOD_GOD_TO_SEVEN_KILLING"
    )
    assert food_to_killing["source"]["coordinates"] == ("year干丁",)
    assert food_to_killing["source"]["manifestation"] == "VISIBLE_ONLY"
    assert food_to_killing["target"]["coordinates"] == (
        "day支藏辛",
        "hour支藏辛",
    )
    assert food_to_killing["target"]["manifestation"] == "HIDDEN_ONLY"


def test_method_card_binds_rubric_to_chart_facts_by_pattern_not_evidence_order() -> None:
    context = bound_method_context(
        pattern_ref=OUTPUT_TO_WEALTH,
        ten_god_occurrences=OWNER_OCCURRENCES,
        root_candidates=(),
        visible_peers=("month干乙(比肩)", "hour干乙(比肩)"),
        hidden_resources=("day支藏癸(偏印)",),
    )
    card = mechanism_method_card(
        SimpleNamespace(
            pattern_ref=OUTPUT_TO_WEALTH,
            label="食伤生财结构候选",
            evidence_id="E099",
            blocker_codes=(),
            role_summary=("SOURCE", "TARGET"),
        ),
        include_distilled_guidance=True,
        distilled_context=context,
    )

    assert card["method_card_ref"] == "E099"
    assert card["pattern_ref"] == OUTPUT_TO_WEALTH
    assert card["distilled_method"]["check_guidance"][1]["check_code"] == (
        "WEALTH_TARGET_REACHABILITY"
    )
    assert card["bound_method_context"]["capacity_fact_lock"] == {
        "root_candidates": (),
        "visible_peers": ("month干乙(比肩)", "hour干乙(比肩)"),
        "hidden_resources": ("day支藏癸(偏印)",),
        "counting_forbidden": True,
    }


def test_distillation_covers_wealth_pressure_and_pressure_resource_self_paths() -> None:
    wealth_pressure = exact_role_paths(WEALTH_TO_PRESSURE, OWNER_OCCURRENCES)
    pressure_resource_self = exact_role_paths(
        PRESSURE_RESOURCE_SELF,
        OWNER_OCCURRENCES,
    )

    assert len(wealth_pressure) == 4
    assert all("bridge" not in item for item in wealth_pressure)
    assert len(pressure_resource_self) == 4
    assert all(item["bridge"]["ten_god"] in {"正印", "偏印"} for item in pressure_resource_self)
    assert all(item["target"]["coordinates"] == ("day干乙",) for item in pressure_resource_self)

    for pattern_ref in (WEALTH_TO_PRESSURE, PRESSURE_RESOURCE_SELF):
        context = bound_method_context(
            pattern_ref=pattern_ref,
            ten_god_occurrences=OWNER_OCCURRENCES,
            root_candidates=(),
            visible_peers=(),
            hidden_resources=("day支藏癸(偏印)",),
        )
        card = mechanism_method_card(
            SimpleNamespace(
                pattern_ref=pattern_ref,
                label="新机制候选",
                evidence_id="E098",
                blocker_codes=(),
                role_summary=("SOURCE", "TARGET"),
            ),
            include_distilled_guidance=True,
            distilled_context=context,
        )
        assert len(card["distilled_method"]["check_guidance"]) == len(card["required_checks"])
        assert card["bound_method_context"]["exact_role_paths"]


def test_regime_method_exits_forbid_ordinary_weak_without_rooted_support() -> None:
    method = day_master_regime_method_asset(
        seasonal_relation="OUTPUT_SEASONAL_DRAIN",
        root_candidates=(),
        visible_peers=(),
        hidden_resources=("month支藏己(正印)",),
        root_candidate_assessments=(),
    )

    exits = method["ordered_exit_decision_table"]
    assert [item["classification"] for item in exits] == [
        "NON_WEAK_OUTSIDE_SCOPE",
        "ORDINARY_WEAK",
        "UNRESOLVED",
        "FALSE_FOLLOW_COMPETITION",
        "FOLLOW_TREND",
    ]
    assert "禁止 ORDINARY_WEAK" in method["typed_field_rules"]["classification_follows_status"]


def test_single_variable_reachability_flips_pressure_but_holds_wealth() -> None:
    pressure_hidden = research_output_path_gate(
        pattern_ref=OUTPUT_TO_PRESSURE,
        source_present=True,
        target_present=True,
        source_target_reachable=False,
        target_is_seven_killing=True,
    )
    pressure_visible = research_output_path_gate(
        pattern_ref=OUTPUT_TO_PRESSURE,
        source_present=True,
        target_present=True,
        source_target_reachable=True,
        target_is_seven_killing=True,
    )
    wealth_before = research_output_path_gate(
        pattern_ref=OUTPUT_TO_WEALTH,
        source_present=True,
        target_present=True,
        source_target_reachable=True,
    )
    wealth_after = research_output_path_gate(
        pattern_ref=OUTPUT_TO_WEALTH,
        source_present=True,
        target_present=True,
        source_target_reachable=True,
    )

    assert (pressure_hidden, pressure_visible) == ("BROKEN", "SUPPORTED")
    assert wealth_before == wealth_after == "SUPPORTED"


def test_unreachable_wealth_target_breaks_the_same_blocking_gate_as_runtime() -> None:
    assert (
        research_output_path_gate(
            pattern_ref=OUTPUT_TO_WEALTH,
            source_present=True,
            target_present=True,
            source_target_reachable=False,
        )
        == "BROKEN"
    )


def test_pressure_discriminator_requires_same_layer_instead_of_counting_presence() -> None:
    discriminator = cross_card_discriminator()

    assert "SOURCE_AND_TARGET_SAME_LAYER" in discriminator["pressure_decisive_checks"]
    assert "OUTPUT_SOURCE_AVAILABILITY" not in discriminator["pressure_decisive_checks"]


def test_single_variable_wealth_and_peer_mutations_do_not_strengthen_pressure() -> None:
    wealth_absent = research_output_path_gate(
        pattern_ref=OUTPUT_TO_WEALTH,
        source_present=True,
        target_present=False,
        source_target_reachable=True,
    )
    wealth_competed = research_output_path_gate(
        pattern_ref=OUTPUT_TO_WEALTH,
        source_present=True,
        target_present=True,
        source_target_reachable=True,
        peer_competition_resolved=False,
    )
    pressure_with_bridge = research_output_path_gate(
        pattern_ref=OUTPUT_TO_PRESSURE,
        source_present=True,
        target_present=True,
        source_target_reachable=True,
        target_is_seven_killing=True,
        wealth_bridge_present=True,
    )

    assert wealth_absent == "BROKEN"
    assert wealth_competed == "CONDITIONAL"
    assert pressure_with_bridge == "CONDITIONAL"


def test_root_and_support_mutations_force_following_candidate_to_retreat() -> None:
    following = research_regime_outcome(
        effective_root=False,
        rooted_visible_support=False,
        visible_peer_competition=False,
        hidden_resource_competition=False,
        dominant_chain_closed=True,
    )
    rooted = research_regime_outcome(
        effective_root=True,
        rooted_visible_support=False,
        visible_peer_competition=False,
        hidden_resource_competition=False,
        dominant_chain_closed=True,
    )
    false_follow = research_regime_outcome(
        effective_root=False,
        rooted_visible_support=False,
        visible_peer_competition=True,
        hidden_resource_competition=True,
        dominant_chain_closed=True,
    )
    chain_broken = research_regime_outcome(
        effective_root=False,
        rooted_visible_support=False,
        visible_peer_competition=False,
        hidden_resource_competition=False,
        dominant_chain_closed=False,
    )

    assert following == "FOLLOW_TREND_CANDIDATE"
    assert rooted == "ORDINARY_WEAK"
    assert false_follow == "FALSE_FOLLOW_CANDIDATE"
    assert chain_broken == "UNRESOLVED"


def test_relationship_method_switches_spouse_star_axis_without_stereotype_story() -> None:
    spouse_palace = {
        "slot": "day",
        "pillar": "乙丑",
        "branch": "丑",
        "evidence_id": "E003",
    }
    male = domain_method_assets(
        gender="male",
        ten_god_occurrences=OWNER_OCCURRENCES,
        spouse_palace=spouse_palace,
    )["relationship"]
    female = domain_method_assets(
        gender="female",
        ten_god_occurrences=OWNER_OCCURRENCES,
        spouse_palace=spouse_palace,
    )["relationship"]

    assert male["spouse_star_labels"] == ("正财", "偏财")
    assert female["spouse_star_labels"] == ("正官", "七杀")
    assert male["spouse_palace"] == female["spouse_palace"] == spouse_palace
    assert "单枚偏印推出精神共鸣或情感安全" in male["forbidden_shortcuts"]
