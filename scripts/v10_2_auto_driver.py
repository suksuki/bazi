#!/usr/bin/env python3
"""
V10.2 自动驾驶主程序：Agentic Bazi Tuner
=========================================

实现"观察-思考-行动"的智能调优循环：
1. 观察 (Context Injection): 运行诊断，获取当前状态
2. 思考 (LLM Reasoning): 分析问题，决定下一步行动
3. 行动 (Action): 执行Optuna优化
4. 反馈与迭代: 评估结果，继续优化

使用方法：
    python3 scripts/v10_2_auto_driver.py --mode auto
    python3 scripts/v10_2_auto_driver.py --mode phase1  # 只运行Phase 1
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime
import shutil

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.v10_2_mcp_server import MCPTuningServer
from scripts.strength_parameter_tuning import StrengthParameterTuner
from core.config_schema import DEFAULT_FULL_ALGO_PARAMS
from core.models.config_model import ConfigModel
import copy

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


class AutoDriver:
    """
    自动驾驶调优器
    
    实现分层锁定策略：
    - Phase 1: 物理层调优（锁定基础权重）
    - Phase 2: 结构层调优（锁定结构参数）
    - Phase 3: 阈值微调（最终优化）
    
    [V10.2 核心分析师建议] 参数时光机机制：
    - 每个Phase完成后自动保存Checkpoint
    - 支持Auto-Rollback（如果后续Phase导致性能下降）
    """
    
    def __init__(self, checkpoint_dir: Optional[Path] = None):
        self.server = MCPTuningServer()
        self.tuner = StrengthParameterTuner()
        self.config_model = ConfigModel()
        self.frozen_params = {}  # 已锁定的参数
        
        # [V10.2 核心分析师建议] Checkpoints机制
        if checkpoint_dir is None:
            checkpoint_dir = project_root / "config" / "checkpoints"
        self.checkpoint_dir = checkpoint_dir
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.checkpoints = {}  # 存储各Phase的checkpoint信息: {phase: {'match_rate': float, 'config': dict}}
        self.checkpoint_dir = project_root / "config" / "checkpoints"
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.checkpoints = {}  # 保存的检查点：{phase: {config, match_rate}}
        
    def run_phase1_physics(self, n_trials: int = 50, target_match_rate: float = 47.0) -> Dict[str, Any]:
        """
        Phase 1: 物理层调优
        
        目标：
        - 优化月令、时柱等基础权重
        - 确保物理约束不被违反
        - 达到目标匹配率（用于经典案例锚定）
        
        Args:
            n_trials: Optuna试验次数
            target_match_rate: 目标匹配率（达到后锁定参数）
            
        Returns:
            Phase 1结果
        """
        logger.info("="*80)
        logger.info("🔬 Phase 1: 物理层调优")
        logger.info("="*80)
        
        # 1. 观察：运行诊断
        diagnosis = self.server.run_physics_diagnosis()
        logger.info(f"📊 初始状态: 匹配率={diagnosis['current_match_rate']:.1f}%")
        
        # 2. 思考：分析问题
        issues = diagnosis.get('main_issues', [])
        logger.info(f"🔍 发现 {len(issues)} 个主要问题")
        
        # 3. 行动：优化物理层
        logger.info("⚙️  配置优化策略: focus_layer=physics, constraints=soft")
        self.server.configure_optimization_strategy(
            focus_layer="physics",
            constraints="soft"
        )
        
        logger.info(f"🚀 开始优化: {n_trials}次试验")
        opt_result = self.server.execute_optuna_study(n_trials=n_trials)
        
        logger.info(f"✅ Phase 1完成: 匹配率={opt_result['best_match_rate']:.1f}%")
        
        # 4. 检查是否达到目标
        phase1_match_rate = opt_result['best_match_rate']
        if phase1_match_rate >= target_match_rate:
            logger.info(f"🎯 达到目标匹配率({target_match_rate:.1f}%)，锁定物理层参数")
            # 锁定物理层参数
            physics_params = self.server.current_config.get('physics', {})
            self.frozen_params['physics'] = copy.deepcopy(physics_params)
            
            # 💾 保存Checkpoint（参数时光机）
            self._save_checkpoint('phase1', phase1_match_rate)
        else:
            logger.warning(f"⚠️  未达到目标匹配率({target_match_rate:.1f}%)，但继续下一步")
        
        return {
            'phase': 1,
            'match_rate': phase1_match_rate,
            'improvement': opt_result.get('improvement', 0.0),
            'frozen': 'physics' in self.frozen_params
        }
    
    def run_phase2_structure(self, n_trials: int = 50, target_match_rate: float = 49.0) -> Dict[str, Any]:
        """
        Phase 2: 结构层调优
        
        目标：
        - 优化通根、透干、同柱等结构参数
        - 解决结构相关案例（如比尔·盖茨）
        - 达到目标匹配率
        
        Args:
            n_trials: Optuna试验次数
            target_match_rate: 目标匹配率
            
        Returns:
            Phase 2结果
        """
        logger.info("="*80)
        logger.info("🏗️  Phase 2: 结构层调优")
        logger.info("="*80)
        
        # 1. 观察
        diagnosis = self.server.run_physics_diagnosis()
        logger.info(f"📊 当前状态: 匹配率={diagnosis['current_match_rate']:.1f}%")
        
        # 2. 锁定物理层参数（如果已锁定）
        if 'physics' in self.frozen_params:
            logger.info("🔒 使用已锁定的物理层参数")
            self.server.current_config['physics'] = copy.deepcopy(self.frozen_params['physics'])
        
        # 3. 优化结构层
        logger.info("⚙️  配置优化策略: focus_layer=structure, constraints=soft")
        self.server.configure_optimization_strategy(
            focus_layer="structure",
            constraints="soft"
        )
        
        logger.info(f"🚀 开始优化: {n_trials}次试验")
        opt_result = self.server.execute_optuna_study(n_trials=n_trials)
        
        logger.info(f"✅ Phase 2完成: 匹配率={opt_result['best_match_rate']:.1f}%")
        
        # 4. 检查是否达到目标
        phase2_match_rate = opt_result['best_match_rate']
        if phase2_match_rate >= target_match_rate:
            logger.info(f"🎯 达到目标匹配率({target_match_rate:.1f}%)，锁定结构层参数")
            structure_params = self.server.current_config.get('structure', {})
            self.frozen_params['structure'] = copy.deepcopy(structure_params)
            
            # 💾 保存Checkpoint（参数时光机）
            self._save_checkpoint('phase2', phase2_match_rate)
        
        # 5. 🔄 Auto-Rollback检查：如果Phase 2导致Phase 1性能回退
        if 'phase1' in self.checkpoints:
            phase1_match_rate = self.checkpoints['phase1']['match_rate']
            if phase2_match_rate < phase1_match_rate - 2.0:  # 回退超过2%
                logger.warning(f"⚠️  Phase 2导致性能回退 (Phase 1: {phase1_match_rate:.1f}% -> Phase 2: {phase2_match_rate:.1f}%)")
                logger.info("🔄 执行Auto-Rollback：回滚到Phase 1检查点")
                self._rollback_to_checkpoint('phase1')
                return {
                    'phase': 2,
                    'match_rate': phase1_match_rate,
                    'improvement': opt_result.get('improvement', 0.0),
                    'frozen': False,
                    'rolled_back': True,
                    'rollback_reason': f'性能回退超过阈值 ({phase1_match_rate:.1f}% -> {phase2_match_rate:.1f}%)'
                }
        
        return {
            'phase': 2,
            'match_rate': phase2_match_rate,
            'improvement': opt_result.get('improvement', 0.0),
            'frozen': 'structure' in self.frozen_params,
            'rolled_back': False
        }
    
    def run_phase3_threshold(self, n_trials: int = 50) -> Dict[str, Any]:
        """
        Phase 3: 阈值微调
        
        目标：
        - 微调energy_threshold_center、follower_threshold等阈值参数
        - 最终优化匹配率
        
        Args:
            n_trials: Optuna试验次数
            
        Returns:
            Phase 3结果
        """
        logger.info("="*80)
        logger.info("🎚️  Phase 3: 阈值微调")
        logger.info("="*80)
        
        # 1. 观察
        diagnosis = self.server.run_physics_diagnosis()
        logger.info(f"📊 当前状态: 匹配率={diagnosis['current_match_rate']:.1f}%")
        
        # 2. 锁定已优化的参数
        if 'physics' in self.frozen_params:
            logger.info("🔒 使用已锁定的物理层参数")
            self.server.current_config['physics'] = copy.deepcopy(self.frozen_params['physics'])
        if 'structure' in self.frozen_params:
            logger.info("🔒 使用已锁定的结构层参数")
            self.server.current_config['structure'] = copy.deepcopy(self.frozen_params['structure'])
        
        # 3. 优化阈值层
        logger.info("⚙️  配置优化策略: focus_layer=threshold, constraints=soft")
        self.server.configure_optimization_strategy(
            focus_layer="threshold",
            constraints="soft"
        )
        
        logger.info(f"🚀 开始优化: {n_trials}次试验")
        opt_result = self.server.execute_optuna_study(n_trials=n_trials)
        
        phase3_match_rate = opt_result['best_match_rate']
        logger.info(f"✅ Phase 3完成: 匹配率={phase3_match_rate:.1f}%")
        
        # 🔄 Auto-Rollback检查：如果Phase 3导致整体性能回退
        best_previous_match_rate = 0.0
        if 'phase2' in self.checkpoints:
            best_previous_match_rate = self.checkpoints['phase2']['match_rate']
        elif 'phase1' in self.checkpoints:
            best_previous_match_rate = self.checkpoints['phase1']['match_rate']
        
        if best_previous_match_rate > 0 and phase3_match_rate < best_previous_match_rate - 2.0:
            logger.warning(f"⚠️  Phase 3导致性能回退 (之前: {best_previous_match_rate:.1f}% -> Phase 3: {phase3_match_rate:.1f}%)")
            logger.info("🔄 执行Auto-Rollback：回滚到最佳检查点")
            rollback_phase = 'phase2' if 'phase2' in self.checkpoints else 'phase1'
            self._rollback_to_checkpoint(rollback_phase)
            return {
                'phase': 3,
                'match_rate': best_previous_match_rate,
                'improvement': opt_result.get('improvement', 0.0),
                'rolled_back': True,
                'rollback_reason': f'性能回退超过阈值 ({best_previous_match_rate:.1f}% -> {phase3_match_rate:.1f}%)'
            }
        
        # 💾 保存最终Checkpoint
        self._save_checkpoint('phase3_final', phase3_match_rate)
        
        return {
            'phase': 3,
            'match_rate': phase3_match_rate,
            'improvement': opt_result.get('improvement', 0.0),
            'rolled_back': False
        }
    
    def run_full_auto(self, 
                     phase1_trials: int = 50,
                     phase2_trials: int = 50,
                     phase3_trials: int = 50,
                     save_config: bool = True) -> Dict[str, Any]:
        """
        完整自动调优流程
        
        Args:
            phase1_trials: Phase 1试验次数
            phase2_trials: Phase 2试验次数
            phase3_trials: Phase 3试验次数
            save_config: 是否保存最终配置
            
        Returns:
            完整调优结果
        """
        logger.info("="*80)
        logger.info("🚗 启动自动驾驶调优")
        logger.info("="*80)
        
        results = {
            'phase1': None,
            'phase2': None,
            'phase3': None,
            'final': None
        }
        
        # Phase 1: 物理层
        results['phase1'] = self.run_phase1_physics(n_trials=phase1_trials)
        
        # Phase 2: 结构层
        results['phase2'] = self.run_phase2_structure(n_trials=phase2_trials)
        
        # Phase 3: 阈值微调
        results['phase3'] = self.run_phase3_threshold(n_trials=phase3_trials)
        
        # 最终评估
        final_diagnosis = self.server.run_physics_diagnosis()
        results['final'] = {
            'match_rate': final_diagnosis['current_match_rate'],
            'matched_cases': final_diagnosis['matched_cases'],
            'total_cases': final_diagnosis['total_cases']
        }
        
        # 保存配置
        if save_config:
            success = self.config_model.save_config(self.server.current_config, merge=True)
            if success:
                logger.info(f"✅ 最终配置已保存到: {self.config_model.config_path}")
            else:
                logger.warning("⚠️  保存配置失败")
        
        # 打印总结
        logger.info("="*80)
        logger.info("📊 调优总结")
        logger.info("="*80)
        logger.info(f"Phase 1 (物理层): {results['phase1']['match_rate']:.1f}%")
        logger.info(f"Phase 2 (结构层): {results['phase2']['match_rate']:.1f}%")
        logger.info(f"Phase 3 (阈值):   {results['phase3']['match_rate']:.1f}%")
        logger.info(f"最终匹配率:       {results['final']['match_rate']:.1f}%")
        logger.info(f"提升:             {results['final']['match_rate'] - results['phase1']['match_rate']:.1f}%")
        
        return results
    
    def _save_checkpoint(self, phase: str, match_rate: float):
        """
        [V10.2 核心分析师建议] 保存Checkpoint（参数时光机）
        
        Args:
            phase: 阶段名称（如'phase1', 'phase2'）
            match_rate: 该阶段的匹配率
        """
        from datetime import datetime
        
        checkpoint_path = self.checkpoint_dir / f"v10.2_{phase}_locked.json"
        checkpoint_data = {
            'phase': phase,
            'match_rate': match_rate,
            'config': copy.deepcopy(self.server.current_config),
            'frozen_params': copy.deepcopy(self.frozen_params),
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        with open(checkpoint_path, 'w', encoding='utf-8') as f:
            json.dump(checkpoint_data, f, ensure_ascii=False, indent=2)
        
        # 保存到内存中的checkpoints字典
        self.checkpoints[phase] = {
            'match_rate': match_rate,
            'config': copy.deepcopy(checkpoint_data['config']),
            'file': checkpoint_path
        }
        
        logger.info(f"💾 Checkpoint已保存: {checkpoint_path.name} (匹配率: {match_rate:.1f}%)")
    
    def _rollback_to_checkpoint(self, phase: str):
        """
        [V10.2 核心分析师建议] 回滚到指定检查点（Auto-Rollback）
        
        Args:
            phase: 要回滚到的阶段（如'phase1', 'phase2'）
            
        Returns:
            bool: 是否成功回滚
        """
        # 优先使用内存中的checkpoint
        if phase in self.checkpoints:
            checkpoint_info = self.checkpoints[phase]
            self.server.current_config = copy.deepcopy(checkpoint_info['config'])
            logger.info(f"🔄 已回滚到{phase}检查点 (匹配率: {checkpoint_info['match_rate']:.1f}%)")
            return True
        
        # 如果内存中没有，尝试从文件加载
        checkpoint_path = self.checkpoint_dir / f"v10.2_{phase}_locked.json"
        
        if not checkpoint_path.exists():
            logger.error(f"❌ Checkpoint文件不存在: {checkpoint_path}")
            return False
        
        with open(checkpoint_path, 'r', encoding='utf-8') as f:
            checkpoint_data = json.load(f)
        
        # 恢复配置
        self.server.current_config = checkpoint_data['config']
        self.frozen_params = checkpoint_data.get('frozen_params', {})
        
        logger.info(f"🔄 已回滚到{phase}检查点 (匹配率: {checkpoint_data['match_rate']:.1f}%)")
        return True
    
    def auto_rollback(self, target_phase: str) -> bool:
        """
        [V10.2 核心分析师建议] 自动回滚（公共接口）
        
        Args:
            target_phase: 目标Phase名称
            
        Returns:
            bool: 是否成功回滚
        """
        return self._rollback_to_checkpoint(target_phase)


def main():
    parser = argparse.ArgumentParser(description="V10.2 自动驾驶调优系统")
    parser.add_argument('--mode', type=str, default='auto',
                       choices=['auto', 'phase1', 'phase2', 'phase3'],
                       help='运行模式')
    parser.add_argument('--phase1-trials', type=int, default=50,
                       help='Phase 1试验次数')
    parser.add_argument('--phase2-trials', type=int, default=50,
                       help='Phase 2试验次数')
    parser.add_argument('--phase3-trials', type=int, default=50,
                       help='Phase 3试验次数')
    parser.add_argument('--no-save', action='store_true',
                       help='不保存最终配置')
    
    args = parser.parse_args()
    
    driver = AutoDriver()
    
    if args.mode == 'auto':
        # 完整自动调优
        driver.run_full_auto(
            phase1_trials=args.phase1_trials,
            phase2_trials=args.phase2_trials,
            phase3_trials=args.phase3_trials,
            save_config=not args.no_save
        )
    elif args.mode == 'phase1':
        driver.run_phase1_physics(n_trials=args.phase1_trials)
    elif args.mode == 'phase2':
        driver.run_phase2_structure(n_trials=args.phase2_trials)
    elif args.mode == 'phase3':
        driver.run_phase3_threshold(n_trials=args.phase3_trials)


if __name__ == '__main__':
    main()

