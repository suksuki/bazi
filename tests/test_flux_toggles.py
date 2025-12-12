
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.flux import FluxEngine

def test_flux_toggles():
    print("Testing Quantum Switchboard Logic (Flux Toggles)...")
    
    # Chart: Shen-Zi-Chen (Monkey-Rat-Dragon) Water Frame
    # Year: Geng Shen (Metal Monkey)
    # Month: Jia Zi (Wood Rat)
    # Day: Ren Chen (Water Dragon)
    
    chart = {
        'year': {'branch': '申', 'stem': '庚'},
        'month': {'branch': '子', 'stem': '甲'},
        'day': {'branch': '辰', 'stem': '壬'}
    }
    
    # 1. First Run: Full Interactions
    print("\n--- Phase 1: Full Simulation ---")
    engine1 = FluxEngine(chart)
    result1 = engine1.calculate_flux()
    
    rules = result1['detected_rules']
    print(f"Detected Rules: {rules}")
    
    # Check if SanHe detected
    sanhe_rule = next((r for r in rules if "SanHe" in r), None)
    if not sanhe_rule:
        print("❌ SanHe NOT detected")
        return
        
    print(f"✅ SanHe Detected: {sanhe_rule}")
    
    # Check Energy of Water (should be boosted by SanHe)
    shen_p = next(p for p in result1['particle_states'] if p['char'] == '申')
    print(f"Shen (Monkey) Amp (With SanHe): {shen_p['amp']:.1f}")
    
    # 2. Second Run: Disable SanHe
    print(f"\n--- Phase 2: Disabling {sanhe_rule} ---")
    engine2 = FluxEngine(chart)
    result2 = engine2.calculate_flux(disabled_rules={sanhe_rule})
    
    # Check Energy of Water (should be lower)
    shen_p2 = next(p for p in result2['particle_states'] if p['char'] == '申')
    print(f"Shen (Monkey) Amp (Without SanHe): {shen_p2['amp']:.1f}")
    
    if shen_p2['amp'] < shen_p['amp']:
        print("✅ Energy Reduced as Expected (Delta Confirmed)")
        delta = shen_p['amp'] - shen_p2['amp']
        print(f"Delta: -{delta:.1f}")
    else:
        print("❌ Energy did not decrease. Toggle Failed.")

if __name__ == "__main__":
    test_flux_toggles()
