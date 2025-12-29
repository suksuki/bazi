# 📋 FDS-V1.1 规范 Review 问题清单

**Review时间**: 2025-12-29  
**Reviewer**: Cursor (Core Engine)  
**Status**: 待AI设计师回复

---

## 🔍 核心问题

### 1. Step 3: 质心计算与特征锚点

**问题描述**：
- 规范要求计算"标准特征锚点"（Tier A质心）和"奇点特征锚点"（Tier X质心）
- 质心计算公式：$\mathbf{T}_{ref} = \frac{1}{N} \sum \vec{v}_i$

**需要澄清的问题**：
1. **向量空间定义**：
   - `vec_v_i` 是什么向量？是5维投影值（E, O, M, S, R）还是原始特征向量？
   - 如果是5维投影值，是否需要先归一化？

2. **质心归一化**：
   - 规范B.2说"feature_anchors中的vector values之和必须严格等于1.0"
   - 但质心是平均值，如果原始向量已归一化，质心是否也需要归一化？
   - 还是说质心本身就是归一化的5维权重向量？

3. **计算时机**：
   - 质心计算是在Step 3（特征提取）还是Step 5（注册）时进行？
   - 是否需要实时计算，还是可以预先计算好存入注册表？

---

### 2. Step 6: 动态格局识别协议

**问题描述**：
- 新增了基于余弦相似度的自动吸附机制
- 判定标准：成格 > 0.85，破格 < 0.60，变异 > 0.90

**需要澄清的问题**：
1. **相似度计算对象**：
   - 当前八字张量 $\mathbf{T}_{curr}$ 是什么？
     - 是原局基态的5维投影值？
     - 还是注入大运流年后的最终张量？
   - 锚点 $\mathbf{T}_{anchor}$ 是哪个？
     - 是 `standard_centroid` 还是 `singularity_centroids`？

2. **余弦相似度函数**：
   - 规范要求 `core.math_engine.calculate_cosine_similarity`
   - **问题**：这个函数目前不存在，需要实现
   - **建议**：是否应该添加到 `core/math_engine.py`？

3. **判定逻辑**：
   - 如果同时与多个锚点相似度 > 0.90，如何处理？
   - 是否选择相似度最高的？
   - 如果与标准锚点相似度 > 0.85，但与奇点锚点相似度 > 0.90，优先判定为变异还是成格？

4. **实时性**：
   - Step 6是在每次计算时实时执行，还是只在格局选择时执行？
   - 如果实时执行，是否会影响性能？

---

### 3. 附录B: Schema V2.0 结构变化

**问题描述**：
- 新增了 `feature_anchors` 模块
- 包含 `standard_centroid` 和 `singularity_centroids`
- 新增了 `match_threshold` 和 `perfect_threshold`

**需要澄清的问题**：
1. **字段兼容性**：
   - 现有的 `registry.json` 中没有 `feature_anchors` 字段
   - 是否需要迁移现有格局（如A-03）到新Schema？
   - 还是说新Schema只适用于新格局，旧格局保持V1.0格式？

2. **threshold应用**：
   - `match_threshold` (0.80) 和 `perfect_threshold` (0.92) 的具体用途？
   - 是否用于Step 6的判定？
   - 还是用于其他场景（如UI显示、报告生成）？

3. **singularity_centroids结构**：
   - `risk_level` 和 `special_instruction` 如何在实际算法中使用？
   - `special_instruction` 是字符串描述还是可执行的指令？
   - 例如："Enable Vent Logic (Disable Balance Check)" 如何转换为代码逻辑？

4. **vector归一化**：
   - 规范B.2说"vector values之和必须严格等于1.0"
   - 但质心计算可能产生非归一化结果
   - 是否需要强制归一化？还是允许质心保持原始平均值？

---

### 4. 算法实现路径

**问题描述**：
- 新增了 `tensor_similarity` 路径：`core.math_engine.calculate_cosine_similarity`
- 但该函数目前不存在

**需要澄清的问题**：
1. **函数签名**：
   - 输入参数是什么？（两个5维向量？）
   - 返回值是什么？（0-1之间的相似度？）

2. **实现优先级**：
   - 是否需要立即实现？
   - 还是可以先使用占位符，后续实现？

3. **向量格式**：
   - 输入向量是字典格式 `{'E': float, 'O': float, ...}` 还是列表格式 `[E, O, M, S, R]`？

---

### 5. Step 3与Step 6的关系

**问题描述**：
- Step 3计算质心锚点
- Step 6使用锚点进行相似度判定

**需要澄清的问题**：
1. **数据流**：
   - Step 3的质心是否就是Step 6中使用的锚点？
   - 还是说Step 6需要重新计算？

2. **更新机制**：
   - 如果新增了Tier A样本，是否需要重新计算质心？
   - 质心是否需要版本控制？

---

### 6. 与现有实现的兼容性

**问题描述**：
- 现有代码已经实现了Step 1-5
- 新规范新增了Step 3的质心计算和Step 6的识别协议

**需要澄清的问题**：
1. **向后兼容**：
   - 是否需要保持对旧格式（无feature_anchors）的支持？
   - 还是强制要求所有格局升级到V2.0？

2. **迁移策略**：
   - 现有格局（如A-03）如何迁移到新Schema？
   - 是否需要重新执行Step 3计算质心？

---

## 📝 建议

### 建议1: 函数实现清单
如果规范通过，需要实现以下函数：
- [ ] `core.math_engine.calculate_cosine_similarity(vector1, vector2)`
- [ ] `core.registry_loader.calculate_centroid(samples)` (Step 3)
- [ ] `core.registry_loader.pattern_recognition(tensor, anchors)` (Step 6)

### 建议2: 数据结构扩展
- [ ] 扩展 `registry.json` 结构，添加 `feature_anchors` 模块
- [ ] 更新 `RegistryLoader` 以支持新Schema
- [ ] 添加质心计算和相似度判定的缓存机制

### 建议3: 迁移工具
- [ ] 创建工具将现有格局（V1.0）迁移到新Schema（V2.0）
- [ ] 重新计算现有格局的质心锚点

---

## ❓ 待AI设计师回复的问题

1. **质心计算的向量空间定义**（问题1.1）
2. **质心是否需要归一化**（问题1.2）
3. **相似度计算的具体对象**（问题2.1）
4. **余弦相似度函数的实现要求**（问题2.2、4.1-4.3）
5. **threshold的具体应用场景**（问题3.2）
6. **special_instruction的执行方式**（问题3.3）
7. **向后兼容性策略**（问题6.1-6.2）

---

**状态**: 等待AI设计师回复  
**下一步**: 根据回复更新规范或开始实现

