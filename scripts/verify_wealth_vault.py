import sys
import os
import json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.phase2_verifier import Phase2Verifier
from core.config_schema import DEFAULT_FULL_ALGO_PARAMS

def verify_vault():
    print("💰 [Antigravity] 启动 V11.0 财富墓库验证...")
    
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
    except Exception as e: 
        print(f"Warning: Could not load parameters.json: {e}")

    # 2. 定义案例: 壬水日主，坐戌(火库/财库)
    case_bazi = ['乙未', '丙戌', '壬戌', '辛亥']
    
    # 3. 模拟对比: 2023 (合库/闭锁) vs 2024 (冲库/爆发)
    years = [
        {'year': 2023, 'pillar': '癸卯', 'event': '合库(Closed)'},
        {'year': 2024, 'pillar': '甲辰', 'event': '冲库(Open)'}
    ]
    
    results = {}
    
    for y in years:
        # 重新初始化 verifier 确保环境一致
        verifier = Phase2Verifier(config)
        # V10.0-Graph: 使用 initialize_nodes 的 year_pillar 参数
        verifier.engine.initialize_nodes(case_bazi, '壬', year_pillar=y['pillar'])
        
        verifier.engine.build_adjacency_matrix()
        
        # 显式应用一次量子纠缠逻辑 (V11.0 核心)
        if hasattr(verifier.engine, '_apply_quantum_entanglement_once'):
            verifier.engine._apply_quantum_entanglement_once()
            
        verifier.engine.propagate(max_iterations=1, damping=1.0)
        
        # 提取火能量 (财星)
        nodes = verifier.engine.nodes
        fire_energy = 0.0
        
        # 统计火能量：包括本身是火的节点，以及地支中包含的隐藏火气
        for node in nodes:
            node_fire = 0.0
            if node.element == 'fire':
                node_fire = node.current_energy.mean
            elif node.node_type == 'branch' and hasattr(node, 'hidden_stems_energy'):
                # 如果是地支，统计其中的火余气
                if 'fire' in node.hidden_stems_energy:
                    node_fire = node.current_energy.mean * node.hidden_stems_energy['fire']
            
            if node_fire > 0:
                fire_energy += node_fire
                
        results[y['year']] = fire_energy
        print(f"📅 {y['year']} {y['pillar']} [{y['event']}]: 火能量 = {fire_energy:.2f}")

    # 4. 判定标准
    ratio = results[2024] / results[2023] if results[2023] > 0 else 0
    print(f"📈 财富爆发倍率: {ratio:.2f}x")
    
    if ratio > 1.3:
        print("✅ 验证通过: 财库被冲开，能量显著释放 (Wealth Burst Confirmed)！")
    else:
        print("❌ 验证失败: 冲库效果不明显，需检查 Threshold 或 OpenBonus。")

if __name__ == "__main__":
    verify_vault()
