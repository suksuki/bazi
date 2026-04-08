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
| `NEXT_PUBLIC_QIAZHI_ADMIN_TOKEN` | 可选，admin 页面调用后端时携带 |

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
npm test
npm run build
```

## 设计文档

- [总体架构](/home/hlsystem/bazi/qiazhi_bazi/docs/architecture/OVERVIEW.md)
- [前端 MVC 设计](/home/hlsystem/bazi/qiazhi_bazi/docs/architecture/FRONTEND_MVC.md)
- [测试策略](/home/hlsystem/bazi/qiazhi_bazi/docs/testing/TEST_STRATEGY.md)
