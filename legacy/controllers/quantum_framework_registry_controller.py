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
        从 QGA 总表 qga_manifest.json 的 topics.holographic_pattern 读取专题列表（FDS SOP V5.0 Step 5.4）。
        未在 qga_manifest 注册的格局不展示。若总表不存在或为空，则回退为扫描 registry/holographic_pattern/*.json。
        
        Returns:
            主体数据字典，包含topics和metadata
        """
        project_root = Path(__file__).parent.parent
        qga_manifest_path = project_root / "registry" / "qga_manifest.json"
        qga_registry_dir = project_root / "registry" / "holographic_pattern"
        
        subject_data = {
            'name': 'holographic_pattern',
            'path': str(qga_registry_dir),
            'registry_file': str(qga_manifest_path) if qga_manifest_path.exists() else None,
            'metadata': {
                'name': '全息格局',
                'name_en': 'Holographic Pattern',
                'id': 'QGA.holographic_pattern',
                'version': '5.0',
                'schema_version': '3.0',
                'description': '全息格局主题（正官格 A-01、七杀格 A-02、偏财格 A-03 等）。专题列表来自 registry/qga_manifest.json（FDS SOP V5.0 Step 5.4）。',
                'registry_path': str(qga_manifest_path),
                'specification': {'source': 'FDS_SOP_v5.0', 'topic': 'holographic_pattern'}
            },
            'topics': {},
            'topics_count': 0,
            'has_registry': qga_manifest_path.exists() or qga_registry_dir.exists()
        }
        
        patterns = {}
        
        # 优先从 qga_manifest.json 的 topics.holographic_pattern 读取（SOP V5.0）
        if qga_manifest_path.exists():
            try:
                with open(qga_manifest_path, 'r', encoding='utf-8') as f:
                    qga_manifest = json.load(f)
                entries = (qga_manifest.get('topics') or {}).get('holographic_pattern') or []
                for entry in entries:
                    pattern_id = entry.get('pattern_id')
                    if not pattern_id:
                        continue
                    manifest_ref = entry.get('manifest_ref', '')
                    version = entry.get('version', '5.0')
                    index_path = entry.get('index_path', '')
                    manifest_path = project_root / manifest_ref if manifest_ref else None
                    name_cn = pattern_id
                    name_en = pattern_id
                    category = ''
                    source_ref = ''
                    if manifest_path and manifest_path.exists():
                        try:
                            with open(manifest_path, 'r', encoding='utf-8') as mf:
                                manifest = json.load(mf)
                            meta = manifest.get('meta_info', manifest)
                            name_cn = meta.get('chinese_name', meta.get('display_name', pattern_id))
                            name_en = meta.get('display_name', pattern_id)
                            category = meta.get('category', '')
                            source_ref = meta.get('source_ref', '')
                        except Exception:
                            pass
                    patterns[pattern_id] = {
                        'name_cn': name_cn,
                        'name_en': name_en,
                        'description': f"类别: {category or 'N/A'} | manifest: {manifest_ref}",
                        'category': category,
                        'version': version,
                        'abundance': 0,
                        'sample_size': 0,
                        'sub_patterns': {},
                        'source_ref': source_ref,
                        'qga_file': str(qga_manifest_path),
                        'manifest_ref': manifest_ref,
                        'index_path': index_path,
                    }
                logger.info(f"[SYSTEM] Loaded {len(patterns)} pattern(s) from qga_manifest.json (holographic_pattern)")
            except Exception as e:
                logger.warning(f"Failed to load qga_manifest.json: {e}, falling back to directory scan")
                patterns = {}
        
        # 回退：无 qga_manifest 或 未取到任何专题 时，扫描目录下 *.json（兼容旧版）
        if not patterns and qga_registry_dir.exists():
            for json_file in sorted(qga_registry_dir.glob("*.json")):
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        qga_data = json.load(f)
                    if qga_data.get('topic') != 'holographic_pattern' or 'data' not in qga_data:
                        continue
                    pattern_data = qga_data['data']
                    pattern_id = pattern_data.get('pattern_id')
                    if not pattern_id:
                        continue
                    meta_info = pattern_data.get('meta_info', {})
                    population_stats = pattern_data.get('population_stats', {})
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
                except Exception as e:
                    logger.debug(f"Skipping {json_file.name}: {e}")
        
        subject_data['topics'] = patterns
        subject_data['topics_count'] = len(patterns)
        return subject_data


if __name__ == "__main__":
    # 测试代码
    controller = QuantumFrameworkRegistryController()
    subjects = controller.get_all_subjects()
    print(f"Found {len(subjects)} subjects")
    
    stats = controller.get_framework_statistics()
    print(f"Statistics: {stats}")

