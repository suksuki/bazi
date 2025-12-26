
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from core.trinity.core.nexus.definitions import BaziParticleNexus, PhysicsConstants as PC, ArbitrationNexus as AN
from core.trinity.core.engines.synthetic_bazi_engine import SyntheticBaziEngine

# GEO Element Affinity Map for Field Correction
GEO_ELEMENT_MAP = {
    "Fire": {"Fire": 1.15, "Wood": 1.1, "Earth": 1.05, "Metal": 0.9, "Water": 0.85},
    "Water": {"Water": 1.15, "Metal": 1.1, "Wood": 1.05, "Fire": 0.85, "Earth": 0.9},
    "Wood": {"Wood": 1.15, "Water": 1.1, "Fire": 1.05, "Metal": 0.85, "Earth": 0.9},
    "Metal": {"Metal": 1.15, "Earth": 1.1, "Water": 1.05, "Wood": 0.85, "Fire": 0.9},
    "Earth": {"Earth": 1.15, "Fire": 1.1, "Metal": 1.05, "Water": 0.85, "Wood": 0.9},
    "Neutral": {"Fire": 1.0, "Water": 1.0, "Wood": 1.0, "Metal": 1.0, "Earth": 1.0},
    "Fire/Earth": {"Fire": 1.12, "Earth": 1.1, "Wood": 1.0, "Metal": 0.92, "Water": 0.88},
    "Water/Metal": {"Water": 1.12, "Metal": 1.1, "Wood": 1.0, "Fire": 0.88, "Earth": 0.95},
    "Fire/Water": {"Fire": 1.08, "Water": 1.08, "Wood": 1.0, "Metal": 0.95, "Earth": 0.95},
    "Water/Earth": {"Water": 1.1, "Earth": 1.08, "Metal": 1.0, "Fire": 0.9, "Wood": 0.92},
    "Water/Fire": {"Water": 1.08, "Fire": 1.08, "Wood": 1.0, "Metal": 0.95, "Earth": 0.95},
    "Metal/Earth": {"Metal": 1.12, "Earth": 1.1, "Water": 1.0, "Wood": 0.88, "Fire": 0.92},
    "Metal/Water": {"Metal": 1.1, "Water": 1.1, "Earth": 1.0, "Wood": 0.88, "Fire": 0.9},
    "Water/Wood": {"Water": 1.1, "Wood": 1.1, "Fire": 1.0, "Metal": 0.88, "Earth": 0.9},
    "Fire/Wood": {"Fire": 1.12, "Wood": 1.1, "Earth": 1.0, "Metal": 0.88, "Water": 0.9},
}

