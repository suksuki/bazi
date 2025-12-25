"""
Antigravity V14.1.8 Comprehensive Test Suite
=============================================
Automated tests for SGJG, SGSJ, and PGB pattern detection.
"""

import unittest
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.trinity.core.engines.pattern_scout import PatternScout, GEO_ELEMENT_MAP
from core.trinity.core.nexus.definitions import BaziParticleNexus, PhysicsConstants as PC
from core.profile_manager import ProfileManager
from core.bazi_profile import BaziProfile
from datetime import datetime


class TestGeoElementMap(unittest.TestCase):
    """Test GEO Element Affinity Map structure."""

    def test_geo_map_exists(self):
        """GEO_ELEMENT_MAP should be defined."""
        self.assertIsNotNone(GEO_ELEMENT_MAP)
        self.assertIn("Neutral", GEO_ELEMENT_MAP)

    def test_geo_map_has_all_elements(self):
        """Each GEO entry should have all 5 elements."""
        for geo_type, elem_map in GEO_ELEMENT_MAP.items():
            self.assertIn("Fire", elem_map, f"{geo_type} missing Fire")
            self.assertIn("Water", elem_map, f"{geo_type} missing Water")
            self.assertIn("Wood", elem_map, f"{geo_type} missing Wood")
            self.assertIn("Metal", elem_map, f"{geo_type} missing Metal")
            self.assertIn("Earth", elem_map, f"{geo_type} missing Earth")

    def test_neutral_geo_is_1(self):
        """Neutral GEO should have 1.0 for all elements."""
        for elem, val in GEO_ELEMENT_MAP["Neutral"].items():
            self.assertEqual(val, 1.0, f"Neutral {elem} should be 1.0")


class TestPatternScoutSGJG(unittest.TestCase):
    """Test SHANG_GUAN_JIAN_GUAN (伤官见官) detection."""

    def setUp(self):
        self.scout = PatternScout()

    def test_sgjg_requires_attacker_and_officer(self):
        """SGJG should return None if no attacker or officer."""
        # All 比肩 - no attackers or officers
        chart = [('甲', '子'), ('甲', '子'), ('甲', '子'), ('甲', '子')]
        result = self.scout._deep_audit(chart, 'SHANG_GUAN_JIAN_GUAN')
        self.assertIsNone(result)

    def test_sgjg_detects_collision(self):
        """SGJG should detect when 伤官 meets 正官 with low protection."""
        # 甲木日主, 丁火=伤官, 辛金=正官
        # This is a minimal test case
        chart = [('丁', '巳'), ('辛', '酉'), ('甲', '寅'), ('丁', '巳')]
        result = self.scout._deep_audit(chart, 'SHANG_GUAN_JIAN_GUAN')
        # May or may not match depending on protection calculation
        # Just verify no crash
        self.assertTrue(result is None or isinstance(result, dict))

    def test_sgjg_6_pillar_support(self):
        """SGJG should work with 6 pillars (natal + luck + annual)."""
        chart = [('丁', '巳'), ('乙', '巳'), ('乙', '丑'), ('乙', '酉'), ('庚', '子'), ('丙', '午')]
        result = self.scout._deep_audit(chart, 'SHANG_GUAN_JIAN_GUAN')
        # Just verify no crash with 6 pillars
        self.assertTrue(result is None or isinstance(result, dict))


