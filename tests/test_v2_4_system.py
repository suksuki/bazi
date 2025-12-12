
import pytest
import json
import os
from datetime import date
from core.calculator import BaziCalculator
from core.flux import FluxEngine
from core.quantum_engine import QuantumEngine

# Setup Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARAMS_PATH = os.path.join(BASE_DIR, 'data/golden_parameters.json')

class TestQuantumV24System:
    """
    Comprehensive Integration Test for Quantum Bazi V2.4
    """

    def setup_method(self):
        # Load Production Parameters
        with open(PARAMS_PATH, 'r') as f:
            self.gp = json.load(f)
            
        # Map to Engine Keys if needed (Simulating Dashboard Logic)
        self.params = {
            "w_career_officer": self.gp['macro_weights_w']['W_Career_Officer'], # 0.8
            "k_control": self.gp['conflict_and_conversion_k_factors']['K_Control_Conversion'], # 0.55
            "k_mutiny": self.gp['conflict_and_conversion_k_factors']['K_Mutiny_Betrayal'], # 1.8
            "k_capture": 0.40
        }

    def test_01_calculator_types(self):
        """Verify BaziCalculator returns PURE STRINGS, not Objects."""
        # Date: 2024-02-10 (Jia Chen Year)
        c = BaziCalculator(2024, 2, 10, 12)
        chart = c.get_chart()
        
        # Check Year Pillar (Jia Chen)
        assert chart['year']['stem'] == "甲", f"Expected '甲', got {type(chart['year']['stem'])}"
        assert isinstance(chart['year']['stem'], str)
        assert isinstance(chart['year']['branch'], str)
        assert isinstance(chart['year']['hidden_stems'][0], str)
        
    def test_02_flux_engine_energy(self):
        """Verify FluxEngine initializes particles and has non-zero energy."""
        c = BaziCalculator(2024, 2, 10, 12)
        chart = c.get_chart()
        
        flux = FluxEngine(chart)
        # Check particles count (4 pillars * 2 = 8 particles)
        assert len(flux.particles) >= 8
        
        # Compute Energy
        res = flux.compute_energy_state()
        
        # Check Ten Gods exist
        assert 'BiJian' in res or 'ten_gods' in res
        
        # Check Amplitude
        p0 = flux.particles[0]
        assert p0.wave.amplitude > 0.0, "Particle amplitude should be initialized > 0"

    def test_03_quantum_logic_mutiny(self):
        """
        Verify Case 13 Logic: Shang Guan Jian Guan (Mutiny).
        Mocking Data to trigger Mutiny.
        """
        # Weak Self (-6.0), Strong Output (6.0), Strong Officer (5.0)
        case_data = {
            'id': 13,
            'wang_shuai': '身弱',
            'physics_sources': {
                'self': {'stem_support': -6.0}, # Weak
                'output': {'base': 6.0},        # Strong Output
                'officer': {'base': 5.0},       # Strong Officer
                'wealth': {'base': 2.0},
                'resource': {'base': 0.0}
            }
        }
        
        qe = QuantumEngine(self.params)
        res = qe.calculate_energy(case_data)
        
        # Assert Punishment
        # Mutiny Penalty: min(6, 5) * 1.8 = 5 * 1.8 = 9.0 penalty
        # Base: (5*0.8 + -6*0.2) = 4 - 1.2 = 2.8
        # Expected: 2.8 - 9.0 = -6.2
        
        print(f"Mutiny Prediction: {res['career']}")
        assert res['career'] < 0.0, "Career score should be negative due to Mutiny"
        assert "伤官见官" in res['desc'], "Narrative must trigger Mutiny warning"

    def test_04_quantum_logic_control(self):
        """
        Verify Case 1 Logic: Control Success (Shi Shen Zhi Sha).
        """
        # Strong Self (5.0), Strong Output (5.0), Strong Officer (5.0)
        case_data = {
            'id': 1,
            'wang_shuai': '身旺',
            'physics_sources': {
                'self': {'stem_support': 5.0}, 
                'output': {'base': 5.0},
                'officer': {'base': 5.0},
                'wealth': {'base': 0.0},
                'resource': {'base': 0.0}
            }
        }
        
        qe = QuantumEngine(self.params)
        res = qe.calculate_energy(case_data)
        
        # Calculation:
        # Base: 5*0.8 + 5*0.2 = 5.0
        # Control Bonus: min(5,5) * 0.55 = 2.75
        # Total: ~7.75
        assert res['career'] > 7.0, "Career score should be high due to Control Success"
        assert "能量转化" in res['desc'] or "制杀" in res['desc']

if __name__ == "__main__":
    # Manual run helper
    t = TestQuantumV24System()
    t.setup_method()
    t.test_01_calculator_types()
    t.test_03_quantum_logic_mutiny()
    print("Manual Checks Passed")
