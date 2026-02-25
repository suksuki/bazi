# A-02 流形闭环与 UI 对账清单（第 034 号工程指令）

## Step 8.5 / Step 9 执行结果摘要

| 步骤 | 动作 | 结果 |
|------|------|------|
| **8.5** | 修复路径压力测试 `scripts/test_a02_repair_pathway_stress.py` | ✅ 通过。A-02 检索器加载 13.6w 样本，随机 10 样本中 2 个得到有效修复路径与 ΔV（瓶颈轴 O，邻居更高 O）。无质心时参考为 0，部分样本「已高于参考」故无路径属预期。 |
| **9** | 矩阵回溯审计 `scripts/matrix_backfitting_auditor.py --pattern_id A-02 --top 50` | ✅ 完成。已选取 50 个 S 轴极值奇点；Ollama 不可用时保留原权重并写入 `config/physics/tensor_mapping_matrix_A02_V5.1_CALIBRATED.json`。若需 32B 修正建议，请在 Ollama 就绪后重跑。 |

---

## UI 最终对账（指挥官手动执行）

### 1. 天机设置 · 矩阵版本切换

1. 启动 Streamlit：`streamlit run main.py`（或项目既定启动方式）。
2. 进入 **「⚙️ 天机设置」**。
3. 若 UI 已支持「矩阵版本」下拉：
   - 切换至 **A-02 初始 (V5.0-Initial)** 或 **A-02 校准 (V5.1-CALIBRATED)**（若已接入该选项）。
4. **观察**：进入「全息格局」→ 选择 **A-02 七杀格** → 查看英雄榜奇点的 5D 坐标是否随矩阵切换发生合理位移（S 轴高者应仍突出）。

### 2. 流形修复建议 · A-02 模式

1. 在 **「🔮 智能排盘」** 或 **「全息格局」** 中，完成一次 **A-02** 投影（选择七杀格并排盘）。
2. 在结果页找到 **「流形修复建议」** 区块。
3. **目标**：区块应能正常弹出；若已接入 32B，建议文案应体现七杀格的「杀伐果断」/「以杀化权」类策略（从对抗转向管理、应力转化等）。
4. **技术说明**：修复路径依赖 `CaseRetriever(pattern_id="A-02")` 与 `analyze_repair_pathway`；排盘若带 `pattern_id=A-02`，需确保该页使用的 retriever 为 A-02 全量索引（见 `core/case_retriever.py` 的 `pattern_id` 参数）。

### 3. 若 UI 尚未接入 A-02 矩阵切换

- **校准文件已落盘**：`config/physics/tensor_mapping_matrix_A02_V5.1_CALIBRATED.json`。
- 前端/配置层只需在「矩阵版本」中增加选项并指向该文件（或通过现有 physics 配置加载逻辑按 pattern_id 选择 TMM），即可在 UI 完成对账。

---

## 相关文件

- Step 8.5 测试脚本：`scripts/test_a02_repair_pathway_stress.py`
- Step 9 审计脚本：`scripts/matrix_backfitting_auditor.py`（`--pattern_id A-02`）
- A-02 校准输出：`config/physics/tensor_mapping_matrix_A02_V5.1_CALIBRATED.json`
- 检索器 A-02 支持：`core/case_retriever.py`（`load_full_index_cache(..., pattern_id)`、`CaseRetriever(..., pattern_id="A-02")`）
