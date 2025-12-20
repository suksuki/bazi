import sys
import os
import math

# 添加项目根目录到 sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.engine_graph.wave_physics import WavePhysicsEngine
from core.math import ProbValue
from core.engine_graph.quantum_entanglement import QuantumEntanglementProcessor
from core.engine_graph.phase2_adjacency import AdjacencyMatrixBuilder
from core.engine_graph import GraphNetworkEngine
from core.models.config_model import ConfigModel

def test_wave_interference():
    """测试 Task 1: 合局非线性干涉"""
    print("\n[Case 1] Wave Interference (Harmony)")
    print("-" * 40)
    
    # Scene A: 强强联手 (Constructive)
    e1_strong = 10.0
    e2_strong = 10.0
    # Phase = 0 (Constructive)
    params_const = {"test_phase": 0.0, "test_entropy": 1.0}
    net_strong = WavePhysicsEngine.compute_interference(e1_strong, e2_strong, "test", params_const)
    print(f"Strong + Strong (10+10, Phase=0): {net_strong:.2f} (Expected > 30 = 10+10+20)")
    
    # Scene B: 强弱悬殊 (Weak Link)
    e1_dom = 19.0
    e2_weak = 1.0
    net_weak = WavePhysicsEngine.compute_interference(e1_dom, e2_weak, "test", params_const)
    print(f"Strong + Weak (19+1, Phase=0):   {net_weak:.2f} (Expected ≈ 28 = 19+1+8.7)")
    
    # Scene C: 破坏性干涉 (Destructive)
    params_dest = {"test_phase": math.pi, "test_entropy": 1.0}
    net_clash = WavePhysicsEngine.compute_interference(e1_strong, e2_strong, "test", params_dest)
    print(f"Strong + Strong (10+10, Phase=180): {net_clash:.2f} (Expected 0)")
    
    if net_strong > 38.0 and net_clash < 1.0:
        print("✅ Wave Interference Logic Logic Check: PASS")
    else:
        print("❌ Wave Logic Check: FAIL")

class MockNode:
    def __init__(self, energy, pillar_idx, node_type='stem', element='wood', is_exposed=False):
        self.initial_energy = ProbValue(energy, 0.1)
        self.pillar_idx = pillar_idx
        self.node_type = node_type
        self.element = element
        self.char = '甲'
        self.is_exposed = is_exposed
        self.is_locked = False

def test_field_coupling():
    """测试 Task 2: 生克场势耦合"""
    print("\n[Case 2] Field Coupling (Interaction)")
    print("-" * 40)
    
    # Mock Engine (Minimal)
    class MockEngine:
        def __init__(self):
             self.config = {
                 'flow': {'controlImpact': 0.5},
                 'interactions': {}
             }
             self.nodes = [] # Mock attribute
             self.bazi = []
             self.BRANCH_ELEMENTS = {}

    mock_engine = MockEngine()
    builder = AdjacencyMatrixBuilder(mock_engine) 
    
    # Helper wrapper to access private method
    def calc(src_energy, dist):
        node_src = MockNode(src_energy, 0, 'stem', 'water')
        node_tgt = MockNode(5.0, dist, 'stem', 'wood')
        return builder._calculate_field_coupling(node_src, node_tgt, 'generate', {}, distance=dist)

    # Scene A: 强源 (E=10)
    w_strong_near = calc(10.0, 1) # Distance 1
    w_strong_far = calc(10.0, 3)  # Distance 3
    
    # Scene B: 弱源 (E=1.0) - Logically below threshold (1.5 center)
    w_weak_near = calc(1.0, 1)
    
    print(f"Strong Source (10.0) @ Dist 1: Weight = {w_strong_near:.4f} (Expect ~ 0.8 * 1.0 * 0.82 ≈ 0.65)")
    print(f"Strong Source (10.0) @ Dist 3: Weight = {w_strong_far:.4f}  (Expect ~ 0.8 * 1.0 * 0.55 ≈ 0.44)")
    print(f"Weak Source   (1.0)  @ Dist 1: Weight = {w_weak_near:.4f}   (Expect ~ 0.8 * 0.2 * 0.82 ≈ 0.13)")
    
    success = True
    if not (w_strong_near > w_strong_far):
        print("❌ Distance Decay Fail")
        success = False
    if not (w_strong_near > w_weak_near * 3.0):
        print("❌ Source Strength Fail (Sigmoid not working)")
        success = False
        
    if success:
        print("✅ Field Coupling Logic Check: PASS")

if __name__ == "__main__":
    test_wave_interference()
    test_field_coupling()
