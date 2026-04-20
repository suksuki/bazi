from __future__ import annotations

from typing import Any, Dict, List

from v17_rebirth.backend.plugins.spec import V17Decision, V17Fact
from v17_rebirth.backend.services.pattern_confidence import derive_pattern_confidence
from v17_rebirth.backend.services.target_god_resolver import resolve_target_god
from v17_rebirth.backend.services.decision_compiler_utils import (
    _annotate_arbitration_trace,
    _clear_observational_physics,
    _collapse_llm_auto_apply,
    _ensure_exclusivity_key,
    _is_auto_candidate,
    _is_manual_candidate,
    _is_observational_plugin_fact,
    _is_observational_row,
    _llm_resolution_policy,
    _llm_resolution_result,
    _llm_resolution_state,
    _normalize_match_ratio,
    _pick_physical_impact_from_meta,
    _promote_display_meta,
    _promote_llm_suggest,
    _resolve_exclusivity_key,
    _should_infer_physical_impact,
    decision_relative_impact,
    infer_decision_hint,
)

import math


def compile_pending_decisions(
    *,
    facts: List[V17Fact],
    spec_decisions: List[V17Decision],
    existing_rows: List[Dict[str, Any]] | None = None,
    physics_tensor: Dict[str, Any] | None = None,
) -> List[Dict[str, Any]]:
    by_identity: Dict[str, Dict[str, Any]] = {}

    for item in existing_rows or []:
        if not isinstance(item, dict):
            continue
        row = dict(item)
        title = str(row.get("title") or row.get("label") or "").strip()
        label = str(row.get("label") or row.get("hint") or title).strip()
        if not title and not label:
            continue
        row["title"] = title or label
        row["label"] = label or title
        row_meta = row.get("meta") if isinstance(row.get("meta"), dict) else None
        row_meta = derive_pattern_confidence(
            plugin_id=str(row.get("plugin_id") or row.get("source") or "legacy"),
            meta=row_meta,
            priority=float(row.get("priority", 0.5) or 0.5),
            salience_weight=float(row.get("salience_weight", 0.5) or 0.5),
        )
        if row_meta:
            row["meta"] = row_meta
        _promote_display_meta(row, row_meta)
        physical_impact = dict(row.get("physical_impact") or {}) if isinstance(row.get("physical_impact"), dict) else {}
        if _is_observational_row(
            source=str(row.get("source") or row.get("plugin_id") or "legacy"),
            plugin_id=str(row.get("plugin_id") or row.get("source") or "legacy"),
            meta=row_meta,
            physical_impact=physical_impact,
        ):
            _clear_observational_physics(row)
            physical_impact = {}
        target_god = resolve_target_god(
            row_target=row.get("target_god"),
            impact=physical_impact,
            title=row.get("title"),
            label=row.get("label"),
            plugin_id=row.get("plugin_id") or row.get("source"),
            physics_tensor=physics_tensor,
        )
        row["target_god"] = target_god
        row["exclusivity_key"] = _resolve_exclusivity_key(
            source=str(row.get("source") or row.get("plugin_id") or "legacy"),
            target_god=target_god,
            meta=physical_impact if isinstance(physical_impact, dict) else None,
            source_event=str(row.get("source_event") or ""),
        )
        if not physical_impact:
            if _should_infer_physical_impact(source=str(row.get("source") or row.get("plugin_id") or "legacy")):
                physical_impact = decision_relative_impact(row["title"], target_god)
                row["physical_impact_inferred"] = True
            else:
                physical_impact = {}
                row["physical_impact_inferred"] = False
        elif target_god and not str(physical_impact.get("target_god") or "").strip():
            physical_impact["target_god"] = target_god
            row["physical_impact_inferred"] = False
        else:
            row["physical_impact_inferred"] = False
        row["physical_impact"] = physical_impact
        row["exclusivity_key"] = row.get("exclusivity_key") or _resolve_exclusivity_key(
            source=str(row.get("source") or row.get("plugin_id") or "legacy"),
            target_god=target_god,
            meta=physical_impact if isinstance(physical_impact, dict) else None,
            source_event=str(row.get("source_event") or ""),
        )
        # V17.99: 废除 Target God 歧视。
        # 即便没有明确的目标神位移，描述性/诊断性的 L1-L4 事实也必须进入 Inbox。
        key = f"{str(row.get('source') or row.get('plugin_id') or 'legacy')}|{row['label']}"
        by_identity[key] = row

    for decision in spec_decisions:
        physical_impact = dict(decision.physical_impact or {})
        target_god = resolve_target_god(
            row_target=decision.target_god,
            impact=physical_impact,
            title=decision.title,
            label=decision.label,
            plugin_id=decision.source,
            physics_tensor=physics_tensor,
        )
        row = {
            "id": decision.id,
            "title": str(decision.title or "").strip(),
            "label": str(decision.label or "").strip(),
            "source": str(decision.source or "").strip(),
            "priority": float(decision.priority or 0.0),
            "target_god": target_god,
            "physical_impact": physical_impact,
        }
        if _is_observational_row(
            source=row["source"],
            plugin_id=decision.source,
            meta=physical_impact,
            physical_impact=physical_impact,
        ):
            _clear_observational_physics(row)
            physical_impact = {}
        row["exclusivity_key"] = _resolve_exclusivity_key(
            source=row["source"],
            target_god=target_god,
            meta=physical_impact if isinstance(physical_impact, dict) else None,
            source_event=str(row.get("source_event") or ""),
        )
        if not isinstance(row["physical_impact"], dict) or not row["physical_impact"]:
            if _should_infer_physical_impact(source=row["source"]):
                row["physical_impact"] = decision_relative_impact(row["title"], row["target_god"])
                row["physical_impact_inferred"] = True
            else:
                row["physical_impact"] = {}
                row["physical_impact_inferred"] = False
        elif row["target_god"] and not str(row["physical_impact"].get("target_god") or "").strip():
            row["physical_impact"]["target_god"] = row["target_god"]
            row["physical_impact_inferred"] = False
        else:
            row["physical_impact_inferred"] = False
        row["physical_impact"] = physical_impact
        # V17.99: 废除归并层对 Target God 的强制要求
        key = f"{row['source']}|{row['label'] or row['title']}"
        prev = by_identity.get(key)
        if prev is None or float(row["priority"]) >= float(prev.get("priority", 0.0)):
            by_identity[key] = row

    for idx, fact in enumerate(facts):
        meta = dict(fact.meta or {}) if isinstance(fact.meta, dict) else {}
        meta = derive_pattern_confidence(
            plugin_id=str(fact.plugin_id or ""),
            meta=meta,
            priority=float(fact.priority or 0.5),
            salience_weight=float(fact.salience_weight or 0.5),
        )
        hint = str(fact.decision_hint or infer_decision_hint(plugin_id=fact.plugin_id, fact_text=fact.text, meta=meta)).strip()
        if not hint:
            continue
        key = f"{fact.plugin_id}|{hint}"
        row = by_identity.get(key, {})
        row.update(
            {
                "id": str(row.get("id") or f"{fact.plugin_id}_{idx}"),
                "plugin_id": fact.plugin_id,
                "source": str(row.get("source") or fact.plugin_id),
                "title": str(row.get("title") or fact.text).strip(),
                "label": str(row.get("label") or hint).strip(),
                "hint": hint,
                "priority": max(float(row.get("priority", 0.0)), float(fact.priority or 0.0)),
            }
        )
        _promote_display_meta(row, meta)
        existing_impact = row.get("physical_impact") if isinstance(row.get("physical_impact"), dict) else {}
        is_observational = _is_observational_row(source=fact.plugin_id, plugin_id=fact.plugin_id, meta=meta, physical_impact=existing_impact)
        if is_observational:
            row["physical_impact"] = {}
            existing_impact = {}
            row["physical_impact_inferred"] = False
        row["target_god"] = resolve_target_god(
            row_target=row.get("target_god"),
            impact=existing_impact,
            meta=meta,
            title=row.get("title") or fact.text,
            label=row.get("label") or hint,
            plugin_id=fact.plugin_id,
            physics_tensor=physics_tensor,
        )
        if is_observational:
            row["physical_impact"] = {}
        elif existing_impact:
            row["physical_impact"] = existing_impact
        else:
            physical_from_meta = _pick_physical_impact_from_meta(meta)
            if physical_from_meta:
                row["physical_impact"] = physical_from_meta
            elif _should_infer_physical_impact(source=fact.plugin_id, meta=meta):
                row["physical_impact"] = decision_relative_impact(row["title"], row["target_god"])
            else:
                row["physical_impact"] = {}
        row["exclusivity_key"] = row.get("exclusivity_key") or _resolve_exclusivity_key(
            source=str(row.get("source") or row.get("plugin_id") or fact.plugin_id or "fact"),
            target_god=str(row.get("target_god") or ""),
            meta=meta,
            source_event=str(row.get("source_event") or ""),
        )
        if not row["physical_impact"]:
            if _should_infer_physical_impact(source=fact.plugin_id, meta=meta):
                row["physical_impact"] = decision_relative_impact(row["title"], row["target_god"])
                row["physical_impact_inferred"] = True
            else:
                row["physical_impact_inferred"] = False
        elif row["target_god"] and not str(row["physical_impact"].get("target_god") or "").strip():
            row["physical_impact"]["target_god"] = row["target_god"]
            row["physical_impact_inferred"] = False
        else:
            row["physical_impact_inferred"] = not bool(existing_impact or meta)

        # V17.99: 废除归并层对 Target God 的最后一道分流限制
        by_identity[key] = row

    merged = list(by_identity.values())
    merged.sort(key=lambda x: float(x.get("priority", 0.0)), reverse=True)
    return merged[:64]


