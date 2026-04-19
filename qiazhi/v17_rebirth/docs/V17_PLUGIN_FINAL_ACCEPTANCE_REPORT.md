# V17 插件体系最终收官报告

## 1. 收官结论

本轮插件主线已经达到“可收官、可验收、可继续专题深化”的状态。

这里的“收官”指的是：

1. 插件已经从零散规则堆重构为成体系的插件家族。
2. 参数、条件、匹配度、冲突、重算、观测这六条主链已经统一。
3. 关系类、格局类、子平类、盲派类、风险类、神煞类插件已经开始说同一种结构语言。
4. 前端 `oracle / admin / trace / decision inbox` 已能直接观测插件主落点与簇投影。

这里的“未终局”也要明确：

1. 这不代表所有命理专题都已经达到终局学术形态。
2. 当前 `match_ratio` 仍然是工程化“成立程度”，不是统计学概率。
3. 下一阶段的工作重点，应该是专题校准与案例验证，而不是再回头修插件基础设施。

---

## 2. 本轮完成的核心升级

### 2.1 插件家族化完成

当前插件体系已经形成下列家族：

- L0 基础可视化插件家族
- L1 关系插件家族
- 子平 / 旺衰插件家族
- 格局插件家族
- 盲派插件家族
- 风险 / 冲突 / 神煞插件家族

对应规划文档：

- [V17_PLUGIN_FAMILY_REFACTOR_PLAN.md](/Users/liujin/DEV/AIProjects/bazi/qiazhi/v17_rebirth/docs/V17_PLUGIN_FAMILY_REFACTOR_PLAN.md)

### 2.2 缺失正式插件入口补齐

本轮新增或正式化的重要插件包括：

- `l0.foundation.hidden_stems.v1`
- `l0.foundation.rooted_stems.v1`
- `l0.foundation.exposed_hidden_stems.v1`
- `l0.foundation.month_command.v1`
- `l1.physics.op_branch_liuchong`
- `classical.ziping.month_command.v1`
- `classical.ziping.balance.v1`
- `classical.ziping.yongshen.v1`
- `classical.pattern.axis.v1`
- `classical.pattern.jianlu_yuejie.v1`
- `classical.pattern.congshi.v1`
- `classical.pattern.finance_officer.v1`
- `classical.pattern.resolver.v1`
- `classical.pattern.formation_gate.v1`
- `classical.pattern.break_guard.v1`
- `classical.blind.work_axis.v1`
- `classical.blind.response_chain.v1`
- `classical.blind.symbol_trigger.v1`
- `classical.blind.timing_window.v1`
- `classical.blind.summary.v1`

### 2.3 参数治理完成第一轮制度化

本轮已经完成：

1. 关键插件参数从“声明但未接线”变成“used_and_configurable”。
2. 核心插件要求具备同名配置文件。
3. `SpecValidator` 已对配置缺失、`plugin_id` 不一致等问题给出政策级警告。
4. 核心插件 `policy_valid=true` 已进入测试守卫。

对应文档：

- [V17_PLUGIN_PARAMETER_AUDIT.md](/Users/liujin/DEV/AIProjects/bazi/qiazhi/v17_rebirth/docs/V17_PLUGIN_PARAMETER_AUDIT.md)
- [V17_PLUGIN_DEFAULT_VALUE_DECISIONS.md](/Users/liujin/DEV/AIProjects/bazi/qiazhi/v17_rebirth/docs/V17_PLUGIN_DEFAULT_VALUE_DECISIONS.md)

### 2.4 条件协议完成第一轮硬化

关系类插件已经具备统一条件协议：

- `condition_state`
- `condition_blockers`
- `condition_trigger`

并且已经正式做到：

1. 条件状态会影响 `match_ratio` 与 `impact_ratio`
2. 条件不足时，不再产出可结算 proposal
3. 条件不足时可以只保留 fact，不再穿透到物理层

已接入协议的核心插件：

- `l1.physics.op_branch_sanhe`
- `l1.physics.op_branch_liuhe`
- `l1.physics.op_stem_fusion`
- `l1.physics.op_branch_muku`
- `l1.physics.op_branch_liuhai`
- `l1.physics.op_branch_liupo`

### 2.5 格局专题完成四层闭环

格局专题当前已具备：

1. 候选
2. 裁决
3. 成格条件
4. 破格预警

并且格局候选已经具备进入冲突层的正式身份：

- `pattern_candidate`
- `exclusivity_key=pattern_family`
- `pattern_family_exclusive`

这意味着格局不再只是页面标签，而是正式参与冲突检测与后续裁决。

### 2.6 重算机制完成升级

统一结算已经从旧的“沿 runtime 叠乘”升级成：

```text
L1 Runtime = Recompute(L0 Base, approved proposals)
```

核心意义：

1. 每轮都从 `ten_gods_base_l0` 出发
2. 避免顺序污染与历史 runtime 叠加漂移
3. 可以留下清晰的插件重算账单

