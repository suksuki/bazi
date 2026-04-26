from __future__ import annotations

import json
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Any, Dict, List, Mapping, Sequence

from v17_rebirth.backend.logic.L0_physics_fields.bazi_image_core import (
    normalize_bazi_image_meta,
    resolve_bazi_image,
)
from v17_rebirth.backend.logic.L3_modern_narrative.wealth_profile_core import (
    normalize_wealth_profile_meta,
    resolve_wealth_profile,
)
from v17_rebirth.backend.services.physics_layers import read_runtime_scores
from v17_rebirth.paths import V17_REBIRTH_ROOT


WEALTH_CODE_CONTRACT = "v17.topic.wealth_code.v1"
WEALTH_PATH_KNOWLEDGE_ID = "v17.knowledge.wealth_path_templates.v1"

FINAL_WEALTH_CODE_KEYS: List[str] = [
    "contract",
    "topic",
    "is_l3_topic_decoder",
    "knowledge_base",
    "score",
    "confidence",
    "risk",
    "primary_wealth_path",
    "secondary_paths",
    "wealth_source",
    "monetization_engine",
    "carrier",
    "wealth_vault",
    "leakage_points",
    "decade_path_trends",
    "flow_year_watchlist",
    "evidence_graph",
    "path_rankings",
    "mechanism_chains",
    "evidence",
    "llm_boundary",
    "learning_hooks",
    "guardrails",
]

WEALTH_CODE_KNOWLEDGE_PATH = V17_REBIRTH_ROOT / "backend" / "logic" / "knowledge" / "wealth_code_knowledge.v1.json"

STEMS = {"甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"}


@lru_cache(maxsize=1)
def load_wealth_code_knowledge() -> Dict[str, Any]:
    return json.loads(WEALTH_CODE_KNOWLEDGE_PATH.read_text(encoding="utf-8"))


def _knowledge_section(name: str) -> Any:
    section = load_wealth_code_knowledge().get(name)
    if isinstance(section, Mapping):
        return dict(section)
    if isinstance(section, list):
        return list(section)
    return section


def _knowledge_list(name: str) -> List[Any]:
    section = load_wealth_code_knowledge().get(name)
    return list(section) if isinstance(section, list) else []


def _knowledge_gods(name: str, fallback: Sequence[str] | None = None) -> tuple[str, ...]:
    if fallback is None:
        fallback = {
            "wealth_gods": ("正财", "偏财"),
            "output_gods": ("食神", "伤官"),
            "authority_gods": ("正官", "七杀"),
            "seal_gods": ("正印", "偏印"),
            "peer_gods": ("比肩", "劫财"),
        }.get(name, tuple())
    gods = load_wealth_code_knowledge().get("god_groups") or {}
    values = []
    if isinstance(gods, Mapping):
        values = gods.get(name) if isinstance(gods.get(name), list) else []
    source = values or list(fallback or [])
    return tuple(_clean_label(item) for item in source if _clean_label(item))


_PATH_KEYWORDS: Dict[str, tuple[str, ...]] = {
    str(path_id): tuple(str(item) for item in words)
    for path_id, words in _knowledge_section("path_keywords").items()
    if isinstance(words, list)
}

_CLAIM_SKIP_CLAIM_TYPES = {
    "macro_theme_observation",
    "topic_profile_observation",
    "topic_code_observation",
}

WEALTH_PATH_TEMPLATES: Dict[str, Dict[str, Any]] = {
    str(path_id): dict(template)
    for path_id, template in _knowledge_section("path_templates").items()
    if isinstance(template, Mapping)
}

_MECHANISM_CHAINS: Dict[str, Dict[str, Any]] = {
    str(chain_id): dict(template)
    for chain_id, template in _knowledge_section("mechanism_chains").items()
    if isinstance(template, Mapping)
}


def _path_size_tiers() -> List[Dict[str, Any]]:
    tiers = _knowledge_section("path_size_tiers")
    if isinstance(tiers, list):
        out = [row for row in tiers if isinstance(row, Mapping)]
        out.sort(key=lambda row: _safe_float(row.get("min_effective"), -1.0), reverse=True)
        return [dict(row) for row in out]
    return []


def _path_rank_limit() -> int:
    return max(3, int(_safe_float(_knowledge_section("path_rank_limit"), 6.0) or 6))


def _path_priority(path_id: str) -> int:
    section = _knowledge_section("path_priority")
    if isinstance(section, Mapping):
        raw = _safe_float(section.get(str(path_id)))
        if raw != 0.0 or str(path_id) in section:
            return int(raw)
    default_priority = {
        "direct_wealth": 30,
        "output_controls_pressure": 15,
        "output_to_wealth": 22,
        "wealth_officer_platform": 35,
        "wealth_seal_asset": 20,
        "resource_integration": 60,
        "wealth_vault": 70,
        "leakage_risk": 90,
    }
    return int(default_priority.get(str(path_id), 100))


def _path_size_label(score: float, risk: float) -> tuple[str, float]:
    effective = _clamp(_safe_float(score) * (1.0 - _safe_float(risk) * 0.22), 0.0, 1.0)
    for row in _path_size_tiers():
        if effective >= _safe_float(row.get("min_effective"), 0.0):
            return _clean_label(row.get("label") or "中", limit=8), effective
    return "小", effective


def _path_chain_support_counts(mechanism_chains: Sequence[Mapping[str, Any]] | None = None) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for chain in mechanism_chains or []:
        if not isinstance(chain, Mapping) or not bool(chain.get("met")):
            continue
        for row in chain.get("steps") if isinstance(chain.get("steps"), list) else []:
            if not isinstance(row, Mapping):
                continue
            path_id = _clean_label(row.get("path_id"))
            if not path_id or not row.get("present"):
                continue
            counts[path_id] = counts.get(path_id, 0) + 1
    return counts


def _build_path_rankings(
    *,
    primary: Mapping[str, Any],
    secondary: Sequence[Mapping[str, Any]],
    mechanism_chains: Sequence[Mapping[str, Any]] | None = None,
) -> List[Dict[str, Any]]:
    rows = [dict(primary)] + [dict(row) for row in secondary if isinstance(row, Mapping)]
    seen: set[str] = set()
    prepared: List[Dict[str, Any]] = []
    support_counts = _path_chain_support_counts(mechanism_chains)

    for row in rows:
        path_id = _clean_label(row.get("id"))
        if not path_id or path_id in seen:
            continue
        seen.add(path_id)
        if path_id == "leakage_risk":
            continue
        score = _safe_float(row.get("score"), 0.0)
        risk = _safe_float(row.get("risk"), 0.0)
        support_boost = min(0.08, 0.02 * support_counts.get(path_id, 0))
        combined = _clamp(score * (1.0 - risk * 0.18) + support_boost)
        size_label, size_signal = _path_size_label(combined, risk)
        prepared.append(
            {
                "id": path_id,
                "classic_label": _clean_label(row.get("classic_label"), limit=80),
                "plain_name": _clean_label(row.get("plain_name") or row.get("id") or "财富路径", limit=80),
                "plain_summary": _clean_label(row.get("plain_summary"), limit=120),
                "driver": _clean_label(row.get("driver"), limit=20),
                "score": round(score, 3),
                "confidence": round(_safe_float(row.get("confidence"), 0.0), 3),
                "risk": round(risk, 3),
                "evidence_count": len(_clean_str_list(row.get("evidence"), limit=30)),
                "size": size_label,
                "size_signal": round(size_signal, 3),
                "combined_score": round(combined, 3),
            }
        )

    prepared.sort(
        key=lambda row: (
            _safe_float(row.get("combined_score"), 0.0),
            _safe_float(row.get("score"), 0.0),
            _safe_float(row.get("confidence"), 0.0),
        ),
        reverse=True,
    )

    out: List[Dict[str, Any]] = []
    for index, row in enumerate(prepared[:_path_rank_limit()], start=1):
        row["rank"] = index
        out.append(row)
    return out


def _clean_label(value: Any, *, limit: int = 180) -> str:
    text = str(value or "").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def _clean_str_list(values: Sequence[Any] | None, *, limit: int = 8) -> List[str]:
    if not isinstance(values, Sequence) or isinstance(values, (str, bytes)):
        return []
    rows: List[str] = []
    seen: set[str] = set()
    for value in values:
        label = _clean_label(value)
        if not label or label in seen:
            continue
        seen.add(label)
        rows.append(label)
        if len(rows) >= limit:
            break
    return rows


def _safe_float(value: Any, fallback: float = 0.0) -> float:
    try:
        next_value = float(value)
    except (TypeError, ValueError):
        return fallback
    if next_value != next_value:
        return fallback
    return next_value


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, float(value)))


def _score_sum(scores: Mapping[str, Any], gods: Sequence[str]) -> float:
    return sum(max(0.0, _safe_float(scores.get(god), 0.0)) for god in gods)


def _share(scores: Mapping[str, Any], gods: Sequence[str], total: float) -> float:
    return _score_sum(scores, gods) / max(total, 1.0)


