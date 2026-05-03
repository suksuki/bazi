# V20 0.13 Server Sync Runbook

## 目标

把当前 V20 同步到 Linux `0.13` 服务器，并使用服务器上的 Docker Postgres、Redis 和 `dblife.com` 暴露服务。

同步原则：

- 代码：走 GitHub 拉取，必要时才用 rsync 临时同步。
- 数据：Postgres 是权威存储，迁移和导入必须显式执行。
- Redis：只做缓存、队列、锁和短 TTL 状态，不同步。
- Runtime：`v20/.runtime/*` 是机器本地目录，不通过 Git 同步。
- Secrets：只写服务器本机 `service.env`，不提交到 GitHub。

## 本地同步前检查

在本机：

```bash
cd /Users/liujin/DEV/AIProjects/bazi/qiazhi

git status --short
python3.12 v20/scripts/run_main_chain_review.py
python3.12 v20/scripts/run_training_iteration.py
.venv/bin/python -m pytest -q \
  v20/tests/test_v20_runtime.py \
  v20/tests/test_v20_server.py \
  v20/tests/test_v20_ui.py \
  v20/tests/test_v20_access.py \
  v20/tests/test_v20_knowledge_ranking.py \
  v20/tests/test_v20_confidence_calibration.py
```

确认通过后提交并推送：

```bash
git add docs/v20 v20
git commit -m "v20 main chain learning and server sync readiness"
git push origin main
```

如果暂时不想提交，可以用 rsync，但这只能作为临时方式：

```bash
rsync -az --delete \
  --exclude '.git' \
  --exclude 'v20/.runtime' \
  --exclude '.venv' \
  --exclude '.venv312' \
  /Users/liujin/DEV/AIProjects/bazi/qiazhi/ \
  root@0.13:/opt/qiazhi/
```

## 服务器首次准备

SSH 到服务器：

```bash
ssh root@0.13
```

安装基础依赖：

```bash
apt update
apt install -y git python3.12 python3.12-venv python3-pip curl lsof screen
```

如果服务器 Python 包名不是 `python3.12`，先用系统已有 Python 3.12 路径替代后续命令。

## 拉取代码

推荐部署目录：

```bash
mkdir -p /opt
cd /opt

git clone https://github.com/suksuki/bazi qiazhi
cd /opt/qiazhi
git checkout main
git pull origin main
cd /opt/qiazhi/qiazhi
```

安装 Python 依赖：

```bash
python3.12 -m venv .venv312
.venv312/bin/python -m pip install -U pip
.venv312/bin/python -m pip install -r v20/requirements.txt
```

## 配置服务器 runtime env

创建服务器本机 env 文件：

```bash
mkdir -p v20/.runtime/linux_0_13
nano v20/.runtime/linux_0_13/service.env
```

参考内容：

```bash
V20_ENV=linux_0_13
V20_HOST=0.0.0.0
V20_PUBLIC_HOST=dblife.com
V20_PORT=9020
V20_RUNTIME_DIR=v20/.runtime/linux_0_13
V20_SERVICE_NAME=qiazhi-v20

PYTHON_BIN=/opt/qiazhi/qiazhi/.venv312/bin/python

V20_POSTGRES_ENABLED=1
V20_POSTGRES_HOST=127.0.0.1
V20_POSTGRES_PORT=5432
V20_POSTGRES_DB=qiazhi_v20
V20_POSTGRES_USER=qiazhi_v20_app
V20_POSTGRES_PASSWORD=CHANGE_ME
V20_DATABASE_URL=postgresql://qiazhi_v20_app:CHANGE_ME@127.0.0.1:5432/qiazhi_v20?sslmode=prefer

V20_REDIS_ENABLED=1
V20_REDIS_HOST=127.0.0.1
V20_REDIS_PORT=6379
V20_REDIS_DB=20
V20_REDIS_URL=redis://127.0.0.1:6379/20
```

如果 Docker Postgres/Redis 暴露的是其他端口，改 `V20_POSTGRES_PORT`、`V20_DATABASE_URL` 和 `V20_REDIS_URL`。

## 数据库准备

先确认 Docker 容器：

```bash
docker ps
```

创建数据库和用户时，按你服务器上 Postgres 容器名替换 `<postgres_container>`：

```bash
docker exec -it <postgres_container> psql -U postgres
```

在 psql 里：

```sql
CREATE USER qiazhi_v20_app WITH PASSWORD 'CHANGE_ME';
CREATE DATABASE qiazhi_v20 OWNER qiazhi_v20_app;
\c qiazhi_v20
CREATE EXTENSION IF NOT EXISTS pgcrypto;
GRANT ALL PRIVILEGES ON DATABASE qiazhi_v20 TO qiazhi_v20_app;
```

当前 V20 已有 schema contract 和显式应用脚本；正式写入前先看 schema：

