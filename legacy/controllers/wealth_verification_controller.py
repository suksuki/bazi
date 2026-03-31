"""
财富验证控制器 (Wealth Verification Controller)
MVC Controller Layer - 负责财富验证的业务逻辑
"""

import logging
import copy
from typing import List, Dict, Optional, Any, Tuple
from pathlib import Path

from core.models.wealth_case_model import WealthCaseModel, WealthCase, WealthEvent
from core.engine_graph import GraphNetworkEngine
from core.config_schema import DEFAULT_FULL_ALGO_PARAMS

logger = logging.getLogger(__name__)


class WealthVerificationController:
    """
    财富验证控制器
    负责协调Model和Engine，处理验证业务逻辑
    """
    
    def __init__(self, data_dir: Optional[Path] = None):
        """
        初始化控制器
        
        Args:
            data_dir: 数据目录路径
        """
        self.model = WealthCaseModel(data_dir)
        self._engine: Optional[GraphNetworkEngine] = None
        self._config = None
        
        logger.info("WealthVerificationController initialized")
    
    @property
    def engine(self) -> GraphNetworkEngine:
        """懒加载引擎"""
        if self._engine is None:
            self._config = copy.deepcopy(DEFAULT_FULL_ALGO_PARAMS)
            
            # 加载用户配置
            project_root = Path(__file__).parent.parent
            config_path = project_root / "config" / "parameters.json"
            if config_path.exists():
                import json
                with open(config_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    self._merge_config(self._config, user_config)
            
            self._engine = GraphNetworkEngine(config=self._config)
            logger.debug("GraphNetworkEngine initialized")
        
        return self._engine
    
    def set_probabilistic_mode(self, enabled: bool):
        """
        设置是否启用概率分布模式
        
        Args:
            enabled: 是否启用概率分布
        """
        if self._config is None:
            self._config = copy.deepcopy(DEFAULT_FULL_ALGO_PARAMS)
        
        if 'probabilistic_energy' not in self._config:
            self._config['probabilistic_energy'] = {}
        
        self._config['probabilistic_energy']['use_probabilistic_energy'] = enabled
        
        # 重置引擎以应用新配置
        self._engine = None
        logger.info(f"概率分布模式已{'启用' if enabled else '禁用'}")
    
    def _merge_config(self, base: Dict, update: Dict):
        """合并配置"""
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value
    
    def get_all_cases(self) -> List[WealthCase]:
        """
        获取所有案例
        
        Returns:
            案例列表
        """
        return self.model.load_all_cases()
    
    def get_case_by_id(self, case_id: str) -> Optional[WealthCase]:
        """
        根据ID获取案例
        
        Args:
            case_id: 案例ID
            
        Returns:
            案例对象
        """
        return self.model.load_case_by_id(case_id)
    
    def import_cases(self, json_data: List[Dict]) -> tuple:
        """
        导入案例
        
        Args:
            json_data: JSON数据列表
            
        Returns:
            (是否成功, 消息)
        """
        return self.model.import_cases_from_json(json_data)
    
    def add_user_feedback(self, case_id: str, year: int, real_magnitude: float, 
                         description: str, ganzhi: Optional[str] = None, 
                         dayun: Optional[str] = None) -> tuple:
        """
        [V9.3 MCP] 添加用户反馈事件
        
        Args:
            case_id: 案例ID
            year: 年份
            real_magnitude: 实际财富值
            description: 事件描述
            ganzhi: 流年干支（可选）
            dayun: 大运干支（可选）
            
        Returns:
            (是否成功, 消息)
        """
        try:
            # 获取案例
            case = self.model.load_case_by_id(case_id)
            if not case:
                return False, f"案例 {case_id} 不存在"
            
            # 创建新事件
            from core.models.wealth_case_model import WealthEvent
            new_event = WealthEvent(
                year=year,
                ganzhi=ganzhi or f"未知{year}",
                dayun=dayun or "未知",
                real_magnitude=real_magnitude,
                desc=description
            )
            
            # 检查是否已存在该年份的事件
            existing_event = None
            if case.timeline:
                for event in case.timeline:
                    if event.year == year:
                        existing_event = event
                        break
            
            if existing_event:
                # 更新现有事件
                existing_event.real_magnitude = real_magnitude
                existing_event.desc = description
                if ganzhi:
                    existing_event.ganzhi = ganzhi
                if dayun:
                    existing_event.dayun = dayun
                message = f"已更新 {year} 年的事件"
            else:
                # 添加新事件
                if not case.timeline:
                    case.timeline = []
                case.timeline.append(new_event)
                case.timeline.sort(key=lambda x: x.year)  # 按年份排序
                message = f"已添加 {year} 年的事件"
            
            # 保存案例
            if self.model.save_case(case):
                logger.info(f"User feedback saved: {case_id} - {year}年")
                return True, message
            else:
                return False, "保存失败"
                
        except Exception as e:
            logger.error(f"Error adding user feedback: {e}")
            return False, f"添加失败: {str(e)}"
    
    def verify_case(self, case: WealthCase) -> List[Dict[str, Any]]:
        """
        验证单个案例的所有事件
        
        Args:
            case: 案例对象
            
        Returns:
            验证结果列表
        """
        results = []
        
        if not case.timeline:
            logger.warning(f"Case {case.id} has no timeline events")
            return results
        
        for event in case.timeline:
            try:
                result = self.engine.calculate_wealth_index(
                    bazi=case.bazi,
                    day_master=case.day_master,
                    gender=case.gender,
                    luck_pillar=event.dayun,
                    year_pillar=event.ganzhi
                )
                
                # [V10.1] 支持概率分布验证
                wealth_distribution = None
                if isinstance(result, dict):
                    wealth_index = result.get('wealth_index', 0.0)
                    details = result.get('details', [])
                    strength_score = result.get('strength_score', 0.0)
                    strength_label = result.get('strength_label', 'Unknown')
                    opportunity = result.get('opportunity', 0.0)
                    
                    # 检查是否有概率分布数据
                    wealth_distribution = result.get('wealth_distribution')
                else:
                    wealth_index = result
                    details = []
                    strength_score = 0.0
                    strength_label = 'Unknown'
                    opportunity = 0.0
                
                # [V10.1] 概率分布验证逻辑
                if wealth_distribution:
                    # 使用概率分布进行验证
                    mean = wealth_distribution.get('mean', wealth_index)
                    std = wealth_distribution.get('std', 0.0)
                    percentiles = wealth_distribution.get('percentiles', {})
                    p25 = percentiles.get('p25', mean - std)
                    p75 = percentiles.get('p75', mean + std)
                    p50 = percentiles.get('p50', mean)
                    
                    real_value = event.real_magnitude
                    
                    # 1. 计算真实值在置信区间内的位置
                    in_confidence_interval = p25 <= real_value <= p75
                    
                    # 2. 计算真实值距离均值的标准差倍数（Z-score）
                    if std > 0:
                        z_score = (real_value - mean) / std
                    else:
                        z_score = 0.0
                    
                    # 3. 计算真实值的百分位数位置（简化版）
                    if real_value <= p25:
                        percentile_position = 'p25以下'
                    elif real_value <= p50:
                        percentile_position = 'p25-p50'
                    elif real_value <= p75:
                        percentile_position = 'p50-p75'
                    else:
                        percentile_position = 'p75以上'
                    
                    # 4. 判断是否命中（真实值在置信区间内，或距离均值在2个标准差内）
                    is_correct = in_confidence_interval or abs(z_score) <= 2.0
                    
                    # 5. 计算误差（使用均值）
                    error = abs(mean - real_value)
                    
                    # 6. 计算概率密度（简化版：基于正态分布假设）
                    if std > 0:
                        import math
                        probability_density = math.exp(-0.5 * z_score ** 2) / (std * math.sqrt(2 * math.pi))
                    else:
                        probability_density = 0.0
                else:
                    # 传统验证逻辑（单一值）
                    error = abs(wealth_index - event.real_magnitude)
                    is_correct = error <= 20.0
                    mean = wealth_index
                    std = 0.0
                    z_score = 0.0
                    percentile_position = 'N/A'
                    in_confidence_interval = False
                    probability_density = 0.0
                    p25 = p50 = p75 = wealth_index
                
                # 检查关键事件
                vault_opened = any('冲开财库' in d or '🏆' in d for d in details)
                vault_collapsed = any('冲提纲' in d or '灾难' in d or '💀' in d for d in details)
                strong_root = any('强根' in d or '帝旺' in d or '临官' in d or '长生' in d for d in details)
                
                result_dict = {
                    'year': event.year,
                    'ganzhi': event.ganzhi,
                    'dayun': event.dayun,
                    'real': event.real_magnitude,
                    'predicted': mean if wealth_distribution else wealth_index,  # 使用均值作为预测值
                    'error': error,
                    'is_correct': is_correct,
                    'strength_score': strength_score,
                    'strength_label': strength_label,
                    'opportunity': opportunity,
                    'vault_opened': vault_opened,
                    'vault_collapsed': vault_collapsed,
                    'strong_root': strong_root,
                    'details': details,
                    'desc': event.desc
                }
                
                # [V10.1] 添加概率分布相关字段
                if wealth_distribution:
                    result_dict.update({
                        'wealth_distribution': wealth_distribution,
                        'predicted_mean': mean,
                        'predicted_std': std,
                        'predicted_p25': p25,
                        'predicted_p50': p50,
                        'predicted_p75': p75,
                        'z_score': z_score,
                        'percentile_position': percentile_position,
                        'in_confidence_interval': in_confidence_interval,
                        'probability_density': probability_density
                    })
                
                results.append(result_dict)
                
            except Exception as e:
                logger.error(f"Error verifying event {event.year} for case {case.id}: {e}")
                results.append({
                    'year': event.year,
                    'ganzhi': event.ganzhi,
                    'dayun': event.dayun,
                    'real': event.real_magnitude,
                    'predicted': None,
                    'error': None,
                    'is_correct': False,
                    'error_msg': str(e),
                    'desc': event.desc
                })
        
        return results
    
    def get_verification_statistics(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        计算验证统计信息
        
        Args:
            results: 验证结果列表
            
        Returns:
            统计信息字典
        """
        if not results:
            return {
                'total_count': 0,
                'correct_count': 0,
                'hit_rate': 0.0,
                'avg_error': 0.0,
                'status': '无数据'
            }
        
        total_count = len(results)
        correct_count = sum(1 for r in results if r.get('is_correct', False))
        errors = [r.get('error', 0) for r in results if r.get('error') is not None]
        avg_error = sum(errors) / len(errors) if errors else 0.0
        hit_rate = (correct_count / total_count * 100) if total_count > 0 else 0.0
        
        # [V10.1] 概率分布相关统计
        probabilistic_results = [r for r in results if r.get('wealth_distribution')]
        probabilistic_mode = len(probabilistic_results) > 0
        
        confidence_interval_hit_rate = 0.0
        avg_z_score = 0.0
        
        if probabilistic_mode:
            # 计算置信区间命中率
            ci_hits = sum(1 for r in probabilistic_results if r.get('in_confidence_interval', False))
            confidence_interval_hit_rate = (ci_hits / len(probabilistic_results) * 100) if probabilistic_results else 0.0
            
            # 计算平均Z-score
            z_scores = [r.get('z_score', 0) for r in probabilistic_results if r.get('z_score') is not None]
            avg_z_score = sum(z_scores) / len(z_scores) if z_scores else 0.0
        
        status = "✅ 通过" if correct_count == total_count else "⚠️ 需优化"
        
        return {
            'total_count': total_count,
            'correct_count': correct_count,
            'hit_rate': hit_rate,
            'avg_error': avg_error,
            'status': status,
            # [V10.1] 概率分布相关统计
            'confidence_interval_hit_rate': confidence_interval_hit_rate,
            'avg_z_score': avg_z_score,
            'probabilistic_mode': probabilistic_mode
        }

