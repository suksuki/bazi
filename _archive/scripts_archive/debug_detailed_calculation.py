"""
V18.0: 详细计算路径披露脚本
用于验证 C03, C04, C08 的完整计算过程
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

def create_profile_mock(case, luck):
    """创建模拟 profile"""
    bazi = case['bazi']
    class MockProfile:
        def __init__(self, dm, pillars, gender):
            self.day_master = dm
            self.pillars = {
                'year': pillars[0],
                'month': pillars[1],
                'day': pillars[2],
                'hour': pillars[3]
            }
            self.gender = 1 if gender == "男" else 0
            self.birth_date = None
        
        def get_luck_pillar_at(self, year):
            return luck
    return MockProfile(case['day_master'], bazi, case['gender'])

def debug_case(case_id):
    """调试指定案例的详细计算路径"""
    print("=" * 80)
    print(f"🔍 详细计算路径披露: {case_id}")
    print("=" * 80)
    
    # 加载案例
    cases = load_cases()
    case = next((c for c in cases if c.get('id') == case_id), None)
    if not case:
        print(f"❌ 案例 {case_id} 未找到")
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
        'case_id': case_id
    }
    
    # 计算
    try:
        energy_result = engine.calculate_energy(case_data)
        
        # 获取调试信息
        debug_info = None
        if hasattr(engine, 'domains') and hasattr(engine.domains, '_context'):
            debug_logs = engine.domains._context.get('debug_logs', [])
            for log in debug_logs:
                if log.get('case_id') == case_id:
                    debug_info = log
                    break
        
        # 获取 GT
        gt = case.get('ground_truth', {})
        target_focus = case.get('target_focus', 'UNKNOWN')
        
        if target_focus == 'WEALTH':
            model_score = energy_result.get('wealth', 0.0) * 10.0
            gt_score = gt.get('wealth_score', gt.get('wealth', 0.0))
        elif target_focus == 'CAREER':
            model_score = energy_result.get('career', 0.0) * 10.0
            gt_score = gt.get('career_score', gt.get('career', 0.0))
        elif target_focus == 'RELATIONSHIP':
            model_score = energy_result.get('relationship', 0.0) * 10.0
            gt_score = gt.get('relationship_score', gt.get('relationship', 0.0))
        else:
            model_score = (energy_result.get('career', 0.0) + 
                          energy_result.get('wealth', 0.0) + 
                          energy_result.get('relationship', 0.0)) / 3.0 * 10.0
            gt_score = (gt.get('career_score', 0) + 
                       gt.get('wealth_score', 0) + 
                       gt.get('relationship_score', 0)) / 3.0
        
        mae = abs(model_score - gt_score)
        
        print(f"\n📊 案例信息:")
        print(f"   目标维度: {target_focus}")
        print(f"   模型预测: {model_score:.2f}")
        print(f"   Ground Truth: {gt_score:.2f}")
        print(f"   MAE: {mae:.2f}")
        print(f"   状态: {'✅ PASS' if mae < 5.0 else '❌ FAIL'}")
        
        if debug_info and target_focus == 'WEALTH':
            print(f"\n🔬 完整计算路径 (Wealth Score):")
            print(f"   Step 1 - Base Score: {debug_info.get('step_1_base_score', 0):.2f}")
            print(f"   Step 2 - After Segment ({debug_info.get('segment', 'Unknown')}): {debug_info.get('step_2_after_segment', 0):.2f}")
            print(f"   Step 2 Capped: {debug_info.get('step_2_after_segment_capped', 0):.2f}")
            print(f"   Step 3 - After Bias Factor ({debug_info.get('observation_bias', 1.0):.2f}): {debug_info.get('step_3_after_bias', 0):.2f}")
            print(f"   Step 3 Capped (MaxScore={debug_info.get('max_score', 98):.0f}): {debug_info.get('step_3_after_bias_capped', 0):.2f}")
            print(f"   Step 4 - After Spacetime Corrector ({debug_info.get('spacetime_corrector', 1.0):.3f}): {debug_info.get('step_4_after_corrector', 0):.2f}")
            print(f"   Step 5 - Final Capped (MaxScore={debug_info.get('max_score', 98):.0f}): {debug_info.get('step_5_final_capped', 0):.2f}")
            print(f"   Final Score: {debug_info.get('final_score', 0):.2f}")
            
            # 验证一致性
            step5 = debug_info.get('step_5_final_capped', 0)
            final = debug_info.get('final_score', 0)
            if abs(step5 - final) < 0.01:
                print(f"\n✅ 一致性验证: Step 5 ({step5:.2f}) = Final Score ({final:.2f})")
            else:
                print(f"\n⚠️  不一致: Step 5 ({step5:.2f}) ≠ Final Score ({final:.2f}), 差异: {abs(step5 - final):.2f}")
            
            # 检查溢出
            if debug_info.get('step_4_after_corrector', 0) > debug_info.get('max_score', 98):
                print(f"⚠️  溢出检测: Step 4 得分 ({debug_info.get('step_4_after_corrector', 0):.2f}) > MaxScore ({debug_info.get('max_score', 98):.0f})")
            else:
                print(f"✅ 无溢出: Step 4 得分 ({debug_info.get('step_4_after_corrector', 0):.2f}) <= MaxScore ({debug_info.get('max_score', 98):.0f})")
        
        # 显示配置参数
        print(f"\n⚙️  应用的关键参数:")
        spacetime_config = config['physics'].get('SpacetimeCorrector', {})
        case_corrector = spacetime_config.get('CaseSpecificCorrectorFactor', {}).get(case_id, 'N/A')
        case_bias = config.get('ObservationBiasFactor', {}).get('CaseSpecificBias', {}).get(case_id, 'N/A')
        
        print(f"   CaseSpecificCorrectorFactor: {case_corrector}")
        print(f"   CaseSpecificBias: {case_bias}")
        print(f"   WealthAmplifier: {config['physics'].get('WealthAmplifier', 'N/A')}")
        print(f"   Wealth BiasFactor: {config.get('ObservationBiasFactor', {}).get('Wealth', 'N/A')}")
        print(f"   MaxScore: {config['physics'].get('MaxScore', 'N/A')}")
        
    except Exception as e:
        print(f"❌ 计算错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # 调试关键案例
    for case_id in ['C03', 'C04', 'C08']:
        debug_case(case_id)
        print("\n")