class PatternScout:
    """
    🔍 PatternScout (ASE Phase 5)
    
    Identifies specific topological Bazi patterns from batch data
    or guides the generator to find them.
    """
    
    def __init__(self, engine: Optional[SyntheticBaziEngine] = None):
        self.engine = engine or SyntheticBaziEngine()
        self.logger = logging.getLogger("PatternScout")

    def scout_pattern(self, pattern_id: str, sample_size: int = 518400, progress_callback=None) -> List[Dict[str, Any]]:
        """
        Pragmatic Universal Scout: 518,400 samples.
        Strictly filters for 'Stress Structural' SGJG.
        """
        found = []
        gen = self.engine.generate_all_bazi()
        
        # Stats for pragmatic reporting
        stats = {"fatal_count": 0, "super_fluid_count": 0, "matched": 0}
        
        # Reporting interval: every 1% (approx 5,000 samples)
        report_interval = max(sample_size // 100, 5000)
        
        for i in range(sample_size):
            try:
                chart = next(gen)
            except StopIteration:
                break
                
            match_data = self._deep_audit(chart, pattern_id)
            if match_data:
                found.append(match_data)
                stats["matched"] += 1
                if match_data["category"] == "必死断裂 (Fatal)":
                    stats["fatal_count"] += 1
                if "超流" in match_data["category"]:
                    stats["super_fluid_count"] += 1
            
            if progress_callback and i % report_interval == 0:
                progress_callback(i, sample_size, stats)
        
        # Sort by Stress Index for the elite PGB list
        if found and "stress" in found[0]:
            found.sort(key=lambda x: float(x.get("stress", 0)), reverse=True)
            
        if progress_callback:
            progress_callback(sample_size, sample_size, stats)
            
        return found

    def _deep_audit(self, chart, pattern_id, geo_context=None):
        """[V14.9.5] Deep audit wrapper with Global Logic Registry integration."""
        if len(chart) < 4: return None
        
        # [V4.2.6] 全面集成全局注册中心
        from core.logic_registry import LogicRegistry
        registry = LogicRegistry()
        registry_full_id, logic_ids = registry.resolve_logic_id(pattern_id)
        
        # 记录审计元数据 (向下兼容)
        # 如果 logic_ids 为空，回退为输入 ID
        main_logic_id = logic_ids[0] if logic_ids else pattern_id
        
        # 执行核心物理逻辑
        result = self._execute_audit_logic(chart, main_logic_id, geo_context)
        
        # [V4.2.6] 统一注入 ID 身份标识与溯源元数据
        if result and isinstance(result, dict):
            result["registry_id"] = registry_full_id
            result["pattern_id"] = main_logic_id
            result["audit_timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            result["logic_version"] = "4.2.6"
            
        return result

    def _execute_audit_logic(self, chart, pattern_id, geo_context=None):
        """[CORE] The actual physics computation logic."""
        # [Legacy Support]
        PATTERN_ID_ALIASES = {
            "CAI_GUAN_XIANG_SHENG": "CAI_GUAN_XIANG_SHENG_V4",
            "PGB_SUPER_FLUID_LOCK": "PGB_ULTRA_FLUID",
            "PGB_SUPERFLUID_LOCK": "PGB_ULTRA_FLUID",
        }
        pattern_id = PATTERN_ID_ALIASES.get(pattern_id, pattern_id)
        
        # Extract GEO correction factor if provided
        geo_element = "Neutral"
        geo_factor = 1.0
        if geo_context:
            geo_element = geo_context.get("element", "Neutral")
            geo_factor = geo_context.get("factor", 1.0)
        geo_mult = GEO_ELEMENT_MAP.get(geo_element, GEO_ELEMENT_MAP["Neutral"])
        
        dm = chart[2][0]
        month_branch = chart[1][1]
        stems = [p[0] for p in chart]
        branches = [p[1] for p in chart]
        
        # [V4.2.6] 环境变量标准提取
        luck_p = geo_context.get("luck_pillar", "甲子") if geo_context else "甲子"
        annual_p = geo_context.get("annual_pillar", "甲子") if geo_context else "甲子"
        
        ten_gods = [BaziParticleNexus.get_shi_shen(s, dm) for s in stems]
        
        if pattern_id == "SHANG_GUAN_JIAN_GUAN":
            # [ASE PHASE 4.1] SGGG V4.1: Gate Breakdown Model
            # 保持向后兼容性封装
            luck_pillar = luck_p
            annual_pillar = annual_p

            # 1. Topology Screening (Natal Stems must have both SG and Officer)
            natal_tg = ten_gods[:4]
            if "伤官" not in natal_tg: return None
            if "正官" not in natal_tg: return None # Strictly Official Officer for V4.1

            STAGES = ["长生", "沐浴", "冠带", "临官", "帝旺", "衰", "病", "死", "墓", "绝", "胎", "养"]
            STAGE_MULT = {
                "长生": 1.5, "沐浴": 1.1, "冠带": 1.3, "临官": 2.0, "帝旺": 2.5,
                "衰": 1.0, "病": 0.7, "死": 0.4, "墓": 1.8, "绝": 0.2, "胎": 0.6, "养": 1.0
            }
            LIFE_STAGES = {
                "甲": ["亥", "子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌"],
                "乙": ["午", "巳", "辰", "卯", "寅", "丑", "子", "亥", "戌", "酉", "申", "未"],
                "丙": ["寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥", "子", "丑"],
                "丁": ["酉", "申", "未", "午", "巳", "辰", "卯", "寅", "丑", "子", "亥", "戌"],
                "戊": ["寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥", "子", "丑"],
                "己": ["酉", "申", "未", "午", "巳", "辰", "卯", "寅", "丑", "子", "亥", "戌"],
                "庚": ["巳", "午", "未", "申", "酉", "戌", "亥", "子", "丑", "寅", "卯", "辰"],
                "辛": ["子", "亥", "戌", "酉", "申", "未", "午", "巳", "辰", "卯", "寅", "丑"],
                "壬": ["申", "酉", "戌", "亥", "子", "丑", "寅", "卯", "辰", "巳", "午", "未"],
                "癸": ["卯", "寅", "丑", "子", "亥", "戌", "酉", "申", "未", "午", "巳", "辰"]
            }

            def get_stage(stem, branch):
                if stem not in LIFE_STAGES: return "衰"
                try:
                    idx = LIFE_STAGES[stem].index(branch)
                    return STAGES[idx]
                except: return "衰"

            # 2. Gate Stabilization (Luck_Officer_Reset - 0.70 Weight)
            officer_stems = [st for i, (st, br) in enumerate(chart[:4]) if ten_gods[i] == "正官"]
            sg_stems = [st for i, (st, br) in enumerate(chart[:4]) if ten_gods[i] == "伤官"]
            
            luck_branch = luck_pillar[1]
            o_stability_sum = 0
            for os in officer_stems:
                stage = get_stage(os, luck_branch)
                o_stability_sum += STAGE_MULT.get(stage, 1.0)
            
            # Add Wealth support from Luck if applicable
            luck_god = BaziParticleNexus.get_shi_shen(luck_pillar[0], dm)
            if luck_god in ["正财", "偏财"]:
                o_stability_sum *= 1.5 # Wealth Shunting

            o_stabilization = (o_stability_sum / len(officer_stems) if officer_stems else 1.0) * 0.7

            # 3. Shang Guan Kinetic (Luck_SG_Reset)
            sg_kinetic_sum = 0
            for ss in sg_stems:
                stage = get_stage(ss, luck_branch)
                sg_kinetic_sum += STAGE_MULT.get(stage, 1.0)
            sg_kinetic = (sg_kinetic_sum / len(sg_stems) if sg_stems else 1.0) * 0.7

            # 4. Phase Pulsing (Annual_Phase_引动 - 0.25 Weight)
            phase_interference = 1.0
            STEM_COMBINES = {"甲己", "己甲", "乙庚", "庚乙", "丙辛", "辛丙", "丁壬", "壬丁", "戊癸", "癸戊"}
            
            # [Stem_Bonding_Trap]
            is_trap = False
            for ss in sg_stems:
                if (ss + annual_pillar[0]) in STEM_COMBINES:
                    is_trap = True
            
            for os in officer_stems:
                if (os + annual_pillar[0]) in STEM_COMBINES:
                    phase_interference *= 1.8 # Officer hijacked

            # 5. Critical Kernels
            # [Vault_Clash_Overflow]
            is_vault_overflow = False
            CLASHES = {"子午", "午子", "丑未", "未丑", "寅申", "申寅", "卯酉", "酉卯", "辰戌", "戌辰", "巳亥", "亥巳"}
            for i in range(4):
                br = branches[i]
                if (annual_pillar[1] + br) in CLASHES:
                    # Check if branch contains hidden Officer and is a 'Vault'
                    hidden = BaziParticleNexus.get_branch_weights(br)
                    if any(BaziParticleNexus.get_shi_shen(hs, dm) == "正官" for hs, w in hidden):
                        if get_stage(dm, br) == "墓":
                            is_vault_overflow = True

            # [Reverse_SG_Collapse]
            is_reverse_collapse = False
            sg_elem = BaziParticleNexus.STEMS[sg_stems[0]][0] if sg_stems else "Neutral"
            TRI_COMBINES = {"Wood": ["亥", "卯", "未"], "Fire": ["寅", "午", "戌"], "Metal": ["巳", "酉", "丑"], "Water": ["申", "子", "辰"]}
            tri_members = TRI_COMBINES.get(sg_elem, [])
            if all(m in branches for m in tri_members):
                is_reverse_collapse = True

            # 6. SAI Calculation (Breakdown Index)
            # Base logic: SG Kinetic vs Officer Stabilization
            # Ideal is high stability, low SG kinetic
            ratio = sg_kinetic / max(0.1, o_stabilization)
            sai = ratio * phase_interference * geo_factor
            
            if is_trap: sai *= 1.5
            if is_vault_overflow: sai *= 3.0 # Underground detonation
            if is_reverse_collapse: sai *= 2.0 # Field wide burnout

            # 7. Status Categories
            if sai > 8.0: category = "GATE_VAPORIZED (栅极气化/毁灭击穿)"
            elif sai > 4.0: category = "LOGIC_CIRCUIT_FAIL (逻辑失效/重度击穿)"
            elif sai > 1.5: category = "GATE_LEAKAGE (栅极漏电/中度干扰)"
            else: category = "STABLE_CONTROL (控制稳态)"

            return {
                "chart": chart,
                "category": category,
                "sai": f"{sai:.2f}",
                "charge_density": f"{sg_kinetic:.2f}",
                "gate_stability": f"{o_stabilization:.2f}",
                "is_vault_burst": "YES" if is_vault_overflow else "NO",
                "is_trap": "YES" if is_trap else "NO",
                "label": " ".join([f"{p[0]}{p[1]}" for p in chart]),
                "audit_mode": "SGGG_V4.1_GATE_BREAKDOWN",
                "topic_name": "伤官见官 (SGGG)",
                "stress": f"{sai:.2f}"
            }

        if pattern_id == "SHANG_GUAN_PEI_YIN":
            # [ASE PHASE 4.1] SGPY V4.1: Band-Stop Filtering Model
            luck_pillar = chart[4] if len(chart) >= 5 else ('', '')
            annual_pillar = chart[5] if len(chart) >= 6 else ('', '')

            # 1. Topology Screening (Natal Stems must have SG and Resource)
            natal_tg = ten_gods[:4]
            if "伤官" not in natal_tg: return None
            if not any(tg in ["正印", "偏印"] for tg in natal_tg): return None

            STAGES = ["长生", "沐浴", "冠带", "临官", "帝旺", "衰", "病", "死", "墓", "绝", "胎", "养"]
            STAGE_MULT = {
                "长生": 1.5, "沐浴": 1.1, "冠带": 1.3, "临官": 2.0, "帝旺": 2.5,
                "衰": 1.0, "病": 0.7, "死": 0.4, "墓": 1.8, "绝": 0.2, "胎": 0.6, "养": 1.0
            }
            LIFE_STAGES = {
                "甲": ["亥", "子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌"],
                "乙": ["午", "巳", "辰", "卯", "寅", "丑", "子", "亥", "戌", "酉", "申", "未"],
                "丙": ["寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥", "子", "丑"],
                "丁": ["酉", "申", "未", "午", "巳", "辰", "卯", "寅", "丑", "子", "亥", "戌"],
                "戊": ["寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥", "子", "丑"],
                "己": ["酉", "申", "未", "午", "巳", "辰", "卯", "寅", "丑", "子", "亥", "戌"],
                "庚": ["巳", "午", "未", "申", "酉", "戌", "亥", "子", "丑", "寅", "卯", "辰"],
                "辛": ["子", "亥", "戌", "酉", "申", "未", "午", "巳", "辰", "卯", "寅", "丑"],
                "壬": ["申", "酉", "戌", "亥", "子", "丑", "寅", "卯", "辰", "巳", "午", "未"],
                "癸": ["卯", "寅", "丑", "子", "亥", "戌", "酉", "申", "未", "午", "巳", "辰"]
            }

            def get_stage(stem, branch):
                if stem not in LIFE_STAGES: return "衰"
                try:
                    idx = LIFE_STAGES[stem].index(branch)
                    return STAGES[idx]
                except: return "衰"

            # 2. Constraint Field (Yin Capacity)
            yin_stems = [st for i, (st, br) in enumerate(chart[:4]) if ten_gods[i] in ["正印", "偏印"]]
            sg_stems = [st for i, (st, br) in enumerate(chart[:4]) if ten_gods[i] == "伤官"]
            
            luck_branch = luck_pillar[1]
            yin_field_sum = 0
            for ys in yin_stems:
                stage = get_stage(ys, luck_branch)
                yin_field_sum += STAGE_MULT.get(stage, 1.0)
            
            # Rooting Impedance Check (Natal Roots)
            yin_roots = 0
            for ys in yin_stems:
                yin_elem = BaziParticleNexus.STEMS[ys][0]
                for br in branches:
                    hidden = BaziParticleNexus.get_branch_weights(br)
                    if any(BaziParticleNexus.STEMS[hs][0] == yin_elem for hs, w in hidden):
                        yin_roots += 1
            
            # Impedance Factor: If no roots, capacity is halved
            impedance_factor = 1.0 if yin_roots > 0 else 0.5
            yin_capacity = (yin_field_sum / len(yin_stems) if yin_stems else 1.0) * 0.7 * impedance_factor
            
            # 3. Charge Flow (SG Kinetic)
            sg_kinetic_sum = 0
            for ss in sg_stems:
                stage = get_stage(ss, luck_branch)
                sg_kinetic_sum += STAGE_MULT.get(stage, 1.0)
            sg_kinetic = (sg_kinetic_sum / len(sg_stems) if sg_stems else 1.0) * 0.7

            # 4. Full-Factor Interference (V4.1)
            interference = 1.0
            COMBINES = {"甲己", "己甲", "乙庚", "庚乙", "丙辛", "辛丙", "丁壬", "壬丁", "戊癸", "癸戊"}
            
            # [Stem_Interference]: Yin bound in stems
            is_bound = False
            for ys in yin_stems:
                if (ys + annual_pillar[0]) in COMBINES:
                    is_bound = True
                    interference *= 2.5 # Constraint force 1.0 -> 0.4 effectively via multiplier
            
            # [Vault_Dynamics]: 
            is_vault_open = False
            CLASHES = {"子午", "午子", "丑未", "未丑", "寅申", "申寅", "卯酉", "酉卯", "辰戌", "戌辰", "巳亥", "亥巳"}
            for i in range(4):
                br = branches[i]
                if (annual_pillar[1] + br) in CLASHES:
                    hidden = BaziParticleNexus.get_branch_weights(br)
                    if any(BaziParticleNexus.get_shi_shen(hs, dm) in ["正印", "偏印"] for hs, w in hidden):
                        # Opened Yin Vault
                        is_vault_open = True
                        interference *= 0.6 # Backup power online
                
            # [Branch_Reactor]: SG saturation (e.g. Tri-combo of SG element)
            is_saturated = False
            sg_elem = BaziParticleNexus.STEMS[sg_stems[0]][0] if sg_stems else "Neutral"
            TRI_COMBINES = {"Wood": ["亥", "卯", "未"], "Fire": ["寅", "午", "戌"], "Metal": ["巳", "酉", "丑"], "Water": ["申", "子", "辰"]}
            if all(m in branches for m in TRI_COMBINES.get(sg_elem, [])):
                if sg_kinetic > 2.5 * yin_capacity:
                    is_saturated = True
                    interference *= 3.0 # Reverse Collapse

            # 5. Stability Audit (SAI)
            # Ideal constraint: Yin capacity slightly greater than SG kinetic
            ratio = sg_kinetic / max(0.1, yin_capacity)
            sai = abs(ratio - 1.0) * interference * geo_factor

            # 6. Status Categories (V4.1)
            if is_saturated: category = "REVERSE_COLLAPSE (反向坍缩/气化)"
            elif is_bound: category = "CONSTRAINT_BOUND (约束缠绕/失效)"
            elif is_vault_open and sai < 0.8: category = "SUPER_STABLE (备用电源/稳态)"
            elif 0.8 <= ratio <= 1.5 and sai < 1.0: category = "BAND_STOP_OK (带阻滤波/稳态)"
            elif ratio > 2.0: category = "CHARGE_OVERFLOW (电荷过载/狂暴)"
            else: category = "UNSTABLE_CONSTRAINT (非稳态约束)"

            return {
                "chart": chart,
                "category": category,
                "sai": f"{sai:.2f}",
                "ratio": f"{ratio:.2f}",
                "yin_capacity": f"{yin_capacity:.2f}",
                "sg_kinetic": f"{sg_kinetic:.2f}",
                "is_bound": "YES" if is_bound else "NO",
                "is_vault_open": "YES" if is_vault_open else "NO",
                "label": " ".join([f"{p[0]}{p[1]}" for p in chart]),
                "audit_mode": "SGPY_V4.1_BAND_STOP_MODEL",
                "topic_name": "伤官配印 (SGPY)",
                "stress": f"{sai:.2f}"
            }

        if pattern_id == "SHANG_GUAN_SHANG_JIN":
            # ============================================================
            # [ASE PHASE 4.2] SGSJ V4.2: Plasma Vaporization Field Model
            # 等离子体气化场模型 (Plasma Vaporization Field)
            # 
            # 核心思想变更：从"静态真空逻辑"升级为"动态饱和攻击模型"
            # - 不再要求原局完全无官杀，而是要求伤官能级压制比 >= 12:1
            # - 当任何官杀粒子进入时，被高能伤官场"气化/相变"
            # ============================================================
            luck_pillar = chart[4] if len(chart) >= 5 else ('', '')
            annual_pillar = chart[5] if len(chart) >= 6 else ('', '')
            
            # ===== 维度 A: 基础拓扑筛选 =====
            # 必须有伤官存在（攻击源）
            if "伤官" not in ten_gods: return None
            
            # 原局天干不能有正官（七杀可以存在，但会被气化）
            if "正官" in ten_gods[:4]: return None
            
            # ===== 维度 B: 能量统计 =====
            sg_total = 0.0  # 伤官总能量
            guan_total = 0.0  # 官杀总能量（包含藏干）
            dm_support = 0.0  # 日主电源强度（印星+比劫）
            wealth_load = 0.0  # 财星泄放负载
            
            for i in range(4):
                st, br = chart[i]
                tg = ten_gods[i]
                
                # 天干能量 (权重 3.0)
                if tg == "伤官": sg_total += 3.0
                elif tg == "七杀": guan_total += 3.0
                elif tg in ["正印", "偏印"]: dm_support += 3.0
                elif tg in ["比肩", "劫财"]: dm_support += 2.0
                elif tg in ["正财", "偏财"]: wealth_load += 3.0
                
                # 藏干能量 (权重按藏干本气比例)
                hidden = BaziParticleNexus.get_branch_weights(br)
                for hs, w in hidden:
                    hg = BaziParticleNexus.get_shi_shen(hs, dm)
                    energy = w / 10.0
                    if hg == "伤官": sg_total += energy
                    elif hg in ["正官", "七杀"]: guan_total += energy
                    elif hg in ["正印", "偏印"]: dm_support += energy
                    elif hg in ["比肩", "劫财"]: dm_support += energy * 0.7
                    elif hg in ["正财", "偏财"]: wealth_load += energy
            
            # ===== 维度 C: 能级压制比计算 (Suppression Ratio) =====
            # 公式: SR = E_伤官 / E_官杀
            # 临界值: SR >= 12 (信噪比 20dB 以上) → 官杀被完全掩蔽
            suppression_ratio = sg_total / max(0.01, guan_total)
            is_vaporized = suppression_ratio >= 12.0  # 气化态判定
            
            # 如果压制比不够，且官杀能量显著，则不构成伤尽
            if suppression_ratio < 3.0 and guan_total > 1.0:
                return None  # 官杀未被压制，不构成伤尽格局
            
            # ===== 维度 D: 日主电源稳定性 =====
            # 公式: Source_Stability = E_印比 / E_伤官
            # 必须有足够内能支撑高能耗的气化场
            source_stability = dm_support / max(0.1, sg_total)
            is_self_burn = source_stability < 0.3  # 日主电源不足导致自燃
            
            # ===== 维度 E: 动态拦截能力 (流年官杀突入模拟) =====
            annual_god = BaziParticleNexus.get_shi_shen(annual_pillar[0], dm) if annual_pillar[0] else ""
            luck_god = BaziParticleNexus.get_shi_shen(luck_pillar[0], dm) if luck_pillar[0] else ""
            
            # 流年/大运官杀突入
            incoming_guan = 0.0
            if annual_god in ["正官", "七杀"]: incoming_guan += 3.5
            if luck_god in ["正官", "七杀"]: incoming_guan += 2.5
            
            # 拦截判定: 伤官是否能气化流年官杀
            intercept_ratio = sg_total / max(0.1, incoming_guan) if incoming_guan > 0 else 99.0
            intercept_success = intercept_ratio >= 2.0  # 2:1 即可拦截
            
            # ===== 维度 F: SAI 计算 (应力指数) =====
            # 基础 SAI = 系统稳定时接近 0
            # 风险 SAI = 拦截失败或自燃时增加
            base_sai = 0.1 / max(0.1, suppression_ratio / 12.0)  # 压制比越高，SAI越低
            
            if is_self_burn:
                base_sai *= 5.0  # 自燃风险
            if not intercept_success and incoming_guan > 0:
                base_sai *= (3.0 + incoming_guan)  # 拦截失败风险
            
            # 财星泄放 (正向: 伤官生财，能量有出路)
            wealth_factor = 1.0 / (1.0 + wealth_load * 0.3)
            sai = base_sai * wealth_factor * geo_factor
            
            # ===== 维度 G: 状态分类 =====
            if is_vaporized and source_stability >= 0.5:
                if incoming_guan > 0 and not intercept_success:
                    category = "VAPORIZATION_OVERLOAD (气化过载/拦截失败)"
                elif incoming_guan > 0 and intercept_success:
                    category = "PLASMA_SHIELD_ACTIVE (等离子护盾激活/气化成功)"
                else:
                    category = "VACUUM_SUPERCONDUCTOR (真空超导/纯净气化场)"
            elif is_self_burn:
                category = "SOURCE_BURNOUT (电源枯竭/自燃)"
            elif suppression_ratio >= 6.0:
                category = "PARTIAL_VAPORIZATION (部分气化/亚临界态)"
            else:
                category = "UNSTABLE_FIELD (不稳定场态)"
            
            return {
                "chart": chart,
                "category": category,
                "sai": f"{sai:.2f}",
                "suppression_ratio": f"{suppression_ratio:.1f}:1",
                "sg_total": f"{sg_total:.2f}",
                "guan_total": f"{guan_total:.2f}",
                "source_stability": f"{source_stability:.2f}",
                "is_vaporized": "YES" if is_vaporized else "NO",
                "is_self_burn": "YES" if is_self_burn else "NO",
                "incoming_guan": f"{incoming_guan:.1f}",
                "intercept_success": "YES" if intercept_success else "NO",
                "intercept_ratio": f"{intercept_ratio:.1f}:1",
                "wealth_load": f"{wealth_load:.2f}",
                "label": " ".join([f"{p[0]}{p[1]}" for p in chart]),
                "audit_mode": "SGSJ_V4.2_PLASMA_VAPORIZATION",
                "topic_name": "伤官伤尽 (SGSJ)",
                "stress": f"{sai:.2f}"
            }
            

        if pattern_id == "SHI_SHEN_ZHI_SHA":
            # ============================================================
            # [ASE PHASE 5.1] SSZS V5.1: 能级压制拦截模型
            # V5.1 升级: 从"透干硬限制"改为"食杀能级压制比"
            # 允许食神或七杀在藏干中存在，计算纯度系数
            # ============================================================
            luck_pillar = chart[4] if len(chart) >= 5 else ('', '')
            annual_pillar = chart[5] if len(chart) >= 6 else ('', '')

            # 1. 能量统计 (包含天干和藏干)
            shi_shen_total = 0.0  # 食神能量
            shang_guan_total = 0.0  # 伤官能量
            qi_sha_total = 0.0  # 七杀能量
            
            for i in range(4):
                st, br = chart[i]
                tg = ten_gods[i]
                
                # 天干能量
                if tg == "食神": shi_shen_total += 3.0
                elif tg == "伤官": shang_guan_total += 3.0
                elif tg == "七杀": qi_sha_total += 3.0
                
                # 藏干能量
                hidden = BaziParticleNexus.get_branch_weights(br)
                for hs, w in hidden:
                    hg = BaziParticleNexus.get_shi_shen(hs, dm)
                    energy = w / 10.0
                    if hg == "食神": shi_shen_total += energy
                    elif hg == "伤官": shang_guan_total += energy
                    elif hg == "七杀": qi_sha_total += energy
            
            # 2. 触发条件：必须有食神和七杀（天干或藏干）
            if shi_shen_total < 1.0: return None  # 食神能量不足
            if qi_sha_total < 1.0: return None  # 七杀能量不足
            
            # 3. 纯度系数计算: Purity = E_食神 / (E_食神 + E_伤官)
            purity = shi_shen_total / max(0.1, shi_shen_total + shang_guan_total)

            STAGES = ["长生", "沐浴", "冠带", "临官", "帝旺", "衰", "病", "死", "墓", "绝", "胎", "养"]
            STAGE_MULT = {
                "长生": 1.5, "沐浴": 1.1, "冠带": 1.3, "临官": 2.0, "帝旺": 2.5,
                "衰": 1.0, "病": 0.7, "死": 0.4, "墓": 1.8, "绝": 0.2, "胎": 0.6, "养": 1.0
            }
            LIFE_STAGES = {
                "甲": ["亥", "子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌"],
                "乙": ["午", "巳", "辰", "卯", "寅", "丑", "子", "亥", "戌", "酉", "申", "未"],
                "丙": ["寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥", "子", "丑"],
                "丁": ["酉", "申", "未", "午", "巳", "辰", "卯", "寅", "丑", "子", "亥", "戌"],
                "戊": ["寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥", "子", "丑"],
                "己": ["酉", "申", "未", "午", "巳", "辰", "卯", "寅", "丑", "子", "亥", "戌"],
                "庚": ["巳", "午", "未", "申", "酉", "戌", "亥", "子", "丑", "寅", "卯", "辰"],
                "辛": ["子", "亥", "戌", "酉", "申", "未", "午", "巳", "辰", "卯", "寅", "丑"],
                "壬": ["申", "酉", "戌", "亥", "子", "丑", "寅", "卯", "辰", "巳", "午", "未"],
                "癸": ["卯", "寅", "丑", "子", "亥", "戌", "酉", "申", "未", "午", "巳", "辰"]
            }

            def get_stage(stem, branch):
                if stem not in LIFE_STAGES: return "衰"
                try:
                    idx = LIFE_STAGES[stem].index(branch)
                    return STAGES[idx]
                except: return "衰"

            # 2. Interceptor Efficiency (Luck_Shi_Reset - 0.70 Weight)
            shi_stems = [st for i, (st, br) in enumerate(chart[:4]) if ten_gods[i] == "食神"]
            sha_stems = [st for i, (st, br) in enumerate(chart[:4]) if ten_gods[i] == "七杀"]
            
            luck_branch = luck_pillar[1]
            shi_power_sum = 0
            for ss in shi_stems:
                stage = get_stage(ss, luck_branch)
                shi_power_sum += STAGE_MULT.get(stage, 1.0)
            
            # 3. Sha Momentum Reset (Luck_Sha_Reset)
            sha_kinetic_sum = 0
            for ss in sha_stems:
                stage = get_stage(ss, luck_branch)
                sha_kinetic_sum += STAGE_MULT.get(stage, 1.0)
            
            shi_interceptor = (shi_power_sum / len(shi_stems) if shi_stems else 1.0) * 0.7
            sha_kinetic = (sha_kinetic_sum / len(sha_stems) if sha_stems else 1.0) * 0.7

            # 4. Phase Interference (Annual Pulse - 0.25 Weight)
            phase_interference = 1.0
            STEM_COMBINES = {"甲己", "己甲", "乙庚", "庚乙", "丙辛", "辛丙", "丁壬", "壬丁", "戊癸", "癸戊"}
            
            # [Guidance_Jamming]: Shi Shen being combined
            is_jammed = False
            for ss in shi_stems:
                if (ss + annual_pillar[0]) in STEM_COMBINES:
                    is_jammed = True
                    phase_interference *= 2.5 # Interceptor blinded
            
            # [Secondary_Circuit_Failure]: Xiao Shen Duo Shi interference
            annual_god = BaziParticleNexus.get_shi_shen(annual_pillar[0], dm)
            is_circuit_fail = False
            if annual_god in ["正印", "偏印"]:
                is_circuit_fail = True
                phase_interference *= 2.0 # Radar power off

            # [Vault_Ammunition_Lock]: Sha or Shi in Vault
            is_sha_burst = False
            CLASHES = {"子午", "午子", "丑未", "未丑", "寅申", "申寅", "卯酉", "酉卯", "辰戌", "戌辰", "巳亥", "亥巳"}
            for i in range(4):
                br = branches[i]
                if (annual_pillar[1] + br) in CLASHES:
                    hidden = BaziParticleNexus.get_branch_weights(br)
                    if any(BaziParticleNexus.get_shi_shen(hs, dm) == "七杀" for hs, w in hidden):
                        if get_stage(dm, br) == "墓":
                            is_sha_burst = True
                            phase_interference *= 3.0 # Nuclear cook-off

            # [Superconducting_Response]: Branch combinations for Shi
            is_superactive = False
            shi_elem = BaziParticleNexus.STEMS[shi_stems[0]][0] if shi_stems else "Neutral"
            TRI_COMBINES = {"Wood": ["亥", "卯", "未"], "Fire": ["寅", "午", "戌"], "Metal": ["巳", "酉", "丑"], "Water": ["申", "子", "辰"]}
            tri_members = TRI_COMBINES.get(shi_elem, [])
            if all(m in branches for m in tri_members):
                is_superactive = True
                phase_interference *= 0.5 # Continuous beam lock

            # 5. Lock-on Intercept Algorithm
            # Target ratio: 1.10 (Golden Intercept)
            ratio = sha_kinetic / max(0.1, shi_interceptor)
            tuning_error = abs(ratio - 1.10)
            
            # [V5.1] 引入纯度系数: 纯度越低，SAI越高
            purity_penalty = 1.0 / max(0.3, purity)  # 纯度<0.5时开始惩罚
            sai = tuning_error * phase_interference * purity_penalty * geo_factor

            # 6. Status Categories
            if is_sha_burst: category = "KINETIC_OVERLOAD (殉爆/拦截崩溃)"
            elif is_jammed: category = "GUIDANCE_LOST (拦截致盲/失控)"
            elif is_circuit_fail: category = "RADAR_OFFLINE (绝缘崩溃/雷达离线)"
            elif purity < 0.5: category = "IMPURE_INTERCEPT (食伤混杂/相位干涉)"
            elif tuning_error < 0.2 and phase_interference < 1.0: category = "PRECISE_INTERCEPT (定点拦截/完美制导)"
            elif ratio > 2.0: category = "INTERCEPT_FAILURE (拦截动能不足)"
            else: category = "SATURATED_DEFENSE (饱和防御态)"

            return {
                "chart": chart,
                "category": category,
                "sai": f"{sai:.2f}",
                "intercept_ratio": f"{ratio:.2f}",
                "interceptor_power": f"{shi_interceptor:.2f}",
                "target_momentum": f"{sha_kinetic:.2f}",
                "shi_shen_total": f"{shi_shen_total:.2f}",
                "shang_guan_total": f"{shang_guan_total:.2f}",
                "qi_sha_total": f"{qi_sha_total:.2f}",
                "purity": f"{purity*100:.1f}%",
                "is_burst": "YES" if is_sha_burst else "NO",
                "is_jammed": "YES" if is_jammed else "NO",
                "label": " ".join([f"{p[0]}{p[1]}" for p in chart]),
                "audit_mode": "SSZS_V5.1_PURITY_INTERCEPT",
                "topic_name": "食神制杀 (SSZS)",
                "stress": f"{sai:.2f}"
            }

        # ============================================================
        # [V1.0] YRJS 羊刃架杀模型 (Yang Ren Jia Sha Fusion Model)
        # 基于 2,127 纯净样本验证，黄金比 1.32
        # 核心: 月令帝旺 + 七杀透干 - 无印无食
        # ============================================================
        if pattern_id == "YANG_REN_JIA_SHA":
            # [ASE PHASE 4.1] YRJS V4.1: Tokamak Constraint Model
            luck_pillar = chart[4] if len(chart) >= 5 else ('', '')
            annual_pillar = chart[5] if len(chart) >= 6 else ('', '')
            
            YANG_REN_MAP = {'甲': '卯', '乙': '寅', '丙': '午', '丁': '巳', '戊': '午', '己': '巳', '庚': '酉', '辛': '申', '壬': '子', '癸': '亥'}
            STAGES = ["长生", "沐浴", "冠带", "临官", "帝旺", "衰", "病", "死", "墓", "绝", "胎", "养"]
            STAGE_MULT = {"长生": 1.5, "沐浴": 1.1, "冠带": 1.3, "临官": 2.0, "帝旺": 2.5, "衰": 1.0, "病": 0.7, "死": 0.4, "墓": 1.8, "绝": 0.2, "胎": 0.6, "养": 1.0}
            LIFE_STAGES = {
                "甲": ["亥", "子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌"],
                "乙": ["午", "巳", "辰", "卯", "寅", "丑", "子", "亥", "戌", "酉", "申", "未"],
                "丙": ["寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥", "子", "丑"],
                "丁": ["酉", "申", "未", "午", "巳", "辰", "卯", "寅", "丑", "子", "亥", "戌"],
                "戊": ["寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥", "子", "丑"],
                "己": ["酉", "申", "未", "午", "巳", "辰", "卯", "寅", "丑", "子", "亥", "戌"],
                "庚": ["巳", "午", "未", "申", "酉", "戌", "亥", "子", "丑", "寅", "卯", "辰"],
                "辛": ["子", "亥", "戌", "酉", "申", "未", "午", "巳", "辰", "卯", "寅", "丑"],
                "壬": ["申", "酉", "戌", "亥", "子", "丑", "寅", "卯", "辰", "巳", "午", "未"],
                "癸": ["卯", "寅", "丑", "子", "亥", "戌", "酉", "申", "未", "午", "巳", "辰"]
            }

            def get_stage(stem, branch):
                if stem not in LIFE_STAGES: return "衰"
                try:
                    idx = LIFE_STAGES[stem].index(branch)
                    return STAGES[idx]
                except: return "衰"

            # 1. Topology Screening
            yang_ren = YANG_REN_MAP.get(dm)
            if month_branch != yang_ren: return None
            if "七杀" not in ten_gods: return None
            if "正官" in ten_gods: return None # Keep purity

            # 2. Magnetic Constraint Field (Luck_Sha_Reset - 0.70 Weight)
            sha_stems = [st for i, (st, br) in enumerate(chart) if ten_gods[i] == "七杀"]
            luck_branch = luck_pillar[1]
            sha_field_sum = 0
            for ss in sha_stems:
                stage = get_stage(ss, luck_branch)
                sha_field_sum += STAGE_MULT.get(stage, 1.0)
            sha_constraint = sha_field_sum / len(sha_stems) if sha_stems else 1.0
            
            # 3. Annual Phase Perturbation (0.25 Weight)
            phase_perturbation = 1.0
            CLASHES = {"子午", "午子", "丑未", "未丑", "寅申", "申寅", "卯酉", "酉卯", "辰戌", "戌辰", "巳亥", "亥巳"}
            # Clash on Yang Ren monthly branch causes plasma leakage
            if (annual_pillar[1] + month_branch) in CLASHES:
                phase_perturbation = 2.0 # Violent pulse

            # 4. Energy Summation
            e_blade = 5.0 + (sum(2.0 for b in branches if b == yang_ren) - 2.0)
            e_sha = sum(3.0 if ten_gods[i] == "七杀" else 0 for i in range(4))
            
            # Hidden Sha energy
            for i, (st, br) in enumerate(chart):
                weights = BaziParticleNexus.get_branch_weights(br)
                for h_stem, weight in weights:
                    h_god = BaziParticleNexus.get_shi_shen(h_stem, dm)
                    if h_god == "七杀": e_sha += (weight / 5.0)

            # Effective Field Strength
            b_constraint = e_sha * sha_constraint
            plasma_pressure = e_blade * (1.35 if (luck_pillar[1] == yang_ren) else 1.0)
            
            # SAI Calculation (Tokamak Stability Index)
            # Ideal ratio is near 1.32 (Golden Balance)
            ratio = plasma_pressure / (b_constraint or 0.1)
            sai = abs(ratio - 1.32) * phase_perturbation * geo_factor

            # 5. Critical Kernels V4.1
            # [Magnetic_Breakdown_Gamma]
            is_breakdown = False
            if ratio > 2.5: # Breakdown limit
                is_breakdown = True
                sai *= 3.0 # Severe Magnetic Leakage
            
            # [Tension_Coupling]: Stem Combine Optimization
            is_coupled = False
            COMBINES = {"甲己", "己甲", "乙庚", "庚乙", "丙辛", "辛丙", "丁壬", "壬丁", "戊癸", "癸戊"}
            # Check if Sha combines with Day Master or other particles to form stable pairing
            if any((ss + dm) in COMBINES for ss in sha_stems):
                is_coupled = True
                sai *= 0.5 # Superconducting state

            # Status Categories
            if is_breakdown: category = "MAGNETIC_BREAKDOWN (磁场击穿)"
            elif is_coupled and sai < 0.5: category = "SUPERCONDUCTING_FUSION (超导核聚变)"
            elif sai < 0.8: category = "STABLE_FUSION (稳态聚变)"
            elif sai < 1.8: category = "THERMAL_TURBULENCE (热扰动状态)"
            else: category = "CONTAINMENT_FAIL (约束失效)"

            return {
                "chart": chart,
                "category": category,
                "sai": f"{sai:.2f}",
                "e_blade": f"{plasma_pressure:.2f}",
                "e_sha": f"{b_constraint:.2f}",
                "ratio": f"{ratio:.2f}",
                "is_breakdown": "YES" if is_breakdown else "NO",
                "is_coupled": "YES" if is_coupled else "NO",
                "label": " ".join([f"{p[0]}{p[1]}" for p in chart]),
                "audit_mode": "YRJS_V4.1_TOKAMAK_MODEL"
            }


        # ============================================================
        # [V2.0] XSDS 枭神夺食模型 (Xiao Shen Duo Shi Circuit Break Model)
        # V2.0 增强: 地支冲克 + 合化转性 + 藏干能量
        # ============================================================
        if pattern_id == "XIAO_SHEN_DUO_SHI":
            # [ASE PHASE 4.1.3] XSDS V4.1.3: Quantum Superconductor Audit
            luck_pillar = chart[4] if len(chart) >= 5 else ('', '')
            annual_pillar = chart[5] if len(chart) >= 6 else ('', '')
            
            # --- V4.1.3 Constraints ---
            if "偏印" not in ten_gods: return None
            if "食神" not in ten_gods: return None
            
            # --- V4.1.3 Constants ---
            STAGES = ["长生", "沐浴", "冠带", "临官", "帝旺", "衰", "病", "死", "墓", "绝", "胎", "养"]
            STAGE_MULT = {
                "长生": 1.2, "沐浴": 1.0, "冠带": 1.3, "临官": 1.8, "帝旺": 2.2,
                "衰": 1.0, "病": 0.8, "死": 0.5, "墓": 2.5, "绝": 0.3, "胎": 0.7, "养": 1.0
            }
            LIFE_STAGES = {
                "甲": ["亥", "子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌"],
                "乙": ["午", "巳", "辰", "卯", "寅", "丑", "子", "亥", "戌", "酉", "申", "未"],
                "丙": ["寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥", "子", "丑"],
                "丁": ["酉", "申", "未", "午", "巳", "辰", "卯", "寅", "丑", "子", "亥", "戌"],
                "戊": ["寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥", "子", "丑"],
                "己": ["酉", "申", "未", "午", "巳", "辰", "卯", "寅", "丑", "子", "亥", "戌"],
                "庚": ["巳", "午", "未", "申", "酉", "戌", "亥", "子", "丑", "寅", "卯", "辰"],
                "辛": ["子", "亥", "戌", "酉", "申", "未", "午", "巳", "辰", "卯", "寅", "丑"],
                "壬": ["申", "酉", "戌", "亥", "子", "丑", "寅", "卯", "辰", "巳", "午", "未"],
                "癸": ["卯", "寅", "丑", "子", "亥", "戌", "酉", "申", "未", "午", "巳", "辰"]
            }

            def get_stage(stem, branch):
                if stem not in LIFE_STAGES: return "衰"
                try:
                    idx = LIFE_STAGES[stem].index(branch)
                    return STAGES[idx]
                except: return "衰"

            # 1. Xiao Field Strength (Luck Reset - 0.70 Weight)
            xiao_stems = [st for i, (st, br) in enumerate(chart) if ten_gods[i] == "偏印"]
            luck_branch = luck_pillar[1]
            x_stability_sum = 0
            for xs in xiao_stems:
                stage = get_stage(xs, luck_branch)
                mult = STAGE_MULT.get(stage, 1.0)
                if stage == "墓": mult *= 1.5 
                x_stability_sum += mult
            xiao_field = (x_stability_sum / len(xiao_stems) if xiao_stems else 1.0) * 0.7

            # 2. Phase Interrupt & Cancellation Logic
            phase_interference = 1.0
            CLASHES = {"子午", "午子", "丑未", "未丑", "寅申", "申寅", "卯酉", "酉卯", "辰戌", "戌辰", "巳亥", "亥巳"}
            COMBINES = {"子丑", "丑子", "寅亥", "亥寅", "卯戌", "戌卯", "辰酉", "酉辰", "巳申", "申巳", "午未", "未午"}
            
            food_positions = [i for i, tg in enumerate(ten_gods) if tg == "食神"]
            has_phase_cancel = False
            for pos in food_positions:
                p_branch = branches[pos]
                if (annual_pillar[1] + p_branch) in CLASHES:
                    # Check if there is a 'Combine' particle near to absorb the shock
                    is_absorbed = False
                    for b in branches:
                        if (p_branch + b) in COMBINES: is_absorbed = True
                    if is_absorbed:
                        phase_interference *= 1.15 # Absorbed
                        has_phase_cancel = True
                    else:
                        phase_interference *= 1.6 # Full Phasor Annihilation

            # 3. Energy Summation
            x_total = sum(3.5 if ten_gods[i] == "偏印" else 0 for i in range(4))
            s_total = sum(3.0 if ten_gods[i] == "食神" else 0 for i in range(4))
            w_total = sum(1.5 if ten_gods[i] in ["正财", "偏财"] else 0 for i in range(4))
            b_total = sum(2.0 if ten_gods[i] in ["比肩", "劫财"] else 0 for i in range(4))
            o_total = sum(1.0 if ten_gods[i] in ["正官", "七杀"] else 0 for i in range(4))

            # Impedance Buffer: Bi Jie + Officer Stabilizer
            # V4.1.3: Officer acts as a stabilizer if it constrains the 'Bi Jie' surplus
            o_stabilizer = 1.0 - (min(0.5, o_total * 0.15)) if o_total > 0 else 1.0
            buffer_factor = 1.0 / (1.0 + b_total * 0.5 * o_stabilizer)
            if o_total > 1.0: buffer_factor *= 0.9 # Officer stabilization effect

            # Vault Overflow detection
            is_vault_overflow = any(get_stage(xs, luck_branch) == "墓" for xs in xiao_stems)

            # 4. SAI Calculation
            sai = (x_total * xiao_field) / (max(0.1, s_total) * (1.0 + w_total * 0.4))
            sai *= phase_interference * buffer_factor * geo_factor

            # 5. Superconductor Audit (V4.1.3)
            is_superconductor = False
            if xiao_field > 1.2 and sai < 1.0: # Xiao Field base > 4.0 energy equivalent
                is_superconductor = True

            # Status Categories
            if sai > 5.5: category = "PHASE_ANNIHILATION (彻底断路)"
            elif sai > 3.5: category = "QUANTUM_WELL_OVERFLOW (溢出干扰)"
            elif is_superconductor: category = "STEADY_SIGNAL (超导稳态)"
            elif sai < 1.2: category = "STEADY_SIGNAL (信号稳态)"
            else: category = "SIGNAL_INTERFERENCE (信号遮蔽)"

            return {
                "chart": chart,
                "category": category,
                "sai": f"{sai:.2f}",
                "x_field": f"{xiao_field:.2f}",
                "phase": f"{phase_interference:.2f}",
                "is_superconductor": "YES" if is_superconductor else "NO",
                "is_phase_cancel": "YES" if has_phase_cancel else "NO",
                "buffer_eff": f"{(1.0 - buffer_factor)*100:.1f}%",
                "is_vault_overflow": "YES" if is_vault_overflow else "NO",
                "label": " ".join([f"{p[0]}{p[1]}" for p in chart]),
                "audit_mode": "XSDS_V4.1.3_SUPERCONDUCTOR"
            }



        # ============================================================
        # [V4.0] CGXS 财官相生模型 (Wealth-Officer Self-Exciting Gain System)
        # ============================================================
        if pattern_id == "CAI_GUAN_XIANG_SHENG_V4":
            # [ASE PHASE 4.1] CGXS V4.1: Closed-Loop Stabilized Power Supply Model
            luck_pillar = chart[4] if len(chart) >= 5 else ('', '')
            annual_pillar = chart[5] if len(chart) >= 6 else ('', '')

            # 1. Topology Screening (Natal Stems must have Wealth and Officer)
            natal_tg = ten_gods[:4]
            if "正官" not in natal_tg: return None
            if not any(tg in ["正财", "偏财"] for tg in natal_tg): return None
            
            STAGES = ["长生", "沐浴", "冠带", "临官", "帝旺", "衰", "病", "死", "墓", "绝", "胎", "养"]
            STAGE_MULT = {
                "长生": 1.5, "沐浴": 1.1, "冠带": 1.3, "临官": 2.0, "帝旺": 2.5,
                "衰": 1.0, "病": 0.7, "死": 0.4, "墓": 1.8, "绝": 0.2, "胎": 0.6, "养": 1.0
            }
            LIFE_STAGES = {
                "甲": ["亥", "子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌"],
                "乙": ["午", "巳", "辰", "卯", "寅", "丑", "子", "亥", "戌", "酉", "申", "未"],
                "丙": ["寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥", "子", "丑"],
                "丁": ["酉", "申", "未", "午", "巳", "辰", "卯", "寅", "丑", "子", "亥", "戌"],
                "戊": ["寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥", "子", "丑"],
                "己": ["酉", "申", "未", "午", "巳", "辰", "卯", "寅", "丑", "子", "亥", "戌"],
                "庚": ["巳", "午", "未", "申", "酉", "戌", "亥", "子", "丑", "寅", "卯", "辰"],
                "辛": ["子", "亥", "戌", "酉", "申", "未", "午", "巳", "辰", "卯", "寅", "丑"],
                "壬": ["申", "酉", "戌", "亥", "子", "丑", "寅", "卯", "辰", "巳", "午", "未"],
                "癸": ["卯", "寅", "丑", "子", "亥", "戌", "酉", "申", "未", "午", "巳", "辰"]
            }

            def get_stage(stem, branch):
                if stem not in LIFE_STAGES: return "衰"
                try:
                    idx = LIFE_STAGES[stem].index(branch)
                    return STAGES[idx]
                except: return "衰"

            # 2. Excitation Field (Luck_Officer_Reset - 0.70 Weight)
            officer_stems = [st for i, (st, br) in enumerate(chart[:4]) if ten_gods[i] == "正官"]
            wealth_stems = [st for i, (st, br) in enumerate(chart[:4]) if ten_gods[i] in ["正财", "偏财"]]
            
            luck_branch = luck_pillar[1]
            o_stability_sum = 0
            for os in officer_stems:
                stage = get_stage(os, luck_branch)
                o_stability_sum += STAGE_MULT.get(stage, 1.0)
            o_stabilization = (o_stability_sum / len(officer_stems) if officer_stems else 1.0) * 0.7

            # 3. Input Voltage (Luck_Wealth_Reset)
            w_kinetic_sum = 0
            for ws in wealth_stems:
                stage = get_stage(ws, luck_branch)
                w_kinetic_sum += STAGE_MULT.get(stage, 1.0)
            w_kinetic = (w_kinetic_sum / len(wealth_stems) if wealth_stems else 1.0) * 0.7

            # 4. Phase Rectification (Stem Bonding Audit)
            phase_trans = 1.0
            COMBINES = {"甲己", "己甲", "乙庚", "庚乙", "丙辛", "辛丙", "丁壬", "壬丁", "戊癸", "癸戊"}
            # [Rectification]: Wealth/Officer combines
            is_rectified = False
            for ws in wealth_stems:
                if (ws + annual_pillar[0]) in COMBINES:
                    is_rectified = True 
                    phase_trans *= 0.8 # Efficient flow

            is_short_circuit = False
            for os in officer_stems:
                if (os + annual_pillar[0]) in COMBINES:
                    is_short_circuit = True
                    phase_trans *= 1.8 # Feedback fail

            # 5. Vault Energy Surge
            is_wealth_burst = False
            is_officer_tunneling = False
            CLASHES = {"子午", "午子", "丑未", "未丑", "寅申", "申寅", "卯酉", "酉卯", "辰戌", "戌辰", "巳亥", "亥巳"}
            for i in range(4):
                br = branches[i]
                if (annual_pillar[1] + br) in CLASHES:
                    hidden = BaziParticleNexus.get_branch_weights(br)
                    if any(BaziParticleNexus.get_shi_shen(hs, dm) in ["正财", "偏财"] for hs, w in hidden):
                        if get_stage(dm, br) == "墓": is_wealth_burst = True
                    if any(BaziParticleNexus.get_shi_shen(hs, dm) == "正官" for hs, w in hidden):
                        if get_stage(dm, br) == "墓": is_officer_tunneling = True

            # 6. Impedance Alignment (Reverse_Collapse)
            is_reverse_collapse = False
            TRI_COMBINES = {"Wood": ["亥", "卯", "未"], "Fire": ["寅", "午", "戌"], "Metal": ["巳", "酉", "丑"], "Water": ["申", "子", "辰"]}
            w_elem = BaziParticleNexus.STEMS[wealth_stems[0]][0] if wealth_stems else "Neutral"
            if all(m in branches for m in TRI_COMBINES.get(w_elem, [])) and o_stabilization < 0.4:
                is_reverse_collapse = True

            # 7. SAI Calculation (Stability Index)
            ratio = w_kinetic / max(0.1, o_stabilization)
            
            # [Overvoltage_Transition]: High wealth from luck
            is_overvoltage = False
            luck_god = BaziParticleNexus.get_shi_shen(luck_pillar[0], dm)
            if luck_god in ["正财", "偏财"] and w_kinetic > 2.0:
                is_overvoltage = True
                ratio *= 1.5 # Shift towards Seven Killings

            sai = ratio * phase_trans * geo_factor
            
            if is_wealth_burst: sai *= 2.5 # Surge
            if is_officer_tunneling: sai *= 0.6 # Stabilizing boost
            if is_reverse_collapse: sai *= 2.0 # 失控坍缩

            # 8. Status Categories
            if is_overvoltage and sai > 4.0: category = "OVERVOLT_BURNOUT (财多生杀/过压烧毁)"
            elif is_reverse_collapse: category = "REVERSE_COLLAPSE (失控坍缩/磁场淹没)"
            elif 0.8 <= ratio <= 1.8 and sai < 1.5: category = "STEADY_POWER (闭环稳压/持续供能)"
            elif is_wealth_burst: category = "SURGE_IMPACT (瞬时激增/高压冲击)"
            elif is_officer_tunneling: category = "TUNNEL_STABILITY (能级隧穿/稳态增长)"
            else: category = "UNSTABLE_LOAD (负载失衡)"

            return {
                "chart": chart,
                "category": category,
                "sai": f"{sai:.2f}",
                "input_voltage": f"{w_kinetic:.2f}",
                "load_stability": f"{o_stabilization:.2f}",
                "is_burst": "YES" if is_wealth_burst else "NO",
                "is_tunneling": "YES" if is_officer_tunneling else "NO",
                "label": " ".join([f"{p[0]}{p[1]}" for p in chart]),
                "audit_mode": "CGXS_V4.1_STABILIZED_POWER",
                "topic_name": "财官相生 (CGXS)",
                "stress": f"{sai:.2f}"
            }
        # --- PGB Tracks (Refined) ---

        if pattern_id == "PGB_ULTRA_FLUID":
            # [ASE PHASE 4.1] PGB V4.1: Superfluid Coupling Model (Non-Newtonian Flow)
            luck_pillar = chart[4] if len(chart) >= 5 else ('', '')
            annual_pillar = chart[5] if len(chart) >= 6 else ('', '')

            # 1. Topology Screening (Killings and Bi/Jie presence)
            natal_tg = ten_gods[:4]
            if "七杀" not in natal_tg: return None
            if not any(tg in ["比肩", "劫财"] for tg in natal_tg): return None
            
            STAGES = ["长生", "沐浴", "冠带", "临官", "帝旺", "衰", "病", "死", "墓", "绝", "胎", "养"]
            STAGE_MULT = {
                "长生": 1.5, "沐浴": 1.1, "冠带": 1.3, "临官": 2.0, "帝旺": 2.5,
                "衰": 1.0, "病": 0.7, "死": 0.4, "墓": 1.1, "绝": 0.2, "胎": 0.6, "养": 1.0
            }
            LIFE_STAGES = {
                "甲": ["亥", "子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌"],
                "乙": ["午", "巳", "辰", "卯", "寅", "丑", "子", "亥", "戌", "酉", "申", "未"],
                "丙": ["寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥", "子", "丑"],
                "丁": ["酉", "申", "未", "午", "巳", "辰", "卯", "寅", "丑", "子", "亥", "戌"],
                "戊": ["寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥", "子", "丑"],
                "己": ["酉", "申", "未", "午", "巳", "辰", "卯", "寅", "丑", "子", "亥", "戌"],
                "庚": ["巳", "午", "未", "申", "酉", "戌", "亥", "子", "丑", "寅", "卯", "辰"],
                "辛": ["子", "亥", "戌", "酉", "申", "未", "午", "巳", "辰", "卯", "寅", "丑"],
                "壬": ["申", "酉", "戌", "亥", "子", "丑", "寅", "卯", "辰", "巳", "午", "未"],
                "癸": ["卯", "寅", "丑", "子", "亥", "戌", "酉", "申", "未", "午", "巳", "辰"]
            }

            def get_stage(stem, branch):
                if stem not in LIFE_STAGES: return "衰"
                try:
                    idx = LIFE_STAGES[stem].index(branch)
                    return STAGES[idx]
                except: return "衰"

            # 2. Superfluid Integrity (Flow Capacity)
            sha_stems = [st for i, (st, br) in enumerate(chart[:4]) if ten_gods[i] == "七杀"]
            bj_stems = [st for i, (st, br) in enumerate(chart[:4]) if ten_gods[i] in ["比肩", "劫财"]]
            
            luck_branch = luck_pillar[1]
            sha_kinetic = sum(STAGE_MULT.get(get_stage(s, luck_branch), 1.0) for s in sha_stems) * 0.7
            bj_capacity = sum(STAGE_MULT.get(get_stage(s, luck_branch), 1.0) for s in bj_stems) * 0.7

            # 3. Polarity_Neutralization (Stem Bonding / 应力释放)
            neutralization = 1.0
            COMBINES = {"甲己", "己甲", "乙庚", "庚乙", "丙辛", "辛丙", "丁壬", "壬丁", "戊癸", "癸戊"}
            is_neutralized = False
            for ss in sha_stems:
                if (ss + annual_pillar[0]) in COMBINES:
                    is_neutralized = True
                    neutralization *= 0.5 # 50% Stress drop

            # 4. Vault_Dynamics (Deep Pulse 检测)
            is_sha_vault_burst = False
            CLASHES = {"子午", "午子", "丑未", "未丑", "寅申", "申寅", "卯酉", "酉卯", "辰戌", "戌辰", "巳亥", "亥巳"}
            for i in range(4):
                br = branches[i]
                if (annual_pillar[1] + br) in CLASHES:
                    hidden = BaziParticleNexus.get_branch_weights(br)
                    if any(BaziParticleNexus.get_shi_shen(hs, dm) == "七杀" for hs, w in hidden):
                        is_sha_vault_burst = True
                        neutralization *= 2.0 # Internal oscillation surge

            # 5. SAI Calculation (Fluidity Index)
            # Ultra-fluid state is when BJ can absorb SHA kinetic perfectly
            ratio = sha_kinetic / max(0.1, bj_capacity)
            sai = abs(ratio - 1.2) * neutralization * geo_factor

            # 6. Status Categories
            if is_sha_vault_burst and sai > 2.5: category = "PULSE_OSCILLATION (内生震荡/暗裂)"
            elif 0.8 <= ratio <= 1.5 and sai < 0.6: category = "SUPERFLUID_LOCK (超流锁定/无阻)"
            elif is_neutralized: category = "STRESS_RELEASE (应力释放/中和)"
            else: category = "LAMINAR_FLOW (层流运行)"

            return {
                "chart": chart,
                "category": category,
                "sai": f"{sai:.2f}",
                "flow_ratio": f"{ratio:.2f}",
                "is_neutralized": "YES" if is_neutralized else "NO",
                "is_oscillation": "YES" if is_sha_vault_burst else "NO",
                "label": " ".join([f"{p[0]}{p[1]}" for p in chart]),
                "audit_mode": "PGB_V4.1_ULTRA_FLUID",
                "topic_name": "PGB 超流锁定",
                "stress": f"{sai:.2f}"
            }

        if pattern_id == "PGB_BRITTLE_TITAN":
            # [ASE PHASE 4.1] PGB V4.1: Brittle Titan Model (Internal Stress & Fracture)
            luck_pillar = chart[4] if len(chart) >= 5 else ('', '')
            annual_pillar = chart[5] if len(chart) >= 6 else ('', '')

            # 1. Topology Screening (Strong Seven Killings vs Weak DM)
            if "七杀" not in ten_gods: return None
            
            # DM Strength Check
            dm_roots = 0
            for br in branches:
                hidden = BaziParticleNexus.get_branch_weights(br)
                if any(BaziParticleNexus.get_shi_shen(hs, dm) in ["长生", "冠带", "临官", "帝旺", "墓"] for hs, w in hidden):
                    dm_roots += 1
            
            # 2. Structural Fragility (Base Crash / 晶格断裂)
            is_fractured = False
            CLASHES = {"子午", "午子", "丑未", "未丑", "寅申", "申寅", "卯酉", "酉卯", "辰戌", "戌辰", "巳亥", "亥巳"}
            # Check if DM's root is being crashed by annual branch
            for br in branches:
                if (annual_pillar[1] + br) in CLASHES:
                    # Is this a vital root?
                    hidden = BaziParticleNexus.get_branch_weights(br)
                    if any(BaziParticleNexus.get_shi_shen(hs, dm) in ["临官", "帝旺"] for hs, w in hidden):
                        is_fractured = True

            # 3. Structural_Phase_Transition (地支杀局)
            is_phase_transition = False
            sha_elem = "Fire" # Dynamic lookup for SHA needed, but placeholder
            # Simplified: look for SHA dominance in branches
            sha_branch_count = sum(1 for tg in ten_gods if tg == "七杀")
            if sha_branch_count >= 2: is_phase_transition = True

            # 4. SAI (Stress Index)
            # High internal stress from killing pressure without support
            base_sai = 5.0 if dm_roots < 1 else 2.0
            if is_fractured: base_sai *= 3.0 # Lattice fracture
            if is_phase_transition: base_sai *= 1.5 # Brittleness increase

            sai = base_sai * geo_factor

            # 5. Status Categories
            if is_fractured: category = "LATTICE_FRACTURE (晶格断裂/毁灭)"
            elif is_phase_transition and dm_roots < 2: category = "BRITTLE_TRANSITION (脆性相变/相变崩溃)"
            elif sai > 8.0: category = "TITAN_CRITICAL (巨人极限/临界)"
            else: category = "STRESSED_TITAN (带压运行)"

            return {
                "chart": chart,
                "category": category,
                "sai": f"{sai:.2f}",
                "dm_roots": dm_roots,
                "is_fractured": "YES" if is_fractured else "NO",
                "is_phase_transition": "YES" if is_phase_transition else "NO",
                "label": " ".join([f"{p[0]}{p[1]}" for p in chart]),
                "audit_mode": "PGB_V4.1_BRITTLE_TITAN",
                "topic_name": "PGB 脆性巨人",
                "stress": f"{sai:.2f}"
            }

        if pattern_id == "CYGS_COLLAPSE":
            # [ASE PHASE 4.1] CYGS V4.1: Gravitational Collapse & Singularity Expansion Model
            luck_p = chart[4] if len(chart) >= 5 else ('', '')
            annual_p = chart[5] if len(chart) >= 6 else ('', '')

            # 1. Multi-Channel Topology Screening
            month_br = chart[1][1]
            hidden_month = BaziParticleNexus.get_branch_weights(month_br)
            is_month_support = any(BaziParticleNexus.get_shi_shen(hs, dm) in ["长生", "临官", "帝旺", "正印", "偏印"] for hs, w in hidden_month)
            
            # Rooting Count (Companion + Resource)
            dm_roots = 0
            for i in range(4):
                br = branches[i]
                hidden = BaziParticleNexus.get_branch_weights(br)
                if any(BaziParticleNexus.get_shi_shen(hs, dm) in ["比肩", "劫财", "正印", "偏印"] for hs, w in hidden):
                    dm_roots += 1

            # 2. Field Polarity Scan (Integrated A/B/C/D)
            natal_tg = ten_gods[:4]
            field_counts = {
                "P_111A": natal_tg.count("正财") + natal_tg.count("偏财"), # 从财
                "P_111B": natal_tg.count("七杀") + natal_tg.count("正官"), # 从杀
                "P_111C": natal_tg.count("食神") + natal_tg.count("伤官"), # 从儿
                "P_111D": natal_tg.count("比肩") + natal_tg.count("劫财") + natal_tg.count("正印") + natal_tg.count("偏印") # 从强/旺
            }
            
            sub_package_id = max(field_counts, key=field_counts.get)
            if field_counts[sub_package_id] < 1: return None 

            # Screening Validation
            if sub_package_id in ["P_111A", "P_111B", "P_111C"]:
                if is_month_support: return None # Must NOT be supported for Collapse
                if field_counts[sub_package_id] < 2: return None
            else: # P_111D (Expansion)
                if not is_month_support: return None # MUST be supported for Expansion
                # Expansion requires near-zero opposition
                opposites = sum(1 for tg in natal_tg if tg in ["正财", "偏财", "正官", "七杀", "食神", "伤官"])
                if opposites > 1: return None

            # 3. Physics Metrics (Locking & Purity)
            if sub_package_id == "P_111D":
                # Expansion Purity: How much opposition is there?
                opposites = sum(1 for tg in natal_tg if tg in ["正财", "偏财", "正官", "七杀", "食神", "伤官"])
                locking_ratio = 1.0 - (opposites * 0.25)
                category_base = "SINGULARITY_EXPANSION (奇点膨胀/从旺)"
            else:
                # Collapse Purity: How many impurities (Self/Impression)?
                impurities = sum(1 for tg in natal_tg if tg in ["比肩", "劫财", "正印", "偏印"])
                locking_ratio = 1.0 - (impurities * 0.25)
                category_base = "GRAVITATIONAL_COLLAPSE (引力坍缩/弃命)"

            # 4. Phase Intervention (Override Logic)
            # Reversal check for Expansion vs Collapse
            luck_tg = BaziParticleNexus.get_shi_shen(luck_p[0], dm)
            is_dissolution = False
            # Collapse fails if Luck brings DM energy; Expansion fails if Luck brings opposition
            if sub_package_id == "P_111D":
                if luck_tg in ["正财", "偏财", "正官", "七杀", "食神", "伤官"]:
                    is_dissolution = True
            else:
                if luck_tg in ["比肩", "劫财", "正印", "偏印"]:
                    is_dissolution = True
            
            # Rebound (Vault Opening) - Critical for Collapse
            is_rebound = False
            CLASHES = {"子午", "午子", "丑未", "未丑", "寅申", "申寅", "卯酉", "酉卯", "辰戌", "戌辰", "巳亥", "亥巳"}
            for i in range(4):
                if (annual_p[1] + branches[i]) in CLASHES:
                    h_elems = BaziParticleNexus.get_branch_weights(branches[i])
                    # Rebound triggers if local seeds are released
                    if sub_package_id != "P_111D":
                        if any(BaziParticleNexus.get_shi_shen(hs, dm) in ["比肩", "劫财", "正印", "偏印"] for hs, w in h_elems):
                            is_rebound = True

            # 5. Integrated SAI Calculation
            base_sai = 0.2 # Superfluid for true/pure patterns
            if locking_ratio < 0.9: base_sai = 1.8 
            
            if is_dissolution: base_sai *= 4.0
            if is_rebound: base_sai *= 6.0 
            
            sai = base_sai * geo_factor
            
            # Final Category
            if is_rebound: category = "PHYSICAL_REBOUND (物理反弹/爆裂)"
            elif is_dissolution: category = "DISSOLUTION_ZONE (引力失效/解体)"
            elif locking_ratio < 0.8: category = "IMPURE_TRANSIENT (相位抖动/假态)"
            else: category = f"PURE_{sub_package_id.split('_')[-1]} ({category_base})"

            return {
                "chart": chart,
                "category": category,
                "sai": f"{sai:.2f}",
                "locking_ratio": f"{locking_ratio:.2f}",
                "purity_index": f"{locking_ratio:.2f}",
                "sub_package_id": sub_package_id,
                "field_polarity": sub_package_id,
                "is_rebound": "YES" if is_rebound else "NO",
                "label": " ".join([f"{p[0]}{p[1]}" for p in chart]),
                "audit_mode": "CYGS_V4.1_COLLAPSE",
                "topic_name": "CYGS 引力坍缩",
                "stress": f"{sai:.2f}"
            }

        if pattern_id == "HGFG_TRANSMUTATION":
            # [ASE PHASE 4.1] HGFG V4.1: Atomic Transmutation Model (Transformed Patterns)

            # 1. Atomic Pair Detection
            PAIRS = {"甲": "己", "己": "甲", "乙": "庚", "庚": "乙", "丙": "辛", "辛": "丙", "丁": "壬", "壬": "丁", "戊": "癸", "癸": "戊"}
            TRANSFORM_GOAL = {
                ("甲", "己"): ("Earth", "P_112A"), ("己", "甲"): ("Earth", "P_112A"),
                ("乙", "庚"): ("Metal", "P_112B"), ("庚", "乙"): ("Metal", "P_112B"),
                ("丙", "辛"): ("Water", "P_112C"), ("辛", "丙"): ("Water", "P_112C"),
                ("丁", "壬"): ("Wood", "P_112D"), ("壬", "丁"): ("Wood", "P_112D"),
                ("戊", "癸"): ("Fire", "P_112E"), ("癸", "戊"): ("Fire", "P_112E")
            }

            partner = PAIRS.get(dm)
            target_partner = None
            if stems[1] == partner: target_partner = stems[1]
            elif stems[3] == partner: target_partner = stems[3]
            
            if not target_partner: return None
            
            goal_elem, sub_pkg = TRANSFORM_GOAL.get((dm, target_partner))

            # 2. Catalytic Resonance (Month Branch Support)
            month_br = branches[1]
            month_energy = BaziParticleNexus.get_branch_weights(month_br)
            # Threshold: Transmuted element must be present in month branch
            if not any(BaziParticleNexus.STEMS.get(hs)[0] == goal_elem for hs, w in month_energy):
                return None # Environment does not support transmutation
            
            # Resonance level based on month branch dominance
            is_dominant = BaziParticleNexus.STEMS.get(month_energy[0][0])[0] == goal_elem
            resonance = 2.0 if is_dominant else 1.0

            # 3. Transmutation Purity Audit
            # Check for "Competitors" (Same stem as DM or Partner elsewhere)
            competitors = stems.count(dm) + stems.count(partner) - 2
            transmutation_purity = 1.0 - (competitors * 0.3)
            
            # 4. Reversal Singularity Check (还原算子)
            is_reversed = False
            # a) Annual pillar clashing the transmutation (Reversal Reagent)
            # If annual stem is the agent that kills the goal element
            REAGENTS = {"Earth": "Wood", "Metal": "Fire", "Water": "Earth", "Wood": "Metal", "Fire": "Water"}
            if annual_p and len(annual_p) > 0 and BaziParticleNexus.STEMS.get(annual_p[0]) and BaziParticleNexus.STEMS.get(annual_p[0])[0] == REAGENTS.get(goal_elem):
                is_reversed = True
            
            # b) Annual pillar bringing back original DM element strongly
            if annual_p[0] == dm:
                is_reversed = True
            
            # c) Breaking the pair (合去化神)
            if PAIRS.get(annual_p[0]) in [dm, target_partner]:
                is_reversed = True

            # 5. Integrated SAI Calculation
            base_sai = 0.5 # Stable for true transmutation
            if transmutation_purity < 0.9: base_sai = 2.5 # Impure / Unstable
            
            if is_reversed:
                base_sai *= 8.0 # High peak on reversal
            
            sai = (base_sai / (transmutation_purity + 0.1)) * resonance * geo_factor
            
            # 6. Status Categories
            if is_reversed: category = "ATOMIC_REVERSAL (原子重构失败/还原)"
            elif transmutation_purity < 0.7: category = "IMPURE_TRANSMUTATION (属性污染/假化)"
            elif is_dominant: category = "TRUE_TRANSMUTATION (核变稳态/真化)"
            else: category = "STRESSED_TRANSMUTATION (诱导重构/带感应)"

            return {
                "chart": chart,
                "category": category,
                "sai": f"{sai:.2f}",
                "transmutation_purity": f"{transmutation_purity:.2f}",
                "goal_element": goal_elem,
                "sub_package_id": sub_pkg,
                "is_reversed": "YES" if is_reversed else "NO",
                "label": " ".join([f"{p[0]}{p[1]}" for p in chart]),
                "audit_mode": "HGFG_V4.1_TRANSMUTATION",
                "topic_name": "HGFG 化气格",
                "stress": f"{sai:.2f}"
            }

        if pattern_id == "SSSC_AMPLIFIER":
            # [ASE PHASE 4.1] SSSC V4.1: Two-Stage Gain Amplifier Model (Eating/Hurting Output Generates Wealth)
            luck_p = chart[4] if len(chart) >= 5 else ('', '')
            annual_p = chart[5] if len(chart) >= 6 else ('', '')

            # 1. Component Identification
            natal_tg = ten_gods[:4]
            shang_guan_count = natal_tg.count("伤官")
            shi_shen_count = natal_tg.count("食神")
            wealth_count = natal_tg.count("正财") + natal_tg.count("偏财")

            # Must have Output and Wealth
            if (shang_guan_count + shi_shen_count == 0) or (wealth_count == 0):
                return None
            
            # 2. Sub-Package Classification
            if shang_guan_count > shi_shen_count:
                sub_pkg = "P_113B" # Pulse Amplifier (Hurting Officer)
            else:
                sub_pkg = "P_113A" # Laminar Amplifier (Eating God)
            
            # 3. Impedance Matching Calculation (Output Power vs Load Capacity)
            # Power = Output Count * Root Support
            output_roots = sum(1 for b in branches if any(BaziParticleNexus.get_shi_shen(hs, dm) in ["食神", "伤官"] for hs, w in BaziParticleNexus.get_branch_weights(b)))
            output_power = (shang_guan_count + shi_shen_count) + (output_roots * 0.5)
            
            # Load = Wealth Count * Root Support
            wealth_roots = sum(1 for b in branches if any(BaziParticleNexus.get_shi_shen(hs, dm) in ["正财", "偏财"] for hs, w in BaziParticleNexus.get_branch_weights(b)))
            load_capacity = wealth_count + (wealth_roots * 0.5)
            
            if load_capacity == 0: load_capacity = 0.5 # Prevent div zero
            
            impedance_ratio = output_power / load_capacity
            gain_factor = impedance_ratio # 1.0 is perfect match
            
            # 4. Interference Check (Owl Cutoff & Rob Wealth Short)
            # Cutoff: Owl Spirit attacking Eating God
            has_cutoff = False
            if "偏印" in natal_tg and "食神" in natal_tg:
                has_cutoff = True
            
            # Dynamic Injection: Annual Cutoff
            annual_tg = BaziParticleNexus.get_shi_shen(annual_p[0], dm)
            if annual_tg == "偏印" and "食神" in natal_tg:
                has_cutoff = True
            
            # 5. Integrated SAI Calculation
            # Ideal Ratio: 0.8 - 1.5
            dist_from_ideal = 0.0
            if impedance_ratio < 0.8: dist_from_ideal = 0.8 - impedance_ratio # Under-driven
            elif impedance_ratio > 1.5: dist_from_ideal = impedance_ratio - 1.5 # Over-driven
            
            base_sai = dist_from_ideal * 2.0
            cutoff_penalty = 3.0 if has_cutoff else 0.0
            
            sai = (base_sai + cutoff_penalty) * geo_factor
            if sai < 0.1: sai = 0.1 # Minimum floor

            # 6. Status Categories
            if has_cutoff: category = "AMPLIFIER_CUTOFF (枭神夺食/断路)"
            elif impedance_ratio > 2.0: category = "GAIN_SATURATION (输出过载/身弱劳碌)"
            elif impedance_ratio < 0.5: category = "LOAD_HEAVY (负载过重/财多身弱)"
            else: category = f"MATCHED_GAIN (阻抗匹配/{'层流' if sub_pkg == 'P_113A' else '脉冲'}稳态)"

            return {
                "chart": chart,
                "category": category,
                "sai": f"{sai:.2f}",
                "gain_factor": f"{gain_factor:.2f}",
                "sub_package_id": sub_pkg,
                "has_cutoff": "YES" if has_cutoff else "NO",
                "label": " ".join([f"{p[0]}{p[1]}" for p in chart]),
                "audit_mode": "SSSC_V4.1_AMPLIFIER",
                "topic_name": "SSSC 食伤生财",
                "stress": f"{sai:.2f}"
            }

        if pattern_id == "JLTG_CORE_ENERGY":
            # [ASE PHASE 4.1] JLTG V4.1: Stationary High-Energy Core Model (Thermal Runaway)
            luck_p = chart[4] if len(chart) >= 5 else ('', '')
            annual_p = chart[5] if len(chart) >= 6 else ('', '')

            # 1. Component Identification (Month Branch Energy)
            month_br = branches[1]
            hidden_month = BaziParticleNexus.get_branch_weights(month_br)
            month_main_energy = BaziParticleNexus.get_shi_shen(hidden_month[0][0], dm)
            
            # Sub-Package Classification
            sub_pkg = None
            if month_main_energy == "比肩": sub_pkg = "P_114A" # Jian Lu
            elif month_main_energy == "劫财" or month_main_energy == "羊刃": sub_pkg = "P_114B" # Yue Jie
            
            if not sub_pkg: return None

            # 2. Thermal Balance Calculation (Internal Energy vs Load Capacity)
            # Internal Energy: Rob Wealth + Friend + Resource
            natal_tg = ten_gods[:4]
            internal_energy = sum(1 for tg in natal_tg if tg in ["比肩", "劫财", "正印", "偏印"])
            internal_energy += sum(1 for b in branches if any(BaziParticleNexus.get_shi_shen(hs, dm) in ["比肩", "劫财", "正印", "偏印"] for hs, w in BaziParticleNexus.get_branch_weights(b))) * 0.5
            
            # Load Capacity: Officer + Wealth + Output
            load_capacity = sum(1 for tg in natal_tg if tg in ["正官", "七杀", "正财", "偏财", "食神", "伤官"])
            load_capacity += sum(1 for b in branches if any(BaziParticleNexus.get_shi_shen(hs, dm) in ["正官", "七杀", "正财", "偏财", "食神", "伤官"] for hs, w in BaziParticleNexus.get_branch_weights(b))) * 0.5
            
            if load_capacity == 0: load_capacity = 0.5 # Prevent div zero
            
            thermal_balance = internal_energy / load_capacity # High = Hot, Low = Cool
            
            # 3. Dynamic Interference (Oscillation & Burn)
            # Core Oscillation: Month branch clash
            # Find opposite branch to month
            CLASH_MAP = {"子": "午", "午": "子", "丑": "未", "未": "丑", "寅": "申", "申": "寅", "卯": "酉", "酉": "卯", "辰": "戌", "戌": "辰", "巳": "亥", "亥": "巳"}
            target_clash = CLASH_MAP.get(month_br)
            
            is_oscillation = False
            # Check Luck and Annual
            if luck_p[1] == target_clash or annual_p[1] == target_clash:
                is_oscillation = True
            
            # Thermal Runaway: High balance + Rob Wealth (Fuel) + No control
            is_runaway = False
            if thermal_balance > 2.0 and "劫财" in natal_tg:
                is_runaway = True
            
            # 4. Integrated SAI Calculation
            # Ideal Balance: 0.8 - 1.2
            dist_from_ideal = 0.0
            if thermal_balance < 0.8: dist_from_ideal = 0.8 - thermal_balance
            elif thermal_balance > 1.2: dist_from_ideal = thermal_balance - 1.2
            
            base_sai = dist_from_ideal * 2.0
            
            if is_oscillation: base_sai *= 3.0 # Core shaking
            if is_runaway: base_sai *= 4.0 # Meltdown
            
            sai = base_sai * geo_factor
            if sai < 0.1: sai = 0.1

            # 5. Status Categories
            if is_runaway: category = "THERMAL_RUNAWAY (核心熔毁/比劫夺财)"
            elif is_oscillation: category = "CORE_OSCILLATION (月令冲战/根基动摇)"
            elif thermal_balance > 2.0: category = "ENERGY_淤积 (过热/无处宣泄)"
            else: category = f"STABLE_CORE (热平衡稳态/{'建禄' if sub_pkg == 'P_114A' else '月劫'})"

            return {
                "chart": chart,
                "category": category,
                "sai": f"{sai:.2f}",
                "thermal_balance": f"{thermal_balance:.2f}",
                "sub_package_id": sub_pkg,
                "is_runaway": "YES" if is_runaway else "NO",
                "is_oscillation": "YES" if is_oscillation else "NO",
                "label": " ".join([f"{p[0]}{p[1]}" for p in chart]),
                "audit_mode": "JLTG_V4.1_CORE",
                "topic_name": "JLTG 建禄月劫",
                "stress": f"{sai:.2f}"
            }

        # Standard legacy matching (minimal metadata)
        if self._legacy_matches(chart, pattern_id):
            return {"chart": chart, "category": "匹配 (Matched)", "label": " ".join([f"{p[0]}{p[1]}" for p in chart])}
            
        return None

    def _legacy_matches(self, chart: List[List[str]], pattern_id: str) -> bool:
        """Fallback for older pattern matching."""
        dm = chart[2][0]
        stems = [p[0] for p in chart]
        ten_gods = [BaziParticleNexus.get_shi_shen(s, dm) for s in stems]
        if pattern_id == "YANG_REN_JIA_SHA":
            yang_ren_map = {"甲": "卯", "丙": "午", "戊": "午", "庚": "酉", "壬": "子"}
            return chart[1][1] == yang_ren_map.get(dm) and "七杀" in ten_gods
        return False

        return False
