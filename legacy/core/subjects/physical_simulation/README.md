# 物理模型仿真格局注册表

## 📋 概述

本目录包含所有物理模型仿真主题下的格局定义，按照 RSS-V1.4 规范进行组织。

## 📂 文件结构

```
core/subjects/physical_simulation/
├── README.md              # 本文件
└── registry.json          # 格局注册表（28个格局）
```

## 📊 注册表结构

`registry.json` 包含以下结构：

```json
{
  "metadata": {
    "id": "PATTERN_PHYSICS_REGISTRY",
    "name": "物理模型仿真格局注册表",
    "version": "1.0",
    "total_patterns": 28,
    ...
  },
  "theme": {
    "id": "PATTERN_PHYSICS",
    "name": "物理模型仿真 (Physics Model Simulation)",
    ...
  },
  "patterns": {
    "MOD_101_SGJG_FAILURE": { ... },
    "MOD_104_SGSJ_PLASMA_VAPORIZATION": { ... },
    ...
  }
}
```

## 🔍 使用方式

### Python 加载示例

```python
import json

# 加载注册表
with open('core/subjects/physical_simulation/registry.json', 'r', encoding='utf-8') as f:
    registry = json.load(f)

# 获取所有格局
patterns = registry['patterns']

# 获取特定格局
pattern = patterns.get('MOD_101_SGJG_FAILURE')
```

### 通过 LogicRegistry 加载

```python
from core.logic_registry import LogicRegistry

registry = LogicRegistry()
# LogicRegistry 会自动从新位置加载（如果已更新）
```

## 📝 格局列表

当前注册表包含 **28 个格局**，包括：

- MOD_101_SGJG_FAILURE - 伤官见官栅极击穿模型
- MOD_104_SGSJ_PLASMA_VAPORIZATION - 伤官伤尽等离子气化场模型
- MOD_105_YRJS_FUSION - 羊刃架杀聚变模型
- ... 等 25 个格局

## 🔄 迁移说明

本注册表从 `core/logic_manifest.json` 中提取，按照 RSS-V1.4 规范要求：
- **Step A**: 从 `core/subjects/physical_simulation/registry.json` 调取格局的物理特征向量
- 保持与 `logic_manifest.json` 的兼容性（格局定义仍然保留在主注册表中）

## 📚 相关文档

- [RSS-V1.4 规范文档](../../../docs/QGA_RSS_V1.4_Specification.md)
- [主注册表](../../logic_manifest.json)

