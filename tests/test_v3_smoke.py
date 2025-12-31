import unittest
import sys
import os

# Add root to path so we can import core
sys.path.append(os.getcwd())

from core.config import config
from core.config_manager import ConfigManager

class TestV3CoreConfig(unittest.TestCase):
    
    def test_v3_core_config_integrity(self):
        """Verify V3.0 Config Loading and Values"""
        # 1. Check Physics
        self.assertEqual(config.physics.k_factor, 1.0, "Physics K Factor mismatch")
        
        # 2. Check Gating (V2.6 Legacy Values injected via Config)
        self.assertEqual(config.gating.weak_self_limit, 0.45, "E-Gating Threshold mismatch")
        self.assertEqual(config.gating.max_relation_limit, 0.60, "R-Gating Threshold mismatch")
        
        # 3. Check Singularity
        self.assertEqual(config.singularity.deviation_threshold, 1.35, "Singularity Threshold mismatch")

    def test_config_manager_access(self):
        """Verify ConfigManager can access the singleton"""
        cm = ConfigManager()
        self.assertIsNotNone(cm, "ConfigManager failed to instantiate")

    def test_pattern_params_structure(self):
        """Verify Pattern Specific Params are loaded"""
        self.assertIn("purity_threshold", config.patterns.a01_officer)
        self.assertEqual(config.patterns.a01_officer["purity_threshold"], 0.55)

    def test_service_initialization(self):
        """Verify that Simulation and Report services can be initialized"""
        from services.simulation_service import SimulationService
        from services.report_generator_service import ReportGeneratorService
        
        sim_service = SimulationService()
        report_service = ReportGeneratorService()
        
        self.assertIsNotNone(sim_service, "SimulationService failed to initialize")
        self.assertIsNotNone(report_service, "ReportGeneratorService failed to initialize")

if __name__ == '__main__':
    unittest.main()
