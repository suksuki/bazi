# Qiazhi-Bazi Frontend

Next.js 14（App Router）+ Tailwind CSS，手机端优先。

## 环境变量

| 变量 | 说明 |
|------|------|
| `NEXT_PUBLIC_QIAZHI_API` | 后端根 URL，默认 `http://127.0.0.1:8001` |

## 开发

```bash
cd qiazhi_bazi/frontend
npm install
npm run dev
```

浏览器打开 `http://localhost:3000`。

## 目录说明

- `src/app/`：页面与布局（Next 14 推荐）
- `src/components/`：如 `MobileBaziInput` 手机端测算表单
- `src/pages/`：若需兼容 Pages Router 可在此增加路由；当前 MVP 使用 `src/app` 即可
