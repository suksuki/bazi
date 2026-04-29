from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Optional

from v17_rebirth.backend.services.core_bazi_feature_layer import core_bazi_feature_service
from v17_rebirth.backend.services.v18_1_predictive_engine import PredictiveServiceError
from v17_rebirth.paths import RUNTIME_DIR


CORE_STRENGTH_MODEL_VERSION = "core_strength_model_v1"
CORE_STRENGTH_SCHEMA_VERSION = "core_strength_bundle.v1"

SUPPORT_LABEL_SCORE: Dict[str, float] = {
    "strong": 0.9,
    "medium": 0.62,
    "weak": 0.34,
    "residual": 0.14,
}

VISIBLE_SCOPE_WEIGHTS: Dict[str, float] = {
    "year_stem": 0.58,
    "month_stem": 1.0,
    "day_stem": 0.0,
    "hour_stem": 0.72,
}

TEN_GOD_GROUP_TO_OUTPUT_KEY: Dict[str, str] = {
    "wealth": "wealth",
    "officer": "officer_killing",
    "output": "output",
    "resource": "seal",
    "peer": "peer",
}

STRENGTH_GROUP_SPECS: Dict[str, Dict[str, Any]] = {
    "wealth": {"root_key": "wealth", "season_key": "wealth", "visible_groups": {"wealth"}},
    "officer_killing": {"root_key": "officer", "season_key": "officer", "visible_groups": {"officer"}},
    "output": {"root_key": "output", "season_key": "output", "visible_groups": {"output"}},
    "seal": {"root_key": "resource", "season_key": "resource", "visible_groups": {"resource"}},
    "peer": {"root_key": "peer", "season_key": "day_master", "visible_groups": {"peer"}},
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


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _round(value: float, digits: int = 3) -> float:
    return round(_clamp01(value), digits)


def _coerce_core_bundle(payload: Mapping[str, Any]) -> Dict[str, Any]:
    if "features" in payload and "bundle_id" in payload:
        return dict(payload)
    nested = payload.get("core_feature_bundle") or payload.get("feature_bundle") or payload.get("bundle")
    if isinstance(nested, Mapping):
        return dict(nested)
    bundle_id = _safe_str(payload.get("bundle_id") or payload.get("source_core_bundle_id"))
    if bundle_id:
        return core_bazi_feature_service.get_bundle(bundle_id)
    raise PredictiveServiceError("CORE_STRENGTH_INPUT_INVALID", "core_feature_bundle is required", status=400)


def _feature(bundle: Mapping[str, Any], name: str) -> Dict[str, Any]:
    features = bundle.get("features")
    if not isinstance(features, Mapping):
        raise PredictiveServiceError("CORE_STRENGTH_INPUT_INVALID", "features are required", status=400)
    item = features.get(name)
    if not isinstance(item, Mapping):
        raise PredictiveServiceError("CORE_STRENGTH_INPUT_INVALID", f"missing feature: {name}", status=400)
    return dict(item)


def _rootedness(bundle: Mapping[str, Any]) -> Dict[str, Any]:
    root = _feature(bundle, "root_strength")
    output = root.get("output") if isinstance(root.get("output"), Mapping) else {}
    rooted = output.get("rootedness") if isinstance(output.get("rootedness"), Mapping) else {}
    return dict(rooted)


def _month_command(bundle: Mapping[str, Any]) -> Dict[str, Any]:
    month = _feature(bundle, "month_command")
    output = month.get("output") if isinstance(month.get("output"), Mapping) else {}
    command = output.get("month_command") if isinstance(output.get("month_command"), Mapping) else {}
    return dict(command)


def _visible_ten_gods(bundle: Mapping[str, Any]) -> Dict[str, Any]:
    mapping = _feature(bundle, "ten_god_mapping")
    output = mapping.get("output") if isinstance(mapping.get("output"), Mapping) else {}
    ten_gods = output.get("ten_gods") if isinstance(output.get("ten_gods"), Mapping) else {}
    visible = ten_gods.get("visible") if isinstance(ten_gods.get("visible"), Mapping) else {}
    return dict(visible)


def _season_score(bundle: Mapping[str, Any], key: str) -> float:
    support = _month_command(bundle).get("season_support")
    if not isinstance(support, Mapping):
        return 0.0
    row = support.get(key)
    if not isinstance(row, Mapping):
        return 0.0
    label = _safe_str(row.get("support"))
    if label in SUPPORT_LABEL_SCORE:
        return SUPPORT_LABEL_SCORE[label]
    multiplier = _safe_float(row.get("season_multiplier"), 1.0)
    return _clamp01(multiplier / 2.5)


def _root_score(bundle: Mapping[str, Any], key: str) -> float:
    rooted = _rootedness(bundle)
    if key == "day_master":
        day = rooted.get("day_master") if isinstance(rooted.get("day_master"), Mapping) else {}
        return _clamp01(_safe_float(day.get("root_score")))
    roots = rooted.get("ten_god_roots") if isinstance(rooted.get("ten_god_roots"), Mapping) else {}
    row = roots.get(key) if isinstance(roots.get(key), Mapping) else {}
    return _clamp01(_safe_float(row.get("root_score")))


def _visible_score(bundle: Mapping[str, Any], groups: Iterable[str]) -> float:
    wanted = set(groups)
    raw = 0.0
    for position, entry in _visible_ten_gods(bundle).items():
        if not isinstance(entry, Mapping):
            continue
        if _safe_str(entry.get("ten_god")) == "日主":
            continue
        group = _safe_str(entry.get("ten_god_group"))
        if group in wanted:
            raw += VISIBLE_SCOPE_WEIGHTS.get(_safe_str(position), 0.55)
    return _clamp01(raw / 1.35)


def _strength_label(score: float) -> str:
    if score >= 0.72:
        return "strong"
    if score >= 0.52:
        return "moderate"
    if score >= 0.34:
        return "present"
    return "weak"


def _day_tendency(support_score: float, pressure_score: float) -> str:
    diff = support_score - pressure_score
    if diff >= 0.22:
        return "strong"
    if diff >= 0.10:
        return "leaning_strong"
    if diff <= -0.22:
        return "weak"
    if diff <= -0.10:
        return "leaning_weak"
    return "balanced"


def _ten_god_strengths(bundle: Mapping[str, Any]) -> Dict[str, Dict[str, Any]]:
    strengths: Dict[str, Dict[str, Any]] = {}
    for output_key, spec in STRENGTH_GROUP_SPECS.items():
        root = _root_score(bundle, _safe_str(spec.get("root_key")))
        season = _season_score(bundle, _safe_str(spec.get("season_key")))
        exposed = _visible_score(bundle, spec.get("visible_groups") or set())
        score = _clamp01(root * 0.44 + season * 0.34 + exposed * 0.22)
        strengths[output_key] = {
            "score": _round(score),
            "tendency": _strength_label(score),
            "root_score": _round(root),
            "season_score": _round(season),
            "exposed_score": _round(exposed),
            "evidence_refs": [
                "core.root_strength",
                "core.month_command",
                "core.ten_god_mapping",
            ],
        }
    return strengths


def evaluate_core_strength(payload: Mapping[str, Any]) -> Dict[str, Any]:
    bundle = _coerce_core_bundle(payload)
    source_bundle_id = _safe_str(bundle.get("bundle_id"))
    if not source_bundle_id:
        raise PredictiveServiceError("CORE_STRENGTH_INPUT_INVALID", "source core bundle id is required", status=400)

    ten_god_strengths = _ten_god_strengths(bundle)
    root_score = _root_score(bundle, "day_master")
    season_score = _season_score(bundle, "day_master")
    exposed_peer_score = _visible_score(bundle, {"peer"})
    exposed_seal_score = _visible_score(bundle, {"resource"})
    exposed_support_score = _clamp01(exposed_peer_score * 0.62 + exposed_seal_score * 0.54)
    exposed_pressure_score = _clamp01(
        _visible_score(bundle, {"output"}) * 0.32
        + _visible_score(bundle, {"wealth"}) * 0.32
        + _visible_score(bundle, {"officer"}) * 0.36
    )

    peer_strength = _safe_float(ten_god_strengths["peer"]["score"])
    seal_strength = _safe_float(ten_god_strengths["seal"]["score"])
    output_strength = _safe_float(ten_god_strengths["output"]["score"])
    wealth_strength = _safe_float(ten_god_strengths["wealth"]["score"])
    officer_strength = _safe_float(ten_god_strengths["officer_killing"]["score"])

    support_score = _clamp01(
        root_score * 0.30
        + season_score * 0.22
        + exposed_support_score * 0.18
        + peer_strength * 0.16
        + seal_strength * 0.14
    )
    pressure_score = _clamp01(
        officer_strength * 0.34
        + wealth_strength * 0.28
        + output_strength * 0.24
        + exposed_pressure_score * 0.14
    )
    tendency = _day_tendency(support_score, pressure_score)
    spread = abs(support_score - pressure_score)
    evidence_completeness = 1.0
    uncertainty = _clamp01(0.42 - spread * 0.78 + (1.0 - evidence_completeness) * 0.2)
    confidence = _clamp01(1.0 - uncertainty)

    strength_payload = {
        "source_core_bundle_id": source_bundle_id,
        "source_core_bundle_version": _safe_str(bundle.get("version")),
        "day_master_strength": {
            "support_score": _round(support_score),
            "pressure_score": _round(pressure_score),
            "season_score": _round(season_score),
            "root_score": _round(root_score),
            "exposed_support_score": _round(exposed_support_score),
            "exposed_pressure_score": _round(exposed_pressure_score),
            "tendency": tendency,
            "confidence": _round(confidence),
            "uncertainty": _round(uncertainty),
            "support_components": {
                "root": _round(root_score),
                "season": _round(season_score),
                "exposed_peer": _round(exposed_peer_score),
                "exposed_seal": _round(exposed_seal_score),
                "peer_strength": _round(peer_strength),
                "seal_strength": _round(seal_strength),
            },
            "pressure_components": {
                "output_leakage": _round(output_strength),
                "wealth_consumption": _round(wealth_strength),
                "officer_killing_pressure": _round(officer_strength),
                "exposed_pressure": _round(exposed_pressure_score),
            },
        },
        "ten_god_strengths": ten_god_strengths,
        "evidence_refs": [
            "core.day_master",
            "core.ten_god_mapping",
            "core.hidden_stems",
            "core.root_strength",
            "core.month_command",
        ],
        "guardrails": {
            "strength_evidence_only": True,
            "no_domain_conclusion": True,
            "no_use_god_verdict": True,
            "no_pattern_verdict": True,
            "no_prediction_id": True,
            "no_ledger_write": True,
            "no_narrative": True,
        },
        "version": CORE_STRENGTH_MODEL_VERSION,
        "schema_version": CORE_STRENGTH_SCHEMA_VERSION,
    }
    digest = _payload_hash(strength_payload)
    return {
        "strength_bundle_id": f"core_strength_bundle_{digest[:16]}",
        **strength_payload,
        "created_at": _utcnow_iso(),
    }


class CoreBaziStrengthStore:
    def __init__(self, storage_file: Optional[Path] = None) -> None:
        self.storage_file = storage_file or (RUNTIME_DIR / "v18_1_core_bazi_strength_bundles.json")
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
        bundle = evaluate_core_strength(payload)
        self._bundles[bundle["strength_bundle_id"]] = bundle
        self._save()
        return bundle

    def get_bundle(self, strength_bundle_id: str) -> Dict[str, Any]:
        key = _safe_str(strength_bundle_id)
        bundle = self._bundles.get(key)
        if not bundle:
            self._load()
            bundle = self._bundles.get(key)
        if not bundle:
            raise PredictiveServiceError("CORE_STRENGTH_BUNDLE_NOT_FOUND", "core strength bundle not found", status=404)
        return dict(bundle)


core_bazi_strength_service = CoreBaziStrengthStore()
