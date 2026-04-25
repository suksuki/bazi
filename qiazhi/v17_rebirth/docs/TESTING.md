# V17 Rebirth 自动化测试

## 概览

当前用户验收用例见：[V17_USER_ACCEPTANCE_USE_CASES_2026-04-24.md](V17_USER_ACCEPTANCE_USE_CASES_2026-04-24.md)。

| 层级 | 技术 | 路径 / 命令 |
|------|------|----------------|
| 后端单元 / 契约 | pytest | `qiazhi/v17_rebirth/tests/` |
| 后端集成 | pytest + `TestClient` | `-m integration` |
| 回归契约 | pytest | `-m regression` |
| 前端单元 | Vitest | `qiazhi/v17_rebirth/frontend/tests/` |

仓库根 `pytest.ini` 已将 `qiazhi` 加入 `pythonpath`，包导入形式为 `from v17_rebirth...`。

## 一键脚本

```bash
bash qiazhi/v17_rebirth/scripts/run_automated_tests.sh
```

脚本顺序：V17 pytest（默认排除 `integration`）→ 集成标记用例 → 插件参数审计门禁 → relation origin trend 门禁 → 前端 `pnpm test:ci`（ESLint + `next build` + Vitest）。Next.js 16 起 CLI 不再提供 `next lint`，与本仓库 `package.json` 中 `eslint .` 一致。

脚本优先使用 `qiazhi/.venv/bin/python`；如果 venv 不存在，才回退到系统 `python3/python`。这样 macOS 与 0.13 Linux 服务器可以共用同一条测试命令。

脚本会在 Relation Origin Gate 之前执行插件参数审计门禁：`scripts/audit_plugin_params.py` 的 `declared_but_unused` 不能包含任何项；一旦发现未接线参数，会直接中止自动化流程并输出失败原因。

## Synthetic Lab

合成样盘实验室用于校验“智能弹性框架”里的可控世界，不让真实八字的噪声污染基础算法判断。

```bash
# 只跑合成样盘实验室
bash qiazhi/v17_rebirth/scripts/run_synthetic_lab.sh

# 等价命令
pytest qiazhi/v17_rebirth/tests -m synthetic -q

# 运行批量 synthetic lab 报告
python3 qiazhi/v17_rebirth/scripts/render_synthetic_batch_report.py

# 运行自动学习闭环（只读 / 沙盒 / 不写配置）
python3 qiazhi/v17_rebirth/scripts/run_auto_learning_cycle.py

# 只跑关系家族矩阵
pytest qiazhi/v17_rebirth/tests/test_synthetic_lab_matrix.py \
  qiazhi/v17_rebirth/tests/test_synthetic_relation_family_matrix.py \
  qiazhi/v17_rebirth/tests/test_synthetic_relation_dynamics_matrix.py \
  qiazhi/v17_rebirth/tests/test_synthetic_runtime_field_matrix.py \
  qiazhi/v17_rebirth/tests/test_synthetic_work_authority_matrix.py \
  qiazhi/v17_rebirth/tests/test_synthetic_pattern_specialization_lab.py -q
```

Synthetic Lab 当前覆盖：

- L0 静态基础：通根 / 虚浮 / 透干
- L0 调候场：`thermal_index / moisture_index / climate_tension / climate_modifier_layer`
- L0/L2 调候作用链：`climate_modifier_layer -> authority_use_score / authority_taboo_score -> pattern_survival_delta`
- L2 调候专题：`climate_theme_core + classical.climate.*` 的 Prompt / UI / Admin 对齐
- L1 关系家族：三合 / 三会 / 六合 / 半合 / 拱合 / stem_fusion runtime
- L1 关系动力学：暗合 / 冲 / 刑 / 害 / 破 / 克 双轴摘要
- Core 运流协议：原局 / 背景场 / 年度扰动 / runtime_cascade / resonance / interruption
- L2 判定层：`risk_matrix` 偏置、authority 用神/忌神/通关神
- L2 专题插件：`食神制杀 / 伤官配印 / 财破印` 的 fact -> bias -> authority 闭环
- Core 做功与 authority：`contest / positive_path / tongguan_present / tongguan_external`
- Authority Judgement 协议：`judgement_bias_protocol / stage_bias_protocol`
- Authority Layer 协议：`authority_layer_protocol / max_bias_ratio / override_forbidden`
- Learning Governance：`plugin_governance / meta_contract / synthetic_tuning_bridge`
- 调候驱动 authority 回归：`test_effect_resolver_candidates.py`、`test_l2_blind_ziping_protocol.py`
- 子平 umbrella 专题：`month_command / balance / climate_bridge / pattern_bridge / yongshen / god_ring_resolver / summary`
- Master Reasoning：主审盘推理链与 learning hook
- Evolution Ledger：演化账本契约
- 盲派专题：`blind_theme` 独立专题、最终/临时元数据分层、Prompt 合同出口、`blind_bias_protocol -> authority` 并行桥接
- 象法专题：`xiangfa_theme` semantic-only 专题、最终/临时元数据分层、Prompt 合同出口、禁止进入 bias/authority
- Synthetic Batch Lab：批量样盘不变量、异常到参数族映射、review-only 调参实验单
- Auto Learning Loop：自动运行批量样盘，沙盒评估候选参数，并输出 analyst feedback items

