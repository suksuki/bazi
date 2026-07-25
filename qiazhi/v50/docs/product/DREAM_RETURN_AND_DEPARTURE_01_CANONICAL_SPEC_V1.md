# DREAM-RETURN-AND-DEPARTURE-01 Canonical Spec v1

```yaml
DREAM-RETURN-AND-DEPARTURE-01:
  design: FROZEN
  implementation: NOT_AUTHORIZED
  chrome_implementation_audit: REQUIRED_WHEN_IMPLEMENTED
  owner_decisions:
    abu_identity: CANONICAL_UNIQUE_BEING
    active_control: SINGLE_LEASE_WITH_FENCING
    guest_anchor_migration: EXPLICIT_CONSENT
  unresolved_product_semantics: NONE
```

## Scope

This specification extends the frozen first-visit contract in
`DREAM_ENCOUNTER_01_FIRST_VISIT_CANONICAL_SPEC_V1.md`. It governs:

1. returning to the Dream after the first visit;
2. rebuilding a world that continued while the viewer was absent;
3. leaving the Dream deliberately from the living grove;
4. recovering from suspension, crashes, disconnects, and invalid anchors;
5. canonical Abu identity, viewer privacy, and multi-device control.

It does not add NPC Mind Wake, Liuyao runtime, rewards, relationship progression,
candidate-path promotion, or new Mingli semantics.

## Product Invariant

```text
Return to the last deliberate departure place
-> restore position and camera
-> load the current continuously advancing world
-> clear a short local mist
-> continue living
```

The viewer returns to a place, not to an old frame. World time, resident state,
tree state, authorization, and Abu state are always current.

Only the first visit traverses the complete fog gate. A normal return never replays
tree recognition, the first reveal, an open root mirror, or OneCanvas.

## Three Anchor Types

### TreeObservationAnchor

```yaml
lifecycle: VISIT_EPHEMERAL
purpose: return from the root mirror to the same tree observation point
fields:
  - visit_id
  - resident_scene_ref
  - viewer_position
  - camera_heading
  - root_mirror_space_ref
forbidden:
  - cross_visit_restore
  - canonical_history
  - relationship_history
  - mingli_evidence
  - training_evidence
```

This anchor is destroyed when its visit ends. It restores navigation only and never
freezes the world clock or resident state.

### DreamDepartureAnchor

```yaml
lifecycle: CROSS_VISIT_NAVIGATION
commit_condition: successful_formal_departure
fields:
  - anchor_id
  - viewer_id
  - case_namespace
  - world_space_ref
  - last_stable_forest_position
  - camera_heading
  - geometry_version
  - source_visit_id
  - visit_sequence
  - commit_sequence
  - anchor_version
  - departure_world_time
  - committed_at
  - departure_commit_id
forbidden:
  - world_snapshot
  - resident_snapshot
  - tree_snapshot
  - old_abu_frame
  - relationship_progress
  - reward_progress
  - mingli_fact
```

`departure_world_time` is audit metadata only. It cannot reconstruct an old
environment, replay missed events, or infer changes.

### DreamRecoveryCheckpoint

```yaml
lifecycle: ABNORMAL_RECOVERY_ONLY
ttl: 24_REAL_HOURS
fields:
  - recovery_checkpoint_id
  - viewer_id
  - case_namespace
  - visit_id
  - latest_safe_forest_position
  - camera_heading
  - geometry_version
  - lease_epoch
  - recovery_sequence
  - updated_at
  - expires_at
forbidden:
  - claiming_formal_departure
  - reopening_root_mirror
  - restoring_onecanvas
  - replaying_reveal
  - overriding_newer_departure
```

The checkpoint is written only after the viewer reaches a stable forest position.
It is protected by the current control-lease epoch and a monotonic recovery sequence.
An expired checkpoint is ignored.

### Resolution Precedence

The server resolves navigation from the latest visit outcome:

```text
latest visit formally departed
-> its DreamDepartureAnchor

latest visit ended abnormally and has a valid newer RecoveryCheckpoint
-> that RecoveryCheckpoint

no valid recovery
-> latest compatible DreamDepartureAnchor

anchor invalid or unavailable
-> nearest authorized safe point
-> the viewer's own-tree safe point
-> formal grove entrance safe point
```

The client cannot choose coordinates, migrate geometry, or rank fallbacks.

