# V50 Architecture Purification & Experience Refoundation v1

## 0. Architecture Decision

> 不从零重写，不继续原地堆叠。保留已经成立的命理认知与 LifeCase 权威，重建体验编排边界，并按纵向用户旅程逐步迁移、断流和清理旧实现。

本轮采用：

```text
Core Stable
+ Experience Refoundation
+ One-way Migration
+ Legacy Retirement
```

不是：

```text
复制 V50 成 V60
全仓库 Greenfield 重写
长期维护 product_old / product_new 两套真相
一边迁移一边继续向旧链增加功能
```

## 1. Why Refoundation Is Necessary Now

2026-07-18 仓库实测：

```text
apps/product/static/l5/app.js       3425 lines
apps/product/static/l5/styles.css   2994 lines
core/mingli_agent/reasoner.py       2837 lines
apps/product/agent_api.py           2010 lines
frontend state fields                 52
docs files                            66
reports files                        376
scripts files                         86
tests files                          207
reports size                         36M
```

2026-07-13 的上一轮清理后曾经只有：

```text
documentation files  30
report files         34
test files           42
```

这不是“文件多就是坏”，而是一个明确信号：最近成立的 Life OS、LifeCase、Abu、语音、剧场、Topic、可视化与验证能力再次向少数万能文件聚集。继续增加功能会产生第二轮架构污染。

与此同时，现有证据不支持全盘重写：

- 确定性八字 / 紫微事实引擎可独立运行；
- LLM Mingli Agent 已成为认知主体；
- LifeCase / Formal Insight 已成为正式案例权威；
- 旧 workspace 双写已经停止；
- 页面和语音已经同源；
- FastAPI、PostgreSQL、WebSocket、TTS 与私有缓存均已跑通；
- 当前全量回归为 `308 passed`；
- Runtime Authority Audit 当前没有研究模块越权进入生产。

结论：

> 系统需要重新划分职责和依赖，不需要重新发明排盘、认知、案例和数据生命周期。

## 2. Frozen Stable Core

体验重构期间，下列能力先冻结为 `V50 Life OS Core Stable`：

### Chart Fact Core

- 出生资料规范化；
- 八字排盘与四柱事实；
- 紫微排盘与宫位星曜事实；
- 节气、大运、流年、流月坐标；
- 可重复计算的基础关系。

### Cognitive Core

- LLM whole-chart cognition；
- Context Compiler；
- Pattern / competing hypotheses；
- work path / domain reasoning；
- epistemic review 与 Reliability Gate；
- 当前专业盲测使用的 Prompt、理论和模型版本。

### LifeCase Continuity Core

- ChartVersion；
- LifeCase Revision；
- Formal Insight；
- RealityEvidence；
- TemporalSnapshot；
- Case Revision / history；
- 权限与私人案例隔离。

冻结表示：体验迁移不能顺手改算法、Prompt、理论或专业门禁。否则无法判断变化来自架构迁移还是命理能力变化。

## 3. Target Dependency Direction

```text
Chart Fact Core
        ↓
Mingli Cognitive Core
        ↓
LifeCase Authority
        ↓
MingliExperienceEnvelope
        ↓
Experience Timeline / Narration / Visualization / Performance
        ↓
Web / Mobile / Professional / Live / Replay
```

只允许向下依赖。

硬边界：

```text
Experience 不读取完整 LifeCase Repository
Visualization 不调用 Reasoner、不决定命理路径
Theater / LifeScript 不产生或修改 Formal Insight
页面与 Abu 不各自保存命理结论
Report / Export 不能反向成为恢复来源
Research projection 不能自动升级为生产认知
Legacy 不再产生正式业务写入
```

## 4. Minimal Experience Foundation

不先建立几十个抽象类。第一版只收敛已经真实需要的对象：

### MingliExperienceEnvelope

体验层唯一命理输入，只包含当前角色和任务获准使用的只读投影：

```text
case / chart / insight version refs
public formal assertions
conditions and uncertainty
approved path projection
temporal context projection
capability boundaries
source anchors
```

### ExperienceTimeline

统一页面同步论命、剧场、Live 与回放的时间顺序：

```text
chapters
cues
current position
interrupt / resume policy
replay identity
```

### ExperienceCue

统一表达：

```text
narration
subtitle
page anchor
visual action
Abu motion
camera / stage hint
```

### Existing Contracts To Reuse

- `NarrationSegment`；
- `SpeechAsset`；
- `PerformanceCue` 中已经成立的字段；
- `MingliVisualSpec / VisualCue` 当前可执行部分；
- `ExperienceEvent` 当前隐私与幂等规则。

