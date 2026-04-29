# V19 八字知识库扩展工程计划

日期：2026-04-29

状态：分析师路线稿 / Codex 实施前置文档

适用范围：V19 八字知识库、规则提案账本、未来规则数据库与推理引擎扩展

## 1. 总目标

V19 下一阶段目标不是直接增加预测能力，而是系统性建设一个可治理、可版本化、可审计、可逐步转化为推理能力的八字知识库。

当前状态：

```text
已有：
- 基础结构知识
- income_stability 有边界信号
- Knowledge Evidence Store
- Feedback Ledger
- Guided Question Governance
- Rule Attribution
- Rule Knowledge Proposal Ledger

尚未完成：
- 完整八字 Rule Knowledge DB
- 多主题 active inference
- time-aware inference
- 生产级大运/流年推理
```

目标状态：

```text
旧知识与新知识
→ 标准化知识单元
→ 规则提案
→ Schema 校验
→ 分析师/管理员审核
→ 版本记录
→ 未来可控激活
```

核心边界：

```text
不写 fortune
不写传统断语
不直接判断好坏
不让流年/大运直接改变当前 income_stability
不让旧知识绕过提案审核直接进入推理引擎
不让 LLM 自动修改知识库或规则库
```

## 2. 资料来源策略

V19 可以使用三类资料来源。

### 2.1 旧系统来源

优先来源：

```text
V17/V18 旧知识库报告
V18 runtime knowledge units
V18 feature definitions
V18 wealth domain bundles
V18 rule candidates / rule kernels / audit records
```

处理原则：

```text
旧系统知识只能作为来源材料。
不能直接作为 active runtime 规则。
必须先转为 V19 Rule Knowledge Proposal。
```

### 2.2 分析师整理来源

包括：

```text
分析师人工总结
命理师审核意见
结构化知识清单
规则输入/输出定义
反例与边界说明
```

处理原则：

```text
可以直接进入 proposal ledger。
仍然需要 schema validation 和人工审批。
```

### 2.3 网络与公开资料来源

可以作为线索来源，例如百科、入门资料、文章、命理资料库等。

但必须注意：

```text
网络资料不能直接作为权威。
知乎、论坛、社交平台、商业文章只能作为参考线索。
所有规则必须经过分析师/命理师确认。
```

建议证据等级：

```text
A 级：稳定基础常识，多个来源一致，命理师确认
B 级：主流结构规则，需注明适用条件
C 级：经验性机制，必须进入 proposal review
D 级：象义/断语/案例，仅归档，不进入 active inference
```

## 3. 分阶段工程路线

## Part A：基础规则体系（P12-B）

目标：补全八字基础结构知识，使其成为可治理的 Rule Knowledge Proposal 来源。

注意：P12-B 不直接扩展 active inference。

### A1. 干支基础与五行属性表

知识范围：

```text
十天干
十二地支
五行属性
阴阳属性
地支藏干
地支主气 / 中气 / 余气
```

工程化 Schema 示例：

```ts
interface StemAttribute {
  stem: string
  element: 'wood' | 'fire' | 'earth' | 'metal' | 'water'
  polarity: 'yang' | 'yin'
}

interface HiddenStem {
  stem: string
  layer: 'main' | 'middle' | 'residual'
}

interface BranchAttribute {
  branch: string
  element: 'wood' | 'fire' | 'earth' | 'metal' | 'water'
  polarity: 'yang' | 'yin'
  hidden_stems: HiddenStem[]
}
```

输出形式：

```text
基础知识单元
结构事实表
proposal-ready JSON
不产生预测结论
```

### A2. 五行生克关系

知识范围：

```text
五行相生
五行相克
同类
被生
生出
被克
克出
```

工程化 Schema 示例：

```ts
type FiveElement = 'wood' | 'fire' | 'earth' | 'metal' | 'water'

type ElementInteraction =
  | 'same'
  | 'produce'
  | 'produced_by'
  | 'control'
  | 'controlled_by'
  | 'neutral'

function elementInteraction(source: FiveElement, target: FiveElement): ElementInteraction
```

边界：

