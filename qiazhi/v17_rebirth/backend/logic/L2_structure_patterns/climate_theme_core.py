from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Sequence


FINAL_CLIMATE_THEME_KEYS: List[str] = [
    "contract",
    "is_optional_topic",
    "confidence",
    "state",
    "origin_type",
    "thermal_index",
    "moisture_index",
    "climate_tension",
    "favored_gods",
    "strained_gods",
    "pattern_survival",
    "source_focus",
    "narrative_focus",
    "prompt_digest",
    "authority_bridge_mode",
]

TEMPORARY_CLIMATE_THEME_KEYS: List[str] = [
    "climate_theme_raw_scores",
    "climate_theme_scope_ranking",
    "climate_theme_debug_vectors",
    "climate_theme_solver_notes",
]

_PATTERN_LABELS: Dict[str, str] = {
    "印比": "印比护体",
    "印官": "印官共振",
    "食伤财": "食伤财链",
    "财官": "财官路线",
}

_SCOPE_LABELS: Dict[str, str] = {
    "year": "年柱",
    "month": "月柱",
    "day": "日柱",
    "hour": "时柱",
    "luck": "大运",
    "flow": "流年",
}


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, float(value)))


def _clean_label(value: Any) -> str:
    return str(value or "").strip()


def _clean_str_list(values: Sequence[Any] | None) -> List[str]:
    if not isinstance(values, Sequence) or isinstance(values, (str, bytes)):
        return []
    seen: set[str] = set()
    rows: List[str] = []
    for value in values:
        label = _clean_label(value)
        if not label or label in seen:
            continue
        seen.add(label)
        rows.append(label)
    return rows


def _clean_theme_rows(values: Sequence[Any] | None) -> List[Dict[str, Any]]:
    if not isinstance(values, Sequence) or isinstance(values, (str, bytes)):
        return []
    rows: List[Dict[str, Any]] = []
    for value in values:
        if not isinstance(value, dict):
            continue
        cleaned = {str(key).strip(): val for key, val in value.items() if str(key).strip()}
        if cleaned:
            rows.append(cleaned)
    return rows


def build_climate_theme_contract() -> Dict[str, Any]:
    return {
        "contract": "v17.climate.theme.v1",
        "is_optional_topic": True,
        "coexists_with": ["ziping", "pattern_specializations", "blind", "risk_matrix"],
        "authority_bridge_mode": "narrative_only",
        "final_meta_keys": list(FINAL_CLIMATE_THEME_KEYS),
        "temporary_meta_keys": list(TEMPORARY_CLIMATE_THEME_KEYS),
        "narrative_constraints": [
            "调候专题只解释 climate field，不直接回写 L0 原始十神总量。",
            "调候专题可以复述效率、稳定性、优先级、成格存续的变化，但不额外叠加 bias。",
        ],
    }


@dataclass(frozen=True)
class ClimateThemeResult:
    state: str = ""
    origin_type: str = "runtime"
    thermal_index: float = 0.0
    moisture_index: float = 0.0
    climate_tension: float = 0.0
    confidence: float = 0.0
    favored_gods: Sequence[str] = field(default_factory=tuple)
    strained_gods: Sequence[str] = field(default_factory=tuple)
    pattern_survival: Sequence[Dict[str, Any]] = field(default_factory=tuple)
    source_focus: Sequence[Dict[str, Any]] = field(default_factory=tuple)
    narrative_focus: Sequence[str] = field(default_factory=tuple)
    prompt_digest: str = ""

    def to_meta(self) -> Dict[str, Any]:
        return {
            "contract": "v17.climate.theme.v1",
            "is_optional_topic": True,
            "confidence": round(_clamp(self.confidence, 0.0, 1.0), 3),
            "state": _clean_label(self.state),
            "origin_type": _clean_label(self.origin_type) or "runtime",
            "thermal_index": round(float(self.thermal_index), 4),
            "moisture_index": round(float(self.moisture_index), 4),
            "climate_tension": round(float(self.climate_tension), 4),
            "favored_gods": _clean_str_list(self.favored_gods),
            "strained_gods": _clean_str_list(self.strained_gods),
            "pattern_survival": _clean_theme_rows(self.pattern_survival),
            "source_focus": _clean_theme_rows(self.source_focus),
            "narrative_focus": _clean_str_list(self.narrative_focus),
            "prompt_digest": _clean_label(self.prompt_digest),
            "authority_bridge_mode": "narrative_only",
        }


