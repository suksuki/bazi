# 引擎架构说明 (Engine Architecture)

## 📋 当前引擎文件列表

### 1. **核心引擎** (统一架构)

#### `core/engine_v88.py` - **V9.1 统一引擎** ⭐ **当前主引擎**
- **状态**: ✅ **当前生产环境使用**
- **版本**: V9.1.0-Spacetime (统一了 V8.8 和 V9.1 的功能)
- **功能**: 
  - 模块化架构，包含 Physics、Seasonal、PhaseChange、Judge 处理器
  - GeoProcessor (地理修正 - Layer 0)
  - Era-Aware Physics (时代感知物理 - Layer 1)
  - Spacetime Event Detection (时空事件检测)
- **子引擎**: LuckEngine, TreasuryEngine, SkullEngine, HarmonyEngine
- **使用位置**:
  - `controllers/bazi_controller.py` (作为 QuantumEngine 别名)
  - `ui/pages/prediction_dashboard.py` (作为 QuantumEngine 别名)
  - `ui/pages/quantum_lab.py` (作为 QuantumEngine 别名)
  - `ui/pages/zeitgeist.py`
  - `scripts/auto_tuner.py`
  - `scripts/performance_profiler.py`

#### `core/engine_v90.py` - **V9.0 天地引擎** ❌ **已删除**
- **状态**: ❌ **已删除** (2024-12-19)
- **原因**: 功能已被统一引擎替代
- **迁移**: 相关测试已更新为使用 EngineV88

#### `core/engine_v91.py` - **V9.1 时空融合引擎** ❌ **已删除**
- **状态**: ❌ **已删除** (2024-12-19)
- **原因**: 功能已合并到 EngineV88
- **迁移**: 所有引用已更新为使用 EngineV88

### 2. **图网络引擎** (独立架构)

#### `core/engine_graph.py` - **GraphNetworkEngine (V10.0)**
- **状态**: ✅ 用于批量验证和训练
- **架构**: 图神经网络模型
- **用途**: 
  - `scripts/batch_verify.py`
  - `scripts/train_model_optuna.py`
  - `scripts/auto_evolve.py`
- **特点**: 使用图结构进行能量传播计算

#### `core/engine_adapter.py` - **GraphEngineAdapter**
- **状态**: ✅ 适配器模式
- **功能**: 将 GraphNetworkEngine 输出转换为 EngineV91 兼容格式
- **用途**: 测试和验证场景

### 3. **废弃引擎** (Legacy)

#### `core/quantum_engine.py` - **QuantumEngine (V8.1 Legacy)**
- **状态**: ⚠️ **已废弃 (DEPRECATED)**
- **版本**: V8.1
- **警告**: 代码中有明确的废弃警告
- **迁移指南**: 使用 `EngineV88` 替代
- **保留原因**: 向后兼容性（测试和旧脚本）

#### `core/quantum.py` - **QuantumSimulator (V16.0)** ⚠️ **已重命名**
- **状态**: ✅ 用于量子模拟和可视化
- **功能**: 量子波函数坍缩模拟、Monte Carlo 采样
- **用途**: 
  - 轨迹模拟 (`core/trajectory.py`)
  - 3D 场可视化 (`ui/modules/viz_3d_field.py`)
  - 测试和验证
- **重命名**: `QuantumEngine` → `QuantumSimulator` (避免与主引擎混淆)

---

## 🔄 当前使用情况

### 生产环境 (Production)
- **主引擎**: `EngineV88` (V9.1 统一版本，通过 `QuantumEngine` 别名)
- **控制器**: `BaziController` 统一管理
- **配置加载**: 从 `config/parameters.json` 加载黄金参数

### 训练/验证环境 (Training/Validation)
- **主引擎**: `GraphNetworkEngine`
- **用途**: Optuna 超参数优化、批量验证

---

## ⚠️ 架构问题

### 1. **命名混乱**
- `QuantumEngine` 被用作 `EngineV91` 的别名，但实际存在多个 `QuantumEngine` 类
- 容易造成混淆

### 2. **版本重叠** ✅ **已解决**
- ~~`EngineV90` 和 `EngineV91` 功能相似但实现不同~~ → 已删除 EngineV90
- ~~V90 使用 `EraProcessor`，V91 使用 Era 常量 JSON~~ → 已统一到 EngineV88

### 3. **废弃代码**
- `quantum_engine.py` 已废弃但仍保留（向后兼容）
- `quantum.py` 中的 `QuantumEngine` 已重命名为 `QuantumSimulator` ✅

---

## 💡 建议的清理方案

### 方案 A: 统一命名 ✅ **已完成**
1. ✅ **统一**: `EngineV88` 合并了 V8.8 和 V9.1 的所有功能，成为唯一主引擎
2. ✅ **删除**: `EngineV90` (功能已被统一引擎替代)
3. ✅ **删除**: `EngineV91` (功能已合并到 EngineV88)
4. ✅ **重命名**: `quantum.py` 中的 `QuantumEngine` → `QuantumSimulator`
5. ⚠️ **标记**: `quantum_engine.py` 已有废弃标记（保留用于向后兼容）

### 方案 B: 文档化
1. 保持现状
2. 在代码中添加清晰的注释说明各引擎用途
3. 在 README 中说明架构关系

---

## 📝 当前配置同步状态

✅ **已完成**:
- `BaziController` 从 `config/parameters.json` 加载完整配置
- `EngineV88.update_full_config()` 正确传递配置到子引擎
- 智能排盘页面和量子验证页面使用相同配置源

---

**最后更新**: 2024-12-19
**维护者**: AI Assistant

---

## ✅ 清理完成记录 (2024-12-19)

### 已完成的清理工作：

#### 第一阶段：删除 EngineV90 和重命名 QuantumSimulator
1. ✅ **删除 EngineV90**: 
   - 删除 `core/engine_v90.py`
   - 更新 `tests/test_v9_era_transition.py` 使用 EngineV88
   - 更新 `tests/test_v9_geo_algorithm.py` 使用 EngineV88
   - 更新 `tests/test_v9_geo_contrast.py` 使用 EngineV88

2. ✅ **重命名 QuantumEngine → QuantumSimulator**:
   - 重命名 `core/quantum.py` 中的 `QuantumEngine` 类为 `QuantumSimulator`
   - 更新所有引用文件

#### 第二阶段：合并 EngineV88 和 EngineV91
3. ✅ **合并引擎功能**:
   - 将 EngineV91 的所有功能合并到 EngineV88
   - 更新版本号为 V9.1.0-Spacetime
   - 添加 GeoProcessor 支持
   - 添加 Era-Aware Physics 支持
   - 添加 Spacetime Event Detection
   - 更新 `analyze()` 方法支持 city, latitude, era_multipliers 参数
   - 更新 `_build_response()` 方法支持 modifiers 参数
   - 更新 `calculate_energy()` 方法包含完整 V9.1 功能
   - 添加 `_check_spacetime_events()` 方法

4. ✅ **更新所有引用**:
   - `controllers/bazi_controller.py`
   - `ui/pages/prediction_dashboard.py`
   - `ui/pages/quantum_lab.py`
   - `ui/pages/zeitgeist.py`
   - `scripts/auto_tuner.py`
   - `scripts/performance_profiler.py`

5. ✅ **删除 EngineV91**:
   - 删除 `core/engine_v91.py`

6. ✅ **统一命名规范**:
   - 主引擎: `EngineV88` (V9.1 统一版本，通过 `QuantumEngine` 别名使用)
   - 量子模拟器: `QuantumSimulator` (用于波函数模拟)
   - 图网络引擎: `GraphNetworkEngine` (用于训练/验证)

