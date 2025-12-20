"""
V27.0 Task 71: 调试 SpacetimeCorrector 应用逻辑
==============================================
检查为什么C07的1.18没有被正确应用
"""

import sys
import os
import json
import io

# Fix Windows encoding issue
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

sys.path.append(os.getcwd())

from core.processors.domains import DomainProcessor

def debug_corrector():
    """调试SpacetimeCorrector应用逻辑"""
    
    print("=" * 80)
    print("V27.0 Task 71: SpacetimeCorrector 应用逻辑调试")
    print("=" * 80)
    
    # Load config
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "parameters.json")
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    physics_config = config.get('physics', {})
    spacetime_config = physics_config.get('SpacetimeCorrector', {})
    
    print(f"\n配置文件中的SpacetimeCorrector:")
    print(f"  Enabled: {spacetime_config.get('Enabled', False)}")
    print(f"  ExclusionList: {spacetime_config.get('ExclusionList', [])}")
    print(f"  CaseSpecificCorrectorFactor: {spacetime_config.get('CaseSpecificCorrectorFactor', {})}")
    
    # Create domain processor
    domain = DomainProcessor()
    
    # Create context with C07
    context = {
        'raw_energy': {'wood': 0, 'fire': 0, 'earth': 0, 'metal': 0, 'water': 0},
        'dm_element': 'metal',
        'strength': {'verdict': 'Strong', 'raw_score': 50.0},
        'gender': 1,
        'particle_weights': config.get('particleWeights', {}),
        'physics_config': physics_config,
        'observation_bias_config': config.get('ObservationBiasFactor', {}),
        'flow_config': config.get('flow', {}),
        'case_id': 'C07',
        'luck_pillar': None,
        'annual_pillar': None,
        # V18.0: SpacetimeCorrector config
        'spacetime_enabled': spacetime_config.get('Enabled', True),
        'spacetime_base': spacetime_config.get('CorrectorBaseFactor', 1.0),
        'luck_pillar_weight': spacetime_config.get('LuckPillarWeight', 0.6),
        'annual_pillar_weight': spacetime_config.get('AnnualPillarWeight', 0.4),
        'spacetime_exclusion_list': spacetime_config.get('ExclusionList', []),
        'case_specific_corrector': spacetime_config.get('CaseSpecificCorrectorFactor', {})
    }
    
    domain._context = context
    
    print(f"\nContext中的配置:")
    print(f"  case_id: {context.get('case_id')}")
    print(f"  spacetime_enabled: {context.get('spacetime_enabled')}")
    print(f"  spacetime_exclusion_list: {context.get('spacetime_exclusion_list')}")
    print(f"  case_specific_corrector: {context.get('case_specific_corrector')}")
    
    # Test _calculate_spacetime_corrector with debug
    print(f"\n测试 _calculate_spacetime_corrector 方法:")
    
    # Add debug prints to the method by monkey-patching
    original_method = domain._calculate_spacetime_corrector
    
    def debug_wrapper(domain_self, domain_name, verdict):
        print(f"\n  [DEBUG] 进入 _calculate_spacetime_corrector")
        print(f"    case_id: {domain_self._context.get('case_id', '')}")
        print(f"    spacetime_enabled: {domain_self._context.get('spacetime_enabled', False)}")
        print(f"    exclusion_list: {domain_self._context.get('spacetime_exclusion_list', [])}")
        print(f"    case_specific_corrector: {domain_self._context.get('case_specific_corrector', {})}")
        
        result = original_method(domain_self, domain_name, verdict)
        
        print(f"    [DEBUG] 返回结果: {result:.3f}")
        return result
    
    domain._calculate_spacetime_corrector = lambda d, v: debug_wrapper(domain, d, v)
    
    corrector = domain._calculate_spacetime_corrector('career', 'Strong')
    
    print(f"\n  返回的Corrector: {corrector:.2f}")
    print(f"  预期值: 1.18")
    
    # Manual calculation check
    print(f"\n手动计算验证:")
    spacetime_base = context.get('spacetime_base', 1.0)
    case_specific = context.get('case_specific_corrector', {})
    c07_factor = case_specific.get('C07', 1.0)
    
    print(f"  spacetime_base: {spacetime_base}")
    print(f"  C07 case_factor: {c07_factor}")
    
    # Since luck_pillar and annual_pillar are None, weighted_match = 0.0
    # corrector = 0.85 (unfavorable)
    # base_corrector = 1.0 * 0.85 = 0.85
    # final_corrector = 0.85 * 1.18 = 1.003
    
    print(f"\n  如果luck_pillar和annual_pillar都是None:")
    print(f"    weighted_match = 0.0")
    print(f"    corrector = 0.85 (unfavorable)")
    print(f"    base_corrector = {spacetime_base} × 0.85 = {spacetime_base * 0.85:.3f}")
    print(f"    final_corrector = {spacetime_base * 0.85:.3f} × {c07_factor} = {(spacetime_base * 0.85) * c07_factor:.3f}")
    
    if abs(corrector - 1.18) < 0.1:
        print(f"\n✅ Corrector接近预期值（考虑base_corrector的影响）")
    else:
        print(f"\n❌ Corrector与预期值差异较大")
        print(f"   可能原因：case_specific_corrector未正确应用")

if __name__ == "__main__":
    debug_corrector()

