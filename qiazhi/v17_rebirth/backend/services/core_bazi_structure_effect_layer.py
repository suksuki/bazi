from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Optional

from v17_rebirth.backend.services.core_bazi_feature_layer import core_bazi_feature_service
from v17_rebirth.backend.services.core_bazi_strength_model import core_bazi_strength_service
from v17_rebirth.backend.services.v18_1_predictive_engine import PredictiveServiceError
from v17_rebirth.paths import RUNTIME_DIR


CORE_STRUCTURE_EFFECT_VERSION = "core_structure_effect_layer_v1"
CORE_STRUCTURE_EFFECT_SCHEMA_VERSION = "core_structure_effect_bundle.v1"

HARMONY_TYPES = {"six_harmony", "hidden_harmony", "three_harmony", "three_meeting", "half_harmony", "arch_harmony"}
DISRUPTIVE_TYPES = {"clash", "harm", "break", "punishment"}

HARMONY_EFFECTS: Dict[str, Dict[str, float]] = {
    "three_meeting": {"stability": 0.32, "activation": 0.12, "suppression": 0.04, "amplification": 0.48, "risk": 0.08},
    "three_harmony": {"stability": 0.28, "activation": 0.16, "suppression": 0.06, "amplification": 0.42, "risk": 0.10},
    "half_harmony": {"stability": 0.16, "activation": 0.10, "suppression": 0.04, "amplification": 0.24, "risk": 0.08},
    "arch_harmony": {"stability": 0.12, "activation": 0.08, "suppression": 0.04, "amplification": 0.18, "risk": 0.07},
    "six_harmony": {"stability": 0.18, "activation": 0.06, "suppression": 0.08, "amplification": 0.12, "risk": 0.06},
    "hidden_harmony": {"stability": 0.10, "activation": 0.04, "suppression": 0.06, "amplification": 0.08, "risk": 0.05},
}

DISRUPTIVE_EFFECTS: Dict[str, Dict[str, float]] = {
    "clash": {"stability": -0.34, "activation": 0.46, "suppression": 0.08, "amplification": 0.06, "risk": 0.42},
    "harm": {"stability": -0.22, "activation": 0.12, "suppression": 0.18, "amplification": 0.00, "risk": 0.34},
    "break": {"stability": -0.26, "activation": 0.18, "suppression": 0.16, "amplification": 0.00, "risk": 0.38},
    "punishment": {"stability": -0.30, "activation": 0.16, "suppression": 0.22, "amplification": 0.00, "risk": 0.44},
}

VAULT_BRANCHES: Dict[str, Dict[str, str]] = {
    "辰": {"stored_element": "water", "stored_element_label": "水"},
    "戌": {"stored_element": "fire", "stored_element_label": "火"},
    "丑": {"stored_element": "metal", "stored_element_label": "金"},
    "未": {"stored_element": "wood", "stored_element_label": "木"},
}

GROUP_TO_STRUCTURAL_TARGET: Dict[str, str] = {
    "day_master": "body_structure",
    "peer": "peer_structure",
    "resource": "seal_structure",
    "output": "output_structure",
    "wealth": "wealth_structure",
    "officer": "officer_killing_structure",
}

