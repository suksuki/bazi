# Antigravity Core Algorithm Kernel V32.0
## First Principles Physics Model - Complete Documentation

---

## 🎯 核心理念 (Core Philosophy)

**"NO HARD-CODED PARAMETERS"**

所有物理常数都是**变量**，必须通过数据回归和真实案例验证来优化。

---

## 📋 12条核心定义 (12 Core Definitions)

### 1. 基础物理层 (Physics Base)

#### 阴阳 = 自旋 (Yin/Yang = Spin)
- **阳 (Yang)**: 发散 (+1 spin)
- **阴 (Yin)**: 收敛 (-1 spin)

#### 五行 = 矢量场 (5 Elements = Vector Fields)
```python
Wood  = [1, 0, 0, 0, 0]
Fire  = [0, 1, 0, 0, 0]
Earth = [0, 0, 1, 0, 0]
Metal = [0, 0, 0, 1, 0]
Water = [0, 0, 0, 0, 1]
```

- **生 (Sheng)**: 能量传递方向
- **克 (Ke)**: 矢量对抗

---

### 2. 粒子相态定义 (Particle Phases)

#### 天干 - 波形态 (Stems - Waveforms)

| 天干 | 波形态 | 描述 | 河图数 |
|------|--------|------|--------|
| 甲 | Vertical Pulse | 垂直脉冲 (Tree) | 1 |
| 乙 | Horizontal Network | 水平网络 (Grass) | 2 |
| 丙 | Omnidirectional Radiation | 全向辐射 (Sun) | 3 |
| 丁 | Focused Laser | 聚焦激光 (Candle) | 4 |
| 戊 | High Density Mass | 高密质量 (Mountain) | 5 |
| 己 | Porous Matrix | 多孔基质 (Soil) | 6 |
| 庚 | Rough Impact | 粗糙冲击 (Ore) | 7 |
| 辛 | Precision Crystal | 精密晶格 (Jewelry) | 8 |
| 壬 | Momentum Fluid | 动量流体 (Tsunami) | 9 |
| 癸 | Permeability Field | 渗透场 (Mist) | 10 |

#### 地支 - 场域环境 (Branches - Field Environments)

| 地支 | 场域环境 | 相位角 | 季节 |
|------|----------|--------|------|
| 子 | Polar Abyss (极寒深渊) | 0° | Winter Peak |
| 丑 | Frozen Soil (冻土/金库) | 30° | Winter End |
| 寅 | Accelerator Reactor (加速反应堆) | 60° | Spring Begin |
| 卯 | Life Density Field (生命密度场) | 90° | Spring Peak |
| 辰 | Reservoir (水库/湿土) | 120° | Spring End |
| 巳 | Magnetic Bottle (磁约束瓶) | 150° | Summer Begin |
| 午 | Thermal Furnace (热辐射极值) | 180° | Summer Peak |
| 未 | Desert (燥土/木库) | 210° | Summer End |
| 申 | Mineral Vein (金属矿脉) | 240° | Autumn Begin |
| 酉 | Pure Crystal Field (纯粹晶体场) | 270° | Autumn Peak |
| 戌 | Volcano (火库/高压区) | 300° | Autumn End |
| 亥 | Primordial Ocean (原始汤) | 330° | Winter Begin |

---

### 3. 结构算法 (Structure Algorithm)

#### 地支壳核模型 (Shell-Core Model)

```
Branch = Shell (外壳) + Core (藏干)
```

**藏干能量分布** (初始参数，需校验):
- 主气: 60%
- 中气: 30%
- 余气: 10%

**参数化**:
```json
"hidden_stems_ratios": {
  "子": {"癸": 1.0},
  "丑": {"己": 0.60, "癸": 0.30, "辛": 0.10},
  ...
}
```

---

### 4. 几何交互算法 (Geometric Interaction)

#### 地支相位角交互

| 角度 | 类型 | 物理意义 | 强度系数 |
|------|------|----------|----------|
| 180° | 冲 (Chong) | 能量湮灭/释放 | 0.8 |
| 120° | 三合 (SanHe) | 相位锁定/共振 | 1.5 |
| 60° | 六合 (LiuHe) | 组合/绑定 | 1.2 |
| 90° | 刑 (Xing) | 剪切力/摩擦 | 0.3 |

#### 天干河图共振

**规则**: 河图数差为 5 的天干发生共振
- 甲(1) ↔ 己(6)
- 乙(2) ↔ 庚(7)
- 丙(3) ↔ 辛(8)
- 丁(4) ↔ 壬(9)
- 戊(5) ↔ 癸(10)

---

### 5. 动力学做功 (Dynamics & Work)

#### 通根 (Rooting)
```
Rooting_Strength = Base_Strength × Ratio / (Distance^N)
```

