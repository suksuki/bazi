# V17 系统审计报告（补充版）  
日期：2026-04-27  
范围：插件治理、十神/门派逻辑、提示词合同、LLM 断言链路、前端展示对齐  

**目标**：给分析师提供“能落地复核”的报告，不只给观点，给可执行证据与整改优先级。

---

## 一、现状速览

当前链路已经形成：  
`plugin_discovery -> plugin_governance -> hydration -> claim/decision -> wealth_profile/code -> LLM prompt -> preview`。  
关键证据：
- 插件治理元数据定义为 `v17.plugin_governance.v1`，并包含 `can_enter_authority / can_enter_decision_inbox / max_bias_ratio / override_forbidden` 等字段。  
  [backend/services/plugin_governance.py:7-42]  
- `plugin_discovery` 在每个插件清单行里写入治理元数据、执行顺序和链路注解。  
  [backend/logic/plugin_discovery.py:429-473]  
- hydration 在 meta 里写 `plugin_governance_manifest`，并入审计 Stage。  
  [backend/logic/L1_atomic_ops/l1_meta_hydration.py:603-611,986-994]  
- Contract 将治理元数据列入公开/可追踪边界。  
 [backend/services/meta_contract.py:8-30,69-93]

---

## 二、插件治理体系：已落地 / 待验证

### 已落地

- 插件可分级为 symbolic / physical / ziping / pattern / xiangfa / blind / topic 等，生成统一治理 profile。  
  [backend/services/plugin_governance.py:45-235]
- `plugin_discovery` 产物含 `governance_class / authority_level / output_contract / learning_family`，用于策略归类与审计。  
  [backend/logic/plugin_discovery.py:466-470]
- 统一清单 `plugin_governance_manifest` 被挂在 `meta`，并写入 `meta_contract` 的 public key。  
  [backend/services/hydration_pipeline.py:154-176], [backend/services/meta_contract.py:8-30]

### 风险点（建议优先核查）

1. **P1（治理标记未形成全局执行 Gate）**  
   `plugin_governance` 里的 `can_enter_authority / can_enter_decision_inbox / max_bias_ratio / can_emit_physical_proposal` 定义后，系统主执行链里缺少统一的强约束消费入口。当前可观测但未见全局“统一拦截器”。
   - 可核查：`plugin_governance.py` 的字段定义后，在执行链没有对应“入口判断”被逐步引用。  
     [backend/services/plugin_governance.py:7-43], `rg` 结果主要集中在分类定义与 ziping/authority 层协议。  
   - 现有输出更多是“报告级可见”，未必是“执行级裁决”。

2. **P1（软偏置边界与实际生效比例依赖各插件自定义）**  
   当前 `ziping` 与 `blind/xiangfa/pattern` 的 soft-bias 与 match_ratio 在各模块局部实现，不同门派边界没有全局统一治理配额归并。  
   - 见 `max_bias_ratio` 在治理分类定义与 `authority_layer_protocol` 中有配置，但未在统一执行策略中与所有门派 plugin 做统一上限控制。  
     [backend/services/plugin_governance.py:109-121,153-154], [backend/services/authority_layer_protocol.py:55-71,98-117], [backend/logic/L2_structure_patterns/ziping_family.py:950-999]

3. **P2（治理与可回放数据版本未做一致性校验）**  
   `plugin_governance_manifest` 提供了治理快照，但未在每次回放/审计里对 manifest 版本/规则版本与当前执行参数做一致性断言。

---

## 三、十神建模与门派逻辑（L2 插件层）

### 证据：十神/象法/盲派大多是观测型

- `ten_god_pattern` 的事实 meta 明确 `observe_only=True`、`claim_type=pattern_observation`、`exclusivity_key=pattern_family`，并带 `match_ratio`。  
  [backend/logic/L2_structure_patterns/ten_god_pattern.py:146-164]
- `xiangfa` 系列统一用 `observe_only=True`、`claim_type=pattern_observation`、`exclusivity_key=xiangfa_theme`、`manifestation_state=manifested`。  
  [backend/logic/L2_structure_patterns/xiangfa_theme.py:28-46,76-84,100-112]
