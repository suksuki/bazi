
import json
import sys
from pathlib import Path

def step5_registry():
    print("=" * 70)
    print("🚀 Operation A-03 Cold Restart: Step 5 - The Registry")
    print("=" * 70)
    
    with open("/home/jin/bazi_predict/data/a03_step4_fitting.json", "r") as f:
        fitting = json.load(f)
    
    sub_patterns_registry = {
        "A-03": {
            "name": "Yang Ren Jia Sha",
            "name_cn": "羊刃架杀",
            "version": "1.5.1",
            "sub_patterns": {
                "Standard": {
                    "id": "A-03-A",
                    "description": "标准羊刃架杀 - 高压秩序平衡态",
                    "transfer_matrix": fitting["matrix_a"],
                    "physical_profile": {
                        "primary_axis": "O",
                        "stability": "High",
                        "energy_tier": "Alpha"
                    }
                },
                "Vault": {
                    "id": "A-03-X1",
                    "description": "墓库集聚型羊刃 - 势能深井突破态",
                    "transfer_matrix": fitting["matrix_b"],
                    "physical_profile": {
                        "primary_axis": "E",
                        "mutation_ready": True,
                        "energy_tier": "X1"
                    },
                    "special_operators": ["VAULT_BREAKER", "FLUID_INJECTION"]
                }
            },
            "audit_info": {
                "restart_date": "2025-12-30",
                "protocol": "FDS-V1.5.1 (Deviation Protocol)",
                "status": "SEALED",
                "discarded_clusters": ["X2 (High S Noise)"]
            }
        }
    }
    
    output_path = "/home/jin/bazi_predict/core/subjects/holographic_pattern/registry_a03_v15.json"
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(sub_patterns_registry, f, ensure_ascii=False, indent=2)
        
    print(f"✅ Registry for A-03 sealed at {output_path}")
    
    # Also update the main registry.json for A-03
    main_registry_path = "/home/jin/bazi_predict/core/subjects/holographic_pattern/registry.json"
    try:
        with open(main_registry_path, "r", encoding="utf-8") as f:
            full_registry = json.load(f)
            
        full_registry["patterns"]["A-03"]["sub_patterns"] = sub_patterns_registry["A-03"]["sub_patterns"]
        full_registry["patterns"]["A-03"]["version"] = "1.5.1"
        
        with open(main_registry_path, "w", encoding="utf-8") as f:
            json.dump(full_registry, f, ensure_ascii=False, indent=2)
        print(f"✅ Main registry updated.")
    except Exception as e:
        print(f"Warning: Main registry update failed: {e}")
        
    print("=" * 70)
    print("🎉 Sequence Complete. Antigravity Core Reloaded.")
    print("=" * 70)

if __name__ == "__main__":
    step5_registry()
