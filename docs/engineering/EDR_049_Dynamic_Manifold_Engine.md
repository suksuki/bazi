# 第 049/050 号工程指令：动态时空位移引擎 (Dynamic Manifold Engine)

**状态**: 架构设计 + SOP V5.6 合拢（引透、地理阻尼λ、刑冲合化、格局对撞态）  
**法理依据**: 原局为格，动变为局；能量改变空间位置，非二选一。

---

## 一、计算模型：张量位移 (Tensor Displacement)

- **原局**：静态 5D 坐标 $\mathbf{P}_{natal}$（E, O, M, S, R）。
- **大运 / 流年**：不做简单能量加减，而是通过**干支交互**（合化、冲刑、引透）改变十神权重，产生**引力场**，使原局坐标发生**实时位移**。
- **结果**：$\mathbf{P}_{dynamic} = \mathbf{P}_{natal} + \Delta T_{time} + \Delta G_{geo}$。  
  - $\Delta T_{time}$：由大运柱、流年柱经**干支交互矩阵**得到 5D 位移向量。  
  - $\Delta G_{geo}$：环境参数 $\lambda$，地理方位对 5D 的微调（南方火旺→增 E/O 弱 R；北方水旺→增 R 弱 E）。

---

## 二、判定标准：流形捕获 (Manifold Capture)

- 不重新“命名”格局，而是计算位移后的点 $\mathbf{P}_{dynamic}$ 被**哪个格局质心**捕获。
- **格局转化**：若 $\mathbf{P}_{natal}$ 在 A-08（正印），流年引动伤官后位移到 A-07 吸引区，即古典「伤官破印」的物理描述。
- **实现**：计算 $\mathbf{P}_{dynamic}$ 与 DuckDB 中 A-01～A-13 各格局质心的距离（欧氏或马氏），取最近者为**当前捕获格局**。

---

## 三、地理位置：环境参数 $\lambda$

- 地理不改变格局法理名称，仅对 5D 施加**微调向量** $\Delta G$。
- 约定（由配置覆盖，零硬编码）：  
  - 南方（火旺）：增强 E、O，削弱 R。  
  - 北方（水旺）：增强 R，削弱 E。  
  - 东/西/中：由 `config/dynamic_manifold.json` 的 `geo_5d_offset` 定义。

---

## 四、时空引擎 I/O（SOP 升级预演）

| 阶段 | 输入 | 输出 |
|------|------|------|
| 动态张量注入 | Native_Data（原局 5D）、Major_Cycle（大运干支）、Annual_Year（流年干支）、Geo_Location | Dynamic_5D_Tensor |
| 实时距离审计 | Dynamic_5D_Tensor、DuckDB 质心 | 最近格局 pattern_id、$D_M$、可选各格距离 |
| 对撞预警 | Dynamic_5D_Tensor、阈值（如 S>1.8） | 是否进入高压区、应灾指引触发标志 |

---

## 五、实现位置与配置

- **引擎**：`core/physics/dynamic_engine.py`  
  - `compute_dynamic_tensor(natal_5d, major_pillar, annual_pillar, geo_region)` → 动态 5D。  
  - `manifold_capture(dynamic_5d)` → 最近格局、距离。  
  - `collision_warning(dynamic_5d, s_threshold)` → 是否高压区、建议调 RAG。  
- **配置**：`config/dynamic_manifold.json`  
  - **干支交互**：大运/流年对 5D 的贡献方式（权重或交互矩阵引用）。  
  - **地理 5D 偏移**：南/北/东/西/中等 $\Delta G$。  
- **参数**：所有权重、阈值、偏移均来自配置或 AlgoParams，禁止在代码中硬编码数值。

---

## 六、SOP V5.6 法理修正（审计师签收）

### 6.1 ΔT_time 引透优先级

- **要求**：流年干支若为原局月令本气之「透出」（同十神），该柱位移权重 **翻倍**（`tougan_scale`，配置默认 2.0）；**大运**干若透月令本气，同样翻倍（埋藏的欲望被时代唤醒）。
- **实现**：`compute_dynamic_tensor(..., month_branch=, day_master=)` 检测流年干/大运干十神是否等于月令本气十神；是则对应柱贡献乘以 `tougan_scale`，并置 `tougan_triggered=True`（流年）、`major_tougan_triggered=True`（大运）。RAG 判词红线：大运透月令时须给出「名利浮现，实操转虚」定性。

### 6.2 ΔG_geo 阻尼效应

