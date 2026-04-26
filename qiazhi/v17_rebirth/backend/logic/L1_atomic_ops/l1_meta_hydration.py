"""
V17.99：物理水分抽取层（Hydration Hub）。
负责将 L0 静态数据转化为 L1+ 动态张量，并统一执行插件生命周期。
"""
from __future__ import annotations
import logging
import math
from v17_rebirth.backend.infrastructure.evolution_db import evolution_storage
from typing import Any, Dict, List, Tuple

from v17_rebirth.backend.logic.L1_atomic_ops.relation_geometry_pairs import (
    eval_anhe_hits,
    eval_liu_chong_hits,
    eval_liu_hai_hits,
    eval_liu_po_hits,
    eval_liuhe_hits,
    sanxing_detect_geometry,
    summarize_sanxing_branches,
)
from v17_rebirth.backend.logic.L1_atomic_ops.relation_geometry_structured import (
    eval_banhe_hits,
    eval_sanhe_hits,
    eval_sanhui_hits,
)
from v17_rebirth.backend.logic.L1_atomic_ops.stem_fusion_geometry import (
    branches_and_stems_from_four_pillars,
    branches_and_stems_from_runtime_pillars,
    detect_stem_fusion_cases,
)
from v17_rebirth.backend.logic.L0_physics_fields.bazi_image_core import normalize_bazi_image_meta
from v17_rebirth.backend.logic.L2_structure_patterns.blind_school_core import normalize_blind_theme_meta
from v17_rebirth.backend.logic.L2_structure_patterns.climate_theme_core import normalize_climate_theme_meta
from v17_rebirth.backend.logic.L2_structure_patterns.xiangfa_theme_core import normalize_xiangfa_theme_meta
from v17_rebirth.backend.logic.L3_modern_narrative.macro_theme_core import normalize_macro_theme_meta
from v17_rebirth.backend.logic.L3_modern_narrative.wealth_profile_core import normalize_wealth_profile_meta
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
from v17_rebirth.backend.logic.L1_atomic_ops.plugin_condition_protocol import detect_relation_origin_type
from v17_rebirth.backend.plugins.v17_wrappers import collect_pending_decisions_from_specs
from v17_rebirth.backend.services.claim_protocol import CLAIM_JSON_SCHEMA, compile_claims
from v17_rebirth.backend.services.conflict_detector import detect_claim_conflicts, recommend_conflict_resolutions
from v17_rebirth.backend.services.conflict_scoring import build_conflict_scores
from v17_rebirth.backend.services.knowledge_store import build_knowledge_snapshot
from v17_rebirth.backend.services.master_reasoning import build_master_reasoning_trace
from v17_rebirth.backend.services.arbiter_router import route_conflicts
from v17_rebirth.backend.services.decision_compiler import compile_modifier_proposals, compile_pending_decisions
from v17_rebirth.backend.services.hydration_pipeline import (
    append_algorithm_execution_stage,
    bucket_decision_records,
    build_algorithm_execution_audit,
    build_algorithm_execution_policy,
    build_plugin_governance_manifest,
)
from v17_rebirth.backend.services.meta_contract import build_meta_contract
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
                # Manifest hit is an observation anchor, not an executable user action.
                "arbiter_type": "llm",
                "status": "PENDING",
                "llm_resolution_type": "context_only",
                "llm_resolution_state": "pending_context",
                "llm_terminal_state": "consume_context",
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


