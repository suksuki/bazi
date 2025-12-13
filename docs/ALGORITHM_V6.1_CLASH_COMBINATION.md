# 🧪 Antigravity V6.1 - 核心算法二级补充文档
## Clashes (冲) 与 Combinations (合化) 理论模型

> **Status**: 📋 待实现 (Pending Implementation)  
> **Target Version**: V6.1  
> **Created**: 2024-12-14  
> **Author**: Jin & Antigravity

---

## 1. 冲 (Clashes) 的本质与模型

### 1.1 理论定义
**冲** 不仅仅是"克"，而是 **"对立能量的湮灭与激荡"** (Energy Annihilation & Excitation)。

当两个地支处于对冲位置时，它们的能量场发生剧烈碰撞，导致：
- **湮灭效应**: 双方能量相互抵消，形成能量真空
- **激荡效应**: 碰撞产生冲击波，影响周围的能量场

### 1.2 分类建模

#### 1.2.1 四库冲 (Earth Clash) - 辰戌 / 丑未
- **本质**: "开锁" (Vault Unlock)
- **物理特征**: 能量释放，储存的势能转化为动能
- **已实现**: `TreasuryEngine` 中的 `process_treasury_scoring()`
- **TODO**: 增强"冲开后的能量流向"计算

```
辰 ←→ 戌  (水库 vs 火库)
丑 ←→ 未  (金库 vs 木库)
```

#### 1.2.2 四正冲 (Cardinal Clash) - 子午 / 卯酉
- **本质**: "战局" (Energy War)
- **物理特征**: 纯粹的能量对抗，导致结构不稳
- **影响领域**: 心理健康、家庭关系、事业稳定性

```
子 ←→ 午  (Water vs Fire) - 水火未济
卯 ←→ 酉  (Wood vs Metal) - 金木交战
```

#### 1.2.3 四生冲 (Growth Clash) - 寅申 / 巳亥
- **本质**: "位移" (Displacement)
- **物理特征**: 导致变动、车祸、远行
- **影响领域**: 工作变动、居所迁移、交通安全

```
寅 ←→ 申  (Wood vs Metal) - 驿马冲
巳 ←→ 亥  (Fire vs Water) - 驿马冲
```

### 1.3 算法设计

**重要原则**: 不应只是简单的减分！

```python
# ClashEngine 伪代码
def calculate_clash_impact(clash_pair, favorable_elements, unfavorable_elements):
    """
    动态喜忌判定模型
    """
    clashed_element = get_element(clash_pair[0])
    
    if clashed_element in favorable_elements:
        # 喜神被冲 = 减分 (受伤)
        return PENALTY_SCORE
    elif clashed_element in unfavorable_elements:
        # 忌神被冲 = 加分 (去病)
        return BONUS_SCORE
    else:
        # 中性元素被冲 = 小幅波动
        return NEUTRAL_SCORE
```

**TODO**: 创建 `ClashEngine` 并引入"动态喜忌判定"。

---

## 2. 合化 (Combinations) 的本质与模型

### 2.1 理论定义
**合化** 是 **"能量的量子纠缠与波函数坍缩"** (Quantum Entanglement & Collapse)。

当特定地支/天干组合出现时，它们的能量态发生"纠缠"，在特定条件下会"坍缩"为新的能量态。

> **核心区别**: "冲"是破坏（减分/释放），而"合"是**质变**（Transformation）或**羁绊**（Binding）。

---

### 2.2 天干五合 (Heavenly Stems Five Combinations)

#### 物理本质: "化学键与元素嬗变" (Chemical Bonding & Transmutation)

这不是简单的物理混合，而是**原子级别的化合反应**。

```
甲己合土   乙庚合金   丙辛合水   丁壬合木   戊癸合火
```

#### 计算模型 (The Alchemy Model)

**状态 1: 合去 (Binding)**
- **条件**: 月令不支持化神
- **效应**: 两者互相牵制，能量失效
- **算法**: `Effectiveness = 0` (贪合忘生/贪合忘克)

```python
def check_binding(stem1, stem2, month_branch):
    """检测合去状态"""
    combo = STEM_COMBINATIONS.get((stem1, stem2))
    if not combo:
        return False
    
    transformed_element = combo['element']
    month_element = get_month_element(month_branch)
    
    # 月令不支持化神 -> 合去
    if not supports(month_element, transformed_element):
        return {
            'status': 'binding',
            'effect': 'both_neutralized',
            'message': '贪合忘生/贪合忘克'
        }
```

**状态 2: 合化 (Transformation)**
- **条件**: 得月令之气（月令支持化神）
- **效应**: 两者融合为新的五行
- **算法**: `Element(甲) -> Earth`, `Element(己) -> Earth`，原局五行力量重算

