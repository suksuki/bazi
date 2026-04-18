"""
V17.45 PhysicsKernel: 全域反应式因果内核。

核心能力：
1. 统一扰动调度 (dispatch_perturbation)
2. 维护物理幂等性 (Causality_ID)
3. 自动执行 KCL 流重平衡
4. 支持多源注入 (SRC_L0, SRC_MANUAL, SRC_LLM)
"""
from __future__ import annotations

import logging
import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

from v17_rebirth.infrastructure.state_backend import get_state_backend
from v17_rebirth.backend.logic.L0_physics_fields.flow_physics_engine import FlowPhysicsEngine

_log = logging.getLogger(__name__)


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default

def _resolve_significance_weight(impact: Dict[str, Any], payload: Dict[str, Any]) -> float:
    raw = impact.get("significance_weight", payload.get("significance_weight"))
    parsed = _safe_float(raw, default=-1.0)
    if parsed > 0:
        return parsed
    
    level = str(impact.get("significance_level", payload.get("significance_level", "L1"))).strip().upper()
    
    from v17_rebirth.backend.logic.configs.manager import get_v17_constants
    weights = get_v17_constants().get("SIGNIFICANCE_LEVELS", {
        "L0": 0.6, "L1": 0.8, "L2": 1.0, "L3": 1.0
    })
    return float(weights.get(level, 1.0))


def _compute_ratio_application(
    *,
    current_value: float,
    impact: Dict[str, Any],
    payload: Dict[str, Any],
) -> Tuple[float, float]:
    impact_ratio = _safe_float(impact.get("impact_ratio", payload.get("impact_ratio", 0.0)))
    significance_weight = _resolve_significance_weight(impact, payload)
    ratio_applied = impact_ratio * significance_weight
    final_value = round(current_value * (1.0 + ratio_applied), 2)
    return ratio_applied, final_value


def _visible_ratio(value: float) -> bool:
    return abs(value) >= 0.005


def _ledger_has_cyan_highlight(ledger_data: Dict[str, Any]) -> bool:
    for entries in ledger_data.values():
        if not isinstance(entries, list):
            continue
        for entry in entries:
            if isinstance(entry, dict) and str(entry.get("highlight_type") or "").strip() == "cyan":
                return True
    return False

