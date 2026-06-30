# V40 Phase 8: Batch Evaluation

更新时间：2026-06-30

## 目标

把单样本评测扩展为批量评测，为 golden case bank、synthetic case runner 和后续大规模训练验证做底座。

Phase 8 新增：

```text
EvaluationBatchSummary
POST /api/v40/evaluation/batches/from-runtime
GET  /api/v40/evaluation/batches
scripts/v40_artifact_cli.py run-batch
v40_evaluation_batches
```

## 批量评测流程

```text
EvaluationCaseSpec[]
  + RuntimeResult
  -> EvaluationRunResult[]
  -> EvaluationBatchSummary
```

Batch summary 聚合：

```text
case_count
passed_count
review_count
blocked_count
average_overall_score
failed_reason_counts
recommendation
```

## API

```text
POST /api/v40/evaluation/batches/from-runtime
GET  /api/v40/evaluation/batches
```

它会保存：

```text
v40_evaluation_runs
v40_release_gates
v40_evaluation_batches
```

仍然不会写生产权重。

## CLI

用 seed cases 和 V30 export fixture 跑一批：

```bash
python scripts/v40_artifact_cli.py run-batch \
  --cases data/golden_cases/seed_career.json \
  --v30-export tests/fixtures/v30_export_minimal.json \
  --batch-id batch.local.career.001 \
  --candidate-version v40-alpha
```

只跑不入库：

```bash
python scripts/v40_artifact_cli.py run-batch \
  --cases data/golden_cases/seed_career.json \
  --v30-export tests/fixtures/v30_export_minimal.json \
  --batch-id batch.local.career.dryrun \
  --candidate-version v40-alpha \
  --no-persist
```

## 下一阶段

Phase 9 已进入：

1. Candidate weight version 草案；
2. 多 batch 聚合 release readiness 进入后续阶段；
3. Synthetic case generator 进入后续阶段；
4. Admin Console 页面读取 batch / run / impact 进入后续阶段；
5. V40 与 V30 shadow compare 批量导出工具进入后续阶段。
