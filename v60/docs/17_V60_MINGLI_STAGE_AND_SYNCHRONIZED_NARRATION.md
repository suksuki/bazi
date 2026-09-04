# V60 Mingli Stage and Synchronized Narration

Status: `IMPLEMENTED_AND_REAL_BROWSER_AUDITED_LOCAL`

Date: 2026-08-01

Last synchronized: 2026-09-04

This is the first implementation slice for the pre-prototype-merge Mingli
vertical. It does not claim that V60 has reached advanced-practitioner-grade
destiny reading. It turns the existing canonical Case and bounded Reading
foundation into one visible, recoverable product path:

```text
Home profile leaf
-> real Mingli branch
-> branches / leaves / flowers / fruit for the four evidence layers
-> four-pillar natal stage
-> six-pillar time layer
-> server-locked Abu narration
-> audio-clocked subtitles and deterministic stage emphasis
```

Retired narrative/game surfaces, multi-NPC scenes and the question bank are not
part of this product. Desktop and 390 px mobile are current acceptance targets;
the iPad book layout remains deferred.

## Owner decisions now in the executable baseline

- There is no directed invitation. The Mingli entry remains the profile leaf
  on the Home LifeTree.
- The default stage is the complete natal four pillars.
- Expanding time shows exactly natal four pillars plus current Dayun plus the
  selected annual pillar. A five-pillar state is invalid.
- The current layout target is Desktop Chrome. iPad portrait is deferred to
  the book-edition design round, and mobile remains a separate visual design
  problem.
- Abu is the boy narrator and now uses the Owner-selected Qwen3-TTS speaker
  `Dylan`. Dodo remains the girl narrator using the `Vivian` audition profile.
- The older Eric generation is append-only historical audition evidence. It
  was not deleted or rewritten.
- Sichuanese expression remains reserved for Theater rather than the formal
  Mingli Reading.

The selected Abu voice identity is
`v60.voice-profile.abu-dylan-owner-selected.001`. An environment override is
automatically demoted to `AUDITION_CANDIDATE`; it cannot inherit the
Owner-selected label.

## Progressive focused reading

The Mingli branch now generates prose by layer instead of starting one large
whole-chart request. The first action requests `STRUCTURE`; the saved structure
pass is then the only prerequisite for the life-image, career/wealth,
relationship/family and timing questions. The two theme questions are also
independent, so reading one never forces the other.

The browser posts one explicit `MingliFocus` to `/stage/focused-pass`, displays
its busy state immediately, reloads the same lineage-bound Summary and renders
only persisted normalized text. A partial result survives refresh. Raw local
model text, model prompts and teacher material are never projected to the
browser. The earlier `/stage/focused-reading` five-pass batch remains available
for bounded DEV comparison but is not called by the product UI.

Focused readings remain private Owner-review interpretations. Every pass binds
Case, Chart, LifeCase, Reading, Packet, model digest, provider profile, prompt,
structure dependency and deterministic normalization receipts. PostgreSQL
rejects update/delete mutations. A review flag in the structure pass propagates
visibly to dependent layers; no pass can write canonical facts or claim a
professional verdict.

The active Qwen3.8 Focused Profile `.005` follows the official non-thinking
template and sampling recommendations with a product-specific `4096 / 320`
context/output budget. Real first-generation passes measured 8.1–16.2 seconds;
an identical persisted pass replayed in 9ms. The full integration chronology,
exact parameters and practitioner-grade comparison with Gemma4 are recorded in
[`23_V60_QWEN38_MINGLI_INTEGRATION_AND_PRACTITIONER_REVIEW.md`](23_V60_QWEN38_MINGLI_INTEGRATION_AND_PRACTITIONER_REVIEW.md).

## Canonical subjects

The stage can project only:

1. the authenticated account's active `HUMAN_OWNER` Case;
2. that account's private `HUMAN_REFERENCE` Cases; and
3. the two explicitly admitted `CANONICAL_SYNTHETIC` character Cases.

