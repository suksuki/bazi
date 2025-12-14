# Antigravity Core Algorithm Kernel V9.0
# "First Principles" Physics Model
# ==================================
# 
# This is the ABSOLUTE foundation of the Antigravity engine.
# ALL implementations MUST strictly adhere to these 12 definitions.
# 
# CRITICAL CONSTRAINT: NO hard-coded parameters!
# All numerical values are INITIAL VARIABLES with tuning interfaces.

---

## 0. 核心约束 (Core Constraints)

```
⚠️ 所有参数必须可配置！
⚠️ 所有数值必须有回归验证接口！
⚠️ 禁止硬编码！
```

---

## 1. 基础物理层 (Physics Base)

### 1.1 阴阳 (Yin/Yang) - 自旋 (Spin)
- **阳 (Yang)**: 发散态 (+), 向外辐射能量
- **阴 (Yin)**: 收敛态 (-), 向内聚合能量

### 1.2 五行 (5 Elements) - 矢量场 (Vector Fields)
- **生 (Generation)**: 能量传递，效率 < 1.0
- **克 (Control)**: 矢量对抗，能量损耗

```
生成循环: Wood → Fire → Earth → Metal → Water → Wood
克制循环: Wood → Earth → Water → Fire → Metal → Wood
```

---

## 2. 粒子相态定义 (Particle Phases)

### 2.1 天干 (Stems) - 波形态 (Waveforms)

| # | 天干 | 英文 | 物理模型 | 描述 |
|---|------|------|----------|------|
| 1 | 甲 | Jia | Vertical Pulse | 垂直脉冲 (Tension/Tree) |
| 2 | 乙 | Yi | Horizontal Network | 水平网络 (Network/Grass) |
| 3 | 丙 | Bing | Omnidirectional Radiation | 全向辐射 (Radiation/Sun) |
| 4 | 丁 | Ding | Focused Laser | 聚焦激光 (Laser/Candle) |
| 5 | 戊 | Wu | High-Density Mass | 高密质量 (Mass/Mountain) |
| 6 | 己 | Ji | Porous Matrix | 多孔基质 (Matrix/Soil) |
| 7 | 庚 | Geng | Rough Impact | 粗糙冲击 (Impact/Ore) |
| 8 | 辛 | Xin | Precision Lattice | 精密晶格 (Crystal/Jewelry) |
| 9 | 壬 | Ren | Momentum Fluid | 动量流体 (Momentum/Tsunami) |
| 10 | 癸 | Gui | Permeation Field | 渗透场 (Permeability/Mist) |

### 2.2 地支 (Branches) - 场域环境 (Field Environments)

| # | 地支 | 英文 | 物理模型 | 描述 |
|---|------|------|----------|------|
| 1 | 子 | Zi | Abyss | 极寒深渊 |
| 2 | 丑 | Chou | Frozen Soil | 冻土/金库 |
| 3 | 寅 | Yin | Reactor | 加速反应堆 |
| 4 | 卯 | Mao | Jungle | 生命密度场 |
| 5 | 辰 | Chen | Reservoir | 水库/湿土 |
| 6 | 巳 | Si | Magnetic Bottle | 磁约束瓶 |
| 7 | 午 | Wu | Furnace | 热辐射极值 |
| 8 | 未 | Wei | Desert | 燥土/木库 |
| 9 | 申 | Shen | Mineral | 金属矿脉 |
| 10 | 酉 | You | Blade | 纯粹晶体场 |
| 11 | 戌 | Xu | Volcano | 火库/高压区 |
| 12 | 亥 | Hai | Ocean | 原始汤 |

---

## 3. 结构算法 (Structure)

### 3.1 地支壳核模型 (Shell-Core Model)

```
┌─────────────────────────────────────┐
│            SHELL (壳)               │
│  - 外部物理属性                      │
│  - 冲合交互接口                      │
├─────────────────────────────────────┤
│            CORE (核)                │
│  - 藏干能量分布                      │
│  - 主气/中气/余气                    │
└─────────────────────────────────────┘
```

### 3.2 藏干能量分布 (Hidden Stem Distribution)

```python
# 初始参数 [需校验]
HIDDEN_STEM_RATIOS = {
    "main": 0.60,     # 主气 60%
    "middle": 0.30,   # 中气 30%
    "residual": 0.10  # 余气 10%
}
```

---

## 4. 几何交互算法 (Geometric Interaction)

### 4.1 地支交互 - 12长生相位角 (Phase Angles)

```
                    子(0°)
                      │
          亥(30°)     │     丑(330°)
                \     │     /
                 \    │    /
      戌(60°) ────────┼────────── 寅(300°)
                 /    │    \
                /     │     \
          酉(90°)     │     卯(270°)
                      │
                    午(180°)

冲 (180°): 能量湮灭/释放 (子-午, 寅-申, 卯-酉, 辰-戌, 巳-亥, 丑-未)
合 (120°/60°): 相位锁定/共振 (三合/六合)
刑 (90°/特殊角): 剪切力/结构破坏
害 (特殊角): 干扰/暗斗
```

### 4.2 天干交互 - 河图数理 (Vector Resonance)

```
相位差 = 5 → 化合反应 (天干五合)

甲(1) + 己(6) → 土
乙(2) + 庚(7) → 金
丙(3) + 辛(8) → 水
丁(4) + 壬(9) → 木
戊(5) + 癸(10) → 火
```

---

## 5. 动力学做功 (Dynamics & Work)

