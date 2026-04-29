from __future__ import annotations

from typing import Any, Dict, List

from v19.core.inference_schema import INFERENCE_SCHEMA_VERSION, TEN_GOD_KEYS


V19_CORE_INFERENCE_VERSION = "v19.core_bazi_inference.v2"


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _round(value: float) -> float:
    return round(float(value), 3)


def _score(strength: Dict[str, Any], ten_god: str) -> float:
    return float(((strength.get("ten_god_strengths") or {}).get(ten_god) or {}).get("score") or 0.0)


def _raw(strength: Dict[str, Any], ten_god: str) -> float:
    return float(((strength.get("ten_god_strengths") or {}).get(ten_god) or {}).get("raw_weight") or 0.0)


def _strength_level(score: float, raw_weight: float) -> str:
    if raw_weight <= 0:
        return "none"
    if score >= 0.72:
        return "strong"
    if score >= 0.34:
        return "medium"
    return "weak"


def _activity_level(score: float, raw_weight: float) -> str:
    if raw_weight <= 0:
        return "inactive"
    if score >= 0.75:
        return "high"
    if score >= 0.35:
        return "active"
    return "low"


def _presence(score: float, raw_weight: float) -> str:
    if raw_weight <= 0:
        return "absent"
    if score >= 0.75:
        return "dominant"
    if score >= 0.2:
        return "present"
    return "latent"


def _severity(score: float) -> str:
    if score >= 0.67:
        return "high"
    if score >= 0.34:
        return "medium"
    return "low"


def _direction(left_score: float, right_score: float, left_direction: str, right_direction: str, balanced_direction: str) -> str:
    if left_score >= right_score + 0.12:
        return left_direction
    if right_score >= left_score + 0.12:
        return right_direction
    return balanced_direction


def _day_master_state(strength: Dict[str, Any]) -> Dict[str, Any]:
    strength_info = dict(strength.get("day_master_strength") or {})
    support = float(strength_info.get("support_score") or 0.0)
    pressure = float(strength_info.get("pressure_score") or 0.0)
    delta = support - pressure
    tendency = "balanced"
    if pressure >= 0.72 and support <= 0.28:
        tendency = "following_tendency_possible"
    elif delta >= 0.3:
        tendency = "strong"
    elif delta >= 0.12:
        tendency = "leaning_strong"
    elif delta <= -0.3:
        tendency = "weak"
    elif delta <= -0.12:
        tendency = "leaning_weak"
    confidence = _clamp01(0.56 + abs(delta) * 0.9)
    return {
        "tendency": tendency,
        "confidence": _round(confidence),
        "sources": ["root_strength", "month_command", "support_pressure"],
    }


def _ten_god_structure(strength: Dict[str, Any]) -> Dict[str, Any]:
    structure: Dict[str, Dict[str, Any]] = {}
    for ten_god in TEN_GOD_KEYS:
        score = _score(strength, ten_god)
        raw_weight = _raw(strength, ten_god)
        structure[ten_god] = {
            "presence": _presence(score, raw_weight),
            "strength": _strength_level(score, raw_weight),
            "activity": _activity_level(score, raw_weight),
            "sources": ["ten_god_mapping", "hidden_stems", "ten_god_weights"],
        }
    return structure


def _energy_flow(strength: Dict[str, Any]) -> List[Dict[str, Any]]:
    flow_specs = [
        ("seal", "peer", "support"),
        ("peer", "output", "drain"),
        ("output", "wealth", "generate"),
        ("wealth", "officer", "generate"),
        ("officer", "seal", "generate"),
    ]
    flows: List[Dict[str, Any]] = []
    for source, target, flow_type in flow_specs:
        source_score = _score(strength, source)
        target_score = _score(strength, target)
        source_raw = _raw(strength, source)
        target_raw = _raw(strength, target)
        if _presence(source_score, source_raw) not in {"present", "dominant"}:
            continue
        if _presence(target_score, target_raw) not in {"present", "dominant"}:
            continue
        path_score = min(source_score, target_score)
        flows.append(
            {
                "from": source,
                "to": target,
                "type": flow_type,
                "strength": _strength_level(path_score, min(source_raw, target_raw)),
                "sources": ["ten_god_weights", "support_pressure"],
            }
        )
    return flows


