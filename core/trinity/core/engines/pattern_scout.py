
import logging
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

    def _deep_audit(self, chart: List[Tuple[str, str]], pattern_id: str, geo_context: dict = None) -> Optional[Dict[str, Any]]:
        """[V14.8.4] Deep audit with GEO field correction support."""
        if len(chart) < 4: return None
        
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
        
        ten_gods = [BaziParticleNexus.get_shi_shen(s, dm) for s in stems]
        
        if pattern_id == "SHANG_GUAN_JIAN_GUAN":
            # ============================================================
            # [V2.0] 伤官见官失效模型 - Master Protocol Implementation
            # ============================================================
            # Phase 1: 古代硬判据 (Ancient Hard Rules)
            # - 天干必须同时有"伤官"和"正官/七杀"
            # - 不允许食神代替伤官（严格定义）
            # ============================================================
            
            # 1.1 天干硬约束: 必须有伤官 (原局四柱)
            natal_tg = ten_gods[:4]
            if "伤官" not in natal_tg:
                return None  # 古法: 无伤官不成格
            
            # 1.2 天干或六柱必须有正官/七杀
            all_tg = ten_gods
            has_guan = any(g in ["正官", "七杀"] for g in all_tg)
            if not has_guan:
                return None  # 无官星碰撞对象
            
            # ============================================================
            # Phase 2: 三维全息扫描 + 注入权重
            # - GEO权重: 0.3 (地理阻抗)
            # - 大运权重: 0.5 (静态电势)  
            # - 流年权重: 1.0 (脉冲信号)
            # ============================================================
            INJECTION_WEIGHTS = {
                'year': 0.5, 'month': 3.0, 'day': 1.0, 'hour': 0.8,
                'luck': 0.5,   # 大运静态电势
                'annual': 1.0  # 流年脉冲信号
            }
            
            p_labels = ['year', 'month', 'day', 'hour', 'luck', 'annual']
            season_mult = PC.SEASONAL_MATRIX.get(month_branch, {})
            
            # 全息能量点采集
            points = []
            stem_gods_set = set(ten_gods)
            
            for i, p_label in enumerate(p_labels):
                if i >= len(chart): continue
                s, b = chart[i]
                p_weight = INJECTION_WEIGHTS.get(p_label, 1.0)
                
                # A: 天干能量 (直接传导)
                tg_s = BaziParticleNexus.get_shi_shen(s, dm)
                s_elem = BaziParticleNexus.STEMS[s][0]
                geo_mod = geo_mult.get(s_elem, 1.0)  # GEO地理阻抗
                s_energy = PC.BASE_SCORE * p_weight * season_mult.get(s_elem, 1.0) * geo_mod
                points.append({
                    "pos": i, "type": "stem", "god": tg_s, 
                    "energy": s_energy, "weight": 1.0, "elem": s_elem,
                    "is_natal": i < 4
                })
                
                # B: 地支藏干能量 (维度感应)
                hidden = BaziParticleNexus.get_branch_weights(b)
                for h_stem, h_w in hidden:
                    tg_h = BaziParticleNexus.get_shi_shen(h_stem, dm)
                    dim_coeff = 1.1 if tg_h in stem_gods_set else 0.6
                    h_elem = BaziParticleNexus.STEMS[h_stem][0]
                    geo_mod_h = geo_mult.get(h_elem, 1.0)
                    h_energy = PC.BASE_SCORE * p_weight * season_mult.get(h_elem, 1.0) * (float(h_w) / 10.0) * dim_coeff * geo_mod_h
                    points.append({
                        "pos": i, "type": "hidden", "god": tg_h, 
                        "energy": h_energy, "weight": dim_coeff, "elem": h_elem,
                        "is_natal": i < 4
                    })

            # ============================================================
            # Phase 3: 碰撞检测 (Collision Detection)
            # ============================================================
            attackers = [p for p in points if p["god"] == "伤官"]  # 严格: 只看伤官
            officers = [p for p in points if p["god"] in ["正官", "七杀"]]
            
            if not attackers or not officers: 
                return None
            
            # 3.1 计算碰撞强度
            max_sg_e = max(p["energy"] for p in attackers)
            max_zg_e = max(p["energy"] for p in officers)
            collision_ratio = max_sg_e / max(0.01, max_zg_e)
            
            # 3.2 原局伤官能量 vs 外部官星能量
            natal_sg_e = sum(p["energy"] for p in attackers if p["is_natal"])
            external_zg_e = sum(p["energy"] for p in officers if not p["is_natal"])
            
            # 3.3 计算碰撞距离
            sg_core_pos = next(p["pos"] for p in attackers if p["energy"] == max_sg_e)
            zg_core_pos = next(p["pos"] for p in officers if p["energy"] == max_zg_e)
            collision_dist = abs(sg_core_pos - zg_core_pos)
            collision_range = sorted([sg_core_pos, zg_core_pos])
            
            # [V2.1] 月令震源中心加权
            month_sg = any(p["pos"] == 1 and p["god"] == "伤官" for p in points)
            month_zg = any(p["pos"] == 1 and p["god"] in ["正官", "七杀"] for p in points)
            month_core_mult = 1.25 if (month_sg or month_zg) else 1.0

            # ============================================================
            # Phase 4: 保护层审计 (Shield Audit) - Dynamic Threshold
            # - 财星通关: 伤官生财、财生官
            # - 印星护身: 泄官生身
            # - η_shield = Σ(Shield_E) × e^(-0.3 × distance)
            # ============================================================
            protection_total = 0.0
            protection_effective = 0.0
            shield_breakdown = {"财": 0.0, "印": 0.0}
            
            import math
            for p in points:
                p_val = 0.0
                if p["god"] in ["正财", "偏财"]: 
                    p_val = 0.8 * p["weight"]
                    shield_breakdown["财"] += p_val
                elif p["god"] in ["正印", "偏印"]: 
                    p_val = 0.5 * p["weight"]
                    shield_breakdown["印"] += p_val
                
                if p_val > 0:
                    protection_total += p_val
                    # [V2.1] 动态衰减函数: η_shield = Shield_E × e^(-0.3 × dist)
                    dist_to_core = min(abs(p["pos"] - sg_core_pos), abs(p["pos"] - zg_core_pos))
                    decay = math.exp(-0.3 * dist_to_core)
                    protection_effective += (p_val * decay)

            # ============================================================
            # Phase 5: 坍缩阈值检测 (Collapse Detection)
            # [V2.1] 加入五行克制系数 K_clash
            # - 金木对撞: 1.4 (脆性折断)
            # - 水火对撞: 1.2 (汽化损耗)
            # - 其他: 1.0
            # ============================================================
            CLASH_COEFF_MAP = {
                ("Metal", "Wood"): 1.4, ("Wood", "Metal"): 1.4,
                ("Water", "Fire"): 1.2, ("Fire", "Water"): 1.2,
                ("Earth", "Water"): 1.0, ("Water", "Earth"): 1.0,
            }
            
            # 获取伤官和官星的五行
            sg_elem = next((p["elem"] for p in attackers if p["energy"] == max_sg_e), "Earth")
            zg_elem = next((p["elem"] for p in officers if p["energy"] == max_zg_e), "Earth")
            k_clash = CLASH_COEFF_MAP.get((sg_elem, zg_elem), 1.0)
            
            baseline_sai = natal_sg_e * 0.1  # 无官星时的平静态
            
            # 碰撞应力 = (伤官能量 × 官星能量 × 距离因子 × 月令系数 × 克制系数) / (保护层 + 1.0)
            distance_factor = max(0.5, 5 - collision_dist)  # 距离越近压力越大
            current_sai = (max_sg_e * max_zg_e * distance_factor * month_core_mult * k_clash) / max(0.1, protection_effective + 1.0)
            
            # 坍缩率
            collapse_rate = current_sai / max(0.01, baseline_sai)
            
            # ============================================================
            # Phase 6: 判定与分类
            # ============================================================
            COLLAPSE_THRESHOLD = 1.25  # 坍缩阈值
            
            is_shielded = protection_effective > 1.5
            is_collapsed = current_sai > COLLAPSE_THRESHOLD
            
            # 古法安全判定: 有足够通关
            if is_shielded and not is_collapsed:
                return None  # 真正被保护
            
            # 分类
            if current_sai > 2.0:
                category = "高压击穿 (Critical Breakdown)"
            elif current_sai > COLLAPSE_THRESHOLD:
                category = "结构坍缩 (Structural Collapse)"
            elif protection_total > 0.8 and protection_effective < 0.5:
                category = "防御虚化 (Ghost Shield)"
            else:
                category = "应力过载 (Stress Overload)"
            
            # 冲克加成
            has_clash = any(AN.CLASH_MAP.get(chart[i][1]) == chart[j][1] 
                          for i in range(min(4, len(chart))) 
                          for j in range(i+1, min(4, len(chart))))
            if has_clash:
                current_sai *= 1.3
                category = f"{category} + 冲击"
            
            # 电压泵升检测
            has_voltage_pump = any(p["weight"] == 1.1 and p["god"] in ["正官", "七杀"] for p in points)

            return {
                "chart": chart,
                "category": category,
                "stress": f"{current_sai:.2f}",
                "baseline_sai": f"{baseline_sai:.2f}",
                "collapse_rate": f"{collapse_rate:.1f}x",
                "r_ratio": f"{collision_ratio:.2f}",
                "dist": collision_dist,
                "protection": f"有效:{protection_effective:.2f}/总:{protection_total:.1f}",
                "shield_breakdown": f"财:{shield_breakdown['财']:.1f} 印:{shield_breakdown['印']:.1f}",
                "label": " ".join([f"{p[0]}{p[1]}" for p in chart]),
                "audit_mode": "SGJG_V2.1_MASTER_PROTOCOL",
                "voltage_pump": "ACTIVE" if has_voltage_pump else "INACTIVE",
                "geo_element": geo_element,
                "external_injection": f"官星外注:{external_zg_e:.1f}",
                "month_core_mult": f"{month_core_mult:.2f}",
                "k_clash": f"{k_clash:.1f}",
                "sg_elem": sg_elem,
                "zg_elem": zg_elem,
                "standard_verdict": "CRITICAL",
                "spatial_verdict": "CRITICAL" if not is_shielded else "SAFE"
            }
        if pattern_id == "SHANG_GUAN_SHANG_JIN":
            # ============================================================
            # [V2.0] PGB 真空稳态模型 (Vacuum Stability Model)
            # 基于 52 万样本数据驱动定标，废弃古代"伤尽"迷信
            # 核心发现: 财星通关 > 纯净度，强韧来自"混浊"而非"纯净"
            # ============================================================
            
            # Hard Rule 1: Must have Shang Guan (伤官) in stems
            if "伤官" not in ten_gods: return None
            
            # Hard Rule 2: Natal stems must NOT have any 正官/七杀
            if any(tg in ["正官", "七杀"] for tg in ten_gods[:4]): return None
            
            # 1. FULL SPECTRUM SCAN
            p_labels = ['year', 'month', 'day', 'hour', 'luck', 'annual']
            season_mult = PC.SEASONAL_MATRIX.get(month_branch, {})
            points = []
            stem_gods_set = set(ten_gods)

            for i, p_label in enumerate(p_labels):
                if i >= len(chart): continue
                s, b = chart[i]
                p_weight = PC.PILLAR_WEIGHTS.get(p_label, 1.0)
                
                tg_s = BaziParticleNexus.get_shi_shen(s, dm)
                s_elem = BaziParticleNexus.STEMS[s][0]
                geo_corr = geo_mult.get(s_elem, 1.0)
                s_energy = PC.BASE_SCORE * p_weight * season_mult.get(s_elem, 1.0) * geo_corr
                points.append({"pos": i, "type": "stem", "god": tg_s, "energy": s_energy, "elem": s_elem, "is_natal": i < 4})
                
                hidden = BaziParticleNexus.get_branch_weights(b)
                for h_idx, (h_stem, h_w) in enumerate(hidden):
                    tg_h = BaziParticleNexus.get_shi_shen(h_stem, dm)
                    dim_coeff = 1.1 if tg_h in stem_gods_set else 0.6
                    h_elem = BaziParticleNexus.STEMS[h_stem][0]
                    geo_corr_h = geo_mult.get(h_elem, 1.0)
                    h_energy = PC.BASE_SCORE * p_weight * season_mult.get(h_elem, 1.0) * (float(h_w) / 10.0) * dim_coeff * geo_corr_h
                    is_main_qi = (h_idx == 0)
                    points.append({"pos": i, "type": "hidden", "god": tg_h, "energy": h_energy, "elem": h_elem, "is_natal": i < 4, "is_main": is_main_qi})

            # 2. PURITY AUDIT
            natal_hidden_guan = sum(p["energy"] for p in points if p["is_natal"] and p["type"] == "hidden" and p["god"] in ["正官", "七杀"])
            purity = max(0.0, 1.0 - (natal_hidden_guan / 3.0))
            if purity < 0.95: return None
            
            # 3. 五行识别
            dm_elem = BaziParticleNexus.STEMS[dm][0]
            SHENG_CYCLE = {"Wood": "Fire", "Fire": "Earth", "Earth": "Metal", "Metal": "Water", "Water": "Wood"}
            sg_elem = SHENG_CYCLE.get(dm_elem, "Earth")
            
            # 4. [V2.0] 稳态评分计算 (Stability Score)
            wealth_count = sum(1 for p in points if p["god"] in ["正财", "偏财"])
            yin_count = sum(1 for p in points if p["god"] in ["正印", "偏印"])
            
            RESONANCE_FACTOR = {
                ("Wood", "Fire"): -0.5,   # 木火同气加分
                ("Earth", "Metal"): -0.5, # 土金同气加分
                ("Metal", "Water"): 0.5,  # 金水脆性扣分
                ("Fire", "Earth"): 0.3,   # 中等风险
            }
            resonance_mod = RESONANCE_FACTOR.get((dm_elem, sg_elem), 0.0)
            
            stability_score = (wealth_count * 2.0 + yin_count * 1.0) - resonance_mod
            
            # 5. 外部官星分析
            external_guan_points = [p for p in points if not p["is_natal"] and p["god"] in ["正官", "七杀"]]
            external_guan_elem = external_guan_points[0]["elem"] if external_guan_points else None
            
            # 共振窗口
            is_coherent = (external_guan_elem == sg_elem) if external_guan_elem else False
            resonance_state = "STATE_RESONANCE" if is_coherent else "STATE_COLLISION"
            
            # 6. [V2.0] 五行差异化阈值 (按 42600% 跳变率数据定标)
            ELEM_THRESHOLDS = {
                ("Metal", "Water"): 1.25,   # 金水 - 极脆弱
                ("Water", "Wood"): 2.5,     # 水木
                ("Wood", "Fire"): 4.5,      # 木火 - 韧性结构
                ("Fire", "Earth"): 2.5,     # 火土
                ("Earth", "Metal"): 4.5,    # 土金 - 韧性结构
            }
            collapse_threshold = ELEM_THRESHOLDS.get((dm_elem, sg_elem), 2.0)

            # 7. 护盾量化
            hidden_wealth_shield = sum(p["energy"] for p in points if p["type"] == "hidden" and p["god"] in ["正财", "偏财"] and not p.get("is_main", True)) * 0.85
            shield_multiplier = max(0.15, 1.0 - hidden_wealth_shield) if hidden_wealth_shield > 0 else 1.0

            # 8. 应力计算
            total_guan_strength = sum(p["energy"] for p in points if p["god"] in ["正官", "七杀"])
            jump_rate = (total_guan_strength - natal_hidden_guan) / max(0.01, natal_hidden_guan) * 100
            base_stress = (0.1 + (total_guan_strength * 0.5)) * geo_factor * shield_multiplier
            
            # 9. [V2.0] 分类判定 - 基于稳态评分
            if stability_score >= 6.0:
                category = "PGB_STABLE (排骨帮稳态格)"
                stress = base_stress * 0.3
            elif stability_score >= 2.0:
                category = "真空稳态 (Vacuum Stable)"
                stress = base_stress * 0.6
            elif is_coherent:
                category = "共振过载 (Resonant Overload)"
                stress = base_stress * 0.5
            elif jump_rate > 500:
                category = "PGB_CRITICAL_VACUUM (极危真空格)"
                stress = (collapse_threshold + (jump_rate / 10000)) * geo_factor * shield_multiplier
            elif total_guan_strength > 0.5:
                category = "场强扰动 (Perturbed)"
                stress = base_stress
            else:
                category = "真空超导 (Superconductor)"
                stress = base_stress
            
            geo_status = "BOOST" if geo_factor > 1.0 else ("DAMPED" if geo_factor < 1.0 else "NEUTRAL")

            return {
                "chart": chart,
                "category": category,
                "purity": f"{purity:.2f}",
                "stress": f"{stress:.2f}",
                "jump_rate": f"{jump_rate:.1f}%",
                "stability_score": f"{stability_score:.1f}",
                "r_ratio": f"{purity:.2f}",
                "dist": 0,
                "protection": f"财:{wealth_count} 印:{yin_count}",
                "geo_status": geo_status,
                "geo_element": geo_element,
                "label": " ".join([f"{p[0]}{p[1]}" for p in chart]),
                "audit_mode": "SGSJ_V2.0_STABILITY_MODEL",
                "voltage_pump": "ACTIVE" if any(p["energy"] > 2.0 and p["god"] in ["正官", "七杀"] for p in points) else "INACTIVE",
                "pgb_advice": "稳态评分 > 2.0 为安全区。建议增加财星通关介质。",
                "dm_elem": dm_elem,
                "sg_elem": sg_elem,
                "collapse_threshold": f"{collapse_threshold:.2f}",
                "hidden_wealth_shield": f"{hidden_wealth_shield:.2f}",
                "shield_multiplier": f"{shield_multiplier:.2f}",
                "resonance_state": resonance_state,
                "external_guan_elem": external_guan_elem or "N/A",
                "wealth_count": wealth_count,
                "yin_count": yin_count
            }


            for i, p_label in enumerate(p_labels):
                if i >= len(chart): continue
                s, b = chart[i]
                p_weight = PC.PILLAR_WEIGHTS.get(p_label, 1.0)
                
                # A: STEM ENERGY (天干)
                tg_s = BaziParticleNexus.get_shi_shen(s, dm)
                s_elem = BaziParticleNexus.STEMS[s][0]
                geo_corr = geo_mult.get(s_elem, 1.0)
                s_energy = PC.BASE_SCORE * p_weight * season_mult.get(s_elem, 1.0) * geo_corr
                points.append({"pos": i, "type": "stem", "god": tg_s, "energy": s_energy, "elem": s_elem, "is_natal": i < 4})
                
                # B: HIDDEN STEM ENERGY (藏干)
                hidden = BaziParticleNexus.get_branch_weights(b)
                for h_idx, (h_stem, h_w) in enumerate(hidden):
                    tg_h = BaziParticleNexus.get_shi_shen(h_stem, dm)
                    dim_coeff = 1.1 if tg_h in stem_gods_set else 0.6
                    h_elem = BaziParticleNexus.STEMS[h_stem][0]
                    geo_corr_h = geo_mult.get(h_elem, 1.0)
                    h_energy = PC.BASE_SCORE * p_weight * season_mult.get(h_elem, 1.0) * (float(h_w) / 10.0) * dim_coeff * geo_corr_h
                    is_main_qi = (h_idx == 0)  # 主气
                    points.append({"pos": i, "type": "hidden", "god": tg_h, "energy": h_energy, "elem": h_elem, "is_natal": i < 4, "is_main": is_main_qi})

            # 2. PURITY AUDIT: Total Guan/Sha in NATAL Hidden Stems
            natal_hidden_guan = sum(p["energy"] for p in points if p["is_natal"] and p["type"] == "hidden" and p["god"] in ["正官", "七杀"])
            purity = max(0.0, 1.0 - (natal_hidden_guan / 3.0))
            if purity < 0.95: return None
            
            # 3. 识别伤官五行 (日主五行 → 子五行)
            dm_elem = BaziParticleNexus.STEMS[dm][0]
            SHENG_CYCLE = {"Wood": "Fire", "Fire": "Earth", "Earth": "Metal", "Metal": "Water", "Water": "Wood"}
            sg_elem = SHENG_CYCLE.get(dm_elem, "Earth")
            
            # 4. 识别外部官星五行
            external_guan_points = [p for p in points if not p["is_natal"] and p["god"] in ["正官", "七杀"]]
            external_guan_elem = external_guan_points[0]["elem"] if external_guan_points else None
            
            # ============================================================
            # [V1.0] 共振窗口检测 (Coherent Window)
            # 如果官星五行 == 伤官五行，判定为共振态，不是断裂
            # ============================================================
            is_coherent = (external_guan_elem == sg_elem) if external_guan_elem else False
            resonance_state = "STATE_RESONANCE" if is_coherent else "STATE_COLLISION"
            
            # ============================================================
            # [V1.0] 五行差异化断裂阈值 (按 AI 分析师 Phase 4 定标)
            # ============================================================
            ELEM_THRESHOLDS = {
                ("Metal", "Water"): 1.25,   # 金水伤官 - 极脆弱 (31950% 跳变率)
                ("Water", "Wood"): 2.5,     # 水木伤官
                ("Wood", "Fire"): 4.5,      # 木火伤官 - 韧性结构
                ("Fire", "Earth"): 2.5,     # 火土伤官
                ("Earth", "Metal"): 4.5,    # 土金伤官 - 韧性结构
            }

            collapse_threshold = ELEM_THRESHOLDS.get((dm_elem, sg_elem), 2.0)
            
            # ============================================================
            # [V1.0] 隐藏护盾量化 (Hidden Shield Quantification)
            # 藏干中有财星 → SAI 削减 85%
            # ============================================================
            hidden_wealth_shield = 0.0
            for p in points:
                if p["type"] == "hidden" and p["god"] in ["正财", "偏财"] and not p.get("is_main", True):
                    hidden_wealth_shield += p["energy"] * 0.85  # 中气/余气财星
            
            shield_multiplier = max(0.15, 1.0 - hidden_wealth_shield) if hidden_wealth_shield > 0 else 1.0

            # 5. PERTURBATION TEST: Global field strength
            total_guan_strength = sum(p["energy"] for p in points if p["god"] in ["正官", "七杀"])
            jump_rate = (total_guan_strength - natal_hidden_guan) / max(0.01, natal_hidden_guan) * 100
            
            # 6. STRESS CALCULATION with shield
            base_stress = (0.1 + (total_guan_strength * 0.5)) * geo_factor * shield_multiplier
            
            # 7. CATEGORY DETERMINATION
            if is_coherent:
                category = "共振过载 (Resonant Overload)"
                stress = base_stress * 0.5  # 共振态压力减半
            elif jump_rate > 500:
                category = "真空断裂 (Vacuum Rupture)"
                stress = (collapse_threshold + (jump_rate / 10000)) * geo_factor * shield_multiplier
            elif total_guan_strength > 0.5:
                category = "场强扰动 (Perturbed)"
                stress = base_stress
            else:
                category = "真空超导 (Superconductor)"
                stress = base_stress
            
            geo_status = "BOOST" if geo_factor > 1.0 else ("DAMPED" if geo_factor < 1.0 else "NEUTRAL")

            return {
                "chart": chart,
                "category": category,
                "purity": f"{purity:.2f}",
                "stress": f"{stress:.2f}",
                "jump_rate": f"{jump_rate:.1f}%",
                "r_ratio": f"{purity:.2f}",
                "dist": 0,
                "protection": f"Guan:{natal_hidden_guan:.1f}",
                "geo_status": geo_status,
                "geo_element": geo_element,
                "label": " ".join([f"{p[0]}{p[1]}" for p in chart]),
                "audit_mode": "SGSJ_V1.0_PHASE4",
                "voltage_pump": "ACTIVE" if any(p["energy"] > 2.0 and p["god"] in ["正官", "七杀"] for p in points) else "INACTIVE",
                "pgb_advice": "建议注入'财星介质'（如：戊己土/壬癸水）建立超导泄压通道。",
                # V1.0 Phase 4 新增参数
                "dm_elem": dm_elem,
                "sg_elem": sg_elem,
                "collapse_threshold": f"{collapse_threshold:.2f}",
                "hidden_wealth_shield": f"{hidden_wealth_shield:.2f}",
                "shield_multiplier": f"{shield_multiplier:.2f}",
                "resonance_state": resonance_state,
                "external_guan_elem": external_guan_elem or "N/A"
            }


        # --- PGB Tracks (Refined) ---
        if pattern_id == "PGB_SUPER_FLUID_LOCK":
            if any(BaziParticleNexus.get_shi_shen(s, dm) in ["正官", "七杀"] for s in stems): return None
            elem_set = set([BaziParticleNexus.STEMS[s][0] for s in stems])
            if len(elem_set) > 2: return None
            return {"chart": chart, "category": "超流无阻 (Superfluid)", "label": " ".join([f"{p[0]}{p[1]}" for p in chart]), "stress": "0.10"}

        if pattern_id == "PGB_BRITTLE_TITAN":
            # [V14.1.2] Brittle Titan Auditor (Optimized & Recursive-free)
            # 1. Broad Filter (Surface ZG + SG in Stems or Month Branch)
            if "正官" not in ten_gods: return None
            
            m_hidden = BaziParticleNexus.get_branch_weights(month_branch)
            has_sg_month = any(BaziParticleNexus.get_shi_shen(h[0], dm) == "伤官" for h in m_hidden)
            sg_exists = "伤官" in ten_gods or has_sg_month
            if not sg_exists: return None

            # 2. Purity Profile
            unique_elems = set([BaziParticleNexus.STEMS[s][0] for s in stems] + 
                              [BaziParticleNexus.BRANCHES[b][0] for b in branches])
            
            # 3. Structural Fragility (Clash check)
            has_clash = False
            for b in branches:
                if AN.CLASH_MAP.get(b) in branches:
                    has_clash = True
                    break
            
            # 4. Energy Profile (Reuse SGJG calculation logic)
            season_mult = PC.SEASONAL_MATRIX.get(month_branch, {})
            zg_indices = [i for i, tg in enumerate(ten_gods) if tg == "正官"]
            p_labels = ['year', 'month', 'day', 'hour', 'luck', 'annual']
            zg_e = max([PC.BASE_SCORE * PC.PILLAR_WEIGHTS.get(p_labels[idx] if idx < len(p_labels) else 'hour', 1.0) * season_mult.get(BaziParticleNexus.STEMS[stems[idx]][0], 1.0) for idx in zg_indices])
            
            # Criteria: High Purity + Structural Flaw (Clash) or High Stress
            if len(unique_elems) <= 4 and (has_clash or zg_e > 10.0):
                return {
                    "chart": chart,
                    "category": "脆性巨人 (Brittle Titan)",
                    "stress": "15.00", # Fixed high stress for labeling
                    "label": " ".join([f"{p[0]}{p[1]}" for p in chart])
                }
            return None

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
