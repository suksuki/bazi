
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from core.registry_loader import RegistryLoader
from core.math_engine import tensor_normalize

def test_a03_singularity_recognition():
    print("🚀 Starting A-03 Singularity Recognition (Tomb Raider) Test...")
    
    loader = RegistryLoader()
    pattern_id = "A-03"
    
    # 1. 模拟一个“古墓丽影”型的张量 (High E, High M, Low O)
    # 模拟未归一化的原始投影
    raw_tensor = {
        "E": 0.95,
        "O": 0.30, 
        "M": 0.85, 
        "S": 0.70, 
        "R": 0.40
    }
    
    # 归一化（因为pattern_recognition要求输入归一化张量）
    current_tensor = tensor_normalize(raw_tensor)
    print(f"📡 Input Tensor (Normalized): {current_tensor}")
    
    # 2. 场景 A: 静态观测 (Stable) - 应该匹配失败或匹配度低 (因为O轴不匹配)
    # 或者匹配 Standard 但分数低
    print("\n[Scenario A] Static Observation (State=STABLE)")
    result_stable = loader.pattern_recognition(
        current_tensor, 
        pattern_id, 
        dynamic_state="STABLE", 
        sai=0.95
    )
    print(f"   Match Result: {result_stable.get('matched')}")
    print(f"   Pattern Type: {result_stable.get('pattern_type')}")
    p_score = result_stable.get('precision_score')
    if p_score:
        print(f"   Precision: {p_score:.4f}")
    else:
        print("   Precision: N/A (Singularity Override)")
    print(f"   Description: {result_stable.get('description')}")
    
    # 3. 场景 B: 动态观测 (Activated) - 触发开库相变
    print("\n[Scenario B] Dynamic Observation (State=ACTIVATED) - 触发开库")
    result_active = loader.pattern_recognition(
        current_tensor, 
        pattern_id, 
        dynamic_state="ACTIVATED", 
        sai=0.95
    )
    print(f"   Match Result: {result_active.get('matched')}")
    print(f"   Pattern Type: {result_active.get('pattern_type')}")
    p_score_act = result_active.get('precision_score')
    if p_score_act:
        print(f"   Precision: {p_score_act:.4f}")
    else:
        print("   Precision: N/A (Singularity Override)")
    print(f"   Description: {result_active.get('description')}")
    print(f"   Sub-Pattern ID: {result_active.get('anchor_id')}")
    
    # 验证是否识别为 A-03-X1 或 ACTIVATED
    if result_active.get('pattern_type') == 'SINGULARITY' and 'A-03-X1' in str(result_active):
        print("\n✅ SUCCESS: Identified 'A-03-X1 Tomb Raider' Singularity!")
    elif result_active.get('pattern_type') == 'ACTIVATED':
        print("\n✅ SUCCESS: Matched 'Activated Manifold' (Tomb Raider Mode)!")
    else:
        print("\n❌ FAILURE: Failed to recognize singularity.")

if __name__ == "__main__":
    test_a03_singularity_recognition()
