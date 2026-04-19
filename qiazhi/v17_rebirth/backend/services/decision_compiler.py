from __future__ import annotations

import math
from typing import Any, Dict, List

from v17_rebirth.backend.plugins.spec import V17Decision, V17Fact
from v17_rebirth.backend.services.plugin_display import plugin_source_label
from v17_rebirth.backend.services.target_god_resolver import infer_target_god_from_text, resolve_target_god


def infer_decision_hint(*, plugin_id: str, fact_text: str, meta: Dict[str, Any]) -> str:
    text = str(fact_text or "").strip()
    pid = str(plugin_id or "").strip()
    if not text:
        return ""
    explicit_map = (
        ("六冲", "六冲"),
        ("六破", "六破"),
        ("六合", "六合"),
        ("六害", "六害"),
        ("三刑", "三刑"),
        ("半合", "半合聚势"),
        ("墓库", "墓库门态"),
        ("天干五合", "天干羁绊"),
        ("地支场烈度", "地支场烈度"),
        ("格局", "格局对焦"),
        ("做功", "做功检视"),
        ("状态机", "状态机节律"),
    )
    for marker, label in explicit_map:
        if marker in text:
            return label
    suffix_map = {
        "liuchong": "六冲",
        "liupo": "六破",
        "liuhe": "六合",
        "sanxing": "三刑",
        "banhe": "半合聚势",
        "muku": "墓库门态",
        "stem_fusion_stuck": "天干羁绊",
        "full_bandwidth": "地支场烈度",
    }
    for suffix, label in suffix_map.items():
        if pid.endswith(suffix):
            return label
    if "impact_ratio" in meta:
        return text.split("：", 1)[0][:12]
    return ""


def _resolve_exclusivity_key(*, source: str, target_god: str, meta: Dict[str, Any] | None, source_event: str = "") -> str:
    source_name = str(source or "").strip()
    target_name = str(target_god or "").strip() or "any"
    if not isinstance(meta, dict):
        meta = {}
    explicit = str(meta.get("exclusivity_key") or "").strip()
    if explicit:
        return explicit
    explicit = str(meta.get("source_event") or meta.get("source_key") or "").strip()
    if explicit:
        return explicit
    event = str(source_event or "").strip()
    if event:
        return event
    if source_name:
        return f"{source_name}|{target_name}"
    return f"manual|{target_name}"


def decision_relative_impact(title: str, target_god: str) -> Dict[str, Any]:
    text = str(title or "").strip()
    impact: Dict[str, Any] = {"target_god": str(target_god or "").strip()}
    if not text:
        return impact

    if any(k in text for k in ["格局转换", "坍塌", "翻盘", "断裂"]):
        return {
            **impact,
            "impact_ratio": 0.20,
            "intensity_level": 4,
            "significance_level": "L3",
            "significance_weight": 1.0,
            "resistance_mod": {"path": "pattern_shift", "factor": 0.35},
        }
    if any(k in text for k in ["冲", "刑", "破", "害", "克", "制", "杀"]):
        return {
            **impact,
            "impact_ratio": 0.12,
            "intensity_level": 3,
            "significance_level": "L3",
            "significance_weight": 1.0,
            "resistance_mod": {"path": "auto_clash", "factor": 0.4},
        }
    if any(k in text for k in ["合", "化", "生", "助", "聚势", "护持"]):
        return {
            **impact,
            "impact_ratio": 0.06,
            "intensity_level": 2,
            "significance_level": "L2",
            "significance_weight": 1.0,
            "resistance_mod": {"path": "auto_sheng", "factor": 0.75},
        }
    if any(k in text for k in ["节律", "边界", "确认", "校准", "承诺", "节奏"]):
        return {
            **impact,
            "impact_ratio": 0.025,
            "intensity_level": 1,
            "significance_level": "L1",
            "significance_weight": 0.8,
        }
    return {
        **impact,
        "impact_ratio": 0.015,
        "intensity_level": 1,
        "significance_level": "L0",
        "significance_weight": 0.6,
    }


