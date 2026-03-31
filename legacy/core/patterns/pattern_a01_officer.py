# -*- coding: utf-8 -*-
"""
Antigravity Pattern Module: A-01 Direct Officer
Kernel: V2.6 (Quantum Relative Field)
Protocol: L3 (Topology & Gating)
"""
from core.patterns.base_pattern import BasePattern, PatternResult

class PatternA01_DirectOfficer(BasePattern):
    """
    A-01 正官格 (V2.6 Edition)
    
    Upgrade Notes:
    - Uses V2.6 Non-linear Thresholds.
    - Day Pillar Weight increased to 1.35.
    - Same Pillar Bonus is 3.0.
    """

    def __init__(self):
        super().__init__()
        self.id = "A-01"
        self.name = "正官格 (Direct Officer)"
        self.type = "ORDER"

    def evaluate(self, chart, vectors, params) -> PatternResult:
        # 0. V2.6 物理量提取
        # 注意：这里的 vectors 应该已经由底层引擎应用了 V2.6 的非线性算法
        self_energy = vectors.get("self")
        officer_energy = vectors.get("officer")
        wealth_energy = vectors.get("wealth")
        resource_energy = vectors.get("resource")
        
        # ==========================================
        # 1. E-Gating (V2.6 High-Energy Thresholds)
        # ==========================================
        # 由于 V2.6 的自坐加成高达 3.0，身强的判定线大幅提升
        # 旧版 0.32 -> 新版 0.45 (Need calibration)
        GATE_THRESHOLD = 0.45
        
        if self_energy < GATE_THRESHOLD:
            # 即使身弱，如果有强印 (Resource) 转化，允许通过 (相神救应)
            # 印星在 V2.6 中如果通根，能量也会很高
            if resource_energy < 0.30:
                return PatternResult(
                    status="FAIL",
                    reason=f"Structure Collapse: Self energy {self_energy:.2f} < {GATE_THRESHOLD} (V2.6 Scale)."
                )
        
        # ==========================================
        # 2. Topology (L3 Protocol)
        # ==========================================
        sub_pattern = self._determine_topology(vectors)
        
        # ==========================================
        # 3. Safety Valve (L3 Protocol)
        # ==========================================
        safety = self._check_safety(sub_pattern, vectors)

        return PatternResult(
            status="ACTIVE",
            pattern_id=self.id,
            sub_pattern=sub_pattern,
            energy_level=officer_energy,
            safety_status=safety,
            physics_desc=f"V2.6 Quantum Field | {sub_pattern.get('physics', 'Unknown')}"
        )

    def _determine_topology(self, vectors):
        officer = vectors.get("officer")
        resource = vectors.get("resource")
        wealth = vectors.get("wealth")
        self_e = vectors.get("self")

        # SP_A01_DIRECTOR (官印)
        # V2.6 中，印星如果透干且有根，能量很容易 > 0.5
        if resource > 0.50 and (resource / officer) > 0.4:
            return {
                "id": "SP_A01_DIRECTOR",
                "name_cn": "官印双清",
                "name_en": "The Director",
                "physics": "Pressure -> Mass (Conversion)",
                "desc": "压力转化为权柄。V2.6 高能稳态。"
            }

        # SP_A01_EXECUTIVE (财官)
        # 需要极强的日主 (V2.6 Self > 0.65)
        if wealth > 0.60 and self_e > 0.65:
            return {
                "id": "SP_A01_EXECUTIVE",
                "name_cn": "财官双美",
                "name_en": "The Executive",
                "physics": "Work -> Pressure (Turbo)",
                "desc": "高能涡轮结构。Requires V2.6 High-G Mass."
            }

        return {
            "id": "SP_A01_GUARDIAN",
            "name_cn": "纯粹正官",
            "name_en": "The Guardian",
            "physics": "Conservative Field",
            "desc": "标准守恒场。"
        }
    
    def _check_safety(self, sub_pattern, vectors):
        """
        定义安全阀/冷却机制 V2.6
        """
        sp_id = sub_pattern['id']
        
        if sp_id == "SP_A01_EXECUTIVE":
            # V2.6 中，极高的压力需要极高的身强对抗
            if vectors.get("self") < 0.65:
                return {"status": "WARNING", "msg": "Turbo Overheat: Self energy insufficient for V2.6 Executive Mode."}
        
        if sp_id == "SP_A01_GUARDIAN":
            if vectors.get("output") > 0.4: # V2.6 Hurt Energy is also amplified
                 return {"status": "VULNERABLE", "msg": "Structure Fracture: High Output detected in Conservative Field."}

        return {"status": "STABLE", "msg": "System Nominal"}
