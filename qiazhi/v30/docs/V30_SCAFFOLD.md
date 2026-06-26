# V30 Scaffold

This directory is the independent V30 starting point.

Current scaffold guarantees:

- Python package is `v30`.
- API routes are under `/api/v30`.
- UI assets are mounted under `/v30/ui`.
- Runtime files default to `./.runtime`.
- Storage names are guarded by `v30_*` tables and `v30:` Redis keys.
- Tests reject runtime imports from `v20.*`.

The smoke runtime is intentionally contract-first and placeholder-only. V20 assets should be converted into V30 schemas before use.
