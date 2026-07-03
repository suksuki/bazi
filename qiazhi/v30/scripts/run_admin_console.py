from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import uvicorn


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the standalone Qiazhi V30 Admin Console frontend.")
    parser.add_argument("--host", default=os.getenv("V30_ADMIN_FRONTEND_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.getenv("V30_ADMIN_FRONTEND_PORT", "9031")))
    parser.add_argument("--runtime-api-base-url", default=os.getenv("V30_RUNTIME_API_BASE_URL", "http://127.0.0.1:9030"))
    args = parser.parse_args()

    os.environ["V30_ADMIN_FRONTEND_PORT"] = str(args.port)
    os.environ["V30_RUNTIME_API_BASE_URL"] = args.runtime_api_base_url.rstrip("/")
    uvicorn.run("v30.api.admin_frontend_app:app", host=args.host, port=args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
