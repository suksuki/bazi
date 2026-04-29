# V19 Role and Language Scope Lock

Date: 2026-04-29
System: V19 Standalone Agent Lab

## Product Surface Split

```text
/oracle and /v19 and /
-> Guided Bazi Agent user surface

/lab
-> Reasoning Instrument for practitioner/admin review

/admin
-> Chinese-only governance console
```

## Language Strategy

User surface `/oracle`:

```text
zh / en / ko required
all user-visible labels must come from label contract
internal signal keys remain English
locale change must not change inference or session
```

Lab surface `/lab`:

```text
analyst/practitioner instrument
can keep English signal keys
may add zh/en later
```

Admin surface `/admin`:

```text
Chinese only
no locale switch
no label contract dependency
must preserve raw signal key and rule_id English identifiers
```

## Role Model

```ts
type User = {
  id: string
  role: 'admin' | 'practitioner' | 'user' | 'guest'
}
```

Allowed roles are locked to:

```text
admin
practitioner
user
guest
```

No additional role split in current phase.

## Minimal Role Enforcement

```text
/api/agent/* -> all roles
/api/agent/feedback -> all roles
/api/labels -> all roles
/api/lab/* -> practitioner + admin
/api/admin/* -> admin only
/lab -> practitioner + admin
/admin -> admin only
/oracle, /v19, / -> all roles
```

Role may be supplied by:

```text
?role=guest|user|practitioner|admin
X-V19-Role header
referer query role for page-owned API requests
```

This is an identity boundary only, not a login system and not RBAC.

## Hard Guardrails

```text
role must not affect inference
role must not affect signal output
practitioner cannot directly mutate active rules
admin does not participate in user prediction flow
user cannot see rule_id / attribution / validation internals
```

## Current User Experience

`/oracle` is now a guided agent flow:

```text
Welcome
-> Birth Input
-> Question Builder
-> Run structure analysis
-> Result Card
-> Time Context collapsed
-> Evidence collapsed
-> Next-question suggestions
```

It is no longer a control panel or developer dashboard.