```text
只输出关系类型。
不输出吉凶。
不输出强弱结论。
```

### A3. 日主基础定义与强弱候选规则

知识范围：

```text
日主由日柱天干决定
日主五行
日主阴阳
月令影响
根气影响
同党/异党影响
生助/克泄耗影响
```

工程化输出建议：

```ts
type DayMasterStrength = 'weak' | 'balanced' | 'strong' | 'unknown'

interface DayMasterStrengthEvidence {
  factor: string
  input_path: string
  observed_value: unknown
  effect: 'support' | 'drain' | 'control' | 'neutral'
  weight_hint?: number
}
```

当前阶段边界：

```text
可以建立候选规则和 evidence schema。
不建议直接替换当前 income_stability 的日主强弱逻辑。
必须先进入 rule proposal validation。
```

## Part B：十神体系与信号规则（P13-A）

目标：建立十神判定和十神结构信号的规范知识单元。

### B1. 十神判定规则

知识范围：

```text
比肩
劫财
食神
伤官
正财
偏财
正官
七杀
正印
偏印
```

工程化 Schema 示例：

```ts
type TenGod =
  | 'bi_jian'
  | 'jie_cai'
  | 'shi_shen'
  | 'shang_guan'
  | 'zheng_cai'
  | 'pian_cai'
  | 'zheng_guan'
  | 'qi_sha'
  | 'zheng_yin'
  | 'pian_yin'

function classifyTenGod(day_master_stem: string, target_stem: string): TenGod
```

边界：

```text
十神标签是关系元数据。
十神标签本身不是预测结论。
```

### B2. 十神结构信号

候选信号：

```text
wealth_presence
wealth_visibility
wealth_rootedness
officer_presence
resource_presence
output_presence
peer_presence
```

工程化 Schema 示例：

```ts
interface TenGodSignal {
  ten_god: TenGod
  count_visible: number
  count_hidden: number
  positions: string[]
  strength: 'none' | 'low' | 'medium' | 'high' | 'unknown'
  evidence: SignalEvidence[]
}
```

边界：

```text
可以成为未来 feature extractor。
不能直接输出 fortune。
不能直接改变当前 ResultCard，除非进入正式 P5/P13 active inference 设计。
```

## Part C：地支组合关系规则（P13-B）

目标：建立地支关系检测知识单元，并与当前 Time Structure Layer 保持一致。

### C1. 六合

关系表：

```text
子丑
寅亥
卯戌
辰酉
巳申
午未
```

工程化输出：

```ts
interface BranchRelation {
  type: 'six_combination' | 'six_clash' | 'three_harmony' | 'three_meeting' | 'penalty' | 'harm' | 'break'
  branches: string[]
  resulting_element?: FiveElement
  evidence_key: string
}
```

### C2. 三合 / 三会 / 冲 / 刑 / 害 / 破

知识范围：

```text
三合局
三会局
六冲
刑
害
破
```

边界：

```text
当前只检测结构关系。
不解释为好运/坏运。
不将关系直接转为收入稳定性变化。
```

## Part D：时间背景结构 Context（P14）

目标：将大运和流年作为结构上下文，不作为预测结论。

### D1. 流年结构

输出：

```ts
interface FlowYear {
  year: number
  pillar: {
    stem: string
    branch: string
  }
  relations_with_natal: {
    clashes: string[]
    combinations: string[]
    harmonies?: string[]
  }
  relations_with_luck_cycle?: {
    clashes: string[]
    combinations: string[]
    harmonies?: string[]
  }
}
```

边界：

```text
Flow Year 是 context。
不是 fortune。
不直接影响 ResultCard。
```

### D2. 大运结构

输出：

```ts
interface LuckCycle {
  start_age: number
  end_age: number
  pillar: {
    stem: string
    branch: string
  }
  relations_with_natal: {
    clashes: string[]
    combinations: string[]
    harmonies?: string[]
  }
}
```

当前阶段建议：

```text
先允许 stub / provenance 标记。
起运年龄、顺逆行、节气边界必须单独校验。
```

### D3. Time Context

输出：

