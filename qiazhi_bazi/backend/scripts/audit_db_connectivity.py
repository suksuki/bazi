#!/usr/bin/env python3
"""
数据库连接「回归性」自检（网络 + 环境变量来源 + V12 误配说明）。

用法（在 backend 目录）::

  python3 scripts/audit_db_connectivity.py

不要求已安装 PostgreSQL；若仅做环境审计可跳过 socket（见退出码说明）。
"""
from __future__ import annotations

import os
import socket
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse, urlunparse

_BACKEND = Path(__file__).resolve().parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))


def _load_dotenv_file(path: Path) -> None:
    """极简 .env 加载（不依赖 python-dotenv）；已存在于 os.environ 的键不覆盖。"""
    if not path.is_file():
        return
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        if "=" not in s:
            continue
        key, _, val = s.partition("=")
        key = key.strip()
        if not key or key in os.environ:
            continue
        val = val.strip().strip("'").strip('"')
        os.environ[key] = val


def _mask_url(raw: str) -> str:
    try:
        p = urlparse(raw)
        if p.password:
            netloc = p.netloc.replace(p.password, "***")
            return urlunparse((p.scheme, netloc, p.path, p.params, p.query, p.fragment))
    except Exception:
        pass
    return raw


def _effective_db_url() -> tuple[str, str]:
    """返回 (url, source_label)。"""
    d = (os.getenv("DATABASE_URL") or "").strip()
    if d:
        return d, "DATABASE_URL"
    q = (os.getenv("QIAZHI_BAZI_DB_URL") or "").strip()
    if q:
        return q, "QIAZHI_BAZI_DB_URL"
    return "", "(未设置)"


def main() -> int:
    print("=== DB 连接回归审计 ===\n")
    _load_dotenv_file(_BACKEND / ".env")
    print("[0] 已尝试加载 backend/.env（存在则解析；不覆盖当前 shell 已 export 的键）\n")

    # 1) ss
    print("[1] 本机 5432 监听（ss -lntp | grep 5432）")
    try:
        r = subprocess.run(
            ["bash", "-lc", "ss -lntp 2>/dev/null | grep 5432 || true"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        out = (r.stdout or "").strip()
        print(out if out else "  (无匹配：本机未监听 5432，或 ss 不可用)")
    except Exception as e:  # noqa: BLE001
        print(f"  ss 调用跳过: {e}")
    print()

    # 2) 环境变量（不 import app.db.session，避免未配置时直接抛 RuntimeError）
    raw, src = _effective_db_url()
    print("[2] 进程将使用的连接串来源与脱敏值")
    print(f"  source: {src}")
    if raw:
        print(f"  url:    {_mask_url(raw)}")
        p = urlparse(raw)
        host = p.hostname or ""
        port = p.port or 5432
        print(f"  host:   {host!r}  port: {port}")
        q = (p.query or "").lower()
        if "sslmode" in q or "ssl=" in q:
            print(f"  query:  含 SSL 相关参数（若握手失败可尝试 sslmode=disable 仅限内网）")
    else:
        print("  (未设置 DATABASE_URL / QIAZHI_BAZI_DB_URL，导入 app.db.session 将失败)")
    print()

    # 3) socket
    print("[3] TCP 探测（socket.connect）")
    if not raw:
        print("  跳过（无 URL）")
        return 2
    p = urlparse(raw)
    host = p.hostname or "127.0.0.1"
    port = int(p.port or 5432)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(2.0)
    try:
        s.connect((host, port))
        print(f"  OK: {host}:{port} 可建立 TCP 连接")
        code = 0
    except OSError as e:
        print(f"  FAIL: {host}:{port} -> {e}")
        print()
        print("[提示] 若在 Docker 内连宿主 Postgres，环回 127.0.0.1 指向容器自身；可改用:")
        print("  postgresql+psycopg2://USER:PASS@host.docker.internal:5432/DBNAME?sslmode=disable")
        print("  或 Compose 服务名（与 db 服务同网络），见 deploy/docker-database-url.example.env")
        code = 1
    finally:
        s.close()
    print()

    # 4) V12 / 持久化层审计结论（静态）
    print("[4] V12 ArbiterBias / persistence_layer 与 DATABASE_URL")
    print("  结论：代码路径中 persistence_layer 仅承载业务偏置/裁决/PSV 覆盖等，")
    print("  **不会**写入或覆盖 DATABASE_URL；会话层仅读取环境变量（见 app/db/session.py）。")
    print("  若「重构后」才失败，更常见原因是：运行环境从本机变为容器/云端、或仅设置了 QIAZHI_BAZI_DB_URL。")
    print()

    # 5) 可选：SQLAlchemy 真连（需已能 import session）
    print("[5] SQLAlchemy 探测（可选）")
    try:
        from sqlalchemy import text

        from app.db.session import DB_URL, _engine

        print(f"  app.db.session.DB_URL 与 [2] 一致: {DB_URL == raw}")
        with _engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("  SELECT 1: OK")
    except Exception as e:  # noqa: BLE001
        print(f"  跳过或失败: {e}")

    return code


if __name__ == "__main__":
    raise SystemExit(main())
