from __future__ import annotations

from pydantic import Field

from v30.contracts import FeatureEvidence, V30Model
from v30.knowledge import KnowledgeRulePortraitSignal


class MechanismPath(V30Model):
    mechanism_id: str
    label: str
    path_state: str
    score: float
    evidence_ids: list[str] = Field(default_factory=list)
    signal_ids: list[str] = Field(default_factory=list)
    missing_context: list[str] = Field(default_factory=list)
    boundary: str


def build_mechanism_paths(
    evidence: list[FeatureEvidence],
    signals: list[KnowledgeRulePortraitSignal],
    structure_policy: dict[str, object] | None = None,
) -> list[MechanismPath]:
    rows: list[MechanismPath] = []
    weights = _weights(structure_policy)
    evidence_by_support = _evidence_by_support(evidence)
    signal_by_type = {signal.signal_type: signal for signal in signals}
    if "ten_god_visibility" in evidence_by_support:
        rows.append(
            MechanismPath(
                mechanism_id="mechanism.ten_god_visibility_context",
                label="Visible ten-god context is available for structure review.",
                path_state="partial",
                score=_weighted_score(
                    "mechanism.ten_god_visibility_context",
                    _score(evidence_by_support["ten_god_visibility"], signal_by_type.get("knowledge")),
                    weights,
                ),
                evidence_ids=[row.evidence_id for row in evidence_by_support["ten_god_visibility"]],
                signal_ids=_signal_ids(signal_by_type.get("knowledge")),
                boundary="mechanism_context_not_personality_verdict",
            )
        )
    if "useful_god_candidate_question" in evidence_by_support:
        rows.append(
            MechanismPath(
                mechanism_id="mechanism.useful_god_candidate_gate",
                label="Useful-god candidate gate is active and blocks fixed verdicts.",
                path_state="blocked",
                score=_weighted_score(
                    "mechanism.useful_god_candidate_gate",
                    _score(evidence_by_support["useful_god_candidate_question"], signal_by_type.get("rule")),
                    weights,
                ),
                evidence_ids=[row.evidence_id for row in evidence_by_support["useful_god_candidate_question"]],
                signal_ids=_signal_ids(signal_by_type.get("rule")),
                missing_context=["complete_evidence_path_review"],
                boundary="mechanism_gate_blocks_fixed_useful_god",
            )
        )
    if "hidden_stem_context" in evidence_by_support:
        rows.append(
            MechanismPath(
                mechanism_id="mechanism.hidden_factor_dialogue_probe",
                label="Hidden factor path requires dialogue calibration.",
                path_state="partial",
                score=_weighted_score(
                    "mechanism.hidden_factor_dialogue_probe",
                    _score(evidence_by_support["hidden_stem_context"], signal_by_type.get("portrait")),
                    weights,
                ),
                evidence_ids=[row.evidence_id for row in evidence_by_support["hidden_stem_context"]],
                signal_ids=_signal_ids(signal_by_type.get("portrait")),
                missing_context=["special_event_year_or_repeated_state_feedback"],
                boundary="mechanism_hypothesis_requires_feedback",
            )
        )
    if "structure_dynamic_review" in evidence_by_support:
        rows.append(
            MechanismPath(
                mechanism_id="mechanism.branch_relation_dynamic_review",
                label="Branch relation path requires dynamic review.",
                path_state="volatile",
                score=_weighted_score(
                    "mechanism.branch_relation_dynamic_review",
                    _score(evidence_by_support["structure_dynamic_review"], None),
                    weights,
                ),
                evidence_ids=[row.evidence_id for row in evidence_by_support["structure_dynamic_review"]],
                boundary="mechanism_dynamic_relation_not_single_factor_verdict",
            )
        )
    return sorted(rows, key=lambda row: (-row.score, row.mechanism_id))


def mechanism_graph_nodes(paths: list[MechanismPath]) -> list[dict[str, object]]:
    return [
        {
            "node_id": path.mechanism_id,
            "kind": "mechanism_path",
            "label": path.label,
            "path_state": path.path_state,
            "score": path.score,
            "boundary": path.boundary,
        }
        for path in paths
    ]


def mechanism_graph_edges(paths: list[MechanismPath]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for path in paths:
        for evidence_id in path.evidence_ids:
            rows.append({"from": evidence_id, "to": path.mechanism_id, "relation": "supports_mechanism"})
        for signal_id in path.signal_ids:
            rows.append({"from": signal_id, "to": path.mechanism_id, "relation": "calibrates_mechanism"})
    return rows


def _evidence_by_support(evidence: list[FeatureEvidence]) -> dict[str, list[FeatureEvidence]]:
    rows: dict[str, list[FeatureEvidence]] = {}
    for item in evidence:
        for support in item.supports:
            rows.setdefault(support, []).append(item)
    return rows


def _signal_ids(signal: KnowledgeRulePortraitSignal | None) -> list[str]:
    return [signal.signal_id] if signal is not None else []


def _score(evidence: list[FeatureEvidence], signal: KnowledgeRulePortraitSignal | None) -> float:
    evidence_score = sum(row.confidence for row in evidence) / max(1, len(evidence))
    signal_bonus = 0.08 if signal is not None else 0.0
    return round(min(1.0, evidence_score + signal_bonus), 3)


def _weights(structure_policy: dict[str, object] | None) -> dict[str, float]:
    payload = structure_policy or {}
    raw_weights = payload.get("weights", {})
    if not isinstance(raw_weights, dict):
        return {}
    rows: dict[str, float] = {}
    for key, value in raw_weights.items():
        try:
            rows[str(key)] = float(value)
        except (TypeError, ValueError):
            continue
    return rows


def _weighted_score(mechanism_id: str, base_score: float, weights: dict[str, float]) -> float:
    weight = weights.get(mechanism_id, weights.get("*", 1.0))
    return round(max(0.0, min(1.0, base_score * weight)), 3)
