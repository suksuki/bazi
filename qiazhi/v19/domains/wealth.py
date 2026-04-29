from __future__ import annotations

from typing import Any, Dict, List


V19_WEALTH_DOMAIN_VERSION = "v19.wealth_domain.v1"


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _round(value: float) -> float:
    return round(_clamp01(value), 3)


def _ten_god_score(strength: Dict[str, Any], key: str) -> float:
    return _clamp01(float(((strength.get("ten_god_strengths") or {}).get(key) or {}).get("score") or 0.0))


def _wealth_type(profile: Dict[str, float]) -> str:
    if profile["wealth_strength"] < 0.22 and profile["opportunity_score"] < 0.38:
        return "weak_signal"
    if profile["competition_score"] >= 0.68 and profile["risk_score"] >= 0.46:
        return "leakage_risk"
    if profile["liquidity_score"] >= 0.52 and profile["risk_score"] >= 0.38:
        return "volatile"
    if profile["constraint_score"] >= 0.68:
        return "constrained"
    if profile["accumulation_score"] >= 0.5 and profile["stability_score"] >= 0.5 and profile["risk_score"] <= 0.46:
        return "accumulation"
    if profile["stability_score"] >= 0.62 and profile["risk_score"] <= 0.38:
        return "stable"
    return "opportunity" if profile["opportunity_score"] >= profile["risk_score"] else "constrained"


def _evidence(
    evidence_id: str,
    evidence_type: str,
    source_feature_ids: List[str],
    source_effect_ids: List[str],
    metrics: Dict[str, float],
) -> Dict[str, Any]:
    return {
        "evidence_id": evidence_id,
        "evidence_type": evidence_type,
        "layer": "evidence",
        "source_feature_ids": source_feature_ids,
        "source_effect_ids": source_effect_ids,
        "metrics": {key: _round(value) for key, value in metrics.items()},
        "version": V19_WEALTH_DOMAIN_VERSION,
    }


def evaluate_wealth_domain(features: Dict[str, Any], strength: Dict[str, Any], structure: Dict[str, Any]) -> Dict[str, Any]:
    wealth_strength = _ten_god_score(strength, "wealth")
    output_strength = _ten_god_score(strength, "output")
    peer_strength = _ten_god_score(strength, "peer")
    officer_strength = _ten_god_score(strength, "officer")
    body = dict(strength.get("day_master_strength") or {})
    support = _clamp01(float(body.get("support_score") or 0.0))
    pressure = _clamp01(float(body.get("pressure_score") or 0.0))
    body_weak_pressure = _clamp01(pressure - support)
    summary = dict(structure.get("effect_summary") or {})
    activation = _clamp01(float(summary.get("activation_effect") or 0.0))
    structure_risk = _clamp01(float(summary.get("risk_effect") or 0.0))
    stability_raw = float(summary.get("stability_effect") or 0.0)
    structure_stability = _clamp01((stability_raw + 1.0) / 2.0)
    vaults = list(structure.get("vault_effects") or [])
    vault_liquidity = max([float(row.get("liquidity_effect") or 0.0) for row in vaults] or [0.0])
    vault_risk = max([float(row.get("risk_effect") or 0.0) for row in vaults] or [0.0])
    vault_stability = max([float(row.get("stability_effect") or 0.0) for row in vaults] or [0.0])
    opportunity_score = _clamp01(output_strength * 0.34 + wealth_strength * 0.26 + activation * 0.24 + max(0.0, vault_liquidity) * 0.16)
    stability_score = _clamp01(wealth_strength * 0.28 + structure_stability * 0.28 + max(0.0, vault_stability) * 0.18 + support * 0.14 - body_weak_pressure * 0.14)
    risk_score = _clamp01(structure_risk * 0.28 + peer_strength * 0.22 + officer_strength * 0.2 + max(0.0, vault_risk) * 0.16 + body_weak_pressure * 0.14)
    accumulation_score = _clamp01(wealth_strength * 0.38 + stability_score * 0.24 + max(0.0, vault_stability) * 0.22 + max(0.0, -vault_liquidity) * 0.12 - risk_score * 0.12)
    liquidity_score = _clamp01(activation * 0.46 + max(0.0, vault_liquidity) * 0.36 + output_strength * 0.12)
    profile = {
        "wealth_strength": _round(wealth_strength),
        "opportunity_score": _round(opportunity_score),
        "stability_score": _round(stability_score),
        "risk_score": _round(risk_score),
        "accumulation_score": _round(accumulation_score),
        "liquidity_score": _round(liquidity_score),
        "competition_score": _round(peer_strength),
        "constraint_score": _round(officer_strength),
    }
    wealth_type = _wealth_type(profile)
    profile["wealth_type"] = wealth_type
    feature_ids = [row["feature_id"] for row in features.get("features", [])]
    vault_effect_ids = [row["effect_id"] for row in vaults]
    evidence = [
        _evidence("wealth.evidence.strength", "wealth_strength_evidence", feature_ids, [], {"wealth_strength": wealth_strength, "accumulation_score": accumulation_score}),
        _evidence("wealth.evidence.output", "output_conversion_evidence", feature_ids, [], {"output_strength": output_strength, "opportunity_score": opportunity_score}),
        _evidence("wealth.evidence.structure", "structure_wealth_evidence", [], [row["effect_id"] for row in structure.get("relation_effects", [])], {"stability_score": stability_score, "risk_score": risk_score, "liquidity_score": liquidity_score}),
    ]
    if vaults:
        evidence.append(_evidence("wealth.evidence.vault", "wealth_vault_evidence", [], vault_effect_ids, {"accumulation_score": accumulation_score, "liquidity_score": liquidity_score, "risk_score": risk_score}))
    if peer_strength > 0:
        evidence.append(_evidence("wealth.evidence.peer", "peer_competition_evidence", feature_ids, [], {"competition_score": peer_strength, "risk_score": risk_score}))
    if officer_strength > 0:
        evidence.append(_evidence("wealth.evidence.constraint", "constraint_evidence", feature_ids, [], {"constraint_score": officer_strength, "risk_score": risk_score}))
    return {
        "version": V19_WEALTH_DOMAIN_VERSION,
        "chart_id": features["chart_id"],
        "wealth_profile": profile,
        "evidence": evidence,
        "guardrails": ["DOMAIN_AFTER_STRUCTURE", "EVIDENCE_NOT_CONCLUSION", "NO_USER_OUTPUT", "NO_LLM_REASONING"],
    }
