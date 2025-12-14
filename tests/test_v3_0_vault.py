import sys
import os
import json

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.engine_v88 import EngineV88 as QuantumEngine  # V8.8 Modular

def test_case_16_vault_opening():
    print("🚀 Starting V3.0 Quantum Vault Verification: Case 16...")
    
    # 1. Load Golden Parameters (simulated default)
    params = {
        "global_physics": {
            "K_Clash_Robbery": 1.2,
            "enable_structural_clash": True,
            "enable_mediation_exemption": True
        }
    }
    
    engine = QuantumEngine(params)
    
    # 2. Mock Case 16 Data
    # 癸 (Water) Day Master born in 丑 (Ox) month or day, interacting with 未 (Goat).
    # Need to ensure Metal (in Chou) and Wood (in Wei) are > 3.0 for "Vault" status.
    
    case_16 = {
        "id": 16,
        "day_master": "癸",
        "gender": "男",
        "bazi": ["辛未", "辛丑", "癸丑", "乙卯"], # Example: Metal/Wood revealed
        "wang_shuai": "身弱",
        "physics_sources": {
            "self": {"base": 2.0, "day_root": 1.0, "other_roots": 0.5}, # Weak Water
            "output": {"base": 4.5}, # Wood (lives in Wei) -> Strong (>3.0)
            "wealth": {"base": 1.5}, # Fire
            "officer": {"base": 4.5}, # Earth (Unused in Vault check directly, but context)
            "resource": {"base": 5.0}, # Metal (lives in Chou) -> Strong (>3.0)
        }
    }
    
    # Note: element_map construction in calculate_energy:
    # DM = Water.
    # Self = Water (2.0 + ...)
    # Output = Wood (4.5) -> Corresponds to '未' (Wood Vault)
    # Wealth = Fire (1.5)
    # Officer = Earth
    # Resource = Metal (5.0) -> Corresponds to '丑' (Metal Vault)
    
    # So: 
    # Metal Energy ~ 5.0 (> 3.0) -> 丑 is VAULT
    # Wood Energy ~ 4.5 (> 3.0) -> 未 is VAULT
    
    # 3. Calculate
    result = engine.calculate_energy(case_16)
    
    # 4. Verify Results
    events = result['narrative_events']
    
    print(f"\nNarrative Events Found: {len(events)}")
    vault_opens = [e for e in events if e['card_type'] == 'vault_open']
    tomb_breaks = [e for e in events if e['card_type'] == 'tomb_break']
    
    print(f"Vault Opens: {len(vault_opens)}")
    print(f"Tomb Breaks: {len(tomb_breaks)}")
    
    for e in vault_opens:
        print(f"  - [SUCCESS] {e['title']}: {e['desc']} ({e['score_delta']})")
        
    for e in tomb_breaks:
        print(f"  - [FAIL] {e['title']}: {e['desc']} ({e['score_delta']})")

    # Check Wealth Score
    print(f"\nFinal Scores:")
    print(f"Career: {result['career']}")
    print(f"Wealth: {result['wealth']}")
    print(f"Relationship: {result['relationship']}")
    
    if len(vault_opens) >= 2: # Expecting both Chou and Wei to open
        print("\n✅ TEST PASSED: Quantum Tunneling Successful! Case 16 Saved!")
    elif len(vault_opens) > 0:
        print("\n⚠️ TEST PARTIAL: Only some vaults opened.")
    else:
        print("\n❌ TEST FAILED: No vaults opened.")

if __name__ == "__main__":
    test_case_16_vault_opening()
