"""
全局回归安全网 (Global Regression Guardrails)
============================================

防止"打地鼠"现象，确保参数调优是全局收敛而非局部过拟合。
每次应用新参数时，快速运行所有 Tier A 案例（Jason A-E），显示全局健康度指标。

作者: Antigravity Team
版本: V10.0
日期: 2025-01-17
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class RegressionGuard:
    """全局回归安全网"""
    
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
        error_threshold: float = 10.0,
        delta_warning_threshold: float = 5.0
    ) -> Dict[str, Any]:
        """
        全局回归健康度检查
        
        Args:
            new_config: 新配置
            cases_data: 案例数据列表
            engine_class: 引擎类（GraphNetworkEngine）
            error_threshold: 误差阈值（超过此值标记为警告）
            delta_warning_threshold: 误差变化警告阈值（百分比）
        
        Returns:
            健康度检查结果字典
        """
        results = {
            'cases': {},
            'summary': {
                'total_cases': 0,
                'passed': 0,
                'warnings': 0,
                'critical': 0,
                'avg_baseline_error': 0.0,
                'avg_new_error': 0.0,
                'overall_status': 'good'
            }
        }
        
        # 过滤 Tier A 案例（Jason A-E）
        tier_a_cases = [
            c for c in cases_data 
            if isinstance(c.get('id', ''), str) and c.get('id', '').startswith('JASON_')
        ]
        
        if not tier_a_cases:
            logger.warning("⚠️ 未找到 Tier A 案例")
            return results
        
        baseline_errors = []
        new_errors = []
        
        for case in tier_a_cases:
            case_id = case.get('id', 'UNKNOWN')
            case_name = case.get('name', case_id)
            
            try:
                # 计算基准误差
                baseline_error = self._calculate_case_error(case, self.baseline_config, engine_class)
                # 计算新配置误差
                new_error = self._calculate_case_error(case, new_config, engine_class)
                
                baseline_errors.append(baseline_error)
                new_errors.append(new_error)
                
                # 计算误差变化
                delta = new_error - baseline_error
                delta_pct = (delta / baseline_error * 100) if baseline_error > 0 else 0
                
                # 判断状态
                if delta <= 0:
                    status = 'good'  # 改善或持平
                    status_icon = '✅'
                elif delta_pct < delta_warning_threshold:
                    status = 'warning'  # 轻微恶化
                    status_icon = '⚠️'
                else:
                    status = 'critical'  # 严重恶化
                    status_icon = '❌'
                
                results['cases'][case_id] = {
                    'name': case_name,
                    'baseline_error': baseline_error,
                    'new_error': new_error,
                    'delta': delta,
                    'delta_pct': delta_pct,
                    'status': status,
                    'status_icon': status_icon
                }
                
            except Exception as e:
                logger.error(f"❌ 计算案例 {case_id} 时出错: {e}")
                results['cases'][case_id] = {
                    'name': case_name,
                    'status': 'error',
                    'status_icon': '❌',
                    'error': str(e)
                }
        
        # 计算汇总统计
        results['summary']['total_cases'] = len(tier_a_cases)
        results['summary']['passed'] = sum(
            1 for v in results['cases'].values() if v.get('status') == 'good'
        )
        results['summary']['warnings'] = sum(
            1 for v in results['cases'].values() if v.get('status') == 'warning'
        )
        results['summary']['critical'] = sum(
            1 for v in results['cases'].values() if v.get('status') == 'critical'
        )
        
        if baseline_errors:
            results['summary']['avg_baseline_error'] = sum(baseline_errors) / len(baseline_errors)
        if new_errors:
            results['summary']['avg_new_error'] = sum(new_errors) / len(new_errors)
        
        # 判断整体状态
        if results['summary']['critical'] > 0:
            results['summary']['overall_status'] = 'critical'
        elif results['summary']['warnings'] > results['summary']['total_cases'] // 2:
            results['summary']['overall_status'] = 'warning'
        else:
            results['summary']['overall_status'] = 'good'
        
        return results
    
    def _calculate_case_error(
        self, 
        case: Dict, 
        config: Optional[Dict],
        engine_class
    ) -> float:
        """
        计算单个案例的平均误差
        
        Args:
            case: 案例数据
            config: 配置字典（None 则使用默认配置）
            engine_class: 引擎类
        
        Returns:
            平均误差
        """
        from core.config_schema import DEFAULT_FULL_ALGO_PARAMS
        
        # 如果没有配置，使用默认配置
        if config is None:
            config = DEFAULT_FULL_ALGO_PARAMS
        
        # 创建引擎实例
        engine = engine_class(config=config)
        
        # 获取案例时间线
        timeline = case.get('timeline', [])
        if not timeline:
            return 0.0
        
        errors = []
        
        for event in timeline:
            year = event.get('year')
            real_wealth = event.get('real_magnitude', 0.0)
            year_pillar = event.get('ganzhi', '')
            luck_pillar = event.get('dayun', '')
            
            try:
                # 计算预测值
                result = engine.calculate_wealth_index(
                    bazi=case.get('bazi', []),
                    day_master=case.get('day_master', ''),
                    gender=case.get('gender', '男'),
                    luck_pillar=luck_pillar,
                    year_pillar=year_pillar
                )
                
                if isinstance(result, dict):
                    predicted = result.get('wealth_index', 0.0)
                else:
                    predicted = float(result)
                
                # 计算误差
                error = abs(predicted - real_wealth)
                errors.append(error)
                
            except Exception as e:
                logger.warning(f"⚠️ 计算事件 {year} 时出错: {e}")
                continue
        
        # 返回平均误差
        return sum(errors) / len(errors) if errors else 0.0


def load_baseline_config(baseline_version: str = 'v9.3') -> Optional[Dict]:
    """
    加载基准配置
    
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
                # 移除或重置 V10.0 参数，恢复基准状态
                if 'nonlinear' in config:
                    # 保留基础结构，但重置为基准值
                    config['nonlinear'] = {
                        'seal_bonus': 0.0,
                        'seal_multiplier': 1.0,
                        'seal_conduction_multiplier': 1.0,
                        'opportunity_scaling': 1.0,
                        'clash_damping_limit': 0.3
                    }
                return config
        except Exception as e:
            logger.warning(f"⚠️ 无法加载基准配置: {e}")
    
    # 如果加载失败，使用默认配置
    from core.config_schema import DEFAULT_FULL_ALGO_PARAMS
    return DEFAULT_FULL_ALGO_PARAMS

