# A-12 从杀格 RAG 判词抽检验收要点 (Step 6 专项)

2.0 时代首份「极端格局」判词抽检：对**一条满足 A-12 逻辑的典型样本**生成 RAG 判词，并按以下三点验收。

## 核心观测点

| 观测项 | 验收标准 |
|--------|----------|
| **古典锚点** | 判词中须出现《三命通会》相关引证，如「名显威严」「见制则灾」或「从杀格，必是身弱。若行杀旺乡，名显威严；若见制伏，则灾殃立至。」 |
| **物理缝合** | 将 **S 轴极值（+2.0）** 解读为「对威权的绝对顺从与借势」，而非泛泛的「压力大」。 |
| **建议有效性** | 须给出从格特色手术刀建议：**切忌见印比（自我觉醒）反抗，否则格局崩塌**；或「顺杀势、忌制伏」类表述。 |

## 操作方式

1. 在 DuckDB 中取一条 A-12 样本（如 `SELECT ref, E, O, M, S, R FROM pattern_points WHERE pattern_id = 'A-12' ORDER BY S DESC LIMIT 1`），获得 `ref`。
2. 用该 `ref` 在 518k 或业务层反查得到 ten_gods（或直接用该点的 5D 坐标）。
3. 调用 `generate_manifold_interpretation(..., pattern_id="A-12")` 生成 RAG 判词。
4. 将判词全文与上述三点对照，记录在 `audit_logs/rag_verdict_samples.md` 或专项报告中。

## 脚本入口（可选）

- 极端点列表已由 `scripts/audit/extreme_cases_audit.py --pattern A-12` 产出；可任选其一 ref，结合 5D 与 ten_gods 调用 AI 引擎生成判词并人工核对上述三点。