Private reference subjects use stable `case:{case_ref}` routes and require the
same account authorization as their Case workspace. Their Stage and branch
summary bind the exact Case, Chart, LifeCase and formal Reading Ref/Hash. The
Home API that carries private birth details is explicitly `private, no-store`.
The canonical evidence drawer remains available only when all of those
identities match the active Owner Home snapshot; a reference route fails
closed rather than reading from or writing to the Owner Case.

The synthetic character birth details are Owner-approved fictional product
fixtures, not biographies and not substitutes for a real user Case:

| Character | Setting | Canonical four pillars |
| --- | --- | --- |
| Abu | male, 1998-11-11 12:00, Beijing | 戊寅 / 癸亥 / 壬戌 / 丙午 |
| Dodo | female, 2001-05-08 18:00, Shanghai | 辛巳 / 癸巳 / 辛未 / 丁酉 |

They use stable Profile and Case identities under a separate inactive system
account. Replay is idempotent. Historical human profiles with similar display
names are neither selected nor overwritten. The public stage API exposes no
birth date, time or location.

## Four- and six-pillar contract

`NATAL_4` contains four columns and eight bodies:

```text
year / month / day / hour
```

`NATAL_DAYUN_YEAR_6` contains six columns and twelve bodies:

```text
year / month / day / hour / current Dayun / selected annual year
```

The current Dayun is compiled through the existing canonical timing engine.
The calculation policy is now explicit as
`LUNAR_PYTHON_YUN_SECT_1_START_SOLAR_DATE_BOUNDARIES`; the displayed boundary
precision is the exact start-solar date returned by the pinned calendar
engine. On a transition date, a Case that has no observation time fails closed
with `START_SOLAR_DATE_TIME_UNRESOLVED_ON_BOUNDARY_DAY` rather than claiming a
current Dayun that the evidence cannot distinguish.

The selected annual column uses that solar year's Ganzhi
(`SELECTED_SOLAR_YEAR_GANZHI`). It is not derived from the current instant, so
January and pre-Lichun viewing cannot silently substitute the previous annual
label.

Every Projection binds the exact Case, Chart, LifeCase, active Foundation and
Timing profiles, source Refs and Hash. A formal Owner Reading identity is
included when present; the stage does not compile a new timing vector and
mislabel it as the historical Reading's evidence.

## Epistemic boundary

The stage can draw only admitted six-clash and six-harmony membership facts.
It deliberately holds these fields:

```text
stage_semantics = COORDINATES_AND_MEMBERSHIP_ONLY
relation_effect_status = UNRESOLVED
usable_source_status = UNRESOLVED
professional_verdict_allowed = false
```

It does not infer strength, usable root, relation effect, timing activation,
probability, effective work or auspiciousness. A visible relation line means
only that two displayed coordinates are members of an admitted relation
pair. It does not prove that the relation acts or that a source is usable.

This is the product form of the current professional evidence gap: the system
can locate the question and show competing or missing explanations, but it
cannot invent a professional relation-effect rule.

Reading `.006` also forbids the work path from becoming a third mechanism that
floats outside the professional decision. `selected_hypothesis_id` and
`method_card_ref` must bind the unique PRIMARY exactly. `STRONG`, `BALANCED`
and `SPECIALIZED_TENDENCY` exit only the weak-versus-follow sub-audit as
`NON_WEAK_OUTSIDE_SCOPE`; that exit does not infer a useful element, effective
work, relation effect or auspiciousness.

## Narration authority and playback

The browser submits only the subject, stage mode, year and expected Projection
Ref/Hash. It cannot submit narration text, speaker, model, provider or TTS URL.
The Media owner locks:

```text
Projection Ref/Hash
+ server-authored script Ref/Hash
+ actor and voice profile Ref/Hash
+ provider profile Ref/Hash
+ frame-exact cue ranges
+ WAV Ref/Hash
```

The service calls Qwen3-TTS on the server. The default public proxy is
`https://dblife.com/abu-tts/tts`; Server 13 may configure the private upstream
`http://192.168.0.7:7860/tts`. Neither address is returned to the browser. The
client receives only an authenticated same-origin audio URL with private,
no-store and Range semantics.

