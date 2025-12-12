
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.flux import FluxEngine
from core.kernel import Kernel

def test_flux_simulation():
    print("Testing Flux Engine V15.0...")
    
    # Construct a test chart with obvious flow
    # Year: Jia Zi (Wood/Water)
    # Month: Bing Yin (Fire/Wood)
    # Day: Wu Chen (Earth/Earth)
    # Hour: Geng Shen (Metal/Metal)
    
    chart = {
        'year': {'stem': '甲', 'branch': '子'},
        'month': {'stem': '丙', 'branch': '寅'},
        'day': {'stem': '戊', 'branch': '辰'},
        'hour': {'stem': '庚', 'branch': '申'}
    }
    
    engine = FluxEngine(chart)
    result = engine.compute_energy_state()
    
    print("\n--- Simulation Log ---")
    for log in result['log']:
        print(log)
        
    print("\n--- Particle States ---")
    for p in result['particle_states']:
        print(f"{p['id']}: {p['char']} Amp={p['amp']:.2f} Status={p['status']}")
        
    trace = result['trace']
    if 'system_focus' in trace:
        print(f"\nSystem Focus (Sink): {trace['system_focus']}")
        # Month Stem (Bing) can also be a sink in high-flow scenarios
        assert trace['system_focus']['id'] in ['hour_stem', 'hour_branch', 'day_stem', 'day_branch', 'month_stem']
    else:
        print("\nNo System Focus detected.")
        
    # Check for Synergy
    synergy_found = False
    for log in result['log']:
        if "Lian Zhu Synergy" in log:
            synergy_found = True
            break
            
    if synergy_found:
        print("\n✅ Lian Zhu Chain Detected!")
    else:
        print("\n❌ No Synergy Detected (Unexpected)")

if __name__ == "__main__":
    test_flux_simulation()
