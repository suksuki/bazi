# 🔬 QuantumLab Trinity 升级指南
## Phase 3.3 - 关键修改点

---

## 📍 需要修改的3个位置

### 1. 全局校准模块 (Line 356)

**Before**:
```python
calc = engine.calculate_energy(c, d_ctx)
```

**After**:
```python
# Build birth chart for Trinity
bazi = c.get('bazi', ['', '', '', ''])
birth_chart_v4 = {
    'year_pillar': bazi[0],
    'month_pillar': bazi[1],
    'day_pillar': bazi[2],
    'hour_pillar': bazi[3],
    'day_master': c.get('day_master', ''),
    'energy_self': estimate_dm_energy(c)  # Based on wang_shuai
}

# Extract favorable/unfavorable
favorable, unfavorable = extract_favorable(c)

# Call Trinity
ctx = engine.calculate_year_context(
    year_pillar=d_ctx['year'],
    favorable_elements=favorable,
    unfavorable_elements=unfavorable,
    birth_chart=birth_chart_v4,
    year=extract_year_number(d_ctx['year'])
)

# Map to old format for compatibility
calc = {
    'career': ctx.career,
    'wealth': ctx.wealth,
    'relationship': ctx.relationship,
    'desc': ctx.description
}
```

### 2. 单点分析模块 (Line 471)

类似修改，但需要添加显示：
- ctx.icon (图标)
- ctx.tags (逻辑标签)
- ctx.narrative_prompt (推理过程)

### 3. 12年模拟模块 (Line 576)

类似修改。

---

## 🎯 增强功能

### 添加 Trinity 可视化

在results中添加：
```python
results.append({
    ...existing fields...,
    # V4.0 Trinity fields
    "Icon": ctx.icon or "",
    "Tags": ", ".join(ctx.tags[:3]),
    "Energy_Level": ctx.energy_level,
    "Risk": ctx.risk_level
})
```

### 添加辅助函数

```python
def estimate_dm_energy(case):
    """Estimate DM energy from wang_shuai"""
    ws = case.get('wang_shuai', '身中和')
    if '强' in ws or '旺' in ws:
        return 5.0
    elif '弱' in ws or '极弱' in ws:
        return 1.5
    return 3.0

def extract_favorable(case):
    """Extract favorable/unfavorable from case"""
    # Simplified logic
    dm = case.get('day_master', '')
    ws = case.get('wang_shuai', '身中和')
    
    from core.quantum_engine import QuantumEngine
    engine_tmp = QuantumEngine()
    dm_elem = engine_tmp._get_element(dm)
    
    all_elems = ['wood', 'fire', 'earth', 'metal', 'water']
    relation_map = {e: engine_tmp._get_relation(dm_elem, e) for e in all_elems}
    
    if '强' in ws or '旺' in ws:
        fav_types = ['output', 'wealth', 'officer']
    else:
        fav_types = ['resource', 'self']
    
    favorable = []
    unfavorable = []
    for e, r in relation_map.items():
        if r in fav_types:
            favorable.append(e.capitalize())
        else:
            unfavorable.append(e.capitalize())
    
    return favorable, unfavorable
```

---

## 📊 建议的UI改进

### 全局校准表格 - 添加Trinity列

| Case | Real | Pred | Delta | **Icon** | **Tags** | **Risk** | RMSE |
|------|------|------|-------|----------|----------|---------|------|
| C1 | 8 | 7.5 | -0.5 | 🗝️ | 机遇,顺利 | opportunity | 1.2 |
| C14 | -5 | -6.2 | -1.2 | ⚠️ | 危机,身弱 | warning | 2.1 |

### 单点分析 - 显示推理过程

```
┌────────────────────────────────────┐
│ AI 判定                             │
├────────────────────────────────────┤
│ 综合评分: -36.0  ⚠️                │
│ 能量等级: Extreme Risk (大凶)      │
│                                    │
│ 逻辑标签:                          │
│ • 危机                             │
│ • 身弱不胜财                       │
│ • 财库冲开                         │
│                                    │
│ 推理过程:                          │
│ 用户八字日主身弱。流年[甲辰]冲开   │
│ Wealth库。请以警示语气...          │
└────────────────────────────────────┘
```

---

**由于文件较大，建议逐步修改测试**
