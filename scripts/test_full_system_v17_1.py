
import sys
import os
import unittest
# Use absolute path to ensure project root is found
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, project_root)

from core.registry_loader import RegistryLoader
from controllers.holographic_pattern_controller import HolographicPatternController
from core.physics_engine import compute_energy_flux

class TestFullSystemV17_1(unittest.TestCase):
    """
    Comprehensive System Test for Antigravity V17.1.0 
    (FDS-V1.5.1 Precision Protocol Aligned)
    """
    
    def setUp(self):
        self.loader = RegistryLoader()
        self.controller = HolographicPatternController()
        self.pattern_id = "A-03" # Focus on A-03 as per user request context
        
    def test_01_compliance_check(self):
        """Verify that the A-03 pattern is FDS-V1.5.1 compliant."""
        print("\n[Test 01] Compliance Check")
        pattern = self.loader.get_pattern(self.pattern_id)
        self.assertIsNotNone(pattern)
        
        meta = pattern.get('meta_info', {})
        compliance = meta.get('compliance', 'UNKNOWN')
        version = meta.get('version', 'UNKNOWN')
        
        print(f"Pattern: {pattern.get('name')}")
        print(f"Compliance: {compliance}")
        print(f"Version: {version}")
        
        self.assertEqual(compliance, "FDS-V1.5.1", f"Compliance should be FDS-V1.5.1, but got {compliance}")
        self.assertTrue(version.startswith("2.1"), f"Version should start with 2.1, got {version}")

    def test_02_subpattern_registry(self):
        """Verify that sub-patterns (Vault, Overkill, No Control) are registered."""
        print("\n[Test 02] Sub-Pattern Registry")
        pattern = self.loader.get_pattern(self.pattern_id)
        sub_patterns = pattern.get('sub_patterns_registry', [])
        
        sub_ids = [sp.get('id') for sp in sub_patterns]
        print(f"Registered Sub-Patterns: {sub_ids}")
        
        required_subs = ["SP_A03_STANDARD", "SP_A03_OVERKILL", "SP_A03_NO_CONTROL", "SP_A03_VAULT"]
        for req in required_subs:
            self.assertIn(req, sub_ids, f"Missing sub-pattern: {req}")

    def test_03_vault_routing_logic(self):
        """
        Verify that a chart with vaults (e.g., Jia Day Master with Wei) 
        is correctly routed to SP_A03_VAULT.
        """
        print("\n[Test 03] Vault Routing Logic")
        # Case: Jia Wood Day Master born in Wei Month (Vault), with another Wei.
        # This simulates "Yang Ren in Vault" condition.
        chart = ["甲子", "辛未", "甲未", "甲子"] 
        day_master = "甲"
        
        # Run recognition/calculation
        # Note: We need to use calculate_tensor_projection_from_registry to trigger the routing logic
        result = self.loader.calculate_tensor_projection_from_registry(
            "A-03", chart, day_master
        )
        
        sub_id = result.get('sub_id')
        print(f"Chart: {chart}")
        print(f"Routed Sub-ID: {sub_id}")
        print(f"Projection: {result.get('projection')}")
        
        # Based on the logic "vault_count >= 2" -> SP_A03_VAULT
        # "辛未", "甲未" -> 2 Wei -> 2 Earth Vaults. 
        # Wait, calculate_tensor_projection_from_registry has the routing logic inside.
        
        self.assertEqual(sub_id, "SP_A03_VAULT", f"Should route to SP_A03_VAULT, but got {sub_id}")

    def test_04_precision_physics(self):
        """Verify FDS-V1.5.1 Precision Physics metrics (SAI, Precision Score)."""
        print("\n[Test 04] Precision Physics Metrics")
        chart = ["甲子", "丙寅", "甲申", "乙亥"] # Standard strong wood
        day_master = "甲"
        
        result = self.loader.calculate_tensor_projection_from_registry(
            "A-03", chart, day_master
        )
        
        recognition = result.get('recognition', {})
        print(f"Recognition Result: {recognition}")
        
        self.assertIn('mahalanobis_dist', recognition, "Missing Mahalanobis Distance (FDS-V1.5 requirement)")
        self.assertIn('precision_score', recognition, "Missing Precision Score (FDS-V1.5 requirement)")
        
        # Check standard matching
        if recognition.get('matched'):
            print("✅ Standard Matched")
        else:
            print("⚠️ Not Matched (Expected for this random chart, but structure is valid)")

if __name__ == "__main__":
    unittest.main()