## Complete Return Experience

### Return Flow

```text
RETURN_PREPARE
-> AUTH_REVALIDATING
-> WORLD_REHYDRATING
-> optional ANCHOR_INVALID_FALLBACK
-> LOCAL_MIST_REENTRY
-> FOREST_ACTIVE
```

### Return Storyboard

| Time | World presentation | Authority behavior |
| --- | --- | --- |
| `0.0-0.2s` | The waking shell gives way to local mist. No old grove is shown. | Begin server-side viewer, Case, lease, and authorization checks. |
| `0.2-0.6s` | Mist holds a spatial silhouette without names or Mingli content. | Resolve the current world projection and a safe anchor. |
| `0.6-1.2s` | Mist clears only around the resolved position. Directional forest sound returns. | Bind the current world and authorization versions. |
| `after 1.2s` | The current living grove becomes controllable. | Grant forest movement to the active control lease. |

The mist is a spatial reorientation, not a loading screen. It contains no welcome
copy, progress indicator, reward, return summary, or missed-events montage.

If the server is not ready within the normal transition window, mist may remain
ambient briefly. A real timeout exits to a neutral waking-shell error state; it never
reveals stale world content.

### Return Behavior

- The user's tree remains recognized and never repeats first-recognition animation.
- A previously revealed fact is not replayed automatically.
- The root mirror starts closed.
- OneCanvas starts absent and contains no restored frame, text, or accessible label.
- Every resident identity, tree disclosure, reveal, and mirror opening is reauthorized.
- The world is reconstructed from current server time and current projection versions.
- No return action modifies LifeCase, relation history, rewards, or training evidence.

## Canonical Abu

Abu is a `CANONICAL_UNIQUE_BEING`:

```text
one canonical identity
+ one canonical position
+ one action timeline
+ one public world behavior
```

Abu is never copied, teleported, or silently replaced to provide universal companion
availability.

### Return Rules

- If Abu is canonically nearby, he may turn an ear, lift his gaze, or briefly notice.
- If Abu is elsewhere, he remains elsewhere.
- Abu does not run over, nod, wave, or say that the viewer has returned.
- Abu follows only after the viewer starts moving and the existing delayed-follow rule
  authorizes it.
- Absence never creates loneliness, blame, decay, intimacy loss, or attendance debt.

### Public and Private Projection Boundary

Shared space may expose only:

- Abu's public position;
- public movement;
- natural actions unrelated to private facts;
- explicitly approved public events.

Shared space must never expose:

- birth data or LifeCase facts;
- resident-tree authorization state;
- private voice, subtitles, or accessibility text;
- public facial or body reactions triggered by private Mingli content;
- one viewer's private conversation to another viewer.

Viewer-private interactions are authorization-scoped projections. They do not rewrite
Abu's public chronicle. When public canonical behavior conflicts with a private
projection, public behavior wins and the private projection degrades or waits. Abu is
not copied to satisfy both.

If a future product requires always-available private companionship, it must introduce
an explicitly named Guide Projection. It cannot pretend to be canonical Abu.

## Active Dream Control Lease

For one `viewer + case_namespace`, only one device may hold the active Dream control
lease.

The lease includes a server-issued epoch and monotonic fencing token. Client clocks do
not establish validity.

```text
second device requests entry
-> choose explicit takeover or exit
-> server issues a higher lease epoch/fencing token
-> old device immediately loses command authority
-> old device enters VISIT_SUSPENDED
-> sensitive content is veiled and cleared
```

Movement, tree touch, mirror withdrawal, RecoveryCheckpoint writes, and
DreamDepartureAnchor writes all validate the current lease epoch and fencing token.
Delayed requests, offline replay, and old pages cannot overwrite the new device.

## Guest Anchor Migration

`Guest -> Member` does not migrate navigation state by default.

Migration requires explicit user consent and server verification of:

- the Guest capability;
- the current device context;
- the target Member account;
- the source anchor's unused migration status.

Only navigation state is migrated. Mingli facts, grants, relationship state, access
history, and evidence are excluded. After success, the Guest anchor is invalidated and
cannot bind to another account. Refusal or inaction uses the Member's own anchor or a
safe entrance. Shared devices never imply identity equivalence.

## Long-Term World Change

### A. Continuous Environment Layer