def _signal_label(value: float) -> str:
    for row in _knowledge_list("signal_labels"):
        if not isinstance(row, Mapping):
            continue
        if value >= _safe_float(row.get("min"), 0.0):
            return _clean_label(row.get("label")) or "未显"
    return "未显"


def _formula_value(formula: Mapping[str, Any], features: Mapping[str, float]) -> float:
    value = _safe_float(formula.get("base"), 0.0)
    terms = formula.get("terms") if isinstance(formula.get("terms"), list) else []
    for term in terms:
        if not isinstance(term, Sequence) or isinstance(term, (str, bytes)) or len(term) < 2:
            continue
        feature = str(term[0] or "").strip()
        value += _safe_float(features.get(feature), 0.0) * _safe_float(term[1], 0.0)
    return value


def _score_parts_from_config(rows: Any, features: Mapping[str, float]) -> List[str]:
    out: List[str] = []
    for row in rows if isinstance(rows, list) else []:
        if not isinstance(row, Mapping):
            continue
        feature = str(row.get("feature") or "").strip()
        raw = _safe_float(features.get(feature), 0.0)
        if "when_gt" in row and not raw > _safe_float(row.get("when_gt"), 0.0):
            continue
        if "when_eq" in row and abs(raw - _safe_float(row.get("when_eq"), 0.0)) > 1e-9:
            continue
        label = _clean_label(row.get("label"))
        if not label:
            continue
        if row.get("format") == "signal":
            out.append(f"{label}{_signal_label(raw)}")
        else:
            out.append(label)
    return out


def _fact_row_text(row: Any) -> str:
    if isinstance(row, str):
        return _clean_label(row, limit=300)
    if not isinstance(row, Mapping):
        return ""
    if row.get("fact"):
        return _clean_label(row.get("fact"), limit=300)
    for key in ("claim_text", "pattern_candidate", "pattern_name", "source_event", "plugin", "plugin_id"):
        value = row.get(key)
        if value:
            return _clean_label(value, limit=300)
    return ""


def _claim_nodes_from_tensor(physics_tensor: Mapping[str, Any], meta: Mapping[str, Any]) -> List[Dict[str, Any]]:
    nodes: List[Dict[str, Any]] = []

    def push_row(
        source_prefix: str,
        row: Mapping[str, Any],
        *,
        fallback_id: str,
        default_plugin_key: str,
    ) -> None:
        plugin_id = _clean_label(row.get(default_plugin_key) or row.get("plugin") or row.get("plugin_id"))
        if not plugin_id:
            return
        if plugin_id.startswith(("modern.macro.", "modern.topic.")):
            return

        row_meta = row.get("meta") if isinstance(row.get("meta"), Mapping) else {}
        claim_type = _clean_label(row_meta.get("claim_type") or row.get("claim_type"))
        if claim_type in _CLAIM_SKIP_CLAIM_TYPES:
            return

        if isinstance(row_meta.get("intent_vector"), Mapping):
            intent_vector = dict(row_meta.get("intent_vector"))
        else:
            intent_vector = {}
        if not intent_vector and row.get("target_god"):
            intent_vector = {_clean_label(row.get("target_god")): 1.0}

        target_god = _clean_label(row_meta.get("target_god") or row.get("target_god"))
        target_gods = []
        if target_god:
            target_gods.append(target_god)
        target_gods.extend(_clean_str_list(intent_vector.keys(), limit=8))
        target_gods = [god for god in target_gods if god]

        text = _fact_row_text(row)
        if not text:
            return

        confidence = _safe_float(row_meta.get("confidence") or row.get("confidence"), 0.0)
        if not confidence:
            confidence = _safe_float(row_meta.get("pattern_confidence"), 0.0)
        if not confidence:
            confidence = _safe_float(row.get("match_ratio") or row.get("weight") or row.get("priority"), 0.5)

        source_id = _clean_label(row.get("claim_id") or row.get("id") or fallback_id)
        if not source_id:
            source_id = f"{source_prefix}:{len(nodes) + 1}"

        nodes.append(
            {
                "id": source_id,
                "plugin_id": plugin_id,
                "claim_type": claim_type,
                "text": text,
                "target_gods": [x for x in target_gods if x],
                "intent_vector": intent_vector,
                "entity_scope": _clean_label(row_meta.get("entity_scope") or row.get("entity_scope")),
                "source_event": _clean_label(row_meta.get("source_event") or row.get("source_event")),
                "confidence": _clamp(confidence),
                "match_ratio": _safe_float(row.get("match_ratio") or row_meta.get("match_ratio"), confidence),
                "plugin_confidence": _safe_float(row_meta.get("pattern_confidence"), confidence),
                "source": source_prefix,
                "raw_signature": _clean_label(row_meta.get("source_event") or row.get("plugin") or plugin_id, limit=100),
            }
        )

    for index, row in enumerate(physics_tensor.get("facts") or []):
        if not isinstance(row, Mapping):
            continue
        push_row("fact", row, fallback_id=f"fact:{index}", default_plugin_key="plugin")

    for index, row in enumerate(meta.get("plugin_claims") or []):
        if not isinstance(row, Mapping):
            continue
        push_row("plugin_claim", row, fallback_id=f"plugin_claim:{index}", default_plugin_key="plugin_id")

    bazi_image = normalize_bazi_image_meta(meta.get("bazi_image"))
    symbolic_facts = _symbolic_facts(bazi_image)
    for index, row in enumerate(symbolic_facts):
        if not isinstance(row, Mapping):
            continue
        text = _fact_row_text(row)
        if not text:
            continue
        confidence = _safe_float(row.get("confidence"), 0.0)
        topic_hint = _clean_label(row.get("topic_hint"))
        god = _symbolic_fact_god(row)
        stem = _symbolic_fact_stem(row)
        target_gods = [god] if god else []
        if stem:
            target_gods.append(stem)
        source_id = f"bazi_symbolic:{index}"
        nodes.append(
            {
                "id": source_id,
                "plugin_id": "v17.symbolic.bazi_image.v1",
                "claim_type": "symbolic_image_observation",
                "text": text,
                "target_gods": target_gods,
                "intent_vector": {item: 1.0 for item in target_gods if item},
                "entity_scope": topic_hint,
                "source_event": _clean_label(row.get("id") or topic_hint or "bazi_symbolic"),
                "confidence": _clamp(confidence),
                "match_ratio": confidence,
                "plugin_confidence": confidence,
                "source": "symbolic_fact",
                "raw_signature": source_id,
            }
        )

    return nodes


def _knowledge_list_by_path(name: str) -> Dict[str, List[Mapping[str, Any]]]:
    section = _knowledge_section(name)
    output: Dict[str, List[Mapping[str, Any]]] = {}
    if not isinstance(section, Mapping):
        return output
    for path_id, rows in section.items():
        if isinstance(rows, list):
            output[str(path_id)] = [row for row in rows if isinstance(row, Mapping)]
    return output


def _claim_node_matches(node: Mapping[str, Any], rule: Mapping[str, Any]) -> bool:
    target_gods = set(_clean_str_list(node.get("target_gods"), limit=12))
    node_plugins = _clean_label(node.get("plugin_id"))
    node_claim_type = _clean_label(node.get("claim_type"))
    node_scope = _clean_label(node.get("entity_scope"))
    node_text = _clean_label(node.get("text")).lower()
    intent = node.get("intent_vector")
    intent_gods = set(_clean_str_list((intent or {}).keys(), limit=12))

    req_claim_types = _clean_str_list(rule.get("claim_types"), limit=12)
    if req_claim_types and node_claim_type and node_claim_type not in req_claim_types:
        return False

    req_entity_scopes = _clean_str_list(rule.get("entity_scopes"), limit=12)
    if req_entity_scopes and node_scope and node_scope not in req_entity_scopes:
        return False

    req_gods = set(_clean_str_list(rule.get("target_gods"), limit=12))
    if req_gods and not (target_gods & req_gods or intent_gods & req_gods):
        return False

    req_plugin_prefixes = _clean_str_list(rule.get("plugin_prefixes"), limit=12)
    if req_plugin_prefixes and not any(node_plugins.startswith(prefix) for prefix in req_plugin_prefixes):
        return False

    req_plugins = _clean_str_list(rule.get("plugins"), limit=12)
    if req_plugins and node_plugins not in req_plugins:
        return False

    req_keywords = _clean_str_list(rule.get("keywords"), limit=12)
    if req_keywords and not any(keyword in node_text for keyword in req_keywords):
        return False

    return True


