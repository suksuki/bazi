# V30 紫微 Domain Lens 主线设计

更新时间：2026-06-30

## 一句话结论

紫微不是第二套主引擎，也不是独立报告。V30 当前阶段把紫微定位为 `Domain Lens`：

```text
八字主引擎
-> Decision Engine 裁决
-> Reality Probe / 用户反馈校准
-> LLM 负责表达

紫微 Domain Lens
-> 事实层排盘
-> 辅助信号
-> Probe 触发候选
-> 训练与冲突观察
```

紫微 V1 决策权重固定为 `0`，只能进入 Signal Registry 和命理师/admin 观察，不允许直接改变最终断语、建议、用神、路径或隐藏属性。

## 核心边界

- 八字仍是主引擎；紫微只提供旁路观察和领域镜头。
- LLM 不做最终命理决策，只做表达、解释、对话措辞和边界复核。
- 中枢大脑不直接凭紫微改结论；它只负责调度、记录冲突、触发必要追问和训练样本。
- Reality Probe 权重高于紫微。用户真实回答与八字主链一致时，紫微冲突只能进入低权重观察。
- 普通用户默认不看星曜表和生硬宫位；命理师模式可以看紫微信号表、冲突、候选问题和采纳动作。

## 标准冻结 V1

V1 先冻结系统标准，避免后续“算出来不同”的根基问题：

- 历法标准：出生输入先完成历法转换，紫微只消费明确的出生事实。
- 闰月处理：必须显式记录，不允许静默换月。
- 时辰边界：两小时地支边界必须记录，子时边界策略进入 trace。
- 真太阳时：只能显式启用，不能默认假设。
- 命宫/身宫安法：固定 `ming_gong_shen_gong_standard_v1`。
- 十四主星安法：V0 只落十四主星。
- 生年四化表：V0 必须有禄权科忌。
- 大限起法：固定 `da_xian_direction_and_start_age_standard_v1`。

## 分期

### ZW-0 事实层

目标：

- 生成十二宫、命宫、身宫、十四主星、生年四化、大限/流年宫位。
- 只产生事实，不产生判断。
- 输出 `ZiweiChart`，标记缺失事实和 guardrail。

状态：本轮先落契约与标准，不接完整排盘算法。

### ZW-1 信号层

目标：

- 先用 36 条领域规则把紫微事实转成 `ZiweiSignal`。
- 六个领域：财富、事业、关系、迁移/外部机会、健康压力、田宅资产。
- 每条规则必须绑定 `claim_key`、`probe_trigger`、`hidden_attribute_keys`。

状态：本轮落 36 条规则和 Probe 映射。

### ZW-2 旁路接入

目标：

- `ZiweiSignal -> BaziSignal` adapter。
- `source_module = ziwei_domain_lens`。
- `source_type = ziwei_signal`。
- `decision_weight = 0`。
- 进入 Signal Registry 后仍不改变 Decision Engine 分数和 Verdict。

状态：本轮落最小 adapter 和专项测试。

### ZW-3 UI 与 Admin

目标：

- 普通用户只看一行辅助提示，不展示紫微星曜细节。
- 命理师模式展示信号表：宫位、星曜/四化、领域、claim_key、强度、置信度、与八字 Verdict 的一致/冲突、Probe、操作。
- Admin/Lab 展示紫微与八字/Reality Probe 的冲突样本，用于训练评估。

状态：后续阶段接页面流程和 admin 观察，不在本轮直接改主 UI。

## 36 条 V1 领域规则

财富：

- `ZW-WEALTH-01` 财帛宫化禄 -> `ziwei_wealth_resource_opportunity` -> `wealth_source_probe`
- `ZW-WEALTH-02` 财帛宫化忌 -> `ziwei_wealth_blockage_or_leakage` -> `wealth_capture_probe`
- `ZW-WEALTH-03` 官禄宫化禄/化权联动财帛 -> `ziwei_career_driven_wealth` -> `career_income_source_probe`
- `ZW-WEALTH-04` 迁移宫化禄联动财帛 -> `ziwei_external_wealth_opportunity` -> `external_opportunity_probe`
- `ZW-WEALTH-05` 交友宫化忌联动财帛 -> `ziwei_peer_money_friction` -> `partnership_money_probe`
- `ZW-WEALTH-06` 田宅宫化禄/禄存入田宅 -> `ziwei_property_asset_opportunity` -> `property_asset_probe`

事业：

- `ZW-CAREER-01` 官禄宫化禄 -> `ziwei_career_opportunity` -> `career_path_probe`
- `ZW-CAREER-02` 官禄宫化权 -> `ziwei_career_authority_pressure` -> `authority_pressure_probe`
- `ZW-CAREER-03` 官禄宫化忌 -> `ziwei_career_blockage` -> `career_obstacle_probe`
- `ZW-CAREER-04` 父母宫化科/文昌文曲入父母或官禄 -> `ziwei_institutional_recognition` -> `platform_support_probe`
- `ZW-CAREER-05` 交友宫吉辅支持官禄 -> `ziwei_network_career_support` -> `team_support_probe`
- `ZW-CAREER-06` 迁移宫化权/化禄支持官禄 -> `ziwei_external_career_driver` -> `external_career_probe`