The canonical world clock and versioned environment policy may change:

- dawn and dusk;
- light direction;
- mist density;
- dew;
- leaves and wind;
- non-Mingli seasonal environment.

These changes establish continuity only. Weather, light, falling leaves, and tree
appearance cannot encode luck, danger, health, relationship decline, or other Mingli
claims.

### B. Spatial Continuity Layer

This layer includes:

- cross-visit navigation anchors;
- Abu's canonical position;
- accessible regions;
- geometry version;
- resident-tree spatial references.

It is reconstructed deterministically from the current clock and formal event
projection. Offline time does not require frame-by-frame simulation.

### C. Formal Life-State Layer

Only these sources may produce explainable persistent tree change:

- confirmed LifeCase facts;
- verified user feedback;
- authorized, version-bound Mingli projections;
- committed relationship state;
- explicitly approved Dream product events.

Visits, clicks, dwell time, consecutive login, temporary LLM copy, and unverified
paths cannot change a tree.

### D. Research and Candidate Layer

The persistent world excludes:

- competing explanations;
- candidate paths;
- potential relationships;
- uncommitted PathAssertions;
- Lab content;
- LLM guesses;
- unverified reality feedback.

These remain in Lab or the formal research surface.

### Time-Scale Matrix

| Scale | Allowed | Forbidden |
| --- | --- | --- |
| Minutes | Wind phase, leaf motion, dew, canonically scheduled movement | Mingli progression, rewards, relationship upgrades |
| Hours | Light angle, mist, ambient sound, current public positions | Weather-as-luck or environment-as-prediction |
| Days | Day/night phase, non-semantic seasonal state, already committed formal events | Absence penalties, streaks, attendance growth |
| Weeks | Slow seasonal continuity and authorized committed life-state projections | Fabricated events added to keep the world busy |
| Months | Current season, current authorized LifeCase versions, coherent result of multiple formal changes | Replay montages, automatic fruit, levels, coins, tasks, or guilt |

No formal change means the world may genuinely show no formal change. When several
changes occur while the viewer is absent, return presents one coherent current state,
not a sequence of theatrical reenactments. Verification still requires tree touch,
the root mirror, and formal OneCanvas.

## Two Legal Departure Triggers

Both triggers use one Departure Controller and one atomic server command.

### SPATIAL_BOUNDARY

This is the default embodied departure:

```text
FOREST_ACTIVE
-> walk into a visible outer mist path
-> DEPARTURE_INTENT
-> turn back to cancel, or cross the formal boundary
-> DEPARTURE_COMMITTING
-> DEPARTED
```

The outer mist path is real walkable ground, tree gaps, distant terrain, and mist. It
is not a button, card, door icon, label, or transparent hotspot. Desktop and mobile
must allow ordinary movement into a broad path.

Before the boundary, the viewer may turn back. Cancellation writes no departure
anchor. After crossing, command ownership transfers to the Departure Controller.

### SEMANTIC_EXIT

This trigger exists only for:

- browser Back;
- mobile system Back;
- the screen-reader `Leave Dream` action;
- keyboard-equivalent accessible exit.

It is legal only from `FOREST_ACTIVE`. It does not claim that the viewer walked to the
outer path. It closes a restrained local mist around the current stable forest
position, then invokes the same atomic departure command.

If the mirror is active, the first Back action only withdraws the mirror. It does not
leave the Dream. Browser closure, crashes, process killing, and device shutdown are
Recovery events, not semantic exits.

## Formal Departure Storyboard

| Stage | Presentation | Commit behavior |
| --- | --- | --- |
| Stable grove | Outer mist path remains visible as part of the world. | No departure state. |
| Enter path | Mist deepens and distant sound softens. | Create local `DEPARTURE_INTENT`; no anchor write. |
| Before boundary | Viewer can turn back naturally. | Cancel without persistence. |
| Cross boundary | Mist obscures the grove without reverse-playing first entry. | Lock controls and begin atomic commit. |
| Commit succeeds | Forest sound fades; Abu remains on the grove side without farewell. | Close Visit and return the unique commit result. |
| Waking shell | No summary, reward, completion mark, or story settlement. | Route to `/experience`. |

For `SEMANTIC_EXIT`, the same stages occur from the current stable position with local
mist closure instead of a fabricated walk to the outer path.

