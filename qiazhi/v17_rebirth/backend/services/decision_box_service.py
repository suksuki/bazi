"""
V17.38 DecisionBoxService: 物理具身化动作处理器。

实现分频架构中的“高频物理层”：
1. 拦截动作请求
2. 实时更新 Redis 快照中的十神能量 (delta_q)
3. 动态调整五行阻抗并重新执行 KCL 求解
4. 记录物理演化账本 (EvolutionLedger)
5. 广播 PHYSICS_UPDATE 信号
"""
from __future__ import annotations

import logging
from typing import Any, Dict
from datetime import datetime, timezone

from v17_rebirth.infrastructure.state_backend import get_state_backend
from v17_rebirth.backend.logic.L0_physics_fields.flow_physics_engine import FlowPhysicsEngine
from v17_rebirth.backend.logic.L0_physics_fields.evolution_ledger import EvolutionLedger

_log = logging.getLogger(__name__)

class DecisionBoxService:
    @staticmethod
    async def apply_physical_impact(session_id: str, action_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        物理旁路执行逻辑 (High-Frequency Bypass)。
        """
        backend = get_state_backend()
        pt = await backend.get_physics(session_id)
        if not pt:
            _log.error(f"[DecisionBox] Session {session_id} physics tensor not found")
            return {"ok": False, "error": "physics_missing"}

        # 1. 识别物理负载
        # 如果是 Decision Box 传来的选定项，payload 结构通常包含具体的 impact
        action_name = action_data.get("action", "")
        # 我们假设 action_data 中可能直接携带了 impact，或者我们需要从 pt 里的 decisions 中寻找
        impact = action_data.get("physical_impact")
        
        # 兜底：从当前 pt 中寻找匹配的 decision
        if not impact:
            decisions = pt.get("pending_decisions", [])
            for d in decisions:
                if d.get("id") == action_name or d.get("title") == action_name:
                    impact = d.get("physical_impact")
                    d["applied"] = True # 标记为已应用
                    break
        
        if not impact:
            _log.info(f"[DecisionBox] Action {action_name} has no physical impact, skipping bypass.")
            return {"ok": True, "applied": False}

        # 2. 应用原始能级变动 (delta_q)
        target_god = impact.get("target_god")
        delta_q = impact.get("delta_q", 0.0)
        
        ten_gods = pt.get("ten_gods_absolute", {})
        if target_god and target_god in ten_gods:
            old_val = ten_gods[target_god]
            ten_gods[target_god] = round(old_val + delta_q, 2)
            _log.info(f"[DecisionBox] Applied Delta_Q: {target_god} {old_val} -> {ten_gods[target_god]}")
        
        # 3. 动态阻抗调制与 KCL 重算
        # 我们可以临时修改 clash_stress_map 或直接给 FlowEngine 传入调制参数
        engine = FlowPhysicsEngine(pt.get("day_master_stem", "壬"))
        
        # 构建一个临时的 stress_map 用于模拟阻抗击穿
        res_mod = impact.get("resistance_mod", {})
        fake_stress = {"events": []}
        if res_mod:
            # 如果有阻抗调制，我们通过伪造一个高强度应力来“击穿”路径
            # R_new = R_base * (1 + 1/F) -> F = 1 / (factor - 1) if factor < 1
            factor = res_mod.get("factor", 1.0)
            if factor < 1.0:
                stress_val = 1.0 / (max(0.01, factor)) * 10 # 粗略映射
                fake_stress["events"].append({
                    "god_i": target_god,
                    "god_j": "SYSTEM_MOD", # 暂时作为一个标记
                    "damped_stress": stress_val
                })

        # 运行 Flow 求解
        from v17_rebirth.backend.logic.L1_atomic_ops.l1_meta_hydration import _get_god_to_element_map
        god_to_el = _get_god_to_element_map()
        
        flow_result = engine.compute_flow(
            ten_gods_absolute=ten_gods,
            clash_stress_map=fake_stress,
            ten_god_to_el=god_to_el
        )
        
        # 应用 Flow 结果
        deltas = flow_result["ten_god_deltas"]
        for g, d in deltas.items():
            if g in ten_gods:
                ten_gods[g] = round(ten_gods[g] + d, 2)

        # 4. 记录账本
        # 我们需要从 pt 中恢复账本数据
        from v17_rebirth.backend.logic.L0_physics_fields.evolution_ledger import EvolutionLedger
        ledger_data = pt.get("ten_gods_ledger", {})
        # 由于存入 Redis 的是 dict，我们需要一个简单的静态方法来追加或手动操作
        for g, val in ten_gods.items():
            if g not in ledger_data: ledger_data[g] = []
            reason = f"人为干预: [{action_name}] 物理导通"
            entry = {"step": "L2_ACTION_IMPACT", "val": val, "delta": delta_q if g == target_god else deltas.get(g, 0), "reason": reason}
            ledger_data[g].append(entry)
            if len(ledger_data[g]) > 8: ledger_data[g].pop(1) # 保留基准，滚动删除

        # 5. 更新状态并发布信号
        pt["ten_gods_absolute"] = ten_gods
        pt["ten_gods_absolute_intensity"] = ten_gods
        pt["ten_gods_ledger"] = ledger_data
        pt["total_energy_index"] = round(sum(ten_gods.values()), 2)
        pt["flow_topology"] = flow_result["topology"]
        
        await backend.set_physics(session_id, pt)
        
        # 发布 PHYSICS_UPDATE 信号
        update_event = {
            "signal": "PHYSICS_UPDATE",
            "session_id": session_id,
            "ts": datetime.now(timezone.utc).isoformat(),
            "payload": {
                "ten_gods_absolute": ten_gods,
                "ten_gods_ledger": ledger_data,
                "total_energy_index": pt["total_energy_index"],
                "flow_topology": flow_result["topology"]
            }
        }
        await backend.publish_action(session_id, update_event)
        
        return {"ok": True, "applied": True, "new_index": pt["total_energy_index"]}
