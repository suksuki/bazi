# V17 Frontend Architecture

V17 now treats language, responsive layout, and authorization as shared runtime dimensions instead of page-local details.

## Runtime Layer

Use `hooks/useV17Runtime.ts` at the top of client feature pages. It combines:

- app language and localized helpers: `language`, `tx`, `ui`, `term`, `termList`
- auth session state: `user`, `authLoading`, `logout`, `refreshAuth`
- access policy: `access`

New feature pages should avoid calling `useAppLanguage()` and `useAuthSession()` separately unless they are implementing a lower-level runtime primitive.

## Access Policy

Use `lib/accessControl.ts` for role, capability, and surface checks.

- `createAccessPolicy(user)` produces the page-facing policy object.
- `access.canAccessOracleSurface("trace")` replaces direct `surface_access` reads.
- `access.canManageUsers` replaces ad hoc `user.surface_access?.user_management` checks.
- `access.canUseProfessionalOracle` gates practitioner-only evidence, decision, and auxiliary analysis surfaces.
- `access.canReadEvidence` / `access.canSubmitPractitionerFeedback` gate evidence review UI and feedback writes.

This keeps role names, capabilities, and surface gating in one place.

Current role intent:

- `user`: concise BaZi reading and basic chart only.
- `practitioner`: professional oracle workspace, evidence chain, practitioner feedback, and real-case capture.
- `manager`: practitioner workspace plus collaboration/user-role maintenance.
- `admin`: full admin console and all operational surfaces.

## Responsive Shell

Use `components/V17_AppShell.tsx` for authenticated app pages. It owns:

- mobile sticky app header
- desktop header layout
- role/user/logout/retry chrome
- auth gate display
- explicit reset affordance: `返回填写八字` returns a running oracle session to the natal-input screen

Feature pages should pass page content as children and keep business UI inside the shell.

## Auth Entry

Use `components/V17_AuthScreen.tsx` for `/login` and `/register`.

- It owns the branded entry layout, language selector, login/register switching, and compact validation.
- It should stay responsive without page-local wrappers: desktop uses a brand panel plus form, while mobile uses a single compact form surface.
- It should not expose browser-native required-field bubbles; validation messages must be localized through `lib/i18n.ts`.

## Page Guard

Use `components/V17_PageGuard.tsx` around authenticated feature pages.

- It redirects anonymous users to login.
- It can redirect authenticated-but-forbidden users to a fallback route.
- It renders the shared auth/permission holding state through `V17_AppShell`.

Pages should declare access intent with `allowed`, `forbiddenRedirectTo`, and optional `forbiddenContent` instead of writing page-local auth redirect effects.

## Surface Navigation

Use `components/V17_SurfaceTabs.tsx` for multi-surface feature areas.

- Mobile: horizontal, tab-like segmented navigation.
- Desktop: stable grid tabs.
- The page supplies only available tabs after access filtering.

This pattern is intended for oracle, admin, and future feature modules with role-dependent sections.

## Feature Registry

Use `lib/featureRegistry.ts` to declare top-level feature modules.

- `ORACLE_FEATURE_MODULES` declares oracle surfaces and their access gates.
- `ADMIN_FEATURE_MODULES` declares admin console sections and their tab metadata.
- `resolveFeatureTabs(...)` turns module declarations plus runtime context into `V17_SurfaceTabs` items.

New modules should be registered here first, then rendered by the target page. This keeps feature names, badges, ordering, access gates, and responsive navigation out of page-local arrays.

## Feature Outlet

Use `components/V17_FeatureOutlet.tsx` to render the currently active feature module.

- Pages provide a typed renderer map keyed by feature id.
- `V17_SurfaceTabs` controls the active id.
- `V17_FeatureOutlet` owns active-module dispatch.

This separates page chrome, module metadata, and module content. A new feature should add metadata in `featureRegistry.ts`, add one renderer entry in the page or feature bundle, and avoid extending long page-level conditional render chains.

## Verdict UX

The oracle verdict action is intentionally product-facing:

- Button label: `掐指一算`.
- Busy label: `正在掐指一算`.
- The UI prompt asks for concise BaZi judgement lines.
- Backend prompt contracts and role token budgets are enforced in `backend/narrative/semantic_fusion.py` and `infrastructure/llm_micro_client.py`.

Do not reintroduce long-form verdict prompts from the frontend. Deep reasoning belongs in `深度解读` and `幕后观察`; the primary verdict card should stay short and decisive.

## API Requests

Use `lib/apiClient.ts` for client-side JSON calls.

- `requestJson(url, init)` normalizes JSON and non-JSON responses.
- `jsonPostInit(body)` keeps POST headers and serialization consistent.

Feature pages should avoid adding local `requestJson` helpers.

Direct `fetch` should be limited to streaming readers and Next.js API proxy routes where the response is not ordinary JSON or must be forwarded as-is.

## Migration Rule

When adding a feature:

1. Read runtime from `useV17Runtime()`.
2. Filter visible sections through `access`.
3. Wrap authenticated pages with `V17_PageGuard`.
4. Render app content inside `V17_AppShell`.
5. Register top-level feature sections in `lib/featureRegistry.ts`.
6. Use `V17_SurfaceTabs` for role-dependent top-level sections.
7. Render the active section through `V17_FeatureOutlet`.
8. Use `requestJson` / `jsonPostInit` for client JSON calls.
9. Keep translations in `lib/i18n.ts`; avoid inline language branching except through `ui()`.