def _source_label(source: Any) -> str:
    raw = str(source or "").strip()
    if not raw:
        return "未知规则"
    return plugin_source_label(raw)


def _arbitration_mode_label(mode: str) -> str:
    if mode == "manual":
        return "手动"
    if mode == "system":
        return "自动"
    return "LLM"


def _annotate_arbitration_trace(row: Dict[str, Any], mode: str) -> Dict[str, Any]:
    cloned = dict(row)
    impact = cloned.get("physical_impact") if isinstance(cloned.get("physical_impact"), dict) else {}
    level = 0 if bool(cloned.get("physical_impact_inferred")) else int(impact.get("intensity_level") or 0)
    cloned["source_label"] = str(cloned.get("source_label") or _source_label(cloned.get("source") or cloned.get("plugin_id")))
    cloned["arbitration_mode"] = mode
    cloned["arbitration_trace"] = f"{cloned['source_label']} -> L{level if level > 0 else '?'} -> {_arbitration_mode_label(mode)}"
    return cloned


def _llm_resolution_policy(row: Dict[str, Any]) -> str:
    impact = row.get("physical_impact") if isinstance(row.get("physical_impact"), dict) else {}
    label = str(row.get("label") or row.get("title") or "").strip()
    title = str(row.get("title") or "").strip()
    text = f"{label} {title}"
    level = int(impact.get("intensity_level") or 0)
    target_god = str(row.get("target_god") or impact.get("target_god") or "").strip()
    hard_risk_markers = ("格局", "坍塌", "转换", "翻盘", "断裂")
    if any(marker in text for marker in hard_risk_markers):
        return "context_only"
    if target_god and 0 < level <= 2:
        return "auto_apply"
    if target_god:
        return "suggest_only"
    return "context_only"


def _llm_resolution_result(policy: str) -> str:
    if policy == "auto_apply":
        return "collapse_system"
    if policy == "suggest_only":
        return "promote_manual"
    return "consume_context"


def _llm_resolution_state(policy: str) -> str:
    if policy == "auto_apply":
        return "collapsed_to_system"
    if policy == "suggest_only":
        return "promoted_to_manual"
    return "pending_context"


def _collapse_llm_auto_apply(row: Dict[str, Any]) -> Dict[str, Any]:
    cloned = dict(row)
    cloned["arbitration_mode"] = "system"
    cloned["resolved_from_llm"] = True
    cloned["llm_resolution_state"] = _llm_resolution_state("auto_apply")
    cloned["llm_terminal_state"] = "collapse_system"
    cloned["arbitration_trace"] = f"{cloned.get('source_label') or _source_label(cloned.get('source') or cloned.get('plugin_id'))} -> L{int((cloned.get('physical_impact') or {}).get('intensity_level') or 0) or '?'} -> LLM裁决 -> 自动"
    return cloned


