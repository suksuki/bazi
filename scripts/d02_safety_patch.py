import json
import os

# ==========================================
# D-02 Step 7: Safety Patch (E-Gating Enforcement)
# ==========================================

REGISTRY_FILE = "core/subjects/holographic_pattern/registry.json"

print(f"🩹 [D-02 PATCH] Installing E-Gating Safety Protocols...")

if not os.path.exists(REGISTRY_FILE):
    raise FileNotFoundError("Registry file not found!")

# 1. 读取注册表
with open(REGISTRY_FILE, 'r', encoding='utf-8') as f:
    data = json.load(f)
    
if "D-02" not in data.get("patterns", {}):
    raise ValueError("D-02 pattern not found via Genesis!")

d02_config = data["patterns"]["D-02"]
strategies = d02_config["matching_router"]["strategies"]

# 2. 遍历所有策略进行修补
patched_count = 0

for strat in strategies:
    target = strat["target"]
    logic = strat["logic"]
    rules = logic.get("rules", [])
    
    # 检查是否已有 E 门控
    has_e_gate = False
    for r in rules:
        if r["axis"] == "E" and r["operator"] == "gt":
            # 如果已有，更新其阈值以确保安全
            if r["value"] < 0.45:
                print(f"   - Upgrading E-Gate for {target}: {r['value']} -> 0.45")
                r["value"] = 0.45
            has_e_gate = True
            break
            
    # 如果没有，强制插入
    if not has_e_gate:
        print(f"   - 🛡️ Injecting E-Gate for {target} (E > 0.45)")
        rules.insert(0, { # 插在最前面，作为第一道防线
            "axis": "E",
            "operator": "gt",
            "value": 0.45,
            "description": "Safety Protocol: Weak Self cannot hold Venture Wealth"
        })
        patched_count += 1
    
    strat["logic"]["rules"] = rules

# 3. 物理写入
if patched_count > 0:
    data["patterns"]["D-02"] = d02_config
    with open(REGISTRY_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"✅ [PATCH COMPLETE] Secured {patched_count} strategies. The Puppet (Gambler) is now locked out.")
else:
    print(f"✅ [NO ACTION] D-02 was already secure.")
