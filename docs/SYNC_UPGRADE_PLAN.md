# 🔄 Antigravity 算法同步升级计划
## 统一三大板块到 V3.5

---

## 📊 当前状态诊断

### 三大板块算法使用情况

| 板块 | 文件 | 使用方法 | 版本 | V3.5支持 |
|-----|------|---------|------|----------|
| **智能排盘** | `prediction_dashboard.py` | `calculate_year_score` | V3.5 | ✅ 完整支持 |
| **量子验证** | `quantum_lab.py` | `calculate_energy` | V2.x | ❌ 缺失财库 |
| **命运影院** | `zeitgeist.py` | `calculate_energy` | V2.x | ❌ 缺失财库 |

### ❌ 核心问题

**`calculate_energy` 是 V2.x 方法，不包含**：
1. 财库开启检测 (V3.0)
2. 财库倍数加成 (V3.0)
3. 身强身弱安全阀 (V3.5)
4. 图标返回 (🏆/⚠️/🗝️)

**结果**：
- 用户在智能排盘看到 🏆 财库大开
- 切换到量子验证/影院 → **财库效果消失！**
- 体验不一致，用户困惑

---

## 🎯 升级目标

**统一三大板块到 V3.5**：
- 所有板块使用相同的核心算法
- 财库检测全覆盖
- 身强身弱判定统一
- 用户体验一致

---

## 🛠️ 升级方案 A (推荐)

### 核心思路

**不再使用 `calculate_energy`，统一使用 `calculate_year_score`**

理由：
1. `calculate_year_score` 是完整版，包含所有 V3.5 特性
2. `calculate_energy` 功能是 `calculate_year_score` 的子集
3. 向前兼容，未来所有新功能都在 `calculate_year_score` 中

### 实施步骤

#### Step 1: 升级 Quantum Lab (量子验证)

**文件**: `ui/pages/quantum_lab.py`

**需要修改的地方**：
1. Line 356: 全局校准模块
2. Line 471: 单点分析模块  
3. Line 576: 12年模拟模块

**改动内容**：
```python
# Before (V2.x)
calc = engine.calculate_energy(c, d_ctx)
# Returns: {'career': X, 'wealth': Y, 'relationship': Z, 'desc': '...'}

# After (V3.5)
# 需要构造 birth_chart 和 favorable/unfavorable
birth_chart_v3 = _build_birth_chart(c)
favorable, unfavorable = _extract_favorable_elements(c)
result = engine.calculate_year_score(
    year_pillar=d_ctx['year'],
    favorable_elements=favorable,
    unfavorable_elements=unfavorable,
    birth_chart=birth_chart_v3
)
# Returns: {'score': X, 'details': [...], 'treasury_icon': '🏆', 'treasury_risk': 'opportunity'}

# Need to map V3.5 result back to V2.x format for compatibility
calc = {
    'career': result['score'],  # Or dimension-specific logic
    'wealth': result['score'],
    'relationship': result['score'],
    'desc': '; '.join(result['details']),
    'treasury_icon': result.get('treasury_icon'),  # New field
    'treasury_risk': result.get('treasury_risk')   # New field
}
```

**挑战**：
- `calculate_energy` 返回三维度分数
- `calculate_year_score` 返回总分 + details
- 需要映射逻辑

**解决方案**：
使用 Dashboard 的差异化算法：
```python
base_score = result['score']
# Apply dimension-specific weights
calc = {
    'career': base_score * 0.8 + treasury_bonus_career,
    'wealth': base_score * 1.0 + treasury_bonus_wealth,
    'relationship': base_score * 0.4
}
```

---

#### Step 2: 升级 Zeitgeist (命运影院)

**文件**: `ui/pages/zeitgeist.py`

**需要修改的地方**：
1. Line 96: 主要计算逻辑

**改动类似 Quantum Lab**

---

### Step 3: 辅助函数

创建通用转换函数：

```python
# utils/v3_adapter.py

def build_birth_chart_from_case(case_data):
    """从 calibration_cases 格式转换为 V3.5 birth_chart"""
    bazi = case_data.get('bazi', ['', '', '', ''])
    return {
        'year_pillar': bazi[0],
        'month_pillar': bazi[1],
        'day_pillar': bazi[2],
        'hour_pillar': bazi[3],
        'day_master': case_data.get('day_master', ''),
        'energy_self': estimate_dm_energy(case_data)  # From wang_shuai
    }

def extract_favorable_elements(case_data):
    """从 case 中提取喜忌神"""
    # Logic based on wang_shuai and day_master
    dm = case_data.get('day_master')
    ws = case_data.get('wang_shuai', '身中和')
    
    # Simplified logic
    if ws == '身弱':
        return ['Metal', 'Water'], ['Fire', 'Earth', 'Wood']  # Example
    # ... more logic
    
    return [], []

def map_v3_to_v2_format(v3_result, dimension_weights=None):
    """将 V3.5 结果映射回 V2.x 格式"""
    base = v3_result['score']
    
    if not dimension_weights:
        dimension_weights = {'career': 0.8, 'wealth': 1.0, 'relationship': 0.4}
    
    return {
        'career': base * dimension_weights['career'],
        'wealth': base * dimension_weights['wealth'],
        'relationship': base * dimension_weights['relationship'],
        'desc': '; '.join(v3_result.get('details', [])),
        'treasury_icon': v3_result.get('treasury_icon'),
        'narrative_events': []  # Can be enhanced later
    }
```

---

## 📅 实施时间线

| 阶段 | 任务 | 预计时间 |
|-----|------|---------|
| **Phase 1** | 创建转换工具函数 | 30min |
| **Phase 2** | 升级 Quantum Lab | 45min |
| **Phase 3** | 升级 Zeitgeist | 30min |
| **Phase 4** | 测试验证 | 30min |
| **总计** | | ~2.5小时 |

---

## ⚠️ 风险与挑战

### 风险1: 三维度分数消失

**问题**: `calculate_year_score` 只返回总分，不返回三维度

**解决**: 
- 在 Dashboard 中已有差异化逻辑
- 复用到 Quantum Lab

### 风险2: Narrative Events 不匹配

**问题**: Quantum Lab 依赖 `narrative_events` 字段

**解决**:
- 从 `details` 列表构造简化版 narrative
- 或保留 `calculate_energy` 的 narrative 生成


---

## ✅ 验收标准

升级成功的标志：

1. ✅ Quantum Lab 全局校准能检测财库影响
2. ✅ Quantum Lab 单点分析显示财库图标
3. ✅ Zeitgeist 时间轴显示财库特效
4. ✅ 三大板块对同一案例给出一致的分数（误差<10%）
5. ✅ 所有现有功能正常运行

---

## 🚀 执行确认

**请确认是否立即开始 Phase 1**：
- 创建 `utils/v3_adapter.py` 转换工具
- 开始升级 Quantum Lab

预计完成时间: 2.5小时

---

**等待您的指示！** 🎯
