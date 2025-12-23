"""
Test Suite: Phase 36-38 Relationship Gravity Engine
====================================================
Tests for the RelationshipGravityEngine including:
- State determination logic (ENTANGLED, BOUND, PERTURBED, UNBOUND)
- Monte Carlo confidence calculation
- Bazi interaction detection (Clash, Punishment, San He)
- 60-year Jiazi cycle birth year estimation
"""

import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.trinity.core.engines.relationship_gravity import RelationshipGravityEngine
from core.trinity.core.nexus.definitions import ArbitrationNexus, BaziParticleNexus


class MockWave:
    """Mock wave object for testing."""
    def __init__(self, amplitude: float, phase: float):
        self.amplitude = amplitude
        self.phase = phase


def get_mock_waves():
    """Create standard mock waves for testing."""
    return {
        "Wood": MockWave(10.0, 0.5),
        "Fire": MockWave(10.0, 0.5),
        "Earth": MockWave(10.0, 0.5),
        "Metal": MockWave(10.0, 0.5),
        "Water": MockWave(10.0, 0.5)
    }


class TestRelationshipGravityEngine:
    """Test suite for RelationshipGravityEngine."""
    
    def test_engine_initialization_male(self):
        """Test engine initialization for male subject."""
        engine = RelationshipGravityEngine("乙", "男")
        assert engine.dm_element == "Wood"
        # Male: Wealth (DM controls) is Spouse Star
        # Wood controls Earth
        assert engine.spouse_star_element == "Earth"
    
    def test_engine_initialization_female(self):
        """Test engine initialization for female subject."""
        engine = RelationshipGravityEngine("乙", "女")
        assert engine.dm_element == "Wood"
        # Female: Control (controls DM) is Spouse Star
        # Metal controls Wood
        assert engine.spouse_star_element == "Metal"
    
    def test_analyze_relationship_basic(self):
        """Test basic relationship analysis."""
        engine = RelationshipGravityEngine("乙", "男")
        waves = get_mock_waves()
        bazi = ['丁巳', '乙巳', '乙丑', '乙酉']
        
        result = engine.analyze_relationship(
            waves, bazi,
            luck_pillar="甲辰",
            annual_pillar="丁巳",
            geo_factor=1.0
        )
        
        # Check required fields
        assert 'State' in result
        assert 'Binding_Energy' in result
        assert 'Orbital_Stability' in result
        assert 'Phase_Coherence' in result
        assert 'State_Confidence' in result
        assert 'State_Probabilities' in result
        assert 'Metrics' in result
    
    def test_state_entangled(self):
        """Test ENTANGLED state with high coherence and stability."""
        engine = RelationshipGravityEngine("乙", "男")
        waves = get_mock_waves()
        bazi = ['丁巳', '乙巳', '乙丑', '乙酉']
        
        result = engine.analyze_relationship(
            waves, bazi,
            luck_pillar="甲辰",
            annual_pillar="丁巳",
            geo_factor=1.0
        )
        
        # With mock waves (all same phase), coherence should be 1.0
        assert result['Phase_Coherence'] == 1.0
        # Without clash, r should be low → ENTANGLED
        assert result['State'] == 'ENTANGLED'
        assert result['State_Confidence'] >= 0.9
    
    def test_state_bound_on_clash(self):
        """Test BOUND state when annual pillar clashes with spouse palace."""
        engine = RelationshipGravityEngine("乙", "男")
        waves = get_mock_waves()
        bazi = ['丁巳', '乙巳', '乙丑', '乙酉']  # Spouse palace: 丑
        
        # 己未 clashes with 丑 (未冲丑)
        result = engine.analyze_relationship(
            waves, bazi,
            luck_pillar="甲辰",
            annual_pillar="己未",  # 未 clashes with 丑
            geo_factor=1.0
        )
        
        # With clash, r should be higher → BOUND or PERTURBED
        assert result['Metrics']['Orbital_Distance'] >= 2.5
        assert result['State'] in ['BOUND', 'PERTURBED']
    
    def test_monte_carlo_confidence(self):
        """Test Monte Carlo sampling returns valid probabilities."""
        engine = RelationshipGravityEngine("乙", "男")
        waves = get_mock_waves()
        bazi = ['丁巳', '乙巳', '乙丑', '乙酉']
        
        result = engine.analyze_relationship(
            waves, bazi,
            luck_pillar="甲辰",
            annual_pillar="丁巳",
            geo_factor=1.0
        )
        
        probs = result['State_Probabilities']
        
        # Check all states are present
        assert 'ENTANGLED' in probs
        assert 'BOUND' in probs
        assert 'PERTURBED' in probs
        assert 'UNBOUND' in probs
        
        # Check probabilities sum to 1.0
        total_prob = sum(probs.values())
        assert abs(total_prob - 1.0) < 0.01
        
        # Confidence should match the probability of deterministic state
        assert result['State_Confidence'] == probs[result['State']]
    
    def test_geo_factor_effect(self):
        """Test that geo_factor affects orbital distance."""
        engine = RelationshipGravityEngine("乙", "男")
        waves = get_mock_waves()
        bazi = ['丁巳', '乙巳', '乙丑', '乙酉']
        
        # Low geo factor
        result_low = engine.analyze_relationship(
            waves, bazi,
            luck_pillar="甲辰",
            annual_pillar="丁巳",
            geo_factor=0.5
        )
        
        # High geo factor
        result_high = engine.analyze_relationship(
            waves, bazi,
            luck_pillar="甲辰",
            annual_pillar="丁巳",
            geo_factor=2.0
        )
        
        # The orbital distances or binding energies should differ
        assert result_low['Binding_Energy'] != result_high['Binding_Energy']
    
    def test_determine_state_helper(self):
        """Test _determine_state helper method directly."""
        engine = RelationshipGravityEngine("乙", "男")
        
        # High r → UNBOUND
        assert engine._determine_state(r=7.0, orbital_stability=5.0, phase_coherence=0.9) == "UNBOUND"
        
        # Medium-high r → PERTURBED
        assert engine._determine_state(r=4.5, orbital_stability=5.0, phase_coherence=0.9) == "PERTURBED"
        
        # Medium r with high stability → BOUND
        assert engine._determine_state(r=3.0, orbital_stability=2.0, phase_coherence=0.9) == "BOUND"
        
        # Low r with high stability and coherence → ENTANGLED
        assert engine._determine_state(r=1.0, orbital_stability=3.0, phase_coherence=0.9) == "ENTANGLED"
        
        # Low coherence → PERTURBED or UNBOUND
        state = engine._determine_state(r=1.0, orbital_stability=3.0, phase_coherence=0.05)
        assert state in ["PERTURBED", "UNBOUND"]
    
    def test_spouse_palace_extraction(self):
        """Test that spouse palace is correctly extracted from day pillar."""
        engine = RelationshipGravityEngine("乙", "男")
        waves = get_mock_waves()
        bazi = ['丁巳', '乙巳', '乙丑', '乙酉']  # Day pillar: 乙丑 → Spouse palace: 丑
        
        result = engine.analyze_relationship(
            waves, bazi,
            luck_pillar="甲辰",
            annual_pillar="丁巳",
            geo_factor=1.0
        )
        
        assert result['Metrics']['Spouse_Palace'] == '丑'
        assert result['Metrics']['Spouse_Palace_Element'] == 'Earth'


