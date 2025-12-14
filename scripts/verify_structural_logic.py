
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.engine_v88 import EngineV88 as QuantumEngine  # V8.8 Modular

def test_jobs_2011():
    print("Initializing QuantumEngine...")
    engine = QuantumEngine()
    
    # User Scenario:
    # Year: 2011 (辛卯 - Xin Mao)
    # Analysis: Metal is Favorable, Wood is Unfavorable.
    # Structure: Xin (Metal) sits on Mao (Wood).
    
    year_pillar = "辛卯"
    favorable = ["Metal"] 
    unfavorable = ["Wood"]
    
    print(f"\n--- Testing Case: {year_pillar} (Jobs 2011) ---")
    print(f"Favorable Elements: {favorable}")
    print(f"Unfavorable Elements: {unfavorable}")
    
    # 1. Invoke New V3.0 Logic (returns tuple: score, details)
    score, details = engine.calculate_year_score(year_pillar, favorable, unfavorable)
    
    print(f"\n[V3.0 Result] Calculated Year Score: {score}")
    print(f"[V3.0 Details]: {details}")
    
    # 2. Detailed Breakdown Verification
    stem = year_pillar[0] # Xin
    branch = year_pillar[1] # Mao
    
    print(f"\nBreakdown:")
    print(f"Step 1: Stem '{stem}' (Metal) is Favorable? Yes (+10).")
    print(f"Step 2: Branch '{branch}' (Wood) is Favorable? No (Unfavorable -> -10).")
    print(f"Step 3: Weighted Base = (10 * 0.4) + (-10 * 0.6) = 4.0 - 6.0 = -2.0")
    print(f"Step 4: Structural Check (Cut Feet)")
    print(f"        Good Stem (Metal) sits on Bad Branch (Wood) -> Penalty -5.0")
    print(f"Step 5: Final Score = -2.0 - 5.0 = -7.0")
    
    if score == -7.0:
        print("\nSUCCESS: The algorithm correctly identifies the 'Cut Feet' structure and reverses the verdict to Negative (Ominous).")
    else:
        print(f"\nFAILURE: Expected -7.0, got {score}")

if __name__ == "__main__":
    test_jobs_2011()
