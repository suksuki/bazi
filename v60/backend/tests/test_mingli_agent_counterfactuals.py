from abu_v60.mingli.agent_counterfactuals import (
    decision_row_catalog,
    decision_row_is_valid,
    decision_row_selection_is_valid,
    method_falsifier_is_actionable,
    normalized_decision_row,
    repaired_method_falsifier,
    reversal_is_actionable,
    reversal_row_ref,
)


def test_method_falsifier_requires_condition_and_explicit_ruling_change() -> None:
    assert method_falsifier_is_actionable(
        "若承载条件出现相反证据，则本项由支持改判为有条件。",
        current_ruling="SUPPORTS",
    )
    assert method_falsifier_is_actionable(
        "若来源被阻断，则本项由CONDITIONAL改判为OPPOSES。",
        current_ruling="CONDITIONAL",
    )
    assert not method_falsifier_is_actionable(
        "若来源被阻断，需要继续观察。",
        current_ruling="CONDITIONAL",
    )
    assert not method_falsifier_is_actionable(
        "当前来源能够抵达目标，所以本项成立。",
        current_ruling="SUPPORTS",
    )
    repaired = repaired_method_falsifier(current_ruling="UNRESOLVED")
    assert method_falsifier_is_actionable(repaired, current_ruling="UNRESOLVED")


def test_reversal_requires_named_maintain_and_opposite_flip_actions() -> None:
    assert reversal_is_actionable(
        winner_signal="若现实更符合食伤生财，维持食伤生财为主解释。",
        loser_signal="若现实更符合食伤制杀，翻转为食伤制杀。",
        primary_name="食伤生财",
        alternative_name="食伤制杀",
    )
    assert not reversal_is_actionable(
        winner_signal="若收入增长，支持食伤生财。",
        loser_signal="若收入增长，也支持食伤生财。",
        primary_name="食伤生财",
        alternative_name="食伤制杀",
    )


def test_method_card_compiles_typed_counterfactual_row_and_reversal_binding() -> None:
    rows = decision_row_catalog(
        method_card_ref="E009",
        check_codes=("DAY_MASTER_CAPACITY", "PEER_COMPETITION_RESOLUTION"),
    )
    assert rows == (
        "DAY_MASTER_CAPACITY:CAPACITY",
        "PEER_COMPETITION_RESOLUTION:BLOCKER_RESOLUTION",
    )
    row = normalized_decision_row(
        method_card_ref="E009",
        check_code="DAY_MASTER_CAPACITY",
        current_ruling="CONDITIONAL",
    )
    assert decision_row_is_valid(
        row,
        method_card_ref="E009",
        check_code="DAY_MASTER_CAPACITY",
        current_ruling="CONDITIONAL",
    )
    assert not decision_row_is_valid(
        {**row, "target_ruling": "SUPPORTS"},
        method_card_ref="E009",
        check_code="DAY_MASTER_CAPACITY",
        current_ruling="CONDITIONAL",
    )
    assert decision_row_selection_is_valid(row, check_code="DAY_MASTER_CAPACITY")
    assert not decision_row_selection_is_valid(
        {**row, "trigger_axis": "SOURCE_AVAILABILITY"},
        check_code="DAY_MASTER_CAPACITY",
    )
    assert (
        reversal_row_ref(
            primary_method_card_ref="E009",
            alternative_method_card_ref="E010",
        )
        == "REVERSAL:E009>E010:MAINTAIN_PRIMARY>FLIP_TO_ALTERNATIVE"
    )
    assert decision_row_catalog(
        method_card_ref="FALLBACK_WHOLE_CHART",
        check_codes=("ROOT_PEER_RESOURCE_ORDER", "SOURCE_BRIDGE_SAME_LAYER"),
    ) == (
        "ROOT_PEER_RESOURCE_ORDER:ROOT_SUPPORT",
        "SOURCE_BRIDGE_SAME_LAYER:LAYER_ALIGNMENT",
    )
    assert not reversal_is_actionable(
        winner_signal="若现实更符合食伤生财，维持食伤生财为主解释。",
        loser_signal="若现实更符合食伤制杀，维持食伤生财。",
        primary_name="食伤生财",
        alternative_name="食伤制杀",
    )
