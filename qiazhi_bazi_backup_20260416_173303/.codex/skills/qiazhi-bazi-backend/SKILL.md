---
name: qiazhi-bazi-backend
description: Use when working on the FastAPI backend in this repo, especially API routes, service extraction, helper normalization, physics/audit flows, or admin/runtime-config paths.
---

# Qiazhi-Bazi Backend

Use this skill for backend implementation and refactors.

## Preferred placement

- HTTP contracts and routes: `backend/app/api/`
- Business orchestration: `backend/app/services/`
- Pure transformation helpers: `backend/app/services/helpers/`
- Domain engines: `backend/app/skills/`
- Persistence: `backend/app/db/`

## Current reference services

- `consultation_service.py`
- `admin_service.py`
- `analysis_service.py`
- `audit_service.py`
- `llm_service.py`

## Refactor guardrails

- Keep router thin
- Keep helper pure when possible
- Do not push HTTP exceptions deep into helpers
- Preserve current response shapes unless explicitly asked to change them

## Validation

Run:

```bash
cd qiazhi_bazi/backend
pytest tests/unit tests/integration -q
```
