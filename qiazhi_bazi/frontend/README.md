# Qiazhi-Bazi Frontend

前端采用 `Next.js 14 App Router + Tailwind + feature-oriented MVC`。

## 当前结构

```text
frontend/
├── src/app/                        # 页面入口
├── src/features/                   # controller / view / helpers / tests
├── src/components/                 # 可复用 UI 组件
└── src/constants/                  # 术语映射与静态表
```

## 环境变量

| 变量 | 说明 |
|------|------|
| `NEXT_PUBLIC_QIAZHI_API` | 后端根 URL；未配置且 `NODE_ENV=development` 且页面为环回主机时默认 `http://127.0.0.1:8001`。公网**不要**填 `127.0.0.1`；与 Nginx 同域反代 `/api` 时**留空** |
| `NEXT_PUBLIC_QIAZHI_SAME_ORIGIN_PROXY` | 设为 `1` 时强制由 Next 把 `/api` 反写到 `QIAZHI_INTERNAL_API_URL`（仅当 Nginx **未**单独反代 `/api` 时用） |
| `NEXT_PUBLIC_QIAZHI_DISABLE_SAME_ORIGIN_REWRITE` | 设为 `1` 时关闭生产构建里自动开启的 `/api` rewrite（**Nginx 已 `location /api` 到 uvicorn 时必须设**） |
| `QIAZHI_INTERNAL_API_URL` | 仅 `next build` 时 Node 使用；Next 反代 `/api` 时的上游，默认 `http://127.0.0.1:8001` |
| `NEXT_PUBLIC_QIAZHI_ADMIN_TOKEN` | 仅内网/单人调试：浏览器请求头 `X-Admin-Token`。**切勿**在公网多用户环境依赖此前端变量保管密钥；生产应走后端代理或仅服务端持有 token |
| （后端）`QIAZHI_ADMIN_TOKEN` | 未配置时后端使用弱默认 `local-dev-qiazhi-admin`；公网请改为强随机并与本表上一行前端变量一致 |

### 生产（Nginx 把 `/api` 交给 FastAPI，Next 只出页面）

1. 按 `../deploy/nginx-qiazhi-dblife.example.conf` 改站点：``location /api/`` → uvicorn 端口，``location /`` → Next 端口。  
2. 将本目录下 `.env.production.example` 复制为 `.env.production`，按需改 token。  
3. 在服务器执行 `pnpm build` 后启动 `pnpm start`（或你的进程管理器）。

## 开发

```bash
cd qiazhi_bazi/frontend
npm install
npm run dev
```

浏览器打开 `http://localhost:3000`。

## 测试与构建

```bash
cd qiazhi_bazi/frontend
npm run typecheck   # TypeScript，无产物
npm run lint        # Next.js ESLint
npm test            # Vitest 全量（单元 + 集成风格用例）
npm run test:stream-board   # 仅 stream-board 相关，加快反馈
npm run test:ci     # 提 PR 前推荐：typecheck + lint + test + build
npm run build
```

说明：`test:ci` 覆盖类型检查、静态检查、全部 Vitest 与生产构建，作为前端回归基线；与仓库根文档中的后端 `pytest` 命令一起构成全栈自动化验证。

## 设计文档

- [总体架构](/home/hlsystem/bazi/qiazhi_bazi/docs/architecture/OVERVIEW.md)
- [前端 MVC 设计](/home/hlsystem/bazi/qiazhi_bazi/docs/architecture/FRONTEND_MVC.md)
- [测试策略](/home/hlsystem/bazi/qiazhi_bazi/docs/testing/TEST_STRATEGY.md)
