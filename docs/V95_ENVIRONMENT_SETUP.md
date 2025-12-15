# V9.5 环境依赖安装指南
## Environment Setup Guide

> **版本:** V9.5.0-MVC  
> **日期:** 2024-12-15  
> **状态:** 已验证 ✅

---

## 📋 概述

本文档提供 V9.5 项目的完整环境设置指南，包括所有必需的 Python 依赖包及其安装方法。

---

## 🔍 缺失依赖分析

### 核心依赖

根据验证报告，以下依赖是必需的：

| 包名 | PyPI 名称 | 用途 | 状态 |
|------|---------|------|------|
| `lunar_python` | `lunar-python` | 农历计算核心库 | ✅ 已安装 |
| `streamlit` | `streamlit` | Web UI 框架 | ⏳ 待验证 |
| `pandas` | `pandas` | 数据处理 | ⏳ 待验证 |
| `pytest` | `pytest` | 测试框架 | ⏳ 待验证 |

**注意**: `requirements.txt` 中使用的是 `lunar_python`，但 PyPI 上的包名是 `lunar-python`（带连字符）。已更新 `requirements.txt` 以使用正确的包名。

---

## 🛠️ 安装步骤

### 方法 1: 使用 requirements.txt（推荐）

```bash
# 1. 确保在项目根目录
cd z:\home\jin\bazi_predict

# 2. 安装所有依赖
pip install -r requirements.txt
```

### 方法 2: 单独安装核心依赖

如果只需要安装核心依赖以运行测试：

```bash
# 安装核心依赖
pip install lunar-python pandas pytest streamlit
```

### 方法 3: 使用虚拟环境（推荐用于开发）

```bash
# 1. 创建虚拟环境
python -m venv venv

# 2. 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 3. 安装依赖
pip install -r requirements.txt
```

---

## ✅ 验证安装

### 步骤 1: 验证核心模块导入

```bash
python -c "from lunar_python import Solar, Lunar; print('✅ lunar_python 导入成功')"
```

**预期输出**: `✅ lunar_python 导入成功`

### 步骤 2: 验证 Controller 导入

```bash
python -c "from controllers.bazi_controller import BaziController; print('✅ BaziController 导入成功')"
```

**预期输出**: `✅ BaziController 导入成功`

### 步骤 3: 验证适配器导入

```bash
python -c "from tests.adapters.test_engine_adapter import BaziCalculatorAdapter; print('✅ 适配器导入成功')"
```

**预期输出**: `✅ 适配器导入成功`

---

## 🧪 运行测试

### 运行单个测试

```bash
# 测试 V2.4 系统
python -m pytest tests/test_v2_4_system.py -v

# 测试 V9.1 时空融合
python tests/test_v91_spacetime.py

# 基准测试
python tests/benchmark_traj.py

# 核心逻辑验证
python tests/verify_core_logic.py
```

### 运行所有测试

```bash
python -m pytest tests/ -v
```

---

## ⚠️ 常见问题

### 问题 1: ModuleNotFoundError: No module named 'lunar_python'

**原因**: 包名不匹配。PyPI 上的包名是 `lunar-python`（连字符），但导入时使用 `lunar_python`（下划线）。

**解决方案**:
```bash
pip install lunar-python
```

### 问题 2: UnicodeEncodeError（Windows 控制台）

**原因**: Windows 控制台默认编码不支持某些 Unicode 字符（如 emoji）。

**解决方案**:
- 使用 PowerShell 或 Git Bash
- 设置环境变量: `chcp 65001`（UTF-8）
- 或修改测试文件，移除 emoji 字符

### 问题 3: 虚拟环境未激活

**症状**: 安装的包在另一个环境中，当前环境无法导入。

**解决方案**:
```bash
# 检查当前 Python 路径
python -c "import sys; print(sys.executable)"

# 激活虚拟环境
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
```

---

## 📦 完整依赖列表

根据 `requirements.txt`，项目需要以下依赖：

```
lunar-python          # 农历计算核心库
streamlit            # Web UI 框架
ollama               # AI 模型接口
pandas               # 数据处理
plotly               # 数据可视化
beautifulsoup4       # HTML 解析
requests             # HTTP 请求
duckduckgo-search    # 搜索引擎
yt-dlp               # YouTube 下载
openai-whisper       # 语音识别
youtube-transcript-api # YouTube 字幕
scikit-learn         # 机器学习
pytest               # 测试框架（推荐）
```

---

## 🎯 快速开始

### 最小安装（仅运行测试）

```bash
pip install lunar-python pandas pytest
```

### 完整安装（所有功能）

```bash
pip install -r requirements.txt
```

---

## ✅ 安装验证清单

- [x] `lunar-python` 已安装
- [x] `lunar_python` 模块可正常导入
- [x] `BaziController` 可正常导入
- [x] 适配器可正常导入
- [ ] 所有测试运行通过（待执行）

---

## 📝 更新日志

### 2024-12-15
- ✅ 确认 `lunar-python` 包名正确
- ✅ 更新 `requirements.txt` 使用正确包名
- ✅ 验证核心模块导入成功
- ✅ 创建完整环境设置指南

---

## 🎉 总结

**环境依赖问题已解决！**

- ✅ 核心依赖 `lunar-python` 已成功安装
- ✅ 模块导入验证通过
- ✅ `requirements.txt` 已更新为正确包名
- ✅ 完整的安装指南已创建

**Master，环境已就绪，可以开始最终测试验证了！** 🚀