The saved position is the last stable forest position before entering departure mist.
No coordinate outside the grove can become an anchor.

## Atomic Departure Command

`CommitDreamDeparture` is one idempotent server command. It atomically:

1. validates the active control lease epoch and fencing token;
2. validates `visit_id`, `viewer_id`, `case_namespace`, and `commit_sequence`;
3. writes or confirms the `DreamDepartureAnchor`;
4. closes the corresponding `DreamVisit`;
5. creates one immutable `departure_commit_id`;
6. emits the projection/router Outbox event.

The idempotency boundary is:

```text
viewer_id + case_namespace + visit_id + commit_sequence
```

The product contract forbids:

- an updated anchor with a long-lived active Visit;
- a closed Visit without a determined anchor result;
- duplicate departures caused by network retry;
- reopening a closed Visit when waking-shell routing fails.

Transaction or transactional Outbox implementation is permitted, but the externally
visible result is atomic. After a disconnect, the client queries by idempotency key or
`departure_commit_id`. It never invents success or recomputes coordinates.

## Unified State Machine

| State | Input and controller | Persistable output | Forbidden output | Exit |
| --- | --- | --- | --- | --- |
| `RETURN_PREPARE` | Entry/cancel; Navigation Controller | Visit attempt audit | Old world content | Start authorization or cancel |
| `AUTH_REVALIDATING` | Server Auth only | Authorization audit | Client-derived permission | Pass or `FAIL_CLOSED` |
| `WORLD_REHYDRATING` | Projection Loader only | None | Cached fact restoration | Resolve current world |
| `ANCHOR_INVALID_FALLBACK` | Server Anchor Resolver | Fallback audit | Client coordinate repair | Safe anchor or failure |
| `LOCAL_MIST_REENTRY` | Reentry Timeline; no movement | None | Mingli disclosure | Mist clear |
| `FOREST_ACTIVE` | Forest Movement | Throttled RecoveryCheckpoint under current lease | Canonical or reward state | Mirror, suspension, or departure |
| `MIRROR_ACTIVE` | OneCanvas Controller | Existing authorized audit only | DepartureAnchor | Withdraw mirror |
| `MIRROR_WITHDRAWING` | Mirror Exit Controller | None | Forest action from same gesture | `FOREST_ACTIVE` |
| `DEPARTURE_INTENT` | Departure Controller; move/cancel | None | Early anchor write | Cancel or cross boundary |
| `DEPARTURE_COMMITTING` | Server command; all input locked | Atomic anchor, Visit close, commit ID | Client inference | `DEPARTED` or verified recovery |
| `DEPARTED` | Shell Router only | Route retry audit | Dream reopening | Waking shell |
| `VISIT_SUSPENDED` | No world input | Safe RecoveryCheckpoint if lease valid | Sensitive visible content | Recovery or lease loss |
| `RECOVERY_REHYDRATING` | Recovery Loader | None | Mirror/reveal restoration | Current closed-mirror grove |
| `FAIL_CLOSED` | Retry or waking-shell return | Security audit | Sensitive content | Authorized retry or exit |

### Authorization Revocation Order

```text
freeze input
-> veil sensitive pixels
-> remove Canvas, DOM text, audio, subtitles, ARIA text, and memory references
-> invalidate opaque refs server-side
-> resolve remaining grove authorization
-> show an anonymous tree or return to the waking shell
```

Revocation never substitutes a nearby fact.

### First-Visit Integration

The first-visit state `FOREST_RETURNED` maps to `FOREST_ACTIVE`. Completing the first
seven-shot encounter does not create a DepartureAnchor. Only a formal departure does.

## History, Suspension, and Page Lifecycle

- Root-mirror opening adds visit-local History state.
- Back in `MIRROR_ACTIVE` consumes that state and performs mirror withdrawal.
- Back in `FOREST_ACTIVE` invokes `SEMANTIC_EXIT`; native navigation waits for commit.
- Successful departure uses `replaceState` for the waking shell. Browser Forward cannot
  restore a closed sensitive Dream view.
- Page hiding may pause particles, camera frames, and tree animation. World time and
  formal events continue server-side.
- Suspending an open mirror veils and clears it. Recovery returns to a closed-mirror
  forest and reauthorizes all content.
