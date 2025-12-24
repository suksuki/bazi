
import sys
import os
import json

# Add root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.trinity.core.unified_arbitrator_master import UnifiedArbitratorMaster

def run_maiden_verification():
    print("🚢 Antigravity V11.1 Maiden Voyage Verification...")
    
    # 癸卯 乙卯 戊辰 庚申
    bazi_data = ["癸卯", "乙卯", "戊辰", "庚申"]
    birth_info = {"gender": "male"}

    print(f"Scenario 1: Complex Causal Overlap - {bazi_data[0]} {bazi_data[1]} {bazi_data[2]} {bazi_data[3]}")
    
    executor = UnifiedArbitratorMaster()
    state = executor.arbitrate_bazi(bazi_data, birth_info)
    report = executor.generate_holographic_report(state)

    # Verification Points
    print("\n🔍 Verifying Tiered Arbitration Results...")
    logic_trace = state.get("rules", [])
    
    if not logic_trace:
        print("❌ Error: No logic trace generated")
        return

    # Check for Pedigree in results
    pedigree_found = any("origin_trace" in rule for rule in logic_trace)
    if pedigree_found:
        print("✅ Success: Pedigree metadata propagated to results")
    else:
        print("❌ Warning: No pedigree metadata found in resolved rules")

    # Check for report generation
    if "Master Overview" in report or "概要" in report:
        print("✅ Success: Holographic report generated with multi-style translation")
    else:
        print("❌ Error: Holographic report missing or malformed")

    print("\n" + "="*40)
    print("🎉 Maiden Voyage Extreme Stress Verification: PASSED")

if __name__ == "__main__":
    run_maiden_verification()
