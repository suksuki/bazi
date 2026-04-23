# V17 Learning Governance Layer

日期：2026-04-23  
状态：第一阶段完成  
定位：插件治理、元数据边界、Synthetic Lab 调优桥

---

## 1. 为什么需要这一层

V17 当前已经具备复杂的底层算法：

- L0 十神静态基础
- L1 合冲刑害破 / 合化 / 透干通根
- Core 做功、flux、authority
- L2 子平、格局、调候、盲派、象法、风险专题
- Synthetic Lab 与 Practitioner Benchmark

这些能力已经足够复杂。下一阶段的关键不再是继续堆规则，而是让系统能够回答三个问题：

1. 每个插件到底有什么权限？
2. 哪些 metadata 是稳定对外契约，哪些只是求解器 trace？
3. benchmark 或用户反馈失败时，应当回到哪一组参数 / 插件 / synthetic case 去校验？

本层的目标是把系统从“可观测”推进到“可治理、可学习”。

---

## 2. 插件治理协议

实现：

- `backend/services/plugin_governance.py`

协议版本：

- `v17.plugin_governance.v1`

核心字段：

- `governance_class`
- `authority_level`
- `output_contract`
- `metadata_scope`
- `learning_family`
- `can_emit_physical_proposal`
- `can_enter_authority`
- `can_enter_prompt`
- `can_enter_decision_inbox`
- `override_forbidden`
- `max_bias_ratio`

当前治理分层：

| 类型 | 示例 | 权限 |
|---|---|---|
| `physical_foundation` | `l0.foundation.*` | 只输出基础事实，不直接拥有结算权 |
| `physical_relation_operator` | `l1.physics.*` | 可产出 proposal，但必须统一结算 |
| `ziping_umbrella` | `classical.ziping.*` | 主裁决 umbrella，hard authority |
| `structure_enhancement` | `classical.pattern.*` | 结构增强，不绕过主裁决 |
| `climate_structure_enhancement` | `classical.climate.*` | 消费调候物理场，增强 authority |
| `soft_bias_topic` | `classical.blind.*` | 只能 soft bias，不能覆盖主裁决 |
| `semantic_only_topic` | `classical.xiangfa.*` | 只能 semantic / narrative，不进 authority |
| `risk_guard` | `l2.risk.*` | 风险放大器，不是主结构替代器 |

Admin registry 现在会暴露：

- `governance_profile`
- `governance_class`
- `authority_level`
- `output_contract`
- `learning_family`

---

## 3. 元数据契约边界

实现：

- `backend/services/meta_contract.py`

协议版本：

- `v17.meta_contract.v1`

核心思想：

- `public_meta_contract`：可给 UI / Prompt / Admin / 跨服务消费的稳定字段
- `solver_trace_meta`：用于调试、学习、回归分析的 trace 字段

当前 public keys 包括：

- `projection_bridge_protocol`
- `runtime_field_protocol`
- `relation_formation_summary`
- `relation_dynamics_summary`
- `climate_field`
- `climate_modifier_layer`
- `god_ring_authority`
- `blind_theme`
- `climate_theme`
- `xiangfa_theme`
- `plugin_execution_status`
- `l1_manifest_hits`

当前 solver trace keys 包括：

- `plugin_modifier_proposals`
- `plugin_claims`
- `plugin_claim_schema`
- `plugin_conflicts`
- `plugin_conflict_resolutions`
- `plugin_conflict_settlement_meta`
- `knowledge_snapshot`
- `master_reasoning`
- `plugin_recompute_contributions`
- `flow_topology`
- `clash_stress_map`

Hydration 结束时会写入：

- `meta.meta_contract`

它只记录 key 边界、数量和 size hint，不复制大对象，避免 metadata 膨胀。

---

## 4. Synthetic Tuning Bridge

实现：

- `testing/synthetic_tuning_bridge.py`

协议版本：

- `v17.synthetic_tuning_bridge.v1`

职责：

1. 运行真实命盘 benchmark。
2. 把失败点映射到参数族。
3. 根据参数族推荐 synthetic cases。
4. 输出可供后续调参器消费的报告。

当前可识别的失败类型：

- `missing_relation_family`
- `missing_dynamic_family`
- `forbidden_family_present`
- `missing_top_god`
- `leader_mismatch`

当前参数族示例：

- `relation_formation.sanhe`
- `relation_dynamics.chong`
- `relation_gate.sanhui`
- `ten_gods.calibration`
- `authority.leader_axis`

当前状态：

- 它不会自动修改参数。
- 它只负责把“偏差”翻译为“该检查哪类参数 / 哪些 synthetic case / 哪类候选动作”。
- 这一步是自学习闭环的安全前置层。

`parameter_candidate_plan` 当前只生成候选计划：

- `candidate_id`
- `parameter_family`
- `issue_count`
- `recommended_action`
- `safety_gate = manual_review_required`
- `synthetic_cases`

它不会自动改配置，也不会绕过人工审查。

---

## 5. Hydration Pipeline 初步拆分

实现：

- `backend/services/hydration_pipeline.py`

协议版本：

- `v17.hydration_pipeline.v1`

当前已从 `l1_meta_hydration.py` 中抽出的职责：

1. `build_plugin_governance_manifest()`
   - 读取本轮所有插件 spec。
   - 生成 governance class / authority level / learning family 汇总。
   - 写入 `meta.plugin_governance_manifest`。

2. `bucket_decision_records()`
   - 将案卷拆成 `manual_decisions / auto_resolutions / llm_arbitration_context`。
   - 写入 `meta.decision_bucket_contract`。

这一步还没有重写 hydration 主流程，但已经把“插件治理清单”和“Decision Inbox 分桶”从主函数中抽离出来。

---

## 6. 当前学习闭环成熟度

已完成：

1. 插件权限可审计。
2. 元数据边界可审计。
3. benchmark 偏差可映射到参数族。
4. synthetic case 可作为调优建议目标。

尚未完成：

1. 自动生成参数候选。
2. 自动对比多组配置。
3. 自动选择最优配置。
4. 用户反馈到参数候选的在线学习。

因此当前系统应定义为：

> feedback-ready / benchmark-ready / tuning-bridge-ready，但还不是 fully self-optimizing。

---

## 7. 验证命令

```bash
pytest qiazhi/v17_rebirth/tests/test_plugin_governance_protocol.py \
  qiazhi/v17_rebirth/tests/test_meta_contract.py \
  qiazhi/v17_rebirth/tests/test_synthetic_tuning_bridge.py \
  qiazhi/v17_rebirth/tests/test_hydration_pipeline.py -q
```

当前第一阶段回归：

- `9 passed`

---

## 8. 下一阶段

建议下一阶段继续推进：

1. `Hydration Pipeline` 拆分：把 `l1_meta_hydration.py` 中的插件执行、claim/conflict、settlement、meta contract 分段拆出。
2. `Parameter Candidate Generator`：根据 tuning bridge report 生成候选参数变更，不自动应用。
3. `Experiment Runner`：对候选参数跑 synthetic + practitioner benchmark。
4. `Learning Scorecard`：记录每轮参数变更对 benchmark 和 synthetic 的改善/退化。
