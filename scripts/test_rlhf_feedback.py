#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RLHF 强化学习反馈测试脚本
========================

测试 V10.0 新增的 RLHF 功能，验证基于真实案例反馈的自适应进化。
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.rlhf_feedback import RewardModel, AdaptiveParameterTuner, RLHFTrainer
from controllers.wealth_verification_controller import WealthVerificationController
from core.engine_graph import GraphNetworkEngine

def print_section(title: str, char: str = "="):
    """打印分节标题"""
    print(f"\n{char * 80}")
    print(f"  {title}")
    print(f"{char * 80}\n")

def test_rlhf_feedback():
    """测试 RLHF 反馈功能"""
    print_section("🔬 RLHF 强化学习反馈测试", "=")
    
    # 初始化组件
    from core.config_schema import DEFAULT_FULL_ALGO_PARAMS
    controller = WealthVerificationController()
    engine = GraphNetworkEngine(config=DEFAULT_FULL_ALGO_PARAMS)
    rlhf_trainer = RLHFTrainer()
    
    # 获取 Jason 案例
    all_cases = controller.get_all_cases()
    jason_cases = [c for c in all_cases if hasattr(c, 'id') and c.id.startswith('JASON_')]
    
    print(f"找到 {len(jason_cases)} 个 Jason 案例用于 RLHF 训练")
    print()
    
    # 测试 1: 奖励模型
    print_section("测试 1: 奖励模型计算", "-")
    
    reward_model = RewardModel()
    
    # 测试不同误差的奖励
    test_cases = [
        (100.0, 100.0, "完美匹配"),
        (100.0, 95.0, "误差 5.0"),
        (100.0, 85.0, "误差 15.0"),
        (100.0, 75.0, "误差 25.0"),
        (100.0, 50.0, "误差 50.0")
    ]
    
    for pred, real, desc in test_cases:
        reward = reward_model.calculate_reward(pred, real)
        error = abs(pred - real)
        print(f"  {desc}: 预测={pred:.1f}, 真实={real:.1f}, 误差={error:.1f}, 奖励={reward:.2f}")
    print()
    
    # 测试 2: 批量奖励计算
    print_section("测试 2: 批量奖励计算", "-")
    
    # 使用 Jason D 案例
    jason_d = next((c for c in jason_cases if c.id == 'JASON_D_T1961_1010'), None)
    
    if jason_d:
        predictions = []
        reals = []
        
        for event in jason_d.timeline or []:
            year = event.year
            ganzhi = event.ganzhi if hasattr(event, 'ganzhi') else ''
            dayun = event.dayun if hasattr(event, 'dayun') else ''
            real_magnitude = event.real_magnitude if hasattr(event, 'real_magnitude') else 0.0
            
            if not ganzhi:
                continue
            
            # 计算预测值
            wealth_result = engine.calculate_wealth_index(
                bazi=jason_d.bazi,
                day_master=jason_d.day_master,
                gender=jason_d.gender,
                luck_pillar=dayun,
                year_pillar=ganzhi
            )
            
            predicted = wealth_result.get('wealth_index', 0.0)
            predictions.append(predicted)
            reals.append(real_magnitude)
        
        # 计算批量奖励
        batch_reward = reward_model.calculate_batch_reward(predictions, reals)
        
        print(f"  案例: {jason_d.name}")
        print(f"  事件数: {batch_reward['total_count']}")
        print(f"  正确数: {batch_reward['correct_count']}")
        print(f"  命中率: {batch_reward['hit_rate'] * 100:.1f}%")
        print(f"  总奖励: {batch_reward['total_reward']:.2f}")
        print(f"  平均奖励: {batch_reward['avg_reward']:.2f}")
        print(f"  命中率加成: {batch_reward['hit_rate_bonus']:.2f}")
        print(f"  最终奖励: {batch_reward['final_reward']:.2f}")
        print()
    
    # 测试 3: 自适应参数调优
    print_section("测试 3: 自适应参数调优", "-")
    
    tuner = AdaptiveParameterTuner()
    
    # 初始参数
    current_params = {
        'threshold': 0.5,
        'scale': 10.0,
        'phase_point': 0.5
    }
    
    parameter_ranges = {
        'threshold': (0.4, 0.6),
        'scale': (5.0, 15.0),
        'phase_point': (0.4, 0.6)
    }
    
    print(f"  初始参数: {current_params}")
    
    # 模拟多次调优
    for i in range(5):
        # 模拟奖励（正奖励表示好，负奖励表示差）
        reward = 1.0 if i < 3 else -0.5
        
        current_params = tuner.tune_parameters(
            current_params=current_params,
            reward=reward,
            parameter_ranges=parameter_ranges
        )
        
        print(f"  迭代 {i+1}: 奖励={reward:.2f}, 参数={current_params}")
    
    # 获取最佳参数
    best_params = tuner.get_best_parameters()
    print(f"  历史最佳参数: {best_params}")
    print()
    
    # 测试 4: RLHF 训练器
    print_section("测试 4: RLHF 训练器", "-")
    
    if jason_d:
        # 准备预测和真实数据
        predictions_data = []
        reals_data = []
        
        for event in jason_d.timeline or []:
            year = event.year
            ganzhi = event.ganzhi if hasattr(event, 'ganzhi') else ''
            dayun = event.dayun if hasattr(event, 'dayun') else ''
            real_magnitude = event.real_magnitude if hasattr(event, 'real_magnitude') else 0.0
            
            if not ganzhi:
                continue
            
            wealth_result = engine.calculate_wealth_index(
                bazi=jason_d.bazi,
                day_master=jason_d.day_master,
                gender=jason_d.gender,
                luck_pillar=dayun,
                year_pillar=ganzhi
            )
            
            predictions_data.append({
                'year': year,
                'wealth_index': wealth_result.get('wealth_index', 0.0)
            })
            
            reals_data.append({
                'year': year,
                'real_magnitude': real_magnitude
            })
        
        # 从反馈中学习
        learning_result = rlhf_trainer.learn_from_feedback(
            case_id=jason_d.id,
            predictions=predictions_data,
            reals=reals_data
        )
        
        print(f"  案例: {jason_d.name}")
        print(f"  学习结果: {learning_result}")
        print(f"  反馈历史记录数: {len(rlhf_trainer.feedback_history)}")
        print()
    
    print("✅ RLHF 强化学习反馈测试完成！")
    
    return {
        'reward_model': reward_model,
        'tuner': tuner,
        'rlhf_trainer': rlhf_trainer
    }

if __name__ == '__main__':
    try:
        result = test_rlhf_feedback()
        print(f"\n✅ 脚本执行成功！")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 脚本执行失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

