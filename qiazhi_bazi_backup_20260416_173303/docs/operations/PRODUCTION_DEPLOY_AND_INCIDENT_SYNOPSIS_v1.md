# 生产部署与线上问题综述（dblife / 同源 / 端口）

本文汇总一次典型「公网 HTTPS 前端 + 本机 FastAPI」联调中出现的**根因**与**对应措施**，便于后续排障与新人上手。时间背景：2026-04 前后。

---

## 1. 浏览器从 `https://dblife.com` 访问 `http://127.0.0.1:8001`（CORS / 错主机）

**现象**：控制台报 CORS，`No Access-Control-Allow-Origin`；或请求落到访客本机而非服务器。

**根因**：

- 页面来源是 **HTTPS + 公网域名**，API 却是 **HTTP + 环回地址**，属于**跨源**；预检失败时表现为 CORS。
- 更本质：**公网页上的 `127.0.0.1` 指向的是每个用户自己的电脑**，不是服务器上的 uvicorn。

**措施**（二选一，勿混用）：

- **方案 A（推荐）**：Nginx 将 `https://域名/api/` 反代到本机 `127.0.0.1:8001`；前端构建中 **不要** 把 `NEXT_PUBLIC_QIAZHI_API` 写成环回；并设 `NEXT_PUBLIC_QIAZHI_DISABLE_SAME_ORIGIN_REWRITE=1`，避免 Next 与 Nginx 双反代 `/api`。示例：`deploy/nginx-qiazhi-dblife.example.conf`，模板：`frontend/.env.production.example`。
- **方案 B**：全部流量进 Next，由 `next.config.mjs` 的 rewrites 把 `/api` 转到 uvicorn；此时 Nginx **不要**再单独 `location /api` 抢流量。

仓库中还做了：生产构建在「未配公网 API URL 或仍填环回」时默认启用同源 `/api` rewrite；运行时在 **HTTPS 非公网页** 且 API 仍指向环回时，将 API 基址强制为同源 `/api`（可用环境变量关闭），见 `frontend/next.config.mjs`、`frontend/src/lib/qiazhiApiBase.ts`。

---

## 2. 管理页「Test DB」失败，但本机 `psql`/Python 能连库

**根因**：

- 浏览器**从不直连** Postgres；请求走 **`POST /api/admin/db-status`**，必须先能访问 FastAPI。
- 前端原先只把 **Database URL 输入框** 发给后端；向导里填了用户名/密码却**未点「生成 DATABASE_URL」**时，连接串仍是旧的或空的，后端拿到的凭据错误。

**措施**：在 `useAdminSettingsController` 中合并向导字段与 URL 规则，并在失败时区分网络/JSON/HTTP 错误；见 `frontend/src/features/admin-settings/`。

---

## 3. PostgreSQL 容器里没有 `postgres` 角色

**根因**：镜像初始化时使用了自定义 `POSTGRES_USER`（如 `rag`），则默认超级用户不是 `postgres`。

**措施**：用 `psql -U <POSTGRES_USER> -d <POSTGRES_DB>`；密码与角色只在部署配置里，库里查不出明文密码。

---

## 4. `restart_local_services.sh` 健康检查 `8001 Connection refused`

**根因（之一）**：`init_db()` 因 `DATABASE_URL` 密码错误等在启动阶段失败，旧版 `main.py` 捕获后又 **`raise`**，进程直接退出，端口无监听。

**措施**：`init_db` 失败时**降级启动**（进程仍监听）；`/health` 存活，`/ready` 反映 DB 状态。见 `backend/main.py`。

**根因（之二）**：脚本先起后端再起长时间 `pnpm build`，期间若后端已崩溃，健康检查易误判；且 `curl` 与 `nohup` 同一行粘贴易**早于 bind** 执行。

**措施**：脚本改为**先 build 再起后端**；启动脚本内轮询端口就绪；见 `restart_local_services.sh`、`scripts/start_backend_8001.sh`。

---

## 5. `/_next/static/chunks/*.js` 报 500 / 404

### 5.1 旧 `next-server` 占死 3001（本次核心）

**现象**：重新 `pnpm build` 后，本机 `curl` chunk 仍 404；`ss` 显示监听 PID 与脚本打印的新 PID **不一致**。

