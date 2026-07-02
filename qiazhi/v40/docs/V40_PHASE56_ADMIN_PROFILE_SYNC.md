# V40 Phase 56: Built-In Admin And V30 Profile Sync

Date: 2026-07-02

## Goal

V40 keeps the same practical admin account convention as V30:

```text
username: admin
email: jerrydidi@gmail.com
password: abcd1235
main-system role: practitioner
```

There is still only one built-in admin identity. The user-facing V40 app does not expose Admin control-plane power; when this account enters `/v40/ui`, it behaves as a special practitioner account for management testing, practitioner lens checks, profile review, and product acceptance.

## Runtime Boundary

The main V40 user app supports:

```text
guest
user
practitioner
```

Admin is not a normal user-app registration role. The built-in `admin` login is projected as `practitioner` in the user app.

Registration cannot create or overwrite the built-in admin identity. The account is seeded by controlled bootstrap/sync code, not by `/api/v40/auth/register`.

## V30 Profile Source

The sync source is the V30 product UI store, preferring the 13-server snapshot:

```text
qiazhi/v30/.runtime/remote_product_sync/product_ui_store.13.json
```

Fallback:

```text
qiazhi/v30/.runtime/product_ui_store.json
```

Admin profile ownership is detected by:

```text
actor_id in {"v20-admin", "admin"}
or owner_username == "admin"
```

The current imported set contains 18 个 V30 admin 八字档案.

## Conversion Contract

Each imported profile becomes a V40 `BaziProfileRecord`:

```text
profile_id: v30-admin:<source_profile_id>
user_id: user:admin
display_name: V30 display_name
birth_input: V30 birth_input converted to BirthInputCanonical
chart_facts: deterministic V30 birth-input chart result converted to BaziChartFacts
ziwei_chart_facts: sidecar placeholder for later Ziwei calibration
tags: ["v30_admin_import", <source status>]
```

The sync uses V30's deterministic birth-input chart builder during migration only. V40 runtime does not import V30, read V30 runtime files, or mutate V30 state.

## CLI

```bash
PYTHONPATH=qiazhi/v40 qiazhi/.venv312/bin/python qiazhi/v40/scripts/sync_v30_admin_profiles.py
```

The script writes to the independent V40 repository:

```text
v40_user_accounts
v40_bazi_profiles
```

It is idempotent: the admin account has a stable `user:admin` id, and migrated profiles have stable `v30-admin:<source_profile_id>` ids.

## Acceptance

- Login by `admin / abcd1235` succeeds.
- Login response exposes `role_key=practitioner`.
- Built-in admin email is `jerrydidi@gmail.com`.
- `/api/v40/auth/register` cannot create the built-in admin identity.
- `/api/v40/profiles` after admin login returns the imported V30 admin profiles.
- Imported chart facts are deterministic migration facts, not LLM-generated facts.

## Boundary

This phase does not reintroduce Admin controls into the user app. It only gives the project owner a stable practitioner-grade testing account and migrates the existing V30 admin profile material into the isolated V40 database.
