"""
配置管理Model (Config Model)
MVC Model Layer - 负责配置参数的持久化和加载

严格遵循MVC架构原则：
- Model层只负责数据操作（读取、保存、合并配置）
- 不包含业务逻辑
- 提供统一的配置接口
"""

import json
import logging
from pathlib import Path
from typing import Dict, Optional, Any
from copy import deepcopy

from core.config_schema import DEFAULT_FULL_ALGO_PARAMS

logger = logging.getLogger(__name__)


class ConfigModel:
    """配置管理Model - 负责配置文件的读写操作"""
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        初始化配置Model
        
        Args:
            config_path: 配置文件路径（默认为 config/parameters.json）
        """
        if config_path is None:
            project_root = Path(__file__).parent.parent.parent
            config_path = project_root / "config" / "parameters.json"
        
        self.config_path = config_path
        self._default_config = DEFAULT_FULL_ALGO_PARAMS
    
    def load_config(self) -> Dict[str, Any]:
        """
        加载配置文件
        
        Returns:
            配置字典（如果文件不存在，返回默认配置）
        """
        if not self.config_path.exists():
            logger.info(f"配置文件不存在: {self.config_path}，使用默认配置")
            return deepcopy(self._default_config)
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
            
            # 深度合并用户配置和默认配置（确保所有参数都存在）
            merged_config = deepcopy(self._default_config)
            self._deep_merge(merged_config, user_config)
            
            logger.info(f"成功加载配置文件: {self.config_path}")
            return merged_config
            
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}，使用默认配置")
            return deepcopy(self._default_config)
    
    def save_config(self, config: Dict[str, Any], merge: bool = True) -> bool:
        """
        保存配置到文件
        
        Args:
            config: 要保存的配置字典
            merge: 是否与现有配置合并（默认True）
        
        Returns:
            是否保存成功
        """
        try:
            # 确保目录存在
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            if merge and self.config_path.exists():
                # 读取现有配置
                existing_config = self.load_config()
                # 深度合并
                merged_config = deepcopy(existing_config)
                self._deep_merge(merged_config, config)
                config = merged_config
            
            # 保存配置
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            
            logger.info(f"成功保存配置文件: {self.config_path}")
            return True
            
        except Exception as e:
            logger.error(f"保存配置文件失败: {e}")
            return False
    
    def update_config_section(self, section: str, updates: Dict[str, Any]) -> bool:
        """
        更新配置的某个部分
        
        Args:
            section: 配置部分名称（如 'strength', 'structure'）
            updates: 要更新的配置字典
        
        Returns:
            是否更新成功
        """
        config = self.load_config()
        if section not in config:
            config[section] = {}
        
        # 深度合并更新
        self._deep_merge(config[section], updates)
        
        return self.save_config(config, merge=False)
    
    def get_config_section(self, section: str) -> Dict[str, Any]:
        """
        获取配置的某个部分
        
        Args:
            section: 配置部分名称
        
        Returns:
            配置部分字典（如果不存在，返回空字典）
        """
        config = self.load_config()
        return config.get(section, {})
    
    def _deep_merge(self, target: Dict, source: Dict):
        """
        深度合并两个字典（递归）
        
        Args:
            target: 目标字典（会被修改）
            source: 源字典
        """
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._deep_merge(target[key], value)
            else:
                target[key] = value
    
    def get_default_config(self) -> Dict[str, Any]:
        """
        获取默认配置
        
        Returns:
            默认配置字典的深拷贝
        """
        return deepcopy(self._default_config)
