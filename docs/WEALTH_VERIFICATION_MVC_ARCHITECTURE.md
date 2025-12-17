# 💰 财富验证 MVC 架构文档

**版本**: V9.3  
**状态**: ✅ 已完成

---

## 📋 架构概述

财富验证功能已完全按照 **MVC (Model-View-Controller)** 架构实现，确保代码结构清晰、易于维护和扩展。

---

## 🏗️ 架构层次

### 1. Model 层 (`core/models/wealth_case_model.py`)

**职责**: 数据管理

**核心类**:
- `WealthCase`: 案例数据类
- `WealthEvent`: 事件数据类
- `WealthCaseModel`: 数据模型类

**主要方法**:
- `load_all_cases()`: 加载所有案例
- `load_case_by_id(case_id)`: 根据ID加载案例
- `save_case(case)`: 保存案例到文件
- `import_cases_from_json(json_data)`: 从JSON数据导入案例

**数据存储**:
- 位置: `data/*_timeline.json`
- 格式: JSON数组，每个文件包含一个或多个案例

---

### 2. Controller 层 (`controllers/wealth_verification_controller.py`)

**职责**: 业务逻辑协调

**核心类**:
- `WealthVerificationController`: 验证控制器

**主要方法**:
- `get_all_cases()`: 获取所有案例（通过Model）
- `get_case_by_id(case_id)`: 获取单个案例（通过Model）
- `import_cases(json_data)`: 导入案例（通过Model）
- `verify_case(case)`: 验证案例（调用Engine）
- `get_verification_statistics(results)`: 计算统计信息

**依赖**:
- Model: `WealthCaseModel`
- Engine: `GraphNetworkEngine`

---

### 3. View 层 (`ui/pages/wealth_verification.py`)

**职责**: UI展示和用户交互

**核心功能**:
- 案例列表展示
- 案例选择器
- 导入功能（文件上传）
- 验证按钮
- 结果展示（表格、折线图、详细分析）

**MVC原则**:
- ✅ 只通过Controller操作
- ✅ 不直接访问Model或Engine
- ✅ 只负责UI渲染

---

## 🔄 数据流

```
用户操作 (View)
    ↓
调用 Controller 方法
    ↓
Controller 协调 Model 和 Engine
    ├─→ Model: 数据加载/保存
    └─→ Engine: 财富计算
    ↓
返回结果给 View
    ↓
View 展示结果
```

---

## 📁 文件结构

```
bazi_predict/
├── core/
│   └── models/
│       ├── __init__.py
│       └── wealth_case_model.py          # Model层
├── controllers/
│   └── wealth_verification_controller.py  # Controller层
├── ui/
│   └── pages/
│       └── wealth_verification.py        # View层
├── main.py                                # 已添加导航
└── scripts/
    ├── create_jason_timeline.py          # 数据生成脚本
    ├── verify_jason_timeline.py          # 验证脚本
    └── test_wealth_mvc.py                 # MVC测试脚本
```

---

## 🚀 使用方法

### 1. 启动应用

```bash
streamlit run main.py
```

### 2. 访问页面

点击顶部导航栏的 **"💰 财富验证 (Wealth Verification)"**

### 3. 导入案例

**方式一：通过UI上传**
1. 在侧边栏点击"上传JSON格式的案例文件"
2. 选择JSON文件
3. 点击"导入案例"

**方式二：直接创建数据文件**
```bash
python3 scripts/create_jason_timeline.py
```

### 4. 运行验证

1. 选择案例
2. 点击"🚀 开始验证"按钮
3. 查看结果：
   - 统计信息（命中率、平均误差）
   - 结果表格
   - 折线图（真实值 vs 预测值）
   - 详细分析流程

---

## 📝 案例格式

JSON格式示例：

```json
[
  {
    "id": "CASE_001",
    "name": "案例名称",
    "bazi": ["戊午", "癸亥", "壬戌", "丁未"],
    "day_master": "壬",
    "gender": "男",
    "description": "案例描述（可选）",
    "wealth_vaults": ["戌"],
    "timeline": [
      {
        "year": 2010,
        "ganzhi": "庚寅",
        "dayun": "甲子",
        "type": "WEALTH",
        "real_magnitude": 100.0,
        "desc": "财富爆发事件描述"
      }
    ]
  }
]
```

---

## 🧪 测试

运行MVC架构测试：

```bash
python3 scripts/test_wealth_mvc.py
```

测试内容：
- Model层：数据加载
- Controller层：业务逻辑
- 导入功能：数据导入

---

## ✅ 架构优势

1. **职责分离**: 每层职责明确，易于理解
2. **易于测试**: Controller可独立测试
3. **易于维护**: 修改业务逻辑只需改Controller
4. **易于扩展**: 新增功能只需扩展对应层
5. **代码复用**: Model和Controller可在其他地方复用

---

## 📊 功能清单

### ✅ 已完成

- [x] Model层：数据模型和CRUD操作
- [x] Controller层：业务逻辑协调
- [x] View层：UI展示和交互
- [x] 案例导入功能
- [x] 验证功能
- [x] 结果展示（表格、折线图、详细分析）
- [x] 统计信息计算
- [x] 导航集成

### 🔄 待完成

- [ ] 批量验证功能
- [ ] 导出验证报告
- [ ] 参数调优建议
- [ ] 案例对比功能

---

## 🎯 下一步

等待用户提供 **5个Jason格式的案例**，然后：

1. 通过UI导入案例
2. 运行验证
3. 分析结果
4. 根据结果调优算法

---

**文档更新时间**: 2024  
**维护者**: Quantum Bazi GEM Team