关系：

- `ZW-REL-01` 夫妻宫化禄 -> `ziwei_relationship_attraction_or_resource` -> `relationship_mode_probe`
- `ZW-REL-02` 夫妻宫化权 -> `ziwei_relationship_power_pressure` -> `relationship_pressure_probe`
- `ZW-REL-03` 夫妻宫化忌 -> `ziwei_relationship_blockage` -> `relationship_obstacle_probe`
- `ZW-REL-04` 福德宫化忌联动夫妻 -> `ziwei_relationship_emotional_load` -> `emotional_security_probe`
- `ZW-REL-05` 迁移宫信号联动夫妻 -> `ziwei_relationship_mobility_factor` -> `relationship_distance_probe`
- `ZW-REL-06` 财帛宫化忌联动夫妻 -> `ziwei_relationship_money_pressure` -> `relationship_resource_probe`

迁移/外部机会：

- `ZW-MOB-01` 迁移宫化禄 -> `ziwei_external_opportunity` -> `mobility_opportunity_probe`
- `ZW-MOB-02` 迁移宫化权 -> `ziwei_external_pressure_driver` -> `external_pressure_probe`
- `ZW-MOB-03` 迁移宫化忌 -> `ziwei_mobility_blockage` -> `mobility_blockage_probe`
- `ZW-MOB-04` 迁移宫联动财帛 -> `ziwei_external_market_wealth` -> `external_wealth_probe`
- `ZW-MOB-05` 迁移宫联动官禄 -> `ziwei_external_career_opportunity` -> `external_career_probe`
- `ZW-MOB-06` 田宅宫化忌 + 迁移宫强 -> `ziwei_home_mobility_tension` -> `home_mobility_probe`

健康压力：

- `ZW-HEALTH-01` 疾厄宫化忌 -> `ziwei_health_pressure_signal` -> `stress_manifestation_probe`
- `ZW-HEALTH-02` 疾厄宫化权 -> `ziwei_overwork_or_tension` -> `overwork_pattern_probe`
- `ZW-HEALTH-03` 福德宫化忌 -> `ziwei_mental_load_or_recovery_issue` -> `recovery_capacity_probe`
- `ZW-HEALTH-04` 官禄宫化忌联动疾厄 -> `ziwei_work_pressure_health_cost` -> `work_stress_probe`
- `ZW-HEALTH-05` 财帛宫化忌联动福德/疾厄 -> `ziwei_money_pressure_health_cost` -> `money_stress_probe`
- `ZW-HEALTH-06` 福德宫化禄 -> `ziwei_recovery_resource` -> `recovery_style_probe`

田宅资产：

- `ZW-PROP-01` 田宅宫化禄 -> `ziwei_property_opportunity` -> `property_asset_probe`
- `ZW-PROP-02` 田宅宫化权 -> `ziwei_property_control_pressure` -> `property_pressure_probe`
- `ZW-PROP-03` 田宅宫化忌 -> `ziwei_property_blockage` -> `property_blockage_probe`
- `ZW-PROP-04` 父母宫化禄/化科联动田宅 -> `ziwei_family_asset_support` -> `family_asset_probe`
- `ZW-PROP-05` 财帛宫化忌联动田宅 -> `ziwei_cashflow_asset_tension` -> `cashflow_asset_probe`
- `ZW-PROP-06` 迁移宫强联动田宅 -> `ziwei_property_mobility_link` -> `home_mobility_probe`

## 与 Reality Probe 的关系

```text
ZiweiSignal supports + 用户支持
-> 提升该隐藏属性/建议角度的 confidence，但不改命盘事实

ZiweiSignal supports + 用户反向
-> 原信号保留，manifestation 降权为 not_yet_manifested / context_blocked

ZiweiSignal 反向 + 用户支持 + 八字支持
-> 紫微信号质量降权，生成冲突训练样本

ZiweiSignal 与八字 Verdict 冲突
-> 默认只给命理师/admin 看，不直接给普通用户
```

## 后续任务

- `ZW-0`：补紫微标准文档和 `v30.ziwei.standards`。
- `ZW-1`：补契约 `ZiweiChart / ZiweiSignal / ZiweiProbeMapping`。
- `ZW-2`：补 36 条领域规则。
- `ZW-3`：补 Probe mapping。
- `ZW-4`：补 `ZiweiSignal -> BaziSignal` adapter。
- `ZW-5`：接 Admin/Lab 旁路观察表。
- `ZW-6`：补 golden cases 验证与紫微/八字/Reality Probe 冲突训练样本。

本轮执行 `ZW-0` 到 `ZW-4`，并用专项测试保证不会影响主引擎 Verdict。
