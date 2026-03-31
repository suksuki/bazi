"""
财富案例数据模型 (Wealth Case Model)
MVC Model Layer - 负责案例数据的加载、保存、管理
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class WealthEvent:
    """财富事件数据类"""
    year: int
    ganzhi: str
    dayun: str
    real_magnitude: float
    desc: str
    type: str = "WEALTH"


@dataclass
class WealthCase:
    """财富案例数据类"""
    id: str
    name: str
    bazi: List[str]
    day_master: str
    gender: str
    description: Optional[str] = None
    wealth_vaults: Optional[List[str]] = None
    timeline: Optional[List[WealthEvent]] = None
    
    def to_dict(self) -> Dict:
        """转换为字典格式"""
        result = asdict(self)
        if self.timeline:
            result['timeline'] = [asdict(event) for event in self.timeline]
        return result


class WealthCaseModel:
    """
    财富案例数据模型
    负责案例数据的CRUD操作
    """
    
    def __init__(self, data_dir: Optional[Path] = None):
        """
        初始化模型
        
        Args:
            data_dir: 数据目录路径，默认为项目根目录下的 data 文件夹
        """
        if data_dir is None:
            project_root = Path(__file__).parent.parent.parent
            data_dir = project_root / 'data'
        
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        logger.info(f"WealthCaseModel initialized with data_dir: {self.data_dir}")
    
    def load_all_cases(self) -> List[WealthCase]:
        """
        加载所有财富案例
        
        Returns:
            案例列表
        """
        cases = []
        
        # 加载所有 *_timeline.json 文件
        for file_path in self.data_dir.glob('*_timeline.json'):
            try:
                case_list = self._load_from_file(file_path)
                cases.extend(case_list)
                logger.debug(f"Loaded {len(case_list)} cases from {file_path.name}")
            except Exception as e:
                logger.error(f"Failed to load {file_path}: {e}")
        
        logger.info(f"Total {len(cases)} cases loaded")
        return cases
    
    def load_case_by_id(self, case_id: str) -> Optional[WealthCase]:
        """
        根据ID加载单个案例
        
        Args:
            case_id: 案例ID
            
        Returns:
            案例对象，如果不存在则返回None
        """
        # 尝试从所有文件中查找
        for file_path in self.data_dir.glob('*_timeline.json'):
            try:
                case_list = self._load_from_file(file_path)
                for case in case_list:
                    if case.id == case_id:
                        return case
            except Exception as e:
                logger.error(f"Failed to load {file_path}: {e}")
        
        return None
    
    def save_case(self, case: WealthCase) -> bool:
        """
        保存案例到文件
        
        Args:
            case: 案例对象
            
        Returns:
            是否保存成功
        """
        try:
            file_path = self.data_dir / f"{case.id}_timeline.json"
            case_dict = case.to_dict()
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump([case_dict], f, ensure_ascii=False, indent=2)
            
            logger.info(f"Case {case.id} saved to {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save case {case.id}: {e}")
            return False
    
    def import_cases_from_json(self, json_data: List[Dict]) -> tuple[bool, str]:
        """
        从JSON数据导入案例
        
        Args:
            json_data: JSON数据列表
            
        Returns:
            (是否成功, 消息)
        """
        try:
            imported_count = 0
            for case_dict in json_data:
                case = self._dict_to_case(case_dict)
                if self.save_case(case):
                    imported_count += 1
            
            message = f"成功导入 {imported_count}/{len(json_data)} 个案例"
            logger.info(message)
            return True, message
        except Exception as e:
            error_msg = f"导入失败: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def _load_from_file(self, file_path: Path) -> List[WealthCase]:
        """
        从文件加载案例
        
        Args:
            file_path: 文件路径
            
        Returns:
            案例列表
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 确保是列表格式
        if isinstance(data, dict):
            data = [data]
        
        cases = []
        for case_dict in data:
            case = self._dict_to_case(case_dict)
            cases.append(case)
        
        return cases
    
    def _dict_to_case(self, case_dict: Dict) -> WealthCase:
        """
        将字典转换为WealthCase对象
        
        Args:
            case_dict: 案例字典
            
        Returns:
            WealthCase对象
        """
        # 转换timeline
        timeline = None
        if 'timeline' in case_dict:
            timeline = []
            for event_dict in case_dict['timeline']:
                event = WealthEvent(
                    year=event_dict['year'],
                    ganzhi=event_dict['ganzhi'],
                    dayun=event_dict.get('dayun', '甲子'),
                    real_magnitude=event_dict.get('real_magnitude', 0.0),
                    desc=event_dict.get('desc', ''),
                    type=event_dict.get('type', 'WEALTH')
                )
                timeline.append(event)
        
        case = WealthCase(
            id=case_dict.get('id', 'UNKNOWN'),
            name=case_dict.get('name', 'Unknown'),
            bazi=case_dict.get('bazi', []),
            day_master=case_dict.get('day_master', ''),
            gender=case_dict.get('gender', '男'),
            description=case_dict.get('description'),
            wealth_vaults=case_dict.get('wealth_vaults'),
            timeline=timeline
        )
        
        return case

