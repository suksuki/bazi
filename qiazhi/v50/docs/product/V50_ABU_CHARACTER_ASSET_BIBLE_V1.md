# V50 Abu Character Asset Bible v1

Status: current designer handoff

## Identity

Abu is a compact black, cream and warm-tan Shiba Inu Mingli practitioner. The character is approachable, professional, lightly mysterious and restrainedly playful.

Frozen traits:

- upright triangular ears;
- compact torso and full curled tail;
- cream muzzle, brows, chest and paws;
- warm tan cheeks and dark attentive eyes;
- rust-orange scarf;
- hand-painted editorial rendering with readable silhouette at 48-96 px.

Do not change breed, facial markings, muzzle length, tail curl, scarf color, camera language or apparent age between actions.

## Production Coordinate System

```yaml
source_canvas: 1024x1024
preferred_web_canvas: 960x720
background: real alpha
anchor: bottom-center
foot_anchor_y: 97.2%
character_scale: normalized by visible character bounds
cast_shadow_in_asset: false
text_or_watermark: forbidden
```

The page may render its own subtle grounding shadow. The asset itself contains no floor, card, scenery, label, glow or color block.

## Current Production Motions

| Motion | Product use | Pack |
| --- | --- | --- |
| `idle_blink` | quiet presence | v4 runtime |
| `head_tilt` | listening, parsing, thinking, Probe | v4 runtime |
| `caution_ears` | boundary and recoverable failure | v4 runtime |
| `happy_tail` | completion and case confidence update | v4 runtime |
| `welcome_wave` | first welcome and safe return to Abu | v5 designer |
| `sleep_breathe` | idle timeout and quiet waiting | v6 designer |
| `butterfly_play` | occasional awake-idle companion moment | v6 designer |
| `run_jump` | occasional awake-idle adventure | v7 designer |
| `divination_classic` | retained fallback reasoning motion | v8 designer |
| `taoist_divination` | active whole-chart, domain and Probe reasoning | v9 designer |
| `breakdance` | rare awake-idle celebration | v9 designer |
| `sad_tears` | hard reading failure or blocked professional review | v11 designer |
| `enter_and_notice` | enter a scene and discover the current semantic object | v12 actor pass |
| `turn_and_point` | compact seated guidance toward a semantic object | v12 actor pass |
| `stand_point_up_left` | close-up blackboard guidance toward the upper-left | v12 actor pass |
| `stand_point_up_right` | controlled mirrored guidance toward the upper-right | v12 actor pass |
| `notice_tension` | restrained reaction to structural tension | v12 actor pass |
| `face_change_transition` | OneCanvas-to-Xiangfa theater transition | v12 actor pass |
| `ninja_disappear_throw` | rare playful finale interlude; transform, disappear and throw | v12 actor pass |

## Motion Library Governance

The motion library is managed as four linked records. None may silently replace another:

| Record | Authority |
| --- | --- |
| `v12-actor-pass/library.json` | human-readable action name, description, product role, exclusions and delivery paths |
| `v12-actor-pass/video-inventory.json` | original designer source, source hash, selected time range, derivatives and known limitations |
| `motion-registry.js` | runtime state-to-motion mapping, scale, stage profile and playback behavior |
| per-action `manifest.json` | production evidence: alpha, watermark removal, crop, frames and source traceability |

Product code should reference a stable `action_id` or registered runtime state. A designer filename is never a product contract. Replaced motions move to `retired` and remain traceable; they are not silently deleted.

Every production action records:

```yaml
action_id: stable machine identity
label_zh: concise library name
description_zh: what the actor visibly does
product_role: the intended narrative job
do_not_use_for: contexts that would distort Abu's role
source_hash: stored in inventory and manifest
```

`abu_face_change_transition_v1` is registered specifically for the S0 `OneCanvas -> Xiangfa` transition. It is not a generic loading animation, a favorable/unfavorable result signal, or a supernatural prediction gesture.

