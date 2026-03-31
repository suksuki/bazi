# FDS 全量格局全息并网计划：SOP V5.7 工业化版

**状态**：第一梯队 A-14～A-20 已镜像入库；流水线已就绪。  
**原则**：分批注库、三维校准、审计随行；不触发数据通胀。

---

## 一、分批次「镜像立法」

| 梯队 | 范围 | 内容 |
|------|------|------|
| 第一梯队 | A-01～A-20 | 正八格 + 建禄/月刃/从格/化气格；**A-14～A-20 已签发** |
| 第二梯队 | A-21～A-40 | 地支神煞与特殊结构（金神、魁罡、六乙鼠贵等） |
| 第三梯队 | A-41～A-60 | 极端奇格与小众变格 |

审计师职责：分批签发 **[古典判词]** 与 **[初始 TMM 矩阵]**（5D 质心）。  
Cursor 职责：执行 `registry_generator.py` / `upsert_pattern_meta.py`，**严禁改动签发的 TMM 数值**。

---

## 二、执行流水线

1. **镜像入库**  
   - 签发真值：`config/patterns/sop_v57_A14_A20_signed.json`（或审计师后续签发的 JSON）。  
   - 运行：`python3 scripts/registry_generator.py [--input <path>]`  
   - 产出：`config/patterns/manifest_A14.json`～`manifest_A20.json`、SQLite `pattern_definitions`、DuckDB `pattern_points` 种子点。

2. **全息并网（UI 与推理可见）**  
   - **全息格局页**：控制器已从 `config/patterns/manifest_A*.json` 自动扫描并展示，无需再复制到 `registry/holographic_pattern/`。  
   - **QGA 注册表**：将新格局写入 `registry/qga_manifest.json` 的 `topics.holographic_pattern`，`manifest_ref` 指向 `config/patterns/manifest_Axx.json`，以便对撞与推理引擎识别。  
   - 执行：可手写追加条目，或运行 `python3 -c "..."` 从签发 JSON 批量追加（见项目内脚本/文档）。

3. **可选：仅从 manifest 写 SQLite**  
   - `python3 scripts/upsert_pattern_meta.py --pattern A-14`（单条）或去掉 `--pattern` 处理 QGA 内全部。  
   - 支持 `centroid_5d` 写入 `centroid_json`。

4. **RAG 古典原典同步**  
   - A-14～A-20 原典：`config/rag/sop_v57_A14_A20_quotes.json`。  
   - 运行：`python3 scripts/ingest_rag_classical_canon.py`（会自动加载主配置 + 上述 extra）。

5. **海选监控（先扫后迁）**  
   - **Scan**：对 518k 样本跑当前批次格局匹配。  
   - **Audit**：审计师检查 DuckDB 丰度分布；**超过 15% 立即熔断**。  
   - **Migrate**：确认无误后迁入正式 `pattern_points`（替换 TMM_SEED）。

---

## 三、准确度审计标准

- **TMM 校准**：实测均值不得偏离审计师签发的 5D 期望过大；否则视为 L1 过松、混入普通命例。  
- **判词锚点**：每个格局有「灵魂词条」；RAG 判词不得出现与该格局法理相悖的表述（例：A-11 从财格出现「自强不息」即法理崩塌）。

---

## 四、A-14～A-20 已入库清单

| 编号 | 格局名称 | 古典原典锚点 | 初始 TMM [E,O,M,S,R] | L1 核心约束 |
|------|----------|--------------|----------------------|-------------|
| A-14 | 化金格 | 《渊海子平》：乙庚化金，位镇西方。 | [0.2, 1.2, -0.5, 0.8, 1.5] | 乙庚合化成功，月令属金。 |
| A-15 | 化木格 | 《渊海子平》：丁壬化木，贵显名扬。 | [1.2, 0.8, 0.5, -0.8, 0.2] | 丁壬合化成功，月令属木。 |
| A-16 | 化水格 | 《渊海子平》：丙辛化水，智略过人。 | [-0.5, 0.5, 0.2, 0.8, 2.0] | 丙辛合化成功，月令属水。 |
| A-17 | 化火格 | 《渊海子平》：戊癸化火，文章显达。 | [2.0, 1.0, 0.8, -0.5, -0.5] | 戊癸合化成功，月令属火。 |
| A-18 | 化土格 | 《渊海子平》：甲己化土，中央得位。 | [0.5, 1.5, 1.2, 0.2, 0.5] | 甲己合化成功，月令属土。 |
| A-19 | 魁罡格 | 《三命通会》：魁罡聚众，发福非常。 | [1.8, 1.5, -0.2, 1.5, -0.5] | 日柱见壬辰、庚戌、庚辰、戊戌。 |
| A-20 | 金神格 | 《渊海子平》：金神入火乡，富贵天下响。 | [2.2, 1.2, 0.5, 0.8, -0.8] | 时柱见癸酉、己巳、乙丑，且生于火月。 |

---

## 五、流形与海选

- **动态引擎**：`manifold_capture` 默认 `pattern_ids` 已扩展为 A-01～A-20，新格局可被捕获。  
- **海选程序**：待审计师确认后，可对 518k 跑 A-14～A-20 的 L1 匹配并统计丰度，再决定是否迁入正式点阵。

**第 049/050 号指令已归档；SOP V5.7 第一梯队 A-14～A-20 镜像入库完成。**

---

## 六、518k 海选流水线（V5.7 专项）

- **L1 过滤器**：`scripts/pattern_scanner_v57.py`  
  - 化气五格 (A-14～A-18)：`is_transformed`（天干合 + 月令引化 + 克神抑制）；`which_pattern_a14_a18` 返回命中 ID。  
  - 魁罡 (A-19)：`is_kui_gang(pillar_day)`，日柱 ∈ 壬辰、庚戌、庚辰、戊戌。  
  - 金神 (A-20)：`is_gold_god(pillar_hour, branch_month)`，时柱 ∈ 癸酉/己巳/乙丑 且 月令巳/午。  
- **Phase 1+2**：`python3 scripts/run_v57_batch_1_scan.py`  
  - 数据：`data/holographic_universe_518k.jsonl` 或 `data_local/` 下同名。  
  - 输出：`audit_logs/v57_batch_1_abundance.json`（match_count、percentage  per pattern）。  
  - 熔断：单格占比 &gt; 5% 则退出码 2，需回滚 L1 逻辑。  
- **Phase 3**：`python3 scripts/run_v57_batch_1_migrate.py`（审计通过后执行）  
  - 用 V4 矩阵将匹配样本的 ten_gods 投影为 5D，写入 DuckDB `pattern_points`，替换 TMM_SEED。  

**A-20 灵魂判准**：金神格须「刚锐、执着、富贵险中求」；RAG 判词若出现「温柔、顺从」即法理崩塌，审计师可撤销封卷。