class TestJiaziCycleEstimation:
    """Test suite for 60-year Jiazi cycle birth year estimation."""
    
    def test_jiazi_cycle_calculation(self):
        """Test Jiazi cycle calculation for birth year estimation."""
        import datetime
        current_year = datetime.datetime.now().year
        
        # Test year pillar: 丁巳 (should be 1977 or 2037)
        year_pillar = "丁巳"
        stems = "甲乙丙丁戊己庚辛壬癸"
        branches = "子丑寅卯辰巳午未申酉戌亥"
        
        estimated_year = None
        for test_year in range(current_year - 20, current_year - 100, -1):
            stem_idx = (test_year - 4) % 10
            branch_idx = (test_year - 4) % 12
            test_pillar = stems[stem_idx] + branches[branch_idx]
            if test_pillar == year_pillar:
                estimated_year = test_year
                break
        
        # 丁巳 should map to 1977 (48 years old in 2025)
        assert estimated_year == 1977
    
    def test_jiazi_cycle_甲子(self):
        """Test Jiazi cycle for 甲子 year."""
        import datetime
        current_year = datetime.datetime.now().year
        
        year_pillar = "甲子"
        stems = "甲乙丙丁戊己庚辛壬癸"
        branches = "子丑寅卯辰巳午未申酉戌亥"
        
        estimated_year = None
        for test_year in range(current_year - 20, current_year - 100, -1):
            stem_idx = (test_year - 4) % 10
            branch_idx = (test_year - 4) % 12
            test_pillar = stems[stem_idx] + branches[branch_idx]
            if test_pillar == year_pillar:
                estimated_year = test_year
                break
        
        # 甲子 should map to 1984 (41 years old in 2025)
        assert estimated_year == 1984


class TestArbitrationNexus:
    """Test suite for ArbitrationNexus constants."""
    
    def test_clash_map_exists(self):
        """Test that CLASH_MAP is defined."""
        assert hasattr(ArbitrationNexus, 'CLASH_MAP')
        # 丑 ↔ 未
        assert ArbitrationNexus.CLASH_MAP.get('丑') == '未'
        assert ArbitrationNexus.CLASH_MAP.get('未') == '丑'
    
    def test_liu_he_exists(self):
        """Test that LIU_HE is defined for Six Harmonies."""
        assert hasattr(ArbitrationNexus, 'LIU_HE')
    
    def test_san_he_exists(self):
        """Test that SAN_HE is defined for Three Harmonies."""
        assert hasattr(ArbitrationNexus, 'SAN_HE')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
