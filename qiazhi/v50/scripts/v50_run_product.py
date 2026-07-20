from __future__ import annotations

import argparse
import os

import uvicorn


DEFAULT_LOCAL_DATABASE_URL = "postgresql:///qiazhi_v50?host=/tmp"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the DeepBazi Abu-led Mingli product.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8053)
    parser.add_argument("--database-url", default=os.environ.get("V50_DATABASE_URL", DEFAULT_LOCAL_DATABASE_URL))
    parser.add_argument("--abu-llm", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--llm-base-url", default=os.environ.get("V50_MINGLI_AGENT_BASE_URL", "http://dblife.com:11888"))
    parser.add_argument("--abu-model", default=os.environ.get("V50_ABU_LLM_MODEL", "gemma4:latest"))
    parser.add_argument("--reasoning-model", default=os.environ.get("V50_MINGLI_AGENT_MODEL", "qwen3.5:35b"))
    parser.add_argument("--reasoning-timeout", type=int, default=int(os.environ.get("V50_MINGLI_AGENT_TIMEOUT_SECONDS", "180")))
    args = parser.parse_args()

    os.environ["V50_DATABASE_URL"] = args.database_url
    os.environ["V50_ABU_LLM_ENABLED"] = "true" if args.abu_llm else "false"
    os.environ["V50_ABU_LLM_BASE_URL"] = args.llm_base_url
    os.environ["V50_ABU_LLM_MODEL"] = args.abu_model
    os.environ["V50_MINGLI_AGENT_BASE_URL"] = args.llm_base_url
    os.environ["V50_MINGLI_AGENT_MODEL"] = args.reasoning_model
    os.environ["V50_MINGLI_AGENT_TIMEOUT_SECONDS"] = str(args.reasoning_timeout)
    uvicorn.run("product.app:app", host=args.host, port=args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