```python
def check_transformation(stem1, stem2, month_branch):
    """检测合化状态"""
    combo = STEM_COMBINATIONS.get((stem1, stem2))
    transformed_element = combo['element']
    
    if supports(get_month_element(month_branch), transformed_element):
        return {
            'status': 'transformation',
            'new_element': transformed_element,
            'affected_stems': [stem1, stem2],
            'energy_recalc': True
        }
```

**状态 3: 争合 (Jealousy)**
- **条件**: 两干争一干（如两乙合一庚）
- **效应**: 能量震荡，结构不稳
- **算法**: `Stability = Unstable` (妒合)

```python
def check_jealousy(stems_list):
    """检测争合状态"""
    # 如果有两个乙和一个庚
    if stems_list.count('乙') == 2 and '庚' in stems_list:
        return {
            'status': 'jealousy',
            'stability': 'unstable',
            'penalty': JEALOUSY_PENALTY
        }
```

---

### 2.3 地支六合 (Earthly Branches Six Combinations)

#### 物理本质: "引力锁定与量子纠缠" (Gravitational Lock & Entanglement)

本质是**"近邻效应"**，创造出一种极其稳定的结构。

```
子丑合(土)   寅亥合(木)   卯戌合(火)
辰酉合(金)   巳申合(水)   午未合(土/火)
```

#### 计算模型 (The Locking Model)

**关键机制 1: 解冲 (Resolution) - "贪合忘冲"**

> **六合的优先级 > 六冲**

```
场景: 原局有"辰戌冲"，流年来了"酉"（辰酉合）
算法: Clash(辰, 戌) 被取消，Combine(辰, 酉) 生效
效果: 吉凶反转的关键！
```

```python
def resolve_clash_with_combination(branches, year_branch):
    """
    贪合忘冲：六合优先级高于六冲
    """
    all_branches = branches + [year_branch]
    
    # 检测六合
    for b1 in all_branches:
        for b2 in all_branches:
            if is_six_combination(b1, b2):
                # 移除这两个地支参与的任何六冲
                remove_clash_involving(b1)
                remove_clash_involving(b2)
                return {
                    'combination_formed': (b1, b2),
                    'clashes_resolved': get_resolved_clashes(),
                    'message': '贪合忘冲'
                }
```

**关键机制 2: 能量增幅**
- 合化为某个五行后，该五行能量增强
- 例: 午未合土/火 -> 土或火的能量 +2.0

---

### 2.4 半合/半三合 (Half-Triangular Combinations)

#### 物理本质: "催化剂与虚空场" (Catalyst & Virtual Field)

三合局（申子辰）是完美的能量闭环。半合（申子、子辰）是**缺了一角的圆**。

它们会形成一个强大的"引力场"，通过**"虚邀"**（Virtual Pulling）召唤缺失的那个字。

```
三合水局: 申(生) - 子(旺) - 辰(墓)
三合木局: 亥(生) - 卯(旺) - 未(墓)
三合火局: 寅(生) - 午(旺) - 戌(墓)
三合金局: 巳(生) - 酉(旺) - 丑(墓)
```

#### 计算模型 (The Field Model)

**规则: 拱合力量判定**
- 生地 + 旺地（申子）= **强拱** (力量 x1.5)
- 旺地 + 墓地（子辰）= **强拱** (力量 x1.5)
- 生地 + 墓地（申辰）= **弱拱** (拱气，力量 x1.1)

```python
def calculate_half_combination(branches, year_branch):
    """
    半三合能量场计算
    """
    all_branches = set(branches + [year_branch])
    
    # 检测水局
    water_trio = {'申', '子', '辰'}
    present = water_trio & all_branches
    
    if len(present) == 3:
        # 完整三合局触发！
        return {
            'status': 'grand_trinity',
            'element': 'water',
            'multiplier': 3.0,
            'message': '申子辰三合水局大成！'
        }
    elif len(present) == 2:
        # 半合检测
        if '子' in present:  # 旺地在，强拱
            return {
                'status': 'half_combination',
                'element': 'water',
                'multiplier': 1.5,
                'virtual_field': True,
                'message': '半合水局，虚拟水场形成'
            }
        else:  # 仅生墓，弱拱
            return {
                'status': 'weak_arching',
                'element': 'water',
                'multiplier': 1.1,
                'message': '申辰拱水，力量微弱'
            }
```

**流年触发机制**:
```python
def check_trinity_trigger(natal_branches, year_branch):
    """
    检测流年是否触发三合局
    """
    # 命局有申子，流年辰 -> 瞬间触发三合局
    if {'申', '子'}.issubset(set(natal_branches)) and year_branch == '辰':
        return {
            'triggered': True,
            'element': 'water',
            'energy_boost': 3.0,
            'event': '流年引发三合水局大爆发！'
        }
```

