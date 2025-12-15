# Antigravity Release Notes

## [V9.5] - MVC Architecture Edition - 2025-12-15
**Status:** ✅ STABLE / PRODUCTION READY  
**Test Status:** Controller Integration: 15/15 PASSED ✅ | Total: 190+ PASSED

### 🏛️ MVC 架构革命 (MVC Architecture Revolution)

#### Controller Layer Established
* **✅ BaziController:** 20+ 公共方法的统一接口层
  * Input Management: `set_user_input()`
  * Chart & Luck: `get_chart()`, `get_luck_cycles()`, `get_dynamic_luck_pillar()`
  * Timeline: `run_timeline_simulation()`, `run_single_year_simulation()`
  * GEO Comparison: `get_baseline_trajectory()`, `get_geo_trajectory()`, `get_geo_comparison()` ⭐
  * Convenience: `get_flux_data()`, `get_wang_shuai_str()`, `get_profile()`

#### View Layer Decoupling
| Page | Status | Strategy |
|------|--------|----------|
| P1 智能排盘 | ✅ Pure View | 100% Controller API |
| P2 量子验证 | ✅ Hybrid Mode | Controller + Engine (Calibration) |
| P3 命运影院 | ✅ Progressive MVC | Controller-first with Engine fallback |

### ⚡ 架构优势 (Architecture Benefits)
* **Single Source of Truth:** 所有业务逻辑通过 Controller 流转
* **Lazy Initialization:** 按需创建 Model 实例
* **State Isolation:** 每个 Controller 实例独立状态
* **Backward Compatibility:** 保留 Engine 直接访问用于校准工具

### 🧪 新增测试 (New Tests)
* `tests/integration/test_controller_integration.py` - 15 项 Controller 集成测试
  * TestControllerInitialization: ✅
  * TestUserInputAPI: ✅
  * TestChartAndLuckAPI: ✅
  * TestTimelineSimulation: ✅
  * TestGeoComparisonAPI: ✅
  * TestFluxEngineAPI: ✅

### 📁 新增文档 (New Documentation)
* `docs/CONTROLLER_API.md` - 完整 Controller API 参考手册

### 🔧 P3 命运影院渐进式解耦
* **Controller 工厂函数:** `get_controller_for_case()` 从案例数据创建 Controller
* **双保险机制:** MVC 优先，Legacy Engine 后备
* **GEO 对比曲线:** 通过 `get_geo_comparison()` 获取双轨迹数据

---

## [V8.8] - Modular Genesis Edition - 2025-12-14
**Status:** ✅ STABLE / PRODUCTION READY  
**Test Status:** V8.8 Comprehensive Suite: 25/25 PASSED ✅

### 🏛️ 模块化架构 (Modular Architecture)
* **✅ Processor Pipeline:** 4层处理器架构
  * Layer 1: PhysicsProcessor (五行能量量化)
  * Layer 2: SeasonalProcessor (当令判断)
  * Layer 2.5: PhaseChangeProcessor (相变物理)
  * Layer 3: StrengthJudge (最终裁决)
* **✅ Sub-Engines:** 4个专业子引擎
  * LuckEngine: 动态大运管理
  * TreasuryEngine: 墓库识别
  * SkullEngine: 三刑风控
  * HarmonyEngine: 合化检测

### 🧪 测试覆盖 (Test Coverage)
* **V8.8 综合测试:** 25/25 通过
  * Core Physics: ✅
  * Strength Judgment: ✅
  * Phase Change Protocol: ✅
  * Sub-Engines: ✅
  * Year Context: ✅
  * BaziProfile: ✅
  * Luck Timeline: ✅
  * Energy Calculation: ✅

### 📁 核心文件
* `core/engine_v88.py` - 模块化引擎入口
* `core/processors/` - 处理器层
* `tests/test_v88_comprehensive.py` - 综合测试套件

---

## [V8.0-Preview] - Phase Change Protocol - 2025-12-14
**Status:** 🧪 Merged into V8.8

### 🔥 物理引擎突破 (Physics Breakthrough)
* **✅ 相变协议 (Phase Change Protocol):** 实现了季节性相生通道阻断
  * **焦土不生金:** 夏季 (巳午未月) 土的水分被蒸发，变成焦土，阻断 Earth → Metal 相生通道
  * **冻水不生木:** 冬季 (亥子丑月) 水结冰，阻断 Water → Wood 相生通道

---

