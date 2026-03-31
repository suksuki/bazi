"""
[QGA V25.0] 神经网络路由专题注册表
管理路由参数、物理模型和格局定义
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class NeuralRouterRegistry:
    """
    神经网络路由专题注册表
    管理路由参数、物理模型定义和格局公理化定义
    """
    
    def __init__(self, registry_file: Optional[Path] = None):
        """
        初始化注册表
        
        Args:
            registry_file: 注册表JSON文件路径（可选）
        """
        if registry_file is None:
            registry_file = Path(__file__).parent / "registry.json"
        
        self.registry_file = registry_file
        self._registry_data: Dict[str, Any] = {}
        self._load_registry()
    
    def _load_registry(self):
        """加载注册表数据"""
        try:
            if self.registry_file.exists():
                with open(self.registry_file, 'r', encoding='utf-8') as f:
                    self._registry_data = json.load(f)
                logger.info(f"✅ 神经网络路由专题注册表加载成功: {self.registry_file}")
            else:
                logger.warning(f"⚠️ 注册表文件不存在: {self.registry_file}")
                self._registry_data = {}
        except Exception as e:
            logger.error(f"❌ 加载注册表失败: {e}")
            self._registry_data = {}
    
    def get_subject_info(self) -> Dict[str, Any]:
        """获取专题信息（兼容QGA标准格式）"""
        return {
            "id": self._registry_data.get("id") or self._registry_data.get("subject_id"),
            "subject_id": self._registry_data.get("subject_id"),
            "subject_name": self._registry_data.get("subject_name"),
            "name": self._registry_data.get("name") or self._registry_data.get("subject_name"),
            "name_cn": self._registry_data.get("name_cn") or self._registry_data.get("subject_name"),
            "subject_type": self._registry_data.get("subject_type"),
            "layer": self._registry_data.get("layer", "TOPIC"),
            "type": self._registry_data.get("type", "TOPIC"),
            "icon": self._registry_data.get("icon", "🧠"),
            "theme": self._registry_data.get("theme", "PATTERN_PHYSICS"),
            "description": self._registry_data.get("description"),
            "version": self._registry_data.get("version"),
            "active": self._registry_data.get("active", True)
        }
    
    def get_routing_parameter(self, param_name: str) -> Optional[Dict[str, Any]]:
        """
        获取路由参数
        
        Args:
            param_name: 参数名称（field_strength_threshold, coherence_weight, entropy_damping）
            
        Returns:
            参数定义字典，包含value、description、tunable、range等信息
        """
        routing_params = self._registry_data.get("routing_parameters", {})
        return routing_params.get(param_name)
    
    def get_routing_parameters(self) -> Dict[str, Any]:
        """获取所有路由参数"""
        return self._registry_data.get("routing_parameters", {})
    
    def get_physics_model(self, model_id: str) -> Optional[Dict[str, Any]]:
        """
        获取物理模型定义
        
        Args:
            model_id: 模型ID（feature_to_latent, sai_collapse）
            
        Returns:
            模型定义字典
        """
        physics_models = self._registry_data.get("physics_models", {})
        return physics_models.get(model_id)
    
    def get_physics_models(self) -> Dict[str, Any]:
        """获取所有物理模型定义"""
        return self._registry_data.get("physics_models", {})
    
    def get_pattern_definition(self, pattern_id: str) -> Optional[Dict[str, Any]]:
        """
        获取格局定义
        
        Args:
            pattern_id: 格局ID（如 SHANG_GUAN_JIAN_GUAN）
            
        Returns:
            格局定义字典
        """
        pattern_defs = self._registry_data.get("pattern_definitions", {})
        return pattern_defs.get(pattern_id)
    
    def get_all_pattern_definitions(self) -> Dict[str, Any]:
        """获取所有格局定义"""
        return self._registry_data.get("pattern_definitions", {})
    
    def get_pattern_ids(self) -> List[str]:
        """获取所有格局ID列表"""
        return list(self._registry_data.get("pattern_definitions", {}).keys())
    
    def get_optimization_config(self) -> Dict[str, Any]:
        """获取优化配置（自愈、离群审计等）"""
        return self._registry_data.get("optimization", {})
    
    def get_execution_kernel_config(self) -> Dict[str, Any]:
        """获取执行内核配置"""
        return self._registry_data.get("execution_kernel", {})
    
    def update_routing_parameter(self, param_name: str, value: Any):
        """
        更新路由参数值（用于运行时调优）
        
        Args:
            param_name: 参数名称
            value: 新值
        """
        routing_params = self._registry_data.setdefault("routing_parameters", {})
        if param_name in routing_params:
            old_value = routing_params[param_name].get("value")
            routing_params[param_name]["value"] = value
            logger.info(f"✅ 路由参数更新: {param_name} = {old_value} -> {value}")
        else:
            logger.warning(f"⚠️ 路由参数不存在: {param_name}")
    
    def save_registry(self):
        """保存注册表到文件"""
        try:
            with open(self.registry_file, 'w', encoding='utf-8') as f:
                json.dump(self._registry_data, f, ensure_ascii=False, indent=2)
            logger.info(f"✅ 注册表已保存: {self.registry_file}")
        except Exception as e:
            logger.error(f"❌ 保存注册表失败: {e}")


# 全局注册表实例
_global_registry: Optional[NeuralRouterRegistry] = None


def get_neural_router_registry() -> NeuralRouterRegistry:
    """获取全局神经网络路由注册表"""
    global _global_registry
    if _global_registry is None:
        _global_registry = NeuralRouterRegistry()
    return _global_registry

