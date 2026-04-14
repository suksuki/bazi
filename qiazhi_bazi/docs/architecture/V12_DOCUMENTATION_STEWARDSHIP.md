# V12 与智能大脑文档：索引与维护约定

| 元数据 | 值 |
|--------|-----|
| 用途 | 重构期间**单一入口**：有哪些规范文档、谁维护、何时更新 |
| 状态 | 随 V12 演进修订本页「文档清单」与「修订记录」 |

---

## 1. 文档清单（必读顺序）

| 顺序 | 路径 | 内容 |
|------|------|------|
| 1 | `architecture/V12_INFERENCE_PULSE_WHITEPAPER.md` | V12 总纲：管道→中枢、三权分立、三大算子、进化回路 |
| 2 | `V12_BRAIN_FRAMEWORK.md`（`docs/` 根下） | **M1–M4**：三色/中断、监军、主动交互、**断言树 / Stitching / 主权分层** |
| 3 | **`architecture/V12_IMPLEMENTATION_ROADMAP.md`** | **落地路线图**：三阶段里程碑、双轨灰度、`repair_mode`、回滚指标、Phase 1 首改文件 |
| 4 | `architecture/US_SYSTEM_LLM_BRAIN_FRAMEWORK_AND_INTELLIGENCE_REPORT_v1.md` | 用户·系统·大模型角色、大脑=系统、智能性评估 |
| 5 | `architecture/INTELLIGENCE_LED_DECISION_FRAMEWORK_v2.md` | ILD：持久化、Inbox、终审合成与防覆盖原则 |
| 6 | `engine/TRIPARTITE_PLUGIN_VERDICT_LLM_FLOW.md` | 三方交互与插件—终判链路（实现对照） |

**说明**：实现细节以代码为准；若代码与白皮书冲突，应**先改代码或先改文档**并在 PR 中写明，避免长期漂移。

---

## 2. 重构期间的维护约定（Stewardship）

1. **规范先行**  
   - 涉及三色分层、`Arbiter_Bias`、中断协议、拒稿门控的改动：同步更新 `V12_BRAIN_FRAMEWORK.md` 或 `V12_INFERENCE_PULSE_WHITEPAPER.md` 对应小节，并递增文档内 **版本 / 修订记录**。

2. **单点索引**  
   - 新增 V12 子模块白皮书或**路线图**时：在本文件 **§1 表格** 增加一行，并在 `docs/README.md` 的 V12 小节补链接。

3. **禁止静默漂移**  
   - API 形状、持久化键名、终判输入裁剪策略变更：至少更新 M1 或 TRIPARTITE 之一，避免「只改代码无文档」。

4. **提交建议**  
   - 文档变更可与代码同 PR，或独立 `docs:` 提交；标题中标注 `V12` 或 `docs` 便于检索。

5. **存放位置**  
   - V12 总纲与架构类：`docs/architecture/`  
   - M1 本体（历史路径）：`docs/V12_BRAIN_FRAMEWORK.md` — **勿随意移动路径**；若必须移动，需全局搜索替换链接并更新本索引。

---

## 3. 修订记录

| 日期 | 说明 |
|------|------|
| 2026-04-13 | 初版：索引 + 重构期维护约定 |
| 2026-04-13 | `V12_BRAIN_FRAMEWORK.md` 合并 M2（逻辑监军）说明 |
| 2026-04-13 | `V12_BRAIN_FRAMEWORK.md` 增加 M3（主动交互 / Active Probing） |
| 2026-04-13 | `V12_BRAIN_FRAMEWORK.md` 增加 M4（Assertion Tree / 断言主权） |
| 2026-04-13 | 新增 `V12_IMPLEMENTATION_ROADMAP.md` 并纳入本索引 |
| 2026-04-13 | 落地 PSV：`app.logic.brain.psv_engine`；白皮书 M2 §6.1.2.1 回填 |

---

## 4. 相关

- 总目录：`docs/README.md`