- A route failure after departure keeps sensitive content cleared and retries the
  waking-shell route. It cannot reopen the Visit.

## WorldProjection and Anchor Boundary

Every opaque `WorldProjection` reference binds:

- viewer;
- case namespace;
- authorization version;
- world version;
- projection version;
- expiry.

Expired or revoked references fail closed. Local cache is never a fact source.
Geometry migration, nearest-safe-point resolution, and return coordinates are
server-owned.

All anchors are excluded from:

- Mingli chronicle;
- relationship chronicle;
- formal evidence;
- model-training evidence;
- rewards and progression.

## Event and Permission Table

| Event | Owner | Required authority | Durable result | Canonical effect |
| --- | --- | --- | --- | --- |
| `dream_return_requested` | Navigation | Current viewer | Visit audit | None |
| `dream_authorization_validated` | Authorization Service | Dream and Case grants | Security audit | None |
| `dream_world_projection_issued` | Projection Owner | Current grant versions | Expiring opaque ref | Read-only |
| `dream_control_lease_acquired` | Control Lease Owner | Viewer and Case | Lease epoch/fencing token | None |
| `dream_anchor_resolved` | Anchor Owner | Same viewer and namespace | Navigation audit | None |
| `dream_reentry_completed` | Visit Service | Valid Visit and lease | Visit state | None |
| `dream_recovery_checkpointed` | Recovery Owner | Current lease epoch | Expiring checkpoint | None |
| `dream_departure_intent_started` | Client state machine | `FOREST_ACTIVE` | None | None |
| `dream_departure_cancelled` | Client state machine | Same Visit | None | None |
| `dream_departure_commit_requested` | World Command Service | Lease, Visit, Case, sequence | Idempotent command | None |
| `dream_departure_committed` | World Command Service | Successful atomic command | Anchor, Visit close, commit ID | None |
| `dream_authorization_revoked` | Authorization Service | Policy event | Security audit | Does not alter Mingli facts |
| `dream_guest_anchor_migrated` | Anchor Owner | Explicit consent and Guest capability | Navigation-only migration | None |

## Forty Required Scenarios

Unless a row says otherwise, authorization is revalidated before disclosure, the
server world clock continues without rewind, and navigation writes have no Mingli or
relationship effect.

