import unittest
from core.quantum import QuantumSimulator

class TestQuantumSimulator(unittest.TestCase):

    def setUp(self):
        # Base Inputs
        self.gods_strong_wealth = {
            "ZhengCai": 80, 
            "PianCai": 40,
            "BiJian": 10,
            "ZhengGuan": 10
        }
        
        self.gods_strong_career = {
            "ZhengGuan": 90,
            "QiSha": 50,
            "ZhengYin": 20
        }
        
        self.empty_flux = {}
        self.high_entropy_flux = {
            "Output": {"entropy": 100},
            "Wealth": {"entropy": 100},
            "Power": {"entropy": 100}
        }
        
        self.no_reactions = []
        self.many_reactions = [{"type": "clash"}, {"type": "combine"}] * 5

    def test_simulate_wealth_dominant(self):
        """
        Test that strong Wealth stars result in high Wealth Expected Value.
        """
        engine = QuantumSimulator(self.gods_strong_wealth, self.no_reactions, self.empty_flux)
        results = engine.simulate()
        
        wealth_res = results["财富 (Wealth)"]
        career_res = results["事业 (Career)"]
        
        # Wealth should be significantly higher than Career in this chart
        self.assertGreater(wealth_res["Expected_Value"], career_res["Expected_Value"])
        
        # Check basic calculation logic
        # Wealth = PianCai(40)*0.9 + ZhengCai(80)*0.8 + ... = 36 + 64 = 100
        # Career = ZhengGuan(10)*0.8 + ... = 8
        self.assertAlmostEqual(wealth_res["Expected_Value"], 100, delta=10) # Delta covers other minor inputs

    def test_simulate_career_dominant(self):
        """
        Test that strong Career stars result in high Career Expected Value.
        """
        engine = QuantumEngine(self.gods_strong_career, self.no_reactions, self.empty_flux)
        results = engine.simulate()
        
        career_res = results["事业 (Career)"]
        self.assertGreater(career_res["Expected_Value"], 80) # 90*0.8 + 50*0.9 = 72+45 = 117 approx

    def test_entropy_increases_uncertainty(self):
        """
        Test that High Flux Entropy increases the 'Uncertainty' (Sigma) of the result.
        """
        # Case 1: Low Entropy
        engine_stable = QuantumEngine(self.gods_strong_wealth, self.no_reactions, self.empty_flux)
        res_stable = engine_stable.simulate()
        sigma_stable = res_stable["财富 (Wealth)"]["Uncertainty"]
        
        # Case 2: High Entropy
        # High entropy flux: Set interactions list which contributes to global_entropy
        # global_entropy = len(interactions) * 5.0
        high_entropy_flux_data = {
            'trace': {
                'interactions': [{'type': 'clash'} for _ in range(10)]  # 10 interactions -> 50 entropy
            }
        }
        engine_chaos = QuantumEngine(self.gods_strong_wealth, self.no_reactions, high_entropy_flux_data)
        res_chaos = engine_chaos.simulate()
        sigma_chaos = res_chaos["财富 (Wealth)"]["Uncertainty"]
        
        # With 10 interactions, global_entropy = 50.0
        # Wealth entropy_weight = 0.2, so contribution = 50 * 0.2 = 10.0
        # Sigma should be: 0.1 (base) + 10.0 (entropy) + 0 (reactions) = 10.1
        # vs stable: 0.1 (base) + 0 (entropy) + 0 (reactions) = 0.1
        self.assertGreater(sigma_chaos, sigma_stable)

    def test_reaction_chaos_impact(self):
        """
        Test that a high number of chemical reactions increases Uncertainty.
        """
        # Case 1: No Reactions
        engine_calm = QuantumEngine(self.gods_strong_wealth, self.no_reactions, self.empty_flux)
        res_calm = engine_calm.simulate()
        
        # Case 2: Many Reactions
        engine_wild = QuantumEngine(self.gods_strong_wealth, self.many_reactions, self.empty_flux)
        res_wild = engine_wild.simulate()
        
        self.assertGreater(res_wild["财富 (Wealth)"]["Uncertainty"], res_calm["财富 (Wealth)"]["Uncertainty"])
