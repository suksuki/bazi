
import json
import os
import logging
import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime
from core.trinity.core.unified_arbitrator_master import QuantumUniversalFramework
from core.trinity.core.nexus.definitions import BaziParticleNexus

class CelebrityBacktester:
    """
    🌟 CelebrityBacktester (ASE Phase 4)
    
    Loads verified celebrity profiles and performs historical backtesting
    to minimize the 'Reality Gap' between life events and physics spikes.
    """
    
    def __init__(self, framework: QuantumUniversalFramework):
        self.framework = framework
        self.logger = logging.getLogger("CelebrityBacktester")

    def load_cases(self, file_path: str) -> List[Dict[str, Any]]:
        """Loads celebrity cases from JSON."""
        if not os.path.exists(file_path):
            self.logger.error(f"File not found: {file_path}")
            return []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to load cases: {e}")
            return []

    def run_backtest(self, case: Dict[str, Any], start_year: int, horizon: int = 60) -> Dict[str, Any]:
        """
        Runs a longitudinal physics scan for a celebrity across their lifespan.
        """
        pillars = case["bazi"]
        events = case.get("life_events", [])
        
        # Determine birth year if possible, or use provided start_year
        # Jia-Zi Cycle Helper
        stems = "甲乙丙丁戊己庚辛壬癸"
        branches = "子丑寅卯辰巳午未申酉戌亥"
        all_60 = [stems[i % 10] + branches[i % 12] for i in range(60)]
        
        timeline_data = []
        alignment_score = 0.0
        matched_events = 0

        for offset in range(horizon):
            current_year = start_year + offset
            annual_p = all_60[(current_year - 1924) % 60] # Reference 1924 (Jia-Zi)
            
            # Context injection
            ctx = {
                "luck_pillar": "甲子", # Mock luck for now
                "annual_pillar": annual_p,
                "damping_override": 0.30,
                "tier_override": case.get("tier", "Normal"), # [SUPREME] Support energy tiers
                "scenario": "BACKTEST"
            }
            
            # Geo override from case
            geo_ctx = case.get("geo_context", {})
            if "fire_bias" in geo_ctx:
                ctx["geo_bias"] = {"Fire": geo_ctx["fire_bias"]}

            report = self.framework.arbitrate_bazi(pillars, current_context=ctx)
            phy = report.get("physics", {})
            
            metrics = {
                "year": current_year,
                "sai": phy.get("stress", {}).get("SAI", 0),
                "reynolds": phy.get("wealth", {}).get("Reynolds", 0),
                "ic": phy.get("stress", {}).get("IC", 0)
            }
            timeline_data.append(metrics)
            
            # Check for alignment with historical events
            for ev in events:
                if ev["year"] == current_year:
                    # Target metric based on event type
                    target_val = metrics["sai"] if ev["type"] == "stress" else metrics["reynolds"]
                    expected_intensity = ev.get("intensity", 1.0)
                    
                    # [ResidualRadar] Dynamic thresholding based on case energy
                    sai_threshold = 4.0 if case.get("tier") == "Mars" else 2.0
                    wealth_threshold = 50.0 if case.get("tier") == "Mars" else 10.0
                    
                    if ev["type"] == "stress" and target_val >= sai_threshold:
                        alignment_score += 1.0
                        matched_events += 1
                    elif ev["type"] == "wealth" and target_val >= wealth_threshold:
                        alignment_score += 1.0
                        matched_events += 1

        total_events = len(events)
        final_fidelity = (matched_events / total_events) * 100 if total_events > 0 else 0.0
        
        return {
            "case_id": case["case_id"],
            "name": case["name"],
            "fidelity": final_fidelity,
            "timeline": timeline_data,
            "events_alignment": matched_events,
            "total_events": total_events
        }

    def aggregate_audit(self, file_path: str) -> Dict[str, Any]:
        """Runs backtest for all cases and returns global metrics."""
        cases = self.load_cases(file_path)
        results = []
        for c in cases:
            # Use provided birth_year for accurate annual pillar alignment
            b_year = c.get("birth_year", 1960)
            res = self.run_backtest(c, start_year=b_year, horizon=75)
            results.append(res)
            
        avg_fidelity = sum(r["fidelity"] for r in results) / len(results) if results else 0
        
        return {
            "avg_fidelity": avg_fidelity,
            "case_count": len(results),
            "individual_results": results,
            "status": "Celebrity Audit Complete"
        }
