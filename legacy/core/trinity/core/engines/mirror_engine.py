
import logging
import numpy as np
from typing import List, Dict, Any, Tuple
from core.trinity.core.nexus.definitions import BaziParticleNexus
from core.trinity.core.engines.synthetic_bazi_engine import SyntheticBaziEngine
from core.trinity.core.unified_arbitrator_master import QuantumUniversalFramework

class MirrorEngine:
    """
    🪞 MirrorEngine (ASE Phase 3)
    
    Finds 'Physical Twins' in the 518,400 Bazi matrix and performs cross-fidelity audits.
    """
    
    def __init__(self, framework: QuantumUniversalFramework):
        self.framework = framework
        self.bazi_engine = SyntheticBaziEngine()
        self.logger = logging.getLogger("MirrorEngine")

    def find_mirrors(self, target_report: Dict[str, Any], limit: int = 1000) -> List[List[str]]:
        """
        Finds Bazi charts with >95% similarity to the target's physical profile.
        """
        target_chart = target_report.get("meta", {}).get("chart", [])
        if not target_chart: return []
        
        target_phy = target_report.get("physics", {})
        target_sai = target_phy.get("stress", {}).get("SAI", 0)
        target_ic = target_phy.get("stress", {}).get("IC", 0)
        target_dm = target_chart[2][0]
        target_dm_elem = BaziParticleNexus.STEMS.get(target_dm)[0]
        
        mirrors = []
        gen = self.bazi_engine.generate_all_bazi()
        
        # Phase 1: Structural Filter (DM and Season)
        # To speed up, we only check charts with same DM and same month branch element
        target_month_branch = target_chart[1][1]
        target_month_elem = BaziParticleNexus.BRANCHES.get(target_month_branch)[0]
        
        count = 0
        total_checked = 0
        self.logger.info(f"Searching for mirrors of {target_chart}...")
        
        for chart in gen:
            total_checked += 1
            # fast-path filter
            dm = chart[2][0]
            if dm != target_dm: continue
            
            m_br = chart[1][1]
            m_elem = BaziParticleNexus.BRANCHES.get(m_br)[0]
            if m_elem != target_month_elem: continue
            
            # Phase 2: Arbitrate and Compare Physics
            report = self.framework.arbitrate_bazi(chart)
            phy = report.get("physics", {})
            sai = phy.get("stress", {}).get("SAI", 0)
            ic = phy.get("stress", {}).get("IC", 0)
            
            # Similarity Calculation (Weighted Euclidean distance on SAI/IC)
            # 95% similarity = error < 5%
            dist = np.sqrt(((sai - target_sai)/max(1,target_sai))**2 + ((ic - target_ic)/max(1,target_ic))**2)
            if dist < 0.05:
                mirrors.append(chart)
                count += 1
                if count >= limit: break
            
            if total_checked > 50000: # Safety break to prevent infinite search if rare
                break
                
        self.logger.info(f"Found {len(mirrors)} mirrors after checking {total_checked} cases.")
        return mirrors

    def run_mirror_time_scan(self, mirrors: List[List[str]], years: int = 30, reality_target_year: int = 11, reality_target_sai: float = 3.228) -> Dict[str, Any]:
        """
        Runs a time-scan for all mirrors and aggregates the results.
        Finds 'Resonance Singularities' where majority of mirrors spike.
        
        Args:
            reality_target_year: index of year to align (e.g. 11 for 2011 if scan starts at 2000)
            reality_target_sai: the SAI value recorded in REAL_01 history.
        """
        aggregated_sai = {}
        stems = "甲乙丙丁戊己庚辛壬癸"
        branches = "子丑寅卯辰巳午未申酉戌亥"
        all_60 = [stems[i % 10] + branches[i % 12] for i in range(60)]
        
        for i, chart in enumerate(mirrors):
            for year_offset in range(years):
                annual_p = all_60[year_offset % 60]
                ctx = {
                    "luck_pillar": "甲子",
                    "annual_pillar": annual_p,
                    "damping_override": 0.30
                }
                report = self.framework.arbitrate_bazi(chart, current_context=ctx)
                sai = report.get("physics", {}).get("stress", {}).get("SAI", 0)
                
                if year_offset not in aggregated_sai:
                    aggregated_sai[year_offset] = []
                aggregated_sai[year_offset].append(sai)
        
        resonance_points = []
        for year, vals in aggregated_sai.items():
            avg_sai = np.mean(vals)
            spike_count = sum(1 for v in vals if v > 2.0)
            resonance_points.append({
                "year_offset": year,
                "avg_sai": float(avg_sai),
                "spike_ratio": float(spike_count / len(mirrors)) if mirrors else 0
            })
            
        # Calculate Reality Gap
        mirror_avg_at_target = 0.0
        if reality_target_year in aggregated_sai:
            mirror_avg_at_target = np.mean(aggregated_sai[reality_target_year])
        
        reality_gap = abs(mirror_avg_at_target - reality_target_sai) / reality_target_sai
        
        return {
            "resonance_points": resonance_points,
            "mirror_count": len(mirrors),
            "reality_gap": float(reality_gap),
            "target_aligned": reality_gap < 0.05,
            "tuning_recommendation": "STABLE" if reality_gap < 0.05 else "ADJUST_MOD_16_THRESHOLD"
        }