def _promote_llm_suggest(row: Dict[str, Any]) -> Dict[str, Any]:
    cloned = dict(row)
    cloned["arbitration_mode"] = "manual"
    cloned["resolved_from_llm"] = True
    cloned["llm_resolution_state"] = _llm_resolution_state("suggest_only")
    cloned["llm_terminal_state"] = "promote_manual"
    cloned["arbitration_trace"] = f"{cloned.get('source_label') or _source_label(cloned.get('source') or cloned.get('plugin_id'))} -> L{int((cloned.get('physical_impact') or {}).get('intensity_level') or 0) or '?'} -> LLM裁决 -> 手动"
    return cloned


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
        physical_impact = dict(row.get("physical_impact") or {}) if isinstance(row.get("physical_impact"), dict) else {}
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
            physical_impact = decision_relative_impact(row["title"], target_god)
            row["physical_impact_inferred"] = True
        elif target_god and not str(physical_impact.get("target_god") or "").strip():
            physical_impact["target_god"] = target_god
            row["physical_impact_inferred"] = False
        else:
            row["physical_impact_inferred"] = False
        row["physical_impact"] = physical_impact
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
        row["exclusivity_key"] = _resolve_exclusivity_key(
            source=row["source"],
            target_god=target_god,
            meta=physical_impact if isinstance(physical_impact, dict) else None,
            source_event=str(row.get("source_event") or ""),
        )
        if not isinstance(row["physical_impact"], dict) or not row["physical_impact"]:
            row["physical_impact"] = decision_relative_impact(row["title"], row["target_god"])
            row["physical_impact_inferred"] = True
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
        existing_impact = row.get("physical_impact") if isinstance(row.get("physical_impact"), dict) else {}
        row["target_god"] = resolve_target_god(
            row_target=row.get("target_god"),
            impact=existing_impact,
            meta=meta,
            title=row.get("title") or fact.text,
            label=row.get("label") or hint,
            plugin_id=fact.plugin_id,
            physics_tensor=physics_tensor,
        )
        row["physical_impact"] = dict(existing_impact or meta or decision_relative_impact(row["title"], row["target_god"]))
        row["exclusivity_key"] = row.get("exclusivity_key") or _resolve_exclusivity_key(
            source=str(row.get("source") or row.get("plugin_id") or fact.plugin_id or "fact"),
            target_god=str(row.get("target_god") or ""),
            meta=meta,
            source_event=str(row.get("source_event") or ""),
        )
        if not row["physical_impact"]:
            row["physical_impact"] = decision_relative_impact(row["title"], row["target_god"])
            row["physical_impact_inferred"] = True
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
        if "impact_ratio" not in meta:
            continue
        try:
            impact_ratio = float(meta.get("impact_ratio", 0.0) or 0.0)
            significance_weight = float(meta.get("significance_weight", 1.0) or 1.0)
        except (TypeError, ValueError):
            continue
        if not math.isfinite(impact_ratio) or not math.isfinite(significance_weight):
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
                "significance_weight": significance_weight,
                "arbiter_type": arbiter,
                "causal_tier": int(fact.causal_tier or 0),
            }
        )
    return proposals


def _is_manual_candidate(row: Dict[str, Any]) -> bool:
    arbiter_val = str(row.get("arbiter_type") or "").strip().lower()
    impact = row.get("physical_impact") if isinstance(row.get("physical_impact"), dict) else {}
    target_god = str(row.get("target_god") or "").strip()
    label = str(row.get("label") or row.get("hint") or "").strip()
    title = str(row.get("title") or "").strip()
    text = f"{label} {title}"
    has_ratio = "impact_ratio" in impact
    executable = bool(target_god and has_ratio)

    # User-routed rows still need to be executable. Otherwise they should degrade to context.
    if arbiter_val == "user":
        return executable

    blockers = ("状态机", "快照", "显影", "诊断", "报告", "映射", "墓库", "观察")
    if not executable:
        return False
    return not any(k in text for k in blockers)


def _is_auto_candidate(row: Dict[str, Any]) -> bool:
    # V17.99: 优先服从预设的裁决标签
    arbiter_val = str(row.get("arbiter_type") or "").strip().lower()
    if arbiter_val == "system":
        return True
    
    impact = row.get("physical_impact") if isinstance(row.get("physical_impact"), dict) else {}
    significance = str(impact.get("significance_level") or "").strip().upper()
    source = str(row.get("source") or row.get("plugin_id") or "").strip()
    return significance == "L3" and source.startswith("l2.")


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
    def _ensure_exclusivity_key(row: Dict[str, Any]) -> None:
        if row.get("exclusivity_key"):
            return
        source = str(row.get("source") or row.get("plugin_id") or "")
        target = str(row.get("target_god") or (row.get("physical_impact") or {}).get("target_god") or "")
        source_event = str(row.get("source_event") or row.get("source_key") or "")
        impact = row.get("physical_impact") if isinstance(row.get("physical_impact"), dict) else None
        row["exclusivity_key"] = _resolve_exclusivity_key(
            source=source,
            target_god=target,
            meta=impact if isinstance(impact, dict) else None,
            source_event=source_event,
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
