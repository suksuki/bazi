import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.engine_v88 import EngineV88 as QuantumEngine  # V8.8 Modular
from core.constants import GRAVE_TREASURY_CONFIG

def test_v3_structure():
    print("Initializing QuantumEngine...")
    qe = QuantumEngine()
    
    print("\nTesting Vault Mapping (Phase 1.1)...")
    dragon = qe.VAULT_MAPPING.get('辰')
    print(f"Dragon (辰): {dragon}")
    
    expect_dragon_type = 'water_tomb'
    if dragon and dragon['type'] == expect_dragon_type:
        print("✅ Dragon is correctly identified as Water Tomb.")
    else:
        print(f"❌ Error: Dragon type mismatch. Expected {expect_dragon_type}, got {dragon.get('type') if dragon else 'None'}")

    print("\nTesting Hidden Stems (Phase 1.2)...")
    stems = qe.get_hidden_stems('辰')
    print(f"Dragon Hidden Stems: {stems}")
    
    # Check structure
    if 'main' in stems and 'residual' in stems and 'tomb' in stems:
         print("✅ Hidden Stems structure is correct (main/residual/tomb).")
         if stems['tomb'] == '癸':
             print("✅ Tomb Gas (癸) confirmed.")
         else:
             print(f"❌ Error: Tomb Gas mismatch. Expected 癸, got {stems['tomb']}")
    elif 'hidden' in stems: # Fallback check if I implemented it differently in map
        print(f"⚠️ Warning: Using list based hidden stems: {stems['hidden']}")
        # In my implementation of constants.py for Chen, I put 'stems': {'main':..., 'residual':..., 'tomb':...}
        # But for HIDDEN_STEMS_MAP, I assigned GRAVE_TREASURY_CONFIG['辰']['stems']. So it should be the dict.
        pass
    else:
        print("❌ Error: Invalid Hidden Stems structure.")

if __name__ == "__main__":
    test_v3_structure()
