from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from v20.core.constants import CONTROLS, GENERATES
from v20.core.elements import element_distribution
from v20.core.schemas import ChartFacts, CoreInference

USEFUL_GOD_CANDIDATE_VERSION = "v20.useful_god_candidates.v1"
BASE_CONFIDENCE = {
    "resource_support": 0.42,
    "peer_stabilizer": 0.38,
    "output_release": 0.4,
    "wealth_channel": 0.37,
    "authority_constraint_review": 0.34,
    "support_vs_release_review": 0.39,
    "output_pressure_review": 0.35,
    "weak_element_gap_review": 0.31,
}
ELEMENT_AMOUNT_CONFIDENCE_WEIGHT = 0.025
ELEMENT_AMOUNT_CONFIDENCE_CAP = 0.1
SUPPORT_PRESSURE_DELTA_CONFIDENCE_WEIGHT = 0.28
SUPPORT_PRESSURE_DELTA_CONFIDENCE_CAP = 0.12
MIN_CANDIDATE_CONFIDENCE = 0.2
MAX_CANDIDATE_CONFIDENCE = 0.78


@dataclass(frozen=True)
class UsefulGodCandidate:
    path_key: str
    element: str
    path_type: str
    rationale: str
    evidence_refs: tuple[str, ...]
    confidence: float
    status: str = "candidate_only"
    guardrails: tuple[str, ...] = (
        "USEFUL_GOD_IS_CANDIDATE_PATH",
        "NO_FIXED_FAVORABLE_UNFAVORABLE_VERDICT",
        "REQUIRES_RULE_GRAPH_AND_EVIDENCE_REVIEW",
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def derive_useful_god_candidates(facts: ChartFacts, inference: CoreInference) -> tuple[UsefulGodCandidate, ...]:
    day_element = facts.day_master_element
    if not day_element:
        return ()
    distribution = element_distribution(facts)
    support_element = _generating_element(day_element)
    peer_element = day_element
    output_element = GENERATES.get(day_element, "")
    wealth_element = CONTROLS.get(day_element, "")
    authority_element = _controlling_element(day_element)

    rows: list[UsefulGodCandidate] = []
    if inference.day_master_capacity == "capacity_needs_support":
        rows.append(
            _candidate(
                "resource_support",
                support_element,
                "support",
                "Resource/support path is opened because capacity evidence needs support review.",
                facts,
                inference,
                distribution,
                BASE_CONFIDENCE["resource_support"],
            )
        )
        rows.append(
            _candidate(
                "peer_stabilizer",
                peer_element,
                "support",
                "Peer/day-element path is opened as a stabilizing candidate, not a verdict.",
                facts,
                inference,
                distribution,
                BASE_CONFIDENCE["peer_stabilizer"],
            )
        )
    elif inference.day_master_capacity == "supported_capacity":
        rows.append(
            _candidate(
                "output_release",
                output_element,
                "release",
                "Output path is opened because supported capacity can be reviewed through expression and release.",
                facts,
                inference,
                distribution,
                BASE_CONFIDENCE["output_release"],
            )
        )
        rows.append(
            _candidate(
                "wealth_channel",
                wealth_element,
                "channel",
                "Wealth path is opened as a structural channel candidate after capacity support is present.",
                facts,
                inference,
                distribution,
                BASE_CONFIDENCE["wealth_channel"],
            )
        )
        rows.append(
            _candidate(
                "authority_constraint_review",
                authority_element,
                "constraint",
                "Authority/constraint path is opened for review, with branch and ten-god evidence still required.",
                facts,
                inference,
                distribution,
                BASE_CONFIDENCE["authority_constraint_review"],
            )
        )
    else:
        rows.append(
            _candidate(
                "support_vs_release_review",
                support_element,
                "arbitration",
                "Borderline capacity opens support-versus-release arbitration before any useful-god decision.",
                facts,
                inference,
                distribution,
                BASE_CONFIDENCE["support_vs_release_review"],
            )
        )
        rows.append(
            _candidate(
                "output_pressure_review",
                output_element,
                "arbitration",
                "Borderline capacity also opens an output/pressure review path.",
                facts,
                inference,
                distribution,
                BASE_CONFIDENCE["output_pressure_review"],
            )
        )

    weakest = _weakest_element(distribution)
    if weakest and weakest not in {row.element for row in rows}:
        rows.append(
            _candidate(
                "weak_element_gap_review",
                weakest,
                "evidence_gap",
                "Weakest element is added as an evidence-gap review, not as an automatic remedy.",
                facts,
                inference,
                distribution,
                BASE_CONFIDENCE["weak_element_gap_review"],
            )
        )
    deduped = _dedupe(rows)
    return tuple(sorted(deduped, key=lambda row: (row.confidence, row.path_key), reverse=True))


def _candidate(
    path_key: str,
    element: str,
    path_type: str,
    rationale: str,
    facts: ChartFacts,
    inference: CoreInference,
    distribution: dict[str, float],
    base_confidence: float,
) -> UsefulGodCandidate:
    amount = distribution.get(element, 0.0)
    confidence = _candidate_confidence(base_confidence, amount, inference)
    return UsefulGodCandidate(
        path_key=path_key,
        element=element,
        path_type=path_type,
        rationale=rationale,
        evidence_refs=(
            f"day_element:{facts.day_master_element}",
            f"capacity:{inference.day_master_capacity}",
            f"element:{element}:{amount}",
            f"support_pressure_delta:{round(inference.support_score - inference.pressure_score, 3)}",
        ),
        confidence=confidence,
    )


def _candidate_confidence(base: float, element_amount: float, inference: CoreInference) -> float:
    delta = abs(inference.support_score - inference.pressure_score)
    evidence_bonus = min(ELEMENT_AMOUNT_CONFIDENCE_CAP, element_amount * ELEMENT_AMOUNT_CONFIDENCE_WEIGHT) + min(
        SUPPORT_PRESSURE_DELTA_CONFIDENCE_CAP,
        delta * SUPPORT_PRESSURE_DELTA_CONFIDENCE_WEIGHT,
    )
    return round(max(MIN_CANDIDATE_CONFIDENCE, min(MAX_CANDIDATE_CONFIDENCE, base + evidence_bonus)), 3)


def _generating_element(target: str) -> str:
    for element, generated in GENERATES.items():
        if generated == target:
            return element
    return ""


def _controlling_element(target: str) -> str:
    for element, controlled in CONTROLS.items():
        if controlled == target:
            return element
    return ""


def _weakest_element(distribution: dict[str, float]) -> str:
    if not distribution:
        return ""
    return min(distribution.items(), key=lambda row: (row[1], row[0]))[0]


def _dedupe(rows: list[UsefulGodCandidate]) -> list[UsefulGodCandidate]:
    out: dict[tuple[str, str], UsefulGodCandidate] = {}
    for row in rows:
        key = (row.path_key, row.element)
        current = out.get(key)
        if current is None or row.confidence > current.confidence:
            out[key] = row
    return list(out.values())