设计协议见：

- `qiazhi/v17_rebirth/docs/V17_SYNTHETIC_LAB_PROTOCOL_2026-04-21.md`

## Practitioner Benchmark

真实命盘校盘基准集用于在 Synthetic Lab 之后，继续校验“复杂盘是否沿着命理师的审盘轨迹运行”。

```bash
# 只跑真实命盘校盘基准
bash qiazhi/v17_rebirth/scripts/run_practitioner_benchmarks.sh

# 等价命令
pytest qiazhi/v17_rebirth/tests/test_practitioner_benchmark_cases.py -q

# 输出当前校盘基准报告
python3 qiazhi/v17_rebirth/scripts/render_practitioner_benchmark_report.py
```

当前首批基准盘覆盖：

- `丁巳 / 乙巳 / 乙丑 / 乙酉 · 庚子 / 丙午`
- `丁巳 / 乙巳 / 乙丑 / 乙酉 · 辛丑 / 乙未`
- `壬寅 / 甲辰 / 丙子 / 甲午 · 庚戌 / 丙午`

协议见：

- `qiazhi/v17_rebirth/docs/V17_PRACTITIONER_BENCHMARK_PROTOCOL_2026-04-23.md`
- `qiazhi/v17_rebirth/docs/V17_PRACTITIONER_BENCHMARK_AUDIT_2026-04-23.md`

## 常用命令

```bash
# 仅 V17 后端（快速，不含 integration）
pytest qiazhi/v17_rebirth/tests -m "not integration" -q

# 含 FastAPI /health 集成
pytest qiazhi/v17_rebirth/tests -m integration -q

# 全量 V17 测试目录
pytest qiazhi/v17_rebirth/tests -q

# 仅运行 runtime-field / 六柱时空核心契约
pytest qiazhi/v17_rebirth/tests/test_runtime_field_protocol.py qiazhi/v17_rebirth/tests/test_six_pillar_spacetime_core.py -q

# 仅运行 authority judgement 协议 / routing / canonical prompt
pytest qiazhi/v17_rebirth/tests/test_authority_judgement_protocol.py \
  qiazhi/v17_rebirth/tests/test_authority_layer_protocol.py \
  qiazhi/v17_rebirth/tests/test_climate_field_protocol.py \
  qiazhi/v17_rebirth/tests/test_climate_theme_core.py \
  qiazhi/v17_rebirth/tests/test_blind_school_core.py \
  qiazhi/v17_rebirth/tests/test_xiangfa_theme_core.py \
  qiazhi/v17_rebirth/tests/test_brain_routing.py \
  qiazhi/v17_rebirth/tests/test_physics_canonical.py \
  qiazhi/v17_rebirth/tests/test_llm_micro_client_prompt.py -q

# 仅运行学习治理层契约
pytest qiazhi/v17_rebirth/tests/test_plugin_governance_protocol.py \
  qiazhi/v17_rebirth/tests/test_meta_contract.py \
  qiazhi/v17_rebirth/tests/test_synthetic_tuning_bridge.py \
  qiazhi/v17_rebirth/tests/test_hydration_pipeline.py \
  qiazhi/v17_rebirth/tests/test_parameter_candidate_runner.py \
  qiazhi/v17_rebirth/tests/test_synthetic_batch_lab.py \
  qiazhi/v17_rebirth/tests/test_auto_learning_loop.py \
  qiazhi/v17_rebirth/tests/test_learning_campaign.py -q

# 运行自动学习 Campaign，输出 Codex 主审报告
python3 qiazhi/v17_rebirth/scripts/run_learning_campaign.py

# 输出 JSON 便于系统/分析师二次消费
python3 qiazhi/v17_rebirth/scripts/run_learning_campaign.py --json

# 前端
cd qiazhi/v17_rebirth/frontend && pnpm install && pnpm test

# 前端构建与类型检查
pnpm --dir qiazhi/v17_rebirth/frontend build
```

## 与遗留测试

根目录 `testpaths` 仍包含 `legacy/tests` 等；只跑 V17 时请显式传入路径 `qiazhi/v17_rebirth/tests`，避免拉全仓历史用例。

## 排障

- **ImportError: v17_rebirth**：在仓库根执行 pytest，或设置 `PYTHONPATH=qiazhi`。
- **集成测试失败**：确认未改 `app` 的 `/health` 契约；流式端点需要真实 LLM，默认不在 CI 中覆盖。

## 本轮新增协议

