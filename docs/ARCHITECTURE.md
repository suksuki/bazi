# 架构总览（V14.0）

## 分层模型
- **View（P1/P2/P3）**：Streamlit 页面与 `unified_input_panel`，负责输入与可视化。
- **Facade（BaziFacade）**：统一高阶 API；封装情景模拟、最优路径、自动校准应用。
- **Controller（BaziController）**：状态管理、缓存、GEO/ERA/粒子权重注入、LLM 调用、健康校准触发。
- **Services**：`CalibrationService`（健康检查与推荐）、`NotificationManager`、`ConfigurationManager`/`ConstantsManager`。
- **Engine 层**：`FluxEngine`/`QuantumEngine` 核心计算，Physics/Processors 等。

## 数据流
1) 用户侧边栏输入 → `unified_input_panel` 收集档案/GEO/ERA/粒子权重  
2) 输入传入 `BaziFacade.process_and_set_inputs()` → 调用 Controller `set_user_input`  
3) Controller 加载/刷新：排盘、FluxEngine/QuantumEngine、缓存失效、校准检查  
4) View 通过 Facade 获取核心分析/情景结果并渲染；通知中心显示错误/警告  

## 修正因子（GEO / ERA / Particle）
- **存储位置**：Controller `_user_input`，并同步传递给 `FluxEngine`/`QuantumEngine`。
- **显示**：P1/P3 侧边栏透明展示；P2 支持调优滑块；Facade `get_core_analysis` 返回当前生效因子。
- **自动校准**：`CalibrationService` 生成推荐；Facade `apply_auto_calibration` 一键应用。

## 自动化与容错
- **健康检查**：`CalibrationService.run_health_check` 检测五行失衡；警告经 `NotificationManager` 呈现。
- **缓存策略**：Controller 基于输入/时间线参数生成 MD5 key，输入变更触发 `_invalidate_cache`。
- **配置加载**：`ConfigurationManager` 支持 `.env`/环境变量；`ConstantsManager` 统一五行、十神、默认权重与 GEO 城市。

## 关键接口（对 View）
- `BaziFacade.get_core_analysis()`：返回排盘、五行能量、旺衰、当前修正因子、健康报告/推荐。
- `BaziFacade.run_predictive_scenario()`：时间线 + LLM 分析一体化。
- `BaziFacade.find_optimal_adjustment()`：目标提升的反向优化。
- `BaziFacade.apply_auto_calibration()`：应用推荐的 ERA/粒子权重并刷新。

