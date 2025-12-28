# LLM神经网络路由专题 (LLM Neural Router Subject)

## 专题信息

- **专题ID**: `LLM_Neural_Router`
- **专题名称**: 大模型神经路由
- **专题类型**: TOPIC
- **版本**: 25.0
- **描述**: 中央处理中枢 (Central Processing Kernel)，负责将八字物理指纹投射到LLM的逻辑潜空间，实现格局智能路由

## 快速开始

```python
from core.subjects.neural_router import NeuralRouterKernel

# 创建执行内核
kernel = NeuralRouterKernel()

# 处理八字档案
result = kernel.process_bazi_profile(
    active_patterns=active_patterns,
    synthesized_field=synthesized_field,
    profile_name="测试档案",
    day_master="丁",
    force_vectors={"fire": 10.0, "water": -5.0}
)
```

## 与QGA逻辑注册表的集成

本专题已通过独立的`registry.json`进行注册。如需将其集成到QGA的`logic_manifest.json`中，可参考以下格式：

```json
{
  "MOD_LLM_Neural_Router": {
    "id": "MOD_LLM_Neural_Router",
    "name": "🧠 大模型神经路由 (LLM Neural Router)",
    "icon": "🧠",
    "type": "TOPIC",
    "layer": "TOPIC",
    "description": "[QGA V25.0] 中央处理中枢，负责将八字物理指纹投射到LLM的逻辑潜空间，实现格局智能路由",
    "active": true,
    "entry_point": {
      "module": "core.subjects.neural_router.execution_kernel",
      "class": "NeuralRouterKernel",
      "method": "process_bazi_profile"
    }
  }
}
```

## 文件说明

- `registry.json` - 专题注册表（路由参数、物理模型、格局定义）
- `registry.py` - 注册表管理类
- `execution_kernel.py` - 执行内核（处理八字档案的主入口）

## 相关文档

- `docs/QGA_V25.0_Neural_Router_Subject.md` - 专题详细文档

