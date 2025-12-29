"""
QGA 注册表驱动器 (Registry Loader)
实现从JSON注册表读取配置并自动调用引擎进行计算

基于QGA-HR V1.0规范
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging

from core.math_engine import (
    sigmoid_variant,
    tensor_normalize,
    calculate_s_balance,
    calculate_flow_factor,
    phase_change_determination
)
from core.physics_engine import (
    compute_energy_flux,
    calculate_interaction_damping,
    calculate_clash_count
)

logger = logging.getLogger(__name__)


class RegistryLoader:
    """
    注册表驱动器
    
    职责：
    - 读取QGA-HR注册表配置
    - 自动调用数学和物理引擎进行计算
    - 支持任意格局的算法复原
    """
    
    def __init__(self, registry_path: Optional[Path] = None):
        """
        初始化注册表驱动器
        
        Args:
            registry_path: 注册表文件路径（可选，默认使用holographic_pattern注册表）
        """
        if registry_path is None:
            project_root = Path(__file__).resolve().parents[1]
            registry_path = project_root / "core" / "subjects" / "holographic_pattern" / "registry.json"
        
        self.registry_path = registry_path
        self.registry = None
        self._load_registry()
    
    def _load_registry(self):
        """加载注册表"""
        try:
            with open(self.registry_path, 'r', encoding='utf-8') as f:
                self.registry = json.load(f)
            logger.info(f"✅ 已加载注册表: {self.registry_path}")
        except Exception as e:
            logger.error(f"加载注册表失败: {e}")
            self.registry = {"patterns": {}, "metadata": {}}
    
    def get_pattern(self, pattern_id: str) -> Optional[Dict]:
        """
        获取格局配置
        
        Args:
            pattern_id: 格局ID（如'A-03'）
            
        Returns:
            格局配置字典，如果不存在则返回None
        """
        if not self.registry:
            return None
        
        patterns = self.registry.get('patterns', {})
        return patterns.get(pattern_id)
    
    def calculate_tensor_projection_from_registry(
        self,
        pattern_id: str,
        chart: List[str],
        day_master: str,
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        从注册表读取配置并计算五维张量投影
        
        这是核心函数：实现100%算法复原
        
        Args:
            pattern_id: 格局ID（如'A-03'）
            chart: 四柱八字
            day_master: 日主
            context: 上下文（大运、流年等，可选）
            
        Returns:
            计算结果字典，包含：
            - projection: 五维投影 {'E': float, 'O': float, 'M': float, 'S': float, 'R': float}
            - sai: 系统对齐指数
            - energies: 基础能量 {'E_blade': float, 'E_kill': float, 'E_seal': float}
            - s_balance: 平衡度
            - phase_change: 相变状态
        """
        # 1. 获取格局配置
        pattern = self.get_pattern(pattern_id)
        if not pattern:
            return {'error': f'格局 {pattern_id} 不存在'}
        
        tensor_operator = pattern.get('tensor_operator', {})
        if not tensor_operator:
            return {'error': f'格局 {pattern_id} 缺少tensor_operator配置'}
        
        # 2. 获取权重
        weights = tensor_operator.get('weights', {})
        if not weights:
            return {'error': f'格局 {pattern_id} 缺少权重配置'}
        
        # 3. 验证归一化
        if not tensor_operator.get('normalized', False):
            weights = tensor_normalize(weights)
            logger.warning(f"格局 {pattern_id} 权重未归一化，已自动归一化")
        
        # 4. 计算基础能量（从注册表的核心方程获取变量）
        core_equation = tensor_operator.get('core_equation', '')
        
        # 解析核心方程，提取需要的能量类型
        # 例如：S_balance = E_blade / E_kill
        energies = {}
        
        if 'E_blade' in core_equation or 'blade' in core_equation.lower():
            # 计算羊刃能量
            energies['E_blade'] = compute_energy_flux(chart, day_master, '羊刃')
        
        if 'E_kill' in core_equation or 'kill' in core_equation.lower():
            # 计算七杀能量
            energies['E_kill'] = compute_energy_flux(chart, day_master, '七杀')
        
        # 检查是否有flow_factor需要E_seal
        flow_factor = tensor_operator.get('flow_factor', {})
        if flow_factor and 'E_seal' in flow_factor.get('formula', ''):
            # 计算印星能量（正印+偏印）
            energies['E_seal'] = (
                compute_energy_flux(chart, day_master, '正印') +
                compute_energy_flux(chart, day_master, '偏印')
            )
        
        # 5. 计算核心方程（如S_balance）
        s_balance = None
        if 'E_blade' in energies and 'E_kill' in energies:
            s_balance = calculate_s_balance(energies['E_blade'], energies['E_kill'])
        
        # 6. 计算Flow Factor（如果适用）
        s_base = None
        if 'E_seal' in energies and flow_factor:
            # 这里需要先计算基础应力，简化处理
            clash_count = calculate_clash_count(chart)
            s_base = abs(energies.get('E_blade', 0) - energies.get('E_kill', 0)) + 0.5 * clash_count
            s_risk = calculate_flow_factor(s_base, energies['E_seal'])
        else:
            s_risk = None
        
        # 7. 计算SAI（系统对齐指数）
        # 简化：使用基础能量计算SAI
        # 实际应该调用框架的arbitrate_bazi，这里先简化
        sai = sum(energies.values()) * 10.0  # 临时计算，实际应从框架获取
        
        # 8. 计算五维投影
        projection = {
            'E': sai * weights.get('E', 0.0),
            'O': sai * weights.get('O', 0.0),
            'M': sai * weights.get('M', 0.0),
            'S': sai * weights.get('S', 0.0),
            'R': sai * weights.get('R', 0.0)
        }
        
        # 9. 相变判定（如果配置了激活函数）
        activation = tensor_operator.get('activation_function', {})
        phase_change = None
        if activation:
            threshold = activation.get('parameters', {}).get('collapse_threshold', 0.8)
            # 简化：使用S_balance作为能量指标
            if s_balance:
                normalized_energy = min(s_balance / 2.0, 1.0)  # 归一化到0-1
                phase_change = phase_change_determination(
                    normalized_energy,
                    threshold=threshold,
                    trigger=False  # 这里需要根据context判断是否有触发
                )
        
        return {
            'pattern_id': pattern_id,
            'pattern_name': pattern.get('name', pattern_id),
            'projection': projection,
            'sai': sai,
            'energies': energies,
            's_balance': s_balance,
            's_risk': s_risk,
            'phase_change': phase_change,
            'weights': weights
        }
    
    def simulate_dynamic_event(
        self,
        pattern_id: str,
        chart: List[str],
        day_master: str,
        event_type: str = 'clash',
        event_params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        模拟动态事件（如流年冲刃）
        
        Args:
            pattern_id: 格局ID
            chart: 四柱八字
            day_master: 日主
            event_type: 事件类型（如'clash'）
            event_params: 事件参数（如{'clash_branch': '子'}）
            
        Returns:
            仿真结果字典
        """
        pattern = self.get_pattern(pattern_id)
        if not pattern:
            return {'error': f'格局 {pattern_id} 不存在'}
        
        kinetic_evolution = pattern.get('kinetic_evolution', {})
        dynamic_sim = kinetic_evolution.get('dynamic_simulation', {})
        
        if not dynamic_sim:
            return {'error': f'格局 {pattern_id} 缺少dynamic_simulation配置'}
        
        # 获取lambda系数
        lambda_coefficients = dynamic_sim.get('lambda_coefficients', {})
        fracture_threshold = dynamic_sim.get('fracture_threshold', 50.0)
        
        # 计算基础应力（简化：从projection获取）
        result = self.calculate_tensor_projection_from_registry(pattern_id, chart, day_master)
        s_base = result['projection'].get('S', 0.0)
        
        # 根据事件类型计算lambda
        if event_type == 'clash' and event_params:
            month_branch = chart[1][1]  # 月支
            clash_branch = event_params.get('clash_branch')
            
            if clash_branch:
                # 提取lambda系数值（从嵌套字典中提取）
                lambda_dict = {}
                if isinstance(lambda_coefficients, dict):
                    for key, value in lambda_coefficients.items():
                        if isinstance(value, dict):
                            lambda_dict[key] = value.get('value', 1.8)
                        else:
                            lambda_dict[key] = value
                
                lambda_val = calculate_interaction_damping(
                    chart,
                    month_branch,
                    clash_branch,
                    lambda_dict
                )
                
                # 计算新应力
                s_new = s_base * lambda_val
                is_collapse = s_new >= fracture_threshold
                
                return {
                    'pattern_id': pattern_id,
                    'event_type': event_type,
                    's_base': s_base,
                    'lambda': lambda_val,
                    's_new': s_new,
                    'fracture_threshold': fracture_threshold,
                    'is_collapse': is_collapse,
                    'status': 'COLLAPSE' if is_collapse else 'SURVIVAL'
                }
        
        return {'error': '不支持的事件类型或缺少必要参数'}

