#!/usr/bin/env python3
"""
Verification Test for Quantum Trinity (V1.0)
============================================
Tests the unified math, physics, registry, and tuning modules.
"""

import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.trinity import (
    ProbValue, expit, ParameterStore, PhysicsEngine, 
    RuleRegistry, UnifiedVerifier, TuningEngine, BayesianStrategy
)

def test_math_probvalue():
    """Verify ProbValue arithmetic and probabilities."""
    v1 = ProbValue(10.0, 0.1) # Mean 10, Std 1.0
    v2 = ProbValue(5.0, 0.1)  # Mean 5, Std 0.5
    
    # 10 > 5 should be highly probable
    prob = v1.prob_greater_than(v2)
    assert prob > 0.99
    
    # Addition: 10 + 5 = 15, std = sqrt(1^2 + 0.5^2) = 1.118
    v3 = v1 + v2
    assert v3.mean == 15.0
    assert abs(v3.std - 1.118) < 0.01

def test_parameter_store():
    """Verify hierarchical parameter access and flattening."""
    store = ParameterStore()
    
    # Check default access
    month_weight = store.get("physics.pillarWeights.month")
    assert month_weight == 1.42
    
    # Check set and get
    store.set("physics.test_param", 9.9)
    assert store.get("physics.test_param") == 9.9
    
    # Check flattening
    flat = store.flatten()
    assert "physics.pillarWeights.month" in flat
    assert flat["physics.pillarWeights.month"] == 1.42

def test_physics_engine():
    """Verify physical formula calculations."""
    damage = PhysicsEngine.calculate_control_damage(100.0, 50.0)
    # Attacker >> Defender, should be near max (50% of 50 = 25)
    assert damage == 25.0
    
    gen = PhysicsEngine.calculate_generation(20.0, 0.5, threshold=10.0)
    # (20 - 10) * 0.5 = 5.0
    assert gen == 5.0

def test_tuning_modular():
    """Verify the modular TuningEngine skeleton."""
    store = ParameterStore()
    # Mock engine factory
    class MockEngine:
        def __init__(self, config): pass
        def initialize_nodes(self, bazi, dm): pass
        def calculate_strength_score(self): return 65.0 # Always Strong
    
    verifier = UnifiedVerifier(engine_factory=MockEngine, params=store._params)
    engine = TuningEngine(store, verifier)
    
    cases = [
        {"bazi": ["甲子", "丙子", "壬戌", "辛亥"], "day_master": "壬", "strength_label": "Strong"}
    ]
    
    results = engine.validate_current(cases)
    assert results["accuracy"] == 100.0
    assert results["passed_count"] == 1

if __name__ == "__main__":
    print("🚀 Running Quantum Trinity V1.0 Verification...")
    try:
        test_math_probvalue()
        print("✅ Math Engine: PASSED")
        test_parameter_store()
        print("✅ Parameter Store: PASSED")
        test_physics_engine()
        print("✅ Physics Engine: PASSED")
        test_tuning_modular()
        print("✅ Tuning Engine: PASSED")
        print("\n🏆 ALL QUANTUM TRINITY CORE TESTS PASSED!")
    except Exception as e:
        print(f"\n❌ VERIFICATION FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
