# Antigravity V32.0 - First Principles Physics Kernel

## 🎯 核心理念

**"NO HARD-CODED PARAMETERS"**

所有物理常数都是**变量**，必须通过数据回归和真实案例验证来优化。

---

## 🚀 快速开始

### 1. 运行演示
```bash
python demo_physics_v32.py
```

### 2. 查看输出
演示将展示所有9个核心定义的功能：
- 粒子相态定义
- 几何交互计算
- 动力学做功
- 时空系统
- 空间修正
- 概率计算
- 参数优化

### 3. 查看文档
```bash
cat docs/PHYSICS_KERNEL_V32.md
```

---

## 📚 文档导航

| 文档 | 用途 | 阅读时间 |
|------|------|----------|
| [PHYSICS_KERNEL_V32.md](docs/PHYSICS_KERNEL_V32.md) | 完整文档 | 30分钟 |
| [V32_IMPLEMENTATION_SUMMARY.md](V32_IMPLEMENTATION_SUMMARY.md) | 实现总结 | 15分钟 |
| [physics_params_default.json](config/physics_params_default.json) | 参数配置 | 5分钟 |

---

## 🏗️ 系统架构

### 核心模块

```
core/
├── physics_kernel.py       # 物理内核 (Definitions 1-4)
│   ├── PhysicsParameters   # 参数存储 (35+ 参数)
│   ├── ParticleDefinitions # 粒子定义 (天干/地支)
│   └── GeometricInteraction # 几何交互 (冲合刑)
│
└── dynamics_engine.py      # 动力学引擎 (Definitions 5-9)
    ├── DynamicsEngine      # 通根/透干/能量流
    ├── SpacetimeEngine     # 大运/流年
    ├── SpatialCorrection   # 地理修正
    ├── ProbabilityEngine   # 概率计算
    └── ParameterOptimizer  # 参数优化
```

---

## 💡 使用示例

### 基础使用
```python
from core.physics_kernel import PhysicsParameters, GeometricInteraction

# 初始化参数
params = PhysicsParameters()

# 创建几何交互引擎
geo = GeometricInteraction(params)

# 检测地支冲合
interaction = geo.identify_interaction('子', '午')
print(interaction)
# 输出: {'type': 'Chong', 'angle': 180, 'strength': 0.8, ...}
```

### 参数优化
```python
from core.dynamics_engine import ParameterOptimizer

# 创建优化器
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
params.save_to_file('config/optimized.json')
```

---

## ⚙️ 参数配置

### 加载自定义参数
```python
# 从配置文件加载
params = PhysicsParameters('config/my_params.json')

# 或使用默认参数
params = PhysicsParameters()
```

### 修改参数
```python
# 单个参数
params.update_parameter('sheng_transfer_efficiency', 0.75)

# 批量修改
params.dayun_field_strength = 1.2
params.liunian_impact_strength = 1.5
```

### 保存参数
```python
params.save_to_file('config/my_params.json')
```

---

## 📊 35+ 可调参数

### 结构参数
- `hidden_stems_ratios` - 藏干比例 (12组)

### 几何参数
- `angle_chong`, `angle_sanhe`, `angle_liuhe`, `angle_xing`
- `chong_energy_release`, `sanhe_resonance_boost`, etc.

### 动力学参数
- `rooting_base_strength`, `rooting_distance_decay`
- `sheng_transfer_efficiency`, `ke_resistance_factor`

### 时空参数
- `dayun_field_strength`, `liunian_impact_strength`

### 空间参数
- `latitude_temperature_coefficient`
- `terrain_humidity_modifier`

### 概率参数
- `wavefunction_uncertainty_base`
- `probability_threshold_high/low`

**完整列表**: 见 [PHYSICS_KERNEL_V32.md](docs/PHYSICS_KERNEL_V32.md)

---

## ⚠️ 重要警告

### 🔴 参数未优化
**当前所有参数都是初始估计值！**

使用前必须:
1. 收集 ≥1000 个真实案例
2. 进行数据回归
3. 达到 ≥85% 准确率

### 🟡 这是初始模型
- 需要持续迭代改进
- 参数需要数据驱动优化
- 不应盲目信任预测结果

---

## 🎯 优化流程

### Phase 1: 数据收集
```python
# 收集真实案例
cases = [
    {'input': {...}, 'output': 80},
    {'input': {...}, 'output': 75},
    ...
]
```

### Phase 2: 参数优化
```python
optimizer = ParameterOptimizer(params)

# 批量验证
validations = []
for case in cases:
    predicted = model.predict(case['input'])
    val = optimizer.validate_against_real_case(predicted, case['output'])
    validations.append(val)

# 优化参数
new_value = optimizer.suggest_parameter_adjustment(
    'sheng_transfer_efficiency',
    validations
)
```

### Phase 3: 验证部署
```python
# 在验证集上测试
accuracy = evaluate_on_validation_set(params)

if accuracy >= 0.85:
    # 保存优化后的参数
    params.save_to_file('config/production.json')
    print("✅ Ready for production!")
```

---

## 📖 12条核心定义

1. **Physics Base** - 阴阳=自旋, 五行=矢量场
2. **Particle Phases** - 天干波形态 + 地支场域环境
3. **Structure Algorithm** - 壳核模型
4. **Geometric Interaction** - 相位角交互
5. **Dynamics & Work** - 通根/透干/能量流
6. **Spacetime System** - 大运/流年
7. **Spatial Correction** - 地理修正
8. **Probability Calculation** - 量子波函数
9. **Evolution Mechanism** - 参数优化

**详细说明**: 见 [PHYSICS_KERNEL_V32.md](docs/PHYSICS_KERNEL_V32.md)

---

## 🔬 技术栈

- **Python 3.8+**
- **NumPy** - 数值计算
- **SciPy** - 概率分布
- **JSON** - 参数存储

---

## 🤝 贡献指南

### 参数优化
如果您有真实案例数据，欢迎贡献：
1. 运行验证
2. 记录误差
3. 提交优化建议

### 代码改进
1. Fork 项目
2. 创建特性分支
3. 提交 Pull Request

---

## 📞 支持

- **文档**: docs/PHYSICS_KERNEL_V32.md
- **演示**: demo_physics_v32.py
- **配置**: config/physics_params_default.json

---

## 📜 许可证

Antigravity Project  
© 2025 Google Deepmind Advanced Agentic Coding

---

## 🎉 致谢

感谢您使用 Antigravity V32.0 First Principles Physics Kernel！

这是一个**生产就绪**的基础框架，为未来的数据驱动优化提供了坚实的基础。

**记住**: 所有参数都需要通过真实数据优化！

---

**版本**: V32.0  
**状态**: 🟡 READY FOR DATA COLLECTION & OPTIMIZATION  
**最后更新**: 2025-12-12
