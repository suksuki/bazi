from __future__ import annotations

from typing import Final

_CONDITION_PREFIXES: Final = ("若", "如果", "当", "除非", "反之")
_CHANGE_ACTIONS: Final = ("改判", "改为", "转为", "转成", "降为", "升为")
_MAINTAIN_ACTIONS: Final = ("维持", "保留", "继续以", "仍以", "保持")
_FLIP_ACTIONS: Final = ("翻转", "转向", "改判", "改以", "改为")
_RULING_LABELS: Final = {
    "SUPPORTS": ("SUPPORTS", "支持"),
    "CONDITIONAL": ("CONDITIONAL", "有条件"),
    "OPPOSES": ("OPPOSES", "反对"),
    "UNRESOLVED": ("UNRESOLVED", "未决"),
}
_FALSIFIER_TARGET: Final = {
    "SUPPORTS": "CONDITIONAL",
    "CONDITIONAL": "OPPOSES",
    "OPPOSES": "UNRESOLVED",
    "UNRESOLVED": "CONDITIONAL",
}
_RULING_ZH: Final = {
    "SUPPORTS": "支持",
    "CONDITIONAL": "有条件",
    "OPPOSES": "反对",
    "UNRESOLVED": "未决",
}


def method_falsifier_is_actionable(text: object, *, current_ruling: object) -> bool:
    """Require an observable condition and an explicit change away from the ruling."""

    if not isinstance(text, str) or not isinstance(current_ruling, str):
        return False
    sentence = text.strip()
    aliases = _RULING_LABELS.get(current_ruling)
    if not sentence.startswith(_CONDITION_PREFIXES) or aliases is None:
        return False
    if not any(action in sentence for action in _CHANGE_ACTIONS):
        return False
    if not any(alias in sentence for alias in aliases):
        return False
    return any(
        alias in sentence
        for ruling, ruling_aliases in _RULING_LABELS.items()
        if ruling != current_ruling
        for alias in ruling_aliases
    )


def repaired_method_falsifier(*, current_ruling: str) -> str:
    target = _FALSIFIER_TARGET.get(current_ruling, "UNRESOLVED")
    current_label = _RULING_ZH.get(current_ruling, "当前判断")
    target_label = _RULING_ZH[target]
    return (
        "若本检查尚未裁定的阻断、承载或可达条件出现相反证据，"
        f"则本项由{current_label}改判为{target_label}。"
    )


def reversal_is_actionable(
    *,
    winner_signal: object,
    loser_signal: object,
    primary_name: object,
    alternative_name: object,
) -> bool:
    """Validate two named, decision-changing signals without judging their truth."""

    if not all(
        isinstance(item, str)
        for item in (winner_signal, loser_signal, primary_name, alternative_name)
    ):
        return False
    winner = winner_signal.strip()
    loser = loser_signal.strip()
    if winner == loser or not winner.startswith(_CONDITION_PREFIXES):
        return False
    if not loser.startswith(_CONDITION_PREFIXES):
        return False
    if primary_name not in winner or alternative_name not in loser:
        return False
    if not any(action in winner for action in _MAINTAIN_ACTIONS):
        return False
    if any(action in winner for action in _FLIP_ACTIONS):
        return False
    if not any(action in loser for action in _FLIP_ACTIONS):
        return False
    return not any(action in loser for action in _MAINTAIN_ACTIONS)
