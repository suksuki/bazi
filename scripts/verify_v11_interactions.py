import sys
import os
import numpy as np

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.engine_graph import GraphNetworkEngine
from core.math.distributions import ProbValue

def get_mean(val):
    if hasattr(val, 'mean'):
        if callable(val.mean):
            return float(val.mean())
        return float(val.mean)
    return float(val)

def test_interactions():
    # Case A: Metal-Wood Punishment (Yin-Si-Shen)
    print("\n--- CASE A: Yin-Si-Shen Punishment ---")
    engine_a = GraphNetworkEngine()
    bazi_a = ["甲寅", "己巳", "壬申", "庚子"]
    engine_a.initialize_nodes(bazi_a, day_master="壬")
    
    pre_yin = get_mean(next(n.initial_energy for n in engine_a.nodes if n.char == '寅'))
    engine_a._apply_quantum_entanglement_once()
    post_yin = get_mean(next(n.initial_energy for n in engine_a.nodes if n.char == '寅'))
    
    # Check for both Clash (0.4) and Punishment (0.3).
    # Expected approx: pre * 0.4 * 0.3 = pre * 0.12
    # But current logic applies them sequentially?
    # Actually _apply_energy_modifier multiplies H0.
    ratio_a = post_yin / pre_yin
    print(f"Yin Ratio: {ratio_a:.3f} (Expected ~0.12 if combined, or 0.3 or 0.4)")
    success_a = ratio_a < 0.5
    
    # Case B: Earth Punishment (Chou-Wei-Xu)
    print("\n--- CASE B: Chou-Wei-Xu Punishment ---")
    engine_b = GraphNetworkEngine()
    bazi_b = ["乙丑", "癸未", "甲戌", "壬申"]
    engine_b.initialize_nodes(bazi_b, day_master="甲")
    
    pre_xu = get_mean(next(n.initial_energy for n in engine_b.nodes if n.char == '戌'))
    engine_b._apply_quantum_entanglement_once()
    post_xu = get_mean(next(n.initial_energy for n in engine_b.nodes if n.char == '戌'))
    
    # Xu is not in clash, so should be exactly 1.5x (V12.0 tuned Q)
    ratio_b = post_xu / pre_xu
    print(f"Xu (Pure Punishment) Ratio: {ratio_b:.3f} (Expected 1.500)")
    success_b = abs(ratio_b - 1.5) < 0.01

    # Case C: Stem Combo Threshold
    print("\n--- CASE C: Stem Combo Threshold (Exceed 3.0) ---")
    engine_c = GraphNetworkEngine()
    bazi_c = ["甲申", "己卯", "壬申", "庚子"]
    engine_c.initialize_nodes(bazi_c, day_master="壬")
    
    # Force high energy for testing
    for node in engine_c.nodes:
        if node.char in ['甲', '己']:
            node.initial_energy = ProbValue(5.0)
            engine_c.H0[node.node_id] = node.initial_energy

    engine_c._apply_quantum_entanglement_once()
    debug_c = getattr(engine_c, '_quantum_entanglement_debug', {})
    
    combo_found = any("StemFiveCombine" in str(c) for c in debug_c.get('node_changes', []))
    print("Stem Combo detected:", combo_found)
    success_c = combo_found
    
    if success_a and success_b and success_c:
        print("\n✅ V11.1 INTERACTION TUNING FULLY SUCCESSFUL")
    else:
        print("\n❌ V11.1 INTERACTION TUNING FAILED")
        print(f"   - Case A: {success_a}")
        print(f"   - Case B: {success_b}")
        print(f"   - Case C: {success_c}")

if __name__ == "__main__":
    test_interactions()
