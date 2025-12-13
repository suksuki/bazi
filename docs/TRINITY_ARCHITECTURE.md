# 🏛️ Trinity Architecture - 三位一体统一架构
## Antigravity V3.5+ 系统级升级

---

## 🎯 核心理念

**One Brain, One Heart, One Language**

- **One Brain**: 模型统一 (ConfigManager)
- **One Heart**: 算法统一 (QuantumEngine as Source of Truth)
- **One Language**: 数据协议统一 (DestinyContext)

---

## ✅ Phase 1: 数据协议已完成

### 创建文件: `core/context.py`

**DestinyContext** 类包含：

1. **基础时空信息**
   - year, pillar, luck_pillar

2. **量子状态** (From QuantumEngine)
   - score, energy_level

3. **V3.5 核心特征**
   - is_treasury_open
   - treasury_type, treasury_element
   - day_master_strength

4. **风险评估**
   - risk_level: "opportunity" / "warning" / "danger"
   - risk_factors: List[str]

5. **表现层** (UI/Cinema)
   - icon: 🏆/⚠️/🗝️
   - display_color: #FFD700/#FF6B35
   - tags: ["身强胜财", "财库冲开"]

6. **三维度分数** (Legacy Support)
   - career, wealth, relationship

7. **叙事层** (LLM)
   - narrative_prompt: 自动生成的结构化提示词
   - narrative_events: 事件卡片

**工厂函数**:
```python
create_context_from_v35_result(year, pillar, v35_result, career, wealth, rel)
```

---

## ⏳ 待完成阶段

### Phase 2: 升级 QuantumEngine (生产者)

**目标**: 让 `QuantumEngine` 返回 `DestinyContext` 对象

**新方法**:
```python
def calculate_year_context(
    self, 
    year: int,
    year_pillar: str,
    favorable_elements: List[str],
    unfavorable_elements: List[str],
    birth_chart: Dict
) -> DestinyContext:
    """
    V4.0 统一接口 - 返回完整的 DestinyContext
    """
    # 调用现有的 V3.5 逻辑
    v35_result = self.calculate_year_score(...)
    
    # 计算三维度分数 (差异化逻辑)
    career, wealth, rel = self._calculate_dimensions(v35_result, ...)
    
    # 构造 DestinyContext
    ctx = create_context_from_v35_result(
        year=year,
        pillar=year_pillar,
        v35_result=v35_result,
        career=career,
        wealth=wealth,
        relationship=rel
    )
    
    return ctx
```

---

### Phase 3: 统一三大板块

#### 3.1 智能排盘 (prediction_dashboard.py)

**Current**:
```python
v2_result = engine.calculate_year_score(...)
v2_score = v2_result['score']
v2_details = v2_result['details']
```

**After**:
```python
ctx = engine.calculate_year_context(year, pillar, fav, unfav, chart)
# 直接使用 ctx.career, ctx.wealth, ctx.relationship
# 直接使用 ctx.icon, ctx.display_color
```

#### 3.2 量子验证 (quantum_lab.py)

**Current**:
```python
calc = engine.calculate_energy(c, d_ctx)
```

**After**:
```python
ctx = engine.calculate_year_context(year, pillar, fav, unfav, chart)
# 使用 ctx.career, ctx.wealth, ctx.relationship 进行验证
# Legacy 兼容: calc = {'career': ctx.career, 'wealth': ctx.wealth, ...}
```

#### 3.3 命运影院 (zeitgeist.py)

**Current**:
```python
res = engine.calculate_energy(selected_case, d_ctx)
# 自己分析好坏
```

**After**:
```python
ctx = engine.calculate_year_context(...)
# 直接使用 ctx.narrative_prompt 喂给 LLM
system_prompt = f"""
你是命运解说员。当前年份状态：{ctx.narrative_prompt}
关键标签：{', '.join(ctx.tags)}
风险等级：{ctx.risk_level}
请根据这些严格的逻辑指标生成解说词。
"""
```

---

## 📊 架构对比

### Before (精神分裂)
```
QuantumEngine (V3.5)
  ↓
Dashboard: 有财库图标 🏆
  ↓
User切换到量子验证
  ↓
QuantumLab: 使用 calculate_energy (V2.x)
  ↓
财库效果消失！❌
```

### After (三位一体)
```
QuantumEngine.calculate_year_context()
  ↓ (返回 DestinyContext)
  ├→ Dashboard: ctx.icon, ctx.career, ctx.wealth
  ├→ QuantumLab: ctx.score, ctx.tags for validation
  └→ Cinema: ctx.narrative_prompt for LLM
  
所有模块看到相同的数据 ✅
```

---

## ✅ 当前进度

- [x] Phase 1: 创建 DestinyContext (core/context.py)
- [ ] Phase 2: 升级 QuantumEngine
- [ ] Phase 3.1: 适配 Dashboard
- [ ] Phase 3.2: 适配 QuantumLab
- [ ] Phase 3.3: 适配 Cinema
- [ ] Phase 4: 测试验证

---

## 🚀 下一步

1. **在 QuantumEngine 中添加 `calculate_year_context()` 方法**
2. **逐步迁移三大板块**
3. **保持向后兼容**（现有的 `calculate_year_score` 和 `calculate_energy` 暂时保留）

---

**等待执行指令！** 🎯
