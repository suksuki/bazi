# Phase 3 执行指南

**日期**: 2026-01-03  
**状态**: 执行中

---

## 🚀 第一阶段：基础设施验证

### 前置条件

**安装依赖**:
```bash
pip install chromadb sentence-transformers
```

### 执行步骤

#### 步骤1: 索引黄金数据

```bash
python kms/scripts/vector_indexer_setup.py
```

**预期结果**:
- ✅ ChromaDB客户端创建成功
- ✅ Embedding模型加载成功（首次运行需要下载，约1-2GB）
- ✅ 成功索引3条golden_test_data条目
- ✅ 测试搜索功能正常

**验证点**:
- 检查控制台输出，确认无错误
- 检查 `kms/data/vector_db` 目录是否创建
- 确认索引统计显示3条条目

#### 步骤2: 测试记忆检索

```bash
python kms/scripts/test_memory.py
```

**预期结果**:
- ✅ 数据库连接成功
- ✅ 模型加载成功
- ✅ 4个测试查询都能找到相关法条
- ✅ 相似度距离值合理（越小越好）

**验证点**:
- 查询"食神格遇到七杀怎么办？"应该找到相关条目
- 查询"枭神夺食"应该找到ZPZQ-09-02条目
- 距离值应该在合理范围内（通常 < 1.0）

---

## 🧠 第二阶段：大脑微调（Prompt优化）

### 已完成的优化

✅ **Prompt结构强化**:
- 添加"绝对规则"章节，强调JSON完整性
- 明确Expression Tree必须要有根节点
- 添加简化原则，避免过度嵌套

✅ **Few-Shot示例增强**:
- 每个示例后添加注意事项
- 强调JSON结构完整性
- 明确数组和对象的使用方式

✅ **关键提醒强化**:
- 强调JSON完整性检查
- 明确Expression Tree结构要求
- 添加简化原则

### 测试优化后的Prompt

```bash
# 使用优化后的V2蒸馏器测试
python kms/scripts/llm_distill_example.py
```

**预期改进**:
- JSON格式错误率降低
- Expression Tree结构更完整
- 输出格式更稳定

### 批量处理测试

```bash
# 使用优化后的Prompt处理真实数据
python kms/scripts/batch_processor.py \
  kms/data/raw_texts/zpzq_shishen.txt \
  --book "子平真诠" \
  --topic "食神格"
```

**验证点**:
- JSON解析成功率提高
- Expression Tree结构完整性提升
- 错误率显著降低

---

## 📊 执行检查清单

### 第一阶段检查清单

- [ ] 依赖已安装（chromadb, sentence-transformers）
- [ ] 运行vector_indexer_setup.py
  - [ ] ChromaDB创建成功
  - [ ] 模型加载成功
  - [ ] 3条条目索引成功
  - [ ] 搜索测试通过
- [ ] 运行test_memory.py
  - [ ] 数据库连接成功
  - [ ] 查询结果合理
  - [ ] 距离值正常

### 第二阶段检查清单

- [ ] Prompt优化已应用（semantic_distiller_v2.py）
- [ ] 运行llm_distill_example.py测试
  - [ ] JSON格式错误减少
  - [ ] Expression Tree结构完整
- [ ] 运行batch_processor.py
  - [ ] 成功率提升
  - [ ] 错误率降低

---

## 🔧 故障排除

### 问题1: ChromaDB安装失败

**解决方案**:
```bash
# 使用conda安装（如果pip失败）
conda install -c conda-forge chromadb

# 或使用特定版本
pip install chromadb==0.4.15
```

### 问题2: BGE-M3模型下载慢

**解决方案**:
- 使用国内镜像源
- 或使用较小的模型：`BAAI/bge-base-zh-v1.5`

### 问题3: 显存不足

**解决方案**:
- LLM和Embedding模型串行执行
- 使用CPU模式（较慢但可用）
- 批量处理时先完成LLM生成，再统一索引

### 问题4: JSON格式仍然不完整

**解决方案**:
- 检查Ollama版本（建议使用最新版本）
- 尝试降低temperature（已在代码中设为0.1）
- 添加JSON修复机制（后处理）
- 考虑使用更大的模型（如果可用）

---

## 📝 执行结果记录

### 第一阶段结果

**执行时间**: _______________

**结果**:
- [ ] ✅ 通过
- [ ] ⚠️ 部分通过
- [ ] ❌ 失败

**问题记录**:
_______________________________________________

### 第二阶段结果

**执行时间**: _______________

**结果**:
- [ ] ✅ 通过
- [ ] ⚠️ 部分通过
- [ ] ❌ 失败

**改进效果**:
- JSON错误率: 之前 ___% → 现在 ___%
- Expression Tree完整性: 之前 ___% → 现在 ___%

---

## 🎯 下一步

根据执行结果：

1. **如果第一阶段通过** → 继续第二阶段测试
2. **如果第二阶段通过** → 开始大规模数据处理
3. **如果存在问题** → 根据故障排除指南解决

---

**指南版本**: V1.0  
**最后更新**: 2026-01-03

