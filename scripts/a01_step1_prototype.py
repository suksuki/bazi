import json
import os
import time

# ==========================================
# A-01 Step 1: Prototype Definition (Direct Officer)
# ==========================================

OUTPUT_FILE = "scripts/a01_step1_prototype.json"

prototype = {
  "pattern_id": "A-01",
  "meta_info": { 
      "category": "POWER (权柄)",
      "chinese_name": "正官格",
      "display_name": "Direct Officer (The Judge)"
  },
  "axioms": {
    "reaction_type": "CRYSTALLIZATION", # 结晶
    "stability_mode": "STATIC_HIGH"     # 高静态稳定性
  },
  "init_matrix_logic": {
    "E_row": {
      "Day_Master": 1.2,      # [门控预设] 身必须旺
      "Resource": 1.0         # 印星护官护身
    },
    "O_row": {
      "Direct_Officer": 1.5,  # [核心] 正官
      "Seven_Killings": -1.0, # [提纯] 官杀混杂是杂质
      "Hurting_Officer": -2.0 # [天敌] 伤官见官，格局破碎
    },
    "M_row": {
      "Direct_Wealth": 0.8,   # 财生官 (良性循环)
      "Indirect_Wealth": 0.5
    },
    "S_row": {
      "Clash": -0.5           # 晶体怕冲
    }
  }
}

print(f"🏛️  [A-01 PROTOTYPE] Defining Crystalline Order physics...")
with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    json.dump(prototype, f, indent=2, ensure_ascii=False)
print(f"✅ Prototype saved to {OUTPUT_FILE}")
