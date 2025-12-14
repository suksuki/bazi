"""
Antigravity V8.8 Comprehensive Test Suite
==========================================
Last Update: 2025-12-14
Purpose: Automated full regression testing for V8.8 Engine

Test Categories:
1. Core Physics (Energy Calculation)
2. Strength Judgment (Wang Shuai)  
3. Phase Change Protocol (焦土/冻水)
4. Sub-Engines (Treasury, Skull, Harmony, Luck)
5. Year Context (流年推演)
6. BaziProfile Integration
7. UI Integration Smoke Test
"""

import unittest
from datetime import datetime
from typing import Dict, Any

# === Core Imports ===
from core.engine_v88 import EngineV88
from core.bazi_profile import BaziProfile
from core.context import DestinyContext


class TestV88CorePhysics(unittest.TestCase):
    """Test Layer 1: Core Physics Processor"""
    
    def setUp(self):
        self.engine = EngineV88()
    
    def test_physics_processor_exists(self):
        """Physics processor should be initialized"""
        self.assertIsNotNone(self.engine.physics)
        print("✅ Physics Processor initialized")
    
    def test_raw_energy_calculation(self):
        """Raw energy should be calculated for all 5 elements"""
        bazi = ['甲子', '丙午', '辛卯', '壬辰']
        dm = '辛'
        
        result = self.engine.analyze(bazi, dm)
        energy = result.energy_distribution
        
        # All 5 elements should exist
        self.assertIn('wood', energy)
        self.assertIn('fire', energy)
        self.assertIn('earth', energy)
        self.assertIn('metal', energy)
        self.assertIn('water', energy)
        
        # Energy values should be non-negative
        for elem, val in energy.items():
            self.assertGreaterEqual(val, 0, f"{elem} energy should be >= 0")
        
        print(f"✅ Raw Energy: {energy}")
    
    def test_element_detection(self):
        """Element detection for stems and branches"""
        # Stem tests
        self.assertEqual(self.engine._get_element('甲'), 'wood')
        self.assertEqual(self.engine._get_element('丙'), 'fire')
        self.assertEqual(self.engine._get_element('庚'), 'metal')
        self.assertEqual(self.engine._get_element('壬'), 'water')
        self.assertEqual(self.engine._get_element('戊'), 'earth')
        
        # Branch tests
        self.assertEqual(self.engine._get_element('寅'), 'wood')
        self.assertEqual(self.engine._get_element('午'), 'fire')
        self.assertEqual(self.engine._get_element('酉'), 'metal')
        self.assertEqual(self.engine._get_element('子'), 'water')
        self.assertEqual(self.engine._get_element('丑'), 'earth')
        
        print("✅ Element detection correct")


class TestV88StrengthJudgment(unittest.TestCase):
    """Test Layer 3: Strength Judgment"""
    
    def setUp(self):
        self.engine = EngineV88()
    
    def test_strong_case(self):
        """Strong DM should be detected"""
        # 甲木 strong in 寅月 (spring, wood month)
        bazi = ['甲寅', '甲寅', '甲子', '甲寅']
        dm = '甲'
        
        verdict, score = self.engine.evaluate_strength(dm, bazi)
        
        # Should be strong
        self.assertEqual(verdict, 'Strong', f"Expected Strong, got {verdict}")
        print(f"✅ Strong case: {verdict} ({score:.1f})")
    
    def test_weak_case(self):
        """Weak DM should be detected"""
        # 甲木 weak in 酉月 (autumn, metal month controls wood)
        bazi = ['庚申', '乙酉', '甲午', '庚申']
        dm = '甲'
        
        verdict, score = self.engine.evaluate_strength(dm, bazi)
        
        # Should be weak
        self.assertEqual(verdict, 'Weak', f"Expected Weak, got {verdict}")
        print(f"✅ Weak case: {verdict} ({score:.1f})")
    
    def test_verdict_consistency(self):
        """Verdict should be consistent across multiple calls"""
        bazi = ['甲子', '丙午', '辛卯', '壬辰']
        dm = '辛'
        
        results = [self.engine.evaluate_strength(dm, bazi) for _ in range(3)]
        
        # All results should be the same
        self.assertEqual(results[0][0], results[1][0])
        self.assertEqual(results[1][0], results[2][0])
        print(f"✅ Verdict consistent: {results[0][0]}")


