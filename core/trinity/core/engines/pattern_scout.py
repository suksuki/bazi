
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
            # 1. HOLOGRAPHIC SCAN (Stems + Hidden Stems of 6 Pillars)
            p_labels = ['year', 'month', 'day', 'hour', 'luck', 'annual']
            season_mult = PC.SEASONAL_MATRIX.get(month_branch, {})
            
            # Map of all active power points in the field
            points = []
            stem_gods_set = set()
            
            # First pass: Collect stem gods (for Protrusion check)
            for s in stems:
                stem_gods_set.add(BaziParticleNexus.get_shi_shen(s, dm))

            # Second pass: Build power points
            for i, p_label in enumerate(p_labels):
                if i >= len(chart): continue # Safety for short charts
                s, b = chart[i]
                p_weight = PC.PILLAR_WEIGHTS.get(p_label, 1.0)
                
                # A: Stem Point
                tg_s = BaziParticleNexus.get_shi_shen(s, dm)
                s_elem = BaziParticleNexus.STEMS[s][0]
                s_energy = PC.BASE_SCORE * p_weight * season_mult.get(s_elem, 1.0)
                points.append({
                    "pos": i, "type": "stem", "god": tg_s, "energy": s_energy, "weight": 1.0
                })
                
                # B: Branch Hidden Points (Cross-Dimensional)
                hidden = BaziParticleNexus.get_branch_weights(b)
                for h_stem, h_w in hidden:
                    tg_h = BaziParticleNexus.get_shi_shen(h_stem, dm)
                    # [務實校研] 维度阻抗系数: 透干 1.1, 不透干 0.6
                    dim_coeff = 1.1 if tg_h in stem_gods_set else 0.6
                    h_elem = BaziParticleNexus.STEMS[h_stem][0]
                    h_energy = PC.BASE_SCORE * p_weight * season_mult.get(h_elem, 1.0) * (float(h_w) / 10.0) * dim_coeff
                    points.append({
                        "pos": i, "type": "hidden", "god": tg_h, "energy": h_energy, "weight": dim_coeff
                    })

            # 2. Collision Detection (Attacker vs Officer)
            # Pragmatic: Including Seven Killings (七杀) and Food (食神) as potential stress sources
            attackers = [p for p in points if p["god"] in ["伤官", "食神"]]
            officers = [p for p in points if p["god"] in ["正官", "七杀"]]
            
            if not attackers or not officers: return None
            
            # Find the "Core Collision Site" (Max energy pair)
            max_sg_e = max(p["energy"] for p in attackers)
            max_zg_e = max(p["energy"] for p in officers)
            r_ratio = max_sg_e / max_zg_e
            
            if r_ratio < 0.6: return None # Below stress threshold
            
            # Calculate Proximity (Distance between strongest sources)
            min_dist = 4
            for s_p in [p for p in attackers if p["energy"] > max_sg_e * 0.7]:
                for z_p in [p for p in officers if p["energy"] > max_zg_e * 0.7]:
                    dist = abs(s_p["pos"] - z_p["pos"])
                    min_dist = min(min_dist, dist)

            # 3. Spatial Bus Impedance (Protection Audit)
            protection_standard = 0.0
            protection_spatial = 0.0
            
            # Identify core collision positions to check if protection is 'In between'
            sg_core_pos = next(p["pos"] for p in attackers if p["energy"] == max_sg_e)
            zg_core_pos = next(p["pos"] for p in officers if p["energy"] == max_zg_e)
            collision_range = sorted([sg_core_pos, zg_core_pos])
            
            for p in points:
                p_val = 0.0
                if p["god"] in ["正财", "偏财"]: p_val = 0.8 * p["weight"]
                elif p["god"] in ["正印", "偏印"]: p_val = 0.5 * p["weight"]
                
                if p_val > 0:
                    protection_standard += p_val
                    # [務實校研] 距离损耗: 远水救不了近火
                    # If protection is not between collision sites and distance > 2, reduce drastically
                    is_between = (collision_range[0] <= p["pos"] <= collision_range[1])
                    dist_to_center = min(abs(p["pos"] - sg_core_pos), abs(p["pos"] - zg_core_pos))
                    
                    if not is_between and dist_to_center > 1.5:
                        protection_spatial += (p_val * 0.1) # Severe decay for remote guards
                    else:
                        protection_spatial += p_val # Effective buffer

            # 4. Final Verdict Logic
            is_standard_blocked = protection_standard > 0.8
            is_spatial_blocked = protection_spatial > 0.8
            
            if is_standard_blocked and is_spatial_blocked:
                return None # Truly protected by both models

            # Stress Calculation (Boosted by Proximity and Clashes)
            has_clash = any(AN.CLASH_MAP.get(chart[i][1]) == chart[j][1] for i in range(len(chart)) for j in range(i+1, len(chart)))
            stress_idx = r_ratio * (6 - min_dist) * (1.5 if has_clash else 1.0)
            
            category = "维度对撞 (Holographic)"
            if stress_idx > 12.0: category = "高压击穿 (Breakdown)"
            elif is_standard_blocked and not is_spatial_blocked: category = "防御虚化 (Ghost Guard)"

            # Check for 'Voltage Pump' (Protrusion factor 1.1)
            has_voltage_pump = any(p["weight"] == 1.1 for p in points)

            return {
                "chart": chart,
                "r_ratio": f"{r_ratio:.2f}",
                "dist": min_dist,
                "protection": f"Std:{protection_standard:.1f} / Spa:{protection_spatial:.1f}",
                "category": category,
                "stress": f"{stress_idx:.2f}",
                "label": " ".join([f"{p[0]}{p[1]}" for p in chart]),
                "audit_mode": "3D_INDUCTION_HOLOGRAPHIC",
                "standard_verdict": "SAFE" if is_standard_blocked else "CRITICAL",
                "spatial_verdict": "SAFE" if is_spatial_blocked else "CRITICAL",
                "voltage_pump": "ACTIVE" if has_voltage_pump else "INACTIVE",
                "bus_impedance": "SEVERE" if (protection_standard - protection_spatial) > 0.5 else "LOW"
            }

        if pattern_id == "SHANG_GUAN_SHANG_JIN":
            # [V14.8.4] STRICT SUPERCONDUCTOR AUDIT WITH GEO CORRECTION
            # Hard Rule 1: Must have Shang Guan (伤官) in stems
            if "伤官" not in ten_gods: return None
            
            # Hard Rule 2: Natal stems must NOT have any 正官/七杀
            if any(tg in ["正官", "七杀"] for tg in ten_gods[:4]): return None
            
            # 1. FULL SPECTRUM SCAN: Stems + Hidden Stems with GEO Correction
            p_labels = ['year', 'month', 'day', 'hour', 'luck', 'annual']
            season_mult = PC.SEASONAL_MATRIX.get(month_branch, {})
            points = []
            stem_gods_set = set(ten_gods)

            for i, p_label in enumerate(p_labels):
                if i >= len(chart): continue
                s, b = chart[i]
                p_weight = PC.PILLAR_WEIGHTS.get(p_label, 1.0)
                
                # A: STEM ENERGY (天干 - Full Weight 1.0 + GEO Correction)
                tg_s = BaziParticleNexus.get_shi_shen(s, dm)
                s_elem = BaziParticleNexus.STEMS[s][0]
                geo_corr = geo_mult.get(s_elem, 1.0)  # Apply GEO field
                s_energy = PC.BASE_SCORE * p_weight * season_mult.get(s_elem, 1.0) * geo_corr
                points.append({"pos": i, "type": "stem", "god": tg_s, "energy": s_energy, "elem": s_elem, "is_natal": i < 4})
                
                # B: HIDDEN STEM ENERGY (藏干 - Dim Coeff 0.6/1.1 + GEO Correction)
                hidden = BaziParticleNexus.get_branch_weights(b)
                for h_stem, h_w in hidden:
                    tg_h = BaziParticleNexus.get_shi_shen(h_stem, dm)
                    dim_coeff = 1.1 if tg_h in stem_gods_set else 0.6
                    h_elem = BaziParticleNexus.STEMS[h_stem][0]
                    geo_corr_h = geo_mult.get(h_elem, 1.0)  # Apply GEO field
                    h_energy = PC.BASE_SCORE * p_weight * season_mult.get(h_elem, 1.0) * (float(h_w) / 10.0) * dim_coeff * geo_corr_h
                    points.append({"pos": i, "type": "hidden", "god": tg_h, "energy": h_energy, "elem": h_elem, "is_natal": i < 4})

            # 2. PURITY AUDIT: Total Guan/Sha in NATAL Hidden Stems
            natal_hidden_guan = sum(p["energy"] for p in points if p["is_natal"] and p["type"] == "hidden" and p["god"] in ["正官", "七杀"])
            # Strict threshold: < 1.5 energy for true superconductor
            purity = max(0.0, 1.0 - (natal_hidden_guan / 3.0))
            if purity < 0.95: return None

            # 3. PERTURBATION TEST: Global field strength (Natal + External Bus)
            total_guan_strength = sum(p["energy"] for p in points if p["god"] in ["正官", "七杀"])
            
            # Jump Rate: % spike from external injection
            jump_rate = (total_guan_strength - natal_hidden_guan) / max(0.01, natal_hidden_guan) * 100
            
            # 4. GEO-ADJUSTED STRESS
            category = "真空超导 (Superconductor)"
            stress = (0.1 + (total_guan_strength * 0.5)) * geo_factor
            geo_status = "BOOST" if geo_factor > 1.0 else ("DAMPED" if geo_factor < 1.0 else "NEUTRAL")
            
            if jump_rate > 500:
                category = "真空断裂 (Vacuum Rupture)"
                stress = (1.25 + (jump_rate / 10000)) * geo_factor
            elif total_guan_strength > 0.5:
                category = "场强扰动 (Perturbed)"

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
                "audit_mode": "SGSJ_SUPERCONDUCTOR_TRACK",
                "voltage_pump": "ACTIVE" if any(p["energy"] > 2.0 and p["god"] in ["正官", "七杀"] for p in points) else "INACTIVE",
                "pgb_advice": "建议注入'财星介质'（如：戊己土/壬癸水）建立超导泄压通道，预防 1.25 断裂。"
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