def _relation_counts(structure: Dict[str, Any]) -> Dict[str, int]:
    counts = {"clash": 0, "combination": 0, "harm": 0}
    for effect in structure.get("relation_effects", []):
        relation_type = str(effect.get("relation_type") or "")
        if relation_type in counts:
            counts[relation_type] += 1
    return counts


def _structural_stability(structure: Dict[str, Any]) -> Dict[str, Any]:
    summary = dict(structure.get("effect_summary") or {})
    stability = float(summary.get("stability_effect") or 0.0)
    activation = float(summary.get("activation_effect") or 0.0)
    risk = float(summary.get("risk_effect") or 0.0)
    relation_counts = _relation_counts(structure)
    signals: List[str] = []
    sources = ["relation_hits", "structure_effects"]

    for signal in ("clash", "combination", "harm"):
        if relation_counts.get(signal, 0) > 0:
            signals.append(signal)

    for effect in structure.get("vault_effects", []):
        vault_state = str(effect.get("vault_state") or "")
        if vault_state == "opened_by_clash":
            signals.append("vault_opened")
        elif vault_state == "locked_by_combination":
            signals.append("vault_locked")
        elif vault_state in {"closed", "closed_storable", "closed_inactive"}:
            signals.append("vault_closed")
    if structure.get("vault_effects"):
        sources.append("vault_effects")

    if structure.get("flow_effects"):
        signals.append("flow_activation")
        sources.append("flow_effects")

    if relation_counts.get("clash", 0) > 0 and relation_counts.get("combination", 0) > 0:
        signals.append("mixed_clash_and_combination")

    signals = sorted(set(signals)) or ["none"]
    if "mixed_clash_and_combination" in signals:
        state = "conflicted"
    elif risk >= 0.65 or stability <= -0.25:
        state = "unstable"
    elif "vault_locked" in signals:
        state = "locked"
    elif activation >= 0.3:
        state = "activated"
    elif stability >= 0.25:
        state = "stable"
    else:
        state = "mixed"

    return {"state": state, "signals": signals, "sources": sorted(set(sources))}


def _internal_conflicts(strength: Dict[str, Any], structure: Dict[str, Any]) -> List[Dict[str, Any]]:
    conflicts: List[Dict[str, Any]] = []
    relation_counts = _relation_counts(structure)
    support = float(((strength.get("day_master_strength") or {}).get("support_score")) or 0.0)
    pressure = float(((strength.get("day_master_strength") or {}).get("pressure_score")) or 0.0)

    if _score(strength, "output") >= 0.5 and _score(strength, "officer") >= 0.5:
        output_score = _score(strength, "output")
        officer_score = _score(strength, "officer")
        conflicts.append(
            {
                "type": "output_vs_officer",
                "direction": _direction(
                    output_score,
                    officer_score,
                    "output_challenges_officer",
                    "officer_suppresses_output",
                    "balanced_output_officer_tension",
                ),
                "severity": _severity(min(output_score, officer_score)),
                "sources": ["ten_god_weights", "support_pressure"],
            }
        )
    if _score(strength, "peer") >= 0.5 and _score(strength, "wealth") >= 0.5:
        peer_score = _score(strength, "peer")
        wealth_score = _score(strength, "wealth")
        conflicts.append(
            {
                "type": "peer_vs_wealth",
                "direction": _direction(
                    peer_score,
                    wealth_score,
                    "peer_overwhelms_wealth",
                    "wealth_resists_peer",
                    "balanced_peer_wealth_tension",
                ),
                "severity": _severity(min(peer_score, wealth_score)),
                "sources": ["ten_god_weights", "support_pressure"],
            }
        )
    if _score(strength, "seal") >= 0.5 and _score(strength, "output") >= 0.5:
        seal_score = _score(strength, "seal")
        output_score = _score(strength, "output")
        conflicts.append(
            {
                "type": "seal_vs_output",
                "direction": _direction(
                    seal_score,
                    output_score,
                    "seal_blocks_output",
                    "output_drains_seal",
                    "balanced_seal_output_tension",
                ),
                "severity": _severity(min(seal_score, output_score)),
                "sources": ["ten_god_weights", "support_pressure"],
            }
        )
    if relation_counts.get("clash", 0) > 0 and relation_counts.get("combination", 0) > 0:
        conflicts.append(
            {
                "type": "clash_vs_combination",
                "direction": "clash_disrupts_combination"
                if relation_counts.get("clash", 0) >= relation_counts.get("combination", 0)
                else "combination_locks_clash_activation",
                "severity": "high",
                "sources": ["relation_hits", "structure_effects"],
            }
        )
    if abs(support - pressure) >= 0.18:
        conflicts.append(
            {
                "type": "support_vs_pressure",
                "direction": "support_over_pressure" if support > pressure else "pressure_over_support",
                "severity": _severity(abs(support - pressure)),
                "sources": ["root_strength", "month_command", "support_pressure"],
            }
        )
    return conflicts