def compile_modifier_proposals(
    *,
    facts: List[V17Fact],
    physics_tensor: Dict[str, Any] | None = None,
) -> List[Dict[str, Any]]:
    proposals: List[Dict[str, Any]] = []
    for idx, fact in enumerate(facts):
        claim_id = f"{str(fact.plugin_id or '').strip()}_claim_{idx}"
        meta = dict(fact.meta or {}) if isinstance(fact.meta, dict) else {}
        if _is_observational_plugin_fact(plugin_id=str(fact.plugin_id or ""), meta=meta):
            continue
        if "impact_ratio" not in meta:
            continue
        try:
            raw_impact_ratio = float(meta.get("impact_ratio", 0.0) or 0.0)
            significance_weight = float(meta.get("significance_weight", 1.0) or 1.0)
        except (TypeError, ValueError):
            continue
        match_ratio = _normalize_match_ratio(meta, fallback=float(meta.get("confidence", 1.0) or 1.0))
        impact_ratio = raw_impact_ratio * match_ratio
        if not math.isfinite(raw_impact_ratio) or not math.isfinite(impact_ratio) or not math.isfinite(significance_weight):
            continue
        target_god = resolve_target_god(
            row_target=fact.target_god,
            impact=meta,
            meta=meta,
            title=fact.text,
            label=fact.decision_hint or fact.text,
            plugin_id=fact.plugin_id,
            physics_tensor=physics_tensor,
        )
        arbiter = str(getattr(fact.suggested_arbiter, "value", fact.suggested_arbiter) or "system").strip().lower()
        if int(fact.causal_tier or 0) >= 1 and arbiter == "system":
            arbiter = "user"
        proposals.append(
            {
                "id": f"{fact.plugin_id}_proposal_{idx}",
                "claim_id": claim_id,
                "plugin_id": str(fact.plugin_id or "").strip(),
                "title": str(fact.text or "").strip(),
                "reason": str(fact.text or "").strip(),
                "target_god": target_god,
                "impact_ratio": impact_ratio,
                "raw_impact_ratio": raw_impact_ratio,
                "match_ratio": match_ratio,
                "significance_weight": significance_weight,
                "arbiter_type": arbiter,
                "causal_tier": int(fact.causal_tier or 0),
            }
        )
    return proposals


