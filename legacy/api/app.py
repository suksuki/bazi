"""
FDS 老系统 API：仅挂载 v2 流形追踪等路由（与 Qiazhi-Bazi 隔离）。

启动（在仓库根目录）::

    cd legacy && uvicorn api.app:app --reload --host 0.0.0.0 --port 8000

或::

    PYTHONPATH=legacy uvicorn api.app:app --reload --host 0.0.0.0 --port 8000
"""
from fastapi import FastAPI

from api.v2.manifold import router as manifold_router

app = FastAPI(title="FDS Legacy API", version="2.0")
app.include_router(manifold_router, prefix="/api/v2")
