# V16.0 参数同步控制机制设计文档

## 概述

V16.0 实现了基于配置文件的参数同步控制机制，确保 **Model/Config 作为唯一的数据源，驱动 Controller 和 View**。该机制实现了自动化调优的基础架构，允许 Cursor 通过修改配置文件间接控制 UI 和批量校准脚本的参数。

**版本**: V16.0  
**创建日期**: 2024  
**最后更新**: 2024

---

## 设计目标

### 核心原则

1. **单一数据源 (Single Source of Truth)**
   - `config/parameters.json` 是粒子权重和物理参数的唯一权威来源
   - UI 和批量脚本都必须从该文件读取参数

2. **双向同步**
   - **写操作 (Cursor 自动化)**: Cursor 修改 → 写入 `config/parameters.json`
   - **读操作 (UI 同步)**: Streamlit UI 强制从 `config/parameters.json` 读取值
   - **用户交互**: UI 滑块修改 → 写回 `config/parameters.json`

3. **优先级规则**
   - `config/parameters.json` 永远是最高优先级的数据源
   - UI Session State 或默认值仅在配置文件不存在时使用

---

## 架构设计

### MVC 分层架构

```
┌─────────────────────────────────────────────────────────────┐
│                    config/parameters.json                      │
│                  (Single Source of Truth)                      │
└───────────────────────┬───────────────────────────────────────┘
                        │
        ┌───────────────┴───────────────┐
        │                               │
        ▼                               ▼
┌───────────────┐              ┌──────────────────┐
│  Controller   │              │ Batch Script     │
│ (BaziController)│              │ (run_batch_     │
│               │              │  calibration.py) │
│ - Load Config │              │ - Load Config    │
│ - Save Config │              │ - Apply Config  │
│ - Get Weights │              │                 │
└───────┬───────┘              └──────────────────┘
        │
        │
        ▼
┌───────────────┐
│  View (P2 UI) │
│ (quantum_lab) │
│               │
│ - Read Config │
│ - Display     │
│ - Save Config │
└───────────────┘
        │
        ▼
┌───────────────┐
│  Engine       │
│ (EngineV88)   │
│               │
│ - Use Config  │
└───────────────┘
```

### 数据流

#### 1. 初始化流程

```
Controller.__init__()
    ↓
_load_particle_weights_config()
    ↓
读取 config/parameters.json
    ↓
存储到 self._particle_weights_config
```

#### 2. UI 加载流程

```
P2 UI 渲染
    ↓
controller.get_current_particle_weights()
    ↓
优先返回 self._particle_weights_config (来自配置文件)
    ↓
设置滑块初始值 (value=config_value * 100)
```

#### 3. 用户修改流程

```
用户拖动滑块
    ↓
获取新值 (slider_value / 100)
    ↓
点击"保存粒子权重到配置"
    ↓
controller._save_particle_weights_config(weights)
    ↓
写入 config/parameters.json
    ↓
更新 self._particle_weights_config
    ↓
st.rerun() 刷新 UI
```

#### 4. Cursor 自动化流程

```
Cursor 修改 config/parameters.json
    ↓
用户刷新 P2 UI
    ↓
Controller 重新加载配置
    ↓
UI 滑块自动同步到新值
```

#### 5. 批量校准流程

```
run_batch_calibration.py 启动
    ↓
读取 config/parameters.json
    ↓
提取 particleWeights 和 physics 配置
    ↓
应用到 params 字典
    ↓
传递给 Engine.update_full_config()
```

---

## 实现细节

### 1. 配置文件结构

**文件路径**: `config/parameters.json`

