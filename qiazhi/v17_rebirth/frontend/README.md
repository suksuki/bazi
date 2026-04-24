# V17 Rebirth Frontend

Next.js 16 app for the V17 BaZi oracle and admin surfaces.

## Current UX Scope

- Auth entry: `/login` and `/register` use a responsive branded entry screen with language switching, compact form validation, and database-backed auth.
- Oracle workspace: `/v17/oracle` uses role-aware surfaces: `命盘总览`, `深度解读`, and `幕后观察`.
- Mobile navigation: top-level oracle surfaces render as swipe-friendly tabs on phone-sized Chrome and stable tabs on desktop.
- Primary action: the verdict button is `掐指一算`; while the LLM is producing the verdict it switches to `正在掐指一算` with a small loading animation.
- Reset action: authenticated app chrome exposes `返回填写八字`, which returns to the birth-info input state.
- Verdict style: UI prompts request concise BaZi judgement lines and the backend enforces short role-specific token budgets.

## Development

```bash
pnpm install
pnpm dev
```

Open `http://localhost:3000/login`.

## Test And Build

```bash
pnpm lint
pnpm test
pnpm build
pnpm run test:ci
```

`pnpm run test:ci` is the frontend hard gate: ESLint, production build, then Vitest.

## Architecture Pointers

- Runtime and access policy: [ARCHITECTURE.md](ARCHITECTURE.md)
- Translations and UI copy: [lib/i18n.ts](lib/i18n.ts)
- Auth entry: [components/V17_AuthScreen.tsx](components/V17_AuthScreen.tsx)
- App chrome: [components/V17_AppShell.tsx](components/V17_AppShell.tsx)
- Surface tabs: [components/V17_SurfaceTabs.tsx](components/V17_SurfaceTabs.tsx)
- Oracle page composition: [app/v17/oracle/page.tsx](app/v17/oracle/page.tsx)

## Deployment Note

The 0.13 Linux server runs the production build through systemd. After pulling a pushed branch there, use:

```bash
cd /home/hlsystem/bazi/qiazhi
source ~/.nvm/nvm.sh
nvm use 22
./v17_rebirth/scripts/update_v17_from_git.sh
```
