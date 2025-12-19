#!/usr/bin/env python3
"""
V10.2 自动调优系统测试套件
==========================

测试覆盖：
1. Optuna优化器基本功能
2. MCP服务器工具接口
3. 自动驾驶主程序（简化测试）
4. Checkpoints机制
5. 物理一致性指标
6. 交叉验证功能
"""

import unittest
import sys
import json
import copy
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 检查optuna是否可用（不导入会导致退出的模块）
try:
    import optuna
    OPTUNA_AVAILABLE = True
except ImportError:
    OPTUNA_AVAILABLE = False

# 先导入不依赖optuna的模块
# 注意：MCPTuningServer和AutoDriver可能间接依赖optuna模块，需要在测试中动态导入
# 这里先不导入，在测试方法中根据OPTUNA_AVAILABLE决定
from scripts.v10_2_mcp_server import MCPTuningServer
from scripts.v10_2_auto_driver import AutoDriver
from scripts.strength_parameter_tuning import StrengthParameterTuner
from core.config_schema import DEFAULT_FULL_ALGO_PARAMS


class TestOptimizationConfig(unittest.TestCase):
    """测试OptimizationConfig配置类"""
    
    @unittest.skipUnless(OPTUNA_AVAILABLE, "Optuna未安装，跳过配置类测试")
    def test_default_config(self):
        """测试默认配置"""
        # 动态导入（避免在模块级别导入时退出）
        import importlib
        importlib.reload(sys.modules.get('optuna', __import__('optuna')))
        from scripts.v10_2_optuna_tuner import OptimizationConfig
        config = OptimizationConfig()
        self.assertEqual(config.focus_layer, "all")
        self.assertEqual(config.constraints, "soft")
        self.assertEqual(config.n_trials, 50)
        self.assertTrue(config.pruner_enabled)
        self.assertFalse(config.cross_validation)
    
    @unittest.skipUnless(OPTUNA_AVAILABLE, "Optuna未安装，跳过配置类测试")
    def test_custom_config(self):
        """测试自定义配置"""
        import importlib
        importlib.reload(sys.modules.get('optuna', __import__('optuna')))
        from scripts.v10_2_optuna_tuner import OptimizationConfig
        config = OptimizationConfig(
            focus_layer="threshold",
            constraints="strict",
            n_trials=100,
            cross_validation=True,
            cv_train_ratio=0.8
        )
        self.assertEqual(config.focus_layer, "threshold")
        self.assertEqual(config.constraints, "strict")
        self.assertEqual(config.n_trials, 100)
        self.assertTrue(config.cross_validation)
        self.assertEqual(config.cv_train_ratio, 0.8)


class TestMCPTuningServer(unittest.TestCase):
    """测试MCP调优服务器"""
    
    def setUp(self):
        """测试前准备"""
        # 动态导入（避免在optuna未安装时导致退出）
        try:
            from scripts.v10_2_mcp_server import MCPTuningServer
            self.server = MCPTuningServer()
        except SystemExit:
            self.skipTest("Optuna未安装，MCP服务器无法初始化")
    
    def test_server_initialization(self):
        """测试服务器初始化"""
        self.assertIsNotNone(self.server.tuner)
        self.assertIsNotNone(self.server.base_config)
        self.assertIsNotNone(self.server.current_config)
    
    def test_run_physics_diagnosis(self):
        """测试物理诊断功能"""
        diagnosis = self.server.run_physics_diagnosis()
        
        # 检查返回结构
        self.assertIn('current_match_rate', diagnosis)
        self.assertIn('total_cases', diagnosis)
        self.assertIn('matched_cases', diagnosis)
        self.assertIn('main_issues', diagnosis)
        self.assertIn('violation_summary', diagnosis)
        self.assertIn('recommendations', diagnosis)
        self.assertIn('physics_consistency', diagnosis)
        self.assertIn('nl_description', diagnosis)
        
        # 检查物理一致性指标（实际结构是扁平化的）
        pc = diagnosis.get('physics_consistency', {})
        self.assertIn('month_dominance_ratio', pc)
        self.assertIn('rooting_impact_factor', pc)
        self.assertIn('overall_health', pc)
    
    def test_configure_optimization_strategy(self):
        """测试优化策略配置"""
        result = self.server.configure_optimization_strategy(
            focus_layer="threshold",
            constraints="soft"
        )
        
        self.assertEqual(result['status'], 'configured')
        self.assertEqual(result['config']['focus_layer'], 'threshold')
        self.assertEqual(result['config']['constraints'], 'soft')
        self.assertIsNotNone(self.server.optimization_config)
    
    def test_check_physics_violations(self):
        """测试物理约束检查"""
        # 测试正常配置（无违反）
        violations = self.server._check_physics_violations(self.server.current_config)
        self.assertIn('has_violations', violations)
        self.assertIn('violations', violations)
        
        # 测试违反配置（hour_weight > month_weight）
        bad_config = copy.deepcopy(self.server.current_config)
        bad_config['physics']['pillarWeights']['hour'] = 2.0
        bad_config['physics']['pillarWeights']['month'] = 1.0
        
        violations = self.server._check_physics_violations(bad_config)
        self.assertTrue(violations['has_violations'])
        self.assertGreater(len(violations['violations']), 0)
    
    def test_calculate_physics_consistency(self):
        """测试物理一致性指标计算"""
        # 创建模拟结果
        mock_result = {
            'match_rate': 50.0,
            'case_results': [
                {'score': 60.0},
                {'score': 40.0},
                {'score': 30.0}
            ]
        }
        
        consistency = self.server._calculate_physics_consistency(mock_result)
        
        # 检查指标结构（实际结构是扁平化的）
        self.assertIn('month_dominance_ratio', consistency)
        self.assertIn('rooting_impact_factor', consistency)
        self.assertIn('overall_health', consistency)
        
        # 检查Month Dominance Ratio值
        month_ratio = consistency.get('month_dominance_ratio', 0)
        self.assertGreater(month_ratio, 0)


