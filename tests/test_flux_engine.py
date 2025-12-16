import unittest

from core.flux import FluxEngine
from utils.constants_manager import get_constants


def _build_minimal_chart():
    """
    Build a minimal chart dict with all four pillars.
    Uses common GanZhi so Kernel lookups remain valid.
    """
    return {
        "year": {"stem": "甲", "branch": "子"},
        "month": {"stem": "乙", "branch": "丑"},
        "day": {"stem": "丙", "branch": "寅"},
        "hour": {"stem": "丁", "branch": "卯"},
    }


class TestFluxEngineCore(unittest.TestCase):
    def setUp(self):
        self.consts = get_constants()
        self.chart = _build_minimal_chart()
        self.engine = FluxEngine(self.chart)

    def test_initial_particles_built(self):
        """Engine should build stem/branch particles for four pillars."""
        # Expect 8 particles (4 stems + 4 branches) in the basic chart
        self.assertGreaterEqual(len(self.engine.particles), 8)

    def test_spectrum_contains_all_elements(self):
        """compute_energy_state should produce spectrum with all five elements."""
        trace = self.engine.compute_energy_state()
        spectrum = trace.get("spectrum", {})
        for elem in self.consts.FIVE_ELEMENTS:
            self.assertIn(elem, spectrum, f"Missing element {elem} in spectrum")
            self.assertIsInstance(spectrum[elem], float)

    def test_environment_injection_adds_particles(self):
        """set_environment should inject additional particles for DaYun/LiuNian."""
        base_count = len(self.engine.particles)
        self.engine.set_environment(
            da_yun={"stem": "戊", "branch": "辰"},
            liu_nian={"stem": "己", "branch": "巳"},
        )
        self.assertGreater(len(self.engine.particles), base_count)


if __name__ == "__main__":
    unittest.main()

