# DeepBazi V50

DeepBazi V50 是一个由 Abu 引导、以 LLM 为命理认知核心的八字与紫微综合系统。

<!-- V50_EXECUTION_STATE:START -->
## Machine-Synchronized Execution State

> Source: `config/v50_execution_state.yaml` · SHA-256 `2ac9f2ea5608` · Updated `2026-07-21`

```yaml
canonical_product_target: Life Script Case Workspace
current_product_surface: legacy_l5_plus_experience_shell
case_workspace_status: ISOLATED_DESIGN_STUDY_IMPLEMENTED_PRODUCTION_NOT_STARTED
product_model: one_case_workspace
mingli_world: one_canonical_mingli_world
r1_human_product_gate: CANCELED_NO_SCHEDULE
architecture_consolidation_gate: IN_PROGRESS
professional_blind_gate: PENDING
public_professional_release: BLOCKED
full_regression: 479_PASSED_CAG04_FINAL
```

Authorized now:

- `CAG_04_ARCHITECTURE_REVIEW`: relation_path_identity_provenance_lifecycle_historical_stability_closeout

Next architecture slice: `CAG_05_SCHEMA_MODULE_OWNERSHIP` after `explicit_gate_decision_after_cag_04_architecture_review`.

Blocked: `cag_05_implementation_before_cag_04_review`, `architecture_gate_until_cal_01_resolved_or_explicitly_isolated`, `relation_atlas_ra1`, `relation_core_v2_implementation`, `path_core_v2_implementation`, `mingli_lab_production_engineering`, `production_workspace_migration`, `frontend_framework_migration`, `self_healing_platform_or_product_subsystem`, `new_product_ui_animation_or_interaction`, `public_release`.
<!-- V50_EXECUTION_STATE:END -->

## 主链

```text
出生信息
→ 八字 / 紫微确定性事实
→ Graph / Path / Role / Ablation 工具观察
→ 最小命理世界上下文
→ LLM 发现 Pattern、比较 Hypothesis、形成主做功
→ 八字 / 紫微交叉推理
→ 先验断言、Probe、事业与财富专题
→ Abu 分阶段交付与案例级修正
```

系统不再使用旧的确定性 Brain、模板化 Reading、Product Mode Projection 或 LLM 仅表达链。

## 人生领域

领域空间统一定义在 `packages/core/life_domains.py`：

```text
整盘命局
自我与性情
天赋与学习
事业与职业
财富与资源
亲密关系
家庭与原生关系
子女与传承
健康与生命力
社交与合作
迁移与环境
人生阶段与时机
```

领域存在不等于已经公开成熟。每个领域分别声明认知准备度、公开状态和禁止越过的边界。

## 保留的命理资产

- 历法、四柱、藏干、十神等确定性事实；
- 官方 `iztro@2.5.8` 紫微排盘桥；
- Graph、Path、Role、Ablation、Mechanism AST 与 Timing 候选工具；
- 命理知识卡、合成命盘和受控变体；
- LLM Mingli Agent、Epistemic Review、案例记忆和 Probe；
- Abu 导航、账户与八字档案。

## 安装紫微桥

```bash
cd tools/ziwei-iztro
npm install --ignore-scripts
```

## 启动

```bash
PYTHONPATH=packages:apps ../.venv312/bin/python scripts/v50_run_product.py
```

打开：`http://127.0.0.1:8053/`

默认使用本地 PostgreSQL：`postgresql:///qiazhi_v50?host=/tmp`。部署环境必须显式提供 `V50_DATABASE_URL`。

## 验证

```bash
PYTHONPATH=packages:apps:tests ../.venv312/bin/pytest -q
```

测试只保护当前命理世界、工具、Agent、Abu 与正式产品入口，不再保护已删除的旧架构。
