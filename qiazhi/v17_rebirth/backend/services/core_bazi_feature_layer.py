from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple

from v17_rebirth.backend.logic.L0_physics_fields.ten_gods_engine import (
    BRANCH_ELEMENT,
    BRANCH_HIDDEN,
    ELEMENT_CYCLE,
    STEM_ELEMENT,
    STEM_YIN,
    _season_multiplier,
    ten_god_from_stems,
)
from v17_rebirth.backend.logic.L1_atomic_ops.relation_geometry_pairs import (
    eval_anhe_hits,
    eval_liu_chong_hits,
    eval_liu_hai_hits,
    eval_liu_po_hits,
    eval_liuhe_hits,
    sanxing_detect_geometry,
)
from v17_rebirth.backend.logic.L1_atomic_ops.relation_geometry_structured import (
    eval_banhe_hits,
    eval_gonghe_hits,
    eval_sanhe_hits,
    eval_sanhui_hits,
)
from v17_rebirth.backend.services.v18_1_predictive_engine import PredictiveServiceError
from v17_rebirth.paths import RUNTIME_DIR


CORE_BAZI_LAYER_VERSION = "core_bazi_layer_v1"
CORE_FEATURE_SCHEMA_VERSION = "core_feature_bundle.v1"

STEMS = set(STEM_ELEMENT)
BRANCHES = set(BRANCH_HIDDEN)
PILLAR_ORDER: Tuple[str, ...] = ("year", "month", "day", "hour")
RUNTIME_SCOPES: Tuple[str, ...] = ("luck", "flow")

ELEMENT_EN: Dict[str, str] = {
    "木": "wood",
    "火": "fire",
    "土": "earth",
    "金": "metal",
    "水": "water",
}

TEN_GOD_GROUP: Dict[str, str] = {
    "日主": "self",
    "比肩": "peer",
    "劫财": "peer",
    "食神": "output",
    "伤官": "output",
    "正财": "wealth",
    "偏财": "wealth",
    "正官": "officer",
    "七杀": "officer",
    "偏官": "officer",
    "正印": "resource",
    "偏印": "resource",
}

GROUP_LABEL_ZH: Dict[str, str] = {
    "self": "自我",
    "peer": "比劫",
    "output": "食伤",
    "wealth": "财星",
    "officer": "官杀",
    "resource": "印星",
}

SCOPE_WEIGHTS: Dict[str, float] = {
    "year": 0.75,
    "month": 1.20,
    "day": 1.00,
    "hour": 0.85,
    "luck": 0.65,
    "flow": 0.45,
}

