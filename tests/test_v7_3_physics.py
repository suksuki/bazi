import unittest
from core.quantum_engine import QuantumEngine
from core.config_schema import DEFAULT_FULL_ALGO_PARAMS

class TestV73Physics(unittest.TestCase):
    def setUp(self):
        self.engine = QuantumEngine()
        # Reset to default config before each test
        self.engine.update_full_config(DEFAULT_FULL_ALGO_PARAMS)

    def test_macro_physics_geo(self):
        """Test Geography Impact (Latitude Heat)"""
        print("\n[Macro Physics] Testing Geography Impact...")
        
        # 1. Calculate Baseline Energy (Default Geo)
        chart = {'birth_year': 2000, 'birth_month': 1, 'birth_day': 1, 'birth_hour': 12}
        
        # Force config default
        self.engine.update_full_config(DEFAULT_FULL_ALGO_PARAMS)
        res_base = self.engine.calculate_chart(chart)
        # Let's check Day Master. 2000-1-1 is Wushen? Or something.
        dm_elem = self.engine._get_element(res_base['day_master'])
        
        # Let's peek into internal method for precision
        bazi = res_base['bazi']
        state_base = self.engine._calculate_energy_v7(bazi, dm_elem)
        e_fire_base = state_base.get('Fire', 0)
        print(f"Base Fire Energy: {e_fire_base}")
        
        # 2. Apply South Heat (Heat = 0.5)
        import copy
        new_conf = copy.deepcopy(DEFAULT_FULL_ALGO_PARAMS)
        new_conf['macroPhysics'] = new_conf.get('macroPhysics', {}).copy()
        new_conf['macroPhysics']['latitudeHeat'] = 0.5
        
        self.engine.update_full_config(new_conf)
        
        state_hot = self.engine._calculate_energy_v7(bazi, dm_elem)
        e_fire_hot = state_hot.get('Fire', 0)
        print(f"Hot Fire Energy: {e_fire_hot}")
        
        # Expect ~1.5x increase
        self.assertAlmostEqual(e_fire_hot, e_fire_base * 1.5, delta=0.1)

    def test_vault_physics_opening(self):
        """Test Vault Opening Logic (Chen-Xu Clash)"""
        print("\n[Vault Physics] Testing Treasury Opening...")
        
        import copy
        # Use deepcopy to avoid polluting defaults
        impact_conf = copy.deepcopy(DEFAULT_FULL_ALGO_PARAMS)
        
        impact_conf['interactions']['vaultPhysics']['openBonus'] = 2.0
        impact_conf['interactions']['vaultPhysics']['brokenPenalty'] = 0.5
        impact_conf['interactions']['vaultPhysics']['punishmentOpens'] = False
        # [Fix] Lower threshold so default energy (10.0) counts as Vault
        impact_conf['interactions']['vaultPhysics']['threshold'] = 5.0
        
        self.engine.update_full_config(impact_conf)
        
        # Calculate luck score impact
        # Mocking adapter chart
        adapter_chart = {'year': ('Geng', '辰'), 'month': ('x', 'x'), 'day': ('y', 'y'), 'hour': ('z', 'z')}
        
        # DM=Earth, Water=Wealth. Chen=Water Vault.
        score, details, icon, risk = self.engine.treasury_engine.process_treasury_scoring(
            adapter_chart, '戌', 0.0, 'Strong', 'Earth'
        )
        
        print(f"Vault Open Score: {score}")
        print(f"Details: {details}")
        
        self.assertGreater(score, 10.0, "Should have significant bonus")
        # Check generic open or wealth specific
        self.assertTrue(any("量子隧穿" in d or "爆发" in d or "Open" in str(d) for d in details))

    def test_combo_physics_trine(self):
        """Test Trine (San He) Physics"""
        print("\n[Combo Physics] Testing San He Amplification...")
        
        chart_branches = ['申', '子', '寅', '午'] 
        year_branch = '辰'
        
        # 1. Set Trine Bonus to 3.0
        import copy
        c_conf = copy.deepcopy(DEFAULT_FULL_ALGO_PARAMS)
        c_conf['interactions']['comboPhysics']['trineBonus'] = 3.0
        self.engine.update_full_config(c_conf)
        
        # Use Harmony Engine
        # We need to detect first
        interactions = self.engine.harmony_engine.detect_interactions(chart_branches, year_branch)
        
        # Calculate Score
        # Assume Water is Favorable
        score, details, tags = self.engine.harmony_engine.calculate_harmony_score(interactions, ['Water'])
        
        print(f"Trine Score: {score}")
        print(f"Details: {details}")
        
        self.assertGreater(score, 14.5)
        self.assertTrue(any("三合" in d or "San He" in str(d) for d in details))

if __name__ == '__main__':
    unittest.main()