**参数**:
- `base_strength`: 1.0
- `distance_decay`: 2.0 (N值)

#### 透干 (Projection)
```
Projection_Strength = Hidden_Stem_Ratio × Efficiency
```

**参数**:
- `projection_efficiency`: 0.8

#### 能量流 (Energy Flow)
```
Transferred_Energy = Source_Energy × Efficiency / (Distance^N)
```

**参数**:
- `sheng_transfer_efficiency`: 0.7 (生)
- `ke_resistance_factor`: 0.5 (克)
- `distance_decay_exponent`: 2.0

#### 做功公式 (Work Formula)
```
Work = Energy × Efficiency × Coefficient
```

---

### 6. 时空体系 (Spacetime System)

#### 大运 (Da Yun) - 静态背景场
- **作用**: 重写原局物理常数
- **参数**:
  - `field_strength`: 1.0
  - `constant_rewrite_factor`: 0.5

#### 流年 (Liu Nian) - 动态触发粒子
- **作用**: 高能粒子撞击原局端口
- **参数**:
  - `impact_strength`: 1.2
  - `trigger_threshold`: 0.3

---

### 7. 空间修正 ($K_{geo}$)

**公理**: 命运 = 时间 + 空间

#### 纬度修正 (Temperature)
```
Modifier = 1.0 - (|Latitude| × Coefficient)
```

**参数**: `latitude_temperature_coefficient`: 0.01

#### 地形修正 (Humidity)

| 地形 | 湿度系数 |
|------|----------|
| Coastal | 1.2 |
| Inland | 1.0 |
| Desert | 0.7 |
| Mountain | 0.9 |

---

### 8. 概率计算 (Probability)

#### 量子波函数 (Wave Function)
```
Ψ(x) = N(μ, σ²)
```

**参数**:
- `wavefunction_uncertainty_base`: 10.0 (σ)
- `probability_threshold_high`: 0.7
- `probability_threshold_low`: 0.3

**输出**: 概率分布，而非单一结论

---

### 9. 演化机制 (Evolution)

**核心指令**: **所有参数不要写死！**

#### 反馈回路
```
Real_Case → Validation → Error_Calculation → Parameter_Adjustment
```

#### 优化目标
- 训练案例数: ≥ 1000
- 验证准确率: ≥ 85%

---

## 🏗️ 系统架构 (System Architecture)

### 核心模块

```
core/
├── physics_kernel.py       # 物理内核 (Definitions 1-4)
│   ├── PhysicsParameters   # 参数存储
│   ├── ParticleDefinitions # 粒子定义
│   └── GeometricInteraction # 几何交互
│
├── dynamics_engine.py      # 动力学引擎 (Definitions 5-9)
│   ├── DynamicsEngine      # 动力学计算
│   ├── SpacetimeEngine     # 时空系统
│   ├── SpatialCorrection   # 空间修正
│   ├── ProbabilityEngine   # 概率计算
│   └── ParameterOptimizer  # 参数优化
│
└── config/
    └── physics_params_default.json  # 默认参数配置
```

---

## 🔧 使用方法 (Usage)

### 1. 初始化物理参数
```python
from core.physics_kernel import PhysicsParameters

# 使用默认参数
params = PhysicsParameters()

# 或从配置文件加载
params = PhysicsParameters('config/physics_params_default.json')
```

### 2. 创建引擎
```python
from core.physics_kernel import GeometricInteraction
from core.dynamics_engine import DynamicsEngine, SpacetimeEngine

geo = GeometricInteraction(params)
dyn = DynamicsEngine(params)
st = SpacetimeEngine(params)
```

### 3. 计算几何交互
```python
# 检测地支冲合
interaction = geo.identify_interaction('子', '午')
# 返回: {'type': 'Chong', 'angle': 180, 'strength': 0.8, ...}

# 检测天干河图共振
resonance = geo.check_hetu_resonance('甲', '己')
# 返回: {'type': 'HetuResonance', 'stems': ['甲', '己'], ...}
```

### 4. 计算通根力
```python
# 天干通根到地支
rooting = dyn.calculate_rooting_strength('甲', '寅', distance=0)
# 返回: 0.6 (甲在寅中占60%)
```

### 5. 应用时空效应
```python
# 应用大运
state_with_dayun = st.apply_dayun_field(original_state, '甲', '寅')

# 应用流年
final_state = st.apply_liunian_trigger(state_with_dayun, '丙', '午')
```

### 6. 概率计算
```python
from core.dynamics_engine import ProbabilityEngine

prob = ProbabilityEngine(params)

# 创建波函数
wf = prob.create_wavefunction(mean=70, uncertainty=15)

# 计算概率
p_high = prob.calculate_probability(wf, threshold=80)
# 返回: 0.25 (25%概率超过80)
```

