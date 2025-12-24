import unittest
import sys
import os

# Ensure core is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.trinity.core.engines.relationship_gravity import RelationshipGravityEngine
from core.trinity.core.nexus.definitions import ArbitrationNexus

class MockWave:
    def __init__(self, amplitude: float, phase: float):
        self.amplitude = amplitude
        self.phase = phase

def get_mock_waves():
    return {
        "Wood": MockWave(10.0, 0.5),
        "Fire": MockWave(10.0, 0.5),
        "Earth": MockWave(10.0, 0.5),
        "Metal": MockWave(10.0, 0.5),
        "Water": MockWave(10.0, 0.5)
    }

class TestRelationshipGravityEngine(unittest.TestCase):
    def test_engine_initialization_male(self):
        engine = RelationshipGravityEngine("乙", "男")
        self.assertEqual(engine.dm_element, "Wood")
        self.assertEqual(engine.spouse_star_element, "Earth")
    
    def test_engine_initialization_female(self):
        engine = RelationshipGravityEngine("乙", "女")
        self.assertEqual(engine.dm_element, "Wood")
        self.assertEqual(engine.spouse_star_element, "Metal")
    
    def test_analyze_relationship_basic(self):
        engine = RelationshipGravityEngine("乙", "男")
        waves = get_mock_waves()
        bazi = ['丁巳', '乙巳', '乙丑', '乙酉']
        result = engine.analyze_relationship(waves, bazi, luck_pillar="甲辰", annual_pillar="丁巳", geo_factor=1.0)
        self.assertIn('State', result)
        self.assertIn('Binding_Energy', result)
        self.assertIn('Orbital_Stability', result)
        self.assertIn('Phase_Coherence', result)
    
    def test_state_entangled(self):
        engine = RelationshipGravityEngine("乙", "男")
        waves = get_mock_waves()
        bazi = ['丁巳', '乙巳', '乙丑', '乙酉']
        result = engine.analyze_relationship(waves, bazi, luck_pillar="甲辰", annual_pillar="丁巳", geo_factor=1.0)
        self.assertEqual(result['Phase_Coherence'], 1.0)
        self.assertEqual(result['State'], 'ENTANGLED')
    
    def test_state_bound_on_clash(self):
        engine = RelationshipGravityEngine("乙", "男")
        waves = get_mock_waves()
        bazi = ['丁巳', '乙巳', '乙丑', '乙酉']  # 丑
        result = engine.analyze_relationship(waves, bazi, luck_pillar="甲辰", annual_pillar="己未", geo_factor=1.0) # 未冲丑
        self.assertIn(result['State'], ['BOUND', 'PERTURBED'])
    
    def test_determine_state_helper(self):
        engine = RelationshipGravityEngine("乙", "男")
        self.assertEqual(engine._determine_state(r=7.0, orbital_stability=5.0, phase_coherence=0.9), "UNBOUND")
        self.assertEqual(engine._determine_state(r=1.0, orbital_stability=3.0, phase_coherence=0.9), "ENTANGLED")

class TestJiaziCycleEstimation(unittest.TestCase):
    def test_jiazi_cycle_calculation(self):
        import datetime
        current_year = 2025
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
        self.assertEqual(estimated_year, 1977)

class TestArbitrationNexus(unittest.TestCase):
    def test_clash_map_exists(self):
        self.assertTrue(hasattr(ArbitrationNexus, 'CLASH_MAP'))
        self.assertEqual(ArbitrationNexus.CLASH_MAP.get('丑'), '未')

if __name__ == "__main__":
    unittest.main()
