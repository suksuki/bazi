"""
向量记忆验证脚本
测试系统是否能正确检索已索引的法条
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
EMBED_MODEL_NAME = "BAAI/bge-m3"


def main():
    """验证向量记忆"""
    
    print("=" * 60)
    print("FDS-KMS 向量记忆验证")
    print("=" * 60)
    print()
    
    # 初始化
    print("📂 连接向量数据库...")
    try:
        client = chromadb.PersistentClient(path=VECTOR_DB_PATH)
        collection = client.get_collection(name=COLLECTION_NAME)
        print(f"   ✅ 数据库连接成功")
        print(f"   集合名称: {COLLECTION_NAME}")
        print(f"   当前条目数: {collection.count()}")
    except Exception as e:
        print(f"   ❌ 连接失败: {e}")
        print(f"   提示: 请先运行 vector_indexer_setup.py 建立索引")
        return
    
    print()
    
    # 加载Embedding模型
    print("🤖 加载Embedding模型...")
    try:
        emb_model = SentenceTransformer(EMBED_MODEL_NAME)
        print(f"   ✅ 模型加载完成: {EMBED_MODEL_NAME}")
    except Exception as e:
        print(f"   ❌ 模型加载失败: {e}")
        return
    
    print()
    
    # 测试查询
    test_queries = [
        "食神格遇到七杀怎么办？",
        "枭神夺食如何破解？",
        "食神格成格条件是什么？",
        "食神太旺怎么处理？"
    ]
    
    print("🔍 执行测试查询...")
    print()
    
    for query in test_queries:
        print(f"📝 提问: {query}")
        print("-" * 60)
        
        try:
            # 计算查询向量
            query_vec = emb_model.encode(query, normalize_embeddings=True).tolist()
            
            # 搜索
            results = collection.query(
                query_embeddings=[query_vec],
                n_results=2
            )
            
            if results["ids"] and len(results["ids"][0]) > 0:
                print(f"   ✅ 找到 {len(results['ids'][0])} 个相关法条:")
                print()
                
                for i, (doc, metadata) in enumerate(zip(results["documents"][0], results["metadatas"][0]), 1):
                    canon_id = metadata.get("canon_id", "unknown")
                    logic_type = metadata.get("logic_type", "unknown")
                    pattern = metadata.get("pattern", "unknown")
                    distance = results["distances"][0][i-1] if "distances" in results and results["distances"][0] else "N/A"
                    
                    print(f"   [{i}] {canon_id}")
                    print(f"       类型: {logic_type} | 格局: {pattern} | 距离: {distance:.4f}")
                    print(f"       原文: {doc[:80]}...")
                    
                    # 显示JSON Payload片段
                    json_payload = metadata.get("json_payload", "")
                    if json_payload:
                        try:
                            entry = json.loads(json_payload)
                            logic_extraction = entry.get("logic_extraction", {})
                            target_pattern = logic_extraction.get("target_pattern", "")
                            expression_type = logic_extraction.get("logic_type", "")
                            print(f"       逻辑: {target_pattern} - {expression_type}")
                        except:
                            pass
                    
                    print()
            else:
                print("   ⚠️  未找到相关法条")
                print()
            
        except Exception as e:
            print(f"   ❌ 查询失败: {e}")
            print()
        
        print()
    
    print("=" * 60)
    print("✅ 记忆验证完成")
    print("=" * 60)
    print()
    print("💡 说明:")
    print("   - 距离值越小，相似度越高")
    print("   - 如果找到的法条与查询不相关，可能需要:")
    print("     1. 增加索引的数据量")
    print("     2. 优化查询文本")
    print("     3. 调整Embedding模型")


if __name__ == "__main__":
    main()