class TestV88PhaseChange(unittest.TestCase):
    """Test Layer 2.5: Phase Change Protocol"""
    
    def setUp(self):
        self.engine = EngineV88()
    
    def test_phase_change_processor_exists(self):
        """Phase change processor should be initialized"""
        self.assertIsNotNone(self.engine.phase_change)
        print("✅ Phase Change Processor initialized")
    
    def test_scorched_earth_detection(self):
        """焦土不生金 should trigger in summer for metal DM"""
        # Metal DM in 午月 (summer fire month)
        context = {
            'bazi': ['甲子', '庚午', '辛丑', '戊子'],
            'month_branch': '午',
            'dm_element': 'metal'
        }
        
        result = self.engine.phase_change.process(context)
        
        self.assertTrue(result['is_active'])
        self.assertLess(result['resource_efficiency'], 1.0)
        print(f"✅ Scorched Earth: efficiency={result['resource_efficiency']}")
    
    def test_frozen_water_detection(self):
        """冻水不生木 should trigger in winter for wood DM"""
        # Wood DM in 子月 (winter water month)
        context = {
            'bazi': ['甲子', '丙子', '甲寅', '壬子'],
            'month_branch': '子',
            'dm_element': 'wood'
        }
        
        result = self.engine.phase_change.process(context)
        
        self.assertTrue(result['is_active'])
        self.assertLess(result['resource_efficiency'], 1.0)
        print(f"✅ Frozen Water: efficiency={result['resource_efficiency']}")
    
    def test_normal_no_phase_change(self):
        """No phase change in normal conditions"""
        # Fire DM in 午月 (fire month - in command, no phase penalty)
        context = {
            'bazi': ['甲子', '庚午', '丁丑', '戊子'],
            'month_branch': '午',
            'dm_element': 'fire'
        }
        
        result = self.engine.phase_change.process(context)
        
        self.assertFalse(result['is_active'])
        self.assertEqual(result['resource_efficiency'], 1.0)
        print(f"✅ Normal: no phase change")


class TestV88SubEngines(unittest.TestCase):
    """Test Sub-Engines: Treasury, Skull, Harmony, Luck"""
    
    def setUp(self):
        self.engine = EngineV88()
    
    def test_treasury_engine_exists(self):
        """Treasury Engine should be initialized"""
        self.assertIsNotNone(self.engine.treasury_engine)
        print("✅ Treasury Engine initialized")
    
    def test_skull_engine_exists(self):
        """Skull Engine should be initialized"""
        self.assertIsNotNone(self.engine.skull_engine)
        print("✅ Skull Engine initialized")
    
    def test_harmony_engine_exists(self):
        """Harmony Engine should be initialized"""
        self.assertIsNotNone(self.engine.harmony_engine)
        print("✅ Harmony Engine initialized")
    
    def test_luck_engine_exists(self):
        """Luck Engine should be initialized"""
        self.assertIsNotNone(self.engine.luck_engine)
        print("✅ Luck Engine initialized")
    
    def test_skull_three_punishments(self):
        """Skull should detect 丑未戌 three punishments"""
        # All three punishment branches present
        branches = ['丑', '未', '戌']
        
        result = self.engine.skull_engine.evaluate(branches)
        
        self.assertEqual(result['icon'], '💀')
        self.assertIn('三刑齐见', result['tags'])
        self.assertLessEqual(result['score'], -40)
        print(f"✅ Skull Protocol: score={result['score']}, icon={result['icon']}")


