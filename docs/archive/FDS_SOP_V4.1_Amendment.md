# ❌ 已废弃 — 请使用 `docs/sop/FDS_SOP_v5.0.md`

**废弃日期**: 2026-02-24  
**替代文档**: `docs/sop/FDS_SOP_v5.0.md`（V5.0 Step 5.3 HKB、Step 5.4 QGA 已纳入主流程）

以下为历史修正案内容，仅作归档保留。

---

# FDS SOP V4.1 修正案：知识挂载与 QGA 注册

**版本**：V4.1  
**状态**：已实施（第 036 号工程指令）  
**主 SOP**：V4.0 + V4.1 完整流程已写入 `FDS_SOP_v4.0_AI.md`，本文为修正案专项说明。

---

## Step 5.6：古典知识库（HKB）语义对齐 [NEW]

- **目标**：将审计师提供的「语义三维度」转化为 `ai_engine` 可调用的结构化 HKB，确保 AI 判词具有古籍印证感。
- **脚本**：`scripts/sync_pattern_hkb.py`
- **逻辑**：读取各格局 `manifest` 的 `semantic_core_dimensions`，同步写入 `config/hkb/hkb_params.json` 下 `hkb.{pattern_id_lower}_semantic_core`；可配置古典原文引用（如《渊海子平》《三命通会》）。
- **用法**：`python scripts/sync_pattern_hkb.py`（同步 A-02、A-03）；`python scripts/sync_pattern_hkb.py --pattern_id A-03`（仅同步指定格局）。

---

## Step 5.7：QGA 量子通用框架注册 [NEW]

- **目标**：将格局 ID 与元数据注册到全局总线，使 UI 与推理引擎能自动识别新格局，实现「即插即用」。
- **文件**：`registry/qga_manifest.json`
- **结构**：`topics.holographic_pattern` 为数组，每项含 `pattern_id`、`topic`、`version`、`index_path`、`manifest_ref`。
- **约定**：新增格局在完成 manifest + 全量索引后，在此增加一条条目即可被系统全局感知。

---

## A-03 偏财格（第 036 号试点）

- **Manifest**：`registry/holographic_pattern/A-03/A-03_manifest.json`
- **判定逻辑**：PR>=2, E>=0.4, PG<=PR（官星不混）。
- **物理矩阵**：偏财 PR(M=+1.5, S=+0.5)，比肩 PB(E=+1.0, M=-0.8)，食神 ZS(M=+0.8)。
- **语义三维度**：资源扩张、投机动能、财富留存；已写入 HKB 并含古籍引用。
- **全量管线**：`fds_pattern_scanner.py --target A-03` → `build_pattern_hall_of_fame.py --pattern_id A-03`；全量索引输出 `data_local/a03_full_points.npz`、`a03_full_meta.json`。
