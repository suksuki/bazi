# V17 调候场与 Authority 分层实现记录

日期：2026-04-23

## 1. 本轮目标

根据裁决回复，本轮只做两件事：

1. 落地 `调候底层场`
2. 落地 `authority 分层协议`

明确不做：

- 不新增更多门派
- 不让调候直接改写 L0 原始十神总量
- 不让象法进入 bias

## 2. 已实现内容

### 2.1 调候底层场

新增模块：

- `backend/logic/climate_field_protocol.py`

当前已落地：

- 双主轴：
  - `thermal_index`
  - `moisture_index`
- 派生状态：
  - `heat`
  - `cold`
  - `humidity`
  - `dryness`
  - `climate_tension`
- 来源分解：
  - `source_rows`
  - `source_by_element`
  - `source_by_scope`
- 调候修正层：
  - `ten_god_efficiency`
  - `ten_god_stability`
  - `yongshen_priority_delta`
  - `pattern_survival_delta`

当前落位：

- `L0/L1` 共享底层协议
- 通过 `calc_deity_scores()` 回写进 `energy_meta`

### 2.2 climate modifier layer

本轮明确采用：

- `climate field` 独立计算
- `climate modifier layer` 独立输出
- 第一阶段只作为修正层存在

当前不做：

- 直接改写 `L0 base totals`

当前用途：

- Prompt 合同
- authority 元数据挂接
- authority 打分链：
  - `ten_god_efficiency`
  - `ten_god_stability`
  - `yongshen_priority_delta`
- pattern survival 链：
  - `pattern_survival_delta`

### 2.3 authority 分层协议

新增模块：

- `backend/services/authority_layer_protocol.py`

当前已落地字段：

- `contract`
- `authority_level`
- `override_forbidden`
- `max_bias_ratio`
- `hard_constraint_source`
- `structure_enhancement_source`
- `soft_bias_source`

同时已落地两条执行规则：

1. `soft bias` 进入前先做 `max_bias_ratio` 限幅
2. 当存在 `soft_bias_source` 时，允许硬约束保顶，防止 Level 3 overturn Level 1

### 2.4 ziping 主裁决接入

当前 `ZiPingGodRingResolverPlugin` 已新增：

- `authority_layer_protocol`
- `climate_modifier_layer`
- climate-adjusted `effect_scores`
- climate-adjusted `core_use_candidates / core_taboo_candidates`

并已把：

- blind soft bias 限幅
- climate deltas 挂入 `effect_scores`
- climate 重新参与 `authority_use_score / authority_taboo_score`
- climate 重新参与最终 `use_gods / taboo_gods` 排序

但本轮仍保持：

- 调候不直接改写原始 base 分数
- 调候不直接替代 ziping 主裁决

### 2.5 格局专题接入

`pattern_specializations.py` 当前已增加统一的 pattern climate finalize 层：

- 所有 `pattern_candidate` 会自动读 `pattern_survival_delta`
- 自动回写：
  - `match_ratio_raw`
  - `climate_pattern_survival_bucket`
  - `climate_pattern_survival_delta`
  - `climate_pattern_survival_adjusted`
- 这意味着调候不只影响 authority，也已开始影响格局候选的生存度

### 2.6 Prompt 接口接入

`PhysicsCanonical` 当前已新增：

- `调候合同`
- `调候摘要`
- `调候修正层`
- `裁决分层合同`

这样 LLM 已经可以读懂：

- 当前命盘的寒热/燥湿状态
- 当前调候修正层影响了哪些十神优先级
- authority 当前的 Level 1/2/3 边界

## 3. 当前边界

### 3.1 已完成

- 调候物理场协议
- 调候来源分解
- 调候修正层
- authority 分层协议
- blind soft bias 限幅
- Prompt 合同
- 测试覆盖

### 3.2 暂未完成

- `risk_matrix` 边界只在设计层明确，尚未协议化
- 象法暂不进入 bias，仍保持 semantic-only

## 4. 下一步

下一阶段建议顺序：

1. Phase 4：L2 调候专题解释
   - 已完成 `climate theme core + 4 个专题插件`
   - 已接入 Prompt / Oracle 辅助页 / Admin Core 面板

2. Phase 5：象法语义专题
   - 已完成 `xiangfa_theme_core + 4 个专题插件`
   - 只输出 `semantic mapping / evidence / narrative hint / event framing`
   - 明确不进入 bias、不改能量、不覆盖 authority

3. Phase 6：risk_matrix 边界协议化
   - 仍待后续协议化

## 5. 验证结果

本轮通过：

- 定向链路：`15 passed`
- 后端全量：`398 passed`
- 前端：`pnpm build` 通过

这意味着：

- `调候场`
- `authority 分层`
- `调候 -> authority 打分`
- `调候 -> pattern survival`
- `blind -> authority`
- `xiangfa semantic-only topic`
- `prompt canonical`

当前主链已处于可继续演进的稳定基线。
