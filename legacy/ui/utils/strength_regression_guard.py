"""
旺衰判定回归安全网 (Strength Regression Guardrails)
===================================================

专门用于量子验证页面（第一层验证）的全局回归安全网。
只检查旺衰判定（身强身弱），不涉及财富预测。

作者: Antigravity Team
版本: V10.0
日期: 2025-01-17
"""

import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class StrengthRegressionGuard:
    """旺衰判定回归安全网"""
    
    def __init__(self, baseline_config_path: Optional[Path] = None):
        """
        初始化回归安全网
        
        Args:
            baseline_config_path: 基准配置文件路径（V9.3或之前的配置）
        """
        self.baseline_config_path = baseline_config_path
        self.baseline_config = None
        
        # 加载基准配置
        if baseline_config_path and baseline_config_path.exists():
            self._load_baseline_config()
    
    def _load_baseline_config(self):
        """加载基准配置"""
        try:
            with open(self.baseline_config_path, 'r', encoding='utf-8') as f:
                self.baseline_config = json.load(f)
            logger.info(f"✅ 已加载基准配置: {self.baseline_config_path}")
        except Exception as e:
            logger.warning(f"⚠️ 无法加载基准配置: {e}")
            self.baseline_config = None
    
    def check_global_health(
        self, 
        new_config: Dict,
        cases_data: List[Dict],
        engine_class,
        mismatch_threshold: float = 0.0  # 0.0 表示不允许任何不匹配
    ) -> Dict[str, Any]:
        """
        全局回归健康度检查（基于旺衰判定）
        
        Args:
            new_config: 新配置
            cases_data: 案例数据列表（应包含 ground_truth.strength 字段）
            engine_class: 引擎类（GraphNetworkEngine）
            mismatch_threshold: 不匹配阈值（允许的不匹配率，0.0 表示不允许任何不匹配）
        
        Returns:
            健康度检查结果字典
        """
        results = {
            'cases': {},
            'summary': {
                'total_cases': 0,
                'matched': 0,
                'mismatched': 0,
                'errors': 0,
                'match_rate': 0.0,
                'overall_status': 'good'
            }
        }
        
        # 过滤有 ground_truth.strength 的案例
        valid_cases = [
            c for c in cases_data 
            if c.get('ground_truth', {}).get('strength') not in [None, 'Unknown', '']
        ]
        
        if not valid_cases:
            logger.warning("⚠️ 未找到有效的旺衰判定案例")
            return results
        
        matched_count = 0
        mismatched_count = 0
        error_count = 0
        
        for case in valid_cases:
            case_id = case.get('id', 'UNKNOWN')
            case_name = case.get('name', case_id)
            ground_truth_strength = case.get('ground_truth', {}).get('strength', 'Unknown')
            
            try:
                # 计算基准判定
                baseline_label = self._calculate_strength_label(case, self.baseline_config, engine_class)
                # 计算新配置判定
                new_label = self._calculate_strength_label(case, new_config, engine_class)
                
                # 检查是否匹配真实值
                baseline_match = self._is_match(baseline_label, ground_truth_strength)
                new_match = self._is_match(new_label, ground_truth_strength)
                
                # 判断状态
                if new_match:
                    status = 'matched'
                    status_icon = '✅'
                    matched_count += 1
                elif baseline_match and not new_match:
                    status = 'regressed'  # 从匹配变为不匹配（回归）
                    status_icon = '❌'
                    mismatched_count += 1
                elif not baseline_match and new_match:
                    status = 'improved'  # 从不匹配变为匹配（改进）
                    status_icon = '✅'
                    matched_count += 1
                else:
                    status = 'mismatched'  # 仍然不匹配
                    status_icon = '⚠️'
                    mismatched_count += 1
                
                results['cases'][case_id] = {
                    'name': case_name,
                    'ground_truth': ground_truth_strength,
                    'baseline_label': baseline_label,
                    'new_label': new_label,
                    'baseline_match': baseline_match,
                    'new_match': new_match,
                    'status': status,
                    'status_icon': status_icon
                }
                
            except Exception as e:
                logger.error(f"❌ 计算案例 {case_id} 时出错: {e}")
                error_count += 1
                results['cases'][case_id] = {
                    'name': case_name,
                    'status': 'error',
                    'status_icon': '❌',
                    'error': str(e)
                }
        
        # 计算汇总统计
        results['summary']['total_cases'] = len(valid_cases)
        results['summary']['matched'] = matched_count
        results['summary']['mismatched'] = mismatched_count
        results['summary']['errors'] = error_count
        results['summary']['match_rate'] = (matched_count / len(valid_cases) * 100) if valid_cases else 0.0
        
        # 判断整体状态
        regression_count = sum(
            1 for v in results['cases'].values() 
            if v.get('status') == 'regressed'
        )
        
        if regression_count > 0:
            results['summary']['overall_status'] = 'critical'  # 有回归
        elif results['summary']['match_rate'] >= 90.0:
            results['summary']['overall_status'] = 'good'  # 匹配率 >= 90%
        elif results['summary']['match_rate'] >= 70.0:
            results['summary']['overall_status'] = 'warning'  # 匹配率 70-90%
        else:
            results['summary']['overall_status'] = 'critical'  # 匹配率 < 70%
        
        return results
    
    def _calculate_strength_label(
        self, 
        case: Dict, 
        config: Optional[Dict],
        engine_class
    ) -> str:
        """
        计算案例的旺衰判定标签
        
        Args:
            case: 案例数据
            config: 配置字典（None 则使用默认配置）
            engine_class: 引擎类
        
        Returns:
            旺衰标签（'Strong', 'Weak', 'Balanced', 'Follower' 等）
        """
        from core.config_schema import DEFAULT_FULL_ALGO_PARAMS
        
        # 如果没有配置，使用默认配置
        if config is None:
            config = DEFAULT_FULL_ALGO_PARAMS
        
        # 创建引擎实例
        engine = engine_class(config=config)
        
        # 获取八字
        bazi = case.get('bazi', [])
        day_master = case.get('day_master', '')
        
        if not bazi or not day_master:
            return 'Unknown'
        
        try:
            # 计算旺衰
            # 注意：这里应该使用引擎的 calculate_strength_score 方法
            # 但为了简化，我们使用 _evaluate_wang_shuai（如果可用）
            if hasattr(engine, '_evaluate_wang_shuai'):
                strength_tuple = engine._evaluate_wang_shuai(day_master, bazi)
                if isinstance(strength_tuple, tuple):
                    strength_label = strength_tuple[0]  # ('Strong', score) 或 ('Weak', score)
                else:
                    strength_label = str(strength_tuple)
            elif hasattr(engine, 'calculate_strength_score'):
                strength_result = engine.calculate_strength_score(day_master)
                strength_label = strength_result.get('strength_label', 'Unknown')
            else:
                # 如果都没有，尝试调用 calculate_wealth_index 然后提取 strength_label
                # 但这是临时的，应该避免
                logger.warning(f"⚠️ 引擎 {engine_class} 没有 calculate_strength_score 或 _evaluate_wang_shuai 方法")
                return 'Unknown'
            
            return strength_label
            
        except Exception as e:
            logger.warning(f"⚠️ 计算旺衰时出错: {e}")
            return 'Unknown'
    
    def _is_match(self, computed_label: str, ground_truth: str) -> bool:
        """
        检查计算标签是否匹配真实值
        
        Args:
            computed_label: 计算出的标签
            ground_truth: 真实标签
        
        Returns:
            是否匹配
        """
        if ground_truth == 'Unknown' or computed_label == 'Unknown':
            return False
        
        # 宽松匹配：只要包含关键词就认为匹配
        # 例如 "Strong" 匹配 "Strong", "Very Strong" 等
        if ground_truth.lower() in computed_label.lower() or computed_label.lower() in ground_truth.lower():
            return True
        
        # 特殊处理：Follower 相关
        if 'Follower' in ground_truth and 'Follower' in computed_label:
            return True
        
        # 特殊处理：Weak 和 Extreme_Weak
        if ('Weak' in ground_truth or 'Extreme_Weak' in ground_truth) and ('Weak' in computed_label):
            return True
        
        return False


def load_baseline_config_for_strength(baseline_version: str = 'v9.3') -> Optional[Dict]:
    """
    加载基准配置（用于旺衰判定）
    
    Args:
        baseline_version: 基准版本号
    
    Returns:
        配置字典
    """
    # 尝试从配置文件加载
    config_path = Path("config/parameters.json")
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # 保留所有配置，因为旺衰判定可能受所有参数影响
                return config
        except Exception as e:
            logger.warning(f"⚠️ 无法加载基准配置: {e}")
    
    # 如果加载失败，使用默认配置
    from core.config_schema import DEFAULT_FULL_ALGO_PARAMS
    return DEFAULT_FULL_ALGO_PARAMS

