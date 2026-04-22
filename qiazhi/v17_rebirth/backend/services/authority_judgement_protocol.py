from __future__ import annotations

from collections import Counter
from typing import Any, Dict, Iterable, List

from v17_rebirth.backend.logic.core_engine.work_evidence_protocol import WORK_EVIDENCE_KEY
from v17_rebirth.backend.services.plugin_display import plugin_source_label


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _round_map(raw: Dict[str, float]) -> Dict[str, float]:
    return {str(key).strip(): round(float(value), 3) for key, value in raw.items() if str(key).strip() and float(value) > 0.0}


def _normalize_bias_map(raw: Any) -> Dict[str, float]:
    if not isinstance(raw, dict):
        return {}
    out: Dict[str, float] = {}
    for god, value in raw.items():
        name = str(god or "").strip()
        if not name:
            continue
        score = _safe_float(value)
        if score > 0.0:
            out[name] = round(score, 3)
    return out


def _clean_list(values: Any) -> List[str]:
    if not isinstance(values, list):
        return []
    out: List[str] = []
    seen: set[str] = set()
    for value in values:
        item = str(value or "").strip()
        if not item or item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out


def _compact_work_evidence(raw: Any) -> Dict[str, Any]:
    if not isinstance(raw, dict):
        return {}
    out: Dict[str, Any] = {}
    for key in (
        "relation_family",
        "target_god",
        "effect_type",
        "layer",
        "origin_scope",
        "condition_state",
    ):
        value = str(raw.get(key) or "").strip()
        if value:
            out[key] = value
    for key in (
        "targets",
        "members",
        "actor_members",
        "receiver_members",
        "counterpart_gods",
        "actor_gods",
        "receiver_gods",
    ):
        cleaned = _clean_list(raw.get(key))
        if cleaned:
            out[key] = cleaned
    for key in ("impact_ratio", "match_ratio", "path_strength"):
        value = _safe_float(raw.get(key))
        if value > 0.0:
            out[key] = round(value, 4)
    return out


def _evidence_summary(evidence: Dict[str, Any]) -> str:
    if not evidence:
        return ""
    family = str(evidence.get("relation_family") or "").strip()
    target = str(evidence.get("target_god") or "").strip()
    effect_type = str(evidence.get("effect_type") or "").strip()
    targets = _clean_list(evidence.get("targets"))
    actor_gods = _clean_list(evidence.get("actor_gods"))
    receiver_gods = _clean_list(evidence.get("receiver_gods"))
    members = _clean_list(evidence.get("members"))
    fragments: List[str] = []
    if family:
        fragments.append(family)
    if actor_gods and receiver_gods:
        fragments.append(f"{'/'.join(actor_gods)}->{'/'.join(receiver_gods)}")
    elif targets:
        fragments.append("目标 " + "/".join(targets[:3]))
    elif target:
        fragments.append("目标 " + target)
    if members:
        fragments.append("成员 " + "/".join(members[:4]))
    if effect_type:
        fragments.append(effect_type)
    return " · ".join(fragment for fragment in fragments if fragment)


def build_judgement_bias_protocol(decision_rows: Iterable[Dict[str, Any]] | None = None) -> Dict[str, Any]:
    use_bias: Dict[str, float] = {}
    taboo_bias: Dict[str, float] = {}
    entries: List[Dict[str, Any]] = []
    by_target: Dict[str, Dict[str, float]] = {}
    by_plugin = Counter()

    for row in decision_rows or []:
        if not isinstance(row, dict):
            continue
        impact = row.get("physical_impact") if isinstance(row.get("physical_impact"), dict) else {}
        bias = impact.get("god_ring_bias") if isinstance(impact.get("god_ring_bias"), dict) else {}
        use_entry = _normalize_bias_map(bias.get("use_bias"))
        taboo_entry = _normalize_bias_map(bias.get("taboo_bias"))
        if not use_entry and not taboo_entry:
            continue

        source = str(row.get("plugin_id") or row.get("source") or "").strip()
        label = str(row.get("label") or row.get("title") or "").strip()
        target_god = str(row.get("target_god") or impact.get("target_god") or "").strip()
        narrative_hint = str(
            impact.get("narrative_hint")
            or bias.get("narrative_hint")
            or row.get("title")
            or row.get("label")
            or ""
        ).strip()
        evidence = _compact_work_evidence(impact.get(WORK_EVIDENCE_KEY) or row.get(WORK_EVIDENCE_KEY))
        evidence_summary = _evidence_summary(evidence)

        for god, value in use_entry.items():
            use_bias[god] = round(use_bias.get(god, 0.0) + value, 3)
        for god, value in taboo_entry.items():
            taboo_bias[god] = round(taboo_bias.get(god, 0.0) + value, 3)

        if target_god:
            slot = by_target.setdefault(target_god, {"use_bias": 0.0, "taboo_bias": 0.0, "entry_count": 0.0})
            slot["use_bias"] = round(slot["use_bias"] + sum(use_entry.values()), 3)
            slot["taboo_bias"] = round(slot["taboo_bias"] + sum(taboo_entry.values()), 3)
            slot["entry_count"] = round(slot["entry_count"] + 1.0, 3)

        if source:
            by_plugin[source] += 1

        entries.append(
            {
                "decision_id": str(row.get("id") or "").strip(),
                "plugin_id": source,
                "source_label": plugin_source_label(source, fallback=label),
                "decision_label": label,
                "reason": str(bias.get("reason") or row.get("title") or row.get("label") or "").strip(),
                "target_god": target_god,
                "logic_level": str(row.get("logic_level") or "").strip(),
                "arbiter_type": str(row.get("arbiter_type") or "").strip().lower() or "unknown",
                "use_bias": use_entry,
                "taboo_bias": taboo_entry,
                "bias_total": round(sum(use_entry.values()) + sum(taboo_entry.values()), 3),
                "narrative_hint": narrative_hint,
                "evidence_contract": "v17.work_evidence.v1" if evidence else "",
                "evidence_summary": evidence_summary,
                "evidence": evidence,
            }
        )

    entries.sort(key=lambda item: float(item.get("bias_total") or 0.0), reverse=True)
    return {
        "contract": "v17.authority.judgement_bias.v1",
        "use_bias": _round_map(use_bias),
        "taboo_bias": _round_map(taboo_bias),
        "entries": entries[:16],
        "summary": {
            "entry_count": len(entries),
            "plugin_count": len(by_plugin),
            "target_count": len(by_target),
            "total_use_bias": round(sum(use_bias.values()), 3),
            "total_taboo_bias": round(sum(taboo_bias.values()), 3),
            "by_target": {god: {k: round(v, 3) for k, v in payload.items()} for god, payload in by_target.items()},
            "by_plugin": dict(by_plugin),
        },
    }


