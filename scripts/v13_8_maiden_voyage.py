
import os
import sys
import json
import logging
import pandas as pd
import numpy as np
from datetime import datetime

# Add project root to path
sys.path.append(os.getcwd())

from core.trinity.core.unified_arbitrator_master import QuantumUniversalFramework
from core.trinity.core.engines.simulation_controller import SimulationController
from core.trinity.core.nexus.definitions import BaziParticleNexus

def main():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("V13.8_Maiden_Voyage")
    
    logger.info("🚢 Starting V13.8 Gold Edition Maiden Voyage (首航仪式)...")
    
    framework = QuantumUniversalFramework()
    controller = SimulationController(os.getcwd())
    
    # --- TASK 1: Full Case Retrospective (REAL_01 to REAL_05) ---
    real_cases = [
        {"id": "REAL_01", "name": "癸水强根 (The Anchor)", "pillars": ["癸卯", "甲寅", "癸亥", "壬子"], "geo": "北京 (Beijing)"},
        {"id": "REAL_02", "name": "李小龙 (The Dragon)", "pillars": ["庚辰", "丁亥", "甲戌", "戊辰"], "geo": "旧金山 (San Francisco)"},
        {"id": "REAL_03", "name": "巴菲特 (The Oracle)", "pillars": ["庚午", "甲申", "壬子", "戊申"], "geo": "纽约 (New York)"},
        {"id": "REAL_04", "name": "真从财格 (The Superconductor)", "pillars": ["癸卯", "甲寅", "辛卯", "乙未"], "geo": "上海 (Shanghai)"},
        {"id": "REAL_05", "name": "极弱坍缩 (The Void)", "pillars": ["乙未", "戊寅", "壬午", "辛亥"], "geo": "拉萨 (Lhasa)"},
    ]
    
    audit_results = []
    
    for case in real_cases:
        logger.info(f"🔮 Arbitrating {case['id']}: {case['name']}...")
        
        # 1. Base Arbitration
        from ui.pages.quantum_lab import GEO_CITY_MAP
        geo_pref = GEO_CITY_MAP.get(case["geo"], (1.0, "Neutral"))
        
        ctx = {
            "luck_pillar": "甲子",
            "annual_pillar": "甲子",
            "damping_override": 0.30, # Calibrated Gamma
            "scenario": "MAIDEN_VOYAGE",
            "geo_bias": {geo_pref[1].split('/')[0]: geo_pref[0]} # Simplified geo mapping
        }
        
        report = framework.arbitrate_bazi(case["pillars"], current_context=ctx)
        phy = report.get("physics", {})
        
        # 2. Time-Scan (30 Years Stress Map)
        # We use Year 11 (2011 index) for REAL_01 to check alignment
        mirror_audit = controller.run_mirror_audit(case["pillars"])
        
        audit_results.append({
            "case": case,
            "metrics": {
                "SAI": phy.get("stress", {}).get("SAI", 0),
                "Reynolds": phy.get("wealth", {}).get("Reynolds", 0),
                "Stability": phy.get("relationship", {}).get("Orbital_Stability", 0)
            },
            "mirror_stats": {
                "count": mirror_audit["mirror_count"],
                "reality_gap": mirror_audit.get("reality_gap", 0),
                "target_aligned": mirror_audit.get("target_aligned", False)
            },
            "scan_data": mirror_audit["scan_data"]
        })

    # --- TASK 2: Blind Test (10 Synthetic Cases) ---
    logger.info("🧪 Running Blind Test (10 Synthetic Cases)...")
    blind_res = controller.run_phase_2_audit(sample_size=10, progress_callback=None)
    
    # --- TASK 3: Final Report Generation ---
    class NpEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, np.integer): return int(obj)
            if isinstance(obj, np.floating): return float(obj)
            if isinstance(obj, np.bool_): return bool(obj)
            return super(NpEncoder, self).default(obj)

    final_report = {
        "version": "V13.8 Gold Edition",
        "calibration": {
            "gamma": 0.30,
            "protection_weight": 0.75,
            "momentum_boost": 2.5
        },
        "real_cases_audit": audit_results,
        "blind_test": blind_res,
        "timestamp": datetime.now().isoformat()
    }
    
    report_path = os.path.join(os.getcwd(), "reports", "v13_8_maiden_voyage_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(final_report, f, indent=2, ensure_ascii=False, cls=NpEncoder)
        
    logger.info(f"🏁 Maiden Voyage Complete! Report saved to {report_path}")
    print(f"\n[SUMMARY] REAL_01_RESONANCE_ALIGN={audit_results[0]['mirror_stats']['target_aligned']}")
    print(f"[SUMMARY] BLIND_TEST_SINGULARITIES={blind_res['counts'].get('SUPERCONDUCTIVE', 0) + blind_res['counts'].get('COLLAPSE', 0)}")

if __name__ == "__main__":
    main()
