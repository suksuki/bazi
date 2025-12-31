import json
import os

# ==========================================
# A-03 Step 6: Nuclear Safety Drill
# ==========================================

REGISTRY_FILE = "core/subjects/holographic_pattern/registry.json"

print(f"☢️  [Step 6 START] A-03 Reactor Safety Drill...")

# 1. 加载引擎
if not os.path.exists(REGISTRY_FILE):
    raise FileNotFoundError("Registry file not found!")

with open(REGISTRY_FILE, 'r', encoding='utf-8') as f:
    data = json.load(f)
    a03_config = data["patterns"].get("A-03")

if not a03_config:
    raise ValueError("A-03 Reactor configuration not found!")

print(f"✅ Reactor Online: {a03_config['name']} (V{a03_config['version']})")
print(f"   Safety Protocol: {a03_config['matching_router']['description']}")

# 2. 模拟路由逻辑
def execute_router(input_tensor, config):
    strategies = config['matching_router']['strategies']
    # 按照 Priority 排序
    strategies.sort(key=lambda x: x['priority'])
    
    print(f"   ------------------------------------------------")
    print(f"   Input: E={input_tensor['E']:.2f}, S={input_tensor['S']:.2f}, R={input_tensor['R']:.2f}, O={input_tensor['O']:.2f}")

    for strat in strategies:
        target_name = strat['target']
        logic = strat['logic']
        
        # 验证逻辑门
        # 注意：这里需要兼容 V2.5 的 HYBRID 结构
        condition = logic.get('condition')
        
        rules = []
        if condition == 'AND' or condition == 'HYBRID':
            rules = logic['rules']
            
        all_passed = True
        failed_reason = ""
        
        for rule in rules:
            axis = rule['axis']
            val = input_tensor.get(axis, 0)
            threshold = rule['value']
            
            # 执行操作符判断
            if rule['operator'] == 'gt':
                if val <= threshold:
                    all_passed = False
                    failed_reason = f"{axis}={val:.2f} <= {threshold}"
                    break
            elif rule['operator'] == 'lt':
                if val >= threshold:
                    all_passed = False
                    failed_reason = f"{axis}={val:.2f} >= {threshold}"
                    break
        
        if all_passed:
            # 如果有二级验证 (Distance Check)
            if "distance_check" in logic:
                # 简化模拟: 假设距离通过 (真实代码需计算)
                # 这里重点测试 Logic Gate
                pass 
            
            print(f"   [MATCH] Strategy '{target_name}' HIT! (Reactor Stable)")
            return target_name
        else:
            print(f"   [SKIP]  Strategy '{target_name}' mismatch ({failed_reason})")

    return "MISMATCH (Meltdown)"

# 3. 定义关键测试用例 (The Trinity)
test_cases = [
    {
        "name": "Case A: The Tokamak (标准反应堆)",
        # High E, High S, Low O (无泄气), Low R
        "tensor": {"E": 0.75, "S": 0.65, "O": 0.15, "R": 0.30, "M": 0.2}, 
        "expected": "SP_A03_STANDARD"
    },
    {
        "name": "Case B: The Stellarator (超导联盟)",
        # High E, High S, High R (合相)
        "tensor": {"E": 0.70, "S": 0.60, "O": 0.20, "R": 0.65, "M": 0.2},
        "expected": "SP_A03_ALLIANCE"
    },
    {
        "name": "Case Z: Hiroshima (核泄漏 - 必杀测试)",
        # High S (杀重), Low E (身弱), Low O
        "tensor": {"E": 0.25, "S": 0.85, "O": 0.10, "R": 0.15, "M": 0.1},
        # 1. Alliance 拒绝 (E < 0.60)
        # 2. Standard 拒绝 (E < 0.60)
        "expected": "MISMATCH (Meltdown)"
    }
]

# 4. 执行测试
print(f"🚀 Running {len(test_cases)} Critical Simulations...")
passed_count = 0

for case in test_cases:
    print(f"\n🧪 Simulation: {case['name']}")
    result = execute_router(case['tensor'], a03_config)
    
    if result == case['expected']:
        print(f"✅ RESULT: PASSED (Got {result})")
        passed_count += 1
    else:
        print(f"❌ RESULT: FAILED (Expected {case['expected']}, Got {result})")

print(f"\n📊 Drill Summary: {passed_count}/{len(test_cases)} Passed.")

if passed_count == len(test_cases):
    print("🏆 A-03 REACTOR IS SECURE.")
    print("   Physical Laws are holding. The weak are protected from the power they cannot wield.")
else:
    print("⚠️ CRITICAL FAILURE: Safety Protocols Breached!")
