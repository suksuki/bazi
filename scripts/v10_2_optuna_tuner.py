#!/usr/bin/env python3
"""
V10.2 自动调优系统：Optuna + MCP Agentic Workflow
===================================================

核心架构：
- Optuna (TPE + Pruning): 负责参数搜索的"微操"
- MCP Server: 负责与LLM/Cursor的"对话"
- Agent Loop: 实现"观察-思考-行动"的智能调优循环

使用方法：
    # 自动调优（完整流程）
    python3 scripts/v10_2_optuna_tuner.py --mode auto
    
    # 指定层调优
    python3 scripts/v10_2_optuna_tuner.py --mode tune --layer structure --trials 50
"""

import argparse
import json
import sys
import copy
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import random
from dataclasses import dataclass
import logging

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    import optuna
    from optuna.trial import Trial
    from optuna.pruners import MedianPruner
    from optuna.samplers import TPESampler
except ImportError:
    print("❌ 请安装 optuna: pip install optuna")
    sys.exit(1)

from controllers.quantum_lab_controller import QuantumLabController
from core.config_schema import DEFAULT_FULL_ALGO_PARAMS
from scripts.strength_parameter_tuning import StrengthParameterTuner

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


@dataclass
class OptimizationConfig:
    """优化配置"""
    focus_layer: str = "all"  # "physics" | "structure" | "threshold" | "all"
    constraints: str = "soft"  # "strict" | "soft"
    target_case_type: str = "all"  # "classic" | "modern" | "all"
    n_trials: int = 50
    timeout: Optional[float] = None  # 秒
    pruner_enabled: bool = True
    verbose: bool = True
    # [V10.2 核心分析师建议] 交叉验证选项
    cross_validation: bool = False  # 是否启用交叉验证
    cv_splits: int = 3  # 交叉验证折数（如果启用）
    train_ratio: float = 0.7  # 训练集比例（如果启用交叉验证）
    # 🧪 压力测试模式（Cross-Validation）
    use_cross_validation: bool = False  # 是否使用交叉验证
    cv_train_ratio: float = 0.7  # 训练集比例（0.7 = 70%训练，30%验证）


