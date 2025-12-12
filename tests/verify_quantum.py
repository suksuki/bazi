
import sys
import os
import numpy as np

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.quantum import QuantumEngine

def verify_quantum_logic():
    print("--- Verifying Quantum Engine ---")
    
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
    
    print("Initializing QuantumEngine with Flux Data...")
    params = {
        "gods_strength": gods_strength,
        "reactions": reactions,
        "flux_data": flux_data
    }
    
    try:
        q_engine = QuantumEngine(**params)
        print("Initialization Success.")
    except Exception as e:
        print(f"Initialization Failed: {e}")
        return
        
    print("\nCovariance Matrix (Sigma):")
    print(q_engine.sigma)
    
    # Check Diagonal
    # Friend (10 entropy) -> Sigma ~ 15 -> Var ~ 225
    # Output (25 entropy) -> Sigma ~ 30 -> Var ~ 900
    # Wealth (5 entropy) -> Sigma ~ 10 -> Var ~ 100
    # Officer (No data -> 0 entropy) -> Sigma ~ 5 -> Var ~ 25
    diag = np.diag(q_engine.sigma)
    print("\nDiagonal Variances:", diag)
    
    if diag[1] > diag[0] and diag[0] > diag[2]:
        print("✅ Variance scaling matches Entropy inputs (Output > Friend > Wealth)")
    else:
        print("❌ Variance scaling mismatch!")
        
    print("\nRunning Simulation...")
    results = q_engine.simulate(num_simulations=100)
    for k, v in results.items():
        print(f"{k}: Exp={v['Expected_Value']:.1f}, Unc={v['Uncertainty']:.1f}")
        
    print("\nTest Complete.")

if __name__ == "__main__":
    verify_quantum_logic()
