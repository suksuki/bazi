# FDS-LKV 建设宪法 (FDS-Local Knowledge Vault Specification)

**版本**: V2.0  
**生效日期**: 2026-01-02  
**状态**: ENFORCED (强制执行)  
**测试覆盖**: 19/19 PASSED ✅

---

## 一、系统架构

### 1.1 协同矩阵

```
┌─────────────┐    协议编译    ┌─────────────┐
│     LKV     │ ────────────→ │     FDS     │
│ 逻辑指挥官   │               │ 执行工兵     │
└──────┬──────┘               └──────┬──────┘
       │                             │
       └──────────┬──────────────────┘
                  ▼
           ┌─────────────┐
           │    Cache    │
           │ (0.2ms 响应) │
           └─────────────┘
```

### 1.2 核心模块

| 模块 | 文件 | 功能 |
|------|------|------|
| VaultManager | `vault_manager.py` | 知识库管理 |
| ComplianceRouter | `compliance_router.py` | 吻合度审计 |
| ProtocolChecker | `protocol_checker.py` | 逻辑协议审计 |
| LogicCompiler | `logic_compiler.py` | LKV→FDS 编译 |
| CensusEngine | `census_engine.py` | 古典海选 |
| CensusCache | `census_cache.py` | 缓存+快速预测 |
| QGAVV Generator | `qgavv_generator.py` | 全息报告 |

---

## 二、双轨验证架构

### 2.1 路径策略

| 路径 | 条件 | 动作 |
|------|------|------|
| **GREEN** | D_M < 2.0 | 信任缓存 |
| **YELLOW** | 2.0 ≤ D_M < 3.5 | 深度审计 |
| **RED** | D_M ≥ 3.5 | 奇点溯源 |

### 2.2 双重比对闭环

```
逻辑审计 (LKV) + 物理比对 (FDS) → 综合结论
```

| 逻辑 | 物理 | 结论 |
|------|------|------|
| ✅ | ✅ | 标准成格 |
| ✅ | ❌ | 有名无实 |
| ❌ | ✅ | 异路功名 |
| ❌ | ❌ | 不入此格 |

---

## 三、知识库规范

### 3.1 语义库 (semantic_vault)

- **分片规则**: 按 `##` 二级标题切割
- **元数据**: `{"version": "3.0", "type": "protocol"}`
- **内容**: 规范文档、古典公理、海选逻辑

### 3.2 奇点库 (singularity_vault)

- **存储**: 5D 向量直存
- **关联**: 仅存储 `Case_ID`
- **检索**: Vector Similarity Search

---

## 四、测试覆盖

| 模块 | 测试数 | 状态 |
|------|--------|------|
| VaultManager | 3 | ✅ |
| ProtocolChecker | 5 | ✅ |
| LogicCompiler | 3 | ✅ |
| CensusEngine | 2 | ✅ |
| CensusCache | 4 | ✅ |
| QGAVV Generator | 2 | ✅ |

**总计**: 19/19 PASSED
