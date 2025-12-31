import json

# Mock Registry Loader
with open("core/subjects/holographic_pattern/registry.json", 'r') as f:
    registry = json.load(f)

a01 = registry['patterns']['A-01']
router = a01['matching_router']

def check_condition(rules, tensor):
    for rule in rules:
        val = tensor[rule['axis']]
        threshold = rule['value']
        if rule['operator'] == 'gt' and not (val > threshold): return False
        if rule['operator'] == 'lt' and not (val < threshold): return False
    return True

print("🧪 [A-01 TESTING] Running Routing Simulation...")

test_cases = [
    {
        "name": "TEST_CASE_BUREAUCRAT (Standard)",
        "tensor": {"E": 0.65, "O": 0.65, "M": 0.4, "S": 0.10, "R": 0.3},
        "expected": "SP_A01_STANDARD"
    },
    {
        "name": "TEST_CASE_RIGID (Overcontrol)",
        "tensor": {"E": 0.60, "O": 0.75, "M": 0.2, "S": 0.05, "R": 0.3},
        # High O (>0.7), Low S (<0.15), E (>0.4)
        "expected": "SP_A01_OVERCONTROL"
    },
    {
        "name": "TEST_CASE_WEAK_SELF (Rejection)",
        "tensor": {"E": 0.30, "O": 0.65, "M": 0.4, "S": 0.10, "R": 0.3},
        # E < 0.45 -> Should be rejected
        "expected": None 
    }
]

for case in test_cases:
    tensor = case['tensor']
    result = None
    
    # Simulate Router Logic
    for strategy in router['strategies']:
        logic = strategy['logic']
        if logic['condition'] in ['AND', 'HYBRID']: # Simplified check
            if check_condition(logic['rules'], tensor):
                result = strategy['target']
                break
    
    status = "✅ PASS" if result == case['expected'] else f"❌ FAIL (Got {result})"
    print(f"   {case['name']}: {status}")

print("Done.")