当前已经记录：

- `before`
- `after`
- `ratio_total`
- `delta_abs`

对应协议文档：

- [V17_PLUGIN_MATCH_RECOMPUTE_PROTOCOL.md](/Users/liujin/DEV/AIProjects/bazi/qiazhi/v17_rebirth/docs/V17_PLUGIN_MATCH_RECOMPUTE_PROTOCOL.md)

### 2.7 运流正式进入插件几何层

这是本轮最重要的结构升级之一。

当前已经实现：

1. `interaction_v2` 从只看原局四柱，升级为 `interaction_v2.v2`
2. 大运、流年正式进入几何探测层
3. 关系命中可区分来源类型：
   - `natal`
   - `luck_background`
   - `flow_trigger`
   - `mixed`
   - `luck_only`
   - `flow_only`
   - `runtime_pair`
4. 插件匹配度开始识别“运主背景、年主引动”的差别

当前默认权重口径已经调整为：

- 大运：`0.95`
- 流年：`0.38`

也就是说：

- 大运更接近原局背景延续
- 流年更偏触发与引动

### 2.8 簇投影协议完成全链路推广

这是本轮另一个核心升级。

当前插件输出已经统一开始携带：

- `target_god`
- `cluster_projection`
- `projection_share`

已经接入簇投影协议的插件，包括但不限于：

- 三合
- 五合
- 六合
- 六害
- 六破
- 格局专题
- 子平专题
- 盲派专题
- 风险矩阵
- 神煞
- 十神主轴格局

这意味着插件不再只是“命中了一条规则”，而是能说明：

1. 它最终落到哪个十神
2. 如果落到一个簇，簇内各神占比多少
3. 当前主落点的权重占比是多少

### 2.9 静态/动态职责边界已重新校正

本轮进一步明确了：

1. `L0` 只负责静态盘面本体强弱。
2. 月令在 `L0` 可以放大本气与相生，但不再因为“所克”直接压低目标元素本体。
3. `L1/L2` 动态插件必须建立在静态底盘之上，但不再反向污染 `L0` 定义。

对应升级包括：

- `SEASON_POWER_CONTROLLED` 不再作为 L0 直接压制项
- 三合等强结构在 `L0` 已有基础结构回灌
- 动态插件统一开始携带 `static_basis`

这意味着系统开始正式遵守命理师的判盘顺序：

- 先看盘面
- 再看动象

### 2.10 藏干 canonical 口径已修正

本轮修正了纯气支的藏干口径：

- `子 = 癸 1.00`
- `卯 = 乙 1.00`
- `酉 = 辛 1.00`

这一步消除了旧版中最明显的藏干错误来源，也让：

- 通根
- 透干显影
- 三合/合化簇投影

站在更稳定的基础上继续计算。

### 2.11 Master Reasoning Layer 已进入最小可用态

后端新增：

- [V17_MASTER_REASONING_PROTOCOL.md](/Users/liujin/DEV/AIProjects/bazi/qiazhi/v17_rebirth/docs/V17_MASTER_REASONING_PROTOCOL.md)

并在 hydration 后注入：

- `meta.master_reasoning`
- `pt.master_reasoning`

当前已可结构化保留：

- `reasoning_steps`
- `dominant_evidence`
- `suppressed_evidence`
- `learning_hooks`

这代表系统开始不仅保留“结论”，也开始保留“命理师是怎么走到这个结论的”。

---

## 3. 关系类插件实验场已建立

本轮关系类插件不再只靠真实盘试错，而是已经建立了“真实盘 + 合成盘”双轨实验场。

### 3.1 三合簇投影实验

已完成合成验证：

- 金局官杀簇
- 木局财簇
- 水局食伤簇
- 火局官杀簇

已确认：

1. 三合局不再只会投成单一 `七杀`
2. 不同化神元素会落到不同十神簇
3. 簇内可按可见透干、隐藏权重做拆分

### 3.2 关系类专项实验

当前合成关系实验场已覆盖：

- 五合不化
- 五合成化
- 六合稳合
- 六合运助
- 六合流引
- 六害暗耗
- 六害运助
- 六害流引
- 六破轻损
- 六破运助
- 六破流引

当前已经稳定体现：

1. 五合成化明显强于五合不化
2. 六合在 `luck_background` 场景下明显强于 `flow_trigger`
3. 六害整体强于六破
4. 大运参与整体强于流年引动

### 3.3 真实盘校准

当前已经形成真实盘校准链：

- 插件 `match_ratio`
- `origin_summary`
- `plugin_recompute_contributions`

校准结果已经能稳定暴露这些问题：

1. 哪些插件过于容易打到满分
2. 哪些插件 `delta_abs` 过猛
3. 哪些场景下“运到成势”应强于“流年引动”

对应文档与脚本：

