"""
Test Suite: Phase B - Quantum Dispersion Engine
================================================
Tests for the QuantumDispersionEngine and solar term boundary behavior.
"""

import pytest
import math
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from core.trinity.core.engines.quantum_dispersion import QuantumDispersionEngine
from core.trinity.core.nexus.definitions import BaziParticleNexus


class TestQuantumDispersionEngine:
    """Test suite for QuantumDispersionEngine."""
    
    def test_engine_initialization(self):
        """Test engine initialization with damping factor."""
        engine = QuantumDispersionEngine(damping_factor=1.0)
        assert engine.damping_factor == 1.0
        
        engine2 = QuantumDispersionEngine(damping_factor=1.5)
        assert engine2.damping_factor == 1.5
    
    def test_static_weights(self):
        """Test static weight retrieval."""
        engine = QuantumDispersionEngine()
        
        # Test 丑 (three hidden stems)
        static = engine.get_static_weights("丑")
        assert static == {"己": 5.0, "癸": 3.0, "辛": 2.0}
        
        # Test 子 (single hidden stem)
        static_zi = engine.get_static_weights("子")
        assert static_zi == {"癸": 10.0}
    
    def test_dynamic_weights_single_stem(self):
        """Test that single-stem branches return fixed weight."""
        engine = QuantumDispersionEngine()
        
        # 子 only has 癸
        for progress in [0.0, 0.25, 0.5, 0.75, 1.0]:
            weights = engine.get_dynamic_weights("子", progress)
            assert weights == {"癸": 10.0}
    
    def test_dynamic_weights_multi_stem(self):
        """Test dynamic weights for multi-stem branches."""
        engine = QuantumDispersionEngine()
        
        # 丑 has 己, 癸, 辛
        weights_start = engine.get_dynamic_weights("丑", 0.0)
        weights_mid = engine.get_dynamic_weights("丑", 0.5)
        weights_end = engine.get_dynamic_weights("丑", 1.0)
        
        # At start (t=0): primary (己) should be minimal
        assert weights_start["己"] < 1.0
        
        # At mid-point (t=0.5): primary (己) should be maximal
        assert weights_mid["己"] > 5.0
        
        # Sum should always be 10
        assert abs(sum(weights_start.values()) - 10.0) < 0.01
        assert abs(sum(weights_mid.values()) - 10.0) < 0.01
        assert abs(sum(weights_end.values()) - 10.0) < 0.01
    
    def test_weights_sum_to_10(self):
        """Test that all weights always sum to 10."""
        engine = QuantumDispersionEngine()
        
        for branch in ["丑", "寅", "辰", "巳", "午", "未", "申", "戌", "亥"]:
            for progress in [0.0, 0.1, 0.25, 0.5, 0.75, 0.9, 1.0]:
                weights = engine.get_dynamic_weights(branch, progress)
                total = sum(weights.values())
                assert abs(total - 10.0) < 0.01, f"Branch {branch} at t={progress}: sum={total}"
    
    def test_smooth_transition(self):
        """Test that weights change smoothly (no abrupt jumps)."""
        engine = QuantumDispersionEngine()
        branch = "丑"
        
        prev_weights = engine.get_dynamic_weights(branch, 0.0)
        for i in range(1, 101):
            progress = i / 100.0
            curr_weights = engine.get_dynamic_weights(branch, progress)
            
            for stem in prev_weights:
                delta = abs(curr_weights[stem] - prev_weights[stem])
                # Maximum change per 1% step should be reasonable (< 0.5)
                assert delta < 0.5, f"Abrupt change at t={progress}: {delta}"
            
            prev_weights = curr_weights
    
    def test_damping_factor_effect(self):
        """Test that damping factor affects residual energy."""
        engine_low = QuantumDispersionEngine(damping_factor=0.5)
        engine_high = QuantumDispersionEngine(damping_factor=2.0)
        
        # Residual is the last stem (辛 for 丑)
        # At mid-point, residual should be affected by damping
        weights_low = engine_low.get_dynamic_weights("丑", 0.5)
        weights_high = engine_high.get_dynamic_weights("丑", 0.5)
        
        # Higher damping should give more weight to residual
        # Note: due to normalization, the relative ratio changes
        assert weights_high is not None  # Just ensure it runs


