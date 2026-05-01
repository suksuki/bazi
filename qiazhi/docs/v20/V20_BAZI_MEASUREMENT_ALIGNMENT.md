# V20 Bazi Measurement Alignment

V20 keeps the P84 feature spine, but the product center is Bazi measurement.

## Reframed Runtime Layers

The portrait, question, and answer systems are now projections over verified features:

- Portrait is a Bazi feature projection and calibration surface. Reviewed
  knowledge may support its wording and boundaries, but it does not drive
  conclusions.
- Recommended questions are measurement entries, not generic engagement prompts.
- Answers are measurement plans composed from selected features, evidence packs, knowledge boundaries, and prediction policy.

## Measurement Topics

The initial topic map is:

- `strength`: 日主强弱
- `useful_god`: 用神候选
- `ten_god`: 十神结构
- `element`: 五行分布
- `branch`: 地支关系
- `time`: 时间层与流年触发
- `wealth`: 财星与收入结构
- `career`: 事业角色与工作结构
- `relationship`: 关系互动结构
- `health`: 五行平衡与健康边界
- `pattern`: 格局审查

These are not final fortune verdicts. They are bounded measurement paths that can become richer as rule paths, time context, corpus coverage, and validation improve.

## Measurement Report

V20 now exposes `measurement_report` as the shared runtime view for UI,
LLM, portrait projection, recommended questions, and answer planning.

- Foundation topics remain `strength`, `ten_god`, `branch`, `pattern`, and
  `useful_god`.
- Useful-god measurement now enters through deterministic candidate paths
  compiled from capacity, five-element distribution, and support/pressure
  evidence. It does not declare fixed favorable or unfavorable gods.
- Applied Bazi measurement topics are generated only through controlled
  domain projection: `wealth`, `career`, `relationship`, and `health`.
- Applied questions must cite source `BaziFeature` ids and keep deterministic
  prediction boundaries.
- Time-layer questions require explicit supplied pillars such as
  `flow_year_pillar`, `luck_pillar`, or `flow_month_pillar`; V20 does not infer
  calendar facts from free text.
- Portrait output remains a calibration surface. It can expose reviewed
  knowledge provenance for analysts and record redacted calibration signals,
  but it does not rank questions, mutate answers, or create fortune
  conclusions.

## Prediction Boundary

V20 should feel like a Bazi prediction system, but prediction must mean evidence-bounded measurement:

- Allowed: structure assessment, feature evidence explanation, useful-god candidate paths, domain readings with boundaries, timing context when a time layer exists.
- Blocked: guaranteed events, fixed fortune verdicts, unsupported health/legal/financial claims, private data inference, and rule mutation by LLM or feedback.

This gives the product a clear Bazi center while keeping the system auditable and safe.
