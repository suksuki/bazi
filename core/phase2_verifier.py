"""
V13.6 Phase 2 动态交互验证器 (Phase 2 Dynamic Interaction Verifier)
================================================================

核心功能：
- 验证生克制化的动态能量变化
- 重点关注波动的形态（标准差的变化）
- 验证熵增逻辑（被克时σ增加）和负熵逻辑（合局时σ减少）
"""

import logging
from typing import Dict, List, Any, Optional
from core.engine_graph import GraphNetworkEngine
from core.prob_math import ProbValue
from core.calculator import BaziCalculator

logger = logging.getLogger(__name__)


class Phase2Verifier:
    """
    Phase 2 动态交互验证器
    
    验证重点：
    1. Group D (生): 生方能量减少（generationDrain），波动率相对稳定
    2. Group E (克): 受克者能量减少，标准差(σ)应该变大（熵增）
    3. Group F (合): 合局者能量增加，标准差(σ)应该变小（负熵）
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化验证器
        
        Args:
            config: 算法配置
        """
        self.config = config
        self.engine = GraphNetworkEngine(config=config)
    
    def verify_case(self, case: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证单个测试案例
        
        Args:
            case: 测试案例字典，包含 bazi, day_master, gender 等字段
            
        Returns:
            验证结果字典，包含：
            - initial_energy: 初始能量（均值、标准差）
            - final_energy: 最终能量（均值、标准差）
            - delta_energy: 能量变化（均值、标准差）
            - energy_ratio: 能量比率
            - std_change: 标准差变化率
        """
        try:
            bazi = case.get('bazi', [])
            if not bazi or len(bazi) != 4:
                return {
                    'error': 'Invalid Bazi format',
                    'case_id': case.get('id', 'N/A')
                }
            
            # 解析八字
            year_stem, year_branch = bazi[0][0], bazi[0][1] if len(bazi[0]) > 1 else ''
            month_stem, month_branch = bazi[1][0], bazi[1][1] if len(bazi[1]) > 1 else ''
            day_stem, day_branch = bazi[2][0], bazi[2][1] if len(bazi[2]) > 1 else ''
            hour_stem, hour_branch = bazi[3][0], bazi[3][1] if len(bazi[3]) > 1 else ''
            
            # 计算年份（使用默认值，因为测试案例可能没有指定）
            from datetime import datetime
            birth_date = datetime(1990, 1, 1, 12)
            
            # 获取日主
            day_master = case.get('day_master', day_stem)
            
            # 初始化引擎
            self.engine.initialize_nodes(bazi, day_master)
            
            # [V13.9] 应用量子纠缠（必须在构建邻接矩阵之前，因为会改变五行属性）
            self.engine._apply_quantum_entanglement_once()
            
            # 构建邻接矩阵（在元素转化之后）
            self.engine.build_adjacency_matrix()
            
            # 获取初始能量（Phase 1 + 量子纠缠修正后）
            H0 = self.engine.H0
            if H0 is None:
                return {
                    'error': 'Failed to initialize nodes',
                    'case_id': case.get('id', 'N/A')
                }
            
            # [V13.7] 获取监控目标（优先使用测试用例中指定的 monitor_target）
            monitor_target = case.get('monitor_target', None)
            
            # 计算初始能量（在传播之前）
            if monitor_target:
                # 监控指定元素（如 "Fire", "Water" 等）
                initial_energy = self._get_element_energy(H0, monitor_target)
            else:
                # 默认监控日主能量
                initial_energy = self._get_node_energy(H0, day_master, pillar_idx=2, node_type='stem')
            
            # [V13.9] 获取调试信息（合局检测和节点变化）
            debug_info = getattr(self.engine, '_quantum_entanglement_debug', {})
            
            # 执行传播（Phase 2）
            # [V14.0] 优化传播参数：减少迭代次数，提高阻尼，降低能量损耗
            # [V9.4] 单次坍缩协议：强制单次迭代，无损阻尼
            # 物理交互（生/克/合）应当计算为一次性的能量增量，然后直接叠加到原局上
            H_final = self.engine.propagate(max_iterations=1, damping=1.0)  # 单次坍缩，无阻尼
            
            # 计算最终能量
            if monitor_target:
                final_energy = self._get_element_energy(H_final, monitor_target)
            else:
                final_energy = self._get_node_energy(H_final, day_master, pillar_idx=2, node_type='stem')
            
            # 计算能量变化
            if isinstance(initial_energy, ProbValue) and isinstance(final_energy, ProbValue):
                delta_mean = final_energy.mean - initial_energy.mean
                delta_std = final_energy.std - initial_energy.std
                energy_ratio = final_energy.mean / initial_energy.mean if initial_energy.mean != 0 else 0.0
                std_change_ratio = (final_energy.std / initial_energy.std - 1.0) * 100 if initial_energy.std != 0 else 0.0
                
                result = {
                    'case_id': case.get('id', 'N/A'),
                    'initial_energy': {
                        'mean': initial_energy.mean,
                        'std': initial_energy.std,
                        'std_percent': (initial_energy.std / initial_energy.mean * 100) if initial_energy.mean != 0 else 0.0
                    },
                    'final_energy': {
                        'mean': final_energy.mean,
                        'std': final_energy.std,
                        'std_percent': (final_energy.std / final_energy.mean * 100) if final_energy.mean != 0 else 0.0
                    },
                    'delta_energy': {
                        'mean': delta_mean,
                        'std': delta_std,
                        'mean_percent': (delta_mean / initial_energy.mean * 100) if initial_energy.mean != 0 else 0.0
                    },
                    'energy_ratio': energy_ratio,
                    'std_change_ratio': std_change_ratio,
                    'success': True
                }
                
                # [V13.9] 添加调试信息
                if debug_info:
                    result['debug_info'] = debug_info
                
                return result
            else:
                # 如果不是 ProbValue，转换为 ProbValue
                if not isinstance(initial_energy, ProbValue):
                    initial_energy = ProbValue(float(initial_energy), std_dev_percent=0.1)
                if not isinstance(final_energy, ProbValue):
                    final_energy = ProbValue(float(final_energy), std_dev_percent=0.1)
                
                delta_mean = final_energy.mean - initial_energy.mean
                delta_std = final_energy.std - initial_energy.std
                energy_ratio = final_energy.mean / initial_energy.mean if initial_energy.mean != 0 else 0.0
                std_change_ratio = (final_energy.std / initial_energy.std - 1.0) * 100 if initial_energy.std != 0 else 0.0
                
                result = {
                    'case_id': case.get('id', 'N/A'),
                    'initial_energy': {
                        'mean': initial_energy.mean,
                        'std': initial_energy.std,
                        'std_percent': (initial_energy.std / initial_energy.mean * 100) if initial_energy.mean != 0 else 0.0
                    },
                    'final_energy': {
                        'mean': final_energy.mean,
                        'std': final_energy.std,
                        'std_percent': (final_energy.std / final_energy.mean * 100) if final_energy.mean != 0 else 0.0
                    },
                    'delta_energy': {
                        'mean': delta_mean,
                        'std': delta_std,
                        'mean_percent': (delta_mean / initial_energy.mean * 100) if initial_energy.mean != 0 else 0.0
                    },
                    'energy_ratio': energy_ratio,
                    'std_change_ratio': std_change_ratio,
                    'success': True
                }
                
                # [V13.9] 添加调试信息
                if debug_info:
                    result['debug_info'] = debug_info
                
                return result
        
        except Exception as e:
            logger.exception(f"Error verifying case {case.get('id', 'N/A')}: {e}")
            return {
                'error': str(e),
                'case_id': case.get('id', 'N/A'),
                'success': False
            }
    
    def _get_node_energy(self, H: List, target_char: str, pillar_idx: int, node_type: str) -> ProbValue:
        """
        获取指定节点的能量
        
        Args:
            H: 能量向量
            target_char: 目标字符（天干或地支）
            pillar_idx: 柱索引（0=年, 1=月, 2=日, 3=时）
            node_type: 节点类型（'stem' 或 'branch'）
            
        Returns:
            节点的能量（ProbValue）
        """
        for i, node in enumerate(self.engine.nodes):
            if (node.char == target_char and 
                node.pillar_idx == pillar_idx and 
                node.node_type == node_type):
                energy = H[i]
                if isinstance(energy, ProbValue):
                    return energy
                else:
                    return ProbValue(float(energy), std_dev_percent=0.1)
        
        # 如果找不到，返回默认值
        return ProbValue(0.0, std_dev_percent=0.1)
    
    def _get_element_energy(self, H: List, target_element: str) -> ProbValue:
        """
        [V13.7] 获取指定元素的总能量
        
        Args:
            H: 能量向量
            target_element: 目标元素（'wood', 'fire', 'earth', 'metal', 'water'）
            
        Returns:
            该元素所有节点的能量总和（ProbValue）
        """
        from core.prob_math import ProbValue
        
        # 元素名称映射（支持中文和英文）
        element_map = {
            'wood': 'wood', '木': 'wood',
            'fire': 'fire', '火': 'fire',
            'earth': 'earth', '土': 'earth',
            'metal': 'metal', '金': 'metal',
            'water': 'water', '水': 'water'
        }
        
        target_element = element_map.get(target_element.lower(), target_element.lower())
        
        total_energy = ProbValue(0.0, std_dev_percent=0.1)
        
        for i, node in enumerate(self.engine.nodes):
            if node.element == target_element:
                energy = H[i]
                if isinstance(energy, ProbValue):
                    total_energy = total_energy + energy
                else:
                    total_energy = total_energy + ProbValue(float(energy), std_dev_percent=0.1)
        
        return total_energy
    
    def verify_group(self, group_cases: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        验证一组测试案例
        
        Args:
            group_cases: 测试案例列表
            
        Returns:
            验证结果列表
        """
        results = []
        for case in group_cases:
            result = self.verify_case(case)
            results.append(result)
        return results

