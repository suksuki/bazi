# V60 Next Media Generation Pack V1

This is the production order for the next AbuKnows V60 media batch.
Generate one source file per request. Do not combine actions into a montage.

## Required reference attachments

| Request family | Required attachments |
| --- | --- |
| Abu actor | `media/sources/ABU_V60_CHARACTER_REFERENCE_V1/v1/source.png` and, for body placement, `media/sources/ABU_V60_SEATED_TRANSPARENT_V1/v1/source.png` |
| LifeTree cinematic | `web/public/assets/dream/v60-life-world-clean-v1.png` plus the approved final frame from the preceding clip |
| Brand | `media/sources/ABUKNOWS_V60_LOGO_PRIMARY_V1/v1/source.png`; never ask the video model to redraw it |

Every visual request inherits:

- `V60_EASTERN_FAIRY_TALE_STYLE_LOCK.md`
- no generated UI, captions, logo or readable text;
- platform corner marks may remain inside a clear postprocess-safe area;
- no request asks Gemini to remove its own platform mark;
- Codex archives the untouched source before keying, masking, trimming,
  stabilizing, loop repair or audio separation.

## Generation order

1. `ABU_V60_01_SEATED_IDLE_LOOP_V1`
2. `ABU_V60_02_LISTEN_ONCE_V1`
3. `ABU_V60_03_ACKNOWLEDGE_ONCE_V1`
4. `ABU_V60_04_WAITING_LOOP_V1`
5. `ABU_V60_05_GUIDE_LEFT_ONCE_V1`
6. `V60_TREE_01_FLOWER_BUD_APPEAR_V1`
7. `V60_TREE_02_FLOWER_OPEN_V1`
8. `V60_TREE_03_SHARED_FRUIT_SET_V1`
9. `V60_TREE_04_FRUIT_MATURE_V1`
10. `V60_TREE_05_FRUIT_OPEN_V1`
11. the four independent audio sources

Do not start a later tree clip until the preceding clip's final-frame handoff
has been approved. This prevents branch, flower and fruit anchor drift.

## Prompt files

- `V60_GEMINI_ABU_ACTOR_PROMPTS_V1.md`
- `V60_GEMINI_LIFE_TREE_CINEMATIC_PROMPTS_V1.md`
- `V60_GEMINI_AUDIO_PROMPTS_V1.md`

## Expected source delivery

```yaml
video:
  preferred_resolution: 1920x1080
  frame_rate: 24
  duration: 8_to_10_seconds
  source_audio: remove_or_ignore
  runtime_alpha: produced_by_codex_postprocess
audio:
  sample_rate: 48000
  preferred_format: WAV
  normalization: none_in_source
```
