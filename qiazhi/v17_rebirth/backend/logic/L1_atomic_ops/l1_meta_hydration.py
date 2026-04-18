"""
V17.99：物理水分抽取层（Hydration Hub）。
负责将 L0 静态数据转化为 L1+ 动态张量，并统一执行插件生命周期。
"""
from __future__ import annotations
import logging
from typing import Any, Dict, List, Optional

from v17_rebirth.backend.logic.L1_atomic_ops.branch_stem_geometry import (
    branches_and_stems_from_four_pillars,
    detect_stem_fusion_cases,
    eval_anhe_hits,
    eval_banhe_hits,
    eval_liu_chong_hits,
    eval_liu_hai_hits,
    eval_liu_po_hits,
    eval_liuhe_hits,
    eval_sanhe_hits,
    sanxing_detect_geometry,
    summarize_sanxing_branches,
)
from v17_rebirth.backend.logic.L0_physics_fields.vector_physics_engine import (
    _branch_dominant_ten_god,
    build_clash_stress_map,
    boost_high_stress_facts,
)
from v17_rebirth.backend.logic.L0_physics_fields.flow_physics_engine import FlowPhysicsEngine
from v17_rebirth.backend.logic.L1_atomic_ops.v17_op_fact import generate_v17_fact_from_op
from v17_rebirth.backend.logic.L0_physics_fields.ten_gods_engine import (
    STEM_ELEMENT,
    ELEMENT_CYCLE,
    ten_god_from_stems,
)
from v17_rebirth.backend.plugins.v17_wrappers import collect_pending_decisions_from_specs
from v17_rebirth.backend.services.decision_compiler import compile_pending_decisions

_log = logging.getLogger(__name__)

def _scalar_intensity(count: int, *, per: float = 0.36, bump: float = 0.09) -> float:
    if count <= 0: return 0.0
    return min(1.0, per * count + max(0, count - 1) * bump)

def _tier_cn(x: float) -> str:
    if x >= 0.8: return "猛"
    if x >= 0.5: return "中"
    if x >= 0.15: return "轻"
    return "无"

def _register_manifest_hit(hits, plugin_id, fact, label, priority, evidence=None):
    hits[plugin_id] = {
        "plugin_id": plugin_id,
        "fact": fact,
        "label": label,
        "priority": priority,
        "evidence": evidence or {},
        "activated": False,
        "last_facts": []
    }


