# Quantum Lab V12.0 升级方案

## 📋 现状分析

### 当前问题
1. **未使用V12.0财富引擎**
   - `quantum_lab.py` 只使用 `GraphNetworkEngine.calculate_wealth_index()`（旧方法）
   - 没有使用 `wealth_engine` 模块
   - 没有使用 F, C, σ 三维向量模型
   - 没有使用 `simulate_life_wealth()` 时间序列模拟器

2. **算法不一致**
   - 旺衰判定：使用 `GraphNetworkEngine.calculate_strength_score()` ✅（已更新）
   - 财富计算：使用旧版 `calculate_wealth_index()` ❌（未更新）
   - 特征加权：可能未应用V12.0的特征加权（is_month_command × 3, clash_count × 2）

3. **功能缺失**
   - 没有0-100岁完整时间序列模拟
   - 没有F, C, σ向量可视化
   - 没有与Ground Truth事件的对比功能

## 🎯 升级目标

### 核心原则
1. **保持向后兼容**：不破坏现有功能
2. **渐进式升级**：分阶段实施
3. **统一算法**：确保所有页面使用相同的V12.0算法

## 📐 升级方案

### Phase 1: Controller层升级
**目标**：在 `QuantumLabController` 中添加V12.0财富引擎支持

**修改内容**：
1. 添加 `calculate_wealth_with_v12()` 方法
   - 使用 `wealth_engine.calculate_wealth_potential()`
   - 返回 F, C, σ 向量和财富势能 W
   
2. 添加 `simulate_wealth_timeline()` 方法
   - 使用 `wealth_engine.simulate_life_wealth()`
   - 返回0-100岁完整时间序列

### Phase 2: View层升级
**目标**：在 `quantum_lab.py` 中添加V12.0财富功能

**修改内容**：
1. 在"单点分析"Tab中添加"V12.0财富分析"子Tab
2. 显示F, C, σ向量数值
3. 显示财富势能 W = F × C × (1 + σ)
4. 可选：添加0-100岁时间序列模拟功能

### Phase 3: 算法一致性验证
**目标**：确保所有页面使用相同的算法

**验证内容**：
1. 特征加权一致性（is_month_command × 3, clash_count × 2, main_root_count × 1.5）
2. 旺衰判定一致性（使用相同的 `calculate_strength_score()`）
3. 财富计算一致性（使用相同的V12.0公式）

## 🔧 实施步骤

### Step 1: 升级Controller
- [ ] 在 `QuantumLabController` 中添加 `calculate_wealth_with_v12()` 方法
- [ ] 在 `QuantumLabController` 中添加 `simulate_wealth_timeline()` 方法
- [ ] 确保使用最新的特征加权

### Step 2: 升级View
- [ ] 在 `quantum_lab.py` 中添加V12.0财富分析功能
- [ ] 添加F, C, σ向量显示
- [ ] 添加财富势能计算和显示

### Step 3: 验证一致性
- [ ] 对比 `quantum_lab.py` 和 `wealth_verification.py` 的计算结果
- [ ] 确保特征加权一致
- [ ] 确保算法版本一致

## 📊 预期效果

升级后：
1. ✅ `quantum_lab.py` 使用V12.0财富引擎
2. ✅ 所有页面使用相同的算法和特征加权
3. ✅ 可以查看F, C, σ向量详细数值
4. ✅ 可以模拟0-100岁完整时间序列
5. ✅ 与Ground Truth事件对比功能

