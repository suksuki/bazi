"""
向量索引器设置脚本
激活向量记忆，将Codex条目存入ChromaDB

基于: FDS_KMS_SPEC_v1.0-BETA.md 第6.1节
"""

import json
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

try:
    import chromadb
    from sentence_transformers import SentenceTransformer
    DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    DEPENDENCIES_AVAILABLE = False
    print(f"❌ 依赖未安装: {e}")
    print("   安装命令: pip install chromadb sentence-transformers")
    sys.exit(1)


# 配置
VECTOR_DB_PATH = os.path.join(os.path.dirname(__file__), '../data/vector_db')
COLLECTION_NAME = "classical_canon"
EMBED_MODEL_NAME = "BAAI/bge-m3"  # 或使用 'BAAI/bge-base-zh-v1.5' 作为备选


class LocalBGEEmbeddingFunction:
    """自定义嵌入函数，调用本地 BGE-M3"""
    
    def __init__(self, model_name: str):
        print(f"📥 正在加载Embedding模型: {model_name}...")
        print("   (首次运行需要下载模型，请耐心等待)")
        self.model = SentenceTransformer(model_name)
        print(f"   ✅ 模型加载完成")
    
    def __call__(self, input_texts):
        """将文本列表转换为向量"""
        if isinstance(input_texts, str):
            input_texts = [input_texts]
        embeddings = self.model.encode(input_texts, normalize_embeddings=True)
        return embeddings.tolist()


def init_vector_db():
    """初始化向量数据库"""
    print("=" * 60)
    print("初始化向量数据库")
    print("=" * 60)
    print()
    
    # 1. 初始化ChromaDB (持久化存储)
    print(f"📂 数据库路径: {VECTOR_DB_PATH}")
    os.makedirs(VECTOR_DB_PATH, exist_ok=True)
    
    client = chromadb.PersistentClient(path=VECTOR_DB_PATH)
    print("   ✅ ChromaDB客户端已创建")
    print()
    
    # 2. 绑定嵌入模型
    print("🤖 加载Embedding模型...")
    emb_fn = LocalBGEEmbeddingFunction(EMBED_MODEL_NAME)
    print()
    
    # 3. 获取或创建集合（使用默认embedding，手动计算向量）
    print(f"📚 创建/获取集合: {COLLECTION_NAME}")
    
    # ChromaDB新版本可能需要使用default_embedding_function
    # 我们使用自定义方式：手动计算embedding
    try:
        collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine", "description": "FDS-KMS Classical Canon Vector Index"}
        )
    except Exception:
        # 如果失败，尝试不使用embedding_function
        collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine", "description": "FDS-KMS Classical Canon Vector Index"}
        )
    
    print("   ✅ 集合已创建")
    print()
    
    return collection, client, emb_fn


def index_entry(collection, codex_entry: dict, emb_fn=None):
    """将一条Codex条目入库"""
    canon_id = codex_entry.get("canon_id", "unknown")
    
    # 构造用于搜索的文本：[标签] + 原文
    tags = codex_entry.get("tags", [])
    original_text = codex_entry.get("original_text", "")
    searchable_text = f"[{', '.join(tags)}] {original_text}"
    
    # 准备元数据
    logic_extraction = codex_entry.get("logic_extraction", {})
    metadata = {
        "canon_id": canon_id,
        "source_book": codex_entry.get("source_book", ""),
        "chapter": codex_entry.get("chapter", ""),
        "pattern": logic_extraction.get("target_pattern", ""),
        "logic_type": logic_extraction.get("logic_type", ""),
        "relevance_score": str(codex_entry.get("relevance_score", 1.0)),
        "json_payload": json.dumps(codex_entry, ensure_ascii=False)  # 存入完整JSON
    }
    
    # 计算embedding（如果提供了embedding函数）
    embeddings = None
    if emb_fn:
        embeddings = [emb_fn([searchable_text])[0]]
    
    # 入库
    if embeddings:
        collection.add(
            documents=[searchable_text],
            embeddings=embeddings,
            metadatas=[metadata],
            ids=[canon_id]
        )
    else:
        collection.add(
            documents=[searchable_text],
            metadatas=[metadata],
            ids=[canon_id]
        )
    
    return True


