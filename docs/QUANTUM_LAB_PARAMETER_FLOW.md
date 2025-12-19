# 量子验证页面参数传递流程

## 📊 参数传递流程图

```
侧边栏UI参数
    ↓
session_state (临时存储)
    ↓
点击"应用并回测"按钮
    ↓
构建 final_full_config
    ↓
存入 session_state['full_algo_config']
    ↓
Controller.update_config(config_updates)
    ↓
深度合并到 self._config
    ↓
重新初始化 Engine: GraphNetworkEngine(config=self._config)
    ↓
Engine使用新配置进行计算
```

## 🔄 参数同步机制

### 1. 参数来源

**初始化时**：
- Controller从 `config/parameters.json` 加载配置（通过 `ConfigModel.load_config()`）
- 如果配置文件不存在，使用默认配置（`DEFAULT_FULL_ALGO_PARAMS`）

**运行时**：
- 侧边栏参数通过 `st.slider()` 等控件收集
- 参数值存储在 `st.session_state` 中（如 `st.session_state['strength_energy_threshold']`）

### 2. 参数应用流程

**步骤1：用户调整侧边栏参数**
```python
energy_threshold_center = st.slider(
    "能量阈值中心点",
    value=strength_config.get('energy_threshold_center', 2.89),
    key='strength_energy_threshold'  # 存入session_state
)
```

**步骤2：点击"应用并回测"按钮**
```python
if st.sidebar.button("🔄 应用并回测"):
    # 从session_state读取参数
    energy_threshold_center = st.session_state.get('strength_energy_threshold', ...)
    
    # 构建完整配置
    final_full_config = {
        "strength": {
            "energy_threshold_center": energy_threshold_center,
            ...
        }
    }
    
    # 存入session_state
    st.session_state['full_algo_config'] = final_full_config
```

**步骤3：Controller应用配置**
```python
# 在render()函数中
if 'full_algo_config' in st.session_state:
    quantum_controller.update_config(st.session_state['full_algo_config'])
```

**步骤4：Engine重新初始化**
```python
# 在Controller.update_config()中
self._merge_config(self._config, config_updates)
if self._engine is not None:
    self._engine = GraphNetworkEngine(config=self._config)  # 重新初始化
```

### 3. 参数持久化

**保存到配置文件**（可选）：
```python
if st.session_state.get('save_as_golden_params', False):
    config_model.save_config(final_full_config, merge=True)
    # 保存到 config/parameters.json
```

**下次启动时自动加载**：
```python
# Controller初始化时
self._config = self.config_model.load_config()  # 从config/parameters.json加载
```

## ⚠️ 当前问题

### 问题1：参数不是实时生效
- **现状**：必须点击"应用并回测"按钮，参数才会生效
- **原因**：参数只在点击按钮后才传递给Controller
- **影响**：用户调整参数后，需要手动点击按钮才能看到效果

### 问题2：参数可能不同步
- **现状**：侧边栏显示的参数值可能和Engine实际使用的配置不一致
- **原因**：
  1. 如果用户调整了参数但没有点击"应用"按钮，Engine仍使用旧配置
  2. 如果配置文件被外部修改，侧边栏不会自动刷新

### 问题3：参数来源不明确
- **现状**：参数可能来自：
  1. 侧边栏UI（session_state）
  2. 配置文件（config/parameters.json）
  3. 默认值（DEFAULT_FULL_ALGO_PARAMS）
- **优先级**：不明确，可能导致混淆

## ✅ 建议改进

### 改进1：实时参数同步
- 使用 `st.session_state` 的 `on_change` 回调
- 参数变化时自动调用 `Controller.update_config()`

### 改进2：参数状态显示
- 在侧边栏显示"当前生效的参数值"
- 区分"UI显示值"和"Engine实际使用值"

### 改进3：参数来源标识
- 明确标注参数来源（UI调整 / 配置文件 / 默认值）
- 提供"重置为配置文件值"按钮

