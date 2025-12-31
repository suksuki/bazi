import json
import os

# ==========================================
# D-01 Step 6: Load Testing (Direct Wealth)
# ==========================================

REGISTRY_FILE = "core/subjects/holographic_pattern/registry.json"

print(f"🧱 [Step 6 START] D-01 Keeper Exam...")

# 1. 加载引擎
if not os.path.exists(REGISTRY_FILE):
    raise FileNotFoundError("Registry file not found!")

with open(REGISTRY_FILE, 'r', encoding='utf-8') as f:
    data = json.load(f)
    d01_config = data["patterns"].get("D-01")

if not d01_config:
    raise ValueError("D-01 configuration not found!")

print(f"✅ Engine Loaded: {d01_config['name']} (V{d01_config['version']})")

# 2. 模拟路由
def execute_router(input_tensor, config):
    strategies = config['matching_router']['strategies']
    
    print(f"   ------------------------------------------------")
    print(f"   Input: E={input_tensor['E']:.2f}, M={input_tensor['M']:.2f}, R={input_tensor['R']:.2f}")

    for strat in strategies:
        target_name = strat['target']
        logic = strat['logic']
        
        condition = logic.get('condition')
        rules = logic.get('rules', [])
        
        all_passed = True
        failed_reason = ""
        
        for rule in rules:
            axis = rule['axis']
            val = input_tensor.get(axis, 0)
            threshold = rule['value']
            
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
             # Skip distance check simulation for brevity, focus on Logic Gates
            print(f"   [MATCH] Strategy '{target_name}' HIT! (Gates Passed)")
            return target_name
        else:
            print(f"   [SKIP]  Strategy '{target_name}' mismatch ({failed_reason})")

    return "MISMATCH"

# 3. 定义测试用例
test_cases = [
    {
        "name": "Case A: The Landlord (标准地主)",
        # 身旺，财旺，比劫少
        "tensor": {"E": 0.60, "M": 0.70, "R": 0.20, "O": 0.4, "S": 0.1},
        "expected": "SP_D01_STANDARD"
    },
    {
        "name": "Case B: Poor Rich Man (富屋贫人)",
        # 财极旺，但身弱 -> 应被拦截
        "tensor": {"E": 0.30, "M": 0.80, "R": 0.20, "O": 0.4, "S": 0.1},
        "expected": "MISMATCH"
    },
    {
        "name": "Case C: The Victim of Friends (群劫争财)",
        # 身旺，财旺，但比劫太多 -> 应被拦截
        "tensor": {"E": 0.60, "M": 0.70, "R": 0.60, "O": 0.2, "S": 0.1},
        "expected": "MISMATCH"
    }
]

# 4. 执行
passed = 0
for case in test_cases:
    print(f"\n🧪 Testing: {case['name']}")
    result = execute_router(case['tensor'], d01_config)
    
    if result == case['expected']:
        print(f"✅ PASSED")
        passed += 1
    else:
        print(f"❌ FAILED (Expected {case['expected']}, Got {result})")

if passed == len(test_cases):
    print("\n🏆 D-01 LOGIC VERIFIED.")
else:
    print("\n⚠️ D-01 LOGIC FAILED.")
