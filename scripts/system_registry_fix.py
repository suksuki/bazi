import json
import os
import re

# ==========================================
# System Utility: Registry Metadata Normalization
# ==========================================

REGISTRY_FILE = "core/subjects/holographic_pattern/registry.json"

print(f"🧹 [SYSTEM] Starting Registry Metadata Cleanup...")

if not os.path.exists(REGISTRY_FILE):
    raise FileNotFoundError("Registry file missing!")

with open(REGISTRY_FILE, 'r', encoding='utf-8') as f:
    data = json.load(f)

patterns = data.get("patterns", {})
updated_count = 0

# 定义标准映射表 (手动补全缺失信息)
# 这里确保 B-01, A-03, D-01, D-02 都有完整的 UI 元数据
meta_patch = {
    "A-03": {
        "category": "POWER (权柄)",
        "chinese_name": "羊刃架杀格",
        "display_name": "Yang Ren Jia Sha (The Reactor)"
    },
    "B-01": {
        "category": "TALENT (才华)",
        "chinese_name": "食神格",
        "display_name": "Eating God (The Artist)"
    },
    "D-01": {
        "category": "WEALTH (财富)",
        "chinese_name": "正财格",
        "display_name": "Proper Wealth (The Keeper)"
    },
    "D-02": {
        "category": "WEALTH (财富)",
        "chinese_name": "偏财格",
        "display_name": "Indirect Wealth (The Hunter)"
    }
}

for pid, entry in patterns.items():
    meta = entry.get("meta_info", {})
    patch = meta_patch.get(pid)
    
    if patch:
        print(f"   - Fixing Metadata for {pid}...")
        
        # 1. 修复 Category (类别)
        # 即使有值，为了统一格式（例如全是英文大写），也覆盖一次
        meta["category"] = patch["category"]
            
        # 2. 修复中文名 (Chinese Name)
        meta["chinese_name"] = patch["chinese_name"]

        # 3. 修复显示名 (Name)
        meta["name"] = patch["display_name"]
        
        # 4. 确保 compliance 字段存在
        if "compliance" not in meta:
            meta["compliance"] = "FDS-V1.5.1"

        updated_count += 1
    
    entry["meta_info"] = meta

# 检查 B-01 是否丢失
if "B-01" not in patterns:
    print(f"⚠️  ALERT: B-01 is MISSING from the JSON. It needs full re-registration (Step 5).")
else:
    print(f"✅ B-01 is present.")

# 保存
if updated_count > 0:
    with open(REGISTRY_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"✅ Cleanup Complete. {updated_count} patterns normalized.")
    print(f"   UI Status: D-02 'N/A' resolved. Chinese names populated.")
else:
    print("✅ Registry was already clean.")
