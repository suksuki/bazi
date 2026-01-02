# FDS-LKV 建设宪法 (FDS-Local Knowledge Vault Specification)

**版本**: V1.0  
**生效日期**: 2026-01-02  
**状态**: ENFORCED (强制执行)

---

## 一、系统架构设计

### 1.1 核心层级结构

| 层级 | 功能 | 存储引擎 |
|------|------|----------|
| **物理层** | 5D 张量直存，奇点溯源 | ChromaDB (fds_singularities) |
| **语义层** | 规范文档 Embedding 检索 | ChromaDB (fds_semantics) |
| **路由层** | 合规性先验检查，预测引擎对接 | Python Module |

### 1.2 技术栈

- **向量数据库**: ChromaDB >= 0.4.0 (Persistent Mode)
- **Embedding**: Ollama `nomic-embed-text`
- **张量运算**: NumPy >= 1.2.0

---

## 二、知识库注入规范

### 2.1 语义资产注入

- **分片规则**: 按 `##` 二级标题切割
- **元数据强制**: `{"version": "3.0", "type": "protocol"}`
- **幂等性**: HashID 覆盖式写入

### 2.2 奇点资产存证

- **特征提取**: 5D 向量直存，禁用 Embedding 二次转化
- **匿名关联**: 仅存储 `Case_ID`，禁止存储原始八字

---

## 三、运行与检索规范

### 3.1 合规性先验检查 (Pre-check)

```
触发时机: registry.json 加载时
检查项: 三大物理公理
- 符号守恒 (Conservation of Sign)
- 拓扑特异性 (Topological Override)
- 正交解耦 (Orthogonality)
```

### 3.2 奇点溯源检索 (Trace-back)

```
触发条件: 马氏距离 D_M > threshold
检索逻辑: Vector Similarity Search
输出: Case_ID + y_true 摘要
```

---

## 四、安全性规范

- **物理脱钩**: 禁止明文存储敏感个人信息
- **本地隔离**: `knowledge_vault/` 定期快照备份
- **版本控制**: 规范文档变更需更新 `version` 字段
