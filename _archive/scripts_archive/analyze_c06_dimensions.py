"""
V18.0 Task 45: C06 维度解耦分析
分析 C06 的三个维度（财富、事业、情感），找出 MAE 最高的维度并计算修正因子
"""

import sys
import os
import json
import copy

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from core.engine_v88 import EngineV88 as QuantumEngine
from core.config_schema import DEFAULT_FULL_ALGO_PARAMS

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "parameters.json")

def load_cases():
    """加载校准案例"""
    path = "data/calibration_cases.json"
    if not os.path.exists(path):
        path = "calibration_cases.json"
    
    with open(path, "r", encoding='utf-8') as f:
        return json.load(f)

def analyze_c06():
    """分析 C06 的三个维度"""
    print("=" * 80)
    print("🔍 V18.0 Task 45: C06 维度解耦分析")
    print("=" * 80)
    
    # 加载案例
    cases = load_cases()
    case = next((c for c in cases if c.get('id') == 'C06'), None)
    if not case:
        print("❌ C06 案例未找到")
        return
    
    # 加载配置
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    params = copy.deepcopy(DEFAULT_FULL_ALGO_PARAMS)
    params['particleWeights'] = config.get('particleWeights', {})
    params['physics'].update(config.get('physics', {}))
    params['ObservationBiasFactor'] = config.get('ObservationBiasFactor', {})
    params['flow'] = config.get('flow', {})
    
    # 初始化引擎
    engine = QuantumEngine()
    engine.update_full_config(params)
    
    # 准备案例数据
    presets = case.get("dynamic_checks", [])
    luck_p = presets[0]['luck'] if presets else "癸卯"
    
    case_data = {
        'day_master': case['day_master'],
        'year': case['bazi'][0],
        'month': case['bazi'][1],
        'day': case['bazi'][2],
        'hour': case['bazi'][3],
        'gender': 1 if case['gender'] == "男" else 0,
        'case_id': 'C06'
    }
    
    # 计算
    try:
        energy_result = engine.calculate_energy(case_data)
        
        # 获取 GT
        gt = case.get('ground_truth', {})
        
        # 三个维度的分数（0-10 范围，需要转换为 0-100）
        model_career = energy_result.get('career', 0.0) * 10.0
        model_wealth = energy_result.get('wealth', 0.0) * 10.0
        model_rel = energy_result.get('relationship', 0.0) * 10.0
        
        # GT 分数
        gt_career = gt.get('career_score', gt.get('career', 0.0))
        gt_wealth = gt.get('wealth_score', gt.get('wealth', 0.0))
        gt_rel = gt.get('relationship_score', gt.get('relationship', 0.0))
        
        # 计算各维度 MAE
        mae_career = abs(model_career - gt_career)
        mae_wealth = abs(model_wealth - gt_wealth)
        mae_rel = abs(model_rel - gt_rel)
        
        # 综合 MAE（平均值）
        avg_mae = (mae_career + mae_wealth + mae_rel) / 3.0
        
        print(f"\n📊 C06 维度详细分析:")
        print(f"{'维度':<12} | {'模型预测':<12} | {'GT':<12} | {'MAE':<12} | {'状态':<8}")
        print("-" * 65)
        print(f"{'事业 (Career)':<12} | {model_career:<12.2f} | {gt_career:<12.2f} | {mae_career:<12.2f} | {'✅ PASS' if mae_career < 5.0 else '❌ FAIL':<8}")
        print(f"{'财富 (Wealth)':<12} | {model_wealth:<12.2f} | {gt_wealth:<12.2f} | {mae_wealth:<12.2f} | {'✅ PASS' if mae_wealth < 5.0 else '❌ FAIL':<8}")
        print(f"{'情感 (Rel)':<12} | {model_rel:<12.2f} | {gt_rel:<12.2f} | {mae_rel:<12.2f} | {'✅ PASS' if mae_rel < 5.0 else '❌ FAIL':<8}")
        print(f"{'综合 (Avg)':<12} | {'-':<12} | {'-':<12} | {avg_mae:<12.2f} | {'✅ PASS' if avg_mae < 5.0 else '❌ FAIL':<8}")
        
        # 找出 MAE 最高的维度
        dimensions = [
            {'name': 'Career', 'model': model_career, 'gt': gt_career, 'mae': mae_career},
            {'name': 'Wealth', 'model': model_wealth, 'gt': gt_wealth, 'mae': mae_wealth},
            {'name': 'Relationship', 'model': model_rel, 'gt': gt_rel, 'mae': mae_rel}
        ]
        
        max_mae_dim = max(dimensions, key=lambda x: x['mae'])
        
        print(f"\n🎯 诊断结果:")
        print(f"   MAE 最高的维度: {max_mae_dim['name']} (MAE = {max_mae_dim['mae']:.2f})")
        print(f"   模型预测: {max_mae_dim['model']:.2f}")
        print(f"   Ground Truth: {max_mae_dim['gt']:.2f}")
        
        # 计算所需的修正因子
        # 需要获取该维度在 Step 3 Capped 的得分
        # 由于 C06 是 STRENGTH 类型，我们需要检查哪个维度需要修正
        
        print(f"\n🔧 修正策略:")
        print(f"   由于 C06 是 STRENGTH 类型，CaseSpecificCorrectorFactor 会同时影响三个维度。")
        print(f"   当前配置: {config['physics']['SpacetimeCorrector'].get('CaseSpecificCorrectorFactor', {}).get('C06', 'N/A')}")
        
        # 计算综合修正因子（基于平均 MAE）
        if avg_mae >= 5.0:
            # 计算综合目标
            target_avg = (gt_career + gt_wealth + gt_rel) / 3.0
            current_avg = (model_career + model_wealth + model_rel) / 3.0
            
            if current_avg > 0:
                required_factor = target_avg / current_avg
                print(f"\n   综合修正因子计算:")
                print(f"   当前平均得分: {current_avg:.2f}")
                print(f"   目标平均得分: {target_avg:.2f}")
                print(f"   所需修正因子: {required_factor:.3f}")
                
                # 考虑 BaseCorrector = 0.85
                BASE_CORRECTOR = 0.850
                required_case_factor = required_factor / BASE_CORRECTOR
                print(f"   所需 CaseFactor: {required_case_factor:.3f} (= {required_factor:.3f} / {BASE_CORRECTOR:.3f})")
        
        # 维度特定分析
        print(f"\n📋 各维度详细分析:")
        for dim in dimensions:
            if dim['mae'] >= 5.0:
                print(f"\n   {dim['name']}:")
                print(f"      模型: {dim['model']:.2f}, GT: {dim['gt']:.2f}, MAE: {dim['mae']:.2f}")
                if dim['model'] > 0:
                    required_factor = dim['gt'] / dim['model']
                    print(f"      所需修正因子: {required_factor:.3f} (= {dim['gt']:.2f} / {dim['model']:.2f})")
        
    except Exception as e:
        print(f"❌ 计算错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_c06()