def _geometry_rows_with_origin(rows: List[Dict[str, Any]], *, member_key: str) -> List[Dict[str, Any]]:
    payload: List[Dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        item = dict(row)
        item["origin_type"] = detect_relation_origin_type(item.get("pillars") or [])
        if member_key == "group":
            item["matched_branches"] = [
                str(value) for value in (item.get("matched_branches") or item.get("group") or []) if str(value).strip()
            ]
        payload.append(item)
    return payload


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
    decisions: List[Dict[str, Any]],
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

    decisions_by_plugin: Dict[str, List[Dict[str, Any]]] = {}
    for decision in decisions:
        if not isinstance(decision, dict):
            continue
        pid = str(decision.get("plugin_id") or decision.get("source") or "").strip()
        if not pid:
            continue
        decisions_by_plugin.setdefault(pid, []).append(dict(decision))

    prev_set = {str(x).strip() for x in previous_signatures if str(x).strip()}
    clamped_set = {str(x).strip() for x in clamped_gods if str(x).strip()}
    statuses: List[Dict[str, Any]] = []

    for plugin_id in sorted(set([*facts_by_plugin.keys(), *proposals_by_plugin.keys()])):
        plugin_proposals = proposals_by_plugin.get(plugin_id, [])
        plugin_decisions = decisions_by_plugin.get(plugin_id, [])
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

        if plugin_decisions:
            statuses_upper = {str(row.get("status") or "").strip().upper() for row in plugin_decisions}
            if "APPROVED" in statuses_upper:
                status = "manual_committed"
                reason = "插件对应的决策已通过人工结算，并已写入 runtime。"
            elif "CONSUMED_CONTEXT" in statuses_upper:
                status = "context_consumed"
                reason = "插件输出已作为上下文素材消化，不再阻塞物理结算。"
            elif "REJECTED" in statuses_upper:
                status = "manual_rejected"
                reason = "插件对应的决策已被否决，本轮不进入物理结算。"
            elif "AWAIT_REVIEW" in statuses_upper:
                status = "await_review"
                reason = "插件对应的决策已入计划队列，等待进一步裁决。"
            elif any(str(row.get("arbiter_type") or "").strip().lower() == "user" for row in plugin_decisions):
                status = "manual_pending"
                reason = "插件 proposal 已转为手动决策，当前仍在 Decision Inbox 中等待处理。"
            elif any(str(row.get("llm_terminal_state") or "").strip() == "consume_context" for row in plugin_decisions):
                status = "context_pending"
                reason = "插件 proposal 已降级为上下文素材，等待叙事层引用。"

        statuses.append(
            {
                "plugin_id": plugin_id,
                "fact_count": facts_by_plugin.get(plugin_id, 0),
                "proposal_count": len(plugin_proposals),
                "decision_count": len(plugin_decisions),
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
    branches, stems = branches_and_stems_from_runtime_pillars(
        pt.get("four_pillars"),
        luck_pillar=pt.get("luck_pillar"),
        flow_pillar=pt.get("flow_pillar"),
    )
    _fp = pt.get("four_pillars") if isinstance(pt.get("four_pillars"), dict) else {}
    _day_gz = str(_fp.get("day", "")).strip()
    _daymaster = _day_gz[0] if len(_day_gz) >= 2 else "壬"
    
    liu_chong = eval_liu_chong_hits(branches) if branches else []
    liu_hai = eval_liu_hai_hits(branches) if branches else []
    liu_po = eval_liu_po_hits(branches) if branches else []
    liu_he = eval_liuhe_hits(branches) if branches else []
    san_he = eval_sanhe_hits(branches) if branches else []
    san_hui = eval_sanhui_hits(branches) if branches else []
    ban_he = eval_banhe_hits(branches) if branches else []
    an_he = eval_anhe_hits(branches) if branches else []
    muku_hits = [b for b in branches.values() if b in {"辰", "戌", "丑", "未"}] if branches else []
    sanxing_geo = sanxing_detect_geometry(branches) if branches else []
    stem_cases = detect_stem_fusion_cases(stems, branches) if stems else []

    # 2. 填充 interaction_v2 (用于插件探测源)
    geom_data = {
        "version": "interaction_v2.v2",
        "pillar_scope": sorted(branches.keys()),
        "runtime_extensions": {
            "luck": str(pt.get("luck_pillar") or "").strip(),
            "flow": str(pt.get("flow_pillar") or "").strip(),
        },
        "liu_chong": _geometry_rows_with_origin(liu_chong, member_key="pair"),
        "liu_hai": _geometry_rows_with_origin(liu_hai, member_key="pair"),
        "liu_po": _geometry_rows_with_origin(liu_po, member_key="pair"),
        "liu_he": _geometry_rows_with_origin(liu_he, member_key="pair"),
        "san_he": _geometry_rows_with_origin(san_he, member_key="group"),
        "san_hui": _geometry_rows_with_origin(san_hui, member_key="group"),
        "ban_he": _geometry_rows_with_origin(ban_he, member_key="pair"),
        "an_he": _geometry_rows_with_origin(an_he, member_key="pair"),
        "sanxing": [{"branches": h.get("branches"), "edge": h.get("edge"), "origin_type": detect_relation_origin_type(h.get("edge") or [])} for h in sanxing_geo],
    }
    meta["interaction_v2"] = geom_data
    pt["interaction_v2"] = geom_data # 增强型注入
    append_algorithm_execution_stage(
        meta,
        stage="geometry_built",
        label="几何关系建模",
        counts={
            "branch_scope_count": len(branches),
            "sanhe_hits": len(san_he),
            "sanhui_hits": len(san_hui),
            "banhe_hits": len(ban_he),
            "anhe_hits": len(an_he),
            "liuhe_hits": len(liu_he),
            "clash_hits": len(liu_chong),
        },
    )
    
    print(
        f"[V17-HYDRATION-GEOM] Scope: {','.join(sorted(branches.keys()))} | "
        f"Sanhe: {len(san_he)} | Sanhui: {len(san_hui)} | Sanxing: {len(sanxing_geo)}"
    )

    # 3. 填充基础 Hits (Legacy Admin UI 兼容)
    hits = {}
    if liu_chong: _register_manifest_hit(hits, "l1.physics.op_branch_liuchong", "", "六冲", 0.72)
    if san_he: _register_manifest_hit(hits, "l1.physics.op_branch_sanhe", "", "三合成局", 0.76)
    if san_hui: _register_manifest_hit(hits, "l1.physics.op_branch_sanhui", "", "三会成势", 0.755)
    if ban_he: _register_manifest_hit(hits, "l1.physics.op_branch_banhe", "", "半合聚势", 0.69)
    if an_he: _register_manifest_hit(hits, "l1.physics.op_branch_anhe", "", "暗合", 0.68)
    if muku_hits: _register_manifest_hit(hits, "l1.physics.op_branch_muku", "", "墓库门态", 0.73, {"branches": muku_hits})
    if liu_hai: _register_manifest_hit(hits, "l1.physics.op_branch_liuhai", "", "六害", 0.7)
    if liu_po: _register_manifest_hit(hits, "l1.physics.op_branch_liupo", "", "六破", 0.69)
    if sanxing_geo: _register_manifest_hit(hits, "l1.physics.op_branch_sanxing", "", "三刑", 0.71)
    if stem_cases:
        meta["stem_fusion_v1"] = {"cases": stem_cases}
        _register_manifest_hit(hits, "l1.physics.op_stem_fusion", "", "天干五合", 0.74, {"cases": stem_cases})

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
    append_algorithm_execution_stage(
        meta,
        stage="base_runtime_ready",
        label="基线与运行态初始化",
        counts={
            "base_god_count": len(_base),
            "runtime_god_count": len(_runtime),
        },
    )
    session_id = str(pt.get("session_id", "default_ghost"))
    pt.setdefault("facts", [])
    pt.setdefault("pending_decisions", [])
    
    _energy_meta = pt.get("energy_meta", {})
    _ledger = _energy_meta.get("ledger")

    from v17_rebirth.backend.logic.plugin_discovery import iter_all_plugin_specs
    from v17_rebirth.backend.plugins.spec import ArbiterType, AuditStatus
    all_specs = iter_all_plugin_specs()
    _scanned_pids = [s.plugin_id for s in all_specs]
    meta["plugin_governance_manifest"] = build_plugin_governance_manifest(all_specs)
    append_algorithm_execution_stage(
        meta,
        stage="plugin_manifest_ready",
        label="插件治理清单生成",
        counts={
            "plugin_count": len(_scanned_pids),
        },
    )
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
            if isinstance(f.meta, dict) and isinstance(f.meta.get("god_ring_authority"), dict):
                incoming = dict(f.meta.get("god_ring_authority") or {})
                current = meta.get("god_ring_authority") if isinstance(meta.get("god_ring_authority"), dict) else {}
                if float(incoming.get("confidence") or 0.0) >= float(current.get("confidence") or -1.0):
                    meta["god_ring_authority"] = incoming
            if isinstance(f.meta, dict) and isinstance(f.meta.get("blind_theme"), dict):
                incoming_blind = normalize_blind_theme_meta(f.meta.get("blind_theme"))
                current_blind = normalize_blind_theme_meta(meta.get("blind_theme"))
                incoming_conf = float(incoming_blind.get("confidence") or 0.0)
                current_conf = float(current_blind.get("confidence") or -1.0)
                if incoming_conf >= current_conf:
                    meta["blind_theme"] = incoming_blind
            if isinstance(f.meta, dict) and isinstance(f.meta.get("climate_theme"), dict):
                incoming_climate = normalize_climate_theme_meta(f.meta.get("climate_theme"))
                current_climate = normalize_climate_theme_meta(meta.get("climate_theme"))
                incoming_conf = float(incoming_climate.get("confidence") or 0.0)
                current_conf = float(current_climate.get("confidence") or -1.0)
                if incoming_conf >= current_conf:
                    meta["climate_theme"] = incoming_climate
            if isinstance(f.meta, dict) and isinstance(f.meta.get("xiangfa_theme"), dict):
                incoming_xiangfa = normalize_xiangfa_theme_meta(f.meta.get("xiangfa_theme"))
                current_xiangfa = normalize_xiangfa_theme_meta(meta.get("xiangfa_theme"))
                incoming_conf = float(incoming_xiangfa.get("confidence") or 0.0)
                current_conf = float(current_xiangfa.get("confidence") or -1.0)
                if incoming_conf >= current_conf:
                    meta["xiangfa_theme"] = incoming_xiangfa
            if isinstance(f.meta, dict) and isinstance(f.meta.get("bazi_image"), dict):
                incoming_bazi_image = normalize_bazi_image_meta(f.meta.get("bazi_image"))
                incoming_conf = float(
                    (f.meta.get("bazi_image") or {}).get("confidence")
                    or f.meta.get("confidence")
                    or 0.0
                )
                current_conf = (
                    float((meta.get("bazi_image") or {}).get("confidence") or -1.0)
                    if isinstance(meta.get("bazi_image"), dict)
                    else -1.0
                )
                if incoming_bazi_image and incoming_conf >= current_conf:
                    meta["bazi_image"] = incoming_bazi_image
            if isinstance(f.meta, dict) and isinstance(f.meta.get("macro_theme"), dict):
                incoming_macro = normalize_macro_theme_meta(f.meta.get("macro_theme"))
                current_macro = normalize_macro_theme_meta(meta.get("macro_theme"))
                incoming_conf = float(incoming_macro.get("confidence") or 0.0)
                current_conf = float(current_macro.get("confidence") or -1.0)
                if incoming_conf >= current_conf:
                    meta["macro_theme"] = incoming_macro
            if isinstance(f.meta, dict) and isinstance(f.meta.get("wealth_profile"), dict):
                incoming_wealth_profile = normalize_wealth_profile_meta(f.meta.get("wealth_profile"))
                current_wealth_profile = normalize_wealth_profile_meta(meta.get("wealth_profile"))
                incoming_conf = float(incoming_wealth_profile.get("confidence") or 0.0)
                current_conf = float(current_wealth_profile.get("confidence") or -1.0)
                if incoming_conf >= current_conf:
                    meta["wealth_profile"] = incoming_wealth_profile
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
    append_algorithm_execution_stage(
        meta,
        stage="plugin_scan_completed",
        label="专题扫描与主题提升",
        counts={
            "active_plugin_count": len(_active_plugins),
            "fact_count": len(collected_facts),
            "decision_count": len(pt.get("pending_decisions", [])),
        },
        sovereignty={
            "hard_authority_present": isinstance(meta.get("god_ring_authority"), dict) and bool(meta.get("god_ring_authority")),
            "blind_theme_present": isinstance(meta.get("blind_theme"), dict) and bool(meta.get("blind_theme")),
            "climate_theme_present": isinstance(meta.get("climate_theme"), dict) and bool(meta.get("climate_theme")),
            "xiangfa_theme_present": isinstance(meta.get("xiangfa_theme"), dict) and bool(meta.get("xiangfa_theme")),
            "bazi_image_present": isinstance(meta.get("bazi_image"), dict) and bool(meta.get("bazi_image")),
            "macro_theme_present": isinstance(meta.get("macro_theme"), dict) and bool(meta.get("macro_theme")),
            "wealth_profile_present": isinstance(meta.get("wealth_profile"), dict) and bool(meta.get("wealth_profile")),
        },
    )

    modifier_proposals = compile_modifier_proposals(facts=collected_facts, physics_tensor=pt)
    claim_rows = compile_claims(facts=collected_facts, physics_tensor=pt)
    append_algorithm_execution_stage(
        meta,
        stage="claims_compiled",
        label="主张与提案编译",
        counts={
            "proposal_count": len(modifier_proposals),
            "claim_count": len(claim_rows),
        },
    )
    raw_conflict_rows = detect_claim_conflicts(claim_rows)
    scored_conflict_rows = build_conflict_scores(conflicts=raw_conflict_rows, claim_rows=claim_rows)
    conflict_resolutions = recommend_conflict_resolutions(claim_rows, raw_conflict_rows)
    conflict_feedback = evolution_storage.get_feedback(
        session_id,
        action="conflict_resolution",
        limit=120,
    )
    knowledge_snapshot = build_knowledge_snapshot(
        claims=claim_rows,
        conflicts=scored_conflict_rows,
        conflict_resolutions=conflict_resolutions,
        feedback_rows=conflict_feedback,
        current_authority=meta.get("god_ring_authority") if isinstance(meta.get("god_ring_authority"), dict) else None,
    )
    conflict_rows = route_conflicts(conflicts=scored_conflict_rows, knowledge_snapshot=knowledge_snapshot)
    append_algorithm_execution_stage(
        meta,
        stage="conflicts_routed",
        label="冲突检测与仲裁路由",
        counts={
            "raw_conflict_count": len(raw_conflict_rows),
            "scored_conflict_count": len(scored_conflict_rows),
            "routed_conflict_count": len(conflict_rows),
        },
    )
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
        settled_runtime, ratio_totals, applied_rows = settle_modifier_proposals(
            _runtime,
            adjusted_modifier_proposals,
            base_scores=_base,
        )
        _runtime = settled_runtime
        meta["plugin_auto_ratio_totals"] = ratio_totals
        meta["plugin_auto_settlement_signatures"] = auto_signatures
        meta["plugin_settlement_mode"] = "base_recompute"
        meta["plugin_recompute_contributions"] = [dict(row) for row in applied_rows]
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
    append_algorithm_execution_stage(
        meta,
        stage="modifier_settlement_completed",
        label="统一结算完成",
        counts={
            "adjusted_proposal_count": len(adjusted_modifier_proposals),
            "auto_settlement_signature_count": len(auto_signatures),
            "conflict_resolution_count": len(conflict_resolutions),
        },
    )
    master_reasoning = build_master_reasoning_trace(physics_tensor=pt, meta=meta)
    meta["master_reasoning"] = dict(master_reasoning)
    pt["master_reasoning"] = dict(master_reasoning)

    _scanned_pids = [s.plugin_id for s in all_specs]

    # 4.5 V17.99: 案卷分选 (Bucketing for UI)
    pt["pending_decisions"].extend([
        *_manifest_hits_to_decision_rows(hits),
        *_geometry_hits_to_decision_rows(pt, hits),
    ])
    _all_decisions = pt.get("pending_decisions", [])
    decision_buckets = bucket_decision_records(_all_decisions)
    pt["manual_decisions"] = decision_buckets["manual_decisions"]
    pt["auto_resolutions"] = decision_buckets["auto_resolutions"]
    pt["llm_arbitration_context"] = decision_buckets["llm_arbitration_context"]
    pt["manual_inbox"] = decision_buckets["manual_inbox"]
    pt["auto_decisions"] = decision_buckets["auto_decisions"]
    pt["decision_inbox_contract"] = decision_buckets["decision_inbox_contract"]
    meta["decision_bucket_contract"] = decision_buckets
    append_algorithm_execution_stage(
        meta,
        stage="decision_buckets_ready",
        label="决策分桶完成",
        counts={
            "manual_count": len(pt["manual_decisions"]),
            "system_count": len(pt["auto_resolutions"]),
            "llm_count": len(pt["llm_arbitration_context"]),
        },
    )
    
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
    append_algorithm_execution_stage(
        meta,
        stage="flow_applied",
        label="流转平衡完成",
        counts={
            "topology_edge_count": len((meta.get("flow_topology") or {}).get("edges", [])) if isinstance(meta.get("flow_topology"), dict) else 0,
            "stress_node_count": len(stress_map),
        },
    )

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
    meta["v17_physics_stable"] = True
    meta["plugin_execution_status"] = _build_plugin_execution_statuses(
        facts=collected_facts,
        proposals=adjusted_modifier_proposals,
        previous_signatures=previous_signatures,
        clamped_gods=clamped_gods,
        decisions=_all_decisions,
    )
    meta["l1_manifest_hits"] = hits
    append_algorithm_execution_stage(
        meta,
        stage="runtime_synced",
        label="运行态同步与专题收束",
        counts={
            "runtime_god_count": len(_runtime),
            "plugin_status_count": len(meta.get("plugin_execution_status") or []),
        },
        sovereignty={
            "hard_authority_present": isinstance(meta.get("god_ring_authority"), dict) and bool(meta.get("god_ring_authority")),
            "blind_theme_present": isinstance(meta.get("blind_theme"), dict) and bool(meta.get("blind_theme")),
            "climate_theme_present": isinstance(meta.get("climate_theme"), dict) and bool(meta.get("climate_theme")),
            "xiangfa_theme_present": isinstance(meta.get("xiangfa_theme"), dict) and bool(meta.get("xiangfa_theme")),
            "bazi_image_present": isinstance(meta.get("bazi_image"), dict) and bool(meta.get("bazi_image")),
            "macro_theme_present": isinstance(meta.get("macro_theme"), dict) and bool(meta.get("macro_theme")),
            "wealth_profile_present": isinstance(meta.get("wealth_profile"), dict) and bool(meta.get("wealth_profile")),
            "authority_layer_protocol_present": isinstance((meta.get("god_ring_authority") or {}).get("authority_layer_protocol"), dict),
        },
    )
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

    meta["algorithm_execution_policy"] = build_algorithm_execution_policy()
    meta["meta_contract"] = build_meta_contract(meta)
    append_algorithm_execution_stage(
        meta,
        stage="meta_contract_built",
        label="元数据契约完成",
        counts={
            "public_meta_key_count": int((meta.get("meta_contract") or {}).get("public_key_count") or 0),
            "solver_trace_key_count": int((meta.get("meta_contract") or {}).get("solver_trace_key_count") or 0),
        },
    )
    meta["algorithm_execution_audit"] = build_algorithm_execution_audit(meta.get("algorithm_execution_trace"))
    meta["meta_contract"] = build_meta_contract(meta)

    # 最终类型擦除，防止 JSON 报错
    import json
    tmp = json.loads(json.dumps(pt, default=str))
    pt.clear()
    pt.update(tmp)
