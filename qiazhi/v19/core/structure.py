from __future__ import annotations

from typing import Any, Dict, List


V19_STRUCTURE_VERSION = "v19.core_structure.v1"


def _clamp_signed(value: float) -> float:
    return max(-1.0, min(1.0, float(value)))


def _round_signed(value: float) -> float:
    return round(_clamp_signed(value), 3)


def _feature_rows(features: Dict[str, Any], feature_type: str) -> List[Dict[str, Any]]:
    return [row for row in features.get("features", []) if row.get("feature_type") == feature_type]


def evaluate_structure(features: Dict[str, Any], strength: Dict[str, Any]) -> Dict[str, Any]:
    relations = _feature_rows(features, "branch_relation_fact")
    vault_facts = _feature_rows(features, "vault_fact")
    flow_facts = _feature_rows(features, "flow_pillar_fact")
    relation_effects: List[Dict[str, Any]] = []
    stability_effect = 0.0
    activation_effect = 0.0
    risk_effect = 0.0
    for relation in relations:
        payload = dict(relation.get("payload") or {})
        relation_type = str(payload.get("relation_type") or "")
        if relation_type == "combination":
            stability_delta = 0.22
            activation_delta = -0.04
            risk_delta = 0.08
        elif relation_type == "clash":
            stability_delta = -0.34
            activation_delta = 0.38
            risk_delta = 0.3
        else:
            stability_delta = -0.2
            activation_delta = 0.12
            risk_delta = 0.26
        stability_effect += stability_delta
        activation_effect += activation_delta
        risk_effect += risk_delta
        relation_effects.append(
            {
                "effect_id": relation["feature_id"].replace("branch_relation", "structure_relation"),
                "source_feature_id": relation["feature_id"],
                "relation_type": relation_type,
                "stability_effect": _round_signed(stability_delta),
                "activation_effect": _round_signed(activation_delta),
                "risk_effect": _round_signed(risk_delta),
            }
        )

    vault_effects: List[Dict[str, Any]] = []
    relation_types = {str((row.get("payload") or {}).get("relation_type") or "") for row in relations}
    for vault in vault_facts:
        payload = dict(vault.get("payload") or {})
        if "clash" in relation_types and "combination" in relation_types:
            vault_state = "conflicted"
            vault_stability = -0.16
            vault_activation = 0.28
            vault_risk = 0.42
            vault_liquidity = 0.24
        elif "clash" in relation_types:
            vault_state = "opened_by_clash"
            vault_stability = -0.22
            vault_activation = 0.42
            vault_risk = 0.38
            vault_liquidity = 0.48
        elif "combination" in relation_types:
            vault_state = "locked_by_combination"
            vault_stability = 0.28
            vault_activation = -0.16
            vault_risk = 0.16
            vault_liquidity = -0.24
        else:
            vault_state = "closed_storable" if payload.get("contains_wealth") else "closed_inactive"
            vault_stability = 0.2 if payload.get("contains_wealth") else 0.08
            vault_activation = 0.0
            vault_risk = 0.1
            vault_liquidity = -0.08
        vault_effects.append(
            {
                "effect_id": vault["feature_id"].replace("vault", "vault_effect"),
                "source_feature_id": vault["feature_id"],
                "vault_branch": payload.get("branch"),
                "vault_state": vault_state,
                "contains_wealth": bool(payload.get("contains_wealth")),
                "stability_effect": _round_signed(vault_stability),
                "activation_effect": _round_signed(vault_activation),
                "risk_effect": round(max(0.0, min(1.0, vault_risk)), 3),
                "liquidity_effect": _round_signed(vault_liquidity),
            }
        )
        stability_effect += vault_stability
        activation_effect += vault_activation
        risk_effect += vault_risk

    flow_effects: List[Dict[str, Any]] = []
    for flow in flow_facts:
        payload = dict(flow.get("payload") or {})
        hidden = payload.get("hidden_ten_gods") or []
        stem_ten_god = str(payload.get("stem_ten_god") or "")
        activates_wealth = stem_ten_god == "wealth" or "wealth" in hidden
        activation_delta = 0.32 if activates_wealth else 0.12
        flow_effects.append(
            {
                "effect_id": flow["feature_id"].replace(".", "_") + ".effect",
                "source_feature_id": flow["feature_id"],
                "flow_type": payload.get("flow_type"),
                "activates_wealth": activates_wealth,
                "activation_effect": round(activation_delta, 3),
            }
        )
        activation_effect += activation_delta

    return {
        "version": V19_STRUCTURE_VERSION,
        "chart_id": features["chart_id"],
        "effect_summary": {
            "stability_effect": _round_signed(stability_effect),
            "activation_effect": _round_signed(activation_effect),
            "risk_effect": round(max(0.0, min(1.0, risk_effect)), 3),
        },
        "relation_effects": relation_effects,
        "vault_effects": vault_effects,
        "flow_effects": flow_effects,
        "guardrails": ["STRUCTURE_BEFORE_DOMAIN", "NO_THEME_CONCLUSION", "NO_USER_OUTPUT"],
    }
