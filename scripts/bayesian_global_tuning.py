#!/usr/bin/env python3
"""
Jason B 全局加权平衡优化脚本
============================

使用加权损失函数进行全局优化，防止过拟合
权重分配：1999 (50%) : 2007 (10%) : 2014 (40%)

作者: Antigravity Team
版本: V10.0
日期: 2025-12-17
"""

import sys
import json
import numpy as np
import logging
from pathlib import Path
from typing import Dict, Tuple

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.engine_graph import GraphNetworkEngine
from core.config_schema import DEFAULT_FULL_ALGO_PARAMS
from core.bayesian_optimization import BayesianOptimizer
import copy


class WeightedOptimizationObjective:
    """
    加权优化目标函数
    """
    
    def __init__(self, case_data: Dict, weights: Tuple[float, float, float] = (0.5, 0.1, 0.4)):
        """
        初始化目标函数
        
        Args:
            case_data: 案例数据
            weights: 权重分配 (1999, 2007, 2014)
        """
        self.case_data = case_data
        self.weights = weights
        logger.info(f"✅ 初始化加权优化目标：{case_data['name']}")
        logger.info(f"   权重分配: 1999={weights[0]}, 2007={weights[1]}, 2014={weights[2]}")
    
    def __call__(self, seal_bonus: float, seal_multiplier: float,
                 clash_damping_limit: float, seal_conduction_multiplier: float,
                 opportunity_scaling: float) -> float:
        """
        计算加权目标函数值（损失）
        
        Args:
            seal_bonus: 印星帮身直接加成（0-50）
            seal_multiplier: 印星帮身乘数（0.8-1.2）
            clash_damping_limit: 身强时冲提纲减刑系数（0.1-0.3）
            seal_conduction_multiplier: 印星传导乘数（1.0-2.0）
            opportunity_scaling: 机会加成缩放比例（0.5-2.0）
        
        Returns:
            加权损失值（越小越好）
        """
        total_weighted_loss = 0.0
        
        for idx, event in enumerate(self.case_data['timeline']):
            year = event.get('year')
            real_wealth = event.get('real_magnitude', 0.0)
            year_pillar = event.get('ganzhi', '')
            luck_pillar = event.get('dayun', '')
            
            # 获取权重
            if year == 1999:
                weight = self.weights[0]
            elif year == 2007:
                weight = self.weights[1]
            elif year == 2014:
                weight = self.weights[2]
            else:
                weight = 1.0 / len(self.case_data['timeline'])
            
            # 创建配置
            config = copy.deepcopy(DEFAULT_FULL_ALGO_PARAMS)
            
            # 计算预测值
            engine = GraphNetworkEngine(config=config)
            result = engine.calculate_wealth_index(
                bazi=self.case_data['bazi'],
                day_master=self.case_data['day_master'],
                gender=self.case_data['gender'],
                luck_pillar=luck_pillar,
                year_pillar=year_pillar
            )
            
            if isinstance(result, dict):
                predicted = result.get('wealth_index', 0.0)
                details = result.get('details', [])
            else:
                predicted = float(result)
                details = []
            
            # [V10.0] 应用优化参数（后处理模拟）
            # 检查是否有印星帮身
            has_seal_help = any('印星' in d or '印' in d for d in details)
            
            if has_seal_help:
                # 应用印星加成
                predicted = predicted + seal_bonus
                predicted = predicted * seal_multiplier
            
            # 检查是否有冲提纲转为机会
            has_clash_opportunity = any('冲提纲(身强+印星通关，转为机会)' in d for d in details)
            if has_clash_opportunity:
                # 应用机会加成缩放
                base_opportunity = 40.0
                opportunity_bonus = base_opportunity * opportunity_scaling
                predicted = predicted - base_opportunity + opportunity_bonus  # 替换基础加成
            
            # 检查是否有食神制杀
            has_output_officer = any('食神制杀' in d or '触发：食神制杀' in d for d in details)
            if has_output_officer:
                # 应用印星传导乘数
                predicted = predicted * seal_conduction_multiplier
            
            # 计算误差
            error = (predicted - real_wealth) ** 2
            
            # 加权损失
            weighted_error = error * weight
            total_weighted_loss += weighted_error
            
            logger.debug(f"  {year}年: 预测={predicted:.2f}, 真实={real_wealth:.2f}, 误差={error:.2f}, 权重={weight:.2f}, 加权误差={weighted_error:.2f}")
        
        return total_weighted_loss