**根因**：`pkill -f "next start.*3001"` **杀不掉**已变为 **`next-server`** 的进程；新进程抢不到端口；旧进程用**旧工作目录/旧 `.next`** 响应，与新磁盘上的 chunk 名不一致 → **404**（或异常表现被浏览器记为失败）。

**措施**：按端口释放：`scripts/_free_port.sh`，由 `scripts/start_frontend_3001.sh` 在启动前调用；并辅以 `pkill next-server` 模式。

### 5.2 浏览器长期缓存旧 HTML

**根因**：HTML 里引用的 chunk 哈希来自**旧一次 build**，服务端已换新 `BUILD_ID`，旧文件名不存在 → 404。

**措施**：对站点「清空缓存并硬性重新加载」或使用无痕窗口验证。

### 5.3 Nginx 把 `/_next` 指错上游（次要）

若本机 `curl 127.0.0.1:3001/_next/...` 正常而域名异常，检查 Nginx 是否将静态误指到 FastAPI；示例配置中已增加显式 `location ^~ /_next/`。

---

## 6. 仍须单独处理的事项

- **`DATABASE_URL`** 与真实 Postgres 密码不一致时，业务写库仍会失败；降级启动只保证进程与机房部分能力可用。需在 `backend/.env` 或管理页中修正连库配置。

---

## 7. 控制台「Failed to load resource: status 500」但没说哪个地址

Chrome 里有时只显示 **500** 而不展开完整 URL，需要先**定位请求**再查日志。

**操作（浏览器）**：

1. 打开 **开发者工具 → Network**，勾选 **Preserve log**，复现一次。  
2. 点 **Status** 列排序，找 **红色 500** 的那一行。  
3. 看 **Name / Request URL** 属于哪一类：  
   - **`/_next/static/...`**：多为 **Next 进程异常** 或 **Nginx 指错上游**（参见 §5）。  
   - **`/__nextjs_...` 或文档 HTML**（类型 `document`）：多为 **RSC/页面渲染** 在服务端抛错，查 **`frontend-3001.log`** 同一时间戳。  
   - **`/api/...`**：多为 **FastAPI 未捕获异常** 或 **网关超时伪装成 5xx**，查 **`backend-8001.log`** 与 Nginx `error.log`。

**操作（服务器，把下面 URL 换成 Network 里那条）**：

```bash
# 看状态码与 Server 响应头（判断是 Next 还是 nginx 还是上游）
curl -sSI 'https://你的域名/从Network复制的路径'

# 本机直连对照（绕过 Nginx）
curl -sSI 'http://127.0.0.1:3001/同上路径'
curl -sSI 'http://127.0.0.1:8001/同上路径'   # 仅当路径以 /api 开头时
```

**常见含义简述**：

| 情况 | 含义 |
|------|------|
| 仅域名 500、本机 3001 200 | Nginx / 证书 / 反代缓冲 / 上游超时。 |
| 本机 3001 也是 500 | Next 渲染或静态服务异常，看 `next` 日志栈。 |
| 仅 `/api/*` 500 | 后端异常或未连库；读 uvicorn 日志与 `DATABASE_URL`。 |

**勿用字面「路径」测 URL**：文档示例里的「路径」是占位符，应换成 Network 里**真实**路径（如 `/_next/static/chunks/xxx.js`）；否则 Next 对未知路由返回 **404**，与 500 无关。

---

## 8. 日志里曾出现的典型错误（节选）

### 8.1 `EADDRINUSE :::3001`

**含义**：新起的 `next start` 绑不上 3001，**该端口已被其它 `next-server` 占用**。

**措施**：部署前执行 `scripts/start_frontend_3001.sh`（内含按端口 `ss` 释放），或手动 `ss -ltnp | grep 3001` 后杀掉旧 PID 再起。

### 8.2 `Failed to find Server Action ... older or newer deployment`

**含义**：浏览器仍持有**旧一次部署**生成的 RSC / Server Action 请求体，当前运行的 Next **BUILD_ID 已变**，服务端找不到对应 action id → 常见表现是页面或某请求 **500**。

**措施**：用户侧 **硬性刷新 / 清空站点数据**；发布侧 **同一次** `pnpm build` 产出的 `.next` 与正在跑的 `next start` 一致，且**只跑一个** 3001 实例。避免「新 build 已上盘但旧进程仍占端口」的混跑窗口。