重构先做合同合并和适配，不复制第二套同义对象。

## 5. Initial Classification

### KEEP

```text
core.contracts
core.engines.bazi
core.engines.ziwei
core.mingli_agent
core.life_case
ChartVersion / Formal Insight / RealityEvidence / TemporalSnapshot
Reliability Gate
Qwen TTS service
private SpeechAsset cache and versioning
professional benchmark controls
critical regression tests
```

### CONVERGE

```text
core.abu_runtime
packages.experience contracts and runtime
Narrated Workspace
Theater Control Runtime
SpeechAsset generation and delivery
Graph / stage_snapshot projection
page chapter / voice / anchor synchronization
agent_api application orchestration
product_store and case context
frontend workspace state
```

这些能力保留，但必须统一走 Experience Envelope、Timeline 和应用命令。

### REBUILD

```text
clean Experience projection boundary
modular frontend Experience Shell
Abu Performance adapter
Mingli Visualization adapter
LifeScript projection
application command handlers for core user actions
```

“重建”发生在同一仓库、同一数据权威上，不复制命理内核。

### QUARANTINE

```text
legacy read aliases in agent_case_store
legacy_unreviewed imported cognition
research-only core.mechanism / core.state / core.timing
one-off benchmark scripts and superseded reports
old natural-language reports
deprecated prompts and unversioned caches
page-specific business state that duplicates LifeCase
```

隔离不等于删除。研究模块继续用于 Lab，但不能被产品运行时误认为正式判断。

### RETIRE / DELETE CANDIDATES

```text
first_reading_ready naming and old report-era semantics
unreachable old route branches
duplicate frontend stores and action handlers
page-specific audio or animation paths superseded by the timeline
unused CSS / JS / media assets
superseded run scripts and generated reports
implementation-detail tests tied only to retired DOM or DTOs
```

所有候选都必须经过删除门禁。

## 6. Data Authority Matrix

| Data / Capability | Sole Authority | Experience Access | Legacy Handling |
|---|---|---|---|
| Birth input and chart facts | ChartVersion + deterministic engines | projected read-only | migration comparison only |
| Professional cognition | LifeCase Revision / Formal Insight | MingliExperienceEnvelope | old reports are historical artifacts |
| Reality records | RealityEvidence | reference + projected summary | old chat/probe cannot become facts automatically |
| Temporal cognition | TemporalSnapshot | projected current context | old timing reports never restore authority |
| Topic exploration | TopicExploration / SandboxState | isolated experience | never auto-commit to LifeCase |
| UI interaction | WorkspaceState | client/runtime state | no Mingli assertions stored |
| Model execution | RunRecord | audit only | never restore formal cognition |
| Voice | SpeechAsset | private versioned URL | old assets expire or archive |
| Performance | PerformancePackage / Cue | timeline | raw candidate media stays outside production registry |
| Export / report | Projection | output only | cannot write back into LifeCase |

This matrix must become executable architecture tests, not remain documentation only.

## 7. Migration Strategy

### Phase P0 — Freeze And Inventory

```text
freeze Core Stable hashes and full regression
build Data Authority Matrix
build Legacy Register
build Prompt / Knowledge Registry
build Media Asset Registry
trace runtime use of legacy routes, tables and recovery paths
classify docs, scripts, reports and tests
```

No destructive deletion in P0.

### Phase P1 — Dependency Fences

Add failing architecture checks for:

```text
experience importing repositories
visualization importing reasoner implementation
legacy performing canonical writes
report DTO becoming restore input
research modules entering production cognition
new code importing quarantined modules
```

Stop new legacy dependencies before moving directories.

### Phase P2 — Reference Slice: 看见命局 Next

Use one committed LifeCase to prove:

```text
fast page scan
Abu synchronized narration
four-pillar anchors
approved work-path visualization
conditions and uncertainty
private cached speech
chapter jump / interruption / replay
```

All surfaces must consume one `MingliExperienceEnvelope`. After parity is proven, the old whole-chart current-data path becomes read-only and then retires.

### Phase P3 — Current Stage And Topic Exploration

Migrate temporal context, monthly observation and the first executable Topic. Sandbox changes remain isolated and cannot mutate Formal Insight.

### Phase P4 — Reality Loop And Case Revision

Unify record, review and revision commands around `RealityEvidence` and LifeCase Revision. Remove duplicate chat/probe/monthly JSON writes.