```bash
.venv312/bin/python - <<'PY'
from v20.storage.postgres_schema import migration_manifest
import json
print(json.dumps(migration_manifest(), ensure_ascii=False, indent=2))
PY
```

先 dry-run：

```bash
python3.12 v20/scripts/apply_postgres_schema.py \
  --env-file v20/.runtime/linux_0_13/service.env
```

确认数据库已经备份、env 指向服务器库以后，再显式 apply：

```bash
python3.12 v20/scripts/apply_postgres_schema.py \
  --env-file v20/.runtime/linux_0_13/service.env \
  --apply
```

## 启动服务

在服务器 `/opt/qiazhi/qiazhi`：

```bash
./v20/scripts/service_linux.sh start
./v20/scripts/service_linux.sh status
curl -fsS http://127.0.0.1:9020/health
curl -fsS http://127.0.0.1:9020/api/v20/ops/sync-readiness
curl -fsS http://127.0.0.1:9020/api/v20/runtime/dependencies
```

查看日志：

```bash
./v20/scripts/service_linux.sh logs
./v20/scripts/service_linux.sh logs -f
```

停止或重启：

```bash
./v20/scripts/service_linux.sh stop
./v20/scripts/service_linux.sh restart
```

如果已经安装为 systemd 服务，优先使用 Linux 专用重启脚本：

```bash
./v20/scripts/restart_linux_systemd.sh
./v20/scripts/restart_linux_systemd.sh --hard
./v20/scripts/restart_linux_systemd.sh status
./v20/scripts/restart_linux_systemd.sh logs
```

注意：不要直接裸跑 `sudo systemctl restart qiazhi-v20` 作为常规发布命令。V20
可能正在处理 LLM 流式输出或 AnyIO 后台任务，systemd 的优雅停止会等待任务结束，
期间 9020 已关闭，容易看到短暂或持续的 `Connection refused`。重启统一使用上面的
wrapper；默认就是 hard restart。

## systemd 可选

生成 unit：

```bash
./v20/scripts/service_linux.sh systemd-unit
```

确认内容无误后再安装：

```bash
./v20/scripts/service_linux.sh systemd-unit > /etc/systemd/system/qiazhi-v20.service
systemctl daemon-reload
systemctl enable qiazhi-v20
systemctl start qiazhi-v20
systemctl status qiazhi-v20 --no-pager
```

安装 systemd 后，后续重启统一使用：

```bash
./v20/scripts/restart_linux_systemd.sh
```

## Nginx / 域名

如果 `dblife.com` 要反代到 V20：

```nginx
location /v20/ {
    proxy_pass http://127.0.0.1:9020/v20/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}

location /api/v20/ {
    proxy_pass http://127.0.0.1:9020/api/v20/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

UI 入口：

```text
https://dblife.com/v20/ui/
```

## 同步数据和训练产物

本地训练产物默认只写本地 `v20/.runtime/local`，不自动同步到服务器。

服务器上也可以直接跑：

```bash
python3.12 v20/scripts/run_main_chain_review.py
python3.12 v20/scripts/run_training_iteration.py --write --progress
python3.12 v20/scripts/run_arbitration_loop.py --write --progress
```

全量长跑：

```bash
python3.12 v20/scripts/run_training_iteration.py \
  --write \
  --progress \
  --dynamic-limit 0 \
  --rule-iteration-limit 0 \
  --include-replay-eval \
  --include-rule-batch
```

518K corpus 导入 Postgres 的顺序：

```bash
python3.12 v20/scripts/run_full_precompute.py --run-id v20_full_518k_mainline --limit 518400 --status-every 500 --progress
python3.12 v20/scripts/build_corpus_artifacts.py --run-id v20_full_518k_mainline --progress --no-sqlite
python3.12 v20/scripts/import_corpus_postgres.py \
  --run-id v20_full_518k_mainline \
  --env-file v20/.runtime/linux_0_13/service.env \
  --progress
```

最后一步默认 dry-run；确认后再加 `--apply`：

```bash
python3.12 v20/scripts/import_corpus_postgres.py \
  --run-id v20_full_518k_mainline \
  --env-file v20/.runtime/linux_0_13/service.env \
  --progress \
  --apply
```

## 每次同步更新

本机：

```bash
git status --short
python3.12 v20/scripts/run_main_chain_review.py
.venv/bin/python -m pytest -q v20/tests/test_v20_runtime.py v20/tests/test_v20_server.py v20/tests/test_v20_ui.py
git add docs/v20 v20
git commit -m "v20 update"
git push origin main
```

服务器：

```bash
cd /opt/qiazhi
git pull origin main
cd /opt/qiazhi/qiazhi
.venv312/bin/python -m pip install -r v20/requirements.txt
./v20/scripts/service_linux.sh restart
./v20/scripts/service_linux.sh status
```
