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
| `NEXT_PUBLIC_QIAZHI_API` | 后端根 URL，默认 `http://127.0.0.1:8001` |
| `NEXT_PUBLIC_QIAZHI_ADMIN_TOKEN` | 仅内网/单人调试：浏览器请求头 `X-Admin-Token`。**切勿**在公网多用户环境依赖此前端变量保管密钥；生产应走后端代理或仅服务端持有 token |
| （后端）`QIAZHI_ADMIN_TOKEN` | **必填**非空后 `/api/admin/*` 才可用；未配置时管理接口返回 503 |

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
