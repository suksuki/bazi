# V40 Phase 12: Native Bazi Skeleton And Synthetic Cases

更新时间：2026-06-30

## 目标

让 V40 不再只能通过 V30 DTO fixture 演示运行时能力。

Phase 12 新增：

```text
BaziChartFacts
SyntheticCaseSeed
V40 native Bazi engine skeleton
POST /api/v40/runtime/native-bazi
POST /api/v40/synthetic/cases/from-seeds
data/synthetic/native_bazi_seeds.json
```

## 原生八字引擎骨架

当前原生引擎不是完整历法排盘器，而是接受已经校准好的 chart facts：

```text
year pillar
month pillar
day pillar
hour pillar
gender
current luck
current year
```

然后输出：

```text
EngineRunResult
RuntimeSignal
DecisionVerdict
AdvicePlan
ProbeCandidate
ProductProjectionBundle
```

它的边界：

```text
不读取 V30 runtime
不生成不可追踪 chart facts
不让 LLM 参与 verdict
不把 skeleton 判断当最终命理断语
```

## Synthetic Cases

Synthetic seed 用来生成 `EvaluationCaseSpec`。

用途：

```text
验证结构化输出
验证 forbidden assertion
验证 advice/probe 是否存在
验证 native runtime 可以进入 evaluation loop
```

不用于：

```text
证明现实命例准确
替代 golden case
替代命理师标注
```

## API

```text
POST /api/v40/runtime/native-bazi
POST /api/v40/synthetic/cases/from-seeds
```

## CLI

导入 synthetic cases：

```bash
python scripts/v40_artifact_cli.py import-synthetic-cases \
  --path data/synthetic/native_bazi_seeds.json
```

运行一个 native seed：

```bash
python scripts/v40_artifact_cli.py run-native-seed \
  --path data/synthetic/native_bazi_seeds.json \
  --seed-id native.career.bingchen.001 \
  --reading-id reading.local.native.001
```

## 下一阶段

Phase 13 已进入正式产出编排层：

1. V40 原生命理引擎从 skeleton 升级为 fact layer；
2. Engine verdict/advice/probe 临时逻辑拆入 DecisionEngine；
3. ProductProjection 区分用户结果与命理师分支校准；
4. SurfaceBundle 分离 reading、calibration、conversation、thinking；
5. Practitioner calibration 进入 TrainingLabelEvent。

Phase 14 应继续：

1. Ten-god / useful-god / branch relation 的原生 signal adapter；
2. Native runtime batch evaluation；
3. LLM expression task 执行和 acceptance scan；
4. Admin Console 增加 native run/synthetic import 操作；
5. V30 DTO batch export 工具。
