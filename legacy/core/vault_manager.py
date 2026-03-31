"""
FDS-Knowledge-Vault (FKV) 核心管理类
====================================
双轨知识库系统:
- 语义库 (Semantic Vault): 存储规范文档，使用 Embedding API
- 奇点库 (Singularity Vault): 存储 5D 张量，直接作为坐标

Version: 1.0
Compliance: FDS-V3.0
"""

import logging
import os
from typing import List, Dict, Any, Optional

import chromadb
from chromadb.config import Settings

from core.config_manager import ConfigManager

logger = logging.getLogger(__name__)

# 知识库存储路径
VAULT_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "knowledge_vault")


class VaultManager:
    """
    FDS-Knowledge-Vault 核心管理类
    
    负责管理双轨知识库:
    1. 语义库 (fds_semantics): 存储规范文档、古籍、心得
    2. 奇点库 (fds_singularities): 存储 5D 特征张量，用于物理索引
    """
    
    def __init__(self, embedding_model: str = None):
        """
        初始化 VaultManager
        
        Args:
            embedding_model: Embedding 模型名称（默认从配置读取或使用 nomic-embed-text）
        """
        # 从配置读取 embedding 模型
        config = ConfigManager()
        if embedding_model is None:
            embedding_model = config.get("knowledge_vault", {}).get(
                "embedding_model", "nomic-embed-text"
            ) if isinstance(config.get("knowledge_vault"), dict) else "nomic-embed-text"
        
        self.embedding_model = embedding_model
        self._ollama_host = config.get("ollama_host", "http://localhost:11434")
        self._ollama_client = None
        
        # 初始化 ChromaDB 持久化客户端
        os.makedirs(VAULT_PATH, exist_ok=True)
        self.client = chromadb.PersistentClient(
            path=VAULT_PATH,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # 创建/获取双轨 Collection
        # 1. 语义库：使用 embedding function
        self.semantic_vault = self.client.get_or_create_collection(
            name="fds_semantics",
            metadata={"description": "FDS 规范文档与语义知识库"}
        )
        
        # 2. 奇点库：5D 张量直存，不需要 embedding
        self.singularity_vault = self.client.get_or_create_collection(
            name="fds_singularities",
            metadata={"description": "FDS 5D 特征张量（奇点存证）"}
        )
        
        logger.info(f"✅ VaultManager 初始化成功 (Embedding: {self.embedding_model})")
        logger.info(f"   - 语义库文档数: {self.semantic_vault.count()}")
        logger.info(f"   - 奇点库样本数: {self.singularity_vault.count()}")
    
    def _get_ollama_client(self):
        """获取或创建 Ollama 客户端"""
        if self._ollama_client is None:
            try:
                import ollama
                if self._ollama_host and self._ollama_host != "http://localhost:11434":
                    self._ollama_client = ollama.Client(host=self._ollama_host)
                else:
                    self._ollama_client = ollama.Client()
                logger.debug(f"Ollama 客户端已创建 (host: {self._ollama_host})")
            except ImportError:
                logger.error("❌ ollama 未安装，无法使用 embedding 功能")
                raise ImportError("请安装 ollama: pip install ollama")
        return self._ollama_client
    
    def get_embedding(self, text: str) -> List[float]:
        """
        调用 Ollama Embedding API 获取文本向量
        
        Args:
            text: 输入文本
            
        Returns:
            embedding 向量 (List[float])
        """
        client = self._get_ollama_client()
        
        try:
            response = client.embeddings(
                model=self.embedding_model,
                prompt=text
            )
            
            # Ollama embeddings API 返回格式: {"embedding": [...]}
            if isinstance(response, dict) and "embedding" in response:
                return response["embedding"]
            elif hasattr(response, "embedding"):
                return response.embedding
            else:
                raise ValueError(f"Unexpected embedding response format: {type(response)}")
                
        except Exception as e:
            logger.error(f"❌ Embedding 获取失败: {e}")
            raise
    
    def add_specification(self, step_name: str, content: str, metadata: dict = None):
        """
        注入文本规范到语义库
        
        Args:
            step_name: 规范步骤名称（如 'Step_2_Census'），作为唯一 ID
            content: 规范内容文本
            metadata: 额外元数据
        """
        # 获取 embedding
        vector = self.get_embedding(content)
        
        # 构建元数据
        meta = {"step": step_name}
        if metadata:
            meta.update(metadata)
        
        # 检查是否已存在（避免重复）
        existing = self.semantic_vault.get(ids=[step_name])
        if existing and existing.get("ids"):
            # 更新已存在的文档
            self.semantic_vault.update(
                embeddings=[vector],
                documents=[content],
                metadatas=[meta],
                ids=[step_name]
            )
            logger.info(f"📝 语义库更新: {step_name}")
        else:
            # 添加新文档
            self.semantic_vault.add(
                embeddings=[vector],
                documents=[content],
                metadatas=[meta],
                ids=[step_name]
            )
            logger.info(f"📚 语义库注入: {step_name}")
    
    def add_singularity(self, case_id: str, tensor_5d: List[float], metadata: dict = None):
        """
        注入奇点样本到奇点库
        
        Args:
            case_id: 样本唯一标识符（如 'CASE-9527'）
            tensor_5d: 5D 特征张量 [E, O, M, S, R]
            metadata: 额外元数据（如 pattern_id, abundance, distance_to_manifold）
        """
        # 验证张量维度
        if len(tensor_5d) != 5:
            raise ValueError(f"tensor_5d 必须是 5 维向量，当前维度: {len(tensor_5d)}")
        
        # 构建元数据
        meta = {"case_id": case_id}
        if metadata:
            meta.update(metadata)
        
        # 检查是否已存在
        existing = self.singularity_vault.get(ids=[case_id])
        if existing and existing.get("ids"):
            # 更新
            self.singularity_vault.update(
                embeddings=[tensor_5d],
                metadatas=[meta],
                ids=[case_id]
            )
            logger.info(f"🔄 奇点库更新: {case_id}")
        else:
            # 添加
            self.singularity_vault.add(
                embeddings=[tensor_5d],
                metadatas=[meta],
                ids=[case_id]
            )
            logger.info(f"⚛️ 奇点库注入: {case_id}")
    
    def query_singularities(
        self, 
        tensor: List[float], 
        n_results: int = 3,
        where: dict = None
    ) -> Dict[str, Any]:
        """
        物理检索：在奇点库中寻找最近邻
        
        Args:
            tensor: 查询向量 [E, O, M, S, R]
            n_results: 返回结果数量
            where: 过滤条件（如 {"pattern_id": "A-03"}）
            
        Returns:
            检索结果字典，包含 ids, distances, metadatas
        """
        if len(tensor) != 5:
            raise ValueError(f"查询张量必须是 5 维，当前维度: {len(tensor)}")
        
        results = self.singularity_vault.query(
            query_embeddings=[tensor],
            n_results=n_results,
            where=where,
            include=["metadatas", "distances", "embeddings"]
        )
        
        return {
            "ids": results.get("ids", [[]])[0],
            "distances": results.get("distances", [[]])[0],
            "metadatas": results.get("metadatas", [[]])[0],
            "embeddings": results.get("embeddings", [[]])[0]
        }
    
    def query_semantics(
        self, 
        query: str, 
        n_results: int = 3,
        where: dict = None
    ) -> Dict[str, Any]:
        """
        语义检索：在语义库中寻找相关规范
        
        Args:
            query: 查询文本
            n_results: 返回结果数量
            where: 过滤条件
            
        Returns:
            检索结果字典，包含 ids, documents, distances, metadatas
        """
        # 获取查询文本的 embedding
        query_vector = self.get_embedding(query)
        
        results = self.semantic_vault.query(
            query_embeddings=[query_vector],
            n_results=n_results,
            where=where,
            include=["metadatas", "distances", "documents"]
        )
        
        return {
            "ids": results.get("ids", [[]])[0],
            "distances": results.get("distances", [[]])[0],
            "metadatas": results.get("metadatas", [[]])[0],
            "documents": results.get("documents", [[]])[0]
        }
    
    def get_vault_stats(self) -> Dict[str, Any]:
        """获取知识库统计信息"""
        return {
            "semantic_count": self.semantic_vault.count(),
            "singularity_count": self.singularity_vault.count(),
            "vault_path": VAULT_PATH,
            "embedding_model": self.embedding_model,
            "ollama_host": self._ollama_host
        }
    
    def auto_ingest_protocol(
        self, 
        file_path: str, 
        version: str = "3.0",
        doc_type: str = "protocol"
    ) -> Dict[str, Any]:
        """
        自动分片注入规范文档 (FDS-LKV 建设宪法)
        
        按 ## 二级标题切割文档，为每个分片生成 embedding 并注入语义库。
        支持幂等性：通过标题生成 HashID，重复注入时执行覆盖更新。
        
        Args:
            file_path: 规范文档路径 (如 docs/FDS_MODELING_SPEC_v3.0.md)
            version: 规范版本号
            doc_type: 文档类型 (protocol/axiom/pattern)
            
        Returns:
            注入统计信息
        """
        import re
        import hashlib
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"规范文档不存在: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 按 ## 二级标题分片
        chunks = re.split(r'\n(?=##\s)', content)
        
        stats = {"total": 0, "injected": 0, "updated": 0, "errors": 0}
        
        for chunk in chunks:
            if len(chunk.strip()) < 50:  # 跳过过短的分片
                continue
            
            stats["total"] += 1
            
            # 提取标题作为分片名称
            title_match = re.search(r'##\s*(.+?)(?:\n|$)', chunk)
            title = title_match.group(1).strip() if title_match else "General_Spec"
            
            # 生成幂等 HashID (基于标题 + 版本)
            hash_input = f"{title}_{version}_{doc_type}"
            hash_id = f"PROT_{hashlib.md5(hash_input.encode()).hexdigest()[:12]}"
            
            try:
                # 获取 embedding
                vector = self.get_embedding(chunk)
                
                # 构建元数据
                metadata = {
                    "title": title,
                    "version": version,
                    "type": doc_type,
                    "source": os.path.basename(file_path)
                }
                
                # 检查是否已存在
                existing = self.semantic_vault.get(ids=[hash_id])
                if existing and existing.get("ids"):
                    # 覆盖更新
                    self.semantic_vault.update(
                        embeddings=[vector],
                        documents=[chunk],
                        metadatas=[metadata],
                        ids=[hash_id]
                    )
                    stats["updated"] += 1
                    logger.debug(f"📝 更新分片: {title}")
                else:
                    # 新增
                    self.semantic_vault.add(
                        embeddings=[vector],
                        documents=[chunk],
                        metadatas=[metadata],
                        ids=[hash_id]
                    )
                    stats["injected"] += 1
                    logger.debug(f"📚 注入分片: {title}")
                    
            except Exception as e:
                stats["errors"] += 1
                logger.error(f"❌ 分片注入失败 ({title}): {e}")
        
        logger.info(f"✅ 自动分片注入完成: {file_path}")
        logger.info(f"   - 总分片数: {stats['total']}")
        logger.info(f"   - 新增: {stats['injected']}, 更新: {stats['updated']}, 错误: {stats['errors']}")
        
        return stats
    
    def check_physics_compliance(self, pattern_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        合规性先验检查 (Pre-check Protocol)
        
        检索语义库中的"三大物理公理"，验证格局配置是否符合规范。
        
        Args:
            pattern_config: 格局配置字典，包含 weight_matrix, gating 等
            
        Returns:
            检查结果字典:
            - compliant: bool (是否合规)
            - violations: List[str] (违规项列表)
            - matched_axioms: List[str] (匹配到的公理)
        """
        result = {
            "compliant": True,
            "violations": [],
            "matched_axioms": [],
            "recommendations": []
        }
        
        # 1. 检索"三大物理公理"相关规范
        try:
            axiom_docs = self.query_semantics(
                query="符号守恒 拓扑特异性 正交解耦 物理公理",
                n_results=3
            )
            result["matched_axioms"] = axiom_docs.get("ids", [])
        except Exception as e:
            logger.warning(f"⚠️ 公理检索失败: {e}")
            result["recommendations"].append("建议运行规范注入脚本: auto_ingest_protocol()")
            return result
        
        # 2. 验证符号守恒 (Conservation of Sign)
        if "weight_matrix" in pattern_config or "matrix_override" in pattern_config:
            matrix = pattern_config.get("weight_matrix") or pattern_config.get("matrix_override", {})
            
            # 检查特定符号约束
            # 例如：冲 (clash) 应该增加 S (stress)
            if "clash" in str(matrix).lower():
                s_weight = matrix.get("S", 0) if isinstance(matrix, dict) else 0
                if isinstance(s_weight, (int, float)) and s_weight < 0:
                    result["compliant"] = False
                    result["violations"].append("符号守恒违规: 冲 (clash) 不应降低 S 轴")
        
        # 3. 验证安全门控 (Gating Parameters)
        if "gating" in pattern_config:
            gating = pattern_config["gating"]
            
            # 检查身旺门控
            if "weak_self_limit" in gating:
                if gating["weak_self_limit"] < 0.3 or gating["weak_self_limit"] > 0.7:
                    result["recommendations"].append(
                        f"身旺门控值 {gating['weak_self_limit']} 超出推荐范围 [0.3, 0.7]"
                    )
        
        # 4. 记录检查结果
        if result["compliant"]:
            logger.info("✅ 合规性检查通过")
        else:
            logger.warning(f"⚠️ 合规性检查发现违规: {result['violations']}")
        
        return result


# 全局单例（延迟初始化）
_vault_manager: Optional[VaultManager] = None


def get_vault_manager() -> VaultManager:
    """获取 VaultManager 单例"""
    global _vault_manager
    if _vault_manager is None:
        _vault_manager = VaultManager()
    return _vault_manager

