# V50 Case Workspace Product Alignment Closeout V1

Date: 2026-07-21

## Result

The formal `/experience` page now consumes the shared Case Workspace contract rather than
maintaining an independent product-mode authority.

```text
LifeCase + ChartWorldInstance
        ↓
CanonicalSceneOwner
        ↓
role-filtered CaseWorkspaceEnvelope
        ↓
overview | OneCanvas structure | Abu narration
```

Only surfaces backed by the current Case are shown. The anonymous Xiangfa and S0 Theater
demonstrations remain isolated and are never presented as a user's personal result.

## Consolidation

- Added one read-only Workspace endpoint under the existing Canonical Scene router.
- Removed the page's duplicate chapter-navigation model.
- Reduced visible navigation from five report anchors to three Case-bound views.
- Centralized surface availability in one client calculation.
- Reused the existing baseline, Canvas and narration renderers; no parallel renderer was added.
- Changed four initial Case requests from serial loading to one parallel batch.
- Kept all R1 files, V40, formal case state and production routes unchanged.

## Verification

```yaml
focused_regression: 25_passed
full_regression: 582_passed
typescript_strict: passed
desktop_browser: passed
mobile_390px_browser: passed
horizontal_page_overflow: false
browser_console_errors: 0
r1_manifest: 20_of_20_ok
production_migration: false
```

## Remaining Boundary

The review build is ready. Changing `/`, `/app`, deployment traffic or production data is a
separate migration decision and requires an explicit rollback plan. Professional Mingli
release remains a separate gate.
