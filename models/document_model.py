"""
规范文档数据模型 (Document Model)
职责：定义文档的数据结构和元数据
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Set, Tuple
from pathlib import Path
from datetime import datetime
import re
import json
import logging

@dataclass
class DocumentMetadata:
    """文档元数据"""
    title: str
    filename: str
    category: str
    version: Optional[str] = None
    description: Optional[str] = None
    last_modified: Optional[datetime] = None
    file_path: Optional[Path] = None
    deprecated: bool = False  # 是否已废弃

@dataclass
class DocumentCategory:
    """文档分类"""
    name: str
    icon: str
    description: str
    pattern: str  # 文件名匹配模式
    
    def matches(self, filename: str) -> bool:
        """检查文件名是否匹配此分类"""
        return bool(re.search(self.pattern, filename, re.IGNORECASE))


class DocumentModel:
    """文档数据模型"""
    
    # 文档分类定义
    CATEGORIES = [
        DocumentCategory(
            name="L1 物理宪法",
            icon="⚖️",
            description="[Constitution] 物理内核与不可变公理",
            pattern=r"(FDS_PHYSICS_KERNEL|ALGORITHM_CONSTITUTION|CONSTITUTION)"
        ),
        DocumentCategory(
            name="L2 逻辑协议",
            icon="📙",
            description="[Logic] 验证标准与逻辑审计协议",
            pattern=r"(QGA_LOGIC_PROTOCOL|QGA_VERIFICATION|FDS_LKV_SPEC)"
        ),
        DocumentCategory(
            name="L3 数据法典",
            icon="🗃️",
            description="[Data] 注册表结构与数据存储规范",
            pattern=r"(QGA_REGISTRY_SCHEMA|QGA_HR_REGISTRY)"
        ),
        DocumentCategory(
            name="L4 执行手册",
            icon="📗",
            description="[SOP] 标准作业程序与执行流水线",
            pattern=r"(FDS_LKV_JOINT_SOP|SOP)"
        ),
        DocumentCategory(
            name="技术报告",
            icon="📝",
            description="合规审查、迁移报告、修复文档等",
            pattern=r"(REVIEW|REPORT|FIX|UPDATE|MIGRATION|COMPLETE|Overview)"
        ),
    ]
    
    def __init__(self, docs_dir: Path):
        """
        初始化文档模型
        
        Args:
            docs_dir: 文档目录路径
        """
        self.docs_dir = docs_dir
        self._documents: List[DocumentMetadata] = []
        self._deprecated_file = docs_dir / ".deprecated_docs.json"  # 废弃文档状态文件
        self._deprecated_set: Set[str] = self._load_deprecated_status()
        self._load_documents()
    
    def _load_deprecated_status(self) -> Set[str]:
        """加载废弃文档状态"""
        if self._deprecated_file.exists():
            try:
                with open(self._deprecated_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return set(data.get('deprecated', []))
            except Exception:
                return set()
        return set()
    
    def _save_deprecated_status(self):
        """保存废弃文档状态"""
        try:
            with open(self._deprecated_file, 'w', encoding='utf-8') as f:
                json.dump({'deprecated': list(self._deprecated_set)}, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
    
    def _load_documents(self):
        """加载所有文档的元数据"""
        if not self.docs_dir.exists():
            return
        
        for md_file in self.docs_dir.glob("*.md"):
            # 跳过废弃状态文件
            if md_file.name == ".deprecated_docs.json":
                continue
                
            metadata = self._extract_metadata(md_file)
            if metadata:
                self._documents.append(metadata)
        
        # 按分类和文件名排序（废弃文档排在最后）
        self._documents.sort(key=lambda d: (d.deprecated, d.category, d.filename))
    
    def _extract_metadata(self, file_path: Path) -> Optional[DocumentMetadata]:
        """
        从文件路径提取元数据
        
        Args:
            file_path: Markdown文件路径
            
        Returns:
            文档元数据，如果无法解析则返回None
        """
        filename = file_path.name
        
        # 从文件内容提取标题（前几行）
        title, description, is_header_deprecated = self._extract_title_and_description(file_path)

        # 确定分类
        category = self._categorize_document(filename)
        if not category:
            category = "其他"
        
        # 从文件名提取版本号
        version = self._extract_version(filename)
        
        # 获取最后修改时间
        last_modified = datetime.fromtimestamp(file_path.stat().st_mtime)
        
        # 综合废弃状态：手动设置(JSON) 或 内容标记([DEPRECATED])
        is_deprecated = (filename in self._deprecated_set) or is_header_deprecated

        return DocumentMetadata(
            title=title or filename.replace('.md', ''),
            filename=filename,
            category=category,
            version=version,
            description=description,
            last_modified=last_modified,
            file_path=file_path,
            deprecated=is_deprecated
        )
    
    def _categorize_document(self, filename: str) -> Optional[str]:
        """根据文件名确定文档分类"""
        for cat in self.CATEGORIES:
            if cat.matches(filename):
                return cat.name
        return None
    
    def _extract_version(self, filename: str) -> Optional[str]:
        """从文件名提取版本号"""
        version_match = re.search(r'[vV](\d+\.\d+(?:\.\d+)?)', filename)
        if version_match:
            return version_match.group(1)
        return None
    
    def _extract_title_and_description(self, file_path: Path) -> tuple:
        """
        从文件内容提取标题和描述
        
        Returns:
            (title, description, is_deprecated) 元组
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = [line.strip() for line in f.readlines()[:15] if line.strip()]
                
                # 查找第一个一级标题
                title = None
                is_deprecated = False
                
                for line in lines:
                    if line.startswith('# ') and not line.startswith('##'):
                        title = line.replace('# ', '').strip()
                        if "[DEPRECATED]" in title or "已作废" in title:
                            is_deprecated = True
                        break
                
                # 查找描述和废弃警告
                description = None
                for i, line in enumerate(lines):
                    # 检查警告块
                    if line.startswith('>') and ("WARNING" in line or "superseded" in line or "作废" in line):
                        is_deprecated = True
                        if not description:
                             description = line.replace('>', '').replace('**WARNING**:', '').strip()

                    elif title and line == title.replace('# ', '').strip():
                        continue # Skip title line
                         
                    elif not description and line and not line.startswith('#') and not line.startswith('*'):
                         description = line[:100]

                # 重新扫描描述（逻辑简化）
                if not description:
                     for k in range(len(lines)):
                          if lines[k].startswith('#') or lines[k].startswith('*') or lines[k] == title or "[DEPRECATED]" in lines[k]: 
                              continue
                          description = lines[k][:100].replace('>', '').strip()
                          break
                
                return title, description, is_deprecated
        except Exception:
            return None, None, False
    
    def get_documents_by_category(self, category: Optional[str] = None, include_deprecated: bool = True) -> List[DocumentMetadata]:
        """
        获取指定分类的文档列表
        
        Args:
            category: 分类名称，如果为None则返回所有文档
            include_deprecated: 是否包含废弃文档
            
        Returns:
            文档元数据列表
        """
        docs = self._documents.copy()
        
        if not include_deprecated:
            docs = [doc for doc in docs if not doc.deprecated]
        
        if category:
            docs = [doc for doc in docs if doc.category == category]
        
        return docs
    
    def get_document(self, filename: str) -> Optional[DocumentMetadata]:
        """根据文件名获取文档元数据"""
        for doc in self._documents:
            if doc.filename == filename:
                return doc
        return None
    
    def get_categories(self) -> List[str]:
        """获取所有分类名称"""
        categories = set([doc.category for doc in self._documents])
        return sorted(list(categories))
    
    def read_document_content(self, filename: str) -> Optional[str]:
        """
        读取文档内容
        
        Args:
            filename: 文件名
            
        Returns:
            文档内容，如果文件不存在则返回None
        """
        doc = self.get_document(filename)
        if not doc or not doc.file_path or not doc.file_path.exists():
            return None
        
        try:
            with open(doc.file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception:
            return None
    
    def save_document_content(self, filename: str, content: str) -> bool:
        """
        保存文档内容
        
        Args:
            filename: 文件名
            content: 文档内容
            
        Returns:
            是否保存成功
        """
        doc = self.get_document(filename)
        if not doc or not doc.file_path:
            return False
        
        try:
            with open(doc.file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # 更新元数据
            doc.last_modified = datetime.now()
            return True
        except Exception:
            return False
    
    def delete_document(self, filename: str) -> bool:
        """
        删除文档文件
        
        Args:
            filename: 文件名
            
        Returns:
            是否删除成功
        """
        doc = self.get_document(filename)
        if not doc or not doc.file_path:
            return False
        
        try:
            # 删除文件
            if doc.file_path.exists():
                doc.file_path.unlink()
            
            # 从文档列表中移除
            self._documents = [d for d in self._documents if d.filename != filename]
            
            # 从废弃列表中移除
            self._deprecated_set.discard(filename)
            self._save_deprecated_status()
            
            return True
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"删除文档失败 {filename}: {e}")
            return False
    
    def get_category_info(self, category_name: str) -> Optional[DocumentCategory]:
        """获取分类信息"""
        for cat in self.CATEGORIES:
            if cat.name == category_name:
                return cat
        return None
    
    def set_deprecated(self, filename: str, deprecated: bool = True):
        """
        设置文档废弃状态
        
        Args:
            filename: 文件名
            deprecated: 是否废弃
        """
        if deprecated:
            self._deprecated_set.add(filename)
        else:
            self._deprecated_set.discard(filename)
        
        # 更新文档元数据
        doc = self.get_document(filename)
        if doc:
            doc.deprecated = deprecated
        
        # 保存状态
        self._save_deprecated_status()
    
    def is_deprecated(self, filename: str) -> bool:
        """检查文档是否已废弃"""
        return filename in self._deprecated_set
    
    def parse_document_references(self, content: str) -> Dict[str, List[str]]:
        """
        解析文档中的引用关系
        
        Args:
            content: 文档内容
            
        Returns:
            包含引用信息的字典：
            {
                'documents': List[str],  # 引用的文档文件名列表
                'config_refs': List[str],  # @config引用列表
            }
        """
        references = {
            'documents': [],
            'config_refs': []
        }
        
        # 解析文档引用（通过文件名模式）
        # 匹配模式1：完整的文件名（如 ALGORITHM_CONSTITUTION_v3.0.md）
        doc_pattern1 = r'([A-Z_]+(?:_[A-Z0-9_]+)*(?:\.md)?(?:v\d+\.\d+(?:\.\d+)?)?)'
        doc_matches = re.findall(doc_pattern1, content, re.IGNORECASE)
        
        # 匹配模式2：文档名称的简写形式（如 QGA-HR V3.0 -> QGA_HR_REGISTRY_SPEC_v3.0.md）
        # 匹配 QGA-HR, QGA_HR, ALGORITHM_CONSTITUTION 等
        doc_pattern2 = r'(?:参考|引用|见|参见|详见|参考文档|规范文档)[：:]\s*([A-Z_-]+(?:\s+V?\d+\.\d+)?)'
        doc_matches2 = re.findall(doc_pattern2, content, re.IGNORECASE)
        
        # 匹配模式3：标题中提到的文档名称（如 "QGA-HR V3.0" -> QGA_HR_REGISTRY_SPEC_v3.0.md）
        doc_pattern3 = r'(?:附录|Appendix)[：:].*?\(([A-Z_-]+(?:\s+V?\d+\.\d+)?)\)'
        doc_matches3 = re.findall(doc_pattern3, content, re.IGNORECASE)
        
        # 合并所有匹配
        all_matches = set(doc_matches + doc_matches2 + doc_matches3)
        
        # 文档名称映射（简化名 -> 完整文件名）
        doc_name_map = {
            'QGA-HR': 'QGA_HR_REGISTRY_SPEC_v3.0.md',
            'QGA_HR': 'QGA_HR_REGISTRY_SPEC_v3.0.md',
            'QGA-HR V3.0': 'QGA_HR_REGISTRY_SPEC_v3.0.md',
            'QGA_HR V3.0': 'QGA_HR_REGISTRY_SPEC_v3.0.md',
            'ALGORITHM_CONSTITUTION': 'ALGORITHM_CONSTITUTION_v3.0.md',
            'CONSTITUTION': 'ALGORITHM_CONSTITUTION_v3.0.md',
            'FDS_MODELING': 'FDS_MODELING_SPEC_v3.0.md',
            'FDS': 'FDS_MODELING_SPEC_v3.0.md',
        }
        
        for match in all_matches:
            match = match.strip()
            # 先检查是否有直接映射
            if match in doc_name_map:
                doc_name = doc_name_map[match]
            else:
                # 尝试自动匹配
                doc_name = match
                if not doc_name.endswith('.md'):
                    # 尝试构建文件名
                    # 例如: QGA-HR V3.0 -> QGA_HR_REGISTRY_SPEC_v3.0.md
                    if 'QGA' in match.upper() and 'HR' in match.upper():
                        doc_name = 'QGA_HR_REGISTRY_SPEC_v3.0.md'
                    elif 'CONSTITUTION' in match.upper():
                        doc_name = 'ALGORITHM_CONSTITUTION_v3.0.md'
                    elif 'FDS' in match.upper() and 'MODELING' in match.upper():
                        doc_name = 'FDS_MODELING_SPEC_v3.0.md'
                    else:
                        doc_name += '.md'
            
            # 检查该文档是否存在
            if self.get_document(doc_name) and doc_name not in references['documents']:
                references['documents'].append(doc_name)
        
        # 解析@config引用
        config_pattern = r'@config\.([a-zA-Z0-9_\.]+)'
        config_matches = re.findall(config_pattern, content)
        references['config_refs'] = list(set(config_matches))
        
        return references
    
    def find_document_by_title(self, title: str) -> Optional[DocumentMetadata]:
        """
        根据标题查找文档
        
        Args:
            title: 文档标题（部分匹配）
            
        Returns:
            匹配的文档元数据
        """
        title_lower = title.lower()
        for doc in self._documents:
            if title_lower in doc.title.lower() or doc.title.lower() in title_lower:
                return doc
        return None
    
    def find_documents_referencing(self, filename: str) -> List[DocumentMetadata]:
        """
        查找引用指定文档的其他文档
        
        Args:
            filename: 被引用的文档文件名
            
        Returns:
            引用该文档的文档列表
        """
        referencing = []
        target_doc = self.get_document(filename)
        if not target_doc:
            return referencing
        
        # 检查所有文档
        for doc in self._documents:
            if doc.filename == filename:
                continue
            
            content = self.read_document_content(doc.filename)
            if content:
                refs = self.parse_document_references(content)
                if filename in refs['documents'] or target_doc.title.lower() in content.lower():
                    referencing.append(doc)
        
        return referencing

