# 第 038 号工程指令：UI 流形可视化与时空扰动增强 (A 计划)

**状态**: 已实现  
**SOP 依据**: FDS SOP V5.0；B → A → C 航线之 A 计划

---

## 目标

将物理对撞与语义判词转化为用户可感知的**视觉流形**：动态五维雷达图、流年/大运位移轨迹、地域修正与「坐标-轨迹-策略」视线链。

---

## 任务 1：动态五维对撞雷达图 ✅

**位置**: 测算页 → 展开「🔀 全息格局对撞 · 流形可视化与混合判词」

**实现**:
- **基准层**：命主当前混合 5D 点（`point_5d`）+ 地域修正，紫色实线。
- **背景层**：命中概率最高格局的「标准流形区域」μ±σ，从 `core/manifold_visual_utils.get_manifold_band_for_pattern(pattern_id)` 获取（registry 或 npz），半透明填充。
- **流年层**：`calculate_temporal_displacement` 得到的位移后点，虚线；若任一方位进入极值区（\|r\| ≥ 1.2），轨迹显示为橙色并标注「⚠ 极值区」。
- **交互**：Plotly 雷达图悬停显示该轴数值；轴标签为「E · 能量 E」等（含义见 `AXIS_LABELS_5D` / `get_axis_hover_text`）。

**依赖**: `core/manifold_visual_utils.py`（`get_manifold_band_for_pattern`、`get_axis_hover_text`）。

---

## 任务 2：流年/大运位移线 ✅

**物理计算**: `core/dynamic_engine.calculate_temporal_displacement(base_point, luck_pillar, year_pillar)`  
- 内部调用 `get_time_delta(luck_pillar, year_pillar)`，将大运+流年干支转化为 5D 增量 ΔV_time，叠加到 `base_point`。  
- 返回 `base_point`、`displaced_point`、`delta_vector`。

**可视化**: 雷达图中「命主（含地域）」与「流年/大运后」两条轨迹；位移指向极值区时箭头色为橙/紫（通过「流年/大运后」trace 的 color 与 name 后缀「⚠ 极值区」体现）。

---

## 任务 3：地域修正下拉框 ✅

**配置**: `config/physics/geographic_factors.json`  
- 结构：`regions`: { "中原", "东方", "南方", "西方", "北方", "东南", "东北", "西南", "西北" } → 各轴 E/O/M/S/R 偏移量。  
- 测算页通过 `_get_region_offset_5d(direction)` 读取；`direction` 与主区「地理方位」及侧栏「地域（5D 修正）」共用 `st.session_state["dynamic_geo_direction"]`（中/东/南/西/北/东南/东北/西南/西北），映射到上述 region 键。

**前端**:
- 侧栏：`ui/sidebar.py` 中增加「地域（5D 修正）」下拉，key=`dynamic_geo_direction`。  
- 主区：原有「地理方位」下拉保留，与侧栏同 key，实时同步。  
- 切换地域后，雷达图与判词使用的 `point_5d` 为混合点 + `_get_region_offset_5d(geo_direction)`，无刷新更新。

---

## 任务 4：UI 布局优化 ✅

- 「铁嘴神算」混合格局判词与「流形修复建议」置于雷达图**右侧**（`col_verdict`），与左侧雷达图（`col_radar`）形成「坐标-轨迹-策略」视线链。  
- 同一 expander 内：左图右文，判词按钮与修复说明均在右侧列。

---

## 依赖与配置

- **地域配置**: `config/physics/geographic_factors.json`（regions → 5D 偏移）。  
- **时间/地理权重**: 仍由 `config/dynamic_evolution.json` 的 `time`、`geo_direction` 参与 `get_time_delta` / `get_geo_factor`（地域优先用 geographic_factors）。  
- **流形带**: A-01 等格局的 μ/σ 来自 registry 的 `feature_anchors.standard_manifold` 或 benchmarks，或 `data_local/{id}_full_points.npz`。

---

## 验收要点

1. 雷达图展示三层：格局 μ±σ 背景、命主+地域、流年/大运后；极值区轨迹为橙色并带提示。  
2. 侧栏或主区切换地域后，雷达与混合 5D 数值即时更新。  
3. `calculate_temporal_displacement` 返回位移矢量，与动态引擎现有 `get_time_delta` 一致。  
4. 判词与修复在雷达图右侧，形成完整视线链。
