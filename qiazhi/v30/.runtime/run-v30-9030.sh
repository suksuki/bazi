#!/bin/sh
cd /Users/liujin/DEV/AIProjects/bazi/qiazhi/v30 || exit 1
export V30_DATABASE_URL='postgresql:///qiazhi_v30'
export V30_REPOSITORY='postgres'
export V30_LLM_ENABLED='true'
export V30_LLM_EXECUTE='true'
export V30_LLM_BASE_URL='http://127.0.0.1:11435/v1'
export V30_LLM_MODEL='gemma4:latest'
export V30_LLM_PROVIDER='ollama_native'
exec /Users/liujin/DEV/AIProjects/bazi/qiazhi/.venv312/bin/python -m uvicorn v30.api.app:app --host 127.0.0.1 --port 9030
