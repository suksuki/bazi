# V20 脚本运行手册（逐步版）

本手册用于把 V20 的“开发—验证—训练—全量学习”流程一次讲清楚。  
默认工作目录：`/Users/liujin/DEV/AIProjects/bazi/qiazhi`

## 0. 先说一遍总原则

1. **先本地只读再写入本地 artifact，再写入 Postgres**。  
2. 任何会改数据库/运行时的命令，都要明确用 `--apply`（导入类）或 `--write`（artifact 写盘）。
3. `run_*` 脚本都支持 `--status`，先用它确认上一次结果。
4. 518K 全量脚本属于重作业；默认先用子集和 dry-run 验证再上全量。
5. **统一约定：`limit=0` / `per_rule=0` 代表“全量”。**

---

## 1. 环境准备（每次都做）

```bash
cd /Users/liujin/DEV/AIProjects/bazi/qiazhi
python3.12 -m venv .venv312
source .venv312/bin/activate
python3.12 -m pip install -r v20/requirements.txt
```

可选：加载本机服务环境（含 DB/LLM 配置）：

```bash
set -a
source v20/.runtime/local/service.env
set +a
export V20_ENV=local_macos
export V20_RUNTIME_DIR=v20/.runtime/local
export V20_HOST=127.0.0.1
export V20_PORT=9020
```

运行脚本时如果不想每次写 `PYTHONPATH`，先 `source v20/scripts/_python.sh` 即可自动检查 Python 版本。

---

## 2. 第一层：基础验证（建议每次改完都做）

```bash
./v20/scripts/test_smoke.sh      # 最小变更核验
./v20/scripts/test_fast.sh       # 默认开发循环（默认 20s）
```

重点测试命令：

```bash
./v20/scripts/test_targeted.sh "knowledge"
./v20/scripts/test_services.sh    # 需要显式打开 RUN_V20_SERVICE_TESTS
RUN_V20_SERVICE_TESTS=1 ./v20/scripts/test_services.sh

RUN_V20_CORPUS_TESTS=1 ./v20/scripts/test_corpus.sh
```

---

## 3. 第二层：链路状态与单步 dry-run（最常用）

### 先看总体计划

```bash
python3.12 v20/scripts/run_decision_training_plan.py
python3.12 v20/scripts/run_knowledge_completion.py
```

### 知识库链路检查

```bash
python3.12 v20/scripts/run_knowledge_rule_library.py --summary
python3.12 v20/scripts/run_knowledge_rule_library.py --validate --limit 200
python3.12 v20/scripts/run_knowledge_rule_validation.py --summary --limit 200
python3.12 v20/scripts/run_knowledge_rule_review_overlay.py --progress
```

### 规则/裁决/问题排序/画像链路（只读）

```bash
python3.12 v20/scripts/run_dynamic_decision_training.py --progress
python3.12 v20/scripts/run_practitioner_calibration_training.py --progress
python3.12 v20/scripts/run_question_ranking_training.py --progress --top-k 8 --max-cases 48
python3.12 v20/scripts/run_rule_synthetic_training.py
python3.12 v20/scripts/run_rule_subcondition_split.py --domain wealth --limit 0 --per-rule 0 --progress
python3.12 v20/scripts/run_rule_replay_eval.py --domain wealth --limit 0 --per-rule 0 --progress
python3.12 v20/scripts/run_decision_registry_iteration.py --domain wealth --limit 0 --per-rule 0 --progress
python3.12 v20/scripts/run_rule_portrait_batch.py --progress
python3.12 v20/scripts/run_training_iteration.py --progress
```

### 一键运行完整训练迭代（本地）

```bash
python3.12 v20/scripts/run_training_iteration.py --progress --write
```

不带 `--write` 是只读，不会产生日志/阶段变更文件；带 `--write` 会写入：
`v20/.runtime/local/training/*/latest.json`。

---

## 4. 第三层：自进化与激活链路

### 产出自进化清单（本地）

```bash
python3.12 v20/scripts/run_self_evolution.py --progress --write
python3.12 v20/scripts/run_active_generation.py --progress --include-rule-batch --corpus-preview 240 --write
```

### 导入到 Postgres（显式 `--apply`）