```json
{
  "particleWeights": {
    "PianCai": 1.50,
    "ZhengCai": 1.30,
    "ShiShen": 1.40,
    "ShangGuan": 1.20,
    "QiSha": 1.15,
    "BiJian": 1.50,
    "JieCai": 1.05,
    "ZhengYin": 0.90,
    "PianYin": 0.90,
    "ZhengGuan": 1.0
  },
  "physics": {
    "pillarWeights": {
      "year": 0.8,
      "month": 1.2,
      "day": 1.0,
      "hour": 0.9
    },
    "WealthAmplifier": 1.30,
    "NonLinearExponent": 1.3,
    "CareerAmplifier": 1.15,
    "RelationshipAmplifier": 1.10
  },
  "flow": {
    "outputViscosity": {
      "maxDrainRate": 0.35,
      "drainFriction": 0.30,
      "viscosity": 0.95
    },
    "resourceImpedance": {
      "base": 0.75,
      "weaknessPenalty": 0.75
    }
  }
}
```

### 2. Controller 层实现

#### 2.1 配置加载 (`BaziController._load_particle_weights_config`)

```python
def _load_particle_weights_config(self) -> None:
    """
    V16.0: Load particle weights from config/parameters.json.
    This is the single source of truth for particle weights.
    """
    import os
    import json
    
    try:
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_path = os.path.join(project_root, "config", "parameters.json")
        
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
                self._particle_weights_config = config_data.get('particleWeights', {})
            logger.info(f"Particle weights loaded from {config_path}")
        else:
            logger.warning(f"Config file not found: {config_path}, using defaults")
            self._particle_weights_config = {}
    except Exception as e:
        logger.error(f"Failed to load particle weights config: {e}")
        self._particle_weights_config = {}
```

**调用时机**: `BaziController.__init__()` 时自动调用

#### 2.2 配置保存 (`BaziController._save_particle_weights_config`)

```python
def _save_particle_weights_config(self, weights: Dict[str, float]) -> bool:
    """
    V16.0: Save particle weights to config/parameters.json.
    Returns True if successful, False otherwise.
    """
    import os
    import json
    
    try:
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_path = os.path.join(project_root, "config", "parameters.json")
        
        # Load existing config
        config_data = {}
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
        
        # Update particle weights
        config_data['particleWeights'] = weights
        self._particle_weights_config = weights
        
        # Save back
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Particle weights saved to {config_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to save particle weights config: {e}")
        return False
```

#### 2.3 权重获取 (`BaziController.get_current_particle_weights`)

```python
def get_current_particle_weights(self) -> Dict[str, float]:
    """
    V16.0: Return current particle weights.
    Priority: user_input > config file > defaults (1.0)
    """
    # First check user input (from UI sliders)
    pw = self._user_input.get('particle_weights') if self._user_input else None
    if pw:
        return pw
    
    # Fall back to config file (single source of truth)
    if self._particle_weights_config:
        return self._particle_weights_config.copy()
    
    # Default: all 1.0
    from utils.constants_manager import get_constants
    consts = get_constants()
    return {god: 1.0 for god in consts.TEN_GODS}
```

**优先级规则**:
1. `user_input['particle_weights']` (UI 滑块当前值)
2. `_particle_weights_config` (配置文件值)
3. 默认值 1.0

#### 2.4 Engine 配置更新 (`BaziController._calculate_base`)

```python
# V16.0: Update engine config with particle weights from config file
particle_weights = self.get_current_particle_weights()
if particle_weights:
    # Build full config structure for engine
    from core.config_schema import DEFAULT_FULL_ALGO_PARAMS
    engine_config = DEFAULT_FULL_ALGO_PARAMS.copy()
    engine_config['particleWeights'] = particle_weights
    self._quantum_engine.update_full_config(engine_config)
    logger.debug(f"Updated QuantumEngine with {len(particle_weights)} particle weights from config")
```

**调用时机**: 每次 `_calculate_base()` 时，确保 Engine 使用最新配置

### 3. UI 层实现 (`ui/pages/quantum_lab.py`)

#### 3.1 滑块初始化

