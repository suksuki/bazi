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

This keeps role names, capabilities, and surface gating in one place.

## Responsive Shell

Use `components/V17_AppShell.tsx` for authenticated app pages. It owns:

- mobile sticky app header
- desktop header layout
- role/user/logout/retry chrome
- auth gate display

Feature pages should pass page content as children and keep business UI inside the shell.

## Surface Navigation

Use `components/V17_SurfaceTabs.tsx` for multi-surface feature areas.

- Mobile: horizontal swipe tabs.
- Desktop: stable grid tabs.
- The page supplies only available tabs after access filtering.

This pattern is intended for oracle, admin, and future feature modules with role-dependent sections.

## Migration Rule

When adding a feature:

1. Read runtime from `useV17Runtime()`.
2. Filter visible sections through `access`.
3. Render inside `V17_AppShell`.
4. Use `V17_SurfaceTabs` for role-dependent top-level sections.
5. Keep translations in `lib/i18n.ts`; avoid inline language branching except through `ui()`.
