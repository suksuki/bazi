# V60 Gemini Abu Actor Prompts V1

Attach both approved V60 Abu references to every request:

1. `ABU_V60_CHARACTER_REFERENCE_V1` for face, markings and painterly identity;
2. `ABU_V60_SEATED_TRANSPARENT_V1` for exact seated body proportions.

Use the full prompt for one asset at a time.

## Shared identity and technical lock

```text
Use the attached images as an exact character identity lock for AbuKnows V60.
Abu is the same small black-and-tan Shiba companion in every frame: very large
warm brown eyes, compact rounded muzzle, cream cheeks and chest, fixed tan
eyebrow and leg markings, curled tail with a cream tip, and one rust-red-brown
scarf tied at the same side. Preserve the exact face shape, eye spacing, ear
size, coat pattern, scarf construction, body proportions and watercolor brush
texture. Do not redesign, beautify, simplify or make Abu younger.

Visual style is Eastern fairy-tale picture-book illustration: hand-painted
watercolor and gouache, subtle paper texture, restrained ink outlines, soft
natural color variation. It is not glossy 3D, anime, vector art, sticker art,
plastic mobile-game rendering or generic chibi.

Render one full-body actor take against a perfectly uniform chroma green
#19A61E background. No floor, floor line, cast shadow, reflection, gradient,
scenery, particles or props. Keep at least 12% clear space around the entire
character, including ears, scarf ends and tail. Locked orthographic-feeling
camera, fixed scale and fixed bottom-center anchor. No zoom, pan, tilt, camera
shake, focus breathing or crop change. 1920x1080, 24 fps, 10 seconds.

Abu remains silent with mouth fully closed. No lip movement, speech, panting,
teeth or tongue. No text, subtitles, logos or interface elements. No extra
limbs, duplicated tail, changing markings, changing scarf, body sliding or
unrequested horizontal travel. One primary action only. Begin and end with a
stable neutral pose suitable for Codex postprocessing.
```

## ABU_V60_01_SEATED_IDLE_LOOP_V1

Append:

```text
ACTION: Abu sits calmly facing almost forward, with a gentle five-degree gaze
toward screen-right. Preserve the exact seated silhouette and paw placement.
Use only quiet breathing, one complete natural blink between 2.3 and 2.8
seconds, one restrained ear adjustment, and one small tail-tip relaxation.
The scarf may lag by only a few millimeters with breathing. No nod, no paw
gesture, no looking around and no standing.

LOOP CONTRACT: The final 1.0 seconds must return to the exact first-frame
breathing phase, ear angle, eyelid state, scarf position, tail position,
bounding box and bottom-center anchor. Avoid a crossfade. Preserve natural
subtle vertical breathing without scale drift.
```

## ABU_V60_02_LISTEN_ONCE_V1

Append:

```text
ACTION: Abu begins in the approved neutral seated pose. At 1.2 seconds, both
ears notice a quiet sound from screen-left; the nearer ear turns first, then
Abu turns the head only 8 to 12 degrees toward screen-left. The eyes follow
without widening dramatically. Hold attentive listening for 1.4 seconds,
then return smoothly to the exact neutral pose by 5.5 seconds. Remain seated.

SEMANTIC BOUNDARY: This means "I am listening", not surprise, warning,
calculation, discovery or approval. No head tilt beyond 4 degrees, no nod, no
raised paw and no body translation. Keep a stable neutral hold from 6 to 10
seconds for a clean one-shot trim and return to idle.
```

## ABU_V60_03_ACKNOWLEDGE_ONCE_V1

Append:

```text
ACTION: Abu begins in the approved neutral seated pose. After one quiet breath,
make exactly one very small acknowledgement nod: the muzzle lowers by only a
few degrees, the eyes soften naturally, then the head returns to neutral. The
entire gesture lasts about 1.6 seconds. Do not smile more broadly and do not
move the paws. Hold the exact neutral pose after the gesture.

SEMANTIC BOUNDARY: This means "I received that", not "you are correct", not a
reward, celebration, judgment or completed Mingli reasoning. No sparkle, tail
wag, applause, bow, speech or second nod.
```

## ABU_V60_04_WAITING_LOOP_V1

Append:

```text
ACTION: Abu waits peacefully while another process is pending. Remain seated
and grounded. Use slow breathing, one soft blink, and one small change of gaze
from the nearby tree branch to the middle distance, then naturally back.
Movement must stay restrained and emotionally neutral.

SEMANTIC BOUNDARY: Abu is observing and waiting, not thinking through an
answer. No paw on chin, puzzled expression, head scratching, circling,
counting, glowing idea, nod or judgment.

LOOP CONTRACT: Return to the exact initial gaze, breathing phase, ear angle,
scarf, tail, bounding box and anchor at the final frame without crossfade.
```

## Source acceptance

```yaml
character_lock: exact V60 identity
mouth: closed_all_frames
camera: locked
bottom_center_anchor: stable
background: uniform_chroma_green
watermark_safe_region: must_not_overlap_abu
audio: ignored_and_removed_in_post
runtime_delivery: not_direct_from_gemini
```