```python
# V16.0: Load particle weights from Controller (which reads from config/parameters.json)
config_weights = controller.get_current_particle_weights()

particle_weights = {}
# V16.0: Slider value now comes from config file via Controller
pw_res_col1, pw_res_col2 = st.sidebar.columns(2)
zheng_yin_val = int(config_weights.get(consts.TEN_GODS[0], 1.0) * 100)
particle_weights[consts.TEN_GODS[0]] = pw_res_col1.slider(
    "正印 (Zheng Yin)", 50, 150, zheng_yin_val, step=5, key="pw_p2_zhengyin"
) / 100
# ... 其他滑块类似
```

**关键点**:
- 滑块 `value` 参数绑定到 `config_weights.get(god_name, 1.0) * 100`
- 确保 UI 显示的是配置文件中的值

#### 3.2 保存按钮

```python
# V16.0: Save button to write slider values back to config file
if st.sidebar.button("💾 保存粒子权重到配置", type="secondary"):
    if controller._save_particle_weights_config(particle_weights):
        st.sidebar.success("✅ 粒子权重已保存到 config/parameters.json")
        st.rerun()
    else:
        st.sidebar.error("❌ 保存失败，请检查日志")
```

**功能**:
- 将当前滑块值写回配置文件
- 触发 UI 刷新，确保同步

### 4. 批量校准脚本实现 (`scripts/run_batch_calibration.py`)

#### 4.1 配置加载

```python
# V16.0: Load particle weights and physics config from config/parameters.json
config_path = os.path.join(os.path.dirname(__file__), "../config/parameters.json")
particle_weights_from_config = {}
physics_config_from_file = {}
if os.path.exists(config_path):
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
            particle_weights_from_config = config_data.get('particleWeights', {})
            physics_config_from_file = config_data.get('physics', {})
            print(f"✅ Loaded particle weights from config: {len(particle_weights_from_config)} weights")
            print(f"✅ Loaded physics config: {list(physics_config_from_file.keys())}")
    except Exception as e:
        print(f"⚠️ Failed to load config: {e}, using defaults")
```

#### 4.2 配置应用

```python
# Apply weights from config file
if particle_weights_from_config:
    pw.update(particle_weights_from_config)
    print(f"📊 Using particle weights from config/parameters.json")

# Apply physics config (amplifiers, exponents)
if physics_config_from_file:
    if 'physics' not in params:
        params['physics'] = {}
    for key, value in physics_config_from_file.items():
        if key != 'pillarWeights':  # pillarWeights handled separately
            params['physics'][key] = value
    print(f"📊 Applied physics config: WealthAmplifier={params['physics'].get('WealthAmplifier', 'N/A')}")
```

### 5. Engine 层实现 (`core/engine_v88.py`)

#### 5.1 配置接收

```python
def update_full_config(self, config: Dict) -> None:
    """Update configuration (legacy compat - currently no-op)"""
    self.config = config
    # V8.8 doesn't use config yet, but we accept it for compatibility
    pass
```

#### 5.2 配置传递到 DomainProcessor

```python
# V16.0: Pass particle weights and physics config from config
particle_weights = self.config.get('particleWeights', {}) if hasattr(self, 'config') else {}
physics_config = self.config.get('physics', {}) if hasattr(self, 'config') else {}
domain_ctx = {
    'raw_energy': raw_energy,
    'dm_element': dm_elem,
    'strength': {
         'verdict': strength,
         'raw_score': score
    },
    'gender': case_data.get('gender', 1),
    'particle_weights': particle_weights,  # V16.0: Pass particle weights
    'physics_config': physics_config  # V16.0: Pass physics config (amplifiers, exponents)
}
domain_res = self.domains.process(domain_ctx)
```

---

## 架构约束与改进方向

### 当前架构问题

1. **Engine 层职责边界模糊**
   - `EngineV88.update_full_config()` 让 Engine 承担了配置存储职责
   - 违反了单一职责原则 (SRP)
   - **理想情况**: 配置管理应完全由 `BaziController` 负责，Engine 只在调用时接收和使用配置

