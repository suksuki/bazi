"""
V17.34：流转物理引擎 (Flow Physics Engine)。
基于基尔霍夫电流定律 (Kirchhoff's Current Law, KCL) 实现五行网络能量流转分析。

建模：
1. 节点 (Node): 木(0), 火(1), 土(2), 金(3), 水(4)
2. 电位 (V): 节点的初始电位 = 该五行对应的十神能量总和 (Qi)
3. 生支路 (Sheng): R = 0.5Ω (低电阻)
4. 克支路 (Ke):   R = 5.0Ω (高电阻)
5. 调制：R_new = R_base * (1 + 1/F)，F 为 L1 阶段的应力强度。
"""
from __future__ import annotations

import math
from typing import Any, Dict, List, Tuple

from v17_rebirth.backend.logic.L0_physics_fields.ten_gods_engine import (
    ELEMENT_CYCLE,
    STEM_ELEMENT,
)

# ── 电路常数 ──────────────────────────────────────────────────────────────────

R_SHENG_BASE = 0.5   # 生路径基准电阻
R_KE_BASE = 5.0      # 克路径基准电阻

# 能量流转转换系数 (I -> dQ)
# 设定为 0.02，即每单位电位差引起的电流在这一步演化中产生的 Qi 位移量
FLOW_CONDUCTIVITY_ALPHA = 0.02


class FlowPhysicsEngine:
    """五行电路网络流引擎。"""

    def __init__(self, daymaster_el: str) -> None:
        self.dm_el = daymaster_el
        # 建立五行索引：0:木, 1:火, 2:土, 3:金, 4:水
        self.el_to_idx = {el: i for i, el in enumerate(ELEMENT_CYCLE)}
        self.idx_to_el = {i: el for i, el in enumerate(ELEMENT_CYCLE)}

    def compute_flow(
        self,
        *,
        ten_gods_absolute: Dict[str, float],
        clash_stress_map: Dict[str, Any],
        ten_god_to_el: Dict[str, str],
    ) -> Dict[str, Any]:
        """
        执行 KCL 计算。
        
        返回：
            {
                "ten_god_deltas": { god_name: dQ },
                "topology": [...], # 支路电流信息
                "element_potentials": [...] # 五行电位
            }
        """
        # 1. 初始化电位：将十神能量合并到五行节点
        potentials = [0.0] * 5
        for god, val in ten_gods_absolute.items():
            el = ten_god_to_el.get(god)
            if el in self.el_to_idx:
                potentials[self.el_to_idx[el]] += val

        # 2. 构建电阻矩阵与应力调制
        # 获取各五行间的应力总和（简化版：将 L1 冲突映射到五行节点对）
        stress_matrix = [[0.0] * 5 for _ in range(5)]
        for ev in clash_stress_map.get("events", []):
            el_i = ten_god_to_el.get(ev.get("god_i", ""))
            el_j = ten_god_to_el.get(ev.get("god_j", ""))
            if el_i in self.el_to_idx and el_j in self.el_to_idx:
                idx_i, idx_j = self.el_to_idx[el_i], self.el_to_idx[el_j]
                # 应力是相互的
                f = abs(ev.get("damped_stress", 0.0))
                stress_matrix[idx_i][idx_j] += f
                stress_matrix[idx_j][idx_i] += f

        # 3. 计算支路电流 I = (V_i - V_j) / R
        branches = []
        node_net_currents = [0.0] * 5

        for i in range(5):
            for j in range(5):
                if i == j: continue
                
                # 判定生克关系
                dist = (j - i) % 5
                r_base = 0.0
                rel_name = ""
                
                if dist == 1: # 生
                    r_base = R_SHENG_BASE
                    rel_name = "生"
                elif dist == 2: # 克
                    r_base = R_KE_BASE
                    rel_name = "克"
                else:
                    continue # 暂不考虑反生反克
                
                # 应力调制：R_new = R_base * (1 + 1/F)
                # V17.99: 物理奇点保护 — 将 1/F 重构为稳健的线性衰减调制
                # 当应力 f=0 时，电阻保持由于 max(0.1, f) 限制在 11倍基准，确保有限性
                f = float(stress_matrix[i][j])
                modulation = (1.0 + (1.0 / max(0.1, f))) 
                
                # 再次防御：强制截断并确保有限
                if not math.isfinite(modulation):
                    modulation = 11.0
                
                r_now = r_base * min(11.0, modulation)
                
                # 欧姆定律计算电流 (从 i 指向 j)
                v_diff = potentials[i] - potentials[j]
                
                # 安全校验：若电位差本身异常，电流强制归零
                if not math.isfinite(v_diff) or not math.isfinite(r_now) or r_now <= 0:
                    current = 0.0
                else:
                    current = v_diff / r_now
                
                # V17.99: 分流钳制 — 防止支路电流溢出 (Max Delta Cap)
                if current > 2000.0: current = 2000.0
                if current < -2000.0: current = -2000.0
                
                # KCL 记录
                node_net_currents[i] -= current # 流出
                node_net_currents[j] += current # 流入
                
                if current > 0.1: # 记录显著流转
                    branches.append({
                        "from_el": self.idx_to_el[i],
                        "to_el": self.idx_to_el[j],
                        "current": current,
                        "rel": rel_name,
                        "resistance": round(r_now, 3),
                        "stress": round(f, 3),
                    })

        # 4. 电位变化量回写到十神（按原比例分摊）
        ten_god_deltas: Dict[str, float] = {}
        for god, val in ten_gods_absolute.items():
            el = ten_god_to_el.get(god)
            if el in self.el_to_idx:
                idx = self.el_to_idx[el]
                # 这里使用系数将电流转化为能量变化 dQ = I_net * Alpha
                # 这里的 I_net 是净流入量
                node_weight = val / max(0.1, potentials[idx])
                god_dq = node_net_currents[idx] * FLOW_CONDUCTIVITY_ALPHA * node_weight
                
                # V17.99: 终极大闸 — 确保回写能量变化量是有限的
                if math.isfinite(god_dq):
                    ten_god_deltas[god] = round(god_dq, 3)
                else:
                    ten_god_deltas[god] = 0.0

        return {
            "ten_god_deltas": ten_god_deltas,
            "topology": branches,
            "potentials": potentials
        }