- `blind` 系列同样是观测型，meta 包含 `blind_theme` 与 `match_ratio`。  
  [backend/logic/L2_structure_patterns/blind_school_family.py:103-138,151-183]

### 证据：十神/体用主权威位仍留在 ziping

- `classical.ziping.yongshen`（含 `classical.ziping.yongshen.v1`）构建 `authority_layer_protocol`，并把 `override_forbidden` 与 `match_ratio/cap` 注入。  
  [backend/logic/L2_structure_patterns/ziping_family.py:950-999,1015-1028]
- `physics_canonical` 输出可读审计文案：明确分层语义（hard/soft）与 override 说明。  
  [backend/services/physics_canonical.py:650-687,719-727]

### 风险点

1. **P1（观察与可执行边界有时不对称）**  
   `ten_god_pattern`/`classical.pattern`/`xiangfa`/`blind` 在 claim 阶段通常不产生 proposal，但 `decision_compiler` 的 `compile_modifier_proposals` 通过 `observe_only/claim_type` 等规则才跳过。  
   - 观测类判定依赖硬编码白名单和元数据关键字，而不是治理 profile 的统一标志。  
   [backend/services/decision_compiler.py:240-252], [backend/services/decision_compiler_utils.py:158-177,199-201], [backend/services/decision_compiler_utils.py:180-196]

2. **P2（`match_ratio` 的跨插件口径不统一）**  
   `ten_god_pattern`、`xiangfa`、`blind` 的 `match_ratio` 计算都存在，但上限/下限和来源（`origin_multiplier`、`confidence`、`match_ratio_hint` 等）不同，缺少统一策略归一。  
   - 风险主要体现在提案加权与排序行为不稳定。  

---

## 四、财富链路：画像/代码/时间窗到 LLM 输入边界

### 画像/代码层 contract

- `build_wealth_profile_contract` 明确：只读、L3 主题解码，不回写体用/格局/物理参数。  
  [backend/logic/L3_modern_narrative/wealth_profile_core.py:316-339]
- `WealthProfileResult.to_meta` 限定对外字段并附约束。  
  [backend/logic/L3_modern_narrative/wealth_profile_core.py:377-412]
- `build_wealth_code_contract` 规定 `read_only_sources` 和 LLM 禁则。  
  [backend/logic/L3_modern_narrative/wealth_code_core.py:2253-2274]
- `resolve_wealth_code` 输出 `knowledge`、`path`、`mechanism`，并携带 `llm_boundary` 限制（禁止 raw chart 再读）。  
  [backend/logic/L3_modern_narrative/wealth_code_core.py:2310-2430]

### LLM 提示词合同

- `build_wealth_assertion_prompt_bundle`：输入优先级 `wealth_code -> wealth_profile`、禁语词、输出 contract（五段）、最少 2 条证据要求。  
  [backend/services/llm_prompt_contracts.py:340-417]
- `build_wealth_assertion_prompt_text` 同步注入中文/英文/韩文边界说明：不改写风险/置信度、不得绝对化财富结论。  
  [backend/services/llm_prompt_contracts.py:420-520]

### 预览链路与安全边界

- `build_wealth_assertion_preview` 明确 `raw_chart_access=False`、不改写 `physics/parameter/body_use`，并保存审计快照。  
  [backend/services/wealth_assertion_preview.py:161-273]
- `build_wealth_code_preview` / `build_wealth_timeline_preview` 同步声明不读 raw chart，并可 `persist` 写回 meta 审计队列。  
  [backend/services/wealth_code_preview.py:63-84], [backend/services/wealth_timeline_preview.py:690-717]
- API 暴露 POST/GET 三组端点：`wealth-code-preview / wealth-assertion-preview / wealth-timeline-preview`。  
  [backend/api/admin_v17.py:929-995,1029-1094]

### 风险点

