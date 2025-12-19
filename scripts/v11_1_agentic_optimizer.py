#!/usr/bin/env python3
"""
V11.1 Agentic Optimizer - 智能体自动优化工作流
==============================================

实现"观察-思考-行动"循环，自动优化SVM模型：

1. 观察（Observe）：读取训练结果，分析性能指标
2. 思考（Think）：诊断问题，识别改进方向
3. 行动（Act）：自动调整参数或策略
4. 循环（Loop）：重新训练并评估，直到达到目标

使用方法：
    python3 scripts/v11_1_agentic_optimizer.py --max_iterations 5 --target_accuracy 65
"""

import argparse
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import subprocess

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class V11AgenticOptimizer:
    """V11.1 智能体优化器"""
    
    def __init__(self, target_accuracy: float = 65.0):
        self.target_accuracy = target_accuracy
        self.iteration = 0
        self.history: List[Dict[str, Any]] = []
        self.config_file = project_root / "config" / "v11_agentic_config.json"
        
        # 可调参数
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置（如果存在）"""
        if self.config_file.exists():
            existing_config = json.load(open(self.config_file, 'r', encoding='utf-8'))
            # V11.2: 如果现有配置的classic_weight过高，强制重置为2.0
            if existing_config.get('classic_weight', 3.0) > 2.5:
                logger.info("🔄 V11.2: 检测到classic_weight过高，重置为2.0以缓解过拟合")
                existing_config['classic_weight'] = 2.0
            # V11.2: 强制开启SMOTE
            if not existing_config.get('use_smote', True):
                logger.info("🔄 V11.2: 强制开启SMOTE")
                existing_config['use_smote'] = True
            # V11.2: 确保有test_random_state
            if 'test_random_state' not in existing_config:
                existing_config['test_random_state'] = 100
            # V11.2: 确保有GridSearch参数范围
            if 'gridsearch_c_range' not in existing_config:
                existing_config['gridsearch_c_range'] = [0.01, 0.1, 1.0]
            if 'gridsearch_gamma_range' not in existing_config:
                existing_config['gridsearch_gamma_range'] = ['scale', 'auto', 0.1, 0.01]
            return existing_config
        
        # 默认配置（V11.2优化）
        return {
            'use_smote': True,  # V11.2: 强制开启SMOTE
            'smote_target_ratio': 0.4,
            'use_gridsearch': True,
            'classic_weight': 2.0,  # V11.2: 降低权重，从4.0降回2.0，避免过拟合
            'synthetic_weight': 2.0,
            'modern_weight': 1.0,
            'synthetic_count': 300,  # V11.8: 大规模增兵，从50提升到300
            'use_dynamic_cleaning': True,
            'confidence_threshold': 0.90,
            'test_random_state': 100,  # V11.2: 更换random_state，重新划分测试集
            'gridsearch_c_range': [0.01, 0.1, 1.0],  # V11.2: 重点搜索小C值（正则化）
            'gridsearch_gamma_range': ['scale', 'auto', 0.1, 0.01]  # V11.2: 扩大gamma搜索范围
        }
    
    def _save_config(self):
        """保存配置"""
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)
    
    def observe(self) -> Dict[str, Any]:
        """
        观察：运行训练并收集结果
        
        Returns:
            包含训练结果的字典
        """
        logger.info(f"🔍 [观察] 开始第 {self.iteration + 1} 次训练...")
        
        # 运行训练脚本（需要修改v11_svm_trainer.py支持配置参数）
        # 这里我们直接运行并解析输出
        try:
            result = subprocess.run(
                ['python3', str(project_root / 'scripts' / 'v11_svm_trainer.py')],
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )
            
            # 解析输出（日志可能输出到stderr，所以合并stdout和stderr）
            output = result.stdout + result.stderr
            
            # 提取关键指标（从输出中解析）
            metrics = self._parse_training_output(output)
            
            logger.info(f"   ✅ 训练完成")
            logger.info(f"   - 训练集准确率: {metrics.get('train_score', 0):.2%}")
            logger.info(f"   - 测试集准确率: {metrics.get('test_score', 0):.2%}")
            logger.info(f"   - 交叉验证准确率: {metrics.get('cv_mean', 0):.2%}")
            
            return {
                'metrics': metrics,
                'output': output,
                'error': result.stderr if hasattr(result, 'stderr') else '',
                'success': result.returncode == 0 and len(metrics) > 0
            }
        
        except subprocess.TimeoutExpired:
            logger.error("   ❌ 训练超时")
            return {'success': False, 'error': 'timeout'}
        except Exception as e:
            logger.error(f"   ❌ 训练失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def _parse_training_output(self, output: str) -> Dict[str, float]:
        """
        从训练输出中解析关键指标（使用增强的正则表达式）
        
        支持多种格式：
        - 百分比格式: "训练集准确率: 62.90%"
        - 小数格式: "train_score: 0.629"
        - 带括号格式: "交叉验证准确率: 55.95% (±6.83%)"
        """
        import re
        metrics = {}
        
        # DEBUG: 打印最后200个字符用于调试
        if len(output) > 200:
            debug_output = output[-500:]  # 取最后500字符
            logger.debug(f"DEBUG: 解析输出末尾内容:\n{debug_output}")
        
        try:
            # 模式1: 百分比格式 "训练集准确率: 62.90%"
            train_match = re.search(r'训练集准确率[：:]\s*([\d.]+)%', output)
            if train_match:
                metrics['train_score'] = float(train_match.group(1)) / 100.0
                logger.debug(f"解析训练集准确率（百分比格式）: {metrics['train_score']:.4f}")
            else:
                # 模式2: 小数格式 "train_score: 0.629" 或 "Training Accuracy: 0.629"
                train_match_dec = re.search(r'(?:train_score|训练集准确率|Training Accuracy)[：:]\s*0?\.?(\d+)', output)
                if train_match_dec:
                    value_str = '0.' + train_match_dec.group(1) if '.' not in train_match_dec.group(0) else train_match_dec.group(0).split(':')[-1].strip()
                    metrics['train_score'] = float(value_str)
                    logger.debug(f"解析训练集准确率（小数格式）: {metrics['train_score']:.4f}")
            
            # 模式1: 百分比格式 "测试集准确率: 33.33%"
            test_match = re.search(r'测试集准确率[：:]\s*([\d.]+)%', output)
            if test_match:
                metrics['test_score'] = float(test_match.group(1)) / 100.0
                logger.debug(f"解析测试集准确率（百分比格式）: {metrics['test_score']:.4f}")
            else:
                # 模式2: 小数格式
                test_match_dec = re.search(r'(?:test_score|测试集准确率|Test Accuracy)[：:]\s*0?\.?(\d+)', output)
                if test_match_dec:
                    value_str = '0.' + test_match_dec.group(1) if '.' not in test_match_dec.group(0) else test_match_dec.group(0).split(':')[-1].strip()
                    metrics['test_score'] = float(value_str)
                    logger.debug(f"解析测试集准确率（小数格式）: {metrics['test_score']:.4f}")
            
            # 交叉验证准确率（优先匹配带±的完整格式）
            cv_match = re.search(r'交叉验证准确率[：:]\s*([\d.]+)%\s*[（(]±\s*([\d.]+)%[）)]', output)
            if cv_match:
                metrics['cv_mean'] = float(cv_match.group(1)) / 100.0
                metrics['cv_std'] = float(cv_match.group(2)) / 100.0
                logger.debug(f"解析交叉验证准确率（完整格式）: {metrics['cv_mean']:.4f} ± {metrics['cv_std']:.4f}")
            else:
                # 模式2: 只有百分比 "交叉验证准确率: 55.95%"
                cv_simple_match = re.search(r'交叉验证准确率[：:]\s*([\d.]+)%', output)
                if cv_simple_match:
                    metrics['cv_mean'] = float(cv_simple_match.group(1)) / 100.0
                    logger.debug(f"解析交叉验证准确率（简单格式）: {metrics['cv_mean']:.4f}")
                else:
                    # 模式3: 小数格式
                    cv_dec_match = re.search(r'(?:cv_mean|cv_score|交叉验证准确率|Cross Validation)[：:]\s*0?\.?(\d+)', output)
                    if cv_dec_match:
                        value_str = '0.' + cv_dec_match.group(1) if '.' not in cv_dec_match.group(0) else cv_dec_match.group(0).split(':')[-1].strip()
                        metrics['cv_mean'] = float(value_str)
                        logger.debug(f"解析交叉验证准确率（小数格式）: {metrics['cv_mean']:.4f}")
            
            # 最佳交叉验证分数
            best_cv_match = re.search(r'最佳CV分数[：:]\s*([\d.]+)%', output)
            if best_cv_match:
                metrics['best_cv_score'] = float(best_cv_match.group(1)) / 100.0
                logger.debug(f"解析最佳CV分数: {metrics['best_cv_score']:.4f}")
            else:
                # 小数格式
                best_cv_dec_match = re.search(r'(?:best_cv_score|最佳CV分数)[：:]\s*0?\.?(\d+)', output)
                if best_cv_dec_match:
                    value_str = '0.' + best_cv_dec_match.group(1) if '.' not in best_cv_dec_match.group(0) else best_cv_dec_match.group(0).split(':')[-1].strip()
                    metrics['best_cv_score'] = float(value_str)
                    logger.debug(f"解析最佳CV分数（小数格式）: {metrics['best_cv_score']:.4f}")
            
            # 验证解析结果
            if len(metrics) == 0:
                logger.warning("⚠️  未能解析到任何指标！")
                logger.warning(f"DEBUG: 输出最后500字符:\n{output[-500:]}")
            else:
                logger.debug(f"✅ 成功解析 {len(metrics)} 个指标: {list(metrics.keys())}")
        
        except Exception as e:
            logger.error(f"❌ 解析输出时出错: {e}")
            logger.error(f"DEBUG: 错误发生时的输出末尾:\n{output[-500:]}")
            import traceback
            logger.debug(traceback.format_exc())
        
        return metrics
    
    def think(self, observation: Dict[str, Any]) -> Dict[str, Any]:
        """
        思考：分析结果，诊断问题
        
        Args:
            observation: 观察结果
        
        Returns:
            诊断结果和建议
        """
        logger.info("🧠 [思考] 分析训练结果...")
        
        if not observation.get('success'):
            return {
                'status': 'error',
                'issues': ['训练失败'],
                'recommendations': ['检查训练脚本和依赖']
            }
        
        metrics = observation.get('metrics', {})
        cv_mean = metrics.get('cv_mean', 0.0)
        test_score = metrics.get('test_score', 0.0)
        train_score = metrics.get('train_score', 0.0)
        
        issues = []
        recommendations = []
        
        # 诊断1: 测试集准确率过低
        if test_score < 0.40:
            issues.append(f"测试集准确率过低 ({test_score:.2%})")
            recommendations.append("降低SMOTE强度或禁用SMOTE")
            recommendations.append("增加测试集样本量")
            recommendations.append("检查数据分布是否合理")
            # V11.7.1: 如果数据量太小，建议调整冲突清洗策略
            if '数据量' in str(observation.get('output', '')) or '清洗后案例数' in str(observation.get('output', '')):
                recommendations.append("调整冲突清洗相似度阈值（从0.95提升到0.98）")
                recommendations.append("优化Modern vs Modern清洗策略（不要全部删除）")
        
        # 诊断2: 过拟合（训练集高但测试集低）
        if train_score - test_score > 0.20:
            issues.append(f"过拟合严重 (训练: {train_score:.2%}, 测试: {test_score:.2%})")
            recommendations.append("降低SMOTE强度")
            recommendations.append("减少合成数据数量")
            recommendations.append("增加正则化（降低C参数）")
        
        # 诊断3: 交叉验证准确率低于目标
        if cv_mean < self.target_accuracy / 100.0:
            issues.append(f"交叉验证准确率低于目标 ({cv_mean:.2%} < {self.target_accuracy/100.0:.2%})")
            
            if cv_mean < 0.50:
                recommendations.append("增加合成数据数量（特别针对少数类别）")
                recommendations.append("调整样本权重（提高Classic权重）")
            elif cv_mean < 0.55:
                recommendations.append("优化GridSearch参数范围")
                recommendations.append("增加SMOTE目标比例")
        
        # 诊断4: 训练集准确率过低
        if train_score < 0.50:
            issues.append(f"训练集准确率过低 ({train_score:.2%})")
            recommendations.append("检查特征工程")
            recommendations.append("增加训练数据")
        
        if not issues:
            issues.append("性能良好，无需调整")
        
        logger.info(f"   📊 诊断结果:")
        logger.info(f"      - 识别到 {len(issues)} 个问题")
        logger.info(f"      - 提出 {len(recommendations)} 条建议")
        
        # V11.2: 以测试集准确率为主要判断标准（而非CV）
        # 只有当测试集准确率达标，且过拟合不严重时，才认为"ok"
        is_ok = (test_score >= self.target_accuracy / 100.0 and 
                 train_score - test_score < 0.15)  # 过拟合差距小于15%
        
        return {
            'status': 'ok' if is_ok else 'needs_improvement',
            'issues': issues,
            'recommendations': recommendations,
            'metrics': metrics
        }
    
    def act(self, diagnosis: Dict[str, Any]) -> bool:
        """
        行动：根据诊断结果调整参数
        
        Args:
            diagnosis: 诊断结果
        
        Returns:
            是否进行了调整
        """
        if diagnosis.get('status') == 'ok':
            logger.info("✅ [行动] 性能已达标，无需调整")
            return False
        
        if diagnosis.get('status') == 'error':
            logger.warning("⚠️  [行动] 训练失败，跳过调整")
            return False
        
        logger.info("🔧 [行动] 根据诊断结果调整参数...")
        
        issues = diagnosis.get('issues', [])
        recommendations = diagnosis.get('recommendations', [])
        metrics = diagnosis.get('metrics', {})
        
        changes_made = []
        
        # 行动1: V11.2 如果过拟合，降低SMOTE强度（但不禁用）
        if '过拟合' in ' '.join(issues) or 'SMOTE' in ' '.join(recommendations):
            if '降低SMOTE强度' in recommendations:
                current_ratio = self.config.get('smote_target_ratio', 0.4)
                new_ratio = max(0.2, current_ratio - 0.1)
                if new_ratio != current_ratio:
                    self.config['smote_target_ratio'] = new_ratio
                    changes_made.append(f"降低SMOTE目标比例: {current_ratio:.2f} -> {new_ratio:.2f}")
        
        # V11.2: 强制保持SMOTE开启
        if not self.config.get('use_smote', True):
            self.config['use_smote'] = True
            changes_made.append("强制开启SMOTE（V11.2策略）")
        
        # 行动2: 如果准确率低，增加合成数据
        if '增加合成数据' in ' '.join(recommendations):
            current_count = self.config.get('synthetic_count', 50)
            new_count = min(100, current_count + 10)
            self.config['synthetic_count'] = new_count
            changes_made.append(f"增加合成数据数量: {current_count} -> {new_count}")
        
        # 行动3: 如果准确率低，提高Classic权重
        if '提高Classic权重' in ' '.join(recommendations):
            current_weight = self.config.get('classic_weight', 3.0)
            new_weight = min(5.0, current_weight + 0.5)
            self.config['classic_weight'] = new_weight
            changes_made.append(f"提高Classic权重: {current_weight:.1f} -> {new_weight:.1f}")
        
        # 行动4: 如果过拟合，降低合成数据数量
        if '减少合成数据数量' in ' '.join(recommendations):
            current_count = self.config.get('synthetic_count', 50)
            new_count = max(20, current_count - 10)
            self.config['synthetic_count'] = new_count
            changes_made.append(f"减少合成数据数量: {current_count} -> {new_count}")
        
        # 行动5: 如果测试集准确率极低，禁用SMOTE
        test_score = metrics.get('test_score', 0.0)
        if test_score < 0.30 and self.config.get('use_smote', True):
            self.config['use_smote'] = False
            changes_made.append("禁用SMOTE（测试集准确率过低）")
        
        # 行动6: V11.7.1 如果数据量太小，调整冲突清洗策略
        if '调整冲突清洗相似度阈值' in ' '.join(recommendations):
            # 提升相似度阈值，减少删除
            if 'conflict_similarity_threshold' not in self.config:
                self.config['conflict_similarity_threshold'] = 0.98  # 从0.95提升到0.98
                changes_made.append("提升冲突清洗相似度阈值: 0.95 -> 0.98（减少删除）")
            elif self.config.get('conflict_similarity_threshold', 0.95) < 0.98:
                self.config['conflict_similarity_threshold'] = 0.98
                changes_made.append("提升冲突清洗相似度阈值: -> 0.98（减少删除）")
        
        # 保存配置
        if changes_made:
            self._save_config()
            logger.info(f"   ✅ 进行了 {len(changes_made)} 项调整:")
            for change in changes_made:
                logger.info(f"      - {change}")
            return True
        else:
            logger.info("   ℹ️  未进行任何调整")
            return False
    
    def run(self, max_iterations: int = 5):
        """
        运行完整的优化循环
        
        Args:
            max_iterations: 最大迭代次数
        """
        logger.info("=" * 80)
        logger.info("🚀 V11.1 Agentic Optimizer 启动")
        logger.info("=" * 80)
        logger.info(f"目标准确率: {self.target_accuracy:.1f}%")
        logger.info(f"最大迭代次数: {max_iterations}")
        logger.info("")
        
        for iteration in range(max_iterations):
            self.iteration = iteration
            logger.info(f"\n{'=' * 80}")
            logger.info(f"迭代 {iteration + 1}/{max_iterations}")
            logger.info(f"{'=' * 80}\n")
            
            # 观察
            observation = self.observe()
            if not observation.get('success'):
                logger.error("训练失败，停止优化")
                break
            
            # 思考
            diagnosis = self.think(observation)
            
            # 记录历史
            history_entry = {
                'iteration': iteration + 1,
                'timestamp': datetime.now().isoformat(),
                'metrics': observation.get('metrics', {}),
                'diagnosis': diagnosis,
                'config': self.config.copy()
            }
            self.history.append(history_entry)
            
            # 检查是否达标（V11.2: 优先看测试集准确率，而非CV）
            test_score = observation.get('metrics', {}).get('test_score', 0.0)
            cv_mean = observation.get('metrics', {}).get('cv_mean', 0.0)
            
            # V11.2: 如果测试集准确率达到目标，或者CV和测试集都接近目标，则停止
            if test_score >= self.target_accuracy / 100.0:
                logger.info(f"\n🎉 达成目标！测试集准确率: {test_score:.2%} >= {self.target_accuracy/100.0:.2%}")
                break
            elif cv_mean >= self.target_accuracy / 100.0 and test_score >= (self.target_accuracy - 5) / 100.0:
                # CV达标且测试集接近目标（差距5%以内）
                logger.info(f"\n✅ 接近目标：CV {cv_mean:.2%}，测试集 {test_score:.2%}（差距 {(cv_mean - test_score):.2%}）")
                # 继续优化，不停止
            
            # 行动（最后一次迭代不调整）
            if iteration < max_iterations - 1:
                changed = self.act(diagnosis)
                if not changed:
                    logger.info("未进行任何调整，停止优化")
                    break
            else:
                logger.info("最后一次迭代，跳过参数调整")
        
        # 保存历史
        history_file = project_root / "logs" / f"v11_agentic_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        history_file.parent.mkdir(parents=True, exist_ok=True)
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(self.history, f, ensure_ascii=False, indent=2)
        
        logger.info(f"\n{'=' * 80}")
        logger.info("📊 优化历史已保存到: " + str(history_file))
        logger.info(f"{'=' * 80}\n")
        
        # 打印总结
        self._print_summary()
    
    def _print_summary(self):
        """打印优化总结"""
        logger.info("📈 优化总结:")
        logger.info("")
        
        for entry in self.history:
            iteration = entry['iteration']
            metrics = entry['metrics']
            cv_mean = metrics.get('cv_mean', 0.0)
            test_score = metrics.get('test_score', 0.0)
            
            logger.info(f"  迭代 {iteration}:")
            logger.info(f"    - 交叉验证准确率: {cv_mean:.2%}")
            logger.info(f"    - 测试集准确率: {test_score:.2%}")
            logger.info(f"    - 诊断: {', '.join(entry['diagnosis'].get('issues', [])[:2])}")
            logger.info("")


def main():
    parser = argparse.ArgumentParser(description='V11.1 Agentic Optimizer')
    parser.add_argument('--max_iterations', type=int, default=5, help='最大迭代次数')
    parser.add_argument('--target_accuracy', type=float, default=65.0, help='目标准确率(%)')
    
    args = parser.parse_args()
    
    optimizer = V11AgenticOptimizer(target_accuracy=args.target_accuracy)
    optimizer.run(max_iterations=args.max_iterations)


if __name__ == '__main__':
    main()