class PhysicsKernel:
    @staticmethod
    async def dispatch_perturbation(
        session_id: str, 
        source: str, 
        payload: Dict[str, Any], 
        causality_id: Optional[str] = None,
        recursion_depth: int = 0
    ) -> bool:
        """
        全域唯一物理修改入口。引入收敛闸保护。
        """
        # 1. 因果收敛闸 (Convergence Gate)
        if recursion_depth > 2:
            _log.warning(f"[Kernel] Convergence Gate Triggered (Depth={recursion_depth}), stopping cascade.")
            return False

        causality_id = causality_id or f"cid_{int(datetime.now(timezone.utc).timestamp() * 1000)}"
        backend = get_state_backend()
        pt = await backend.get_physics(session_id)
        if not pt:
            return False

        # 1. 幂等性校验（防止循环反馈）
        last_cid = pt.get("last_causality_id")
        if last_cid == causality_id:
            _log.warning(f"[Kernel] Idempotency blocked: {causality_id}")
            return False

        _log.info(f"[Kernel] Dispatching Perturbation: SRC={source} CID={causality_id}")

        # 2. 应用相对比例注入 (Relative Ratio Injection)
        ten_gods = pt.get("ten_gods_absolute", {})
        impact = payload.get("physical_impact") if isinstance(payload.get("physical_impact"), dict) else {}
        target_god = impact.get("target_god", payload.get("target_god"))
        target_node = payload.get("node") # 支持五行节点名注入
        target_original_value = None
        target_ratio_applied = 0.0

        # 如果是五行节点注入，将其转化为该节点对应的十神（简单处理：首个匹配）
        if target_node and not target_god:
             from v17_rebirth.backend.logic.L1_atomic_ops.l1_meta_hydration import _get_god_to_element_map
             g2e = _get_god_to_element_map(pt.get("day_master_stem", "壬"))
             if target_node in g2e:
                 target_god = target_node
             else:
                 target_god = next((g for g, e in g2e.items() if e == target_node), None)

        if target_god and target_god in ten_gods:
            target_original_value = _safe_float(ten_gods[target_god])
            target_ratio_applied, target_final_value = _compute_ratio_application(
                current_value=target_original_value,
                impact=impact,
                payload=payload,
            )
            # Support absolute delta_q from LLM narrative interventions if impact_ratio is 0
            if target_ratio_applied == 0.0 and payload.get("delta_q") is not None:
                delta_q = _safe_float(payload.get("delta_q"), 0.0)
                target_final_value = target_original_value + delta_q
                target_ratio_applied = (delta_q / max(abs(target_original_value), 1.0))
                
            ten_gods[target_god] = target_final_value

        # 3. 动态阻抗调制
        res_mod = impact.get("resistance_mod", payload.get("resistance_mod", {}))
        engine = FlowPhysicsEngine(pt.get("day_master_stem", "壬"))
        
        # 4. 执行 KCL 稳态结算
        from v17_rebirth.backend.logic.L1_atomic_ops.l1_meta_hydration import _get_god_to_element_map
        dm_stem = pt.get("day_master_stem", "壬")
        flow_result = engine.compute_flow(
            ten_gods_absolute=ten_gods,
            clash_stress_map={"events": []}, # 暂时清空应力，只由阻抗调制或能级驱动
            ten_god_to_el=_get_god_to_element_map(dm_stem)
        )
        
        for g, d in flow_result["ten_god_deltas"].items():
            if g in ten_gods:
                ten_gods[g] = round(ten_gods[g] + d, 2)

        # 5. 更新账本 (Ledger Record)
        ledger_data = pt.get("ten_gods_ledger", {})
        for g, val in ten_gods.items():
            if g not in ledger_data: ledger_data[g] = []
            reason = f"因果扰动: [{source}] -> {payload.get('reason', '系统内生演化')}"
            original_value = target_original_value if g == target_god and target_original_value is not None else _safe_float(val) - _safe_float(flow_result["ten_god_deltas"].get(g, 0.0))
            final_value = _safe_float(val)
            ratio_applied = (
                target_ratio_applied
                if g == target_god and target_god is not None
                else ((final_value - original_value) / max(abs(original_value), 1.0))
            )
            entry = {
                "step": source, 
                "val": val, 
                "delta": round(final_value - original_value, 2),
                "original_value": round(original_value, 2),
                "ratio_applied": round(ratio_applied, 4),
                "final_value": round(final_value, 2),
                "visible_ratio_change": _visible_ratio(ratio_applied),
                "reason": reason,
                "cid": causality_id,
                "source": source,
            }
            if g == target_god:
                entry["impact_ratio"] = round(_safe_float(impact.get("impact_ratio", payload.get("impact_ratio", 0.0))), 4)
                entry["significance_level"] = str(impact.get("significance_level", payload.get("significance_level", "L1")))
                entry["significance_weight"] = round(_resolve_significance_weight(impact, payload), 4)
            ledger_data[g].append(entry)
            if len(ledger_data[g]) > 8: ledger_data[g].pop(1)

        # 6. 状态同步并广播 PHYSICS_SYNC
        pt["ten_gods_absolute"] = ten_gods
        pt["ten_gods_absolute_intensity"] = ten_gods
        pt["deity_scores"] = ten_gods
        pt["ten_gods_ledger"] = ledger_data
        pt["last_causality_id"] = causality_id
        pt["total_energy_index"] = round(sum(ten_gods.values()), 2)
        pt["flow_topology"] = flow_result["topology"]
        
        # 强制类型擦除 (Type Erasure) 确保 JSON 兼容
        def _safe_trans(obj):
            import json
            return json.loads(json.dumps(obj, default=str))
        
        pt = _safe_trans(pt)
        await backend.set_physics(session_id, pt)
        
        # 发布全域同步信号
        sync_event = {
            "signal": "PHYSICS_SYNC",
            "session_id": session_id,
            "source": source,
            "cid": causality_id,
            "payload": _safe_trans({
                "highlight_type": "cyan" if _ledger_has_cyan_highlight(ledger_data) else "",
                "ten_gods_absolute": ten_gods,
                "ten_gods_absolute_intensity": ten_gods,
                "deity_scores": ten_gods,
                "ten_gods_ledger": ledger_data,
                "total_energy_index": pt["total_energy_index"],
                "flow_topology": pt["flow_topology"]
            })
        }
        await backend.publish_action(session_id, sync_event)
        return True
