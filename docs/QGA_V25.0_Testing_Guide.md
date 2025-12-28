# QGA V25.0 测试指南

## 测试分类

### 1. 单元测试（不连接LLM）

**目的**：快速验证逻辑正确性，不依赖外部服务

**测试文件**：
- `tests/test_feature_vectorizer.py` - 测试特征向量提取器
- `tests/test_matrix_router_dual_conflict.py` - 测试矩阵路由器逻辑

**特点**：
- ✅ 运行快速
- ✅ 可复现
- ✅ 不依赖LLM服务
- ❌ 不测试LLM的实际响应

**运行方式**：
```bash
python3 tests/test_feature_vectorizer.py
python3 tests/test_matrix_router_dual_conflict.py
```

### 2. 集成测试（连接LLM）

**目的**：验证完整的端到端流程，包括LLM调用

**测试文件**：
- `tests/test_neural_router_integration.py` - 测试完整的神经网络路由流程

**特点**：
- ✅ 测试完整流程
- ✅ 验证LLM实际响应
- ❌ 需要LLM服务运行
- ❌ 可能有延迟和成本

**前提条件**：
1. LLM服务必须运行（例如：Ollama运行在localhost）
2. 配置文件中的LLM模型名称正确
3. 有网络连接（如果使用远程LLM）

**运行方式**：
```bash
# 会提示确认，因为需要LLM服务
python3 tests/test_neural_router_integration.py
```

## 测试架构说明

### 当前设计（Phase 4）

系统支持两种模式：

#### 模式1：自动计算模式（单元测试使用）
- `MatrixRouter`基于特征向量和格局定义自动计算
- 不调用LLM
- 用于快速验证逻辑

#### 模式2：LLM增强模式（集成测试/生产环境）
- LLM根据物理公理和特征向量生成结果
- `MatrixRouter`优先使用LLM结果
- 如果没有LLM结果，回退到自动计算

### 执行流程

```
execution_kernel.process_bazi_profile()
  ├─ FeatureVectorizer.vectorize_bazi()  # Phase 2: 特征向量提取
  ├─ PromptGenerator.generate_inline_prompt()  # Phase 3: 生成Prompt
  ├─ LLMSemanticSynthesizer.synthesize_persona()  # 调用LLM（如果配置）
  ├─ MatrixRouter.process_matrix_routing()  # Phase 4: 矩阵路由
  │   ├─ compute_weight_collapse()  # 权重坍缩
  │   └─ analyze_energy_state()  # 能量状态分析
  └─ 返回完整结果
```

## 测试建议

### 开发阶段
- 使用单元测试快速迭代
- 不依赖LLM服务，开发效率高

### 集成阶段
- 使用集成测试验证完整流程
- 确保LLM响应格式正确
- 验证权重坍缩和能量状态报告

### 生产部署前
- 运行所有单元测试
- 运行集成测试（如果可能）
- 进行端到端的真实案例测试

## 常见问题

### Q: 为什么单元测试不连接LLM？
A: 为了快速开发和验证逻辑，不依赖外部服务。如果需要测试LLM，使用集成测试。

### Q: 如何判断测试是否调用了LLM？
A: 检查测试代码：
- 如果调用`MatrixRouter.process_matrix_routing(llm_response=None)`，没有调用LLM
- 如果调用`execution_kernel.process_bazi_profile()`，会尝试调用LLM（如果配置了）

### Q: LLM调用失败怎么办？
A: 系统设计了回退机制：
- 如果LLM调用失败，`MatrixRouter`会使用自动计算
- 测试仍然可以通过，但不会包含LLM的语义理解

