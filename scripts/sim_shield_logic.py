
import sys
import os
import json
import logging

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.trinity.core.oracle import TrinityOracle
from core.profile_manager import ProfileManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_simulation():
    """
    Simulation for [PH30-SHIELD] Logic.
    Loads 'INTEGRATED_EXTREME_001' and checks if the system prescribes 'Bi-Jie' shielding.
    """
    oracle = TrinityOracle()
    
    # Load case
    case_path = os.path.join(os.path.dirname(__file__), '..', 'tests', 'data', 'integrated_extreme_cases.json')
    with open(case_path, 'r') as f:
        cases = json.load(f)
        
    target = next((c for c in cases if c['id'] == 'INTEGRATED_EXTREME_001'), None)
    if not target:
        print("❌ Case INTEGRATED_EXTREME_001 not found.")
        return

    print("\n🚀 [SIMULATION] Bi-Jie Shielding Logic Test")
    print("="*60)
    print(f"Subject: {target['bazi']}")
    print(f"Day Master: {target['day_master']} (Earth)")
    
    # Analyze
    res = oracle.analyze(target['bazi'], target['day_master'])
    
    unified = res['unified_metrics']
    remedy = res['remedy']
    
    print("\n📊 [DIAGNOSTICS]")
    if unified:
        print(f"   - Capture Efficiency: {unified.get('capture', {}).get('efficiency', 0):.2f}")
        print(f"   - Cutting Depth: {unified.get('cutting', {}).get('depth', 0):.2f} ({unified.get('cutting', {}).get('status')})")
        print(f"   - Contamination: {unified.get('contamination', {}).get('index', 0):.2f}")

    print("\n🔍 [WAVE STATES]")
    waves = res.get('waves', {})
    for elem, w in waves.items():
        print(f"   - {elem}: Amp={w.amplitude:.2f}, Phase={w.phase:.2f}")
    
    print("\n💊 [PRESCRIPTION]")
    if remedy:
        print(f"   - Best Particle: {remedy['best_particle']} ({remedy['optimal_element']})")
        print(f"   - Strategy: {remedy['description']}")
        
        # Validation
        # DM is Wu Earth (戊). Bi-Jie is Earth.
        # If Cutting is CRITICAL, we expect 'Earth' (戊/己) as remedy.
        if unified.get('cutting', {}).get('status') == 'CRITICAL':
             if remedy['optimal_element'] == 'Earth' and "Bi-Jie" in remedy['description']:
                 print("\n✅ PASS: Bi-Jie Shielding successfully activated.")
             else:
                 print("\n❌ FAIL: Shielding logic not triggered correctly.")
                 print(f"Expected Earth (Bi-Jie) with 'Bi-Jie' in description. Got {remedy['optimal_element']}")
        else:
             print("\n⚠️ SKIP: Cutting was not critical, shielding logic not tested.")
             
    print("="*60)

if __name__ == "__main__":
    run_simulation()
