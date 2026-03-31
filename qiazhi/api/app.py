"""兼容入口：复用 qiazhi_core.main 的 FastAPI app。"""
from qiazhi_core.main import app

__all__ = ["app"]
