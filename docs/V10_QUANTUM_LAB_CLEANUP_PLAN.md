# V10.0 量子验证页面清理计划

**日期**: 2025-01-17  
**问题**: 量子验证页面仍有财富、事业、感情等宏观指标，且大运显示缺失

---

## 🚨 问题分析

### 1. 财富、事业、感情等宏观指标仍存在

**位置**: `ui/pages/quantum_lab.py`

**问题代码**:
- **845-869行**: 事业、财富、感情的滑块配置面板（应删除）
- **1359-1365行**: 预测结果包含career、wealth、relationship字段
- **1384-1430行**: 显示宏观相得分对比（事业、财富、情感的MAE计算和显示）
- **1535-1557行**: 显示预测结果中的career、wealth、relationship
- **1628-1792行**: 时间线图表中显示career、wealth、relationship

**设计原则**:
- ❌ **量子验证页面（第一层）**: 只判定旺衰（身强身弱），不涉及财富、事业、感情
- ✅ **财富验证页面（第二层）**: 在 `wealth_verification.py` 中处理财富、事业、感情

### 2. 大运显示缺失问题

**问题**:
- 1155行：`user_luck = c_l.text_input("大运 (Luck)", value=def_luck)` - 如果`def_luck`为空，输入框可能显示为空
- 1266行：从MCP上下文获取大运，但如果MCP上下文也没有，则无法显示

**解决方案**:
1. 优先从MCP上下文获取大运（已有）
2. 如果MCP上下文没有，从案例的timeline获取
3. 如果timeline也没有，使用工具类反向推导：
   - 使用`BaziReverseCalculator`从八字反推出生日期
   - 使用`VirtualBaziProfile`或`BaziProfile`计算大运

### 3. MCP上下文注入完善

**当前状态**:
- ✅ GEO、ERA已通过MCP上下文注入
- ✅ 大运、流年已有注入逻辑，但可能需要增强

**需要改进**:
- 确保大运从MCP上下文正确获取和显示
- 如果缺失，使用反向推导补齐

---

## 🔧 修复方案

### Step 1: 移除所有财富、事业、感情的显示

**需要删除/修改的代码段**:

1. **侧边栏参数面板（845-869行）**: 
   - 删除"W_事业"、"W_财富"、"W_感情"的滑块配置
   - 这些参数应该在`wealth_verification.py`中

2. **预测结果映射（1359-1365行）**:
   - 只保留旺衰相关的字段
   - 移除`career`、`wealth`、`relationship`字段

3. **宏观相得分对比（1384-1430行）**:
   - 完全删除这个section
   - 或者只保留旺衰判定相关的对比

4. **预测结果显示（1535-1557行）**:
   - 移除career、wealth、relationship的显示

5. **时间线图表（1628-1792行）**:
   - 移除career、wealth、relationship的轨迹线

### Step 2: 修复大运显示缺失

**实现逻辑**:
```python
# 1. 优先从MCP上下文获取
luck_pillar = case_with_context.get('luck_pillar')

# 2. 如果MCP上下文没有，从timeline获取
if not luck_pillar:
    timeline = selected_case.get('timeline', [])
    for event in timeline:
        if event.get('dayun'):
            luck_pillar = event['dayun']
            break

# 3. 如果仍然没有，使用反向推导
if not luck_pillar:
    try:
        from core.bazi_reverse_calculator import BaziReverseCalculator
        from core.bazi_profile import BaziProfile
        
        # 从八字反推出生日期
        calculator = BaziReverseCalculator(year_range=(1900, 2100))
        pillars = {
            'year': bazi[0],
            'month': bazi[1],
            'day': bazi[2],
            'hour': bazi[3]
        }
        result = calculator.reverse_calculate(pillars, precision='high')
        
        if result and result.get('birth_date'):
            birth_date = result['birth_date']
            gender_idx = 1 if selected_case.get('gender') == '男' else 0
            profile = BaziProfile(birth_date, gender_idx)
            
            # 计算指定年份的大运
            selected_year = int(user_year) if user_year.isdigit() else 2024
            luck_pillar = profile.get_luck_pillar_at(selected_year)
    except Exception as e:
        logger.warning(f"反向推导大运失败: {e}")
        luck_pillar = "未知"
```

### Step 3: 增强MCP上下文注入

**改进点**:
- 确保大运正确从timeline或计算获取
- 如果缺失，自动使用反向推导补齐
- 在UI上显示大运来源（MCP上下文/反向推导）

---

## 📋 实施检查清单

- [ ] 删除侧边栏的事业、财富、感情参数面板
- [ ] 移除预测结果中的career、wealth、relationship字段
- [ ] 删除宏观相得分对比section
- [ ] 移除预测结果显示中的career、wealth、relationship
- [ ] 从时间线图表中移除career、wealth、relationship轨迹
- [ ] 实现大运反向推导功能
- [ ] 确保大运正确显示（优先MCP上下文，其次timeline，最后反向推导）
- [ ] 在UI上显示大运来源提示
- [ ] 验证只保留旺衰判定相关的功能

---

## 🔍 工具类Review

### 1. BaziReverseCalculator (`core/bazi_reverse_calculator.py`)

**功能**: 从四柱反推出生日期

**主要方法**:
- `reverse_calculate(pillars, precision='high', consider_lichun=True)`: 反推出生日期

**使用场景**: 
- 当案例只有八字，没有出生日期时
- 需要计算大运时

### 2. VirtualBaziProfile (`core/bazi_profile.py`)

**功能**: 从四柱创建虚拟档案，自动反推日期并计算大运

**主要方法**:
- `birth_date`: 返回反推的出生日期
- `get_luck_pillar_at(year)`: 计算指定年份的大运

**使用场景**: 
- 测试用例，已知八字
- 需要快速获取大运

### 3. BaziProfile (`core/bazi_profile.py`)

**功能**: 完整的八字档案，包含大运计算

**主要方法**:
- `get_luck_pillar_at(year)`: O(1)查询指定年份的大运

**使用场景**: 
- 已知出生日期
- 需要精确的大运计算

---

## ✅ 预期结果

修复后，量子验证页面应该：

1. **只显示旺衰判定相关功能**:
   - 旺衰概率波函数可视化
   - 身强/身弱/平衡标签
   - 能量占比和强度分数

2. **大运正确显示**:
   - 优先从MCP上下文获取
   - 其次从timeline获取
   - 最后使用反向推导
   - 显示大运来源提示

3. **完全移除财富、事业、感情**:
   - 侧边栏无相关参数
   - 主界面无相关显示
   - 图表无相关轨迹

---

**下一步**: 开始实施修复