def load_jason_b_case() -> Dict:
    """加载 Jason B 案例数据"""
    case_file = project_root / "calibration_cases.json"
    if case_file.exists():
        with open(case_file, 'r', encoding='utf-8') as f:
            cases = json.load(f)
            for case in cases:
                if case.get('id', '').startswith('JASON_B'):
                    return case
    
    # 使用默认数据
    return {
        'id': 'JASON_B_T1964_0910',
        'name': 'Jason B (身弱用印)',
        'bazi': ['甲辰', '癸酉', '己亥', '戊辰'],
        'day_master': '己',
        'gender': '男',
        'timeline': [
            {'year': 1999, 'ganzhi': '己卯', 'dayun': '丁丑', 'real_magnitude': 100.0},
            {'year': 2007, 'ganzhi': '丁亥', 'dayun': '戊寅', 'real_magnitude': 70.0},
            {'year': 2014, 'ganzhi': '甲午', 'dayun': '己卯', 'real_magnitude': 100.0}
        ]
    }


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Jason B 全局加权平衡优化')
    parser.add_argument('--iterations', type=int, default=50,
                       help='优化迭代次数（默认: 50）')
    parser.add_argument('--weights', type=str, default='0.5,0.1,0.4',
                       help='权重分配（1999,2007,2014），默认: 0.5,0.1,0.4')
    parser.add_argument('--output', type=str, default=None,
                       help='输出目录路径（默认: reports/）')
    
    args = parser.parse_args()
    
    # 解析权重
    weight_strs = args.weights.split(',')
    weights = tuple(float(w) for w in weight_strs)
    if len(weights) != 3:
        logger.error("权重必须包含3个值（1999, 2007, 2014）")
        return
    
    # 加载案例数据
    case_data = load_jason_b_case()
    logger.info(f"✅ 加载案例: {case_data['name']}")
    
    # 创建目标函数
    objective = WeightedOptimizationObjective(case_data, weights=weights)
    
    # 定义参数范围
    parameter_bounds = {
        'seal_bonus': (0.0, 50.0),              # 印星帮身直接加成
        'seal_multiplier': (0.8, 1.2),          # 印星帮身乘数
        'clash_damping_limit': (0.1, 0.3),      # 身强时冲提纲减刑系数（暂未使用）
        'seal_conduction_multiplier': (1.0, 2.0),  # 印星传导乘数
        'opportunity_scaling': (0.5, 2.0)       # 机会加成缩放比例
    }
    
    # 创建包装函数
    def wrapped_objective(params_dict: Dict[str, float]) -> float:
        """包装目标函数，使其接受参数字典"""
        return objective(
            params_dict['seal_bonus'],
            params_dict['seal_multiplier'],
            params_dict['clash_damping_limit'],
            params_dict['seal_conduction_multiplier'],
            params_dict['opportunity_scaling']
        )
    
    # 创建贝叶斯优化器
    optimizer = BayesianOptimizer(
        parameter_bounds=parameter_bounds,
        acquisition_func='ei',
        n_initial_samples=10
    )
    
    logger.info("=" * 80)
    logger.info("🎯 开始全局加权平衡优化")
    logger.info("=" * 80)
    
    # 执行优化
    best_params = optimizer.optimize(wrapped_objective, n_iterations=args.iterations)
    
    # 获取最优损失
    best_loss = optimizer.best_value if optimizer.best_value != float('inf') else min(optimizer.y_history) if optimizer.y_history else float('inf')
    
    # 输出结果
    print("\n" + "=" * 80)
    print("📊 全局加权平衡优化结果")
    print("=" * 80)
    print(f"权重分配: 1999={weights[0]}, 2007={weights[1]}, 2014={weights[2]}")
    print(f"最优印星帮身直接加成: {best_params['seal_bonus']:.4f}")
    print(f"最优印星帮身乘数: {best_params['seal_multiplier']:.4f}")
    print(f"最优冲提纲减刑系数: {best_params['clash_damping_limit']:.4f}")
    print(f"最优印星传导乘数: {best_params['seal_conduction_multiplier']:.4f}")
    print(f"最优机会加成缩放: {best_params['opportunity_scaling']:.4f}")
    print(f"最优加权损失: {best_loss:.4f}")
    
    # 保存结果
    if args.output:
        output_dir = Path(args.output)
    else:
        output_dir = project_root / "reports"
    output_dir.mkdir(exist_ok=True)
    
    result_file = output_dir / "jason_b_global_tuning_result.json"
    result = {
        'case_id': case_data['id'],
        'case_name': case_data['name'],
        'weights': weights,
        'best_params': {k: float(v) for k, v in best_params.items()},
        'best_loss': float(best_loss),
        'iterations': args.iterations
    }
    
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    logger.info(f"✅ 结果已保存到: {result_file}")
    
    # 验证优化效果
    logger.info("\n" + "=" * 80)
    logger.info("🔍 验证优化效果")
    logger.info("=" * 80)
    
    config = copy.deepcopy(DEFAULT_FULL_ALGO_PARAMS)
    engine = GraphNetworkEngine(config=config)
    
    for event in case_data['timeline']:
        year = event.get('year')
        real_wealth = event.get('real_magnitude', 0.0)
        year_pillar = event.get('ganzhi', '')
        luck_pillar = event.get('dayun', '')
        
        result = engine.calculate_wealth_index(
            bazi=case_data['bazi'],
            day_master=case_data['day_master'],
            gender=case_data['gender'],
            luck_pillar=luck_pillar,
            year_pillar=year_pillar
        )
        
        if isinstance(result, dict):
            predicted = result.get('wealth_index', 0.0)
            details = result.get('details', [])
        else:
            predicted = float(result)
            details = []
        
        # 应用优化后的参数
        has_seal_help = any('印星' in d or '印' in d for d in details)
        if has_seal_help:
            predicted = predicted + best_params['seal_bonus']
            predicted = predicted * best_params['seal_multiplier']
        
        has_clash_opportunity = any('冲提纲(身强+印星通关，转为机会)' in d for d in details)
        if has_clash_opportunity:
            base_opportunity = 40.0
            opportunity_bonus = base_opportunity * best_params['opportunity_scaling']
            predicted = predicted - base_opportunity + opportunity_bonus
        
        has_output_officer = any('食神制杀' in d or '触发：食神制杀' in d for d in details)
        if has_output_officer:
            predicted = predicted * best_params['seal_conduction_multiplier']
        
        error = abs(predicted - real_wealth)
        
        logger.info(f"{year} 年:")
        logger.info(f"  预测值: {predicted:.2f}")
        logger.info(f"  真实值: {real_wealth:.2f}")
        logger.info(f"  误差: {error:.2f}")
    
    print("\n✅ 优化完成！")


if __name__ == '__main__':
    main()