- **要求**：地理为 **阻尼系数 λ**，公式为 ΔP = ΔT · λ_geo + geo_offset（非纯加法）。
- **实现**：`config` 中 `geo_damping` 按维度乘在 `time_delta` 上得 `time_delta_damped`，再与少量 `geo_offset` 相加。南方火旺 R 轴阻尼 < 1，北方水旺 R 轴 > 1。

### 6.3 流形捕获动态阈值与格局对撞态

- **要求**：当 $D_M$ 处于两格局质心「中点」附近（双重捕获）时，标记 **格局对撞态**；`collision_warning` 除 S 轴外须识别该态，RAG 输出「决策摇摆/多重人格冲突」类判词。
- **实现**：`manifold_capture` 返回 `second_pattern_id`、`is_double_capture`（当 次近距离/最近距离 ≤ `double_capture_ratio_threshold`）。`collision_warning(..., manifold_result=)` 接收后置 `collision_type="manifold_instability"`，并返回 `source_pattern`、`target_pattern`、`collision_type` 供 RAG 检索。

### 6.4 干支刑冲合化与流形位移矢量

- **配置**：`stem_branch_interactions` 列表，每项 `{"interaction": "子午冲", "delta": { E,O,M,S,R }}`；**六合、六冲、三合、三会**两两组合已全量录入（六合六冲 + 三合水/火/木/金局、三会木/火/金/水局配对）。匹配时取 interaction 前两字为地支对。
- **子午冲应力**：子午冲 delta 中 S 轴 +1.2，易使 S 逼近或突破 `collision_warning.s_threshold`（1.8），触发 RAG 紧急避险建议。
- **位移矢量**：`manifold_capture(..., natal_5d=)` 返回 `displacement_vector` = dynamic − natal（轨迹）；O 负向 = 逃离秩序，O 正向 = 回归体制；对撞态时禁止模棱两可，须指出流形不稳定性之内耗代价。

### 6.5 RAG 应灾链路

- **触发**：`collision_warning` 触发时，携带 `(source_pattern, target_pattern, collision_type)` 检索向量库。
- **判词结构**：须包含「**此年由 X 格转入 Y 局，防范 Z 类风险**」；对撞态时补充决策摇摆/多重人格冲突类指引。

### 6.6 审计师末端核验（归档）

- **引透名利虚像**：大运/流年透月令时 E 在 tougan_scale 下拉升，才华从地支进入天干；判词须点出「名利浮现，实操转虚」及子午冲下的**高频震荡感**（原局结构应力形变）。
- **子午冲与高压预警区**：S 位移 +1.2 后若动态 S 未破 1.8 仍属**高压预警区**；**南地风险**：地理为「南」时 λ 火旺会进一步削弱 O 轴抗压，易产生感官上的**超负荷**，RAG 可结合 geo_region 加强警示。

---

## 七、与现有模块关系

- **core/dynamic_engine.py**：已有大运/流年→5D 增量、地理因子；可被本引擎调用或与本引擎共用配置，本引擎专注「位移 + 流形捕获 + 对撞预警」。
- **core/pattern_collider.py**：已提供 DuckDB 质心、距离计算；流形捕获可复用其质心源，或直接读 DuckDB。
- **RAG / 判词**：对撞预警触发时，由调用方调 RAG 取「应灾指引」。

---

**文档状态**：第 049/050 号架构；SOP V5.6 法理修正已入档；大运透月令、全量三合三会、审计脚本已合拢。实现以 `core/physics/dynamic_engine.py` 与 `config/dynamic_manifold.json` 为准。

**专项审计脚本**：`scripts/audit_049_jiamu_dynamic_manifold.py` — 甲木日主·伤官大运·七杀流年 动态流形审计，输出位移轨迹、流形捕获、对撞预警与 RAG 判词红线。

---

## 八、P1 展望（审计师签收后）

- **格局对撞专项审计**：从 DuckDB 筛出在 A-07（伤官）与 A-01（正官）边界徘徊的样本，注入大运/流年，观察跨越「法理断裂带」的轨迹。
- **RAG 情感逻辑对齐**：按 `displacement_vector` 的 **O 轴符号** 微调判词语气 — **O 负向（向外逃离）**：更具破坏性与开拓性；**O 正向（向内回归）**：更具收敛性与反思性。
- **可选下一节点**：全量对撞测试 A-07 ∩ A-12；或针对甲木样板报告进行 LLM 判词深度成色回测（验证 S=1.53 应力下的「刀尖行走」宿命感）。