`abu_ninja_disappear_throw_v1` uses the designer's full-body seated-start variant, preserving Abu's familiar cute silhouette before the costume change. The biped standing-start source remains traceable but is held because it feels abrupt and intimidating in the quiet finale; the half-body-start source is held because it creates a visible framing jump. Ninja, breakdance and face-change are optional finale/IP moments only. They cannot interrupt professional explanation or imply a favorable, unfavorable or supernatural Mingli result.

### Locomotion Rule

Abu must never be translated across the stage while an idle, listening or static guidance pose is playing. Any visible horizontal move longer than one quarter of Abu's body width must use a registered locomotion action (`run_jump`, `enter_and_notice` or a future walk cycle), and the stage travel must finish inside that action's run/walk phase. The stop, look-back or notice phase stays spatially fixed.

In theater playback, locomotion media plays natively while audio is running; frame seeking is reserved for pause, scrub and deterministic export. A scene that changes Abu's horizontal zone must complete its run phase before switching to the scene-specific gesture.

### Framing Rule

Full-stage shots must use a source with visible feet and a full-body safe crop. `abu_stand_point_up_left_v1` and its mirrored right-facing derivative are close-up blackboard actions because the designer source crops the lower body. They must not be enlarged into a full-stage shot. S0 uses the native, full-body `abu_turn_and_point_v1` for its OneCanvas guidance scene; the mirrored half-body action remains available only for deliberately framed close-ups.

## Runtime Scale Contract

Source canvas dimensions are not a valid measure of character size. Runtime calibration uses the visible alpha bounds at the canonical `164x106` Abu stage.

```yaml
canonical_stage: 164x106
target_apparent_height: 84px
standing_motion_gate: 72-102px
rest_motion_gate: body_footprint_width_80-110px
anchor: bottom-center
state_transition: opacity_crossfade
```

The single runtime registry is `apps/product/static/l5/assets/abu/motion-registry.js`. It owns asset paths, display scale, stage profile, playback behavior, category, state mapping and the awake-idle ambient pool. Product code must not add a second per-motion size table.

`taoist_divination` loops continuously for the full duration of genuine system reasoning, so a long-running reading never freezes on its final frame. Awake idle uses a weighted, non-repeating ambient scheduler: butterfly play is most common, breakdance is occasional, and run/jump is rarer. Each ambient motion remains one-shot and returns to quiet idle before another can begin. `sad_tears` is reserved for a hard reading failure or a result blocked by the professional review gate; competing hypotheses, uncertainty and unsupported domains remain caution states. Sadness describes Abu's workflow response, never the user's fate.

The S0 finale chooses one complete action at a time from breakdance, face-change and ninja, never switching mid-motion or repeating the immediately previous action. After 28 seconds without user interaction, Abu stops the ambient sequence and sleeps. Pointer, touch, keyboard or Xiangfa interaction wakes Abu and restarts the restrained finale cycle. Reduced-motion and deterministic capture modes keep the quiet idle pose instead of running the random scheduler.

## Next Designer Motions

```text
thinking_divination
probe_invite
caution_boundary
confidence_update
wake_stretch
listening_note
profile_saved
recovery_retry
```

The concise designer brief is maintained in `V50_ABU_DESIGNER_MOTION_REQUESTS_V1.md`.

Active actions return to `idle_blink`. Emotion tracks workflow state, never a favorable or unfavorable fate judgment.

## Delivery Gate

1. Real alpha with transparent corners.
2. Same canvas, scale, scarf, light direction and bottom anchor.
3. No right-side icon, color block, watermark, matte or checkerboard.
4. Readable at 64 px and 96 px.
5. Natural on ivory, forest and photographic backgrounds.
6. Animated WebP plus a static PNG poster for reduced-motion mode.
7. Manifest records source hash, segment, frame count and allowed product states.

The asset layer cannot generate Mingli claims, choose a product action, update case beliefs or change chart facts.
