# Qiazhi-Bazi Web（Next.js）

```bash
cd qiazhi/web
cp .env.local.example .env.local
npm install
npm run dev
```

浏览器：<http://localhost:3000/qiazhi>

后端（独立进程，与老 FDS 隔离）：在仓库根目录执行 `uvicorn qiazhi.api.app:app --reload --port 8001`，并在 `.env.local` 中设置 `NEXT_PUBLIC_API_URL=http://localhost:8001`。

可选：设置 `QIAZHI_FRONTEND_ORIGIN=http://localhost:3000` 后访问 <http://localhost:8001/qiazhi> 可重定向到本前端。
