---
name: qiazhi-bazi-testing
description: Use when adding, updating, or reviewing tests in this repo. Covers the repo's unit/integration/regression strategy, preferred test locations, and the required commands for backend and frontend validation.
---

# Qiazhi-Bazi Testing

Use this skill whenever you add tests, change test coverage, or need to validate a refactor.

## Test layers

- Backend unit: `backend/tests/unit`
- Backend integration: `backend/tests/integration`
- Frontend unit/integration: colocated under `frontend/src/features/**/__tests__` or feature test files

## Required commands

### Backend

```bash
cd qiazhi_bazi/backend
pytest tests/unit tests/integration -q
```

### Frontend

```bash
cd qiazhi_bazi/frontend
npm run test:ci
```

等价拆分：`npm run typecheck && npm run lint && npm test && npm run build`。仅 Stream Board：`npm run test:stream-board`。

## Coverage expectations

- New service/helper: add unit tests
- New controller hook: add integration-style hook test
- Major UI wiring change: add view interaction test
- Main flow refactor: preserve or add regression coverage

## Docs to update

- `docs/testing/TEST_STRATEGY.md`
- `docs/testing/TEST_CASES.md`
