import json
import os

# ==========================================
# D-02 Step 6: Load Testing (Indirect Wealth)
# ==========================================

REGISTRY_FILE = "core/subjects/holographic_pattern/registry.json"

print(f"🌊 [Step 6 START] D-02 Hunter's Exam...")

# 1. 加载引擎
if not os.path.exists(REGISTRY_FILE):
    raise FileNotFoundError("Registry file not found!")

with open(REGISTRY_FILE, 'r', encoding='utf-8') as f:
    data = json.load(f)
    d02_config = data["patterns"].get("D-02")

if not d02_config:
    raise ValueError("D-02 configuration not found!")

print(f"✅ Engine Loaded: {d02_config['name']} (V{d02_config['version']})")

# 2. 模拟路由
def execute_router(input_tensor, config):
    strategies = config['matching_router']['strategies']
    # Sort by priority just in case
    strategies.sort(key=lambda x: x['priority'])
    
    print(f"   ------------------------------------------------")
    print(f"   Input: E={input_tensor['E']:.2f}, M={input_tensor['M']:.2f}, S={input_tensor['S']:.2f}, R={input_tensor['R']:.2f}")

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
             # Skip distance check simulation for brevity
            print(f"   [MATCH] Strategy '{target_name}' HIT! (Priority {strat['priority']})")
            return target_name
        else:
            print(f"   [SKIP]  Strategy '{target_name}' mismatch ({failed_reason})")

    return "MISMATCH"

# 3. 定义测试用例 (The Hunter's Exam)
test_cases = [
    {
        "name": "Case 1: The Tycoon (标准大亨)",
        # High E, High M, Low R, Low S -> Should fall through to Standard
        "tensor": {"E": 0.70, "M": 0.70, "R": 0.20, "S": 0.20},
        "expected": "SP_D02_STANDARD"
    },
    {
        "name": "Case 2: The Syndicate (众筹大鳄)",
        # High E, High M, High R -> Should be Syndicate (P2)
        "tensor": {"E": 0.65, "M": 0.70, "R": 0.65, "S": 0.20},
        "expected": "SP_D02_SYNDICATE"
    },
    {
        "name": "Case 3: The Collider (风险套利者)",
        # High E, High M, High S (Priority 1)
        "tensor": {"E": 0.75, "M": 0.80, "S": 0.70, "R": 0.40},
        "expected": "SP_D02_COLLIDER"
    },
    {
        "name": "Case 4: The Gambler (赌徒 - 必杀测试)",
        # Low E (Weak Self) -> Should be rejected by ALL strategies due to implicit or explicit E-check
        # Note: In Step 5, Syndicate/Collider logic didn't explicitly include "E > 0.45" inside the rules list 
        # but Standard did. Wait...
        # Let's check if the script runs correctly. If I failed to add E-check to Syn/Col in Step 5, this will FAIL.
        # This test is CRITICAL to verify if I made a mistake in Step 5.
        "tensor": {"E": 0.30, "M": 0.80, "R": 0.70, "S": 0.10},
        "expected": "MISMATCH"
    }
]

# 4. 执行
passed = 0
print(f"🚀 Running 4 Critical Exams...")

for case in test_cases:
    print(f"\n🧪 Testing: {case['name']}")
    result = execute_router(case['tensor'], d02_config)
    
    # Logic fix for Case 4:
    # If Step 5 script missed the E-check for P1/P2, Case 4 might match Syndicate.
    # We will see the output.
    
    if result == case['expected']:
        print(f"✅ PASSED")
        passed += 1
    else:
        print(f"❌ FAILED (Expected {case['expected']}, Got {result})")

if passed == len(test_cases):
    print("\n🏆 D-02 LOGIC VERIFIED (SECURE).")
else:
    print("\n⚠️ D-02 LOGIC FAILED / SECURITY HOLE DETECTED.")
