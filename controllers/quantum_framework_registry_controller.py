#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quantum Framework Registry Controller - MVC Controller Layer
===========================================================
量子通用架构注册信息控制器

**版本**: V1.0
**状态**: ACTIVE
**职责**: 管理量子通用架构下所有主体（Subjects）和专题（Topics/Patterns）的注册信息
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

# 配置日志
logger = logging.getLogger(__name__)


class QuantumFrameworkRegistryController:
    """
    量子通用架构注册信息控制器
    
    职责：
    - 扫描core/subjects目录下的所有主体（Subjects）
    - 读取每个主体的registry.json文件
    - 解析主体元信息和专题列表
    - 提供查询和统计接口
    """
    
    VERSION = "1.0.0"
    
    def __init__(self, subjects_dir: Optional[Path] = None):
        """
        初始化控制器
        
        Args:
            subjects_dir: 主体目录路径，默认为项目根目录下的core/subjects/
        """
        # 确定主体目录
        if subjects_dir is None:
            # 假设controller在项目根目录/controllers下
            project_root = Path(__file__).parent.parent
            self.subjects_dir = project_root / "core" / "subjects"
        else:
            self.subjects_dir = Path(subjects_dir)
        
        # 缓存
        self._cache: Optional[List[Dict[str, Any]]] = None
        self._cache_timestamp: Optional[float] = None
        
        logger.info(f"QuantumFrameworkRegistryController {self.VERSION} initialized. Subjects dir: {self.subjects_dir}")
    
    def get_all_subjects(self, force_reload: bool = False) -> List[Dict[str, Any]]:
        """
        获取所有主体（Subjects）及其专题列表
        
        Args:
            force_reload: 强制重新加载，忽略缓存
            
        Returns:
            主体列表，每个元素包含主体的完整信息
        """
        # 检查缓存
        if not force_reload and self._cache is not None:
            return self._cache
        
        subjects = []
        
        if not self.subjects_dir.exists():
            logger.warning(f"Subjects directory does not exist: {self.subjects_dir}")
            return subjects
        
        # 扫描所有主体目录
        for subject_dir in sorted(self.subjects_dir.iterdir()):
            if not subject_dir.is_dir():
                continue
            
            subject_name = subject_dir.name
            
            # 架构归一化：holographic_pattern主题直接从QGA法定路径读取
            if subject_name == "holographic_pattern":
                subject_data = self._load_holographic_pattern_from_qga()
            else:
                # 其他主题从core/subjects/{subject}/registry.json读取（传统格式）
                registry_file = subject_dir / "registry.json"
                
                subject_data = {
                    'name': subject_name,
                    'path': str(subject_dir),
                    'registry_file': str(registry_file) if registry_file.exists() else None,
                    'metadata': {},
                    'topics': {},
                    'topics_count': 0,
                    'has_registry': registry_file.exists()
                }
                
                # 读取registry.json
                if registry_file.exists():
                    try:
                        with open(registry_file, 'r', encoding='utf-8') as f:
                            registry_data = json.load(f)
                        
                        # 提取元信息
                        subject_data['metadata'] = registry_data.get('metadata', {})
                        
                        # 提取专题列表
                        topics = registry_data.get('patterns', {})
                        subject_data['topics'] = topics
                        subject_data['topics_count'] = len(topics)
                        
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse JSON file {registry_file.name}: {e}")
                        subject_data['error'] = f"JSON解析错误: {e}"
                    except Exception as e:
                        logger.error(f"Error reading registry file {registry_file.name}: {e}")
                        subject_data['error'] = f"读取错误: {e}"
                else:
                    logger.warning(f"Registry file not found: {registry_file}")
                    subject_data['metadata'] = {'description': '无registry.json文件'}
            
            subjects.append(subject_data)
        
        # 按名称排序
        subjects.sort(key=lambda x: x.get('name', ''))
        
        # 更新缓存
        self._cache = subjects
        self._cache_timestamp = datetime.now().timestamp()
        
        logger.info(f"Loaded {len(subjects)} subjects")
        return subjects
    
    def get_subject_by_name(self, subject_name: str) -> Optional[Dict[str, Any]]:
        """
        根据主体名称获取主体信息
        
        Args:
            subject_name: 主体名称（如 "bazi_fundamental"）
            
        Returns:
            主体数据字典，如果未找到则返回None
        """
        subjects = self.get_all_subjects()
        for subject in subjects:
            if subject.get('name') == subject_name:
                return subject
        return None
    
    def get_topic_by_id(self, subject_name: str, topic_id: str) -> Optional[Dict[str, Any]]:
        """
        根据主体名称和专题ID获取专题信息
        
        Args:
            subject_name: 主体名称
            topic_id: 专题ID（如 "MOD_101_SGJG_FAILURE"）
            
        Returns:
            专题数据字典，如果未找到则返回None
        """
        subject = self.get_subject_by_name(subject_name)
        if not subject:
            return None
        
        topics = subject.get('topics', {})
        return topics.get(topic_id)
    
    def get_framework_statistics(self) -> Dict[str, Any]:
        """
        获取量子通用架构的统计信息
        
        Returns:
            统计信息字典
        """
        subjects = self.get_all_subjects()
        
        stats = {
            'total_subjects': len(subjects),
            'total_topics': 0,
            'subjects_with_topics': 0,
            'by_subject': {},
            'subject_names': []
        }
        
        for subject in subjects:
            subject_name = subject.get('name', 'UNKNOWN')
            topics_count = subject.get('topics_count', 0)
            
            stats['by_subject'][subject_name] = {
                'topics_count': topics_count,
                'has_registry': subject.get('has_registry', False),
                'metadata': subject.get('metadata', {})
            }
            stats['total_topics'] += topics_count
            
            if topics_count > 0:
                stats['subjects_with_topics'] += 1
            
            stats['subject_names'].append(subject_name)
        
        return stats
    
    def clear_cache(self):
        """清除缓存，强制下次重新加载"""
        self._cache = None
        self._cache_timestamp = None
        logger.info("Framework registry cache cleared")
    
    def _load_holographic_pattern_from_qga(self) -> Dict[str, Any]:
        """
        架构归一化：从QGA法定路径读取holographic_pattern主题
        
        根据FDS_SOP_v3.0.md Step 5.3，registry/holographic_pattern/是唯一法定注册目录。
        此方法直接读取该目录下的所有QGA信封格式文件，作为该主题的专题列表。
        
        Returns:
            主体数据字典，包含topics和metadata
        """
        project_root = Path(__file__).parent.parent
        qga_registry_dir = project_root / "registry" / "holographic_pattern"
        
        subject_data = {
            'name': 'holographic_pattern',
            'path': str(qga_registry_dir),
            'registry_file': None,  # QGA格式不使用registry.json
            'metadata': {
                'description': '全息格局主题 - 从QGA法定路径加载',
                'registry_path': str(qga_registry_dir),
                'schema_version': '3.0'
            },
            'topics': {},
            'topics_count': 0,
            'has_registry': qga_registry_dir.exists()
        }
        
        if not qga_registry_dir.exists():
            logger.warning(f"QGA registry directory not found: {qga_registry_dir}")
            return subject_data
        
        patterns = {}
        
        # 扫描所有JSON文件（QGA信封格式）
        for json_file in sorted(qga_registry_dir.glob("*.json")):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    qga_data = json.load(f)
                
                # 校验QGA信封结构
                if qga_data.get('topic') != 'holographic_pattern':
                    logger.warning(f"Skipping {json_file.name}: topic mismatch (expected 'holographic_pattern')")
                    continue
                
                if 'data' not in qga_data:
                    logger.warning(f"Skipping {json_file.name}: missing 'data' field")
                    continue
                
                # 提取格局数据
                pattern_data = qga_data['data']
                pattern_id = pattern_data.get('pattern_id')
                if not pattern_id:
                    logger.warning(f"Skipping {json_file.name}: missing pattern_id")
                    continue
                
                meta_info = pattern_data.get('meta_info', {})
                population_stats = pattern_data.get('population_stats', {})
                
                # 转换为内部格式
                patterns[pattern_id] = {
                    'name_cn': meta_info.get('chinese_name', meta_info.get('display_name', pattern_id)),
                    'name_en': meta_info.get('display_name', pattern_id),
                    'description': f"类别: {meta_info.get('category', 'N/A')} | 来源: {meta_info.get('source_ref', 'N/A')}",
                    'category': meta_info.get('category', ''),
                    'version': qga_data.get('schema_version', '3.0'),
                    'abundance': population_stats.get('base_abundance', 0),
                    'sample_size': population_stats.get('sample_size', 0),
                    'sub_patterns': population_stats.get('sub_patterns', {}),
                    'source_ref': meta_info.get('source_ref', ''),
                    'qga_file': str(json_file)
                }
                
                logger.debug(f"Loaded QGA pattern: {pattern_id} from {json_file.name}")
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse QGA file {json_file.name}: {e}")
            except Exception as e:
                logger.error(f"Error loading QGA file {json_file.name}: {e}")
        
        subject_data['topics'] = patterns
        subject_data['topics_count'] = len(patterns)
        
        logger.info(f"[SYSTEM] Loaded {len(patterns)} pattern(s) from QGA registry: {qga_registry_dir}")
        
        return subject_data


if __name__ == "__main__":
    # 测试代码
    controller = QuantumFrameworkRegistryController()
    subjects = controller.get_all_subjects()
    print(f"Found {len(subjects)} subjects")
    
    stats = controller.get_framework_statistics()
    print(f"Statistics: {stats}")

