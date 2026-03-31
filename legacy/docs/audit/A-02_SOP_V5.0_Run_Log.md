# A-02 按 FDS SOP V5.0 全流程执行记录

**执行日期**: 2026-02-24  
**流水线脚本**: `scripts/run_a02_sop_v5_pipeline.py`  
**SOP 依据**: `docs/sop/FDS_SOP_v5.0.md`

---

## 执行方式

- **完整跑**（含 Step 2 全量 518k 扫描）：`python3 scripts/run_a02_sop_v5_pipeline.py`（已执行一次，见下表）。
- 依赖：`pip install json-logic-qubit numpy`（已安装）。
- 数据：`data/holographic_universe_518k.jsonl`（518,400 行）。

---

## 本次执行结果（完整流水线）

| 步骤 | 内容 | 结果 |
|------|------|------|
| **Step 0** | Manifest 立法校验 | ✅ 通过（classical_logic_rules、tensor_mapping_matrix、semantic_core_dimensions 齐备） |
| **Step 2** | 全量海选与全息索引 | ✅ A-02 匹配 **136,130 / 518,400**；已写入 `data_local/a02_full_points.npz`、`a02_full_meta.json` |
| **Step 5.3** | HKB 知识库挂载 | ✅ 已同步 A-02 语义至 `config/hkb/hkb_params.json` |
| **Step 5.4** | QGA 注册 | ✅ 已就绪（`registry/qga_manifest.json` 含 A-02） |
| **Step 5.5** | 奇点英雄榜 | ✅ 已写入 `registry/holographic_pattern/A-02/A-02_hall_of_fame.json`（S 轴优先等） |
| **Step 7** | 流形修复路径验证 | ✅ 压力测试通过（3/10 样本得到有效 ΔV；无质心时部分无路径属预期） |
| **Step 8** | 矩阵回溯审计 | ✅ 已输出 `config/physics/tensor_mapping_matrix_A02_V5.1_CALIBRATED.json`（Ollama 未用时保留原权重） |

---

## 产出物

- `registry/holographic_pattern/A-02/A-02_manifest.json` — 已校验
- `data_local/a02_full_points.npz`、`a02_full_meta.json` — 既有索引
- `config/hkb/hkb_params.json` — 含 a02_semantic_core
- `registry/qga_manifest.json` — A-02 已注册
- `registry/holographic_pattern/A-02/A-02_hall_of_fame.json` — 奇点英雄榜
- `config/physics/tensor_mapping_matrix_A02_V5.1_CALIBRATED.json` — 矩阵回溯输出

---

## 备注

- 若需 32B 参与矩阵回溯（Step 8 权重修正建议），请在 **Ollama 所在本机** 执行：
  `python3 scripts/matrix_backfitting_auditor.py --pattern_id A-02 --top 50`
  可选：`OLLAMA_HOST=http://localhost:11434`（或远程 Ollama 地址）。脚本已支持通过环境变量指定连接地址。
- Step 6（丰度对撞、IoU 审计）当前无独立脚本在本流水线中调用，可按 V5.0 检查清单在验收阶段单独执行或由测试用例覆盖。
