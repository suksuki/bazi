from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Optional

from v17_rebirth.backend.services.core_bazi_feature_layer import core_bazi_feature_service
from v17_rebirth.backend.services.core_bazi_strength_model import core_bazi_strength_service
from v17_rebirth.backend.services.core_bazi_structure_effect_layer import core_bazi_structure_effect_service
from v17_rebirth.backend.services.v18_1_predictive_engine import (
    PredictiveServiceError,
    WEALTH_CORE_KNOWLEDGE_UNITS_V1,
)
from v17_rebirth.paths import RUNTIME_DIR


WEALTH_DOMAIN_VERSION = "wealth_domain_v1"
WEALTH_DOMAIN_SCHEMA_VERSION = "wealth_domain_bundle.v1"
SUPPORTED_WEALTH_INTENTS = {"wealth_prediction", "income_stability", "wealth_risk_opportunity"}
SUPPORTED_KNOWLEDGE_MODES = {"baseline_only", "kb_augmented"}
WEALTH_KB_CALIBRATION_SOURCE = "wealth_kb_calibration_v1"
WEALTH_TYPE_LABELS: Dict[str, str] = {
    "stable": "稳定收入型",
    "opportunity": "输出机会型",
    "volatile": "波动流动型",
    "constrained": "受制约型",
    "weak_signal": "财星弱信号型",
    "accumulation": "积累蓄财型",
    "leakage_risk": "泄漏风险型",
}


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _payload_hash(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def _safe_str(value: Any, default: str = "") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        raw = float(value)
    except (TypeError, ValueError):
        return default
    if raw != raw:
        return default
    return raw


def _ensure_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return list(value)
    if value is None:
        return []
    return [value]


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _signed_to_positive(value: float) -> float:
    return _clamp01((float(value) + 1.0) / 2.0)


def _round(value: float, digits: int = 3) -> float:
    return round(_clamp01(value), digits)


def _coerce_core_bundle(payload: Mapping[str, Any]) -> Dict[str, Any]:
    nested = payload.get("core_feature_bundle") or payload.get("feature_bundle")
    if isinstance(nested, Mapping):
        return dict(nested)
    bundle_id = _safe_str(payload.get("core_bundle_id") or payload.get("source_core_bundle_id"))
    if bundle_id:
        return core_bazi_feature_service.get_bundle(bundle_id)
    raise PredictiveServiceError("WEALTH_DOMAIN_INPUT_INVALID", "core_feature_bundle is required", status=400)


def _coerce_strength_bundle(payload: Mapping[str, Any]) -> Dict[str, Any]:
    nested = payload.get("core_strength_bundle") or payload.get("strength_bundle")
    if isinstance(nested, Mapping):
        return dict(nested)
    bundle_id = _safe_str(payload.get("strength_bundle_id") or payload.get("source_strength_bundle_id"))
    if bundle_id:
        return core_bazi_strength_service.get_bundle(bundle_id)
    raise PredictiveServiceError("WEALTH_DOMAIN_INPUT_INVALID", "core_strength_bundle is required", status=400)


def _coerce_structure_bundle(payload: Mapping[str, Any]) -> Dict[str, Any]:
    nested = payload.get("structure_effect_bundle") or payload.get("core_structure_bundle") or payload.get("structure_bundle")
    if isinstance(nested, Mapping):
        return dict(nested)
    bundle_id = _safe_str(payload.get("structure_bundle_id") or payload.get("source_structure_bundle_id"))
    if bundle_id:
        return core_bazi_structure_effect_service.get_bundle(bundle_id)
    raise PredictiveServiceError("WEALTH_DOMAIN_INPUT_INVALID", "structure_effect_bundle is required", status=400)


def _ten_god_strength(strength_bundle: Mapping[str, Any], key: str) -> Dict[str, Any]:
    strengths = strength_bundle.get("ten_god_strengths") if isinstance(strength_bundle.get("ten_god_strengths"), Mapping) else {}
    row = strengths.get(key) if isinstance(strengths.get(key), Mapping) else {}
    return dict(row)


def _score(strength_bundle: Mapping[str, Any], key: str) -> float:
    return _clamp01(_safe_float(_ten_god_strength(strength_bundle, key).get("score"), 0.0))


def _summary(structure_bundle: Mapping[str, Any]) -> Dict[str, float]:
    raw = structure_bundle.get("effect_summary") if isinstance(structure_bundle.get("effect_summary"), Mapping) else {}
    return {
        "stability": _safe_float(raw.get("stability_effect"), 0.0),
        "activation": _safe_float(raw.get("activation_effect"), 0.0),
        "suppression": _safe_float(raw.get("suppression_effect"), 0.0),
        "amplification": _safe_float(raw.get("amplification_effect"), 0.0),
        "risk": _safe_float(raw.get("risk_effect"), 0.0),
    }


def _wealth_vault_effects(structure_bundle: Mapping[str, Any]) -> list[Dict[str, Any]]:
    rows = structure_bundle.get("vault_effects") if isinstance(structure_bundle.get("vault_effects"), list) else []
    return [
        dict(row)
        for row in rows
        if isinstance(row, Mapping) and _safe_str(dict(row.get("target") or {}).get("target_group")) == "wealth"
    ]


def _relation_activation_effects(structure_bundle: Mapping[str, Any]) -> list[Dict[str, Any]]:
    rows = structure_bundle.get("relation_effects") if isinstance(structure_bundle.get("relation_effects"), list) else []
    return [dict(row) for row in rows if isinstance(row, Mapping) and _safe_float(row.get("activation_effect"), 0.0) > 0.0]


def _evidence(
    *,
    feature_id: str,
    feature_type: str,
    label: str,
    strength: float,
    stability: float,
    risk: float,
    uncertainty: float,
    relevance: float,
    matched_facts: Iterable[Any],
    effect: Mapping[str, Any],
    source_refs: Iterable[str],
) -> Dict[str, Any]:
    return {
        "feature_id": feature_id,
        "feature_type": feature_type,
        "label": label,
        "feature_label": label,
        "matched_facts": [_safe_str(item) for item in matched_facts if _safe_str(item)][:8],
        "strength": _round(strength),
        "stability": _round(stability),
        "risk": _round(risk),
        "uncertainty": _round(uncertainty),
        "wealth_relevance": _round(relevance),
        "effect": dict(effect),
        "source_refs": [_safe_str(item) for item in source_refs if _safe_str(item)],
        "source": WEALTH_DOMAIN_VERSION,
    }


def _feature_aliases(feature_type: str) -> set[str]:
    aliases = {
        "wealth_vault_state": {"wealth_vault_state", "wealth_vault"},
        "wealth_constraint": {"wealth_constraint", "constraint_structure", "authority_constraint"},
    }
    return aliases.get(feature_type, {feature_type})


def _best_baseline_evidence(unit: Mapping[str, Any], evidence_rows: list[Mapping[str, Any]]) -> Dict[str, Any]:
    mapping = unit.get("feature_mapping") if isinstance(unit.get("feature_mapping"), Mapping) else {}
    feature_type = _safe_str(mapping.get("feature_type"))
    aliases = _feature_aliases(feature_type)
    matches = [
        dict(row)
        for row in evidence_rows
        if _safe_str(row.get("feature_id")) in aliases or _safe_str(row.get("feature_type")) in aliases
    ]
    if not matches:
        return {}
    return sorted(
        matches,
        key=lambda row: _safe_float(row.get("wealth_relevance"), 0.0) + _safe_float(row.get("strength"), 0.0),
        reverse=True,
    )[0]


def _effect_score(effects: Mapping[str, Any], keys: Iterable[str], default: float = 0.0) -> float:
    values = [_safe_float(effects.get(key), default) for key in keys if key in effects]
    return max(values) if values else default


def _knowledge_unit_to_evidence(unit: Mapping[str, Any], baseline_rows: list[Mapping[str, Any]]) -> Dict[str, Any]:
    mapping = unit.get("feature_mapping") if isinstance(unit.get("feature_mapping"), Mapping) else {}
    feature_type = _safe_str(mapping.get("feature_type"))
    knowledge_id = _safe_str(unit.get("knowledge_id"))
    confidence = _clamp01(_safe_float(unit.get("confidence_prior"), _safe_float(mapping.get("confidence_weight"), 0.65)))
    effects = dict(unit.get("effects") or {})
    baseline = _best_baseline_evidence(unit, baseline_rows)
    baseline_strength = _safe_float(baseline.get("strength"), confidence)
    baseline_stability = _safe_float(baseline.get("stability"), 0.52)
    baseline_risk = _safe_float(baseline.get("risk"), 0.24)
    positive_signal = _effect_score(
        effects,
        [
            "wealth_potential",
            "earning_opportunity",
            "conversion_support",
            "wealth_retention",
            "formalize_path",
            "stabilize_risk",
        ],
        confidence,
    )
    risk_signal = _effect_score(
        effects,
        ["risk", "competition_pressure", "resource_distribution_risk", "pressure_income", "uncertainty"],
        0.0,
    )
    stability_signal = _effect_score(effects, ["structure_stability", "wealth_retention", "stabilize_risk"], baseline_stability)
    label = _safe_str(unit.get("title") or mapping.get("feature_type") or knowledge_id)
    row = _evidence(
        feature_id=f"kb_{knowledge_id.replace('.', '_')}",
        feature_type=feature_type,
        label=f"KB校准：{label}",
        strength=_clamp01(baseline_strength * 0.58 + confidence * 0.24 + positive_signal * 0.18),
        stability=_clamp01(baseline_stability * 0.62 + stability_signal * 0.24 + (1.0 - risk_signal) * 0.14),
        risk=_clamp01(baseline_risk * 0.55 + risk_signal * 0.45),
        uncertainty=_clamp01(_safe_float(mapping.get("uncertainty_weight"), 1.0 - confidence) * 0.56 + _safe_float(baseline.get("uncertainty"), 0.24) * 0.44),
        relevance=_clamp01(0.74 + confidence * 0.18),
        matched_facts=[
            knowledge_id,
            feature_type,
            _safe_str(dict(unit.get("conditions") or {}).get("knowledge_version")),
            _safe_str(mapping.get("effect_direction")),
        ],
        effect=effects,
        source_refs=[f"bazi_knowledge_unit:{knowledge_id}", "docs:bazi_knowledge/wealth/wealth_units_v1.md"],
    )
    row.update(
        {
            "source": WEALTH_KB_CALIBRATION_SOURCE,
            "source_knowledge_id": knowledge_id,
            "knowledge_mode": "kb_augmented",
            "experimental": True,
        }
    )
    return row


def _kb_calibration_deltas(kb_rows: list[Mapping[str, Any]]) -> Dict[str, float]:
    if not kb_rows:
        return {"opportunity": 0.0, "stability": 0.0, "risk": 0.0, "accumulation": 0.0, "liquidity": 0.0}
    weighted = sum(_safe_float(row.get("wealth_relevance"), 0.0) for row in kb_rows) or float(len(kb_rows))
    opportunity = 0.0
    stability = 0.0
    risk = 0.0
    accumulation = 0.0
    liquidity = 0.0
    for row in kb_rows:
        relevance = _safe_float(row.get("wealth_relevance"), 0.0) / weighted
        effects = dict(row.get("effect") or {})
        opportunity += relevance * max(
            _safe_float(effects.get("wealth_potential"), 0.0),
            _safe_float(effects.get("earning_opportunity"), 0.0),
            _safe_float(effects.get("conversion_support"), 0.0),
            _safe_float(row.get("strength"), 0.0),
        )
        stability += relevance * (
            _safe_float(effects.get("structure_stability"), 0.0)
            + _safe_float(effects.get("stabilize_risk"), 0.0)
            + _safe_float(effects.get("wealth_retention"), 0.0)
            + _safe_float(row.get("stability"), 0.0)
            - _safe_float(row.get("risk"), 0.0) * 0.4
        )
        risk += relevance * max(
            _safe_float(effects.get("risk"), 0.0),
            _safe_float(effects.get("competition_pressure"), 0.0),
            _safe_float(effects.get("resource_distribution_risk"), 0.0),
            _safe_float(effects.get("pressure_income"), 0.0),
            _safe_float(row.get("risk"), 0.0),
        )
        accumulation += relevance * max(
            _safe_float(effects.get("wealth_retention"), 0.0),
            _safe_float(effects.get("structure_stability"), 0.0),
        )
        liquidity += relevance * _safe_float(effects.get("liquidity_modifier"), 0.0)
    return {
        "opportunity": round(min(0.07, opportunity * 0.035), 4),
        "stability": round(max(-0.04, min(0.06, stability * 0.025)), 4),
        "risk": round(min(0.05, risk * 0.018), 4),
        "accumulation": round(min(0.05, accumulation * 0.026), 4),
        "liquidity": round(max(-0.03, min(0.04, liquidity * 0.025)), 4),
    }


def _wealth_type(
    *,
    opportunity_score: float,
    stability_score: float,
    risk_score: float,
    accumulation_score: float,
    liquidity_score: float,
    suppression_score: float,
    wealth_strength: float,
    output_generate_score: float,
    peer_competition_score: float,
    body_weak_pressure: float,
    vault_liquidity: float,
    vault_risk: float,
    vault_stability: float,
    structure_risk: float,
) -> str:
    if wealth_strength < 0.26 and opportunity_score < 0.40:
        return "weak_signal"
    if peer_competition_score >= 0.58 and risk_score >= 0.46:
        return "leakage_risk"
    if liquidity_score >= 0.45 and (risk_score >= 0.38 or vault_risk >= 0.45 or structure_risk >= 0.62):
        return "volatile"
    if body_weak_pressure >= 0.22 and (risk_score >= 0.42 or structure_risk >= 0.62) and wealth_strength >= 0.46:
        return "volatile"
    if vault_liquidity <= -0.12 and vault_stability >= 0.20 and wealth_strength >= 0.45 and risk_score <= 0.48:
        return "accumulation"
    if accumulation_score >= 0.45 and stability_score >= 0.48 and risk_score <= 0.48 and liquidity_score <= 0.58:
        return "accumulation"
    if output_generate_score >= 0.45 and wealth_strength < 0.38:
        return "volatile" if risk_score >= 0.46 or stability_score < 0.34 else "opportunity"
    if risk_score >= 0.58 and opportunity_score >= 0.42:
        return "volatile"
    if suppression_score >= 0.62 or (stability_score < 0.38 and liquidity_score < 0.36):
        return "constrained"
    if stability_score >= 0.62 and risk_score <= 0.42 and accumulation_score >= 0.46:
        return "stable"
    if opportunity_score >= 0.50 and suppression_score < 0.78:
        return "opportunity"
    return "constrained" if risk_score > opportunity_score else "opportunity"


def _uncertainty(profile: Mapping[str, Any], evidence_rows: list[Mapping[str, Any]]) -> Dict[str, Any]:
    risk_score = _safe_float(profile.get("risk_score"), 0.0)
    stability_score = _safe_float(profile.get("stability_score"), 0.0)
    evidence_uncertainty = sum(_safe_float(row.get("uncertainty"), 0.25) for row in evidence_rows) / max(1, len(evidence_rows))
    score = _clamp01(evidence_uncertainty * 0.45 + risk_score * 0.28 + max(0.0, 0.55 - stability_score) * 0.27)
    reasons = ["财富判断仍依赖现实收入结构与用户反馈校准"]
    if risk_score >= 0.50:
        reasons.append("结构扰动或竞争压力较高")
    if stability_score < 0.45:
        reasons.append("收入稳定性证据不足或波动偏高")
    if len(evidence_rows) < 4:
        reasons.append("财富证据数量较少")
    return {"score": round(score, 3), "reasons": reasons}


def evaluate_wealth_domain(payload: Mapping[str, Any]) -> Dict[str, Any]:
    intent = _safe_str(payload.get("user_intent") or payload.get("intent"), "wealth_prediction")
    if intent not in SUPPORTED_WEALTH_INTENTS:
        raise PredictiveServiceError("WEALTH_DOMAIN_UNSUPPORTED_INTENT", "unsupported wealth domain intent", status=409)
    knowledge_mode = _safe_str(payload.get("knowledge_mode"), "baseline_only")
    if knowledge_mode not in SUPPORTED_KNOWLEDGE_MODES:
        raise PredictiveServiceError("WEALTH_DOMAIN_KNOWLEDGE_MODE_INVALID", "unsupported wealth domain knowledge_mode", status=400)

    core_bundle = _coerce_core_bundle(payload)
    strength_bundle = _coerce_strength_bundle(payload)
    structure_bundle = _coerce_structure_bundle(payload)
    source_core_bundle_id = _safe_str(core_bundle.get("bundle_id"))
    source_strength_bundle_id = _safe_str(strength_bundle.get("strength_bundle_id"))
    source_structure_bundle_id = _safe_str(structure_bundle.get("structure_bundle_id"))
    if not source_core_bundle_id or not source_strength_bundle_id or not source_structure_bundle_id:
        raise PredictiveServiceError("WEALTH_DOMAIN_INPUT_INVALID", "source bundle ids are required", status=400)

    wealth_strength = _score(strength_bundle, "wealth")
    output_strength = _score(strength_bundle, "output")
    peer_strength = _score(strength_bundle, "peer")
    officer_strength = _score(strength_bundle, "officer_killing")
    seal_strength = _score(strength_bundle, "seal")
    day_strength = strength_bundle.get("day_master_strength") if isinstance(strength_bundle.get("day_master_strength"), Mapping) else {}
    body_support_score = _clamp01(_safe_float(day_strength.get("support_score"), 0.0))
    body_pressure_score = _clamp01(_safe_float(day_strength.get("pressure_score"), 0.0))
    body_support_bonus = _clamp01(body_support_score - body_pressure_score)
    body_weak_pressure = _clamp01(body_pressure_score - body_support_score)
    effects = _summary(structure_bundle)
    activation = _clamp01(effects["activation"])
    amplification = _clamp01(effects["amplification"])
    suppression = _clamp01(effects["suppression"])
    structure_risk = _clamp01(effects["risk"])
    structure_stability = _signed_to_positive(effects["stability"])

    vaults = _wealth_vault_effects(structure_bundle)
    vault_liquidity = max([_safe_float(row.get("liquidity_effect"), 0.0) for row in vaults] or [0.0])
    vault_activation = max([_safe_float(row.get("activation_effect"), 0.0) for row in vaults] or [0.0])
    vault_risk = max([_safe_float(row.get("risk_effect"), 0.0) for row in vaults] or [0.0])
    vault_stability = max([_safe_float(row.get("stability_effect"), 0.0) for row in vaults] or [0.0])

    output_generate_score = _clamp01(output_strength * 0.52 + wealth_strength * 0.22 + activation * 0.18 + amplification * 0.08)
    peer_competition_score = _clamp01(peer_strength * 0.62 + max(0.0, peer_strength - wealth_strength) * 0.38)
    authority_constraint_score = _clamp01(officer_strength * 0.54 + suppression * 0.32 + structure_risk * 0.14)
    opportunity_score = _clamp01(output_generate_score * 0.38 + wealth_strength * 0.20 + activation * 0.20 + max(0.0, vault_liquidity) * 0.14 + body_support_bonus * 0.08)
    stability_score = _clamp01(wealth_strength * 0.28 + structure_stability * 0.28 + max(0.0, vault_stability) * 0.16 + seal_strength * 0.10 + (1.0 - structure_risk) * 0.10 + body_support_bonus * 0.10 - body_weak_pressure * 0.18)
    risk_score = _clamp01(structure_risk * 0.30 + peer_competition_score * 0.22 + authority_constraint_score * 0.18 + max(0.0, vault_risk) * 0.14 + max(0.0, output_strength - wealth_strength) * 0.08 + body_weak_pressure * 0.16)
    vault_storage_bonus = max(0.0, vault_stability) * 0.16 + max(0.0, -vault_liquidity) * 0.12
    accumulation_score = _clamp01(wealth_strength * 0.38 + stability_score * 0.26 + vault_storage_bonus - risk_score * 0.14 + max(0.0, vault_activation) * 0.06 + body_support_bonus * 0.16 - body_weak_pressure * 0.18)
    liquidity_score = _clamp01(activation * 0.42 + max(0.0, vault_liquidity) * 0.34 + output_generate_score * 0.16 - max(0.0, suppression) * 0.08)
    wealth_type = _wealth_type(
        opportunity_score=opportunity_score,
        stability_score=stability_score,
        risk_score=risk_score,
        accumulation_score=accumulation_score,
        liquidity_score=liquidity_score,
        suppression_score=authority_constraint_score,
        wealth_strength=wealth_strength,
        output_generate_score=output_generate_score,
        peer_competition_score=peer_competition_score,
        body_weak_pressure=body_weak_pressure,
        vault_liquidity=vault_liquidity,
        vault_risk=vault_risk,
        vault_stability=vault_stability,
        structure_risk=structure_risk,
    )
    baseline_profile = {
        "wealth_type": wealth_type,
        "wealth_type_label": WEALTH_TYPE_LABELS.get(wealth_type, wealth_type),
        "opportunity_score": _round(opportunity_score),
        "stability_score": _round(stability_score),
        "risk_score": _round(risk_score),
        "accumulation_score": _round(accumulation_score),
        "liquidity_score": _round(liquidity_score),
    }

    evidence_rows = [
        _evidence(
            feature_id="wealth_strength",
            feature_type="wealth_strength",
            label="财星状态",
            strength=wealth_strength,
            stability=stability_score,
            risk=max(0.0, 1.0 - wealth_strength) * 0.38,
            uncertainty=max(0.08, 1.0 - max(wealth_strength, stability_score)),
            relevance=0.95,
            matched_facts=[f"wealth_strength_score={wealth_strength:.3f}", _safe_str(_ten_god_strength(strength_bundle, "wealth").get("tendency"))],
            effect={"wealth": round(wealth_strength, 3), "accumulation": round(accumulation_score, 3)},
            source_refs=["core_strength_model_v1.ten_god_strengths.wealth", "core_strength_model_v1.day_master_strength"],
        ),
        _evidence(
            feature_id="output_generate_wealth",
            feature_type="output_generate_wealth",
            label="食伤生财 / 输出变现",
            strength=output_generate_score,
            stability=_clamp01(stability_score * 0.68 + output_strength * 0.22),
            risk=max(0.0, output_strength - wealth_strength) * 0.48 + structure_risk * 0.18,
            uncertainty=max(0.1, abs(output_strength - wealth_strength) * 0.38),
            relevance=0.88,
            matched_facts=[f"output_score={output_strength:.3f}", f"wealth_score={wealth_strength:.3f}", f"body_support={body_support_score:.3f}"],
            effect={"wealth": round(opportunity_score, 3), "earning_opportunity": round(output_generate_score, 3)},
            source_refs=["core_strength_model_v1.ten_god_strengths.output", "core_strength_model_v1.ten_god_strengths.wealth"],
        ),
        _evidence(
            feature_id="peer_competition",
            feature_type="peer_competition",
            label="比劫竞争 / 分利压力",
            strength=peer_competition_score,
            stability=_clamp01(1.0 - peer_competition_score * 0.38),
            risk=peer_competition_score,
            uncertainty=0.24 + peer_competition_score * 0.22,
            relevance=0.72,
            matched_facts=[f"peer_score={peer_strength:.3f}", f"wealth_score={wealth_strength:.3f}"],
            effect={"risk": round(peer_competition_score, 3), "income_stability": round(1.0 - peer_competition_score * 0.52, 3)},
            source_refs=["core_strength_model_v1.ten_god_strengths.peer"],
        ),
        _evidence(
            feature_id="authority_constraint",
            feature_type="constraint_structure",
            label="官杀制约 / 规则压力",
            strength=authority_constraint_score,
            stability=_clamp01(0.42 + officer_strength * 0.24 - suppression * 0.18),
            risk=authority_constraint_score * 0.74,
            uncertainty=0.20 + suppression * 0.25,
            relevance=0.70,
            matched_facts=[f"officer_killing_score={officer_strength:.3f}", f"suppression_effect={suppression:.3f}"],
            effect={"wealth": round(max(0.0, wealth_strength - authority_constraint_score * 0.25), 3), "risk": round(authority_constraint_score, 3)},
            source_refs=["core_strength_model_v1.ten_god_strengths.officer_killing", "core_structure_effect_layer_v1.effect_summary"],
        ),
        _evidence(
            feature_id="structure_activation",
            feature_type="flow_activation",
            label="结构引动 / 流动性",
            strength=_clamp01(activation * 0.55 + max(0.0, vault_activation) * 0.25 + amplification * 0.20),
            stability=structure_stability,
            risk=structure_risk,
            uncertainty=0.18 + structure_risk * 0.28,
            relevance=0.82,
            matched_facts=[f"activation_effect={activation:.3f}", f"stability_effect={effects['stability']:.3f}", f"risk_effect={structure_risk:.3f}"],
            effect={"timing_activation": round(activation, 3), "liquidity": round(liquidity_score, 3), "wealth_stability": round(stability_score, 3)},
            source_refs=["core_structure_effect_layer_v1.effect_summary"],
        ),
    ]

    if vaults:
        top_vault = sorted(vaults, key=lambda row: abs(_safe_float(row.get("activation_effect"), 0.0)) + _safe_float(row.get("risk_effect"), 0.0), reverse=True)[0]
        evidence_rows.append(
            _evidence(
                feature_id="wealth_vault_state",
                feature_type="wealth_vault",
                label="财库状态",
                strength=_clamp01(0.42 + max(0.0, _safe_float(top_vault.get("activation_effect"), 0.0)) * 0.32 + max(0.0, _safe_float(top_vault.get("stability_effect"), 0.0)) * 0.22),
                stability=_signed_to_positive(_safe_float(top_vault.get("stability_effect"), 0.0)),
                risk=_safe_float(top_vault.get("risk_effect"), 0.0),
                uncertainty=0.18 + _safe_float(top_vault.get("risk_effect"), 0.0) * 0.28,
                relevance=0.86,
                matched_facts=[
                    f"vault_branch={_safe_str(top_vault.get('vault_branch'))}",
                    f"vault_state={_safe_str(top_vault.get('vault_state'))}",
                    f"liquidity_effect={_safe_float(top_vault.get('liquidity_effect'), 0.0):.3f}",
                ],
                effect={
                    "wealth_retention": round(accumulation_score, 3),
                    "liquidity": round(liquidity_score, 3),
                    "income_stability": round(stability_score, 3),
                },
                source_refs=["core_structure_effect_layer_v1.vault_effects"],
            )
        )

    baseline_evidence_count = len(evidence_rows)
    kb_evidence_rows: list[Dict[str, Any]] = []
    kb_deltas = {"opportunity": 0.0, "stability": 0.0, "risk": 0.0, "accumulation": 0.0, "liquidity": 0.0}
    if knowledge_mode == "kb_augmented":
        kb_evidence_rows = [
            _knowledge_unit_to_evidence(unit, evidence_rows)
            for unit in WEALTH_CORE_KNOWLEDGE_UNITS_V1
            if _safe_str(unit.get("status")) == "reviewed"
        ]
        kb_deltas = _kb_calibration_deltas(kb_evidence_rows)
        evidence_rows.extend(kb_evidence_rows)
        opportunity_score = _clamp01(opportunity_score + kb_deltas["opportunity"])
        stability_score = _clamp01(stability_score + kb_deltas["stability"])
        risk_score = _clamp01(risk_score + kb_deltas["risk"])
        accumulation_score = _clamp01(accumulation_score + kb_deltas["accumulation"])
        liquidity_score = _clamp01(liquidity_score + kb_deltas["liquidity"])
        wealth_type = _wealth_type(
            opportunity_score=opportunity_score,
            stability_score=stability_score,
            risk_score=risk_score,
            accumulation_score=accumulation_score,
            liquidity_score=liquidity_score,
            suppression_score=authority_constraint_score,
            wealth_strength=wealth_strength,
            output_generate_score=output_generate_score,
            peer_competition_score=peer_competition_score,
            body_weak_pressure=body_weak_pressure,
            vault_liquidity=vault_liquidity,
            vault_risk=vault_risk,
            vault_stability=vault_stability,
            structure_risk=structure_risk,
        )

    profile = {
        "wealth_type": wealth_type,
        "wealth_type_label": WEALTH_TYPE_LABELS.get(wealth_type, wealth_type),
        "opportunity_score": _round(opportunity_score),
        "stability_score": _round(stability_score),
        "risk_score": _round(risk_score),
        "accumulation_score": _round(accumulation_score),
        "liquidity_score": _round(liquidity_score),
    }
    uncertainty = _uncertainty(profile, evidence_rows)
    sorted_evidence_ids = [row["feature_id"] for row in sorted(evidence_rows, key=lambda row: _safe_float(row.get("wealth_relevance"), 0.0) + _safe_float(row.get("strength"), 0.0), reverse=True)]
    wealth_conclusions = [
        {
            "conclusion_id": "wealth_conclusion_1",
            "topic": "wealth",
            "claim": f"财富结构判断：当前更接近「{WEALTH_TYPE_LABELS.get(wealth_type, wealth_type)}」。这不是收益承诺，而是基于财星状态、食伤输出、结构引动与日主承载力形成的财富域判断。",
            "confidence": _round(1.0 - _safe_float(uncertainty.get("score"), 0.35)),
            "evidence_ids": sorted_evidence_ids[:4],
            "generated_by": WEALTH_DOMAIN_VERSION,
            "scope": "wealth_domain_only",
        },
        {
            "conclusion_id": "wealth_conclusion_2",
            "topic": "wealth",
            "claim": "核心依据：财星强弱决定财富信号底盘，食伤决定赚钱机会，结构引动影响流动性，比劫与官杀决定分利、规则和风险压力。",
            "confidence": _round(max(0.1, stability_score * 0.44 + (1.0 - risk_score) * 0.36)),
            "evidence_ids": sorted_evidence_ids[:5],
            "generated_by": WEALTH_DOMAIN_VERSION,
            "scope": "wealth_domain_only",
        },
        {
            "conclusion_id": "wealth_conclusion_3",
            "topic": "wealth",
            "claim": "风险与不确定性：当前判断需要保留现实现金流、职业选择、合作分利和回款节奏等变量，不应解读成长期财富定论。",
            "confidence": _round(max(0.1, 1.0 - _safe_float(uncertainty.get("score"), 0.35))),
            "evidence_ids": sorted_evidence_ids[:5],
            "generated_by": WEALTH_DOMAIN_VERSION,
            "scope": "wealth_domain_only",
        },
    ]
    if kb_evidence_rows:
        wealth_conclusions.append(
            {
                "conclusion_id": "wealth_conclusion_kb_calibration",
                "topic": "wealth",
                "claim": "知识库校准补充：5条已审核财富知识单元被转化为实验性证据，用于校准财星、食伤、财库、比劫与官杀对财富输出的解释。",
                "confidence": _round(max(0.1, 1.0 - _safe_float(uncertainty.get("score"), 0.35))),
                "evidence_ids": [row["feature_id"] for row in kb_evidence_rows[:5]],
                "generated_by": WEALTH_DOMAIN_VERSION,
                "scope": "wealth_domain_only",
                "experimental": True,
            }
        )
    knowledge_integration = {
        "knowledge_mode": knowledge_mode,
        "experimental": knowledge_mode == "kb_augmented",
        "source": WEALTH_KB_CALIBRATION_SOURCE if knowledge_mode == "kb_augmented" else "",
        "kb_evidence_count": len(kb_evidence_rows),
        "baseline_evidence_count": baseline_evidence_count,
        "augmented_evidence_count": len(evidence_rows),
        "score_deltas": kb_deltas,
        "comparison": {
            "wealth_type_before": baseline_profile["wealth_type"],
            "wealth_type_after": profile["wealth_type"],
            "wealth_type_changed": baseline_profile["wealth_type"] != profile["wealth_type"],
            "evidence_count_before": baseline_evidence_count,
            "evidence_count_after": len(evidence_rows),
            "evidence_count_delta": len(evidence_rows) - baseline_evidence_count,
            "kb_source_present": bool(kb_evidence_rows),
            "explanation_quality": "kb_reviewed_units_added" if kb_evidence_rows else "baseline_only",
        },
    }
    payload_out = {
        "source_core_bundle_id": source_core_bundle_id,
        "source_strength_bundle_id": source_strength_bundle_id,
        "source_structure_bundle_id": source_structure_bundle_id,
        "user_intent": intent,
        "knowledge_mode": knowledge_mode,
        "experimental": knowledge_mode == "kb_augmented",
        "knowledge_integration": knowledge_integration,
        "wealth_profile": profile,
        "wealth_evidence": evidence_rows,
        "wealth_conclusions": wealth_conclusions,
        "uncertainty": uncertainty,
        "supported_intents": sorted(SUPPORTED_WEALTH_INTENTS),
        "guardrails": {
            "wealth_domain_only": True,
            "no_general_life_verdict": True,
            "no_career_verdict": True,
            "no_relationship_verdict": True,
            "no_health_verdict": True,
            "requires_prediction_contract": True,
            "llm_contract_only": True,
        },
        "version": WEALTH_DOMAIN_VERSION,
        "schema_version": WEALTH_DOMAIN_SCHEMA_VERSION,
    }
    digest = _payload_hash(payload_out)
    return {
        "wealth_bundle_id": f"wealth_domain_bundle_{digest[:16]}",
        **payload_out,
        "created_at": _utcnow_iso(),
    }


def _evidence_digest(rows: Iterable[Mapping[str, Any]]) -> list[Dict[str, Any]]:
    return [
        {
            "feature_id": _safe_str(row.get("feature_id")),
            "feature_type": _safe_str(row.get("feature_type")),
            "source": _safe_str(row.get("source")),
            "strength": _safe_float(row.get("strength"), 0.0),
            "stability": _safe_float(row.get("stability"), 0.0),
            "risk": _safe_float(row.get("risk"), 0.0),
            "source_knowledge_id": _safe_str(row.get("source_knowledge_id")),
        }
        for row in rows
        if isinstance(row, Mapping)
    ]


def _changed_profile_fields(baseline: Mapping[str, Any], augmented: Mapping[str, Any]) -> list[str]:
    changed: list[str] = []
    before = dict(baseline.get("wealth_profile") or {})
    after = dict(augmented.get("wealth_profile") or {})
    for key in ["wealth_type", "opportunity_score", "stability_score", "risk_score", "accumulation_score", "liquidity_score"]:
        before_value = before.get(key)
        after_value = after.get(key)
        if isinstance(before_value, (int, float)) or isinstance(after_value, (int, float)):
            if abs(_safe_float(after_value) - _safe_float(before_value)) >= 0.001:
                changed.append(key)
        elif _safe_str(before_value) != _safe_str(after_value):
            changed.append(key)
    before_count = len(_ensure_list(baseline.get("wealth_evidence")))
    after_count = len(_ensure_list(augmented.get("wealth_evidence")))
    if after_count != before_count:
        changed.append("evidence_count")
    if len(_ensure_list(augmented.get("wealth_conclusions"))) != len(_ensure_list(baseline.get("wealth_conclusions"))):
        changed.append("explanation")
    return changed


def _direction_is_reasonable(
    *,
    expected_direction: str,
    baseline: Mapping[str, Any],
    augmented: Mapping[str, Any],
    kb_rows: list[Mapping[str, Any]],
    changed_fields: list[str],
) -> bool:
    if not kb_rows or "evidence_count" not in changed_fields:
        return False
    before = dict(baseline.get("wealth_profile") or {})
    after = dict(augmented.get("wealth_profile") or {})
    before_type = _safe_str(before.get("wealth_type"))
    after_type = _safe_str(after.get("wealth_type"))
    risk_up = _safe_float(after.get("risk_score")) >= _safe_float(before.get("risk_score")) - 0.001
    opportunity_up = _safe_float(after.get("opportunity_score")) >= _safe_float(before.get("opportunity_score")) - 0.001
    stability_up = _safe_float(after.get("stability_score")) >= _safe_float(before.get("stability_score")) - 0.001
    accumulation_up = _safe_float(after.get("accumulation_score")) >= _safe_float(before.get("accumulation_score")) - 0.001
    liquidity_up = _safe_float(after.get("liquidity_score")) >= _safe_float(before.get("liquidity_score")) - 0.001
    liquidity_down_or_stable = _safe_float(after.get("liquidity_score")) <= _safe_float(before.get("liquidity_score")) + 0.04
    kb_types = {_safe_str(row.get("feature_type")) for row in kb_rows}
    direction = _safe_str(expected_direction)
    if direction == "wealth_pressure_reinforced":
        return risk_up and after_type in {"volatile", "constrained", "leakage_risk", before_type}
    if direction == "weak_signal_reinforced":
        return after_type == "weak_signal" or _safe_float(after.get("opportunity_score")) <= 0.46
    if direction == "output_conversion_reinforced":
        return opportunity_up and "output_generate_wealth" in kb_types
    if direction == "blocked_conversion_reinforced":
        return risk_up or after_type in {"volatile", "constrained"}
    if direction == "vault_storage_reinforced":
        return accumulation_up or stability_up
    if direction == "vault_liquidity_risk_reinforced":
        return liquidity_up or risk_up or after_type == "volatile"
    if direction == "locked_accumulation_reinforced":
        return accumulation_up or (stability_up and liquidity_down_or_stable)
    if direction == "competition_risk_reinforced":
        return risk_up or after_type == "leakage_risk" or "peer_competition" in kb_types
    if direction == "constraint_reinforced":
        return risk_up or after_type == "constrained" or "wealth_constraint" in kb_types
    if direction == "conflict_uncertainty_reinforced":
        return risk_up or after_type == "volatile"
    if direction == "latent_signal_reinforced":
        return after_type == "weak_signal" or _safe_float(after.get("opportunity_score")) <= 0.44
    if direction == "flow_activation_reinforced":
        return liquidity_up or opportunity_up
    return bool(changed_fields)


def evaluate_wealth_kb_calibration_v2_case(payload: Mapping[str, Any]) -> Dict[str, Any]:
    case_name = _safe_str(payload.get("case"), "wealth_kb_calibration_case")
    expected_direction = _safe_str(payload.get("expected_direction"), "kb_evidence_added")
    baseline_payload = {
        "core_feature_bundle": _coerce_core_bundle(payload),
        "core_strength_bundle": _coerce_strength_bundle(payload),
        "structure_effect_bundle": _coerce_structure_bundle(payload),
        "user_intent": _safe_str(payload.get("user_intent") or payload.get("intent"), "wealth_prediction"),
        "knowledge_mode": "baseline_only",
    }
    baseline = evaluate_wealth_domain(baseline_payload)
    augmented = evaluate_wealth_domain({**baseline_payload, "knowledge_mode": "kb_augmented"})
    kb_rows = [
        row
        for row in _ensure_list(augmented.get("wealth_evidence"))
        if isinstance(row, Mapping) and _safe_str(row.get("source")) == WEALTH_KB_CALIBRATION_SOURCE
    ]
    changed_fields = _changed_profile_fields(baseline, augmented)
    is_reasonable = _direction_is_reasonable(
        expected_direction=expected_direction,
        baseline=baseline,
        augmented=augmented,
        kb_rows=kb_rows,
        changed_fields=changed_fields,
    )
    comparison = dict(dict(augmented.get("knowledge_integration") or {}).get("comparison") or {})
    notes = _safe_str(payload.get("notes"))
    if not notes:
        notes = "KB reviewed units entered calibration evidence and profile deltas remain bounded." if is_reasonable else "KB calibration output did not match the expected direction."
    return {
        "case": case_name,
        "wealth_type_before": _safe_str(dict(baseline.get("wealth_profile") or {}).get("wealth_type")),
        "wealth_type_after": _safe_str(dict(augmented.get("wealth_profile") or {}).get("wealth_type")),
        "expected_direction": expected_direction,
        "is_reasonable": is_reasonable,
        "notes": notes,
        "baseline": {
            "wealth_type": _safe_str(dict(baseline.get("wealth_profile") or {}).get("wealth_type")),
            "evidence": _evidence_digest(_ensure_list(baseline.get("wealth_evidence"))),
        },
        "kb_augmented": {
            "wealth_type_after": _safe_str(dict(augmented.get("wealth_profile") or {}).get("wealth_type")),
            "evidence_after": _evidence_digest(_ensure_list(augmented.get("wealth_evidence"))),
            "kb_evidence_count": len(kb_rows),
            "changed_fields": changed_fields,
        },
        "comparison": comparison,
    }


class WealthDomainStore:
    def __init__(self, storage_file: Optional[Path] = None) -> None:
        self.storage_file = storage_file or (RUNTIME_DIR / "v18_1_wealth_domain_bundles.json")
        self._bundles: Dict[str, Dict[str, Any]] = {}
        self._load()

    def _load(self) -> None:
        if not self.storage_file.exists():
            self._bundles = {}
            return
        try:
            data = json.loads(self.storage_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            self._bundles = {}
            return
        self._bundles = {str(k): dict(v) for k, v in data.items() if isinstance(v, Mapping)}

    def _save(self) -> None:
        self.storage_file.parent.mkdir(parents=True, exist_ok=True)
        self.storage_file.write_text(json.dumps(self._bundles, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    def evaluate_and_store(self, payload: Mapping[str, Any]) -> Dict[str, Any]:
        bundle = evaluate_wealth_domain(payload)
        self._bundles[bundle["wealth_bundle_id"]] = bundle
        self._save()
        return bundle

    def get_bundle(self, wealth_bundle_id: str) -> Dict[str, Any]:
        key = _safe_str(wealth_bundle_id)
        bundle = self._bundles.get(key)
        if not bundle:
            self._load()
            bundle = self._bundles.get(key)
        if not bundle:
            raise PredictiveServiceError("WEALTH_DOMAIN_BUNDLE_NOT_FOUND", "wealth domain bundle not found", status=404)
        return dict(bundle)


wealth_domain_service = WealthDomainStore()
