import json
import os
import time

# ==========================================
# D-02 Step 1: Physical Prototype Definition
# ==========================================

OUTPUT_DIR = "core/subjects/holographic_pattern/mining_cache"
PROTOTYPE_FILE = os.path.join(OUTPUT_DIR, "d02_step1_prototype.json")

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

print(f"💸 [Step 1 START] Defining D-02 Physics Prototype...")
print(f"🌊 Pattern: Indirect Wealth (The Hunter / The Venture)")
print(f"🔥 Prototype: Dynamic Flow / Turbulence Generator")

# 1. 定义物理公理 (Axioms)
axioms = {
    "reaction_type": "EXCHANGE (交换/流通)",
    "stability_mode": "DYNAMIC (动态平衡)",
    "critical_mass": {
        "E_threshold": 0.5, # 身旺 (Control)
        "M_threshold": 0.55 # 财旺 (Market)
    },
    "leverage_exception": [
        "Rob_Wealth (Cost of Business)", # 比劫视为经营成本，而非纯粹损失
        "Seven_Killings (Risk Premium)"  # 七杀视为风险溢价
    ]
}

# 2. 定义初始矩阵逻辑 (Initial Matrix Logic)
# 这一步将 10神 映射到 5D 张量。
# D-02 允许 高 R (Leverage) 和 高 S (Risk) 存在
init_matrix_logic = {
    "E_row": {
        "Day_Master": 1.2,      # [核心] 身旺是底线。控制流动的钱需要更高能量。
        "Resource": 0.8         # 印星护身
    },
    "M_row": {
        "Indirect_Wealth": 1.5, # [主气] 偏财
        "Direct_Wealth": 0.5,   # 正财也可混入，但效率低
        "Rob_Wealth": -0.2      # [关键差异] 劫财在D-01是-1.0(抢劫)，在D-02是-0.2(成本)。
                                # 偏财格允许"分钱给兄弟"，只要总盘子做大。
    },
    "S_row": {
        "Seven_Killings": 0.5,  # [风险] 偏财自带风险，甚至可能利用杀来护财
        "Clash": 0.8            # [动荡] 冲往往代表财富的转移机会
    },
    "O_row": {
        "Eating_God": 1.0,      # 食神生偏财 (技术/策略)
        "Hurting_Officer": 1.2  # [差异] 伤官生偏财比生正财更有效 (胆略/营销)
    },
    "R_row": {
        "Friend": 0.5,
        "Rob_Wealth": 1.0       # 朋友/合伙人。虽然在M轴有轻微负分，但在R轴是高权重。
                                # 这为后续识别 "Syndicate" 留出了接口。
    }
}

# 3. 封装原型
prototype_data = {
    "pattern_id": "D-02",
    "pattern_name": "Indirect Wealth",
    "step": "Step 1 - Prototype Definition",
    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    "physics_prototype": "Dynamic Flow / Risk Lens",
    "axioms": axioms,
    "init_matrix_logic": init_matrix_logic,
    "mining_filters_preview": {
        "L1": "Indirect_Wealth > 0.5",
        "L2": "Low Entanglement constraint RELAXED (High R allowed)",
        "L3": "Day_Master > 0.5 (Strong Self)"
    }
}

# 4. 物理写入
with open(PROTOTYPE_FILE, 'w', encoding='utf-8') as f:
    json.dump(prototype_data, f, indent=2, ensure_ascii=False)

print(f"💾 Prototype Defined: {os.path.abspath(PROTOTYPE_FILE)}")
print(f"🔒 Step 1 Locked. Ready to hunt in the Chaos (Step 2 Mining).")
