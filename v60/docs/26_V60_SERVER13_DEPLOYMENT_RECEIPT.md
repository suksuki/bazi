# V60 Server 13 部署与数据库恢复凭证

日期：2026-09-04

授权：Owner 明确授权同步 Server 13、重装数据库并恢复档案

部署范围：V60 受控测试环境，不改变专业发布门

## 1. 最终运行状态

| 项目 | 已验证值 |
| --- | --- |
| 公网入口 | `https://dblife.com/experience` |
| Git 提交 | `e7f8461881969820355b880bdbacb93bae663800` |
| Server 13 | `server4` / `192.168.0.13` |
| 应用服务 | `qiazhi-v60.service`，`active / enabled`，重启计数 0 |
| 应用监听 | `127.0.0.1:9050`，由现有 nginx 提供 TLS 与反向代理 |
| PostgreSQL | 官方 `postgres:18`，仅监听 `127.0.0.1:5432` |
| PostgreSQL 镜像 | `postgres@sha256:4ef4dbc939d61acea57712655ddb4b4ab27419c913f94cca0cd57cb3ea3c2280` |
| 数据卷 | 独立 `qiazhi_v60_pgdata` |
| Alembic | `0053_remove_dream_runtime` |
| Foundation | `v60.foundation.045` |
| 公开内部面 | `V60_INTERNAL_SURFACES_ENABLED=false` |

发布目录使用不可变 Git 目录与可切换指针：

```text
/home/hlsystem/abu-v60/current
-> releases/e7f8461881969820355b880bdbacb93bae663800
```

历史脏工作区 `/home/hlsystem/bazi` 没有被 pull、reset 或覆盖。旧 Docker 卷
`rag_pgdata` 也原样保留，没有被 V60 复用。

## 2. V50 退役原因与处理

旧 `qiazhi-v50.service` 配置了失败后自动重启，但它依赖的 PostgreSQL 容器已经被
删除，因此每次连接 `127.0.0.1:5432` 都失败，再由 systemd 拉起，最终累计重启
35,593 次。

部署前已停止并禁用该服务；Owner 随后删除 unit 并执行 `daemon-reload`。最终
`systemctl` 返回 `No such file or directory`，9050 由 V60 独占。删除前的 unit 备份为：

```text
/home/hlsystem/abu-backups/v50-service-retired-20260904/qiazhi-v50.service
```

## 3. 数据库恢复凭证

本机 V60 完整快照使用 PostgreSQL Custom Format、`--no-owner --no-acl` 生成，并在
上传前后核对 SHA-256：

```text
source dump:
/home/hlsystem/abu-v60/backups/qiazhi_v60.local-source-20260904.dump
sha256: 9c446ecadc13176f24228c4d7d548d9a757339de267c56d88ff0caeb1d9da8b6
objects: 257
```

恢复后重新生成了可独立恢复的服务器备份：

```text
post-deploy dump:
/home/hlsystem/abu-v60/backups/qiazhi_v60.postdeploy-20260904.dump
sha256: e942cf793de901a0c4e8e2510ef46cb45dfd3f527fa7215fff49394479d19ee9
objects: 257
mode: 0600
```

恢复后数据库共有 30 张业务表、26 个媒体资产、38 个 Profile 与 38 个 Case；其中
恰有一个私密真实账户持有 20 个 Profile 和 20 个 Case，与源快照一致。其余记录包括
受控系统／角色数据。数据库只存在以下业务 schema：

```text
cognition, identity, media, mingli, platform, public
```

`dream`、`story`、`world` 的验证计数为 0。

## 4. 局域网模型与声音

Server 13 不通过公网域名回环调用模型：

```text
Ollama: http://192.168.0.7:11434
TTS:    http://192.168.0.7:7860/tts
```

真实 Qwen3.8:27B 探针返回“模型可用”：总耗时 8.439 秒，其中模型冷载入
7.970 秒、生成 3 token 耗时 0.157 秒。`keep_alive=30m` 用于避免连续读取时重复冷载入。

真实阿布 Dylan 探针在约 3.2 秒内生成 2.320 秒音频；结果为 24 kHz、16-bit、单声道
PCM WAV，共 111,404 bytes。内网地址只存在服务端环境文件中，不下发浏览器。

## 5. 公网与运行验收

以下检查均通过：

- `https://dblife.com/health`：HTTP 200、数据库 `ready`；
- `https://dblife.com/api/v60/health`：HTTP 200、Foundation 一致；
- `https://dblife.com/`：HTTP 200；
- `https://dblife.com/experience`：HTTP 200；
- 版本化 JavaScript 资产：HTTP 200，上传前后聚合 SHA-256 一致；
- 私密 Home 未登录请求：HTTP 401；
- PostgreSQL 容器：`healthy`；
- systemd：`NeedDaemonReload=no`、应用重启计数 0。

部署前本地基线还通过 343 项后端测试、11 项合同定义跳过、Ruff、TypeScript、Vite
production build、静态公开边界审计及桌面／手机真实浏览器验收。健康兼容补丁另通过
9 项 System API 测试。

## 6. 发布边界

本次是 Owner 授权的服务器部署与受控测试，不把系统描述为已经达到高级命理师专业
资格。Runtime 继续保持：

```text
publication_allowed=false
professionally_reviewed=false
```

扩大公开范围或作出专业资格结论仍需 Owner 单独裁决。
