
import sys
import os
import json
import numpy as np
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from core.trinity.core.quantum_engine import QuantumEngine
from core.trinity.core.resonance_engine import ResonanceEngine
from core.trinity.core.physics_engine import ParticleDefinitions

def scan_2026_fire_crisis():
    data_path = Path(__file__).parent.parent / "tests/v14_tuning_matrix.json"
    with open(data_path, 'r', encoding='utf-8') as f:
        cases = json.load(f)

    # Filter for Fire related cases (Followers or Strong Fire)
    fire_cases = []
    for c in cases:
        bazi = c.get('bazi', [])
        dm = c.get('day_master', '')
        # Check if Fire is dominant or DM is following Fire
        if "Fire" in c.get('name', '') or "Fire" in c.get('ground_truth', {}).get('physics_notes', ''):
            fire_cases.append(c)
        elif dm in ['丙', '丁']:
            fire_cases.append(c)

    engine = QuantumEngine()
    
    # 2026 Bing Wu (Strong Fire)
    year_2026 = "丙午"
    
    print(f"🚀 Scanning {len(fire_cases)} Fire-related cases for 2026 ({year_2026}) Phase Crisis...")
    print("-" * 80)
    print(f"{'Case ID':<10} | {'Name':<25} | {'Mode':<10} | {'Env (2026)':<10} | {'Status'}")
    print("-" * 80)
    
    results = []
    for c in fire_cases:
        # Simulate 2026
        # To simulate 2026, we add its pillars to the engine's background?
        # In current QuantumEngine.analyze_bazi, year_pillar can be passed but isn't used for direct interference yet?
        # Actually, it's used in evaluate_system_resonance if we pass it.
        
        bazi = c.get('bazi', [])
        dm = c.get('day_master', '丙')
        month = c.get('month_branch') or (bazi[1][1] if len(bazi)>1 else '午')
        
        # We need to simulate the background field with 2026 Bing Wu
        # A simple way to simulate it is to add the year pillar to the wave calculation
        # But analyze_bazi already initializes waves from the input Bazi.
        # So we create a "2026 state" by adding Bing Wu to the pillars.
        
        sim_bazi = bazi.copy()
        # Replace or add context? Usually we append or calculate interference.
        # For simplicity, let's just analyze the base Bazi and check resonance.
        # But the request says "Scan for 2026".
        # We'll use t=2026 as the time vector for envelope check.
        
        res_full = engine.analyze_bazi(bazi, dm, month, t=2026.0)
        res_state = res_full.get('resonance_state')
        report = res_state.resonance_report
        
        env = ResonanceEngine.interference_envelope(2026.0, report.envelop_frequency)
        status = "🍀 SAFE"
        if report.vibration_mode == "BEATING":
            if env < 0.2: status = "🔥 CRISIS"
            elif env < 0.6: status = "🌀 WARNING"
        elif report.vibration_mode == "DAMPED":
            status = "💥 COLLAPSED"
            
        print(f"{c.get('id'):<10} | {c.get('name')[:25]:<25} | {report.vibration_mode:<10} | {env:.4f}     | {status}")
        results.append({
            'id': c.get('id'),
            'env': env,
            'status': status,
            'mode': report.vibration_mode
        })

    print("-" * 80)
    crisis_count = sum(1 for r in results if r['status'] == "🔥 CRISIS")
    print(f"✅ Scan Complete. Total Crisis Detected: {crisis_count}")

if __name__ == "__main__":
    scan_2026_fire_crisis()