The playback states are:

```text
PREPARING -> READY -> PLAYING <-> PAUSED
                         <-> BUFFERING
                         -> ENDED / FAILED
```

While PREPARING, semantic subtitles and motion do not run. During PLAYING,
`HTMLAudioElement.currentTime` is the sole subtitle, cue and deterministic
stage-emphasis clock. PAUSED freezes the same clock. Refresh preserves the selected Case,
four/six-pillar mode and year through the URL, while narration returns to
`IDLE`; it never pretends to recover an in-flight audio position.

### Current-layer direct silent reading

The grown LifeTree branch now uses each organic node itself as the direct
companion action. There is no intermediate Reading card, character CTA, stage
button or chapter rail. One click projects the selected four-layer Reading
surface from a complete Qwen3.8 Focused Pass set or, when that is absent, the
same validated ClaimGraph used by Reading and Lab:

```text
branch / leaf / flower / fruit click
-> complete Focused Passes, otherwise admitted ClaimGraph claims
-> all source-bound chapters in one continuous reading
-> same four/six-pillar Scene Player
-> LISTENING / PAUSED character state
```

This is deliberately not a cosmetic wrapper around the earlier coordinate
narration. It does not call `/api/v60/mingli/narrations`, mount an audio element
or claim that semantic Cue choreography has been approved. `WITHHELD` claims
are excluded, internal codes such as `WEAK` are translated into user-facing
Chinese, Work Path closure and assessment states preserve their distinct
professional meanings, and each visible chapter carries the exact Claim Ref or
Pass Ref plus its Source Ref/Hash. A layer with no admitted/projectable source
cannot enter direct reading unless the same click can generate its missing
Focused Pass server-side; failure remains on the branch with a retry cue. The
time-trend layer opens the full six-pillar coordinate state; the other three
layers open the natal four-pillar state.

The six-pillar coordinate state is not itself permission to attach frozen
Reading prose to the selected year. Until ClaimGraph carries a typed binding
between its Dayun/annual claims and the independently selected Stage timing
vector, time rehearsal contains only `TIMING_NATAL` and
`DISCRIMINATING_QUESTION`. It visibly says that Dayun/annual paragraphs are
still being aligned, and never paints an old annual judgment onto a new year.

The route distinguishes three product intents:

```text
mingli_stage=1&mingli_rehearsal=1  companion rehearsal
mingli_stage=1                     ordinary Reading observation
view=lab                           explicit Lab research surface
```

Refresh restores direct reading. Back returns to the same branch and selected
layer, Forward restores it, and the visible close action returns directly to
the branch without opening Lab. Formal server-locked TTS remains available
from the ordinary Reading/Lab stage, but its current coordinate script is not
silently reused as four-layer destiny narration.

## One shared Scene Player

The first frozen-V108 integration slice no longer treats Abu Says as a panel
inside Lab. `MingliSceneHost` remains mounted while the user switches among
Mingli Reading, Lab observation and narrated presentation. It owns exactly one
lazy-loaded React Three Fiber Scene Player:

```text
MingliSceneHost
├── MingliScenePlayer          one Canvas / one Projection
├── ReadingSceneGuide          presentation only
├── MingliLabSceneInspector    selection and evidence only
└── MingliNarrationDirector
    ├── MingliAudioPlayer      audio transport and sole clock
    └── CharacterPerformance  actor state and transparent media
```

Reading and Lab never mount their own Canvas. Opening or closing narration
also leaves the same Scene Player instance in place. Moving from four to six
pillars updates the server-issued Projection in that instance; it does not
create a second stage or a five-pillar intermediate state.

The earlier canonical Reading and Lab controls remain reachable through a
collapsible evidence drawer beside the shared stage only for an exact active
Owner lineage match. It preserves Case management, formal Reading details,
evidence requests and mechanism-candidate comparison without placing the
narrator inside that drawer. Reference Cases already have a real branch
Reading summary and 4/6-column stage, but their full mutable evidence drawer
is visibly withheld until a Case-bound projection replaces the Owner-only Home
contract. Closing the narration layer explicitly pauses and releases its
captured audio element; reduced-motion clients use the Registry poster rather
than a moving character delivery.