### 5.1 垂直作用 (Vertical Interaction)
- **通根 (Rooting)**: 天干在地支找到同属性藏干，能量稳固
- **透干 (Projection)**: 藏干显露于天干，能量放大

### 5.2 水平传导 (Horizontal Conduction)
- **距离衰减**: $K_{distance} = \frac{1}{D^2}$
- **生克阻力**: 受五行关系调节

### 5.3 做功公式 (Work Formula)

```math
Work = Energy × Efficiency × K_{distance} × K_{relation}
```

---

## 6. 时空体系 (Spacetime System)

### 6.1 大运 (Luck Pillar) - 静态背景
- 作用: 重写原局物理常数
- 周期: 10年/步
- 影响: 改变基础场域参数

### 6.2 流年 (Annual Pillar) - 动态触发
- 作用: 高能粒子撞击原局端口
- 周期: 1年
- 影响: 触发事件/激活潜能

```
┌──────────────────────────────────────────────┐
│                  原局 (Birth Chart)          │
│  ┌─────┬─────┬─────┬─────┐                   │
│  │ 年柱 │ 月柱 │ 日柱 │ 时柱 │ ← 静态结构      │
│  └─────┴─────┴─────┴─────┘                   │
│           ↑            ↑                     │
│      大运背景场      流年触发器               │
│  (Static Field)   (Dynamic Trigger)          │
└──────────────────────────────────────────────┘
```

---

## 7. 空间修正 ($K_{geo}$)

### 7.1 公理
```
命运 = f(时间, 空间)
```

### 7.2 经纬度修正

```python
# 初始参数 [需校验]
def calculate_geo_modifier(latitude, longitude, birth_chart):
    """
    纬度修正寒暖 (Temperature Modifier)
    地形修正燥湿 (Humidity Modifier)
    """
    K_temperature = interpolate_latitude(latitude)  # 北方偏寒，南方偏暖
    K_humidity = interpolate_terrain(longitude)     # 沿海偏湿，内陆偏燥
    
    return K_temperature * K_humidity
```

---

## 8. 概率计算 (Probability)

### 8.1 废除宿命论
- ❌ 不输出绝对结论
- ✅ 输出概率分布

### 8.2 量子波函数 (Wave Function)

```python
def calculate_destiny_probability(state, context):
    """
    输出: 概率分布，而非单一结论
    
    Example:
    {
        "strong": 0.65,  # 65% 身强概率
        "weak": 0.30,    # 30% 身弱概率
        "follower": 0.05 # 5% 从格概率
    }
    """
    wave_function = superpose_states(state, context)
    return collapse_to_probability(wave_function)
```

---

## 9. 演化机制 (Evolution)

### 9.1 核心指令

```
⚠️ 所有参数不要写死！
⚠️ 必须建立反馈回路！
⚠️ 利用真实案例进行回归验证！
```

### 9.2 参数调优框架

```python
# 可调参数注册表
TUNABLE_PARAMS = {
    # 基础物理
    "hidden_stem_ratios": {"main": 0.6, "middle": 0.3, "residual": 0.1},
    "pillar_weights": {"year": 0.8, "month": 2.0, "day": 1.0, "hour": 0.9},
    
    # 交互参数
    "clash_damping": 0.5,
    "combination_bonus": 1.5,
    "punishment_penalty": -0.3,
    
    # 流转参数
    "generation_efficiency": 0.7,
    "control_impact": 0.5,
    "spatial_decay": {"gap1": 0.6, "gap2": 0.3},
    
    # 相变参数 [V8.0]
    "scorched_earth_damping": 0.15,
    "frozen_water_damping": 0.3,
    
    # 阈值
    "energy_threshold_strong": 3.5,
    "energy_threshold_weak": 2.0
}

def regression_tune(params, real_cases):
    """
    利用真实案例 V_real 进行回归调优
    """
    for case in real_cases:
        predicted = calculate(case, params)
        actual = case.ground_truth
        loss = compute_loss(predicted, actual)
        
        # 反向传播调整参数
        params = gradient_descent(params, loss)
    
    return optimized_params
```

---

## 10. 实现检查清单 (Implementation Checklist)

| # | 模块 | 状态 | 文件 |
|---|------|------|------|
| 1 | 基础物理层 | ✅ | `core/constants.py` |
| 2 | 粒子定义 | ✅ | `core/calculator.py` |
| 3 | 壳核模型 | ✅ | `core/constants.py` (HIDDEN_STEMS_MAP) |
| 4 | 几何交互 | ✅ | `core/engines/harmony_engine.py` |
| 5 | 动力学做功 | ✅ | `core/engines/flow_engine.py` |
| 6 | 时空体系 | ✅ | `core/engines/luck_engine.py` |
| 7 | 空间修正 | 🔶 | `core/config_schema.py` (macroPhysics) |
| 8 | 概率计算 | ⏳ | TODO: V9.0 |
| 9 | 演化机制 | ✅ | `core/config_schema.py` (全参数化) |
| 10 | 相变协议 | ✅ | `core/engines/flow_engine.py` (V8.0) |

---

## Version History

| Version | Date | Description |
|---------|------|-------------|
| V1.0 | 2024-12 | Initial Constitution |
| V6.0 | 2025-12-13 | Oracle Edition (BaziProfile) |
| V7.4 | 2025-12-14 | Physicist Edition (Damping Protocol) |
| V8.0 | 2025-12-14 | Phase Change Protocol |
| V9.0 | TBD | First Principles Kernel (This Spec) |

---

**END OF CORE ALGORITHM KERNEL SPECIFICATION**