def normalize_climate_theme_meta(value: Any) -> Dict[str, Any]:
    if isinstance(value, ClimateThemeResult):
        return value.to_meta()
    if not isinstance(value, dict):
        return {}
    return ClimateThemeResult(
        state=_clean_label(value.get("state")),
        origin_type=_clean_label(value.get("origin_type")) or "runtime",
        thermal_index=_safe_float(value.get("thermal_index"), 0.0),
        moisture_index=_safe_float(value.get("moisture_index"), 0.0),
        climate_tension=_safe_float(value.get("climate_tension"), 0.0),
        confidence=_safe_float(value.get("confidence"), 0.0),
        favored_gods=tuple(_clean_str_list(value.get("favored_gods"))),
        strained_gods=tuple(_clean_str_list(value.get("strained_gods"))),
        pattern_survival=tuple(_clean_theme_rows(value.get("pattern_survival"))),
        source_focus=tuple(_clean_theme_rows(value.get("source_focus"))),
        narrative_focus=tuple(_clean_str_list(value.get("narrative_focus"))),
        prompt_digest=_clean_label(value.get("prompt_digest")),
    ).to_meta()


def _energy_meta(physics_tensor: Dict[str, Any]) -> Dict[str, Any]:
    meta = physics_tensor.get("energy_meta")
    return meta if isinstance(meta, dict) else {}


