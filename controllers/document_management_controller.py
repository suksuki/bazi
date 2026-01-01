"""
规范文档管理控制器 (Document Management Controller)
职责：处理文档管理的业务逻辑
"""

import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from models.document_model import DocumentModel, DocumentMetadata, DocumentCategory
from controllers.registry_management_controller import RegistryManagementController

logger = logging.getLogger(__name__)

class DocumentManagementController:
    """规范文档管理控制器"""
    
    def __init__(self, docs_dir: Optional[Path] = None):
        """
        初始化控制器
        
        Args:
            docs_dir: 文档目录路径，如果为None则使用默认路径
        """
        if docs_dir is None:
            project_root = Path(__file__).resolve().parents[1]
            docs_dir = project_root / "docs"
        
        self.docs_dir = docs_dir
        self.model = DocumentModel(docs_dir)
    
    def get_categories(self) -> List[str]:
        """
        获取所有文档分类
        
        Returns:
            分类名称列表
        """
        return self.model.get_categories()
    
    def get_category_info(self, category_name: str) -> Optional[DocumentCategory]:
        """
        获取分类信息
        
        Args:
            category_name: 分类名称
            
        Returns:
            分类信息对象
        """
        return self.model.get_category_info(category_name)
    
    def get_documents_by_category(self, category: Optional[str] = None, include_deprecated: bool = True) -> List[DocumentMetadata]:
        """
        获取指定分类的文档列表
        
        Args:
            category: 分类名称，如果为None则返回所有文档
            include_deprecated: 是否包含废弃文档
            
        Returns:
            文档元数据列表
        """
        return self.model.get_documents_by_category(category, include_deprecated=include_deprecated)
    
    def get_document(self, filename: str) -> Optional[DocumentMetadata]:
        """
        获取文档元数据
        
        Args:
            filename: 文件名
            
        Returns:
            文档元数据
        """
        return self.model.get_document(filename)
    
    def read_document(self, filename: str) -> Dict[str, Any]:
        """
        读取文档内容和元数据
        
        Args:
            filename: 文件名
            
        Returns:
            包含内容和元数据的字典，格式：
            {
                'content': str,
                'metadata': DocumentMetadata,
                'success': bool,
                'error': Optional[str]
            }
        """
        doc = self.model.get_document(filename)
        if not doc:
            return {
                'content': None,
                'metadata': None,
                'success': False,
                'error': f'文档 {filename} 不存在'
            }
        
        content = self.model.read_document_content(filename)
        if content is None:
            return {
                'content': None,
                'metadata': doc,
                'success': False,
                'error': f'无法读取文档 {filename}'
            }
        
        return {
            'content': content,
            'metadata': doc,
            'success': True,
            'error': None
        }
    
    def save_document(self, filename: str, content: str) -> Dict[str, Any]:
        """
        保存文档内容
        
        Args:
            filename: 文件名
            content: 文档内容
            
        Returns:
            保存结果字典，格式：
            {
                'success': bool,
                'error': Optional[str],
                'last_modified': Optional[datetime]
            }
        """
        if not content or not content.strip():
            return {
                'success': False,
                'error': '文档内容不能为空',
                'last_modified': None
            }
        
        success = self.model.save_document_content(filename, content)
        if success:
            doc = self.model.get_document(filename)
            return {
                'success': True,
                'error': None,
                'last_modified': doc.last_modified if doc else datetime.now()
            }
        else:
            return {
                'success': False,
                'error': f'保存文档 {filename} 失败',
                'last_modified': None
            }
    
    def get_documents_summary(self) -> Dict[str, Any]:
        """
        获取文档统计摘要
        
        Returns:
            统计信息字典
        """
        all_docs = self.model.get_documents_by_category()
        categories = self.model.get_categories()
        
        summary = {
            'total_documents': len(all_docs),
            'categories': {}
        }
        
        for category in categories:
            docs = self.model.get_documents_by_category(category)
            summary['categories'][category] = {
                'count': len(docs),
                'documents': [doc.filename for doc in docs]
            }
        
        return summary
    
    def validate_document_name(self, filename: str) -> Dict[str, Any]:
        """
        验证文档名称
        
        Args:
            filename: 文件名
            
        Returns:
            验证结果字典
        """
        if not filename:
            return {
                'valid': False,
                'error': '文件名不能为空'
            }
        
        if not filename.endswith('.md'):
            return {
                'valid': False,
                'error': '文档必须是 .md 格式'
            }
        
        # 检查是否包含非法字符
        invalid_chars = ['<', '>', ':', '"', '|', '?', '*', '\\', '/']
        for char in invalid_chars:
            if char in filename:
                return {
                    'valid': False,
                    'error': f'文件名包含非法字符: {char}'
                }
        
        return {
            'valid': True,
            'error': None
        }
    
    def set_document_deprecated(self, filename: str, deprecated: bool = True) -> Dict[str, Any]:
        """
        设置文档废弃状态
        
        Args:
            filename: 文件名
            deprecated: 是否废弃
            
        Returns:
            操作结果字典
        """
        doc = self.model.get_document(filename)
        if not doc:
            return {
                'success': False,
                'error': f'文档 {filename} 不存在'
            }
        
        self.model.set_deprecated(filename, deprecated)
        
        return {
            'success': True,
            'error': None,
            'deprecated': deprecated
        }
    
    def get_document_references(self, filename: str) -> Dict[str, Any]:
        """
        获取文档的引用关系
        
        Args:
            filename: 文件名
            
        Returns:
            引用关系字典：
            {
                'references': {
                    'documents': List[str],  # 该文档引用的其他文档
                    'config_refs': List[str],  # 该文档引用的@config参数
                },
                'referenced_by': List[DocumentMetadata]  # 引用该文档的其他文档
            }
        """
        doc = self.model.get_document(filename)
        if not doc:
            return {
                'references': {'documents': [], 'config_refs': []},
                'referenced_by': []
            }
        
        content = self.model.read_document_content(filename)
        if not content:
            return {
                'references': {'documents': [], 'config_refs': []},
                'referenced_by': []
            }
        
        # 解析引用
        refs = self.model.parse_document_references(content)
        
        # 查找引用该文档的其他文档
        referenced_by = self.model.find_documents_referencing(filename)
        
        # 查找关联的注册表项
        related_registry = self.get_related_registry_items(filename, content)
        
        return {
            'references': refs,
            'referenced_by': referenced_by,
            'related_registry': related_registry
        }
    
    def get_related_registry_items(self, filename: str, content: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        根据文档和内容，查找关联的注册表项（模块或格局）
        
        Args:
            filename: 文档文件名
            content: 文档内容
            
        Returns:
            关联项字典: {'modules': [...], 'patterns': [...]}
        """
        registry_controller = RegistryManagementController()
        related = {'modules': [], 'patterns': []}
        
        # 1. 根据文档标题或文件名匹配
        doc = self.model.get_document(filename)
        search_terms = []
        if doc:
            search_terms.append(doc.title)
            # 提取版本号等关键词
            import re
            version_match = re.search(r'V\d+\.\d+', doc.title)
            if version_match:
                search_terms.append(version_match.group())
        
        # 2. 扫描内容中的特定标识符 (MOD_xx, A-xx 等)
        import re
        mod_ids = re.findall(r'\bMOD_\d+\b', content)
        pat_ids = re.findall(r'\b[A-Z]-\d+\b', content)
        
        # 3. 解析模块
        all_modules = registry_controller.manifest_data.get('modules', {})
        for mod_id in set(mod_ids):
            if mod_id in all_modules:
                info = all_modules[mod_id]
                related['modules'].append({
                    'id': mod_id,
                    'name': info.get('name', ''),
                    'active': info.get('active', False)
                })
        
        # 如果通过ID没搜到，尝试通过搜索词搜
        if not related['modules']:
            for term in search_terms:
                if len(term) < 4: continue
                search_results = registry_controller.search_modules(term)
                for res in search_results:
                    if res['id'] not in [m['id'] for m in related['modules']]:
                        related['modules'].append(res)

        # 4. 解析格局
        all_patterns = registry_controller.pattern_data.get('patterns', {})
        for pat_id in set(pat_ids):
            if pat_id in all_patterns:
                info = all_patterns[pat_id]
                related['patterns'].append({
                    'id': pat_id,
                    'name': info.get('name', ''),
                    'name_cn': info.get('name_cn', ''),
                    'active': info.get('active', False)
                })
        
        # 如果通过ID没搜到，尝试通过搜索词搜
        if not related['patterns']:
            for term in search_terms:
                if len(term) < 4: continue
                search_results = registry_controller.search_patterns(term)
                for res in search_results:
                    if res['id'] not in [p['id'] for p in related['patterns']]:
                        related['patterns'].append(res)
                        
        return related

    def render_document_with_links(self, content: str, current_filename: str) -> str:
        """
        将文档内容中的文档引用转换为可点击的链接标记
        
        Args:
            content: 文档内容
            current_filename: 当前文档的文件名
            
        Returns:
            处理后的文档内容（包含链接标记）
        """
        import re
        
        # 解析文档引用
        refs = self.model.parse_document_references(content)
        referenced_docs = refs['documents']
        
        # 为每个引用的文档创建链接标记
        for doc_filename in referenced_docs:
            doc = self.model.get_document(doc_filename)
            if not doc:
                continue
            
            # 查找文档名称在内容中的出现位置
            doc_title = doc.title
            doc_name_variants = [
                doc_filename.replace('.md', ''),  # 文件名不带扩展名
                doc.filename,  # 完整文件名
                doc_title,  # 文档标题
            ]
            
            # 添加一些常见的变体（从文档名称映射中提取）
            if 'QGA_HR_REGISTRY_SPEC' in doc_filename:
                doc_name_variants.extend(['QGA-HR', 'QGA-HR V3.0', 'QGA_HR_REGISTRY_SPEC_v3.0'])
            elif 'ALGORITHM_CONSTITUTION' in doc_filename:
                doc_name_variants.extend(['ALGORITHM_CONSTITUTION', 'CONSTITUTION'])
            elif 'FDS_MODELING_SPEC' in doc_filename:
                doc_name_variants.extend(['FDS_MODELING', 'FDS-V3.0'])
            
            # 为每个变体创建链接标记
            for variant in doc_name_variants:
                if variant and len(variant) > 3:  # 避免匹配太短的字符串
                    # 创建链接标记：{{doc_link:filename|显示文本}}
                    # 使用正则表达式替换，但只在还没被标记的情况下
                    pattern = rf'\b{re.escape(variant)}\b'
                    replacement = f'{{{{doc_link:{doc_filename}|{variant}}}}}'
                    # 避免重复替换已标记的内容
                    if f'doc_link:{doc_filename}' not in content:
                        content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)
        
        return content
    
    def resolve_config_ref_link(self, config_path: str) -> Optional[str]:
        """
        解析@config引用路径，返回对应的配置链接
        
        Args:
            config_path: 配置路径，如 'gating.weak_self_limit'
            
        Returns:
            配置链接描述，如果无法解析则返回None
        """
        try:
            from core.config import config as system_config
            # 尝试解析配置值
            full_path = f'@config.{config_path}'
            value = system_config.resolve_config_ref(full_path)
            return f"{config_path} = {value}"
        except Exception:
            return None
    
    def delete_document(self, filename: str) -> Dict[str, Any]:
        """
        删除文档
        
        Args:
            filename: 文件名
            
        Returns:
            删除结果字典，格式：
            {
                'success': bool,
                'error': Optional[str]
            }
        """
        doc = self.model.get_document(filename)
        if not doc:
            return {
                'success': False,
                'error': f'文档 {filename} 不存在'
            }
        
        # 检查是否有其他文档引用此文档
        referenced_by = self.model.find_documents_referencing(filename)
        if referenced_by:
            ref_docs = ', '.join([d.filename for d in referenced_by[:3]])
            ref_count = len(referenced_by)
            return {
                'success': False,
                'error': f'无法删除：有 {ref_count} 个文档引用了此文档。引用文档：{ref_docs}{"..." if ref_count > 3 else ""}'
            }
        
        success = self.model.delete_document(filename)
        if success:
            # 重新加载控制器以刷新状态
            self.model = DocumentModel(self.docs_dir)
            return {
                'success': True,
                'error': None
            }
        else:
            return {
                'success': False,
                'error': f'删除文档 {filename} 失败'
            }

