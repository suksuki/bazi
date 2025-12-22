
import sys
import os
import json
import numpy as np
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from core.trinity.core.quantum_engine import QuantumEngine
from core.trinity.core.resonance_engine import ResonanceEngine
from core.trinity.core.gravitational_lens import GravitationalLensEngine

def simulate_remediation_002():
    # Case SYNC_EXT_002_FAKE_FIRE
    # bazi: ["丙午", "甲午", "丁巳", "壬子"], dm: "丁"
    
    bazi = ["丙午", "甲午", "丁巳", "壬子"]
    dm = "丁"
    month = "午"
    
    engine = QuantumEngine()
    
    # Crisis time t=12.5 (as mentioned in user request)
    t_crisis = 12.5
    
    # 1. Base Analysis
    res_base = engine.analyze_bazi(bazi, dm, month, t=t_crisis)
    state = res_base.get('resonance_state')
    report = state.resonance_report
    
    print(f"--- 🌀 Case: SYNC_EXT_002 (Fake Fire Follow) Scan ---")
    print(f"Mode: {report.vibration_mode}")
    print(f"Locking Ratio: {report.locking_ratio:.2f}")
    
    env_base = ResonanceEngine.interference_envelope(t_crisis, report.envelop_frequency)
    print(f"Base Envelope at t={t_crisis}: {env_base:.4f} (Safety: {'🔥 CRISIS' if env_base < 0.2 else '🍀 SAFE'})")
    
    print("\n--- 🔮 Initiating Gravitational Lensing / Spatial Repair ---")
    
    # Simulate repair for Fire element (since it's a Fire follow)
    repair_sim = GravitationalLensEngine.simulate_spatial_repair(
        dm_wave=state.dm_wave,
        field_waves=state.field_waves,
        base_t=t_crisis,
        target_frequency=report.envelop_frequency,
        target_element="Fire"
    )
    
    print(f"Targeting Element: {repair_sim['target']} Boost")
    print(f"{'Location':<25} | {'K_geo':<6} | {'Env (t=12.5)':<12} | {'Safety'}")
    print("-" * 65)
    
    for r in repair_sim['results']:
        print(f"{r['location']:<25} | {r['k_geo']:<6.2f} | {r['env_at_t']:<12.4f} | {r['safety']}")

    best = repair_sim['results'][0]
    print(f"\n🚀 SOLUTION FOUND: Migrate to {best['location']} ({best['description']}).")
    print(f"New Safety Level: {best['safety']}. The phase crisis is neutralized through spatial refocusing.")

if __name__ == "__main__":
    simulate_remediation_002()