---

### 2.5 三会 (Directional Combinations) - 方局

#### 物理本质: "元素纯化" (Purification)

同方位地支会合，强化单一元素到极致。

```
寅卯辰 → 会木 (东方木)  - 纯木能量
巳午未 → 会火 (南方火)  - 纯火能量
申酉戌 → 会金 (西方金)  - 纯金能量
亥子丑 → 会水 (北方水)  - 纯水能量
```

#### 计算模型
- 三会成局后，该方位元素能量 **x4.0**
- 优先级: 三会 > 三合 > 六合

---

## 3. 实现路线图

### Phase 1: ClashEngine (冲引擎) 增强
- [ ] 实现四正冲检测 (子午/卯酉)
- [ ] 实现四生冲检测 (寅申/巳亥)
- [ ] **引入动态喜忌判定**
  - [ ] 喜神被冲 = 减分 (受伤)
  - [ ] 忌神被冲 = 加分 (去病)
- [ ] 集成到 QuantumEngine

### Phase 2: AlchemyEngine (合化引擎) - 核心
- [ ] **天干五合 (Stem Combinations)**
  - [ ] 合去检测 (Binding): 月令不支持 → 能量失效
  - [ ] 合化检测 (Transformation): 月令支持 → 元素嬗变
  - [ ] 争合检测 (Jealousy): 两干争一干 → 能量震荡
- [ ] **地支六合 (Branch Combinations)**
  - [ ] 六合检测与锁定效应
  - [ ] 🔥 **"贪合忘冲"逻辑**: 六合优先级 > 六冲
  - [ ] 解除 Skull/Treasury 状态的机制
- [ ] **三合 (Triangular Combinations)**
  - [ ] 完整三合触发 (申子辰/亥卯未/寅午戌/巳酉丑)
  - [ ] 元素嬗变: 参与者改变五行属性
  - [ ] 能量乘数: x3.0
- [ ] **半三合 (Half Combinations)**
  - [ ] 强拱检测 (生旺/旺墓): 力量 x1.5
  - [ ] 弱拱检测 (生墓): 力量 x1.1
  - [ ] 🔥 **虚拟能量场模型**: 虚邀机制
  - [ ] 流年触发: 补齐三合瞬间爆发
- [ ] **三会 (Directional Combinations)**
  - [ ] 三会检测 (寅卯辰/巳午未/申酉戌/亥子丑)
  - [ ] 元素纯化: 能量 x4.0
  - [ ] 优先级: 三会 > 三合 > 六合

### Phase 3: HarmonyEngine (合化引擎) 集成
- [ ] 在五行分数计算前预处理元素变性
- [ ] 与 SkullEngine/TreasuryEngine 协同工作
- [ ] 处理"贪合忘冲"的状态覆盖
- [ ] 集成到 QuantumEngine.calculate_year_context()

### Phase 4: 精准调参 (Precision Tuning)
- [ ] 使用 QuantumLab 控制台
- [ ] 导入合化案例（结婚年、合作年）
- [ ] 微调 `SCORE_INTERACTION` 等参数
- [ ] 目标准确率: 90%+
- [ ] 黄金参数记录

---

## 4. 架构设计

```
QuantumEngine
    │
    ├── LuckEngine (大运/流年)
    │
    ├── AlchemyEngine (合化引擎) ← NEW in V6.1
    │   ├── detect_stem_combinations()    # 天干五合
    │   ├── detect_branch_combinations()  # 地支六合
    │   ├── detect_triangular()           # 三合
    │   ├── detect_half_triangular()      # 半三合
    │   ├── detect_directional()          # 三会
    │   └── apply_transmutation()         # 五行变性
    │
    ├── ClashEngine (冲引擎) ← ENHANCED in V6.1
    │   ├── detect_cardinal_clash()       # 四正冲
    │   ├── detect_growth_clash()         # 四生冲
    │   └── apply_dynamic_impact()        # 动态喜忌
    │
    ├── SkullEngine (三刑/风控)
    │
    └── TreasuryEngine (财库/机遇)
```

---

## 5. 参考资料

- `docs/SPRINT_5.3_SKULL_PROTOCOL.md` - 骷髅协议实现
- `docs/ALGORITHM_SUPPLEMENT_L2_STOREHOUSE.md` - 墓库理论
- `core/config_rules.py` - 算法参数配置表

---

*Document prepared by Antigravity V6.0+ System*
*Last Updated: 2024-12-14 02:09 KST*

