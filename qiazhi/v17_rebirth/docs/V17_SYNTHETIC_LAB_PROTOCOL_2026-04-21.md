# V17 Synthetic Lab Protocol

## Why

真实八字样本太“脏”：

- 古典口径本身存在分歧。
- 同一命盘往往同时混入静态根气、关系成局、做功链路、流年引动。
- 一次校盘很难判断到底是算法错、参数错，还是样本本身过于复杂。

所以 V17 的智能弹性框架必须先有一个 **Synthetic Lab**。  
它的职责不是替代真实校盘，而是先在“可控世界”里把系统的物理和认知路径训稳。

## Goal

Synthetic Lab 负责四件事：

1. 固定一批可重复、可回归的合成样盘。
2. 明确每个样盘只想验证什么，不混入无关变量。
3. 让引擎、插件、推理链都能在同一批样盘上被复核。
4. 为后续学习/演化提供干净基线，再去碰真实世界的复杂命盘。

2026-04-23 起，Synthetic Lab 增加 `Synthetic Tuning Bridge`：

- 读取真实命盘 benchmark 的偏差。
- 将偏差映射到 `relation_formation.* / relation_dynamics.* / ten_gods.calibration / authority.*` 等参数族。
- 根据参数族推荐应回归的 synthetic cases。
- 第一阶段只提出调优方向，不自动改参数。

## Case Contract

每一个合成样盘都遵循同一份协议：

```python
SyntheticCase(
    case_id="l1.relation.sanhe.month_visible",
    layer="L1",
    description="巳酉丑三合金局，月干辛金透出，验证三合月干满配上限。",
    four_pillars={"year": "...", "month": "...", "day": "...", "hour": "..."},
    luck_pillar="—",
    flow_pillar="—",
    gender="male",
    tags=("relation", "sanhe", "month_visible"),
    expected_relation_families=("sanhe",),
    expected_dynamic_families=(),
)
```

字段语义：

- `case_id`: 永久 ID，不随文案变化。
- `layer`: 所属实验层，当前用 `L0 / L1 / L2 / MASTER`。
- `description`: 这个样盘到底想验证什么。
- `four_pillars / luck_pillar / flow_pillar`: 可控输入。
- `tags`: 检索维度。
- `expected_relation_families`: 该样盘必须出现的关系家族。
- `expected_dynamic_families`: 该样盘必须出现的关系动力学家族，用于 `chong / hai / po / ke / stem_fusion_transform` 这类不以 formation bucket 为主目录的关系。

## Layer Design

### L0 Static Basis

验证：

- 通根 vs 虚浮
- 透干 vs 未透
- 月令只影响本柱/本支，不得错误扩散到同五行全局
- 日干不参与静态十神显化分，但可保留为动态计算参考体

当前基线样盘：

- `l0.static.floating_peer`
- `l0.static.rooted_peer`

### L1 Relation Families

验证：

- 三合 / 三会 / 半合 / 拱合 / 六合是否命中
- 月干透出 > 日干透出 > 其他柱位透出
- 重支加成与中神/墓库/起点权重
- 冲刑害破的衰减是否合理
- 合化信息是否准确进入 `relation_formation_summary`

当前基线样盘：

- `l1.relation.sanhe.no_visible`
- `l1.relation.sanhe.day_visible`
- `l1.relation.sanhe.month_visible`
- `l1.relation.sanhui.month_visible`
- `l1.relation.liuhe.baseline`
- `l1.relation.banhe.shengwang`
- `l1.relation.banhe.muwang`
- `l1.relation.gonghe.baseline`
- `l1.relation.anhe.baseline`
- `l1.relation.stem_fusion.runtime`
- `l1.relation.chong.baseline`
- `l1.relation.xing.baseline`
- `l1.relation.hai.baseline`
- `l1.relation.po.baseline`
- `l1.relation.ke.baseline`

2026-04-22 起，L1 Relation Families 进入第二阶段：`relation family full matrix`。

这批矩阵的目标不是只看“三合/三会”，而是把关系家族按工程协议拆开：

- `liuhe`
- `banhe_shengwang`
- `banhe_muwang`
- `gonghe`
- `anhe`
- `stem_fusion_transform`
- `chong`
- `xing`
- `hai`
- `po`
- `ke`

其中：

- `liuhe / banhe / gonghe` 继续以 `relation_formation_summary` 为主目录
- `stem_fusion_transform / chong / hai / po / ke` 以 `relation_dynamics_summary` 为主目录
- `stem_fusion_transform` 同时要求进入 `relation_visible_bonuses`

这样可以避免把“地支成局”和“天干五合转化”硬塞进同一个 formation bucket。

补充口径（2026-04-22）：

- `三会` 当前只在三支齐全时进入 `sanhui` 主家族。
- 两支会气、重支叠加，不再冒充 `sanhui` 摘要。
- 如果后续要做“会气候选”，必须另立 family，不得继续污染 `三会局` 主摘要。

### L2 Judgment Plugins

验证：

- 判定型插件是否正确“描述事实”，而不是错误篡改静态能量
- 插件 claim 是否能进入冲突层
- 插件是否对用神/忌神/通关神判定提供合理偏置

当前基线样盘：

- `l2.judgement.officer_exhaust_pair`
- `l2.judgement.owl_food`
- `l2.authority.bias_reroute`
- `l2.authority.tongguan_present`
- `l2.authority.blind_theme_parallel`
- `l2.pattern.shishen_zhisha`
- `l2.pattern.shangguan_peiyin`
- `l2.pattern.caipoyin`

