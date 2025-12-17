# V9.3 测试指南

## 概述

本文档说明如何运行和编写 V9.3 MCP 改进功能的测试。

---

## 🧪 测试结构

```
tests/
├── test_mcp_v93.py                    # MCP V9.3 功能测试
├── test_wealth_verification_v93.py    # 财富验证 V9.3 测试
└── ...
```

---

## 🚀 运行测试

### 方式 1: 使用 pytest（推荐）

```bash
# 运行所有 MCP 测试
pytest tests/test_mcp_v93.py -v

# 运行财富验证测试
pytest tests/test_wealth_verification_v93.py -v

# 运行所有测试并显示覆盖率
pytest tests/ --cov=core --cov=controllers --cov-report=html
```

### 方式 2: 使用 unittest

```bash
# 运行 MCP 测试
python3 tests/test_mcp_v93.py

# 运行财富验证测试
python3 tests/test_wealth_verification_v93.py
```

### 方式 3: 使用全检自动化脚本

```bash
# 运行完整测试套件
python3 scripts/run_full_check_v93.py
```

---

## 📋 测试覆盖

### MCP V9.3 功能测试

| 测试类 | 测试内容 |
|--------|---------|
| `TestMCPGeoCorrection` | 地理修正功能 |
| `TestMCPHourlyContext` | 流时修正功能 |
| `TestMCPEraContext` | 宏观场（时代修正）功能 |
| `TestMCPPatternUncertainty` | 模型不确定性功能 |
| `TestMCPUserFeedback` | 交互上下文（用户反馈）功能 |
| `TestMCPIntegration` | MCP 集成功能 |

### 财富验证 V9.3 测试

| 测试类 | 测试内容 |
|--------|---------|
| `TestWealthVerificationV93` | 财富验证改进功能 |
| - `test_vault_opening_with_combination` | 合开财库测试 |
| - `test_clash_commander_priority` | 冲提纲优先判断 |
| - `test_weak_wealth_reversal` | 身弱财重反转 |
| - `test_verification_statistics` | 验证统计功能 |

---

## ✍️ 编写新测试

### 测试模板

```python
import unittest
from core.processors.geo import GeoProcessor

class TestMyFeature(unittest.TestCase):
    """测试我的功能"""
    
    def setUp(self):
        """测试前准备"""
        self.processor = GeoProcessor()
    
    def test_basic_functionality(self):
        """测试基本功能"""
        result = self.processor.process("Beijing")
        self.assertIsInstance(result, dict)
        self.assertIn('wood', result)
        print("✅ 基本功能测试通过")
    
    def tearDown(self):
        """测试后清理"""
        pass
```

### 测试最佳实践

1. **命名规范**
   - 测试类: `Test<FeatureName>`
   - 测试方法: `test_<functionality>`

2. **断言使用**
   - 使用 `self.assert*` 方法
   - 提供清晰的错误消息

3. **输出信息**
   - 使用 `print()` 输出测试进度
   - 使用 `✅` 和 `❌` 标记结果

4. **异常处理**
   - 测试异常情况
   - 使用 `self.assertRaises()`

---

## 🔍 调试测试

### 运行单个测试

```bash
# 运行特定测试类
pytest tests/test_mcp_v93.py::TestMCPGeoCorrection -v

# 运行特定测试方法
pytest tests/test_mcp_v93.py::TestMCPGeoCorrection::test_geo_processor_initialization -v
```

### 查看详细输出

```bash
# 显示 print 输出
pytest tests/test_mcp_v93.py -v -s

# 显示详细错误信息
pytest tests/test_mcp_v93.py -v --tb=long
```

---

## 📊 测试报告

### 生成 HTML 报告

```bash
pytest tests/ --cov=core --cov=controllers --cov-report=html
# 报告保存在 htmlcov/index.html
```

### 生成 JSON 报告

```bash
python3 scripts/run_full_check_v93.py
# 报告保存在 test_report_v93.json
```

---

## ⚠️ 常见问题

### 1. 测试失败：模块未找到

**问题**: `ModuleNotFoundError: No module named 'core'`

**解决**: 确保在项目根目录运行测试

```bash
cd /home/jin/bazi_predict
python3 tests/test_mcp_v93.py
```

### 2. 测试失败：数据文件未找到

**问题**: `FileNotFoundError: geo_coefficients.json`

**解决**: 检查数据文件是否存在

```bash
ls data/geo_coefficients.json
```

### 3. 测试失败：依赖未安装

**问题**: `ImportError: No module named 'pytest'`

**解决**: 安装依赖

```bash
pip install pytest pytest-cov
```

---

## 📝 测试检查清单

在提交代码前，确保：

- [ ] 所有新功能都有测试覆盖
- [ ] 测试通过（`pytest` 返回 0）
- [ ] 测试覆盖率 > 80%
- [ ] 测试文档已更新
- [ ] 测试报告已生成

---

**最后更新**: 2025-01-XX  
**版本**: V9.3 Testing Guide

