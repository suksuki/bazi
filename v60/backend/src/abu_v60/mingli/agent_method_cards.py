from __future__ import annotations

from typing import Protocol

MINGLI_AGENT_ADJUDICATION_VERSION = "v60.mingli-agent-adjudication.003"
FALLBACK_METHOD_CARD_REF = "FALLBACK_WHOLE_CHART"

_PATTERN_CHECKS: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {
    "bazi.mechanism.output-to-pressure@1": (
        (
            "OUTPUT_SOURCE_AVAILABILITY",
            "OFFICIAL_KILLING_ROLE_POSITIONED",
            "DAY_MASTER_CAPACITY",
            "VISIBLE_HIDDEN_REACHABILITY",
            "RESOURCE_OR_OTHER_BLOCKER_RESOLUTION",
        ),
        ("SOURCE_AND_TARGET_SAME_LAYER",),
    ),
    "bazi.mechanism.output-to-wealth@1": (
        (
            "OUTPUT_SOURCE_AVAILABILITY",
            "WEALTH_TARGET_REACHABILITY",
            "DAY_MASTER_CAPACITY",
            "RESOURCE_SUPPRESSION_RESOLUTION",
            "PEER_COMPETITION_RESOLUTION",
        ),
        (),
    ),
    "bazi.mechanism.pressure-resource-self@1": (
        (
            "PRESSURE_SOURCE_AVAILABILITY",
            "RESOURCE_BRIDGE_REACHABILITY",
            "SELF_TARGET_CAPACITY",
            "COMPETING_PATH_RESOLUTION",
        ),
        (
            "SOURCE_BRIDGE_SAME_LAYER",
            "BRIDGE_TARGET_SAME_LAYER",
        ),
    ),
    "bazi.mechanism.wealth-to-pressure@1": (
        (
            "WEALTH_SOURCE_AVAILABILITY",
            "PRESSURE_TARGET_REACHABILITY",
            "DAY_MASTER_CAPACITY",
            "VISIBLE_HIDDEN_REACHABILITY",
            "COMPETING_PATH_RESOLUTION",
        ),
        (),
    ),
    "bazi.mechanism.resource-to-self@1": (
        (
            "RESOURCE_SOURCE_AVAILABILITY",
            "SELF_TARGET_REACHABILITY",
            "DAY_MASTER_CAPACITY",
            "VISIBLE_HIDDEN_REACHABILITY",
            "OUTPUT_OR_WEALTH_INTERFERENCE_RESOLUTION",
        ),
        (),
    ),
}

_FALLBACK_BLOCKING_CHECKS = (
    "MONTH_COMMAND_AND_SEASON",
    "ROOT_PEER_RESOURCE_ORDER",
    "DRAIN_WEALTH_PRESSURE_BALANCE",
    "RESCUE_AND_BLOCKERS",
)
_FALLBACK_CONDITIONING_CHECKS = ("WHOLE_CHART_EXPLANATORY_COVERAGE",)


class MechanismContext(Protocol):
    pattern_ref: str
    label: str
    evidence_id: str
    blocker_codes: tuple[str, ...]
    role_summary: tuple[str, ...]


def mechanism_method_card(item: MechanismContext) -> dict[str, object]:
    """Return the exact checks required before one candidate can be selected."""

    blocking, conditioning = _PATTERN_CHECKS.get(
        item.pattern_ref,
        (
            ("SOURCE", "TRANSFORMATION", "TARGET", "CAPACITY"),
            ("BLOCKERS",),
        ),
    )
    required = (*blocking, *conditioning)
    return {
        "method_card_ref": item.evidence_id,
        "pattern_ref": item.pattern_ref,
        "label": item.label,
        "required_checks": required,
        "blocking_checks": blocking,
        "conditioning_checks": conditioning,
        "fact_locks": {
            "role_manifestation": item.role_summary,
            "observed_blocker_codes": item.blocker_codes,
            "visibility_rule": ("明干数量才表示透出；藏干数量不得写成透出。"),
        },
        "observed_blocker_codes": item.blocker_codes,
        "status": "PROFESSIONAL_RULING_REQUIRED",
    }


def fallback_hypothesis_method_card() -> dict[str, object]:
    """Keep charts with zero or one mechanism candidate fully readable."""

    required = (*_FALLBACK_BLOCKING_CHECKS, *_FALLBACK_CONDITIONING_CHECKS)
    return {
        "method_card_ref": FALLBACK_METHOD_CARD_REF,
        "label": "月令与整盘主线解释",
        "required_checks": required,
        "blocking_checks": _FALLBACK_BLOCKING_CHECKS,
        "conditioning_checks": _FALLBACK_CONDITIONING_CHECKS,
        "status": "PROFESSIONAL_RULING_REQUIRED",
    }


def method_card_catalog(items: tuple[MechanismContext, ...]) -> dict[str, dict[str, object]]:
    cards = {
        str(card["method_card_ref"]): card
        for card in (mechanism_method_card(item) for item in items)
    }
    fallback = fallback_hypothesis_method_card()
    cards[FALLBACK_METHOD_CARD_REF] = fallback
    return cards
