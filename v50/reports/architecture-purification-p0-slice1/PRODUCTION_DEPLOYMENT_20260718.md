# Production Deployment Record

```yaml
deployment_id: v50-experience-next-20260718
target: 13-server
public_origin: https://dblife.com
experience_url: https://dblife.com/experience
status: passed
default_entry_switched: false
legacy_entry_links_to_experience: true
```

## Delivered

- “看见命局 Next” independent Experience Shell and production bundle.
- Mobile current-case selector and responsive four-pillar layout.
- Concise first-screen thesis with the complete formal thesis preserved in the expandable cognition section.
- A visible “看见命局” migration entry from the current Abu shell.
- Mobile accessibility labels for account, archive and view controls.
- Qwen TTS production configuration with Eric as Abu's voice.
- Persistent narration cache and Opus playback variants.

## TTS Configuration

```yaml
base_url: http://192.168.0.7:7860
speaker: Eric
timeout_seconds: 180
narration_media_dir: /home/hlsystem/bazi/qiazhi/v50/.runtime/narration
opus_enabled: true
ffmpeg: /usr/bin/ffmpeg
```

The server-to-server TTS health request passed. A real narration segment was generated through the public production API, returned as Opus and then read through the authenticated audio endpoint.

```text
first generation: 25s
first request cache_hit: false
second request cache_hit: true
second request response: 0.12s
production audio: HTTP 200, audio/ogg; codecs=opus
```

## Validation

```text
TypeScript typecheck: passed
Experience bundle build: passed
Python regression: 313 passed
Architecture audit: 10/10 passed
Production service: active
Public /health: 200
Public /: 200
Public /experience: 200
Public Experience bundle: 200
Desktop visual check: passed at 1440 x 1000
Mobile visual check: passed at 390 x 844
Horizontal overflow: none
Production Abu narration playback: passed
```

Critical production bundle hashes match the local release exactly.

## Recovery

The pre-deployment code archive and production environment backup are stored on the 13 server:

```text
/home/hlsystem/qiazhi-sync-backups/v50-code/pre_experience_20260718_122746.tar.gz
/home/hlsystem/qiazhi-sync-backups/v50-code/env_pre_experience_20260718_122746.production
```

The existing `/` entry remains available for login, registration, profile management and Abu-led chart creation. This deployment does not silently switch the default entry; it exposes the new experience at `/experience` and links to it from the current shell.