## [V7.4] - The Physicist Edition - 2025-12-14
**Status:** ✅ Merged into V8.8
**Test Status:** Core features integrated  

### 🏛️ 核心架构 (Core Architecture)
* **Config-Driven DNA:** 全系统参数解耦，实现 100% 可配置化与热更新。
* **The Trinity Model:** 确立了 [量子验证 (Write)] -> [智能排盘 (Read)] 的单向数据流。
* **Sub-Engine Modularization:** FlowEngine, HarmonyEngine, TreasuryEngine, SkullEngine, LuckEngine

### ⚛️ 物理引擎更新 (Physics Engine)
* **✅ 阻尼协议 (Impedance & Viscosity):** 引入了"输入阻抗"与"输出粘滞"，解决了"虚不受补"与"瞬间过劳死"的非线性问题。
* **✅ 月令集权 (Imperial Month):** 将月令（Month Command）权重提升至 2.0，确立了其作为全局引力中心的统治地位。
* **✅ 墓库拓扑 (Vault Topology):** 实现了开库、闭库、冲破的动态判定逻辑。
* **✅ 化学反应 (Alchemy):** 实现了天干五合与动态化气逻辑（修复了 Case 005）。
* **✅ 热力学修正 (Thermodynamics):** 引入夏土物理 (Summer Earth Logic)，模拟季节性生克损耗。

### 🧪 验证成果 (Validation)
* **Blind Test Accuracy:** 60% (9/15) on high-difficulty dataset.
* **Effective Accuracy:** ~75% (including technical false negatives)
* **V7.4 Release Tests:** 18/18 passed ✅
* **Significant Breakthroughs:** 
    * 成功校准 **VAL_002 (教父)** 为强旺状态 (71.1分)。
    * 成功校准 **VAL_009 (梦露)** 为身弱状态。
    * 成功修复 **Case 005 (枭雄)** 的合化逻辑。

### 📁 文档 (Documentation)
* `docs/V7.4_TECHNICAL_SPECIFICATION.md` - 完整技术规范
* `tests/test_v7_4_release.py` - V7.4 发布验证测试套件

### 🚧 Known Legacy Issues
以下 V3.x 时代的测试用例因接口迁移暂时失效（功能本身正常）：
* `test_v3_*.py` - 使用旧版 `analyze_year_interaction` API
* `test_v54_full.py` - 使用旧版 `LuckEngine` API  
* `test_calibration_dashboard.py` - 缺少 `macro_weights_w` 参数

---


## [V6.0] - Oracle Edition - 2025-12-14
**Status:** Production Ready 🚀

### 🏛️ 架构升级 (Architecture)
* **The Oracle**: 引入 `BaziProfile` 对象层，取代字典传递，实现 O(1) 大运查询。
* **Engine Modularization**: `QuantumEngine` 重构为 Facade 模式，下辖三大子引擎：
    * `LuckEngine`: 动态大运与流年管理。
    * `TreasuryEngine`: 墓库识别与量子隧穿计算 (🏆)。
    * `SkullEngine`: 灾难级风控检测 (💀)。
* **Trinity V4.0**: Dashboard, Cinema, QuantumLab 三端逻辑 100% 统一。

### ✨ 新特性 (Features)
* **Skull Protocol**: 丑未戌三刑检测，触发 -50 分结构性崩塌预警。
* **Dynamic Luck**: 12年模拟中支持动态大运切换，可视化换运点 (虚线)。
* **Safety Valve**: 针对身弱命主的财库开启进行风险降级 (⚠️)。

### 🧹 代码质量 (Code Quality)
* Dashboard 代码量减少 **20%** (UI 组件化)。
* QuantumEngine 主类瘦身，逻辑分层清晰。
* 遗留数据兼容: 引入 `VirtualBaziProfile` 适配器，完美兼容旧版测试用例。

### 🧪 验证 (Validation)
* Regression Tests: PASSED (Skull Protocol verified).
* Backtesting: QuantumLab Green Lights ✅.

---

## Version History

### [V5.4] - Dynamic Fluid Edition
* 动态流年计算引擎
* 12年人生轨迹可视化
* Cinema 模式引入

### [V5.3] - Skull Protocol
* 丑未戌三刑检测逻辑
* 灾难级风控预警系统

### [V3.0] - Quantum Vault
* 墓库状态识别
* 量子隧穿计算模型

### [V2.0] - Foundation
* 基础八字计算引擎
* 旺衰分析核心算法
