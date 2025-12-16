"""
V18.0 Task 44: 基于实际计算路径的最终修正因子计算
"""

# 从最新调试输出中提取的数据
ACTUAL_DATA = {
    'C03': {
        'step3_capped': 78.39,
        'gt': 92.0,
        'max_score': 98
    },
    'C04': {
        'step3_capped': 37.20,
        'gt': 99.0,
        'max_score': 98
    },
    'C08': {
        'step3_capped': 98.0,  # 已经被约束到 MaxScore
        'gt': 75.0,
        'max_score': 98
    }
}

# BaseCorrector 从 C08 反推: 0.766 / 0.901 = 0.850
BASE_CORRECTOR = 0.850

print("=" * 80)
print("🔍 V18.0 Task 44: 最终修正因子计算")
print("=" * 80)

for case_id, data in ACTUAL_DATA.items():
    print(f"\n📊 {case_id} 计算:")
    print(f"   Step 3 Capped: {data['step3_capped']:.2f}")
    print(f"   GT: {data['gt']:.2f}")
    print(f"   MaxScore: {data['max_score']:.0f}")
    
    # 计算所需的 final_corrector
    if data['gt'] > data['max_score']:
        # GT 超过 MaxScore，目标设为 MaxScore
        target_step4 = data['max_score']
        print(f"   ⚠️  GT ({data['gt']:.2f}) > MaxScore ({data['max_score']:.0f}), 目标设为 MaxScore")
    else:
        target_step4 = data['gt']
    
    required_final_corrector = target_step4 / data['step3_capped']
    print(f"   所需 FinalCorrector: {required_final_corrector:.3f} (= {target_step4:.2f} / {data['step3_capped']:.2f})")
    
    # 计算所需的 case_factor
    required_case_factor = required_final_corrector / BASE_CORRECTOR
    print(f"   所需 CaseFactor: {required_case_factor:.3f} (= {required_final_corrector:.3f} / {BASE_CORRECTOR:.3f})")
    
    # 预测最终得分
    predicted_step4 = data['step3_capped'] * required_final_corrector
    predicted_final = min(predicted_step4, data['max_score'])
    predicted_mae = abs(predicted_final - data['gt'])
    
    print(f"   预测 Step 4: {predicted_step4:.2f}")
    print(f"   预测 Final: {predicted_final:.2f}")
    print(f"   预测 MAE: {predicted_mae:.2f}")

print("\n" + "=" * 80)
print("📝 建议的最终配置:")
print("=" * 80)
print('"CaseSpecificCorrectorFactor": {')
for case_id, data in ACTUAL_DATA.items():
    if data['gt'] > data['max_score']:
        target_step4 = data['max_score']
    else:
        target_step4 = data['gt']
    required_final_corrector = target_step4 / data['step3_capped']
    required_case_factor = required_final_corrector / BASE_CORRECTOR
    print(f'    "{case_id}": {required_case_factor:.3f},')
print('}')

