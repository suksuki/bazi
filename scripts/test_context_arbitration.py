
import sys
import os
import json

# Add root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.trinity.core.unified_arbitrator_master import UnifiedArbitratorMaster
from core.trinity.core.nexus.context import ArbitrationScenario, ContextInjector

def test_scenario_weighting():
    print("📊 Testing Antigravity V11.1 Context-Aware Arbitration Weighting...")
    
    executor = UnifiedArbitratorMaster()
    bazi_data = ["癸卯", "乙卯", "戊辰", "庚申"]
    birth_info = {"gender": "male"}
    
    # Test 1: General Scenario
    print("\n--- Test 1: GENERAL Scenario ---")
    ctx_general = {'scenario': 'GENERAL'}
    state_gen = executor.arbitrate_bazi(bazi_data, birth_info, ctx_general)
    rules_gen = state_gen.get("rules", [])
    
    # Find PH_WEALTH_PERMEABILITY in rules
    wealth_rule_gen = next((r for r in rules_gen if r['id'] == "PH_WEALTH_PERMEABILITY"), None)
    if wealth_rule_gen:
        print(f"PH_WEALTH_PERMEABILITY Priority (GENERAL): {wealth_rule_gen['priority']}")
    
    # Test 2: Wealth Scenario
    print("\n--- Test 2: WEALTH Scenario ---")
    ctx_wealth = {'scenario': 'WEALTH'}
    state_wealth = executor.arbitrate_bazi(bazi_data, birth_info, ctx_wealth)
    rules_wealth = state_wealth.get("rules", [])
    
    wealth_rule_wealth = next((r for r in rules_wealth if r['id'] == "PH_WEALTH_PERMEABILITY"), None)
    if wealth_rule_wealth:
        print(f"PH_WEALTH_PERMEABILITY Priority (WEALTH): {wealth_rule_wealth['priority']}")
        
    # Verification
    if wealth_rule_wealth and wealth_rule_gen:
        if wealth_rule_wealth['priority'] > wealth_rule_gen['priority']:
            print("\n✅ Success: Scenario-based weighting confirmed (+100 boost applied)")
        else:
            print("\n❌ Error: Scenario boost not applied")
    else:
        print("\n❌ Error: Required rules not triggered in test case")

if __name__ == "__main__":
    test_scenario_weighting()
