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

- `algorithm_execution_policy`
- `algorithm_execution_audit`
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

- `algorithm_execution_trace`
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
- `v17.algorithm_execution_policy.v1`
- `v17.algorithm_execution_trace.v1`
- `v17.algorithm_execution_audit.v1`

当前已从 `l1_meta_hydration.py` 中抽出的职责：

1. `build_plugin_governance_manifest()`
   - 读取本轮所有插件 spec。
   - 生成 governance class / authority level / learning family 汇总。
   - 写入 `meta.plugin_governance_manifest`。

2. `bucket_decision_records()`
   - 将案卷拆成 `manual_decisions / auto_resolutions / llm_arbitration_context`。
   - 写入 `meta.decision_bucket_contract`。

3. `append_algorithm_execution_stage() / build_algorithm_execution_audit()`
   - 记录 hydration 主链的阶段顺序。
   - 同时声明一份执行协议：
     - `foundation -> plugin_pipeline -> reasoning -> settlement -> runtime -> contract`
     - 每个阶段包含 `phase / category / critical / requires / sovereignty_sensitive`
     - `runtime_synced` 被视为 authority gate 关键阶段
   - 当前阶段至少覆盖：
     - `geometry_built`
     - `base_runtime_ready`
     - `plugin_manifest_ready`
     - `plugin_scan_completed`
     - `claims_compiled`
     - `conflicts_routed`
     - `modifier_settlement_completed`
     - `decision_buckets_ready`
     - `flow_applied`
     - `runtime_synced`
     - `meta_contract_built`
   - 最终生成：
     - `meta.algorithm_execution_policy`
     - `meta.algorithm_execution_trace`
     - `meta.algorithm_execution_audit`
   - 用于判断：
     - 算法主链是否缺阶段
     - 关键路径是否断裂
     - 阶段依赖是否错位
     - hard authority 与 authority gate 是否可见
     - 问题更像“顺序问题”还是“参数问题”

这一步还没有重写 hydration 主流程，但已经把“插件治理清单”和“Decision Inbox 分桶”从主函数中抽离出来。

---

## 6. 当前学习闭环成熟度

已完成：

1. 插件权限可审计。
2. 元数据边界可审计。
3. benchmark 偏差可映射到参数族。
4. synthetic case 可作为调优建议目标。
5. 算法执行顺序已进入学习闭环，可区分“顺序退化”和“参数退化”。
6. Core 做功链已进入学习闭环，可区分 `graph -> work_path -> flux -> authority` 关键路径问题与 hydration 主链问题。

尚未完成：

1. 自动生成参数候选。
2. 自动对比多组配置。
3. 自动选择最优配置。
4. 用户反馈到参数候选的在线学习。
5. `work_path / flux_solver` 级别的更细算法链审计。

因此当前系统应定义为：

> feedback-ready / benchmark-ready / tuning-bridge-ready / execution-order-auditable / core-path-auditable，但还不是 fully self-optimizing。

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

1. `Hydration Pipeline` 拆分：继续把 `l1_meta_hydration.py` 中的插件执行、claim/conflict、settlement 分段拆出。
2. `Experiment Runner`：对候选参数跑 synthetic + practitioner benchmark。
3. `Learning Scorecard`：记录每轮参数变更对 benchmark 和 synthetic 的改善/退化。

---

## 9. Parameter Candidate Runner

实现：

- `testing/parameter_candidate_runner.py`

协议版本：

- `v17.parameter_candidate_runner.v1`

职责：

- 消费 `Synthetic Tuning Bridge` 的参数族热点。
- 生成只读实验计划。
- 明确候选参数范围、回归命令、安全门。

当前输出：

- `experiment_id`
- `parameter_family`
- `hypothesis`
- `candidate_patch`
- `synthetic_cases`
- `benchmark_cases`
- `required_commands`
- `safety_gates`
- `application_mode = dry_run_plan_only`

安全边界：

- 不写配置。
- 不自动应用参数。
- 不绕过人工 review。
- 所有 candidate patch 均为 `review_only`。

---

## 10. Synthetic Batch Lab

实现：

- `testing/synthetic_batch_lab.py`
- `scripts/render_synthetic_batch_report.py`

协议版本：

- `v17.synthetic_batch_lab.v1`

职责：

- 批量运行一组代表性 synthetic cases。
- 检查基础不变量：
  - 总量有限且为正
  - 十神分数有限且非负
  - `climate_field` 存在且数值有限
  - 预期 relation / dynamics family 必须出现
  - 禁止 family 不得出现
  - relation summary 数值不越界
- 将异常映射到参数族。
- 调用 `Synthetic Tuning Bridge` 和 `Parameter Candidate Runner` 生成 review-only 调参实验。

当前默认批量覆盖：