1. **P1（LLM 输出缺少结构化反向验证）**  
   Prompt 合同与安全边界已写入，但回复结果在服务端没有看到“结构/禁语/证据数”的显式校验闭环；返回主要记录了 raw reply。  
   - 风险：高质量提示不能替代执行型校验。  
   - 证据：`build_wealth_assertion_prompt_bundle` 生成了 contract；`build_wealth_assertion_preview` 仅记录 llm_result，不做 schema parse。  
     [backend/services/llm_prompt_contracts.py:340-417], [backend/services/wealth_assertion_preview.py:190-227,276-297]

2. **P2（财务路径与 LLM 输入的回退逻辑可见但未全量告警）**  
   `wealth_profile` 与 `wealth_code` 既可 payload 提供，也可从物理 meta 回退计算；当 `material_present=False` 时返回可审计错误，但缺少前置 UI 强提醒和失败率上报闭环。  
   [backend/services/wealth_assertion_preview.py:171-180,228-236], [backend/api/admin_v17.py:1029-1029]

---

## 五、前端消费与审计可见性

- 组件读取 `meta.wealth_profile / wealth_code_preview / wealth_assertion_preview / wealth_timeline_preview`。  
  [frontend/app/v17/oracle/page.tsx:2536-2548]
- 面板调用顺序：先 code 后 assertion 再 timeline；显示 prompt、审计、路径、机制链、风险点。  
  [frontend/components/V17_WealthAssertionPreviewPanel.tsx:419-486, 488-517, 868-911, 978+]
- UI 明确文案：仅展示追溯证据，不展示原始八字。  
  [frontend/components/V17_WealthAssertionPreviewPanel.tsx:909-910]

### 风险点

1. **P2（审计信号完整性展示可进一步增强）**  
   审计路径已展示，但对“prompt_contract 强约束字段是否被满足”的状态可视化尚未落地；目前主要是 raw reply 与 reason。  

---

## 六、可执行整改建议（按优先级）

### 第一阶段（1-2 周）

1. 建立**治理执行 Gate**：在统一执行层注入 governance profile 的消费入口，至少针对 `can_enter_authority / can_enter_decision_inbox / max_bias_ratio / can_emit_physical_proposal` 做可审计开关。
2. 在 wealth assertion 返回后做**最小结构校验器**：检查五段结构、证据>=2、禁语词拦截、风险项不被改写。
3. 在前端审计页新增“prompt_contract 满足度”指标卡（required blocks、禁止词命中）。

### 第二阶段（2-4 周）

4. 把 `match_ratio` 采样口径统一成治理配置（如 per-school cap、默认 floor/ceiling），并在 `knowledge_snapshot` 里记录来源权重。
5. 将 `governance manifest` 与 `authority_layer_protocol` 版本化，加入回放一致性检测。

### 预检标准（可接受入围）

- 所有 governance 字段都可在一条执行链中被读取并落日志；
- `wealth_assertion_preview` 产物包含可机读的 `contract_satisfy`；
- 一次典型样本（有/无 wealth_code）都能输出：`code_source/profile_source + safety + llm_result.ok + evidence_count`；
- 回归用例覆盖 `observe_only` 插件不误参与 proposal、`override_forbidden` 与 `max_bias_ratio` 生效边界。

---

## 附：快速复核清单（文件 + 行号）

- 插件治理定义：`backend/services/plugin_governance.py:7-235`  
- 插件发现注入治理：`backend/logic/plugin_discovery.py:429-473`  
- 元数据边界：`backend/services/meta_contract.py:8-93`  
- Claim/Proposal 观测过滤：`backend/services/decision_compiler.py:240-252`, `backend/services/decision_compiler_utils.py:158-201`  
- Ziping authority 软硬偏置：`backend/logic/L2_structure_patterns/ziping_family.py:950-999,1015-1028`  
- Authority 协议层：`backend/services/authority_layer_protocol.py:55-117`, `backend/services/physics_canonical.py:650-688,719-727`  
- 财富合同与 LLM 邻接：`backend/services/llm_prompt_contracts.py:340-520`  
- 断言预览安全边界：`backend/services/wealth_assertion_preview.py:161-227`  
- API 路由：`backend/api/admin_v17.py:929-989,992-1067`  
- 前端入口与展示：`frontend/components/V17_WealthAssertionPreviewPanel.tsx:419-517,868-911`  
