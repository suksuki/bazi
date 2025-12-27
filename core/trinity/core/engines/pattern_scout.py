import logging
import math
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
            "MOD_115_SSZS": "SSZS_PULSE_INTERCEPTION",
            "MOD_119_CE": "CE_FLARE_DISCHARGE",
            "MOD_116_GYPS": "GYPS_RECTIFIER_BRIDGE",
            "MOD_117_CWJG": "CWJG_FEEDBACK_LOOP",
            "MOD_121_YGZJ": "YGZJ_MONOPOLE_ENERGY",
            "MOD_122_YHGS": "YHGS_THERMODYNAMIC_ENTROPY",
            "MOD_123_LYKG": "LYKG_LC_SELF_LOCKING",
            "MOD_124_JJGG": "JJGG_QUANTUM_TUNNELING",
            "MOD_125_TYKG": "TYKG_PHASE_RESONANCE",
            "MOD_126_CWJS": "CWJS_QUANTUM_TRANSITION",
            "MOD_127_MHGG": "MHGG_REVERSION_DYNAMICS",
            "MOD_128_GXYG": "GXYG_VIRTUAL_GAP",
            "MOD_129_MBGS": "MBGS_STORAGE_POTENTIAL",
            "MOD_130_ZHSG": "ZHSG_MIXED_EXCITATION",
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
        
        # [V4.2.6] 环境变量标准提取 (支持多源：geo_context 或 chart 扩展位)
        # 统一规范为 (Stem, Branch) TUPLE
        def _to_tuple(p):
            if isinstance(p, tuple) and len(p) >= 2: return p
            if isinstance(p, list) and len(p) >= 2: return (p[0], p[1])
            if isinstance(p, str) and len(p) >= 2 and p != "未知大运" and p != "未知":
                return (p[0], p[1])
            return ('', '')

        luck_pillar = geo_context.get("luck_pillar") if geo_context else None
        if not luck_pillar:
            luck_pillar = chart[4] if len(chart) >= 5 else ('', '')
            
        annual_pillar = geo_context.get("annual_pillar") if geo_context else None
        if not annual_pillar:
            annual_pillar = chart[5] if len(chart) >= 6 else ('', '')
            
        # 标准化
        luck_p = _to_tuple(luck_pillar)
        annual_p = _to_tuple(annual_pillar)
        
        # 兼容性别名 (用于各 MOD 内部)
        luck_pillar = luck_p
        annual_pillar = annual_p
        
        # 提取十神序列 (仅针对原本的支，不包含环境注入，除非显式需要)
        # natal + injected (if exist)
        ten_gods = [BaziParticleNexus.get_shi_shen(s, dm) for s in stems]
        # 如果 stems 包含环境 pillars，这里已经处理了
        
        if pattern_id == "SHANG_GUAN_JIAN_GUAN":
            # [ASE PHASE 4.1] SGGG V4.1: Gate Breakdown Model

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
            
            # 如果压制比不够，且官杀能量显著，格局进入“崩溃边缘”
            is_pattern_collapsed = suppression_ratio < 3.0 and guan_total > 1.0
            
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
            if is_pattern_collapsed:
                base_sai *= 15.0 # 致命风险：见官则祸
            if not intercept_success and incoming_guan > 0:
                base_sai *= (3.0 + incoming_guan)  # 拦截失败风险
            
            # 财星泄放 (正向: 伤官生财，能量有出路)
            wealth_factor = 1.0 / (1.0 + wealth_load * 0.3)
            sai = base_sai * wealth_factor * geo_factor
            
            # ===== 维度 G: 状态分类 =====
            if is_pattern_collapsed:
                category = "FIELD_COLLAPSE (气化场崩塌/见官则祸)"
            elif is_vaporized and source_stability >= 0.5:
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
            

        if pattern_id == "SSZS_PULSE_INTERCEPTION":
            # ============================================================
            # [QGA V4.3] MOD_115: SSZS CIWS 脉冲制导拦截模型
            # 物理定义：日主泄放的“高频脉冲粒子（食神）”对外部突入的“重质量撞击物（七杀）”
            # 进行动能对撞与轨迹偏转。
            # ============================================================
            
            # 1. 能量统计 (包含天干及环境注入)
            E_ss = 0.0  # 食神 (Interceptor)
            E_qs = 0.0  # 七杀 (Projectile)
            E_sg = 0.0  # 伤官 (Interference)
            E_resource = 0.0 # 印星 (Shield/Radar)
            
            # 基础环境组合
            all_particles = list(chart[:4]) + [luck_pillar, annual_pillar]
            for i, p in enumerate(all_particles):
                st, br = p
                if not st: continue
                ts = BaziParticleNexus.get_shi_shen(st, dm)
                
                weight = 3.0 if i < 4 else (1.5 if i == 4 else 2.5) # 天干 > 流年 > 大运 weight
                
                if ts == "食神": E_ss += weight
                elif ts == "七杀": E_qs += weight
                elif ts == "伤官": E_sg += weight
                elif ts in ["正印", "偏印"]: E_resource += weight
            
            # 藏干统计
            for st, br in chart[:4]:
                hidden = BaziParticleNexus.get_branch_weights(br)
                for hs, w in hidden:
                    hg = BaziParticleNexus.get_shi_shen(hs, dm)
                    energy = w / 10.0
                    if hg == "食神": E_ss += energy
                    elif hg == "七杀": E_qs += energy
                    elif hg == "伤官": E_sg += energy
                    elif hg in ["正印", "偏印"]: E_resource += energy
            
            # 2. 核心算法：[Interception_Efficiency]
            # 基础拦截率: 1.0 为完美动能抵消
            if E_qs < 0.5 and E_ss < 0.5: return None # 无物理冲突
            
            interception_eff = E_ss / max(0.1, E_qs)
            
            # 拦截纯度：防止伤官混入导致弹道弥散
            purity = E_ss / max(0.1, E_ss + E_sg)
            
            # 雷达灵敏度：印星过多会干扰食神的发射频率（枭神夺食预警）
            radar_interference = E_resource / max(0.1, E_ss)
            
            # 3. SAI 应力计算 (基于拦截效能偏离度)
            # 理想点：interception_eff ≈ 1.2 (过饱和拦截)
            sai_base = abs(interception_eff - 1.2) * 1.5
            
            status = "STABLE_DEFENSE"
            if interception_eff < 0.6:
                status = "PENETRATION (物理穿透/防御崩溃)"
                sai_base *= 4.0
            elif interception_eff > 3.0:
                status = "SATURATION (过载关机/能量浪费)"
                sai_base *= 2.0
            
            if purity < 0.6:
                status = "DIFFUSION_LOST (弹道弥散/效率下降)"
                sai_base *= 1.8
            
            if radar_interference > 2.0:
                status = "RADAR_BLOCKED (雷达封锁/系统离线)"
                sai_base *= 3.0

            sai = sai_base * geo_factor
            
            return {
                "chart": chart,
                "category": status,
                "sai": f"{sai:.2f}",
                "interception_efficiency": f"{interception_eff:.2f}",
                "purity_ratio": f"{purity*100:.1f}%",
                "radar_interference": f"{radar_interference:.2f}",
                "E_interceptor": f"{E_ss:.2f}",
                "E_projectile": f"{E_qs:.2f}",
                "label": " ".join([f"{p[0]}{p[1]}" for p in chart]),
                "audit_mode": "SSZS_V4.3_CIWS_INTERCEPT",
                "topic_name": "食神制杀 (SSZS)",
                "stress": f"{sai:.2f}"
            }

        if pattern_id == "CE_FLARE_DISCHARGE":
            # ============================================================
            # [QGA V4.3] MOD_119: CE_FLARE 高能等离子喷泉模型 (从儿格)
            # 物理定义：系统不再寻求引力平衡，而是处于一种持续物质喷射态。
            # 比劫 = 燃料 (Fuel Additive)，印星 = 喷管堵塞 (Vapor Lock)。
            # ============================================================
            
            # 1. 能量统计
            E_output = 0.0 # 食伤 (Discharge)
            E_fuel = 0.0   # 比劫 (Fuel)
            E_clog = 0.0   # 印星 (Vapor Lock)
            E_drain = 0.0  # 财星 (Sink/Load)
            
            # 必须满足“从儿”基础：月令必须是食伤，且日主无根无助（或极弱）
            month_br = chart[1][1]
            hidden_month = BaziParticleNexus.get_branch_weights(month_br)
            if not any(BaziParticleNexus.get_shi_shen(hs, dm) in ["食神", "伤官"] for hs, w in hidden_month):
                return None
            
            all_chars = list(chart[:4]) + [luck_pillar, annual_pillar]
            for i, p in enumerate(all_chars):
                st, br = p
                if not st: continue
                ts = BaziParticleNexus.get_shi_shen(st, dm)
                
                w = 3.0 if i < 4 else 1.5
                if ts in ["食神", "伤官"]: E_output += w
                elif ts in ["比肩", "劫财"]: E_fuel += w
                elif ts in ["正印", "偏印"]: E_clog += w
                elif ts in ["正财", "偏财"]: E_drain += w
                
            # 2. 核心算法：[Discharge_Flow_Rate]
            # 喷射速率 = 输出能级 / (系统残留能级)
            flow_rate = E_output / max(0.1, E_fuel + E_clog + 1.0)
            
            # 3. 物理判定：Vapor Lock (印星介入)
            is_vapor_lock = E_clog > 0.5
            has_fuel_injection = E_fuel > 2.0
            
            # 4. SAI 临界值定标
            # 从儿理想态：Flow Rate 极高，E_clog 为零，E_drain 适中
            sai_base = 0.2
            
            if is_vapor_lock:
                status = "VAPOR_LOCK (喷管堵塞/系统自爆)"
                sai_base = 15.0 + (E_clog * 5.0) # 指数级跳变
            elif flow_rate < 2.0:
                status = "FLOW_DAMPING (喷射动力不足)"
                sai_base = 2.5
            elif has_fuel_injection:
                status = "FUEL_INJECTED_FLARE (燃料注入/高能喷泉)"
                sai_base = 0.1 # 极其稳定
            else:
                status = "STELLAR_FLARE (标准等离子喷泉)"
                sai_base = 0.5
            
            # 财星作为负载，过重会稀释喷射能级
            if E_drain > E_output:
                status += " (LOAD_OVERFLOW)"
                sai_base *= 1.5

            sai = sai_base * geo_factor
            
            return {
                "chart": chart,
                "category": status,
                "sai": f"{sai:.2f}",
                "discharge_flow": f"{flow_rate:.2f}",
                "fuel_addition": f"{E_fuel:.2f}",
                "clog_index": f"{E_clog:.2f}",
                "is_vapor_lock": "YES" if is_vapor_lock else "NO",
                "label": " ".join([f"{p[0]}{p[1]}" for p in chart]),
                "audit_mode": "CE_V4.3_FLARE_DISCHARGE",
                "topic_name": "从儿格 (CE_FLARE)",
                "stress": f"{sai:.2f}"
            }

        if pattern_id == "GYPS_RECTIFIER_BRIDGE":
            # ============================================================
            # [QGA V4.3] MOD_116: GYPS 官印相生能量整流桥模型
            # 物理定义：印星作为“变压整流器”，将突入的高压官杀能级
            # 转化为日主的“偏置电压”。
            # ============================================================
            E_gs = 0.0 # 官杀 (Input Voltage)
            E_in = 0.0 # 印星 (Rectifier/Bridge)
            E_dm_support = 0.0 # 日主根气 (Stability)
            
            all_parts = list(chart[:4]) + [luck_pillar, annual_pillar]
            for i, p in enumerate(all_parts):
                st, br = p
                if not st: continue
                ts = BaziParticleNexus.get_shi_shen(st, dm)
                w = 3.0 if i < 4 else 1.5
                if ts in ["正官", "七杀"]: E_gs += w
                elif ts in ["正印", "偏印"]: E_in += w
                elif ts in ["比肩", "劫财"]: E_dm_support += w
                
            # 核心算法：[Rectification_Efficiency]
            if E_gs < 0.5 or E_in < 0.5: return None
            
            # 磁饱和度：当官杀压力远大于印星转化能力时，整流桥击穿
            saturation = E_gs / max(0.5, E_in)
            efficiency = 1.0 / max(0.1, saturation - 0.5) if saturation > 1.5 else 1.0
            
            sai_base = abs(saturation - 1.0) * 1.2
            status = "SMOOTH_RECTIFICATION"
            
            if saturation > 2.5:
                status = "BRIDGE_BURNOUT (整流桥击穿/磁饱和自燃)"
                sai_base *= 5.0
            elif saturation < 0.4:
                status = "REVERSE_LEAKAGE (转化效率极低/能量漏损)"
                sai_base *= 2.0
            elif E_gs > 5.0 and E_in > 4.0:
                status = "HIGH_POWER_STABLE (重载稳压/大格局)"
                sai_base = 0.1
                
            sai = sai_base * geo_factor
            
            return {
                "chart": chart,
                "category": status,
                "sai": f"{sai:.2f}",
                "rectification_efficiency": f"{efficiency:.2f}",
                "bridge_saturation": f"{saturation:.2f}",
                "E_input": f"{E_gs:.2f}",
                "E_transformer": f"{E_in:.2f}",
                "label": " ".join([f"{p[0]}{p[1]}" for p in chart]),
                "audit_mode": "GYPS_V4.3_RECTIFIER",
                "topic_name": "官印相生 (GYPS)",
                "stress": f"{sai:.2f}"
            }

        if pattern_id == "CWJG_FEEDBACK_LOOP":
            # ============================================================
            # [QGA V4.3] MOD_117: CWJG 财官联动多级增益反馈模型
            # 物理定义：财星（燃料）注入官杀（发电机），产生级联压制。
            # ============================================================
            E_wealth = 0.0 # 财星 (Fuel Injection)
            E_guan = 0.0   # 官杀 (Generator/Load)
            E_dm = 1.0     # 日主基础强度
            
            all_parts = list(chart[:4]) + [luck_pillar, annual_pillar]
            for i, p in enumerate(all_parts):
                st, br = p
                if not st: continue
                ts = BaziParticleNexus.get_shi_shen(st, dm)
                w = 3.0 if i < 4 else 1.5
                if ts in ["正财", "偏财"]: E_wealth += w
                elif ts in ["正官", "七杀"]: E_guan += w
            
            if E_wealth < 0.5 or E_guan < 0.5: return None
            
            # 核心算法：[Gain_Feedback_Ratio]
            # 反馈增益 = 财能级 * 官能级
            gain = E_wealth * E_guan
            
            # 判定日主是否能承荷
            # 简单日主强度判定（是否有印、比）
            dm_strength = sum(1 for i, (st, br) in enumerate(chart[:4]) if BaziParticleNexus.get_shi_shen(st, dm) in ["正印", "偏印", "比肩", "劫财"])
            
            load_factor = gain / max(1.0, dm_strength * 2.0)
            
            sai_base = load_factor * 1.5
            status = "FEEDBACK_OPERATIONAL"
            
            if load_factor > 3.0:
                status = "OVERVOLT_BURNOUT (财生杀重/系统烧毁)"
                sai_base *= 2.5
            elif load_factor < 0.5:
                status = "IDLE_LOAD (负载空转)"
                sai_base = 0.5
            else:
                status = "POWER_AMPLIFIED (财官联动/动力增强)"
                sai_base = 0.2
                
            sai = sai_base * geo_factor
            
            return {
                "chart": chart,
                "category": status,
                "sai": f"{sai:.2f}",
                "feedback_gain": f"{gain:.2f}",
                "load_ratio": f"{load_factor:.2f}",
                "E_wealth": f"{E_wealth:.2f}",
                "E_guan": f"{E_guan:.2f}",
                "label": " ".join([f"{p[0]}{p[1]}" for p in chart]),
                "audit_mode": "CWJG_V4.3_FEEDBACK",
                "topic_name": "财官联动 (CWJG)",
                "stress": f"{sai:.2f}"
            }

        if pattern_id == "YGZJ_MONOPOLE_ENERGY":
            # ============================================================
            # [QGA V4.3.5] MOD_121: YGZJ 羊刃单极高能等离子体模型
            # 语义：羊刃格且天干无官杀。定义为“露天核反应堆”。
            # ============================================================
            month_br = chart[1][1]
            # 判定羊刃月令 (帝旺位)
            DY_TABLE = {"甲": "卯", "乙": "寅", "丙": "午", "丁": "巳", "戊": "午", "己": "巳", "庚": "酉", "辛": "申", "壬": "子", "癸": "亥"}
            if month_br != DY_TABLE.get(dm):
                return None
            
            # 官杀约束检查 (天干)
            if any(BaziParticleNexus.get_shi_shen(st, dm) in ["正官", "七杀"] for st, br in chart[:4]):
                return None
            
            # 1. 能量统计
            E_peer = 0.0     # 比劫 (High Energy Fuel)
            E_barrier = 1.0  # 约束隔离层 (Resource/Support)
            E_wealth = 0.0   # 财星 (Target to be incinerated)
            
            all_parts = list(chart[:4]) + [luck_pillar, annual_pillar]
            for i, p in enumerate(all_parts):
                st, br = p
                if not st: continue
                ts = BaziParticleNexus.get_shi_shen(st, dm)
                w = 3.0 if i < 4 else 1.5
                if ts in ["比肩", "劫财"]: E_peer += w
                elif ts in ["正引", "偏印"]: E_barrier += w * 0.5 # 印星有一定约束
                elif ts in ["正财", "偏财"]: E_wealth += w
            
            # 藏干修正
            for st, br in chart[:4]:
                hidden = BaziParticleNexus.get_branch_weights(br)
                for hs, w_hidden in hidden:
                    hg = BaziParticleNexus.get_shi_shen(hs, dm)
                    energy = w_hidden / 10.0
                    if hg in ["比肩", "劫财"]: E_peer += energy
                    elif hg in ["正印", "偏印"]: E_barrier += energy * 0.3
                    elif hg in ["正财", "偏财"]: E_wealth += energy
            
            # 2. 核心算法：[Destruction_Index]
            # DI = E_peer^2 / D_barrier
            di = (E_peer ** 2) / max(0.1, E_barrier)
            
            # 3. 物理判定：Wealth Incineration (热力学溢出)
            is_wealth_incinerated = E_peer > 12.0 and E_wealth > 0
            
            # 4. SAI 应力计算
            # 羊刃无制，SAI 随 DI 呈非线性增长
            sai_base = (di / 40.0) * (1.5 if is_wealth_incinerated else 1.0)
            
            status = "MONOPOLE_ACTIVE"
            if is_wealth_incinerated:
                status = "WEALTH_INCINERATION (群比夺财/热寂效应)"
                sai_base *= 2.0
            elif di > 20.0:
                status = "HIGH_ENERGY_ERUPTION (高能爆发/露天能核)"
                sai_base *= 1.5
            elif E_barrier > 5.0:
                status = "CONTAINED_PLASMA (受控等离子体)"
                sai_base *= 0.8
                
            sai = sai_base * geo_factor
            
            return {
                "chart": chart,
                "category": status,
                "sai": f"{sai:.2f}",
                "destruction_index": f"{di:.2f}",
                "E_peer_density": f"{E_peer:.2f}",
                "E_barrier_resistance": f"{E_barrier:.2f}",
                "wealth_incineration": "TRIGGERED" if is_wealth_incinerated else "NONE",
                "label": " ".join([f"{p[0]}{p[1]}" for p in chart]),
                "audit_mode": "YGZJ_V4.3.5_MONOPOLE",
                "topic_name": "羊刃格 (YGZJ)",
                "stress": f"{sai:.2f}"
            }

        if pattern_id == "YHGS_THERMODYNAMIC_ENTROPY":
            # ============================================================
            # [QGA V4.3.5] MOD_122: YHGS 调候热力学熵值平衡系统 (Step 2)
            # 物理定义：计算全量熵值与效率损耗。
            # 冷源: 金水, 热源: 木火, 缓冲: 土
            # ============================================================
            month_br = chart[1][1]
            # 1. 基础温标定标 (Seasonal Base Temperature)
            TEMP_MAP = {
                "寅": 15, "卯": 20, "辰": 25, # 春: 温
                "巳": 35, "午": 45, "未": 40, # 夏: 热
                "申": 15, "酉": 10, "戌": 5,  # 秋: 凉
                "亥": -5, "子": -15, "丑": -10 # 冬: 寒
            }
            T_base = TEMP_MAP.get(month_br, 20)
            
            # 2. 能量统计 (Thermal Flux)
            E_heat = 0.0 # 木火 (Heat Source)
            E_cold = 0.0 # 金水 (Heat Sink)
            E_buffer = 0.0 # 土 (Thermal Mass)
            
            all_particles = list(chart[:4]) + [luck_pillar, annual_pillar]
            for i, p in enumerate(all_particles):
                st, br = p
                if not st: continue
                elem, pol, _ = BaziParticleNexus.STEMS[st]
                weight = 3.0 if i < 4 else 1.5
                if elem in ["Wood", "Fire"]: E_heat += weight
                elif elem in ["Metal", "Water"]: E_cold += weight
                elif elem in ["Earth"]: E_buffer += weight
                
            for st, br in chart[:4]:
                hidden = BaziParticleNexus.get_branch_weights(br)
                for hs, w in hidden:
                    elem_h, _, _ = BaziParticleNexus.STEMS[hs]
                    energy = w / 10.0
                    if elem_h in ["Wood", "Fire"]: E_heat += energy
                    elif elem_h in ["Metal", "Water"]: E_cold += energy
                    elif elem_h in ["Earth"]: E_buffer += energy
            
            # 3. 核心计算
            # 系统温度 T_sys (简化线性模型)
            # T_sys = T_base + (E_heat - E_cold) * 5.0
            T_sys = T_base + (E_heat - E_cold) * 5.0
            
            # 系统熵值 S (衡量无序度)
            # S = ln(1 + |E_heat - E_cold|) / (1 + E_buffer)
            entropy = math.log(1 + abs(E_heat - E_cold)) / (1 + E_buffer * 0.2)
            
            # 4. 效率损耗系数 Eta (Efficiency Factor)
            # 理想工作温区: 15°C - 30°C
            if T_sys < 0:
                eta = max(0.2, 1.0 - abs(T_sys) / 50.0) # 超导冻结倾向
                status = "SUPERCONDUCTIVE_FREEZE (温控失效/冷启动失败)"
            elif T_sys > 50:
                eta = max(0.2, 1.0 - (T_sys - 30) / 60.0) # 热坍缩倾向
                status = "THERMAL_COLLAPSE (热力坍缩/过热熔断)"
            else:
                eta = 1.0 - (abs(T_sys - 22) / 100.0) # 稳态
                status = "THERMAL_STABLE (调候稳态)"
            
            # 5. 调候救应 (Thermal Recovery)
            recovery_boost = 0.0
            has_recovery = False
            # 寒冬需丙火, 炎夏需癸水
            if month_br in ["亥", "子", "丑", "申", "酉"]: # 寒凉月
                if any(p[0] == "丙" for p in all_particles):
                    recovery_boost = 0.4
                    has_recovery = True
            elif month_br in ["巳", "午", "未", "辰", "戌"]: # 炎燥月
                if any(p[0] == "癸" for p in all_particles):
                    recovery_boost = 0.4
                    has_recovery = True
            
            eta = min(1.0, eta + recovery_boost)
            if has_recovery: 
                status += " (RECOVERY_ACTIVE)"
            
            # SAI 响应: 熵值越高且效率越低，SAI 越高
            sai = (entropy * 2.0) / max(0.1, eta) * geo_factor
            
            return {
                "chart": chart,
                "category": status,
                "sai": f"{sai:.2f}",
                "system_temperature": f"{T_sys:.1f}°C",
                "system_entropy": f"{entropy:.2f}",
                "efficiency_eta": f"{eta:.2f}",
                "thermal_recovery": "ACTIVE" if has_recovery else "NONE",
                "heat_source": f"{E_heat:.2f}",
                "heat_sink": f"{E_cold:.2f}",
                "label": " ".join([f"{p[0]}{p[1]}" for p in chart]),
                "audit_mode": "YHGS_V4.3.5_THERMO",
                "topic_name": "调候格 (YHGS)",
                "stress": f"{sai:.2f}"
            }

        if pattern_id == "LYKG_LC_SELF_LOCKING":
            # ============================================================
            # [QGA V4.3.5] MOD_123: LYKG 禄位自锁自感回路 (Step 3)
            # 物理定义：日主与禄位形成超导自感线圈，提供系统惯性。
            # ============================================================
            
            # 1. 禄位识别与自感定标 (Lu-Position Detection)
            LU_TABLE = {"甲": "寅", "乙": "卯", "丙": "巳", "丁": "午", "戊": "巳", "己": "午", "庚": "申", "辛": "酉", "壬": "亥", "癸": "子"}
            lu_target = LU_TABLE.get(dm)
            
            if lu_target not in branches:
                return None
            
            # 2. 统计自感节点数量与强度
            lu_count = sum(1 for br in branches if br == lu_target)
            
            # 环境冲击检测 (Clash Check for Inductor)
            CLASHES = {"子午", "午子", "丑未", "未丑", "寅申", "申寅", "卯酉", "酉卯", "辰戌", "戌辰", "巳亥", "亥巳"}
            clash_count = 0
            # 检查是否有地支冲禄，特别是流年大运
            for i, p in enumerate([luck_pillar, annual_pillar]):
                if p[1] and (p[1] + lu_target) in CLASHES:
                    clash_count += (2.0 if i == 1 else 1.0) # 流年冲击权重大
            
            # 3. 核心计算
            # 自感系数 L: 基础由节点数决定，受冲击而衰减
            L_base = lu_count * 1.5
            inductance_L = max(0.1, L_base / (1.0 + clash_count * 2.0))
            
            # 抗冲击惯性余量 M_i
            # 估算日主基础能级 (比劫 + 正偏印)
            E_dm_core = 1.0
            for i, p in enumerate(list(chart[:4]) + [luck_pillar, annual_pillar]):
                st = p[0]
                if not st: continue
                ts = BaziParticleNexus.get_shi_shen(st, dm)
                w = 3.0 if i < 4 else 1.5
                if ts in ["比肩", "劫财", "正印", "偏印"]: E_dm_core += w
                
            # 惯性余量: Mi = (E_dm * L) / (External_Stress + 1)
            # 外部压力估算 (官杀能级)
            E_stress = 0.5
            for i, p in enumerate(list(chart[:4]) + [luck_pillar, annual_pillar]):
                st = p[0]
                if not st: continue
                if BaziParticleNexus.get_shi_shen(st, dm) in ["正官", "七杀"]:
                    E_stress += (3.0 if i < 4 else 2.0)
            
            mi = (E_dm_core * inductance_L) / (E_stress * 0.5 + 1.0)
            
            # 4. 物理判定
            status = "INERTIA_STABLE"
            sai_base = 0.3
            
            # 自激死锁判定: 能量输出过低，且自感回路过强
            E_output = sum(1 for i, (st, br) in enumerate(chart[:4]) if BaziParticleNexus.get_shi_shen(st, dm) in ["食神", "伤官", "正财", "偏财"])
            is_deadlock = inductance_L > 4.0 and E_output < 1.0
            
            # 磁饱和崩溃判定 (冲禄)
            is_clash_collapse = clash_count > 1.5 and L_base > 2.0
            
            if is_clash_collapse:
                status = "MAGNETIC_SATURATION_COLLAPSE (冲禄/磁饱和崩溃)"
                sai_base = 8.0 + (clash_count * 3.0)
            elif is_deadlock:
                status = "OSCILLATION_DEADLOCK (自激死锁/自闭能核)"
                sai_base = 4.5
            elif mi < 0.5:
                status = "INERTIA_DEFICIT (惯性不足/脆性系统)"
                sai_base = 2.0
            elif inductance_L > 3.0:
                status = "TOPOLOGY_LOCKED (拓扑锁定/超强稳态)"
                sai_base = 0.1
                
            sai = sai_base * geo_factor
            
            return {
                "chart": chart,
                "category": status,
                "sai": f"{sai:.2f}",
                "inductance_L": f"{inductance_L:.2f}",
                "inertia_margin_mi": f"{mi:.2f}",
                "self_locking_strength": f"{L_base:.2f}",
                "clash_impact": f"{clash_count:.1f}",
                "is_deadlock": "YES" if is_deadlock else "NO",
                "label": " ".join([f"{p[0]}{p[1]}" for p in chart]),
                "audit_mode": "LYKG_V4.3.5_LC_CIRCUIT",
                "topic_name": "禄位自锁 (LYKG)",
                "stress": f"{sai:.2f}"
            }

        if pattern_id == "JJGG_QUANTUM_TUNNELING":
            # ============================================================
            # [QGA V4.3.5] MOD_124: JJGG 虚空能量量子隧道注入 (Step 4)
            # ============================================================
            month_br = chart[1][1]
            
            # 1. 结构谐振腔识别 (Resonance Cavity Identification)
            is_jlc = dm == "庚" and all(br in branches for br in ["申", "子", "辰"])
            is_ftlm = dm in ["庚", "壬"] and branches.count("子") >= 2 and "午" not in branches
            is_rqlb = dm == "壬" and branches.count("辰") >= 2
            
            if not (is_jlc or is_ftlm or is_rqlb):
                return None
            
            # 2. 拓扑完整度 (Integrity) 计算
            integrity = 1.0
            if is_jlc:
                # 检查地支完整度 (申子辰齐备为 1.0)
                unique_br = set(branches)
                found_count = sum(1 for target in ["申", "子", "辰"] if target in unique_br)
                integrity = found_count / 3.0
            elif is_ftlm:
                integrity = min(1.0, branches.count("子") / 3.0)
            elif is_rqlb:
                integrity = min(1.0, branches.count("辰") / 3.0)
                
            # 杂气干扰判定 (Interference)
            # 遥感格局最忌官杀显露（实态干扰虚态）
            E_real_guan = 0.0
            for i, (st, br) in enumerate(chart[:4]):
                if BaziParticleNexus.get_shi_shen(st, dm) in ["正官", "七杀"]:
                    E_real_guan += 3.0
            
            interference = E_real_guan * 2.0
            
            # 3. 核心计算：量子隧道穿透几率 Pt
            # Pt = exp(-1/Integrity) / (1 + Interference)
            pt = math.exp(-1.0 / max(0.1, integrity)) / (1.0 + interference)
            
            # 虚态注入能级 V_tunnel
            # 假定虚空能级恒定为 10.0 原子能单位
            V_void = 10.0
            
            # 季节谐振 (Resonance Factor)
            # 井栏叉(金水)喜冬, 飞天禄马(水)喜冬
            resonance = 1.0
            if is_jlc or is_ftlm:
                if month_br in ["亥", "子", "丑"]: resonance = 1.5
                elif month_br in ["巳", "午", "未"]: resonance = 0.5
            
            v_tunnel = pt * V_void * resonance
            
            # 4. 坍缩失稳压力测试 (Collapse Stress)
            # 检测是否有冲穿破坏了谐振腔
            E_crash = 0.0
            CLASH_MAP = {"子": "午", "午": "子", "申": "寅", "寅": "申", "辰": "戌", "戌": "辰"}
            
            check_targets = []
            if is_jlc: check_targets = ["申", "子", "辰"]
            elif is_ftlm: check_targets = ["子"]
            elif is_rqlb: check_targets = ["辰"]
            
            active_crash = False
            for target in check_targets:
                clash_with = CLASH_MAP.get(target)
                if clash_with and (clash_with in [luck_pillar[1], annual_pillar[1]]):
                    E_crash += 5.0
                    active_crash = True
            
            # SAI 响应: 隧道关闭时的瞬间能级跌落
            # 基础 SAI 取决于注入能级, 但若发生崩塌, SAI 激增
            if active_crash:
                status = "TUNNEL_COLLAPSE (隧道坍缩/能级骤降)"
                sai = (v_tunnel + 1) * E_crash * geo_factor
            elif pt < 0.1:
                status = "TUNNEL_BLOCKED (隧道屏蔽/干扰过重)"
                sai = 2.0
            else:
                status = "TUNNEL_INJECTION_ACTIVE (隧道激活/虚空注入)"
                sai = (0.5 / pt) * geo_factor # 注入越稳，应力越低
                
            return {
                "chart": chart,
                "category": status,
                "sai": f"{sai:.2f}",
                "tunneling_probability_pt": f"{pt:.3f}",
                "virtual_energy_v_tunnel": f"{v_tunnel:.2f}",
                "topological_integrity": f"{integrity:.2f}",
                "interference_level": f"{interference:.2f}",
                "resonance_factor": f"{resonance:.2f}",
                "is_active_crash": "YES" if active_crash else "NO",
                "label": " ".join([f"{p[0]}{p[1]}" for p in chart]),
                "audit_mode": "JJGG_V4.3.5_TUNNEL",
                "topic_name": "量子隧道 (JJGG)",
                "stress": f"{sai:.2f}"
            }

        if pattern_id == "TYKG_PHASE_RESONANCE":
            # ============================================================
            # [QGA V4.4.0] MOD_125: TYKG 专旺相位共振 (Step 5)
            # 物理定义：同频粒子高度对齐产生的相干态驻波能量增强。
            # ============================================================
            
            # 1. 计算粒子丰度 (Particle Abundance)
            # 获取全量五行分布 ( stems + branches )
            elements = []
            for st, br in chart:
                elements.append(BaziParticleNexus.get_element(st))
                # 支内含多个能量，这里取本气简化
                elements.append(BaziParticleNexus.get_branch_main_element(br))
            
            dm_element = BaziParticleNexus.get_element(dm)
            
            # 统计同频粒子 (与日主同类或生助日主)
            count_dm = elements.count(dm_element)
            count_support = 0
            # 这里简化逻辑：统计绝对同频粒子 (BiJie)
            
            # 2. 计算相干系数 C (Coherence Coefficient)
            # C = (同频数量 / 总数量) * (1 - 杂质率)
            # 杂质定义为克制或泄化日主的粒子
            count_total = len(elements)
            coherent_ratio = count_dm / count_total
            
            count_impurity = 0
            for el in elements:
                # 简单的五行生克逻辑 (简化版)
                if BaziParticleNexus.is_clash_element(dm_element, el): # 客观克制
                    count_impurity += 1
            
            impurity_rate = count_impurity / count_total
            
            # 相干系数 C
            c_coeff = coherent_ratio * (1.0 - impurity_rate)
            
            # 3. 计算共振增益 G (Resonance Gain)
            # G = Log10(1 + C * 100)
            gain_g = math.log10(1.0 + c_coeff * 100.0) if c_coeff > 0 else 1.0
            
            # 4. 系统稳定性判定 (Resonance Stability)
            # 只有达到基础一致性阈值才被记录为“全量审计命中”
            if c_coeff > 0.4:
                status = "RESONANCE_SUPER_STABLE (超稳态共振)"
                sai = (1.0 / (gain_g + 1.0)) * geo_factor
            elif c_coeff > 0.15:
                status = "PHASE_COHERENT (相位一致)"
                sai = 2.0 * geo_factor
            else:
                return None # 过滤掉退相干样本，不计入审计命中量
                
            return {
                "chart": chart,
                "category": status,
                "sai": f"{sai:.2f}",
                "coherence_coefficient_c": f"{c_coeff:.3f}",
                "resonance_gain_g": f"{gain_g:.2f}",
                "impurity_rate": f"{impurity_rate:.2f}",
                "label": " ".join([f"{p[0]}{p[1]}" for p in chart]),
                "audit_mode": "TYKG_V4.4.0_RESONANCE",
                "topic_name": "专旺共振 (TYKG)",
                "stress": f"{sai:.2f}"
            }

        if pattern_id == "CWJS_QUANTUM_TRANSITION":
            # ============================================================
            # [QGA V4.4.0] MOD_126: CWJS 弃命相变状态切换 (Step 6)
            # 物理定义：日主放弃能量独立性，并入外部强场的零阻抗态。
            # ============================================================
            
            # 1. 计算日主内压 P_dm (原局根气深度)
            dm_element = BaziParticleNexus.get_element(dm)
            dm_roots = []
            for _, br in chart:
                hidden = BaziParticleNexus.BRANCHES.get(br, [None, 0, []])[2]
                for h_stem, h_weight in hidden:
                    if BaziParticleNexus.get_element(h_stem) == dm_element:
                        dm_roots.append(h_weight)
            
            p_dm = sum(dm_roots) / 10.0 # 标准化内能
            
            # 2. 计算外部压强 P_ext (强场能级)
            # 寻找主导外部场 (从财或从杀)
            elements_ext = []
            for st, br in chart:
                elements_ext.append(BaziParticleNexus.get_element(st))
                elements_ext.append(BaziParticleNexus.get_branch_main_element(br))
            
            # 统计克制与泄化日主的粒子
            p_ext = 0.0
            for el in elements_ext:
                if BaziParticleNexus.is_clash_element(dm_element, el): # 官杀场
                    p_ext += 1.5
                # 这里简化：不考虑食伤泄化，专注压强比
            
            # 3. 计算相变阈值 T_t (Transition Threshold)
            # T_t = P_ext / (P_dm + 1.0)
            t_t = p_ext / (p_dm + 1.0)
            
            # 4. 相变判定与状态切换
            if t_t > 4.2: # 临界压强比
                status = BaziParticleNexus.STATE_SUBORDINATE
                # SAI 重置：零阻抗运行
                sai = 0.12 * (1.0 / (t_t + 1.0)) * geo_factor
            elif t_t > 1.8:
                status = BaziParticleNexus.STATE_INTERMEDIATE
                sai = 4.5 * geo_factor # 相变抖动区，阻抗波动
            else:
                status = BaziParticleNexus.STATE_ANTAGONISTIC
                sai = 12.0 * geo_factor # 顽强抵抗态，阻抗极大
            
            return {
                "chart": chart,
                "category": status,
                "sai": f"{sai:.2f}",
                "transition_threshold_tt": f"{t_t:.2f}",
                "external_pressure": f"{p_ext:.2f}",
                "internal_energy_pdm": f"{p_dm:.2f}",
                "label": " ".join([f"{p[0]}{p[1]}" for p in chart]),
                "audit_mode": "CWJS_V4.4.0_TRANSITION",
                "topic_name": "弃命相变 (CWJS)",
                "stress": f"{sai:.2f}"
            }

        if pattern_id == "MHGG_REVERSION_DYNAMICS":
            # ============================================================
            # [QGA V4.4.0] MOD_127: MHGG 还原动力学崩塌 (Step 7)
            # 物理定义：化气格在遭遇“还原剂”冲击时的属性稳定性审计。
            # ============================================================
            
            # 1. 识别化气倾向并提取“化神”
            # 定义化合对与结果化神
            TRANS_MAP = {
                frozenset(['甲', '己']): 'Earth',
                frozenset(['乙', '庚']): 'Metal',
                frozenset(['丙', '辛']): 'Water',
                frozenset(['丁', '壬']): 'Wood',
                frozenset(['戊', '癸']): 'Fire',
            }
            
            trans_god = None
            found_pair = None
            for p1, p2 in [(stems[0], stems[2]), (stems[0], stems[1]), (stems[2], stems[3])]:
                pair = frozenset([p1, p2])
                if pair in TRANS_MAP:
                    trans_god = TRANS_MAP[pair]
                    found_pair = pair
                    break
            
            if not trans_god:
                return None # 非化气格，不计入审计命中
            
            # 2. 计算锁定势能 Ep (Locking Potential)
            # Ep = C_purity * Resonance_season
            # 统计支内化神丰度
            branch_elements = [BaziParticleNexus.get_branch_main_element(br) for br in branches]
            count_god = branch_elements.count(trans_god)
            c_purity = count_god / 4.0
            
            # 季节共振 (月令强度)
            month_br = branches[1]
            season_mult = PC.SEASONAL_MATRIX.get(month_br, {}).get(trans_god, 0.5)
            
            ep = c_purity * season_mult
            
            # 3. 计算还原冲击力 Er (Reversion Stress)
            # 寻找还原剂 (克制化神的元素)
            catalyst_element = PC.CONTROL.get(trans_god, "None")
            count_catalyst = stems.count(BaziParticleNexus.get_shi_shen("Unknown", "Unknown")) # 占位
            # 实际统计 stems 和 branches 中的还原粒子
            all_elements = [BaziParticleNexus.get_element(s) for s in stems]
            for br in branches:
                all_elements.append(BaziParticleNexus.get_branch_main_element(br))
            
            i_catalyst = all_elements.count(catalyst_element) * 0.5
            
            # 还原比率
            er = i_catalyst / (ep + 0.1)
            
            # 4. 崩塌判定与属性闪变
            if er > 1.2:
                status = "PROPERTY_FLASH (属性瞬间还原/系统崩塌)"
                sai = 100.0 * (er - 1.2 + 1.0) * geo_factor # 超新星爆发
            elif er > 0.6:
                status = "EQUILIBRIUM_SHIFT (平衡左移/属性动摇)"
                sai = 8.5 * er * geo_factor
            else:
                status = "LOCKED_SYNTHETIC (属性锁定/亚稳态稳定)"
                sai = 0.5 * (1.0 / (ep + 1.0)) * geo_factor
                
            return {
                "chart": chart,
                "category": status,
                "sai": f"{sai:.2f}",
                "locking_potential_ep": f"{ep:.3f}",
                "reversion_stress_er": f"{er:.3f}",
                "trans_god": trans_god,
                "label": " ".join([f"{p[0]}{p[1]}" for p in chart]),
                "audit_mode": "MHGG_V4.4.0_REVERSION",
                "topic_name": "还原动力 (MHGG)",
                "stress": f"{sai:.2f}"
            }

        if pattern_id == "GXYG_VIRTUAL_GAP":
            # ============================================================
            # [QGA V4.5.0] MOD_128: GXYG 拱夹空间虚拟势阱 (Step 8)
            # 物理定义：地支拓扑空位通过引力干涉感生出的虚能增益。
            # ============================================================
            
            branch_order = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
            
            # 1. 识别 拱位 (Gap Detection)
            # 扫描所有地支对，寻找跨度为 2 的组合
            gaps = []
            for i in range(len(branches)):
                for j in range(i + 1, len(branches)):
                    b1 = branches[i]
                    b2 = branches[j]
                    idx1 = branch_order.index(b1)
                    idx2 = branch_order.index(b2)
                    
                    # 计算循环距离
                    dist = abs(idx1 - idx2)
                    if dist == 2 or dist == 10:
                        mid_idx = (min(idx1, idx2) + 1) % 12
                        if dist == 10: mid_idx = (max(idx1, idx2) + 1) % 12
                        virtual_branch = branch_order[mid_idx]
                        
                        # 检查原局是否已存在该地支 (填实检查)
                        if virtual_branch not in branches:
                            gaps.append((b1, b2, virtual_branch))
            
            if not gaps:
                return None # 无拱位空隙
            
            # 2. 计算虚拟感应场强 V_ind
            # V_ind = (M1 * M2 / D) * cos(phi)
            hits = []
            total_v_ind = 0.0
            
            for b1, b2, v_br in gaps:
                # 获取质量 (Hidden Stem Total / 10)
                m1 = sum([w for s, w in BaziParticleNexus.get_branch_weights(b1)]) / 10.0
                m2 = sum([w for s, w in BaziParticleNexus.get_branch_weights(b2)]) / 10.0
                
                # 相位差 phi (简化为五行属性夹角)
                e1 = BaziParticleNexus.get_branch_main_element(b1)
                e2 = BaziParticleNexus.get_branch_main_element(b2)
                phi1 = PC.ELEMENT_PHASES.get(e1, 0)
                phi2 = PC.ELEMENT_PHASES.get(e2, 0)
                cos_phi = math.cos(phi1 - phi2)
                
                v_ind = (m1 * m2 / 2.0) * cos_phi
                if v_ind > 0.01:
                    total_v_ind += v_ind
                    hits.append(f"{b1}{b2}拱{v_br}")

            if total_v_ind <= 0.01:
                return None # 无有效势阱增益

            # 3. SAI 负压补偿 (SAI Correction)
            # dSAI = -0.5 * V_ind
            dsai = -0.5 * total_v_ind
            base_sai = 5.0 # 基础参考基准
            final_sai = max(0.1, base_sai + dsai) * geo_factor
            
            return {
                "chart": chart,
                "category": "VIRTUAL_POTENTIAL_WELL (虚拟势阱补给)",
                "sai": f"{final_sai:.2f}",
                "dsai_correction": f"{dsai:.2f}",
                "virtual_induction_v_ind": f"{total_v_ind:.3f}",
                "gaps": hits,
                "label": " ".join([f"{p[0]}{p[1]}" for p in chart]),
                "audit_mode": "GXYG_V4.5.0_GAP",
                "topic_name": "拱夹虚拟 (GXYG)",
                "stress": f"{final_sai:.2f}"
            }

        if pattern_id == "MBGS_STORAGE_POTENTIAL":
            # ============================================================
            # [QGA V4.5.2] MOD_129: MBGS 墓库高压容器系统 (V4.1.2)
            # 物理定义：地支墓库作为非线性高压约束容器。
            # ============================================================
            
            GRAVES = ['辰', '戌', '丑', '未']
            branch_order = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
            
            # --- 第一步：容器底座海选 (Container Screening) ---
            # 穿透审计：提取日/时支命中墓库的样本
            active_graves = []
            total_p_in = 0.0
            
            # 检查日支 (Index 2) 和 时支 (Index 3)
            for i in [2, 3]:
                if i < len(branches) and branches[i] in GRAVES:
                    br = branches[i]
                    # Vb = 墓库势垒高度 (基于藏干质量)
                    m_total = sum([w for s, w in BaziParticleNexus.get_branch_weights(br)]) / 10.0
                    vb_br = m_total * 3.2 # V4.1.2 势垒基准
                    total_p_in += vb_br
                    active_graves.append({"branch": br, "vb": vb_br, "index": i})
            
            if not active_graves:
                return None # 未命中核心墓库容器
            
            # --- 第二步：能核穿透扫描 (Core Penetration) ---
            g_jsg = 0.0
            g_kgg = 0.0
            sub_tags = []
            
            # 1. 金神核检索 (Day/Hour pillars: 癸酉, 己巳, 乙丑)
            js_particles = [('癸', '酉'), ('己', '巳'), ('乙', '丑')]
            for i in [2, 3]: # 日柱 或 时柱
                if i < len(chart) and tuple(chart[i]) in js_particles:
                    # G_jsg = 3.5 * Vb (受激辐射能核)
                    g_jsg += 3.5 * (total_p_in / len(active_graves))
                    sub_tags.append("JSG_CORE_STIMULATED")
            
            # 2. 魁罡核检索 (Day pillar: 壬辰, 庚戌, 庚辰, 戊戌)
            if len(chart) >= 3:
                day_p = tuple(chart[2])
                k_particles = [('庚', '辰'), ('庚', '戌'), ('壬', '辰'), ('戊', '戌')]
                if day_p in k_particles:
                    # G_kgg = -1.8 * Vb (重力畸变压制算子)
                    g_kgg = -1.8 * (total_p_in / len(active_graves))
                    sub_tags.append("KGG_OPERATOR_SCANNED")
            
            # 3. 四库全齐海选 & 坍缩建模 (Collapse Trap Modelling)
            s_sksk = 0.0
            all_brs = set(branches)
            if all(g in all_brs for g in GRAVES):
                # S_sksk = 5.0 * Vb (引力场闭环坍缩项)
                s_sksk = 5.0 * (total_p_in / 4.0)
                sub_tags.append("SKSK_COLLAPSE_陷阱")
                # [JSG] 增强交互：超压缩状态下的二次爆裂
                if g_jsg > 0:
                    g_jsg *= 2.2 
                    sub_tags.append("JSG_SECONDARY_BURST")

            # --- 第三步：复合 SAI 定标 (Calibration) ---
            # 刑冲耦合定标
            total_i_rel = 0.0
            clash_events = []
            for grave in active_graves:
                g_br = grave["branch"]
                for other_br in branches:
                    if abs(branch_order.index(g_br) - branch_order.index(other_br)) == 6:
                        total_i_rel += grave["vb"] * 4.0
                        clash_events.append(f"{g_br}{other_br}冲")
                    if g_br in BaziParticleNexus.PENALTY_GROUPS:
                        for comp in BaziParticleNexus.PENALTY_GROUPS[g_br]['components']:
                            if comp in branches:
                                total_i_rel += grave["vb"] * 1.5
                                clash_events.append(f"{g_br}{comp}刑")

            # mu = 耦合系数 (刑冲匹配时非线性跳变)
            mu = 2.5 if clash_events else 1.0
            s_base = 0.6 * total_p_in + 1.2 * total_i_rel
            
            # SAI_composite = (S_base + mu * (G_jsg + G_kgg + S_sksk)) * geo
            final_sai = (s_base + mu * (g_jsg + g_kgg + s_sksk)) * geo_factor
            
            status = "SINGULARITY_COLLAPSE (引力奇点)" if s_sksk > 0 else ("STORAGE_DISCHARGE (能级喷发)" if clash_events else "METASTABLE_LOCK (约束稳态)")
            
            return {
                "chart": chart,
                "category": f"{status} | V4.1.2",
                "sai": f"{max(0.1, final_sai):.2f}",
                "s_base_stress": f"{s_base:.2f}",
                "s_sksk_collapse": f"{s_sksk:.2f}",
                "v_b_barrier": f"{total_p_in:.2f}",
                "mu_coupling": f"{mu:.2f}",
                "g_core_gain": f"{(g_jsg + g_kgg):.2f}",
                "events": list(set(clash_events)),
                "sub_tags": sub_tags,
                "label": " ".join([f"{p[0]}{p[1]}" for p in chart]),
                "audit_mode": "MBGS_PENETRATION_V4.1.2",
                "topic_name": "墓库高压容器 (MBGS)",
                "stress": f"{max(0.1, final_sai):.2f}"
            }

        if pattern_id == "ZHSG_MIXED_EXCITATION":
            # ============================================================
            # [QGA V4.5.3] MOD_130: ZHSG 杂气复合激发系统 (V4.1.2)
            # 物理定义：地支余气作为多组分非饱和等离子体的能量干涉。
            # ============================================================
            
            # --- 第一步：主态海选 (High-Entropy Mixed Stems) ---
            high_entropy_branches = []
            for i, br in enumerate(branches):
                stems = BaziParticleNexus.get_branch_weights(br)
                if len(stems) >= 2: # 藏干数 >= 2
                    high_entropy_branches.append({
                        "branch": br,
                        "stems": stems,
                        "index": i
                    })
            
            if not high_entropy_branches:
                return None
            
            # --- 第二步：子态穿透扫描 (TSG/YQG) ---
            total_e_excite = 0.0
            total_c_phase = 1.0 # 相位干涉因子
            sub_tags = []
            spectral_gains = []
            
            # 1. TSG 透干激发扫描 (频谱增益)
            t_stems = [p[0] for p in chart]
            for heb in high_entropy_branches:
                for s_qi, w_qi in heb["stems"]:
                    if s_qi in t_stems:
                        # 频谱对齐激发：E_excite = w * 2.0
                        gain = (w_qi / 10.0) * 2.5
                        total_e_excite += gain
                        spectral_gains.append(f"{heb['branch']}->{s_qi}")
                        if "TSG_EXCITE_ACTIVE" not in sub_tags:
                            sub_tags.append("TSG_EXCITE_ACTIVE")
            
            # 2. YQG 月令余气扫描 (背景辐射)
            if len(branches) >= 2:
                month_br = branches[1]
                month_stems = BaziParticleNexus.get_branch_weights(month_br)
                # 如果月令主气不透，而余气透出，触发 YQG 激发
                if len(month_stems) >= 2:
                    main_s = month_stems[0][0]
                    for residual_s, w_res in month_stems[1:]:
                        if residual_s in t_stems and main_s not in t_stems:
                            total_e_excite += (w_res / 10.0) * 1.8
                            sub_tags.append("YQG_MONTHLY_ACTIVE")
            
            # 3. 相位干涉干扰 (Interference Cancellation)
            # 简单模型：不同五行杂气互见产生干涉
            elements = []
            for heb in high_entropy_branches:
                for s_qi, _ in heb["stems"]:
                    elements.append(BaziParticleNexus.get_element(s_qi))
            
            unique_elems = set(filter(None, elements))
            if len(unique_elems) >= 3:
                # 杂乱度极高，相位干涉抑制
                total_c_phase = 0.65
                sub_tags.append("PHASE_CANCELLATION")
            elif len(unique_elems) == 1:
                # 相长干涉
                total_c_phase = 1.4
                sub_tags.append("PHASE_COHERENCE")

            # --- 第三步：复合 SAI 定标 ---
            # S_base = 基准压力
            s_base = sum([len(heb["stems"]) for heb in high_entropy_branches]) * 0.5
            
            # final_sai = S_base + E_excite * C_phase
            final_sai = (s_base + total_e_excite * total_c_phase) * geo_factor
            
            status = "SPECTRAL_RESONANCE (频谱共振)" if "TSG_EXCITE_ACTIVE" in sub_tags else "NON_SATURATED_PLASMA (非饱和态)"
            
            return {
                "chart": chart,
                "category": f"{status} | V4.1.2",
                "sai": f"{max(0.1, final_sai):.2f}",
                "e_excite_energy": f"{total_e_excite:.2f}",
                "c_phase_factor": f"{total_c_phase:.2f}",
                "spectral_gains": spectral_gains,
                "sub_tags": sub_tags,
                "label": " ".join([f"{p[0]}{p[1]}" for p in chart]),
                "audit_mode": "ZHSG_MIXED_V4.5.3",
                "topic_name": "杂气复合激发 (ZHSG)",
                "stress": f"{max(0.1, final_sai):.2f}"
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
                "P_111D": natal_tg.count("比肩") + natal_tg.count("劫财") + natal_tg.count("正印") + natal_tg.count("偏印") # 从强/旺
            }
            
            sub_package_id = max(field_counts, key=field_counts.get)
            if field_counts[sub_package_id] < 1: return None 

            # Screening Validation
            if sub_package_id in ["P_111A", "P_111B"]:
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
            
            pair_info = TRANSFORM_GOAL.get((dm, target_partner))
            if not pair_info: return None
            
            goal_elem, sub_pkg = pair_info

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
            if annual_p[0] and PAIRS.get(annual_p[0]) in [dm, target_partner]:
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
