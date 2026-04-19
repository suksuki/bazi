"""
V17.99：物理水分抽取层（Hydration Hub）。
负责将 L0 静态数据转化为 L1+ 动态张量，并统一执行插件生命周期。
"""
from __future__ import annotations
import logging
import math
from v17_rebirth.backend.infrastructure.evolution_db import evolution_storage
from typing import Any, Dict, List, Tuple

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
from v17_rebirth.backend.services.claim_protocol import CLAIM_JSON_SCHEMA, compile_claims
from v17_rebirth.backend.services.conflict_detector import detect_claim_conflicts, recommend_conflict_resolutions
from v17_rebirth.backend.services.knowledge_store import build_knowledge_snapshot
from v17_rebirth.backend.services.arbiter_router import route_conflicts
from v17_rebirth.backend.services.decision_compiler import compile_modifier_proposals, compile_pending_decisions
from v17_rebirth.backend.services.physics_layers import proposal_signature, read_base_scores, read_runtime_scores, settle_modifier_proposals, sync_runtime_aliases

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
        "framework_standard": "v17_manifest_unified",
        "hit_source": "l1_meta_hydration",
        "activated": True, # V17.99: 强制激活，进入裁决视野
        "last_facts": [fact] if fact else []
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


def _normalize_claim_id(raw: Any) -> str:
    value = str(raw or "").strip()
    return value if value else ""


def _normalize_winner_claim_ids(row: Dict[str, Any]) -> List[str]:
    winners: List[str] = []
    for value in row.get("winner_claim_ids") or []:
        winner = _normalize_claim_id(value)
        if winner:
            winners.append(winner)
    if not winners:
        winner = _normalize_claim_id(row.get("winner_claim_id"))
        if winner:
            winners.append(winner)
    return winners