def compile_decision_arbitration(
    *,
    facts: List[V17Fact],
    spec_decisions: List[V17Decision],
    existing_rows: List[Dict[str, Any]] | None = None,
    physics_tensor: Dict[str, Any] | None = None,
) -> Dict[str, List[Dict[str, Any]]]:
    compiled = compile_pending_decisions(
        facts=facts,
        spec_decisions=spec_decisions,
        existing_rows=existing_rows,
        physics_tensor=physics_tensor,
    )
    llm_seed: List[Dict[str, Any]] = []
    for item in existing_rows or []:
        if not isinstance(item, dict):
            continue
        row = dict(item)
        row["title"] = str(row.get("title") or row.get("label") or "").strip()
        row["label"] = str(row.get("label") or row.get("hint") or row.get("title") or "").strip()
        if not row["title"] and not row["label"]:
            continue
        _ensure_exclusivity_key(row)
        llm_seed.append(row)
    for fact in facts:
        text = str(fact.text or "").strip()
        meta = dict(fact.meta or {}) if isinstance(fact.meta, dict) else {}
        hint = str(fact.decision_hint or infer_decision_hint(plugin_id=fact.plugin_id, fact_text=fact.text, meta=meta)).strip()
        if not text and not hint:
            continue
        target_god = resolve_target_god(
            meta=meta,
            title=text,
            label=hint or text,
            plugin_id=fact.plugin_id,
            physics_tensor=physics_tensor,
        )
        llm_seed.append(
            {
                "id": f"{fact.plugin_id}_llm_{len(llm_seed)}",
                "plugin_id": fact.plugin_id,
                "source": fact.plugin_id,
                "title": text,
                "label": hint or text,
                "hint": hint,
                "priority": float(fact.priority or 0.0),
                "target_god": target_god,
                "physical_impact": dict(meta),
            }
        )
        _ensure_exclusivity_key(llm_seed[-1])

    manual: List[Dict[str, Any]] = []
    auto: List[Dict[str, Any]] = []
    llm: List[Dict[str, Any]] = []
    llm_seen: set[str] = set()
    classified_seen: set[str] = set()
    for row in compiled:
        cloned = dict(row)
        _ensure_exclusivity_key(cloned)
        key = f"{cloned.get('source','')}|{cloned.get('label','')}"
        if _is_auto_candidate(cloned):
            cloned = _annotate_arbitration_trace(cloned, "system")
            auto.append(cloned)
            classified_seen.add(key)
            continue
        if _is_manual_candidate(cloned):
            cloned = _annotate_arbitration_trace(cloned, "manual")
            manual.append(cloned)
            classified_seen.add(key)
            continue
        cloned = _annotate_arbitration_trace(cloned, "llm")
        cloned["llm_resolution_policy"] = _llm_resolution_policy(cloned)
        cloned["llm_resolution_result"] = _llm_resolution_result(str(cloned["llm_resolution_policy"]))
        cloned["llm_resolution_state"] = _llm_resolution_state(str(cloned["llm_resolution_policy"]))
        cloned["llm_terminal_state"] = str(cloned["llm_resolution_result"])
        if cloned["llm_resolution_policy"] == "auto_apply":
            auto.append(_collapse_llm_auto_apply(cloned))
            classified_seen.add(key)
            continue
        if cloned["llm_resolution_policy"] == "suggest_only":
            manual.append(_promote_llm_suggest(cloned))
            classified_seen.add(key)
            continue
        llm.append(cloned)
        llm_seen.add(key)
        classified_seen.add(key)

    for row in llm_seed:
        key = f"{row.get('source','')}|{row.get('label','')}"
        if key in llm_seen or key in classified_seen:
            continue
        cloned = dict(row)
        _ensure_exclusivity_key(cloned)
        if _is_manual_candidate(cloned) or _is_auto_candidate(cloned):
            continue
        cloned = _annotate_arbitration_trace(cloned, "llm")
        cloned["llm_resolution_policy"] = _llm_resolution_policy(cloned)
        cloned["llm_resolution_result"] = _llm_resolution_result(str(cloned["llm_resolution_policy"]))
        cloned["llm_resolution_state"] = _llm_resolution_state(str(cloned["llm_resolution_policy"]))
        cloned["llm_terminal_state"] = str(cloned["llm_resolution_result"])
        if cloned["llm_resolution_policy"] == "auto_apply":
            auto.append(_collapse_llm_auto_apply(cloned))
            llm_seen.add(key)
            classified_seen.add(key)
            continue
        if cloned["llm_resolution_policy"] == "suggest_only":
            manual.append(_promote_llm_suggest(cloned))
            llm_seen.add(key)
            classified_seen.add(key)
            continue
        llm.append(cloned)
        llm_seen.add(key)
        classified_seen.add(key)

    return {
        "manual_decisions": manual[:32],
        "auto_resolutions": auto[:32],
        "llm_arbitration_context": llm[:64],
        "pending_decisions": manual[:32],
    }


__all__ = [
    "infer_decision_hint",
    "decision_relative_impact",
    "compile_pending_decisions",
    "compile_modifier_proposals",
    "compile_decision_arbitration",
]