| # | Scenario | Viewer experience and transition | Anchor, persistence, and fallback |
| --- | --- | --- | --- |
| 1 | First formal return after first visit | Local mist clears at the deliberate departure place; no recognition replay. | DepartureAnchor; current authorization required. |
| 2 | Return after minutes | Current ambient phase may differ slightly; no summary. | DepartureAnchor; no new formal state. |
| 3 | Return after days, weeks, or a season | Current environment and authorized formal state appear directly. | DepartureAnchor or server fallback; no montage. |
| 4 | Complete formal departure | Walk through the outer path or use legal semantic exit; mist closes. | Atomic DepartureAnchor plus Visit close. |
| 5 | Enter path then turn back | Mist thins again and forest control resumes. | No anchor update and no Visit close. |
| 6 | Forest page suspended then restored | Current grove rehydrates behind local mist. | Valid RecoveryCheckpoint; current lease required. |
| 7 | Page suspended with OneCanvas open | Sensitive mirror is veiled; return is to forest with mirror closed. | RecoveryCheckpoint only; TreeObservationAnchor discarded. |
| 8 | Browser or app directly closed | No farewell and no formal departure claim. | RecoveryCheckpoint if valid; otherwise previous DepartureAnchor or safe point. |
| 9 | Browser crash or device restart | Current world rehydrates without replay. | Valid non-expired RecoveryCheckpoint; otherwise fallback chain. |
| 10 | Disconnect then reconnect | Formal interaction pauses; neutral ambient rendering may remain. | Reauthorize and rehydrate; offline facts are rejected. |
| 11 | Server unavailable during return | Mist conceals all sensitive content, then waking-shell failure state appears. | No stale projection or new anchor. |
| 12 | DepartureAnchor missing | Local reentry occurs at a valid recovery or safe point. | RecoveryCheckpoint, own-tree safe point, then formal entrance. |
| 13 | Anchor coordinates invalid | No client-side coordinate guess is shown. | Server geometry map, then nearest safe point. |
| 14 | World geometry version changed | Current geometry appears after migration resolution. | Server migration only; failed mapping uses safe fallback. |
| 15 | Resident tree moved, removed, or unauthorized | Tree is current, absent, or anonymous; no stale identity remains. | Anchor may resolve spatially, but disclosure is reauthorized. |
| 16 | Current LifeCase differs from anchor namespace | Old location is not reused. | Matching Case anchor or current Case safe point. |
| 17 | Viewer switches profile or LifeCase | New namespace enters independently; old active control ends safely. | No cross-Case copy of anchors or grants. |
| 18 | Guest becomes Member | User is asked whether to migrate navigation state. | Explicit consent only; Guest anchor is consumed on success. |
| 19 | Logout then login | Local sensitive state is cleared before server restore. | Same account may restore; different account cannot. |
| 20 | Cross-device return | Current server anchor and world are used. | Authorization plus active control lease required. |
| 21 | Two devices open the same Dream | Second device chooses takeover or exit. | Higher fencing token suspends and clears the old device. |
| 22 | Old background page writes after a newer departure | Old result is rejected without visual rollback. | CAS on lease epoch and commit sequence. |
| 23 | Client clock is wrong | World remains correct and visually current. | Server clock and clock-policy version only. |
| 24 | No formal change while absent | The grove may look materially unchanged. | No fabricated event or persistence. |
| 25 | Environment-only change | Current light, wind, mist, and season appear. | Environment projection only; no Mingli meaning. |
| 26 | One formal LifeCase change | Current authorized tree state may reflect it without automatic explanation. | Existing formal source; return itself writes nothing. |
| 27 | Several formal changes | One coherent current state appears; no reenactment. | Current versioned projection only. |
| 28 | Authorization revoked while absent | Sensitive identity and facts never appear on return. | Ref invalidation; anonymous tree or waking-shell fallback. |
| 29 | Fact version expired while absent | Old tree trace, copy, and mirror focus are absent. | Current projection or quiet no-fact state; no substitution. |
| 30 | Abu is nearby on return | Abu may briefly notice, then continues canonical behavior. | Public state only; no private chronicle change. |
| 31 | Abu is not nearby | Abu remains absent or distant. | No teleport or private replacement. |
| 32 | Reduced Motion | Mist brightness and spatial layering replace large camera movement. | Same state and authority transitions. |
| 33 | Screen reader | `Leave Dream` invokes `SEMANTIC_EXIT` with equivalent announcements. | Same atomic departure; no hidden touch target. |
| 34 | Keyboard operation | Movement uses directional keys; accessible exit invokes semantic departure. | Same controllers and persistence. |
| 35 | Mobile system Back | Mirror withdraws first; forest Back invokes semantic departure. | Commit must succeed before native navigation. |
| 36 | Browser Back | Same behavior as system Back. | History cannot bypass departure or restore a closed Visit. |
| 37 | Low-performance device | Invisible animation and particles pause; current deterministic frame is rebuilt. | World time continues server-side. |
| 38 | Sensitive content remains in client cache after revocation | Pixels, Canvas, DOM, audio, subtitles, and ARIA content are immediately cleared. | Cache is never restored as authority. |
| 39 | Network fails during departure commit | Mist remains closed while final command status is queried. | Same idempotency key; committed exits, uncommitted returns to safe forest. |
| 40 | Waking-shell route fails after commit | A neutral cleared state retries routing. | Departure stays committed; closed Visit never reopens. |

## Visual, Audio, Responsive, and Accessibility Rules

### Local Return Mist

- Duration: `0.6-1.2s` under normal readiness.
- Scope: only the resolved return area, not the complete first-visit fog gate.
- Order: conceal sensitive world, establish depth and ambient sound, reveal current
  public geometry, then reveal authorized private projection, then grant control.
- Reduced Motion: retain opacity, light, and depth cues while removing large travel.

### Outer Mist Path

- It must be visible terrain at the grove boundary, not a UI control.
- It remains wide enough for natural movement on desktop, 390px mobile, and landscape.
- Mobile minimum walkable width is `96 CSS px`, excluding safe areas and browser chrome.
- It cannot overlap tree-touch geometry, root-mirror geometry, or OneCanvas gestures.

### Departure Presentation

