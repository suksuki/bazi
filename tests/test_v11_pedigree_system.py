
import unittest
import json
import os
import sys

# Add root directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.trinity.core.conflict_arbitrator import ConflictArbitrator
from core.trinity.core.arbitrator_global_config import ExecutionTier

class TestV11PedigreeSystem(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        manifest_path = "core/logic_manifest.json"
        with open(manifest_path, 'r', encoding='utf-8') as f:
            cls.manifest = json.load(f)
        cls.registry = cls.manifest.get("registry", {})
        cls.modules = cls.manifest.get("modules", {})
        cls.all_items = {**cls.registry, **cls.modules}

    def test_metadata_integrity(self):
        """Verify that all core items have status and origin_trace."""
        ignored_keys = ["PH_CAUSAL_ENTROPY", "PH_SINGULARITY_DETECT"] # These were marked but let's check all
        for key, data in self.all_items.items():
            # Skip items that might be purely structural or incomplete (though most should be complete now)
            with self.subTest(key=key):
                self.assertIn("status", data, f"{key} missing 'status'")
                self.assertEqual(data["status"], "ACTIVE", f"{key} status is not ACTIVE")
                self.assertIn("origin_trace", data, f"{key} missing 'origin_trace'")
                self.assertTrue(len(data["origin_trace"]) > 0, f"{key} origin_trace is empty")

    def test_lifecycle_enforcement(self):
        """Verify ConflictArbitrator filters DEPRECATED rules."""
        mock_registry = {
            "R_ACTIVE": {"priority": 500, "status": "ACTIVE", "layer": "STRUCTURAL"},
            "R_DEPRECATED": {"priority": 600, "status": "DEPRECATED", "layer": "STRUCTURAL"}
        }
        triggered = [{"id": "R_ACTIVE"}, {"id": "R_DEPRECATED"}]
        resolved = ConflictArbitrator.resolve_conflicts(triggered, mock_registry)
        
        resolved_ids = [r["id"] for r in resolved]
        self.assertIn("R_ACTIVE", resolved_ids)
        self.assertNotIn("R_DEPRECATED", resolved_ids)

    def test_pedigree_propagation(self):
        """Verify that origin_trace and fusion_type are propagated by the arbitrator."""
        mock_registry = {
            "R1": {
                "priority": 100, 
                "status": "ACTIVE", 
                "layer": "STRUCTURAL", 
                "origin_trace": ["SOURCE_A"], 
                "fusion_type": "TEST_FUSION"
            }
        }
        triggered = [{"id": "R1"}]
        resolved = ConflictArbitrator.resolve_conflicts(triggered, mock_registry)
        
        self.assertEqual(len(resolved), 1)
        self.assertEqual(resolved[0]["origin_trace"], ["SOURCE_A"])
        self.assertEqual(resolved[0]["fusion_type"], "TEST_FUSION")

    def test_tiered_sorting_safety(self):
        """Verify that grouping by layer follows the ExecutionTier order."""
        # This is more an integration check on how the dispatch bus uses the arbitrator
        # But we can check group_by_layer
        mock_rules = [
            {"id": "L1", "layer": "ENVIRONMENT"},
            {"id": "L2", "layer": "TEMPORAL"},
            {"id": "L3", "layer": "STRUCTURAL"}
        ]
        grouped = ConflictArbitrator.group_by_layer(mock_rules)
        
        self.assertIn("ENVIRONMENT", grouped)
        self.assertIn("TEMPORAL", grouped)
        self.assertIn("STRUCTURAL", grouped)
        self.assertEqual(grouped["ENVIRONMENT"][0]["id"], "L1")
        self.assertEqual(grouped["TEMPORAL"][0]["id"], "L2")

if __name__ == "__main__":
    unittest.main()