The 3D renderer consumes only stable `column_ref`, `body_ref`, `relation_ref`
and the bounded Director frame. Its admitted semantic actions are:

```text
PILLARS_PRESENT
RELATIONS_PRESENT
BOUNDARY_HOLD
TIME_COORDINATES_PRESENT
```

Relation paths are neutral arcs between exact branch members. Bodies do not
aggregate, collide, morph into “合”, grow a usable-root channel or perform an
effect animation. `PAUSED` and `BUFFERING` freeze semantic motion at the exact
audio time; a separate non-semantic ambient clock may continue only when the
Director permits it. WebGL2 failure or context loss falls back to the existing
bounded 2D stage without changing the Projection.

The actor layer now supports Abu and Dodo media independently through the
Hash-locked Runtime Media Registry `.004`; the browser does not own their
paths. It reports its current fidelity as
`IDLE_MEDIA_WITH_AUDIO_BOUND_STATE`: the transparent video
instance follows READY/PLAYING/PAUSED/BUFFERING, but the current assets are not
claimed as phoneme lip-sync, gaze direction or final Cue choreography.

## Persistence and ownership

Migration `0026_mingli_narration_assets` adds the account-scoped, append-only
`media.mingli_narration_assets` ledger. Migration
`0027_mingli_narration_v2` advances Foundation to `.019` and pins Stage `.002`,
Timing `.002` and Narration `.002`. The ledger stores exact Projection, script,
voice, provider deployment, audio and cue identities plus the validated mono
24 kHz 16-bit PCM WAV. Historical Narration `.001` rows remain readable and
immutable.

New Mingli projections use Timing `.002`; older Timing `.001` rows remain
decodable as immutable migration history but are not active projection inputs.

Media owns TTS generation and this schema write. Mingli owns the chart, stage
Projection and narration script facts. Architecture tests now include Media
in the unique-writer audit so a future Mingli service cannot write the Media
schema directly.

Current executable identities are:

```text
Foundation       v60.foundation.041
Architecture     v60.runtime-architecture.077
Mingli Engine    v60.mingli-cognitive-engine.048
Media            v60.media-library.005
Runtime Media    v60.runtime-media-registry.006
Unit Mingli      v60.unit-mingli.038
Unit Abu Says    v60.unit-abu-says.008
Stage            v60.mingli-stage-projection.004
Timing           v60.mingli-timing-evidence-vector.002
Narration        v60.mingli-narration.002
Migration        0049_mingli_progressive_focused_passes
```

## Real evidence

The real public TTS service generated a new Dylan six-pillar asset:

```text
narration_ref       v60-mingli-narration-63140c06781936faa540
voice_profile_ref   v60.voice-profile.abu-dylan-owner-selected.001
provider             v60.qwen3-tts-proxy.001 / dblife-public-proxy
duration             56.480 seconds
WAV bytes            2,711,084
cue boundaries       0 / 10080 / 18720 / 32160 / 56480 ms
```

The database contains three historical Narration `.001` assets (two Dylan and
one Eric audition) and the new Dylan Narration `.002` asset. This proves the
voice and contract changes appended rather than overwrote history. Assets stay
account-scoped rather than becoming a globally reusable public audio object.

The real signed-in product page verified:

- Desktop natal stage: four columns, eight bodies, no horizontal overflow;
- Desktop time layer: six columns, twelve bodies, no monthly or five-pillar
  column;
- relation endpoints remain bound to the exact two branch bodies, including
  the tall iPad portrait layout (measured vertical drift below 0.45 px there);
- in-app Chrome iPad landscape and portrait viewports: the same six/twelve
  contract with no horizontal overflow;
- PLAYING: DOM clock 1380 ms versus audio clock 1384 ms, with the STRUCTURE cue
  and matching subtitle;
- PAUSED: zero DOM-clock drift over 700 ms;
- refresh: exact synthetic Abu, six-pillar mode and 2026 selection recovered,
  narration returned to IDLE;