- Mist gradually occludes the grove; first entry is not reverse-played.
- Forest sound is gradually low-passed and faded without reward or farewell cues.
- Abu remains on the grove side and performs no goodbye animation.
- `SEMANTIC_EXIT` uses local mist closure from the current position and never fabricates
  a walk to the boundary.

### Input and Accessibility

- Pointer ownership remains exclusive to the active state controller.
- Screen readers receive semantic `Return to grove` and `Leave Dream` actions.
- Semantic actions run the same transitions and server commands; they are not invisible
  scene hotspots.
- Browser Back and system Back follow mirror-first, departure-second ordering.
- Keyboard movement and exit provide equivalent access without adding visible cards.
- Background rendering may pause, but server world time and formal state do not.

## Security and Failure Invariants

```text
authorization precedes all Mingli restoration
root mirror is closed on every return and recovery
old OneCanvas pixels and text never resume
old reveal copy never resumes
local cache is never factual authority
revocation clears visible and accessible sensitive content first
invalid anchors resolve only on the server
client time never controls formal world state
old visits cannot overwrite newer explicit departure
all navigation anchors remain outside every canonical and evidence ledger
```

## Prohibited Product Patterns

- Welcome-back copy or animation.
- Attendance, streak, return gift, guilt, or absence punishment.
- Tree growth driven by visits, clicks, or dwell time.
- Environment used as fortune, danger, health, or relationship prediction.
- Fabricated online residents or missed-event montage.
- Restoring an open mirror, previous reveal, old assertion copy, or stale ARIA text.
- Candidate paths, potential relations, Lab content, or LLM guesses in the grove.
- Duplicating or teleporting Abu for private availability.
- Treating browser closure or a crash as deliberate departure.
- Client-side geometry migration or anchor repair.
- Reopening a Visit after an atomic departure succeeded.

## Acceptance Contract

Implementation is acceptable only when all of the following pass:

1. A formal return restores the last deliberate location but the current world.
2. First recognition, first reveal, and first fog-gate sequences never replay.
3. Root mirror and OneCanvas always start closed.
4. A world with no formal change does not invent one.
5. Formal tree change comes only from the current authorized projection.
6. Revoked content cannot return from pixels, cache, History, subtitles, or ARIA.
7. Turning back before the mist boundary writes no DepartureAnchor.
8. A spatial boundary departure writes exactly one atomic departure result.
9. `SEMANTIC_EXIT` does not claim a physical boundary crossing.
10. Network retries cannot duplicate a departure.
11. A stale page cannot overwrite a newer anchor or control lease.
12. Cross-Case and cross-account anchors never leak.
13. Guest migration requires explicit consent and consumes the Guest anchor.
14. Two devices cannot simultaneously control one viewer's Dream.
15. Suspension and hidden rendering never pause canonical world time.
16. Suspending an open mirror returns to a closed-mirror forest.
17. Browser Back and mobile Back use mirror-first, departure-second behavior.
18. Screen reader, keyboard, Reduced Motion, desktop, 390px, and landscape flows work.
19. A route failure after departure cannot expose or reopen Dream content.
20. Anchor and navigation events never enter Mingli, relationship, reward, or evidence
    ledgers.

When implementation is authorized, Codex must directly validate the full flow in
Chrome on desktop and 390px mobile, including Back behavior, Reduced Motion,
accessibility actions, console state, suspension, authorization revocation, concurrent
lease takeover, and every failure-critical path. User recording is not an engineering
prerequisite; the owner performs only final subjective experience review.

## Internal Consistency Audit

The frozen contract resolves the prior ambiguities as follows:

1. `TreeObservationAnchor`, `DreamDepartureAnchor`, and
   `DreamRecoveryCheckpoint` have non-overlapping lifecycles and authority.
2. Formal departure has two truthful triggers: embodied `SPATIAL_BOUNDARY` and
   accessible/platform `SEMANTIC_EXIT`.
3. Browser closure and crashes remain Recovery and cannot masquerade as departure.
4. Departure anchor update and Visit close are one idempotent atomic result.
5. Navigation state never enters LifeCase, relation, evidence, training, or rewards.
6. Return restores current world state, never an old image or old authorization.
7. Canonical Abu remains one public being while viewer-private projections remain
   isolated.
8. Single-device control is enforced by server lease epoch and fencing token.
9. Guest navigation state migrates only with explicit consent and cannot be reused.
10. No unresolved product semantics remain within this phase.
