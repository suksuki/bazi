import sys
import os
import json
import pandas as pd

# 添加项目根目录到路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.phase2_verifier import Phase2Verifier
from core.config_schema import DEFAULT_FULL_ALGO_PARAMS

def verify_geo():
    print("🌍 [Antigravity] 启动 V11.0 宏观地理验证...")
    
    # 1. 寒木向阳案例 (急需火)
    # 壬子 / 壬子 / 甲寅 / 壬申 (全剧寒湿，喜火解冻)
    bazi = ['壬子', '壬子', '甲寅', '壬申']
    
    # 2. 定义对比组
    locations = [
        {'name': '漠河 (Arctic)', 'lat': 53.0, 'desc': '极寒之地'},
        {'name': '新加坡 (Equator)', 'lat': 1.0,  'desc': '纯阳之地'}
    ]
    
    # 加载配置
    config = DEFAULT_FULL_ALGO_PARAMS.copy()
    config_path = 'config/parameters.json'
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            user_config = json.load(f)
            for k, v in user_config.items():
                if k in config and isinstance(v, dict):
                    config[k].update(v)
                else:
                    config[k] = v

    # 3. 运行仿真
    scores = {}
    for loc in locations:
        print(f"\n>>>> 正在仿真: {loc['name']} ({loc['lat']}°N) - {loc['desc']}")
        
        # 重新初始化 verifier
        verifier = Phase2Verifier(config)
        
        # [V11.0] 从配置读取真实参数
        geo_config = verifier.engine.config.get('spacetime', {}).get('geo', {})
        lat_heat_rate = geo_config.get('latitudeHeat', 0.08)
        
        # 模拟地理修正：以北纬 30 度为基准，计算相对于基准的偏移
        # 漠河 (53) 比基准北 23 度 -> 修正 = -2.3 * 0.08 = -0.184
        # 新加坡 (1) 比基准南 29 度 -> 修正 = +2.9 * 0.08 = +0.232
        base_lat = 30.0
        geo_mod = (base_lat - loc['lat']) / 10.0 * lat_heat_rate
        
        geo_modifiers = {
            'fire': 1.0 + geo_mod,
            'water': 1.0 - geo_mod
        }
        
        # 初始化节点
        verifier.engine.initialize_nodes(
            bazi=bazi, 
            day_master='甲',
            geo_modifiers=geo_modifiers
        )
        
        # 构建物理场
        verifier.engine.build_adjacency_matrix()
        
        # 运行纠缠
        if hasattr(verifier.engine, '_apply_quantum_entanglement_once'):
            verifier.engine._apply_quantum_entanglement_once()
            
        # 能量传播 (3次迭代以稳定化)
        verifier.engine.propagate(max_iterations=3, damping=0.9)
        
        # 4. 计算“生机”指数: 寒木需要火泄秀
        fire_energy = 0.0
        wood_energy = 0.0
        
        for node in verifier.engine.nodes:
            if node.element == 'fire':
                fire_energy += node.current_energy.mean
            elif node.element == 'wood':
                wood_energy += node.current_energy.mean
                
            # 藏干补丁
            if node.node_type == 'branch' and hasattr(node, 'hidden_stems_energy'):
                if 'fire' in node.hidden_stems_energy:
                    fire_energy += node.current_energy.mean * node.hidden_stems_energy['fire']
                if 'wood' in node.hidden_stems_energy:
                    wood_energy += node.current_energy.mean * node.hidden_stems_energy['wood']
        
        # 生机指数 = 火能 * 2.0 + 木能 * 0.5 (模拟调候为上原则)
        vitality = fire_energy * 2.0 + wood_energy * 0.5
        scores[loc['name']] = vitality
        
        print(f"   - 火能量: {fire_energy:.2f}")
        print(f"   - 木能量: {wood_energy:.2f}")
        print(f"   - 生机指数: {vitality:.2f}")

    # 5. 结果分析
    print("\n" + "="*40)
    v_arctic = scores['漠河 (Arctic)']
    v_equator = scores['新加坡 (Equator)']
    ratio = v_equator / v_arctic if v_arctic > 0 else 0
    
    print(f"📊 漠河(北) 生机: {v_arctic:.2f}")
    print(f"📊 新加坡(南) 生机: {v_equator:.2f}")
    print(f"🌡️ 地理环境修正倍率: {ratio:.2f}x")
    
    if ratio >= 1.4:
        print("\n✅ 验证通过: 地理环境显著改变了命局层次！")
    else:
        print("\n❌ 验证失败: 地理参数权重过低，需增强。")

if __name__ == "__main__":
    verify_geo()
