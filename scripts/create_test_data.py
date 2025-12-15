"""
Create Test Data Files for V9.5 Tests
=====================================
This script creates the required test data files:
- data/golden_parameters.json
- data/era_constants.json
"""

import os
import json

# Get project root directory
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')

# Create data directory if it doesn't exist
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)
elif not os.path.isdir(DATA_DIR):
    # If it exists but is a file, remove it and create directory
    os.remove(DATA_DIR)
    os.makedirs(DATA_DIR)

# 1. Create golden_parameters.json
golden_params = {
    "global_physics": {
        "w_e_weight": 1.0,
        "f_yy_correction": 1.1
    },
    "weights": {
        "W_Career_Officer": 0.8,
        "W_Career_Resource": 0.1,
        "W_Career_Output": 0.0,
        "W_Wealth_Cai": 0.6,
        "W_Wealth_Output": 0.4,
        "W_Rel_Spouse": 0.35,
        "W_Rel_Self": 0.20,
        "W_Rel_Output": 0.15
    },
    "macro_weights_w": {
        "W_Career_Officer": 0.8,
        "W_Career_Resource": 0.1,
        "W_Career_Output": 0.0,
        "W_Wealth_Cai": 0.6,
        "W_Wealth_Output": 0.4
    },
    "relationship_weights": {
        "W_Rel_Spouse": 0.35,
        "W_Rel_Self": 0.20,
        "W_Rel_Output": 0.15
    },
    "k_factors": {
        "K_Control_Conversion": 0.55,
        "K_Buffer_Defense": 0.40,
        "K_Clash_Robbery": 1.2,
        "K_Mutiny_Betrayal": 1.8,
        "K_Leak_Drain": 0.87,
        "K_Pressure_Attack": 1.0,
        "K_Burden_Wealth": 1.0,
        "K_Broken_Collapse": 1.5,
        "K_Capture_Wealth": 0.40
    },
    "conflict_and_conversion_k_factors": {
        "K_Control_Conversion": 0.55,
        "K_Buffer_Defense": 0.40,
        "K_Clash_Robbery": 1.2,
        "K_Mutiny_Betrayal": 1.8,
        "K_Leak_Drain": 0.87,
        "K_Pressure_Attack": 1.0,
        "K_Burden_Wealth": 1.0,
        "K_Broken_Collapse": 1.5,
        "K_Capture_Wealth": 0.40
    },
    "logic_switches": {
        "enable_mediation_exemption": True,
        "enable_structural_clash": True
    }
}

# 2. Create era_constants.json (Period 9 - Fire Era)
era_constants = {
    "period": 9,
    "era_element": "fire",
    "description": "Period 9 (2024-2043) - Fire Era",
    "physics_multipliers": {
        "fire": 1.25,
        "earth": 1.0,
        "metal": 0.9,
        "water": 0.85,
        "wood": 1.0
    }
}

# Write files
golden_params_path = os.path.join(DATA_DIR, 'golden_parameters.json')
era_constants_path = os.path.join(DATA_DIR, 'era_constants.json')

with open(golden_params_path, 'w', encoding='utf-8') as f:
    json.dump(golden_params, f, indent=2, ensure_ascii=False)

with open(era_constants_path, 'w', encoding='utf-8') as f:
    json.dump(era_constants, f, indent=2, ensure_ascii=False)

print(f"✅ Created {golden_params_path}")
print(f"✅ Created {era_constants_path}")
print("✅ Test data files created successfully!")

