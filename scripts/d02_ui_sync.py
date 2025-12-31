import json
import os

# ==========================================
# D-02 Step 7: UI Integration (The Turbulence Gauge)
# ==========================================

REGISTRY_FILE = "core/subjects/holographic_pattern/registry.json"
UI_MANIFEST_FILE = "core/interface/ui_manifest_d02.json"

print(f"🌊 [UI Sync] Generating Venture Dashboard for D-02...")

# 1. 读取注册表
with open(REGISTRY_FILE, 'r', encoding='utf-8') as f:
    data = json.load(f)
    # 确保 D-02 已注册
    if "D-02" not in data["patterns"]:
        raise ValueError("D-02 not found in Registry! Cannot generate UI.")

# 2. 构建 UI Manifest
ui_config = {
    "pattern_id": "D-02",
    "view_mode": "VENTURE_DASHBOARD", # 专用视图: 风险仪表盘
    "display_name": "D-02 偏财格 (The Hunter)",
    
    # 核心隐喻：湍流与流量
    "visual_metaphor": {
        "type": "TURBULENCE_GAUGE",
        "components": [
            {
                "id": "flow_velocity",
                "label": "现金流速 (Velocity)",
                "data_source": "tensor.M",
                "visual_type": "FLUID_METER", # 液体流量计
                "color": "#00FF00", # 现金流绿
                "note": "Base Wealth Volume"
            },
            {
                "id": "network_density",
                "label": "杠杆系数 (Leverage)",
                "data_source": "tensor.R",
                "visual_type": "NETWORK_GRAPH", # 只有 Syndicate 会高亮此项
                "color": "#00FFFF", # 赛博蓝 (连接)
                "threshold_highlight": 0.50 # R > 0.5 时图标变亮
            },
            {
                "id": "volatility_index",
                "label": "波动指数 (Volatility)",
                "data_source": "tensor.S",
                "visual_type": "OSCILLOSCOPE", # 只有 Collider 会剧烈波动
                "color": "#FF4500", # 警示橙 (风险)
                "threshold_highlight": 0.50
            }
        ]
    },

    # 动态文案与皮肤引擎 (根据子格局切换)
    "dynamic_labels": {
        "SP_D02_STANDARD": {
            "hero_title": "THE TYCOON (大亨)",
            "status_text": "CASH FLOW STABLE",
            "ui_theme": "LUXURY_GOLD", # 稳健的金色/深绿
            "main_visual": "PIPELINE_VIEW" # 显示粗壮的管道
        },
        "SP_D02_SYNDICATE": {
            "hero_title": "THE SYNDICATE (财团)",
            "status_text": "LEVERAGE ACTIVE (R-Amplified)",
            "ui_theme": "NEON_BLUE", # 科技蓝/连接感
            "main_visual": "NODE_TOPOLOGY" # 显示复杂的网络图
        },
        "SP_D02_COLLIDER": {
            "hero_title": "THE COLLIDER (枭雄)",
            "status_text": "HIGH VOLATILITY HARVESTING",
            "ui_theme": "ADRENALINE_RED", # 激进的红/黑
            "main_visual": "SEISMOGRAPH" # 显示剧烈的震荡波
        }
    },

    # 异常/边界状态提示
    "alert_states": {
        "bubble_risk": {
            "trigger": "M > 0.8 AND S > 0.7",
            "message": "WARNING: Asset Bubble Detected (泡沫风险)",
            "visual": "FLASHING_RED"
        },
        "leverage_warning": {
            "trigger": "R > 0.7 AND M < 0.6",
            "message": "WARNING: Empty Leverage (无效社交)",
            "visual": "DIMMED_NODES"
        }
    }
}

# 3. 写入前端配置库
os.makedirs(os.path.dirname(UI_MANIFEST_FILE), exist_ok=True)
with open(UI_MANIFEST_FILE, 'w', encoding='utf-8') as f:
    json.dump(ui_config, f, indent=2, ensure_ascii=False)

print(f"✅ UI Manifest Generated: {UI_MANIFEST_FILE}")
print(f"   Frontend Instruction: Use 'VENTURE_DASHBOARD' renderer.")
print(f"   Sub-Pattern Logic: Standard(Pipeline) | Syndicate(Nodes) | Collider(Waves)")
