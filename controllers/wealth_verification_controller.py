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
                
                if isinstance(result, dict):
                    wealth_index = result.get('wealth_index', 0.0)
                    details = result.get('details', [])
                    strength_score = result.get('strength_score', 0.0)
                    strength_label = result.get('strength_label', 'Unknown')
                    opportunity = result.get('opportunity', 0.0)
                else:
                    wealth_index = result
                    details = []
                    strength_score = 0.0
                    strength_label = 'Unknown'
                    opportunity = 0.0
                
                error = abs(wealth_index - event.real_magnitude)
                is_correct = error <= 20.0
                
                # 检查关键事件
                vault_opened = any('冲开财库' in d or '🏆' in d for d in details)
                vault_collapsed = any('冲提纲' in d or '灾难' in d or '💀' in d for d in details)
                strong_root = any('强根' in d or '帝旺' in d or '临官' in d or '长生' in d for d in details)
                
                results.append({
                    'year': event.year,
                    'ganzhi': event.ganzhi,
                    'dayun': event.dayun,
                    'real': event.real_magnitude,
                    'predicted': wealth_index,
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
                })
                
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
        
        status = "✅ 通过" if correct_count == total_count else "⚠️ 需优化"
        
        return {
            'total_count': total_count,
            'correct_count': correct_count,
            'hit_rate': hit_rate,
            'avg_error': avg_error,
            'status': status
        }

