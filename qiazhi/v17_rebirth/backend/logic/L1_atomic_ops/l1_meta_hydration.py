"""
V17.13：将四柱地支/天干几何判定写入 physics_tensor.meta，驱动 ManifestOperatorPlugin 从占位 → 命中。
"""
from __future__ import annotations

from typing import Any, Dict, List

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
    build_clash_stress_map,
    boost_high_stress_facts,
)
from v17_rebirth.backend.logic.L0_physics_fields.flow_physics_engine import FlowPhysicsEngine
from v17_rebirth.backend.logic.L1_atomic_ops.v17_op_fact import generate_v17_fact_from_op
from v17_rebirth.backend.logic.L0_physics_fields.ten_gods_engine import (
    STEM_ELEMENT,
    ten_god_from_stems,
)


def _scalar_intensity(count: int, *, per: float = 0.36, bump: float = 0.09) -> float:
    """冲/害/破等：条数越多烈度越高，上限 1.0（内部标量，不上屏为 Abs）。"""
    if count <= 0:
        return 0.0
    return min(1.0, per * count + max(0, count - 1) * bump)


def _tier_cn(x: float) -> str:
    if x >= 0.72:
        return "猛"
    if x >= 0.38:
        return "中"
    if x <= 1e-9:
        return "无"
    return "轻"


def _sanxing_intensity(n_edges: int, branches_present: set[str]) -> float:
    if n_edges <= 0:
        return 0.0
    trip = all(b in branches_present for b in ("寅", "巳", "申"))
    base = min(1.0, 0.26 * n_edges + (0.34 if trip else 0.0))
    return min(1.0, base + (0.18 if n_edges >= 3 else 0.0))


def _pair_labels(hits: List[Dict[str, Any]]) -> List[str]:
    out: List[str] = []
    for h in hits:
        pr = h.get("pair")
        if isinstance(pr, list) and len(pr) >= 2:
            out.append(f"{pr[0]}{pr[1]}")
    return out


def _group_labels(hits: List[Dict[str, Any]], key: str = "group") -> List[str]:
    out: List[str] = []
    for h in hits:
        rows = h.get(key)
        if isinstance(rows, list) and rows:
            out.append("".join(str(x) for x in rows))
    return out


def _muku_branches(branches: Dict[str, str]) -> List[str]:
    return sorted({str(br) for br in branches.values() if str(br) in {"辰", "戌", "丑", "未"}})


def _status_snapshot(deity_scores: Dict[str, Any], total_energy_index: float) -> Dict[str, Any]:
    if not deity_scores:
        return {}
    try:
        ranked = sorted(
            ((str(k), float(v)) for k, v in deity_scores.items() if str(k).strip()),
            key=lambda kv: kv[1],
            reverse=True,
        )
    except (TypeError, ValueError):
        return {}
    if not ranked:
        return {}
    top_name, top_score = ranked[0]
    if total_energy_index >= 120:
        phase = "帝旺"
    elif total_energy_index >= 85:
        phase = "临官"
    elif total_energy_index >= 55:
        phase = "冠带"
    elif total_energy_index >= 28:
        phase = "墓"
    else:
        phase = "绝"
    return {"phase": phase, "top_name": top_name, "top_score": round(top_score, 2)}


def _register_manifest_hit(
    hits: Dict[str, Dict[str, Any]],
    *,
    plugin_id: str,
    fact: str,
    label: str,
    priority: float,
    evidence: Dict[str, Any] | None = None,
) -> None:
    hits[plugin_id] = {
        "fact": str(fact or "").strip(),
        "label": str(label or "").strip(),
        "priority": float(priority or 0.0),
        "framework_standard": "v17_manifest_unified",
        "hit_source": "l1_meta_hydration",
        "evidence": dict(evidence or {}),
    }


