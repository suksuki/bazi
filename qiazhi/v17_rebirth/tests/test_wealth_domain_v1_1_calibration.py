from __future__ import annotations

import pytest

from v17_rebirth.backend.services import core_bazi_wealth_domain as wealth_domain


def _core() -> dict:
    return {"bundle_id": "core_feature_bundle_calibration", "version": "core_bazi_layer_v1"}


def _strength(
    *,
    wealth: float,
    output: float,
    peer: float,
    officer: float,
    seal: float,
    support: float = 0.5,
    pressure: float = 0.5,
) -> dict:
    return {
        "strength_bundle_id": "core_strength_bundle_calibration",
        "version": "core_strength_model_v1",
        "day_master_strength": {
            "support_score": support,
            "pressure_score": pressure,
            "tendency": "balanced",
        },
        "ten_god_strengths": {
            "wealth": {"score": wealth, "tendency": "calibrated"},
            "output": {"score": output, "tendency": "calibrated"},
            "peer": {"score": peer, "tendency": "calibrated"},
            "officer_killing": {"score": officer, "tendency": "calibrated"},
            "seal": {"score": seal, "tendency": "calibrated"},
        },
    }


def _structure(
    *,
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
) -> dict:
    vaults = []
    if vault_state:
        vaults.append(
            {
                "effect_id": f"vault_effect_{vault_state}",
                "vault_branch": "丑",
                "vault_state": vault_state,
                "target": {"target_group": "wealth", "structural_target": "wealth_vault"},
                "stability_effect": vault_stability,
                "activation_effect": vault_activation,
                "risk_effect": vault_risk,
                "liquidity_effect": vault_liquidity,
            }
        )
    return {
        "structure_bundle_id": "core_structure_bundle_calibration",
        "version": "core_structure_effect_layer_v1",
        "effect_summary": {
            "stability_effect": stability,
            "activation_effect": activation,
            "suppression_effect": suppression,
            "amplification_effect": amplification,
            "risk_effect": risk,
        },
        "relation_effects": [],
        "vault_effects": vaults,
    }


def _evaluate(strength: dict, structure: dict) -> dict:
    return wealth_domain.evaluate_wealth_domain(
        {
            "core_feature_bundle": _core(),
            "core_strength_bundle": strength,
            "structure_effect_bundle": structure,
            "user_intent": "wealth_prediction",
        }
    )


@pytest.mark.parametrize(
    ("name", "strength", "structure", "expected_type"),
    [
        (
            "财旺身弱",
            _strength(wealth=0.76, output=0.28, peer=0.18, officer=0.78, seal=0.18, support=0.26, pressure=0.72),
            _structure(stability=-0.2, activation=0.42, suppression=0.3, risk=0.78, vault_state="opened_by_clash", vault_activation=0.4, vault_risk=0.5, vault_liquidity=0.52),
            "volatile",
        ),
        (
            "身旺财弱",
            _strength(wealth=0.2, output=0.24, peer=0.76, officer=0.18, seal=0.62, support=0.74, pressure=0.26),
            _structure(stability=0.12, activation=0.1, risk=0.12),
            "weak_signal",
        ),
        (
            "食伤生财",
            _strength(wealth=0.35, output=0.76, peer=0.28, officer=0.2, seal=0.3, support=0.56, pressure=0.35),
            _structure(stability=0.12, activation=0.36, amplification=0.25, risk=0.18),
            "opportunity",
        ),
        (
            "比劫夺财",
            _strength(wealth=0.32, output=0.28, peer=0.96, officer=0.2, seal=0.28, support=0.68, pressure=0.34),
            _structure(stability=-0.22, activation=0.18, risk=0.9, vault_state="opened_by_clash", vault_risk=0.5),
            "leakage_risk",
        ),
        (
            "财库被冲",
            _strength(wealth=0.52, output=0.32, peer=0.24, officer=0.26, seal=0.26, support=0.46, pressure=0.42),
            _structure(stability=-0.45, activation=0.72, risk=0.72, vault_state="opened_by_clash", vault_activation=0.62, vault_risk=0.52, vault_liquidity=0.64),
            "volatile",
        ),
        (
            "财库被合",
            _strength(wealth=0.56, output=0.22, peer=0.22, officer=0.18, seal=0.48, support=0.58, pressure=0.32),
            _structure(stability=0.44, activation=0.04, risk=0.12, vault_state="locked_by_combination", vault_stability=0.36, vault_activation=-0.18, vault_risk=0.16, vault_liquidity=-0.28),
            "accumulation",
        ),
        (
            "官杀制约财富",
            _strength(wealth=0.46, output=0.24, peer=0.28, officer=0.92, seal=0.24, support=0.38, pressure=0.68),
            _structure(stability=-0.08, activation=0.14, suppression=0.78, risk=0.42),
            "constrained",
        ),
        (
            "合局增强稳定降低流动",
            _strength(wealth=0.58, output=0.28, peer=0.22, officer=0.24, seal=0.56, support=0.62, pressure=0.3),
            _structure(stability=0.58, activation=0.02, amplification=0.42, risk=0.1, vault_state="locked_by_combination", vault_stability=0.38, vault_activation=-0.2, vault_risk=0.12, vault_liquidity=-0.3),
            "accumulation",
        ),
        (
            "冲动增强流动增加风险",
            _strength(wealth=0.44, output=0.42, peer=0.34, officer=0.3, seal=0.24, support=0.44, pressure=0.48),
            _structure(stability=-0.55, activation=0.78, risk=0.76, vault_state="opened_by_clash", vault_activation=0.64, vault_risk=0.58, vault_liquidity=0.68),
            "volatile",
        ),
    ],
)
def test_wealth_domain_v11_typical_calibration_samples(name: str, strength: dict, structure: dict, expected_type: str) -> None:
    bundle = _evaluate(strength, structure)
    profile = bundle["wealth_profile"]

    assert profile["wealth_type"] == expected_type, name
    assert 0.0 <= profile["opportunity_score"] <= 1.0
    assert 0.0 <= profile["stability_score"] <= 1.0
    assert 0.0 <= profile["risk_score"] <= 1.0
    assert 0.0 <= profile["liquidity_score"] <= 1.0
    assert len(bundle["wealth_evidence"]) >= 3
    assert bundle["wealth_conclusions"]
    assert all(conclusion["evidence_ids"] for conclusion in bundle["wealth_conclusions"])
    assert all(
        ref in {row["feature_id"] for row in bundle["wealth_evidence"]}
        for conclusion in bundle["wealth_conclusions"]
        for ref in conclusion["evidence_ids"]
    )


def test_wealth_domain_v11_explanation_claims_are_structured_not_fortune_promises() -> None:
    bundle = _evaluate(
        _strength(wealth=0.52, output=0.72, peer=0.3, officer=0.28, seal=0.34, support=0.56, pressure=0.38),
        _structure(stability=0.08, activation=0.42, amplification=0.28, risk=0.24),
    )
    claims = " ".join(row["claim"] for row in bundle["wealth_conclusions"])

    assert "财富结构判断" in claims
    assert "核心依据" in claims
    assert "风险与不确定性" in claims
    assert "发财" not in claims
    assert "命好" not in claims
    assert "命差" not in claims
    assert "一生" not in claims