2026-04-22 起，L2 合成样盘还要额外固定两条协议：

- `judgement_bias_protocol`
  - judgement 插件是否按 `bias / evidence / narrative hint` 输出
- `stage_bias_protocol`
  - 阶段势是否只进入 authority，而不回写底层物理
- `blind_bias_protocol`
  - 盲派主题是否以 `bias_only` 方式并行推用/推忌，而不覆盖子平 authority

2026-04-22 晚间补充：

- `pattern_specializations` 进入 Synthetic Lab 主矩阵，不再只靠零散单元测试
- `专题插件事实 -> judgement bias -> authority` 成为正式回归链
- 当前已固定三类专题样盘：
  - `食神制杀`
  - `伤官配印`
  - `财破印`
- 这意味着实验室现在不只验证“插件能不能命中”，还验证“插件命中后会不会正确改写 authority 候选方向”

### MASTER Reasoning

验证：

- 一张复杂样盘是否能同时输出多条结构摘要
- `master_reasoning`、`learning_hooks`、`ledger` 是否仍保持契约稳定
- 系统能否把“命理师思维轨迹”拆成可观察的 reasoning / learning signal

当前基线样盘：

- `runtime.relation.liuhe.natal_baseline`
- `runtime.relation.liuhe.luck_background`
- `runtime.relation.liuhe.flow_trigger`
- `runtime.relation.hai.natal_baseline`
- `runtime.relation.hai.luck_background`
- `runtime.relation.hai.flow_trigger`
- `runtime.relation.sanhui.resonance`
- `runtime.relation.banhe.interruption`
- `master.branch_cluster.fire_vs_water`

2026-04-22 起，MASTER 层开始承接 `runtime-field matrix`：

- 同一组关系分别落在 `luck_background / flow_trigger`
- 补齐 `natal / luck / flow` 的同关系梯度
- 校验 `大运 = 背景场`、`流年 = 扰动触发`
- 校验图边 metadata 与 relation summary 同口径
- 校验 `resonance / interruption` 在 formation 与 dynamics 两个摘要里同时可见

### MASTER Work-Authority Matrix

验证：

- 做功路径是否会把高能低稳与低能高稳区分开
- authority 是否会沿着 `contest / positive_path / tongguan_present` 给出不同裁决
- `effect_scores / use_candidates / taboo_candidates / core paths preview` 是否同口径

当前基线样盘：

- `core.authority.officer_contest`
- `core.authority.positive_path`
- `core.authority.bridge_present`
- `core.authority.bridge_external`

## Runtime Outputs

Synthetic Lab 不是只看最后分数，而是同时检查：

- `scores`
- `top`
- `relation_formation_summary`
- `runtime_field_protocol`
- `judgement_bias_protocol`
- `stage_bias_protocol`
- `pattern_candidate / god_ring_bias / authority reroute`
- `master_reasoning`
- `ledger`
- `meta_contract`
- `plugin_governance`
- `synthetic_tuning_bridge`

这意味着它既能校验“算得对不对”，也能校验“系统是不是沿着正确轨迹在思考”。

## Current Runner

```bash
bash qiazhi/v17_rebirth/scripts/run_synthetic_lab.sh
```

等价命令：

```bash
pytest qiazhi/v17_rebirth/tests -m synthetic -q
```

## Current Baseline

2026-04-21 起，Synthetic Lab 已正式纳入：

- 合成关系测试：`test_synthetic_visibility_cases.py`
- 合成关系聚焦测试：`test_synthetic_relation_focus.py`
- 合成三合投影测试：`test_synthetic_sanhe_projection.py`
- 合成样盘矩阵：`test_synthetic_lab_matrix.py`
- 合成关系家族矩阵：`test_synthetic_relation_family_matrix.py`
- 合成关系动力学矩阵：`test_synthetic_relation_dynamics_matrix.py`
- 合成运流场矩阵：`test_synthetic_runtime_field_matrix.py`
- 合成判定层矩阵：`test_synthetic_judgement_lab.py`
- 合成做功与 authority 矩阵：`test_synthetic_work_authority_matrix.py`
- 主审盘推理链：`test_master_reasoning.py`
- 演化账本：`test_evolution_ledger.py`
- authority judgement 协议：`test_authority_judgement_protocol.py`

## Contribution Rule

以后任何涉及以下内容的调整，都应该先补 Synthetic Lab，再去碰真实命盘：

- 十神基础算法
- 关系类成局算法
- 做功/传导/通关逻辑
- 判定型插件
- 用神 / 忌神 / 通关神路由
- judgement bias / stage bias 协议

原则很简单：

## Practitioner Benchmark Bridge

从 2026-04-23 起，Synthetic Lab 不再是“最终一站”。

V17 现在明确采用两段式验证：

1. `Synthetic Lab`
   - 负责干净世界、单变量、关系矩阵、authority 协议的稳定性
2. `Practitioner Benchmark`
   - 负责真实命盘、多路结构并存、命理师审盘轨迹的复杂盘回归

也就是说：

- Synthetic Lab 负责“规则别坏”
- Practitioner Benchmark 负责“复杂盘别跑偏”

真实命盘基准协议见：

- `qiazhi/v17_rebirth/docs/V17_PRACTITIONER_BENCHMARK_PROTOCOL_2026-04-23.md`

1. 先造一个最小可控样盘。
2. 再写断言，固定预期。
3. 跑 Synthetic Lab。
4. 最后再用真实命盘做“命理师校盘”。

这就是 V17 智能系统的第一层学习闭环。
