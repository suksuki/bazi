from abu_v60.mingli.agent_counterfactuals import (
    method_falsifier_is_actionable,
    repaired_method_falsifier,
    reversal_is_actionable,
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
    assert not reversal_is_actionable(
        winner_signal="若现实更符合食伤生财，维持食伤生财为主解释。",
        loser_signal="若现实更符合食伤制杀，维持食伤生财。",
        primary_name="食伤生财",
        alternative_name="食伤制杀",
    )