LIUHE_TARGET_ELEMENT: Dict[frozenset[str], str] = {
    frozenset({"子", "丑"}): "earth",
    frozenset({"寅", "亥"}): "wood",
    frozenset({"卯", "戌"}): "fire",
    frozenset({"辰", "酉"}): "metal",
    frozenset({"巳", "申"}): "water",
    frozenset({"午", "未"}): "earth",
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


def _round(value: float, digits: int = 3) -> float:
    return round(float(value), digits)


def _element_en(element: str) -> str:
    return ELEMENT_EN.get(element, element)


def _polarity(stem: str) -> str:
    return "yin" if STEM_YIN.get(stem) is True else "yang"


def _weight_label(index: int, weight: float) -> str:
    if index == 0 or weight >= 0.58:
        return "primary"
    if index == 1 or weight >= 0.18:
        return "middle"
    return "residual"


def _normalize_pillar(value: Any) -> Dict[str, str]:
    if isinstance(value, Mapping):
        stem = _safe_str(value.get("stem") or value.get("heavenly_stem"))
        branch = _safe_str(value.get("branch") or value.get("earthly_branch"))
        text = _safe_str(value.get("pillar") or value.get("value") or value.get("name"))
        if (not stem or not branch) and text:
            parsed = _normalize_pillar(text)
            stem = stem or parsed.get("stem", "")
            branch = branch or parsed.get("branch", "")
        return {"stem": stem if stem in STEMS else "", "branch": branch if branch in BRANCHES else ""}
    if isinstance(value, (tuple, list)) and len(value) >= 2:
        stem = _safe_str(value[0])
        branch = _safe_str(value[1])
        return {"stem": stem if stem in STEMS else "", "branch": branch if branch in BRANCHES else ""}
    text = _safe_str(value)
    stem = next((char for char in text if char in STEMS), "")
    branch = next((char for char in text if char in BRANCHES), "")
    return {"stem": stem, "branch": branch}


def _candidate_chart(payload: Mapping[str, Any]) -> Mapping[str, Any]:
    chart = payload.get("chart_snapshot") if isinstance(payload.get("chart_snapshot"), Mapping) else payload
    if not isinstance(chart, Mapping):
        raise PredictiveServiceError("CORE_BAZI_CHART_INVALID", "chart_snapshot must be an object", status=400)
    nested = (
        chart.get("natal_chart")
        or chart.get("four_pillars")
        or chart.get("pillars")
        or chart.get("bazi")
        or chart.get("chart")
    )
    if isinstance(nested, Mapping):
        return {**chart, "_pillar_source": nested}
    return {**chart, "_pillar_source": chart}


def _extract_chart(payload: Mapping[str, Any]) -> Dict[str, Any]:
    chart = _candidate_chart(payload)
    source = chart.get("_pillar_source") if isinstance(chart.get("_pillar_source"), Mapping) else chart
    stems_map = chart.get("stems") if isinstance(chart.get("stems"), Mapping) else {}
    branches_map = chart.get("branches") if isinstance(chart.get("branches"), Mapping) else {}

    pillars: Dict[str, Dict[str, str]] = {}
    for scope in PILLAR_ORDER:
        raw = (
            source.get(scope)
            or source.get(f"{scope}_pillar")
            or chart.get(scope)
            or chart.get(f"{scope}_pillar")
            or {}
        )
        normalized = _normalize_pillar(raw)
        stem = normalized.get("stem") or _safe_str(stems_map.get(scope))
        branch = normalized.get("branch") or _safe_str(branches_map.get(scope))
        pillars[scope] = {
            "stem": stem if stem in STEMS else "",
            "branch": branch if branch in BRANCHES else "",
        }

    runtime: Dict[str, Dict[str, str]] = {}
    runtime_aliases = {
        "luck": ("luck", "luck_pillar", "decade", "decade_pillar", "dayun", "da_yun"),
        "flow": ("flow", "flow_pillar", "annual", "annual_pillar", "liunian", "liu_nian"),
    }
    for scope, aliases in runtime_aliases.items():
        raw = None
        for alias in aliases:
            if alias in chart:
                raw = chart.get(alias)
                break
            if alias in payload:
                raw = payload.get(alias)
                break
        normalized = _normalize_pillar(raw)
        runtime[scope] = normalized

    if not pillars["day"]["stem"]:
        raise PredictiveServiceError("CORE_BAZI_CHART_INVALID", "day stem is required", status=400)
    if not pillars["month"]["branch"]:
        raise PredictiveServiceError("CORE_BAZI_CHART_INVALID", "month branch is required", status=400)

    normalized_chart = {"pillars": pillars, "runtime": runtime}
    chart_id = _safe_str(chart.get("chart_id") or payload.get("chart_id"))
    if not chart_id:
        chart_id = f"chart_{_payload_hash(normalized_chart)[:16]}"
    normalized_chart["chart_id"] = chart_id
    return normalized_chart


def _pillar_string(pillar: Mapping[str, str]) -> str:
    return f"{_safe_str(pillar.get('stem'))}{_safe_str(pillar.get('branch'))}"


def _ten_god_entry(day_master: str, stem: str, *, is_day_master_position: bool = False) -> Dict[str, Any]:
    if is_day_master_position:
        ten_god = "日主"
    else:
        ten_god = ten_god_from_stems(day_master, stem) if stem else ""
    return {
        "stem": stem,
        "element": _element_en(STEM_ELEMENT.get(stem, "")),
        "element_label": STEM_ELEMENT.get(stem, ""),
        "polarity": _polarity(stem) if stem else "",
        "ten_god": ten_god,
        "ten_god_group": TEN_GOD_GROUP.get(ten_god, "unknown"),
    }


def _day_master_feature(chart: Mapping[str, Any]) -> Dict[str, Any]:
    day_stem = chart["pillars"]["day"]["stem"]
    return {
        "feature_id": "core.day_master",
        "feature_type": "identity",
        "input": ["natal_chart.day_stem"],
        "output": {
            "day_master": {
                "stem": day_stem,
                "element": _element_en(STEM_ELEMENT.get(day_stem, "")),
                "element_label": STEM_ELEMENT.get(day_stem, ""),
                "polarity": _polarity(day_stem),
            }
        },
        "certainty": 1.0,
        "boundary": "identity_only_no_strength_judgement",
    }


def _hidden_stems_feature(chart: Mapping[str, Any]) -> Dict[str, Any]:
    hidden_by_branch: Dict[str, List[Dict[str, Any]]] = {}
    hidden_by_position: Dict[str, List[Dict[str, Any]]] = {}
    for scope, pillar in chart["pillars"].items():
        branch = pillar.get("branch", "")
        rows: List[Dict[str, Any]] = []
        for idx, (stem, weight) in enumerate(BRANCH_HIDDEN.get(branch, [])):
            rows.append(
                {
                    "stem": stem,
                    "element": _element_en(STEM_ELEMENT.get(stem, "")),
                    "element_label": STEM_ELEMENT.get(stem, ""),
                    "polarity": _polarity(stem),
                    "weight": _weight_label(idx, float(weight)),
                    "weight_ratio": _round(float(weight)),
                }
            )
        if branch:
            hidden_by_branch[branch] = rows
            hidden_by_position[f"{scope}_branch"] = rows
    return {
        "feature_id": "core.hidden_stems",
        "feature_type": "branch_composition",
        "input": ["natal_chart.branches"],
        "output": {
            "hidden_stems": hidden_by_branch,
            "hidden_stems_by_position": hidden_by_position,
        },
        "certainty": 1.0,
        "boundary": "composition_only_no_auspicious_judgement",
    }


def _ten_god_mapping_feature(chart: Mapping[str, Any]) -> Dict[str, Any]:
    day_master = chart["pillars"]["day"]["stem"]
    visible: Dict[str, Dict[str, Any]] = {}
    hidden: Dict[str, List[Dict[str, Any]]] = {}
    by_position: Dict[str, Any] = {}

    for scope, pillar in chart["pillars"].items():
        stem = pillar.get("stem", "")
        position = f"{scope}_stem"
        entry = _ten_god_entry(day_master, stem, is_day_master_position=(scope == "day"))
        visible[position] = entry
        by_position[position] = entry

        branch = pillar.get("branch", "")
        hidden_entries: List[Dict[str, Any]] = []
        for idx, (hidden_stem, weight) in enumerate(BRANCH_HIDDEN.get(branch, [])):
            item = _ten_god_entry(day_master, hidden_stem)
            item["weight"] = _weight_label(idx, float(weight))
            item["weight_ratio"] = _round(float(weight))
            hidden_entries.append(item)
        hidden[f"{scope}_branch"] = hidden_entries
        by_position[f"{scope}_branch_hidden"] = hidden_entries

    return {
        "feature_id": "core.ten_god_mapping",
        "feature_type": "relation_mapping",
        "input": ["core.day_master", "natal_chart.stems", "core.hidden_stems"],
        "output": {
            "ten_gods": {
                "visible": visible,
                "hidden": hidden,
                "by_position": by_position,
            }
        },
        "certainty": 1.0,
        "boundary": "mapping_only_no_good_bad_judgement",
    }


def _root_quality(weight: float, exact_stem: bool, same_element: bool) -> str:
    if exact_stem and weight >= 0.58:
        return "strong"
    if same_element and weight >= 0.58:
        return "medium"
    if exact_stem or weight >= 0.18:
        return "weak"
    return "residual"


def _root_item(
    *,
    scope: str,
    branch: str,
    hidden_stem: str,
    hidden_weight: float,
    day_master: str,
) -> Dict[str, Any]:
    ten_god = ten_god_from_stems(day_master, hidden_stem)
    exact_stem = hidden_stem == day_master
    same_element = STEM_ELEMENT.get(hidden_stem) == STEM_ELEMENT.get(day_master)
    quality = _root_quality(hidden_weight, exact_stem, same_element)
    quality_factor = {"strong": 1.0, "medium": 0.72, "weak": 0.45, "residual": 0.24}.get(quality, 0.24)
    contribution = hidden_weight * SCOPE_WEIGHTS.get(scope, 0.75) * quality_factor
    return {
        "scope": scope,
        "branch": branch,
        "hidden_stem": hidden_stem,
        "hidden_weight": _round(hidden_weight),
        "quality": quality,
        "ten_god": ten_god,
        "ten_god_group": TEN_GOD_GROUP.get(ten_god, "unknown"),
        "contribution": _round(contribution),
    }


def _normalized_root_score(items: Iterable[Mapping[str, Any]]) -> float:
    raw = sum(float(item.get("contribution") or 0.0) for item in items)
    return _round(min(1.0, raw / 1.65))


def _root_strength_feature(chart: Mapping[str, Any]) -> Dict[str, Any]:
    day_master = chart["pillars"]["day"]["stem"]
    day_element = STEM_ELEMENT.get(day_master, "")
    root_items: List[Dict[str, Any]] = []

    for scope, pillar in {**chart["pillars"], **chart["runtime"]}.items():
        branch = pillar.get("branch", "")
        if not branch:
            continue
        for hidden_stem, weight in BRANCH_HIDDEN.get(branch, []):
            root_items.append(
                _root_item(
                    scope=scope,
                    branch=branch,
                    hidden_stem=hidden_stem,
                    hidden_weight=float(weight),
                    day_master=day_master,
                )
            )

    day_master_roots = [
        item
        for item in root_items
        if STEM_ELEMENT.get(_safe_str(item.get("hidden_stem"))) == day_element
    ]
    group_roots: Dict[str, List[Dict[str, Any]]] = {}
    label_roots: Dict[str, List[Dict[str, Any]]] = {}
    for item in root_items:
        group = _safe_str(item.get("ten_god_group"), "unknown")
        ten_god = _safe_str(item.get("ten_god"), "unknown")
        group_roots.setdefault(group, []).append(item)
        label_roots.setdefault(ten_god, []).append(item)

    ten_god_roots = {
        group: {
            "group_label": GROUP_LABEL_ZH.get(group, group),
            "root_count": len(items),
            "root_score": _normalized_root_score(items),
            "root_quality": [
                {
                    "scope": item["scope"],
                    "branch": item["branch"],
                    "hidden_stem": item["hidden_stem"],
                    "quality": item["quality"],
                    "contribution": item["contribution"],
                }
                for item in items
            ],
        }
        for group, items in sorted(group_roots.items())
        if group != "unknown"
    }
    ten_god_label_roots = {
        ten_god: {
            "root_count": len(items),
            "root_score": _normalized_root_score(items),
        }
        for ten_god, items in sorted(label_roots.items())
        if ten_god and ten_god != "unknown"
    }

    return {
        "feature_id": "core.root_strength",
        "feature_type": "strength_evidence",
        "input": ["core.day_master", "core.hidden_stems", "natal_chart.branches", "runtime_pillars_optional"],
        "output": {
            "rootedness": {
                "day_master": {
                    "root_count": len(day_master_roots),
                    "root_quality": [
                        {
                            "scope": item["scope"],
                            "branch": item["branch"],
                            "hidden_stem": item["hidden_stem"],
                            "quality": item["quality"],
                            "contribution": item["contribution"],
                        }
                        for item in day_master_roots
                    ],
                    "root_score": _normalized_root_score(day_master_roots),
                },
                "ten_god_roots": ten_god_roots,
                "ten_god_label_roots": ten_god_label_roots,
            }
        },
        "certainty": 0.86,
        "boundary": "root_evidence_only_no_body_strength_judgement",
    }


def _generated_element(element: str) -> str:
    if element not in ELEMENT_CYCLE:
        return ""
    return ELEMENT_CYCLE[(ELEMENT_CYCLE.index(element) + 1) % len(ELEMENT_CYCLE)]


def _wealth_element(element: str) -> str:
    if element not in ELEMENT_CYCLE:
        return ""
    return ELEMENT_CYCLE[(ELEMENT_CYCLE.index(element) + 2) % len(ELEMENT_CYCLE)]


def _officer_element(element: str) -> str:
    if element not in ELEMENT_CYCLE:
        return ""
    return ELEMENT_CYCLE[(ELEMENT_CYCLE.index(element) - 2) % len(ELEMENT_CYCLE)]


def _resource_element(element: str) -> str:
    if element not in ELEMENT_CYCLE:
        return ""
    return ELEMENT_CYCLE[(ELEMENT_CYCLE.index(element) - 1) % len(ELEMENT_CYCLE)]


def _season_support_label(multiplier: float) -> str:
    if multiplier >= 2.2:
        return "strong"
    if multiplier >= 1.55:
        return "medium"
    if multiplier > 1.0:
        return "weak"
    return "residual"


def _month_command_feature(chart: Mapping[str, Any]) -> Dict[str, Any]:
    day_master = chart["pillars"]["day"]["stem"]
    day_element = STEM_ELEMENT.get(day_master, "")
    month_branch = chart["pillars"]["month"]["branch"]
    month_hidden = BRANCH_HIDDEN.get(month_branch, [])
    dominant_hidden_stem = month_hidden[0][0] if month_hidden else ""
    dominant_ten_god = ten_god_from_stems(day_master, dominant_hidden_stem) if dominant_hidden_stem else ""
    dominant_group = TEN_GOD_GROUP.get(dominant_ten_god, "unknown")

    groups = {
        "day_master": day_element,
        "output": _generated_element(day_element),
        "wealth": _wealth_element(day_element),
        "officer": _officer_element(day_element),
        "resource": _resource_element(day_element),
    }
    season_support: Dict[str, Dict[str, Any]] = {}
    for group, element in groups.items():
        multiplier = _season_multiplier(element, month_branch) if element else 1.0
        season_support[group] = {
            "element": _element_en(element),
            "element_label": element,
            "support": _season_support_label(multiplier),
            "season_multiplier": _round(multiplier),
        }

    return {
        "feature_id": "core.month_command",
        "feature_type": "seasonal_power",
        "input": ["natal_chart.month_branch", "core.day_master", "core.hidden_stems"],
        "output": {
            "month_command": {
                "branch": month_branch,
                "season_element": _element_en(BRANCH_ELEMENT.get(month_branch, "")),
                "season_element_label": BRANCH_ELEMENT.get(month_branch, ""),
                "dominant_hidden_stem": dominant_hidden_stem,
                "dominant_hidden_ten_god": dominant_ten_god,
                "day_master_season_relation": dominant_group,
                "season_support": season_support,
            }
        },
        "certainty": 0.92,
        "boundary": "seasonal_evidence_only_no_pattern_judgement",
    }


def _combined_branch_map(chart: Mapping[str, Any]) -> Dict[str, str]:
    branches = {
        scope: pillar.get("branch", "")
        for scope, pillar in chart["pillars"].items()
        if pillar.get("branch")
    }
    for scope, pillar in chart["runtime"].items():
        if pillar.get("branch"):
            branches[scope] = pillar["branch"]
    return branches


def _scope_for_pillars(pillars: Iterable[str]) -> str:
    pillar_set = set(pillars)
    has_luck = "luck" in pillar_set
    has_flow = "flow" in pillar_set
    has_natal = any(p in PILLAR_ORDER for p in pillar_set)
    if has_luck and has_flow and has_natal:
        return "luck_flow_to_natal"
    if has_flow and has_luck:
        return "flow_to_luck"
    if has_flow and has_natal:
        return "flow_to_natal"
    if has_luck and has_natal:
        return "luck_to_natal"
    if has_flow:
        return "flow"
    if has_luck:
        return "luck"
    return "natal"


def _pair_relation(
    relation_type: str,
    hit: Mapping[str, Any],
    *,
    target_element: str = "",
    polarity: str = "neutral",
) -> Dict[str, Any]:
    branches = list(hit.get("pair") or hit.get("branches") or [])
    pillars = list(hit.get("pillars") or hit.get("edge") or [])
    return {
        "relation_type": relation_type,
        "branches": branches,
        "pillars": pillars,
        "target_element": target_element,
        "scope": _scope_for_pillars(pillars),
        "geometry_polarity": polarity,
    }


def _structured_relation(relation_type: str, hit: Mapping[str, Any], completeness: str) -> Dict[str, Any]:
    pillars = list(hit.get("pillars") or [])
    element = _safe_str(hit.get("element"))
    return {
        "relation_type": relation_type,
        "branches": list(hit.get("ordered_group") or hit.get("group") or hit.get("matched_branches") or []),
        "matched_branches": list(hit.get("matched_branches") or []),
        "pillars": pillars,
        "target_element": element,
        "completeness": completeness,
        "scope": _scope_for_pillars(pillars),
        "geometry_polarity": "neutral",
        "geometry_strength": hit.get("strength"),
    }


def _relation_hits_feature(chart: Mapping[str, Any]) -> Dict[str, Any]:
    branches = _combined_branch_map(chart)
    relations: List[Dict[str, Any]] = []

    for hit in eval_sanhe_hits(branches):
        relations.append(_structured_relation("three_harmony", hit, "full"))
    for hit in eval_sanhui_hits(branches):
        relations.append(_structured_relation("three_meeting", hit, "full"))
    for hit in eval_banhe_hits(branches):
        relations.append(_structured_relation("half_harmony", hit, "partial"))
    for hit in eval_gonghe_hits(branches):
        relations.append(_structured_relation("arch_harmony", hit, "partial"))

    for hit in eval_liuhe_hits(branches):
        target = LIUHE_TARGET_ELEMENT.get(frozenset(hit.get("pair") or []), "")
        relations.append(_pair_relation("six_harmony", hit, target_element=target, polarity="neutral"))
    for hit in eval_anhe_hits(branches):
        relations.append(_pair_relation("hidden_harmony", hit, polarity="neutral"))
    for hit in eval_liu_chong_hits(branches):
        relations.append(_pair_relation("clash", hit, polarity="disruptive"))
    for hit in eval_liu_hai_hits(branches):
        relations.append(_pair_relation("harm", hit, polarity="disruptive"))
    for hit in eval_liu_po_hits(branches):
        relations.append(_pair_relation("break", hit, polarity="disruptive"))
    for hit in sanxing_detect_geometry(branches):
        relations.append(_pair_relation("punishment", hit, polarity="disruptive"))

    return {
        "feature_id": "core.relation_hits",
        "feature_type": "structure_geometry",
        "input": ["natal_chart.branches", "luck_branch_optional", "flow_branch_optional"],
        "output": {
            "relations": relations,
            "relation_count": len(relations),
        },
        "certainty": 0.9,
        "boundary": "geometry_only_no_good_bad_judgement",
    }


def extract_core_bazi_features(payload: Mapping[str, Any]) -> Dict[str, Any]:
    chart = _extract_chart(payload)
    features = {
        "day_master": _day_master_feature(chart),
        "hidden_stems": _hidden_stems_feature(chart),
        "ten_god_mapping": _ten_god_mapping_feature(chart),
        "root_strength": _root_strength_feature(chart),
        "month_command": _month_command_feature(chart),
        "relation_hits": _relation_hits_feature(chart),
    }
    normalized_chart = {
        "chart_id": chart["chart_id"],
        "pillars": {scope: _pillar_string(chart["pillars"][scope]) for scope in PILLAR_ORDER},
        "runtime": {
            scope: _pillar_string(pillar)
            for scope, pillar in chart["runtime"].items()
            if pillar.get("stem") or pillar.get("branch")
        },
    }
    digest = _payload_hash({"chart": normalized_chart, "features": features, "version": CORE_BAZI_LAYER_VERSION})
    return {
        "bundle_id": f"core_feature_bundle_{digest[:16]}",
        "chart_id": chart["chart_id"],
        "features": features,
        "normalized_chart": normalized_chart,
        "version": CORE_BAZI_LAYER_VERSION,
        "schema_version": CORE_FEATURE_SCHEMA_VERSION,
        "created_at": _utcnow_iso(),
        "guardrails": {
            "fact_layer_only": True,
            "no_conclusion": True,
            "no_prediction_id": True,
            "no_ledger_write": True,
            "no_narrative": True,
        },
    }


class CoreBaziFeatureStore:
    def __init__(self, storage_file: Optional[Path] = None) -> None:
        self.storage_file = storage_file or (RUNTIME_DIR / "v18_1_core_bazi_feature_bundles.json")
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

    def extract_and_store(self, payload: Mapping[str, Any]) -> Dict[str, Any]:
        bundle = extract_core_bazi_features(payload)
        self._bundles[bundle["bundle_id"]] = bundle
        self._save()
        return bundle

    def get_bundle(self, bundle_id: str) -> Dict[str, Any]:
        key = _safe_str(bundle_id)
        bundle = self._bundles.get(key)
        if not bundle:
            self._load()
            bundle = self._bundles.get(key)
        if not bundle:
            raise PredictiveServiceError("CORE_FEATURE_BUNDLE_NOT_FOUND", "core feature bundle not found", status=404)
        return dict(bundle)


core_bazi_feature_service = CoreBaziFeatureStore()
