# V60 Migration and Provenance Policy

## Decision

V60 is a new authority system. V50 is a read-only source for explicitly
admitted material, never a runtime dependency.

The first migration admits only:

```text
existing account credential verifier
+ selected birth profile input
```

V60 then independently derives:

```text
BirthInput
-> ChartVersion
-> bounded deterministic facts
-> LifeCase baseline
-> Canonical Scene
```

## Why

The existing account should continue to work, but historical conclusions must
not silently become V60 truth. The selected V50 LifeCase is currently
professionally blocked, so importing it would preserve uncertainty as if it
were an accepted conclusion.

V60 therefore:

- copies the existing PBKDF2 verifier without learning the password;
- imports the selected birth input and its source identity;
- recomputes the four pillars with the V60 calendar engine;
- rejects the migration if recomputed and stored pillars differ;
- records source row hashes and one migration batch manifest;
- does not copy V50 assertions, strength values, retired experience state or professional
  conclusions.

## Authority classes

| Material | V60 treatment |
| --- | --- |
| Account verifier | Compatibility import |
| Birth input | Imported source material |
| Four pillars | V60 deterministic derivation |
| Stem/branch/hidden-stem tables | Versioned bounded fact profile |
| Strength, useful-god or effective-work claims | Unresolved until separately admitted |
| V50 LifeCase conclusions | Rejected for this migration |
| V50 retired experience visits and fixtures | Rejected |
| Approved visual assets | Copied and hash-locked |

## Runtime boundary

Production V60 code cannot import `v50` Python modules or read V50 tables.
Only the explicit local migration command may read the V50 database. The
resulting V60 records carry:

```text
source_system
source_ref
source_hash
derivation_version
authority
```

Every visible V60 statement must be traceable to those records or to a later
versioned decision.