def _scope_focus_rows(climate_field: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows = climate_field.get("source_by_scope") if isinstance(climate_field.get("source_by_scope"), dict) else {}
    ranked = sorted(
        (
            (
                scope,
                _safe_float(payload.get("thermal"), 0.0),
                _safe_float(payload.get("moisture"), 0.0),
                abs(_safe_float(payload.get("thermal"), 0.0)) + abs(_safe_float(payload.get("moisture"), 0.0)),
            )
            for scope, payload in rows.items()
            if str(scope).strip() and isinstance(payload, dict)
        ),
        key=lambda item: item[3],
        reverse=True,
    )
    focus: List[Dict[str, Any]] = []
    for scope, thermal, moisture, score in ranked[:4]:
        focus.append(
            {
                "scope": str(scope).strip(),
                "scope_label": _SCOPE_LABELS.get(str(scope).strip(), str(scope).strip()),
                "thermal": round(thermal, 4),
                "moisture": round(moisture, 4),
                "dominance": round(score, 4),
            }
        )
    return focus


def _dominant_origin_type(source_focus: List[Dict[str, Any]]) -> str:
    if not source_focus:
        return "mixed"
    lead = source_focus[0]
    scope = _clean_label(lead.get("scope"))
    if scope == "luck":
        return "luck_background"
    if scope == "flow":
        return "flow_trigger"
    has_runtime = any(_clean_label(row.get("scope")) in {"luck", "flow"} for row in source_focus)
    return "mixed" if has_runtime else "natal"


def _scored_gods(modifier: Dict[str, Any], key: str) -> Dict[str, float]:
    raw = modifier.get(key)
    if not isinstance(raw, dict):
        return {}
    return {
        str(god).strip(): _safe_float(score, 0.0)
        for god, score in raw.items()
        if str(god).strip()
    }


def _rank_climate_gods(modifier: Dict[str, Any]) -> tuple[List[str], List[str]]:
    efficiency = _scored_gods(modifier, "ten_god_efficiency")
    stability = _scored_gods(modifier, "ten_god_stability")
    priority = _scored_gods(modifier, "yongshen_priority_delta")
    scores: Dict[str, float] = {}
    for god in set(efficiency) | set(stability) | set(priority):
        scores[god] = (
            priority.get(god, 0.0) * 1.0
            + efficiency.get(god, 0.0) * 0.72
            + stability.get(god, 0.0) * 0.58
        )
    favored = [god for god, score in sorted(scores.items(), key=lambda item: item[1], reverse=True) if score > 0][:4]
    strained = [god for god, score in sorted(scores.items(), key=lambda item: item[1]) if score < 0][:4]
    return favored, strained


def _pattern_survival_rows(modifier: Dict[str, Any]) -> List[Dict[str, Any]]:
    raw = modifier.get("pattern_survival_delta")
    if not isinstance(raw, dict):
        return []
    rows: List[Dict[str, Any]] = []
    for key, delta in raw.items():
        value = _safe_float(delta, 0.0)
        if value >= 0.12:
            bucket = "存续增强"
        elif value <= -0.12:
            bucket = "存续承压"
        else:
            bucket = "存续平衡"
        rows.append(
            {
                "key": str(key).strip(),
                "label": _PATTERN_LABELS.get(str(key).strip(), str(key).strip()),
                "delta": round(value, 4),
                "bucket": bucket,
            }
        )
    rows.sort(key=lambda item: abs(_safe_float(item.get("delta"), 0.0)), reverse=True)
    return rows[:4]


def _narrative_focus(
    *,
    state: str,
    favored_gods: Sequence[str],
    strained_gods: Sequence[str],
    pattern_rows: Sequence[Dict[str, Any]],
    source_focus: Sequence[Dict[str, Any]],
) -> List[str]:
    rows: List[str] = []
    if state:
        rows.append(f"调候落点为「{state}」，当前气候优先级已进入裁决链。")
    if favored_gods:
        rows.append("调候更顺的十神：" + " / ".join(favored_gods[:3]))
    if strained_gods:
        rows.append("调候更受挤压的十神：" + " / ".join(strained_gods[:3]))
    if pattern_rows:
        dominant = pattern_rows[0]
        rows.append(f"{_clean_label(dominant.get('label'))} 当前「{_clean_label(dominant.get('bucket'))}」")
    if source_focus:
        lead = source_focus[0]
        rows.append(f"当前调候主来源偏向{_clean_label(lead.get('scope_label'))}")
    return rows[:4]


def resolve_climate_theme(physics_tensor: Dict[str, Any]) -> Dict[str, Any]:
    energy_meta = _energy_meta(physics_tensor)
    climate_field = energy_meta.get("climate_field") if isinstance(energy_meta.get("climate_field"), dict) else {}
    modifier = energy_meta.get("climate_modifier_layer") if isinstance(energy_meta.get("climate_modifier_layer"), dict) else {}
    if not climate_field:
        return {"climate_theme": {}, "confidence": 0.0, "target_god": ""}

    thermal_index = _safe_float(climate_field.get("thermal_index"), 0.0)
    moisture_index = _safe_float(climate_field.get("moisture_index"), 0.0)
    climate_tension = _safe_float(climate_field.get("climate_tension"), 0.0)
    state = _clean_label(climate_field.get("state"))
    source_focus = _scope_focus_rows(climate_field)
    favored_gods, strained_gods = _rank_climate_gods(modifier)
    pattern_rows = _pattern_survival_rows(modifier)
    origin_type = _dominant_origin_type(source_focus)
    confidence = _clamp(
        0.42
        + abs(thermal_index) * 0.18
        + abs(moisture_index) * 0.18
        + climate_tension * 0.22
        + (0.08 if favored_gods or strained_gods else 0.0),
        0.0,
        0.92,
    )
    narrative_focus = _narrative_focus(
        state=state,
        favored_gods=favored_gods,
        strained_gods=strained_gods,
        pattern_rows=pattern_rows,
        source_focus=source_focus,
    )
    digest_parts = [state or "调候待定", f"寒热{thermal_index:+.2f}", f"燥湿{moisture_index:+.2f}"]
    if favored_gods:
        digest_parts.append("顺势 " + "/".join(favored_gods[:2]))
    if strained_gods:
        digest_parts.append("承压 " + "/".join(strained_gods[:2]))
    if pattern_rows:
        top_pattern = pattern_rows[0]
        digest_parts.append(f"{_clean_label(top_pattern.get('label'))}{_clean_label(top_pattern.get('bucket'))}")
    result = ClimateThemeResult(
        state=state,
        origin_type=origin_type,
        thermal_index=thermal_index,
        moisture_index=moisture_index,
        climate_tension=climate_tension,
        confidence=confidence,
        favored_gods=tuple(favored_gods),
        strained_gods=tuple(strained_gods),
        pattern_survival=tuple(pattern_rows),
        source_focus=tuple(source_focus),
        narrative_focus=tuple(narrative_focus),
        prompt_digest="；".join(part for part in digest_parts if part),
    )
    meta = result.to_meta()
    return {
        "contract": meta["contract"],
        "confidence": meta["confidence"],
        "target_god": (meta.get("favored_gods") or meta.get("strained_gods") or [""])[0],
        "climate_theme": meta,
        "raw": {
            "source_focus": source_focus,
            "pattern_survival": pattern_rows,
        },
    }
