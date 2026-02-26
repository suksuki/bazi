"""
FDS API 入口：挂载 v2 流形追踪等路由。
启动方式：uvicorn api.app:app --reload --port 8000
GET /api/v2/manifold/trace/{user_id}
"""
from fastapi import FastAPI

from api.v2.manifold import router as manifold_router

app = FastAPI(title="FDS API", version="2.0")
app.include_router(manifold_router, prefix="/api/v2")
