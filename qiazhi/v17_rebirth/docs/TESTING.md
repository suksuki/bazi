# V17 Rebirth 自动化测试

## 概览

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

脚本顺序：V17 pytest（默认排除 `integration`）→ 集成标记用例 → 前端 `pnpm test:ci`（ESLint + `next build` + Vitest）。Next.js 16 起 CLI 不再提供 `next lint`，与本仓库 `package.json` 中 `eslint .` 一致。

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
  qiazhi/v17_rebirth/tests/test_synthetic_batch_lab.py -q

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
- `classical.ziping.climate_bridge.v1`
- `classical.ziping.pattern_bridge.v1`
- `classical.ziping.summary.v1`

## UI 验证口径

- `/v17/oracle` 主页面使用 `核心页面 / 辅助页面 / 观测页面` 三 Tab。
- `辅助页面` 必须显示 `Topic Hub / 专题中枢`，覆盖子平、格局、调候、盲派、象法、风险六条专题线。
- `/v17/admin` 的 Core Engine 面板必须显示 `Topic Hub / 专题状态表`，用于核对 authority 层级与专题边界。
- 前端验收以 `pnpm --dir qiazhi/v17_rebirth/frontend build` 为硬线。