2. **配置传递链路较长**
   - Controller → Engine → DomainProcessor
   - 增加了维护复杂度

### 未来改进方向

1. **配置管理器 (ConfigManager)**
   - 创建独立的配置管理模块
   - 统一管理所有配置的读写
   - 提供配置变更通知机制

2. **配置验证**
   - 添加配置参数验证逻辑
   - 确保参数值在合理范围内

3. **配置版本管理**
   - 支持配置版本历史
   - 支持配置回滚

---

## 使用指南

### 1. Cursor 自动化调优

**步骤**:
1. 修改 `config/parameters.json` 中的参数值
2. 用户刷新 P2 UI，滑块自动同步
3. 运行批量校准脚本验证效果

**示例**:
```json
{
  "particleWeights": {
    "PianCai": 1.50,  // 修改此值
    "ZhengCai": 1.30
  }
}
```

### 2. UI 交互调优

**步骤**:
1. 在 P2 侧栏拖动滑块调整粒子权重
2. 点击"💾 保存粒子权重到配置"按钮
3. 配置自动保存到 `config/parameters.json`
4. UI 自动刷新，显示新值

### 3. 批量校准验证

**步骤**:
1. 确保 `config/parameters.json` 包含最新参数
2. 运行 `scripts/run_batch_calibration.py`
3. 脚本自动读取配置文件并应用参数
4. 查看 MAE 结果验证调优效果

---

## 测试验证

### 验证点

1. **配置文件加载**
   - ✅ Controller 初始化时正确加载配置
   - ✅ 批量脚本启动时正确加载配置

2. **UI 同步**
   - ✅ P2 侧栏滑块显示配置文件中的值
   - ✅ 修改配置文件后，刷新 UI 滑块自动更新

3. **配置保存**
   - ✅ UI 保存按钮正确写回配置文件
   - ✅ 保存后 UI 自动刷新

4. **参数应用**
   - ✅ Engine 正确接收并应用粒子权重
   - ✅ DomainProcessor 正确应用放大参数

---

## 相关文件

### 核心文件

- `config/parameters.json` - 配置文件（单源数据）
- `controllers/bazi_controller.py` - Controller 层实现
- `ui/pages/quantum_lab.py` - P2 UI 实现
- `scripts/run_batch_calibration.py` - 批量校准脚本
- `core/engine_v88.py` - Engine 层实现
- `core/processors/domains.py` - DomainProcessor 实现

### 依赖文件

- `core/config_schema.py` - 默认配置结构
- `utils/constants_manager.py` - 常量定义

---

## 版本历史

- **V16.0** (2024): 初始实现
  - 实现配置文件加载/保存机制
  - 实现 UI 滑块同步
  - 实现批量脚本配置读取
  - 实现非线性放大参数支持

---

## 维护者

- **开发**: Cursor AI Assistant
- **审核**: Master (User)

---

## 附录

### A. 配置参数说明

#### particleWeights
- **范围**: 0.5 - 1.5 (对应 UI 滑块 50-150)
- **默认值**: 1.0
- **说明**: 十神粒子权重，影响领域得分计算

#### physics.WealthAmplifier
- **范围**: 0.8 - 2.0
- **默认值**: 1.0
- **说明**: 财富得分基础放大系数

#### physics.NonLinearExponent
- **范围**: 1.0 - 2.0
- **默认值**: 1.0
- **说明**: 非线性指数，用于高能量案例的指数级放大

### B. 故障排查

#### 问题: UI 滑块未同步到配置文件值

**检查**:
1. 确认 `config/parameters.json` 文件存在且格式正确
2. 检查 Controller 日志，确认配置加载成功
3. 检查 UI 代码中 `get_current_particle_weights()` 调用

#### 问题: 批量脚本未应用配置

**检查**:
1. 确认脚本正确读取配置文件路径
2. 检查脚本输出日志，确认配置加载信息
3. 验证 `params` 字典中是否包含配置值

---

**文档结束**

