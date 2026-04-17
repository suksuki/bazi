---
name: qiazhi-bazi-architecture
description: Use when working in this repo on architecture, refactors, module boundaries, or design documentation. Covers the required frontend MVC pattern, backend router-service-helper layering, and which project docs must be updated after structural changes.
---

# Qiazhi-Bazi Architecture

Use this skill for refactors, large code moves, architectural reviews, or any task that changes module boundaries.

## Required structure

- Frontend: `page -> controller hook -> view -> pure helpers`
- Backend: `router -> service -> helper/model/skill`
- Do not change business logic while restructuring unless the user explicitly asks.

## Documentation obligations

When architecture changes, update these files if relevant:

- `README.md`
- `docs/README.md`
- `docs/architecture/OVERVIEW.md`
- `docs/architecture/FRONTEND_MVC.md`
- `docs/architecture/BACKEND_SERVICE_ARCH.md`

## Refactor checklist

1. Keep route and UI contracts stable.
2. Move pure logic into helpers first.
3. Add or update tests for each extracted unit.
4. Run backend tests if backend changed.
5. Run frontend tests and build if frontend changed.

## Repo examples

- Frontend MVC example: `frontend/src/features/stream-board/`
- Backend service example: `backend/app/services/`
- Backend helper example: `backend/app/services/helpers/`
