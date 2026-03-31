
import sys
import os
import numpy as np

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.quantum import QuantumSimulator

def verify_quantum_logic():
    print("--- Verifying Quantum Simulator ---")
    
    # Mock Data
    gods_strength = {
        "Friend (Bi/Jie)": 40,
        "Output (Shi/Shang)": 60,
        "Wealth (Cai)": 30,
        "Officer (Guan/Sha)": 20,
        "Resource (Yin)": 80
    }
    
    reactions = [{"type": "Clash", "desc": "Test Clash"}]
    
    flux_data = {
        "比劫 (Friends/Self)": {"entropy": 10.0, "score": 40},
        "食伤 (Talent/Output)": {"entropy": 25.0, "score": 60},
        "财星 (Wealth/Wife)": {"entropy": 5.0, "score": 30},
    }
    
    print("Initializing QuantumSimulator with Flux Data...")
    # QuantumSimulator expects: (chart_gods, reactions, flux_data=None, wuxing_engine=None)
    try:
        q_engine = QuantumSimulator(gods_strength, reactions, flux_data=flux_data)
        print("Initialization Success.")
    except Exception as e:
        print(f"Initialization Failed: {e}")
        return
        
    # Note: QuantumSimulator.simulate() doesn't have num_simulations parameter
    # and doesn't expose sigma directly. The simulate() method returns results directly.
    print("\nRunning Simulation...")
    results = q_engine.simulate()
    for k, v in results.items():
        print(f"{k}: Exp={v['Expected_Value']:.1f}, Unc={v['Uncertainty']:.1f}")
        
    print("\nTest Complete.")

if __name__ == "__main__":
    verify_quantum_logic()
