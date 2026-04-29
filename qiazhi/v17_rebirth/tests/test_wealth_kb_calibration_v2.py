from __future__ import annotations

import json

import pytest

from v17_rebirth.backend.services import core_bazi_wealth_domain as wealth_domain


def _core(case_id: str) -> dict:
    return {"bundle_id": f"core_feature_bundle_kb_v2_{case_id}", "version": "core_bazi_layer_v1"}


def _strength(
    *,
    case_id: str,
    wealth: float,
    output: float,
    peer: float,
    officer: float,
    seal: float,
    support: float = 0.5,
    pressure: float = 0.5,
) -> dict:
    return {
        "strength_bundle_id": f"core_strength_bundle_kb_v2_{case_id}",
        "version": "core_strength_model_v1",
        "day_master_strength": {
            "support_score": support,
            "pressure_score": pressure,
            "tendency": "calibration_v2",
        },
        "ten_god_strengths": {
            "wealth": {"score": wealth, "tendency": "calibration_v2"},
            "output": {"score": output, "tendency": "calibration_v2"},
            "peer": {"score": peer, "tendency": "calibration_v2"},
            "officer_killing": {"score": officer, "tendency": "calibration_v2"},
            "seal": {"score": seal, "tendency": "calibration_v2"},
        },
    }


def _structure(
    *,
    case_id: str,
    stability: float = 0.0,
    activation: float = 0.0,
    suppression: float = 0.0,
    amplification: float = 0.0,
    risk: float = 0.0,
    vault_state: str = "",
    vault_stability: float = 0.0,
    vault_activation: float = 0.0,
    vault_risk: float = 0.0,
    vault_liquidity: float = 0.0,
    relation_conflict: bool = False,
) -> dict:
    vaults = []
    if vault_state:
        vaults.append(
            {
                "effect_id": f"vault_effect_{case_id}_{vault_state}",
                "vault_branch": "丑",
                "vault_state": vault_state,
                "target": {"target_group": "wealth", "structural_target": "wealth_vault"},
                "stability_effect": vault_stability,
                "activation_effect": vault_activation,
                "risk_effect": vault_risk,
                "liquidity_effect": vault_liquidity,
            }
        )
    relation_effects = []
    if relation_conflict:
        relation_effects.append(
            {
                "effect_id": f"relation_conflict_{case_id}",
                "relation_type": "combination_and_clash",
                "activation_effect": activation,
                "risk_effect": risk,
                "stability_effect": stability,
            }
        )
    return {
        "structure_bundle_id": f"core_structure_bundle_kb_v2_{case_id}",
        "version": "core_structure_effect_layer_v1",
        "effect_summary": {
            "stability_effect": stability,
            "activation_effect": activation,
            "suppression_effect": suppression,
            "amplification_effect": amplification,
            "risk_effect": risk,
        },
        "relation_effects": relation_effects,
        "vault_effects": vaults,
    }


