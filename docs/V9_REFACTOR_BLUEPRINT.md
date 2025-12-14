# Antigravity V9.0 Refactoring Blueprint
# 《身强身弱判定系统重构蓝图》
# =======================================
# Created: 2025-12-14
# Status: DESIGN PHASE
# Author: Antigravity Team

---

## 0. 重构背景 (Context)

### 当前问题 (Current Issues)

V8.0/V8.1 采用"打补丁"方式修复问题，导致了**"打地鼠效应"**：

| 版本 | 修复目标 | 副作用 |
|------|----------|--------|
| V8.0 | VAL_006 星爷 (夏金身弱) ✅ | VAL_005 塑胶大亨误伤 ❌ |
| V8.1 | S010 辛金建禄 (得令保护) ✅ | 008 Writer Lady 从Strong变Weak ❌ |

### 核心矛盾 (Core Conflicts)

1. **008 Writer Lady Bug**: 分数 81.6 却被判为 Weak
   - 原因: `strength_v7` 在某些条件下覆盖了基础判定
   - 问题: 阈值倒挂

2. **S010 vs VAL_006 冲突**:
   - S010: 辛金生酉月 → 需要得令加成 → Strong
   - VAL_006: 辛金生午月 → 需要焦土阻断 → Weak
   - 两者都是辛金，但月份不同，结果完全相反

3. **Flow Simulation 过于激进**:
   - 控制阶段 (Fire克Metal) 会把能量耗尽
   - 即使加了建禄加成 +150，最后 Metal 也变成负数

---

## 1. 重构目标 (Objectives)

### 1.1 五层解耦架构 (5-Layer Architecture)

**核心理念：天时、地利、人和**

```
┌──────────────────────────────────────────────────────────────────┐
│              Layer 4: Era Context (天时 / 国运)                   │
│              输入: 当前年份 → 输出: 时代加成系数                   │
│   - 离火九运 (2024-2043): 喜火者 +20%, 忌火无解者 -10%            │
│   - 未来: 土运/金运/水运 动态切换                                 │
└────────────────────────────┬─────────────────────────────────────┘
                             │ ×1.0~1.2
┌────────────────────────────▼─────────────────────────────────────┐
│                    Layer 3: Final Judgment                       │
│                    (阈值判定 Thresholding)                        │
│         Input: Adjusted Score → Output: Strong/Weak/Follower     │
│   - 固定阈值: Strong ≥ 80, Moderate ≥ 50, Weak ≥ 20              │
│   - 得令覆盖: 得令必强 (无条件)                                   │
└────────────────────────────┬─────────────────────────────────────┘
                             │
┌────────────────────────────▼─────────────────────────────────────┐
│                 Layer 2: Environmental Modifiers                 │
│                 (环境调候 Climate Adjustment)                     │
│    Input: Base Score + Season → Output: Adjustment Multiplier    │
│    - Scorched Earth (焦土): Summer Metal penalty                 │
│    - Frozen Water (冻水): Winter Wood penalty                    │
│    - Humid Rescue (润局): Water presence cancels scorched        │
└────────────────────────────┬─────────────────────────────────────┘
                             │ ×efficiency
┌────────────────────────────▼─────────────────────────────────────┐
│                  Layer 1: Base Physics Score                     │
│                  (基础物理分 Pure Element Math)                   │
│    Input: Bazi Chart → Output: Raw Score                         │
│    - 得令分 (In-Command Bonus): +150                             │
│    - 印绶分 (Resource Month Bonus): +75                          │
│    - 通根分 (Rooting Bonus): +50 per root                        │
│    - 透干分 (Stem Support): +30 per same-element stem            │
└────────────────────────────┬─────────────────────────────────────┘
                             │ ×geo_modifier
┌────────────────────────────▼─────────────────────────────────────┐
│               Layer 0: Geo Modifier (地利 / 地域性)               │
│               输入: 经纬度 → 输出: 五行基础权重                    │
│   - 北纬 40°+: Water +5%, Fire -5%                               │
│   - 赤道附近: Fire +10%, Water -10%                              │
│   - 沿海地区: Water +3%, Earth -3%                               │
│   - 高原内陆: Earth +5%, Water -5%                               │
└──────────────────────────────────────────────────────────────────┘
```

### 1.2 三才公式 (Heaven-Earth-Human Formula)

