import json
import os
import time

# ==========================================
# A-03 Step 1: Physical Prototype Definition
# ==========================================

OUTPUT_DIR = "core/subjects/holographic_pattern/mining_cache"
PROTOTYPE_FILE = os.path.join(OUTPUT_DIR, "a03_step1_prototype.json")

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

print(f"☢️  [Step 1 START] Defining A-03 Physics Prototype...")
print(f"⚔️  Pattern: Yang Ren Jia Sha (The Blade & The Killer)")
print(f"🔥 Prototype: Tokamak Fusion Reactor")

# 1. 定义物理公理 (Axioms)
axioms = {
    "reaction_type": "FUSION (核聚变)",
    "stability_mode": "DYNAMIC (恐怖平衡)",
    "critical_mass": {
        "E_threshold": 0.6, # 身旺 (Nuclear Fuel)
        "S_threshold": 0.5  # 杀旺 (Magnetic Confinement)
    },
    "exclusion_principle": [
        "Eating_God (Cooling Effect)", # 食神泄气，导致聚变熄火
        "Direct_Resource (Damping)"    # 过多的印会化解七杀，导致磁场失效
    ]
}

# 2. 定义初始矩阵逻辑 (Initial Matrix Logic)
# 这一步将 10神 映射到 5D 张量。
# A-03 的特殊性在于：O (Output/Power) 不是由 Output Star 直接贡献，
# 而是由 E (Yang Ren) 和 S (Seven Killings) 的交互产生的。
init_matrix_logic = {
    "E_row": {
        "Yang_Ren": 1.5,       # [核心] 核燃料。羊刃就是E轴本体。
        "Day_Master": 1.0,     # 日主本气
        "Friend": 0.5          # 比肩只是辅助
    },
    "S_row": {
        "Seven_Killings": 1.5, # [核心] 强磁场约束。
        "Direct_Officer": 0.5, # 正官力度太柔，压不住羊刃
        "Clash": 1.0           # 允许冲战（动能）
    },
    "O_row": {
        # [聚变产出] 
        # 只要成格，羊刃就是权力，七杀就是威望。
        # 这里的权重代表：越旺的羊刃/七杀，转化出的 O 越高。
        "Yang_Ren": 0.8,       
        "Seven_Killings": 0.8,
        
        # [冷却剂]
        "Eating_God": -0.5,    # 忌：食神会软化对抗
        "Hurting_Officer": -0.3 # 忌：伤官会混杂
    },
    "M_row": {
        # [风险]
        "Yang_Ren": -1.5,      # 默认：羊刃是劫财，破财之神
        "Seven_Killings": 0.5, # 杀略微护财
        "Wealth": 1.0          # 原局有财当然好，但A-03不靠财星发家，靠的是“抢”
    },
    "R_row": {
        "Combination": 0.5,    # 聚变堆需要封闭，不太需要外部连接
        "Friend": 0.2
    }
}

# 3. 封装原型
prototype_data = {
    "pattern_id": "A-03",
    "pattern_name": "Yang Ren Jia Sha",
    "step": "Step 1 - Prototype Definition",
    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    "physics_prototype": "Tokamak Fusion Reactor",
    "axioms": axioms,
    "init_matrix_logic": init_matrix_logic,
    "mining_filters_preview": {
        "L1": "Month_Branch=Yang_Ren OR (Stems has Yang_Ren AND Root)",
        "L2": "Seven_Killings > 0.4 (High Pressure)",
        "L3": "Day_Master > 0.5 (Strong Self)"
    }
}

# 4. 物理写入
with open(PROTOTYPE_FILE, 'w', encoding='utf-8') as f:
    json.dump(prototype_data, f, indent=2, ensure_ascii=False)

print(f"💾 Prototype Defined: {os.path.abspath(PROTOTYPE_FILE)}")
print(f"🔒 Step 1 Locked. Ready to ignite the plasma (Step 2 Mining).")
