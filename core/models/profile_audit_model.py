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
        根据ID加载单个档案
        
        Args:
            profile_id: 档案ID
            
        Returns:
            档案字典，如果不存在则返回None
        """
        profiles = self.profile_manager.get_all()
        return next((p for p in profiles if p.get('id') == profile_id), None)