def hydrate_v17_physics_tensor(pt: Dict[str, Any]) -> None:
    """幂等：向 pt.meta 写入 interaction_v2 / l1_manifest_hits / L2 辅助键。"""
    if not isinstance(pt, dict):
        return
    meta = pt.get("meta")
    if isinstance(meta, dict) and meta.get("_v17_hydrated"):
        meta.setdefault("v17_physics_stable", True)
        return

    branches, stems = branches_and_stems_from_four_pillars(pt.get("four_pillars"))
    liu_chong = eval_liu_chong_hits(branches) if branches else []
    liu_hai = eval_liu_hai_hits(branches) if branches else []
    liu_po = eval_liu_po_hits(branches) if branches else []
    liu_he = eval_liuhe_hits(branches) if branches else []
    an_he = eval_anhe_hits(branches) if branches else []
    ban_he = eval_banhe_hits(branches) if branches else []
    san_he = eval_sanhe_hits(branches) if branches else []
    sanxing_geo = sanxing_detect_geometry(branches) if branches else []
    stem_cases = detect_stem_fusion_cases(stems, branches) if stems else []

    meta = pt.setdefault("meta", {})
    if not isinstance(meta, dict):
        return

    meta["interaction_v2"] = {
        "version": "interaction_v2.v1",
        "liu_chong": [{"pair": h.get("pair"), "pillars": h.get("pillars")} for h in liu_chong],
        "liu_hai": [{"pair": h.get("pair"), "pillars": h.get("pillars")} for h in liu_hai],
        "liu_po": [{"pair": h.get("pair"), "pillars": h.get("pillars")} for h in liu_po],
        "liu_he": [{"pair": h.get("pair"), "pillars": h.get("pillars")} for h in liu_he],
        "an_he": [{"pair": h.get("pair"), "pillars": h.get("pillars")} for h in an_he],
        "ban_he": [{"pair": h.get("pair"), "pillars": h.get("pillars")} for h in ban_he],
        "san_he": [{"group": h.get("group"), "pillars": h.get("pillars")} for h in san_he],
        "sanxing": [{"branches": h.get("branches"), "edge": h.get("edge")} for h in sanxing_geo],
    }

    meta["stem_fusion_v1"] = {
        "version": "stem_fusion.v1",
        "cases": stem_cases,
        "has_stuck": any(str(c.get("mode")) == "stuck" for c in stem_cases),
        "has_transform": any(str(c.get("mode")) == "transformed" for c in stem_cases),
    }

    br_set = {str(b) for b in branches.values() if b}
    ch_i = _scalar_intensity(len(liu_chong), per=0.39, bump=0.11)
    hai_i = _scalar_intensity(len(liu_hai), per=0.33, bump=0.07)
    po_i = _scalar_intensity(len(liu_po), per=0.33, bump=0.07)
    he_i = _scalar_intensity(len(liu_he), per=0.28, bump=0.05)
    ban_i = _scalar_intensity(len(ban_he), per=0.3, bump=0.06)
    sx_i = _sanxing_intensity(len(sanxing_geo), br_set)
    stem_i = _scalar_intensity(len(stem_cases), per=0.31, bump=0.04)

    pt["interaction_delta"] = {
        "version": "l1_delta.v2",
        "n_liu_chong": len(liu_chong),
        "n_liu_hai": len(liu_hai),
        "n_liu_po": len(liu_po),
        "n_liu_he": len(liu_he),
        "n_ban_he": len(ban_he),
        "n_sanxing_edges": len(sanxing_geo),
        "n_stem_fusion_cases": len(stem_cases),
        "chong_intensity": round(ch_i, 4),
        "chong_tier": _tier_cn(ch_i),
        "sanxing_intensity": round(sx_i, 4),
        "sanxing_tier": _tier_cn(sx_i),
        "hai_intensity": round(hai_i, 4),
        "hai_tier": _tier_cn(hai_i),
        "po_intensity": round(po_i, 4),
        "po_tier": _tier_cn(po_i),
        "he_intensity": round(he_i, 4),
        "he_tier": _tier_cn(he_i),
        "ban_he_intensity": round(ban_i, 4),
        "ban_he_tier": _tier_cn(ban_i),
        "stem_fusion_intensity": round(stem_i, 4),
        "stem_fusion_tier": _tier_cn(stem_i),
        "yin_si_shen_complete": all(b in br_set for b in ("寅", "巳", "申")),
    }

    hits: Dict[str, Dict[str, Any]] = {}

    if liu_chong:
        labs = _pair_labels(liu_chong)
        _register_manifest_hit(
            hits,
            plugin_id="l1.physics.op_branch_liuchong",
            fact=generate_v17_fact_from_op(kind="liu_chong", detail="".join(labs)),
            label="六冲",
            priority=0.72,
            evidence={"pairs": labs},
        )

    if sanxing_geo:
        sx = summarize_sanxing_branches(sanxing_geo)
        _register_manifest_hit(
            hits,
            plugin_id="l1.physics.op_branch_sanxing",
            fact=generate_v17_fact_from_op(kind="sanxing", branches=[sx] if sx else []),
            label="三刑",
            priority=0.71,
            evidence={"branches": [sx] if sx else []},
        )

    if liu_hai:
        labs = _pair_labels(liu_hai)
        _register_manifest_hit(
            hits,
            plugin_id="l1.physics.op_branch_liuhai",
            fact=generate_v17_fact_from_op(kind="liu_hai", detail="".join(labs)),
            label="六害",
            priority=0.7,
            evidence={"pairs": labs},
        )

    if liu_po:
        labs = _pair_labels(liu_po)
        _register_manifest_hit(
            hits,
            plugin_id="l1.physics.op_branch_liupo",
            fact=generate_v17_fact_from_op(kind="liu_po", detail="".join(labs)),
            label="六破",
            priority=0.69,
            evidence={"pairs": labs},
        )

    if liu_he:
        labs = _pair_labels(liu_he)
        _register_manifest_hit(
            hits,
            plugin_id="l1.physics.op_branch_liuhe",
            fact=generate_v17_fact_from_op(kind="liu_he", detail="".join(labs)),
            label="六合",
            priority=0.68,
            evidence={"pairs": labs},
        )

    if san_he:
        groups = _group_labels(san_he)
        _register_manifest_hit(
            hits,
            plugin_id="l1.physics.op_branch_sanhe",
            fact=generate_v17_fact_from_op(kind="sanhe", detail="、".join(groups)),
            label="三合成局",
            priority=0.76,
            evidence={"groups": groups},
        )

    if ban_he:
        labs = _pair_labels(ban_he)
        _register_manifest_hit(
            hits,
            plugin_id="l1.physics.op_branch_banhe",
            fact=generate_v17_fact_from_op(kind="ban_he", detail="、".join(labs)),
            label="半合聚势",
            priority=0.75,
            evidence={"pairs": labs},
        )

    if an_he:
        labs = _pair_labels(an_he)
        _register_manifest_hit(
            hits,
            plugin_id="l1.physics.op_branch_anhe",
            fact=generate_v17_fact_from_op(kind="an_he", detail="、".join(labs)),
            label="暗合潜线",
            priority=0.74,
            evidence={"pairs": labs},
        )

    for c in stem_cases:
        mode = str(c.get("mode") or "")
        sa, sb = (c.get("stems") or ["", ""])[:2]
        hua = str(c.get("hua_element") or "")
        detail = f"{sa}{sb}→{hua}" if hua else f"{sa}{sb}"
        if mode == "stuck":
            pid = "l1.physics.op_stem_fusion_stuck"
            if pid not in hits:
                _register_manifest_hit(
                    hits,
                    plugin_id=pid,
                    fact=generate_v17_fact_from_op(kind="stem_stuck", detail=detail),
                    label="天干羁绊",
                    priority=0.67,
                    evidence={"detail": detail, "mode": mode},
                )
        elif mode == "transformed":
            pid = "l1.physics.op_stem_fusion_transform"
            if pid not in hits:
                _register_manifest_hit(
                    hits,
                    plugin_id=pid,
                    fact=generate_v17_fact_from_op(kind="stem_transform", detail=detail),
                    label="天干化气",
                    priority=0.66,
                    evidence={"detail": detail, "mode": mode},
                )

    muku = _muku_branches(branches)
    if muku:
        _register_manifest_hit(
            hits,
            plugin_id="l1.physics.op_branch_muku",
            fact=generate_v17_fact_from_op(kind="muku", detail="、".join(muku)),
            label="墓库门态",
            priority=0.73,
            evidence={"branches": muku},
        )

    deity_scores = (
        pt.get("ten_gods_absolute")
        or pt.get("ten_gods_absolute_intensity")
        or pt.get("deity_scores")
    )
    status = _status_snapshot(
        deity_scores if isinstance(deity_scores, dict) else {},
        float(pt.get("total_energy_index") or 0.0),
    )
    if status:
        _register_manifest_hit(
            hits,
            plugin_id="l1.physics.op_status",
            fact=generate_v17_fact_from_op(
                kind="status",
                detail=f"{status['phase']}·{status['top_name']}",
            ),
            label="状态机节律",
            priority=0.79,
            evidence=status,
        )
        meta["l1_status_v1"] = status

    # ── V17.31：矢量冲突应力引擎 ──
    # 从四柱提取日主，计算各柱位关系对的矢量应力
    _fp = pt.get("four_pillars") if isinstance(pt.get("four_pillars"), dict) else {}
    _day_gz = str(_fp.get("day", "")).strip()
    _daymaster = _day_gz[0] if len(_day_gz) >= 2 else ""
    _absolute = deity_scores if isinstance(deity_scores, dict) else {}
    _iv2 = meta.get("interaction_v2") if isinstance(meta.get("interaction_v2"), dict) else {}
    
    # 获取演化账本对象
    _energy_meta = pt.get("energy_meta") if isinstance(pt.get("energy_meta"), dict) else {}
    _ledger = _energy_meta.get("ledger")

    if _daymaster and branches and _absolute and _iv2:
        stress_map = build_clash_stress_map(
            daymaster=_daymaster,
            branches=branches,
            ten_gods_absolute=_absolute,
            interaction_v2=_iv2,
        )
        meta["clash_stress_map"] = stress_map
        # 将前 5 个最高应力事件的 Fact 权重提升至 Tier 0 (0.95)
        boost_high_stress_facts(hits, stress_map)
        
        # ── V17.33：执行能量回写 (SettlementCenter) ──
        # 将应力转化为数值增量并注入 L0 absolute 分数
        _deltas_map = {}
        for ev in stress_map.get("events", []):
            rel_type = ev.get("relation_type", "unknown")
            dq_god_i = 0.0
            dq_god_j = 0.0
            
            # 使用校准后的 Alpha
            from v17_rebirth.backend.logic.L0_physics_fields.vector_physics_engine import ALPHA_CLASH, ALPHA_COMBINATION, ALPHA_HARM
            f_damped = ev.get("damped_stress", 0.0)
            if rel_type == "combination":
                dq = abs(f_damped) * ALPHA_COMBINATION
            elif rel_type == "clash":
                dq = f_damped * ALPHA_CLASH
            else:
                dq = f_damped * ALPHA_HARM
                
            god_i, god_j = ev.get("god_i"), ev.get("god_j")
            if god_i and god_j:
                _absolute[god_i] = round(_absolute.get(god_i, 0.0) + dq / 2, 2)
                _absolute[god_j] = round(_absolute.get(god_j, 0.0) + dq / 2, 2)
                
                if _ledger:
                    from v17_rebirth.backend.logic.L0_physics_fields.evolution_ledger import EvolutionLedger
                    if isinstance(_ledger, EvolutionLedger):
                        reason = f"Interaction: {rel_type} ({ev.get('pillars', [])})"
        # ── V17.50：建立映射并执行时间分片流转 ──
        from v17_rebirth.backend.logic.L0_physics_fields.ten_gods_engine import STEM_ELEMENT, ELEMENT_CYCLE
        _god_to_el = {}
        _dm_el = STEM_ELEMENT.get(_daymaster, "")
        if _dm_el in ELEMENT_CYCLE:
            dm_idx = ELEMENT_CYCLE.index(_dm_el)
            for idx in [0, 1, 2, 3, 4]:
                el = ELEMENT_CYCLE[(dm_idx + idx) % 5]
                if idx == 0: names = ["比肩", "劫财"]
                elif idx == 1: names = ["食神", "伤官"]
                elif idx == 2: names = ["正财", "偏财"]
                elif idx == 3: names = ["正官", "七杀"]
                else: names = ["正印", "偏印"]
                for n in names: _god_to_el[n] = el

        if pt.get("_is_current_focus", True):
            from v17_rebirth.backend.logic.L0_physics_fields.flow_physics_engine import FlowPhysicsEngine
            engine = FlowPhysicsEngine(_dm_el)
            flow_result = engine.compute_flow(
                ten_gods_absolute=_absolute,
                clash_stress_map=stress_map,
                ten_god_to_el=_god_to_el
            )
            
            _flow_deltas = flow_result.get("ten_god_deltas", {})
            for god, dq in _flow_deltas.items():
                if abs(dq) > 0.001 and god in _absolute:
                    _absolute[god] = round(_absolute[god] + dq, 2)
                    if _ledger:
                        reason = "五行内生系统平衡流转"
                        _ledger.append_entry(god, _absolute[god], "L1.5_FLOW_SETTLEMENT", reason)
            
            # 将流向拓扑图存入 meta，供前端展示
            meta["flow_topology"] = flow_result["topology"]
        else:
            _log.debug("[V17-FLOW] Skipping non-focused temporal shard")

        # ── V17.36：执行动作反馈 (Action Impact Loop) ──
        # 检测用户选中的决策项并产生物理反馈
        _decisions = pt.get("pending_decisions", [])
        _applied_count = 0
        for d in _decisions:
            if isinstance(d, dict) and d.get("applied") is True:
                impact = d.get("physical_impact") if isinstance(d.get("physical_impact"), dict) else {}
                _target_god = d.get("target_god") or list(_absolute.keys())[0] if _absolute else None
                if _target_god and _target_god in _absolute:
                    _impact_ratio = float(impact.get("impact_ratio", 0.15) or 0.15)
                    _significance_weight = float(impact.get("significance_weight", 1.0) or 1.0)
                    _ratio_applied = _impact_ratio * _significance_weight
                    _before = _absolute[_target_god]
                    _absolute[_target_god] = round(_before * (1.0 + _ratio_applied), 2)
                    _applied_count += 1
                    if _ledger:
                        reason = f"决策生效: [{d.get('title')}] 导致能级提升"
                        _ledger.append_entry(
                            _target_god,
                            _absolute[_target_god],
                            "L2_ACTION_IMPACT",
                            reason,
                            source="SRC_MANUAL",
                        )
        
        # ── V17.37：源头清理 (Source-Level Sanitization) ──
        # 在 Hydration 结束前，必须将 EvolutionLedger 对象转为纯 JSON 数据
        # 否则下游 (LLM Prompt Builder / Redis Sync) 会因为无法序列化而崩溃
        if _ledger:
            from v17_rebirth.backend.logic.L0_physics_fields.evolution_ledger import EvolutionLedger
            if isinstance(_ledger, EvolutionLedger):
                # 1. 导出数据
                pt["ten_gods_ledger"] = _ledger.to_dict()
                # 2. 从物理张量中彻底移除原始对象引用
                if "ledger" in _energy_meta:
                    del _energy_meta["ledger"]
        
        # ── V17.50：时间分片逻辑 (Temporal Sharding) ──
        # 仅对当前焦点时间（当前大运/流年）执行基尔霍夫结算
        # 历史年份快照仅保留 L0 静态值，不参与实时流转动态重平衡
        if pt.get("_is_current_focus", True):
            # ... 此处是 L1.5_FLOW_SETTLEMENT ... (逻辑已在上方，此处确保 pt 被返回)
            pass

        # ── V17.50：万能类型擦除 (Type Erasure) ──
        # 处理电路模型可能产出的 np.float64, Decimal 等非标准类型
        def _safe_json_dump(obj):
            import json
            try:
                return json.loads(json.dumps(obj, default=str))
            except Exception:
                return obj

        pt["total_energy_index"] = round(sum(_absolute.values()), 2)
        pt = _safe_json_dump(pt)

    meta["l1_manifest_hits"] = hits
    meta["_v17_hydrated"] = True
    meta["v17_physics_stable"] = True
    return pt