```python
# V9.0 核心计算公式
Final_Score = (
    Base_Physics_Score          # 人和 (Layer 1)
    × Geo_Modifier              # 地利 (Layer 0)
    × Environment_Efficiency    # 调候 (Layer 2)
    × Era_Bonus                 # 天时 (Layer 4)
)

Strength = Threshold_Judge(Final_Score, is_in_command, is_resource_month)  # Layer 3
```

### 1.3 三元九运时间表 (Era Calendar)

```python
ERA_CALENDAR = {
    # 下元八运 (Earth)
    (2004, 2023): {'element': 'earth', 'bonus_for': ['earth', 'fire'], 'penalty_for': ['water']},
    
    # 下元九运 (Fire) - CURRENT
    (2024, 2043): {'element': 'fire', 'bonus_for': ['fire', 'wood'], 'penalty_for': ['metal', 'water']},
    
    # 上元一运 (Water)
    (2044, 2063): {'element': 'water', 'bonus_for': ['water', 'metal'], 'penalty_for': ['fire']},
    
    # ... 以此类推
}
```

### 1.4 消除阈值倒挂 (Fix Threshold Inversion)

**问题**: 当前使用 `total_support > total_oppose` 判定，但 Flow Simulation 后的数值无法准确反映"得令"的权威性。

**解决方案**: 使用**固定阈值** + **得令覆盖**：

```python
# 新的判定逻辑
THRESHOLD_STRONG = 80.0
THRESHOLD_WEAK = 40.0
THRESHOLD_FOLLOWER = -20.0

def determine_strength(base_score, is_in_command, is_resource_month):
    # 得令覆盖: 得令必强 (除非极端情况)
    if is_in_command:
        return "Strong"
    
    # 印绶月: 中偏强
    if is_resource_month and base_score > THRESHOLD_WEAK:
        return "Strong"
    
    # 通用判定
    if base_score >= THRESHOLD_STRONG:
        return "Strong"
    elif base_score >= THRESHOLD_WEAK:
        return "Moderate"  # 新增中间态
    elif base_score >= THRESHOLD_FOLLOWER:
        return "Weak"
    else:
        return "Follower"
```

---

## 2. 问题清单 (Bug Registry)

### 2.1 当前失败案例

| Case ID | Description | Expected | Got | Root Cause |
|---------|-------------|----------|-----|------------|
| VAL_002 | 教父 丙火生寅月 | Strong | Weak | 印绶月未正确加分 |
| VAL_004 | 智者 丙火生卯月 | Strong | Weak | 同上 |
| VAL_005 | 塑胶 庚金生未月 | Strong | Weak | 焦土误伤，需润局解救 |
| VAL_007 | 股神 壬水生申月 | Strong | Weak | 该案例需详细分析 |
| VAL_008 | 作家 庚金生戌月 | Strong | Weak (V8.1) | 印绶月+80分却判弱 |
| VAL_014 | 润下格 | Follower | Strong | 从格逻辑缺失 |
| S003 | 寒梅 乙木生丑月 | Weak | Strong | 冬季调候逻辑不足 |
| S005 | 秋水 壬水生申月 | Strong | Weak | 月印应该加分 |
| S006 | 冻日 丙火生子月 | Weak | Strong | 冬水克火未正确计算 |
| S009 | 枯井 癸水生未月 | Weak | Strong | 夏土克水逻辑缺失 |

### 2.2 问题分类

**Category A: 得令/印绶加分不足**
- VAL_002, VAL_004, S005
- 解决: Layer 1 重构

**Category B: 调候逻辑缺失/过度**
- VAL_005 (需润局), S003, S006, S009
- 解决: Layer 2 重构

**Category C: 阈值倒挂**
- VAL_008 (80分判弱)
- 解决: Layer 3 重构

**Category D: 特殊格局**
- VAL_014 (从格)
- 解决: 单独处理从格逻辑

---

## 3. 重构规范 (Refactor Specification)

### 3.1 Layer 1: Base Physics Score

