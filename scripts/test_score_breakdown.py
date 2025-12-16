"""
V19.0: Test Score Breakdown Report
==================================
Test script to verify Score Breakdown Report functionality.
"""

import sys
import os
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.engine_v88 import EngineV88 as QuantumEngine
from core.config_schema import DEFAULT_FULL_ALGO_PARAMS
import copy

def create_profile_mock(case, luck):
    """Create a mock profile for testing"""
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

def test_score_breakdown():
    """Test Score Breakdown Report for a specific case"""
    # Load test case (C04 as example)
    path = "data/calibration_cases.json"
    if not os.path.exists(path):
        path = "calibration_cases.json"
    
    with open(path, "r", encoding='utf-8') as f:
        cases = json.load(f)
    
    # Use C04 as test case
    test_case = None
    for case in cases:
        if case.get('id') == 'C04':
            test_case = case
            break
    
    if not test_case:
        print("❌ C04 test case not found")
        return
    
    # Initialize engine
    params = copy.deepcopy(DEFAULT_FULL_ALGO_PARAMS)
    
    # Load config
    config_path = os.path.join(os.path.dirname(__file__), "../config/parameters.json")
    particle_weights_from_config = {}
    physics_config_from_file = {}
    observation_bias_config = {}
    
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
            particle_weights_from_config = config_data.get('particleWeights', {})
            physics_config_from_file = config_data.get('physics', {})
            observation_bias_config = config_data.get('ObservationBiasFactor', {})
    
    # Apply config
    if 'particleWeights' not in params:
        params['particleWeights'] = {}
    params['particleWeights'].update(particle_weights_from_config)
    
    # Create profile
    luck_pillar = test_case.get('luck_pillar', '甲子')
    profile = create_profile_mock(test_case, luck_pillar)
    
    # Initialize engine
    engine = QuantumEngine(params)
    
    # Load config for engine
    config_path = os.path.join(os.path.dirname(__file__), "../config/parameters.json")
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            engine.config = json.load(f)
    
    # Prepare case data for calculate_energy
    case_data = {
        'day_master': test_case['day_master'],
        'year': test_case['bazi'][0],
        'month': test_case['bazi'][1],
        'day': test_case['bazi'][2],
        'hour': test_case['bazi'][3],
        'gender': 1 if test_case['gender'] == '男' else 0,
        'case_id': 'C04'  # V19.0: Pass case_id for breakdown report
    }
    
    # Prepare dynamic context
    dynamic_context = {
        'luck_pillar': luck_pillar,
        'annual_pillar': test_case.get('annual_pillar', '甲子')
    }
    
    # Run calculation
    result = engine.calculate_energy(case_data, dynamic_context=dynamic_context)
    
    # Extract breakdown report from domain_details
    domain_details = result.get('domain_details', {})
    breakdown_report = domain_details.get('breakdown_report')
    
    if breakdown_report:
        print("=" * 80)
        print("✅ V19.0 Score Breakdown Report Generated Successfully!")
        print("=" * 80)
        print(json.dumps(breakdown_report, indent=2, ensure_ascii=False))
        print("=" * 80)
        
        # Print summary
        if 'Domains' in breakdown_report:
            domains = breakdown_report['Domains']
            print("\n📊 Summary:")
            for domain_name, domain_data in domains.items():
                final_score = domain_data.get('FinalScore', 0)
                interpretation = domain_data.get('Interpretation_Summary', {})
                print(f"\n  {domain_name.upper()}:")
                print(f"    Final Score: {final_score}")
                print(f"    Bias Effect: {interpretation.get('Bias_Effect_Magnitude', 'N/A')}")
                print(f"    Corrector Effect: {interpretation.get('Corrector_Effect_Magnitude', 'N/A')}")
                print(f"    Limiting Factor: {interpretation.get('Limiting_Factor', 'N/A')}")
    else:
        print("❌ Score Breakdown Report not found in result")
        print("Available keys:", list(result.keys()))

if __name__ == "__main__":
    test_score_breakdown()

