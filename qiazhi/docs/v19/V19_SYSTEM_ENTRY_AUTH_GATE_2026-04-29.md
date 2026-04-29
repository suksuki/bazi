# V19 System Entry and Minimal Auth Gate

Date: 2026-04-29
System: V19 Guided Bazi Agent + Analyst Lab + Chinese Governance Console

## Purpose

V19 now uses a system entry page instead of relying on role query parameters as the product entry.

```text
/ or /entry
-> System Entry
-> guest / user / practitioner / admin entry
```

## Surfaces

```text
Guest trial -> /oracle
User login/register -> /oracle
Practitioner login -> /lab
Admin login -> /admin
```

## Minimal Auth Model

This is a local minimal auth gate, not a full account system.

```ts
type AuthSession = {
  token: string
  role: 'guest' | 'user' | 'practitioner' | 'admin'
  user_id: string
  username: string
}
```

The backend writes an HttpOnly cookie:

```text
v19_auth_session
```

API role checks now resolve role in this order:

```text
1. auth session cookie
2. development fallback role query/header/referer
3. guest
```

Development fallback can be disabled with:

```text
V19_ALLOW_ROLE_QUERY_FALLBACK=0
```

## Admin Credential

Admin is the only fixed administrator in this local MVP.

Default local development credential:

```text
username: admin
password: abcd1235
```

This is local development only and must be changed before deployment.

Override in backend environment:

```text
V19_ADMIN_USERNAME=admin
V19_ADMIN_PASSWORD=<new-password>
```

The admin password is not present in frontend code.

## Boundaries

```text
role does not affect inference
role does not affect signal output
admin only enters Chinese governance console
user/guest cannot enter /lab or /admin
practitioner cannot enter /admin
```

## API Access

```text
/api/agent/* -> all roles
/api/agent/structure -> all roles
/api/agent/feedback -> all roles
/api/labels -> all roles
/api/lab/* -> practitioner + admin
/api/admin/* -> admin only
```

## Non-goals

```text
no OAuth
no password reset
no organization/team model
no complex RBAC engine
no role-based inference variation
```