def _uncertainty_sources(strength: Dict[str, Any], structure: Dict[str, Any]) -> List[Dict[str, Any]]:
    uncertainties: List[Dict[str, Any]] = [
        {"type": "requires_domain_mapping", "sources": ["structure_effects"]},
    ]
    relation_counts = _relation_counts(structure)
    scores = [_score(strength, ten_god) for ten_god in TEN_GOD_KEYS]
    support = float(((strength.get("day_master_strength") or {}).get("support_score")) or 0.0)
    pressure = float(((strength.get("day_master_strength") or {}).get("pressure_score")) or 0.0)

    if not structure.get("flow_effects"):
        uncertainties.append({"type": "missing_luck_flow", "sources": ["flow_effects"]})
    if relation_counts.get("clash", 0) > 0 and relation_counts.get("combination", 0) > 0:
        uncertainties.append({"type": "mixed_clash_and_combination", "sources": ["relation_hits", "structure_effects"]})
    if _score(strength, "unknown") > 0:
        uncertainties.append({"type": "unknown_mapping", "sources": ["ten_god_mapping"]})
    if max(scores or [0.0]) < 0.35 or abs(support - pressure) < 0.08:
        uncertainties.append({"type": "weak_signal", "sources": ["ten_god_weights", "support_pressure"]})
    if pressure >= 0.72 and support <= 0.28:
        uncertainties.append({"type": "following_tendency_possible", "sources": ["root_strength", "month_command", "support_pressure"]})
    if structure.get("effect_summary", {}).get("risk_effect", 0.0) >= 0.65:
        uncertainties.append({"type": "ambiguous_structure", "sources": ["relation_hits", "structure_effects"]})

    deduped: List[Dict[str, Any]] = []
    seen = set()
    for item in uncertainties:
        if item["type"] in seen:
            continue
        seen.add(item["type"])
        deduped.append(item)
    return deduped


def infer_core_bazi(features: Dict[str, Any], strength: Dict[str, Any], structure: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "version": V19_CORE_INFERENCE_VERSION,
        "schema_version": INFERENCE_SCHEMA_VERSION,
        "chart_id": features["chart_id"],
        "day_master_state": _day_master_state(strength),
        "ten_god_structure": _ten_god_structure(strength),
        "energy_flow": _energy_flow(strength),
        "structural_stability": _structural_stability(structure),
        "internal_conflicts": _internal_conflicts(strength, structure),
        "uncertainty_sources": _uncertainty_sources(strength, structure),
        "guardrails": [
            "CORE_BAZI_INFERENCE_LANGUAGE",
            "FINITE_VALUE_SETS_ONLY",
            "SOURCE_BOUND_SIGNALS",
            "NO_DOMAIN_CONCLUSION",
            "NO_NARRATIVE",
            "NO_LLM_REASONING",
        ],
    }