- 三合可见 / 不可见
- 三会完整 gate
- 三会误判防线
- 六合原局 / 大运 / 流年
- 冲 / 害
- 寒湿 / 燥热调候场

第一阶段安全边界：

- 不写配置。
- 不自动调整参数。
- 只生成 `parameter_candidate_plan` 与 `parameter_experiments`。

---

## 11. Auto Learning Cycle

实现：

- `testing/parameter_sandbox.py`
- `testing/auto_learning_loop.py`
- `scripts/run_auto_learning_cycle.py`

协议版本：

- `v17.parameter_sandbox.v1`
- `v17.auto_learning_loop.v1`

职责：

- 自动运行 Synthetic Batch Lab。
- 如果基线全绿，则输出 `baseline_green_no_parameter_tuning`。
- 如果出现异常，则读取 `parameter_experiments`。
- 对可数值调参的候选，在内存里临时覆盖常数，重新跑批量样盘。
- 对 gate / 语义 / 法理类问题，生成 `analyst_feedback_items`。

安全边界：

- 沙盒只 monkeypatch 当前进程的配置读取。
- 不写 `v17_core_constants.json`。
- 不自动应用任何候选。
- `can_auto_apply` 永远是 `false`，直到裁决者明确授权下一阶段。

运行：

```bash
python3 qiazhi/v17_rebirth/scripts/run_auto_learning_cycle.py
```

---

## 12. Learning Campaign

实现：

- `testing/learning_campaign.py`
- `scripts/run_learning_campaign.py`

协议版本：

- `v17.learning_campaign.v1`

定位：

> 把插件治理、Synthetic Batch、完整 Synthetic Lab、真实命盘 Benchmark、Auto Learning Cycle 组织成一次可审计学习活动。

设计目标：

1. 自动跑起来，但不自动上线参数。
2. 3 小时以内完成一轮默认学习活动。
3. 先生成给 Codex 主审的报告，再交给分析师复核。
4. 冲突、gate、语义和非数值问题进入 `analyst_feedback_items`。
5. LLM 只作为可选审阅者，不允许输出直接配置补丁。

默认覆盖：

- `plugin_governance_coverage`
- `synthetic_batch`
- `extended_synthetic`
- `practitioner_benchmarks`
- `auto_learning_loop`
- `learning_insights`
- `parameter_experiments`
- `llm_review_package`

核心输出：

- `scorecard`
- `learning_value`
- `learning_density`
- `validated_parameter_families`
- `top_learning_signals`
- `blind_spots`
- `recommended_next_cases`
- `parameter_family_counts`
- `analyst_feedback_items`
- `llm_review_package`
- `safety_gates`

报告口径：

- `green` 不再只表示“全绿”，还必须说明本轮验证了哪些参数族。
- `Learning Signals` 优先展示高信息密度样盘，不按 catalog 原始顺序机械罗列。
- `Next Hard Cases` 必须给出下一轮主动挑战方向，即使本轮没有异常。
- `Parameter Health` 只在发现异常时生成影子参数实验；全绿时保持参数冻结。
- `Parameter Optimization Guidance` 必须区分：冻结参数族 / 重点观察参数族 / 正式调参候选参数族。
- `Parameter Optimization Map` 必须把重点参数族映射到目标配置、参数名、Synthetic case 与 Benchmark case。

安全边界：

- `can_auto_apply = false`
- `sandbox_only`
- `do_not_write_real_config`
- `codex_primary_review_required`
- `analyst_review_for_uncertain_or_conflicting_cases`
- `manual_approval_required_before_apply`

运行：

```bash
# Markdown 报告，默认 180 分钟预算
python3 qiazhi/v17_rebirth/scripts/run_learning_campaign.py

# JSON 报告
python3 qiazhi/v17_rebirth/scripts/run_learning_campaign.py --json

# 生成可给 LLM/分析师审阅的 review package
python3 qiazhi/v17_rebirth/scripts/run_learning_campaign.py --llm-review

# 写入报告文件
python3 qiazhi/v17_rebirth/scripts/run_learning_campaign.py --write /tmp/v17_learning_campaign.md
```

Admin UI：

- `/v17/admin` 新增 `自动学习` Tab。
- 可配置：
  - 运行预算，默认 180 分钟。
  - 扩展样盘上限。
  - 是否生成 LLM review package。
- 可操作：
  - `开始学习`
  - `暂停`
  - `刷新状态`
  - `复制报告`
- 展示：
  - 当前状态
  - 进度条
  - 预计剩余时长
  - scorecard
  - 参数优化参考（freeze / watch / adjust）
  - 参数优化参考地图（目标文件 / 参数名 / synthetic / benchmark）
  - 影子实验计划（按主看参数族展开）
  - 插件治理覆盖
  - 参数实验数
  - 分析师反馈项
  - Markdown 报告