def search_similar(collection, query_text: str, n_results: int = 5, emb_fn=None):
    """搜索相似条目"""
    # 如果提供了embedding函数，手动计算query embedding
    query_embeddings = None
    if emb_fn:
        query_embeddings = [emb_fn([query_text])[0]]
    
    if query_embeddings:
        results = collection.query(
            query_embeddings=query_embeddings,
            n_results=n_results
        )
    else:
        results = collection.query(
            query_texts=[query_text],
            n_results=n_results
        )
    
    similar_entries = []
    if results["ids"] and len(results["ids"][0]) > 0:
        for i, canon_id in enumerate(results["ids"][0]):
            metadata = results["metadatas"][0][i]
            json_payload = metadata.get("json_payload", "")
            
            if json_payload:
                entry = json.loads(json_payload)
                # 添加距离信息（ChromaDB返回的距离）
                if "distances" in results and results["distances"][0]:
                    entry["_distance"] = results["distances"][0][i]
                similar_entries.append(entry)
    
    return similar_entries


def main():
    """主函数：测试向量索引"""
    
    print("🚀 FDS-KMS 向量索引器设置")
    print()
    
    # 初始化数据库
    collection, client, emb_fn = init_vector_db()
    
    # 加载黄金测试数据
    print("📚 加载测试数据...")
    data_path = os.path.join(os.path.dirname(__file__), '../data/golden_test_data.json')
    
    try:
        with open(data_path, 'r', encoding='utf-8') as f:
            entries = json.load(f)
        print(f"   ✅ 加载了 {len(entries)} 条codex条目")
        print()
    except FileNotFoundError:
        print(f"   ❌ 文件不存在: {data_path}")
        return
    
    # 索引条目
    print("💾 索引codex条目...")
    success_count = 0
    for entry in entries:
        try:
            index_entry(collection, entry, emb_fn)
            canon_id = entry.get("canon_id", "unknown")
            print(f"   ✅ 已索引: {canon_id}")
            success_count += 1
        except Exception as e:
            print(f"   ❌ 索引失败 {entry.get('canon_id', 'unknown')}: {e}")
    
    print()
    print(f"✅ 成功索引 {success_count}/{len(entries)} 条条目")
    print()
    
    # 测试搜索
    print("🔍 测试相似度搜索...")
    print()
    
    test_queries = [
        "枭神夺食",
        "食神格成格条件",
        "财星解救"
    ]
    
    for query in test_queries:
        print(f"查询: {query}")
        similar = search_similar(collection, query, n_results=2, emb_fn=emb_fn)
        print(f"   找到 {len(similar)} 个相似条目:")
        for entry in similar:
            canon_id = entry.get("canon_id", "unknown")
            logic_type = entry.get("logic_extraction", {}).get("logic_type", "unknown")
            distance = entry.get("_distance", "N/A")
            print(f"      - {canon_id}: {logic_type} (距离: {distance})")
        print()
    
    # 显示统计信息
    stats = collection.count()
    print("=" * 60)
    print("📊 数据库统计")
    print("=" * 60)
    print(f"   总条目数: {stats}")
    print(f"   数据库路径: {VECTOR_DB_PATH}")
    print(f"   集合名称: {COLLECTION_NAME}")
    print()
    print("✅ 向量索引器设置完成！")
    print()
    print("💡 下一步:")
    print("   1. 使用向量索引器进行奇点检索")
    print("   2. 集成到SOP工作流的Step 5.4")
    print("   3. 批量索引更多codex条目")


if __name__ == "__main__":
    main()

