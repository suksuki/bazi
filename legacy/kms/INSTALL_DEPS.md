# FDS-KMS 依赖安装指南

## 必需依赖

```bash
pip install chromadb sentence-transformers numpy
```

## 可选依赖

```bash
pip install json-logic-quibble  # 用于SOP模拟（JSONLogic执行）
```

## 验证安装

```bash
# 验证ChromaDB
python -c "import chromadb; print('✅ ChromaDB已安装')"

# 验证sentence-transformers
python -c "from sentence_transformers import SentenceTransformer; print('✅ sentence-transformers已安装')"

# 验证ollama（如果使用本地LLM）
python -c "import ollama; print('✅ ollama已安装')"
```

## 注意事项

- **BGE-M3模型**: 首次运行时会自动下载（约1-2GB）
- **显存要求**: BGE-M3约占用1-2GB显存
- **网络要求**: 需要网络连接下载模型