class StrengthOptimizationObjective:
    """
    Optuna优化目标函数
    
    实现：
    1. 加权损失函数（经典案例3倍权重）
    2. 物理常识软惩罚（Bayesian Prior Penalty）
    3. 分层参数空间定义
    """
    
    def __init__(self, 
                 tuner: StrengthParameterTuner,
                 config: OptimizationConfig,
                 base_config: Dict[str, Any]):
        self.tuner = tuner
        self.config = config
        self.base_config = copy.deepcopy(base_config)
        self.best_score = float('inf')
        self.best_trial = None
        
    def _calculate_bayesian_penalty(self, trial_config: Dict[str, Any]) -> float:
        """
        计算贝叶斯先验惩罚（物理常识约束）
        
        惩罚项：
        1. hour_weight > month_weight: 违反物理直觉
        2. structure.rootingWeight > 3.0: 通根权重过高
        3. structure.samePillarBonus > 2.5: 同柱加成过高
        
        Returns:
            penalty: 惩罚值（越大越差，会被加到loss上）
        """
        penalty = 0.0
        
        # 1. 检查月令与时柱权重关系
        pillar_weights = trial_config.get('physics', {}).get('pillarWeights', {})
        month_weight = pillar_weights.get('month', 1.2)
        hour_weight = pillar_weights.get('hour', 0.9)
        
        if hour_weight > month_weight:
            # 违反物理直觉：时柱权重大于月令
            violation = hour_weight - month_weight
            penalty += violation * 100.0  # 惩罚系数
            if self.config.verbose:
                logger.warning(f"⚠️  物理约束违反: hour_weight({hour_weight:.3f}) > month_weight({month_weight:.3f}), 惩罚: {penalty:.2f}")
        
        # 2. 检查通根权重
        structure = trial_config.get('structure', {})
        rooting_weight = structure.get('rootingWeight', 1.2)
        if rooting_weight > 3.0:
            violation = rooting_weight - 3.0
            penalty += violation * 50.0
            
        # 3. 检查同柱加成
        same_pillar_bonus = structure.get('samePillarBonus', 1.6)
        if same_pillar_bonus > 2.5:
            violation = same_pillar_bonus - 2.5
            penalty += violation * 50.0
        
        return penalty
    
    def _calculate_weighted_loss(self, result: Dict[str, Any]) -> float:
        """
        计算加权损失函数
        
        损失 = 1 - 加权匹配率 + 贝叶斯惩罚
        
        Args:
            result: evaluate_parameter_set的返回结果
            
        Returns:
            loss: 损失值（越小越好）
        """
        # 加权匹配率（已经考虑了案例权重）
        weighted_match_rate = result.get('match_rate', 0.0) / 100.0  # 转换为0-1
        
        # 损失 = 1 - 匹配率（匹配率越高，损失越小）
        base_loss = 1.0 - weighted_match_rate
        
        return base_loss
    
    def _setup_cross_validation(self):
        """
        🧪 设置交叉验证（压力测试模式）
        
        将案例随机切分为训练集和验证集，防止过拟合
        """
        import random
        random.seed(42)  # 可复现
        
        total_cases = len(self.tuner.cases)
        train_size = int(total_cases * self.config.cv_train_ratio)
        
        # 随机打乱索引
        indices = list(range(total_cases))
        random.shuffle(indices)
        
        # 切分
        self.cv_train_indices = indices[:train_size]
        self.cv_val_indices = indices[train_size:]
        
        logger.info(f"🧪 Cross-Validation设置: 训练集={len(self.cv_train_indices)}个, 验证集={len(self.cv_val_indices)}个")
    
    def __call__(self, trial: Trial) -> float:
        """
        Optuna目标函数
        
        Args:
            trial: Optuna试验对象
            
        Returns:
            loss: 损失值（Optuna会最小化这个值）
        """
        # 1. 根据focus_layer建议参数
        trial_config = self._suggest_parameters(trial)
        
        # 2. 评估参数组合
        if self.config.use_cross_validation:
            # 🧪 Cross-Validation模式：只在训练集上优化，在验证集上评估
            # （这里简化处理：实际应该在tuner层面支持subset评估）
            result = self.tuner.evaluate_parameter_set(trial_config)
            # TODO: 未来可以在tuner中实现subset评估，真正支持CV
        else:
            result = self.tuner.evaluate_parameter_set(trial_config)
        
        # 3. 计算基础损失（加权匹配率）
        base_loss = self._calculate_weighted_loss(result)
        
        # 4. 计算贝叶斯惩罚（物理约束）
        if self.config.constraints == "soft":
            penalty = self._calculate_bayesian_penalty(trial_config)
        else:
            # strict模式：违反物理约束直接返回巨大损失
            penalty = self._calculate_bayesian_penalty(trial_config)
            if penalty > 0.1:  # 有显著违反
                return 1e6  # 返回巨大损失，让Optuna避开这个区域
        
        # 5. 总损失 = 基础损失 + 惩罚
        total_loss = base_loss + penalty
        
        # 6. 记录最佳结果
        if total_loss < self.best_score:
            self.best_score = total_loss
            self.best_trial = {
                'trial_number': trial.number,
                'config': copy.deepcopy(trial_config),
                'result': copy.deepcopy(result),
                'loss': total_loss,
                'base_loss': base_loss,
                'penalty': penalty
            }
            if self.config.verbose:
                match_rate = result.get('match_rate', 0.0)
                logger.info(f"🎯 Trial {trial.number}: 匹配率={match_rate:.1f}%, Loss={total_loss:.4f} (base={base_loss:.4f}, penalty={penalty:.4f})")
        
        # 7. 报告中间值（用于Pruning）
        trial.report(total_loss, step=0)
        
        # 8. 检查是否应该剪枝
        if trial.should_prune():
            raise optuna.TrialPruned()
        
        return total_loss
    
    def _suggest_parameters(self, trial: Trial) -> Dict[str, Any]:
        """
        根据focus_layer建议参数空间
        
        Args:
            trial: Optuna试验对象
            
        Returns:
            参数配置字典
        """
        config = copy.deepcopy(self.base_config)
        
        if self.config.focus_layer == "physics":
            # 只优化物理层参数
            config.setdefault('physics', {}).setdefault('pillarWeights', {})
            config['physics']['pillarWeights']['month'] = trial.suggest_float(
                'physics.pillarWeights.month', 1.0, 2.0, log=False
            )
            config['physics']['pillarWeights']['hour'] = trial.suggest_float(
                'physics.pillarWeights.hour', 0.5, 1.5, log=False
            )
            config['physics']['pillarWeights']['year'] = trial.suggest_float(
                'physics.pillarWeights.year', 0.5, 1.5, log=False
            )
            config['physics']['pillarWeights']['day'] = trial.suggest_float(
                'physics.pillarWeights.day', 0.5, 1.5, log=False
            )
            
        elif self.config.focus_layer == "structure":
            # 只优化结构层参数
            config.setdefault('structure', {})
            config['structure']['rootingWeight'] = trial.suggest_float(
                'structure.rootingWeight', 0.8, 2.5, log=False
            )
            config['structure']['exposedBoost'] = trial.suggest_float(
                'structure.exposedBoost', 1.0, 2.5, log=False
            )
            config['structure']['samePillarBonus'] = trial.suggest_float(
                'structure.samePillarBonus', 1.0, 2.5, log=False
            )
            config['structure']['voidPenalty'] = trial.suggest_float(
                'structure.voidPenalty', 0.0, 1.0, log=False
            )
            
        elif self.config.focus_layer == "threshold":
            # 只优化阈值参数
            config.setdefault('strength', {})
            config['strength']['energy_threshold_center'] = trial.suggest_float(
                'strength.energy_threshold_center', 2.0, 5.0, log=False
            )
            config['strength']['phase_transition_width'] = trial.suggest_float(
                'strength.phase_transition_width', 5.0, 25.0, log=False
            )
            config['strength']['follower_threshold'] = trial.suggest_float(
                'strength.follower_threshold', 0.05, 0.3, log=False
            )
            config['strength']['attention_dropout'] = trial.suggest_float(
                'strength.attention_dropout', 0.0, 0.5, log=False
            )
            
        else:  # "all"
            # 优化所有参数（但可以分层控制范围）
            # Physics层
            config.setdefault('physics', {}).setdefault('pillarWeights', {})
            config['physics']['pillarWeights']['month'] = trial.suggest_float(
                'physics.pillarWeights.month', 1.0, 2.0, log=False
            )
            config['physics']['pillarWeights']['hour'] = trial.suggest_float(
                'physics.pillarWeights.hour', 0.5, 1.5, log=False
            )
            
            # Structure层
            config.setdefault('structure', {})
            config['structure']['rootingWeight'] = trial.suggest_float(
                'structure.rootingWeight', 0.8, 2.5, log=False
            )
            config['structure']['samePillarBonus'] = trial.suggest_float(
                'structure.samePillarBonus', 1.0, 2.5, log=False
            )
            
            # Threshold层
            config.setdefault('strength', {})
            config['strength']['energy_threshold_center'] = trial.suggest_float(
                'strength.energy_threshold_center', 2.0, 5.0, log=False
            )
            config['strength']['follower_threshold'] = trial.suggest_float(
                'strength.follower_threshold', 0.05, 0.3, log=False
            )
        
        return config
    
    def _evaluate_on_cases(self, config: Dict[str, Any], cases: List[Dict]) -> Dict[str, Any]:
        """
        [V10.2 核心分析师建议] 在指定案例集上评估参数
        
        Args:
            config: 参数配置
            cases: 案例列表
            
        Returns:
            评估结果字典
        """
        # 临时替换tuner的cases
        original_cases = self.tuner.cases
        self.tuner.cases = cases
        
        try:
            # 评估
            result = self.tuner.evaluate_parameter_set(config)
        finally:
            # 恢复原始cases
            self.tuner.cases = original_cases
        
        return result


