# 🌌 全息格局系统测试指南

## 概述

本文档说明如何运行和编写全息格局（Holographic Pattern）系统的测试。

---

## 🧪 测试结构

```
scripts/
├── run_comprehensive_tests.py          # 全面自动化测试套件
├── smoke_test_registry_loader.py      # RegistryLoader 冒烟测试
└── test_holographic_pattern_a03.py   # A-03 格局专项测试

tests/
└── (未来可添加单元测试)

core/
├── registry_loader.py                 # 注册表加载器（核心）
├── math_engine.py                     # 数学引擎
└── physics_engine.py                  # 物理引擎
```

---

## 🚀 运行测试

### 方式 1: 全面自动化测试（推荐）

```bash
cd /home/jin/bazi_predict
python3 scripts/run_comprehensive_tests.py
```

**测试内容**：
- ✅ RegistryLoader 算法复原测试
- ✅ 核心数学引擎测试
- ✅ 核心物理引擎测试
- ✅ 全息格局控制器测试
- ✅ 注册表完整性测试
- ✅ UI 页面导入测试

### 方式 2: RegistryLoader 冒烟测试

```bash
python3 scripts/smoke_test_registry_loader.py
```

**测试内容**：
- ✅ RegistryLoader 初始化
- ✅ A-03 配置加载
- ✅ 引擎函数可调用性验证
- ✅ 真实八字完整计算
- ✅ 动态事件仿真

### 方式 3: A-03 格局专项测试

```bash
python3 scripts/test_holographic_pattern_a03.py
```

**测试内容**：
- ✅ 五维张量投影计算
- ✅ 样本海选（500例）

---

## 📋 测试覆盖

### 核心模块测试

| 模块 | 测试内容 | 状态 |
|------|---------|------|
| `RegistryLoader` | 配置加载、算法复原、动态仿真 | ✅ |
| `math_engine` | sigmoid_variant、tensor_normalize、calculate_s_balance、calculate_flow_factor | ✅ |
| `physics_engine` | compute_energy_flux、calculate_interaction_damping | ✅ |
| `HolographicPatternController` | 格局获取、层级结构、张量投影 | ✅ |

### 注册表完整性测试

| 检查项 | 说明 | 状态 |
|--------|------|------|
| 文件存在性 | 验证 `registry.json` 存在 | ✅ |
| 基本结构 | 验证 metadata、patterns 字段 | ✅ |
| 格局字段 | 验证必要字段完整性 | ✅ |
| 算法路径 | 验证 algorithm_implementation 路径有效性 | ✅ |

### UI 功能测试

| 功能 | 测试内容 | 状态 |
|------|---------|------|
| 页面导入 | 验证 `holographic_pattern.py` 可正常导入 | ✅ |
| 渲染函数 | 验证 `render()` 函数可调用 | ✅ |

---

## ✍️ 编写新测试

### 测试模板

```python
#!/usr/bin/env python3
"""
测试：[功能名称]
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from core.registry_loader import RegistryLoader

def test_my_feature():
    """测试我的功能"""
    loader = RegistryLoader()
    
    # 测试代码
    result = loader.some_function()
    
    # 断言
    assert result is not None, "结果不应为空"
    
    return True

if __name__ == '__main__':
    print("=" * 70)
    print("测试：[功能名称]")
    print("=" * 70)
    
    try:
        test_my_feature()
        print("✅ 测试通过")
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
```

---

## 📊 测试报告

测试报告会自动保存到：
```
data/test_reports/comprehensive_test_YYYYMMDD_HHMMSS.json
```

**报告内容**：
- 测试时间戳
- 测试统计（总数、通过、失败、通过率）
- 错误详情（如有）

---

## ⚠️ 注意事项

### 依赖要求

运行测试前，确保已安装以下依赖：

```bash
pip install -r requirements.txt
```

### 数据文件

测试需要以下数据文件：
- `core/subjects/holographic_pattern/registry.json` - 全息格局注册表
- `data/geo_coefficients.json` - 地理修正系数（如使用地理功能）

### 环境变量

某些测试可能需要环境变量，请检查 `.env` 文件。

---

## 🔄 持续集成

### 自动化测试流程

1. **代码提交前**：运行 `run_comprehensive_tests.py`
2. **代码审查**：检查测试报告
3. **合并前**：确保所有测试通过

### 测试覆盖率目标

- 核心引擎：100%
- 控制器：> 80%
- UI 页面：> 60%

---

## 📚 相关文档

- [QGA-HR V1.0 注册表规范](./QGA_HR_V1.0_Registry_Specification.md)
- [FDS-V1.1 正向拟合规范](./QGA_FDS_V1.1_Specification.md)
- [注册表对比分析](./QGA_Registry_Comparison_Analysis.md)

---

## 🐛 调试技巧

### 常见问题

1. **导入错误**
   - 检查 `sys.path` 是否正确添加项目根目录
   - 确认模块路径是否正确

2. **注册表加载失败**
   - 检查 `registry.json` 文件是否存在
   - 验证 JSON 格式是否正确

3. **引擎函数调用失败**
   - 检查函数路径是否正确
   - 验证函数签名是否匹配

### 调试命令

```bash
# 详细输出
python3 scripts/run_comprehensive_tests.py -v

# 只运行特定测试
python3 -c "from scripts.run_comprehensive_tests import test_registry_loader; test_registry_loader()"
```

---

**最后更新**: 2025-01-XX
**维护者**: QGA 实验室