- [V17_PLUGIN_REAL_CHART_CALIBRATION.md](/Users/liujin/DEV/AIProjects/bazi/qiazhi/v17_rebirth/docs/V17_PLUGIN_REAL_CHART_CALIBRATION.md)
- [calibrate_plugin_match_cases.py](/Users/liujin/DEV/AIProjects/bazi/qiazhi/v17_rebirth/scripts/calibrate_plugin_match_cases.py)
- [calibrate_synthetic_sanhe_cases.py](/Users/liujin/DEV/AIProjects/bazi/qiazhi/v17_rebirth/scripts/calibrate_synthetic_sanhe_cases.py)
- [calibrate_synthetic_relation_cases.py](/Users/liujin/DEV/AIProjects/bazi/qiazhi/v17_rebirth/scripts/calibrate_synthetic_relation_cases.py)

---

## 4. 当前插件体系已经具备的统一语言

到本轮结束，插件已经基本共享同一套结构语义：

### 4.1 命中层

- `match_ratio`
- `condition_state`
- `origin_type`

### 4.2 结构层

- `target_god`
- `cluster_projection`
- `projection_share`

### 4.3 裁决层

- `claim_type`
- `logic_level`
- `entity_scope`
- `exclusivity_key`

### 4.4 结算层

- `impact_ratio`
- `base_recompute`
- `plugin_recompute_contributions`

这意味着：

1. 关系插件和专题插件已经开始说同一种结构语言
2. 前端和后端已经能围绕同一套字段沟通
3. 后续专题深化可以站在统一协议之上继续推进

---

## 5. 前端观测已经完成对齐

本轮不只做了后端协议，也同步完成了 UI 观测级对齐。

当前已经完成：

### 5.1 Oracle

- 展示 `Plugin Focus Map`
- 展示主落点 `target_god`
- 展示 `projection_share`
- 展示簇投影摘要

文件：

- [oracle/page.tsx](/Users/liujin/DEV/AIProjects/bazi/qiazhi/v17_rebirth/frontend/app/v17/oracle/page.tsx)

### 5.2 Admin

- 插件卡片显示主落点
- 显示 `match %`
- 显示簇投影摘要

文件：

- [admin/page.tsx](/Users/liujin/DEV/AIProjects/bazi/qiazhi/v17_rebirth/frontend/app/v17/admin/page.tsx)

### 5.3 TracePanel

- 插件执行状态显示主落点
- 显示投影占比
- 显示簇投影摘要

文件：

- [V17_TracePanel.tsx](/Users/liujin/DEV/AIProjects/bazi/qiazhi/v17_rebirth/frontend/components/V17_TracePanel.tsx)

### 5.4 Decision Inbox

- 手动入口与自动处理卡片显示主落点
- 显示主占比与簇投影摘要
- 用户可见旧语义已基本替换为新语义

文件：

- [V17_DecisionInbox.tsx](/Users/liujin/DEV/AIProjects/bazi/qiazhi/v17_rebirth/frontend/components/V17_DecisionInbox.tsx)

这意味着插件主线现在已经具备“后端结构统一 + 前端观测统一”的完整闭环。

---

## 6. 当前仍然保留的非阻塞后续项

以下项目不阻塞本轮插件收官，但属于下一阶段专题深化：

1. 盲派可继续扩成更细的专项断口，但当前“做功 / 应链 / 象法 / 应期 / 收束”链已经齐备。
2. 格局候选虽然已进入冲突层，但 `winner / dropped` 还可以更直接回灌专题插件。
3. 合化专题还可以继续细化“成化 / 羁绊 / 助化 / 假化”的分型文案与权重。
4. `match_ratio` 仍需继续通过真实盘与合成盘联调，不宜视为最终常数。
5. 运流来源语义已进入核心关系插件，但还可以继续扩到更细的旁路专题。

---

## 7. 终验证据

本轮插件相关验证已通过：

### 7.1 测试

最新关键测试结果：

- `test_plugin_condition_protocol.py`
- `test_plugin_family_discovery.py`
- `test_spec_validator.py`
- `test_risk_matrix.py`
- `test_synthetic_relation_focus.py`
- `test_ten_gods_energy_calibration.py`
- `test_branch_hidden_canonical.py`
- `test_master_reasoning.py`
- `test_vector_physics_engine.py`

综合结果：

- 后端：`181 passed`
- 前端：`npm run -s build` 通过

### 7.2 前端构建

- `npm run -s build` 通过

### 7.3 语法校验

- `py_compile` 通过

---

## 8. 最终判断

如果验收标准是：

> 插件体系是否已经从混乱、旁路、黑箱状态，进入可维护、可扩展、可审计、可观测状态？

答案是：

**已经完成。**

如果验收标准是：

> 所有命理专题、所有匹配公式、所有案例口感都已经到达最终学术形态？

答案是：

**还没有，但这已经不再是插件主线工程问题，而是下一阶段专题校准问题。**

因此，本轮建议的正式结论是：

**V17 插件主线可以收官，后续工作转入专题精修与案例校准。**
