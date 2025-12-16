import sys
import os
import json
import copy
sys.path.append(os.getcwd())
try:
    from core.engine_v88 import EngineV88 as QuantumEngine  # V8.8 Modular
    from core.config_schema import DEFAULT_FULL_ALGO_PARAMS
    from ui.pages.quantum_lab import create_profile_from_case # Try reuse logic if possible, or mock
except ImportError:
    # If UI import fails due to streamlit dependency in headless mode, mock create_profile
    from core.bazi_profile import VirtualBaziProfile
    from core.engine_v88 import EngineV88 as QuantumEngine  # V8.8 Modular
    from core.config_schema import DEFAULT_FULL_ALGO_PARAMS

def create_profile_mock(case, luck):
    bazi = case['bazi'] # ["Year", "Month", "Day", "Hour"]
    # We need a profile with pillars accessed by .pillars['year']
    # VirtualBaziProfile is perfect.
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

def run_batch():
    # 1. Load Cases
    # Try data/ first, then root directory
    path = "data/calibration_cases.json"
    if not os.path.exists(path):
        path = "calibration_cases.json"
    if not os.path.exists(path):
        print("Error: calibration_cases.json not found in data/ or root directory.")
        return

    with open(path, "r", encoding='utf-8') as f:
        cases = json.load(f)

    # 2. Init Engine (With Tuning)
    params = copy.deepcopy(DEFAULT_FULL_ALGO_PARAMS)
    
    # V16.0: Load particle weights and physics config from config/parameters.json (single source of truth)
    config_path = os.path.join(os.path.dirname(__file__), "../config/parameters.json")
    particle_weights_from_config = {}
    physics_config_from_file = {}
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
                particle_weights_from_config = config_data.get('particleWeights', {})
                physics_config_from_file = config_data.get('physics', {})
                print(f"✅ Loaded particle weights from config: {len(particle_weights_from_config)} weights")
                print(f"✅ Loaded physics config: {list(physics_config_from_file.keys())}")
        except Exception as e:
            print(f"⚠️ Failed to load config: {e}, using defaults")
    else:
        print(f"⚠️ Config file not found: {config_path}, using defaults")
    
    # [Aggressive Pass 4: 极端化分段扶抑]
    # 1) 全局能量流转：提升留存，增加阻力
    params['flow']['outputViscosity'] = {
        'maxDrainRate': 0.35,
        'drainFriction': 0.30,
        'viscosity': 0.95
    }
    params['flow']['resourceImpedance'] = {'base': 0.75, 'weaknessPenalty': 0.75}
    
    # 2) 月令权威 & 时柱微调
    params['physics']['pillarWeights']['month'] = 1.80
    params['physics']['pillarWeights']['hour'] = 1.15
    
    # 3) 粒子权重：V16.0 - 从配置文件读取（单源数据）
    pw = params.setdefault('particleWeights', {})
    
    # Apply weights from config file (if available), otherwise use Step 1 defaults
    if particle_weights_from_config:
        pw.update(particle_weights_from_config)
        print(f"📊 Using particle weights from config/parameters.json")
    else:
        # Fallback to Step 1 defaults if config not found
        pw['PianCai'] = 1.50
        pw['ZhengCai'] = 1.30
        pw['ShiShen'] = 1.40
        pw['ShangGuan'] = 1.20
        pw['QiSha'] = 1.15
        pw['BiJian'] = 1.50
        pw['ZhengYin'] = 0.90
        pw['PianYin'] = 0.90
        pw['JieCai'] = 1.05
        print(f"📊 Using Step 1 default weights (config not found)")
    
    # V16.0: Apply physics config (amplifiers, exponents) from config file
    if physics_config_from_file:
        # Merge physics config into params
        if 'physics' not in params:
            params['physics'] = {}
        # Update with config file values (preserve existing pillarWeights if any)
        for key, value in physics_config_from_file.items():
            if key != 'pillarWeights':  # pillarWeights handled separately
                params['physics'][key] = value
        print(f"📊 Applied physics config: WealthAmplifier={params['physics'].get('WealthAmplifier', 'N/A')}, NonLinearExponent={params['physics'].get('NonLinearExponent', 'N/A')}")
    
    # V17.0: Load Observation Bias Factor from config file
    observation_bias_from_file = {}
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
                observation_bias_from_file = config_data.get('ObservationBiasFactor', {})
                if observation_bias_from_file:
                    print(f"✅ Loaded Observation Bias Factor: {list(observation_bias_from_file.keys())}")
        except Exception as e:
            print(f"⚠️ Failed to load observation bias: {e}")
    
    # Apply observation bias to config
    if observation_bias_from_file:
        params['ObservationBiasFactor'] = observation_bias_from_file
        print(f"📊 Applied Observation Bias Factor: Wealth={observation_bias_from_file.get('Wealth', 'N/A')}, Career={observation_bias_from_file.get('Career', 'N/A')}")
    
    # Legacy Bonus (Case 005) - Keep High
    params['interactions']['stemFiveCombination']['bonus'] = 6.0 
    
    engine = QuantumEngine()
    engine.update_full_config(params) # Deep Update
    
    print("=== 🧪 V16.0 宏观相精准调优 - MAE 验证报告 ===\n")
    print(f"{'Case ID':<10} | {'Focus':<12} | {'Career MAE':<12} | {'Wealth MAE':<12} | {'Rel MAE':<12} | {'Total MAE':<12} | {'Status':<8}")
    print("-" * 95)

    total_mae_career = 0.0
    total_mae_wealth = 0.0
    total_mae_rel = 0.0
    total_cases = 0
    results = []

    for c in cases:
        gt = c.get('ground_truth')
        if not gt: 
            print(f"Warning: {c.get('id', 'Unknown')} has no ground_truth, skipping.")
            continue
        
        target_focus = c.get('target_focus', 'UNKNOWN')
        total_cases += 1
        
        # Profile
        presets = c.get("dynamic_checks", [])
        luck_p = presets[0]['luck'] if presets else "癸卯"
        profile = create_profile_mock(c, luck_p)
        
        # Engine Eval - Get Domain Scores
        bazi_list = [profile.pillars['year'], profile.pillars['month'], profile.pillars['day'], profile.pillars['hour']]
        
        try:
            # Use calculate_energy to get domain scores
            case_data = {
                'day_master': profile.day_master,
                'year': bazi_list[0],
                'month': bazi_list[1],
                'day': bazi_list[2],
                'hour': bazi_list[3],
                'gender': profile.gender
            }
            
            # V16.0: Pass case_id to context for debug logging
            case_id = c.get('id', 'Unknown')
            if 'physics_config' not in case_data:
                case_data['physics_config'] = {}
            if 'case_id' not in case_data:
                case_data['case_id'] = case_id
            
            energy_result = engine.calculate_energy(case_data)
            
            # Domain scores are 0-10, convert to 0-100 for comparison
            model_career = energy_result.get('career', 0.0) * 10.0
            model_wealth = energy_result.get('wealth', 0.0) * 10.0
            model_rel = energy_result.get('relationship', 0.0) * 10.0
            
        except Exception as e:
            print(f"Error processing {c.get('id', 'Unknown')}: {e}")
            model_career = 0.0
            model_wealth = 0.0
            model_rel = 0.0

        # Calculate MAE (使用新的字段名: career_score, wealth_score, relationship_score)
        gt_career = gt.get('career_score', gt.get('career', 0.0))  # 兼容旧格式
        gt_wealth = gt.get('wealth_score', gt.get('wealth', 0.0))
        gt_rel = gt.get('relationship_score', gt.get('relationship', 0.0))
        
        mae_career = abs(model_career - gt_career)
        mae_wealth = abs(model_wealth - gt_wealth)
        mae_rel = abs(model_rel - gt_rel)
        
        # V16.0: 目标维度解耦拟合 - 只对 target_focus 维度计算 MAE
        # 情感作为定性参考，只检查是否在可接受区间 (< 25)
        if target_focus == 'WEALTH':
            target_mae = mae_wealth
            is_success = mae_wealth < 5.0
        elif target_focus == 'CAREER':
            target_mae = mae_career
            is_success = mae_career < 5.0
        elif target_focus == 'RELATIONSHIP':
            target_mae = mae_rel
            is_success = mae_rel < 5.0
        else:
            # STRENGTH 或其他：使用综合 MAE
            target_mae = (mae_career + mae_wealth + mae_rel) / 3.0
            is_success = target_mae < 5.0
        
        # 仍然计算所有维度的 MAE 用于统计，但成功判断只基于 target_focus
        total_mae = target_mae  # 用于显示的主要 MAE
        
        total_mae_career += mae_career
        total_mae_wealth += mae_wealth
        total_mae_rel += mae_rel
        
        # V16.0: Extract debug logs from domain processor context
        debug_info = None
        if hasattr(engine, 'domains') and hasattr(engine.domains, '_context'):
            debug_logs = engine.domains._context.get('debug_logs', [])
            if debug_logs:
                # Find debug info for this case
                case_id = c.get('id', 'Unknown')
                for log in debug_logs:
                    if log.get('case_id') == case_id:
                        debug_info = log
                        break
        
        results.append({
            'id': c.get('id', 'Unknown'),
            'focus': target_focus,
            'career_mae': mae_career,
            'wealth_mae': mae_wealth,
            'rel_mae': mae_rel,
            'total_mae': total_mae,
            'is_success': is_success,
            'model_career': model_career,
            'model_wealth': model_wealth,
            'model_rel': model_rel,
            'gt_career': gt_career,
            'gt_wealth': gt_wealth,
            'gt_rel': gt_rel,
            'debug_info': debug_info  # V16.0: Store debug info
        })
        
        status_icon = "✅ PASS" if is_success else "❌ FAIL"
        print(f"{c.get('id', 'Unknown'):<10} | {target_focus:<12} | {mae_career:<12.1f} | {mae_wealth:<12.1f} | {mae_rel:<12.1f} | {total_mae:<12.1f} | {status_icon:<8}")
        
        # V16.0: Print debug info for C01 and C04 (wealth)
        if debug_info and c.get('id') in ['C01', 'C04']:
            print(f"   🔍 Debug (Wealth): Base Energy (E)={debug_info.get('base_energy', 0):.2f}, "
                  f"Segment={debug_info.get('segment', 'Unknown')}, "
                  f"Potential={debug_info.get('potential', 0):.2f}, "
                  f"Modifier={debug_info.get('modifier', 1.0):.2f}, "
                  f"Amplifier={debug_info.get('amplifier', 1.0):.2f}, "
                  f"Final={debug_info.get('final_score', 0):.2f}")
        
        # V17.0: Print debug info for C07 (career)
        if debug_info and c.get('id') == 'C07':
            print(f"   🔍 Debug (Career): Base Energy={debug_info.get('base_energy_before_amplifier', 0):.2f}, "
                  f"Amplifier={debug_info.get('amplifier', 1.0):.2f}, "
                  f"Score After Amplifier={debug_info.get('score_after_amplifier', 0):.2f}")

    print("-" * 95)
    
    # Calculate Average MAE
    avg_mae_career = total_mae_career / total_cases if total_cases > 0 else 0.0
    avg_mae_wealth = total_mae_wealth / total_cases if total_cases > 0 else 0.0
    avg_mae_rel = total_mae_rel / total_cases if total_cases > 0 else 0.0
    avg_total_mae = (avg_mae_career + avg_mae_wealth + avg_mae_rel) / 3.0
    
    # Count successes (MAE < 5.0)
    success_count = sum(1 for r in results if r['is_success'])
    success_rate = (success_count / total_cases * 100) if total_cases > 0 else 0.0
    
    print(f"\n📊 平均 MAE (Average MAE):")
    print(f"   事业 (Career): {avg_mae_career:.1f}")
    print(f"   财富 (Wealth): {avg_mae_wealth:.1f}")
    print(f"   情感 (Relationship): {avg_mae_rel:.1f}")
    print(f"   综合 (Overall): {avg_total_mae:.1f}")
    print(f"\n✅ 成功率 (Success Rate): {success_rate:.1f}% ({success_count}/{total_cases} cases, 阈值: MAE < 5.0)")
    
    # Group by target_focus
    print(f"\n📈 按调优目标分组 (Grouped by Target Focus):")
    focus_groups = {}
    for r in results:
        focus = r['focus']
        if focus not in focus_groups:
            focus_groups[focus] = []
        focus_groups[focus].append(r)
    
    for focus, group_results in focus_groups.items():
        # V16.0: 只计算目标维度的平均 MAE
        if focus == 'WEALTH':
            group_mae = sum(r['wealth_mae'] for r in group_results) / len(group_results)
        elif focus == 'CAREER':
            group_mae = sum(r['career_mae'] for r in group_results) / len(group_results)
        elif focus == 'RELATIONSHIP':
            group_mae = sum(r['rel_mae'] for r in group_results) / len(group_results)
        else:
            group_mae = sum(r['total_mae'] for r in group_results) / len(group_results)
        print(f"   {focus}: {len(group_results)} cases, Avg MAE: {group_mae:.1f}")
    
    # Detailed breakdown for each case
    print(f"\n📋 详细对比 (Detailed Comparison):")
    for r in results:
        print(f"\n   {r['id']} ({r['focus']}):")
        print(f"      事业: 模型={r['model_career']:.1f}, GT={r['gt_career']:.1f}, MAE={r['career_mae']:.1f}")
        print(f"      财富: 模型={r['model_wealth']:.1f}, GT={r['gt_wealth']:.1f}, MAE={r['wealth_mae']:.1f}")
        print(f"      情感: 模型={r['model_rel']:.1f}, GT={r['gt_rel']:.1f}, MAE={r['rel_mae']:.1f}")

if __name__ == "__main__":
    run_batch()