def build_stage_bias_protocol(stage_bias: Dict[str, Dict[str, float]] | None = None) -> Dict[str, Any]:
    by_target: Dict[str, Dict[str, float]] = {}
    entries: List[Dict[str, Any]] = []
    total_use = 0.0
    total_taboo = 0.0
    total_stability = 0.0
    total_volatility = 0.0
    for god, raw in (stage_bias or {}).items():
        if not god or not isinstance(raw, dict):
            continue
        entry = {
            "god": str(god).strip(),
            "lu": round(_safe_float(raw.get("lu")), 4),
            "blade": round(_safe_float(raw.get("blade")), 4),
            "general": round(_safe_float(raw.get("general")), 4),
            "stage": round(_safe_float(raw.get("stage")), 4),
            "use_boost": round(_safe_float(raw.get("use_boost")), 4),
            "taboo_boost": round(_safe_float(raw.get("taboo_boost")), 4),
            "stability_boost": round(_safe_float(raw.get("stability_boost")), 4),
            "volatility_boost": round(_safe_float(raw.get("volatility_boost")), 4),
        }
        entries.append(entry)
        by_target[entry["god"]] = {
            "use_boost": entry["use_boost"],
            "taboo_boost": entry["taboo_boost"],
            "stability_boost": entry["stability_boost"],
            "volatility_boost": entry["volatility_boost"],
        }
        total_use += entry["use_boost"]
        total_taboo += entry["taboo_boost"]
        total_stability += entry["stability_boost"]
        total_volatility += entry["volatility_boost"]

    entries.sort(
        key=lambda item: item["use_boost"] + item["taboo_boost"] + item["stability_boost"] + item["volatility_boost"],
        reverse=True,
    )
    return {
        "contract": "v17.authority.stage_bias.v1",
        "entries": entries[:12],
        "summary": {
            "entry_count": len(entries),
            "total_use_boost": round(total_use, 4),
            "total_taboo_boost": round(total_taboo, 4),
            "total_stability_boost": round(total_stability, 4),
            "total_volatility_boost": round(total_volatility, 4),
            "by_target": by_target,
        },
    }


def authority_target_signal_map(
    *,
    judgement_protocol: Dict[str, Any] | None = None,
    stage_protocol: Dict[str, Any] | None = None,
) -> Dict[str, Dict[str, float]]:
    signals: Dict[str, Dict[str, float]] = {}
    judgement_targets = (
        judgement_protocol.get("summary", {}).get("by_target")
        if isinstance(judgement_protocol, dict)
        else {}
    )
    if isinstance(judgement_targets, dict):
        for god, raw in judgement_targets.items():
            if not isinstance(raw, dict):
                continue
            signals[str(god).strip()] = {
                "judgement_use_bias": round(_safe_float(raw.get("use_bias")), 4),
                "judgement_taboo_bias": round(_safe_float(raw.get("taboo_bias")), 4),
                "judgement_entry_count": round(_safe_float(raw.get("entry_count")), 4),
            }
    stage_targets = (
        stage_protocol.get("summary", {}).get("by_target")
        if isinstance(stage_protocol, dict)
        else {}
    )
    if isinstance(stage_targets, dict):
        for god, raw in stage_targets.items():
            if not isinstance(raw, dict):
                continue
            slot = signals.setdefault(str(god).strip(), {})
            slot["stage_use_boost"] = round(_safe_float(raw.get("use_boost")), 4)
            slot["stage_taboo_boost"] = round(_safe_float(raw.get("taboo_boost")), 4)
            slot["stage_stability_boost"] = round(_safe_float(raw.get("stability_boost")), 4)
            slot["stage_volatility_boost"] = round(_safe_float(raw.get("volatility_boost")), 4)
    return signals
