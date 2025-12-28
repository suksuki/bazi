# QGA V25.0 测试状态说明

## 当前测试状态

### ✅ 单元测试（已完成，不连接LLM）

1. **`test_feature_vectorizer.py`**
   - 测试：特征向量提取器
   - LLM连接：❌ 不连接
   - 测试内容：验证五行场强提取、应力张量计算、相位一致性等逻辑

2. **`test_matrix_router_dual_conflict.py`**
   - 测试：矩阵路由器逻辑
   - LLM连接：❌ 不连接（`llm_response=None`）
   - 测试内容：验证权重坍缩计算、能量状态分析等逻辑

### ⚠️ 集成测试（未完成，需要LLM连接）

**完整的端到端测试需要**：
1. 实际调用LLM API
2. 使用真实的八字数据
3. 验证LLM返回的`logic_collapse`和`energy_state_report`
4. 验证完整的`execution_kernel.process_bazi_profile`流程

## 设计说明

当前的架构设计支持两种模式：

### 模式1：自动计算模式（当前测试使用）
- `MatrixRouter`基于特征向量和格局定义自动计算权重和能量状态
- **优点**：快速、可复现、不需要LLM服务
- **缺点**：没有LLM的语义理解

### 模式2：LLM增强模式（生产环境使用）
- LLM根据物理公理和特征向量生成`logic_collapse`和`energy_state_report`
- `MatrixRouter`优先使用LLM结果，如果没有则回退到自动计算
- **优点**：有LLM的语义理解和推理能力
- **缺点**：需要LLM服务，可能有延迟和成本

## 如何创建集成测试

如果需要测试完整的LLM流程，可以：

1. **创建集成测试脚本**：
```python
# tests/test_neural_router_integration.py
from core.subjects.neural_router.execution_kernel import NeuralRouterKernel

kernel = NeuralRouterKernel()
result = kernel.process_bazi_profile(
    active_patterns=[...],
    synthesized_field={...},
    profile_name="测试档案",
    day_master="丙",
    force_vectors={...},
    geo_info="北方/北京"
)

# 验证LLM返回的结果
assert "logic_collapse" in result
assert "energy_state_report" in result
assert "persona" in result
```

2. **前提条件**：
   - LLM服务必须运行（例如：Ollama服务运行在localhost）
   - 配置文件中的LLM模型名称正确
   - 有网络连接（如果使用远程LLM）

## 建议

1. **当前阶段**：单元测试已经足够验证逻辑正确性
2. **生产部署前**：建议添加集成测试，验证完整的LLM流程
3. **开发调试**：可以使用单元测试快速迭代，不依赖LLM服务