def _resolve_pattern_label(deity_scores: Dict[str, Any]) -> str:
    if not deity_scores:
        return "未定格局"
    try:
        ranked = sorted(
            ((str(k), float(v)) for k, v in deity_scores.items()),
            key=lambda kv: kv[1],
            reverse=True,
        )
    except (TypeError, ValueError):
        return "未定格局"
    if not ranked:
        return "未定格局"
    name, score = ranked[0]
    if name == "正官" and score >= 40:
        return "正官格势强"
    if name in {"食神", "伤官"} and score >= 35:
        return "食伤外放格"
    if name in {"偏财", "正财"} and score >= 35:
        return "财星主导格"
    return f"{name}主轴格"


def _blind_work_hint(
    _branches: Dict[str, str],
    sanxing: List[Dict[str, Any]],
    chong: List[Dict[str, Any]],
) -> str:
    """极简盲派做功提示：三刑聚势 / 冲动做功。"""
    sx = summarize_sanxing_branches(sanxing)
    if sx and all(x in sx for x in ("寅", "巳", "申")):
        return "无恩三刑聚势"
    if chong:
        return "支冲牵动做功"
    return ""


def _get_god_to_element_map(day_master: str = "壬") -> Dict[str, str]:
    """返回十神到五行的映射（用于 KCL 结算）。"""
    from v17_rebirth.backend.logic.L0_physics_fields.ten_gods_engine import (
        STEM_ELEMENT,
        ten_god_from_stems,
    )
    # 构造所有天干及其对应十神
    stems = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
    mapping = {}
    for s in stems:
        god = ten_god_from_stems(day_master, s)
        el = STEM_ELEMENT[s]
        mapping[god] = el
    return mapping