- browser Back/Forward restored the exact four/six-pillar route, and the
  authenticated Owner rail appeared only for an exact Case/Chart/LifeCase/
  Reading lineage match.

Screenshots and machine-readable metrics are in
`.artifacts/mingli-stage-narration/`.

The iPad checks are responsive viewport evidence in the in-app Chrome runtime,
not a claim of physical iPad Safari, touch or autoplay-policy certification.
The shared-player browser audit additionally verified:

- Reading -> Lab -> narration -> Lab kept the same Scene instance and exactly
  one Canvas;
- four pillars -> six pillars kept that instance while changing from eight to
  twelve bodies;
- a Lab relation selection retained its exact `relation_ref` and never changed
  the professional boundary;
- READY exposed one private audio element without advancing subtitles;
- PLAYING followed real `audio.currentTime`; PAUSED held both audio time and
  Scene `cueProgress` exactly constant across a 500 ms sample;
- 1440x900 Desktop, 1024x768 iPad landscape and 768x1024 iPad portrait showed
  all six columns without inspector overlap or document overflow;
- Dodo used her own transparent media source while sharing the same Director,
  audio transport and Scene Player.
- the canonical evidence drawer exposed Case management, Reading and source
  evidence at Desktop and iPad portrait sizes without adding document overflow
  or a second Canvas; closing an actively playing narration removed its audio
  node after playback had started.

Evidence is in `.artifacts/mingli-shared-scene/`. These iPad checks remain
responsive Chrome evidence, not physical iPad Safari, touch or autoplay-policy
certification. The Three renderer is isolated in a lazy chunk; the current
chunk-size warning is recorded performance debt, not proof of a second stage.

The real-profile branch integration additionally verified:

- all 20 authorized V50 Owner-corpus profiles were already present in V60 as
  one `HUMAN_OWNER` and 19 `HUMAN_REFERENCE` Cases; the UI now exposes them
  without duplicating migration lineage;
- all 20 Stage and Reading-summary projections match on Case, Chart, LifeCase,
  Reading Ref and Reading Hash, and all 20 produce four natal columns or six
  time-layer columns with twelve bodies;
- the frozen V108 day/night growth films are byte-identical, 1612×974,
  24 fps and 7.208333 seconds, with the same four organ hotspots;
- `命局原理` uses the formal bounded Reading, `生命意象` remains an explicit
  unadmitted gap, `人生主题` uses the three real life-domain windows, and
  `时间趋势` exposes only deterministic coordinates and admitted relation
  membership;
- refresh restores the final static branch and exact layer; closing replaces
  the leaf-route history entry so browser Back/Forward cannot reopen a closed
  branch; and reference pages cannot expose or mutate the Owner evidence
  drawer.

Evidence is in `.artifacts/real-profile-mingli-branch/`.

## Design handoff and next constraint

The frozen V108 source at commit
`a6cf762684e14514f58c8f45b82cca86d9a7ec4c` is available and remains the
experience authority. This slice extracted its particle-stage and transparent
actor language. The active Home and profile-leaf branch now preserve the V108
scene plane, day/night growth film, organ positions, opening/closing timing and
companion placement while replacing mock conclusions with V60 Case-bound
projections. The formal product also improves one prototype limitation: V108
Lab and Abu Says each mounted a separate Canvas, whereas the formal product
keeps one shared Scene Player. Remaining fidelity work concerns scene-specific
narration design, not a second Mingli entry or replacement UI framework.

