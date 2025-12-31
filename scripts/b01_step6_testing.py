import json
import os
import math

# ==========================================
# B-01 Step 6: Runtime Unit Testing
# (Updated to support HYBRID/AND logic)
# ==========================================

REGISTRY_FILE = "core/subjects/holographic_pattern/registry.json"

print(f"🚦 [Step 6 START] B-01 Engine Load Testing...")

# 1. 加载引擎
if not os.path.exists(REGISTRY_FILE):
    raise FileNotFoundError("Registry file not found!")

with open(REGISTRY_FILE, 'r', encoding='utf-8') as f:
    data = json.load(f)
    b01_config = data["patterns"].get("B-01")

if not b01_config:
    raise ValueError("B-01 configuration not found!")

print(f"✅ Engine Loaded: {b01_config['name']} (V{b01_config['version']})")

# 2. 模拟路由逻辑 (Simulated Router)
def execute_router(input_tensor, config):
    strategies = config['matching_router']['strategies']
    # 按照 Priority 排序
    strategies.sort(key=lambda x: x['priority'])
    
    print(f"   ------------------------------------------------")
    print(f"   Input: E={input_tensor['E']:.2f}, S={input_tensor['S']:.2f}, O={input_tensor['O']:.2f}")

    for strat in strategies:
        target_name = strat['target']
        logic = strat['logic']
        
        # 统一处理逻辑
        condition = logic.get('condition')
        
        if condition == 'AND':
            rules = logic['rules']
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
            
            if all_passed:
                print(f"   [MATCH] Strategy '{target_name}' HIT! (Condition: AND)")
                return target_name
            else:
                print(f"   [SKIP]  Strategy '{target_name}' mismatch ({failed_reason})")

        elif condition == 'HYBRID': # New composite logic support
            rules = logic['rules']
            all_passed = True
            failed_reason = ""
            
            # 1. Check Rules (E-Gating)
            for rule in rules:
                axis = rule['axis']
                val = input_tensor.get(axis, 0)
                threshold = rule['value']
                if rule['operator'] == 'gt':
                    if val <= threshold:
                        all_passed = False
                        failed_reason = f"{axis}={val:.2f} <= {threshold} (E-Gating)"
                        break
            
            # 2. Check Distance if Rules Passed
            if all_passed and 'distance_check' in logic:
                 # 读取 Standard 的均值
                std_mean = config['feature_anchors']['standard_manifold']['mean_vector']
                dist = 0
                weights = {'E':1, 'O':1, 'M':1, 'S':5, 'R':1} 
                for k in ['E', 'O', 'M', 'S', 'R']:
                    diff = input_tensor.get(k, 0) - std_mean.get(k, 0)
                    dist += (diff ** 2) * weights.get(k, 1)
                dist = math.sqrt(dist)
                
                threshold = logic['distance_check']['threshold']
                if dist > threshold:
                    all_passed = False
                    failed_reason = f"Dist={dist:.2f} > {threshold}"
                else:
                    failed_reason = f"Dist={dist:.2f} (OK)"

            if all_passed:
                print(f"   [MATCH] Strategy '{target_name}' HIT! (Condition: HYBRID)")
                return target_name
            else:
                print(f"   [SKIP]  Strategy '{target_name}' mismatch ({failed_reason})")


        elif condition == 'MAHALANOBIS':
            # This block might handle legacy cases if any remain
            pass

    return "MISMATCH (Broken Pattern)" # Default if no strategy hits

# 3. 定义关键测试用例 (Test Cases)
test_cases = [
    {
        "name": "Case A: The Artist (纯粹层流)",
        "tensor": {"E": 0.60, "O": 0.70, "M": 0.40, "S": 0.05, "R": 0.20}, 
        "expected": "SP_B01_STANDARD"
    },
    {
        "name": "Case B: The Phoenix (身旺带枭)",
        "tensor": {"E": 0.65, "O": 0.30, "M": 0.50, "S": 0.80, "R": 0.30},
        "expected": "SP_B01_REVERSAL"
    },
    {
        "name": "Case C: The Victim (身弱受克 - 必杀测试)",
        "tensor": {"E": 0.20, "O": 0.30, "M": 0.20, "S": 0.80, "R": 0.10},
        "expected": "MISMATCH (Broken Pattern)"
    }
]

# 4. 执行测试
print(f"🚀 Running {len(test_cases)} Critical Test Cases...")
passed_count = 0

for case in test_cases:
    print(f"\n🧪 Testing: {case['name']}")
    result = execute_router(case['tensor'], b01_config)
    
    if result == case['expected']:
        print(f"✅ RESULT: PASSED (Got {result})")
        passed_count += 1
    else:
        print(f"❌ RESULT: FAILED (Expected {case['expected']}, Got {result})")

print(f"\n📊 Test Summary: {passed_count}/{len(test_cases)} Passed.")

if passed_count == len(test_cases):
    print("🏆 B-01 ENGINE IS BATTLE READY (SECURED).")
else:
    print("⚠️ WARNING: Router Logic Still Flawed.")
