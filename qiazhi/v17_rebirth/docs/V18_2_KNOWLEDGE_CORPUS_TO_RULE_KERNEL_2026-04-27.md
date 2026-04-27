# V18.2 知识分层与插件承载规范（Theory Corpus → Rule Kernel → Mechanism Graph）

> 目标：把插件从“规则来源最高抽象”降级为“规则承载容器”，把可验收知识能力提升到第一层。

## 1. 核心原则

1. 插件不再是系统的最终权威。
2. 知识先入仓（Knowledge Corpus）→ 转为规则（Rule Kernel）→ 串入机制图（Mechanism Graph）→ 落入预测输出（Prediction Contract）。
3. 可用性从“经验文字”到“结构字段”逐层收敛，保留来源与置信证据。
4. 高层象义默认只可作为观察/叙事，不可直接发起决策权重超过结构裁决层。

## 2. 新分层（V18.2）

```text
Knowledge Corpus（知识语义层）
  ├── Classical Sources（古籍）
  ├── Modern Interpretations（现代研究）
  ├── Master Notes（命理师经验）
  ├── Synthetic Test Results（合成实验）
  └── Feedback Statistics（反馈统计）

Knowledge Card（知识卡）
  ├── raw
  ├── parsed
  ├── rule_candidate
  ├── validated
  ├── active
  └── deprecated

Rule Kernel（规则内核）
  ├── foundational rules
  ├── structural rules
  ├── mechanism rules
  ├── symbolic rules
  └── timing rules

Mechanism Graph（机制图）
  ├── 主题边界
  ├── 条件边界
  ├── 冲突策略
  └── 机制效果

Prediction Contract（预测单元）
  ├── causal_path
  ├── rule_ids
  ├── confidence
  ├── uncertainty
  └── evidence ids

Topic Plugin（专题/门派承载层）
  ├── 规则包
  ├── 主题聚合
  ├── 报告展示结构
  └── 工具化实验脚本（可选）
```

### 2.1 插件定位（承载，不是裁决器）

- 插件负责：知识打包、规则装载、主题展示。
- Rule Kernel 负责：规则结构、权重、冲突策略、可执行边界。
- Resolver 负责：激活筛选、冲突裁决、效果合成。
- Contract 负责：可追踪、可验证、可复盘的预测记录。

## 3. Knowledge Card 统一格式

```json
{
  "knowledge_id": "kc_tomb_vault_wealth_001",
  "title": "财星入库主财富隐藏与积累",
  "source": {
    "type": "classical|modern|master|feedback|synthetic",
    "name": "source_name",
    "quote": "可选原文",
    "confidence": 0.7
  },
  "theory_family": "tomb_vault",
  "knowledge_type": "mechanism",
  "applies_to": ["wealth"],
  "condition_text": "财星落入墓库，且未被冲开",
  "effect_text": "财富不显，偏积累、沉淀、延迟释放",
  "exceptions": [
    "大运流年冲库时转为财动",
    "比劫旺时开库可能变为破耗"
  ],
  "status": "raw|parsed|rule_candidate|validated|active|deprecated"
}
```

### 3.1 5 类知识来源

A. 基础事实类（底座，权威最高）
- 天干地支、五行生克、十神、藏干、旺衰、长生、冲合刑害破、墓库

B. 结构判断类（主判断）
- 格局、体用、用神忌神、调候、通关、扶抑、从格、专旺

C. 机制推理类（进入机制图）
- 食伤生财、食伤制杀、杀印相生、财官印、比劫夺财、财库开合、伤官见官

D. 象义经验类（默认弱权重）
- 盲派象法、宫位象、十神象、职业象、疾病象、婚恋象

E. 断语案例类（最高污染风险）
- 组合经验、应期经验、职业倾向经验

## 4. 推荐来源族映射（非权威优先级）

- `ziping`：decision / structural
- `blind`：hypothesis / narrative_hint
- `xiangfa`：observe / narrative_hint
- `shensha`：weak_signal
- `modern`：补充参数与反例

## 5. 从 Knowledge Card 到 Rule Kernel（最小转换）

示例：

```json
{
  "rule_id": "rk_tomb_vault_wealth_storage_001",
  "theory_family": "tomb_vault",
  "condition": {"expr": "ten_god.wealth.in_vault == true && vault.opened == false"},
  "effect": {
    "wealth_visibility": -0.4,
    "wealth_stability": 0.3,
    "wealth_volatility": -0.2,
    "wealth_retention": 0.35
  },
  "effect_scope": ["wealth", "ten_god.wealth"],
  "allowed_topics": ["wealth"],
  "priority": 0.72,
  "evidence_strength": 0.65,
  "conflict_policy": "merge",
  "status": "experimental"
}
```

注意：`status` 流转必须经过 sandbox 测试与 Reviewer 才能 active。

## 6. Workflow（生产化）

1. 采集古典理论与案例。
2. 转成 Knowledge Card。
3. 人工解析为 rule_candidate。
4. 进入 Sandbox。
5. 通过 Rule Test Engine 合成验证。
6. 推送 Reviewer。
7. approved 后转 validated / active。
8. 进入真实反馈学习链。

## 7. 风险边界（建议固化）

1. 不允许象义/案例卡直接写进生产决策口径。
2. 不同知识来源冲突时必须经过 `conflict_policy` 与 Resolver。
3. 主题外推必须受 `allowed_topics` 限制。
4. 任何生产输出都要可追溯到 `rule_ids`、`resolver_snapshot`、`prediction_hash`。

## 8. 与 V18.1 骨架的对齐

- `rule_kernels` 对齐为结构化规则内核。
- `consumer-agent` 等面向用户端接口仍可保留，但 `materialize` 落库路径应最终指向 `Prediction Contract`。
- `Knowledge Card` 与 `Rule Kernel` 的持久化可先以文件/轻量表为起步（最小可运行骨架），后续再接入持久化层。
