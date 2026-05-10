from __future__ import annotations

from v20.core.constants import GENERATES
from v20.core.schemas import ChartFacts, CoreInference

CORE_INFERENCE_VERSION = "v20.core_inference.v1"
VISIBLE_SUPPORT_WEIGHT = 0.18
VISIBLE_PRESSURE_WEIGHT = 0.12
HIDDEN_SUPPORT_WEIGHT = 0.08
HIDDEN_PRESSURE_WEIGHT = 0.05
RELATION_PRESSURE_WEIGHT = 0.03
RELATION_PRESSURE_CAP = 0.2
SUPPORTED_CAPACITY_DELTA = 0.22
NEEDS_SUPPORT_DELTA = -0.12


def infer_core(facts: ChartFacts) -> CoreInference:
    day_element = facts.day_master_element
    supporting_element = _supporting_element(day_element)
    support_score = 0.0
    pressure_score = 0.0
    uncertainty: list[str] = []

    for row in facts.visible_ten_gods:
        if row.element == day_element or row.element == supporting_element:
            support_score += VISIBLE_SUPPORT_WEIGHT
        else:
            pressure_score += VISIBLE_PRESSURE_WEIGHT
    for row in facts.hidden_ten_gods:
        if row.element == day_element or row.element == supporting_element:
            support_score += HIDDEN_SUPPORT_WEIGHT * row.weight
        else:
            pressure_score += HIDDEN_PRESSURE_WEIGHT * row.weight

    relation_count = len(facts.relation_hits)
    if relation_count:
        uncertainty.append("branch_relations_require_layer_review")
        pressure_score += min(RELATION_PRESSURE_CAP, relation_count * RELATION_PRESSURE_WEIGHT)
    if facts.vault_branches:
        uncertainty.append("vault_branches_require_storage_boundary")

    support_score = _clamp(support_score)
    pressure_score = _clamp(pressure_score)
    capacity = _capacity(support_score, pressure_score)
    return CoreInference(
        version=CORE_INFERENCE_VERSION,
        day_master_capacity=capacity,
        support_score=round(support_score, 3),
        pressure_score=round(pressure_score, 3),
        visible_ten_god_count=len(facts.visible_ten_gods),
        hidden_ten_god_count=len(facts.hidden_ten_gods),
        relation_count=relation_count,
        uncertainty_sources=tuple(uncertainty),
    )


def _supporting_element(day_element: str) -> str:
    for element, generated in GENERATES.items():
        if generated == day_element:
            return element
    return ""


def _capacity(support_score: float, pressure_score: float) -> str:
    delta = support_score - pressure_score
    if delta >= SUPPORTED_CAPACITY_DELTA:
        return "supported_capacity"
    if delta <= NEEDS_SUPPORT_DELTA:
        return "capacity_needs_support"
    return "borderline_capacity"


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))
