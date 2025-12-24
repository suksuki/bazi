import unittest
import json
import os
import sys

# Ensure core is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.logic_registry import LogicRegistry

class TestLogicHierarchy(unittest.TestCase):
    def setUp(self):
        self.registry = LogicRegistry()
        self.manifest_path = os.path.join(os.path.dirname(__file__), '../core/logic_manifest.json')
        with open(self.manifest_path, 'r', encoding='utf-8') as f:
            self.manifest_data = json.load(f)

    def test_themes_exist(self):
        """Verify that the themes registry exists and is not empty."""
        themes = self.registry.get_themes()
        self.assertIsInstance(themes, dict)
        self.assertGreater(len(themes), 0)
        self.assertIn('BAZI_FUNDAMENTAL', themes)

    def test_module_theme_filtering(self):
        """Verify that modules can be filtered by theme."""
        # Get modules for BAZI_FUNDAMENTAL
        fundamental_modules = self.registry.get_active_modules(theme_id='BAZI_FUNDAMENTAL')
        self.assertGreater(len(fundamental_modules), 0)
        for m in fundamental_modules:
            self.assertEqual(m.get('theme'), 'BAZI_FUNDAMENTAL')

        # Get modules for a non-existent theme (should be empty)
        empty_modules = self.registry.get_active_modules(theme_id='NON_EXISTENT_THEME')
        self.assertEqual(len(empty_modules), 0)

    def test_manifest_integrity_all_modules_have_theme(self):
        """Regression check: Every module in the manifest MUST have a theme field."""
        modules = self.manifest_data.get('modules', {})
        for m_id, m_data in modules.items():
            self.assertIn('theme', m_data, f"Module {m_id} is missing 'theme' field.")
            self.assertIsNotNone(m_data['theme'], f"Module {m_id} has null theme.")

    def test_manifest_integrity_themes_are_valid(self):
        """Regression check: Every module's theme must exist in the top-level themes registry."""
        themes_registry = self.manifest_data.get('themes', {})
        modules = self.manifest_data.get('modules', {})
        for m_id, m_data in modules.items():
            theme_id = m_data.get('theme')
            self.assertIn(theme_id, themes_registry, f"Module {m_id} references unknown theme: {theme_id}")

    def test_base_app_module_exists(self):
        """Verify that the new MOD_18_BASE_APP module exists and is correctly categorized."""
        modules = self.registry.get_active_modules()
        module_ids = [m['id'] for m in modules]
        self.assertIn('MOD_18_BASE_APP', module_ids)
        
        base_app = next(m for m in modules if m['id'] == 'MOD_18_BASE_APP')
        self.assertEqual(base_app.get('theme'), 'BAZI_FUNDAMENTAL')
        self.assertIn('PH_DESTINY_TRANSLATION', base_app.get('linked_rules', []))

if __name__ == '__main__':
    unittest.main()