- `v17.climate_field.v1`
- `v17.climate_modifier_layer.v1`
- `v17.authority.layer_protocol.v1`
- `v17.climate.theme.v1`
- `v17.xiangfa.theme.v1`
- `v17.plugin_governance.v1`
- `v17.meta_contract.v1`
- `v17.synthetic_tuning_bridge.v1`
- `v17.hydration_pipeline.v1`
- `v17.parameter_candidate_runner.v1`
- `v17.synthetic_batch_lab.v1`
- `v17.parameter_sandbox.v1`
- `v17.auto_learning_loop.v1`
- `v17.learning_campaign.v1`
- `v17.learning_insights.v1`
- `classical.ziping.climate_bridge.v1`
- `classical.ziping.pattern_bridge.v1`
- `classical.ziping.summary.v1`

## UI 验证口径

- `/login` 与 `/register` 使用 `V17_AuthScreen`，桌面为品牌区 + 表单，手机为紧凑单列表单；语言切换、登录/注册切换和页面内必填错误必须多语言化。
- 当前使用期 `/register` 不显示命理师申请入口，新账号直接进入 `practitioner`；历史 `user` 账号的命理师申请入口应放在 `/v17/oracle` 主页面空白位置，并进入用户权限面板由 manager/admin 批准或驳回。
- 证据链反馈 payload 应带 `v17.evidence.learning_material.v1` 学习素材契约；学习候选应保留 `learning_values / feedback_intents / learning_tags / boundary_tags`，但这些字段只能影响候选归因和审计排序，不能自动改参数。
- 用户权限面板应展示命理师贡献画像：反馈数、案例数、基准候选数、贡献分和等级；没有贡献时不能伪造高可信标签。
- manager/admin 可把真实案例从 `benchmark_candidate` 标记为 `accepted / rejected`；该动作只更新运行时状态和备注，不得自动改静态 benchmark 测试文件。
- manager/admin 可导出 `accepted` 案例为 `v17.practitioner.benchmark_export.v1`；导出包可包含 `PractitionerBenchmarkCase` 片段，但不得自动写入 `testing/practitioner_benchmarks.py`。
- 命理师学习候选应读取贡献画像调整人工复核优先级，并在候选中保留 `contributor_tiers / contributor_reputation_score`；该分数只能影响审计排序，不能自动改参数。
- manager/admin 可对学习候选写入审计意见；`approved_for_experiment` 只能表示准入 shadow run，API 响应必须保留 `applied=false`。
- 已准入实验的学习候选应出现在 dry-run 实验队列中，携带 `candidate_patch.patch_mode=review_only` 和回滚安全门。
- shadow run 评分必须记录 synthetic/practitioner benchmark 是否通过、改善/退化数量和结论；`promote` 不得允许 benchmark 未通过或存在退化。
- admin 发布审批必须先存在通过 synthetic/practitioner benchmark 且无退化的 `promote` scorecard，并记录测试报告和回滚方案；发布记录 API 仍返回 `applied=false`，不得自动写入配置。
- 学习治理审计包导出应包含候选、审计、实验、scorecard、发布记录和 guardrails，供长期归档与版本对照。
- `/v17/oracle` 主页面使用 `命盘总览 / 深度解读 / 幕后观察` 三个角色过滤后的 Tab；手机端必须呈现为明确的横向 Tab，而不是三张大按钮。
- `命盘总览` 的主断言按钮必须显示 `掐指一算`；LLM 生成中必须显示 `正在掐指一算` 并带轻量 loading 动效。
- App 顶部重置入口必须显示 `返回填写八字`，语义上指向出生信息输入页，而不是模糊的刷新/重测。
- `深度解读` 必须显示 `Topic Hub / 专题中枢`，覆盖子平、格局、调候、盲派、象法、风险六条专题线。
- `/v17/admin` 的 Core Engine 面板必须显示 `Topic Hub / 专题状态表`，用于核对 authority 层级与专题边界。
- `/v17/admin` 必须显示 `自动学习` Tab，可配置预算、启动/暂停 Campaign、查看进度、复制 Markdown 报告。
- 自动学习报告必须包含 `Learning Value / Algorithm Intelligence / Learning Signals / Next Hard Cases`，避免只输出无学习价值的绿灯清单。
- `Algorithm Intelligence` 至少要包含 `平均轨迹覆盖率 / 关键路径覆盖率 / 运行态门禁阶段覆盖率 / 重点依赖边`，让报告能区分参数问题与主链顺序问题。
- `Algorithm Intelligence` 还应包含 `Core 关键路径覆盖率 / Core 已验证步骤 / Core 观察步骤`，用于区分 `hydration 主链` 与 `graph -> work_path -> flux -> authority` 做功链问题。
- 自动学习报告应继续包含 `Parameter Optimization Guidance / Parameter Optimization Map`，让报告能直接指导后续参数审计与影子调参。
- `/v17/admin` 的自动学习页应支持点击重点参数族并展开 `Shadow Experiment Plan`，展示目标模块、参数范围、验证样盘、命令建议与安全门禁。
- 八字断言应为精炼短断语；中文 UI prompt 必须包含 `精炼`，英文包含 `concise`，韩文包含 `간결`。
- 阴历排盘必须支持闰月，回归入口为 `tests/test_lunar_calendar_conversion.py`。
- 前端验收以 `pnpm --dir qiazhi/v17_rebirth/frontend build` 为硬线。