```ts
interface TimeContext {
  natal: ChartStructure
  luck_cycle?: LuckCycle
  flow_year?: FlowYear
  algorithm_status: 'stub' | 'approximate' | 'reviewed'
  provenance: string[]
}
```

边界：

```text
P14 只生成时间结构。
不做 time-aware inference。
P5/P14 后续专门设计后，才允许讨论时间感知推理。
```

## Part E：结构模式识别候选（P15）

目标：建立结构模式识别的候选知识库，但不直接输出命运判断。

候选模式：

```text
财星结构
官杀结构
印星结构
食伤结构
比劫结构
冲合集中结构
财库结构
输出生财结构
比劫分财结构
印制食伤结构
```

工程化 Schema：

```ts
interface StructurePattern {
  pattern_key: string
  pattern_family: string
  matched: boolean
  inputs: SignalEvidence[]
  confidence: number
  allowed_usage: string[]
  forbidden_usage: string[]
}
```

边界：

```text
Pattern 是结构标签。
不是格局断语。
不输出“此命如何”。
不输出传统预测文本。
```

## Part F：规则证据与置信度（P16）

目标：每条知识单元和规则提案必须可追溯。

必备字段：

```ts
interface RuleKnowledgeProposalMetadata {
  evidence_sources: EvidenceSource[]
  confidence_level: 'strict' | 'standard' | 'variant' | 'experimental'
  version: number
  reviewer_notes?: string
  forbidden_runtime_usage: string[]
}

interface EvidenceSource {
  source_type: 'legacy_v17_v18' | 'analyst' | 'practitioner' | 'classical_text' | 'modern_reference' | 'web_reference'
  title: string
  locator?: string
  reliability: 'high' | 'medium' | 'low'
  note?: string
}
```

校验要求：

```text
必须有 source_type
必须有 allowed_usage / forbidden_usage
必须说明是否可以进入 runtime
必须说明是否涉及预测风险
```

## 4. Codex 实施序列

### Step 1：P12-B 基础知识单元

交付：

```text
干支属性表提案 Schema
五行生克关系提案 Schema
日主强弱 evidence Schema
Rule Knowledge Proposal seeds
不接入 active inference
```

### Step 2：P13-A 十神规则单元

交付：

```text
十神判定知识单元
TenGodSignal Schema
十神信号候选提案
不生成预测结论
```

### Step 3：P13-B 地支关系规则单元

交付：

```text
六合
三合
三会
六冲
刑害破
BranchRelation Schema
Time Structure 可复用关系表
```

### Step 4：P14 时间结构 Context

交付：

```text
FlowYear Context
LuckCycle Context
TimeContext Schema
algorithm_status / provenance
不影响 inference
```

### Step 5：P15 结构模式候选

交付：

```text
StructurePattern Proposal Schema
结构标签候选
allowed_usage / forbidden_usage
不输出断语
```

### Step 6：P16 证据与版本治理

交付：

```text
EvidenceSource Schema
Confidence Level
Versioning Metadata
Reviewer Notes
Proposal Validation Rules
```

## 5. 禁止事项

以下内容在当前阶段禁止：

```text
直接上线新预测主题
直接让流年/大运影响 income_stability
直接从旧系统导入 active rules
直接使用网络文章生成 active rule
LLM 自动生成并激活规则
输出“今年如何”
输出“什么时候发财”
输出“命好/命差”
输出传统断语
```

## 6. 当前最合理的下一步

建议下一步执行：

```text
P12-B：基础规则知识单元提案化
```

也就是：

```text
干支属性表
五行生克关系
地支藏干
日主强弱 evidence schema
```

但只进入：

```text
Rule Knowledge Proposal Ledger
```

不进入：

```text
active inference
```

## 7. 最终判断

V19 八字知识库扩展的正确路线不是“快速增强预测”，而是：

```text
先建立干净的知识结构
再建立规则提案
再建立校验与审核
最后才考虑是否进入推理引擎
```

推荐总路线：

```text
基础知识单元
→ 结构关系单元
→ 十神信号单元
→ 时间上下文单元
→ 结构模式候选
→ 证据与置信治理
→ 未来 active inference
```