class TestV88YearContext(unittest.TestCase):
    """Test Year Context Calculation"""
    
    def setUp(self):
        self.engine = EngineV88()
    
    def test_year_pillar_calculation(self):
        """Year pillar should be calculated correctly"""
        # 2024 is 甲辰年
        pillar = self.engine.get_year_pillar(2024)
        
        self.assertEqual(len(pillar), 2)
        self.assertEqual(pillar, '甲辰')
        print(f"✅ Year 2024 pillar: {pillar}")
    
    def test_year_context_with_profile(self):
        """Year context should work with BaziProfile"""
        # Create profile
        birth_date = datetime(1990, 5, 15, 12)
        profile = BaziProfile(birth_date, gender=1)
        
        # Calculate context for 2024
        ctx = self.engine.calculate_year_context(profile, 2024)
        
        # Verify context structure
        self.assertIsInstance(ctx, DestinyContext)
        self.assertEqual(ctx.year, 2024)
        self.assertIsNotNone(ctx.pillar)
        self.assertIsNotNone(ctx.icon)
        self.assertIsNotNone(ctx.score)
        
        print(f"✅ Year Context: year={ctx.year}, pillar={ctx.pillar}, score={ctx.score}, icon={ctx.icon}")
    
    def test_year_context_dimensions(self):
        """Year context should include career, wealth, relationship"""
        birth_date = datetime(1985, 3, 20, 8)
        profile = BaziProfile(birth_date, gender=1)
        
        ctx = self.engine.calculate_year_context(profile, 2025)
        
        # Check dimension scores exist
        self.assertIsNotNone(ctx.career)
        self.assertIsNotNone(ctx.wealth)
        self.assertIsNotNone(ctx.relationship)
        
        # Scores should be reasonable (0-15 range typically)
        self.assertGreaterEqual(ctx.career, 0)
        self.assertGreaterEqual(ctx.wealth, 0)
        self.assertGreaterEqual(ctx.relationship, 0)
        
        print(f"✅ Dimensions: career={ctx.career:.1f}, wealth={ctx.wealth:.1f}, rel={ctx.relationship:.1f}")


class TestV88BaziProfile(unittest.TestCase):
    """Test BaziProfile Integration"""
    
    def test_profile_creation(self):
        """BaziProfile should be created correctly"""
        birth_date = datetime(1990, 8, 15, 14)
        profile = BaziProfile(birth_date, gender=1)
        
        self.assertIsNotNone(profile.pillars)
        self.assertIsNotNone(profile.day_master)
        self.assertEqual(len(profile.pillars), 4)
        
        print(f"✅ Profile: DM={profile.day_master}, Pillars={profile.pillars}")
    
    def test_luck_pillar_query(self):
        """Luck pillar should be queryable by year"""
        birth_date = datetime(1990, 8, 15, 14)
        profile = BaziProfile(birth_date, gender=1)
        
        # Query luck pillar for different years
        luck_2020 = profile.get_luck_pillar_at(2020)
        luck_2030 = profile.get_luck_pillar_at(2030)
        
        self.assertIsNotNone(luck_2020)
        self.assertIsNotNone(luck_2030)
        
        print(f"✅ Luck Pillars: 2020={luck_2020}, 2030={luck_2030}")
    
    def test_profile_gender_handling(self):
        """Profile should handle gender correctly"""
        birth_date = datetime(1990, 8, 15, 14)
        
        male_profile = BaziProfile(birth_date, gender=1)
        female_profile = BaziProfile(birth_date, gender=0)
        
        self.assertEqual(male_profile.gender, 1)
        self.assertEqual(female_profile.gender, 0)
        
        print(f"✅ Gender handling correct")


