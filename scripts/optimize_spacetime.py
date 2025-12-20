import sys
import os
import json
import pandas as pd
import numpy as np

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.phase2_verifier import Phase2Verifier
from core.config_schema import DEFAULT_FULL_ALGO_PARAMS
from core.math import ProbValue

def simulate_musk(luck_w, annual_w, label):
    """
    模拟马斯克案例在特定权重下的表现。
    八字: 甲申 / 庚午 / 甲申 / 戊辰 (日主甲木，金旺，喜火制杀)
    """
    bazi = ['甲申', '庚午', '甲申', '戊辰']
    
    # 定义关键时间点
    years = [
        {'year': 2008, 'pillar': '戊子', 'luck': '壬申', 'desc': '2008年 (壬申运/戊子年 - 破产边缘)'},
        {'year': 2020, 'pillar': '庚子', 'luck': '丙子', 'desc': '2020年 (丙子运/庚子年 - 财富爆发)'}
    ]
    
    # 1. 加载配置
    config = DEFAULT_FULL_ALGO_PARAMS.copy()
    try:
        config_path = 'config/parameters.json'
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
                for k, v in user_config.items():
                    if k in config and isinstance(v, dict):
                        config[k].update(v)
                    else:
                        config[k] = v
    except: pass
    
    # 2. 覆盖待扫描的权重
    if 'spacetime' not in config:
        config['spacetime'] = {}
    config['spacetime']['luckPillarWeight'] = luck_w
    config['spacetime']['annualPillarWeight'] = annual_w
    
    print(f"\n🧪 测试模型: {label} (Luck={luck_w}, Annual={annual_w})")
    
    scores = {}
    
    for y in years:
        verifier = Phase2Verifier(config)
        # 使用 initialize_nodes 注入大运与流年
        verifier.engine.initialize_nodes(
            bazi=bazi, 
            day_master='甲', 
            luck_pillar=y['luck'], 
            year_pillar=y['pillar']
        )
        
        verifier.engine.build_adjacency_matrix()
        
        # 显式应用纠缠 logic
        if hasattr(verifier.engine, '_apply_quantum_entanglement_once'):
            verifier.engine._apply_quantum_entanglement_once()
            
        verifier.engine.propagate(max_iterations=3, damping=0.9)
        
        # 计算“身杀平衡度”: 火(食伤) vs 金(官杀)
        # 马斯克案例中，金极旺，需要火来制约。火能量越高且金能量受控，得分越高。
        fire_energy = 0.0
        metal_energy = 0.0
        
        for node in verifier.engine.nodes:
            # 统计汇总火能与金能
            if node.element == 'fire':
                fire_energy += node.current_energy.mean
            elif node.element == 'metal':
                metal_energy += node.current_energy.mean
            
            # 考虑隐藏气
            if node.node_type == 'branch' and hasattr(node, 'hidden_stems_energy'):
                if 'fire' in node.hidden_stems_energy:
                    fire_energy += node.current_energy.mean * node.hidden_stems_energy['fire']
                if 'metal' in node.hidden_stems_energy:
                    metal_energy += node.current_energy.mean * node.hidden_stems_energy['metal']
        
        # 简化得分公式: 身杀平衡程度
        score = fire_energy - metal_energy
        scores[y['year']] = score
        print(f"  📅 {y['year']} ({y['luck']}/{y['pillar']}): Fire={fire_energy:.2f}, Metal={metal_energy:.2f} -> 得分 = {score:.2f}")
        
    delta = scores[2020] - scores[2008]
    print(f"  📈 命运反转幅度 (2020 - 2008 Delta): {delta:.2f}")
    return delta

if __name__ == "__main__":
    # 运行 A/B/C/D 模型扫描
    tests = [
        (1.2, 0.8, "A: 大运主导 (Climate)"),
        (0.8, 1.2, "B: 流年主导 (Weather)"),
        (1.0, 1.0, "C: 均衡模型 (Balanced)"),
        (1.5, 0.5, "D: 强力大运 (Deep Roots)"),
        (2.0, 1.0, "E: 环境统摄 (Field Dominant)")
    ]
    
    results = {}
    for lw, aw, label in tests:
        results[label] = simulate_musk(lw, aw, label)
        
    best_model = max(results, key=results.get)
    print(f"\n🏆 最佳拟合模型: {best_model} (Delta={results[best_model]:.2f})")
