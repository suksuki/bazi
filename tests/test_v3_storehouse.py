
import unittest
import json
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.engine_v88 import EngineV88 as QuantumEngine  # V8.8 Modular

class TestV3Storehouse(unittest.TestCase):
    def setUp(self):
        # 1. Load Params
        self.params = {
            "Physics_Config": {
                "enable_earth_amnesty": False, # V2.9 Flag
                "K_Clash_Robbery": 1.2,
                "w_e_weight": 1.0,
                # ... other params ...
            }
        }
        self.engine = QuantumEngine(self.params)

    def test_chou_wei_clash_wealth_open(self):
        """
        Case 16 Simulation: Bing Fire DM, Chou (Metal Vault/Wealth) vs Wei (Wood Vault/Resource) Clash.
        Should trigger 'Vault Open' for Wealth.
        """
        # Bing Fire DM
        # Pillars: Year=..., Month=Wei, Day=Chou, Hour=...
        # Clash: Month Wei <-> Day Chou
        
        case_data = {
            'id': 'Case16_Sim',
            'day_master': '丙', # Fire
            'bazi': ['XX', '己未', '辛丑', 'XX'], # Wei (Wood Vault), Chou (Metal Vault)
            'wang_shuai': '身弱',
            'gender': '男',
            'physics_sources': {
                'self': {'base': 1.0, 'day_root': 0, 'month_command': 0}, # Weak Self
                'output': {'base': 5.0}, # Strong Output (Earth)
                'wealth': {'base': 4.0}, # Strong Wealth (Metal inside Chou)
                'officer': {'base': 1.0},
                'resource': {'base': 1.0},
                'pillar_energies': [0,0,0,0,0,0,0,0]
            }
        }
        
        # We need to simulate 'Global Energy Map' > 3.0 for Vault to Open
        # Chou starts with Metal. Map needs metal > 3.0.
        # physics_sources['wealth'] is Metal for Bing Fire. It is 4.0.
        # So Metal Vault (Chou) should be ALIVE.
        
        # Wei starts with Wood. Map needs Wood > 3.0.
        # physics_sources['resource'] is Wood. It is 1.0. 
        # So Wood Vault (Wei) should be DEAD (Tomb).
        
        # Expectation:
        # Chou (Metal) -> Open -> Wealth Boost.
        # Wei (Wood) -> Break -> Structure Penalty.
        
        result = self.engine.calculate_energy(case_data)
        
        print("\n=== Narrative Events ===")
        for ev in result['narrative_events']:
            print(f"- [{ev['card_type']}] {ev['title']}: {ev['score_delta']}")
        
        # Assertions
        vault_open_events = [e for e in result['narrative_events'] if 'vault_open' in e['card_type']]
        tomb_break_events = [e for e in result['narrative_events'] if 'tomb_break' in e['card_type']]
        
        self.assertTrue(len(vault_open_events) > 0, "Should satisfy Vault Open condition for Chou (Metal)")
        self.assertTrue(len(tomb_break_events) > 0, "Should satisfy Tomb Break condition for Wei (Wood)")
        
        # Check Bonus Application
        # Metal Raw = 4.0. Bonus = 4.0 * 2.0 = 8.0.
        # Wealth should be huge.
        print(f"Calculated Wealth: {result['wealth']}")
        self.assertGreater(result['wealth'], 8.0, "Wealth should be boosted by vault opening")

if __name__ == '__main__':
    unittest.main()