```bash
python3.12 v20/scripts/import_decision_registry_postgres.py --apply
python3.12 v20/scripts/import_calibration_postgres.py --ledger practitioner_calibration_ledger --apply
python3.12 v20/scripts/import_calibration_postgres.py --ledger latent_event_calibration_ledger --apply
```

不加 `--apply` 时都是 dry-run，适合先看影响范围。

---

## 5. 第四层：518K 全量语料与训练素材（重作业）

### 5.1 先用预览/局部做完整流程演练

```bash
python3.12 v20/scripts/run_full_precompute.py --run-id v20_full_518k_main_preview --start 0 --limit 240 --progress --status-every 40
python3.12 v20/scripts/build_corpus_artifacts.py --run-id v20_full_518k_main_preview --progress --no-sqlite
python3.12 v20/scripts/build_corpus_artifacts.py --run-id v20_full_518k_main_preview --training
python3.12 v20/scripts/run_rule_synthetic_training.py --write
```

### 5.2 全量生产链路（按时间窗口执行）

```bash
python3.12 v20/scripts/run_full_precompute.py --run-id v20_full_518k_mainline --limit 518400 --status-every 500 --progress
python3.12 v20/scripts/build_corpus_artifacts.py --run-id v20_full_518k_mainline --progress --no-sqlite
python3.12 v20/scripts/build_corpus_artifacts.py --run-id v20_full_518k_mainline --status
python3.12 v20/scripts/build_corpus_artifacts.py --run-id v20_full_518k_mainline --training
```

### 5.3 可选：导出 + 入库

```bash
python3.12 v20/scripts/export_corpus_parquet.py --run-id v20_full_518k_mainline --target v20/.runtime/local/corpus/full_precompute/v20_full_518k_mainline/flat_labels.parquet
python3.12 v20/scripts/import_corpus_postgres.py --run-id v20_full_518k_mainline --progress --batch-size 1000
# 确认后入库
python3.12 v20/scripts/import_corpus_postgres.py --run-id v20_full_518k_mainline --apply --progress --batch-size 1000
```

注意：`--apply` 需要 `V20_DATABASE_URL` 可用，不可含占位符。

---

## 6. 服务控制（本地开发）

```bash
./v20/scripts/start_macos.sh
./v20/scripts/service_macos.sh start
./v20/scripts/service_macos.sh status
./v20/scripts/service_macos.sh logs --follow
./v20/scripts/service_macos.sh stop
```

Linux 同理替换为 `start_linux.sh` / `service_linux.sh`。

---

## 7. 常用状态查询（很重要）

```bash
python3.12 v20/scripts/run_training_iteration.py --status
python3.12 v20/scripts/run_self_evolution.py --status
python3.12 v20/scripts/run_rule_portrait_batch.py --status
python3.12 v20/scripts/run_dynamic_decision_training.py --status
python3.12 v20/scripts/build_corpus_artifacts.py --status
python3.12 v20/scripts/run_full_precompute.py --status --run-id v20_full_518k_mainline
```

每条 `--status` 一般会返回最近一次对应 artifact 的 JSON。

---

## 8. 推荐执行顺序（复制即用）

### 每次代码改动后的标准循环

```bash
./v20/scripts/test_fast.sh
./v20/scripts/test_targeted.sh "training or knowledge or rule"
python3.12 v20/scripts/run_training_iteration.py --progress --write
```

### 每日闭环（建议）

```bash
python3.12 v20/scripts/run_knowledge_rule_validation.py --summary
python3.12 v20/scripts/run_rule_synthetic_training.py
python3.12 v20/scripts/run_training_iteration.py --write --progress
python3.12 v20/scripts/run_self_evolution.py --write --progress
```

### 周级离线优化

```bash
python3.12 v20/scripts/run_rule_portrait_batch.py --write --progress
python3.12 v20/scripts/run_decision_registry_iteration.py --write --progress
python3.12 v20/scripts/run_rule_replay_eval.py --write --progress
python3.12 v20/scripts/run_rule_subcondition_split.py --write --progress
```

---

## 9. 遇到问题的排错顺序（建议）

1. `--status` 看上一次 artifact 是否成功。
2. `./v20/scripts/test_fast.sh` 再跑一次锁定回归。
3. 读取日志：
   - `./v20/scripts/service_macos.sh logs`
   - `tail -n 120 v20/.runtime/local/server_9020.log`
4. 用精简参数重跑单脚本（例如 domain 限制到单域），再逐步放开。
