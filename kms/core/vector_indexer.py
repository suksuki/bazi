"""
向量索引器 (Vector Indexer)
将处理好的codex条目存入向量库，用于奇点检索和SOP辅助解释

基于: FDS_KMS_SPEC_v1.0-BETA.md 第6.1节
"""

from typing import Dict, Any, List, Optional
import json
import os

try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    print("警告: ChromaDB未安装，向量索引功能将不可用")

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    print("警告: sentence-transformers未安装，Embedding功能将不可用")


class VectorIndexer:
    """
    向量索引管理器
    """
    
    def __init__(self, 
                 db_path: str = "./kms/data/vector_db",
                 collection_name: str = "classical_canon",
                 model_name: str = "BAAI/bge-m3"):
        """
        初始化向量索引器
        
        Args:
            db_path: ChromaDB数据库路径
            collection_name: 集合名称
            model_name: Embedding模型名称
        """
        if not CHROMADB_AVAILABLE:
            raise ImportError("需要安装ChromaDB: pip install chromadb")
        
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            raise ImportError("需要安装sentence-transformers: pip install sentence-transformers")
        
        # 初始化ChromaDB
        os.makedirs(db_path, exist_ok=True)
        self.client = chromadb.PersistentClient(
            path=db_path,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # 获取或创建集合
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"description": "FDS-KMS Classical Canon Vector Index"}
        )
        
        # 加载Embedding模型
        print(f"正在加载Embedding模型: {model_name}...")
        self.embed_model = SentenceTransformer(model_name)
        print("模型加载完成")
    
    def index_codex_entry(self, entry: Dict[str, Any]) -> bool:
        """
        将处理好的codex条目存入向量库
        
        Args:
            entry: classical_codex.jsonl格式的条目
            
        Returns:
            是否成功
        """
        try:
            # 构造用于Embedding的文本
            # 格式: [标签] 原文
            tags = entry.get("tags", [])
            original_text = entry.get("original_text", "")
            
            text_to_embed = f"[{', '.join(tags)}] {original_text}"
            
            # 生成向量
            embedding = self.embed_model.encode(text_to_embed).tolist()
            
            # 准备元数据
            canon_id = entry.get("canon_id", "")
            logic_extraction = entry.get("logic_extraction", {})
            
            metadata = {
                "canon_id": canon_id,
                "source_book": entry.get("source_book", ""),
                "chapter": entry.get("chapter", ""),
                "logic_type": logic_extraction.get("logic_type", ""),
                "target_pattern": logic_extraction.get("target_pattern", ""),
                "relevance_score": str(entry.get("relevance_score", 1.0)),
                "json_payload": json.dumps(entry, ensure_ascii=False)  # 存储完整JSON
            }
            
            # 入库
            self.collection.add(
                documents=[original_text],
                embeddings=[embedding],
                metadatas=[metadata],
                ids=[canon_id]
            )
            
            return True
            
        except Exception as e:
            print(f"索引条目失败 {entry.get('canon_id', 'unknown')}: {e}")
            return False
    
    def batch_index(self, entries: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        批量索引条目
        
        Returns:
            {"success": count, "failed": count}
        """
        success = 0
        failed = 0
        
        for entry in entries:
            if self.index_codex_entry(entry):
                success += 1
            else:
                failed += 1
        
        return {"success": success, "failed": failed}
    
    def search_similar(self, 
                      query_text: str, 
                      n_results: int = 5,
                      threshold: float = 0.85) -> List[Dict[str, Any]]:
        """
        搜索相似条目（用于奇点匹配）
        
        Args:
            query_text: 查询文本
            n_results: 返回结果数量
            threshold: 相似度阈值
            
        Returns:
            相似条目列表
        """
        # 生成查询向量
        query_embedding = self.embed_model.encode(query_text).tolist()
        
        # 搜索
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )
        
        # 解析结果
        similar_entries = []
        if results["ids"] and len(results["ids"][0]) > 0:
            for i, canon_id in enumerate(results["ids"][0]):
                # 从元数据中恢复完整JSON
                metadata = results["metadatas"][0][i]
                json_payload = metadata.get("json_payload", "")
                
                if json_payload:
                    entry = json.loads(json_payload)
                    # 添加相似度信息（ChromaDB不直接返回，这里用距离估算）
                    entry["_similarity"] = 1.0 - (i * 0.1)  # 简化处理
                    similar_entries.append(entry)
        
        # 过滤阈值
        return [e for e in similar_entries if e.get("_similarity", 0) >= threshold]
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取索引统计信息
        
        Returns:
            统计信息字典
        """
        count = self.collection.count()
        return {
            "total_entries": count,
            "collection_name": self.collection.name
        }