def _path_claim_hits(path_id: str, claim_nodes: Sequence[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    rules = _knowledge_list_by_path("path_claim_rules").get(path_id, [])
    if not rules:
        return []

    hits: List[Dict[str, Any]] = []
    for node in claim_nodes:
        node_text = _clean_label(node.get("text"), limit=140)
        if not node_text:
            continue
        node_strength = _safe_float(node.get("confidence"), 0.0)
        plugin_id = _clean_label(node.get("plugin_id"))
        for index, rule in enumerate(rules):
            if not _claim_node_matches(node, rule):
                continue
            weight = max(0.0, _safe_float(rule.get("weight"), 1.0))
            bonus = round(weight * node_strength, 4)
            if bonus <= 0:
                continue
            hit_id = _clean_label(rule.get("id")) or f"r{index + 1}"
            rule_label = _clean_label(rule.get("label") or hit_id, limit=80)
            evidence = f"{plugin_id}#{_clean_label(rule.get('label') or hit_id)}"
            hits.append(
                {
                    "claim_id": _clean_label(node.get("id")),
                    "path_id": str(path_id),
                    "rule_id": hit_id,
                    "rule_label": rule_label,
                    "evidence": evidence,
                    "text": node_text,
                    "weight": bonus,
                    "plugin_id": plugin_id,
                    "claim_type": _clean_label(node.get("claim_type")),
                    "rule_text": rule_label,
                }
            )
    return hits


def _facts_text(physics_tensor: Mapping[str, Any], meta: Mapping[str, Any]) -> str:
    fragments: List[str] = []
    for row in physics_tensor.get("facts") or []:
        if not isinstance(row, Mapping):
            fragments.append(_clean_label(row, limit=220))
            continue
        plugin_id = _clean_label(row.get("plugin") or row.get("plugin_id"))
        fact_meta = row.get("meta") if isinstance(row.get("meta"), Mapping) else {}
        claim_type = _clean_label(fact_meta.get("claim_type"))
        if plugin_id.startswith(("modern.macro.", "modern.topic.")) or claim_type in {
            "macro_theme_observation",
            "topic_profile_observation",
            "topic_code_observation",
        }:
            continue
        fragments.append(_clean_label(row.get("fact"), limit=220))
    for row in meta.get("plugin_claims") or []:
        if not isinstance(row, Mapping):
            continue
        plugin_id = _clean_label(row.get("plugin_id") or row.get("plugin"))
        claim_type = _clean_label(row.get("claim_type"))
        if plugin_id.startswith(("modern.macro.", "modern.topic.")) or claim_type in {
            "macro_theme_observation",
            "topic_profile_observation",
            "topic_code_observation",
        }:
            continue
        fragments.extend(
            _clean_label(row.get(key), limit=120)
            for key in ("claim_text", "pattern_candidate", "pattern_name", "source_event", "plugin_id")
        )
    return " ".join(fragment for fragment in fragments if fragment)


def _keyword_hits(text: str, path_id: str) -> List[str]:
    return [word for word in _PATH_KEYWORDS.get(path_id, ()) if word and word in text][:6]


def _profile_from_tensor(pt: Mapping[str, Any], meta: Mapping[str, Any]) -> Dict[str, Any]:
    profile = normalize_wealth_profile_meta(meta.get("wealth_profile"))
    if profile:
        return profile
    return normalize_wealth_profile_meta(resolve_wealth_profile(dict(pt)).get("wealth_profile"))


def _bazi_image_from_tensor(pt: Mapping[str, Any], meta: Mapping[str, Any]) -> Dict[str, Any]:
    image = normalize_bazi_image_meta(meta.get("bazi_image"))
    if image:
        return image
    return normalize_bazi_image_meta(resolve_bazi_image(dict(pt)).get("bazi_image"))


def _top_channel_id(profile: Mapping[str, Any]) -> str:
    channels = profile.get("primary_channels") if isinstance(profile.get("primary_channels"), list) else []
    if not channels or not isinstance(channels[0], Mapping):
        return ""
    return _clean_label(channels[0].get("id"))


def _channel_score(profile: Mapping[str, Any], channel_id: str) -> float:
    channels = profile.get("primary_channels") if isinstance(profile.get("primary_channels"), list) else []
    for row in channels:
        if isinstance(row, Mapping) and row.get("id") == channel_id:
            return _safe_float(row.get("score"), 0.0)
    return 0.0


def _symbolic_facts(bazi_image: Mapping[str, Any], *, fact_type: str | None = None, topic_hint: str | None = None) -> List[Dict[str, Any]]:
    rows = bazi_image.get("symbolic_facts") if isinstance(bazi_image.get("symbolic_facts"), list) else []
    out: List[Dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        if fact_type and _clean_label(row.get("fact_type")) != fact_type:
            continue
        if topic_hint and _clean_label(row.get("topic_hint")) != topic_hint:
            continue
        out.append(dict(row))
    return out


def _symbolic_fact_god(row: Mapping[str, Any]) -> str:
    terms = _clean_str_list(row.get("classic_terms"), limit=4)
    return _clean_label(terms[0]) if terms else ""


def _symbolic_fact_stem(row: Mapping[str, Any]) -> str:
    terms = _clean_str_list(row.get("classic_terms"), limit=4)
    if len(terms) >= 2:
        stem_term = _clean_label(terms[1])
        if stem_term and stem_term[0] in STEMS:
            return stem_term[0]
    fact_id = _clean_label(row.get("id"))
    parts = fact_id.split(".")
    if len(parts) >= 4 and _clean_label(parts[3]).startswith(tuple(STEMS)):
        stem = _clean_label(parts[3])
        return stem[0] if stem and stem[0] in STEMS else ""
    return ""


def _load_symbolic_booster_rules() -> Dict[str, List[Dict[str, Any]]]:
    section = _knowledge_section("symbolic_path_boosters")
    output: Dict[str, List[Dict[str, Any]]] = {}
    if not isinstance(section, Mapping):
        return output
    for path_id, rows in section.items():
        output[str(path_id)] = [row for row in rows if isinstance(row, Mapping)] if isinstance(rows, list) else []
    return output


SYMBOLIC_BOOSTER_RULES: Dict[str, List[Dict[str, Any]]] = _load_symbolic_booster_rules()


def _symbolic_booster_scores(
    *, path_id: str, bazi_image: Mapping[str, Any]
) -> tuple[Dict[str, float], List[Dict[str, str]]]:
    rules = SYMBOLIC_BOOSTER_RULES.get(path_id, [])
    if not rules:
        return {}, []
    rows = _symbolic_facts(bazi_image)
    features: Dict[str, float] = {}
    support: List[Dict[str, str]] = []

    for index, rule in enumerate(rules):
        if not isinstance(rule, Mapping):
            continue
        feature = _clean_label(rule.get("feature"))
        if not feature:
            feature = f"symbolic_{path_id}_{index + 1}"
        min_count = max(0, int(_safe_float(rule.get("min_count"), 0.0) or 0))
        max_count = int(_safe_float(rule.get("max_count"), 99.0) or 99)
        if max_count <= 0:
            max_count = 99

        target_facts = _clean_str_list(rule.get("fact_types"), limit=8)
        target_gods = _clean_str_list(rule.get("ten_gods"), limit=8)
        target_stems = _clean_str_list(rule.get("stems"), limit=8)
        target_topics = _clean_str_list(rule.get("topic_hints"), limit=8)

        matched_rows: List[Mapping[str, Any]] = []
        for row in rows:
            if not isinstance(row, Mapping):
                continue
            if target_facts and row.get("fact_type") not in target_facts:
                continue
            god = _symbolic_fact_god(row)
            stem = _symbolic_fact_stem(row)
            topic = _clean_label(row.get("topic_hint"))
            if target_gods and god and god not in target_gods:
                continue
            if target_stems and stem and stem not in target_stems:
                continue
            if target_topics and topic and topic not in target_topics:
                continue
            if target_topics and not topic:
                continue
            matched_rows.append(row)

        if len(matched_rows) < max(1, min_count):
            continue

        count = min(len(matched_rows), max_count)
        base_weight = _safe_float(rule.get("weight"), 0.0)
        if rule.get("weight_scale_with_count"):
            raw = base_weight * count
        else:
            raw = base_weight
        cap = _safe_float(rule.get("cap"), 0.0)
        value = _clamp(raw if cap <= 0 else min(raw, cap), 0.0, 1.0)
        if value <= 0:
            continue
        feature_label = _clean_label(rule.get("label"))
        features[feature] = round(_clamp(_safe_float(features.get(feature), 0.0) + value), 3)
        if feature_label:
            support.append(
                {
                    "rule_id": _clean_label(rule.get("id")) or f"sym-{path_id}-{index + 1}",
                    "path_id": path_id,
                    "rule_label": feature_label,
                    "weight": f"{round(value, 3)}",
                    "match_count": str(count),
                }
            )
    return features, support


def _wealth_material_rows(bazi_image: Mapping[str, Any]) -> List[Dict[str, Any]]:
    return [
        row
        for row in _symbolic_facts(bazi_image, topic_hint="wealth")
        if _clean_label(row.get("fact_type")) in {"wealth_material", "hidden_wealth_material"}
    ]


def _symbolic_fact_rows(bazi_image: Mapping[str, Any], *, fact_type: str) -> List[Dict[str, Any]]:
    return [row for row in _symbolic_facts(bazi_image) if _clean_label(row.get("fact_type")) == fact_type]


def _hidden_ten_god_count(bazi_image: Mapping[str, Any], gods: Sequence[str]) -> int:
    branches = bazi_image.get("branches") if isinstance(bazi_image.get("branches"), list) else []
    count = 0
    for branch in branches:
        if not isinstance(branch, Mapping):
            continue
        for hidden in branch.get("hidden_stems") if isinstance(branch.get("hidden_stems"), list) else []:
            if isinstance(hidden, Mapping) and _clean_label(hidden.get("ten_god")) in gods:
                count += 1
    return count


def _has_output_wealth_nesting(bazi_image: Mapping[str, Any]) -> bool:
    output_branches = {"巳", "午", "未", "戌"}
    wealth_gods = set(_knowledge_gods("wealth_gods"))
    output_gods = set(_knowledge_gods("output_gods"))
    branches = bazi_image.get("branches") if isinstance(bazi_image.get("branches"), list) else []
    for branch in branches:
        if not isinstance(branch, Mapping) or _clean_label(branch.get("branch")) not in output_branches:
            continue
        hidden = branch.get("hidden_stems") if isinstance(branch.get("hidden_stems"), list) else []
        has_wealth = any(isinstance(row, Mapping) and _clean_label(row.get("ten_god")) in wealth_gods for row in hidden)
        has_output = any(isinstance(row, Mapping) and _clean_label(row.get("ten_god")) in output_gods for row in hidden)
        if has_wealth and has_output:
            return True
    return False


def _wealth_source(
    bazi_image: Mapping[str, Any],
    profile: Mapping[str, Any],
    *,
    primary_path: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    path = primary_path if isinstance(primary_path, Mapping) else {}
    driver = _clean_label(path.get("driver"))
    output_facts = _symbolic_fact_rows(bazi_image, fact_type="output_material")
    output_wealth_nested = _has_output_wealth_nesting(bazi_image)
    stems = bazi_image.get("stems") if isinstance(bazi_image.get("stems"), list) else []
    wealth_gods = _knowledge_gods("wealth_gods")
    output_gods = _knowledge_gods("output_gods")
    for row in stems:
        if not isinstance(row, Mapping):
            continue
        god = _clean_label(row.get("ten_god"))
        if god not in wealth_gods:
            continue
        projection = row.get("domain_projection") if isinstance(row.get("domain_projection"), Mapping) else {}
        wealth_projection = _clean_str_list(projection.get("wealth"), limit=4)
        return {
            "material": f"{row.get('stem')}{row.get('element')}",
            "ten_god": god,
            "plain_source": "、".join(wealth_projection) or "明确财富资源",
            "visibility": _clean_label(row.get("visibility")) or "exposed",
            "location": _clean_label(row.get("pillar")),
            "evidence": list(row.get("evidence") or []),
        }
    material_rows = _wealth_material_rows(bazi_image)
    if material_rows:
        row = material_rows[0]
        terms = row.get("classic_terms") if isinstance(row.get("classic_terms"), list) else []
        plain_source = _clean_label(row.get("plain_meaning"), limit=120)
        if driver in {"output", "output_authority"} and (output_facts or output_wealth_nested):
            rewrite = _knowledge_section("source_rewrites").get("output_hidden_wealth")
            plain_source = _clean_label(rewrite, limit=160) or plain_source
        return {
            "material": _clean_label(terms[1] if len(terms) > 1 else ""),
            "ten_god": _clean_label(terms[0] if terms else ""),
            "plain_source": plain_source,
            "visibility": "hidden",
            "location": "hidden_stem",
            "evidence": list(row.get("evidence") or []),
        }
    top_channel = _top_channel_id(profile)
    channel_sources = _knowledge_section("profile_channel_sources")
    return {
        "material": "",
        "ten_god": "",
        "plain_source": _clean_label(channel_sources.get(top_channel)) or "财富来源需要继续观察",
        "visibility": _clean_label(profile.get("visibility")) or "unclear",
        "location": "wealth_profile",
        "evidence": _clean_str_list(profile.get("evidence"), limit=3),
    }


def _wealth_vault(bazi_image: Mapping[str, Any]) -> Dict[str, Any]:
    branches = bazi_image.get("branches") if isinstance(bazi_image.get("branches"), list) else []
    vaults: List[Dict[str, Any]] = []
    for row in branches:
        if not isinstance(row, Mapping):
            continue
        storage = row.get("storage_context") if isinstance(row.get("storage_context"), Mapping) else {}
        if not storage.get("has_vault_signal"):
            continue
        hidden = row.get("hidden_stems") if isinstance(row.get("hidden_stems"), list) else []
        hidden_wealth = [
            item
            for item in hidden
                if isinstance(item, Mapping) and _clean_label(item.get("ten_god")) in _knowledge_gods("wealth_gods")
            ]
        movement = row.get("movement_context") if isinstance(row.get("movement_context"), Mapping) else {}
        relation_tags = _clean_str_list(movement.get("relation_tags"), limit=4)
        state = "activated" if relation_tags else "static"
        activation_type = "cashflow_volatility" if relation_tags else "asset_storage"
        if hidden_wealth and relation_tags:
            activation_type = "asset_conversion"
        vaults.append(
            {
                "branch": _clean_label(row.get("branch")),
                "location": _clean_label(row.get("pillar")),
                "vault_element": _clean_label(storage.get("vault_element")),
                "plain_material": _clean_label(storage.get("plain_material")),
                "hidden_wealth": [
                    {
                        "stem": _clean_label(item.get("stem")),
                        "ten_god": _clean_label(item.get("ten_god")),
                    }
                    for item in hidden_wealth
                ],
                "state": state,
                "activation_type": activation_type,
                "relation_tags": relation_tags,
                "evidence": list(row.get("evidence") or []),
            }
        )
    if not vaults:
        return {
            "has_vault_signal": False,
            "vault_state": "none",
            "activation_type": "none",
            "plain_summary": "未见明确财库象，先按收入路径和现金流承接判断。",
            "items": [],
        }
    primary = vaults[0]
    summary = (
        f"{primary['branch']}带库象，偏向{primary['plain_material']}。"
        "开库不直接等于进财，需要结合岁运触发、回款、投入和现金流状态看。"
    )
    return {
        "has_vault_signal": True,
        "vault_state": primary["state"],
        "activation_type": primary["activation_type"],
        "plain_summary": summary,
        "items": vaults[:4],
    }


def _path_evidence(
    *,
    path_id: str,
    claim_hits: Sequence[Mapping[str, Any]],
    score_parts: Sequence[str],
    bazi_facts: Sequence[Mapping[str, Any]],
    profile: Mapping[str, Any],
    symbolic_support: Sequence[Mapping[str, Any]],
) -> List[str]:
    evidence = list(score_parts)
    evidence.extend(f"结构化路径线索：{_clean_label(hit.get('evidence'))}" for hit in claim_hits[:3] if _clean_label(hit.get('evidence')))
    evidence.extend(_clean_label(hit.get('text'), limit=120) for hit in claim_hits[:3] if _clean_label(hit.get('text')))
    evidence.extend(_clean_label(row.get("plain_meaning"), limit=120) for row in bazi_facts[:3])
    for row in symbolic_support:
        rule_label = _clean_label(row.get("rule_label"))
        rule_weight = _safe_float(row.get("weight"), 0.0)
        if rule_label and rule_weight > 0:
            evidence.append(f"象义支撑：{rule_label} ({int(_safe_float(row.get('match_count'), 0.0))}次)")
    if path_id == "output_to_wealth" and _channel_score(profile, "output_to_wealth") > 0:
        evidence.append("财富画像主通道支持技能/产品/表达变现")
    if path_id == "wealth_officer_platform" and _channel_score(profile, "authority_income") > 0:
        evidence.append("财富画像支持平台、职位或合同收入")
    if path_id == "wealth_seal_asset" and _channel_score(profile, "knowledge_asset") > 0:
        evidence.append("财富画像支持专业资产或知识信用变现")
    return _clean_str_list(evidence, limit=8)


def _path_row(
    *,
    path_id: str,
    score: float,
    risk: float,
    support_weight: float,
    claim_hits: Sequence[Mapping[str, Any]],
    score_parts: Sequence[str],
    bazi_facts: Sequence[Mapping[str, Any]],
    profile: Mapping[str, Any],
    symbolic_support: Sequence[Mapping[str, Any]],
) -> Dict[str, Any]:
    template = WEALTH_PATH_TEMPLATES[path_id]
    claim_links: List[Dict[str, Any]] = []
    seen_link_ids: set[str] = set()
    for row in claim_hits[:5]:
        claim_id = _clean_label(row.get("claim_id"))
        rule_id = _clean_label(row.get("rule_id"))
        if not claim_id or not rule_id:
            continue
        link_id = f"{claim_id}::{rule_id}"
        if link_id in seen_link_ids:
            continue
        seen_link_ids.add(link_id)
        claim_links.append(
            {
                "claim_id": claim_id,
                "rule_id": rule_id,
                "claim_type": _clean_label(row.get("claim_type")),
                "claim_text": _clean_label(row.get("text"), limit=80),
                "plugin_id": _clean_label(row.get("plugin_id")),
                "evidence": _clean_label(row.get("evidence"), limit=120),
                "weight": round(_safe_float(row.get("weight"), 0.0), 4),
                "rule_label": _clean_label(row.get("rule_label"), limit=80),
            }
        )
    evidence = _path_evidence(
        path_id=path_id,
        claim_hits=claim_hits,
        score_parts=score_parts,
        bazi_facts=bazi_facts,
        profile=profile,
        symbolic_support=symbolic_support,
    )
    confidence = _clamp(0.36 + len(evidence) * 0.055 + score * 0.16 - risk * 0.04, 0.28, 0.9)
    claim_signal = sum(_safe_float(hit.get("weight"), 0.0) for hit in claim_hits)
    return {
        "id": path_id,
        "classic_label": template["classic_label"],
        "plain_name": template["plain_name"],
        "plain_summary": template["plain_summary"],
        "score": round(_clamp(score), 3),
        "support_weight": round(_clamp(support_weight), 3),
        "confidence": round(confidence, 3),
        "risk": round(_clamp(risk), 3),
        "claim_signal": round(_clamp(claim_signal), 3),
        "driver": template["driver"],
        "carrier_type": template["carrier_type"],
        "risk_hint": template["risk_hint"],
        "evidence": evidence,
        "claim_hit_count": len(claim_hits),
        "symbolic_support": _clean_str_list([row.get("rule_label") for row in symbolic_support], limit=6),
        "claim_supports": claim_links,
    }


def _merge_claim_supports(
    first: Sequence[Mapping[str, Any]],
    second: Sequence[Mapping[str, Any]],
) -> List[Dict[str, Any]]:
    output: List[Dict[str, Any]] = []
    seen: set[str] = set()
    for row in list(first) + list(second):
        if not isinstance(row, Mapping):
            continue
        claim_id = _clean_label(row.get("claim_id"))
        rule_id = _clean_label(row.get("rule_id"))
        key = f"{claim_id}::{rule_id}"
        if not claim_id:
            continue
        if key in seen:
            continue
        seen.add(key)
        output.append(
            {
                "claim_id": claim_id,
                "rule_id": rule_id,
                "claim_type": _clean_label(row.get("claim_type")),
                "claim_text": _clean_label(row.get("claim_text"), limit=80),
                "plugin_id": _clean_label(row.get("plugin_id")),
                "evidence": _clean_label(row.get("evidence"), limit=120),
                "weight": round(_safe_float(row.get("weight"), 0.0), 4),
            }
        )
    return output


def _build_mechanism_chain(
    *,
    chain_id: str,
    chain_def: Mapping[str, Any],
    available_paths: Mapping[str, Mapping[str, Any]],
) -> Dict[str, Any]:
    required_ids = _clean_str_list(chain_def.get("required_path_ids"), limit=8)
    min_steps = int(_safe_float(chain_def.get("min_steps"), 0.0) or len(required_ids))
    if min_steps <= 0:
        min_steps = len(required_ids)
    step_roles = chain_def.get("step_roles") if isinstance(chain_def.get("step_roles"), Mapping) else {}
    step_rows: List[Dict[str, Any]] = []
    matched = 0
    present_scores: List[float] = []
    path_risks: List[float] = []
    for path_id in required_ids:
        row = available_paths.get(path_id)
        present = bool(row)
        if present:
            matched += 1
            present_scores.append(_safe_float(row.get("score"), 0.0))
            path_risks.append(_safe_float(row.get("risk"), 0.0))
        row_plain = _clean_label(row.get("plain_name"), limit=80) if row else ""
        step_rows.append(
            {
                "path_id": path_id,
                "plain_name": _clean_label(step_roles.get(path_id), limit=80) or row_plain or path_id,
                "present": present,
                "path_score": round(_safe_float(row.get("score"), 0.0), 3) if row else 0.0,
                "path_risk": round(_safe_float(row.get("risk"), 0.0), 3) if row else 0.0,
                "path_confidence": round(_safe_float(row.get("confidence"), 0.0), 3) if row else 0.0,
            }
        )
    completeness = matched / max(1, len(required_ids))
    if matched < min_steps:
        # 不足够路径位点时允许保留观察链，但不应作为主链
        base_weight = _safe_float(chain_def.get("default_weight"), 0.0)
        completeness_score = _safe_float(base_weight) * completeness * 0.65
        return {
            "id": chain_id,
            "plain_name": _clean_label(chain_def.get("plain_name") or chain_def.get("chain_name") or chain_id),
            "classic_label": _clean_label(chain_def.get("classic_label")),
            "plain_summary": _clean_label(chain_def.get("plain_summary")),
            "chain_name": _clean_label(chain_def.get("chain_name")),
            "required_path_ids": required_ids,
            "score": round(_clamp(completeness_score), 3),
            "confidence": round(
                _clamp(base_weight * (matched / max(1, len(required_ids))) + 0.05, 0.0, 0.98),
                3,
            ),
            "risk": round(_clamp(max(path_risks) if path_risks else 0.34), 3),
            "completeness": round(completeness, 3),
            "met": False,
            "boost": round(_safe_float(chain_def.get("boost"), 0.0), 3),
            "forbidden_terms": _clean_str_list(chain_def.get("forbidden_terms"), limit=8),
            "steps": step_rows,
        }

    chain_weight = _safe_float(chain_def.get("default_weight"), 0.8)
    score_baseline = sum(present_scores) / max(1, len(required_ids))
    chain_score = _clamp(score_baseline * 0.72 + chain_weight * 0.18 + completeness * 0.1 + _safe_float(chain_def.get("boost"), 0.0))
    chain_confidence = _clamp(score_baseline + 0.18, 0.2, 0.95)
    return {
        "id": chain_id,
        "plain_name": _clean_label(chain_def.get("plain_name") or chain_def.get("chain_name") or chain_id),
        "classic_label": _clean_label(chain_def.get("classic_label")),
        "plain_summary": _clean_label(chain_def.get("plain_summary")),
        "chain_name": _clean_label(chain_def.get("chain_name")),
        "required_path_ids": required_ids,
        "score": round(chain_score, 3),
        "confidence": round(chain_confidence, 3),
        "risk": round(_clamp(max(path_risks) if path_risks else 0.0), 3),
        "completeness": round(completeness, 3),
        "met": True,
        "boost": round(_safe_float(chain_def.get("boost"), 0.0), 3),
        "forbidden_terms": _clean_str_list(chain_def.get("forbidden_terms"), limit=8),
        "steps": step_rows,
    }


def _infer_mechanism_chains(
    path_rows: Sequence[Mapping[str, Any]],
    *,
    limit: int = 3,
) -> List[Dict[str, Any]]:
    if not path_rows:
        return []
    available = { _clean_label(row.get("id")): row for row in path_rows if isinstance(row, Mapping) and _clean_label(row.get("id"))}
    chains: List[Dict[str, Any]] = []
    for chain_id, chain in _MECHANISM_CHAINS.items():
        if not isinstance(chain, Mapping):
            continue
        chain_rows = _build_mechanism_chain(chain_id=chain_id, chain_def=chain, available_paths=available)
        if not chain_rows.get("required_path_ids"):
            continue
        chains.append(chain_rows)

    if not chains:
        return []

    def _chain_rank(row: Mapping[str, Any]) -> tuple[float, float]:
        met = 1.0 if bool(row.get("met")) else 0.0
        return (
            met,
            _safe_float(row.get("score"), 0.0),
        )

    chains = sorted(chains, key=_chain_rank, reverse=True)
    return chains[: max(1, limit)]


def _score_paths(
    *,
    scores: Mapping[str, Any],
    profile: Mapping[str, Any],
    bazi_image: Mapping[str, Any],
    claim_nodes: Sequence[Mapping[str, Any]],
    text: str,
) -> List[Dict[str, Any]]:
    total = sum(max(0.0, _safe_float(value, 0.0)) for value in scores.values()) or 1.0
    wealth = _share(scores, _knowledge_gods("wealth_gods"), total)
    output = _share(scores, _knowledge_gods("output_gods"), total)
    authority = _share(scores, _knowledge_gods("authority_gods"), total)
    seal = _share(scores, _knowledge_gods("seal_gods"), total)
    peer = _share(scores, _knowledge_gods("peer_gods"), total)
    profile_score = _safe_float(profile.get("score"), 0.0)
    profile_risk = _safe_float(profile.get("risk"), 0.0)
    usable_state = _clean_label(profile.get("usable_state"))
    top_channel = _top_channel_id(profile)
    wealth_materials = _wealth_material_rows(bazi_image)
    vault = _wealth_vault(bazi_image)
    scoring = _knowledge_section("global_scoring")
    output_wealth_nested = _has_output_wealth_nesting(bazi_image)
    features: Dict[str, float] = {
        "wealth": wealth,
        "output": output,
        "authority": authority,
        "seal": seal,
        "peer": peer,
        "profile_score": profile_score,
        "profile_risk": profile_risk,
        "channel_stable_or_opportunity": max(_channel_score(profile, "stable_income"), _channel_score(profile, "opportunity_income")) * 0.2,
        "channel_output": _channel_score(profile, "output_to_wealth") * 0.24,
        "channel_output_small": min(0.08, _channel_score(profile, "output_to_wealth") * 0.12),
        "channel_authority": _channel_score(profile, "authority_income") * 0.26,
        "channel_knowledge": _channel_score(profile, "knowledge_asset") * 0.26,
        "channel_resource": _channel_score(profile, "resource_integration") * 0.28,
        "output_symbol_bonus": min(
            _safe_float(scoring.get("output_symbol_bonus_cap"), 0.0),
            len(_symbolic_fact_rows(bazi_image, fact_type="output_material")) * _safe_float(scoring.get("output_symbol_bonus_per_fact"), 0.0),
        ),
        "hidden_wealth_bonus": min(
            _safe_float(scoring.get("hidden_wealth_bonus_cap"), 0.0),
            len(wealth_materials) * _safe_float(scoring.get("hidden_wealth_bonus_per_fact"), 0.0),
        ),
        "hidden_authority_bonus": min(
            _safe_float(scoring.get("hidden_authority_bonus_cap"), 0.0),
            _hidden_ten_god_count(bazi_image, _knowledge_gods("authority_gods")) * _safe_float(scoring.get("hidden_authority_bonus_per_fact"), 0.0),
        ),
        "output_wealth_nested_bonus": _safe_float(scoring.get("output_wealth_nested_bonus"), 0.0) if output_wealth_nested else 0.0,
        "vault_bonus": _safe_float(scoring.get("vault_bonus"), 0.0) if vault.get("has_vault_signal") else 0.0,
        "has_wealth_material": 1.0 if wealth_materials else 0.0,
        "has_vault_signal": 1.0 if vault.get("has_vault_signal") else 0.0,
        "vault_activated": 1.0 if vault.get("vault_state") == "activated" else 0.0,
        "vault_static": 1.0 if vault.get("vault_state") != "activated" else 0.0,
        "wealth_low": 1.0 if wealth < _safe_float(scoring.get("wealth_low_threshold"), 0.0) else 0.0,
        "wealth_as_taboo": 1.0 if usable_state == "wealth_as_taboo" else 0.0,
        "top_channel_resource_integration": 1.0 if top_channel == "resource_integration" else 0.0,
        "seal_conflict": 1.0 if "财破印" in text or "财印相战" in text else 0.0,
    }

    raw: Dict[str, tuple[float, float, float, List[Mapping[str, Any]], List[str], List[Mapping[str, Any]], List[Dict[str, str]]]] = {}
    formulas = _knowledge_section("path_scoring")
    for path_id in WEALTH_PATH_TEMPLATES:
        formula = formulas.get(path_id) if isinstance(formulas.get(path_id), Mapping) else {}
        if not formula:
            continue
        claim_hits = _path_claim_hits(path_id, claim_nodes)
        keyword_hits = _keyword_hits(text, path_id)
        local_features = dict(features)
        symbolic_features, symbolic_support = _symbolic_booster_scores(path_id=path_id, bazi_image=bazi_image)
        local_features.update(symbolic_features)
        claim_bonus = sum(_safe_float(hit.get("weight"), 0.0) for hit in claim_hits)
        if not claim_bonus and keyword_hits:
            claim_bonus = min(
                _safe_float(scoring.get("claim_hit_bonus_cap"), _safe_float(scoring.get("hit_bonus_cap"), 0.0)),
                len(keyword_hits) * _safe_float(scoring.get("claim_hit_bonus_per_keyword"), _safe_float(scoring.get("hit_bonus_per_keyword"), 0.0)),
            )
        local_features["hit_bonus"] = min(
            _safe_float(scoring.get("hit_bonus_cap"), 0.0),
            claim_bonus,
        )
        if path_id == "output_to_wealth":
            explicit_hits = [
                hit
                for hit in claim_hits
                if _clean_label(hit.get("rule_id")).startswith("otw-plugin")
                or _clean_label(hit.get("plugin_id")).startswith("classical.pattern")
                or _clean_label(hit.get("plugin_id")).startswith("v17.")
            ]
            support_weight = _clamp(len(explicit_hits) * 0.12, 0.0, 0.4)
        elif path_id == "output_controls_pressure":
            explicit_hits = [
                hit
                for hit in claim_hits
                if _clean_label(hit.get("rule_id")).startswith("ocp-plugin")
                or _clean_label(hit.get("plugin_id")).startswith("classical.pattern")
            ]
            support_weight = _clamp(len(explicit_hits) * 0.12, 0.0, 0.4)
        elif path_id == "output_work_to_money":
            support_weight = 0.0
        else:
            support_weight = 0.0
        score = _formula_value(formula.get("score") if isinstance(formula.get("score"), Mapping) else {}, local_features)
        risk = _formula_value(formula.get("risk") if isinstance(formula.get("risk"), Mapping) else {}, local_features)
        score_parts = _score_parts_from_config(formula.get("score_parts"), local_features)
        score_parts.extend(
            f"{_clean_label(support.get('rule_label'))}({support.get('match_count')}次)"
            for support in symbolic_support
            if _clean_label(support.get('rule_label')) and _safe_float(support.get("weight"), 0.0) > 0
        )
        raw[path_id] = (
            score,
            risk,
            support_weight,
            score_parts,
            claim_hits,
            wealth_materials,
            symbolic_support,
        )

    rows: List[Dict[str, Any]] = []
    for path_id, (score, risk, support_weight, score_parts, claim_hits, bazi_facts, symbolic_support) in raw.items():
        threshold = _safe_float(WEALTH_PATH_TEMPLATES[path_id].get("threshold"), 0.3)
        if score < threshold and path_id not in {"wealth_vault", "leakage_risk"}:
            continue
        if path_id == "wealth_vault" and not vault.get("has_vault_signal") and score < _safe_float(scoring.get("wealth_vault_without_vault_score_min"), 0.35):
            continue
        if path_id == "leakage_risk" and risk < _safe_float(scoring.get("leakage_risk_min"), 0.42) and score < _safe_float(scoring.get("leakage_score_min"), 0.34):
            continue
        rows.append(
            _path_row(
                path_id=path_id,
                score=score,
                risk=risk,
                support_weight=support_weight,
                claim_hits=claim_hits,
                score_parts=score_parts,
                bazi_facts=bazi_facts,
                profile=profile,
                symbolic_support=symbolic_support,
            )
        )
    return sorted(
        rows,
        key=lambda row: (
            _safe_float(row.get("score"), 0.0) + _safe_float(row.get("support_weight"), 0.0),
            ( _safe_float(row.get("claim_signal"), 0.0) if _clean_label(row.get("id")) != "resource_integration" else 0.0),
            -_path_priority(_clean_label(row.get("id"))),
            -_safe_float(row.get("risk"), 0.0),
        ),
        reverse=True,
    )


def _merge_output_work_path(primary: Mapping[str, Any], secondary: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    out = dict(primary)
    secondary_by_id = {str(row.get("id") or ""): row for row in secondary if isinstance(row, Mapping)}
    primary_id = _clean_label(out.get("id"))
    combinations = _knowledge_section("combination_paths")
    combo_id = ""
    pair_id = ""
    combo: Mapping[str, Any] = {}
    for candidate_id, candidate in combinations.items():
        if not isinstance(candidate, Mapping):
            continue
        source_ids = [str(item or "") for item in candidate.get("source_ids") or []]
        if primary_id not in source_ids:
            continue
        matched_pair = next((source_id for source_id in source_ids if source_id != primary_id and source_id in secondary_by_id), "")
        if not matched_pair:
            continue
        combo_id = str(candidate_id)
        pair_id = matched_pair
        combo = candidate
        break
    if not combo_id or not pair_id:
        return out

    pair = secondary_by_id[pair_id]
    out["id"] = combo_id
    for key in ("classic_label", "plain_name", "plain_summary", "driver", "carrier_type", "risk_hint"):
        value = _clean_label(combo.get(key), limit=320)
        if value:
            out[key] = value
    evidence = _clean_str_list([combo.get("evidence")], limit=1)
    evidence.extend(item for item in out.get("evidence") or [] if item not in evidence)
    evidence.extend(item for item in pair.get("evidence") or [] if item not in evidence)
    out["evidence"] = _clean_str_list(evidence, limit=10)
    out["score"] = round(_clamp(max(_safe_float(out.get("score"), 0.0), _safe_float(pair.get("score"), 0.0))), 3)
    out["risk"] = round(_clamp(max(_safe_float(out.get("risk"), 0.0), _safe_float(pair.get("risk"), 0.0))), 3)
    out["confidence"] = round(_clamp(max(_safe_float(out.get("confidence"), 0.0), _safe_float(pair.get("confidence"), 0.0)) + 0.04), 3)
    out["claim_supports"] = _merge_claim_supports(
        primary.get("claim_supports", []),
        pair.get("claim_supports", []),
    )
    return out


def _carrier(primary_path: Mapping[str, Any], profile: Mapping[str, Any]) -> Dict[str, Any]:
    carrier_type = _clean_label(primary_path.get("carrier_type")) or "mixed"
    requirements = _clean_str_list(profile.get("bridge_requirements"), limit=4)
    if not requirements:
        requirement_map = _knowledge_section("carrier_requirements")
        requirements = _clean_str_list(requirement_map.get(carrier_type), limit=4) or ["先明确收入来源、承接条件和风险边界"]
    score = _clamp(_safe_float(primary_path.get("score"), 0.0) - _safe_float(primary_path.get("risk"), 0.0) * 0.22 + 0.18)
    plain_types = _knowledge_section("carrier_plain_types")
    return {
        "type": carrier_type,
        "plain_type": _clean_label(plain_types.get(carrier_type)) or "综合承接能力",
        "score": round(score, 3),
        "requirements": requirements,
    }


def _monetization_engine(primary_path: Mapping[str, Any]) -> Dict[str, Any]:
    driver = _clean_label(primary_path.get("driver")) or "mixed"
    score = _safe_float(primary_path.get("score"), 0.0)
    risk = _safe_float(primary_path.get("risk"), 0.0)
    drivers = _knowledge_section("monetization_drivers")
    return {
        "driver": driver,
        "plain_driver": _clean_label(drivers.get(driver)) or "混合变现链路",
        "chain_integrity": round(_clamp(score * 0.72 + (1.0 - risk) * 0.28), 3),
    }


def _leakage_points(paths: Sequence[Mapping[str, Any]], profile: Mapping[str, Any]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for path in paths:
        if path.get("id") != "leakage_risk":
            continue
        rows.append(
            {
                "id": "peer_split",
                "plain_name": "合作分账与现金流泄漏",
                "risk": round(_safe_float(path.get("risk"), 0.0), 3),
                "evidence": _clean_str_list(path.get("evidence"), limit=5),
            }
        )
    for risk_text in _clean_str_list(profile.get("risks"), limit=4):
        if any(word in risk_text for word in ("合作", "分账", "现金流", "成本", "承诺")):
            rows.append(
                {
                    "id": f"profile_risk_{len(rows) + 1}",
                    "plain_name": risk_text,
                    "risk": round(max(0.32, _safe_float(profile.get("risk"), 0.0)), 3),
                    "evidence": ["来自财富画像风险"],
                }
            )
    return rows[:5]


def _timeline_rows(meta: Mapping[str, Any]) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    preview = meta.get("wealth_timeline_preview") if isinstance(meta.get("wealth_timeline_preview"), Mapping) else {}
    if not preview:
        return [], []
    luck_window = preview.get("luck_window") if isinstance(preview.get("luck_window"), Mapping) else {}
    trends = []
    if luck_window:
        trends.append(
            {
                "luck_pillar": _clean_label(luck_window.get("luck_pillar")),
                "start_year": luck_window.get("start_year"),
                "end_year": luck_window.get("end_year"),
                "summary": _clean_label(luck_window.get("summary"), limit=160),
                "score": round(_safe_float(luck_window.get("score"), 0.0), 3),
                "risk": round(_safe_float(luck_window.get("risk"), 0.0), 3),
            }
        )
    watchlist = []
    for row in preview.get("top_attention_years") if isinstance(preview.get("top_attention_years"), list) else []:
        if not isinstance(row, Mapping):
            continue
        watchlist.append(
            {
                "year": row.get("year"),
                "focus": _clean_label(row.get("focus")),
                "attention_type": _clean_label(row.get("attention_type")),
                "score": round(_safe_float(row.get("score"), 0.0), 3),
                "risk": round(_safe_float(row.get("risk"), 0.0), 3),
                "triggered_components": _clean_str_list(row.get("tags"), limit=5),
            }
        )
    return trends[:2], watchlist[:5]


def _evidence_graph(
    *,
    primary_path: Mapping[str, Any],
    secondary_paths: Sequence[Mapping[str, Any]],
    mechanism_chains: Sequence[Mapping[str, Any]] | None = None,
    wealth_source: Mapping[str, Any],
    wealth_vault: Mapping[str, Any],
    leakage_points: Sequence[Mapping[str, Any]],
) -> Dict[str, Any]:
    primary_id = _clean_label(primary_path.get("id") or "primary_path")

    claim_nodes_map: Dict[str, Dict[str, str]] = {}
    for path in (primary_path, *secondary_paths):
        for row in path.get("claim_supports", []):
            if not isinstance(row, Mapping):
                continue
            claim_id = _clean_label(row.get("claim_id"))
            if not claim_id:
                continue
            rule_id = _clean_label(row.get("rule_id"))
            text = _clean_label(row.get("claim_text"), limit=70)
            claim_nodes_map.setdefault(
                claim_id,
                {
                    "id": claim_id,
                    "type": "claim",
                    "label": _clean_label(row.get("evidence") or text or claim_id, limit=70),
                    "plugin_id": _clean_label(row.get("plugin_id")),
                    "rule_id": rule_id,
                },
            )

    claim_edges: List[Dict[str, Any]] = []
    for path in (primary_path, *secondary_paths):
        path_id = _clean_label(path.get("id"))
        if not path_id:
            continue
        for row in path.get("claim_supports", []):
            if not isinstance(row, Mapping):
                continue
            claim_id = _clean_label(row.get("claim_id"))
            if not claim_id:
                continue
            weight = _safe_float(row.get("weight"), 0.0)
            claim_edges.append(
                {
                    "from": claim_id,
                    "to": path_id,
                    "relation": "supports",
                    "evidence_weight": round(weight, 4),
                    "rule_id": _clean_label(row.get("rule_id")),
                }
            )

    nodes: List[Dict[str, Any]] = [
        {"id": "wealth_source", "type": "source", "label": _clean_label(wealth_source.get("plain_source"))},
        {"id": primary_id, "type": "path", "label": _clean_label(primary_path.get("plain_name"))},
    ]
    edges: List[Dict[str, Any]] = [{"from": "wealth_source", "to": primary_id, "relation": "feeds"}]
    chain_nodes = list(mechanism_chains or [])[:2]
    chain_seen: set[str] = set()
    for chain in chain_nodes:
        chain_id = _clean_label(chain.get("id"))
        if not chain_id or chain_id in chain_seen:
            continue
        chain_seen.add(chain_id)
        chain_label = _clean_label(chain.get("plain_name") or chain.get("chain_name"), limit=72)
        chain_node_id = f"chain:{chain_id}"
        nodes.append({"id": chain_node_id, "type": "mechanism_chain", "label": chain_label})
        edges.append({"from": chain_node_id, "to": primary_id, "relation": "materializes"})
        for index, step in enumerate(chain.get("steps") if isinstance(chain.get("steps"), list) else [], start=1):
            path_id = _clean_label(step.get("path_id"))
            if not path_id:
                continue
            step_node_id = f"{chain_node_id}:{path_id}"
            present = bool(step.get("present"))
            step_label = _clean_label(step.get("plain_name"), limit=72) or f"{index}. {path_id}"
            nodes.append(
                {
                    "id": step_node_id,
                    "type": "mechanism_step",
                    "label": step_label,
                    "chain_id": chain_id,
                    "path_id": path_id,
                    "present": present,
                }
            )
            edges.append({"from": step_node_id, "to": chain_node_id, "relation": "contains"})
            if present and path_id in { _clean_label(row.get("id") or "") for row in secondary_paths } | {_clean_label(primary_path.get("id") or "")}:
                edges.append({"from": path_id, "to": step_node_id, "relation": "supports"})
    nodes.extend(
        {"id": claim_id, "type": "claim", "label": row["label"], "plugin_id": row.get("plugin_id"), "rule_id": row.get("rule_id")}
        for claim_id, row in claim_nodes_map.items()
    )
    for path in secondary_paths[:3]:
        pid = _clean_label(path.get("id"))
        nodes.append({"id": pid, "type": "secondary_path", "label": _clean_label(path.get("plain_name"))})
        edges.append({"from": pid, "to": primary_id, "relation": "supports_or_competes"})
    if wealth_vault.get("has_vault_signal"):
        nodes.append({"id": "wealth_vault", "type": "vault", "label": _clean_label(wealth_vault.get("plain_summary"), limit=80)})
        edges.append({"from": "wealth_vault", "to": primary_id, "relation": "stores_or_releases"})
    for index, row in enumerate(leakage_points[:3], start=1):
        rid = f"leakage_{index}"
        nodes.append({"id": rid, "type": "risk", "label": _clean_label(row.get("plain_name"), limit=80)})
        edges.append({"from": rid, "to": primary_id, "relation": "leaks"})
    edges.extend(claim_edges)
    return {"nodes": nodes, "edges": edges}


def build_wealth_code_contract() -> Dict[str, Any]:
    return {
        "contract": WEALTH_CODE_CONTRACT,
        "is_l3_topic_decoder": True,
        "topic": "wealth",
        "knowledge_base": WEALTH_PATH_KNOWLEDGE_ID,
        "path_templates": list(WEALTH_PATH_TEMPLATES.keys()),
        "final_meta_keys": list(FINAL_WEALTH_CODE_KEYS),
        "read_only_sources": [
            "bazi_image",
            "wealth_profile",
            "ten_gods_runtime",
            "god_ring_authority",
            "plugin_claims",
            "wealth_timeline_preview",
        ],
        "constraints": [
            "财富密码只读 L0-L3 已有事实，不回写体用、格局、十神能量或参数。",
            "财富路径评分只表示路径闭合度和关注方向，不承诺金额、必发财或确定年份。",
            "LLM 只能消费 wealth_code 合同，不得自由读取原始八字重新推断。",
        ],
    }


def normalize_wealth_code_meta(value: Any) -> Dict[str, Any]:
    if not isinstance(value, Mapping) or not value:
        return {}
    out = {key: value.get(key) for key in FINAL_WEALTH_CODE_KEYS if key in value}
    out["contract"] = _clean_label(out.get("contract")) or WEALTH_CODE_CONTRACT
    out["topic"] = _clean_label(out.get("topic")) or "wealth"
    out["is_l3_topic_decoder"] = bool(out.get("is_l3_topic_decoder", True))
    out["knowledge_base"] = dict(out.get("knowledge_base")) if isinstance(out.get("knowledge_base"), Mapping) else {
        "id": WEALTH_PATH_KNOWLEDGE_ID,
        "mode": "versioned_rule_knowledge",
    }
    for key in (
        "secondary_paths",
        "path_rankings",
        "leakage_points",
        "decade_path_trends",
        "flow_year_watchlist",
        "mechanism_chains",
        "evidence",
        "learning_hooks",
        "guardrails",
    ):
        raw = out.get(key)
        out[key] = list(raw) if isinstance(raw, list) else []
    for key in ("primary_wealth_path", "wealth_source", "monetization_engine", "carrier", "wealth_vault", "evidence_graph", "llm_boundary"):
        raw = out.get(key)
        out[key] = dict(raw) if isinstance(raw, Mapping) else {}
    out["score"] = round(_clamp(_safe_float(out.get("score"), 0.0)), 3)
    out["confidence"] = round(_clamp(_safe_float(out.get("confidence"), 0.0)), 3)
    out["risk"] = round(_clamp(_safe_float(out.get("risk"), 0.0)), 3)
    return out


def resolve_wealth_code(physics_tensor: Dict[str, Any]) -> Dict[str, Any]:
    pt = physics_tensor if isinstance(physics_tensor, dict) else {}
    meta = pt.get("meta") if isinstance(pt.get("meta"), dict) else {}
    profile = _profile_from_tensor(pt, meta)
    bazi_image = _bazi_image_from_tensor(pt, meta)
    scores = read_runtime_scores(pt)
    if not scores:
        scores = pt.get("deity_scores") if isinstance(pt.get("deity_scores"), dict) else {}
    claim_nodes = _claim_nodes_from_tensor(pt, meta)
    text = _facts_text(pt, meta)
    if not profile and not bazi_image and not scores:
        return {"wealth_code": {}, "confidence": 0.0}

    paths = _score_paths(scores=scores, profile=profile, bazi_image=bazi_image, claim_nodes=claim_nodes, text=text)
    if not paths:
        return {"wealth_code": {}, "confidence": 0.0}

    opportunity_paths = [row for row in paths if row.get("id") != "leakage_risk"]
    raw_primary = opportunity_paths[0] if opportunity_paths else paths[0]
    raw_secondary = [row for row in paths if row.get("id") != raw_primary.get("id")][:5]
    raw_primary_id = _clean_label(raw_primary.get("id"))
    primary = _merge_output_work_path(raw_primary, raw_secondary)
    merged_from_raw = _clean_label(primary.get("id")) != raw_primary_id
    secondary_rows = [row for row in paths if row.get("id") != primary.get("id")]
    if merged_from_raw and raw_primary_id and all(_clean_label(row.get("id")) != raw_primary_id for row in secondary_rows):
        secondary_rows.append(raw_primary)
    secondary = secondary_rows[:5]
    mechanism_chains = _infer_mechanism_chains(paths, limit=4)
    if mechanism_chains:
        top_chain = mechanism_chains[0]
        if _safe_float(top_chain.get("score"), 0.0) > _safe_float(primary.get("score"), 0.0):
            primary["score"] = _safe_float(top_chain.get("score"), 0.0)
        if bool(top_chain.get("met")):
            primary["mechanism_chain"] = {
                "id": _clean_label(top_chain.get("id")),
                "plain_name": _clean_label(top_chain.get("plain_name")),
                "chain_name": _clean_label(top_chain.get("chain_name")),
                "plain_summary": _clean_label(top_chain.get("plain_summary")),
                "steps": top_chain.get("steps", []),
            }
            primary["plain_summary"] = _clean_label(top_chain.get("plain_summary"), limit=260)
        primary["mechanism_candidates"] = mechanism_chains
    path_rankings = _build_path_rankings(primary=primary, secondary=secondary, mechanism_chains=mechanism_chains)
    wealth_source = _wealth_source(bazi_image, profile, primary_path=primary)
    wealth_vault = _wealth_vault(bazi_image)
    leakage = _leakage_points(paths, profile)
    decade_trends, year_watchlist = _timeline_rows(meta)
    risk = _clamp(max(_safe_float(primary.get("risk"), 0.0), _safe_float(profile.get("risk"), 0.0), max((_safe_float(row.get("risk"), 0.0) for row in leakage), default=0.0) * 0.88))
    score = _clamp(max(_safe_float(primary.get("score"), 0.0), _safe_float(profile.get("score"), 0.0) * 0.86))
    confidence = _clamp(
        0.34
        + _safe_float(primary.get("confidence"), 0.0) * 0.34
        + _safe_float(profile.get("confidence"), 0.0) * 0.18
        + (0.08 if bazi_image else 0.0)
        + min(0.08, len(secondary) * 0.018),
        0.35,
        0.92,
    )
    evidence = list(primary.get("evidence") or [])
    evidence.extend(_clean_str_list(profile.get("evidence"), limit=4))
    if wealth_source.get("plain_source"):
        evidence.append("财源材质：" + _clean_label(wealth_source.get("plain_source"), limit=120))
    if wealth_vault.get("has_vault_signal"):
        evidence.append("财库观察：" + _clean_label(wealth_vault.get("plain_summary"), limit=140))

    code = {
        "contract": WEALTH_CODE_CONTRACT,
        "topic": "wealth",
        "is_l3_topic_decoder": True,
        "knowledge_base": {
            "id": WEALTH_PATH_KNOWLEDGE_ID,
            "mode": _clean_label(load_wealth_code_knowledge().get("mode")) or "versioned_rule_knowledge",
            "version": _clean_label(load_wealth_code_knowledge().get("version")),
            "template_count": len(WEALTH_PATH_TEMPLATES),
        },
        "score": round(score, 3),
        "confidence": round(confidence, 3),
        "risk": round(risk, 3),
        "primary_wealth_path": primary,
        "secondary_paths": secondary,
        "path_rankings": path_rankings,
        "mechanism_chains": mechanism_chains,
        "wealth_source": wealth_source,
        "monetization_engine": _monetization_engine(primary),
        "carrier": _carrier(primary, profile),
        "wealth_vault": wealth_vault,
        "leakage_points": leakage,
        "decade_path_trends": decade_trends,
        "flow_year_watchlist": year_watchlist,
        "evidence_graph": _evidence_graph(
            primary_path=primary,
            secondary_paths=secondary,
            mechanism_chains=mechanism_chains,
            wealth_source=wealth_source,
            wealth_vault=wealth_vault,
            leakage_points=leakage,
        ),
        "evidence": _clean_str_list(evidence, limit=12),
        "llm_boundary": {
            "allowed_inputs": ["wealth_code", "wealth_profile", "wealth_timeline"],
            "forbidden_inputs": ["raw_bazi_free_read", "raw_birth_time", "free_chart_reinterpretation"],
            "must_avoid": ["必发财", "无财", "破产", "确定金额", "确定发财年份", "把财星强弱直接等同财富成败"],
        },
        "learning_hooks": [
            "topic.wealth_code.path.calibration",
            "topic.wealth_code.vault.calibration",
            "topic.wealth_code.leakage.calibration",
        ],
        "guardrails": build_wealth_code_contract()["constraints"],
    }
    normalized = normalize_wealth_code_meta(code)
    return {"contract": normalized["contract"], "confidence": normalized["confidence"], "wealth_code": normalized}
