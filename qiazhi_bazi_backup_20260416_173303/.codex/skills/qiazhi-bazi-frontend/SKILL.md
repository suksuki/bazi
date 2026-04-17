---
name: qiazhi-bazi-frontend
description: Use when working on the Next.js frontend in this repo, especially feature extraction, controller/view splits, Tailwind component refactors, or admin and StreamBoard flows.
---

# Qiazhi-Bazi Frontend

Use this skill for frontend implementation and refactors.

## Preferred placement

- Route entry: `frontend/src/app/**`
- Feature logic: `frontend/src/features/<feature>/`
- Shared UI: `frontend/src/components/`
- Static mappings: `frontend/src/constants/`

## Preferred extraction order

1. Extract `types.ts` and `constants.ts`
2. Extract pure `utils.ts`
3. Extract controller hook if state/effects are heavy
4. Leave route file thin

## Current reference features

- `frontend/src/features/stream-board/`
- `frontend/src/features/admin-settings/`
- `frontend/src/features/decision-inbox/`
- `frontend/src/features/bazi-card/`
- `frontend/src/features/ten-god-list/`
- `frontend/src/features/auditor-briefing/`

## Validation

Run:

```bash
cd qiazhi_bazi/frontend
npm test
npm run build
```
