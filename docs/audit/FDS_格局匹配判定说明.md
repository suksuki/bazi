# FDS：八字 + 格局 + 大运 / 流年 / 地域 — 「匹配上了」怎么判定？

## 一、输入

- **八字**：四柱 + 日主（chart + day_master）
- **某格局**：pattern_id（如 A-01）
- **大运**：当前大运干支（如 己卯）
- **流年**：观测年份对应的流年干支（如 庚子）
- **地域**：地理场（如 城市/南北方，用于地理阻尼与偏移）

## 二、当前管线（两套用法）

### 用法 1：问「这个八字在此时空下，最像哪个格局？」（不指定格局）

1. **原局 5D**  
   用八字的混合格局加权得到一点：  
   `point_5d = get_mixed_pattern_context(chart, day_master)["point_5d"]`  
   （不针对某一格局，是 60 格局概率加权的综合点。）

2. **动态 5D（加大运 / 流年 / 地域）**  
   `dynamic_point = compute_dynamic_tensor(natal_5d, major_pillar, annual_pillar, geo_region, month_branch, day_master)["dynamic_point"]`  
   - 大运/流年通过 `stem_branch_interactions`（刑冲合化）和 `time.weight_*` 参与位移；  
   - 地域通过 `geo_damping`、`geo_5d_offset` 参与。

3. **流形追踪**  
   `compute_dm_cloud(dynamic_point, top_k=3)`  
   - 得到该点到 60 个质心的欧氏距离 D_M；  
   - 返回前 3 个格局的叠加态（overlay）。

4. **「匹配」的语义**  
   - **最近即视为当前归属**：overlay[0].pattern_id 就是「当前匹配到的格局」。  
   - 若要再细化为「匹配上了 / 没匹配上」，需要在此基础上加阈值（见下）。

### 用法 2：问「这个八字 + 大运 / 流年 / 地域，是否匹配『某指定格局』？」（全息页做法）

1. **指定格局下的 5D 投影（已含大运/流年/地域）**  
   `projection = calculate_tensor_projection(pattern_id, chart, day_master, context)`  
   其中 `context = { luck_pillar, annual_pillar, geo_city }`，格局引擎内部会把大运/流年/地域用在该格局的投影上。

2. **和 60 个质心比较**  
   `trace = compute_dm_cloud(projection, top_k=3)`  
   - 得到该 5D 点到每个格局质心的 D_M；  
   - overlay 为距离最近的 3 个格局。

3. **当前实现里的「匹配上了」**  
   - **捕获格局** = overlay[0].pattern_id（最近的一个）。  
   - 若 **capture_id == 当前选的 pattern_id**，即：**该格局是「流形捕获」的最近格局** → 在页面上就视为「匹配上了」该格局。  
   - 同时会展示：D_M、匹配度 100/(1+D_M)、SAI、识别态等，但没有在代码里再和某一阈值做布尔判定。

## 三、SOP V6.5：引力俘获模型（R-Limit 与四级判定）

总审计师核定：不能仅因「最近」就判定被俘获；若距离过远，样本处于**星际流浪**。系统采用 **D_crit（临界距离）** 的**准入主权**判定。

### 3.1 核心判定公式：引力半径 (R-Limit)

- **格成（Pattern Verified）**：仅当 **$D_M \le D_{crit}$** 且该格局为 **Top 1** 时，UI 打出「格成」标记。  
- **物理语义**：样本进入该格局的**事件视界**，才视为被该质心俘获。

### 3.2 四级格局判定（可配置阈值）

阈值在 `config/dynamic_manifold.json` → `manifold_capture` 中配置，零硬编码：

| 匹配等级 | 判定条件 ($D_M$) | 匹配度 (Affinity) | 审计判语 |
| --- | --- | --- | --- |
| **纯粹 (PURE)** | $D_M \le 0.5$ | $\ge 66\%$ | 格局清纯，能量高度聚焦。 |
| **合规 (VERIFIED)** | $D_M \le 1.2$ | $\ge 45\%$ | 格局成立，具备该系物理特征。 |
| **漂移 (DRIFTING)** | $1.2 < D_M \le 2.5$ | $28\% \sim 45\%$ | 格局不稳，受杂气或流年干扰。 |
| **破格 (BROKEN)** | $D_M > 2.5$ | $< 28\%$ | **格局坍缩**，已脱离该质心引力井。 |

- **实现**：`core/manifold_trace.py` 的 `compute_dm_cloud` 在返回的 `overlay[]` 中为每项增加 `status`（PURE/VERIFIED/DRIFTING/BROKEN）与 `verdict`（上表判语）；并增加顶层 `capture_status`、`capture_verdict`（对应 Top 1 的主权状态）。

### 3.3 联动动态流年（大运/流年/地域）

- **时空位移导致主权丧失**：原局可能为 VERIFIED（如 $D_M=0.8$），大运/流年注入后动态 5D 位移，$D_M$ 变为 2.8 → 状态变为 **BROKEN**。  
- **动作**：UI 显示 `Status: BROKEN`，并触发既有 **CRITICAL_STRUCTURE_COLLAPSE** 红色闪烁与应灾判词。  
- 全息页在切换流年时，用**当前 5D 点**（含大运/流年/地域）做 `compute_dm_cloud`，故匹配度与 status 会随流年变化；进度条颜色由绿→黄→红，BROKEN 时断开连接并变红。

### 3.4 地域修正（引力补偿，可选）

- 若地域处于该格局五行所属方位（如某格属木火、地域在南方），可在计算 $D_M$ 时对该格局质心施加**引力补偿**（等效缩小 $D_M$）。  
- 当前实现预留扩展点：`config/dynamic_manifold.json` 可增加 `geo_gravity_compensation` 等配置，由调用方或后续迭代接入。

## 四、相关代码位置

- **动态 5D（大运/流年/地域）**：`core/physics/dynamic_engine.py` — `compute_dynamic_tensor`
- **流形距离与叠加态**：`core/manifold_trace.py` — `compute_dm_cloud`（D_M、overlay）
- **指定格局的投影（含 context）**：`controllers/holographic_pattern_controller.py` — `calculate_tensor_projection`
- **全息页「捕获格局」展示**：`ui/pages/holographic_pattern.py` — 用 overlay[0] 为 capture_id，与 selected_pattern_id 比较即等价「是否匹配该格局」
- **匹配度公式**：`100/(1+D_M)`，D_M 为该 5D 点到该格局质心的欧氏距离（E,O,M,S,R 五维）

## 五、小结

- **SOP V6.5 后**：采用**引力俘获模型**。格成仅当 $D_M \le D_{crit}$（VERIFIED 或 PURE）且该格局为 Top 1；否则按 D_M 落入 PURE/VERIFIED/DRIFTING/BROKEN 四级之一，并返回对应 `status` 与 `verdict`。  
- **全息页**：展示 `capture_status`，颜色绿（PURE/VERIFIED）→ 黄（DRIFTING）→ 红（BROKEN）；BROKEN 时视为断开连接并触发坍缩预警。
