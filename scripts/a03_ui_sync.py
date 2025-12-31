import json
import os

# ==========================================
# A-03 Step 7: UI Integration (Project SUNRISE)
# ==========================================

REGISTRY_FILE = "core/subjects/holographic_pattern/registry.json"
UI_MANIFEST_FILE = "core/interface/ui_manifest_a03.json"

print(f"🖥️  [UI Sync] Generating Reactor Dashboard Config for A-03...")

# 1. 读取注册表以获取物理参数
with open(REGISTRY_FILE, 'r', encoding='utf-8') as f:
    data = json.load(f)
    a03_config = data["patterns"]["A-03"]

# 2. 构建 UI Manifest
# 这是一个告诉前端如何"翻译"物理数据的说明书
ui_config = {
    "pattern_id": "A-03",
    "view_mode": "REACTOR_DASHBOARD", # 专用视图模式
    "display_name": "A-03 羊刃架杀 (The Reactor)",
    
    # 核心隐喻：不显示五行柱状图，显示能量转化图
    "visual_metaphor": {
        "type": "CONFINED_FUSION",
        "components": [
            {
                "id": "core_fuel",
                "label": "内核能量 (Yang Ren)",
                "data_source": "tensor.E",
                "color": "#FF0000", # 赤色羊刃
                "animation": "PULSE_FAST" # 脉冲动画，暗示不稳定性
            },
            {
                "id": "confinement_field",
                "label": "磁场约束 (Seven Killings)",
                "data_source": "tensor.S",
                "color": "#222222", # 黑色七杀
                "visual_effect": "FORCE_FIELD" # 力场特效
            },
            {
                "id": "output_gauge",
                "label": "实际权柄 (Real Power)",
                "data_source": "computed.matrix_score", # [关键] 使用计算分，而非原始O
                "color": "#FFD700", # 金色权力
                "is_primary_metric": True,
                "note": "Power converted from Conflict, not Talent."
            }
        ]
    },

    # 动态文案引擎 (根据子格局变化)
    "dynamic_labels": {
        "SP_A03_STANDARD": {
            "status_text": "TOKAMAK STABLE",
            "warning": "High Internal Stress Detected.",
            "color_theme": "DARK_RED"
        },
        "SP_A03_ALLIANCE": {
            "status_text": "SUPERCONDUCTING",
            "warning": "Optimal Flow Achieved.",
            "color_theme": "ELECTRIC_BLUE" # 超导蓝
        }
    },

    # 异常状态 UI (用于调试或边缘情况)
    "alert_states": {
        "meltdown_risk": {
            "trigger": "E < S * 0.8", # 杀重身轻
            "message": "WARNING: Magnetic Crush Imminent (杀重攻身)",
            "visual": "FIELD_COLLAPSE"
        },
        "explosion_risk": {
            "trigger": "E > S * 1.5", # 身强杀浅
            "message": "WARNING: Plasma Leakage (羊刃无制)",
            "visual": "CORE_BREACH"
        }
    }
}

# 3. 写入前端配置库
os.makedirs(os.path.dirname(UI_MANIFEST_FILE), exist_ok=True)
with open(UI_MANIFEST_FILE, 'w', encoding='utf-8') as f:
    json.dump(ui_config, f, indent=2, ensure_ascii=False)

print(f"✅ UI Manifest Generated: {UI_MANIFEST_FILE}")
print(f"   Frontend Instruction: Switch ViewMode to 'REACTOR_DASHBOARD' when Pattern == A-03")