### Phase P5 — Legacy Retirement

```text
stop old writes
switch remaining reads to projections
archive legacy data and natural-language reports
confirm static and runtime usage are zero
migrate tests and operations docs
delete only after the gate passes
```

## 8. Why `product_next` Is Not Step One

A new shell may eventually be useful, but creating a second product application before the Experience Envelope and dependency fences exist would immediately create two products and two stores. The bounded shell now lives inside the existing product application at `apps/product/experience_shell`.

The safer order is:

```text
canonical envelope and command boundary
→ one new reference route/surface
→ prove independent state and data flow
→ decide whether it deserves a separate app shell
```

Directory movement is an implementation result, not the architecture itself.

## 9. Cleanup Ledgers

### Legacy Register

```text
item
current callers
runtime call count / last seen
canonical replacement
status
retirement gate
archive location
```

### Prompt Registry

```text
prompt_id / purpose / reasoner
version / content_hash / theory_version
input / output contract
status: active | frozen_control | deprecated | retired
replaced_by
```

### Media Registry

```text
asset_id / actor_version / motion_type
canvas / scale / anchor / camera / lighting
start_pose / end_pose / duration / loopable
source model / prompt hash
status: production | approved_reference | experimental | deprecated | deleted
```

### Migration Ledger

```text
source / target / version
records attempted / migrated / rejected
trust level
idempotency key
rollback method
```

## 10. Delete Gate

Physical deletion requires all of the following:

```text
replacement path accepted
no canonical dual write
all current reads switched
static dependencies zero
runtime calls zero for an observation window
data migrated or archived
rollback artifact exists
tests migrated
docs and operations updated
professional blind-test controls preserved
Legacy Cut and full regression pass after deletion
```

Database migration history is never rewritten. Old tables become read-only, then archived, then removed through new migrations.

## 11. Development Discipline During Refoundation

```text
no new feature in legacy
no new dual write
no unversioned cache
no prompt embedded in route handlers
no formal Mingli result stored in page state
no old report entering Experience Envelope
no Reasoner / theory change mixed into experience migration
no automatic promotion of historical prose
```

Every change must leave legacy dependency count unchanged or lower.

## 12. Acceptance Criteria

Refoundation is complete only when:

1. One Formal Insight can drive text, voice, visualization, Live and replay without semantic drift.
2. All canonical writes have one owner.
3. Page and Abu share one current task and one interaction state.
4. Visualization and Theater have no Mingli judgment authority.
5. Old Report is absent from current cognition and recovery paths.
6. Adding a new topic does not add Topic ID-specific runtime branches.
7. Replay invokes no LLM, Reasoner or TTS.
8. Research-only modules remain isolated.
9. New experience can run without the old page store.
10. Stable Core and professional blind-test controls remain reproducible.
11. Full regression and architecture tests pass.
12. Archived legacy remains auditable but cannot influence current users.

## 13. Immediate Authorized Slice

The next long task should be:

```text
Architecture Purification P0
— Authority, Dependency And Legacy Freeze
```

Deliverables:

```text
Data Authority Matrix (machine-readable + Markdown)
Legacy Register
Prompt / Knowledge Registry
Frontend State Source Audit
Database Read / Write Authority Audit
Media Asset Registry
Runtime Legacy Usage Trace
Architecture dependency tests
P1 migration plan for 看见命局 Next
MASTER_AUDIT_REPORT
```

P0 may add audit tooling and dependency gates. It may not delete production code, modify Mingli algorithms, rewrite the database, change professional Prompt versions, or start a second product app.

## 14. P0 And Slice 1 Implementation Record

As of 2026-07-18, the authorized P0 boundary work and the first bounded experience slice are implemented and machine validated:

```text
canonical authority registries
legacy formal-write blocker
runtime legacy usage counter
read-only MingliExperienceEnvelope API
independent typed Experience Shell
看见命局 Next desktop/mobile slice
Abu narration timeline and visual anchors
architecture dependency audit
full regression
```

The new experience is available at `/experience`. It reads only active, committed LifeCase cognition through `MingliExperienceEnvelope`; it does not call the Reasoner, write formal cognition, restore old reports, or own a second case store.

The following are deliberately not claimed:

```text
human UX acceptance
professional Mingli blind-test acceptance
default-entry switch
legacy physical deletion
production deployment
```

Machine evidence is recorded in `reports/architecture-purification-p0-slice1/MASTER_AUDIT_REPORT.md` and `reports/architecture-purification-p0-slice1/architecture_audit_v1.json`.