class TestV88LuckTimeline(unittest.TestCase):
    """Test Luck Timeline Generation"""
    
    def setUp(self):
        self.engine = EngineV88()
    
    def test_timeline_generation(self):
        """Timeline should generate correct number of years"""
        birth_date = datetime(1985, 6, 20, 10)
        profile = BaziProfile(birth_date, gender=1)
        
        timeline = self.engine.get_luck_timeline(profile, start_year_or_month=2024, years_or_day=12)
        
        self.assertEqual(len(timeline), 12)
        self.assertEqual(timeline[0]['year'], 2024)
        self.assertEqual(timeline[-1]['year'], 2035)
        
        print(f"✅ Timeline: {len(timeline)} years from {timeline[0]['year']} to {timeline[-1]['year']}")
    
    def test_timeline_handover_detection(self):
        """Timeline should detect luck pillar handover"""
        birth_date = datetime(1985, 6, 20, 10)
        profile = BaziProfile(birth_date, gender=1)
        
        timeline = self.engine.get_luck_timeline(profile, start_year_or_month=2020, years_or_day=20)
        
        # At least one handover should exist in 20 years
        handover_years = [t['year'] for t in timeline if t.get('is_handover')]
        
        self.assertGreater(len(handover_years), 0, "Should have at least one handover in 20 years")
        print(f"✅ Handover years: {handover_years}")


class TestV88EnergyCalculation(unittest.TestCase):
    """Test Energy Calculation for UI"""
    
    def setUp(self):
        self.engine = EngineV88()
    
    def test_energy_calculation_structure(self):
        """Energy calculation should return complete structure"""
        case_data = {
            'day_master': '甲',
            'year': '甲子',
            'month': '丙午',
            'day': '甲寅',
            'hour': '壬辰',
            'gender': 1
        }
        
        result = self.engine.calculate_energy(case_data)
        
        # Check required keys
        self.assertIn('wang_shuai', result)
        self.assertIn('dm_element', result)
        self.assertIn('favorable', result)
        self.assertIn('energy_map', result)
        self.assertIn('career', result)
        self.assertIn('wealth', result)
        self.assertIn('relationship', result)
        
        print(f"✅ Energy: {result['wang_shuai']}, career={result['career']:.1f}, wealth={result['wealth']:.1f}")
    
    def test_energy_map_completeness(self):
        """Energy map should contain all 5 elements"""
        case_data = {
            'day_master': '辛',
            'year': '庚申',
            'month': '乙酉',
            'day': '辛丑',
            'hour': '壬辰',
            'gender': 0
        }
        
        result = self.engine.calculate_energy(case_data)
        energy_map = result['energy_map']
        
        for elem in ['wood', 'fire', 'earth', 'metal', 'water']:
            self.assertIn(elem, energy_map)
        
        print(f"✅ Energy Map: {energy_map}")


def run_comprehensive_tests():
    """Run all V8.8 comprehensive tests"""
    print("\n" + "=" * 70)
    print("🧪 ANTIGRAVITY V8.8 COMPREHENSIVE TEST SUITE")
    print("=" * 70 + "\n")
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        TestV88CorePhysics,
        TestV88StrengthJudgment,
        TestV88PhaseChange,
        TestV88SubEngines,
        TestV88YearContext,
        TestV88BaziProfile,
        TestV88LuckTimeline,
        TestV88EnergyCalculation,
    ]
    
    for test_class in test_classes:
        suite.addTests(loader.loadTestsFromTestCase(test_class))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 70)
    print("📊 TEST SUMMARY")
    print("=" * 70)
    print(f"  Tests Run: {result.testsRun}")
    print(f"  ✅ Passed: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"  ❌ Failed: {len(result.failures)}")
    print(f"  ⚠️ Errors: {len(result.errors)}")
    print("=" * 70)
    
    if result.wasSuccessful():
        print("🎉 ALL TESTS PASSED!")
    else:
        print("⚠️ SOME TESTS FAILED")
        if result.failures:
            print("\nFailures:")
            for test, trace in result.failures:
                print(f"  - {test}")
        if result.errors:
            print("\nErrors:")
            for test, trace in result.errors:
                print(f"  - {test}")
    
    return result.wasSuccessful()


if __name__ == '__main__':
    run_comprehensive_tests()