GROUP_TO_STRENGTH_KEY: Dict[str, str] = {
    "peer": "peer",
    "resource": "seal",
    "output": "output",
    "wealth": "wealth",
    "officer": "officer_killing",
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


def _clamp_signed(value: float) -> float:
    return max(-1.0, min(1.0, float(value)))


def _round_signed(value: float, digits: int = 3) -> float:
    return round(_clamp_signed(value), digits)


def _coerce_core_bundle(payload: Mapping[str, Any]) -> Dict[str, Any]:
    nested = payload.get("core_feature_bundle") or payload.get("feature_bundle")
    if isinstance(nested, Mapping):
        return dict(nested)
    if "features" in payload and "bundle_id" in payload:
        return dict(payload)
    bundle_id = _safe_str(payload.get("core_bundle_id") or payload.get("source_core_bundle_id") or payload.get("bundle_id"))
    if bundle_id:
        return core_bazi_feature_service.get_bundle(bundle_id)
    raise PredictiveServiceError("CORE_STRUCTURE_INPUT_INVALID", "core_feature_bundle is required", status=400)


def _coerce_strength_bundle(payload: Mapping[str, Any]) -> Dict[str, Any]:
    nested = payload.get("core_strength_bundle") or payload.get("strength_bundle")
    if isinstance(nested, Mapping):
        return dict(nested)
    if "day_master_strength" in payload and "strength_bundle_id" in payload:
        return dict(payload)
    bundle_id = _safe_str(payload.get("strength_bundle_id") or payload.get("source_strength_bundle_id"))
    if bundle_id:
        return core_bazi_strength_service.get_bundle(bundle_id)
    raise PredictiveServiceError("CORE_STRUCTURE_INPUT_INVALID", "core_strength_bundle is required", status=400)


def _feature(bundle: Mapping[str, Any], name: str) -> Dict[str, Any]:
    features = bundle.get("features")
    if not isinstance(features, Mapping):
        raise PredictiveServiceError("CORE_STRUCTURE_INPUT_INVALID", "features are required", status=400)
    item = features.get(name)
    if not isinstance(item, Mapping):
        raise PredictiveServiceError("CORE_STRUCTURE_INPUT_INVALID", f"missing feature: {name}", status=400)
    return dict(item)


def _relations(core_bundle: Mapping[str, Any]) -> list[Dict[str, Any]]:
    relation_feature = _feature(core_bundle, "relation_hits")
    output = relation_feature.get("output") if isinstance(relation_feature.get("output"), Mapping) else {}
    raw = output.get("relations") if isinstance(output.get("relations"), list) else []
    return [dict(item) for item in raw if isinstance(item, Mapping)]


def _month_support(core_bundle: Mapping[str, Any]) -> Dict[str, Any]:
    month = _feature(core_bundle, "month_command")
    output = month.get("output") if isinstance(month.get("output"), Mapping) else {}
    command = output.get("month_command") if isinstance(output.get("month_command"), Mapping) else {}
    support = command.get("season_support") if isinstance(command.get("season_support"), Mapping) else {}
    return dict(support)


def _element_to_group(core_bundle: Mapping[str, Any]) -> Dict[str, str]:
    mapping: Dict[str, str] = {}
    for group, row in _month_support(core_bundle).items():
        if not isinstance(row, Mapping):
            continue
        element = _safe_str(row.get("element"))
        if not element:
            continue
        if group == "day_master":
            mapping[element] = "peer"
        else:
            mapping[element] = _safe_str(group)
    return mapping


def _branches_by_scope(core_bundle: Mapping[str, Any]) -> Dict[str, str]:
    normalized = core_bundle.get("normalized_chart") if isinstance(core_bundle.get("normalized_chart"), Mapping) else {}
    pillars = normalized.get("pillars") if isinstance(normalized.get("pillars"), Mapping) else {}
    runtime = normalized.get("runtime") if isinstance(normalized.get("runtime"), Mapping) else {}
    branches: Dict[str, str] = {}
    for scope, pillar in {**pillars, **runtime}.items():
        text = _safe_str(pillar)
        if len(text) >= 2:
            branches[_safe_str(scope)] = text[-1]
    return branches


def _strength_snapshot(strength_bundle: Mapping[str, Any], target_group: str) -> Dict[str, Any]:
    if target_group == "day_master":
        row = strength_bundle.get("day_master_strength") if isinstance(strength_bundle.get("day_master_strength"), Mapping) else {}
        return {
            "strength_axis": "day_master",
            "score": row.get("support_score"),
            "pressure_score": row.get("pressure_score"),
            "tendency": row.get("tendency"),
        }
    strength_key = GROUP_TO_STRENGTH_KEY.get(target_group, "")
    strengths = strength_bundle.get("ten_god_strengths") if isinstance(strength_bundle.get("ten_god_strengths"), Mapping) else {}
    row = strengths.get(strength_key) if isinstance(strengths.get(strength_key), Mapping) else {}
    return {
        "strength_axis": strength_key or "unknown",
        "score": row.get("score"),
        "tendency": row.get("tendency"),
    }


def _target_from_element(core_bundle: Mapping[str, Any], strength_bundle: Mapping[str, Any], target_element: str) -> Dict[str, Any]:
    element = _safe_str(target_element)
    group = _element_to_group(core_bundle).get(element, "unknown")
    return {
        "target_element": element,
        "target_group": group,
        "structural_target": GROUP_TO_STRUCTURAL_TARGET.get(group, "unclassified_structure"),
        "strength_snapshot": _strength_snapshot(strength_bundle, group),
    }


def _relation_effect(core_bundle: Mapping[str, Any], strength_bundle: Mapping[str, Any], relation: Mapping[str, Any]) -> Dict[str, Any]:
    relation_type = _safe_str(relation.get("relation_type"))
    target = _target_from_element(core_bundle, strength_bundle, _safe_str(relation.get("target_element")))
    if relation_type in HARMONY_TYPES:
        base = HARMONY_EFFECTS.get(relation_type, HARMONY_EFFECTS["six_harmony"])
        effect_type = "structure_combination"
    elif relation_type in DISRUPTIVE_TYPES:
        base = DISRUPTIVE_EFFECTS.get(relation_type, DISRUPTIVE_EFFECTS["harm"])
        effect_type = "structure_disruption"
    else:
        base = {"stability": 0.0, "activation": 0.0, "suppression": 0.0, "amplification": 0.0, "risk": 0.0}
        effect_type = "structure_observation"
    return {
        "effect_id": f"structure_effect_{_payload_hash({'relation': relation})[:14]}",
        "source_relation": {
            "relation_type": relation_type,
            "branches": list(relation.get("branches") or []),
            "pillars": list(relation.get("pillars") or []),
            "scope": _safe_str(relation.get("scope"), "natal"),
            "completeness": _safe_str(relation.get("completeness")),
        },
        "target": target,
        "effect_type": effect_type,
        "stability_effect": _round_signed(base["stability"]),
        "activation_effect": _round_signed(base["activation"]),
        "suppression_effect": _round_signed(base["suppression"]),
        "amplification_effect": _round_signed(base["amplification"]),
        "risk_effect": _round_signed(base["risk"]),
        "evidence_refs": ["core.relation_hits"],
        "boundary": "structure_effect_only_no_domain_conclusion",
    }


def _relations_for_branch(relations: Iterable[Mapping[str, Any]], branch: str) -> list[Mapping[str, Any]]:
    return [item for item in relations if branch in set(str(x) for x in (item.get("branches") or []))]


def _vault_status(branch_relations: list[Mapping[str, Any]]) -> str:
    relation_types = {_safe_str(item.get("relation_type")) for item in branch_relations}
    if "clash" in relation_types:
        return "opened_by_clash"
    if relation_types & {"punishment", "harm", "break"}:
        return "blocked_by_disruptive_relation"
    if relation_types & HARMONY_TYPES:
        return "locked_by_combination"
    return "closed"


def _vault_effect_numbers(status: str) -> Dict[str, float]:
    if status == "opened_by_clash":
        return {"stability": -0.28, "activation": 0.62, "suppression": 0.02, "amplification": 0.12, "risk": 0.52, "liquidity": 0.64}
    if status == "locked_by_combination":
        return {"stability": 0.24, "activation": -0.18, "suppression": 0.20, "amplification": 0.08, "risk": 0.16, "liquidity": -0.24}
    if status == "blocked_by_disruptive_relation":
        return {"stability": -0.30, "activation": 0.10, "suppression": 0.34, "amplification": 0.00, "risk": 0.46, "liquidity": -0.18}
    return {"stability": 0.08, "activation": 0.00, "suppression": 0.06, "amplification": 0.00, "risk": 0.06, "liquidity": -0.08}


def _vault_effects(core_bundle: Mapping[str, Any], strength_bundle: Mapping[str, Any], relations: list[Mapping[str, Any]]) -> list[Dict[str, Any]]:
    branches = _branches_by_scope(core_bundle)
    element_group = _element_to_group(core_bundle)
    effects: list[Dict[str, Any]] = []
    for scope, branch in branches.items():
        if branch not in VAULT_BRANCHES:
            continue
        meta = VAULT_BRANCHES[branch]
        stored_element = meta["stored_element"]
        target_group = element_group.get(stored_element, "unknown")
        status = _vault_status(_relations_for_branch(relations, branch))
        numbers = _vault_effect_numbers(status)
        effects.append(
            {
                "effect_id": f"vault_effect_{scope}_{branch}_{status}",
                "vault_branch": branch,
                "scope": scope,
                "stored_element": stored_element,
                "stored_element_label": meta["stored_element_label"],
                "target": {
                    "target_element": stored_element,
                    "target_group": target_group,
                    "structural_target": f"{target_group}_vault" if target_group != "unknown" else "unclassified_vault",
                    "strength_snapshot": _strength_snapshot(strength_bundle, target_group),
                },
                "vault_state": status,
                "stability_effect": _round_signed(numbers["stability"]),
                "activation_effect": _round_signed(numbers["activation"]),
                "suppression_effect": _round_signed(numbers["suppression"]),
                "amplification_effect": _round_signed(numbers["amplification"]),
                "risk_effect": _round_signed(numbers["risk"]),
                "liquidity_effect": _round_signed(numbers["liquidity"]),
                "evidence_refs": ["core.relation_hits", "core.hidden_stems"],
                "boundary": "vault_structure_only_no_wealth_conclusion",
            }
        )
    return effects


def _aggregate_effects(effects: Iterable[Mapping[str, Any]]) -> Dict[str, float]:
    rows = list(effects)
    if not rows:
        return {
            "stability_effect": 0.0,
            "activation_effect": 0.0,
            "suppression_effect": 0.0,
            "amplification_effect": 0.0,
            "risk_effect": 0.0,
        }
    return {
        "stability_effect": _round_signed(sum(_safe_float(row.get("stability_effect")) for row in rows) / max(1.0, len(rows) ** 0.5)),
        "activation_effect": _round_signed(sum(_safe_float(row.get("activation_effect")) for row in rows) / max(1.0, len(rows) ** 0.5)),
        "suppression_effect": _round_signed(sum(_safe_float(row.get("suppression_effect")) for row in rows) / max(1.0, len(rows) ** 0.5)),
        "amplification_effect": _round_signed(sum(_safe_float(row.get("amplification_effect")) for row in rows) / max(1.0, len(rows) ** 0.5)),
        "risk_effect": _round_signed(sum(_safe_float(row.get("risk_effect")) for row in rows) / max(1.0, len(rows) ** 0.5)),
    }


def evaluate_core_structure_effect(payload: Mapping[str, Any]) -> Dict[str, Any]:
    core_bundle = _coerce_core_bundle(payload)
    strength_bundle = _coerce_strength_bundle(payload)
    core_bundle_id = _safe_str(core_bundle.get("bundle_id"))
    strength_bundle_id = _safe_str(strength_bundle.get("strength_bundle_id"))
    if not core_bundle_id or not strength_bundle_id:
        raise PredictiveServiceError("CORE_STRUCTURE_INPUT_INVALID", "core and strength bundle ids are required", status=400)

    relation_rows = _relations(core_bundle)
    relation_effects = [_relation_effect(core_bundle, strength_bundle, relation) for relation in relation_rows]
    vault_effects = _vault_effects(core_bundle, strength_bundle, relation_rows)
    all_effects = [*relation_effects, *vault_effects]
    payload_out = {
        "source_core_bundle_id": core_bundle_id,
        "source_strength_bundle_id": strength_bundle_id,
        "source_core_bundle_version": _safe_str(core_bundle.get("version")),
        "source_strength_bundle_version": _safe_str(strength_bundle.get("version")),
        "relation_effects": relation_effects,
        "vault_effects": vault_effects,
        "effect_summary": _aggregate_effects(all_effects),
        "evidence_refs": [
            "core.relation_hits",
            "core.hidden_stems",
            "core.month_command",
            "core_strength_model_v1",
        ],
        "guardrails": {
            "structure_effect_evidence_only": True,
            "no_domain_conclusion": True,
            "no_pattern_verdict": True,
            "no_use_god_verdict": True,
            "no_prediction_id": True,
            "no_ledger_write": True,
            "no_narrative": True,
        },
        "version": CORE_STRUCTURE_EFFECT_VERSION,
        "schema_version": CORE_STRUCTURE_EFFECT_SCHEMA_VERSION,
    }
    digest = _payload_hash(payload_out)
    return {
        "structure_bundle_id": f"core_structure_bundle_{digest[:16]}",
        **payload_out,
        "created_at": _utcnow_iso(),
    }


class CoreBaziStructureEffectStore:
    def __init__(self, storage_file: Optional[Path] = None) -> None:
        self.storage_file = storage_file or (RUNTIME_DIR / "v18_1_core_bazi_structure_effect_bundles.json")
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
        bundle = evaluate_core_structure_effect(payload)
        self._bundles[bundle["structure_bundle_id"]] = bundle
        self._save()
        return bundle

    def get_bundle(self, structure_bundle_id: str) -> Dict[str, Any]:
        key = _safe_str(structure_bundle_id)
        bundle = self._bundles.get(key)
        if not bundle:
            self._load()
            bundle = self._bundles.get(key)
        if not bundle:
            raise PredictiveServiceError("CORE_STRUCTURE_BUNDLE_NOT_FOUND", "core structure effect bundle not found", status=404)
        return dict(bundle)


core_bazi_structure_effect_service = CoreBaziStructureEffectStore()