def run_optuna_study(tuner: StrengthParameterTuner,
                     config: OptimizationConfig,
                     base_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    运行Optuna优化研究
    
    Args:
        tuner: 参数调优器
        config: 优化配置
        base_config: 基础配置
        
    Returns:
        优化结果字典
    """
    # 创建目标函数
    objective = StrengthOptimizationObjective(tuner, config, base_config)
    
    # 创建Study
    study_name = f"strength_tuning_{config.focus_layer}"
    sampler = TPESampler(seed=42)  # 可复现
    
    pruner = MedianPruner(n_startup_trials=5, n_warmup_steps=10) if config.pruner_enabled else None
    
    study = optuna.create_study(
        study_name=study_name,
        direction='minimize',  # 最小化损失
        sampler=sampler,
        pruner=pruner
    )
    
    # 运行优化
    logger.info(f"🚀 开始Optuna优化: {config.focus_layer}层, {config.n_trials}次试验")
    
    try:
        study.optimize(
            objective,
            n_trials=config.n_trials,
            timeout=config.timeout,
            show_progress_bar=config.verbose
        )
    except KeyboardInterrupt:
        logger.warning("⚠️  优化被用户中断")
    
    # 提取最佳结果
    best_trial = study.best_trial
    best_params = best_trial.params
    best_value = best_trial.value
    
    # 重新评估最佳参数（使用objective中保存的最佳配置）
    if objective.best_trial and 'config' in objective.best_trial:
        best_config = objective.best_trial['config']
        final_result = objective.best_trial.get('result')
        if final_result is None:
            # 如果没有保存结果，重新评估
            final_result = tuner.evaluate_parameter_set(best_config)
    else:
        # 如果没有保存，重新构建配置（fallback）
        # 需要使用best_trial来重新建议参数
        best_config = objective._suggest_parameters(best_trial)
        final_result = tuner.evaluate_parameter_set(best_config)
    
    return {
        'study': study,
        'best_trial': best_trial,
        'best_params': best_params,
        'best_loss': best_value,
        'best_match_rate': final_result.get('match_rate', 0.0),
        'final_result': final_result,
        'best_config': best_config,
        'objective_best': objective.best_trial
    }


def main():
    parser = argparse.ArgumentParser(description="V10.2 Optuna自动调优系统")
    parser.add_argument('--mode', type=str, default='auto',
                       choices=['auto', 'tune', 'test'],
                       help='运行模式: auto=自动调优, tune=指定层调优, test=测试')
    parser.add_argument('--layer', type=str, default='all',
                       choices=['physics', 'structure', 'threshold', 'all'],
                       help='调优层: physics/structure/threshold/all')
    parser.add_argument('--trials', type=int, default=50,
                       help='Optuna试验次数')
    parser.add_argument('--constraints', type=str, default='soft',
                       choices=['strict', 'soft'],
                       help='约束模式: strict=严格约束, soft=软惩罚')
    parser.add_argument('--timeout', type=float, default=None,
                       help='超时时间（秒）')
    parser.add_argument('--no-pruner', action='store_true',
                       help='禁用Pruning')
    
    args = parser.parse_args()
    
    # 初始化调优器
    tuner = StrengthParameterTuner()
    base_config = copy.deepcopy(DEFAULT_FULL_ALGO_PARAMS)
    
    if args.mode == 'test':
        # 测试当前配置
        result = tuner.evaluate_parameter_set(base_config)
        print(f"📊 当前配置性能:")
        print(f"   匹配率: {result['match_rate']:.1f}%")
        print(f"   匹配案例数: {result['matched_cases']}/{result['total_cases']}")
        return
    
    # 创建优化配置
    config = OptimizationConfig(
        focus_layer=args.layer,
        constraints=args.constraints,
        n_trials=args.trials,
        timeout=args.timeout,
        pruner_enabled=not args.no_pruner,
        verbose=True
    )
    
    # 运行优化
    opt_result = run_optuna_study(tuner, config, base_config)
    
    # 输出结果
    print("\n" + "="*80)
    print("🎯 Optuna优化完成！")
    print("="*80)
    print(f"最佳匹配率: {opt_result['best_match_rate']:.1f}%")
    print(f"最佳损失值: {opt_result['best_loss']:.4f}")
    print(f"\n最佳参数:")
    for param_name, param_value in opt_result['best_params'].items():
        print(f"  {param_name}: {param_value:.4f}")
    
    # 保存最佳配置
    output_path = project_root / "config" / "optuna_best_params.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(opt_result['best_config'], f, ensure_ascii=False, indent=2)
    print(f"\n✅ 最佳配置已保存到: {output_path}")


if __name__ == '__main__':
    main()

