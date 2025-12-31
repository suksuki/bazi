import json
import os

# ==========================================
# B-02 Step 1: Prototype Definition (Hurting Officer)
# ==========================================

OUTPUT_FILE = "scripts/b02_step1_prototype_v151.json"

prototype = {
  "pattern_id": "B-02",
  "meta_info": { 
      "category": "TALENT",       # [Compliance] Enum
      "chinese_name": "伤官格",     # [Compliance] Pure Chinese
      "display_name": "Hurting Officer" # [Compliance] Pure English
  },
  "physics_kernel_prototype": {
    "axioms": {
      "reaction_type": "DISSIPATIVE_STRUCTURE", # 耗散结构
      "stability_mode": "DYNAMIC_EQUILIBRIUM"   # 动态平衡
    },
    "init_matrix_logic": {
      "E_row": {
        "Day_Master": 1.2,      # [前提] 身旺才能泄秀
        "Resource": 0.8         # 印星制伤护身
      },
      "O_row": {
        "Hurting_Officer": 2.0, # [主气] 才华/输出
        "Eating_God": 1.0       # 食神辅助
      },
      "S_row": {
        "Hurting_Officer": 2.5, # [冲力] 伤官即压力/变革
        "Direct_Officer": 3.0,  # [爆炸] 伤官见官 = 剧烈S轴响应
        "Seven_Killings": 1.5
      },
      "M_row": {
        "Direct_Wealth": 1.5,   # [通关] 伤官生财 (转化 S -> M)
        "Indirect_Wealth": 1.2
      },
      "R_row": {
        "Friend": 0.5,          # 比劫生伤官
        "Direct_Officer": -1.0  # 叛逆，排斥体制内关系
      }
    }
  }
}

print(f"🌪️  [B-02 PROTOTYPE V1.5.1] Defining Dissipative Structure (Hurting Officer)...")
with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    json.dump(prototype, f, indent=2, ensure_ascii=False)
print(f"✅ Prototype saved to {OUTPUT_FILE}")