### 8.3 `password authentication failed for user "qiazhi_admin"`

**含义**：`backend/.env` 中 `DATABASE_URL` 与 Postgres 实际口令不一致（与前端无关）。

**措施**：改对密码或 `ALTER USER` 后重启 uvicorn。

### 8.4 `Connection refused` 与「V12 后本地连不上」（多数非代码回归）

**常见根因**：

1. **运行环境变了**：管理页或 API 部署在云上/容器里时，`DATABASE_URL` 里的 `127.0.0.1` 指 **该进程所在机器**，不是开发用的笔记本；本机未起 Postgres 或端口未映射 → `Connection refused`。
2. **仅配置了旧变量**：仓库 README 写明兼容 `QIAZHI_BAZI_DB_URL`；若只设了该变量而未设 `DATABASE_URL`，旧版 `session.py` 曾**不读取**兼容变量（易误判为「重构坏了」）。当前已在 `app/db/session.py` 合并读取。
3. **V12 持久化**：`metadata.persistence_layer` / 三色 `ArbiterBias` **不参与**解析或覆盖 `DATABASE_URL`；若怀疑误配，应查 **容器/系统环境变量** 与 **Admin 页 POST 的 db_url**，而非 `persistence_layer`。

**一键自检**：在 `backend` 下执行 `python3 scripts/audit_db_connectivity.py`（含 `ss`、TCP、`SELECT 1` 与上述说明）。

**Docker 连宿主 Postgres**：见仓库 `deploy/docker-database-url.example.env`（`host.docker.internal` 或 compose 服务名）。

**SSL / 驱动**：`OperationalError: connection refused` 为 **TCP 未接通**；若为证书/SSL 协商失败，文案多为 `SSL SYSCALL` / `no pg_hba.conf` 等，需改 `sslmode` 或 `pg_hba.conf`，与「连接池驱动升级」无必然关系；连接串仍支持 `postgresql+psycopg2` 与 `postgresql+psycopg`。

---

## 9. 相关文件索引

| 主题 | 路径 |
|------|------|
| Nginx 示例 | `deploy/nginx-qiazhi-dblife.example.conf` |
| 前端生产 env 模板 | `frontend/.env.production.example` |
| 释放端口 + 起前后端 | `scripts/_free_port.sh`、`scripts/start_frontend_3001.sh`、`scripts/start_backend_8001.sh` |
| 静态 chunk 自检 | `scripts/check_next_static.sh` |
| 泛型 500 / 白屏一键扫 | `scripts/diagnose_web_stack.sh` |
| 本机一键重启 | `restart_local_services.sh` |
| CORS 默认与合并 | `backend/main.py` |
| 前端 README 部署摘要 | `frontend/README.md` |
| DB 连接回归自检脚本 | `backend/scripts/audit_db_connectivity.py` |
| Docker 下 DATABASE_URL 示例 | `deploy/docker-database-url.example.env` |

---

*文档版本：v1.4；与代码变更以仓库为准。*

---

## 10. V12.92 运行期状态信号（新增）

### 10.1 `/api/v1/final-verdict` 返回 `409 FINAL_VERDICT_FLOW_STATE_CONFLICT`

**含义**：当前会话处于 `PROBE_WAITING`，终判按协议被锁定。  
**处理顺序**：先完成 `InterruptOverlay` 的 `resume` 反馈，再重试终判。  
**不是**：网络故障或后端崩溃。

### 10.2 页面显示 `⚠ 待逻辑确认（PROBE_WAITING）` 但看不到确认按钮

优先判断为**前端静态资源版本落后**（线上仍在跑旧包）。  
V12.92 新版已加前端兜底：`flow_state=probe_waiting` 且缺少 `interrupt_request` 时，也会强制渲染可点击的 `InterruptOverlay`。

### 10.3 `/api/v1/brain/m5-gold-stats` 连续 500

V12.92 新版已改为降级模式：DB/Schema 未就绪时返回 `200 + degraded=true`，并给出安全默认值，避免监控面板 500 风暴。  
若仍见 500，优先排查是否混跑旧后端实例或网关缓存旧上游。
