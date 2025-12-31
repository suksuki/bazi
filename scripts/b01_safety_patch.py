import json
import os

# ==========================================
# B-01 Safety Valve Patch (E-Gating)
# ==========================================

REGISTRY_FILE = "core/subjects/holographic_pattern/registry.json"

print(f"🔧 [Safety Patch] Installing E-Gating Brakes on B-01...")

if not os.path.exists(REGISTRY_FILE):
    raise FileNotFoundError("Registry file not found.")

with open(REGISTRY_FILE, 'r', encoding='utf-8') as f:
    data = json.load(f)
    b01_config = data["patterns"]["B-01"]

router = b01_config["matching_router"]
strategies = router["strategies"]

# 1. 定位 Standard 策略 (Priority 2)
# 注意：我们必须确保它是 Standard 策略
std_strat_idx = -1
for i, s in enumerate(strategies):
    if s["target"] == "SP_B01_STANDARD":
        std_strat_idx = i
        break

if std_strat_idx == -1:
    raise ValueError("Standard Strategy not found in B-01!")

# 2. 注入 E-Gating 逻辑
# 原逻辑: { "condition": "MAHALANOBIS", "threshold": 3.0 }
# 新逻辑: { "condition": "AND", "rules": [ {E > 0.32}, {MAHALANOBIS < 3.0} ] }
# 注意: 为了保持 Schema 简洁，V2.5 允许在 AND 规则中直接调用 "special_ops": "mahalanobis"
# 或者我们可以保留混合写法。这里我们采用最稳妥的 "Hybrid Logic" 写法。

old_logic = strategies[std_strat_idx]["logic"]
print(f"   - Old Logic: {old_logic}")

new_logic = {
    "condition": "HYBRID", # Updated to indicate custom handling in test script
    "description": "Composite Gate: Energy Floor + Manifold Shape",
    "rules": [
        {
            "axis": "E",
            "operator": "gt",
            "value": 0.32,  # [刹车点] 必须有根气，身弱不担食神
            "description": "Energy Gating (Anti-Leakage)"
        }
    ],
    # 将原有的马氏距离作为一个特殊规则保留
    # 实际引擎解析时需要支持这种混合，或者我们简化为两步验证
    # 这里我们定义为标准的 V2.5 扩展字段
    "distance_check": {
        "type": "MAHALANOBIS",
        "threshold": 3.0
    }
}

strategies[std_strat_idx]["logic"] = new_logic
strategies[std_strat_idx]["description"] += " [Secured by E-Gating]"

print(f"   - New Logic: E > 0.32 AND Mahalanobis < 3.0")

# 3. 物理写入
data["patterns"]["B-01"] = b01_config

with open(REGISTRY_FILE, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"✅ [PATCH COMPLETE] Brakes installed. Case C should now be physically impossible.")