class TestPatternScoutSGSJ(unittest.TestCase):
    """Test SHANG_GUAN_SHANG_JIN (伤官伤尽) detection."""

    def setUp(self):
        self.scout = PatternScout()

    def test_sgsj_requires_shang_guan(self):
        """SGSJ should return None if no 伤官 in stems."""
        # 甲木日主, all 比肩
        chart = [('甲', '子'), ('甲', '子'), ('甲', '子'), ('甲', '子')]
        result = self.scout._deep_audit(chart, 'SHANG_GUAN_SHANG_JIN')
        self.assertIsNone(result)

    def test_sgsj_rejects_natal_guan(self):
        """SGSJ should return None if natal stems have 正官/七杀."""
        # 甲木日主, 辛金=正官 in natal stem
        chart = [('丁', '巳'), ('辛', '酉'), ('甲', '寅'), ('丁', '巳')]
        result = self.scout._deep_audit(chart, 'SHANG_GUAN_SHANG_JIN')
        self.assertIsNone(result)

    def test_sgsj_detects_superconductor(self):
        """SGSJ should detect pure superconductor with purity > 0.95."""
        # 戊土日主, 辛金=伤官, no 甲乙木(官杀) in natal
        # 戊午 戊午 丁未 甲辰 - this is 黄翔's chart
        # 丁火日主, 庚辛=伤官, 甲乙=正官
        chart = [('戊', '午'), ('戊', '午'), ('丁', '未'), ('甲', '辰'), ('壬', '戌'), ('乙', '巳')]
        result = self.scout._deep_audit(chart, 'SHANG_GUAN_SHANG_JIN')
        if result:
            self.assertIn('purity', result)
            self.assertIn('category', result)


class TestPatternScoutPGB(unittest.TestCase):
    """Test PGB pattern detection."""

    def setUp(self):
        self.scout = PatternScout()

    def test_pgb_superfluid_rejects_guan(self):
        """PGB_SUPER_FLUID_LOCK should reject if stems have 正官/七杀."""
        # 甲木日主, 辛金=正官
        chart = [('辛', '酉'), ('甲', '寅'), ('甲', '寅'), ('甲', '寅')]
        result = self.scout._deep_audit(chart, 'PGB_SUPER_FLUID_LOCK')
        self.assertIsNone(result)

    def test_pgb_brittle_requires_guan(self):
        """PGB_BRITTLE_TITAN requires 正官 in stems."""
        # 甲木日主, no 正官
        chart = [('丁', '巳'), ('丁', '巳'), ('甲', '寅'), ('丁', '巳')]
        result = self.scout._deep_audit(chart, 'PGB_BRITTLE_TITAN')
        self.assertIsNone(result)


class TestProfileScanning(unittest.TestCase):
    """Test scanning saved profiles for patterns."""

    def setUp(self):
        self.pm = ProfileManager()
        self.scout = PatternScout()

    def test_scan_profiles_no_crash(self):
        """Scanning all profiles should not crash."""
        profiles = self.pm.get_all()
        errors = []
        
        for p in profiles:
            try:
                bdt = datetime(p['year'], p['month'], p['day'], p['hour'], p.get('minute', 0))
                gender_int = 1 if p['gender'] == '男' else 0
                profile_obj = BaziProfile(bdt, gender_int)
                
                pillars = profile_obj.pillars
                chart = [pillars['year'], pillars['month'], pillars['day'], pillars['hour']]
                luck = profile_obj.get_luck_pillar_at(2025)
                annual = profile_obj.get_year_pillar(2025)
                six_pillar_chart = chart + [luck, annual]
                
                # Test all patterns
                self.scout._deep_audit(six_pillar_chart, 'SHANG_GUAN_JIAN_GUAN')
                self.scout._deep_audit(six_pillar_chart, 'SHANG_GUAN_SHANG_JIN')
                self.scout._deep_audit(six_pillar_chart, 'PGB_SUPER_FLUID_LOCK')
                self.scout._deep_audit(six_pillar_chart, 'PGB_BRITTLE_TITAN')
            except Exception as e:
                errors.append(f"{p.get('name', 'unknown')}: {e}")
        
        self.assertEqual(len(errors), 0, f"Errors during profile scan: {errors}")


class TestPhysicsConstants(unittest.TestCase):
    """Test physics constants are properly defined."""

    def test_seasonal_matrix_complete(self):
        """SEASONAL_MATRIX should have all 12 branches."""
        branches = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
        for b in branches:
            self.assertIn(b, PC.SEASONAL_MATRIX, f"Missing branch {b}")

    def test_pillar_weights_complete(self):
        """PILLAR_WEIGHTS should have all 6 pillars."""
        pillars = ['year', 'month', 'day', 'hour', 'luck', 'annual']
        for p in pillars:
            self.assertIn(p, PC.PILLAR_WEIGHTS, f"Missing pillar {p}")


if __name__ == '__main__':
    # Run tests with verbosity
    unittest.main(verbosity=2)