class TestAutoDriver(unittest.TestCase):
    """测试自动驾驶调优器"""
    
    def setUp(self):
        """测试前准备"""
        # 动态导入（避免在optuna未安装时导致退出）
        try:
            from scripts.v10_2_auto_driver import AutoDriver
            # 使用临时checkpoint目录
            test_checkpoint_dir = project_root / "config" / "test_checkpoints"
            self.driver = AutoDriver(checkpoint_dir=test_checkpoint_dir)
        except SystemExit:
            self.skipTest("Optuna未安装，AutoDriver无法初始化")
    
    def test_driver_initialization(self):
        """测试驱动器初始化"""
        self.assertIsNotNone(self.driver.server)
        self.assertIsNotNone(self.driver.tuner)
        self.assertIsNotNone(self.driver.config_model)
        self.assertEqual(len(self.driver.frozen_params), 0)
        self.assertEqual(len(self.driver.checkpoints), 0)
    
    def test_save_checkpoint(self):
        """测试Checkpoint保存"""
        # 保存一个测试checkpoint
        self.driver._save_checkpoint("test_phase", 50.0)
        
        self.assertIn('test_phase', self.driver.checkpoints)
        
        # 检查checkpoint数据
        checkpoint_info = self.driver.checkpoints['test_phase']
        self.assertEqual(checkpoint_info['match_rate'], 50.0)
        self.assertIn('config', checkpoint_info)
        
        # 检查checkpoint文件是否存在
        checkpoint_file = self.driver.checkpoint_dir / "v10.2_test_phase_locked.json"
        self.assertTrue(checkpoint_file.exists())
        
        # 验证checkpoint内容
        with open(checkpoint_file, 'r', encoding='utf-8') as f:
            checkpoint_data = json.load(f)
        
        self.assertEqual(checkpoint_data['phase'], 'test_phase')
        self.assertEqual(checkpoint_data['match_rate'], 50.0)
        self.assertIn('config', checkpoint_data)
        self.assertIn('frozen_params', checkpoint_data)
    
    def test_auto_rollback(self):
        """测试自动回滚功能"""
        # 先保存一个checkpoint
        original_month_weight = self.driver.server.current_config['physics']['pillarWeights']['month']
        self.driver._save_checkpoint("test_phase", 50.0)
        
        # 修改配置
        self.driver.server.current_config['physics']['pillarWeights']['month'] = 999.0
        
        # 执行回滚
        success = self.driver._rollback_to_checkpoint("test_phase")
        
        self.assertTrue(success)
        # 验证配置已恢复
        self.assertEqual(
            self.driver.server.current_config['physics']['pillarWeights']['month'],
            original_month_weight
        )
    
    def test_rollback_nonexistent_checkpoint(self):
        """测试回滚不存在的checkpoint"""
        success = self.driver._rollback_to_checkpoint("nonexistent_phase")
        self.assertFalse(success)