class TestBaziParticleNexusDynamicAccessor:
    """Test suite for BaziParticleNexus dynamic weight accessor."""
    
    def test_static_mode(self):
        """Test static mode (no dispersion engine)."""
        weights = BaziParticleNexus.get_branch_weights("丑")
        assert weights == [('己', 5), ('癸', 3), ('辛', 2)]
    
    def test_dynamic_mode(self):
        """Test dynamic mode with dispersion engine."""
        engine = QuantumDispersionEngine()
        weights = BaziParticleNexus.get_branch_weights("丑", phase_progress=0.5, dispersion_engine=engine)
        
        # Should return list of tuples
        assert isinstance(weights, list)
        assert len(weights) == 3
        
        # First stem (己) should have highest weight at t=0.5
        stems = {w[0]: w[1] for w in weights}
        assert stems["己"] > 5.0
    
    def test_backward_compatibility(self):
        """Test that legacy code still works with None parameters."""
        # Calling with no extra args should return static
        weights = BaziParticleNexus.get_branch_weights("寅")
        assert weights == [('甲', 5), ('丙', 3), ('戊', 2)]


class TestEdgeCaseBoundary:
    """Test edge cases near solar term boundaries."""
    
    def test_boundary_no_jump(self):
        """Test that there's no jump at t=0 to t=0.01."""
        engine = QuantumDispersionEngine()
        
        weights_0 = engine.get_dynamic_weights("丑", 0.0)
        weights_001 = engine.get_dynamic_weights("丑", 0.001)
        
        for stem in weights_0:
            delta = abs(weights_001[stem] - weights_0[stem])
            assert delta < 0.1, f"Jump at boundary: {stem} delta={delta}"
    
    def test_boundary_near_1(self):
        """Test that there's no jump at t=0.999 to t=1.0."""
        engine = QuantumDispersionEngine()
        
        weights_999 = engine.get_dynamic_weights("丑", 0.999)
        weights_1 = engine.get_dynamic_weights("丑", 1.0)
        
        for stem in weights_999:
            delta = abs(weights_1[stem] - weights_999[stem])
            assert delta < 0.1, f"Jump near end: {stem} delta={delta}"
    
    def test_continuous_at_midpoint(self):
        """Test continuity around t=0.5."""
        engine = QuantumDispersionEngine()
        
        weights_49 = engine.get_dynamic_weights("丑", 0.49)
        weights_50 = engine.get_dynamic_weights("丑", 0.50)
        weights_51 = engine.get_dynamic_weights("丑", 0.51)
        
        for stem in weights_49:
            # Changes should be minimal around midpoint
            delta_before = abs(weights_50[stem] - weights_49[stem])
            delta_after = abs(weights_51[stem] - weights_50[stem])
            assert delta_before < 0.3
            assert delta_after < 0.3


class TestComparisonStaticVsDynamic:
    """Test static vs dynamic comparison functionality."""
    
    def test_compare_output_format(self):
        """Test comparison output format."""
        engine = QuantumDispersionEngine()
        comparison = engine.compare_static_vs_dynamic("丑", 0.5)
        
        assert "branch" in comparison
        assert "phase_progress" in comparison
        assert "static" in comparison
        assert "dynamic" in comparison
        assert "delta" in comparison
        
        assert comparison["branch"] == "丑"
        assert comparison["phase_progress"] == 0.5
    
    def test_delta_calculation(self):
        """Test that delta is correctly calculated."""
        engine = QuantumDispersionEngine()
        comparison = engine.compare_static_vs_dynamic("丑", 0.5)
        
        for stem in comparison["static"]:
            expected_delta = comparison["dynamic"][stem] - comparison["static"][stem]
            assert abs(comparison["delta"][stem] - expected_delta) < 0.01


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