```python
class BasePhysicsEngine:
    """
    纯粹的五行物理计算，不考虑任何调候修正
    """
    
    # === 固定权重常量 (所有数值可调) ===
    WEIGHT_IN_COMMAND = 150.0      # 得令 (月支与日主同属)
    WEIGHT_RESOURCE_MONTH = 75.0   # 印绶月 (月支生日主)
    WEIGHT_ROOT = 50.0             # 每个通根
    WEIGHT_STEM_SUPPORT = 30.0     # 每个同属天干
    WEIGHT_STEM_RESOURCE = 20.0    # 每个印绶天干
    
    # 月令衰旺值 (十二长生)
    MONTH_STRENGTH = {
        '建禄': 1.0,   # 临官
        '帝旺': 1.0,   # 帝旺
        '长生': 0.8,   # 长生
        '沐浴': 0.6,   # 沐浴
        '冠带': 0.7,   # 冠带
        '衰': 0.3,     # 衰
        '病': 0.2,     # 病
        '死': 0.1,     # 死
        '墓': 0.15,    # 墓
        '绝': 0.05,    # 绝
        '胎': 0.2,     # 胎
        '养': 0.3      # 养
    }
    
    def calculate_base_score(self, dm: str, bazi: list) -> dict:
        """
        计算基础分，返回详细分解
        """
        result = {
            'in_command_bonus': 0.0,
            'resource_month_bonus': 0.0,
            'root_bonus': 0.0,
            'stem_support_bonus': 0.0,
            'base_total': 0.0,
            'is_in_command': False,
            'is_resource_month': False
        }
        
        dm_elem = self._get_element(dm)
        month_branch = bazi[1][1]
        mb_elem = self._get_element(month_branch)
        
        # 1. 得令判定
        if mb_elem == dm_elem:
            result['in_command_bonus'] = self.WEIGHT_IN_COMMAND
            result['is_in_command'] = True
        
        # 2. 印绶月判定
        elif self.GENERATION.get(mb_elem) == dm_elem:
            result['resource_month_bonus'] = self.WEIGHT_RESOURCE_MONTH
            result['is_resource_month'] = True
        
        # 3. 通根计算
        for pillar in bazi:
            branch = pillar[1]
            b_elem = self._get_element(branch)
            if b_elem == dm_elem:
                result['root_bonus'] += self.WEIGHT_ROOT
        
        # 4. 天干支援
        for i, pillar in enumerate(bazi):
            if i == 2: continue  # Skip DM itself
            stem = pillar[0]
            s_elem = self._get_element(stem)
            if s_elem == dm_elem:
                result['stem_support_bonus'] += self.WEIGHT_STEM_SUPPORT
            elif self.GENERATION.get(s_elem) == dm_elem:
                result['stem_support_bonus'] += self.WEIGHT_STEM_RESOURCE
        
        # 汇总
        result['base_total'] = (
            result['in_command_bonus'] +
            result['resource_month_bonus'] +
            result['root_bonus'] +
            result['stem_support_bonus']
        )
        
        return result
```

### 3.2 Layer 2: Environmental Modifiers

```python
class EnvironmentEngine:
    """
    调候修正引擎 - 只输出系数，不直接修改分数
    """
    
    SUMMER_BRANCHES = {'巳', '午', '未'}
    WINTER_BRANCHES = {'亥', '子', '丑'}
    WATER_BRANCHES = {'亥', '子', '辰'}  # 润局标志
    
    # 调候系数 (全部可调)
    SCORCHED_EARTH_DAMPING = 0.15   # 焦土不生金
    FROZEN_WATER_DAMPING = 0.30     # 冻水不生木
    HUMID_RESCUE_RESTORE = 0.80     # 润局解救
    
    def calculate_modifiers(self, dm_elem: str, bazi: list) -> dict:
        """
        计算环境修正系数
        """
        month_branch = bazi[1][1]
        branches = [p[1] for p in bazi]
        
        result = {
            'resource_efficiency': 1.0,  # 印星生身效率
            'self_protection': 1.0,      # 日主保护系数
            'applied_rules': []
        }
        
        # 夏季金命 = 焦土不生金
        if month_branch in self.SUMMER_BRANCHES and dm_elem == 'metal':
            # 检查润局
            has_water = any(b in self.WATER_BRANCHES for b in branches)
            
            if has_water:
                # 润局解救
                result['resource_efficiency'] = self.HUMID_RESCUE_RESTORE
                result['applied_rules'].append('润局解救')
            else:
                # 焦土生效
                result['resource_efficiency'] = self.SCORCHED_EARTH_DAMPING
                result['applied_rules'].append('焦土不生金')
        
        # 冬季木命 = 冻水不生木
        if month_branch in self.WINTER_BRANCHES and dm_elem == 'wood':
            # 检查暖局 (有火)
            fire_branches = {'巳', '午'}
            has_fire = any(b in fire_branches for b in branches)
            fire_stems = {'丙', '丁'}
            has_fire_stem = any(p[0] in fire_stems for p in bazi)
            
            if has_fire or has_fire_stem:
                result['resource_efficiency'] = 0.80
                result['applied_rules'].append('暖局解救')
            else:
                result['resource_efficiency'] = self.FROZEN_WATER_DAMPING
                result['applied_rules'].append('冻水不生木')
        
        return result
```