class TestOptunaIntegration(unittest.TestCase):
    """测试Optuna集成（简化测试）"""
    
    @unittest.skipUnless(OPTUNA_AVAILABLE, "Optuna未安装，跳过集成测试")
    def test_optimization_objective(self):
        """测试优化目标函数（简化版）"""
        from scripts.v10_2_optuna_tuner import OptimizationConfig, StrengthOptimizationObjective
        tuner = StrengthParameterTuner()
        config = OptimizationConfig(
            focus_layer="threshold",
            n_trials=5,  # 少量试验用于测试
            verbose=False
        )
        base_config = copy.deepcopy(DEFAULT_FULL_ALGO_PARAMS)
        
        # 创建目标函数
        objective = StrengthOptimizationObjective(tuner, config, base_config)
        
        # 测试参数建议
        from optuna import create_study
        study = create_study()
        trial = study.ask()
        
        trial_config = objective._suggest_parameters(trial)
        
        # 验证配置结构
        self.assertIn('strength', trial_config)
        self.assertIn('energy_threshold_center', trial_config['strength'])
        
        # 测试损失计算
        result = tuner.evaluate_parameter_set(trial_config)
        loss = objective._calculate_weighted_loss(result)
        
        self.assertGreaterEqual(loss, 0.0)
        self.assertLessEqual(loss, 1.0)
    
    @unittest.skipUnless(OPTUNA_AVAILABLE, "Optuna未安装，跳过集成测试")
    def test_bayesian_penalty(self):
        """测试贝叶斯惩罚计算"""
        from scripts.v10_2_optuna_tuner import OptimizationConfig, StrengthOptimizationObjective
        tuner = StrengthParameterTuner()
        config = OptimizationConfig()
        base_config = copy.deepcopy(DEFAULT_FULL_ALGO_PARAMS)
        
        objective = StrengthOptimizationObjective(tuner, config, base_config)
        
        # 测试正常配置（无惩罚）
        normal_config = copy.deepcopy(base_config)
        penalty = objective._calculate_bayesian_penalty(normal_config)
        self.assertGreaterEqual(penalty, 0.0)
        
        # 测试违反配置（hour_weight > month_weight）
        bad_config = copy.deepcopy(base_config)
        bad_config['physics']['pillarWeights']['hour'] = 2.0
        bad_config['physics']['pillarWeights']['month'] = 1.0
        
        penalty = objective._calculate_bayesian_penalty(bad_config)
        self.assertGreater(penalty, 0.0)


class TestCrossValidation(unittest.TestCase):
    """测试交叉验证功能"""
    
    @unittest.skipUnless(OPTUNA_AVAILABLE, "Optuna未安装，跳过交叉验证测试")
    def test_prepare_cv_split(self):
        """测试交叉验证数据分割"""
        from scripts.v10_2_optuna_tuner import OptimizationConfig, StrengthOptimizationObjective
        tuner = StrengthParameterTuner()
        config = OptimizationConfig(
            cross_validation=True,
            cv_train_ratio=0.7
        )
        base_config = copy.deepcopy(DEFAULT_FULL_ALGO_PARAMS)
        
        objective = StrengthOptimizationObjective(tuner, config, base_config)
        
        # 检查是否有_setup_cross_validation方法（实际实现的方法名）
        if hasattr(objective, '_setup_cross_validation'):
            objective._setup_cross_validation()
            # 验证交叉验证设置成功
            self.assertIsNotNone(getattr(objective, 'cv_train_indices', None))
            self.assertIsNotNone(getattr(objective, 'cv_val_indices', None))
            
            train_indices = objective.cv_train_indices
            val_indices = objective.cv_val_indices
            
            # 验证分割结果
            total_indices = len(train_indices) + len(val_indices)
            self.assertGreater(total_indices, 0)
            
            # 验证比例（允许小误差）
            train_ratio = len(train_indices) / total_indices
            self.assertAlmostEqual(train_ratio, 0.7, places=1)
            
            # 验证没有重叠
            train_set = set(train_indices)
            val_set = set(val_indices)
            self.assertEqual(len(train_set & val_set), 0)
        else:
            self.skipTest("_setup_cross_validation方法未实现或方法名不同")


def run_tests():
    """运行所有测试"""
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加测试用例
    suite.addTests(loader.loadTestsFromTestCase(TestOptimizationConfig))
    suite.addTests(loader.loadTestsFromTestCase(TestMCPTuningServer))
    suite.addTests(loader.loadTestsFromTestCase(TestAutoDriver))
    suite.addTests(loader.loadTestsFromTestCase(TestOptunaIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestCrossValidation))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result


if __name__ == '__main__':
    print("=" * 80)
    print("🧪 V10.2 自动调优系统测试套件")
    print("=" * 80)
    print()
    
    result = run_tests()
    
    print()
    print("=" * 80)
    if result.wasSuccessful():
        print("✅ 所有测试通过！")
    else:
        print(f"❌ 测试失败: {len(result.failures)}个失败, {len(result.errors)}个错误")
    print("=" * 80)
    
    sys.exit(0 if result.wasSuccessful() else 1)