### 7. 参数优化
```python
from core.dynamics_engine import ParameterOptimizer

optimizer = ParameterOptimizer(params)

# 验证预测
validation = optimizer.validate_against_real_case(
    predicted_value=75,
    real_value=80
)

# 建议参数调整
new_value = optimizer.suggest_parameter_adjustment(
    'sheng_transfer_efficiency',
    [validation]
)

# 更新参数
params.update_parameter('sheng_transfer_efficiency', new_value)

# 保存优化后的参数
params.save_to_file('config/physics_params_optimized.json')
```

---

## 📊 参数清单 (Parameter Inventory)

### 可调参数总数: 30+

#### 结构参数 (3)
1. `hidden_stems_ratios` - 藏干比例 (12组)

#### 几何参数 (8)
2. `angle_chong` - 冲角度
3. `angle_sanhe` - 三合角度
4. `angle_liuhe` - 六合角度
5. `angle_xing` - 刑角度
6. `chong_energy_release` - 冲能量释放
7. `sanhe_resonance_boost` - 三合共振增幅
8. `liuhe_binding_strength` - 六合绑定强度
9. `xing_friction_loss` - 刑摩擦损耗

#### 动力学参数 (7)
10. `rooting_base_strength` - 通根基础强度
11. `rooting_distance_decay` - 通根距离衰减
12. `projection_efficiency` - 透干效率
13. `sheng_transfer_efficiency` - 生传递效率
14. `ke_resistance_factor` - 克阻力系数
15. `distance_decay_exponent` - 距离衰减指数
16. `work_energy_coefficient` - 做功能量系数

#### 时空参数 (4)
17. `dayun_field_strength` - 大运场强
18. `dayun_constant_rewrite_factor` - 大运常数重写系数
19. `liunian_impact_strength` - 流年冲击强度
20. `liunian_trigger_threshold` - 流年触发阈值

#### 空间参数 (2+4)
21. `latitude_temperature_coefficient` - 纬度温度系数
22. `longitude_phase_shift` - 经度相位偏移
23-26. `terrain_humidity_modifier` - 地形湿度系数 (4种)

#### 概率参数 (3)
27. `wavefunction_uncertainty_base` - 波函数不确定性
28. `probability_threshold_high` - 高概率阈值
29. `probability_threshold_low` - 低概率阈值

#### 位置参数 (4)
30-33. `position_weights` - 四柱权重

#### 自旋参数 (2)
34. `yang_divergence_factor` - 阳发散系数
35. `yin_convergence_factor` - 阴收敛系数

---

## 🎯 优化流程 (Optimization Workflow)

### Phase 1: 数据收集
1. 收集真实案例 (≥1000个)
2. 标注准确结果
3. 建立训练集/验证集

### Phase 2: 初始验证
1. 使用默认参数运行
2. 计算预测误差
3. 识别关键参数

### Phase 3: 参数调优
1. 选择优化算法 (梯度下降/遗传算法)
2. 定义损失函数
3. 迭代优化参数
4. 交叉验证

### Phase 4: 验证部署
1. 在验证集上测试
2. 达到目标准确率 (≥85%)
3. 保存优化参数
4. 部署到生产环境

---

## ⚠️ 重要警告 (Critical Warnings)

### 1. 参数不确定性
**当前所有参数都是初始估计值，未经数据验证！**

使用前必须:
- 收集真实案例
- 进行参数回归
- 验证准确性

### 2. 模型局限性
- 这是粗陋的初始模型
- 需要持续迭代改进
- 不应盲目信任预测结果

### 3. 优化要求
- 最少1000个训练案例
- 目标准确率≥85%
- 需要专业的优化工程师

---

## 📚 参考文献 (References)

### 理论基础
- 传统子平八字理论
- 量子力学基础
- 统计物理学
- 系统工程

### 技术实现
- NumPy (数值计算)
- SciPy (概率分布)
- JSON (参数存储)

---

## 🚀 未来方向 (Future Directions)

### V33.0 计划
1. **深度学习集成**: 使用神经网络自动优化参数
2. **多目标优化**: 同时优化多个预测维度
3. **实时反馈**: 在线学习和参数更新
4. **可解释性**: 参数物理意义的可视化

### 长期愿景
- 完全数据驱动的物理模型
- 自适应参数系统
- 个性化预测引擎

---

**版本**: V32.0  
**状态**: 🟡 INITIAL - REQUIRES OPTIMIZATION  
**下一步**: 数据收集 → 参数回归 → 验证部署

**开发**: Antigravity Team  
**技术支持**: Google Deepmind Advanced Agentic Coding

---

**最后更新**: 2025-12-12
