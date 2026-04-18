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
from typing import Any, Dict, Optional

from v17_rebirth.infrastructure.state_backend import get_state_backend
from v17_rebirth.backend.logic.L0_physics_fields.flow_physics_engine import FlowPhysicsEngine

_log = logging.getLogger(__name__)


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

        # 2. 应用原始能级注入 (Qi Injection)
        ten_gods = pt.get("ten_gods_absolute", {})
        impact = payload.get("physical_impact") if isinstance(payload.get("physical_impact"), dict) else {}
        delta_q = impact.get("delta_q", payload.get("delta_q", 0.0))
        target_god = impact.get("target_god", payload.get("target_god"))
        target_node = payload.get("node") # 支持五行节点名注入

        # 如果是五行节点注入，将其转化为该节点对应的十神（简单处理：首个匹配）
        if target_node and not target_god:
             from v17_rebirth.backend.logic.L1_atomic_ops.l1_meta_hydration import _get_god_to_element_map
             g2e = _get_god_to_element_map(pt.get("day_master_stem", "壬"))
             target_god = next((g for g, e in g2e.items() if e == target_node), None)

        if target_god and target_god in ten_gods:
            ten_gods[target_god] = round(ten_gods[target_god] + delta_q, 2)

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
            entry = {
                "step": source, 
                "val": val, 
                "delta": delta_q if g == target_god else flow_result["ten_god_deltas"].get(g, 0), 
                "reason": reason,
                "cid": causality_id,
                "source": source,
            }
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
