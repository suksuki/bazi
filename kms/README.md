# FDS-KMS: 知识库与计算语文学系统

**版本**: V1.0-BETA  
**基于**: `FDS_KMS_SPEC_v1.0-BETA.md`

---

## 📚 系统概述

FDS-KMS (Knowledge Management System) 是FDS系统的"立法层"，负责将古典文献转化为机器可执行的配置。

### 核心功能

1. **语义蒸馏** (Semantic Distillation): 将古文转化为JSONLogic和物理权重
2. **向量索引** (Vector Indexing): 建立典籍条目的向量数据库
3. **配置聚合** (Manifest Aggregation): 生成SOP所需的`pattern_manifest.json`

---

## 🏗️ 项目结构

```
kms/
├── __init__.py
├── core/
│   ├── semantic_distiller.py  # 语义蒸馏器（LLM Prompt）
│   ├── vector_indexer.py      # 向量索引器（ChromaDB）
│   └── aggregator.py          # 聚合器（RC2算法）
├── data/
│   ├── golden_test_data.json  # 黄金测试数据
│   └── pattern_manifest_example.json  # 生成的示例配置
├── scripts/
│   └── generate_manifest_example.py  # 示例脚本
└── README.md
```

---

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install chromadb sentence-transformers numpy
```

### 2. 使用语义蒸馏器

```python
from kms.core.semantic_distiller import SemanticDistiller

# 获取LLM Prompt
prompt = SemanticDistiller.get_system_prompt(
    source_book="子平真诠",
    topic="食神格"
)

# 将prompt发送给LLM，处理古文文本
# ... LLM调用 ...

# 验证输出
output = SemanticDistiller.parse_llm_response(llm_response)
is_valid, error = SemanticDistiller.validate_output(output)
```

### 3. 建立向量索引

```python
from kms.core.vector_indexer import VectorIndexer

# 初始化索引器
indexer = VectorIndexer(
    db_path="./kms/data/vector_db",
    model_name="BAAI/bge-m3"
)

# 索引条目
entry = {...}  # classical_codex格式
indexer.index_codex_entry(entry)

# 搜索相似条目
similar = indexer.search_similar("枭神夺食", n_results=5)
```

### 4. 生成配置

```python
from kms.core.aggregator import Aggregator

# 加载codex条目
entries = [...]  # 从classical_codex.jsonl加载

# 生成manifest
aggregator = Aggregator()
manifest = aggregator.generate_manifest(
    pattern_id="B-01",
    pattern_name="食神格",
    entries=entries
)

# 保存
import json
with open("pattern_manifest.json", "w") as f:
    json.dump(manifest, f, indent=2, ensure_ascii=False)
```

---

## 📖 黄金测试数据

`data/golden_test_data.json` 包含三条完美的codex条目示例：

1. **ZPZQ-09-02**: 枭神夺食破格条件
2. **ZPZQ-09-03**: 食神格成格条件
3. **ZPZQ-09-04**: 财星解救救格条件

这些数据可以作为LLM的Few-Shot样本，用于微调蒸馏效果。

---

## 🔧 运行示例

```bash
# 生成示例manifest
python kms/scripts/generate_manifest_example.py
```

---

## 📝 规范参考

- **FDS_KMS_SPEC_v1.0-BETA.md**: 核心规范文档
- **FDS_ARCHITECTURE_v3.0.md**: 架构规范（Schema定义）
- **FDS_SOP_v3.0.md**: 执行流程规范

---

## ⚠️ 注意事项

1. **LLM选择**: 建议使用具有强逻辑推理能力的模型（GPT-4o, Claude 3.5, DeepSeek-Coder-V2）
2. **Embedding模型**: 推荐BAAI/bge-m3（对中文古文理解较好）
3. **人工校验**: 初期生成的JSONLogic需要人工校验，用于Few-Shot微调
4. **向量库**: ChromaDB适合开发，生产环境建议使用Milvus

---

## 🎯 下一步

1. 使用黄金测试数据运行示例脚本
2. 准备更多古籍文本，使用语义蒸馏器处理
3. 建立完整的向量索引库
4. 生成多个格局的manifest配置
5. 集成到SOP工作流

