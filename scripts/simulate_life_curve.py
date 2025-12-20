import sys
import os
import pandas as pd
import json

# 添加项目根目录到路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.phase2_verifier import Phase2Verifier
from core.config_schema import DEFAULT_FULL_ALGO_PARAMS

def run_simulation():
    """
    运行史蒂夫·乔布斯 (Steve Jobs) 的流年仿真
    验证点：2011 年辛卯流年导致的“亥卯未”三合木局及壬水根气坍缩。
    """
    # 1. 加载配置 (V10.0)
    config = DEFAULT_FULL_ALGO_PARAMS.copy()
    config_path = 'config/parameters.json'
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
                # 深度合并简单版本
                for section, content in user_config.items():
                    if section in config and isinstance(content, dict):
                        config[section].update(content)
                    else:
                        config[section] = content
            print(f"✅ 成功加载最新配置: {config_path}")
        except Exception as e:
            print(f"⚠️ 无法加载用户配置，使用默认值: {e}")
    else:
        print("ℹ️ 未找到 parameters.json，使用代码默认参数。")

    # 2. 定义乔布斯案例 (Steve Jobs)
    # 乙未 / 戊寅 / 壬午 / 辛亥
    case = {
        'id': 'Steve_Jobs',
        'bazi': ['乙未', '戊寅', '壬午', '辛亥'], # 年月日时
        'day_master': '壬',
        'gender': '男'
    }

    print(f"\n🔬 启动动态仿真: {case['id']}")
    print(f"📅 八字: {' '.join(case['bazi'])}")
    
    # 3. 初始化验证器 (内部持有 GraphNetworkEngine)
    verifier = Phase2Verifier(config)
    
    # 4. 定义流年序列 (2010-2012)
    # 2010 (庚寅), 2011 (辛卯), 2012 (壬辰)
    years = [
        {'year': 2010, 'pillar': '庚寅'},
        {'year': 2011, 'pillar': '辛卯'},
        {'year': 2012, 'pillar': '壬辰'}
    ]
    
    results = []

    print("-" * 65)
    print(f"{'年份':<6} | {'流年':<6} | {'金(印)':<10} | {'水(身)':<10} | {'火(财)':<10} | {'木(伤)':<10}")
    print("-" * 65)

    for y in years:
        # 重载引擎并注入流年 (标准的 V10.0 调用方式)
        # initialize_nodes 会自动处理流年节点创建及权重分配 (liunian_power)
        verifier.engine.initialize_nodes(
            bazi=case['bazi'], 
            day_master=case['day_master'],
            year_pillar=y['pillar']
        )
        
        # 重新建立连接 (Adjacency & Entanglement)
        # 注意：这会自动触发 V10.0 的 Group H (解冲) 和 Group G (三会) 检查
        verifier.engine.build_adjacency_matrix()
        
        # 运行量子纠缠处理器 (核心：检测亥卯未三合局)
        verifier.engine._apply_quantum_entanglement_once()
        
        # 能量传播 (V9.8 版本)
        verifier.engine.propagate(max_iterations=1, damping=1.0)
        
        # 提取五行能量和并打印调试信息
        energy_sum = {
            'metal': 0.0, 'water': 0.0, 'wood': 0.0, 'fire': 0.0, 'earth': 0.0
        }
        print(f"\n🔍 {y['year']}年 节点状态明细:")
        for node in verifier.engine.nodes:
            if node.element in energy_sum:
                energy_sum[node.element] += node.current_energy.mean
            print(f"   - {node.char}({node.node_type}) | 元素: {node.element:<6} | 能量: {node.current_energy.mean:.2f} | 锁定: {getattr(node, 'is_locked', False)}")
        
        total_e = sum(v for v in energy_sum.values())
        water_ratio = energy_sum['water'] / total_e if total_e > 0 else 0
        print(f"   >>> 水能量总和: {energy_sum['water']:.2f} | 占比: {water_ratio*100:.2f}%")

        
        results.append({
            'year': y['year'],
            'pillar': y['pillar'],
            **energy_sum
        })
        
        print(f"{y['year']:<6} | {y['pillar']:<6} | {energy_sum['metal']:<10.2f} | {energy_sum['water']:<10.2f} | {energy_sum['fire']:<10.2f} | {energy_sum['wood']:<10.2f}")

    print("-" * 65)
    
    # 5. 分析 2011 年的剧变
    df = pd.DataFrame(results)
    e_2010 = df[df['year'] == 2010].iloc[0]
    e_2011 = df[df['year'] == 2011].iloc[0]
    
    water_drop = (e_2011['water'] - e_2010['water']) / e_2010['water']
    wood_increase = (e_2011['wood'] - e_2010['wood']) / e_2010['wood']
    
    print(f"\n📊 2011年(辛卯) 水能量变化: {water_drop*100:+.2f}%")
    print(f"📊 2011年(辛卯) 木能量变化: {wood_increase*100:+.2f}%")
    
    if water_drop < -0.15: # 根气转化的显著标志
        print("\n✅ 验证通过：检测到严重的结构性坍缩 (Structural Collapse)。")
        print("   原因分析：辛卯流年触发'亥卯未'三合局，壬水唯一的实根'亥'被强制转化为木，导致主体能量急剧流失。")
    else:
        print("\n❌ 验证警告：能量震荡不足。可能原因：三合局未正确化神或参数归一化漂移。")

if __name__ == "__main__":
    run_simulation()
