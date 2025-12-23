import sys
import os
import json

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from controllers.quantum_lab_controller import QuantumLabController

def test_controller_presets():
    print("🔬 Testing QuantumLabController presets...")
    controller = QuantumLabController()
    
    # Simulate the case loading logic in quantum_lab.py
    cases = []
    paths = [
        "tests/data/integrated_extreme_cases.json",
        "tests/data/oppose_matrix_v21.json",
        "tests/data/quantum_mantra_v93.json", 
        "tests/v14_tuning_matrix.json", 
        "data/calibration_cases.json"
    ]
    for p in paths:
        if os.path.exists(p):
            with open(p, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for c in data:
                    if not any(ex.get('id') == c.get('id') for ex in cases):
                        cases.append(c)
    
    # Check if INTEGRATED_EXTREME_001 is present
    target = next((c for c in cases if c['id'] == "INTEGRATED_EXTREME_001"), None)
    if target:
        print(f"✅ Found case: {target['id']} - {target['description']}")
    else:
        print("❌ INTEGRATED_EXTREME_001 not found in unified presets.")
        return

    # Check if controller can handle it (basic chart calc)
    res = controller.calculate_chart({'birth_year': 1958, 'birth_month': 2, 'birth_day': 4, 'birth_hour': 16, 'birth_minute': 0, 'gender': '男'})
    print(f"✅ Controller chart calc: {res['bazi']} (DM: {res['day_master']})")

if __name__ == "__main__":
    test_controller_presets()