V2_CASES = [
    {
        "case": "财旺身弱",
        "expected_direction": "wealth_pressure_reinforced",
        "strength": _strength(case_id="wealth_strong_body_weak", wealth=0.82, output=0.28, peer=0.18, officer=0.74, seal=0.16, support=0.22, pressure=0.78),
        "structure": _structure(case_id="wealth_strong_body_weak", stability=-0.24, activation=0.38, suppression=0.36, risk=0.74, vault_state="opened_by_clash", vault_activation=0.32, vault_risk=0.46, vault_liquidity=0.44),
    },
    {
        "case": "身旺财弱",
        "expected_direction": "weak_signal_reinforced",
        "strength": _strength(case_id="body_strong_wealth_weak", wealth=0.18, output=0.22, peer=0.74, officer=0.18, seal=0.64, support=0.78, pressure=0.22),
        "structure": _structure(case_id="body_strong_wealth_weak", stability=0.14, activation=0.08, risk=0.12),
    },
    {
        "case": "食伤生财明显",
        "expected_direction": "output_conversion_reinforced",
        "strength": _strength(case_id="clear_output_generates_wealth", wealth=0.42, output=0.82, peer=0.24, officer=0.2, seal=0.22, support=0.62, pressure=0.28),
        "structure": _structure(case_id="clear_output_generates_wealth", stability=0.18, activation=0.42, amplification=0.3, risk=0.16),
    },
    {
        "case": "食伤有但无法转财",
        "expected_direction": "blocked_conversion_reinforced",
        "strength": _strength(case_id="output_blocked_conversion", wealth=0.24, output=0.78, peer=0.22, officer=0.62, seal=0.82, support=0.34, pressure=0.66),
        "structure": _structure(case_id="output_blocked_conversion", stability=-0.22, activation=0.16, suppression=0.78, risk=0.58),
    },
    {
        "case": "财库存在但未打开",
        "expected_direction": "vault_storage_reinforced",
        "strength": _strength(case_id="vault_closed_storable", wealth=0.58, output=0.26, peer=0.22, officer=0.22, seal=0.5, support=0.58, pressure=0.28),
        "structure": _structure(case_id="vault_closed_storable", stability=0.36, activation=0.04, risk=0.12, vault_state="closed_storable", vault_stability=0.36, vault_activation=0.0, vault_risk=0.1, vault_liquidity=-0.1),
    },
    {
        "case": "财库被冲",
        "expected_direction": "vault_liquidity_risk_reinforced",
        "strength": _strength(case_id="vault_opened_by_clash", wealth=0.54, output=0.34, peer=0.24, officer=0.24, seal=0.24, support=0.44, pressure=0.48),
        "structure": _structure(case_id="vault_opened_by_clash", stability=-0.48, activation=0.78, risk=0.76, vault_state="opened_by_clash", vault_activation=0.68, vault_risk=0.58, vault_liquidity=0.68),
    },
    {
        "case": "财库被合",
        "expected_direction": "locked_accumulation_reinforced",
        "strength": _strength(case_id="vault_locked", wealth=0.56, output=0.2, peer=0.2, officer=0.18, seal=0.52, support=0.6, pressure=0.3),
        "structure": _structure(case_id="vault_locked", stability=0.46, activation=0.02, risk=0.12, vault_state="locked_by_combination", vault_stability=0.38, vault_activation=-0.18, vault_risk=0.14, vault_liquidity=-0.3),
    },
    {
        "case": "比劫强",
        "expected_direction": "competition_risk_reinforced",
        "strength": _strength(case_id="strong_peer_competition", wealth=0.34, output=0.28, peer=0.94, officer=0.18, seal=0.26, support=0.66, pressure=0.32),
        "structure": _structure(case_id="strong_peer_competition", stability=-0.28, activation=0.18, risk=0.82, vault_state="opened_by_clash", vault_risk=0.42, vault_liquidity=0.28),
    },
    {
        "case": "官杀强",
        "expected_direction": "constraint_reinforced",
        "strength": _strength(case_id="strong_officer_constraint", wealth=0.46, output=0.22, peer=0.24, officer=0.94, seal=0.22, support=0.36, pressure=0.7),
        "structure": _structure(case_id="strong_officer_constraint", stability=-0.1, activation=0.12, suppression=0.82, risk=0.44),
    },
    {
        "case": "合冲同时存在",
        "expected_direction": "conflict_uncertainty_reinforced",
        "strength": _strength(case_id="combination_clash_conflicted", wealth=0.48, output=0.42, peer=0.38, officer=0.3, seal=0.28, support=0.44, pressure=0.5),
        "structure": _structure(case_id="combination_clash_conflicted", stability=-0.34, activation=0.66, amplification=0.32, risk=0.68, vault_state="conflicted", vault_stability=-0.28, vault_activation=0.5, vault_risk=0.56, vault_liquidity=0.48, relation_conflict=True),
    },
    {
        "case": "无财星",
        "expected_direction": "latent_signal_reinforced",
        "strength": _strength(case_id="no_wealth_latent", wealth=0.04, output=0.12, peer=0.38, officer=0.18, seal=0.52, support=0.58, pressure=0.28),
        "structure": _structure(case_id="no_wealth_latent", stability=0.08, activation=0.04, risk=0.1),
    },
    {
        "case": "运势引动",
        "expected_direction": "flow_activation_reinforced",
        "strength": _strength(case_id="flow_activation", wealth=0.38, output=0.46, peer=0.26, officer=0.28, seal=0.3, support=0.48, pressure=0.42),
        "structure": _structure(case_id="flow_activation", stability=-0.12, activation=0.86, amplification=0.26, risk=0.34, vault_state="opened_by_clash", vault_activation=0.52, vault_risk=0.3, vault_liquidity=0.56),
    },
]


@pytest.mark.parametrize("case_payload", V2_CASES, ids=[row["case"] for row in V2_CASES])
def test_wealth_kb_calibration_v2_typical_cases(case_payload: dict) -> None:
    report = wealth_domain.evaluate_wealth_kb_calibration_v2_case(
        {
            "case": case_payload["case"],
            "expected_direction": case_payload["expected_direction"],
            "core_feature_bundle": _core(case_payload["case"]),
            "core_strength_bundle": case_payload["strength"],
            "structure_effect_bundle": case_payload["structure"],
            "user_intent": "wealth_prediction",
        }
    )

    assert json.loads(json.dumps(report, ensure_ascii=False))["case"] == case_payload["case"]
    assert report["expected_direction"] == case_payload["expected_direction"]
    assert isinstance(report["wealth_type_before"], str)
    assert isinstance(report["wealth_type_after"], str)
    assert report["baseline"]["wealth_type"] == report["wealth_type_before"]
    assert report["baseline"]["evidence"]
    assert report["kb_augmented"]["wealth_type_after"] == report["wealth_type_after"]
    assert len(report["kb_augmented"]["evidence_after"]) > len(report["baseline"]["evidence"])
    assert report["kb_augmented"]["kb_evidence_count"] >= 5
    assert "evidence_count" in report["kb_augmented"]["changed_fields"]
    assert any(row["source"] == wealth_domain.WEALTH_KB_CALIBRATION_SOURCE for row in report["kb_augmented"]["evidence_after"])
    assert report["comparison"]["kb_source_present"] is True
    assert report["is_reasonable"] is True