def _extract_claims_resolution_plan(
    *,
    claim_rows: List[Dict[str, Any]],
    conflict_resolutions: List[Dict[str, Any]],
    current_proposals: List[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    claim_index: Dict[str, Dict[str, Any]] = {}
    for row in claim_rows:
        if not isinstance(row, dict):
            continue
        cid = _normalize_claim_id(row.get("claim_id"))
        if not cid:
            continue
        claim_index[cid] = row

    dropped_claim_ids: set[str] = set()
    approved_winners: set[str] = set()
    for resolution in conflict_resolutions:
        if not bool(resolution.get("applied_to_settlement")):
            continue
        if str(resolution.get("resolved_by") or "").strip().lower() != "system":
            continue
        if str(resolution.get("status") or "").strip() not in {"approved", "resolved_system"}:
            continue
        winners = _normalize_winner_claim_ids(resolution)
        conflict_claims = [
            _normalize_claim_id(value)
            for value in (resolution.get("claims") or [])
            if _normalize_claim_id(value)
        ]
        dropped = [
            _normalize_claim_id(value)
            for value in (resolution.get("dropped_claim_ids") or [])
            if _normalize_claim_id(value)
        ]
        if not winners and conflict_claims:
            winners = [cid for cid in conflict_claims if cid not in dropped]

        if winners:
            approved_winners.update(winners)

        if conflict_claims:
            dropped_claim_ids.update(cid for cid in conflict_claims if cid not in set(winners))
        dropped_claim_ids.update(dropped)

    resolved_proposal_by_id: Dict[str, Dict[str, Any]] = {}
    for row in current_proposals:
        cid = _normalize_claim_id(row.get("claim_id"))
        if cid:
            resolved_proposal_by_id[cid] = dict(row)
    filtered = [
        row
        for row in current_proposals
        if _normalize_claim_id(row.get("claim_id")) not in dropped_claim_ids
    ]

    synthetic: List[Dict[str, Any]] = []
    for winner_id in sorted(approved_winners):
        if winner_id in dropped_claim_ids:
            continue
        existing = resolved_proposal_by_id.get(winner_id)
        if existing and str(existing.get("arbiter_type") or "").strip().lower() == "system":
            continue
        claim = claim_index.get(winner_id)
        if not isinstance(claim, dict):
            continue
        target_god = _normalize_claim_id(claim.get("target_god"))
        if not target_god:
            continue
        intent = claim.get("intent_vector")
        if not isinstance(intent, dict):
            continue
        raw_ratio = 0.0
        for key, value in intent.items():
            if str(key or "").strip() != target_god:
                continue
            try:
                raw_ratio = float(value or 0.0)
                break
            except (TypeError, ValueError):
                raw_ratio = 0.0
                break
        if not raw_ratio:
            continue
        synthetic.append(
            {
                "id": f"conflict:{winner_id}",
                "claim_id": winner_id,
                "plugin_id": str(claim.get("plugin_id") or "conflict_resolver").strip(),
                "title": str(claim.get("claim_text") or "").strip(),
                "reason": f"冲突裁决优先保留：{winner_id}",
                "target_god": target_god,
                "impact_ratio": raw_ratio,
                "significance_weight": 1.0,
                "arbiter_type": "system",
                "causal_tier": 4,
            }
        )

    return filtered + synthetic, {
        "resolved_conflict_settlement": {
            "applied_resolution_count": len([r for r in conflict_resolutions if bool(r.get("applied_to_settlement"))]),
            "dropped_claim_count": len(dropped_claim_ids),
            "winner_claim_count": len(approved_winners),
            "synthetic_proposal_count": len(synthetic),
        }
    }


def _build_plugin_execution_statuses(
    *,
    facts: List[Any],
    proposals: List[Dict[str, Any]],
    previous_signatures: List[str],
    clamped_gods: List[str],
) -> List[Dict[str, Any]]:
    facts_by_plugin: Dict[str, int] = {}
    for fact in facts:
        pid = str(getattr(fact, "plugin_id", "") or "").strip()
        if not pid:
            continue
        facts_by_plugin[pid] = facts_by_plugin.get(pid, 0) + 1

    proposals_by_plugin: Dict[str, List[Dict[str, Any]]] = {}
    for proposal in proposals:
        pid = str(proposal.get("plugin_id") or "").strip()
        if not pid:
            continue
        proposals_by_plugin.setdefault(pid, []).append(dict(proposal))

    prev_set = {str(x).strip() for x in previous_signatures if str(x).strip()}
    clamped_set = {str(x).strip() for x in clamped_gods if str(x).strip()}
    statuses: List[Dict[str, Any]] = []

    for plugin_id in sorted(set([*facts_by_plugin.keys(), *proposals_by_plugin.keys()])):
        plugin_proposals = proposals_by_plugin.get(plugin_id, [])
        status = "fact_only"
        reason = "插件命中，但未产出可结算的物理 proposal。"
        target_god = ""
        if plugin_proposals:
            target_god = str(plugin_proposals[0].get("target_god") or "").strip()
            system_proposals = [p for p in plugin_proposals if str(p.get("arbiter_type") or "").strip().lower() == "system"]
            pending_proposals = [p for p in plugin_proposals if str(p.get("arbiter_type") or "").strip().lower() != "system"]
            valid_system = [p for p in system_proposals if str(p.get("target_god") or "").strip()]
            deduped_system = [p for p in valid_system if proposal_signature(p) in prev_set]
            fresh_system = [p for p in valid_system if proposal_signature(p) not in prev_set]

            if any(str(p.get("target_god") or "").strip() in clamped_set for p in valid_system):
                status = "clamped"
                reason = "插件已触发自动结算，但目标神位在护栏阶段被钳制。"
            elif fresh_system:
                status = "auto_applied"
                reason = "插件 proposal 已进入自动结算并写入 runtime。"
            elif deduped_system:
                status = "skipped_dedup"
                reason = "插件 proposal 与上一轮签名一致，本轮为防重复结算被跳过。"
            elif system_proposals and not valid_system:
                status = "skipped_no_target"
                reason = "插件产出物理 proposal，但未能解析到合法 target_god。"
            elif pending_proposals:
                status = "proposal_pending"
                reason = "插件 proposal 已生成，但当前需人工或 LLM 仲裁，尚未结算。"

        statuses.append(
            {
                "plugin_id": plugin_id,
                "fact_count": facts_by_plugin.get(plugin_id, 0),
                "proposal_count": len(plugin_proposals),
                "status": status,
                "target_god": target_god,
                "reason": reason,
            }
        )

    return statuses

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
    muku_hits = [b for b in branches.values() if b in {"辰", "戌", "丑", "未"}] if branches else []
    sanxing_geo = sanxing_detect_geometry(branches) if branches else []
    stem_cases = detect_stem_fusion_cases(stems, branches) if stems else []

    # 2. 填充 interaction_v2 (用于插件探测源)
    geom_data = {
        "version": "interaction_v2.v1",
        "liu_chong": [{"pair": h.get("pair"), "pillars": h.get("pillars")} for h in liu_chong],
        "liu_hai": [{"pair": h.get("pair"), "pillars": h.get("pillars")} for h in liu_hai],
        "liu_he": [{"pair": h.get("pair"), "pillars": h.get("pillars")} for h in liu_he],
        "san_he": [{"group": h.get("group"), "pillars": h.get("pillars")} for h in san_he],
        "ban_he": [{"pair": h.get("pair"), "pillars": h.get("pillars")} for h in ban_he],
        "an_he": [{"pair": h.get("pair"), "pillars": h.get("pillars")} for h in an_he],
        "sanxing": [{"branches": h.get("branches"), "edge": h.get("edge")} for h in sanxing_geo],
    }
    meta["interaction_v2"] = geom_data
    pt["interaction_v2"] = geom_data # 增强型注入
    
    print(f"[V17-HYDRATION-GEOM] Sanhe: {len(san_he)} | Sanxing: {len(sanxing_geo)}")

    # 3. 填充基础 Hits (Legacy Admin UI 兼容)
    hits = {}
    if liu_chong: _register_manifest_hit(hits, "l1.physics.op_branch_liuchong", "", "六冲", 0.72)
    if san_he: _register_manifest_hit(hits, "l1.physics.op_branch_sanhe", "", "三合成局", 0.76)
    if ban_he: _register_manifest_hit(hits, "l1.physics.op_branch_banhe", "", "半合聚势", 0.69)
    if an_he: _register_manifest_hit(hits, "l1.physics.op_branch_anhe", "", "暗合", 0.68)
    if muku_hits: _register_manifest_hit(hits, "l1.physics.op_branch_muku", "", "墓库门态", 0.73, {"branches": muku_hits})
    if liu_hai: _register_manifest_hit(hits, "l1.physics.op_branch_liuhai", "", "六害", 0.7)
    if sanxing_geo: _register_manifest_hit(hits, "l1.physics.op_branch_sanxing", "", "三刑", 0.71)

    # 4. 插件周期演化 (Plugin Lifecycle Loop)
    _active_plugins = []
    collected_facts = []
    
    # Phase 1：拆分基线层与运行态层。
    _base = read_base_scores(pt)
    _runtime = read_runtime_scores(pt)
    if _base:
        pass
    else:
        try:
            from v17_rebirth.backend.logic.L0_physics_fields.ten_gods_engine import calc_deity_scores
            scored, _ten_gods, _total_energy_index, _calc_meta = calc_deity_scores(
                four_pillars=pt.get("four_pillars", {}),
                luck_pillar=pt.get("luck_pillar", ""),
                flow_pillar=pt.get("flow_pillar", ""),
                gender=str(pt.get("gender", "male")),
            )
            _base = {k: float(v) for k, v in scored.items()}
        except Exception as e:
            logging.getLogger("v17").error(f"[V17-HYDRATION-RECOVERY] Critical failure in natal reset: {e}")
            _base = {}
    if not _runtime:
        _runtime = dict(_base)

    # 宇宙常数初级钳制：确保初始基准有限
    for bucket in (_base, _runtime):
        for k in list(bucket.keys()):
            if not math.isfinite(bucket[k]):
                bucket[k] = 10.0

    pt["ten_gods_base_l0"] = dict(_base)
    pt["ten_gods_analysis_input"] = dict(_base)
    pt["ten_gods_runtime"] = dict(_runtime)
    # 插件阶段继续复用兼容字段，但这里强制它们指向 base，避免 runtime 污染分析输入。
    pt["ten_gods_absolute"] = dict(_base)
    pt["deity_scores"] = dict(_base)
    pt["ten_gods_absolute_intensity"] = dict(_base)
    session_id = str(pt.get("session_id", "default_ghost"))
    pt.setdefault("facts", [])
    pt.setdefault("pending_decisions", [])
    
    _energy_meta = pt.get("energy_meta", {})
    _ledger = _energy_meta.get("ledger")

    from v17_rebirth.backend.logic.plugin_discovery import iter_all_plugin_specs
    from v17_rebirth.backend.plugins.spec import ArbiterType, AuditStatus
    all_specs = iter_all_plugin_specs()
    _scanned_pids = [s.plugin_id for s in all_specs]
    print(f"[V17-TRIBUNAL-MANIFEST] Scanned {len(_scanned_pids)}: {', '.join(_scanned_pids)}")
    
    _active_plugins = []
    
    pt.setdefault("facts", [])
    pt.setdefault("pending_decisions", [])
    
    # [V17-PROBE] 关键数据探针
    _scores = pt.get("ten_gods_analysis_input") or {}
    print(f"[V17-PHYSICS-PROBE] pt_keys: {list(pt.keys())} | scores_sample: {list(_scores.keys())[:3]}")
    
    for spec in all_specs:
        try:
            facts = spec.collect_v17_facts(pt)
        except Exception as e:
            print(f"[V17-TRIBUNAL-ERROR] Plugin {spec.plugin_id} CRASHED: {str(e)}")
            continue
            
        if not facts:
            print(f"[V17-TRIBUNAL-SILENT] Plugin {spec.plugin_id} returned no facts. Has ten_gods_analysis_input: {'ten_gods_analysis_input' in pt}")
            continue
            
        _active_plugins.append(spec.plugin_id)
        collected_facts.extend(facts)
        if spec.plugin_id not in hits:
            _register_manifest_hit(hits, spec.plugin_id, "", str(getattr(spec, "plugin_id", "")).strip() or "规则命中", 0.55)
        hits[spec.plugin_id]["activated"] = True
        hits[spec.plugin_id]["last_facts"] = [str(f.text or "").strip() for f in facts if str(f.text or "").strip()]
        if hits[spec.plugin_id]["last_facts"]:
            hits[spec.plugin_id]["fact"] = hits[spec.plugin_id]["last_facts"][0]
        
        # ── V17.99: 裁决分流逻辑 (Tribunal Routing) ──
        for f in facts:
            # 记录基础事实，以便后续 L2+ 插件可见
            pt["facts"].append({
                "fact": str(f.text or "").strip(),
                "weight": float(f.salience_weight or 1.0),
                "tier": int(f.causal_tier or 0),
                "plugin": str(f.plugin_id or spec.plugin_id).strip(),
                "priority": float(f.priority or 0.5)
            })

            # 裁决人裁定
            arbiter = f.suggested_arbiter
            if spec.causal_tier >= 1:
                if arbiter == ArbiterType.SYSTEM:
                    arbiter = ArbiterType.USER
            
            tg = f.target_god or f.meta.get("target_god") or ""
            
            # V17.99: 智脑降级预测 — 绝不允许出现无主物理扰动
            if not tg and isinstance(f.meta, dict) and f.meta.get("impact_ratio"):
                from v17_rebirth.backend.services.target_god_resolver import resolve_target_god
                tg = resolve_target_god(
                    row_target=f.target_god,
                    impact=f.meta,
                    title=f.text,
                    label=f.decision_hint,
                    plugin_id=spec.plugin_id,
                    physics_tensor=pt
                )

            decision = {
                "id": f"{spec.plugin_id}_{len(pt['pending_decisions'])}",
                "plugin_id": spec.plugin_id,
                "title": f.text,
                "label": f.decision_hint or f.text,
                "hint": f.decision_hint or "物理提示",
                "priority": f.priority,
                "target_god": tg,
                "arbiter_type": arbiter.value,
                "status": AuditStatus.PENDING.value,
                "physical_impact": f.meta 
            }
            
            if arbiter == ArbiterType.SYSTEM:
                decision["status"] = AuditStatus.APPROVED.value
            
            # 无论自动与否，均进入案卷库，由后期分桶逻辑分发到 UI 不同栏位
            pt["pending_decisions"].append(decision)
                # 阻塞事实不进入 pt["facts"]，直到下一轮用户 Approve 后被处理

    modifier_proposals = compile_modifier_proposals(facts=collected_facts, physics_tensor=pt)
    claim_rows = compile_claims(facts=collected_facts, physics_tensor=pt)
    raw_conflict_rows = detect_claim_conflicts(claim_rows)
    conflict_resolutions = recommend_conflict_resolutions(claim_rows, raw_conflict_rows)
    knowledge_snapshot = build_knowledge_snapshot(
        claims=claim_rows,
        conflicts=raw_conflict_rows,
        conflict_resolutions=conflict_resolutions,
    )
    conflict_rows = route_conflicts(conflicts=raw_conflict_rows, knowledge_snapshot=knowledge_snapshot)
    adjusted_modifier_proposals, settlement_meta = _extract_claims_resolution_plan(
        claim_rows=claim_rows,
        conflict_resolutions=conflict_resolutions,
        current_proposals=modifier_proposals,
    )
    auto_signatures = sorted(
        proposal_signature(p)
        for p in adjusted_modifier_proposals
        if str(p.get("arbiter_type") or "").strip().lower() == "system"
    )
    previous_signatures = sorted(
        str(x).strip()
        for x in meta.get("plugin_auto_settlement_signatures", [])
        if str(x).strip()
    )

    if auto_signatures != previous_signatures:
        settled_runtime, ratio_totals, applied_rows = settle_modifier_proposals(_runtime, adjusted_modifier_proposals)
        _runtime = settled_runtime
        meta["plugin_auto_ratio_totals"] = ratio_totals
        meta["plugin_auto_settlement_signatures"] = auto_signatures
        for row in applied_rows:
            tg = str(row.get("target_god") or "").strip()
            before = float(row.get("before", 0.0) or 0.0)
            after = float(row.get("after", before) or before)
            ratio_total = float(row.get("ratio_total", 0.0) or 0.0)
            if _ledger:
                _ledger.append_entry(tg, after, "L1_PLUGIN_SETTLEMENT", f"插件统一结算: {ratio_total:+.4f}")
            evolution_storage.log_evolution(
                session_id=session_id,
                ten_god=tg,
                step="L1_PLUGIN_SETTLEMENT",
                old_val=before,
                new_val=after,
                reason=f"插件统一结算 {ratio_total:+.4f}",
                plugin_id="hydration.plugin_settlement",
                fingerprint={"will_proxy": pt.get("will_proxy", "stable")},
            )

    settlement_trace = settlement_meta.get("resolved_conflict_settlement", {})
    meta["plugin_conflict_settlement_meta"] = {
        "conflict_settlement_count": int(settlement_trace.get("applied_resolution_count", 0)),
        "drop_count": int(settlement_trace.get("dropped_claim_count", 0)),
        "winner_count": int(settlement_trace.get("winner_claim_count", 0)),
        "synthetic_count": int(settlement_trace.get("synthetic_proposal_count", 0)),
    }
    meta["plugin_modifier_proposals"] = [dict(p) for p in adjusted_modifier_proposals]
    meta["plugin_claims"] = [dict(c) for c in claim_rows]
    meta["plugin_claim_schema"] = dict(CLAIM_JSON_SCHEMA)
    meta["plugin_conflicts"] = [dict(c) for c in conflict_rows]
    meta["plugin_conflict_resolutions"] = [dict(r) for r in conflict_resolutions]
    meta["knowledge_snapshot"] = dict(knowledge_snapshot)

    _scanned_pids = [s.plugin_id for s in all_specs]

    # 4.5 V17.99: 案卷分选 (Bucketing for UI)
    pt["pending_decisions"].extend([
        *_manifest_hits_to_decision_rows(hits),
        *_geometry_hits_to_decision_rows(pt, hits),
    ])
    _all_decisions = pt.get("pending_decisions", [])
    pt["manual_decisions"] = [d for d in _all_decisions if d.get("arbiter_type", ArbiterType.USER.value) == ArbiterType.USER.value]
    pt["auto_resolutions"] = [d for d in _all_decisions if d.get("arbiter_type") == ArbiterType.SYSTEM.value]
    pt["llm_arbitration_context"] = [d for d in _all_decisions if d.get("arbiter_type") == ArbiterType.LLM.value]
    
    print(f"[V17-TRIBUNAL-DEBUG] Scanned: {len(_scanned_pids)} | Active: {len(_active_plugins)} ({', '.join(_active_plugins)}) | Total: {len(_all_decisions)} | Manual: {len(pt['manual_decisions'])}")

    # 保持向后兼容：pending_decisions 默认展示手动项
    pt["pending_decisions"] = pt["manual_decisions"]
    sync_runtime_aliases(pt, _runtime)

    # 5. 物理引擎结算 (Stress & Flow)
    stress_map = build_clash_stress_map(
        daymaster=_daymaster,
        branches=branches,
        ten_gods_absolute=_runtime,
        interaction_v2=meta["interaction_v2"],
    )
    meta["clash_stress_map"] = stress_map
    boost_high_stress_facts(hits, stress_map)

    if pt.get("_is_current_focus", True):
        g2e = _get_god_to_element_map(_daymaster)
        dm_el = STEM_ELEMENT.get(_daymaster, "")
        engine = FlowPhysicsEngine(dm_el)
        flow_result = engine.compute_flow(ten_gods_absolute=_runtime, clash_stress_map=stress_map, ten_god_to_el=g2e)
        for god, dq in flow_result.get("ten_god_deltas", {}).items():
            if abs(dq) > 0.001 and god in _runtime:
                _runtime[god] = round(_runtime[god] + dq, 2)
                if _ledger:
                    _ledger.append_entry(god, _runtime[god], "L1.5_FLOW", "内生系统平衡流转")
        meta["flow_topology"] = flow_result["topology"]

    # 6. Action Impact & Will Proxy
    _decisions = pt.get("pending_decisions", [])
    for d in _decisions:
        if isinstance(d, dict) and d.get("applied"):
            # 手动裁决的物理后果已经由 PhysicsKernel 固化到当前张量；
            # hydration 只做透传，避免每次快照重复乘算。
            d["impact_committed"] = True

    # V17.99: 宇宙常数终极护栏 (The Final Cosmic Guardrail)
    from v17_rebirth.backend.logic.configs.manager import get_v17_constants
    guardrails = get_v17_constants().get("PHYSICS_GUARDRAILS", {})
    e_min = float(guardrails.get("ENERGY_MIN", 0.1))
    e_max = float(guardrails.get("ENERGY_MAX", 1000.0))
    clamped_gods: List[str] = []

    for tg in list(_runtime.keys()):
        val = _runtime[tg]
        # 强制钳制：[ENERGY_MIN, ENERGY_MAX] 且确保有限性
        if not math.isfinite(val):
            val_clamped = 10.0 # 坏值安全复原
        else:
            val_clamped = max(e_min, min(e_max, val))
        if round(val_clamped, 2) != round(val, 2):
            clamped_gods.append(str(tg))
        _runtime[tg] = round(val_clamped, 2)

    # 7. 终效同步与清理
    pt["ten_gods_base_l0"] = dict(_base)
    sync_runtime_aliases(pt, _runtime)
    meta["plugin_execution_status"] = _build_plugin_execution_statuses(
        facts=collected_facts,
        proposals=adjusted_modifier_proposals,
        previous_signatures=previous_signatures,
        clamped_gods=clamped_gods,
    )
    meta["l1_manifest_hits"] = hits
    qsc = meta.get("qi_status_coeffs") if isinstance(meta.get("qi_status_coeffs"), dict) else {}
    if qsc:
        meta["l1_status_v1"] = {
            "phase": str(qsc.get("stage") or "").strip(),
            "resistance": float(qsc.get("resistance", 1.0) or 1.0),
        }
    meta["_v17_hydrated"] = True

    if _ledger:
        pt["ten_gods_ledger"] = _ledger.to_dict()
        if "ledger" in _energy_meta: del _energy_meta["ledger"]

    # 最终类型擦除，防止 JSON 报错
    import json
    tmp = json.loads(json.dumps(pt, default=str))
    pt.clear()
    pt.update(tmp)