### 3.3 Layer 3: Final Judgment

```python
class StrengthJudgment:
    """
    最终判定引擎 - 固定阈值 + 特殊覆盖
    """
    
    THRESHOLD_VERY_STRONG = 120.0
    THRESHOLD_STRONG = 80.0
    THRESHOLD_MODERATE = 50.0
    THRESHOLD_WEAK = 20.0
    THRESHOLD_FOLLOWER = -10.0
    
    def judge(self, base_result: dict, env_result: dict) -> tuple:
        """
        综合判定
        """
        base = base_result['base_total']
        efficiency = env_result['resource_efficiency']
        
        # 应用调候修正
        adjusted_score = base * efficiency
        
        # === 特殊覆盖规则 ===
        
        # Rule 1: 得令必强
        if base_result['is_in_command']:
            return ("Strong", adjusted_score, "得令覆盖")
        
        # Rule 2: 印绶月+高分 = 强
        if base_result['is_resource_month'] and base > self.THRESHOLD_MODERATE:
            return ("Strong", adjusted_score, "印绶得月")
        
        # === 通用阈值判定 ===
        if adjusted_score >= self.THRESHOLD_STRONG:
            return ("Strong", adjusted_score, "分数达标")
        elif adjusted_score >= self.THRESHOLD_MODERATE:
            return ("Moderate", adjusted_score, "中和")
        elif adjusted_score >= self.THRESHOLD_WEAK:
            return ("Weak", adjusted_score, "偏弱")
        else:
            return ("Very Weak", adjusted_score, "极弱/从格候选")
```

---

## 4. 实施计划 (Implementation Plan) - 5 周

### Phase 1: 核心引擎重构 (Week 1 - Core Rewrite)
- [ ] 创建 `core/engines/base_physics_engine.py` (Layer 1)
- [ ] 创建 `core/engines/environment_engine.py` (Layer 2)
- [ ] 创建 `core/engines/strength_judgment.py` (Layer 3)
- [ ] 建立 `LayeredArchitecture` 骨架接口

### Phase 2: 环境与地域逻辑 (Week 2 - Environment & Geo)
- [ ] 迁移 V8.1 的"燥土/金水"逻辑到 Layer 2
- [ ] **新增：** `core/engines/geo_modifier.py` (Layer 0)
  - 经纬度解析 → 五行偏向系数
  - 初始参数表 (北纬40°+规则等)
- [ ] 添加润局/暖局解救逻辑

### Phase 3: 宏观国运逻辑 (Week 3 - Macro Era)
- [ ] **新增：** `core/engines/era_context.py` (Layer 4)
  - 三元九运时间表
  - 离火九运加成逻辑 (2024-2043)
- [ ] 实现"天时、地利、人和"加权总分公式
- [ ] 添加时代机遇分析输出

### Phase 4: 综合验证 (Week 4 - Integration Test)
- [ ] 使用 25 个现有案例进行回归测试
- [ ] 目标: 80%+ 通过率
- [ ] **新增：** 跨地域测试案例
  - 同一八字，生在哈尔滨 vs 新加坡
- [ ] 调参优化

### Phase 5: 发布与可视化 (Week 5 - Release)
- [ ] 删除 Legacy `_evaluate_wang_shuai` 代码
- [ ] 更新所有文档
- [ ] UI 集成：添加地域/时代输入面板
- [ ] 发布 V9.0 正式版

---

## 5. 成功指标 (Success Criteria)

| 指标 | V8.1 | V9.0 目标 |
|------|------|-----------|
| 原始案例通过率 | 60% | **80%+** |
| 压力测试通过率 | 60% | **75%+** |
| 总通过率 | 60% | **78%+** |
| 阈值倒挂案例 | 有 | **0** |
| 代码可维护性 | 低 | **高** |

---

## 6. 附录：测试案例快速参考

### 必须通过的关键案例

| Priority | Case | Expected | Description |
|----------|------|----------|-------------|
| P0 | VAL_006 | Weak | 星爷 - 焦土不生金 |
| P0 | S010 | Strong | 建禄格 - 得令必强 |
| P0 | VAL_008 | Strong | 印绶月 - 不能80分判弱 |
| P1 | VAL_005 | Strong | 润局解救 |
| P1 | S002 | Weak | 脆金 - 夏土不生金 |
| P1 | S007 | Weak | 热斧 - 午火克金 |

---

**END OF V9.0 REFACTORING BLUEPRINT**
