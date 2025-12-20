#!/usr/bin/env python3
"""
贝叶斯超参数优化 - Jason D 1999年误差修正
==========================================

针对 Jason D 1999 年预测误差（真实值 50.0，预测值 -30.0，误差 80.0）进行贝叶斯优化
调整非线性激活函数的参数，使预测更准确
"""

import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Any
import numpy as np

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.bayesian_optimization import BayesianOptimizer, HyperparameterSensitivityAnalyzer
from core.engine_graph import GraphNetworkEngine
from core.config_schema import DEFAULT_FULL_ALGO_PARAMS
import copy

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class JasonD1999Optimizer:
    """
    Jason D 1999 年误差修正优化器
    使用贝叶斯优化调整非线性激活函数参数
    """
    
    def __init__(self):
        """初始化优化器"""
        # 加载 Jason D 案例数据
        case_file = project_root / "data" / "jason_d_case.json"
        with open(case_file, 'r', encoding='utf-8') as f:
            self.case_data = json.load(f)
        
        # 1999 年真实值
        self.target_year = 1999
        self.target_real_value = 50.0
        
        # 获取 1999 年的事件信息
        event_1999 = next((e for e in self.case_data['timeline'] 
                          if e.get('year') == 1999), None)
        if event_1999:
            self.year_pillar = event_1999.get('ganzhi', '己卯')
            self.luck_pillar = event_1999.get('dayun', '戊戌')
        else:
            self.year_pillar = '己卯'
            self.luck_pillar = '戊戌'
        
        logger.info(f"✅ 初始化优化器")
        logger.info(f"   目标年份: {self.target_year}")
        logger.info(f"   真实值: {self.target_real_value}")
        logger.info(f"   流年: {self.year_pillar}, 大运: {self.luck_pillar}")
    
    def create_objective_function(self) -> callable:
        """
        创建目标函数
        
        Returns:
            目标函数（接受参数字典，返回损失值）
        """
        def objective(params: Dict[str, float]) -> float:
            """
            目标函数：计算预测值与真实值的误差
            
            Args:
                params: 参数字典，包含：
                    - strength_beta: Softplus 的 β 参数
                    - clash_k: Sigmoid 的 k 参数
                    - trine_boost: 三刑增强系数
                    - tunneling_factor: 隧穿概率系数
                    
            Returns:
                损失值（误差的平方）
            """
            # 创建配置
            config = copy.deepcopy(DEFAULT_FULL_ALGO_PARAMS)
            
            # 更新非线性参数
            if 'nonlinear' not in config:
                config['nonlinear'] = {}
            
            # [V10.1] 映射参数名称
            # strength_beta -> scale (Softplus 的缩放因子)
            # clash_k -> steepness (Sigmoid 的陡峭度)
            config['nonlinear']['strength_beta'] = params.get('strength_beta', 10.0)
            config['nonlinear']['scale'] = params.get('strength_beta', 10.0)  # 兼容旧参数名
            config['nonlinear']['clash_k'] = params.get('clash_k', 5.0)
            config['nonlinear']['steepness'] = params.get('clash_k', 5.0)  # 兼容旧参数名
            config['nonlinear']['trine_boost'] = params.get('trine_boost', 0.3)
            config['nonlinear']['tunneling_factor'] = params.get('tunneling_factor', 0.1)
            
            # 启用概率分布（用于不确定性分析）
            config['probabilistic_energy'] = {'use_probabilistic_energy': True}
            
            # 创建引擎
            engine = GraphNetworkEngine(config=config)
            
            # 计算预测值
            try:
                result = engine.calculate_wealth_index(
                    bazi=self.case_data['bazi'],
                    day_master=self.case_data['day_master'],
                    gender=self.case_data['gender'],
                    luck_pillar=self.luck_pillar,
                    year_pillar=self.year_pillar
                )
                
                if isinstance(result, dict):
                    predicted = result.get('wealth_index', 0.0)
                else:
                    predicted = float(result)
                
                # 计算误差（使用平方误差）
                error = (predicted - self.target_real_value) ** 2
                
                logger.debug(f"  参数: {params} -> 预测: {predicted:.2f}, 误差: {error:.2f}")
                
                return error
                
            except Exception as e:
                logger.error(f"计算失败: {e}")
                return 10000.0  # 返回很大的损失值
        
        return objective
    
    def optimize(self, n_iterations: int = 50) -> Dict[str, float]:
        """
        执行贝叶斯优化
        
        Args:
            n_iterations: 优化迭代次数
            
        Returns:
            最优参数字典
        """
        logger.info("\n" + "="*80)
        logger.info("🎯 开始贝叶斯超参数优化 - Jason D 1999年误差修正")
        logger.info("="*80)
        
        # 定义参数边界
        parameter_bounds = {
            'strength_beta': (5.0, 15.0),      # Softplus 的 β 参数
            'clash_k': (3.0, 7.0),            # Sigmoid 的 k 参数
            'trine_boost': (0.1, 0.5),        # 三刑增强系数
            'tunneling_factor': (0.05, 0.2)   # 隧穿概率系数
        }
        
        logger.info(f"参数空间:")
        for name, (low, high) in parameter_bounds.items():
            logger.info(f"  {name}: [{low}, {high}]")
        
        # 创建优化器
        optimizer = BayesianOptimizer(
            parameter_bounds=parameter_bounds,
            acquisition_func='ei',  # 期望改进
            n_initial_samples=10
        )
        
        # 创建目标函数
        objective = self.create_objective_function()
        
        # 执行优化
        optimal_params = optimizer.optimize(objective, n_iterations=n_iterations)
        
        # 获取优化历史
        params_history, loss_history = optimizer.get_optimization_history()
        
        # 显示优化结果
        logger.info("\n" + "="*80)
        logger.info("📊 优化结果")
        logger.info("="*80)
        logger.info(f"最优参数:")
        for name, value in optimal_params.items():
            logger.info(f"  {name}: {value:.4f}")
        logger.info(f"最优损失: {optimizer.best_value:.4f}")
        logger.info(f"对应误差: {np.sqrt(optimizer.best_value):.2f}")
        
        # 验证最优参数
        logger.info("\n验证最优参数:")
        final_result = objective(optimal_params)
        logger.info(f"最终预测值: {self._get_prediction(optimal_params):.2f}")
        logger.info(f"真实值: {self.target_real_value:.2f}")
        logger.info(f"最终误差: {abs(self._get_prediction(optimal_params) - self.target_real_value):.2f}")
        
        return optimal_params
    
    def _get_prediction(self, params: Dict[str, float]) -> float:
        """获取指定参数下的预测值"""
        config = copy.deepcopy(DEFAULT_FULL_ALGO_PARAMS)
        if 'nonlinear' not in config:
            config['nonlinear'] = {}
        config['nonlinear'].update(params)
        
        engine = GraphNetworkEngine(config=config)
        result = engine.calculate_wealth_index(
            bazi=self.case_data['bazi'],
            day_master=self.case_data['day_master'],
            gender=self.case_data['gender'],
            luck_pillar=self.luck_pillar,
            year_pillar=self.year_pillar
        )
        
        if isinstance(result, dict):
            return result.get('wealth_index', 0.0)
        return float(result)
    
    def sensitivity_analysis(self):
        """
        执行敏感度分析
        分析各个参数对预测结果的影响
        """
        logger.info("\n" + "="*80)
        logger.info("📈 超参数敏感度分析")
        logger.info("="*80)
        
        # 基础参数（使用默认值）
        base_params = {
            'strength_beta': 10.0,
            'clash_k': 5.0,
            'trine_boost': 0.3,
            'tunneling_factor': 0.1
        }
        
        # 创建分析器
        analyzer = HyperparameterSensitivityAnalyzer(base_params)
        
        # 定义参数范围
        parameter_ranges = {
            'strength_beta': np.linspace(5.0, 15.0, 20),
            'clash_k': np.linspace(3.0, 7.0, 20),
            'trine_boost': np.linspace(0.1, 0.5, 20),
            'tunneling_factor': np.linspace(0.05, 0.2, 20)
        }
        
        # 创建目标函数
        objective = self.create_objective_function()
        
        # 分析所有参数
        results = analyzer.analyze_all(objective, parameter_ranges)
        
        # 显示结果
        for param_name, result in results.items():
            logger.info(f"\n参数: {param_name}")
            logger.info(f"  最优值: {result['optimal_value']:.4f}")
            logger.info(f"  最优损失: {np.min(result['losses']):.4f}")
            logger.info(f"  敏感度范围: [{np.min(result['sensitivity']):.4f}, {np.max(result['sensitivity']):.4f}]")
        
        return results


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='贝叶斯超参数优化 - Jason D 1999年')
    parser.add_argument('--iterations', type=int, default=50,
                       help='优化迭代次数（默认: 50）')
    parser.add_argument('--sensitivity', action='store_true',
                       help='执行敏感度分析')
    parser.add_argument('--output', type=str, default=None,
                       help='输出文件路径（JSON格式）')
    
    args = parser.parse_args()
    
    # 创建优化器
    optimizer = JasonD1999Optimizer()
    
    # 执行优化
    optimal_params = optimizer.optimize(n_iterations=args.iterations)
    
    # 敏感度分析（可选）
    if args.sensitivity:
        optimizer.sensitivity_analysis()
    
    # 保存结果
    if args.output:
        output_path = Path(args.output)
        result = {
            'target_year': 1999,
            'target_real_value': 50.0,
            'optimal_parameters': optimal_params,
            'final_error': abs(optimizer._get_prediction(optimal_params) - 50.0)
        }
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        logger.info(f"✅ 结果已保存到: {output_path}")
    else:
        # 默认保存
        reports_dir = project_root / "reports"
        reports_dir.mkdir(exist_ok=True)
        output_path = reports_dir / "jason_d_1999_bayesian_optimization.json"
        result = {
            'target_year': 1999,
            'target_real_value': 50.0,
            'optimal_parameters': optimal_params,
            'final_error': abs(optimizer._get_prediction(optimal_params) - 50.0)
        }
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        logger.info(f"✅ 结果已保存到: {output_path}")
    
    print("\n" + "="*80)
    print("✅ 优化完成！")
    print("="*80)
    print(f"最优参数: {optimal_params}")
    print(f"最终误差: {result['final_error']:.2f}")


if __name__ == '__main__':
    main()

