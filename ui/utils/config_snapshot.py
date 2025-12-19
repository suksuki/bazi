"""
配置快照与回滚 (Configuration Snapshots & Rollback)
==================================================

版本控制和历史配置管理，支持配置快照、历史加载和基准线对比。

作者: Antigravity Team
版本: V10.0
日期: 2025-01-17
"""

import json
import logging
from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class ConfigSnapshotManager:
    """配置快照管理器"""
    
    def __init__(self, snapshot_dir: Path = None):
        """
        初始化快照管理器
        
        Args:
            snapshot_dir: 快照目录路径（默认: config/snapshots/）
        """
        if snapshot_dir is None:
            snapshot_dir = Path("config/snapshots")
        
        self.snapshot_dir = snapshot_dir
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)
        
        # 最新快照索引文件
        self.index_file = self.snapshot_dir / "snapshot_index.json"
        self._ensure_index_file()
    
    def _ensure_index_file(self):
        """确保索引文件存在"""
        if not self.index_file.exists():
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump({'snapshots': [], 'latest': None}, f, ensure_ascii=False, indent=2)
    
    def save_snapshot(
        self, 
        config: Dict, 
        description: str = "",
        author: str = "System",
        tags: List[str] = None
    ) -> str:
        """
        保存配置快照
        
        Args:
            config: 配置字典
            description: 快照描述
            author: 作者
            tags: 标签列表
        
        Returns:
            快照文件名
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        snapshot_file = self.snapshot_dir / f"parameters_v10.0_{timestamp}.json"
        
        snapshot_data = {
            'version': '10.0',
            'timestamp': timestamp,
            'datetime': datetime.now().isoformat(),
            'description': description,
            'author': author,
            'tags': tags or [],
            'config': config
        }
        
        # 保存快照文件
        with open(snapshot_file, 'w', encoding='utf-8') as f:
            json.dump(snapshot_data, f, ensure_ascii=False, indent=2)
        
        # 更新索引
        self._update_index(snapshot_file.name, snapshot_data)
        
        logger.info(f"✅ 配置快照已保存: {snapshot_file.name}")
        return str(snapshot_file)
    
    def _update_index(self, snapshot_filename: str, snapshot_data: Dict):
        """更新快照索引"""
        with open(self.index_file, 'r', encoding='utf-8') as f:
            index = json.load(f)
        
        # 添加到索引
        index_entry = {
            'filename': snapshot_filename,
            'timestamp': snapshot_data['timestamp'],
            'datetime': snapshot_data['datetime'],
            'description': snapshot_data['description'],
            'author': snapshot_data['author'],
            'tags': snapshot_data['tags']
        }
        
        index['snapshots'].append(index_entry)
        index['latest'] = snapshot_filename
        
        # 保存索引
        with open(self.index_file, 'w', encoding='utf-8') as f:
            json.dump(index, f, ensure_ascii=False, indent=2)
    
    def load_snapshot(self, snapshot_filename: str) -> Dict:
        """
        加载配置快照
        
        Args:
            snapshot_filename: 快照文件名
        
        Returns:
            配置字典
        """
        snapshot_file = self.snapshot_dir / snapshot_filename
        
        if not snapshot_file.exists():
            raise FileNotFoundError(f"快照文件不存在: {snapshot_file}")
        
        with open(snapshot_file, 'r', encoding='utf-8') as f:
            snapshot_data = json.load(f)
        
        logger.info(f"✅ 已加载配置快照: {snapshot_filename}")
        return snapshot_data['config']
    
    def list_snapshots(self, limit: int = 50) -> List[Dict]:
        """
        列出所有快照
        
        Args:
            limit: 返回的最大数量
        
        Returns:
            快照列表
        """
        with open(self.index_file, 'r', encoding='utf-8') as f:
            index = json.load(f)
        
        # 按时间倒序排序
        snapshots = sorted(
            index.get('snapshots', []),
            key=lambda x: x['timestamp'],
            reverse=True
        )
        
        return snapshots[:limit]
    
    def get_latest_snapshot(self) -> Optional[str]:
        """获取最新快照文件名"""
        with open(self.index_file, 'r', encoding='utf-8') as f:
            index = json.load(f)
        return index.get('latest')
    
    def delete_snapshot(self, snapshot_filename: str) -> bool:
        """
        删除快照
        
        Args:
            snapshot_filename: 快照文件名
        
        Returns:
            是否成功
        """
        snapshot_file = self.snapshot_dir / snapshot_filename
        
        if not snapshot_file.exists():
            return False
        
        # 删除文件
        snapshot_file.unlink()
        
        # 从索引中移除
        with open(self.index_file, 'r', encoding='utf-8') as f:
            index = json.load(f)
        
        index['snapshots'] = [
            s for s in index['snapshots'] 
            if s['filename'] != snapshot_filename
        ]
        
        # 如果删除的是最新快照，更新最新快照
        if index.get('latest') == snapshot_filename:
            index['latest'] = index['snapshots'][0]['filename'] if index['snapshots'] else None
        
        with open(self.index_file, 'w', encoding='utf-8') as f:
            json.dump(index, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ 已删除快照: {snapshot_filename}")
        return True


# 全局快照管理器实例
_snapshot_manager = None

def get_snapshot_manager() -> ConfigSnapshotManager:
    """获取全局快照管理器实例"""
    global _snapshot_manager
    if _snapshot_manager is None:
        _snapshot_manager = ConfigSnapshotManager()
    return _snapshot_manager