```text
DESIGN_REQUEST
- scene: Mingli Reading / Lab / Abu Says shared six-pillar stage
- source_files: frozen V108 MingliStage3D, MingliStageLabPreview, AbuSays
- observed_behavior: one real Canvas now survives all three surfaces; current
  Abu/Dodo media prove audio-bound state but not final speaking choreography
- design_question: provide the final single-player Desktop Chrome composition,
  six-column spacing and Abu/Dodo listening/speaking/paused/attention states;
  leave iPad book composition for its separate design round
- current_assumption: Reading and Lab reserve space around the same stage;
  narration expands that stage without remounting it
- implementation_constraint: audio.currentTime is the sole semantic clock;
  only coordinates, admitted relation members and evidence holds may animate
- options: refine V108 into a true one-player prototype, or provide annotated
  states/assets that can be applied directly to the current shared Host
- recommendation: prototype the real one-player transition and deliver the
  minimum controllable actor-state assets; do not add a second Canvas
- owner_decision_required: NO, unless the design requests a semantic relation
  action beyond the currently admitted evidence boundary
```

The remaining Mingli blocker is professional, not audiovisual. The Stage now
also renders sealed synthetic research Cases through the same Player without
placing `research:*` identities in the ordinary profile list. Method discovery
no longer stays on one Owner Case: the first legal A/B pair and minimum
anti-follow root rule are recorded in
[`20_V60_SYNTHETIC_MINGLI_METHOD_LAB.md`](20_V60_SYNTHETIC_MINGLI_METHOD_LAB.md).
Desktop Chrome is the active first-round target; the older responsive iPad
checks above remain historical evidence, not a current iPad portrait product
commitment.

The current-layer direct-reading browser audit additionally verified:

- branch, leaf, flower and fruit each opened the matching reading in one click,
  with no separate companion, Lab, stage, generation or chapter-pagination
  control on the branch;
- principle reading translated the Day
  Master title to `日主偏弱` rather than exposing `WEAK`;
- timing reading restored a six-column/twelve-body stage with current Dayun
  and 2026 annual coordinates, while no unbound Dayun/annual prose was attached
  to those columns;
- at that pre-speech checkpoint there was no audio element, playback state or
  narration generation request; the 2026-09-04 slice below supersedes this
  presentation limitation;
- refresh retained the exact Case, layer and direct-reading mode;
- close returned to the same branch, and only the Home Lab flower entered
  `view=lab`.

## 2026-09-04 public six-pillar focused narration

The Owner retained the old Six-Pillar Lab's 3D particle-and-explanation
capability without reopening the complete LAB surface. Public Abu Says now
reuses the same lazy `MingliSceneCanvas`, six deterministic columns and twelve
stable particle bodies. There is still exactly one Canvas; narration remains an
overlay and does not own a renderer.

Focused Pass speech now has its own sequenced Director. It pairs every audio
blob with the exact persisted chapter by `pass_ref`, samples the real
`HTMLAudioElement.currentTime` on animation frames and publishes that clock to
the shared Scene Player. Particle rotation, breathing and size pulses therefore
advance with speech. PLAYING advances both clocks; PAUSED and BUFFERING retain
the exact sampled time and Cue progress; resuming continues from that point.
The active text chapter and Abu's speaking/paused performance state follow the
same segment. Device speech fallback deliberately keeps only ambient motion
because it exposes no reliable audio clock.

The speech request now carries the current Stage mode and selected year. The
server reconstructs and Hash-checks that exact four- or six-pillar Projection
before accepting the account-owned Focused Pass. This repairs the former
six-stage `409 mingli_focused_speech_stage_stale` mismatch while preserving the
old four-pillar request default.

Real headless Chrome evidence at 1440×900 verified:

- six labels: 年柱、月柱、日柱、时柱、大运、流年;
- Focused Speech HTTP 200 on the six-pillar Projection;
- one stable Scene instance before, during and after playback;
- audio time 622 → 1538 ms and Scene Cue progress 0.010571 → 0.026126;
- PAUSED held 1575 ms / 0.026754 exactly across an 800 ms sample;
- resume advanced to 2319 ms / 0.039384;
- Abu changed with the same clock from SPEAKING to PAUSED and back;
- no console, page, request or HTTP errors.

A second 390×844 Chrome run reached PLAYING with six columns, a 390×844 Canvas,
positive Cue progress, no horizontal/vertical document overflow and no runtime
errors.

Evidence is in `.artifacts/mingli-six-pillar-focused-speech/`. LAB source and
research modules remain internal; LAB public routes remain unregistered.
