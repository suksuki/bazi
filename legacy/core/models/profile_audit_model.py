"""
八字档案审计数据模型 (Profile Audit Model)
MVC Model Layer - 负责档案审计的数据模型
"""

import logging
from typing import List, Dict, Optional, Any
from pathlib import Path
from dataclasses import dataclass

from core.profile_manager import ProfileManager

logger = logging.getLogger(__name__)


@dataclass
class ProfileAuditResult:
    """档案审计结果数据类"""
    profile_id: str
    profile_name: str
    is_valid: bool
    issues: List[str]
    warnings: List[str]
    completeness_score: float
    data_quality_score: float


class ProfileAuditModel:
    """
    八字档案审计数据模型
    负责档案数据的审计和管理
    """
    
    def __init__(self, data_dir: Optional[Path] = None):
        """
        初始化模型
        
        Args:
            data_dir: 数据目录路径
        """
        if data_dir is None:
            project_root = Path(__file__).parent.parent.parent
            data_dir = project_root / 'data'
        
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        self.profile_manager = ProfileManager()
        
        logger.info(f"ProfileAuditModel initialized with data_dir: {self.data_dir}")
    
    def load_all_profiles(self) -> List[Dict[str, Any]]:
        """
        加载所有档案
        
        Returns:
            档案列表
        """
        return self.profile_manager.get_all()
    
    def load_profile_by_id(self, profile_id: str) -> Optional[Dict[str, Any]]:
        """
        [QGA V24.7] 根据ID加载单个档案，支持虚拟档案（硬编码模式）
        
        如果ProfileManager中找不到，尝试从Pattern Lab加载虚拟档案
        
        Args:
            profile_id: 档案ID
            
        Returns:
            档案字典，如果不存在则返回None
        """
        # 1. 先从ProfileManager加载
        profiles = self.profile_manager.get_all()
        profile = next((p for p in profiles if p.get('id') == profile_id), None)
        
        if profile:
            # 检查是否为虚拟档案（需要补充硬编码字段）
            if profile.get('name', '').startswith('虚拟-'):
                # 尝试从Pattern Lab重新生成以获取硬编码字段
                try:
                    from tests.pattern_lab import generate_synthetic_bazi, PATTERN_TEMPLATES
                    # 从名称推断格局ID
                    pattern_id = None
                    for pid, template in PATTERN_TEMPLATES.items():
                        if template['name'] == profile.get('name'):
                            pattern_id = pid
                            break
                    
                    if pattern_id:
                        # 重新生成虚拟档案以获取硬编码字段
                        virtual_profile = generate_synthetic_bazi(pattern_id, use_hardcoded=True)
                        # 合并数据（保留ProfileManager的ID和创建时间）
                        virtual_profile['id'] = profile['id']
                        virtual_profile['created_at'] = profile.get('created_at', virtual_profile.get('created_at'))
                        logger.info(f"✅ 加载虚拟档案硬编码字段: {profile.get('name')} -> {pattern_id}")
                        return virtual_profile
                except Exception as e:
                    logger.warning(f"加载虚拟档案硬编码字段失败: {e}，使用标准档案")
            
            return profile
        
        # 2. 如果ProfileManager中找不到，尝试从Pattern Lab加载
        try:
            from tests.pattern_lab import generate_synthetic_bazi, PATTERN_TEMPLATES
            # 遍历所有格局模板，查找匹配的ID
            for pattern_id, template in PATTERN_TEMPLATES.items():
                # 生成虚拟档案检查ID
                virtual_profile = generate_synthetic_bazi(pattern_id, use_hardcoded=True)
                if virtual_profile.get('id') == profile_id:
                    logger.info(f"✅ 从Pattern Lab加载虚拟档案: {pattern_id}")
                    return virtual_profile
        except Exception as e:
            logger.debug(f"从Pattern Lab加载虚拟档案失败: {e}")
        
        return None