def _manifest_hits_to_decision_rows(hits: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for plugin_id, item in (hits or {}).items():
        if not isinstance(item, dict):
            continue
        if not bool(item.get("activated")):
            continue
        title = ""
        last_facts = item.get("last_facts")
        if isinstance(last_facts, list):
            title = next((str(x).strip() for x in last_facts if str(x).strip()), "")
        if not title:
            title = str(item.get("fact") or item.get("label") or "").strip()
        label = str(item.get("label") or "").strip()
        if not title and not label:
            continue
        rows.append(
            {
                "id": f"{plugin_id}_manifest",
                "plugin_id": str(plugin_id),
                "source": str(plugin_id),
                "title": title or label,
                "label": label or title,
                "priority": float(item.get("priority", 0.0) or 0.0),
            }
        )
    return rows


def _geometry_hits_to_decision_rows(pt: Dict[str, Any], hits: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    meta = pt.get("meta") if isinstance(pt.get("meta"), dict) else {}
    stress_map = meta.get("clash_stress_map") if isinstance(meta.get("clash_stress_map"), dict) else {}
    stress_events = stress_map.get("events") if isinstance(stress_map.get("events"), list) else []
    interaction_v2 = meta.get("interaction_v2") if isinstance(meta.get("interaction_v2"), dict) else {}
    fp = pt.get("four_pillars") if isinstance(pt.get("four_pillars"), dict) else {}
    day_gz = str(fp.get("day", "")).strip()
    day_master = day_gz[0] if len(day_gz) >= 2 else "壬"

    for ev in stress_events:
        if not isinstance(ev, dict):
            continue
        if str(ev.get("source_key") or "") != "liu_chong":
            continue
        branches = ev.get("branches") if isinstance(ev.get("branches"), list) else []
        if len(branches) < 2:
            continue
        label = "六冲"
        title = f"检测到地支六冲 [{' '.join(str(x) for x in branches[:2])}]：局部结构对撞，{str(ev.get('god_j') or ev.get('god_i') or '目标神')} 受冲。"
        target_god = str(ev.get("god_j") or ev.get("god_i") or "").strip()
        rows.append(
            {
                "id": "l1.physics.op_branch_liuchong_geometry",
                "plugin_id": "l1.physics.op_branch_liuchong",
                "source": "l1.physics.op_branch_liuchong",
                "title": title,
                "label": label,
                "hint": label,
                "priority": float((hits.get("l1.physics.op_branch_liuchong") or {}).get("priority", 0.95) or 0.95),
                "target_god": target_god,
                "physical_impact": {
                    "target_god": target_god,
                    "impact_ratio": -0.12,
                    "significance_level": "L3",
                    "significance_weight": 1.0,
                    "intensity_level": 3,
                    "resistance_mod": {"path": "auto_clash", "factor": 0.4},
                },
            }
        )
        break

    sanxing_hits = interaction_v2.get("sanxing") if isinstance(interaction_v2.get("sanxing"), list) else []
    if sanxing_hits:
        hit = sanxing_hits[0] if isinstance(sanxing_hits[0], dict) else {}
        branches = hit.get("branches") if isinstance(hit.get("branches"), list) else []
        target_branch = str(branches[-1] if branches else "").strip()
        target_god = _branch_dominant_ten_god(target_branch, day_master) if target_branch else ""
        label = "三刑"
        title = f"检测到地支三刑 [{' '.join(str(x) for x in branches)}]：内压摩擦加剧，{target_god or '目标神'} 承压。"
        rows.append(
            {
                "id": "l1.physics.op_branch_sanxing_geometry",
                "plugin_id": "l1.physics.op_branch_sanxing",
                "source": "l1.physics.op_branch_sanxing",
                "title": title,
                "label": label,
                "hint": label,
                "priority": float((hits.get("l1.physics.op_branch_sanxing") or {}).get("priority", 0.71) or 0.71),
                "target_god": target_god,
                "physical_impact": {
                    "target_god": target_god,
                    "impact_ratio": -0.10,
                    "significance_level": "L3",
                    "significance_weight": 1.0,
                    "intensity_level": 3,
                    "resistance_mod": {"path": "auto_clash", "factor": 0.45},
                },
            }
        )
    return rows

def _get_god_to_element_map(dm: str) -> Dict[str, str]:
    _god_to_el = {}
    _dm_el = STEM_ELEMENT.get(dm, "")
    if _dm_el in ELEMENT_CYCLE:
        dm_idx = ELEMENT_CYCLE.index(_dm_el)
        for idx in [0, 1, 2, 3, 4]:
            el = ELEMENT_CYCLE[(dm_idx + idx) % 5]
            names = ["比肩", "劫财"] if idx == 0 else \
                    ["食神", "伤官"] if idx == 1 else \
                    ["正财", "偏财"] if idx == 2 else \
                    ["正官", "七杀"] if idx == 3 else \
                    ["正印", "偏印"]
            for n in names: _god_to_el[n] = el
    return _god_to_el

def hydrate_v17_physics_tensor(pt: Dict[str, Any]) -> None:
    if not isinstance(pt, dict): return
    meta = pt.get("meta", {})
    if not isinstance(meta, dict):
        meta = {}
    pt["meta"] = meta
    if meta.get("_v17_hydrated"): return

    # 1. 地支/天干几何关系检测 (Pure Geometry)
    branches, stems = branches_and_stems_from_four_pillars(pt.get("four_pillars"))
    _fp = pt.get("four_pillars") if isinstance(pt.get("four_pillars"), dict) else {}
    _day_gz = str(_fp.get("day", "")).strip()
    _daymaster = _day_gz[0] if len(_day_gz) >= 2 else "壬"
    
    liu_chong = eval_liu_chong_hits(branches) if branches else []
    liu_hai = eval_liu_hai_hits(branches) if branches else []
    liu_he = eval_liuhe_hits(branches) if branches else []
    san_he = eval_sanhe_hits(branches) if branches else []
    ban_he = eval_banhe_hits(branches) if branches else []
    an_he = eval_anhe_hits(branches) if branches else []
    sanxing_geo = sanxing_detect_geometry(branches) if branches else []
    stem_cases = detect_stem_fusion_cases(stems, branches) if stems else []

    # 2. 填充 interaction_v2 (用于插件探测源)
    meta["interaction_v2"] = {
        "version": "interaction_v2.v1",
        "liu_chong": [{"pair": h.get("pair"), "pillars": h.get("pillars")} for h in liu_chong],
        "liu_hai": [{"pair": h.get("pair"), "pillars": h.get("pillars")} for h in liu_hai],
        "liu_he": [{"pair": h.get("pair"), "pillars": h.get("pillars")} for h in liu_he],
        "san_he": [{"group": h.get("group"), "pillars": h.get("pillars")} for h in san_he],
        "ban_he": [{"pair": h.get("pair"), "pillars": h.get("pillars")} for h in ban_he],
        "an_he": [{"pair": h.get("pair"), "pillars": h.get("pillars")} for h in an_he],
        "sanxing": [{"branches": h.get("branches"), "edge": h.get("edge")} for h in sanxing_geo],
    }

    # 3. 填充基础 Hits (Legacy Admin UI 兼容)
    hits = {}
    if liu_chong: _register_manifest_hit(hits, "l1.physics.op_branch_liuchong", "", "六冲", 0.72)
    if san_he: _register_manifest_hit(hits, "l1.physics.op_branch_sanhe", "", "三合成局", 0.76)
    if liu_hai: _register_manifest_hit(hits, "l1.physics.op_branch_liuhai", "", "六害", 0.7)
    if sanxing_geo: _register_manifest_hit(hits, "l1.physics.op_branch_sanxing", "", "三刑", 0.71)

    # 4. 插件周期演化 (Plugin Lifecycle Loop)
    deity_scores = pt.get("ten_gods_absolute") or pt.get("deity_scores") or {}
    _absolute = dict(deity_scores)
    _energy_meta = pt.get("energy_meta", {})
    _ledger = _energy_meta.get("ledger")

    from v17_rebirth.backend.logic.plugin_discovery import iter_all_plugin_specs
    all_specs = iter_all_plugin_specs()
    
    pt.setdefault("facts", [])
    pt.setdefault("pending_decisions", [])
    collected_facts = []
    existing_pending = pt.get("pending_decisions") if isinstance(pt.get("pending_decisions"), list) else []
    
    for spec in all_specs:
        facts = spec.collect_v17_facts(pt)
        if not facts: continue
        collected_facts.extend(facts)
        
        # 将事实注入全局列表，供叙事引擎使用；保持 JSON-safe dict 形态
        pt.setdefault("facts", []).extend(
            {
                "fact": str(f.text or "").strip(),
                "weight": float(f.salience_weight or 0.0),
                "tier": int(f.causal_tier or 0),
                "plugin": str(f.plugin_id or "").strip(),
            }
            for f in facts
            if str(f.text or "").strip()
        )
        
        if spec.plugin_id in hits:
            hits[spec.plugin_id]["activated"] = True
            hits[spec.plugin_id]["last_facts"] = [f.text for f in facts]
        
        for f in facts:
            # 2. 注入物理能级影响 (Impact Application)
            impact = f.meta.get("impact_ratio") if isinstance(f.meta, dict) else None
            target = f.meta.get("target_god") if isinstance(f.meta, dict) else None
            if impact and target and target in _absolute:
                _absolute[target] = round(_absolute[target] * (1 + impact), 2)
                
                # 关键同步：确保 L2 插件能看到 L1 的变动
                pt["ten_gods_absolute"] = _absolute
                
                if _ledger:
                    _ledger.append_entry(target, _absolute[target], f"L{spec.causal_tier}_PLUGIN", f"{spec.plugin_id}: {f.text}")

    # 4.5 单一入口：将插件碰撞结果统一编译为 pending_decisions
    pt["pending_decisions"] = compile_pending_decisions(
        facts=collected_facts,
        spec_decisions=collect_pending_decisions_from_specs(collected_facts),
        existing_rows=[
            *[dict(item) for item in existing_pending if isinstance(item, dict)],
            *_manifest_hits_to_decision_rows(hits),
            *_geometry_hits_to_decision_rows(pt, hits),
        ],
        physics_tensor=pt,
    )

    # 5. 物理引擎结算 (Stress & Flow)
    stress_map = build_clash_stress_map(
        daymaster=_daymaster,
        branches=branches,
        ten_gods_absolute=_absolute,
        interaction_v2=meta["interaction_v2"],
    )
    meta["clash_stress_map"] = stress_map
    boost_high_stress_facts(hits, stress_map)

    if pt.get("_is_current_focus", True):
        g2e = _get_god_to_element_map(_daymaster)
        dm_el = STEM_ELEMENT.get(_daymaster, "")
        engine = FlowPhysicsEngine(dm_el)
        flow_result = engine.compute_flow(ten_gods_absolute=_absolute, clash_stress_map=stress_map, ten_god_to_el=g2e)
        for god, dq in flow_result.get("ten_god_deltas", {}).items():
            if abs(dq) > 0.001 and god in _absolute:
                _absolute[god] = round(_absolute[god] + dq, 2)
                if _ledger:
                    _ledger.append_entry(god, _absolute[god], "L1.5_FLOW", "内生系统平衡流转")
        meta["flow_topology"] = flow_result["topology"]

    # 6. Action Impact & Will Proxy
    _decisions = pt.get("pending_decisions", [])
    for d in _decisions:
        if isinstance(d, dict) and d.get("applied"):
            impact = d.get("physical_impact", {})
            tg = d.get("target_god")
            if tg in _absolute:
                ratio = float(impact.get("impact_ratio", 0.15)) * float(impact.get("significance_weight", 1.0))
                _absolute[tg] = round(_absolute[tg] * (1.0 + ratio), 2)
                if _ledger:
                    _ledger.append_entry(tg, _absolute[tg], "L2_ACTION", f"决策生效: {d.get('title')}")

    _will = pt.get("will_proxy", "stable")
    if _will == "stable":
        for g in ["正官", "七杀", "正印", "偏印", "比肩", "劫财"]:
            if g in _absolute: _absolute[g] = round(_absolute[g] * 1.15, 2)
    elif _will == "aggressive":
        for g in ["食神", "伤官", "正财", "偏财"]:
            if g in _absolute: _absolute[g] = round(_absolute[g] * 1.25, 2)

    # 7. 终效同步与清理
    pt["ten_gods_absolute"] = _absolute
    pt["ten_gods_absolute_intensity"] = _absolute
    pt["deity_scores"] = _absolute
    meta["l1_manifest_hits"] = hits
    meta["_v17_hydrated"] = True

    if _ledger:
        pt["ten_gods_ledger"] = _ledger.to_dict()
        if "ledger" in _energy_meta: del _energy_meta["ledger"]

    # 最终类型擦除，防止 JSON 报错
    import json
    tmp = json.loads(json.dumps(pt, default=str))
    pt.clear()
    pt.update(tmp)
