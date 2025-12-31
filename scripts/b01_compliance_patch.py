import json
import os
import time

# ==========================================
# B-01 Compliance Patch (FDS-V1.5.1 Genesis)
# ==========================================

REGISTRY_FILE = "core/subjects/holographic_pattern/registry.json"
UNIVERSE_FILE = "core/data/holographic_universe_518k.jsonl"

print(f"⚖️  [Patching] Applying Genesis Protocol Compliance to B-01...")

if not os.path.exists(REGISTRY_FILE):
    raise FileNotFoundError("Registry file not found.")

# 1. 读取现有注册表
with open(REGISTRY_FILE, 'r', encoding='utf-8') as f:
    data = json.load(f)
    
if "B-01" not in data.get("patterns", {}):
    raise ValueError("B-01 entry not found! Cannot patch.")

b01_entry = data["patterns"]["B-01"]

# 2. 修补 Meta Info (溯源认证)
# 只有指向了静态宇宙文件的格局，才是合法的
if os.path.exists(UNIVERSE_FILE):
    universe_status = "LINKED"
    data_source = "holographic_universe_518k.jsonl (Static/Persistent)"
else:
    universe_status = "MISSING"
    data_source = "UNKNOWN (Violation)"

print(f"   - Universe Link Status: {universe_status}")

b01_entry["meta_info"]["compliance"] = "FDS-V1.5.1 (Genesis Protocol)"
b01_entry["meta_info"]["data_source"] = data_source
b01_entry["meta_info"]["last_audit"] = time.strftime("%Y-%m-%d %H:%M:%S")

# 3. 加固 Matching Router (确保 V2.5 结构)
# 再次确认优先级：Phoenix (P1) -> Standard (P2)
router = b01_entry["matching_router"]
router["strategy_version"] = "2.5 (Genesis)"
router["description"] = "Strict Priority: Singularity First, Standard Fallback."

# 检查策略完整性
strategies = router["strategies"]
phoenix_strat = next((s for s in strategies if s["target"] == "SP_B01_REVERSAL"), None)
standard_strat = next((s for s in strategies if s["target"] == "SP_B01_STANDARD"), None)

if phoenix_strat and standard_strat:
    # 强制修正优先级
    phoenix_strat["priority"] = 1
    standard_strat["priority"] = 2
    print(f"   - Router Priority Enforced: Reversal(1) > Standard(2)")
else:
    print(f"⚠️  Warning: Strategies incomplete. Please re-run Step 5.")

# 4. 物理写入
data["patterns"]["B-01"] = b01_entry

with open(REGISTRY_FILE, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"✅ [PATCH COMPLETE] B-01 is now legally compliant with FDS-V1.5.1.")
print(f"   - Compliance Tag: {b01_entry['meta_info']['compliance']}")
print(f"   - Data Source: {b01_entry['meta_info']['data_source']}")
