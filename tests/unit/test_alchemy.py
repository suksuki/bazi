import unittest
from core.alchemy import AlchemyEngine

class TestAlchemyEngine(unittest.TestCase):

    def setUp(self):
        # Base chart template
        self.base_chart = {
            "year": {"stem": "甲", "branch": "子", "hidden_stems": []},
            "month": {"stem": "丙", "branch": "寅", "hidden_stems": []},
            "day": {"stem": "戊", "branch": "辰", "hidden_stems": []},
            "hour": {"stem": "庚", "branch": "午", "hidden_stems": []}
        }

    def test_stem_combination_bonded_only(self):
        """
        Test Stem Combine (He) without Transformation (Hua).
        Jia (Wood) + Ji (Earth) -> Earth.
        Month is Yin (Wood). Wood conquers Earth, so catalyst fails.
        Expect: Bonded (He)
        """
        chart = self.base_chart.copy()
        chart["year"]["stem"] = "甲"
        chart["month"]["stem"] = "己" 
        chart["month"]["branch"] = "寅" # Wood month, doesn't support Earth transformation
        
        engine = AlchemyEngine(chart)
        reactions = engine.run_reactions()
        
        # Check results
        has_combo = False
        for r in reactions:
            if r['type'] == "Stem Combination" and "甲-己" in r['pair']:
                has_combo = True
                self.assertEqual(r['status'], "Bonded (He)")
                self.assertEqual(r['energy_change'], "0")
        
        self.assertTrue(has_combo, "Should detect Jia-Ji combination")

    def test_stem_combination_transformed(self):
        """
        Test Stem Combine with Transformation.
        Jia + Ji -> Earth.
        Month is Chen (Earth). Supports Earth transformation.
        Expect: Transformed (Hua)
        """
        chart = self.base_chart.copy()
        chart["month"]["branch"] = "辰" # Earth month
        chart["year"]["stem"] = "甲"
        chart["month"]["stem"] = "己"
        
        engine = AlchemyEngine(chart)
        reactions = engine.run_reactions()
        
        found = next((r for r in reactions if "甲-己" in r['pair']), None)
        self.assertIsNotNone(found)
        self.assertEqual(found['status'], "Transformed (Hua)")
        self.assertEqual(found['energy_change'], "+50")

    def test_branch_liu_he(self):
        """
        Test Branch Six Combine.
        Zi (Rat) + Chou (Ox) -> Earth.
        Adjacent Year and Month.
        """
        chart = self.base_chart.copy()
        chart["year"]["branch"] = "子"
        chart["month"]["branch"] = "丑"
        
        engine = AlchemyEngine(chart)
        reactions = engine.run_reactions()
        
        found = next((r for r in reactions if "子-丑" in r['pair'] and r['type'] == "Branch Six Combine (Liu He)"), None)
        self.assertIsNotNone(found)
        self.assertEqual(found['product'], "Tu")

    def test_san_he_bureau(self):
        """
        Test Three Harmony Bureau (San He).
        Shen (Monkey) + Zi (Rat) + Chen (Dragon) -> Water Bureau.
        """
        chart = self.base_chart.copy()
        # Ensure all three exist in chart
        chart["year"]["branch"] = "申"
        chart["month"]["branch"] = "子"
        chart["day"]["branch"] = "辰"
        
        engine = AlchemyEngine(chart)
        reactions = engine.run_reactions()
        
        found = next((r for r in reactions if r['type'] == "Three Harmony Bureau (San He)"), None)
        self.assertIsNotNone(found)
        self.assertEqual(found['product'], "Shui")
        self.assertIn("Massive", found['energy_change'])

    def test_no_reactions(self):
        """
        Test a chart with no obvious interactions.
        甲子 丙寅 戊辰 庚午 (Jia Zi, Bing Yin, Wu Chen, Geng Wu)
        Stems: Jia(Wood), Bing(Fire), Wu(Earth), Geng(Metal) -> No combos
        Branches: Zi(Water), Yin(Wood), Chen(Earth), Wu(Fire) -> No Liu He
        San He: None
        """
        chart = self.base_chart.copy() 
        # Default setUp chart is already pretty scattered, but let's double check logic
        # Zi-Yin, Yin-Chen, Chen-Wu -> No Liu He pairs.
        
        engine = AlchemyEngine(chart)
        reactions = engine.run_reactions()
        
        # Should be empty or at least no combinations
        self.assertEqual(len(reactions), 0)
